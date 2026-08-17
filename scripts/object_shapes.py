"""One reader for the two trial-carrying object schemas in this repo.

WHY THIS EXISTS
    `arm_identity_gate` and `poolability` returned UNCHECKABLE and UNASSESSABLE
    on 100% of a real v1 object. Neither was broken: both read
    `canonical.trials[]`, the extraction artefact's shape, while the v1 objects
    carry `inputs.trials[]`. Two of the standard's own properties were unmeasured
    on the architecture the standard exists to describe, and I had been citing
    both as coverage.

    A gate pointed at the wrong schema does not announce itself. It reports the
    honest thing it can see -- nothing -- and if it had defaulted that to PASS
    instead of UNCHECKABLE, every cardiology topic would have shipped with green
    properties. That is why this file exists rather than a quiet `or {}`.

WHAT THIS DOES NOT DO
    - It does NOT invent a field. A schema that carries no arms yields no arms,
      and the caller must report UNCHECKABLE rather than assume two.
    - It does NOT reconcile the two schemas' semantics. It exposes what each one
      states, and where they disagree the caller decides.
"""
from __future__ import annotations


def trials_of(obj):
    """-> list of normalised trials from EITHER schema. Empty list is honest."""
    out = []

    # SSOT / v1 objects
    for t in ((obj.get("inputs") or {}).get("trials")) or []:
        arms = []
        for a in (t.get("arms") or []):
            arms.append({"label": a.get("label") or "", "role": a.get("role") or ""})
        out.append({
            "id": t.get("nct") or t.get("id") or "",
            "nct": t.get("nct") or "",
            "name": t.get("name") or "",
            "arms": arms,
            "comparator_type": t.get("comparator_type") or "",
            "_schema": "ssot",
            "_raw": t,
        })
    if out:
        return out

    # extraction canonical artefacts
    for t in ((obj.get("canonical") or {}).get("trials")) or []:
        arms = []
        for key in ("intervention", "comparator"):
            v = t.get(key)
            if isinstance(v, dict):
                arms.append({"label": v.get("label") or v.get("name") or "",
                             "role": "treatment" if key == "intervention" else "control"})
            elif isinstance(v, str) and v:
                arms.append({"label": v,
                             "role": "treatment" if key == "intervention" else "control"})
        for a in (t.get("arms") or []):
            if isinstance(a, dict):
                arms.append({"label": a.get("label") or "", "role": a.get("role") or ""})
        out.append({
            "id": t.get("nct") or t.get("id") or "",
            "nct": t.get("nct") or "",
            "name": t.get("name") or t.get("label") or "",
            "arms": arms,
            "comparator_type": t.get("comparator_type") or "",
            "_schema": "canonical",
            "_raw": t,
        })
    return out


def pooled_of(obj):
    """-> (k, pooled_dict) from either schema, or (None, {})."""
    by = ((obj.get("results") or {}).get("by_outcome")) or {}
    for res in by.values():
        p = res.get("pooled") or {}
        if p.get("point") is not None:
            return res.get("k"), p
    rep = (((obj.get("canonical") or {}).get("result")) or {}).get("reported") or {}
    if rep:
        return rep.get("k"), rep
    return None, {}


def schema_of(obj):
    if ((obj.get("inputs") or {}).get("trials")):
        return "ssot"
    if ((obj.get("canonical") or {}).get("trials")):
        return "canonical"
    return "unknown"
