"""Check whether protocol benchmark citations are external and disclosed.

Input records are dictionaries shaped like:
    {"id": ..., "benchmark": {"name": ..., "pmid": ..., "doi": ...,
     "trials": [...]}, "meta_trials": [...]}

The scanner is intentionally small and stdlib-only so it can be vendored into
protocol validation pipelines.
"""

from __future__ import annotations


DISCLOSURE_MARKERS = ("same-trials", "cross-check", "ipd")


def _present(value) -> bool:
    """Return True for non-empty values after string trimming."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def _trial_set(values) -> set[str]:
    """Normalize trial IDs for exact-set comparison."""
    if not values:
        return set()
    normalized = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            normalized.add(text.casefold())
    return normalized


def _same_trial_set(benchmark_trials, meta_trials) -> bool:
    """Return True when the benchmark/meta trial Jaccard is exactly 1.0."""
    benchmark_set = _trial_set(benchmark_trials)
    meta_set = _trial_set(meta_trials)
    union = benchmark_set | meta_set
    if not union:
        return False
    return len(benchmark_set & meta_set) / len(union) == 1.0


def _labelled_same_trials(name: str) -> bool:
    name_lower = name.casefold()
    return any(marker in name_lower for marker in DISCLOSURE_MARKERS)


def scan(pages) -> list[tuple[object, str]]:
    """Return ``(id, reason)`` tuples for benchmark citation violations."""
    findings = []
    for page in pages:
        page_id = page.get("id")
        benchmark = page.get("benchmark") or {}
        name = benchmark.get("name")

        # A benchmark is subject to the citation rules only when it is actually CLAIMED (name present).
        # Phrased positively so the absence of a name is a POSITIVE state (claimed=False), not a bare
        # negative skip-guard inside a corpus loop (see audit_exclusion_by_absence).
        claimed = _present(name)
        if claimed:
            name_text = str(name).strip()
            cited = _present(benchmark.get("pmid")) or _present(benchmark.get("doi"))
            uncited = not cited
            if uncited:
                findings.append((page_id, "uncited benchmark: claimed benchmark has no PMID or DOI"))

            same_set = _same_trial_set(benchmark.get("trials"), page.get("meta_trials"))
            disclosed_same_trials = _labelled_same_trials(name_text)
            undisclosed_self_ref = same_set and not disclosed_same_trials
            if undisclosed_self_ref:
                findings.append(
                    (
                        page_id,
                        "undisclosed self-reference: benchmark trials match meta_trials "
                        "but name is not labelled as same-trials/cross-check/IPD",
                    )
                )

    return findings


def _selftest() -> bool:
    pages = [
        {
            "id": "POSITIVE1",
            "benchmark": {
                "name": "known external benchmark",
                "pmid": "",
                "doi": None,
                "trials": ["NCT1", "NCT2"],
            },
            "meta_trials": ["NCT3", "NCT4"],
        },
        {
            "id": "POSITIVE2",
            "benchmark": {
                "name": "external validation",
                "pmid": "12345678",
                "doi": "",
                "trials": ["NCT1", "NCT2"],
            },
            "meta_trials": ["NCT2", "NCT1"],
        },
        {
            "id": "NEGATIVE1",
            "benchmark": {
                "name": "published benchmark",
                "pmid": "",
                "doi": "10.1000/example",
                "trials": ["NCT1", "NCT2", "NCT3"],
            },
            "meta_trials": ["NCT1", "NCT2"],
        },
        {
            "id": "NEGATIVE2",
            "benchmark": {
                "name": "same-trials IPD cross-check",
                "pmid": "",
                "doi": "10.1000/ipd-check",
                "trials": ["NCT1", "NCT2"],
            },
            "meta_trials": ["NCT1", "NCT2"],
        },
    ]

    findings = scan(pages)
    expected = {
        ("POSITIVE1", "uncited benchmark: claimed benchmark has no PMID or DOI"),
        (
            "POSITIVE2",
            "undisclosed self-reference: benchmark trials match meta_trials "
            "but name is not labelled as same-trials/cross-check/IPD",
        ),
    }
    return set(findings) == expected


if __name__ == "__main__":
    ok = _selftest()
    print("OK" if ok else "FAIL")
    print("ALL PASS" if ok else "FAILURES")
    if not ok:
        raise SystemExit(1)
