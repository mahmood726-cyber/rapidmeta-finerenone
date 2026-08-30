# -*- coding: utf-8 -*-
"""Renderers for the 2026-08-30 dapivirine layers: the bibliographic screen,
the registry extraction, harms, and the four reader renderings.

WHY THIS FILE EXISTS, AND IT IS THE OLDEST DEFECT IN THIS REPOSITORY.

Three blocks were written into the object -- a 1,443-record per-record
screening ledger, a machine extraction with an arm-code inversion finding, and
four reader renderings with a passing consistency check -- and then the page
was grepped for them. `bibliographic_screen` 0 hits. `reader_renderings` 0
hits. `UChoose` 0 hits. `seven-fold` 0 hits. NONE OF IT REACHED A READER.

`build_tabbed.py` renders a FIXED SET OF NAMED CARDS into a FIXED SET OF NAMED
SLOTS. A new top-level key in the store is invisible by construction -- not
dropped with a warning, not rendered as unknown, simply never looked at. The
builder's own comments say this happened before, twice, in the same words:

    "The published comparison had NO RENDERER. It has been written into
     objects since ARNI and reached a reader on no surface."

    "A property a reader cannot see is not a property the page has."

So the work of an afternoon existed only in a JSON file that no judge, no
reviewer and no reader in Uganda would ever open. Writing to the store is not
delivering. THE ASSERTION HAS TO HOLD AT THE RECEIVER.

EVERY CARD HERE IS GUARDED ON KEY PRESENCE and returns "" when its block is
absent, so this module is a no-op on the other topics in the corpus and cannot
change any page that does not carry these keys.
"""
import html


def _e(x):
    return html.escape("—" if x is None else str(x))


def _card(title, inner, cls="card"):
    return "<div class='%s'>\n  <h2>%s</h2>\n%s</div>\n" % (cls, _e(title), inner)


def _para(s):
    return "  <p>%s</p>\n" % _e(s)


def _small(s):
    return "  <p><small>%s</small></p>\n" % _e(s)


def _h3(s):
    return "  <h3>%s</h3>\n" % _e(s)


