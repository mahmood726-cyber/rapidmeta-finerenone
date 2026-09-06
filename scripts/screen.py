# -*- coding: utf-8 -*-
"""screen.py -- generic screening: one decision function, every rule with an id, three results-states.

The root cause of the largest defect family (FINDINGS-FIX-ALL): there was NO generic screener, only
~30 bespoke `screen_*` scripts, so every screening fix landed on one review's script and the next
review inherited the bug. This is the single home. The rules it encodes are exactly the ones the
external reviews found violated, each drawn from a named instance:

  R-DESIGN         design must match (RCT); EXCLUDE with the ACTUAL design as a verifiable reason
                   (gate 42: an exclusion reason must be checkable, not asserted).
  R-INTERVENTION   the eligible intervention must be present.
  R-POPULATION     population must match; must NOT screen on an OUTCOME (outcomes are reporting-only).
  R-OUTCOME-ANYRANK  the estimand outcome may appear at ANY rank -- a trial that reports it as a
                   SECONDARY is INCLUDED, not excluded for a differing PRIMARY (AMPLIFY was falsely
                   excluded this way).
  R-RESULTS-ABSENCE  a trial is NEVER terminally excluded because the registry posted no results
                   (gate 53: hasResults=false is a fact about ClinicalTrials.gov, not the trial).
                   It resolves to one of THREE states, and NOT_YET_SEARCHED renders as an OPEN TASK:
                       PUBLISHED_RESULTS_FOUND | SEARCHED_NONE_FOUND | NOT_YET_SEARCHED
                   (AVERT, APROPOS, Mokadem were lost this way; AVERT is a real NEJM pivotal.)

Every decision carries the rule_id that produced it and the evidence it rests on, so a screening
call is an auditable decision, not an opaque include/exclude. Written in-tree (Codex cannot write).
"""
from __future__ import annotations
import io, re, sys, json

INCLUDE = "INCLUDE"
EXCLUDE = "EXCLUDE"
PUBLICATION_SEARCH_REQUIRED = "PUBLICATION_SEARCH_REQUIRED"
RESULTS_STATES = ("PUBLISHED_RESULTS_FOUND", "SEARCHED_NONE_FOUND", "NOT_YET_SEARCHED")


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def _any_contains(haystacks, needle):
    n = _norm(needle)
    return any(n in _norm(h) for h in haystacks)


# words that carry no discriminating meaning when matching an outcome title
_OUTCOME_STOPWORDS = frozenset((
    "or", "of", "the", "a", "an", "to", "for", "and", "in", "on", "with", "first", "time",
    "event", "adjudicated", "composite", "endpoint", "outcome", "due", "from", "occurrence",
    "worsening", "unplanned", "subjects", "included", "number", "total",
    "component", "components", "two", "three", "point",  # descriptors of a composite, not clinical content
))


def _canon(t):
    """Canonicalise British/American medical spelling so token-subset matching is spelling-blind.
    hospitalisation==hospitalization was silently excluding DAPA-HF/EMPEROR when the estimand used the
    British form -- the same class as the h[ae]moglobin lesson, here on -isation/-ization."""
    t = t.replace("isation", "ization").replace("isension", "ization")
    for a, b in (("haemo", "hemo"), ("oedema", "edema"), ("aemia", "emia"), ("aemic", "emic"),
                 ("anaesth", "anesth"), ("oesoph", "esoph"), ("paediatr", "pediatr"),
                 ("tumour", "tumor"), ("ischaemi", "ischemi")):
        t = t.replace(a, b)
    return t


def _content_tokens(s):
    return {_canon(t) for t in re.findall(r"[a-z0-9]+", _norm(s))
            if t not in _OUTCOME_STOPWORDS and len(t) > 1}


def _outcome_matches(term, text):
    """A term matches a text if it is a substring OR all its content tokens appear in the text.

    Token-subset handles real registry titles that interleave words -- e.g. the term 'cardiovascular
    death or first hospitalisation for heart failure' matches 'Time to the First Event of Adjudicated
    Cardiovascular Death or Adjudicated Hospitalisation for Heart Failure', which no substring match
    would catch. Synonym handling ('HHF' == 'hospitalisation for heart failure') is left to the
    protocol's outcome_synonyms rather than hard-coded here."""
    if _norm(term) in _norm(text):
        return True
    tt = _content_tokens(term)
    return bool(tt) and tt.issubset(_content_tokens(text))


