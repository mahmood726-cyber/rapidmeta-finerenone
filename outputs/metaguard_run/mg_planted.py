"""
mg_planted.py -- plant a known defect into REAL corpus rows and check it fires.

WHY REAL ROWS AND NOT FIXTURES. A fixture is a row I wrote to be caught. It
proves the detector's logic is reachable in principle. It does not prove the
detector is reachable on data shaped the way the corpus is actually shaped --
different field names, different units, missing columns, string-typed numbers,
cluster designs the fixture never contemplated. Every one of the five dead
guards found today would have passed a fixture test. So: take a real row that
the corpus actually contains, break it in one specific way, and require the
detector to notice.

The output feeds mg_corpus.py --planted, which uses it to separate
SILENT_COVERED from SILENT_DEAD.

Three outcomes per detector:
  fires = True    the planted defect was caught on real corpus data
  fires = False   NOT caught -- the detector is dead on this corpus even if the
                  fixture suite is green. This is the finding.
  fires = None    could not plant: the corpus never supplies the fields this
                  defect needs. Reported as NOT_PLANTABLE with the missing
                  fields named, which is an extraction-coverage gap, not a pass.

Run:
  python3 mg_planted.py corpus.ndjson --out mg_planted_report.json
"""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys

from mg_core import (
    INCONSISTENT, MISSING, SUSPECT, all_detectors, g, get_detector, run_detector,
)
import mg_detectors  # noqa: F401
from mg_corpus import load_corpus

ACTIONABLE = (INCONSISTENT, SUSPECT)


def _find_row(pool, *fields):
    """First real row carrying every named field."""
    for r in g(pool, "rows", []) or []:
        if all(g(r, f) is not MISSING for f in fields):
            return r
    return None


# --------------------------------------------------------------------------
# Injectors. Each returns (mutated_pool, expected_code) or (None, missing_fields)
# Each must make the SMALLEST realistic change that should trigger the detector.
# --------------------------------------------------------------------------

def inj_d01(pool):
    r = _find_row(pool, "trial_key", "first_author")
    if r is None:
        return None, ["trial_key", "first_author"]
    p = copy.deepcopy(pool)
    src = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    clone = copy.deepcopy(src)
    clone["row_id"] = str(src.get("row_id", "x")) + "__planted"
    clone["citation_id"] = str(src.get("citation_id", "c")) + "__planted"
    clone["trial_key"] = str(src["trial_key"]) + "_ALT"   # same trial, second key
    p["rows"].append(clone)
    return p, "CANDIDATE_KEY_COLLISION"


