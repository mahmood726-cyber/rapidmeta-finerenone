"""ESTIMAND DEFINITION -- was each trial's endpoint READ, or was it assumed?

WHY THIS EXISTS -- IT CAUGHT WHAT EVERYTHING ELSE MISSED
    SGLT2_HF pooled four trials as one estimand and was live, carrying
    HR 0.7785 (0.7296-0.8306), k=4. It passed arm_identity, identity_by_
    registration, subject_match, card_matches_page, build_stamp,
    no_synthesised_absence, the whole regression set and the harness gate.

    And DAPA-HF and DELIVER count "CV death, HF hospitalisation, OR URGENT HF
    VISIT", while both EMPEROR trials count "CV death or HF hospitalisation"
    only. Two trials counted an event class the other two did not.

    THE OBJECT RECORDED NO PER-TRIAL ENDPOINT DEFINITION AT ALL. What it carried
    instead were RESULT sentences -- "the primary outcome occurred in 386 of 2373
    patients (16.3%) ... hazard ratio, 0.74" -- filed as provenance.

    A QUOTE THAT SAYS WHAT HAPPENED IS NOT A QUOTE THAT SAYS WHAT WAS COUNTED.
    That distinction withdrew a live four-trial estimate, and it is the only
    defect so far that survived every other check in this repository, including
    the ones written the same day.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the recorded definition is the trial's TRUE endpoint. It checks
      that one was recorded and that the recorded ones agree; only a registry
      read establishes truth, and this gate says when one is owed.
    - NOT that agreeing definitions license a pool. Populations, follow-up and
      analysis sets can still differ.
    - NOT anything about a single-trial object: nothing to compare, UNCHECKABLE.
"""
from __future__ import annotations
import io, json, os, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# A RESULT sentence reports an outcome's VALUE. A DEFINITION states what the
# outcome IS. These patterns are what a result looks like; matching one where a
# definition is owed is the SGLT2 defect exactly.
RESULT_SENTENCE = re.compile(
    r"occurred in\s+\d|hazard ratio[,:]?\s*[\d.]|"
    r"\d+\s+of\s+\d+\s+patients|\(\s*\d+\.\d+\s*%\s*\)|"
    r"95%\s*(?:confidence interval|CI)", re.I)

# Components that change what a composite counts. Compared as whole normalised
# fields, never as fragments -- the rule this repo broke inside its own auditor.
COMPONENT = re.compile(
    r"urgent(?:\s+\w+){0,3}\s+visit|hospitali[sz]ation|hospitali[sz]ed|"
    # A PARENTHETICAL ABBREVIATION BETWEEN THE TWO WORDS. Registries write
    # "cardiovascular (CV) death" and "heart failure (HF) hospitalization", and
    # the first of those matched NEITHER alternative here, so PARALLEL-HF's
    # correctly-recorded endpoint read as counting hospitalisation and no death
    # -- disagreeing with three trials that count exactly what it counts. The
    # under-read again, and again in the direction that argues for a withdrawal.
    r"cardiovascular\s*(?:\([^)]{0,12}\))?\s*death|cv death|"
    r"death(?:s)? from cardiovascular causes|"
    # "CV mortality" is how IRONMAN's registry writes the component that
    # AFFIRM-AHF's writes as "CV Death". Neither the death nor the
    # from-cardiovascular-causes alternative reaches it, so a correctly-recorded
    # IRONMAN definition read as carrying NO cardiovascular-death component and
    # the two trials appeared to count different things. Same family as
    # "deaths from cardiovascular causes" on SOTAGLIFLOZIN: an under-read
    # manufactures a disagreement exactly as an over-read manufactures an
    # agreement, and the first argues for withdrawing a sound estimate.
    r"(?:cardiovascular|cv) mortality|"
    r"all-cause (?:death|mortality)|(?:death|mortality) from any cause|"
    r"any-cause (?:death|mortality)|total mortality|"
    # ABLATION_AF, 2026-08-17. CABANA's registry endpoint is "Total Mortality,
    # Disabling Stroke, Serious Bleeding, or Cardiac Arrest" and this reader saw
    # ONE of those four: stroke. Three whole components of a composite were
    # invisible, so an object pairing CABANA with a stroke-only trial would have
    # been reported as counting the same events. That is the comfortable
    # direction and it was sitting in a live object.
    r"serious bleeding|major bleeding|cardiac arrest|acute coronary syndrome|"
    # DOAC_AF, 2026-08-18. Four registry records, four composites, every one of
    # them "stroke OR systemic embolism" -- and this reader saw ONE of the two.
    # Half of every composite in the topic was invisible, and the gate reported
    # PASS "they agree" from a reading of the other half. Same shape as CABANA
    # above and same shape as the CKD false agreement, in a third vocabulary.
    r"non-?cns systemic embolism|systemic embolic events?|"
    r"systemic emboli[sz]ation|systemic embolism|systemic emboli|"
    r"myocardial infarction|stroke|worsening heart failure", re.I)

