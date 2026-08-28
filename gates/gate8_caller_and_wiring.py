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
                  "gates/run_all.py", "gates/verify_gates_can_fail.py")

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

    return gate.report(denominator="%d gate modules; %d removal-shaped scripts"
                                   % (kinds_a.get("gate module with a main()", 0),
                                      kinds_b.get("removal-shaped script", 0)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
