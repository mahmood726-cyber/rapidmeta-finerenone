#!/usr/bin/env python3
"""Propagate the EvidenceHydrator namespace + init hook (CFTR commit) across
all 98 other RapidMeta _REVIEW.html apps. Idempotent — guarded by sentinel
'const EvidenceHydrator = {'. Anchors on the AbstractHydrator comment block
which is universal across all apps post-Rayyan migration.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

ANCHOR = "        /* ── Abstract hydration: Rayyan-style rich abstracts in Screening tab."

# The EvidenceHydrator namespace, pasted byte-for-byte from CFTR.
EVIDENCE_HYDRATOR = """        /* ── Evidence hydration: CT.gov-derived structured evidence items
           (allocation/masking/eligibility/baseline characteristics) populate
           the Demographics + Risk of Bias + Data Entry panels in the Extraction
           tab. Without this, those panels show "No source extracts available.
           Manual entry required" because realData[*].evidence ships empty.
           Cache: localStorage keyed by NCT, 90-day TTL.
           Sync pass applies cached evidence before first render; async pass
           fetches from CT.gov v2 API in parallel and re-renders on arrival. ── */
        const EvidenceHydrator = {
            CACHE_PREFIX: 'rm_evidence_v1_',
            CACHE_TTL_MS: 90 * 24 * 60 * 60 * 1000,

            cacheKey(nct) { return this.CACHE_PREFIX + String(nct).trim(); },

            getCached(nct) {
                try {
                    const raw = localStorage.getItem(this.cacheKey(nct));
                    if (!raw) return null;
                    const { items, fetchedAt } = JSON.parse(raw);
                    if (!Array.isArray(items) || !fetchedAt) return null;
                    if (Date.now() - fetchedAt > this.CACHE_TTL_MS) return null;
                    return items;
                } catch (e) { return null; }
            },

            setCached(nct, items) {
                try {
                    localStorage.setItem(this.cacheKey(nct), JSON.stringify({ items, fetchedAt: Date.now() }));
                } catch (e) { /* quota exceeded — ignore */ }
            },

            /* Fetch CT.gov v2 study record (design + eligibility + baseline)
               and parse into evidence items. Returns [] on failure. */
            async fetchCtgovEvidence(nct) {
                try {
                    const fields = 'protocolSection.designModule,protocolSection.eligibilityModule,resultsSection.baselineCharacteristicsModule';
                    const url = `https://clinicaltrials.gov/api/v2/studies/${encodeURIComponent(nct)}?fields=${fields}&format=json`;
                    const r = await fetch(url);
                    if (!r.ok) return [];
                    const data = await r.json();
                    return this.parseToEvidenceItems(nct, data);
                } catch (e) { return []; }
            },

            parseToEvidenceItems(nct, data) {
                const items = [];
                const proto = data.protocolSection || {};
                const results = data.resultsSection || {};

                /* Design — allocation + masking. Informs RoB Domain 2 (deviations)
                   and the blinding sub-domain. */
                const design = proto.designModule || {};
                const masking = design.maskingInfo || {};
                if (design.allocation || masking.masking) {
                    const allocText = design.allocation || 'NOT REPORTED';
                    const maskText = masking.masking || 'NOT REPORTED';
                    const whoMasked = (masking.whoMasked || []).join(', ');
                    items.push({
                        label: 'Design — Allocation & masking',
                        source: `CT.gov ${nct} protocolSection.designModule`,
                        text: `Allocation: ${allocText}. Masking: ${maskText}${whoMasked ? ' (' + whoMasked + ')' : ''}.`,
                        highlights: [allocText, maskText, whoMasked].filter(Boolean)
                    });
                }

                /* Eligibility — sex + age range. Informs Population transitivity. */
                const elig = proto.eligibilityModule || {};
                if (elig.minimumAge || elig.maximumAge || elig.sex) {
                    items.push({
                        label: 'Eligibility — Population window',
                        source: `CT.gov ${nct} protocolSection.eligibilityModule`,
                        text: `Sex: ${elig.sex || 'ALL'}. Age range: ${elig.minimumAge || 'N/A'} to ${elig.maximumAge || 'N/A'}.`,
                        highlights: [elig.sex, elig.minimumAge, elig.maximumAge].filter(Boolean)
                    });
                }

                /* Baseline characteristics — per-arm demographic measurements
                   (age, sex, race). Informs Demographics panel. */
                const bcm = results.baselineCharacteristicsModule || {};
                const groups = bcm.groups || [];
                for (const measure of (bcm.measures || [])) {
                    const title = measure.title || '';
                    if (!/age|sex|gender|female|male|race|ethnic|baseline/i.test(title)) continue;
                    const groupValues = [];
                    for (const cls of (measure.classes || [])) {
                        for (const cat of (cls.categories || [])) {
                            for (const meas of (cat.measurements || [])) {
                                const grp = groups.find(g => g.id === meas.groupId);
                                const grpName = grp?.title || meas.groupId;
                                if (meas.value != null) groupValues.push(`${grpName}: ${meas.value}`);
                            }
                        }
                    }
                    if (groupValues.length > 0) {
                        items.push({
                            label: `Baseline — ${title}`.slice(0, 80),
                            source: `CT.gov ${nct} baselineCharacteristicsModule`,
                            text: groupValues.join('; ') + (measure.unitOfMeasure ? ` (${measure.unitOfMeasure})` : ''),
                            highlights: groupValues.map(v => v.split(': ')[1]).filter(Boolean).slice(0, 6)
                        });
                    }
                }

                return items;
            },

            /* Merge new items into trial.data.evidence, avoiding duplicates by
               (label + source). Returns true if anything was added. */
            applyToTrial(trial, items) {
                if (!trial || !Array.isArray(items) || items.length === 0) return false;
                if (!trial.data) trial.data = {};
                const existing = Array.isArray(trial.data.evidence) ? trial.data.evidence : [];
                const seen = new Set(existing.map(e => `${e?.label}|${e?.source}`));
                const merged = [...existing];
                let added = 0;
                for (const item of items) {
                    const key = `${item?.label}|${item?.source}`;
                    if (!seen.has(key)) { merged.push(item); seen.add(key); added++; }
                }
                if (added === 0) return false;
                trial.data.evidence = merged;
                return true;
            },

            async hydrateTrials(trials) {
                if (!Array.isArray(trials) || trials.length === 0) return;
                let anyChanged = false;

                /* Sync cache pass */
                trials.forEach(t => {
                    if (!t?.id?.startsWith('NCT')) return;
                    const cached = this.getCached(t.id);
                    if (cached && this.applyToTrial(t, cached)) anyChanged = true;
                });
                if (anyChanged) {
                    try { ExtractEngine.render?.(); } catch (e) {}
                    try { RapidMeta.save?.(); } catch (e) {}
                }

                /* Async fetch pass — one concurrent call per trial */
                const pending = trials.filter(t => t?.id?.startsWith('NCT') && !this.getCached(t.id));
                if (pending.length === 0) return;

                await Promise.allSettled(pending.map(async (trial) => {
                    try {
                        const items = await this.fetchCtgovEvidence(trial.id);
                        if (!items || items.length === 0) return;
                        this.setCached(trial.id, items);
                        if (this.applyToTrial(trial, items)) {
                            try { ExtractEngine.render?.(); } catch (e) {}
                            try { RapidMeta.save?.(); } catch (e) {}
                        }
                    } catch (e) { /* swallow — trial keeps its empty evidence */ }
                }));
            }
        };

