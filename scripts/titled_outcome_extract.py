# -*- coding: utf-8 -*-
"""Titled-outcome extraction: a 2x2 (events, N per arm) for an EFFICACY outcome from a trial's
OWN posted outcome measure -- not the AE module. This is the step that unlocks the efficacy block
(CV death, MI, stroke, HF hospitalisation) of a benchmark.

FOUR RULES, each one a scar. Every one has a test in test_titled_outcome_extract.py that fails
before the rule exists and passes after.

  RULE 1  THE ANALYSIS DENOMINATOR IS OFTEN IN THE CLASS TITLE, NOT outcome_counts.
          outcome_counts holds the randomised total; the analysis N is frequently written into
          the class title as "(n=2629, 2616)" or "(n=343; n=334; n=345)", positional to the
          arms. Reading outcome_counts there gave 48 confidently-wrong integers. So: parse the
          class title first; fall back to outcome_counts; and RECORD which field was read, so a
          reader can check it against the class title.

  RULE 2  THE ROUTE IS ARITHMETIC, NOT PROSE. 730 of 1009 recoverable values are events = a
          posted percentage x the analysis N; only 2 of 83 trials needed prose. So a percentage
          measure is turned into a count arithmetically; a count measure is read directly. There
          is NO prose parser, by design.

  RULE 3  DO NOT FALL BACK TO THE AE MODULE FOR AN EFFICACY OUTCOME. It reaches every trial,
          which is why it tempts, and it disagrees: HEART-FID is 354/367 in the AE module against
          131/158 in its own titled outcome, moving crude RR from 0.965 to 0.830. This extractor
          reads outcome measures ONLY. A caller may CROSS-CHECK against the AE module and flag a
          disagreement; it must never SUBSTITUTE.

  RULE 4  A 0/0 CANNOT BE REPRODUCTION-IDENTIFIED. When both arms have zero events the value
          cannot discriminate which outcome it is, so identity is by title and the status is
          NOT_DISCRIMINATING -- never folded into "could not determine".
"""
from __future__ import annotations
import csv, os, re, sys
from collections import defaultdict

# arm-side vocab (shared with reproduce_benchmark's convention)
GLP1 = ("semaglutide", "liraglutide", "dulaglutide", "exenatide", "lixisenatide",
        "albiglutide", "efpeglenatide", "tirzepatide")
CTRL = ("placebo", "control", "comparator", "standard", "sham", "usual care", "matching")

_PCT = re.compile(r"percent|%", re.I)
_COUNTUNIT = re.compile(r"participant|subject|patient|count|number|events?\b", re.I)
# incidence-rate units -- refused, because a rate needs person-time (an IRR), not a 2x2 count
_RATE = re.compile(r"per\s*100|per\s*year|person[-\s]?year|patient[-\s]?year|/\s*100|\brate\b", re.I)
# per-arm analysis N inside a class title: "(n=2629, 2616)" or "(n=343; n=334; n=345)"
_CLASS_N = re.compile(r"\bn\s*=\s*([\d,;\s=n]+)\)", re.I)


def parse_class_denoms(class_title):
    """RULE 1. Return the per-arm N list embedded in a class title, or None. Handles both
    '(n=2629, 2616)' and '(n=343; n=334; n=345)'."""
    if not class_title:
        return None
    m = _CLASS_N.search(class_title)
    if not m:
        return None
    nums = re.findall(r"\d+", m.group(1))
    return [int(x) for x in nums] if nums else None


def load_tables(aact, ncts):
    want = {n for n in ncts if n}
    meas = defaultdict(list)     # nct -> [row dict]
    counts = defaultdict(lambda: defaultdict(dict))   # nct -> outcome_id -> {group: N}
    groups = defaultdict(dict)   # nct -> {group_code: title}
    ae = defaultdict(list)       # nct -> [(event_type, group, affected, at_risk)]

    def rows(name):
        with open(os.path.join(aact, name), encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f, delimiter="|"):
                if (r.get("nct_id") or "").strip().upper() in want:
                    yield r
    for r in rows("outcome_measurements.txt"):
        meas[r["nct_id"].upper()].append(r)
    for r in rows("outcome_counts.txt"):
        n = r.get("count")
        try:
            n = int(n)
        except (TypeError, ValueError):
            continue
        if (r.get("units") or "").lower().startswith("participant") or r.get("scope") == "Measure":
            counts[r["nct_id"].upper()][r.get("outcome_id")][r.get("ctgov_group_code")] = n
    for r in rows("result_groups.txt"):
        groups[r["nct_id"].upper()][r.get("ctgov_group_code")] = r.get("title") or ""
    for r in rows("reported_event_totals.txt"):
        ae[r["nct_id"].upper()].append((r.get("event_type"), r.get("ctgov_group_code"),
                                        r.get("subjects_affected"), r.get("subjects_at_risk")))
    return {"meas": meas, "counts": counts, "groups": groups, "ae": ae}


