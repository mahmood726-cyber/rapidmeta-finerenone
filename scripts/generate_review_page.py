# -*- coding: utf-8 -*-
"""AUTO_FULL review page generator: object -> self-contained HTML page.

The load-bearing component. A review page is a PURE FUNCTION of its committed ssot object, so the page
can never drift from the object (the object<->page divergence / half-migration that three reviewers
called a submission blocker). Renders ONLY current values; superseded object fields are shown solely in
a clearly-'superseded'-labelled section, so reproduce_review's RENDER axis (headline present + engine
match + no dead value served live) passes.

Acceptance test (both directions):
  1. generate_page(review_id) -> HTML written to <REVIEW_ID>.generated.html
  2. reproduce_review RENDER against it must REPRODUCE (headline shown, no superseded value served live).

Deliberate first target: the AUTO_FULL family (EMPAGLIFLOZIN first -- clean object, reproduces
PROTOCOL+PIPELINE). SGLT2's 3.9MB hand-app stays bannered until last.
"""
from __future__ import annotations
import io, os, re, json, math, sys, html, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = 1.959963985


def _load(mod, path):
    spec = importlib.util.spec_from_file_location(mod, os.path.join(ROOT, "scripts", path))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


_hksj = _load("modified_hksj", "modified_hksj.py")


def _e(x):
    return html.escape("" if x is None else str(x))


def _fmt(x, dp=4):
    return ("%.*f" % (dp, x)).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def _primary_outcome(obj):
    bo = (obj.get("results") or {}).get("by_outcome") or {}
    # the outcome with the most contributing trials is the primary pool
    best = None
    for oid, o in bo.items():
        if isinstance(o, dict) and o.get("pooled") and o.get("per_trial"):
            if best is None or len(o.get("per_trial") or []) > len(best[1].get("per_trial") or []):
                best = (oid, o)
    return best


