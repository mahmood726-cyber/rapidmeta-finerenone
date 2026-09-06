"""Detect outcome-result absence that is not explicitly declared.

A missing outcome result must be represented as state="absent", not as a
reported result with a null value and not as an undeclared null.
"""


def scan(pages):
    """Return [(id, trial, outcome), ...] for absence-as-result violations."""
    flagged = []

    for page in pages:
        page_id = page.get("id")
        for cell in page.get("cells", []):
            value = cell.get("value")
            state = cell.get("state")

            reported_without_value = state == "reported" and value in (None, "")
            undeclared_absence = state is None and value is None

            if reported_without_value or undeclared_absence:
                flagged.append((page_id, cell.get("trial"), cell.get("outcome")))

    return flagged


def _selftest():
    tests = [
        (
            "POSITIVE1",
            [{"id": "p1", "cells": [{"trial": "t1", "outcome": "o1", "value": None, "state": "reported"}]}],
            [("p1", "t1", "o1")],
        ),
        (
            "POSITIVE2",
            [{"id": "p2", "cells": [{"trial": "t2", "outcome": "o2", "value": None, "state": None}]}],
            [("p2", "t2", "o2")],
        ),
        (
            "NEGATIVE1",
            [{"id": "p3", "cells": [{"trial": "t3", "outcome": "o3", "value": 0.8, "state": "reported"}]}],
            [],
        ),
        (
            "NEGATIVE2",
            [{"id": "p4", "cells": [{"trial": "t4", "outcome": "o4", "value": None, "state": "absent"}]}],
            [],
        ),
    ]

    failures = 0
    for name, pages, expected in tests:
        actual = scan(pages)
        if actual == expected:
            print("OK", name)
        else:
            failures += 1
            print("FAIL", name, "expected", expected, "got", actual)

    if failures:
        print("FAILURES")
        raise SystemExit(1)

    print("ALL PASS")


if __name__ == "__main__":
    _selftest()
