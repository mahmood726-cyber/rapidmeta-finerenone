# -*- coding: utf-8 -*-
"""Emit a `ma-studies-v1` envelope FROM THE SSOT STORE, so a reader can recompute our estimate.

⭐ WHAT THIS IS FOR. allmeta holds 124 browser-based, offline, MIT-licensed analysis tools, and
zero of 1,473 review pages link to any of them. A reader who clicks from our pooled estimate and
RECOMPUTES IT IN THEIR OWN BROWSER is doing something the comparator structurally cannot offer:
RevMan is desktop and subscription, and its data is not in a URL. ***THAT IS THE DIFFERENCE
BETWEEN CLAIMING VERIFIABILITY AND HANDING IT OVER.***

⛔ FROM THE STORE, NOT FROM THE RENDERED PAGE. Scraping our own HTML would make the envelope a
copy of a copy: it would agree with the page by construction and could not detect a rendering
fault. Reading the object means the envelope and the page are two independent derivations of the
same fields, and a disagreement between them is a real finding.

⛔ KEYED FROM THE REGISTRY IDENTIFIER, LABEL DERIVED. The two dapivirine trials were once
INVERTED in this store -- the estimates were right and every sentence naming a trial was wrong,
and six blinded judges caught none of it. So the envelope carries the NCT, and the display label
is built from the registry's own acronym and sponsor study id rather than from our `label` field.
`plant_inversion()` inverts both labels and asserts the envelope is unmoved.

⚠️ LOG SCALE FOR RATIOS, per the bus spec: `est = ln(RR)`, `se` on the same scale. The spec's
own worked example is OR 1.5 [1.1, 2.1] -> est 0.405, se 0.165. Back-transformation happens at
the display layer, never in the bus.
"""
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCHEMA = "ma-studies-v1"

RATIO_MEASURES = ("RR", "OR", "HR", "IRR")


def _utf8():
    if not getattr(sys.stdout, "_env_wrapped", False):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace", line_buffering=True)
        sys.stdout._env_wrapped = True


def registry_label(nct, root=None):
    """The DISPLAY label, built from the registry's own fields. Never from our `label`."""
    p = os.path.join(root or os.path.join(REPO, "evidence", "acquisition"),
                     nct, "registry.txt")
    if not os.path.exists(p):
        return None
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return None
    idm = (d.get("protocolSection") or {}).get("identificationModule") or {}
    acr = idm.get("acronym")
    org = (idm.get("orgStudyIdInfo") or {}).get("id")
    bits = [x for x in (acr, org) if x]
    return "%s (%s)" % (" / ".join(bits), nct) if bits else nct


def _pair(arms):
    """(treatment, control) read from the ROLE, never from label order."""
    t = next((a for a in arms if str(a.get("role", "")).lower() == "treatment"), None)
    c = next((a for a in arms if str(a.get("role", "")).lower() == "control"), None)
    return t, c


def _counts(trial):
    """The 2x2 this object stands behind, with the TIER it came from.

    Prefers `arms_basis.tier` -- the object's own declaration of which tier its arms use --
    rather than picking a tier here. A component that chose its own tier could quietly select
    the one that gives a nicer answer.
    """
    basis = trial.get("arms_basis") or {}
    tier = basis.get("tier")
    tiers = ((trial.get("counts_by_tier") or {}).get("tiers") or {})
    row = tiers.get(tier)
    if row and all(row.get(k) is not None for k in
                   ("treatment_events", "treatment_n", "control_events", "control_n")):
        return row, tier
    t, c = _pair(trial.get("arms") or [])
    if t and c and t.get("events") is not None and c.get("events") is not None:
        return ({"treatment_events": t.get("events"), "treatment_n": t.get("n"),
                 "control_events": c.get("events"), "control_n": c.get("n")},
                basis.get("tier") or "arms")
    return None, None


