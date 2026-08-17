"""Remaining projectors for the tabbed SSOT page.

Split from projectors.py so each block commits as it lands rather than at
round-end -- the discipline whose absence lost a day's work to one reset.

Prose recovered from the .pyc where it existed; control flow written fresh.
"""
import collections
import math
import re

from projectors import (NL, e, fmt, kv_card, fig, scatter_svg, rows_svg,
                        funnel_svg, rob_traffic_light_svg, prisma_flow_svg,
                        visual_abstract_svg,
                        not_computable_svg, GRADE_DOMAINS)


def protocol_card(canon, p):
    """The registration pack, PROSPERO field set.

    Where a field has no content it is STATED as absent with the reason, never
    omitted: an absent field reads as an oversight, a stated absence as a
    decision."""
    sc = canon.get("screening") or {}
    cfg = canon.get("config") or {}
    na = lambda why: "<em>Not recorded &mdash; %s</em>" % why
    pairs = [
        ("Review title", p(canon["title"])),
        ("Review question (PICO)", p(canon["question"])),
        ("Background / rationale", na(
            "this object holds no background field, and an introduction generated "
            "without one would be argument that no source in this review supports")),
        ("Eligibility criteria", p(sc["eligibility"]) if sc.get("eligibility") else ""),
        ("Information sources", "%d source layers, listed on the <a href=\"#extract\">Extraction tab</a>"
         % len(canon.get("sources") or {})),
        ("Search strategy", "The executed strings, datetimes, filters and hit "
                            "counts are on the <a href=\"#search\">Search tab</a>"),
        ("Study selection process", "Two independent screeners of different model "
         "families, title/abstract then full text, with named human adjudication"),
        ("Number of screeners", "Two, cross-family. Two instances of one model is "
         "one screener run twice and its agreement statistic is meaningless"),
        ("Data extraction items", "Registry id, primary publication, year, design, "
         "population, arms, the analysed denominator and the randomised total "
         "SEPARATELY, per-arm event counts, and the published effect with its "
         "interval and its stated level"),
        ("Outcomes and prioritisation",
         "; ".join(p(o["name"]) for o in canon.get("outcomes", []))),
        ("Risk of bias method", p(canon["risk_of_bias_verdict"])
         if canon.get("risk_of_bias_verdict") else
         na("no per-domain RoB-2 assessment exists yet")),
        ("Synthesis methods", "Random effects on the log scale; REML headline; "
         "HKSJ reported alongside; leave-one-out and an estimator comparison, all "
         "pre-specified before the search"),
        ("Subgroup analyses", na(
            "none pre-specified. At this k any contrast would be underpowered and "
            "post hoc, and none will later be presented as though planned")),
        ("Meta-bias assessment", "Funnel, Egger and Peters, each reported as a "
         "computed value with the caveat that below about ten studies they have "
         "almost no power"),
        ("Certainty assessment", "GRADE, all five domains, on the "
         "<a href=\"#report\">Certainty tab</a>"),
        ("Confidence level", "%s%%" % fmt(cfg.get("confidence_level"))
         if cfg.get("confidence_level") else ""),
        ("Funding", na("no funding statement is recorded for this review")),
        ("Competing interests", na("no declaration is recorded")),
        ("Built", e(str(canon.get("built", "")))),
        ("Schema", e(str(canon.get("schema_version", "")))),
    ]
    return kv_card("Registration and administrative information "
                   "(PROSPERO field set)", pairs)


def registration_card(canon, p):
    reg = canon.get("registration") or {}
    if not reg:
        return ""
    rows = "".join(
        "    <tr><td><code>%s</code></td><td class='num'>%s</td><td>%s<br>"
        "<small><a href='%s'>%s</a></small></td></tr>%s"
        % (e(c["sha"][:12]), e(c["committed_utc"]), p(c["subject"]),
           e(c["permalink"]), e(c["permalink"]), NL)
        for c in reg.get("commits", []))
    o = reg.get("ordering") or {}
    ord_rows = "".join(
        "    <tr><th scope='col'>%s</th><td>%s</td></tr>%s" % (k, e(str(v)), NL)
        for k, v in (("Verdict", o.get("verdict", "")),
                     ("Protocol committed", o.get("protocol_committed_utc", "")),
                     ("Strengthened", o.get("strengthened_commit_utc", "")),
                     ("First query attempted", o.get("first_query_attempted_utc", "")),
                     ("First query executed", o.get("first_query_executed_utc", "")),
                     ("Margin vs registration", o.get("margin_vs_registration", "")),
                     ("Margin vs strengthened", o.get("margin_vs_strengthened", "")))
        if v)
    return ("<div class='card'>" + NL + "  <h3>Protocol registration</h3>" + NL
            + "  <p><strong>Method:</strong> %s &mdash; repository <a href='%s'>%s"
              "</a>, path <code>%s</code>.</p>%s"
              % (p(reg.get("method", "")), e(reg.get("repository", "")),
                 e(reg.get("repository", "")), e(reg.get("path", "")), NL)
            + "  <table>%s    <tr><th scope='col'>Commit</th><th>Committed (UTC)</th>"
              "<th>Subject and permalink</th></tr>%s%s  </table>%s" % (NL, NL, rows, NL)
            + "  <p><small>Permalinks are pinned to the commit SHA, not to a "
              "branch. A branch link moves and would prove nothing.</small></p>" + NL
            + "  <h4>Ordering test: did the protocol precede the search?</h4>" + NL
            + "  <table>%s%s  </table>%s" % (NL, ord_rows, NL)
            + "  <p>%s</p>%s" % (p(o.get("reason", "")), NL)
            + "  <h4>What this evidence establishes</h4>" + NL
            + "  <p>%s</p>%s" % (p(reg.get("what_the_commit_evidence_establishes", "")), NL)
            + "  <h4>What it does not</h4>" + NL
            + "  <p>%s</p>%s" % (p(reg.get("what_the_commit_evidence_does_not_establish", "")), NL)
            + "</div>" + NL)


