"""P47 failures: CONTENT gap, or a projector that cannot reach what the object holds?

THE PREDICTION, STATED BEFORE THE RUN: overwhelmingly the first. If even a handful are the
second kind, that is one fix rather than 141 pieces of topic work, and it changes what
tomorrow looks like -- so it is tested rather than assumed.

The four reader-facing sections and the exact fields ssot/paper_projector.py reads:

    abstract       question + k_cascade.k_included + results.by_outcome   (composed, not stored)
    introduction   protocol.rationale
    discussion     discussion
    conclusions    conclusions

A CONTENT gap means the field is absent or empty and no field elsewhere on the object holds
the text either. A RENDER defect means the object HOLDS interpretive text somewhere the
projector does not look -- which is the case that would make this one fix.

So this does not merely re-check the declared fields. It sweeps every string leaf on every
object for a NEAR-MISS: a field whose name suggests background, rationale, discussion,
interpretation or conclusion, carrying enough prose to be the missing section. Anything it
finds is a render defect and is named with its path.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

DECLARED = {"introduction": "protocol.rationale",
            "discussion": "discussion",
            "conclusions": "conclusions"}

# Names that would hold the missing prose if it existed under another key.
NEAR = {
    "introduction": re.compile(r"rationale|background|why_this_review|introduction", re.I),
    "discussion": re.compile(r"discussion|interpret|what_this_means|principal_finding"
                             r"|implication", re.I),
    "conclusions": re.compile(r"conclusion|bottom_line|summary_judgement|takeaway", re.I),
}
MIN_PROSE = 120     # characters: below this it is a label, not a section


def leaves(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, p + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, p + "[%d]" % i)
    else:
        yield p, o


def get(obj, path):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def main():
    content_gap, render_defect, held = [], [], []
    objects = 0
    for name in sorted(os.listdir(SSOT)):
        d = os.path.join(SSOT, name)
        if not os.path.isdir(d):
            continue
        fp = os.path.join(d, name + ".json")
        if not os.path.exists(fp):
            continue
        try:
            obj = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        if not ((obj.get("results") or {}).get("by_outcome")):
            continue
        objects += 1
        for section, path in DECLARED.items():
            declared = get(obj, path)
            if isinstance(declared, str) and len(declared.strip()) >= MIN_PROSE:
                held.append((name, section, path))
                continue
            # The projector cannot reach it -- but is it THERE, under another name?
            found = []
            for lp, val in leaves(obj):
                if not isinstance(val, str) or len(val.strip()) < MIN_PROSE:
                    continue
                seg = lp.rsplit(".", 1)[-1]
                if NEAR[section].search(seg):
                    found.append((lp, len(val)))
            if found:
                found.sort(key=lambda x: -x[1])
                render_defect.append((name, section, found[0][0], found[0][1], len(found)))
            else:
                content_gap.append((name, section, path))

    total = len(held) + len(render_defect) + len(content_gap)
    if total == 0:
        print("NOT_ASSESSABLE: examined %d object(s) and reached zero section slots." % objects)
        return 2

    print("objects with a pooled result        %d" % objects)
    print("section slots examined              %d  (3 per object: intro, discussion, conclusions)"
          % total)
    print()
    print("  HELD -- the declared field carries prose        %4d" % len(held))
    print("  RENDER DEFECT -- prose exists, elsewhere        %4d" % len(render_defect))
    print("  CONTENT GAP -- nothing on the object at all     %4d" % len(content_gap))
    print()
    if render_defect:
        print("RENDER DEFECTS -- the object holds text the projector does not look at. These")
        print("are ONE FIX, not per-topic work:")
        print("%-40s %-14s %-56s %7s %5s" % ("topic", "section", "where it actually is",
                                             "chars", "cand"))
        print("-" * 126)
        for row in sorted(render_defect, key=lambda r: (r[1], r[0])):
            print("%-40s %-14s %-56s %7d %5d" % row)
    else:
        print("NO RENDER DEFECTS. Not one object holds background, discussion or conclusion")
        print("prose under any near-miss field name. THE PREDICTION HELD: these are content")
        print("gaps, and they are per-topic work.")
    print()
    from collections import Counter
    c = Counter(s for _, s, _ in content_gap)
    print("content gaps by section: %s"
          % ", ".join("%s %d" % (k, v) for k, v in sorted(c.items())))
    if held:
        c2 = Counter(s for _, s, _ in held)
        print("held by section        : %s"
              % ", ".join("%s %d" % (k, v) for k, v in sorted(c2.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
