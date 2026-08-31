# -*- coding: utf-8 -*-
"""THE `ids` FIELD: one definition, shared by everything that writes or reads a search record.

WHY THIS FILE EXISTS. Every one of our six search sources stores a COUNT and not one stores
the SET. `records_returned: 137` is a number nothing can recompute, and it is the reason we
cannot write the one sentence a subscription review cannot write:

    source X contributed N records that no other source returned, and here they are.

UNIQUE YIELD is measurable. SEARCH BREADTH -- "we searched five databases" -- is a list of
names a reader cannot check. Breadth is the only axis six blinded judges gave the
comparator, and it is the weaker claim; we lose it because we do not carry the sets.

THE THREE STATES, AND THE WHOLE POINT OF THIS MODULE IS THAT THEY ARE THREE.

    ids: ["NCT02551094", ...]   the source ran and returned these
    ids: []                     THE SOURCE RAN AND RETURNED NOTHING. A fact about the world.
    ids: null                   WE DID NOT CAPTURE IT. A fact about us.

A default that folds the second into the third -- or the third into the second -- converts
"our record is incomplete" into "the literature is empty", and that is this codebase's
single most common defect: 253 silent-default handlers were counted in it.

AND THERE IS A FOURTH STATE THAT `dict.get` CANNOT SEE. A record with NO `ids` KEY AT ALL is
not the same as a record whose `ids` is null. `null` is a writer who considered the field and
declared it uncaptured; an ABSENT key is a writer who never considered it. `rec.get("ids")`
returns None for both, which is the silent default wearing the exact shape of the bug it
hides. Every read in this module goes through `state()`, which tests membership, not value.

NORMALISATION HAPPENS BESIDE THE VALUE, NEVER ON THE WAY IN.

The source's own string is stored VERBATIM. A normalised copy is stored ALONGSIDE it, in the
same positional order. Both, never one.

Two costs are already on this project's books for getting that wrong: label-equality checks
across estimands, and Crossref lowercasing DOIs while PubMed uppercases them, which produced
a 0% recall artefact that was a fact about string case and looked like a fact about coverage.
Normalising on the way in destroys the evidence needed to diagnose the next one of those.

THE NORMALISER IS ONE RULE IN ONE DIRECTION: strip all whitespace, then casefold. It is
deliberately not per-namespace. A branch per namespace is a branch that can be wrong per
namespace, and case is the only difference that has actually cost us anything.

WHAT THIS MODULE DOES NOT DO. It does not judge whether the identifiers are the RIGHT ones,
or whether the query was well aimed. `records_reported == len(ids)` compares a record against
itself, which is exactly the check that was impossible while only the count existed.
"""
import re

IDS = "ids"
IDS_NORMALISED = "ids_normalised"
IDS_ABSENT_BECAUSE = "ids_absent_because"
ID_NAMESPACE = "id_namespace"

# The states. Returned by state() and never inferred from a truthiness test anywhere else.
CAPTURED = "CAPTURED"                                    # a list with at least one entry
RAN_AND_RETURNED_NOTHING = "RAN_AND_RETURNED_NOTHING"    # ids == []
NOT_CAPTURED = "NOT_CAPTURED"                            # ids is present and null, with a reason
FIELD_ABSENT = "FIELD_ABSENT"                            # no ids key -- never considered
MALFORMED = "MALFORMED"                                  # present, but not a list of strings

_WS = re.compile(r"\s+")


def normalise(s):
    """Strip ALL whitespace, then casefold. One rule, one direction, no namespace branch."""
    return _WS.sub("", str(s)).casefold()


def state(rec):
    """Which of the four states this record is in. TESTS KEY MEMBERSHIP, NOT VALUE.

    `rec.get("ids")` is None for BOTH an absent key and an explicit null, and telling those
    apart is the reason this function exists. Nothing in this codebase may read the field
    any other way.
    """
    if not isinstance(rec, dict) or IDS not in rec:
        return FIELD_ABSENT
    v = rec[IDS]
    if v is None:
        return NOT_CAPTURED
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        return MALFORMED
    return RAN_AND_RETURNED_NOTHING if not v else CAPTURED