def _side(title, trt_terms=GLP1):
    t = (title or "").lower()
    if any(g in t for g in trt_terms):
        return "TRT"
    if any(c in t for c in CTRL):
        return "CTRL"
    return "?"


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# Galli efficacy outcome -> how to find it in the measures. `class_match` reads a COMPONENT
# class within a composite outcome (the LEADER route); `title_match` reads a standalone outcome.
# `composite` forbids summing components (MACE != sum of its parts -- double counts a participant
# with two component events).
SPECS = {
    "cv_death":           {"class_match": [r"cardiovascular death", r"\bcv death"], "composite": False},
    "nonfatal_mi":        {"class_match": [r"non-?fatal myocardial infarction", r"non-?fatal mi\b"], "composite": False},
    "nonfatal_stroke":    {"class_match": [r"non-?fatal stroke"], "composite": False},
    "hf_hospitalisation": {"class_match": [r"heart failure \(hospitali", r"hospitali.*heart failure"], "composite": False},
    "mace":               {"title_match": [r"\bmace\b", r"3-?point", r"major adverse cardiovascular"],
                           "composite": True},
    "all_cause_death":    {"title_match": [r"all[- ]?cause (death|mortality)", r"death from any cause",
                                           r"number of deaths"], "composite": False},
}


def _collect(nct, tables, match_field, patterns, is_class):
    """Gather measurement rows for one outcome, grouped by outcome_id, that match the patterns in
    either the class title (is_class) or the outcome title. Returns {outcome_id: [rows]}."""
    out = defaultdict(list)
    for r in tables["meas"].get(nct, []):
        hay = (r.get("classification") if is_class else r.get("title")) or ""
        if any(re.search(p, hay, re.I) for p in patterns):
            out[r.get("outcome_id")].append(r)
    return out


