"""
mg_detectors.py -- D-01 .. D-31.

Every detector obeys the design rules in mg_core:
  * collect into `out`, return once at the end (R4)
  * ctx.touch() on every row actually inspected (R5)
  * missing inputs -> UNVERIFIABLE, never silent pass (R1)

Network detectors (D-27..D-31) take their external data from `pool["external"]`.
They perform no I/O themselves, so they are testable offline and so that the
retraction lane -- which a sibling process owns -- is consumed, not duplicated.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from mg_core import (
    CHOICE, INCONSISTENT, SEV_HIGH, SEV_INFO, SEV_LOW, SEV_MED, SUSPECT,
    UNVERIFIABLE, Ctx, Finding, MISSING, betainc, bowley_skew, chi2_cdf,
    dersimonian_laird, design_effect, g, grim_inconsistent,
    implied_events_from_hr_ci, inv_var_pool, jaccard, log_or, log_rr,
    missing_of, monte_carlo_q_lower, norm_ppf, q_lower_tail_p, register,
    se_from_ci, smd_hedges_g, t_ppf, unverifiable,
)

RATIO_MEASURES = {"RR", "OR", "HR", "RATE_RATIO", "IRR"}
NCT_RE = re.compile(r"\bNCT\d{8}\b")
OTHER_REGISTRY_RE = {
    "ISRCTN": re.compile(r"\bISRCTN\d{8}\b"),
    "EudraCT": re.compile(r"\b\d{4}-\d{6}-\d{2}\b"),
    "UMIN": re.compile(r"\bUMIN\d{9}\b"),
    "ChiCTR": re.compile(r"\bChiCTR[-A-Za-z]*\d{6,10}\b"),
    "CTRI": re.compile(r"\bCTRI/\d{4}/\d{2,3}/\d{6}\b"),
}
TTE_TERMS = ("cox", "proportional hazards", "kaplan-meier", "kaplan meier",
             "log-rank", "logrank", "person-year", "person-time", "censor",
             "time-to-event", "time to event", "survival analysis")
CORRECTION_TERMS = ("bonferroni", "holm", "sidak", "greenhouse-geisser",
                    "huynh-feldt", "false discovery", "fdr", "tukey",
                    "benjamini")


# ==========================================================================
# TIER 0 -- identity and duplication
# ==========================================================================

@register(
    id="D-01", name="Trial-identity coverage and collision audit", tier=0,
    network=False, requires=("rows",),
    catches="rows with no trial identity key; one trial under several citations; "
            "two identity keys pointing at one trial",
    misses="a trial whose every report shares an identical wrong key; "
           "collisions where no fingerprint field is populated",
    fp_behaviour="CANDIDATE_MULTI_REPORT fires legitimately whenever a trial has a "
                 "primary report plus a follow-up. Expected to be the modal outcome "
                 "on older corpora: Bashir 2017 found a median 49% of articles carry "
                 "a machine-resolvable link (range 8-97%).",
    fn_behaviour="Cannot see a duplicate whose reports carry no shared author, "
                 "institution, N or period, i.e. von Elm pattern 4.",
)
def d01(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    rows = g(pool, "rows", [])
    by_key: dict[str, set] = defaultdict(set)
    by_fp: dict[tuple, set] = defaultdict(set)
    n_missing = 0
    for r in rows:
        ctx.touch()
        rid = g(r, "row_id", "?")
        key = g(r, "trial_key")
        cit = g(r, "citation_id", rid)
        if key is MISSING:
            n_missing += 1
            out.append(Finding(
                detector="D-01", code="UNVERIFIABLE_IDENTITY", verdict=UNVERIFIABLE,
                severity=SEV_INFO, row_id=rid, pool_id=g(pool, "pool_id"),
                message="row has no trial_key; identity cannot be resolved",
                evidence={"missing_fields": ["trial_key"]},
            ))
        else:
            by_key[key].add(cit)
        fp = (str(g(r, "first_author", "")).lower(),
              g(r, "n_t", 0) + g(r, "n_c", 0),
              g(r, "recruit_year", ""),
              str(g(r, "country", "")).lower())
        if any(x not in ("", 0) for x in fp):
            by_fp[fp].add(key if key is not MISSING else f"__none__{rid}")

    for key, cits in sorted(by_key.items()):
        if len(cits) > 1:
            out.append(Finding(
                detector="D-01", code="CANDIDATE_MULTI_REPORT", verdict=CHOICE,
                severity=SEV_LOW, pool_id=g(pool, "pool_id"),
                message=f"trial {key} appears under {len(cits)} distinct citations",
                evidence={"trial_key": key, "citations": sorted(cits)},
            ))
    for fp, keys in sorted(by_fp.items(), key=lambda kv: str(kv[0])):
        real = {k for k in keys if not k.startswith("__none__")}
        if len(real) > 1:
            out.append(Finding(
                detector="D-01", code="CANDIDATE_KEY_COLLISION", verdict=SUSPECT,
                severity=SEV_MED, pool_id=g(pool, "pool_id"),
                message=f"one trial fingerprint maps to {len(real)} identity keys",
                evidence={"fingerprint": list(fp), "keys": sorted(real)},
            ))
    if rows:
        out.append(Finding(
            detector="D-01", code="IDENTITY_COVERAGE", verdict=UNVERIFIABLE
            if n_missing else CHOICE,
            severity=SEV_INFO, pool_id=g(pool, "pool_id"),
            message=f"identity coverage {len(rows)-n_missing}/{len(rows)}",
            evidence={"rows": len(rows), "with_key": len(rows) - n_missing},
        ))
    return out


@register(
    id="D-02", name="Enrolment-magnitude concordance [NOVEL]", tier=0,
    network=False, requires=("rows",),
    catches="an identifier that resolves but points at a different trial; any two "
            "records claiming one trial whose enrolments differ by >=1.5x (soft) "
            "or >=3x (hard)",
    misses="identity swaps between trials of similar size; a wrong identifier where "
           "only one enrolment figure is available",
    fp_behaviour="ITT vs per-protocol denominators (suppressed below 1.5x); declared "
                 "substudies (suppressed by outcome-scope check); cluster trials "
                 "reporting clusters vs participants (suppressed by design check). "
                 "Registry ANTICIPATED enrolment is excluded from the comparison set "
                 "by construction and reported separately.",
    fn_behaviour="Blind when only one N exists. Carlisle 2020's existence screen "
                 "(215/38,001 = 0.6% non-resolving) cannot fire here and vice versa; "
                 "the two are complementary, not redundant.",
)
def d02(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        ns: dict[str, float] = {}
        for label, key in (("review_table", "reported_n"),
                           ("forest_row", "forest_n"),
                           ("publication", "pub_reported_n"),
                           ("registry_actual", "registry_enrolment")):
            v = g(r, key)
            if v is not MISSING and v:
                ns[label] = float(v)
        antic = g(r, "registry_anticipated")
        if not ns or len(ns) < 2:
            out.append(unverifiable(
                "D-02", "SINGLE_ENROLMENT_SOURCE",
                "fewer than two independent enrolment figures; cannot cross-check",
                missing=[k for k in ("reported_n", "pub_reported_n",
                                     "registry_enrolment") if g(r, k) is MISSING],
                row_id=rid, pool_id=g(pool, "pool_id")))
        else:
            lo, hi = min(ns.values()), max(ns.values())
            ratio = hi / lo if lo > 0 else float("inf")
            design = str(g(r, "design", "parallel")).lower()
            m = g(r, "cluster_m")
            suppressed = None
            if design == "cluster" and m not in (MISSING, None) and m:
                if abs(ratio - float(m)) / float(m) < 0.25:
                    suppressed = "cluster_size_ratio"
            if g(r, "is_declared_substudy", False):
                suppressed = "declared_substudy"
            if suppressed:
                out.append(Finding(
                    detector="D-02", code="ENROLMENT_RATIO_SUPPRESSED", verdict=CHOICE,
                    severity=SEV_INFO, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=f"ratio {ratio:.2f} explained by {suppressed}",
                    evidence={"ratio": round(ratio, 3), "reason": suppressed,
                              "enrolments": ns}))
            elif ratio >= 3.0:
                out.append(Finding(
                    detector="D-02", code="IDENTITY_MISMATCH_SUSPECTED",
                    verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                    pool_id=g(pool, "pool_id"),
                    message=(f"enrolment ratio {ratio:.2f} between records claiming "
                             "the same trial; no analysis-population difference "
                             "produces a threefold gap"),
                    evidence={"ratio": round(ratio, 3), "enrolments": ns,
                              "threshold": 3.0}))
            elif ratio >= 1.5:
                out.append(Finding(
                    detector="D-02", code="ENROLMENT_DISCORDANCE", verdict=SUSPECT,
                    severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=f"enrolment ratio {ratio:.2f} across sources",
                    evidence={"ratio": round(ratio, 3), "enrolments": ns,
                              "threshold": 1.5}))
        if antic not in (MISSING, None) and antic:
            act = ns.get("registry_actual")
            if act and float(antic) / act >= 3.0:
                out.append(Finding(
                    detector="D-02", code="REGISTRY_PLANNING_GAP", verdict=CHOICE,
                    severity=SEV_LOW, row_id=rid, pool_id=g(pool, "pool_id"),
                    message="registry anticipated enrolment >=3x actual",
                    evidence={"anticipated": float(antic), "actual": act}))
    return out


@register(
    id="D-03", name="Cross-row numeric fingerprint (duplicate data)", tier=0,
    network=False, requires=("rows",),
    catches="the same outcome tuple entered under two different citations; nested or "
            "growing cohorts from one author-institution cluster (von Elm 3A/3B)",
    misses="duplicated data that was re-rounded or partially re-reported; duplicates "
           "with only one numeric cell in common",
    fp_behaviour="High on small counts -- two independent trials reporting 2/30 vs "
                 "5/30 are unremarkable. Precision is bought by requiring BOTH arm Ns "
                 "to be identical, which chance collisions rarely satisfy. Kwon 2015 "
                 "established false-positive merging is a real cost.",
    fn_behaviour="Cannot see duplication where the duplicate report changed the "
                 "denominators, which Bhandari 2005 measured at 31% of duplicates.",
)
def d03(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    rows = g(pool, "rows", [])
    for r in rows:
        ctx.touch()
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if g(a, "citation_id") == g(b, "citation_id"):
                continue
            bin_a = [g(a, k) for k in ("e_t", "n_t", "e_c", "n_c")]
            bin_b = [g(b, k) for k in ("e_t", "n_t", "e_c", "n_c")]
            if MISSING not in bin_a and MISSING not in bin_b:
                m = sum(1 for x, y in zip(bin_a, bin_b) if x == y)
                same_n = (bin_a[1] == bin_b[1]) and (bin_a[3] == bin_b[3])
                if same_n and m >= 2:
                    out.append(Finding(
                        detector="D-03",
                        code="DUPLICATE_DATA_CANDIDATE", verdict=INCONSISTENT
                        if m == 4 else SUSPECT,
                        severity=SEV_HIGH if m == 4 else SEV_MED,
                        pool_id=g(pool, "pool_id"),
                        message=(f"rows {g(a,'row_id')} and {g(b,'row_id')} share "
                                 f"{m}/4 outcome cells with identical arm Ns"),
                        evidence={"rows": [g(a, "row_id"), g(b, "row_id")],
                                  "cells_matched": m, "tuple_a": bin_a,
                                  "tuple_b": bin_b,
                                  "citations": [g(a, "citation_id"),
                                                g(b, "citation_id")]}))
            con_a = [g(a, k) for k in ("mean_t", "sd_t", "n_t", "mean_c", "sd_c", "n_c")]
            con_b = [g(b, k) for k in ("mean_t", "sd_t", "n_t", "mean_c", "sd_c", "n_c")]
            if MISSING not in con_a and MISSING not in con_b:
                m = sum(1 for x, y in zip(con_a, con_b) if x == y)
                same_n = (con_a[2] == con_b[2]) and (con_a[5] == con_b[5])
                if same_n and m >= 3:
                    out.append(Finding(
                        detector="D-03", code="DUPLICATE_DATA_CANDIDATE",
                        verdict=INCONSISTENT if m == 6 else SUSPECT,
                        severity=SEV_HIGH if m == 6 else SEV_MED,
                        pool_id=g(pool, "pool_id"),
                        message=(f"rows {g(a,'row_id')} and {g(b,'row_id')} share "
                                 f"{m}/6 continuous cells with identical arm Ns"),
                        evidence={"rows": [g(a, "row_id"), g(b, "row_id")],
                                  "cells_matched": m}))
            au_a, au_b = g(a, "first_author"), g(b, "first_author")
            in_a, in_b = g(a, "institution"), g(b, "institution")
            yr_a, yr_b = g(a, "year"), g(b, "year")
            if (au_a is not MISSING and au_a == au_b and in_a is not MISSING
                    and in_a == in_b and yr_a is not MISSING and yr_b is not MISSING
                    and abs(int(yr_a) - int(yr_b)) <= 5):
                na, nb = g(a, "n_t", 0) + g(a, "n_c", 0), g(b, "n_t", 0) + g(b, "n_c", 0)
                if na and nb and abs(na - nb) / max(na, nb) <= 0.25:
                    out.append(Finding(
                        detector="D-03", code="NESTED_COHORT_CANDIDATE",
                        verdict=SUSPECT, severity=SEV_MED,
                        pool_id=g(pool, "pool_id"),
                        message="same author+institution, near-identical N within 5 years",
                        evidence={"rows": [g(a, "row_id"), g(b, "row_id")],
                                  "n_a": na, "n_b": nb, "author": au_a}))
    return out


@register(
    id="D-04", name="N-conservation against the trial's own ceiling", tier=0,
    network=False, requires=("rows",),
    catches="one trial entered k times: pooled N exceeds the trial's true enrolment",
    misses="duplication where the duplicate reports a disjoint subgroup",
    fp_behaviour="Fires legitimately on a multi-arm trial whose shared control arm was "
                 "entered more than once -- a real unit-of-analysis error, so the flag "
                 "is routed to D-13 rather than suppressed. Also fires where a trial "
                 "contributes to mutually exclusive subgroups; suppressed when subgroup "
                 "labels are declared exclusive and their Ns sum to the true N.",
    fn_behaviour="Needs a trustworthy ceiling. If the registry record is itself the "
                 "wrong trial (our finding 4) the ceiling is wrong and this passes; "
                 "that is exactly why D-02 must run first.",
)
def d04(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    agg: dict[str, dict] = defaultdict(lambda: {"pooled": 0.0, "rows": [],
                                                "true": None, "excl": True,
                                                "arms": set()})
    for r in g(pool, "rows", []):
        ctx.touch()
        key = g(r, "trial_key")
        if key is MISSING:
            continue
        a = agg[key]
        a["pooled"] += float(g(r, "n_t", 0)) + float(g(r, "n_c", 0))
        a["rows"].append(g(r, "row_id", "?"))
        a["arms"].add(str(g(r, "arm_label", g(r, "row_id", "?"))))
        if not g(r, "subgroup_exclusive", False):
            a["excl"] = False
        t = g(r, "trial_true_n", g(r, "registry_enrolment"))
        if t is not MISSING and t:
            a["true"] = float(t)
    for key, a in sorted(agg.items()):
        if a["true"] is None:
            out.append(unverifiable(
                "D-04", "NO_ENROLMENT_CEILING",
                f"no true enrolment for {key}; N-conservation cannot be tested",
                missing=["trial_true_n", "registry_enrolment"],
                pool_id=g(pool, "pool_id")))
        elif a["pooled"] > 1.05 * a["true"]:
            factor = a["pooled"] / a["true"]
            if a["excl"] and len(a["rows"]) > 1:
                verdict, code = CHOICE, "N_INFLATION_SUPPRESSED_EXCLUSIVE_SUBGROUPS"
                sev = SEV_INFO
            elif len(a["arms"]) > 1 and factor < 2.5:
                verdict, code, sev = SUSPECT, "N_INFLATION_MULTIARM_ROUTE", SEV_MED
            else:
                verdict, code, sev = INCONSISTENT, "N_INFLATION", SEV_HIGH
            out.append(Finding(
                detector="D-04", code=code, verdict=verdict, severity=sev,
                pool_id=g(pool, "pool_id"),
                message=(f"trial {key}: pooled N {a['pooled']:.0f} vs true "
                         f"{a['true']:.0f} (factor {factor:.2f})"),
                evidence={"trial_key": key, "pooled_n": a["pooled"],
                          "true_n": a["true"], "factor": round(factor, 3),
                          "rows": a["rows"]}))
    return out


@register(
    id="D-05", name="Lower-tail Q / low-heterogeneity corroboration [NOVEL USE]",
    tier=0, network=False, requires=("rows",),
    catches="extreme between-study homogeneity, as the second half of the "
            "N-inflation-plus-low-I2 duplication signature",
    misses="everything at k<5, where the test has essentially no power -- and small k "
           "is the norm (INSPECT-SR Stage 2: 54% of assessable meta-analyses had 1 RCT)",
    fp_behaviour="Restricted randomisation alone moves baseline I2 from 0% to 62% "
                 "(Clark 2021), so randomisation design is a hard gate. Effect metric "
                 "and non-independence across trials are further confounders (Mascha "
                 "2017). Asymptotic Q over-flags, so a Monte Carlo p is computed "
                 "alongside and the stricter of the two governs.",
    fn_behaviour="By design this NEVER fires alone: it upgrades to DUPLICATION_SIGNATURE "
                 "only when D-02/D-03/D-04 already flagged the pool. Alone it emits an "
                 "informational code. Expected yield on a clean corpus: 1.21% at "
                 "p_low<0.01 (Ioannidis 2006, 143/11,803).",
)
def d05(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    eff, ses, designs = [], [], []
    for r in g(pool, "rows", []):
        ctx.touch()
        e, s = g(r, "effect"), g(r, "se")
        if e is not MISSING and s is not MISSING and float(s) > 0:
            eff.append(float(e)); ses.append(float(s))
            designs.append(str(g(r, "randomisation", "unknown")).lower())
    k = len(eff)
    if k < 5:
        out.append(Finding(
            detector="D-05", code="UNDERPOWERED_HOMOGENEITY_TEST", verdict=UNVERIFIABLE,
            severity=SEV_INFO, pool_id=g(pool, "pool_id"),
            message=f"k={k} usable effects; lower-tail Q has no power below k=5",
            evidence={"k": k}))
        return out
    est, se, q = inv_var_pool(eff, ses)
    p_asym = q_lower_tail_p(q, k)
    p_mc = monte_carlo_q_lower(eff, ses, iters=int(g(pool, "mc_iters", 20000)))
    p_gov = max(p_asym, p_mc)
    _, _, tau2, i2 = dersimonian_laird(eff, ses)
    blocked = [d for d in designs if "block" in d]
    gate = None
    if blocked:
        gate = f"restricted allocation in {len(blocked)}/{k} rows"
    corroborated = bool(g(pool, "_prior_duplication_flags", []))
    ev = {"k": k, "Q": round(q, 4), "I2_percent": round(i2, 2),
          "p_lower_asymptotic": round(p_asym, 6),
          "p_lower_montecarlo": round(p_mc, 6),
          "p_governing": round(p_gov, 6),
          "randomisation_gate": gate,
          "corroborating_flags": list(g(pool, "_prior_duplication_flags", []))}
    if p_gov < 0.01 and gate is None:
        if corroborated:
            out.append(Finding(
                detector="D-05", code="DUPLICATION_SIGNATURE", verdict=INCONSISTENT,
                severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
                message=(f"extreme homogeneity (p_low={p_gov:.4g}, I2={i2:.1f}%) "
                         "corroborated by an identity-based duplication flag"),
                evidence=ev))
        else:
            out.append(Finding(
                detector="D-05", code="EXTREME_HOMOGENEITY_UNEXPLAINED",
                verdict=SUSPECT, severity=SEV_LOW, pool_id=g(pool, "pool_id"),
                message=(f"extreme homogeneity (p_low={p_gov:.4g}) with no "
                         "corroborating duplication flag; informational only"),
                evidence=ev))
    elif p_gov < 0.01 and gate is not None:
        out.append(Finding(
            detector="D-05", code="HOMOGENEITY_GATED_BY_DESIGN", verdict=CHOICE,
            severity=SEV_INFO, pool_id=g(pool, "pool_id"),
            message=f"extreme homogeneity present but gated: {gate}",
            evidence=ev))
    return out


# ==========================================================================
# TIER 1 -- arithmetic on the review's own table
# ==========================================================================

@register(
    id="D-06", name="SD/SE dual-interpretation test", tier=1, network=False,
    requires=("rows",),
    catches="a reported dispersion that is an SE masquerading as an SD; effect sizes "
            "of implausible magnitude",
    misses="SE/SD mix-ups that land near |SMD| 1.0 -- Kadlec states these explicitly "
           "as the blind spot of the magnitude rule, which is why the "
           "dispersion-ratio arm exists",
    fp_behaviour="The magnitude arm (|SMD|>=3) is high precision, low recall: 13/22 "
                 "(59%) of >3.0 effects in Kadlec traced to SE/SD. The dispersion-ratio "
                 "arm is the reverse and fires on genuinely low-variance outcomes, so "
                 "it needs >=5 comparable rows before the cohort median is meaningful.",
    fn_behaviour="Blind where only an effect estimate is reported without arm-level "
                 "means and SDs.",
)
def d06(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    rows = g(pool, "rows", [])
    usable = []
    for r in rows:
        ctx.touch()
        need = ("mean_t", "sd_t", "n_t", "mean_c", "sd_c", "n_c")
        miss = missing_of(r, *need)
        if miss:
            out.append(unverifiable(
                "D-06", "NO_ARM_LEVEL_DATA",
                "cannot re-derive the effect size without arm means, SDs and Ns",
                missing=miss, row_id=g(r, "row_id"), pool_id=g(pool, "pool_id")))
        else:
            usable.append(r)
    sds = []
    for r in usable:
        sds.extend([float(g(r, "sd_t")), float(g(r, "sd_c"))])
    med_sd = sorted(sds)[len(sds) // 2] if sds else None
    for r in usable:
        rid = g(r, "row_id", "?")
        d_sd = smd_hedges_g(float(g(r, "mean_t")), float(g(r, "sd_t")), int(g(r, "n_t")),
                            float(g(r, "mean_c")), float(g(r, "sd_c")), int(g(r, "n_c")))
        d_se = smd_hedges_g(float(g(r, "mean_t")),
                            float(g(r, "sd_t")) * math.sqrt(int(g(r, "n_t"))),
                            int(g(r, "n_t")), float(g(r, "mean_c")),
                            float(g(r, "sd_c")) * math.sqrt(int(g(r, "n_c"))),
                            int(g(r, "n_c")))
        if abs(d_sd) >= 3.0:
            code = "SE_AS_SD_SUSPECTED" if abs(d_se) < 3.0 else "IMPLAUSIBLE_EFFECT_SIZE"
            out.append(Finding(
                detector="D-06", code=code,
                verdict=INCONSISTENT if code == "SE_AS_SD_SUSPECTED" else SUSPECT,
                severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                message=(f"SMD as-SD = {d_sd:.2f}; as-SE = {d_se:.2f}"),
                evidence={"smd_as_sd": round(d_sd, 3), "smd_as_se": round(d_se, 3),
                          "threshold": 3.0}))
        elif med_sd and len(usable) >= 5:
            for arm in ("t", "c"):
                sd = float(g(r, f"sd_{arm}")); n = int(g(r, f"n_{arm}"))
                if sd <= med_sd / math.sqrt(n) * 1.5:
                    out.append(Finding(
                        detector="D-06", code="SE_AS_SD_SUSPECTED_WEAK",
                        verdict=SUSPECT, severity=SEV_MED, row_id=rid,
                        pool_id=g(pool, "pool_id"),
                        message=(f"arm {arm} dispersion {sd:.3f} is close to "
                                 f"cohort_median/sqrt(n) = {med_sd/math.sqrt(n):.3f}"),
                        evidence={"arm": arm, "sd": sd, "n": n,
                                  "cohort_median_sd": med_sd}))
    return out


@register(
    id="D-07", name="Effect-measure dimensional plausibility [NOVEL]", tier=1,
    network=False, requires=("rows",),
    catches="a quantity that is not a hazard ratio printed under an HR heading; an HR "
            "whose CI implies an impossible number of events",
    misses="a mislabelled ratio whose CI happens to imply a feasible event count and "
           "whose source does contain survival language",
    fp_behaviour="Arm A assumes 1:1 allocation and light covariate adjustment; heavy "
                 "adjustment or unbalanced allocation shifts implied events by roughly "
                 "1.2-2x, which is why the reported-events comparison uses a generous "
                 "3x band. HRs digitised from Kaplan-Meier curves have imputed SEs and "
                 "are suppressed when the review declares indirect estimation. Arm B "
                 "must only run on full text, never abstracts.",
    fn_behaviour="Silent when no CI is reported, and when the source text is "
                 "unavailable Arm B degrades to UNVERIFIABLE rather than passing.",
)
def d07(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        if str(g(r, "measure", "")).upper() != "HR":
            continue
        if g(r, "hr_indirect_from_km", False):
            out.append(Finding(
                detector="D-07", code="HR_INDIRECT_SUPPRESSED", verdict=CHOICE,
                severity=SEV_INFO, row_id=rid, pool_id=g(pool, "pool_id"),
                message="HR declared as indirectly estimated from KM curves; Arm A skipped",
                evidence={"declared": "hr_indirect_from_km"}))
        else:
            lo, hi = g(r, "ci_lo"), g(r, "ci_hi")
            n_tot = g(r, "n_t", 0) + g(r, "n_c", 0)
            if lo is MISSING or hi is MISSING:
                out.append(unverifiable(
                    "D-07", "NO_HR_CI", "HR without a CI; implied-events check impossible",
                    missing=missing_of(r, "ci_lo", "ci_hi"), row_id=rid,
                    pool_id=g(pool, "pool_id")))
            elif not n_tot:
                out.append(unverifiable(
                    "D-07", "NO_N_FOR_HR", "HR without arm Ns; cannot bound events",
                    missing=["n_t", "n_c"], row_id=rid, pool_id=g(pool, "pool_id")))
            else:
                lo_f, hi_f = float(lo), float(hi)
                if lo_f <= 0 or hi_f <= 0 or hi_f <= lo_f:
                    out.append(Finding(
                        detector="D-07", code="HR_CI_INVALID",
                        verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                        pool_id=g(pool, "pool_id"),
                        message="HR CI has a non-positive or unordered bound",
                        evidence={"ci": [lo_f, hi_f]}))
                else:
                    e_imp = implied_events_from_hr_ci(lo_f, hi_f)
                    ev = {"ci": [lo_f, hi_f], "implied_events": round(e_imp, 1),
                          "total_n": n_tot}
                    if e_imp > n_tot:
                        out.append(Finding(
                            detector="D-07", code="HR_LABEL_IMPLAUSIBLE",
                            verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                            pool_id=g(pool, "pool_id"),
                            message=(f"CI implies {e_imp:.0f} events in a trial of "
                                     f"{n_tot}; the quantity cannot be a hazard ratio"),
                            evidence=ev))
                    elif e_imp > 0.9 * n_tot:
                        out.append(Finding(
                            detector="D-07", code="HR_LABEL_SUSPECT", verdict=SUSPECT,
                            severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                            message=f"CI implies {e_imp:.0f} events, >90% of N={n_tot}",
                            evidence=ev))
                    rep_e = g(r, "reported_events")
                    if rep_e is not MISSING and rep_e:
                        ratio = e_imp / float(rep_e)
                        if ratio > 3.0 or ratio < 1 / 3.0:
                            out.append(Finding(
                                detector="D-07", code="HR_PRECISION_MISMATCH",
                                verdict=SUSPECT, severity=SEV_MED, row_id=rid,
                                pool_id=g(pool, "pool_id"),
                                message=(f"implied events {e_imp:.0f} vs reported "
                                         f"{rep_e} (ratio {ratio:.2f})"),
                                evidence={**ev, "reported_events": float(rep_e),
                                          "ratio": round(ratio, 2)}))
        src = g(r, "source_fulltext")
        if src is MISSING:
            out.append(unverifiable(
                "D-07", "NO_SOURCE_TEXT",
                "no full text; cannot test for time-to-event machinery",
                missing=["source_fulltext"], row_id=rid, pool_id=g(pool, "pool_id")))
        else:
            low = str(src).lower()
            if not any(term in low for term in TTE_TERMS):
                out.append(Finding(
                    detector="D-07", code="HR_LABEL_UNSUPPORTED", verdict=INCONSISTENT,
                    severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                    message="row labelled HR but source contains no time-to-event method",
                    evidence={"searched_terms": list(TTE_TERMS),
                              "source_chars": len(low)}))
        alt = g(r, "source_alt_labels")
        if alt is not MISSING and isinstance(alt, dict):
            est = g(r, "effect")
            for label, val in alt.items():
                if est is not MISSING and val is not None and \
                        abs(float(val) - float(est)) < 1e-9:
                    out.append(Finding(
                        detector="D-07", code="LABEL_COLLISION", verdict=INCONSISTENT,
                        severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                        message=(f"the value entered as an HR appears in the source "
                                 f"labelled '{label}'"),
                        evidence={"value": float(est), "other_label": label}))
    return out


@register(
    id="D-08", name="CI<->SE divisor and distribution consistency", tier=1,
    network=False, requires=("rows",),
    catches="a 90% or 99% interval entered as if 95%; an SE inconsistent with its own "
            "CI; a normal quantile used where the Handbook requires t",
    misses="an SE and CI that are consistently wrong together",
    fp_behaviour="Heavily rounded published limits inflate the apparent divisor error, "
                 "so rows reporting fewer than two significant figures are skipped.",
    fn_behaviour="Cannot fire when SE is absent; emits UNVERIFIABLE instead.",
)
def d08(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        lo, hi, se = g(r, "ci_lo"), g(r, "ci_hi"), g(r, "se")
        if MISSING in (lo, hi, se):
            out.append(unverifiable(
                "D-08", "NO_CI_OR_SE", "need ci_lo, ci_hi and se",
                missing=missing_of(r, "ci_lo", "ci_hi", "se"), row_id=rid,
                pool_id=g(pool, "pool_id")))
            continue
        ratio_scale = str(g(r, "measure", "")).upper() in RATIO_MEASURES
        entered_log = bool(g(r, "entered_on_log_scale", ratio_scale))
        lo_f, hi_f = float(lo), float(hi)
        se_f = float(se)
        if se_f <= 0:
            out.append(Finding(
                detector="D-08", code="NONPOSITIVE_SE", verdict=INCONSISTENT,
                severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                message="standard error is not positive",
                evidence={"se": se_f}))
            continue
        if ratio_scale and not entered_log:
            if lo_f <= 0 or hi_f <= 0:
                out.append(Finding(
                    detector="D-08", code="NONPOSITIVE_RATIO_CI",
                    verdict=UNVERIFIABLE, severity=SEV_INFO, row_id=rid,
                    pool_id=g(pool, "pool_id"),
                    message="ratio-measure CI has a non-positive bound; log-divisor check impossible",
                    evidence={"ci": [lo_f, hi_f]}))
                continue
            l2, h2 = math.log(lo_f), math.log(hi_f)
        else:
            l2, h2 = lo_f, hi_f
        div = (h2 - l2) / se_f
        ev = {"implied_divisor": round(div, 4), "se": se_f, "ci": [lo, hi]}
        level = float(g(r, "ci_level", 0.95))
        expected = 2.0 * norm_ppf(0.5 + level / 2.0)
        if abs(div - expected) > 0.15:
            if abs(div - 3.29) < 0.10:
                out.append(Finding(
                    detector="D-08", code="CI_LEVEL_MISMATCH", verdict=INCONSISTENT,
                    severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                    message="divisor ~3.29: a 90% interval is being used as 95%",
                    evidence={**ev, "suspected_level": 0.90}))
            elif abs(div - 5.15) < 0.15:
                out.append(Finding(
                    detector="D-08", code="CI_LEVEL_MISMATCH", verdict=INCONSISTENT,
                    severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                    message="divisor ~5.15: a 99% interval is being used as 95%",
                    evidence={**ev, "suspected_level": 0.99}))
            else:
                out.append(Finding(
                    detector="D-08", code="SE_CI_INCONSISTENT", verdict=INCONSISTENT,
                    severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=f"implied divisor {div:.3f} vs expected {expected:.3f}",
                    evidence={**ev, "expected_divisor": round(expected, 4)}))
        else:
            nt, nc = g(r, "n_t"), g(r, "n_c")
            if (str(g(r, "outcome_type", "continuous")).lower() == "continuous"
                    and nt is not MISSING and nc is not MISSING
                    and min(int(nt), int(nc)) < 30):
                df = int(nt) + int(nc) - 2
                tdiv = 2.0 * t_ppf(0.975, df)
                if abs(div - expected) < 0.05 and abs(div - tdiv) > 0.15:
                    out.append(Finding(
                        detector="D-08", code="NORMAL_USED_WHERE_T_REQUIRED",
                        verdict=SUSPECT, severity=SEV_LOW, row_id=rid,
                        pool_id=g(pool, "pool_id"),
                        message=(f"normal quantile used with df={df}; Handbook 6.3.1 "
                                 f"requires t (divisor {tdiv:.3f})"),
                        evidence={**ev, "df": df, "t_divisor": round(tdiv, 4)}))
    return out


@register(
    id="D-09", name="Log-scale entry check for ratio measures", tier=1,
    network=False, requires=("rows",),
    catches="an RR/OR/HR entered on the raw scale where the Handbook requires ln",
    misses="raw-scale entry for ratios near 1.0, where both scales are near-symmetric",
    fp_behaviour="Suppressed for 0.9 < estimate < 1.11 because the test has no power "
                 "there. Rounded limits can manufacture spurious asymmetry, so rows "
                 "with fewer than two decimals are skipped.",
    fn_behaviour="Silent by design in the low-power band, which is stated rather than "
                 "hidden.",
)
def d09(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        if str(g(r, "measure", "")).upper() not in RATIO_MEASURES:
            continue
        est, lo, hi = g(r, "effect"), g(r, "ci_lo"), g(r, "ci_hi")
        if MISSING in (est, lo, hi):
            out.append(unverifiable(
                "D-09", "NO_RATIO_CI", "need effect and both CI limits",
                missing=missing_of(r, "effect", "ci_lo", "ci_hi"), row_id=rid,
                pool_id=g(pool, "pool_id")))
            continue
        est, lo, hi = float(est), float(lo), float(hi)
        if min(est, lo, hi) <= 0:
            out.append(Finding(
                detector="D-09", code="NONPOSITIVE_RATIO", verdict=INCONSISTENT,
                severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                message="ratio measure with a non-positive value or limit",
                evidence={"effect": est, "ci": [lo, hi]}))
            continue
        if 0.9 < est < 1.11:
            out.append(Finding(
                detector="D-09", code="LOW_POWER_BAND", verdict=UNVERIFIABLE,
                severity=SEV_INFO, row_id=rid, pool_id=g(pool, "pool_id"),
                message="ratio too close to 1.0 for the symmetry test to discriminate",
                evidence={"effect": est}))
            continue
        sym_log = abs(math.log(hi) - math.log(est)) - abs(math.log(est) - math.log(lo))
        sym_raw = abs(hi - est) - abs(est - lo)
        if abs(sym_log) > 0.05 and abs(sym_raw) < 0.02:
            out.append(Finding(
                detector="D-09", code="RAW_SCALE_ENTRY_SUSPECTED", verdict=INCONSISTENT,
                severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                message=("CI is symmetric on the ratio scale, not the log scale: "
                         "the value was entered without taking logs"),
                evidence={"asym_log": round(sym_log, 5), "asym_raw": round(sym_raw, 5),
                          "effect": est, "ci": [lo, hi]}))
    return out


@register(
    id="D-10", name="Sign and reciprocal check", tier=1, network=False,
    requires=("rows",),
    catches="an effect entered with the wrong sign; a ratio entered as its reciprocal; "
            "opposite-polarity scales pooled with no documented reversal; a negative SD",
    misses="a sign error that coincides with a genuine reversal of the outcome's framing",
    fp_behaviour="Low. The main benign cause is a pool framed as risk of harm rather "
                 "than benefit, resolved by comparing against the pool's declared "
                 "direction rather than an assumed one.",
    fn_behaviour="Needs raw cells to derive the implied sign; degrades to UNVERIFIABLE.",
)
def d10(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    polarities = set()
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        pol = g(r, "scale_polarity")
        if pol is not MISSING:
            polarities.add(str(pol))
        sd_t, sd_c = g(r, "sd_t"), g(r, "sd_c")
        for nm, v in (("sd_t", sd_t), ("sd_c", sd_c)):
            if v is not MISSING and float(v) < 0:
                out.append(Finding(
                    detector="D-10", code="IMPOSSIBLE_SD", verdict=INCONSISTENT,
                    severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=f"{nm} is negative; an SD is never sign-adjusted",
                    evidence={nm: float(v)}))
        est = g(r, "effect")
        if est is MISSING:
            out.append(unverifiable("D-10", "NO_EFFECT", "no effect estimate",
                                    missing=["effect"], row_id=rid,
                                    pool_id=g(pool, "pool_id")))
            continue
        est = float(est)
        implied = None
        if not missing_of(r, "mean_t", "mean_c"):
            implied = math.copysign(1.0, float(g(r, "mean_t")) - float(g(r, "mean_c"))) \
                if float(g(r, "mean_t")) != float(g(r, "mean_c")) else 0.0
        elif not missing_of(r, "e_t", "n_t", "e_c", "n_c"):
            nt, nc = float(g(r, "n_t")), float(g(r, "n_c"))
            if nt <= 0 or nc <= 0:
                out.append(Finding(
                    detector="D-10", code="NONPOSITIVE_RATE_DENOMINATOR",
                    verdict=UNVERIFIABLE, severity=SEV_INFO, row_id=rid,
                    pool_id=g(pool, "pool_id"),
                    message="event-rate sign/reciprocal check needs positive arm denominators",
                    evidence={"n_t": nt, "n_c": nc}))
                continue
            rt = float(g(r, "e_t")) / nt
            rc = float(g(r, "e_c")) / nc
            if str(g(r, "measure", "")).upper() in RATIO_MEASURES:
                cells_ratio = (rt / rc) if rc > 0 else None
                if cells_ratio and cells_ratio > 0 and est > 0:
                    if abs(est - 1.0 / cells_ratio) < 0.02 * cells_ratio and \
                            abs(est - cells_ratio) > 0.02 * cells_ratio:
                        out.append(Finding(
                            detector="D-10", code="RECIPROCAL_ENTERED",
                            verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                            pool_id=g(pool, "pool_id"),
                            message=("entered value equals the reciprocal of the "
                                     "ratio implied by the 2x2"),
                            evidence={"entered": est,
                                      "from_cells": round(cells_ratio, 5)}))
                implied = None
            else:
                implied = math.copysign(1.0, rt - rc) if rt != rc else 0.0
        if implied is not None and implied != 0.0 and est != 0.0:
            if math.copysign(1.0, est) != implied:
                out.append(Finding(
                    detector="D-10", code="SIGN_ERROR", verdict=INCONSISTENT,
                    severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                    message="entered effect has the opposite sign to the raw cells",
                    evidence={"entered": est, "implied_sign": implied}))
    if len(polarities) > 1:
        methods = str(g(pool, "methods_text", "")).lower()
        if "multiply" not in methods and "-1" not in methods and "revers" not in methods:
            out.append(Finding(
                detector="D-10", code="UNDOCUMENTED_POLARITY", verdict=INCONSISTENT,
                severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
                message=("scales of opposite polarity pooled with no stated reversal; "
                         "MECIR C61 is mandatory"),
                evidence={"polarities": sorted(polarities)}))
    return out


@register(
    id="D-11", name="2x2 and continuous-cell integrity", tier=1, network=False,
    requires=("rows",),
    catches="events exceeding N; negative or zero denominators; non-positive SDs; "
            "arm Ns exceeding the randomised total; N drifting across outcomes of one "
            "trial with no missingness statement; baseline categories not summing to N",
    misses="internally consistent but wrong numbers",
    fp_behaviour="N_DRIFT fires legitimately where outcomes have different missingness, "
                 "hence suppression when a missingness statement is present. The "
                 "category-sum check is pure integer arithmetic and near-zero FP: "
                 "Bolland 2025 found 51/929 (5.5%) failures.",
    fn_behaviour="Cannot detect a plausible-but-wrong count.",
)
def d11(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    per_trial: dict[str, list] = defaultdict(list)
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        for arm in ("t", "c"):
            e, n = g(r, f"e_{arm}"), g(r, f"n_{arm}")
            if e is not MISSING and n is not MISSING:
                if float(n) <= 0:
                    out.append(Finding(
                        detector="D-11", code="NONPOSITIVE_N", verdict=INCONSISTENT,
                        severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                        message=f"arm {arm} has n={n}",
                        evidence={f"n_{arm}": float(n)}))
                elif float(e) < 0:
                    out.append(Finding(
                        detector="D-11", code="NEGATIVE_EVENTS", verdict=INCONSISTENT,
                        severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                        message=f"arm {arm} has {e} events",
                        evidence={f"e_{arm}": float(e)}))
                elif float(e) > float(n):
                    out.append(Finding(
                        detector="D-11", code="EVENTS_EXCEED_N", verdict=INCONSISTENT,
                        severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                        message=f"arm {arm}: {e} events in {n} participants",
                        evidence={f"e_{arm}": float(e), f"n_{arm}": float(n)}))
            sd = g(r, f"sd_{arm}")
            if sd is not MISSING and float(sd) <= 0:
                out.append(Finding(
                    detector="D-11", code="NONPOSITIVE_SD", verdict=INCONSISTENT,
                    severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=f"arm {arm} SD is {sd}",
                    evidence={f"sd_{arm}": float(sd)}))
        tot = g(r, "trial_true_n")
        if tot is not MISSING and not missing_of(r, "n_t", "n_c"):
            s = float(g(r, "n_t")) + float(g(r, "n_c"))
            if s > 1.05 * float(tot):
                out.append(Finding(
                    detector="D-11", code="ARMS_EXCEED_RANDOMISED", verdict=INCONSISTENT,
                    severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=f"arm Ns sum to {s:.0f} vs randomised {float(tot):.0f}",
                    evidence={"arm_sum": s, "randomised": float(tot)}))
        cats = g(r, "baseline_categories")
        if cats is not MISSING and isinstance(cats, dict):
            for var, spec in cats.items():
                counts, n_arm = spec.get("counts", []), spec.get("n")
                if counts and n_arm and sum(counts) != n_arm:
                    out.append(Finding(
                        detector="D-11", code="CATEGORY_SUM_MISMATCH",
                        verdict=INCONSISTENT, severity=SEV_MED, row_id=rid,
                        pool_id=g(pool, "pool_id"),
                        message=(f"baseline '{var}': categories sum to {sum(counts)}, "
                                 f"arm N is {n_arm}"),
                        evidence={"variable": var, "counts": counts, "n": n_arm}))
        key = g(r, "trial_key")
        if key is not MISSING and not missing_of(r, "n_t", "n_c"):
            per_trial[key].append((rid, float(g(r, "n_t")) + float(g(r, "n_c")),
                                   bool(g(r, "missingness_stated", False))))
    for key, entries in sorted(per_trial.items()):
        if len(entries) < 2:
            continue
        ns = [e[1] for e in entries]
        if max(ns) > 0 and (max(ns) - min(ns)) / max(ns) > 0.20:
            if all(e[2] for e in entries):
                continue
            out.append(Finding(
                detector="D-11", code="N_DRIFT", verdict=SUSPECT, severity=SEV_MED,
                pool_id=g(pool, "pool_id"),
                message=(f"trial {key}: N varies {min(ns):.0f}-{max(ns):.0f} across "
                         "outcomes with no missingness statement"),
                evidence={"trial_key": key, "ns": ns,
                          "rows": [e[0] for e in entries]}))
    return out


@register(
    id="D-12", name="Arm-transposition detector", tier=1, network=False,
    requires=("rows",),
    catches="two records of one trial whose arm Ns are the same multiset but assigned "
            "differently; denominators swapped between arms",
    misses="a transposition present identically in every record of the trial",
    fp_behaviour="Very low. A transposition is not a defensible choice, which is what "
                 "makes this rule high precision, unlike most cross-review comparisons. "
                 "Only fires spuriously when two arms genuinely have equal N and the "
                 "records disagree for a substantive reason.",
    fn_behaviour="Needs two independent records of the same trial.",
)
def d12(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    by_trial: dict[str, list] = defaultdict(list)
    for r in g(pool, "rows", []):
        ctx.touch()
        key = g(r, "trial_key")
        if key is not MISSING and not missing_of(r, "n_t", "n_c"):
            by_trial[key].append(r)
    for key, rs in sorted(by_trial.items()):
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = rs[i], rs[j]
                if g(a, "outcome") != g(b, "outcome"):
                    continue
                na = (float(g(a, "n_t")), float(g(a, "n_c")))
                nb = (float(g(b, "n_t")), float(g(b, "n_c")))
                if na != nb and sorted(na) == sorted(nb):
                    out.append(Finding(
                        detector="D-12", code="ARM_TRANSPOSITION", verdict=INCONSISTENT,
                        severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
                        message=(f"trial {key}: arm Ns {na} vs {nb} -- same multiset, "
                                 "different assignment"),
                        evidence={"trial_key": key, "a": list(na), "b": list(nb),
                                  "rows": [g(a, "row_id"), g(b, "row_id")]}))
                ea, eb = g(a, "e_t"), g(b, "e_t")
                ea2, eb2 = g(a, "e_c"), g(b, "e_c")
                if MISSING not in (ea, eb, ea2, eb2) and \
                        (float(ea), float(ea2)) == (float(eb), float(eb2)) and na != nb:
                    out.append(Finding(
                        detector="D-12", code="DENOMINATOR_TRANSPOSITION",
                        verdict=INCONSISTENT, severity=SEV_HIGH,
                        pool_id=g(pool, "pool_id"),
                        message=f"trial {key}: identical events, swapped denominators",
                        evidence={"trial_key": key, "n_a": list(na), "n_b": list(nb),
                                  "rows": [g(a, "row_id"), g(b, "row_id")]}))
    return out


@register(
    id="D-13", name="Multi-arm shared-control double-count", tier=1, network=False,
    requires=("rows",),
    catches="a shared control arm entered whole in more than one comparison; a control "
            "arm repeated with identical mean and SD and un-halved N",
    misses="double-counting that was partially corrected",
    fp_behaviour="Low provided subgroup structure is parsed: a trial contributing to "
                 "two mutually exclusive subgroups is not double-counting. Axon 2023 "
                 "gives the cross-check -- combining and splitting must yield the same "
                 "point estimate with different CIs.",
    fn_behaviour="Needs the trial's true control-arm N; otherwise UNVERIFIABLE.",
)
def d13(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    agg: dict[str, dict] = defaultdict(lambda: {"csum": 0.0, "rows": [],
                                                "true_c": None, "sig": []})
    for r in g(pool, "rows", []):
        ctx.touch()
        key = g(r, "trial_key")
        if key is MISSING or g(r, "n_c") is MISSING:
            continue
        a = agg[key]
        a["csum"] += float(g(r, "n_c"))
        a["rows"].append(g(r, "row_id", "?"))
        a["sig"].append((g(r, "mean_c"), g(r, "sd_c"), g(r, "n_c")))
        tc = g(r, "trial_control_n")
        if tc is not MISSING:
            a["true_c"] = float(tc)
    for key, a in sorted(agg.items()):
        if len(a["rows"]) < 2:
            continue
        if a["true_c"] is None:
            out.append(unverifiable(
                "D-13", "NO_TRUE_CONTROL_N",
                f"trial {key} contributes {len(a['rows'])} rows but no control-arm N",
                missing=["trial_control_n"], pool_id=g(pool, "pool_id")))
            continue
        ratio = a["csum"] / a["true_c"] if a["true_c"] else float("inf")
        if ratio >= 1.9:
            out.append(Finding(
                detector="D-13", code="SHARED_CONTROL_DOUBLE_COUNT",
                verdict=INCONSISTENT, severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
                message=(f"trial {key}: control N summed to {a['csum']:.0f} against a "
                         f"true {a['true_c']:.0f} (x{ratio:.2f}); MECIR C66 is mandatory"),
                evidence={"trial_key": key, "control_sum": a["csum"],
                          "true_control_n": a["true_c"], "ratio": round(ratio, 3),
                          "rows": a["rows"]}))
        sigs = [s for s in a["sig"] if MISSING not in s]
        if len(sigs) >= 2 and len(set(map(tuple, sigs))) == 1:
            out.append(Finding(
                detector="D-13", code="CONTROL_ARM_NOT_SPLIT", verdict=INCONSISTENT,
                severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
                message=f"trial {key}: identical control mean/SD/n in {len(sigs)} rows",
                evidence={"trial_key": key, "signature": list(sigs[0]),
                          "rows": a["rows"]}))
    return out


@register(
    id="D-14", name="Cluster-adjustment detector", tier=1, network=False,
    requires=("rows",),
    catches="a cluster-randomised trial entered with an unadjusted SE",
    misses="adjustment applied with the wrong ICC",
    fp_behaviour="Requires an ICC, which is frequently absent -- Konnyu 2021 built a "
                 "database of 59 ICCs precisely because the inputs for the standard fix "
                 "are usually missing. Where ICC is unavailable this emits UNVERIFIABLE, "
                 "never a pass.",
    fn_behaviour="Blind to cluster trials that were not labelled as such upstream.",
)
def d14(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        if str(g(r, "design", "")).lower() != "cluster":
            continue
        miss = missing_of(r, "cluster_m", "icc", "se")
        if miss:
            out.append(unverifiable(
                "D-14", "NO_CLUSTER_INPUTS",
                "cluster trial without M, ICC or SE; adjustment cannot be verified",
                missing=miss, row_id=rid, pool_id=g(pool, "pool_id")))
            continue
        de = design_effect(float(g(r, "cluster_m")), float(g(r, "icc")))
        naive = g(r, "se_naive")
        if naive is MISSING and not missing_of(r, "e_t", "n_t", "e_c", "n_c"):
            _, naive = log_rr(g(r, "e_t"), g(r, "n_t"), g(r, "e_c"), g(r, "n_c"))
        if naive is MISSING:
            out.append(unverifiable(
                "D-14", "NO_NAIVE_SE", "cannot derive an unadjusted SE for comparison",
                missing=["se_naive", "e_t", "n_t", "e_c", "n_c"], row_id=rid,
                pool_id=g(pool, "pool_id")))
            continue
        ratio = float(g(r, "se")) / float(naive)
        ev = {"design_effect": round(de, 4), "sqrt_de": round(math.sqrt(de), 4),
              "se_entered": float(g(r, "se")), "se_naive": float(naive),
              "ratio": round(ratio, 4)}
        if abs(ratio - 1.0) < 0.05:
            out.append(Finding(
                detector="D-14", code="CLUSTERING_IGNORED", verdict=INCONSISTENT,
                severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                message=("entered SE equals the naive SE; clustering was ignored and "
                         "this row will be over-weighted (MECIR C70)"),
                evidence=ev))
        elif abs(ratio - math.sqrt(de)) >= 0.10:
            out.append(Finding(
                detector="D-14", code="CLUSTER_ADJUSTMENT_UNCLEAR", verdict=SUSPECT,
                severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                message=f"SE ratio {ratio:.3f} matches neither 1 nor sqrt(DE)",
                evidence=ev))
    return out


@register(
    id="D-15", name="Crossover-handling detector", tier=1, network=False,
    requires=("rows",),
    catches="a crossover trial entered as arm-wise parallel-group data; an imputed "
            "correlation left unstated, escalated when the measure is an SMD",
    misses="crossover trials not labelled as such",
    fp_behaviour="Low, but wholly dependent on correct design labelling. Nolan 2016 "
                 "found only 69/218 (32%) of crossover trials presented results in an "
                 "includable form at all.",
    fn_behaviour="Silent where design is unlabelled; that is why an explicit "
                 "UNVERIFIABLE is emitted for rows with no design field.",
)
def d15(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        design = g(r, "design")
        if design is MISSING:
            out.append(unverifiable("D-15", "NO_DESIGN_LABEL",
                                    "row has no design field", missing=["design"],
                                    row_id=rid, pool_id=g(pool, "pool_id")))
            continue
        if str(design).lower() != "crossover":
            continue
        layout = str(g(r, "layout", "armwise")).lower()
        if layout == "armwise":
            out.append(Finding(
                detector="D-15", code="CROSSOVER_AS_PARALLEL", verdict=INCONSISTENT,
                severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                message=("crossover trial entered as parallel-group arm data; "
                         "conservative in direction but a unit-of-analysis error"),
                evidence={"layout": layout}))
        if g(r, "sd_diff") is MISSING and g(r, "imputed_corr") is MISSING:
            sev = SEV_HIGH if str(g(r, "measure", "")).upper() == "SMD" else SEV_MED
            out.append(Finding(
                detector="D-15", code="UNSTATED_CORRELATION",
                verdict=INCONSISTENT if sev == SEV_HIGH else SUSPECT, severity=sev,
                row_id=rid, pool_id=g(pool, "pool_id"),
                message=("no SD of differences and no stated correlation" +
                         ("; for an SMD the correlation changes the POINT ESTIMATE"
                          if sev == SEV_HIGH else "")),
                evidence={"measure": str(g(r, "measure", "")),
                          "escalated": sev == SEV_HIGH}))
    return out


@register(
    id="D-16", name="Pooled-estimate recomputation", tier=1, network=False,
    requires=("rows", "pooled_estimate"),
    catches="a reported pooled estimate or CI width that does not recompute from the "
            "review's own per-study table under the declared model",
    misses="an error present identically in the table and the pool",
    fp_behaviour="Dominated by undeclared estimator defaults rather than real error: "
                 "Maassen 2020 found 2/33 meta-analyses reported model, software and "
                 "estimator. Where the estimator is undeclared the pool is recomputed "
                 "under both common-effect and DerSimonian-Laird and flagged only if "
                 "BOTH exceed threshold.",
    fn_behaviour="Cannot fire without a per-study effect and SE on every row.",
)
def d16(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    eff, ses = [], []
    for r in g(pool, "rows", []):
        ctx.touch()
        e, s = g(r, "effect"), g(r, "se")
        if e is not MISSING and s is not MISSING and float(s) > 0:
            eff.append(float(e)); ses.append(float(s))
    rep = g(pool, "pooled_estimate")
    lo, hi = g(pool, "pooled_ci_lo"), g(pool, "pooled_ci_hi")
    if rep is MISSING or len(eff) < 2:
        out.append(unverifiable(
            "D-16", "CANNOT_RECOMPUTE",
            "need a reported pooled estimate and >=2 rows with effect+SE",
            missing=missing_of(pool, "pooled_estimate") + (["rows_with_effect_se"]
                                                          if len(eff) < 2 else []),
            pool_id=g(pool, "pool_id")))
        return out
    model = str(g(pool, "model", "")).lower()
    cands = {}
    fe, fe_se, _ = inv_var_pool(eff, ses)
    cands["common_effect"] = (fe, fe_se)
    re_est, re_se, _, _ = dersimonian_laird(eff, ses)
    cands["dersimonian_laird"] = (re_est, re_se)
    if "random" in model:
        chosen = {"dersimonian_laird": cands["dersimonian_laird"]}
    elif "common" in model or "fixed" in model:
        chosen = {"common_effect": cands["common_effect"]}
    else:
        chosen = cands
        out.append(Finding(
            detector="D-16", code="UNVERIFIABLE_METHOD", verdict=UNVERIFIABLE,
            severity=SEV_INFO, pool_id=g(pool, "pool_id"),
            message="no model declared; testing against every candidate",
            evidence={"candidates": sorted(cands)}))
    z = norm_ppf(0.975)
    results = {}
    for nm, (est, se) in chosen.items():
        d_est = abs(est - float(rep)) / abs(float(rep)) if float(rep) != 0 else abs(est)
        d_ciw = None
        if lo is not MISSING and hi is not MISSING and float(hi) > float(lo):
            rep_w = float(hi) - float(lo)
            d_ciw = abs(2 * z * se - rep_w) / rep_w
        results[nm] = {"recomputed": round(est, 6), "d_est": round(d_est, 4),
                       "d_ciw": round(d_ciw, 4) if d_ciw is not None else None}
    worst = min(max(v["d_est"], v["d_ciw"] or 0.0) for v in results.values())
    ev = {"reported": float(rep), "results": results, "k": len(eff),
          "best_relative_difference": round(worst, 4)}
    if worst >= 0.10:
        out.append(Finding(
            detector="D-16", code="NOT_REPRODUCIBLE", verdict=INCONSISTENT,
            severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
            message=f"pool does not recompute within 10% under any declared model",
            evidence=ev))
    elif worst >= 0.05:
        out.append(Finding(
            detector="D-16", code="MARGINALLY_REPRODUCIBLE", verdict=SUSPECT,
            severity=SEV_LOW, pool_id=g(pool, "pool_id"),
            message="pool recomputes within 10% but not within 5%",
            evidence=ev))
    if lo is not MISSING and hi is not MISSING:
        for nm, (est, se) in chosen.items():
            r_lo, r_hi = est - z * se, est + z * se
            null = float(g(pool, "null_value", 0.0))
            rep_crosses = float(lo) <= null <= float(hi)
            rec_crosses = r_lo <= null <= r_hi
            if rep_crosses != rec_crosses or \
                    math.copysign(1, est - null) != math.copysign(1, float(rep) - null):
                out.append(Finding(
                    detector="D-16", code="MEANINGFUL_DIFFERENCE", verdict=INCONSISTENT,
                    severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
                    message=("recomputation changes the interpretation: direction or "
                             "null-crossing differs"),
                    evidence={**ev, "model": nm,
                              "recomputed_ci": [round(r_lo, 5), round(r_hi, 5)],
                              "reported_ci": [float(lo), float(hi)],
                              "null": null}))
                break
    return out


@register(
    id="D-17", name="Weight consistency", tier=1, network=False, requires=("rows",),
    catches="reported weights inconsistent with inverse-variance weighting; near-equal "
            "weights across studies of very different size",
    misses="weights consistent with a different but undeclared weighting scheme",
    fp_behaviour="Fires where the declared model does not match the model actually "
                 "used -- which is itself the finding, not a false positive. "
                 "Mantel-Haenszel weighting legitimately departs from 1/SE^2 and is "
                 "excluded when declared.",
    fn_behaviour="Needs weights to be reported at all; most reviews report them only "
                 "in the forest plot.",
)
def d17(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    ws, ses, ns = [], [], []
    for r in g(pool, "rows", []):
        ctx.touch()
        w, s = g(r, "weight"), g(r, "se")
        if w is not MISSING and s is not MISSING and float(s) > 0:
            ws.append(float(w)); ses.append(float(s))
            ns.append(float(g(r, "n_t", 0)) + float(g(r, "n_c", 0)))
    if len(ws) < 3:
        out.append(unverifiable("D-17", "TOO_FEW_WEIGHTS",
                                "fewer than 3 rows report both weight and SE",
                                missing=["weight", "se"], pool_id=g(pool, "pool_id")))
        return out
    if "mantel" in str(g(pool, "estimator", "")).lower():
        out.append(Finding(
            detector="D-17", code="MH_WEIGHTING_DECLARED", verdict=CHOICE,
            severity=SEV_INFO, pool_id=g(pool, "pool_id"),
            message="Mantel-Haenszel declared; inverse-variance check not applicable",
            evidence={"estimator": str(g(pool, "estimator"))}))
        return out
    exp = [1.0 / (s * s) for s in ses]
    se_ = sum(exp); sw_ = sum(ws)
    exp_n = [e / se_ for e in exp]
    obs_n = [w / sw_ for w in ws]
    mx, my = sum(exp_n) / len(exp_n), sum(obs_n) / len(obs_n)
    num = sum((a - mx) * (b - my) for a, b in zip(exp_n, obs_n))
    den = math.sqrt(sum((a - mx) ** 2 for a in exp_n) *
                    sum((b - my) ** 2 for b in obs_n))
    rho = num / den if den > 0 else 0.0
    if rho < 0.95:
        out.append(Finding(
            detector="D-17", code="WEIGHT_INCONSISTENT", verdict=INCONSISTENT,
            severity=SEV_MED, pool_id=g(pool, "pool_id"),
            message=f"weight-vs-inverse-variance correlation {rho:.3f} < 0.95",
            evidence={"rho": round(rho, 4), "expected": [round(x, 4) for x in exp_n],
                      "observed": [round(x, 4) for x in obs_n]}))
    if ns and max(ns) > 0 and min(n for n in ns if n > 0) > 0:
        if max(ns) / min(n for n in ns if n > 0) > 5 and \
                (max(obs_n) - min(obs_n)) < 0.02:
            out.append(Finding(
                detector="D-17", code="UNWEIGHTED_SUSPECTED", verdict=SUSPECT,
                severity=SEV_MED, pool_id=g(pool, "pool_id"),
                message="near-equal weights across studies differing >5x in size",
                evidence={"weights": [round(x, 4) for x in obs_n], "ns": ns}))
    return out


@register(
    id="D-18", name="Median-to-mean conversion validity", tier=1, network=False,
    requires=("rows",),
    catches="Hozo bands applied outside their stated n range; a conversion estimator "
            "that does not match the quantiles available; skewed data converted under "
            "a normality assumption; imputation uncertainty ignored in pooling",
    misses="a correct estimator applied to fabricated quantiles",
    fp_behaviour="The Bowley gate fires on genuinely skewed outcomes where conversion "
                 "was nonetheless the least-bad option; these are emitted as SUSPECT, "
                 "not INCONSISTENT. No prevalence study of this misapplication exists, "
                 "so the base rate is unknown and this detector would produce the first.",
    fn_behaviour="Blind unless the review declares that a conversion was performed.",
)
def d18(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        conv = g(r, "conversion")
        if conv is MISSING:
            continue
        method = str(conv.get("method", "")).lower()
        n = conv.get("n")
        have_range = conv.get("min") is not None and conv.get("max") is not None
        have_iqr = conv.get("q1") is not None and conv.get("q3") is not None
        if "wan" in method and not have_iqr and have_range:
            out.append(Finding(
                detector="D-18", code="WRONG_ESTIMATOR", verdict=INCONSISTENT,
                severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                message="Wan IQR formula used but only min/median/max are available",
                evidence={"method": method, "available": {"range": have_range,
                                                          "iqr": have_iqr}}))
        if "hozo" in method and n:
            band = conv.get("band", "")
            n = int(n)
            expect = "range/4" if 15 < n <= 70 else ("range/6" if n > 70 else "hozo")
            if band and band != expect:
                out.append(Finding(
                    detector="D-18", code="HOZO_BAND_VIOLATION", verdict=INCONSISTENT,
                    severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=f"n={n} requires {expect}; {band} was used",
                    evidence={"n": n, "band_used": band, "band_required": expect}))
        if have_iqr and conv.get("median") is not None:
            b = bowley_skew(float(conv["q1"]), float(conv["median"]),
                            float(conv["q3"]))
            if abs(b) > 0.3:
                out.append(Finding(
                    detector="D-18", code="SKEW_VIOLATES_CONVERSION", verdict=SUSPECT,
                    severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=(f"Bowley skew {b:.2f}: the median is not centred between "
                             "the quartiles, so approximate normality fails"),
                    evidence={"bowley": round(b, 4), "threshold": 0.3}))
        if not conv.get("uncertainty_inflated", False):
            out.append(Finding(
                detector="D-18", code="IMPUTATION_UNCERTAINTY_IGNORED", verdict=SUSPECT,
                severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                message=("imputed SD entered into inverse-variance pooling with no "
                         "uncertainty inflation; McGrath 2023 documents underestimated "
                         "SEs and overestimated tau^2"),
                evidence={"uncertainty_inflated": False}))
    return out


@register(
    id="D-19", name="Cross-artifact consistency", tier=1, network=False,
    requires=("artifacts",),
    catches="the same quantity rendered differently in the abstract, the results text, "
            "the forest plot, a table and the supplement",
    misses="an error replicated identically across every artifact",
    fp_behaviour="Near zero and zero-cost. Differences within the precision of the "
                 "least precise rendering are ignored. REPRISE recorded 2 forest-vs-text "
                 "discrepancies and 1 forest-plot typo across 121 reproduction attempts.",
    fn_behaviour="Only as good as the number of artifacts supplied.",
)
def d19(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    arts = g(pool, "artifacts")
    ctx.touch(len(g(pool, "rows", [])) or 1)
    if arts is MISSING or not isinstance(arts, dict) or len(arts) < 2:
        out.append(unverifiable("D-19", "TOO_FEW_ARTIFACTS",
                                "need >=2 renderings of the same quantity",
                                missing=["artifacts"], pool_id=g(pool, "pool_id")))
        return out
    keys = sorted(arts)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            ka, kb = keys[i], keys[j]
            a, b = arts[ka], arts[kb]
            for field_ in sorted(set(a) & set(b)):
                va, vb = a[field_], b[field_]
                if va is None or vb is None:
                    continue
                dp = min(_decimals(va), _decimals(vb))
                if round(float(va), dp) != round(float(vb), dp):
                    out.append(Finding(
                        detector="D-19", code="CROSS_ARTIFACT_MISMATCH",
                        verdict=INCONSISTENT, severity=SEV_MED,
                        pool_id=g(pool, "pool_id"),
                        message=f"{field_}: {ka}={va} vs {kb}={vb}",
                        evidence={"field": field_, ka: va, kb: vb,
                                  "compared_at_decimals": dp}))
    return out


def _decimals(v) -> int:
    s = repr(float(v))
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


@register(
    id="D-20", name="GRIM-style integer feasibility", tier=1, network=False,
    requires=("rows",),
    catches="a reported mean of integer data that no integer total can produce; a "
            "percentage compatible with more than one numerator",
    misses="everything once n is large relative to reporting precision -- GRIM's power "
           "collapses as n grows",
    fp_behaviour="A GRIM flag can be a typo, a rounding convention or an excluded "
                 "participant rather than misconduct. Brown & Heathers requested data "
                 "for 21 flagged articles, got 9 replies and confirmed >=1 reporting "
                 "error in all 9 -- the flags were real but several needed only minor "
                 "correction. Verdict is therefore SUSPECT, never INCONSISTENT.",
    fn_behaviour="Silent for non-integer data, which is stated rather than assumed.",
)
def d20(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        for arm in ("t", "c"):
            m, n = g(r, f"mean_{arm}"), g(r, f"n_{arm}")
            if m is MISSING or n is MISSING or not g(r, "integer_data", False):
                continue
            items = int(g(r, "items", 1))
            dec = int(g(r, "mean_decimals", 2))
            if grim_inconsistent(float(m), int(n), items, dec):
                out.append(Finding(
                    detector="D-20", code="GRIM_INCONSISTENT", verdict=SUSPECT,
                    severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=(f"arm {arm} mean {m} is not attainable from {n} integer "
                             f"observations x {items} items"),
                    evidence={"mean": float(m), "n": int(n), "items": items,
                              "decimals": dec}))
        pcts = g(r, "percentages")
        if pcts is not MISSING and isinstance(pcts, dict):
            for label, spec in pcts.items():
                p, n = spec.get("pct"), spec.get("n")
                dp = int(spec.get("decimals", 1))
                if p is None or not n:
                    continue
                cands = [k for k in range(int(n) + 1)
                         if round(100.0 * k / int(n), dp) == round(float(p), dp)]
                if len(cands) != 1:
                    out.append(Finding(
                        detector="D-20", code="AMBIGUOUS_NUMERATOR", verdict=SUSPECT,
                        severity=SEV_LOW, row_id=rid, pool_id=g(pool, "pool_id"),
                        message=(f"'{label}': {p}% of {n} is compatible with "
                                 f"{len(cands)} numerators"),
                        evidence={"label": label, "pct": float(p), "n": int(n),
                                  "candidates": cands[:10]}))
    return out


@register(
    id="D-21", name="statcheck-style p-value recomputation", tier=1, network=False,
    requires=("rows",),
    catches="a reported p-value inconsistent with its own test statistic and df; a "
            "gross inconsistency that flips the .05 decision",
    misses="p-values reported without a test statistic",
    fp_behaviour="ONE DOCUMENTED FAILURE MODE, handled explicitly: statcheck cannot "
                 "handle corrected p-values, so tests applying Bonferroni, Holm, "
                 "Greenhouse-Geisser, FDR and similar are systematically mis-flagged "
                 "while papers OMITTING necessary corrections are certified correct "
                 "(Schmidt, arXiv:1610.01010). Rows naming a correction are suppressed.",
    fn_behaviour="Blind to one-tailed tests reported as two-tailed and vice versa.",
)
def d21(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        tests = g(r, "reported_tests")
        if tests is MISSING:
            continue
        for t in tests:
            kind = str(t.get("kind", "")).lower()
            note = str(t.get("note", "")).lower()
            if any(c in note for c in CORRECTION_TERMS):
                out.append(Finding(
                    detector="D-21", code="CORRECTION_SUPPRESSED", verdict=CHOICE,
                    severity=SEV_INFO, row_id=rid, pool_id=g(pool, "pool_id"),
                    message="a multiplicity correction is named; recomputation skipped",
                    evidence={"note": note}))
                continue
            stat, df, p_rep = t.get("stat"), t.get("df"), t.get("p")
            if stat is None or p_rep is None:
                out.append(unverifiable(
                    "D-21", "INCOMPLETE_TEST", "test statistic or p missing",
                    missing=[k for k in ("stat", "p") if t.get(k) is None],
                    row_id=rid, pool_id=g(pool, "pool_id")))
                continue
            if kind == "t" and df:
                p_calc = 2 * (1 - t_cdf_abs(float(stat), float(df)))
            elif kind == "chi2" and df:
                p_calc = 1 - chi2_cdf(float(stat), int(df))
            elif kind == "z":
                p_calc = 2 * (1 - _phi_abs(float(stat)))
            else:
                out.append(unverifiable(
                    "D-21", "UNSUPPORTED_TEST", f"test kind {kind!r} not supported",
                    missing=["kind/df"], row_id=rid, pool_id=g(pool, "pool_id")))
                continue
            dec = len(str(p_rep).split(".")[1]) if "." in str(p_rep) else 3
            if round(p_calc, dec) != round(float(p_rep), dec):
                gross = (p_calc < 0.05) != (float(p_rep) < 0.05)
                out.append(Finding(
                    detector="D-21",
                    code="GROSS_INCONSISTENT" if gross else "P_INCONSISTENT",
                    verdict=INCONSISTENT, severity=SEV_HIGH if gross else SEV_MED,
                    row_id=rid, pool_id=g(pool, "pool_id"),
                    message=(f"{kind}({df})={stat}: recomputed p={p_calc:.5f}, "
                             f"reported p={p_rep}"),
                    evidence={"kind": kind, "stat": float(stat), "df": df,
                              "p_reported": float(p_rep),
                              "p_recomputed": round(p_calc, 6), "gross": gross}))
    return out


def t_cdf_abs(t: float, df: float) -> float:
    from mg_core import t_cdf
    return t_cdf(abs(t), df)


def _phi_abs(z: float) -> float:
    from mg_core import norm_cdf
    return norm_cdf(abs(z))


# ==========================================================================
# TIER 2 -- requires source documents
# ==========================================================================

@register(
    id="D-22", name="Comparator / intervention concordance [NOVEL]", tier=2,
    network=False, requires=("rows", "declared_comparator"),
    catches="a trial whose actual comparator differs from the comparator the pool "
            "declares, at ingredient level and at class level",
    misses="comparator drift within the trial (treatment switching), which is GRADE "
           "indirectness and a different problem",
    fp_behaviour="Two benign causes. Genuine class-level pooling is legitimate but must "
                 "be declared, hence the protocol gate -- and Tendal found 0/10 "
                 "protocols gave a control-group hierarchy, so the class-substitution "
                 "code is expected to fire often simply because nobody writes it down. "
                 "Brand-vs-generic and salt forms are handled by normalisation.",
    fn_behaviour="Cannot fire when the trial's actual comparator is unavailable; emits "
                 "UNVERIFIABLE_COMPARATOR instead of passing.",
)
def d22(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    decl = g(pool, "declared_comparator")
    dic = g(pool, "drug_dictionary", {})
    protocol_class = bool(g(pool, "protocol_declares_class_pooling", False))
    if decl is MISSING:
        out.append(unverifiable("D-22", "NO_DECLARED_COMPARATOR",
                                "pool does not declare a comparator",
                                missing=["declared_comparator"],
                                pool_id=g(pool, "pool_id")))
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        actual = g(r, "comparator_from_source")
        if decl is MISSING:
            continue
        if actual is MISSING:
            out.append(unverifiable(
                "D-22", "UNVERIFIABLE_COMPARATOR",
                "trial's actual comparator not extracted from source or registry",
                missing=["comparator_from_source"], row_id=rid,
                pool_id=g(pool, "pool_id")))
            continue
        d_ing = _norm_drug(str(decl), dic)
        a_ing = _norm_drug(str(actual), dic)
        if d_ing["ingredient"] == a_ing["ingredient"]:
            continue
        same_class = (d_ing["atc_class"] and
                      d_ing["atc_class"] == a_ing["atc_class"])
        if same_class and protocol_class:
            out.append(Finding(
                detector="D-22", code="CLASS_LEVEL_POOLING", verdict=CHOICE,
                severity=SEV_INFO, row_id=rid, pool_id=g(pool, "pool_id"),
                message=(f"{a_ing['ingredient']} pooled as {d_ing['ingredient']}; "
                         "protocol declares class-level pooling"),
                evidence={"declared": d_ing, "actual": a_ing}))
        elif same_class:
            out.append(Finding(
                detector="D-22", code="COMPARATOR_CLASS_SUBSTITUTION",
                verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                pool_id=g(pool, "pool_id"),
                message=(f"trial comparator is {a_ing['ingredient']} but the pool "
                         f"declares {d_ing['ingredient']}; same class, undeclared"),
                evidence={"declared": d_ing, "actual": a_ing,
                          "protocol_declares_class_pooling": False}))
        else:
            out.append(Finding(
                detector="D-22", code="COMPARATOR_MISMATCH", verdict=INCONSISTENT,
                severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                message=(f"trial comparator {a_ing['ingredient']} is not in the same "
                         f"class as the declared {d_ing['ingredient']}"),
                evidence={"declared": d_ing, "actual": a_ing}))
    return out


def _norm_drug(name: str, dic: dict) -> dict:
    key = re.sub(r"[^a-z]", "", name.lower())
    for suffix in ("hydrochloride", "maleate", "sodium", "besylate", "mesylate"):
        key = key.replace(suffix, "")
    entry = dic.get(key) or dic.get(name.lower())
    if entry:
        return {"ingredient": entry.get("ingredient", key),
                "atc_class": entry.get("atc_class")}
    return {"ingredient": key, "atc_class": None}


@register(
    id="D-23", name="Outcome/timepoint/scale concordance and multiplicity", tier=2,
    network=False, requires=("rows",),
    catches="pooled numbers that correspond to an outcome, timepoint or scale the pool "
            "does not declare; rows where more than one admissible value existed and "
            "the review did not say which it used",
    misses="substitution where the source reports only one admissible value that is "
           "itself mislabelled",
    fp_behaviour="UNJUSTIFIED_SELECTION is expected to fire on roughly a third of rows "
                 "on current evidence (Tendal 2011: 29%/36%/35% multiplicity) and is "
                 "therefore labelled a CHOICE, not an error. Carroll's definition "
                 "governs: an error is a value reflecting NONE of the source's "
                 "potential data.",
    fn_behaviour="Needs the source's full admissible set enumerated upstream.",
)
def d23(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    d_out = g(pool, "declared_outcome")
    d_tp = g(pool, "declared_timepoint")
    d_sc = g(pool, "declared_scale")
    mult = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        adm = g(r, "admissible_tuples")
        used = (g(r, "outcome"), g(r, "timepoint"), g(r, "scale"))
        if adm is MISSING:
            out.append(unverifiable(
                "D-23", "NO_ADMISSIBLE_SET",
                "source's admissible outcome/timepoint/scale set not enumerated",
                missing=["admissible_tuples"], row_id=rid, pool_id=g(pool, "pool_id")))
        else:
            adm_t = [tuple(a) for a in adm]
            mult.append(len(adm_t))
            if MISSING not in used and tuple(used) not in adm_t:
                out.append(Finding(
                    detector="D-23", code="OUTCOME_SUBSTITUTION", verdict=INCONSISTENT,
                    severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=(f"extracted {used} is not among the source's admissible "
                             f"tuples"),
                    evidence={"used": list(used), "admissible": [list(a) for a in adm_t]}))
            elif len(adm_t) > 1 and not g(r, "selection_stated", False):
                out.append(Finding(
                    detector="D-23", code="UNJUSTIFIED_SELECTION", verdict=CHOICE,
                    severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=(f"{len(adm_t)} admissible values existed; the review does "
                             "not state which was chosen"),
                    evidence={"multiplicity": len(adm_t), "used": list(used)}))
        for declared, got, nm in ((d_out, g(r, "outcome"), "outcome"),
                                  (d_tp, g(r, "timepoint"), "timepoint"),
                                  (d_sc, g(r, "scale"), "scale")):
            if declared is not MISSING and got is not MISSING and declared != got:
                out.append(Finding(
                    detector="D-23", code="DECLARED_FIELD_MISMATCH",
                    verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                    pool_id=g(pool, "pool_id"),
                    message=f"pool declares {nm}={declared!r} but row uses {got!r}",
                    evidence={"field": nm, "declared": declared, "used": got}))
    if mult:
        out.append(Finding(
            detector="D-23", code="MULTIPLICITY_PROFILE", verdict=CHOICE,
            severity=SEV_INFO, pool_id=g(pool, "pool_id"),
            message=f"admissible-value counts: {mult}",
            evidence={"counts": mult, "max": max(mult),
                      "rows_with_multiplicity": sum(1 for m in mult if m > 1)}))
    return out


@register(
    id="D-24", name="Companion-publication and multiple-report linkage", tier=2,
    network=False, requires=("rows",),
    catches="two included references that are reports of one trial, scored on shared "
            "registry id, author overlap, institution, recruitment period and title; "
            "monotone N sequences from one group over time (von Elm 3A/3B)",
    misses="companion reports with no shared metadata at all",
    fp_behaviour="Must tolerate title rewording 24%, author add/remove 38%, author "
                 "reorder 34% and changed N 31% (Bhandari 2005), and 64% differing "
                 "authorship (von Elm), so exact title or author-set matching is "
                 "forbidden. Methods-section text is excluded from any textual score "
                 "because Roig 2005 showed most reuse is confined there.",
    fn_behaviour="Recall is near-saturated in this space; the whole gain is precision "
                 "(Errami 2010: 50.3% -> 78.9%), so this is a candidate generator.",
)
def d24(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    rows = g(pool, "rows", [])
    for r in rows:
        ctx.touch()
    thr = float(g(pool, "linkage_threshold", 0.55))
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if g(a, "citation_id") == g(b, "citation_id"):
                continue
            parts = {}
            nct_a, nct_b = g(a, "nct"), g(b, "nct")
            parts["registry"] = 1.0 if (nct_a is not MISSING and nct_a == nct_b) else 0.0
            au_a = set(map(str.lower, g(a, "authors", []) or []))
            au_b = set(map(str.lower, g(b, "authors", []) or []))
            parts["authors"] = jaccard(au_a, au_b) if (au_a or au_b) else 0.0
            parts["institution"] = 1.0 if (g(a, "institution") is not MISSING and
                                           g(a, "institution") == g(b, "institution")) else 0.0
            ra, rb = g(a, "recruit_period"), g(b, "recruit_period")
            parts["period"] = 1.0 if (ra is not MISSING and ra == rb) else 0.0
            ta = set(re.findall(r"[a-z]{4,}", str(g(a, "title", "")).lower()))
            tb = set(re.findall(r"[a-z]{4,}", str(g(b, "title", "")).lower()))
            parts["title"] = jaccard(ta, tb) if (ta or tb) else 0.0
            score = (0.45 * parts["registry"] + 0.20 * parts["authors"] +
                     0.10 * parts["institution"] + 0.10 * parts["period"] +
                     0.15 * parts["title"])
            if score >= thr:
                out.append(Finding(
                    detector="D-24", code="CANDIDATE_SAME_STUDY", verdict=SUSPECT,
                    severity=SEV_MED, pool_id=g(pool, "pool_id"),
                    message=(f"{g(a,'row_id')} and {g(b,'row_id')} score {score:.2f} "
                             "as reports of one study"),
                    evidence={"score": round(score, 3), "components":
                              {k: round(v, 3) for k, v in parts.items()},
                              "rows": [g(a, "row_id"), g(b, "row_id")],
                              "threshold": thr}))
    groups: dict[tuple, list] = defaultdict(list)
    for r in rows:
        au, inst = g(r, "first_author"), g(r, "institution")
        if au is not MISSING and inst is not MISSING and g(r, "year") is not MISSING:
            groups[(str(au).lower(), str(inst).lower())].append(r)
    for key, rs in sorted(groups.items()):
        if len(rs) < 3:
            continue
        rs = sorted(rs, key=lambda x: int(g(x, "year")))
        ns = [float(g(x, "n_t", 0)) + float(g(x, "n_c", 0)) for x in rs]
        if all(ns) and (all(ns[i] < ns[i + 1] for i in range(len(ns) - 1)) or
                        all(ns[i] > ns[i + 1] for i in range(len(ns) - 1))):
            outs = {g(x, "outcome") for x in rs}
            if len(outs) == 1:
                out.append(Finding(
                    detector="D-24", code="NESTED_REPORT_SEQUENCE", verdict=SUSPECT,
                    severity=SEV_MED, pool_id=g(pool, "pool_id"),
                    message=("monotone N sequence with identical outcomes from one "
                             "author-institution group (von Elm pattern 3A/3B)"),
                    evidence={"group": list(key), "ns": ns,
                              "rows": [g(x, "row_id") for x in rs],
                              "largest_n_row": g(rs[ns.index(max(ns))], "row_id")}))
    return out


@register(
    id="D-25", name="Adjusted-vs-unadjusted and effect-measure homogeneity", tier=2,
    network=False, requires=("rows",),
    catches="a pool mixing RR with OR with HR; a pool mixing adjusted with unadjusted "
            "estimates; rows whose adjustment status is unstated",
    misses="incompatible estimands that share a measure label, e.g. time-to-event vs "
           "binary-at-fixed-timepoint both entered as RR",
    fp_behaviour="UNVERIFIABLE_ADJUSTMENT will dominate: Cheurfa 2024 found the status "
                 "unspecified in 108/132 (82%). It is therefore reported as a "
                 "transparency metric, not an alarm.",
    fn_behaviour="Cannot see estimand mismatch inside one measure type.",
)
def d25(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    measures, adj = set(), set()
    n_unstated = 0
    rows = g(pool, "rows", [])
    for r in rows:
        ctx.touch()
        m = g(r, "measure")
        if m is not MISSING:
            measures.add(str(m).upper())
        a = g(r, "adjusted")
        if a is MISSING:
            n_unstated += 1
        else:
            adj.add(bool(a))
    ratio_present = measures & RATIO_MEASURES
    if len(ratio_present) > 1:
        out.append(Finding(
            detector="D-25", code="MEASURE_MIXING", verdict=INCONSISTENT,
            severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
            message=f"pool mixes ratio measures {sorted(ratio_present)}",
            evidence={"measures": sorted(measures)}))
    if len(adj) > 1:
        out.append(Finding(
            detector="D-25", code="ADJUSTMENT_MIXING", verdict=INCONSISTENT,
            severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
            message="pool mixes adjusted and unadjusted estimates",
            evidence={"adjusted_values": sorted(map(str, adj))}))
    if n_unstated and rows:
        out.append(Finding(
            detector="D-25", code="UNVERIFIABLE_ADJUSTMENT", verdict=UNVERIFIABLE,
            severity=SEV_INFO, pool_id=g(pool, "pool_id"),
            message=f"{n_unstated}/{len(rows)} rows do not state adjustment status",
            evidence={"unstated": n_unstated, "rows": len(rows)}))
    return out


@register(
    id="D-26", name="Protocol specificity linter", tier=2, network=False,
    requires=("protocol",),
    catches="a protocol that fails to pre-specify scale hierarchy, timepoint, "
            "change-vs-post, control-group hierarchy, effect measure, or model plus "
            "estimator plus software version",
    misses="a protocol that names an item but specifies it uselessly",
    fp_behaviour="None. It is a presence check on our own document. Tendal's baseline "
                 "was 0/10 protocols specifying a scale hierarchy and 0/10 a "
                 "control-group hierarchy -- item 4 is the one that would have "
                 "prevented our benazepril finding.",
    fn_behaviour="Cannot judge quality of specification, only presence.",
)
def d26(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    ctx.touch(len(g(pool, "rows", [])) or 1)
    proto = g(pool, "protocol")
    items = ("scale_hierarchy", "timepoint", "change_vs_post",
             "control_group_hierarchy", "effect_measure", "model_estimator_version")
    if proto is MISSING or not isinstance(proto, dict):
        out.append(unverifiable("D-26", "NO_PROTOCOL", "no protocol supplied",
                                missing=["protocol"], pool_id=g(pool, "pool_id")))
        return out
    absent = [i for i in items if not proto.get(i)]
    for i in absent:
        sev = SEV_HIGH if i in ("control_group_hierarchy",
                                "model_estimator_version") else SEV_MED
        out.append(Finding(
            detector="D-26", code="PROTOCOL_ITEM_ABSENT", verdict=INCONSISTENT,
            severity=sev, pool_id=g(pool, "pool_id"),
            message=f"protocol does not pre-specify {i}",
            evidence={"item": i, "present": sorted(set(items) - set(absent))}))
    out.append(Finding(
        detector="D-26", code="PROTOCOL_SCORE", verdict=CHOICE, severity=SEV_INFO,
        pool_id=g(pool, "pool_id"),
        message=f"protocol specifies {len(items)-len(absent)}/{len(items)} items",
        evidence={"score": len(items) - len(absent), "of": len(items),
                  "absent": absent}))
    return out


# ==========================================================================
# TIER 3 -- external data, supplied by another lane; no I/O performed here
# ==========================================================================

@register(
    id="D-27", name="Retraction / erratum / EoC screen (consumes sibling lane)",
    tier=3, network=True, requires=("external.retraction_lane",),
    catches="an included trial that is retracted, corrected, or under an expression of "
            "concern, and the delta to the pool from removing it",
    misses="integrity problems that never resulted in a notice",
    fp_behaviour="Near zero for existence. The judgement is what to do about it. "
                 "Calibration from VITALITY Study I: removing retracted trials changed "
                 "direction in 8.4% (95% CI 6.8-10.1) and significance in 16.0% "
                 "(14.2-17.9) of 3,902 meta-analyses.",
    fn_behaviour="Entirely dependent on the sibling lane's coverage. If the lane "
                 "reports no data for a trial this emits UNVERIFIABLE, never a pass. "
                 "THIS DETECTOR PERFORMS NO LOOKUPS -- the retraction lane is the "
                 "single writer and this consumes its output.",
)
def d27(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    lane = (g(pool, "external", {}) or {}).get("retraction_lane")
    if lane is None:
        out.append(unverifiable(
            "D-27", "LANE_NOT_SUPPLIED",
            "retraction lane output absent; status of every trial is unknown",
            missing=["external.retraction_lane"], pool_id=g(pool, "pool_id")))
        ctx.touch(len(g(pool, "rows", [])) or 1)
        return out
    keep_e, keep_s = [], []
    flagged = []
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        cid = str(g(r, "citation_id", rid))
        rec = lane.get(cid)
        if rec is None:
            out.append(unverifiable(
                "D-27", "NO_LANE_RECORD",
                f"retraction lane has no record for {cid}",
                missing=[f"retraction_lane[{cid}]"], row_id=rid,
                pool_id=g(pool, "pool_id")))
            continue
        status = str(rec.get("status", "unknown")).lower()
        if status in ("retracted", "expression_of_concern", "erratum"):
            flagged.append(rid)
            out.append(Finding(
                detector="D-27", code=f"NOTICE_{status.upper()}",
                verdict=INCONSISTENT if status == "retracted" else SUSPECT,
                severity=SEV_HIGH if status == "retracted" else SEV_MED,
                row_id=rid, pool_id=g(pool, "pool_id"),
                message=f"{cid} carries a {status} notice (source: {rec.get('source')})",
                evidence={"citation_id": cid, **rec}))
        else:
            e, s = g(r, "effect"), g(r, "se")
            if e is not MISSING and s is not MISSING and float(s) > 0:
                keep_e.append(float(e)); keep_s.append(float(s))
    if flagged and len(keep_e) >= 2 and g(pool, "pooled_estimate") is not MISSING:
        est, se, _, _ = dersimonian_laird(keep_e, keep_s)
        z = norm_ppf(0.975)
        rep = float(g(pool, "pooled_estimate"))
        null = float(g(pool, "null_value", 0.0))
        lo_n, hi_n = est - z * se, est + z * se
        crosses_after = lo_n <= null <= hi_n
        rep_lo, rep_hi = g(pool, "pooled_ci_lo"), g(pool, "pooled_ci_hi")
        crosses_before = (float(rep_lo) <= null <= float(rep_hi)) \
            if MISSING not in (rep_lo, rep_hi) else None
        out.append(Finding(
            detector="D-27", code="RETRACTION_REMOVAL_DELTA", verdict=SUSPECT,
            severity=SEV_HIGH, pool_id=g(pool, "pool_id"),
            message=(f"removing {len(flagged)} flagged trial(s): {rep:.4g} -> "
                     f"{est:.4g}"),
            evidence={"removed_rows": flagged, "before": rep, "after": round(est, 6),
                      "after_ci": [round(lo_n, 6), round(hi_n, 6)],
                      "significance_changed": (crosses_before is not None and
                                               crosses_before != crosses_after),
                      "direction_changed": math.copysign(1, rep - null) !=
                                           math.copysign(1, est - null),
                      "magnitude_change_pct": round(
                          abs(est - rep) / abs(rep) * 100, 2) if rep else None}))
    return out


@register(
    id="D-28", name="Registry id resolution, neighbour recovery, cross-registry",
    tier=3, network=True, requires=("rows",),
    catches="an identifier that does not resolve; a single-digit typo recoverable to a "
            "unique real record; another registry's identifier mislabelled as an NCT; "
            "identifiers that disagree between abstract, full text and databank field",
    misses="a wrong identifier that resolves -- that is D-02's job, and the two are "
           "deliberately complementary",
    fp_behaviour="Low. Carlisle 2020 audited 22 non-resolving NCTs: all 22 had a "
                 "findable true record, 17/22 (77%) differed by a single digit, 2/22 "
                 "were other registries'. Neighbour recovery requires EXACTLY ONE "
                 "resolving candidate plus a condition/intervention match, so ambiguous "
                 "recoveries are reported, never applied.",
    fn_behaviour="Extends the existing name<->NCT bijection test rather than repeating "
                 "it: the bijection assumes both sides are well-formed and present; "
                 "this supplies existence, correction proposals, cross-registry "
                 "disambiguation and intra-document consistency upstream of it.",
)
def d28(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    resolver = (g(pool, "external", {}) or {}).get("registry_snapshot")
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        locs = {k: str(g(r, k, "")) for k in
                ("text_abstract", "text_fulltext", "databank_field")
                if g(r, k) is not MISSING}
        found = {k: set(NCT_RE.findall(v)) for k, v in locs.items()}
        allnct = set().union(*found.values()) if found else set()
        declared = g(r, "nct")
        if declared is not MISSING:
            allnct.add(str(declared))
        if resolver is None:
            out.append(unverifiable(
                "D-28", "NO_REGISTRY_SNAPSHOT",
                "no cached registry snapshot; resolution cannot be tested",
                missing=["external.registry_snapshot"], row_id=rid,
                pool_id=g(pool, "pool_id")))
        else:
            for nct in sorted(allnct):
                if nct in resolver:
                    continue
                cands = []
                for pos in range(3, 11):
                    for dig in "0123456789":
                        alt = nct[:pos] + dig + nct[pos + 1:]
                        if alt != nct and alt in resolver:
                            cands.append(alt)
                cands = sorted(set(cands))
                if len(cands) == 1:
                    out.append(Finding(
                        detector="D-28", code="SUGGESTED_CORRECTION",
                        verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                        pool_id=g(pool, "pool_id"),
                        message=f"{nct} does not resolve; {cands[0]} does (1 digit)",
                        evidence={"bad": nct, "candidate": cands[0]}))
                elif cands:
                    out.append(Finding(
                        detector="D-28", code="AMBIGUOUS_CORRECTION", verdict=SUSPECT,
                        severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                        message=f"{nct} does not resolve; {len(cands)} candidates",
                        evidence={"bad": nct, "candidates": cands}))
                else:
                    out.append(Finding(
                        detector="D-28", code="NCT_DOES_NOT_RESOLVE",
                        verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                        pool_id=g(pool, "pool_id"),
                        message=f"{nct} corresponds to no registry entry",
                        evidence={"bad": nct}))
        for reg, rx in OTHER_REGISTRY_RE.items():
            for tok in rx.findall(" ".join(locs.values())):
                if g(r, "registry_label", "NCT") == "NCT":
                    out.append(Finding(
                        detector="D-28", code="REGISTRY_FORMAT_MISASSIGNMENT",
                        verdict=SUSPECT, severity=SEV_MED, row_id=rid,
                        pool_id=g(pool, "pool_id"),
                        message=f"{reg}-format identifier {tok} labelled as NCT",
                        evidence={"registry": reg, "token": tok}))
        nonempty = {k: v for k, v in found.items() if v}
        if len(nonempty) > 1 and len({frozenset(v) for v in nonempty.values()}) > 1:
            out.append(Finding(
                detector="D-28", code="INTRA_DOCUMENT_ID_INCONSISTENCY",
                verdict=INCONSISTENT, severity=SEV_MED, row_id=rid,
                pool_id=g(pool, "pool_id"),
                message="identifiers disagree across abstract / full text / databank",
                evidence={k: sorted(v) for k, v in nonempty.items()}))
    return out


@register(
    id="D-29", name="Registry field diff", tier=3, network=True,
    requires=("external.registry_records",),
    catches="field-level disagreement between registry and publication on enrolment, "
            "primary outcome description and value, SAE and death counts, completion "
            "status; retrospective registration; undeclared outcomes",
    misses="agreement that is agreement on the wrong trial -- again D-02's job",
    fp_behaviour="High background rate, so these are METRICS not alarms. Hartung 2014 "
                 "(n=110): secondary-outcome count inconsistent 80%, primary outcome "
                 "description 15%, value 20%. Kosa 2017 (n=200): 13%. Goldacre 2019 "
                 "(n=67): mean 5.4 undeclared outcomes per trial.",
    fn_behaviour="Silent without a pinned registry version; the version is recorded in "
                 "evidence or the comparison is declared irreproducible.",
)
def d29(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    recs = (g(pool, "external", {}) or {}).get("registry_records")
    if recs is None:
        out.append(unverifiable("D-29", "NO_REGISTRY_RECORDS",
                                "registry records not supplied",
                                missing=["external.registry_records"],
                                pool_id=g(pool, "pool_id")))
        ctx.touch(len(g(pool, "rows", [])) or 1)
        return out
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        nct = g(r, "nct")
        rec = recs.get(str(nct)) if nct is not MISSING else None
        if rec is None:
            out.append(unverifiable("D-29", "NO_RECORD_FOR_ROW",
                                    f"no registry record for {nct}",
                                    missing=["registry_records[nct]"], row_id=rid,
                                    pool_id=g(pool, "pool_id")))
            continue
        ver = rec.get("version") or rec.get("retrieved_at")
        if not ver:
            out.append(Finding(
                detector="D-29", code="REGISTRY_VERSION_UNPINNED", verdict=UNVERIFIABLE,
                severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                message="registry record has no version or timestamp; not reproducible",
                evidence={"nct": str(nct)}))
        for fld, pubkey in (("enrolment", "pub_reported_n"),
                            ("primary_outcome", "outcome"),
                            ("sae_count", "pub_sae"),
                            ("death_count", "pub_deaths")):
            rv, pv = rec.get(fld), g(r, pubkey)
            if rv is None or pv is MISSING:
                continue
            if rv != pv:
                extra = {}
                if fld == "sae_count":
                    extra["registry_higher"] = float(rv) > float(pv)
                out.append(Finding(
                    detector="D-29", code="REGISTRY_FIELD_DISCORDANCE", verdict=SUSPECT,
                    severity=SEV_MED if fld != "primary_outcome" else SEV_HIGH,
                    row_id=rid, pool_id=g(pool, "pool_id"),
                    message=f"{fld}: registry {rv!r} vs publication {pv!r}",
                    evidence={"field": fld, "registry": rv, "publication": pv,
                              "version": ver, **extra}))
        reg_d, enrol_d = rec.get("registration_date"), rec.get("first_enrolment_date")
        if reg_d and enrol_d and reg_d > _plus_days(enrol_d, 60):
            out.append(Finding(
                detector="D-29", code="RETROSPECTIVE_REGISTRATION", verdict=SUSPECT,
                severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                message=f"registered {reg_d} after first enrolment {enrol_d} + 60d",
                evidence={"registration_date": reg_d,
                          "first_enrolment_date": enrol_d}))
        reg_out = set(rec.get("registered_outcomes") or [])
        pub_out = set(g(r, "published_outcomes", []) or [])
        extra_out = pub_out - reg_out
        if reg_out and extra_out:
            out.append(Finding(
                detector="D-29", code="UNDECLARED_OUTCOMES", verdict=SUSPECT,
                severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                message=f"{len(extra_out)} published outcomes were not registered",
                evidence={"count": len(extra_out), "outcomes": sorted(extra_out)}))
    return out


def _plus_days(iso: str, days: int) -> str:
    from datetime import date, timedelta
    y, m, d = (int(x) for x in iso.split("-"))
    return (date(y, m, d) + timedelta(days=days)).isoformat()


@register(
    id="D-30", name="Registry link recovery where no identifier exists", tier=3,
    network=True, requires=("external.link_candidates",),
    catches="a publication for a registration that carries no machine-resolvable link",
    misses="registrations whose publication is not in the candidate corpus",
    fp_behaviour="BY DESIGN this returns up to 50 candidates per registration, most of "
                 "them wrong. It is a recall tool feeding human adjudication, never a "
                 "flag. Dunn 2017: median rank 2, first for 40%, top-50 recovers 86% "
                 "of unreported links.",
    fn_behaviour="Never infer non-publication from a missing link: NPV of 'no linked "
                 "publication' is 56% (Huser & Cimino 2012) and 72.2% of completed "
                 "trials carry no structured link at all.",
)
def d30(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    cands = (g(pool, "external", {}) or {}).get("link_candidates")
    if cands is None:
        out.append(unverifiable("D-30", "NO_CANDIDATES", "no candidate corpus supplied",
                                missing=["external.link_candidates"],
                                pool_id=g(pool, "pool_id")))
        ctx.touch(len(g(pool, "rows", [])) or 1)
        return out
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        if g(r, "nct") is not MISSING:
            continue
        terms = set(re.findall(r"[a-z]{4,}", str(g(r, "title", "")).lower()))
        scored = []
        for cid, meta in cands.items():
            ct = set(re.findall(r"[a-z]{4,}", str(meta.get("title", "")).lower()))
            scored.append((jaccard(terms, ct), cid))
        scored.sort(reverse=True)
        top = scored[:50]
        out.append(Finding(
            detector="D-30", code="LINK_CANDIDATES", verdict=UNVERIFIABLE,
            severity=SEV_INFO, row_id=rid, pool_id=g(pool, "pool_id"),
            message=f"{len(top)} ranked candidates for manual adjudication",
            evidence={"top5": [{"id": c, "score": round(s, 3)} for s, c in top[:5]],
                      "screened": len(top)}))
    return out


@register(
    id="D-31", name="Sample-size cross-check against an external index", tier=3,
    network=True, requires=("external.index_sample_sizes",),
    catches="a review-reported N that disagrees with an independent large-scale "
            "extraction of the same trial's N",
    misses="errors replicated in the external index",
    fp_behaviour="Bounded by the external index's own extraction accuracy, which "
                 "Trialstreamer does not report per-field. Disagreement is therefore a "
                 "prompt to check, never evidence of review error. Feeds D-02.",
    fn_behaviour="Only covers trials present in the index (673,191 RCT publications as "
                 "of June 2020).",
)
def d31(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    idx = (g(pool, "external", {}) or {}).get("index_sample_sizes")
    if idx is None:
        out.append(unverifiable("D-31", "NO_INDEX", "external index not supplied",
                                missing=["external.index_sample_sizes"],
                                pool_id=g(pool, "pool_id")))
        ctx.touch(len(g(pool, "rows", [])) or 1)
        return out
    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        cid = str(g(r, "citation_id", rid))
        ext = idx.get(cid)
        rep = g(r, "reported_n")
        if ext is None or rep is MISSING:
            out.append(unverifiable("D-31", "NO_INDEX_ENTRY",
                                    f"no indexed N for {cid}",
                                    missing=["index_sample_sizes[cid]", "reported_n"],
                                    row_id=rid, pool_id=g(pool, "pool_id")))
            continue
        if float(rep) <= 0:
            continue
        d = abs(float(ext) - float(rep)) / float(rep)
        if d > 0.05:
            out.append(Finding(
                detector="D-31", code="INDEX_N_DISAGREEMENT", verdict=SUSPECT,
                severity=SEV_MED, row_id=rid, pool_id=g(pool, "pool_id"),
                message=f"review N {rep} vs indexed N {ext} ({d*100:.1f}% apart)",
                evidence={"reported_n": float(rep), "indexed_n": float(ext),
                          "relative_difference": round(d, 4)}))
    return out


@register(
    id="D-32", name="Erratum-impact screen (consumes sibling lane)", tier=3,
    network=True, requires=("external.erratum_lane",),
    catches="an erratum or correction notice that touches a cell we actually store, "
            "i.e. one that changes a number already in the extracted table",
    misses="errata whose scope is not machine-readable and which nobody has read; "
           "corrections issued only in a subsequent paper rather than as a notice",
    fp_behaviour="An erratum touching only authorship, affiliation, funding or a "
                 "typographical fix in prose has no effect on the pool and is emitted "
                 "as CHOICE, not a flag. The expensive class is the middle one: an "
                 "erratum exists but its scope is unknown, which is UNVERIFIABLE and "
                 "must be read by a human -- never silently treated as harmless.",
    fn_behaviour="Entirely dependent on the erratum lane's field-level scope "
                 "extraction. If the lane supplies only 'an erratum exists', every "
                 "artefact degrades to UNVERIFIABLE_ERRATUM_SCOPE, which is the "
                 "correct and expensive answer. PERFORMS NO LOOKUPS: the sibling "
                 "lane is the single writer.",
)
def d32(pool: dict, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    lane = (g(pool, "external", {}) or {}).get("erratum_lane")
    if lane is None:
        out.append(unverifiable(
            "D-32", "ERRATUM_LANE_NOT_SUPPLIED",
            "erratum lane output absent; correction status of every artefact unknown",
            missing=["external.erratum_lane"], pool_id=g(pool, "pool_id")))
        ctx.touch(len(g(pool, "rows", [])) or 1)
        return out

    # cells that, if corrected, change the pooled result
    STORED = {"n_t", "n_c", "e_t", "e_c", "mean_t", "mean_c", "sd_t", "sd_c",
              "effect", "se", "ci_lo", "ci_hi", "reported_n", "trial_true_n",
              "reported_events", "weight", "outcome", "timepoint"}
    # tokens in erratum prose that imply a numeric correction
    NUMERIC_HINTS = ("table", "figure", "should read", "incorrect", "corrected",
                     "erroneous", "reversed", "transposed", "denominator",
                     "numerator", "standard deviation", "standard error",
                     "confidence interval", "sample size", "number of patients",
                     "hazard ratio", "odds ratio", "risk ratio", "mean")
    INERT_ONLY = {"author", "authors", "affiliation", "affiliations", "funding",
                  "conflict_of_interest", "acknowledgements", "orcid", "title",
                  "spelling", "reference_list"}

    for r in g(pool, "rows", []):
        ctx.touch()
        rid = g(r, "row_id", "?")
        cid = str(g(r, "citation_id", rid))
        rec = lane.get(cid)
        if rec is None:
            out.append(unverifiable(
                "D-32", "NO_ERRATUM_RECORD",
                f"erratum lane has no record for {cid}",
                missing=[f"erratum_lane[{cid}]"], row_id=rid,
                pool_id=g(pool, "pool_id")))
            continue
        if not rec.get("has_erratum"):
            continue

        # which cells does THIS row actually populate?
        populated = {k for k in STORED if g(r, k) is not MISSING}
        touched = set(rec.get("fields_touched") or [])
        text = str(rec.get("erratum_text", "")).lower()

        if touched:
            hits = sorted(touched & populated)
            inert = touched and touched.issubset(INERT_ONLY)
            if hits:
                out.append(Finding(
                    detector="D-32", code="ERRATUM_TOUCHES_STORED_CELL",
                    verdict=INCONSISTENT, severity=SEV_HIGH, row_id=rid,
                    pool_id=g(pool, "pool_id"),
                    message=(f"erratum {rec.get('erratum_pmid','?')} corrects "
                             f"{hits}, which this row stores; re-extraction required"),
                    evidence={"citation_id": cid, "cells_affected": hits,
                              "fields_touched": sorted(touched),
                              "erratum_pmid": rec.get("erratum_pmid"),
                              "populated_cells": sorted(populated)}))
            elif inert:
                out.append(Finding(
                    detector="D-32", code="ERRATUM_INERT", verdict=CHOICE,
                    severity=SEV_INFO, row_id=rid, pool_id=g(pool, "pool_id"),
                    message="erratum touches only non-data fields; pool unaffected",
                    evidence={"citation_id": cid, "fields_touched": sorted(touched)}))
            else:
                out.append(Finding(
                    detector="D-32", code="ERRATUM_OFF_TARGET", verdict=SUSPECT,
                    severity=SEV_LOW, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=("erratum corrects data fields this row does not store; "
                             "check whether the row should store them"),
                    evidence={"citation_id": cid, "fields_touched": sorted(touched),
                              "populated_cells": sorted(populated)}))
        elif text:
            hints = sorted(h for h in NUMERIC_HINTS if h in text)
            if hints:
                out.append(Finding(
                    detector="D-32", code="ERRATUM_LIKELY_NUMERIC", verdict=SUSPECT,
                    severity=SEV_HIGH, row_id=rid, pool_id=g(pool, "pool_id"),
                    message=(f"erratum scope not structured, but its text implies a "
                             f"numeric correction: {hints[:5]}"),
                    evidence={"citation_id": cid, "hints": hints,
                              "erratum_pmid": rec.get("erratum_pmid")}))
            else:
                out.append(Finding(
                    detector="D-32", code="UNVERIFIABLE_ERRATUM_SCOPE",
                    verdict=UNVERIFIABLE, severity=SEV_MED, row_id=rid,
                    pool_id=g(pool, "pool_id"),
                    message="erratum exists; scope not determinable, must be read",
                    evidence={"citation_id": cid,
                              "erratum_pmid": rec.get("erratum_pmid"),
                              "missing_fields": ["fields_touched"]}))
        else:
            out.append(Finding(
                detector="D-32", code="UNVERIFIABLE_ERRATUM_SCOPE",
                verdict=UNVERIFIABLE, severity=SEV_MED, row_id=rid,
                pool_id=g(pool, "pool_id"),
                message=("erratum exists with neither structured scope nor text; "
                         "this is the expensive class and must not be treated as "
                         "harmless"),
                evidence={"citation_id": cid,
                          "erratum_pmid": rec.get("erratum_pmid"),
                          "missing_fields": ["fields_touched", "erratum_text"]}))
    return out
