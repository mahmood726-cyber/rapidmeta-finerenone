# -*- coding: utf-8 -*-
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


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="out")
    a = ap.parse_args(argv)

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
        citers = sorted(cited.get(os.path.basename(rel), set()))
        runners = [(c, k) for c, k in citers if k != "PROSE"]
        rows.append({"path": rel, "can_fail": can_fail, "why": why,
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
    print("WHEN DID EACH LAST FAIL: UNRECORDED, FOR EVERY CHECK IN THIS REPO.")
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
