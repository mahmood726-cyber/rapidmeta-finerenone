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

# ONE MAP FOR EVERY SPELLING OF A CONCEPT. Without this import `_aliases` is undefined and the
# builder dies on the first page with a withdrawn estimate -- which it did, four times, because
# the insert that was supposed to add this line was guarded by `if "field_aliases" not in src`
# and the string was already present IN THE COMMENT BELOW explaining the map.
import field_aliases as _aliases  # noqa: E402

NL = chr(10)

REF_RE = re.compile(r"\{([a-z0-9_]+(?:\.[a-z0-9_]+|\[\d+\])*)\}", re.I)
ALIASES = {"res": "results", "cfg": "config", "rm": "removed_citations",
           "t": "inputs.trials[0]"}



_NOT_RECORDED_PREFIXES = ("not recorded", "not available", "not stated", "no record",
                          "not established", "not captured")


def _recorded(v):
    """False for None, blank, and any string that opens with an absence marker."""
    if v is None:
        return False
    s = str(v).strip()
    return bool(s) and not any(s.lower().startswith(x) for x in _NOT_RECORDED_PREFIXES)


def _finding_block(res, key, role, p, nl):
    """Render a narrative finding on an estimate -- EVERY field the object holds.

    WHY THIS ITERATES INSTEAD OF NAMING FIELDS
        The version this replaces read eight named keys out of the object. A
        ninth field added to the object rendered nowhere, silently, and looked
        exactly like a field nobody had written. That is the artefact-versus-
        object defect turned inside out: the finding was in the source of truth
        and the projector dropped it.

        Iterating the object's own keys makes the drop UNREPRESENTABLE rather
        than merely unlikely. The object's key order is the reading order, which
        also means the order is edited where the content is edited.

    WHAT IS DELIBERATELY NOT RENDERED
        Keys beginning with an underscore. They are notes to whoever edits the
        object -- provenance for the editing decision, not content for a reader.
    """
    blk = res.get(key)
    if not isinstance(blk, dict):
        return ""
    fields = [(k, v) for k, v in blk.items()
              if not k.startswith("_") and isinstance(v, str) and v.strip()]
    if not fields:
        return ""
    out = ["  <div class='absent-state' role='%s'>" % role]
    for i, (k, v) in enumerate(fields):
        # The first field is the headline and carries the emphasis. Every other
        # field is its own paragraph, so a long finding stays readable and no
        # sentence is glued to an unrelated one.
        out.append("<p><strong>%s</strong></p>" % p(v) if i == 0
                   else "<p>%s</p>" % p(v))
    out.append("</div>")
    return "".join(out) + nl


def _house_rule_table(res, p, e):
    """The k<=3 sensitivity interval, for objects that hold ONE rather than a full grid.

    THE DECISION WAS TAKEN AND THE REMEDY STOPPED AT THE PROJECTION LAYER.
    `DECISIONS-COCHRANE-2026-08-18.md` settled it against Handbook 10.10.4.4-10.10.4.5 --
    *"When there are only two or three studies, we advise review authors to undertake a
    sensitivity analysis to compare results from the different methods"* -- and concluded
    that HKSJ is NOT the primary interval but is REPORTED as a sensitivity analysis at
    k <= 3, because the Handbook's remedy is to SHOW BOTH rather than to pick one.

    Nineteen pooled outcomes carry the resulting `house_rule_interval_*` block. EIGHT of
    them also carry a full `between_study_variance_method_comparison`, and only those eight
    reached a page: `_method_table` renders that grid and nothing renders this block. So on
    ELEVEN outcomes the analysis exists on the object, was correctly computed, and no
    reader can see it -- including `finerenone-cv` and `sglt2-hf`.

        A REMEDY THAT STOPS AT THE PROJECTION LAYER IS INVISIBLE FROM BOTH ENDS: the
        object holds it, so an object audit passes; the page lacks it, so a reader never
        sees it; and nothing compares the two.

    This renders the two intervals the object actually holds, each with its estimator
    named, and states that the POINT ESTIMATE IS UNCHANGED -- which is the whole finding.
    What differs between them is the precision claim, and on fifteen of the nineteen the
    published interval excludes the null while this one does not.
    """
    hr = next((res[k] for k in res if k.startswith("house_rule_interval")), None)
    if not isinstance(hr, dict) or hr.get("ci_low") is None:
        return ""
    pub = hr.get("published_interval") or {}

    def n4(x):
        # `fmt` does not round -- every other table feeds it values the object already
        # rounded at storage. `published_interval` does not: finerenone-cv holds
        # 0.7876670478566473, which `fmt` would print in full at a reader beside
        # 0.4699 and 1.594. Sixteen significant figures on a two-study pool is a
        # precision claim nothing supports. Rounded to the corpus's own 4 dp.
        if x is None:
            return "not stated"
        if isinstance(x, (int, float)):
            return ("%.4f" % float(x)).rstrip("0").rstrip(".")
        return str(x)
    rows = ""
    for label, est, lo, hi in (
            ("as published", pub.get("estimator") or "as stored",
             pub.get("ci_low"), pub.get("ci_high")),
            ("sensitivity (Handbook 10.10.4.5)", hr.get("estimator") or "Hartung-Knapp",
             hr.get("ci_low"), hr.get("ci_high"))):
        if lo is None or hi is None:
            continue
        rows += ("    <tr><td>%s</td><td>%s</td><td class='num'>%s (%s to %s)</td></tr>%s"
                 % (e(label), p(est), n4(hr.get("point")), n4(lo), n4(hi), NL))
    if not rows:
        return ""
    note = hr.get("THE_POINT_ESTIMATE_IS_UNCHANGED") or ""
    floor = hr.get("variance_inflation_floor") or ""
    return ("  <h3>Does the answer depend on the pooling method?</h3>" + NL
            + "  <p>With two or three studies the Cochrane Handbook (10.10.4.4&ndash;"
              "10.10.4.5) asks for a sensitivity analysis comparing interval methods "
              "rather than a choice between them. Both are given here; the published "
              "interval is the first row.</p>" + NL
            + "  <table>" + NL
            + "    <tr><th>Interval</th><th>Method</th><th>Summary (95% CI)</th></tr>" + NL
            + rows + "  </table>" + NL
            + ("  <p><small>%s</small></p>%s" % (p(note), NL) if note else "")
            + ("  <p><small>%s</small></p>%s" % (p(floor), NL) if floor else ""))


def _method_table(sens, p, e, pooled=None):
    """Render the between-study-variance method comparison, if the object has one.

    Handbook 10.10.4.5 asks for this comparison whenever a random-effects pool
    has only two or three studies, and every pool in this batch does. Computed
    and stored but not shown, it would satisfy the letter of that advice and
    none of its purpose -- the point is that a READER sees whether the answer
    depends on the method.
    """
    mc = sens.get("between_study_variance_method_comparison")
    if not mc:
        return ""
    # The object stores the estimators by their conventional abbreviations,
    # which are what a methods reader looks for. A page has readers who are not
    # methods readers, so both are shown rather than either alone.
    LONG = {"DL": "DerSimonian-Laird (DL)", "PM": "Paule-Mandel (PM)",
            "REML": "restricted maximum likelihood (REML)"}
    LONG_INT = {"Wald": "ordinary (Wald)",
                "HKSJ": "Hartung-Knapp-Sidik-Jonkman (HKSJ)"}
    rows = "".join(
        f"    <tr><td>{e(LONG.get(m['between_study_variance_estimator'], m['between_study_variance_estimator']))}</td>"
        f"<td>{e(LONG_INT.get(m['interval_method'], m['interval_method']))}</td>"
        f"<td class='num'>{fmt(m['point'])} "
        f"({fmt(m['ci_low'])} to {fmt(m['ci_high'])})</td>"
        f"<td class='num'>{fmt(m['tau2'])}</td></tr>" + NL
        for m in mc["methods"])
    # A WITHDRAWN POOL'S METHOD COMPARISON MUST SAY SO, IN THE TABLE.
    #
    # After SGLT2_HF's four-trial estimate was withdrawn, the headline card said
    # so and THIS table went on printing the withdrawn value under four
    # estimators -- four more occurrences of a number no longer claimed, laid out
    # as a methods result. The withdrawal is about the ESTIMAND, so no estimator
    # rescues it, and a reader scrolling to this table would find the value alive
    # and well four screens below the notice retiring it.
    _wd = ""
    if isinstance(pooled, dict) and pooled.get("withdrawn"):
        _wd = ("  <div class='absent-state' role='note'><strong>These are the "
               "WITHDRAWN pool's values.</strong> The estimate below is retired: "
               "the trials do not share one endpoint. The comparison is kept "
               "because it answers a real question -- whether the arithmetic "
               "depended on the estimator, and it did not -- and it does not "
               "rescue the pool, because the objection is to the ESTIMAND and no "
               "choice of between-study variance touches that.</div>" + NL)
    return (f"  <h3>Does the answer depend on the pooling method?</h3>" + NL
            + _wd
            + f"  <p>{p(mc['why'])}</p>" + NL + "  <table>" + NL
            + "    <tr><th>Between-study variance</th><th>Interval</th>"
              "<th>Summary (95% CI)</th><th>&tau;&sup2;</th></tr>" + NL
            + rows + "  </table>" + NL
            + f"  <p><strong>{p(mc['verdict'])}</strong></p>" + NL
            + f"  <p><small>{p(mc['estimator_kept'])}</small></p>" + NL)



