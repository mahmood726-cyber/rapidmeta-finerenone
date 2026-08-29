"""S1 -- a result published with no rows behind it, and no refusal.

Q4 WAS HERE AND HAS BEEN RETIRED FROM THIS MODULE, 2026-08-29. Two lanes instrumented Q4
independently. Cross-run against both plant sets, `count_matches_rows.findings` scored 7/7 on
positives where this module scored 1/7 -- it DERIVES the count/row pairing from the naming
relation and reaches every block, where this one only ever looked at
`results.by_outcome.<id>.k` against `per_trial`. It keeps the class.

What survived from this side is the DECLARED-REFUSAL exclusion, which was merged INTO that
module: on the real corpus it returned 38 findings to this module's 1, and 37 of the 38 were
blocks declaring they decline to pool while stating the k they WOULD have pooled. Merged, it
scores 7/7 positives, 11/11 negatives and 1 corpus finding.

LINEAGE.
  S1, register C8: "An outcome published with ZERO check payloads behind it -- and, worse, a
  CERTAINTY over it", with the standing warning to DISTINGUISH ABSENT FROM UNEXPORTED.

THE STRUCTURAL BOUNDARY, AND WHY THERE IS NOTHING TO TUNE. A block that declines to pool is a
different KIND of object from a block that pools. 95 of the 96 row-less blocks in this corpus
carry `poolable: false` or `the_pool_this_refusal_declines_to_report` -- they state k as the
number of trials they WOULD have pooled and then refuse, which is the behaviour the project
wants and the model answer for this class. So the discriminator is the declared refusal state,
a typed field, not a count and not a threshold. Excluding refusals by a number (say, "ignore
blocks with fewer than 2 rows") would fit one page and silently weaken every other.
"""
from __future__ import annotations

REFUSAL_MARKER = "the_pool_this_refusal_declines_to_report"

# NO KEY VOCABULARY. The first version asked whether the block held a key named `certainty`,
# `grade`, `grade_certainty` or `certainty_of_evidence`. Measured against this corpus that hand
# list MISSED 5 of the 7 distinct certainty-ish key names present -- and it missed them in the
# dangerous direction, where a certainty under an unlisted name means the check stays silent.
# Extending the list would have been the open-vocabulary defect for the eighth time.
#
# So the question is asked of the VALUE instead of the key: GRADE defines exactly four levels,
# and that vocabulary is closed by the GRADE handbook rather than by us. Any key at all whose
# value IS one of those levels is a certainty rating; prose fields such as
# `certainty_derivation` or `what_this_certainty_is_about` hold sentences, not levels, and are
# correctly not read as ratings. There is no list here to fall behind the corpus.
GRADE_LEVELS = ("high", "moderate", "low", "very low")


def _is_grade_level(v):
    if not isinstance(v, str):
        return False
    norm = " ".join(v.strip().lower().replace("_", " ").replace("-", " ").split())
    return norm in GRADE_LEVELS


def is_refusal(block):
    """Does this block DECLARE that it declines to pool? Typed field, not inference."""
    if block.get("poolable") is False:
        return True, "poolable=false"
    if REFUSAL_MARKER in block:
        return True, REFUSAL_MARKER
    reason = block.get("poolable_reason")
    if block.get("poolable") is None and isinstance(reason, str) and reason.strip():
        return True, "poolable_reason stated with poolable unset"
    return False, None


def asserts_a_result(block):
    """Does the block publish something a reader would take as a result over these rows?"""
    pooled = block.get("pooled")
    if isinstance(pooled, dict) and any(v is not None for v in pooled.values()):
        return True, "a populated `pooled` block"
    for key, v in block.items():
        if _is_grade_level(v):
            return True, "a GRADE level rendered over it (%s=%r)" % (key, v)
    return False, None


def scan(obj, topic="fixture"):
    """(rows, seen). Q4 and S1 findings over one topic object's outcome blocks."""
    rows = []
    seen = {"outcome_blocks": 0, "blocks_stating_k": 0, "blocks_with_rows": 0,
            "declared_refusals": 0}
    by_outcome = ((obj.get("results") or {}).get("by_outcome") or {})
    for oid, block in by_outcome.items():
        if not isinstance(block, dict):
            continue
        seen["outcome_blocks"] += 1
        k = block.get("k")
        per_trial = block.get("per_trial")
        refused, why = is_refusal(block)
        if refused:
            seen["declared_refusals"] += 1
        if isinstance(k, int):
            seen["blocks_stating_k"] += 1
        if isinstance(per_trial, list) and per_trial:
            seen["blocks_with_rows"] += 1

        # ---- S1: a result asserted with no rows behind it, and no refusal -----
        if not per_trial and not refused:
            asserts, what = asserts_a_result(block)
            if asserts:
                rows.append({
                    "cls": "S1", "topic": topic, "outcome": oid, "k": k, "rows": 0,
                    "refusal": None,
                    "detail": ("outcome %r publishes %s with ZERO rows behind it and declares "
                               "no refusal. Absent is not the same as unexported: a block that "
                               "holds nothing must say so." % (oid, what)),
                })
    return rows, seen
