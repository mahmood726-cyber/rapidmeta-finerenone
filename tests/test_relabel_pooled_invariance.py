"""A RELABELLING THAT CHANGES A NUMBER IS NOT A RELABELLING.

WHAT THIS GUARDS. `ssot/relabel_outcome_verdict_2026_09_04.py` moves screening
rows from EXCLUDED to ELIGIBLE_OUTCOME_UNAVAILABLE. That verdict says a trial
QUALIFIED and contributes nothing extractable to an outcome. The next obvious
step -- actually pooling one of those trials -- changes results, and it needs
extraction, recomputation, review and a rebuild. The two must not be able to
travel together by accident, because a relabelling reads as safe and a
re-inclusion does not, and the diff of the first looks exactly like the diff of
the second in every field except the one that matters.

FOUR CHECKS, AND THE FOURTH IS THE ONE THAT MATTERS

  1. --check writes nothing. Every canonical object is byte-identical after it.
  2. The migration is a fixed point. Applying it twice reports zero changes.
  3. Applying it moves no pooled point and no interval bound, on any object.
  4. NEGATIVE CONTROL. A pooled value is deliberately perturbed and the guard is
     required to REFUSE the write. A test that cannot fail is not a test, and
     invariance suites are the easiest place in a repository to accumulate checks
     that pass because they inspect nothing.

Scope note: the migration touches 4 objects. Checks 1 and 3 run over all 155
canonical objects anyway, because the cost is a few seconds and the failure this
is guarding against is precisely a write somewhere nobody was looking.
"""
import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MIGRATION = ROOT / "ssot" / "relabel_outcome_verdict_2026_09_04.py"


