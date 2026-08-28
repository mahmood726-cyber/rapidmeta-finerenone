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
from rob_block import rob_block

# THE ONE PLACE CERTAINTY IS RESOLVED. This module printed the stored level directly and
# was therefore a seventh consumer outside the module built to be the single answer.
try:
    import grade_authority as _ga
except ImportError:  # pragma: no cover -- package import path
    from . import grade_authority as _ga


# =========================================================================================
# TABLE 1's PROCEDURAL ROWS, PROJECTED. Each was a hardcoded constant asserting that an act
# was carried out, on every page that rendered it, whatever the object held.
#
# THE INHERITANCE TRAP THIS PROJECT PREDICTED AND THOUGHT IT HAD PREVENTED. ARNI holds the
# timestamps (protocol committed 11:27:47Z, first query attempted 12:19:18Z) and the named
# adjudication that make these sentences TRUE OF ARNI. They were copied to every page as
# constants. On MAVACAMTEN the table asserted "two independent screeners ... with named human
# adjudication" while the same page said "No screening log is recorded for this review", and
# asserted "all pre-specified before the search" beside "Refused: the claim that the review
# methods were prespecified".
#
# ONE ROW IN THE SAME TABLE ALREADY DID IT PROPERLY: `Risk of bias method` projects and
# degrades to "Not recorded -- no per-domain RoB-2 assessment exists yet". The fix was
# available and sitting two rows away.
#
# NO DEFAULTS. Where a field does not exist the output is a refusal naming what is missing --
# never a plausible sentence about what a review of this kind usually does.
# =========================================================================================

def _dupe(canon):
    """The screening record, under EITHER of the two names the corpus uses for it.

    ARNI stores `screening.dual_screening`; SGLT2 stores `screening.duplicate_screening`. Same
    concept, two keys, and a projection reading only one of them refuses on the page that
    actually HAS the record -- which is how the first version of this fix reported "no
    screening record" for the one object holding a named adjudicator. The divergence is a
    finding in its own right and is reported rather than silently absorbed.
    """
    sc = canon.get("screening") or {}
    for k in ("duplicate_screening", "dual_screening"):
        v = sc.get(k)
        if isinstance(v, dict) and v:
            return v
    return {}


def _attest(canon, which):
    return ((canon.get("attestations") or {}).get(which)) or {}


def _extraction_items(canon, na):
    """What was ACTUALLY extracted on this object, not what the schema allows.

    THE ROW I FIRST DEFENDED AND THEN WITHDREW. It listed "Registry id, primary publication,
    year, design, population, arms, the analysed denominator and the randomised total
    SEPARATELY, per-arm event counts, and the published effect with its interval and its
    stated level" -- as a constant, on every page.

    Listing schema fields is not claiming a procedure ran, which is why I first left it in.
    But measured against the corpus it describes a schema THE OBJECTS DO NOT IMPLEMENT:

        registry id            137 / 137
        primary publication     59 / 137
        arms                    58 / 137
        per-arm event counts    59 / 137
        published effect        59 / 137
        design                  24 / 137
        year                    12 / 137

    Only the registry id is universal. On 78 objects the row asserts per-arm event counts and a
    published effect that are not there, and on 125 it asserts a year. So it is false about the
    extraction on most of the corpus, and it belongs with the six.
    """
    trials = ((canon.get("inputs") or {}).get("trials")) or []
    if not trials:
        return na("this object holds no trial records, so nothing was extracted per trial")
    keys = set()
    for t in trials:
        if isinstance(t, dict):
            keys |= set(t.keys())
    present = []
    for label, alts in (("registry id", ("nct", "trial_id", "id", "registry_id")),
                        ("primary publication", ("pmid", "citation")),
                        ("year", ("year",)),
                        ("design", ("design",)),
                        ("arms", ("arms", "arms_as_registered")),
                        ("per-arm counts and the published effect", ("by_outcome",)),
                        ("the randomised total, separately from the analysed denominator",
                         ("enrolled", "registration_enrolment"))):
        if any(a in keys for a in alts):
            present.append(label)
    if not present:
        return na("no extractable field is present on this object's trial records")
    return ("Extracted per trial on this object: %s. Fields not listed here were not extracted."
            % "; ".join(present))


def _selection_process(canon, p, na):
    """Who screened, from the record of screening -- or a refusal naming its absence."""
    d = _dupe(canon)
    att = _attest(canon, "screening")
    status = str(d.get("status") or "")
    done = d.get("performed") is True or status.upper().startswith("COMPLETE")
    if done:
        fam = d.get("families")
        who = ""
        if isinstance(fam, dict) and fam:
            who = " (%s)" % p("; ".join("%s: %s" % (k, v) for k, v in fam.items()))
        # THE ADJUDICATOR, FROM WHEREVER THIS OBJECT RECORDS ONE -- and NOT claimed otherwise.
        # The constant said "with named human adjudication" on every page; ARNI is the object
        # that actually holds a name, and it holds it under `adjudication.adjudicator` while
        # the attestation block's `by` is null.
        adjr = ((d.get("adjudication") or {}).get("adjudicator")
                or att.get("by"))
        when = ((d.get("adjudication") or {}).get("date_utc") or att.get("date_utc"))
        if adjr:
            adj = ", adjudicated by %s%s" % (p(str(adjr)),
                                             " on %s" % p(str(when)) if when else "")
        else:
            adj = ", with disagreements NOT adjudicated" if "unadjudicated" in status.lower() \
                else ""
        return "Two independent screens were run%s%s." % (who, adj)
    if isinstance(d, dict) and d.get("performed") is False:
        why = d.get("why")
        return ("A second independent screen was NOT run. %s"
                % p(str(why)) if why else
                "A second independent screen was NOT run for this review.")
    if ((canon.get("absent_from_source") or {}).get("screening")):
        return na("no screening record was recoverable from the page this object was "
                  "extracted from, so who screened and how cannot be stated")
    return na("this object holds no screening record, so the selection process cannot be "
              "described")


def _screener_count(canon, na):
    """How many screeners, counted -- never asserted."""
    d = _dupe(canon)
    fam = d.get("families") if isinstance(d, dict) else None
    if isinstance(fam, dict) and fam:
        return ("%d, of different model families. Two instances of one model is one screener "
                "run twice and its agreement statistic is meaningless." % len(fam))
    if isinstance(d, dict) and d.get("performed") is False:
        return "One. No second independent screen was run."
    return na("this object records no screener count")