"""

INIT_HOOK_OLD = "                try { AbstractHydrator.hydrateTrials(this.state.trials); } catch (e) {}"
INIT_HOOK_NEW = (
    "                try { AbstractHydrator.hydrateTrials(this.state.trials); } catch (e) {}\n"
    "                /* CT.gov evidence hydration: pulls allocation/masking/eligibility/baseline\n"
    "                   characteristics into trial.data.evidence so Demographics + RoB panels\n"
    "                   stop showing \"No source extracts available\". Cached in localStorage. */\n"
    "                try { EvidenceHydrator.hydrateTrials(this.state.trials); } catch (e) {}"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if "const EvidenceHydrator = {" in text:
        return f"SKIP {path.name}: already-migrated"
    if ANCHOR not in text:
        return f"SKIP {path.name}: no AbstractHydrator anchor (run propagate_rayyan_abstracts.py first)"

    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text

    # Edit 1: insert EvidenceHydrator immediately before AbstractHydrator
    if work.count(ANCHOR) != 1:
        return f"FAIL {path.name}: ANCHOR matched {work.count(ANCHOR)} times (expected 1)"
    work = work.replace(ANCHOR, EVIDENCE_HYDRATOR + ANCHOR, 1)

    # Edit 2: hook init() after the existing AbstractHydrator call
    if work.count(INIT_HOOK_OLD) != 1:
        return f"FAIL {path.name}: INIT_HOOK_OLD matched {work.count(INIT_HOOK_OLD)} times (expected 1)"
    work = work.replace(INIT_HOOK_OLD, INIT_HOOK_NEW, 1)

    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}: +{len(work) - len(text.replace(chr(13)+chr(10), chr(10)) if crlf else text)} chars"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        result = apply_to_file(p, dry_run=args.dry_run)
        if result.startswith("OK"): ok += 1
        elif result.startswith("SKIP"): skip += 1
        else: fail += 1
        if not result.startswith("SKIP"):
            print(result)
    print(f"\nSummary: {len(targets)} files | {ok} migrate | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
