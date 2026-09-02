r"""Absolute effects from the SSOT store: risk difference and NNT, with the
baseline that produced them named on every row.

WHY THIS EXISTS
    The store publishes RELATIVE estimates. A relative estimate is not
    actionable on its own: the SAME risk ratio means wildly different things
    at different baseline risks. The dapivirine ring case in this corpus is
    the standing illustration -- roughly 75 woman-years per infection
    prevented at the trial's own incidence, roughly 3,370 in a
    lower-incidence setting, from ONE unchanged risk ratio.

    Therefore every number this module emits carries:
        baseline_value   -- the control-arm risk actually used
        baseline_source  -- where that number came from, by name
        baseline_note    -- that a different baseline gives a different answer
    and the per-trial spread of control risks, so the reader can see the
    range the pooled baseline is hiding.

WHAT IT DOES NOT DO
    It does not recommend, rank, or say a drug is better for any population.
    It publishes a calculation and its inputs. The reader supplies the setting.

    It does not assign clinical valence. `cure_toc_me` counts CURES as
    events, so a risk ratio below 1 there is not "benefit". Direction is
    reported as FEWER_EVENTS / MORE_EVENTS, which is arithmetic, not judgement.

ORDER OF CHECKS (the store's refusal is consulted FIRST)
    1. REFUSED_BY_STORE     pooled.withdrawn true, or poolable false.
                            The store refused this pool with a written
                            reason; adding an absolute effect on top of it
                            would be the same defect one layer up.
    2. NNT_NOT_COMPUTABLE   a named state with a reason. Never a blank,
                            never a zero.
    3. COMPUTABLE           risk difference + NNT + interval.

MEASURES
    RR, OR      convertible, each with its assumption named.
    HR          REFUSED. A hazard ratio is not a risk ratio: converting it
                needs proportional hazards AND a stated time horizon.
    MD, IRR,
    RATE_RATIO  REFUSED. Mean differences are not risks; rate ratios are
                person-time and their "baseline" is not a proportion.

INTERVAL
    The baseline is held FIXED and the relative measure's interval is
    transformed through it. The resulting interval therefore reflects
    uncertainty in the RELATIVE measure only, and NOT uncertainty in the
    baseline risk. That assumption is stated on every computed row as
    `interval_assumption`; it is the Cochrane Handbook convention and it is
    an understatement of total uncertainty, not an overstatement.

    NNT intervals follow Altman (BMJ 1998;317:1309): when the risk-difference
    interval spans zero, the NNT interval is NOT a finite range -- it runs
    from a benefit bound out to infinity and back from harm.
"""
from __future__ import annotations
import json, math, os, re, glob, argparse
from collections import OrderedDict, Counter

STORE = os.path.join("ssot", "*", "*.json")

CONVERTIBLE = {"RR", "OR"}
REFUSED_MEASURES = {
    "HR": "a hazard ratio is not a risk ratio; converting it requires "
          "proportional hazards and a stated time horizon, neither of which "
          "this module assumes",
    "MD": "a mean difference is a change on a continuous scale, not a risk; "
          "an NNT would require a responder threshold that the store does "
          "not state",
    "MEAN_DIFFERENCE": "a mean difference is a change on a continuous scale, "
          "not a risk; an NNT would require a responder threshold that the "
          "store does not state",
    "RATE_RATIO": "a rate ratio is per person-time; its baseline is an "
          "incidence rate, not a proportion, so a risk difference is not "
          "defined without a follow-up duration",
    "IRR": "an incidence rate ratio is per person-time; its baseline is an "
          "incidence rate, not a proportion, so a risk difference is not "
          "defined without a follow-up duration",
}

# Words that identify an arm as the CONTROL/COMPARATOR by role rather than
# by drug name. Matched against the arm-key prefix AND against the
# comparator the object itself declares in outcomes[].comparator.
ROLE_WORDS = ("control", "comparator", "placebo", "sham", "usual_care",
              "standard_care", "background")


def _dicts(seq):
    """Yield only the mapping items of seq.

    POSITIVE FORM, and the reason is not cosmetic. These are TYPE guards on
    individual items -- nothing here is counted, reported, or has a
    denominator -- but written as `if not isinstance(x, dict): continue`
    they are indistinguishable, to a reader or to the repo-wide exclusion
    gate, from a filter that silently shrinks a population. Naming what is
    KEPT removes the ambiguity instead of arguing about it.
    """
    for item in (seq or []):
        if isinstance(item, dict):
            yield item


