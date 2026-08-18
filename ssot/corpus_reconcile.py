"""ID-keyed reconciliation across the SSOT corpus.

This is pure computation over files already on disk. It intentionally does not import
batch1_assess.py because that module writes its own output at import time. The two reader
functions below are the same inclusion/removal logic: included trials come only from
inputs.trials[].nct, and already-removed registrations are reported separately.
"""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any


SSOT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SSOT_ROOT.parent
CASCADE_PATH = REPO_ROOT / "evidence" / "2026-08-19-batch1" / "cascade.json"
BATCH1_ASSESS_PATH = REPO_ROOT / "evidence" / "2026-08-19-batch1" / "assess.json"
OUT_DIR = REPO_ROOT / "evidence" / "2026-08-19-corpus"
OUT_PATH = OUT_DIR / "reconcile.json"

NCT = re.compile(r"\bNCT\d{8}\b")
EXECUTED_SEARCH = "EXECUTED_SEARCH"
NO_EXECUTED_SEARCH = "NO_EXECUTED_SEARCH"


def included_ncts(obj: dict[str, Any]) -> set[str]:
    """The INCLUDED set: inputs.trials[].nct. Not a regex over the document."""
    out = []
    for t in ((obj.get("inputs") or {}).get("trials") or []):
        nct = t.get("nct")
        if isinstance(nct, str) and NCT.fullmatch(nct.strip()):
            out.append(nct.strip())
    return set(out)


def removed_ncts(obj: dict[str, Any]) -> set[str]:
    """What the object says it REMOVED, reported separately from disappearances."""
    out = set()
    rc = obj.get("removed_citations")
    if isinstance(rc, dict):
        for cat in (rc.get("categories") or []):
            for v in (cat or {}).values():
                if isinstance(v, str):
                    out.update(NCT.findall(v))
    return out


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def canonical_topic_paths() -> list[Path]:
    paths = []
    for child in SSOT_ROOT.iterdir():
        if not child.is_dir():
            continue
        candidate = child / f"{child.name}.json"
        if candidate.exists():
            paths.append(candidate)
    return sorted(paths, key=lambda p: p.parent.name)


def input_trials_state(obj: dict[str, Any]) -> tuple[bool, list[Any] | None]:
    inputs = obj.get("inputs")
    if not isinstance(inputs, dict):
        return False, None
    trials = inputs.get("trials")
    if not isinstance(trials, list):
        return False, None
    return True, trials


def validate_cascade_entry(topic: str, entry: dict[str, Any]) -> None:
    roles = entry.get("roles")
    if not isinstance(roles, dict):
        raise ValueError(f"{topic}: cascade entry has no roles object")

    checks = [
        ("experimental_ids", "k3_experimental"),
        ("comparator_ids", "k4_comparator"),
        ("not_assessable_ids", "kNA_not_assessable"),
    ]
    for id_key, count_key in checks:
        ids = entry.get(id_key)
        count = entry.get(count_key)
        if not isinstance(ids, list):
            raise ValueError(f"{topic}: cascade {id_key} is not a list")
        if not isinstance(count, int):
            raise ValueError(f"{topic}: cascade {count_key} is not an integer")
        if len(set(ids)) != count:
            raise ValueError(
                f"{topic}: cascade {count_key}={count} but {id_key} has "
                f"{len(set(ids))} unique id(s)"
            )


def disappearance_reason(nct: str, cascade_entry: dict[str, Any]) -> str:
    roles = cascade_entry.get("roles") or {}
    surfaced = set(roles)
    comparator = set(cascade_entry.get("comparator_ids") or [])
    not_assessable_ids = set(cascade_entry.get("not_assessable_ids") or [])

    if nct in comparator:
        return "STRICTER CHECK: topic drug resolves to the COMPARATOR arm, not the intervention"
    if nct in not_assessable_ids:
        return "NOT_ASSESSABLE: role could not be located -- NOT excluded, unclassified"
    if nct in surfaced:
        role = roles[nct]["role"]
        return f"surfaced but roled {role}"
    return "NOT SURFACED by the executed search under its named intervention"