# "WORSENING HEART FAILURE" IS USUALLY A QUALIFIER, NOT A COMPONENT.
#
# "hospitalisation for worsening heart failure" names ONE counted event. Read as
# two matches it added a phantom component, and that alone made EMPEROR-Reduced
# ("cardiovascular death or hospitalization for worsening heart failure") differ
# from EMPEROR-Preserved ("cardiovascular death or hospitalization for heart
# failure") -- two trials that count the same thing, separated by one word of
# orthography. The same phantom separated AFFIRM-AHF from IRONMAN.
#
# Two shapes, and the attached one must be stripped FIRST or the umbrella
# pattern swallows a parenthesis that merely mentions hospitalisations:
#   attached  "<hospitalisation|admission|visit> [for|due to] worsening heart failure"
#   umbrella  "worsening heart failure (<...enumerating hospitalisation or visit...>)"
# Anything else -- a standalone worsening-heart-failure event, which some trials
# really do count separately -- still yields its own component.
_WORSENING_ATTACHED = re.compile(
    r"\b(hospitali[sz]\w*|admission\w*|admitted|visits?)"
    r"(?:\s+(?:for|due to|because of))?\s+worsening\s+heart\s+failure", re.I)
# AND THE SAME PHRASE WITH THE WORDS THE OTHER WAY ROUND. CASTLE-AF's registry
# endpoint is "worsening heart failure REQUIRING UNPLANNED HOSPITALIZATION", which
# the attached pattern cannot see because the qualifier comes first. One counted
# event read as two, on a live object -- the EMPEROR over-read in mirror image,
# found the same day the first half was fixed.
_WORSENING_LEADING = re.compile(
    r"\bworsening\s+heart\s+failure\s+(?:requiring|leading to|resulting in)"
    r"(?:\s+\w+){0,2}\s+(hospitali[sz]\w*|admission\w*)", re.I)
_WORSENING_UMBRELLA = re.compile(
    r"\bworsening\s+heart\s+failure\s*(?=\([^)]*(?:hospitali|visit))", re.I)


def _norm(s):
    return re.sub(r"[^a-z0-9 ]+", " ", re.sub(r"\s+", " ", (s or "").lower())).strip()


# CANONICAL KEYS, not raw matched text. The first cut compared normalised match
# strings and failed its own negative control, because "hospitalisation" and
# "hospitalization" normalise to different tokens -- the British-spelling trap in
# a new costume, and a gate that fails on everything is worth nothing. Each match
# now maps to ONE key, so orthography cannot manufacture a difference and only a
# real component change can.
_CANON = (
    (re.compile(r"urgent", re.I), "urgent_visit"),
    (re.compile(r"hospitali", re.I), "hf_hospitalisation"),
    # PHRASING VARIANTS MAP TO ONE KEY. "deaths from cardiovascular causes" is the
    # same component as "cardiovascular death" and matched neither pattern, so a
    # correctly-recorded SOTAGLIFLOZIN definition read as carrying no CV-death
    # component. Under-reading manufactures disagreements exactly as over-reading
    # does, and a withdrawal needs the same evidentiary standard as a claim.
    # THE PARENTHETICAL HAS TO BE ALLOWED HERE TOO. COMPONENT finds the phrase
    # and this table classifies it; widening one without the other means the
    # match is found and then silently DROPPED, assigned to no key at all, which
    # is indistinguishable from not finding it. Two places, one fact -- and the
    # first fix touched only one of them.
    (re.compile(r"(cardiovascular|cv)\s*(?:\([^)]{0,12}\))?\s*death|"
                r"death.{0,3} from cardiovascular", re.I), "cv_death"),
    (re.compile(r"all-cause|any-cause|from any cause|total mortality", re.I),
     "all_cause_death"),
    (re.compile(r"serious bleeding|major bleeding", re.I), "serious_bleeding"),
    (re.compile(r"cardiac arrest", re.I), "cardiac_arrest"),
    (re.compile(r"acute coronary syndrome", re.I), "acs"),
    (re.compile(r"(cardiovascular|cv) mortality", re.I), "cv_death"),
    (re.compile(r"myocardial infarction", re.I), "mi"),
    # ONE KEY FOR ALL FOUR PHRASINGS, and the reason is written down because
    # this is exactly the kind of judgement that manufactures an agreement if
    # it is wrong. RE-LY writes "systemic embolic event", ARISTOTLE "Systemic
    # Embolism", ENGAGE "Systemic Embolic Events", ROCKET AF "non-CNS systemic
    # embolism". The "non-CNS" is a clarification rather than a narrowing: an
    # embolus reaching the brain is counted by all four as STROKE, which is the
    # other arm of the same composite, so the non-CNS qualifier removes nothing
    # the other three records count. Four descriptions, one event.
    # SPLITTING THEM WOULD MANUFACTURE A DISAGREEMENT between four trials that
    # count the same thing -- the destructive direction, because it argues for
    # withdrawing a sound estimate.
    (re.compile(r"systemic embol", re.I), "systemic_embolism"),
    (re.compile(r"stroke", re.I), "stroke"),
    (re.compile(r"worsening heart failure", re.I), "worsening_hf"),
)


