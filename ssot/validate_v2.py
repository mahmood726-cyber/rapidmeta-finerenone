#!/usr/bin/env python
"""Schema-v2 validator: multi-outcome, k>1.

v1 (`validate.py`) stays frozen with the golden reference. This adds the checks
that only become possible once k>1, and the first of them is the one the whole
batch phase exists to test:

    RECOMPUTE THE POOLED NUMBER FROM THE PER-TRIAL INPUTS AND COMPARE.

At k=1 there was no pooling arithmetic, so every detector could only compare
labels to labels. This one can catch a pooled estimate that is simply WRONG.
"""
from __future__ import annotations

import io
import json
import math
import pathlib
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

Z = {90: 1.644853627, 95: 1.959963985, 99: 2.575829304}


class Report:
    def __init__(self):
        self.blocks: list[tuple[str, str]] = []
        self.passes: list[str] = []

    def block(self, rule, msg):
        self.blocks.append((rule, msg))


# --------------------------------------------------------------- pooling
def _log_rr(tE, tN, cE, cN):
    """log RR and its variance, with a 0.5 correction ONLY when a cell is zero."""
    if 0 in (tE, cE, tN - tE, cN - cE):
        tE, cE, tN, cN = tE + 0.5, cE + 0.5, tN + 1, cN + 1
    y = math.log((tE / tN) / (cE / cN))
    v = 1 / tE - 1 / tN + 1 / cE - 1 / cN
    return y, v


def _log_or(tE, tN, cE, cN):
    if 0 in (tE, cE, tN - tE, cN - cE):
        tE, cE, tN, cN = tE + 0.5, cE + 0.5, tN + 1, cN + 1
    a, b, c, d = tE, tN - tE, cE, cN - cE
    return math.log((a * d) / (b * c)), 1 / a + 1 / b + 1 / c + 1 / d


def pool_generic(effects, estimator, level=95, log_scale=False):
    """Inverse-variance pooling from per-trial EFFECT + INTERVAL.

    Extension forced by alirocumab: its trials report a least-squares mean
    difference from each trial's own model, not a 2x2. There are no counts to
    pool, so the variance comes from the published interval. For a ratio measure
    the pooling happens on the log scale; for a mean difference it does not.
    """
    ys, vs = [], []
    for e in effects:
        z = Z.get(e.get("ci_level", level))
        if z is None:
            return None
        if log_scale:
            y = math.log(e["point"])
            se = (math.log(e["ci_high"]) - math.log(e["ci_low"])) / (2 * z)
        else:
            y = e["point"]
            se = (e["ci_high"] - e["ci_low"]) / (2 * z)
        if se <= 0:
            return None
        ys.append(y); vs.append(se * se)
    w = [1 / v for v in vs]
    fe = sum(a * b for a, b in zip(w, ys)) / sum(w)
    Q = sum(wi * (yi - fe) ** 2 for wi, yi in zip(w, ys))
    df = len(ys) - 1
    if estimator.lower().startswith(("dersimonian", "dl")):
        C = sum(w) - sum(x * x for x in w) / sum(w)
        tau2 = max(0.0, (Q - df) / C) if C > 0 else 0.0
    elif estimator.lower() in ("fixed", "none", "iv", "inverse variance"):
        tau2 = 0.0
    else:
        return None
    wr = [1 / (v + tau2) for v in vs]
    mu = sum(a * b for a, b in zip(wr, ys)) / sum(wr)
    se = math.sqrt(1 / sum(wr))
    z = Z[level]
    i2 = max(0.0, 100 * (Q - df) / Q) if Q > 0 else 0.0
    f = math.exp if log_scale else (lambda x: x)
    return dict(point=f(mu), ci_low=f(mu - z * se), ci_high=f(mu + z * se),
                tau2=tau2, i2=i2, q=Q, df=df)


COUNT_POOLABLE = {"RR", "OR"}


