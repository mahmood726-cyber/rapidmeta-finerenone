"""THE PLANT REGISTRY -- one entry per defect class found on this corpus, forever.

WHAT THIS IS FOR. Every class below was found by a person reading a page, not by an
instrument. This registry is the standing proof of whether that is still true. Each entry
plants the class and asks the instruments we own whether they see it.

TWO OUTCOMES ARE BOTH LEGITIMATE, AND THE SUITE FAILS IF EITHER CHANGES.

    expect="DETECTED"   an instrument reports this class. If it stops, that is a REGRESSION.
    expect="ZERO"       nothing we own reports this class. Measured, not assumed. If something
                        starts reporting it, that is NEWS and this registry is stale -- which
                        is also a failure, because a known-zero that has quietly become a
                        known-one is a false statement about our coverage.

TIERS, BECAUSE COST IS A CONSTRAINT AND A SUITE THAT IS SWITCHED OFF IS WORSE THAN NONE.

    1  every build.  In-process calls to the REAL shipped predicate against a small fixture.
                     No corpus scan, no file writes, no network, NO MODEL CALLS. Milliseconds.
    2  nightly.      Multiple instances per class planted into the real corpus, restored and
                     hash-asserted. Minutes. This is where traversal is tested, not just the
                     predicate.
    3  manual.       Anything needing a model call or a network fetch. Never automatic.

WHY TIER 1 CALLS THE PREDICATE AND TIER 2 PLANTS THE CORPUS -- the two catch different
failures and neither substitutes for the other. Tier 1 proves the rule still fires. Tier 2
proves the traversal still REACHES a defect in situ. Measured on 2026-08-28: gate 1's
predicate is correct and its traversal never reaches a swapped name written in prose, so a
tier-1-only suite would have reported that class green.

THE INSTRUMENT NAMED ON EACH ENTRY IS THE SHIPPED ONE, IMPORTED, NEVER A COPY. A gate that
re-implements what it checks is a tautology.
"""

# --------------------------------------------------------------------------------------
# fixtures. Small, literal, and each one is the SHAPE of a defect actually seen on this
# corpus rather than an invented one.
# --------------------------------------------------------------------------------------

def fx_swapped_label_store():
    """A1 store: a label naming a different pinned trial than its own registration."""
    return {"fixture-topic": {"inputs": {"trials": [
        {"nct": "NCT00509106", "label": "FOCUS 2"}]}}}


def fx_correct_label_store():
    """A1 store, KNOWN NEGATIVE: the same shape, correct. Precision, not just recall."""
    return {"fixture-topic": {"inputs": {"trials": [
        {"nct": "NCT00509106", "label": "FOCUS 1"}]}}}


FX_SWAP_PROSE = ("The trial was registered as "
                 "FOCUS 2 &mdash; https://clinicaltrials.gov/study/NCT00509106 and reported "
                 "in 2010.")

FX_SWAP_PROSE_BOTH = ("FOCUS 1 &mdash; https://clinicaltrials.gov/study/NCT00509106 in the "
                      "table, and later "
                      "FOCUS 2 &mdash; https://clinicaltrials.gov/study/NCT00509106 in the "
                      "narrative.")

FX_CORRECT_PROSE = ("FOCUS 1 &mdash; https://clinicaltrials.gov/study/NCT00509106")


def fx_divergent_reason():
    """Two spellings of the reason for not pooling, holding two different answers."""
    return {"fixture-topic": {"results": {"by_outcome": {"primary": {
        "poolable_reason": "Both trials register the same composite; one question.",
        "not_poolable_reason": "The trials measure different quantities and were never "
                               "combined; nothing was pooled.",
    }}}}}


def fx_identical_reason():
    """KNOWN NEGATIVE: same text under two names is redundant, not contradictory."""
    return {"fixture-topic": {"results": {"by_outcome": {"primary": {
        "poolable_reason": "One endpoint definition, one question.",
        "not_poolable_reason": "One endpoint definition, one question.",
    }}}}}


def fx_bare_judgement():
    """AS4: a verdict with no reference of any kind, and NOTHING above it either."""
    return {"review": {"verdict": "low risk of bias",
                       "reason": "the allocation sequence was concealed"}}