def _components(s):
    s = _WORSENING_ATTACHED.sub(lambda m: m.group(1), s or "")
    s = _WORSENING_LEADING.sub(lambda m: m.group(1), s)
    s = _WORSENING_UMBRELLA.sub("", s)
    out = set()
    for m in COMPONENT.finditer(s or ""):
        raw = m.group(0)
        for rx, key in _CANON:
            if rx.search(raw):
                out.add(key)
                break
    return frozenset(out)


# ---------------------------------------------------------------------------
# THE HUNTING LIST -- and why this gate needed a SECOND list rather than a
# LONGER first one.
#
# COMPONENT and _CANON are entirely CARDIOLOGICAL: hospitalisation, CV death,
# stroke, MI, bleeding, cardiac arrest, ACS, worsening heart failure. There is
# nothing renal in them, nothing infectious, nothing oncological.
#
# On 2026-08-18 this gate was run on SGLT2_CKD, whose three trials record three
# DIFFERENT primary composites in their own registry records:
#
#   CREDENCE     doubling of serum creatinine, ESKD, renal or CV death
#   DAPA-CKD     >=50% sustained decline in eGFR, ESRD, CV death, renal death
#   EMPA-KIDNEY  kidney disease progression (ESKD, eGFR to <10, renal death,
#                >=40% sustained decline in eGFR) or CV death
#
# ALL THREE REDUCED TO {cv_death}. Every renal component of every composite was
# invisible, and the gate reported "every pooled outcome has a recorded endpoint
# definition and THEY AGREE" -- a PASS, on three composites that differ on the
# threshold at which kidney-function decline is counted at all.
#
# THIS IS THE CABANA DEFECT AND IT FAILS TOWARD COMFORT. CABANA's four-component
# endpoint was read as "stroke", and that argued for pooling it with a
# stroke-only trial. Here five components are read as one, and it argues for
# pooling three composites that are not the same. Every other under-read in the
# ledger failed toward ALARM; this one manufactures an AGREEMENT, which is the
# direction that survives, because nobody investigates a green.
#
# LENGTHENING _CANON DOES NOT FIX IT. A recognition list over an open domain is
# wrong again the first time this gate meets a specialty nobody added -- and the
# whole infectious-disease set is next. So the fix is structural:
#
#     THE RECOGNITION LIST DECIDES PASS.
#     THIS LIST DECIDES WHETHER THE GATE MAY DECIDE AT ALL.
#
# EVENT_LIKE is deliberately over-broad. Its failure mode is flagging a term the
# recognition list actually handles, which yields UNCHECKABLE -- an alarm, and a
# cheap one to investigate. A gap in THIS list is one level further back than a
# gap in _CANON, and it is the only comfortable failure left in the design.
EVENT_LIKE = re.compile(
    r"\b(?:"
    # renal -- the set that was invisible
    r"creatinine|egfr|glomerular filtration|dialysis|transplantation|transplant|"
    r"end[- ]stage|eskd|esrd|kidney disease progression|kidney failure|"
    r"renal death|renal failure|renal replacement|albuminuria|proteinuria|"
    r"nephropathy|"
    # progression / decline language that names a counted event
    r"doubling|sustained decline|disease progression|progression-free|"
    # other specialties, so this is not merely cardiology-plus-renal
    r"relapse|remission|recurrence|exacerbation|infection|bacteraemia|"
    r"bacteremia|seroconversion|viral load|virologic failure|virological "
    r"failure|treatment failure|fracture|amputation|blindness|visual acuity|"
    r"overall survival|readmission|intubation|ventilation|transfusion|"
    r"revascularisation|revascularization|graft loss|rejection|"
    # the term whose absence let this list fail at the job it exists for
    r"systemic embol[a-z]*|embolism|embolic|thromboembolism|"
    r"venous thromboembolism|pulmonary embolism|deep vein thrombosis"
    r")\b", re.I)