def inj_d02(pool):
    r = _find_row(pool, "reported_n")
    if r is None:
        return None, ["reported_n"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["registry_enrolment"] = float(t["reported_n"]) * 10.0   # the 16124/1617 shape
    t.pop("is_declared_substudy", None)
    return p, "IDENTITY_MISMATCH_SUSPECTED"


def inj_d03(pool):
    r = _find_row(pool, "e_t", "n_t", "e_c", "n_c")
    if r is None:
        return None, ["e_t", "n_t", "e_c", "n_c"]
    p = copy.deepcopy(pool)
    src = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    clone = copy.deepcopy(src)
    clone["row_id"] = str(src.get("row_id", "x")) + "__planted"
    clone["citation_id"] = str(src.get("citation_id", "c")) + "__planted"
    p["rows"].append(clone)
    return p, "DUPLICATE_DATA_CANDIDATE"


def inj_d04(pool):
    r = _find_row(pool, "trial_key", "n_t", "n_c", "trial_true_n")
    if r is None:
        r = _find_row(pool, "trial_key", "n_t", "n_c", "registry_enrolment")
        if r is None:
            return None, ["trial_key", "n_t", "n_c", "trial_true_n|registry_enrolment"]
    p = copy.deepcopy(pool)
    src = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    clone = copy.deepcopy(src)
    clone["row_id"] = str(src.get("row_id", "x")) + "__planted"
    clone["citation_id"] = str(src.get("citation_id", "c")) + "__planted"
    clone.pop("subgroup_exclusive", None)
    clone["arm_label"] = src.get("arm_label", "A")
    p["rows"].append(clone)
    return p, "N_INFLATION"


def inj_d05(pool):
    rows = [r for r in (g(pool, "rows", []) or [])
            if g(r, "effect") is not MISSING and g(r, "se") is not MISSING]
    if len(rows) < 5:
        return None, ["effect", "se (needs >=5 rows)"]
    p = copy.deepcopy(pool)
    keep = [r for r in p["rows"]
            if g(r, "effect") is not MISSING and g(r, "se") is not MISSING]
    target = float(keep[0]["effect"])
    for r in keep:
        r["effect"] = target                    # collapse heterogeneity to zero
        r["randomisation"] = "simple"           # clear the design gate
    p["rows"] = keep
    p["_prior_duplication_flags"] = ["PLANTED:N_INFLATION"]
    p["mc_iters"] = 4000
    return p, "DUPLICATION_SIGNATURE"


def inj_d06(pool):
    r = _find_row(pool, "mean_t", "sd_t", "n_t", "mean_c", "sd_c", "n_c")
    if r is None:
        return None, ["mean_t", "sd_t", "n_t", "mean_c", "sd_c", "n_c"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    n = int(t["n_t"])
    # divide the SD by sqrt(n): exactly the SE-reported-as-SD substitution
    t["sd_t"] = float(t["sd_t"]) / (n ** 0.5)
    t["sd_c"] = float(t["sd_c"]) / (int(t["n_c"]) ** 0.5)
    return p, "SE_AS_SD_SUSPECTED"


def inj_d07(pool):
    r = _find_row(pool, "n_t", "n_c")
    if r is None:
        return None, ["n_t", "n_c"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["measure"] = "HR"
    t["effect"], t["ci_lo"], t["ci_hi"] = 1.06, 1.02, 1.10   # implies ~10,781 events
    t.pop("hr_indirect_from_km", None)
    return p, "HR_LABEL_IMPLAUSIBLE"


def inj_d08(pool):
    r = _find_row(pool, "ci_lo", "ci_hi", "se")
    if r is None:
        return None, ["ci_lo", "ci_hi", "se"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    lo, hi = float(t["ci_lo"]), float(t["ci_hi"])
    if str(t.get("measure", "")).upper() in ("RR", "OR", "HR"):
        import math
        lo, hi = math.log(lo), math.log(hi)
    t["se"] = (hi - lo) / 3.29          # a 90% interval used as if 95%
    t["ci_level"] = 0.95
    return p, "CI_LEVEL_MISMATCH"


def inj_d09(pool):
    r = _find_row(pool, "effect")
    if r is None:
        return None, ["effect"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["measure"] = "OR"
    t["effect"], t["ci_lo"], t["ci_hi"] = 0.50, 0.30, 0.70   # symmetric on ratio scale
    return p, "RAW_SCALE_ENTRY_SUSPECTED"


def inj_d10(pool):
    r = _find_row(pool, "effect", "mean_t", "mean_c")
    if r is not None:
        p = copy.deepcopy(pool)
        t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
        implied = 1.0 if float(t["mean_t"]) > float(t["mean_c"]) else -1.0
        t["effect"] = -abs(float(t["effect"]) or 1.0) * implied   # flip the sign
        if t["effect"] == 0:
            t["effect"] = -implied
        return p, "SIGN_ERROR"

    ratio_measures = {"RR", "OR", "HR", "IRR", "RATE_RATIO"}
    for cand in g(pool, "rows", []) or []:
        if any(g(cand, f) is MISSING for f in ("effect", "e_t", "n_t", "e_c", "n_c")):
            continue
        if str(g(cand, "measure", "")).upper() not in ratio_measures:
            continue
        et, nt, ec, nc = map(float, (g(cand, "e_t"), g(cand, "n_t"),
                                     g(cand, "e_c"), g(cand, "n_c")))
        if min(et, nt, ec, nc) <= 0:
            continue
        cells_ratio = (et / nt) / (ec / nc)
        if cells_ratio <= 0 or abs(cells_ratio - 1.0) < 0.05:
            continue
        p = copy.deepcopy(pool)
        t = next(x for x in p["rows"] if x.get("row_id") == cand.get("row_id"))
        t["effect"] = 1.0 / cells_ratio
        return p, "RECIPROCAL_ENTERED"

    return None, ["effect, mean_t, mean_c OR reciprocal-testable effect/e_t/n_t/e_c/n_c"]


def inj_d11(pool):
    r = _find_row(pool, "e_t", "n_t")
    if r is None:
        return None, ["e_t", "n_t"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["e_t"] = float(t["n_t"]) + 5      # more events than participants
    return p, "EVENTS_EXCEED_N"


def inj_d12(pool):
    r = _find_row(pool, "trial_key", "n_t", "n_c", "outcome")
    if r is None:
        return None, ["trial_key", "n_t", "n_c", "outcome"]
    if float(r["n_t"]) == float(r["n_c"]):
        alt = next((x for x in (g(pool, "rows", []) or [])
                    if g(x, "n_t") is not MISSING and g(x, "n_c") is not MISSING
                    and float(x["n_t"]) != float(x["n_c"])
                    and g(x, "trial_key") is not MISSING), None)
        if alt is None:
            return None, ["a row with n_t != n_c"]
        r = alt
    p = copy.deepcopy(pool)
    src = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    clone = copy.deepcopy(src)
    clone["row_id"] = str(src.get("row_id", "x")) + "__planted"
    clone["citation_id"] = str(src.get("citation_id", "c")) + "__planted"
    clone["n_t"], clone["n_c"] = src["n_c"], src["n_t"]      # transpose the arms
    p["rows"].append(clone)
    return p, "ARM_TRANSPOSITION"


def inj_d13(pool):
    r = _find_row(pool, "trial_key", "n_c", "trial_control_n")
    if r is None:
        return None, ["trial_key", "n_c", "trial_control_n"]
    p = copy.deepcopy(pool)
    src = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    clone = copy.deepcopy(src)
    clone["row_id"] = str(src.get("row_id", "x")) + "__planted"
    clone["citation_id"] = str(src.get("citation_id", "c")) + "__planted"
    clone["n_c"] = src["trial_control_n"]     # whole control arm entered twice
    src["n_c"] = src["trial_control_n"]
    p["rows"].append(clone)
    return p, "SHARED_CONTROL_DOUBLE_COUNT"


def inj_d14(pool):
    r = _find_row(pool, "e_t", "n_t", "e_c", "n_c")
    if r is None:
        return None, ["e_t", "n_t", "e_c", "n_c"]
    from mg_core import log_rr
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["design"] = "cluster"
    t["cluster_m"], t["icc"] = 30, 0.02
    _, naive = log_rr(t["e_t"], t["n_t"], t["e_c"], t["n_c"])
    t["se"] = naive                       # clustering ignored
    return p, "CLUSTERING_IGNORED"


def inj_d15(pool):
    r = _find_row(pool, "row_id")
    if r is None:
        return None, ["row_id"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["design"] = "crossover"
    t["layout"] = "armwise"
    return p, "CROSSOVER_AS_PARALLEL"


def inj_d16(pool):
    if g(pool, "pooled_estimate") is MISSING:
        return None, ["pooled_estimate"]
    rows = [r for r in (g(pool, "rows", []) or [])
            if g(r, "effect") is not MISSING and g(r, "se") is not MISSING]
    if len(rows) < 2:
        return None, ["effect", "se (needs >=2 rows)"]
    p = copy.deepcopy(pool)
    p["pooled_estimate"] = float(p["pooled_estimate"]) * 1.6 + 0.05
    return p, "NOT_REPRODUCIBLE"


def inj_d17(pool):
    rows = [r for r in (g(pool, "rows", []) or [])
            if g(r, "se") is not MISSING]
    if len(rows) < 3:
        return None, ["se (needs >=3 rows)"]
    p = copy.deepcopy(pool)
    for r in p["rows"]:
        if g(r, "se") is not MISSING:
            r["weight"] = 25.0             # equal weights regardless of precision
    p.pop("estimator", None)
    return p, "WEIGHT_INCONSISTENT"


def inj_d18(pool):
    r = _find_row(pool, "row_id")
    if r is None:
        return None, ["row_id"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["conversion"] = {"method": "hozo", "n": 120, "band": "range/4",
                       "min": 2, "max": 40, "median": 12,
                       "uncertainty_inflated": True}
    return p, "HOZO_BAND_VIOLATION"


def inj_d19(pool):
    p = copy.deepcopy(pool)
    base = g(pool, "pooled_estimate", 0.5)
    p["artifacts"] = {"abstract": {"pooled": float(base)},
                      "forest_plot": {"pooled": float(base) * 2.0 + 0.31},
                      "results_text": {"pooled": float(base)}}
    return p, "CROSS_ARTIFACT_MISMATCH"


def inj_d20(pool):
    r = _find_row(pool, "mean_t", "n_t")
    if r is None:
        return None, ["mean_t", "n_t"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    n = int(t["n_t"])
    t["integer_data"], t["items"], t["mean_decimals"] = True, 1, 2
    # pick a value strictly between two attainable multiples of 1/n
    k = max(1, int(float(t["mean_t"]) * n))
    t["mean_t"] = round((k + 0.5) / n, 2)
    if not (abs(round(t["mean_t"] * n) / n - t["mean_t"]) > 0.005):
        t["mean_t"] = round((k + 0.5) / n, 3)
        t["mean_decimals"] = 3
    return p, "GRIM_INCONSISTENT"


def inj_d21(pool):
    r = _find_row(pool, "row_id")
    if r is None:
        return None, ["row_id"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["reported_tests"] = [{"kind": "t", "stat": 1.10, "df": 40, "p": 0.02}]
    return p, "GROSS_INCONSISTENT"


def inj_d22(pool):
    if g(pool, "declared_comparator") is MISSING:
        return None, ["declared_comparator"]
    r = _find_row(pool, "comparator_from_source")
    if r is None:
        return None, ["comparator_from_source"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["comparator_from_source"] = "__planted_other_drug__"
    p.setdefault("drug_dictionary", {})
    p["protocol_declares_class_pooling"] = False
    return p, "COMPARATOR_MISMATCH"


def inj_d23(pool):
    if g(pool, "declared_timepoint") is MISSING:
        return None, ["declared_timepoint"]
    r = _find_row(pool, "timepoint")
    if r is None:
        return None, ["timepoint"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    t["timepoint"] = "__planted_wrong_timepoint__"
    return p, "DECLARED_FIELD_MISMATCH"


def inj_d24(pool):
    r = _find_row(pool, "first_author", "institution", "year", "n_t", "n_c",
                  "outcome")
    if r is None:
        return None, ["first_author", "institution", "year", "n_t", "n_c", "outcome"]
    p = copy.deepcopy(pool)
    src = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    base = float(src["n_t"]) + float(src["n_c"])
    for i, mult in enumerate((1.4, 1.9), start=1):
        clone = copy.deepcopy(src)
        clone["row_id"] = f"{src.get('row_id','x')}__planted{i}"
        clone["citation_id"] = f"{src.get('citation_id','c')}__planted{i}"
        clone["trial_key"] = f"{src.get('trial_key','T')}__planted{i}"
        clone["year"] = int(src["year"]) + i
        clone["n_t"] = base * mult / 2.0
        clone["n_c"] = base * mult / 2.0
        p["rows"].append(clone)
    return p, "NESTED_REPORT_SEQUENCE"


def inj_d25(pool):
    rows = [r for r in (g(pool, "rows", []) or []) if g(r, "measure") is not MISSING]
    if len(rows) < 2:
        return None, ["measure (needs >=2 rows)"]
    p = copy.deepcopy(pool)
    got = [r for r in p["rows"] if g(r, "measure") is not MISSING]
    got[0]["measure"] = "RR"
    got[1]["measure"] = "HR"
    return p, "MEASURE_MIXING"


def inj_d26(pool):
    p = copy.deepcopy(pool)
    p["protocol"] = {"scale_hierarchy": "x", "timepoint": "y",
                     "change_vs_post": "z", "effect_measure": "RR"}
    return p, "PROTOCOL_ITEM_ABSENT"


def inj_d27(pool):
    r = _find_row(pool, "citation_id")
    if r is None:
        return None, ["citation_id"]
    p = copy.deepcopy(pool)
    ext = dict(g(p, "external", {}) or {})
    lane = dict(ext.get("retraction_lane") or {})
    lane[str(r["citation_id"])] = {"status": "retracted",
                                   "source": "planted_positive_control"}
    ext["retraction_lane"] = lane
    p["external"] = ext
    return p, "NOTICE_RETRACTED"


def inj_d28(pool):
    r = _find_row(pool, "nct")
    if r is None:
        return None, ["nct"]
    p = copy.deepcopy(pool)
    ext = dict(g(p, "external", {}) or {})
    snap = dict(ext.get("registry_snapshot") or {})
    real = str(r["nct"])
    snap.setdefault(real, {"title": "planted"})
    ext["registry_snapshot"] = snap
    p["external"] = ext
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    d = real[-1]
    t["nct"] = real[:-1] + ("8" if d != "8" else "7")   # one digit off
    t.pop("text_abstract", None)
    t.pop("text_fulltext", None)
    t.pop("databank_field", None)
    # All three codes mean "the planted identifier does not resolve", which IS
    # the defect. Demanding only SUGGESTED_CORRECTION produced a FALSE DEAD on
    # the first run: the snapshot happened to contain five single-digit
    # neighbours, so the detector correctly answered AMBIGUOUS_CORRECTION and
    # the harness called it dead. A planted positive must assert that the
    # detector NOTICED, not that it phrased the notice one particular way.
    return p, ("SUGGESTED_CORRECTION", "AMBIGUOUS_CORRECTION",
               "NCT_DOES_NOT_RESOLVE")


def inj_d29(pool):
    r = _find_row(pool, "nct", "pub_reported_n")
    if r is None:
        return None, ["nct", "pub_reported_n"]
    p = copy.deepcopy(pool)
    ext = dict(g(p, "external", {}) or {})
    recs = dict(ext.get("registry_records") or {})
    recs[str(r["nct"])] = {"version": "planted-1", "enrolment":
                           float(r["pub_reported_n"]) + 500}
    ext["registry_records"] = recs
    p["external"] = ext
    return p, "REGISTRY_FIELD_DISCORDANCE"


def inj_d30(pool):
    rows = g(pool, "rows", []) or []
    if not rows:
        return None, ["rows"]
    p = copy.deepcopy(pool)
    ext = dict(g(p, "external", {}) or {})
    ext["link_candidates"] = {"planted_pm1": {"title": str(
        g(rows[0], "title", "planted candidate title"))}}
    p["external"] = ext
    for r in p["rows"]:
        r.pop("nct", None)
    return p, "LINK_CANDIDATES"


def inj_d31(pool):
    r = _find_row(pool, "citation_id", "reported_n")
    if r is None:
        return None, ["citation_id", "reported_n"]
    p = copy.deepcopy(pool)
    ext = dict(g(p, "external", {}) or {})
    idx = dict(ext.get("index_sample_sizes") or {})
    idx[str(r["citation_id"])] = float(r["reported_n"]) * 0.5
    ext["index_sample_sizes"] = idx
    p["external"] = ext
    return p, "INDEX_N_DISAGREEMENT"


def inj_d32(pool):
    r = _find_row(pool, "citation_id")
    if r is None:
        return None, ["citation_id"]
    p = copy.deepcopy(pool)
    t = next(x for x in p["rows"] if x.get("row_id") == r.get("row_id"))
    stored = [k for k in ("sd_t", "sd_c", "n_t", "e_t", "effect", "se")
              if g(t, k) is not MISSING]
    if not stored:
        return None, ["any of sd_t, sd_c, n_t, e_t, effect, se"]
    ext = dict(g(p, "external", {}) or {})
    lane = dict(ext.get("erratum_lane") or {})
    lane[str(t["citation_id"])] = {
        "has_erratum": True, "erratum_pmid": "planted",
        "fields_touched": stored[:2],
        "erratum_text": "In Table 2 the values were incorrect and should read."}
    ext["erratum_lane"] = lane
    p["external"] = ext
    return p, "ERRATUM_TOUCHES_STORED_CELL"


INJECTORS = {
    "D-01": inj_d01, "D-02": inj_d02, "D-03": inj_d03, "D-04": inj_d04,
    "D-05": inj_d05, "D-06": inj_d06, "D-07": inj_d07, "D-08": inj_d08,
    "D-09": inj_d09, "D-10": inj_d10, "D-11": inj_d11, "D-12": inj_d12,
    "D-13": inj_d13, "D-14": inj_d14, "D-15": inj_d15, "D-16": inj_d16,
    "D-17": inj_d17, "D-18": inj_d18, "D-19": inj_d19, "D-20": inj_d20,
    "D-21": inj_d21, "D-22": inj_d22, "D-23": inj_d23, "D-24": inj_d24,
    "D-25": inj_d25, "D-26": inj_d26, "D-27": inj_d27, "D-28": inj_d28,
    "D-29": inj_d29, "D-30": inj_d30, "D-31": inj_d31, "D-32": inj_d32,
}


def plant(pools: list[dict], max_pools: int = 200) -> dict:
    results = {}
    for det in all_detectors():
        inj = INJECTORS.get(det.id)
        if inj is None:
            results[det.id] = {"fires": None, "reason": "NO_INJECTOR"}
            continue
        fired, tried, missing_seen = False, 0, []
        for pool in pools[:max_pools]:
            mutated, expect = inj(pool)
            if mutated is None:
                missing_seen = expect
                continue
            tried += 1
            accept = (expect,) if isinstance(expect, str) else tuple(expect)
            findings, ctx = run_detector(det, mutated)
            # D-30 is a recall tool and reports at UNVERIFIABLE by design, so
            # "noticed" cannot be defined as "actionable" for it. Anywhere else,
            # an UNVERIFIABLE response to a planted defect is NOT a catch.
            noticed = any(
                f.code in accept and
                (f.verdict in ACTIONABLE or det.id == "D-30")
                for f in findings)
            if noticed:
                fired = True
                results[det.id] = {
                    "fires": True, "reason": "PLANTED_CAUGHT",
                    "expected_code": list(accept),
                    "pool_id": pool.get("pool_id"),
                    "rows_examined": ctx.rows_examined,
                    "pools_attempted": tried}
                break
        if not fired:
            if tried == 0:
                results[det.id] = {
                    "fires": None, "reason": "NOT_PLANTABLE",
                    "missing_fields": missing_seen,
                    "note": ("corpus never supplies the fields this defect needs; "
                             "this is an extraction-coverage gap, not a pass")}
            else:
                results[det.id] = {
                    "fires": False, "reason": "PLANTED_NOT_CAUGHT",
                    "pools_attempted": tried,
                    "note": ("DEAD ON THIS CORPUS: a real row was broken in the "
                             "exact way this detector exists to catch, and it did "
                             "not fire, despite a green fixture suite")}
    return results


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus", nargs="+")
    ap.add_argument("--out", default="mg_planted_report.json")
    ap.add_argument("--max-pools", type=int, default=200)
    args = ap.parse_args(argv[1:])

    pools = []
    for p in args.corpus:
        path = pathlib.Path(p)
        if not path.exists():
            print(f"no such corpus file: {path}", file=sys.stderr)
            return 2
        pools.extend(load_corpus(path))
    if not pools:
        print("corpus contained no pools", file=sys.stderr)
        return 2

    results = plant(pools, args.max_pools)
    dead = [d for d, v in results.items() if v["fires"] is False]
    gaps = [d for d, v in results.items() if v["fires"] is None]

    print("=" * 88)
    print(f"planted positives in real corpus rows ({len(pools)} pools available)")
    print("=" * 88)
    for did in sorted(results):
        v = results[did]
        mark = {True: "fires", False: "DEAD", None: "not plantable"}[v["fires"]]
        extra = ""
        if v["fires"] is None and v.get("missing_fields"):
            extra = f"  needs: {v['missing_fields']}"
        print(f"  {did:<8}{mark:<16}{v['reason']:<22}{extra}")
    print("-" * 88)
    if dead:
        print(f"  DEAD ON THIS CORPUS: {dead}")
    if gaps:
        print(f"  EXTRACTION-COVERAGE GAPS (cannot be tested, not clean): {gaps}")
    if not dead and not gaps:
        print("  every detector fired on a planted defect in real corpus data")

    pathlib.Path(args.out).write_text(
        json.dumps({"pools_available": len(pools), "detectors": results}, indent=2),
        encoding="utf-8")
    print(f"\nwrote {args.out}")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
