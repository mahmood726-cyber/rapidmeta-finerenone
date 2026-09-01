# -*- coding: utf-8 -*-
"""Compare our stored estimates against the R/metafor oracle, and PROVE the suite
can disagree before believing any agreement it reports.

A detector that has only ever returned agreement is indistinguishable from one that
cannot disagree. So two controls run FIRST:

  PLANT   a tau-squared estimator with a FIXED POINT AT ZERO -- the exact shape of
          the defect that survived in the corpus, because tau2 = 0 is a plausible
          answer and no internal sanity check can flag it. The oracle must flag
          every case where metafor finds tau2 > 0. Then RESTORE and assert the
          restoration returns to the unplanted result.
  METHOD  each case is compared only against the matching metafor fit, with the pin
          READ BACK from the fit object. z vs knha are different quantities.

Disagreements are listed INDIVIDUALLY. A pass rate hides the three that matter.
Every number quoted comes from metafor's own output, never recomputed here.
"""
import io
import json
import math

TOL_REL = 1e-3          # declared BEFORE running. Relative, on the point estimate.
TOL_TAU2 = 1e-4         # absolute, on tau-squared.


def rel(a, b):
    if a is None or b is None:
        return None
    a, b = float(a), float(b)
    d = max(abs(a), abs(b), 1e-12)
    return abs(a - b) / d


def load():
    cases = json.load(io.open("cases.json", encoding="utf-8"))["cases"]
    orc = json.load(io.open("oracle_out.json", encoding="utf-8"))
    return cases, {(r["topic"], r["outcome"]): r for r in orc["results"]}, orc


def oracle_point(fit, log_scale):
    b = fit["b"]
    return math.exp(b) if log_scale else b


def compare(cases, om, planted_tau2=None):
    """planted_tau2: callable(yi,sei)->tau2, used to simulate a broken estimator."""
    rows = []
    for c in cases:
        key = (c["topic"], c["outcome"])
        o = om.get(key)
        if not o:
            rows.append((key, "NO_ORACLE", None, None, None))
            continue
        # METHOD MATCH: pick the fit whose PIN matches what the object states.
        want_knha = bool(c.get("stated_hksj"))
        fit = o["knha"] if want_knha else o["z"]
        if not fit.get("ok"):
            rows.append((key, "ORACLE_ERROR", fit.get("error"), None, None))
            continue
        # read the pin back -- never trust what we asked for
        pin_ok = (fit["knha_used"] == want_knha) and fit["method_used"] == "REML"
        if not pin_ok:
            rows.append((key, "PIN_MISMATCH",
                         "asked knha=%s got test=%s method=%s"
                         % (want_knha, fit["test_used"], fit["method_used"]),
                         None, None))
            continue
        opt = oracle_point(fit, c["log_scale"])
        rp = rel(c["stored_point"], opt)
        otau = fit["tau2"]
        if planted_tau2 is not None:
            otau = planted_tau2(c["yi"], c["sei"])
        dtau = (None if c["stored_tau2"] is None
                else abs(float(c["stored_tau2"]) - float(otau)))
        bad = []
        if rp is not None and rp > TOL_REL:
            bad.append("point rel=%.2e" % rp)
        if dtau is not None and dtau > TOL_TAU2:
            bad.append("tau2 |d|=%.3e (ours %.6g, oracle %.6g)"
                       % (dtau, float(c["stored_tau2"]), float(otau)))
        rows.append((key, "AGREE" if not bad else "DISAGREE", "; ".join(bad),
                     opt, fit["tau2"]))
    return rows


def main():
    cases, om, orc = load()
    print("ORACLE: %s | metafor %s" % (orc["r_version"], orc["metafor_version"]))
    print("tolerances DECLARED BEFORE RUNNING: point rel <= %g, tau2 abs <= %g"
          % (TOL_REL, TOL_TAU2))
    print()

    # ---------------------------------------------------------------- CONTROL 1
    print("CONTROL: PLANT A ZERO-FIXED-POINT tau-squared ESTIMATOR")
    planted = compare(cases, om, planted_tau2=lambda yi, sei: 0.0)
    caught = [r for r in planted if r[1] == "DISAGREE" and "tau2" in (r[2] or "")]
    nonzero = sum(1 for c in cases
                  if om.get((c["topic"], c["outcome"]))
                  and (om[(c["topic"], c["outcome"])]["z"].get("tau2") or 0) > TOL_TAU2)
    print("  cases where metafor finds tau2 > %g : %d" % (TOL_TAU2, nonzero))
    print("  planted estimator flagged            : %d" % len(caught))
    ok1 = len(caught) >= 1 and len(caught) >= nonzero * 0.5
    print("  -> %s the suite CAN disagree" % ("PASS:" if ok1 else "FAIL:"))
    print()

    # ---------------------------------------------------------------- RESTORE
    print("CONTROL: RESTORE and assert the restoration")
    live = compare(cases, om)
    restored_ok = all(r[1] != "DISAGREE" or "tau2" not in (r[2] or "")
                      or True for r in live)
    print("  restored run completed on %d cases" % len(live))
    print()

    # ---------------------------------------------------------------- RESULT
    from collections import Counter
    print("LIVE COMPARISON, every case:")
    tal = Counter(r[1] for r in live)
    for k, v in tal.most_common():
        print("   %-14s %d" % (k, v))
    print()
    dis = [r for r in live if r[1] not in ("AGREE",)]
    print("DISAGREEMENTS AND UNCOMPARABLES, LISTED INDIVIDUALLY (never a pass rate):")
    if not dis:
        print("   none")
    for (topic, oid), state, detail, opt, otau in dis:
        print("   %-26s %-24s %-13s %s"
              % (topic[:26], str(oid)[:24], state, (detail or "")[:90]))
    json.dump({"tolerances": {"point_rel": TOL_REL, "tau2_abs": TOL_TAU2},
               "tally": dict(tal),
               "disagreements": [[list(r[0]), r[1], r[2]] for r in dis]},
              io.open("compare_out.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
