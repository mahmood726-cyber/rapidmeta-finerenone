# -*- coding: utf-8 -*-
"""Where a topic holds more than one count basis, pool BOTH and name the headline.

    python ssot/count_bases.py --object ssot/<topic>/<topic>.json
    python ssot/count_bases.py --corpus

THE JUDGEMENT THIS MAKES VISIBLE. The numerator of a meta-analysis comes from a
document, and for a registered trial there are usually two defensible documents:
the registry's posted results and the trial's own publication. They are not two
views of one number. On NCT01539226 the registry posts 82 and 61 seroconversions
and the publication reports 77 and 56 -- FIVE MORE EVENTS IN EACH ARM in the
registry -- while on NCT01617096 the two agree exactly at 71 and 97.

Choosing the document is a judgement, it is rarely written down, and it chooses
the ESTIMAND as a side effect: a registry reports events over participants and
so forces a risk ratio; a publication reports events over person-years and so
forces a rate ratio.

⭐ SO THE RULE IS: any topic holding more than one basis renders BOTH and NAMES
which one is the headline. Not "the review used the registry" buried in a
provenance field -- both pools, side by side, and the choice stated as a choice.

THE CONVENTION, so any topic can populate it without new code:

    results.by_outcome.<oid>.count_bases = {
        "<tier name>": {
            "source": "...",              # what document
            "scale": "risk" | "rate",     # participants or person-time
            "headline": true,             # exactly one basis may set this
            "per_trial": [ {trial, e1, n1, e2, n2} , ... ]
        }, ...
    }

`n1`/`n2` are participants on the risk scale and person-time on the rate scale.
The module pools each basis, compares them, and REFUSES to guess the headline.

NO NETWORK. NO TOPIC NAMES.
"""
import argparse
import glob
import io
import json
import math
import os
import sys


def _rr(e1, n1, e2, n2, scale):
    """Ratio and its interval. The standard error differs by scale and getting
    it wrong is silent: on the rate scale there is no 1/n term, because a
    person-year is not a person who could have been an event."""
    if not (e1 and n1 and e2 and n2):
        return None
    r = (float(e1) / float(n1)) / (float(e2) / float(n2))
    if scale == "rate":
        se = math.sqrt(1.0 / e1 + 1.0 / e2)
    else:
        se = math.sqrt(1.0 / e1 - 1.0 / n1 + 1.0 / e2 - 1.0 / n2)
    return math.log(r), se


def _pool(rows):
    if not rows:
        return None
    w = [1.0 / (s * s) for _, s in rows]
    mu = sum(wi * y for wi, (y, _) in zip(w, rows)) / sum(w)
    se = math.sqrt(1.0 / sum(w))
    q = sum(wi * (y - mu) ** 2 for wi, (y, _) in zip(w, rows))
    return {"point": round(math.exp(mu), 4),
            "ci_low": round(math.exp(mu - 1.959964 * se), 4),
            "ci_high": round(math.exp(mu + 1.959964 * se), 4),
            "k": len(rows), "q": round(q, 4)}


