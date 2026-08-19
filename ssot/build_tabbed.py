"""Build the tabbed SSOT page.

Drives build_app_v2's existing per-outcome machinery and the rebuilt projectors,
rather than editing the 1035-line original in place. The original stays the FLAT
control -- `build_app_v2.py <obj> <out>` still emits the pre-tab layout
byte-identically, which is what every A/B is measured against.

Usage:  python ssot/build_tabbed.py <object.json> <out.html>
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_app_v2 as G          # noqa: E402

# The base generator carries its own fmt() and it is what renders the pooled
# result card -- which is why "HR 0.8392 (0.7429 to 0.948)" survived rounding the
# projectors. It is patched HERE rather than in build_app_v2.py itself because
# that module is the flat control: running it standalone must still emit the
# pre-tab layout unchanged, or every A/B measured against it becomes meaningless.
# The rounding therefore belongs to this build, not to the baseline.
#
# FOUR significant figures, not three (changed 2026-08-16). At three, this build
# SILENTLY ALTERED verified estimates: sotagliflozin's object holds
# HR 0.7171 (0.6246 to 0.8234) and the page rendered 0.717 (0.625 to 0.823), so
# the string 0.7171 appeared NOWHERE in the artefact. The same rounding moved
# SGLT2 (0.7785 -> 0.778, 0.7296 -> 0.73), IV iron (0.8066 -> 0.807) and
# alirocumab (-54.66 -> -54.7). ARNI was unaffected only by coincidence: 0.872,
# 0.746 and 1.02 are already three figures, which is why the shell looked correct
# on the one page that had it.
#
# Two things then break. The index card and the page disagree, so the page fails
# the three-surface check outright. And a value established by a day of source
# work is replaced during a REBUILD, which is meant to change layout and nothing
# else. sig()'s own default stays 3 -- the argument in its docstring about false
# precision is sound and other callers keep it. This is the one place where the
# displayed number must equal the verified number.
def _round_base_fmt():
    import projectors as _pj
    _orig = G.fmt

    def _fmt(x):
        if isinstance(x, float):
            return _pj.sig(x, 4)
        return _orig(x)
    G.fmt = _fmt


_round_base_fmt()
import projectors as pj           # noqa: E402
import projectors2 as p2
import paper as pp
import wysiwyg as wy          # noqa: E402

NL = pj.NL

def _v(x, absent="—", limit=None):
    """Escape a value for HTML, rendering ABSENCE as a dash rather than as the word "None".

    THE DEFECT THIS CLOSES, CAUGHT BY THE PRE-PUSH GATE ON SIX PAGES AT ONCE. The builder used
    `_v((x))` in fifty places. `str(None)` is the four-character string "None", so an absent
    field rendered as a table cell reading None -- and the criteria table on six pages showed

        limb  |  value  |  derived from
        None  |  None   |  None

    which is not an absence marker. IT IS A VALUE, and a reader has no way to tell it from a
    field whose content is the word None. This is the leak class recorded in the project's own
    lessons: a Python None reaching rendered output, which previously shipped to 1110
    dashboards before anyone saw it.

    `str()` IS THE BUG, NOT THE ESCAPING. Escaping "None" faithfully produces "None".
    """
    if x is None:
        return absent
    t = str(x)
    if limit:
        t = t[:limit]
    return html.escape(t) if t.strip() else absent

e = html.escape

READER_JS = """
<script>
(function(){
 var K='rmreader:'+(document.title||'page');
 function load(){try{return JSON.parse(localStorage.getItem(K)||'{}')}catch(x){return {}}}
 function save(s){try{localStorage.setItem(K,JSON.stringify(s))}catch(x){}}
 var st=load();
 var d=document.getElementById('draft');
 if(d){
  d.value=st.draft||'';
  d.addEventListener('input',function(){st.draft=d.value;save(st);});
  document.addEventListener('click',function(ev){
   var c=ev.target.closest('.chip'); if(!c) return;
   d.value += (d.value && !/\\n$/.test(d.value) ? '\\n' : '') + c.dataset.ins;
   st.draft=d.value; save(st); d.focus();
  });
 }
})();
</""" + """script>
"""


def paper_studio(canon, res, p):
    """A drafting surface carrying a PROJECTED manuscript, not an empty box.

    Every paragraph is assembled from object fields. Sections the object cannot
    back say so in the review's own voice rather than leaving a gap -- an
    introduction or discussion generated without a source would be argument that
    nothing in this review supports."""
    pooled = res.get("pooled") or {}
    if not pooled.get("point"):
        return ""
    het = res.get("heterogeneity") or {}
    g = res.get("grade") or {}
    sc = canon.get("screening") or {}
    sens = res.get("sensitivity") or {}
    ce = res.get("cross_engine") or {}
    o = canon["outcomes"][0]
    ks = res.get("k_status") or {}
    meas = _v((pooled.get("measure", "")))

    def li(h, body):
        return ("    <li><strong>%s.</strong> %s</li>%s" % (h, body, NL)) if body else ""

    draft = (
        li("Question", p(canon["question"]))
        + li("Outcome and estimand", p(o["name"]))
        + li("Search", p(sc.get("search_note", "")))
        + li("Eligibility", p(sc.get("eligibility", "")))
        + li("Synthesis method",
             "%s model, estimator %s, k = %s%s."
             % (p(str(res.get("model", ""))),
                p(str(res.get("estimator_used") or res.get("estimator", ""))),
                pj.fmt(res.get("k")),
                " (a LOWER BOUND, not a settled count)" if ks.get("is_lower_bound")
                else ""))
        + li("Result",
             "Pooled %s %s (%s to %s, %s%% interval). I-squared %s%%, tau-squared %s."
             % (meas, pj.fmt(pooled["point"]), pj.fmt(pooled["ci_low"]),
                pj.fmt(pooled["ci_high"]), pj.fmt(pooled.get("ci_level", 95)),
                pj.fmt(het.get("i2")), pj.fmt(het.get("tau2"))))
        + li("Robustness", p(sens.get("leave_one_out_finding", "")))
        + li("Cross-engine check", p(ce.get("agreement", "")))
        + li("Certainty",
             ("GRADE certainty: %s. %s" % (p(g["certainty"]),
                                           p(g.get("certainty_derivation", ""))))
             if g.get("certainty") else "")
        + li("What this review could not settle", p(sc.get("known_limitation", "")))
        + li("Introduction and Discussion",
             "Not written here. The object holds no background or interpretation, "
             "and generating either would be argument that no source in this "
             "review supports. Left for the author, and its absence stated rather "
             "than filled.")
    )
    snips = [("Pooled estimate",
              "%s %s (%s to %s)" % (meas, pj.fmt(pooled["point"]),
                                    pj.fmt(pooled["ci_low"]),
                                    pj.fmt(pooled["ci_high"]))),
             ("Trials pooled", "k = %s" % pj.fmt(res.get("k")))]
    if het.get("i2") is not None:
        snips.append(("Heterogeneity", "I-squared %s%%" % pj.fmt(het["i2"])))
    if g.get("certainty"):
        snips.append(("Certainty", "GRADE certainty: %s" % _v((g["certainty"]))))
    chips = "".join('    <button type="button" class="chip" data-ins="%s">%s'
                    '</button>%s' % (v, k, NL) for k, v in snips)

    cites = canon.get("citations") or {}
    pol = (canon.get("citation_policy") or {}).get("ratio") or {}
    refs = ""
    # BIBLIOGRAPHIC TEXT ARRIVES PRE-ENCODED AND MUST BE UNESCAPED BEFORE IT IS
    # ESCAPED. PubMed returns 'Echeverr&#xed;a', an ideographic space as
    # '&#x3000;', and non-breaking spaces as '&#xa0;'. p() escapes, so the reader
    # saw the literal characters '&amp;#xed;' -- seven times on ARNI_HF_REVIEW,
    # the flagship, in its reference list.
    #
    # THIRD ORIGIN OF ONE CLASS, and the first that is not our own doing: the
    # first was markup we generated and escaped twice, the second an entity used
    # as a fallback string, this one is text that was already encoded when it
    # reached us. The previous fix addressed NAMED entities; these are NUMERIC.
    #
    # unescape-then-escape is the correct normalisation for any field that MAY be
    # pre-encoded: a plain value passes through untouched and a pre-encoded one is
    # repaired. scripts/double_escape_gate.py is the check that makes this stick,
    # because this class has now recurred three times after being written down.
    def _pre(v):
        return html.unescape(v) if isinstance(v, str) else v

    for i, (pmid, c) in enumerate(sorted(cites.items()), 1):
        bits = [p(_pre(c.get("authors_vancouver", ""))), p(_pre(c.get("title", ""))),
                p(_pre(c.get("journal", ""))), pj.fmt(c.get("year"))]
        vol = "%s%s%s" % (c.get("volume") or "",
                          "(%s)" % c["issue"] if c.get("issue") else "",
                          ":%s" % c["pages"] if c.get("pages") else "")
        st = c.get("link_status")
        note = c.get("doi_link_note") or c.get("link_note")
        refs += ("    <li>%s. <em>%s</em> %s;%s. "
                 "<a href='%s'>PMID %s</a> [HTTP %s]%s%s</li>%s"
                 % (bits[0], bits[1], bits[2], vol or bits[3],
                    e(c.get("url", "")), e(pmid), _v((st)),
                    (" <a href='%s'>doi</a>" % e(c["doi_url"])) if c.get("doi_url") else "",
                    (" <small>%s</small>" % p(_pre(note))) if note else "", NL))
    ratio = ("  <p><small>%s of %s references trace to a record this review "
             "adjudicated; %s background. A citation in no screening record is a "
             "claim the review never assessed.</small></p>%s"
             % (pj.fmt(pol.get("trace_to_included_or_excluded")),
                pj.fmt(pol.get("total")), pj.fmt(pol.get("background")), NL)
             if pol else "")

    return ("<div class='card'>%s  <h3>Projected manuscript draft</h3>%s"
            "  <p><small>Every paragraph below is assembled from the canonical "
            "object at build time. Nothing here is written by the generator, and "
            "nothing recomputes when you open the page.</small></p>%s"
            "  <ol class='draft'>%s%s  </ol>%s</div>%s"
            % (NL, NL, NL, NL, draft, NL, NL)
            + ("<div class='card'>%s  <h3>References</h3>%s  <ol>%s%s  </ol>%s%s"
               "</div>%s" % (NL, NL, NL, refs, NL, ratio, NL) if refs else "")
            + "<div class='card'>%s  <h3>Your draft</h3>%s"
              "  <p><small>Stored in this browser only. The buttons paste figures "
              "projected at build time &mdash; the same strings shown elsewhere on "
              "the page.</small></p>%s  <div class='chips'>%s%s  </div>%s"
              "  <textarea id='draft' rows='14' placeholder='Write your synthesis "
              "here.'></textarea>%s</div>%s"
              % (NL, NL, NL, NL, chips, NL, NL, NL))


def statistics_tables(res, p):
    pan = res.get("panels") or {}
    cp = res.get("count_panels") or {}
    out, rows = "", ""
    pr = pan.get("prediction")
    if pr:
        rows += ("    <tr><th>Prediction interval</th><td class='num'>%s to %s</td>"
                 "<td><small>%s</small></td></tr>%s"
                 % (pj.fmt(pr["pi_low"]), pj.fmt(pr["pi_high"]),
                    p(pr.get("convention", "")), NL))
    tc = pan.get("tau2_ci")
    if tc:
        rows += ("    <tr><th>Between-study variance</th><td class='num'>%s (%s to "
                 "%s)</td><td><small>%s</small></td></tr>%s"
                 % (pj.fmt(tc["estimate"]), pj.fmt(tc["ci_low"]),
                    pj.fmt(tc["ci_high"]), p(tc.get("method", "")), NL))
    eg = pan.get("egger")
    if eg and eg.get("estimable"):
        rows += ("    <tr><th>Egger's regression</th><td class='num'>intercept %s, "
                 "p = %s</td><td><small>%s</small></td></tr>%s"
                 % (pj.fmt(eg["intercept"]), pj.fmt(eg["p"]),
                    p(eg.get("caution", "")), NL))
    by = pan.get("bayes")
    if by:
        rows += ("    <tr><th>Bayesian posterior</th><td class='num'>%s (%s to %s)"
                 "</td><td><small>%s</small></td></tr>%s"
                 % (pj.fmt(by["posterior_median"]), pj.fmt(by["cri_low"]),
                    pj.fmt(by["cri_high"]), p(by.get("method", "")), NL))
    pt = cp.get("peters")
    if pt and pt.get("estimable"):
        rows += ("    <tr><th>Peters' test</th><td class='num'>intercept %s, p = %s"
                 "</td><td><small>%s</small></td></tr>%s"
                 % (pj.fmt(pt["intercept"]), pj.fmt(pt["p"]),
                    p(pt.get("note", "")), NL))
    if rows:
        out += ("<div class='card'>%s  <h3>Diagnostics</h3>%s  <table>%s"
                "    <tr><th>Statistic</th><th>Value</th><th>Method and caution</th>"
                "</tr>%s%s  </table>%s</div>%s" % (NL, NL, NL, NL, rows, NL, NL))
    inf = pan.get("influence")
    if inf:
        r2 = "".join("    <tr><th>%s</th><td class='num'>%s%%</td>"
                     "<td class='num'>%s</td><td class='num'>%s</td>"
                     "<td class='num'>%s</td></tr>%s"
                     % (p(str(x["trial"])), pj.fmt(x["weight"]), pj.fmt(x["hat"]),
                        pj.fmt(x["cook_d"]), pj.fmt(x["rstudent"]), NL)
                     for x in inf)
        out += ("<div class='card'>%s  <h3>Per-trial influence and weight</h3>%s"
                "  <table>%s    <tr><th>Trial</th><th>Weight</th><th>Leverage</th>"
                "<th>Cook's D</th><th>Std. residual</th></tr>%s%s  </table>%s"
                "  <p><small>Read the weight column beside the leave-one-out rows: "
                "a trial carrying most of the weight is the trial the answer rests "
                "on.</small></p>%s</div>%s" % (NL, NL, NL, NL, r2, NL, NL, NL))
    lo = pan.get("leave_one_out")
    if lo:
        r3 = "".join("    <tr><th>%s</th><td class='num'>%s (%s to %s)</td>"
                     "<td class='num'>%s%%</td></tr>%s"
                     % (p(str(x["omitted"])), pj.fmt(x["point"]),
                        pj.fmt(x["ci_low"]), pj.fmt(x["ci_high"]),
                        pj.fmt(x["I2"]), NL) for x in lo)
        out += ("<div class='card'>%s  <h3>Leave-one-out, numerically</h3>%s"
                "  <table>%s    <tr><th>Omitted</th><th>Pooled</th>"
                "<th>I-squared</th></tr>%s%s  </table>%s</div>%s"
                % (NL, NL, NL, NL, r3, NL, NL))
    if pan.get("_provenance"):
        out += ("<div class='card'>%s  <h3>Where these numbers came from</h3>%s"
                "  <p>%s</p>%s</div>%s" % (NL, NL, p(pan["_provenance"]), NL, NL))
    return out


def count_tables(res, p):
    cp = res.get("count_panels")
    if not cp:
        return ""
    out, rows = "", ""
    for key, lab in (("rr", "Risk ratio"), ("or", "Odds ratio"),
                     ("rd", "Risk difference")):
        b = cp.get(key)
        if b:
            rows += ("    <tr><th>%s</th><td class='num'>%s (%s to %s)</td>"
                     "<td class='num'>%s%%</td></tr>%s"
                     % (lab, pj.fmt(b["point"]), pj.fmt(b["ci_low"]),
                        pj.fmt(b["ci_high"]), pj.fmt(b["I2"]), NL))
    if rows:
        out += ("<div class='card'>%s  <h3>The same 2x2, on three scales</h3>%s"
                "  <table>%s    <tr><th>Measure</th><th>Pooled</th>"
                "<th>I-squared</th></tr>%s%s  </table>%s"
                "  <p><small>None of these three is this review's primary result "
                "&mdash; that remains the pooled hazard ratio, which uses time to "
                "first event rather than counting people once. An odds ratio is "
                "not collapsible, which is why Handbook 10.4.2 asks for both when "
                "baseline risks differ.</small></p>%s</div>%s"
                % (NL, NL, NL, NL, rows, NL, NL, NL))
    n = cp.get("nnt")
    if n:
        body = ("  <p><strong>Not defined.</strong> %s</p>%s"
                % (p(n.get("undefined_because", "")), NL) if n.get("nnt") is None
                else "  <p><strong>%s</strong> (%s to %s)</p>%s"
                     "  <p><small>From the pooled risk difference %s (%s to %s), "
                     "never from a ratio.</small></p>%s"
                     % (pj.fmt(n["nnt"]), pj.fmt(n["nnt_high"]),
                        pj.fmt(n["nnt_low"]), NL, pj.fmt(n["pooled_rd"]),
                        pj.fmt(n["rd_ci_low"]), pj.fmt(n["rd_ci_high"]), NL))
        out += ("<div class='card'>%s  <h3>Number needed to treat</h3>%s%s</div>%s"
                % (NL, NL, body, NL))
    br = cp.get("baseline_risk")
    if br:
        r = "".join("    <tr><th>%s</th><td class='num'>%s / %s</td>"
                    "<td class='num'>%s</td></tr>%s"
                    % (p(str(x["trial"])), pj.fmt(x["control_events"]),
                       pj.fmt(x["control_n"]), pj.fmt(x["control_risk"]), NL)
                    for x in br)
        out += ("<div class='card'>%s  <h3>Baseline risk, per trial</h3>%s"
                "  <table>%s    <tr><th>Trial</th><th>Control events / analysed</th>"
                "<th>Risk</th></tr>%s%s  </table>%s</div>%s"
                % (NL, NL, NL, NL, r, NL, NL))
    bf = cp.get("benford")
    if bf:
        obs, exp = bf["observed"], bf["expected"]
        r = "".join("    <tr><th>%s</th><td class='num'>%s</td>"
                    "<td class='num'>%s</td></tr>%s"
                    % (pj.fmt(i + 1), pj.fmt(obs[i]), pj.fmt(exp[i]), NL)
                    for i in range(9))
        out += ("<div class='card'>%s  <h3>Benford first-digit screen</h3>%s"
                "  <table>%s    <tr><th>Leading digit</th><th>Observed</th>"
                "<th>Expected</th></tr>%s%s  </table>%s  <p><small>%s</small></p>%s"
                "</div>%s" % (NL, NL, NL, NL, r, NL, p(bf.get("note", "")), NL, NL))
    if cp.get("_provenance"):
        out += ("<div class='card warn'>%s  <h3>What these counts are, and are not"
                "</h3>%s  <p>%s</p>%s</div>%s"
                % (NL, NL, p(cp["_provenance"]), NL, NL))
    return out


def cross_engine_card(res, p):
    ce = res.get("cross_engine") or {}
    cmp_ = ce.get("comparison")
    if not cmp_:
        return ""
    rows = "".join("    <tr><th>%s</th><td class='num'>%s</td>"
                   "<td class='num'>%s</td><td><small>%s</small></td></tr>%s"
                   % (p(r["quantity"]), pj.fmt(r["this_object"]),
                      pj.fmt(r["metafor"]), p(r["agree"]), NL)
                   for r in cmp_["rows"])
    return ("<div class='card'>%s  <h3>Cross-engine check against R</h3>%s"
            "  <p><strong>%s</strong>, estimator %s. %s</p>%s  <table>%s"
            "    <tr><th>Quantity</th><th>This object</th><th>metafor</th>"
            "<th>Agreement</th></tr>%s%s  </table>%s  <p><small>%s</small></p>%s"
            "</div>%s"
            % (NL, NL, p(cmp_["engine"]), p(cmp_["estimator"]), p(cmp_["computed"]),
               NL, NL, NL, rows, NL, p(ce.get("i2_definitions_differ", "")), NL, NL))


def panels_card(res, p):
    panels = res.get("analysis_panels") or []
    if not panels:
        return ""
    rows = "".join("    <tr><th>%s</th><td>%s</td><td><small>%s</small></td></tr>%s"
                   % (p(x["panel"]), p(x["status"]), p(x.get("detail", "")), NL)
                   for x in panels)
    return ("<div class='card'>%s  <h3>Further analyses &mdash; what was run, and "
            "what was not</h3>%s  <table>%s    <tr><th>Analysis</th><th>Status</th>"
            "<th>Why</th></tr>%s%s  </table>%s</div>%s"
            % (NL, NL, NL, NL, rows, NL, NL))


def output_card(canon, p):
    sof = ""
    for oid, r in canon["results"]["by_outcome"].items():
        o = next(x for x in canon["outcomes"] if x["id"] == oid)
        pl = r.get("pooled") or {}
        g = r.get("grade") or {}
        ks = r.get("k_status") or {}
        sof += ("    <tr><td>%s</td><td class='num'>%s%s</td><td class='num'>%s</td>"
                "<td>%s</td></tr>%s"
                % (p(o["name"]), pj.fmt(r.get("k")),
                   " (lower bound)" if ks.get("is_lower_bound") else "",
                   ("%s %s (%s to %s)" % (_v((pl.get("measure", ""))),
                                          pj.fmt(pl["point"]),
                                          pj.fmt(pl["ci_low"]),
                                          pj.fmt(pl["ci_high"]))
                    if pl.get("point") else "not pooled"),
                   p(g["certainty"]) if g.get("certainty") else "&mdash;", NL))
    reg = canon.get("registration") or {}
    c0 = (reg.get("commits") or [{}])[0]
    first = next(iter(canon["results"]["by_outcome"].values()), {})
    repro = pj.kv_card("Reproducibility artifact", [
        ("Canonical object", "<code>%s</code>" % _v((reg.get("path", "")))),
        ("Registered at", "<code>%s</code> %s" % (_v(c0.get("sha", ""), limit=12),
                                                  _v((c0.get("committed_utc", ""))))),
        ("Permalink", ("<a href='%s'>%s</a>" % (e(c0["permalink"]), e(c0["permalink"])))
         if c0.get("permalink") else ""),
        ("Schema", _v((canon.get("schema_version", "")))),
        ("Built", _v((canon.get("built", "")))),
        # BUILD STAMP. The generator commit this page was produced from, in the
        # served bytes.
        #
        # ARNI, the flagship, served a build that predated the extraction
        # provenance table while its object carried more source quotes than any
        # neighbouring page. Nothing detected it, because "fixed in the generator"
        # and "fixed on the site" are different claims and no artefact recorded
        # which build a page came from. Recovering that from git ancestry is
        # archaeology: it needs the file still traceable in history, it fails for
        # anything built out-of-tree, and on this repo it could judge only 25 of
        # 554 linked pages -- the rest were last touched on merged branches and
        # fell outside the first-parent line entirely.
        #
        # Stamped, the question is answered by inspection and forever: compare
        # this string with the generator head. It is shown to READERS rather than
        # hidden in a comment, because which build produced what you are reading
        # belongs beside the R output and the source links.
        # THE STANDARD VERSION BELONGS IN THE STAMP, NOT ONLY THE COMMIT.
        # "Built to v1" is what makes a page at v1 under a v3 standard HONESTLY
        # LABELLED rather than silently stale, and it is what turns "bring
        # cardiology to standard" into a countable backlog instead of a feeling.
        # The commit cannot say it on its own: the bar is written down in a
        # different file from the generator, so two pages built by the same
        # commit can be built against two different versions of it.
        ("Generator build", "<code>%s</code>%s, built to STANDARD v%s"
                            % (e(_generator_stamp()[0]), e(_generator_stamp()[1]),
                               _v((_standard_version())))),
        ("Statistical engine", p((first.get("cross_engine") or {}).get("engine", ""))),
    ], "Everything a third party needs to rebuild this page. Each figure on the "
       "Analysis tab downloads as an SVG carrying exactly the values shown.")
    return ("<div class='card'>%s  <h3>Summary of findings</h3>%s  <table>%s"
            "    <tr><th>Outcome</th><th>k</th><th>Pooled effect</th>"
            "<th>Certainty</th></tr>%s%s  </table>%s</div>%s"
            % (NL, NL, NL, NL, sof, NL, NL)) + repro


# WHERE THE DOCUMENT MODEL AND THE .docx COME FROM.
# This was a bare absolute path into ONE interactive session's scratch directory.
# That session has since ended. The path still resolves today, so nothing failed
# and nothing warned -- but the flagship page's document view and both of its
# Word downloads were reading out of a temp folder nobody owns, which is one
# cleanup away from silently emitting a page with no manuscript and no downloads
# (render() returns "" when the model is absent, and the download rows degrade to
# "not built at page-build time"). Both failures are quiet.
# Overridable now, with the old location kept as the fallback so the current
# build is unchanged; set ARNI_DOC_DIR to move it somewhere owned.
# _SCRATCH / _DOCMODEL DELETED 2026-08-16. They were a single hardcoded path
# outside the repo, and every tabbed build rendered whatever manuscript sat there
# regardless of which object it was building. See _doc_dir_for(). The path is not
# kept as a fallback on purpose: a fallback is what caused the incident, and the
# environment override made it worse by making the source of the manuscript
# invisible in the build output. ARNI's manuscript now lives in ssot/arni-hfref/
# alongside the object it belongs to, like every other artefact of that review.



_STAMP_CACHE = None


def _standard_version():
    """The version of THE STANDARD this build was made against.

    Read from scripts/standard_manifest.py, never typed here: a version constant
    copied into the generator is a second source of truth for the one fact whose
    whole purpose is to be authoritative, and it would drift silently the moment
    the standard incremented. UNKNOWN rather than a guess if it cannot be read --
    a page claiming a bar it cannot name is worse than one that admits it.
    """
    try:
        import importlib.util
        p = os.path.join(os.path.dirname(HERE), "scripts", "standard_manifest.py")
        spec = importlib.util.spec_from_file_location("_standard_manifest", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.STANDARD_VERSION
    # NARROWED. "UNKNOWN" is printed on the page, so a bug here becomes a published
    # statement about the standard this build claims to meet. Absent or unreadable
    # manifest is expected and still yields UNKNOWN honestly; anything else is ours.
    except (OSError, ImportError, AttributeError):
        return "UNKNOWN"


def _generator_stamp():
    """(short sha, suffix) of the commit that last changed any generator file.

    Read once per build. The suffix says DIRTY when a generator file is modified
    but uncommitted, because a page built from uncommitted code cannot be
    reproduced from the stamp alone -- and a stamp that quietly implies it can is
    worse than none. UNKNOWN when git is unavailable, never a guess.
    """
    global _STAMP_CACHE
    if _STAMP_CACHE is not None:
        return _STAMP_CACHE
    import subprocess
    gen = ["ssot/projectors.py", "ssot/projectors2.py", "ssot/build_tabbed.py",
           "ssot/build_app_v2.py", "ssot/wysiwyg.py", "ssot/paper.py"]
    root = os.path.dirname(HERE)
    try:
        sha = subprocess.run(["git", "-C", root, "log", "-1", "--format=%h", "--", *gen],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "--", *gen],
                               capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        sha, dirty = "", ""
    if not sha:
        _STAMP_CACHE = ("UNKNOWN", " -- git unavailable at build time")
    else:
        _STAMP_CACHE = (sha, " (uncommitted generator changes -- NOT REPRODUCIBLE "
                             "from this stamp alone)" if dirty else "")
    return _STAMP_CACHE


def _doc_dir_for(canon):
    """Where THIS object's manuscript lives, or None.

    THE BUG THIS REPLACES (2026-08-16). _DOCMODEL was a single hardcoded path and
    every tabbed build rendered whatever manuscript happened to sit there. That
    file was ARNI's, so sotagliflozin, SGLT2, IV iron and alirocumab each went
    live carrying ARNI's manuscript -- 239,773 characters of another review,
    including its Table 4 with PARADIGM-HF's 558/4187. The counts were
    byte-identical across four unrelated drugs because it was literally the same
    file. Nothing in the build was per-object at all.

    A manuscript belongs to ONE object. It is looked up under that object's own
    directory, and if it is not there the page says so. There is deliberately NO
    FALLBACK: a silent fallback to another page's manuscript is precisely what
    produced the contamination, and a fallback that is "usually right" is the
    worst kind, because it fails invisibly on exactly the pages nobody checks.
    """
    app = (canon.get("app_id") or "").strip()
    if not app:
        return None
    d = os.path.join(HERE, app)
    return d if os.path.isdir(d) else None


def _downloads_html(canon):
    """The manuscript and the supplement, as real files a reader can save.

    A submission needs the supplement as much as the paper, and a reader who can
    only read it on screen cannot submit it. Both are embedded as data URIs so
    the page stays a single self-contained file, and each states its own byte
    size so a truncated embed is visible rather than silently short.

    Filenames are derived from the object's own app_id. They were hardcoded to
    ARNI_manuscript.docx and ARNI_supplement.docx, so every rebuilt page offered
    ARNI's Word documents as its own downloads.
    """
    import base64 as _b64
    d = _doc_dir_for(canon)
    app = (canon.get("app_id") or "unknown")
    if not d:
        return ("  <p><strong>Downloads</strong></p>%s"
                "  <div class='absent-state' role='note'><strong>Not held in this "
                "object.</strong> No manuscript or supplement is built for %s, so "
                "none is offered. Nothing from another review is substituted."
                "</div>%s" % (NL, e(app), NL))
    rows = ""
    for fn, label in (("%s_manuscript.docx" % app, "Manuscript (Word, .docx)"),
                      ("%s_supplement.docx" % app, "Supplementary material (Word, .docx)")):
        fp = os.path.join(d, fn)
        if not os.path.exists(fp):
            rows += ("    <li><small>%s &mdash; not built at page-build time, so "
                     "not offered. Stated rather than shown as a dead "
                     "link.</small></li>%s" % (e(label), NL))
            continue
        b = open(fp, "rb").read()
        uri = ("data:application/vnd.openxmlformats-officedocument"
               ".wordprocessingml.document;base64," + _b64.b64encode(b).decode())
        rows += ("    <li><a class='dl' download='%s' href=\"%s\">&#11015; %s</a> "
                 "<small>%s KB</small></li>%s"
                 % (e(fn), uri, e(label), "{:,}".format(max(1, len(b) // 1024)), NL))
    return ("  <p><strong>Downloads</strong></p>%s  <ul>%s%s  </ul>%s"
            % (NL, NL, rows, NL))


def _projected_paper_html(canon):
    """The manuscript PROJECTED FROM THIS OBJECT, with every section's source field on it.

    PREFERRED OVER THE DOCMODEL FILE, and the reason is the contamination incident this
    module's own docstring records: a manuscript read from a FIXED PATH belongs to whoever
    wrote that path. A manuscript projected from `canon` cannot be another review's, because
    it is derived from this review's fields and carries their names.

    Returns "" when the object supports no section, so the caller falls through to the
    absent-state banner rather than printing an empty manuscript.
    """
    try:
        import paper_projector as ppj
        secs = ppj.project(canon)
    except Exception as exc:                       # noqa: BLE001 - reported, never silent
        return ("<div class='absent-state' role='note'><strong>Not assessable.</strong> "
                "The manuscript projector failed on this object (%s: %s). That is a broken "
                "instrument, and it is reported rather than shown as an absent "
                "manuscript.</div>" % (e(type(exc).__name__), _v(exc, limit=200)))
    if not any(s.state == ppj.WRITTEN for s in secs):
        return ""
    out = ["<div class='card'>", "<h2>Paper</h2>",
           "<p class='muted'>Every paragraph below is PROJECTED from a field of this "
           "object, and names it. <strong>A section with no field behind it is not "
           "written</strong> &mdash; it is refused, by name, so a reader can tell an absent "
           "procedure from an unmentioned one.</p>"]
    for s in secs:
        out.append("<h3>%s</h3>" % e(s.heading))
        for text, fields in s.paras:
            out.append("<p>%s<br><small class='muted'>&larr; %s</small></p>"
                       % (e(text), e(", ".join(fields))))
        # A PROJECTED TABLE. Every cell is escaped -- the cells are object values, and an
        # object value containing markup must render as text and never as markup. The
        # caption carries the same field trace a paragraph does, because a table asserts
        # as much as a sentence and is read with more trust.
        for caption, headers, rows, fields in getattr(s, "tables", []):
            out.append("<table><caption>%s<br><small class='muted'>&larr; %s</small>"
                       "</caption>" % (e(caption), e(", ".join(fields))))
            out.append("<tr>%s</tr>" % "".join("<th>%s</th>" % e(h) for h in headers))
            for row in rows:
                out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % e(c) for c in row))
            out.append("</table>")
        for what, missing in s.refusals:
            out.append("<div class='absent-state' role='note'><strong>Refused:</strong> %s "
                       "&mdash; no field: <code>%s</code></div>"
                       % (e(what), e(", ".join(missing))))
    out.append("</div>")
    return NL.join(out)


def _paper_panel(canon):
    """The Paper Studio tab, from THIS object's manuscript or an honest state.

    A page with no manuscript of its own says so, loudly, in the same red-banner
    style the absent-state panels use. It does NOT borrow one. The whole
    contamination incident was a silent fallback: the build found a manuscript at
    a fixed path, rendered it, and every check passed because a manuscript was
    present -- just not this page's.
    """
    projected = _projected_paper_html(canon)
    if projected:
        return projected
    d = _doc_dir_for(canon)
    app = (canon.get("app_id") or "unknown")
    model = os.path.join(d, "manuscript_docmodel.json") if d else None
    if not model or not os.path.exists(model):
        return ("<div class='card'>%s  <h2>Paper Studio</h2>%s"
                "  <div class='absent-state' role='note'><strong>Not held in this "
                "object.</strong> No manuscript has been generated for %s. A "
                "manuscript belongs to one review, so none from another review is "
                "shown here &mdash; this tab is empty of content rather than "
                "filled with someone else&rsquo;s.</div>%s</div>%s"
                % (NL, NL, e(app), NL, NL))
    return wy.render(model, _downloads_html(canon))


def _caption_tables(html):
    """Give every table a <caption>, taken from the heading it sits under.

    "Numbered, captioned figures and tables" is one of the things an editor reads
    for, and 0 of 31 tables carried a caption. The text is NOT invented: it is the
    nearest preceding heading in the same card, which is the label the table was
    already filed under -- so the caption cannot describe something the page does
    not say. Tables that already have one are left alone.
    """
    import re as _re
    out, pos, n = [], 0, [0]

    def head_before(i):
        # THIRD INSTANCE OF ONE CLASS, 2026-08-18. Stripping tags from generated
        # markup does NOT yield plain text. Here the heading still contains an
        # entity the projector emitted deliberately -- "Further analyses &mdash;
        # what was run, and what was not" -- and the caller escapes what it is
        # handed, so the reader sees the literal characters "&mdash;" in the
        # table caption.
        #
        # The other two found today: _anchor_headings feeding the jump list, and
        # an em-dash fallback passed inside e() in projectors2. THE CLASS: text
        # extracted from generated markup is not plain text, and treating it as
        # plain text at an escaping boundary goes wrong in one direction or the
        # other every time. Unescape at extraction, so the value is plain text
        # from here outward and is escaped exactly once, at render.
        import html as _htmlmod
        h = None
        for m in _re.finditer(r"<h[234][^>]*>(.*?)</h[234]>", html[:i], _re.S):
            h = m.group(1)
        return _htmlmod.unescape(_re.sub(r"<[^>]+>", "", h)).strip() if h else None

    for m in _re.finditer(r"<table(?![^>]*caption)[^>]*>", html):
        seg = html[m.end():m.end() + 200]
        if "<caption" in seg:
            continue
        t = head_before(m.start())
        if not t:
            continue
        n[0] += 1
        out.append((m.end(), "%s    <caption>Table %d. %s</caption>%s"
                    % (NL, n[0], e(t), NL)))
    for at, ins in reversed(out):
        html = html[:at] + ins + html[at:]
    # Every table gets a scrolling WRAPPER. If a table still exceeds the measure
    # after wrapping -- a genuinely wide one -- it scrolls inside its own box and
    # the page does not. Nothing is hidden or truncated: the container clips
    # nothing, it only scrolls.
    html = _re.sub("(<table[ >])", lambda mm: "<div class='tscroll'>" + mm.group(1), html)
    html = _re.sub("(</table>)", lambda mm: mm.group(1) + "</div>", html)
    return html


def _standard_block(canon, e_):
    """Render the page-standard properties. A page with no stamp SAYS SO rather than omitting.

    Every branch here emits something. An unstamped page renders "unknown-version", which is
    what `arni-hfref` currently is -- unstamped is not the same as compliant, and the corpus
    is not allowed to look compliant by virtue of a missing field.
    """
    stamp = canon.get("build_stamp")
    if not stamp:
        return ("<div class='card warn'><h2>Page standard</h2><p><strong>UNSTAMPED — "
                "unknown-version.</strong> This page carries no <code>build_stamp</code>, so "
                "the standard it was built to cannot be established. That is a statement "
                "about the record, not a claim that the page is below standard.</p></div>")

    rows = []
    for name, prop in (stamp.get("properties") or {}).items():
        cls = "ok" if prop.get("state") == "HELD" else "warn"
        rows.append("<tr class='%s'><td>%s</td><td><strong>%s</strong></td><td>%s</td></tr>"
                    % (cls, e_(name), _v((prop.get("state"))), _v((prop.get("reason")))))

    casc = canon.get("k_cascade") or {}
    casc_rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (e_(k), _v((v)))
                        for k, v in casc.items() if not k.startswith("_"))

    prov = (canon.get("screening") or {}).get("eligibility_provenance") or {}
    prov_html = ""
    if prov:
        prov_html = (
            "<h3>Inclusion criteria — derived, post hoc</h3>"
            "<p><strong>predefined: %s &nbsp;|&nbsp; post_hoc: %s</strong> — derived %s</p>"
            "<p><small>%s</small></p>"
            % (_v((prov.get("predefined"))), _v((prov.get("post_hoc"))),
               _v((prov.get("derived_on"))),
               _v((prov.get("authority_permitting_this", "")))))
        prov_html += "<table><tr><th>limb</th><th>value</th><th>derived from</th></tr>"
        for el in prov.get("elements") or []:
            prov_html += ("<tr><td>%s</td><td>%s</td><td><code>%s</code></td></tr>"
                          % (_v(el.get("limb")), _v(el.get("value"), limit=160),
                             _v(el.get("derived_from"))))
        prov_html += "</table>"

    pv = canon.get("precondition_verdict") or {}
    pre_rows = "".join(
        "<tr><td>%s</td><td><strong>%s</strong></td><td><small>%s</small></td>"
        "<td><small>%s</small></td></tr>"
        % (e_(n), _v(v.get("verdict")), _v(v.get("reason"), limit=220),
           _v(v.get("authority"), limit=200))
        for n, v in (pv.get("verdicts") or {}).items())

    # P6 and P7 detail. The property TABLE already carries each refusal and its reason; these
    # blocks carry the evidence underneath it. A first served-bytes check found the reasons
    # present and the evidence absent, which is a page that says it refuses without showing
    # what it refused on.
    # EVERY pool that carries output, not just the first outcome. Taking the first meant
    # sglt2-hf rendered nothing: its first outcome is the WITHDRAWN pool, which correctly has
    # no r_output, while the two pools that DO carry verbatim metafor output sit behind it.
    _by = ((canon.get("results") or {}).get("by_outcome") or {})
    ro_html = ""
    for _oid, _res in _by.items():
        ro = (_res or {}).get("r_output") or {}
        if not ro:
            continue
        if ro.get("verbatim"):
            ro_html += ("<h3>Analysis output — %s (quoted verbatim)</h3>"
                        "<p><small>%s &nbsp;|&nbsp; call: <code>%s</code></small></p>"
                        "<pre style='overflow-x:auto'>%s</pre>"
                        % (_v((_oid)), _v((ro.get("_environment", ""))),
                           _v((ro.get("call", ""))), _v((ro.get("verbatim")))))
            if ro.get("reproduces_the_stored_value"):
                ro_html += "<p><small>%s</small></p>" % _v((ro["reproduces_the_stored_value"]))
            continue
    ro = (next(iter(_by.values()), {}) or {}).get("r_output") or {}
    if ro and not ro_html:
        stands = ro.get("what_stands_instead") or {}
        ro_html = ("<h3>Analysis output — %s</h3><p>%s</p>"
                   "<p><strong>What stands instead:</strong> %s<br>"
                   "<small>Provenance: %s</small><br>"
                   "<code>%s</code></p>"
                   "<p><small>Heterogeneity: %s<br>What would change it: %s</small></p>"
                   % (_v((ro.get("state"))), _v((ro.get("_why_absent"))),
                      _v((stands.get("estimate", ""))),
                      _v((stands.get("provenance", ""))),
                      _v((stands.get("verbatim_from_registry", ""))),
                      _v((ro.get("heterogeneity_reason", ""))),
                      _v((ro.get("what_would_change_it", "")))))

    pc = canon.get("published_comparison") or {}
    pc_html = ""
    if isinstance(pc, dict) and pc.get("state"):
        pc_html = ("<h3>Published-meta comparison — %s</h3>"
                   "<p><strong>Denominator: %s.</strong> %s</p>"
                   "<p><small><strong>Explicitly not done:</strong> %s</small></p>"
                   "<p><small>Blocked on: %s</small></p>"
                   % (_v((pc.get("state"))), _v((pc.get("denominator"))),
                      _v((pc.get("denominator_reason", ""))),
                      _v((pc.get("explicitly_not_done", ""))),
                      _v((pc.get("blocked_on", "")))))

    # The screen of the unscreened remainder. Sixteen verdicts each keyed to a registration
    # id, and the withholding question shown as asked rather than asserted as asked.
    # The withholding question is rendered wherever it is recorded -- as a per-trial block on
    # a screened topic, or as a top-level record on a topic where it decided the pools.
    wq_top = canon.get("withholding_question") or {}
    wq_html = ""
    if wq_top:
        rows_wq = "".join(
            "<tr><td><code>%s</code></td><td>%s</td><td><small>%s</small></td>"
            "<td><small>%s</small></td></tr>"
            % (_v((k)), _v((v.get("name", ""))), _v((v.get("two_component", ""))),
               _v((v.get("three_component", ""))))
            for k, v in (wq_top.get("per_trial") or {}).items())
        md = wq_top.get("matcher_defect_found_and_not_relied_on") or {}
        # THE ANSWER WAS IN THE OBJECT AND ON NO PAGE. Until 2026-08-19 this rendered the
        # QUESTION and the per-trial table and nothing else, so a topic could record that it
        # asked, what it found, and which way the finding cut -- and a reader saw only that it
        # had asked. The reverse of the sglt2-hf shape, where the withdrawal was on the page
        # and the live number was still in the object: same class, opposite direction.
        answer = wq_top.get("answer", "")
        bought = (wq_top.get("what_asking_it_bought_and_what_it_did_not")
                  or wq_top.get("what_asking_it_bought") or "")
        wq_html = ("<h3>The withholding question, asked at every rank</h3>"
                   "<p><em>%s</em></p>"
                   % (_v((wq_top.get("question", "")))))
        if answer:
            wq_html += "<p><strong>%s</strong></p>" % _v((answer))
        if bought:
            wq_html += "<p>%s</p>" % _v((bought))
        wq_html += ("<p><small>%s</small></p>"
                    "<table><tr><th>registration</th><th>trial</th><th>two-component</th>"
                    "<th>three-component</th></tr>%s</table>"
                    % (_v((wq_top.get("why_before_deciding", ""))), rows_wq))

        # THE DIRECTION PAIR. A review that reports only its own recoveries invites exactly
        # one reading -- that we ask until we get the answer we want. The refutation is that
        # the same question, on the same discipline, on the same drug, on the same night, moved
        # one review's poolable set UP and the other's DOWN. Neither instance is publishable
        # without the other, so the projector renders both or the object is asked to say why.
        dp = wq_top.get("direction") or {}
        if dp:
            ci = dp.get("counter_instance") or {}
            wq_html += (
                "<div class='card warn'><h4>The same question, the opposite answer</h4>"
                "<table><tr><th>review</th><th>poolable set</th><th>direction</th></tr>"
                "<tr><td>%s</td><td><strong>%s</strong></td><td>%s</td></tr>"
                "<tr><td>%s</td><td><strong>%s</strong></td><td>%s</td></tr></table>"
                "<p>%s</p><p><small>%s</small></p></div>"
                % (_v((dp.get("topic", ""))), _v((dp.get("moved", ""))),
                   _v((dp.get("direction", ""))),
                   _v((ci.get("topic", ""))), _v((ci.get("moved", ""))),
                   _v((ci.get("direction", ""))),
                   _v((dp.get("why_both_are_stated_together", ""))),
                   _v((dp.get("what_it_does_not_establish", "")))))
        if md:
            wq_html += ("<div class='card warn'><h4>A matcher defect, found and not relied on"
                        "</h4><p>%s</p><p><small>%s</small></p><p><small>Class: %s</small></p>"
                        "</div>" % (_v((md.get("what_happened", ""))),
                                    _v((md.get("why_it_mattered", ""))),
                                    _v((md.get("class", "")))))

    sc = canon.get("screening_of_remainder") or {}
    sc_html = wq_html
    if sc:
        res = sc.get("result") or {}
        wq = sc.get("withholding_question") or {}
        limb_rows = "".join(
            "<tr><td>%s</td><td>%s</td><td><small>%s</small></td></tr>"
            % (_v((k)), _v((v.get("n"))), e_(", ".join(v.get("ncts") or [])))
            for k, v in (sc.get("exclusions_by_failing_limb") or {}).items())
        mace_rows = "".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (_v((h.get("nct"))), _v((hit.get("rank"))), _v((hit.get("measure"))))
            for h in (wq.get("trials_with_a_mace_matching_outcome_at_some_rank") or [])
            for hit in (h.get("hits") or []))
        trial_rows = "".join(
            "<tr><td><code>%s</code></td><td><strong>%s</strong></td><td>%s</td>"
            "<td><small>%s</small></td></tr>"
            % (_v(r.get("nct")), _v(r.get("verdict")),
               _v(r.get("failing_limb") or ""), _v(r.get("reason"), limit=260))
            for r in (sc.get("rows") or []))
        sc_html += (
            "<h3>Screening of the remainder — %s screened, %s included, %s excluded, "
            "%s not-assessable</h3>"
            "<p>%s</p><p><strong>k after screening: %s.</strong> %s</p>"
            "<table><tr><th>failing limb</th><th>n</th><th>registrations</th></tr>%s</table>"
            "<h4>The withholding question, asked at every rank</h4><p><em>%s</em></p>"
            "<p><small>%s</small></p>"
            "<table><tr><th>registration</th><th>rank</th><th>matching outcome</th></tr>%s</table>"
            "<h4>Every trial, with its reason</h4>"
            "<table><tr><th>registration</th><th>verdict</th><th>limb</th><th>reason</th></tr>"
            "%s</table>"
            % (_v((sc.get("n_screened"))), _v((res.get("include"))),
               _v((res.get("exclude"))), _v((res.get("not_assessable"))),
               _v((sc.get("screened_against", ""))),
               _v((sc.get("k_after_screening"))),
               _v((sc.get("k_unchanged_because", ""))),
               limb_rows, _v((wq.get("asked", ""))),
               _v((wq.get("why_asked_before_deciding_not_to_pool", ""))),
               mace_rows, trial_rows))
        # A correction to a recorded exclusion reason belongs on the page, not only in the
        # object: the page previously carried the wrong reason.
        for st in ((canon.get("eligible_but_not_contributing") or {}).get("studies") or []):
            corr = st.get("why_not_contributing_CORRECTED_2026_08_19")
            if corr:
                sc_html += ("<div class='card warn'><h4>Correction — %s</h4>"
                            "<p>%s</p><p><small>How it happened: %s</small></p>"
                            "<p><small>Verdict: %s</small></p>"
                            "<p><small>Class: %s</small></p></div>"
                            % (_v((st.get("id"))),
                               _v((corr.get("the_recorded_reason_was_wrong", ""))),
                               _v((corr.get("how_the_error_happened", ""))),
                               _v((corr.get("the_verdict_still_stands_but_on_a_different_limb", ""))),
                               _v((corr.get("class", "")))))

    auth = pv.get("authority") or {}
    return (
        "<div class='card'><h2>Page standard %s</h2>"
        "<p>Built %s by <code>%s</code> against <code>%s</code>. "
        "<strong>%d held, %d refusing.</strong> A refusal is a complete outcome; nothing is "
        "generated to fill a slot.</p>"
        "<table><tr><th>property</th><th>state</th><th>reason</th></tr>%s</table>"
        "<h3>k at every stage</h3><table><tr><th>stage</th><th>k</th></tr>%s</table>"
        "%s%s%s%s"
        "<h3>Preconditions</h3><p><small>Authority: %s %s, verified %s. Publishable: %s.</small></p>"
        "<table><tr><th>precondition</th><th>verdict</th><th>reason</th><th>authority</th></tr>"
        "%s</table>"
        "<p><small>%s</small></p></div>"
        % (_v((stamp.get("page_standard_version"))), _v((stamp.get("built_utc"))),
           _v((stamp.get("built_by"))), _v((stamp.get("standard_document"))),
           len(stamp.get("held") or []), len(stamp.get("refusing") or []),
           "".join(rows), casc_rows, prov_html, sc_html, ro_html, pc_html,
           _v((auth.get("handbook", ""))), _v((auth.get("version", ""))),
           _v((auth.get("verified_on", ""))), _v((pv.get("publishable"))),
           pre_rows, _v((stamp.get("_ratchet", "")))))


def build(canon):
    e_ = html.escape

    def p(s, scope=None):
        return e_(G.render(canon, s, scope))

    parts = []
    for oid in canon["results"]["by_outcome"]:
        d = G._outcome_section(canon, oid, p, e_)
        res = canon["results"]["by_outcome"][oid]
        outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
        if isinstance(d, str):          # original returns one string
            d = {"name": p(outcome["name"]), "trials": d, "headline": "",
                 "estimand": "", "hb": "", "sens": "", "dissent": "",
                 "subgroups": "", "note": ""}
        d["forest"] = pj.forest_ranged(res, outcome, e,
                                       browser=pj.RASTER.get("browser"),
                                       workdir=pj.RASTER.get("workdir"),
                                       outdir=pj.RASTER.get("outdir"))
        # The PRISMA flow and the risk-of-bias traffic light are the two figures
        # an editor looks for first and neither rendered anywhere. They project
        # from the screening corpus and the RoB-2 block, both already stored.
        # underpowered_figures() states the three that k=4 cannot support rather
        # than drawing them.
        d["figures"] = (p2.visual_abstract(canon, res, outcome, p)
                        + p2.prisma_figure(canon, p)
                        + p2.analysis_figures(res, outcome, p)
                        + p2.rob_figure(canon, p)
                        + p2.underpowered_figures(res, p))
        d["countfigs"] = p2.count_figures(res, p)
        d["grade"] = p2.grade_section(res, p)
        d["stats"] = statistics_tables(res, p)
        d["counttabs"] = count_tables(res, p)
        d["crossengine"] = cross_engine_card(res, p)
        d["panels"] = panels_card(res, p)
        parts.append(d)

    rd = pj.readiness(canon)
    first_oid = next(iter(canon["results"]["by_outcome"]))
    first_res = next(iter(canon["results"]["by_outcome"].values()))
    srcs = canon.get("sources") or {}
    sources_rows = "".join(
        "    <tr><td>%s</td><td>%s<br><small>%s</small></td>"
        "<td><small>%s</small></td></tr>%s"
        % (p(v.get("layer", "")), p(v.get("name", "")), e_(v.get("url", "")),
           p(v.get("access_note", "")), NL)
        for v in sorted(srcs.values(), key=lambda x: x.get("layer_rank", 99)))
    stmt = canon.get("completeness_statement", "")

    page = {
        "protocol": p2.protocol_card(canon, p),
        "registration": p2.registration_card(canon, p),
        "amendments": p2.amendments_card(canon, p),
        "attestation": p2.attestation_card(canon, rd, p),
        "completeness": ("<div class='card warn'>%s  <h3>What this object claims to "
                         "contain</h3>%s  <p>%s</p>%s</div>%s"
                         % (NL, NL, p(stmt), NL, NL)) if stmt else "",
        "authority": "",
        "searchcard": "",
        "searchstrings": p2.search_strings_card(canon, p),
        "screening": p2.screening_cards(canon, p),
        "corpus": p2.corpus_card(canon, p),
        # The Extraction tab is the AUDIT SURFACE: a reader must be able to see
        # every extracted value and reach its source without reading the
        # manuscript and without trusting us. This slot was empty, so the tab
        # rendered the numbers only inside prose, with no clickable link anywhere.
        "carried": pj.extraction_provenance_table(canon),
        "considered": "", "components": "",
        "rob": p2.rob2_card(canon, p),
        "switching": p2.discrepancies_card(canon, p),
        "sources_card": ("<div class='card'>%s  <h2>Sources</h2>%s  <table>%s"
                         "    <tr><th>Layer</th><th>Source</th>"
                         "<th>How it was obtained</th></tr>%s%s  </table>%s</div>%s"
                         % (NL, NL, NL, NL, sources_rows, NL, NL)),
        # The published comparison had NO RENDERER. It has been written into
        # objects since ARNI and reached a reader on no surface -- the Word file
        # got four token counts from it and the page got nothing. `recon` was an
        # empty slot sitting in the tab that should have carried it.
        "network": p2.outcomes_card(canon, p),
        "recon": p2.published_comparison_card(canon, p), "removal": "",
        "output": output_card(canon, p),
        # WYSIWYG ONLY. The panel used to render the manuscript THREE times: the
        # document view, then manuscript_section's card version, then
        # paper_studio's draft. Fifteen headings appeared twice -- two Abstracts,
        # two Results, two reference lists -- because three renderers were each
        # doing their job on the same content. The document view is the one that
        # matches the Word file block for block, so it is the one that stays.
        "paper": _paper_panel(canon),
    }
    body, tab_css = pj.tabbed_body(canon, parts, page)
    # THE STANDARD BLOCK MUST REACH SERVED BYTES, NOT JUST THE OBJECT.
    #
    # bempedoic-acid-review was built to page standard 1.0.0-2026-08-19 and the object
    # carried all ten properties. A served-bytes check then found FOUR of them absent from
    # the page: the k cascade, the criteria provenance, the precondition verdicts and the
    # build stamp itself. The build exited 0 and the object was right; the page was not.
    #
    # That is the whole reason P10 is verified in bytes rather than by an exit code. A
    # property a reader cannot see is not a property the page has.
    body += _standard_block(canon, e_)
    body = _caption_tables(body)
    return """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<style>
 :root{--bg:#fff;--fg:#111;--line:#d4d4d8;--muted:#3f3f46;
       --warnb:#b45309;--warnbg:#fffbeb;--accent:#1d4ed8;
       --paper:#fff;--paperfg:#111;--thbg:#f4f4f5;--soft:#f4f4f5}
 /* LIGHT IS THE DEFAULT, unconditionally. A prefers-color-scheme block used to
    sit here, which made the page follow the reader's operating system -- so a
    reader on a dark desktop got dark without ever asking for it. Dark is now
    strictly opt-in through the toggle, and nothing about the machine changes
    what the page opens as. */
 body:has(#dm:checked){--bg:#0f1115;--fg:#e8e8ec;--line:#33363d;--muted:#a8adb8;
       --warnb:#d99b3c;--warnbg:#241d10;--accent:#7aa2ff;
       --paper:#15181e;--paperfg:#e8e8ec;--thbg:#1c2029;--soft:#1a1e26}
 /* Measure was ~125 characters at 64rem/16px -- about double a comfortable
    line. Serif for prose, sans for tables and numbers: a reader can tell at a
    glance which register they are in, and serif digits in dense tables are
    worse than a good sans. No webfont, deliberately -- this file is opened from
    disk by people on slow connections and 200 KB of woff2 buys nothing that a
    system serif does not already give. */
 body{font-family:Charter,"Bitstream Charter","Iowan Old Style",
       "Source Serif Pro",Georgia,"Times New Roman",serif;
       max-width:46rem;margin:0 auto;padding:1.5rem 1.25rem;
       font-size:1.02rem;line-height:1.65;color:var(--fg);background:var(--bg);
       text-rendering:optimizeLegibility}
 /* DOCUMENT vs INTERFACE. All of this was system-ui while only body copy got the
    serif, so a heading and the table under it read as a different document from
    the paragraph between them. The split is now by ROLE, not by element: what a
    reader would read in the printed paper is set in the text face, and what
    belongs to the software around it stays sans. Numerals, code and the download
    chips stay sans deliberately -- tabular digits and identifiers are read glyph
    by glyph, which is the one job the sans face does better here. */
 .tabnav label,.num,code,pre,small,a.dl,.chip{
   font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
 h1,h2,h3,h4,th,td,.toc,figcaption{font-family:inherit}
 th,td{font-variant-numeric:tabular-nums}
 /* A10: numeric cells right-align so digits stack by place value. Only
    cells that are actually numeric -- left-aligning prose is correct. */
 td.num,th.num,td:has(.num){text-align:right}
 /* A7: a visible focus ring. The tab strip and the range control are
    radio+label, so a keyboard reader lands on an input that is clipped to
    1px -- without this the focus is invisible and the page is unusable by
    keyboard. Applied to the LABEL, which is what a reader sees. */
 .tabs input:focus-visible + label,.fwr:focus-visible + label,
 a:focus-visible,summary:focus-visible,#dm:focus-visible + .dml{
   outline:3px solid var(--accent);outline-offset:2px}
 /* Backstop. The rule above names the controls this page has TODAY; anything
    focusable added later would ship with no indicator and nobody would notice,
    because a missing focus ring is invisible to everyone not using a keyboard.
    :focus-visible only fires for keyboard interaction, so this costs mouse
    users nothing. The tab strip's own ring is emitted per-tab in projectors.py
    -- its labels are not adjacent siblings of their radios, so the selector
    above cannot reach them. */
 button:focus-visible,input:focus-visible,select:focus-visible,
 textarea:focus-visible,[tabindex]:focus-visible,label:focus-visible{
   outline:3px solid var(--accent);outline-offset:2px}
 /* A15: the tab strip stays reachable in a 111,000-character panel. */
 .tabnav{position:sticky;top:0;z-index:5;background:var(--bg)}
 h1{font-size:1.6rem;line-height:1.25;letter-spacing:-.01em}
 p{margin:.7rem 0}
 /* Wide evidence must not widen the PAGE. The previous rule put display:block
    on the table itself to get overflow-x, and that destroys the table formatting
    context: cells stop participating in column layout, so a 900-character prose
    cell expands to its natural width instead of wrapping. One cell in
    Contributing trials reached 3,935px and dragged 3,782px of horizontal scroll
    onto the whole document. The scroll container belongs on a WRAPPER, never on
    the table -- the table must keep display:table to lay out at all. */
 .tscroll{max-width:100%%;overflow-x:auto}
 .card table,.doc table{width:100%%;table-layout:auto}
 /* Long unbroken tokens -- a DOI, a URL, an accession -- cannot wrap without
    this and would reintroduce the same overflow one string at a time. */
 th,td{overflow-wrap:break-word;word-break:normal;text-align:left}th:first-child,td:first-child{min-width:12ch}
 @media (max-width:560px){body{padding:1rem .75rem;font-size:1rem}
   .tabnav label{padding:.4rem .6rem;font-size:.82rem}
   /* .num carries white-space:nowrap so a figure never breaks mid-number.
      Some projected values are whole phrases -- the registration margin is
      one -- and at 360px an unbreakable 539px span was the last thing
      pushing the page sideways. On a phone, wrapping the phrase beats
      scrolling the document. */
   /* span.num, not .num: the base .num rule is declared later in the sheet
      at equal specificity and was winning the cascade, so the phrase stayed
      unbreakable and the page still scrolled 88px at 485. */
   span.num{white-space:normal;overflow-wrap:anywhere}}
 #dm{position:absolute;width:1px;height:1px;opacity:0}
 .dml{position:fixed;top:.5rem;right:.5rem;z-index:9;border:1px solid var(--line);
       border-radius:1rem;padding:.15rem .6rem;font-size:.8rem;cursor:pointer;
       background:var(--bg);color:var(--muted)}
 svg{color:var(--fg)}
 .fwr{position:absolute;width:1px;height:1px;opacity:0}
 .fwl{display:inline-block;border:1px solid var(--line);border-radius:.35rem;
       padding:.1rem .55rem;margin:0 .3rem .4rem 0;font-size:.85rem;
       cursor:pointer;color:var(--muted)}
 /* height:0 rather than display:none -- display:none drops the node from
    document.body.innerText and the invariance detector would see nothing. */
 .fwp{height:0;overflow:hidden}
 #fw-fit:checked~#fwp-fit,#fw-w1:checked~#fwp-w1,
 #fw-w2:checked~#fwp-w2,#fw-w3:checked~#fwp-w3{height:auto;overflow:visible}
 #fw-fit:checked~.fwl[for=fw-fit],#fw-w1:checked~.fwl[for=fw-w1],
 #fw-w2:checked~.fwl[for=fw-w2],#fw-w3:checked~.fwl[for=fw-w3]{
       border-color:var(--accent);color:var(--fg);font-weight:600}
 .card{border:1px solid var(--line);border-radius:.5rem;padding:1rem;margin:1rem 0}
 .card.warn{border-color:var(--warnb);background:var(--warnbg)}
 .num{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
 table{border-collapse:collapse;width:100%%} th,td{border:1px solid var(--line);padding:.5rem;text-align:left;vertical-align:top}
 small{color:var(--muted)}
 a{color:var(--accent)}
%s%s</style>

<input type="checkbox" id="dm"><label for="dm" class="dml" title="Switch the page
between light and dark. Figures inherit the text colour, so they stay legible in
both; downloaded files are always generated light for print.">&#9681; theme</label>
%s
<h1>%s</h1>
<p>%s</p>

%s
<p><small>Every number on this page is projected from a single canonical object,
and each measured cell names the source analysis it was read from. That is what is
machine-checked. It does not establish that the underlying sources are right, only
that this page faithfully reports them.</small></p>
""" % (p(canon["title"]), tab_css, wy.DOC_CSS,   # NOT %-escaped: DOC_CSS is an ARGUMENT, not part of the
       # template. It was escaped back when it was spliced into the literal,
       # and the escaping was left behind when it became an argument -- so
       # every rule shipped as width:100%% and the browser dropped all of
       # them. That is why the document-view images rendered at their
       # natural 1406px and dragged horizontal scroll onto the page.

       pj.verdict_card(canon, rd, p),
       p(canon["title"]), p(canon["question"]), body)


if __name__ == "__main__":
    obj = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    # Raster handles, resolved once. If no headless browser is present the
    # figures still build and offer the vector format, and each figure SAYS the
    # rasters were not generated rather than quietly offering fewer files.
    import figures as _fg
    _rd = os.path.join(os.path.dirname(os.path.abspath(out)) or ".", "figs")
    os.makedirs(_rd, exist_ok=True)
    pj.RASTER.update(browser=_fg.find_browser(), workdir=_rd, outdir=_rd)
    print("raster browser: %s" % (pj.RASTER["browser"] or "NONE -- vector only"))
    _html = build(obj)
    # Tokens reach the page through paths fill() never sees -- a figure title, a
    # note, any string interpolated straight into HTML. Checking fill()'s own
    # inputs therefore does not establish the claim that no placeholder reaches a
    # reader. This checks the ARTEFACT, which is the only thing that claim is
    # actually about.
    import re as _re
    _leaked = sorted(set(_re.findall(r"\[\[[a-z0-9_]+\]\]", _html)))
    if _leaked:
        raise SystemExit("BUILD REFUSED: unsubstituted placeholder(s) reached the "
                         "rendered page: %s" % ", ".join(_leaked))
    # WOULD THIS BUILD DESTROY A MANUSCRIPT ALREADY DELIVERED HERE?
    #
    # ARNI serves a 100,825-character authored docmodel render. _paper_panel() prefers the
    # projector, ARNI's object now satisfies the projector, so a rebuild replaces 26
    # sections with 1 -- a 94% loss that exits 0 and passes the regression check, which
    # counts studies and pools and has no opinion about manuscripts.
    #
    # Checked HERE, before the file is opened for writing, so a refusal leaves the
    # delivered page untouched.
    import manuscript_guard as _mg
    _mg.enforce(_html, out)
    open(out, "w", encoding="utf-8").write(_html)
    print("built %s (%d bytes)" % (out, os.path.getsize(out)))
