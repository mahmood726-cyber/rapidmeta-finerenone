#!/usr/bin/env python3
"""ENUMERATE EVERY CONVERTER-DERIVED EFFECT IN THE CORPUS.

WHY THIS EXISTS, and it is the whole reason the enumeration comes before any writing.

Mahmood's D5 decision is that risk of bias judges what the TRIAL did, not what our
converter did to the trial's result. That is Handbook section 8.7: domain 5 is selective
reporting BY THE TRIAL AUTHORS. It is the right decision and it leaves something
unassessed. When this review selects among several results a trial reported -- one rank,
one timepoint, one analysis population, one of several co-primary endpoints -- or when it
COMPUTES a number the trial never printed, that carries a real risk of bias and RoB 2 has
no domain for it, because the tool assesses trials and not reviews.

So our selection is DECLARED, never RATED. This script finds the population that needs a
declaration. It does not write one.

TWO AXES, ORTHOGONAL, NEVER MERGED INTO ONE NUMBER.

  AXIS 1 -- WHOSE NUMBER IS IT.  Is the stored point the number the trial printed, or a
        number computed here from something the trial printed?
  AXIS 2 -- WHOSE CHOICE WAS IT.  Given several results the trial reported, which one is
        on this row, and did this review choose it?

A row can be clean on one axis and not the other. A printed hazard ratio taken from a
SECONDARY endpoint is the trial's number and our choice. A risk ratio computed from the
trial's own two-by-two on its registered primary is our number and their choice. Adding
the two axes together would produce a single figure that describes neither.

STRUCTURAL BEFORE PROSE. Every classification prefers a field the object holds as data --
`derived_here`, `how`, arm-level counts -- over reading `derivation` prose. Prose is a
declared fallback and the number of rows classified by it is reported separately, because
a prose matcher is exactly the instrument that has been narrower than its own docstring in
this project before. Substring tests only: no regex, so there is no escape to mangle and
no character class to be quietly wrong about.

THREE STATES, NEVER TWO. present / absent / COULD NOT DETERMINE. A row whose provenance
field is missing is NOT an as-printed row. It is a row we cannot classify, it is counted
as such, and it is named. The failure mode this forbids is the one that would make the
declaration population look smaller than it is.

WHAT IS NOT ENUMERATED HERE, named rather than implied:
  - Pooled estimates. All 33 pooled points carry no `derived_from`; every pooled estimate
    is by construction a number no trial printed, and it is already labelled as a pool on
    the page. The declaration this enumeration serves is per-trial.
  - The 480 legacy pages. They are not in `ssot/` and their conversion is a separate item.
"""
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")

# ---------------------------------------------------------------------------
# AXIS 1 markers. Each is a lowercase substring found in a `derivation` string,
# with the class it establishes. First match wins, and the ORDER IS LOAD-BEARING:
# INTERVAL_COMPUTED is tested before POINT_COMPUTED because "with an interval
# computed here from the standard error it prints beside it" CONTAINS the point
# marker "computed here from". Testing the point marker first classified that row
# as though the point were ours when only the interval is.
#
#   That defect was found because INTERVAL_COMPUTED came back as exactly zero on a
#   corpus whose own derivation strings visibly contain the phrase. A zero on a
#   class you wrote a marker for is a claim about the instrument first.
#
# COMPUTED is tested before AS_PRINTED: a string saying both "computed here" and
# "the source prints" is describing a computation over something printed.
# ---------------------------------------------------------------------------
POINT_COMPUTED = (
    "derived by conversion",
    "computed here from",
    "computed from this trial",
    "computed from the two counts",
    "md = ",
    "assembled, and labelled so",
)
INTERVAL_COMPUTED = (
    "with an interval computed here",
    "interval computed here from the standard error",
)
AS_PRINTED = (
    "stored as published",
    "read as printed",
    "as printed in the registry",
    "the source prints",
    "the published effect estimate",
    "the published hazard ratio",
    "the printed hazard ratio",
    "the published rate ratio",
    "read from the trial",
    "the hazard ratio this trial published",
)