def build(canon, outcome_id="primary", root=None):
    """-> (envelope, notes). Refuses rather than guessing."""
    notes = []
    res = ((canon.get("results") or {}).get("by_outcome") or {}).get(outcome_id) or {}
    measure = (res.get("pooled") or {}).get("measure") or res.get("measure")
    if measure not in RATIO_MEASURES:
        return None, ["measure %r is not a ratio; the log-scale rule does not apply and this "
                      "component will not guess a scale" % measure]
    studies = []
    for trial in (canon.get("inputs") or {}).get("trials", []):
        nct = trial.get("nct")
        if not nct:
            notes.append("a trial with no NCT was skipped: the bus row would have no "
                         "checkable identity")
            continue
        row, tier = _counts(trial)
        if not row:
            notes.append("%s skipped: no complete 2x2 in the object" % nct)
            continue
        a, n1 = float(row["treatment_events"]), float(row["treatment_n"])
        b, n2 = float(row["control_events"]), float(row["control_n"])
        if min(a, b) <= 0 or n1 <= 0 or n2 <= 0:
            notes.append("%s skipped: a zero cell needs a continuity decision, which is a "
                         "METHODS choice and is not made here" % nct)
            continue
        rr = (a / n1) / (b / n2)
        se = math.sqrt(1.0 / a - 1.0 / n1 + 1.0 / b - 1.0 / n2)
        studies.append({
            "label": registry_label(nct, root) or nct,
            "est": round(math.log(rr), 10),
            "se": round(se, 10),
            "moderator": None, "group": None, "year": None,
            "_nct": nct, "_tier": tier,
            "_counts": {"treatment_events": int(a), "treatment_n": int(n1),
                        "control_events": int(b), "control_n": int(n2)},
        })
    env = {"_schema": SCHEMA, "_savedAt": None, "studies": studies,
           "_measure": measure, "_scale": "log",
           "_provenance": ("Derived from this review's SSOT object, not from its rendered page. "
                           "Each row is keyed to its ClinicalTrials.gov identifier and its "
                           "display label is built from the registry's own acronym and sponsor "
                           "study id, never from a label stored on our own object.")}
    return env, notes


class MixedBasis(Exception):
    """Raised when a pool would mix count bases across trials."""


def assert_one_basis(studies):
    """⛔ EVERY STUDY IN A POOL MUST SHARE A COUNT BASIS.

    THIS GUARD EXISTS BECAUSE A SCHEMA CAUGHT WHAT VIGILANCE WOULD NOT HAVE. Asking both
    dapivirine trials for their "adjudicated publication" counts crashed on a bare `None`,
    because only ONE of them has that tier: the Ring Study holds `external review citing the
    adjudicated publication`, ASPIRE holds `trial report`. Had the missing tier silently fallen
    back to the registry counts, the result would have been THE RING STUDY'S ADJUDICATED COUNTS
    POOLED WITH ASPIRE'S REGISTRY COUNTS, presented as one basis.

    ⚠️ That is the estimand-mixing class this project has already paid for. A pooled number
    whose inputs come from two different provenance tiers is not the quantity its label claims,
    and nothing downstream can detect it -- the arithmetic is impeccable and the inputs are not
    comparable.

    ⭐ SO THE FAILURE NAMES BOTH TIERS AND BOTH TRIALS rather than raising `NoneType is not
    subscriptable`. A structure that encodes a methodological assumption enforces it; a habit
    of remembering does not.
    """
    tiers = {}
    for r in studies:
        tiers.setdefault(r.get("_tier"), []).append(r.get("_nct") or r.get("label"))
    if None in tiers:
        raise MixedBasis(
            "a study carries no declared count basis: %s. A pool needs every input to say "
            "which tier its counts came from." % ", ".join(str(x) for x in tiers[None]))
    if len(tiers) > 1:
        detail = "; ".join("%r <- %s" % (t, ", ".join(v)) for t, v in sorted(tiers.items()))
        raise MixedBasis(
            "MIXED COUNT BASIS -- this pool would combine %d different provenance tiers: %s. "
            "The arithmetic would succeed and the result would not be the quantity its label "
            "claims. Choose ONE basis for all studies, or publish the bases separately."
            % (len(tiers), detail))
    return list(tiers)[0]