def pool(rows, measure, estimator, level=95):
    """Inverse-variance pooling, implemented here so the check is independent of
    whatever produced the recorded number.

    Only measures that can actually be computed from a 2x2 are accepted. An
    earlier version sent everything that was not OR to the RR path, so an
    outcome relabelled HR was still pooled as a risk ratio and the mislabel was
    invisible. A hazard ratio needs time-to-event data that a 2x2 does not hold.
    """
    if measure not in COUNT_POOLABLE:
        return None
    f = _log_or if measure == "OR" else _log_rr
    ys, vs = zip(*(f(*r) for r in rows))
    w = [1 / v for v in vs]
    fe = sum(wi * yi for wi, yi in zip(w, ys)) / sum(w)
    Q = sum(wi * (yi - fe) ** 2 for wi, yi in zip(w, ys))
    df = len(ys) - 1
    if estimator.lower().startswith(("dersimonian", "dl")):
        C = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
        tau2 = max(0.0, (Q - df) / C) if C > 0 else 0.0
    elif estimator.lower() in ("fixed", "none", "iv", "inverse variance"):
        tau2 = 0.0
    else:
        tau2 = None                       # estimator we do not implement
    if tau2 is None:
        return None
    wr = [1 / (v + tau2) for v in vs]
    mu = sum(wi * yi for wi, yi in zip(wr, ys)) / sum(wr)
    se = math.sqrt(1 / sum(wr))
    z = Z.get(level)
    if z is None:
        return None
    i2 = max(0.0, 100 * (Q - df) / Q) if Q > 0 else 0.0
    return dict(point=math.exp(mu), ci_low=math.exp(mu - z * se),
                ci_high=math.exp(mu + z * se), tau2=tau2, i2=i2, q=Q, df=df)


def _norm_numbers(text: str) -> str:
    """Strip separators INSIDE numerals. PubMed XML writes 14964 as 14 964 with
    a thin space, so a naive search reports a present value as missing."""
    import html as _html
    t = _html.unescape(text)
    return re.sub(r"(?<=\d)[\s\u2007\u2008\u2009\u00a0\u202f,](?=\d)", "", t)


def check_against_sources(canon, rep, sources_root=None):
    """Verify MEASURED cells against the staged source payloads.

    Until now the validator could only establish that an object agreed with
    ITSELF. An adversary made the consequence concrete: change a measured effect
    and recompute the pooled result consistently, and everything passed while
    the staged registry file said something else. With payloads on disk that is
    checkable, so it is now checked.

    If the payloads are absent the object does NOT pass. A source-backed claim
    that cannot be checked is not a claim that has been verified.
    """
    root = pathlib.Path(sources_root or "sources") / canon["app_id"]
    if not root.is_dir():
        rep.block("sources-unavailable",
                  f"no source payloads at {root}. The object asserts MEASURED values; "
                  f"without the sources those assertions cannot be verified, and an "
                  f"unverifiable claim is not a passing one.")
        return
    blobs = {}
    for f in root.glob("*"):
        if f.suffix in (".json", ".xml"):
            blobs[f.name] = _norm_numbers(f.read_text(encoding="utf-8", errors="replace"))
    if not blobs:
        rep.block("sources-unavailable", f"{root} contains no source payloads")
        return

    def find(value, prefer):
        want = str(value)
        for name, blob in blobs.items():
            if prefer and prefer not in name:
                continue
            if want in blob:
                return name
        for name, blob in blobs.items():
            if want in blob:
                return name
        return None

    for t in canon["inputs"]["trials"]:
        nct = t.get("nct", "")
        for oid, d in t.get("by_outcome", {}).items():
            prov = d.get("provenance") or {}
            title = prov.get("source_outcome_title")
            eff = d.get("effect")
            if eff and prov.get("source_id", "").startswith("REGISTRY"):
                # CELL IDENTITY, not token presence. Navigate to the exact posted
                # outcome measure the object names and compare there. Without
                # this, one trial's on-treatment effect passes in place of its
                # intention-to-treat effect: same file, different definition.
                if not title:
                    rep.block("source-cell-unbound",
                              f"{t['id']}/{oid} is registry-sourced but names no "
                              f"source_outcome_title, so its value can only be checked for "
                              f"presence somewhere in the file rather than in the analysis "
                              f"it claims to come from.")
                else:
                    f = root / f"{nct}.ctgov.json"
                    try:
                        raw = json.loads(f.read_text(encoding="utf-8"))
                        oms = raw["resultsSection"]["outcomeMeasuresModule"]["outcomeMeasures"]
                    except Exception as exc:
                        oms = []
                        rep.block("source-cell-unbound",
                                  f"{t['id']}/{oid}: cannot read posted outcomes from {f.name}: {exc}")
                    m = next((o for o in oms if (o.get("title") or "") == title), None)
                    if m is None:
                        rep.block("source-cell-unbound",
                                  f"{t['id']}/{oid} names source_outcome_title "
                                  f"{title[:60]!r}, which is not a posted outcome measure "
                                  f"in {nct}.")
                    else:
                        an = (m.get("analyses") or [{}])[0]
                        pairs = [("point", an.get("paramValue")),
                                 ("ci_low", an.get("ciLowerLimit")),
                                 ("ci_high", an.get("ciUpperLimit"))]
                        for key, sval in pairs:
                            if sval is None:
                                continue
                            if abs(float(sval) - float(eff[key])) > 1e-9:
                                rep.block("source-cell-mismatch",
                                          f"{t['id']}/{oid}: {key}={eff[key]} but the named "
                                          f"analysis in {nct} gives {sval}. The value must "
                                          f"come from the analysis the object cites, not "
                                          f"merely appear somewhere in the file.")
                        dn = {x["groupId"]: x["value"] for g in m.get("denoms", [])
                              for x in g.get("counts", [])}
                        gt = {g["id"]: (g.get("title") or "").lower()
                              for g in m.get("groups", [])}
                        got = {}
                        for gid, lab in gt.items():
                            role = "control" if any(w in lab for w in
                                                    ("placebo", "control", "alum")) else "treatment"
                            if gid in dn:
                                got[role] = int(dn[gid])
                        for role, n in (d.get("analysed") or {}).items():
                            if role in got and int(n) != got[role]:
                                rep.block("source-cell-mismatch",
                                          f"{t['id']}/{oid}: analysed.{role}={n} but the "
                                          f"named analysis in {nct} reports {got[role]}")
            cells = {}
            if eff:
                cells.update({f"effect.{k}": eff[k]
                              for k in ("point", "ci_low", "ci_high") if k in eff})
                cells.update({f"analysed.{k}": v
                              for k, v in (d.get("analysed") or {}).items()})
            else:
                for role in ("treatment", "control"):
                    arm = d.get(role)
                    if arm:
                        cells[f"{role}.events"] = arm["events"]
                        cells[f"{role}.n"] = arm["n"]
            if t.get("enrolled") is not None:
                cells["enrolled"] = t["enrolled"]
            for label, value in cells.items():
                if find(value, nct) is None and find(value, None) is None:
                    rep.block("source-unsupported",
                              f"{t['id']}/{oid}: {label}={value} does not appear in any "
                              f"staged source payload for this app. Either the value is "
                              f"wrong or its source is not staged; both are blocking.")


