# -*- coding: utf-8 -*-
"""Recompute the pooled estimate from the stored per-trial rows, for ANY topic.

    python ssot/recompute_envelope.py --object ssot/<topic>/<topic>.json
    python ssot/recompute_envelope.py --corpus

WHAT IT IS FOR. A page carries a pooled number. The reader is asked to trust it.
This recomputes that number FROM THE ROWS THE SAME PAGE SHOWS and reports the
agreement, so the arithmetic between the extraction table and the headline is
checkable without any tool the reader does not have.

⚠️ WHAT IT IS NOT. It is NOT a validation of the review. It cannot detect a
wrong count, a swapped arm or a mis-specified model -- it re-runs the same
inputs through a standard estimator and asks whether the stored point falls
where they put it. AN ENVELOPE THAT AGREES PROVES THE ARITHMETIC AND NOTHING
ELSE, and that sentence ships with the output rather than being left for a
reader to work out.

⭐ IT REPORTS AN ENVELOPE, NOT A VERDICT. Fixed-effect and DerSimonian-Laird
random-effects bounds are both computed; a stored point inside the envelope
agrees, one outside is reported with the distance. Where the object declares a
different estimator (REML is the house default) the envelope will usually
CONTAIN the stored point without reproducing it exactly, and that is the correct
outcome rather than a failure -- REML and DL differ, and a check that demanded
equality would fire on every correctly-built page.

NO NETWORK. NO TOPIC NAMES.
"""
import argparse
import glob
import io
import json
import math
import os
import sys


_IDENTITY_MEASURES = ("MD", "MEANDIFFERENCE", "SMD", "RD", "RISKDIFFERENCE")


def _IDENTITY_OK(m):
    return m in _IDENTITY_MEASURES


def _rows(res, log_scale=True):
    """(effect on the analysis scale, se) per trial, plus what was unusable.

    ⚠️ THE SCALE IS NOT ALWAYS log. A ratio pools on the log scale; a MEAN
    DIFFERENCE pools on the identity scale, and taking its logarithm is
    meaningless. The first version of this module logged everything and
    reported `incretin-hfpef-review kccq_css_change` -- a KCCQ score
    difference of 7.384 points -- as 0.5% outside its envelope. The number was
    nonsense in both directions and it looked like a small, plausible
    disagreement, which is the kind that gets believed.
    """
    xf = (lambda v: math.log(v)) if log_scale else (lambda v: v)
    good, skipped = [], []
    for t in (res.get("per_trial") or []):
        if not isinstance(t, dict):
            continue
        label = t.get("nct") or t.get("trial_id") or t.get("label") or "?"
        pt = t.get("point")
        se = t.get("se_log_rr") or t.get("se_log") or t.get("se")
        if pt and se:
            try:
                if log_scale and float(pt) <= 0:
                    raise ValueError("non-positive on a ratio scale")
                good.append((xf(float(pt)), float(se), label))
                continue
            except (ValueError, TypeError):
                pass
        lo, hi = t.get("ci_low"), t.get("ci_high")
        if pt is not None and lo is not None and hi is not None and (not log_scale or lo > 0):
            try:
                se2 = (xf(float(hi)) - xf(float(lo))) / (2 * 1.959964)
                if se2 > 0:
                    good.append((xf(float(pt)), se2, label))
                    continue
            except (ValueError, TypeError):
                pass
        skipped.append({"trial": label,
                        "why": "no point with a standard error or an interval"})
    return good, skipped


def _fe(rows):
    w = [1.0 / (s * s) for _, s, _ in rows]
    mu = sum(wi * y for wi, (y, _, _) in zip(w, rows)) / sum(w)
    return mu, math.sqrt(1.0 / sum(w))


