r"""Summary of Findings, DERIVED, for every topic in the store.

WHY THIS EXISTS
    hta_card() renders an AUTHORED block, reader_renderings_2026_08_30.
    renderings.hta. Exactly ONE topic of 141 has one. Every other topic
    renders an empty HTA tab, not because the data is missing but because
    nobody hand-wrote the block.

    The standing test is "would this apply to the next topic without being
    redone?" A hand-authored block fails it by construction. So this derives
    the table from the object's own cells and runs over every topic.

WHAT IT EMITS, per outcome (Cochrane Handbook ch. 14)
    the relative effect and its interval, AS PUBLISHED
    ABSOLUTE effects at a RANGE of baseline risks -- 14.1.3 asks for a range
      of plausible baseline risks, not one assumed number
    number of participants and number of studies
    mechanical GRADE INPUTS, with the downgrade LEFT UNSCORED

WHERE THE BASELINE RANGE COMES FROM, AND WHY IT NEEDS NO ASSUMPTION
    The trials' own control arms. The LOWEST observed control risk, the
    POOLED one, and the HIGHEST. Each is a risk some real population in this
    evidence actually had, so the range is observed rather than assumed --
    which is stronger than the single assumed risk 14.1.3 permits, and it
    carries its own provenance.

    This matters more than it sounds. The same relative effect at the lowest
    and highest observed baselines gives different absolute numbers, and the
    spread inside a single topic reaches sevenfold in this corpus. A single
    baseline hides that; a range shows it.

WHAT IS NOT DONE HERE
    NO COMPOSED PROSE. Every string below is a fixed template in this file.
    Every number is derived at runtime from cells the table also prints.
    Nothing is authored per topic and nothing calls a model.

    GRADE DOWNGRADES ARE NOT SCORED. The mechanical inputs are emitted -- k,
    participants, I-squared, interval width, design -- and the judgement is
    left to a reader. We do not have a panel, and emitting a rating we did
    not convene would be the claim this project exists to refuse.

    An outcome whose 2x2 cells we do not hold is NOT_DERIVABLE_NO_2X2, named
    in the table, never silently dropped.
"""
from __future__ import annotations
import math

# ---------------------------------------------------------------- arithmetic


def _arm_ok(block):
    if isinstance(block, dict) is False:
        return False
    for arm in (block.get("control"), block.get("treatment")):
        if isinstance(arm, dict) is False:
            return False
        for key in ("events", "n"):
            v = arm.get(key)
            if isinstance(v, int) is False or isinstance(v, bool):
                return False
    return True


def _store_ncts(obj):
    inputs = obj.get("inputs")
    trials = inputs.get("trials") if isinstance(inputs, dict) else None
    out = set()
    for t in (trials or []):
        if isinstance(t, dict) and t.get("nct"):
            out.add(str(t["nct"]).upper())
    return out


def sidecar_cells(obj, sidecar):
    """2x2 cells from the topic's sidecar -- ONLY on proven trial identity.

    The sidecar is a different artefact from the store object, and a matching
    NAME is not an identity: ARNI_HF.json and ssot/arni-hfref pool DIFFERENT
    trials, and two other same-named pairs in this corpus share no trial at
    all. So cells are taken only where the two sides share a registration,
    and the row records that the identity was proven rather than assumed.
    """
    if isinstance(sidecar, dict) is False:
        return [], "no sidecar of this topic's name exists"
    cells = [t for t in (sidecar.get("trials") or [])
             if isinstance(t, dict)
             and all(k in t for k in ("tE", "tN", "cE", "cN"))]
    if len(cells) == 0:
        # A NAMED absence, not None. AGYW_HIV_PREP.json is the specimen: two
        # trial rows carrying hazard ratios and no per-arm counts, and no NCT
        # identifiers at all -- so there is nothing to take and nothing to
        # match on. Returning None here made the row say cells_from=None,
        # which tells a reader nothing about why.
        return [], ("a sidecar of this name exists but carries no per-arm "
                    "counts -- %d trial row(s), none with tE/tN/cE/cN"
                    % len(sidecar.get("trials") or []))
    side_ncts = {str(t.get("nct")).upper() for t in cells if t.get("nct")}
    overlap = side_ncts & _store_ncts(obj)
    if len(overlap) == 0:
        return [], ("a sidecar of this name exists and carries cells, but it "
                    "shares no trial registration with this object, so its "
                    "cells are NOT used. A matching name is not an identity.")
    rows = [{"trial": t.get("name") or t.get("nct") or "?",
             "cE": t["cE"], "cN": t["cN"], "tE": t["tE"], "tN": t["tN"]}
            for t in cells]
    return rows, ("the page sidecar for this topic, identity PROVEN by %d "
                  "shared trial registration(s)" % len(overlap))


def cells_for(obj, outcome, sidecar=None):
    """Per-trial 2x2 for ONE outcome, from the cells the effect comes from.

    The store's own by_outcome block first, because it is keyed to THIS
    outcome and is the authority. The sidecar only where the store holds
    nothing, and only on proven trial identity.
    """
    rows = []
    inputs = obj.get("inputs")
    trials = inputs.get("trials") if isinstance(inputs, dict) else None
    for t in (trials or []):
        if isinstance(t, dict) is False:
            continue
        bo = t.get("by_outcome")
        e = bo.get(outcome) if isinstance(bo, dict) else None
        if _arm_ok(e):
            rows.append({
                "trial": t.get("id") or t.get("nct") or "?",
                "cE": e["control"]["events"], "cN": e["control"]["n"],
                "tE": e["treatment"]["events"], "tN": e["treatment"]["n"]})
    if len(rows) > 0:
        return rows, ("this object's own by_outcome.%s.{control,treatment} "
                      "cells, keyed to this outcome" % outcome)
    return sidecar_cells(obj, sidecar)