# --------------------------------------------------------------- detectors
def check_k_derived(canon, rep):
    """A declared k must equal the number of trials contributing to that outcome.

    (The field is still written in the object; this verifies it against the data
    rather than trusting it. An earlier docstring said k was "never declared",
    which overstated what the check does.)"""
    for oid, res in canon["results"]["by_outcome"].items():
        # Contributing means carrying DATA, not merely having the key. An
        # adversary emptied a trial's effect and analysed blocks; k stayed 6
        # while the pooled figure was recomputed from 5.
        contributing = [t for t in canon["inputs"]["trials"]
                        if (t.get("by_outcome", {}).get(oid) or {}).get("effect")
                        or ((t.get("by_outcome", {}).get(oid) or {}).get("treatment")
                            and (t.get("by_outcome", {}).get(oid) or {}).get("control"))]
        if res["k"] != len(contributing):
            rep.block("k-vs-contributing",
                      f"outcome {oid!r} records k={res['k']} but {len(contributing)} "
                      f"trial(s) contribute data for it; k is derived, not declared")


def check_pooled_recompute(canon, rep):
    """THE k>1 DETECTOR.

    Recompute the pooled estimate from the per-trial 2x2s and compare with the
    recorded one. This is the first check in the whole design capable of catching
    a pooled number that is simply wrong, as opposed to a label that disagrees
    with another label.
    """
    for oid, res in canon["results"]["by_outcome"].items():
        rec = res.get("pooled")
        if not rec:
            continue
        outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
        if rec.get("measure") and rec["measure"] != outcome["measure"]:
            rep.block("pooled-measure-mismatch",
                      f"outcome {oid!r} declares measure {outcome['measure']!r} but its "
                      f"pooled block is labelled {rec['measure']!r}. The arithmetic uses "
                      f"the outcome's measure, so the label alone changes what a reader "
                      f"thinks the number is.")
        rows, effects = [], []
        for t in canon["inputs"]["trials"]:
            d = t.get("by_outcome", {}).get(oid)
            if not d:
                continue
            if d.get("effect"):
                effects.append(d["effect"])
                continue
            tx, ct = d.get("treatment"), d.get("control")
            if tx and ct:
                rows.append((tx["events"], tx["n"], ct["events"], ct["n"]))
        if rows and effects:
            rep.block("mixed-input-forms",
                      f"outcome {oid!r} mixes per-trial 2x2 counts with per-trial effect "
                      f"estimates. Pooling both together silently combines two different "
                      f"variance derivations; the object must say which one applies.")
            continue
        if len(rows) + len(effects) < 2:
            continue
        if effects:
            got = pool_generic(effects, res.get("estimator_used", "DL"),
                               rec.get("ci_level", 95),
                               log_scale=outcome["measure"] not in ("MD", "SMD"))
        else:
            got = pool(rows, outcome["measure"], res.get("estimator_used", "DL"),
                       rec.get("ci_level", 95))
        if got is None:
            rep.block("pooled-recompute",
                      f"outcome {oid!r}: cannot verify the pooled estimate. Either the "
                      f"estimator {res.get('estimator_used')!r} is not one this validator "
                      f"implements, or the measure {outcome['measure']!r} cannot be "
                      f"computed from the inputs given (a 2x2 supports RR and OR only; a "
                      f"hazard ratio needs time-to-event data). An unverifiable pooled "
                      f"number is not a passing one.")
            continue
        for field in ("point", "ci_low", "ci_high"):
            want, have = got[field], rec[field]
            # Tolerance = half of the last decimal place the value is STATED to,
            # with a small allowance for estimator implementation differences.
            # Percentage tolerances were the hole: 5% of 60.61 is 3.0, so a
            # confidence bound could be moved three whole points and still pass.
            dec = len(str(have).split(".")[1]) if "." in str(have) else 0
            # Half of the last stated decimal place, and nothing else. A value
            # written to two decimals must round-trip to two decimals. A
            # percentage floor reintroduced exactly the hole this comment warns
            # about: 0.2 per cent of 54.66 is 0.109.
            tol = max(0.5 * 10 ** (-dec), 1e-9)
            # Writing a value coarsely must not widen its own tolerance: an
            # integer gave dec=0 and therefore tol=0.5, which admitted 0 in
            # place of 0.221. If the stated precision cannot resolve the value
            # to within a tenth of itself, the value is under-stated, not
            # merely rounded.
            if dec < 2:
                rep.block("pooled-precision",
                          f"outcome {oid!r}: {field}={have} is written to {dec} decimal "
                          f"place(s). A pooled estimate must be stated to at least two, "
                          f"because the tolerance is derived from the precision and a "
                          f"coarse value therefore buys itself a loose check: -55 would "
                          f"pass against -54.653.")
                continue
            if abs(want) > 1e-9 and tol > 0.1 * abs(want):
                rep.block("pooled-precision",
                          f"outcome {oid!r}: {field}={have} is stated to {dec} decimal "
                          f"place(s), which makes its own tolerance {tol:.4g} -- more than "
                          f"a tenth of the recomputed {want:.4g}. State it precisely enough "
                          f"to be checkable.")
                continue
            if abs(have - want) > tol:
                rep.block("pooled-recompute",
                          f"outcome {oid!r}: recorded {field}={have} but pooling the "
                          f"{len(rows)} per-trial 2x2s with "
                          f"{res.get('estimator_used')} gives {want:.4f} "
                          f"(off by {abs(have-want):.4f}, tolerance {tol:.4f})")
        het = res.get("heterogeneity") or {}
        if "df" in het and het["df"] != got["df"]:
            rep.block("heterogeneity-recompute",
                      f"outcome {oid!r}: recorded df={het['df']} but {got['df']} degrees of "
                      f"freedom follow from {got['df'] + 1} contributing trials")
        for field in ("tau2", "i2", "q"):
            if field in het and het[field] is not None:
                want = got[{"tau2": "tau2", "i2": "i2", "q": "q"}[field]]
                have_h = het[field]
                dec_h = len(str(have_h).split(".")[1]) if "." in str(have_h) else 0
                if abs(have_h - want) > max(0.5 * 10 ** (-dec_h), 1e-9):
                    rep.block("heterogeneity-recompute",
                              f"outcome {oid!r}: recorded {field}={het[field]} but "
                              f"recomputation gives {want:.4f}")


