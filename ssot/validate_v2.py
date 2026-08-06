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
    """log RR and its variance, with a 0.5 correction ONLY when an arm has zero EVENTS.

    The trigger used to be any zero cell, including a non-event cell -- that is,
    an arm where every participant had the event. That is the ODDS-RATIO rule
    applied to a risk ratio. log RR is perfectly well defined at 100 per cent
    incidence: only a zero NUMERATOR breaks it. Correcting a saturated arm
    shifts the estimate for no reason.

    This is not a change made to suit a build. It moves a published number in
    this corpus -- two paediatric arms report 100 per cent incidence -- and the
    direction of the change is toward the uncorrected value, which is the
    correct one for this measure. The odds-ratio path below keeps the broader
    trigger, because a zero non-event cell genuinely breaks an odds ratio.
    """
    if 0 in (tE, cE):
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


def _quote_norm(s):
    """Normalise for quote comparison. Order is the whole difficulty here.

    Three orderings were wrong before this one, each making a quote copied
    straight out of its source read as absent:

      * entities BLANKED rather than unescaped -- this source writes decimals
        with a middle dot, giving "48 2" on one side and "48·2" on the other.
      * entities unescaped BEFORE tags are stripped -- "&lt;" becomes a real
        "<" and the tag pattern then eats the rest of the sentence, so
        "(P &lt; .001 for both)." lost everything after "(P ".
      * whitespace collapsed BEFORE unescaping -- a thin space written as an
        entity survives as U+2008 on one side and as an ordinary space on the
        other, so "5 microgram/dose" matched nothing.

    Correct order: strip tags, unescape, collapse whitespace, then join
    numerals. Anything that compares a quote to a source must use THIS.
    """
    import html as _h
    s = re.sub(r"<[^>]+>", " ", str(s))
    s = _h.unescape(s)
    s = re.sub(r"\s+", " ", s)
    return re.sub(r"(?<=\d)[\s     ,](?=\d)", "", s).strip()


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
    blobs, raw_blobs = {}, {}
    for f in root.glob("*"):
        if f.suffix in (".json", ".xml"):
            raw = f.read_text(encoding="utf-8", errors="replace")
            # Token lookups want numerals joined, which requires unescaping.
            # Quote comparison must NOT see unescaped text before tags are
            # stripped, or a "&lt;" becomes a real "<" and the tag pattern eats
            # the rest of the sentence. So the raw text is kept alongside.
            raw_blobs[f.name] = raw
            blobs[f.name] = _norm_numbers(raw)
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
            # A DERIVED cell is not required to appear literally in the source -
            # it was computed, not read. What must hold is that its INPUTS are
            # sourced and that the derivation reproduces the stored value. Left
            # unhandled, the source check demanded literal presence and blocked
            # every legitimately derived count.
            prov_tag = (prov.get("tag") or "").upper()
            if prov_tag == "DERIVED":
                for role in ("treatment", "control"):
                    arm = d.get(role) or {}
                    pct, n, ev = arm.get("percentage"), arm.get("n"), arm.get("events")
                    if pct is None or n is None or ev is None:
                        continue
                    if find(pct, nct) is None:
                        rep.block("source-unsupported",
                                  f"{t['id']}/{oid}/{role}: percentage={pct} does not "
                                  f"appear in a staged source payload for {nct}")
                    if find(n, nct) is None:
                        rep.block("source-unsupported",
                                  f"{t['id']}/{oid}/{role}: denominator={n} does not "
                                  f"appear in a staged source payload for {nct}")
                    want = round(pct / 100 * n)
                    if abs(ev - want) > 0:
                        rep.block("derivation-mismatch",
                                  f"{t['id']}/{oid}/{role}: events={ev} but the recorded "
                                  f"derivation, {pct} per cent of {n}, gives {want}")
                continue
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
                # Scoped to THIS trial's own payloads. A global fallback let a
                # value belonging to another trial count as sourced for this one,
                # so a duplicated trial under an invented registration could
                # borrow the original's numbers.
                if find(value, nct) is None:
                    elsewhere = find(value, None)
                    where = (f" It appears in {elsewhere}, which belongs to a different "
                             f"trial and does not source this one." if elsewhere else "")
                    rep.block("source-unsupported",
                              f"{t['id']}/{oid}: {label}={value} does not appear in a "
                              f"staged source payload for {nct}.{where}")
            # Presence is not identity. A reviewer changed a MEASURED event
            # count from 16 to 21 and it passed, because 21 occurs in the same
            # abstract in "From 21 days after the first dose" -- a different
            # number entirely. Confirmed by executing it.
            #
            # A registry cell is identified by naming its outcome and category.
            # An unstructured publication has no such structure, so the object
            # names the SENTENCE instead. Each quote must appear verbatim in a
            # staged source, and every count and denominator must fall inside
            # one of them. Proximity was tried first and is the wrong mechanism:
            # one of these trials states its denominators in the interventions
            # section and its counts in the results section, legitimately far
            # apart, so a window tight enough to bind the others rejected it.
            has_counts = any((d.get(r_) or {}).get("events") is not None
                             for r_ in ("treatment", "control"))
            if has_counts and not d.get("effect"):
                quotes = prov.get("source_quotes") or []
                if not quotes:
                    rep.block("source-cell-unbound",
                              f"{t['id']}/{oid} reports MEASURED counts from an "
                              f"unstructured source but names no source_quotes, so each "
                              f"number can only be checked for appearing SOMEWHERE in "
                              f"the file.")
                else:
                    joined = ""
                    for q in quotes:
                        qn = _quote_norm(q)
                        if any(qn in _quote_norm(b) for b in raw_blobs.values()):
                            joined += " " + qn
                        else:
                            rep.block("source-quote-absent",
                                      f"{t['id']}/{oid}: the quoted source sentence "
                                      f"{str(q)[:70]!r} does not appear in any staged "
                                      f"payload for {nct}.")
                    # Per-ARM fragments, not just the sentence. Quoting the
                    # sentence was not enough: the Sputnik results sentence
                    # opens "From 21 days after the first dose", so setting the
                    # treatment count to 21 still found "21" inside the quote.
                    # A fragment names the phrase that carries THIS arm's count.
                    #
                    # A number followed by a unit is a duration or a percentage,
                    # not a count of participants, so it cannot satisfy an
                    # events cell.
                    UNIT = r"(?!\s*(?:days?|weeks?|months?|years?|%))"
                    for role in ("treatment", "control"):
                        arm = d.get(role) or {}
                        if arm.get("events") is None:
                            continue
                        frags = arm.get("source_fragments") or []
                        if not frags:
                            rep.block("source-cell-unbound",
                                      f"{t['id']}/{oid}/{role} states a count but names no "
                                      f"source_fragments, so the number can only be found "
                                      f"somewhere in a sentence rather than in the phrase "
                                      f"that reports THIS arm.")
                            continue
                        fjoin = ""
                        for fr in frags:
                            fn = _quote_norm(fr)
                            if fn and fn in joined:
                                fjoin += " " + fn
                            else:
                                rep.block("source-fragment-absent",
                                          f"{t['id']}/{oid}/{role}: the fragment "
                                          f"{str(fr)[:60]!r} is not inside any sentence "
                                          f"this object quotes from {nct}.")
                        ev, n = arm.get("events"), arm.get("n")
                        if not re.search(r"(?<![0-9])" + str(ev) + r"(?![0-9])" + UNIT, fjoin):
                            rep.block("source-cell-unbound",
                                      f"{t['id']}/{oid}/{role}.events={ev} is not reported "
                                      f"as a count in the fragment(s) this object names. A "
                                      f"number that appears only as a duration or a "
                                      f"percentage is not this arm's event count.")
                        if n is not None and not re.search(
                                r"(?<![0-9])" + str(n) + r"(?![0-9])", fjoin):
                            rep.block("source-cell-unbound",
                                      f"{t['id']}/{oid}/{role}.n={n} does not appear in the "
                                      f"fragment(s) this object names.")


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


