/* eslint-disable */
/**
 * Living-MA augment: CT.gov v2 fetch + 24h browser cache +
 * structured-extract helper.
 *
 * Public API:
 *   LivingMACtgov.searchByPico(query, opts) -> Promise<Candidate[]>
 *   LivingMACtgov.fetchStudy(nct)            -> Promise<StudyJson>
 *   LivingMACtgov.extractStructured(study)   -> Partial<Trial>
 *
 * Cache: localStorage, key = `livingma_ctgov_${sha256(query+opts)}`,
 * TTL 24h. Bypassed if `opts.forceRefresh === true`.
 *
 * Public CT.gov v2 endpoint (no auth, ~250 req/h soft limit).
 *
 * The structured extractor pulls from these CT.gov modules:
 *   - protocolSection.identificationModule  (NCT, brief title)
 *   - protocolSection.statusModule          (overall status, dates)
 *   - protocolSection.designModule          (phase, allocation)
 *   - protocolSection.armsInterventionsModule (interventions)
 *   - protocolSection.eligibilityModule     (sex, ages, criteria)
 *   - resultsSection.participantFlowModule  (randomization N per arm)
 *   - resultsSection.outcomeMeasuresModule  (event counts, statistical
 *                                            analyses with HR/RR/OR+CI)
 *
 * Confidence ladder:
 *   "HIGH"   - structural CT.gov field
 *   "MEDIUM" - inferred from CT.gov narrative (e.g. brief summary)
 *   "NONE"   - field missing; user must enter manually
 */