def appearance_item(nct: str, cascade_entry: dict[str, Any]) -> dict[str, Any]:
    role_record = (cascade_entry.get("roles") or {}).get(nct) or {}
    return {
        "nct": nct,
        "reason": "surfaced by the executed search and roled experimental; absent from inputs.trials",
        "role": role_record.get("role"),
        "role_evidence": role_record.get("evidence"),
    }


def reconcile_topic(
    topic: str,
    path: Path,
    obj: dict[str, Any],
    cascade: dict[str, Any],
) -> dict[str, Any]:
    has_trials, trials = input_trials_state(obj)
    old = included_ncts(obj) if has_trials else set()
    already_removed = removed_ncts(obj)

    row: dict[str, Any] = {
        "topic": topic,
        "object_path": rel(path),
        "object_state": "READ",
        "has_inputs_trials": has_trials,
        "inputs_trials_count": len(trials) if trials is not None else None,
        "old_k": len(old) if has_trials else None,
        "old_ids": sorted(old) if has_trials else None,
        "already_removed": len(already_removed),
        "already_removed_ids": sorted(already_removed),
    }

    if topic not in cascade:
        row.update(
            {
                "search_state": NO_EXECUTED_SEARCH,
                "located_k": None,
                "located_ids": None,
                "raw_surfaced_k": None,
                "kept": None,
                "kept_ids": None,
                "disappeared": None,
                "disappeared_items": None,
                "appeared": None,
                "appeared_items": None,
            }
        )
        return row

    c = cascade[topic]
    validate_cascade_entry(topic, c)
    experimental = set(c.get("experimental_ids") or [])

    located_k = c.get("k3_experimental")
    if not isinstance(located_k, int):
        raise ValueError(f"{topic}: k3_experimental is not an integer")

    row.update(
        {
            "search_state": EXECUTED_SEARCH,
            "located_k": located_k,
            "located_ids": sorted(experimental),
            "raw_surfaced_k": c.get("k0_surfaced_raw"),
        }
    )

    if not has_trials:
        row.update(
            {
                "kept": None,
                "kept_ids": None,
                "disappeared": None,
                "disappeared_items": None,
                "appeared": None,
                "appeared_items": None,
                "old_k_undefined_reason": "object carries no inputs.trials list",
            }
        )
        return row

    disappeared_items = [
        {"nct": nct, "reason": disappearance_reason(nct, c)}
        for nct in sorted(old - experimental)
    ]
    appeared_items = [appearance_item(nct, c) for nct in sorted(experimental - old)]

    row.update(
        {
            "kept": len(old & experimental),
            "kept_ids": sorted(old & experimental),
            "disappeared": len(disappeared_items),
            "disappeared_items": disappeared_items,
            "appeared": len(appeared_items),
            "appeared_items": appeared_items,
        }
    )
    return row


def load_topics() -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, Path]]:
    objects: dict[str, dict[str, Any]] = {}
    unreadable: dict[str, str] = {}
    paths: dict[str, Path] = {}

    for path in canonical_topic_paths():
        topic = path.parent.name
        paths[topic] = path
        try:
            loaded = read_json(path)
        except (OSError, ValueError) as exc:
            unreadable[topic] = f"{type(exc).__name__}: {exc}"
            continue
        if not isinstance(loaded, dict):
            unreadable[topic] = f"top-level JSON is {type(loaded).__name__}, not object"
            continue
        objects[topic] = loaded

    return objects, unreadable, paths