def fx_bare_judgement_under_a_date():
    """AS4, the case that MATTERS: identical judgement, one dated ancestor above it.

    Measured 2026-08-28: this is scored TIMESTAMPED rather than NOTHING, because
    classify() unions the judgement's keys with every ancestor key on its path.
    """
    return {"trials": [{"read_utc": "2026-08-18",
                        "review": {"verdict": "low risk of bias",
                                   "reason": "the allocation sequence was concealed"}}]}


def fx_fake_full_hash():
    """AS5: eight hex characters calling itself a full sha256, above a bare judgement.

    Measured 2026-08-28: adding this ONE key promoted 76 judgements from 'believed' to
    'exactly re-checkable' and the gate passed.
    """
    return {"source_sha256_full": "9c1b8e07",
            "review": {"verdict": "low risk of bias"}}


# --------------------------------------------------------------------------------------
# the registry
# --------------------------------------------------------------------------------------
# probe: name of a probe function on the runner. expect: DETECTED | ZERO.
# corpus_plants: tier-2 instances, by id, in scratch plant registries (see TIER2_SOURCES).

# ---------------------------------------------------------------------------------------
# S3 / Q4 / S1 fixtures -- added 2026-08-29 with their instruments (gates 13 and 14).
# Each fixture is the SMALLEST object that exercises the real mechanism: the NI ones turn on
# an NCT that the external registry lists, not on any word in the prose, because that NCT is
# what the shipped predicate actually joins on.
# ---------------------------------------------------------------------------------------
NI_REGISTERED_NCT = "NCT01721408"      # present in out/blind-review/noninferiority_trials.json
NOT_NI_NCT = "NCT00643188"             # present in the corpus, absent from that list


def fx_ni_pooled_as_superiority():
    return {"results": {"by_outcome": {"primary": {
        "k": 2, "favours": "treatment",
        "per_trial": [{"nct": NI_REGISTERED_NCT}, {"nct": NOT_NI_NCT}]}}}}


def fx_ni_with_margin():
    """THE MODEL ANSWER: the same pool, with the trial's own estimand and its margin."""
    return {"results": {"by_outcome": {"primary": {
        "k": 2, "favours": "treatment",
        "trial_own_estimand": {"estimand": "risk difference",
                               "non_inferiority_margin_pp": 10},
        "per_trial": [{"nct": NI_REGISTERED_NCT}, {"nct": NOT_NI_NCT}]}}}}


def fx_ni_margin_present_but_empty():
    """A margin FIELD with no value must not clear the accusation."""
    return {"results": {"by_outcome": {"primary": {
        "k": 2, "favours": "treatment", "non_inferiority_margin_pp": None,
        "per_trial": [{"nct": NI_REGISTERED_NCT}, {"nct": NOT_NI_NCT}]}}}}


def fx_k_disagrees_with_rows():
    return {"results": {"by_outcome": {"primary": {
        "k": 3, "per_trial": [{"nct": "NCT1"}, {"nct": "NCT2"}, {"nct": "NCT3"},
                              {"nct": "NCT4"}]}}}}


def fx_k_refusal_states_k_with_no_rows():
    """THE MODEL ANSWER for Q4: a refusal states the k it WOULD have pooled and carries none."""
    return {"results": {"by_outcome": {"primary": {
        "k": 3, "per_trial": [], "poolable": False,
        "poolable_reason": "the three trials do not share a comparator"}}}}


def fx_result_with_no_rows():
    return {"results": {"by_outcome": {"primary": {
        "k": 3, "per_trial": [],
        "pooled": {"estimate": 0.82, "ci_low": 0.71, "ci_high": 0.95}}}}}


def fx_no_rows_but_refuses():
    """THE MODEL ANSWER for S1: nothing behind it, and it says so."""
    return {"results": {"by_outcome": {"primary": {
        "k": 3, "per_trial": [], "poolable": False,
        "poolable_reason": "no trial reported this outcome in a poolable form"}}}}