def amendments_card(canon, p):
    """The protocol's full commit history, not only its head."""
    pr = canon.get("protocol") or {}
    am = pr.get("amendment_history") or []
    if not am:
        return ""
    # An amendment recorded in the SAME commit that enacts it cannot carry that
    # commit's own sha -- the sha does not exist until the write is finished.
    # That is a real transient state, not corruption, so it renders as the
    # uncommitted state it is instead of crashing the build (which is what
    # a["sha"][:12] did on a null). It is NOT silently blanked: a reader is told
    # the entry has no commit behind it yet, because an amendment presented in a
    # commit-evidence table with an empty Commit cell would read as committed.
    def _row(a):
        sha, link = a.get("sha"), a.get("permalink")
        if sha:
            commit = "<code>%s</code>" % e(str(sha)[:12])
            where = ("<small><a href='%s'>%s</a></small>"
                     % (e(link), e(link))) if link else \
                    "<small>No permalink recorded.</small>"
        else:
            commit = "<em>not yet committed</em>"
            where = ("<small>Recorded in the object; no commit stands behind this "
                     "entry yet, so it carries none of the timestamp evidence the "
                     "rows above do.</small>")
        return ("    <tr><td>%s</td><td class='num'>%s</td><td>%s<br>%s</td>"
                "<td>%s</td></tr>%s"
                % (commit, e(a.get("committed_utc") or "--"), p(a.get("subject", "")),
                   where,
                   "<strong>AFTER the search</strong>" if a.get("post_dates_first_query")
                   else "before the search", NL))

    rows = "".join(_row(a) for a in am)
    return ("<div class='card'>%s  <h3>Protocol amendment history</h3>%s  <table>%s"
            "    <tr><th scope='col'>Commit</th><th>Committed (UTC)</th><th>Subject</th>"
            "<th>Relative to the search</th></tr>%s%s  </table>%s"
            "  <p><small>%s</small></p>%s</div>%s"
            % (NL, NL, NL, NL, rows, NL, p(pr.get("amendment_note", "")), NL, NL))


def attestation_card(canon, rd, p):
    if not rd["attestable"]:
        return ""
    rows = ""
    for a in rd["attestable"]:
        if a["ok"]:
            at = a["att"]
            val = ("<strong>Attested</strong> by %s on %s, against %s"
                   % (p(at["by"]), e(str(at["date_utc"])),
                      p(at["source_checked_against"])))
        else:
            val = "<em>Awaiting attestation</em>"
        rows += ("    <tr><th scope='col'>%s</th><td>%s</td><td><small>%s</small></td></tr>%s"
                 % (e(a["label"]), val, p(a["what"]), NL))
    return ("<div class='card'>%s  <h3>Author attestation</h3>%s"
            "  <p>These are the surfaces a human author discharges by checking "
            "them and recording that they did. An attestation records that "
            "someone checked what is already here; it never alters a number and "
            "never raises a cell's source tier. A slot naming no person, no "
            "source or no date reads as absent.</p>%s  <table>%s"
            "    <tr><th scope='col'>Surface</th><th>Status</th><th>What must be checked</th>"
            "</tr>%s%s  </table>%s</div>%s"
            % (NL, NL, NL, NL, NL, rows, NL, NL))


def search_strings_card(canon, p):
    """The search as EXECUTED: string, endpoint, filters, datetime, hit count."""
    s = canon.get("search")
    if not s:
        return ""
    out = ""
    for db in s.get("databases", []):
        rows = "".join(
            "    <tr><th scope='col'>%s</th><td>%s</td></tr>%s" % (k, p(str(db[f])), NL)
            for k, f in (("Endpoint", "endpoint"), ("Parameters", "parameters"),
                         ("Filters applied", "filters"),
                         ("Executed (UTC)", "executed_utc"),
                         ("Hit count", "hit_count"),
                         ("Records retrieved", "records_retrieved"))
            if db.get(f))
        out += ("<div class='card'>%s  <h3>%s</h3>%s"
                "  <p><small>Query as executed:</small></p>%s  <pre>%s</pre>%s"
                "  <table>%s%s  </table>%s</div>%s"
                % (NL, p(db["database"]), NL, NL,
                   e(db.get("query_as_executed") or ""), NL, NL, rows, NL, NL))
    if s.get("reproducibility_note"):
        out += ("<div class='card'>%s  <h3>How to re-run this search</h3>%s"
                "  <p>%s</p>%s  <p><small>Captured by: %s. Source: <code>%s</code>."
                "</small></p>%s</div>%s"
                % (NL, NL, p(s["reproducibility_note"]), NL,
                   p(s.get("executed_by", "")), e(s.get("capture_source", "")),
                   NL, NL))
    return out


def corpus_card(canon, p):
    """Every retrieved record, with its decision and the stage it was taken at."""
    sc = canon.get("screening") or {}
    rows = sc.get("corpus") or []
    if not rows:
        return ""
    summary = "".join("    <tr><th scope='col'>%s</th><td class='num'>%s</td></tr>%s"
                      % (e(k), fmt(v), NL)
                      for k, v in sorted((sc.get("corpus_counts") or {}).items()))
    body = ""
    for r in rows:
        dec = str(r.get("decision", ""))
        cls = ("inc" if dec.upper() == "INCLUDE" else
               "und" if dec == "undetermined" else "")
        link = ("<a href='%s'>%s</a>" % (e(r["url"]), e(str(r.get("record_id", ""))))
                if r.get("url") else e(str(r.get("record_id", ""))))
        body += ('    <tr class="%s"><td>%s</td><td>%s</td><td>%s<br><small>%s %s'
                 '</small></td><td>%s</td><td><strong>%s</strong></td><td>%s</td>'
                 '<td><small>%s</small></td></tr>%s'
                 % (cls, e(str(r.get("source", ""))), link,
                    p(str(r.get("title", ""))),
                    p(str(r.get("journal_or_status", ""))),
                    e(str(r.get("year_or_start", ""))), e(str(r.get("stage", ""))),
                    e(dec), e(str(r.get("axis_failed") or "&mdash;")),
                    p(str(r.get("quantity_reported_instead") or "")), NL))
    return ("<div class='card'>%s  <h3>Every record the search retrieved</h3>%s"
            "  <p>%s</p>%s  <table>%s%s  </table>%s  <table>%s"
            "    <tr><th scope='col'>Source</th><th>Record</th><th>Title</th><th>Stage</th>"
            "<th>Decision</th><th>Axis failed</th><th>What it reports instead</th>"
            "</tr>%s%s  </table>%s</div>%s"
            % (NL, NL, p(sc.get("corpus_note", "")), NL, NL, summary, NL, NL, NL,
               body, NL, NL))


