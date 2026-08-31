# -*- coding: utf-8 -*-
"""Project the GRADE engine's derivation into the shape the page renderer reads.

⛔ WHY THIS EXISTS, AND WHY IT IS A PROJECTION AND NOT A SECOND RATING. The engine derives
the certainty and its five domains. The renderer (`projectors2.grade_section`) reads a
different shape: `res["grade"]["certainty"]` and `res["grade"]["domains"][k]["rating"]` with
a `basis_in_sources` string. Until now this object carried the engine's answer only in prose
and in a cache key the renderer does not read, so THE BUILD CRASHED WITH KeyError:
'certainty' -- and before that, the served page printed "Pending" for a result the object
had already rated.

⭐ THE OBJECT WAS RIGHT AND THE PAGE WAS WRONG, WHICH IS THE FAILURE THIS PROJECT KEEPS
PAYING FOR IN BOTH DIRECTIONS. Earlier today the same gap ran the other way: a supersede
marker written in prose while the field consumers read still held the old value. A claim is
only true where the consumers look.

⚠️ EVERY FIELD HERE IS DERIVED, NONE IS AUTHORED. Run it again after any input changes and
it overwrites. That is the whole point: a hand-written GRADE block on this same object went
stale in two independent ways inside one day -- a population ruling and a threshold choice --
while the generator tracked both.
"""
import datetime
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "ssot"))

import atomic_write as aw     # noqa: E402
import grade_engine as G      # noqa: E402

TOPIC = "agyw-hiv-prep-review"
UTC = datetime.datetime.now(datetime.timezone.utc).isoformat()

# The renderer's own vocabulary, so a reader meets GRADE's words and not the engine's enum.
RATING_WORD = {
    "NO_DOWNGRADE": "not serious",
    "DOWNGRADE": "serious",
    "NOT_ASSESSABLE": "not assessable",
    "REFUSED": "refused -- input not held",
}


def main(oid="primary", apply_changes=False):
    path = os.path.join(_HERE, "..", "ssot", TOPIC, "%s.json" % TOPIC)
    obj = json.load(open(path, encoding="utf-8"))
    rec = G.derive(obj, oid)
    if rec.get("state") != "RATED":
        print("REFUSED: the engine does not rate this result (state=%s). A projection of a "
              "withheld rating would publish a letter the review is withholding."
              % rec.get("state"))
        return 1

    res = obj["results"]["by_outcome"][oid]
    grade = res.setdefault("grade", {})
    domains = {}
    for d in rec.get("domains") or []:
        levels = d.get("levels") or 0
        word = RATING_WORD.get(d.get("state"), str(d.get("state")).lower())
        if d.get("state") == "DOWNGRADE" and levels > 1:
            word = "very serious"
        domains[d["domain"]] = {
            "rating": word,
            "levels": levels,
            "state": d.get("state"),
            "basis_in_sources": d.get("reason") or "",
        }
    grade["certainty"] = rec["certainty"]
    grade["domains"] = domains
    grade["starting_point"] = rec.get("starting_certainty")
    grade["starting_point_because"] = rec.get("starting_certainty_because")
    down = [d["domain"] for d in (rec.get("domains") or [])
            if d.get("state") == "DOWNGRADE"]
    grade["certainty_derivation"] = (
        "Started %s; rated down %d level(s) across %s; total -%d -> %s."
        % (rec.get("starting_certainty"), rec.get("downgrade_levels") or 0,
           ", ".join(d.replace("_", " ") for d in down) or "no domain",
           rec.get("downgrade_levels") or 0, rec["certainty"]))
    sens = (rec.get("sensitivity") or {}).get("statement")
    if sens:
        grade["certainty_is_threshold_sensitive"] = sens
    grade["projected_from"] = (
        "grade_engine.derive(canon, %r), projected into the renderer's shape by "
        "scripts/project_grade_for_render_2026_08_30.py. DERIVED, NOT AUTHORED -- re-run "
        "after any input change and it overwrites." % oid)
    grade["projected_utc"] = UTC

    print("certainty      : %s" % grade["certainty"])
    print("derivation     : %s" % grade["certainty_derivation"])
    for k, v in domains.items():
        print("  %-17s %-16s %s" % (k, v["rating"], (v["basis_in_sources"] or "")[:70]))
    if not apply_changes:
        print("dry run -- pass --apply to write")
        return 0
    print("WRITTEN %d bytes" % aw.write_json(path, obj))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(apply_changes="--apply" in sys.argv))
