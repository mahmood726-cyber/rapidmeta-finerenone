# -*- coding: utf-8 -*-
"""Repair "what is the effect ON VERSUS x" -- broken prose rendered to readers.

⚠️ THE DEFECT, AND WHERE IT CAME FROM. `scripts/repair_paper_reads_terribly_2026_08_24.py`
rewrote every title-shaped question as "In <title>, what is the effect on <tail>?" where
<tail> is whatever followed the title. Where that tail already began with "versus", the
result was "what is the effect ON VERSUS daily oral TDF/FTC on ..." -- ungrammatical, and
rendered 4-5 times per page in the question, the introduction and the manuscript.

⭐ A CLARITY REPAIR SCRIPT PRODUCED A CLARITY DEFECT. That is worth stating plainly rather
than quietly fixing: the pass that ran to make these pages read better is the pass that
broke four of them, and it went unnoticed for six days because nothing checked the prose it
emitted. Clarity is one of the three axes this corpus loses on in blinded comparison.

⛔ WHAT THIS REPAIR DOES NOT DO. It does NOT invent a population. The verb phrase is
repaired using the INTERVENTION NAMED IN THE OBJECT'S OWN TITLE and nothing else -- no
registry text, and above all nothing read off the contributing trials. The 55 further
objects whose question is "In <title>, ..." with the title standing in the population slot
are NOT touched here: they need an authored question, which is an editorial act, not a
string fix. See `apply_question_pico_2026_08_30.REFUSED` for why that matters -- a PICO
declared against a mechanically generated question is a PICO declared against an artefact.
"""
from __future__ import annotations

import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from atomic_write import write_json  # noqa: E402

BROKEN = "what is the effect on versus "

# slug -> the intervention as its OWN TITLE names it. Nothing here comes from a trial.
INTERVENTION = {
    "cab-prep-hiv-review": "long-acting injectable cabotegravir",
    "ceftaroline-auto-full-review": "ceftaroline fosamil",
    "lefamulin-cabp-auto-full-review": "lefamulin",
    "nirsevimab-infant-rsv-review": "nirsevimab",
}


def main():
    n = 0
    for slug, drug in INTERVENTION.items():
        path = os.path.join(_HERE, slug, slug + ".json")
        canon = json.load(open(path, encoding="utf-8"))
        title = (canon.get("title") or "")
        if drug.lower() not in title.lower():
            print("  SKIP %-34s intervention not in its own title" % slug)
            continue
        fixed = "what is the effect of %s versus " % drug
        touched = []

        q = canon.get("question")
        if isinstance(q, str) and BROKEN in q:
            canon["question"] = q.replace(BROKEN, fixed)
            touched.append("question")

        man = canon.get("manuscript")
        if isinstance(man, dict):
            for k, v in list(man.items()):
                if isinstance(v, str) and BROKEN in v:
                    man[k] = v.replace(BROKEN, fixed)
                    touched.append("manuscript.%s" % k)
        for key in ("manuscript_draft_2026_08_21",):
            blk = canon.get(key)
            if isinstance(blk, dict):
                for k, v in list(blk.items()):
                    if isinstance(v, str) and BROKEN in v:
                        blk[k] = v.replace(BROKEN, fixed)
                        touched.append("%s.%s" % (key, k))

        if not touched:
            print("  SKIP %-34s nothing to repair" % slug)
            continue

        canon["question_prose_repaired_2026_08_30"] = {
            "what": ("Repaired 'what is the effect ON VERSUS x' to 'what is the effect OF "
                     "<intervention> VERSUS x'. Grammar only."),
            "the_intervention_came_from": ("this object's own title, %r. NOT from the "
                                           "contributing trials and NOT from any registry "
                                           "record." % title),
            "introduced_by": ("scripts/repair_paper_reads_terribly_2026_08_24.py, which "
                              "built the question as 'In <title>, what is the effect on "
                              "<tail>?' where the tail already began with 'versus'."),
            "fields_changed": touched,
            "WHAT_WAS_NOT_DONE": (
                "⛔ NO POPULATION WAS ADDED. This question still states no population, and "
                "that is why the indirectness domain REFUSES to rate this outcome rather "
                "than deriving a rating from it. The population exists on this object in "
                "one place only -- the eligibility of the contributing trials -- and "
                "reading it off them would be inferring the question from the studies that "
                "answer it, which returns DIRECT by construction. An authored question is "
                "required and is an editorial decision, not a repair."),
            "repaired_utc": "2026-08-30",
        }
        write_json(path, canon, indent=1)
        n += 1
        print("  FIXED %-34s %d field(s): %s" % (slug, len(touched), ", ".join(touched[:4])))
        print("        %s" % canon["question"][:150])
    print("\nrepaired %d object(s). Pages must be REBUILT to show it." % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