# --------------------------------------------------------------- screening --
def bibliographic_screen_card(canon, p=None):
    """The per-record screen, its denominator, and the two resolved candidates.

    THE DENOMINATOR IS RENDERED WITH THE DECISIONS, never above or below them
    on their own. A decision table without its denominator is the defect this
    whole block was written to correct, and rendering it that way would
    reproduce the defect in the artefact that reports it.
    """
    b = canon.get("bibliographic_screen_2026_08_30") or {}
    if not b:
        return ""
    den = b.get("denominator") or {}
    dec = b.get("decisions") or {}
    n = den.get("records_screened")
    if not n or not dec:
        return ""

    rows = ""
    for k in sorted(dec, key=lambda x: -dec[x]):
        cls = "warn" if k in ("UNDECIDABLE", "PASS_OUTSIDE_REGISTRY_SET") else ""
        rows += ("    <tr class='%s'><td><code>%s</code></td>"
                 "<td><strong>%s of %s</strong></td>"
                 "<td>%s%%</td></tr>\n"
                 % (cls, _e(k), dec[k], n, round(100.0 * dec[k] / n, 1)))

    src = b.get("sources") or {}
    srows = ""
    for name, s in src.items():
        srows += ("    <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n"
                  % (_e(name), _e(s.get("status")), _e(s.get("reported")),
                     _e(s.get("retrieved"))))

    miss = b.get("candidate_search_misses_RESOLVED") or {}
    mrows = ""
    for k, v in miss.items():
        if not isinstance(v, dict):
            continue
        mrows += ("    <tr class='warn'><td><code>%s</code><br><small>%s</small></td>"
                  "<td>%s</td><td><strong>%s</strong><br><small>%s</small></td></tr>\n"
                  % (_e(k), _e(v.get("cited_by")), _e(v.get("what_it_is")),
                     _e(v.get("verdict")), _e(v.get("reason"))))

    nt = b.get("negative_test") or {}
    inner = (
        _para(b.get("_what"))
        + "  <div class='absent-state'>%s</div>\n" % _e(b.get("why_it_exists"))
        + _h3("Sources, reported against retrieved")
        + "  <table>\n    <tr><th>Source</th><th>Status</th>"
          "<th>Reported</th><th>Retrieved</th></tr>\n" + srows + "  </table>\n"
        + _small(b.get("europe_pmc_truncation_CLOSED", {}).get("now", ""))
        + _h3("Every screened record, by decision")
        + _para(den.get("_what_the_denominator_is_OF"))
        + "  <table>\n    <tr><th>Decision</th><th>Records</th>"
          "<th>Share</th></tr>\n" + rows
        + "    <tr><td><strong>total</strong></td><td><strong>%s</strong></td>"
          "<td>100.0%%</td></tr>\n" % b.get("decisions_sum_to_the_denominator", n)
        + "  </table>\n"
        + _small("Full ledger, one row per record with the rule that decided "
                 "it and the field the rule read: %s"
                 % b.get("ledger_is_at", ""))
    )
    if mrows:
        inner += (_h3("Candidate search misses — every one named and resolved")
                  + _para(miss.get("what_a_candidate_miss_IS"))
                  + "  <table>\n    <tr><th>Registration</th><th>What it is</th>"
                    "<th>Verdict</th></tr>\n" + mrows + "  </table>\n"
                  + _para(miss.get("so")))
    if nt:
        inner += (_h3("The screen was shown to be able to fail")
                  + _para(nt.get("what"))
                  + _small("planted miss scored %s · planted editorial scored %s · %s"
                           % (nt.get("planted_miss_scored"),
                              nt.get("planted_editorial_scored"),
                              nt.get("controls_are_not_in_the_denominator"))))
    res = b.get("residual_NAMED_not_swept") or {}
    if res:
        inner += _h3("What is still open")
        for k, v in res.items():
            inner += _para("%s — %s %s" % (k, v.get("n", ""), v.get("what", "")))
            for extra in ("how_far_they_were_taken",
                          "what_is_therefore_still_open", "what_they_mostly_are"):
                if v.get(extra):
                    inner += _small(v[extra])
    inner += "  <div class='absent-state'>%s</div>\n" % _e(
        b.get("the_instrument_and_its_unmeasured_error", ""))
    return _card("Bibliographic screen — every record, with its reason", inner)


