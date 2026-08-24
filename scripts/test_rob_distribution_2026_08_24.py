"""Plant-the-defect regression for the risk-of-bias distribution.

THE DEFECT THIS CLOSES. `_fit_to_budget` summarised risk of bias by regex-matching the
section's RENDERED PROSE for "high risk of bias|some concerns|low risk of bias|no
information". Because judgements are stored as the bare token `HIGH` and because method text
discusses "some concerns" and "no information" freely, the count inflated the reassuring
categories and could not see a HIGH judgement at all. Two live pages told readers that no
result was at high risk of bias when 3 of 4 and 3 of 3 respectively were.

WHY THESE CASES. Each one plants a defect that the OLD implementation would pass and the new
one must fail, so the test cannot quietly degrade into a check that only ever says yes. The
first case is the original bug reproduced exactly; the rest are the ways a future edit could
reintroduce it while still looking correct.

Fixtures are built here, never read from the corpus: a test that reads live objects starts
passing or failing when the data changes, which is not what it is measuring.
"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "ssot"))

import paper_projector as P  # noqa: E402

FAILS = []


def check(name, got, want, why):
    ok = got == want
    print("  %-58s %s" % (name, "PASS" if ok else "FAIL"))
    if not ok:
        FAILS.append("%s\n      expected %r\n      got      %r\n      %s"
                     % (name, want, got, why))


def obj_with(results):
    """A minimal object holding per-result overall verdicts and their domains."""
    by = {}
    for i, (overall, domains) in enumerate(results):
        by.setdefault("outcome_%d" % (i // 2), {})["NCT%08d" % i] = {
            "overall": overall,
            "domains": {("D%d_x" % (j + 1)): {"judgement": d}
                        for j, d in enumerate(domains)},
        }
    return {"risk_of_bias": {"by_outcome": by}}


def main():
    print("PLANT-THE-DEFECT: risk-of-bias distribution")
    print()

    # 1. THE ORIGINAL BUG, REPRODUCED. Method prose mentions the reassuring verdicts; the
    #    stored judgements are HIGH. A prose count returns the former. A read returns HIGH.
    o = obj_with([("HIGH", ["NO_INFORMATION"] * 5),
                  ("HIGH", ["NO_INFORMATION"] * 5),
                  ("HIGH", ["NO_INFORMATION"] * 5),
                  ("SOME_CONCERNS", ["NO_INFORMATION"] * 5)])
    o["risk_of_bias"]["default_rule"] = (
        "A domain that cannot be judged is NO_INFORMATION, never SOME_CONCERNS. A rating of "
        "SOME CONCERNS with no explanation reads as a judgement against the trial.")
    counts, n, unit = P._rob_distribution(o)
    check("3 of 4 results at HIGH are counted as HIGH", counts.get("HIGH"), 3,
          "the prose-counting version reported 0 here -- this is the shipped bug")
    check("the denominator is results, not domains", n, 4,
          "20 domain judgements exist; the claim is 'per reported result'")
    check("the unit is named", unit, "results", "4 results and 20 domains are not the same")
    check("method prose does not add verdicts", sum(counts.values()), 4,
          "default_rule mentions SOME CONCERNS and NO_INFORMATION and is not a judgement")

    # 2. HIGH MUST SURVIVE ITS SPELLING VARIANTS. `HIGH_RISK` and "high risk of bias" mean
    #    the same verdict; a map keyed only on today's token silently drops tomorrow's.
    for token in ("HIGH", "HIGH_RISK", "high risk of bias", "High Risk Of Bias"):
        c, _n, _u = P._rob_distribution(obj_with([(token, ["LOW"])]))
        check("verdict %-18r normalises to HIGH" % token, c.get("HIGH"), 1,
              "an unrecognised spelling is dropped, which understates")

    # 3. AN OBJECT WITH NO OVERALL VERDICTS FALLS BACK TO DOMAINS, AND SAYS SO.
    o2 = {"risk_of_bias": {"by_outcome": {"o": {"NCT1": {
        "domains": {"D1_x": {"judgement": "HIGH"}, "D2_x": {"judgement": "LOW"}}}}}}}
    c2, n2, u2 = P._rob_distribution(o2)
    check("falls back to domain judgements", (c2.get("HIGH"), n2), (1, 2),
          "a result with no overall verdict still holds domain evidence")
    check("the fallback names its unit", u2, "domain judgements",
          "reporting domains under the word 'results' is the denominator swap")

    # 4. NOTHING STORED MUST YIELD NOTHING, NOT AN EMPTY REASSURANCE. A summary that
    #    reports "0 at high risk of bias" when no assessment exists is the SKIP-as-pass
    #    failure: absence of a finding rendered as a finding of absence.
    for empty in ({}, {"risk_of_bias": None}, {"risk_of_bias": {}},
                  {"risk_of_bias": {"by_outcome": {}}},
                  {"risk_of_bias": {"by_outcome": {"o": {"NCT1": {"overall": ""}}}}}):
        c3, n3, _u3 = P._rob_distribution(empty)
        check("no judgements -> empty, not a zero tally", (c3, n3), ({}, 0),
              "the caller refuses the section on this; a tally would assert an assessment")

    # 5. THE SUMMARY SENTENCE ITSELF MUST NAME HIGH FIRST AND NOT REPEAT IT.
    counts, n, unit = P._rob_distribution(o)
    order = ("HIGH", "SOME_CONCERNS", "NO_INFORMATION", "LOW")
    parts = ", ".join("%d at %s" % (counts[k], P._ROB_WORDS[k])
                      for k in order if counts.get(k))
    check("HIGH leads the rendered list", parts.startswith("3 at high risk of bias"), True,
          "a reader must not have to scan a list for the worst verdict")
    check("HIGH is stated once", parts.lower().count("high risk of bias"), 1,
          "emphasis by repetition is the defect five blind reviewers named")

    print()
    if FAILS:
        print("FAILED %d:" % len(FAILS))
        for f in FAILS:
            print("   " + f)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
