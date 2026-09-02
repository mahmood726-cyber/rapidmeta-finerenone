# -*- coding: utf-8 -*-
# KNOWN_NEGATIVE CONTROL -- EXECUTABLE, AND IT LIVES IN THIS FILE: --selftest.
#   3 positives       a hook / a CI workflow / a shell script naming scripts/target.py
#                     MUST be counted as an invocation
#   3 known negatives a .md, a findings report and an .html naming the SAME path MUST NOT
# This file's headline is "150 checks are named by nothing that runs", and that number rests
# entirely on telling an INVOCATION from a MENTION. If a prose citation counted, dead checks
# would read as wired -- silently, in the flattering direction.
#   python scripts/audit_check_liveness.py --selftest
# A count without a measured precision is not a finding.

"""Every check in this repo, crossed with: IS IT INVOKED - BY WHAT - CAN IT FAIL - LAST FAILED.

WHY THIS FILE EXISTS. Three pieces of machinery in this repo were built, committed, and
never fired: rebuild_guard.py (written for the exact defect that recurred the next day),
four files named *_gate.py with no reachable non-zero exit, and a Docker CI step gated on a
path that never matched, inside a job that went green every time. Each was AVAILABLE. None
was OPERATIVE. The distance between those two words is the whole subject.

THE FOUR QUESTIONS, AND WHY THE ORDER IS THE ORDER:

    CAN IT FAIL      structural, and already answered by lint_gate_can_fail.has_failing_exit,
                     which is IMPORTED here rather than reimplemented. Two implementations of
                     one predicate is two answers to one question.
    IS IT INVOKED    by walking the invocation surfaces and reading what they name. This is
                     the question nobody asks, and it is the one all three precedents failed.
    BY WHAT          a hook, CI, a runner, another script -- recorded, because "it is wired"
                     with no cited citer is the claim, not the evidence.
    WHEN DID IT      unanswerable today, for every check in this repo, because NOTHING here
    LAST FAIL        records that a check ran. That is reported as a gap, never as a zero.

A MENTION IS NOT AN INVOCATION. A check named in a .md is documented, not wired; that
distinction is the entire difference between the three precedents and a live gate, so citers
are typed and prose citers are excluded from the wired count rather than quietly counted.

Read-only. Usage: python scripts/audit_check_liveness.py [--json OUT]
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from lint_gate_can_fail import has_failing_exit   # ONE implementation of the predicate

SKIP_DIRS = (".git", "__pycache__", "node_modules", "vendor", ".mypy_cache")
PY_REF = re.compile(r"[A-Za-z0-9_./\-]+\.py")

# Surfaces that can actually RUN something, typed by how much authority they carry.
KIND_BY_EXT = {".sh": "SHELL", ".bash": "SHELL", ".bat": "SHELL", ".ps1": "SHELL",
               ".yml": "CI", ".yaml": "CI", ".json": "REGISTRY", ".py": "PY",
               ".toml": "REGISTRY", ".cfg": "REGISTRY", ".ini": "REGISTRY"}
PROSE_EXT = (".md", ".txt", ".html", ".rst")


def walk_files():
    """The TRACKED population, from git -- not an os.walk of the checkout.

    The walk version ran twenty minutes without finishing because it descended into
    untracked evidence directories holding tens of thousands of payloads. That is not
    only slow: those files are not part of the repo, so including them would have put
    untracked scratch into a denominator that claims to describe the repo.

    A REACH FIGURE IS NOT A COVERAGE FIGURE. If this listing fails it RAISES rather than
    returning what it managed to collect, because a partial population read as a complete
    one is precisely how an unsearched region comes to look like a clean one.
    """
    out = subprocess.run(["git", "ls-files", "-z"], cwd=_ROOT, capture_output=True)
    if out.returncode != 0:
        raise SystemExit("REFUSED: git ls-files failed (%s). A partial population would be "
                         "reported as a complete one."
                         % out.stderr.decode("utf-8", "replace").strip()[:140])
    for rel in out.stdout.decode("utf-8", "replace").split(chr(0)):
        rel = rel.strip()
        if not rel:
            continue
        if any(p in SKIP_DIRS for p in rel.split("/")):
            continue
        yield rel, os.path.join(_ROOT, rel.replace("/", os.sep))


def citer_kind(rel):
    if rel.startswith(".githooks/"):
        return "HOOK"
    if rel.startswith(".github/workflows/"):
        return "CI"
    ext = os.path.splitext(rel)[1].lower()
    if ext in PROSE_EXT:
        return "PROSE"
    return KIND_BY_EXT.get(ext)


MAX_SURFACE_BYTES = 1_500_000


def read(full, cap=None):
    """(text, state). A file not read is NAMED, never treated as empty.

    The size cap exists because this walk regexes multi-megabyte SSOT stores and took
    over ten minutes. A cap that silently drops files would shrink the denominator in
    exactly the way this repo keeps finding, so an oversized file returns its own STATE
    and is counted and listed under that state rather than passing through as empty.
    """
    try:
        if cap is not None:
            n = os.path.getsize(full)
            if n > cap:
                return None, "OVERSIZE: %d bytes > cap %d" % (n, cap)
        with io.open(full, "rb") as fh:
            return fh.read().decode("utf-8", "replace"), "READ"
    except OSError as exc:
        return None, "UNREADABLE: %s" % exc


DIFF_MARKS = ("diff --cached", "--cached", "diff-filter", "git diff", "HEAD~",
              "--name-only", "staged")
TREE_MARKS = ("os.walk", "ls-files", "ls-tree", "rglob", "glob.glob", "iterdir",
              "PAGE_MAP", "candidates()")


def _ledger_gates():
    """Gates this working copy has actually seen refuse. Empty is a real state, not a zero."""
    out = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=_ROOT,
                         capture_output=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        return set()
    p = os.path.join(out.stdout.strip(), "check_ledger.jsonl")
    if not os.path.exists(p):
        return set()
    seen = set()
    with io.open(p, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("verdict") == "REFUSED":
                seen.add(r.get("gate"))
    return seen


def _last_touched(paths):
    """{path: last commit date}. One `git log` pass over history, not one call per file.

    613 separate `git log -1 -- <path>` calls is 613 process spawns. This walks history once
    and takes the FIRST date each path appears with, which is its most recent change.
    """
    out = subprocess.run(["git", "log", "--format=%x01%cI", "--name-only", "--no-renames"],
                         cwd=_ROOT, capture_output=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        return {}
    # chr(1) -- NOT an escape, and NOT the raw byte this line used to carry. The separator
    # is the 0x01 that --format=%x01 emits two lines above, so the intent is fixed by the
    # adjacent line and needed no guessing. Written as an escape it was eaten by a heredoc
    # and reached the tree as a LITERAL 0x01: invisible in a diff, to grep, and on a page.
    # Caught by scripts/lint_control_chars.py, which this lane landed in the SAME COMMIT as
    # this defect. chr(1) leaves no escape for any shell to eat.
    SEP = chr(1)
    seen, when = {}, None
    for line in out.stdout.splitlines():
        if line.startswith(SEP):
            when = line[1:].strip()[:10]
            continue
        f = line.strip().replace("\\", "/")
        if f and f in paths and f not in seen:
            seen[f] = when
    return seen


def scan_scope(text):
    """DIFF / TREE / BOTH / UNKNOWN -- and the column decides WHERE the check belongs.

    ⛔ MEASURED TONIGHT: the pre-push chain on this repo runs 30-77 MINUTES, one gate at
    178s and another at 486s. A pre-push chain that takes an hour is not a gate, it is a
    QUEUE -- and it makes every WALL indistinguishable from a RACE. Five lanes spent hours
    believing they were losing races to a moving main while one gate was refusing outright.

    ⛔ AND THE COMPANION PROPERTY, WHICH IS WORSE: A TREE-SCANNING GATE FROZEN AGAINST A
    BASELINE PENALISES THE MOST UP-TO-DATE LANE AND EXEMPTS THE MOST STALE ONE. A lane 304
    commits behind sails through because the offending file is not in its tree; a fully
    merged lane is stopped for work it did not do -- and that failure is the hardest of all
    to attribute, because nothing in the lane's own diff explains it.

    So the remedy is one change and this column names it: TREE-scanning gates belong in CI
    on main, where the tree is the thing being judged and one machine pays the cost once.
    DIFF-scoped checks belong in the hook, where they are fast and judge only what the lane
    actually did.
    """
    low = text.lower()
    d = any(m.lower() in low for m in DIFF_MARKS)
    t = any(m.lower() in low for m in TREE_MARKS)
    if d and t:
        return "BOTH"
    if d:
        return "DIFF"
    if t:
        return "TREE"
    return "UNKNOWN"


def selftest():
    """A control for the one judgement this audit makes: INVOCATION versus MENTION.

    ⛔ WHY THIS FILE NEEDED ONE. Its headline is "150 checks are named by nothing that runs",
    and that number rests entirely on telling an invocation apart from a prose mention. If a
    .md citation counted as an invocation, dead checks would read as wired -- silently, in the
    flattering direction. A COUNT WITHOUT A MEASURED PRECISION IS NOT A FINDING, and this
    file was making one of the larger counts in the repo with no control at all.

    The negatives are the load-bearing half: a checker that calls everything an invocation
    would report zero dead checks and look like very good news.
    """
    cases = [
        # (label, filename, text, must_be_invocation)
        ("hook invokes it", ".githooks/pre-commit",
         'python "$R/scripts/target.py" || exit 1', True),
        ("CI invokes it", ".github/workflows/x.yml",
         "run: python scripts/target.py", True),
        ("shell invokes it", "tools/run.sh", "python scripts/target.py", True),
        # KNOWN NEGATIVES -- a mention is not an invocation
        ("prose MENTIONS it", "NOTES.md",
         "we should wire scripts/target.py one day", False),
        ("prose in a report", "FINDINGS-x.md",
         "scripts/target.py was never run", False),
        ("html page names it", "page.html",
         "<p>generated by scripts/target.py</p>", False),
    ]
    bad = []
    print("SELFTEST -- invocation versus mention, the judgement the 150 rests on")
    print()
    for label, fname, text, want in cases:
        kind = citer_kind(fname)
        refs = {os.path.basename(m) for m in PY_REF.findall(text)}
        counted = ("target.py" in refs) and kind is not None and kind != "PROSE"
        ok = counted == want
        print("  %s  %-22s %-26s kind=%-8s counted=%s want=%s"
              % ("OK  " if ok else "WRONG", label, fname[:26], kind, counted, want))
        if not ok:
            bad.append(label)
    if bad:
        print()
        print("REFUSED: %d control case(s) wrong: %s" % (len(bad), ", ".join(bad)))
        print("The invoked/uninvoked split is the whole finding; if this cannot tell a")
        print("mention from an invocation, the count is not a measurement.")
        return 1
    print()
    print("Invocation and mention separated on %d cases, %d of them known negatives."
          % (len(cases), sum(1 for c in cases if not c[3])))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        raise SystemExit(selftest())

    pys, surfaces, unreadable = {}, [], []
    for rel, full in walk_files():
        if rel.endswith(".py"):
            pys[rel] = full
        k = citer_kind(rel)
        if k:
            surfaces.append((rel, full, k))

    # ---- who names whom. Basename, because hooks call by path and CI by relative path.
    cited = {}
    for rel, full, kind in surfaces:
        text, state = read(full, cap=MAX_SURFACE_BYTES)
        if text is None:
            unreadable.append((rel, state))
            continue
        for m in set(PY_REF.findall(text)):
            b = os.path.basename(m.replace("\\", "/"))
            if b == os.path.basename(rel):
                continue                      # a file naming itself is not a citer
            cited.setdefault(b, set()).add((rel, kind))

    rows = []
    for rel in sorted(pys):
        text, state = read(pys[rel])
        if text is None:
            unreadable.append((rel, state))
            continue
        try:
            tree = ast.parse(text, filename=rel)
            can_fail, why = has_failing_exit(tree), "AST"
        except SyntaxError as exc:
            can_fail, why = None, "UNPARSABLE: %s" % str(exc)[:70]
        scope = scan_scope(text)
        citers = sorted(cited.get(os.path.basename(rel), set()))
        runners = [(c, k) for c, k in citers if k != "PROSE"]
        rows.append({"path": rel, "can_fail": can_fail, "why": why, "scope": scope,
                     "invoked_by": [{"citer": c, "kind": k} for c, k in runners],
                     "prose_only": [c for c, k in citers if k == "PROSE"],
                     "last_observed_failure": None})
    return rows, unreadable, a.out


def report(rows, unreadable, out):
    checks = [r for r in rows if r["can_fail"] is True]
    wired = [r for r in checks if r["invoked_by"]]
    dead = [r for r in checks if not r["invoked_by"]]
    prose = [r for r in dead if r["prose_only"]]

    print("CHECK LIVENESS -- every .py walked, never grepped for a name")
    print("=" * 78)
    print("python files enumerated          : %d" % len(rows))
    print("  CAN FAIL (a non-zero exit is reachable) : %d" % len(checks))
    print("  cannot fail / no verdict path           : %d"
          % sum(1 for r in rows if r["can_fail"] is False))
    print("  UNPARSABLE, so NOT ASSESSED             : %d"
          % sum(1 for r in rows if r["can_fail"] is None))
    print()
    print("OF THE %d THAT CAN FAIL:" % len(checks))
    print("  INVOKED by a hook, CI, runner or script : %d" % len(wired))
    print("  NAMED BY NOTHING THAT RUNS              : %d" % len(dead))
    print("     ...of which named only in prose      : %d  (documented, not wired)"
          % len(prose))
    print()
    byk = {}
    for r in wired:
        for iv in r["invoked_by"]:
            byk[iv["kind"]] = byk.get(iv["kind"], 0) + 1
    print("invocations by surface (a check may have several):")
    for k, v in sorted(byk.items(), key=lambda kv: -kv[1]):
        print("   %-10s %4d" % (k, v))

    print()
    # ⛔ THREE NUMBERS, NEVER TWO. "no recorded failure" and "cannot fail" are different
    # facts, and collapsing them is the folding error this repo has corrected six times.
    # A check with no recorded failure is NOT dead -- it is UNOBSERVED, and the whole point
    # of the column is that the two are indistinguishable from outside.
    ledgered = _ledger_gates()
    answerable = [r for r in checks
                  if any(iv["kind"] == "HOOK" for iv in r["invoked_by"])]
    print("WHEN DID EACH LAST FAIL")
    print("   %4d  ANSWERABLE          -- hook-wired, so a refusal is recorded by"
          % len(answerable))
    print("         check_ledger.py at the moment it happens")
    print("   %4d  NO EVIDENCE EITHER WAY -- nothing records that these ever ran"
          % (len(checks) - len(answerable)))
    print("   %4d  total that can fail" % len(checks))
    print()
    print("   The %d are NOT 'dead'. No recorded failure is not the same fact as cannot"
          % (len(checks) - len(answerable)))
    print("   fail, and that indistinguishability IS the finding -- it is exactly how")
    print("   rebuild_guard.py, four unfailable *_gate.py files and a CI step that never")
    print("   ran all went unnoticed while everything around them stayed green.")
    if ledgered:
        print()
        print("   observed in THIS working copy so far: %d gate(s) have actually refused"
              % len(ledgered))
    print()
    print("(historic note, kept because it dates the gap)")
    print("  Nothing here stores that a check ran, so the question cannot be answered for")
    print("  any of the %d. A check that has never been observed to fail is not thereby" % len(checks))
    print("  passing -- it is unobserved, and the two look identical from outside.")

    if unreadable:
        kinds = {}
        for _rel, st in unreadable:
            kinds[st.split(":")[0]] = kinds.get(st.split(":")[0], 0) + 1
        print()
        print("NOT SCANNED FOR CITERS -- counted and named, never dropped (%d):"
              % len(unreadable))
        for k, v in sorted(kinds.items()):
            print("   %-12s %4d" % (k, v))
        for rel, st in unreadable[:8]:
            print("   %-52s %s" % (rel[:52], st[:52]))
        print("   A citer inside one of these would be INVISIBLE here, so any check")
        print("   reported as uninvoked is uninvoked BY THE SURFACES ACTUALLY READ.")

    print()
    print("SCOPE -- and this column decides WHERE a check belongs:")
    hookish = [r for r in checks
               if any(iv["kind"] in ("HOOK", "SHELL") for iv in r["invoked_by"])]
    bys = {}
    for r in hookish:
        bys[r.get("scope", "UNKNOWN")] = bys.get(r.get("scope", "UNKNOWN"), 0) + 1
    for k, v in sorted(bys.items(), key=lambda kv: -kv[1]):
        print("   hook/shell-wired, %-8s %3d" % (k, v))
    misplaced = [r for r in hookish if r.get("scope") in ("TREE", "BOTH")]
    if misplaced:
        print()
        print("TREE-SCANNING AND WIRED INTO A HOOK (%d) -- these penalise the most up-to-date"
              % len(misplaced))
        print("lane and exempt the most stale one, and they are what makes the chain an hour:")
        for r in sorted(misplaced, key=lambda r: r["path"])[:20]:
            print("   %-58s %s" % (r["path"][:58], r.get("scope")))
        print("   A tree-scanning gate judges the TREE, which is main's property, not this")
        print("   lane's diff. It belongs in CI on main where one machine pays the cost once.")

    # ⭐ WHERE THE NEXT DEAD CHECK IS HIDING. Ranked by BLAST RADIUS then AGE, because a
    # check nothing has ever observed is most dangerous when it judges the WHOLE TREE (so a
    # silent failure is repo-wide) and has sat untouched longest (so nobody would notice it
    # stopped mattering). Neither number is a verdict -- both are places to look.
    unobs = [r for r in checks
             if not any(iv["kind"] == "HOOK" for iv in r["invoked_by"])]
    dates = _last_touched({r["path"] for r in unobs})
    def _key(r):
        wide = 0 if r.get("scope") in ("TREE", "BOTH") else 1
        return (wide, dates.get(r["path"], "0000-00-00"))
    print()
    print("THE 613, RANKED -- widest blast radius first, then longest untouched.")
    print("A check nothing has observed is most dangerous when it judges the whole tree and")
    print("has sat longest. This is where to look, never a verdict:")
    print("   %-56s %-6s %-10s %s" % ("check", "scope", "last seen", "invoked by"))
    for r in sorted(unobs, key=_key)[:20]:
        by = ",".join(sorted({i["kind"] for i in r["invoked_by"]})) or "NOTHING"
        print("   %-56s %-6s %-10s %s"
              % (r["path"][:56], r.get("scope", "?"), dates.get(r["path"], "unknown"), by))

    print()
    print("HOOK-WIRED CHECKS (the only ones that block a commit):")
    for r in sorted(wired, key=lambda r: r["path"]):
        if any(iv["kind"] == "HOOK" for iv in r["invoked_by"]):
            print("   %s" % r["path"])

    if out:
        with io.open(os.path.join(_ROOT, out), "w", encoding="utf-8") as fh:
            json.dump({"_what": "every .py, crossed with can-fail and who invokes it",
                       "rows": rows}, fh, indent=1, sort_keys=True)
        print()
        print("written: %s" % out)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    _rows, _unread, _out = main(sys.argv[1:])
    sys.exit(report(_rows, _unread, _out))