# -------------------------------------------------------------- extraction --
def registry_extraction_card(canon, p=None):
    """Participant flow, the arm-code inversion, and what the posted results
    answer in RoB 2."""
    r = canon.get("registry_extraction_2026_08_30") or {}
    if not r:
        return ""
    inv = r.get("THE_ARM_CODE_INVERSION") or {}
    flow = r.get("participant_flow") or {}

    grows = ""
    for nct, v in flow.items():
        mods = v.get("groups_by_module") or {}
        for mod, gmap in mods.items():
            idx0 = gmap.get(sorted(gmap)[0]) if gmap else ""
            cls = "warn" if (nct == "NCT01539226"
                             and mod == "outcome_measures") else ""
            grows += ("    <tr class='%s'><td><code>%s</code></td><td>%s</td>"
                      "<td><strong>%s</strong></td></tr>\n"
                      % (cls, _e(nct), _e(mod), _e(idx0)))

    frows = ""
    for nct, v in flow.items():
        an = v.get("primary_outcome_analysed") or {}
        tot = sum(an.values()) if an else 0
        rand = v.get("randomised")
        frows += ("    <tr><td><code>%s</code></td><td>%s</td><td>%s</td>"
                  "<td><strong>%s of %s</strong> (%s%%)</td></tr>\n"
                  % (_e(nct), _e(rand),
                     _e(" / ".join("%s %s" % (k, x)
                                   for k, x in (v.get("started") or {}).items())),
                     tot, rand,
                     round(100.0 * tot / rand, 2) if rand else "—"))

    rob = r.get("what_the_posted_results_ANSWER_in_RoB_2") or {}
    inner = (
        _para(r.get("_what"))
        + _h3("The index means different arms in different modules of one registration")
        + "  <div class='absent-state'>%s</div>\n" % _e(inv.get("finding", ""))
        + "  <table>\n    <tr><th>Registration</th><th>Module</th>"
          "<th>What index 000 is</th></tr>\n" + grows + "  </table>\n"
        + _para(inv.get("why_it_matters"))
        + _small(inv.get("verified_by"))
        + _small(inv.get("and_the_stored_2x2s_were_CHECKED_against_it"))
        + _h3("Participant flow and the analysis population")
        + "  <table>\n    <tr><th>Registration</th><th>Randomised</th>"
          "<th>Started, per arm</th><th>Analysed for the primary</th></tr>\n"
        + frows + "  </table>\n"
    )
    ap = r.get("analysis_populations_VERBATIM") or {}
    if ap:
        inner += _h3("The analysis populations, verbatim")
        for k, v in ap.items():
            if k.startswith(("_", "field", "this_supersedes")):
                continue
            inner += _para("%s — “%s”" % (k, v))
        inner += _small(ap.get("this_supersedes", ""))
    if rob:
        inner += _h3("What the posted results answer in RoB 2")
        inner += "  <div class='absent-state'>%s</div>\n" % _e(
            rob.get("⚠️_this_is_evidence_not_a_rating", ""))
        for key in ("3.1_outcome_data_for_all_or_nearly_all",
                    "2.6_appropriate_analysis_for_the_effect_of_assignment"):
            q = rob.get(key) or {}
            if not q:
                continue
            inner += _para("%s — was %s, now %s"
                           % (key, q.get("was"), q.get("answer")))
            for sub in ("reason", "the_distinction_that_matters",
                        "what_is_still_NOT_answered"):
                if q.get(sub):
                    inner += _small(q[sub])
            ar = q.get("arithmetic") or {}
            for nct, txt in ar.items():
                inner += _small("%s: %s" % (nct, txt))
        if rob.get("1.2_allocation_concealment_STILL_OPEN"):
            inner += ("  <div class='absent-state'>%s</div>\n"
                      % _e(rob["1.2_allocation_concealment_STILL_OPEN"]))
        d3 = rob.get("D3_DERIVED_FROM_THE_TOOLS_OWN_TABLE_2026_08_30") or {}
        if d3:
            inner += _h3("Domain 3, derived from the tool's own table and NOT applied")
            b4 = d3.get("before_this_evidence") or {}
            af = d3.get("with_3.1_answered_YES") or {}
            inner += ("  <table>\n    <tr><th>Answers</th><th>Domain</th>"
                      "<th>Table row</th></tr>\n"
                      "    <tr><td>3.1 = NI</td><td><strong>%s</strong></td>"
                      "<td><small>%s</small></td></tr>\n"
                      "    <tr class='warn'><td>3.1 = YES</td>"
                      "<td><strong>%s</strong></td><td><small>%s</small></td></tr>\n"
                      "  </table>\n"
                      % (_e(b4.get("domain")), _e(b4.get("table_row")),
                         _e(af.get("domain")), _e(af.get("table_row"))))
            inner += _para(d3.get("⚠️_A_PREDICTION_THIS_CONTRADICTS"))
            na = d3.get("⛔_DERIVED_AND_NOT_APPLIED") or {}
            inner += "  <div class='absent-state'>%s %s</div>\n" % (
                _e(na.get("what_is_NOT_done", "")), _e(na.get("why", "")))
            inner += _small(na.get("and_the_GRADE_step_that_depends_on_it", ""))
    return _card("Registry extraction — flow, populations, and the arm-code trap",
                 inner)


