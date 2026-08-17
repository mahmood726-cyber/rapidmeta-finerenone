"""The detector registry. A detector that has never fired cannot be registered.

The admission rule, in one line: no detector counts until it has been
demonstrated firing on a real positive AND silent on a real negative.

This is the direct countermeasure to the documented failure in
`14_RULE_TESTS_AND_SPECIFICATIONS.md`, where five rules were propagated before
any of them had been fired, three needed repair, and Rules 4 and 5 "in their v1
form were incapable of firing on the failures they existed to prevent".
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .check import Check
from .verdict import Result, Verdict, make_invalid


class InadmissibleDetector(ValueError):
    pass


class Registry:
    def __init__(self) -> None:
        self._checks: dict[str, Check] = {}

    # ---------- registration --------------------------------------------------

    def register(self, check: Check) -> Check:
        problems = check.admissibility_problems()
        if problems:
            raise InadmissibleDetector(
                f"{check.check_id} is inadmissible:\n  - " + "\n  - ".join(problems))
        if check.check_id in self._checks:
            raise InadmissibleDetector(f"{check.check_id} already registered")
        self._checks[check.check_id] = check
        return check

    def __contains__(self, check_id: object) -> bool:
        return check_id in self._checks

    def __len__(self) -> int:
        return len(self._checks)

    def ids(self) -> list[str]:
        return sorted(self._checks)

    def get(self, check_id: str) -> Check:
        return self._checks[check_id]

    # ---------- execution -----------------------------------------------------

    def run(self, check_id: str, payload: Mapping[str, Any]) -> Result:
        if check_id not in self._checks:
            return make_invalid(check_id, "registry",
                                "no such detector registered -- an unregistered "
                                "check cannot produce a clean result")
        return self._checks[check_id].run(payload)

    def run_all(self, payload: Mapping[str, Any]) -> list[Result]:
        return [self.run(cid, payload) for cid in self.ids()]

    # ---------- the self-test that must pass before any real run --------------

    def self_test(self) -> dict:
        """Fire every registered detector against its own fixtures.

        Returns a report, never a bare boolean. If any detector's controls
        misbehave, the whole registry is unfit and the caller must not report
        results from it.
        """
        report: dict[str, Any] = {"checks": {}, "unfit": []}
        for cid, chk in sorted(self._checks.items()):
            controls = chk.run_controls()
            report["checks"][cid] = controls
            if not controls["ok"]:
                report["unfit"].append(cid)
        report["ok"] = not report["unfit"]
        report["n_checks"] = len(self._checks)
        return report

    def fixture_coverage(self) -> dict:
        """Which historical incidents are pinned by at least one fixture."""
        cover: dict[str, list[str]] = {}
        for cid, chk in self._checks.items():
            for f in list(chk.must_fire_on) + list(chk.must_be_silent_on):
                if f.provenance:
                    cover.setdefault(f.provenance, []).append(f"{cid}:{f.name}")
        return {k: sorted(v) for k, v in sorted(cover.items())}
