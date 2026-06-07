"""Fix the duplicate-outcome dropdown across all generated meta apps.

Bug: populateOutcomeSelector renders a synthetic "default" option plus one
option per distinct outcome shortLabel. outcomeLabel("default") returns the
highest-count outcome's title, which is identical to that outcome's own named
option -> the SAME outcome text appears twice in #outcome-selector. On
AUTO_FULL_REVIEW apps (all shortLabel "MACE") it is blatant.

Fix: dedupe the option list by rendered label (first occurrence wins), so two
keys that resolve to the same display text collapse to one <option>.

Idempotent (skips files already carrying the dedupe token). --dry-run prints
counts only. Reports files that contain populateOutcomeSelector but whose
render expression did not match (for manual review).
"""
from __future__ import annotations
import argparse, glob, io, os, re, sys

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEDUP_TOKEN = "findIndex(q=>q[1]===p[1])"

PAT = re.compile(
    r'sel\.innerHTML\s*=\s*\[\.\.\.allLabels\]\.map\(\s*\(?\s*(\w+)\s*\)?\s*=>\s*'
    r'`<option value="\$\{escapeHtml\(\1\)\}"\$\{\s*\1\s*===\s*(\w+)\s*\?\s*" selected"\s*:\s*""\s*\}>'
    r'\$\{escapeHtml\(this\.outcomeLabel\(\1\)\)\}</option>`\s*\)\.join\(\s*""\s*\)'
)
REPL = (r'sel.innerHTML=[...allLabels].map(\g<1>=>[\g<1>,this.outcomeLabel(\g<1>)])'
        r'.filter((p,i,a)=>a.findIndex(q=>q[1]===p[1])===i)'
        r'.map(p=>`<option value="${escapeHtml(p[0])}"${p[0]===\g<2>?" selected":""}>'
        r'${escapeHtml(p[1])}</option>`).join("")')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--glob", default="*.html", help="file glob (relative to repo root)")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(HERE, args.glob)))
    fixed = already = nomatch = nopop = 0
    nomatch_files = []
    for p in files:
        s = io.open(p, encoding="utf-8", errors="replace").read()
        if "populateOutcomeSelector" not in s:
            nopop += 1
            continue
        if DEDUP_TOKEN in s:
            already += 1
            continue
        new, n = PAT.subn(REPL, s, count=1)
        if n == 0:
            nomatch += 1
            nomatch_files.append(os.path.basename(p))
            continue
        if not args.dry_run:
            io.open(p, "w", encoding="utf-8", newline="").write(new)
        fixed += 1

    print(f"Files scanned          : {len(files)}")
    print(f"{'Would fix' if args.dry_run else 'Fixed'}              : {fixed}")
    print(f"Already deduped        : {already}")
    print(f"Has populate, no match : {nomatch}")
    print(f"No populateOutcome     : {nopop}")
    if nomatch_files:
        print(f"\nUnmatched (manual review, {len(nomatch_files)}):")
        print("   " + ", ".join(nomatch_files[:30]) + (" ..." if len(nomatch_files) > 30 else ""))


if __name__ == "__main__":
    main()
