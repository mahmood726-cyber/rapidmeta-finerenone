"""Detect conflicting pooled estimates for the same comparison and outcome."""

from collections import defaultdict


TOLERANCE = 0.001


def scan(pages):
    """Return conflicts as (id, comparison, outcome, points).

    A conflict exists when a page contains multiple pools with the same
    (comparison, outcome) and any two point estimates differ by more than
    TOLERANCE.
    """
    findings = []

    for page in pages:
        page_id = page.get("id")
        grouped = defaultdict(list)

        for pool in page.get("pools", []):
            key = (pool.get("comparison"), pool.get("outcome"))
            grouped[key].append(float(pool.get("point")))

        for (comparison, outcome), points in grouped.items():
            if len(points) < 2:
                continue
            if max(points) - min(points) > TOLERANCE:
                findings.append((page_id, comparison, outcome, points))

    return findings


def _selftest():
    failures = []

    positive = [
        {
            "id": "positive",
            "pools": [
                {"comparison": "drug vs placebo", "outcome": "mortality", "point": 0.77},
                {"comparison": "drug vs placebo", "outcome": "mortality", "point": 0.80},
            ],
        }
    ]
    expected_positive = [("positive", "drug vs placebo", "mortality", [0.77, 0.80])]
    if scan(positive) == expected_positive:
        print("OK positive")
    else:
        print("FAIL positive")
        failures.append("positive")

    negative1 = [
        {
            "id": "negative1",
            "pools": [
                {"comparison": "drug vs placebo", "outcome": "mortality", "point": 0.77},
                {"comparison": "drug vs placebo", "outcome": "remission", "point": 0.80},
            ],
        }
    ]
    if scan(negative1) == []:
        print("OK negative1")
    else:
        print("FAIL negative1")
        failures.append("negative1")

    negative2 = [
        {
            "id": "negative2",
            "pools": [
                {"comparison": "drug vs placebo", "outcome": "mortality", "point": 0.77},
                {"comparison": "drug vs usual care", "outcome": "mortality", "point": 0.80},
            ],
        }
    ]
    if scan(negative2) == []:
        print("OK negative2")
    else:
        print("FAIL negative2")
        failures.append("negative2")

    if failures:
        print("FAILURES")
        raise SystemExit(1)

    print("ALL PASS")


if __name__ == "__main__":
    _selftest()
