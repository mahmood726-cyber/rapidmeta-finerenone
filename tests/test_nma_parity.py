"""VAL-6: gate the JS NMA engine against stored netmeta references.

Thin pytest wrapper around tests/nma_parity.mjs (node, no browser, no R). The
harness sources the authoritative contrast-basis input from each
nma/validation/*_netmeta.R script (the exact network netmeta was run on), runs
the JS engine, and asserts it reproduces netmeta's contrasts + tau2 + SUCRA.
It fails closed on an UNEXPECTED divergence (a regression, a new dataset, or a
documented-divergence dataset that drifts further); the handful of known
tau2-approximation divergences are recorded in the harness with their reason.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "tests" / "nma_parity.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_nma_engine_matches_netmeta():
    res = subprocess.run(
        [shutil.which("node"), str(HARNESS)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=180,
    )
    # The harness prints its report to stdout and exits 1 only on a real
    # parity mismatch among corresponding datasets.
    assert res.returncode == 0, (
        f"NMA parity harness failed (exit {res.returncode}):\n{res.stdout}\n{res.stderr}"
    )
    # Guard against the harness silently validating nothing or losing coverage:
    # require a healthy number of clean-pass networks (currently 17 of 22 gated).
    m = re.search(r"\((\d+) clean,", res.stdout)
    assert m and int(m.group(1)) >= 15, (
        f"NMA parity clean-pass coverage dropped below 15:\n{res.stdout}"
    )
