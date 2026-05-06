#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Propagate the applyOutcomeScope `undefined`-counts fix (CFTR) to all
other _REVIEW.html apps. Three byte-exact edits per file, idempotent.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SENTINEL = "// Preserve trial-level tE/cE when the outcome entry omits them"

EDIT1_OLD = (
    "                    if (outcomeKey === 'default') {\n"
    "                        const def = outcomes.find(o => o.shortLabel === 'MACE');\n"
    "                        if (def) {\n"
    "                            t.data.tE = def.tE;\n"
    "                            t.data.cE = def.cE;\n"
    "                            if (def.nT != null) t.data.tN = def.nT;\n"
    "                            if (def.nC != null) t.data.cN = def.nC;"
)
EDIT1_NEW = (
    "                    if (outcomeKey === 'default') {\n"
    "                        const def = outcomes.find(o => o.shortLabel === 'MACE');\n"
    "                        if (def) {\n"
    "                            // Preserve trial-level tE/cE when the outcome entry omits them\n"
    "                            // (e.g. MD-scale outcomes like ppFEV1 have no event counts; they\n"
    "                            // carry pubHR/pubHR_LCI/pubHR_UCI only). Nullish-coalesce so 0 is kept.\n"
    "                            t.data.tE = def.tE ?? t.data.tE;\n"
    "                            t.data.cE = def.cE ?? t.data.cE;\n"
    "                            if (def.nT != null) t.data.tN = def.nT;\n"
    "                            if (def.nC != null) t.data.cN = def.nC;"
)

EDIT2_OLD = (
    "                    } else {\n"
    "                        const oc = outcomes.find(o => o.shortLabel === outcomeKey);\n"
    "                        if (oc) {\n"
    "                            t.data.tE = oc.tE;\n"
    "                            t.data.cE = oc.cE;\n"
    "                            // Per-outcome denominator override (e.g., safety analysis set for hyperkalemia)\n"
    "                            if (oc.nT != null) t.data.tN = oc.nT;\n"
    "                            if (oc.nC != null) t.data.cN = oc.nC;"
)
EDIT2_NEW = (
    "                    } else {\n"
    "                        const oc = outcomes.find(o => o.shortLabel === outcomeKey);\n"
    "                        if (oc) {\n"
    "                            // Preserve trial-level tE/cE when the outcome entry omits them\n"
    "                            // (MD-scale outcomes carry no event counts).\n"
    "                            t.data.tE = oc.tE ?? t.data.tE;\n"
    "                            t.data.cE = oc.cE ?? t.data.cE;\n"
    "                            // Per-outcome denominator override (e.g., safety analysis set for hyperkalemia)\n"
    "                            if (oc.nT != null) t.data.tN = oc.nT;\n"
    "                            if (oc.nC != null) t.data.cN = oc.nC;"
)

EDIT3_OLD = (
    "                    const selectionEvidence = {\n"
    "                        label: 'Outcome Selected For Pooling',\n"
    "                        source: 'Outcome selector (analysis scope)',\n"
    "                        text: `Current selection for this trial: ${this.outcomeLabel(selectedOutcome.shortLabel ?? outcomeKey)} (${selectedOutcome.type ?? 'N/A'}) with counts ${t.data.tE}/${t.data.tN} vs ${t.data.cE}/${t.data.cN}. Note: other source extracts below may describe a different endpoint.`,\n"
    "                        highlights: [String(t.data.tE), String(t.data.tN), String(t.data.cE), String(t.data.cN), this.outcomeLabel(selectedOutcome.shortLabel ?? outcomeKey)]\n"
    "                    };"
)
EDIT3_NEW = (
    "                    // Build an outcome-scale-aware evidence sentence: 2x2 counts for\n"
    "                    // binary outcomes, published effect estimate + CI for HR/MD/ratio-scale\n"
    "                    // outcomes (e.g. ppFEV1 MD, rate-ratio), so we never render \"undefined\".\n"
    "                    const _hasCounts = Number.isFinite(Number(t.data.tE)) && Number.isFinite(Number(t.data.cE));\n"
    "                    const _pubEff = selectedOutcome.pubHR ?? t.data.pubHR ?? null;\n"
    "                    const _pubLo  = selectedOutcome.pubHR_LCI ?? t.data.pubHR_LCI ?? null;\n"
    "                    const _pubHi  = selectedOutcome.pubHR_UCI ?? t.data.pubHR_UCI ?? null;\n"
    "                    const _effLabel = selectedOutcome.estimandType ?? t.data.estimandType ?? (_pubEff != null ? 'HR' : '');\n"
    "                    let _selectionDetail;\n"
    "                    if (_hasCounts && (t.data.tE > 0 || t.data.cE > 0)) {\n"
    "                        _selectionDetail = `counts ${t.data.tE}/${t.data.tN} vs ${t.data.cE}/${t.data.cN}`;\n"
    "                    } else if (_pubEff != null && _pubLo != null && _pubHi != null) {\n"
    "                        _selectionDetail = `${_effLabel || 'effect'} ${_pubEff} (95% CI ${_pubLo} to ${_pubHi}); n = ${t.data.tN} vs ${t.data.cN}`;\n"
    "                    } else {\n"
    "                        _selectionDetail = `n = ${t.data.tN} vs ${t.data.cN}`;\n"
    "                    }\n"
    "                    const selectionEvidence = {\n"
    "                        label: 'Outcome Selected For Pooling',\n"
    "                        source: 'Outcome selector (analysis scope)',\n"
    "                        text: `Current selection for this trial: ${this.outcomeLabel(selectedOutcome.shortLabel ?? outcomeKey)} (${selectedOutcome.type ?? 'N/A'}) with ${_selectionDetail}. Note: other source extracts below may describe a different endpoint.`,\n"
    "                        highlights: [String(t.data.tN), String(t.data.cN), this.outcomeLabel(selectedOutcome.shortLabel ?? outcomeKey), _pubEff != null ? String(_pubEff) : null].filter(Boolean)\n"
    "                    };"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if SENTINEL in text:
        return f"SKIP {path.name}: already-migrated"
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    for label, old, new in (("EDIT1-default-branch", EDIT1_OLD, EDIT1_NEW),
                            ("EDIT2-named-branch",   EDIT2_OLD, EDIT2_NEW),
                            ("EDIT3-evidence-text",  EDIT3_OLD, EDIT3_NEW)):
        if work.count(old) != 1:
            return f"FAIL {path.name}: {label} matched {work.count(old)} (expected 1)"
        work = work.replace(old, new, 1)
    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply): ap.error("pass --dry-run or --apply")
    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        r = apply_to_file(p, dry_run=args.dry_run)
        if r.startswith("OK"): ok += 1
        elif r.startswith("SKIP"): skip += 1
        else: fail += 1
        if not r.startswith("SKIP"): print(r)
    print(f"\nSummary: {len(targets)} | {ok} migrate | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
