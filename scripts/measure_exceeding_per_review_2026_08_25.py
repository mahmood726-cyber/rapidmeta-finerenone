"""For each review, how much per-trial data could we furnish for ITS OWN included trials?

THE FRAMING, and it is transparency rather than access. The claim is not that we have data
nobody else could get -- every number here comes from the public registry, which anyone may
read. The claim is that per-trial numbers exist in public for trials whose review printed none,
and that publishing them per trial is a choice a review can make and largely does not.

THE DENOMINATOR IS THE REVIEW'S OWN INCLUDED TRIALS. A count of "trials we can furnish data
for" over the whole corpus would be a statement about our reach. Over each review's own
included set it is a statement about that review, which is the only version that means
anything. Every figure below is per review first and aggregated second.

FOUR STEPS, each a narrowing of the previous, so the loss is visible where it happens:

    labels the review lists
      -> resolved to a registration        (the validated join)
      -> that registration posted results  (a transparency fact about the trial)
      -> the review's own arm sizes reproduce from the posting  (recovery, tier A)

NO NETWORK. Everything is read from artefacts already on disk: the widened join, the extracted
Cochrane counts, and the recovery run's per-trial outcome. This is a re-cut of measurements
already made, not a new measurement, and it is labelled as such.

WHAT IS NOT KNOWN HERE, stated rather than glossed. Whether each of these 400 reviews prints a
per-trial outcome table was measured on a DIFFERENT sample -- 331 PMC full-text reviews, of
which 74% print none -- and is not known review-by-review for these 400. So this reports what
could be furnished, and does not assert that each review printed nothing.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\p70")
JOIN = os.path.join(REPO, "outputs", "join_end_to_end_wide_2026_08_25.json")
RECOV = os.path.join(REPO, "outputs", "recovery_against_p70_key_2026_08_25.json")
OUT = os.path.join(REPO, "outputs", "exceeding_per_review_2026_08_25.json")


def run_controls():
    from instrument_controls import require_controls
    # A review with two labels, one resolved and posted, one not: the per-review proportion
    # must be 1/2 and not 1/1 -- dropping unresolved labels from the denominator is exactly
    # the failure this control exists to catch.
    rows = [{"review": "R", "label": "a", "nct": "NCT1"},
            {"review": "R", "label": "b"}]
    per = {}
    for r in rows:
        d = per.setdefault(r["review"], {"labels": 0, "nct": 0})
        d["labels"] += 1
        if r.get("nct"):
            d["nct"] += 1
    require_controls(
        "exceeding_per_review (denominator)",
        ("an unresolved label stays in the review's denominator", per["R"]["labels"], 2),
        ("the denominator counts only resolved labels", per["R"]["labels"] == 1, True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    for f in (JOIN, RECOV):
        if not os.path.exists(f):
            log("NOT MEASURABLE: %s absent." % os.path.relpath(f, REPO))
            return 1

    join = json.load(io.open(JOIN, encoding="utf-8"))["rows"]
    rec = json.load(io.open(RECOV, encoding="utf-8"))["rows"]

    posted, recovered = {}, {}
    for r in rec:
        key = (r.get("review"), r.get("label"))
        posted[key] = bool(r.get("has_results"))
        recovered[key] = (r.get("tierA") == "recovered")

    per = {}
    for j in join:
        rv = j.get("review")
        if not rv:
            continue
        d = per.setdefault(rv, {"labels": 0, "nct": 0, "posted": 0, "reproduced": 0})
        d["labels"] += 1
        if not j.get("nct"):
            continue
        d["nct"] += 1
        key = (rv, j.get("label"))
        if posted.get(key):
            d["posted"] += 1
        if recovered.get(key):
            d["reproduced"] += 1

    rows = []
    for rv, d in sorted(per.items()):
        rows.append(dict(d, review=rv,
                         pct_nct=(100.0 * d["nct"] / d["labels"]) if d["labels"] else 0.0,
                         pct_posted=(100.0 * d["posted"] / d["labels"]) if d["labels"] else 0.0))

    # POST-2005 ONLY: before 2005 a registration cannot exist, so the aggregate above is
    # dominated by trial age rather than by any choice a review made. This is the stratum
    # where the question "could this have been furnished?" is answerable at all.
    p05 = {"labels": 0, "nct": 0, "posted": 0, "reproduced": 0}
    for j in join:
        y = j.get("year")
        try:
            if not y or int(y) < 2005:
                continue
        except ValueError:
            continue
        p05["labels"] += 1
        if not j.get("nct"):
            continue
        p05["nct"] += 1
        key = (j.get("review"), j.get("label"))
        if posted.get(key):
            p05["posted"] += 1
        if recovered.get(key):
            p05["reproduced"] += 1

    L = sum(d["labels"] for d in per.values())
    N = sum(d["nct"] for d in per.values())
    P = sum(d["posted"] for d in per.values())
    R = sum(d["reproduced"] for d in per.values())

    log("reviews: %d    included-study labels: %d" % (len(per), L))
    log("")
    log("aggregated over every review's own included set")
    log("  resolved to a registration      : %d / %d  (%.0f%%)" % (N, L, 100.0 * N / L))
    log("  registration posted results     : %d / %d  (%.0f%%)" % (P, L, 100.0 * P / L))
    log("  arm sizes reproduce from posting: %d / %d  (%.0f%%)" % (R, L, 100.0 * R / L))
    log("")

    if p05["labels"]:
        q = p05
        log("post-2005 labels only, where a registration can exist at all")
        log("  labels                          : %d" % q["labels"])
        log("  resolved to a registration      : %d  (%.0f%%)"
            % (q["nct"], 100.0 * q["nct"] / q["labels"]))
        log("  registration posted results     : %d  (%.0f%%)"
            % (q["posted"], 100.0 * q["posted"] / q["labels"]))
        log("  arm sizes reproduce from posting: %d  (%.0f%%)"
            % (q["reproduced"], 100.0 * q["reproduced"] / q["labels"]))
        log("")
    # per-review distribution, because an aggregate hides whether it is spread or concentrated
    withany = [r for r in rows if r["posted"] > 0]
    zero = [r for r in rows if r["posted"] == 0]
    log("per review, trials with posted results")
    log("  reviews where NONE of the included trials has posted results : %d / %d  (%.0f%%)"
        % (len(zero), len(rows), 100.0 * len(zero) / len(rows)))
    log("  reviews where at least one has                               : %d" % len(withany))
    if withany:
        sh = sorted(r["pct_posted"] for r in withany)
        log("  among those, share of included trials posted: median %.0f%%, max %.0f%%"
            % (sh[len(sh) // 2], sh[-1]))
    log("")
    log("READ THIS AS TRANSPARENCY, NOT ACCESS. Every number comes from the public registry.")
    log("The finding is that per-trial data exists in public for trials whose review printed")
    log("none -- not that we hold anything others could not read.")
    log("")
    log("NOT KNOWN HERE: whether each of these reviews prints a per-trial table. That was")
    log("measured on a different sample (331 PMC full-text reviews, 74% printing none) and is")
    log("not known review-by-review for these %d." % len(per))

    json.dump({"framing": "transparency, not access -- every figure is from the public registry",
               "denominator": "each review's own included-study labels, never the corpus",
               "provenance": "a re-cut of the widened join and the recovery run; no new fetches",
               "not_known": "per-trial-table status of these reviews; measured elsewhere on a "
                            "different sample",
               "reviews": len(per), "labels": L, "with_nct": N, "posted": P, "reproduced": R,
               "reviews_with_no_posted_trial": len(zero), "post_2005": p05, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