def extract_titled(nct, outcome_key, tables, trt_terms=GLP1):
    """Return {tE,tN,cE,cN, event_route, denom_source, outcome_id, disagreement} for a side-
    resolved 2x2, or {"status": ...} (NOT_FOUND / NOT_DISCRIMINATING / AMBIGUOUS / UNSUPPORTED).
    Reads outcome measures ONLY (RULE 3). Denominator per RULE 1; events per RULE 2."""
    spec = SPECS.get(outcome_key)
    if not spec:
        return {"status": "UNSUPPORTED", "why": "no spec for %s" % outcome_key}
    is_class = "class_match" in spec
    patterns = spec.get("class_match") or spec.get("title_match")
    by_oid = _collect(nct, tables, None, patterns, is_class)
    if not by_oid:
        return {"status": "NOT_FOUND", "why": "no titled/class match for %s" % outcome_key}
    groups = tables["groups"].get(nct, {})

    def _title_is_composite(t):
        t = (t or "").lower()
        return ("composite" in t or "first occurrence of a comp" in t or "\bmace\b" in t
                or sum(w in t for w in ("cardiovascular death", "myocardial infarction", "stroke")) >= 2)

    # An outcome whose title is a COMPOSITE must not answer a single-component key, and vice
    # versa: PIONEER-6's composite (69/89) and its standalone all-cause death (23/45) both match
    # the word 'death', and picking by row-count took the wrong one. Filter by composite-ness of
    # the OUTCOME TITLE against the spec before choosing.
    want_composite = bool(spec.get("composite"))
    filtered = {}
    for oid, rows in by_oid.items():
        otitle = next((r.get("title") for r in rows if r.get("title")), "")
        if _title_is_composite(otitle) == want_composite:
            filtered[oid] = rows
    by_oid = filtered or by_oid

    # pick ONE outcome_id: the one whose rows resolve to both a TRT and a CTRL side.
    for oid, rows in sorted(by_oid.items(), key=lambda kv: -len(kv[1])):
        agg = {}   # side -> {"E":..,"N":..}
        route = denomsrc = None
        pooled_seen = singles_seen = False
        for r in rows:
            cls = (r.get("classification") or "").strip()
            cat = (r.get("category") or "").strip()
            # Take the OVERALL number, never a sub-breakdown that would double/triple count.
            # A title-matched outcome's overall row has empty class AND category; a class-matched
            # component's row has the matched class but must have no further category split.
            if is_class:
                if cat:
                    continue
            else:
                if cls or cat:
                    continue
            gcode = r.get("ctgov_group_code")
            gtitle = groups.get(gcode, "")
            side = _side(gtitle, trt_terms)
            if side == "?":
                continue
            # RULE 2: event route
            val = _num(r.get("param_value_num") if r.get("param_value_num") not in (None, "") else r.get("param_value"))
            if val is None:
                continue
            units = r.get("units") or ""
            # RULE 1: denominator -- class title first, then outcome_counts
            cds = parse_class_denoms(r.get("classification"))
            if cds:
                # positional: group order among this nct's groups
                order = sorted({g for g in groups})
                idx = order.index(gcode) if gcode in order else None
                N = cds[idx] if (idx is not None and idx < len(cds)) else (cds[0] if len(cds) == 1 else None)
                dsrc = "class_title"
            else:
                N = tables["counts"].get(nct, {}).get(oid, {}).get(gcode)
                dsrc = "outcome_counts"
            if N is None:
                continue
            # REFUSE INCIDENCE RATES. "events per 100 participant-years" is a rate; turning it
            # into a count needs person-time and gives an IRR, not a 2x2. Reading it as a count
            # produced AMPLITUDE-O/HARMONY MACE = 5, a confidently-wrong integer. A rate is not
            # extractable here; skip it so the outcome reports NOT_FOUND, never a fabricated count.
            if _RATE.search(units):
                continue
            # arithmetic pct*N ONLY for a percentage OF PARTICIPANTS (a proportion of people),
            # never a bare 'percentage' that could be a rate.
            if _PCT.search(units) and re.search(r"participant|subject|patient", units, re.I):
                E = val / 100.0 * N; route = "arithmetic(pct*N)"
            elif r.get("param_type") == "COUNT_OF_PARTICIPANTS" or _COUNTUNIT.search(units):
                E = val; route = "direct_count"
            else:
                continue
            denomsrc = dsrc
            # pooled multi-dose arm guard (AMPLITUDE-O): if a TRT group title has '+', it is a
            # pre-pooled dose group; do not also add the single-dose groups.
            if side == "TRT" and "+" in gtitle:
                pooled_seen = True
            elif side == "TRT":
                singles_seen = True
            slot = agg.setdefault(side, {"E": 0.0, "N": 0.0, "pooled": [], "single": []})
            (slot["pooled"] if (side == "TRT" and "+" in gtitle) else slot["single"]).append((E, N))
        # resolve TRT: prefer pooled dose groups if present (avoid double count)
        def side_total(slot):
            use = slot["pooled"] if slot["pooled"] else slot["single"]
            return sum(e for e, _ in use), sum(n for _, n in use)
        if "TRT" in agg and "CTRL" in agg:
            tE, tN = side_total(agg["TRT"]); cE, cN = side_total(agg["CTRL"])
            tE, cE = int(round(tE)), int(round(cE)); tN, cN = int(round(tN)), int(round(cN))
            if not (tN > 0 and cN > 0 and 0 <= tE <= tN and 0 <= cE <= cN):
                continue
            if tE == 0 and cE == 0:                       # RULE 4
                return {"status": "NOT_DISCRIMINATING", "outcome_id": oid,
                        "why": "0/0: value cannot reproduction-identify the outcome"}
            return {"tE": tE, "tN": tN, "cE": cE, "cN": cN, "event_route": route,
                    "denom_source": denomsrc, "outcome_id": oid, "nct": nct}
    return {"status": "AMBIGUOUS", "why": "matched rows but no outcome_id resolved both arms"}


def ae_crosscheck(nct, tables, outcome_key, trt_terms=GLP1):
    """RULE 3 helper: what the AE module would say, for a caller to FLAG (never substitute).
    Only defined for all_cause_death (AE 'deaths' totals)."""
    if outcome_key != "all_cause_death":
        return None
    aff, at = defaultdict(int), defaultdict(int)
    for et, code, a, risk in tables["ae"].get(nct, []):
        s = _side(tables["groups"].get(nct, {}).get(code, ""), trt_terms)
        if s == "?":
            continue
        if et == "deaths" and _num(a) is not None:
            aff[s] += int(_num(a))
        if et in ("serious", "other") and _num(risk) is not None:
            at[s] = max(at[s], int(_num(risk)))
    if "TRT" in aff and "CTRL" in aff:
        return {"tE": aff["TRT"], "cE": aff["CTRL"], "tN": at.get("TRT"), "cN": at.get("CTRL")}
    return None