def fx_arm_role_inverted():
    """The arms imply protection; the stored ratio claims harm, with an interval excluding
    the null. The mechanism is the SIGN disagreement, not any word on the page."""
    return {"inputs": {"trials": [{"nct": "NCT-FX", "arms": [
        {"role": "treatment", "events": 10, "participants": 200},
        {"role": "control", "events": 40, "participants": 200}]}]},
        "results": {"by_outcome": {"primary": {"per_trial": [
            {"nct": "NCT-FX", "measure": "RR", "point": 4.0,
             "ci_low": 2.1, "ci_high": 7.6}]}}}}


def fx_arm_role_agrees():
    """THE MODEL ANSWER: the same counts with the effect pointing the same way as its arms."""
    return {"inputs": {"trials": [{"nct": "NCT-FX", "arms": [
        {"role": "treatment", "events": 10, "participants": 200},
        {"role": "control", "events": 40, "participants": 200}]}]},
        "results": {"by_outcome": {"primary": {"per_trial": [
            {"nct": "NCT-FX", "measure": "RR", "point": 0.25,
             "ci_low": 0.13, "ci_high": 0.48}]}}}}


def fx_arm_role_mean_difference():
    """A MEAN DIFFERENCE is read against a null of ZERO. Comparing it to a crude ratio is a
    category error, and the first version of gate 16 made exactly that accusation against a
    correct page. It must be REFUSED, not judged."""
    return {"inputs": {"trials": [{"nct": "NCT-FX", "arms": [
        {"role": "treatment", "events": 10, "participants": 200},
        {"role": "control", "events": 40, "participants": 200}]}]},
        "results": {"by_outcome": {"primary": {"per_trial": [
            {"nct": "NCT-FX", "measure": "MD", "point": 6.9,
             "ci_low": 3.3, "ci_high": 10.6}]}}}}


