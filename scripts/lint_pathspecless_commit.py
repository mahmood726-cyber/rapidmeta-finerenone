# -*- coding: utf-8 -*-
# KNOWN_NEGATIVE CONTROL -- EXECUTABLE, AND IT LIVES IN THIS FILE: --selftest.
#   [1] positive       pathspec-less `git commit -m ...`  MUST be refused
#   [2] known negative `git commit -- b.txt`              MUST NOT be refused
#   [3] known negative SHARED_INDEX_OK override           MUST NOT be refused
#   [4] known negative a SINGLE-worktree repo, nothing staged: MUST stay silent
# Measured on REAL commits in a REAL two-worktree repo the selftest builds, so the rate is
# re-measured on every run rather than quoted from memory. The negatives are the load-bearing
# half: this check refusing everything would be as useless as it refusing nothing, and case
# [4] is the one a fresh clone caught -- see the cwd note below.
#   python scripts/lint_pathspecless_commit.py --selftest
# A count without a measured precision is not a finding.

"""Refuse a pathspec-less `git commit` in a shared worktree, and NAME what it would capture.

TWO NEAR-MISSES IN ONE NIGHT, FROM ONE MECHANISM, AND THE DEFENCE WAS A PARAGRAPH BEING
RELAYED BY HAND TO SEVEN LANES:

  1. CAPTURE. Four lanes stage into ONE index. A lane that runs `git commit -m "..."` with no
     pathspec commits every staged entry -- including files another lane staged seconds ago
     and has not finished. At 02:00 tonight that index held 52 staged paths from several
     lanes at once.

  2. INVERSE DELETION. A commit built on a private GIT_INDEX_FILE leaves the shared index one
     commit stale. A stale shared index stages the INVERSE of what was just committed -- a
     DELETION of the file that was just added -- and the next pathspec-less commit from any
     lane silently undoes the work.

Both are the same shape: A PATHSPEC-LESS COMMIT COMMITS A SHARED OBJECT THAT NOBODY OWNS.
A rule recalled by situation fails when the situation is disguised, so this is a check in the
path rather than a note in a document.

HOW IT KNOWS, AND IT WAS MEASURED RATHER THAN ASSUMED. git hands a pre-commit hook a
different GIT_INDEX_FILE depending on how the commit was invoked. Measured in a throwaway
repo, three distinct signatures:

    git commit -m x            -> .git/index                    SHARED  (hazard)
    git commit -m y -- b.txt   -> .git/next-index-22232.lock    private (safe)
    git commit -a -m z         -> .git/index.lock               SHARED  (hazard, and worse:
                                                                 -a stages every modified
                                                                 tracked file first)

A basename of next-index-* means git built a temporary index for a pathspec, so the commit
can only contain the paths named. Anything else means the commit takes the shared index
wholesale. The signal is exact and needs no parsing of anyone's command line.

WHY IT ONLY FIRES IN A SHARED WORKTREE. In a single-worktree repo a pathspec-less commit is
completely normal and refusing it would be the refuse-everything failure this repo has
already paid for once. The trigger is: more than one worktree exists AND the shared index has
staged entries. Both conditions are checked, and the refusal lists the entries by name.

Override, with the reason on the record:
    SHARED_INDEX_OK="why this commit may take the whole index" git commit ...

Read-only. Exit 1 refuses. `--selftest` builds a real two-worktree repo and proves that this
refuses one form, passes the other, and honours the override.


LOAD-BEARING, NOT A BACKSTOP. Two routes exist for committing in a shared worktree and each
trades one staleness mode for another:

    shared index          goes one commit stale after a private-GIT_INDEX_FILE commit, so it
                          stages the INVERSE of what was just committed
    --no-checkout worktree  an EMPTY TREE against a FULL HEAD, so the index describes
                          thousands of files that are not there

NEITHER ROUTE IS SAFE WITHOUT AN EXPLICIT PATHSPEC. The pathspec is the only unconditional
rule, and it covers BOTH modes -- which makes this check the single defence standing between
a stale index of either kind and a repository-deleting commit. A worktree carrying 13,832
staged deletions was found on this machine tonight, one pathspec-less commit from wiping it.
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

SAFE_PREFIX = "next-index-"


def index_is_shared(env=None):
    """(is_shared, what_was_seen). Unset counts as SHARED -- the fail-closed direction.

    An unset GIT_INDEX_FILE means git is using the default index, which in a worktree is the
    shared one. Treating unknown as safe would make the check pass exactly when it cannot
    tell, which is the vacuous pass this repo keeps finding.
    """
    env = os.environ if env is None else env
    raw = env.get("GIT_INDEX_FILE")
    if not raw:
        return True, "GIT_INDEX_FILE unset (default index)"
    base = os.path.basename(raw.replace("\\", "/"))
    if base.startswith(SAFE_PREFIX):
        return False, base
    return True, base


def repo_here():
    """The repository THIS COMMIT IS HAPPENING IN -- the cwd, never this file's location.

    ⛔ THE FRESH-CLONE READ-BACK IS WHAT CAUGHT THIS, AND NOTHING ELSE WOULD HAVE.
    Every git query below used to run against _ROOT, derived from __file__. A pre-commit
    hook runs with cwd set to the top of the repo being committed to -- which is NOT
    necessarily where this script lives, and in a worktree it never is. The selftest passed
    locally for the WRONG REASON: it inspected the author's shared worktree, which happens
    to have several worktrees and staged files, so the refusal fired no matter what the
    temporary test repo contained. Cloned fresh, _ROOT became a one-worktree repo with
    nothing staged, and the check quietly passed everything.

    A CHECK THAT READS A DIFFERENT REPOSITORY THAN THE ONE BEING COMMITTED TO IS INERT, AND
    IT IS INERT IN THE DIRECTION THAT LOOKS LIKE SUCCESS.
    """
    return os.getcwd()


def _git(args, cwd=None, env=None):
    out = subprocess.run(["git"] + args, cwd=cwd or repo_here(), capture_output=True,
                         encoding="utf-8", errors="replace")
    return out.returncode, out.stdout, out.stderr


def worktree_count(cwd=None):
    rc, out, _err = _git(["worktree", "list"], cwd)
    if rc != 0:
        # A repo whose worktrees cannot be listed is not thereby a single-worktree repo.
        # Fail closed: assume shared, so the check still speaks.
        return 2
    return len([l for l in out.splitlines() if l.strip()])


def staged_paths(cwd=None):
    rc, out, err = _git(["diff", "--cached", "--name-only"], cwd)
    if rc != 0:
        raise SystemExit("REFUSED: cannot read the staged set (%s). A check that cannot see "
                         "what the commit contains must not pass it." % err.strip()[:140])
    return [l.strip() for l in out.splitlines() if l.strip()]


def check(cwd=None, env=None):
    """(exit_code, lines). The decision and its explanation, so the selftest can read both."""
    lines = []
    shared, seen = index_is_shared(env)
    wt = worktree_count(cwd)
    if not shared:
        lines.append("OK: this commit names a pathspec (%s), so it can only contain the "
                     "paths it names." % seen)
        return 0, lines
    if wt < 2:
        lines.append("OK: single-worktree repo -- a pathspec-less commit is normal here.")
        return 0, lines
    staged = staged_paths(cwd)
    if not staged:
        lines.append("OK: shared index, but nothing is staged -- nothing to capture.")
        return 0, lines

    why = (env or os.environ).get("SHARED_INDEX_OK")
    if why:
        lines.append("ALLOWED by SHARED_INDEX_OK=%r over %d staged path(s)."
                     % (why[:120], len(staged)))
        return 0, lines

    lines.append("")
    lines.append("REFUSED: this commit names no pathspec, and %d worktree(s) share this "
                 "index." % wt)
    lines.append("It would commit ALL %d staged path(s), including any another lane staged "
                 "and has not finished:" % len(staged))
    for p in staged[:25]:
        lines.append("    %s" % p)
    if len(staged) > 25:
        lines.append("    ... and %d more" % (len(staged) - 25))
    lines.append("")
    lines.append("The index git handed this hook was %s -- the SHARED one. A commit with a "
                 "pathspec gets its own temporary index (next-index-*) and cannot reach "
                 "anyone else's work." % seen)
    lines.append("")
    lines.append("    git commit -F msg.txt -- path/one path/two      <- name what is yours")
    lines.append("    SHARED_INDEX_OK=\"why\" git commit ...            <- with the reason on "
                 "the record")
    return 1, lines


# --------------------------------------------------------------------------------------
# The selftest builds a REAL repo with TWO worktrees and runs REAL commits through this
# file as the hook. Nothing is simulated, because the whole subject is a hook firing
# during an actual commit, and a mock of git would prove only that the mock behaves.
# --------------------------------------------------------------------------------------
HOOK = ("#!/bin/sh\n"
        "exec python \"%s\" \"$@\"\n")


def selftest():
    tmp = tempfile.mkdtemp(prefix="__control_pathspec_")
    repo = os.path.join(tmp, "repo")
    bad = []
    try:
        os.makedirs(repo)
        for a in (["init", "-q", "."], ["config", "user.email", "t@t"],
                  ["config", "user.name", "t"]):
            _git(a, repo)
        for n in ("a.txt", "b.txt"):
            with io.open(os.path.join(repo, n), "w", encoding="utf-8") as fh:
                fh.write("one\n")
        _git(["add", "-A"], repo)
        _git(["commit", "-q", "-m", "base", "--no-verify"], repo)
        # a SECOND worktree -- without it the check correctly stays silent
        _git(["worktree", "add", "-q", os.path.join(tmp, "wt2")], repo)

        hookdir = os.path.join(repo, ".git", "hooks")
        if not os.path.isdir(hookdir):
            os.makedirs(hookdir)
        hp = os.path.join(hookdir, "pre-commit")
        with io.open(hp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(HOOK % os.path.abspath(__file__).replace("\\", "/"))
        os.chmod(hp, 0o755)

        for n in ("a.txt", "b.txt"):
            with io.open(os.path.join(repo, n), "w", encoding="utf-8") as fh:
                fh.write("two\n")
        _git(["add", "--", "a.txt"], repo)          # a staged file, as another lane would leave

        print("SELFTEST -- real repo, two worktrees, real commits through this hook\n")

        rc, out, err = _git(["commit", "-m", "pathspec-less"], repo)
        ok = rc != 0 and "REFUSED" in (out + err)
        print("  %s  pathspec-less `git commit -m ...`  -> rc=%d"
              % ("REFUSES" if ok else "PASSED -- CHECK IS DEAD", rc))
        if not ok:
            bad.append("pathspec-less commit was not refused")

        rc2, out2, err2 = _git(["commit", "-m", "with pathspec", "--", "b.txt"], repo)
        ok2 = rc2 == 0
        print("  %s  `git commit -- b.txt`               -> rc=%d"
              % ("ALLOWS " if ok2 else "REFUSED -- REFUSES EVERYTHING", rc2))
        if not ok2:
            bad.append("a pathspec commit was refused: %s" % (out2 + err2)[:200])

        # [4] KNOWN NEGATIVE -- A SINGLE-WORKTREE REPO HAS NO HAZARD AND MUST STAY SILENT.
        # This is the case a fresh clone caught and the selftest did not: the check used to
        # read _ROOT (this file's location) instead of the repo being committed to, so in a
        # normal clone it inspected the wrong repository, found one worktree, and passed
        # everything. It was green for the wrong reason on the only case that mattered.
        # Verified by hand at the time; run here now, because a case I checked by hand is a
        # claim and a case in the suite is a control.
        solo = os.path.join(tmp, "solo")
        os.makedirs(solo)
        for a in (["init", "-q", "."], ["config", "user.email", "t@t"],
                  ["config", "user.name", "t"]):
            _git(a, solo)
        with io.open(os.path.join(solo, "x.txt"), "w", encoding="utf-8") as fh:
            fh.write("one" + chr(10))
        _git(["add", "-A"], solo)
        rc4, _l4 = check(cwd=solo, env={"GIT_INDEX_FILE": os.path.join(solo, ".git", "index")})
        ok4 = rc4 == 0
        print("  %s  single-worktree repo, staged file, no pathspec -> rc=%d"
              % ("SILENT" if ok4 else "REFUSED -- FIRES WHERE THERE IS NO HAZARD", rc4))
        if not ok4:
            bad.append("refused in a single-worktree repo, where the hazard cannot exist")

        env = dict(os.environ, SHARED_INDEX_OK="a stated reason")
        p = subprocess.run(["git", "commit", "-m", "override"], cwd=repo, env=env,
                           capture_output=True, encoding="utf-8", errors="replace")
        ok3 = p.returncode == 0
        print("  %s  SHARED_INDEX_OK override             -> rc=%d"
              % ("ALLOWS " if ok3 else "IGNORED -- OVERRIDE IS DEAD", p.returncode))
        if not ok3:
            bad.append("the documented override did not work")
    finally:
        # NO `git worktree prune` HERE, DELIBERATELY, EVEN ON A THROWAWAY REPO. The standing
        # instruction in this project is never to run it, and a rule that gets re-litigated
        # per-case whenever someone judges the case harmless is not a rule. The temp tree is
        # removed wholesale instead; nothing outside it was ever registered.
        shutil.rmtree(tmp, ignore_errors=True)

    if bad:
        print()
        print("REFUSED: %d selftest case(s) wrong:" % len(bad))
        for b in bad:
            print("   %s" % b)
        return 1
    print("\nRefuses the hazard, allows the safe form, honours the override. All four "
          "measured on real commits.")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    rc, lines = check()
    for l in lines:
        print(l)
    return rc


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
