"""GATE: GRADE imprecision needs a stated decision threshold.

If a GRADE step downgrades for imprecision, the object must record the
imprecision threshold that made that judgement interpretable. A wide interval is
not self-explaining; the decision value inside the confidence interval is the
support for the rating.
"""

import sys,os; sys.dont_write_bytecode=True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _harness as H
import collections
import math
import re


GRADE_CERTAINTY_RANK = {
    "VERY_LOW": 0,
    "LOW": 1,
    "MODERATE": 2,
    "HIGH": 3,
}
STEP_FIELDS = set([
    "steps", "downgrades", "downgrade_steps", "grade_steps", "rating_steps",
    "judgements", "judgments", "domains",
])
REASON_FIELDS = set([
    "reason", "rationale", "explanation", "judgement", "judgment", "note",
    "text", "comment",
])
THRESHOLD_WORDS = re.compile(
    r"\b(threshold|boundary|margin|mcid|mid|minimal|minimum|clinically|"
    r"important|decision|cross(?:es|ed)?|span(?:s|ned)?|include(?:s|d)?|"
    r"exclude(?:s|d)?|null|no effect)\b",
    re.I,
)
THRESHOLD_FIELD_WORDS = re.compile(
    r"\b(threshold|boundary|margin|mcid|mid|minimal|minimum|clinically|"
    r"important|decision)\b",
    re.I,
)
NUMBER = re.compile(r"(?<![A-Za-z0-9])[-+]?(?:\d+\.\d+|\d+)(?:\s*%)?(?![A-Za-z0-9])")
MISSING_TEXT = set([
    "", "none", "null", "missing", "not recorded", "not specified",
    "unspecified", "n/a", "na", "not applicable", "no threshold",
    "no threshold stated",
])


