import re
# -*- coding: utf-8 -*-
"""The HTA tab as a SUMMARY OF FINDINGS table, and the Guideline tab as an
EVIDENCE-TO-DECISION COVERAGE MAP. Both derived. Neither composed.

⛔ WE INVENTED "HTA VIEW" AND THEN COULD NOT FILL IT. The Cochrane Handbook
already specifies the artefact that belongs in each place, and specifying it
first is what made them derivable:

    HTA       -> Summary of Findings table          (Handbook ch. 14, 14.1.2)
    Guideline -> Evidence-to-Decision coverage map  (Handbook ch. 15, 15.6)

⛔ NO COMPOSED PROSE ANYWHERE IN THIS FILE. Every cell is read from the object
with its field path recorded, or it says the object does not hold it. A tab that
declines HAVING SHOWN what is held is a better artefact than an empty panel, and
a much better one than an invented panel.

=========================================================================
ABSOLUTE EFFECTS, AND WHY A GRID RATHER THAN ONE ASSUMED BASELINE RISK
=========================================================================
Handbook 14.1.3 asks for absolute effects at stated baseline risks. A SINGLE
assumed baseline risk is a modelling choice the review author makes on behalf of
a jurisdiction they do not know -- which is exactly why `absolute_effect.py`
REFUSES to emit one without a declared indirectness argument, and refuses on 145
of 146 outcome blocks.

This card does not bypass that gate and does not pretend to satisfy it. It does
two separate things:

  1. It shows the arithmetic on a GRID of baseline risks the READER chooses
     from. That is not a transfer claim: no baseline is asserted to be this
     reader's, so there is nothing to transfer. It is `RR x baseline`, stated as
     arithmetic, at several baselines, with the reader supplying which one
     applies to their population.

  2. Where `absolute_effect.derive()` DECLINES, the card prints the declination
     AS A FIELD, in the module's own words. The gate's judgement stays visible
     on the surface rather than being routed around silently.

Those are different claims and the card keeps them apart. Presenting one assumed
risk as "the" absolute effect would be the loosening; a grid plus the recorded
refusal is not.
"""
import io
import json
import os

HANDBOOK_SOF = "Cochrane Handbook v6.5, chapter 14 (14.1.2 contents, 14.1.3 absolute effects)"
HANDBOOK_ETD = "Cochrane Handbook v6.5, chapter 15 (15.6 implications for practice)"

# The GRADE Evidence-to-Decision considerations, in the Handbook's order. This
# list is a FORMAT, not a judgement: naming every domain and marking which are
# unanswered is the whole content of the guideline tab.
ETD_DOMAINS = (
    ("problem_is_a_priority", "Is the problem a priority?"),
    ("desirable_anticipated_effects", "How substantial are the desirable effects?"),
    ("undesirable_anticipated_effects", "How substantial are the undesirable effects?"),
    ("certainty_of_evidence", "What is the overall certainty of the evidence?"),
    ("values", "Is there important uncertainty about how much people value the outcomes?"),
    ("balance_of_effects", "Does the balance favour the intervention or the comparison?"),
    ("resources_required", "How large are the resource requirements?"),
    ("certainty_of_resource_evidence", "What is the certainty of the resource evidence?"),
    ("cost_effectiveness", "Does cost-effectiveness favour the intervention?"),
    ("equity", "What would be the impact on health equity?"),
    ("acceptability", "Is the intervention acceptable to key stakeholders?"),
    ("feasibility", "Is the intervention feasible to implement?"),
)

# Baseline risks per 1000, spanning two orders of magnitude so a reader in any
# setting finds a row near their own incidence. Fixed here, not tuned per topic:
# a grid chosen to flatter a particular result is a single assumed risk wearing
# a disguise.
BASELINE_GRID = (1, 5, 10, 50, 100, 200)


