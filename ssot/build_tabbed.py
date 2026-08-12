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
import projectors as pj           # noqa: E402
import projectors2 as p2
import paper as pp          # noqa: E402

NL = pj.NL
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
    meas = e(str(pooled.get("measure", "")))

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
        snips.append(("Certainty", "GRADE certainty: %s" % e(str(g["certainty"]))))
    chips = "".join('    <button type="button" class="chip" data-ins="%s">%s'
                    '</button>%s' % (v, k, NL) for k, v in snips)

    cites = canon.get("citations") or {}
    pol = (canon.get("citation_policy") or {}).get("ratio") or {}
    refs = ""
    for i, (pmid, c) in enumerate(sorted(cites.items()), 1):
        bits = [p(c.get("authors_vancouver", "")), p(c.get("title", "")),
                p(c.get("journal", "")), pj.fmt(c.get("year"))]
        vol = "%s%s%s" % (c.get("volume") or "",
                          "(%s)" % c["issue"] if c.get("issue") else "",
                          ":%s" % c["pages"] if c.get("pages") else "")
        st = c.get("link_status")
        note = c.get("doi_link_note") or c.get("link_note")
        refs += ("    <li>%s. <em>%s</em> %s;%s. "
                 "<a href='%s'>PMID %s</a> [HTTP %s]%s%s</li>%s"
                 % (bits[0], bits[1], bits[2], vol or bits[3],
                    e(c.get("url", "")), e(pmid), e(str(st)),
                    (" <a href='%s'>doi</a>" % e(c["doi_url"])) if c.get("doi_url") else "",
                    (" <small>%s</small>" % p(note)) if note else "", NL))
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
                   ("%s %s (%s to %s)" % (e(str(pl.get("measure", ""))),
                                          pj.fmt(pl["point"]),
                                          pj.fmt(pl["ci_low"]),
                                          pj.fmt(pl["ci_high"]))
                    if pl.get("point") else "not pooled"),
                   p(g["certainty"]) if g.get("certainty") else "&mdash;", NL))
    reg = canon.get("registration") or {}
    c0 = (reg.get("commits") or [{}])[0]
    first = next(iter(canon["results"]["by_outcome"].values()), {})
    repro = pj.kv_card("Reproducibility artifact", [
        ("Canonical object", "<code>%s</code>" % e(str(reg.get("path", "")))),
        ("Registered at", "<code>%s</code> %s" % (e(str(c0.get("sha", ""))[:12]),
                                                  e(str(c0.get("committed_utc", ""))))),
        ("Permalink", ("<a href='%s'>%s</a>" % (e(c0["permalink"]), e(c0["permalink"])))
         if c0.get("permalink") else ""),
        ("Schema", e(str(canon.get("schema_version", "")))),
        ("Built", e(str(canon.get("built", "")))),
        ("Statistical engine", p((first.get("cross_engine") or {}).get("engine", ""))),
    ], "Everything a third party needs to rebuild this page. Each figure on the "
       "Analysis tab downloads as an SVG carrying exactly the values shown.")
    return ("<div class='card'>%s  <h3>Summary of findings</h3>%s  <table>%s"
            "    <tr><th>Outcome</th><th>k</th><th>Pooled effect</th>"
            "<th>Certainty</th></tr>%s%s  </table>%s</div>%s"
            % (NL, NL, NL, NL, sof, NL, NL)) + repro


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
        d["figures"] = p2.analysis_figures(res, outcome, p)
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
        "carried": "", "considered": "", "components": "",
        "rob": p2.rob2_card(canon, p),
        "switching": p2.discrepancies_card(canon, p),
        "sources_card": ("<div class='card'>%s  <h2>Sources</h2>%s  <table>%s"
                         "    <tr><th>Layer</th><th>Source</th>"
                         "<th>How it was obtained</th></tr>%s%s  </table>%s</div>%s"
                         % (NL, NL, NL, NL, sources_rows, NL, NL)),
        "network": "", "recon": "", "removal": "",
        "output": output_card(canon, p),
        "paper": (pp.manuscript_section(canon, first_res, first_oid, p)
                  + paper_studio(canon, first_res, p)),
    }
    body, tab_css = pj.tabbed_body(canon, parts, page)
    return """<meta charset="utf-8">
<title>%s</title>
<style>
 :root{--bg:#fff;--fg:#111;--line:#d4d4d8;--muted:#3f3f46;
       --warnb:#b45309;--warnbg:#fffbeb;--accent:#1d4ed8}
 @media (prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e8e8ec;
       --line:#33363d;--muted:#a8adb8;--warnb:#d99b3c;--warnbg:#241d10;
       --accent:#7aa2ff}}
 /* Manual override, checkbox + CSS only. :has() keeps the control at the top of
    the document without wrapping the whole body in an extra element. */
 body:has(#dm:checked){--bg:#0f1115;--fg:#e8e8ec;--line:#33363d;--muted:#a8adb8;
       --warnb:#d99b3c;--warnbg:#241d10;--accent:#7aa2ff}
 @media (prefers-color-scheme:dark){body:has(#dm:checked){--bg:#fff;--fg:#111;
       --line:#d4d4d8;--muted:#3f3f46;--warnb:#b45309;--warnbg:#fffbeb;
       --accent:#1d4ed8}}
 body{font-family:system-ui,-apple-system,sans-serif;max-width:64rem;
       margin:0 auto;padding:1.5rem;line-height:1.6;
       color:var(--fg);background:var(--bg)}
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
%s</style>

<input type="checkbox" id="dm"><label for="dm" class="dml" title="Switch the page
between light and dark. Figures inherit the text colour, so they stay legible in
both; downloaded files are always generated light for print.">&#9681; theme</label>
%s
<h1>%s</h1>
<p>%s</p>

%s%s
<p><small>Every number on this page is projected from a single canonical object,
and each measured cell names the source analysis it was read from. That is what is
machine-checked. It does not establish that the underlying sources are right, only
that this page faithfully reports them.</small></p>
""" % (p(canon["title"]), tab_css, pj.verdict_card(canon, rd, p),
       p(canon["title"]), p(canon["question"]), body, READER_JS)


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
    open(out, "w", encoding="utf-8").write(build(obj))
    print("built %s (%d bytes)" % (out, os.path.getsize(out)))
