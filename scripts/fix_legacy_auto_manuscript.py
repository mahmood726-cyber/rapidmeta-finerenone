#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Bespoke fix for the 3 legacy-template apps (COLCHICINE_CVD_REVIEW.html,
GLP1_CVOT_REVIEW.html, SGLT2_HF_REVIEW.html) that fell outside
fix_auto_manuscript_and_rval.py's anchor pattern.

These 3 apps have AnalysisEngine.run() but:
  - The standard anchor (PrismaEngine.renderToElement + GradeProfileEngine.renderTable
    as back-to-back calls) doesn't exist — they have these calls in different
    flows (GradeProfileEngine.renderTable is only in a button onclick, not
    auto-called at analysis time).
  - generateManuscriptText() IS defined and IS called — but only from inside
    ReportEngine.generate(), which fires when the user clicks "Generate
    Synthesis". Until that click, manuscript-text panel stays on placeholder.
  - runRValidation() similarly waits for a manual click.

All 3 apps share a common line at the end of AnalysisEngine.run():
    // Auto-regenerate report if it was previously generated
    const reportEl = document.getElementById('report-content');
    if (reportEl && !reportEl.classList.contains('hidden')) ReportEngine.generate();

Fix: inject the two auto-calls IMMEDIATELY AFTER this existing block, still
inside AnalysisEngine.run().
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")
LEGACY_APPS = ['COLCHICINE_CVD_REVIEW.html', 'GLP1_CVOT_REVIEW.html', 'SGLT2_HF_REVIEW.html']

OLD = (
    "                // Auto-regenerate report if it was previously generated\n"
    "                const reportEl = document.getElementById('report-content');\n"
    "                if (reportEl && !reportEl.classList.contains('hidden')) ReportEngine.generate();\n"
)

NEW = (
    "                // Auto-regenerate report if it was previously generated\n"
    "                const reportEl = document.getElementById('report-content');\n"
    "                if (reportEl && !reportEl.classList.contains('hidden')) ReportEngine.generate();\n"
    "                // Auto-generate manuscript Methods & Results text (no manual click needed)\n"
    "                try { if (typeof generateManuscriptText === 'function') generateManuscriptText(); } catch (e) {}\n"
    "                // Auto-refresh R cross-validation against stored baseline (cheap; static check)\n"
    "                try { if (typeof this.runRValidation === 'function') this.runRValidation(); } catch (e) {}\n"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if "Auto-generate manuscript Methods & Results text (no manual click needed)" in text:
        return f"SKIP {path.name}: already-migrated"
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    if work.count(OLD) != 1:
        return f"FAIL {path.name}: OLD matched {work.count(OLD)} times (expected 1)"
    work = work.replace(OLD, NEW, 1)
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
    ok = skip = fail = 0
    for name in LEGACY_APPS:
        r = apply_to_file(ROOT / name, dry_run=args.dry_run)
        print(r)
        if r.startswith("OK"): ok += 1
        elif r.startswith("SKIP"): skip += 1
        else: fail += 1
    print(f"\nSummary: {len(LEGACY_APPS)} | {ok} fix | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
