"""UNIT 4 -- a certainty rating may not stand over an unadjudicated risk-of-bias judgement.

THE REAL DEFECT THIS CAME FROM. MASTER-DEFECT-REGISTER row A10, quoted:

    "A10 | GRADE certainty rendered where RoB is unadjudicated -- generator fixed corpus-wide
     | 3 pages, 27 outcomes / 19 topics | LANDED, 2 unrebuilt"

and the row that defines what unadjudicated MEANS here, A11:

    "A11 | 'No information' used as a RoB 2 domain/overall judgement -- invalid per the tool
     | 21 | LANDED, unrebuilt"

A10 was fixed at the generator and never instrumented, so nothing stands between the corpus
and its return. That is the specific hole: a class marked LANDED with no standing measurement
is a class we will rediscover.

WHY IT MATTERS IN THE READER'S DIRECTION. Risk of bias is an INPUT to certainty. Rating
certainty before the input exists does not produce a weaker rating -- it produces a rating that
did not consider the thing most likely to lower it, and GRADE's own arithmetic then presents it
with the authority of a completed assessment.

WHY THE BOUNDARY IS STRUCTURAL AND NOT NUMERIC. Two typed fields inside ONE ENCLOSING BLOCK,
and the question is whether the second holds a judgement at all. Nothing is scored, nothing is
thresholded, and there is no number that could be nudged until the page goes quiet.
"No information" is not a low value on a scale -- it is invalid as a RoB 2 judgement, per the
tool, which is what A11 records.

THE DENOMINATOR RULE, WHICH THIS CLASS EXISTS TO BREAK. A query on a typed field measures that
FIELD'S ADOPTION, not the condition it names. So the absence of a RoB field is NOT read as
absence of adjudication -- it is read as NOT ASSESSABLE and reported as its own kind:

    OUT OF POPULATION  no certainty field, or certainty withheld  -> not examined
    NOT ASSESSABLE     certainty rated, NO rob field at this layer -> its own kind, never clean
    ADJUDICATED        certainty rated, rob holds a judgement      -> clean
    UNADJUDICATED      certainty rated, rob present and empty      -> the finding

THIS DETECTOR IS THEREFORE A FLOOR, SAID PLAINLY. Every count it produces under-finds by
exactly the NOT-ASSESSABLE column, and `assessable()` returns that column so the floor can
never be quoted as a total.

THE MODEL ANSWER, asserted to pass -- and it is the whole reason this detector is safe. The
behaviour this class enforces is *withhold the rating until the input exists*. So an outcome
that holds an unadjudicated RoB and states NO certainty, or states certainty as PENDING, is
the EXEMPLARY CORRECT FORM and must not fire. If this detector accused a withheld rating, the
cheapest way to satisfy it would be to publish a rating -- driving the corpus toward exactly
the defect the class is about. A detector that flags the model answer is worse than no
detector.

Two further negatives are model answers in their own right: a certainty rated over a RoB
adjudicated as HIGH risk is correct (a bad judgement is still a judgement), and a certainty of
VERY LOW is a rating like any other and is not evidence of a missing input.

REACH, STATED. This reads a store object. A certainty rendered into a page whose RoB lives in
a different object, with nothing holding both, is out of reach here.
"""
from __future__ import annotations

CERTAINTY_FIELDS = ("certainty", "grade_certainty", "certainty_of_evidence",
                    "grade", "grade_level", "certainty_level")

ROB_FIELDS = ("rob_overall", "risk_of_bias_overall", "rob", "risk_of_bias",
              "rob_judgement", "rob2_overall")

# The four GRADE levels, and nothing else. A field holding anything outside this set is not a
# RATING -- it is a status, and a status is how a rating is correctly withheld.
GRADE_LEVELS = ("high", "moderate", "low", "very low", "very-low", "verylow")

# Values that are PRESENT and are not a judgement. "no information" is here on the authority
# of the RoB 2 tool itself, recorded as A11: it is not a permitted domain or overall judgement.
NOT_A_JUDGEMENT = ("", "no information", "no info", "pending", "unadjudicated",
                   "not assessed", "not adjudicated", "unknown", "tbd", "n/a", "na",
                   "?", "-", "--", "—", "–", "none", "null")


def _norm(v):
    if v is None:
        return None
    if isinstance(v, str):
        return " ".join(v.strip().lower().split())
    return v


def is_rating(v):
    """True only for one of GRADE's four levels. Everything else is a status, not a rating."""
    n = _norm(v)
    return isinstance(n, str) and n in GRADE_LEVELS


def is_adjudicated(v):
    """True when the field holds an actual risk-of-bias judgement."""
    n = _norm(v)
    if n is None or not isinstance(n, str):
        return False
    return n not in NOT_A_JUDGEMENT