def _dl(rows):
    """DerSimonian-Laird. ⚠️ House rule: DL is biased at k < 10 and the object's
    own estimator is REML. DL is used HERE only to widen the envelope, never as
    the review's estimate, and the output says so."""
    mu_fe, _ = _fe(rows)
    w = [1.0 / (s * s) for _, s, _ in rows]
    q = sum(wi * (y - mu_fe) ** 2 for wi, (y, _, _) in zip(w, rows))
    k = len(rows)
    if k < 2:
        return mu_fe, math.sqrt(1.0 / sum(w)), 0.0, q
    c = sum(w) - sum(x * x for x in w) / sum(w)
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    w2 = [1.0 / (s * s + tau2) for _, s, _ in rows]
    mu = sum(wi * y for wi, (y, _, _) in zip(w2, rows)) / sum(w2)
    return mu, math.sqrt(1.0 / sum(w2)), tau2, q


def derive(canon, oid="primary"):
    res = (((canon.get("results") or {}).get("by_outcome") or {}).get(oid) or {})
    pooled = res.get("pooled") if isinstance(res.get("pooled"), dict) else {}
    stored = pooled.get("point")
    if pooled.get("absent"):
        return {"state": "DECLINED", "outcome": oid,
                "reason": "The pool is recorded ABSENT by the object: %s"
                          % (pooled.get("absent_reason") or "no reason given")}
    # ⚠️ A WITHDRAWN POOL IS A DECISION, NOT A GAP, AND THE FIRST VERSION OF
    # THIS CHECK CALLED IT ONE. 103 of 146 outcome-blocks reported "No stored
    # pooled point to check" -- a sentence that reads as a hole in the store.
    # They are overwhelmingly pools the object WITHDREW on purpose, carrying
    # `withdrawn: True` and a stated reason ("THE FOUR TRIALS MEASURE FOUR
    # DIFFERENT THINGS", and so on). Reporting a deliberate withdrawal as a
    # missing value would have made the corpus look incomplete where it was
    # being careful, which is the direction of error that discredits the
    # careful work.
    if pooled.get("withdrawn"):
        return {"state": "DECLINED", "outcome": oid,
                "reason": "The pool is WITHDRAWN by the object: %s"
                          % (pooled.get("withdrawn_reason")
                             or pooled.get("withdrawn_because")
                             or "reason recorded elsewhere on the block"),
                "this_is_a_DECISION_not_a_gap": True}
    if not stored:
        return {"state": "DECLINED", "outcome": oid,
                "reason": "No stored pooled point, and the pool is not marked "
                          "absent or withdrawn."}
    try:
        import absolute_effect as _AE
        measure, mpath = _AE.measure_of(canon, oid, res)
    except Exception:
        measure, mpath = None, "measure lookup unavailable"
    log_scale = (measure in _AE.RATIO_MEASURES) if measure else True
    if measure and measure not in _AE.RATIO_MEASURES and not _IDENTITY_OK(measure):
        return {"state": "DECLINED", "outcome": oid,
                "reason": "The summary measure is %r (%s). This module "
                          "recomputes ratio pools on the log scale and mean "
                          "differences on the identity scale; it does not know "
                          "this one, and guessing the scale is how a nonsense "
                          "number acquires a plausible-looking percentage."
                          % (measure, mpath)}
    rows, skipped = _rows(res, log_scale=log_scale)
    if len(rows) < 2:
        return {"state": "DECLINED", "outcome": oid,
                "reason": ("Only %d contributing row(s) carry a usable effect "
                           "and error. A pool cannot be rechecked from them."
                           % len(rows)),
                "rows_unusable": skipped,
                "⚠️_this_is_about_the_STORE_not_the_review": (
                    "The review may be perfectly sound. What is missing is the "
                    "per-trial arithmetic a reader would need to check it, and "
                    "that absence is the finding.")}

    fe_mu, fe_se = _fe(rows)
    dl_mu, dl_se, tau2, q = _dl(rows)
    back = (lambda v: math.exp(v)) if log_scale else (lambda v: v)
    lo = min(back(fe_mu - 1.959964 * fe_se), back(dl_mu - 1.959964 * dl_se))
    hi = max(back(fe_mu + 1.959964 * fe_se), back(dl_mu + 1.959964 * dl_se))
    pt_lo, pt_hi = min(back(fe_mu), back(dl_mu)), max(back(fe_mu), back(dl_mu))
    # ⚠️ THE ENVELOPE COLLAPSES TO A POINT WHEN tau-squared IS ZERO, because
    # DerSimonian-Laird then equals fixed effect. Without a tolerance the check
    # reported pages as OUTSIDE THE ENVELOPE at a relative distance of 0.0% --
    # a failure message on an exact agreement, which is the most discrediting
    # output a checker can produce. TOL is relative and declared.
    # ⚠️ AND THE TOLERANCE MUST WIDEN BY MAGNITUDE, NOT BY MULTIPLICATION.
    # `pt_lo * (1 - TOL)` widens a POSITIVE bound downward and a NEGATIVE bound
    # UPWARD -- it inverts the interval on every mean-difference outcome, which
    # is exactly where the identity scale had just been added. It reported
    # `azilsartan sbp_change_wk8`, stored -5.691 against a fixed effect of
    # -5.6912, as OUTSIDE at 0.0%. Third instrument bug of the day, and all
    # three produced a confident-looking number rather than an error.
    TOL = 0.005
    inside = ((pt_lo - TOL * abs(pt_lo)) - 1e-12 <= stored
              <= (pt_hi + TOL * abs(pt_hi)) + 1e-12)
    rel = abs(stored - back(fe_mu)) / abs(back(fe_mu)) if back(fe_mu) else 0.0

    return {
        "state": "EMITTED",
        "outcome": oid,
        "k_rows_used": len(rows),
        "k_rows_unusable": len(skipped),
        "rows_unusable": skipped,
        "stored_point": stored,
        "summary_measure": measure,
        "scale_used": "log" if log_scale else "identity",
        "declared_estimator": res.get("estimator") or res.get("model") or "not declared",
        "recomputed": {
            "fixed_effect": {"point": round(back(fe_mu), 4),
                             "ci_low": round(back(fe_mu - 1.959964 * fe_se), 4),
                             "ci_high": round(back(fe_mu + 1.959964 * fe_se), 4)},
            "dersimonian_laird": {"point": round(back(dl_mu), 4),
                                  "ci_low": round(back(dl_mu - 1.959964 * dl_se), 4),
                                  "ci_high": round(back(dl_mu + 1.959964 * dl_se), 4),
                                  "tau2": round(tau2, 6), "q": round(q, 4)},
        },
        "envelope_of_points": [round(pt_lo, 4), round(pt_hi, 4)],
        "relative_tolerance_applied": TOL,
        "_why_a_tolerance": (
            "At tau-squared = 0 the DerSimonian-Laird and fixed-effect points "
            "coincide and the envelope has zero width. A 0.5% relative "
            "tolerance keeps the check from firing on exact agreement while "
            "leaving real disagreements -- 9% and 16% in this corpus -- well "
            "outside it."),
        "envelope_of_intervals": [round(lo, 4), round(hi, 4)],
        "stored_point_inside_the_envelope": inside,
        "relative_distance_from_fixed_effect": round(rel, 4),
        "verdict": ("AGREES -- the stored point lies between the fixed-effect "
                    "and DerSimonian-Laird estimates computed from the rows "
                    "this page shows." if inside else
                    "OUTSIDE THE ENVELOPE -- the stored point is %.2f%% from "
                    "the fixed-effect estimate of the same rows. That is a "
                    "question to answer, not a verdict: a different estimator, "
                    "a continuity correction or a weighting choice can put it "
                    "there legitimately." % (100 * rel)),
        "⚠️_what_agreement_does_NOT_prove": (
            "It proves the ARITHMETIC between the extraction table and the "
            "headline. It cannot detect a wrong count, a swapped arm or a "
            "mis-specified model, because it re-runs the same inputs."),
        "_why_DL_and_not_REML": (
            "DerSimonian-Laird is biased at k below about ten and this project "
            "uses REML. DL is here only to WIDEN the envelope so a REML point "
            "falls inside it; it is never offered as the review's estimate."),
        "_derived_by": "ssot/recompute_envelope.py derive()",
        "_generality": "Fires on any topic whose per-trial rows carry an effect and an error.",
    }


