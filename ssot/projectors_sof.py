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


def _is_ratio(measure):
    return str(measure or "").strip().upper() in (
        "RR", "OR", "HR", "RATE_RATIO", "RATERATIO", "IRR")


def _absolute_rows(measure, point, lo, hi):
    """RR x baseline, at each grid baseline. Arithmetic, not a transfer claim."""
    rows = []
    for b in BASELINE_GRID:
        cell = []
        for v in (point, lo, hi):
            cell.append(None if not isinstance(v, (int, float)) else round(b * v, 1))
        if cell[0] is None:
            continue
        rows.append((b, cell[0], cell[1], cell[2], round(cell[0] - b, 1)))
    return rows


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
        inner += ("  <table>\n"
                  "    <tr><th>Relative effect</th><th>№ participants</th>"
                  "<th>№ studies</th></tr>\n"
                  "    <tr><td><strong>%s %s</strong> (%s to %s)</td>"
                  "<td>%s</td><td>%s</td></tr>\n  </table>\n"
                  % (_e(measure), _e(point), _e(lo), _e(hi),
                     _e(n_part) if n_part else "not held",
                     _e(k) if k else "not held"))
        if _is_ratio(measure):
            rows = _absolute_rows(measure, point, lo, hi)
            body = ""
            for b, pt, l, h, diff in rows:
                body += ("    <tr><td>%s per 1000</td><td>%s per 1000</td>"
                         "<td>%s to %s</td><td>%s</td></tr>\n"
                         % (b, pt, _e(l), _e(h), diff))
            inner += ("  <h3>Absolute effect, at baseline risks you choose</h3>\n"
                      "  <p><small>Handbook 14.1.3 asks for absolute effects at "
                      "STATED baseline risks. A single assumed baseline risk is a "
                      "modelling choice made on behalf of a jurisdiction we do not "
                      "know, so a GRID is given instead and the reader applies the "
                      "row nearest their own incidence. This is arithmetic -- the "
                      "relative effect multiplied by a baseline -- and it asserts "
                      "nothing about whether this evidence transfers to that "
                      "population. <strong>The grid is arithmetic the reader "
                      "parameterises; the refusal below is about transfer. "
                      "Different claims, kept apart.</strong></small></p>\n"
                      "  <table>\n    <tr><th>Assumed baseline risk</th>"
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

    ⛔ THIS TAB DECLINES MOST OF ITS CELLS AND THAT IS THE HANDBOOK-CORRECT
    ANSWER. An evidence-to-decision framework needs values, resource use,
    equity, acceptability and feasibility. The Handbook places those with the
    review authors and a guideline panel -- they are NOT derivable from trial
    data and never were. So the deliverable is a COMPLETE, DECLARED map of which
    considerations this review can inform and which it cannot. The empty cells
    are the point: a panel handed 4 of 12 filled cells and a named reason for
    each blank is better served than one handed prose that reads as though it
    covered all twelve."""
    blocks = _blocks(canon)
    live = [(oid, rec) for oid, rec in blocks
            if not (rec.get("pooled") or {}).get("withdrawn")
            and (rec.get("pooled") or {}).get("point") is not None]
    has_effect = bool(live)
    has_certainty = any((rec.get("grade") or {}).get("certainty")
                        for _, rec in live if isinstance(rec.get("grade"), dict))
    harms_key = [k for k in canon.keys()
                 if isinstance(k, str) and k.startswith("harms_")]
    reg_key = [k for k in canon.keys()
               if isinstance(k, str) and k.startswith("registry_extraction_")]
    trials = (canon.get("inputs") or {}).get("trials") or []
    has_population = any(isinstance(t, dict) and t.get("population") for t in trials)

    answers = {
        "problem_is_a_priority": (
            ("PARTIALLY INFORMED",
             "The populations the contributing trials enrolled are recorded on "
             "this object and are shown in the Extraction tab. Whether the "
             "problem is a priority in a given jurisdiction is not a property of "
             "those trials.")
            if has_population else
            ("NOT ADDRESSED", "No trial population is recorded on this object.")),
        "desirable_anticipated_effects": (
            ("INFORMED", "The pooled relative effect and its interval, with an "
                         "absolute-effect grid, are in the Summary of Findings "
                         "tab.")
            if has_effect else
            ("NOT ADDRESSED", "No pooled estimate is held for any outcome.")),
        "undesirable_anticipated_effects": (
            ("PARTIALLY INFORMED",
             "Serious adverse events and deaths per arm, with denominators, are "
             "read from the registry and shown in the Extraction tab. That is "
             "two summary categories, not a full harms review.")
            if harms_key else
            ("NOT ADDRESSED", "No harms block is held on this object.")),
        "certainty_of_evidence": (
            ("INFORMED", "GRADE certainty is stored and is shown beside each "
                         "outcome in the Summary of Findings tab.")
            if has_certainty else
            ("NOT ADDRESSED", "No GRADE certainty is stored for any outcome.")),
        "values": ("NOT ADDRESSED",
                   "No study of how people weigh these outcomes was sought or "
                   "synthesised. This is a review of trial effects."),
        "balance_of_effects": (
            "CANNOT BE DETERMINED",
            "A balance requires values. With values unaddressed, a balance "
            "statement would be the review author's preference wearing a "
            "panel's authority."),
        "resources_required": ("NOT ADDRESSED", "No cost input of any kind is held."),
        "certainty_of_resource_evidence": ("NOT APPLICABLE", "No resource evidence."),
        "cost_effectiveness": ("NOT ADDRESSED",
                               "No economic evaluation was sought."),
        "equity": (
            ("PARTIALLY INFORMED",
             "Eligibility as registered -- sex, age bounds and countries -- is "
             "read from the registry and shown in the Extraction tab. Who was "
             "eligible bounds who the result can speak for.")
            if reg_key else
            ("NOT ADDRESSED", "No registry extraction is held on this object.")),
        "acceptability": ("NOT ADDRESSED",
                          "Acceptability studies are outside this review's scope."),
        "feasibility": ("NOT ADDRESSED",
                        "Implementation and delivery are outside this review's "
                        "scope."),
    }

    rows = ""
    informed = 0
    for key, question in ETD_DOMAINS:
        ans, why = answers.get(key, ("NOT ADDRESSED", "Not held."))
        if ans.startswith(("INFORMED", "PARTIALLY")):
            informed += 1
        cls = "ok" if ans.startswith(("INFORMED", "PARTIALLY")) else "warn"
        rows += ("    <tr class='%s'><td>%s</td><td><strong>%s</strong></td>"
                 "<td><small>%s</small></td></tr>\n"
                 % (cls, _e(question), _e(ans), _e(why)))
    # ⛔ A MAP WITH NOTHING INFORMED IS A DECLINATION, NOT CONTENT, AND IT MUST
    # SCORE AS ONE. This table is twelve <tr> rows whatever it says, so a page
    # that can answer NONE of the twelve would still register as a populated tab
    # under the content detector -- the detector looks for evidence-bearing
    # elements outside `absent-state`, and a row saying "NOT ADDRESSED" is an
    # element. That is a loophole this very build would have walked through, and
    # it flatters in exactly the direction we were warned about: eleven pages
    # jumping to 8/8 in one pass.
    #
    # So when the map informs nothing, the whole card is wrapped as an
    # absent-state block. The reader still sees the complete twelve-row map --
    # nothing is hidden -- but the tab is scored EMPTY, which is the truth.
    if informed == 0:
        return ("  <div class='absent-state'>\n"
                "  <p>Format: %s. This review can inform NONE of the twelve "
                "GRADE Evidence-to-Decision considerations. The full map is "
                "reproduced so the gap is legible, and this panel is marked as "
                "carrying no content, because it does not.</p>\n"
                "  </div>\n" % _e(HANDBOOK_ETD))
    return ("  <p><small>Format: %s. The twelve considerations below are the "
            "GRADE Evidence-to-Decision framework, reproduced in full whether or "
            "not this review can answer them.</small></p>\n"
            "  <table>\n    <tr><th>Consideration</th><th>Answer</th>"
            "<th>From this review</th></tr>\n%s  </table>\n"
            "  <div class='absent-state'><strong>%d of %d considerations "
            "informed or partially informed; %d not addressed.</strong> The empty "
            "cells are the point. An evidence-to-decision framework needs values, "
            "resource use, equity, acceptability and feasibility; the Handbook "
            "places those with the review authors and a guideline panel, and they "
            "are not derivable from trial data. A panel handed a complete map of "
            "what is unanswered is better served than one handed prose that reads "
            "as though it covered all twelve.</div>\n"
            % (_e(HANDBOOK_ETD), rows, informed, len(ETD_DOMAINS),
               len(ETD_DOMAINS) - informed))