def baseline_grid(rows):
    """Lowest, pooled and highest OBSERVED control risk, each with its source."""
    risks = [(r["trial"], r["cE"] / r["cN"]) for r in rows if r["cN"] > 0]
    if len(risks) == 0:
        return []
    ce = sum(r["cE"] for r in rows)
    cn = sum(r["cN"] for r in rows)
    lo = min(risks, key=lambda x: x[1])
    hi = max(risks, key=lambda x: x[1])
    grid = [("lowest observed", lo[1], "the control arm of %s" % lo[0]),
            ("pooled", ce / cn, "all control arms: %d of %d" % (ce, cn))]
    if hi[0] != lo[0]:
        grid.append(("highest observed", hi[1], "the control arm of %s" % hi[0]))
    return grid


def absolute_at(measure, point, lo, hi, baseline):
    """Absolute risk at a stated baseline. Returns None where not estimable."""
    if baseline is None or not (0.0 < baseline < 1.0):
        return None
    if isinstance(point, (int, float)) is False or point <= 0:
        return None

    def conv(rel):
        if rel is None:
            return None
        if measure == "RR":
            return baseline * rel
        if measure == "OR":
            oc = baseline / (1.0 - baseline)
            ot = oc * rel
            return ot / (1.0 + ot)
        return None
    r1 = conv(point)
    if r1 is None:
        return None
    out = {"treated_risk": r1, "risk_difference": r1 - baseline,
           "per_1000": (r1 - baseline) * 1000.0}
    a, b = conv(lo), conv(hi)
    if a is not None and b is not None:
        d1, d2 = a - baseline, b - baseline
        out["rd_low"], out["rd_high"] = min(d1, d2), max(d1, d2)
    rd = out["risk_difference"]
    out["nnt"] = (1.0 / abs(rd)) if rd else None
    return out


def grade_inputs(rows, outcome_entry, participants):
    """The MECHANICAL inputs only. The downgrade is deliberately unscored."""
    pooled = outcome_entry.get("pooled")
    pooled = pooled if isinstance(pooled, dict) else {}
    het = outcome_entry.get("heterogeneity")
    i2 = None
    if isinstance(het, dict):
        i2 = het.get("I2") if isinstance(het.get("I2"), (int, float)) else None
    lo, hi = pooled.get("ci_low"), pooled.get("ci_high")
    width = None
    if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo > 0:
        width = hi / lo
    return {
        "studies": len(rows),
        "participants": participants,
        "I2_percent": i2,
        "interval_ratio_high_over_low": width,
        "design": "randomised trials",
        "downgrade": "NOT SCORED -- the inputs above are mechanical; the "
                     "rating is a panel judgement and no panel was convened "
                     "for this table.",
    }


# --------------------------------------------------------------- projection

def sof_rows(obj, sidecar=None):
    """One row per outcome. Every outcome appears; none is dropped."""
    out = []
    res = obj.get("results")
    bo = res.get("by_outcome") if isinstance(res, dict) else None
    if isinstance(bo, dict) is False:
        return out
    for name, entry in bo.items():
        if isinstance(entry, dict) is False:
            continue
        row = {"outcome": name}
        pooled = entry.get("pooled")
        pooled = pooled if isinstance(pooled, dict) else {}

        # the store's own refusal is a STATED REASON, and that is content
        if pooled.get("withdrawn") or entry.get("poolable") is False:
            row["state"] = "DECLINED_BY_THE_STORE"
            row["reason"] = (pooled.get("withdrawn_reason")
                             or entry.get("poolable_reason")
                             or "refused with no reason recorded")
            out.append(row)
            continue

        row["measure"] = pooled.get("measure")
        row["point"] = pooled.get("point")
        row["ci_low"] = pooled.get("ci_low")
        row["ci_high"] = pooled.get("ci_high")
        row["k_recorded"] = entry.get("k")

        rows, provenance = cells_for(obj, name, sidecar)
        row["cells_from"] = provenance
        if len(rows) == 0:
            row["state"] = "NOT_DERIVABLE_NO_2X2"
            row["reason"] = (provenance or
                             "no trial in this object carries both arms' "
                             "events and n for this outcome, and no sidecar "
                             "supplies them on a proven trial identity, so no "
                             "absolute effect and no participant count can be "
                             "derived. The relative effect above is as "
                             "published.")
            out.append(row)
            continue

        row["cells"] = rows
        row["n_studies"] = len(rows)
        row["n_participants"] = sum(r["cN"] + r["tN"] for r in rows)
        row["baseline_grid"] = []
        for label, base, source in baseline_grid(rows):
            abs_eff = absolute_at(row["measure"], row["point"], row["ci_low"],
                                  row["ci_high"], base)
            row["baseline_grid"].append({
                "label": label, "baseline_risk": base, "source": source,
                "absolute": abs_eff,
                "not_estimable_because": None if abs_eff else
                ("the pooled measure is %r, which is not a risk ratio or an "
                 "odds ratio and cannot be applied to a baseline risk without "
                 "an assumption this table does not make" % row["measure"])})
        row["grade_inputs"] = grade_inputs(rows, entry, row["n_participants"])
        row["state"] = "DERIVED"
        out.append(row)
    return out


def summarise(obj, sidecar=None):
    """Counts by state, for a projector that must never silently drop a row."""
    rows = sof_rows(obj, sidecar)
    c = {}
    for r in rows:
        c[r["state"]] = c.get(r["state"], 0) + 1
    return rows, c
