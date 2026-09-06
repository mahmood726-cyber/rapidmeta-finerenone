"""Check that trial exclusion reasons are backed by stated evidence fields.

Input pages are dictionaries shaped like:
    {"id": "...", "exclusions": [{"nct": "...", "reason": "...",
                                   "evidence_field": "...",
                                   "evidence_value": "..."}]}

The corroboration rules are intentionally small. They catch only direct claims
where a compact keyword check is defensible:
    - "not randomi..." must be corroborated by evidence text suggesting a
      non-randomized design, such as observational, single-arm, registry, or
      cohort.
"""

from __future__ import annotations


NON_RANDOMIZED_CORROBORATORS = (
    "observational",
    "single",
    "single-arm",
    "single arm",
    "registry",
    "cohort",
    "case-control",
    "case control",
    "nonrandom",
    "non-random",
    "open-label non-random",
)


def _is_empty(value: object) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _as_pages(pages: object) -> list[dict]:
    if isinstance(pages, dict):
        return [pages]
    return list(pages or [])


def _corroboration_failure(reason: object, evidence_value: object) -> str | None:
    reason_text = str(reason or "").lower()
    evidence_text = str(evidence_value or "").lower()

    if "not randomi" in reason_text:
        if not any(term in evidence_text for term in NON_RANDOMIZED_CORROBORATORS):
            return "reason says not randomized but evidence_value does not corroborate non-randomized design"

    return None


def scan(pages: object) -> list[tuple[object, object, str]]:
    """Return (id, nct, why) for exclusions lacking checkable evidence."""
    findings = []

    for page in _as_pages(pages):
        page_id = page.get("id")
        exclusions = page.get("exclusions") or []

        for exclusion in exclusions:
            nct = exclusion.get("nct")
            evidence_field = exclusion.get("evidence_field")
            evidence_value = exclusion.get("evidence_value")

            if _is_empty(evidence_field):
                findings.append((page_id, nct, "evidence_field is empty; reason is unverifiable"))
                continue

            if _is_empty(evidence_value):
                findings.append((page_id, nct, "evidence_value is empty; reason is unverifiable"))
                continue

            failure = _corroboration_failure(exclusion.get("reason"), evidence_value)
            if failure is not None:
                findings.append((page_id, nct, failure))

    return findings


def _selftest() -> bool:
    tests = [
        (
            "POSITIVE1",
            {
                "id": "page-1",
                "exclusions": [
                    {
                        "nct": "NCT00000001",
                        "reason": "not randomised",
                        "evidence_field": None,
                        "evidence_value": "observational cohort",
                    }
                ],
            },
            True,
        ),
        (
            "POSITIVE2",
            {
                "id": "page-2",
                "exclusions": [
                    {
                        "nct": "NCT00000002",
                        "reason": "not randomised",
                        "evidence_field": "study_design",
                        "evidence_value": "randomised double-blind",
                    }
                ],
            },
            True,
        ),
        (
            "NEGATIVE",
            {
                "id": "page-3",
                "exclusions": [
                    {
                        "nct": "NCT00000003",
                        "reason": "not randomised",
                        "evidence_field": "study_design",
                        "evidence_value": "observational cohort",
                    }
                ],
            },
            False,
        ),
    ]

    failures = []
    for name, payload, should_flag in tests:
        flagged = bool(scan(payload))
        ok = flagged is should_flag
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(name)

    if failures:
        print("FAILURES")
        return False

    print("ALL PASS")
    return True


if __name__ == "__main__":
    if not _selftest():
        raise SystemExit(1)