def build_duplicate_report(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_nct: dict[str, list[str]] = defaultdict(list)
    for topic, row in rows.items():
        for nct in row.get("old_ids") or []:
            by_nct[nct].append(topic)

    records = [
        {"nct": nct, "topics": topics}
        for nct, topics in sorted(by_nct.items())
        if len(topics) > 1
    ]

    omecamtiv_topics = by_nct.get("NCT02929329", [])
    sacubitril_topics = by_nct.get("NCT01035255", [])
    return {
        "n_registration_ids_in_more_than_one_topic": len(records),
        "records": records,
        "known_pattern_check": {
            "omecamtiv_NCT02929329": {
                "state": "CONFIRMED" if len(omecamtiv_topics) == 3 else "REFUTED",
                "topics": omecamtiv_topics,
            },
            "sacubitril_NCT01035255": {
                "state": "CONFIRMED_AS_TWO" if len(sacubitril_topics) == 2 else "REFUTED_AS_TWO",
                "topics": sacubitril_topics,
            },
        },
    }


def batch1_expected_row(assess_topic: dict[str, Any]) -> dict[str, Any]:
    r = assess_topic["reconciliation"]
    return {
        "old_k": r["old_k_by_nct"],
        "already_removed": r["n_already_removed"],
        "located_k": r["new_k3_experimental"],
        "kept": len(r["kept"]),
        "disappeared": r["n_disappeared"],
        "appeared": r["n_appeared"],
        "old_ids": r["old_ids"],
        "already_removed_ids": r["already_removed_by_object"],
        "kept_ids": r["kept"],
        "disappeared_items": r["disappeared"],
        "appeared_ids": r["appeared_experimental"],
    }


def batch1_actual_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "old_k": row["old_k"],
        "already_removed": row["already_removed"],
        "located_k": row["located_k"],
        "kept": row["kept"],
        "disappeared": row["disappeared"],
        "appeared": row["appeared"],
        "old_ids": row["old_ids"],
        "already_removed_ids": row["already_removed_ids"],
        "kept_ids": row["kept_ids"],
        "disappeared_items": row["disappeared_items"],
        "appeared_ids": [item["nct"] for item in (row["appeared_items"] or [])],
    }


def compare_batch1(rows: dict[str, dict[str, Any]], assess: dict[str, Any]) -> dict[str, Any]:
    mismatches = []
    topics = sorted((assess.get("topics") or {}).keys())
    for topic in topics:
        if topic not in rows:
            mismatches.append({"topic": topic, "problem": "missing from corpus rows"})
            continue
        expected = batch1_expected_row(assess["topics"][topic])
        actual = batch1_actual_row(rows[topic])
        if actual != expected:
            mismatches.append({"topic": topic, "expected": expected, "actual": actual})

    return {
        "matched": not mismatches,
        "matched_topics": len(topics) - len(mismatches),
        "total_topics": len(topics),
        "mismatches": mismatches,
    }


def fmt(value: Any) -> str:
    return "NULL" if value is None else str(value)


def print_table(rows: dict[str, dict[str, Any]]) -> None:
    header = (
        f"{'topic':<55} {'old k':>7} {'already_removed':>16} "
        f"{'search state':<18} {'located k':>9} {'kept':>7} "
        f"{'disappeared':>12} {'appeared':>9}"
    )
    print(header)
    for topic, row in rows.items():
        print(
            f"{topic:<55} {fmt(row['old_k']):>7} {fmt(row['already_removed']):>16} "
            f"{row['search_state']:<18} {fmt(row['located_k']):>9} {fmt(row['kept']):>7} "
            f"{fmt(row['disappeared']):>12} {fmt(row['appeared']):>9}"
        )


def print_disappearances(rows: dict[str, dict[str, Any]], cascade_topics: list[str]) -> None:
    print("DISAPPEARANCES FOR EXECUTED-SEARCH TOPICS")
    for topic in cascade_topics:
        items = rows[topic]["disappeared_items"] or []
        if not items:
            print(f"  {topic}: none")
            continue
        for item in items:
            print(f"  {topic:<48} {item['nct']}  {item['reason']}")