def screening_cards(canon, p):
    """The adjudicated records, plus any adjudication that OVERRODE a screener.

    An inclusion that rests on a named human ruling rather than on a screener is
    shown as an override, because a reader is entitled to know which it was."""
    sc = canon.get("screening") or {}
    out = ""
    for t in canon["inputs"]["trials"]:
        ip = t.get("inclusion_provenance")
        if ip:
            out += ("<div class='card warn'>%s  <h3>Adjudication: %s</h3>%s"
                    "  <p><strong>Screener A said: %s. Resolved by %s &mdash; %s, "
                    "%s.</strong></p>%s  <p>%s</p>%s</div>%s"
                    % (NL, p(t.get("name") or t["id"]), NL,
                       e(str(ip.get("screener_a", ""))),
                       e(str(ip.get("resolved_by", ""))),
                       p(str(ip.get("adjudicator", ""))),
                       e(str(ip.get("adjudicated_utc", ""))), NL,
                       p(ip.get("note", "")), NL, NL))
    for r in (sc.get("records") or []):
        # `.get(k, "")` returns the DEFAULT only when the key is ABSENT. These
        # keys are PRESENT with value None, so str() rendered the literal "None"
        # and filter(None, ...) kept it, because the STRING "None" is truthy.
        # Five iv-iron-hf records have both identifiers null and every one
        # printed "None" beside the trial name. Caught by the batch-1 gate.
        ident = " &middot; ".join(filter(None, [
            e(str(r.get("nct") or "")),
            ("PMID %s" % e(str(r["pmid"]))) if r.get("pmid") else ""]))
        crit = "".join("<li>%s</li>" % p(c) for c in (r.get("criteria_failed") or []))
        decided = (p(str(r["disposition"])) if r.get("disposition")
                   else ("excluded" if r.get("criteria_failed") else "included"))
        out += ("<div class='card rec'>%s  <h3>%s <small>%s</small></h3>%s"
                "  <p><strong>This review's decision: %s.</strong></p>%s"
                % (NL, p(str(r.get("trial", ""))), ident, NL, decided, NL)
                + ("  <p>%s</p>%s" % (p(r["reason"]), NL) if r.get("reason") else "")
                + ("  <ul>%s</ul>%s" % (crit, NL) if crit else "")
                + ("  <p><small><strong>What it actually reports:</strong> %s"
                   "</small></p>%s" % (p(r["quantity_it_reports"]), NL)
                   if r.get("quantity_it_reports") else "")
                + ("  <p><small><strong>Why that is not this review's measure:"
                   "</strong> %s</small></p>%s"
                   % (p(r["why_that_quantity_is_never_stored_as_a_hazard_ratio"]), NL)
                   if r.get("why_that_quantity_is_never_stored_as_a_hazard_ratio")
                   else "")
                + ("  <p><small><a href='%s'>%s: %s</a></small></p>%s"
                   % (e(r["source_url"]), e(str(r.get("source_tier", "source"))),
                      e(r["source_url"]), NL) if r.get("source_url") else "")
                + _evidence_basis(r.get("evidence_basis"), p)
                + "</div>" + NL)
    return out


def _evidence_basis(eb, p):
    """How a screening decision is KNOWN, not merely what it was.

    An exclusion that is right because third-party sources agreed and one that is
    right because someone read the trial's own endpoint definition are the same
    decision resting on different things, and only one of them is checkable.
    Projecting the difference lets a reader see which rows have been read and
    which are still inferred, and makes an upgrade legible as an upgrade.
    """
    if not eb:
        return ""
    comp = "".join("      <li>%s</li>%s" % (p(str(x)), NL)
                   for x in (eb.get("composite_as_defined_by_the_trial") or []))
    rows = "".join(
        "    <tr><th scope='col'>%s</th><td>%s</td></tr>%s" % (lab, p(str(eb[k])), NL)
        for k, lab in (("level", "Evidence basis"), ("was", "Previously"),
                       ("upgraded_utc", "Upgraded (UTC)"),
                       ("what_was_read", "What was read"),
                       ("citation", "Citation"),
                       ("analysis_reported", "Analysis the trial reports"))
        if eb.get(k))
    if eb.get("url"):
        rows += ("    <tr><th scope='col'>Source</th><td><a href='%s'>%s</a></td></tr>%s"
                 % (e(eb["url"]), e(eb["url"]), NL))
    return ("  <details class='eb' open><summary><strong>%s</strong> "
            "<small>&mdash; how this decision is known</small></summary>%s"
            "  <table>%s%s  </table>%s"
            % (p(str(eb.get("level", "evidence basis"))), NL, NL, rows, NL)
            + ("  <p><small>The composite as the trial itself defines it:</small>"
               "</p>%s  <ul>%s%s  </ul>%s" % (NL, NL, comp, NL) if comp else "")
            + ("  <p>%s</p>%s" % (p(eb["why_this_is_not_our_estimand"]), NL)
               if eb.get("why_this_is_not_our_estimand") else "")
            + ("  <p><small>%s</small></p>%s" % (p(eb["what_changed"]), NL)
               if eb.get("what_changed") else "")
            + "  </details>" + NL)


def grade_section(res, p):
    g = res.get("grade")
    if not g:
        return ""
    rows = ""
    for k in GRADE_DOMAINS:
        d = (g.get("domains") or {}).get(k)
        if not d:
            continue
        basis = str(d.get("basis_in_sources", "")).strip()
        rows += ("    <tr><th scope='col'>%s</th><td>%s</td><td><small>%s</small></td></tr>%s"
                 % (e(k.replace("_", " ").capitalize()), p(d["rating"]),
                    p(basis) if basis else "&mdash;", NL))
    start = ""
    if g.get("starting_point"):
        because = str(g.get("starting_point_because", "")).strip()
        start = ("  <p>Started at <strong>%s</strong>%s.</p>%s"
                 % (p(g["starting_point"]),
                    " &mdash; " + p(because) if because else "", NL))
    deriv = ("  <p><small>%s</small></p>%s" % (p(g["certainty_derivation"]), NL)
             if g.get("certainty_derivation") else "")
    # Whether the completed RoB-2 moved this rating, projected EITHER WAY. A
    # rating that survives an assessment and one that was never tested look
    # identical on the page unless the page says which it is, and the protocol
    # requires the no-movement case to be stated as explicitly as movement.
    rr = ((g.get("domains") or {}).get("risk_of_bias") or {}).get(
        "rob2_effect_on_this_rating")
    effect = ""
    if rr:
        effect = ("<div class='card%s'>%s  <h3>Did the completed RoB-2 assessment "
                  "move this rating?</h3>%s  <p><strong>%s.</strong> It was "
                  "<strong>%s</strong> before the assessment and is "
                  "<strong>%s</strong> after it.</p>%s  <p>%s</p>%s"
                  "  <p><small>The opposite reading, recorded rather than "
                  "suppressed: %s</small></p>%s"
                  "  <p><small>What would change it: %s</small></p>%s</div>%s"
                  % ("" if rr.get("moved") else " warn", NL, NL,
                     "Yes" if rr.get("moved") else "No, it does NOT move",
                     p(rr.get("rating_before_rob2", "")),
                     p(rr.get("rating_after_rob2", "")), NL,
                     p(rr.get("why_it_does_not_move", "")), NL,
                     p(rr.get("counter_argument_recorded", "")), NL,
                     p(rr.get("conditions_under_which_it_would_move", "")), NL, NL))
    return ("<div class='card'>%s  <h3>Certainty of the evidence (GRADE)</h3>%s"
            "  <p><strong>Certainty: %s</strong></p>%s%s%s  <table>%s"
            "    <tr><th scope='col'>Domain</th><th>Rating</th><th>Why it was rated that way"
            "</th></tr>%s%s  </table>%s</div>%s%s"
            % (NL, NL, p(g["certainty"]), NL, start, deriv, NL, NL, rows, NL, NL,
               effect))


