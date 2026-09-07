import sys,os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _harness as H
import re


def main(argv):
    name = "SELF-REFERENCE BENCHMARK"
    what = "an external benchmark must not be a subset of the pooled trials"
    gate=H.Gate(name,what)
    gate.expect_case("PINNED_POSITIVE",
                     "claimed-independent benchmark whose trials equal the pooled trials fires")
    gate.requires_control()

    pos = scan_object("__control_positive__", positive_control())
    neg = scan_object("__control_negative__", negative_control())
    if len(pos["findings"]) == 1:
        gate.saw("PINNED_POSITIVE")
    else:
        gate.broken("positive control should fire once, got %d" % len(pos["findings"]))
    n_neg = 1
    n_fp = len(neg["findings"])
    examples = [f["key"] for f in neg["findings"][:5]]
    gate.control(n_neg,n_fp,examples,accuses=True)

    repo = H.repo_root()
    paths, path_kinds = H.topic_objects(repo)
    totals = empty_counts()
    findings = []
    load_failures = []

    if not paths:
        gate.broken("0 topic objects found under ssot/*/*.json where basename[:-5] == dirname")

    for path in paths:
        try:
            obj = H.load(path)
        except Exception as e:
            load_failures.append("%s: %s" % (path, e))
            continue
        scanned = scan_object(H.topic_id(path), obj)
        add_counts(totals, scanned["counts"])
        findings.extend(scanned["findings"])

    for item in load_failures[:5]:
        gate.broken("could not read topic object: %s" % item)

    gate.kinds({
        "topic object (ssot/<t>/<t>.json)": path_kinds.get(
            "topic object (ssot/<t>/<t>.json)", 0),
        "other json under ssot/<t>/": path_kinds.get("other json under ssot/<t>/", 0),
        "outcomes reached": totals["outcomes"],
        "outcomes with no claimed-independent external benchmark": totals["not_claimed"],
        "claimed-independent external benchmark outcomes": totals["claimed"],
        "claimed outcomes with pooled per_trial NCTs and benchmark NCTs": totals["assessable"],
        "claimed outcomes missing pooled per_trial NCTs": totals["missing_pooled_ncts"],
        "claimed outcomes missing benchmark NCTs": totals["missing_benchmark_ncts"],
        "self-reference benchmark firings": len(findings),
    })
    gate.coverage(totals["assessable"], totals["claimed"],
                  "claimed-independent external benchmark outcomes without both explicit "
                  "benchmark NCTs and pooled per_trial NCTs; this gate cannot decide overlap")
    gate.note("controls: positive fires=%d; negative fires=%d" %
              (len(pos["findings"]), len(neg["findings"])))
    gate.note("corpus finding count: %d" % len(findings))

    for f in findings:
        gate.finding(
            "SELF-REFERENCE-BENCHMARK",
            "%s %s claims an independent external benchmark (%s), but benchmark NCTs %s "
            "are a subset of the pooled per_trial NCTs %s. Present it as a same-trials "
            "cross-check, not independent external evidence."
            % (f["topic"], f["outcome"], f["benchmark_key"],
               ", ".join(sorted(f["benchmark_ncts"])),
               ", ".join(sorted(f["pooled_ncts"]))),
            numerator=len(f["benchmark_ncts"]),
            denominator=len(f["pooled_ncts"]))

    return gate.report(denominator="%d topic objects; %d claimed-independent benchmark "
                                   "outcomes; %d corpus findings"
                       % (len(paths), totals["claimed"], len(findings)))


NCT_RE = re.compile(r"\bNCT\d{8}\b", re.I)
BENCHMARK_KEYS = {
    "external_benchmark",
    "external_benchmark_2026_09_07",
}
TRIAL_SET_KEYS = {
    "trial",
    "trials",
    "trial_set",
    "trial_sets",
    "trial_nct",
    "trial_ncts",
    "trial_id",
    "trial_ids",
    "nct",
    "ncts",
    "nct_id",
    "nct_ids",
    "registration",
    "registrations",
    "registration_id",
    "registration_ids",
    "included_trials",
    "included_studies",
    "studies",
    "study_ids",
}
PER_TRIAL_ID_KEYS = {
    "nct",
    "nct_id",
    "trial_id",
    "registration",
    "registration_id",
    "ctgov_id",
    "clinicaltrials_id",
    "source_url",
}


