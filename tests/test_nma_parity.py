"""VAL-6: gate the JS NMA engine against stored netmeta references.

Thin pytest wrapper around tests/nma_parity.mjs (node, no browser, no R). The
harness asserts the engine reproduces netmeta's contrasts + tau2 + SUCRA on
every dataset whose committed CSV network corresponds to its stored reference,
and reports (without failing) the datasets whose CSV is a subset of the
reference network. Exit non-zero on a real parity mismatch.
"""
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
    # Guard against the harness silently validating nothing: at least the one
    # corresponding dataset (jaki_ra) must be gated.
    assert "0 dataset(s) gated" not in res.stdout, (
        f"NMA parity asserted nothing — all networks mismatched:\n{res.stdout}"
    )