def check_superseded(canon, rep):
    """A superseded figure that is rendered must be recomputable.

    The object keeps an earlier pooled result as an audit trail and renders it in
    prose. Nothing checked it, so it could carry any number at all. It must name
    the trials it was computed from, and it must reproduce from them.
    """
    for oid, res in canon["results"]["by_outcome"].items():
        sup = res.get("superseded")
        if not sup:
            continue
        ids = sup.get("trial_ids")
        if not ids:
            rep.block("superseded-unverifiable",
                      f"outcome {oid!r} keeps a superseded figure but does not name the "
                      f"trials it came from, so it cannot be recomputed and could hold any "
                      f"value while being rendered to a reader.")
            continue
        outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
        effects = [t["by_outcome"][oid]["effect"]
                   for t in canon["inputs"]["trials"]
                   if t["id"] in ids and t.get("by_outcome", {}).get(oid, {}).get("effect")]
        if len(effects) != len(ids):
            rep.block("superseded-unverifiable",
                      f"outcome {oid!r}: superseded names {len(ids)} trials but "
                      f"{len(effects)} of them carry an effect in this object")
            continue
        got = pool_generic(effects, res.get("estimator_used", "DL"), 95,
                           log_scale=outcome["measure"] not in ("MD", "SMD"))
        if got is None:
            return
        for f in ("point", "ci_low", "ci_high"):
            if f in sup:
                dec = len(str(sup[f]).split(".")[1]) if "." in str(sup[f]) else 0
                # Same precision floor as the live pooled estimate. It was added
                # there and forgotten here, so a superseded figure could be
                # written coarsely and buy itself a 0.5 tolerance.
                if dec < 2:
                    rep.block("superseded-precision",
                              f"outcome {oid!r}: superseded {f}={sup[f]} is written to "
                              f"{dec} decimal place(s). A rendered figure must be stated "
                              f"precisely enough to be checkable.")
                    continue
                if abs(sup[f] - got[f]) > max(0.5 * 10 ** (-dec), 1e-9):
                    rep.block("superseded-recompute",
                              f"outcome {oid!r}: superseded {f}={sup[f]} but pooling the "
                              f"{len(effects)} named trials gives {got[f]:.4f}")


