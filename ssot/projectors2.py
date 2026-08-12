"""Remaining projectors for the tabbed SSOT page.

Split from projectors.py so each block commits as it lands rather than at
round-end -- the discipline whose absence lost a day's work to one reset.

Prose recovered from the .pyc where it existed; control flow written fresh.
"""
from projectors import (NL, e, fmt, kv_card, fig, scatter_svg, rows_svg,
                        GRADE_DOMAINS)


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
        ("Information sources", "%d source layers, listed on the Extraction tab"
         % len(canon.get("sources") or {})),
        ("Search strategy", "The executed strings, datetimes, filters and hit "
                            "counts are on the Search tab"),
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
        ("Certainty assessment", "GRADE, all five domains, on the Certainty tab"),
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
        "    <tr><th>%s</th><td>%s</td></tr>%s" % (k, e(str(v)), NL)
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
            + "  <table>%s    <tr><th>Commit</th><th>Committed (UTC)</th>"
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
    rows = "".join(
        "    <tr><td><code>%s</code></td><td class='num'>%s</td><td>%s<br>"
        "<small><a href='%s'>%s</a></small></td><td>%s</td></tr>%s"
        % (e(a["sha"][:12]), e(a["committed_utc"]), p(a["subject"]),
           e(a["permalink"]), e(a["permalink"]),
           "<strong>AFTER the search</strong>" if a.get("post_dates_first_query")
           else "before the search", NL) for a in am)
    return ("<div class='card'>%s  <h3>Protocol amendment history</h3>%s  <table>%s"
            "    <tr><th>Commit</th><th>Committed (UTC)</th><th>Subject</th>"
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
        rows += ("    <tr><th>%s</th><td>%s</td><td><small>%s</small></td></tr>%s"
                 % (e(a["label"]), val, p(a["what"]), NL))
    return ("<div class='card'>%s  <h3>Author attestation</h3>%s"
            "  <p>These are the surfaces a human author discharges by checking "
            "them and recording that they did. An attestation records that "
            "someone checked what is already here; it never alters a number and "
            "never raises a cell's source tier. A slot naming no person, no "
            "source or no date reads as absent.</p>%s  <table>%s"
            "    <tr><th>Surface</th><th>Status</th><th>What must be checked</th>"
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
            "    <tr><th>%s</th><td>%s</td></tr>%s" % (k, p(str(db[f])), NL)
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
    summary = "".join("    <tr><th>%s</th><td class='num'>%s</td></tr>%s"
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
            "    <tr><th>Source</th><th>Record</th><th>Title</th><th>Stage</th>"
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
        ident = " &middot; ".join(filter(None, [
            e(str(r.get("nct", ""))),
            "PMID %s" % e(str(r["pmid"])) if r.get("pmid") else ""]))
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
                + "</div>" + NL)
    return out


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
        rows += ("    <tr><th>%s</th><td>%s</td><td><small>%s</small></td></tr>%s"
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
    return ("<div class='card'>%s  <h3>Certainty of the evidence (GRADE)</h3>%s"
            "  <p><strong>Certainty: %s</strong></p>%s%s%s  <table>%s"
            "    <tr><th>Domain</th><th>Rating</th><th>Why it was rated that way"
            "</th></tr>%s%s  </table>%s</div>%s"
            % (NL, NL, p(g["certainty"]), NL, start, deriv, NL, NL, rows, NL, NL))


def analysis_figures(res, outcome, p):
    """Every Analysis-Suite chart the object can back, from stored values."""
    pan = res.get("panels")
    if not pan:
        return ""
    null_v = outcome.get("null_value", 1)
    out = ""
    if pan.get("funnel"):
        out += fig(scatter_svg([(x["log_effect"], x["se"], x["trial"])
                                for x in pan["funnel"]],
                               "log effect", "standard error",
                               invert_y=True, vline=0),
                   "Funnel plot", "funnel.svg",
                   "Standard error against log effect, most precise at the top. "
                   "At three studies a funnel cannot be read for asymmetry; it is "
                   "shown because the positions are real and the emptiness is the "
                   "finding.")
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
                             for x in pan["leave_one_out"]], null_v),
                   "Leave-one-out", "leave-one-out.svg",
                   "The pool refitted with each trial removed in turn.")
    if pan.get("cumulative"):
        out += fig(rows_svg([{"label": "through %s (%s)" % (x["through"],
                                                            fmt(x["year"])),
                              "point": x["point"], "ci_low": x["ci_low"],
                              "ci_high": x["ci_high"]}
                             for x in pan["cumulative"]], null_v),
                   "Cumulative meta-analysis", "cumulative.svg",
                   "The pool as each trial reported, in year order.")
    by = pan.get("bayes")
    if by and by.get("density"):
        out += fig(scatter_svg([(x["x"], x["d"], "") for x in by["density"]],
                               "pooled ratio", "posterior density", vline=null_v),
                   "Bayesian posterior density", "posterior.svg", p(by["method"]))
    return out


def count_figures(res, p):
    cp = res.get("count_panels")
    if not cp:
        return ""
    out = ""
    if cp.get("labbe"):
        out += fig(scatter_svg([(x["control_risk"], x["treatment_risk"], x["trial"])
                                for x in cp["labbe"]],
                               "risk in the control arm", "risk in the treatment arm"),
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