def unrecognised_terms(s):
    """Event-like phrases in a definition that the recognition list cannot see.

    A NON-EMPTY RESULT MEANS THE GATE MUST NOT COMPARE THIS DEFINITION. It has
    read part of a composite and has no way to know whether the part it could
    not read is the part that differs.
    """
    if not s:
        return frozenset()
    covered = " ".join(m.group(0) for m in COMPONENT.finditer(s)).lower()
    return frozenset(m.group(0).lower() for m in EVENT_LIKE.finditer(s)
                     if m.group(0).lower() not in covered)


def definition_for(bo):
    """The endpoint definition recorded on ONE trial-outcome cell, or "".

    THE ONE PLACE THIS LOGIC LIVES. `poolability` reported "N of N trials carry
    no outcome definition" on every SSOT object in the repository, because it
    read a field only the extraction schema has. That is a FALSE ALARM, and a
    false alarm here is not the safe direction: it argues for withdrawing a
    correct estimate, and a withdrawal needs the same evidentiary standard as a
    claim. Rather than copy the resolution into a second gate -- two copies
    diverge, and the divergence is invisible -- both callers use this.

    Order: the explicit field, then a provenance quote that is a DEFINITION
    rather than a RESULT. The second half is what lets an object that quotes the
    registry's outcome-measure title pass without also passing an object whose
    provenance is "the primary outcome occurred in 386 of 2373 patients".
    """
    if not isinstance(bo, dict):
        return ""
    d = (bo.get("outcome_definition") or bo.get("definition")
         or bo.get("endpoint_definition") or "")
    if d:
        # A TITLE CAN BE A LABEL RATHER THAN A DEFINITION, and then the
        # DESCRIPTION is where the components live. PARALLEL-HF's registry title
        # is "Number of Participants Who Had CEC Confirmed Composite Endpoints"
        # -- which names no event at all -- while its description says "either
        # cardiovascular (CV) death or heart failure (HF) hospitalization". Read
        # from the title alone the trial appeared to count NOTHING, and a trial
        # counting nothing disagrees with every trial that counts something. The
        # recorded definition is both fields, because that is what was read.
        desc = (bo.get("outcome_definition_source") or {}).get(
            "description_verbatim")
        return "%s %s" % (d, desc) if desc else d
    quotes = (bo.get("provenance") or {}).get("source_quotes") or []
    cand = [q for q in quotes if not RESULT_SENTENCE.search(q) and _components(q)]
    return max(cand, key=len) if cand else ""


