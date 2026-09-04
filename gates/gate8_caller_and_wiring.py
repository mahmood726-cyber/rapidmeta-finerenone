"""GATE 8 -- a gate with no caller is VACUOUS, and a removal path with no precondition refuses.

MAHMOOD'S RULING, 2026-08-28: *"A gate no script calls is a rule in a document with extra
steps."* `gates/absence.py` sat for a day with no caller. It was correct, tested, and inert --
AVAILABLE, NOT OPERATIVE, which is the distinction `.githooks/pre-commit` already warns about,
arriving in the work of the person building the gate for it.

This is the vacuum check one level up. Gate harness asks *did this gate reach the case it was
built to find*; gate 8 asks *does anything reach this gate at all*.

ARM A -- EVERY GATE NAMES ITS CALLER. A module in `gates/` that exports `main()` must be
invoked by the pre-push hook, the CI workflow, or `run_all.py`. Uncalled means VACUOUS, never
PASS: an uncalled gate cannot fail, and a check that cannot fail is verification theatre.

ARM B -- EVERY REMOVAL PATH INVOKES THE PRECONDITION. A script that deletes or tombstones a
corpus artefact must call `absence.sanction`, or be registered in REMOVAL_PATHS.json with a
state and a stated reason. A NEW removal-shaped script that is in neither fails this gate.

WHY A REGISTRY AND NOT PURE INFERENCE. Seventeen scripts contain a delete or a tombstone
write; hand-reading them, most remove a lock file, a probe directory or a temp artefact. A
detector that called all seventeen "removal paths" would be the third over-broad detector I
have written today -- 739 of 820 modules, 53 of 925 scripts, and a radius of 6 that was 155.
The registry records the hand-read verdict WITH ITS REASON, and the mechanical part is the one
thing inference does well: noticing that a new one has appeared.
"""
from __future__ import annotations

import ast
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

REGISTRY = "REMOVAL_PATHS.json"
CALLER_SOURCES = (".githooks/pre-push", ".github/workflows/executable-rule-gates.yml",
                  ".github/workflows/hook-chain.yml",
                  "gates/run_all.py", "gates/verify_gates_can_fail.py",
                  # ADDED 2026-09-04, OWNER-AUTHORISED. gates/run_repo_checks.py is
                  # invoked from .githooks/pre-push:338 and executes every entry in
                  # this manifest's `pre_push` list. A script wired THERE genuinely
                  # runs on every push, and arm A could not see it -- so it accused
                  # three correctly-wired instruments of having no caller. That is
                  # the manufactured violation the note below already describes.
                  # Reach only: nothing about what counts as a violation changed.
                  "gates/WIRED_REPO_CHECKS.json")
# ⚠️ ARM A READS THIS LIST; ARM B READS EVERY FILE IN .github/workflows/. That is an
# inconsistency inside one gate rather than a policy: a module run by any workflow other
# than executable-rule-gates.yml is invisible to arm A, which then accuses it of having no
# caller. The guard just below already names that as the worse direction -- "arm A would
# under-report every gate as uncalled, which is the opposite error and just as bad" -- so a
# workflow that really does run a gate belongs here. Adding a caller SURFACE does not
# change what counts as a violation; it stops one being manufactured.

OSMOD = {"os", "shutil"}
DELETES = {"remove", "unlink", "rmtree"}
MOVES = {"replace", "rename", "move"}
# A REMOVAL BY MOVE IS STILL A REMOVAL, AND THIS DETECTOR STILL CANNOT SEE ALL OF THEM.
#
# The first version looked only for deletes and missed `prune_legacy_corpus_2026_08_26.py` --
# the 1,191-page prune, and the script whose own docstring carries the rule this gate
# enforces. It does not delete: it `os.replace(src, dst)` into `_pruned_2026_08_26/`,
# deliberately, so an abort is recoverable without git. From a reader's side a page moved out
# of the served tree is gone; only the recovery story differs.
#
# Widening to moves catches the case where the DESTINATION IS A LITERAL naming a quarantine
# directory. It does NOT catch the prune, because both paths are variables and resolving them
# is dataflow analysis this gate does not do. `os.replace(tmp, real)` is also how every atomic
# write in this repo works, so treating all moves as removals would be the fourth over-broad
# detector of the day.
#
# ⇒ THE LIMIT IS STATED RATHER THAN PAPERED OVER, and printed on every run: a NEW
# variable-path move-based removal is invisible here. The known ones are covered by name in
# the registry. Found by asking the detector about the four scripts I already knew were
# removals -- the check that should follow every detector: does it see the cases I can name?
QUARANTINE = re.compile(r"removed|retired|delisted|deleted|quarantine|_archive", re.I)
TEMPISH = re.compile(r"temp|tmp|scratch|__pycache__|\.pyc|mkdtemp|TemporaryDirectory|"
                     r"build-artefacts|outputs/", re.I)
