# -*- coding: utf-8 -*-
# KNOWN_NEGATIVE CONTROL -- EXECUTABLE, AND IT LIVES IN THIS FILE: --selftest.
#   [1] positive       a hook naming a script that is ON DISK but NOT in the index
#                      MUST be refused  (os.path.exists would pass this exact case)
#   [2] known negative the SAME hook once that script is staged too MUST NOT be refused
# Both measured against a real git index in a repo the selftest builds. The negative is what
# caught this file refusing everything once already: the extractor kept the shell-variable
# remnant, so `$R/scripts/x.py` read as `R/scripts/x.py` and every reference looked missing.
#   python scripts/lint_hook_references_resolve.py --selftest
# A count without a measured precision is not a finding.

"""A hook may not reference a script the same commit does not bring with it.

THE NEAR-MISS THIS WAS WRITTEN FROM, STOPPED BY HAND AT 02:00 AND ONLY BY LUCK.

A push retry loop re-read its inputs on every attempt. Between attempt one and attempt two
the hook file gained a line invoking a NEW lint -- but the loop's file list was written
before that lint existed, so a later attempt would have staged the hook WITHOUT the script
it calls. On main, `.githooks/pre-commit` would then invoke a path that does not exist:

    python "$R/scripts/lint_pathspecless_commit.py"   ->  no such file  ->  non-zero

and the hook refuses. EVERY COMMIT. FOR EVERY LANE. A repository bricked by a file that was
never added, with no bad code anywhere in it.

    ⛔ A HOOK AND EVERY SCRIPT IT INVOKES LAND IN ONE COMMIT, NEVER SEPARATELY.

TWO RULES, AND ONLY THE FIRST IS MECHANISABLE -- SAID PLAINLY RATHER THAN IMPLIED:

  1. ENFORCED HERE. Every path a tracked hook names must be present IN THE INDEX being
     committed -- not merely on this disk. A file that exists in your working tree and not in
     the commit is exactly the failure above; the person who clones does not have your disk.

  2. NOT ENFORCED HERE, AND NOT PRETENDED TO BE. A retry loop must commit a FROZEN SET,
     captured once before the first attempt. A loop that re-reads its inputs is NOT
     IDEMPOTENT: it commits a different thing each attempt, and the difference is invisible
     because every attempt looks like the same command. That is a discipline about how loops
     are written, and no pre-commit hook can see it. Rule 1 catches its worst outcome, which
     is why rule 1 is the one worth wiring.

RESOLVED AGAINST THE INDEX, DELIBERATELY. `os.path.exists` would pass on the exact defect
this exists to stop, because during that near-miss the file WAS on disk -- it was simply not
in the commit. The question is never "is it here", it is "will it be there for whoever
receives this commit". `git ls-files` answers that; the filesystem answers something else.

Read-only. Exit 1 refuses. `--selftest` builds a real repo, commits a hook that names a
missing script, and proves this refuses it.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

HOOK_DIR = ".githooks"
# Any token that looks like a repo path to a runnable file. Deliberately broad: a reference
# missed here is a reference not checked, and the cost of a false candidate is one lookup.
REF = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|sh|R|js)\b")
# Shell variables that stand in for the repo root in this project's hooks.
ROOT_VARS = ('"$R/', '"$(git rev-parse --show-toplevel)/', '$R/', "${R}/")


def _git(args, cwd=None, env=None):
    out = subprocess.run(["git"] + args, cwd=cwd or _ROOT, capture_output=True,
                         encoding="utf-8", errors="replace", env=env)
    return out.returncode, out.stdout, out.stderr


def tracked_or_staged(paths, cwd=None, env=None):
    """The subset of `paths` present in the INDEX -- i.e. that the commit will actually carry.

    Asked in ONE `git ls-files` call rather than one per path, because a per-path loop over a
    hook with two dozen references is two dozen process spawns inside a pre-commit hook.
    """
    if not paths:
        return set()
    rc, out, err = _git(["ls-files", "--"] + sorted(paths), cwd, env)
    if rc != 0:
        raise SystemExit("REFUSED: cannot read the index (%s). A check that cannot see what "
                         "the commit carries must not pass it." % err.strip()[:140])
    return {l.strip().replace("\\", "/") for l in out.splitlines() if l.strip()}


def hook_files(cwd=None):
    d = os.path.join(cwd or _ROOT, HOOK_DIR)
    if not os.path.isdir(d):
        return []
    out = []
    for fn in sorted(os.listdir(d)):
        full = os.path.join(d, fn)
        if os.path.isfile(full) and not fn.endswith(".md"):
            out.append((HOOK_DIR + "/" + fn, full))
    return out


def _top_dirs(cwd=None):
    """Top-level directory names, used to find where a repo-relative path really starts."""
    root = cwd or _ROOT
    try:
        return {d for d in os.listdir(root)
                if os.path.isdir(os.path.join(root, d)) and not d.startswith(".")} | {HOOK_DIR}
    except OSError:
        return {"scripts", "ssot", "gates", "tests", HOOK_DIR}


def references_of(text, tops=None):
    """Paths a hook actually invokes, normalised to repo-relative form.

    ⛔ THE SHELL VARIABLE IS PART OF THE TOKEN AND MUST BE CUT, AND THE SELFTEST IS WHAT
    CAUGHT THIS. Hooks here invoke `python "$R/scripts/foo.py"`. A regex for a path-like
    token starts matching at the R, yielding `R/scripts/foo.py` -- which is in no index, so
    EVERY reference read as missing and the check refused everything. That is the failure
    this repo has already paid for once, arriving inside the check written to prevent a
    different one. The fix is not a longer regex: it is to find where the REPO-RELATIVE part
    of the path begins, by looking for a directory that actually exists.
    """
    tops = _top_dirs() if tops is None else tops
    found = set()
    for m in REF.finditer(text):
        parts = m.group(0).replace("\\", "/").lstrip("./").split("/")
        for i, seg in enumerate(parts):
            if seg in tops:
                parts = parts[i:]
                break
        else:
            continue                     # names no known directory -- not a repo path
        if len(parts) < 2:
            continue
        found.add("/".join(parts))
    return found


def check(cwd=None, env=None):
    lines, missing = [], []
    hooks = hook_files(cwd)
    if not hooks:
        # A repo with no tracked hooks is a real state, not a pass to be announced quietly.
        lines.append("OK: no %s/ directory -- nothing to resolve." % HOOK_DIR)
        return 0, lines
    tops = _top_dirs(cwd)
    allrefs = {}
    for rel, full in hooks:
        try:
            with io.open(full, "rb") as fh:
                text = fh.read().decode("utf-8", "replace")
        except OSError as exc:
            # A hook that cannot be read cannot be cleared. Fail closed and name it.
            lines.append("")
            lines.append("REFUSED: cannot read %s (%s). An unreadable hook is not a hook "
                         "with no references." % (rel, exc))
            return 1, lines
        for r in references_of(text, tops):
            allrefs.setdefault(r, []).append(rel)
    present = tracked_or_staged(set(allrefs), cwd, env)
    for ref in sorted(allrefs):
        if ref not in present:
            missing.append((ref, allrefs[ref]))

    lines.append("hooks read: %d   references found: %d   present in the index: %d"
                 % (len(hooks), len(allrefs), len(present)))
    if not missing:
        return 0, lines
    lines.append("")
    lines.append("REFUSED: %d script(s) a hook invokes are NOT in this commit." % len(missing))
    for ref, by in missing:
        lines.append("    %-56s  named by %s" % (ref, ", ".join(by)))
    lines.append("")
    lines.append("On disk is not the question. Whoever receives this commit does not have")
    lines.append("your working tree, and a hook whose script is absent exits non-zero, which")
    lines.append("means EVERY COMMIT IN THE REPOSITORY FAILS -- for every lane, until someone")
    lines.append("works out that the bad file is the one that was never added.")
    lines.append("")
    lines.append("    git commit -F msg.txt -- .githooks/pre-commit %s"
                 % " ".join(r for r, _b in missing[:3]))
    return 1, lines


def selftest():
    """A real repo, a real hook, a real commit. The defect is planted, not described."""
    tmp = tempfile.mkdtemp(prefix="__control_hookrefs_")
    repo = os.path.join(tmp, "repo")
    bad = []
    try:
        os.makedirs(os.path.join(repo, HOOK_DIR))
        os.makedirs(os.path.join(repo, "scripts"))
        for a in (["init", "-q", "."], ["config", "user.email", "t@t"],
                  ["config", "user.name", "t"]):
            _git(a, repo)

        # (1) a hook naming a script that is NOT in the index -- but IS on disk, which is
        #     precisely the shape that makes os.path.exists useless here.
        with io.open(os.path.join(repo, HOOK_DIR, "pre-commit"), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write('#!/bin/sh\npython "$R/scripts/absent_from_commit.py" || exit 1\n')
        with io.open(os.path.join(repo, "scripts", "absent_from_commit.py"), "w",
                     encoding="utf-8") as fh:
            fh.write("# on disk, deliberately never added to the index\n")
        _git(["add", "--", HOOK_DIR + "/pre-commit"], repo)
        rc, lines = check(cwd=repo)
        on_disk = os.path.exists(os.path.join(repo, "scripts", "absent_from_commit.py"))
        ok = rc == 1 and any("absent_from_commit.py" in l for l in lines)
        print("  %s  hook names a script that is on disk but NOT in the commit (rc=%d, "
              "file exists on disk=%s)"
              % ("REFUSES" if ok else "PASSED -- CHECK IS DEAD", rc, on_disk))
        if not ok:
            bad.append("a hook referencing a non-indexed script was not refused")

        # (2) same hook, script now staged -- must pass, or it refuses everything
        _git(["add", "--", "scripts/absent_from_commit.py"], repo)
        rc2, lines2 = check(cwd=repo)
        ok2 = rc2 == 0
        print("  %s  same hook once the script is staged too (rc=%d)"
              % ("ALLOWS " if ok2 else "REFUSED -- REFUSES EVERYTHING", rc2))
        if not ok2:
            bad.append("a resolvable hook was refused: %s" % " / ".join(lines2[:3]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if bad:
        print()
        print("REFUSED: %d selftest case(s) wrong:" % len(bad))
        for b in bad:
            print("   %s" % b)
        return 1
    print("\nRefuses a hook whose script the commit omits; allows one that brings it. Both "
          "measured on a real index, with the file present on disk in the refusing case.")
    return 0



def _control_env():
    """os.environ with every GIT_* variable stripped.

    ⛔ THIS IS NOT OPTIONAL AND IT COST A CORRUPTED INDEX TO LEARN. `git commit` exports
    GIT_INDEX_FILE and GIT_DIR to its hooks. A child `git` spawned from inside a hook
    therefore operates on THE COMMIT'S OWN INDEX unless the environment is scrubbed --
    so `git add` in this fixture's throwaway repo wrote a `.githooks/pre-commit` entry
    into the real commit index, naming a blob that exists only in the temp repo's object
    store. The commit then died with `invalid object ... Error building trees`.

    A CONTROL MUST NOT DISTURB THE THING IT MEASURES. This one ran harmlessly for as long
    as it lived behind --selftest and became destructive the moment it was moved onto the
    path that runs inside a hook, which is the only path that matters.
    """
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _fixture_repo(repo, env=None):
    """Build the planted case: a hook naming a script that is ON DISK but NOT in the index.

    This is the exact shape that makes os.path.exists useless here, which is why the
    fixture writes the file to disk and deliberately never adds it.
    """
    os.makedirs(os.path.join(repo, HOOK_DIR), exist_ok=True)
    os.makedirs(os.path.join(repo, "scripts"), exist_ok=True)
    for a in (["init", "-q", "."], ["config", "user.email", "t@t"],
              ["config", "user.name", "t"]):
        _git(a, repo, env)
    with io.open(os.path.join(repo, HOOK_DIR, "pre-commit"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write('#!/bin/sh\npython "$R/scripts/absent_from_commit.py" || exit 1\n')
    with io.open(os.path.join(repo, "scripts", "absent_from_commit.py"), "w",
                 encoding="utf-8") as fh:
        fh.write("# on disk, deliberately never added to the index\n")
    _git(["add", "--", HOOK_DIR + "/pre-commit"], repo, env)


def _control_probe():
    """-> (rc_planted, rc_clean), both produced by check() UNCHANGED on a real index.

    The clean case is the load-bearing half. This file refused EVERYTHING once, because the
    reference extractor kept the shell-variable remnant and every path read as missing; a
    positive-only control passes happily while that is true.
    """
    tmp = tempfile.mkdtemp(prefix="__control_hookrefs_")
    repo = os.path.join(tmp, "repo")
    try:
        env = _control_env()
        _fixture_repo(repo, env)
        rc_planted, _ = check(cwd=repo, env=env)
        _git(["add", "--", "scripts/absent_from_commit.py"], repo, env)
        rc_clean, _ = check(cwd=repo, env=env)
        return rc_planted, rc_clean
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def controls():
    """Run the known answers before any count. Raises ControlFailed if either moves."""
    sys.path.insert(0, _HERE)
    from instrument_controls import require_controls
    rc_planted, rc_clean = _control_probe()
    require_controls(
        "lint_hook_references_resolve",
        ("a hook naming a script on disk but ABSENT from the index must be refused",
         rc_planted, 1),
        ("the same hook once that script is staged must NOT be refused",
         rc_clean == 1, True))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    controls()
    rc, lines = check()
    for l in lines:
        print(l)
    return rc


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