# Arm-level count field name fragments. A row carrying a pair of these has the
# ingredients to compute its own point, which is a structural fact, not a reading.
COUNT_FRAGMENTS = ("_events", "_failures", "_cured", "_deaths", "_at_risk", "_analysed",
                   "_evaluable", "events_", "n_")

A1_POINT_OURS = "POINT_COMPUTED_HERE"
A1_INTERVAL_OURS = "POINT_PRINTED_INTERVAL_COMPUTED_HERE"
A1_PRINTED = "AS_PRINTED"
A1_CND_UNMATCHED = "COULD_NOT_DETERMINE__prose_present_unmatched"
A1_CND_ABSENT = "COULD_NOT_DETERMINE__no_provenance_field"

A2_OURS = "SELECTION_BY_THIS_REVIEW"
A2_THEIRS = "TRIALS_OWN_PRIMARY"
A2_CND = "COULD_NOT_DETERMINE__no_rank_field"

# A rank string establishing that the row is the trial's own designated primary.
# Anything else that IS present is a selection this review made among what the trial
# reported -- including every co-primary, because choosing one of three co-primaries
# under a multiplicity procedure is a choice.
#
# THE CORPUS WRITES THIS RANK TWO WAYS and the first version of this list knew one.
# Twenty-three rows carry the bare token `PRIMARY`; ten carry a sentence containing
# "own primary". Matching only the sentence attributed 23 of the trials' OWN primary
# endpoints to this review's selection -- a marker narrower than the corpus's own
# vocabulary, which is the same defect class as a separator class of `[_ ]` against a
# corpus that writes hyphens. Found because 39-of-49 selection looked too high.
#
# The bare token must be matched EXACTLY, not as a substring: `SECONDARY -- this
# trial's only primary outcome is the proportion with adverse events` contains
# "primary" and is not a primary.
PRIMARY_MARKERS = ("own primary", "own registered primary", "registered primary")
PRIMARY_EXACT_TOKENS = ("primary", "primary endpoint", "primary outcome")


def _has_count_pair(row):
    frags = [k for k in row if any(f in k for f in COUNT_FRAGMENTS)]
    return len(frags) >= 2


def classify_axis1(row):
    """Return (class, basis). Structural fields first, prose only as declared fallback."""
    if "derived_here" in row:
        v = row["derived_here"]
        if v is True:
            return A1_POINT_OURS, "structural: derived_here=True"
        if v is False:
            return A1_PRINTED, "structural: derived_here=False"
    if row.get("how"):
        return A1_POINT_OURS, "structural: `how` records the formula for the point"
    d = row.get("derivation")
    if d is None:
        # Counts alone are ingredients, not evidence that the point was computed.
        # Without a provenance field this row cannot be classified, and saying so is
        # the point of the field.
        if _has_count_pair(row):
            return A1_CND_ABSENT, "no provenance field; arm-level counts present"
        return A1_CND_ABSENT, "no provenance field"
    low = d.lower()
    for m in INTERVAL_COMPUTED:          # MORE SPECIFIC FIRST -- see the note above.
        if m in low:
            return A1_INTERVAL_OURS, "prose: %r" % m
    for m in POINT_COMPUTED:
        if m in low:
            return A1_POINT_OURS, "prose: %r" % m
    for m in AS_PRINTED:
        if m in low:
            return A1_PRINTED, "prose: %r" % m
    return A1_CND_UNMATCHED, "prose present, matched no declared marker"


def classify_axis2(row):
    rk = row.get("endpoint_rank_in_its_own_trial")
    if rk is None:
        return A2_CND, "no rank field", None
    low = str(rk).lower().strip()
    if low in PRIMARY_EXACT_TOKENS:
        return A2_THEIRS, "rank is the bare token %r" % low, rk
    for m in PRIMARY_MARKERS:
        if m in low:
            return A2_THEIRS, "rank names the trial's own primary", rk
    return A2_OURS, "rank is something other than the trial's own primary", rk


