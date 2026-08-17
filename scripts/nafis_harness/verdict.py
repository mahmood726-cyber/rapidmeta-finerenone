"""Three-state verdicts with a mandatory witness on every PASS.

The clinical model. A diagnostic assay runs a positive and a negative control on
every plate. When a control fails, the run is void and NO RESULT IS REPORTED --
the laboratory does not report a negative from a dead plate. Every catalogued
failure in this project was a negative reported from a dead plate:

  * a 429 rate-limit read as "no record exists"
  * `pgrep` on Windows -- which always returns nothing -- read as "process exited"
  * a `ref`-based click that silently no-op'd, read as "clicked"
  * a caption checker reading the downloads block, returning zero findings

In each case the instrument was incapable of producing the opposite answer, and
the absence of a finding was reported as a finding of absence.

This module makes that structurally impossible in three ways:

  1. FAIL and INVALID are different values. There is no boolean to collapse them
     into. A check that cannot see cannot say "clean".
  2. A PASS carries a Witness -- what was observed, where, and what the opposite
     observation would have looked like on this instrument. A PASS without a
     witness is not a PASS; it is coerced to INVALID and says so.
  3. Verdicts do not silently become booleans. `bool(Result)` raises.

Pure stdlib. No network, no model calls, no I/O. Deterministic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Mapping


class Verdict(str, Enum):
    """Three states. FAIL and INVALID are not interchangeable.

    PASS    -- the check ran on a live instrument and the property holds.
               Requires a Witness.
    FAIL    -- the check ran on a live instrument and the property does not hold.
               This is a positive finding of a defect.
    INVALID -- the check did not run, could not see, ran on a dead instrument,
               was vacuous, or produced a PASS it could not witness.
               This is NOT a clean result. It carries no information about the
               property. It must never be counted as a PASS or as a FAIL.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    INVALID = "INVALID"

    def is_reportable(self) -> bool:
        """INVALID results are not reportable as findings, in either direction."""
        return self is not Verdict.INVALID


class WitnessError(ValueError):
    """Raised when a PASS is constructed without an adequate witness in strict mode."""


@dataclass(frozen=True)
class Witness:
    """Concrete evidence for a PASS, including the instrument-declaration term.

    `opposite_would_be` is the load-bearing field and the reason this class
    exists. Before recording a result you must state what the opposite outcome
    would have looked like ON THIS INSTRUMENT. If you cannot describe a distinct
    observation that the instrument would have produced had the answer been the
    other way, the instrument cannot discriminate and the result is void.

    The holdings-table case is the one this field is aimed at and does not fully
    solve -- see BLIND_SPOTS in the accompanying report. A holdings table CAN
    produce the opposite observation (a title absent from the list), so this
    field is satisfiable while the check still answers the wrong question.
    """

    observed: str          # what was actually seen, verbatim where possible
    locator: str           # exactly where: path+line, table+row, url+field, NCT+module
    opposite_would_be: str # the distinct observation a FAIL would have produced here

    def deficiencies(self) -> list[str]:
        out = []
        if not (self.observed or "").strip():
            out.append("witness.observed is empty")
        if not (self.locator or "").strip():
            out.append("witness.locator is empty")
        if not (self.opposite_would_be or "").strip():
            out.append("witness.opposite_would_be is empty "
                       "(instrument declaration missing: state what a FAIL "
                       "would have looked like on this instrument)")
        return out

    def is_adequate(self) -> bool:
        return not self.deficiencies()


