"""A2 -- role inversion on the arms: the counts and the stored effect disagree in DIRECTION.

LINEAGE. Ranked #1 of the fourteen undefended classes on harm: "a harmful drug reads as
protective, with a plausible interval and nothing contradicting it". It is one of only two
classes that can make a reader act in the WRONG DIRECTION. Register A0 is its sibling at the
label layer (trial names swapped, IDs right); this is the same failure at the ARM layer.

THE TEST IS A SIGN TEST, SO THERE IS NOTHING TO TUNE. Every trial that records arms with
`role`, `events` and `participants` implies a crude risk ratio. The stored `point` is an
effect for the same contrast. If the arms were swapped, the stored effect is the reciprocal of
the implied one -- which means the two lie on OPPOSITE SIDES OF THE NULL. Direction is a sign,
not a magnitude: no tolerance, no epsilon, no threshold that could be fitted to one page.

WHY IT DOES NOT FIRE ON ADJUSTED ESTIMATES. A stored adjusted HR legitimately differs from a
crude count-derived RR in MAGNITUDE, and the standing orders forbid substituting a count-
derived ratio for a reported hazard ratio (register A21). It rarely differs in SIGN. To keep
that legitimate difference out of the finding set, the gate additionally requires the STORED
interval to exclude the null on its own terms -- a typed field the object already carries.
An estimate whose own CI spans the null is making no directional claim and is not accused.
"""
from __future__ import annotations

import math

# THE MEASURE MUST BE A RATIO, and this is a structural restriction on a typed field, not a
# threshold. The first run of this gate accused `MD 6.900` (a KCCQ mean difference) of
# contradicting a crude risk ratio. It does not: a mean difference is read against a null of
# ZERO, and 6.9 is the right side of it. Comparing a difference to a ratio is not a weak
# signal, it is a category error, and it produced a confident, plausible, WRONG accusation
# against a correct page -- the direction our detectors are measured to fail in. A measure
# this gate cannot classify is REFUSED and counted as out of reach, never quietly passed.
# A WHITELIST IN THE SAFE DIRECTION: a measure not named here is REFUSED and counted as out
# of reach, never judged and never counted clean. Separators are NORMALISED rather than
# enumerated -- the first version listed "rate ratio" and therefore refused the corpus's own
# "rate_ratio" on 4 rows, which is the open-vocabulary defect in miniature: a hand list that
# spells one variant and silently drops the others. Normalising derives every separator form
# from one entry instead of adding entries.
# Measured coverage on this corpus: 145 of 177 per_trial rows carry a measure this recognises
# as a ratio; 9 distinct measure values exist and 4 are refused (md, none, win_ratio,
# ratio-type-not-named-in-source), each for a stated reason.
# win_ratio is refused DELIBERATELY, not overlooked: its polarity is inverted relative to a
# risk ratio (a win ratio above 1 favours treatment), so judging it on the same sign rule
# would manufacture the very inversion this gate reports.
RATIO_MEASURES = ("rr", "or", "hr", "irr", "risk ratio", "odds ratio", "hazard ratio",
                  "rate ratio", "incidence rate ratio", "relative risk")
REFUSED_WITH_REASON = {"win_ratio": "polarity is inverted relative to a risk ratio",
                       "md": "a difference is read against a null of zero, not one",
                       "smd": "a difference is read against a null of zero, not one"}


def _normalise_measure(m):
    """Separator-insensitive: rate_ratio, rate-ratio and 'rate ratio' are one measure."""
    return " ".join(str(m or "").strip().lower().replace("_", " ").replace("-", " ").split())

