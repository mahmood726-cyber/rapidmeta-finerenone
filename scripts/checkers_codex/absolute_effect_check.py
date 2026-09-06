"""Check that relative meta-analysis effects include absolute-effect context.

Pages reporting RR, HR, or OR must also report either:
- ARR and NNT with a named control-risk source, or
- an explicit undefined-note explaining why the absolute effect is undefined.
"""

from typing import Any, Iterable


RELATIVE_MEASURES = {"RR", "HR", "OR"}


def _has_named_control_risk_source(page: dict[str, Any]) -> bool:
    source = page.get("control_risk_source")
    return isinstance(source, str) and bool(source.strip())


def _has_complete_absolute_effect(page: dict[str, Any]) -> bool:
    return (
        bool(page.get("has_arr"))
        and bool(page.get("has_nnt"))
        and _has_named_control_risk_source(page)
    )


def scan(pages: Iterable[dict[str, Any]]) -> list[Any]:
    """Return ids for pages with a relative effect but no valid absolute effect."""
    flagged = []
    for page in pages:
        relative_measure = page.get("relative_measure")
        has_relative_effect = relative_measure in RELATIVE_MEASURES
        has_allowed_absolute_context = _has_complete_absolute_effect(page) or bool(
            page.get("undefined_note")
        )
        if has_relative_effect and not has_allowed_absolute_context:
            flagged.append(page.get("id"))
    return flagged


def _check(name: str, got: list[Any], expected: list[Any]) -> bool:
    ok = got == expected
    print(f"{'OK' if ok else 'FAIL'} {name}")
    if not ok:
        print(f"  expected: {expected!r}")
        print(f"  got:      {got!r}")
    return ok


def _selftest() -> None:
    checks = [
        (
            "positive_missing_arr_nnt_undefined_note",
            [
                {
                    "id": "rr_missing_absolute",
                    "relative_measure": "RR",
                    "has_arr": False,
                    "has_nnt": False,
                    "control_risk_source": None,
                    "undefined_note": False,
                }
            ],
            ["rr_missing_absolute"],
        ),
        (
            "negative_complete_absolute_effect",
            [
                {
                    "id": "rr_complete_absolute",
                    "relative_measure": "RR",
                    "has_arr": True,
                    "has_nnt": True,
                    "control_risk_source": "median control risk from included trials",
                    "undefined_note": False,
                }
            ],
            [],
        ),
        (
            "negative_undefined_absolute_effect",
            [
                {
                    "id": "rd_crosses_zero",
                    "relative_measure": "OR",
                    "has_arr": False,
                    "has_nnt": False,
                    "control_risk_source": None,
                    "undefined_note": True,
                }
            ],
            [],
        ),
    ]

    failures = 0
    for name, pages, expected in checks:
        failures += not _check(name, scan(pages), expected)

    if failures:
        print("FAILURES")
        raise SystemExit(1)
    print("ALL PASS")


if __name__ == "__main__":
    _selftest()