def rows():
    """Yield (topic, outcome_id, index, row) for every render-facing per_trial row."""
    for t in sorted(os.listdir(SSOT)):
        p = os.path.join(SSOT, t, t + ".json")
        if not os.path.isdir(os.path.join(SSOT, t)) or not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8") as fh:
            obj = json.load(fh)
        for oid, blk in ((obj.get("results") or {}).get("by_outcome") or {}).items():
            for i, r in enumerate((blk or {}).get("per_trial") or []):
                if isinstance(r, dict):
                    yield t, oid, i, r


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    recs = []
    for topic, oid, i, r in rows():
        c1, b1 = classify_axis1(r)
        c2, b2, rank = classify_axis2(r)
        recs.append({
            "topic": topic, "outcome": oid, "row_index": i,
            "trial": r.get("nct") or r.get("trial_id"),
            "measure": r.get("measure"),
            "axis1_whose_number": c1, "axis1_basis": b1,
            "axis2_whose_choice": c2, "axis2_basis": b2, "rank_verbatim": rank,
            "derivation_verbatim": r.get("derivation"),
        })
    n = len(recs)
    if n == 0:
        print("REFUSED: zero per_trial rows found. That is a selector failure, not an "
              "empty corpus -- suspect the selector before the corpus.")
        return 1

    def tally(key):
        out = {}
        for rec in recs:
            out[rec[key]] = out.get(rec[key], 0) + 1
        return out

    a1, a2 = tally("axis1_whose_number"), tally("axis2_whose_choice")
    print("PER-TRIAL RENDER-FACING ROWS: %d   (topics contributing: %d)"
          % (n, len({r["topic"] for r in recs})))
    print()
    print("AXIS 1 -- WHOSE NUMBER IS IT.  denominator %d" % n)
    for k in (A1_POINT_OURS, A1_INTERVAL_OURS, A1_PRINTED, A1_CND_UNMATCHED, A1_CND_ABSENT):
        print("   %-52s %4d" % (k, a1.get(k, 0)))
    print("   %-52s %4d" % ("(classified by prose fallback rather than a field)",
                            sum(1 for r in recs if r["axis1_basis"].startswith("prose"))))
    print()
    print("AXIS 2 -- WHOSE CHOICE WAS IT.  denominator %d" % n)
    for k in (A2_OURS, A2_THEIRS, A2_CND):
        print("   %-52s %4d" % (k, a2.get(k, 0)))
    print()
    needs = [r for r in recs if r["axis1_whose_number"] in (A1_POINT_OURS, A1_INTERVAL_OURS)
             or r["axis2_whose_choice"] == A2_OURS]
    cnd = [r for r in recs if r["axis1_whose_number"].startswith("COULD_NOT_DETERMINE")
           and r["axis2_whose_choice"] != A2_OURS]
    print("DECLARATION POPULATION (either axis attributes something to this review): "
          "%d of %d rows, %d topics"
          % (len(needs), n, len({r["topic"] for r in needs})))
    print("ROWS THAT CANNOT BE CLASSIFIED ON EITHER AXIS: %d of %d -- these are a MISSING "
          "FIELD to name, not a sentence to invent" % (len(cnd), n))
    print()
    print("ROWS ATTRIBUTED TO THIS REVIEW, BY TOPIC")
    per = {}
    for r in needs:
        per.setdefault(r["topic"], []).append(r)
    for t in sorted(per):
        kinds = sorted({r["axis1_whose_number"] for r in per[t]} |
                       {r["axis2_whose_choice"] for r in per[t] if r["axis2_whose_choice"] == A2_OURS})
        print("   %-52s %3d  %s" % (t, len(per[t]), ", ".join(kinds)))
    dest = os.path.join(REPO, "outputs",
                        "converter_derived_effects_2026_08_24.json")
    if not os.path.isdir(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    with io.open(dest, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "rows": n,
            "axis1_whose_number": a1,
            "axis2_whose_choice": a2,
            "declaration_population": len(needs),
            "unclassifiable_on_both_axes": len(cnd),
            "records": recs,
        }, indent=1))
    print()
    print("wrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
