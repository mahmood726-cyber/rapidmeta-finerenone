"""UNIT 3 -- a declared count must equal the rows it is a count OF.

THE REAL DEFECT THIS CAME FROM. MASTER-DEFECT-REGISTER row A17, quoted:

    "A17 | Index badge disagrees with its own page (4 trials claimed, 3 shown) | >=1 | OPEN"

and the standing plant Q4, whose probe carried this admission until now:

    "p_k_vs_rows: No shipped instrument. Prove the fixture is genuinely defective, then
     report the zero.  ...  k=5 over 2 rows; no shipped module joins k to its rows"

Q4 is the class where the corpus states a number and separately holds the things the number
counts, and the two disagree. A reader cannot see both -- the badge is on the index, the rows
are on the page -- so the disagreement is invisible at the point of reading and only visible
to something that holds both at once.

WHY THE BOUNDARY IS STRUCTURAL AND NOT NUMERIC. The boundary is an ENCLOSING BLOCK: the count
and the rows must be siblings inside one object. `k` at the top of a topic and `per_trial`
three levels down under a different outcome are not a claim about each other, and joining them
would manufacture findings out of layout. Inside one block, equality is exact -- there is no
tolerance, no threshold, and nothing that goes quiet when a number is nudged.

THREE STATES, NEVER TWO (standing orders 9d). This is the class where a two-state answer does
the most damage, because most outcome blocks legitimately hold one side and not the other:

    OUT OF POPULATION  neither a count field nor a row list      -> not examined
    NOT ASSESSABLE     one side present, the other absent        -> its own kind, never clean
    AGREEING           count == len(rows)                        -> clean
    DISAGREEING        count != len(rows)                        -> the finding

`assessable()` returns all four so a caller must print the denominator. A corpus in which no
block holds both fields would otherwise report "0 disagreements" and be read as coverage, when
what it measured was that the join never happens -- the standing rule that a no-match bucket
measures the JOIN, not the world.

THE MODEL ANSWER, asserted to pass. The behaviour this class enforces is *state the count and
show the rows, and let them agree*. So a block holding k=2 over two rows must not fire. And
the second model answer matters more: a block that holds rows and states NO count is the
correct form of refusing to claim a number you have not derived, and it must not fire either.
A detector that demanded a count wherever rows exist would push the corpus to manufacture the
very claims this project's derive-or-refuse rule exists to prevent.

REACH, STATED. This joins two fields inside one store object. A count rendered only into an
index badge, with the rows on a different page and nothing holding both, is out of reach here
and is not counted as clean -- that join is a served-layer problem and is named as such.
"""
from __future__ import annotations

import re

# HOW A COUNT FINDS ITS ROWS -- DERIVED FROM THE NAMES, NOT HAND-LISTED.
#
# Measured 2026-08-29 on a real store object
# (outputs/extraction_audit/truthcert/NORMOTHERMIC_TRANSPLANT_NMA_REVIEW.json): the first
# version of this module carried an explicit list of count fields and an explicit list of row
# fields. That file holds `n_fixes_applied` beside `fixes_applied` -- a count and its rows,
# sitting as siblings -- and the module examined NEITHER, because neither name was on either
# hand-list. It reported the file NOT ASSESSABLE and would have been read as coverage.
#
# That is this project's own recurring defect, named in the standing orders: testing for the
# presence of a good thing over an OPEN VOCABULARY, where a hand-listed set is a SAMPLE and
# everything outside it is silently missed. It has now been met in a regex, a path list, a
# label matcher, a proxy join, an estimand check, a trial-field extractor -- and, on the first
# real file it was pointed at, in this module. Do not make it seven.
#
# So the pairing is DERIVED from a naming relation the corpus already uses:
#
#     n_X   num_X   number_of_X   k_X   X_count   count_of_X      counts the sibling list  X
#
# and X is matched after stripping a trailing plural, so `n_trial` pairs with `trials`. The
# relation is structural: no vocabulary to maintain, and a new field name is covered the day
# it is written. The only hand-listed part is the small set of BARE conventional names below,
# which name no subject and so cannot be derived from -- and each is stated with what it counts.

