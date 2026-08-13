#!/usr/bin/env python
"""Compare app trial identity labels with cached ClinicalTrials.gov records.

This is intentionally conservative. EnrollmentCount is not used. A cached
registry record without an acronym is UNVERIFIABLE, never DISAGREES, because
title/sponsor text alone is too sparse to prove that an acronym claim is wrong.
An NCT absent from the cache is NCT_NOT_IN_CACHE, which means unknown.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any


NCT_RE = re.compile(r"^NCT\d{8}$")
NULLED_NCT_RE = re.compile(r"^NULLED:NCT\d{8}$")
AUTHOR_YEAR_RE = re.compile(
    r"^[A-Z][a-z]+(?:\s+(?:et\s+al\.?|[A-Z][a-z]+))*\s+(?:19|20)\d{2}$"
)
GENERIC_NAME_RE = re.compile(
    r"^(NCT\d{8}|Study[- ]?\d*|Trial[- ]?\d*|Phase[- ]?\d|"
    r"[A-Z]{1,3}\d{2,5}|C\d{3,4}|N0\d+|PER-\d+|JANSSEN-\d+|"
    r"YKP3089[-\w]*|[A-Z]+-001|MEZAGITAMAB-\w+|Vivitrol-\w+|"
    r"NCT\d+[a-z]?)$",
    re.IGNORECASE,
)

ROMAN_NUMERALS = {
    "i": "1",
    "ii": "2",
    "iii": "3",
    "iv": "4",
    "v": "5",
    "vi": "6",
    "vii": "7",
    "viii": "8",
    "ix": "9",
    "x": "10",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "by",
    "controlled",
    "dose",
    "double",
    "efficacy",
    "evaluate",
    "evaluating",
    "for",
    "in",
    "label",
    "of",
    "on",
    "open",
    "oral",
    "or",
    "participants",
    "patients",
    "phase",
    "randomised",
    "randomized",
    "safety",
    "single",
    "study",
    "subcutaneous",
    "the",
    "therapy",
    "to",
    "treatment",
    "trial",
    "versus",
    "vs",
    "with",
}

STATE_ORDER = ("AGREES", "DISAGREES", "UNVERIFIABLE", "NCT_NOT_IN_CACHE")
KNOWN_UNBIASED_IDENTITY_ERROR_RATE = 3 / 58


def split_tokens(value: str | None) -> list[str]:
    text = value or ""
    text = re.sub(r"([A-Za-z])([0-9])", r"\1 \2", text)
    text = re.sub(r"([0-9])([A-Za-z])", r"\1 \2", text)
    return [token for token in re.split(r"[^A-Za-z0-9]+", text) if token]


def romanize_tokens(tokens: list[str]) -> list[str]:
    return [ROMAN_NUMERALS.get(token.lower(), token.lower()) for token in tokens]


def normalize_number(token: str) -> str:
    if token.isdigit():
        return str(int(token))
    return token


def compact_variants(value: str | None) -> set[str]:
    tokens = split_tokens(value)
    variants: set[str] = set()
    for use_roman in (False, True):
        roman_tokens = romanize_tokens(tokens) if use_roman else [t.lower() for t in tokens]
        for use_number_norm in (False, True):
            normalized = [
                normalize_number(token) if use_number_norm else token for token in roman_tokens
            ]
            compact = "".join(re.sub(r"[^a-z0-9]", "", token) for token in normalized)
            if compact:
                variants.add(compact)
            without_stopwords = "".join(token for token in normalized if token not in STOPWORDS)
            if without_stopwords:
                variants.add(without_stopwords)
    raw = re.sub(r"[^a-z0-9]", "", (value or "").lower())
    if raw:
        variants.add(raw)
    return variants


def abbreviation_variants(value: str | None) -> set[str]:
    tokens = romanize_tokens(split_tokens(value))
    alpha_tokens = [token for token in tokens if re.search("[a-z]", token) and token not in STOPWORDS]
    number_tokens = [normalize_number(token) for token in tokens if token.isdigit()]
    variants: set[str] = set()
    if len(alpha_tokens) >= 2:
        initials = "".join(token[0] for token in alpha_tokens)
        variants.add(initials)
        variants.add(initials + "".join(number_tokens))
    return {variant for variant in variants if len(variant) >= 2}


def digit_groups(value: str) -> list[str]:
    return [str(int(group)) for group in re.findall(r"\d+", value)]


def numeric_conflict(left: str, right: str) -> bool:
    left_digits = digit_groups(left)
    right_digits = digit_groups(right)
    return bool(left_digits and right_digits and left_digits != right_digits)


def content_tokens(value: str | None) -> set[str]:
    tokens = set()
    for token in romanize_tokens(split_tokens(value)):
        normalized = normalize_number(token)
        if len(normalized) >= 3 and normalized not in STOPWORDS:
            tokens.add(normalized)
    return tokens


def is_generic_claim(name: str, nct: str) -> bool:
    clean = name.strip()
    if not clean or clean.upper() == nct:
        return True
    if GENERIC_NAME_RE.match(clean):
        return True
    return not content_tokens(clean)


def is_acronym_like(name: str) -> bool:
    if not name.strip() or AUTHOR_YEAR_RE.match(name.strip()):
        return False
    letters = re.findall(r"[A-Za-z]", name)
    if not letters:
        return False
    if re.search(r"\d", name):
        return True
    uppercase = sum(1 for char in letters if char.isupper())
    if uppercase / len(letters) >= 0.45:
        return True
    for token in split_tokens(name):
        if len(token) >= 3 and sum(1 for char in token if char.isupper()) >= 2:
            return True
    return False


def acronym_field_matches(claimed_name: str, registry_acronym: str) -> bool:
    claim_variants = compact_variants(claimed_name) | abbreviation_variants(claimed_name)
    acronym_variants = compact_variants(registry_acronym) | abbreviation_variants(registry_acronym)
    if claim_variants & acronym_variants:
        return True
    for acronym_variant in acronym_variants:
        if len(acronym_variant) < 3:
            continue
        for claim_variant in claim_variants:
            if len(claim_variant) < 3:
                continue
            if numeric_conflict(acronym_variant, claim_variant):
                continue
            if (
                claim_variant.startswith(acronym_variant)
                or claim_variant.endswith(acronym_variant)
                or acronym_variant.startswith(claim_variant)
                or acronym_variant.endswith(claim_variant)
            ):
                return True
    return False


def claim_matches_registry(claimed_name: str, registry_row: dict[str, Any]) -> tuple[bool, str]:
    registry_acronym = str(registry_row.get("acronym") or "")
    if acronym_field_matches(claimed_name, registry_acronym):
        return True, "acronym:variant_or_boundary"

    claim_variants = compact_variants(claimed_name) | abbreviation_variants(claimed_name)
    for field in ("brief_title", "lead_sponsor"):
        field_value = str(registry_row.get(field) or "")
        field_variants = compact_variants(field_value) | abbreviation_variants(field_value)
        if claim_variants & field_variants:
            return True, f"{field}:variant"
        for claim_variant in claim_variants:
            if len(claim_variant) < 5:
                continue
            for field_variant in field_variants:
                if len(field_variant) < 5:
                    continue
                if numeric_conflict(claim_variant, field_variant):
                    continue
                if claim_variant in field_variant or field_variant in claim_variant:
                    return True, f"{field}:substring"

    claim_tokens = content_tokens(claimed_name)
    for field in ("brief_title", "lead_sponsor"):
        field_tokens = content_tokens(str(registry_row.get(field) or ""))
        if not claim_tokens:
            continue
        if (
            len(claim_tokens) >= 2
            and len(claim_tokens & field_tokens) / len(claim_tokens) >= 0.75
            and not numeric_conflict("".join(sorted(claim_tokens)), "".join(sorted(field_tokens)))
        ):
            return True, f"{field}:token_overlap"
        if len(claim_tokens) == 1:
            only = next(iter(claim_tokens))
            if len(only) >= 7 and only in field_tokens:
                return True, f"{field}:single_token"
    return False, "no_match"


def compare_trial(
    *,
    app: str,
    nct: str,
    claimed_name: str,
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    registry_row = registry.get(nct)
    if registry_row is None:
        return {
            "state": "NCT_NOT_IN_CACHE",
            "reason": "nct absent from registry cache; unknown, not wrong",
            "app": app,
            "nct": nct,
            "claimed_name": claimed_name,
            "registry_acronym": None,
            "registry_brief_title": None,
            "registry_lead_sponsor": None,
        }

    base = {
        "app": app,
        "nct": nct,
        "claimed_name": claimed_name,
        "registry_acronym": registry_row.get("acronym"),
        "registry_brief_title": registry_row.get("brief_title"),
        "registry_lead_sponsor": registry_row.get("lead_sponsor"),
    }
    if is_generic_claim(claimed_name, nct):
        return {
            "state": "UNVERIFIABLE",
            "reason": "blank, NCT-as-name, or generic claim",
            **base,
        }
    if not registry_row.get("acronym"):
        return {
            "state": "UNVERIFIABLE",
            "reason": "registry acronym absent",
            **base,
        }

    agrees, reason = claim_matches_registry(claimed_name, registry_row)
    if agrees:
        return {"state": "AGREES", "reason": reason, **base}
    if not is_acronym_like(claimed_name) or len(content_tokens(claimed_name)) > 6 or len(claimed_name) > 80:
        return {"state": "UNVERIFIABLE", "reason": "claim not acronym-like", **base}
    return {"state": "DISAGREES", "reason": reason, **base}


def iter_app_trials(data_dir: Path) -> tuple[list[dict[str, Any]], int, int]:
    rows: list[dict[str, Any]] = []
    skipped_nulled = 0
    files_seen = 0
    for json_path in sorted(data_dir.glob("*.json")):
        if json_path.name.startswith("_"):
            continue
        files_seen += 1
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        real_data = payload.get("realData") or {}
        if not isinstance(real_data, dict):
            continue
        app = str(payload.get("file") or f"{json_path.stem}.html")
        for raw_nct, trial in real_data.items():
            if NULLED_NCT_RE.match(str(raw_nct)):
                skipped_nulled += 1
                continue
            if not NCT_RE.match(str(raw_nct)) or not isinstance(trial, dict):
                continue
            rows.append(
                {
                    "app": app,
                    "nct": str(raw_nct),
                    "claimed_name": str(trial.get("name") or "").strip(),
                }
            )
    return rows, files_seen, skipped_nulled


def build_report(data_dir: Path, registry_cache: Path, top: int = 25) -> dict[str, Any]:
    started = time.perf_counter()
    cache = json.loads(registry_cache.read_text(encoding="utf-8"))
    registry = cache.get("studies") or {}
    if not isinstance(registry, dict):
        raise ValueError("registry cache lacks a studies object")

    app_rows, files_seen, skipped_nulled = iter_app_trials(data_dir)
    comparisons = [
        compare_trial(
            app=row["app"],
            nct=row["nct"],
            claimed_name=row["claimed_name"],
            registry=registry,
        )
        for row in app_rows
    ]
    counts = Counter(row["state"] for row in comparisons)
    ordered_counts = {state: counts.get(state, 0) for state in STATE_ORDER}
    verifiable = ordered_counts["AGREES"] + ordered_counts["DISAGREES"]
    disagreement_rate = ordered_counts["DISAGREES"] / verifiable if verifiable else None
    disagrees = sorted(
        (row for row in comparisons if row["state"] == "DISAGREES"),
        key=lambda row: (row["app"], row["nct"], row["claimed_name"]),
    )
    cache_acronym_absent = int(cache.get("acronym_absent") or 0)
    cache_returned = int(cache.get("returned") or len(registry))
    elapsed = time.perf_counter() - started
    far_above_known = bool(disagreement_rate is not None and disagreement_rate > 0.10)

    return {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inputs": {
            "data_dir": str(data_dir),
            "registry_cache": str(registry_cache),
            "registry_cache_built_utc": cache.get("built_utc"),
            "registry_requested": cache.get("requested"),
            "registry_returned": cache_returned,
            "registry_not_returned": cache.get("not_returned"),
            "registry_acronym_absent": cache_acronym_absent,
            "registry_acronym_absent_pct": (
                cache_acronym_absent / cache_returned if cache_returned else None
            ),
        },
        "warnings": {
            "enrollment_count": (
                "EnrollmentCount is not used. It is not a randomised-N check; "
                "COAPT-style screened/roll-in counts can exceed randomised totals."
            ),
            "registry_acronym_absent": (
                "Cached records with no acronym are classified UNVERIFIABLE, never DISAGREES."
            ),
            "nct_absent": (
                "An NCT absent from the cache is classified NCT_NOT_IN_CACHE: unknown, not wrong."
            ),
            "known_unbiased_identity_error_rate": "3/58 = 5.2%",
            "rate_warning": (
                "DISAGREES/(AGREES+DISAGREES) exceeds 10%; this is far above the "
                "known unbiased rate, so the matcher should be treated as too broad."
                if far_above_known
                else None
            ),
        },
        "summary": {
            "json_files_scanned": files_seen,
            "apps_with_nct_rows": len({row["app"] for row in app_rows}),
            "trial_pairs_with_nct": len(app_rows),
            "unique_ncts": len({row["nct"] for row in app_rows}),
            "skipped_nulled_nct_keys": skipped_nulled,
            "state_counts": ordered_counts,
            "verifiable_pairs": verifiable,
            "disagreement_rate_among_verifiable": disagreement_rate,
            "known_unbiased_identity_error_rate": KNOWN_UNBIASED_IDENTITY_ERROR_RATE,
            "far_above_known_rate": far_above_known,
            "seconds": elapsed,
        },
        "top_disagrees": disagrees[:top],
        "rows": comparisons,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "state",
        "reason",
        "app",
        "nct",
        "claimed_name",
        "registry_acronym",
        "registry_brief_title",
        "registry_lead_sponsor",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("outputs") / "extraction_audit" / "data",
        help="Directory of extracted app JSON files.",
    )
    parser.add_argument(
        "--registry-cache",
        type=Path,
        default=Path("outputs") / "nct_cache" / "nct_registry_cache.json",
        help="ClinicalTrials.gov registry cache JSON.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("outputs") / "nct_cache" / "registered_intervention_comparator.json",
        help="Output JSON report.",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=Path("outputs") / "nct_cache" / "registered_intervention_comparator.csv",
        help="Output CSV with one row per compared app trial.",
    )
    parser.add_argument("--top", type=int, default=25, help="Number of disagreements to surface.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.data_dir, args.registry_cache, top=args.top)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(args.csv_out, report["rows"])

    summary = report["summary"]
    counts = summary["state_counts"]
    print(f"Compared {summary['trial_pairs_with_nct']} app/NCT trial rows")
    print(
        "States: "
        + ", ".join(f"{state}={counts[state]}" for state in STATE_ORDER)
    )
    print(
        "DISAGREES/(AGREES+DISAGREES)="
        f"{summary['disagreement_rate_among_verifiable']:.3%}"
        if summary["verifiable_pairs"]
        else "No verifiable pairs"
    )
    if summary["far_above_known_rate"]:
        print("WARNING: disagreement rate is far above 3/58 = 5.2%; matcher is likely too broad.")
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print("Top DISAGREES:")
    for row in report["top_disagrees"]:
        print(
            f"  {row['app']} | {row['claimed_name']} | {row['nct']} | "
            f"{row['registry_brief_title']}"
        )
    print(f"Seconds: {summary['seconds']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
