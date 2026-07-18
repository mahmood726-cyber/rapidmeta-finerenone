#!/usr/bin/env python
"""Regression gate for the HARMONY Outcomes (NCT02465515) count fix.

WHY THIS FILE EXISTS
--------------------
Commit 8b2eaeac0 corrected HARMONY's secondary CV counts in
`GLP1_CVOT_REVIEW.html`. The correction was validated once, by hand, and then
left ungated: no committed test asserted it. Meanwhile branch
`fix/count-provenance-2026-07-12` still carried the PRE-fix values
(CV death 113/130, all-cause 196/218, nonfatal MI 158/210, nonfatal stroke
81/98). Merging that branch would have silently reverted the fix and nothing
in the repo would have caught it.

Worse, that branch was ALSO an instance of the card<->object defect class: its
evidence card already read the correct Lancet values (102/109, 196/205,
160/228, 76/91) while the plotted object carried the wrong ones. A reader
comparing the two panels would have seen them disagree.

This test closes both holes and is designed to FAIL on the pre-fix values.

WHAT IS ASSERTED
----------------
1. COMPOSITE CHECKSUM (internal). The three MACE components must sum to the
   trial's own 3-point composite, per arm:
       albiglutide  102 + 160 +  76 = 338
       placebo      109 + 228 +  91 = 428
   The pre-fix values fail this: 113+158+81 = 352 != 338.

   NOTE ON WHAT THIS DOES *NOT* PROVE (do not overstate it): this identity is
   three unknowns in one equation per arm, so it has 2 degrees of freedom and
   is invariant to any uniform shift among the components. It catches the
   specific known regression; it is NOT a proof that the components are right.

2. EXTERNAL ANCHOR. The composite 338/428 is independently confirmed from the
   Hernandez 2018 abstract (Lancet 2018;392:1519-1529, PMID 29693361) via
   Europe PMC: "The primary composite outcome occurred in 338 (7%) of 4731
   patients ... and in 428 (9%) of 4732 patients (hazard ratio 0.78, 95% CI
   0.68-0.90)". The four COMPONENT counts are NOT externally verified -- the
   paper is not open access and Table 2 has not been read. They are asserted
   here as the values the fix established, not as externally confirmed values.

3. CARD<->OBJECT AGREEMENT. Every count in the plotted object must also appear
   in the evidence card prose, so the two panels cannot drift apart again.

4. NO TOTAL-ESTIMATE ON A NONFATAL COUNT. The published HR 0.75 (MI) and
   HR 0.86 (stroke) are TOTAL (fatal+nonfatal) estimates; the counts beside
   them are NONFATAL. Attaching them would be the right-number-wrong-endpoint
   defect, so the fix withholds them (effect:0 + an effectNote). This asserts
   they stay withheld.
"""
import io
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "GLP1_CVOT_REVIEW.html"
NCT = "NCT02465515"

# The values established by 8b2eaeac0. (tE, cE) per shortLabel.
EXPECTED = {
    "MACE":   (338, 428),
    "CVD":    (102, 109),
    "ACM":    (196, 205),
    "MI":     (160, 228),
    "Stroke": (76, 91),
}
COMPONENTS = ("CVD", "MI", "Stroke")
COMPOSITE = "MACE"


def _source():
    if not APP.exists():
        pytest.skip(f"{APP.name} not present")
    # CRLF-preserving byte read; this file must never be rewritten by this test.
    return io.open(APP, "r", encoding="latin-1", newline="").read()


def _harmony_outcomes(src):
    """Parse the allOutcomes array of the HARMONY trial object."""
    h = src.find(f'{NCT}:{{name:"HARMONY Outcomes"')
    assert h >= 0, f"{NCT} HARMONY trial object not found in {APP.name}"
    i = src.find("allOutcomes:[", h)
    j = src.find("}],safetyData", h)
    assert 0 <= i < j, "allOutcomes array not found or malformed"
    block = src[i:j]

    out = {}
    for m in re.finditer(
        r'\{shortLabel:"(?P<label>[^"]+)".*?tE:(?P<tE>\d+),cE:(?P<cE>\d+)'
        r'.*?effect:(?P<effect>[\d.]+)',
        block,
    ):
        out[m.group("label")] = {
            "tE": int(m.group("tE")),
            "cE": int(m.group("cE")),
            "effect": float(m.group("effect")),
        }
    assert out, "parsed zero outcomes -- parser drift, failing closed"
    return block, out


