"""How many exclusion criteria in this pipeline are phrased as a MISSING property?

CLASS 49, ONE LAYER OUT. A skip criterion is a claim about the population it excludes, and
stating it as an absence excludes everything that lacks the property FOR ANY REASON -- only
one of which is the reason meant.

Two instances already on the record:

    the reading-order rollout    skipped pages with ZERO `paper-*` sections as "not built by
                                 this generator". Three were current-generator pages with no
                                 paper tab, and two of those serve nothing for a pooled point
                                 their object holds.
    a phase filter               dropped CABANA and RAFT-AF because they DECLINED TO DECLARE
                                 A PHASE. `NA` is not a phase, and enumerating phases drops
                                 every registrant who declared none.

Both are the identical error: `absence of X` used where `is a Y` was meant.

WHAT THIS COUNTS. Exclusion or skip conditions expressed negatively -- `if not x`, `if x is
None`, `if not x.get(...)`, `== 0`, `== []` -- followed by a `continue`, `skip`, `return` or
an exclusion append. And, in the objects, recorded exclusion reasons whose text is an
absence.

IT COUNTS AND NAMES. It does not rewrite: several of these are correct -- excluding a record
that genuinely has no comparator is right -- and only reading each settles which. THE POINT
IS THE POPULATION, NOT A VERDICT.

1,281 IS A POPULATION AND NOT A FINDING. DO NOT READ THEM.

THE SUBSET WORTH FINDING LATER, and the criterion for finding it, recorded now so the search
is a query rather than a re-derivation:

    A guard that excludes an item from a CORPUS-WIDE OPERATION -- a rollout, a rebuild, a
    corpus sweep, a batch verification -- rather than from a single-item computation.

Those are the ones where an absence standing in for something else SILENTLY REMOVES ITEMS
FROM A FIX, which is exactly what cost us two objectless-serving pages: the reading-order
rollout's `zero paper sections` excluded three live pages, two of which do not serve a
pooled point their object holds. A negative guard inside one page's rendering is a local
decision; a negative guard inside a loop over the corpus decides what a fix reaches.

That is a much smaller set than 1,281. Find it by looking for negative guards whose
enclosing function iterates a corpus listing -- `os.listdir(SSOT)`, `PAGE_MAP`, a glob over
`*.html` -- rather than a single object. LEFT FOR TOMORROW.

AND THE OBJECT-SIDE COUNT OF 4 IS NOT TRUSTED. `screening.excluded` is empty on most
objects, so a sweep over it measures the emptiness of the field rather than the phrasing of
the criteria -- the same instrument-shaped error as a resolver sweep reporting zero across
782 files. Reported as unreliable rather than as 4.
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEG_GUARD = re.compile(
    r"if\s+(?:not\s+[\w\.\[\]\(\)'\"]+|[\w\.\[\]\(\)'\"]+\s+is\s+None|"
    r"[\w\.\[\]\(\)'\"]+\s*==\s*(?:None|\[\]|\{\}|0|''|\"\")|"
    r"len\([^)]+\)\s*==\s*0)\s*:")
EXIT = re.compile(r"^\s*(continue|break|return|raise)\b|excluded\.append|skip", re.M)

# Exclusion reasons in the objects, phrased as an absence.
ABSENCE_TEXT = re.compile(
    r"\bno\s+(?:comparator|control|placebo|results?|posted|randomis|phase|estimand|"
    r"registered|declared)|\bnot\s+(?:declared|posted|recorded|reported|registered|"
    r"stated|available)\b|\bdoes not (?:declare|post|report|record)\b|\blacks?\b|"
    r"\babsent\b|\bmissing\b|\bunstated\b|\bnone declared\b", re.I)


def code_sweep():
    hits = []
    files = 0
    for root in (os.path.join(REPO, "scripts"), os.path.join(REPO, "ssot")):
        if not os.path.isdir(root):
            continue
        for dp, _d, names in os.walk(root):
            for nm in sorted(names):
                if not nm.endswith(".py"):
                    continue
                fp = os.path.join(dp, nm)
                try:
                    src = io.open(fp, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                files += 1
                lines = src.split("\n")
                for i, ln in enumerate(lines):
                    if not NEG_GUARD.search(ln):
                        continue
                    nxt = "\n".join(lines[i + 1:i + 3])
                    if EXIT.search(nxt):
                        hits.append((os.path.relpath(fp, REPO).replace("\\", "/"),
                                     i + 1, ln.strip()[:88]))
    return files, hits


def object_sweep():
    ssot = os.path.join(REPO, "ssot")
    reasons = []
    objects = 0
    for name in sorted(os.listdir(ssot)):
        d = os.path.join(ssot, name)
        if not os.path.isdir(d):
            continue
        fp = os.path.join(d, name + ".json")
        if not os.path.exists(fp):
            continue
        try:
            obj = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        objects += 1
        exc = ((obj.get("screening") or {}).get("excluded")) or []
        for e in exc:
            if not isinstance(e, dict):
                continue
            txt = " ".join(str(v) for k, v in e.items()
                           if isinstance(v, str) and k in ("reason", "why", "criterion",
                                                           "failed_limb", "detail"))
            if txt and ABSENCE_TEXT.search(txt):
                reasons.append((name, txt[:100]))
    return objects, reasons


def main():
    files, hits = code_sweep()
    objects, reasons = object_sweep()
    if files == 0 and objects == 0:
        print("NOT_ASSESSABLE: read no files and no objects.")
        return 2

    print("python files read                            %d" % files)
    print("NEGATIVE guards that exclude, skip or return %d" % len(hits))
    print()
    print("objects read                                 %d" % objects)
    print("recorded exclusions phrased as an absence    %d" % len(reasons))
    print()
    byfile = {}
    for rel, ln, txt in hits:
        byfile.setdefault(rel, []).append((ln, txt))
    print("TOP FILES BY NEGATIVE-EXCLUSION COUNT:")
    for rel, rows in sorted(byfile.items(), key=lambda kv: -len(kv[1]))[:16]:
        print("   %-56s %3d" % (rel, len(rows)))
    print()
    if reasons:
        from collections import Counter
        c = Counter(n for n, _t in reasons)
        print("OBJECTS WITH THE MOST ABSENCE-PHRASED EXCLUSIONS:")
        for n, k in c.most_common(8):
            print("   %-46s %4d" % (n, k))
        print()
        print("   examples:")
        for n, t in reasons[:5]:
            print("     %-30s %s" % (n[:30], t))
    print()
    print("COUNTED AND NAMED, NOT ADJUDICATED. Many of these are correct -- excluding a")
    print("record that genuinely has no comparator arm is right. The defect is only where")
    print("the absence stands in for a DIFFERENT property that was meant, as `zero paper")
    print("sections` stood in for `built by an older generator` and `phase not in the")
    print("enumerated list` stood in for `not a phase 3 trial`. Reading each settles it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
