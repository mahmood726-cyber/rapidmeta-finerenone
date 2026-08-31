"""How many group-C pages hold a live pooled estimate they no longer publish?

THE CLASS, FOUND FROM ONE HELD PAGE. `acfb3ff5f` converted "113 topics that hold no poolable
evidence" from a manuscript to a short statement, on a split whose own group A is "29 pages
with a live pooled estimate keep a manuscript". ROSUVASTATIN_AUTO_FULL_REVIEW holds
`pooled.point = 0.6561`, `k = 2`, `per_trial = 2` -- a live pooled estimate -- and was
converted anyway. Either it is a single misclassification, or the criterion is narrower than
the rule it states.

THE DIRECTION IS WHY THIS MATTERS. This defect makes a page say LESS than its evidence
supports. Every detector this project owns looks for pages CLAIMING more than they hold; none
looks for the reverse. A false denial passes every check we have, which is why it took a held
page rather than a sweep to surface it -- and why the sweep has to be run now that one exists.

WHAT IS COUNTED, and the unit is the PAGE:
    LIVE ESTIMATE   at least one outcome with pooled.point not None AND per_trial rows
    POINT ONLY      pooled.point present but no per_trial rows behind it
    NO ESTIMATE     neither

Only the first contradicts the split's own group-A rule. The second is a weaker case and is
reported separately rather than folded in, because "has a number" and "has evidence behind the
number" are different claims and this project has conflated them before.
"""
import collections
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OUT = os.path.join(REPO, "outputs", "groupc_with_estimates_2026_08_28.json")


def classify(obj):
    """(state, detail) for one object."""
    by = (obj.get("results") or {}).get("by_outcome") or {}
    live, point_only = [], []
    for oid, blk in by.items():
        if not isinstance(blk, dict):
            continue
        pooled = blk.get("pooled") or {}
        pt = pooled.get("point")
        per = blk.get("per_trial") or []
        if pt is None:
            continue
        if per:
            live.append((oid, pt, blk.get("k"), len(per)))
        else:
            point_only.append((oid, pt, blk.get("k"), 0))
    if live:
        return "LIVE ESTIMATE", live
    if point_only:
        return "POINT ONLY", point_only
    return "NO ESTIMATE", []


def run_controls():
    from instrument_controls import require_controls
    live = {"results": {"by_outcome": {"a": {"pooled": {"point": 0.65},
                                             "per_trial": [{"t": 1}], "k": 2}}}}
    nopt = {"results": {"by_outcome": {"a": {"pooled": {}, "per_trial": [{"t": 1}]}}}}
    require_controls(
        "groupc_estimates",
        ("an object with a pooled point AND per_trial rows reads LIVE ESTIMATE",
         classify(live)[0], "LIVE ESTIMATE"),
        ("an object with no pooled point reads LIVE ESTIMATE",
         classify(nopt)[0] == "LIVE ESTIMATE", True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    pages = [l.rstrip(chr(10)).split(chr(9))[0]
             for l in io.open(os.path.join(REPO, "outputs", "_popC.txt"), encoding="utf-8")
             if l.strip()]
    c = collections.Counter()
    rows, live_pages = [], []
    for p in pages:
        path = pm.get(p)
        if not path or not os.path.exists(os.path.join(REPO, path)):
            continue
        obj = json.load(io.open(os.path.join(REPO, path), encoding="utf-8"))
        state, detail = classify(obj)
        c[state] += 1
        rows.append({"page": p, "state": state,
                     "outcomes": [{"id": o, "point": pt, "k": k, "per_trial": n}
                                  for o, pt, k, n in detail]})
        if state == "LIVE ESTIMATE":
            live_pages.append((p, detail))

    n = len(rows)
    say("group-C pages examined : %d" % n)
    say("")
    for k in ("LIVE ESTIMATE", "POINT ONLY", "NO ESTIMATE"):
        say("  %-14s %3d / %d  (%.0f%%)" % (k, c[k], n, 100.0 * c[k] / n if n else 0))
    say("")
    say("THE ONE THAT CONTRADICTS THE SPLIT'S OWN RULE: LIVE ESTIMATE = %d" % c["LIVE ESTIMATE"])
    say("  acfb3ff5f states 'A: 29 pages with a live pooled estimate keep a manuscript'.")
    say("  These were converted to a statement instead.")
    say("")
    for p, detail in live_pages[:14]:
        o, pt, k, nper = detail[0]
        say("    %-46s %-22s point=%-9s k=%-3s per_trial=%d"
            % (p[:46], o[:22], pt, k, nper))
    if len(live_pages) > 14:
        say("    ... and %d more" % (len(live_pages) - 14))

    json.dump({"question": "group-C pages holding a live pooled estimate they no longer "
                           "publish as a manuscript",
               "direction": "FALSE DENIAL -- the page says less than its evidence supports; "
                            "no detector in this project looks for this direction",
               "counts": dict(c), "n": n, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
