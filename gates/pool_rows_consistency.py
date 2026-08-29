"""Q4 and S1 -- the pool and the rows behind it must agree, or the block must refuse.

LINEAGE.
  Q4, register: "pooled k disagreeing with the rows behind it". Gate 10 has carried this class
  at ZERO with a probe that computes the disagreement only to prove its own fixture is really
  defective, then reports that nothing we own looks.
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
    for key in ("certainty", "grade", "grade_certainty", "certainty_of_evidence"):
        v = block.get(key)
        if v not in (None, "", {}, []):
            return True, "a certainty rendered over it (%s)" % key
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

        # ---- Q4: k stated, rows present, and they disagree -------------------
        if isinstance(k, int) and isinstance(per_trial, list) and per_trial:
            if k != len(per_trial):
                rows.append({
                    "cls": "Q4", "topic": topic, "outcome": oid, "k": k,
                    "rows": len(per_trial), "refusal": why,
                    "detail": ("outcome %r states k=%d over %d rows. A reader takes k as the "
                               "number of studies behind the estimate; the rows are what is "
                               "actually there.%s"
                               % (oid, k, len(per_trial),
                                  " The block also declares a refusal (%s), so the disagreement "
                                  "is not excused by it -- a refusal with rows still publishes "
                                  "those rows." % why if refused else "")),
                })

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
