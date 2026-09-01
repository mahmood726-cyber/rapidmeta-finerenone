# -*- coding: utf-8 -*-
"""GAP 3 -- MECHANICAL GRADE *INPUTS*. THE DOWNGRADE IS DELIBERATELY NOT SCORED.

THE BINDING CONSTRAINT, AND IT IS STRUCTURAL RATHER THAN A CONVENTION
  GRADE certainty is a judgement the Cochrane Handbook places with the review authors and
  a panel. We have no panel. So this module emits the QUANTITIES a panel would read -- k,
  n, I-squared, tau-squared, interval width, design, and mechanical indirectness signals --
  and it CANNOT emit a certainty. `certainty` is not merely left None: the constructor
  REFUSES a certainty if one is passed, so a later caller cannot quietly start setting it.

  A convention that relies on someone remembering will be broken by the next person in a
  hurry, and it fails silently. This one raises.

NO MODEL IS INVOLVED, so no RAISE declaration is required: every field is arithmetic on
numbers already in the object, or a regex over text already in the object. Nothing here
makes or suggests a judgement, and nothing here writes a number the object did not have.
"""
import math
import re

SURROGATE_OUTCOMES = (
    r"\bHbA1c\b|glycated haemoglobin|\bLDL\b|cholesterol|blood pressure|"
    r"ejection fraction|\bBNP\b|\bNT-proBNP\b|viral load|CD4 count|bone mineral density|"
    r"\beGFR\b|proteinuria|albuminuria|tumou?r response|progression[- ]free survival"
)
COMPOSITE = r"\bcomposite\b|\bMACE\b|major adverse cardiac|death or |or hospitalisation|or hospitalization"


class CertaintyRefused(Exception):
    """Raised when a caller tries to attach a GRADE certainty rating."""


def _i_squared(q, df):
    """I^2 from Cochran's Q. Returns None when undefined; NEVER a silent zero.
    Undefined for df<=0, and floored at 0 by definition when Q<df."""
    if q is None or df is None or df <= 0:
        return None
    return max(0.0, (q - df) / float(q)) if q > 0 else 0.0


def _interval_width_ratio(lo, hi):
    """On a ratio scale the meaningful width is hi/lo, not hi-lo. None if not computable."""
    try:
        if lo is None or hi is None or lo <= 0 or hi <= 0:
            return None
        return hi / float(lo)
    except (TypeError, ZeroDivisionError):
        return None


def grade_inputs(k=None, n_total=None, q=None, df=None, tau2=None,
                 ci_lower=None, ci_upper=None, point=None, scale="ratio",
                 design=None, outcome_text="", population_text="",
                 certainty=None, **_ignored):
    """Emit the mechanical inputs to a GRADE assessment. Never the assessment."""
    if certainty is not None:
        raise CertaintyRefused(
            "GRADE certainty is a panel judgement under Cochrane Handbook v6.5 and this "
            "system has no panel. Emit the inputs and let a human rate them.")

    if df is None and k is not None:
        df = k - 1
    i2 = _i_squared(q, df)
    width = _interval_width_ratio(ci_lower, ci_upper) if scale == "ratio" else (
        (ci_upper - ci_lower) if (ci_lower is not None and ci_upper is not None) else None)

    null = 1.0 if scale == "ratio" else 0.0
    crosses = None
    if ci_lower is not None and ci_upper is not None:
        crosses = bool(ci_lower <= null <= ci_upper)

    ot = outcome_text or ""
    return {
        # --- what a panel reads ---
        "k": k,
        "n_total": n_total,
        "df": df,
        "q": q,
        "i_squared": None if i2 is None else round(i2, 4),
        "tau_squared": tau2,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "point_estimate": point,
        "scale": scale,
        "interval_width_ratio": None if width is None else round(width, 4),
        "interval_crosses_no_effect": crosses,
        "design": design,
        # --- mechanical signals ONLY: presence of a pattern, never a downgrade ---
        "indirectness_signals": {
            "outcome_matches_surrogate_list": bool(re.search(SURROGATE_OUTCOMES, ot, re.I)),
            "outcome_is_composite": bool(re.search(COMPOSITE, ot, re.I)),
            "surrogate_terms_found": sorted(set(m.group(0) for m in
                                                re.finditer(SURROGATE_OUTCOMES, ot, re.I))),
            "population_text_present": bool((population_text or "").strip()),
        },
        # --- the refusal, carried IN the payload so it travels with any subset ---
        "certainty": None,
        "certainty_is_not_emitted_because": (
            "GRADE certainty is a judgement the Cochrane Handbook (v6.5) assigns to the "
            "review authors and a panel. This system has no panel, so it emits the inputs "
            "and does not rate them. A certainty appearing in this field would be a defect."),
        "downgrade_domains_scored": [],
        "emitted_by": "grade_inputs.py (mechanical; no model, no judgement, no panel)",
    }


