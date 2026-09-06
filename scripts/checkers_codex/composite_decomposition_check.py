"""Check composite primary outcomes for component decomposition reporting."""

from __future__ import annotations

import re


_COMPOSITE_OR_RE = re.compile(r"\s+\bor\b\s+", re.IGNORECASE)
_ALPHA_RE = re.compile(r"[A-Za-z]")


def _has_term(text: str) -> bool:
    return bool(_ALPHA_RE.search(text))


def is_composite(primary_outcome: str) -> bool:
    """Return True when a primary outcome joins two terms with standalone 'or'."""
    if not isinstance(primary_outcome, str):
        return False

    for match in _COMPOSITE_OR_RE.finditer(primary_outcome):
        left = primary_outcome[: match.start()]
        right = primary_outcome[match.end() :]
        if _has_term(left) and _has_term(right):
            return True
    return False


def scan(pages):
    """Return ids for composite-outcome pages missing component reporting."""
    flagged = []
    for page in pages:
        if not isinstance(page, dict):
            continue

        components_reported = page.get("components_reported") or []
        components_unavailable_note = bool(page.get("components_unavailable_note"))

        if (
            is_composite(page.get("primary_outcome", ""))
            and len(components_reported) < 2
            and not components_unavailable_note
        ):
            flagged.append(page.get("id"))
    return flagged


def _selftest():
    tests = [
        (
            "positive composite without components or note",
            [
                {
                    "id": "positive",
                    "primary_outcome": "CV death or HF hospitalisation",
                    "components_reported": [],
                    "components_unavailable_note": False,
                }
            ],
            ["positive"],
        ),
        (
            "negative composite with two components",
            [
                {
                    "id": "reported",
                    "primary_outcome": "CV death or HF hospitalisation",
                    "components_reported": ["CV death", "HF hospitalisation"],
                    "components_unavailable_note": False,
                }
            ],
            [],
        ),
        (
            "negative non-composite",
            [
                {
                    "id": "non_composite",
                    "primary_outcome": "all-cause mortality",
                    "components_reported": [],
                    "components_unavailable_note": False,
                }
            ],
            [],
        ),
    ]

    failures = 0
    for name, pages, expected in tests:
        actual = scan(pages)
        if actual == expected:
            print(f"OK: {name}")
        else:
            failures += 1
            print(f"FAIL: {name}: expected {expected!r}, got {actual!r}")

    if failures:
        print("FAILURES")
        raise SystemExit(1)

    print("ALL PASS")


if __name__ == "__main__":
    _selftest()
