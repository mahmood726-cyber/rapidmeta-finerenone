# -*- coding: utf-8 -*-
"""Backfill origin onto the 59 templated `question` and `introduction` fields. Nothing else.

⭐ WHY THESE 59 AND ONLY THESE. They are the only fields in the corpus whose provenance is
genuinely RECOVERABLE -- the writer, its rule and its run date are all known:

    scripts/repair_paper_reads_terribly_2026_08_24.py, run 2026-08-24, wrote
        question     <- title      as "In <title>, what is the effect on <tail>?"
        introduction <- question   as "This review asks: <question>"

⛔ AND THEY ARE THE EXACT FIELDS THAT CAUSED THE DEFECT THIS MODULE EXISTS TO PREVENT. The
corpus appears to hold 59 independent statements of what each review asks and holds ZERO:
one transform, echoed into two fields, read as corroboration for six days. Recording the
origin turns 59 false witnesses into 59 honest ones, and it is the primitive's first real
use rather than a demonstration.

⛔ BACKFILL NOTHING ELSE. For the other ~116,000 fields the origin is unrecoverable -- the
transforms ran and left no trace, and reconstructing it from git history would be a guess
dressed as a record. A FABRICATED ORIGIN IS WORSE THAN AN ABSENT ONE: absent is honest,
fabricated is a false witness. Unknown stays unknown until a writer touches the field.

⚠️ EVERY RECORD WRITTEN HERE IS MARKED `reconstructed: true` WITH ITS BASIS. It was
reassembled after the fact from the script's source, not emitted by the transform. A
reconstruction must never be indistinguishable from a contemporaneous record.
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import claims as C                     # noqa: E402
from atomic_write import write_json    # noqa: E402

BY = "scripts/repair_paper_reads_terribly_2026_08_24.py"
RAN = "2026-08-24"
BASIS = ("The script's own source: it builds `question` as 'In <title>, what is the effect "
         "on <tail>?' and rewrites `manuscript.introduction` to open 'This review asks: "
         "<question>' in the same pass. Both rules are read from the committed script, not "
         "inferred from the values.")


def prose_text(v):
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list):
        out = []
        for x in v:
            if isinstance(x, dict):
                out.append(str(x.get("text") or ""))
            elif isinstance(x, str):
                out.append(x)
        return " ".join(out).strip()
    return ""


def main():
    pm = json.load(open(os.path.join(_HERE, "PAGE_MAP.json"), encoding="utf-8"))
    objs = sorted(set(pm.values()))
    root = os.path.dirname(_HERE)
    nq = ni = skipped = 0
    touched = []
    for rel in objs:
        path = rel if os.path.isabs(rel) else os.path.join(root, rel)
        canon = json.load(open(path, encoding="utf-8"))
        title = canon.get("title") or ""
        q = canon.get("question")
        # ⛔ THE ELIGIBILITY TEST IS THE SCRIPT'S OWN OUTPUT SHAPE, not a guess. A question
        # that does not start with "In <title>," was not written by this transform, and
        # stamping it would be inventing provenance.
        repaired = "question_prose_repaired_2026_08_30" in canon
        if not (isinstance(q, str) and title and (q.startswith("In " + title) or repaired)):
            continue
        changed = False
        if C.SUFFIX_FROM not in ("question" + C.SUFFIX_FROM) or True:
            if ("question" + C.SUFFIX_FROM) not in canon:
                C.set_derived(canon, "question", q, ["title"], BY,
                              run_utc=RAN, reconstructed=True)
                canon["question" + C.SUFFIX_FROM]["reconstruction_basis"] = BASIS
                if repaired:
                    canon["question" + C.SUFFIX_FROM]["later_edited_by"] = (
                        "ssot/repair_effect_on_versus_2026_08_30.py -- grammar only, no "
                        "population added")
                nq += 1
                changed = True
        man = canon.get("manuscript")
        if isinstance(man, dict):
            intro = prose_text(man.get("introduction"))
            if intro.startswith("This review asks:") and \
                    ("introduction" + C.SUFFIX_FROM) not in man:
                C.set_derived(man, "introduction", man["introduction"], ["question"], BY,
                              run_utc=RAN, reconstructed=True)
                man["introduction" + C.SUFFIX_FROM]["reconstruction_basis"] = BASIS
                man["introduction" + C.SUFFIX_FROM]["and_therefore"] = (
                    "This introduction is NOT an independent statement of the review's "
                    "question. It restates `question`, which restates `title`. Treating the "
                    "two as agreeing witnesses is one fact counted twice.")
                ni += 1
                changed = True
        if changed:
            write_json(path, canon, indent=1)
            touched.append(os.path.basename(os.path.dirname(path)))
        else:
            skipped += 1

    print("objects scanned              : %d" % len(objs))
    print("question provenance written  : %d" % nq)
    print("introduction provenance      : %d" % ni)
    print("eligible but already recorded: %d" % skipped)
    print("objects touched              : %d" % len(touched))
    print()
    print("Every record is reconstructed:true with its basis and the REAL run date %s."
          % RAN)
    print("Nothing else was backfilled. Unknown stays unknown.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
