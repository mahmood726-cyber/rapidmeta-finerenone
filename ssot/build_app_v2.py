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
    # The INDEX is kept, not just the record: a per-trial note that references
    # {self.…} needs a scope path, and only the index can build one.
    per_trial = {r["trial_id"]: (j, r)
                 for j, r in enumerate(res.get("per_trial") or [])}
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
            an = d.get("analysed") or {}
            size = (f"{fmt(an.get('treatment'))} / {fmt(an.get('control'))}")
            if an and an.get("treatment") is None:
                # Some trials publish only one side of the contrast at the level
                # the row describes. Printing "not stated / 2974" beside a scope
                # note is honest; printing a number the source never split is not.
                size = "<br>".join(f"{e(k.replace('_', ' '))}: {fmt(v)}"
                                   for k, v in an.items())
            if d.get("analysed_scope"):
                size += f"<br><small><em>{p(d['analysed_scope'], scope)}</em></small>"
            est = (f"{fmt(eff['point'])} "
                   f"({fmt(eff['ci_low'])} to {fmt(eff['ci_high'])})")
            if eff.get("ci_level") and eff["ci_level"] != 95:
                # A 97.5 per cent interval printed without its level reads as a
                # 95 per cent one, which is a narrower claim than the trial made.
                est += f"<br><small>{fmt(eff['ci_level'])}% interval</small>"
            if eff.get("published_ve_percent") is not None:
                est += (f"<br><small>published vaccine efficacy "
                        f"{fmt(eff['published_ve_percent'])}% "
                        f"({fmt(eff['published_ve_ci_low_percent'])} to "
                        f"{fmt(eff['published_ve_ci_high_percent'])})</small>")
            if eff.get("log_point") is not None:
                est += (f"<br><small>on the log scale: {fmt(eff['log_point'])} "
                        f"(standard error {fmt(eff['log_se'])})</small>")
            if d.get("regimen"):
                est += f"<br><small>regimen: {p(d['regimen'], scope)}</small>"
            if d.get("follow_up_note"):
                # Where two cohorts in one pool do not share a follow-up window,
                # the difference belongs beside each estimate rather than only in
                # the outcome's prose, because the row is what a reader compares.
                est += (f"<br><small><em>{p(d['follow_up_note'], scope)}"
                        f"</em></small>")
        else:
            # 2x2 count form. The generator does NOT compute a per-trial effect
            # from these: deriving a number at a surface is exactly what this
            # architecture forbids. The counts are shown; the pooled estimate
            # below is the only effect this object holds.
            tx, ct = d.get("treatment") or {}, d.get("control") or {}
            size = f"{fmt(tx.get('n'))} / {fmt(ct.get('n'))}"
            j, pt = per_trial.get(t["id"], (None, None))
            pt_scope = f"results.by_outcome.{oid}.per_trial[{j}]" if pt else None
            if pt and pt.get("point") is None:
                # A row that deliberately carries no estimate shows why, not a
                # blank where a number would go. It also still shows the
                # reference figure it holds: dropping that made the page say
                # nothing about a vaccine the object has a published efficacy
                # for, while the reading note promised one beside every row.
                est = (f"{fmt(tx.get('events'))} / {fmt(ct.get('events'))} events"
                       f"<br><small>no ratio computed &mdash; "
                       f"{p(pt.get('not_computed_reason',''), pt_scope)}</small>")
                if pt.get("reference_efficacy_percent") is not None:
                    est += (f"<br><small>reference review reports "
                            f"{fmt(pt['reference_efficacy_percent'])}% efficacy "
                            f"({fmt(pt['reference_ci_low_percent'])} to "
                            f"{fmt(pt['reference_ci_high_percent'])})</small>")
            elif pt:
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
            # Why this row's number is not the review's number, ON the row. The
            # object held both of these and the page rendered neither, while the
            # rendered reading note told the reader "the row says so". It now
            # does. Same rule the subgroup block below is written under.
            for k in ("estimand_difference", "source_divergence"):
                if pt and pt.get(k):
                    est += f"<br><small><em>{p(pt[k], pt_scope)}</em></small>"
        rows += (
            f"    <tr><td>{p(t['name'])}<br><small>{e(t['nct'])} &middot; "
            f"{e(d.get('outcome_role_in_trial', 'primary'))} outcome</small></td>"
            f"<td class='num'>{size}</td>"
            f"<td class='num'>{est}</td>"
            f"<td><small>{p(srcs[d['provenance']['source_id']]['layer'])}: "
            f"{p(d['provenance'].get('source_outcome_title', d['provenance'].get('source', '')), scope)}"
            + ("".join(f"<br><q>{e(q)}</q>"
                       for q in (d['provenance'].get('source_quotes') or []))
               if not d['provenance'].get('source') else "")
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
            + ((f"  <p class='num'>Vaccine efficacy "
                f"{fmt(pooled['pooled_ve_percent'])}% "
                f"({fmt(pooled['pooled_ve_ci_low_percent'])} to "
                f"{fmt(pooled['pooled_ve_ci_high_percent'])})</p>" + NL)
               if pooled.get("pooled_ve_percent") is not None else "")
            + f"  <p><small>&tau;&sup2; {fmt(het.get('tau2'))} &middot; I&sup2; "
              f"{fmt(het.get('i2'))}% &middot; Q {fmt(het.get('q'))} on "
              f"{fmt(het.get('df'))} df</small></p>" + NL
            + ((f"  <p><small>{p(res['heterogeneity_status'])}</small></p>" + NL)
               if res.get("heterogeneity_status") else "")
            + ((f"  <p><strong>How to read this:</strong> "
                f"{p(res['interpretation_caveat'])}</p>" + NL)
               if res.get("interpretation_caveat") else "")
            # What the pool holds constant and what it crosses, as a table a
            # reader can check. Held in the object and rendered nowhere, it
            # could not be disagreed with.
            + ((("  <h3>What this pool holds constant</h3>" + NL + "  <table>" + NL
                 + "    <tr><th>Dimension</th><th>Across the pooled cohorts</th>"
                   "<th>If it differs, why it is crossed anyway</th></tr>" + NL
                 + "".join(
                     f"    <tr><td>{e(k.replace('_', ' '))}</td>"
                     f"<td>{e(v[0])}</td><td><small>{p(v[1]) if v[1] else '&mdash;'}"
                     f"</small></td></tr>" + NL
                     for k, v in res["pool_uniformity"].items())
                 + "  </table>" + NL))
               if res.get("pool_uniformity") else "")
            + "</div>" + NL)
    else:
        # No headline number, deliberately. This object declines to combine
        # these trials, so there is nothing to put here, and inventing one is
        # exactly the defect the reshape removed.
        # k=1 and "k>=2 but declining to pool" are different states and were not
        # distinguished here: a single-cohort outcome has no pooled estimate
        # because there is nothing to combine, and it still has a NUMBER, which
        # this branch used to swallow entirely. An outcome whose only estimate is
        # one trial's must show that estimate, not an empty explanation.
        only = (res.get("per_trial") or [None])[0]
        if res.get("k") == 1 and only:
            headline = (
                "<div class='card warn'>" + NL
                + "  <h2>Single cohort &mdash; no synthesis</h2>" + NL
                + f"  <p class='num'>{e(only['measure'])} {fmt(only['point'])} "
                  f"({fmt(only['ci_low'])} to {fmt(only['ci_high'])})"
                + (f", {fmt(only['ci_level'])}% interval"
                   if only.get("ci_level") and only["ci_level"] != 95 else "")
                + "</p>" + NL
                + ((f"  <p class='num'>Vaccine efficacy "
                    f"{fmt(only['published_ve_percent'])}% "
                    f"({fmt(only['published_ve_ci_low_percent'])} to "
                    f"{fmt(only['published_ve_ci_high_percent'])})</p>" + NL)
                   if only.get("published_ve_percent") is not None else "")
                + f"  <p>{p(res.get('poolable_reason', ''))}</p>" + NL
                + "</div>" + NL)
        else:
            headline = (
                "<div class='card warn'>" + NL + "  <h2>No combined estimate</h2>" + NL
                + f"  <p>{p(res.get('not_poolable_reason', res.get('poolable_reason', '')))}</p>" + NL
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
            f"<td class='num'>{e(sg.get('measure', outcome['measure']))} "
            f"{fmt(sg['point'])} "
            f"({fmt(sg['ci_low'])} to {fmt(sg['ci_high'])})"
            + (f"<br><small>efficacy {fmt(sg['ve_percent'])}%</small>"
               if sg.get("ve_percent") is not None else "")
            + "</td>"
            f"<td class='num'>{fmt(sg.get('i2'))}%</td>"
            # What each stratum MIXES, beside its own estimate. The object held
            # this and the page showed none of it, so the one thing a reader
            # most needs in order to discount the number was unreadable.
            f"<td><small><strong>{e(sg.get('composition', ''))}</strong><br>"
            f"{p(sg.get('note', ''))}</small></td></tr>\n"
            for sg in res["subgroups"])
        # The heading and the footnote below describe WHAT the split is. They
        # were written for a split by age and hard-coded, so an object that
        # stratifies by anything else would have had its strata announced as
        # age groups. The object says what its strata are; the default is the
        # wording the first object to carry strata already ships.
        sg_head = res.get("subgroup_heading", "By age stratum")
        sg_foot = res.get("subgroup_footnote")
        subgroups = (f"<div class='card'>\n  <h2>{e(sg_head)}</h2>\n  <table>\n"
                     f"    <tr><th>Stratum</th><th>Trials</th>"
                     f"<th>{e(outcome['measure'])} (95% CI)</th><th>I&sup2;</th>"
                     f"<th>What this stratum mixes</th></tr>\n{srows}  </table>\n"
                     + (f"  <p><small>{p(sg_foot)}</small></p>\n" if sg_foot else
                        f"  <p><small>These strata are reported, not tested against each "
                        f"other, and no claim is made that they differ. They are grouped by "
                        f"AGE alone: neither is homogeneous in how the symptom was measured, "
                        f"and each says what it mixes. The I&sup2; column is what the trials "
                        f"actually show, and it is the only homogeneity claimed here."
                        f"</small></p>\n")
                     + f"</div>\n")

    # The methods rule that governs THIS outcome's combine-or-not decision, on
    # the outcome itself. Held only in a registry at the foot of the page, a
    # reader would have to go looking for the authority behind the number in
    # front of them.
    hb = ""
    if res.get("handbook"):
        h = res["handbook"]
        hb = (f"<div class='card'>\n  <h3>The methods rule governing this "
              f"decision</h3>\n"
              f"  <p><strong>Decision:</strong> {p(h['decision'])}</p>\n"
              f"  <p><strong>Cochrane Handbook sections:</strong> "
              f"{e(', '.join(str(x) for x in h['sections']))}</p>\n"
              f"  <p>{p(h['conformance'])}</p>\n"
              + ((f"  <p><small><strong>An objection raised repeatedly in "
                  f"review, and why it is not upheld:</strong> "
                  f"{p(h['recurring_objection_and_why_it_is_not_upheld'])}"
                  f"</small></p>\n")
                 if h.get("recurring_objection_and_why_it_is_not_upheld") else "")
              + "</div>\n")

    # A pooled result has to be shown robust to the decision that produced it,
    # and the decision worth testing here is the one review challenged. Held in
    # the object and rendered nowhere, the test would prove nothing to a reader.
    sens = ""
    if res.get("sensitivity"):
        s = res["sensitivity"]
        srows = "".join(
            f"    <tr><td>{e(a['omitted'])}</td>"
            f"<td class='num'>{fmt(a['k'])}</td>"
            f"<td class='num'>{fmt(a['point'])} "
            f"({fmt(a['ci_low'])} to {fmt(a['ci_high'])})</td>"
            f"<td class='num'>{fmt(a['ve_percent'])}%</td></tr>\n"
            for a in s["analyses"])
        sens = (f"<div class='card'>\n  <h3>Leave-one-out sensitivity</h3>\n"
                f"  <p>{p(s['decision_under_test'])}</p>\n  <table>\n"
                f"    <tr><th>Cohort omitted</th><th>k</th>"
                f"<th>{e(outcome['measure'])} (95% CI)</th>"
                f"<th>Efficacy</th></tr>\n{srows}  </table>\n"
                f"  <p><strong>{p(s['conclusion'])}</strong></p>\n"
                f"  <p><small>{p(s['authority'])}</small></p>\n</div>\n")

    # Where the two judging families disagreed about whether a figure should be
    # published at all, the disagreement is shown rather than resolved silently
    # in favour of the side that lets the figure stand.
    dissent = ""
    if res.get("gate_dissent"):
        gd = res["gate_dissent"]
        dissent = (
            f"<div class='card warn'>\n  <h3>The two review families disagreed "
            f"about this figure</h3>\n  <p><strong>{p(gd['question'])}</strong></p>\n"
            f"  <ul>\n"
            f"    <li><strong>One family:</strong> {p(gd['openai_family_position'])}"
            f"</li>\n"
            f"    <li><strong>The other:</strong> {p(gd['google_family_position'])}"
            f"</li>\n  </ul>\n"
            f"  <p>{p(gd['resolution'])}</p>\n"
            + (f"  <p><small>Settled against: {p(gd['authority'])}</small></p>\n"
               if gd.get("authority") else "")
            + "</div>\n")

    note = ""
    if res.get("subgroup_note"):
        note = f"  <p><small>{p(res['subgroup_note'])}</small></p>\n"

    # WHAT WAS MEASURED, above the number. An object whose whole point is that a
    # ratio is meaningless until its estimand is named cannot leave the estimand
    # in the object and off the page.
    estimand = ""
    est_blk = outcome.get("estimand")
    if est_blk:
        fu = est_blk.get("follow_up_months")
        # DATA-DRIVEN. This block named vaccine, regimen and comparator
        # explicitly, which made the shared generator refuse any object that is
        # not about a vaccine. What belongs on the page is whatever the estimand
        # and the outcome actually carry, so the rows are built from the keys
        # that are there.
        def row(label, value, extra=""):
            return (f"    <tr><th>{e(label)}</th><td>{value}{extra}</td></tr>"
                    + NL) if value else ""

        if outcome.get("vaccine"):
            # The shape the first objects to carry an estimand use. Kept
            # byte-for-byte so their pages do not move under a change made for
            # a different object.
            outcome_rows = (
                row("Vaccine", p(outcome["vaccine"]))
                + row("Regimen", p(outcome["regimen"]))
                + row("Comparator", f"{p(outcome['comparator'])} "
                                    f"({e(outcome['comparator_type'])})"))
        else:
            outcome_rows = "".join(
                row(k.replace("_", " ").capitalize(), p(outcome[k]))
                for k in ("intervention", "comparator", "comparator_kind",
                          "population")
                if outcome.get(k))
        estimand = (
            "<div class='card'>" + NL + "  <h3>What was measured</h3>" + NL
            + "  <table>" + NL
            + outcome_rows
            + row("Estimand", f"{e(est_blk['family'])} &mdash; "
                              f"{p(est_blk['model'])}")
            + "".join(row(k.replace("_", " ").capitalize(), p(est_blk[k]))
                      for k in ("unit_of_analysis", "case_definition")
                      if est_blk.get(k))
            + row("Window", p(est_blk["window"]) if est_blk.get("window") else "",
                  f" &mdash; about {fmt(fu)} months" if fu else "")
            + row("Analysis population",
                  p(est_blk["analysis_population"])
                  if est_blk.get("analysis_population") else "")
            + row("Effect scale", f"pooled on the "
                                  f"{e(outcome.get('effect_scale', 'natural'))} "
                                  f"scale")
            + "  </table>" + NL + "</div>" + NL)

    return f"""<section>
<h2>{p(outcome['name'])}</h2>
{estimand}{headline}
<div class="card">
  <h3>Contributing trials</h3>
  <table>
    <tr><th>Trial</th><th>Analysed<br><small>treatment / control</small></th>
        <th>{e(outcome['measure'])} (95% CI), or events</th>
        <th>Source of this cell</th></tr>
{rows}  </table>
  <p><small>{p(outcome['definition_note'])}</small></p>
</div>
{hb}{sens}{dissent}{subgroups}{note}</section>
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
    # The banner announced a reduction unconditionally. An object that removed
    # nothing would have told its reader it had been cut down to a core, which
    # is a false disclosure rather than a cautious one.
    banner = ("NOT SUBMISSION-READY &mdash; rebuilt on a sourceable core."
              if canon.get("build_mode") != "full" else
              "NOT SUBMISSION-READY &mdash; full build; every cohort cited is "
              "reported.")

    removal = ""
    if rm:
        cats = "".join(
            f"    <li><strong>{p(c['reason'])}</strong> &mdash; {fmt(c['count'])}. "
            f"{p(c['detail'])}"
            + (f" <em>{e(', '.join(c['removed_ids']))}</em>" if c.get("removed_ids") else "")
            + "</li>\n" for c in rm["categories"])
        removal = (f"<div class='card warn'>\n  <h2>What was removed, and why</h2>\n"
                   f"  <p>{p(rm['disclosure_note'])}</p>\n  <ul>\n{cats}  </ul>\n</div>\n")

    # Contrasts the object holds, shows, and deliberately keeps out of every
    # pool. Holding them without rendering them would make the exclusions
    # invisible, which is the thing they exist to prevent.
    carried = ""
    if canon.get("carried_contrasts"):
        crows = "".join(
            f"    <tr><td>{p(c['label'])}<br><small>{e(c['trial_id'])}</small></td>"
            f"<td class='num'>{fmt(c['effect']['point'])} "
            f"({fmt(c['effect']['ci_low'])} to {fmt(c['effect']['ci_high'])})"
            + (f"<br><small>efficacy {fmt(c['effect']['published_ve_percent'])}%"
               f"</small>" if c["effect"].get("published_ve_percent") is not None
               else "")
            + f"</td><td><small>{p(c['excluded_from_pool_because'])}"
              f"<br><q>{e(c['source_quote'])}</q></small></td></tr>\n"
            for c in canon["carried_contrasts"])
        carried = (f"<div class='card warn'>\n  <h2>Published contrasts shown here "
                   f"but kept out of every pooled estimate</h2>\n"
                   f"  <p>Each of these is a real, published result. Not one of them "
                   f"is pooled, and the reason is on its own row. Most are here "
                   f"because two "
                   f"contrasts leaning on one control group cannot both enter one "
                   f"estimate without counting those control participants twice.</p>\n"
                   f"  <table>\n    <tr><th>Contrast</th><th>Estimate</th>"
                   f"<th>Why it is outside every pool</th></tr>\n{crows}  </table>\n"
                   f"</div>\n")

    # What the search found and did NOT keep. A completeness claim that lists
    # only survivors cannot be argued with; this lists the exclusions and their
    # reasons, so a reader can disagree with a specific decision.
    screening = ""
    sc = canon.get("screening")
    if sc:
        xs = "".join(
            f"    <li><strong>{p(x['reason'])}</strong><br>{p(x['detail'])}</li>\n"
            for x in sc.get("excluded", []))
        screening = (
            f"<div class='card'>\n  <h2>What the search found, and what was kept</h2>\n"
            f"  <p>{p(sc['search_note'])}</p>\n"
            f"  <p><strong>Eligible:</strong> {p(sc['eligibility'])}</p>\n"
            f"  <h3>Excluded, with reasons</h3>\n  <ul>\n{xs}  </ul>\n"
            f"  <p><small>{p(sc['known_limitation'])}</small></p>\n</div>\n")

    # The comparison against the published synthesis of the same literature.
    recon = ""
    r = canon.get("reconciliation")
    if r:
        def block(title, items, keys):
            if not items:
                return ""
            lis = "".join(
                "    <li>" + "".join(
                    f"<strong>{p(it[k])}</strong> " if k == keys[0]
                    else f"<br>{p(it[k])}" for k in keys if it.get(k))
                + "</li>\n" for it in items)
            return f"  <h3>{e(title)}</h3>\n  <ul>\n{lis}  </ul>\n"
        recon = (
            "<div class='card'>\n  <h2>Reconciliation against the published "
            "synthesis of the same literature</h2>\n"
            f"  <p>{p(srcs[r['target_source_id']]['name'])}</p>\n"
            f"  <p class='warn'><small>{p(r['access_limitation'])}</small></p>\n"
            + block("What matches", r.get("matches"), ["item", "detail"])
            + block("What this object corrects", r.get("corrections"),
                    ["item", "review_reports", "this_object"])
            + block("What could not be resolved", r.get("unresolved"),
                    ["item", "detail"])
            + "</div>\n")

    # The methods authority every combine-or-not decision was referred to, with
    # what each cited section settled. Rendered because a decision sourced to a
    # section a reader cannot see is an appeal to authority rather than a
    # citation.
    authority = ""
    ma = canon.get("methodological_authority")
    if ma:
        arows = "".join(
            f"    <tr><td class='num'>{e(s['section'])}</td>"
            f"<td>{p(s['title'])}</td><td><small>{p(s['used_for'])}</small></td></tr>\n"
            for s in ma["sections_relied_on"])
        authority = (
            f"<div class='card'>\n  <h2>The methods authority these decisions rest "
            f"on</h2>\n  <p>{p(ma['reference'])}<br><small>{e(ma['url'])}</small></p>\n"
            f"  <p>{p(ma['note'])}</p>\n  <table>\n"
            f"    <tr><th>Section</th><th>Title</th><th>What it settled here</th>"
            f"</tr>\n{arows}  </table>\n</div>\n")

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

<div class="badge" role="status">{banner}
Outcomes reported: {fmt(n_out)}.
{p(canon.get('completeness_statement', ''))}</div>

<h1>{p(canon['title'])}</h1>
<p>{p(canon['question'])}</p>

{sections}
{screening}{carried}{recon}{authority}{removal}
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