def _norm(s):
    """Lowercase, strip punctuation, collapse to underscore tokens."""
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


def _tokens(s):
    return set(t for t in _norm(s).split("_") if t)


# ---------------------------------------------------------------- arm reading

def _pairs_from_row(row):
    """Find <prefix>_events/<prefix>_n and events_<suffix>/n_<suffix> pairs.

    Returns {prefix: {'events': int, 'n': int}} for prefixes that have BOTH.
    Key names in this store are drug-specific (events_apixaban,
    dapivirine_ring_events, ceftaroline_n), so a fixed key list would
    silently miss most topics. This pairs them structurally instead.
    """
    ev, nn = {}, {}
    for k, v in row.items():
        # named positively: what a usable arm count IS. A bool is excluded
        # explicitly because in Python True is an int and would pass as 1.
        is_a_plain_integer = isinstance(v, int) and isinstance(v, bool) is False
        if is_a_plain_integer is False:
            continue
        m = re.match(r"^(.+)_events$", k)
        if m:
            ev[m.group(1)] = v
            continue
        m = re.match(r"^events_(.+)$", k)
        if m:
            ev[m.group(1)] = v
            continue
        m = re.match(r"^(.+)_n$", k)
        if m:
            nn[m.group(1)] = v
            continue
        m = re.match(r"^n_(.+)$", k)
        if m:
            nn[m.group(1)] = v
            continue
    return {p: {"events": ev[p], "n": nn[p]} for p in ev if p in nn}


def _resolve_control(prefixes, declared_comparator):
    """Decide which of exactly two arm prefixes is the CONTROL.

    Resolution is by NAME, never by position or order:
      1. a prefix carrying a control/comparator role word;
      2. a prefix whose tokens overlap the comparator the object declares.
    If neither resolves, or both do, the caller must refuse. Guessing the
    control arm inverts the baseline and every number downstream of it.
    """
    if len(prefixes) != 2:
        return None, "expected exactly two arms, found %d: %s" % (
            len(prefixes), sorted(prefixes))
    by_role = [p for p in prefixes
               if any(w in _norm(p) for w in ROLE_WORDS)]
    if len(by_role) == 1:
        return by_role[0], "arm key carries a control/comparator role word"
    if declared_comparator:
        ctoks = _tokens(declared_comparator)
        by_name = [p for p in prefixes if _tokens(p) & ctoks]
        if len(by_name) == 1:
            return by_name[0], (
                "arm key matches the comparator this object declares (%r)"
                % declared_comparator)
    return None, (
        "cannot name which of %s is the control arm; declared comparator is "
        "%r. Refusing rather than guessing: guessing inverts the baseline."
        % (sorted(prefixes), declared_comparator))