def test_all_expected_outcomes_present():
    _, got = _harmony_outcomes(_source())
    missing = set(EXPECTED) - set(got)
    assert not missing, f"outcomes missing from HARMONY object: {sorted(missing)}"


@pytest.mark.parametrize("label", sorted(EXPECTED))
def test_outcome_counts_match_the_fix(label):
    """Fails on the pre-fix values 113/130, 196/218, 158/210, 81/98."""
    _, got = _harmony_outcomes(_source())
    assert (got[label]["tE"], got[label]["cE"]) == EXPECTED[label], (
        f"{label}: object has {got[label]['tE']}/{got[label]['cE']}, "
        f"expected {EXPECTED[label][0]}/{EXPECTED[label][1]} (commit 8b2eaeac0). "
        f"If this is a deliberate re-extraction, update EXPECTED and cite the source."
    )


@pytest.mark.parametrize("arm", ["tE", "cE"])
def test_composite_checksum(arm):
    """CV death + nonfatal MI + nonfatal stroke == 3-point MACE, per arm."""
    _, got = _harmony_outcomes(_source())
    total = sum(got[c][arm] for c in COMPONENTS)
    composite = got[COMPOSITE][arm]
    assert total == composite, (
        f"{arm}: components sum to {total} but the 3-point MACE row is "
        f"{composite} ({' + '.join(f'{c}={got[c][arm]}' for c in COMPONENTS)}). "
        f"The card and the plotted object are inconsistent."
    )


def test_composite_matches_external_anchor():
    """338/428 is confirmed from the Hernandez 2018 abstract via Europe PMC."""
    _, got = _harmony_outcomes(_source())
    assert (got["MACE"]["tE"], got["MACE"]["cE"]) == (338, 428), (
        "the 3-point MACE composite no longer matches the published abstract "
        "(Hernandez 2018, Lancet 392:1519-1529, PMID 29693361)"
    )


@pytest.mark.parametrize("label", ["MI", "Stroke"])
def test_total_estimate_not_attached_to_nonfatal_count(label):
    """HR 0.75 (MI) / 0.86 (stroke) are TOTAL estimates; counts are NONFATAL."""
    block, got = _harmony_outcomes(_source())
    assert got[label]["effect"] == 0, (
        f"{label}: effect={got[label]['effect']} is displayed beside a NONFATAL "
        f"count, but the published HR is the TOTAL (fatal+nonfatal) estimate. "
        f"This is the right-number-wrong-endpoint defect; it must stay withheld."
    )
    assert "effectNote" in block, (
        "the effectNote explaining why the HR is withheld has been removed"
    )


def test_card_and_object_agree():
    """Every count in the object must also appear in the evidence card prose."""
    src = _source()
    _, got = _harmony_outcomes(src)

    # Scope to HARMONY's OWN card. A bare find() for the label returns the
    # FIRST such card in the file, which belongs to ELIXA -- this test was
    # briefly written that way and compared HARMONY's object against ELIXA's
    # card. Anchor on the Hernandez citation instead.
    m = re.search(
        r'\{label:"Secondary CV Outcomes",source:"Hernandez AF[^"]*".*?\]\}', src
    )
    assert m, "HARMONY's own Secondary CV Outcomes evidence card not found"
    card = m.group(0)

    for label in ("CVD", "ACM", "MI", "Stroke"):
        for arm in ("tE", "cE"):
            n = got[label][arm]
            assert re.search(rf"\b{n}\b", card), (
                f"object has {label}.{arm}={n} but that number does not appear "
                f"in the evidence card -- card and object have drifted apart. "
                f"This is exactly the defect branch fix/count-provenance-2026-07-12 "
                f"shipped."
            )
