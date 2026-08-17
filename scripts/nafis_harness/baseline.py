"""The LangSmith pattern, and only the LangSmith pattern: dataset -> reference
outputs -> baseline diff. Implemented locally, deterministically, at zero token cost.

WHAT WAS TAKEN AND WHAT WAS NOT, and why

  TAKEN -- the evaluation pattern. A fixed dataset of cases with reference
  outputs, a stored baseline, and a diff of the current run against it so that a
  regression is a visible event rather than a thing somebody notices later. That
  pattern is sound and is roughly 200 lines of local code.

  NOT TAKEN -- LangChain core. It injects boilerplate into every structured call
  and wraps a retry loop that re-bills whole calls on failure. Against Mahmood's
  two binding constraints -- no regression, no unnecessary tokens -- it fails the
  second outright, and it would put a model in the path of checks that are
  currently deterministic CPU, which fails the first.

  NOT TAKEN -- LangGraph, except `interrupt()`. Its replay re-executes model
  calls. Against a written ledger, replay is a downgrade paid for in tokens: the
  ledger already has the answer, and re-deriving it can differ from it. The
  `interrupt()` idea -- a durable pause for a human adjudication that resumes
  without re-running what came before -- is kept, and is implemented in
  `interrupt.py` over the ledger, with no model calls at all.

WHAT LANGSMITH DOES NOT SOLVE, and the guard added here

  A LangSmith-style evaluator that returns `{"ok": 1}` shows 100% green and
  raises nothing. The dashboard cannot tell a correct evaluator from a constant
  one. That is validator validation, and it is exactly the failure this project
  keeps making: an instrument incapable of the opposite answer.

  So `Dataset.discrimination_problems()` refuses a dataset that cannot
  discriminate:
    * it must contain at least one case expected to FAIL and one expected to PASS
    * a run in which every case returns the same verdict is reported as
      NON-DISCRIMINATING, whatever that verdict is -- all-green included
    * a run whose INVALID share exceeds a threshold is reported as INSTRUMENT
      DEGRADED rather than scored

  A constant evaluator scores 50% at best on a two-sided dataset and is flagged
  as non-discriminating. It cannot show green.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .registry import Registry
from .verdict import Verdict


@dataclass(frozen=True)
class Case:
    case_id: str
    check_id: str
    payload: Mapping[str, Any]
    expect: Verdict
    provenance: str = ""


@dataclass
class Dataset:
    name: str
    cases: Sequence[Case] = field(default_factory=tuple)

    def discrimination_problems(self) -> list[str]:
        problems = []
        expects = {c.expect for c in self.cases}
        if not self.cases:
            problems.append("dataset is empty")
        if Verdict.FAIL not in expects:
            problems.append("no case expects FAIL -- an evaluator that always "
                            "returns PASS would score 100% on this dataset")
        if Verdict.PASS not in expects:
            problems.append("no case expects PASS -- an evaluator that always "
                            "returns FAIL would score 100% on this dataset")
        return problems


@dataclass
class RunRecord:
    dataset: str
    results: dict           # case_id -> {"expect", "got", "reason", "check_id"}
    counts: dict
    discriminating: bool
    notes: list


def run_dataset(registry: Registry, dataset: Dataset,
                *, invalid_ceiling: float = 0.25) -> RunRecord:
    notes = list(dataset.discrimination_problems())
    results: dict[str, dict] = {}
    counts = {"match": 0, "mismatch": 0, "invalid": 0}
    observed: list[Verdict] = []

    for case in dataset.cases:
        r = registry.run(case.check_id, case.payload)
        observed.append(r.verdict)
        entry = {
            "check_id": case.check_id,
            "expect": case.expect.value,
            "got": r.verdict.value,
            "reason": r.reason,
            "provenance": case.provenance,
        }
        if r.verdict is Verdict.INVALID and case.expect is not Verdict.INVALID:
            counts["invalid"] += 1
            entry["status"] = "INVALID"
        elif r.verdict is case.expect:
            counts["match"] += 1
            entry["status"] = "match"
        else:
            counts["mismatch"] += 1
            entry["status"] = "MISMATCH"
        results[case.case_id] = entry

    n = len(dataset.cases) or 1
    distinct = set(observed)
    discriminating = len(distinct) > 1
    if not discriminating and dataset.cases:
        notes.append(
            f"NON-DISCRIMINATING RUN: every case returned "
            f"{next(iter(distinct)).value}. A constant evaluator produces this. "
            "The run is not scoreable.")
    if counts["invalid"] / n > invalid_ceiling:
        notes.append(
            f"INSTRUMENT DEGRADED: {counts['invalid']}/{n} cases returned INVALID, "
            f"above the {invalid_ceiling:.0%} ceiling. Fix the instrument before "
            "reading the score.")

    return RunRecord(dataset=dataset.name, results=results, counts=counts,
                     discriminating=discriminating, notes=notes)


# ---------- baseline storage and diff ----------------------------------------

def save_baseline(record: RunRecord, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"dataset": record.dataset, "results": record.results,
                   "counts": record.counts,
                   "discriminating": record.discriminating,
                   "notes": record.notes},
                  fh, indent=2, sort_keys=True)


def load_baseline(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def diff_baseline(current: RunRecord, baseline: dict | None) -> dict:
    """Regressions, improvements, and -- the one people forget -- new INVALIDs.

    A case moving PASS -> INVALID is not neutral. It means the instrument went
    blind between runs, and the corpus stopped being watched at that point.
    """
    if baseline is None:
        return {"first_run": True, "regressions": [], "improvements": [],
                "went_blind": [], "new_cases": sorted(current.results),
                "dropped_cases": []}

    old = baseline.get("results", {})
    new = current.results
    regressions, improvements, went_blind = [], [], []

    for cid in sorted(set(old) & set(new)):
        o, n = old[cid]["got"], new[cid]["got"]
        if o == n:
            continue
        rec = {"case": cid, "from": o, "to": n, "reason": new[cid]["reason"],
               "provenance": new[cid].get("provenance", "")}
        if n == "INVALID":
            went_blind.append(rec)
        elif o == new[cid]["expect"] and n != new[cid]["expect"]:
            regressions.append(rec)
        elif o != new[cid]["expect"] and n == new[cid]["expect"]:
            improvements.append(rec)
        else:
            regressions.append(rec)

    return {
        "first_run": False,
        "regressions": regressions,
        "improvements": improvements,
        "went_blind": went_blind,
        "new_cases": sorted(set(new) - set(old)),
        "dropped_cases": sorted(set(old) - set(new)),
    }


def diff_is_clean(diff: dict) -> bool:
    return not (diff["regressions"] or diff["went_blind"] or diff["dropped_cases"])
