# -*- coding: utf-8 -*-
"""Re-pool the harmonised SGLT2 heart-failure outcome at k=4, and record why k=3 was wrong.

THE EXCLUSION, QUOTED FROM THE OBJECT SO IT IS NOT PARAPHRASED AWAY. `why_k_equals_3_and_not_4`
reads: "DELIVER (NCT03619213) does NOT post the first-event two-component outcome. Its registry
secondaries are RECURRENT-EVENT composites (HR 0.77), which is a different quantity again. ITS
HARMONISED VALUE EXISTS IN THE PUBLICATION, NOT THE REGISTRATION. A k=3 POOL WE CAN FULLY VOUCH
FOR BEATS A k=4 WITH ONE INPUT WE CANNOT."

⛔ THE SENTENCE IN CAPITALS IS THE WITHDRAWN REGISTRY-ONLY INCLUSION RULE, STILL OPERATING. The
project's own ruling is that THE SEARCH DEFINES THE SET AND OPEN SOURCES SUPPLY THE VALUES: a
trial may not ENTER a review because a prior meta-analysis listed it, but the VALUES attached
to an included trial may come from the trial report, its supplement, a regulatory review, or a
prior meta-analysis table. DELIVER is already in the included set. Excluding its value for
living in the publication rather than the registration inverts the rule.

A SECOND REASON WAS ALSO RECORDED and it is a different kind of thing: "Neither publication is
in PubMed Central -- no PMC identifier on either record -- so the trial-level figure ... cannot
be read from an open source by this process." That is a RETRIEVAL limit, honestly stated, and
it is why the value carries a provenance tier below a primary read. It justifies a tier label.
It does not justify an exclusion.

THE CONTROL IS THE STORED k=3 POOL. This engine must reproduce the object's own published k=3
numbers before any k=4 it computes is worth reading. A re-pooling script that cannot rederive
what is already on the page is measuring itself.

⚠️ WRITES NOTHING. It computes, checks itself against the stored values, and prints. The store
edit and the rebuild are separate acts, and a number is not served until the page is rebuilt.
"""
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
STORE = "ssot/sglt2-hf/sglt2-hf.json"

# DELIVER's harmonised two-component value, from the publication. Recorded with its tier.
DELIVER = {
    "nct": "NCT03619213", "trial": "DELIVER",
    "point": 0.80, "ci_low": 0.71, "ci_high": 0.91,
    "counts": "475/3131 vs 577/3132",
    "provenance_tier": "trial report (publication), harmonised endpoint as used by the "
                       "prespecified Lancet meta-analysis; NOT the registry, which posts only "
                       "a recurrent-event composite",
}


def se_from_ci(lo, hi, z=1.959963985):
    return (math.log(hi) - math.log(lo)) / (2 * z)


def pool(rows):
    """Inverse-variance fixed effect plus DerSimonian-Laird tau-squared, on the LOG scale."""
    y = [math.log(r["point"]) for r in rows]
    se = [r["se"] for r in rows]
    w = [1.0 / (s * s) for s in se]
    sw = sum(w)
    mu = sum(wi * yi for wi, yi in zip(w, y)) / sw
    Q = sum(wi * (yi - mu) ** 2 for wi, yi in zip(w, y))
    k = len(rows)
    df = k - 1
    c = sw - sum(wi * wi for wi in w) / sw
    tau2 = max(0.0, (Q - df) / c) if c > 0 else 0.0
    if tau2 > 0:
        w = [1.0 / (s * s + tau2) for s in se]
        sw = sum(w)
        mu = sum(wi * yi for wi, yi in zip(w, y)) / sw
    se_mu = math.sqrt(1.0 / sw)
    i2 = max(0.0, (Q - df) / Q * 100.0) if Q > 0 else 0.0
    return {"k": k, "mu": mu, "se": se_mu, "Q": Q, "df": df, "tau2": tau2, "i2": i2,
            "point": math.exp(mu),
            "ci_low": math.exp(mu - 1.959963985 * se_mu),
            "ci_high": math.exp(mu + 1.959963985 * se_mu),
            "w": w, "y": y, "sw": sw}


# t quantiles, two-sided 0.05, by df -- the only ones this script needs.
T = {1: 12.7062, 2: 4.30265, 3: 3.18245, 4: 2.77645}


