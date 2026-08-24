"""Every field whose job is to QUALIFY a claim: how many objects hold it, how many pages show it.

# control: the POSITIVE is `what_this_verdict_does_not_establish`, established by hand
# tonight at 68 objects and 0 delivered pages, and it must come back unrendered. The NEGATIVE
# is `withdrawn_reason`, which IS rendered inside every withdrawal notice and must NOT be
# reported as unrendered -- otherwise this instrument would say the corpus hides everything.

THREE SEPARATE DISCOVERIES OF ONE DIAGNOSIS, IN ONE WEEK.

    17 objects   a withdrawal reason held under an alias, pages printing "No reason recorded."
    125 objects  the estimand-contrast caveat, reaching ZERO delivered pages
    68 objects   `what_this_verdict_does_not_establish`, reaching ZERO delivered pages

Three anecdotes are not a finding. A denominator is. So this stops discovering the pattern
one field at a time and MEASURES it: every field in the corpus whose purpose is to qualify,
caveat, scope, bound or guard a claim, with the two numbers that matter side by side.

IF THE PATTERN HOLDS, THE FINDING IS NOT "we found three unprojected caveats". It is:

    THIS CORPUS SYSTEMATICALLY RECORDS ITS OWN QUALIFICATIONS AND DOES NOT SHOW THEM.

which is a much stronger claim, a much more honest one, and -- unlike three anecdotes --
checkable, refutable, and answerable with a number.

HOW A FIELD IS JUDGED TO BE A QUALIFICATION. By its NAME, against vocabulary the corpus
actually uses, plus every sentence-shaped key, which in this corpus is nearly always a
finding written where a name should be. The rule is stated in the output so the boundary is
visible rather than asserted -- a reader can disagree with the vocabulary and recount.

HOW "RENDERED" IS JUDGED. Case-insensitively, against a substantial prefix of the stored
value, on every page PAGE_MAP builds from that object. Case matters: the projector
sentence-cases stored prose, and a case-sensitive probe earlier tonight reported 3 pages
carrying a caveat that 26 were carrying. The render is the only thing a reader sees.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

# THE PREDICATE LIVES IN ssot/qualification_fields.py AND IS IMPORTED, NOT COPIED.
#
# The renderer needs the same one. Two predicates for one concept is how
# `dual_screening` and `duplicate_screening` both exist in this corpus -- and it fails
# worse here, because the whole point of this audit is that its count MOVES when the
# renderer starts showing these fields. A count measured by one rule and acted on by
# another is not a measurement of anything.
sys.path.insert(0, os.path.join(REPO, "ssot"))
from qualification_fields import (  # noqa: E402
    QUAL, NOT_QUAL, is_qualification, MIN_VALUE_CHARS)

def walk(x, out, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            if (isinstance(v, str) and len(v) >= MIN_VALUE_CHARS
                    and is_qualification(k)):
                out.setdefault(k, []).append(v)
            walk(v, out, path + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, out, "%s[%d]" % (path, i))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    pm = {}
    for pg, rel in json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"),
                                     encoding="utf-8")).items():
        pm.setdefault(rel.replace("\\", "/"), []).append(pg)

    field_objs, field_rendered = {}, {}
    page_cache = {}
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        found = {}
        walk(o, found)
        # THE POSITIVE PROPERTY: this object HOLDS at least one qualifying field, so
        # there is something here for the audit to count. Written the other way round
        # -- `if not found: continue` -- it stated only what the object is not, and an
        # audit keyed to an absence cannot distinguish `holds nothing` from `I read the
        # wrong field`. That distinction is not academic: 23 charges came back
        # NOT_IN_NOTICE tonight because the locator read one field of an object the
        # reviewers had been handed whole.
        if found:
            pages = [x for x in pm.get("ssot/%s/%s.json" % (t, t), [])
                     if os.path.isfile(os.path.join(REPO, x))]
            texts = []
            for pg in pages:
                if pg not in page_cache:
                    page_cache[pg] = io.open(os.path.join(REPO, pg), encoding="utf-8",
                                             errors="replace").read().lower()
                texts.append(page_cache[pg])
            for k, vals in found.items():
                field_objs.setdefault(k, set()).add(t)
                # RENDERED means a substantial prefix of the stored value appears on a page
                # this object builds, case-insensitively.
                shown = any(any(str(v)[:70].lower() in txt for txt in texts) for v in vals)
                if shown:
                    field_rendered.setdefault(k, set()).add(t)

    rows = []
    for k, objs in field_objs.items():
        rows.append((len(objs), len(field_rendered.get(k, set())), k))
    rows.sort(key=lambda r: (-r[0], r[2]))

    pos = next((r for r in rows if r[2] == "what_this_verdict_does_not_establish"), None)
    # KEYED TO WHAT IS STABLE, NOT TO WHAT THIS WORK IS CHANGING.
    #
    # The first version asserted this field was held on 68 objects and rendered on ZERO --
    # both numbers read by hand hours earlier. It refused, and it was right to: the corpus
    # holds it on 88 (the 68 was the subset with a withdrawn outcome, a narrower
    # denominator), and the rendered count had already moved from 0 to 1 because the
    # rollout is rebuilding pages against the projector fix that renders it.
    #
    # A CONTROL KEYED TO THE NUMBER YOU ARE CHANGING EXPIRES THE MOMENT YOU SUCCEED. That
    # lesson has cost six instances in this project and this is the seventh. The stable
    # property is that the field EXISTS and is held widely; the rendered count is the
    # FINDING and must never also be the control.
    require_controls(
        "qualifications_reach_a_reader",
        ("what_this_verdict_does_not_establish is a qualifying field held across the "
         "corpus -- its presence and breadth are stable, its render count is the finding "
         "and is deliberately not asserted here; got held=%s" % (pos and pos[0]),
         bool(pos and pos[0] >= 60), True),
        ("withdrawn_reason IS rendered in every withdrawal notice and must not appear in "
         "this table at all, or the instrument would be claiming the corpus hides "
         "everything; it appears: %s"
         % any(r[2] == "withdrawn_reason" for r in rows),
         any(r[2] == "withdrawn_reason" for r in rows), True))

    held_tot = sum(r[0] for r in rows)
    shown_tot = sum(r[1] for r in rows)
    print("")
    print("QUALIFYING FIELDS: HELD vs RENDERED")
    print("")
    print("   rule: a field NAME containing one of %d qualification words, or a key with 6+"
          % len(QUAL))
    print("         underscore-separated words (a finding written where a name should be),")
    print("         whose value is 60+ characters. %d name(s) excluded by hand: %s"
          % (len(NOT_QUAL), ", ".join(NOT_QUAL[:4]) + ", ..."))
    print("   rendered: a 70-character prefix of the stored value found on a page this")
    print("         object builds, CASE-INSENSITIVELY.")
    print("")
    print("   %-62s %7s %8s" % ("field", "objects", "pages"))
    print("   %-62s %7s %8s" % ("-" * 62, "-------", "--------"))
    for held, shown, k in rows:
        mark = "" if shown else "   <- reaches no reader"
        print("   %-62s %7d %8d%s" % (k[:62], held, shown, mark))
    print("")
    print("   %-62s %7d %8d" % ("TOTAL field-object pairs", held_tot, shown_tot))
    silent = [r for r in rows if r[1] == 0]
    print("")
    print("   distinct qualifying fields            %4d" % len(rows))
    print("   fields rendered on NO page at all     %4d" % len(silent))
    print("   object-fields held                    %4d" % held_tot)
    print("   object-fields a reader can see        %4d   %.1f%%"
          % (shown_tot, 100.0 * shown_tot / max(1, held_tot)))
    print("")
    print("THE CLAIM THIS SUPPORTS, stated so it can be refuted: this corpus records its own")
    print("qualifications and shows %.0f%% of them." % (100.0 * shown_tot / max(1, held_tot)))
    json.dump({"rows": [{"field": k, "objects": h, "pages": s} for h, s, k in rows],
               "held_total": held_tot, "shown_total": shown_tot,
               "fields_never_rendered": len(silent)},
              io.open(os.path.join(REPO, "outputs",
                                   "qualifications_reach_a_reader_2026_08_24.json"),
                      "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