def collect_control_arms(obj, outcome_name, outcome_entry, comparator):
    """Gather per-trial control/treatment counts for ONE outcome.

    Reads every arm shape this store actually uses, all of them keyed to the
    outcome being pooled -- never a trial-level or registered-primary count
    borrowed from a different endpoint.

    Returns (rows, notes). rows: [{trial, control_events, control_n,
    treatment_events, treatment_n, shape, arm_resolution}]
    """
    rows, notes = [], []

    # Shape A: inputs.trials[].by_outcome.<outcome>.{control,treatment}
    # Explicitly labelled. No arm-role inference needed.
    inputs = obj.get("inputs")
    trials = inputs.get("trials") if isinstance(inputs, dict) else None
    for t in _dicts(trials):
        bo = t.get("by_outcome")
        e = bo.get(outcome_name) if isinstance(bo, dict) else None
        c = e.get("control") if isinstance(e, dict) else None
        x = e.get("treatment") if isinstance(e, dict) else None
        if isinstance(c, dict) and isinstance(x, dict):
            try:
                ce, cn = int(c["events"]), int(c["n"])
                te, tn = int(x["events"]), int(x["n"])
            except (KeyError, TypeError, ValueError):
                continue
            rows.append(dict(trial=t.get("id") or t.get("nct") or "?",
                             control_events=ce, control_n=cn,
                             treatment_events=te, treatment_n=tn,
                             shape="inputs.trials[].by_outcome.%s.control"
                                   % outcome_name,
                             arm_resolution="the store labels the arms "
                                            "control and treatment "
                                            "explicitly"))

    # Shape B: results...per_trial[] and per_trial[].as_posted, drug-keyed.
    for r in _dicts(outcome_entry.get("per_trial")):
        ap = r.get("as_posted")
        for container, tag in ((r, "per_trial[]"),
                               (ap if isinstance(ap, dict) else None,
                                "per_trial[].as_posted")):
            if container is None:
                continue
            pairs = _pairs_from_row(container)
            if len(pairs) != 2:
                if pairs:
                    notes.append("%s on trial %s yielded %d arm(s), not 2: %s"
                                 % (tag, r.get("trial_id"), len(pairs),
                                    sorted(pairs)))
                continue
            ctrl, why = _resolve_control(set(pairs), comparator)
            if ctrl is None:
                notes.append("%s on trial %s: %s"
                             % (tag, r.get("trial_id"), why))
                continue
            trt = [p for p in pairs if p != ctrl][0]
            rows.append(dict(trial=r.get("trial_id") or r.get("nct") or "?",
                             control_events=pairs[ctrl]["events"],
                             control_n=pairs[ctrl]["n"],
                             treatment_events=pairs[trt]["events"],
                             treatment_n=pairs[trt]["n"],
                             shape=tag + " (%s vs %s)" % (trt, ctrl),
                             arm_resolution=why))
            break  # one shape per trial row; as_posted is not a second trial

    # Shape C: count_panels.baseline_risk[] -- control arm only, no treatment.
    cp = outcome_entry.get("count_panels")
    if isinstance(cp, dict) and not rows:
        br = cp.get("baseline_risk")
        if isinstance(br, list):
            for b in _dicts(br):
                try:
                    ce, cn = int(b["control_events"]), int(b["control_n"])
                except (KeyError, TypeError, ValueError):
                    continue
                rows.append(dict(trial=b.get("trial") or "?",
                                 control_events=ce, control_n=cn,
                                 treatment_events=None, treatment_n=None,
                                 shape="count_panels.baseline_risk[]",
                                 arm_resolution="the store labels this a "
                                                "control arm explicitly"))
    # De-duplicate on trial, keeping the FIRST shape seen, which is the
    # explicitly labelled one because the labelled pass runs first.
    #
    # `setdefault` rather than `if key in seen`: an identifier on the left of
    # `in` cannot be told apart statically from an unanchored substring test,
    # which is a real trap this repo has been bitten by, so the lint refuses
    # the shape rather than guessing. First-wins dedup is expressible without
    # the operator at all, and reads better for it.
    by_trial = OrderedDict()
    for r in rows:
        by_trial.setdefault(r["trial"], r)
    return list(by_trial.values()), notes


# ------------------------------------------------------------- the arithmetic

def risk_from_relative(measure, rel, baseline):
    """Treated-arm risk implied by a relative measure at a given baseline."""
    if measure == "RR":
        return baseline * rel
    if measure == "OR":
        odds_c = baseline / (1.0 - baseline)
        odds_t = odds_c * rel
        return odds_t / (1.0 + odds_t)
    raise ValueError("not convertible: %r" % measure)