def selftest(canon, oid="primary"):
    """⭐ A CHECK THAT PASSES EVERYTHING IS NOT PROVEN.

    After the scale and tolerance fixes this module reported 32 of 32 stored
    points inside their envelopes. That is the RIGHT answer -- a REML point
    lies between fixed-effect and DerSimonian-Laird by construction -- and it
    is also indistinguishable from a check that cannot fail. So a real object
    is taken, its stored point is MOVED, and the check must catch it.

    Returns the smallest perturbation that was caught, which is the module's
    actual resolving power rather than an assertion about it.
    """
    import copy
    base = derive(canon, oid)
    if base.get("state") != "EMITTED":
        return {"state": "SKIPPED", "why": base.get("reason")}
    caught_at = None
    for pct in (0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50):
        probe = copy.deepcopy(canon)
        pooled = probe["results"]["by_outcome"][oid]["pooled"]
        pooled["point"] = pooled["point"] * (1.0 + pct)
        r = derive(probe, oid)
        if r.get("state") == "EMITTED" and not r["stored_point_inside_the_envelope"]:
            caught_at = pct
            break
    if caught_at is None:
        raise AssertionError(
            "NEGATIVE TEST FAILED: moving the stored point by 50%% was not "
            "caught on outcome %r. The envelope cannot fire and its 'agrees' "
            "verdicts mean nothing." % oid)
    return {"state": "PASSED",
            "smallest_perturbation_caught": caught_at,
            "resolving_power": (
                "A stored point %.1f%% away from the rows is flagged. Anything "
                "smaller is inside the fixed-effect-to-DerSimonian-Laird "
                "envelope and this module WILL NOT SEE IT -- which is the "
                "honest statement of what an agreeing verdict is worth."
                % (100 * caught_at)),
            "control_is_synthetic": (
                "The probe is a deep copy. It never touches the object on "
                "disk and never enters a corpus count."),
            }