def _e(s):
    return (str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _blocks(canon):
    """(outcome_id, record) for every outcome carrying a pooled result."""
    res = canon.get("results")
    bo = res.get("by_outcome") if isinstance(res, dict) else None
    if not isinstance(bo, dict):
        return []
    out = []
    for oid, rec in bo.items():
        if isinstance(rec, dict) and isinstance(rec.get("pooled"), dict):
            out.append((oid, rec))
    return out


def _participants(canon):
    """Total randomised across contributing trials, and the count of trials.

    Returns (n_participants or None, n_trials). None is printed as a named
    absence, never as 0 -- zero participants is a claim and an unknown is not."""
    trials = (canon.get("inputs") or {}).get("trials") or []
    total = 0
    seen = 0
    for t in trials:
        if not isinstance(t, dict):
            continue
        seen += 1
        n = t.get("enrolled")
        if isinstance(n, int):
            total += n
        else:
            arms = t.get("arms")
            if isinstance(arms, list):
                for a in arms:
                    if isinstance(a, dict) and isinstance(a.get("participants"), int):
                        total += a["participants"]
    return (total or None), seen


def _participants_for(canon, oid, k_stored):
    """Participants ANALYSED for THIS outcome, from the cells the effect uses.

    Returns (n or None, k_derived, state). The states are:

      DERIVED        every trial the object counts for this outcome also
                     holds per-arm counts, so the total is a total.
      PARTIAL_CELLS  some contributing trials hold counts and some do not. No
                     number is returned. A sum over the subset would be an
                     UNDERSTATEMENT, and an understatement is more dangerous
                     than the overstatement it replaces because it reads as
                     conservative.
      NO_CELLS       no contributing trial holds per-arm counts.

    Read in this order, both outcome-specific:
      1. by_outcome[oid].analysed = {treatment, control}
      2. by_outcome[oid].control.n + by_outcome[oid].treatment.n
    A trial-level enrolment attached to a specific outcome is the error being
    fixed here, so it is never a fallback.
    """
    total = 0
    k_cells = 0
    k_named = 0
    for t in ((canon.get("inputs") or {}).get("trials") or []):
        if isinstance(t, dict) is False:
            continue
        e = (t.get("by_outcome") or {}).get(oid)
        if isinstance(e, dict) is False:
            continue
        k_named += 1
        got = None
        a = e.get("analysed")
        if isinstance(a, dict):
            tx, cx = a.get("treatment"), a.get("control")
            if _plain_int(tx) and _plain_int(cx) and tx >= 0 and cx >= 0:
                got = tx + cx
        if got is None:
            c, tr = e.get("control"), e.get("treatment")
            if isinstance(c, dict) and isinstance(tr, dict):
                cn, tn = c.get("n"), tr.get("n")
                if _plain_int(cn) and _plain_int(tn) and cn >= 0 and tn >= 0:
                    got = cn + tn
        if got is not None:
            total += got
            k_cells += 1
    if k_cells == 0:
        return None, 0, "NO_CELLS"
    expected = k_stored if _plain_int(k_stored) and k_stored > 0 else k_named
    if k_cells != expected:
        return None, k_cells, "PARTIAL_CELLS"
    return total, k_cells, "DERIVED"


def _plain_int(v):
    """An int that is not a bool. `isinstance(True, int)` is True in Python."""
    return isinstance(v, int) and isinstance(v, bool) is False


def _is_ratio(measure):
    return str(measure or "").strip().upper() in (
        "RR", "OR", "HR", "RATE_RATIO", "RATERATIO", "IRR")


def _absolute_from_ratio(measure, p0, v):
    """One baseline risk and one ratio -> the absolute risk it implies.

    ⛔ THE MEASURE DECIDES THE ARITHMETIC, NOT JUST THE CAVEAT. This function
    exists because `_absolute_rows` previously took `measure` and never read
    it: every ratio was multiplied by the baseline, so a hazard ratio was
    converted as though it were a risk ratio. A parameter that is accepted and
    ignored is worse than one that is absent, because the call site looks
    correct. At p0 = 200/1000 and HR 0.7636 the multiplication gives 152.7
    where the survival form gives 156.7.

    ⚠️ AND THE COINCIDENCE THAT LET IT SURVIVE REVIEW: on the SGLT2_HF page,
    200 x 0.7835 = 156.70 (the WRONG value for the three-component pool) and
    the CORRECT value for the harmonised pool's HR 0.7636 is 156.67. A reviewer
    spot-checking one table against the other pool's ratio would have confirmed
    the page was fine. This is why the regression test carries a fixture
    instead of an eyeball.
    """
    m = str(measure or "").strip().upper()
    if m == "RR":
        # A risk ratio acts on the risk directly. Multiplication is exact.
        return p0 * v
    if m == "OR":
        # An odds ratio acts on the ODDS: o1 = o0 * OR, then back to a risk.
        odds = (p0 / (1.0 - p0)) * v
        return odds / (1.0 + odds)
    if m in ("HR", "RATE_RATIO", "RATERATIO", "IRR"):
        # A hazard ratio and a rate ratio both act multiplicatively on the
        # instantaneous hazard, so S1 = S0**ratio and p1 = 1 - (1 - p0)**ratio.
        # This is EXACT under proportional hazards -- it is not an extra
        # assumption on top of the multiplication, it is what proportional
        # hazards actually implies. The multiplication is the RARE-EVENT
        # approximation to it, and the two diverge as p0 grows.
        return 1.0 - (1.0 - p0) ** v
    # An unrecognised measure gets no arithmetic rather than a guess.
    return None


def _absolute_rows(measure, point, lo, hi, grid=None):
    """Baseline risk + ratio -> absolute risk, by the arithmetic the MEASURE
    licenses. Arithmetic, not a transfer claim.

    `grid` is a sequence of baselines per 1000. When the caller supplies
    OBSERVED control-arm risks they are used; otherwise BASELINE_GRID, the
    assumed range, is used AND THE TABLE SAYS WHICH.
    """
    rows = []
    for b in (grid if grid else BASELINE_GRID):
        cell = []
        for v in (point, lo, hi):
            if not isinstance(v, (int, float)):
                cell.append(None)
                continue
            r = _absolute_from_ratio(measure, b / 1000.0, v)
            cell.append(None if r is None else round(r * 1000.0, 1))
        if cell[0] is None:
            continue
        rows.append((b, cell[0], cell[1], cell[2], round(cell[0] - b, 1)))
    return rows


def _observed_baselines(canon, oid):
    """Control-arm risks OBSERVED in the trials contributing this outcome.

    Handbook 14.1.3 asks for a range of plausible baseline risks. An assumed
    grid satisfies the letter; the control arms of the very trials being
    pooled satisfy it AND carry provenance -- every point is a risk some real
    population in this evidence actually had, and the trial it came from is
    named beside it.

    Returns a list of (label, risk_per_1000, source) or [] when no control
    arm is held, in which case the caller falls back to the assumed grid and
    SAYS SO on the table.
    """
    rows = []
    for t in ((canon.get("inputs") or {}).get("trials") or []):
        if isinstance(t, dict) is False:
            continue
        e = (t.get("by_outcome") or {}).get(oid)
        if isinstance(e, dict) is False:
            continue
        c = e.get("control")
        if isinstance(c, dict) is False:
            continue
        ev, n = c.get("events"), c.get("n")
        ev_ok = isinstance(ev, int) and isinstance(ev, bool) is False
        n_ok = isinstance(n, int) and isinstance(n, bool) is False and n > 0
        if ev_ok and n_ok and 0 <= ev <= n:
            rows.append((t.get("id") or t.get("nct") or "?", ev, n))
    if len(rows) == 0:
        return []
    risks = [(nm, ev / float(n)) for nm, ev, n in rows]
    tot_e = sum(r[1] for r in rows)
    tot_n = sum(r[2] for r in rows)
    lo = min(risks, key=lambda x: x[1])
    hi = max(risks, key=lambda x: x[1])
    # ROUNDED AT SOURCE, not in the formatter. The baseline is both printed
    # and multiplied, and a page that prints 84.2 while multiplying by
    # 84.21052631578947 is not recomputable from the cells it shows. One
    # decimal place is below the resolution of any control arm here.
    out = [("lowest observed", round(lo[1] * 1000.0, 1),
            "the control arm of %s" % lo[0]),
           ("pooled", round((tot_e / float(tot_n)) * 1000.0, 1),
            "all control arms, %d of %d" % (tot_e, tot_n))]
    if hi[0] != lo[0]:
        out.append(("highest observed", round(hi[1] * 1000.0, 1),
                    "the control arm of %s" % hi[0]))
    return out


NEEDS_HORIZON = ("HR", "RATE_RATIO", "RATERATIO", "IRR")

_HORIZON_PERIOD = re.compile(
    r"[0-9]+(\.[0-9]+)?\s*(week|wk|month|mo|year|yr|day)s?", re.I)
_HORIZON_OUTCOME_FIELDS = ("follow_up", "time_frame", "timeframe", "horizon",
                           "follow_up_window")
_HORIZON_TRIAL_FIELDS = ("registered_primary_timeframe", "follow_up",
                         "median_follow_up", "duration")


def _needs_horizon(measure):
    return str(measure or "").strip().upper() in NEEDS_HORIZON


def _horizon_text(v):
    if isinstance(v, str) and v.strip() and _HORIZON_PERIOD.search(v):
        return v.strip()
    return None


def _time_horizon(canon, oid):
    """(text, field, caveat) for THIS outcome, or (None, None, None).

    Outcome-specific fields first. A trial-level period is accepted only from
    a trial that CONTRIBUTES this outcome -- lending another trial's follow-up
    to this row is the same error the participants column just shed.

    `caveat` is the object's own stored warning about the field, quoted, not
    paraphrased. It exists on the registered-timeframe fields and says that a
    registered primary timeframe is not necessarily overall follow-up.
    """
    trials = (canon.get("inputs") or {}).get("trials") or []
    for t in trials:
        if isinstance(t, dict) is False:
            continue
        e = (t.get("by_outcome") or {}).get(oid)
        if isinstance(e, dict) is False:
            continue
        for f in _HORIZON_OUTCOME_FIELDS:
            s = _horizon_text(e.get(f))
            if s:
                return s, "by_outcome.%s" % f, None
    for t in trials:
        if isinstance(t, dict) is False:
            continue
        if isinstance((t.get("by_outcome") or {}).get(oid), dict) is False:
            continue
        for f in _HORIZON_TRIAL_FIELDS:
            s = _horizon_text(t.get(f))
            if s:
                basis = t.get(f + "_basis")
                cav = basis.strip() if isinstance(basis, str) and basis.strip() \
                    else None
                return s, "trial.%s" % f, cav
    return None, None, None


def _horizon_assumption_html(measure, text, field, caveat):
    """The assumption, stated. Fixed sentences plus quotations, no prose."""
    m = str(measure or "").strip().upper()
    if m in ("RATE_RATIO", "RATERATIO", "IRR"):
        what = ("A rate ratio counts repeat events per unit of time. The table "
                "below converts it with 1 - (1 - p)**ratio, which assumes the "
                "rate is constant over the period rather than assuming events "
                "are rare enough for a rate and a risk to coincide.")
    else:
        what = ("A hazard ratio is not a risk ratio, so the table below does "
                "NOT multiply it by the baseline. It uses 1 - (1 - p)**HR, "
                "which is what proportional hazards implies -- proportional "
                "hazards is the justification for this formula, not an extra "
                "assumption needed to excuse multiplying.")
    out = ("  <div class='absent-state'><strong>What this conversion "
           "assumes.</strong> %s The absolute numbers are risks OVER THAT "
           "PERIOD, not lifetime risks. Period, quoted from <code>%s</code>: "
           "<em>%s</em>." % (_e(what), _e(field), _e(text)))
    if caveat:
        out += (" The object stores this warning about that field, quoted: "
                "<em>%s</em>" % _e(caveat))
    return out + "</div>" + chr(10)


def _horizon_declined_html(measure):
    return ("  <div class='absent-state'><strong>"
            "NOT_ESTIMABLE_NO_TIME_HORIZON.</strong> The summary measure is "
            "%s, which describes events per unit of time. Converting it to an "
            "absolute risk requires a stated period, and no trial contributing "
            "this outcome records one. No absolute effect is shown rather than "
            "one computed over an unstated period.</div>" % _e(measure)
            + chr(10))


def _declination(canon, oid):
    """What absolute_effect.py says about this block, in its own words."""
    try:
        import importlib.util
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "absolute_effect.py")
        spec = importlib.util.spec_from_file_location("_ae_for_sof", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        r = mod.derive(canon, oid)
    except Exception as exc:
        return {"state": "NOT_ASSESSABLE",
                "reason": "absolute_effect could not be consulted here (%s). That "
                          "is a fact about this page's build, not about the "
                          "evidence." % type(exc).__name__}
    return {"state": r.get("state"), "reason": r.get("reason") or ""}


def sof_card(canon, p=None):
    """SUMMARY OF FINDINGS -- Handbook 14. Returns "" when nothing is held."""
    blocks = _blocks(canon)
    if not blocks:
        return ""
    n_part, n_trials = _participants(canon)
    inner = ("  <p><small>Format: %s. The FIELDS are fixed by the Handbook so a "
             "reader can check the shape of this table as well as its numbers."
             "</small></p>\n" % _e(HANDBOOK_SOF))
    any_row = False
    for oid, rec in blocks:
        pooled = rec.get("pooled") or {}
        measure = pooled.get("measure")
        point, lo, hi = pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")
        k = rec.get("k") if isinstance(rec.get("k"), int) else n_trials
        inner += "  <h3>%s</h3>\n" % _e(oid.replace("_", " "))
        if pooled.get("withdrawn"):
            inner += ("  <div class='absent-state'>This pooled estimate is "
                      "WITHDRAWN by the object itself. No relative or absolute "
                      "effect is shown for it.</div>\n")
            continue
        if point is None:
            inner += ("  <div class='absent-state'>No pooled point estimate is "
                      "held for this outcome, so no relative effect and no "
                      "absolute effect can be shown.</div>\n")
            continue
        any_row = True
        n_row, k_row, n_state = _participants_for(canon, oid, rec.get("k"))
        if n_state == "DERIVED":
            n_cell = _e(n_row)
            k_cell = _e(k_row)
        elif n_state == "PARTIAL_CELLS":
            n_cell = ("not held: per-arm counts for %s of %s studies"
                      % (_e(k_row), _e(k)))
            k_cell = _e(k) if k else "not held"
        else:
            n_cell = "not held"
            k_cell = _e(k) if k else "not held"
        inner += ("  <table>\n"
                  "    <tr><th>Relative effect</th><th>No. participants analysed</th>"
                  "<th>No. studies</th></tr>\n"
                  "    <tr><td><strong>%s %s</strong> (%s to %s)</td>"
                  "<td>%s</td><td>%s</td></tr>\n  </table>\n"
                  % (_e(measure), _e(point), _e(lo), _e(hi),
                     n_cell, k_cell))
        inner += ("  <p><small>Participants is the number ANALYSED for this "
                  "outcome, summed from the same per-arm counts the effect "
                  "above is computed from -- not the number the trials "
                  "enrolled, which is a larger and different quantity. Where "
                  "some contributing trial holds no per-arm counts the cell "
                  "says so rather than showing a sum over the trials that "
                  "do, because a partial sum is not a total.</small></p>\n")
        _hz_txt, _hz_field, _hz_cav = (None, None, None)
        if _needs_horizon(measure):
            _hz_txt, _hz_field, _hz_cav = _time_horizon(canon, oid)
        if _is_ratio(measure) and _needs_horizon(measure) and _hz_txt is None:
            inner += _horizon_declined_html(measure)
        elif _is_ratio(measure):
            if _hz_txt is not None:
                inner += _horizon_assumption_html(
                    measure, _hz_txt, _hz_field, _hz_cav)
            observed = _observed_baselines(canon, oid)
            rows = _absolute_rows(
                measure, point, lo, hi,
                [bl for _lab, bl, _src in observed] or None)
            body = ""
            for b, pt, l, h, diff in rows:
                body += ("    <tr><td>%s per 1000</td><td>%s per 1000</td>"
                         "<td>%s to %s</td><td>%s</td></tr>\n"
                         % (b, pt, _e(l), _e(h), diff))
            if observed:
                kind = "Observed baseline risk"
                prov = ("The baselines below are OBSERVED. Each is a control-"
                        "arm risk from a trial in this pool, and the trial it "
                        "came from is named: " +
                        "; ".join(
                            "%s = %.1f per 1000, from %s"
                            % (lab, bl, whence)
                            for lab, bl, whence in observed) + ". ")
            else:
                kind = "Assumed baseline risk"
                prov = ("No control arm is held for this outcome, so the "
                        "baselines below are ASSUMED and belong to no population "
                        "in this evidence. ")
            inner += ("  <h3>Absolute effect, at baseline risks you choose</h3>\n"
                      "  <p><small>" + _e(prov) + "Handbook 14.1.3 asks "
                      "for absolute effects at STATED baseline risks. This is "
                      "arithmetic -- the relative effect multiplied by a baseline "
                      "-- and it asserts nothing about whether this evidence "
                      "transfers to that population. <strong>The table is "
                      "arithmetic; the refusal below is about transfer. Different "
                      "claims, kept apart.</strong></small></p>\n"
                      "  <table>\n    <tr><th>" + kind + "</th>"
                      "<th>Risk with intervention</th><th>95% CI</th>"
                      "<th>Difference</th></tr>\n" + body + "  </table>\n")
            d = _declination(canon, oid)
            if d.get("state") != "EMITTED":
                inner += ("  <div class='absent-state'><strong>What the absolute-"
                          "effect gate says about this outcome (%s):</strong> %s"
                          "</div>\n" % (_e(d.get("state")), _e(d.get("reason"))))
        else:
            inner += ("  <div class='absent-state'>The summary measure is %s, "
                      "which is not a ratio, so there is no baseline risk to "
                      "apply it to and no absolute-effect grid is shown. An NNT "
                      "derived from a mean difference would be fabrication."
                      "</div>\n" % _e(measure or "not stated"))
        grade = rec.get("grade") if isinstance(rec.get("grade"), dict) else {}
        cert = grade.get("certainty")
        doms = grade.get("domains") if isinstance(grade.get("domains"), dict) else {}
        if cert or doms:
            rows = ""
            for dk, dv in (doms or {}).items():
                rating = dv.get("rating") if isinstance(dv, dict) else None
                rows += ("    <tr><td>%s</td><td>%s</td></tr>\n"
                         % (_e(dk.replace("_", " ")), _e(rating or "not rated")))
            inner += ("  <h3>Certainty</h3>\n  <table>\n"
                      "    <tr><th>Domain</th><th>Rating</th></tr>\n" + rows
                      + "  </table>\n"
                      + ("  <p><small>Overall certainty as stored: <strong>%s"
                         "</strong>. The domain ratings are reproduced as STORED "
                         "JUDGEMENTS; this card does not compute or revise them."
                         "</small></p>\n" % _e(cert) if cert else ""))
        else:
            inner += ("  <div class='absent-state'>No GRADE certainty is stored "
                      "for this outcome. The Handbook's SoF table carries one; "
                      "this object does not, and the cell is left declared rather "
                      "than filled.</div>\n")
    if not any_row:
        return ("  <div class='absent-state'>Every pooled outcome on this object "
                "is withdrawn or holds no point estimate, so no Summary of "
                "Findings row can be built. The outcomes are listed above with "
                "the reason for each.</div>\n" if inner else "")
    return inner


def etd_coverage_card(canon, p=None):
    """EVIDENCE-TO-DECISION COVERAGE MAP -- Handbook 15.6.

    THIS TAB DECLINES MOST OF ITS CELLS AND THAT IS THE HANDBOOK-CORRECT ANSWER. An
    evidence-to-decision framework needs values, resource use, equity, acceptability and
    feasibility. The Handbook places those with the review authors and a guideline panel --
    they are NOT derivable from trial data and never were. So the deliverable is a COMPLETE,
    DECLARED map of which considerations this review can inform and which it cannot. The
    empty cells are the point.

    RULING 1 -- TWO STATES ONLY, AND `PARTIALLY INFORMED` IS ABOLISHED.

    This card previously emitted PARTIALLY INFORMED, CANNOT BE DETERMINED and NOT APPLICABLE
    alongside INFORMED and NOT ADDRESSED, and scored anything beginning INFORMED or PARTIALLY
    as informed. The decisive case was `Is the problem a priority?`, which printed PARTIALLY
    INFORMED beside the reason "whether the problem is a priority in a given jurisdiction is
    not a property of those trials" -- A MARK CONTRADICTING THE REASON PRINTED NEXT TO IT.

    That is the third independent instance of this defect: a probe here that fell back
    question -> title so the named field was not the field doing the work; AGYW's authored
    block, which called the same row PARTIALLY INFORMED; and this. Three instances make it a
    class, not a slip. A third state exists only to soften, and softening is what this tab
    exists to refuse.

    SO: INFORMED -- and it must NAME THE FIELD that informs it -- or NOT ADDRESSED. A mark
    and its reason are now generated from ONE decision, so a row cannot print a reason that
    denies its own mark.

    ABOLISHING THE THIRD STATE IS NOT THE SAME AS DEMOTING EVERYTHING IN IT. Each of the
    three partials was decided on whether the review holds evidence a panel would USE for
    that consideration, and they did not go the same way:
      problem      DEMOTED. Trial populations say who was studied, not whether the problem
                   outranks competing claims on the same budget. Its own reason says so.
      undesirable  INFORMED, naming the harms field. "Two summary categories, not a full
                   harms review" QUALIFIES the mark; it does not deny it.
      equity       INFORMED, naming the registry extraction. Who was eligible -- sex, age
                   bounds, countries -- is evidence a panel uses for equity, because who was
                   excluded is the equity question.

    RULING 2 -- RENDER THE MAP ALWAYS; SCORE THE PANEL EMPTY WHEN NOTHING IS INFORMED.

    This card used to DROP the twelve-row table when nothing was informed, returning one
    sentence instead -- so 112 of 141 live topics showed no map at all, which is precisely
    where a complete declared map of the unanswered is most informative. The sentence "the
    empty cells are the point" survived in the branch where cells are FILLED and the table
    was dropped in the branch where they are ALL EMPTY.

    THE GUARD THAT MOTIVATED THAT IS CORRECT AND IS PRESERVED, NOT OVERRULED: a twelve-row
    table of NOT ADDRESSED must not register as a populated tab and jump pages to 8 of the
    ruled 8 in one pass. The two concerns are separable and were only ever conflated because
    the content detector counts RENDERED ELEMENTS:

        what a READER SEES   -- the full map, always
        what a COUNTER SCORES -- empty, when nothing is informed

    So when informed == 0 the map is wrapped in a container carrying
    `data-scores-as-empty="1"`, and `projectors.tabbed_body` excludes marked regions before
    applying the content floor. The scorer now reads DERIVED STATE declared by the producer
    instead of inferring it from the presence of a <table>. THE TAB COUNT MUST NOT MOVE
    BECAUSE OF THIS CHANGE, and the control asserts exactly that, per object, both ways.
    """
    blocks = _blocks(canon)
    live = [(oid, rec) for oid, rec in blocks
            if not (rec.get("pooled") or {}).get("withdrawn")
            and (rec.get("pooled") or {}).get("point") is not None]

    effect_field = ("results.by_outcome.%s.pooled" % live[0][0]) if live else None
    certainty_field = None
    for oid, rec in live:
        g = rec.get("grade")
        if isinstance(g, dict) and g.get("certainty"):
            certainty_field = "results.by_outcome.%s.grade.certainty" % oid
            break
    harms_field = next((k for k in sorted(canon)
                        if isinstance(k, str) and k.startswith("harms_")), None)
    registry_field = next((k for k in sorted(canon)
                           if isinstance(k, str)
                           and k.startswith("registry_extraction_")), None)

    # (mark, reason, field). `field` is REQUIRED whenever the mark is INFORMED and is
    # asserted by the control: an informed mark nobody can check against a named field is
    # the same defect as a k that changes without a named trial list.
    ADDRESSED = "NOT ADDRESSED"
    answers = {
        "problem_is_a_priority": (
            ADDRESSED,
            "Whether a problem is a priority ranks it against competing claims on the same "
            "budget. The trial populations recorded here say who was studied; they are not "
            "a property that can rank the problem, and this review does not rank it.",
            None),
        "desirable_anticipated_effects": (
            ("INFORMED",
             "The pooled relative effect and its interval, with an absolute-effect grid, "
             "are in the Summary of Findings tab.", effect_field)
            if effect_field else
            (ADDRESSED, "No pooled estimate is held for any outcome.", None)),
        "undesirable_anticipated_effects": (
            ("INFORMED",
             "Serious adverse events and deaths per arm, with denominators, are read from "
             "the registry and shown in the Extraction tab. That is two summary categories "
             "and not a full harms review, which bounds what it supports rather than "
             "withdrawing it.", harms_field)
            if harms_field else
            (ADDRESSED,
             "No harms block is held on this object. THAT IS NOT A FINDING OF NO HARM -- it "
             "is an absence of extraction, and a panel must treat it as unmeasured rather "
             "than as reassurance.", None)),
        "certainty_of_evidence": (
            ("INFORMED",
             "GRADE certainty is stored and is shown beside each outcome in the Summary of "
             "Findings tab.", certainty_field)
            if certainty_field else
            (ADDRESSED, "No GRADE certainty is stored for any outcome.", None)),
        "values": (
            ADDRESSED,
            "No study of how people weigh these outcomes was sought or synthesised. This is "
            "a review of trial effects.", None),
        "balance_of_effects": (
            ADDRESSED,
            "A balance requires values. With values unaddressed, a balance statement would "
            "be the review author's preference wearing a panel's authority.", None),
        "resources_required": (
            ADDRESSED, "No cost input of any kind is held.", None),
        "certainty_of_resource_evidence": (
            ADDRESSED,
            "No resource evidence is held, so there is no certainty to rate in it.", None),
        "cost_effectiveness": (
            ADDRESSED, "No economic evaluation was sought.", None),
        "equity": (
            ("INFORMED",
             "Eligibility as registered -- sex, age bounds and countries -- is read from "
             "the registry and shown in the Extraction tab. Who was eligible bounds who the "
             "result can speak for, and who was excluded is the equity question.",
             registry_field)
            if registry_field else
            (ADDRESSED, "No registry extraction is held on this object.", None)),
        "acceptability": (
            ADDRESSED, "Acceptability studies are outside this review's scope.", None),
        "feasibility": (
            ADDRESSED,
            "Implementation and delivery are outside this review's scope.", None),
    }

    rows = ""
    informed = 0
    for key, question in ETD_DOMAINS:
        ans, why, field = answers.get(key, (ADDRESSED, "Not held.", None))
        if ans == "INFORMED":
            informed += 1
            why = "%s Informed by <code>%s</code>." % (why, _e(field))
            cls = "ok"
        else:
            cls = "warn"
        rows += ("    <tr class='%s'><td>%s</td><td><strong>%s</strong></td>"
                 "<td><small>%s</small></td></tr>\n"
                 % (cls, _e(question), _e(ans), why))

    table = ("  <p><small>Format: %s. The twelve considerations below are the GRADE "
             "Evidence-to-Decision framework, reproduced in full whether or not this review "
             "can answer them.</small></p>\n"
             "  <table>\n    <tr><th>Consideration</th><th>Answer</th>"
             "<th>From this review</th></tr>\n%s  </table>\n"
             % (_e(HANDBOOK_ETD), rows))

    if informed == 0:
        # THE MAP IS STILL RENDERED IN FULL. The wrapper is what the COUNTER reads, not what
        # the reader loses: `data-scores-as-empty` tells tabbed_body to exclude this region
        # before applying the content floor, so an all-declining map cannot flatter the tab
        # count while the reader still gets every row and every reason.
        return ("  <div class='absent-state' data-scores-as-empty=\"1\">\n"
                "  <p><strong>This review can inform NONE of the twelve GRADE "
                "Evidence-to-Decision considerations.</strong> The full map is reproduced "
                "below so the gap is legible by row, and this panel is scored as carrying "
                "no content, because it carries none.</p>\n%s  </div>\n" % table)

    return (table +
            "  <div class='absent-state'><strong>%d of %d considerations informed; %d not "
            "addressed.</strong> The empty cells are the point. An evidence-to-decision "
            "framework needs values, resource use, equity, acceptability and feasibility; "
            "the Handbook places those with the review authors and a guideline panel, and "
            "they are not derivable from trial data. A panel handed a complete map of what "
            "is unanswered is better served than one handed prose that reads as though it "
            "covered all twelve. Every informed row names the field it is informed by.</div>"
            "\n" % (informed, len(ETD_DOMAINS), len(ETD_DOMAINS) - informed))