def check_estimator_labels(canon, rep):
    """The estimator actually used must agree with the labels a reader sees.

    check_pooled_recompute pools with `estimator_used`, but nothing compared that
    with the visible `estimator` and `model`. An adversary set estimator_used to
    "fixed", supplied matching fixed-effect numbers, left model="random" and
    estimator="DerSimonian-Laird" in place, and the build passed: a fixed-effect
    estimate presented as random-effects. The hidden field and the shown label
    must describe the same analysis.
    """
    FIXED = {"fixed", "none", "iv", "inverse variance", "common effect"}
    for oid, res in canon["results"]["by_outcome"].items():
        used = str(res.get("estimator_used", "")).strip().lower()
        shown = str(res.get("estimator", "")).strip().lower()
        model = str(res.get("model", "")).strip().lower()
        if not used:
            continue
        # "none" and "none (no synthesis)" are the same answer written two ways.
        # Compare what they MEAN, not their exact spelling.
        NONE_FORMS = {"none", "none (no synthesis)", "none (k=1)", "not applicable", "n/a"}
        if shown and used != shown and not (used in NONE_FORMS and shown in NONE_FORMS):
            rep.block("estimator-label-mismatch",
                      f"outcome {oid!r}: pooling used {res.get('estimator_used')!r} but the "
                      f"object shows estimator={res.get('estimator')!r}. A reader would be "
                      f"told one analysis was run while another was.")
        used_is_fixed = used in FIXED
        model_is_fixed = model in ("fixed", "common", "single-study")
        if model and used_is_fixed != model_is_fixed:
            rep.block("estimator-label-mismatch",
                      f"outcome {oid!r}: model={res.get('model')!r} but the estimator "
                      f"actually used ({res.get('estimator_used')!r}) is "
                      f"{'a fixed-effect' if used_is_fixed else 'a random-effects'} method.")


def agreement_tol(want):
    """How far a stored estimate may sit from its recomputation.

    A flat 0.005 was the rule, on the reasoning that a value must agree to two
    decimal places. That reasoning silently inverts for small estimates: a
    vaccine-efficacy risk ratio of 0.0845 could be written as 0.0890 -- a five
    per cent error in the number a reader sees -- and still pass, because the
    absolute gap is 0.0045. An adversary found exactly that and it was confirmed
    by executing it.

    So the allowance is the TIGHTER of two decimal places and one per cent of
    the value itself. Large estimates keep the two-decimal rule; small ones are
    held to a proportionate standard instead of being handed a tolerance many
    times their own magnitude. The floor stops a near-zero value from demanding
    impossible precision.
    """
    return max(min(0.005, 0.01 * abs(want)), 1e-6)


