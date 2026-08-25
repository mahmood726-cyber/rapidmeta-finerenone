"""Where does a PROSE cleaner silently blank a NON-PROSE value?

THE MECHANISM. `_tidy` ends in `strip_citation_keys`, which drops any fragment carrying
fewer than four alphabetic words. That is correct for its own purpose -- a sentence whose
entire content was reference labels has nothing left to say once they are removed. It is
destructive applied to a controlled value:

    _tidy("excluded")            -> ''
    _tidy("LOW")                 -> ''
    _tidy("needs adjudication")  -> ''
    _tidy("0.72")                -> ''
    _tidy("REML")                -> ''

Anything under four words comes back empty.

THIS ALREADY SHIPPED ONCE. Routing a screening verdict through the escaper -- which applies
`_tidy` -- turned 501 wrong decisions into 501 BLANK ones. A blank is worse than a wrong
value in one specific way: it reads as "nothing to report" rather than as an error, so
nobody investigates it.

WHY THE AUDIT IS EMPIRICAL AND NOT STATIC. Which call sites can receive a short value is not
decidable by reading the code -- it depends on what the objects hold. So this WRAPS `_tidy`,
projects every object in the corpus, and records every input that was non-empty going in and
empty coming out. That is the actual population, not a guess at it.

A CONTROL RUNS FIRST. The wrapper must observe the known case -- a bare status word blanked
-- before any count from it is believed. An instrument that cannot see the defect it was
built for cannot be trusted on the ones it reports.
"""
import collections
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))

import paper_projector as pp          # noqa: E402


def main():
    blanked = collections.Counter()
    examples = {}
    real = pp._tidy

    def watched(text, protect=()):
        out = real(text, protect)
        s = str(text or "").strip()
        if s and not str(out).strip():
            blanked[s[:70]] += 1
            examples.setdefault(s[:70], len(s.split()))
        return out

    # CONTROL, BEFORE ANYTHING IS COUNTED.
    #
    # THE CONTROL HAD TO BE REPOINTED, and the reason is worth keeping. It was
    # `watched("excluded")` -- a bare status word, the case this audit was built to find.
    # Once that was fixed the control stopped holding, and the audit correctly REFUSED to
    # print any count rather than reporting a clean corpus it could no longer verify.
    #
    # A control must be a case that STILL blanks, or the instrument retires itself the
    # moment it succeeds. A citation-only fragment is the behaviour `strip_citation_keys` is
    # supposed to have and will keep having, so it is the durable control.
    pp._tidy = watched
    watched("See PM_VADUGANATHAN2022 and OA_SOLOIST2021.")
    if not blanked:
        print("REFUSED: the wrapper did not observe the known case (a citation-only "
              "fragment blanked). It cannot be trusted on anything else, and NO COUNT IS "
              "PRINTED.")
        return 2
    print("CONTROL: a citation-only fragment is observed being blanked -> True")
    blanked.clear()
    examples.clear()
    print()

    ok = err = 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        try:
            pp.render(pp.project(obj), show_fields=False)
            ok += 1
        except Exception:
            err += 1
    pp._tidy = real

    L = ["objects projected: %d (raised: %d)" % (ok, err), ""]
    L.append("DISTINCT VALUES SILENTLY BLANKED BY THE PROSE CLEANER: %d" % len(blanked))
    L.append("total occurrences                                    : %d"
             % sum(blanked.values()))
    L.append("")
    L.append("Every one of these was a non-empty value that reached a reader as nothing.")
    L.append("")
    for val, n in blanked.most_common(40):
        L.append("  %5d x  (%d words)  %r" % (n, examples[val], val))

    out = os.path.join(REPO, "outputs", "tidy_blanked_values_2026_08_25.txt")
    io.open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:55]))
    return 1 if blanked else 0


sys.exit(main())
