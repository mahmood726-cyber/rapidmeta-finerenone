"""Regression: the validator's REML+HKSJ pooler must stay concordant with R
metafor. Gold values from rma(yi, vi, method="REML", test="knha") on a fixed
4-study example (metafor 4.x): tau^2=0.018872, pooled exp(b)=0.771883.

The validator was upgraded from DerSimonian-Laird to REML+HKSJ on 2026-06-01
(DL is biased at the small k typical here); this locks the implementation to
metafor so it cannot silently drift back or regress.
"""
import math
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "vv", Path(__file__).resolve().parent.parent / "validate_living_ma_portfolio.py")
vv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vv)

YI = [-0.5, -0.2, 0.1, -0.35]
VI = [0.04, 0.06, 0.05, 0.03]


def test_reml_tau2_matches_metafor():
    tau2 = vv._reml_tau2(YI, VI)
    assert abs(tau2 - 0.018872) < 1e-4, tau2


def test_reml_pooled_estimate_matches_metafor():
    tau2 = vv._reml_tau2(YI, VI)
    w = [1.0 / (v + tau2) for v in VI]
    mu = sum(x * y for x, y in zip(w, YI)) / sum(w)
    assert abs(math.exp(mu) - 0.771883) < 1e-3, math.exp(mu)


def test_pool_dl_endtoend_reml():
    # build trials whose publishedHR + CI reproduce (yi, vi), then pool
    trials = {}
    for i, (y, v) in enumerate(zip(YI, VI)):
        se = math.sqrt(v)
        trials[f"NCT{i:08d}"] = {
            "publishedHR": math.exp(y),
            "hrLCI": math.exp(y - 1.96 * se),
            "hrUCI": math.exp(y + 1.96 * se),
            "name": f"T{i}",
        }
    res = vv.pool_dl(trials)
    assert res["k"] == 4
    assert abs(res["est"] - 0.77) < 0.02, res["est"]


def test_homogeneous_data_gives_zero_tau2():
    # identical effects -> tau^2 = 0, pool = that value
    assert vv._reml_tau2([0.3, 0.3, 0.3], [0.04, 0.05, 0.06]) == 0.0
