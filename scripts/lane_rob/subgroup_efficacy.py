# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: where the effect holds and where it has NOT BEEN SHOWN to.

WHY THIS EXISTS AS A SECTION AND NOT AS A LIMITATION. The pilot page held the most
decision-relevant result these trials produced -- that protection was not demonstrated in the
youngest women -- and spent it in a limitations paragraph, where it reads as a caveat about the
review rather than a finding about the drug. A pooled average over a population in which the
effect differs by stratum is not wrong; it is just not the number that decides who is offered
the intervention.

⛔ THE THREE-STATE RULE, AND IT IS THE WHOLE POINT OF THIS COMPONENT.

  demonstrated       the interval excludes no difference and favours the intervention
  NOT DEMONSTRATED   the interval includes no difference
  harm demonstrated  the interval excludes no difference and favours the control

⚠️ "NOT DEMONSTRATED" IS NOT "NO EFFECT", and the component will not print the second. A
subgroup with few events has a wide interval whatever the truth is; calling that "ineffective"
converts absence of evidence into evidence of absence, and in a prevention context it is the
error that takes a working intervention away from the people who need it most. A control below
asserts that the phrase never appears.

⛔ AND A POST-HOC SUBGROUP IS LABELLED ON EVERY ROW, not once in a footnote. A subgroup whose
prespecification is not recorded in the object is REFUSED -- not rendered with a hedge --
because a reader cannot tell a planned analysis from a found one by looking at it, and the
difference is most of what the result is worth.