def check_outcome_coverage(canon, rep):
    """Declared outcomes and result blocks must correspond exactly."""
    declared = {o["id"] for o in canon["outcomes"]}
    resulted = set(canon["results"]["by_outcome"])
    for x in declared - resulted:
        rep.block("outcome-no-result", f"outcome {x!r} is declared but has no result")
    for x in resulted - declared:
        rep.block("result-no-outcome", f"result block {x!r} names an undeclared outcome")
    for t in canon["inputs"]["trials"]:
        for x in set(t.get("by_outcome", {})) - declared:
            rep.block("trial-undeclared-outcome",
                      f"{t['id']} carries data for undeclared outcome {x!r}")


def check_heterogeneity_and_k(canon, rep):
    for oid, res in canon["results"]["by_outcome"].items():
        if res["k"] < 2 and res.get("heterogeneity"):
            rep.block("heterogeneity-at-k1",
                      f"outcome {oid!r} reports heterogeneity with k={res['k']}")
        if res["k"] < 2 and res.get("pooled"):
            rep.block("pooled-at-k1", f"outcome {oid!r} reports a pooled estimate at k={res['k']}")
        if bool(res.get("poolable")) != (res["k"] >= 2):
            rep.block("poolable-vs-k",
                      f"outcome {oid!r}: poolable={res.get('poolable')} but k={res['k']}")


def check_removal_disclosure(canon, rep):
    """A build-to-core app must SHOW what it removed.

    An app rebuilt on a fraction of its cited evidence, without saying so, is a
    worse defect than the contamination it replaced: the reader sees a clean
    small analysis and cannot know it was once a large dirty one.
    """
    # An object could previously escape this check entirely by simply omitting
    # build_mode: the detector returned early and the reduction went undisclosed.
    # The declaration is therefore mandatory, and "full" must be earned.
    mode = canon.get("build_mode")
    if mode not in ("full", "build-to-core"):
        rep.block("build-mode-undeclared",
                  f"build_mode is {mode!r}; every object must declare whether it is a "
                  f"full build or built to a sourceable core. Omitting it was a way to "
                  f"skip the disclosure requirement.")
        return
    if mode == "full":
        if canon.get("removed_citations") or canon.get("quarantine"):
            rep.block("full-build-with-removals",
                      "build_mode is 'full' but the object records removals or a "
                      "quarantine; a full build removed nothing by definition")
        # "full" must be EARNED, not merely asserted by deleting the evidence of
        # a reduction. A full build carries every trial it cites, so it must say
        # how many it cited and that number must equal the trials it holds.
        cited = canon.get("cited_total")
        held = len(canon["inputs"]["trials"])
        if cited is None:
            rep.block("full-build-unsubstantiated",
                      f"build_mode is 'full' but the object does not record how many "
                      f"trials were cited, so the claim cannot be checked. Deleting a "
                      f"removals block is not the same as having removed nothing.")
        elif cited != held:
            rep.block("full-build-unsubstantiated",
                      f"build_mode is 'full' but the object cites {cited} trials and "
                      f"holds {held}; the difference was removed and must be disclosed")
        return
    rm = canon.get("removed_citations")
    if not rm:
        rep.block("removal-not-disclosed",
                  "build_mode is build-to-core but the object records no removed_citations")
        return
    cats = rm.get("categories") or []
    if not cats:
        rep.block("removal-not-disclosed", "removed_citations records no reasons")
    counted = sum(c.get("count", 0) for c in cats
                  if "contributes no data" not in c.get("reason", ""))
    if counted != rm.get("removed"):
        rep.block("removal-arithmetic",
                  f"removed={rm.get('removed')} but the itemised reasons account for "
                  f"{counted}; every removal must have a stated reason")
    if rm.get("retained", 0) + rm.get("removed", 0) != rm.get("total_cited"):
        rep.block("removal-arithmetic",
                  f"retained + removed does not equal total_cited "
                  f"({rm.get('retained')} + {rm.get('removed')} != {rm.get('total_cited')})")
    for c in cats:
        if not c.get("detail"):
            rep.block("removal-not-disclosed",
                      f"removal category {c.get('reason')!r} states no detail")


