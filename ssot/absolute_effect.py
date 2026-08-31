# -*- coding: utf-8 -*-
"""Absolute effects from a pooled ratio, for ANY topic. Standalone, no network.

    python ssot/absolute_effect.py --incidence-per-1000 1.0
    python ssot/absolute_effect.py --object ssot/<topic>/<topic>.json
    python ssot/absolute_effect.py --corpus            # every topic, gated

WHY IT IS GATED AND NOT UNIVERSAL. A relative risk becomes an absolute one only
against a baseline risk, and a baseline risk belongs to a POPULATION. Applying a
pooled ratio to a reader's own incidence is only defensible where the review has
said, in the store, how far its evidence transfers -- otherwise the table
silently invites a reader in Kampala to apply an estimate measured somewhere
else, and dresses that in arithmetic.

SO THE GATE IS: a pooled RATIO measure, AND a declared indirectness argument.
Both, or the module DECLINES AND SAYS WHY. A refusal that names its reason is
the output; an absolute table produced anyway is not.

⭐ THE SIGN TRAP, ASSERTED RATHER THAN COMMENTED. The interval bounds INVERT
when a ratio becomes a count prevented: the HIGH relative risk gives the LOW
number of events prevented. Getting it backwards makes the benefit look better
at its worst, which is the direction nobody checks. `_rows` asserts the ordering
on every row it builds.

NO NETWORK. NO TOPIC NAMES. Works on a canon dict or standalone from a number.
"""
import argparse
import glob
import io
import json
import math
import os
import sys

RATIO_MEASURES = ("RR", "OR", "HR", "IRR")

# The corpus spells the same measure several ways. Normalising is not tidying:
# an unnormalised lookup declined a HAZARDRATIO block as "not a ratio", which
# is a false statement about that review produced by this module's vocabulary.
_MEASURE_ALIASES = {
    "RISKRATIO": "RR", "RELATIVERISK": "RR", "RR": "RR",
    "ODDSRATIO": "OR", "OR": "OR",
    "HAZARDRATIO": "HR", "HR": "HR",
    "RATERATIO": "IRR", "INCIDENCERATERATIO": "IRR", "IRR": "IRR",
}

# A baseline-risk grid the READER moves along, rather than one assumed risk the
# review author picked on behalf of a jurisdiction they do not know.
DEFAULT_GRID = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0)


def measure_of(canon, oid, res):
    """Find the summary measure, and RETURN WHERE IT WAS READ FROM.

    ⚠️ THE FIRST VERSION OF THIS FUNCTION LOOKED IN TWO PLACES AND THE CORPUS
    USES THREE. It checked `pooled.measure` and `results...measure`, and
    declined 87 of 146 outcome-blocks with the message "the pooled measure is
    not recorded" -- a sentence about the store that was actually about this
    lookup. The measure lives at `outcomes[].measure` on 77 blocks where
    `pooled.measure` is absent.

    A gate that declines for a reason it invented is worse than no gate, so the
    path is returned beside the value and printed in the refusal. Precedence is
    declared rather than incidental: the pooled block is the most specific, the
    per-outcome result next, the outcomes[] declaration last.
    """
    outs = {o.get("id"): o for o in (canon.get("outcomes") or [])
            if isinstance(o, dict)}
    pooled = res.get("pooled") if isinstance(res.get("pooled"), dict) else {}
    for value, path in (
            (pooled.get("measure"), "results.by_outcome.%s.pooled.measure" % oid),
            (res.get("measure"), "results.by_outcome.%s.measure" % oid),
            (res.get("effect_measure"),
             "results.by_outcome.%s.effect_measure" % oid),
            ((outs.get(oid) or {}).get("measure"), "outcomes[id=%s].measure" % oid)):
        if value:
            raw = str(value).replace(" ", "").replace("-", "").replace("_", "").upper()
            return (_MEASURE_ALIASES.get(raw, raw), path)
    return (None, "not found in pooled.measure, results.*.measure, "
                  "results.*.effect_measure or outcomes[].measure")