⚠️ CREDIBILITY IS NOT ASSERTED HERE. Whether a subgroup difference is real is a question about
an interaction, and reporting stratum-specific intervals side by side is not a test of one. The
component prints the interaction evidence the object holds and says plainly when the object
holds none, rather than letting two non-overlapping intervals imply a test that was never run.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SSOT = os.path.join(REPO, "ssot")
for _p in (HERE, SSOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# A ratio below 1 favours the intervention for a harmful outcome. Efficacy percent is the
# complement and is stored as the sources print it.
LOWER_IS_BETTER = ("RR", "OR", "HR", "IRR", "RISK RATIO", "ODDS RATIO", "HAZARD RATIO",
                   "RATE RATIO", "RELATIVE RISK")


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _u(x):
    return str(x or "").strip().upper()


def _num(x):
    return x if isinstance(x, (int, float)) else None


def stratum_reading(st, measure):
    """The three states, and nothing else. -> (state, sentence)."""
    if _num(st.get("efficacy_percent")) is not None:
        pt = _num(st.get("efficacy_percent"))
        lo, hi = _num(st.get("ci_low")), _num(st.get("ci_high"))
        null, favours_treatment = 0.0, (pt is not None and pt > 0)
    else:
        pt = _num(st.get("point"))
        lo, hi = _num(st.get("ci_low")), _num(st.get("ci_high"))
        if _u(measure) not in LOWER_IS_BETTER:
            return ("undecidable",
                    "the measure is not one this component can read a direction from")
        null, favours_treatment = 1.0, (pt is not None and pt < 1.0)
    if lo is None or hi is None:
        return ("undecidable", "no interval is recorded for this stratum")
    if lo <= null <= hi:
        # ⛔ THE SENTENCE IS FIXED HERE AND MUST NOT BE SOFTENED INTO "NO EFFECT".
        return ("not demonstrated",
                "the interval includes no difference, so an effect in this stratum has not "
                "been demonstrated &mdash; which is not the same as showing there is none")
    if favours_treatment:
        return ("demonstrated", "the interval excludes no difference and favours the "
                                "intervention")
    return ("harm demonstrated",
            "the interval excludes no difference and favours the control")


def _cell(st):
    """Print the quantity the SOURCE gives, never a conversion presented as the source's own."""
    if _num(st.get("efficacy_percent")) is not None:
        pt, lo, hi = (_num(st.get("efficacy_percent")), _num(st.get("ci_low")),
                      _num(st.get("ci_high")))
        if lo is None or hi is None:
            return "%.0f%% (no interval recorded)" % pt
        a, b = sorted((lo, hi))
        return "%.0f%% (%.0f to %.0f)" % (pt, a, b)
    pt, lo, hi = _num(st.get("point")), _num(st.get("ci_low")), _num(st.get("ci_high"))
    if pt is None:
        return "&mdash;"
    if lo is None or hi is None:
        return "%.3f (no interval recorded)" % pt
    a, b = sorted((lo, hi))
    return "%.3f (%.3f to %.3f)" % (pt, a, b)


def _blocks(res):
    """The WITHIN-TRIAL subgroup blocks on an outcome, in a shape the renderer can walk.

    ⛔ THE KEY IS `stratified_analyses`, AND `subgroups` IS A DIFFERENT OBJECT. The corpus
    already uses `res["subgroups"]` for a list of POOLED strata -- each carrying its own k,
    pooled estimate, interval and I-squared -- which is a stratified meta-analysis ACROSS
    trials, rendered by `build_app_v2._outcome_section`. What this component reports is a
    subgroup analysis reported WITHIN one trial.

    ⚠️ Writing the second under the first's name crashed the build on the first attempt. That
    was lucky: the shapes were incompatible enough to raise. Had they been merely similar, one
    trial's post-hoc strata would have been published inside a table headed as a pooled
    analysis, and nothing would have said so.
    """
    # ⛔ THE RENDERER IS RETIRED; THIS READER IS NOT. One finding, one key, one renderer --
    # the store key is now `subgroups`, feeding the renderer that predates both lanes. But
    # clinical_reading DERIVES C1 and C4 through this function, so retiring it wholesale would
    # have silently dropped the safety-critical "not demonstrated in 18 to 21" claim from the
    # clinical reading. ⚠️ A SCHEMA MIGRATION THAT MOVES A KEY MUST FOLLOW EVERY READER OF IT,
    # and git cannot see that dependency any more than it could see the duplicate write.
    sg = res.get("subgroups")
    if isinstance(sg, list) and sg:
        pre = [x for x in sg if isinstance(x, dict) and x.get("prespecified")]
        post = [x for x in sg if isinstance(x, dict) and not x.get("prespecified")]
        out = []
        for name, group, flag in (("age (prespecified)", pre, True),
                                  ("age (post-hoc)", post, False)):
            if not group:
                continue
            out.append((name, {
                "prespecified": flag,
                "strata": [{"label": x.get("label"),
                            "efficacy_percent": x.get("ve_percent", x.get("point")),
                            "ci_low": x.get("ci_low"), "ci_high": x.get("ci_high"),
                            "p": x.get("p_as_printed"),
                            "source_quote": x.get("verbatim")} for x in group],
                "interaction": ({"stated": res["subgroups_interaction"].get("how_to_read_it"),
                                 "p": res["subgroups_interaction"].get("p")}
                                if flag and isinstance(res.get("subgroups_interaction"), dict)
                                else None),
                "basis": "analysis_status: %s" % ", ".join(
                    sorted({str(x.get("analysis_status")) for x in group})),
            }))
        return out
    legacy = res.get("stratified_analyses")
    if isinstance(legacy, dict):
        return [(k, v) for k, v in legacy.items() if isinstance(v, dict)]
    return []


def has_pooled_strata(res):
    """Does the outcome carry the OTHER kind of stratification, rendered elsewhere?"""
    return isinstance(res.get("subgroups"), (list, dict)) and bool(res.get("subgroups"))


def render(canon):
    head = "<h2>Where this works, and where it has not been shown to</h2>"
    r = canon.get("results")
    outs = (r or {}).get("by_outcome") if isinstance(r, dict) else None
    if not isinstance(outs, dict) or not outs:
        return head + ("<p>This object records no outcome, so there is no effect to stratify. "
                       "That is a refusal, not an omission.</p>")
    out, any_block = [head], False
    for oid, res in outs.items():
        if not isinstance(res, dict):
            continue
        name = _esc(str(oid)[:60])
        blocks = _blocks(res)
        if not blocks:
            continue
        measure = _u((res.get("pooled") or {}).get("measure") or res.get("measure"))
        for factor, blk in blocks:
            any_block = True
            pre = blk.get("prespecified")
            if pre is None:
                # ⛔ REFUSED, NOT HEDGED. See the module docstring.
                out.append(
                    "<p><b>%s, by %s &mdash; not shown.</b> This object does not record whether "
                    "the analysis was prespecified. A reader cannot tell a planned subgroup from "
                    "a found one by looking at it, and that difference is most of what the "
                    "result is worth, so it is refused rather than printed with a hedge.</p>"
                    % (name, _esc(factor)))
                continue
            strata = [s for s in (blk.get("strata") or []) if isinstance(s, dict)]
            if not strata:
                out.append("<p><b>%s, by %s &mdash; not shown.</b> The block records no "
                           "strata.</p>" % (name, _esc(factor)))
                continue
            rows, readings = [], []
            for st in strata:
                state, why = stratum_reading(st, st.get("measure") or measure)
                cls = {"demonstrated": "good", "not demonstrated": "warn",
                       "harm demonstrated": "stop"}.get(state, "")
                rows.append(
                    "<tr><td>%s</td><td>%s</td><td>%s</td><td class=\"sg-state %s\">%s</td>"
                    "</tr>"
                    % (_esc(st.get("label") or "?"), _cell(st),
                       _esc(st.get("events") or st.get("n")) if (st.get("events") or st.get("n")) else "&mdash;",
                       cls, state))
                readings.append((st.get("label") or "?", state, why))
            out.append("<h3>%s, by %s</h3>" % (name, _esc(factor)))
            out.append("<div class=\"scroll\"><table><tr><th>Stratum</th>"
                       "<th>Effect (95%)</th><th>Events or n</th><th>Reading</th></tr>"
                       + "".join(rows) + "</table></div>")
            out.append(
                "<p><b>%s</b> %s</p>"
                % ("Prespecified." if pre else "Post-hoc, and labelled as such on every row "
                                               "above.",
                   _esc(blk.get("basis") or
                        ("These strata were prespecified in the trials' analysis plans."
                         if pre else
                         "This object does not record how the strata were formed."))))
            for label, state, why in readings:
                out.append("<p><b>%s:</b> %s.</p>" % (_esc(label), why))
            # ⚠️ THE INTERACTION, OR ITS ABSENCE, STATED. Two non-overlapping intervals are not
            # a test, and a page that shows them without saying so invites the reader to run one
            # in their head.
            inter = blk.get("interaction")
            if isinstance(inter, dict) and inter.get("stated"):
                out.append("<p>Interaction across these strata, as the source reports it: %s</p>"
                           % _esc(inter.get("stated")))
            else:
                out.append(
                    "<p>No test of interaction across these strata is recorded in this object. "
                    "The intervals above are stratum-specific and comparing them by eye is not "
                    "a test: intervals that fail to overlap can still be consistent with one "
                    "common effect, and intervals that overlap can still hide a real "
                    "difference.</p>")
            if not pre:
                out.append(
                    "<p>A post-hoc subgroup is hypothesis-generating. It is reported here rather "
                    "than in the limitations because it is the most decision-relevant result "
                    "these trials produced, and because a caveat filed under limitations is read "
                    "as a property of the review when it is a property of the evidence.</p>")
            ext = blk.get("external_corroboration")
            if ext:
                out.append("<p>%s</p>" % _esc(ext))
    if not any_block:
        # ⛔ THE ABSENCE IS PRINTED, AND IN THREE STATES RATHER THAN TWO. An object may hold
        # POOLED strata -- a stratified meta-analysis across trials, rendered by the outcome
        # section -- while holding no within-trial subgroup analysis at all. Reporting that as
        # "no stratified reading" would accuse a page that already carries one.
        pooled_elsewhere = any(
            isinstance(res, dict) and has_pooled_strata(res) for res in outs.values())
        if pooled_elsewhere:
            out.append(
                "<p>This object carries POOLED strata &mdash; a stratified meta-analysis across "
                "trials, shown with the outcome above &mdash; and no within-trial subgroup "
                "analysis. The two are different objects: a pooled stratum is this review's own "
                "estimate within a subset of trials, and a within-trial subgroup is the trial's "
                "own analysis within a subset of its participants. Neither substitutes for the "
                "other and only the first is held here.</p>")
        else:
            out.append(
                "<p>This object records no subgroup analysis for any outcome, so no stratified "
                "reading is given. The pooled estimate is an average over the trials' whole "
                "eligible population, and this page does not know whether it holds uniformly "
                "within it.</p>")
    return "".join(out)


MARKER = "<h2>Where this works, and where it has not been shown to</h2>"


def inject(html, canon):
    if MARKER in html:
        return html
    return html + "\n<div class=\"card\">\n" + render(canon) + "\n</div>\n"


# ---------------------------------------------------------------------------------------------
# COVERAGE, and the controls.
# ---------------------------------------------------------------------------------------------

def coverage(root=None):
    import collections
    import glob
    import json
    root = root or SSOT
    per = collections.Counter()
    skipped = collections.Counter()
    objs = with_block = 0
    for f in sorted(glob.glob(os.path.join(root, "*", "*.json"))):
        try:
            c = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            # ⛔ COUNTED, NOT SKIPPED. A `continue` here removes the file from the denominator
            # and the coverage figure silently becomes a reach figure.
            skipped["file did not parse as JSON"] += 1
            continue
        if not isinstance(c, dict):
            skipped["top level is not an object"] += 1
            continue
        r = c.get("results")
        outs = r.get("by_outcome") if isinstance(r, dict) else None
        if not isinstance(outs, dict) or not outs:
            skipped["no results.by_outcome recorded"] += 1
            continue
        objs += 1
        hit = False
        for _oid, res in outs.items():
            if not isinstance(res, dict):
                continue
            bl = _blocks(res)
            if not bl:
                per["no subgroup block recorded"] += 1
                continue
            for _factor, blk in bl:
                hit = True
                if blk.get("prespecified") is None:
                    per["refused: prespecification not recorded"] += 1
                elif not [s for s in (blk.get("strata") or []) if isinstance(s, dict)]:
                    per["refused: no strata"] += 1
                else:
                    per["RENDERED"] += 1
        with_block += 1 if hit else 0
    return {"objects_with_a_pooled_result": objs, "objects_with_a_subgroup_block": with_block,
            "blocks_and_outcomes": dict(per), "total": sum(per.values()),
            "skipped": dict(skipped)}


# ⭐ THE MODEL ANSWER, keyed to arithmetic anyone can check and to figures published outside
# this repository: the dapivirine over-21 stratum is reported as 56% (31 to 71). A risk ratio of
# 0.44 (0.29 to 0.69) is the same statement -- 1 - 0.44 = 0.56, 1 - 0.69 = 0.31, 1 - 0.29 = 0.71
# -- so a component that reads direction correctly must call BOTH forms "demonstrated".
MODEL_ANSWER = {
    "app_id": "__control_model_answer_subgroup",
    "results": {"by_outcome": {"primary": {
        "measure": "RR",
        "pooled": {"point": 0.71, "ci_low": 0.57, "ci_high": 0.89, "measure": "RR"},
        "stratified_analyses": {"age": {
            "prespecified": False,
            "basis": "Post-hoc; strata were formed to give approximately equal numbers of "
                     "events.",
            "strata": [
                {"label": "Over 21", "efficacy_percent": 56, "ci_low": 31, "ci_high": 71},
                {"label": "21 or younger", "efficacy_percent": -27, "ci_low": -133,
                 "ci_high": 31},
                {"label": "Over 21, stated as a ratio", "measure": "RR", "point": 0.44,
                 "ci_low": 0.29, "ci_high": 0.69}]}}}}}}

# ⭐ REFUSAL CONTROL 1. Prespecification absent -> the block is refused, not hedged.
NO_PRESPEC_CONTROL = {
    "app_id": "__control_refusal_no_prespecification",
    "results": {"by_outcome": {"primary": {
        "measure": "RR",
        "pooled": {"point": 0.71, "ci_low": 0.57, "ci_high": 0.89, "measure": "RR"},
        "stratified_analyses": {"age": {"strata": [
            {"label": "Over 21", "efficacy_percent": 56, "ci_low": 31, "ci_high": 71}]}}}}}}

# ⭐ REFUSAL CONTROL 2, AND THE ONE THAT MATTERS CLINICALLY. A stratum whose interval spans no
# difference must be read as NOT DEMONSTRATED and must never be described as having no effect.
# ⚠️ If this control ever creates pressure to print a crisper word, the control is right.
NOT_DEMONSTRATED_CONTROL = {
    "app_id": "__control_absence_of_evidence",
    "results": {"by_outcome": {"primary": {
        "measure": "RR",
        "pooled": {"point": 0.71, "ci_low": 0.57, "ci_high": 0.89, "measure": "RR"},
        "stratified_analyses": {"age": {
            "prespecified": True,
            "strata": [{"label": "18 to 24", "efficacy_percent": 10, "ci_low": -41,
                        "ci_high": 43}]}}}}}}

# ⭐ REFUSAL CONTROL 3 -- an object holding POOLED strata under the legacy `subgroups` key and
# no within-trial analysis must NOT be reported as unstratified. That would accuse a page that
# already carries a stratified table of not carrying one.
POOLED_STRATA_ELSEWHERE_CONTROL = {
    "app_id": "__control_pooled_strata_are_a_different_object",
    "results": {"by_outcome": {"primary": {
        "measure": "RR",
        "pooled": {"point": 0.71, "ci_low": 0.57, "ci_high": 0.89, "measure": "RR"},
        "subgroups": [{"label": "Children under 5", "k": 3, "point": 0.66, "ci_low": 0.55,
                       "ci_high": 0.79, "i2": 0.0}]}}}}

FORBIDDEN_PHRASES = ("no effect", "ineffective", "does not work", "has no benefit",
                     "shown to be ineffective", "no benefit")


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def plant():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    html = render(MODEL_ANSWER)
    t = _plain(html)
    print("MODEL ANSWER -- 56% (31 to 71) and RR 0.44 (0.29 to 0.69) are the same statement.")
    states = re.findall(r"<td class=\"sg-state [^\"]*\">([^<]*)</td>", html)
    assert states == ["demonstrated", "not demonstrated", "demonstrated"], states
    print("   readings: %s   [PASS]" % ", ".join(states))
    assert "56% (31 to 71)" in t, t[:300]
    assert "0.440 (0.290 to 0.690)" in t, t[:300]
    print("   both forms printed as the source gives them, no silent conversion   [PASS]")
    assert "Post-hoc" in t, t[:300]
    print("   post-hoc label present   [PASS]")
    assert "No test of interaction" in t, t[:400]
    print("   the missing interaction test is stated, not implied   [PASS]")
    print("")
    t2 = _plain(render(NO_PRESPEC_CONTROL))
    ok = "not shown" in t2 and "prespecified" in t2
    no_table = "<td class=\"sg-state" not in render(NO_PRESPEC_CONTROL)
    print("REFUSAL CONTROL -- prespecification not recorded")
    print("   reason stated: %s   no stratum table emitted: %s   [%s]"
          % (ok, no_table, "PASS" if ok and no_table else "FAIL"))
    assert ok and no_table, t2[:400]
    t3 = _plain(render(NOT_DEMONSTRATED_CONTROL)).lower()
    said = "not been demonstrated" in t3
    bad = [p for p in FORBIDDEN_PHRASES if p in t3]
    print("REFUSAL CONTROL -- absence of evidence is not evidence of absence")
    print("   says 'not been demonstrated': %s   forbidden phrases found: %s   [%s]"
          % (said, bad or "none", "PASS" if said and not bad else "FAIL"))
    assert said and not bad, (said, bad)
    # ⛔ AND THE FORBIDDEN-PHRASE CHECK MUST BE ABLE TO FIRE. A guard that has never been shown
    # to fail is not a guard; this proves the phrase list is actually consulted.
    probe = _plain("<p>This stratum shows no effect.</p>").lower()
    assert [p for p in FORBIDDEN_PHRASES if p in probe], "the phrase list never matches anything"
    print("   the phrase list demonstrably fires on a planted sentence   [PASS]")
    t4 = _plain(render(POOLED_STRATA_ELSEWHERE_CONTROL))
    right = "POOLED strata" in t4 and "different objects" in t4
    wrong = "records no subgroup analysis" in t4
    print("REFUSAL CONTROL -- pooled strata are not a within-trial subgroup analysis")
    print("   names the distinction: %s   does NOT report the page as unstratified: %s   [%s]"
          % (right, not wrong, "PASS" if right and not wrong else "FAIL"))
    assert right and not wrong, t4[:400]
    print("")
    print("⚠️ 'Not demonstrated' may not be tightened into 'no effect' to read more crisply.")
    return 0


if __name__ == "__main__":
    if "--plant" in sys.argv:
        raise SystemExit(plant())
    import json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    if "--coverage" in sys.argv:
        root = SSOT
        for i, a in enumerate(sys.argv):
            if a == "--root" and i + 1 < len(sys.argv):
                root = sys.argv[i + 1]
        c = coverage(root)
        n, m = c["objects_with_a_pooled_result"], c["total"]
        print("")
        print("COVERAGE FRACTION -- stratified reading")
        print("  scanned: %s" % root)
        if not n:
            print("  ⛔ SCAN FOUND NOTHING -- a failure of this scan, not of the corpus.")
            raise SystemExit(2)
        print("  objects with a pooled result       %4d   == the object denominator" % n)
        print("  objects carrying a subgroup block  %4d   %5.1f%%"
              % (c["objects_with_a_subgroup_block"],
                 100.0 * c["objects_with_a_subgroup_block"] / n))
        print("  outcome-blocks examined            %4d" % m)
        for k, v in sorted(c["blocks_and_outcomes"].items(), key=lambda kv: -kv[1]):
            print("     %-44s %4d   %5.1f%%" % (k, v, 100.0 * v / m if m else 0.0))
        if c.get("skipped"):
            print("")
            print("  SKIPPED, by kind -- these files were NOT in any denominator "
                  "above:")
            for _k, _v in sorted(c["skipped"].items(), key=lambda kv: -kv[1]):
                print("     %-46s %4d" % (_k, _v))
            print("  ⚠️ A skip that is not counted turns a coverage figure into a "
                  "reach figure.")
        raise SystemExit(0)
    os.chdir(REPO)
    for path in sys.argv[1:] or ["ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"]:
        canon = json.load(io.open(path, encoding="utf-8"))
        print("=" * 78)
        print(os.path.basename(path))
        print(_plain(render(canon))[:1800])