def make(namespace, ids=None, absent_because=None):
    """Build the field fragment. Exactly one of `ids` / `absent_because`, never both.

    `ids=[]` is a POSITIVE assertion that the source ran and returned nothing, so it is not
    interchangeable with omitting the argument. Passing neither is the uncaptured case and it
    REQUIRES a reason -- an unexplained null is how a gap becomes invisible.
    """
    if ids is not None and absent_because is not None:
        raise ValueError("a record cannot both list identifiers and say why it has none")
    if ids is None and not absent_because:
        raise ValueError("ids is null, so ids_absent_because is required and must be "
                         "non-empty -- an unexplained null is indistinguishable from a "
                         "writer who never looked")
    if ids is None:
        return {ID_NAMESPACE: namespace, IDS: None, IDS_NORMALISED: None,
                IDS_ABSENT_BECAUSE: absent_because}
    ids = [str(x) for x in ids]
    # ORDER AND DUPLICATES ARE PRESERVED. A duplicate identifier keeps the sum right and the
    # total right and is invisible to every check but a set comparison; de-duplicating here
    # would delete the evidence of it.
    return {ID_NAMESPACE: namespace, IDS: ids,
            IDS_NORMALISED: [normalise(x) for x in ids]}


def reconcile(rec, reported):
    """(ok, detail). The count we already publish, CHECKED against the set.

    NOT_CAPTURED / FIELD_ABSENT return ok=None -- NOT_ASSESSABLE. A record that names nothing
    cannot fail this and must never be reported as having passed it.
    """
    st = state(rec)
    if st in (NOT_CAPTURED, FIELD_ABSENT):
        return None, "%s: there is no set to check the count against. NOT A PASS." % st
    if st == MALFORMED:
        return False, "ids is present but is not a list of strings"
    ids = rec[IDS]
    norm = rec.get(IDS_NORMALISED)
    if not isinstance(norm, list) or len(norm) != len(ids):
        return False, ("ids_normalised must be a parallel list of the same length -- "
                       "%d verbatim against %s normalised"
                       % (len(ids), len(norm) if isinstance(norm, list) else "no"))
    if [normalise(x) for x in ids] != norm:
        return False, "ids_normalised is not the normalisation of ids, position by position"
    bad = []
    if reported is not None and reported != len(ids):
        bad.append("the record reports %s and lists %d" % (reported, len(ids)))
    if len(set(norm)) != len(norm):
        dup = sorted({x for x in norm if norm.count(x) > 1})
        bad.append("DUPLICATE identifiers after normalisation: %s" % dup[:6])
    return (not bad), ("; ".join(bad) if bad
                       else "reported == listed == distinct (%d)" % len(ids))


# --------------------------------------------------------------------- the derivations
#
# EVERYTHING BELOW IS WHY THE FIELD IS WORTH ADDING. None of it is computable from counts.

def _sets(records):
    """{label: set(normalised ids)} for records that actually captured a set.

    RECORDS IN THE OTHER THREE STATES ARE EXCLUDED AND THE CALLER IS TOLD HOW MANY. A source
    that did not capture its set is not a source that returned nothing, and letting it enter
    as an empty set would credit every OTHER source with unique yield it has not earned --
    the uncaptured source's records would score as returned-by-nobody-else.
    """
    out, skipped = {}, {}
    for label, rec in records:
        st = state(rec)
        if st in (CAPTURED, RAN_AND_RETURNED_NOTHING):
            out[label] = set(rec[IDS_NORMALISED])
        else:
            skipped[label] = st
    return out, skipped


def unique_yield(records):
    """Per source: the identifiers NO OTHER source in this set returned.

    `records` is [(label, rec), ...]. Returns the sentence a subscription review cannot
    write, as data: for each source, the records it contributed that nothing else did.
    """
    sets, skipped = _sets(records)
    out = {}
    for label, s in sets.items():
        others = set()
        for other, o in sets.items():
            if other != label:
                others |= o
        uniq = sorted(s - others)
        out[label] = {"returned": len(s), "unique": len(uniq), "unique_ids": uniq}
    return {"per_source": out,
            "union": len(set().union(*sets.values())) if sets else 0,
            "sources_counted": len(sets),
            # examined + skipped == candidates. A skip that never reaches the denominator is
            # how a clean number gets manufactured.
            "sources_skipped": skipped,
            "candidates": len(records)}


def pairwise_overlap(records):
    """|A n B| for every unordered pair, plus each side's count. Jaccard where defined."""
    sets, skipped = _sets(records)
    labels = sorted(sets)
    rows = []
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            inter = sets[a] & sets[b]
            union = sets[a] | sets[b]
            rows.append({"a": a, "b": b, "n_a": len(sets[a]), "n_b": len(sets[b]),
                         "intersection": len(inter),
                         # UNDEFINED, NOT ZERO, WHEN BOTH SIDES ARE EMPTY. 0/0 reported as
                         # 0.0 would read as "these two sources overlap in nothing", which
                         # is a claim, made from two sources that returned nothing.
                         "jaccard": (len(inter) / len(union)) if union else None})
    return {"pairs": rows, "sources_counted": len(sets), "sources_skipped": skipped,
            "candidates": len(records)}
