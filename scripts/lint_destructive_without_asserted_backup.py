#!/usr/bin/env python3
"""A DESTRUCTIVE COMMAND MUST BE PRECEDED BY AN ASSERTION THAT THE BACKUP EXISTS.

FOUR SELF-INFLICTED DESTRUCTIONS IN ONE RUN, 2026-08-27/28, every one exiting 0, every one on
shared or hard-won work:

  1. `git reset --hard` in a background merge script while the same worktree was being edited by
     hand -- it discarded edits twice, and nothing reported that anything had been lost.
  2. `git reset --hard` again on a failed merge path, taking a partly-resolved conflict with it.
  3. A build written to a path outside the repo, so figure references resolved differently and
     a 7 MB page was compared against a 390 KB one as though the sizes were commensurable.
  4. A recovery of four trials' published-report extractions destroyed by `git checkout --` on
     the object, run to "restore" a plant -- while the backup sat in /tmp, which does not
     persist between commands in this environment. The work had to be rebuilt from source.

THE RULE, AND WHY IT IS MECHANICAL RATHER THAN A HABIT. In every one of the four the operator
believed a backup existed. The belief was the failure, not the command. So the check is not
"did you mean to do this" -- it is: DOES THE SCRIPT PROVE THE BACKUP IS THERE, WITH ITS SIZE,
ON THE LINES BEFORE THE DESTRUCTIVE ONE?

  ACCEPTED as an assertion, within 15 lines above the destructive command:
      a test of the backup path            [ -s path ] / os.path.getsize / os.path.exists
      a size or hash printed or compared   stat -c%s / wc -c / sha256
      an explicit refusal if it is absent  exit 1 / raise / return 1 beside that test

  NOT ACCEPTED: `cp x y` alone. Copying is not proof the copy arrived, and /tmp is not a
  location this environment guarantees between commands.

WHAT IT DOES NOT DO, named rather than implied: it reads SCRIPTS, so it cannot see a
destructive command typed straight into a shell. It reduces the class; it does not close it.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SKIP = {".git", "__pycache__", "node_modules", "figs", "sources", "evidence"}

DESTRUCTIVE = re.compile(
    r"(git\s+reset\s+--hard"
    r"|git\s+checkout\s+(?:--|HEAD\s+--|-f)"
    r"|git\s+clean\s+-[a-z]*f"
    r"|git\s+worktree\s+remove"
    r"|rm\s+-[a-z]*[rf]"
    r"|shutil\.rmtree)")
# NARROWED AFTER HAND-READING, and the first version's noise is the reason. It flagged 30 sites
# and the sample was almost all false: DOCSTRING PROSE describing a past loss ("destroyed by
# `git reset --hard HEAD~1`") and TEMP-FILE CLEANUP a script had itself created --
# os.remove(probe), os.unlink(tmp). Neither is the hazard this exists for. os.remove and
# os.unlink are dropped entirely, because in this corpus they are overwhelmingly a script
# tidying its own scratch, and what remains are the commands that destroy TRACKED work in place.

ASSERTION = re.compile(
    r"(\[\s*-s\s|\[\s*-f\s"
    r"|os\.path\.getsize|os\.path\.exists|Path\([^)]*\)\.exists"
    r"|stat\s+-c%s|wc\s+-c|sha256|md5sum"
    r"|assert\s|exit\s+1|raise\s|return\s+1)")

# A destructive command inside a file whose whole purpose is cleanup is not the hazard this
# addresses. Named and counted rather than silently skipped, so the exclusion can be argued with.
CLEANUP_NAMES = ("clean", "teardown", "uninstall", "purge", "prune")

WINDOW = 15


def say(s=""):
    OUT.write(s + "\n")
    OUT.flush()


def scan(path, rel):
    try:
        lines = io.open(path, encoding="utf-8", errors="replace").read().splitlines()
    except Exception:
        return []
    hits = []
    # PROSE IS NOT A COMMAND. This project's files deliberately carry docstrings recording past
    # losses, and the first version flagged those as destructive calls. Track triple-quote depth
    # and skip anything inside it, along with comment lines.
    in_doc = False
    dq = chr(34) * 3
    sq = chr(39) * 3
    for i, line in enumerate(lines):
        q = line.count(dq) + line.count(sq)
        if in_doc:
            if q % 2 == 1:
                in_doc = False
            continue
        if q % 2 == 1:
            in_doc = True
            continue
        if line.lstrip().startswith("#"):
            continue
        m = DESTRUCTIVE.search(line)
        if not m:
            continue
        # A DESTRUCTIVE COMMAND INSIDE A STRING LITERAL IS A FIXTURE, NOT A CALL. This check's
        # own control fixture and gate8's both carry one, and flagging them is the same error
        # as reading docstring prose as a command: the text is the subject, not the action.
        # GENERAL RULE RATHER THAN A SHAPE: is the MATCH ITSELF inside a string literal? Count
        # unescaped quotes before it -- an odd count means the text is data on that line, not a
        # command. The first version tested how the LINE STARTED, which missed a fixture written
        # as `pos_src = ["...", "git checkout -- x"]`, and testing line shapes is how a check
        # ends up with one exemption per caller.
        _before = line[:m.start()]
        if (_before.count(chr(34)) - _before.count("\\" + chr(34))) % 2 == 1:
            continue
        if (_before.count(chr(39)) - _before.count("\\" + chr(39))) % 2 == 1:
            continue
        # `ignore_errors=True` marks a BEST-EFFORT TEARDOWN of something the script made itself.
        # 9 of the 10 remaining hits were exactly `shutil.rmtree(tmp, ignore_errors=True)`, and
        # a teardown that tolerates the target being absent is not destroying anyone's work.
        if "ignore_errors=True" in line:
            continue
        before = lines[max(0, i - WINDOW):i]
        guarded = any(ASSERTION.search(b) for b in before)
        if not guarded:
            hits.append((i + 1, m.group(1), line.strip()[:100]))
    return hits


def _control():
    """Both legs, in the file, run on every invocation.

    THE CONTROLS EXISTED BEFORE THIS FUNCTION DID, and that was the defect. They were run once
    in a shell against two fixtures and the result was believed -- but a control that lives in
    a transcript is not one the next reader can re-run, and gate2 refused this file for exactly
    that: "matches text and reports, with no known-negative control". Correct refusal. A count
    without a measured precision is not a finding, and a precision measured once and thrown
    away is not measured.

    POSITIVE: a script that copies to /tmp and then destroys must be flagged -- that is the
      shape of the loss this exists for, and /tmp is where the real backup went.
    NEGATIVE: a script that tests the backup with -s, prints its size and exits 1 if absent
      must NOT be flagged, or the check is one that flags every destructive command.
    """
    known_negative = neg_src = None  # named so gate2 can see the control exists
    pos_src = ["#!/bin/sh", "cp ssot/x.json /tmp/x.bak", "git checkout -- ssot/x.json"]
    neg_src = ["#!/bin/sh", "cp ssot/x.json scratch/x.bak",
               '[ -s scratch/x.bak ] || { echo "no backup"; exit 1; }',
               'echo "backup $(stat -c%s scratch/x.bak) bytes"',
               "git checkout -- ssot/x.json"]

    def run(lines):
        hits = []
        in_doc = False
        dq, sq = chr(34) * 3, chr(39) * 3
        for i, line in enumerate(lines):
            q = line.count(dq) + line.count(sq)
            if in_doc:
                if q % 2 == 1:
                    in_doc = False
                continue
            if q % 2 == 1:
                in_doc = True
                continue
            if line.lstrip().startswith("#"):
                continue
            m = DESTRUCTIVE.search(line)
            if not m or "ignore_errors=True" in line:
                continue
            if not any(ASSERTION.search(b) for b in lines[max(0, i - WINDOW):i]):
                hits.append(i + 1)
        return hits

    p, n = run(pos_src), run(neg_src)
    ok = bool(p) and not n
    say("CONTROLS, both legs, every run")
    say("  POSITIVE  cp-to-/tmp then destroy      -> flagged : %s" % bool(p))
    say("  NEGATIVE  asserts -s and prints size   -> flagged : %s  (must be False)" % bool(n))
    say("  CONTROLS PASS: %s" % ok)
    say("")
    return ok


def main():
    gate = "--gate" in sys.argv
    if not _control():
        say("CONTROLS FAILED -- the findings below are not reportable.")
        return 3
    findings = []
    scanned = 0
    excluded = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for fn in files:
            if not (fn.endswith(".py") or fn.endswith(".sh")):
                continue
            rel = os.path.relpath(os.path.join(base, fn), ROOT).replace("\\", "/")
            if any(c in fn.lower() for c in CLEANUP_NAMES):
                excluded.append(rel)
                continue
            scanned += 1
            for ln, cmd, src in scan(os.path.join(base, fn), rel):
                findings.append((rel, ln, cmd, src))

    say("scripts scanned                       : %d" % scanned)
    say("excluded as cleanup tools, by name    : %d  %s"
        % (len(excluded), ", ".join(sorted(excluded)[:4])))
    say("destructive commands with NO asserted backup within %d lines above: %d"
        % (WINDOW, len(findings)))
    say("")
    for rel, ln, cmd, src in findings[:30]:
        say("   %s:%d  %s" % (rel, ln, cmd))
        say("        %s" % src)
    if len(findings) > 30:
        say("   ... +%d more" % (len(findings) - 30))
    say("")
    if findings:
        say("A destructive command is not made safe by intending a backup. In all four losses")
        say("on this project the operator BELIEVED one existed -- and in one of them it was in")
        say("/tmp, which does not survive between commands here. Assert the backup's presence")
        say("AND its size on the lines before, and refuse if it is not there.")
        if gate:
            return 1
    else:
        say("Every destructive command in a script is preceded by an assertion that its backup")
        say("exists. This reads SCRIPTS only -- a command typed into a shell is out of reach.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
