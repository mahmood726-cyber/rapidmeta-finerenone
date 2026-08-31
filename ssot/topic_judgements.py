# -*- coding: utf-8 -*-
"""THE JUDGEMENT REGISTER, AS A GENERATOR COMPONENT.

WHAT CHANGED AND WHY. A judgement register was written for one topic on
2026-08-30. It was 459 lines of prose about dapivirine and it would not have
regenerated for topic two -- which makes it a repair, not an improvement, and it
did not count toward the bar. This module is that register turned into a
DERIVER: it reads any canon, finds which judgements are DECLARED and which are
not, and computes the counterfactual wherever the store holds the inputs to
compute it.

⭐ THE OUTPUT IS AN AUDIT, NOT A BOAST. Run across the corpus it reports how
many topics declare each judgement. The first run said: 172 outcome-blocks carry
a pooled result, `decision_threshold` exists on 1 of them, `question_pico` on 4.
That is the number worth having. A register that only ever describes the one
topic it was written for cannot produce it.

⛔ THE RULE THAT KEEPS THIS HONEST, AND IT IS ENFORCED IN CODE BELOW: NO
JUDGEMENT IS RESOLVED BY INFERRING FROM THE INCLUDED TRIALS. Deriving a review's
question from the populations that were enrolled returns DIRECT by construction
-- a tautology wearing a rating. Where the store does not declare a judgement,
this module writes UNDECLARED. It never fills the gap from the evidence, and
`_refuse_inference_from_trials` exists so that rule is a function rather than a
comment.

EVERY ENTRY CARRIES FOUR THINGS or it is disclosure rather than audit:
    decided        -- what was chosen, read from a named field
    decided_by     -- who or what chose it, and whether a harness could have
    alternative    -- the defensible other option
    if_alternative -- what would change. COMPUTED where the store allows,
                      and labelled NOT_COMPUTED where it does not.

NO NETWORK. NO TOPIC NAMES. NO HARDCODED IDENTIFIERS.
"""
import math

# Judgement slots. The list is the contract: adding a topic must not add a slot,
# and a slot that cannot be evaluated from the store is reported UNDECLARED
# rather than dropped.
SLOTS = ("QUESTION_PICO", "ELIGIBILITY_RULE", "COUNT_TIER", "INDIRECTNESS",
         "ESTIMAND", "IMPRECISION_THRESHOLD", "HARMS_POOLING", "INDEX_ENTRY")

DECLARED = "DECLARED"
UNDECLARED = "UNDECLARED"
NOT_APPLICABLE = "NOT_APPLICABLE"

_RATIO_MEASURES = ("RR", "OR", "HR", "IRR", "RATERATIO", "RATE_RATIO")


# --------------------------------------------------------------- helpers ----
def _g(o, *path, **kw):
    """Nested get that never raises and never invents."""
    cur = o
    for p in path:
        if isinstance(cur, dict):
            cur = cur.get(p)
        elif isinstance(cur, list) and isinstance(p, int) and -len(cur) <= p < len(cur):
            cur = cur[p]
        else:
            return kw.get("default")
    return cur if cur is not None else kw.get("default")


def _outcome(canon, oid):
    return _g(canon, "results", "by_outcome", oid, default={}) or {}


def _trials(canon):
    t = _g(canon, "inputs", "trials", default=[]) or []
    return [x for x in t if isinstance(x, dict)]


def _refuse_inference_from_trials(slot, value_source):
    """⛔ THE ANTI-TAUTOLOGY GUARD, AS CODE RATHER THAN AS A COMMENT.

    A judgement about what the review ASKS may never be sourced from what the
    trials DID. If it is, the comparison that judgement feeds -- indirectness
    above all -- returns DIRECT by construction and the rating is a restatement
    of the evidence rather than a test of it.

    Raises rather than returning a flag, because a caller that silently ignored
    the flag would reintroduce exactly the defect.
    """
    banned = ("inputs.trials", "per_trial", "trial_pico", "registered_",
              "eligibilities", "enrolled")
    s = str(value_source or "")
    for b in banned:
        if b in s:
            raise ValueError(
                "REFUSED: judgement %s would be sourced from %r, which "
                "describes the CONTRIBUTING TRIALS. Deriving the review's own "
                "question or eligibility from the trials returns DIRECT by "
                "construction. Declare it, or leave it UNDECLARED."
                % (slot, value_source))
    return True


