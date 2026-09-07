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


def generate_page(review_id):
    slug = review_id.lower().replace("_", "-")
    obj = json.load(io.open(os.path.join(ROOT, "ssot", slug, slug + ".json"), encoding="utf-8"))
    oid, o = _primary_outcome(obj)
    pooled = o["pooled"]; measure = pooled.get("measure", o.get("measure", "HR"))
    het = o.get("heterogeneity") or {}
    # modified HKSJ from the pooled value + Q (ratio measures only; difference measures show Wald)
    hksj_line = ""
    if measure.upper() in ("HR", "RR", "OR", "IRR") and isinstance(het.get("q"), (int, float)):
        se = _hksj.se_from_ci(pooled["point"], pooled["ci_low"], pooled["ci_high"])
        lo, hi, info = _hksj.modified_hksj(math.log(pooled["point"]), se, Q=het["q"], k=len(o["per_trial"]))
        hksj_line = ("modified HKSJ (floor q=max(1,Q/(k−1)) at 1, t<sub>k−1</sub>): "
                     "<strong>%s–%s</strong>" % (_fmt(lo, 3), _fmt(hi, 3)))

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
<p class="muted">{k} trials, {model} ({estimator}). {hksj}. {het}</p>
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
           k=len(o["per_trial"]), model=_e(o.get("model", "random-effects")), estimator=_e(o.get("estimator", "REML")),
           hksj=hksj_line, het=het_line, forest=forest, trials=trials_rows, comp=comp_html, bench=bench_html,
           het_status=_e((o.get("heterogeneity_status") or "")[:600]))

    grade = obj.get("grade") or o.get("grade")
    if isinstance(grade, dict) and grade.get("certainty"):
        body += "<h2>GRADE</h2><p>Certainty: <strong>%s</strong>. %s</p>" % (_e(grade.get("certainty")), _e(grade.get("why", ""))[:500])

    out = os.path.join(ROOT, review_id.upper() + ".generated.html")
    io.open(out, "w", encoding="utf-8").write(body)
    return out, pooled["point"]


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rid = sys.argv[1] if sys.argv[1:] else "EMPAGLIFLOZIN_HF_AUTO_FULL_REVIEW"
    path, pt = generate_page(rid)
    print("generated %s (headline %s)" % (path, pt))