def analysis_figures(res, outcome, p):
    """Every Analysis-Suite chart the object can back, from stored values."""
    pan = res.get("panels")
    if not pan:
        return ""
    null_v = outcome.get("null_value", 1)
    # Named on the axis so a reader does not have to infer the measure
    # from the surrounding prose.
    _meas = str(((res.get("pooled") or {}).get("measure")) or "Effect")
    out = ""
    _k = res.get("k") or len(res.get("per_trial") or [])
    if pan.get("funnel"):
        _fit = pan.get("fit") or {}
        _pl = _fit.get("log_point")
        if _pl is None:
            _pp = (res.get("pooled") or {}).get("point")
            _pl = math.log(_pp) if _pp and _pp > 0 else 0.0
        out += fig(funnel_svg([(x["log_effect"], x["se"], x["trial"])
                               for x in pan["funnel"]], _pl, null_log=0.0,
                              measure=_meas,
                              k_note="At k = %d it cannot be read for "
                                     "asymmetry." % _k),
                   "Funnel plot", "funnel.svg",
                   "Standard error against the effect, most precise at the top, "
                   "with the 95%% and 99%% pseudo-confidence funnel drawn from "
                   "the pooled estimate and contour bands around the null. At "
                   "k = %d a funnel CANNOT be read for asymmetry and none is "
                   "claimed: it is shown because the positions are real and the "
                   "emptiness is the finding." % _k)
    if pan.get("galbraith"):
        out += fig(scatter_svg([(x["precision"], x["z"], x["trial"])
                                for x in pan["galbraith"]],
                               "precision (1/SE)", "z = effect / SE"),
                   "Galbraith (radial) plot", "galbraith.svg",
                   "Each trial's standardised effect against its precision.")
    if pan.get("baujat"):
        out += fig(scatter_svg([(x["q_contribution"], x["pooled_influence"],
                                 x["trial"]) for x in pan["baujat"]],
                               "contribution to Q", "influence on the pooled estimate"),
                   "Baujat plot", "baujat.svg",
                   "Right means a trial drives heterogeneity; up means it moves "
                   "the pooled result. Top-right is both.")
    if pan.get("influence"):
        out += fig(scatter_svg([(x["hat"], x["cook_d"], x["trial"])
                                for x in pan["influence"]],
                               "leverage (hat)", "Cook's distance"),
                   "Influence diagnostics", "influence.svg",
                   "Leverage against Cook's distance, from metafor's influence "
                   "diagnostics.")
    if pan.get("leave_one_out"):
        out += fig(rows_svg([{"label": "omitting " + str(x["omitted"]),
                              "point": x["point"], "ci_low": x["ci_low"],
                              "ci_high": x["ci_high"]}
                             for x in pan["leave_one_out"]], null_v,
                            measure=_meas,
                            axis_note="Each row is the pool WITHOUT that trial."),
                   "Leave-one-out", "leave-one-out.svg",
                   "The pool refitted with each trial removed in turn.")
    if pan.get("cumulative"):
        out += fig(rows_svg([{"label": "through %s (%s)" % (x["through"],
                                                            fmt(x["year"])),
                              "point": x["point"], "ci_low": x["ci_low"],
                              "ci_high": x["ci_high"]}
                             for x in pan["cumulative"]], null_v,
                            measure=_meas,
                            axis_note="Each row adds the next trial in year order."),
                   "Cumulative meta-analysis", "cumulative.svg",
                   "The pool as each trial reported, in year order.")
    by = pan.get("bayes")
    if by and by.get("density"):
        out += fig(scatter_svg([(x["x"], x["d"], "") for x in by["density"]],
                               "pooled ratio", "posterior density", vline=null_v),
                   "Bayesian posterior density", "posterior.svg", p(by["method"]))
    return out


def visual_abstract(canon, res, outcome, p):
    """The graphical abstract, projected. Under the same gates as any figure."""
    pooled = res.get("pooled") or {}
    if not pooled.get("point"):
        return ""
    n_total = 0
    for t in (canon.get("inputs") or {}).get("trials", []):
        for a in (t.get("arms") or []):
            n_total += a.get("participants") or 0
    g = res.get("grade") or {}
    sens = res.get("sensitivity") or {}
    loo = ""
    rows = [a for a in (sens.get("analyses") or []) if isinstance(a, dict)]
    kept = [a for a in rows if a.get("still_excludes_null")]
    if rows:
        loo = ("Leave-one-out: %d of %d refits still exclude no difference; the "
               "estimate does not survive removal of the largest trial."
               % (len(kept), len(rows)))
    return fig(visual_abstract_svg(
        canon.get("title", ""), canon.get("question", ""),
        res.get("k") or len(res.get("per_trial") or []),
        "{:,}".format(n_total) if n_total else None,
        pooled.get("measure", ""), pooled["point"], pooled.get("ci_low"),
        pooled.get("ci_high"), outcome.get("null_value", 1),
        g.get("certainty"), outcome.get("name", ""), loo),
        "Visual abstract", "visual-abstract.svg",
        "Projected from the canonical object, so it carries the same k, the same "
        "pooled estimate and the same interval as the paper and cannot drift "
        "from them. The interval is drawn CROSSING the no-difference line "
        "because it does: a graphical abstract travels without its caption, and "
        "one that showed a favourable point estimate without showing that its "
        "interval includes no effect would be overstating a null result, which "
        "is a defect class this review documents in other papers.")