def _benchmark_trial_count(b):
    """How many trials a published benchmark pooled, or an honest blank.

    An explicit count wins over a list length, because an object may know the
    number without being able to name the members -- one synthesis here states
    its trial count and patient total and names none of its trials, so its list
    is INFERRED and its count is read. Where neither is present this returns
    "not stated" rather than a zero, which is the whole point: a zero is a claim.
    """
    n = b.get("trial_count")
    if isinstance(n, int) and n > 0:
        return str(n)
    trials = b.get("trials") or []
    return str(len(trials)) if trials else "not stated"


def _cell_source_link(cell, srcs, e):
    """The measured cell's source, as something a reader can actually open.

    The object carries `source_tier` and `source_url` on every measured cell and
    the page projected NEITHER: every anchor on the rendered page belonged to a
    SCREENED-OUT trial, so a reader could click through to a study the review
    excluded but not to the source of any number it reports. The object declares
    `source_links_enforced`; this is what makes that claim something a reader can
    exercise rather than something only a validator can see.
    """
    url = cell.get("source_url")
    layer = (srcs.get(cell.get("provenance", {}).get("source_id"), {})
             .get("layer", "")) or cell.get("source_tier", "")
    if not url:
        return e(layer)
    return f"<a href='{e(url)}'>{e(layer)}</a>"


def _rank_label(cell, e):
    """The contributing row's rank IN ITS OWN TRIAL, or nothing.

    Never defaults. See the comment at the call site: the default this replaces
    printed "primary outcome" on rows the object recorded as secondary.
    """
    rank = (cell.get("outcome_role_in_trial")
            or cell.get("endpoint_rank_in_its_own_trial"))
    if not str(rank or "").strip():
        return ""
    rank = str(rank).strip()
    # A stored rank that already NAMES what it is -- "…primary composite
    # endpoint", "an other-prespecified outcome…" -- is printed as it stands.
    # One that is only a rank -- "primary", "FIRST SECONDARY" -- gets the noun
    # it needs. Keying on word count instead got "FIRST SECONDARY" wrong, which
    # a fresh projection of a live object caught.
    if re.search(r"\b(outcome|endpoint)s?\b", rank, re.I):
        return " &middot; " + e(rank)
    return " &middot; " + e(f"{rank} outcome")


def _favoured_arm(res, outcome):
    """Name the favoured arm, and say which way the outcome runs.

    `favours` stores "treatment", "control" or "neither", which tells a reader
    nothing about WHICH treatment or which way better runs. The nodes are on the
    outcome; the direction of benefit is too. Spelling both out is the whole
    point, because a ratio below one on a CURE outcome means less cure, and an
    app in this corpus presented exactly that as a benefit.
    """
    f = res.get("favours")
    tx = outcome.get("treatment_node") or "the intervention"
    ct = outcome.get("comparator_node") or "the comparator"
    # POLARITY IS DERIVED, NEVER DEFAULTED. The previous line tested
    # `== "higher"` and sent EVERYTHING else to "lower is better" -- so an
    # outcome storing the full phrase "higher is better" rendered as its own
    # opposite (KCCQ 0-100, pooled MD +7.43, labelled "lower is better"), and
    # 21 outcomes recording that the direction was NOT KNOWN rendered as a
    # confident directional claim. A default is an assertion the object never
    # made. Unknown polarity must REFUSE, not pick the common case.
    _POLARITY = {"higher": "higher is better",
                 "higher is better": "higher is better",
                 "lower": "lower is better",
                 "lower is better": "lower is better"}
    _raw = outcome.get("direction_of_benefit")
    way = _POLARITY.get(str(_raw).strip().lower()) if _raw is not None else None
    if way is None:
        way = "direction of benefit not recorded for this outcome"
    if f == "neither":
        return f"neither arm; the interval spans the null ({way})"
    if f == "treatment":
        return f"{tx} ({way})"
    if f == "control":
        return f"{ct} ({way})"
    return str(f)


def fmt(x):
    if x is None:
        return "not stated"
    if isinstance(x, float) and x == int(x):
        return str(int(x))
    return str(x)


def _interval(eff, p=lambda s: s):
    """Render a point with its interval, or a point that HAS no interval.

    A boundary estimate sits where the log scale ends, so it carries a point
    and no bounds. Feeding those bounds through fmt() printed the literal
    phrase 'not stated to not stated' at the reader, which reads as missing
    data rather than as a value that cannot have an interval. Where the object
    explains the absence, the page shows the explanation instead.
    """
    lo, hi = eff.get("ci_low"), eff.get("ci_high")
    if eff.get("point") is None:
        # Some outcomes carry counts and NO effect at all, because the source
        # published none and none is derivable. Showing "not stated" where a
        # value would go reads as missing data; the reason reads as what it is.
        why = eff.get("effect_absent_because") or eff.get("not_computed_reason")
        return (f"<small>{p(why)}</small>" if why
                else "<small>no estimate is stored for this row</small>")
    if lo is None and hi is None:
        why = (eff.get("not_log_transformable_because")
               or eff.get("interval_absent_reason"))
        return (f"{fmt(eff['point'])}"
                + (f" <small>&mdash; no interval: {p(why)}</small>" if why
                   else ""))
    return f"{fmt(eff['point'])} ({fmt(lo)} to {fmt(hi)})"


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
    """Resolve references, bounded so a cycle fails loudly.

    A NULL FIELD IS AN ABSENCE, NOT A TYPE ERROR. `p(x)` is called on optional fields all
    over this renderer, and `REF_RE.sub` on None raises `expected string or bytes-like
    object` from inside `re` -- a message that names neither the object nor the field. The
    display for an absent value is an em dash, the same as every other empty cell here.
    """
    if s is None:
        return "—"
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
    # AN ABSENT VALUE RENDERS AS AN EM DASH, NOT AS AttributeError.
    #
    # `html.escape(None)` raises inside the standard library, so the traceback names
    # `s.replace` in `html/__init__.py` and neither the object, the outcome nor the field.
    # Four separate call sites hit it on this corpus-wide rebuild -- `pooled['measure']`,
    # `outcome['measure']`, and two more behind them -- and patching them one at a time is
    # how you spend a night on the fourth. A field the object does not hold is an ABSENCE,
    # and the display for an absence is a dash.
    #
    # NOT A PLACEHOLDER LEAK. This never emits the token `None`; the house lint that blocks
    # a bare `None` reaching a page is unaffected, and an em dash is what every other absent
    # cell in these tables already shows.
    def e(x):
        return html.escape("—" if x is None else str(x))
    def p(s, scope=None):
        return e(render(canon, s, scope))

    sections = "".join(_outcome_section(canon, oid, p, e)
                       for oid in canon["results"]["by_outcome"])
    return _page(canon, sections, p, e)


def _verdict_scope(res, pooled, canon):
    """`what_this_verdict_does_not_establish`, wherever this corpus puts it.

    Three levels hold it across the corpus -- the outcome block, the pooled block and the
    object root -- so all three are read. Reading one of three is exactly how seventeen
    pages printed "No reason recorded." over a reason they held.
    """
    k = "what_this_verdict_does_not_establish"
    for src in (res, pooled, canon):
        if isinstance(src, dict) and src.get(k):
            return src[k]
    return None


