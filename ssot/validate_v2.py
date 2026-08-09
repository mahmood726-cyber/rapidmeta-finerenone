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

# 97.5 is here because the RTS,S phase 3 states its twelve-month co-primary
# efficacy at that level rather than at 95, on account of its interim looks --
# the same class of fact as the 95.8 per cent interval recorded in the schema
# for ChAdOx1. Assuming 95 for such a figure silently narrows a correctly
# published interval, so the level travels with the estimate and the constant
# must exist for the level the source actually used.
Z = {90: 1.644853627, 95: 1.959963985, 97.5: 2.241402728, 99: 2.575829304}


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
    elif estimator.lower() in ("reml", "restricted maximum likelihood"):
        # Added because the alternative was worse. Handbook 10.10.4.4 records
        # REML as RevMan's default and says other estimators outperform
        # DerSimonian-Laird -- but this function could only recompute DL, so an
        # object wanting the Handbook's default had to choose between being
        # method-correct and being externally checkable. A reviewer put exactly
        # that to an object here. Implementing it removes the choice.
        from estimators import tau2_reml
        tau2 = tau2_reml(list(ys), list(vs))
    elif estimator.lower() in ("pm", "paule-mandel", "paule mandel"):
        from estimators import tau2_pm
        tau2 = tau2_pm(list(ys), list(vs))
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
    # STAGED_AS MUST BIND TO A FILE THAT EXISTS.
    #
    # The registry names, for each source, the file it was read from. Nothing
    # checked that the name resolved. One object pointed every entry at a JSON
    # wrapper the gate deliberately withholds from reviewers, and a checker
    # following the registry would have been sent to a file no leg ever saw --
    # caught by a reviewer, not by this. A registry entry that cannot be opened
    # is not provenance, it is a label.
    for sid, src in (canon.get("sources") or {}).items():
        named = src.get("staged_as")
        if named and not (root / named).is_file():
            rep.block("staged-as-unresolvable",
                      f"source {sid!r} says it is staged as {named!r}, and no such "
                      f"file is in {root}. The registry must name a file a reader "
                      f"can actually open.")

    blobs, raw_blobs = {}, {}
    for f in root.glob("*"):
        # .txt is loaded too. It was excluded, so the verbatim TEXT extracts --
        # which are what the gate hands every reviewer, and what the quoted
        # sentences were read from -- were bound by nothing here.
        if f.suffix in (".json", ".xml", ".txt"):
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
                # An effect DERIVED from a published vaccine efficacy is not in the
                # source as a ratio -- the source prints a percentage. Demanding the
                # ratio appear literally was therefore both wrong and, worse, WEAK:
                # a short ratio like 0.23 is a token that turns up somewhere in a
                # large payload by coincidence, so the check passed for the wrong
                # reason on some rows and failed honestly on others.
                #
                # What must hold for a derived value is what already holds for a
                # derived count: its INPUTS are sourced, and the derivation
                # reproduces the stored value. Both are checked here, so moving
                # either the stored ratio or the published percentage it came from
                # now breaks the pair.
                if eff.get("derived_from") == "published_vaccine_efficacy_percent":
                    trio = [("published_ve_percent", "point"),
                            ("published_ve_ci_high_percent", "ci_low"),
                            ("published_ve_ci_low_percent", "ci_high")]
                    for src_key, eff_key in trio:
                        pct = eff.get(src_key)
                        if pct is None:
                            rep.block("derivation-unsourced",
                                      f"{t['id']}/{oid}: effect.{eff_key} is declared "
                                      f"derived from a published efficacy but "
                                      f"{src_key} is absent, so there is nothing to "
                                      f"derive it from or to check it against.")
                            continue
                        if find(pct, nct) is None:
                            rep.block("source-unsupported",
                                      f"{t['id']}/{oid}: {src_key}={pct} is the "
                                      f"published figure this effect is derived from, "
                                      f"but it does not appear in any payload staged "
                                      f"for {nct}.")
                        want = round(1 - pct / 100, 4)
                        if abs(eff[eff_key] - want) > 1e-9:
                            rep.block("derivation-mismatch",
                                      f"{t['id']}/{oid}: effect.{eff_key}="
                                      f"{eff[eff_key]} but the published {src_key}="
                                      f"{pct} gives {want}. The efficacy interval "
                                      f"INVERTS into the ratio interval, and a row "
                                      f"that does not reproduce has either the wrong "
                                      f"stored value or the bounds the wrong way "
                                      f"round.")
                else:
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
            # Every trial-level number a READER can reach, not just `enrolled`.
            # Both gate families demonstrated the gap with the same shape of
            # edit: registry_enrolment 33758 -> 12345 and dosed 39540 -> 12345
            # both returned VALIDATOR CLEAN, and both are interpolated into
            # rendered prose ("The registry records an ACTUAL enrolment of
            # {self.registry_enrolment}"). A field that reaches a reader and is
            # checked against nothing is an editable field wearing a citation.
            for fld in ("enrolled", "registry_enrolment", "dosed"):
                if t.get(fld) is not None:
                    cells[fld] = t[fld]
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
            if r.get("point") is None:
                # Nothing to recompute: this row deliberately carries no
                # estimate. check_reference_consistency owns the requirement
                # that it explain itself.
                continue
            if not r.get("measure"):
                # A row that HAS a point but no measure used to fall through the
                # same `continue`, which made `measure` a delete-to-disable
                # switch: drop the key and ci_high could then be moved to
                # anything. A row carrying a reader-visible estimate must say
                # what that estimate IS, or it cannot be recomputed at all.
                rep.block("per-trial-unmeasured",
                          f"outcome {oid!r}/{r['trial_id']} carries point={r['point']} but "
                          f"names no measure, so nothing can recompute it. Deleting the "
                          f"measure key must not be a way to switch this check off.")
                continue
            got = pool([(tx["events"], tx["n"], ct["events"], ct["n"])],
                       r["measure"], "fixed", r.get("ci_level", 95))
            if got is None:
                rep.block("per-trial-recompute",
                          f"outcome {oid!r}/{r['trial_id']}: cannot recompute a "
                          f"{r['measure']} from the counts given")
                continue
            # A BOUNDARY row carries a point with no interval, because the point
            # sits where the log scale ends. Its point must still recompute; it
            # is the interval, and only the interval, that is allowed to be
            # absent -- and it must then be absent on BOTH sides, so the
            # declaration cannot be used to hide one bound.
            boundary = bool(str(r.get("not_log_transformable_because", "")).strip())
            fields = ("point", "ci_low", "ci_high")
            if boundary:
                # pool() adds the usual half to every cell when one is zero. A
                # boundary row is precisely the row that DECLINES that
                # correction, so recomputing it through pool() would compare the
                # stored number against a correction the object refused. Redo
                # the arithmetic raw. This is stricter than the pooled path, not
                # looser: it pins the point to exact division.
                # Reaching here means pool() accepted the measure, and pool()
                # accepts only the two that a 2x2 determines, so both are
                # handled and there is no third case to guard against.
                if r["measure"] == "RR":
                    raw = (tx["events"] / tx["n"]) / (ct["events"] / ct["n"])
                else:
                    raw = ((tx["events"] / (tx["n"] - tx["events"])) /
                           (ct["events"] / (ct["n"] - ct["events"])))
                got = dict(got, point=raw)
                if r.get("ci_low") is not None or r.get("ci_high") is not None:
                    rep.block("boundary-row-half-interval",
                              f"outcome {oid!r}/{r['trial_id']} declares itself "
                              f"not log-transformable but still carries an "
                              f"interval bound. A boundary row has no interval "
                              f"on either side or it is not a boundary row.")
                fields = ("point",)
            for f in fields:
                if r.get(f) is None:
                    rep.block("per-trial-missing-bound",
                              f"outcome {oid!r}/{r['trial_id']} carries "
                              f"point={r['point']} but no {f}, and does not "
                              f"declare itself a boundary estimate. A row with "
                              f"a reader-visible point owes a full interval.")
                    continue
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
    # A cited SECTION NUMBER is a name, in the same class as an NCT number: the
    # object cites "section 10.10.2" of a published methods handbook, and the
    # digits in it are an address, not a quantity this object computed. Without
    # this, citing the authority a decision rests on was impossible -- the rule
    # fired on the citation and the only way to satisfy it was to stop naming
    # the section, which is the opposite of what sourcing a decision means.
    IDENT = re.compile(r"NCT\d{8}|COV\d{3}|PMID\s*\d+|phase\s*\d(?:/\d)?"
                       r"|HIV-\d|SARS-CoV-\d"
                       r"|groups?\s*\d+(?:\s*,\s*\d+)*(?:\s+and\s+\d+)?"
                       r"|\d+\s*-?\s*valent"
                       r"|sections?\s*\d+(?:\.\d+)*(?:\s*(?:,|and)\s*"
                       r"\d+(?:\.\d+)*)*"
                       r"|version\s*\d+"
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
    # "difference" and "divergence" were added after both gate families noticed
    # the same hole independently: estimand_difference and source_divergence are
    # prose, are RENDERED on the row a reader sees, and matched no entry here,
    # so they could restate any structured value and go stale against it freely.
    PROSE_KEYS = ("note", "detail", "reason", "source", "access_note",
                  "caveat", "disclosure_note", "statement", "title", "question",
                  "definition", "difference", "divergence")

    structured: set[str] = set()
    # CONFIGURATION is not data. schema_version, a source's layer_rank, the
    # confidence level and an outcome's null value are properties of the format,
    # not quantities a sentence could be restating -- and treating them as data
    # produced a false block the moment this rule was widened to cover more prose
    # keys: "the two arms" collided with schema_version 2, so a sentence
    # correctly quoting an earlier version of itself was reported as a stale copy
    # of the SCHEMA NUMBER. A rule that fires on a coincidence teaches people to
    # edit true prose until the tool stops complaining.
    STRUCTURAL = {"schema_version", "layer_rank", "confidence_level", "ci_level",
                  "null_value"}

    def collect(node):
        if isinstance(node, dict):
            for key, val in node.items():
                if isinstance(val, bool) or key in STRUCTURAL:
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
        outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
        if not rec:
            # An object that declines to pool used to leave this detector with
            # nothing to do, and direction_of_benefit -- which says which way
            # counts as better -- was then checked by no rule at all. Flipping it
            # to "higher", so the object asserts that MORE disease is the
            # benefit, returned clean. With no pooled interval to read, the
            # anchor is the published figure each row already carries: a review
            # reporting positive efficacy means a ratio measure goes DOWN when
            # the intervention helps.
            w = outcome.get("direction_of_benefit")
            if w is None:
                rep.block("direction-unanchored",
                          f"outcome {oid!r} declares no direction_of_benefit and has no "
                          f"pooled result, so nothing records which way is better.")
                continue
            if outcome.get("measure") in ("RR", "OR", "HR"):
                for r in res.get("per_trial") or []:
                    ref = r.get("reference_efficacy_percent")
                    if ref is None:
                        continue
                    implied = "lower" if ref > 0 else "higher"
                    if w != implied:
                        rep.block("direction-anchor",
                                  f"outcome {oid!r}/{r['trial_id']}: the published review "
                                  f"reports {ref}% efficacy, so benefit is a {implied} "
                                  f"{outcome['measure']}, but the outcome declares "
                                  f"direction_of_benefit={w!r}.")
                        break
            continue
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
                boundary = bool(str(eff.get("not_log_transformable_because", "")).strip())
                ordered = ((eff["ci_low"] <= eff["point"] <= eff["ci_high"])
                           if boundary else
                           (eff["ci_low"] < eff["point"] < eff["ci_high"]))
                if not ordered:
                    rep.block("arithmetic",
                              f"{t['id']}/{oid}: interval is not ordered around the point "
                              f"({eff['ci_low']}, {eff['point']}, {eff['ci_high']})")
                if boundary and eff["point"] > eff["ci_low"]:
                    rep.block("boundary-effect-misdeclared",
                              f"{t['id']}/{oid}: the effect declares itself a "
                              f"boundary estimate that cannot be log-transformed, "
                              f"but its point {eff['point']} lies strictly above "
                              f"its lower limit {eff['ci_low']}, so it is an "
                              f"ordinary estimate and the declaration is an "
                              f"escape from the log-scale checks.")
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
            rows, effects = [], []
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
                if d.get("effect"):
                    # A stratum over EFFECT-based rows was unverifiable here: this
                    # detector only knew how to pool two-by-two counts, so a
                    # subgroup of trials that report an effect estimate fell into
                    # the missing-outcome branch and was reported as carrying no
                    # data when it carried exactly the data being pooled. An
                    # outcome whose trials report hazard or rate ratios has no
                    # counts to pool and must still have its strata recomputed.
                    effects.append(d["effect"])
                    continue
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
            if rows is None:
                continue
            if rows and effects:
                rep.block("subgroup-mixed-input-forms",
                          f"outcome {oid!r}: subgroup {sg.get('id')!r} names trials "
                          f"that report counts AND trials that report effect "
                          f"estimates. Their variances derive differently and a "
                          f"stratum may not silently combine both.")
                continue
            n_contrib = len(rows) + len(effects)
            if not n_contrib:
                continue
            if int(sg.get("k", n_contrib)) != n_contrib:
                rep.block("subgroup-k",
                          f"outcome {oid!r}: subgroup {sg.get('id')!r} declares k="
                          f"{sg.get('k')} but names {n_contrib} trials")
            if n_contrib < 2:
                # A one-trial stratum has nothing to pool, but its printed value
                # must still BE that trial's value rather than anything typed in.
                only = (effects or [None])[0]
                if only:
                    for field in ("point", "ci_low", "ci_high"):
                        if field in sg and abs(float(sg[field]) - only[field]) > 1e-9:
                            rep.block("subgroup-recompute",
                                      f"outcome {oid!r}: subgroup {sg.get('id')!r} "
                                      f"names one trial and shows {field}={sg[field]}, "
                                      f"but that trial's own {field} is "
                                      f"{only[field]}. A stratum of one is its "
                                      f"member, not an independent number.")
                continue
            outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
            if effects:
                got = pool_generic(effects,
                                   res.get("estimator_used", "DerSimonian-Laird"),
                                   sg.get("ci_level", 95),
                                   log_scale=outcome["measure"] not in ("MD", "SMD"))
            else:
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
                              f"{sg[field]} but pooling the {n_contrib} trials it names "
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


# A row of a review's summary-of-findings table, as (efficacy, lo, hi, n).
# Both gate families broke the bag-of-numbers check the same way: a value was
# accepted because it occurred SOMEWHERE in 1.5M characters, so 91.1 could be
# replaced by 95.1 -- its own CI upper bound -- or by another vaccine's figure
# entirely, and the CI bounds could be swapped end for end. Presence is not
# identity. A figure has to be found as the row it claims to be.
_REVIEW_ROWS: dict = {}

# The review prints "VE 91.10 (83.80 to 95.10) 18,695 (1 RCT)" in its tables and
# "VE 91.10%, 95% CI 83.80% to 95.10%; 1 RCT, 18,695 participants" in its prose.
# Both forms are read; a figure need only be found in one of them.
_ROW_PATTERNS = (
    re.compile(r"VE\s*([\d.]+)\s*\(\s*([\d.]+)\s+to\s+([\d.]+)\s*\)\s*([\d,]+)?", re.I),
    re.compile(r"VE[:\s]*([\d.]+)%?,?\s*95%\s*CI\s*([\d.]+)%?\s*to\s*([\d.]+)%?"
               r"(?:;\s*\d+\s*RCTs?,?\s*([\d,]+))?", re.I),
    re.compile(r"([\d.]+)%,\s*95%\s*CI\s*([\d.]+)%\s*to\s*([\d.]+)%;"
               r"\s*\d+\s*RCTs?,\s*([\d,]+)", re.I),
)


def _f(tok):
    try:
        return float(str(tok).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _review_rows(path, section=None):
    """Rows found in a staged review payload, optionally within one section.

    `section` is a slice of the staged EXTRACT keyed to one trial, which is what
    makes this per-vaccine rather than per-document: without it, one vaccine's
    figures satisfy another vaccine's row, which is a substitution a reviewer
    executed against the previous version of this check.
    """
    key = (str(path), section is not None and hash(section))
    if key not in _REVIEW_ROWS:
        text = section if section is not None else path.read_text(
            encoding="utf-8", errors="replace")
        text = _norm_numbers(text.replace("‐", "-").replace(" ", " "))
        rows = set()
        for pat in _ROW_PATTERNS:
            for m in pat.finditer(text):
                eff, lo, hi, n = (_f(m.group(1)), _f(m.group(2)),
                                  _f(m.group(3)), _f(m.group(4)))
                if None not in (eff, lo, hi):
                    rows.add((eff, lo, hi, n))
        _REVIEW_ROWS[key] = rows
    return _REVIEW_ROWS[key]


def _extract_section(path, nct):
    """The block of a staged extract that belongs to one registration.

    The extract is written with '###' headers carrying the NCT id, precisely so
    a figure can be tied to the vaccine it belongs to.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    blocks = re.split(r"\n###\s", text)
    for b in blocks:
        if nct and nct in b.split("\n", 1)[0]:
            return b
    return None


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
            # IDENTITY, not presence. The triple must be found as ONE ROW of the
            # review -- efficacy, then its own two CI bounds in that order -- and
            # where a staged extract exists, inside the block belonging to THIS
            # registration. Presence-anywhere let 91.1 be replaced by its own CI
            # bound 95.1, let the two bounds be swapped end for end, and let one
            # vaccine's figures stand in for another's. All three were executed
            # against the previous version of this check and all three passed.
            lo, hi = r.get("reference_ci_low_percent"), r.get("reference_ci_high_percent")
            section = None
            extract = src.get("staged_extract")
            if extract and (root / extract).is_file():
                section = _extract_section(root / extract, r.get("nct") or "")
                if section is None:
                    rep.block("reference-unlocated",
                              f"outcome {oid!r}/{r['trial_id']}: the staged extract "
                              f"{extract} has no block for {r.get('nct')!r}, so this row's "
                              f"published figure cannot be tied to this registration.")
                    continue
            rows = _review_rows(path, section)
            if lo is None or hi is None:
                nums = _review_numbers(path)
                if not any(abs(float(ref) - x) < 1e-9 for x in nums):
                    rep.block("reference-unsupported",
                              f"outcome {oid!r}/{r['trial_id']}: "
                              f"reference_efficacy_percent={ref} does not appear in "
                              f"{staged_as}.")
            elif not any(abs(ref - a) < 1e-9 and abs(lo - b) < 1e-9 and abs(hi - c) < 1e-9
                         for a, b, c, _n in rows):
                where = f"the {r.get('nct')} block of {extract}" if section else staged_as
                rep.block("reference-row-unmatched",
                          f"outcome {oid!r}/{r['trial_id']}: the published figure "
                          f"{ref} ({lo} to {hi}) is not reported as a row in {where}. "
                          f"Every one of those three numbers may occur in the review "
                          f"separately -- a CI bound reused as a point estimate, or two "
                          f"bounds swapped, still finds each of them. The row is what "
                          f"identifies the figure.")
            # The review's own analysis population belongs to the row it was read
            # from. Left unbound it moved freely: 18695 -> 18696 and 18695 ->
            # 25062, another vaccine's population, both passed.
            pop = r.get("reference_analysis_population")
            if pop is not None and lo is not None and hi is not None:
                match = [n for a, b, c, n in rows
                         if abs(ref - a) < 1e-9 and abs(lo - b) < 1e-9
                         and abs(hi - c) < 1e-9 and n is not None]
                if match and not any(abs(float(pop) - n) < 1e-9 for n in match):
                    rep.block("reference-population-mismatch",
                              f"outcome {oid!r}/{r['trial_id']}: "
                              f"reference_analysis_population={pop}, but the review row "
                              f"carrying {ref} ({lo} to {hi}) reports "
                              f"{'/'.join(str(int(n)) for n in match)}. The population "
                              f"belongs to the row the figure came from.")
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


def check_identifier_anchoring(canon, rep, sources_root=None):
    """An identifier must BE the record it names, not merely look like one.

    A reviewer changed a trial's pmid to 99999999 and its nct to NCT00000000 and
    the validator returned clean, because nothing ever compared the object's
    identifier fields with the identity of the payload staged beside them. Both
    are reader-visible -- the page prints the NCT under every trial name -- and
    both are the key every other source check is scoped by, so a wrong one
    silently redirects the whole verification.
    """
    root = pathlib.Path(sources_root or "sources") / canon["app_id"]
    if not root.is_dir():
        return
    for t in canon["inputs"]["trials"]:
        nct = t.get("nct")
        if nct:
            f = root / f"{nct}.ctgov.json"
            if not f.is_file():
                rep.block("identifier-unstaged",
                          f"{t['id']} cites {nct} but no {nct}.ctgov.json is staged, so "
                          f"the registration cannot be confirmed to exist or to be this "
                          f"trial.")
            else:
                try:
                    got = (json.loads(f.read_text(encoding="utf-8"))["protocolSection"]
                           ["identificationModule"]["nctId"])
                except Exception as exc:
                    got = None
                    rep.block("identifier-unreadable",
                              f"{t['id']}: cannot read nctId from {f.name}: {exc}")
                if got is not None and got != nct:
                    rep.block("identifier-mismatch",
                              f"{t['id']} declares nct={nct} but the payload staged under "
                              f"that name identifies itself as {got}.")
        pmid = t.get("pmid")
        if pmid:
            f = root / f"PMID{pmid}.pubmed.xml"
            if not f.is_file():
                rep.block("identifier-unstaged",
                          f"{t['id']} cites PMID {pmid} but no PMID{pmid}.pubmed.xml is "
                          f"staged. The publication a cell is read from must be the "
                          f"publication the object names.")
            else:
                raw = f.read_text(encoding="utf-8", errors="replace")
                if not re.search(r"<PMID[^>]*>\s*" + re.escape(str(pmid)) + r"\s*</PMID>", raw):
                    rep.block("identifier-mismatch",
                              f"{t['id']} declares pmid={pmid} but the payload staged "
                              f"under that name does not carry that PMID.")
    # The per_trial row prints its own nct beside the estimate a reader reads.
    by_id = {t["id"]: t for t in canon["inputs"]["trials"]}
    for oid, res in canon["results"]["by_outcome"].items():
        for r in res.get("per_trial") or []:
            t = by_id.get(r.get("trial_id"))
            if t and r.get("nct") and r["nct"] != t.get("nct"):
                rep.block("identifier-mismatch",
                          f"outcome {oid!r}/{r['trial_id']}: the result row shows "
                          f"nct={r['nct']} while the trial it names is {t.get('nct')}.")


def check_per_trial_source_fields(canon, rep, sources_root=None):
    """Reader-visible per-row numbers that are neither counts nor estimates.

    A row can carry figures that no other detector owns: what the trial itself
    reported in its own units, and the population its crude counts rest on. A
    reviewer moved 9.8 to 99.8 and it passed. These are printed on the row.
    """
    root = pathlib.Path(sources_root or "sources") / canon["app_id"]
    blobs = {}
    if root.is_dir():
        for f in root.glob("*"):
            if f.suffix in (".json", ".xml", ".txt"):
                blobs[f.name] = _norm_numbers(f.read_text(encoding="utf-8", errors="replace"))
    by_id = {t["id"]: t for t in canon["inputs"]["trials"]}
    for oid, res in canon["results"]["by_outcome"].items():
        for r in res.get("per_trial") or []:
            t = by_id.get(r.get("trial_id")) or {}
            nct = t.get("nct", "")
            for key, val in r.items():
                if not key.startswith("trial_reported_rate_") or not isinstance(val, (int, float)):
                    continue
                if not blobs:
                    rep.block("sources-unavailable",
                              f"outcome {oid!r}/{r['trial_id']}: {key}={val} is attributed "
                              f"to the trial's own report but no payload is staged.")
                    continue
                hit = any(str(val) in b for n, b in blobs.items() if nct and nct in n) or \
                      any(str(val) in b for n, b in blobs.items()
                          if t.get("pmid") and str(t["pmid"]) in n)
                if not hit:
                    rep.block("source-unsupported",
                              f"outcome {oid!r}/{r['trial_id']}: {key}={val} is presented "
                              f"as what the trial itself reports, but does not appear in "
                              f"any payload staged for {nct or r['trial_id']}.")
            # A population the object says its own counts rest on is DERIVED from
            # those counts. It was stored free-standing and checked by nothing.
            pop = r.get("crude_analysis_population")
            d = (t.get("by_outcome") or {}).get(oid) or {}
            tx, ct = d.get("treatment") or {}, d.get("control") or {}
            if pop is not None and tx.get("n") is not None and ct.get("n") is not None:
                want = int(tx["n"]) + int(ct["n"])
                if int(pop) != want:
                    rep.block("crude-population-mismatch",
                              f"outcome {oid!r}/{r['trial_id']}: "
                              f"crude_analysis_population={pop}, but the arms this row's "
                              f"ratio is computed from hold {tx['n']} + {ct['n']} = {want}.")


def check_removal_grounds(canon, rep, sources_root=None):
    """A stated removal reason must be the reason the staged registration shows.

    check_removal_disclosure counts removals and requires each category to carry
    a detail. A reviewer showed that is bookkeeping, not verification: refile the
    HPV video-game trial from 'wrong disease area' to 'per-arm counts not
    verifiable', rewrite its detail to match, and everything still passed --
    while the registration staged beside it is plainly not a COVID-19 trial. The
    reader sees the reason, so the reason is checked.

    The disease vocabulary is taken from the RETAINED trials rather than
    hardcoded, so this travels to any app: whatever the retained registrations
    are about is what a removed one is measured against.
    """
    rm = canon.get("removed_citations")
    if not rm:
        return
    root = pathlib.Path(sources_root or "sources") / canon["app_id"]
    if not root.is_dir():
        return

    def payload(nct):
        for p in (root / f"{nct}.ctgov.json", root / "removed" / f"{nct}.ctgov.json"):
            if p.is_file():
                return p
        return None

    def words(nct):
        p = payload(nct)
        if p is None:
            return None
        try:
            ps = json.loads(p.read_text(encoding="utf-8"))["protocolSection"]
        except Exception:
            return None
        text = " ".join([ps.get("identificationModule", {}).get("briefTitle", "") or "",
                         ps.get("identificationModule", {}).get("officialTitle", "") or "",
                         " ".join(ps.get("conditionsModule", {}).get("conditions") or [])])
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    STOP = {"a", "an", "the", "of", "in", "to", "and", "study", "trial", "clinical",
            "phase", "safety", "efficacy", "immunogenicity", "randomized", "randomised",
            "placebo", "controlled", "participants", "adults", "vaccine", "vaccines",
            "vaccination", "evaluate", "candidate", "healthy", "subjects", "prevention",
            "double", "blind", "multicenter", "with", "for", "against", "dose", "doses"}
    domain = set()
    for t in canon["inputs"]["trials"]:
        w = words(t.get("nct", ""))
        if w:
            domain |= (w - STOP)
    if not domain:
        return
    for c in rm.get("categories") or []:
        reason = str(c.get("reason", "")).lower()
        for nct in c.get("removed_ids") or []:
            w = words(nct)
            if w is None:
                continue
            shared = (w - STOP) & domain
            off_topic = not shared
            if off_topic and "disease" not in reason:
                rep.block("removal-reason-wrong",
                          f"{nct} is filed under {c.get('reason')!r}, but the staged "
                          f"registration shares no disease vocabulary with the retained "
                          f"trials of this object, which is the signature of a "
                          f"wrong-disease citation rather than an unsourceable one. "
                          f"Refiling it must not be a way to soften what it was.")
            if not off_topic and "disease" in reason:
                rep.block("removal-reason-wrong",
                          f"{nct} is filed under {c.get('reason')!r}, but the staged "
                          f"registration shares disease vocabulary "
                          f"({sorted(shared)[:4]}) with the retained trials, so it is not "
                          f"off-topic. A removal reason is a claim about the record.")


def check_quoted_group_disclosure(canon, rep):
    """A trial group named in the object's OWN quoted source must be accounted for.

    Deleting BBIBP's shared_control_note -- the disclosure that the trial ran
    THREE groups against one shared alum control -- passed every detector,
    because the arm rules read either the object's declared arms (which no
    longer mentioned the third group) or a posted registry outcome (which
    abstract-sourced cells do not have).

    The anchor that does exist for those cells is the quoted sentence itself,
    which check_against_sources has already proved appears verbatim in a staged
    payload. If that sentence names a group, the object cannot silently not have
    it. Generic words are excluded: "the vaccine group" and "the placebo group"
    name a role, not a distinct arm.
    """
    GENERIC = {"vaccine", "placebo", "control", "treatment", "intervention", "study",
               "each", "both", "the", "this", "that", "same", "other", "either",
               "active", "comparator", "first", "second", "third", "per", "protocol"}
    for t in canon["inputs"]["trials"]:
        declared = " ".join([str(a.get("label", "")) for a in t.get("arms", [])]
                            + [str(x) for x in (t.get("arms_not_used") or [])]).lower()
        disclosed = " ".join(str(v) for k, v in t.items()
                             if k.endswith("_note") and isinstance(v, str)).lower()
        for oid, d in t.get("by_outcome", {}).items():
            for q in ((d.get("provenance") or {}).get("source_quotes") or []):
                for name in re.findall(r"([A-Za-z0-9][A-Za-z0-9\-]{1,20})\s+group\b", str(q)):
                    low = name.lower()
                    if low in GENERIC or low.isdigit():
                        continue
                    if low in declared or low in disclosed:
                        continue
                    rep.block("quoted-group-undisclosed",
                              f"{t['id']}/{oid}: the source sentence this object quotes "
                              f"names a {name!r} group, which the object neither declares "
                              f"as an arm, lists in arms_not_used, nor mentions in any "
                              f"note. A group the object's own evidence names cannot be "
                              f"absent from the object without a word.")


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
            if any(ty in want for ty in hits):
                continue
            # HEAD-TO-HEAD. When neither arm is inactive, BOTH are posted as
            # active comparators and the registry's label records which arm the
            # sponsor registered as the reference -- not which arm the published
            # contrast runs from. Refusing every such object would make a
            # vaccine-versus-chemoprevention trial unrepresentable; accepting it
            # silently would reopen the arm-swap this detector exists to close.
            # So the exemption is narrow and must be DECLARED: the trial says its
            # comparator is active, and the arm carries a note saying which way
            # its published effect runs. A swap then has to be written down to
            # pass, which is what makes it visible.
            if (role == "treatment" and t.get("comparator_type") == "active"
                    and all(ty == "ACTIVE_COMPARATOR" for ty in hits)
                    and str(a.get("head_to_head_role_note", "")).strip()):
                continue
            rep.block("arm-role-vs-registry",
                      f"{t['id']}: arm {lab!r} is declared {role!r} but the registry "
                      f"posts it as {hits!r}. A role is not a matter of opinion when "
                      f"the source records what the arm was.")


SURVIVAL_FAMILIES = {"time_to_first", "recurrent_rate", "first_episode_rate"}
# Measures whose value does not identify the quantity: a hazard ratio and an
# incidence-rate ratio each require the estimand to be named before they mean
# anything, because one trial publishes several of them for one endpoint.
RATE_MEASURES = {"HR", "IRR"}


def check_estimand_storage_form(canon, rep):
    """A survival or rate endpoint may NOT be stored as a table of participants.

    This is the defect the malaria object was rebuilt to remove, and it is the
    one a validator that only checks arithmetic cannot see. The RTS,S phase 3
    analysed ALL clinical malaria episodes by negative binomial regression with
    person-time as the offset: its published counts are EPISODES and exceed the
    number of participants, so a two-by-two built from them has a numerator that
    cannot sit over its denominator. The R21 trials analysed the TIME to a first
    episode by Cox regression. Neither is a proportion of participants, and the
    earlier corpus record stored both as binary counts.

    Nothing downstream can recover from this: pooling counts gives a risk ratio,
    which is a different quantity from a hazard ratio or a rate ratio, and the
    result looks perfectly well-formed. So the storage form is constrained at
    the point where it is declared.
    """
    fam = {o["id"]: (o.get("estimand") or {}).get("family") for o in canon["outcomes"]}
    for t in canon["inputs"]["trials"]:
        for oid, d in (t.get("by_outcome") or {}).items():
            if fam.get(oid) not in SURVIVAL_FAMILIES:
                continue
            for role in ("treatment", "control"):
                arm = d.get(role)
                if isinstance(arm, dict) and arm.get("events") is not None:
                    rep.block("estimand-storage-form",
                              f"{t['id']}/{oid}: the outcome declares estimand family "
                              f"{fam[oid]!r}, which is a time-to-event or rate "
                              f"quantity, but this row stores a participant count "
                              f"under {role!r}. Pooling counts would produce a risk "
                              f"ratio and present it as the ratio the trial actually "
                              f"estimated. Binary counts belong in "
                              f"binary_supplementary, never in the pooled path.")
            if not d.get("effect"):
                rep.block("estimand-storage-form",
                          f"{t['id']}/{oid}: family {fam[oid]!r} requires a published "
                          f"effect estimate with its interval, because the variance "
                          f"of a hazard or rate ratio cannot be reconstructed from "
                          f"anything else this object holds.")


def check_estimand_homogeneity(canon, rep):
    """One pool, one estimand. Every contributing row must name the same one.

    Mixing a hazard ratio for the time to a first episode with a rate ratio for
    all episodes, or mixing two follow-up windows, yields a weighted average of
    quantities that answer different questions. It recomputes perfectly, which is
    exactly why arithmetic checking cannot catch it.
    """
    for oid, res in canon["results"]["by_outcome"].items():
        outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
        want = (outcome.get("estimand") or {}).get("id")
        if not want:
            # SCOPED, deliberately. A risk ratio or a mean difference on a
            # participant-level outcome is already pinned by its case definition
            # and its timepoint, and three objects that shipped before this rule
            # existed are correct without an estimand block. Requiring one from
            # them would be a retroactive block with nothing wrong behind it.
            # A ratio of RATES is different: the same trial routinely publishes
            # a time-to-first and an all-episode version of one endpoint, over
            # several windows, and those numbers are interchangeable to look at
            # and not interchangeable to pool. There the declaration is required.
            if outcome.get("measure") in RATE_MEASURES:
                rep.block("estimand-undeclared",
                          f"outcome {oid!r} reports a {outcome.get('measure')} but "
                          f"declares no estimand id. A ratio of rates is ambiguous "
                          f"between the time to a first event and the rate of all "
                          f"events, over any of several windows, so nothing here "
                          f"could establish that the rows pooled under it measure "
                          f"one thing.")
            continue
        if res.get("estimand_id") != want:
            rep.block("estimand-homogeneity",
                      f"outcome {oid!r}: the result block names estimand "
                      f"{res.get('estimand_id')!r} while the outcome declares "
                      f"{want!r}.")
        for t in canon["inputs"]["trials"]:
            d = (t.get("by_outcome") or {}).get(oid)
            if not d:
                continue
            got = d.get("estimand_id")
            if got != want:
                rep.block("estimand-homogeneity",
                          f"{t['id']}/{oid}: this row names estimand {got!r} but "
                          f"contributes to an outcome whose estimand is {want!r}. A "
                          f"pool of two estimands is a weighted average of two "
                          f"different questions.")
        for r in res.get("per_trial") or []:
            if r.get("estimand_id") != want:
                rep.block("estimand-homogeneity",
                          f"outcome {oid!r}/{r.get('trial_id')}: the rendered row "
                          f"names estimand {r.get('estimand_id')!r}, not {want!r}.")


def check_shared_control_double_count(canon, rep):
    """No two rows in one pool may lean on the same control participants.

    Both pivotal programmes randomised MORE THAN ONE vaccinated group against a
    single control group: two adjuvant doses against one rabies group, and a
    boosted and an unboosted schedule against one comparator group. Each
    published contrast is valid on its own. Using two of them in one pooled
    estimate counts those control participants, and their events, twice --
    which narrows the interval by borrowing precision that does not exist.
    """
    for oid, res in canon["results"]["by_outcome"].items():
        seen = {}
        for t in canon["inputs"]["trials"]:
            d = (t.get("by_outcome") or {}).get(oid)
            if not (d and d.get("effect")):
                continue
            key = d.get("control_arm_key")
            if not key:
                # Required where sharing is POSSIBLE, which is where the trial
                # randomised more than one treatment arm. A two-arm trial has one
                # control serving one contrast, and demanding a key from it would
                # be bookkeeping with no failure mode behind it -- it would also
                # retroactively block objects that shipped correct before this
                # rule existed. A multi-arm trial is the case where two published
                # contrasts lean on the same control participants, so there the
                # key is the thing that makes the collision detectable.
                n_treat = sum(1 for a in t.get("arms", [])
                              if a.get("role") == "treatment")
                if n_treat > 1:
                    rep.block("shared-control-unkeyed",
                              f"{t['id']}/{oid} contributes to a pool from a trial "
                              f"with {n_treat} treatment arms, but names no "
                              f"control_arm_key. Where one control group serves "
                              f"several published contrasts, nothing else can "
                              f"establish that only one of them was used.")
                continue
            if key in seen:
                rep.block("shared-control-double-count",
                          f"outcome {oid!r}: {t['id']} and {seen[key]} both "
                          f"contribute and both name control group {key!r}. One "
                          f"control group cannot serve two rows of the same pool; "
                          f"choose one contrast and carry the other outside it.")
            seen[key] = t["id"]
        # Every contrast the object deliberately set aside must say which control
        # it shared, or the disclosure is decorative.
        for c in canon.get("carried_contrasts") or []:
            if not str(c.get("excluded_from_pool_because", "")).strip():
                rep.block("carried-contrast-unexplained",
                          f"a carried contrast on {c.get('trial_id')!r} gives no "
                          f"reason for being outside every pool. A contrast that is "
                          f"shown but not pooled must say why, or a reader cannot "
                          f"tell exclusion from oversight.")


def check_regimen_homogeneity(canon, rep):
    """A non-exploratory pool may not silently mix regimens.

    Seasonal administration and age-based administration are different
    interventions, and the phase 3 trial registered them as SEPARATE co-primary
    endpoints. Averaging them reports a schedule nobody used. Where a collapse is
    legitimate it must be the trial's own, declared and anchored.
    """
    for oid, res in canon["results"]["by_outcome"].items():
        outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
        if outcome.get("type") == "exploratory" or not res.get("pooled"):
            continue
        regs = {r.get("regimen") for r in (res.get("per_trial") or [])}
        if len(regs) > 1:
            rep.block("regimen-mixed",
                      f"outcome {oid!r} pools rows administered under different "
                      f"regimens ({sorted(str(x) for x in regs)}). A pooled value "
                      f"across schedules describes a schedule no participant "
                      f"received.")
        for sg in res.get("subgroups") or []:
            if sg.get("regimen_collapse_prespecified") and not \
                    str(sg.get("regimen_collapse_reason", "")).strip():
                rep.block("regimen-collapse-unexplained",
                          f"outcome {oid!r}: subgroup {sg.get('id')!r} declares a "
                          f"prespecified regimen collapse with no reason given.")


def check_log_effect_consistency(canon, rep):
    """A stored log effect must BE the log of the effect stored beside it.

    The object stores both, because the pooling happens on the log scale and a
    reader sees the ratio. Two representations of one quantity can disagree, and
    a validator that reads only one of them would never know which is rendered.
    """
    for t in canon["inputs"]["trials"]:
        for oid, d in (t.get("by_outcome") or {}).items():
            e = d.get("effect")
            if not e or e.get("scale") != "log":
                continue
            if not (e["ci_low"] > 0 and e["point"] > 0 and e["ci_high"] > 0):
                rep.block("log-effect-domain",
                          f"{t['id']}/{oid}: a ratio measure stored on the log scale "
                          f"must be strictly positive; got "
                          f"({e['ci_low']}, {e['point']}, {e['ci_high']}).")
                continue
            z = Z.get(e.get("ci_level"))
            if z is None:
                continue
            want_pt = math.log(e["point"])
            want_se = (math.log(e["ci_high"]) - math.log(e["ci_low"])) / (2 * z)
            if "log_point" in e and abs(e["log_point"] - want_pt) > 5e-6:
                rep.block("log-effect-inconsistent",
                          f"{t['id']}/{oid}: log_point={e['log_point']} but the log "
                          f"of the stored point {e['point']} is {want_pt:.6f}.")
            if "log_se" in e and abs(e["log_se"] - want_se) > 5e-6:
                rep.block("log-effect-inconsistent",
                          f"{t['id']}/{oid}: log_se={e['log_se']} but the stored "
                          f"interval at its stated confidence level implies "
                          f"{want_se:.6f}. The standard error is what the pooling "
                          f"weights are built from, so a wrong one moves the pooled "
                          f"value without moving anything a reader can see.")


def check_ve_consistency(canon, rep):
    """Every efficacy percentage a reader sees must be the effect it sits beside.

    Efficacy is the presentation; the ratio is the stored quantity. They are two
    views of one number and the page shows the percentage, so an efficacy that
    drifted from its ratio would be a wrong headline over a right analysis.
    """
    def check(where, pct, ratio_val):
        if pct is None or ratio_val is None:
            return
        want = 100 * (1 - ratio_val)
        if abs(pct - want) > 0.01:
            rep.block("ve-inconsistent",
                      f"{where}: an efficacy of {pct} is shown beside a ratio of "
                      f"{ratio_val}, which is an efficacy of {want:.4f}.")

    # A head-to-head ratio is NOT a vaccine efficacy, and one minus it is not
    # one either. The trial that forced this compared the vaccine against an
    # active chemoprevention regimen, so its hazard ratio near the null means
    # the two interventions performed alike -- not that the vaccine barely
    # works. Relabelling that row as an efficacy passed every other detector,
    # because the arithmetic of one-minus-a-ratio is the same whatever the
    # comparator was. The comparator is what makes it meaningless, so the
    # comparator is what this reads.
    for o in canon["outcomes"]:
        if o.get("comparator_type") != "active":
            continue
        oid = o["id"]
        for t in canon["inputs"]["trials"]:
            d = (t.get("by_outcome") or {}).get(oid) or {}
            e = d.get("effect") or {}
            if e.get("published_ve_percent") is not None or \
                    e.get("derived_from") == "published_vaccine_efficacy_percent":
                rep.block("efficacy-against-active-comparator",
                          f"{t['id']}/{oid} carries a vaccine efficacy, but this "
                          f"outcome declares an ACTIVE comparator "
                          f"({o.get('comparator')!r}). An efficacy is a contrast "
                          f"against an unprotected control; against an effective "
                          f"comparator, one minus the ratio reports a vaccine that "
                          f"barely works when what the trial showed was two "
                          f"interventions performing alike.")
        res = canon["results"]["by_outcome"].get(oid) or {}
        for r in res.get("per_trial") or []:
            if r.get("published_ve_percent") is not None:
                rep.block("efficacy-against-active-comparator",
                          f"outcome {oid!r}/{r.get('trial_id')}: the rendered row "
                          f"shows a vaccine efficacy against an active comparator.")
        if (res.get("pooled") or {}).get("pooled_ve_percent") is not None:
            rep.block("efficacy-against-active-comparator",
                      f"outcome {oid!r}: a pooled vaccine efficacy is reported "
                      f"against an active comparator.")

    for oid, res in canon["results"]["by_outcome"].items():
        p = res.get("pooled")
        if p:
            check(f"outcome {oid!r} pooled", p.get("pooled_ve_percent"), p.get("point"))
            check(f"outcome {oid!r} pooled lower",
                  p.get("pooled_ve_ci_low_percent"), p.get("ci_high"))
            check(f"outcome {oid!r} pooled upper",
                  p.get("pooled_ve_ci_high_percent"), p.get("ci_low"))
        for sg in res.get("subgroups") or []:
            check(f"outcome {oid!r} subgroup {sg.get('id')!r}",
                  sg.get("ve_percent"), sg.get("point"))
        for r in res.get("per_trial") or []:
            check(f"outcome {oid!r}/{r.get('trial_id')}",
                  r.get("published_ve_percent"), r.get("point"))


def check_analysed_scope(canon, rep):
    """A denominator that is not the contrast's own must say so.

    The R21 phase 3 publishes its analysed population only for the whole trial,
    while reporting two co-primary strata. Printing the whole-trial denominator
    on a stratum row without a word would tell a reader that stratum was the
    size of the trial. Omitting it instead would leave the row unweighable. So
    the figure is carried at the level the source reports it, and the level is
    declared and rendered.
    """
    measure = {o["id"]: o.get("measure") for o in canon["outcomes"]}
    for t in canon["inputs"]["trials"]:
        for oid, d in (t.get("by_outcome") or {}).items():
            if not d.get("effect"):
                continue
            sizes = d.get("analysed") or {}
            if not sizes:
                continue
            # Scoped for the same reason as the estimand declaration above: on a
            # rate measure a row's denominator is routinely published only at a
            # level coarser than the contrast, and the gap between the two is
            # invisible unless it is written down.
            if measure.get(oid) not in RATE_MEASURES:
                continue
            if not str(d.get("analysed_scope", "")).strip():
                rep.block("analysed-scope-undeclared",
                          f"{t['id']}/{oid} carries analysed denominators but does "
                          f"not say what population they describe. A denominator "
                          f"whose scope is unstated is read as the row's own.")
            for role, n in sizes.items():
                if not isinstance(n, (int, float)) or n <= 0:
                    rep.block("analysed-invalid",
                              f"{t['id']}/{oid}: analysed.{role}={n} is not a "
                              f"positive count.")
                elif t.get("enrolled") and n > t["enrolled"]:
                    rep.block("analysed-exceeds-enrolled",
                              f"{t['id']}/{oid}: analysed.{role}={n} exceeds the "
                              f"{t['enrolled']} recorded as enrolled.")


def check_pool_uniformity(canon, rep):
    """A pool may not CLAIM to hold constant what it records as varying.

    Both gate families found the same thing in the same round: a result block
    saying "the same estimand over the same window" while the outcome's own
    estimand block, three fields away, said the windows were not the same
    length. Neither statement was wrong about the world; they were wrong about
    each other. The boilerplate had been written when it was true and stayed put
    when a later commit made it false.

    Nothing structural could catch that, because "same window" was free text.
    So the uniformity of a pool becomes DATA -- one entry per dimension, each
    either identical or differing, and a differing one carrying the reason it is
    crossed anyway -- and the prose is generated from it. This detector enforces
    that the data exists, that every crossed dimension is justified, and that the
    prose does not assert sameness on a dimension recorded as differing.
    """
    # A phrase that asserts uniformity, mapped to the dimension it asserts it
    # about. Deliberately short and literal: this is a guard against boilerplate
    # drifting out of step with data, not a natural-language checker.
    CLAIMS = {
        "follow_up_window": ("same window", "same follow-up", "common window",
                             "same follow up"),
        "regression_model": ("same model", "same regression"),
        "analysis_population": ("same population",),
        "age_range": ("same age", "same population band"),
        "case_definition": ("same case definition",),
        "estimand_family": ("same estimand",),
        "comparator": ("same comparator",),
    }
    for oid, res in canon["results"]["by_outcome"].items():
        if not res.get("pooled"):
            continue
        u = res.get("pool_uniformity")
        if not u:
            # Required of objects in the estimand regime, which is where a pool
            # can cross a dimension invisibly. An object that predates the
            # regime is left alone rather than blocked for lacking a field that
            # did not exist when it shipped -- the same scoping the estimand and
            # analysed-scope rules already use.
            outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
            if outcome.get("estimand"):
                rep.block("pool-uniformity-undeclared",
                          f"outcome {oid!r} declares an estimand and publishes a "
                          f"pooled estimate, but records nothing about WHAT its "
                          f"contributing cohorts hold constant. Without that, any "
                          f"sentence describing the pool is unfalsifiable and can "
                          f"go stale against the object silently.")
            continue
        # Scan EVERY reader-visible description of the pool, not just the one
        # the generator writes. A reviewer found a stale "the comparator is
        # identical" surviving in the outcome's definition_note after the
        # uniformity table had recorded the comparator as differing -- the
        # contradiction detector was pointed at poolable_reason alone and could
        # not see it. A rule that checks one of the several places a claim can
        # live is a rule that relocates the defect.
        outcome_for_scan = next(o for o in canon["outcomes"] if o["id"] == oid)
        reason = " ".join(str(x).lower() for x in (
            res.get("poolable_reason", ""),
            res.get("heterogeneity_status", ""),
            res.get("interpretation_caveat", ""),
            outcome_for_scan.get("definition_note", ""),
            outcome_for_scan.get("definition", ""),
            (res.get("handbook") or {}).get("decision", ""),
            (res.get("handbook") or {}).get("conformance", ""),
        ))
        for dim, entry in u.items():
            state = entry[0] if isinstance(entry, (list, tuple)) else entry.get("state")
            note = (entry[1] if isinstance(entry, (list, tuple))
                    else entry.get("note", ""))
            if state not in ("identical", "differs", "not applicable"):
                rep.block("pool-uniformity-state",
                          f"outcome {oid!r}: dimension {dim!r} records state "
                          f"{state!r}, which is not one this rule understands.")
                continue
            if state != "differs":
                continue
            if not str(note).strip():
                rep.block("pool-uniformity-unjustified",
                          f"outcome {oid!r}: dimension {dim!r} differs across the "
                          f"cohorts being pooled and no reason is given for pooling "
                          f"across it. Crossing a dimension is allowed; crossing it "
                          f"silently is what this rule exists to stop.")
            for phrase in CLAIMS.get(dim, ()):
                if phrase in reason:
                    rep.block("pool-uniformity-contradiction",
                              f"outcome {oid!r}: the pooled result's own "
                              f"description says {phrase!r} while this object "
                              f"records {dim!r} as DIFFERING across the cohorts it "
                              f"pools. One of the two is wrong about the other, and "
                              f"a reader sees the sentence.")


def check_handbook_citation(canon, rep):
    """Every pooling or scope decision names the section that governs it.

    STANDING RULE, from 2026-08-08: methodological decisions about pooling,
    scope, estimand, heterogeneity and unit of analysis are settled against the
    latest Cochrane Handbook, and the object records which section settled each.

    The rule exists because this object twice lost an argument to a rule it had
    invented itself. Once the invented rule was too STRICT -- "never mix
    follow-up windows" would have discarded a pool the Handbook permits, of two
    cohorts agreeing to three thousandths. Once it was self-CONTRADICTORY -- the
    stated question and the actual practice disagreed, and both review families
    found it. A cited section cannot be argued with in either direction; it can
    only be checked.

    WHAT THIS DETECTOR DOES AND DOES NOT DO. It checks that the citation EXISTS,
    that it names sections in a plausible form, and that it carries a conformance
    statement. It does NOT and cannot decide whether the decision genuinely
    follows from the section it cites -- that is a judgement about a document
    this validator has not read, and it is what the two independent review
    families are for. This records and checks; it never adjudicates.
    """
    ma = canon.get("methodological_authority")
    outcomes = {o["id"]: o for o in canon["outcomes"]}
    # Only objects that have opted into the regime are held to it, on the same
    # scoping principle as the estimand rules: an object that shipped before the
    # standing rule is not retroactively in breach of it.
    if not ma:
        if any(o.get("estimand") for o in canon["outcomes"]):
            rep.block("handbook-authority-undeclared",
                      "this object declares estimands but names no methodological "
                      "authority. Under the standing rule every pooling and scope "
                      "decision is settled against the latest Cochrane Handbook "
                      "with the section recorded; an object with no authority "
                      "block is deciding by preference.")
        return
    for field in ("reference", "version", "sections_relied_on"):
        if not ma.get(field):
            rep.block("handbook-authority-incomplete",
                      f"the methodological authority block has no {field!r}. A "
                      f"citation missing its version cannot be checked against "
                      f"the document that was actually consulted.")
    for s in ma.get("sections_relied_on") or []:
        if not re.fullmatch(r"\d+(?:\.\d+)*", str(s.get("section", ""))):
            rep.block("handbook-section-malformed",
                      f"{s.get('section')!r} is not a section number.")
        if not str(s.get("used_for", "")).strip():
            rep.block("handbook-section-purposeless",
                      f"section {s.get('section')!r} is cited with no statement of "
                      f"what it settled. A citation that does not say what it is "
                      f"for cannot be checked against the decision it supports.")

    cited = {str(s.get("section")) for s in ma.get("sections_relied_on") or []}
    for oid, res in canon["results"]["by_outcome"].items():
        # EVERY result block, not only the pooled ones. The first version asked
        # for a citation where the object had POOLED or declined to pool, on the
        # reasoning that a single-cohort outcome makes no decision. A reviewer
        # read the object's own stated rule -- "every decision about pooling,
        # scope, estimand, heterogeneity or unit of analysis names the section
        # that governs it" -- against the object and found six result blocks
        # with none. The reviewer was right and the reasoning was wrong: a
        # single-cohort outcome still decides what MEASURE its estimate is, and
        # that is exactly the decision this whole object exists to get right.
        hb = res.get("handbook")
        if not hb:
            verb = ("pooling" if res.get("pooled")
                    else "declining to pool" if res.get("k", 0) >= 2
                    else "reporting a single cohort in a named effect measure")
            rep.block("handbook-citation-missing",
                      f"outcome {oid!r}: {verb} is a methodological decision and "
                      f"this object names no Handbook section governing it, while "
                      f"its own rule says every such decision names one.")
            continue
        for field in ("decision", "sections", "conformance"):
            if not hb.get(field):
                rep.block("handbook-citation-incomplete",
                          f"outcome {oid!r}: the Handbook decision record has no "
                          f"{field!r}.")
        for sec in hb.get("sections") or []:
            if str(sec) not in cited:
                rep.block("handbook-section-unregistered",
                          f"outcome {oid!r} cites section {sec!r}, which is not in "
                          f"the object's own list of sections relied on. A section "
                          f"invoked on a decision but absent from the register is "
                          f"a citation nobody has stated the meaning of.")


def check_network(canon, rep):
    """A network's claims about its own shape must follow from its edges.

    Added with the first network object. The claim that matters is whether an
    INDIRECT comparison is supportable, and that turns on whether the graph
    contains a closed loop -- the Handbook measures incoherence as a difference
    between direct and indirect estimates around one. A star of edges meeting at
    a single comparator has none, so consistency there is untestable rather than
    satisfied, and an object must not present it as satisfied.

    This checks the graph against the object's own count, not against a
    judgement: loops are recomputed from the edges.
    """
    net = canon.get("network")
    if not net:
        return
    ids = {t["id"] for t in net.get("treatments", [])}
    if not ids:
        rep.block("network-no-treatments",
                  "a network block declares no treatments.")
        return
    refs = [t["id"] for t in net["treatments"] if t.get("is_reference")]
    outcomes = {o["id"]: o for o in canon["outcomes"]}
    pairs, seen_edges = [], set()
    for e in net.get("edges", []):
        oid = e.get("outcome_id")
        o = outcomes.get(oid)
        if o is None:
            rep.block("network-edge-unknown-outcome",
                      f"network edge {e.get('comparison')!r} names outcome "
                      f"{oid!r}, which this object does not declare.")
            continue
        a, b = o.get("treatment_node"), o.get("comparator_node")
        if a not in ids or b not in ids:
            rep.block("network-edge-unknown-node",
                      f"network edge {e.get('comparison')!r} runs between "
                      f"{a!r} and {b!r}, and one of those is not a declared "
                      f"treatment.")
            continue
        key = frozenset((a, b))
        if key in seen_edges:
            rep.block("network-duplicate-edge",
                      f"two edges connect {a!r} and {b!r}; a comparison is one "
                      f"edge however many studies inform it.")
        seen_edges.add(key)
        pairs.append((a, b))
    # A DIRECT COMPARISON THE OBJECT COMPUTED CANNOT BE MISSING FROM THE GRAPH.
    #
    # An object held a third within-trial contrast between two of its own
    # declared nodes -- counts, point estimate, interval, the lot -- and left it
    # out of `edges`, then reported the loop count that omission produced. Every
    # check here passed, because they all read the edge list and the edge list
    # was self-consistent. The graph was simply not the graph the object's own
    # results described, and a reviewer caught what the validator could not.
    #
    # The anchor that does exist is the outcome set: an outcome naming two
    # declared nodes and carrying a per-trial estimate IS a direct comparison,
    # so it owes an edge. Outcomes whose nodes are not both in this network are
    # untouched -- that is how a second, separate synthesis lives in one object.
    for oid, o in outcomes.items():
        a, b = o.get("treatment_node"), o.get("comparator_node")
        if a not in ids or b not in ids or a is None or b is None:
            continue
        res = canon.get("results", {}).get("by_outcome", {}).get(oid) or {}
        if not (res.get("per_trial") or res.get("pooled")):
            continue
        if frozenset((a, b)) not in seen_edges:
            rep.block("network-missing-edge",
                      f"outcome {oid!r} compares {a!r} with {b!r}, both declared "
                      f"treatments of this network, and carries a result -- but "
                      f"no edge connects them. A direct comparison the object "
                      f"computed cannot be absent from the graph it reports, "
                      f"because the loop count is derived from that graph.")

    # Loops, recomputed. Edges = E, nodes touched = V, components = C; the
    # cyclomatic number E - V + C is the number of independent closed loops.
    nodes = {n for pr in pairs for n in pr}
    parent = {n: n for n in nodes}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps = len({find(n) for n in nodes}) if nodes else 0
    loops = len(pairs) - len(nodes) + comps if nodes else 0
    if net.get("closed_loops") != loops:
        rep.block("network-loops",
                  f"the network records closed_loops={net.get('closed_loops')} "
                  f"but its {len(pairs)} edge(s) over {len(nodes)} node(s) in "
                  f"{comps} component(s) contain {loops}. The count is derived "
                  f"from the graph, not declared about it.")
    # EXACTLY ONE REFERENCE PER COMPONENT. The old rule demanded one reference
    # for the whole network, which silently assumed the graph was connected: a
    # reference is the node others are expressed against, and nothing in a
    # second component can be expressed against a node in the first. Demanding
    # a single global reference on a disconnected graph forces an object to
    # nominate one arbitrarily and assert a comparison that does not exist.
    # Per-component is strictly tighter than the old rule on a connected graph,
    # where there is one component and the two rules coincide.
    if nodes:
        by_comp = {}
        for n in nodes:
            by_comp.setdefault(find(n), set()).add(n)
        for root, members in sorted(by_comp.items()):
            local = sorted(set(refs) & members)
            if len(local) != 1:
                rep.block("network-reference",
                          f"each connected component needs exactly one "
                          f"reference treatment; the component "
                          f"{sorted(members)} names {local}.")
    stray = sorted(set(refs) - nodes)
    if stray:
        rep.block("network-reference-unconnected",
                  f"{stray} are marked as reference treatments but no edge "
                  f"touches them, so nothing is expressed against them.")
    connected = comps <= 1
    if net.get("connected") is not None and bool(net["connected"]) != connected:
        rep.block("network-connected",
                  f"the network records connected={net.get('connected')} but its "
                  f"edges form {comps} component(s).")
    # The load-bearing rule: no indirect estimate without a loop to check it.
    has_indirect = any(
        (canon["results"]["by_outcome"].get(e.get("outcome_id")) or {}).get("pooled")
        for e in net.get("edges", []))
    if loops == 0:
        if net.get("status", "").strip() == "":
            rep.block("network-status-undeclared",
                      "a network with no closed loop must state its status; "
                      "consistency there is untestable, not satisfied.")
        if not str(net.get("why_no_network_estimate", "")).strip():
            rep.block("network-silent-on-loops",
                      "this network contains no closed loop and says nothing "
                      "about what that costs. Incoherence is measured around a "
                      "loop; with none, an indirect estimate rests on an "
                      "assumption nothing in the object can test.")
        if has_indirect:
            rep.block("network-indirect-without-loop",
                      "this network publishes a synthesised estimate while "
                      "containing no closed loop, so nothing in it can be "
                      "checked against anything else.")
    # A multi-arm study contributes a covariance; claiming none while declaring
    # one is the unit-of-analysis error 23.3.4 names.
    declared_multi = net.get("multi_arm_studies")
    actual_multi = sum(
        1 for t in canon["inputs"]["trials"]
        if sum(1 for a in t.get("arms", []) if a.get("role") == "treatment") > 1)
    if declared_multi is not None and declared_multi != actual_multi:
        rep.block("network-multi-arm-count",
                  f"the network records {declared_multi} multi-arm studies but "
                  f"{actual_multi} of the trials declare more than one treatment "
                  f"arm.")


def check_self_reference(canon, rep):
    """Prose may not ASSERT a block of this object that this object lacks.

    A reviewer found completeness_statement saying the excluded registrations
    were itemised in the removal block, one commit after the removal block was
    deleted -- the object describing a part of itself that no longer existed.
    The removal-disclosure detector could not see it, because it reads the block
    and not the sentence pointing at the block.

    POLARITY MATTERS and the first version of this rule got it wrong, firing on
    "there is no removal block and no quarantine", which is a correct statement
    about an object that has neither -- and firing it against an object already
    published. A denial is not a dangling reference. So the sentence is split on
    its clauses and only a clause that mentions the block WITHOUT a negation in
    it counts as an assertion.
    """
    NAMED = {
        "removal block": ("removed_citations",),
        "removed_citations": ("removed_citations",),
        "quarantine": ("quarantine",),
        "screening block": ("screening",),
        "reconciliation block": ("reconciliation",),
        "network block": ("network",),
    }
    PROSE_KEYS = ("note", "detail", "reason", "statement", "conformance",
                  "caveat", "definition_note", "decision", "question_note")
    NEG = re.compile(r"\b(no|not|never|without|neither|nor|absent|lacks)\b")
    SPLIT = re.compile(r"[.;]|\band\b|\bbut\b")

    def present(keys):
        return any(canon.get(k) for k in keys)

    def asserts(text, phrase):
        """True only if some clause names the phrase and does not negate it."""
        # Word boundaries in BOTH tests. A bare "and" splits
        # inside "randomised", so the clauses stop
        # corresponding to anything.
        for clause in SPLIT.split(text.lower()):
            if phrase in clause and not NEG.search(clause):
                return True
        return False

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str):
                    if not any(k == pk or k.endswith("_" + pk) for pk in PROSE_KEYS):
                        continue
                    for phrase, keys in NAMED.items():
                        if present(keys):
                            continue
                        if asserts(v, phrase):
                            rep.block("self-reference-absent",
                                      f"{path}.{k} asserts a {phrase!r} that this "
                                      f"object does not contain. A sentence "
                                      f"pointing at a part of the object is wrong "
                                      f"the moment that part is removed, and "
                                      f"nothing else here can see it.")
                else:
                    walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(canon, "canonical")


DETECTORS = [
    ("outcome-coverage", check_outcome_coverage),
    ("self-reference", check_self_reference),
    ("network", check_network),
    ("handbook-citation", check_handbook_citation),
    ("pool-uniformity", check_pool_uniformity),
    ("estimand-storage-form", check_estimand_storage_form),
    ("estimand-homogeneity", check_estimand_homogeneity),
    ("shared-control-double-count", check_shared_control_double_count),
    ("regimen-homogeneity", check_regimen_homogeneity),
    ("log-effect-consistency", check_log_effect_consistency),
    ("ve-consistency", check_ve_consistency),
    ("analysed-scope", check_analysed_scope),
    ("arm-role-vs-registry", lambda c, r: check_arm_role_vs_registry(c, r)),
    ("identifier-anchoring", check_identifier_anchoring),
    ("superseded", check_superseded),
    ("removal-disclosure", check_removal_disclosure),
    ("removal-grounds", check_removal_grounds),
    ("per-trial-source-fields", check_per_trial_source_fields),
    ("quoted-group-disclosure", check_quoted_group_disclosure),
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
