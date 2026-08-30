# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: what the pooled ratio means in people -- risk per 1000, and the NNT.

WHY THIS ONE FIRST. Of the thirteen features that won the blinded comparison, this is the one
the judges weighted highest and it needs NO retrieval: the baseline risk is already in the
object, in the control arms of the trials being pooled. A ratio alone does not tell a clinician
or a programme what a treatment costs per event averted, and that is the sentence a reader
takes away.

⛔ DERIVE OR REFUSE, AND THE REFUSALS HERE ARE NOT EDGE CASES -- THEY ARE MOST OF THE CORPUS.

  * A RISK ratio can be applied to a baseline RISK. An ODDS ratio cannot: OR x baseline-risk is
    not a risk, and the substitution overstates the effect whenever the outcome is common.
  * A HAZARD ratio over person-time needs a baseline RATE and a time horizon, not a baseline
    risk, and this object does not hold person-time. Refused by measure, not approximated.
  * No arm pair -> no baseline. Read via `arm_roles.the_pair`, which returns None rather than
    guessing when a trial has two treatments or unlabelled arms.
  * A withdrawn pool gets the withdrawal and no absolute effect.

⚠️ AND THE INTERVAL ON THE ABSOLUTE EFFECT IS THE RATIO'S INTERVAL, NOT A NEW ONE. The baseline
risk is treated as fixed -- it is an observed quantity in these trials, not an estimate being
propagated -- so the interval printed here carries the uncertainty in the RATIO only. That is
the Cochrane summary-of-findings convention and it is stated on the page rather than left for a
reader to assume, because an interval whose provenance is unstated is a number nobody can
check.

⛔ AND WHERE THE RATIO'S INTERVAL SPANS NO DIFFERENCE, NO BOUNDED NNT IS PRINTED. As the risk
ratio approaches 1 the absolute reduction approaches zero and the NNT diverges; past 1 it
becomes a number needed to HARM. An interval that crosses 1 therefore maps to an NNT interval
that passes through infinity, and printing its two endpoints as though they bracketed a number
is the single commonest way this statistic is reported wrongly. The component says so instead.

