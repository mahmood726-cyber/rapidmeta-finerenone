"""Fail-closed independent-benchmark provenance gate.

Numerical closeness is only a diagnostic. Passing an independent reproduction
requires an external synthesis reference, an explicitly adjudicated source-level
comparison, matching contributors/endpoints/estimands, and a numerical match.
Never auto-populate adjudications from the app or its internal pooled estimate.
"""
from __future__ import annotations

import math
import re

EXTERNAL_TYPES = frozenset({"external_IPD", "external_aggregate"})
_CANONICAL_NCT = re.compile(r"NCT[0-9]{8}\Z")
_PMID = re.compile(r"[0-9]{1,8}\Z")


def assess_reference(legacy: dict | None, published: dict | None,
                     pool: dict | None, numeric_match: bool = False) -> dict:
    """Return a *separate* provenance verdict, not the old numerical result.

    All real records currently lack source-level independent adjudications.
    They therefore remain NOT_VERIFIED. Merely filling in a published number
    or a PMID must not change their verification state.
    """
    reasons: list[str] = []
    source_type = published.get("benchmark_type") if isinstance(published, dict) else None
    verdict = {
        "verification_status": "NOT_VERIFIED",
        "benchmark_type": source_type,
        "provenance_reasons": reasons,
    }
    if not legacy:
        reasons.append("NO_LEGACY_NUMERIC_BENCHMARK")
    if not isinstance(published, dict):
        reasons.append("NO_PUBLISHED_REFERENCE_RECORD")
        return verdict
    if source_type not in EXTERNAL_TYPES:
        reasons.append("NOT_AN_INDEPENDENT_EXTERNAL_META_ANALYSIS")
    if not _PMID.fullmatch(str(published.get("pmid", ""))):
        reasons.append("NO_CANONICAL_PUBLISHED_META_ANALYSIS_PMID")
    if not published.get("source") or not published.get("primary_outcome"):
        reasons.append("MISSING_SOURCE_OR_OUTCOME")
    if published.get("estimand") not in ("HR", "RR", "OR", "IRR", "MD", "SMD", "RD"):
        reasons.append("MISSING_OR_INVALID_ESTIMAND")
    if not isinstance(published.get("k"), int) or published.get("k", 0) < 2:
        reasons.append("REFERENCE_NOT_A_MULTI_TRIAL_SYNTHESIS")
    if not isinstance(pool, dict) or pool.get("k", 0) < 2:
        reasons.append("APP_NOT_A_MULTI_TRIAL_POOL")
    elif published.get("k") != pool.get("k"):
        reasons.append("TRIAL_COUNT_MISMATCH")
    if legacy:
        if legacy.get("measure") != published.get("estimand"):
            reasons.append("ESTIMAND_MISMATCH")
        for a, b in (("est", "pooled"), ("lo", "lci"), ("hi", "uci")):
            x, y = legacy.get(a), published.get(b)
            if not (isinstance(x, (int, float)) and isinstance(y, (int, float))
                    and math.isfinite(x) and math.isfinite(y)
                    and math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-10)):
                reasons.append("EMBEDDED_REFERENCE_DISAGREES_WITH_PUBLISHED_REGISTRY")
                break
    review = published.get("independent_comparability_review")
    if not isinstance(review, dict) or review.get("status") != "source_adjudicated":
        reasons.append("INDEPENDENT_SOURCE_ADJUDICATION_ABSENT")
        return verdict
    # A 'verified' label alone is not proof: all explicit source comparability
    # inputs must be present and tied to the exact trial IDs used by the pool.
    required = ("reviewer", "reviewed_on", "source_locator", "outcome_definition",
                "population", "comparator", "followup", "method_difference_note")
    if any(not isinstance(review.get(k), str) or not review[k].strip() for k in required):
        reasons.append("SOURCE_REVIEW_EVIDENCE_INCOMPLETE")
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", str(review.get("reviewed_on", ""))):
        reasons.append("INVALID_REVIEW_DATE")
    if review.get("source_pmid") != published.get("pmid"):
        reasons.append("SOURCE_REVIEW_PMID_MISMATCH")
    if review.get("primary_outcome") != published.get("primary_outcome"):
        reasons.append("OUTCOME_MISMATCH")
    if review.get("estimand") != published.get("estimand"):
        reasons.append("REVIEW_ESTIMAND_MISMATCH")

    # Exact *contributing* study rows, not total app realData membership.
    # Never count a suffix (multi-arm comparison) as an independent NCT RCT.
    ids = pool.get("trial_ids") if isinstance(pool, dict) else None
    reference_ids = review.get("source_trial_ids")
    if (not isinstance(ids, list) or not isinstance(reference_ids, list)
            or not ids or len(ids) != len(set(ids))
            or len(reference_ids) != len(set(reference_ids))
            or any(not isinstance(x, str) or not _CANONICAL_NCT.fullmatch(x)
                   for x in ids + reference_ids)
            or set(ids) != set(reference_ids)):
        reasons.append("SOURCE_AND_APP_TRIAL_SETS_NOT_VERIFIED_IDENTICAL")

    # The pooled validator accepts published ratio CIs and can fall back to
    # odds ratios from 2x2 counts. That fallback must *not* silently reproduce
    # a source HR or RR. Each contributing estimand needs manual adjudication.
    inputs = pool.get("trial_inputs") if isinstance(pool, dict) else None
    if (not isinstance(inputs, list) or len(inputs) != pool.get("k")
            or any(not isinstance(item, dict) for item in inputs)
            or any(item.get("effect_input") != "published_ratio_ci" for item in inputs)):
        reasons.append("POOLED_EFFECT_INPUTS_REQUIRE_SOURCE_ADJUDICATION")
    per_trial = review.get("per_trial")
    if not isinstance(per_trial, dict) or not isinstance(ids, list) or set(per_trial) != set(ids):
        reasons.append("PER_TRIAL_ENDPOINTS_NOT_ADJUDICATED")
    else:
        for item in per_trial.values():
            if not isinstance(item, dict) or item.get("estimand") != published.get("estimand") or any(
                not isinstance(item.get(k), str) or not item[k].strip()
                for k in ("outcome", "comparator", "population", "followup", "source_locator")
            ):
                reasons.append("PER_TRIAL_ENDPOINTS_NOT_ADJUDICATED")
                break

    if reasons:
        return verdict
    if not numeric_match:
        verdict["verification_status"] = "SOURCE_COMPARABLE_BUT_NUMERIC_MISMATCH"
        verdict["provenance_reasons"] = ["NUMERIC_MISMATCH"]
        return verdict
    verdict["verification_status"] = "EXTERNALLY_VERIFIED"
    return verdict