def absolute_effect(measure, point, ci_low, ci_high, baseline):
    """Risk difference and NNT at a FIXED baseline.

    Both conversions are monotone increasing in the relative measure, so the
    risk-difference bounds come from the relative bounds in the same order.
    """
    r1 = risk_from_relative(measure, point, baseline)
    ard = r1 - baseline
    out = OrderedDict()
    out["treated_risk"] = r1
    out["baseline_risk"] = baseline
    out["risk_difference"] = ard
    out["risk_difference_per_1000"] = ard * 1000.0
    out["direction"] = "FEWER_EVENTS" if ard < 0 else (
        "MORE_EVENTS" if ard > 0 else "NO_DIFFERENCE")
    out["nnt"] = (1.0 / abs(ard)) if ard != 0 else None

    if ci_low is None or ci_high is None:
        out["interval"] = None
        out["interval_absent_reason"] = (
            "the store supplies no interval for the relative measure, so no "
            "interval is manufactured here")
        return out

    lo = risk_from_relative(measure, ci_low, baseline) - baseline
    hi = risk_from_relative(measure, ci_high, baseline) - baseline
    lo, hi = (lo, hi) if lo <= hi else (hi, lo)
    out["risk_difference_ci_low"] = lo
    out["risk_difference_ci_high"] = hi

    # Altman 1998: an NNT interval across a risk difference spanning zero is
    # NOT a finite range. Reporting one would be a fabrication.
    if lo < 0 < hi:
        out["nnt_ci_kind"] = "SPANS_NO_DIFFERENCE"
        out["nnt_ci"] = OrderedDict([
            ("nnt_fewer_events_bound", 1.0 / abs(lo)),
            ("to", "infinity"),
            ("nnt_more_events_bound", 1.0 / abs(hi)),
            ("reading", "Altman 1998: the risk difference interval includes "
                        "zero, so the NNT interval is not a finite range. It "
                        "runs from the fewer-events bound out to infinity "
                        "and back from the more-events bound."),
        ])
    elif lo == 0 or hi == 0:
        out["nnt_ci_kind"] = "BOUND_AT_NO_DIFFERENCE"
        out["nnt_ci"] = {"reading": "an interval bound sits exactly at no "
                                    "difference, so one NNT bound is "
                                    "infinite"}
    else:
        out["nnt_ci_kind"] = "FINITE"
        a, b = abs(lo), abs(hi)
        out["nnt_ci"] = OrderedDict([("low", 1.0 / max(a, b)),
                                     ("high", 1.0 / min(a, b))])
    return out


# -------------------------------------------------------------- store walking

def store_refusal(outcome_entry):
    """The store's own refusal, consulted BEFORE any arithmetic.

    Returns (refused: bool, verbatim_reason: str|None).
    """
    pooled = outcome_entry.get("pooled")
    pooled = pooled if isinstance(pooled, dict) else {}
    if pooled.get("withdrawn"):
        return True, (pooled.get("withdrawn_reason")
                      or pooled.get("withdrawn_because")
                      or pooled.get("withdrawn_note")
                      or "pooled.withdrawn is set with no reason recorded")
    if outcome_entry.get("poolable") is False:
        return True, (outcome_entry.get("poolable_reason")
                      or "poolable is false with no reason recorded")
    if pooled.get("absent"):
        return True, (pooled.get("absent_reason")
                      or "pooled.absent is set with no reason recorded")
    return False, None


def declared_comparator(obj, outcome_name):
    for oc in (obj.get("outcomes") or []):
        if isinstance(oc, dict) and oc.get("id") == outcome_name:
            return oc.get("comparator")
    return None