def check(obj):
    trials = ((obj.get("inputs") or {}).get("trials")) or []
    results = ((obj.get("results") or {}).get("by_outcome")) or {}
    if not trials or not results:
        return "UNCHECKABLE", ["object carries no trials or no pooled outcome"]

    notes, bad, withdrawn_for_this = [], False, False
    unreadable_for_this = False
    for oid, res in results.items():
        if (res.get("k") or 0) < 2:
            notes.append("%s: k<2, nothing to compare" % oid)
            continue
        # A POOL ALREADY WITHDRAWN FOR THIS EXACT REASON IS THE PROPERTY MET.
        #
        # ABLATION_AF's four trials record four different primary composites, and
        # its estimate is withdrawn WITH that as the stated reason. Scoring it
        # FAIL made a page that found the difference and acted on it
        # indistinguishable from a page that pooled straight through -- which is
        # SGLT2_HF, whose object still carries a live k=4 point. A score that
        # cannot tell those two apart cannot measure the thing it is for.
        #
        # This is NOT an escape hatch: a withdrawn pool displays no number, so
        # there is nothing left for a mismatched estimand to be wrong about. A
        # LIVE pool with disagreeing definitions still FAILs, which is the
        # constructible failure and the SGLT2 replay.
        _p = res.get("pooled") or {}
        _withdrawn = (_p.get("point") is None and _p.get("withdrawn")
                      and (_p.get("withdrawn_reason") or "").strip())
        defs, missing, resultish = {}, [], []
        for t in trials:
            bo = (t.get("by_outcome") or {}).get(oid)
            if not bo:
                continue
            name = t.get("name") or t.get("nct") or "?"
            # A QUOTE CAN BE THE DEFINITION -- that is the whole distinction, and
            # it is resolved in definition_for() so poolability cannot drift from
            # it. FINERENONE_CV stores each trial's endpoint TITLE, read word for
            # word from the registry, in source_quotes. SGLT2_HF stores RESULT
            # sentences in the same field. Failing both would mean the gate
            # cannot tell the work done right from the work done wrong, which is
            # the property it exists to measure.
            d = definition_for(bo)
            quotes = (bo.get("provenance") or {}).get("source_quotes") or []
            if not d:
                missing.append(name)
                if quotes and RESULT_SENTENCE.search(" ".join(quotes)):
                    resultish.append(name)
            else:
                defs[name] = d
        if missing:
            if _withdrawn:
                withdrawn_for_this = True
            else:
                bad = True
            notes.append("%s: NO endpoint definition recorded for %d trial(s): %s"
                         % (oid, len(missing), ", ".join(missing[:6])))
            if resultish:
                notes.append("    and the provenance quote is a RESULT sentence on "
                             "%d of them: %s -- what happened, never what was counted"
                             % (len(resultish), ", ".join(resultish[:6])))
        if len(defs) > 1:
            # BEFORE COMPARING ANYTHING: can this reader read these definitions?
            # A comparison of two partial readings is not a comparison of two
            # definitions. If the recognition vocabulary cannot see event-like
            # terms that are present in the text, the honest verdict is that the
            # gate could not read them -- NOT that they agree.
            blind = {n: unrecognised_terms(d) for n, d in defs.items()}
            unread = {n: t for n, t in blind.items() if t}
            if unread:
                unreadable_for_this = True
                notes.append(
                    "%s: THIS GATE CANNOT READ %d of %d definitions. Its component "
                    "vocabulary is cardiological and these name events it does not "
                    "recognise, so any agreement it reported would be an agreement "
                    "between two PARTIAL READINGS:" % (oid, len(unread), len(defs)))
                for n in sorted(unread):
                    notes.append("    %-22s unrecognised: {%s}   recognised: {%s}"
                                 % (n, ", ".join(sorted(unread[n])[:8]),
                                    ", ".join(sorted(_components(defs[n]))) or "-"))
                notes.append("    Read these by hand against the registry. A PASS "
                             "here would be the CABANA under-read failing toward "
                             "comfort instead of toward alarm.")
                continue
            comp = {n: _components(d) for n, d in defs.items()}
            if len(set(comp.values())) > 1:
                if _withdrawn:
                    withdrawn_for_this = True
                else:
                    bad = True
                notes.append("%s: recorded definitions DISAGREE across trials%s:"
                             % (oid, " -- AND THE ESTIMATE IS WITHDRAWN, WITH THIS "
                                     "AS ITS STATED REASON" if _withdrawn else ""))
                for n, c in comp.items():
                    notes.append("    %-22s counts {%s}"
                                 % (n, ", ".join(sorted(c)) or "-"))
    if not notes:
        notes = ["every pooled outcome has a recorded endpoint definition and they agree"]
    if bad:
        return "FAIL", notes
    # UNCHECKABLE OUTRANKS WITHDRAWN AND PASS. If the gate could not read the
    # definitions it cannot certify that a withdrawal was for the right reason
    # either -- and a withdrawal made on an unread definition is exactly the
    # destructive error this whole apparatus exists to prevent.
    if unreadable_for_this:
        notes.append("-> UNCHECKABLE. The gate found event terms it does not "
                     "recognise and refuses to report agreement or disagreement "
                     "from a partial reading. This is NOT a pass and NOT a "
                     "failure of the object.")
        return "UNCHECKABLE", notes
    if withdrawn_for_this:
        notes.append("-> the definitions do not agree and NO ESTIMATE IS DISPLAYED. "
                     "The property is met by the withholding, not by agreement, and "
                     "this is recorded as WITHDRAWN rather than passed.")
        return "WITHDRAWN", notes
    return "PASS", notes


