"""Check GRADE imprecision ratings against OIS and CI threshold crossing."""

from __future__ import annotations

from typing import Iterable, Mapping, Any


VALID_GRADES = {"not_serious", "serious", "very_serious"}


def _ci_crosses_null(page: Mapping[str, Any]) -> bool:
    return float(page["ci_low"]) < float(page["null_value"]) < float(page["ci_high"])


def _reason_for_flag(page: Mapping[str, Any]) -> str | None:
    grade = str(page["grade_imprecision"])
    if grade not in VALID_GRADES:
        raise ValueError(f"invalid grade_imprecision for {page.get('id')!r}: {grade!r}")

    total_n = int(page["total_n"])
    ois = int(page["ois"])
    crosses_null = _ci_crosses_null(page)

    if grade == "not_serious":
        reasons = []
        if total_n < ois:
            reasons.append("not_serious but total_n < ois")
        if crosses_null:
            reasons.append("not_serious but CI crosses null_value")
        if reasons:
            return "; ".join(reasons)

    if grade == "serious" and total_n >= ois and not crosses_null:
        return "serious downgrade without cause: total_n >= ois and CI excludes null_value"

    return None


def scan(pages: Iterable[Mapping[str, Any]]) -> list[tuple[Any, str]]:
    """Return ``(id, reason)`` for records with inconsistent imprecision ratings."""
    flagged = []
    for page in pages:
        reason = _reason_for_flag(page)
        if reason is not None:
            flagged.append((page["id"], reason))
    return flagged


def _selftest() -> bool:
    cases = [
        (
            "POSITIVE1",
            [
                {
                    "id": "POSITIVE1",
                    "grade_imprecision": "not_serious",
                    "total_n": 80,
                    "ois": 100,
                    "ci_low": 1.1,
                    "ci_high": 1.5,
                    "null_value": 1.0,
                }
            ],
            ["POSITIVE1"],
        ),
        (
            "POSITIVE2",
            [
                {
                    "id": "POSITIVE2",
                    "grade_imprecision": "not_serious",
                    "total_n": 100,
                    "ois": 100,
                    "ci_low": 0.8,
                    "ci_high": 1.2,
                    "null_value": 1.0,
                }
            ],
            ["POSITIVE2"],
        ),
        (
            "NEGATIVE",
            [
                {
                    "id": "NEGATIVE",
                    "grade_imprecision": "not_serious",
                    "total_n": 100,
                    "ois": 100,
                    "ci_low": 1.1,
                    "ci_high": 1.5,
                    "null_value": 1.0,
                }
            ],
            [],
        ),
        (
            "POSITIVE3",
            [
                {
                    "id": "POSITIVE3",
                    "grade_imprecision": "serious",
                    "total_n": 100,
                    "ois": 100,
                    "ci_low": 1.1,
                    "ci_high": 1.5,
                    "null_value": 1.0,
                }
            ],
            ["POSITIVE3"],
        ),
    ]

    failures = []
    for name, pages, expected_ids in cases:
        actual_ids = [item_id for item_id, _reason in scan(pages)]
        if actual_ids == expected_ids:
            print(f"OK {name}")
        else:
            print(f"FAIL {name}: expected {expected_ids!r}, got {actual_ids!r}")
            failures.append(name)

    if failures:
        print("FAILURES")
        return False

    print("ALL PASS")
    return True


if __name__ == "__main__":
    if not _selftest():
        raise SystemExit(1)
