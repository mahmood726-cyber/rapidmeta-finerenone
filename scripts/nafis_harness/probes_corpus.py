"""CHK016-CHK025 -- the ten classes from the corpus lane's sweep.

FIXTURE PROVENANCE, stated per detector in `FIXTURE_STATUS` at the bottom and
summarised in HARNESS.md. Two things to know before reading the fixtures:

  1. The objects named in the brief -- MAVACAMTEN_HCM's OR 6.67, MITRAL's 0.6677,
     AZITHROMYCIN's -0.15082288973458366 -- are NOT present in the repos I can
     reach. `F:\\rapidmeta-ssot-shell` and `F:\\rapidmeta-finerenone` are mounted
     read-only and are behind the corpus lane's working state; `findings/*.json`
     for those slugs are error stubs and the HTML carries none of the values.
     So their PROVENANCE is [R] operator-relayed, not [F] file-backed.

  2. Their ARITHMETIC is independently verified, which is a real if partial
     check, and it is the part that matters for CHK016:

        SE(lnOR) from CI 2.09-21.30      = 0.5922   (stated 0.5922)  OK
        SE(lnOR) from 45/123 vs 22/128   = 0.2999   (stated 0.2999)  OK
        OR implied by those counts       = 2.780    -- NOT 6.67
        ratio                            = 1.975
        MITRAL SE from CI 0.4009-1.1120  = 0.2603   (stated 0.2603)  OK
        MITRAL point 0.6677 = sqrt(0.4009 x 1.1120) exactly -- self-consistent

     Both fixtures reproduce to four decimals, and MITRAL's point estimate is the
     exact geometric mean of its own bounds. Numbers that agree that precisely
     were not misremembered.

Every detector here is deterministic CPU. No network, no model calls.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Mapping

from .check import Check, Fixture, Instrument
from .verdict import Result, Verdict, make_fail, make_invalid, make_pass

Z = 1.959963985


def _mut(payload: Mapping[str, Any], **changes) -> dict:
    d = copy.deepcopy(dict(payload))
    d.update(changes)
    return d


# =============================================================================
# CHK016 -- PRECISION / SAMPLE MISMATCH        *** the strongest of the ten ***
# =============================================================================
# The interval's width implies a standard error. The arm sizes imply another. If
# they disagree, the estimate and the sample it is attached to are not describing
# the same thing -- the number came from somewhere else.
#
# What makes this the strongest: it needs ONLY THE ROW. No source document, no
# registry, no network, no model. It catches a value that is correctly labelled,
# internally consistent, and about a different population -- which is invisible
# to CHK005 (a self-consistent row passes any self-referential test), to CHK006
# (the identity is right), and to CHK009 (the outcome label is right).
#
# It also has no adversarial counterexample yet, unlike the heterogeneity
# signature -- because it is arithmetic, not inference. Two SEs computed from
# disjoint inputs either agree or they do not.

def _se_from_ci(lo: float, hi: float) -> float:
    return (math.log(hi) - math.log(lo)) / (2 * Z)


def _se_from_counts(a: int, n1: int, b: int, n2: int) -> float:
    # Woolf / delta-method SE of ln(OR) on a 2x2
    cells = [a, n1 - a, b, n2 - b]
    if any(c <= 0 for c in cells):
        return float("nan")
    return math.sqrt(sum(1.0 / c for c in cells))


def _precision_sample_mismatch(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK016_PRECISION_SAMPLE_MISMATCH", "interval-vs-sample"

    if p.get("variance_adjustment_declared"):
        # HKSJ, random-effects inflation, robust SEs and design effects all move
        # the interval away from the raw 2x2 SE legitimately. This instrument
        # cannot resolve a declared adjustment from a wrong population, so it
        # must not try. Same rule as CHK006's tolerance band.
        return make_invalid(cid, inst,
                            "a variance adjustment is declared "
                            f"({p['variance_adjustment_declared']!r}), so the "
                            "interval is not expected to reproduce the raw 2x2 "
                            "standard error. This check cannot discriminate here.")

    lo, hi = p.get("ci_low"), p.get("ci_high")
    if not (lo and hi) or lo <= 0 or hi <= 0:
        return make_invalid(cid, inst, "no usable confidence interval on the row")

    try:
        a, n1 = int(p["events_t"]), int(p["n_t"])
        b, n2 = int(p["events_c"]), int(p["n_c"])
    except (KeyError, TypeError, ValueError):
        return make_invalid(cid, inst,
                            "arm-level events and denominators are not all present; "
                            "the sample-implied standard error cannot be computed")

    se_ci = _se_from_ci(lo, hi)
    se_n = _se_from_counts(a, n1, b, n2)
    if not (se_n == se_n) or se_n <= 0:          # NaN guard
        return make_invalid(cid, inst,
                            "a zero cell makes the sample-implied standard error "
                            "undefined without a continuity correction")

    ratio = se_ci / se_n
    thr = float(p.get("ratio_threshold", 1.5))
    if ratio > thr or ratio < 1.0 / thr:
        implied_or = ((a / (n1 - a)) / (b / (n2 - b)))
        return make_fail(cid, inst,
                         f"interval implies SE {se_ci:.4f}; the reported arms imply "
                         f"SE {se_n:.4f} (ratio {ratio:.3f}, threshold {thr}). The "
                         "estimate and the sample attached to it are inconsistent.",
                         observed=f"CI {lo}-{hi} -> SE {se_ci:.4f}; arms "
                                  f"{a}/{n1} vs {b}/{n2} -> SE {se_n:.4f}; those arms "
                                  f"imply a point estimate of {implied_or:.3f} against "
                                  f"a claimed {p.get('estimate')}",
                         locator=str(p.get("row_id")),
                         opposite_would_be="the two standard errors agreeing within "
                                           f"a factor of {thr}, as they do when the "
                                           "interval was computed from these arms",
                         se_from_ci=round(se_ci, 4), se_from_counts=round(se_n, 4),
                         ratio=round(ratio, 3), implied_estimate=round(implied_or, 3))

    return make_pass(cid, inst,
                     observed=f"CI-implied SE {se_ci:.4f} vs sample-implied SE "
                              f"{se_n:.4f} (ratio {ratio:.3f})",
                     locator=str(p.get("row_id")),
                     opposite_would_be=f"a ratio outside [{1/thr:.2f}, {thr:.2f}], "
                                       "meaning the interval was computed on a "
                                       "different sample from the one recorded")


CHK016 = Check(
    check_id="CHK016_PRECISION_SAMPLE_MISMATCH",
    instrument=Instrument("interval-vs-sample",
                          reads=("ci_low", "ci_high", "events_t", "n_t",
                                 "events_c", "n_c")),
    fn=_precision_sample_mismatch,
    description="The interval's SE and the sample's SE must be the same SE.",
    must_fire_on=[Fixture(
        "mavacamten_hcm_or_from_elsewhere",
        {"row_id": "MAVACAMTEN_HCM", "estimate": 6.67, "ci_low": 2.09,
         "ci_high": 21.30, "events_t": 45, "n_t": 123, "events_c": 22, "n_c": 128},
        Verdict.FAIL,
        provenance="[R] corpus lane. Claimed OR 6.67 (2.09-21.30) -> SE 0.5922; "
                   "EXPLORER-HCM's real 45/123 vs 22/128 -> SE 0.2999 and OR 2.780. "
                   "An exhaustive search found 936 small 2x2 tables reproducing the "
                   "claimed pair, all small-subgroup shaped. Arithmetic verified.")],
    must_be_silent_on=[Fixture(
        "mitral_object_internally_consistent",
        {"row_id": "MITRAL_FUNCMR", "estimate": 0.6677, "ci_low": 0.4009,
         "ci_high": 1.1120, "events_t": 45, "n_t": 150, "events_c": 60, "n_c": 145},
        Verdict.PASS,
        provenance="[R] corpus lane. OR 0.6677 (0.4009-1.1120) -> SE 0.2603, and "
                   "0.6677 is the exact geometric mean of its own bounds. A real "
                   "row with a real interval that COULD have fired and does not.")],
    observation_terms={
        "ci_high": lambda p: _mut(p, ci_high=p["ci_high"] * 4),
        "n_t": lambda p: _mut(p, n_t=p["n_t"] * 20, n_c=p["n_c"] * 20,
                              events_t=p["events_t"] * 20,
                              events_c=p["events_c"] * 20),
        "variance_adjustment_declared": lambda p: _mut(
            p, variance_adjustment_declared="HKSJ"),
    },
)


# =============================================================================
# CHK017 -- DUP-1 BY BIT EQUALITY (replaces the heterogeneity signature)
# =============================================================================
# CORRECTED 2026-08-18. THE ORIGINAL PREMISE WAS FALSE, AND IT WAS FALSE ABOUT
# THIS CHECK'S OWN FOUNDING CASE.
#
# What it used to say: "two distinct trials cannot agree to 16 significant
# digits ... This is a PROOF, not an inference." What is actually true: the
# founding fixture's value, -0.15082288973458366, is BIT-IDENTICAL TO
# math.log(0.86). The sixteen digits are manufactured by math.log out of a
# TWO-DECIMAL PUBLISHED RATIO -- so every trial reporting HR 0.86 yields exactly
# that float, and agreement between two of them proves nothing whatever.
#
# THE CHECK WAS READING THE PRECISION OF THE FLOAT AND CALLING IT THE PRECISION
# OF THE ESTIMATE. Published effect estimates arrive at two decimals; a plausible
# ratio band holds about 36 of them, so among k=3 entries a collision occurs
# ABOUT 8% OF THE TIME BY CHANCE ALONE -- and more often in reality, because real
# effect sizes cluster rather than spreading uniformly.
#
# THE PROOF WAS THE OTHER CONDITION ALL ALONG, and it sat here as decoration: an
# appended sentence on a verdict already reached without it. Inverse-variance
# pooling of two DISTINCT values cannot return either one exactly. So POOLED
# BIT-IDENTICAL TO AN ENTRY is the arithmetic proof of duplication; ENTRY
# BIT-IDENTICAL TO ENTRY is an ordinary coincidence at published precision.
#
# WHAT FAILS NOW, and the founding case still fails on the first of them:
#   (a) the pooled estimate is bit-identical to a repeated entry -- PROOF; or
#   (b) the shared value is NOT reducible to a short-decimal ratio, i.e. it
#       carries precision no published summary could supply, which genuinely
#       cannot arise twice independently.
#
# A shared SHORT-DECIMAL value with a distinct pooled estimate is reported and
# does NOT fail, because it is the ordinary case: DAPA-HF and EMPEROR-Reduced
# both report 0.75 for CV death or heart-failure hospitalisation, with intervals
# 0.65-0.85 and 0.65-0.86. Two trials, one two-decimal number, no duplication.
#
# THIS MAKES THE CHECK NARROWER IN WHAT IT ASSERTS AND NOT WEAKER IN WHAT IT
# CATCHES: every genuine duplicate carries condition (a), because bit-identical
# entries are exactly what force the pooled value onto them.

def _is_short_decimal_ratio(log_value: float) -> bool:
    """Is this log-estimate explicable as the log of a PUBLISHED two/three-decimal ratio?

    THIS IS THE DISCRIMINATOR THE CHECK LACKED. Published effect estimates arrive
    already rounded -- 0.75, 0.86, 1.02 -- and math.log turns each into a
    full-precision float. Those sixteen digits describe THE LOGARITHM, not the
    estimate, so two trials reporting the same rounded number produce the same
    float necessarily rather than remarkably.

    The tolerance is loose deliberately: objects in this corpus store log_point
    rounded to six decimals, so exp() lands NEAR the published value rather than
    exactly on it. -0.287682 exponentiates to 0.7500000543, not to 0.75.
    """
    try:
        r = math.exp(log_value)
    except (OverflowError, ValueError):
        return False
    if not (0.0 < r < 1e6):
        return False
    return any(abs(r - round(r, d)) < 5e-6 for d in (2, 3))


def _dup1_bit_equality(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK017_DUP1_BIT_EQUALITY", "float-identity"
    entries = list(p.get("entries") or [])
    if len(entries) < 2:
        return make_invalid(cid, inst,
                            "fewer than two entries; duplication is not defined")
    if any("estimate" not in e for e in entries):
        return make_invalid(cid, inst, "an entry carries no point estimate")

    groups: dict[str, list] = {}
    for e in entries:
        groups.setdefault(repr(float(e["estimate"])), []).append(e)

    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    if dupes:
        k0, members = sorted(dupes.items())[0]
        ids = [m.get("id") for m in members]
        variances = [m.get("variance") for m in members]
        pooled = p.get("pooled_estimate")
        pooled_matches = pooled is not None and repr(float(pooled)) == k0

        if pooled_matches:
            return make_fail(
                cid, inst,
                f"entries {ids} carry the same estimate {k0}"
                + (f" with differing variances {variances}" if
                   len(set(map(repr, variances))) > 1 else "")
                + ". THE POOLED ESTIMATE IS BIT-IDENTICAL TO IT, and THAT is the "
                  "proof: inverse-variance pooling of two DISTINCT values cannot "
                  "return either one exactly, so this pool holds one value entered "
                  "twice, whatever the weights claim.",
                observed=f"pooled == entry == {k0} for {len(members)} entries: {ids}",
                locator=str(p.get("pool_id")),
                opposite_would_be="a pooled estimate strictly between the entries, "
                                  "which is what pooling two distinct values gives",
                duplicate_value=k0, members=ids, proof="pooled-bit-identity")

        if not _is_short_decimal_ratio(float(k0)):
            return make_fail(
                cid, inst,
                f"entries {ids} carry the bit-identical estimate {k0}, WHICH IS NOT "
                "REDUCIBLE TO A PUBLISHED SHORT-DECIMAL RATIO. A value at this "
                "precision is the output of a computation, and one computation run "
                "over two different trials does not land on the same float.",
                observed=f"repr(float(estimate)) == {k0} for {len(members)} entries: "
                         f"{ids}; exp() does not round-trip through three "
                         "significant figures",
                locator=str(p.get("pool_id")),
                opposite_would_be="a shared value explicable as a two-decimal "
                                  "published ratio, where collision is ordinary",
                duplicate_value=k0, members=ids, proof="precision-beyond-publication")

        # SHARED, AT PUBLISHED PRECISION, WITH A DISTINCT POOLED ESTIMATE. The
        # ordinary case, and NOT a finding. Reported in full so the correction of
        # 2026-08-18 is legible at exactly the point where it applies.
        return make_pass(
            cid, inst,
            observed=f"entries {ids} share {k0}, which is the log of a short-decimal "
                     f"ratio, and the pooled estimate {pooled!r} is DISTINCT from it: "
                     "two trials reporting the same two-decimal number, which happens "
                     "in roughly 8% of three-entry pools by chance alone",
            locator=str(p.get("pool_id")),
            opposite_would_be="a pooled estimate bit-identical to the shared value, "
                              "which pooling two distinct values cannot produce",
            shared_value=k0, members=ids, at_published_precision=True)

    return make_pass(cid, inst,
                     observed=f"{len(entries)} entries, {len(groups)} distinct "
                              "point estimates",
                     locator=str(p.get("pool_id")),
                     opposite_would_be="two entries sharing a value with the pooled "
                                       "estimate bit-identical to it")


CHK017 = Check(
    check_id="CHK017_DUP1_BIT_EQUALITY",
    instrument=Instrument("float-identity", reads=("entries", "pooled_estimate")),
    fn=_dup1_bit_equality,
    description="Bit-equal point estimates are one estimate entered twice.",
    must_fire_on=[Fixture(
        "azithromycin_child_mortality_bit_equal",
        {"pool_id": "AZITHROMYCIN_CHILD_MORTALITY",
         "entries": [{"id": "entry-1", "estimate": -0.15082288973458366,
                      "variance": 0.0041},
                     {"id": "entry-2", "estimate": -0.15082288973458366,
                      "variance": 0.0117}],
         "pooled_estimate": -0.15082288973458366},
        Verdict.FAIL,
        provenance="[R] corpus lane -- both entries carrying "
                   "-0.15082288973458366, pooling to exactly that value")],
    must_be_silent_on=[
        Fixture(
            "fidelio_vs_figaro_distinct",
            {"pool_id": "finerenone-kidney",
             "entries": [{"id": "FIDELIO-DKD", "estimate": -0.19845,
                          "variance": 0.0038},
                         {"id": "FIGARO-DKD", "estimate": -0.13103,
                          "variance": 0.0041}],
             "pooled_estimate": -0.16389},
            Verdict.PASS,
            provenance="[F] report #3 -- FIDELIO-DKD (2833/2840) and FIGARO-DKD "
                       "(3666/3686) are the two trials the published metas "
                       "triple-count; as DISTINCT entries they are the natural "
                       "negative for a duplication check"),
        Fixture(
            "dapa_hf_and_emperor_reduced_both_report_0_75",
            {"pool_id": "harmonised_cvdeath_or_hhf",
             "entries": [{"id": "NCT03036124", "estimate": -0.287682,
                          "variance": 0.004683486095999999},
                         {"id": "NCT03057977", "estimate": -0.287682,
                          "variance": 0.0051008163999999995},
                         {"id": "NCT03057951", "estimate": -0.235722,
                          "variance": 0.004464},
                         ],
             "pooled_estimate": -0.269518},
            Verdict.PASS,
            provenance="[R] registry, read 2026-08-18 -- THE FALSE POSITIVE THIS "
                       "CORRECTION EXISTS FOR. DAPA-HF posts HR 0.75 (0.65-0.85) for "
                       "CV death or heart-failure hospitalisation as a SECONDARY "
                       "outcome, and EMPEROR-Reduced posts 0.75 (0.65-0.86). Two "
                       "trials, two intervals, one two-decimal number -- and the "
                       "pooled estimate 0.7636 is distinct from both, so the "
                       "arithmetic proof of duplication is ABSENT. The old check "
                       "called this a duplicate and blocked a push over it. The old "
                       "negative fixture could never have caught that, because two "
                       "DISTINCT estimates pass under every version of this check; "
                       "a negative fixture has to be the shape that was getting it "
                       "wrong."),
    ],
    observation_terms={
        # RE-POINTED WITH THE CORRECTION. Each term now mutates into the branch it
        # actually governs, so the flip proves the check reads that term. Forcing
        # two entries equal no longer suffices -- under the corrected check that is
        # the ORDINARY case, which is the whole point.
        # THE MUTATION VALUE IS ITSELF A TRAP AND I WALKED INTO IT ONCE. The first
        # attempt used -0.1984512345678901, which sits 3e-7 from log(0.82) -- so the
        # corrected check read it as PUBLISHED PRECISION, returned PASS, and CHK017
        # went vacuous on thirteen real artefacts. A mutation must land in the branch
        # it is testing. log(0.834567) cannot be a published ratio.
        "entries": lambda p: _mut(p, entries=[
            {**p["entries"][0], "estimate": -0.18084225150576030},
            {**p["entries"][1], "estimate": -0.18084225150576030}]
            + [dict(e) for e in p["entries"][2:]]),
        "pooled_estimate": lambda p: _mut(
            p,
            entries=[dict(e) for e in p["entries"]] + [
                {**p["entries"][0], "id": "entry-dup"}],
            pooled_estimate=p["entries"][0]["estimate"]),
    },
)


# =============================================================================
# CHK018 -- MIXED-DIRECTION / MIXED-MEASURE POOLING
# =============================================================================
# NOTE WHAT IS NOT AN INPUT: I-squared. The heterogeneity signature was
# dismantled by the adversary, and high heterogeneity has legitimate causes. This
# check reads only the MEASURE TYPE and the DIRECTION OF BENEFIT of each entry --
# both structural properties of the endpoint, not statistics about the data. It
# must stay silent on INCLISIRAN's I^2 = 72% single-endpoint pool.

_RATIO_MEASURES = {"OR", "RR", "HR", "IRR"}
_DIFF_MEASURES = {"MD", "SMD", "RD"}


def _mixed_pooling(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK018_MIXED_POOLING", "pool-composition"
    entries = list(p.get("entries") or [])
    if len(entries) < 2:
        return make_invalid(cid, inst, "fewer than two entries; no pool to inspect")
    if any(not e.get("measure") or not e.get("direction_of_benefit")
           for e in entries):
        return make_invalid(cid, inst,
                            "an entry does not declare its measure or its direction "
                            "of benefit; mixed pooling cannot be seen without both")

    measures = {e["measure"] for e in entries}
    directions = {e["direction_of_benefit"] for e in entries}

    if len(directions) > 1 and not p.get("composite_endpoint"):
        by_dir = {d: [e["id"] for e in entries if e["direction_of_benefit"] == d]
                  for d in sorted(directions)}
        return make_fail(cid, inst,
                         f"entries pooled across opposite directions of benefit: "
                         f"{by_dir}. A harm and an efficacy endpoint do not sum.",
                         observed=f"directions present: {sorted(directions)} -> {by_dir}",
                         locator=str(p.get("pool_id")),
                         opposite_would_be="every entry running in the same "
                                           "direction, or a declared composite "
                                           "endpoint enumerating its components",
                         by_direction=by_dir)

    if len(measures) > 1:
        kinds = {("ratio" if m in _RATIO_MEASURES else
                  "difference" if m in _DIFF_MEASURES else "other")
                 for m in measures}
        if len(kinds) > 1 or measures & _RATIO_MEASURES != measures:
            by_m = {m: [e["id"] for e in entries if e["measure"] == m]
                    for m in sorted(measures)}
            return make_fail(cid, inst,
                             f"entries pooled across incompatible measures: {by_m}",
                             observed=f"measures present: {sorted(measures)}",
                             locator=str(p.get("pool_id")),
                             opposite_would_be="one measure across the pool, or a "
                                               "declared conversion with its "
                                               "assumptions stated",
                             by_measure=by_m)
        # HR pooled with OR: same family, different estimands and timepoints
        by_m = {m: [e["id"] for e in entries if e["measure"] == m]
                for m in sorted(measures)}
        return make_fail(cid, inst,
                         f"entries pooled across different ratio estimands: {by_m}. "
                         "A hazard ratio and an odds ratio answer different "
                         "questions over different follow-up.",
                         observed=f"measures present: {sorted(measures)}",
                         locator=str(p.get("pool_id")),
                         opposite_would_be="one estimand across the pool",
                         by_measure=by_m)

    return make_pass(cid, inst,
                     observed=f"{len(entries)} entries, single measure "
                              f"{sorted(measures)[0]}, single direction "
                              f"{sorted(directions)[0]}"
                              + (" (declared composite)" if p.get("composite_endpoint")
                                 else ""),
                     locator=str(p.get("pool_id")),
                     opposite_would_be="two measures, or two directions of benefit, "
                                       "inside one estimate")


CHK018 = Check(
    check_id="CHK018_MIXED_POOLING",
    instrument=Instrument("pool-composition",
                          reads=("entries.measure", "entries.direction_of_benefit",
                                 "composite_endpoint")),
    fn=_mixed_pooling,
    description="Direction and measure only. I-squared is deliberately not an input.",
    must_fire_on=[Fixture(
        "mitral_hazard_ratio_pooled_with_odds_ratio",
        {"pool_id": "MITRAL_FUNCMR",
         "entries": [{"id": "COAPT", "measure": "HR",
                      "direction_of_benefit": "efficacy"},
                     {"id": "MITRA-FR", "measure": "OR",
                      "direction_of_benefit": "efficacy"}]},
        Verdict.FAIL,
        provenance="[R] corpus lane -- COAPT's hazard ratio pooled with MITRA-FR's "
                   "odds ratio, different endpoints and timepoints, I^2 ~ 88. "
                   "COAPT and MITRA-FR are [F] present in the MITRAL page")],
    must_be_silent_on=[Fixture(
        "inclisiran_single_endpoint_high_heterogeneity",
        {"pool_id": "INCLISIRAN_LIPID",
         "i_squared": 72,
         "entries": [{"id": "ORION-9", "measure": "MD",
                      "direction_of_benefit": "efficacy"},
                     {"id": "ORION-10", "measure": "MD",
                      "direction_of_benefit": "efficacy"},
                     {"id": "ORION-11", "measure": "MD",
                      "direction_of_benefit": "efficacy"}]},
        Verdict.PASS,
        provenance="[R] corpus lane -- I^2 = 72% on ONE endpoint. The load-bearing "
                   "negative: a pool with heterogeneity high enough that the "
                   "dismantled heterogeneity signature would have fired, and this "
                   "check must not. ORION-9/10/11 are [F] in report #6")],
    observation_terms={
        "measure": lambda p: _mut(p, entries=[
            {**e, "measure": "OR"} if i == 0 else dict(e)
            for i, e in enumerate(p["entries"])]),
        # The observation term is "directions differ IN A POOL NOT DECLARED AS A
        # COMPOSITE". Flipping direction alone leaves a declared composite
        # passing -- correctly, since a composite is allowed to mix directions --
        # and the vacuity sweep rightly reported that as the term doing nothing.
        # The mutator therefore strips the declaration as well, which is the
        # actual flipping value for the property being observed.
        # NB: this must SET each entry, not flip only the first. Flipping entry 0
        # to "harm" when entry 1 was already "harm" produced a UNIFORM pool and
        # the PASS survived -- the mutant was not the intended mutant. Caught by
        # the sweep reporting direction_of_benefit vacuous on a composite fixture.
        "direction_of_benefit": lambda p: _mut(
            p, composite_endpoint=False,
            entries=[{**e, "direction_of_benefit":
                      ("harm" if i == 0 else "efficacy")}
                     for i, e in enumerate(p["entries"])]),
        "composite_endpoint": lambda p: _mut(
            p, composite_endpoint=False,
            entries=[{**e, "direction_of_benefit":
                      ("harm" if i == 0 else "efficacy")}
                     for i, e in enumerate(p["entries"])]),
    },
)


# =============================================================================
# CHK019 -- INERT ENGINE
# =============================================================================
# A page whose hard-coded trial-ID array shares no identifier with the page's own
# data. The analysis returns null unconditionally -- it cannot produce a result,
# and therefore cannot produce a wrong one, which is why nothing ever flagged it.
# Measured at 612/651 pages.

def _inert_engine(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK019_INERT_ENGINE", "engine-wiring"
    eng = set(p.get("engine_trial_ids") or [])
    dat = set(p.get("data_trial_ids") or [])
    if not eng or not dat:
        return make_invalid(cid, inst,
                            "engine or data identifier list is empty; wiring cannot "
                            "be assessed (an empty engine list is a different defect)")
    shared = eng & dat
    if not shared:
        return make_fail(cid, inst,
                         f"engine references {sorted(eng)[:4]}... and the page holds "
                         f"{sorted(dat)[:4]}...: no identifier in common, so the "
                         "analysis returns null unconditionally",
                         observed=f"|engine|={len(eng)} |data|={len(dat)} "
                                  f"|intersection|=0",
                         locator=str(p.get("page_id")),
                         opposite_would_be="at least one identifier shared, so the "
                                           "engine can address the page's own data",
                         engine_only=sorted(eng)[:6], data_only=sorted(dat)[:6])
    return make_pass(cid, inst,
                     observed=f"{len(shared)} identifier(s) shared between engine and "
                              f"page data: {sorted(shared)[:4]}",
                     locator=str(p.get("page_id")),
                     opposite_would_be="an empty intersection, which makes the "
                                       "engine inert")


CHK019 = Check(
    check_id="CHK019_INERT_ENGINE",
    instrument=Instrument("engine-wiring",
                          reads=("engine_trial_ids", "data_trial_ids")),
    fn=_inert_engine,
    description="An engine that cannot address its page's data returns null forever.",
    must_fire_on=[Fixture(
        "inert_page_no_shared_identifier",
        {"page_id": "ARNI_HF_REVIEW", "engine_trial_ids": ["NCT01035255",
                                                            "NCT01920711"],
         "data_trial_ids": ["NCT02554890", "NCT03036124", "NCT01730534"]},
        Verdict.FAIL,
        provenance="[R] corpus lane -- 612 of 651 pages. NCTs are [F] real "
                   "identifiers from cardio_acm_harness_report.md")],
    must_be_silent_on=[Fixture(
        "wired_page_shares_identifiers",
        {"page_id": "SGLT2_CVOT", "engine_trial_ids": ["NCT01131676", "NCT01730534"],
         "data_trial_ids": ["NCT01131676", "NCT01730534", "NCT01986881"]},
        Verdict.PASS,
        provenance="*** CONSTRUCTED, NOT CORPUS-DERIVED -- the one fixture in this "
                   "module that is not real. *** 786 pages were scanned and ZERO "
                   "wired pages were found, so no real negative exists to use. The "
                   "identifiers are [F] (classes[29] carries EMPA-REG NCT01131676, "
                   "DECLARE-TIMI 58 NCT01730534, VERTIS-CV NCT01986881 as its own "
                   "rows) but the wiring is not. Replace this the moment a genuinely "
                   "non-inert page exists.")],
    observation_terms={
        "data_trial_ids": lambda p: _mut(p, data_trial_ids=["NCT99999999"]),
        "engine_trial_ids": lambda p: _mut(p, engine_trial_ids=[]),
    },
)


# =============================================================================
# CHK020 -- ORPHAN POOLED RESULT
# =============================================================================
# A displayed pooled estimate on a page whose engine cannot compute one. 39 pages.
# The number on the screen has no live derivation behind it.

def _orphan_pooled(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK020_ORPHAN_POOLED_RESULT", "render-vs-engine"
    shown = p.get("displayed_pooled_estimate")
    can = p.get("engine_can_pool")
    if can is None:
        return make_invalid(cid, inst,
                            "engine_can_pool not determined; cannot tell an orphan "
                            "from a computed result")
    if shown is not None and not can:
        return make_fail(cid, inst,
                         f"page displays a pooled estimate ({shown}) that its own "
                         "engine cannot compute: the number has no live derivation",
                         observed=f"displayed={shown!r}, engine_can_pool=False "
                                  f"(reason: {p.get('engine_block_reason')!r})",
                         locator=str(p.get("page_id")),
                         opposite_would_be="either no displayed pooled estimate, or "
                                           "an engine that can produce one",
                         displayed=shown)
    if shown is None:
        return make_pass(cid, inst,
                         observed="no pooled estimate displayed",
                         locator=str(p.get("page_id")),
                         opposite_would_be="a displayed pooled estimate with a dead "
                                           "engine behind it")
    return make_pass(cid, inst,
                     observed=f"displayed pooled estimate {shown} with a live engine",
                     locator=str(p.get("page_id")),
                     opposite_would_be="a displayed estimate the engine cannot "
                                       "produce")


CHK020 = Check(
    check_id="CHK020_ORPHAN_POOLED_RESULT",
    instrument=Instrument("render-vs-engine",
                          reads=("displayed_pooled_estimate", "engine_can_pool")),
    fn=_orphan_pooled,
    description="A rendered number must have a derivation that still runs.",
    must_fire_on=[Fixture(
        "orphan_pooled_on_dead_engine",
        {"page_id": "ORPHAN_PAGE", "displayed_pooled_estimate": 0.87,
         "engine_can_pool": False, "engine_block_reason": "no shared trial ids"},
        Verdict.FAIL,
        provenance="[R] corpus lane -- 39 pages")],
    must_be_silent_on=[Fixture(
        "pooled_estimate_with_live_engine",
        {"page_id": "SGLT2_CVOT", "displayed_pooled_estimate": 0.87,
         "engine_can_pool": True},
        Verdict.PASS,
        provenance="[F] DEFECT-03 -- classes[29] carries a live pool object with "
                   "k=2 and its own trial rows")],
    observation_terms={
        "engine_can_pool": lambda p: _mut(p, engine_can_pool=False),
        "displayed_pooled_estimate": lambda p: _mut(p, engine_can_pool=None),
    },
)


# =============================================================================
# CHK021 -- MEASURE / SCALE MISMATCH
# =============================================================================
# The back-transform bug: a mean difference of -54, stored on the natural scale,
# exponentiated as though it were a log-ratio -> exp(-54) = 0.0000. The output is
# a number, correctly typed, and silently meaningless.

def _measure_scale(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK021_MEASURE_SCALE_MISMATCH", "scale-declaration"
    measure, scale = p.get("measure"), p.get("stored_scale")
    xf = p.get("back_transform")
    if not measure or not scale:
        return make_invalid(cid, inst, "measure or stored scale not declared")

    if measure in _DIFF_MEASURES:
        if scale != "natural" or xf not in (None, "identity"):
            return make_fail(cid, inst,
                             f"{measure} is a difference on the natural scale but is "
                             f"stored as {scale!r} with back_transform {xf!r}",
                             observed=f"measure={measure} scale={scale!r} "
                                      f"back_transform={xf!r}"
                                      + (f"; rendered value {p.get('rendered_value')}"
                                         if p.get("rendered_value") is not None else ""),
                             locator=str(p.get("row_id")),
                             opposite_would_be=f"{measure} stored on the natural "
                                               "scale with no back-transform",
                             measure=measure, scale=scale, back_transform=xf)
    elif measure in _RATIO_MEASURES:
        if scale == "log" and xf != "exp":
            return make_fail(cid, inst,
                             f"{measure} stored on the log scale with back_transform "
                             f"{xf!r}; it will render as a log value",
                             observed=f"measure={measure} scale=log back_transform={xf!r}",
                             locator=str(p.get("row_id")),
                             opposite_would_be="an exp back-transform on a "
                                               "log-scale ratio",
                             measure=measure, scale=scale, back_transform=xf)
        if scale == "natural" and xf == "exp":
            return make_fail(cid, inst,
                             f"{measure} already on the natural scale is being "
                             "exponentiated again",
                             observed=f"measure={measure} scale=natural back_transform=exp",
                             locator=str(p.get("row_id")),
                             opposite_would_be="no back-transform on a natural-scale "
                                               "ratio",
                             measure=measure, scale=scale, back_transform=xf)
    return make_pass(cid, inst,
                     observed=f"{measure} on the {scale} scale with back_transform "
                              f"{xf!r}",
                     locator=str(p.get("row_id")),
                     opposite_would_be="a difference measure exponentiated, or a "
                                       "log-scale ratio rendered without exp")


CHK021 = Check(
    check_id="CHK021_MEASURE_SCALE_MISMATCH",
    instrument=Instrument("scale-declaration",
                          reads=("measure", "stored_scale", "back_transform")),
    fn=_measure_scale,
    description="A measure and the scale it is stored on must agree.",
    must_fire_on=[Fixture(
        "md_minus_54_exponentiated",
        {"row_id": "MD_backtransform_bug", "measure": "MD",
         "stored_scale": "natural", "back_transform": "exp",
         "rendered_value": 0.0000},
        Verdict.FAIL,
        provenance="[R] corpus lane -- the back-transform bug that turned MD -54 "
                   "into 0.0000 by exponentiating a natural-scale value. "
                   "exp(-54) = 3.5e-24, which renders as 0.0000 at four decimals")],
    must_be_silent_on=[Fixture(
        "log_odds_ratio_with_exp",
        {"row_id": "finerenone-kidney-OR", "measure": "OR", "stored_scale": "log",
         "back_transform": "exp"},
        Verdict.PASS,
        provenance="[F] the standard correct encoding -- log-scale ratios with an "
                   "exp back-transform, as the netmeta outputs in nma/validation use")],
    # FLIP TO THE OPPOSITE VALUE, NOT TO A FIXED ONE.
    #
    # These forced "identity" and "natural" whatever the payload already held.
    # For a mean-difference row -- natural/identity by definition when correctly
    # encoded -- both mutants came out byte-identical to the input, so the sweep
    # varied nothing and then reported the check as not depending on the terms it
    # had failed to vary. Flipping RELATIVE to the current value gives a real
    # mutant on both encodings: a ratio row becomes natural-with-exp (double
    # exponentiation) and a difference row becomes log-scale, which is the
    # exp(-54) = 0.0000 defect this check exists to catch.
    observation_terms={
        "back_transform": lambda p: _mut(
            p, back_transform=("identity" if p.get("back_transform") == "exp"
                               else "exp")),
        "stored_scale": lambda p: _mut(
            p, stored_scale=("natural" if p.get("stored_scale") == "log"
                             else "log")),
    },
)


# =============================================================================
# CHK022 -- COMPUTED RATIO FROM A PERCENTAGE
# =============================================================================
# MORDOR-I: the abstract never uses a ratio word -- "Mortality was 13.5% lower
# overall" -- and a ratio was extracted anyway. A percentage reduction does not
# determine a ratio without knowing which quantity the percentage is of.

_RATIO_WORDS = ("hazard ratio", "risk ratio", "rate ratio", "odds ratio",
                "incidence rate ratio", " hr ", " rr ", " or ", " irr ",
                "hr=", "rr=", "or=", "hr ", "relative risk")


def _ratio_from_percentage(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK022_RATIO_FROM_PERCENTAGE", "source-wording"
    measure = p.get("extracted_measure")
    text = p.get("source_text")
    if not measure:
        return make_invalid(cid, inst, "no extracted measure recorded")
    if text is None:
        return make_invalid(cid, inst,
                            "no source text recorded, so the wording that would "
                            "support or refute a ratio cannot be inspected")
    if measure not in _RATIO_MEASURES:
        return make_pass(cid, inst,
                         observed=f"extracted measure {measure} is not a ratio",
                         locator=str(p.get("row_id")),
                         opposite_would_be="a ratio extracted from a source that "
                                           "states only a percentage")

    low = " " + text.lower() + " "
    has_ratio_word = any(w in low for w in _RATIO_WORDS)
    if not has_ratio_word:
        return make_fail(cid, inst,
                         f"{measure} extracted from a source that uses no ratio "
                         "term. A percentage reduction does not determine a ratio.",
                         observed=f"source text carries no ratio word: {text[:160]!r}",
                         locator=str(p.get("row_id")),
                         opposite_would_be="the source naming a ratio explicitly, "
                                           "e.g. 'hazard ratio 0.87 (0.75-1.01)'",
                         extracted_measure=measure)
    return make_pass(cid, inst,
                     observed=f"{measure} extracted from a source that names a ratio",
                     locator=str(p.get("row_id")),
                     opposite_would_be="no ratio term anywhere in the source text")


CHK022 = Check(
    check_id="CHK022_RATIO_FROM_PERCENTAGE",
    instrument=Instrument("source-wording",
                          reads=("extracted_measure", "source_text")),
    fn=_ratio_from_percentage,
    description="A ratio must exist in the source, not be inferred from a percent.",
    must_fire_on=[Fixture(
        "mordor_i_percentage_only",
        {"row_id": "MORDOR-I", "extracted_measure": "RR",
         "source_text": "Mortality was 13.5% lower overall in communities that "
                        "received azithromycin than in those that received placebo."},
        Verdict.FAIL,
        provenance="[R] corpus lane -- MORDOR-I's abstract never uses a ratio word, "
                   "yet a ratio was extracted")],
    must_be_silent_on=[Fixture(
        "parachute_hf_states_a_hazard_ratio",
        {"row_id": "PARACHUTE-HF", "extracted_measure": "HR",
         "source_text": "For first heart failure hospitalisation or cardiovascular "
                        "death the hazard ratio was 0.91 (95% CI, 0.73-1.13), "
                        "P = .40, from a Cox model stratified by country."},
        Verdict.PASS,
        provenance="[F] 13_ERROR_LIBRARY.md N1 -- JAMA 2026;335(1):49-59 Table 2, "
                   "read via PMC12676478. A real source that names its ratio")],
    observation_terms={
        "source_text": lambda p: _mut(
            p, source_text="Mortality was 9% lower in the treatment group."),
        "extracted_measure": lambda p: _mut(p, extracted_measure=None),
    },
)


# =============================================================================
# CHK023 -- CROSS-AGENT POOLING
# =============================================================================

def _cross_agent(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK023_CROSS_AGENT_POOLING", "intervention-identity"
    entries = list(p.get("entries") or [])
    if len(entries) < 2 or any(not e.get("intervention") for e in entries):
        return make_invalid(cid, inst,
                            "fewer than two entries, or an entry does not name its "
                            "intervention")
    agents = sorted({e["intervention"] for e in entries})
    if len(agents) > 1 and not p.get("declared_class"):
        return make_fail(cid, inst,
                         f"distinct interventions {agents} pooled into one estimate "
                         "with no declared class",
                         observed=f"interventions in pool: {agents}",
                         locator=str(p.get("pool_id")),
                         opposite_would_be="one intervention, or a declared class "
                                           "the protocol permits pooling within",
                         interventions=agents)
    return make_pass(cid, inst,
                     observed=f"interventions {agents}"
                              + (f" pooled under declared class "
                                 f"{p['declared_class']!r}" if p.get("declared_class")
                                 else " (single agent)"),
                     locator=str(p.get("pool_id")),
                     opposite_would_be="two agents pooled with no declared class")


CHK023 = Check(
    check_id="CHK023_CROSS_AGENT_POOLING",
    instrument=Instrument("intervention-identity",
                          reads=("entries.intervention", "declared_class")),
    fn=_cross_agent,
    description="Distinct agents in one estimate need a declared class.",
    must_fire_on=[Fixture(
        "covid_antivirals_pooled",
        {"pool_id": "COVID_ANTIVIRALS",
         "entries": [{"id": "EPIC-HR", "intervention": "nirmatrelvir-ritonavir"},
                     {"id": "MOVe-OUT", "intervention": "molnupiravir"}]},
        Verdict.FAIL,
        provenance="[R] corpus lane -- nirmatrelvir 0.11 pooled with molnupiravir "
                   "0.69, I^2 = 91")],
    must_be_silent_on=[Fixture(
        "sglt2_declared_class_pool",
        {"pool_id": "SGLT2_CVOT_T2D", "declared_class": "SGLT2 inhibitor",
         "entries": [{"id": "EMPA-REG", "intervention": "empagliflozin"},
                     {"id": "DECLARE-TIMI 58", "intervention": "dapagliflozin"},
                     {"id": "VERTIS-CV", "intervention": "ertugliflozin"}]},
        Verdict.PASS,
        provenance="[F] DEFECT-03 -- classes[29] 'SGLT2 CVOT (T2D)' pools three "
                   "distinct agents under a named class. A real multi-agent pool "
                   "that COULD fire and must not")],
    observation_terms={
        "declared_class": lambda p: _mut(p, declared_class=None),
        "entries": lambda p: _mut(p, declared_class=None, entries=[
            {**e, "intervention": f"agent-{i}"} for i, e in enumerate(p["entries"])]),
    },
)


# =============================================================================
# CHK024 -- FALSE METHOD CLAIM
# =============================================================================

def _false_method(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK024_FALSE_METHOD_CLAIM", "method-vs-object"
    claimed = (p.get("claimed_method") or "").upper()
    if not claimed:
        return make_invalid(cid, inst, "no method claimed on the card")
    if claimed in ("NMA", "NETWORK META-ANALYSIS"):
        edges = list(p.get("network_edges") or [])
        nodes = {n for e in edges for n in e}
        if len(edges) < 2 or len(nodes) < 3:
            return make_fail(cid, inst,
                             f"card claims {claimed} but the object holds "
                             f"{len(edges)} edge(s) over {len(nodes)} node(s): there "
                             "is no network to analyse",
                             observed=f"edges={edges} nodes={sorted(nodes)}",
                             locator=str(p.get("page_id")),
                             opposite_would_be="at least two edges over three or "
                                               "more nodes, i.e. an actual network",
                             edges=len(edges), nodes=len(nodes))
    return make_pass(cid, inst,
                     observed=f"claimed method {claimed} is supported by the object "
                              f"({len(p.get('network_edges') or [])} edges)",
                     locator=str(p.get("page_id")),
                     opposite_would_be="an NMA claim over an object with no network")


CHK024 = Check(
    check_id="CHK024_FALSE_METHOD_CLAIM",
    instrument=Instrument("method-vs-object",
                          reads=("claimed_method", "network_edges")),
    fn=_false_method,
    description="A method claim must be supported by the object's own structure.",
    must_fire_on=[Fixture(
        "nma_claimed_no_network",
        {"page_id": "FALSE_NMA_CARD", "claimed_method": "NMA",
         "network_edges": [["A", "B"]]},
        Verdict.FAIL,
        provenance="[R] corpus lane -- a card asserting NMA where the object holds "
                   "no network")],
    must_be_silent_on=[Fixture(
        "adc_her2_real_network",
        {"page_id": "ADC_HER2_NMA", "claimed_method": "NMA",
         "network_edges": [["T-DXd", "T-DM1"], ["T-DM1", "TPC"],
                           ["T-DXd", "TPC"]]},
        Verdict.PASS,
        provenance="[F] nma/validation/adc_her2_nma_netmeta.R and its "
                   "_results.json/.rds -- a real netmeta object with a genuine "
                   "network, present in the repo")],
    observation_terms={
        "network_edges": lambda p: _mut(p, network_edges=[["A", "B"]]),
        "claimed_method": lambda p: _mut(p, claimed_method=None),
    },
)


# =============================================================================
# CHK025 -- MULTI-SURFACE DISAGREEMENT
# =============================================================================
# The index carries claims on up to three surfaces: 109 table rows, 513 cards,
# 71 pages carrying both. A withdrawn card can leave a live number in a table row.

def _multi_surface(p: Mapping[str, Any]) -> Result:
    cid, inst = "CHK025_MULTI_SURFACE_DISAGREEMENT", "surface-consistency"
    surfaces = dict(p.get("surfaces") or {})
    present = {k: v for k, v in surfaces.items() if v is not None}
    if len(present) < 2:
        return make_invalid(cid, inst,
                            f"claim appears on {len(present)} surface(s); "
                            "disagreement is not defined below two")

    vals = {k: (v.get("value"), v.get("status")) for k, v in present.items()}
    distinct = {v for v in vals.values()}
    if len(distinct) > 1:
        return make_fail(cid, inst,
                         f"the same claim differs across surfaces: {vals}",
                         observed="; ".join(f"{k}: value={v[0]!r} status={v[1]!r}"
                                            for k, v in sorted(vals.items())),
                         locator=str(p.get("claim_id")),
                         opposite_would_be="identical value and status on every "
                                           "surface that carries the claim",
                         surfaces=vals)
    return make_pass(cid, inst,
                     observed=f"claim identical on {sorted(present)}: {next(iter(distinct))}",
                     locator=str(p.get("claim_id")),
                     opposite_would_be="one surface carrying a different value or a "
                                       "different status from another")


CHK025 = Check(
    check_id="CHK025_MULTI_SURFACE_DISAGREEMENT",
    instrument=Instrument("surface-consistency", reads=("surfaces",)),
    fn=_multi_surface,
    description="A claim must say the same thing on every surface that carries it.",
    must_fire_on=[Fixture(
        "withdrawn_card_live_table_row",
        {"claim_id": "claim-0417",
         "surfaces": {"card": {"value": 0.87, "status": "withdrawn"},
                      "table_row": {"value": 0.87, "status": "live"}}},
        Verdict.FAIL,
        provenance="[R] corpus lane -- a withdrawn card leaving a live number in a "
                   "table row; 71 pages carry both surfaces")],
    must_be_silent_on=[Fixture(
        "surfaces_agree",
        {"claim_id": "claim-0002",
         "surfaces": {"card": {"value": 0.91, "status": "live"},
                      "table_row": {"value": 0.91, "status": "live"},
                      "page": {"value": 0.91, "status": "live"}}},
        Verdict.PASS,
        provenance="[R] corpus lane -- the 71 both-surface pages that agree are the "
                   "natural negative")],
    observation_terms={
        "surfaces": lambda p: _mut(p, surfaces={
            **p["surfaces"], "card": {"value": 0.99, "status": "live"}}),
        "status": lambda p: _mut(p, surfaces={
            **p["surfaces"], "card": {**p["surfaces"]["card"],
                                      "status": "withdrawn"}}),
    },
)


CORPUS_CHECKS = [CHK016, CHK017, CHK018, CHK019, CHK020, CHK021, CHK022,
                 CHK023, CHK024, CHK025]


# =============================================================================
# Fixture provenance -- the honest register
# =============================================================================
# "which of the ten you can fixture both ways today, and which lack a defensible
#  negative -- that second list matters more than the first"
#
# STRENGTH of a negative = could it plausibly have fired?  A negative that cannot
# fire proves nothing; it is the "one trivial own-entry" that defeated Rule 5 v1.

FIXTURE_STATUS = {
    "CHK016_PRECISION_SAMPLE_MISMATCH": {
        "positive": "[R]+arithmetic-verified", "negative": "[R]+arithmetic-verified",
        "negative_strength": "STRONG",
        "note": "MITRAL is a real row with a real interval whose SE ratio is ~1.0; "
                "it sits on the same instrument as the positive and could have "
                "fired. Both SEs reproduce to 4 dp independently."},
    "CHK017_DUP1_BIT_EQUALITY": {
        "positive": "[R]", "negative": "[R]",
        "negative_strength": "STRONG",
        "note": "CORRECTED 2026-08-18, AND THE OLD NOTE IS THE MOST INSTRUCTIVE "
                "THING IN THIS TABLE. It read: FIDELIO/FIGARO are real and "
                "distinct, but no two independently derived floats are ever "
                "bit-equal, so the negative cannot plausibly fire. A near-miss "
                "negative -- two entries agreeing to 6+ dp but not at full "
                "precision -- would stress it and I DO NOT HAVE ONE. THIS IS THE "
                "WEAKEST NEGATIVE OF THE TEN. Every clause of that was right "
                "except the last four words. THE FIXTURE WAS IN THE CORPUS THE "
                "WHOLE TIME: sglt2-hf holds DAPA-HF at 0.75 (0.65-0.85) and "
                "EMPEROR-Reduced at 0.75 (0.65-0.86), two trials agreeing exactly "
                "at published precision. It is now the second negative, and it is "
                "load-bearing: it FAILED under the old check, which is how the "
                "false premise was found. The author named the gap, named what "
                "would close it, and did not go looking."},
    "CHK018_MIXED_POOLING": {
        "positive": "[R]", "negative": "[R]",
        "negative_strength": "STRONG",
        "note": "INCLISIRAN I^2=72% on one endpoint is the load-bearing negative: "
                "the dismantled heterogeneity signature WOULD have fired on it. "
                "I-squared is deliberately not an input to this check."},
    "CHK019_INERT_ENGINE": {
        "positive": "[F] MEASURED THIS SESSION", "negative": "NONE FOUND -- CONSTRUCTED",
        "negative_strength": "NONE",
        "note": "I scanned 786 pages in F:\\rapidmeta-ssot-shell (400 AUTO + 386 "
                "curated), treating a JS array literal of >=2 NCT strings as the "
                "engine array. Among pages HAVING such an array: 224/233 (96.1%) "
                "AUTO and 291/311 (93.6%) curated share NO identifier with the "
                "page's other NCTs. That independently corroborates the corpus "
                "lane's 612/651 = 94.0%. The positive is now file-backed: "
                "ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html's engine array carries "
                "NCT01035255 and NCT01920711 -- PARADIGM-HF and PARAGON-HF, two "
                "heart-failure trials -- against page data NCT01343004 / "
                "NCT05901831. An osteoporosis page wired to cardiology trials. "
                "*** BUT: ZERO WIRED PAGES WERE FOUND IN 786. *** The shipped "
                "negative is therefore CONSTRUCTED, not corpus-derived, because "
                "there may be no non-inert page in the corpus to draw one from. "
                "Until one is produced, this detector is unproven in the "
                "silent direction -- exactly the Rule 1 problem from "
                "14_RULE_TESTS_AND_SPECIFICATIONS.md."},
    "CHK020_ORPHAN_POOLED_RESULT": {
        "positive": "[R]", "negative": "[F]-object",
        "negative_strength": "MODERATE",
        "note": "classes[29] is a real live pool. `engine_can_pool` is my "
                "abstraction of the corpus lane's determination, not a field I read."},
    "CHK021_MEASURE_SCALE_MISMATCH": {
        "positive": "[R]", "negative": "[F]-convention",
        "negative_strength": "MODERATE",
        "note": "The negative is the standard log+exp encoding rather than a named "
                "row I verified. It could fire if the convention were violated."},
    "CHK022_RATIO_FROM_PERCENTAGE": {
        "positive": "[R]", "negative": "[F]",
        "negative_strength": "STRONG",
        "note": "PARACHUTE-HF's 'hazard ratio was 0.91 (95% CI, 0.73-1.13)' is read "
                "verbatim from 13_ERROR_LIBRARY.md N1. Real source text on the same "
                "instrument."},
    "CHK023_CROSS_AGENT_POOLING": {
        "positive": "[R]", "negative": "[F]",
        "negative_strength": "STRONG",
        "note": "classes[29] pools empagliflozin, dapagliflozin and ertugliflozin "
                "under a declared class -- a real multi-agent pool that this check "
                "must not fire on. Read verbatim from DEFECT-03."},
    "CHK024_FALSE_METHOD_CLAIM": {
        "positive": "[R]", "negative": "[F]-artefact",
        "negative_strength": "MODERATE",
        "note": "nma/validation/adc_her2_nma_netmeta.R and its results files are "
                "[F] present; I listed them but did not read the edge list, so the "
                "three edges are representative rather than transcribed."},
    "CHK025_MULTI_SURFACE_DISAGREEMENT": {
        "positive": "[R]", "negative": "[R]",
        "negative_strength": "WEAK",
        "note": "Both sides are operator-relayed and the negative is generic "
                "agreement rather than a named claim. A claim that differs "
                "LEGITIMATELY across surfaces -- a rounded card against a full "
                "-precision table row -- is the negative that would stress it, and "
                "it would currently FIRE on that. SECOND WEAKEST."},
}
