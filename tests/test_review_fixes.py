"""Regression guards for the 2026-06-02 code-review fixes.

Locks in the defects fixed in fix/review-defects-25 so they cannot silently
regress, and adds the identifier/encoding integrity coverage the suite was
missing (review finding VAL-8). Pure-Python + a node shell-out for the JS
engine guard; no R, no browser.
"""
import importlib.util
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(modname, filename):
    spec = importlib.util.spec_from_file_location(modname, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


iou = _load("iou_test", "_io_utils.py")
gen = _load("gen_test", "generate_living_ma_v13.py")
atlas = _load("atlas_test", "cardiology_mortality_atlas.py")


# ── P0: the normal/t inverse-CDF that was wrong by ~150x (STATS-1/STATS-2) ──

@pytest.mark.parametrize("p,expected", [
    (0.975, 1.959964), (0.025, -1.959964), (0.995, 2.575829), (0.5, 0.0),
])
def test_norm_ppf_matches_R_qnorm(p, expected):
    assert abs(iou.norm_ppf(p) - expected) < 1e-3, iou.norm_ppf(p)


@pytest.mark.parametrize("p,df,expected", [
    (0.975, 1, 12.70620),   # the value Cornish-Fisher got wrong (~7.2)
    (0.975, 2, 4.302653),
    (0.975, 5, 2.570582),
    (0.975, 30, 2.042272),
    (0.025, 4, -2.776445),
])
def test_t_quantile_matches_R_qt(p, df, expected):
    assert abs(iou.t_quantile(p, df) - expected) < 1e-3, iou.t_quantile(p, df)


def test_atlas_uses_shared_correct_t_quantile():
    # The atlas previously had its own broken t_quantile; it must now resolve to
    # the corrected shared one.
    assert abs(atlas.t_quantile(0.975, 1) - 12.70620) < 1e-3


# ── DATA-1: missing 2x2 cells must become JS null, not a fabricated 0 ──

def test_build_trial_js_missing_cells_are_null():
    js = gen.build_trial_js("NCT00000001", {"name": "T", "publishedHR": 0.8,
                                            "hrLCI": 0.7, "hrUCI": 0.9})
    for field in ("tE", "tN", "cE", "cN"):
        assert f"{field}: null" in js, f"{field} should be null when absent\n{js}"
    assert "tE: 0" not in js


def test_build_trial_js_present_cells_preserved():
    js = gen.build_trial_js("NCT00000002", {"name": "T2", "tE": 10, "tN": 100,
                                            "cE": 0, "cN": 100})
    assert "tE: 10" in js and "tN: 100" in js
    assert "cE: 0" in js  # a REAL zero count must survive


# ── XSS-1/2/3: build-time escapers ──

def test_escape_js_neutralizes_script_breakout():
    out = gen.escape_js("danger</script><img src=x onerror=alert(1)>")
    assert "</script>" not in out
    assert "<" not in out and ">" not in out


def test_escape_js_preserves_quote_and_backslash_escaping():
    assert gen.escape_js("O'Brien") == "O\\'Brien"
    assert gen.escape_js("a\\b") == "a\\\\b"


def test_escape_html_escapes_all_metachars():
    assert gen.escape_html('a"<b>&\'') == "a&quot;&lt;b&gt;&amp;&#39;"


# ── STATS-7: atlas pool CI must be the (wider) HKSJ t-interval, not naive 1.96 ──

def test_atlas_pool_ci_is_hksj_t_not_naive():
    est = [(math.log(0.8), 0.10), (math.log(0.9), 0.12), (math.log(0.75), 0.15)]
    r = atlas.dl_pool(est)
    naive_lo = math.exp(r["pooled_log"] - 1.96 * r["pooled_se"])
    naive_hi = math.exp(r["pooled_log"] + 1.96 * r["pooled_se"])
    assert r["pooled_lo"] <= naive_lo + 1e-9
    assert r["pooled_hi"] >= naive_hi - 1e-9
    assert "pooled_se_hksj" in r


# ── VAL-8: identifier integrity (NCT validation typed, not approximate text) ──

@pytest.mark.parametrize("nct,ok", [
    ("NCT01234567", True),    # NCT + exactly 8 digits = valid
    ("NCT00000000", True),
    ("NCT0123456", False),    # 7 digits
    ("NCT012345678", False),  # 9 digits
    ("nct01234567", False),   # lowercase prefix
    ("NCT01234567 ", False),  # trailing space
    ("", False),
    (None, False),
    (12345678, False),        # not a string
])
def test_is_valid_nct(nct, ok):
    assert iou.is_valid_nct(nct) is ok


def test_md_cell_formula_injection_guard():
    # CSV/Markdown formula-injection prefix on =,+,@ but NOT on '-' (per lesson).
    assert iou.md_cell("=1+1").startswith("'")
    assert iou.md_cell("@SUM").startswith("'")
    assert iou.md_cell("+5").startswith("'")
    assert not iou.md_cell("-5").startswith("'")
    assert iou.md_cell("Aspirin") == "Aspirin"


# ── NMA-1: the JS NMA engine must reject multi-arm trials (fail closed) ──

@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_nma_engine_rejects_multi_arm():
    script = r"""
      require('./rapidmeta-nma-engine-v2.js');
      const E = globalThis.RapidMetaNMA;
      const multi=[{studlab:'M1',treat1:'A',treat2:'B',TE:-0.2,seTE:0.1},
                   {studlab:'M1',treat1:'A',treat2:'C',TE:-0.3,seTE:0.12},
                   {studlab:'S3',treat1:'B',treat2:'C',TE:-0.1,seTE:0.15}];
      let threw=false;
      try { E.fit({trials:multi,reference:'A'}); } catch(e){ threw=true; }
      const ok=E.fit({trials:multi,reference:'A',allowMultiArm:true});
      console.log(JSON.stringify({threw, studies:ok.multi_arm_studies}));
    """
    res = subprocess.run([shutil.which("node"), "-e", script],
                         cwd=str(ROOT), capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    import json
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert out["threw"] is True, "multi-arm input must throw by default"
    assert out["studies"] == ["M1"]