# ------------------------------------------------------------------ controls
def _controls():
    """Known-answer controls. A plant validates an implementation; only a known answer
    validates the intention -- so these are hand-computed, not taken from the code."""
    out = []

    # 1. KNOWN ANSWER: Q=10, df=4 -> I2 = (10-4)/10 = 0.60 exactly.
    g = grade_inputs(k=5, q=10.0, ci_lower=0.5, ci_upper=2.0)
    out.append(("I2 known answer 0.60", abs(g["i_squared"] - 0.60) < 1e-9, g["i_squared"]))

    # 2. KNOWN ANSWER: Q<df must floor at 0, not go negative.
    g2 = grade_inputs(k=5, q=2.0)
    out.append(("I2 floors at 0 when Q<df", g2["i_squared"] == 0.0, g2["i_squared"]))

    # 3. KNOWN ANSWER: width ratio 2.0/0.5 = 4.0
    out.append(("interval width ratio 4.0", abs(g["interval_width_ratio"] - 4.0) < 1e-9,
                g["interval_width_ratio"]))

    # 4. MUST-FIRE: an interval spanning 1 must be flagged as crossing no effect.
    out.append(("crosses no effect fires", g["interval_crosses_no_effect"] is True,
                g["interval_crosses_no_effect"]))

    # 5. MUST-NOT-FIRE: an interval entirely below 1 must NOT be flagged.
    g3 = grade_inputs(k=5, q=10.0, ci_lower=0.6, ci_upper=0.9)
    out.append(("crosses no effect stays silent", g3["interval_crosses_no_effect"] is False,
                g3["interval_crosses_no_effect"]))

    # 6. MUST-FIRE: a surrogate outcome must be detected.
    g4 = grade_inputs(k=3, outcome_text="Change in HbA1c at 24 weeks")
    out.append(("surrogate detected", g4["indirectness_signals"]["outcome_matches_surrogate_list"],
                g4["indirectness_signals"]["surrogate_terms_found"]))

    # 7. MUST-NOT-FIRE: a hard clinical outcome must NOT be called a surrogate.
    g5 = grade_inputs(k=3, outcome_text="All-cause mortality at 12 months")
    out.append(("hard outcome not flagged",
                g5["indirectness_signals"]["outcome_matches_surrogate_list"] is False,
                g5["indirectness_signals"]["surrogate_terms_found"]))

    # 8. I2 UNDEFINED must be None, never 0 -- a blank and a zero are different facts.
    g6 = grade_inputs(k=1, q=None)
    out.append(("I2 undefined is None not 0", g6["i_squared"] is None, g6["i_squared"]))

    # 9. THE STRUCTURAL REFUSAL must actually raise.
    try:
        grade_inputs(k=5, certainty="moderate")
        out.append(("certainty refused", False, "DID NOT RAISE"))
    except CertaintyRefused:
        out.append(("certainty refused", True, "raised"))

    # 10. certainty is None on every emission.
    out.append(("certainty always None", g["certainty"] is None, g["certainty"]))
    return out


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    print("GAP 3 -- mechanical GRADE inputs. Certainty is structurally refused.")
    print("cmd: python grade_inputs.py")
    print("")
    rows = _controls()
    for name, ok, got in rows:
        print("  %-32s %-5s  got=%s" % (name, "PASS" if ok else "FAIL", got))
    bad = [r for r in rows if not r[1]]
    print("")
    print("VERDICT  %d/%d controls pass%s" % (len(rows) - len(bad), len(rows),
                                              "" if not bad else "  -- FAILURES PRESENT"))
    raise SystemExit(1 if bad else 0)
