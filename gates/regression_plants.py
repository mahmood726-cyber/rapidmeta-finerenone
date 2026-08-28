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
    dict(id="A2", cls="A2 role inversion on the arms", tier=1, layer="store",
         instrument=None, probe="p_none", expect="ZERO",
         note="no instrument reads comparator/intervention roles for inversion"),
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
    dict(id="Q4", cls="Q4 pooled k disagreeing with the rows behind it", tier=1, layer="store",
         instrument=None, probe="p_k_vs_rows", expect="ZERO",
         note="no SHIPPED instrument. The probe computes the disagreement to prove the "
              "fixture is genuinely defective, then reports that nothing we own looks."),

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
    dict(id="S1", cls="S1 outcome published with no rows behind it", tier=1, layer="store",
         instrument=None, probe="p_none", expect="ZERO"),
    dict(id="S2", cls="S2 certainty rating over an unadjudicated assessment", tier=1,
         layer="store", instrument=None, probe="p_none", expect="ZERO"),
    dict(id="S3", cls="S3 non-inferiority trial pooled as superiority", tier=1, layer="store",
         instrument=None, probe="p_none", expect="ZERO",
         note="out/blind-review/noninferiority_trials.json lists 46 such registrations and "
              "nothing joins it to the pools"),
    dict(id="S4", cls="S4 partial repair, one copy fixed and another not", tier=1,
         layer="store+served", instrument=None, probe="p_none", expect="ZERO"),

    # ---- the gate-3 class, which DOES have a detector ----------------------------------
    dict(id="X1", cls="X1 two spellings of one reason, two different answers", tier=1,
         layer="store", instrument="gates/gate3_one_reason_field.scan", probe="p_gate3_divergent",
         expect="DETECTED"),
    dict(id="X2", cls="X1 two spellings of one reason, two different answers", tier=1,
         layer="store", instrument="gates/gate3_one_reason_field.scan", probe="p_gate3_identical",
         expect="ZERO", note="KNOWN NEGATIVE: identical text under two names must NOT fire"),
]

# tier-2 instances live in the lane's plant registries and are run against the real corpus.
TIER2_SOURCES = ("plants.py (28 instances, 11 classes)",
                 "plants_r2.py (5 positive controls at the gates' own reading sites)",
                 "plants_r3.py (12 instances, 7 classes)")