def _indirectness_argument(canon, oid, res):
    """A DECLARED argument about transfer. Either a stored indirectness domain
    with a reason, or a declared question_pico the domain could be derived from.

    ⛔ NOT the trial populations. Reading transferability off who was enrolled
    returns 'transfers everywhere it was measured', which is not an argument."""
    g = (res.get("grade") or {}).get("indirectness") or \
        (((canon.get("grade") or {}).get("by_outcome") or {}).get(oid) or {}).get("indirectness")
    if isinstance(g, dict) and (g.get("reason") or g.get("state")):
        return {"kind": "stored_indirectness_domain",
                "state": g.get("state"), "reason": g.get("reason"),
                "path": "results.by_outcome.%s.grade.indirectness" % oid}
    q = res.get("question_pico")
    if isinstance(q, dict) and q.get("population"):
        return {"kind": "declared_question_pico",
                "state": None,
                "reason": ("The review declares its own population as %r, so "
                           "the limits of transfer are stated even though the "
                           "domain has not been rated." % q.get("population")),
                "path": "results.by_outcome.%s.question_pico" % oid}
    return None


# ⭐ THE EXISTENCE PROOF FOR DECLARED DERIVATIONS. ONE PROJECTOR, NOT ALL.
#
# Measured on the delivered dapivirine page: 1,801 distinct numbers rendered,
# 1,761 present verbatim in the store, 40 NOT. All forty traced -- every one a
# legitimate derivation, 21 of them produced by THIS function.
#
# ⛔ SO A FABRICATION DETECTOR THAT COMPARES RENDERED VALUES AGAINST STORED ONES
# ACCUSES EVERY DERIVED VALUE, AND DERIVATION IS THE ENTIRE PURPOSE OF A
# PROJECTOR. 0% precision by construction, and it INVERTS THE INCENTIVE: the
# more working a page shows, the more it is accused.
#
# The whole gap was one sentence -- this function already knows
# `baseline x (1 - ratio)` and nothing wrote it down where a checker could read
# it. `derivation_record()` writes it down. A checker can now recompute a
# rendered value from named store fields instead of asking whether the string
# appears somewhere.
#
# ⚠️ WHAT THIS DOES NOT DO. It declares ONE derivation on ONE projector. It is
# an existence proof that makes the rest schedulable, not coverage: every other
# render-time computation on that page -- the ledger's link count, the recompute
# envelope's points, the harms risk ratios -- is still undeclared and would
# still be accused.
# ⭐ THE SHAPE IS allmeta-02's `render_derivation`, NOT ONE OF MY OWN.
#
# I wrote a bespoke `derivation_record` first and then asked for their shape
# rather than shipping mine, because TWO CONVENTIONS FOR ONE FACT IS HOW THE
# INDEX ACQUIRED FOUR DESCRIPTIONS OF ONE URL. Theirs is ratified in
# ssot/claims.py, carries a required field list enforced by validate_claim, and
# has a recompute function this module calls rather than reimplements.
#
# FOUR PROPERTIES OF IT THAT MATTER, and none is decoration:
#   `op` is a KEY INTO claims.RENDER_OPS, never an expression. A declaration
#       carrying a string to evaluate would invite the checker to run
#       page-supplied text, and the fabrication detector is the last place that
#       should exist.
#   `inputs` are DOTTED PATHS from the object root, same addressing as
#       origins()/resolve(). One that does not resolve RAISES -- a declaration a
#       checker cannot follow is unverifiable, which is the state it exists to
#       remove. A value not in the store is passed as {"literal": x}, explicitly.
#   `produces` is REQUIRED, so the checker can say "the page shows 1.485, the
#       declaration says complement_product(5.0, 0.703), and that is 1.485"
#       rather than "a projector asserts this is fine".
#   it reuses __claim/__evidence rather than forking a parallel key.
#
# ⛔ AND THE DECLARATION IS VERIFIED IN THE SAME PASS THAT EMITS IT. A
# declaration never checked against the value it claims to produce is the same
# shape as a gate that has never fired -- and this module already shipped one
# check that could only pass, so the rule is applied here rather than trusted.
DERIVATION_OP = "complement_product"


