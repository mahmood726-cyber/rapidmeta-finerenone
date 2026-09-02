"""Page-standard properties, as PREDICATES over the object.

WHY THIS MODULE EXISTS
======================

A property that can only ever report HELD is not a check, in the same way that a
liveness probe that can only report "alive" is not a check. Before this module,
five of the page-standard properties were emitted as::

    props["P1_executed_search"] = prop(
        HELD, f"{_dbs} database queries recorded verbatim with dates and counts; ...")

-- a constant verdict beside a sentence DESCRIBING what ought to be true, computed
from nothing that could contradict it. The count `_dbs` is the length of a list;
the words "recorded verbatim with dates and counts" were never checked against
any query, date or count. That is a marker satisfiable by assertion, which is a
PASSWORD, and it was the password in production:

    AZILSARTAN_HTN_AUTO_FULL_REVIEW.html
      P1_executed_search  HELD  "2 database queries recorded verbatim ..."
      ...while the page's own PubMed card renders
      <pre>NOT EXECUTED FOR THIS TOPIC</pre>

Measured on the served surface at the time of writing: 15 such contradictions on
13 of the 19 served pages that carry the property table -- 68%. Until this is
fixed every other green the project holds is unaudited, INCLUDING the gates
written to audit it, because those gates read the marker.

WHAT CHANGED
============

Each property below is a pure function of the object returning `(state, reason)`.
Three consequences, and the third is the point:

1. It can be called from a test with a hand-built object, so a negative test can
   plant the defect and watch the property refuse.
2. Its reason is BUILT FROM WHAT WAS FOUND, not from what should have been found.
   A reason that names the offending database, cell or field is a reason a reader
   can check; "recorded verbatim with dates and counts" is not.
3. Every one of them has a reachable non-HELD branch. That is asserted mechanically
   by `scripts/test_properties_can_refuse.py`, which plants a defect per property
   and fails if the property still holds.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
=========================================

It does not decide whether a query is a GOOD query, whether a source sentence
SUPPORTS the value quoted beside it, or whether criteria are well chosen. Those
are judgements. It decides only whether the thing the marker CLAIMS is present is
present -- which is the claim the marker makes, and the claim that was false.

A refusal here is a complete outcome. Nothing in this module upgrades a refusal
into a hold by relaxing what it asks for.
"""
from __future__ import annotations

import re

HELD = "HELD"
REFUSING = "REFUSING"
NOT_ASSESSABLE = "NOT-ASSESSABLE"

# A query that is one of these is not a query. Anchored and whole-string: a real
# PubMed query may legitimately contain the word "none" inside a term, and a
# substring test would refuse it.
_PLACEHOLDER_QUERY = re.compile(
    r"^\s*(?:not\s+executed.*|not\s+run.*|n/?a|none|pending.*|tbd|todo|-+|\?+)?\s*$",
    re.I | re.S)


def _is_placeholder_query(q) -> bool:
    """True when a 'query as executed' field does not hold a query."""
    if q is None:
        return True
    if not isinstance(q, str):
        return False          # a structured query is a query; type is checked elsewhere
    return bool(_PLACEHOLDER_QUERY.match(q))


def _quote(items, limit=3):
    items = list(items)
    shown = ", ".join(repr(x) for x in items[:limit])
    return shown + (" and %d more" % (len(items) - limit) if len(items) > limit else "")


# ---------------------------------------------------------------------------
# P1 -- the search was EXECUTED, and the record says what it returned.
# ---------------------------------------------------------------------------
def p1_executed_search(obj):
    dbs = ((obj.get("search") or {}).get("databases")) or []
    if not dbs:
        return REFUSING, ("No database record on this object, so there is no executed "
                          "search to report.")

    placeholders, undated, uncounted, executed = [], [], [], []
    for d in dbs:
        name = d.get("database") or "<unnamed database>"
        if _is_placeholder_query(d.get("query_as_executed")):
            placeholders.append("%s (%r)" % (name, (d.get("query_as_executed") or "")[:40]))
            continue
        if not d.get("date_executed"):
            undated.append(name)
        if d.get("records_returned") is None and d.get("total_count") is None:
            uncounted.append(name)
        executed.append(name)

    if placeholders:
        return REFUSING, (
            "%d of %d database entries carry no query. %s holds a placeholder where the "
            "query as executed belongs, so that search was NOT RUN and the page must not "
            "report it as one. The %d that were run are %s."
            % (len(placeholders), len(dbs), _quote(placeholders), len(executed),
               _quote(executed) or "none"))
    if undated or uncounted:
        return REFUSING, (
            "%d queries were run, but the record is incomplete: %s carry no execution date "
            "and %s carry no result count. A search whose yield is unrecorded cannot support "
            "a PRISMA identification count."
            % (len(executed), _quote(undated) or "none", _quote(uncounted) or "none"))

    # THE PAGE ALREADY SAYS THIS, AND P1 WAS NOT LISTENING.
    #
    # `ssot/projectors.py:545` renders a NOT-READY banner whenever `search.strategy` is
    # absent: "No systematic search was run (no attestation can discharge this) -- The
    # included set is a named two-trial programme rather than the yield of a database
    # search. Nothing on this page should be read as though a systematic search had been
    # performed." That banner is HONEST and CORRECT.
    #
    # P1 read `search.databases` and the banner reads `search.strategy` -- two keys on one
    # block, with nothing asserting they agree. Measured on the served surface: 17 of the
    # 19 pages carrying the property table serve P1_executed_search HELD directly beside
    # that sentence. A reader sees a green "executed search" property on a page that tells
    # them no search was executed.
    #
    # THE MARKER IS THE DEFECT, NOT THE BANNER. Running a couple of registry lookups is
    # not a systematic search, and P1 must not certify one. This refuses instead, and names
    # the queries that WERE run so the refusal costs nothing that was actually done.
    if not (obj.get("search") or {}).get("strategy"):
        return REFUSING, (
            "%d database quer%s executed (%s), but the object declares NO SEARCH STRATEGY. "
            "Queries against a registry are not a systematic search, and this page's own "
            "readiness banner already says so. What was run is recorded above; what is "
            "refused is the claim that it constitutes an executed search."
            % (len(executed), "y was" if len(executed) == 1 else "ies were",
               _quote(executed, 4)))

    return HELD, (
        "%d database quer%s executed, each with its query string, its execution date and "
        "its result count: %s."
        % (len(executed), "y" if len(executed) == 1 else "ies", _quote(executed, 4)))


