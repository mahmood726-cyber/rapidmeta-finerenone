/* eslint-disable */
/**
 * Living-MA augment: UI glue + state.trials integration.
 *
 * Mounts the search-augment panel into the Sources tab (#tab-search)
 * and the curated-only toggle into the Analysis tab (#tab-analysis).
 * Wires LivingMACtgov + LivingMAPubmed + LivingMARegex into the
 * validate-trial modal and the add-trial action.
 *
 * Self-installs on DOMContentLoaded if RapidMeta is present. Idempotent.
 *
 * Per outputs/living_ma_augment_spec.md:
 *  - userAdded:true flag persists alongside the existing trial shape
 *  - dual-reviewer signoff via existing RapidMeta.getReviewerId() flow
 *  - 'Curated only' toggle = the regression detector
 *  - USER-ADDED yellow pill on every render of a userAdded trial
 *  - all string injections screen for the apostrophe trap
 */
(function () {
    'use strict';

    if (typeof window === 'undefined') return;
    if (window._LivingMA && window._LivingMA._installed) return;

    const RX = () => window.LivingMARegex;
    const CTG = () => window.LivingMACtgov;
    const PM = () => window.LivingMAPubmed;

    const NS = {
        _installed: false,
        _curatedOnlyMode: false,
        _candidates: [],

        // --- mount ---
        install() {
            if (this._installed) return;
            if (!window.RapidMeta) {
                console.warn('[LivingMA] RapidMeta not yet available; retrying...');
                setTimeout(() => this.install(), 200);
                return;
            }
            try {
                this._injectCSS();
                this._mountSearchPanel();
                this._mountCuratedToggle();
                this._tagUserAddedTrials();
                this._installed = true;
                console.log('[LivingMA] installed');
            } catch (e) {
                console.error('[LivingMA] install failed:', e);
            }
        },

        _injectCSS() {
            if (document.getElementById('living-ma-css')) return;
            const css = document.createElement('style');
            css.id = 'living-ma-css';
            css.textContent = `
                .living-ma-panel { background: rgba(15,23,42,0.6); border: 1px solid #1e293b; border-radius: 1.5rem; padding: 2rem; margin-top: 1.5rem; }
                .living-ma-panel h3 { font-size: 1rem; font-weight: 700; color: #e2e8f0; margin-bottom: 0.75rem; }
                .living-ma-panel .label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.25rem; }
                .living-ma-btn { background: #0891b2; color: white; padding: 0.5rem 1rem; border-radius: 0.75rem; font-size: 0.8rem; font-weight: 600; border: none; cursor: pointer; }
                .living-ma-btn:hover { background: #0e7490; }
                .living-ma-btn:disabled { background: #475569; cursor: not-allowed; }
                .living-ma-card { background: rgba(30,41,59,0.6); border: 1px solid #334155; border-radius: 1rem; padding: 1rem; margin-top: 0.75rem; }
                .living-ma-card h4 { font-size: 0.85rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.4rem; }
                .living-ma-card .meta { font-size: 0.7rem; color: #94a3b8; }
                .user-added-pill { display: inline-block; background: #fbbf24; color: #1e293b; font-size: 0.625rem; font-weight: 700; padding: 2px 6px; border-radius: 0.375rem; letter-spacing: 0.05em; margin-left: 0.5rem; }
                .living-ma-modal { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 2rem; }
                .living-ma-modal-inner { background: #0f172a; border: 1px solid #334155; border-radius: 1.25rem; max-width: 60rem; width: 100%; max-height: 90vh; overflow-y: auto; }
                .living-ma-modal-header { padding: 1.25rem 1.5rem; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; }
                .living-ma-modal-body { padding: 1.5rem; }
                .living-ma-tabs { display: flex; gap: 0.5rem; border-bottom: 1px solid #1e293b; margin-bottom: 1rem; }
                .living-ma-tab-btn { padding: 0.5rem 1rem; background: transparent; color: #94a3b8; border: none; cursor: pointer; font-size: 0.8rem; font-weight: 600; border-bottom: 2px solid transparent; }
                .living-ma-tab-btn.active { color: #06b6d4; border-bottom-color: #06b6d4; }
                .living-ma-field { margin-bottom: 0.75rem; }
                .living-ma-field label { display: block; font-size: 0.7rem; color: #94a3b8; margin-bottom: 0.25rem; }
                .living-ma-field input { width: 100%; background: #1e293b; border: 1px solid #334155; color: #e2e8f0; padding: 0.4rem 0.6rem; border-radius: 0.5rem; font-size: 0.85rem; }
                .living-ma-field .source { font-size: 0.65rem; color: #64748b; margin-top: 0.2rem; font-style: italic; }
                .conf-HIGH { color: #10b981; font-weight: 600; }
                .conf-MEDIUM { color: #f59e0b; font-weight: 600; }
                .conf-LOW { color: #f97316; font-weight: 600; }
                .conf-NONE { color: #ef4444; font-weight: 600; }
                .living-ma-validation-error { color: #f87171; font-size: 0.75rem; margin-top: 0.5rem; }
                .living-ma-curated-toggle { display: inline-flex; align-items: center; gap: 0.5rem; background: #1e293b; border: 1px solid #334155; padding: 0.4rem 0.8rem; border-radius: 0.75rem; font-size: 0.75rem; color: #e2e8f0; margin-left: 0.5rem; }
                .living-ma-curated-toggle.active { background: #fbbf24; color: #1e293b; border-color: #f59e0b; }
                .living-ma-delta { background: rgba(251,191,36,0.1); border: 1px solid #f59e0b; border-radius: 0.75rem; padding: 0.75rem 1rem; font-size: 0.8rem; color: #fbbf24; margin-top: 0.5rem; }
            `;
            document.head.appendChild(css);
        },

        _mountSearchPanel() {
            const tabSearch = document.getElementById('tab-search');
            if (!tabSearch) return;
            if (document.getElementById('living-ma-search-panel')) return;

            const container = tabSearch.querySelector('.max-w-5xl, .max-w-6xl, .max-w-7xl, [class*="max-w"]');
            const target = container || tabSearch;

            const panel = document.createElement('div');
            panel.id = 'living-ma-search-panel';
            panel.className = 'living-ma-panel';
            panel.innerHTML = `
                <h3>Living-MA: Re-query CT.gov for new RCTs</h3>
                <p class="label">Re-runs the PICO search live against ClinicalTrials.gov v2; surfaces new NCTs not already in the curated pool.</p>
                <div style="display:flex;gap:0.5rem;margin-top:0.75rem;align-items:center;flex-wrap:wrap">
                    <input id="living-ma-query" type="text" placeholder="PICO query (auto-filled)" style="flex:1;min-width:20rem;background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:0.5rem 0.75rem;border-radius:0.5rem;font-size:0.85rem">
                    <input id="living-ma-date-from" type="text" placeholder="2015-01-01" value="2015-01-01" style="width:8rem;background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:0.5rem 0.75rem;border-radius:0.5rem;font-size:0.85rem">
                    <button id="living-ma-search-btn" class="living-ma-btn"><i class="fa-solid fa-magnifying-glass-plus"></i> Search</button>
                    <label style="font-size:0.7rem;color:#94a3b8;display:flex;gap:0.25rem;align-items:center"><input type="checkbox" id="living-ma-force-refresh"> Force refresh</label>
                </div>
                <div id="living-ma-status" style="font-size:0.75rem;color:#94a3b8;margin-top:0.5rem"></div>
                <div id="living-ma-candidates" style="margin-top:1rem"></div>
            `;
            target.appendChild(panel);

            // Pre-fill query from PICO.
            const proto = window.RapidMeta?.state?.protocol || {};
            const queryInput = panel.querySelector('#living-ma-query');
            const seedQuery = proto.query || `${proto.int || ''} ${proto.pop || ''}`.trim().slice(0, 120);
            queryInput.value = seedQuery;

            panel.querySelector('#living-ma-search-btn').addEventListener('click', () => this._runSearch());
        },

        async _runSearch() {
            const status = document.getElementById('living-ma-status');
            const cands = document.getElementById('living-ma-candidates');
            const query = document.getElementById('living-ma-query').value.trim();
            const dateFrom = document.getElementById('living-ma-date-from').value.trim() || '2015-01-01';
            const forceRefresh = document.getElementById('living-ma-force-refresh').checked;
            if (!query) { status.textContent = 'Enter a PICO query first.'; return; }
            const excludeNcts = (window.RapidMeta?.state?.trials || []).map(t => t.id).filter(Boolean);

            status.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching CT.gov v2...';
            cands.innerHTML = '';

            try {
                const results = await CTG().searchByPico(query, { excludeNcts, dateFrom, forceRefresh });
                this._candidates = results;
                if (results.length === 0) {
                    status.textContent = 'No new RCTs matching this query (or all hits already in curated pool).';
                    return;
                }
                status.textContent = `Found ${results.length} candidate trial(s) not already in the dashboard.`;
                results.forEach((c, i) => cands.appendChild(this._renderCandidateCard(c, i)));
            } catch (e) {
                status.innerHTML = `<span style="color:#f87171">Search failed: ${this._escape(e.message)}</span>`;
            }
        },

        _renderCandidateCard(c, idx) {
            const card = document.createElement('div');
            card.className = 'living-ma-card';
            card.innerHTML = `
                <h4>${this._escape(c.title)}</h4>
                <div class="meta">${this._escape(c.nct)} · ${this._escape(c.phase || 'phase ?')} · ${this._escape(c.status || '?')} · sponsor: ${this._escape(c.sponsor || '?')}</div>
                <div class="meta" style="margin-top:0.25rem">Started: ${this._escape(c.startDate)} · Completed: ${this._escape(c.completionDate || 'ongoing')}</div>
                <div style="margin-top:0.5rem">
                    <a href="https://clinicaltrials.gov/study/${this._escape(c.nct)}" target="_blank" rel="noopener" style="color:#06b6d4;font-size:0.75rem">View on CT.gov ↗</a>
                    <button class="living-ma-btn" style="float:right" data-idx="${idx}"><i class="fa-solid fa-magnifying-glass"></i> Validate &amp; Add</button>
                </div>
            `;
            card.querySelector('button[data-idx]').addEventListener('click', () => this._openValidateModal(c));
            return card;
        },

        async _openValidateModal(candidate) {
            const status = document.getElementById('living-ma-status');
            status.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Fetching CT.gov full record + PubMed abstract...';
            let study, structured, pubmed = null;
            try {
                study = await CTG().fetchStudy(candidate.nct);
                structured = CTG().extractStructured(study);
            } catch (e) {
                status.innerHTML = `<span style="color:#f87171">CT.gov fetch failed: ${this._escape(e.message)}</span>`;
                return;
            }
            try {
                pubmed = await PM().findByNct(candidate.nct);
            } catch (e) {
                pubmed = null;
            }

            // If CT.gov has no HR/CI but PubMed has an abstract, regex-extract.
            if (structured.publishedHR.confidence === 'NONE' && pubmed?.abstract) {
                const eff = RX().extractEffectAndCI(pubmed.abstract, structured.primaryOutcome.value || '');
                if (eff) {
                    structured.publishedHR = { value: eff.value, confidence: eff.confidence, source: `PubMed abstract: "${eff.source}"` };
                    structured.hrLCI = { value: eff.lci, confidence: eff.confidence, source: `PubMed abstract: "${eff.source}"` };
                    structured.hrUCI = { value: eff.uci, confidence: eff.confidence, source: `PubMed abstract: "${eff.source}"` };
                    structured.estimandType = { value: /HR|hazard/i.test(eff.kind) ? 'HR' : (/RR|relative risk|risk ratio/i.test(eff.kind) ? 'RR' : 'OR'), confidence: eff.confidence, source: `PubMed abstract: "${eff.source}"` };
                }
            }
            // mITT detector for population.
            const popSource = pubmed?.abstract || structured.briefSummary?.value || '';
            const pop = RX().detectAnalyticPopulation(popSource);
            structured._analyticPopulation = pop;

            status.textContent = '';
            this._renderModal(candidate, structured, pubmed);
        },

        _renderModal(candidate, fields, pubmed) {
            this._closeModal();
            const modal = document.createElement('div');
            modal.className = 'living-ma-modal';
            modal.id = 'living-ma-modal';
            modal.innerHTML = `
                <div class="living-ma-modal-inner">
                    <div class="living-ma-modal-header">
                        <div>
                            <h3 style="font-size:1rem;font-weight:700;color:#e2e8f0">Validate &amp; Add: ${this._escape(candidate.nct)}</h3>
                            <div style="font-size:0.75rem;color:#94a3b8">${this._escape(candidate.title)}</div>
                        </div>
                        <button class="living-ma-btn" id="living-ma-close" style="background:#475569"><i class="fa-solid fa-xmark"></i></button>
                    </div>
                    <div class="living-ma-tabs">
                        <button class="living-ma-tab-btn active" data-tab="meta">1. CT.gov metadata</button>
                        <button class="living-ma-tab-btn" data-tab="outcomes">2. Outcomes</button>
                        <button class="living-ma-tab-btn" data-tab="rob">3. RoB</button>
                        <button class="living-ma-tab-btn" data-tab="signoff">4. Sign-off</button>
                    </div>
                    <div class="living-ma-modal-body" id="living-ma-modal-body"></div>
                </div>
            `;
            document.body.appendChild(modal);

            const close = () => this._closeModal();
            modal.querySelector('#living-ma-close').addEventListener('click', close);
            modal.addEventListener('click', (e) => { if (e.target === modal) close(); });

            const tabs = modal.querySelectorAll('.living-ma-tab-btn');
            const body = modal.querySelector('#living-ma-modal-body');
            const renderTab = (name) => {
                tabs.forEach(b => b.classList.toggle('active', b.dataset.tab === name));
                body.innerHTML = this._renderTabContent(name, candidate, fields, pubmed);
                if (name === 'signoff') this._bindSignoffSubmit(candidate, fields, pubmed);
            };
            tabs.forEach(b => b.addEventListener('click', () => renderTab(b.dataset.tab)));
            renderTab('meta');
        },

        _renderTabContent(name, candidate, fields, pubmed) {
            const f = (k, label, editable) => {
                const v = fields[k] || { value: '', confidence: 'NONE', source: '' };
                const src = v.source ? `<div class="source">source: ${this._escape(v.source)}</div>` : '';
                if (editable) {
                    return `<div class="living-ma-field">
                        <label>${this._escape(label)} <span class="conf-${v.confidence}">[${v.confidence}]</span></label>
                        <input type="text" data-field="${k}" value="${this._escape(String(v.value ?? ''))}">
                        ${src}
                    </div>`;
                }
                return `<div class="living-ma-field">
                    <label>${this._escape(label)} <span class="conf-${v.confidence}">[${v.confidence}]</span></label>
                    <div style="background:#1e293b;border:1px solid #334155;color:#94a3b8;padding:0.4rem 0.6rem;border-radius:0.5rem;font-size:0.85rem">${this._escape(String(v.value ?? '—'))}</div>
                    ${src}
                </div>`;
            };

            if (name === 'meta') {
                return `
                    ${f('nct', 'NCT', false)}
                    ${f('name', 'Trial name', false)}
                    ${f('phase', 'Phase', false)}
                    ${f('year', 'Start year', false)}
                    ${f('status', 'Status', false)}
                    ${f('sponsor', 'Lead sponsor', false)}
                    ${f('primaryOutcome', 'Primary outcome', false)}
                    <div class="living-ma-field"><label>Analytic population (auto-detected)</label>
                    <div style="background:#1e293b;border:1px solid #334155;color:#94a3b8;padding:0.4rem 0.6rem;border-radius:0.5rem;font-size:0.85rem">${this._escape(fields._analyticPopulation || 'unknown')}</div></div>
                    ${pubmed ? `<div class="living-ma-field"><label>PubMed PMID (auto-found)</label><div style="background:#1e293b;border:1px solid #334155;color:#94a3b8;padding:0.4rem 0.6rem;border-radius:0.5rem;font-size:0.85rem">PMID ${this._escape(pubmed.pmid)} — ${this._escape((pubmed.title || '').slice(0, 100))}</div></div>` : `<div class="living-ma-field"><label>PubMed</label><div style="color:#f87171;font-size:0.75rem">No PubMed record auto-found by NCT. Paste a PMID manually if you have one.</div></div>`}
                `;
            }
            if (name === 'outcomes') {
                return `
                    <p style="font-size:0.75rem;color:#94a3b8;margin-bottom:0.5rem">Auto-prefilled from CT.gov outcomeMeasures + statisticalAnalyses where available; from PubMed abstract regex otherwise. Verify and edit; values must satisfy: tE ≤ tN, cE ≤ cN, hrLCI ≤ HR ≤ hrUCI.</p>
                    ${f('tE', 'Treatment events (tE)', true)}
                    ${f('tN', 'Treatment denominator (tN)', true)}
                    ${f('cE', 'Control events (cE)', true)}
                    ${f('cN', 'Control denominator (cN)', true)}
                    ${f('publishedHR', 'Published HR / RR / OR', true)}
                    ${f('hrLCI', 'CI lower (95%)', true)}
                    ${f('hrUCI', 'CI upper (95%)', true)}
                    ${f('estimandType', 'Estimand type (HR/RR/OR)', true)}
                `;
            }
            if (name === 'rob') {
                return `<p style="font-size:0.75rem;color:#94a3b8;margin-bottom:0.5rem">RoB 2.0 across 5 domains. No auto-extract — judgment calls only.</p>
                    ${['D1 Randomization', 'D2 Deviations', 'D3 Missing data', 'D4 Outcome measurement', 'D5 Selection of result'].map((d, i) => `
                        <div class="living-ma-field"><label>${d}</label>
                        <select data-rob="${i}" style="width:100%;background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:0.4rem 0.6rem;border-radius:0.5rem;font-size:0.85rem">
                            <option value="low">Low</option><option value="some">Some concerns</option><option value="high">High</option>
                        </select></div>
                    `).join('')}
                `;
            }
            if (name === 'signoff') {
                const r1 = (window.RapidMeta?.getReviewerId && window.RapidMeta.getReviewerId()) || '';
                return `<p style="font-size:0.75rem;color:#94a3b8;margin-bottom:0.5rem">User-added trials require dual-reviewer sign-off. No skip option.</p>
                    <div class="living-ma-field"><label>Reviewer 1 ID (you)</label><input type="text" id="lma-r1" value="${this._escape(r1)}" placeholder="e.g. mahmood726"></div>
                    <div class="living-ma-field"><label>Reviewer 2 ID (co-signer)</label><input type="text" id="lma-r2" placeholder="e.g. cohort_member_42"></div>
                    <div class="living-ma-field"><label>Sign-off note</label><input type="text" id="lma-note" placeholder="Brief justification"></div>
                    <div id="lma-validation-errors" class="living-ma-validation-error"></div>
                    <button class="living-ma-btn" id="lma-add-btn" style="margin-top:1rem;background:#10b981"><i class="fa-solid fa-plus"></i> Add to dashboard</button>
                `;
            }
            return '';
        },

        _bindSignoffSubmit(candidate, fields, pubmed) {
            const btn = document.getElementById('lma-add-btn');
            if (!btn) return;
            btn.addEventListener('click', () => this._submitAdd(candidate, fields, pubmed));
        },

        _readEditedFields(fields) {
            // Pull values back from the editable inputs in the outcomes tab.
            // (Tab body may have been swapped; we walk the modal for any [data-field] inputs.)
            const out = JSON.parse(JSON.stringify(fields));
            document.querySelectorAll('.living-ma-modal [data-field]').forEach(el => {
                const k = el.dataset.field;
                if (!out[k]) out[k] = { value: null, confidence: 'NONE', source: '' };
                out[k].value = el.value;
            });
            // RoB selects
            const rob = ['low', 'low', 'low', 'low', 'low'];
            document.querySelectorAll('.living-ma-modal [data-rob]').forEach(el => {
                rob[parseInt(el.dataset.rob, 10)] = el.value;
            });
            out._rob = rob;
            return out;
        },

        _submitAdd(candidate, _fields, pubmed) {
            const errEl = document.getElementById('lma-validation-errors');
            errEl.textContent = '';
            const fields = this._readEditedFields(_fields);
            const r1 = (document.getElementById('lma-r1') || {}).value?.trim();
            const r2 = (document.getElementById('lma-r2') || {}).value?.trim();
            const note = (document.getElementById('lma-note') || {}).value?.trim();
            const errs = [];
            if (!r1) errs.push('Reviewer 1 ID required.');
            if (!r2) errs.push('Reviewer 2 ID required.');
            if (r1 && r2 && r1 === r2) errs.push('Reviewer 2 must differ from Reviewer 1.');
            if (!note) errs.push('Sign-off note required.');

            const num = (k) => {
                const v = parseFloat(fields[k]?.value);
                return Number.isFinite(v) ? v : null;
            };
            const tE = num('tE'), tN = num('tN'), cE = num('cE'), cN = num('cN');
            const hr = num('publishedHR'), lci = num('hrLCI'), uci = num('hrUCI');

            if (tE == null || tN == null || cE == null || cN == null) errs.push('tE/tN/cE/cN must all be numeric.');
            if (tE != null && tN != null && tE > tN) errs.push('tE must be ≤ tN.');
            if (cE != null && cN != null && cE > cN) errs.push('cE must be ≤ cN.');
            if (hr == null || lci == null || uci == null) errs.push('publishedHR/hrLCI/hrUCI must all be numeric.');
            if (hr != null && lci != null && uci != null && !(lci <= hr && hr <= uci)) errs.push('CI must bracket the point estimate (hrLCI ≤ HR ≤ hrUCI).');

            // Apostrophe screen on string fields that get injected back into JS.
            try {
                RX().screenForApostrophe(fields.name?.value || '', 'name');
                RX().screenForApostrophe(fields.primaryOutcome?.value || '', 'primaryOutcome');
                RX().screenForApostrophe(note, 'note');
            } catch (e) {
                errs.push(e.message);
            }

            if (errs.length) {
                errEl.innerHTML = errs.map(e => '• ' + this._escape(e)).join('<br>');
                return;
            }

            // Build trial in dashboard's expected shape.
            const trial = {
                id: candidate.nct,
                status: 'include',
                userAdded: true,
                _addedAt: new Date().toISOString(),
                _addedBy: r1,
                _coSignedBy: r2,
                _coSignedAt: new Date().toISOString(),
                _addNote: note,
                data: {
                    name: fields.name?.value || candidate.title,
                    phase: (fields.phase?.value || 'III').replace(/^PHASE/i, ''),
                    year: parseInt(fields.year?.value, 10) || (new Date().getFullYear()),
                    pmid: pubmed?.pmid || '',
                    tE, tN, cE, cN,
                    publishedHR: hr,
                    hrLCI: lci,
                    hrUCI: uci,
                    pubHR: hr,
                    pubHR_LCI: lci,
                    pubHR_UCI: uci,
                    estimandType: fields.estimandType?.value || 'HR',
                    group: `User-added ${candidate.nct} via Living-MA augment`,
                    rob: fields._rob || ['low','low','low','low','low'],
                    snippet: pubmed ? `PubMed PMID ${pubmed.pmid}` : `CT.gov ${candidate.nct}`,
                    sourceUrl: pubmed ? `https://pubmed.ncbi.nlm.nih.gov/${pubmed.pmid}/` : `https://clinicaltrials.gov/study/${candidate.nct}`,
                    ctgovUrl: `https://clinicaltrials.gov/study/${candidate.nct}`,
                    allOutcomes: [{
                        shortLabel: 'MACE',
                        title: fields.primaryOutcome?.value || 'Primary outcome',
                        type: 'PRIMARY',
                        matchScore: 80,
                        effect: hr,
                        lci: lci,
                        uci: uci,
                        estimandType: fields.estimandType?.value || 'HR',
                        pubHR: hr, pubHR_LCI: lci, pubHR_UCI: uci,
                    }],
                },
            };

            // Push to state.trials and persist.
            window.RapidMeta.state.trials.push(trial);
            try { window.RapidMeta.save && window.RapidMeta.save(); } catch (e) {}
            this._closeModal();

            // Notify and refresh.
            const status = document.getElementById('living-ma-status');
            if (status) status.innerHTML = `<span style="color:#10b981">Added ${this._escape(candidate.nct)} to dashboard. Switch to Analysis to recompute.</span>`;
            this._tagUserAddedTrials();
            // Trigger re-render via existing screen filter rerun if available.
            try { window.RapidMeta.syncUI && window.RapidMeta.syncUI(); } catch (e) {}
        },

        _closeModal() {
            const m = document.getElementById('living-ma-modal');
            if (m) m.remove();
        },

        _mountCuratedToggle() {
            const tabAnalysis = document.getElementById('tab-analysis');
            if (!tabAnalysis) return;
            if (document.getElementById('living-ma-curated-toggle-btn')) return;
            const toggle = document.createElement('button');
            toggle.id = 'living-ma-curated-toggle-btn';
            toggle.className = 'living-ma-curated-toggle';
            toggle.innerHTML = '<i class="fa-solid fa-filter"></i> Curated only';
            toggle.title = 'Toggle to exclude user-added trials and verify the curated-only conclusion';
            toggle.addEventListener('click', () => this._toggleCuratedOnly(toggle));
            // Mount it inside the analysis tab header area; fallback to top of section.
            const target = tabAnalysis.querySelector('h2, .glass') || tabAnalysis;
            target.appendChild(toggle);
        },

        _toggleCuratedOnly(btn) {
            this._curatedOnlyMode = !this._curatedOnlyMode;
            btn.classList.toggle('active', this._curatedOnlyMode);
            // Hide user-added trials by setting status='exclude' temporarily.
            const trials = window.RapidMeta?.state?.trials || [];
            trials.forEach(t => {
                if (!t.userAdded) return;
                if (this._curatedOnlyMode) {
                    t._priorStatus = t.status;
                    t.status = 'exclude';
                } else if (t._priorStatus) {
                    t.status = t._priorStatus;
                    delete t._priorStatus;
                }
            });
            // Banner
            const tabAnalysis = document.getElementById('tab-analysis');
            let banner = document.getElementById('living-ma-delta');
            if (!banner) {
                banner = document.createElement('div');
                banner.id = 'living-ma-delta';
                banner.className = 'living-ma-delta';
                tabAnalysis.insertBefore(banner, tabAnalysis.firstChild);
            }
            const userAddedCount = trials.filter(t => t.userAdded).length;
            banner.style.display = this._curatedOnlyMode && userAddedCount > 0 ? 'block' : 'none';
            if (this._curatedOnlyMode) {
                banner.innerHTML = `<i class="fa-solid fa-circle-info"></i> Curated-only mode: excluding ${userAddedCount} user-added trial(s). The pooled estimate now reflects only the pre-curated pool.`;
            }
            // Re-run analysis through existing entry point.
            try {
                if (window.RapidMeta.runAnalysis) window.RapidMeta.runAnalysis();
                else if (window.RapidMeta.analyze) window.RapidMeta.analyze();
                else if (window.RapidMeta.switchTab) window.RapidMeta.switchTab('analysis');
            } catch (e) { console.warn('[LivingMA] re-run failed:', e); }
        },

        _tagUserAddedTrials() {
            // Add USER-ADDED pill anywhere a trial id appears.
            const trials = window.RapidMeta?.state?.trials || [];
            const userAddedIds = new Set(trials.filter(t => t.userAdded).map(t => t.id));
            // Add a body-level data attribute so downstream renders can style.
            document.body.dataset.livingMaUserAdded = userAddedIds.size;
            // Best-effort: walk for elements with data-trial-id attribute and pill them.
            document.querySelectorAll('[data-trial-id]').forEach(el => {
                if (!userAddedIds.has(el.dataset.trialId)) return;
                if (el.querySelector('.user-added-pill')) return;
                const pill = document.createElement('span');
                pill.className = 'user-added-pill';
                pill.textContent = 'USER-ADDED';
                el.appendChild(pill);
            });
        },

        _escape(s) {
            return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
        },
    };

    window._LivingMA = NS;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => NS.install());
    } else {
        // RapidMeta may not yet be fully constructed; defer to next tick + retry.
        setTimeout(() => NS.install(), 100);
    }
})();