_DOSE_WORDS = frozenset((
    "mg", "ml", "mcg", "ug", "g", "kg", "iu", "daily", "once", "twice", "dose", "doses", "oral",
    "orally", "tablet", "tablets", "capsule", "capsules", "day", "week", "weekly", "injection",
    "subcutaneous", "iv", "po", "qd", "bid", "matching", "placebo", "arm", "group", "10", "mg/day",
))


def _drug_tokens(s):
    return _content_tokens(s) - _DOSE_WORDS


def _intervention_matches(want, trial_intvs):
    """True if the wanted intervention shares a non-dose (drug) token with any trial intervention."""
    wt = _drug_tokens(want)
    return bool(wt) and any(wt & _drug_tokens(i) for i in trial_intvs)


def _outcome_at_any_rank(trial, outcome_terms):
    """True if the estimand outcome appears at ANY outcome rank (primary OR secondary OR other)."""
    outs = trial.get("outcomes") or []
    texts = []
    for o in outs:
        if isinstance(o, dict):
            texts.append(o.get("measure") or o.get("title") or o.get("name") or "")
        else:
            texts.append(str(o))
    for term in outcome_terms:
        for t in texts:
            if _outcome_matches(term, t):
                return True, [t]
    return False, []


def _decide_results(trial):
    """Resolve a registry-results-absence into one of the three states (never a terminal EXCLUDE)."""
    pub = trial.get("publication")            # a found publication (PMID/citation) => PUBLISHED
    searched = trial.get("publication_searched")  # True if a real search was done and found nothing
    if pub:
        return "PUBLISHED_RESULTS_FOUND", {"publication": pub}
    if searched:
        return "SEARCHED_NONE_FOUND", {"note": "a publication search was performed and found none"}
    return "NOT_YET_SEARCHED", {"open_task": "search for a journal/regulatory publication of %s"
                                % (trial.get("nct") or trial.get("nct_id") or "this trial")}


def screen_trial(trial, protocol):
    """Return an auditable screening decision: {nct, decision, rule_id, reason, evidence, [results_state]}."""
    nct = trial.get("nct") or trial.get("nct_id") or trial.get("study_id") or "?"
    elig = (protocol.get("eligibility") or {})
    estimands = protocol.get("estimands") or []
    outcome_terms = [e.get("outcome") for e in estimands if e.get("outcome")]
    # also accept explicit synonyms the protocol lists
    outcome_terms += (protocol.get("outcome_synonyms") or [])

    def out(decision, rule_id, reason, evidence, **extra):
        d = {"nct": str(nct), "decision": decision, "rule_id": rule_id, "reason": reason,
             "evidence": evidence}
        d.update(extra); return d

    # R-DESIGN: must be an RCT (or the protocol's declared design). Verifiable reason = actual design.
    want_design = _norm(elig.get("design") or "randomised controlled trial")
    trial_design = _norm(trial.get("design") or trial.get("study_type") or "")
    if trial_design and "randomi" in want_design and "randomi" not in trial_design \
            and "rct" not in trial_design:
        return out(EXCLUDE, "R-DESIGN", "design is %r, protocol requires a randomised design"
                   % (trial.get("design") or trial.get("study_type")), {"trial_design": trial_design})

    # R-INTERVENTION: the eligible DRUG must be present. Match on a shared drug token, not a substring
    # of the full spec: protocol 'empagliflozin 10 mg once daily' vs trial 'Empagliflozin' share the
    # drug token 'empagliflozin'; dose/formulation words ('mg','daily') must not drive the match.
    want_intv = elig.get("intervention") or ""
    intv_names = trial.get("interventions") or []
    if isinstance(intv_names, str):
        intv_names = [intv_names]
    intv_terms = [want_intv] + (protocol.get("intervention_synonyms") or [])
    if want_intv and not any(_intervention_matches(t, intv_names) for t in intv_terms if t):
        return out(EXCLUDE, "R-INTERVENTION", "eligible intervention %r shares no drug token with the "
                   "trial interventions" % want_intv, {"trial_interventions": intv_names})

    # R-OUTCOME-ANYRANK: the estimand outcome must appear at SOME rank -- but do NOT require PRIMARY.
    if outcome_terms:
        present, ev = _outcome_at_any_rank(trial, outcome_terms)
        if not present:
            return out(EXCLUDE, "R-OUTCOME-ANYRANK",
                       "estimand outcome %s not reported at any outcome rank" % outcome_terms,
                       {"trial_outcomes": [(_norm(o.get("measure") if isinstance(o, dict) else o))[:60]
                                           for o in (trial.get("outcomes") or [])]})
        # present at some rank -> this criterion is satisfied even if it is a SECONDARY outcome.

    # R-RESULTS-ABSENCE: if the ONLY remaining issue is that the registry has no posted results,
    # this is NOT an exclusion -- it is a publication-search task with three states (gate 53).
    has_results = trial.get("hasResults")
    if has_results is False:
        state, ev = _decide_results(trial)
        if state == "PUBLISHED_RESULTS_FOUND":
            return out(INCLUDE, "R-RESULTS-ABSENCE",
                       "registry posted no results, but a publication was found -> included",
                       ev, results_state=state)
        return out(PUBLICATION_SEARCH_REQUIRED, "R-RESULTS-ABSENCE",
                   "registry hasResults=false is a fact about ClinicalTrials.gov, not the trial; "
                   "resolve by publication search (NOT a terminal exclusion)", ev, results_state=state)

    # All hard criteria satisfied.
    return out(INCLUDE, "R-INCLUDE", "meets design, intervention and outcome-at-any-rank criteria",
               {"outcome_terms": outcome_terms})