# Bare count names that carry a convention rather than a subject. Each maps to the row lists
# that convention points at. This list is a SAMPLE and is declared as one: a bare count under
# an unlisted name is NOT ASSESSABLE, never clean.
BARE_COUNTS = {
    "k": ("per_trial", "trials", "studies", "rows", "per_study", "contributions"),
    "n_studies": ("studies", "per_study"),
    "n_included": ("included", "trials", "studies"),
}

_COUNT_PREFIX = re.compile(r"\A(?:n|num|number_of|k|count_of)_(?P<subject>.+)\Z")
_COUNT_SUFFIX = re.compile(r"\A(?P<subject>.+)_(?:count|n)\Z")


def _singular(s):
    for suf in ("ies", "es", "s"):
        if s.endswith(suf) and len(s) > len(suf) + 1:
            return s[: -len(suf)] + ("y" if suf == "ies" else "")
    return s


def _subject_of(field):
    """The thing a count field says it counts, or None if the name declares no subject."""
    for pat in (_COUNT_PREFIX, _COUNT_SUFFIX):
        m = pat.match(field)
        if m:
            return m.group("subject")
    return None


def _is_count(block, f):
    v = block.get(f)
    return isinstance(v, int) and not isinstance(v, bool)


# ---------------------------------------------------------------------------
# MERGED 2026-08-29 from lane/undefended-classes. A DECLARED REFUSAL IS A THIRD KIND.
#
# Reconciliation that produced this: both lanes instrumented class Q4 independently. Run
# against both plant sets, this detector scored 7/7 on positives against the other's 1/7 --
# it derives the count/row pairing from the naming relation and reaches every block, where
# the other only ever looked at `results.by_outcome.<id>.k`. It therefore keeps the class.
#
# But on the real corpus it returned 38 findings where the other returned 1, and 37 of the 38
# are blocks that DECLARE they decline to pool and then state the k they WOULD have pooled,
# carrying no rows. That is not a count disagreeing with its rows; it is a refusal, and it is
# the behaviour this project wants. Firing on it makes the cheapest way to satisfy the
# detector "delete the k from your refusals", which destroys the record of how many trials
# were considered. This module's own Q4-model note states the mirror principle -- rows shown
# with no count claimed is correct, because refusing to state an underived number is correct.
#
# The exclusion is STRUCTURAL and narrow: the block must declare a refusal AND the paired row
# list must be EMPTY. `finerenone-review/primary` declares poolable=false and still carries 4
# rows against k=3, so it is still reported -- it publishes rows, and a refusal that publishes
# rows is making a claim about them.
_REFUSAL_MARKER = "the_pool_this_refusal_declines_to_report"


def _declares_refusal(block):
    if block.get("poolable") is False:
        return True
    if _REFUSAL_MARKER in block:
        return True
    reason = block.get("poolable_reason")
    return block.get("poolable") is None and isinstance(reason, str) and bool(reason.strip())


def _pairs(block):
    """Every (count_field, count, row_field, n_rows) pair that is SIBLINGS in this block."""
    if not isinstance(block, dict):
        return
    lists = {k: v for k, v in block.items() if isinstance(v, list)}
    refuses = _declares_refusal(block)
    for f in block:
        if not _is_count(block, f):
            continue
        subj = _subject_of(f)
        if subj is not None:
            for lf in lists:
                if _singular(lf) == _singular(subj):
                    if refuses and not lists[lf]:
                        continue
                    yield f, block[f], lf, len(lists[lf])
        elif f in BARE_COUNTS:
            for lf in BARE_COUNTS[f]:
                if lf in lists:
                    if refuses and not lists[lf]:
                        continue
                    yield f, block[f], lf, len(lists[lf])


def _has_count(block):
    return any(_is_count(block, f) and (_subject_of(f) is not None or f in BARE_COUNTS)
               for f in block)


def _has_rows_for_any_count(block):
    return any(True for _ in _pairs(block))


