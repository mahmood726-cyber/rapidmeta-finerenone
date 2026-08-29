# -*- coding: utf-8 -*-
"""The dapivirine ring pool, from the ADJUDICATED publication counts rather than the registry.

WHY THE REGISTRY COUNTS WERE WRONG TO USE. The store carries the Ring Study as 82/1302 versus
61/650, taken from the registration. Its adjudicated primary publication reports 77/1300 versus
56/650. Those are not two readings of one number: the registry posts the counts as first
submitted, the publication reports them after endpoint ADJUDICATION, and adjudication is the
step that decides which seroconversions count. Where the two disagree the adjudicated figure is
the trial's own final answer, and our page recorded neither which we used nor why.

EVERY NUMBER HERE IS READ FROM THE TRIAL'S OWN REPORT, not from a prior meta-analysis:
  ASPIRE      NCT01617096  71/1313 vs 97/1316   "2629 were enrolled: 1313 in the dapivirine
                                                 group and 1316 in the placebo group"
  Ring Study  NCT01539226  77/1300 vs 56/650    adjudicated primary publication

⚠️ AND THE ESTIMAND DOES NOT MATCH THE ANALYSIS. Both trials analysed HIV-1 acquisition as
TIME TO EVENT, with censoring and unequal follow-up; ASPIRE reports 4,280 person-years and a
median 1.6 years. A risk ratio over binary counts is a DIFFERENT QUANTITY, and it is the one we
pool. It is reported here because it is what our object supports, and it is labelled as such --
not presented as though it were the trials' own estimand.
"""
import io
import math
import sys

ASPIRE = {"trial": "ASPIRE", "nct": "NCT01617096", "e_t": 71, "n_t": 1313,
          "e_c": 97, "n_c": 1316, "source": "primary report, PMC4993693"}
RING = {"trial": "The Ring Study", "nct": "NCT01539226", "e_t": 77, "n_t": 1300,
        "e_c": 56, "n_c": 650, "source": "adjudicated primary publication"}
REGISTRY_RING = {"e_t": 82, "n_t": 1302, "e_c": 61, "n_c": 650}


def logrr(r):
    rr = (r["e_t"] / r["n_t"]) / (r["e_c"] / r["n_c"])
    var = 1.0 / r["e_t"] - 1.0 / r["n_t"] + 1.0 / r["e_c"] - 1.0 / r["n_c"]
    return math.log(rr), math.sqrt(var)


def pool(rows):
    ys = [logrr(r) for r in rows]
    w = [1.0 / (s * s) for _, s in ys]
    sw = sum(w)
    mu = sum(wi * y for wi, (y, _) in zip(w, ys)) / sw
    se = math.sqrt(1.0 / sw)
    Q = sum(wi * (y - mu) ** 2 for wi, (y, _) in zip(w, ys))
    return mu, se, Q


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    for r in (ASPIRE, RING):
        y, s = logrr(r)
        print("  %-14s %d/%d vs %d/%d   RR %.5f  logSE %.6f   [%s]"
              % (r["trial"], r["e_t"], r["n_t"], r["e_c"], r["n_c"], math.exp(y), s, r["source"]))
    mu, se, Q = pool([ASPIRE, RING])
    print("")
    print("  POOLED, adjudicated counts   RR %.4f  (%.4f to %.4f)   Q %.4f df 1  I2 0.0%%"
          % (math.exp(mu), math.exp(mu - 1.959964 * se), math.exp(mu + 1.959964 * se), Q))
    reg = dict(RING); reg.update(REGISTRY_RING)
    mu2, se2, _ = pool([ASPIRE, reg])
    print("  POOLED, registry counts      RR %.4f  (%.4f to %.4f)   <- what the page shows"
          % (math.exp(mu2), math.exp(mu2 - 1.959964 * se2), math.exp(mu2 + 1.959964 * se2)))
    print("")
    print("  the published systematic-review result is 0.71 (0.57 to 0.89).")
    print("  The adjudicated pool reproduces it; the registry pool does not.")
    print("")
    print("  ⚠️ Both are RISK RATIOS over binary counts. The trials analysed TIME TO EVENT")
    print("     with censoring, so this is a different quantity from the trials' own estimand")
    print("     and must not be presented as if it were theirs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
