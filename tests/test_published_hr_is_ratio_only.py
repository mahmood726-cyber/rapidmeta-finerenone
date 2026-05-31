"""Regression: `publishedHR` in the generated realData block must hold a
ratio-scale effect (HR/OR/RR/...) or null -- never a mean difference, risk
difference, or other non-ratio quantity.

Root cause (fixed 2026-05-31): scripts/generate_topic_html.py wrote
`publishedHR: pub_es` for *every* extracted effect regardless of type, so a
continuous mean difference such as -2.09 (MG-ADL change) became an impossible
negative "hazard ratio". This poisoned both the client-side JS ratio engine
and the external validator's pool_dl (which prefers publishedHR), leaving apps
that DO have usable 2x2 counts mislabelled as non-poolable.

See lessons.md "Negated-counts silent corruption" family: schema-valid but
semantically wrong values that pass downstream validation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from generate_topic_html import realdata_for_engine, _is_ratio_effect  # noqa: E402


def _trial(nct, eff_type, eff_size, lci=None, uci=None):
    return {
        "nct": nct, "acronym": nct, "pmid": "1", "year": 2024,
        "tN": 100, "cN": 100, "tE": 10, "cE": 20,
        "interventions": ["drug"], "primary_outcome": "x",
        "published_effect_type": eff_type, "published_effect_size": eff_size,
        "published_ci_lower": lci, "published_ci_upper": uci,
        "published_source_snippet": "", "pubmed_title": "",
    }


def test_mean_difference_never_in_published_hr():
    rd = realdata_for_engine([_trial("NCT1", "MD", -2.09, -3.24, -0.95)])
    e = rd["NCT1"]
    assert e["publishedHR"] is None, "MD must not land in publishedHR"
    assert e["hrLCI"] is None and e["hrUCI"] is None
    # value preserved for the continuous engine
    assert e["publishedEffect"] == -2.09
    assert e["publishedEffectType"] == "MD"
    # falls back to event counts for ratio pooling
    assert e["tE"] == 10 and e["cE"] == 20


def test_ratio_effect_kept_in_published_hr():
    rd = realdata_for_engine([_trial("NCT2", "HR", 0.86, 0.79, 0.92)])
    e = rd["NCT2"]
    assert e["publishedHR"] == 0.86
    assert e["hrLCI"] == 0.79 and e["hrUCI"] == 0.92


def test_no_negative_or_zero_published_hr():
    for bad in (-2.09, 0, -0.0):
        rd = realdata_for_engine([_trial("NCT3", "HR", bad, -1, 1)])
        assert rd["NCT3"]["publishedHR"] is None, f"{bad} is not a valid ratio"


def test_is_ratio_effect_predicate():
    assert _is_ratio_effect("OR", 1.2)
    assert _is_ratio_effect("RR", 0.5)
    assert not _is_ratio_effect("MD", -2.0)
    assert not _is_ratio_effect("RD", 0.03)
    assert not _is_ratio_effect("HR", -1.0)
    assert not _is_ratio_effect("HR", 0)
    assert not _is_ratio_effect("HR", None)
    assert not _is_ratio_effect("HR", True)  # bool is not a real effect size
