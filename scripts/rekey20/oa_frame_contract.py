# -*- coding: utf-8 -*-
"""CONTRACT FOR AN OPEN-ACCESS COMPARATOR FRAME. The coordination artefact, not a message.

⭐ WHY AN ARTEFACT AND NOT A MESSAGE. `ListAgents` returns 242 peer sessions, almost all
named after the same directories, so there is no way to address "the infectious-disease
frame lane" by name and broadcasting to 242 is noise. A contract in the repo coordinates
without addressing anyone: a lane that builds to it concatenates with this one, and a lane
that does not is REFUSED loudly by the consumer rather than silently producing a second,
incompatible frame.

⛔ `frame_contract.py` IS NOT MODIFIED AND MUST NOT BE. Its `CD\\d{6}` key check is correct
for the Cochrane frame it gates, and widening one contract to cover two frames deletes the
check that makes it useful. Two strict contracts, not one loose one.

⛔⛔ THE DEFECT THIS EXISTS TO CLOSE, MEASURED. `oa_retrieve.py` hard-coded
`record_kind: "systematic_review"` on every row it emitted. Four of 124 verified rows were
PROTOCOLS -- PMC12183782 ("This is a protocol for a Cochrane Review"), and PMC12964950,
which reached three separate topics. A protocol reports no results and cannot be a
comparator; the Cochrane frame contract excludes 30 of them on exactly that ground.

⇒ THE KIND WAS ASSERTED INSTEAD OF READ, and it was caught by a human reading the record's
own words, not by any gate or plant. So this contract does not accept a stated
`record_kind`: it DERIVES one from the record's own text and REFUSES when the producer's
claim disagrees. *List the kinds before the number* is only enforceable if the kinds are
read.

⚠️ AND THE VERIFICATION MATERIAL IS PART OF THE CONTRACT. A Cochrane objectives statement
is one or two sentences; an abstract is ~250 words. Verifying against an abstract makes a
match cheaper without changing a line of any rule -- 6 of 20 topics MATCHED on CDSR became
16 of 20 here. So every frame declares `verification_field_kind`, and `refuse_cross_kind`
makes comparing two frames of different kinds an error rather than a footnote.
"""
import re

GATE = "rekey20/oa_frame_contract.py"

REQUIRED = ("oa_id", "source", "title", "objectives_verbatim", "objectives_source",
            "record_kind", "is_open_access", "verification_field_kind", "provenance")

RECORD_KINDS = ("systematic_review", "protocol", "unknown")
VERIFICATION_FIELD_KINDS = ("cochrane_objectives", "abstract")

# A stable EXTERNAL identifier. Never a title: titles are retitled across versions, cannot
# be deduplicated, and cannot be joined to any enumerable source.
OA_ID = re.compile(r"^(?:PMC\d{4,}|PMID:\d{4,}|DOI:10\.\d{4,}/\S+)$")

# ⭐ EACH ALTERNATIVE IS SEPARATELY COUNTABLE, and `kind_evidence` returns WHICH one fired.
# A disjunction is green as soon as one branch matches; a caller that cannot see which
# branch fired cannot tell a live rule from a dead one.
PROTOCOL_MARKS = (
    ("cochrane_protocol", re.compile(r"(?i)this is (?:a|the) protocol for")),
    ("protocol_for_review", re.compile(r"(?i)protocol for a (?:cochrane )?(?:systematic )?review")),
    ("study_protocol", re.compile(r"(?i)\bstudy protocol\b")),
    ("protocol_pubtype", re.compile(r"(?i)^protocol$")),
)


class OAFrameRefused(Exception):
    pass


def _refuse(oa_id, rule):
    """Offending record FIRST, rule second, gate third. Naming the accuser before the
    accused has cost this project a four-hour standoff."""
    raise OAFrameRefused("%s\n  rule: %s\n  found by: %s" % (oa_id, rule, GATE))


def kind_evidence(row):
    """-> (derived_kind, [marks that fired]). READ from the record, never taken on trust."""
    text = " ".join([str(row.get("title") or ""), str(row.get("objectives_verbatim") or "")])
    fired = [name for name, rx in PROTOCOL_MARKS if rx.search(text)]
    for pt in (row.get("pub_types") or []):
        if PROTOCOL_MARKS[3][1].search(str(pt)):
            fired.append("protocol_pubtype")
    if fired:
        return "protocol", sorted(set(fired))
    if not (row.get("objectives_verbatim") or "").strip():
        # ⚠️ No abstract is not evidence of being a review. `unknown` is a real third kind,
        # not a hole: a record whose kind cannot be read must not be counted as either.
        return "unknown", []
    return "systematic_review", []