def derive(canon, oid="primary"):
    res = (((canon.get("results") or {}).get("by_outcome") or {}).get(oid) or {})
    bases = res.get("count_bases")
    if not isinstance(bases, dict) or len(bases) < 2:
        n = len(bases) if isinstance(bases, dict) else 0
        return {
            "state": "DECLINED", "outcome": oid,
            "n_bases_declared": n,
            "reason": (
                "This topic declares %d count basis. The block renders when a "
                "topic holds MORE THAN ONE." % n),
            "⚠️_this_is_not_a_statement_that_only_one_exists": (
                "Almost every registered trial has two retrievable count "
                "bases -- the registry's posted results and the trial's own "
                "publication. Holding one means the other was not extracted, "
                "NOT that the review checked and found them identical. Those "
                "are different facts and only the second would be reassuring."),
            "how_to_populate": (
                "results.by_outcome.%s.count_bases = {<tier>: {source, scale, "
                "headline, per_trial:[{trial,e1,n1,e2,n2}]}}" % oid),
        }

    pooled, per_basis = {}, {}
    headline = [k for k, v in bases.items() if isinstance(v, dict) and v.get("headline")]
    for name, b in bases.items():
        if not isinstance(b, dict):
            continue
        scale = str(b.get("scale") or "risk").lower()
        rows, trials = [], []
        for t in (b.get("per_trial") or []):
            got = _rr(t.get("e1"), t.get("n1"), t.get("e2"), t.get("n2"), scale)
            if got:
                rows.append(got)
                trials.append({"trial": t.get("trial"),
                               "intervention": "%s/%s" % (t.get("e1"), t.get("n1")),
                               "comparator": "%s/%s" % (t.get("e2"), t.get("n2")),
                               "events": "%s vs %s" % (t.get("e1"), t.get("e2")),
                               "ratio": round(math.exp(got[0]), 4)})
        p = _pool(rows)
        if p:
            pooled[name] = p
            per_basis[name] = {"source": b.get("source"), "scale": scale,
                               "per_trial": trials}

    if len(pooled) < 2:
        return {"state": "DECLINED", "outcome": oid,
                "reason": "Fewer than two bases could be pooled from the "
                          "counts given.", "pooled": pooled}

    pts = sorted((v["point"], k) for k, v in pooled.items())
    spread = pts[-1][0] - pts[0][0]
    rel = spread / pts[0][0] if pts[0][0] else 0.0

    # Where the SAME trial appears in both bases with different counts, say so
    # by name -- that is the fact the choice actually turns on.
    # ⚠️ COMPARE THE EVENTS, NOT THE DENOMINATORS, WHERE THE SCALES DIFFER.
    # The first version compared the whole "e/n" string and flagged
    # NCT01617096 as disagreeing because the registry says 71/1313 and the
    # publication says 71/2151.5 -- 71 EVENTS BOTH TIMES, on participants and
    # on person-years. A denominator difference between a risk scale and a
    # rate scale is the definition of the two scales, not a disagreement about
    # what happened, and reporting it as one would have manufactured a
    # discrepancy on a trial where the sources agree exactly.
    disagreeing = []
    names = list(per_basis)
    if len(names) == 2:
        sa = per_basis[names[0]]["scale"]
        sb = per_basis[names[1]]["scale"]
        same_scale = (sa == sb)
        a, b = per_basis[names[0]]["per_trial"], per_basis[names[1]]["per_trial"]
        bm = {t["trial"]: t for t in b}
        for t in a:
            o = bm.get(t["trial"])
            if not o:
                continue
            if same_scale:
                differs = (o["intervention"] != t["intervention"]
                           or o["comparator"] != t["comparator"])
                what = "events and denominators"
            else:
                differs = (o["events"] != t["events"])
                what = "EVENTS ONLY -- the denominators are on different scales"
            if differs:
                disagreeing.append({
                    "trial": t["trial"],
                    "compared": what,
                    names[0]: ("%s vs %s" % (t["intervention"], t["comparator"])
                               if same_scale else t["events"]),
                    names[1]: ("%s vs %s" % (o["intervention"], o["comparator"])
                               if same_scale else o["events"])})
    scales_differ = (len({v["scale"] for v in per_basis.values()}) > 1)

    return {
        "state": "EMITTED",
        "outcome": oid,
        "n_bases": len(pooled),
        "pooled_by_basis": pooled,
        "detail_by_basis": per_basis,
        "headline_basis": headline[0] if len(headline) == 1 else None,
        "⛔_headline_not_named" if len(headline) != 1 else "headline_named": (
            "NO BASIS IS MARKED `headline`, or more than one is. The review "
            "must say which number is its answer: a page carrying two pooled "
            "estimates for one result and naming neither is a worse defect "
            "than either being wrong, because a reader cannot tell which is "
            "the review's." if len(headline) != 1 else headline[0]),
        "spread": {"absolute": round(spread, 4),
                   "relative": round(rel, 4),
                   "lowest": pts[0][1], "highest": pts[-1][1]},
        "trials_whose_COUNTS_DIFFER_between_bases": disagreeing,
        "what_was_compared": (
            "EVENT COUNTS ONLY -- the two bases are on different scales "
            "(risk against rate), so their denominators differ by definition "
            "and comparing them would manufacture a disagreement."
            if scales_differ else
            "Events and denominators, since both bases are on the same scale."),
        "⭐_what_this_shows": (
            "The bases differ by %.2f%% on the pooled point. %s"
            % (100 * rel,
               ("The counts themselves differ on %d trial(s), named above -- so "
                "the agreement of the pools is a fact about this topic and not "
                "a property of the two sources."
                % len(disagreeing)) if disagreeing else
               "No contributing trial's counts differ between the bases.")),
        "and_the_estimand_moves_with_it": (
            "Choosing the document chooses the measure: participants give a "
            "risk ratio, person-time gives a rate ratio. Where the two bases "
            "use different scales that is an estimand change nobody decided "
            "separately."),
        "_derived_by": "ssot/count_bases.py derive()",
        "_generality": "Fires on any topic declaring two or more count bases.",
    }


def _cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--object")
    ap.add_argument("--outcome", default="primary")
    ap.add_argument("--corpus", action="store_true")
    a = ap.parse_args()
    if a.object:
        canon = json.load(open(a.object, encoding="utf-8"))
        print(json.dumps(derive(canon, a.outcome), indent=1, ensure_ascii=False))
        return
    if not a.corpus:
        ap.error("give --object or --corpus")
    here = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in sorted(glob.glob(os.path.join(here, "*", "*.json")))
             if not f.endswith(".striptest")]
    em = de = tot = 0
    for f in files:
        try:
            canon = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(canon, dict):
            continue
        bo = ((canon.get("results") or {}) if isinstance(canon.get("results"), dict)
              else {}).get("by_outcome") or {}
        if not isinstance(bo, dict):
            continue
        for oid, res in bo.items():
            if not isinstance(res, dict) or not res.get("pooled"):
                continue
            tot += 1
            r = derive(canon, oid)
            if r["state"] == "EMITTED":
                em += 1
                print("  EMITTED  %-42s %-22s %s  headline=%s"
                      % (os.path.basename(f)[:42], oid[:22],
                         {k: v["point"] for k, v in r["pooled_by_basis"].items()},
                         r.get("headline_basis")))
            else:
                de += 1
    print()
    print("COUNT BASES -- CORPUS")
    print("  outcome-blocks with a pooled result : %d  <- denominator" % tot)
    print("  declare TWO OR MORE count bases     : %d of %d" % (em, tot))
    print("  declare fewer than two              : %d of %d" % (de, tot))
    print()
    print("  ⚠️ A topic holding one basis has NOT checked that the other")
    print("     agrees. Almost every registered trial has two retrievable")
    print("     bases; holding one means the other was not extracted.")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    _cli()
