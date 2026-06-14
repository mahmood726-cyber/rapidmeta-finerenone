"""
Tests for the RapidMeta truth_recovery_engine adapter.

Proves: (1) the adapter reaches the packaged engine and reproduces its numbers through
the RapidMeta-side interface, (2) the engine reproduces a validated golden harness cell,
(3) the flag tooling is read-only.

Run:  set TRUTH_RECOVERY_HOME=F:/allmeta/engines
      python -m pytest scripts/test_truth_recovery_engine.py -v
"""

import json
import math
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

tre = pytest.importorskip("truth_recovery_engine",
                          reason="set TRUTH_RECOVERY_HOME to allmeta/engines")
TR = tre.TR

_GOLDEN = os.path.join(os.path.dirname(tre.__file__) if hasattr(tre, "__file__") else HERE,
                       "..", "..", "allmeta", "engines", "truth_recovery", "tests",
                       "golden_unified.json")


def test_adapter_reaches_engine():
    assert TR.info()["label"] == "Unified truth-recovery (honest coverage)"
    assert TR.info()["config"]["coverage_target"] == 0.90


def test_estimate_logscale_matches_engine():
    yi = [0.58, 1.03, 3.82]
    si = [0.30, 0.21, 1.01]
    r = tre.estimate_logscale(yi, si)
    direct = TR.estimate(yi, [s * s for s in si])
    assert r["point"] == direct["point"]
    assert r["ci_lo"] == direct["ci_lo"] and r["ci_hi"] == direct["ci_hi"]
    # ratio views are exp() of the log-scale outputs
    assert abs(r["ratio_point"] - math.exp(direct["point"])) < 1e-12


@pytest.mark.skipif(not os.path.exists(_GOLDEN), reason="golden file not found")
def test_reproduces_validated_golden_through_adapter():
    golden = json.load(open(_GOLDEN, encoding="utf-8"))
    g = golden[0]
    # feed the golden (y, v) as (yi, si) with si=sqrt(v)
    si = [math.sqrt(x) for x in g["v"]]
    r = tre.estimate_logscale(g["y"], si)
    assert abs(r["point"] - g["mu"]) < 1e-9
    assert abs(r["ci_lo"] - g["ci_lo"]) < 1e-9
    assert abs(r["ci_hi"] - g["ci_hi"]) < 1e-9


def test_null_crossing_helper():
    assert tre._crosses_null_log(-0.1, 0.2) is True
    assert tre._crosses_null_log(0.1, 0.5) is False
    assert tre._crosses_null_log(-0.5, -0.1) is False


def test_classical_comparator_runs():
    c = tre._classical_hksj([0.58, 1.03, 3.82], [0.30, 0.21, 1.01])
    assert c["ok"] is True
    assert c["ci_lo"] < c["point"] < c["ci_hi"]


def test_repool_flag_is_read_only(tmp_path, monkeypatch):
    """The flag run must not modify any input/published artifact (only the report)."""
    if not os.path.exists(tre.POOLCHECK):
        pytest.skip("poolcheck_input.json not present")
    before = os.path.getmtime(tre.POOLCHECK)
    findings_before = None
    if os.path.isdir(tre.FINDINGS):
        sample = [f for f in os.listdir(tre.FINDINGS)][:5]
        findings_before = {f: os.path.getmtime(os.path.join(tre.FINDINGS, f)) for f in sample}
    # write the report + audit dump to throwaway paths so the test never clobbers them
    monkeypatch.setattr(tre, "REPORT", str(tmp_path / "flag_test.md"))
    monkeypatch.setattr(tre, "AUDIT_JSON", str(tmp_path / "repool_test.json"))
    res = tre.repool_flag(limit=5)
    assert res["processed"] >= 1
    assert os.path.getmtime(tre.POOLCHECK) == before, "poolcheck input was modified!"
    if findings_before:
        for f, mt in findings_before.items():
            assert os.path.getmtime(os.path.join(tre.FINDINGS, f)) == mt, f"{f} modified!"
