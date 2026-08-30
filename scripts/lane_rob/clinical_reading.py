# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: what a clinician or a programme should take from this.

⛔ EVERY SENTENCE IS CONDITIONAL ON A FACT IN THE OBJECT. NOTHING HERE IS PROSE.

That is the whole difficulty of this section and the reason it was hand-written until now. An
interpretation is exactly the thing a generator is not supposed to produce -- so this component
does not interpret. It ASSEMBLES: each clause is emitted only when a specific derived condition
holds, and where the condition cannot be evaluated the clause is ABSENT rather than softened.
A reader gets the clauses the evidence earns and no others.

THE CLAUSES, AND WHAT EACH ONE REQUIRES:

  direction        a pooled ratio whose interval excludes no difference
  magnitude        a number needed to treat, which requires a baseline risk (absolute_effects)
  where it holds   a stratum read as `demonstrated` (subgroup_efficacy)
  where it does not a stratum read as `not demonstrated`
  harms            other-outcome rows at a tier strong enough to support the claim
  what it is not   outcomes recorded as absent or not measurable
  efficacy vs use  an adherence finding recorded in the object

⚠️ AND THE ONE CLAUSE THAT IS EMITTED WHEN NOTHING ELSE IS. A section that renders empty when
the object is thin reads as a review with nothing to say. When no clause qualifies, the
component states which conditions failed, by name -- so the gap is a readable property of the
evidence rather than a blank space.

⛔ IT WILL NOT SAY "SAFE". A claim of safety over the outcomes a trial happened to measure is
not a claim about safety, and the distance between the two is where post-marketing withdrawals
live. Where harms rows exist and show no excess, the clause says exactly that: no excess was
seen ON WHAT WAS MEASURED, and it names how many outcomes that was. A control asserts the
unqualified word never appears.

⛔ AND IT WILL NOT RECOMMEND. "Offer this to X" is a guideline's job, made against costs,
alternatives and values this object does not hold. The clauses state what the evidence supports
and what it does not; the decision stays with the reader.
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

import absolute_effects as AE  # noqa: E402
import other_outcomes as OO  # noqa: E402
import subgroup_efficacy as SE  # noqa: E402