(function (root) {
    'use strict';

    const API_BASE = 'https://clinicaltrials.gov/api/v2/studies';
    const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24h
    const CACHE_PREFIX = 'livingma_ctgov_';

    // ---- cache helpers ----

    async function sha256Short(s) {
        // Use Web Crypto if available, else a simple fallback hash.
        try {
            const buf = new TextEncoder().encode(s);
            const hashBuf = await crypto.subtle.digest('SHA-256', buf);
            const hex = Array.from(new Uint8Array(hashBuf))
                .slice(0, 8)
                .map(b => b.toString(16).padStart(2, '0')).join('');
            return hex;
        } catch (e) {
            // Fallback: simple djb2-style
            let h = 5381;
            for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
            return (h >>> 0).toString(16);
        }
    }

    function cacheGet(key) {
        try {
            const raw = localStorage.getItem(CACHE_PREFIX + key);
            if (!raw) return null;
            const obj = JSON.parse(raw);
            if (!obj.t || Date.now() - obj.t > CACHE_TTL_MS) {
                localStorage.removeItem(CACHE_PREFIX + key);
                return null;
            }
            return obj.v;
        } catch (e) {
            return null;
        }
    }

    function cacheSet(key, value) {
        try {
            localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ t: Date.now(), v: value }));
        } catch (e) {
            // localStorage quota, etc -- silent
        }
    }

    // ---- API helpers ----

    /**
     * Search CT.gov by a free-text PICO query.
     *
     * @param {string} query - e.g. "dolutegravir HIV first-line"
     * @param {object} opts
     * @param {string[]} [opts.excludeNcts=[]] - dedup against these
     * @param {string} [opts.dateFrom='2015-01-01'] - studies started on/after
     * @param {string[]} [opts.phase=['PHASE3']]
     * @param {boolean} [opts.forceRefresh=false]
     * @param {number} [opts.pageSize=50]
     * @returns {Promise<Array<{nct, title, phase, status, startDate, completionDate, sponsor, briefSummary}>>}
     */
    async function searchByPico(query, opts = {}) {
        const excludeNcts = new Set(opts.excludeNcts || []);
        const dateFrom = opts.dateFrom || '2015-01-01';
        const phases = opts.phase || ['PHASE3'];
        const forceRefresh = !!opts.forceRefresh;
        const pageSize = opts.pageSize || 50;

        const cacheKey = await sha256Short(`search|${query}|${dateFrom}|${phases.join(',')}|${pageSize}`);
        if (!forceRefresh) {
            const cached = cacheGet(cacheKey);
            if (cached) {
                return cached.filter(c => !excludeNcts.has(c.nct));
            }
        }

        const params = new URLSearchParams();
        params.set('query.term', query);
        params.set('filter.studyType', 'INTERVENTIONAL');
        params.set('filter.phase', phases.join(','));
        params.set('filter.advanced', `AREA[StartDate]RANGE[${dateFrom},MAX]`);
        params.set('pageSize', String(pageSize));
        params.set('fields',
            'NCTId,BriefTitle,OverallStatus,Phase,StartDate,CompletionDate,LeadSponsorName,BriefSummary,StudyType'
        );
        params.set('format', 'json');

        const url = `${API_BASE}?${params.toString()}`;
        const res = await fetch(url);
        if (!res.ok) {
            throw new Error(`CT.gov search failed: ${res.status} ${res.statusText}`);
        }
        const json = await res.json();
        const studies = (json.studies || []).map(s => {
            const id = s.protocolSection?.identificationModule || {};
            const status = s.protocolSection?.statusModule || {};
            const design = s.protocolSection?.designModule || {};
            const sponsor = s.protocolSection?.sponsorCollaboratorsModule?.leadSponsor || {};
            const desc = s.protocolSection?.descriptionModule || {};
            return {
                nct: id.nctId || '',
                title: id.briefTitle || '',
                phase: (design.phases || []).join('/'),
                status: status.overallStatus || '',
                startDate: status.startDateStruct?.date || '',
                completionDate: status.completionDateStruct?.date || '',
                sponsor: sponsor.name || '',
                briefSummary: desc.briefSummary || '',
            };
        });

        cacheSet(cacheKey, studies);
        return studies.filter(c => !excludeNcts.has(c.nct));
    }

    /**
     * Fetch one study's full v2 JSON record.
     */
    async function fetchStudy(nct, opts = {}) {
        const forceRefresh = !!opts.forceRefresh;
        const cacheKey = await sha256Short(`study|${nct}`);
        if (!forceRefresh) {
            const cached = cacheGet(cacheKey);
            if (cached) return cached;
        }
        const url = `${API_BASE}/${encodeURIComponent(nct)}?format=json`;
        const res = await fetch(url);
        if (!res.ok) {
            throw new Error(`CT.gov fetchStudy(${nct}) failed: ${res.status}`);
        }
        const json = await res.json();
        cacheSet(cacheKey, json);
        return json;
    }

    /**
     * Extract a partial trial object from a CT.gov v2 study record.
     * Fields not extractable get `confidence: 'NONE'` and `value: null`
     * so the validation modal can prompt the user to enter manually.
     */
    function extractStructured(study) {
        const ps = study?.protocolSection || {};
        const rs = study?.resultsSection || {};
        const id = ps.identificationModule || {};
        const status = ps.statusModule || {};
        const design = ps.designModule || {};
        const arms = ps.armsInterventionsModule || {};
        const desc = ps.descriptionModule || {};
        const sponsor = ps.sponsorCollaboratorsModule?.leadSponsor || {};

        const out = {
            nct: { value: id.nctId || null, confidence: id.nctId ? 'HIGH' : 'NONE', source: 'CT.gov identificationModule' },
            name: { value: id.briefTitle || null, confidence: id.briefTitle ? 'HIGH' : 'NONE', source: 'CT.gov briefTitle' },
            phase: { value: (design.phases || []).join('/') || null, confidence: design.phases ? 'HIGH' : 'NONE', source: 'CT.gov designModule' },
            year: null, // filled below
            status: { value: status.overallStatus || null, confidence: status.overallStatus ? 'HIGH' : 'NONE', source: 'CT.gov statusModule' },
            sponsor: { value: sponsor.name || null, confidence: sponsor.name ? 'HIGH' : 'NONE', source: 'CT.gov sponsor' },
            briefSummary: { value: desc.briefSummary || null, confidence: 'MEDIUM', source: 'CT.gov briefSummary' },
            interventions: [],
            comparators: [],
            tE: { value: null, confidence: 'NONE', source: '' },
            tN: { value: null, confidence: 'NONE', source: '' },
            cE: { value: null, confidence: 'NONE', source: '' },
            cN: { value: null, confidence: 'NONE', source: '' },
            publishedHR: { value: null, confidence: 'NONE', source: '' },
            hrLCI: { value: null, confidence: 'NONE', source: '' },
            hrUCI: { value: null, confidence: 'NONE', source: '' },
            estimandType: { value: null, confidence: 'NONE', source: '' },
            primaryOutcome: { value: null, confidence: 'NONE', source: '' },
        };

        // Year from start date
        const startDate = status.startDateStruct?.date || '';
        if (startDate) {
            const yMatch = /\b(\d{4})\b/.exec(startDate);
            if (yMatch) {
                out.year = { value: parseInt(yMatch[1], 10), confidence: 'HIGH', source: `CT.gov startDate: ${startDate}` };
            }
        }
        if (!out.year) out.year = { value: null, confidence: 'NONE', source: '' };

        // Interventions / comparators by arm
        const armList = arms.armGroups || [];
        for (const a of armList) {
            const label = a.label || '';
            const desc = a.description || '';
            const type = (a.type || '').toUpperCase();
            const entry = { label, description: desc, type };
            if (type === 'EXPERIMENTAL' || type === 'ACTIVE_COMPARATOR') {
                out.interventions.push(entry);
            } else if (type === 'PLACEBO_COMPARATOR' || type === 'SHAM_COMPARATOR' || type === 'NO_INTERVENTION') {
                out.comparators.push(entry);
            }
        }

        // Participant flow -> per-arm randomization N
        const flow = rs.participantFlowModule || {};
        const flowGroups = flow.groups || [];
        const flowPeriods = flow.periods || [];
        // Take the FIRST period (usually "Overall Study" / randomization)
        if (flowGroups.length >= 2 && flowPeriods.length >= 1) {
            const milestones = flowPeriods[0].milestones || [];
            const startedMs = milestones.find(m => /started|enrolled|randomized/i.test(m.type || ''));
            if (startedMs && startedMs.achievements) {
                // Match achievements to groups by groupId
                const byId = {};
                for (const ach of startedMs.achievements) {
                    byId[ach.groupId] = parseInt(ach.numSubjects, 10);
                }
                // Heuristic: first non-placebo group = treatment, first placebo = control
                const tGroup = flowGroups.find(g => /experimental|treatment|active/i.test(g.title || ''));
                const cGroup = flowGroups.find(g => /placebo|sham|control/i.test(g.title || ''));
                if (tGroup && byId[tGroup.id] != null) {
                    out.tN = { value: byId[tGroup.id], confidence: 'HIGH', source: `CT.gov participantFlow ${tGroup.title}` };
                }
                if (cGroup && byId[cGroup.id] != null) {
                    out.cN = { value: byId[cGroup.id], confidence: 'HIGH', source: `CT.gov participantFlow ${cGroup.title}` };
                }
            }
        }

        // Outcome measures -> primary outcome event counts + statistical analyses
        const outcomes = rs.outcomeMeasuresModule?.outcomeMeasures || [];
        const primary = outcomes.find(o => /primary/i.test(o.type || ''));
        if (primary) {
            out.primaryOutcome = { value: primary.title || '', confidence: 'HIGH', source: 'CT.gov outcomeMeasures (PRIMARY)' };
            // Try to read per-group event counts from the first measurement
            const grps = primary.groups || [];
            const cls = primary.classes || [];
            if (cls.length > 0 && cls[0].categories && cls[0].categories.length > 0) {
                const cat = cls[0].categories[0];
                const measByGroup = {};
                for (const m of (cat.measurements || [])) {
                    const v = parseFloat(m.value);
                    if (Number.isFinite(v)) measByGroup[m.groupId] = v;
                }
                const tGroup = grps.find(g => /experimental|treatment|active/i.test(g.title || ''));
                const cGroup = grps.find(g => /placebo|sham|control/i.test(g.title || ''));
                if (tGroup && measByGroup[tGroup.id] != null) {
                    out.tE = { value: Math.round(measByGroup[tGroup.id]), confidence: 'HIGH', source: `CT.gov outcomeMeasures ${tGroup.title}` };
                }
                if (cGroup && measByGroup[cGroup.id] != null) {
                    out.cE = { value: Math.round(measByGroup[cGroup.id]), confidence: 'HIGH', source: `CT.gov outcomeMeasures ${cGroup.title}` };
                }
            }
            // Statistical analyses -> HR/RR/OR + CI
            const stats = primary.analyses || [];
            if (stats.length > 0) {
                const a = stats[0];
                const param = (a.paramType || '').toUpperCase();
                const knownTypes = { 'HAZARD_RATIO': 'HR', 'RISK_RATIO': 'RR', 'ODDS_RATIO': 'OR', 'MEAN_DIFFERENCE': 'MD' };
                if (knownTypes[param] && Number.isFinite(parseFloat(a.paramValue))) {
                    out.publishedHR = { value: parseFloat(a.paramValue), confidence: 'HIGH', source: `CT.gov analysis ${param}` };
                    out.estimandType = { value: knownTypes[param], confidence: 'HIGH', source: `CT.gov analysis ${param}` };
                    if (Number.isFinite(parseFloat(a.ciLowerLimit))) {
                        out.hrLCI = { value: parseFloat(a.ciLowerLimit), confidence: 'HIGH', source: `CT.gov ciLower` };
                    }
                    if (Number.isFinite(parseFloat(a.ciUpperLimit))) {
                        out.hrUCI = { value: parseFloat(a.ciUpperLimit), confidence: 'HIGH', source: `CT.gov ciUpper` };
                    }
                }
            }
        }

        return out;
    }

    // ---- public API ----
    const api = { searchByPico, fetchStudy, extractStructured };
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = api;
    } else {
        root.LivingMACtgov = api;
    }
})(typeof window !== 'undefined' ? window : globalThis);