COVERAGE FRACTION, measured rather than asserted. `coverage()` counts the topic objects under
`ssot/` whose every contributing trial carries a labelled arm pair -- the input this component
cannot work without. A component that ran silently on the objects it could serve and said
nothing about the rest would be reporting its reach as its population.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SSOT = os.path.join(REPO, "ssot")
for _p in (HERE, SSOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arm_roles  # noqa: E402

# Measures whose point estimate multiplies a baseline RISK to give a risk. Nothing else does.
RISK_RATIO = ("RR", "RISK RATIO", "RELATIVE RISK")

# Named individually so a refusal can say WHICH wrong thing it declined to do, rather than
# printing one sentence that fits every measure and explains none of them.
NOT_A_RISK_RATIO = {
    "OR": "an odds ratio applied to a baseline risk does not give a risk, and the error grows "
          "with the event rate",
    "ODDS RATIO": "an odds ratio applied to a baseline risk does not give a risk, and the error "
                  "grows with the event rate",
    "HR": "a hazard ratio is a ratio of rates over person-time; converting it needs a baseline "
          "RATE and a stated horizon, and this object holds neither",
    "HAZARD RATIO": "a hazard ratio is a ratio of rates over person-time; converting it needs a "
                    "baseline RATE and a stated horizon, and this object holds neither",
    "IRR": "an incidence-rate ratio needs person-time, which this object does not hold",
    "RATE RATIO": "an incidence-rate ratio needs person-time, which this object does not hold",
    "MD": "a mean difference is already on the outcome's own scale and needs no conversion",
    "SMD": "a standardised mean difference has no absolute reading without a reference standard "
           "deviation, which this object does not hold",
}


def _u(x):
    return str(x or "").strip().upper()


def _trial_index(canon):
    """nct / trial_id / label -> the input trial record, which is where arms live."""
    idx = {}
    inp = canon.get("inputs")
    trials = (inp or {}).get("trials") if isinstance(inp, dict) else None
    for t in (trials or []):
        if not isinstance(t, dict):
            continue
        for key in (t.get("nct"), t.get("trial_id"), t.get("label")):
            if key:
                idx.setdefault(str(key), t)
    return idx


def baseline(canon, res):
    """Pooled control-arm risk across the CONTRIBUTING trials.

    -> ((risk, events, n, labels), None) or (None, reason).

    ⛔ PARTIAL IS A REFUSAL, NOT A SMALLER SAMPLE. A baseline pooled over some of the trials in
    a pool is not the baseline of that pool: it is a different population wearing this pool's
    ratio. So a single missing arm pair refuses the whole outcome and names what was missing.
    """
    idx = _trial_index(canon)
    ev = n = 0
    used, missing = [], []
    for pt in (res.get("per_trial") or []):
        if not isinstance(pt, dict):
            continue
        name = pt.get("label") or pt.get("nct") or pt.get("trial_id") or "?"
        rec = None
        for key in (pt.get("nct"), pt.get("trial_id"), pt.get("label")):
            if key and str(key) in idx:
                rec = idx[str(key)]
                break
        pair = arm_roles.the_pair((rec or {}).get("arms")) or arm_roles.the_pair(pt.get("arms"))
        if not pair:
            missing.append(str(name))
            continue
        _t, c = pair
        e = c.get("events")
        m = c.get("participants", c.get("n"))
        if not isinstance(e, (int, float)) or not isinstance(m, (int, float)) or m <= 0:
            missing.append(str(name))
            continue
        ev += e
        n += m
        used.append(str(name))
    if not used:
        return None, ("no contributing trial carries a labelled control arm with counts%s"
                      % ((" (" + ", ".join(m[:40] for m in missing[:4]) + ")")
                         if missing else ""))
    if missing:
        return None, ("only %d of %d contributing trials carry a labelled control arm with "
                      "counts, and a baseline pooled over part of the evidence is not the "
                      "baseline of this pool (missing: %s)"
                      % (len(used), len(used) + len(missing),
                         ", ".join(m[:40] for m in missing[:4])))
    return (float(ev) / float(n), ev, n, used), None


def absolute(risk0, rr, lo, hi):
    """Risks per 1000 and the NNT. The baseline is fixed; the interval is the ratio's."""
    r1 = [risk0 * v * 1000.0 for v in (rr, lo, hi)]
    arr = [risk0 * 1000.0 - v for v in r1]              # positive = fewer events on treatment
    out = {"per1000_control": risk0 * 1000.0, "per1000_treated": r1, "arr_per1000": arr,
           "spans_null": (lo <= 1.0 <= hi)}
    out["nnt"] = (1000.0 / arr[0]) if abs(arr[0]) > 1e-12 else None
    # ⛔ Endpoints are printed ONLY when the ratio's interval stays on one side of 1. Otherwise
    # the NNT interval passes through infinity and its endpoints bracket nothing.
    out["nnt_ci"] = None
    if not out["spans_null"] and all(abs(a) > 1e-12 for a in arr[1:]):
        a, b = sorted((1000.0 / arr[1], 1000.0 / arr[2]))
        out["nnt_ci"] = (a, b)
    return out


def _horizon(canon, res):
    """What span this NNT is over: a typed field, else the registries' verbatim wording.

    ⚠️ The registered time frames are NOT parsed into a number. The objects store them verbatim
    precisely because the registries' wording varies, and normalising "a minimum of 12 months
    and a maximum of 14 months per participant" into a figure would assert a precision the
    source does not carry.
    """
    for src in (res, canon):
        f = src.get("followup") if isinstance(src, dict) else None
        if not isinstance(f, dict):
            continue
        # ⛔ THE FIELD WAS THERE AND THIS FUNCTION COULD NOT SEE IT. It required `value`; the
        # field was landed as `median`/`unit` by the retrieval that read it at source, so the
        # horizon silently fell through to the verbatim-timeframes branch and the NNT was
        # published with no span at all.
        #
        # ⚠️ CAUGHT BY A SIBLING LANE'S CLAIM LEDGER, NOT BY MINE: my own ledger's C3 probe
        # asked only for "need to be treated ... prevent", which the sentence satisfied WITHOUT
        # a horizon. A reader-facing claim that names a number of people and no period of time
        # is not the claim -- and a probe that does not require the horizon cannot notice.
        for key in ("value", "median", "mean"):
            if f.get(key) and f.get("unit"):
                return ("%s %s" % (f[key], f["unit"]), f.get("basis") or "", True)
    inp = canon.get("inputs")
    trials = (inp or {}).get("trials") if isinstance(inp, dict) else None
    quoted = []
    for t in (trials or []):
        v = t.get("registered_primary_timeframe") if isinstance(t, dict) else None
        if v:
            quoted.append("%s: &ldquo;%s&rdquo;" % (t.get("label") or t.get("nct") or "?", v))
    return (None, "; ".join(quoted), False)


def _f(x, nd=1):
    return ("%." + str(nd) + "f") % x


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(canon):
    r = canon.get("results")
    outs = (r or {}).get("by_outcome") if isinstance(r, dict) else None
    head = "<h2>What the pooled effect means in people</h2>"
    if not isinstance(outs, dict) or not outs:
        return (head + "<p>This object records no outcome, so there is no ratio to convert. "
                "That is a refusal, not an omission.</p>")
    rows, notes = [], []
    for oid, res in outs.items():
        if not isinstance(res, dict):
            continue
        name = _esc(str(oid)[:60])
        pooled = res.get("pooled") or {}
        if pooled.get("withdrawn"):
            notes.append("<p><b>%s &mdash; no absolute effect is given.</b> This pool is "
                         "withdrawn; converting it to people would republish a number the "
                         "object exists to retract.</p>" % name)
            continue
        measure = _u(pooled.get("measure") or res.get("measure"))
        if measure in NOT_A_RISK_RATIO:
            notes.append("<p><b>%s &mdash; not converted.</b> The pooled quantity is %s, and %s. "
                         "It is refused rather than approximated.</p>"
                         % (name, _esc(measure), NOT_A_RISK_RATIO[measure]))
            continue
        if measure not in RISK_RATIO:
            notes.append("<p><b>%s &mdash; not converted.</b> The pooled measure is recorded as "
                         "%s, which this component cannot place on a risk scale. An unrecognised "
                         "measure is refused, not assumed to be a risk ratio.</p>"
                         % (name, _esc(measure) or "absent"))
            continue
        pt, lo, hi = pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")
        if not all(isinstance(v, (int, float)) and v > 0 for v in (pt, lo, hi)):
            notes.append("<p><b>%s &mdash; not converted.</b> The pooled ratio or its interval is "
                         "absent from this object.</p>" % name)
            continue
        got, why = baseline(canon, res)
        if got is None:
            notes.append("<p><b>%s &mdash; no baseline risk, so no absolute effect.</b> %s. "
                         "Borrowing a baseline from an external population would put a different "
                         "review's number inside this one's interval.</p>" % (name, _esc(why)))
            continue
        risk0, ev, n, _used = got
        a = absolute(risk0, float(pt), float(lo), float(hi))
        if a["spans_null"]:
            nnt_cell = "not bounded &mdash; the ratio's interval spans no difference"
        elif a["nnt_ci"]:
            nnt_cell = "%d (%d to %d)" % (round(a["nnt"]), round(a["nnt_ci"][0]),
                                          round(a["nnt_ci"][1]))
        else:
            nnt_cell = "%d" % round(a["nnt"]) if a["nnt"] else "&mdash;"
        # ⛔ ENDPOINTS ARE SORTED, NOT ASSUMED. Mapping the ratio's lower bound to the lower
        # absolute bound is only right while the ratio is below 1; a ratio whose interval
        # crosses 1 printed "(125.0 to 72.0)" -- descending, and read by anyone as a typo in
        # the data rather than in the renderer. Caught by the spans-null control, which is the
        # only case where the two orders differ.
        tlo, thi = sorted(a["per1000_treated"][1:])
        alo, ahi = sorted(a["arr_per1000"][1:])
        rows.append(
            "<tr><td>%s</td><td>%s</td><td>%s (%s to %s)</td><td>%s (%s to %s)</td>"
            "<td class=\"nnt\">%s</td></tr>"
            % (name, _f(a["per1000_control"]),
               _f(a["per1000_treated"][0]), _f(tlo), _f(thi),
               _f(a["arr_per1000"][0]), _f(alo), _f(ahi),
               nnt_cell))
        span, quoted, typed = _horizon(canon, res)
        horizon = (" over %s" % _esc(span)) if typed else ""
        if a["spans_null"]:
            notes.append(
                "<p>For <b>%s</b>: %d of %d in the pooled control arms had the outcome, so the "
                "baseline is %s per 1000. <b>No bounded number needed to treat is given</b>, "
                "because the ratio's interval (%s to %s) includes no difference. As the ratio "
                "approaches 1 the absolute reduction approaches zero and the number needed to "
                "treat diverges; past 1 it is a number needed to harm. Printing the two "
                "endpoints as though they bracketed a value is the commonest way this statistic "
                "is reported wrongly.</p>"
                % (name, ev, n, _f(risk0 * 1000.0), _f(float(lo), 3), _f(float(hi), 3)))
        else:
            notes.append(
                "<p>For <b>%s</b>: %d of %d in the pooled control arms had the outcome, so the "
                "baseline is %s per 1000. Applying the pooled ratio, about <b>%d</b> people need "
                "to be treated%s to prevent one event%s. The number needed to treat is given "
                "because a ratio alone does not tell a clinician or a programme what a treatment "
                "costs per event averted.</p>"
                % (name, ev, n, _f(risk0 * 1000.0), round(a["nnt"]), horizon,
                   (", and the plausible range runs from %d to %d"
                    % (round(a["nnt_ci"][0]), round(a["nnt_ci"][1]))) if a["nnt_ci"] else ""))
        if not typed and quoted:
            notes.append(
                "<p>This object does not state a follow-up span in a comparable form, so no "
                "single horizon is asserted for the figures above and none is invented. The "
                "registered primary time frames, verbatim: %s.</p>" % quoted)
    out = [head]
    if rows:
        out.append("<div class=\"scroll\"><table><tr><th>Outcome</th>"
                   "<th>Risk per 1,000, control</th><th>Risk per 1,000, treated (95%)</th>"
                   "<th>Absolute reduction per 1,000 (95%)</th>"
                   "<th>Number needed to treat</th></tr>" + "".join(rows) + "</table></div>")
        out.append(
            "<p>The baseline is this review's own pooled control arms, not an external "
            "population, and it is treated as a fixed observed quantity: <b>the interval on "
            "every absolute figure above carries the uncertainty in the ratio and nothing "
            "else</b>. A reader who needs these numbers for a population with a different "
            "underlying risk should re-apply the ratio to that risk.</p>")
    out.extend(notes)
    return "".join(out)


MARKER = "<h2>What the pooled effect means in people</h2>"


def inject(html, canon):
    if MARKER in html:
        return html
    return html + "\n<div class=\"card\">\n" + render(canon) + "\n</div>\n"


# ---------------------------------------------------------------------------------------------
# COVERAGE, and the two controls.
# ---------------------------------------------------------------------------------------------

def classify(canon, res):
    """Why this outcome is or is not converted. ⛔ ENUMERATE THE KINDS BEFORE COUNTING.

    The first version of `coverage()` counted objects whose trials carry an arm pair and called
    that the reach. It is not: CASTLE-AF carries a perfectly good arm pair and pools a HAZARD
    ratio, which this component refuses on purpose. Counting it as served would have reported
    a reach of 46 objects for a component that converts far fewer, and the number would have
    looked like a capability.
    """
    pooled = res.get("pooled") or {}
    if pooled.get("withdrawn"):
        return "refused: the pool is withdrawn"
    measure = _u(pooled.get("measure") or res.get("measure"))
    if measure in NOT_A_RISK_RATIO:
        return "refused: the measure is %s, not a risk ratio" % measure
    if measure not in RISK_RATIO:
        return "refused: the measure is unrecognised (%s)" % (measure or "absent")
    pt, lo, hi = pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")
    if not all(isinstance(v, (int, float)) and v > 0 for v in (pt, lo, hi)):
        return "refused: no pooled ratio or no interval"
    got, _why = baseline(canon, res)
    if got is None:
        return "refused: no baseline risk (no labelled control arm with counts)"
    return "CONVERTED"


def coverage(root=None):
    """Reach over the population this component claims to police, by KIND and with a denominator."""
    import collections
    import glob
    import json
    root = root or SSOT
    per_outcome = collections.Counter()
    skipped = collections.Counter()
    objs = 0
    obj_any = 0
    for f in sorted(glob.glob(os.path.join(root, "*", "*.json"))):
        try:
            c = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            # ⛔ COUNTED, NOT SKIPPED. A `continue` here removes the file from the denominator
            # and the coverage figure silently becomes a reach figure.
            skipped["file did not parse as JSON"] += 1
            continue
        if not isinstance(c, dict):
            skipped["top level is not an object"] += 1
            continue
        r = c.get("results")
        outs = r.get("by_outcome") if isinstance(r, dict) else None
        if not isinstance(outs, dict) or not outs:
            skipped["no results.by_outcome recorded"] += 1
            continue
        objs += 1
        hit = False
        for _oid, res in outs.items():
            if not isinstance(res, dict):
                continue
            k = classify(c, res)
            per_outcome[k] += 1
            hit = hit or (k == "CONVERTED")
        obj_any += 1 if hit else 0
    return {"objects_with_a_pooled_result": objs,
            "objects_with_at_least_one_conversion": obj_any,
            "outcomes": dict(per_outcome),
            "outcomes_total": sum(per_outcome.values()),
            "skipped": dict(skipped)}


# ⭐ THE MODEL ANSWER. Arithmetic anyone can check on paper, so the control is keyed to an
# answer established OUTSIDE this file: a baseline of 100 per 1000 and a risk ratio of exactly
# 0.50 must give 50 per 1000 treated, an absolute reduction of 50 per 1000, and an NNT of 20.
MODEL_ANSWER = {
    "app_id": "__control_model_answer",
    "inputs": {"trials": [
        {"nct": "NCT00000001", "label": "Control trial A", "arms": [
            {"label": "treatment", "role": "treatment", "events": 50, "participants": 1000},
            {"label": "placebo", "role": "control", "events": 100, "participants": 1000}]}]},
    "results": {"by_outcome": {"primary": {
        "measure": "RR",
        "pooled": {"point": 0.50, "ci_low": 0.40, "ci_high": 0.625, "measure": "RR"},
        "per_trial": [{"nct": "NCT00000001", "label": "Control trial A", "measure": "RR",
                       "point": 0.50, "ci_low": 0.40, "ci_high": 0.625}]}}}}

# ⭐ THE REFUSAL CONTROL. A hazard ratio has no baseline RISK to multiply, and this component
# must go on saying so. If a later change makes this control fail, the component has started
# converting a quantity it cannot convert -- and the control is what tells you, because the
# output would otherwise look like a capability rather than a defect.
REFUSAL_CONTROL = {
    "app_id": "__control_refusal_hazard_ratio",
    "inputs": {"trials": [
        {"nct": "NCT00000002", "label": "Control trial B", "arms": [
            {"label": "treatment", "role": "treatment", "events": 50, "participants": 1000},
            {"label": "placebo", "role": "control", "events": 100, "participants": 1000}]}]},
    "results": {"by_outcome": {"primary": {
        "measure": "HR",
        "pooled": {"point": 0.50, "ci_low": 0.40, "ci_high": 0.625, "measure": "HR"},
        "per_trial": [{"nct": "NCT00000002", "label": "Control trial B", "measure": "HR",
                       "point": 0.50, "ci_low": 0.40, "ci_high": 0.625}]}}}}

# ⭐ THE SECOND REFUSAL CONTROL. A ratio whose interval spans 1 must NOT be given a bounded NNT.
SPANS_NULL_CONTROL = {
    "app_id": "__control_refusal_spans_null",
    "inputs": {"trials": [
        {"nct": "NCT00000003", "label": "Control trial C", "arms": [
            {"label": "treatment", "role": "treatment", "events": 95, "participants": 1000},
            {"label": "placebo", "role": "control", "events": 100, "participants": 1000}]}]},
    "results": {"by_outcome": {"primary": {
        "measure": "RR",
        "pooled": {"point": 0.95, "ci_low": 0.72, "ci_high": 1.25, "measure": "RR"},
        "per_trial": [{"nct": "NCT00000003", "label": "Control trial C", "measure": "RR",
                       "point": 0.95, "ci_low": 0.72, "ci_high": 1.25}]}}}}

# ⭐ THE THIRD REFUSAL CONTROL. One of two contributing trials has no labelled arm pair, so the
# baseline would be pooled over half the evidence. That must stay a refusal: the failure it
# guards against produces a number that looks entirely normal.
PARTIAL_CONTROL = {
    "app_id": "__control_refusal_partial_baseline",
    "inputs": {"trials": [
        {"nct": "NCT00000004", "label": "Control trial D", "arms": [
            {"label": "treatment", "role": "treatment", "events": 50, "participants": 1000},
            {"label": "placebo", "role": "control", "events": 100, "participants": 1000}]},
        {"nct": "NCT00000005", "label": "Control trial E"}]},
    "results": {"by_outcome": {"primary": {
        "measure": "RR",
        "pooled": {"point": 0.50, "ci_low": 0.40, "ci_high": 0.625, "measure": "RR"},
        "per_trial": [{"nct": "NCT00000004", "label": "Control trial D"},
                      {"nct": "NCT00000005", "label": "Control trial E"}]}}}}


import re  # noqa: E402  (used by the controls below and by the display-order assertion)


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def _no_nnt_column(html):
    """No table at all: the outcome was refused before any figure was produced."""
    return ("Number needed to treat</th>" not in html), "no table emitted"


def _no_bounded_nnt(html):
    """A table is fine here; a NUMBER in the NNT cell is not.

    ⛔ STRUCTURAL, NOT TEXTUAL. The cell is found by its own class rather than by position or
    by searching the whole page for digits -- the page is full of legitimate digits, and a
    check that counted them would be measuring the renderer's verbosity.
    """
    cells = re.findall(r"<td class=\"nnt\">(.*?)</td>", html, re.S)
    if not cells:
        return False, "the NNT cell was not found at all"
    bad = [c for c in cells if re.search(r"\d", _plain(c))]
    return (not bad), "no bounded NNT printed"


def plant():
    """Watch it produce the right answer, and watch each refusal STAY a refusal."""
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    got, why = baseline(MODEL_ANSWER, MODEL_ANSWER["results"]["by_outcome"]["primary"])
    assert got, why
    risk0 = got[0]
    assert abs(risk0 - 0.10) < 1e-12, risk0
    a = absolute(risk0, 0.50, 0.40, 0.625)
    print("MODEL ANSWER -- baseline 100/1000, RR 0.50; the answer is fixed by arithmetic, not")
    print("               by this file: 50 per 1000 treated, 50 averted, NNT 20.")
    assert abs(a["per1000_control"] - 100.0) < 1e-9, a
    assert abs(a["per1000_treated"][0] - 50.0) < 1e-9, a
    assert abs(a["arr_per1000"][0] - 50.0) < 1e-9, a
    assert abs(a["nnt"] - 20.0) < 1e-9, a
    assert a["nnt_ci"] and abs(a["nnt_ci"][0] - (1000.0 / 60.0)) < 1e-9, a
    body = _plain(render(MODEL_ANSWER))
    assert "50.0" in body and "20" in body, body[:400]
    assert "number needed to treat" in body.lower(), body[:400]
    print("   rendered, and the section SAW the case it was built for   [PASS]")
    print("")
    # ⛔ WHAT "THE REFUSAL HELD" MEANS DIFFERS BY CONTROL, AND SAYING SO IS THE POINT.
    #
    # The first version of this loop asserted one thing for all three -- that no table was
    # emitted -- and the spans-null control FAILED it. Correctly: an interval that crosses 1
    # still has a perfectly good absolute reduction, and only the NNT is unbounded. The
    # component was right and the control was wrong, which is exactly the direction a control
    # is supposed to be able to fail in.
    #
    # ⚠️ AND THE SECOND HALF IS WHAT MAKES EACH ONE A CONTROL RATHER THAN A GREP: it asserts
    # what must be ABSENT. A page that printed the reason AND the number would pass on the
    # reason string alone.
    for obj, must_say, forbidden, what in (
            (REFUSAL_CONTROL, "hazard ratio", _no_nnt_column,
             "a hazard ratio is refused rather than multiplied into a risk"),
            (SPANS_NULL_CONTROL, "not bounded", _no_bounded_nnt,
             "an interval spanning no difference gets no bounded NNT"),
            (PARTIAL_CONTROL, "not the baseline of this pool", _no_nnt_column,
             "a baseline over part of the evidence is refused")):
        html = render(obj)
        t = _plain(html)
        ok = must_say.lower() in t.lower()
        held, held_what = forbidden(html)
        print("REFUSAL CONTROL -- %s" % what)
        print("   reason stated: %s   %s: %s   [%s]"
              % (ok, held_what, held, "PASS" if (ok and held) else "FAIL"))
        assert ok and held, t[:400]
    # ⛔ AND THE DISPLAY ORDER, which the spans-null control also caught: an interval whose
    # endpoints print descending is a defect in the renderer that reads as a defect in the data.
    for obj in (MODEL_ANSWER, SPANS_NULL_CONTROL):
        for a, b in re.findall(r"\(([-\d.]+) to ([-\d.]+)\)", render(obj)):
            assert float(a) <= float(b), "interval printed descending: (%s to %s)" % (a, b)
    print("   every printed interval ascends   [PASS]")
    print("")
    print("⚠️ If a control here ever creates pressure to stop refusing, the control is wrong")
    print("   and the refusal is right. None of the three may be relaxed to raise a count.")
    return 0


if __name__ == "__main__":
    if "--plant" in sys.argv:
        raise SystemExit(plant())
    import json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    if "--coverage" in sys.argv:
        # ⛔ A ZERO OVER AN UNSTATED DENOMINATOR IS A STATEMENT ABOUT REACH, so the root being
        # scanned is printed and an empty scan is a FAILURE rather than a clean sheet. Measured:
        # run from outside the repo this reported "0 objects" in a confident-looking table.
        root = SSOT
        for i, a in enumerate(sys.argv):
            if a == "--root" and i + 1 < len(sys.argv):
                root = sys.argv[i + 1]
        c = coverage(root)
        n, m = c["objects_with_a_pooled_result"], c["outcomes_total"]
        print("")
        print("  scanned: %s" % root)
        if not n:
            print("  ⛔ SCAN FOUND NOTHING. That is a failure of this scan, not a property of the")
            print("     corpus. Point --root at the ssot directory.")
            raise SystemExit(2)
        print("")
        print("COVERAGE FRACTION -- absolute effects and NNT")
        print("")
        print("  objects with a pooled result        %4d   == the object denominator" % n)
        print("  objects with >=1 conversion         %4d   %5.1f%%"
              % (c["objects_with_at_least_one_conversion"],
                 100.0 * c["objects_with_at_least_one_conversion"] / n if n else 0.0))
        print("")
        print("  outcomes examined                   %4d   == the outcome denominator" % m)
        for k, v in sorted(c["outcomes"].items(), key=lambda kv: -kv[1]):
            print("     %-52s %4d   %5.1f%%" % (k, v, 100.0 * v / m if m else 0.0))
        print("")
        print("  The component RENDERS on every one of them: where it cannot convert it prints a")
        print("  NAMED refusal rather than nothing, so the gap is visible on the page and not")
        print("  only in this table. A silent skip would report reach as population.")
        if c.get("skipped"):
            print("")
            print("  SKIPPED, by kind -- these files were NOT in any denominator "
                  "above:")
            for _k, _v in sorted(c["skipped"].items(), key=lambda kv: -kv[1]):
                print("     %-46s %4d" % (_k, _v))
            print("  ⚠️ A skip that is not counted turns a coverage figure into a "
                  "reach figure.")
        raise SystemExit(0)
    os.chdir(REPO)
    for path in sys.argv[1:] or ["ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"]:
        canon = json.load(io.open(path, encoding="utf-8"))
        print("=" * 78)
        print(os.path.basename(path))
        print(_plain(render(canon))[:1800])