def _previous_values_text(pooled):
    """What this withdrawal supersedes, from either recorded shape.

    ABLATION_AF records {"card": "...", "page": "..."} -- the two SURFACES that
    disagreed. SGLT2_HF records a LIST of the superseded pooled objects, which is
    the shape that keeps the actual numbers. Both are real and both must render;
    the previous code understood one and printed "n/a" for the other, which is a
    withdrawal notice withholding the value it withdraws.
    """
    pv = pooled.get("previous_values")
    if isinstance(pv, dict):
        parts = ["%s: %s" % (k, v) for k, v in pv.items() if v]
        return html.escape("; ".join(parts)) if parts else html.escape(json.dumps(pv))
    if isinstance(pv, list):
        out = []
        for v in pv:
            if isinstance(v, dict) and v.get("point") is not None:
                out.append("%s %s (%s to %s)"
                           % (v.get("measure", ""), fmt(v.get("point")),
                              fmt(v.get("ci_low")), fmt(v.get("ci_high"))))
            else:
                out.append(str(v))
        return html.escape("; ".join(out))
    return html.escape(str(pv))


def _endpoint_definitions(canon, oid, p, e):
    """The registry endpoint definition for every trial that contributes, verbatim.

    See the module note at the top of this patch's history: four topics had their
    endpoint definitions read from the registry and not one page showed a reader
    one of them. A property established only in the object is a property the
    reader has to take on trust.
    """
    rows = ""
    for t in canon["inputs"]["trials"]:
        bo = (t.get("by_outcome") or {}).get(oid)
        if not bo:
            continue
        d = bo.get("outcome_definition")
        src = bo.get("outcome_definition_source") or {}
        name = t.get("name") or t.get("nct") or "?"
        reg = t.get("nct") or ""
        if not d:
            # AN ABSENT DEFINITION SAYS SO. It is not skipped: a trial silently
            # missing from this table would read as a trial with nothing to
            # declare, and the whole point of the table is that the reader can
            # see which trials were actually read.
            rows += ("    <tr><td><strong>%s</strong><br><small>%s</small></td>"
                     "<td colspan='4'><em>No endpoint definition is recorded for "
                     "this trial. Its effect was pooled without one.</em></td></tr>\n"
                     % (e(name), e(reg)))
            continue
        link = src.get("source_url") or ""
        linkhtml = ('<a href="%s" rel="noopener">%s</a>' % (e(link), e(reg or link))
                    if link else e(reg) or "—")
        # THE RANK IS THE AXIS AN UNREGISTERED ENDPOINT LIVES ON, and it was held
        # in the object and rendered nowhere. ARNI_HF pools four trials; three
        # register this composite (two as primary, one as first secondary) and
        # ANSWER-HF registers it at no rank at all, which is a stronger statement
        # than any of the others and had no column to appear in. A row whose rank
        # is an absence is marked so the reader meets it as a state and not as a
        # long sentence in a definition cell.
        rank = str(src.get("endpoint_rank") or "").strip()
        unregistered = "not registered" in rank.lower()
        rows += (
            "    <tr%s><td><strong>%s</strong><br><small>%s</small></td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n"
            % (" class='absent-state'" if unregistered else "",
               e(name), linkhtml,
               ("<strong>%s</strong>" % e(rank)) if unregistered
               else (e(rank) or "&mdash;"),
               p(d),
               p(src.get("description_verbatim") or
                 "no description is recorded in this registry field"),
               p(src.get("analysis_set_as_the_registry_states_it")
                 or src.get("time_frame") or "—")))
        if unregistered:
            rows += ("    <tr><td colspan='5' class='absent-state' role='note'>"
                     "<strong>This trial's registration declares no such endpoint.</strong> "
                     "%s</td></tr>\n"
                     % p(src.get("what_this_costs_the_pool")
                         or "The quantity pooled from this trial appears only in "
                            "its publication."))
        # A CONFLICT ABOUT A TRIAL BELONGS BESIDE THAT TRIAL. On DOAC_CANCER_VTE
        # the fact that NCT02583191 names a different study from the one whose
        # data sits on the row reached the page ONLY inside the withdrawal prose,
        # eleven lines from the table. The reader who follows the registration
        # link is looking at the ROW.
        conflict = t.get("identity_conflict")
        if conflict:
            rows += ("    <tr><td colspan='5' class='absent-state' role='note'>"
                     "<strong>Identity conflict on this row.</strong> %s</td></tr>\n"
                     % p(conflict))
    if not rows:
        return ""
    read_on = sorted({(((t.get("by_outcome") or {}).get(oid) or {})
                       .get("outcome_definition_source") or {}).get("read_utc")
                      for t in canon["inputs"]["trials"]} - {None})
    when = (" Read from the registry on %s." % e(", ".join(read_on))) if read_on else ""
    return ("""<div class="card">
  <h3>Endpoint definitions, read from the registry</h3>
  <p><small>What each trial COUNTED, in its own registry record's words, before
  anything here was pooled. A sentence saying what HAPPENED is not a sentence
  saying what was COUNTED, and only the second one licenses a pool.%s Follow the
  registration link to disagree with any row.</small></p>
  <table>
    <tr><th>Trial</th><th>Rank in its own trial</th>
        <th>Registered outcome measure</th>
        <th>Description, verbatim</th><th>Analysis set / window</th></tr>
%s  </table>
</div>
""" % (when, rows))


def _not_contributing(canon, p, e):
    """Trials on this review that contribute nothing to its pool."""
    blk = canon.get("eligible_but_not_contributing") or {}
    studies = [x for x in (blk.get("studies") or []) if isinstance(x, dict)]
    if not studies:
        return ""
    rows = ""
    for st in studies:
        link = st.get("source_url")
        reg = st.get("id") or ""
        linkhtml = ('<a href="%s" rel="noopener">%s</a>' % (e(link), e(reg))
                    if link else e(reg) or "—")
        rows += ("    <tr><td><strong>%s</strong><br><small>%s</small></td>"
                 "<td>%s</td><td>%s</td></tr>\n"
                 % (e(st.get("name") or reg or "?"), linkhtml,
                    p(st.get("why_not_contributing") or "not stated"),
                    p(st.get("what_the_registry_holds_that_the_page_does_not")
                      or st.get("registered_primary_measure") or "—")))
    return ("""<div class="card">
  <h3>Named on this review, contributing nothing to its pool</h3>
  <p><small>%s</small></p>
  <table>
    <tr><th>Trial</th><th>Why it contributes nothing</th>
        <th>What the registry holds</th></tr>
%s  </table>
</div>
""" % (p(blk.get("note") or "No reason is recorded."), rows))