TOMBSTONE_WRITE = re.compile(r"TOMB\s*%|TOMB\.format|write\(\s*TOMB")


def removal_shaped(src):
    """(removes_corpus_path, writes_tombstone). Shape only -- the verdict is in the registry.

    "Removes" covers deleting AND moving into a quarantine directory. See QUARANTINE above.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    corpus = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        base = n.func.value
        bn = base.id if isinstance(base, ast.Name) else None
        if bn in OSMOD and n.func.attr in DELETES and n.args:
            arg = ast.unparse(n.args[0])
            if not TEMPISH.search(arg):
                corpus.append(arg[:60])
        elif bn in OSMOD and n.func.attr in MOVES and len(n.args) >= 2:
            dest = ast.unparse(n.args[1])
            src_ = ast.unparse(n.args[0])
            if QUARANTINE.search(dest) and not TEMPISH.search(src_):
                corpus.append("%s -> %s" % (src_[:28], dest[:28]))
    return corpus, bool(TOMBSTONE_WRITE.search(src))


# KNOWN-NEGATIVE CONTROL for the removal-shape detector: source that must NOT read as a
# corpus removal. Added because gate 2 caught THIS module reporting counts from regexes over
# source with no measured precision -- the third gate of mine it has caught doing that, and the
# second time it caught one in the same run in which that gate was checking everyone else.
_NL = chr(10)
SHAPE_PROBES = [
    (_NL.join(["import os", "os.remove(tmp_path)"]), False,
     "removing a temp path is not a corpus removal"),
    (_NL.join(["import os", "os.replace(tmp, real)"]), False,
     "an atomic write is not a removal"),
    (_NL.join(["import shutil", "shutil.rmtree(scratch_dir)"]), False,
     "a scratch tree is not the corpus"),
    ("x = 'tombstone is mentioned in this docstring'", False,
     "naming a tombstone is not writing one"),
    ("s = page.replace('a', 'b')", False, "str.replace is not os.replace"),
    (_NL.join(["import os", "os.remove(page)"]), True,
     "removing a page IS a corpus removal"),
    (_NL.join(["import os", "os.replace(src, os.path.join(REPO, 'removed', f))"]), True,
     "a move into a quarantine directory IS a removal"),
    ("out.write(TOMB % {'title': t})", True, "writing a tombstone IS a removal"),
]


def run_shape_control(gate):
    wrong, fp = [], 0
    for src, expect, why in SHAPE_PROBES:
        corpus, tomb = removal_shaped(src)
        got = bool(corpus or tomb)
        if got != expect:
            wrong.append("%s -> expected %s, got %s" % (why, expect, got))
            if got and not expect:
                fp += 1
    negatives = [q for q in SHAPE_PROBES if not q[1]]
    gate.control(len(negatives), fp, wrong)
    if wrong:
        gate.broken("the removal-shape detector failed %d of %d probes: %s"
                    % (len(wrong), len(SHAPE_PROBES), "; ".join(wrong)))


def arm_a(gate, repo):
    """Every gate module must be named by something that runs it."""
    callers = ""
    for rel in CALLER_SOURCES:
        p = os.path.join(repo, rel)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                callers += fh.read()
        else:
            gate.broken("caller source %s is absent; arm A would under-report every gate as "
                        "uncalled, which is the opposite error and just as bad." % rel)

    kinds = collections.Counter()
    uncalled = []
    gdir = os.path.join(repo, "gates")
    for fn in sorted(os.listdir(gdir)):
        if not fn.endswith(".py") or fn.startswith("_"):
            kinds["gates/ module that is a library, not a gate"] += 1
            continue
        with open(os.path.join(gdir, fn), "r", encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        if "def main(" not in src:
            kinds["gates/ module that is a library, not a gate"] += 1
            continue
        stem = fn[:-3]
        kinds["gate module with a main()"] += 1
        if stem in callers or fn in callers:
            kinds["  named by a caller"] += 1
        else:
            kinds["  NO CALLER -- cannot fail, so cannot protect"] += 1
            uncalled.append("gates/" + fn)
    return uncalled, kinds


# ---------------------------------------------------------------------------
# ARM A2 -- THE REPO'S OWN GATES, not just this lane's.
#
# Arm A covered gates/ and found one uncalled module: itself. Pointed at scripts/, the same
# question returns a very different number, and it is the answer to "is the system stopping us
# repeating mistakes": 200 scripts named like a gate CAN fail, and 156 of them are called by
# NOTHING. A further 59 are named like a gate and have no failing exit at all.
#
# The instance that earned this arm: scripts/lint_shared_scratch_path_2026_08_24.py was
# written four days ago, documents a lane clobbering another lane's file in the shared scratch
# root, and is called by nothing -- so it did not fire when this lane did exactly that.
# ---------------------------------------------------------------------------
REPO_GATE = re.compile(r"^(gate|check|lint|audit|sweep|verify|assert|detect|probe)_"
                       r"|_(gate|check|lint|audit|sweep)\.py$")
UNCALLED_BACKLOG = "UNCALLED_REPO_GATES.json"


def arm_a2(gate, repo):
    callers = ""
    # ADDED 2026-09-04, OWNER-AUTHORISED: gates/WIRED_REPO_CHECKS.json. Arm A2 keeps
    # its OWN copy of this list, separate from CALLER_SOURCES above -- the same list
    # written twice, which is why adding the surface in one place did not reach here.
    for rel in (".githooks/pre-push", ".githooks/pre-commit", ".githooks/pre-commit-staging",
                "gates/run_all.py", "gates/verify_gates_can_fail.py",
                "gates/WIRED_REPO_CHECKS.json"):
        p = os.path.join(repo, rel)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                callers += fh.read()
    wf = os.path.join(repo, ".github", "workflows")
    if os.path.isdir(wf):
        for f in sorted(os.listdir(wf)):
            with open(os.path.join(wf, f), "r", encoding="utf-8", errors="replace") as fh:
                callers += fh.read()

    # A GATE THAT IS ITSELF CALLED IS A CALLER. Arm A2 previously read only the hooks and
    # the workflows, so a script invoked by a REGISTERED gate -- which the hook does run,
    # every push -- was still reported as "called by nothing". That is not a lenient
    # definition being tightened; it is a wrong answer: the script runs on every push.
    #
    # THE GUARANTEE IS PRESERVED BECAUSE ONLY REGISTERED GATES COUNT. The names are taken
    # from run_all.GATES, which is the list the hook actually executes. A script called
    # only by an UNregistered gate module is still inert and still reported, because that
    # gate is itself inert -- which arm A already catches.
    registered = ""
    try:
        sys.path.insert(0, os.path.join(repo, "gates"))
        import run_all as _ra
        for mod, _what, _speed in _ra.GATES:
            gp = os.path.join(repo, "gates", mod + ".py")
            if os.path.exists(gp):
                with open(gp, "r", encoding="utf-8", errors="replace") as fh:
                    registered += fh.read()
    except Exception:
        # A failure here must not silently widen the caller set: leaving `registered`
        # empty means this arm falls back to hooks and CI only, which OVER-reports
        # inertness. That is the safe direction, and it is stated rather than assumed.
        registered = ""
    callers += registered

    kinds = collections.Counter()
    uncalled = []
    sdir = os.path.join(repo, "scripts")
    for fn in sorted(os.listdir(sdir)):
        if not fn.endswith(".py") or not REPO_GATE.search(fn):
            continue
        with open(os.path.join(sdir, fn), "r", encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        if "sys.exit" not in src and "SystemExit" not in src:
            kinds["named like a gate, has NO failing exit -- cannot fail at all"] += 1
            continue
        kinds["repo gate/lint that CAN fail"] += 1
        if fn[:-3] in callers or fn in callers:
            kinds["  called by a hook or CI"] += 1
        else:
            kinds["  CALLED BY NOTHING -- available, not operative"] += 1
            uncalled.append("scripts/" + fn)
    return uncalled, kinds


def arm_b(gate, repo):
    regpath = os.path.join(repo, "gates", REGISTRY)
    registry = H.load(regpath) if os.path.exists(regpath) else {"paths": {}}
    reg = registry.get("paths", {})

    kinds = collections.Counter()
    unregistered, mis_declared = [], []
    sdir = os.path.join(repo, "scripts")
    for fn in sorted(os.listdir(sdir)):
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(sdir, fn), "r", encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        shape = removal_shaped(src)
        if shape is None:
            kinds["unparseable"] += 1
            continue
        corpus, tomb = shape
        if not corpus and not tomb:
            kinds["not removal-shaped"] += 1
            continue
        rel = "scripts/" + fn
        kinds["removal-shaped script"] += 1
        calls = "absence.sanction" in src or "_absence.sanction" in src
        declared = reg.get(rel)
        if declared is None:
            kinds["  UNREGISTERED -- new since the registry was written"] += 1
            unregistered.append(rel)
            continue
        state = declared.get("state")
        kinds["  registered: " + str(state)] += 1
        if state == "WIRED" and not calls:
            mis_declared.append("%s is registered WIRED and does not call absence.sanction"
                                % rel)
        if state != "WIRED" and calls:
            mis_declared.append("%s calls absence.sanction but is registered %r -- the "
                                "registry is behind the code" % (rel, state))
    return unregistered, mis_declared, kinds, reg


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("8  CALLER AND WIRING",
                  "a gate with no caller cannot fail; a removal path with no precondition "
                  "must not run")

    gate.expect_case("absence-is-called",
                     "gates/absence.py is invoked by the live retirement path")
    gate.expect_case("a-gate-has-a-caller",
                     "at least one gate module is named by the hook or CI")

    gate.requires_control()
    run_shape_control(gate)
    H.assert_append_only_intact(gate, repo)

    uncalled, kinds_a = arm_a(gate, repo)
    repo_uncalled, kinds_a2 = arm_a2(gate, repo)
    new_uncalled = H.ratchet(gate, UNCALLED_BACKLOG, repo_uncalled,
                             "scripts named like a gate that CAN fail and are called by "
                             "nothing. Available, not operative.")
    if kinds_a.get("  named by a caller"):
        gate.saw("a-gate-has-a-caller")

    unregistered, mis_declared, kinds_b, reg = arm_b(gate, repo)

    wired = [p for p, d in reg.items() if d.get("state") == "WIRED"]
    for rel in wired:
        full = os.path.join(repo, rel)
        if os.path.exists(full):
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                if "absence" in fh.read():
                    gate.saw("absence-is-called")

    if "--plant" in argv:
        unregistered.append("scripts/__planted_removal_without_a_precondition.py")
        kinds_b["  UNREGISTERED -- new since the registry was written"] += 1
        gate.note("PLANTED: a new removal-shaped script in neither the registry nor wired")

    merged = dict(kinds_a)
    merged.update(kinds_a2)
    merged.update(kinds_b)
    gate.kinds(merged)
    gate.note("KNOWN BLIND SPOT, stated every run: a removal performed by os.replace/os.rename "
              "into a VARIABLE destination is not detected. prune_legacy_corpus_2026_08_26.py "
              "is exactly that shape and is covered by name in the registry, not by the "
              "detector. A NEW script of that shape would pass this gate.")

    for g in uncalled:
        gate.finding("GATE-WITH-NO-CALLER",
                     "%s exports main() and nothing runs it. An uncalled gate cannot fail, "
                     "and a check that cannot fail is verification theatre." % g,
                     numerator=len(uncalled),
                     denominator=kinds_a.get("gate module with a main()", 0))
    for mod in new_uncalled:
        gate.finding("NEW-GATE-WITH-NO-CALLER",
                     "%s is named like a gate, can fail, and nothing runs it. It is NEW since "
                     "the backlog was frozen -- a gate written and left inert." % mod,
                     numerator=len(new_uncalled), denominator=len(repo_uncalled))
    for rel in unregistered:
        gate.finding("REMOVAL-PATH-NOT-DECLARED",
                     "%s deletes or tombstones a corpus artefact and is neither wired to "
                     "absence.sanction nor declared in gates/%s with a reason. Every removal "
                     "path must invoke the precondition or say why it need not."
                     % (rel, REGISTRY),
                     numerator=len(unregistered),
                     denominator=kinds_b.get("removal-shaped script", 0))
    for m in mis_declared:
        gate.finding("REGISTRY-DISAGREES-WITH-THE-CODE", m)

    art = os.path.join(repo, "out", "gate8_caller_and_wiring.json")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8") as fh:
        json.dump({"gate": gate.as_json(), "uncalled_gates": uncalled,
                   "unregistered_removal_paths": unregistered,
                   "mis_declared": mis_declared}, fh, indent=1)

    # COVERAGE. A file named like a gate with NO failing exit cannot be assessed for whether
    # it would fail; there is nothing to trip. The known os.replace blind spot is real and
    # is NOT in this fraction, because it cannot be counted -- it is named in a note instead.
    gate.coverage(gate.kind("repo gate/lint that CAN fail"),
                  max(gate.kind("repo gate/lint that CAN fail")
                      + gate.kind("named like a gate, has NO failing exit -- cannot fail at all"), 1),
                  "files named like a gate with no reachable failing exit, which this gate "
                  "counts but cannot assess, plus an uncountable blind spot named in the notes")
    return gate.report(denominator="%d gate modules; %d removal-shaped scripts"
                                   % (kinds_a.get("gate module with a main()", 0),
                                      kinds_b.get("removal-shaped script", 0)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