TREATMENT_ROLES = ("treatment", "experimental", "intervention", "active")
CONTROL_ROLES = ("control", "comparator", "placebo", "usual care", "standard")


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def implied_risk_ratio(arms):
    """Crude RR = risk(treatment) / risk(control), from the arms' own recorded roles.

    Returns (rr, why_not). Refuses -- rather than guessing -- on anything it cannot resolve:
    a missing role, a zero denominator, or two arms sharing a role.
    """
    if not isinstance(arms, list) or len(arms) < 2:
        return None, "fewer than two arms recorded"
    t = [a for a in arms if isinstance(a, dict)
         and str(a.get("role", "")).strip().lower() in TREATMENT_ROLES]
    c = [a for a in arms if isinstance(a, dict)
         and str(a.get("role", "")).strip().lower() in CONTROL_ROLES]
    if len(t) != 1 or len(c) != 1:
        return None, "roles do not resolve to exactly one treatment and one control"
    te, tn = _num(t[0].get("events")), _num(t[0].get("participants"))
    ce, cn = _num(c[0].get("events")), _num(c[0].get("participants"))
    if None in (te, tn, ce, cn):
        return None, "an arm is missing events or participants"
    if tn <= 0 or cn <= 0:
        return None, "an arm has a non-positive denominator"
    if te <= 0 or ce <= 0:
        return None, "a zero event cell -- a crude ratio is undefined without a correction"
    return (te / tn) / (ce / cn), None


def side_of_null(value, null=1.0):
    if value is None:
        return None
    if value > null:
        return "above"
    if value < null:
        return "below"
    return "at"


def excludes_null(lo, hi, null=1.0):
    lo, hi = _num(lo), _num(hi)
    if lo is None or hi is None:
        return False
    return (lo > null and hi > null) or (lo < null and hi < null)


def scan(obj, topic="fixture"):
    """(rows, seen). One row per per_trial estimate whose DIRECTION contradicts its own arms."""
    rows = []
    seen = {"per_trial_rows": 0, "rows_joined_to_arms": 0, "rows_with_usable_counts": 0,
            "rows_on_a_ratio_measure": 0, "rows_with_a_directional_claim": 0,
            "rows_refused_non_ratio_measure": 0}
    arms_by_nct = {}
    for t in (obj.get("inputs") or {}).get("trials") or []:
        if isinstance(t, dict) and t.get("nct"):
            arms_by_nct[t["nct"]] = t.get("arms")

    for oid, block in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(block, dict):
            continue
        for r in block.get("per_trial") or []:
            if not isinstance(r, dict):
                continue
            seen["per_trial_rows"] += 1
            nct = r.get("nct")
            if nct not in arms_by_nct:
                continue
            seen["rows_joined_to_arms"] += 1
            rr, why_not = implied_risk_ratio(arms_by_nct[nct])
            if rr is None:
                continue
            seen["rows_with_usable_counts"] += 1
            if _normalise_measure(r.get("measure")) not in [_normalise_measure(m) for m in RATIO_MEASURES]:
                seen["rows_refused_non_ratio_measure"] += 1
                continue
            seen["rows_on_a_ratio_measure"] += 1
            point = _num(r.get("point"))
            if point is None or point <= 0:
                continue
            if not excludes_null(r.get("ci_low"), r.get("ci_high")):
                continue
            seen["rows_with_a_directional_claim"] += 1
            s_stored, s_implied = side_of_null(point), side_of_null(rr)
            if s_stored != s_implied and "at" not in (s_stored, s_implied):
                rows.append({
                    "topic": topic, "outcome": oid, "nct": nct,
                    "stored": point, "implied": rr,
                    "measure": r.get("measure"),
                    "detail": ("%s in outcome %r: the arms this object records imply a crude "
                               "risk ratio of %.3f (%s the null) while the stored %s is %.3f "
                               "(%s the null, CI %s to %s, which excludes it). The counts and "
                               "the published effect point OPPOSITE WAYS; log-ratio sum is "
                               "%.3f, and a sum near zero is the signature of swapped arms."
                               % (nct, oid, rr, s_implied, r.get("measure") or "effect",
                                  point, s_stored, r.get("ci_low"), r.get("ci_high"),
                                  math.log(point) + math.log(rr))),
                })
    return rows, seen
