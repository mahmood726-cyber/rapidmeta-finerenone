"""Fix `evData.map(ev => ...)` failing on null entries in renderEvidencePanels.

Bug: evData arrays sometimes contain null entries (likely from JSON
serialization of incomplete evidence stubs). The .map callback then accesses
`ev.text` and throws TypeError, breaking the Extraction tab.

Fix: insert `.filter(Boolean)` between `evData` and `.map` so the callback
never receives null/undefined. Idempotent — running twice is a no-op because
the second run sees `evData.filter(Boolean).map(...)` and won't double-apply.

Usage: python scripts/fix_evdata_null_map.py [--dry-run]
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

# Match `evData.map(ev =>` but NOT if `.filter(` is already chained before .map
PATTERN = re.compile(r"\bevData\.map\(ev\s*=>")
GUARDED = "evData.filter(Boolean).map(ev =>"

# Negative-lookbehind for already-fixed: "evData.filter(Boolean).map" already shipping
ALREADY_FIXED = re.compile(r"evData\.filter\(Boolean\)\.map\(ev\s*=>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Scanning {len(files)} review HTMLs ...")

    changed, already, no_match = 0, 0, 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        already_fixed_count = len(ALREADY_FIXED.findall(text))
        # Find unguarded matches: any `evData.map(ev =>` NOT preceded by `.filter(Boolean)`
        # Strategy: count all PATTERN matches, subtract already-fixed.
        all_matches = PATTERN.findall(text)
        unguarded = len(all_matches) - already_fixed_count
        if unguarded == 0:
            if already_fixed_count > 0:
                already += 1
            else:
                no_match += 1
            continue

        # Apply fix only to unguarded occurrences. Walk and replace one by one.
        new_text = text
        # Use lookbehind-style replacement: replace occurrences where the
        # preceding 22 chars do NOT contain ".filter(Boolean)".
        out_chunks = []
        i = 0
        while i < len(new_text):
            m = PATTERN.search(new_text, i)
            if not m:
                out_chunks.append(new_text[i:])
                break
            preceding = new_text[max(0, m.start() - 22): m.start()]
            out_chunks.append(new_text[i: m.start()])
            if ".filter(Boolean)" in preceding:
                # already guarded — keep as-is
                out_chunks.append(m.group(0))
            else:
                out_chunks.append(GUARDED)
            i = m.end()
        new_text = "".join(out_chunks)

        if new_text != text:
            changed += 1
            print(f"  PATCH {hp.name}: {unguarded} occurrence(s)")
            if not args.dry_run:
                hp.write_text(new_text, encoding="utf-8")

    print(f"\n=== Summary ===")
    print(f"  Files patched:      {changed}")
    print(f"  Already-fixed:      {already}")
    print(f"  No `evData.map`:    {no_match}")
    if args.dry_run:
        print("\n  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
