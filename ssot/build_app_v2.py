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

NL = chr(10)

REF_RE = re.compile(r"\{([a-z0-9_]+(?:\.[a-z0-9_]+|\[\d+\])*)\}", re.I)
ALIASES = {"res": "results", "cfg": "config", "rm": "removed_citations",
           "t": "inputs.trials[0]"}


def fmt(x):
    if x is None:
        return "not stated"
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return str(x)


def resolve(canon, ref, scope=None):
    """Resolve a reference. `scope` binds `self` to the record the text lives on.

    A per-trial note that says {t.enrolled} resolves `t` to trials[0] for EVERY
    trial, so a note on the second trial silently reported the first one's
    number. A fixed alias cannot address the record it is attached to; `self`
    can.
    """
    head, _, rest = ref.partition(".")
    if head == "self":
        if not scope:
            raise KeyError("'self' used outside a scoped record")
        path = scope + ("." + rest if rest else "")
    else:
        if head not in ALIASES and head not in canon:
            raise KeyError(
                f"unknown reference alias {head!r} in {ref!r}. Known aliases: "
                f"{sorted(ALIASES)} plus 'self' inside a scoped record, or a "
                f"top-level key of the object.")
        path = (ALIASES[head] + ("." + rest if rest else "")) if head in ALIASES else ref
    node = canon
    for part in path.split("."):
        if "[" in part:
            name, idx = part[:-1].split("[")
            node = node[name][int(idx)]
        else:
            node = node[part]
    return node


def render(canon, s, scope=None):
    """Resolve references, bounded so a cycle fails loudly."""
    for _ in range(8):
        out = REF_RE.sub(lambda m: fmt(resolve(canon, m.group(1), scope)), s)
        if out == s:
            return out
        s = out
    raise ValueError(f"reference resolution did not converge in {s[:60]!r}")


def build(canon: dict) -> str:
    """Render EVERY outcome the object holds, not just the first.

    The object used to carry one outcome and this read `next(iter(...))`. It now
    carries four solicited symptoms, and rendering the first would have shown
    pain alone on the page while the object held all four -- reintroducing the
    selected endpoint at the surface, which is exactly what reporting all four
    was meant to remove. A projection shows what the object holds.
    """
    e = html.escape
    def p(s, scope=None):
        return e(render(canon, s, scope))

    sections = "".join(_outcome_section(canon, oid, p, e)
                       for oid in canon["results"]["by_outcome"])
    return _page(canon, sections, p, e)