def _blocks(obj, path=""):
    if isinstance(obj, dict):
        yield path or "<root>", obj
        for k, v in obj.items():
            yield from _blocks(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _blocks(v, "%s[%d]" % (path, i))


def assessable(obj):
    """(n_blocks, n_not_assessable, n_agreeing, n_disagreeing) -- the denominator, always.

    n_not_assessable counts blocks that state a count whose subject list is not a sibling. It
    is its own kind and is never folded into agreeing: a corpus in which the join never
    happens would otherwise report "0 disagreements" and be read as coverage, when what it
    measured was the JOIN and not the world.
    """
    blocks = na = ok = bad = 0
    for _, block in _blocks(obj):
        if not isinstance(block, dict):
            continue
        if not _has_count(block):
            continue
        blocks += 1
        pairs = list(_pairs(block))
        if not pairs:
            na += 1
        elif any(c != n for _, c, _, n in pairs):
            bad += 1
        else:
            ok += 1
    return blocks, na, ok, bad


def findings(obj, source="?"):
    """Every declared count that disagrees with the sibling row list it counts."""
    out = []
    for path, block in _blocks(obj):
        for cf, c, rf, n in _pairs(block):
            if c == n:
                continue
            out.append({
                "source": source, "block": path,
                "count_field": cf, "declared": c,
                "row_field": rf, "rows": n,
                "quote": "%s: %s=%d over %d row(s) in %s" % (path, cf, c, n, rf),
            })
    return out


# ---------------------------------------------------------------------------
# CONTROLS, anchored to fixtures.
# ---------------------------------------------------------------------------
KNOWN_NEGATIVES = [
    # THE MODEL ANSWER: the count and the rows agree.
    {"k": 2, "per_trial": [{"nct": "NCT03036124"}, {"nct": "NCT03619213"}]},
    # THE SECOND MODEL ANSWER, and the one that keeps this detector honest: rows shown, no
    # count claimed. Refusing to state a number you have not derived is correct behaviour.
    {"per_trial": [{"nct": "NCT03036124"}, {"nct": "NCT03619213"}]},
    # a count with no rows held at this layer -- NOT ASSESSABLE, and not an accusation
    {"k": 5},
    # k=0 over an empty list
    {"k": 0, "per_trial": []},
    # a participant count is not a row count, and has no row list to disagree with
    {"n": 4037, "per_trial": [{"nct": "NCT04938830"}]},
    {"n_participants": 8058, "trials": [{"nct": "NCT04938830"}]},
    # two different outcomes, each internally consistent
    {"by_outcome": {"primary": {"k": 2, "per_trial": [{"a": 1}, {"b": 2}]},
                    "safety": {"k": 1, "per_trial": [{"a": 1}]}}},
    # the count is a sibling of a DIFFERENT block's rows -- not a claim about each other
    {"k": 5, "by_outcome": {"primary": {"per_trial": [{"a": 1}, {"b": 2}]}}},
    # booleans are not counts
    {"k_trials": True, "trials": [{"a": 1}, {"b": 2}]},
    # nested lists of topics, all agreeing
    {"topics": [{"k": 1, "trials": [{"a": 1}]}, {"k": 3, "trials": [1, 2, 3]}]},
]

KNOWN_POSITIVES = [
    # the motivating fixture, verbatim from the Q4 probe
    {"k": 5, "per_trial": [{"nct": "NCT03036124"}, {"nct": "NCT03619213"}]},
    # A17 as registered: four claimed, three shown
    {"n_trials": 4, "trials": [{"a": 1}, {"b": 2}, {"c": 3}]},
    # a count that OVERSTATES by one, the shape a dropped row leaves behind
    {"k": 3, "per_trial": [{"a": 1}, {"b": 2}]},
    # a count that UNDERSTATES -- a row added and the badge not rebuilt
    {"k": 1, "per_trial": [{"a": 1}, {"b": 2}]},
    # zero claimed over rows that exist: the false-denial direction of this class
    {"k": 0, "per_trial": [{"a": 1}]},
    # nested under an outcome, where the corpus actually puts it
    {"results": {"by_outcome": {"primary": {"k_studies": 6, "studies": [{"a": 1}]}}}},
]


def control():
    """(n_negatives, n_false_positives, examples), (n_positives, n_missed, examples)."""
    fp = [o for o in KNOWN_NEGATIVES if findings(o, "control")]
    missed = [o for o in KNOWN_POSITIVES if not findings(o, "control")]
    return (len(KNOWN_NEGATIVES), len(fp), fp), (len(KNOWN_POSITIVES), len(missed), missed)