def check_source_ids(canon, rep):
    """Every source_id must resolve in the sources registry.

    The object claims each number names the source layer it came from. Nothing
    checked that the named source EXISTS, so a provenance block could cite
    anything at all and the claim would still read as satisfied.
    """
    known = set(canon.get("sources", {}))

    def walk(node, path):
        if isinstance(node, dict):
            for k, val in node.items():
                if k.endswith("source_id") and isinstance(val, str):
                    if val not in known:
                        rep.block("dangling-source-id",
                                  f"{path}.{k} cites {val!r}, which is not in the sources "
                                  f"registry ({sorted(known)})")
                elif isinstance(val, (dict, list)):
                    walk(val, f"{path}.{k}")
        elif isinstance(node, list):
            for i, val in enumerate(node):
                walk(val, f"{path}[{i}]")

    walk(canon, "canonical")


def check_arm_roles(canon, rep):
    for t in canon["inputs"]["trials"]:
        roles = sorted(a.get("role") for a in t["arms"])
        if roles != ["control", "treatment"]:
            rep.block("arm-roles", f"{t['id']} declares roles {roles!r}")


CONTROL_WORDS = ("placebo", "control", "sham", "usual care", "standard care", "alum")


def check_role_label_agreement(canon, rep):
    """An arm's declared role must not contradict its own label.

    check_arm_roles only verified that the SET of roles was one treatment and
    one control. Swapping the role values between the two arms leaves that set
    unchanged, so a control could be declared the treatment and the displayed
    direction would invert with every role-based check still passing.
    """
    for t in canon["inputs"]["trials"]:
        for a in t["arms"]:
            lab = str(a.get("label", "")).strip().lower()
            looks_control = any(w in lab for w in CONTROL_WORDS)
            if a.get("role") == "treatment" and looks_control:
                rep.block("role-label-contradiction",
                          f"{t['id']}: an arm declares role=treatment but is labelled "
                          f"{a['label']!r}")
            if a.get("role") == "control" and not looks_control:
                rep.block("role-label-contradiction",
                          f"{t['id']}: an arm declares role=control but is labelled "
                          f"{a['label']!r}, which names no comparator")


