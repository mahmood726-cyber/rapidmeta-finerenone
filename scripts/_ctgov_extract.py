"""Extract a clean 2x2 (treatment vs control event counts) from a ctgov study
JSON, or return None when it cannot be done unambiguously.

Conservative by design: a wrong outcome/arm pick injects new bad data, so every
ambiguity (no >=2-group binary outcome, no identifiable control, non-integer or
impossible counts) returns None -> caller nulls the trial instead of guessing.
"""
import re

_CONTROL_RE = re.compile(r"\b(placebo|control|standard|usual care|comparator|sham|vehicle)\b", re.I)
_CONTINUOUS_PARAM = {"MEAN", "LEAST_SQUARES_MEAN", "MEDIAN", "GEOMETRIC_MEAN"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _group_n(om):
    """groupId -> N from denoms (prefer the analysed-participants denom)."""
    out = {}
    for den in om.get("denoms", []):
        for c in den.get("counts", []):
            n = _num(c.get("value"))
            if n is not None:
                out[c["groupId"]] = n
    return out


def _events_by_group(om):
    """groupId -> event count for a count-of-participants outcome (first class)."""
    classes = om.get("classes", [])
    if not classes:
        return {}
    cls = classes[0]
    out = {}
    for cat in cls.get("categories", []):
        for m in cat.get("measurements", []):
            v = _num(m.get("value"))
            if v is not None:
                out[m["groupId"]] = out.get(m["groupId"], 0) + v
    return out


def _candidate_outcomes(study):
    oms = study.get("resultsSection", {}).get("outcomeMeasuresModule", {}).get("outcomeMeasures", [])
    cands = []
    for o in oms:
        groups = o.get("groups", [])
        if len(groups) < 2:
            continue
        if o.get("paramType") in _CONTINUOUS_PARAM:
            continue
        unit = (o.get("unitOfMeasure") or "").lower()
        title = (o.get("title") or "").lower()
        # skip clearly continuous endpoints
        if "change" in title or "change" in unit or "mean" in unit:
            continue
        cands.append(o)
    return cands


def extract_2x2(study, want_title=None):
    """Return {tE,tN,cE,cN, outcome, groups} or None."""
    cands = _candidate_outcomes(study)
    if not cands:
        return None

    def score(o):
        s = 0
        if o.get("type") == "PRIMARY":
            s += 2
        if want_title:
            wt = set(re.findall(r"[a-z0-9]+", want_title.lower()))
            ot = set(re.findall(r"[a-z0-9]+", (o.get("title") or "").lower()))
            s += len(wt & ot)
        return s

    for om in sorted(cands, key=score, reverse=True):
        groups = om.get("groups", [])
        gtitle = {g["id"]: g.get("title", "") for g in groups}
        controls = [gid for gid, t in gtitle.items() if _CONTROL_RE.search(t)]
        treatments = [gid for gid in gtitle if gid not in controls]
        if len(controls) != 1 or not treatments:
            continue  # ambiguous control structure -> try next candidate
        cgid = controls[0]
        # prefer a single non-control treatment arm; if several (dose-ranging),
        # ambiguous which to pool -> skip to stay honest
        if len(treatments) != 1:
            continue
        tgid = treatments[0]
        ns = _group_n(om)
        es = _events_by_group(om)
        is_pct = "percent" in (om.get("unitOfMeasure") or "").lower() or "%" in (om.get("unitOfMeasure") or "")
        tN, cN = ns.get(tgid), ns.get(cgid)
        if not tN or not cN:
            continue
        if is_pct:
            tE = round(es.get(tgid, 0) / 100.0 * tN) if tgid in es else None
            cE = round(es.get(cgid, 0) / 100.0 * cN) if cgid in es else None
        else:
            tE, cE = es.get(tgid), es.get(cgid)
        if tE is None or cE is None:
            continue
        tE, tN, cE, cN = int(round(tE)), int(round(tN)), int(round(cE)), int(round(cN))
        if not (0 <= tE <= tN and 0 <= cE <= cN and tN > 0 and cN > 0):
            continue
        return {"tE": tE, "tN": tN, "cE": cE, "cN": cN,
                "outcome": om.get("title", "")[:80],
                "treatment": gtitle[tgid][:40], "control": gtitle[cgid][:40]}
    return None
