"""On every topic carrying a published comparison, how does OUR trial count compare with THEIRS?

THE QUESTION REVERSES THE FOUNDING THESIS. This project began from the proposition that
published syntheses fail on SEARCH BREADTH and on CHECKING. The evidence so far is three
confirmed checking failures on their side and ZERO confirmed breadth failures on their side
-- and on `nirsevimab-infant-rsv-review` a published review included SIX randomised trials
where this corpus pools TWO. That is a breadth failure ON OURS.

So the computable version, across every topic with a comparison.

THE STANDARD HELD THROUGHOUT, AND IT IS THE POINT: **A COUNT THAT EXCEEDS OURS IS NOT THE
SAME AS NAMED TRIALS WE MISSED.** Where the published abstract does not list its included
studies and no included-study table was read, the difference is COUNTED AND NOT IDENTIFIED,
and this file reports those two states separately. Collapsing them would turn "they say six
and we have two" into "we missed four specific trials", which is a claim nobody here has
earned.

READS THE OBJECTS. Every number comes from `published_comparison.reviews[].n_trials_named`
or from the stored `trial_set` / `trial_set_basis` fields written when each comparison was
appraised, plus the object's own contributing trial count. Nothing is typed.
"""
import glob
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

# "n = 12,086", "six RCTs", "three trials" -- the published count as the abstract stated it.
NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
             "eight": 8, "nine": 9, "ten": 10}
COUNT_RE = re.compile(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
                      r"(?:randomi[sz]ed\s+)?(?:controlled\s+)?(?:RCTs?|trials?|studies)\b",
                      re.I)
NOT_READ = re.compile(r"NOT READ|NOT NAMED|not established", re.I)


def their_count(review):
    """The published trial count, from the appraised record. None if not stated."""
    for field in ("n_trials", "trial_set"):
        v = review.get(field)
        if isinstance(v, list):
            named = [x for x in v if not NOT_READ.search(str(x))]
            if named:
                return len(named), True          # named, so identifiable
        if isinstance(v, str):
            m = COUNT_RE.search(v)
            if m:
                tok = m.group(1).lower()
                return (NUM_WORDS.get(tok) or int(tok)), False
    blob = " ".join(str(review.get(k, "")) for k in
                    ("trial_set", "design", "outcome_pooled", "estimate_quoted",
                     "why_not_comparable", "agreement", "trial_set_basis"))
    m = COUNT_RE.search(blob)
    if m:
        tok = m.group(1).lower()
        return (NUM_WORDS.get(tok) or int(tok)), False
    return None, False


def main():
    require_controls(
        "audit_our_k_against_theirs",
        positive=("'six RCTs' is read as a count of 6",
                  their_count({"trial_set": ["NOT NAMED -- six RCTs, n = 12,086"]}) == (6, False),
                  True),
        negative=("a NOT-READ trial list is reported as identified",
                  their_count({"trial_set": ["NOT READ"]})[1], True))

    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        topic = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != topic + ".json":
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        pc = obj.get("published_comparison")
        if not isinstance(pc, dict) or not pc.get("reviews"):
            continue
        ours = len([t for t in (obj.get("inputs") or {}).get("trials") or [] if t.get("nct")])
        for rev in pc["reviews"]:
            if not isinstance(rev, dict):
                continue
            n, identified = their_count(rev)
            rows.append({"topic": topic, "ours": ours, "theirs": n,
                         "identified": identified, "pmid": rev.get("pmid"),
                         "comparable": rev.get("comparable_to_ours")})

    # One row per topic: the review with the LARGEST stated count, since the question is
    # whether ANY published synthesis carried more trials than we did.
    best = {}
    for r in rows:
        if r["theirs"] is None:
            best.setdefault(r["topic"], r)
            continue
        cur = best.get(r["topic"])
        if cur is None or (cur["theirs"] or -1) < r["theirs"]:
            best[r["topic"]] = r

    print("")
    print("TOPICS CARRYING A PUBLISHED COMPARISON: %d" % len(best))
    print("")
    print("%-40s %5s %7s  %s" % ("topic", "ours", "theirs", "their set"))
    lower = same = higher = unknown = 0
    for topic, r in sorted(best.items()):
        t = r["theirs"]
        if t is None:
            state, unknown = "NOT STATED", unknown + 1
        elif t > r["ours"]:
            state, lower = "OURS LOWER", lower + 1
        elif t == r["ours"]:
            state, same = "equal", same + 1
        else:
            state, higher = "ours higher", higher + 1
        print("%-40s %5d %7s  %-14s %s"
              % (topic[:40], r["ours"], t if t is not None else "-",
                 "IDENTIFIED" if r["identified"] else "counted only", state))

    print("")
    print("OURS LOWER          %d of %d" % (lower, len(best)))
    print("equal               %d of %d" % (same, len(best)))
    print("ours higher         %d of %d" % (higher, len(best)))
    print("their count NOT STATED %d of %d" % (unknown, len(best)))
    print("")
    idn = [t for t, r in best.items()
           if r["theirs"] and r["theirs"] > r["ours"] and r["identified"]]
    cnt = [t for t, r in best.items()
           if r["theirs"] and r["theirs"] > r["ours"] and not r["identified"]]
    print("WHERE OURS IS LOWER AND THE TRIALS ARE IDENTIFIED (a nameable gap): %d" % len(idn))
    for t in idn:
        print("   %s" % t)
    print("WHERE OURS IS LOWER AND THE SET WAS NOT READ (counted, NOT identified): %d"
          % len(cnt))
    for t in cnt:
        print("   %s" % t)
    print("")
    print("A COUNT THAT EXCEEDS OURS IS NOT THE SAME AS NAMED TRIALS WE MISSED. The second")
    print("group is a difference in stated counts and nothing more until somebody opens the")
    print("included-study table.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