def _synthesis_methods(canon, na):
    """The model and estimator actually used, and prespecification only if recorded."""
    cfg = canon.get("config") or {}
    blocks = [b for b in ((canon.get("results") or {}).get("by_outcome") or {}).values()
              if isinstance(b, dict)]
    # ONLY BLOCKS THAT ACTUALLY POOLED. MAVACAMTEN holds model="random-effects" and
    # estimator="not pooled -- the estimate is withdrawn" with pooled.point null, so reading
    # the fields without the predicate produced "Pooled with random-effects-effects not pooled
    # -- the estimate is withdrawn estimator" on a page that pools nothing. `_pool_occurred` is
    # the same predicate the manuscript uses; the two surfaces must not disagree about whether
    # a pool happened.
    pooled_blocks = [b for b in blocks
                     if isinstance(b.get("pooled"), dict)
                     and b["pooled"].get("point") is not None
                     and not b["pooled"].get("withdrawn")]
    if not pooled_blocks:
        return na("no outcome on this object carries a pooled estimate, so no synthesis "
                  "method was applied")

    def _norm(v):
        # "random" and "random-effects" are the same model under two spellings and both occur
        # on SGLT2, which produced "random, random-effects-effects".
        s = str(v).strip().lower()
        return s[:-len("-effects")] if s.endswith("-effects") else s

    models = sorted({_norm(b["model"]) for b in pooled_blocks if b.get("model")})
    ests = sorted({str(b["estimator"]).strip() for b in pooled_blocks
                   if b.get("estimator")
                   and str(b["estimator"]).strip().lower() not in
                   ("", "not applicable", "n/a", "none", "not recorded")
                   and "not pooled" not in str(b["estimator"]).lower()})
    if not models and cfg.get("model"):
        models = [_norm(cfg["model"])]
    if not models and not ests:
        return na("this object records no model or estimator, so no synthesis method can be "
                  "stated")
    bits = []
    if models:
        bits.append("%s-effects" % ", ".join(models))
    if ests:
        bits.append("with the %s estimator" % ", ".join(ests))
    if cfg.get("scale"):
        bits.append("on the %s scale" % str(cfg["scale"]))
    out = "Pooled under " + " ".join(bits) + "."
    # PRESPECIFICATION IS A SEPARATE CLAIM AND IS ONLY MADE WHERE THE OBJECT RECORDS IT.
    # "all pre-specified before the search" was asserted on pages whose own Paper panel argues
    # that writing such a sentence would invalidate every other refusal on the page.
    pre = (canon.get("protocol") or {}).get("prespecified")
    if pre is True:
        out += " These methods were prespecified before the search."
        if (canon.get("registration") or {}).get("ordering", {}).get(
                "protocol_committed_utc"):
            out += (" Protocol committed %s."
                    % canon["registration"]["ordering"]["protocol_committed_utc"])
    elif pre is False:
        out += (" These methods were NOT prespecified before the search, and are not "
                "presented as though they were.")
    else:
        out += (" Whether they were prespecified is not recorded on this object.")
    return out


def _subgroup_analyses(canon, p, na):
    """THREE STATES, NOT TWO. This row is why a hardcoded REFUSAL is as dangerous as a
    hardcoded assertion.

    It read "none pre-specified. At this k any contrast would be underpowered and post hoc,
    and none will later be presented as though planned" -- on EVERY page, without checking.
    On any object that DID prespecify a subgroup, that publishes a review misreporting its own
    protocol. A refusal nobody checks is still a claim, and refusals escape scrutiny precisely
    because they look like caution.

    The collapse it fixes is absent-reads-as-zero in prose: "none were prespecified" and "no
    record is held" are different states and the old sentence said the first for both.
    """
    sub = canon.get("subgroup_analyses")
    if sub is None:
        sub = (canon.get("protocol") or {}).get("subgroup_analyses")
    if isinstance(sub, (list, tuple)) and sub:
        return ("Prespecified: %s."
                % p("; ".join(str(s) for s in sub)))
    if isinstance(sub, str) and sub.strip():
        return p(sub)
    if sub in ([], {}) or (canon.get("protocol") or {}).get(
            "subgroup_analyses_none_prespecified") is True:
        return ("None were prespecified. Any contrast at this k would be underpowered and "
                "post hoc, and none is presented as though planned.")
    return na("this object records no subgroup-analysis field at all, so whether any were "
              "prespecified is UNKNOWN -- which is not the same as none having been")


def _meta_bias(canon, na):
    """Only claimed where a computed value exists."""
    blocks = ((canon.get("results") or {}).get("by_outcome") or {})
    found = sorted({k for b in blocks.values() if isinstance(b, dict)
                    for k in b if k.lower() in ("egger", "peters", "funnel",
                                                "publication_bias", "small_study")})
    if found:
        return ("Reported as computed values (%s), with the caveat that below about ten "
                "studies these have almost no power." % ", ".join(found))
    return na("no funnel, Egger or Peters value is held on this object, so no meta-bias "
              "assessment is claimed")