def _cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--object")
    ap.add_argument("--outcome", default="primary")
    ap.add_argument("--corpus", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.object and a.selftest:
        canon = json.load(open(a.object, encoding="utf-8"))
        print(json.dumps(selftest(canon, a.outcome), indent=1, ensure_ascii=False))
        return
    if a.object:
        canon = json.load(open(a.object, encoding="utf-8"))
        print(json.dumps(derive(canon, a.outcome), indent=1, ensure_ascii=False))
        return
    if not a.corpus:
        ap.error("give --object or --corpus")
    here = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in sorted(glob.glob(os.path.join(here, "*", "*.json")))
             if not f.endswith(".striptest")]
    em = de = agree = disagree = 0
    reasons = {}
    worst = []
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
            r = derive(canon, oid)
            if r["state"] != "EMITTED":
                de += 1
                reasons[r["reason"][:56]] = reasons.get(r["reason"][:56], 0) + 1
                continue
            em += 1
            if r["stored_point_inside_the_envelope"]:
                agree += 1
            else:
                disagree += 1
                worst.append((os.path.basename(f), oid, r["stored_point"],
                              r["recomputed"]["fixed_effect"]["point"],
                              r["relative_distance_from_fixed_effect"]))
    tot = em + de
    print("RECOMPUTE ENVELOPE -- CORPUS")
    print("  outcome-blocks with a pooled result : %d  <- denominator" % tot)
    print("  RECHECKED                           : %d of %d" % (em, tot))
    print("    stored point inside the envelope  : %d of %d" % (agree, em))
    print("    outside the envelope              : %d of %d" % (disagree, em))
    print("  COULD NOT RECHECK                   : %d of %d" % (de, tot))
    for k, v in sorted(reasons.items(), key=lambda x: -x[1])[:6]:
        print("      %4d  %s..." % (v, k))
    if worst:
        print()
        print("  OUTSIDE THE ENVELOPE, worst first:")
        for name, oid, st, fe, rel in sorted(worst, key=lambda x: -x[4])[:12]:
            print("    %-42s %-22s stored %-9s FE %-9s %.1f%%"
                  % (name[:42], oid[:22], st, fe, 100 * rel))


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    _cli()
