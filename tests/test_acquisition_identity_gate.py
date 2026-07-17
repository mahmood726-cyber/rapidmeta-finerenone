"""Regression + mutation tests for the acquisition-lane identity gate.

Run: pytest tests/test_acquisition_identity_gate.py -v

The load-bearing test here is test_mutation_*: we take a CLEAN app, seed a cardio
artefact into one lane, and assert the gate BLOCKS. A gate that cannot fail is
verification theatre, so we prove it fails on a known-bad input before trusting
that it passes on a good one.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from acquisition_identity_gate import check_app, drug_tokens, owns_seed  # noqa: E402

CARDIO_CT = 'empagliflozin+OR+dapagliflozin+OR+sacubitril+AND+heart+failure+reduced'


def app_html(ctgov, openalex, epmc='trastuzumab deruxtecan'):
    """Minimal app shaped like the real 3-lane acquisition block."""
    return (
        'const ctgovUrl="https://clinicaltrials.gov/api/v2/studies?query.intr=%s&pageSize=100",'
        'epmcUrl="https://www.ebi.ac.uk/europepmc/webservices/rest/search?query="+'
        "encodeURIComponent('%s AND (TITLE:randomized OR PUB_TYPE:\"Randomized Controlled Trial\")'),"
        'oaUrl="https://api.openalex.org/works?search=%s&per_page=50";'
        % (ctgov, epmc, openalex)
    )


# ── the mutation test: the gate must be able to fail ───────────────────────

def test_mutation_cardio_seeded_into_clean_oncology_app_is_blocked():
    """Seed a cardio CT.gov query into an otherwise-clean HER2 app -> BLOCK.

    This is the exact defect found in ADC_HER2_LOW_REVIEW.html on 2026-07-17:
    EPMC and OpenAlex correctly named trastuzumab deruxtecan while CT.gov still
    queried heart-failure drugs.
    """
    clean = app_html('trastuzumab deruxtecan', 'trastuzumab deruxtecan')
    assert check_app('ADC_HER2_LOW_REVIEW.html', clean) == [], 'clean app must pass'

    mutated = app_html(CARDIO_CT, 'trastuzumab deruxtecan')
    viol = check_app('ADC_HER2_LOW_REVIEW.html', mutated)
    assert viol, 'MUTATION SURVIVED: cardio query in an oncology app was not caught'
    assert {v['rule'] for v in viol} >= {'R1-cross-lane', 'R2-seed-value'}


def test_mutation_every_lane_contaminated_is_still_blocked():
    """R1 alone cannot see this: all lanes agree, and all are wrong.

    Two contaminated lanes agreeing is not correctness. R2 (seed-value) is what
    catches it. Guards against someone deleting R2 as redundant.
    """
    all_cardio = app_html(CARDIO_CT, 'sglt2 heart failure', epmc='sglt2 heart failure')
    viol = check_app('ALS_NEW_AGENTS_NMA_REVIEW.html', all_cardio)
    assert viol, 'MUTATION SURVIVED: uniformly-cardio lanes in an ALS app'
    assert any(v['rule'] == 'R2-seed-value' for v in viol), 'R2 must catch what R1 cannot'


@pytest.mark.parametrize('seed', [
    'dapagliflozin+OR+empagliflozin',
    'bempedoic acid',
    'sacubitril AND valsartan',
])
def test_mutation_each_known_seed_value_is_caught(seed):
    viol = check_app('DENGUE_VACCINE_NEW_NMA_REVIEW.html', app_html(seed, 'dengue vaccine'))
    assert any(v['rule'] == 'R2-seed-value' for v in viol), 'seed %r slipped through' % seed


# ── the gate must not fire on legitimate apps ──────────────────────────────

def test_seed_owner_may_keep_its_own_value():
    """The real bempedoic template legitimately queries bempedoic acid."""
    html = app_html('bempedoic acid', 'bempedoic acid', epmc='bempedoic acid')
    assert check_app('BEMPEDOIC_ACID_REVIEW.html', html) == []


def test_genuine_sglt2_app_is_not_flagged():
    html = app_html('dapagliflozin+OR+empagliflozin', 'dapagliflozin empagliflozin',
                    epmc='dapagliflozin empagliflozin')
    assert check_app('DAPAGLIFLOZIN_HFPEF_AUTO_REVIEW.html', html) == []


def test_topic_matched_app_passes():
    html = app_html('lasmiditan AND MIGRAINE', 'lasmiditan', epmc='lasmiditan')
    assert check_app('LASMIDITAN_MIGRAINE_AUTO_REVIEW.html', html) == []


def test_app_with_no_acquisition_lanes_is_not_flagged():
    """~491 apps have no CT.gov lane; absence is not a defect."""
    assert check_app('SOME_STATIC_REVIEW.html', '<html>no lanes here</html>') == []


# ── unit behaviour ─────────────────────────────────────────────────────────

def test_drug_tokens_drops_scaffolding_but_keeps_identity():
    t = drug_tokens('lasmiditan AND MIGRAINE AND randomized AND placebo')
    assert 'lasmiditan' in t and 'migraine' in t
    assert 'randomized' not in t and 'placebo' not in t


def test_drug_tokens_normalises_url_encoding():
    assert drug_tokens('sglt2%20heart%20failure') == drug_tokens('sglt2+heart+failure')


def test_owns_seed_is_scoped_to_the_owner():
    assert owns_seed('BEMPEDOIC_ACID_REVIEW.html', 'bempedoic acid')
    assert not owns_seed('ADC_HER2_LOW_REVIEW.html', 'bempedoic acid')
