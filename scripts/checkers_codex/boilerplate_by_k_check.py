#!/usr/bin/env python3
"""Detect interpretation boilerplate reused across different pooled-trial counts."""

from __future__ import annotations

import io
import sys
from collections import defaultdict
from itertools import combinations
from typing import Any, Iterable


def _normalise_interpretation(text: str) -> bytes:
    """Lowercase and collapse whitespace, then encode for byte-identical compare."""
    return " ".join(text.lower().split()).encode("utf-8")


def scan(pages: Iterable[dict[str, Any]]) -> list[tuple[Any, Any, int, int]]:
    """Return pairs whose normalised interpretation is identical but k differs."""
    by_text: dict[bytes, list[tuple[Any, int]]] = defaultdict(list)

    for page in pages:
        page_id = page["id"]
        k = page["k"]
        interpretation = page["interpretation"]
        if not isinstance(k, int):
            raise TypeError(f"page {page_id!r} has non-int k: {k!r}")
        if not isinstance(interpretation, str):
            raise TypeError(
                f"page {page_id!r} has non-string interpretation: {interpretation!r}"
            )
        by_text[_normalise_interpretation(interpretation)].append((page_id, k))

    flagged: list[tuple[Any, Any, int, int]] = []
    for matches in by_text.values():
        for (id1, k1), (id2, k2) in combinations(matches, 2):
            if k1 != k2:
                flagged.append((id1, id2, k1, k2))

    return flagged


def _check(name: str, passed: bool) -> bool:
    print(f"{name}: {'OK' if passed else 'FAIL'}")
    return passed


def _selftest() -> None:
    failures = 0

    positive_pages = [
        {
            "id": "k1",
            "k": 1,
            "interpretation": "The pooled evidence supports a cautious conclusion.",
        },
        {
            "id": "k12",
            "k": 12,
            "interpretation": "The pooled evidence supports a cautious conclusion.",
        },
    ]
    positive_result = scan(positive_pages)
    if not _check("positive identical text different k", positive_result == [("k1", "k12", 1, 12)]):
        failures += 1

    negative_pages = [
        {
            "id": "own-k-1",
            "k": 1,
            "interpretation": "This interpretation is based on 1 pooled trial.",
        },
        {
            "id": "own-k-12",
            "k": 12,
            "interpretation": "This interpretation is based on 12 pooled trials.",
        },
    ]
    negative_result = scan(negative_pages)
    if not _check("negative own-k text differs", negative_result == []):
        failures += 1

    print("FAILURES" if failures else "ALL PASS")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    elif hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    _selftest()