# ------------------------------------------------------------------ harms --
def harms_card(canon, p=None):
    """Harms, and the refusal to pool them."""
    h = canon.get("harms_2026_08_30") or {}
    if not h:
        return ""
    inner = _para(h.get("_what"))
    for label, key in (("Serious adverse events", "serious_adverse_events"),
                       ("Deaths", "deaths")):
        blk = h.get(key) or {}
        per = blk.get("per_trial") or {}
        if not per:
            continue
        rows = ""
        for nct, v in per.items():
            d, pl, rr = v.get("dapivirine", {}), v.get("placebo", {}), v.get("rr", {})
            rows += ("    <tr><td><code>%s</code></td>"
                     "<td>%s / %s</td><td>%s / %s</td>"
                     "<td><strong>%s</strong> (%s to %s)</td></tr>\n"
                     % (_e(nct), d.get("events"), d.get("n"),
                        pl.get("events"), pl.get("n"),
                        rr.get("point"), rr.get("ci_low"), rr.get("ci_high")))
        inner += (_h3(label)
                  + "  <table>\n    <tr><th>Registration</th>"
                    "<th>Dapivirine</th><th>Placebo</th>"
                    "<th>Risk ratio (95% CI)</th></tr>\n" + rows + "  </table>\n")
        np_ = blk.get("⛔_NOT_POOLED") or {}
        if np_:
            inner += "  <div class='absent-state'>%s</div>\n" % _e(np_.get("why", ""))
            inner += _small(np_.get("the_statistic_that_shows_it", ""))
            inner += _small(np_.get("what_IS_reported_instead", ""))
            inner += _small(np_.get("and_this_is_not_a_safety_verdict", ""))
        if blk.get("not_pooled_either"):
            inner += _small(blk["not_pooled_either"])
        if blk.get("consistency"):
            inner += _small(blk["consistency"])
    inner += "  <div class='absent-state'>%s</div>\n" % _e(
        h.get("what_this_does_NOT_add", ""))
    inner += _small(h.get("why_the_registry_and_not_the_papers", ""))
    return _card("Harms — both trials, and why they are not pooled", inner)


# ------------------------------------------------------ reader renderings --
_LABEL = {"hta": "For a health-technology-assessment body",
          "guideline": "For a guideline panel",
          "clinician": "For a clinician",
          "public": "For the public"}


