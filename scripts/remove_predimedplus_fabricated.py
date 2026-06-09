#!/usr/bin/env python
"""Remove the fabricated PREDIMED-Plus trial row from MEDITERRANEAN_DIET_CV.

PREDIMED-Plus is a confirmed fabricated citation (no Lancet paper exists; pmid
38924767 -> a perinatal paper; DOI 10.1016/S0140-6736(24)00822-0 unregistered),
so its event counts have no source. Per user decision (2026-06-09): remove the
trial row entirely. The two real arms (PREDIMED, CORDIOPREV) remain.

Removes: the realData entry object (balanced-brace), the id from the canonical
AL_IDS set and the nctAcronyms map, and the cosmetic '+ PREDIMED-Plus' in titles.
Default dry-run; --apply to write.
"""
import io, re, sys, argparse
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "MEDITERRANEAN_DIET_CV_REVIEW.html"
KEY = '"LEGACY-ISRCTN-89898870-PREDIMEDPLUS"'

def remove_realdata_entry(s):
    """Remove `,KEY:{...}` (balanced) — returns (s, n_removed)."""
    anchor = KEY + ":{"
    i = s.find(anchor)
    if i < 0:
        return s, 0
    # include a leading comma if present (entry is comma-separated in realData)
    start = i
    if s[i-1] == ",":
        start = i - 1
    j = i + len(anchor) - 1  # at '{'
    depth, k = 0, j
    while k < len(s):
        if s[k] == "{": depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    # if no leading comma (was first entry), drop a trailing comma instead
    end = k + 1
    if start == i and end < len(s) and s[end] == ",":
        end += 1
    return s[:start] + s[end:], 1

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    s0 = FILE.read_text(encoding="utf-8")
    s = s0
    changes = []

    s, n = remove_realdata_entry(s)
    changes.append(("realData entry (balanced)", n))

    # canonical AL_IDS set element  ,"...PREDIMEDPLUS"
    before = s
    s = s.replace(',' + KEY, '')      # removes from AL_IDS array AND nctAcronyms key-part start
    # nctAcronyms left a dangling :"PREDIMED-Plus" ? handle the full pair first instead:
    s = before  # revert; do precise removals
    s = s.replace(',' + KEY + ':"PREDIMED-Plus"', '', 1)   # nctAcronyms pair
    changes.append(("nctAcronyms pair", 1 if (',' + KEY + ':"PREDIMED-Plus"') in before else 0))
    before2 = s
    s = s.replace(',' + KEY, '')      # AL_IDS array element (now the only remaining ,KEY)
    changes.append(("AL_IDS element", before2.count(',' + KEY)))

    # cosmetic title strings
    n_title = s.count(" + PREDIMED-Plus")
    s = s.replace(" + PREDIMED-Plus", "")
    changes.append(("title '+ PREDIMED-Plus'", n_title))

    # report
    print("DRY-RUN" if not args.apply else "APPLY")
    for label, n in changes:
        print(f"  {label}: {n}")
    remaining = s.count("PREDIMEDPLUS") + s.count("PREDIMED-Plus") + s.count("38924767") + s.count("00822-0")
    print(f"  residual PREDIMEDPLUS/PREDIMED-Plus/38924767/00822-0 tokens: {remaining}")
    if args.apply:
        FILE.write_text(s, encoding="utf-8")
        print("  written.")

if __name__ == "__main__":
    main()
