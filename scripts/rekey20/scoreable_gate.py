# -*- coding: utf-8 -*-
"""THE HARD GATE IN FRONT OF SCORING. A page that disagrees with itself may not be judged.

⛔⛔ A page must AGREE WITH EVERY SURFACE THAT DESCRIBES IT before it is scored. Three of the
eleven comparator pages currently serve TWO DIFFERENT QUANTITIES under one column header --
`ARNI_HF_REVIEW`, `NIRSEVIMAB_INFANT_RSV_REVIEW` and `SGLT2_MACE_CVOT_REVIEW`. Scoring a page
whose own surfaces disagree produces a number about WHICH SURFACE WAS READ, not about the
page.

⭐ THE FAILURE IS A NAMED STATE, NEVER A LOSS AND NEVER A SILENT EXCLUSION:

    SCOREABLE                          every surface agrees; the page may be judged
    NOT_SCOREABLE_SURFACE_DISAGREEMENT the page serves conflicting quantities; NAMED, with
                                       the divergence code and detail carried through
    NOT_SCOREABLE_NO_BASELINE          the frozen baseline holds no row for this page --
                                       a THIRD state, because "absent from the baseline" and
                                       "present and clean" are different facts and collapsing
                                       them is how a gate starts passing what it never saw

⛔ THE BASELINE IS READ, NOT RE-DERIVED. The surfaces lane froze it at
`gates/COMPARATOR_PAGES_CROSS_SURFACE_BEFORE_2026-09-01.json` in its own worktree. Re-deriving
it here would produce a second opinion from an instrument that has never been validated
against theirs, and a disagreement between the two would be unattributable. It is read by
explicit path and HASHED, so a later run can prove which version gated it.

⚠️ TEN IS THE FAMILY COUNT AND ELEVEN IS THE PAGE COUNT. The baseline says so in its own
`population.note`. This gate runs over PAGES.
"""
import hashlib
import io
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)

BASELINE = ("F:/rapidmeta-xsurface/gates/"
            "COMPARATOR_PAGES_CROSS_SURFACE_BEFORE_2026-09-01.json")
COMPARATORS = "F:/rapidmeta-xsurface/TWENTY_COMPARATORS.json"
OUT = "../../evidence/2026-09-01-scored-run/scoreable_state.json"

SCOREABLE = "SCOREABLE"
DISAGREE = "NOT_SCOREABLE_SURFACE_DISAGREEMENT"
NO_BASELINE = "NOT_SCOREABLE_NO_BASELINE"
ALL_STATES = (SCOREABLE, DISAGREE, NO_BASELINE)


def classify(page, baseline_pages):
    """-> (state, reason, divergences). Total: every page maps to exactly one state."""
    if page not in baseline_pages:
        return (NO_BASELINE,
                "the frozen baseline holds no row for this page, so nothing is known about "
                "whether its surfaces agree. Absent is not clean", [])
    div = baseline_pages[page].get("divergences") or []
    if div:
        codes = ", ".join(d.get("code", "?") for d in div)
        return (DISAGREE,
                "the page serves conflicting quantities across its surfaces (%s). A score "
                "would measure WHICH SURFACE WAS READ, not the page" % codes, div)
    return SCOREABLE, "every recorded surface agrees", []