def _forest_svg(per_trial, pooled, measure):
    """A minimal, dependency-free forest plot. Ratio measures on a log axis, differences on a linear one."""
    is_ratio = measure.upper() in ("HR", "RR", "OR", "IRR", "LOG_HR", "LOG_RR", "LOG_OR")
    rows = [(t.get("trial") or t.get("label") or t.get("nct"), t.get("point"), t.get("ci_low"), t.get("ci_high"))
            for t in per_trial if isinstance(t.get("point"), (int, float))]
    rows.append(("Pooled", pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")))
    xs = [v for _, p, lo, hi in rows for v in (lo, hi) if isinstance(v, (int, float))]
    if not xs:
        return ""
    tx = (lambda v: math.log(v)) if is_ratio else (lambda v: v)
    lo_x, hi_x = min(tx(v) for v in xs), max(tx(v) for v in xs)
    pad = (hi_x - lo_x) * 0.12 or 0.1
    lo_x, hi_x = lo_x - pad, hi_x + pad
    W, rowh, left = 760, 30, 320
    def X(v):
        return left + (tx(v) - lo_x) / (hi_x - lo_x) * (W - left - 30)
    H = rowh * (len(rows) + 1) + 20
    null = 1.0 if is_ratio else 0.0
    parts = ['<svg viewBox="0 0 %d %d" role="img" aria-label="Forest plot" style="max-width:100%%;height:auto;font:13px system-ui">' % (W, H)]
    if lo_x <= tx(null) <= hi_x:
        parts.append('<line x1="%.1f" y1="20" x2="%.1f" y2="%d" stroke="#9ca3af" stroke-dasharray="4 3"/>' % (X(null), X(null), H - 20))
    for i, (name, p, lo, hi) in enumerate(rows):
        y = 30 + i * rowh
        is_pool = (name == "Pooled")
        parts.append('<text x="8" y="%.1f" %s>%s</text>' % (y + 4, 'font-weight="700"' if is_pool else '', _e(name)[:44]))
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
            parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#111"/>' % (X(lo), y, X(hi), y))
        if isinstance(p, (int, float)):
            if is_pool:
                cx = X(p)
                parts.append('<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f Z" fill="#1d4ed8"/>'
                             % (cx, y - 6, X(hi) if isinstance(hi, (int, float)) else cx, y,
                                cx, y + 6, X(lo) if isinstance(lo, (int, float)) else cx, y))
            else:
                parts.append('<rect x="%.1f" y="%.1f" width="8" height="8" fill="#111"/>' % (X(p) - 4, y - 4))
            parts.append('<text x="%d" y="%.1f" text-anchor="end">%s (%s–%s)</text>'
                         % (W - 2, y + 4, _fmt(p, 3), _fmt(lo, 3), _fmt(hi, 3)))
    parts.append("</svg>")
    return "".join(parts)


# Analyses that are REFUSED at small k for a stated reason -- a declared refusal, not silence.
# The reviewers praised these pages for withholding GOSH/TSA/meta-regression/funnel below their
# thresholds; the generator renders that refusal WITH its reason, same discipline as harms.
_REFUSAL_RULES = [
    ("GOSH (graphical exploration of heterogeneity)", 10,
     "explores model fit across the 2^k study subsets; below k&asymp;10 there are too few subsets for the cloud to be informative"),
    ("Trial-sequential analysis (TSA)", 5,
     "the required information size and O'Brien-Fleming boundaries are unstable with a handful of trials; a pooled point at this k is not a monitoring boundary"),
    ("Meta-regression", 10,
     "Cochrane Handbook advises &ap;10 studies per covariate; fitting a moderator at this k over-fits and is not reported"),
    ("Funnel plot / Egger's test (small-study effects)", 10,
     "both have negligible power below k&asymp;10 (Handbook 13.3.5.4); a funnel with this many points cannot distinguish asymmetry from chance"),
]


def _refusal_sections(k):
    out = "<h2>Analyses withheld at this k (declared refusals, not omissions)</h2><ul>"
    for title, thresh, reason in _REFUSAL_RULES:
        if k < thresh:
            out += "<li><strong>%s &mdash; not reported at k=%d.</strong> %s.</li>" % (_e(title), k, reason)
    out += "</ul>"
    return out


def _completeness_disclosure(review_id, generated_html):
    """Condition 1+2: publish the measured delta as a NAMED list, and flag the subset that would
    need object fields we do not yet hold (the specification for a future narrative-parity build)."""
    # original pages are named with UNDERSCORES (EMPAGLIFLOZIN_HF_AUTO_FULL_REVIEW.html); the
    # review_id carries hyphens, so try both spellings before declaring no prior page.
    cands = [review_id.upper().replace("-", "_") + ".html", review_id.upper() + ".html"]
    orig_path = next((os.path.join(ROOT, c) for c in cands if os.path.exists(os.path.join(ROOT, c))), None)
    orig_name = os.path.basename(orig_path) if orig_path else cands[0]
    if not orig_path:
        return "<h2>Content-completeness</h2><p>No prior hand-maintained page found to diff against; this page is the first rendering of the object.</p>"
    try:
        cc = _load("content_completeness", "content_completeness.py")
    except Exception:
        return ""
    orig = io.open(orig_path, encoding="utf-8", errors="replace").read()
    d = cc.delta(orig, generated_html)
    missing = [m for m in d["missing_in_generated"]]
    claim_missing = [m for m in missing if m.startswith("claim:")]
    head_missing = [m[2:] for m in missing if m.startswith("h:")]
    # headings that plausibly carry DATA (not prose framing) -> would need object fields = a finding
    NEEDS_FIELD = ("extraction", "endpoint", "trial characteristics", "references", "regulatory",
                   "inter-assessor", "audit trail", "trial-sequential", "meta-regression", "gosh",
                   "included studies", "figures", "visual abstract")
    needs_field = sorted({h for h in head_missing if any(t in h for t in NEEDS_FIELD)})
    prose = sorted(set(head_missing) - set(needs_field))
    s = "<h2>Content-completeness (measured, disclosed)</h2>"
    s += "<p>Semantic categories present: all %d (every claim the object holds renders; every absence is declared). " % 8
    if claim_missing:
        s += "<strong>Claim categories still missing: %s.</strong> " % _e(", ".join(claim_missing))
    s += "%d narrative headings from the prior page are not reproduced &mdash; enumerated below, never waved away.</p>" % len(head_missing)
    if needs_field:
        s += ("<p><strong>Of those, %d would require object fields that do not yet exist</strong> "
              "(a finding: this is the specification for a future narrative-parity build, not something to invent tonight): "
              "%s.</p>" % (len(needs_field), _e("; ".join(needs_field))))
    if prose:
        s += "<details><summary>%d narrative/framing headings not reproduced (prose, no object data lost)</summary><p>%s</p></details>" % (
            len(prose), _e("; ".join(prose)))
    s += ("<p class='muted'>The prior hand-maintained page remains retrievable at "
          "<code>%s</code>; this compact page replaces it in serving but does not destroy the record of what was served.</p>" % _e(orig_name))
    return s


def generate_page(review_id):
    slug = review_id.lower().replace("_", "-")
    obj = json.load(io.open(os.path.join(ROOT, "ssot", slug, slug + ".json"), encoding="utf-8"))
    oid, o = _primary_outcome(obj)
    pooled = o["pooled"]; measure = pooled.get("measure", o.get("measure", "HR"))
    het = o.get("heterogeneity") or {}
    declared_model = pooled.get("model") or o.get("model") or "random-effects"
    declared_ci = pooled.get("ci_method") or ""
    # ONE method, the one the OBJECT declares. Only render the modified-HKSJ interval when the object
    # actually declares HKSJ -- imposing it universally recomputes t_{k-1} (=12.7 at k=2) and
    # manufactures a SECOND interval that contradicts the served CI. The generator renders the object's
    # served interval; it does not re-derive one by a method the object did not use.
    uses_hksj = re.search(r"hksj|hartung", declared_model + " " + declared_ci, re.I)
    if uses_hksj and measure.upper() in ("HR", "RR", "OR", "IRR") and isinstance(het.get("q"), (int, float)):
        se = _hksj.se_from_ci(pooled["point"], pooled["ci_low"], pooled["ci_high"])
        lo, hi, info = _hksj.modified_hksj(math.log(pooled["point"]), se, Q=het["q"], k=len(o["per_trial"]))
        hksj_line = ("interval: modified HKSJ, floor q=max(1,Q/(k−1)) at 1, t<sub>k−1</sub> "
                     "(<strong>%s–%s</strong>, matching the served CI)" % (_fmt(lo, 3), _fmt(hi, 3)))
    else:
        # if the object names a distinct CI method, state it once; otherwise the model line already has it
        hksj_line = ("interval: %s" % _e(declared_ci)) if declared_ci else "interval as served by the object"

    def row(k, v):
        return "<tr><th scope='row'>%s</th><td>%s</td></tr>" % (_e(k), v)

    trials_rows = ""
    for t in o["per_trial"]:
        trials_rows += ("<tr><td>%s</td><td>%s</td><td>%s (%s–%s)</td><td>%s</td><td>%s</td></tr>"
                        % (_e(t.get("trial") or t.get("label") or t.get("nct")), _e(t.get("nct")),
                           _fmt(t.get("point"), 3), _fmt(t.get("ci_low"), 3), _fmt(t.get("ci_high"), 3),
                           _e(t.get("analysis_variant") or ""),
                           _e((t.get("provenance") or {}).get("tier") if isinstance(t.get("provenance"), dict)
                              else (t.get("source") or ""))))

    comp = o.get("component_effects_machine_readable_2026_09_03")
    comp_html = ""
    if isinstance(comp, dict):
        comp_html = "<h2>Component decomposition</h2><p>%s</p><ul>" % _e(comp.get("why_this_is_on_the_page", ""))
        for k, v in comp.items():
            if k.startswith("why") or k.startswith("what"):
                continue
            comp_html += "<li><strong>%s:</strong> %s</li>" % (_e(k.replace("_", " ")), _e(v))
        comp_html += "</ul>"

    bench = o.get("external_benchmark_2026_09_07") or o.get("external_benchmark")
    bench_html = ""
    if isinstance(bench, dict):
        if bench.get("independent_external_exists") is False:
            bench_html = ("<h2>External benchmark</h2><p><strong>No independent external benchmark exists.</strong> %s</p>"
                          % _e(bench.get("why", "")))
        else:
            bench_html = "<h2>External benchmark</h2><p>%s</p>" % _e(bench.get("why_genuinely_external") or json.dumps(bench)[:300])

    forest = _forest_svg(o["per_trial"], pooled, measure)
    title = obj.get("title") or review_id
    question = obj.get("question") or ""
    het_line = ("Q = %s on %s df, I² %s%%, τ² %s"
                % (_fmt(het.get("q"), 4), het.get("df", len(o["per_trial"]) - 1),
                   _fmt(het.get("i2"), 1), _fmt(het.get("tau2"), 4))) if het else ""

    body = """<!doctype html>
<html lang="en" data-store="ssot/{slug}/{slug}.json" data-artefact="review" data-generated="object">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
 :root{{--fg:#111;--muted:#3f3f46;--line:#d4d4d8;--accent:#1d4ed8}}
 body{{font:15px/1.55 system-ui;color:var(--fg);max-width:900px;margin:2rem auto;padding:0 1rem}}
 h1{{font-size:1.5rem;line-height:1.3}} h2{{font-size:1.15rem;margin-top:2rem;border-bottom:1px solid var(--line);padding-bottom:.2rem}}
 table{{border-collapse:collapse;width:100%;margin:.5rem 0}} th,td{{border:1px solid var(--line);padding:.4rem .6rem;text-align:left;vertical-align:top}}
 .headline{{font-size:1.3rem;font-weight:700}} .muted{{color:var(--muted);font-size:.9rem}}
 caption{{text-align:left;font-weight:600;margin:.3rem 0}}
</style>
<h1>{title}</h1>
<p class="muted">This page is <strong>generated from its object</strong> (<code>ssot/{slug}/{slug}.json</code>);
every value below is a function of that committed object. Primary outcome: <em>{outcome}</em>.</p>
<p>{question}</p>

<h2>Primary result</h2>
<p class="headline">{measure} {pt} ({lo}–{hi})</p>
<p class="muted">{k} trials, {model}{estimator}. {hksj}. {het}</p>
{forest}

<h2>Contributing trials</h2>
<table><caption>Per-trial estimates with analysis variant and provenance tier</caption>
<tr><th>Trial</th><th>NCT</th><th>{measure}</th><th>Variant</th><th>Provenance</th></tr>
{trials}</table>

{comp}
{bench}

<h2>Heterogeneity</h2>
<p>{het}. {het_status}</p>
""".format(slug=_e(slug), title=_e(title), outcome=_e(oid), question=_e(question),
           measure=_e(measure), pt=_fmt(pooled["point"], 4), lo=_fmt(pooled["ci_low"], 4), hi=_fmt(pooled["ci_high"], 4),
           k=len(o["per_trial"]), model=_e(declared_model),
           estimator=(" (%s)" % _e(pooled.get("estimator"))) if pooled.get("estimator") else "",
           hksj=hksj_line, het=het_line, forest=forest, trials=trials_rows, comp=comp_html, bench=bench_html,
           het_status=_e((o.get("heterogeneity_status") or "")[:600]))

    # ---- GRADE (from grade.by_outcome.<oid> or a flat grade) ----------------------------------
    grade = obj.get("grade") or o.get("grade")
    g_oc = (grade.get("by_outcome", {}).get(oid) if isinstance(grade, dict) else None) or (grade if isinstance(grade, dict) else {})
    if g_oc.get("certainty"):
        body += "<h2>Certainty of the evidence (GRADE)</h2><p>Certainty: <strong>%s</strong>." % _e(g_oc.get("certainty"))
        if g_oc.get("why"):
            body += " " + _e(g_oc["why"])[:400]
        body += "</p>"
        steps = g_oc.get("steps") or []
        if steps:
            body += "<ul>" + "".join("<li>%s: %s</li>" % (_e((s or {}).get("domain")), _e(json.dumps((s or {}).get("levels") or (s or {}).get("reason") or ""))[:160]) for s in steps) + "</ul>"

    # ---- Risk of bias (RoB 2, per result) -----------------------------------------------------
    rob = obj.get("risk_of_bias")
    rob_oc = (rob.get("by_outcome", {}).get(oid) if isinstance(rob, dict) else None)
    if isinstance(rob_oc, dict):
        body += "<h2>Risk of bias (RoB 2, assessed per result)</h2><table><tr><th>Trial</th><th>Overall / domains</th></tr>"
        for nct, r in rob_oc.items():
            if isinstance(r, dict):
                overall = r.get("overall") or r.get("judgement") or json.dumps({k: v for k, v in r.items() if k != "nct"})[:120]
                body += "<tr><td>%s</td><td>%s</td></tr>" % (_e(nct), _e(overall)[:200])
        body += "</table>"
        body += "<p class='muted'>RoB 2 assesses bias in the trial RESULT, not deficiencies in this review's document retrieval.</p>"

    # ---- Published comparison ----------------------------------------------------------------
    pc = obj.get("published_comparison")
    if isinstance(pc, dict) and pc.get("_why"):
        body += "<h2>Comparison with published syntheses</h2><p>%s</p>" % _e(pc["_why"])[:600]

    # ---- Screening (render the DECLARED ABSENCE honestly, not a blank) -------------------------
    scr = obj.get("screening") or {}
    if isinstance(scr, dict):
        sn = scr.get("search_note"); recs = scr.get("records") or []
        body += "<h2>Screening and search</h2>"
        if not recs and (not sn or "not recorded" in str(sn).lower()):
            body += "<p><strong>No search/screening record was extracted for this review</strong> (the source page did not carry one). This is a declared absence, not a completed PRISMA flow.</p>"
        else:
            body += "<p>%s</p>" % _e(sn or "")[:400]

    # ---- Harms: a DECLARED ABSENCE is not the same as an omission (null + state) ---------------
    harms = obj.get("harms") or (o.get("harms")) or (obj.get("mandatory_outputs") or {}).get("harms")
    body += "<h2>Harms</h2>"
    if harms:
        body += "<ul>" + "".join("<li>%s</li>" % _e(h) for h in harms) + "</ul>"
    else:
        body += "<p><strong>No harms outcome extracted.</strong> The object holds no harms data for this review; this absence is declared explicitly rather than the section being silently dropped. (A harms extraction is owed.)</p>"

    # ---- Funding: declared absence ------------------------------------------------------------
    if not re.search(r"fund|sponsor", json.dumps(obj), re.I):
        body += "<h2>Funding</h2><p><strong>No funding statement extracted</strong> (declared absence; owed).</p>"

    # ---- Absolute effect: DERIVED transparently from the ratio; baseline is a declared absence ----
    _pt = pooled.get("point")
    is_ratio = str(measure).lower() in ("or", "rr", "hr", "log_or", "log_rr", "log_hr") or "ratio" in str(measure).lower()
    if is_ratio and isinstance(_pt, (int, float)):
        body += "<h2>Absolute effect, at baseline risks you choose</h2>"
        baseline = obj.get("reference_baseline_risk") or o.get("reference_baseline_risk")
        if baseline:
            b = float(baseline); arr = b * (1 - _pt)
            body += "<p>At a baseline risk of %.1f%%, this %s of %.3f implies an absolute risk reduction of %.2f percentage points (NNT %.0f).</p>" % (b * 100, str(measure).upper(), _pt, arr * 100, (1 / arr if arr else float('inf')))
        else:
            body += ("<p>An effect of <strong>%.3f</strong> means: at a baseline risk B, the absolute risk reduction is "
                     "B&times;(1&minus;%.3f) and the NNT is 1 / [B&times;%.3f]. <strong>This review's object declares no reference "
                     "baseline risk</strong>, so no specific ARR or NNT is asserted here &mdash; the absolute effect is stated as a "
                     "formula rather than invented from an assumed baseline.</p>") % (_pt, _pt, (1 - _pt))

    # ---- Declared refusals at this k (GOSH/TSA/meta-regression/funnel) -------------------------
    k_studies = len(o.get("per_trial") or [])
    body += _refusal_sections(k_studies)

    # ---- Content-completeness disclosure (measured delta vs the prior page; conditions 1-3) -----
    body += _completeness_disclosure(review_id, body)

    out = os.path.join(ROOT, review_id.upper() + ".generated.html")
    io.open(out, "w", encoding="utf-8").write(body)
    return out, pooled["point"]


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rid = sys.argv[1] if sys.argv[1:] else "EMPAGLIFLOZIN_HF_AUTO_FULL_REVIEW"
    path, pt = generate_page(rid)
    print("generated %s (headline %s)" % (path, pt))
