"""Who walks every string on an object and then attributes it BY PATH SEGMENT?

THE EXPOSED PATTERN, STATED WHEN prose_claim_gate's DEFECT WAS FOUND AND STILL THE
CRITERION: attribution-after-the-fact is exposed; reading a declared field is not.

    EXPOSED   walk all strings on the object, then decide which OUTCOME each belongs to by
              parsing its path -- `path.split(".")[2]`, `rsplit(".", 1)[-1]`, a regex over
              the path. The attribution is a GUESS made after the scan, and it is wrong
              wherever the path shape differs from the one the author had in mind.
    SAFE      read a declared field -- `results.by_outcome[oid].pooled` -- where the object
              itself says which outcome the value belongs to.

The difference matters because the exposed form FAILS SILENTLY AND PLAUSIBLY: a string
attributed to the wrong outcome is still a string, still numeric, still passes a truth test,
and produces a complete report about the wrong thing.

THE FIRST SWEEP FOR THIS TIMED OUT BEFORE COMPLETING and found one candidate,
execute_merges_2026_08_19.py. An incomplete sweep is a reading list with an unknown
denominator, which is the shape this project has spent the night learning not to quote. This
one reports how many files it read against how many exist, so an incomplete run says so.

READING LIST, NOT A DEFECT COUNT. Walking strings is correct in a linter whose subject IS
the strings. What this finds is where the walk is followed by an ATTRIBUTION, and each needs
a human to say whether the attribution is load-bearing.
"""
import ast
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

ROOTS = (os.path.join(REPO, "scripts"), os.path.join(REPO, "ssot"))
# A recursive walk that yields (path, string) pairs over an arbitrary object.
WALK = re.compile(r"def\s+(_?walk\w*|_?iter_strings\w*|_?strings\w*)\s*\(")
YIELDS_PATH = re.compile(r"yield\s+\(?\s*(?:path|p|pfx|prefix)\b")
# Attribution AFTER the walk: pulling an identity out of the path text.
ATTRIB = re.compile(r"path\.split\(\"\.\"\)|path\.rsplit\(\"\.\"|"
                    r"\bpath\.split\('\.'\)|re\.(?:search|match|findall)\([^)]*path")


def classify(src):
    has_walk = bool(WALK.search(src) and YIELDS_PATH.search(src))
    has_attrib = bool(ATTRIB.search(src))
    if has_walk and has_attrib:
        return "WALK_THEN_ATTRIBUTE"
    if has_walk:
        return "walk_only"
    if has_attrib:
        return "attribute_only"
    return "neither"


def main():
    require_controls(
        "audit_attribution_after_the_fact",
        positive=("a module that walks strings AND parses the path is flagged",
                  classify('def walk(o):\n    yield (path, s)\n'
                           'k = path.split(".")[2]\n') == "WALK_THEN_ATTRIBUTE", True),
        negative=("a module that reads a declared field is flagged",
                  classify('v = obj["results"]["by_outcome"][oid]["pooled"]\n')
                  == "WALK_THEN_ATTRIBUTE", True))

    seen = read = 0
    unreadable = []
    buckets = {}
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dp, _d, names in os.walk(root):
            # THE POSITIVE PROPERTY, WRITTEN POSITIVELY: this sweep is about Python
            # modules, so it selects them rather than excluding everything else. `seen`
            # counts only Python files, so the denominator IS the population -- a
            # non-Python file was never a candidate and is not a silent exclusion.
            for nm in [n for n in sorted(names) if n.endswith(".py")]:
                seen += 1
                fp = os.path.join(dp, nm)
                rel = os.path.relpath(fp, REPO).replace("\\", "/")
                try:
                    src = io.open(fp, encoding="utf-8", errors="replace").read()
                    ast.parse(src)
                except Exception:                          # noqa: BLE001
                    unreadable.append(rel)
                    continue
                read += 1
                buckets.setdefault(classify(src), []).append(rel)

    print("")
    print("PYTHON FILES SEEN %d ; READ AND PARSED %d of %d" % (seen, read, seen))
    if unreadable:
        print("   unreadable or unparseable, NAMED not dropped: %d -- %s"
              % (len(unreadable), ", ".join(unreadable[:6])))
    if read < seen:
        print("   THE SWEEP IS INCOMPLETE AND SAYS SO. A candidate count from a partial")
        print("   read is a reading list with an unknown denominator.")
    print("")
    for k in ("WALK_THEN_ATTRIBUTE", "walk_only", "attribute_only", "neither"):
        print("   %-22s %d of %d" % (k, len(buckets.get(k, [])), read))

    print("")
    print("WALK_THEN_ATTRIBUTE -- walks every string, then decides what each belongs to by")
    print("parsing its path. Each needs a human to say whether the attribution is")
    print("load-bearing; walking strings is correct where the strings ARE the subject.")
    for rel in buckets.get("WALK_THEN_ATTRIBUTE", []):
        note = ""
        if rel.endswith("audit_attribution_after_the_fact.py"):
            note = ("  <- THIS FILE. False positive by construction: it DEFINES the "
                    "pattern as a regex string, so it contains it.")
        print("   %s%s" % (rel, note))

    print("")
    print("AND THIS CRITERION IS NOT A SUPERSET OF THE ORIGINAL SWEEP'S.")
    print("The first, incomplete sweep found ONE candidate, execute_merges_2026_08_19.py.")
    print("Under this criterion that file classifies as `neither` -- it neither walks")
    print("strings yielding a path nor parses one. So the two sweeps are looking for")
    print("different things, and this one does NOT supersede that finding; it stands")
    print("beside it. Reported rather than reconciled, because reconciling them by")
    print("widening the regex until the remembered file reappears is how a criterion")
    print("becomes a search for a number.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
