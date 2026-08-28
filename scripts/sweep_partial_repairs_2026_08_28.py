"""Where the same fact is stored twice, did a repair land on only ONE copy?

THE SHAPE, PROVED TWICE TONIGHT ON ONE OBJECT. hepatitis-b-taf-tdf stores its arms in
`inputs.trials[].arms` and again in `results...per_trial[].as_posted`. The 2026-08-18 repair
landed on as_posted alone. Two consequences, and the second is worse than the first:

  1. Whichever checker read the mended copy passed; whichever read the other was lied to. My
     own three-source check reported OBJECT and REASON agreeing while the REGISTRY disagreed
     -- they did agree, because I was reading the uncorrected copy.
  2. THE ARM-ROLE GATE HAD BASELINED FOUR ENTRIES AS LIVE DEFECTS, all of them artefacts of
     the unrepaired label. A baseline built on the stale copy encodes the mislabel and then
     defends it.

SO THIS ASKS ONE QUESTION OF EVERY OBJECT HOLDING BOTH COPIES: do they still agree?

THE COMPARISON IS NUMERIC FIRST, NAMES SECOND, because that is what settled hepatitis-b. The
as_posted block carries a comparator/intervention n and a posted percentage; the arms carry
participants and events. If the counts match and only the NAME differs, the arms copy is
UNREPAIRED and the fix is a label. If the COUNTS differ, that is a larger defect than a label
and it is reported, never quietly repaired.

    AGREE            labels and counts reconcile
    LABEL DIVERGES   counts match, names do not -> the hepatitis-b shape
    COUNT DIVERGES   the numbers themselves disagree -> escalate, do not touch
    NOT COMPARABLE   one side lacks the fields to compare

NOTHING IS WRITTEN. This reports. A repair is a decision about which copy is authoritative,
and on the count-divergent ones that is a published-number decision.
"""
import collections
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
from paper_projector import _as_posted_pairs        # noqa: E402  one parser, both callers
OUT = os.path.join(REPO, "outputs", "partial_repairs_2026_08_28.json")
TOL = 1.0
MARKER = re.compile(r"RECOVERED|REPAIRED|CORRECTED|repaired_|corrected_|_repair")


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def compare(trial, ap):
    """(verdict, detail) for one trial against its as_posted block."""
    arms = trial.get("arms") or []
    # NO SECOND COPY IS NOT AGREEMENT. 13 of 19 trials store an as_posted block carrying
    # counts and NO arms at all. Folding that into "not comparable" would have let this
    # sweep report "0 divergences" off a reach of 2 -- the same reach-for-coverage error
    # this project keeps making.
    if not arms:
        # ONE FUNCTION, BOTH CALLERS. This asked `ap.get("intervention_n")` directly and so
        # recognised two of the EIGHT as_posted schemas in this corpus: the six arm-named
        # variants (ceftaroline_, dapivirine_ring_, cabotegravir_, cangrelor_, iv_iron_,
        # nirsevimab_) fell through to "neither copy carries arms" and the recoverable
        # population read 4 when it is 13. The renderer handled all eight; the sweep handled
        # two. Both now route through the same parser, so they cannot disagree again.
        if _as_posted_pairs(ap):
            return ("ONLY ONE COPY EXISTS",
                    "as_posted carries counts and inputs.trials[].arms is empty")
        return "NOT COMPARABLE", "neither copy carries arms"
    trt = [a for a in arms if a.get("role") == "treatment"]
    ctl = [a for a in arms if a.get("role") == "control"]
    if len(trt) != 1 or len(ctl) != 1:
        return "NOT COMPARABLE", "arms present but not exactly one treatment and one control"
    trt, ctl = trt[0], ctl[0]

    pairs = [(trt, ap.get("intervention"), ap.get("intervention_n"),
              ap.get("intervention_pct"), "intervention"),
             (ctl, ap.get("comparator"), ap.get("comparator_n"),
              ap.get("comparator_pct"), "comparator")]
    if any(n is None for _, _, n, _, _ in pairs):
        return "NOT COMPARABLE", "as_posted lacks participant counts"

    count_diff, label_diff = [], []
    for arm, ap_label, ap_n, ap_pct, who in pairs:
        a_n, a_ev = arm.get("participants"), arm.get("events")
        if a_n is None:
            return "NOT COMPARABLE", "arms lack participants"
        if float(a_n) != float(ap_n):
            count_diff.append("%s participants %s vs as_posted %s" % (who, a_n, ap_n))
            continue
        if a_ev is not None and ap_pct is not None:
            implied = float(ap_n) * float(ap_pct) / 100.0
            if abs(float(a_ev) - implied) > TOL:
                count_diff.append("%s events %s vs implied %.1f" % (who, a_ev, implied))
                continue
        if ap_label and norm(arm.get("label")) != norm(ap_label):
            label_diff.append("%s: arms %r vs as_posted %r" % (who, arm.get("label"), ap_label))

    if count_diff:
        return "COUNT DIVERGES", "; ".join(count_diff)
    if label_diff:
        return "LABEL DIVERGES", "; ".join(label_diff)
    return "AGREE", ""


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    c = collections.Counter()
    rows = []
    n_obj = n_both = 0

    for page, rel in sorted(pm.items()):
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        n_obj += 1
        if "as_posted" not in text:
            continue
        n_both += 1
        obj = json.loads(text)
        marked = bool(MARKER.search(text))
        trials = dict((t.get("nct"), t) for t in (obj.get("inputs") or {}).get("trials") or []
                      if t.get("nct"))
        for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            if not isinstance(blk, dict):
                continue
            for row in blk.get("per_trial") or []:
                ap = row.get("as_posted")
                nct = row.get("nct")
                if not ap or nct not in trials:
                    continue
                verdict, detail = compare(trials[nct], ap)
                c[verdict] += 1
                rows.append({"page": page, "nct": nct, "outcome": oid, "verdict": verdict,
                             "detail": detail, "object_carries_repair_marker": marked,
                             "as_posted_read_utc": ap.get("read_utc")})

    total = sum(c.values())
    say("objects in PAGE_MAP read            : %d" % n_obj)
    say("objects storing the fact TWICE      : %d" % n_both)
    say("trial-outcome pairs comparable      : %d" % total)
    say("")
    for k in ("AGREE", "LABEL DIVERGES", "COUNT DIVERGES", "ONLY ONE COPY EXISTS",
              "NOT COMPARABLE"):
        say("  %-16s %4d / %d" % (k, c[k], total))
    say("")
    for name, title in (("ONLY ONE COPY EXISTS",
                         "as_posted HAS COUNTS AND THE ARMS COPY IS EMPTY -- recoverable"),
                        ("COUNT DIVERGES", "COUNTS DISAGREE -- escalate, do not repair here"),
                        ("LABEL DIVERGES", "THE hepatitis-b SHAPE -- counts match, names do not")):
        bad = [r for r in rows if r["verdict"] == name]
        say("%s (%d)" % (title, len(bad)))
        for r in bad[:14]:
            say("   %-40s %s  %s" % (r["page"][:40], r["nct"], r["detail"][:90]))
        if not bad:
            say("   (none)")
        say("")

    nc = [r for r in rows if r["verdict"] == "NOT COMPARABLE"]
    say("NOT COMPARABLE, by reason -- this is the sweep's REACH, not a clean result")
    for reason, n in collections.Counter(r["detail"] for r in nc).most_common():
        say("   %-52s %d" % (reason[:52], n))

    json.dump({"question": "where a fact is stored twice, did a repair land on only one copy",
               "n_objects": n_obj, "n_objects_storing_twice": n_both,
               "counts": dict(c), "rows": rows,
               "not_written": "this reports only; deciding which copy is authoritative is a "
                              "published-number decision on the count-divergent rows",
               "DO_NOT_RECONCILE_WITH_THE_DEVIATION_LANE": {
                   "this_sweep": "2 comparable, 0 divergent. Scope: WITHIN-OBJECT, the "
                                 "inputs.trials[].arms against results...per_trial[]."
                                 "as_posted shape only.",
                   "deviation_lane": "2 assessable, 2 divergent, 70 not assessable. Scope: "
                                     "CROSS-FILE.",
                   "why_it_matters": "Different scopes and different denominators. Both are "
                                     "true. Averaging or summing them produces a number that "
                                     "describes neither, and the two 2s are not the same 2."},
               "schemas": "as_posted appears in EIGHT shapes across 19 populated "
                          "records: intervention/comparator with percentages, "
                          "experimental/comparator with events, and SIX arm-named variants "
                          "(ceftaroline_, dapivirine_ring_, cabotegravir_, cangrelor_, "
                          "iv_iron_, nirsevimab_). Enumerated, not met: the first report of "
                          "this said THREE, which was the number this lane had encountered.",
               "for_the_gates_lane": "any arm-role baseline taken before 2026-08-28 may encode "
                                     "an unrepaired label -- four hepatitis-b entries were "
                                     "baselined as live defects and were artefacts of exactly "
                                     "that"},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