def _load_migration(ssot_dir=None):
    spec = importlib.util.spec_from_file_location("relabel_mig", MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if ssot_dir is not None:
        mod.SSOT = str(ssot_dir)
    return mod


def _canonical_objects(ssot_dir):
    """A canonical object is <id>/<id>.json. Sidecars are not objects."""
    return sorted(p for p in ssot_dir.glob("*/*.json") if p.parent.name == p.stem)


def _pooled(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    by = ((d.get("results") or {}).get("by_outcome") or {})
    items = by.items() if isinstance(by, dict) else enumerate(by)
    return {str(k): v["pooled"] for k, v in items
            if isinstance(v, dict) and "pooled" in v}


def _pooled_corpus(ssot_dir):
    return {p.stem: _pooled(p) for p in _canonical_objects(ssot_dir)}


def _sha_corpus(ssot_dir):
    import hashlib
    return {p.stem: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in _canonical_objects(ssot_dir)}


# --------------------------------------------------------------------------- 1
def test_check_mode_writes_nothing():
    before = _sha_corpus(ROOT / "ssot")
    r = subprocess.run([sys.executable, str(MIGRATION), "--check"],
                       cwd=str(ROOT), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    after = _sha_corpus(ROOT / "ssot")
    moved = sorted(k for k in before if before[k] != after.get(k))
    assert not moved, "--check wrote to: %s" % moved


def _unmigrate_iv_iron(ssot):
    """Rebuild the PRE-migration state of iv-iron-hf's screening records.

    The store is already migrated, so a test that copies it and runs the
    migration would inspect a no-op and pass by doing nothing. This reverses the
    row edits FROM THE OBJECT'S OWN DATED SUPERSESSION RECORDS -- which is also a
    check on those records: if they do not hold enough to reconstruct what was
    replaced, they are decoration rather than provenance and this raises.
    """
    p = ssot / "iv-iron-hf" / "iv-iron-hf.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    n = 0
    for row in d["screening"]["records"]:
        sup = row.pop("criteria_failed_superseded_2026_09_04", None)
        if not sup:
            continue
        row["criteria_failed"] = sup["was"]
        for k in ("verdict", "verdict_means", "verdict_changed_2026_09_04",
                  "contribution_axis", "eligibility_axes_met", "eligibility_basis",
                  "eligibility_basis_evidence", "what_it_does_report",
                  "contributes_to_outcomes"):
            row.pop(k, None)
        n += 1
    assert n, "no dated supersession records found; cannot build a pre-state"
    p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    return n


# --------------------------------------------------------------------------- 2
def test_migration_is_idempotent(tmp_path):
    ssot = tmp_path / "ssot"
    shutil.copytree(ROOT / "ssot", ssot,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    reverted = _unmigrate_iv_iron(ssot)
    mod = _load_migration(ssot)
    first = sum(len(fn(False)) for _, fn in mod.MIGRATIONS)
    second = sum(len(fn(False)) for _, fn in mod.MIGRATIONS)
    assert first >= reverted, (
        "reverted %d row(s) but the migration reported only %d change(s); it does "
        "not re-apply to a pre-state" % (reverted, first))
    assert second == 0, "second run reported %d change(s); not a fixed point" % second


# --------------------------------------------------------------------------- 3
def test_apply_moves_no_pooled_estimate(tmp_path):
    ssot = tmp_path / "ssot"
    shutil.copytree(ROOT / "ssot", ssot,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    _unmigrate_iv_iron(ssot)
    before = _pooled_corpus(ssot)
    mod = _load_migration(ssot)
    for _, fn in mod.MIGRATIONS:
        fn(False)
    after = _pooled_corpus(ssot)

    assert set(before) == set(after), "an object appeared or vanished"
    drift = []
    for obj in sorted(before):
        b, a = before[obj], after[obj]
        if set(b) != set(a):
            drift.append("%s: outcome set changed %s -> %s"
                         % (obj, sorted(b), sorted(a)))
            continue
        for oid in sorted(b):
            if b[oid] != a[oid]:
                drift.append("%s/%s: %r -> %r" % (obj, oid, b[oid], a[oid]))
    assert not drift, "pooled estimate(s) moved under a RELABELLING:\n  " + \
                      "\n  ".join(drift)

    # And the relabelling actually happened -- otherwise this test passes by
    # inspecting a migration that did nothing.
    ivi = json.loads((ssot / "iv-iron-hf" / "iv-iron-hf.json").read_text(encoding="utf-8"))
    verdicts = [r.get("verdict") for r in ivi["screening"]["records"]]
    assert verdicts.count(mod.VERDICT) == 4, verdicts


# --------------------------------------------------------------------------- 4
def test_guard_refuses_when_a_pooled_value_moves(tmp_path):
    """NEGATIVE CONTROL. Perturb one pooled point; require a refusal."""
    ssot = tmp_path / "ssot"
    shutil.copytree(ROOT / "ssot", ssot,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    mod = _load_migration(ssot)

    obj = mod.load("iv-iron-hf")[2]
    before = mod.pooled_snapshot(obj)
    assert before, "fixture holds no pooled block; the control would be vacuous"
    oid = sorted(before)[0]
    after = copy.deepcopy(before)
    after[oid]["point"] = float(after[oid]["point"]) + 0.01

    with pytest.raises(SystemExit) as ex:
        mod.assert_pooled_frozen("iv-iron-hf", before, after)
    assert "REFUSING TO WRITE" in str(ex.value)
    assert oid in str(ex.value)


def test_guard_also_catches_an_interval_bound(tmp_path):
    """A point can hold while an interval moves. Both are served numbers."""
    ssot = tmp_path / "ssot"
    shutil.copytree(ROOT / "ssot", ssot,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    mod = _load_migration(ssot)
    obj = mod.load("iv-iron-hf")[2]
    before = mod.pooled_snapshot(obj)
    oid = next((k for k in sorted(before) if "ci_high" in before[k]), None)
    assert oid, "no pooled block carries an interval; the control would be vacuous"
    after = copy.deepcopy(before)
    after[oid]["ci_high"] = float(after[oid]["ci_high"]) + 0.01
    with pytest.raises(SystemExit):
        mod.assert_pooled_frozen("iv-iron-hf", before, after)