def _ratio_measure(res):
    m = str(_g(res, "pooled", "measure") or res.get("measure") or "").upper()
    m = m.replace(" ", "").replace("-", "")
    return m if m in _RATIO_MEASURES else None


def _ci(pt, se):
    return (round(math.exp(math.log(pt) - 1.959964 * se), 4),
            round(math.exp(math.log(pt) + 1.959964 * se), 4))


def _fe_pool(rows):
    """Fixed-effect inverse variance. Used ONLY to place two count tiers on the
    same footing inside one topic; it is never offered as the review's pool."""
    if not rows:
        return None
    w = [1.0 / (s * s) for _, s in rows if s]
    ys = [y for y, s in rows if s]
    if not w:
        return None
    mu = sum(wi * y for wi, y in zip(w, ys)) / sum(w)
    se = math.sqrt(1.0 / sum(w))
    lo, hi = _ci(math.exp(mu), se)
    return {"point": round(math.exp(mu), 4), "ci_low": lo, "ci_high": hi,
            "k": len(ys)}


def _entry(slot, state, decided, decided_by, alternative, if_alt,
           field_path, harness_could=False, **extra):
    e = {"slot": slot, "state": state, "decided": decided,
         "decided_by": decided_by, "alternative": alternative,
         "if_alternative": if_alt, "field_path": field_path,
         "a_harness_could_derive_this": harness_could}
    e.update(extra)
    return e


# ------------------------------------------------- THE PROVENANCE GATE ------
# Phrases a field uses to say IT HOLDS NOTHING, and templated prefixes a repair
# pass wrote across the corpus. A slot that tests only whether a field EXISTS
# counts every one of these as a declared judgement.
_NON_DECLARATIONS = (
    "not recorded", "not stated", "not reported", "no information",
    "unknown", "not applicable", "none recorded", "not established",
    "not derivable", "derived_post_hoc", "derived post hoc", "post_hoc",
    "this review asks:",          # the templated introduction prefix
)


