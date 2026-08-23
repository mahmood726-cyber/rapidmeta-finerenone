"""Estimates whose inputs are placeholders, and the reason each is withdrawn.

WHAT HAPPENED. `scripts/regenerate_catastrophic_sidecars.R` writes, at line 111:

    # Substitute placeholder HRs that reflect single-arm response benchmarks
    # against historical control; these will be flagged for human verification
    # via 'regenerated_from' field.
    hr = c(0.50, 0.45, 0.55)

They were never flagged. They were pooled, written to `outputs/r_validation/<topic>.json`,
copied into `outputs/portfolio_index.json` by `build_portfolio_index.py`, and rendered by
`dashboard.html` under the heading "Pooled OR (95% CI)". A reader meets an invented number as a
finding.

EVERYTHING ELSE FOUND THIS WEEK HAS BEEN A TRUE FACT RENDERED WRONGLY -- a real reason under
the wrong key, a real rating in a location no surface reads, a real result hidden by a
truthiness test. THIS IS A FABRICATED ONE REACHING A READER.

THE FLAG THE COMMENT PROMISED EXISTS AND LIES. `regenerated_from` reads
"curated_publishedHR_via_metafor_5.0.1" on all four sidecars this script emits, asserting the
numbers came from publications. A WRONG ESTIMATE CAN BE CAUGHT BY SOMEONE WHO LOOKS; A
PROVENANCE STRING THAT LIES REMOVES THE REASON TO LOOK. That is the worse defect of the two.

TWO REASONS, NOT ONE, AND THE DISTINCTION IS THE POINT. Three sidecars carry tau2 = 0.0 AND
I2 = 0.0 exactly -- hand-chosen numbers agree perfectly because nothing generated them.
COPD_TRIPLE does not: tau2 0.0244, I2 88.5, which is what real heterogeneity looks like. Its
inputs may be genuine. It carries the same false provenance label, so it CANNOT BE DETERMINED
FROM THE ARTEFACT, and that is the honest verdict rather than an accusation. Four withdrawals
with two reasons are more useful than four with one.

NOTHING HERE IS REPAIRED INTO A REAL NUMBER. Establishing what is real means reading the
pivotal publications, which is not a projection and is not this file's to invent.
"""

# topic -> (reason_code, the sentence a reader is shown)
WITHDRAWN = {
    "FGFR_INHIBITORS_SOLID": (
        "inputs_are_placeholders",
        "The estimate is withdrawn. Its inputs were placeholder hazard ratios written by "
        "hand in the script that produced them -- 0.50, 0.45 and 0.55 -- and the pooled "
        "result carries tau-squared 0.0 and I-squared 0.0, which is what three chosen "
        "numbers look like rather than three trials. No estimate is published here until "
        "the underlying effects are read from their sources."),
    "HEPATITIS_HCV_DAA": (
        "inputs_are_placeholders",
        "The estimate is withdrawn. Its inputs were placeholder effects written by hand in "
        "the script that produced them, and the pooled result carries tau-squared 0.0 and "
        "I-squared 0.0 -- perfect agreement between numbers nothing generated. No estimate "
        "is published here until the underlying effects are read from their sources."),
    "HPV_DOSE_REDUCTION": (
        "inputs_are_placeholders",
        "The estimate is withdrawn. Its inputs were placeholder effects written by hand in "
        "the script that produced them, and the pooled result carries tau-squared 0.0 and "
        "I-squared 0.0 -- perfect agreement between numbers nothing generated. No estimate "
        "is published here until the underlying effects are read from their sources."),
    "COPD_TRIPLE": (
        "provenance_unverifiable",
        "The estimate is withdrawn because its provenance cannot be established, NOT because "
        "its inputs are known to be invented. It was produced by the same script that wrote "
        "placeholder effects for three other topics, and it carries the same "
        "'curated_publishedHR' label as those -- a label now known to be false where it was "
        "checked. Unlike them its heterogeneity is real-looking (tau-squared 0.0244, "
        "I-squared 88.5), so its inputs may well be genuine. WHICH IS TRUE CANNOT BE "
        "DETERMINED FROM THE ARTEFACT, and an estimate whose source cannot be named is not "
        "published here."),
}

# The provenance string the script emits on all four. It asserts curation that did not happen.
FALSE_PROVENANCE = "curated_publishedHR_via_metafor_5.0.1"

# Fields cleared from a withdrawn row. The ROW SURVIVES: the record that the topic exists and
# its estimate was withdrawn is itself the finding, which is the form the not-poolable pages
# already use and the reason this is not a deletion.
CLEARED = ("pooled_OR", "ci_low", "ci_high", "I2", "tau2", "PI_low", "PI_high")


def withdrawal_for(topic, regenerated_from=None):
    """-> (reason_code, sentence) or None. Matches by topic, or by the false label alone."""
    hit = WITHDRAWN.get(topic)
    if hit:
        return hit
    if regenerated_from == FALSE_PROVENANCE:
        return ("provenance_unverifiable",
                "The estimate is withdrawn: it carries a provenance label known to be false "
                "on every topic where it was checked, so the source of its inputs cannot be "
                "named.")
    return None


def apply_to_row(row):
    """Clear a withdrawn estimate from a portfolio row, in place. Returns the reason or None."""
    got = withdrawal_for(row.get("topic"), row.get("regenerated_from"))
    if not got:
        return None
    code, sentence = got
    for f in CLEARED:
        row[f] = None
    row["estimate_withdrawn"] = True
    row["withdrawn_reason_code"] = code
    row["withdrawn_reason"] = sentence
    return code
