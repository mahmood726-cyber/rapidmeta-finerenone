#!/usr/bin/env python3
"""THE THREE PROSE RULES, HELD AGAINST THE REAL OBJECTS.

Mahmood read the delivered manuscripts and said they were badly written, not merely
incomplete. Read beside ARNI's authored prose, three defects were specific and nameable,
and each is now a rule this test holds:

  RULE 1  the subject of a sentence is the REGISTERED OUTCOME TEXT, never the database key
          was: "For hfh_cvd_recurrent (k = 2), the pooled estimate was 0.8066"
  RULE 2  numbers at DISPLAY precision, never storage precision
          was: 0.8066 where the flagship writes 0.872 from a stored 0.87153524291
  RULE 3  a manuscript NEVER ADDRESSES A MAINTAINER
          was: "The model output is stored verbatim on the object rather than re-typed here"

It calls the real `project()` on the real objects -- no fixtures, and no re-implementation
of the branch under test (registry class 32).

SCOPE, and it is deliberate: this runs over the objects that HAVE the material, because
prose is a proof here rather than a rollout. A topic whose object holds no pooled estimate
is NOT_ASSESSABLE for these rules and is named, never counted as a pass.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import paper_projector as ppj                                          # noqa: E402

RICH = ["iv-iron-hf", "sglt2-hf", "sotagliflozin-hf", "alirocumab-lipid",
        "bococizumab-lipid-review", "arni-hfref"]

# Phrases addressed to whoever maintains the pipeline, not to a reader of the paper.
MAINTAINER = [
    "stored verbatim on the object",
    "re-typed here",
    "rather than re-typed",
    "on this object rather than",
]

FAILS, NA = [], []


def ck(name, got, want):
    ok = got == want
    print("  %-70s %s" % (name[:70], "ok" if ok else "FAIL"))
    if not ok:
        print("      got %r want %r" % (got, want))
        FAILS.append(name)


def main():
    os.chdir(REPO)
    checked = 0
    for topic in RICH:
        path = os.path.join("ssot", topic, topic + ".json")
        if not os.path.exists(path):
            print("  %-30s NOT_ASSESSABLE (object not on disk)" % topic)
            NA.append(topic)
            continue
        obj = json.load(open(path, encoding="utf-8"))
        secs = ppj.project(obj)
        prose = " ".join(t for s in secs for t, _ in s.paras)
        composed = " ".join(t for s in secs for t, _ in s.paras
                            if s.key in ("results", "abstract"))
        oids = [o.get("id") for o in (obj.get("outcomes") or [])
                if isinstance(o, dict) and o.get("id")]
        pooled = [oid for oid in oids
                  if ((ppj.get(obj, "results.by_outcome.%s.pooled.point" % oid)) is not None)]
        if not pooled:
            print("  %-30s NOT_ASSESSABLE (object pools nothing)" % topic)
            NA.append(topic)
            continue
        checked += 1
        print("\n%s -- %d pooled outcome(s)" % (topic, len(pooled)))

        # RULE 1 -- no database key is the subject of a composed sentence.
        leaked = [oid for oid in pooled if re.search(r"\b%s\b" % re.escape(oid), composed)]
        ck("rule 1: no outcome KEY appears in Results/Abstract prose", leaked, [])

        # ...and the registered text IS there.
        missing_names = []
        for oid in pooled:
            nm = ppj.outcome_text(obj, oid)
            if nm:
                stub = ppj.strip_measure_suffix(nm, None) or nm
                if stub[:40].lower() not in composed.lower():
                    missing_names.append(oid)
        ck("rule 1: the registered outcome text IS the subject", missing_names, [])

        # RULE 2 -- the composed prose does not carry storage precision.
        over = []
        for oid in pooled:
            pt = ppj.get(obj, "results.by_outcome.%s.pooled.point" % oid)
            raw = repr(float(pt))
            # a stored value with more than 4 significant digits must not appear verbatim
            digits = re.sub(r"[^0-9]", "", raw.split(".")[-1])
            if len(digits) > 3 and raw.rstrip("0") in composed:
                over.append((oid, raw))
        ck("rule 2: no stored point value is printed at full precision", over, [])

        # RULE 3 -- nothing addresses a maintainer, anywhere in the manuscript.
        said = [m for m in MAINTAINER if m.lower() in prose.lower()]
        ck("rule 3: no sentence addresses a maintainer", said, [])

        # AND THE ARGUMENT IS PRESENT WHERE THE OBJECT RECORDS ONE.
        has_reason = any(ppj.get(obj, "results.by_outcome.%s.heterogeneity_status" % oid)
                         or ppj.get(obj, "results.by_outcome.%s.poolable_reason" % oid)
                         for oid in pooled)
        if has_reason:
            ck("the recorded REASONING reaches the prose",
               ("grounds for pooling are recorded" in prose
                or "caveat" in prose.lower() or "because" in prose.lower()), True)
        else:
            print("      (this object records no pooling reason -- NOT_ASSESSABLE)")

        # NO IDENTICAL PARAGRAPH IS PRINTED TWICE.
        para_texts = [t for s in secs for t, _ in s.paras if len(t) > 120]
        dupes = sorted({t[:60] for t in para_texts if para_texts.count(t) > 1})
        ck("no long paragraph is emitted more than once", dupes, [])

    print()
    if NA:
        print("NOT_ASSESSABLE (%d): %s" % (len(NA), ", ".join(NA)))
        print("  -- named, never counted as a pass.")
    if FAILS:
        print("FAILED (%d):" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        return 1
    print("PASSED on %d object(s) that hold pooled estimates. This says nothing about the "
          "topics whose objects hold nothing to write prose about." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