def _number(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        v = float(x)
        return v if math.isfinite(v) else None
    return None


def _numberish(x):
    n = _number(x)
    if n is not None:
        return n
    if isinstance(x, str):
        text = x.strip()
        if re.fullmatch(r"[-+]?(?:\d+\.\d+|\d+)", text):
            try:
                return float(text)
            except ValueError:
                return None
    return None


def _norm_certainty(value):
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("certainty", "final_certainty", "overall_certainty",
                    "grade", "rating", "quality", "level"):
            if key in value:
                found = _norm_certainty(value.get(key))
                if found:
                    return found
        return None
    if isinstance(value, list):
        for item in value:
            found = _norm_certainty(item)
            if found:
                return found
        return None
    s = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    s = re.sub(r"[^A-Z_]", "", s)
    if s == "VERYLOW":
        s = "VERY_LOW"
    return s or None


def _grade_records(obj, oid, outcome):
    records = []
    if isinstance(outcome, dict):
        if "grade" in outcome:
            records.append(outcome.get("grade"))
        if any(k in outcome for k in ("certainty", "final_certainty", "overall_certainty",
                                      "imprecision_threshold")):
            records.append(outcome)
        if any(k in outcome for k in STEP_FIELDS):
            records.append(outcome)

    grade = obj.get("grade") if isinstance(obj, dict) else None
    if isinstance(grade, dict):
        if "imprecision_threshold" in grade:
            records.append(grade)
        by_outcome = grade.get("by_outcome")
        if isinstance(by_outcome, dict) and oid in by_outcome:
            records.append(by_outcome.get(oid))
        elif oid in grade and oid != "by_outcome":
            records.append(grade.get(oid))
    elif grade is not None:
        records.append(grade)

    return [r for r in records if r is not None]


def _looks_like_step(value):
    if not isinstance(value, dict):
        return False
    return any(k in value for k in (
        "domain", "name", "downgrade", "downgraded", "rated_down", "reason",
        "rationale", "judgement", "judgment", "threshold",
    ))


def _steps_from_container(value):
    steps = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                steps.append(item)
        return steps
    if isinstance(value, dict):
        if _looks_like_step(value):
            steps.append(value)
        for name, child in value.items():
            if isinstance(child, dict):
                step = dict(child)
                step.setdefault("domain", name)
                steps.append(step)
            elif child is not None:
                steps.append({"domain": name, "judgement": child})
    return steps


def _steps_from_record(record):
    if not isinstance(record, dict):
        return []
    steps = []
    if _looks_like_step(record):
        steps.append(record)
    for key in STEP_FIELDS:
        if key in record:
            steps.extend(_steps_from_container(record.get(key)))
    for key in ("imprecision", "precision"):
        if key in record:
            for step in _steps_from_container(record.get(key)):
                step = dict(step)
                step.setdefault("domain", "imprecision")
                steps.append(step)
    return steps


def _domain_is_imprecision(step):
    if not isinstance(step, dict):
        return False
    val = step.get("domain")
    return val is not None and "imprecis" in str(val).lower()


def _text_says_downgrade(text):
    t = str(text).lower()
    if re.search(r"\b(no|not|without)\s+(?:a\s+)?downgrade", t):
        return False
    if re.search(r"\bnot\s+rated\s+down|\bnot\s+serious|\bno\s+serious", t):
        return False
    return bool(re.search(r"\bdowngrad|\brated\s+down|\brate\s+down|\bvery\s+serious\b|\bserious\b", t))


def _step_downgrades(step):
    if not isinstance(step, dict):
        return False
    if "levels" in step:
        n = _numberish(step.get("levels"))
        if n is not None:
            return n != 0
        if _text_says_downgrade(step.get("levels")):
            return True
    before = _norm_certainty(step.get("from"))
    after = _norm_certainty(step.get("to"))
    if before in GRADE_CERTAINTY_RANK and after in GRADE_CERTAINTY_RANK:
        return GRADE_CERTAINTY_RANK[after] < GRADE_CERTAINTY_RANK[before]
    for key in ("downgrade", "downgraded", "rated_down", "downrated"):
        if key not in step:
            continue
        value = step.get(key)
        if isinstance(value, bool):
            return value
        n = _number(value)
        if n is not None:
            return n != 0
        if _text_says_downgrade(value):
            return True
    for key in ("change", "delta", "level_change", "rating_change"):
        if key in step:
            n = _number(step.get(key))
            if n is not None and n < 0:
                return True
    for key in ("decision", "judgement", "judgment", "rating", "action", "reason", "rationale"):
        if key in step and _text_says_downgrade(step.get(key)):
            return True
    return False


def _imprecision_downgrade_steps(records):
    steps = []
    for record in records:
        for step in _steps_from_record(record):
            if _domain_is_imprecision(step) and _step_downgrades(step):
                steps.append(step)
    return steps


def _threshold_field_records(value, ci):
    if _missing_text(value):
        return False
    return _threshold_value_records(value, ci)


def _ci_from_mapping(value):
    if not isinstance(value, dict):
        return None

    pairs = [
        ("ci_low", "ci_high"), ("lower_ci", "upper_ci"), ("ci_lower", "ci_upper"),
        ("lower", "upper"), ("low", "high"), ("lcl", "ucl"), ("ll", "ul"),
    ]
    for lo_key, hi_key in pairs:
        lo = _number(value.get(lo_key))
        hi = _number(value.get(hi_key))
        if lo is not None and hi is not None:
            return (min(lo, hi), max(lo, hi))

    for key in ("ci", "confidence_interval", "interval"):
        ci = value.get(key)
        if isinstance(ci, (list, tuple)) and len(ci) >= 2:
            lo = _number(ci[0])
            hi = _number(ci[1])
            if lo is not None and hi is not None:
                return (min(lo, hi), max(lo, hi))
        if isinstance(ci, dict):
            found = _ci_from_mapping(ci)
            if found:
                return found
    return None


def _ci_bounds(outcome):
    if not isinstance(outcome, dict):
        return None
    for candidate in (outcome.get("pooled"), outcome.get("effect"), outcome):
        found = _ci_from_mapping(candidate)
        if found:
            return found
    return None


def _inside_ci(value, ci):
    lo, hi = ci
    tol = max(1e-9, 1e-9 * max(abs(lo), abs(hi), abs(value)))
    return lo - tol <= value <= hi + tol


def _same_as_bound(value, ci):
    lo, hi = ci
    tol = max(1e-9, 1e-7 * max(abs(lo), abs(hi), abs(value), 1.0))
    return abs(value - lo) <= tol or abs(value - hi) <= tol


def _flatten_text(value):
    if value is None:
        return []
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            out.append(str(k))
            out.extend(_flatten_text(v))
        return out
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            out.extend(_flatten_text(item))
        return out
    return [str(value)]


def _missing_text(value):
    return str(value).strip().lower() in MISSING_TEXT


def _values_from_number_token(token):
    is_percent = token.strip().endswith("%")
    raw = token.strip().rstrip("%").strip()
    try:
        value = float(raw)
    except ValueError:
        return []
    values = [value]
    if is_percent:
        values.append(value / 100.0)
    return values


def _confidence_level_token(text, match):
    token = match.group(0).strip()
    if not token.endswith("%"):
        return False
    raw = token.rstrip("%").strip()
    try:
        value = float(raw)
    except ValueError:
        return False
    if value not in (80.0, 90.0, 95.0, 99.0):
        return False
    window = text[match.end():match.end() + 24].lower()
    return "ci" in window or "cri" in window or "confidence" in window


def _threshold_value_records(value, ci):
    n = _number(value)
    if n is not None:
        return True
    if isinstance(value, dict):
        for child in value.values():
            if child is None:
                continue
            if _threshold_value_records(child, ci):
                return True
        return False
    if isinstance(value, (list, tuple)):
        for child in value:
            if child is None:
                continue
            if _threshold_value_records(child, ci):
                return True
        return False

    text = str(value).strip()
    if _missing_text(text):
        return False
    for match in NUMBER.finditer(text):
        if _confidence_level_token(text, match):
            continue
        return True
    return True


def _threshold_from_step_field(steps, ci):
    for step in steps:
        for key, value in step.items():
            if THRESHOLD_FIELD_WORDS.search(str(key)) and _threshold_field_records(value, ci):
                return True
    return False


def _threshold_from_grade_field(records, ci):
    for record in records:
        if not isinstance(record, dict):
            continue
        if "imprecision_threshold" in record:
            if _threshold_field_records(record.get("imprecision_threshold"), ci):
                return True
        grade = record.get("grade")
        if isinstance(grade, dict) and "imprecision_threshold" in grade:
            if _threshold_field_records(grade.get("imprecision_threshold"), ci):
                return True
    return False


def _reason_names_threshold(steps, ci):
    for step in steps:
        for key in REASON_FIELDS:
            if key not in step:
                continue
            for text in _flatten_text(step.get(key)):
                if not THRESHOLD_WORDS.search(text):
                    continue
                if re.search(r"\b(null|no effect)\b", text, re.I):
                    return True
                for match in NUMBER.finditer(text):
                    if _confidence_level_token(text, match):
                        continue
                    window = text[max(0, match.start() - 48):match.end() + 48]
                    if not THRESHOLD_WORDS.search(window):
                        continue
                    return True
    return False


def _has_imprecision_threshold(records, imprecision_steps, outcome):
    ci = _ci_bounds(outcome)
    if _threshold_from_step_field(imprecision_steps, ci):
        return True
    if _threshold_from_grade_field(records, ci):
        return True
    return _reason_names_threshold(imprecision_steps, ci)


def _scan_object(obj, topic):
    stats = collections.Counter()
    findings = []
    by_outcome = ((obj.get("results") or {}).get("by_outcome") if isinstance(obj, dict) else None)
    if not isinstance(by_outcome, dict):
        stats["object with no results.by_outcome mapping"] += 1
        return findings, stats

    for oid, outcome in sorted(by_outcome.items()):
        stats["outcome in results.by_outcome"] += 1
        if not isinstance(outcome, dict):
            stats["outcome not stored as an object"] += 1
            continue

        records = _grade_records(obj, oid, outcome)
        imprecision_steps = _imprecision_downgrade_steps(records)
        if not records and not imprecision_steps:
            stats["outcome with no GRADE record"] += 1
            continue

        stats["outcome with GRADE record examined"] += 1
        if not imprecision_steps:
            stats["GRADE record with no imprecision downgrade step"] += 1
            continue

        stats["outcome with imprecision downgrade step"] += 1
        if _has_imprecision_threshold(records, imprecision_steps, outcome):
            stats["imprecision downgrade with threshold recorded"] += 1
            continue

        ci = _ci_bounds(outcome)
        ci_text = "CI %s to %s" % ci if ci else "no parseable CI fields"
        findings.append({
            "key": "%s/%s" % (topic, oid),
            "detail": "%s has an imprecision downgrade step but records no threshold "
                      "in that step or grade.imprecision_threshold; outcome has %s"
                      % ("%s/%s" % (topic, oid), ci_text),
        })
        stats["imprecision downgrade WITHOUT threshold -- finding"] += 1

    return findings, stats


def check_object(obj, topic="__object__"):
    return _scan_object(obj, topic)[0]


def controls():
    bad = {
        "results": {"by_outcome": {"primary": {
            "pooled": {"measure": "RR", "point": 0.92, "ci_low": 0.72, "ci_high": 1.18},
            "grade": {"certainty": "HIGH", "steps": [
                {"domain": "imprecision", "levels": 1, "from": "HIGH", "to": "MODERATE",
                 "rating": "serious",
                 "reason": "Rated down for imprecision because the interval is wide."}
            ]},
        }}}
    }
    good = {
        "results": {"by_outcome": {"primary": {
            "pooled": {"measure": "RR", "point": 0.92, "ci_low": 0.72, "ci_high": 1.18},
            "grade": {"certainty": "HIGH", "steps": [
                {"domain": "imprecision", "levels": 1, "from": "HIGH", "to": "MODERATE",
                 "rating": "serious", "threshold": 0.90,
                 "reason": "Rated down because the CI crosses the clinically important threshold 0.90."}
            ]},
        }}}
    }
    grade_threshold_good = {
        "grade": {"imprecision_threshold": 0.90, "by_outcome": {"primary": {
            "certainty": "HIGH", "steps": [
                {"domain": "imprecision", "levels": 1, "from": "HIGH", "to": "MODERATE",
                 "rating": "serious",
                 "reason": "Rated down for imprecision because the interval is wide."}
            ],
        }}},
        "results": {"by_outcome": {"primary": {
            "pooled": {"measure": "RR", "point": 0.92, "ci_low": 0.72, "ci_high": 1.18},
        }}}
    }
    risk_of_bias_low = {
        "results": {"by_outcome": {"primary": {
            "pooled": {"measure": "RR", "point": 0.92, "ci_low": 0.72, "ci_high": 1.18},
            "grade": {"certainty": "LOW", "steps": [
                {"domain": "risk_of_bias", "levels": 1, "from": "HIGH", "to": "LOW",
                 "rating": "serious",
                 "reason": "Rated down for risk of bias."}
            ]},
        }}}
    }
    pos_fires = bool(check_object(bad, "__positive_control__"))
    threshold_neg_silent = not bool(check_object(good, "__negative_control__"))
    grade_threshold_neg_silent = not bool(check_object(grade_threshold_good, "__grade_threshold_control__"))
    rob_neg_silent = not bool(check_object(risk_of_bias_low, "__risk_of_bias_control__"))
    return pos_fires, threshold_neg_silent, grade_threshold_neg_silent, rob_neg_silent


def main(argv):
    gate = H.Gate("GRADE IMPRECISION NEEDS THRESHOLD",
                  "imprecision downgrade must record the decision threshold")
    named = gate.expect_case("__synthetic_imprecision_no_threshold__",
                             "imprecision downgrade and no threshold must be flagged")
    gate.requires_control()

    pos_fires, neg_silent, grade_threshold_neg_silent, rob_neg_silent = controls()
    if pos_fires:
        gate.saw(named)
    else:
        gate.broken("the positive synthetic control did not fire")
    false_positive_examples = []
    if not neg_silent:
        false_positive_examples.append("threshold-bearing synthetic negative was flagged")
    if not grade_threshold_neg_silent:
        false_positive_examples.append("grade.imprecision_threshold synthetic negative was flagged")
    if not rob_neg_silent:
        false_positive_examples.append("LOW certainty risk-of-bias downgrade was flagged")
    gate.control(3, len(false_positive_examples),
                 false_positive_examples,
                 accuses=True)
    if not neg_silent:
        gate.broken("the negative synthetic control was not silent")
    if not grade_threshold_neg_silent:
        gate.broken("the grade.imprecision_threshold synthetic control was not silent")
    if not rob_neg_silent:
        gate.broken("the risk-of-bias synthetic control was not silent")

    repo = H.repo_root()
    paths, path_kinds = H.topic_objects(repo)
    stats = collections.Counter()
    findings = []
    parse_failures = 0

    for path in paths:
        try:
            obj = H.load(path)
        except Exception as exc:
            parse_failures += 1
            gate.broken("unparseable object %s: %s" % (path, exc))
            continue
        rows, obj_stats = _scan_object(obj, H.topic_id(path))
        findings.extend(rows)
        stats.update(obj_stats)

    for finding in findings:
        gate.finding(finding["key"], finding["detail"])

    population = stats.get("outcome in results.by_outcome", 0)
    if not paths:
        gate.broken("no ssot topic objects found; cannot prove corpus absence")
    elif population == 0:
        gate.broken("no results.by_outcome outcomes found; cannot prove corpus absence")

    gate.note("positive control %s" % pos_fires)
    gate.note("threshold-bearing negative control %s" % neg_silent)
    gate.note("grade.imprecision_threshold negative control %s" % grade_threshold_neg_silent)
    gate.note("risk-of-bias low-certainty control %s" % rob_neg_silent)
    imprecision_step_outcomes = stats.get("outcome with imprecision downgrade step", 0)
    gate.note("outcomes with an imprecision downgrade step %d" % imprecision_step_outcomes)
    gate.note("corpus finding count %d" % len(findings))
    if population > 0:
        if imprecision_step_outcomes == 0:
            gate.note("no imprecision downgrades in the corpus")
        elif len(findings) == 0:
            gate.note("every imprecision downgrade in the corpus records a threshold")

    gate.kinds({
        "topic object (ssot/<t>/<t>.json)": path_kinds.get("topic object (ssot/<t>/<t>.json)", 0),
        "other json under ssot/<t>/": path_kinds.get("other json under ssot/<t>/", 0),
        "unparseable topic object": parse_failures,
        "object with no results.by_outcome mapping": stats.get("object with no results.by_outcome mapping", 0),
        "outcome in results.by_outcome": stats.get("outcome in results.by_outcome", 0),
        "outcome with no GRADE record": stats.get("outcome with no GRADE record", 0),
        "outcome with GRADE record examined": stats.get("outcome with GRADE record examined", 0),
        "GRADE record with no imprecision downgrade step":
            stats.get("GRADE record with no imprecision downgrade step", 0),
        "outcome with imprecision downgrade step":
            stats.get("outcome with imprecision downgrade step", 0),
        "imprecision downgrade with threshold recorded":
            stats.get("imprecision downgrade with threshold recorded", 0),
        "imprecision downgrade WITHOUT threshold -- finding":
            stats.get("imprecision downgrade WITHOUT threshold -- finding", 0),
    })

    visible = stats.get("outcome with GRADE record examined", 0)
    if not paths:
        coverage_note = "no ssot topic objects found; cannot prove corpus absence"
    elif population == 0:
        coverage_note = "no results.by_outcome outcomes found; cannot prove corpus absence"
    elif imprecision_step_outcomes == 0:
        coverage_note = "no imprecision downgrades in the corpus"
    elif len(findings) == 0:
        coverage_note = ("%d imprecision downgrade outcome(s) were examined and every one "
                         "recorded a threshold" % imprecision_step_outcomes)
    else:
        coverage_note = ("%d imprecision downgrade outcome(s) were examined; %d lack a "
                         "threshold" % (imprecision_step_outcomes, len(findings)))
    gate.coverage(visible, population,
                  "%d result outcome(s) carry no GRADE record for this gate to assess; %s"
                  % (max(population - visible, 0), coverage_note))
    return gate.report(denominator="%d imprecision-downgrade GRADE outcome(s) across %d topic object(s)"
                                   % (imprecision_step_outcomes,
                                      len(paths)))


if __name__=="__main__":
    sys.exit(main(sys.argv[1:]))
