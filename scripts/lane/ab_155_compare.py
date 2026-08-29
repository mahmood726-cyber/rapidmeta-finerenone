#!/usr/bin/env python3
"""Compare the two arms and say WHICH pages the shipped classes actually changed.

The prediction on record, made when gate7 said radius 6 and 5:
    statement.py    -> 4 pages   (zero-trial objects with no search record)
    projectors2.py  -> 2 pages   (tigecycline-ciai, apixaban-vte-treatment)

Anything else that moved was not predicted, and an unpredicted change on a class-wide file
is the thing the acknowledgement was supposed to bound.
"""
import difflib
import io
import json
import os
import re
import sys

# PROVENANCE IS NOT CONTENT, AND THE FIRST RUN OF THIS COMPARISON REPORTED 141 OF 141 PAGES
# CHANGED BECAUSE OF IT. Two sources, both created by the method rather than by the classes
# under test:
#   1. the build clock -- "Page generated 2026-08-29 16:25 UTC" vs "16:57"
#   2. the git-dirty marker -- arm A ran with statement.py and projectors2.py overwritten by
#      their pre-change versions, so every page correctly stamped "(uncommitted generator
#      changes -- NOT REPRODUCIBLE from this stamp alone)". The provenance system working.
# `Generator build 6279e4885` is IDENTICAL in both arms, so the commit stamp is left alone.
# Nothing else is normalised: if a normaliser has to grow to keep a comparison quiet, the
# comparison has stopped being one.
_CLOCK = re.compile(r"generated (\d{4}-\d{2}-\d{2}) \d{2}:\d{2} UTC")
_DIRTY = re.compile(r"\s*\(uncommitted generator changes -- NOT REPRODUCIBLE "
                    r"from this stamp alone\)")


def _norm(t):
    # LAMBDAS, NOT BACKREFERENCES. The first version of this function was written through a
    # heredoc and the backslash-1 backreferences arrived on disk as literal 0x01 control
    # characters: the date was replaced by a control char and the punctuation rule DELETED
    # the punctuation instead of keeping it. Both arms were mangled, but not identically,
    # so 135 pages reported a one-token difference that was entirely my own instrument.
    # A lambda replacement has no escape layer to survive, so it cannot fail this way.
    t = _CLOCK.sub(lambda m: "generated %s HH:MM UTC" % m.group(1), t)
    t = _DIRTY.sub("", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s+([,.;:])", lambda m: m.group(1), t)
    return t.strip()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# TAKEN FROM THE COMMITS' OWN RECORDS, NOT FROM MEMORY. The first version of this file
# listed four prep/lipid topics I recalled; out/zero_trial_live.json, written BY the
# statement.py commit as its evidence, names four entirely different ones. Comparing against
# a remembered prediction would have manufactured four "NOT PREDICTED" changes and four
# "predicted, did not move" -- an instrument reporting on my recall rather than on the corpus.
PREDICTED = {
    # out/zero_trial_live.json, added by 9e32a702b
    "statement.py": {"caspofungin-fungal-auto-full-review",
                     "emtricitabine-hiv-auto-full-review",
                     "etesevimab-covid-auto-full-review",
                     "men-acwy-auto-full-review"},
    # named in 6279e4885's message: "2 pages changed of the 9 whose objects hold sensitivity analyses"
    "projectors2.py": {"tigecycline-ciai", "apixaban-vte-treatment"},
}


def main():
    A = json.load(io.open(os.path.join(ROOT, "out", "ab155_A.json"), encoding="utf-8"))
    B = json.load(io.open(os.path.join(ROOT, "out", "ab155_B.json"), encoding="utf-8"))
    both = sorted(set(A["built"]) & set(B["built"]))
    onlyA = sorted(set(A["built"]) - set(B["built"]))
    onlyB = sorted(set(B["built"]) - set(A["built"]))
    print("KINDS BEFORE COUNTS")
    print("  topic objects                       : %d" % A["expected"])
    print("  refused, no title and no results    : %d (arm A) / %d (arm B)"
          % (len(A["refused"]), len(B["refused"])))
    print("  built in BOTH arms, comparable      : %d" % len(both))
    print("  built in one arm only               : %d %s" % (len(onlyA) + len(onlyB),
                                                             onlyA + onlyB))
    def _txt(arm, t):
        return _norm(io.open(os.path.join(ROOT, "scratch_ab", arm, t + ".txt"),
                             encoding="utf-8").read())

    changed = [t for t in both if _txt("A", t) != _txt("B", t)]
    print("\nRENDERED TEXT DIFFERS ON %d of %d comparable pages\n" % (len(changed), len(both)))
    allpred = PREDICTED["statement.py"] | PREDICTED["projectors2.py"]
    unpredicted = [t for t in changed if t not in allpred]
    missing = sorted(allpred - set(changed) - set(A["refused"]))
    for t in changed:
        ta, tb = _txt("A", t).split(" "), _txt("B", t).split(" ")
        sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
        adds, dels = [], []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("insert", "replace") and j2 > j1:
                adds.append(" ".join(tb[j1:j2]))
            if tag in ("delete", "replace") and i2 > i1:
                dels.append(" ".join(ta[i1:i2]))
        which = ("PREDICTED" if t in allpred else "*** NOT PREDICTED ***")
        print("  %-38s %-22s net %+d words" % (t, which, len(tb) - len(ta)))
        for d in dels[:2]:
            print("       - %s" % d[:190])
        for d in adds[:2]:
            print("       + %s" % d[:190])
    print("\nSUMMARY")
    print("  predicted and changed   : %d" % len([t for t in changed if t in allpred]))
    print("  NOT predicted, changed  : %d  %s" % (len(unpredicted), unpredicted))
    print("  predicted, did NOT move : %d  %s" % (len(missing), missing))
    print("  refused in both arms, so never assessed either way: %d"
          % len(set(A["refused"]) & set(B["refused"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
