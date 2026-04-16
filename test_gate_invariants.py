"""Contract tests for QUALITY_GATE v1.2 invariants.

Run: pytest test_gate_invariants.py -v
Also standalone: python test_gate_invariants.py

These tests prevent silent drift between the two curated sets
(EXCLUDED_APPS, MIXED_OUTCOME_APPS) and between the validator's
runtime classifier and the generator's scaffold-time classifier.
If any of these fail, the gate has become self-inconsistent and
the failing invariant must be fixed before the next push.
"""
import os
import sys
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import validate_living_ma_portfolio as v
import generate_living_ma_v13 as g


def test_mixed_outcome_apps_are_all_excluded():
    """Every app with documented mixed-outcome rationale must also be
    in EXCLUDED_APPS so it's actually removed from portfolio scans.
    Otherwise the rationale is documented but the app still produces
    a garbage pool."""
    missing = set(v.MIXED_OUTCOME_APPS) - v.EXCLUDED_APPS
    assert not missing, (
        f"{len(missing)} app(s) in MIXED_OUTCOME_APPS but not in "
        f"EXCLUDED_APPS: {sorted(missing)}. Add them to EXCLUDED_APPS "
        f"or remove them from MIXED_OUTCOME_APPS."
    )


def test_every_mixed_outcome_app_has_rationale():
    """Rationale strings must be non-empty and describe the mix."""
    for app, rationale in v.MIXED_OUTCOME_APPS.items():
        assert rationale, f"{app}: empty rationale in MIXED_OUTCOME_APPS"
        assert len(rationale) > 40, (
            f"{app}: rationale too short ({len(rationale)} chars); "
            f"must describe which outcome classes are mixed and the "
            f"remediation path."
        )


def test_scaffold_time_shortlabel_mapping_matches_runtime():
    """Scaffold-time and runtime classifiers must use identical
    shortLabel -> class mappings. Drift between them means a config
    that passes scaffold may fail runtime (or vice versa) for reasons
    unrelated to the pool."""
    runtime = v.SHORTLABEL_TO_CLASS
    scaffold = g._SHORTLABEL_TO_CLASS
    runtime_only = set(runtime) - set(scaffold)
    scaffold_only = set(scaffold) - set(runtime)
    assert not runtime_only, (
        f"{len(runtime_only)} shortLabel(s) in runtime classifier but "
        f"not in scaffold-time: {sorted(runtime_only)}. Copy them into "
        f"generate_living_ma_v13.py::_SHORTLABEL_TO_CLASS."
    )
    assert not scaffold_only, (
        f"{len(scaffold_only)} shortLabel(s) in scaffold-time classifier "
        f"but not in runtime: {sorted(scaffold_only)}. Copy them into "
        f"validate_living_ma_portfolio.py::SHORTLABEL_TO_CLASS."
    )
    # And matching values for shared keys
    for key in runtime:
        assert runtime[key] == scaffold[key], (
            f"{key}: runtime says {runtime[key]!r}, scaffold says "
            f"{scaffold[key]!r}. Align both."
        )


def test_no_in_portfolio_app_has_uncurated_mixed_outcomes():
    """Every in-portfolio app's live HTML must either classify to a
    single outcome class OR already be in MIXED_OUTCOME_APPS. A new
    uncurated WARN means either (a) a new app was added with mixed
    outcomes without being added to the exclusions, or (b) the
    classifier lexicon needs refinement."""
    apps = v.find_all_apps(local_only=False)
    uncurated = []
    for path, name in apps:
        if name in v.EXCLUDED_APPS:
            continue  # already excluded, not in live portfolio
        with open(path, encoding='utf-8') as fh:
            html = fh.read()
        trials = v.extract_real_data(html)
        pooled = v.extract_pooled_outcomes(html)
        class_per_trial = {}
        for tid, (sl, t) in pooled.items():
            trial = trials.get(tid, {})
            contributes = bool(trial.get('publishedHR')) or (
                trial.get('tN') and trial.get('cN') and
                (trial.get('tE', 0) > 0 or trial.get('cE', 0) > 0)
            )
            if not contributes:
                continue
            if sl or t:
                class_per_trial[tid] = v.classify_pooled_outcome(sl, t)
        classes = set(class_per_trial.values()) - {'unclassified'}
        if len(classes) > 1:
            uncurated.append((name, sorted(classes)))
    assert not uncurated, (
        f"{len(uncurated)} in-portfolio app(s) auto-detected as mixed: "
        f"{uncurated}. Add to MIXED_OUTCOME_APPS + EXCLUDED_APPS with "
        f"remediation note, or refine classifier lexicon."
    )


def test_excluded_apps_not_in_benchmarks():
    """Excluded apps should not have benchmark entries (benchmarks
    describe in-portfolio apps). Stray benchmark entries for excluded
    apps are dead config that will drift."""
    stray = v.EXCLUDED_APPS & set(v.BENCHMARKS)
    assert not stray, (
        f"{len(stray)} excluded app(s) have stale BENCHMARKS entries: "
        f"{sorted(stray)}. Remove them from BENCHMARKS."
    )


if __name__ == '__main__':
    sys.exit(pytest.main([__file__, '-v']))