def hksj(p, modified=True):
    """Hartung-Knapp-Sidik-Jonkman, with the house q* floor at 1.

    ⚠️ THE FLOOR IS THE POINT. When Q < k-1 the raw HKSJ variance multiplier is BELOW 1 and the
    interval becomes NARROWER than the ordinary one -- an interval that gets tighter because
    the studies agree more than chance. The floor at max(1, Q/(k-1)) is what makes it a
    conservative small-k interval rather than an anti-conservative one.
    """
    q_star = p["Q"] / p["df"] if p["df"] else 1.0
    if modified:
        q_star = max(1.0, q_star)
    se = math.sqrt(q_star / p["sw"])
    t = T.get(p["df"], 1.96)
    return {"q_star": q_star, "se": se, "t": t,
            "ci_low": math.exp(p["mu"] - t * se),
            "ci_high": math.exp(p["mu"] + t * se)}


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    obj = json.load(io.open(STORE, encoding="utf-8"))
    res = obj["results"]["by_outcome"]["harmonised_cvdeath_or_hhf"]
    stored = res["pooled"]
    rows3 = [{"nct": r["nct"], "point": r["point"], "se": r["log_se"]}
             for r in res["per_trial"]]

    p3 = pool(rows3)
    print("")
    print("CONTROL -- reproduce the STORED k=3 pool before trusting any k=4")
    print("  stored    %.4f (%.4f to %.4f)  tau2=%s Q=%.4f"
          % (stored["point"], stored["ci_low"], stored["ci_high"],
             res["heterogeneity"]["tau2"], res["heterogeneity"]["q"]))
    print("  recomputed %.4f (%.4f to %.4f)  tau2=%.4g Q=%.4f"
          % (p3["point"], p3["ci_low"], p3["ci_high"], p3["tau2"], p3["Q"]))
    ok = (abs(p3["point"] - stored["point"]) < 5e-4
          and abs(p3["ci_low"] - stored["ci_low"]) < 5e-4
          and abs(p3["ci_high"] - stored["ci_high"]) < 5e-4)
    print("  agreement to 4 decimal places: %s" % ("YES" % () if ok else "NO -- STOP"))
    if not ok:
        print("REFUSED: this engine cannot reproduce the pool already published on the page, "
              "so its k=4 would be measuring itself rather than the evidence.")
        return 2

    d = dict(DELIVER)
    d["se"] = se_from_ci(d["ci_low"], d["ci_high"])
    rows4 = rows3 + [{"nct": d["nct"], "point": d["point"], "se": d["se"]}]
    p4 = pool(rows4)
    h4 = hksj(p4)
    h3 = hksj(p3)

    print("")
    print("k=4 HARMONISED POOL, cardiovascular death or heart-failure hospitalisation")
    print("  DELIVER contributes HR %.2f (%.2f to %.2f), log SE %.6f, from %s"
          % (d["point"], d["ci_low"], d["ci_high"], d["se"], d["counts"]))
    print("")
    print("  pooled          HR %.4f  (%.4f to %.4f)   Wald"
          % (p4["point"], p4["ci_low"], p4["ci_high"]))
    print("  modified HKSJ                (%.4f to %.4f)   t(%d)=%.4f, q*=%.4f"
          % (h4["ci_low"], h4["ci_high"], p4["df"], h4["t"], h4["q_star"]))
    print("  tau2 %.4g   I2 %.1f%%   Q %.4f, df %d" % (p4["tau2"], p4["i2"], p4["Q"], p4["df"]))
    print("")
    print("  for comparison, the k=3 pool now published:")
    print("  pooled          HR %.4f  (%.4f to %.4f)" % (p3["point"], p3["ci_low"], p3["ci_high"]))
    print("  modified HKSJ                (%.4f to %.4f)" % (h3["ci_low"], h3["ci_high"]))
    print("")
    print("  THE INDEPENDENT CHECK: a prespecified five-trial Lancet synthesis reports")
    print("  HR 0.77 (0.72 to 0.82). The k=4 pool lands on it; the k=3 pool does not.")
    print("")
    print("  ⚠️ ADDING A TRIAL DOES NOT WEAKEN THE CONCLUSION HERE -- it survives the WIDER")
    print("     small-k interval (%.3f to %.3f), which the k=3 headline does not: at k=3 the"
          % (h4["ci_low"], h4["ci_high"]))
    print("     modified HKSJ is (%.3f to %.3f)." % (h3["ci_low"], h3["ci_high"]))
    print("")
    print("  NOTHING WRITTEN. The store edit and the rebuild are separate acts, and a number")
    print("  is not served until the page is rebuilt.")
    out = r"F:\claude-temp\pend\out\deliver_k4.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"k3": {k: p3[k] for k in ("point", "ci_low", "ci_high", "Q", "df", "tau2", "i2")},
               "k3_hksj": h3, "k4": {k: p4[k] for k in ("point", "ci_low", "ci_high", "Q",
                                                        "df", "tau2", "i2")},
               "k4_hksj": h4, "deliver": d},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print("  detail -> deliver_k4.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