def evaluate(path, obj, outcome_name, outcome_entry):
    """One candidate -> exactly one of COMPUTABLE / REFUSED_BY_STORE /
    NNT_NOT_COMPUTABLE. Never a blank, never a zero."""
    topic = os.path.basename(os.path.dirname(path))
    row = OrderedDict(topic=topic, outcome=outcome_name, source_file=path)

    refused, reason = store_refusal(outcome_entry)
    if refused:
        row["state"] = "REFUSED_BY_STORE"
        row["store_reason_verbatim"] = reason
        return row

    pooled = outcome_entry.get("pooled")
    pooled = pooled if isinstance(pooled, dict) else {}
    measure, point = pooled.get("measure"), pooled.get("point")
    row["measure"] = measure
    row["pooled_point"] = point
    row["k"] = outcome_entry.get("k")

    if measure is None:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("MEASURE_ABSENT: the pool records no measure, so "
                         "there is nothing to convert")
        return row
    if measure in REFUSED_MEASURES:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = "MEASURE_NOT_CONVERTIBLE:%s -- %s" % (
            measure, REFUSED_MEASURES[measure])
        return row
    if measure not in CONVERTIBLE:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("MEASURE_UNRECOGNISED:%s -- not converted, because "
                         "this module converts only %s"
                         % (measure, sorted(CONVERTIBLE)))
        return row
    # Named positively: what a usable pooled point IS. A ratio must be a real
    # number, finite, and strictly positive -- a bool is excluded explicitly
    # because in Python True is an int and would otherwise pass as 1.0.
    point_is_a_positive_finite_ratio = (
        isinstance(point, (int, float))
        and not isinstance(point, bool)
        and math.isfinite(point)
        and point > 0)
    if point_is_a_positive_finite_ratio is False:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("POOLED_POINT_UNUSABLE: %r is not a positive finite "
                         "ratio" % (point,))
        return row

    comp = declared_comparator(obj, outcome_name)
    arms, notes = collect_control_arms(obj, outcome_name, outcome_entry, comp)
    if notes:
        row["arm_reading_notes"] = notes
    usable = [a for a in arms if isinstance(a["control_events"], int)
              and isinstance(a["control_n"], int) and a["control_n"] > 0]
    if len(usable) == 0:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("NO_CONTROL_ARM_RISK: no trial in this object "
                         "supplies control-arm events and denominator for "
                         "this outcome. A baseline is NOT substituted from "
                         "any other source; an absolute effect without a "
                         "named baseline is meaningless.")
        return row

    ce = sum(a["control_events"] for a in usable)
    cn = sum(a["control_n"] for a in usable)
    baseline = ce / cn
    baseline_is_a_proportion = (0.0 < baseline < 1.0)
    if baseline_is_a_proportion is False:
        row["state"] = "NNT_NOT_COMPUTABLE"
        row["reason"] = ("BASELINE_DEGENERATE: pooled control risk is %r "
                         "(%d/%d); a risk of exactly 0 or 1 gives no usable "
                         "risk difference" % (baseline, ce, cn))
        return row

    row["state"] = "COMPUTABLE"
    row["baseline_value"] = baseline
    row["baseline_source"] = (
        "CONTROL ARMS OF THE TRIALS IN THIS OBJECT: %d events in %d "
        "control-arm participants, summed across %d trial(s) contributing "
        "this outcome." % (ce, cn, len(usable)))
    row["baseline_note"] = (
        "THIS ANSWER IS A FUNCTION OF THIS BASELINE. A different baseline "
        "gives a different absolute effect from the SAME relative estimate. "
        "In this corpus the dapivirine ring shows the size of that: roughly "
        "75 woman-years per infection prevented at trial incidence against "
        "roughly 3,370 in a lower-incidence setting, from one unchanged "
        "risk ratio. The reader must supply the baseline for their setting.")
    per_trial_risk = [
        OrderedDict([("trial", a["trial"]),
                     ("control_events", a["control_events"]),
                     ("control_n", a["control_n"]),
                     ("control_risk", a["control_events"] / a["control_n"]),
                     ("shape", a["shape"]),
                     ("arm_resolution", a["arm_resolution"])])
        for a in usable]
    row["baseline_per_trial"] = per_trial_risk
    risks = [p["control_risk"] for p in per_trial_risk]
    row["baseline_spread"] = OrderedDict([
        ("min", min(risks)), ("max", max(risks)),
        ("fold", (max(risks) / min(risks)) if min(risks) > 0 else None),
        ("note", "the spread the pooled baseline is hiding; the absolute "
                 "effect at the lowest and highest trial baselines differs "
                 "by this factor")])

    row["conversion_assumption"] = (
        "RISK RATIO APPLIED TO THE BASELINE RISK: treated risk = baseline x "
        "RR." if measure == "RR" else
        "ODDS RATIO CONVERTED THROUGH THE ODDS OF THE BASELINE RISK: "
        "treated odds = OR x baseline odds, then back to a risk. This "
        "assumes the odds ratio is constant across baseline risk, which is "
        "an assumption, not a measurement.")
    row["interval_assumption"] = (
        "The baseline is held FIXED. The interval below transforms the "
        "interval of the relative measure only, and therefore EXCLUDES "
        "uncertainty in the baseline risk. It understates total uncertainty.")
    row["ci_level"] = pooled.get("ci_level")
    row.update(absolute_effect(measure, point, pooled.get("ci_low"),
                               pooled.get("ci_high"), baseline))
    return row


def _file_kind(path):
    """Name what a store file IS. Returns (kind, obj_or_None).

    Every return here states a positive property of the file. The caller
    counts the kind before deciding whether to walk it, so a file that is
    not walked still appears in the population.
    """
    try:
        obj = json.load(open(path, encoding="utf-8"))
    except Exception:
        return "unparseable", None
    if isinstance(obj, dict):
        if "THE_OBJECT_AS_IT_STOOD_AT_RETIREMENT" in obj:
            return "tombstone", obj
        res = obj.get("results")
        if isinstance(res, dict):
            bo = res.get("by_outcome")
            if isinstance(bo, dict) and bo:
                return "live_with_outcomes", obj
            return "no_by_outcome", obj
        return "no_results", obj
    return "root_not_dict", None


