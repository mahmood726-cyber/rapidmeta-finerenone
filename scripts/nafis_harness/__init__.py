"""nafis_harness -- verification harness for the Nafis / RapidMeta lanes.

Design constraints, both binding, both from Mahmood:
  1. It must not cause regression. Nothing here writes to a corpus repo, makes a
     network call, or replaces an existing check. It is additive and read-only.
  2. It must not burn tokens. Every detector is deterministic CPU. There are no
     model calls anywhere in this package, and no dependency that would put one
     in the path.

Entry points:

    from nafis_harness import build_registry, Verdict
    reg = build_registry()
    report = reg.self_test()          # fire every detector against its fixtures
    result = reg.run("CHK005_EXTERNAL_REFERENT", payload)

    python -m nafis_harness           # self-test + dataset run + baseline diff
"""

from .verdict import (Verdict, Witness, Result, WitnessError, make_pass,
                      make_fail, make_invalid, tally)
from .check import Check, Fixture, Instrument
from .registry import Registry, InadmissibleDetector
from .baseline import (Case, Dataset, RunRecord, run_dataset, save_baseline,
                       load_baseline, diff_baseline, diff_is_clean)
from .interrupt import Interrupt, Ledger
from .probes import ALL_CHECKS, build_registry

__all__ = [
    "Verdict", "Witness", "Result", "WitnessError", "make_pass", "make_fail",
    "make_invalid", "tally", "Check", "Fixture", "Instrument", "Registry",
    "InadmissibleDetector", "Case", "Dataset", "RunRecord", "run_dataset",
    "save_baseline", "load_baseline", "diff_baseline", "diff_is_clean",
    "Interrupt", "Ledger", "ALL_CHECKS", "build_registry",
]

__version__ = "1.0.0"