def _certainty_method(canon, na):
    """GRADE only where a GRADE record exists, counted."""
    g = canon.get("grade") or {}
    by = g.get("by_outcome") or {}
    if isinstance(by, dict) and by:
        appr = g.get("approach")
        return ("GRADE, recorded for %d outcome(s)%s. The ratings are on the "
                "<a href=\"#report\">Certainty tab</a>."
                % (len(by), " (%s)" % appr if appr else ""))
    tbl = [b for b in ((canon.get("results") or {}).get("by_outcome") or {}).values()
           if isinstance(b, dict) and isinstance(b.get("grade"), dict)
           and b["grade"].get("certainty")]
    if tbl:
        return ("GRADE, recorded for %d outcome(s) in the results block. The ratings are on "
                "the <a href=\"#report\">Certainty tab</a>." % len(tbl))
    if ((canon.get("absent_from_source") or {}).get("grade")):
        return na("no GRADE record was recoverable from the page this object was extracted "
                  "from")
    return na("no GRADE record is held on this object, so no certainty assessment is claimed")


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
        ("Information sources", "%d source layers, listed on the <a href=\"#pn-extract\">Extraction tab</a>"
         % len(canon.get("sources") or {})),
        # THE FRAGMENT MUST NAME AN ELEMENT THAT EXISTS. These read "#search" and
        # "#extract"; the ids on the page are "pn-search"/"pn-extract" (panels) and
        # "rt-search"/"rt-extract" (the tab radios). 197 dead fragments across 148 of 149
        # pages, of which 143 were this one. Pointing at the panel makes the link resolve.
        # HONEST LIMIT: the tab shell is CSS-only and driven by radios, so a fragment cannot
        # SELECT the tab without script -- this fixes a dead link, not tab activation.
        ("Search strategy", "The executed strings, datetimes, filters and hit "
                            "counts are on the <a href=\"#pn-search\">Search tab</a>"),
        ("Study selection process", _selection_process(canon, p, na)),
        ("Number of screeners", _screener_count(canon, na)),
        ("Data extraction items", _extraction_items(canon, na)),
        ("Outcomes and prioritisation",
         "; ".join(p(o["name"]) for o in canon.get("outcomes", []))),
        # KEYED ON THE ASSESSMENT, NOT ON THE PROSE SUMMARY. This row read
        # `risk_of_bias_verdict` alone, so a store holding a full per-result RoB 2
        # assessment and no prose summary DENIED ITSELF in the protocol table while the
        # traffic light rendered below it on the same page. paper_projector.py already
        # gates the abstract's claim on `risk_of_bias.by_outcome` existing; that fix was
        # made and never propagated here. A fix applied in one place and not swept for
        # siblings is a fix with a half-life.
        ("Risk of bias method",
         p(canon["risk_of_bias_verdict"]) if canon.get("risk_of_bias_verdict")
         else ("RoB 2, per result, five domains &mdash; see the risk-of-bias table below"
               if ((canon.get("risk_of_bias") or {}).get("by_outcome")
                   or (canon.get("rob2") or {}).get("trials"))
               else na("no per-domain RoB-2 assessment exists yet"))),
        ("Synthesis methods", _synthesis_methods(canon, na)),
        ("Subgroup analyses", _subgroup_analyses(canon, p, na)),
        ("Meta-bias assessment", _meta_bias(canon, na)),
        ("Certainty assessment", _certainty_method(canon, na)),
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
                    # THE FALLBACK IS MARKUP AND MUST NOT GO THROUGH THE ESCAPER.
                    # This read e(str(r.get("axis_failed") or "&mdash;")), so
                    # every screening row with no failed axis served a reader the
                    # literal characters "&mdash;" -- ten of them on ARNI's
                    # screening table. Every other em-dash default in these
                    # projectors sits OUTSIDE e()/p(); this one was inside.
                    # Escape the DATA, never the markup you have chosen to emit.
                    e(dec),
                    (e(str(r["axis_failed"])) if r.get("axis_failed") else "&mdash;"),
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
        # THE DECISION IS READ, AND IT NEVER DEFAULTS TO "included".
        #
        # This chain was: `disposition`, else "excluded" if `criteria_failed`, else
        # "included". Both are the OLD decision vocabulary. Records written since carry
        # their decision in `verdict`, have neither legacy field, and so fell through to the
        # final else -- so a page told a reader:
        #
        #     "This review's decision: included."
        #     "All limbs: Population holds, comparator fails, intervention holds,
        #      estimand fails."
        #
        # on a record whose stored verdict is EXCLUDED, with its own exclusion reasons
        # printed directly underneath. Found by an overnight adversarial hunt briefed to
        # look for a category error at a join, and verified by hand against
        # EARLY_RHYTHM_CONTROL_AF / NCT00184249 before anything was changed.
        #
        # 695 of 799 screening records across 3 topics: 225 stored EXCLUDED, 383
        # NEEDS_ADJUDICATION, 71 ELIGIBLE_NO_RESULTS_YET. A systematic review's screening
        # decision IS the review, and every one of these errs in the direction that inflates
        # the evidence base.
        #
        # A MISSING FIELD IS NOT A DECISION. The absence of an old-shape key is evidence
        # about our schema, not about whether a trial was included -- so where no decision
        # can be read the card says so, rather than choosing the reassuring answer. Same
        # rule as a SKIP that must not be counted as a PASS.
        # NOT THROUGH `p`. A DECISION IS A CONTROLLED VALUE, NOT PROSE.
        #
        # `p` applies `_tidy`, which is a PROSE cleaner and drops short fragments: it returns
        # '' for "excluded", '' for "needs adjudication", '' for "included", and keeps
        # "eligible no results yet" only because it is four words. Routing the verdict
        # through it replaced 501 of 551 wrong decisions with 501 BLANK ones -- a different
        # defect, not a fix.
        #
        # The old code never hit this because its fallback returned the bare literal
        # "included" without calling `p` at all; only the `disposition` branch was escaped.
        # So the bug and its camouflage were the same line.
        #
        # These values come from our own enum -- letters and underscores -- so they are
        # HTML-safe by construction, and they are rendered as themselves.
        _verdict = str(r.get("verdict") or "").strip()
        if _verdict:
            decided = re.sub(r"[^A-Za-z0-9 ]", "", _verdict.replace("_", " ")).lower()
        elif r.get("disposition"):
            decided = p(str(r["disposition"]))
        elif r.get("criteria_failed"):
            decided = "excluded"
        else:
            decided = "not recorded on this record"
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


