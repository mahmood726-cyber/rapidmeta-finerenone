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
    r = _dated_block(canon, "registry_extraction")
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
def _dated_block(canon, prefix):
    """The newest `<prefix>_YYYY_MM_DD` block on the object, or {}.

    ⛔ THE KEY WAS HARDCODED TO ONE DATE. `canon.get("harms_2026_08_30")` means a
    block extracted on any other day is INVISIBLE: the card returns "" and the
    page looks like a topic that has no harms data, rather than one whose data
    the renderer could not find. The two failure modes are indistinguishable on
    the page, and only one of them is true."""
    keys = sorted(k for k in canon.keys()
                  if isinstance(k, str) and k.startswith(prefix + "_"))
    for k in reversed(keys):
        v = canon.get(k)
        if isinstance(v, dict) and v:
            return v
    return {}


def _arm_keys(per_trial):
    """The two arm keys THIS block uses, in the order it stores them.

    ⛔ THESE WERE HARDCODED TO "dapivirine" AND "placebo", inside a function whose
    name promises nothing of the kind. Run against any other topic's block the
    card rendered a full table of `None / None` under a Dapivirine column header
    -- a dapagliflozin review asserting dapivirine data. It did not fail, it
    published. The arm keys are a property of the block and are read from it."""
    for v in (per_trial or {}).values():
        if isinstance(v, dict):
            arms = [k for k in v.keys() if k != "rr"]
            if len(arms) == 2:
                return arms
    return []


def harms_card(canon, p=None):
    """Harms, and the refusal to pool them."""
    h = _dated_block(canon, "harms")
    if not h:
        return ""
    inner = _para(h.get("_what"))
    for label, key in (("Serious adverse events", "serious_adverse_events"),
                       ("Deaths", "deaths")):
        blk = h.get(key) or {}
        per = blk.get("per_trial") or {}
        arms = _arm_keys(per)
        if per and len(arms) == 2:
            pass
        else:
            continue
        a_key, b_key = arms
        rows = ""
        for nct, v in per.items():
            d, pl, rr = v.get(a_key, {}), v.get(b_key, {}), v.get("rr", {})
            rows += ("    <tr><td><code>%s</code></td>"
                     "<td>%s / %s</td><td>%s / %s</td>"
                     "<td><strong>%s</strong> (%s to %s)</td></tr>\n"
                     % (_e(nct), d.get("events"), d.get("n"),
                        pl.get("events"), pl.get("n"),
                        rr.get("point"), rr.get("ci_low"), rr.get("ci_high")))
        inner += (_h3(label)
                  + "  <table>\n    <tr><th>Registration</th>"
                    "<th>%s</th><th>%s</th>"
                    "<th>Risk ratio (95%% CI)</th></tr>\n"
                    % (_e(a_key.replace("_", " ").title()),
                       _e(b_key.replace("_", " ").title()))
                  + rows + "  </table>\n")
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