def rob_figure(canon, p):
    """Risk-of-bias traffic light, both assessors, from the stored RoB-2 block."""
    rb = canon.get("rob2") or {}
    trials = rb.get("trials") or []
    if not trials:
        return fig(not_computable_svg(
            "Risk-of-bias traffic light",
            "No per-domain RoB-2 assessment is stored in this object."),
            "Risk of bias", "rob-traffic-light.svg",
            "Not drawn, because there is nothing to draw it from.")
    doms = [d.get("domain") for d in trials[0].get("domains", [])]
    a = rb.get("assessors") or [{}, {}]
    keys = ("assessor_1_openai", "assessor_2_google")

    def cell(trial_name, domain, idx):
        for t in trials:
            if t.get("trial") != trial_name:
                continue
            for dd in t.get("domains", []):
                if dd.get("domain") == domain:
                    return (dd.get(keys[idx]) or {}).get("judgement")
        return None

    # EVERY POOLED TRIAL GETS A ROW, assessed or not. RoB-2 here was run before
    # ANSWER-HF was adjudicated into the pool, so it has no judgement -- and a
    # traffic light silently showing three rows beside a four-trial forest is the
    # same k mismatch that put a k=3 leave-one-out under a k=4 headline. The
    # missing trial is drawn as NOT ASSESSED so the gap is visible rather than
    # absent.
    names = [t.get("trial") for t in trials]
    assessed = set(names)
    for _t in (canon.get("inputs") or {}).get("trials", []):
        _id = _t.get("id")
        if _id and _id not in assessed:
            names.append(_id)
    fams = [x.get("model_family", "assessor %d" % (i + 1))
            for i, x in enumerate(a)]
    agree = rb.get("agreement")
    return fig(rob_traffic_light_svg(names, doms, fams, cell),
               "Risk of bias, both assessors", "rob-traffic-light.svg",
               "Every cell carries BOTH independent cross-family assessments and "
               "they are not reconciled: showing one column would be a "
               "reconciliation presented as an observation. Glyph as well as "
               "colour, so the panel survives greyscale printing and colour-blind "
               "reading. A trial with no judgement is shown as a row of "
               "not-assessed markers rather than omitted, so a gap in the "
               "assessment cannot be mistaken for a clean assessment. %s"
               % (("Agreement as measured: %s." % p(str(agree)))
                  if agree else ""))


def prisma_figure(canon, p):
    """PRISMA flow, with the stages this corpus never recorded stated as such."""
    sc = canon.get("screening") or {}
    corpus = sc.get("corpus") or []
    if not corpus:
        return ""
    cc = sc.get("corpus_counts") or {}
    tiab = sum(v for k, v in cc.items() if str(k).startswith("TiAb"))
    full = sum(v for k, v in cc.items() if str(k).startswith("FullText"))
    inc = sum(v for k, v in cc.items() if str(k).endswith("INCLUDE"))
    und = sum(v for k, v in cc.items() if str(k).endswith("undetermined"))
    ex_tiab = cc.get("TiAb/exclude")
    ex_full = cc.get("FullText/exclude")
    ax = collections.Counter(r.get("axis_failed") for r in corpus
                    if r.get("decision") == "exclude" and r.get("axis_failed"))
    why = ", ".join("%s %d" % (k.lower(), v) for k, v in ax.most_common())
    # SCREENED is every record that entered title/abstract screening, which is
    # the whole corpus -- NOT the number whose decision was FINAL at that stage.
    # The first cut printed 414, the count resolved at title/abstract, so the
    # box under-reported the screened total by exactly the nine that went on to
    # full text. Caught by reading the rendered diagram and checking that its
    # own arithmetic closes.
    # THE IDENTIFICATION TIER WAS NOT UNRECOVERABLE. The object recorded it all
    # along, in search.databases: each database's hit count as the API returned
    # it and how many of those were retrieved. They sum to exactly the screened
    # corpus, and the corpus's own per-source tally agrees independently. The
    # "permanently unrecoverable" note was stale, and an empty identification
    # tier is a submission blocker -- so this is populated from stored evidence
    # rather than by re-running the search, which means no record enters or
    # leaves the pool and k cannot move.
    dbs = (canon.get("search") or {}).get("databases") or []
    ident, per_db = 0, []
    for db in dbs:
        m = re.search(r"(\d+)", str(db.get("records_retrieved")
                                     or db.get("hit_count") or ""))
        if not m:
            per_db, ident = [], 0
            break
        ident += int(m.group(1))
        per_db.append("%s %s" % (str(db.get("database", "")).split(" (")[0],
                                 m.group(1)))
    screened = len(corpus)
    tiab_removed = (ex_tiab or 0) + (und or 0)
    _ident_ok = (not ident) or (ident == screened)
    _studies = len((canon.get("inputs") or {}).get("trials") or [])
    if screened - tiab_removed != full or not _ident_ok or (inc and inc < _studies):
        # Refuse to draw a flow that does not add up rather than ship a diagram
        # a reader can falsify with mental arithmetic. This review checks the
        # PRISMA arithmetic of the published syntheses it audits; it has to
        # survive the same check.
        return fig(not_computable_svg(
            "PRISMA flow of records",
            "Refused: the flow does not reconcile. %d identified, %d screened, "
            "%d removed at title/abstract, %d assessed at full text."
            % (ident, screened, tiab_removed, full)),
            "PRISMA flow of records", "prisma-flow.svg",
            "Not drawn, because the stored stage counts do not reconcile.")
    by_src = collections.Counter(r.get("source") for r in corpus)
    boxes = [
        {"label": "Records identified from databases and registers",
         "n": ident or None,
         "note": ("; ".join(per_db)) if per_db else
                 "No per-database counts are recorded.",
         "side": "corpus tally: %s" % ", ".join(
             "%s %d" % (k, v) for k, v in sorted(by_src.items()) if k)},
        {"label": "Records removed before screening",
         "n": 0 if ident and ident == len(corpus) else None,
         # Short enough to fit the box. The full reasoning is in the caption;
         # a note clipped mid-word ("disjoint record typ") is the same lost-text
         # defect as the axis title that ran off its own viewBox.
         "note": ("No de-duplication step recorded; retrieved totals sum "
                  "exactly to the screened corpus."
                  if ident == len(corpus) else
                  "Not recorded; cannot be reconstructed without inventing it.")},
        {"label": "Records screened on title and abstract", "n": screened,
         "side": ("excluded %s" % fmt(ex_tiab)) if ex_tiab else None,
         "note": ("%s further record(s) UNDETERMINED at this stage, not counted "
                  "as exclusions." % fmt(und)) if und else None},
        {"label": "Full texts assessed for eligibility", "n": full or None,
         "side": ("excluded %s" % fmt(ex_full)) if ex_full else None},
        # PRISMA 2020 separates REPORTS from STUDIES, and this corpus needs the
        # distinction: PARADIGM-HF and PARALLEL-HF each contribute a publication
        # record and a registry record, so seven included records are four
        # trials. Printing 7 in the final box would overstate the evidence base
        # by three studies that do not exist.
        {"label": "Reports of included studies", "n": inc or None,
         "note": "Records, not studies: two trials contribute both a "
                 "publication and a registry record."},
        {"label": "Studies contributing to the synthesis",
         "n": len((canon.get("inputs") or {}).get("trials") or []) or None},
    ]
    return fig(prisma_flow_svg(boxes), "PRISMA flow of records",
               "prisma-flow.svg",
               "Every stage carries a count. The identification tier is "
               "populated from search.databases, and this caption previously "
               "said the opposite -- that two boxes were drawn as NOT RECORDED "
               "because the counts had never been captured. They had been, all "
               "along; a diagram missing its top box reads as "
               "an oversight, one that states the gap reads as a decision. The "
               "identification tier is populated from search.databases -- each "
               "database's hit count as the API returned it, and how many were "
               "retrieved -- which sum to exactly the screened corpus, and the "
               "corpus's own per-source tally agrees independently. No search "
               "was re-run to fill it, so no record entered or left the pool. "
               "The two sources return disjoint record types (PMIDs and NCT "
               "numbers) and no de-duplication step is recorded, which is why "
               "records removed before screening is zero rather than unknown. "
               "Exclusion reasons across the whole corpus: %s." % p(why))


