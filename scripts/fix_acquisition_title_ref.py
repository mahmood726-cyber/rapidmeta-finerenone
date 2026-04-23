#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Fix ReferenceError in SearchEngine.executePrecision() OpenAlex dedup step.

User-visible symptom: clicking "Run Acquisition" in the Search tab throws
`Acquisition Error: title is not defined`, aborting the search.

Root cause: a clone-template typo — two bugs on the same line:

    const seenTitles = new Set(trials.map(t => t.String(title ?? "")...));
                                              ^^^^^^^^      ^^^^^
                                              1) t.String is not a function
                                              2) `title` is not declared
                                                 at this scope (it's a
                                                 per-iteration variable
                                                 declared 8 lines later
                                                 inside forEach)

Should be:  String(t.title ?? "")
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

OLD = 'const seenTitles = new Set(trials.map(t => t.String(title ?? "").toLowerCase().replace(/[^a-z0-9]/g, \'\')));'
NEW = 'const seenTitles = new Set(trials.map(t => String(t.title ?? "").toLowerCase().replace(/[^a-z0-9]/g, \'\')));'


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if OLD not in text:
        return f"SKIP {path.name}: bug not present"
    if text.count(OLD) != 1:
        return f"FAIL {path.name}: OLD matched {text.count(OLD)} times (expected 1)"
    new_text = text.replace(OLD, NEW, 1)
    if not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="")
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
