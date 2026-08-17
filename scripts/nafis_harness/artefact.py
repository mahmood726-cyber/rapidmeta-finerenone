"""Adapters: a build artefact in, detector payloads out.

THE HONEST SCOPE, STATED BEFORE THE CODE
----------------------------------------
Not all 33 AVAILABLE detectors can run at push time. Some need retrieval context
that only exists while a lane is working -- an HTTP status, a click's post-state,
a route log, a source document's wording. Running those against a static artefact
would produce INVALID for every page, and a gate that emits mostly INVALID gets
bypassed. The pre-push hook's own header records where that leads:

    "a push sat in a headless-browser walk for hours. That is what made bypassing
     it feel reasonable, which is how a broken guard survives."

So the detectors are partitioned, and the partition is published rather than
implied:

    ARTEFACT_DECIDABLE   everything needed is in the page/object. These run in
                         the pre-push gate and can block.
    RETRIEVAL_SCOPED     needs live context. These belong in the retrieval lanes,
                         called at the moment the observation is made.

A detector in RETRIEVAL_SCOPED is NOT guarded by the build gate, and the ledger
must not count it as if it were. That is the whole reason this partition is a
data structure and not a comment.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

ARTEFACT_DECIDABLE = [
    "CHK002_TOKEN_MATCH",
    "CHK005_EXTERNAL_REFERENT",
    "CHK006_IDENTITY_KEY",
    "CHK008_FRAME_DENOMINATOR",
    "CHK009_POOL_IDENTITY",
    "CHK013_FIELD_SEMANTICS",
    "CHK016_PRECISION_SAMPLE_MISMATCH",
    "CHK017_DUP1_BIT_EQUALITY",
    "CHK018_MIXED_POOLING",
    "CHK019_INERT_ENGINE",
    "CHK020_ORPHAN_POOLED_RESULT",
    "CHK021_MEASURE_SCALE_MISMATCH",
    "CHK023_CROSS_AGENT_POOLING",
    "CHK024_FALSE_METHOD_CLAIM",
    "CHK025_MULTI_SURFACE_DISAGREEMENT",
    "CHK026_WRONG_REASON_ABSENCE_PANEL",
    "CHK027_SENTINEL_LEAK",
    "CHK028_DISQUALIFIED_REFERENT_PROMOTED",
    "CHK029_SIGN_NORMALISATION",
    "CHK030_BUILD_MODE_BLIND_TEXT",
]

RETRIEVAL_SCOPED = [
    "CHK001_RETRIEVAL_ABSENCE",     # needs an HTTP status
    "CHK003_ACTION_EFFECT",         # needs a pre/post state around an action
    "CHK004_LIVENESS",              # needs a live process probe
    "CHK007_ABSENCE_SCREEN",        # needs a screen execution record
    "CHK010_CHAIN_EXHAUSTION",      # needs a route log
    "CHK011_CORRECTION_BURDEN",     # needs the provenance of a correction
    "CHK012_LAYER_MATCH",           # needs the claim's layer, declared by a human
    "CHK014_FILTER_FIRED",          # needs the returned URLs of a live search
    "CHK015_HIT_COUNT_SANITY",      # needs a live query's hit count
    "CHK022_RATIO_FROM_PERCENTAGE", # needs the source document's wording
]

DEFAULT_SENTINELS = ["NOT RECOVERABLE FROM THE PAGE", "__PLACEHOLDER__", "TODO:",
                     "{{", "NaN%", "undefined", "None", "[object Object]"]


def payloads_for(artefact: Mapping[str, Any]) -> list[tuple[str, dict]]:
    """Yield (check_id, payload) for every artefact-decidable check that applies.

    A check whose inputs are absent from the artefact is NOT emitted. Emitting it
    would return INVALID, and a wall of INVALIDs is indistinguishable from a
    broken gate. Absence of a payload is reported as NOT APPLICABLE by the gate,
    which is a different statement from "checked and clean".
    """
    out: list[tuple[str, dict]] = []
    page = artefact.get("page_id") or artefact.get("id") or "<unnamed>"

    # --- engine wiring -----------------------------------------------------
    if artefact.get("engine_trial_ids") is not None and \
            artefact.get("data_trial_ids") is not None:
        out.append(("CHK019_INERT_ENGINE",
                    {"page_id": page,
                     "engine_trial_ids": artefact["engine_trial_ids"],
                     "data_trial_ids": artefact["data_trial_ids"]}))

    # ONE PAYLOAD PER OUTCOME. The orphan check compares a DISPLAYED value with
    # the verdict on whether it can be computed, and both of those are per
    # estimand. A single payload per page joined a value from one outcome to a
    # reason from another and reported a defect that did not exist -- see the
    # exporter's note on SOTAGLIFLOZIN 0.7488. The locator names the estimand so
    # a FAIL says WHICH pool is orphaned rather than which page.
    caps = artefact.get("pool_capability")
    if caps:
        for cap in caps:
            if cap.get("engine_can_pool") is None:
                continue
            out.append(("CHK020_ORPHAN_POOLED_RESULT",
                        {"page_id": "%s::%s" % (page, cap.get("outcome_id") or "?"),
                         "displayed_pooled_estimate":
                             cap.get("displayed_pooled_estimate"),
                         "engine_can_pool": cap["engine_can_pool"],
                         "engine_block_reason": cap.get("engine_block_reason")}))
    elif artefact.get("engine_can_pool") is not None:
        # Older artefacts still carry the flattened triple. Read rather than
        # ignored, because dropping the fallback would silently stop checking
        # every artefact produced before this change -- a coverage loss that
        # looks exactly like a clean run.
        out.append(("CHK020_ORPHAN_POOLED_RESULT",
                    {"page_id": page,
                     "displayed_pooled_estimate":
                         artefact.get("displayed_pooled_estimate"),
                     "engine_can_pool": artefact["engine_can_pool"],
                     "engine_block_reason": artefact.get("engine_block_reason")}))

    # --- rendered text -----------------------------------------------------
    if artefact.get("reader_text") is not None:
        out.append(("CHK027_SENTINEL_LEAK",
                    {"surface_id": page, "reader_text": artefact["reader_text"],
                     "sentinels": artefact.get("sentinels") or DEFAULT_SENTINELS}))

    # --- absence panels / build-path conditioning ---------------------------
    for panel in artefact.get("absence_panels") or []:
        out.append(("CHK026_WRONG_REASON_ABSENCE_PANEL",
                    {"page_id": page,
                     "page_provenance": artefact.get("page_provenance"),
                     **panel}))
    for s in artefact.get("rationale_strings") or []:
        out.append(("CHK030_BUILD_MODE_BLIND_TEXT",
                    {"build_path": artefact.get("build_path"), **s}))

    # --- method claim ------------------------------------------------------
    if artefact.get("claimed_method"):
        out.append(("CHK024_FALSE_METHOD_CLAIM",
                    {"page_id": page, "claimed_method": artefact["claimed_method"],
                     "network_edges": artefact.get("network_edges") or []}))

    # --- pools -------------------------------------------------------------
    for pool in artefact.get("pools") or []:
        pid = pool.get("pool_id") or pool.get("panel_name") or page
        entries = pool.get("entries") or []
        if pool.get("panel_rows"):
            out.append(("CHK009_POOL_IDENTITY", {"panel_name": pid, **pool}))
        if len(entries) >= 2:
            if all("estimate" in e for e in entries):
                out.append(("CHK017_DUP1_BIT_EQUALITY",
                            {"pool_id": pid, "entries": entries,
                             "pooled_estimate": pool.get("pooled_estimate")}))
            if all(e.get("measure") and e.get("direction_of_benefit")
                   for e in entries):
                out.append(("CHK018_MIXED_POOLING",
                            {"pool_id": pid, "entries": entries,
                             "composite_endpoint": pool.get("composite_endpoint")}))
            if all(e.get("intervention") for e in entries):
                out.append(("CHK023_CROSS_AGENT_POOLING",
                            {"pool_id": pid, "entries": entries,
                             "declared_class": pool.get("declared_class")}))

    # --- rows --------------------------------------------------------------
    for row in artefact.get("rows") or []:
        rid = row.get("row_id") or row.get("id") or page
        if all(k in row for k in ("ci_low", "ci_high", "events_t", "n_t",
                                  "events_c", "n_c")):
            out.append(("CHK016_PRECISION_SAMPLE_MISMATCH", {"row_id": rid, **row}))
        if row.get("measure") and row.get("stored_scale"):
            out.append(("CHK021_MEASURE_SCALE_MISMATCH", {"row_id": rid, **row}))
        if row.get("registration_id") is not None or row.get("claimed_name"):
            out.append(("CHK006_IDENTITY_KEY", {**row}))
        if row.get("external_referent") is not None:
            out.append(("CHK005_EXTERNAL_REFERENT", {**row}))

    # --- raw numeric strings ------------------------------------------------
    for f in artefact.get("numeric_fields") or []:
        if "raw" in f and "naive_value" in f:
            out.append(("CHK029_SIGN_NORMALISATION", {**f}))

    # --- claims across surfaces --------------------------------------------
    for claim in artefact.get("claims") or []:
        if claim.get("surfaces"):
            out.append(("CHK025_MULTI_SURFACE_DISAGREEMENT", {**claim}))
        if claim.get("card") and claim.get("object"):
            out.append(("CHK028_DISQUALIFIED_REFERENT_PROMOTED", {**claim}))

    # --- coverage claims ----------------------------------------------------
    for c in artefact.get("coverage_claims") or []:
        out.append(("CHK008_FRAME_DENOMINATOR", {**c}))

    return out