def is_authored(value):
    """Does this field carry an AUTHORED judgement, or does it merely exist?

    ⛔ WHY THIS GATE EXISTS, AND IT IS A CORRECTION TO THIS MODULE'S OWN COUNTS.
    Every slot below originally tested PRESENCE. Measured across the corpus on
    2026-08-30 that was wrong twice, both times in the direction that flatters
    the review:

      `_estimand_rule` is carried by 44 objects with only SIXTEEN DISTINCT
      VALUES, and the most common -- on TWENTY objects -- is the string
      "not recorded on the page this object was extracted from". A field whose
      content is a statement that nothing was recorded was being counted as a
      declared estimand judgement.

      `screening.eligibility_provenance` most often reads
      {state: "derived_post_hoc", predefined: false}. That is the object saying
      its criteria were reconstructed AFTER the fact. It was being counted as a
      declared eligibility rule.

    This is the same failure the inventory lane measured on manuscript
    introductions: a naive "does the field exist" test flips 138 of 152 objects
    because a repair pass wrote a templated restatement into nearly all of
    them -- 137 restatements against 1 genuinely authored. TEMPLATED CONTENT
    LOOKS LIKE REAL CONTENT TO EVERY TEST THAT DOES NOT ASK WHERE IT CAME FROM.

    ⚠️ WHAT THIS GATE IS NOT. It is a phrase list, so it catches the templates
    THIS corpus happens to contain and nothing else. It is a stopgap for a real
    `derived_from` provenance field, and it must not be mistaken for one: a new
    repair pass writing a new template defeats it silently, which is precisely
    how the defect it corrects was introduced.
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, dict):
        if value.get("state") and str(value["state"]).lower() in (
                "derived_post_hoc", "post_hoc", "unknown", "not_recorded"):
            return False
        if value.get("predefined") is False:
            return False
        return any(is_authored(v) for k, v in value.items()
                   if not str(k).startswith("_"))
    if isinstance(value, (list, tuple)):
        return any(is_authored(v) for v in value)
    t = str(value).strip().lower()
    if len(t) < 4:
        return False
    for bad in _NON_DECLARATIONS:
        if bad in t:
            return False
    return True


# ------------------------------------------------------------ J: PICO -------
def _j_question_pico(canon, oid, res):
    AXES = ("population", "intervention", "comparator", "outcome")
    q = res.get("question_pico")
    path = "results.by_outcome.%s.question_pico" % oid
    if isinstance(q, dict) and all(is_authored(q.get(a)) for a in AXES):
        _refuse_inference_from_trials("QUESTION_PICO", q.get("source"))
        # ⛔ AND A POPULATION SLOT HOLDING A PASTE OF THE TITLE IS A MECHANICAL
        # TRANSFORM, NOT A JUDGEMENT. A repair pass rebuilt title-shaped
        # questions as "In <title>, what is the effect on <tail>", producing 55
        # objects with the title pasted into the population slot. Those must
        # score UNDECLARED: a transform of a title is not an authored PICO.
        import re as _re
        _w = lambda x: set(w for w in _re.findall(r"[a-z0-9]+", str(x or "").lower())
                           if len(w) > 3)
        pop_w, title_w = _w(q.get("population")), _w(canon.get("title"))
        if pop_w and title_w and len(pop_w) > 3 and pop_w <= title_w:
            return _entry(
                "QUESTION_PICO", UNDECLARED,
                "The population slot is a SUBSET OF THE TITLE (%r) -- a "
                "mechanical transform, not an authored population."
                % q.get("population"),
                "A REPAIR PASS, not a person.",
                "Declare the population independently of the title.",
                "⛔ An indirectness comparison against a population read off "
                "the title compares the review with itself.",
                path)
        return _entry(
            "QUESTION_PICO", DECLARED,
            "; ".join("%s = %r" % (a, q.get(a)) for a in AXES),
            "A HUMAN. `source` records what it was read from: %r"
            % (q.get("source") or "not recorded"),
            "Declare the question as the studied band rather than the asked "
            "one.",
            "The indirectness comparison would change, and it would change in "
            "the direction that flatters the review. NOT COMPUTED here: "
            "rescoping a question is an editorial act about what the review "
            "CLAIMS and must not be simulated to see which letter it buys.",
            path)
    missing = [a for a in AXES if not (q or {}).get(a)] if isinstance(q, dict) else list(AXES)
    return _entry(
        "QUESTION_PICO", UNDECLARED,
        "NOT DECLARED -- missing axes: %s" % ", ".join(missing),
        "NOBODY. The review question exists as prose and has never been "
        "resolved into axes.",
        "Declare it, axis by axis.",
        "⛔ WITHOUT IT THE INDIRECTNESS DOMAIN CANNOT BE COMPARED AXIS BY AXIS "
        "AT ALL. Prose cannot be compared with prose. Any indirectness rating "
        "on this topic is therefore a stored judgement or an absence, never a "
        "derivation.",
        path)


# ----------------------------------------------------- J: ELIGIBILITY -------
def _j_eligibility(canon, oid, res):
    """A concept block is NOT an eligibility rule.

    ⭐ THE PROOF IS ALREADY IN THIS CORPUS: a drug-only concept block returned
    an IDENTICAL 125 candidates across six different colchicine topics. The
    block finds the drug. The rule that turns candidates into an included set
    is the judgement, and it is the part no query expresses. So a topic counts
    as DECLARED only if it states a criterion on the COMPARATOR and on the
    OUTCOME -- the two a phase-and-randomisation screen does not test.
    """
    cands = []
    for p in (("screening", "eligibility"), ("screening", "criteria"),
              ("config", "eligibility"), ("eligibility",),
              ("scope_decisions",)):
        v = _g(canon, *p)
        if v:
            cands.append((".".join(p), v))
    # a search block's own screen
    for k in canon:
        if str(k).startswith("search_executed"):
            sc = _g(canon, k, "screen")
            if sc:
                cands.append(("%s.screen" % k, sc))
            ad = _g(canon, k, "adjudication_rule")
            if ad:
                cands.append(("%s.adjudication_rule" % k, ad))
    # ⚠️ GATED. The commonest shape here is
    # {state: "derived_post_hoc", predefined: false} -- the object saying its
    # criteria were reconstructed after the fact, which is the opposite of a
    # declared rule and was being counted as one.
    cands = [(pth, v) for pth, v in cands if is_authored(v)]
    blob = " ".join(str(v).lower() for _, v in cands)
    has_comparator = "comparator" in blob
    has_outcome = ("outcome" in blob) or ("endpoint" in blob)
    path = " | ".join(p for p, _ in cands) or "none found"

    if cands and has_comparator and has_outcome:
        return _entry(
            "ELIGIBILITY_RULE", DECLARED,
            "A rule is recorded that names criteria on BOTH the comparator "
            "and the outcome.",
            "A HUMAN. The concept block finds the drug; this is the part it "
            "cannot express.",
            "Widen or narrow the comparator or outcome criterion.",
            "k would change, and which trials contribute with it. NOT "
            "COMPUTED: re-screening is not a store operation.",
            path)
    return _entry(
        "ELIGIBILITY_RULE", UNDECLARED,
        "NO RULE STATES BOTH A COMPARATOR AND AN OUTCOME CRITERION. "
        "comparator named: %s; outcome named: %s" % (has_comparator, has_outcome),
        "⚠️ ENACTED RATHER THAN DECLARED. Where a screen tests only phase and "
        "randomisation, the comparator and outcome criteria are applied as "
        "per-case verdicts, and a harness cannot regenerate the rule from "
        "what is written.",
        "State the rule.",
        "⛔ A CANDIDATE COUNT IS NOT AN ELIGIBILITY DECISION. A drug-only "
        "concept block returned an identical 125 candidates across six "
        "colchicine topics in this corpus; the count says nothing about which "
        "of them belong.",
        path)


# ------------------------------------------------------ J: COUNT TIER -------
def _j_count_tier(canon, oid, res):
    """Which document supplies the numerator. Renders BOTH where both exist."""
    per = res.get("per_trial") or []
    tiers = {}
    for t in per:
        if not isinstance(t, dict):
            continue
        prov = str(t.get("provenance") or t.get("source_tier") or "").upper()
        if "REGISTR" in prov or t.get("as_posted"):
            tiers.setdefault("registry", []).append(t)
        elif "PUBLICATION" in prov or "PAPER" in prov or "PMID" in prov:
            tiers.setdefault("publication", []).append(t)
        elif prov:
            tiers.setdefault(prov.lower()[:24], []).append(t)
    path = "results.by_outcome.%s.per_trial[].provenance" % oid

    if len(tiers) > 1:
        pools = {}
        for name, rows in tiers.items():
            rr = []
            for t in rows:
                pt, se = t.get("point"), t.get("se_log_rr")
                if pt and se:
                    rr.append((math.log(pt), se))
            p = _fe_pool(rr)
            if p:
                pools[name] = p
        return _entry(
            "COUNT_TIER", DECLARED if res.get("count_tier_declared") else UNDECLARED,
            "MORE THAN ONE COUNT BASIS IS PRESENT: %s" % ", ".join(sorted(tiers)),
            "⚠️ A HUMAN, and unless `count_tier_declared` is set the page names "
            "neither basis as a CHOICE.",
            "The other tier.",
            "COMPUTED per tier below." if pools else "NOT COMPUTED -- the "
            "per-trial rows lack a point estimate and a standard error.",
            path, tiers_present=sorted(tiers), pools_by_tier=pools,
            headline_must_be_named=True)

    only = (sorted(tiers) or ["none recorded"])[0]
    return _entry(
        "COUNT_TIER", NOT_APPLICABLE if tiers else UNDECLARED,
        "ONE COUNT BASIS: %s" % only,
        "Recorded per trial." if tiers else "NOT RECORDED on any contributing row.",
        "The other tier, where the trial has one.",
        "NOT COMPUTED -- the store holds only one basis, so the alternative "
        "cannot be evaluated without going back to the sources.",
        path, tiers_present=sorted(tiers))


# ---------------------------------------------------- J: INDIRECTNESS -------
def _j_indirectness(canon, oid, res):
    stored = _g(res, "grade", "indirectness") or \
        _g(canon, "grade", "by_outcome", oid, "indirectness")
    path = "results.by_outcome.%s.grade.indirectness" % oid
    if isinstance(stored, dict) and stored.get("state"):
        by = str(stored.get("judged_by") or "")
        return _entry(
            "INDIRECTNESS", DECLARED,
            "%s, %s level(s)" % (stored.get("state"), stored.get("levels")),
            "⚠️ A STORED HAND-WRITTEN JUDGEMENT that the engine READS rather "
            "than derives. %s" % (by or "judged_by not recorded."),
            "The opposite rating.",
            "The certainty letter moves by one level. NOT COMPUTED here "
            "because flipping a stored judgement to see the letter it buys is "
            "the gaming move the store's own guard forbids.",
            path)
    q = res.get("question_pico")
    if not isinstance(q, dict) or not q.get("population"):
        return _entry(
            "INDIRECTNESS", UNDECLARED,
            "NO STORED JUDGEMENT AND NO DECLARED question_pico.",
            "NOBODY. The domain cannot be derived without both PICOs and it "
            "has not been judged by hand either.",
            "Declare question_pico, or judge the domain explicitly.",
            "⛔ Until one of the two happens the domain is neither rated nor "
            "refused -- it is simply missing, which reads to a reader as no "
            "concern.",
            path)
    return _entry(
        "INDIRECTNESS", UNDECLARED,
        "question_pico is declared but no indirectness judgement is stored.",
        "Derivable by ssot.indirectness_procedure once both PICOs exist.",
        "Judge it by hand instead.", "NOT COMPUTED.", path,
        harness_could=True)


# -------------------------------------------------------- J: ESTIMAND -------
def _j_estimand(canon, oid, res):
    """Does the pool combine trials measured over different follow-up?"""
    frames = []
    for t in _trials(canon):
        v = t.get("registered_primary_timeframe") or t.get("timeframe")
        if v:
            frames.append(str(v).strip())
    path = "inputs.trials[].registered_primary_timeframe"
    distinct = sorted(set(frames))
    if len(distinct) <= 1:
        return _entry(
            "ESTIMAND", NOT_APPLICABLE if distinct else UNDECLARED,
            "Follow-up is recorded as %s across contributing trials."
            % ("a single value" if distinct else "NOTHING"),
            "Read from the registrations." if distinct else "NOT RECORDED.",
            "n/a" if distinct else "Record the registered time frame per trial.",
            "No estimand normalisation is required." if distinct else
            "⛔ WITHOUT THE TIME FRAMES NOBODY CAN TELL whether this pool "
            "combines cumulative incidences over unequal follow-up.",
            path, distinct_timeframes=distinct)
    # ⚠️ GATED. `_estimand_rule` reads "not recorded on the page this object
    # was extracted from" on 20 objects; presence is not declaration.
    declared = (is_authored(res.get("estimand_normalisation"))
                or is_authored(canon.get("_estimand_rule")))
    return _entry(
        "ESTIMAND", DECLARED if declared else UNDECLARED,
        "⚠️ CONTRIBUTING TRIALS REPORT %d DIFFERENT PRIMARY TIME FRAMES: %s. "
        "The pool combines them on one scale." % (len(distinct), " | ".join(distinct)),
        "A HUMAN, and often as a SIDE EFFECT of the count tier rather than as "
        "its own decision -- a registry reports participants and so forces a "
        "risk ratio; a publication reports person-years and so forces a rate "
        "ratio. Choosing the document chose the measure.",
        "Pool on person-time instead, which is estimand-consistent under "
        "unequal follow-up.",
        "NOT COMPUTED -- person-time denominators are not in this store. "
        "Where a topic holds them the alternative is one line.",
        path, distinct_timeframes=distinct)


# --------------------------------------------- J: IMPRECISION THRESHOLD -----
def _j_threshold(canon, oid, res):
    thr = res.get("decision_threshold")
    path = "results.by_outcome.%s.decision_threshold" % oid
    pooled = res.get("pooled") or {}
    lo, hi = pooled.get("ci_low"), pooled.get("ci_high")
    if isinstance(thr, dict) and thr.get("lo"):
        # What actually moves the letter is the RULE, not the value: does the
        # interval cross the declared zone, and does it cross no effect?
        crosses_null = bool(lo and hi and lo < 1.0 < hi)
        crosses_zone = bool(lo and hi and (lo < thr["lo"] < hi or
                                           lo < (thr.get("hi") or 1e9) < hi))
        return _entry(
            "IMPRECISION_THRESHOLD", DECLARED,
            "Appreciable effect declared at %s to %s."
            % (thr.get("lo"), thr.get("hi")),
            "A HUMAN. %s" % (thr.get("source") or "source not recorded"),
            "The Handbook rough guide, 0.75 to 1.25, which is a DECLARED "
            "DEFAULT and not a clinical judgement.",
            "COMPUTED from the stored interval: it crosses no effect = %s; it "
            "crosses the declared zone = %s. ⭐ THE VALUE IS USUALLY NOT WHAT "
            "MOVES THE LETTER -- the RULE is. An imprecision domain judged on "
            "'excludes no effect' and one judged on 'spans an appreciable "
            "zone' give different answers on the same interval, and that "
            "choice is rarely written down anywhere."
            % (crosses_null, crosses_zone),
            path, crosses_null=crosses_null, crosses_declared_zone=crosses_zone)
    return _entry(
        "IMPRECISION_THRESHOLD", UNDECLARED,
        "NO THRESHOLD DECLARED.",
        "⚠️ NOBODY. The engine falls back to the Handbook rough guide of 0.75 "
        "to 1.25 -- which means the most consequential line on the page is "
        "drawn by a default rather than by a clinical judgement.",
        "Declare one, justified from ABSOLUTE effect rather than from the ratio.",
        "The imprecision domain would rest on a stated, arguable line instead "
        "of an unexamined default.",
        path)


# ---------------------------------------------------- J: HARMS POOLING ------
def _j_harms(canon, oid, res):
    harms = None
    for k in canon:
        if "harm" in str(k).lower() or "adverse" in str(k).lower():
            harms = k
            break
    if not harms:
        return _entry(
            "HARMS_POOLING", UNDECLARED,
            "NO HARMS OUTCOME IS HELD.",
            "NOBODY -- the review carries benefit only.",
            "Extract harms.",
            "⛔ OUTCOME SCOPE IS BENEFIT-ONLY. A reader cannot weigh anything "
            "against anything.",
            "(no harms block on this object)")
    blob = str(_g(canon, harms) or "").upper()
    declined = "NOT POOLED" in blob or "NOT_POOLED" in blob
    return _entry(
        "HARMS_POOLING", DECLARED,
        "Harms held at `%s`; pooled = %s" % (harms, not declined),
        "A HUMAN, on statistics a harness CAN compute. What is not derivable "
        "is the inference that a large control-arm difference between trials "
        "in the same population indicates ASCERTAINMENT rather than RISK.",
        "Pool anyway with random effects." if declined else "Decline to pool.",
        "A pooled harms estimate over incommensurable ascertainment reads as "
        "reassurance and is manufactured by the averaging." if declined
        else "NOT COMPUTED.",
        harms, harness_could=False)


# ------------------------------------------------------ J: INDEX ENTRY ------
def _j_index_entry(canon, oid, res):
    """The sentence the portfolio index shows for this review.

    ⭐ WHY THIS IS A JUDGEMENT AND NOT PLUMBING. `scripts/project_index_cards.py`
    projects the NUMBERS onto the index card and states that the PROSE IS
    AUTHORED. So a human writes the tile sentence -- what the review IS, which
    trials it pools -- and nothing reconciles it against the object afterwards.
    That is a per-topic human decision with no owner and no check, which is
    exactly what this register counts.

    ⛔ THE LIVE INSTANCE THAT PUT THIS SLOT HERE. On 2026-08-30 the portfolio
    index described one URL four different ways: a tile naming HPTN 082 and
    FACTS-001, a table row describing oral PrEP adherence and tenofovir gel, a
    PAGE_MAP title calling it an NMA, and a page whose object is a dapivirine
    ring review. The tile's NUMBER was projected and correct; everything naming
    the review was authored and stale. A correct number under a wrong name
    reads as verified, which makes it worse than a wrong number.

    A topic counts as DECLARED only if the object itself carries the index
    sentence, so the index can be projected from the store rather than typed
    beside it.
    """
    for path in (("index_entry",), ("card_note",),
                 ("results", "headline_outcome")):
        v = _g(canon, *path)
        if path == ("index_entry",) and isinstance(v, dict) and v.get("tile"):
            return _entry(
                "INDEX_ENTRY", DECLARED,
                "The object carries its own index sentence: %r" % v.get("tile"),
                "A HUMAN, and recorded in the store so the index can be "
                "PROJECTED from it rather than typed beside it.",
                "Leave the index sentence authored in the index generator.",
                "The index and the object can then disagree about what the "
                "review IS while agreeing about its number -- the failure that "
                "put this slot in the register.",
                "index_entry.tile")
    return _entry(
        "INDEX_ENTRY", UNDECLARED,
        "The object does not carry the sentence the portfolio index shows.",
        "⚠️ A HUMAN, IN THE INDEX GENERATOR, WITH NO LINK BACK. "
        "project_index_cards.py projects the numbers and states that the prose "
        "is authored, so the tile's name for this review lives only in the "
        "index and nothing reconciles the two.",
        "Store the tile sentence on the object and project it.",
        "⛔ Until then a re-pointed object updates its NUMBER on the index and "
        "keeps its old NAME. Measured 2026-08-30: 1 of 44 mapped index entries "
        "names trials the object has never heard of, and the number beside it "
        "was correct. See scripts/audit_index_identity_drift.py.",
        "index_entry (absent)")


_DERIVERS = {
    "QUESTION_PICO": _j_question_pico,
    "ELIGIBILITY_RULE": _j_eligibility,
    "COUNT_TIER": _j_count_tier,
    "INDIRECTNESS": _j_indirectness,
    "ESTIMAND": _j_estimand,
    "IMPRECISION_THRESHOLD": _j_threshold,
    "HARMS_POOLING": _j_harms,
    "INDEX_ENTRY": _j_index_entry,
}


def derive(canon, oid="primary"):
    """The register for ONE outcome of ANY topic. No network, no topic names."""
    res = _outcome(canon, oid)
    if not res:
        return None
    entries = []
    for slot in SLOTS:
        try:
            e = _DERIVERS[slot](canon, oid, res)
        except ValueError as exc:            # the anti-tautology guard fired
            e = _entry(slot, UNDECLARED, "REFUSED", str(exc),
                       "Declare it rather than inferring it.",
                       "n/a", "refused")
        entries.append(e)
    declared = [e for e in entries if e["state"] == DECLARED]
    undeclared = [e for e in entries if e["state"] == UNDECLARED]
    return {
        "_what": ("Judgements this topic required that a harness cannot "
                  "derive, with what was decided, who decided it, the "
                  "alternative, and what would change."),
        "_derived_by": "ssot/topic_judgements.py derive()",
        "_generality": ("This block is GENERATED for any topic holding a "
                        "results block. It is not written per topic. The same "
                        "code produced it for every topic in the corpus "
                        "audit."),
        "⛔_no_entry_is_inferred_from_the_included_trials": (
            "Deriving the review's question or eligibility from the trials "
            "that were included returns DIRECT by construction. Where the "
            "store does not declare a judgement this block writes UNDECLARED "
            "and stops. `_refuse_inference_from_trials` raises rather than "
            "returning a flag, so the rule cannot be ignored by a caller."),
        "outcome": oid,
        "entries": entries,
        "count": {
            "slots": len(SLOTS),
            "declared": "%d of %d" % (len(declared), len(SLOTS)),
            "undeclared": "%d of %d" % (len(undeclared), len(SLOTS)),
            "undeclared_slots": [e["slot"] for e in undeclared],
        },
        "⭐_the_scaling_claim": (
            "A topic costs %d declared judgements on this outcome, not four "
            "hundred. That is a stronger claim than \"automated\", because a "
            "reader can check a declared judgement and cannot check an "
            "inferred one." % len(declared)),
        "what_this_does_NOT_do": (
            "⚠️ It does not make the judgements right, and it does not prove "
            "the SLOT LIST is complete -- the list is bounded by what its "
            "author enumerated. The honest form is \"%d slots checked\", never "
            "\"%d judgements exist\"." % (len(SLOTS), len(SLOTS))),
    }