def empty_counts():
    return {
        "outcomes": 0,
        "not_claimed": 0,
        "claimed": 0,
        "assessable": 0,
        "missing_pooled_ncts": 0,
        "missing_benchmark_ncts": 0,
    }


def add_counts(dst, src):
    for key, value in src.items():
        dst[key] = dst.get(key, 0) + value


def positive_control():
    return {"results": {"by_outcome": {"primary": {
        "per_trial": [
            {"nct": "NCT00000001", "point": 0.8},
            {"nct": "NCT00000002", "point": 0.9},
        ],
        "external_benchmark": {
            "independent_external_exists": True,
            "name": "independent external benchmark",
            "trials": ["NCT00000001", "NCT00000002"],
        },
    }}}}


def negative_control():
    return {"results": {"by_outcome": {"primary": {
        "per_trial": [
            {"nct": "NCT00000001", "point": 0.8},
            {"nct": "NCT00000002", "point": 0.9},
        ],
        "external_benchmark": {
            "independent_external_exists": True,
            "name": "disjoint independent external benchmark",
            "trials": ["NCT00000003", "NCT00000004"],
        },
    }}}}


def scan_object(topic, obj):
    out = {"counts": empty_counts(), "findings": []}
    outcomes = ((obj.get("results") or {}).get("by_outcome") or {})
    if not isinstance(outcomes, dict):
        return out

    for outcome_id, outcome in outcomes.items():
        if not isinstance(outcome, dict):
            continue
        out["counts"]["outcomes"] += 1
        benches = list(iter_benchmarks(outcome))
        claimed = [(key, bench) for key, bench in benches if claims_independent(bench)]
        if not claimed:
            out["counts"]["not_claimed"] += 1
            continue

        pooled_ncts = pooled_per_trial_ncts(outcome.get("per_trial") or [])
        for key, bench in claimed:
            out["counts"]["claimed"] += 1
            benchmark_ncts = benchmark_trial_ncts(bench)
            if not pooled_ncts:
                out["counts"]["missing_pooled_ncts"] += 1
                continue
            if not benchmark_ncts:
                out["counts"]["missing_benchmark_ncts"] += 1
                continue
            out["counts"]["assessable"] += 1
            if benchmark_ncts <= pooled_ncts:
                out["findings"].append({
                    "key": "%s|results.by_outcome.%s|%s" % (topic, outcome_id, key),
                    "topic": topic,
                    "outcome": "results.by_outcome.%s" % outcome_id,
                    "benchmark_key": key,
                    "pooled_ncts": pooled_ncts,
                    "benchmark_ncts": benchmark_ncts,
                })
    return out


def iter_benchmarks(outcome):
    for key, value in outcome.items():
        if key in BENCHMARK_KEYS or key.startswith("external_benchmark_"):
            if isinstance(value, dict):
                yield key, value


def claims_independent(bench):
    explicit = as_bool(bench.get("independent_external_exists"))
    if explicit is False:
        return False
    if explicit is True:
        return True
    return bool(str(bench.get("name") or "").strip())


def as_bool(value):
    if value is True or value is False:
        return value
    if isinstance(value, str):
        text = value.strip().casefold()
        if text in ("true", "yes", "y", "1"):
            return True
        if text in ("false", "no", "n", "0"):
            return False
    return None


def pooled_per_trial_ncts(rows):
    found = set()
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        row_ids = set()
        for key, value in row.items():
            if key in PER_TRIAL_ID_KEYS:
                row_ids.update(ncts_in(value))
        if not row_ids:
            row_ids.update(ncts_in(row))
        found.update(row_ids)
    return found


def benchmark_trial_ncts(bench):
    found = set()
    for key, value in bench.items():
        if key in TRIAL_SET_KEYS or key.startswith("trial_") or key.startswith("nct_"):
            found.update(ncts_in(value))
    return found


def ncts_in(value):
    found = set()
    if value is None:
        return found
    if isinstance(value, str):
        return {m.group(0).upper() for m in NCT_RE.finditer(value)}
    if isinstance(value, dict):
        for nested in value.values():
            found.update(ncts_in(nested))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(ncts_in(nested))
    return found


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