def check_prose_numerals(canon, rep):
    """Prose may not restate a number the object already holds structurally.

    Two corrections, both earned from adversaries. The first version exempted
    note/detail/reason/source/access_note -- every field that actually carries
    prose -- which made the rule a facade. Un-exempting them fired on NCT and
    COV identifiers, on "week 24", and on values deliberately QUOTED from the
    erroneous source app being documented. Those are legitimately literal: an
    identifier is a name, and a quoted wrong value cannot reference our data
    because it is not our data.

    So the rule is narrowed to what single-source-of-truth is actually about: a
    prose COPY of a value the object holds elsewhere, which can go stale against
    the field it describes. A field may opt out by beginning with "QUOTED:",
    which declares that it reproduces foreign data verbatim.

    Scope: no v2 generator exists yet, so these objects have no rendered surface.
    This checks the object against itself, not a page.
    """
    IDENT = re.compile(r"NCT\d{8}|COV\d{3}|PMID\s*\d+|phase\s*\d(?:/\d)?"
                       r"|week\s*\d+|9[059]\s*per cent|9[059]\s*%", re.I)
    # The sign is part of the number. Without it a structured -54.66 was never
    # matched by a prose "54.66", so a stale negative value could be restated in
    # prose untouched.
    NUM = re.compile(r"-?\d+(?:\.\d+)?")
    # Number WORDS escaped a digit-only regex: "Six trials report this outcome"
    # is a copy of k in exactly the way a digit would be.
    WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
             "twelve": 12}
    PROSE_KEYS = ("note", "detail", "reason", "source", "access_note",
                  "caveat", "disclosure_note")

    structured: set[str] = set()

    def collect(node):
        if isinstance(node, dict):
            for val in node.values():
                if isinstance(val, bool):
                    continue
                if isinstance(val, (int, float)):
                    structured.add(str(val))
                    if isinstance(val, float) and val == int(val):
                        structured.add(str(int(val)))
                else:
                    collect(val)
        elif isinstance(node, list):
            for val in node:
                collect(val)

    collect(canon)

    def walk(node, path):
        if isinstance(node, dict):
            for k, val in node.items():
                if isinstance(val, str):
                    if not any(k == pk or k.endswith("_" + pk) for pk in PROSE_KEYS):
                        continue
                    if val.strip().startswith("QUOTED:"):
                        continue
                    # Mask {references} FIRST: a reference PATH contains digits
                    # (t1, i2, arms[0]) that are not values. v1 learned this too.
                    masked = re.sub(r"\{[^}]*\}", " ", val)
                    masked = IDENT.sub(" ", masked)
                    # Only a spelled COUNT of something this object counts.
                    # "one of them" and "two layers" are ordinary English, not
                    # stale copies of a structured value.
                    countable = (r"\s+(?:trials?|studies|citations?|registrations?"
                                 r"|arms?|outcomes?|participants?)\b")
                    for w, n in WORDS.items():
                        if re.search(r"\b" + w + countable, masked, re.I) \
                                and str(n) in structured:
                            rep.block("prose-copies-number",
                                      f"{path}.{k} spells out {w!r}, which this object "
                                      f"holds as the structured value {n}. A spelled "
                                      f"number goes stale exactly as a digit does.")
                    for m in NUM.finditer(masked):
                        tok = m.group(0)
                        if tok in structured or tok.lstrip("-") in structured                                 or ("-" + tok) in structured:
                            rep.block("prose-copies-number",
                                      f"{path}.{k} restates {tok!r}, which this "
                                      f"object already holds as a structured value. A "
                                      f"prose copy goes stale when the field changes "
                                      f"-- in: "
                                      f"{masked[max(0, m.start()-45):m.end()+25].strip()!r}")
                else:
                    walk(val, f"{path}.{k}")
        elif isinstance(node, list):
            for i, val in enumerate(node):
                walk(val, f"{path}[{i}]")

    walk(canon, "canonical")


def check_direction_anchor(canon, rep):
    """The pooled sign must agree with the direction the outcome declares.

    Negating every per-trial estimate AND the pooled estimate leaves the
    arithmetic perfectly consistent, so the recompute check passes while the
    object says the drug raises what it lowers. This catches that flip ONLY when
    `favours` is left alone.

    STATED HONESTLY, because an earlier docstring here claimed more than the
    code does: flipping every sign AND `favours` together is self-consistent and
    passes. This is not an external anchor, it anchors two mutable fields to
    each other. Nothing inside the object can establish which direction is true;
    that is what sourcing and the cross-family gate are for.
    """
    for oid, res in canon["results"]["by_outcome"].items():
        rec = res.get("pooled")
        if not rec:
            continue
        outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
        want = outcome.get("direction_of_benefit")
        favours = res.get("favours")
        if want is None or favours is None:
            rep.block("direction-unanchored",
                      f"outcome {oid!r} declares no direction_of_benefit, or its result "
                      f"declares no favours. Without both, a coordinated sign flip is "
                      f"undetectable.")
            continue
        null = outcome.get("null_value", 0 if outcome["measure"] in ("MD", "SMD") else 1)
        if rec["ci_high"] < null:
            implied = "treatment" if want == "lower" else "control"
        elif rec["ci_low"] > null:
            implied = "control" if want == "lower" else "treatment"
        else:
            implied = None
        if implied is None and favours != "neither":
            rep.block("direction-anchor",
                      f"outcome {oid!r}: the interval spans the null but favours is "
                      f"{favours!r}")
        elif implied is not None and favours != implied:
            rep.block("direction-anchor",
                      f"outcome {oid!r}: the pooled interval ({rec['ci_low']}, "
                      f"{rec['ci_high']}) about a null of {null} with "
                      f"direction_of_benefit={want!r} favours {implied!r}, but the object "
                      f"records favours={favours!r}")


