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


def _topic_is_infection_prevention(measured, absent_rows):
    """Is claim C11 even IN SCOPE for this review?

    THE SHAPE IS THE DEFECT, NOT THE STRING. An `if` gated on topic-relevant
    data whose `else` is gated on NOTHING will emit its claim on every topic
    the claim was not written for -- and it is invisible on the one topic it
    was tested against, because there the `if` fires. Any branch naming a
    disease, a drug class or an outcome family needs the SAME gate on both
    sides.
    """
    names = [str((r or {}).get("outcome") or "")
             for r in list(measured or []) + list(absent_rows or [])]
    return any(re.search(r"hiv|sti\b|sexual|chlamyd|gonorrh|trichomon|syphilis|"
                         r"papillomavirus|herpes|infection|seroconver",
                         n, re.I) for n in names)


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
                # ⛔ THE HORIZON TRAVELS WITH THE NNT. A number of people with no period of
                # time is not the claim: "45 people" and "45 people for eighteen months" are
                # different facts, and a reader takes the first away as if it were the second.
                _span, _quoted, _typed = AE._horizon(canon, res)
                said.append(("magnitude",
                             "About <b>%d</b> people need to be treated%s to prevent one "
                             "event%s. The baseline is this review's own pooled control arms, "
                             "%s per 1,000."
                             % (round(a["nnt"]),
                                (" over %s" % _esc(_span)) if _typed else "",
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
                # ⭐ THE STRATUM'S OWN NUMBER TRAVELS WITH ITS NAME. Naming the stratum and
                # printing only the POOLED effect beside it is the substitution this whole
                # section exists to prevent: a reader takes the average away as if it were the
                # stratum's. The hand-written reference gives "56% protection" for the stratum
                # and it is the sentence a clinician quotes.
                size = SE._cell(st)
                lab = "%s%s" % (st.get("label") or "?", tag)
                if state == "demonstrated":
                    holds.append((lab, size))
                elif state == "not demonstrated":
                    notshown.append((lab, size))
    if holds:
        said.append(("where it holds",
                     "An effect is demonstrated in %s. Those are the strata's own estimates, "
                     "not the pooled average."
                     % _esc("; ".join("%s, %s" % (lab, size) for lab, size in holds))))
    else:
        missing.append(("where it holds", "no stratum reads as demonstrated"))
    if notshown:
        said.append(("where it has not been shown",
                     "It has <b>not been demonstrated</b> in %s. ⚠️ These trials cannot "
                     "say whether that is the intervention or the adherence, and offering it as "
                     "though the pooled figure applied would overstate what is known."
                     % _esc("; ".join("%s, %s" % (lab, size) for lab, size in notshown))))
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
        #
        # ⭐ AND THE OUTCOMES ARE NAMED, NOT COUNTED. "Across 6 outcomes, no excess was seen"
        # is a sentence a reader cannot check and cannot act on; the hand-written reference says
        # "no excess of severe or serious adverse events, and no resistance signal among women
        # who seroconverted", and that is the version a clinician can disagree with. A count is
        # what you write when you have not looked at the list.
        names = [str(r.get("outcome")) for r in strong]
        said.append(("harms",
                     "No excess was seen on what was measured: <b>%s</b>. ⚠️ That is a "
                     "statement about those %d outcomes, not about the intervention — an "
                     "outcome nobody recorded looks, from this page, exactly like an outcome "
                     "that did not occur."
                     % (_esc("; ".join(names[:8])
                             + ("" if len(names) <= 8 else "; and %d more" % (len(names) - 8))),
                        len(strong))))
    else:
        missing.append(("harms", "no harm outcome is held at the trial-report tier"))
    # ⛔ C11, AND MY OWN LEDGER MASKED ITS ABSENCE. The probe read
    # `protects against nothing else|offers nothing on` and matched the sentence about
    # UNMEASURED outcomes -- a different claim entirely. A loose probe scored a miss as a hit,
    # which is the mirror of a strict one scoring a hit as a miss and considerably worse,
    # because it reports coverage the page does not have.
    #
    # ⚠️ AND THE BAND IS NOT THE REFERENCE'S. The hand page says "It protects against nothing
    # else" flat; what the sources support is that no effect on other infections HAS BEEN SHOWN
    # -- the comparator reports them qualitatively and holds no figure for most. Stating the
    # weaker claim is the honest one.
    other_sti = [r for r in measured
                 if re.search(r"chlamyd|gonorrh|trichomon|syphilis|papillomavirus|herpes",
                              str(r.get("outcome") or ""), re.I)]
    if other_sti:
        said.append(("protects against nothing else",
                     "No protection against any other sexually transmitted infection has been "
                     "demonstrated: <b>%s</b> &mdash; every one either shows no effect or is "
                     "held only as a qualitative statement. ⚠️ This does not establish that "
                     "there is none; it establishes that none has been shown."
                     % _esc("; ".join(str(r.get("outcome")) for r in other_sti[:6]))))
    elif _topic_is_infection_prevention(measured, absent_rows):
        missing.append(("protects against nothing else",
                        "no other sexually transmitted infection outcome is recorded"))
    # ELSE: OUT OF SCOPE, AND SILENCE IS THE RIGHT OUTPUT. This `else` used to
    # be gated on nothing, so on every topic that is NOT an infection-prevention
    # review the regex above matched nothing and the branch asserted a fact
    # about sexually transmitted infections anyway. It reached 2 of the 2
    # non-STI pages this generator touched (SGLT2_HF, IV_IRON_HF). A claim that
    # does not apply to the topic is OMITTED -- reporting it as "missing" says
    # the page owes an answer it does not owe.

    if absent_rows:
        said.append(("what it is not",
                     "It offers nothing on: <b>%s</b> &mdash; recorded as not measured or not "
                     "reported in a usable form."
                     % _esc("; ".join(str(r.get("outcome")) for r in absent_rows[:6]))))
    else:
        missing.append(("what it is not", "no outcome is recorded as absent or not measurable"))

    # --- what the estimate is CONDITIONAL ON ---------------------------------------------------
    #
    # ⭐ A PROPERTY OF THE EVIDENCE, NOT A RECOMMENDATION. The hand-written reference says
    # "Condoms, STI screening and partner services remain necessary" -- which is advice, and a
    # review has no standing to give it. The trials RECORD that every participant received that
    # package, so the checkable claim is that the effect was measured ON TOP OF it and says
    # nothing about the intervention used INSTEAD of it. Same decision, sourced.
    for _oid, res in outs.items():
        if not isinstance(res, dict):
            continue
        bg = res.get("background_care")
        if isinstance(bg, dict) and bg.get("what"):
            said.append(("what it is conditional on",
                         "This effect was measured <b>on top of</b> %s, given to %s. It "
                         "describes the intervention ADDED to that care and says nothing about "
                         "it used instead of that care."
                         % (_esc(bg["what"]), _esc(bg.get("delivered_to", "both arms")))))
            break
    else:
        missing.append(("what it is conditional on",
                        "the object records no background care delivered alongside the "
                        "intervention, so this page cannot say what its estimate is on top of"))

    # --- efficacy in a trial versus effectiveness in use --------------------------------------
    #
    # ⛔ THE TYPED FIELD FIRST, THE TEXT SEARCH ONLY AS A FALLBACK. Reading "adherence" out of
    # a prose blob tells you the word occurs; it cannot tell you the RATE or the CONTACT
    # SCHEDULE, and those two are the whole reason effectiveness will differ from efficacy.
    ad = None
    for _oid, res in outs.items():
        if isinstance(res, dict) and isinstance(res.get("adherence"), dict):
            ad = res["adherence"]
            break
    if ad and ad.get("contact_schedule"):
        said.append(("efficacy versus use",
                     "Effectiveness in use will be lower than this. Adherence was measured, not "
                     "assumed — %s — and it was measured under %s. A service that does not "
                     "reproduce that contact should expect lower adherence and a smaller "
                     "effect: this is an efficacy under trial conditions, not an effectiveness "
                     "in use."
                     % (_esc(ad.get("rate_over_21") or "as recorded"),
                        _esc(ad["contact_schedule"]))))
    else:
        blob = " ".join(
            str(blk.get("basis", "")) + str(blk.get("external_corroboration", ""))
            for _o, res in outs.items() if isinstance(res, dict)
            for _f, blk in SE._blocks(res))
        if re.search(r"adherence", blob, re.I):
            said.append(("efficacy versus use",
                         "Effectiveness in use will be lower than this. The object records "
                         "adherence as the proposed explanation for the difference between "
                         "strata, but it does not record the adherence RATE or the contact "
                         "schedule, so this page cannot say by how much."))
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
    # ⭐ PARITY IS ASSERTED HERE, NOT ONLY MEASURED IN A REPORT. The target is that the
    # generated section carries every proposition the HAND-WRITTEN one carried, at no stronger a
    # hedge. Running it in the plant means parity cannot silently regress: a future edit that
    # drops a claim, or strengthens one, fails the component's own controls rather than being
    # noticed by a judge.
    # ⭐ PARITY IS ASSERTED HERE, AGAINST THE SIBLING LANE'S 16-CLAIM LEDGER.
    #
    # ⛔ THEIRS, NOT MINE, AND THE REASON MATTERS. My 12-claim ledger scored the generated page
    # against the REFERENCE's wording -- so it inherited the reference's defects and was
    # structurally blind to them. Theirs scores each claim against its SOURCE, which is why it
    # could see that the reference states a POST HOC subgroup flat while ASPIRE labels it.
    # A parity metric measured against an artefact can only ever reach that artefact's ceiling,
    # INCLUDING ITS ERRORS.
    #
    # ⚠️ THIS IS A RATCHET, NOT A TARGET. Recall sits at 11 of 16 and the five misses have been
    # hand-classified: four are the matcher keyed to the reference's WORDING where this page
    # uses the SOURCE's ("18 to 21 years" not "21 and under"; "grade 3/4" not "severe"; "1.6
    # years" not "18 months"), and one (C13) is a deliberate reframing of a recommendation into
    # a conditionality. ⛔ THE PAGE IS NOT REWORDED TO MATCH THE MATCHER -- that is writing
    # content for a detector. The floor stops a real regression; it does not chase the number.
    import json as _json
    import clinical_reading_claims as _CC
    FLOOR_RECALL, CEIL_LOST = 11, 3
    _obj = os.path.join(SSOT, "agyw-hiv-prep-review", "agyw-hiv-prep-review.json")
    if os.path.exists(_obj):
        _c = _json.load(io.open(_obj, encoding="utf-8"))
        _t = re.sub(r"<[^>]+>", " ", render(_c))
        _rows = _CC.score(_t)
        _recall = sum(1 for r in _rows if r["present"])
        _lost = [r for r in _rows if r["present"] and r["hedge_kept"] is False]
        print("")
        print("PARITY, under the 16-claim ledger (sibling lane's, adopted)")
        print("   recall %d of %d   hedges lost %d   [floor %d / ceiling %d]"
              % (_recall, len(_rows), len(_lost), FLOOR_RECALL, CEIL_LOST))
        print("   absent: %s" % ", ".join(r["id"] for r in _rows if not r["present"]))
        assert _recall >= FLOOR_RECALL, "claim recall regressed below the recorded floor"
        assert len(_lost) <= CEIL_LOST, "a hedge was dropped that was previously kept"
        print("   [PASS] no regression against the recorded floor")
    else:
        print("")
        print("   ⚠️ PARITY NOT CHECKED: the reference object is absent from this checkout,")
        print("      so this run says nothing about claim recall. Not a pass.")
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