def selftest():
    """REPLAYED AGAINST SGLT2_HF's OWN OBJECT -- four trials, two definitions,
    and it was passing every other check we own."""
    ok = True
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    real = os.path.join(root, "ssot", "sglt2-hf", "sglt2-hf.json")
    if os.path.exists(real):
        obj = json.loads(open(real, encoding="utf-8").read())
        # THE POSITIVE CONTROL IS THE STATE THIS OBJECT WAS IN, NOT THE STATE IT
        # IS IN NOW. Its pool has since been withdrawn IN THE OBJECT, so the live
        # object correctly returns WITHDRAWN. Restoring the point from the
        # `previous_values` that the withdrawal preserved replays the exact
        # historical artefact -- four trials, two endpoint definitions, a live
        # k=4 estimate. Without this, remediating the defect would have quietly
        # deleted the only real past defect this gate is proved against, and the
        # selftest would have gone on printing PASS over a control that no longer
        # controls anything.
        for _res in ((obj.get("results") or {}).get("by_outcome") or {}).values():
            _p = _res.get("pooled") or {}
            if _p.get("withdrawn") and _p.get("previous_values"):
                _res["pooled"] = dict(_p["previous_values"][0])
        v, notes = check(obj)
        good = v == "FAIL"
        ok &= good
        print("  POSITIVE SGLT2_HF, pool restored from its own withdrawal record "
              "-> %-5s %s" % (v, "correct" if good else "WRONG"))
        for n in notes[:2]:
            print("        %s" % n[:112])
        v_now, _ = check(json.loads(open(real, encoding="utf-8").read()))
        ok &= v_now == "WITHDRAWN"
        print("  NEGATIVE SGLT2_HF as it stands today, pool withdrawn -> %-9s %s"
              % (v_now, "correct" if v_now == "WITHDRAWN" else "WRONG"))
    else:
        print("  fixture absent: sglt2-hf object -- NOT PROVEN")
        ok = False

    clean = {"inputs": {"trials": [
        {"name": "A", "by_outcome": {"o": {"outcome_definition":
         "cardiovascular death or hospitalisation for heart failure"}}},
        {"name": "B", "by_outcome": {"o": {"outcome_definition":
         "cardiovascular death or hospitalization for heart failure"}}}]},
        "results": {"by_outcome": {"o": {"k": 2}}}}
    v2, _ = check(clean)
    ok &= v2 == "PASS"
    print("  NEGATIVE same definition, spelling aside            -> %-5s %s"
          % (v2, "correct" if v2 == "PASS" else "WRONG"))

    mixed = json.loads(json.dumps(clean))
    mixed["inputs"]["trials"][1]["by_outcome"]["o"]["outcome_definition"] = (
        "cardiovascular death, hospitalisation for heart failure, or urgent "
        "heart failure visit")
    v3, _ = check(mixed)
    ok &= v3 == "FAIL"
    print("  POSITIVE one trial adds an urgent-visit component   -> %-5s %s"
          % (v3, "correct" if v3 == "FAIL" else "WRONG"))

    resultish = {"inputs": {"trials": [
        {"name": "A", "by_outcome": {"o": {"provenance": {"source_quotes": [
            "the primary outcome occurred in 386 of 2373 patients (16.3%) "
            "(hazard ratio, 0.74; 95% CI 0.65-0.85)"]}}}},
        {"name": "B", "by_outcome": {"o": {"provenance": {"source_quotes": [
            "a primary outcome event occurred in 361 of 1863 patients"]}}}}]},
        "results": {"by_outcome": {"o": {"k": 2}}}}
    v4, notes4 = check(resultish)
    ok &= v4 == "FAIL" and any("RESULT sentence" in n for n in notes4)
    print("  POSITIVE result sentences filed as provenance       -> %-5s %s"
          % (v4, "correct" if v4 == "FAIL" else "WRONG"))

    fin = os.path.join(root, "ssot", "finerenone-cv", "finerenone-cv.json")
    if os.path.exists(fin):
        v6, n6 = check(json.loads(open(fin, encoding="utf-8").read()))
        ok &= v6 == "PASS"
        print("  NEGATIVE FINERENONE_CV: endpoint TITLES quoted -> %-5s %s"
              % (v6, "correct" if v6 == "PASS" else "WRONG -- the gate cannot tell "
                 "a definition quote from a result quote"))

    # THE CANON ITSELF, on real registry text. Each of these read WRONG before
    # 2026-08-17 and each wrong reading manufactured a disagreement between
    # trials that count the same events -- the direction that argues for
    # withdrawing a sound estimate.
    print("")
    canon_cases = [
        ("AFFIRM-AHF primary, registry",
         "HF Hospitalizations and CV Death", {"cv_death", "hf_hospitalisation"}),
        ("IRONMAN primary, registry -- 'CV mortality', and a qualifier not a "
         "component",
         "CV mortality or hospitalisation for worsening heart failure (analysis "
         "will include first and recurrent hospitalisations)",
         {"cv_death", "hf_hospitalisation"}),
        ("EMPEROR-Reduced: 'hospitalization for WORSENING heart failure'",
         "a composite of cardiovascular death or hospitalization for worsening "
         "heart failure", {"cv_death", "hf_hospitalisation"}),
        ("EMPEROR-Preserved: the same events, one word apart",
         "a composite of cardiovascular death or hospitalization for heart "
         "failure", {"cv_death", "hf_hospitalisation"}),
        ("DAPA-HF: the umbrella phrase enumerates its own contents",
         "a composite of worsening heart failure (hospitalization or an urgent "
         "visit resulting in intravenous therapy for heart failure) or "
         "cardiovascular death",
         {"cv_death", "hf_hospitalisation", "urgent_visit"}),
        ("a STANDALONE worsening-HF event still counts as its own component",
         "a composite of cardiovascular death or a worsening heart failure event "
         "treated in the outpatient setting", {"cv_death", "worsening_hf"}),
        ("CONFIRM-HF: the publication's own words for the death row",
         "all-cause death, analysed as time to first event", {"all_cause_death"}),
        # ABLATION_AF: four endpoints that must come out DIFFERENT, and three of
        # the four had components this reader could not see at all.
        ("CASTLE-AF: the qualifier BEFORE the hospitalisation, not after",
         "All-cause mortality or worsening heart failure requiring unplanned "
         "hospitalization", {"all_cause_death", "hf_hospitalisation"}),
        ("CABANA: three of its four components were invisible",
         "Number of Participants With Composite of Total Mortality, Disabling "
         "Stroke, Serious Bleeding, or Cardiac Arrest in Patients Warranting "
         "Therapy for AF.",
         {"all_cause_death", "stroke", "serious_bleeding", "cardiac_arrest"}),
        ("EAST-AFNET 4: acute coronary syndrome was invisible",
         "A composite of cardiovascular death, stroke and hospitalization due to "
         "worsening of heart failure or due to acute coronary syndrome.",
         {"cv_death", "stroke", "hf_hospitalisation", "acs"}),
        ("RAFT-AF: all-cause mortality and heart failure events",
         "Composite of All-cause Mortality and Heart Failure Events",
         {"all_cause_death"}),
    ]
    for label, text, want in canon_cases:
        got = set(_components(text))
        good = got == want
        ok &= good
        print("  CANON %-62s %s" % (label[:62], "correct" if good else
                                    "WRONG: %s" % sorted(got)))
    print("")

    v5, _ = check({})
    ok &= v5 == "UNCHECKABLE"
    print("  NEGATIVE an empty object                            -> %-5s %s (not a pass)"
          % (v5, "correct" if v5 == "UNCHECKABLE" else "WRONG"))

    # ---- THE REPLAY: three CKD composites this gate reported as AGREEING ----
    # Real registry text, read 2026-08-18 from the ClinicalTrials.gov protocol
    # records. Before the hunting list, all three reduced to {cv_death} and the
    # gate returned PASS with "they agree".
    print("")
    ckd = {
        "CREDENCE": ("Primary Composite Endpoint of Doubling of Serum Creatinine "
                     "(DoSC), End-stage Kidney Disease (ESKD), and Renal or "
                     "Cardiovascular (CV) Death"),
        "DAPA-CKD": ("Time to the First Occurrence of Any of the Components of the "
                     "Composite: >=50% Sustained Decline in eGFR or Reaching ESRD "
                     "or CV Death or Renal Death."),
        "EMPA-KIDNEY": ("Interventional Part: Time to First Occurrence of Kidney "
                        "Disease Progression or Cardiovascular Death "
                        "('as Adjudicated')"),
    }
    same = len({_components(v) for v in ckd.values()}) == 1
    unread = {n: unrecognised_terms(v) for n, v in ckd.items()}
    all_flagged = all(unread.values())
    ok &= same and all_flagged
    print("  REPLAY SGLT2_CKD: three DIFFERENT composites, recognition list sees")
    for n, v in ckd.items():
        print("        %-12s recognised={%s}  unrecognised={%s}"
              % (n, ", ".join(sorted(_components(v))) or "-",
                 ", ".join(sorted(unread[n])[:5])))
    print("        all three reduce to one component set: %s  (that is the false "
          "agreement)" % same)
    print("        every one flagged as unreadable: %-5s %s"
          % (all_flagged, "correct" if (same and all_flagged) else "WRONG"))
    print("        the version this replaces returned PASS -- 'every pooled outcome "
          "has a recorded")
    print("        endpoint definition and they agree' -- on these exact strings.")

    # AND THE HUNTING LIST MUST NOT FLAG A CARDIOLOGY DEFINITION IT CAN READ.
    # A gate that returns UNCHECKABLE on everything is worth nothing; this is
    # the negative control for the new branch.
    card = ("Cardiovascular death or hospitalization for heart failure",
            "cardiovascular (CV) death or heart failure (HF) hospitalization",
            "Total Mortality, Disabling Stroke, Serious Bleeding, or Cardiac Arrest")
    clean = all(not unrecognised_terms(c) for c in card)
    ok &= clean
    # ------------------------------------------------ DOAC_AF, 2026-08-18
    # SYSTEMIC EMBOLISM WAS INVISIBLE TO ALL THREE LISTS. Four registry
    # composites, every one "stroke OR systemic embolism", and _components()
    # returned frozenset({'stroke'}) for each -- so the gate compared HALF of
    # every composite in the topic and reported that they agreed.
    #
    # It was not caught by EVENT_LIKE either, and that is the part that matters:
    # EVENT_LIKE exists to force UNCHECKABLE whenever the recognition list meets
    # a term it cannot handle, and TOOLING-QUEUE.md recorded that mechanism as
    # the reason "the gate can no longer report agreement from a partial
    # reading". The net had the same hole as the thing it was netting.
    #
    # THE WIDENING MOVED NO VERDICT ON ANY OBJECT IN THE REPOSITORY. DOAC_AF was
    # PASS before and PASS after, because its four composites really do agree.
    # So the only thing that can demonstrate the fix is a pair that differs ONLY
    # in the half that used to be unreadable. Old gate: PASS. New gate: FAIL.
    _doac = {"inputs": {"trials": [
        {"name": "A", "nct": "NCT1",
         "by_outcome": {"o": {"outcome_definition": "Stroke or systemic embolism"}}},
        {"name": "B", "nct": "NCT2",
         "by_outcome": {"o": {"outcome_definition": "Stroke"}}}]},
        "results": {"by_outcome": {"o": {"k": 2, "pooled": {"point": 0.8}}}}}
    _v = check(_doac)[0]
    _good = _v == "FAIL"
    ok &= _good
    print("\n  REPLAY DOAC_AF: two composites differing ONLY in the embolism half")
    for _n, _t in (("RE-LY      ", "Time to first occurrence of stroke or systemic embolic event."),
                   ("ROCKET AF  ", "the first occurrence of a stroke or non-CNS systemic embolism"),
                   ("ARISTOTLE  ", "First Event of Ischemic/Unspecified Stroke, Hemorrhagic Stroke, or Systemic Embolism"),
                   ("ENGAGE     ", "The composite of stroke and Systemic Embolic Events (SEE)")):
        print("        %s reads %s" % (_n, sorted(_components(_t))))
    print("        'stroke or systemic embolism' vs 'stroke' -> %s  %s"
          % (_v, "correct" if _good else "WRONG"))
    print("        the version this replaces returned PASS on that pair -- it could "
          "not see\n        the component that is the entire difference.")

    print("\n  NEGATIVE CONTROL cardiology definitions stay readable -> %-5s %s"
          % (clean, "correct" if clean else
             "WRONG: %s" % [sorted(unrecognised_terms(c)) for c in card]))

    print("\nWHAT A FAILURE WOULD LOOK LIKE: SGLT2_HF passing -- which it did on "
          "every other check in this repository while pooling two different "
          "endpoints as one.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    if not os.path.exists(sys.argv[1]):
        print("estimand_definition: %s does not exist. NOT RUN." % sys.argv[1],
              file=sys.stderr)
        return 2
    v, notes = check(json.loads(open(sys.argv[1], encoding="utf-8",
                                     errors="replace").read()))
    for n in notes:
        print("  %s" % n)
    print("  -> %s" % v)
    # FOUR STATES, FOUR EXIT CODES, because a caller that maps three of them onto
    # "PASS" cannot report what it measured. 0 PASS, 1 FAIL, 2 UNCHECKABLE (ran,
    # could not see -- not a pass), 3 WITHDRAWN (the definitions disagree AND no
    # estimate is displayed, so the property is met by the withholding). A
    # distinct CODE rather than a word in the output, so no caller has to
    # substring-search for it -- which is the over-match this repository has now
    # committed three times.
    return {"PASS": 0, "FAIL": 1, "UNCHECKABLE": 2, "WITHDRAWN": 3}.get(v, 1)


if __name__ == "__main__":
    sys.exit(main())
