#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Two related fixes for the Analysis tab, applied together:

  1. Manuscript text stuck on placeholder
     ---------------------------------------
     73 apps define `function generateManuscriptText()` but NEVER call it.
     The function writes Methods + Results into #manuscript-text when
     state.results populates, but without an invocation hook, the panel
     stays on "Click 'Generate Output' to create manuscript text." forever.
     The 26 working apps call it right after `GradeProfileEngine.renderTable`.

  2. R cross-validation requires a manual click
     --------------------------------------------
     Static R baseline validation (AnalysisEngine.runRValidation) only
     fires on button click. User wants it to auto-update when analysis
     results change.

Fix: insert BOTH auto-calls right after `GradeProfileEngine.renderTable(...)`
so every AnalysisEngine.run() / results-update automatically refreshes the
manuscript text AND the R validation panel.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

OLD = (
    "                PrismaEngine.renderToElement('prisma-flow-container');\n"
    "                GradeProfileEngine.renderTable('grade-profile-container');\n"
)

NEW = (
    "                PrismaEngine.renderToElement('prisma-flow-container');\n"
    "                GradeProfileEngine.renderTable('grade-profile-container');\n"
    "                // Auto-generate manuscript Methods & Results text\n"
    "                if (typeof generateManuscriptText === 'function') generateManuscriptText();\n"
    "                // Auto-refresh R cross-validation against stored baseline (cheap; static check)\n"
    "                try { if (typeof this.runRValidation === 'function') this.runRValidation(); } catch (e) {}\n"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    # Skip if both auto-calls already present
    if ("Auto-generate manuscript Methods & Results text" in text
        and "Auto-refresh R cross-validation against stored baseline" in text):
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
    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        r = apply_to_file(p, dry_run=args.dry_run)
        if r.startswith("OK"): ok += 1
        elif r.startswith("SKIP"): skip += 1
        else: fail += 1
        if not r.startswith("SKIP"): print(r)
    print(f"\nSummary: {len(targets)} | {ok} fix | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