def main() -> int:
    cascade = read_json(CASCADE_PATH)
    assess = read_json(BATCH1_ASSESS_PATH)
    if not isinstance(cascade, dict):
        raise ValueError("cascade.json top level is not an object")
    if not isinstance(assess, dict):
        raise ValueError("assess.json top level is not an object")

    objects, unreadable, paths = load_topics()
    unknown_cascade_topics = sorted(set(cascade) - set(paths))
    if unknown_cascade_topics:
        raise ValueError(f"cascade topics absent from corpus: {unknown_cascade_topics}")

    rows: dict[str, dict[str, Any]] = {}
    for topic in sorted(paths):
        if topic in unreadable:
            rows[topic] = {
                "topic": topic,
                "object_path": rel(paths[topic]),
                "object_state": "UNREADABLE",
                "object_error": unreadable[topic],
                "has_inputs_trials": False,
                "inputs_trials_count": None,
                "old_k": None,
                "old_ids": None,
                "already_removed": None,
                "already_removed_ids": None,
                "search_state": EXECUTED_SEARCH if topic in cascade else NO_EXECUTED_SEARCH,
                "located_k": None,
                "located_ids": None,
                "raw_surfaced_k": None,
                "kept": None,
                "kept_ids": None,
                "disappeared": None,
                "disappeared_items": None,
                "appeared": None,
                "appeared_items": None,
            }
            continue
        rows[topic] = reconcile_topic(topic, paths[topic], objects[topic], cascade)

    batch_check = compare_batch1(rows, assess)
    if not batch_check["matched"]:
        print(
            "BATCH 1 KNOWN-ANSWER CHECK: FAIL - "
            f"{batch_check['matched_topics']}/{batch_check['total_topics']} rows matched"
        )
        print(json.dumps(batch_check["mismatches"], indent=1))
        return 1

    no_inputs_trials = [
        topic for topic, row in rows.items()
        if row.get("object_state") == "READ" and not row.get("has_inputs_trials")
    ]
    empty_inputs_trials = [
        topic for topic, row in rows.items()
        if row.get("object_state") == "READ" and row.get("inputs_trials_count") == 0
    ]
    executed_search_topics = sorted(cascade)
    no_executed_search_topics = [
        topic for topic, row in rows.items()
        if row["search_state"] == NO_EXECUTED_SEARCH
    ]

    coverage_sentence = (
        f"{len(executed_search_topics)} of {len(rows)} topics have an executed search on "
        f"record; {len(no_executed_search_topics)} do not. For topics without cascade data, "
        "located k, kept, disappeared and appeared are null, not zero."
    )

    report = {
        "batch1_known_answer_check": batch_check,
        "corpus": {
            "topic_count": len(rows),
            "executed_search_topics": len(executed_search_topics),
            "no_executed_search_topics": len(no_executed_search_topics),
            "no_inputs_trials_objects": len(no_inputs_trials),
            "no_inputs_trials_topics": no_inputs_trials,
            "empty_inputs_trials_objects": len(empty_inputs_trials),
            "empty_inputs_trials_topics": empty_inputs_trials,
            "executed_search_coverage_finding": coverage_sentence,
        },
        "hardcode_disclosure": [
            {
                "item": "batch 1 known-answer topics",
                "type": "dynamic",
                "source": rel(BATCH1_ASSESS_PATH),
                "note": "Read from assess.json; no topic list or old-k values are hardcoded.",
            },
            {
                "item": "executed-search data",
                "type": "dynamic",
                "source": rel(CASCADE_PATH),
                "note": "Only topics present in cascade.json are marked EXECUTED_SEARCH.",
            },
            {
                "item": "corpus topic list",
                "type": "dynamic",
                "source": "ssot/<topic>/<topic>.json",
                "note": "Discovered from direct same-named topic object files.",
            },
            {
                "item": "output path",
                "type": "static",
                "source": rel(OUT_PATH),
                "note": "Requested artifact path.",
            },
        ],
        "duplicate_seeding": build_duplicate_report(rows),
        "topics": rows,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")

    print(
        "BATCH 1 KNOWN-ANSWER CHECK: PASS - "
        f"all {batch_check['total_topics']} rows matched {rel(BATCH1_ASSESS_PATH)}"
    )
    print()
    print("CORPUS-WIDE")
    print(f"  executed search on record: {len(executed_search_topics)}")
    print(f"  no executed search on record: {len(no_executed_search_topics)}")
    print(f"  finding: {coverage_sentence}")
    print(f"  no inputs.trials at all: {len(no_inputs_trials)}")
    print(
        "  explicit empty inputs.trials lists: "
        f"{len(empty_inputs_trials)}"
    )
    print(
        "  duplicate registration IDs across included sets: "
        f"{report['duplicate_seeding']['n_registration_ids_in_more_than_one_topic']}"
    )
    print()
    print("SUMMARY TABLE")
    print_table(rows)
    print()
    print_disappearances(rows, executed_search_topics)
    print()
    print("DUPLICATE SEEDING")
    for record in report["duplicate_seeding"]["records"]:
        print(f"  {record['nct']}: {', '.join(record['topics'])}")
    print()
    print(f"wrote {rel(OUT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