def reader_renderings_card(canon, p=None):
    """The same evidence for four readers, and the check that they agree."""
    r = canon.get("reader_renderings_2026_08_30") or {}
    if not r:
        return ""
    chk = r.get("consistency_check") or {}
    facts = r.get("shared_facts") or {}

    frows = ""
    for k, v in facts.items():
        frows += ("    <tr><td><code>%s</code></td><td><strong>%s</strong></td>"
                  "<td><small><code>%s</code></small></td></tr>\n"
                  % (_e(k), _e(v.get("v")), _e(v.get("path"))))

    arows = ""
    for row in (r.get("absolute_effect_table") or []):
        ci = row.get("prevented_ci") or ["", ""]
        nci = row.get("nnt_ci") or ["", ""]
        arows += ("    <tr><td>%s</td><td>%s</td><td>%s (%s to %s)</td>"
                  "<td>%s (%s to %s)</td></tr>\n"
                  % (row.get("baseline_per_100_woman_years"),
                     row.get("with_the_ring"),
                     row.get("infections_prevented_per_100_woman_years"),
                     ci[0], ci[1],
                     row.get("number_needed_to_use_for_one_year_to_prevent_one"),
                     nci[0], nci[1]))

    inner = (_para(r.get("_what"))
             + "  <div class='absent-state'>%s</div>\n"
               % _e(r.get("⭐_why_this_is_a_moat_and_not_four_documents", ""))
             + _h3("The check")
             + _para("%s numbers checked across %s renderings; %s untraceable. %s"
                     % (chk.get("numbers_checked"), chk.get("renderings_checked"),
                        len(chk.get("untraceable") or []),
                        "PASSES" if chk.get("PASSES") else "FAILS"))
             + _small(chk.get("what_it_does_NOT_check", "")))

    fired = r.get("THE_CHECK_FIRED_ON_ITS_FIRST_RUN") or {}
    if fired:
        inner += _small("It fired on its first run: %s %s"
                        % (fired.get("what_it_caught", ""),
                           fired.get("how_it_was_fixed", "")))
    nt = r.get("consistency_check_NEGATIVE_TEST") or {}
    if nt:
        inner += _small("And it is shown able to fail: %s Caught: %s. %s"
                        % (nt.get("what", ""), ", ".join(nt.get("caught") or []),
                           nt.get("⚠️_what_the_negative_test_does_NOT_prove", "")))
    miss = r.get("AN_ERROR_THE_CHECK_COULD_NOT_CATCH_AND_A_READING_DID") or {}
    if miss:
        inner += ("  <div class='absent-state'>An error the check could not "
                  "catch, and a reading did — %s %s %s</div>\n"
                  % (_e(miss.get("what_it_said", "")),
                     _e(miss.get("why_it_was_false", "")),
                     _e(miss.get("why_the_consistency_check_did_not_and_could_not_flag_it", ""))))

    inner += (_h3("The one fact table all four are drawn from")
              + "  <table>\n    <tr><th>Fact</th><th>Value</th>"
                "<th>Field it was read from</th></tr>\n" + frows + "  </table>\n")
    if arows:
        inner += (_h3("Absolute effect at a baseline risk the reader chooses")
                  + "  <table>\n    <tr><th>Baseline per 100 woman-years</th>"
                    "<th>With the ring</th><th>Infections prevented</th>"
                    "<th>Number needed for one year</th></tr>\n"
                  + arows + "  </table>\n")

    for key, blk in (r.get("renderings") or {}).items():
        inner += _h3(_LABEL.get(key, key))
        if key == "guideline":
            etd = blk.get("evidence_to_decision") or {}
            rows = ""
            for k, v in etd.items():
                cls = "warn" if str(v.get("answer", "")).startswith("⛔") else "ok"
                rows += ("    <tr class='%s'><td>%s</td>"
                         "<td><strong>%s</strong></td><td><small>%s</small></td></tr>\n"
                         % (cls, _e(k.replace("_", " ")), _e(v.get("answer")),
                            _e(v.get("from_this_review") or v.get("why") or "")))
            cov = blk.get("COVERAGE_OF_THE_FRAMEWORK") or {}
            inner += (_para(blk.get("_why_this_shape"))
                      + "  <table>\n    <tr><th>Consideration</th><th>Answer</th>"
                        "<th>From this review</th></tr>\n" + rows + "  </table>\n"
                      + "  <div class='absent-state'>%s of the framework "
                        "informed, %s not addressed. %s</div>\n"
                      % (_e(cov.get("informed_or_partially_informed")),
                         _e(cov.get("not_addressed")),
                         _e(cov.get("⭐_the_empty_cells_are_the_point", ""))))
            continue
        for k, v in blk.items():
            if k.startswith("_"):
                if k == "_reader":
                    inner += _small("Reader: %s" % v)
                continue
            if isinstance(v, str):
                if k.startswith("⛔") or k.startswith("⚠️"):
                    inner += "  <div class='absent-state'>%s</div>\n" % _e(v)
                else:
                    inner += _para(v)
            elif isinstance(v, dict):
                for kk, vv in v.items():
                    if isinstance(vv, str):
                        if kk.startswith(("⛔", "⚠️", "so")):
                            inner += "  <div class='absent-state'>%s</div>\n" % _e(vv)
                        else:
                            inner += _small("%s — %s" % (kk.replace("_", " "), vv))
        if key == "public":
            rd = blk.get("readability") or {}
            if rd:
                inner += _small(
                    "Readability: Flesch-Kincaid grade %s, reading ease %s, "
                    "%s words in %s sentences. %s"
                    % (rd.get("flesch_kincaid_grade"),
                       rd.get("flesch_reading_ease"), rd.get("words"),
                       rd.get("sentences"), rd.get("instrument")))

    inner += "  <div class='absent-state'>%s</div>\n" % _e(
        r.get("what_this_does_NOT_fix", ""))
    return _card("Four readers, one store — and the check that they agree", inner)