def underpowered_figures(res, p):
    """Diagnostics that this k cannot support, stated rather than drawn.

    GOSH and trial-sequential analysis are both technically computable from what
    is stored -- and both would be pictures of nothing at four studies. Drawing
    them would put a shape on the page that a reader takes as a diagnostic that
    was run and meant something. The honest rendering is the reason.
    """
    k = res.get("k") or len(res.get("per_trial") or [])
    out = ""
    out += fig(not_computable_svg(
        "GOSH plot",
        "Computable but uninformative at k = %d: the whole subset space is %d "
        "points, and its shape is read for clustering that needs an order of "
        "magnitude more studies." % (k, 2 ** k - 1),
        state="not drawn at this k"),
        "GOSH", "gosh.svg",
        "Deliberately not drawn. Every subset meta-analysis of %d trials is %d "
        "points; a cloud that small cannot show the multimodality GOSH exists to "
        "reveal, and a reader would take the picture as evidence of its absence."
        % (k, 2 ** k - 1))
    out += fig(not_computable_svg(
        "Trial-sequential analysis",
        "Not run: TSA needs a pre-specified target information size, and no "
        "anticipated relative risk reduction or control-arm event rate is "
        "registered in this object's protocol."),
        "Trial-sequential analysis", "tsa.svg",
        "TSA boundaries depend entirely on a target information size that must be "
        "pre-specified. This review's protocol registers none, so any boundary "
        "drawn here would be a parameter chosen after seeing the data -- which is "
        "the practice TSA exists to protect against.")
    mods = sorted({t.get("year") for t in
                   (res.get("per_trial") or []) if t.get("year")})
    out += fig(not_computable_svg(
        "Meta-regression bubble plot",
        "Not fitted: %d trials and no pre-specified moderator. A regression on "
        "year would spend 2 of %d degrees of freedom on a covariate this review "
        "never registered." % (k, k),
        state="not drawn at this k"),
        "Meta-regression", "bubble.svg",
        "The protocol pre-specifies no moderator, and at k = %d a meta-regression "
        "would be fitted on %d points. Not drawn rather than drawn with a caveat: "
        "a bubble plot invites reading a slope, and there is no slope here that "
        "any reader should read." % (k, k))
    return out


def count_figures(res, p):
    cp = res.get("count_panels")
    if not cp:
        return ""
    out = ""
    if cp.get("labbe"):
        out += fig(scatter_svg([(x["control_risk"], x["treatment_risk"], x["trial"])
                                for x in cp["labbe"]],
                               "risk in the control arm",
                               "risk in the treatment arm", diagonal=True),
                   "L'Abbe plot", "labbe.svg",
                   "Each trial's own two risks, read from its 2x2. Below the "
                   "diagonal favours the intervention.")
    if cp.get("nnt_curve"):
        out += fig(scatter_svg([(x["control_risk"], x["nnt"], "")
                                for x in cp["nnt_curve"]],
                               "assumed risk without treatment",
                               "number needed to treat"),
                   "Number needed to treat, across baseline risk", "nnt-curve.svg",
                   "The number needed to treat depends on the risk a patient "
                   "starts with. This applies the pooled risk ratio across a "
                   "range of control risks so a reader can read off the value for "
                   "the patient in front of them.")
    return out


