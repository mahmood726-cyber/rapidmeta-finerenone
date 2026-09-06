"""Detect review trials held in an unresolved executed state.

Input pages are dictionaries shaped like:
    {"id": "...", "trials": [{"nct": "...", "state": "..."}]}

The scan result is a list of (page_id, nct) pairs for trials that must render
as OPEN items instead of being silently dropped.
"""

from __future__ import annotations


TERMINAL_STATES = frozenset(
    {
        "INCLUDED",
        "EXCLUDED",
        "PUBLICATION_SEARCH_REQUIRED",
    }
)

UNRESOLVED_HOLDING_STATES = frozenset(
    {
        "EXECUTED_UNRESOLVED",
        None,
        "",
    }
)


def scan(pages):
    """Return [(id, nct), ...] for trials that remain open after execution."""
    flagged = []

    for page in pages:
        page_id = page.get("id")
        for trial in page.get("trials", []):
            state = trial.get("state")
            if state in UNRESOLVED_HOLDING_STATES:
                flagged.append((page_id, trial.get("nct")))

    return flagged


def _selftest():
    cases = [
        (
            "POSITIVE",
            [{"id": "review-1", "trials": [{"nct": "NCT001", "state": "EXECUTED_UNRESOLVED"}]}],
            [("review-1", "NCT001")],
        ),
        (
            "POSITIVE2",
            [{"id": "review-2", "trials": [{"nct": "NCT002", "state": None}]}],
            [("review-2", "NCT002")],
        ),
        (
            "NEGATIVE",
            [
                {
                    "id": "review-3",
                    "trials": [
                        {"nct": "NCT003", "state": "INCLUDED"},
                        {"nct": "NCT004", "state": "EXCLUDED"},
                        {"nct": "NCT005", "state": "PUBLICATION_SEARCH_REQUIRED"},
                    ],
                }
            ],
            [],
        ),
    ]

    failures = []
    for name, pages, expected in cases:
        actual = scan(pages)
        if actual == expected:
            print("OK", name)
        else:
            print("FAIL", name, "expected", expected, "got", actual)
            failures.append(name)

    if failures:
        print("FAILURES", ",".join(failures))
        raise SystemExit(1)

    print("ALL PASS")


if __name__ == "__main__":
    _selftest()