def pool_dl(env):
    """DerSimonian-Laird random effects, on the bus's own log-scale values.

    ⚠️ This exists to CHECK the envelope against our published estimate, not to publish a new
    one. If it disagrees with the page, that disagreement is the finding.
    """
    s = env["studies"]
    if any("_tier" in r for r in s):        # bus rows carry no _tier; ours do
        assert_one_basis(s)
    w = [1.0 / (r["se"] ** 2) for r in s]
    y = [r["est"] for r in s]
    fe = sum(wi * yi for wi, yi in zip(w, y)) / sum(w)
    q = sum(wi * (yi - fe) ** 2 for wi, yi in zip(w, y))
    df = len(s) - 1
    c = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    w2 = [1.0 / (r["se"] ** 2 + tau2) for r in s]
    mu = sum(wi * yi for wi, yi in zip(w2, y)) / sum(w2)
    se = math.sqrt(1.0 / sum(w2))
    return {"tau2": tau2, "Q": q, "df": df, "mu_log": mu, "se_log": se,
            "point": math.exp(mu), "ci_low": math.exp(mu - 1.959964 * se),
            "ci_high": math.exp(mu + 1.959964 * se)}


def plant_inversion(canon, root=None):
    """⭐ INVERT BOTH LABELS AND ASSERT THE ENVELOPE IS UNMOVED."""
    _utf8()
    a, notes = build(canon, root=root)
    flipped = json.loads(json.dumps(canon))
    ts = flipped["inputs"]["trials"]
    ts[0]["label"], ts[1]["label"] = ts[1]["label"], ts[0]["label"]
    b, _ = build(flipped, root=root)
    same = json.dumps(a["studies"], sort_keys=True) == json.dumps(b["studies"], sort_keys=True)
    print("")
    print("PLANT -- label inversion")
    print("   both labels swapped in the object; envelope identical   %-5s [%s]"
          % (same, "PASS" if same else "FAIL"))
    print("   ⚠️ the store once carried these two trials INVERTED, the estimates were")
    print("      right, every sentence naming a trial was wrong, and six blinded judges")
    print("      caught none of it. This is the check that would have.")
    assert same, "the envelope followed our label -- it is not keyed to the registry"
    return 0


def plant_mixed_basis():
    """⭐ BOTH WAYS: one basis pools, two bases REFUSE and name what they mixed."""
    _utf8()
    same = [{"label": "A", "est": -0.4, "se": 0.16, "_tier": "registry results", "_nct": "NCT1"},
            {"label": "B", "est": -0.3, "se": 0.15, "_tier": "registry results", "_nct": "NCT2"}]
    mixed = [dict(same[0]),
             dict(same[1], _tier="external review citing the adjudicated publication")]
    ok_same = pool_dl({"studies": same}) is not None
    try:
        pool_dl({"studies": mixed})
        ok_mixed, msg = False, "(no refusal)"
    except MixedBasis as exc:
        ok_mixed, msg = True, str(exc)
    print("")
    print("PLANT -- one basis per pool")
    print("   two studies, SAME basis  -> pools            %-5s [%s]"
          % (ok_same, "PASS" if ok_same else "FAIL"))
    print("   two studies, TWO bases   -> REFUSES          %-5s [%s]"
          % (ok_mixed, "PASS" if ok_mixed else "FAIL"))
    print("   refusal text: %s" % msg[:150])
    print("   ⚠️ the refusal NAMES both tiers and both trials. A bare")
    print("      'NoneType is not subscriptable' is a crash, not a finding.")
    assert ok_same and ok_mixed
    return 0