def _outcome_section(canon, oid, p, e):
    # AN OUTCOME BLOCK WITH NO DECLARATION IS REFUSED BY NAME, NOT CRASHED ON.
    #
    # This was a bare `next(o for o in canon["outcomes"] if o["id"] == oid)`. On
    # `cangrelor-pci-review` the block `corrected_composite_3component` exists in
    # results.by_outcome and is declared in NO outcomes[] entry, so next() raised
    # StopIteration and THE WHOLE PAGE BUILD DIED.
    #
    # AND THE CRASH AND THE MISSING ESTIMATE ARE THE SAME DEFECT. That block holds a LIVE
    # pooled point -- 0.9646, k=2, not withdrawn -- while the topic's `primary` is
    # withdrawn. So the object publishes an estimate its own page has never shown: 0.9646
    # appears nowhere in the delivered bytes. CANGRELOR was already on the open list as one
    # of two pages serving nothing for a pooled point its object holds, and this is why.
    #
    # Corpus-wide there is exactly ONE such orphan block, this one. A refusal by name makes
    # the second one visible on the page instead of taking the build down.
    outcome = next((o for o in canon["outcomes"] if o["id"] == oid), None)
    if outcome is None:
        return ("<div class='absent-state' role='note'><strong>Not rendered.</strong> "
                "The results block <code>%s</code> is not declared in this object's "
                "<code>outcomes</code>, so there is no registered name, measure or "
                "comparator to render it under. IT IS NOT EMPTY: the block exists and may "
                "carry a pooled estimate. Declaring the outcome is a CONTENT change and is "
                "not made here.</div>" % e(oid))
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
        # A NULLED TRIAL IS NOT A CONTRIBUTING TRIAL, AND THIS TABLE IS HEADED
        # "Contributing trials". `finerenone-review` carries `NULLED:NCT01874431` and the
        # panel showed four rows under a headline stating k=3 -- CHK009_POOL_IDENTITY caught
        # it on the artefact, and a reader would have met the same contradiction on the page.
        # The entry stays on the object and its `nulled_note` says why; it is not listed here
        # as though it contributed.
        if t.get("nulled") or str(t.get("trial_id") or t.get("nct")
                                  or t.get("id") or "").startswith("NULLED:"):
            continue
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
                # The reference-review comparison is OPTIONAL. It exists only
                # where an object anchors its rows against a published
                # synthesis, and requiring it here made the shared generator
                # crash on the first count-based object that had none.
                est = (f"{e(pt['measure'])} {_interval(pt, p)}"
                       f"<br><small>{fmt(tx.get('events'))} / "
                       f"{fmt(ct.get('events'))} events")
                if pt.get("reference_efficacy_percent") is not None:
                    est += (f" &middot; reference review reports "
                            f"{fmt(pt['reference_efficacy_percent'])}% efficacy "
                            f"({fmt(pt['reference_ci_low_percent'])} to "
                            f"{fmt(pt['reference_ci_high_percent'])})")
                est += "</small>"
                if pt.get("reference_efficacy_percent") is None and pt.get("derivation"):
                    # Where there is no reference figure to anchor the row, the
                    # derivation is what tells a reader which direction is which.
                    # A generic "below one is better" is wrong whenever the
                    # outcome is a bad event rather than a good one.
                    est += f"<br><small><em>{p(pt['derivation'])}</em></small>"
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
            f"    <tr><td>{p(t.get('name') or t['label'])}<br><small>"
            # Not every registry is ClinicalTrials.gov. A trial registered
            # elsewhere has no NCT, and escaping the absent value crashed the
            # page rather than showing the identifier the trial actually has.
            f"{e(t.get('nct') or t.get('registration') or 'no registry identifier')}"
            # A DEFAULT THAT ASSERTS A FACT. This read `outcome_role_in_trial`
            # and, when absent, printed the literal string "primary" -- so every
            # contributing row of an object that stores its ranks under any other
            # name was labelled a PRIMARY OUTCOME beside its effect. A gate leg
            # found four such rows in one object: a trial's designated SECONDARY
            # endpoints and its registry-only other-prespecified endpoint, each
            # rendered "primary outcome" while the object stored the correct rank
            # three fields away. That is this batch's central defect class -- a
            # label belonging to a different analysis sitting beside a number --
            # committed by the projection rather than by the object, and it is the
            # same shape as the silent RoB coercion these apps were built to
            # replace: a default that can only ever raise the apparent standing of
            # the evidence.
            #
            # So the rank is read from either field, and when NEITHER is present
            # nothing is printed. A blank tells a reader the rank was not stated;
            # a default tells them something false.
            f"{_rank_label(d, e)}</small></td>"
            f"<td class='num'>{size}</td>"
            f"<td class='num'>{est}</td>"
            f"<td><small>{_cell_source_link(d, srcs, e)}: "
            f"{p(d['provenance'].get('source_outcome_title', d['provenance'].get('source', '')), scope)}"
            # ALWAYS print the quotation. This was conditioned on the cell NOT
            # naming a source -- so the one trial whose provenance carried a
            # named source had its quoted sentence suppressed, and it was the
            # only one of four to show no quotation on the page. An independent
            # review read that and reasonably concluded the value was
            # untraceable; the value was fine and the projector was hiding its
            # evidence. A source and a quotation are complementary: the source
            # says where to look, the quotation says what is there.
            + "".join(f"<br><q>{e(q)}</q>"
                      for q in (d['provenance'].get('source_quotes') or []))
            + (f"<br><em>{p(t['enrolment_note'], scope)}</em>"
               if t.get("enrolment_note") else "")
            + "</small></td></tr>\n")

    if pooled and pooled.get("withdrawn"):
        # A WITHDRAWN pool states its REASON, prominently, instead of rendering
        # "OR not stated (not stated to not stated)" -- which is not false and
        # tells a reader nothing. The reason is the deliverable; the withdrawal is
        # only its consequence. A reader needs to know the arithmetic was correct
        # and the POOL was never established.
        headline = (
            "<div class='card'>" + NL + "  <h2>Pooled result</h2>" + NL
            + "  <div class='absent-state' role='note'><strong>Estimate withdrawn.</strong> "
            # READ EVERY SPELLING. `withdrawn_reason` is one of three names this corpus uses
            # for the same field -- `absent_reason` on 10 objects and `withdrawn_because` on 3
            # -- and reading only the canonical one printed "No reason recorded." on 17 pages
            # that DO record a reason, several of them substantive: "0 of 4 eligible trials
            # have posted results to ClinicalTrials.gov. Two are needed before an estimate."
            #
            # A page withholding the reason an estimate was withdrawn is the single thing this
            # project exists to not do, and it was doing it silently because the reader read
            # one name. The alias map is `ssot/field_aliases.py`; per-site alternates would
            # drift, so nothing lists spellings here.
            + p(_aliases.get(pooled, "withdrawal_reason") or "No reason recorded.")
            + "</div>" + NL
            # WHAT THIS VERDICT DOES NOT ESTABLISH -- HELD ON 68 OBJECTS, RENDERED ON NONE.
            #
            # This field exists for exactly one purpose: to stop a reader taking a
            # statement about a REGISTRATION as a statement about a TRIAL. amoxicillin-aom
            # holds "THIS IS A STATEMENT ABOUT THE REGISTRATION, NOT ABOUT THE TRIAL. It
            # does NOT establish that clinical outcomes were not measured" -- and its page
            # opened with "All 2 of 2 seeded registrations register no clinical endpoint at
            # any rank", which is false of those two trials and which the guard was written
            # to prevent. A field that exists to prevent a misreading and is not projected
            # is the estimand-caveat diagnosis again, on a second field.
            #
            # EVERY OTHER GUARD HERE POINTS AT OVERCLAIMING A RESULT. This one points at
            # overclaiming a CRITICISM, which is a fabrication in the direction that reads
            # as rigour: an overstated result gets caught by a reader who knows the trial,
            # an overstated refusal does not. Being unfairly harsh is a fabrication too.
            #
            # Rendered inside the withdrawal notice, immediately after the reason, because
            # anywhere else is a place the reader has already stopped.
            + ("  <p><small><strong>What this does not establish.</strong> "
               + p(str(_verdict_scope(res, pooled, canon))) + "</small></p>" + NL
               if _verdict_scope(res, pooled, canon) else "")
            + ("  <p><small>" + p(pooled["withdrawn_note"]) + "</small></p>" + NL
               if pooled.get("withdrawn_note") else "")
            # BOTH SHAPES, AND NEVER A SILENT "n/a".
            #
            # This read previous_values as a dict of {card, page} strings and
            # printed "n/a" for anything else. Handed a LIST of superseded pooled
            # objects -- the shape that actually preserves the numbers -- it
            # raised, and before that it would have rendered "card: n/a; page:
            # n/a" for a dict without those two keys, which is a withdrawal
            # notice that withholds the very value it is withdrawing.
            + ("  <p><small>Previously displayed: " + _previous_values_text(pooled)
               + " &mdash; superseded by this withdrawal.</small></p>" + NL
               if pooled.get("previous_values") else "")
            + f"  <p>{p(outcome['name'])}. k = {fmt(res['k'])}.</p>" + NL
            # THE SPLIT POOLS ARE THE READER'S REPLACEMENT ANSWER. Withdrawing an
            # estimate and offering nothing is honest but not useful when the
            # object holds pools that ARE established; where it does, they belong
            # on the card that carries the withdrawal, not several screens away.
            + ((("  <h3>What the endpoint-identical pairs give</h3>" + NL
                 + "  <table>" + NL
                 + "    <tr><th>Pool</th><th>k</th><th>Estimate</th><th>I&sup2;</th>"
                   "</tr>" + NL
                 + "".join(
                     f"    <tr><td>{p(sp.get('label',''))}"
                     f"{('<br><small>' + p(sp['reproduced']) + '</small>') if sp.get('reproduced') else ''}"
                     f"</td><td class='num'>{fmt(sp.get('k'))}</td>"
                     f"<td class='num'>{e(str(sp.get('measure','')))} "
                     f"{fmt(sp.get('point'))} ({fmt(sp.get('ci_low'))} to "
                     f"{fmt(sp.get('ci_high'))})</td>"
                     f"<td class='num'>{fmt(sp.get('i2'))}%</td></tr>" + NL
                     for sp in pooled["split_pools"])
                 + "  </table>" + NL
                 + ((f"  <p><strong>{p(pooled['what_the_split_does_not_establish'])}"
                     f"</strong></p>" + NL)
                    if pooled.get("what_the_split_does_not_establish") else "")))
               if pooled.get("split_pools") else "")
            # AND THE POOL FINDINGS, ON THE WITHDRAWAL CARD TOO.
            #
            # The reported branch below renders POOL_FINDINGS_<stamp> beside the
            # estimate. This branch did not, so on `cangrelor-pci-review` and
            # `incretin-hfpef-review` -- whose findings sit on a WITHDRAWN
            # primary -- the qualification rendered only in the manuscript, a
            # megabyte down the page. A reader who meets "Estimate withdrawn" is
            # precisely the reader the finding was written for: on cangrelor it
            # says a published pool of the same three trials reports 0.81 where
            # this object does not pool at all.
            + "".join(_finding_block(res, k, "alert", p, NL)
                      for k in sorted(res) if k.startswith("POOL_FINDINGS_"))
            + "</div>" + NL)
    # A `pooled` DICT OF NULLS IS TRUTHY AND IS NOT A POOLED RESULT.
    #
    # 15 topics store `pooled` with every field null -- measure, point, ci_low, ci_high all
    # None -- to record that the outcome exists and was not pooled. `elif pooled:` accepted
    # it, and `html.escape(None)` then raised AttributeError with no mention of which object
    # or which field. Each of those 15 pages had not been rebuilt since the state arose, so
    # nothing had reached the line; the corpus-wide rebuild was the first thing to.
    elif pooled and pooled.get("point") is not None:
        # A POOL THAT STANDS SAYS WHY, WITH THE SAME PROMINENCE AS ONE THAT DOES
        # NOT. The withdrawal branch above renders its reason first and states
        # that "the reason is the deliverable". Nothing rendered the symmetric
        # thing, so this projector showed a reader why an estimate was RETRACTED
        # and never why one was KEPT -- and after three consecutive withdrawals
        # that asymmetry is not neutral: it makes destruction legible and
        # verification invisible.
        _stands = pooled.get("stands_because")
        _cav = pooled.get("caveats")
        headline = (
            "<div class='card'>" + NL + "  <h2>Pooled result</h2>" + NL
            + f"  <p class='num'>{e(pooled.get('measure'))} {fmt(pooled['point'])} "
              f"({fmt(pooled['ci_low'])} to {fmt(pooled['ci_high'])}), "
              f"{fmt(pooled['ci_level'])}% interval</p>" + NL
            + f"  <p>{p(outcome['name'])}. {p(res.get('model'))}, estimator "
              f"{p(res.get('estimator_used'))}, k = {fmt(res['k'])}.</p>" + NL
            + ((f"  <p class='num'>Vaccine efficacy "
                f"{fmt(pooled['pooled_ve_percent'])}% "
                f"({fmt(pooled['pooled_ve_ci_low_percent'])} to "
                f"{fmt(pooled['pooled_ve_ci_high_percent'])})</p>" + NL)
               if pooled.get("pooled_ve_percent") is not None else "")
            + f"  <p><small>&tau;&sup2; {fmt(het.get('tau2'))} &middot; I&sup2; "
              f"{fmt(het.get('i2'))}% &middot; Q {fmt(het.get('q'))} on "
              f"{fmt(het.get('df'))} df</small></p>" + NL
            # WHICH ARM THE NUMBER FAVOURS, in words. The object has always
            # carried `favours`, and the validator's direction anchor has
            # always tied it to the interval -- but it was rendered NOWHERE, so
            # a reader saw a ratio below one and had to supply the direction
            # themselves. On a BENEFICIAL outcome that reading inverts, and
            # inverting it is exactly the defect one of these apps shipped.
            + ((f"  <p><strong>Favours: "
                f"{e(_favoured_arm(res, outcome))}</strong>"
                f"{(' &mdash; ' + p(res['favours_note'])) if res.get('favours_note') else ''}"
                f"</p>" + NL)
               if res.get("favours") else "")
            + ((f"  <p><small>{p(res['heterogeneity_status'])}</small></p>" + NL)
               if res.get("heterogeneity_status") else "")
            # WHY THESE TRIALS AND NOT OTHERS -- rendered at last. `poolable_reason` is where
            # the substantive judgement lives on every object in this corpus: which trials
            # share the estimand, which definitions were read, what was refused and why. It
            # was rendered ONLY on the "No combined estimate" branch, so a REFUSAL to pool
            # explained itself and a DECISION to pool did not.
            #
            #     Measured 2026-08-19 on the delivered APIXABAN_VTE_TREATMENT page: the
            #     object's poolable_reason -- "Three trials randomise apixaban ITSELF against
            #     another anticoagulant ... Their definitions were read and compared, not
            #     their names" -- appears NOWHERE in 1.2 MB of shipped HTML.
            #
            # The same class as the withholding-direction gap fixed earlier the same day: the
            # object holds the reasoning and the reader is shown the number.
            + ((f"  <p>{p(res['poolable_reason'])}</p>" + NL)
               if res.get("poolable_reason") else "")
            # WHAT THE CHECK CHANGED -- including when it changed almost nothing.
            #
            # A review that reports only the checks which MOVED a number teaches a reader that
            # checking is worthwhile when it pays, which is the opposite of the lesson. On
            # bococizumab an executed search found a sixth trial and moved the pooled estimate
            # by 0.22 percentage points -- and BEFORE that search nobody could distinguish
            # "right" from "unexamined and lucky", because from the outside the two are
            # identical. A CONFIRMATION IS A RESULT, and it needs somewhere on the page to be
            # one.
            + (("  <div class='card warn'><h3>%s</h3>"
                "<table><tr><th></th><th>k</th><th>n</th><th>estimate</th><th>I&sup2;</th>"
                "</tr>"
                "<tr><td>before the check</td><td class='num'>%s</td><td class='num'>%s</td>"
                "<td class='num'>%s (%s to %s)</td><td class='num'>%s%%</td></tr>"
                "<tr><td>after</td><td class='num'>%s</td><td class='num'>%s</td>"
                "<td class='num'>%s (%s to %s)</td><td class='num'>%s%%</td></tr></table>"
                "<p>%s</p><p><strong>%s</strong></p><p><small>%s</small></p></div>" + NL)
               % (p(res["what_the_check_changed"].get("headline", "")),
                  fmt(res["what_the_check_changed"]["old"].get("k")),
                  fmt(res["what_the_check_changed"]["old"].get("n")),
                  fmt(res["what_the_check_changed"]["old"].get("md")),
                  fmt(res["what_the_check_changed"]["old"].get("ci_low")),
                  fmt(res["what_the_check_changed"]["old"].get("ci_high")),
                  fmt(res["what_the_check_changed"]["old"].get("i2")),
                  fmt(res["what_the_check_changed"]["new"].get("k")),
                  fmt(res["what_the_check_changed"]["new"].get("n")),
                  fmt(res["what_the_check_changed"]["new"].get("md")),
                  fmt(res["what_the_check_changed"]["new"].get("ci_low")),
                  fmt(res["what_the_check_changed"]["new"].get("ci_high")),
                  fmt(res["what_the_check_changed"]["new"].get("i2")),
                  p(res["what_the_check_changed"].get("what_moved", "")),
                  p(res["what_the_check_changed"].get(
                      "why_that_is_a_finding_and_not_a_null_result", "")),
                  p(res["what_the_check_changed"].get("the_third_direction", "")))
               if isinstance(res.get("what_the_check_changed"), dict)
               and res["what_the_check_changed"].get("old") else "")
            + ((f"  <p><strong>How to read this:</strong> "
                f"{p(res['interpretation_caveat'])}</p>" + NL)
               if res.get("interpretation_caveat") else "")
            + (("  <div class='absent-state' role='note'><strong>Why this pool "
                "stands.</strong> " + p(_stands) + "</div>" + NL)
               if _stands else "")
            + (("  <p><small>" + p(_cav) + "</small></p>" + NL) if _cav else "")
            # AN OPEN QUESTION ON THE ESTIMATE RENDERS FROM THE OBJECT.
            #
            # ARNI's was published as a HAND EDIT of the built page and existed
            # in no object: one <div> added straight to the HTML, nothing in the
            # source of truth. THE FIRST REBUILD DELETED THE ENTIRE FINDING, and
            # it was caught only because the rebuild's value counts were compared
            # against the served page before pushing. A finding that lives in the
            # artefact survives exactly until someone regenerates the artefact --
            # the same shape as SGLT2_HF's withdrawal, which was prose on the page
            # while the object kept the withdrawn number live.
            #
            # AND IT RENDERS EVERY KEY THE OBJECT HOLDS, IN THE OBJECT'S OWN
            # ORDER. The first version named eight keys explicitly, so a field
            # added to the object rendered NOWHERE -- the same defect one level
            # in from the one this comment describes: a finding that lives in
            # the object and dies in the projector is no more durable than one
            # that lives in the artefact. Adding the resolution to this block
            # would have silently dropped three of its eleven fields, including
            # the arithmetic witness the whole conclusion rests on.
            #
            # Keys beginning with an underscore are notes to whoever edits the
            # object and are deliberately NOT rendered.
            + _finding_block(res, "open_question", "alert",
                             p, NL)
            # A RESOLVED QUESTION IS PUBLISHED AS PROMINENTLY AS THE QUESTION
            # WAS. The reader who saw the doubt is owed the answer in the same
            # place, at the same size. Quietly deleting the paragraph would
            # leave anyone who wrote it down unable to tell a resolution from a
            # retraction -- the display_change_announced obligation, applied to
            # prose rather than to a number.
            + _finding_block(res, "resolved_question", "note",
                             p, NL)
            # AND THE POOL FINDINGS, WHICH UNTIL 2026-08-21 REACHED THE PAPER
            # PANEL AND NOTHING ELSE. `POOL_FINDINGS_<stamp>` is where every
            # qualification written during the 2026-08-20/21 run was stored --
            # the tigecycline interval that disagrees with its own delivered
            # conclusion, the breadth deficit on four topics, the cangrelor
            # discrepancy, the AGYW trials that enrolled nobody under 18. ONLY
            # `paper_projector` read the key, so all of it rendered at the very
            # bottom of the page inside the manuscript, roughly a megabyte past
            # the estimate it qualifies. I reported to Mahmood that the
            # tigecycline discrepancy "renders where a reader meets the number".
            # IT DID NOT. Class 83, on the findings rather than on the limbs.
            #
            # Prefix-matched, not named, for the same reason `pool_findings()`
            # in the projector is: the key carries a date stamp, so an exact
            # name would go stale the next time one is written.
            + "".join(_finding_block(res, k, "alert", p, NL)
                      for k in sorted(res) if k.startswith("POOL_FINDINGS_"))
            # THE PREDICTION INTERVAL BELONGS BESIDE THE ESTIMATE, NOT IN AN
            # APPENDIX. On a pool with I-squared near 90 the confidence interval
            # answers "where is the average"; the reader almost always wants
            # "what would a new trial show", which here is three times wider. It
            # was held in the object and rendered nowhere, so the only interval
            # on the headline card was the one that understates the spread.
            + ((f"  <p class='num'>Prediction interval "
                f"{fmt(res['prediction_interval']['low'])} to "
                f"{fmt(res['prediction_interval']['high'])}</p>" + NL
                + ((f"  <p><small>{p(res['prediction_interval']['what_it_says'])}"
                    f"</small></p>" + NL)
                   if res["prediction_interval"].get("what_it_says") else ""))
               if isinstance(res.get("prediction_interval"), dict)
               and res["prediction_interval"].get("low") is not None else "")
            # AND THE ESTIMATOR CAVEAT, WHERE THE ESTIMATOR IS NAMED. A page that
            # prints "estimator DerSimonian-Laird" one line above, and carries a
            # recorded objection to using it at this k, and does not show it, has
            # put the objection somewhere the reader who stops at the headline
            # will never go.
            + ((f"  <p><strong>About this estimator:</strong> "
                f"<small>{p(res['estimator_note'])}</small></p>" + NL)
               if res.get("estimator_note") else "")
            + ((("  <h3>What other estimators give on the same values</h3>"
                 + NL + "  <table>" + NL
                 + "    <tr><th>Estimator</th><th>&tau;&sup2;</th><th>I&sup2;</th>"
                   "<th>Pooled (95%)</th></tr>" + NL
                 + "".join(
                     f"    <tr><td>{e(str(r0.get('estimator','')))}"
                     f"{('<br><small>' + e(str(r0['note'])) + '</small>') if r0.get('note') else ''}"
                     f"</td><td class='num'>{fmt(r0.get('tau2'))}</td>"
                     f"<td class='num'>{fmt(r0.get('i2_pct'))}%</td>"
                     f"<td class='num'>{fmt(r0.get('point'))} "
                     f"({fmt(r0.get('ci_low'))} to {fmt(r0.get('ci_high'))})</td>"
                     f"</tr>" + NL
                     for r0 in (res["estimator_sensitivity"].get("rows") or []))
                 + "  </table>" + NL
                 + ((f"  <p><small>{p(res['estimator_sensitivity']['what_moves'])}"
                     f"</small></p>" + NL)
                    if res["estimator_sensitivity"].get("what_moves") else "")
                 + ((f"  <p><strong>"
                     f"{p(res['estimator_sensitivity']['the_one_that_matters'])}"
                     f"</strong></p>" + NL)
                    if res["estimator_sensitivity"].get("the_one_that_matters")
                    else "")))
               if isinstance(res.get("estimator_sensitivity"), dict)
               and res["estimator_sensitivity"].get("rows") else "")
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
                + f"  <p class='num'>{e(only['measure'])} {_interval(only, p)}"
                + (f", {fmt(only['ci_level'])}% interval"
                   if only.get("ci_level") and only["ci_level"] != 95 else "")
                + "</p>" + NL
                + ((f"  <p class='num'>Vaccine efficacy "
                    f"{fmt(only['published_ve_percent'])}% "
                    f"({fmt(only['published_ve_ci_low_percent'])} to "
                    f"{fmt(only['published_ve_ci_high_percent'])})</p>" + NL)
                   if only.get("published_ve_percent") is not None else "")
                # WHICH ARM THE NUMBER FAVOURS, on the SINGLE-COHORT branch too.
                # This line existed only under `if pooled`, so an outcome
                # reported from one trial rendered no direction at all -- and
                # the outcomes most likely to be reported from one trial are the
                # unusual ones. In the intravenous-iron review BOTH outcomes
                # whose benefit runs UPWARD are single-cohort, so the page stated
                # "lower is better" four times and never once said the opposite
                # about the two rows where it is true. A reader meeting a win
                # ratio above one, or a difference in metres, had to supply the
                # direction themselves, which is precisely the inversion this
                # line was added to prevent.
                + ((f"  <p><strong>Favours: "
                    f"{e(_favoured_arm(res, outcome))}</strong>"
                    f"{(' &mdash; ' + p(res['favours_note'])) if res.get('favours_note') else ''}"
                    f"</p>" + NL)
                   if res.get("favours") else "")
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
                     f"<th>{e(outcome.get('measure'))} (95% CI)</th><th>I&sup2;</th>"
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
    h = res.get("handbook") or {}
    # ABSENCE MARKERS ARE NOT VALUES, ON THIS TAB EITHER. `paper_projector` learned this
    # twice today -- at four composition sites, then structurally in `Section.add` after an
    # adversarial pass found 72 more the four guards did not cover. THIS FILE RENDERS A
    # DIFFERENT TAB and inherited neither, so the Extraction tab still printed a card whose
    # whole subject is a methods rule while asserting one that was never recorded:
    # "Decision: not recorded on the page this object was built from", above an empty
    # sections line. `res.get("handbook")` is truthy on the dict and every line inside was
    # emitted unconditionally.
    #
    # The card exists to carry the RULE. With neither the decision nor the conformance
    # recorded there is no rule to carry, and the heading on its own asserts one.
    if h and (_recorded(h.get("decision")) or _recorded(h.get("conformance"))):
        hb = (f"<div class='card'>\n  <h3>The methods rule governing this "
              f"decision</h3>\n"
              + (f"  <p><strong>Decision:</strong> {p(h['decision'])}</p>\n"
                 if _recorded(h.get("decision")) else "")
              + (f"  <p><strong>Cochrane Handbook sections:</strong> "
                 f"{e(', '.join(str(x) for x in h['sections']))}</p>\n"
                 if h.get("sections") else "")
              + (f"  <p>{p(h['conformance'])}</p>\n"
                 if _recorded(h.get("conformance")) else "")
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
    if res.get("sensitivity") and not all(
            "omitted" in a for a in res["sensitivity"].get("analyses", [])):
        # A GENERAL sensitivity block. The original renderer assumed every row
        # omitted a cohort, which is only one of the decisions the Handbook
        # asks to be tested: section 10.4.3 asks specifically whether the
        # choice of summary statistic AND of which category counts as the event
        # changes the conclusion, and neither of those omits anything. An
        # object testing them had its most important finding rendered nowhere.
        # Leave-one-out rows still take the branch below, unchanged.
        s = res["sensitivity"]
        srows = "".join(
            f"    <tr><td>{e(a['changed'])}</td>"
            f"<td class='num'>{fmt(a['result']['point'])} "
            f"({fmt(a['result']['ci_low'])} to {fmt(a['result']['ci_high'])})"
            f"</td>"
            f"<td class='num'>{fmt(a['result']['i2'])}%</td>"
            f"<td>{e(a['verdict'])}</td></tr>\n"
            for a in s["analyses"])
        sens = (f"<div class='card warn'>\n  <h3>Is the finding robust to how "
                f"it was reached?</h3>\n  <p>{p(s['why'])}</p>\n  <table>\n"
                f"    <tr><th>What was changed</th>"
                f"<th>{e(outcome.get('measure'))} or its alternative (95% CI)</th>"
                f"<th>I&sup2;</th><th>Effect on the conclusion</th></tr>\n"
                f"{srows}  </table>\n"
                f"  <p><strong>{p(s['conclusion'])}</strong></p>\n"
                + (_method_table(s, p, e, res.get("pooled"))
                   or _house_rule_table(res, p, e)) + "</div>\n")
    elif res.get("sensitivity"):
        s = res["sensitivity"]
        # An efficacy column and a `conclusion` line are VACCINE-shaped. This
        # renderer was written against a vaccine pool and read both keys
        # unconditionally, so the first hazard-ratio pool to reach it died on
        # KeyError: 've_percent'. A hazard ratio has no vaccine efficacy and
        # inventing one would be a fabricated column, so the column is emitted
        # only where every row actually carries the value. Both branches are
        # byte-identical to the previous output when the keys are present, which
        # is asserted against a fresh projection of all eight live objects
        # rather than reasoned about.
        has_ve = all("ve_percent" in a for a in s["analyses"])
        concl = s.get("conclusion") or s.get("leave_one_out_finding")
        srows = "".join(
            f"    <tr><td>{e(a['omitted'])}</td>"
            f"<td class='num'>{fmt(a['k'])}</td>"
            f"<td class='num'>{fmt(a['point'])} "
            f"({fmt(a['ci_low'])} to {fmt(a['ci_high'])})</td>"
            + (f"<td class='num'>{fmt(a['ve_percent'])}%</td>" if has_ve else "")
            + "</tr>\n"
            for a in s["analyses"])
        # AN EMPTY TABLE IS NOT A SENSITIVITY ANALYSIS. When no leave-one-out fit
        # was run -- which is every single-cohort outcome, where there is nothing
        # to leave out -- this rendered a header row over zero data rows. Two
        # things were wrong with that and both reached the reader: a table with
        # a header reads as an analysis that came out empty rather than as one
        # that was never applicable, which is the exact "manufacturing
        # reassurance" the prose immediately below it disclaims; and the header
        # named a NINETY-FIVE per cent interval on an outcome whose only interval
        # is at ninety-nine, because on a single-cohort outcome there are no
        # rows to read a level from. The finding prose is kept -- it says the
        # analysis was not run and why -- and the empty table is dropped.
        _table = (f"  <table>\n"
                  f"    <tr><th>Cohort omitted</th><th>k</th>"
                  f"<th>{e(outcome.get('measure'))} (95% CI)</th>"
                  + ("<th>Efficacy</th>" if has_ve else "")
                  + f"</tr>\n{srows}  </table>\n") if s["analyses"] else ""
        sens = (f"<div class='card'>\n  <h3>Leave-one-out sensitivity</h3>\n"
                f"  <p>{p(s['decision_under_test'])}</p>\n"
                + _table
                + (f"  <p><strong>{p(concl)}</strong></p>\n" if concl else "")
                + f"  <p><small>{p(s['authority'])}</small></p>\n"
                + (_method_table(s, p, e, res.get("pooled"))
                   or _house_rule_table(res, p, e)) + "</div>\n")

    # AND THE CASE WITH NO `sensitivity` BLOCK AT ALL, which is the one that matters.
    #
    # Both branches above are gated on `res.get("sensitivity")`. `finerenone-cv` has NO
    # sensitivity field -- it is None -- so the whole card was skipped and the fallback
    # placed inside those branches could never run. It rendered correctly when called
    # directly and never once from a build.
    #
    #     PROVING A FUNCTION IS NOT PROVING THE PATH. The four proofs written for
    #     `_house_rule_table` called it directly, and one of them said approvingly that
    #     "no build reported anything" -- which was true, and was the defect: nothing had
    #     established that any build REACHES it. A guard proof must exercise the call
    #     site, not only the callee.
    if not sens:
        _hr = _house_rule_table(res, p, e)
        if _hr:
            sens = "<div class='card'>\n" + _hr + "</div>\n"

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
            # THE WORD "pooled" IS A CLAIM, AND THIS ROW MADE IT UNCONDITIONALLY.
            # Every outcome rendered "pooled on the X scale" -- including the
            # single-cohort ones, which carry a "Single cohort - no synthesis"
            # banner in the SAME block and store poolable=false, model=
            # single-study, estimator=none. The page contradicted itself three
            # lines apart, and a gate leg put the two quotes side by side.
            #
            # FOURTH instance of the generator class, and the one that widened
            # its definition: the first three were an ABSENT FIELD yielding a
            # confident default (`outcome_role_in_trial` -> "primary", the
            # hardcoded 95% header, `len(trials or [])` -> 0). This one is a
            # hardcoded PROSE PREFIX asserting a property the generator never
            # checked. The class is not "absent field, bad default" -- it is
            # "generator prose asserting something it never verified against the
            # object".
            # A PAGE SHOULD SAY "pooled" BECAUSE THE ESTIMAND WAS ESTABLISHED, NOT
            # BECAUSE SOMEONE ONCE POOLED IT. This read res["poolable"], which meant
            # only "the source page pooled these trials" -- never a judgement that the
            # pool was sound. Two live estimates were found combining incommensurable
            # constructs while carrying poolable=true AND estimand "NOT ESTABLISHED" in
            # the same block: finerenone-review pooled three event composites with a
            # continuous albuminuria ratio, and fcm-hf-review pooled a composite with
            # trials whose registered primaries were six-minute walk distance and
            # patient global assessment. The object was honest; the renderer read the
            # wrong field. FIFTH instance of the generator class -- prose asserting a
            # property the generator never verified against the object.
            + row("Effect scale",
                  (f"pooled on the {e(outcome.get('effect_scale', 'natural'))} scale"
                   if res.get("estimand_established") is True else
                   (f"combined on the {e(outcome.get('effect_scale', 'natural'))} scale; "
                    f"ESTIMAND UNIFORMITY NOT ESTABLISHED -- the contributing trials have "
                    f"not been shown to measure the same quantity"
                    if res.get("source_page_pooled") or res.get("poolable") else
                    f"reported on the {e(outcome.get('effect_scale', 'natural'))} "
                    f"scale; nothing is pooled on this outcome")))
            + "  </table>" + NL + "</div>" + NL)

    # THE COLUMN HEADER MUST NOT NAME AN INTERVAL LEVEL THE ROWS DO NOT CARRY.
    # This header hardcoded "95% CI" over whatever the rows held. One trial in
    # this corpus prints its primary with a NINETY-NINE per cent interval,
    # because it set its own significance level at one per cent -- so the header
    # labelled a 99% interval as a 95% one, in the table a reader reads, on the
    # single row in that outcome. The object stored the level correctly the whole
    # time; only the header was wrong, which is the worst place for it to be.
    _levels = {r.get("ci_level", 95) for r in (res.get("per_trial") or [])}
    _lvl = (f"{fmt(_levels.pop())}% CI" if len(_levels) == 1
            else "interval, at each row's own level")
    return f"""<section>
<h2>{p(outcome['name'])}</h2>
{estimand}{headline}
<div class="card">
  <h3>Contributing trials</h3>
  <table>
    <tr><th>Trial</th><th>Analysed<br><small>treatment / control</small></th>
        <th>{e(outcome.get('measure'))} ({_lvl}), or events</th>
        <th>Source of this cell</th></tr>
{rows}  </table>
  <p><small>{p(outcome.get('definition_note'))}</small></p>
</div>
{_endpoint_definitions(canon, oid, p, e)}{_not_contributing(canon, p, e)}{hb}{sens}{dissent}{subgroups}{note}</section>
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
        # The LINK is rendered when the decision carries one. A displayed
        # include/exclude decision is a claim about the world as much as a
        # number is, and under `source_links_enforced` a reader has to be able
        # to click through to the place it was decided from. A review leg found
        # this list rendering bare while the underlying records were fully
        # linked -- provenance that exists only where nobody looks. Objects
        # whose decisions carry no link render exactly as before.
        def _xlink(x):
            u = x.get("source_url")
            if not u:
                return ""
            t = x.get("source_tier")
            label = f"{t}: {u}" if t else u
            return f"<br><small><a href='{e(u)}'>{e(label)}</a></small>"

        xs = "".join(
            f"    <li><strong>{p(x['reason'])}</strong><br>{p(x['detail'])}"
            f"{_xlink(x)}</li>\n"
            for x in sc.get("excluded", []))
        screening = (
            f"<div class='card'>\n  <h2>What the search found, and what was kept</h2>\n"
            f"  <p>{p(sc['search_note'])}</p>\n"
            f"  <p><strong>Eligible:</strong> {p(sc['eligibility'])}</p>\n"
            f"  <h3>Excluded, with reasons</h3>\n  <ul>\n{xs}  </ul>\n"
            f"  <p><small>{p(sc['known_limitation'])}</small></p>\n</div>\n")

    # RESULTS THE OBJECT READ AND DID NOT USE. The screening block answers which
    # TRIALS are here. It has never answered which ROWS are in which pool, and an
    # object can read a result, decline it for a good reason, and leave a reader
    # unable to tell that from an oversight. Stored and unrendered is the same
    # failure as unstored: the object is the source of truth, the page is its
    # projection, and a disposition nobody can see is not a disclosure.
    considered = ""
    rows_any = [(t, r) for t in canon["inputs"]["trials"]
                for r in (t.get("rows_considered_not_pooled") or [])]
    if rows_any:
        def _val(r):
            if r.get("point") is None:
                return "<small>several rows; no value stored</small>"
            return (f"{e(r.get('measure',''))} {fmt(r['point'])} "
                    f"({fmt(r['ci_low'])} to {fmt(r['ci_high'])})")
        body = "".join(
            f"    <tr><td>{p(t.get('name') or t['id'])}</td>"
            f"<td>{p(r['row'])}</td>"
            f"<td class='num'>{_val(r)}</td>"
            f"<td>{e(r.get('designation',''))}</td>"
            f"<td><small>{p(r['why_not_pooled'])}</small></td></tr>\n"
            for t, r in rows_any)
        empties = "".join(
            f"  <p><small><strong>{p(t.get('name') or t['id'])}:</strong> "
            f"{p(t['rows_considered_empty_because'])}</small></p>\n"
            for t in canon["inputs"]["trials"]
            if not (t.get("rows_considered_not_pooled") or [])
            and str(t.get("rows_considered_empty_because", "")).strip())
        basis = next((t["rows_considered_basis"] for t in canon["inputs"]["trials"]
                      if t.get("rows_considered_basis")), "")
        considered = (
            "<div class='card'>\n  <h2>Results this review READ and did not pool</h2>\n"
            + (f"  <p>{p(basis)}</p>\n" if basis else "")
            + "  <table>\n    <tr><th>Trial</th><th>What it reports</th>"
              "<th>Effect</th><th>How the trial designates it</th>"
              "<th>Why it is not pooled here</th></tr>\n"
            + body + "  </table>\n" + empties + "</div>\n")
        screening += considered

    def _benchmarks(r, e, p):
        """The published syntheses' OWN numbers, each with its own scope.

        Emitted only when `reconciliation.published_benchmarks` exists, so every
        object that does not carry the key renders byte-identically to before.

        It exists because of a specific failure it is meant to make impossible.
        The page this block was written for replaced one whose benchmark row
        carried one synthesis's NAME, a second synthesis's trial count and
        sample size, and an interval bound belonging to neither -- three real
        numbers assembled into a claim no source makes. A reader could not have
        caught that from a single row. Printing each synthesis on its own line
        with its own trial list, sample size, model and endpoint is what makes
        the mismatch visible rather than plausible.
        """
        bms = r.get("published_benchmarks")
        if not bms:
            return ""
        rows = ""
        for b in bms:
            trials = ", ".join(b.get("trials") or [])
            ci = (f"{b['point']} ({b['ci_low']} to {b['ci_high']})"
                  if b.get("point") is not None else "")
            rows += (
                f"    <tr><td>{e(b.get('measure', ''))} {e(ci)}</td>"
                # NEVER PRINT A COUNT DERIVED FROM AN ABSENT FIELD. This read
                # `len(b.get("trials") or [])`, so a benchmark row that records
                # its size as a COUNT rather than as a list rendered a hard ZERO
                # in the trials column -- the page telling a reader that a
                # published ten-trial synthesis pooled nothing, while the object
                # three fields away stored ten. A gate leg quoted the row back.
                #
                # This is the THIRD instance of one class in this generator, after
                # `outcome_role_in_trial` defaulting to the string "primary" and
                # the interval header hardcoding 95%: an absent field yielding a
                # confident wrong value instead of an honest blank. The block's
                # own docstring says it exists so a reader can see each
                # synthesis's own trial count -- and it printed zero.
                f"<td class='num'>{e(_benchmark_trial_count(b))}</td>"
                f"<td class='num'>{e(str(b.get('n', '')))}</td>"
                f"<td>{p(b.get('model', ''))}</td>"
                f"<td>{p(b.get('endpoint', ''))}</td></tr>\n"
                f"    <tr><td colspan='5'><small>{p(trials)}"
                f"<br>{p(b.get('comparability', ''))}</small></td></tr>\n")
        note = r.get("what_the_benchmarks_show")
        return (
            "  <h3>What the published syntheses report, each with its own scope</h3>\n"
            "  <table>\n    <thead><tr><th>estimate</th><th>trials</th>"
            "<th>participants</th><th>model</th><th>endpoint</th></tr></thead>\n"
            f"    <tbody>\n{rows}    </tbody>\n  </table>\n"
            + (f"  <p><small>{p(note)}</small></p>\n" if note else ""))

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
            + _benchmarks(r, e, p)
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

    # THE NETWORK, if the object is one. Its shape is the finding: which
    # treatments are compared, by how many studies, and whether any closed loop
    # exists to check an indirect estimate against.
    network = ""
    net = canon.get("network")
    if net:
        nodes = ", ".join(f"{e(t['label'])}"
                          + (" (reference)" if t.get("is_reference") else "")
                          for t in net["treatments"])
        # Follow-up and administration describe an edge in some networks and
        # are simply not part of the comparison in others. Rendering a column
        # no edge carries printed "not stated" down the whole table, which
        # reads as missing data rather than as a column that does not apply.
        show_fu = any(x.get("follow_up_days") is not None for x in net["edges"])
        show_admin = any(x.get("administration") for x in net["edges"])
        erows = "".join(
            f"    <tr><td>{e(x['comparison'])}</td>"
            f"<td class='num'>{fmt(x['studies'])}</td>"
            + (f"<td class='num'>{fmt(x.get('follow_up_days'))}</td>"
               if show_fu else "")
            + (f"<td>{p(x.get('administration', ''))}</td>" if show_admin else "")
            + "</tr>" + NL
            for x in net["edges"])
        network = (
            f"<div class='card warn'>" + NL + "  <h2>The network</h2>" + NL
            + f"  <p><strong>Treatments:</strong> {nodes}</p>" + NL
            + "  <table>" + NL
            + "    <tr><th>Comparison</th><th>Studies</th>"
            + ("<th>Follow-up (days)</th>" if show_fu else "")
            + ("<th>Administration</th>" if show_admin else "")
            + "</tr>" + NL + erows
            + "  </table>" + NL
            + f"  <p><strong>Closed loops: {fmt(net['closed_loops'])}. "
            f"Multi-arm studies: {fmt(net['multi_arm_studies'])}. "
              f"Status: {p(net['status'])}</strong></p>" + NL
            + f"  <p>{p(net['why_no_network_estimate'])}</p>" + NL
            + (f"  <p><small>{p(net['multi_arm_covariance_note'])}</small></p>" + NL
               if net.get("multi_arm_covariance_note") else "")
            + "</div>" + NL)

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
{network}{screening}{carried}{recon}{authority}{removal}
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