def _outcome_section(canon, oid, p, e):
    outcome = next(o for o in canon["outcomes"] if o["id"] == oid)
    res = canon["results"]["by_outcome"][oid]
    pooled, het = res.get("pooled"), res.get("heterogeneity") or {}
    per_trial = {r["trial_id"]: r for r in (res.get("per_trial") or [])}
    srcs = canon["sources"]
    rm = canon.get("removed_citations")

    rows = ""
    for ti, t in enumerate(canon["inputs"]["trials"]):
        # Not every trial posts every symptom: induration is absent from three
        # of these registrations. A trial that does not report an outcome has no
        # row under it, and its absence is stated in the object's subgroup_note
        # rather than filled in with a blank that reads like a zero.
        if oid not in t.get("by_outcome", {}):
            continue
        scope = f"inputs.trials[{ti}]"
        d = t["by_outcome"][oid]
        eff = d.get("effect")
        if eff:
            # per-trial effect form: the trial's own model-based estimate
            size = (f"{fmt((d.get('analysed') or {}).get('treatment'))} / "
                    f"{fmt((d.get('analysed') or {}).get('control'))}")
            est = (f"{fmt(eff['point'])} "
                   f"({fmt(eff['ci_low'])} to {fmt(eff['ci_high'])})")
        else:
            # 2x2 count form. The generator does NOT compute a per-trial effect
            # from these: deriving a number at a surface is exactly what this
            # architecture forbids. The counts are shown; the pooled estimate
            # below is the only effect this object holds.
            tx, ct = d.get("treatment") or {}, d.get("control") or {}
            size = f"{fmt(tx.get('n'))} / {fmt(ct.get('n'))}"
            pt = per_trial.get(t["id"])
            if pt:
                est = (f"{e(pt['measure'])} {fmt(pt['point'])} "
                       f"({fmt(pt['ci_low'])} to {fmt(pt['ci_high'])})"
                       f"<br><small>{fmt(tx.get('events'))} / {fmt(ct.get('events'))} "
                       f"events &middot; reference review reports "
                       f"{fmt(pt['reference_efficacy_percent'])}% efficacy "
                       f"({fmt(pt['reference_ci_low_percent'])} to "
                       f"{fmt(pt['reference_ci_high_percent'])})</small>")
            else:
                est = (f"{fmt(tx.get('events'))} / {fmt(ct.get('events'))} events"
                       "<br><small>no per-trial estimate stored; not derived here</small>")
        rows += (
            f"    <tr><td>{p(t['name'])}<br><small>{e(t['nct'])} &middot; "
            f"{e(d.get('outcome_role_in_trial', 'primary'))} outcome</small></td>"
            f"<td class='num'>{size}</td>"
            f"<td class='num'>{est}</td>"
            f"<td><small>{p(srcs[d['provenance']['source_id']]['layer'])}: "
            f"{p(d['provenance'].get('source_outcome_title', d['provenance']['source']), scope)}"
            + (f"<br><em>{p(t['enrolment_note'], scope)}</em>"
               if t.get("enrolment_note") else "")
            + "</small></td></tr>\n")

    if pooled:
        headline = (
            "<div class='card'>" + NL + "  <h2>Pooled result</h2>" + NL
            + f"  <p class='num'>{e(pooled['measure'])} {fmt(pooled['point'])} "
              f"({fmt(pooled['ci_low'])} to {fmt(pooled['ci_high'])}), "
              f"{fmt(pooled['ci_level'])}% interval</p>" + NL
            + f"  <p>{p(outcome['name'])}. {p(res['model'])}, estimator "
              f"{p(res['estimator_used'])}, k = {fmt(res['k'])}.</p>" + NL
            + f"  <p><small>&tau;&sup2; {fmt(het.get('tau2'))} &middot; I&sup2; "
              f"{fmt(het.get('i2'))}% &middot; Q {fmt(het.get('q'))} on "
              f"{fmt(het.get('df'))} df</small></p>" + NL
            + ((f"  <p><strong>How to read this:</strong> "
                f"{p(res['interpretation_caveat'])}</p>" + NL)
               if res.get("interpretation_caveat") else "")
            + "</div>" + NL)
    else:
        # No headline number, deliberately. This object declines to combine
        # these trials, so there is nothing to put here, and inventing one is
        # exactly the defect the reshape removed.
        headline = (
            "<div class='card warn'>" + NL + "  <h2>No combined estimate</h2>" + NL
            + f"  <p>{p(res['not_poolable_reason'])}</p>" + NL
            + f"  <p><small>{p(res.get('reading_note', ''))}</small></p>" + NL
            + "</div>" + NL)

    # Subgroups, when the object holds them. Rendering these is not decoration:
    # the split is what makes the object comparable with a published synthesis
    # that covers only part of the same population, and a number held in the
    # object but shown nowhere cannot be checked by a reader.
    subgroups = ""
    if res.get("subgroups"):
        srows = "".join(
            f"    <tr><td>{p(sg['label'])}<br><small>"
            f"{e(', '.join(sg.get('trial_ids', [])))}</small></td>"
            f"<td class='num'>{fmt(sg['k'])}</td>"
            f"<td class='num'>{e(sg['measure'])} {fmt(sg['point'])} "
            f"({fmt(sg['ci_low'])} to {fmt(sg['ci_high'])})</td>"
            f"<td class='num'>{fmt(sg.get('i2'))}%</td>"
            # What each stratum MIXES, beside its own estimate. The object held
            # this and the page showed none of it, so the one thing a reader
            # most needs in order to discount the number was unreadable.
            f"<td><small><strong>{e(sg.get('composition', ''))}</strong><br>"
            f"{p(sg.get('note', ''))}</small></td></tr>\n"
            for sg in res["subgroups"])
        subgroups = (f"<div class='card'>\n  <h2>By age stratum</h2>\n  <table>\n"
                     f"    <tr><th>Stratum</th><th>Trials</th>"
                     f"<th>{e(outcome['measure'])} (95% CI)</th><th>I&sup2;</th>"
                     f"<th>What this stratum mixes</th></tr>\n{srows}  </table>\n"
                     f"  <p><small>These strata are reported, not tested against each "
                     f"other, and no claim is made that they differ. They are grouped by "
                     f"AGE alone: neither is homogeneous in how the symptom was measured, "
                     f"and each says what it mixes. The I&sup2; column is what the trials "
                     f"actually show, and it is the only homogeneity claimed here."
                     f"</small></p>\n"
                     f"</div>\n")

    note = ""
    if res.get("subgroup_note"):
        note = f"  <p><small>{p(res['subgroup_note'])}</small></p>\n"

    return f"""<section>
<h2>{p(outcome['name'])}</h2>
{headline}
<div class="card">
  <h3>Contributing trials</h3>
  <table>
    <tr><th>Trial</th><th>Analysed<br><small>treatment / control</small></th>
        <th>{e(outcome['measure'])} (95% CI), or events</th>
        <th>Source of this cell</th></tr>
{rows}  </table>
  <p><small>{p(outcome['definition_note'])}</small></p>
</div>
{subgroups}{note}</section>
"""


def _page(canon, sections, p, e):
    """The page shell: everything that is not outcome-specific.

    Split out when the object went from one outcome to four. The removal
    disclosure and the source registry describe the OBJECT, not a symptom, so
    repeating them under each outcome would have said the same thing four times
    and implied four different reductions.
    """
    srcs = canon["sources"]
    rm = canon.get("removed_citations")
    n_out = len(canon["results"]["by_outcome"])

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
Outcomes reported: {fmt(n_out)}.
{p(canon.get('completeness_statement', ''))}</div>

<h1>{p(canon['title'])}</h1>
<p>{p(canon['question'])}</p>

{sections}
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