def rob2_card(canon, p):
    """RoB-2, both assessors shown side by side and NOT reconciled.

    A risk-of-bias table that shows one column has already made a choice the
    reader cannot see. Two assessors disagreed on a third of the domains here, so
    a single column would be a reconciliation presented as an observation. Both
    are projected, the agreement rate is projected as measured, and the open
    disagreements are projected as open.
    """
    rb = canon.get("rob2")
    if not rb or not rb.get("trials"):
        return ""
    a = rb["assessors"]
    f1, f2 = a[0].get("model_family", "1"), a[1].get("model_family", "2")
    ag = rb.get("agreement") or {}
    rows = ""
    for t in rb["trials"]:
        for dm in t["domains"]:
            j1 = dm["assessor_1_openai"].get("judgement", "")
            j2 = dm["assessor_2_google"].get("judgement", "")
            mark = "yes" if dm["agreed"] else "<strong>NO</strong>"
            rows += ("    <tr><td>%s</td><td>%s %s</td><td>%s</td><td>%s</td>"
                     "<td>%s</td><td>%s</td></tr>%s"
                     % (p(t["trial"]), dm["domain"], p(dm["domain_name"]),
                        p(j1), p(j2), mark, p(dm["carried"]), NL))
    ov = "".join(
        "    <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>%s"
        % (p(t["trial"]), p(t["overall_assessor_1_openai"].get("judgement", "")),
           p(t["overall_assessor_2_google"].get("judgement", "")),
           "yes" if t["overall_agreed"] else "<strong>NO</strong>", NL)
        for t in rb["trials"])
    dis = ""
    if rb.get("disagreements"):
        dis = ("<div class='card warn'>%s  <h3>Open disagreements (%d)</h3>%s"
               "  <table>%s    <tr><th scope='col'>Trial</th><th>Domain</th><th>%s</th>"
               "<th>%s</th><th>Carried</th></tr>%s%s  </table>%s"
               "  <p><small>Carried at the more cautious of the two, provisionally. "
               "Adjudicator: %s. Status: %s.</small></p>%s</div>%s"
               % (NL, len(rb["disagreements"]), NL, NL, p(f1), p(f2), NL,
                  "".join("    <tr><td>%s</td><td>%s %s</td><td>%s</td><td>%s</td>"
                          "<td>%s</td></tr>%s"
                          % (p(x["trial"]), x["domain"], p(x["domain_name"]),
                             p(x["assessor_1_openai"]), p(x["assessor_2_google"]),
                             p(x["provisional_carry"]), NL)
                          for x in rb["disagreements"]),
                  NL, p((rb.get("adjudication") or {}).get("adjudicator", "")),
                  p((rb.get("adjudication") or {}).get("status", "")), NL, NL))
    flags = "".join(
        "<div class='card warn'>%s  <h3>Integrity flag</h3>%s  <p>%s</p>%s"
        "  <p>%s</p>%s  <p><small>Action taken: %s</small></p>%s</div>%s"
        % (NL, NL, p(x.get("flag", "")), NL, p(x.get("detail", "")), NL,
           p(x.get("action", "")), NL, NL)
        for x in (rb.get("integrity_flags") or []))
    return ("<div class='card'>%s  <h2>Risk of bias (RoB-2)</h2>%s  <p>%s</p>%s"
            "  <p><small>Variant: %s</small></p>%s"
            "  <p><small>Unit assessed: %s</small></p>%s"
            "  <p><small>Assessor 1: %s (%s family). Assessor 2: %s (%s family). "
            "%s</small></p>%s"
            "  <table>%s    <tr><th scope='col'>Trial</th><th>Domain</th><th>Assessor 1 (%s)</th>"
            "<th>Assessor 2 (%s)</th><th>Agreed</th><th>Carried</th></tr>%s%s"
            "  </table>%s</div>%s"
            "<div class='card'>%s  <h3>Overall judgement per trial</h3>%s"
            "  <table>%s    <tr><th scope='col'>Trial</th><th>Assessor 1 (%s)</th>"
            "<th>Assessor 2 (%s)</th><th>Agreed</th></tr>%s%s  </table>%s</div>%s"
            "<div class='card'>%s  <h3>Inter-assessor agreement, as measured</h3>%s"
            "  <p>Per-domain: <span class='num'>%s</span> of "
            "<span class='num'>%s</span> agreed "
            "(<span class='num'>%s%%</span>). Overall: <span class='num'>%s</span> "
            "of <span class='num'>%s</span>.</p>%s  <p>%s</p>%s</div>%s%s%s"
            % (NL, NL, p(rb.get("assembler_excluded", "")), NL,
               p(rb.get("variant", "")), NL, p(rb.get("unit_of_assessment", "")), NL,
               p(a[0].get("model", "")), p(f1), p(a[1].get("model", "")), p(f2),
               p(rb.get("blinding", "")), NL,
               NL, p(f1), p(f2), NL, rows, NL, NL,
               NL, NL, NL, p(f1), p(f2), NL, ov, NL, NL,
               NL, NL, ag.get("per_domain_agreed", ""), ag.get("per_domain_total", ""),
               ag.get("per_domain_rate_pct", ""), ag.get("overall_agreed", ""),
               ag.get("overall_total", ""), NL,
               p(ag.get("comparison_to_screening", "")), NL, NL, dis, flags))


def discrepancies_card(canon, p):
    """Quantities on which two sources disagree. Both values, neither adopted.

    Our own multi-source extraction did not record the PARACHUTE-HF serious
    adverse event disagreement; a blinded comparator found it. Carrying one side
    silently is how a review inherits a number nobody checked, so both sides are
    projected with their pointers and the row is marked unresolved.
    """
    rows = [(t.get("name") or t["id"], x) for t in canon["inputs"]["trials"]
            for x in (t.get("discrepancies") or [])]
    if not rows:
        return ""
    body = "".join(
        "    <tr><td>%s</td><td>%s</td><td class='num'>%s</td>"
        "<td class='num'>%s</td><td>%s</td></tr>%s"
        % (p(nm), p(x["quantity"]), p(x["registry_value"]),
           p(x["publication_value"]), p(x["status"]), NL) for nm, x in rows)
    notes = "".join(
        "  <p><small>%s, %s. Registry: %s. Publication: %s.</small></p>%s"
        "  <p>%s</p>%s  <p><small>%s</small></p>%s"
        % (p(nm), p(x["quantity"]), p(x["registry_pointer"]),
           p(x["publication_pointer"]), NL, p(x["why_it_matters"]), NL,
           p(x.get("lesson", "")), NL) for nm, x in rows)
    return ("<div class='card warn'>%s  <h2>Where two sources disagree</h2>%s"
            "  <table>%s    <tr><th scope='col'>Trial</th><th>Quantity</th><th>Registry</th>"
            "<th>Publication</th><th>Status</th></tr>%s%s  </table>%s%s</div>%s"
            % (NL, NL, NL, NL, body, NL, notes, NL))