# ---------------------------------------------------------------------------
# P2 -- k at every stage, and the stages are consistent with each other.
# ---------------------------------------------------------------------------
# THE FILTER CHAIN, AND ONLY THE FILTER CHAIN.
#
# The first version of this list read
#   ("k0_surfaced", "k2_role_located", "k3_experimental", "k4_comparator",
#    "k_included_in_object")
# and refused on SIX of the eighteen checked pages, every one of them at the same
# transition, k4_comparator -> k_included_in_object. Six pages failing at one
# transition is a statement about the instrument, not about six pages: `k4_comparator`
# is NOT a filter stage. `ssot/apply_paper_register_2026_08_20.py:197` defines it as
# "Records where the topic drug is the comparator instead" -- a SIBLING role bucket
# beside k3_experimental, k5_background and kNA_not_assessable, all of which partition
# k2_role_located. Bococizumab carries k4_comparator=0 with 6 trials included, which is
# ordinary and not a contradiction: none of its 6 uses bococizumab as the comparator.
#
# So the monotone chain runs THROUGH k3_experimental, and the role buckets hang off
# k2_role_located. Had this shipped, the gate would have manufactured six defects on
# correct pages -- the direction that costs most, because a flagged page gets "fixed".
_K_STAGES = ("k0_surfaced", "k2_role_located", "k3_experimental", "k_included_in_object")

# Present-and-numeric only. Their SUM against k2_role_located is NOT asserted: on
# bococizumab it is 18+0+3+1=22 against a located count of 21, and whether that is an
# off-by-one defect or a schema nuance was not established. An invariant that has not
# been established does not get to fail a page.
_K_ROLE_BUCKETS = ("k3_experimental", "k4_comparator", "k5_background",
                   "kNA_not_assessable")


def p2_k_cascade(obj):
    casc = obj.get("k_cascade") or {}
    missing = [s for s in _K_STAGES if casc.get(s) is None]
    if missing:
        return REFUSING, ("The cascade does not report every stage; %s %s absent, so k "
                          "cannot be followed from what the search surfaced to what the "
                          "object holds." % (_quote(missing), "is" if len(missing) == 1 else "are"))

    vals = [(s, casc[s]) for s in _K_STAGES]
    rises = [(a, av, b, bv) for (a, av), (b, bv) in zip(vals, vals[1:]) if bv > av]
    if rises:
        a, av, b, bv = rises[0]
        return REFUSING, (
            "The cascade RISES at %s -> %s (%s to %s). A later stage cannot hold more "
            "trials than the stage that fed it; one of the two counts is measuring a "
            "different population from the one its name claims." % (a, b, av, bv))

    rem = casc.get("k_unscreened_remainder")
    tail = ("unscreened remainder %s" % rem) if rem is not None else (
        "UNSCREENED REMAINDER NOT STATED -- which is not the same as zero")
    return HELD, ("k at every stage, non-increasing: %s; %s."
                  % ("; ".join("%s %s" % (s, v) for s, v in vals), tail))