def check_per_trial_recompute(canon, rep):
    """Each per-trial estimate must reproduce from that trial's own two-by-two.

    When an object declines to pool, the per-trial figures become the numbers a
    reader actually sees, so they need the same treatment the pooled estimate
    used to get: recomputed here, not trusted.
    """
    for oid, res in canon["results"]["by_outcome"].items():
        rows = res.get("per_trial") or []
        if not rows:
            continue
        by_id = {t["id"]: t for t in canon["inputs"]["trials"]}
        for r in rows:
            t = by_id.get(r["trial_id"])
            if t is None:
                rep.block("per-trial-unknown",
                          f"outcome {oid!r}: per_trial names {r['trial_id']!r}, which is "
                          f"not a trial in this object")
                continue
            d = t.get("by_outcome", {}).get(oid) or {}
            tx, ct = d.get("treatment"), d.get("control")
            if not (tx and ct):
                continue
            if r.get("point") is None or not r.get("measure"):
                # Nothing to recompute: this row deliberately carries no
                # estimate. check_reference_consistency owns the requirement
                # that it explain itself.
                continue
            got = pool([(tx["events"], tx["n"], ct["events"], ct["n"])],
                       r["measure"], "fixed", r.get("ci_level", 95))
            if got is None:
                rep.block("per-trial-recompute",
                          f"outcome {oid!r}/{r['trial_id']}: cannot recompute a "
                          f"{r['measure']} from the counts given")
                continue
            for f in ("point", "ci_low", "ci_high"):
                if abs(r[f] - got[f]) > agreement_tol(got[f]):
                    rep.block("per-trial-recompute",
                              f"outcome {oid!r}/{r['trial_id']}: {f}={r[f]} but the trial's "
                              f"own two-by-two gives {got[f]:.4f} (allowed "
                              f"{agreement_tol(got[f]):.6g})")


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
            # Judge the VALUE, not its notation. Inferring precision from how a
            # number was typed meant a true 2.0 parsed as dec=1 and was blocked
            # as "coarse" with no way to express it, while -55 against -54.653
            # bought itself a 0.5 tolerance. Requiring agreement to half of the
            # second decimal place enforces the same standard on every value
            # however it happens to be written.
            if abs(have - want) > agreement_tol(want):
                rep.block("pooled-precision",
                          f"outcome {oid!r}: {field}={have} differs from the recomputed "
                          f"{want:.4f} by {abs(have-want):.4f}, more than the allowed "
                          f"{agreement_tol(want):.6g}.")
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
        if res.get("k", 0) >= 2 and res.get("poolable") and not res.get("heterogeneity"):
            rep.block("heterogeneity-missing",
                      f"outcome {oid!r} pools {res['k']} trials but records no heterogeneity")
        if res["k"] < 2 and res.get("heterogeneity"):
            rep.block("heterogeneity-at-k1",
                      f"outcome {oid!r} reports heterogeneity with k={res['k']}")
        if res["k"] < 2 and res.get("pooled"):
            rep.block("pooled-at-k1", f"outcome {oid!r} reports a pooled estimate at k={res['k']}")
        # Poolability is not a consequence of k. Two or more trials CAN be
        # counted and still not estimate a common quantity - covid's three
        # vaccines are the case that taught this. So poolable=false at k>=2 is
        # allowed, but only with a stated reason, and then no pooled figure may
        # be present.
        if res["k"] >= 2 and not res.get("poolable"):
            if not res.get("not_poolable_reason"):
                rep.block("poolable-vs-k",
                          f"outcome {oid!r}: poolable=false at k={res['k']} with no "
                          f"not_poolable_reason. Declining to pool is a judgement and must "
                          f"be justified, not merely asserted.")
            if res.get("pooled"):
                rep.block("poolable-vs-k",
                          f"outcome {oid!r}: declared not poolable but still carries a "
                          f"pooled estimate")
        elif bool(res.get("poolable")) != (res["k"] >= 2):
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