def main():
    braw = io.open(BASELINE, "rb").read()
    craw = io.open(COMPARATORS, "rb").read()
    base = json.loads(braw.decode("utf-8"))
    comp = json.loads(craw.decode("utf-8"))
    bpages = base["pages"]

    print("=== REF ===")
    print("   baseline      %s" % BASELINE)
    print("   baseline sha  %s   frozen_utc %s"
          % (hashlib.sha256(braw).hexdigest()[:16], base.get("frozen_utc")))
    print("   comparators   sha %s" % hashlib.sha256(craw).hexdigest()[:16])
    print("   ⛔ READ, NOT RE-DERIVED -- a second opinion from an unvalidated instrument")
    print("     would make any disagreement unattributable.")
    print("   baseline headline: %s" % json.dumps(base.get("headline")))
    print("   population note  : %s" % base.get("population", {}).get("note"))
    print("")

    # The population is the pages named by the topics, deduplicated. TEN families,
    # FOURTEEN topics, ELEVEN pages -- three different denominators, kept apart.
    topics = comp["topics"]
    pages = sorted({t["our_page_filename"] for t in topics if t.get("our_page_filename")})
    null_pages = [t["topic"] for t in topics if not t.get("our_page_filename")]

    print("=== POPULATION, KINDS BEFORE THE NUMBER ===")
    print("   families %d · topics %d · DISTINCT PAGES %d"
          % (len(comp["_families"]), len(topics), len(pages)))
    print("   topics whose page filename is null: %d   %s"
          % (len(null_pages), ", ".join(null_pages) if null_pages else "none"))
    print("   ⚠️ null means NOT FOUND by the best-coverage page rule -- it does NOT mean no")
    print("     page exists (the comparator file says so in its own header).")
    print("")

    rows, by_state = [], Counter()
    print("=== PER PAGE ===")
    print("   %-40s %-36s %s" % ("page", "state", "topics on it"))
    for pg in pages:
        st, why, div = classify(pg, bpages)
        on = [t["topic"] for t in topics if t.get("our_page_filename") == pg]
        rows.append({"page": pg, "state": st, "reason": why, "divergences": div,
                     "topics": on})
        by_state[st] += 1
        print("   %-40s %-36s %s" % (pg, st, ", ".join(on)))
        if div:
            for d in div:
                print("        ⛔ %-18s %s" % (d.get("code"), str(d.get("detail"))[:110]))

    print("")
    print("=== STATE TALLY ===")
    for s in ALL_STATES:
        print("   %-38s %2d" % (s, by_state.get(s, 0)))
    print("   %-38s %2d   sums to the pages: %s"
          % ("TOTAL", sum(by_state.values()),
             "HOLDS" if sum(by_state.values()) == len(pages) else "BROKEN"))

    # ⭐ TOPIC-LEVEL CONSEQUENCE. A page is what gets scored, but the deliverable is counted
    # in TOPICS, so the block must be reported in both denominators or it will be misread.
    blocked_pages = [r["page"] for r in rows if r["state"] != SCOREABLE]
    blocked_topics = [t for r in rows if r["state"] != SCOREABLE for t in r["topics"]]
    print("")
    print("=== WHAT IS BLOCKED, IN BOTH DENOMINATORS ===")
    print("   pages  blocked: %d of %d   %s" % (len(blocked_pages), len(pages),
                                                ", ".join(blocked_pages)))
    print("   topics blocked: %d of %d   %s" % (len(blocked_topics), len(topics),
                                                ", ".join(blocked_topics)))
    print("   ⛔ these are NOT excluded and NOT losses. They are NAMED and they become")
    print("     scoreable the moment their surfaces agree -- the fix is upstream, not here.")

    # ⭐ CONTROLS. A gate that cannot refuse is decoration, and a gate that refuses
    # everything is worse. Both directions, on the real baseline.
    print("")
    print("=== CONTROLS -- both directions, against the frozen baseline ===")
    pos = classify("ARNI_HF_REVIEW.html", bpages)[0] == DISAGREE
    neg = classify("ABLATION_AF_REVIEW.html", bpages)[0] == SCOREABLE
    absent = classify("__no_such_page__.html", bpages)[0] == NO_BASELINE
    print("   POSITIVE  ARNI_HF_REVIEW (known MEASURE_MISMATCH) is refused   : %s" % pos)
    print("   NEGATIVE  ABLATION_AF_REVIEW (known clean) is SCOREABLE        : %s" % neg)
    print("   THIRD     a page absent from the baseline is NO_BASELINE       : %s" % absent)
    ok = pos and neg and absent
    if not ok:
        print("")
        print("   ⛔ A CONTROL FAILED. NO STATE IS PUBLISHED.")
        sys.exit(1)
    print("   all three hold. A gate proven only to refuse would block everything and pass")
    print("   its own positive control; the negative is what makes this a measurement.")

    json.dump({"baseline": BASELINE,
               "baseline_sha256": hashlib.sha256(braw).hexdigest(),
               "comparators_sha256": hashlib.sha256(craw).hexdigest(),
               "controls_ok": ok, "pages": rows,
               "blocked_pages": blocked_pages, "blocked_topics": blocked_topics},
              io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