# ---------------------------------------------------------------------------
# P3 -- the inclusion criteria are recorded, and pre-specification is DECIDED.
# ---------------------------------------------------------------------------
def p3_inclusion_criteria(obj):
    prov = (obj.get("screening") or {}).get("eligibility_provenance")
    if not prov:
        return REFUSING, "No criteria provenance block on this object."
    if "predefined" not in prov:
        return REFUSING, ("A criteria provenance block is present but carries no "
                          "`predefined` key, so pre-specification was never asked.")

    predefined = prov.get("predefined")
    if predefined is None:
        return NOT_ASSESSABLE, (
            "A criteria provenance block is present and `predefined` is null (state %r). "
            "Null is not false and it is not true: this object declares neither a protocol "
            "statement nor a post-hoc admission, so pre-specification cannot be decided "
            "either way. It is reported as undecided rather than held."
            % (prov.get("state"),))
    if not isinstance(predefined, bool):
        return REFUSING, ("`predefined` is %r, which is neither true nor false. A "
                          "self-labelled string cannot settle pre-specification."
                          % (predefined,))

    return HELD, ("Criteria provenance recorded with predefined=%s (state %r)."
                  % (predefined, prov.get("state")))


# ---------------------------------------------------------------------------
# P4 -- every precondition carries a verdict AND the authority it was decided under.
# ---------------------------------------------------------------------------
def p4_preconditions(obj, expected_names=()):
    block = obj.get("precondition_verdict") or {}
    verdicts = block.get("verdicts") or {}
    if not verdicts:
        return REFUSING, "No precondition verdicts recorded."

    missing = [n for n in expected_names if n not in verdicts]
    unauthorised = sorted(n for n, v in verdicts.items() if not (v or {}).get("authority"))
    reasonless = sorted(n for n, v in verdicts.items() if not (v or {}).get("reason"))
    if missing:
        return REFUSING, ("%d precondition(s) in the standard have no verdict on this "
                          "object: %s." % (len(missing), _quote(missing)))
    if unauthorised or reasonless:
        return REFUSING, (
            "%s carry a verdict with no cited authority and %s carry a verdict with no "
            "reason. A verdict whose authority is unnamed cannot be disagreed with, which "
            "is the whole purpose of recording it."
            % (_quote(unauthorised) or "none", _quote(reasonless) or "none"))

    counts = {}
    for v in verdicts.values():
        counts[v.get("verdict")] = counts.get(v.get("verdict"), 0) + 1
    return HELD, ("All %d preconditions recorded with a verdict and a cited authority: %s."
                  % (len(verdicts),
                     ", ".join("%s %s" % (n, s) for s, n in sorted(counts.items(),
                                                                   key=lambda x: str(x[0])))))


# ---------------------------------------------------------------------------
# P5 -- every READ cell carries the source it was read from AND the sentence.
# ---------------------------------------------------------------------------
def p5_extraction_table(obj):
    cells = ((obj.get("extraction") or {}).get("cells")) or []
    if not cells:
        return REFUSING, "No extraction table on this object."

    unlabelled = [c.get("field", "<unnamed>") for c in cells if not c.get("label")]
    read = [c for c in cells if c.get("label") == "READ"]
    derived = [c for c in cells if c.get("label") == "DERIVED"]

    no_path = [c.get("field", "<unnamed>") for c in read if not c.get("source_path")]
    no_text = [c.get("field", "<unnamed>") for c in read if not c.get("verbatim")]
    # A DERIVED cell names its method in EITHER of two shapes the corpus actually uses.
    # Requiring `derived_by` alone refused ablation-af-heart-failure's standard-error cell,
    # which carries source_path='computed from each printed 95% interval' and
    # verbatim='se = (ln(upper) - ln(lower)) / (2 x 1.959964)' -- the method named more
    # precisely than a `derived_by` string would have named it. That was the SECOND
    # over-strict predicate in this module (see _K_STAGES for the first), so the honest
    # statement is that this module's error rate has been corrected AGAINST the corpus and
    # is therefore not independently measured. Both corrections ran the same direction:
    # refusing correct pages.
    no_method = [c.get("field", "<unnamed>") for c in derived
                 if not (c.get("derived_by") or (c.get("source_path") and c.get("verbatim")))]

    if unlabelled:
        return REFUSING, ("%d cell(s) carry no READ/DERIVED label: %s. A cell with no label "
                          "is not evidence." % (len(unlabelled), _quote(unlabelled)))
    if no_path or no_text or no_method:
        return REFUSING, (
            "Of %d READ cells, %d carry no source path (%s) and %d carry no verbatim "
            "sentence (%s); of %d DERIVED cells, %d do not name the method (%s). The "
            "table cannot be described as carrying the sentence each value was read from."
            % (len(read), len(no_path), _quote(no_path) or "none",
               len(no_text), _quote(no_text) or "none",
               len(derived), len(no_method), _quote(no_method) or "none"))

    return HELD, ("%d cells: %d READ, each with a source path and the verbatim sentence; "
                  "%d DERIVED, each naming the method."
                  % (len(cells), len(read), len(derived)))


# ---------------------------------------------------------------------------
# The table the builder walks. Adding a property here without a reachable
# non-HELD branch fails scripts/test_properties_can_refuse.py.
# ---------------------------------------------------------------------------
PROPERTIES = {
    "P1_executed_search": p1_executed_search,
    "P2_k_cascade": p2_k_cascade,
    "P3_inclusion_criteria": p3_inclusion_criteria,
    "P4_preconditions": p4_preconditions,
    "P5_extraction_table": p5_extraction_table,
}
