/* eslint-disable */
/**
 * Living-MA augment: PubMed E-utilities wrapper.
 *
 * Locked decision (2026-04-30): auto-search PubMed by NCT first
 * (`esearch.fcgi?db=pubmed&term=<NCT>[si]`). On hit, efetch the
 * abstract. On zero hits, surface a "paste a PMID/DOI" affordance to
 * the user.
 *
 * Public API:
 *   LivingMAPubmed.findByNct(nct)         -> Promise<{pmid, title, abstract} | null>
 *   LivingMAPubmed.fetchAbstract(pmid)    -> Promise<{pmid, title, abstract}>
 *
 * Cache: same 24h policy as ctgov_fetch (key = `livingma_pubmed_<sha>`).
 *
 * NCBI E-utilities are public, no API key required for low volume
 * (~3 req/sec). For higher throughput (>3 req/s) an api_key would
 * be required, but for one dashboard's worth of trials we're far
 * below that.
 */
(function (root) {
    'use strict';

    const ESEARCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi';
    const EFETCH  = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi';
    const ESUMMARY = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi';
    const CACHE_TTL_MS = 24 * 60 * 60 * 1000;
    const CACHE_PREFIX = 'livingma_pubmed_';

    async function sha256Short(s) {
        try {
            const buf = new TextEncoder().encode(s);
            const hashBuf = await crypto.subtle.digest('SHA-256', buf);
            return Array.from(new Uint8Array(hashBuf))
                .slice(0, 8).map(b => b.toString(16).padStart(2, '0')).join('');
        } catch (e) {
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
        } catch (e) { return null; }
    }
    function cacheSet(key, value) {
        try { localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ t: Date.now(), v: value })); }
        catch (e) {}
    }

    /**
     * Parse the abstract text out of PubMed's XML efetch response.
     * The XML has <Article><ArticleTitle>...</ArticleTitle>
     * <Abstract><AbstractText>...</AbstractText>...</Abstract></Article>.
     * Some abstracts have multiple <AbstractText Label="BACKGROUND">
     * sections; we concatenate them with section labels preserved.
     */
    function parseEfetchXml(xmlText) {
        // Use DOMParser if available (browser); else lightweight regex.
        let title = '';
        let abstract = '';
        if (typeof DOMParser !== 'undefined') {
            const dom = new DOMParser().parseFromString(xmlText, 'text/xml');
            const t = dom.querySelector('ArticleTitle');
            if (t) title = t.textContent.trim();
            const sections = dom.querySelectorAll('AbstractText');
            const parts = [];
            sections.forEach(s => {
                const label = s.getAttribute('Label');
                const txt = s.textContent.trim();
                if (label) parts.push(`${label}: ${txt}`);
                else parts.push(txt);
            });
            abstract = parts.join('\n\n');
        } else {
            // Regex fallback for Node tests.
            const tMatch = /<ArticleTitle[^>]*>([\s\S]*?)<\/ArticleTitle>/.exec(xmlText);
            if (tMatch) title = tMatch[1].replace(/<[^>]+>/g, '').trim();
            const aRe = /<AbstractText(?:\s+Label="([^"]*)")?[^>]*>([\s\S]*?)<\/AbstractText>/g;
            const parts = [];
            let m;
            while ((m = aRe.exec(xmlText)) !== null) {
                const label = m[1] || '';
                const txt = m[2].replace(/<[^>]+>/g, '').trim();
                parts.push(label ? `${label}: ${txt}` : txt);
            }
            abstract = parts.join('\n\n');
        }
        return { title, abstract };
    }

    /**
     * Find the PubMed record for an NCT ID.
     * @returns {Promise<{pmid, title, abstract} | null>}
     */
    async function findByNct(nct, opts = {}) {
        const forceRefresh = !!opts.forceRefresh;
        const cacheKey = await sha256Short(`bynct|${nct}`);
        if (!forceRefresh) {
            const cached = cacheGet(cacheKey);
            if (cached !== null && cached !== undefined) return cached;
        }

        const searchUrl = `${ESEARCH}?db=pubmed&term=${encodeURIComponent(nct)}%5Bsi%5D&retmode=json`;
        const sRes = await fetch(searchUrl);
        if (!sRes.ok) {
            throw new Error(`PubMed esearch failed: ${sRes.status}`);
        }
        const sJson = await sRes.json();
        const idList = sJson?.esearchresult?.idlist || [];
        if (idList.length === 0) {
            cacheSet(cacheKey, null);
            return null;
        }
        // Heuristic: prefer the lowest PMID (oldest publication = primary).
        const pmid = idList.sort((a, b) => parseInt(a, 10) - parseInt(b, 10))[0];
        const rec = await fetchAbstract(pmid, opts);
        cacheSet(cacheKey, rec);
        return rec;
    }

    /**
     * Fetch a PubMed record's title + abstract by PMID.
     */
    async function fetchAbstract(pmid, opts = {}) {
        const forceRefresh = !!opts.forceRefresh;
        const cacheKey = await sha256Short(`pmid|${pmid}`);
        if (!forceRefresh) {
            const cached = cacheGet(cacheKey);
            if (cached) return cached;
        }
        const url = `${EFETCH}?db=pubmed&id=${encodeURIComponent(pmid)}&rettype=abstract&retmode=xml`;
        const res = await fetch(url);
        if (!res.ok) {
            throw new Error(`PubMed efetch ${pmid} failed: ${res.status}`);
        }
        const xml = await res.text();
        const { title, abstract } = parseEfetchXml(xml);
        const rec = { pmid: String(pmid), title, abstract };
        cacheSet(cacheKey, rec);
        return rec;
    }

    const api = { findByNct, fetchAbstract, parseEfetchXml };
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = api;
    } else {
        root.LivingMAPubmed = api;
    }
})(typeof window !== 'undefined' ? window : globalThis);