def grade_section(res, p, canon=None, oid=None):
    g = res.get("grade")
    if not g:
        return ""
    # THE SEVENTH CONSUMER READING THE STORED LEVEL DIRECTLY. This card printed
    # "Certainty: low", the derivation string "start high; risk_of_bias serious (-1),
    # imprecision serious (-1); total -2 -> low", and the domain ratings that produce it --
    # on a page whose certainty column and abstract had both stopped publishing a level.
    # A panel that withholds a rating and prints the arithmetic ending in that rating is
    # asserting and denying in the same box, and the derivation is the worse half: it
    # names the withheld level in full.
    _res = _ga.resolve(canon, oid) if (canon and oid) else None
    # KEYED ON THE RESOLVED STATE, NOT ON A NAMED SUBSET OF IT. This read
    # `state == "PENDING"` and fell through to the stored value for every other non-RATED
    # state -- so sglt2-hf rendered "Certainty: high" for a WITHDRAWN pool, publishing a
    # rating about an estimate that has been taken down. That is the same false-claim
    # family as the pending case, left standing beside the fix for it, by the same hand in
    # the same hour. Anything the resolver does not call RATED has no level to publish, and
    # a state added later arrives guarded instead of unguarded.
    _withheld = bool(_res and _res.get("state") != "RATED")
    _pending = bool(_res and _res.get("state") == "PENDING")
    rows = ""
    for k in GRADE_DOMAINS:
        d = (g.get("domains") or {}).get(k)
        if not d:
            continue
        basis = str(d.get("basis_in_sources", "")).strip()
        # ONLY THE DOMAIN THAT IS ACTUALLY UNRESOLVED IS MARKED PENDING. Imprecision and
        # inconsistency were established independently of the risk-of-bias assessment and
        # marking them pending would assert something false about them. With the
        # risk-of-bias cell pending, no reader can total the domains into a rating, which
        # is the contradiction that needed removing.
        if _withheld and _pending and k == "risk_of_bias":
            rating = ("<strong>pending</strong>")
            basis = ("This domain is not final: %s Its recorded reasoning is kept with the "
                     "assessment rather than shown here as a settled judgement."
                     % _res.get("pending_because", ""))
        else:
            rating = p(d["rating"])
        rows += ("    <tr><th scope='col'>%s</th><td>%s</td><td><small>%s</small></td></tr>%s"
                 % (e(k.replace("_", " ").capitalize()), rating,
                    p(basis) if basis else "&mdash;", NL))
    start = ""
    if g.get("starting_point"):
        because = str(g.get("starting_point_because", "")).strip()
        start = ("  <p>Started at <strong>%s</strong>%s.</p>%s"
                 % (p(g["starting_point"]),
                    " &mdash; " + p(because) if because else "", NL))
    deriv = ("  <p><small>%s</small></p>%s" % (p(g["certainty_derivation"]), NL)
             if g.get("certainty_derivation") and not _withheld else "")
    if _withheld:
        deriv = ("  <p><small>The stored derivation of this rating is not shown, because "
                 "it ends in the level this review is withholding. It is held with the "
                 "assessment and will be published with the adjudicated "
                 "rating.</small></p>%s" % NL)
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
            % (NL, NL,
               ("<span title=\"%s\">%s</span>"
                % (e(str(_res.get("comment", ""))[:400]),
                   e(str(_res.get("cell") or "not rated")))) if _withheld
               else p(g["certainty"]),
               NL, start, deriv, NL, NL, rows, NL, NL,
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
    _k = (res["k"] if res.get("k") is not None else len(res.get("per_trial") or []))
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


def _fmt_v(v):
    """Numbers as the page prints them: no trailing zeros, no scientific notation."""
    if v is None:
        return "not recorded"
    s = ("%.3f" % float(v)).rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def _interval_caption(pooled, null_value):
    """THE CAPTION IS A FUNCTION OF THE STORED BOUNDS, not a fixed string.

    The previous caption asserted 'The interval is drawn CROSSING the no-difference line
    BECAUSE IT DOES' unconditionally. It read no interval at all -- not ci_low, not ci_high,
    not the null -- so it printed over anything. Measured: 27 of 36 captions sat over an
    interval that EXCLUDES the null, including HR 0.749 (0.664 to 0.845).

    Replacing it with a better fixed sentence would fix one page and leave the rest wrong AND
    HARDER TO FIND, because the replacement is defensible wherever it was tested. So the
    sentence is derived, and when the bounds are missing it says that rather than guessing.
    """
    base = ("Projected from the canonical object, so it carries the same k, the same pooled "
            "estimate and the same interval as the paper and cannot drift from them. ")
    lo, hi = pooled.get("ci_low"), pooled.get("ci_high")
    if lo is None or hi is None:
        return base + ("The interval is not described here because its bounds are not "
                       "recorded on the object.")
    nv = null_value if null_value is not None else 1
    excludes = (lo > nv and hi > nv) or (lo < nv and hi < nv)
    if excludes:
        return base + ("The interval is drawn to scale against the no-difference line, which "
                       "it EXCLUDES: %s to %s, with no difference at %s."
                       % (_fmt_v(lo), _fmt_v(hi), _fmt_v(nv)))
    return base + ("The interval is drawn CROSSING the no-difference line because it does: "
                   "%s to %s spans %s. A graphical abstract travels without its caption, and "
                   "one showing a favourable point estimate without showing that its interval "
                   "includes no effect would overstate a null result."
                   % (_fmt_v(lo), _fmt_v(hi), _fmt_v(nv)))



def _analysed_n_for_outcome(canon, res):
    """(total, matched, wanted) analysed participants for THIS outcome's trials only.

    Keyed on registration id. Returns the counts so the caller can refuse when a
    contributing trial could not be matched, rather than publishing a partial sum.
    """
    # ONE ENTRY PER CONTRIBUTING TRIAL, NOT PER IDENTIFIER STRING. The first version
    # collected every id on every per_trial row into one set, so a two-trial pool carrying
    # both `nct` and `trial_id` produced FOUR "wanted" ids, matched two, and tripped the
    # caller's refusal on every outcome in the corpus. A guard that fires everywhere is as
    # useless as one that never fires, and this one would have blanked a number that was
    # finally correct.
    wanted = []
    for r in (res.get("per_trial") or []):
        if not isinstance(r, dict):
            continue
        ids = {str(r[k]).strip() for k in ("nct", "trial_id", "id") if r.get(k)}
        if ids:
            wanted.append(ids)
    if not wanted:
        return 0, 0, 0
    trials = [t for t in ((canon.get("inputs") or {}).get("trials") or [])
              if isinstance(t, dict)]
    total, matched = 0, 0
    for ids in wanted:
        for t in trials:
            keys = {str(t.get(k)).strip() for k in ("nct", "id", "name") if t.get(k)}
            if keys & ids:
                matched += 1
                for a in (t.get("arms") or []):
                    if isinstance(a, dict):
                        total += a.get("participants") or 0
                break
    return total, matched, len(wanted)


def visual_abstract(canon, res, outcome, p):
    """The graphical abstract, projected. Under the same gates as any figure."""
    pooled = res.get("pooled") or {}
    if pooled.get("point") is None:
        return ""
    # THE PARTICIPANT COUNT BELONGED TO THE PAGE, NOT TO THE POOL, AND IT TRAVELLED.
    #
    # This summed arms across EVERY trial on the object. On iv-iron-hf all four visual
    # abstracts read "2 trials, 6,716 participants" -- 6,716 being the sum over all six
    # pools (2,245 + 1,105 + 0 + 0 + 3,065 + 301), while the two-trial pool each abstract
    # names holds 2,245. The total silently absorbed HEART-FID's 3,065 and CONFIRM-HF's
    # 301, single-trial pools for entirely different outcomes. So it told a reader a
    # two-trial result rested on three times the evidence it does, four times over, and it
    # refuted itself on its own face: AFFIRM-AHF plus IRONMAN is 2,245.
    #
    # A visual abstract is a STANDALONE graphic. It travels without the page that would
    # have corrected it, which makes a wrong number here worse than the same number in
    # prose.
    #
    # JOINED ON THE REGISTRATION ID, not the trial name. per_trial rows carry `nct` and
    # `trial_id`; matching on acronym is the bad-key failure that gave three parties three
    # different answers on the KCCQ outcome.
    n_total, _n_matched, _n_wanted = _analysed_n_for_outcome(canon, res)
    _n_total_note = ""
    # THE DISAGREEING INTERVAL, wherever it is stored. Hartung-Knapp intervals
    # live under at least eight different keys in this corpus; reading one of
    # them found 2 pools and reading all of them found 6.
    def _hk(node, depth=0):
        import re as _re
        if depth > 6:
            return None
        if isinstance(node, dict):
            for k, v in node.items():
                if _re.search(r"hartung|knapp|hksj|knha", str(k), _re.I)                         and isinstance(v, dict) and v.get("ci_low") is not None                         and v.get("ci_high") is not None:
                    return (v["ci_low"], v["ci_high"])
                got = _hk(v, depth + 1)
                if got:
                    return got
        elif isinstance(node, list):
            for v in node[:40]:
                got = _hk(v, depth + 1)
                if got:
                    return got
        return None
    _alt_iv = _hk(res)
    if not n_total:
        # NAME THE REASON, DO NOT JUST WITHHOLD THE NUMBER. On alirocumab-lipid
        # two trials recovered on 2026-08-19 carry `enrolled` but no `arms`, so
        # the ANALYSED total cannot be summed even though enrolment can. The old
        # rendering ("n/a participants") invited the reading that no count
        # existed anywhere, when 4,431 enrolled is recorded on the object and is
        # simply a different quantity.
        _cn = {str(x.get("nct") or x.get("trial_id")) for x in (res.get("per_trial") or [])
               if isinstance(x, dict)}
        _tr = [t for t in ((canon.get("inputs") or {}).get("trials") or [])
               if isinstance(t, dict) and str(t.get("nct") or t.get("id")) in _cn]
        _no_arms = [t for t in _tr if not t.get("arms")]
        if _no_arms and _tr:
            _enr = sum(int(t.get("enrolled") or 0) for t in _tr)
            _n_total_note = ("%d of %d contributing trials record no analysed arm counts"
                             % (len(_no_arms), len(_tr)))
            if _enr and all(t.get("enrolled") for t in _tr):
                _n_total_note += ("; %s were enrolled across all %d, but enrolment is not "
                                  "the analysed total" % ("{:,}".format(_enr), len(_tr)))
    if _n_wanted and _n_matched != _n_wanted:
        # AND IT REFUSES RATHER THAN UNDERSTATING. If a contributing trial cannot be
        # matched to an arm count, the sum is not this pool's total and must not be shown
        # as one -- a quietly smaller wrong number is not an improvement on a larger one.
        n_total = 0
        _n_total_note = ("%d of %d contributing trials could not be matched to a "
                         "registered arm count" % (_n_wanted - _n_matched, _n_wanted))
    g = res.get("grade") or {}
    sens = res.get("sensitivity") or {}
    loo = ""
    rows = [a for a in (sens.get("analyses") or []) if isinstance(a, dict)]
    kept = [a for a in rows if a.get("still_excludes_null")]
    if rows:
        # A SENTENCE ABOUT A NUMBER MUST BE A FUNCTION OF THAT NUMBER.
        # The previous version appended "the estimate does not survive removal of the
        # largest trial" unconditionally, reading `kept` for the count and then ignoring it
        # for the claim. It printed "2 of 2 refits still exclude no difference; the estimate
        # does not survive removal of the largest trial" -- which is not merely contradictory,
        # it is false: if every refit excludes the null then the estimate DOES survive.
        # Measured before the fix: 6 of 12 emitted sentences were self-falsifying.
        _k = res.get("k") if res.get("k") is not None else len(res.get("per_trial") or [])

        # ABSENT IS NOT NEGATIVE, AND NOT EVERY SENSITIVITY ROW IS A REFIT.
        #
        # `kept` counts truthy `still_excludes_null`. On tigecycline-ciai that field is absent
        # from all eight rows, so the count was 0 and the served page asserted "no refit
        # excludes no difference; the estimate does not survive removal of any single trial".
        # Hand-derived from the intervals the object DOES carry, the truth is 1 of 3.
        #
        # Two errors produced that one sentence:
        #   1. None was read as False. A missing verdict is not a computed negative -- the
        #      same absence-as-negative class this corpus has been audited for all day.
        #   2. Five of those eight rows are not leave-one-out at all: they change the summary
        #      statistic, the model, the event definition or the analysis population. A
        #      leave-one-out sentence must be a function of the LEAVE-ONE-OUT rows only.
        #
        # So: select the refits, derive exclusion from the interval where the flag is absent,
        # and refuse the sentence outright when nothing is derivable.
        def _is_refit(a):
            blob = ("%s %s" % (a.get("id") or "", a.get("changed") or "")).lower()
            return ("leave-out" in blob or "leave one out" in blob
                    or "by removing" in blob or a.get("omitted") is not None)

        def _excludes(a):
            """True / False / None -- None means NOT COMPUTED and never counts as False."""
            flag = a.get("still_excludes_null")
            if flag is not None:
                return bool(flag)
            r = a.get("result") if isinstance(a.get("result"), dict) else a
            lo, hi = r.get("ci_low"), r.get("ci_high")
            null = outcome.get("null_value", 1)
            if lo is None or hi is None:
                return None
            return not (lo <= null <= hi)

        _refits = [a for a in rows if _is_refit(a)]
        _decided = [a for a in _refits if _excludes(a) is not None]
        _n, _tot = len([a for a in _decided if _excludes(a)]), len(_decided)
        _undecided = len(_refits) - len(_decided)
        _suffix = ("" if not _undecided else
                   " A further %d refit(s) carry no interval and are not counted."
                   % _undecided)

        if not _refits:
            loo = ("No leave-one-out refit is recorded for this outcome. The %d sensitivity "
                   "analyses here vary the summary statistic, the model, the event definition "
                   "or the analysis population; none removes a trial, so none of them can say "
                   "whether the estimate survives removal of one." % len(rows))
        elif not _decided:
            loo = ("Leave-one-out: %d refit(s) are recorded and none carries an interval or a "
                   "verdict, so whether the estimate survives removal of a single trial is "
                   "NOT ESTABLISHED. That is an absence, not a negative result."
                   % len(_refits))
        elif _k == 2:
            # GENERALISED TO EVERY k=2 POOL, not special-cased to one topic. With two trials
            # a leave-one-out refit IS the other trial, so it cannot be robustness evidence
            # however the arithmetic comes out, and saying so is the honest reading.
            loo = ("Leave-one-out with two trials: each refit is simply the other trial, so "
                   "this is not robustness evidence. %d of %d single-trial refits exclude no "
                   "difference." % (_n, _tot))
        elif _n == _tot:
            loo = ("Leave-one-out: all %d refits still exclude no difference; the estimate "
                   "survives removal of any single trial.%s" % (_tot, _suffix))
        elif _n == 0:
            loo = ("Leave-one-out: none of the %d refits excludes no difference; the estimate "
                   "does not survive removal of any single trial.%s" % (_tot, _suffix))
        else:
            loo = ("Leave-one-out: %d of %d refits still exclude no difference; the estimate "
                   "does not survive removal of every single trial.%s"
                   % (_n, _tot, _suffix))
    return fig(visual_abstract_svg(
        canon.get("title", ""), canon.get("question", ""),
        (res["k"] if res.get("k") is not None else len(res.get("per_trial") or [])),
        "{:,}".format(n_total) if n_total else None,
        pooled.get("measure", ""), pooled["point"], pooled.get("ci_low"),
        pooled.get("ci_high"), outcome.get("null_value", 1),
        # THE EIGHTH CONSUMER, AND IT SAT INSIDE A FIGURE. This read `grade.certainty`
        # straight off the object, so the visual abstract printed "GRADE certainty: low"
        # on a page whose certainty column, GRADE card and abstract had all stopped
        # publishing a level. My own verification of that page checked the column, the
        # card and the abstract -- and not the figure text, which is reach reported as
        # coverage inside a verification step. A corpus gate reading the DELIVERED page
        # found it; nothing that read the generator could have.
        _ga.resolve(canon, outcome.get("id"))["cell"]
        if outcome.get("id") else g.get("certainty"),
        outcome.get("name", ""), loo, _n_total_note, _alt_iv),
        "Visual abstract", "visual-abstract.svg",
        _interval_caption(pooled, outcome.get("null_value", 1)))


def _agreement_statement(rb, ag, two):
    """What to say about inter-assessor agreement, which right now is: not the rate.

    SUPPRESSED WITH A REASON, NOT SILENTLY OMITTED. The measured disagreement on these
    records is not a property of the evidence -- it is an artefact of how the second
    assessor was asked. The blinding prompt refuses to send any text containing a RoB 2
    verdict word, and this project's own decision rule ("a domain that cannot be judged
    from the sources read is NO_INFORMATION, never SOME_CONCERNS") is written in exactly
    those words. So the rule could not reach assessor 2 by construction, and the two
    readers answered under different rules. The signature is one-directional disagreement
    per domain with the sign flipping between D1-D3 and D4-D5 -- 5 of 138 domain
    disagreements run counter to their own domain's dominant direction.

    A page showing total disagreement with no adjudication publishes a harness artefact as
    a finding about someone else's trials. Either the adjudication is shown or the rate is
    withheld; showing the second without the first is the worst of both.
    """
    if not two:
        return ("One assessor. No inter-assessor comparison is available for this "
                "review, and none is implied by the table above.")
    n = ag.get("per_domain_total") or 0
    # THE EXPLANATION THIS SENTENCE USED TO GIVE WAS WRONG, AND IT WAS OURS.
    #
    # It said the blinding prompt withheld the decision rule -- that the guard refuses any
    # text containing a verdict word, that our default rule is written in verdict words,
    # and that the two assessors therefore answered under different rules. Checked against
    # the code the run actually used: the guard scans the assembled FACT BLOCKS only and
    # never the header, and the header carries the rule in full -- "a domain that cannot
    # be judged from the facts given is NO_INFORMATION, never LOW" -- verbatim in commit
    # 0f6764f42, dated 2026-08-21, which is the version the second assessor ran under.
    # The rule was transmitted. The harness-artefact explanation is withdrawn.
    #
    # AND THE DIRECTIONS RUN THE OTHER WAY FROM WHAT IT PREDICTED. A reader who never got
    # the rule would score LOW where the other said NO_INFORMATION. On D1 to D3 the
    # opposite happens: assessor 1 gives a judgement and assessor 2 answers
    # NO_INFORMATION (26, 11 and 16 times respectively), which is the rule being applied
    # MORE strictly, not less. On D4 and D5 assessor 2 is the more lenient one. That is a
    # domain-dependent reading difference between two readers, and it is not explained by
    # a missing instruction.
    return (
        "This assessment is DUAL &mdash; two assessors from different model families, the "
        "second asked blind. <strong>The agreement rate is withheld pending "
        "adjudication.</strong> Both readers were given this review’s decision rule; "
        "an earlier version of this sentence said the blinding had withheld it, and that "
        "was wrong. What the %d domain comparison(s) show is a reading difference that "
        "runs in OPPOSITE directions by domain &mdash; on domains 1 to 3 the second "
        "assessor more often declines to judge at all, and on domains 4 and 5 it more "
        "often judges low. A single agreement rate averages those two behaviours into one "
        "number that describes neither. <strong>Both assessors’ per-result judgements "
        "are shown in the table above, unadjudicated, and neither is this review’s "
        "finding.</strong> No adjudication has been performed, so this review holds no "
        "final risk-of-bias judgement for these results."
        % n)


def rob_figure(canon, p):
    """Risk-of-bias traffic light, both assessors, from the stored RoB-2 block."""
    # ONE READER FOR BOTH SCHEMAS. This asked for canon["rob2"] while 30 of 31 stores
    # write canon["risk_of_bias"], so 29 of the 30 rendered curated topics printed the
    # not-computable box below OVER A STORE THAT HELD AN ASSESSMENT. The one topic that
    # rendered, arni-hfref, is the one object that writes `rob2` -- which is how the
    # cause was identified rather than guessed. Assessors now come from an ORDERED LIST:
    # the old `assessor_1_openai` / `assessor_2_google` keys named the wrong labs (the
    # curated pairs are anthropic + openai) and would have produced a PARTIAL panel,
    # which is harder to notice than a blank one.
    rb = rob_block(canon) or {}
    trials = rb.get("trials") or []
    if not trials:
        return fig(not_computable_svg(
            "Risk-of-bias traffic light",
            "No per-domain RoB-2 assessment is stored in this object."),
            "Risk of bias", "rob-traffic-light.svg",
            "Not drawn, because there is nothing to draw it from.")
    doms = [d.get("domain") for d in trials[0].get("domains", [])]
    a = rb.get("assessors") or [{}]

    def cell(trial_name, domain, idx):
        for t in trials:
            if t.get("trial") != trial_name:
                continue
            for dd in t.get("domains", []):
                if dd.get("domain") == domain:
                    js = dd.get("judgements") or []
                    # One assessor means ONE column. Never repeat assessor 1 into the
                    # second: a panel showing one reader's verdicts twice is a false
                    # claim of independent agreement.
                    return js[idx] if idx < len(js) else None
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
    fams = [x.get("model_family") or x.get("name") or "assessor %d" % (i + 1)
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
    k = (res["k"] if res.get("k") is not None else len(res.get("per_trial") or []))
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
    # Reads either schema through rob_block. The native-only sections below
    # (`carried`, `disagreements`, `adjudication`) exist on arni-hfref alone and are
    # gated on the RAW block rather than assumed -- a KeyError here would have taken the
    # whole page down, and a silent "" would have been the not-computable bug again.
    raw = canon.get("rob2") or {}
    rb = rob_block(canon)
    if not rb or not rb.get("trials"):
        return ""
    a = rb.get("assessors") or [{}]
    f1 = a[0].get("model_family") or a[0].get("name") or "assessor 1"
    f2 = (a[1].get("model_family") or a[1].get("name")) if len(a) > 1 else None
    ag = rb.get("agreement") or {}
    two = f2 is not None

    def _j(seq, i):
        return seq[i] if isinstance(seq, list) and i < len(seq) else ""

    # RoB 2 HAS THREE OVERALL CATEGORIES: Low, Some concerns, High. "No information" is a
    # SIGNALLING-QUESTION response, not an overall judgement -- Handbook 8.2.3 -- and this
    # table was printing it as one on two of the four results. The domain glyph was fixed
    # earlier today and the overall row was not covered by that fix, which is the same
    # miss twice: the search was for places rendering DOMAIN judgements, and this renders
    # an OVERALL one.
    #
    # It is not silently blanked. An assessor who answered NO_INFORMATION reached no
    # overall judgement, and saying so is a fact about our reach; printing nothing would
    # read as agreement with the other column.
    def _ov(v):
        if str(v or "").strip().upper().replace(" ", "_") == "NO_INFORMATION":
            return ("<em>no overall judgement reached</em> &mdash; this assessor answered "
                    "&ldquo;no information&rdquo;, which RoB&nbsp;2 defines as a response "
                    "to a signalling question and not as one of the three overall "
                    "categories (low, some concerns, high)")
        return p(v)

    # A TRIAL ACRONYM IS A TYPED FIELD, NOT PROSE. `p()` runs the prose tidier, which
    # de-shouts any all-caps word of three or more letters that contains a vowel -- so
    # SCORED rendered as "Scored" in every row of this table. SOLOIST-WHF escaped only
    # because its hyphen fails the pattern's boundary, which is luck rather than a rule.
    # Renaming a named trial in a risk-of-bias table is the same class as the other
    # identifier defects on this page: a typed value pushed through a text transform.
    def _trial(v):
        return e(str(v or ""))

    def _outcome_label(oid):
        for o in (canon.get("outcomes") or []):
            if isinstance(o, dict) and o.get("id") == oid:
                return o.get("name") or oid
        return oid or ""

    # A COLUMN WITH NO DATA IS NOT A COLUMN WITH EMPTY VALUES. `carried` exists on exactly
    # ONE object in 155 -- arni-hfref's native rob2 block. Rendering it for the other 30
    # stores produced a column of blanks, which reads as "nothing was carried" rather than
    # "this review does not record a carry". Omitted when nothing supplies it.
    has_carried = any(dm.get("carried") for t in rb["trials"] for dm in t["domains"])
    rows = ""
    for t in rb["trials"]:
        for dm in t["domains"]:
            js = dm.get("judgements") or []
            mark = ("yes" if dm.get("agreed") else "<strong>NO</strong>") \
                if dm.get("agreed") is not None else "one assessor"
            rows += ("    <tr><td>%s</td><td>%s</td><td>%s %s</td><td>%s</td><td>%s</td>"
                     "<td>%s</td>%s</tr>%s"
                     % (_trial(t["trial"]), p(_outcome_label(t.get("outcome"))),
                        dm.get("domain"), p(dm.get("domain_name")),
                        p(_j(js, 0)), p(_j(js, 1)), mark,
                        ("<td>%s</td>" % p(dm.get("carried", ""))) if has_carried else "",
                        NL))
    # THE RESULT, NOT JUST THE TRIAL. RoB 2 assesses a RESULT, so two rows carrying the
    # same trial name and different judgements are unreadable without it: this table
    # showed "SOLOIST-WHF | some concerns | no information" and "SOLOIST-WHF | HIGH |
    # some concerns" with nothing to say which pool each belonged to. The unit of
    # assessment is named at the top of the card and was then absent from every row.
    ov = "".join(
        "    <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>%s"
        % (_trial(t["trial"]), p(_outcome_label(t.get("outcome"))),
           _ov(_j(t.get("overall"), 0)), _ov(_j(t.get("overall"), 1)),
           ("yes" if t.get("overall_agreed") else "<strong>NO</strong>")
           if t.get("overall_agreed") is not None else "one assessor", NL)
        for t in rb["trials"])
    dis = ""
    if raw.get("disagreements"):
        rb = dict(rb, disagreements=raw["disagreements"],
                  adjudication=raw.get("adjudication"))
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
            "  <table>%s    <tr><th scope='col'>Trial</th><th>Result assessed</th>"
            "<th>Domain</th><th>Assessor 1 (%s)</th>"
            "<th>Assessor 2 (%s)</th><th>Agreed</th>%s</tr>%s%s"
            "  </table>%s</div>%s"
            "<div class='card'>%s  <h3>Overall judgement per trial</h3>%s"
            "  <table>%s    <tr><th scope='col'>Trial</th><th>Result assessed</th>"
            "<th>Assessor 1 (%s)</th>"
            "<th>Assessor 2 (%s)</th><th>Agreed</th></tr>%s%s  </table>%s</div>%s"
            "<div class='card'>%s  <h3>Inter-assessor agreement</h3>%s  <p>%s</p>%s"
            "  <p>%s</p>%s</div>%s%s%s"
            % (NL, NL, p(rb.get("assembler_excluded", "")), NL,
               p(rb.get("variant", "")), NL, p(rb.get("unit_of_assessment", "")), NL,
               p(a[0].get("model", "")), p(f1),
               p(a[1].get("model", "")) if len(a) > 1 else
               e("no second assessor is recorded for this review"),
               p(f2) if f2 else e("none"),
               p(rb.get("blinding", "")), NL,
               NL, p(f1), p(f2),
               ("<th>Carried</th>" if has_carried else ""), NL, rows, NL, NL,
               NL, NL, NL, p(f1), p(f2), NL, ov, NL, NL,
               NL, NL, _agreement_statement(rb, ag, two), NL,
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

def endpoint_correction_card(canon, p):
    """A correction to what this page said about a named trial's conduct.

    RENDERED, NOT JUST STORED. The correction was written onto the object and did not
    appear on the page, which is the whole failure repeating: a fact recorded where no
    reader meets it is not a correction, it is a note to ourselves. Placed at the head of
    the risk-of-bias card because that is the section whose reasoning rested on the wrong
    description.
    """
    k = next((x for x in sorted(canon) if str(x).startswith("endpoint_history_correction_")
              and isinstance(canon[x], dict)), None)
    if not k:
        return ""
    c = canon[k]
    q = "".join("    <li><q>%s</q></li>%s" % (e(str(x)), NL)
                for x in ((c.get("source") or {}).get("quotes") or []))
    return ("<div class='card warn'>%s  <h2>Correction &mdash; what this page said about "
            "the trials&rsquo; endpoint history</h2>%s"
            "  <p><strong>What this review said.</strong> %s</p>%s"
            "  <p><strong>What is true.</strong> %s</p>%s"
            "  <p><small>Source: %s &mdash; <a href='%s' rel='noopener'>%s</a></small></p>%s"
            "  <ul>%s%s  </ul>%s"
            "  <p><strong>What this does not change.</strong> %s</p>%s"
            "  <p><strong>Bearing on the pending adjudication.</strong> %s</p>%s"
            "  <p><small><strong>Unresolved:</strong> %s</small></p>%s</div>%s"
            % (NL, NL, p(c.get("what_this_object_said", "")), NL,
               p(c.get("what_is_true", "")), NL,
               e(str((c.get("source") or {}).get("layer", ""))),
               e(str((c.get("source") or {}).get("url", ""))),
               e(str((c.get("source") or {}).get("staged_as", ""))), NL,
               NL, q, NL,
               p(c.get("what_this_does_NOT_change", "")), NL,
               p(c.get("bearing_on_the_pending_adjudication", "")), NL,
               p(c.get("unresolved", "")), NL, NL))


def population_card(res, p):
    """Which population this estimate belongs to, beside the estimate itself."""
    b = res.get("what_population_this_estimate_belongs_to")
    if not isinstance(b, dict):
        return ""
    return ("<div class='card warn'>%s  <h3>What population this estimate belongs to</h3>%s"
            "  <p>%s</p>%s  <p>%s</p>%s"
            "  <p><small>%s</small></p>%s  <p><small>%s</small></p>%s</div>%s"
            % (NL, NL, p(b.get("statement", "")), NL,
               p(b.get("why_it_matters_here", "")), NL,
               p(b.get("derived_not_asserted", "")), NL,
               p(b.get("not_stated_here_because_no_source_is_held", "")), NL, NL))


def bibliography_card(canon, p):
    """The reference list a reader would look up, and what is knowingly missing."""
    r = ((canon.get("manuscript") or {}).get("references") or {})
    inc = r.get("included_studies") or []
    reg = r.get("regulatory_documents") or []
    met = r.get("methods_and_guidance") or []
    if not (inc or reg or met):
        return ""

    def li(items, keys):
        out = ""
        for x in items:
            if not isinstance(x, dict):
                continue
            label = next((str(x[k]) for k in keys if x.get(k)), "")
            url = x.get("publication_url") or x.get("url") or ""
            out += ("    <li>%s%s</li>%s"
                    % (e(label),
                       (" &mdash; <a href='%s' rel='noopener'>%s</a>" % (e(str(url)), e(str(url))))
                       if url else "", NL))
        return out

    om = canon.get("known_omitted_analyses") or []
    omh = ""
    if om:
        omh = ("  <h3>Knowingly not included</h3>%s  <ul>%s%s  </ul>%s"
               % (NL, NL,
                  "".join("    <li><strong>%s</strong> %s <br><small>%s</small></li>%s"
                          % (e(str(x.get("status", ""))), p(x.get("what", "")),
                             p(x.get("why_it_is_not_folded_in", "")), NL)
                          for x in om if isinstance(x, dict)), NL))
    return ("<div class='card'>%s  <h2>References</h2>%s"
            "  <h3>Included studies</h3>%s  <ul>%s%s  </ul>%s"
            "  <h3>Regulatory documents</h3>%s  <ul>%s%s  </ul>%s"
            "  <h3>Methods and guidance</h3>%s  <ul>%s%s  </ul>%s%s</div>%s"
            % (NL, NL, NL, NL, li(inc, ("publication", "label")), NL,
               NL, NL, li(reg, ("label",)), NL,
               NL, NL, li(met, ("label",)), NL, omh, NL))