def render_declarations(canon, oid, rows, per=1000):
    """One `render_derivation` per rendered number, each VERIFIED as emitted.

    Returns (declarations, failures). A declaration that does not recompute is
    NOT emitted -- it is returned as a failure, because emitting an unverified
    declaration would launder a wrong number into a checkable-looking one."""
    try:
        import claims as _c
    except ImportError:
        from . import claims as _c
    point_path = "results.by_outcome.%s.pooled.point" % oid
    decls, fails = [], []
    for r in rows or []:
        b = r.get("baseline_per_%d" % per)
        got = r.get("events_prevented_per_%d" % per)
        if b is None or got is None:
            continue
        decl = {"op": DERIVATION_OP,
                "inputs": [{"literal": b}, point_path],
                "produces": got,
                "by": "ssot/absolute_effect.py",
                "at": "render",
                "authored": False}
        try:
            ok, recomputed = _c.verify_render(canon, decl)
        except Exception as exc:
            fails.append({"baseline": b, "why": "%s: %s" % (type(exc).__name__,
                                                            str(exc)[:80])})
            continue
        if not ok:
            fails.append({"baseline": b, "produces": got,
                          "recomputed": recomputed,
                          "why": "declaration does not reproduce the rendered value"})
            continue
        decls.append(decl)
    return decls, fails


def recompute_check(canon, oid, rows, per=1000):
    """Reproduce EMITTED rows from the declared inputs. Errors, or [].

    ⛔ THIS TAKES THE ROWS AS AN ARGUMENT, AND THE FIRST VERSION DID NOT.
    It called `_rows()` -- the very function that produced the table -- and
    compared the result with itself, so it could only ever pass. That is the
    control failure this module's own derivation_record docstring warns about,
    committed in the check written to demonstrate the fix, and it was caught
    only because a negative test tried to make it fail and could not.
    ⇒ A CHECK THAT REGENERATES ITS SUBJECT IS NOT CHECKING IT.

    So the arithmetic here is written out INDEPENDENTLY of `_rows` -- the
    declared formula, applied to the declared input fields, compared against
    values that arrived from somewhere else.
    """
    res = (((canon.get("results") or {}).get("by_outcome") or {}).get(oid) or {})
    pooled = res.get("pooled") or {}
    pt, lo, hi = pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")
    if not (pt and lo and hi):
        return ["cannot recompute: the declared inputs are not all present"]
    errs = []
    for r in rows or []:
        b = r.get("baseline_per_%d" % per)
        if b is None:
            continue
        # THE DECLARED FORMULA, WRITTEN OUT. Not a call back into the producer.
        want = round(b * (1.0 - pt), 4)
        want_lo = round(b * (1.0 - hi), 4)      # HIGH ratio -> FEWEST prevented
        want_hi = round(b * (1.0 - lo), 4)
        got = r.get("events_prevented_per_%d" % per)
        gci = r.get("prevented_ci") or [None, None]
        if got is None or abs(want - got) > 1e-9:
            errs.append("baseline %s: declared formula gives %s, row carries %s"
                        % (b, want, got))
        if gci[0] is None or abs(want_lo - gci[0]) > 1e-9:
            errs.append("baseline %s: lower bound should be %s, row carries %s"
                        % (b, want_lo, gci[0]))
        if gci[1] is None or abs(want_hi - gci[1]) > 1e-9:
            errs.append("baseline %s: upper bound should be %s, row carries %s"
                        % (b, want_hi, gci[1]))
    return errs


def _rows(ratio, lo, hi, grid, per):
    out = []
    for b in grid:
        prevented = b * (1.0 - ratio)
        p_lo = b * (1.0 - hi)      # HIGH ratio -> FEWEST prevented
        p_hi = b * (1.0 - lo)      # LOW  ratio -> MOST prevented
        assert p_lo <= prevented <= p_hi, (
            "interval bounds inverted at baseline %s: %s / %s / %s -- the HIGH "
            "ratio must give the LOW number prevented" % (b, p_lo, prevented, p_hi))
        row = {"baseline_per_%d" % per: b,
               "with_the_intervention": round(b * ratio, 4),
               "events_prevented_per_%d" % per: round(prevented, 4),
               "prevented_ci": [round(p_lo, 4), round(p_hi, 4)]}
        if prevented > 0:
            row["number_needed_to_treat"] = int(round(per / prevented))
            row["nnt_ci"] = [int(round(per / p_hi)) if p_hi > 0 else None,
                             int(round(per / p_lo)) if p_lo > 0 else None]
        out.append(row)
    return out