def check_counts_sane(canon, rep):
    """Sanity of the per-trial inputs, whichever form they take.

    Three scoping corrections, each earned by an adversary:
      * it once looked only for 2x2 blocks, so against effect-based trials it
        found nothing and reported a pass;
      * the enrolment checks then lived inside the effect branch, so count-based
        trials never reached them, and writing enrolled=0 disabled the very
        comparison it was meant to enable because zero is falsy;
      * plausibility was tested on the TOTAL analysed, which stays reasonable
        when only one arm is shrunk to 1.
    """
    for t in canon["inputs"]["trials"]:
        enrolled = t.get("enrolled")
        if enrolled is None:
            rep.block("enrolled-missing",
                      f"{t['id']} does not record how many participants were enrolled, so "
                      f"the analysed-exceeds-enrolled check cannot fire. An optional field "
                      f"that disables its own detector is not a check.")
        elif enrolled <= 0:
            rep.block("enrolled-invalid",
                      f"{t['id']} records enrolled={enrolled}. A non-positive enrolment is "
                      f"impossible, and zero silently disabled the comparison it exists to "
                      f"enable.")

        for oid, d in t.get("by_outcome", {}).items():
            eff = d.get("effect")
            if eff:
                if not (eff["ci_low"] < eff["point"] < eff["ci_high"]):
                    rep.block("arithmetic",
                              f"{t['id']}/{oid}: interval is not ordered around the point "
                              f"({eff['ci_low']}, {eff['point']}, {eff['ci_high']})")
                if eff.get("ci_level") not in Z:
                    rep.block("arithmetic",
                              f"{t['id']}/{oid}: ci_level {eff.get('ci_level')!r} is not "
                              f"one this validator can convert to a standard error")
                sizes = {k: v for k, v in (d.get("analysed") or {}).items()
                         if isinstance(v, (int, float))}
                if not sizes:
                    rep.block("denominators-missing",
                              f"{t['id']}/{oid} carries an effect estimate with no analysed "
                              f"denominators. A reader cannot weigh a trial whose size is "
                              f"not stated.")
            else:
                tx, ct = d.get("treatment"), d.get("control")
                if not (tx and ct):
                    continue
                for role, arm in (("treatment", tx), ("control", ct)):
                    if arm["events"] > arm["n"]:
                        rep.block("arithmetic",
                                  f"{t['id']}/{oid}/{role}: {arm['events']} events exceeds "
                                  f"{arm['n']} participants")
                    if arm["events"] < 0 or arm["n"] <= 0:
                        rep.block("arithmetic",
                                  f"{t['id']}/{oid}/{role}: non-positive counts")
                sizes = {"treatment": tx["n"], "control": ct["n"]}

            if not sizes:
                continue
            if enrolled and sum(sizes.values()) > enrolled:
                rep.block("analysed-exceeds-enrolled",
                          f"{t['id']}/{oid}: {sum(sizes.values())} analysed exceeds "
                          f"{enrolled} enrolled. The counts belong to something other than "
                          f"this registration.")
            biggest = max(sizes.values())
            for role, n in sizes.items():
                if n <= 0:
                    rep.block("arithmetic",
                              f"{t['id']}/{oid}/{role}: non-positive analysed n")
                elif biggest and n < 0.05 * biggest:
                    rep.block("analysed-implausible",
                              f"{t['id']}/{oid}/{role}: {n} analysed against {biggest} in "
                              f"the other arm, under five per cent of it. Testing only the "
                              f"TOTAL missed this, because one intact arm keeps the total "
                              f"plausible.")


DETECTORS = [
    ("outcome-coverage", check_outcome_coverage),
    ("superseded", check_superseded),
    ("removal-disclosure", check_removal_disclosure),
    ("source-ids", check_source_ids),
    ("against-sources", check_against_sources),
    ("arm-roles", check_arm_roles),
    ("role-label-agreement", check_role_label_agreement),
    ("prose-numerals", check_prose_numerals),
    ("direction-anchor", check_direction_anchor),
    ("counts-sane", check_counts_sane),
    ("k-derived", check_k_derived),
    ("heterogeneity-and-k", check_heterogeneity_and_k),
    ("pooled-recompute", check_pooled_recompute),
]


def validate(path: Path, verbose=True) -> Report:
    canon = json.loads(path.read_text(encoding="utf-8"))
    rep = Report()
    for name, fn in DETECTORS:
        before = len(rep.blocks)
        fn(canon, rep)
        fired = len(rep.blocks) - before
        if verbose:
            print(f"  [{'BLOCK' if fired else ' ok  '}] {name}"
                  + (f"  ({fired})" if fired else ""))
        if not fired:
            rep.passes.append(name)
    return rep


def main():
    p = Path(sys.argv[1])
    print(f"VALIDATING (schema v2) {p.name}\n")
    rep = validate(p)
    print()
    if rep.blocks:
        print(f"BUILD BLOCKED -- {len(rep.blocks)} finding(s):")
        for r, m in rep.blocks:
            print(f"  [{r}] {m}")
        return 1
    print(f"VALIDATOR CLEAN -- {len(rep.passes)}/{len(DETECTORS)} detectors passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
