"""Join AACT baseline population rows to held trial NCTs.

The script reads each local AACT input once, assigns exactly one verdict per
distinct validation-trial NCT, prints mandatory controls, and writes a JSON
artifact for downstream transferability checks.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SNAPSHOT_DATE = "2026-08-30"
OUTPUT_DATE = "2026-09-01"

REPO = Path(__file__).resolve().parent.parent
VALIDATION_DIR = REPO / "outputs" / "r_validation"
OUTPUT_PATH = REPO / "outputs" / f"populations_join_{OUTPUT_DATE}.json"

AACT_FILES = {
    "baseline_measurements": "baseline_measurements.txt",
    "baseline_counts": "baseline_counts.txt",
    "eligibilities": "eligibilities.txt",
}

VERDICT_ORDER = [
    "USABLE",
    "ROWS_BUT_THIN",
    "CANNOT_ASSESS",
    "NO_BASELINE",
    "NOT_IN_AACT",
]

CONTROL_EXPECTED = {
    "NCT02171429": "CANNOT_ASSESS",
    "NCT00818883": "USABLE",
}

NCT_RE = re.compile(r"^NCT\d{8}$")
MULTI_POPULATION_RE = re.compile(
    r"two populations|both populations|presented for .{0,40} populations|two analysis sets",
    re.IGNORECASE,
)
AGE_RE = re.compile(r"\bage\b", re.IGNORECASE)
SEX_RE = re.compile(r"\b(sex|gender)\b", re.IGNORECASE)
REGION_RE = re.compile(
    r"\b(region|country|countries|geographic|geographical)\b",
    re.IGNORECASE,
)


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def resolve_aact_dir() -> Path:
    candidates: list[Path] = []
    env = os.environ.get("AACT_ROOT")
    if env:
        candidates.append(Path(env))
    for drive in ("F", "D", "C"):
        candidates.append(Path(f"{drive}:/") / "AACT-storage" / "AACT" / SNAPSHOT_DATE)

    for candidate in candidates:
        if all((candidate / name).exists() for name in AACT_FILES.values()):
            return candidate

    tried = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "AACT snapshot not found. Set AACT_ROOT to the directory containing "
        f"{', '.join(AACT_FILES.values())}. Tried: {tried}"
    )


def normalize_nct(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    nct = value.strip().upper()
    if NCT_RE.fullmatch(nct):
        return nct
    return None


def load_held_trials() -> tuple[dict[str, set[str]], dict[str, Any]]:
    report_map: dict[str, set[str]] = defaultdict(set)
    files_seen = 0
    files_with_trials = 0
    malformed_files: list[dict[str, str]] = []
    skipped_trial_values = 0

    for path in sorted(VALIDATION_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        files_seen += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            malformed_files.append(
                {"path": path.relative_to(REPO).as_posix(), "error": str(exc)}
            )
            continue

        trials = payload.get("trials")
        if not isinstance(trials, list):
            continue
        files_with_trials += 1

        rel_path = path.relative_to(REPO).as_posix()
        for trial in trials:
            if not isinstance(trial, dict):
                skipped_trial_values += 1
                continue
            nct = normalize_nct(trial.get("nct"))
            if nct is None:
                skipped_trial_values += 1
                continue
            report_map[nct].add(rel_path)

    meta = {
        "validation_json_files_seen": files_seen,
        "validation_json_files_with_trials": files_with_trials,
        "malformed_validation_files": malformed_files,
        "skipped_trial_values": skipped_trial_values,
    }
    return report_map, meta


def empty_state() -> dict[str, Any]:
    return {
        "present_in_aact": False,
        "baseline_measurement_rows": 0,
        "baseline_count_rows": 0,
        "eligibility_rows": 0,
        "has_age": False,
        "has_sex": False,
        "has_region": False,
        "feature_sources": set(),
        "multi_population_prose": False,
        "multi_population_evidence": [],
    }


def fast_nct_from_line(line: str) -> str | None:
    parts = line.split("|", 2)
    if len(parts) < 2:
        return None
    nct = parts[1].strip().upper()
    if NCT_RE.fullmatch(nct):
        return nct
    return None


def require_columns(header: list[str], required: list[str], table: str) -> dict[str, int]:
    col = {name: i for i, name in enumerate(header)}
    missing = [name for name in required if name not in col]
    if missing:
        raise ValueError(f"{table} missing required columns: {', '.join(missing)}")
    return col


def value_at(parts: list[str], col: dict[str, int], name: str) -> str:
    idx = col[name]
    if idx >= len(parts):
        return ""
    return parts[idx]


def feature_text(parts: list[str], col: dict[str, int]) -> str:
    names = [
        "classification",
        "category",
        "title",
        "description",
        "units",
        "number_analyzed_units",
        "population_description",
    ]
    return " ".join(value_at(parts, col, name) for name in names)


def short_snippet(line: str, match: re.Match[str], width: int = 110) -> str:
    start = max(0, match.start() - width)
    end = min(len(line), match.end() + width)
    snippet = line[start:end].strip()
    return re.sub(r"\s+", " ", snippet)


def stream_baseline_measurements(
    path: Path,
    targets: set[str],
    states: dict[str, dict[str, Any]],
    control_rows: dict[str, dict[str, list[str]]],
) -> dict[str, int]:
    scanned = 0
    matched = 0

    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        header = handle.readline().rstrip("\r\n").split("|")
        col = require_columns(
            header,
            [
                "nct_id",
                "classification",
                "category",
                "title",
                "description",
                "units",
                "number_analyzed_units",
                "population_description",
            ],
            path.name,
        )
        if col["nct_id"] != 1:
            raise ValueError(f"{path.name} nct_id column was {col['nct_id']}, expected 1")

        for line in handle:
            scanned += 1
            nct = fast_nct_from_line(line)
            if nct not in targets:
                continue

            matched += 1
            state = states[nct]
            state["present_in_aact"] = True
            state["baseline_measurement_rows"] += 1

            raw = line.rstrip("\r\n")
            if nct in CONTROL_EXPECTED:
                control_rows[nct]["baseline_measurements"].append(raw)

            multi_match = MULTI_POPULATION_RE.search(raw)
            if multi_match:
                state["multi_population_prose"] = True
                if len(state["multi_population_evidence"]) < 5:
                    state["multi_population_evidence"].append(
                        {
                            "table": "baseline_measurements",
                            "match": multi_match.group(0),
                            "snippet": short_snippet(raw, multi_match),
                        }
                    )

            parts = raw.split("|")
            text = feature_text(parts, col)
            if AGE_RE.search(text):
                state["has_age"] = True
                state["feature_sources"].add("age")
            if SEX_RE.search(text):
                state["has_sex"] = True
                state["feature_sources"].add("sex")
            if REGION_RE.search(text):
                state["has_region"] = True
                state["feature_sources"].add("region")

    return {"scanned": scanned, "matched": matched}


def stream_baseline_counts(
    path: Path,
    targets: set[str],
    states: dict[str, dict[str, Any]],
    control_rows: dict[str, dict[str, list[str]]],
) -> dict[str, int]:
    scanned = 0
    matched = 0

    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        header = handle.readline().rstrip("\r\n").split("|")
        col = require_columns(header, ["nct_id"], path.name)
        if col["nct_id"] != 1:
            raise ValueError(f"{path.name} nct_id column was {col['nct_id']}, expected 1")

        for line in handle:
            scanned += 1
            nct = fast_nct_from_line(line)
            if nct not in targets:
                continue

            matched += 1
            state = states[nct]
            state["present_in_aact"] = True
            state["baseline_count_rows"] += 1
            if nct in CONTROL_EXPECTED:
                control_rows[nct]["baseline_counts"].append(line.rstrip("\r\n"))

    return {"scanned": scanned, "matched": matched}


def stream_eligibilities(
    path: Path,
    targets: set[str],
    states: dict[str, dict[str, Any]],
) -> dict[str, int]:
    scanned = 0
    matched = 0

    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        header = handle.readline().rstrip("\r\n").split("|")
        col = require_columns(header, ["nct_id"], path.name)
        if col["nct_id"] != 1:
            raise ValueError(f"{path.name} nct_id column was {col['nct_id']}, expected 1")

        for line in handle:
            scanned += 1
            nct = fast_nct_from_line(line)
            if nct not in targets:
                continue

            matched += 1
            state = states[nct]
            state["present_in_aact"] = True
            state["eligibility_rows"] += 1

    return {"scanned": scanned, "matched": matched}


def verdict_for(state: dict[str, Any]) -> str:
    baseline_rows = state["baseline_measurement_rows"] + state["baseline_count_rows"]
    if not state["present_in_aact"]:
        return "NOT_IN_AACT"
    if baseline_rows == 0:
        return "NO_BASELINE"
    if state["multi_population_prose"]:
        return "CANNOT_ASSESS"
    if state["has_age"] or state["has_sex"] or state["has_region"]:
        return "USABLE"
    return "ROWS_BUT_THIN"


def print_control_rows(nct: str, rows_by_table: dict[str, list[str]]) -> None:
    print(f"CONTROL_ROWS {nct}")
    for table in ("baseline_measurements", "baseline_counts"):
        rows = rows_by_table.get(table, [])
        print(f"  {table}: {len(rows)} row(s)")
        if not rows:
            print("    (none)")
            continue
        for row in rows:
            print(f"    {row}")


def fallback_output_paths() -> list[Path]:
    candidates: list[Path] = []
    env_path = os.environ.get("POPULATION_JOIN_FALLBACK_OUTPUT")
    if env_path:
        candidates.append(Path(env_path))

    for drive in ("F", "D", "C"):
        candidate_dir = Path(f"{drive}:/") / "tmp"
        if candidate_dir.exists():
            candidates.append(candidate_dir / OUTPUT_PATH.name)

    tmp = os.environ.get("TMP") or os.environ.get("TEMP")
    if tmp:
        candidates.append(Path(tmp) / OUTPUT_PATH.name)

    candidates.append(REPO / OUTPUT_PATH.name)
    return candidates


def write_payload(payload: dict[str, Any]) -> tuple[Path, Path | None, str | None]:
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    try:
        OUTPUT_PATH.write_text(data, encoding="utf-8")
        return OUTPUT_PATH, None, None
    except OSError as exc:
        errors = [f"requested {OUTPUT_PATH}: {exc.__class__.__name__}: {exc}"]
        for fallback_path in fallback_output_paths():
            try:
                fallback_path.parent.mkdir(parents=True, exist_ok=True)
                fallback_path.write_text(data, encoding="utf-8")
                return fallback_path, OUTPUT_PATH, "; ".join(errors)
            except OSError as fallback_exc:
                errors.append(
                    f"fallback {fallback_path}: "
                    f"{fallback_exc.__class__.__name__}: {fallback_exc}"
                )
        raise OSError("; ".join(errors)) from exc


def serializable_trial_record(
    nct: str,
    state: dict[str, Any],
    reports: set[str],
    verdict: str,
) -> dict[str, Any]:
    return {
        "nct": nct,
        "verdict": verdict,
        "present_in_aact": state["present_in_aact"],
        "baseline_measurement_rows": state["baseline_measurement_rows"],
        "baseline_count_rows": state["baseline_count_rows"],
        "eligibility_rows": state["eligibility_rows"],
        "baseline_rows": state["baseline_measurement_rows"] + state["baseline_count_rows"],
        "features": {
            "age": state["has_age"],
            "sex": state["has_sex"],
            "region": state["has_region"],
        },
        "feature_sources": sorted(state["feature_sources"]),
        "multi_population_prose": state["multi_population_prose"],
        "multi_population_evidence": state["multi_population_evidence"],
        "reports": sorted(reports),
    }


def main() -> int:
    configure_stdout()
    aact_dir = resolve_aact_dir()
    report_map, trial_meta = load_held_trials()
    targets = set(report_map)

    states = {nct: empty_state() for nct in targets}
    control_rows: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    print(
        "TRIAL_INPUT "
        f"validation_json_files={trial_meta['validation_json_files_seen']} "
        f"files_with_trials={trial_meta['validation_json_files_with_trials']} "
        f"distinct_ncts={len(targets)}"
    )
    if trial_meta["malformed_validation_files"]:
        print("MALFORMED_VALIDATION_FILES")
        for item in trial_meta["malformed_validation_files"]:
            print(f"  {item['path']}: {item['error']}")
    if trial_meta["skipped_trial_values"]:
        print(f"SKIPPED_TRIAL_VALUES {trial_meta['skipped_trial_values']}")

    bm_stats = stream_baseline_measurements(
        aact_dir / AACT_FILES["baseline_measurements"],
        targets,
        states,
        control_rows,
    )
    print(
        "STREAM baseline_measurements "
        f"scanned={bm_stats['scanned']} matched={bm_stats['matched']}"
    )

    bc_stats = stream_baseline_counts(
        aact_dir / AACT_FILES["baseline_counts"],
        targets,
        states,
        control_rows,
    )
    print(
        "STREAM baseline_counts "
        f"scanned={bc_stats['scanned']} matched={bc_stats['matched']}"
    )

    eligibility_stats = stream_eligibilities(
        aact_dir / AACT_FILES["eligibilities"],
        targets,
        states,
    )
    print(
        "STREAM eligibilities "
        f"scanned={eligibility_stats['scanned']} matched={eligibility_stats['matched']}"
    )

    verdicts = {nct: verdict_for(state) for nct, state in states.items()}
    distribution = Counter(verdicts.values())
    appear_in_aact = sum(1 for state in states.values() if state["present_in_aact"])

    print(
        "DENOMINATOR "
        f"distinct_ncts_held={len(targets)} "
        f"appear_in_aact_at_all={appear_in_aact} "
        f"decided={len(verdicts)}"
    )

    controls_passed = True
    for nct, expected in CONTROL_EXPECTED.items():
        observed = verdicts.get(nct, "NOT_HELD")
        status = "PASS" if observed == expected else "FAIL"
        print(f"CONTROL {nct} expected={expected} observed={observed} {status}")
        if status == "FAIL":
            controls_passed = False
            print_control_rows(nct, control_rows[nct])

    if not controls_passed:
        print("ABORTED controls_failed=true distribution_not_reported=true")
        return 2

    print("DISTRIBUTION")
    for verdict in VERDICT_ORDER:
        print(f"  {verdict}={distribution.get(verdict, 0)}")

    records = {
        nct: serializable_trial_record(nct, states[nct], report_map[nct], verdicts[nct])
        for nct in sorted(targets)
    }
    payload = {
        "generated_on": OUTPUT_DATE,
        "aact_snapshot_date": SNAPSHOT_DATE,
        "inputs": {
            "validation_dir": VALIDATION_DIR.relative_to(REPO).as_posix(),
            "aact_dir": str(aact_dir),
            **AACT_FILES,
        },
        "denominator": {
            "distinct_ncts_held": len(targets),
            "appear_in_aact_at_all": appear_in_aact,
            "decided": len(verdicts),
        },
        "controls": {
            nct: {
                "expected": expected,
                "observed": verdicts.get(nct, "NOT_HELD"),
                "passed": verdicts.get(nct) == expected,
            }
            for nct, expected in CONTROL_EXPECTED.items()
        },
        "distribution": {verdict: distribution.get(verdict, 0) for verdict in VERDICT_ORDER},
        "trial_input_meta": trial_meta,
        "stream_stats": {
            "baseline_measurements": bm_stats,
            "baseline_counts": bc_stats,
            "eligibilities": eligibility_stats,
        },
        "trials": records,
    }
    written_path, requested_path, write_error = write_payload(payload)
    if requested_path is None:
        print(f"WROTE {written_path.relative_to(REPO).as_posix()}")
    else:
        print(
            "WRITE_ERROR "
            f"requested={requested_path.relative_to(REPO).as_posix()} "
            f"error={write_error}"
        )
        print(f"WROTE_FALLBACK {written_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