def derive(canon, oid="primary", per=1000, grid=DEFAULT_GRID):
    """Absolute effects for one outcome of any topic, or a REFUSAL that says why."""
    res = (((canon.get("results") or {}).get("by_outcome") or {}).get(oid) or {})
    pooled = res.get("pooled") or {}
    measure, mpath = measure_of(canon, oid, res)
    point, lo, hi = pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")

    # A pool the object records as deliberately ABSENT is not a missing
    # measure. Saying so keeps "we did not pool" distinguishable from "we
    # could not read the pool", which are different facts about the review.
    if pooled.get("absent"):
        return {"state": "DECLINED", "outcome": oid,
                "reason": "The pool is recorded ABSENT by the object itself: %s"
                          % (pooled.get("absent_reason") or "no reason given")}
    if not measure:
        return {"state": "DECLINED", "outcome": oid,
                "reason": "No summary measure is recorded (%s)." % mpath}
    if measure not in RATIO_MEASURES:
        return {"state": "DECLINED", "outcome": oid,
                "reason": "The summary measure is %r, read from %s, which is "
                          "not a ratio. An absolute effect needs a ratio and a "
                          "baseline risk." % (measure, mpath)}
    if not (point and lo and hi):
        return {"state": "DECLINED", "reason":
                "No pooled point estimate with an interval is stored.",
                "outcome": oid}

    ind = _indirectness_argument(canon, oid, res)
    if not ind:
        return {"state": "DECLINED", "outcome": oid, "measure": measure,
                "measure_read_from": mpath,
                "reason": (
                    "⛔ NO DECLARED INDIRECTNESS ARGUMENT. This topic holds a "
                    "pooled %s of %s but says nothing about how far it "
                    "transfers -- no rated indirectness domain and no declared "
                    "question_pico. An absolute table built here would invite "
                    "a reader to apply this estimate to their own population "
                    "with no statement of whether that is supported, and "
                    "arithmetic is not a substitute for that statement."
                    % (measure, point)),
                "what_would_unlock_it": (
                    "Declare question_pico, or rate the indirectness domain. "
                    "Either is one declaration.")}

    if measure == "OR":
        note = ("⚠️ AN ODDS RATIO IS NOT A RISK RATIO. Converting one to an "
                "absolute risk requires the baseline risk AND the assumption "
                "that the odds ratio is constant across it. At the low "
                "baselines below the two nearly coincide; at high baselines "
                "they do not, and this table treats the odds ratio as a risk "
                "ratio, which OVERSTATES the effect as the baseline rises.")
    elif measure in ("HR", "IRR", "RATERATIO", "RATE_RATIO"):
        note = ("⚠️ A HAZARD OR RATE RATIO applied to a cumulative baseline "
                "risk assumes the ratio is constant over the follow-up. Where "
                "the contributing trials ran for different lengths that "
                "assumption is doing real work and is not tested here.")
    else:
        note = ("A risk ratio applied to a baseline risk, which is the "
                "arithmetic GRADE's summary-of-findings table performs.")

    _rows_out = _rows(point, lo, hi, grid, per)
    _decls, _fails = render_declarations(canon, oid, _rows_out, per)
    # Recompute each CLASS independently so one cannot mask another.
    _cls = {"point": [0, 0], "lower_bound": [0, 0], "upper_bound": [0, 0]}
    for _r in _rows_out:
        b = _r.get("baseline_per_%d" % per)
        ci = _r.get("prevented_ci") or [None, None]
        for name, want, got in (
                ("point", round(b * (1.0 - point), 4),
                 _r.get("events_prevented_per_%d" % per)),
                ("lower_bound", round(b * (1.0 - hi), 4), ci[0]),
                ("upper_bound", round(b * (1.0 - lo), 4), ci[1])):
            _cls[name][1] += 1
            if got is not None and abs(want - got) <= 1e-9:
                _cls[name][0] += 1
    _verified_by_class = {k: "%d of %d" % (v[0], v[1]) for k, v in _cls.items()}
    _verified_by_class["_why_split"] = (
        "The interval INVERTS -- ci_high gives the FEWEST events prevented. A "
        "sign error would leave `point` at 100% and fail both bounds, and a "
        "pooled rate would report that as clean.")
    return {
        "state": "EMITTED",
        "outcome": oid,
        "measure": measure,
        "measure_read_from": mpath,
        "pooled": {"point": point, "ci_low": lo, "ci_high": hi},
        "units": "per %d people" % per,
        "_why_a_grid_and_not_one_assumed_risk": (
            "A single assumed baseline risk is a modelling choice the review "
            "author makes on behalf of a jurisdiction they do not know. The "
            "grid is given so the reader applies their own incidence."),
        "indirectness_argument_that_licenses_this": ind,
        "measure_caveat": note,
        "rows": _rows_out,
        "render_derivations": _decls,
        "render_derivations_that_did_NOT_verify": _fails,
        "__claim": "render_derivation",
        # ⛔ BROKEN OUT BY CLASS, NOT POOLED. From run 1: two AI families on
        # identical material agreed 99 of 105 -- and that 94% concealed 98/98
        # on FAIL against 1 OF 7 ON VERIFIED, near-total disagreement on the
        # only verdict that mattered. A pooled rate over an imbalanced set
        # hides the class that is failing, and the class that is failing is
        # always the small one.
        #
        # Here the three classes are the point estimate, the lower bound and
        # the upper bound. They are NOT interchangeable: the interval INVERTS
        # (ci_high gives the FEWEST prevented), so a sign error would leave the
        # point-estimate class at 100% while both bound classes failed, and a
        # pooled "21 of 21" would report that as clean.
        "_derivations_verified_by_class": _verified_by_class,
        "_derivations_verified": "%d of %d rendered POINT values recompute from "
                                 "their declaration; bounds reported separately "
                                 "because a pooled rate would hide a sign error "
                                 "in one class" % (len(_decls), len(_rows_out)),
        "_derived_by": "ssot/absolute_effect.py derive()",
        # emitted below, after the rows exist and each has been verified
        "_generality": ("Fires on ANY topic with a pooled ratio measure and a "
                        "declared indirectness argument. Not written per "
                        "topic."),
    }