def _blocks(obj, path=""):
    if isinstance(obj, dict):
        yield path or "<root>", obj
        for k, v in obj.items():
            yield from _blocks(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _blocks(v, "%s[%d]" % (path, i))


def _read(block):
    cf = next((f for f in CERTAINTY_FIELDS if f in block), None)
    rf = next((f for f in ROB_FIELDS if f in block), None)
    return cf, rf


def assessable(obj):
    """(rated, not_assessable, adjudicated, unadjudicated) -- the denominator, always.

    `rated` is the real population: blocks that state a GRADE level. Quoting a violation count
    against anything else measures how widely the certainty field is adopted.
    """
    rated = na = ok = bad = 0
    for _, block in _blocks(obj):
        if not isinstance(block, dict):
            continue
        cf, rf = _read(block)
        if cf is None or not is_rating(block.get(cf)):
            continue
        rated += 1
        if rf is None:
            na += 1
        elif is_adjudicated(block.get(rf)):
            ok += 1
        else:
            bad += 1
    return rated, na, ok, bad


def findings(obj, source="?"):
    """Every GRADE rating standing over a risk-of-bias field that holds no judgement."""
    out = []
    for path, block in _blocks(obj):
        if not isinstance(block, dict):
            continue
        cf, rf = _read(block)
        if cf is None or rf is None:
            continue
        if not is_rating(block.get(cf)):
            continue
        if is_adjudicated(block.get(rf)):
            continue
        out.append({
            "source": source, "block": path,
            "certainty_field": cf, "certainty": block.get(cf),
            "rob_field": rf, "rob": block.get(rf),
            "quote": "%s: %s=%r rated over %s=%r" % (
                path, cf, block.get(cf), rf, block.get(rf)),
        })
    return out


# ---------------------------------------------------------------------------
# CONTROLS, anchored to fixtures.
# ---------------------------------------------------------------------------
KNOWN_NEGATIVES = [
    # THE MODEL ANSWER: a rating standing over an adjudicated judgement.
    {"certainty": "moderate", "rob_overall": "low risk of bias"},
    # THE MODEL ANSWER THAT MATTERS MOST -- the rating is WITHHELD while the input is missing.
    # If this fired, the cheapest way to satisfy the detector would be to publish a rating.
    {"rob_overall": "no information"},
    {"certainty": "pending", "rob_overall": "no information"},
    {"certainty": None, "rob_overall": ""},
    {"certainty": "not rated", "rob_overall": "no information"},
    # a BAD judgement is still a judgement: rating over high risk of bias is correct
    {"certainty": "very low", "rob_overall": "high risk of bias"},
    {"certainty": "low", "rob_overall": "some concerns"},
    # adjudicated, spelled by the RoB 2 vocabulary
    {"grade_certainty": "high", "risk_of_bias_overall": "Low risk of bias"},
    {"certainty_of_evidence": "MODERATE", "rob": "some concerns"},
    # no certainty field at all: out of the population, not clean and not accused
    {"rob_overall": "pending"},
    # certainty rated, no rob field HELD AT THIS LAYER: not assessable, never a finding,
    # because a query on a typed field measures that field's adoption
    {"certainty": "high"},
    {"results": {"by_outcome": {"primary": {"certainty": "low"}}}},
    # nested and correct
    {"by_outcome": {"primary": {"certainty": "high", "rob_overall": "low risk of bias"},
                    "safety": {"certainty": "low", "rob_overall": "some concerns"}}},
]

KNOWN_POSITIVES = [
    # A10 as registered: a GRADE level over a RoB that holds no judgement.
    {"certainty": "moderate", "rob_overall": "no information"},
    # A11's exact value, which the RoB 2 tool does not permit as a judgement
    {"grade_certainty": "high", "risk_of_bias_overall": "No information"},
    # the empty and null spellings of the same absence
    {"certainty": "low", "rob_overall": ""},
    {"certainty": "very low", "rob_overall": None},
    {"certainty_of_evidence": "HIGH", "rob": "pending"},
    # a falsy rendered into the field -- D1 and A10 meeting
    {"certainty": "moderate", "rob_overall": "—"},
    # nested under an outcome, where the corpus actually puts it
    {"results": {"by_outcome": {"primary": {"certainty": "high",
                                            "rob_overall": "not assessed"}}}},
]


def control():
    """(n_negatives, n_false_positives, examples), (n_positives, n_missed, examples)."""
    fp = [o for o in KNOWN_NEGATIVES if findings(o, "control")]
    missed = [o for o in KNOWN_POSITIVES if not findings(o, "control")]
    return (len(KNOWN_NEGATIVES), len(fp), fp), (len(KNOWN_POSITIVES), len(missed), missed)