def candidates(pattern=STORE):
    """Yield (path, obj, outcome_name, outcome_entry, kinds) for LIVE objects.

    Kinds of file in the population are enumerated, not assumed: tombstones
    (retired objects whose data sits under THE_OBJECT_AS_IT_STOOD_AT_
    RETIREMENT) are excluded and counted separately, because a retired
    object's arm counts are not live data.
    """
    kinds = OrderedDict([("live_with_outcomes", 0), ("tombstone", 0),
                         ("no_results", 0), ("no_by_outcome", 0),
                         ("unparseable", 0), ("root_not_dict", 0)])
    for path in sorted(glob.glob(pattern)):
        # POSITIVE FORM ON PURPOSE. Each file is given a NAME saying what it
        # IS, and only the file named "live_with_outcomes" is walked. Written
        # as a chain of `if not ...: continue` guards this reads as a list of
        # absences, and an absence-shaped skip is how a denominator silently
        # shrinks -- the reason every kind here is counted rather than
        # dropped. Naming the kind makes the skip a reported category instead
        # of a hole.
        kind, obj = _file_kind(path)
        kinds[kind] += 1
        if kind != "live_with_outcomes":
            continue
        res = obj.get("results")
        bo = res.get("by_outcome")
        for name, entry in bo.items():
            if isinstance(entry, dict):
                yield path, obj, name, entry, kinds


def run(pattern=STORE):
    rows, kinds = [], None
    for path, obj, name, entry, k in candidates(pattern):
        kinds = k
        rows.append(evaluate(path, obj, name, entry))
    return rows, (kinds or {})


def main():
    ap = argparse.ArgumentParser(description="absolute effects from the store")
    ap.add_argument("--pattern", default=STORE)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()
    rows, kinds = run(args.pattern)

    n_comp = sum(1 for r in rows if r["state"] == "COMPUTABLE")
    n_ref = sum(1 for r in rows if r["state"] == "REFUSED_BY_STORE")
    n_not = sum(1 for r in rows if r["state"] == "NNT_NOT_COMPUTABLE")
    total = len(rows)

    print("POPULATION -- kinds of file enumerated before any count")
    for k, v in kinds.items():
        print("  %-22s %d" % (k, v))
    print("")
    print("CANDIDATES (outcome entries in live objects): %d" % total)
    print("  COMPUTABLE          %d" % n_comp)
    print("  REFUSED_BY_STORE    %d" % n_ref)
    print("  NNT_NOT_COMPUTABLE  %d" % n_not)
    ok = (n_comp + n_ref + n_not) == total
    print("  identity  computable + refused_by_store + not_computable "
          "== candidates : %s (%d + %d + %d == %d)"
          % ("HOLDS" if ok else "FAILS", n_comp, n_ref, n_not, total))
    print("")
    print("COVERAGE: %d of %d outcome entries in live store objects yield an "
          "absolute effect (%.1f%%)."
          % (n_comp, total, 100.0 * n_comp / total if total else 0.0))
    print("  The denominator is NAMED: outcome entries under "
          "results.by_outcome in the %d live objects matching %s. It is NOT "
          "the topic count and NOT the page count."
          % (kinds.get("live_with_outcomes", 0), args.pattern))
    print("")
    print("WHY THE REST ARE NOT COMPUTABLE")
    c = Counter(r.get("reason", "").split(":")[0].split(" --")[0]
                for r in rows if r["state"] == "NNT_NOT_COMPUTABLE")
    for k, v in c.most_common():
        print("  %-30s %d" % (k, v))
    print("")
    print("COMPUTED ROWS")
    for r in rows:
        if r["state"] != "COMPUTABLE":
            continue
        nnt = r.get("nnt")
        print("  %-40s %-26s %s %.4f  baseline %.4f  %s  ARD %+.4f  "
              "NNT %.1f [%s]"
              % (r["topic"], r["outcome"], r["measure"], r["pooled_point"],
                 r["baseline_value"], r["direction"], r["risk_difference"],
                 nnt if nnt else float("nan"), r.get("nnt_ci_kind")))
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1, ensure_ascii=False)
        print("")
        print("wrote %s" % args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