def _cli():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--incidence-per-1000", type=float, default=None,
                    help="a single baseline risk, per 1000 people")
    ap.add_argument("--ratio", type=float, default=None)
    ap.add_argument("--ci", nargs=2, type=float, default=None,
                    metavar=("LOW", "HIGH"))
    ap.add_argument("--object", default=None, help="path to a topic JSON")
    ap.add_argument("--outcome", default="primary")
    ap.add_argument("--corpus", action="store_true",
                    help="run over every topic and report the gate")
    ap.add_argument("--per", type=int, default=1000)
    a = ap.parse_args()

    if a.corpus:
        here = os.path.dirname(os.path.abspath(__file__))
        files = [f for f in sorted(glob.glob(os.path.join(here, "*", "*.json")))
                 if not f.endswith(".striptest")]
        emitted = declined = 0
        reasons = {}
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
                r = derive(canon, oid, per=a.per)
                if r["state"] == "EMITTED":
                    emitted += 1
                else:
                    declined += 1
                    key = r["reason"][:52]
                    reasons[key] = reasons.get(key, 0) + 1
        tot = emitted + declined
        print("ABSOLUTE EFFECT -- CORPUS GATE")
        print("  outcome-blocks with a pooled result : %d  <- denominator" % tot)
        print("  EMITTED                             : %d of %d" % (emitted, tot))
        print("  DECLINED                            : %d of %d" % (declined, tot))
        print()
        for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
            print("    %4d  %s..." % (v, k))
        return

    if a.object:
        canon = json.load(open(a.object, encoding="utf-8"))
        r = derive(canon, a.outcome, per=a.per)
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return

    if a.ratio is None:
        ap.error("give --ratio (with --ci), or --object, or --corpus")
    lo, hi = (a.ci if a.ci else (a.ratio, a.ratio))
    grid = ([a.incidence_per_1000] if a.incidence_per_1000 is not None
            else list(DEFAULT_GRID))
    print("ABSOLUTE EFFECT  ratio %.4f (%.4f to %.4f), per %d people"
          % (a.ratio, lo, hi, a.per))
    print()
    print("  %-14s %-14s %-26s %s"
          % ("baseline", "with", "prevented (95% CI)", "NNT (95% CI)"))
    for row in _rows(a.ratio, lo, hi, grid, a.per):
        b = row["baseline_per_%d" % a.per]
        pv = row["events_prevented_per_%d" % a.per]
        ci = row["prevented_ci"]
        nnt = row.get("number_needed_to_treat")
        nci = row.get("nnt_ci") or [None, None]
        print("  %-14s %-14s %-26s %s"
              % (b, row["with_the_intervention"],
                 "%.4f (%.4f to %.4f)" % (pv, ci[0], ci[1]),
                 ("%s (%s to %s)" % (nnt, nci[0], nci[1])) if nnt else "—"))
    print()
    print("  ⚠️ THE INTERVAL INVERTS: the HIGH ratio gives the FEWEST events")
    print("     prevented. Asserted on every row rather than commented.")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    _cli()