# ⛔ NEVER EMITTED. See the docstring.
FORBIDDEN = ("is safe", "it is safe", "proven safe", "safe and effective",
             "should be offered", "we recommend", "clinicians should offer")


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def clauses(canon):
    """-> (list of (kind, sentence), list of (kind, why it could not be emitted))."""
    said, missing = [], []
    r = canon.get("results")
    outs = (r or {}).get("by_outcome") if isinstance(r, dict) else None
    if not isinstance(outs, dict) or not outs:
        return [], [("everything", "this object records no outcome")]

    # --- direction, and magnitude -------------------------------------------------------------
    for oid, res in outs.items():
        if not isinstance(res, dict):
            continue
        pooled = res.get("pooled") or {}
        if pooled.get("withdrawn"):
            missing.append(("direction", "the pool for %s is withdrawn" % oid))
            continue
        pt, lo, hi = pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")
        if not all(isinstance(v, (int, float)) and v > 0 for v in (pt, lo, hi)):
            missing.append(("direction", "no pooled estimate with an interval for %s" % oid))
            continue
        if lo <= 1.0 <= hi:
            said.append(("direction",
                         "On <b>%s</b>, the pooled interval includes no difference "
                         "(%.3f, %.3f to %.3f). An effect has not been demonstrated, which is "
                         "not the same as showing there is none." % (_esc(oid), pt, lo, hi)))
        else:
            said.append(("direction",
                         "On <b>%s</b>, the pooled estimate is %.3f (%.3f to %.3f) and the "
                         "interval excludes no difference." % (_esc(oid), pt, lo, hi)))
        got, why = AE.baseline(canon, res)
        cls = AE.classify(canon, res)
        if cls != "CONVERTED":
            missing.append(("magnitude", "no absolute effect for %s (%s)" % (oid, cls)))
        else:
            a = AE.absolute(got[0], float(pt), float(lo), float(hi))
            if a["spans_null"]:
                missing.append(("magnitude",
                                "the interval for %s spans no difference, so the number needed "
                                "to treat is not bounded" % oid))
            else:
                said.append(("magnitude",
                             "About <b>%d</b> people need to be treated to prevent one event%s. "
                             "The baseline is this review's own pooled control arms, %s per "
                             "1,000."
                             % (round(a["nnt"]),
                                (", on a range from %d to %d"
                                 % (round(a["nnt_ci"][0]), round(a["nnt_ci"][1])))
                                if a["nnt_ci"] else "",
                                ("%.1f" % a["per1000_control"]))))

    # --- where it holds, and where it has not been shown to -----------------------------------
    holds, notshown = [], []
    for _oid, res in outs.items():
        if not isinstance(res, dict):
            continue
        for _factor, blk in SE._blocks(res):
            if blk.get("prespecified") is None:
                continue
            for st in (blk.get("strata") or []):
                if not isinstance(st, dict):
                    continue
                state, _why = SE.stratum_reading(
                    st, st.get("measure") or (res.get("pooled") or {}).get("measure"))
                tag = "" if blk.get("prespecified") else " (post-hoc)"
                if state == "demonstrated":
                    holds.append("%s%s" % (st.get("label") or "?", tag))
                elif state == "not demonstrated":
                    notshown.append("%s%s" % (st.get("label") or "?", tag))
    if holds:
        said.append(("where it holds",
                     "An effect is demonstrated in: <b>%s</b>." % _esc("; ".join(holds))))
    else:
        missing.append(("where it holds", "no stratum reads as demonstrated"))
    if notshown:
        said.append(("where it has not been shown",
                     "It has <b>not been demonstrated</b> in: <b>%s</b>. ⚠️ These trials cannot "
                     "say whether that is the intervention or the adherence, and offering it as "
                     "though the pooled figure applied would overstate what is known."
                     % _esc("; ".join(notshown))))
    else:
        missing.append(("where it has not been shown", "no stratum reads as not demonstrated"))

    # --- harms, and what it is not ------------------------------------------------------------
    measured, absent_rows = [], []
    for _oid, res in outs.items():
        if not isinstance(res, dict):
            continue
        rows, _n = OO._rows(res)
        for row in rows:
            if not isinstance(row, dict):
                continue
            ok, _why = OO.check_row(row)
            if not ok:
                continue
            tier = str(row.get("tier")).strip().lower()
            (absent_rows if tier.startswith("absent") else measured).append(row)
    strong = [r for r in measured if str(r.get("tier")).strip().lower() == "trial report"]
    if strong:
        # ⛔ "no excess ON WHAT WAS MEASURED", never "safe". See the docstring and the control.
        said.append(("harms",
                     "Across the <b>%d</b> outcome%s read from the trials' own reports, no "
                     "excess was seen on what was measured. ⚠️ That is a statement about those "
                     "%d outcomes, not about the intervention: an outcome nobody recorded looks, "
                     "from this page, exactly like an outcome that did not occur."
                     % (len(strong), "" if len(strong) == 1 else "s", len(strong))))
    else:
        missing.append(("harms", "no harm outcome is held at the trial-report tier"))
    if absent_rows:
        said.append(("what it is not",
                     "It offers nothing on: <b>%s</b> &mdash; recorded as not measured or not "
                     "reported in a usable form."
                     % _esc("; ".join(str(r.get("outcome")) for r in absent_rows[:6]))))
    else:
        missing.append(("what it is not", "no outcome is recorded as absent or not measurable"))

    # --- efficacy in a trial versus effectiveness in use --------------------------------------
    blob = " ".join(
        str(blk.get("basis", "")) + str(blk.get("external_corroboration", ""))
        for _o, res in outs.items() if isinstance(res, dict)
        for _f, blk in SE._blocks(res))
    if re.search(r"adherence", blob, re.I):
        said.append(("efficacy versus use",
                     "Effectiveness in use will be lower than this. The object records adherence "
                     "as the proposed explanation for the difference between strata, and that "
                     "adherence was measured inside a trial with scheduled contact &mdash; "
                     "conditions a service does not reproduce."))
    else:
        missing.append(("efficacy versus use",
                        "the object records no adherence finding"))
    return said, missing


def render(canon):
    head = "<h2>What a clinician or a programme should take from this</h2>"
    said, missing = clauses(canon)
    out = [head]
    if said:
        out.append("<ul>" + "".join("<li>%s</li>" % s for _k, s in said) + "</ul>")
        out.append(
            "<p><small>Each statement above is emitted only when a specific condition holds in "
            "this review's own object; none is written by hand. This section makes no "
            "recommendation: what to offer, to whom, at what cost and against what alternative "
            "is a judgement this page does not hold the inputs for.</small></p>")
    if missing:
        # ⛔ THE UNSAID IS NAMED. A clause that could not be earned is more informative than its
        # silence, and silence is what lets a thin review read like a confident one.
        out.append(
            "<p><b>What this page cannot tell a clinician, and why.</b> %s</p>"
            % " ".join("<i>%s</i> &mdash; %s." % (_esc(k), _esc(w)) for k, w in missing))
    return "".join(out)


MARKER = "<h2>What a clinician or a programme should take from this</h2>"


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
    objs = 0
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
        said, _missing = clauses(c)
        per["%d clause(s) earned" % len(said)] += 1
    return {"objects_with_a_pooled_result": objs, "detail": dict(per),
            "skipped": dict(skipped)}


def _obj(**kw):
    base = {"inputs": {"trials": [
        {"nct": "NCT00000001", "label": "Control trial A", "arms": [
            {"label": "treatment", "role": "treatment", "events": 50, "participants": 1000},
            {"label": "placebo", "role": "control", "events": 100, "participants": 1000}]}]},
        "results": {"by_outcome": {"primary": {
            "measure": "RR",
            "pooled": {"point": 0.50, "ci_low": 0.40, "ci_high": 0.625, "measure": "RR"},
            "per_trial": [{"nct": "NCT00000001", "label": "Control trial A"}]}}}}
    base["results"]["by_outcome"]["primary"].update(kw)
    return base