# ------------------------------------------------------ judgement register --
def judgement_register_card(canon, p=None):
    """Every judgement a harness cannot derive, with its alternative and the
    consequence of that alternative.

    RENDERED, NOT JUST STORED -- and that sentence is here because the four
    blocks above spent an afternoon in a JSON file no reader would open. A
    register of judgements that a reader cannot see is worth exactly as much as
    the undeclared judgements it was written to replace.
    """
    r = canon.get("judgement_register_2026_08_30") or {}
    if not r:
        return ""
    rows = ""
    for j in (r.get("per_topic_judgements") or []):
        alt = j.get("if_alternative")
        if isinstance(j.get("if_alternative_COMPUTED"), dict):
            c = j["if_alternative_COMPUTED"]
            alt = " ".join(str(v) for v in c.values() if isinstance(v, str))
        elif j.get("if_alternative_COMPUTED"):
            alt = j["if_alternative_COMPUTED"]
        rows += (
            "    <tr><td><code>%s</code><br><strong>%s</strong></td>"
            "<td>%s</td><td><small>%s</small></td>"
            "<td>%s</td><td><small>%s</small></td></tr>\n"
            % (_e(j.get("id")), _e(j.get("judgement")), _e(j.get("decided")),
               _e(j.get("decided_by")), _e(j.get("alternative")), _e(alt)))

    cnt = r.get("count") or {}
    st = r.get("standing_rules_NOT_counted_per_topic") or {}
    srows = "".join("    <tr><td>%s</td><td><small>%s</small></td></tr>\n"
                    % (_e(x.get("rule")), _e(x.get("scope")))
                    for x in (st.get("rules") or []))

    inner = (
        _para(r.get("_what"))
        + "  <div class='absent-state'>%s</div>\n"
          % _e(r.get("⛔_the_rule_that_keeps_this_honest", ""))
        + _para(r.get("_why_this_is_the_claim_worth_making"))
        + _h3("The judgements, each with its alternative and what that would change")
        + "  <table>\n    <tr><th>Judgement</th><th>Decided</th><th>Decided by</th>"
          "<th>Alternative</th><th>If the alternative had been taken</th></tr>\n"
        + rows + "  </table>\n"
        + _h3("The count")
        + "  <table>\n    <tr><th>Measure</th><th>Value</th></tr>\n"
        + "".join("    <tr><td>%s</td><td><strong>%s</strong></td></tr>\n"
                  % (_e(k.replace("_", " ")), _e(v)) for k, v in cnt.items())
        + "  </table>\n"
        + _h3("Standing rules — paid once for the corpus, not once per topic")
        + _para(st.get("_what"))
        + "  <table>\n    <tr><th>Rule</th><th>Scope</th></tr>\n" + srows
        + "  </table>\n"
        + "  <div class='absent-state'>%s</div>\n"
          % _e(r.get("⭐_the_scaling_claim_stated_precisely", ""))
        + "  <div class='absent-state'>%s</div>\n"
          % _e(r.get("what_this_register_does_NOT_do", ""))
    )
    return _card("The judgement register — what a harness cannot derive", inner)


# =========================================================================
# ONE CARD PER READER -- because a tab needs a panel, not a section of one.
#
# ⭐ LANDING THE CONTENT IS NOT THE SAME AS LANDING IT IN THE SHAPE THE TABS
# NEED. `reader_renderings_card` above draws all four readers into a single
# card, which was right while they lived inside Scientific Output and is wrong
# the moment HTA and Guideline become their own panels: a tab points at a
# PANEL, and a panel cannot be a heading three levels inside another card.
# Whoever wires TABS would otherwise find the content present and unusable,
# and the natural assumption on seeing the card land is that the job is done.
#
# ⛔ AND THE CARD AND THE TAB LIST ARE DELIBERATELY NOT 1:1. This module emits
# FOUR reader cards. `ssot/page_format_v1.json` requires TWO of them as tabs --
# HTA and Guideline. `clinician` and `public` were CONSIDERED AND RULED OUT by
# Mahmood on 2026-08-31 ("eight is fine"); they are recorded under
# `considered_and_ruled_out` in that file, which is not the same as absent.
#
# So the asymmetry is a DECISION, not a defect. A future reader finding two
# reader cards without tabs must not "fix" the mismatch by adding two tabs --
# that would silently overturn a ruling by making the code look tidier. If the
# ruling changes, `page_format_v1.json` changes first and the tabs follow it.
#
# ⭐ THE GENERAL FORM, WORTH CARRYING BEYOND THIS CARD:
#
#     TIDINESS IS A PLAUSIBLE MOTIVE FOR REVERSING A DECISION NOBODY RECORDED.
#
# An asymmetry that looks like an oversight invites a well-meaning fix, and the
# fix arrives with a clean rationale -- four cards, four tabs, obviously -- so
# nobody asks whether the missing two were declined. The defence is not a
# comment saying "do not change this"; it is RECORDING THE DECISION WHERE THE
# CODE POINTS AT IT, which is why `_READER_TAB_STATUS` below names the ruling
# and its date on every card rather than only in a file elsewhere.
# =========================================================================