PLANTS = [
    # ---- Attribution ------------------------------------------------------------------
    dict(id="A1a", cls="A1 swapped trial name, registration correct", tier=1, layer="store",
         instrument="gates/gate1_trial_identity.check_objects", probe="p_gate1_swap",
         expect="DETECTED",
         note="the only class in this registry with a working store-side detector"),
    dict(id="A1b", cls="A1 swapped trial name, registration correct", tier=1, layer="served",
         instrument="gates/gate6_nct_beside_name.pair_by_nearest", probe="p_gate6_swap_clean",
         expect="DETECTED",
         note="detected only when the page never names the trial correctly"),
    dict(id="A1c", cls="A1 swapped trial name, registration correct", tier=1, layer="served",
         instrument="gates/gate6_nct_beside_name.pair_by_nearest", probe="p_gate6_swap_mixed",
         expect="ZERO",
         note="THE REALISTIC CASE. One correct mention on the same page downgrades a true "
              "swap to AMBIGUOUS, which is not a finding and does not block a pass."),
    dict(id="A1d", cls="A1 swapped trial name, registration correct", tier=1, layer="store",
         instrument="gates/gate1_trial_identity.check_objects", probe="p_gate1_unpinned",
         expect="ZERO",
         note="REACH, NOT COVERAGE. gate 1's entire authority is four registrations; a swap "
              "between any other pair of trials is outside its universe by construction."),
    dict(id="A2a", cls="A2 role inversion on the arms", tier=1, layer="store",
         instrument="gates/arm_role_inversion.scan", probe="p_a2_inverted", expect="DETECTED",
         note="a SIGN test against the object's own arm counts -- no tolerance, no threshold. "
              "Found a real instance on its first run: IRONMAN in fcm-hf-review, escalated."),
    dict(id="A2b", cls="A2 role inversion on the arms", tier=1, layer="store",
         instrument="gates/arm_role_inversion.scan", probe="p_a2_agrees", expect="ZERO",
         note="MODEL ANSWER: counts and effect pointing the same way must NOT be accused."),
    dict(id="A2c", cls="A2 role inversion on the arms", tier=1, layer="store",
         instrument="gates/arm_role_inversion.scan", probe="p_a2_mean_difference",
         expect="ZERO",
         note="a mean difference has a null of ZERO. Gate 16's first run accused MD 6.900 of "
              "contradicting a crude ratio -- a confident, plausible, WRONG accusation "
              "against a correct page. This fixture keeps that fix honest."),
    dict(id="A3", cls="A3 result published under trials that did not produce it", tier=1,
         layer="store", instrument=None, probe="p_none", expect="ZERO",
         note="no instrument joins pooled rows back to the topic's own source list"),
    dict(id="A4", cls="A4 citation attached to a trial it does not report", tier=3,
         layer="store", instrument="scripts/gate_benchmark_pmid_names_its_trial",
         probe="p_none", expect="ZERO",
         note="TIER 3: the only instrument needs PubMed titles. Measured 2026-08-28 with an "
              "empty cache it decides nothing on all 157 fields and EXITS 0."),

    # ---- Quantity ---------------------------------------------------------------------
    dict(id="Q1", cls="Q1 numerator and denominator from different populations", tier=1,
         layer="store", instrument=None, probe="p_none", expect="ZERO"),
    dict(id="Q2", cls="Q2 interim row where a complete one exists", tier=1, layer="store",
         instrument=None, probe="p_none", expect="ZERO"),
    dict(id="Q3", cls="Q3 narrative interval differing from the declared method", tier=1,
         layer="served", instrument=None, probe="p_none", expect="ZERO"),
    # Q4 SUPERSEDED 2026-08-29 by Q4a/Q4b -- an instrument now exists
    #     (gates/pool_rows_consistency.scan). Kept as a comment rather than deleted so the
    #     lineage from "no instrument" to "instrumented" stays readable in one file.

    # ---- Assertion --------------------------------------------------------------------
    dict(id="AS1", cls="AS1 page denying what it holds", tier=1, layer="served",
         instrument=None, probe="p_none", expect="ZERO"),
    dict(id="AS2", cls="AS2 page asserting what it lacks", tier=1, layer="served",
         instrument=None, probe="p_none", expect="ZERO"),
    dict(id="AS3", cls="AS3 page accusing itself of a defect it does not have", tier=1,
         layer="served", instrument=None, probe="p_none", expect="ZERO"),
    dict(id="AS4a", cls="AS4 stale judgement whose subject has moved", tier=1, layer="store",
         instrument="gates/gate4_judgement_reference.judgement_blocks", probe="p_gate4_bare",
         expect="DETECTED",
         note="a judgement with no reference and no dated ancestor is classified D NOTHING"),
    dict(id="AS4b", cls="AS4 stale judgement whose subject has moved", tier=1, layer="store",
         instrument="gates/gate4_judgement_reference.judgement_blocks",
         probe="p_gate4_bare_under_date", expect="ZERO",
         note="THE REALISTIC CASE. The identical judgement under one dated ancestor is "
              "scored TIMESTAMPED, so the kind-D ratchet never fires."),
    dict(id="AS5", cls="AS5 truncated hash presented as complete", tier=1, layer="store",
         instrument="gates/gate4_judgement_reference.judgement_blocks", probe="p_gate4_fake_hash",
         expect="ZERO",
         note="WORSE THAN A MISS. An 8-character fake sha256 promotes the judgements beneath "
              "it to VERSIONED and RAISES the corpus integrity metric."),
    dict(id="AS6", cls="AS6 falsy value reaching the reader", tier=1, layer="served",
         instrument=None, probe="p_falsy_served", expect="ZERO",
         note="the probe proves the fixture really renders 'None' in reader-facing text"),

    # ---- Structure --------------------------------------------------------------------
    # S1 SUPERSEDED 2026-08-29 by S1a/S1b -- see gates/pool_rows_consistency.scan
    dict(id="S2", cls="S2 certainty rating over an unadjudicated assessment", tier=1,
         layer="store", instrument=None, probe="p_none", expect="ZERO"),
    # S3 SUPERSEDED 2026-08-29 by S3a/S3b/S3c -- the join the old note said was missing
    #     now exists in gates/noninferiority_pooling.scan
    dict(id="S4", cls="S4 partial repair, one copy fixed and another not", tier=1,
         layer="store+served", instrument=None, probe="p_none", expect="ZERO"),

    # ---- the gate-3 class, which DOES have a detector ----------------------------------
    dict(id="X1", cls="X1 two spellings of one reason, two different answers", tier=1,
         layer="store", instrument="gates/gate3_one_reason_field.scan", probe="p_gate3_divergent",
         expect="DETECTED"),
    dict(id="Y1", cls="Y1 estimate outside its own confidence interval", tier=1,
         layer="served", instrument="gates/interval_contains_point.findings",
         probe="p_interval_outside", expect="DETECTED",
         note="the first unit here that runs on content we did not write; measured 0% FP on "
              "15 fixture negatives and it found a real contradiction in a Cochrane review"),
    dict(id="Y2", cls="Y1 estimate outside its own confidence interval", tier=1,
         layer="served", instrument="gates/interval_contains_point.findings",
         probe="p_interval_inside", expect="ZERO",
         note="KNOWN NEGATIVE: a valid interval must NOT fire"),
    # ---- S3 / Q4 / S1: instrumented 2026-08-29, gates 13 and 14 ------------------------
    dict(id="S3a", cls="S3 non-inferiority trial pooled as superiority", tier=1, layer="store",
         instrument="gates/noninferiority_pooling.scan", probe="p_s3_pooled_as_superiority",
         expect="DETECTED",
         note="joins on an EXTERNAL 46-registration list, not on inputs.trials[].design, "
              "which is populated on 93/407 and holds recruitment status (COMPLETED, "
              "TERMINATED) rather than design"),
    dict(id="S3b", cls="S3 non-inferiority trial pooled as superiority", tier=1, layer="store",
         instrument="gates/noninferiority_pooling.scan", probe="p_s3_model_answer",
         expect="ZERO",
         note="MODEL ANSWER: a pool that records the trial's own estimand and its margin must "
              "NOT be accused. A detector that fires here drives the corpus away from "
              "recording margins."),
    dict(id="S3c", cls="S3 non-inferiority trial pooled as superiority", tier=1, layer="store",
         instrument="gates/noninferiority_pooling.scan", probe="p_s3_empty_margin",
         expect="DETECTED",
         note="a margin FIELD whose value is None records nothing and must not launder the "
              "block"),
    dict(id="Q4a", cls="Q4 pooled k disagreeing with the rows behind it", tier=1, layer="store",
         instrument="gates/pool_rows_consistency.scan", probe="p_q4_disagrees",
         expect="DETECTED"),
    dict(id="Q4b", cls="Q4 pooled k disagreeing with the rows behind it", tier=1, layer="store",
         instrument="gates/pool_rows_consistency.scan", probe="p_q4_refusal",
         expect="ZERO",
         note="MODEL ANSWER: 26 of this corpus's 27 k-vs-rows disagreements are declared "
              "refusals stating the k they would have pooled. Excluded by their DECLARED "
              "STATE, never by a count."),
    dict(id="S1a", cls="S1 outcome published with no rows behind it", tier=1, layer="store",
         instrument="gates/pool_rows_consistency.scan", probe="p_s1_no_rows",
         expect="DETECTED",
         note="corpus baseline is a MEASURED zero; this fixture is the only proof the leg "
              "can fire"),
    dict(id="S1b", cls="S1 outcome published with no rows behind it", tier=1, layer="store",
         instrument="gates/pool_rows_consistency.scan", probe="p_s1_refuses",
         expect="ZERO", note="MODEL ANSWER: nothing behind it, and it says so."),
    dict(id="X2", cls="X1 two spellings of one reason, two different answers", tier=1,
         layer="store", instrument="gates/gate3_one_reason_field.scan", probe="p_gate3_identical",
         expect="ZERO", note="KNOWN NEGATIVE: identical text under two names must NOT fire"),
]

# tier-2 instances live in the lane's plant registries and are run against the real corpus.
TIER2_SOURCES = ("plants.py (28 instances, 11 classes)",
                 "plants_r2.py (5 positive controls at the gates' own reading sites)",
                 "plants_r3.py (12 instances, 7 classes)")
