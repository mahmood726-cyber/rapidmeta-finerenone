"""Flag meta-analysis pages that lack named, specific harms.

Input pages are dictionaries shaped like {"id": ..., "harms": list[str]}.
The scan function returns the ids for pages whose harms list is empty or
contains only generic, non-specific safety terms.
"""

from __future__ import annotations


GENERIC_TERMS = frozenset(
    {
        "adverse events",
        "adverse event",
        "ae",
        "aes",
        "safety",
        "side effects",
        "tolerability",
        "serious adverse events",
        "sae",
    }
)


def _normalise(term: str) -> str:
    return term.strip().casefold()


def _is_specific_harm(term: str) -> bool:
    normalised = _normalise(term)
    return bool(normalised) and normalised not in GENERIC_TERMS


def scan(pages):
    """Return ids for pages without at least one named, specific harm."""
    flagged = []

    for page in pages:
        harms = page.get("harms") or []
        if not harms or not any(_is_specific_harm(harm) for harm in harms):
            flagged.append(page.get("id"))

    return flagged


def _selftest():
    cases = [
        (
            "POSITIVE 1",
            [{"id": "empty", "harms": []}],
            ["empty"],
        ),
        (
            "POSITIVE 2",
            [{"id": "generic", "harms": ["adverse events", "serious adverse events"]}],
            ["generic"],
        ),
        (
            "NEGATIVE",
            [{"id": "specific", "harms": ["hyperkalaemia", "hypotension"]}],
            [],
        ),
        (
            "NEGATIVE 2",
            [{"id": "mixed", "harms": ["adverse events", "ketoacidosis"]}],
            [],
        ),
    ]

    failures = []
    for name, pages, expected in cases:
        observed = scan(pages)
        ok = observed == expected
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append((name, expected, observed))

    if failures:
        print("FAILURES")
        for name, expected, observed in failures:
            print(f"{name}: expected {expected!r}, observed {observed!r}")
        raise SystemExit(1)

    print("ALL PASS")


if __name__ == "__main__":
    _selftest()
