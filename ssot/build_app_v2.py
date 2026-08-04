#!/usr/bin/env python
"""Project a schema-v2 canonical object into an app page.

Same discipline as the v1 generator, which is frozen with the golden reference:
this file holds NO study numbers. Every numeral a reader sees is formatted from
the object at emit time, and prose {references} resolve against it, so a
sentence cannot go stale against the field it describes.

What v2 adds over v1: many trials, an outcome-keyed structure, a pooled result
with heterogeneity, a removal disclosure, and a source registry that names where
each cell came from.
"""
import html
import json
import re
import sys
from pathlib import Path

REF_RE = re.compile(r"\{([a-z0-9_]+(?:\.[a-z0-9_]+|\[\d+\])*)\}", re.I)
ALIASES = {"res": "results", "cfg": "config", "rm": "removed_citations",
           "t": "inputs.trials[0]"}


def fmt(x):
    if x is None:
        return "not stated"
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return str(x)


def resolve(canon, ref):
    head, _, rest = ref.partition(".")
    path = (ALIASES[head] + ("." + rest if rest else "")) if head in ALIASES else ref
    node = canon
    for part in path.split("."):
        if "[" in part:
            name, idx = part[:-1].split("[")
            node = node[name][int(idx)]
        else:
            node = node[part]
    return node


def render(canon, s):
    """Resolve references, bounded so a cycle fails loudly."""
    for _ in range(8):
        out = REF_RE.sub(lambda m: fmt(resolve(canon, m.group(1))), s)
        if out == s:
            return out
        s = out
    raise ValueError(f"reference resolution did not converge in {s[:60]!r}")


def build(canon: dict) -> str:
    e = html.escape
    def p(s):
        return e(render(canon, s))

    oid = next(iter(canon["results"]["by_outcome"]))
    outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
    res = canon["results"]["by_outcome"][oid]
    pooled, het = res["pooled"], res.get("heterogeneity") or {}
    srcs = canon["sources"]
    rm = canon.get("removed_citations")

    rows = ""
    for t in canon["inputs"]["trials"]:
        d = t["by_outcome"][oid]
        eff, an = d["effect"], d.get("analysed") or {}
        rows += (
            f"    <tr><td>{p(t['name'])}<br><small>{e(t['nct'])} &middot; "
            f"{e(d.get('outcome_role_in_trial', 'primary'))} outcome</small></td>"
            f"<td class='num'>{fmt(an.get('treatment'))} / {fmt(an.get('control'))}</td>"
            f"<td class='num'>{fmt(eff['point'])} "
            f"({fmt(eff['ci_low'])} to {fmt(eff['ci_high'])})</td>"
            f"<td><small>{p(srcs[d['provenance']['source_id']]['layer'])}: "
            f"{p(d['provenance'].get('source_outcome_title', d['provenance']['source']))}"
            f"</small></td></tr>\n")

    removal = ""
    if rm:
        cats = "".join(
            f"    <li><strong>{p(c['reason'])}</strong> &mdash; {fmt(c['count'])}. "
            f"{p(c['detail'])}"
            + (f" <em>{e(', '.join(c['removed_ids']))}</em>" if c.get("removed_ids") else "")
            + "</li>\n" for c in rm["categories"])
        removal = (f"<div class='card warn'>\n  <h2>What was removed, and why</h2>\n"
                   f"  <p>{p(rm['disclosure_note'])}</p>\n  <ul>\n{cats}  </ul>\n</div>\n")

    sources = "".join(
        f"    <tr><td>{p(v['layer'])}</td><td>{p(v['name'])}<br>"
        f"<small>{e(v['url'])}</small></td><td><small>{p(v['access_note'])}</small></td></tr>\n"
        for v in sorted(srcs.values(), key=lambda x: x.get("layer_rank", 99)))

    return f"""<meta charset="utf-8">
<title>{p(canon['title'])}</title>
<style>
 body{{font-family:system-ui,-apple-system,sans-serif;max-width:64rem;margin:0 auto;padding:1.5rem;line-height:1.6;color:#111}}
 .badge{{background:#b45309;color:#fff;padding:.75rem 1rem;border-radius:.375rem;font-size:.9rem}}
 .card{{border:1px solid #d4d4d8;border-radius:.5rem;padding:1rem;margin:1rem 0}}
 .card.warn{{border-color:#b45309;background:#fffbeb}}
 .num{{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}}
 table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #d4d4d8;padding:.5rem;text-align:left;vertical-align:top}}
 small{{color:#3f3f46}}
</style>

<div class="badge" role="status">NOT SUBMISSION-READY &mdash; rebuilt on a sourceable core.
Trials pooled: {fmt(res['k'])}. Outcome: one. Between-trial variation: {p(res['heterogeneity_status'])}.</div>

<h1>{p(canon['title'])}</h1>
<p>{p(canon['question'])}</p>

<div class="card">
  <h2>Pooled result</h2>
  <p class="num">{e(pooled['measure'])} {fmt(pooled['point'])}
     ({fmt(pooled['ci_low'])} to {fmt(pooled['ci_high'])}),
     {fmt(pooled['ci_level'])}% interval</p>
  <p>{p(outcome['name'])}. {p(res['model'])}-effects, estimator {p(res['estimator_used'])},
     k = {fmt(res['k'])}.</p>
  <p><small>&tau;&sup2; {fmt(het.get('tau2'))} &middot; I&sup2; {fmt(het.get('i2'))}%
     &middot; Q {fmt(het.get('q'))} on {fmt(het.get('df'))} df</small></p>
  <p><strong>How to read this:</strong> {p(res['interpretation_caveat'])}</p>
</div>

<div class="card">
  <h2>Contributing trials</h2>
  <table>
    <tr><th>Trial</th><th>Analysed<br><small>treatment / control</small></th>
        <th>{e(outcome['measure'])} (95% CI)</th><th>Source of this cell</th></tr>
{rows}  </table>
  <p><small>{p(outcome['definition_note'])}</small></p>
</div>

{removal}
<div class="card">
  <h2>Sources</h2>
  <table>
    <tr><th>Layer</th><th>Source</th><th>How it was obtained</th></tr>
{sources}  </table>
</div>

<p><small>Every number on this page is projected from a single canonical object,
and each measured cell names the source analysis it was read from. That is what
is machine-checked. It does not establish that the underlying sources are right,
only that this page faithfully reports them.</small></p>
"""


def main():
    canon = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.write_text(build(canon), encoding="utf-8")
    print(f"built {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