def check_row(row):
    """Refuse a single row, or return its derived kind."""
    oid = row.get("oa_id")
    for k in REQUIRED:
        if k not in row:
            _refuse(oid, "row is missing contract field %r; a frame missing %r is not this "
                         "frame" % (k, k))
    if not (isinstance(oid, str) and OA_ID.match(oid)):
        _refuse(oid, "oa_id %r is not a stable external identifier (PMC…, PMID:…, DOI:10.…). "
                     "A frame keyed by title cannot be deduplicated across versions and "
                     "cannot be joined to an enumerable source" % (oid,))
    o = row["objectives_verbatim"]
    if o is not None and not (isinstance(o, str) and o.strip()):
        _refuse(oid, "objectives_verbatim is %r -- null means UNOBTAINABLE from the source; "
                     "the empty string means the parser saw nothing and said so quietly. "
                     "They are different facts and only null is permitted" % (o,))
    if row["verification_field_kind"] not in VERIFICATION_FIELD_KINDS:
        _refuse(oid, "verification_field_kind %r is not one of %s. A frame that does not say "
                     "WHAT its verification reads cannot be compared to one that does"
                     % (row["verification_field_kind"], VERIFICATION_FIELD_KINDS))
    if row["record_kind"] not in RECORD_KINDS:
        _refuse(oid, "record_kind %r is not one of %s" % (row["record_kind"], RECORD_KINDS))

    # ⛔ THE KIND IS DERIVED AND THE CLAIM IS CHECKED AGAINST IT.
    derived, marks = kind_evidence(row)
    if row["record_kind"] != derived:
        _refuse(oid, "record_kind is stated as %r and the record's own text says %r%s. The "
                     "kind was ASSERTED rather than READ -- the defect that let four "
                     "protocols into a verified set labelled systematic_review"
                     % (row["record_kind"], derived,
                        " (marks: %s)" % ", ".join(marks) if marks else ""))
    return derived


def load_frame(rows):
    """Refuse the frame, or return (rows, kind counts). One row per oa_id."""
    from collections import Counter
    if not rows:
        _refuse("(frame)", "frame holds no rows")
    seen, kinds = {}, Counter()
    for i, r in enumerate(rows, 1):
        kinds[check_row(r)] += 1
        oid = r["oa_id"]
        if oid in seen:
            _refuse(oid, "duplicate oa_id, first seen at row %d -- one row per identifier "
                         "is the frame contract" % seen[oid])
        seen[oid] = i
    if sum(kinds.values()) != len(rows):
        _refuse("(frame)", "the kind partition loses rows: %d kinds over %d rows"
                % (sum(kinds.values()), len(rows)))
    return rows, kinds


def comparators(rows):
    """The rows eligible to BE a comparator, with the excluded kinds NAMED.

    ⭐ A protocol is not a defect and not data -- it is a third kind of item, and a count
    that never enumerated the kinds has assumed its denominator.
    """
    rows, kinds = load_frame(rows)
    keep = [r for r in rows if r["record_kind"] == "systematic_review"]
    excluded = {k: v for k, v in kinds.items() if k != "systematic_review"}
    return keep, {"n_rows": len(rows), "n_comparators": len(keep), "excluded_by_kind": excluded}


def refuse_cross_kind(a_kind, b_kind, what):
    """Comparing a cochrane_objectives number with an abstract number is an ERROR here.

    Not a footnote. `MATCHED` went 6/20 -> 16/20 across exactly this substitution while the
    rule did not change, so a reader handed both numbers under one heading is being misled
    by the frame rather than informed by the result.
    """
    if a_kind != b_kind:
        raise OAFrameRefused(
            "%s\n  rule: refusing to compare a %r-verified number with a %r-verified one. "
            "The verification material differs, so the two numbers do not measure the same "
            "thing under the same rule\n  found by: %s" % (what, a_kind, b_kind, GATE))
    return a_kind
