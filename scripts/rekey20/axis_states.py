# -*- coding: utf-8 -*-
"""THE STATE FUNCTION. Pure, total, and the only place a topic acquires an outcome.

⭐ WHY THIS IS ITS OWN FILE. `scan.py` reported `A 0/0  B 0/0` for eleven of the twenty and
that string carried FOUR DIFFERENT FACTS collapsed into one shape:

    * the frame holds no review of this drug AND none of this condition   (absence)
    * the frame holds the condition, but no review of this drug           (the drug is new)
    * the frame holds the drug, but never under this condition            (pitavastatin)
    * the term list was EMPTY, so nothing was ever searched               (vacuous)

⛔⛔ THE FOURTH IS THE ONE THAT MATTERS AND IT IS INVISIBLE. `all([])` is `True`; an empty
term list scored against 1,186 rows returns `0`; and `0` prints exactly like a search that
ran and missed. Seven of the twenty have no class terms at all because the rule REFUSED to
produce one (F4/F5/F6), and two have no condition terms because the title has no condition
connective. Their zeros were never measurements.

⇒ SO THE STATE IS NAMED, ALWAYS, AND A TOPIC IS NEVER DROPPED. The two axes are scored
INDEPENDENTLY against the whole frame, so the report can say WHICH axis killed each pair
rather than only that the pair died.

THE STATES. Exhaustive and mutually exclusive over every possible input.

  REFUSED_NO_TERMS        an axis has an EMPTY term list. NOTHING WAS SEARCHED. This is not
                          a result and is never scored as one. Carries which axis was empty.
  MATCHED                 >=1 row carries both axes in title+objectives AND re-verifies in
                          objectives_verbatim alone.
  AMBIGUOUS               >=1 row carries both axes, but none verifies -- either
                          objectives_verbatim is null (UNOBTAINABLE) or the second field
                          does not repeat the match. Retrieval found it; verification
                          cannot settle it.
  PAIR_ABSENT             both axes are LIVE in the frame, and no single row carries both.
  INTERVENTION_MISMATCH   the condition axis is live; the intervention axis matches nothing.
                          The frame has the disease and not the drug.
  CONDITION_MISMATCH      the intervention axis is live; the condition axis matches nothing.
                          The frame has the drug and not this disease.
  NO_CANDIDATE_RETRIEVED  neither axis matches anything. There is nothing here to tune.

⛔ NO_CANDIDATE_RETRIEVED AND INTERVENTION_MISMATCH ARE DIFFERENT FACTS AND ARE NEVER
MERGED. Collapsing them is the error that produced "84 of 105 killed" and read as a
threshold problem when it was an absence.

⭐ PAIR_ABSENT IS A SIXTH STATE THE BRIEF'S FIVE DO NOT HOLD, AND IT IS ADDED RATHER THAN
FOLDED. When `endothelin receptor antagonist` matches 6 rows and `atrial fibrillation`
matches 40 and no row carries both, neither axis failed -- the PAIR did. Calling that
INTERVENTION_MISMATCH would assert the frame lacks the drug when the frame plainly has it,
which is the same collapse under a different name.
"""

REFUSED_NO_TERMS = "REFUSED_NO_TERMS"
MATCHED = "MATCHED"
AMBIGUOUS = "AMBIGUOUS"
PAIR_ABSENT = "PAIR_ABSENT"
INTERVENTION_MISMATCH = "INTERVENTION_MISMATCH"
CONDITION_MISMATCH = "CONDITION_MISMATCH"
NO_CANDIDATE_RETRIEVED = "NO_CANDIDATE_RETRIEVED"

ALL_STATES = (REFUSED_NO_TERMS, MATCHED, AMBIGUOUS, PAIR_ABSENT,
              INTERVENTION_MISMATCH, CONDITION_MISMATCH, NO_CANDIDATE_RETRIEVED)


def classify(n_intervention_axis, n_condition_axis, n_both, n_verified,
             have_intervention_terms, have_condition_terms):
    """-> (state, reason). Total over every input; no path returns None.

    ⚠️ THE REFUSAL IS FIRST ON PURPOSE. If it came after the zero tests, an empty term list
    would fall through to NO_CANDIDATE_RETRIEVED and a vacuous zero would be published as a
    measured one. That ordering is the whole defect this function exists to prevent.
    """
    if not have_intervention_terms or not have_condition_terms:
        which = []
        if not have_intervention_terms:
            which.append("intervention")
        if not have_condition_terms:
            which.append("condition")
        return REFUSED_NO_TERMS, (
            "the %s term list is EMPTY, so no search was performed on that axis. The zero "
            "this topic would otherwise report is vacuous, not measured" % " and ".join(which))
    if n_verified > 0:
        return MATCHED, ("%d row(s) carry both axes and re-verify in objectives_verbatim alone"
                         % n_verified)
    if n_both > 0:
        return AMBIGUOUS, (
            "%d row(s) carry both axes in title+objectives and NONE re-verifies in "
            "objectives_verbatim alone. Retrieval found a candidate; verification cannot "
            "settle it" % n_both)
    if n_intervention_axis > 0 and n_condition_axis > 0:
        return PAIR_ABSENT, (
            "both axes are live in the frame -- intervention matches %d rows, condition "
            "matches %d -- and no single row carries both. Neither axis failed; the PAIR "
            "is not in the frame" % (n_intervention_axis, n_condition_axis))
    if n_intervention_axis == 0 and n_condition_axis > 0:
        return INTERVENTION_MISMATCH, (
            "the condition axis matches %d rows and the intervention axis matches NONE. The "
            "frame holds this disease and holds no review of this drug or its class"
            % n_condition_axis)
    if n_intervention_axis > 0 and n_condition_axis == 0:
        return CONDITION_MISMATCH, (
            "the intervention axis matches %d rows and the condition axis matches NONE. The "
            "frame holds this drug and does not hold it under this condition"
            % n_intervention_axis)
    return NO_CANDIDATE_RETRIEVED, (
        "neither axis matches any row. Both term lists were non-empty and both were "
        "searched; the frame holds nothing on either. There is nothing here to tune")
