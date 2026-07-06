"""Regression test for pick_primary_publication (wrong-PMID-by-prestige).

Real case: EMPULSE (NCT04157751), verified against PubMed 2026-07-06.
  * primary results : PMID 35228754, Nat Med 2022-02-28 (FLAGSHIP rank 6)
  * secondary (QoL) : PMID 35377706, Circulation 2022-04-04 (FLAGSHIP rank 3)
Prestige ranking picked the Circulation QoL sub-analysis over the Nat Med
primary-results paper. Selection must prefer the EARLIEST is_primary paper.

Run: python -m pytest outcome_switching/test_pick_primary_publication.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_publications_v2 import pick_primary_publication, _pubdate_key  # noqa: E402

# esummary-shaped metadata for the two real EMPULSE papers.
NATMED_PRIMARY = {
    "pmid": "35228754",
    "title": "The SGLT2 inhibitor empagliflozin in patients hospitalized for "
             "acute heart failure: a multinational randomized trial.",
    "journal": "Nat Med",
    "pubdate": "2022 Feb 28",
    "publication_types": ["Journal Article", "Randomized Controlled Trial"],
}
CIRC_QOL = {
    "pmid": "35377706",
    "title": "Effects of Empagliflozin on Symptoms, Physical Limitations, and "
             "Quality of Life in Patients Hospitalized for Acute Heart Failure: "
             "Results From the EMPULSE Trial.",
    "journal": "Circulation",
    "pubdate": "2022 Apr 04",
    "publication_types": ["Journal Article", "Randomized Controlled Trial"],
}


def test_picks_primary_results_not_higher_prestige_secondary():
    # order should not matter — QoL listed first (as PubMed relevance might).
    picked = pick_primary_publication([CIRC_QOL, NATMED_PRIMARY])
    assert picked is not None
    assert picked["pmid"] == "35228754", picked   # Nat Med primary, NOT Circulation QoL


def test_prestige_only_breaks_ties_on_same_date():
    same_date_high = dict(CIRC_QOL, pubdate="2022 Feb 28")   # Circulation rank 3
    same_date_low = dict(NATMED_PRIMARY, journal="BMJ")       # BMJ rank 9, same date
    picked = pick_primary_publication([same_date_low, same_date_high])
    assert picked["journal"] == "Circulation", picked        # tie broken by prestige


def test_pubdate_key_parsing():
    assert _pubdate_key({"pubdate": "2022 Feb 28"}) == (2022, 2, 28)
    assert _pubdate_key({"pubdate": "2022 Apr 04"}) == (2022, 4, 4)
    assert _pubdate_key({"pubdate": "2021"}) == (2021, 13, 32)
    assert _pubdate_key({"pubdate": ""}) == (9999, 13, 32)     # absent sorts last
    # earliest year wins regardless of missing month/day
    assert _pubdate_key({"pubdate": "2021"}) < _pubdate_key({"pubdate": "2022 Feb 28"})