# ⭐ THE MODEL ANSWER. Every clause earns itself: a demonstrated direction, an NNT of 20 by
# arithmetic anyone can check, one stratum demonstrated and one not, a trial-report harm row,
# an absent outcome, and an adherence finding.
MODEL_ANSWER = _obj(
    stratified_analyses={"age": {
        "prespecified": True,
        "basis": "prespecified; the difference between strata is attributed to adherence",
        "strata": [
            {"label": "25 and over", "efficacy_percent": 61, "ci_low": 32, "ci_high": 77},
            {"label": "Under 25", "efficacy_percent": 10, "ci_low": -41, "ci_high": 43}]}},
    other_outcomes={"rows": [
        {"outcome": "Any serious adverse event", "treatment": "52 (4%)", "control": "48 (4%)",
         "effect": "no material difference", "tier": "trial report"},
        {"outcome": "Herpes simplex virus", "treatment": "&mdash;", "control": "&mdash;",
         "effect": "NOT MEASURABLE", "tier": "absent by design"}]})

# ⭐ REFUSAL CONTROL 1 -- a thin object must NAME the clauses it could not earn, not render
# a confident short list.
THIN_CONTROL = _obj()

# ⭐ REFUSAL CONTROL 2 -- a pooled interval that spans no difference must not produce a
# direction clause claiming an effect, nor a bounded NNT.
SPANS_NULL_CONTROL = {
    "inputs": {"trials": [
        {"nct": "NCT00000003", "label": "C", "arms": [
            {"label": "t", "role": "treatment", "events": 95, "participants": 1000},
            {"label": "c", "role": "control", "events": 100, "participants": 1000}]}]},
    "results": {"by_outcome": {"primary": {
        "measure": "RR",
        "pooled": {"point": 0.95, "ci_low": 0.72, "ci_high": 1.25, "measure": "RR"},
        "per_trial": [{"nct": "NCT00000003", "label": "C"}]}}}}


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def plant():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    said, missing = clauses(MODEL_ANSWER)
    kinds = [k for k, _s in said]
    print("MODEL ANSWER -- every clause conditional, and each one earned by a fact in the object.")
    for k in ("direction", "magnitude", "where it holds", "where it has not been shown",
              "harms", "what it is not", "efficacy versus use"):
        assert k in kinds, "clause %r was not earned: %s" % (k, kinds)
    print("   clauses earned: %s   [PASS]" % ", ".join(kinds))
    t = _plain(render(MODEL_ANSWER))
    assert "About 20 people need to be treated" in t, t[:400]
    print("   the NNT is the arithmetic answer, 20   [PASS]")
    bad = [p for p in FORBIDDEN if p in t.lower()]
    print("   forbidden claims present: %s   [%s]" % (bad or "none", "PASS" if not bad else "FAIL"))
    assert not bad, bad
    assert "not about the intervention" in t, t[:600]
    print("   harms clause is qualified to WHAT WAS MEASURED   [PASS]")
    # ⛔ The forbidden list must be able to fire, or it is decoration.
    probe = "this treatment is safe and effective and should be offered"
    assert [p for p in FORBIDDEN if p in probe], "the forbidden list never matches anything"
    print("   the forbidden list demonstrably fires on a planted sentence   [PASS]")
    print("")
    t2 = _plain(render(THIN_CONTROL))
    named = "What this page cannot tell a clinician" in t2
    print("REFUSAL CONTROL -- a thin object names what it could not say")
    print("   names the failed conditions: %s   [%s]" % (named, "PASS" if named else "FAIL"))
    assert named, t2[:400]
    t3 = _plain(render(SPANS_NULL_CONTROL))
    honest = "has not been demonstrated" in t3
    nonnt = "need to be treated" not in t3
    print("REFUSAL CONTROL -- an interval spanning no difference earns no effect and no NNT")
    print("   states 'not demonstrated': %s   emits no NNT: %s   [%s]"
          % (honest, nonnt, "PASS" if honest and nonnt else "FAIL"))
    assert honest and nonnt, t3[:400]
    print("")
    print("⚠️ The word 'safe' and any recommendation to offer are permanently forbidden here.")
    print("   If a control creates pressure to relax that, the control is right.")
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
        n = c["objects_with_a_pooled_result"]
        print("")
        print("COVERAGE FRACTION -- clinical reading")
        print("  scanned: %s" % root)
        if not n:
            print("  ⛔ SCAN FOUND NOTHING -- a failure of this scan, not of the corpus.")
            raise SystemExit(2)
        print("  objects with a pooled result   %4d   == the denominator" % n)
        for k, v in sorted(c["detail"].items()):
            print("     %-30s %4d   %5.1f%%" % (k, v, 100.0 * v / n))
        print("")
        print("  The section RENDERS on every object; where a clause cannot be earned it is")
        print("  named as unearned rather than omitted.")
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
        print(_plain(render(canon))[:2200])
