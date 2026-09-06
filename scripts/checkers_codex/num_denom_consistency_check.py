"""Check trial-arm numerator, denominator, and percentage consistency."""

from __future__ import annotations

from typing import Any, Iterable


Arm = dict[str, Any]
Finding = tuple[Any, Any, str]


def scan(arms: Iterable[Arm]) -> list[Finding]:
    """Return consistency findings as (trial, arm, reason) tuples."""
    findings: list[Finding] = []

    for record in arms:
        trial = record.get("trial")
        arm = record.get("arm")
        events = record["events"]
        n = record["n"]
        pct = record.get("pct")

        if events > n:
            findings.append((trial, arm, "numerator exceeds denominator"))

        if pct is not None:
            if n == 0:
                findings.append((trial, arm, "pct mismatch"))
            else:
                true_pct = 100.0 * events / n
                if abs(pct - true_pct) > 1.0:
                    findings.append((trial, arm, "pct mismatch"))

    return findings


def _selftest() -> bool:
    cases = [
        (
            "positive numerator exceeds denominator",
            [{"trial": "T1", "arm": "A", "events": 300, "n": 200, "pct": None}],
            "numerator exceeds denominator",
        ),
        (
            "positive pct mismatch",
            [{"trial": "T2", "arm": "A", "events": 50, "n": 200, "pct": 40.0}],
            "pct mismatch",
        ),
        (
            "negative exact pct",
            [{"trial": "T3", "arm": "A", "events": 50, "n": 200, "pct": 25.0}],
            None,
        ),
        (
            "negative rounded pct",
            [{"trial": "T4", "arm": "A", "events": 51, "n": 200, "pct": 25.5}],
            None,
        ),
    ]

    failures = []
    for name, arms, expected_reason in cases:
        findings = scan(arms)
        if expected_reason is None:
            passed = findings == []
        else:
            passed = any(expected_reason in reason for _, _, reason in findings)

        print(f"{'OK' if passed else 'FAIL'} {name}")
        if not passed:
            failures.append((name, findings, expected_reason))

    if failures:
        print("FAILURES")
        for name, findings, expected_reason in failures:
            print(f"FAIL {name}: expected {expected_reason!r}, got {findings!r}")
        return False

    print("ALL PASS")
    return True


if __name__ == "__main__":
    if not _selftest():
        raise SystemExit(1)
