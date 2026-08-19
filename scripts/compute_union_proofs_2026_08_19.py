#!/usr/bin/env python3
"""Independently compute union proofs for the 2026-08-19 merge clusters.

This script intentionally does not import scripts/execute_merges_2026_08_19.py.
It recomputes the proof surface from the adjudication file and the current SSOT
JSON objects only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
EV = REPO / "evidence" / "2026-08-19-batch1"
ADJ = EV / "merge_adjudication.json"
PAGE_MAP = REPO / "ssot" / "PAGE_MAP.json"
DEST = EV / "union_proofs_independent.json"
DATE = "2026-08-19"
EXPECTED_MERGE_CLUSTERS = 12


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def leaves(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, f"{path}/{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            yield from leaves(child, f"{path}[{idx}]")
    else:
        yield path, value


def topic_path(topic: str) -> Path:
    return REPO / "ssot" / topic / f"{topic}.json"


def page_for(topic: str, page_map: dict[str, str]) -> str | None:
    suffix = f"/{topic}.json"
    for page, rel in page_map.items():
        normalized = rel.replace("\\", "/")
        if normalized.endswith(suffix):
            return page
    return None


def trial_ids(obj: dict[str, Any]) -> list[str]:
    trials = ((obj.get("inputs") or {}).get("trials") or [])
    ids: set[str] = set()
    for trial in trials:
        if not isinstance(trial, dict):
            continue
        tid = trial.get("nct") or trial.get("id") or trial.get("registration")
        if tid:
            ids.add(str(tid))
    return sorted(ids)


def unwrap_original_payload(current_retired: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    obj = current_retired
    while (
        isinstance(obj, dict)
        and str(obj.get("state") or "").upper() == "RETIRED"
        and isinstance(obj.get("THE_OBJECT_AS_IT_STOOD_AT_RETIREMENT"), dict)
    ):
        chain.append(obj)
        obj = obj["THE_OBJECT_AS_IT_STOOD_AT_RETIREMENT"]
    source_kind = "live_object" if not chain else "tombstone_chain_unwrapped_original"
    return obj, {
        "source_kind": source_kind,
        "tombstone_depth": len(chain),
        "outer_absorbed_by": chain[0].get("absorbed_by") if chain else None,
        "outer_trials_it_held": sorted(str(x) for x in chain[0].get("trials_it_held", []))
        if chain
        else [],
        "chain_sha256": [canonical_sha256(item) for item in chain],
    }


def find_equal_subtrees(value: Any, target: Any, path: str = "") -> list[str]:
    found: list[str] = []
    if value == target:
        found.append(path or "/")
    if isinstance(value, dict):
        for key, child in value.items():
            found.extend(find_equal_subtrees(child, target, f"{path}/{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            found.extend(find_equal_subtrees(child, target, f"{path}[{idx}]"))
    return found


def classify_absorbed_payload(
    survivor_obj: dict[str, Any],
    retired_topic: str,
    original_obj: dict[str, Any],
) -> dict[str, Any]:
    absorbed = survivor_obj.get("absorbed_topics")
    if not isinstance(absorbed, dict) or retired_topic not in absorbed:
        return {
            "absorbed_block_present": False,
            "payload_kind": "absent",
            "direct_payload_verbatim": False,
            "recoverable_original_verbatim": False,
            "recoverable_original_locations": [],
        }

    block = absorbed.get(retired_topic)
    payload = block.get("THE_WHOLE_OBJECT_VERBATIM") if isinstance(block, dict) else None
    direct = payload == original_obj
    payload_locations = find_equal_subtrees(payload, original_obj) if payload is not None else []
    nested = bool(payload_locations) and not direct
    if direct:
        kind = "direct_original"
    elif nested:
        kind = "payload_contains_original"
    elif payload is None:
        kind = "missing_payload"
    else:
        kind = "payload_mismatch"
    return {
        "absorbed_block_present": True,
        "payload_kind": kind,
        "direct_payload_verbatim": direct,
        "recoverable_original_verbatim": direct or nested,
        "original_locations_inside_payload": payload_locations,
        "recoverable_original_locations": find_equal_subtrees(survivor_obj, original_obj),
    }


def proof_for_retired(
    row: dict[str, Any],
    survivor_obj: dict[str, Any],
    retired_topic: str,
) -> dict[str, Any]:
    current_retired = load_json(topic_path(retired_topic))
    original_obj, source_info = unwrap_original_payload(current_retired)
    source_kind = source_info["source_kind"]
    original_leaf_paths = [path for path, _ in leaves(original_obj)]
    original_trials = trial_ids(original_obj)
    survivor_trials = trial_ids(survivor_obj)
    missing_trials = sorted(set(original_trials) - set(survivor_trials))

    current_locations = find_equal_subtrees(survivor_obj, original_obj)
    absorbed = classify_absorbed_payload(survivor_obj, retired_topic, original_obj)

    simulated = copy.deepcopy(survivor_obj)
    simulated.setdefault("absorbed_topics", {})[retired_topic] = {
        "THE_WHOLE_OBJECT_VERBATIM": original_obj
    }
    simulated_locations = find_equal_subtrees(simulated, original_obj)

    tombstone_checks: dict[str, Any] = {
        "is_tombstone": source_kind == "tombstone_chain_unwrapped_original",
        "tombstone_depth": source_info["tombstone_depth"],
    }
    if source_kind == "tombstone_chain_unwrapped_original":
        tombstone_checks.update(
            {
                "outer_absorbed_by": source_info["outer_absorbed_by"],
                "outer_absorbed_by_matches_survivor": source_info["outer_absorbed_by"]
                == row["survivor"],
                "outer_trials_it_held_matches_original": source_info["outer_trials_it_held"]
                == original_trials,
                "chain_sha256": source_info["chain_sha256"],
            }
        )

    return {
        "retired": retired_topic,
        "source_used_for_retired_object": source_kind,
        "original_object_sha256": canonical_sha256(original_obj),
        "leaves_in_original_retired_object": len(original_leaf_paths),
        "original_trial_ids": original_trials,
        "survivor_trial_ids": survivor_trials,
        "trials_not_in_survivor_inputs": missing_trials,
        "current_survivor_contains_original_verbatim": bool(current_locations),
        "current_original_locations": current_locations,
        "absorbed_payload": absorbed,
        "simulated_absorption_contains_original_verbatim": bool(simulated_locations),
        "simulated_original_locations": simulated_locations,
        "current_union_proven": bool(current_locations) and not missing_trials,
        "simulated_union_proven": bool(simulated_locations) and not missing_trials,
        "tombstone_checks": tombstone_checks,
    }


def build_report() -> dict[str, Any]:
    adjudication = load_json(ADJ)
    page_map = load_json(PAGE_MAP)
    merge_rows = [row for row in adjudication["rows"] if row["verdict"].startswith("MERGE")]
    non_merge_rows = [
        {"cluster": row["cluster"], "verdict": row["verdict"]}
        for row in adjudication["rows"]
        if not row["verdict"].startswith("MERGE")
    ]

    rows: list[dict[str, Any]] = []
    for row in merge_rows:
        survivor = row["survivor"]
        survivor_obj = load_json(topic_path(survivor))
        survivor_page = page_for(survivor, page_map)
        proofs = [proof_for_retired(row, survivor_obj, retired) for retired in row["retire"]]
        current_all = all(proof["current_union_proven"] for proof in proofs)
        simulated_all = all(proof["simulated_union_proven"] for proof in proofs)
        if current_all:
            status = "CURRENT_UNION_PROVEN"
        elif simulated_all:
            status = "NOT_CURRENTLY_ABSORBED_BUT_SIMULATED_UNION_PROVEN"
        else:
            status = "UNION_PROOF_FAILED"
        rows.append(
            {
                "cluster": row["cluster"],
                "survivor": survivor,
                "retire": row["retire"],
                "survivor_page": survivor_page,
                "survivor_page_exists": bool(survivor_page and (REPO / survivor_page).exists()),
                "status": status,
                "proofs": proofs,
            }
        )

    retired_proofs = [proof for row in rows for proof in row["proofs"]]
    return {
        "computed_utc": DATE,
        "independence_statement": (
            "Computed from merge_adjudication.json plus current SSOT JSON files. "
            "This script does not import or execute the merge executor."
        ),
        "proof_rule": (
            "For each MERGE cluster, the retired object's original payload is taken from "
            "THE_OBJECT_AS_IT_STOOD_AT_RETIREMENT when the topic is already a RETIRED "
            "tombstone, otherwise from the live topic object. Current union is proven only "
            "when that original object exists verbatim somewhere in the survivor and every "
            "retired trial id is present in survivor inputs.trials. Deferred clusters also "
            "get a simulated absorption check without writing files."
        ),
        "counts": {
            "expected_merge_clusters": EXPECTED_MERGE_CLUSTERS,
            "merge_clusters_checked": len(rows),
            "retired_topic_proofs_checked": len(retired_proofs),
            "non_merge_clusters_excluded": len(non_merge_rows),
            "clusters_current_union_proven": sum(
                1 for row in rows if row["status"] == "CURRENT_UNION_PROVEN"
            ),
            "clusters_deferred_or_not_currently_absorbed_but_simulated_proven": sum(
                1
                for row in rows
                if row["status"] == "NOT_CURRENTLY_ABSORBED_BUT_SIMULATED_UNION_PROVEN"
            ),
            "clusters_failed": sum(1 for row in rows if row["status"] == "UNION_PROOF_FAILED"),
            "retired_topics_current_union_proven": sum(
                1 for proof in retired_proofs if proof["current_union_proven"]
            ),
            "retired_topics_simulated_union_proven": sum(
                1 for proof in retired_proofs if proof["simulated_union_proven"]
            ),
            "absorbed_payload_direct_original": sum(
                1
                for proof in retired_proofs
                if proof["absorbed_payload"]["payload_kind"] == "direct_original"
            ),
            "absorbed_payload_contains_original": sum(
                1
                for proof in retired_proofs
                if proof["absorbed_payload"]["payload_kind"] == "payload_contains_original"
            ),
            "absorbed_payload_absent": sum(
                1 for proof in retired_proofs if proof["absorbed_payload"]["payload_kind"] == "absent"
            ),
        },
        "expectation_checks": {
            "merge_cluster_count_is_expected": len(rows) == EXPECTED_MERGE_CLUSTERS,
            "no_union_proof_failures": all(
                row["status"] != "UNION_PROOF_FAILED" for row in rows
            ),
            "all_retired_topics_simulated_union_proven": all(
                proof["simulated_union_proven"] for proof in retired_proofs
            ),
        },
        "hardcode_disclosure": [
            {
                "item": "DATE",
                "classification": "static run stamp",
                "value": DATE,
                "reason": "The batch being audited is dated 2026-08-19.",
            },
            {
                "item": "EXPECTED_MERGE_CLUSTERS",
                "classification": "static guard",
                "value": EXPECTED_MERGE_CLUSTERS,
                "reason": "The user requested exactly twelve merge-cluster proofs.",
            },
            {
                "item": "cluster members, survivors, retired topics, object payloads, trials, pages",
                "classification": "dynamic",
                "value": "read from merge_adjudication.json, PAGE_MAP.json, and ssot/*/*.json",
                "reason": "No proof result is hardcoded.",
            },
        ],
        "non_merge_clusters_excluded": non_merge_rows,
        "rows": rows,
    }


def selftest() -> int:
    original = {"app_id": "retired", "inputs": {"trials": [{"nct": "NCT1"}]}, "x": [1, None]}
    survivor = {"inputs": {"trials": [{"nct": "NCT1"}]}}
    row = {"survivor": "survivor"}

    simulated = copy.deepcopy(survivor)
    simulated.setdefault("absorbed_topics", {})["retired"] = {
        "THE_WHOLE_OBJECT_VERBATIM": original
    }
    checks = [
        ("hash stable", canonical_sha256(original) == canonical_sha256(copy.deepcopy(original))),
        ("finds inserted original", bool(find_equal_subtrees(simulated, original))),
        (
            "classifies direct original",
            classify_absorbed_payload(simulated, "retired", original)["payload_kind"]
            == "direct_original",
        ),
        (
            "classifies payload containing original",
            classify_absorbed_payload(
                {
                    "absorbed_topics": {
                        "retired": {
                            "THE_WHOLE_OBJECT_VERBATIM": {
                                "state": "RETIRED",
                                "THE_OBJECT_AS_IT_STOOD_AT_RETIREMENT": original,
                            }
                        }
                    }
                },
                "retired",
                original,
            )["payload_kind"]
            == "payload_contains_original",
        ),
        (
            "trial ids read",
            trial_ids(original) == ["NCT1"] and trial_ids({"inputs": {"trials": []}}) == [],
        ),
        ("row shape independent", row["survivor"] == "survivor"),
    ]
    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"{name}: {'ok' if ok else 'FAIL'}")
    if failed:
        print("SELFTEST FAILED: " + ", ".join(failed))
        return 1
    print("SELFTEST PASSED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help=f"write {DEST.relative_to(REPO)}")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    report = build_report()
    text = json.dumps(report, indent=1, ensure_ascii=False)
    if args.write:
        DEST.write_text(text + "\n", encoding="utf-8")
    counts = report["counts"]
    print(json.dumps(counts, indent=1, ensure_ascii=False))
    for row in report["rows"]:
        print(f"{row['status']}: {row['survivor']} <- {', '.join(row['retire'])}")
        for proof in row["proofs"]:
            print(
                "  {retired}: {leaves} leaves, current={current}, simulated={simulated}, "
                "payload={payload}, missing_trials={missing}".format(
                    retired=proof["retired"],
                    leaves=proof["leaves_in_original_retired_object"],
                    current=proof["current_union_proven"],
                    simulated=proof["simulated_union_proven"],
                    payload=proof["absorbed_payload"]["payload_kind"],
                    missing=len(proof["trials_not_in_survivor_inputs"]),
                )
            )
    expectations = report["expectation_checks"]
    return 1 if counts["clusters_failed"] or not all(expectations.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