def outcomes_card(canon, p):
    """Which outcomes were analysed, which are poolable, and why the rest are not.

    Mahmood asked whether only one outcome had been done. The object could answer
    it and the page could not: a reader had no way to tell whether other outcomes
    had been considered and rejected on stated grounds, or simply never looked at.
    Those two situations look identical from outside, and only one of them is a
    review. This card is the difference.
    """
    oc = canon.get("outcomes_considered")
    sp = canon.get("secondary_pools") or {}
    if not oc:
        return ""
    prim = oc.get("registered_primary") or {}
    rows = ("    <tr><td>%s</td><td>%s</td><td class='num'>%s</td>"
            "<td><strong>%s</strong></td></tr>%s"
            % (p(prim.get("name", "")), e(str(prim.get("measure", ""))),
               prim.get("k", ""), p(prim.get("status", "")), NL))
    for o in (sp.get("outcomes") or []):
        pl = o["pooled"]
        rows += ("    <tr><td>%s%s</td><td>%s</td><td class='num'>%s</td>"
                 "<td>%s <span class='num'>%s</span> (%s to %s), I&sup2; "
                 "<span class='num'>%s</span>%%</td></tr>%s"
                 % (p(o["endpoint"]),
                    " <small>(component of the composite)</small>"
                    if o.get("is_component_of_the_composite") else "",
                    e(o["measure"]), o["k"], e(o["measure"]),
                    fmt(pl["point"]), fmt(pl["ci_low"]), fmt(pl["ci_high"]),
                    fmt(o["heterogeneity"]["i2"]), NL))
    notp = "".join(
        "    <tr><th scope='col'>%s</th><td>%s</td></tr>%s"
        % (p(x["quantity"]), p(x["why"]), NL)
        for x in (oc.get("considered_and_not_pooled") or []))
    cav = "".join(
        "  <p><small>%s</small></p>%s" % (p(o["source_caveat"]), NL)
        for o in (sp.get("outcomes") or []) if o.get("source_caveat"))
    return ("<div class='card'>%s  <h2>Which outcomes were analysed</h2>%s"
            "  <p><strong>%s</strong></p>%s  <table>%s"
            "    <tr><th scope='col'>Outcome</th><th>Measure</th><th>k</th>"
            "<th>Result / status</th></tr>%s%s  </table>%s"
            "  <p>%s</p>%s  <p>%s</p>%s%s"
            "  <h3>Considered and NOT pooled, with the reason</h3>%s"
            "  <table>%s%s  </table>%s"
            "  <p><small>%s</small></p>%s</div>%s"
            % (NL, NL, p(oc.get("short_answer", "")), NL, NL, NL, rows, NL,
               p(sp.get("_why_these_are_not_the_primary", "")), NL,
               p(sp.get("_why_they_must_not_be_added_up", "")), NL, cav,
               NL, NL, notp, NL,
               p(oc.get("honest_note", "")), NL, NL))


# VERDICT COLOURS ARE DELIBERATELY ABSENT. A table that prints errors in red and
# confirmations in grey has already told the reader which half matters, and the
# finding across this lane is that the confirmations are the result: three
# topics reconciled and the published literature implicated in none of them.
_VERDICT_NOTE = {
    "CONFIRMED": "checked and clean",
    "ERROR": "a defect, in the source named",
    "ABSENT": "the thing checked for is not there",
    "UNRESOLVED": "could not be settled at the layer available",
}


def published_comparison_card(canon, p):
    """Comparison with published syntheses -- confirmations included.

    WHY THIS PROJECTOR EXISTS
        The object has carried `published_comparison` since ARNI. NO RENDERER
        EVER EMITTED IT. It reached the Word manuscript as four token counts and
        reached the page not at all, so a section the standard lists as OWED was
        being written into objects and shown to nobody. The section-manifest gate
        could not report it either: it only asks for sections the object EARNS,
        and it asks both surfaces -- but no build had ever put this one in the
        HTML, so there was nothing to compare and the manifest rule for it had
        never fired on a real object.

        That is the same shape as the extraction table missing from every Word
        manuscript: content that exists, a gate that would have caught it, and no
        build path connecting the two.

    THE DENOMINATOR IS RENDERED WITH THE TABLE, NOT UNDER IT. A count of errors
    with no count of checks is a selection. The card refuses to render the rows
    without the denominator for the same reason a proportion must carry its
    comparable fraction inline.
    """
    pc = canon.get("published_comparison") or {}
    checks = pc.get("checks") or []
    den = pc.get("denominator") or {}
    if not checks or not den:
        return ""
    rows = ""
    for c in checks:
        v = c.get("verdict", "")
        q = c.get("quote")
        rows += (
            "    <tr><td><strong>%s</strong><br><small>%s</small></td>"
            "<td>%s<br><small>%s</small></td><td>%s%s</td></tr>%s"
            % (p(c.get("what", "")), e(c.get("id", "")),
               e(v), e(_VERDICT_NOTE.get(v, "")),
               p(c.get("detail", "")),
               ("<br><small>Quoted: &ldquo;%s&rdquo; &mdash; %s</small>"
                % (p(q), p(c.get("location", "")))) if q
               else ("<br><small>%s</small>" % p(c.get("location", ""))
                     if c.get("location") else ""),
               NL))
    revs = "".join(
        "    <tr><th scope='col'>%s</th><td>%s%s</td></tr>%s"
        % (e(r.get("pmid", "") or r.get("id", "")), p(r.get("citation", "")),
           "<br><small>%s</small>" % p(r.get("how_it_differs_from_ours", ""))
           if r.get("how_it_differs_from_ours") else "", NL)
        for r in (pc.get("reviews") or []))
    dd = pc.get("divergence_decomposed") or {}
    dd_html = ""
    if dd:
        dd_html = ("  <h3>Where the numbers differ, and why</h3>%s  <table>%s"
                   "    <tr><th scope='col'>This review</th><td>%s</td></tr>%s"
                   "    <tr><th scope='col'>The published synthesis</th><td>%s</td></tr>%s"
                   "    <tr><th scope='col'>Why they differ</th><td>%s</td></tr>%s"
                   "  </table>%s"
                   % (NL, NL, p(dd.get("ours", "")), NL, p(dd.get("theirs", "")), NL,
                      p(dd.get("why_they_differ", "")), NL, NL))
    return ("<div class='card'>%s  <h2>Comparison with published syntheses</h2>%s"
            "  <p>%s</p>%s"
            "  <p><strong>%s</strong></p>%s"
            "  <p><small>%s</small></p>%s"
            "  <table>%s    <tr><th scope='col'>Check</th><th>Verdict</th>"
            "<th>What was found</th></tr>%s%s  </table>%s"
            "  <h3>The syntheses reconciled against</h3>%s  <table>%s%s  </table>%s"
            "%s  <p><small>How they were identified: %s</small></p>%s</div>%s"
            % (NL, NL, p(pc.get("_why", "")), NL,
               p(den.get("statement", "")), NL,
               p(den.get("symmetry", "")), NL,
               NL, NL, rows, NL, NL, NL, revs, NL,
               dd_html, p(pc.get("_how_identified", "")), NL, NL))
