"""Is the harness gate actually installed? Measured, not declared.

WHY THIS MODULE EXISTS
    The ledger's headline is "what fraction would be caught if it recurred". If I
    typed `guard_state=WIRED` for the detectors I wired, the number would move
    because I said so. It would then be a claim about a build I cannot see, made
    by the party with an interest in the number going up.

    So WIRED is DETECTED. This module looks for a hook that references
    `harness_gate.py` and for the script existing beside it. If the corpus lane
    installs it, the ledger's number moves on its own, on the next run. If they
    do not, it does not move, and no amount of work on my side changes that.

    This is CHK005 applied to my own reporting: an external referent, not a
    second copy of my intention.

WHAT COUNTS AS INSTALLED, and what deliberately does not
    - a hook file that names harness_gate.py, AND the script present  -> INSTALLED
    - the script present but no hook naming it                        -> NOT
    - a hook naming it but the script missing                         -> NOT, and
      it is worse than not installed: the pre-push hook's own rule is "Refusing
      to pass a check that is not present", so this state blocks every push.
      Reported separately as BROKEN.
    - `core.hooksPath` unset is NOT checked here. gate_integrity.py is explicit
      that wiring is the clone sweep's job, not a gate's, and pretending to check
      it from a read-only mount would be the same over-claim one level down.
"""

from __future__ import annotations

import os
from typing import Any

GATE_FILENAME = "harness_gate.py"

# Roots to probe. Read-only mounts are fine: existence is all that is asked.
DEFAULT_ROOTS = [
    r"F:\rapidmeta-ssot-shell",
    r"F:\rapidmeta-finerenone",
    "/sessions/vigilant-trusting-gauss/mnt/rapidmeta-ssot-shell",
    "/sessions/vigilant-trusting-gauss/mnt/rapidmeta-finerenone",
]

HOOK_NAMES = ("pre-push", "pre-commit", "pre-receive")


def detect(roots: list[str] | None = None) -> dict[str, Any]:
    roots = roots if roots is not None else DEFAULT_ROOTS
    evidence: list[str] = []
    installed_roots: list[str] = []
    broken_roots: list[str] = []
    probed = 0

    for root in roots:
        if not os.path.isdir(root):
            continue
        probed += 1
        script = os.path.join(root, "scripts", GATE_FILENAME)
        script_present = os.path.isfile(script)
        referenced = False
        for hd in (os.path.join(root, ".githooks"),
                   os.path.join(root, ".git", "hooks")):
            if not os.path.isdir(hd):
                continue
            for name in HOOK_NAMES:
                hp = os.path.join(hd, name)
                if not os.path.isfile(hp):
                    continue
                try:
                    with open(hp, encoding="utf-8", errors="replace") as fh:
                        if GATE_FILENAME in fh.read():
                            referenced = True
                            evidence.append(f"{hp} references {GATE_FILENAME}")
                except OSError as exc:
                    evidence.append(f"{hp} unreadable: {exc}")
        if referenced and script_present:
            installed_roots.append(root)
            evidence.append(f"{script} present")
        elif referenced and not script_present:
            broken_roots.append(root)
            evidence.append(f"{root}: hook references the gate but {script} is "
                            "MISSING -- this blocks every push")
        elif script_present:
            evidence.append(f"{root}: {GATE_FILENAME} present but no hook names it "
                            "-- present is not invoked")

    return {
        "installed": bool(installed_roots),
        "installed_roots": installed_roots,
        "broken_roots": broken_roots,
        "roots_probed": probed,
        "evidence": evidence,
        # A probe that reached nothing has not established absence. Same rule as
        # every other instrument in this package.
        "determinate": probed > 0,
    }


def status_line(d: dict[str, Any] | None = None) -> str:
    d = d if d is not None else detect()
    if not d["determinate"]:
        return ("harness gate: UNDETERMINED -- no candidate repo root was "
                "reachable, so installation is unknown, not absent")
    if d["broken_roots"]:
        return f"harness gate: BROKEN in {d['broken_roots']} (hook names a missing script)"
    if d["installed"]:
        return f"harness gate: INSTALLED in {d['installed_roots']}"
    return ("harness gate: NOT INSTALLED -- no hook in "
            f"{d['roots_probed']} probed root(s) references {GATE_FILENAME}")