def check_trial_scoped_refs(canon, rep):
    """A per-trial field may not use an alias that points at a fixed trial.

    A note on the second trial said {t.enrolled}, and `t` is bound to trials[0],
    so it silently reported the FIRST trial's number - and {t.dosed} raised on a
    trial that has no such field. Text attached to a record must address that
    record, which is what `self` is for.
    """
    for i, t in enumerate(canon["inputs"]["trials"]):
        def walk(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    if isinstance(v, str) and re.search(r"\{t\d*\.", v):
                        rep.block("trial-scoped-ref",
                                  f"{path}.{k} on {t['id']} uses the fixed alias 't.', "
                                  f"which resolves to the FIRST trial regardless of which "
                                  f"trial the text is attached to. Use 'self.' instead.")
                    elif isinstance(v, (dict, list)):
                        walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for j, v in enumerate(node):
                    walk(v, f"{path}[{j}]")
        walk(t, f"inputs.trials[{i}]")


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
    """Exactly one control; one or more treatments, and more than one only if said.

    The first version demanded exactly one of each, which is wrong for a trial
    that randomises two intervention arms against a shared control. But simply
    permitting many treatment arms would license the defect this rule now
    exists to catch: a build of this very object silently used one of two V114
    formulation arms, and elsewhere silently dropped a route-of-administration
    arm. Neither was visible anywhere in the object.

    So combining arms is allowed and hiding it is not. A trial carrying more
    than one treatment arm must also carry a non-empty arm_selection_note,
    which makes the disclosure structural rather than a courtesy.
    """
    for t in canon["inputs"]["trials"]:
        roles = [a.get("role") for a in t["arms"]]
        controls = roles.count("control")
        treatments = roles.count("treatment")
        if set(roles) - {"control", "treatment"}:
            rep.block("arm-roles",
                      f"{t['id']} declares an arm role outside treatment/control: "
                      f"{sorted(set(roles))!r}")
            continue
        if controls != 1:
            rep.block("arm-roles",
                      f"{t['id']} declares {controls} control arms; a comparison has one")
        if treatments < 1:
            rep.block("arm-roles", f"{t['id']} declares no treatment arm")
        # Also when an arm is SET ASIDE. Requiring a note only for combined
        # treatment arms meant an editor could move an arm into arms_not_used,
        # leaving one treatment arm and no obligation to say why it went.
        if (t.get("arms_not_used") and
                not str(t.get("arm_selection_note", "")).strip()):
            rep.block("arm-roles",
                      f"{t['id']} sets arms aside in arms_not_used but carries no "
                      f"arm_selection_note saying why. Listing an excluded arm is not the "
                      f"same as explaining it.")
        if treatments > 1 and not str(t.get("arm_selection_note", "")).strip():
            rep.block("arm-roles",
                      f"{t['id']} combines {treatments} treatment arms but carries no "
                      f"arm_selection_note. Combining arms is allowed; doing it silently "
                      f"is the defect this rule exists to catch.")


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
            # An ACTIVE comparator is a legitimate control that names a product
            # rather than a placebo, so a head-to-head trial's control arm is not
            # required to look placebo-like. This exempts ONLY that requirement:
            # a TREATMENT arm labelled "placebo" is still a contradiction, and an
            # earlier version of this exemption wrongly cleared both directions.
            active = t.get("comparator_type") == "active"
            if a.get("role") == "treatment" and looks_control:
                rep.block("role-label-contradiction",
                          f"{t['id']}: an arm declares role=treatment but is labelled "
                          f"{a['label']!r}")
            if a.get("role") == "control" and not looks_control and not active:
                rep.block("role-label-contradiction",
                          f"{t['id']}: an arm declares role=control but is labelled "
                          f"{a['label']!r}, which names no comparator")


def entity_names(canon):
    """Names the object holds structurally: arm labels and the arms not used.

    These are entities, not measurements. "Prevnar 13" is what an arm is called;
    the 13 in it is not a number this object computed and cannot go stale.
    """
    out = set()

    def add(lab):
        lab = str(lab).strip()
        if len(lab) <= 2:
            return
        out.add(lab)
        # Registry labels carry trademark marks that prose does not repeat, so
        # "Prevnar 13(TM)" as a label never masked a written "Prevnar 13".
        bare = re.sub(r"[™®©]", "", lab).strip()
        if len(bare) > 2:
            out.add(bare)
            # A label may also be a compound of a group name and a product
            # name ("Group 1: Prevnar 13-Prevnar 13-..."); the product name
            # inside it is still a name.
            for part in re.split(r"[:\-]", bare):
                part = part.strip()
                if len(part) > 4 and re.search(r"[A-Za-z]", part):
                    out.add(part)

    for t in canon.get("inputs", {}).get("trials", []):
        for a in t.get("arms", []):
            add(a.get("label", ""))
        for lab in t.get("arms_not_used", []) or []:
            add(lab)
    return out


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
    # "Group 5" is an arm's NAME, in the same class as an NCT number or a phase:
    # the object holds it structurally as part of the arm label, so prose naming
    # it cannot go stale against a value. Without this exemption a note saying
    # WHICH arms were used could not name them, which would suppress exactly the
    # disclosure check_arm_roles now requires.
    IDENT = re.compile(r"NCT\d{8}|COV\d{3}|PMID\s*\d+|phase\s*\d(?:/\d)?"
                       r"|groups?\s*\d+(?:\s*,\s*\d+)*(?:\s+and\s+\d+)?"
                       r"|\d+\s*-?\s*valent"
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
    # completeness_statement, title, question and definition are all RENDERED,
    # and none of them was scanned: "Seven trials contribute to this review"
    # sat in the badge a reader sees and no rule looked at it. A prose rule that
    # skips the most prominent prose in the object is a rule about the parts
    # nobody reads.
    PROSE_KEYS = ("note", "detail", "reason", "source", "access_note",
                  "caveat", "disclosure_note", "statement", "title", "question",
                  "definition")

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
                    # Entity NAMES the object already holds -- arm labels like
                    # "Prevnar 13" or "Group 5" -- are masked before the numeral
                    # scan. A numeral inside a product name is part of the name,
                    # not a copy of a value, and blocking it would make the
                    # disclosure notes that must name arms unwritable.
                    for nm in sorted(entity_names(canon), key=len, reverse=True):
                        masked = masked.replace(nm, " ")
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


def check_source_category_binding(canon, rep, sources_root=None):
    """A cell drawn from a multi-category outcome must NAME its category.

    This detector exists because of a defect it did not catch in time. A build
    of prevnar15-pneumo read each trial's solicited injection-site outcome by
    taking the LAST posted measurement row. That outcome is not one number: the
    registry posts it as several categories -- erythema, induration, pain,
    swelling -- and the last row is swelling in most of these trials. The object
    therefore published SWELLING under the name "any solicited injection-site
    adverse event".

    Every one of those cells was arithmetically correct, resolved to a real
    registry row, and named a real posted outcome title. The object passed
    sixteen of sixteen detectors, and the reference synthesis later confirmed
    the numbers were right for a different symptom. Nothing internal could see
    it, because nothing was internally wrong. The binding was wrong.

    So the rule is: if the outcome the object cites posts more than one
    category, the object must say which one it read, and the value it stores
    must equal the value posted under THAT category for THOSE arms. Naming the
    outcome is not enough when the outcome is not a single number.
    """
    root = pathlib.Path(sources_root or "sources") / canon["app_id"]
    if not root.is_dir():
        return  # against-sources already blocks on missing payloads

    def norm(s):
        return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()

    for t in canon["inputs"]["trials"]:
        nct = t.get("nct", "")
        f = root / f"{nct}.ctgov.json"
        if not f.is_file():
            continue
        try:
            oms = (json.loads(f.read_text(encoding="utf-8"))["resultsSection"]
                   ["outcomeMeasuresModule"]["outcomeMeasures"])
        except Exception:
            continue
        for oid, d in t.get("by_outcome", {}).items():
            prov = d.get("provenance") or {}
            if not str(prov.get("source_id", "")).startswith("REGISTRY"):
                continue
            title = prov.get("source_outcome_title")
            m = next((o for o in oms if (o.get("title") or "") == title), None)
            if m is None:
                continue  # against-sources owns the unbound-title case
            cats = [(cl, cat) for cl in m.get("classes", [])
                    for cat in cl.get("categories", [])]
            labels = [norm((cl.get("title") or "") + " " + (cat.get("title") or ""))
                      for cl, cat in cats]
            named = prov.get("source_category_title")
            if len(cats) <= 1:
                continue
            if not named:
                rep.block("source-category-unbound",
                          f"{t['id']}/{oid} cites outcome {str(title)[:52]!r} in {nct}, "
                          f"which posts {len(cats)} distinct categories "
                          f"({', '.join(l[:22] for l in labels[:4])}). The object names no "
                          f"category, so this cell cannot be identified in the source: any "
                          f"of those rows would satisfy it.")
                continue
            want = norm(named)
            if want not in labels:
                rep.block("source-category-mismatch",
                          f"{t['id']}/{oid} names category {named!r}, which {nct} does not "
                          f"post under that outcome. Posted: "
                          f"{', '.join(l[:22] for l in labels)}")
                continue
            # The category must be the SYMPTOM THE OUTCOME CLAIMS TO BE. Naming
            # a category was not enough: a reviewer relabelled a pain cell to
            # "Swelling", moved the swelling numbers in with it, recomputed, and
            # it passed -- publishing swelling under the reader-visible heading
            # "pain", which is precisely the defect this rule exists to prevent,
            # reachable again. Confirmed by executing it.
            #
            # So the category title and the outcome's own NAME must refer to the
            # same symptom. The outcome name is what a reader sees, which makes
            # it the right thing to hold the binding to.
            oname = next((o.get("name", "") for o in canon.get("outcomes", [])
                          if o.get("id") == oid), "")
            TERMS = ("pain", "tenderness", "swelling", "erythema", "redness",
                     "induration", "hard lump", "bruis", "itch")
            in_out = {w for w in TERMS if w in norm(oname)}
            in_cat = {w for w in TERMS if w in norm(named)}
            if in_cat and not in_out:
                # An outcome whose cells read a SPECIFIC symptom category must
                # say which symptom it reports. Requiring only that the two
                # AGREE let the check be switched off by renaming the outcome to
                # something with no symptom in it: relabelling a swelling
                # outcome "Any solicited injection-site adverse event" emptied
                # the outcome's term set, and the whole rule was skipped --
                # publishing swelling under a composite name, which is the
                # original defect of this object reproduced exactly. Confirmed
                # by executing it.
                rep.block("outcome-name-unspecific",
                          f"{t['id']}/{oid} reads the specific category {named!r} but its "
                          f"outcome is named {oname!r}, which names no symptom. A cell "
                          f"bound to one symptom may not be published under a heading that "
                          f"implies several.")
                continue
            if in_out and in_cat and not (in_out & in_cat):
                rep.block("category-outcome-mismatch",
                          f"{t['id']}/{oid} reads category {named!r} under an outcome named "
                          f"{oname!r}. Those name different symptoms, so the cell is bound "
                          f"to a real registry row that is not the row this outcome "
                          f"claims to report.")
                continue
            cl, cat = cats[labels.index(want)]
            gt = {g["id"]: (g.get("title") or "") for g in m.get("groups", [])}
            vals = {mm["groupId"]: mm.get("value") for mm in cat.get("measurements", [])}
            dn = {x["groupId"]: x["value"] for g in m.get("denoms", [])
                  for x in g.get("counts", [])}
            for role in ("treatment", "control"):
                arm = d.get(role) or {}
                labs = [a.get("label", "") for a in t.get("arms", [])
                        if a.get("role") == role]
                gids = [g for g, ttl in gt.items()
                        if any(ttl.startswith(l) or l.startswith(ttl) for l in labs if l)]
                if not gids:
                    rep.block("source-category-unbound",
                              f"{t['id']}/{oid}/{role}: no posted arm in {nct} matches the "
                              f"declared label(s) {labs!r}, so the cell cannot be located.")
                    continue
                # Arms are matched by prefix, so a SHORTER declared label
                # silently swallows every posted arm beginning with it:
                # declaring one arm "V114" absorbed both "V114-A" and "V114-B",
                # and because only one treatment arm was then declared,
                # check_arm_roles never asked for the disclosure it exists to
                # require. A reviewer found this and it was confirmed. One
                # declared arm must correspond to one posted arm.
                if len(gids) > len([l for l in labs if l]):
                    matched = sorted(gt[g][:40] for g in gids)
                    rep.block("arm-absorption",
                              f"{t['id']}/{oid}/{role}: {len(labs)} declared label(s) "
                              f"{labs!r} match {len(gids)} posted arms {matched}. A label "
                              f"that is a prefix of several arms combines them without "
                              f"declaring them, which is how an arm gets dropped or merged "
                              f"invisibly. Name each arm.")
                    continue
                stored = arm.get("percentages_by_arm") or (
                    [arm["percentage"]] if arm.get("percentage") is not None else None)
                if stored is None:
                    # NOT a skip. A reviewer showed that deleting `percentage`
                    # made this check and the DERIVED branch of against-sources
                    # both `continue`, so fabricated counts passed with the pool
                    # recomputed to match. Confirmed by executing it. A cell
                    # whose source value is absent is unverifiable, and an
                    # unverifiable cell does not pass -- it blocks.
                    rep.block("source-cell-uncheckable",
                              f"{t['id']}/{oid}/{role} is DERIVED from a registry "
                              f"percentage but stores no percentage, so its counts cannot "
                              f"be checked against the source at all. Omitting the value "
                              f"must not be a way to escape the check.")
                    continue
                posted = sorted(float(vals[g]) for g in gids if vals.get(g) is not None)
                if len(posted) != len(stored):
                    rep.block("source-category-mismatch",
                              f"{t['id']}/{oid}/{role}: stores {len(stored)} arm value(s) "
                              f"but {len(posted)} arm(s) match in {nct}")
                    continue
                for a, b in zip(sorted(float(x) for x in stored), posted):
                    if abs(a - b) > 1e-9:
                        rep.block("source-category-mismatch",
                                  f"{t['id']}/{oid}/{role}: stores {a} but {nct} posts {b} "
                                  f"under category {named!r}. A cell must equal the value "
                                  f"posted for the category it cites.")
                nsum = sum(int(dn[g]) for g in gids if g in dn)
                if nsum and arm.get("n") is not None and int(arm["n"]) != nsum:
                    rep.block("source-category-mismatch",
                              f"{t['id']}/{oid}/{role}: n={arm['n']} but the matching arm(s) "
                              f"in {nct} have denominator {nsum}")
                # The event count itself, for the multi-arm case. The DERIVED
                # branch of check_against_sources requires a scalar `percentage`
                # and skips when a trial carries `percentages_by_arm` instead, so
                # a combined arm's events could be set to any value while its
                # per-arm percentages and summed denominator still matched. A
                # reviewer moved 283 to 250 and it passed. Confirmed.
                # Every arm, not only combined ones. This ran under len(gids) > 1
                # while the DERIVED branch of check_against_sources required a
                # scalar `percentage` and skipped anything carrying
                # percentages_by_arm. A single arm written with
                # percentages_by_arm therefore fell between the two, and a
                # reviewer moved a control count from 260 to 200 with everything
                # downstream recomputed and it passed. Confirmed.
                if arm.get("events") is not None:
                    want_ev = sum(round(float(vals[g]) / 100 * int(dn[g]))
                                  for g in gids if vals.get(g) is not None and g in dn)
                    if want_ev and int(arm["events"]) != want_ev:
                        rep.block("derivation-mismatch",
                                  f"{t['id']}/{oid}/{role}: events={arm['events']} but "
                                  f"deriving each arm from its own posted percentage and "
                                  f"denominator gives {want_ev}. A combined arm's count must "
                                  f"still be the sum of the arms it combines.")


def check_subgroup_recompute(canon, rep):
    """A subgroup estimate is a reader-visible pooled number and must recompute.

    check_pooled_recompute reads only `res["pooled"]`. Subgroups were added to
    this schema and never brought under it, so a reviewer changed the adult
    subgroup point from 1.1696 to 9.1696 and the object still passed 19 of 19.
    Confirmed by executing it.

    Any figure a reader sees gets the same treatment as the headline: recomputed
    from the trials it names, not trusted because it sits in a different key.
    """
    for oid, res in canon["results"]["by_outcome"].items():
        subs = res.get("subgroups") or []
        if not subs:
            continue
        by_id = {t["id"]: t for t in canon["inputs"]["trials"]}
        for sg in subs:
            ids = sg.get("trial_ids") or []
            if len(set(ids)) != len(ids):
                dupes = sorted({i for i in ids if ids.count(i) > 1})
                rep.block("subgroup-duplicate-trial",
                          f"outcome {oid!r}: subgroup {sg.get('id')!r} names {dupes} more "
                          f"than once. The recomputation iterates the list, so a repeated "
                          f"identifier double-counts that trial and the stored estimate "
                          f"can be moved to match it. A trial contributes once.")
                continue
            if not ids:
                rep.block("subgroup-unanchored",
                          f"outcome {oid!r}: subgroup {sg.get('id')!r} names no trial_ids, "
                          f"so its estimate cannot be recomputed from anything.")
                continue
            rows = []
            for tid in ids:
                t = by_id.get(tid)
                if t is None:
                    rep.block("subgroup-unknown-trial",
                              f"outcome {oid!r}: subgroup {sg.get('id')!r} names {tid!r}, "
                              f"which is not a trial in this object")
                    rows = None
                    break
                d = (t.get("by_outcome") or {}).get(oid) or {}
                tx, ct = d.get("treatment"), d.get("control")
                if not (tx and ct):
                    # BLOCK, not skip. Setting rows=None and continuing meant a
                    # subgroup that named a trial lacking this outcome had its
                    # ENTIRE recomputation -- and its k check -- silently
                    # bypassed, so its estimate could be set to anything. A
                    # reviewer deleted one outcome block, left the trial id in
                    # the stratum, and put 9.99 through undetected. Confirmed.
                    rep.block("subgroup-missing-outcome",
                              f"outcome {oid!r}: subgroup {sg.get('id')!r} names {tid!r}, "
                              f"which carries no data for this outcome. A stratum cannot "
                              f"pool a trial that does not report the thing being pooled, "
                              f"and skipping the check instead of failing it left the "
                              f"stratum estimate unverified.")
                    rows = None
                    break
                rows.append((tx["events"], tx["n"], ct["events"], ct["n"]))
            if not rows:
                continue
            if int(sg.get("k", len(rows))) != len(rows):
                rep.block("subgroup-k",
                          f"outcome {oid!r}: subgroup {sg.get('id')!r} declares k="
                          f"{sg.get('k')} but names {len(rows)} trials")
            got = pool(rows, sg.get("measure", "RR"),
                       res.get("estimator_used", "DerSimonian-Laird"),
                       sg.get("ci_level", 95))
            if got is None:
                rep.block("subgroup-recompute",
                          f"outcome {oid!r}: subgroup {sg.get('id')!r} cannot be recomputed "
                          f"from the counts of the trials it names")
                continue
            for field in ("point", "ci_low", "ci_high"):
                if field not in sg:
                    continue
                if abs(float(sg[field]) - got[field]) > agreement_tol(got[field]):
                    rep.block("subgroup-recompute",
                              f"outcome {oid!r}: subgroup {sg.get('id')!r} {field}="
                              f"{sg[field]} but pooling the {len(rows)} trials it names "
                              f"gives {got[field]:.4f}")


_REVIEW_NUMBERS = {}


def _review_numbers(path):
    """Every number in a staged review payload, as floats, read once.

    Textual matching is not usable here: the review prints its figures as
    "91.10" where the object stores 91.1, so searching for the object's
    spelling reported a value that is plainly present as absent. Numbers are
    compared as numbers.
    """
    key = str(path)
    if key not in _REVIEW_NUMBERS:
        text = path.read_text(encoding="utf-8", errors="replace")
        _REVIEW_NUMBERS[key] = {float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)}
    return _REVIEW_NUMBERS[key]


def check_reference_consistency(canon, rep, sources_root=None):
    """A per-trial estimate must not contradict the published figure beside it,
    and that published figure must itself be READ BACK from the review.

    This is the external anchor for an object that declines to pool, since
    check_direction_anchor returns early when there is no pooled result.

    An earlier version of this docstring said the published figure "is outside
    the object and cannot be flipped by editing the object". That was FALSE and
    a reviewer proved it: reference_efficacy_percent is stored INSIDE the
    object, so inverting a trial's arms, recomputing its ratio exactly, and
    moving the reference figure to match passed everything -- leaving the object
    reporting a vaccine that multiplies risk twelvefold. Confirmed by executing
    it.

    An anchor nothing checks is not an anchor, it is another editable field. So
    every reference figure is now looked up in the staged payload of the review
    it is attributed to. If that payload is not staged, the figure is
    unverifiable and blocks rather than passing.

    Where the object records what a published review reports for the same trial,
    that figure is outside the object and cannot be flipped by editing the
    object. Requiring the stored estimate to agree with it in DIRECTION, and not
    to diverge wildly in magnitude, makes an arm swap contradict a number the
    editor does not control.

    Magnitude is checked loosely on purpose. A crude count-based risk ratio and
    a review's model-based efficacy legitimately differ -- one contributing
    trial here analysed its outcome on person-time, a documented 2.6 point gap.
    The check is aimed at inversions and gross errors, not at that.
    """
    # Was 15 points, chosen to leave room for method differences. A reviewer
    # showed that room was a hiding place: a reference efficacy could be moved
    # from 91.1 to 80.0 and still pass. The largest genuine gap in these objects
    # is 2.6 points, from a trial analysed on person-time against a crude count
    # ratio, so 6 leaves that comfortably clear while closing the gap.
    MARGIN_PP = 6.0
    root = pathlib.Path(sources_root or "sources") / canon["app_id"]
    for oid, res in canon["results"]["by_outcome"].items():
        for r in res.get("per_trial") or []:
            ref = r.get("reference_efficacy_percent")
            if ref is None:
                continue
            sid = r.get("reference_source_id")
            src = (canon.get("sources") or {}).get(sid) or {}
            staged_as = src.get("staged_as")
            path = (root / staged_as) if staged_as else None
            if path is None or not path.is_file():
                rep.block("reference-unstaged",
                          f"outcome {oid!r}/{r['trial_id']} cites a published figure of "
                          f"{ref} from {sid!r}, whose source entry names no staged payload "
                          f"this validator can open. A figure described as external, held "
                          f"in an editable field and checked against nothing, is not an "
                          f"anchor.")
                continue
            nums = _review_numbers(path)
            for key in ("reference_efficacy_percent", "reference_ci_low_percent",
                        "reference_ci_high_percent"):
                val = r.get(key)
                if val is None:
                    continue
                if not any(abs(float(val) - x) < 1e-9 for x in nums):
                    rep.block("reference-unsupported",
                              f"outcome {oid!r}/{r['trial_id']}: {key}={val} does not "
                              f"appear anywhere in {staged_as}, the payload of the review "
                              f"it is attributed to. The figure cannot be moved to suit "
                              f"the object's own estimate.")
            if r.get("point") is None:
                # A row may legitimately carry a published figure and NO ratio of
                # our own: one trial reports its events over an efficacy
                # population whose per-arm denominators are never published, so
                # no count-based ratio is computable. The reference figure is
                # still checked against the staged review above; there is simply
                # nothing of ours to compare its direction with.
                if not str(r.get("not_computed_reason", "")).strip():
                    rep.block("reference-without-estimate",
                              f"outcome {oid!r}/{r['trial_id']} carries a published figure "
                              f"but no estimate of its own and no not_computed_reason. A "
                              f"row that declines to compute must say why.")
                continue
            ours_pp = 100.0 * (1.0 - r["point"])
            if (ours_pp >= 0) != (ref >= 0):
                rep.block("reference-contradiction",
                          f"outcome {oid!r}/{r['trial_id']}: this object's estimate implies "
                          f"{ours_pp:.1f}% efficacy while the published review it cites "
                          f"reports {ref}%. The two point in OPPOSITE directions, which an "
                          f"arm swap produces and self-consistent arithmetic cannot reveal.")
                continue
            if abs(ours_pp - ref) > MARGIN_PP:
                rep.block("reference-contradiction",
                          f"outcome {oid!r}/{r['trial_id']}: this object implies "
                          f"{ours_pp:.1f}% efficacy against a published {ref}% -- a gap of "
                          f"{abs(ours_pp-ref):.1f} points, beyond the {MARGIN_PP:.0f} allowed "
                          f"for method differences. Explain it or fix it.")


def check_arm_completeness(canon, rep, sources_root=None):
    """Every arm the SOURCE posts must be declared or explicitly set aside.

    check_arm_roles requires a disclosure when a trial DECLARES more than one
    treatment arm. A reviewer showed that is the wrong hinge: delete the second
    V114 arm from the object entirely, drop the note, and use one formulation's
    own numbers. Every remaining cell then matches the source, the pool
    recomputes, and nothing fires -- because a detector that reads the declared
    arms cannot see an arm that was never declared. Confirmed by executing it.

    The fix has to come from outside the object. This enumerates the arms the
    registry actually posts for the cited outcome and requires each one to be
    either used or named in arms_not_used, so dropping an arm becomes a visible
    act rather than an absence.
    """
    root = pathlib.Path(sources_root or "sources") / canon["app_id"]
    if not root.is_dir():
        return
    for t in canon["inputs"]["trials"]:
        f = root / f"{t.get('nct', '')}.ctgov.json"
        if not f.is_file():
            continue
        try:
            oms = (json.loads(f.read_text(encoding="utf-8"))["resultsSection"]
                   ["outcomeMeasuresModule"]["outcomeMeasures"])
        except Exception:
            continue
        for oid, d in t.get("by_outcome", {}).items():
            prov = d.get("provenance") or {}
            if not str(prov.get("source_id", "")).startswith("REGISTRY"):
                continue
            m = next((o for o in oms
                      if (o.get("title") or "") == prov.get("source_outcome_title")), None)
            if m is None:
                continue
            posted = [(g.get("title") or "") for g in m.get("groups", [])]
            declared = [str(a.get("label", "")) for a in t.get("arms", [])]
            setaside = [str(x) for x in (t.get("arms_not_used") or [])]
            for ptitle in posted:
                if any(ptitle.startswith(l) or l.startswith(ptitle)
                       for l in declared if l):
                    continue
                if any(ptitle.startswith(l) or l.startswith(ptitle)
                       for l in setaside if l):
                    continue
                rep.block("arm-undisclosed",
                          f"{t['id']}/{oid}: the registry posts an arm {ptitle[:48]!r} for "
                          f"the cited outcome which this object neither uses nor lists in "
                          f"arms_not_used. Excluding an arm is allowed; excluding it "
                          f"invisibly is the defect this rule exists to catch.")


def check_arm_role_vs_registry(canon, rep, sources_root=None):
    """A declared role must agree with the arm type the REGISTRY posts.

    check_role_label_agreement reads an arm's own label against a keyword list,
    which cannot tell one vaccine from another: a reviewer swapped the roles AND
    the data blocks of a head-to-head trial, recomputed everything including
    `favours`, and it passed with the object reporting the comparator as the
    intervention. Confirmed by executing it. Every label-based check has this
    hole, because both labels are product names.

    ClinicalTrials.gov records what each arm IS -- EXPERIMENTAL,
    ACTIVE_COMPARATOR, PLACEBO_COMPARATOR -- and that is outside the object.
    Anchoring roles there closes the swap: inverting the object no longer
    inverts the source.
    """
    TREAT = {"EXPERIMENTAL"}
    CONTROL = {"ACTIVE_COMPARATOR", "PLACEBO_COMPARATOR", "SHAM_COMPARATOR",
               "NO_INTERVENTION"}
    root = pathlib.Path(sources_root or "sources") / canon["app_id"]
    if not root.is_dir():
        return
    for t in canon["inputs"]["trials"]:
        f = root / f"{t.get('nct', '')}.ctgov.json"
        if not f.is_file():
            continue
        try:
            ag = (json.loads(f.read_text(encoding="utf-8"))["protocolSection"]
                  ["armsInterventionsModule"]["armGroups"])
        except Exception:
            continue
        posted = {(g.get("label") or ""): (g.get("type") or "") for g in ag}
        if not posted:
            continue
        for a in t.get("arms", []):
            lab, role = str(a.get("label", "")), a.get("role")
            hits = [ty for plab, ty in posted.items()
                    if plab and (plab.startswith(lab) or lab.startswith(plab))]
            if not hits:
                continue
            want = TREAT if role == "treatment" else CONTROL
            if not any(ty in want for ty in hits):
                rep.block("arm-role-vs-registry",
                          f"{t['id']}: arm {lab!r} is declared {role!r} but the registry "
                          f"posts it as {hits!r}. A role is not a matter of opinion when "
                          f"the source records what the arm was.")


DETECTORS = [
    ("outcome-coverage", check_outcome_coverage),
    ("arm-role-vs-registry", lambda c, r: check_arm_role_vs_registry(c, r)),
    ("superseded", check_superseded),
    ("removal-disclosure", check_removal_disclosure),
    ("trial-scoped-refs", check_trial_scoped_refs),
    ("source-ids", check_source_ids),
    ("against-sources", check_against_sources),
    ("source-category-binding", check_source_category_binding),
    ("arm-completeness", check_arm_completeness),
    ("reference-consistency", lambda c, r: check_reference_consistency(c, r)),
    ("subgroup-recompute", check_subgroup_recompute),
    ("arm-roles", check_arm_roles),
    ("role-label-agreement", check_role_label_agreement),
    ("prose-numerals", check_prose_numerals),
    ("direction-anchor", check_direction_anchor),
    ("counts-sane", check_counts_sane),
    ("k-derived", check_k_derived),
    ("heterogeneity-and-k", check_heterogeneity_and_k),
    ("estimator-labels", check_estimator_labels),
    ("per-trial-recompute", check_per_trial_recompute),
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
