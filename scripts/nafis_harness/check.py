"""Checks that run their own controls, and a vacuity sweep, on every execution.

Three mechanisms live here.

CONTROLS (the dead-plate rule)
------------------------------
A Check declares fixtures it must fire on (known-defect inputs, expect FAIL) and
fixtures it must stay silent on (known-clean inputs, expect PASS). Those controls
are re-run on EVERY execution, not once at registration. If a control
misbehaves, the run is void: the payload result is discarded and INVALID is
returned. No negative is reported from a dead plate.

This is what makes `pgrep` on Windows harmless. `pgrep` returns nothing for a
live process and nothing for a dead one, so the must-fire control -- a process
known to be running -- does not fire, the run is void, and the liveness check
reports INVALID rather than "exited".

VACUITY (Beer et al.)
---------------------
A check can pass for reasons unrelated to the property it claims to test. The
caption checker that read the downloads block passed a document with broken
captions because the term it observed was not the captions. Vacuity detection:
force each declared observation term to the value that SHOULD flip the verdict,
re-run, and if PASS survives, the check never depended on that term. It is
vacuous and the verdict is INVALID.

Cost: n+1 executions of a deterministic CPU function for n observation terms.
No model calls. This is the cheapest high-value item in the harness.

MUTATION ADMISSIBILITY
----------------------
A Check with no fixtures cannot be registered (see registry.py). A detector that
has never been demonstrated firing is an unproven detector, and by this project's
own record -- `14_RULE_TESTS_AND_SPECIFICATIONS.md`, "a rule that cannot fire is
not a rule" -- three of five rules that had never been fired needed repair, and
two of them were incapable of firing on the failures they existed to prevent.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from .verdict import Result, Verdict, Witness, make_invalid


@dataclass(frozen=True)
class Instrument:
    """A declaration of what the check can and cannot see.

    `can_distinguish_absent_from_unreachable` is the field that separates a 429
    from an empty result set. If it is False, the check may never return FAIL on
    the grounds of absence -- absence is INVALID until an instrument that can
    distinguish the two says otherwise.
    """

    name: str
    reads: tuple[str, ...]
    can_distinguish_absent_from_unreachable: bool = True
    platforms: tuple[str, ...] = ("any",)

    def available_here(self) -> bool:
        if "any" in self.platforms:
            return True
        return platform.system().lower() in {p.lower() for p in self.platforms}


@dataclass(frozen=True)
class Fixture:
    """A named, real input with a known correct verdict.

    `provenance` should point at the historical incident the fixture encodes, so
    that nobody deletes it as noise later.
    """

    name: str
    payload: Mapping[str, Any]
    expect: Verdict
    provenance: str = ""


CheckFn = Callable[[Mapping[str, Any]], Result]
Mutator = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass
class Check:
    check_id: str
    instrument: Instrument
    fn: CheckFn
    must_fire_on: Sequence[Fixture] = field(default_factory=tuple)
    must_be_silent_on: Sequence[Fixture] = field(default_factory=tuple)
    observation_terms: Mapping[str, Mutator] = field(default_factory=dict)
    description: str = ""

    # ---------- admissibility -------------------------------------------------

    def admissibility_problems(self) -> list[str]:
        problems = []
        if not self.must_fire_on:
            problems.append(
                "no must_fire_on fixture: detector has never been demonstrated "
                "firing on a real positive")
        if not self.must_be_silent_on:
            problems.append(
                "no must_be_silent_on fixture: detector has never been "
                "demonstrated silent on a real negative")
        for f in self.must_fire_on:
            if f.expect is not Verdict.FAIL:
                problems.append(f"must_fire_on fixture {f.name!r} does not expect FAIL")
        for f in self.must_be_silent_on:
            if f.expect is not Verdict.PASS:
                problems.append(f"must_be_silent_on fixture {f.name!r} does not expect PASS")
        if not self.observation_terms:
            problems.append(
                "no observation_terms declared: the vacuity sweep cannot run, so "
                "the check cannot be shown to depend on anything it reads")
        return problems

    # ---------- execution -----------------------------------------------------

    def _raw(self, payload: Mapping[str, Any]) -> Result:
        try:
            r = self.fn(payload)
        except Exception as exc:  # an exception is never a clean result
            return make_invalid(self.check_id, self.instrument.name,
                                f"check raised {type(exc).__name__}: {exc}")
        if not isinstance(r, Result):
            return make_invalid(self.check_id, self.instrument.name,
                                f"check returned {type(r).__name__}, not a Result")
        return r

    def run_controls(self) -> dict:
        """Run every control. Cheap, deterministic, every time."""
        report = {"fired": [], "silent": [], "misbehaved": []}
        for f in self.must_fire_on:
            got = self._raw(f.payload)
            entry = {"fixture": f.name, "expected": "FAIL", "got": got.verdict.value}
            if got.verdict is Verdict.FAIL:
                report["fired"].append(entry)
            else:
                entry["reason"] = got.reason
                report["misbehaved"].append(entry)
        for f in self.must_be_silent_on:
            got = self._raw(f.payload)
            entry = {"fixture": f.name, "expected": "PASS", "got": got.verdict.value}
            if got.verdict is Verdict.PASS:
                report["silent"].append(entry)
            else:
                entry["reason"] = got.reason
                report["misbehaved"].append(entry)
        report["ok"] = not report["misbehaved"]
        return report

    def run_vacuity(self, payload: Mapping[str, Any]) -> dict:
        """Beer-style vacuity: flip each observation term, expect the verdict to move.

        Only meaningful when the unmutated verdict is PASS. A FAIL is a positive
        finding and is not at risk of being vacuously clean.

        A mutator may return EITHER a single mutated payload OR a list of them.
        The list form exists because of a defect found by mutation testing rather
        than by review: CHK005's row mutator was

            lambda p: _deep(p, ["row", sorted(p["row"])[0]], -1)

        which forces only the ALPHABETICALLY FIRST key of a mapping-valued term.
        The sweep therefore covered one key in six, by alphabetical accident:
        renaming `dosed` -> `zz_dosed`, semantics unchanged, flipped INVALID to
        PASS, and renaming `registry_enrolment` -> `aaa_registry_enrolment` moved
        the catch onto that key instead. Coverage that depends on key spelling is
        not coverage.

        A term is vacuous if ANY of its mutants leaves the PASS standing, and the
        report names the specific sub-mutant, not just the term.
        """
        report: dict = {"terms": {}, "vacuous_terms": [], "mutants_run": 0}
        for term, mutate in self.observation_terms.items():
            try:
                produced = mutate(payload)
            except Exception as exc:
                report["terms"][term] = f"mutator raised {type(exc).__name__}: {exc}"
                report["vacuous_terms"].append(term)
                continue

            if isinstance(produced, list):
                mutants = produced
            else:
                mutants = [produced]
            if not mutants:
                report["terms"][term] = "mutator produced no mutants"
                report["vacuous_terms"].append(term)
                continue

            outcomes = []
            for i, mutated in enumerate(mutants):
                label = mutated.pop("_mutant_label", None) if isinstance(
                    mutated, dict) else None
                got = self._raw(mutated)
                report["mutants_run"] += 1
                name = label or (f"{term}[{i}]" if len(mutants) > 1 else term)
                outcomes.append({"mutant": name, "verdict": got.verdict.value})
                if got.verdict is Verdict.PASS:
                    # forcing this term to its flipping value left the PASS
                    # standing: the verdict never depended on it
                    report["vacuous_terms"].append(name)
            report["terms"][term] = outcomes if len(outcomes) > 1 \
                else outcomes[0]["verdict"]

        report["ok"] = not report["vacuous_terms"]
        return report

    def run(self, payload: Mapping[str, Any], *, vacuity: bool = True) -> Result:
        if not self.instrument.available_here():
            return make_invalid(
                self.check_id, self.instrument.name,
                f"instrument not available on {platform.system()!r} "
                f"(declared platforms: {self.instrument.platforms}). "
                "A check that cannot run here returns INVALID, never PASS.")

        controls = self.run_controls()
        if not controls["ok"]:
            return Result(
                check_id=self.check_id, verdict=Verdict.INVALID,
                instrument=self.instrument.name,
                reason="control failure -- run void, no result reported: "
                       + "; ".join(f"{m['fixture']} expected {m['expected']} "
                                   f"got {m['got']}"
                                   for m in controls["misbehaved"]),
                controls=controls)

        result = self._raw(payload)
        vac: dict = {}
        if vacuity and result.verdict is Verdict.PASS:
            vac = self.run_vacuity(payload)
            if not vac["ok"]:
                return Result(
                    check_id=self.check_id, verdict=Verdict.INVALID,
                    instrument=self.instrument.name,
                    reason="PASS is vacuous -- verdict survived forcing "
                           + ", ".join(vac["vacuous_terms"])
                           + " to its flipping value, so the check does not "
                             "depend on the term it claims to observe",
                    controls=controls, vacuity=vac)

        return Result(check_id=result.check_id, verdict=result.verdict,
                      instrument=result.instrument, reason=result.reason,
                      witness=result.witness, evidence=result.evidence,
                      controls=controls, vacuity=vac)
