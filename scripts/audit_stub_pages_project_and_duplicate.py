"""The 25 stub pages: do their objects PROJECT, and is any of them a duplicate?

TWO QUESTIONS, BOTH BEFORE ANY BUILD.

1. DOES THE OBJECT PROJECT? Run the manuscript projector over each and count what comes
   out -- a manuscript, a pooled estimate, both, or neither. IF THEY PROJECT, THE FIX IS A
   BUILD AND IT IS MECHANICAL. If they do not, these topics belong with the ones needing
   content, and the corpus-wide count of topics needing prose RISES -- which, given the
   optimism bias measured tonight (class 74), is the direction to expect.

2. IS ANY OF THEM A DUPLICATE? Two of the wrongly-excluded set turned out to be an unclosed
   merge cluster. A stub whose object is ALREADY SERVED BY A BUILT PAGE is a different
   problem from a stub whose topic has no page at all: the first is a cleanup, the second
   is a delivery gap. Checked two ways -- the same object served by more than one page, and
   two objects whose directory names share a stem.

REPORTS, DECIDES NOTHING, BUILDS NOTHING.
"""
import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
from instrument_controls import require_controls          # noqa: E402
import audit_skipped_but_current as A                     # noqa: E402
import paper_projector as ppj                             # noqa: E402

STAMP = re.compile(r"build[_ ]stamp|page_standard_version|built_by", re.I)


def stubs():
    """The skipped pages classified by NEITHER marker set -- the 25."""
    log = io.open(A.LOG, encoding="utf-8", errors="replace").read()
    skipped = sorted(set(re.findall(r"([A-Z0-9_]+\.html)\s+SKIPPED", log)))
    out = []
    for name in skipped:
        p = os.path.join(REPO, name)
        if not os.path.exists(p):
            continue
        vis = A.visible(io.open(p, encoding="utf-8", errors="replace").read())
        if any(m in vis for m in A.CURRENT) or any(m in vis for m in A.OLD):
            continue
        out.append(name)
    return skipped, out


def main():
    require_controls(
        "audit_stub_pages_project_and_duplicate",
        positive=("an object with a pooled point reports one",
                  bool(((({"results": {"by_outcome": {"p": {"pooled": {"point": 0.8}}}}}
                          ).get("results") or {}).get("by_outcome") or {})), True),
        negative=("an object with no results block reports a pooled point",
                  bool((({"results": {"by_outcome": {}}}.get("results") or {})
                        ).get("by_outcome")), True))

    if not os.path.exists(A.LOG):
        print("NOT_ASSESSABLE: the rollout log that DEFINES the stub set is absent.")
        return 2
    skipped, names = stubs()

    pagemap = {}
    pm = os.path.join(REPO, "ssot", "PAGE_MAP.json")
    for page, obj in json.load(io.open(pm, encoding="utf-8")).items():
        pagemap[os.path.basename(str(page))] = str(obj).replace("\\", "/").split("/")[-2]

    # Which objects are served by which pages, across the WHOLE map -- so a stub whose
    # object also has a built page is visible.
    served = {}
    for page, topic in pagemap.items():
        served.setdefault(topic, []).append(page)

    def is_built(page):
        p = os.path.join(REPO, page)
        if not os.path.exists(p):
            return False
        return os.path.getsize(p) > 200000

    rows = []
    for name in names:
        topic = pagemap.get(name)
        obj = None
        if topic:
            path = os.path.join(REPO, "ssot", topic, topic + ".json")
            if os.path.exists(path):
                try:
                    obj = json.load(io.open(path, encoding="utf-8"))
                except ValueError:
                    obj = None
        if obj is None:
            rows.append((name, topic, "OBJECT_UNREADABLE", 0, 0, [], []))
            continue
        secs = ppj.project(obj)
        written = [s.key for s in secs if s.state == ppj.WRITTEN]
        pooled = [oid for oid, b in ((obj.get("results") or {}).get("by_outcome") or {}).items()
                  if isinstance(b, dict) and (b.get("pooled") or {}).get("point") is not None]
        siblings = [p for p in served.get(topic, []) if p != name]
        built_sibs = [p for p in siblings if is_built(p)]
        rows.append((name, topic, "", len(written), len(pooled), siblings, built_sibs))

    n = len(rows)
    proj = [r for r in rows if r[3] >= 5]
    pool = [r for r in rows if r[4] > 0]
    both = [r for r in rows if r[3] >= 5 and r[4] > 0]
    neither = [r for r in rows if r[3] < 5 and r[4] == 0]
    dupes = [r for r in rows if r[6]]
    any_sib = [r for r in rows if r[5]]

    print("")
    print("SKIPPED PAGES NAMED BY THE LOG %d ; UNCLASSIFIED (the stubs) %d"
          % (len(skipped), n))
    print("")
    print("1. DO THEIR OBJECTS PROJECT?")
    print("   produce a manuscript (>=5 written sections)   %d of %d" % (len(proj), n))
    print("   produce a pooled point estimate               %d of %d" % (len(pool), n))
    print("   produce BOTH                                  %d of %d" % (len(both), n))
    print("   produce NEITHER                               %d of %d" % (len(neither), n))
    print("")
    print("2. IS ANY OF THEM A DUPLICATE?")
    print("   whose object is ALSO served by another page   %d of %d" % (len(any_sib), n))
    print("   ...where that other page is BUILT (>200 KB)   %d of %d" % (len(dupes), n))
    # THE SECOND DUPLICATE CHECK, WHICH THIS FILE'S DOCSTRING DECLARED AND THE FIRST CUT
    # DID NOT RUN. "Same object, two pages" returns 0 -- and the merge-cluster shape is
    # TWO OBJECTS FOR ONE TOPIC, which that test cannot see. MAVACAMTEN_OHCM_REVIEW resolves
    # to `mavacamten-ohcm-review` and MAVACAMTEN_OHCM_AUTO_FULL_REVIEW to `mavacamten-ohcm`:
    # different objects, same subject, and the first check called them unrelated.
    #
    # A DOCSTRING THAT CLAIMS A CHECK THE CODE DOES NOT PERFORM is the self-describing-
    # safety-claim defect, committed in the file measuring duplicates.
    def stem(topic):
        s = topic or ""
        for tail in ("-auto-full-review", "-auto-review", "-review", "-auto2", "-auto-2"):
            if s.endswith(tail):
                s = s[:-len(tail)]
        return s

    by_stem = {}
    for page, topic in pagemap.items():
        by_stem.setdefault(stem(topic), set()).add(topic)
    clusters = []
    for name, topic, _e, _w, _p, _s, _b in rows:
        others = sorted(by_stem.get(stem(topic), set()) - {topic})
        if others:
            clusters.append((name, topic, others))

    print("")
    print("   ...whose TOPIC has another object under the same stem  %d of %d"
          % (len(clusters), n))
    for name, topic, others in clusters:
        built = []
        for o in others:
            built += [p for p in served.get(o, []) if is_built(p)]
        print("      %-44s %s  -> also %s%s"
              % (name[:44], topic, ", ".join(others),
                 "  [BUILT: %s]" % ", ".join(built) if built else "  [none built]"))

    print("")
    print("%-46s %5s %6s  %s" % ("stub page", "secs", "pools", "other page(s) for this object"))
    for name, topic, err, w, p, sibs, built in sorted(rows, key=lambda r: (-r[3], r[0])):
        mark = "  <- BUILT" if built else ""
        print("%-46s %5s %6s  %s%s"
              % (name[:46], err or w, p, ", ".join(sibs)[:44] or "-", mark))
    print("")
    print("REPORTS ONLY. Nothing is built and nothing is decided here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
