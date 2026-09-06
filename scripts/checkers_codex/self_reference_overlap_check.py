"""Detect benchmark self-reference in meta-analysis page records.

Input page shape:
    {
        "id": ...,
        "meta_trials": ["trial-a", "trial-b"],
        "benchmark": {"name": "external pool", "trials": ["trial-a"]},
    }
"""

INVALID_SELF_REFERENCE = "INVALID_SELF_REFERENCE"
JACCARD_THRESHOLD = 0.8


def _as_trial_set(trials):
    """Return a set of non-empty trial identifiers."""
    return {str(trial) for trial in (trials or []) if str(trial)}


def jaccard_overlap(meta_trials, benchmark_trials):
    """Compute |intersection| / |union| for two trial collections."""
    meta_set = _as_trial_set(meta_trials)
    benchmark_set = _as_trial_set(benchmark_trials)
    union = meta_set | benchmark_set
    if not union:
        return 0.0
    return len(meta_set & benchmark_set) / len(union)


def is_invalid_self_reference(page):
    """Return True when a page's benchmark is actually self-referential."""
    benchmark = page.get("benchmark") or {}
    name = str(benchmark.get("name") or "").lower()
    overlap = jaccard_overlap(page.get("meta_trials"), benchmark.get("trials"))
    return "self" in name or overlap >= JACCARD_THRESHOLD


def scan(pages):
    """Return ids for pages whose benchmark should be flagged."""
    return [page.get("id") for page in pages if is_invalid_self_reference(page)]


def _check(label, condition):
    if condition:
        print(f"OK {label}")
        return 0
    print(f"FAIL {label}")
    return 1


def _selftest():
    failures = 0

    positive = {
        "id": "positive-exact-overlap",
        "meta_trials": ["T1", "T2", "T3"],
        "benchmark": {"name": "external benchmark", "trials": ["T1", "T2", "T3"]},
    }
    failures += _check(
        "positive exact overlap jaccard 1.0 flagged",
        jaccard_overlap(positive["meta_trials"], positive["benchmark"]["trials"]) == 1.0
        and scan([positive]) == ["positive-exact-overlap"],
    )

    negative_overlap = {
        "id": "negative-jaccard-half",
        "meta_trials": ["T1", "T2", "T3", "T4"],
        "benchmark": {
            "name": "published external pool",
            "trials": ["T1", "T2", "T3", "T5", "T6"],
        },
    }
    negative_jaccard = jaccard_overlap(
        negative_overlap["meta_trials"], negative_overlap["benchmark"]["trials"]
    )
    failures += _check(
        "negative shared 3 of 6 union jaccard 0.5 not flagged",
        negative_jaccard == 0.5 and scan([negative_overlap]) == [],
    )

    negative_independent = {
        "id": "negative-independent-registry",
        "meta_trials": ["M1", "M2", "M3"],
        "benchmark": {
            "name": "independent registry pool",
            "trials": ["R1", "R2", "R3"],
        },
    }
    failures += _check(
        "negative independent registry pool not flagged",
        jaccard_overlap(
            negative_independent["meta_trials"],
            negative_independent["benchmark"]["trials"],
        )
        < JACCARD_THRESHOLD
        and scan([negative_independent]) == [],
    )

    if failures:
        print("FAILURES")
        raise SystemExit(1)

    print("ALL PASS")


if __name__ == "__main__":
    _selftest()