@dataclass(frozen=True)
class Result:
    """The only object a check may return.

    Construction enforces the witness rule. A PASS without an adequate witness
    is rewritten to INVALID with the deficiency recorded in `reason`. The
    rewrite is loud: the caller gets INVALID, never a quiet PASS.
    """

    check_id: str
    verdict: Verdict
    instrument: str
    reason: str = ""
    witness: Witness | None = None
    evidence: Mapping[str, Any] = field(default_factory=dict)
    controls: Mapping[str, Any] = field(default_factory=dict)
    vacuity: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # SYMMETRIC WITNESS OBLIGATION.
        #
        # This rule used to apply to PASS only. That one-sidedness is a
        # documented failure mode, not a theoretical one:
        # METHODS_negative_evidence.md records that the same rule, written the
        # same way, "was written asymmetrically: it demanded a positive-detection
        # story before recording a NEGATIVE. Within the hour it failed in the
        # other direction" -- Instance 5, a LibKey DOWNLOAD PDF button read as
        # proof of entitlement, when "LibKey renders affordances from metadata
        # and library configuration; it does not prove a delivery will complete."
        #
        # The rule as the lane finally stated it is symmetric and is now
        # implemented symmetrically:
        #
        #   "Before recording ANY result, state what the opposite result would
        #    have looked like on that instrument. If you cannot answer, the
        #    instrument is wrong and the result is void -- WHICHEVER DIRECTION
        #    IT FELL IN."
        #
        # For a FAIL, `opposite_would_be` is what a PASS would have looked like.
        # A defect asserted from an instrument that could not have cleared the
        # subject is as void as a clean bill from one that could not have failed
        # it -- and a false defect is how a correction becomes worse than the
        # original (M10).
        if self.verdict in (Verdict.PASS, Verdict.FAIL):
            problems = ["no witness supplied"] if self.witness is None \
                else self.witness.deficiencies()
            if problems:
                original = self.verdict.value
                object.__setattr__(self, "verdict", Verdict.INVALID)
                joined = "; ".join(problems)
                object.__setattr__(
                    self, "reason",
                    f"{original} refused -- {joined}."
                    + (f" (original reason: {self.reason})" if self.reason else ""),
                )

    # A verdict must never collapse into a boolean. `if result:` is exactly the
    # bug this whole module exists to prevent -- INVALID would be truthy, and a
    # dead instrument would read as a clean one.
    def __bool__(self) -> bool:  # pragma: no cover - defensive
        raise TypeError(
            f"{self.check_id}: a Result is three-state and must not be used as a "
            "boolean. Compare explicitly against Verdict.PASS / FAIL / INVALID."
        )

    @property
    def passed(self) -> bool:
        return self.verdict is Verdict.PASS

    @property
    def failed(self) -> bool:
        return self.verdict is Verdict.FAIL

    @property
    def invalid(self) -> bool:
        return self.verdict is Verdict.INVALID

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)

    def __str__(self) -> str:
        return f"[{self.verdict.value}] {self.check_id} ({self.instrument}): {self.reason}"


def make_pass(check_id: str, instrument: str, observed: str, locator: str,
              opposite_would_be: str, reason: str = "", **evidence) -> Result:
    """Convenience constructor that forces the three witness fields to be named."""
    return Result(
        check_id=check_id,
        verdict=Verdict.PASS,
        instrument=instrument,
        reason=reason,
        witness=Witness(observed=observed, locator=locator,
                        opposite_would_be=opposite_would_be),
        evidence=evidence,
    )


def make_fail(check_id: str, instrument: str, reason: str, *,
              observed: str, locator: str, opposite_would_be: str,
              **evidence) -> Result:
    """A FAIL now carries a witness too. See Result.__post_init__ for why.

    `opposite_would_be` on a FAIL is what a PASS would have looked like on this
    instrument -- the same question, asked from the other side.
    """
    return Result(check_id=check_id, verdict=Verdict.FAIL, instrument=instrument,
                  reason=reason,
                  witness=Witness(observed=observed, locator=locator,
                                  opposite_would_be=opposite_would_be),
                  evidence=evidence)


def make_invalid(check_id: str, instrument: str, reason: str, **evidence) -> Result:
    return Result(check_id=check_id, verdict=Verdict.INVALID, instrument=instrument,
                  reason=reason, evidence=evidence)


def tally(results) -> dict:
    """Counts that keep INVALID separate. There is deliberately no 'clean' total.

    Any downstream summary that wants a pass rate must decide, in the open, what
    it does with INVALID -- it cannot get a denominator by accident.
    """
    counts = {"PASS": 0, "FAIL": 0, "INVALID": 0}
    for r in results:
        counts[r.verdict.value] += 1
    counts["reportable"] = counts["PASS"] + counts["FAIL"]
    counts["total"] = counts["reportable"] + counts["INVALID"]
    return counts