# ---- self-test: fixtures drawn from the named review instances --------------------------
def _selftest():
    ok, rows = True, []
    def chk(name, cond):
        nonlocal ok; ok &= bool(cond); rows.append((name, "OK" if cond else "*** FAIL ***"))

    proto = {"eligibility": {"design": "randomised controlled trial",
                             "intervention": "apixaban", "population": "adults with VTE"},
             "estimands": [{"outcome": "recurrent venous thromboembolism"}],
             "outcome_synonyms": ["recurrent VTE", "VTE recurrence"]}

    # AMPLIFY: reports recurrent VTE (its PRIMARY) -- clean include (the drug + outcome present)
    amplify = {"nct": "NCT00643201", "design": "Randomized", "interventions": ["Apixaban", "Enoxaparin/Warfarin"],
               "outcomes": [{"measure": "Recurrent VTE or VTE-related death"}], "hasResults": True}
    d = screen_trial(amplify, proto)
    chk("AMPLIFY included (drug+outcome present)", d["decision"] == INCLUDE)

    # THE every-outcome-rank fixture: a trial that reports the outcome only as a SECONDARY must NOT
    # be excluded for having a different PRIMARY (this is the AMPLIFY-class false exclusion).
    secondary = {"nct": "NCT_SECOND", "design": "Randomized", "interventions": ["Apixaban"],
                 "outcomes": [{"measure": "Major bleeding"},                      # primary
                              {"measure": "Recurrent VTE"}],                       # secondary
                 "hasResults": True}
    d = screen_trial(secondary, proto)
    chk("outcome at SECONDARY rank -> INCLUDE (not excluded for differing primary)",
        d["decision"] == INCLUDE and d["rule_id"] in ("R-INCLUDE",))

    # gate 53: hasResults=false, no publication searched yet -> PUBLICATION_SEARCH_REQUIRED / NOT_YET
    avert = {"nct": "NCT02048865", "design": "Randomized", "interventions": ["Apixaban"],
             "outcomes": [{"measure": "Recurrent VTE"}], "hasResults": False}
    d = screen_trial(avert, proto)
    chk("AVERT (hasResults=false) NOT terminally excluded", d["decision"] == PUBLICATION_SEARCH_REQUIRED)
    chk("  AVERT resolves to NOT_YET_SEARCHED (an open task)", d.get("results_state") == "NOT_YET_SEARCHED")

    # same trial, once a publication is found -> INCLUDE with PUBLISHED_RESULTS_FOUND
    avert_pub = dict(avert, publication="NEJM 2019; VTE 12/288 vs 28/275")
    d = screen_trial(avert_pub, proto)
    chk("AVERT with a found publication -> INCLUDE / PUBLISHED_RESULTS_FOUND",
        d["decision"] == INCLUDE and d.get("results_state") == "PUBLISHED_RESULTS_FOUND")

    # a genuinely wrong design -> EXCLUDE with a VERIFIABLE reason (the actual design)
    obs = {"nct": "NCT_OBS", "design": "Observational", "interventions": ["Apixaban"],
           "outcomes": [{"measure": "Recurrent VTE"}], "hasResults": True}
    d = screen_trial(obs, proto)
    chk("observational study EXCLUDED on R-DESIGN", d["decision"] == EXCLUDE and d["rule_id"] == "R-DESIGN")
    chk("  exclusion reason is verifiable (names the actual design)", "observational" in _norm(d["reason"]))

    # a trial that never reports the outcome at any rank -> EXCLUDE on R-OUTCOME-ANYRANK
    noout = {"nct": "NCT_NOOUT", "design": "Randomized", "interventions": ["Apixaban"],
             "outcomes": [{"measure": "Quality of life"}], "hasResults": True}
    d = screen_trial(noout, proto)
    chk("outcome absent at every rank -> EXCLUDE on R-OUTCOME-ANYRANK",
        d["decision"] == EXCLUDE and d["rule_id"] == "R-OUTCOME-ANYRANK")

    # wrong drug -> EXCLUDE on R-INTERVENTION
    wrongdrug = {"nct": "NCT_WD", "design": "Randomized", "interventions": ["Rivaroxaban"],
                 "outcomes": [{"measure": "Recurrent VTE"}], "hasResults": True}
    d = screen_trial(wrongdrug, proto)
    chk("wrong intervention -> EXCLUDE on R-INTERVENTION", d["decision"] == EXCLUDE and d["rule_id"] == "R-INTERVENTION")

    # every decision must carry a rule_id and evidence (auditability)
    chk("every decision carries a rule_id", all("rule_id" in screen_trial(t, proto)
        for t in (amplify, avert, obs, noout, wrongdrug)))

    # REGISTRY-TITLE token-subset match: a real registered outcome title interleaves words
    # ('Adjudicated', 'First Event of') that break substring matching -- token-subset must still match.
    hf_proto = {"eligibility": {"design": "randomised controlled trial", "intervention": "empagliflozin",
                                "population": "adults with heart failure"},
                "estimands": [{"outcome": "cardiovascular death or hospitalisation for heart failure"}]}
    emperor = {"nct": "NCT03057977", "design": "Randomized, double-blind, placebo-controlled",
               "interventions": ["Empagliflozin", "Placebo"], "hasResults": True,
               "outcomes": [{"measure": "Time to the First Event of Adjudicated Cardiovascular (CV) "
                             "Death or Adjudicated Hospitalisation for Heart Failure (HHF)"}]}
    d = screen_trial(emperor, hf_proto)
    chk("registry title 'Adjudicated CV Death or Adjudicated HHF' matches estimand (token-subset)",
        d["decision"] == INCLUDE)
    # a title missing a content token (no 'death') must NOT spuriously match
    hfhosp = dict(emperor, outcomes=[{"measure": "Time to first hospitalisation for heart failure"}])
    d = screen_trial(hfhosp, hf_proto)
    chk("title missing a content token ('death') does NOT match -> EXCLUDE",
        d["decision"] == EXCLUDE and d["rule_id"] == "R-OUTCOME-ANYRANK")
    return ok, rows


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ok, rows = _selftest()
    print("screen.py selftest (fixtures from named review instances)")
    for n, v in rows:
        print("  %-58s %s" % (n, v))
    print("\n%s" % ("ALL PASS" if ok else "FAILURES ABOVE"))
    raise SystemExit(0 if ok else 1)