_READER_TAB_STATUS = {
    "hta": "REQUIRED AS A TAB by ssot/page_format_v1.json (pn-hta).",
    "guideline": "REQUIRED AS A TAB by ssot/page_format_v1.json (pn-guideline).",
    "clinician": ("NOT A TAB. Considered and RULED OUT by Mahmood 2026-08-31. "
                  "Recorded under considered_and_ruled_out -- decided against, "
                  "not overlooked. This card is rendered inside Scientific "
                  "Output and that is deliberate."),
    "public": ("NOT A TAB. Considered and RULED OUT by Mahmood 2026-08-31. "
               "Same as clinician: decided against, not overlooked."),
}


def _one_reader_card(canon, key):
    """The rendering for ONE reader, as its own card, or "" if absent."""
    r = canon.get("reader_renderings_2026_08_30") or {}
    blk = (r.get("renderings") or {}).get(key)
    if not isinstance(blk, dict):
        return ""
    inner = _small("Tab status: %s" % _READER_TAB_STATUS.get(key, "not declared"))
    if blk.get("_reader"):
        inner += _small("Reader: %s" % blk["_reader"])

    if key == "guideline":
        etd = blk.get("evidence_to_decision") or {}
        rows = ""
        for k, v in etd.items():
            cls = "warn" if str(v.get("answer", "")).startswith("⛔") else "ok"
            rows += ("    <tr class='%s'><td>%s</td><td><strong>%s</strong></td>"
                     "<td><small>%s</small></td></tr>\n"
                     % (cls, _e(k.replace("_", " ")), _e(v.get("answer")),
                        _e(v.get("from_this_review") or v.get("why") or "")))
        cov = blk.get("COVERAGE_OF_THE_FRAMEWORK") or {}
        inner += (_para(blk.get("_why_this_shape"))
                  + "  <table>\n    <tr><th>Consideration</th><th>Answer</th>"
                    "<th>From this review</th></tr>\n" + rows + "  </table>\n"
                  + "  <div class='absent-state'>%s informed, %s not addressed. "
                    "%s</div>\n"
                  % (_e(cov.get("informed_or_partially_informed")),
                     _e(cov.get("not_addressed")),
                     _e(cov.get("⭐_the_empty_cells_are_the_point", ""))))
    else:
        for k, v in blk.items():
            if k.startswith("_"):
                continue
            if isinstance(v, str):
                if k.startswith(("⛔", "⚠️")):
                    inner += "  <div class='absent-state'>%s</div>\n" % _e(v)
                else:
                    inner += _para(v)
            elif isinstance(v, dict):
                for kk, vv in v.items():
                    if isinstance(vv, str):
                        if kk.startswith(("⛔", "⚠️", "so")):
                            inner += ("  <div class='absent-state'>%s</div>\n"
                                      % _e(vv))
                        else:
                            inner += _small("%s — %s"
                                            % (kk.replace("_", " "), vv))
    if key == "public":
        rd = blk.get("readability") or {}
        if rd:
            inner += _small("Readability: Flesch-Kincaid grade %s, reading "
                            "ease %s, %s words in %s sentences. %s"
                            % (rd.get("flesch_kincaid_grade"),
                               rd.get("flesch_reading_ease"), rd.get("words"),
                               rd.get("sentences"), rd.get("instrument")))
    titles = {"hta": "For a health-technology-assessment body",
              "guideline": "For a guideline panel",
              "clinician": "For a clinician",
              "public": "For the public"}
    return _card(titles.get(key, key), inner)


def hta_card(canon, p=None):
    return _one_reader_card(canon, "hta")


def guideline_card(canon, p=None):
    return _one_reader_card(canon, "guideline")


def clinician_card(canon, p=None):
    return _one_reader_card(canon, "clinician")


def public_card(canon, p=None):
    return _one_reader_card(canon, "public")
