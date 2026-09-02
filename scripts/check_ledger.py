# -*- coding: utf-8 -*-
# no-control: THIS FILE MATCHES NO TEXT AND PRODUCES NO FINDINGS, so there is nothing whose
# precision could be measured. It appends one row per refusal and reads those rows back; the
# only judgement it makes is `verdict == "REFUSED"` on a field it wrote itself. There is no
# population to sample, no positive to reach and no negative to falsely accuse.
#
# ⚠️ AND THIS REASON IS CHECKABLE BY A HUMAN AND UNVERIFIABLE BY THE GATE. gate2 accepts the
# marker above whether or not the sentence is true -- a marker satisfiable by assertion is a
# password, not a requirement. It is written here because it IS true, and flagged as the
# weaker kind of assurance so the next reader knows which they are holding. Where a control
# was constructible in this lane it was BUILT and made executable instead; see
# lint_pathspecless_commit.py, lint_hook_references_resolve.py and audit_check_liveness.py.

"""Record that a check RAN and what it returned, so `when did it last fail` has an answer.

THE COLUMN THAT COULD NOT BE FILLED. The check inventory crosses every check with: is it
invoked, by what, can it fail, and WHEN DID IT LAST FAIL. The first three were measurable
from the tree. The fourth was UNRECORDED FOR ALL 664 CHECKS, because nothing in this
repository stored that a check had ever run.

    A CHECK THAT HAS NEVER BEEN OBSERVED TO FAIL IS NOT THEREBY PASSING. IT IS UNOBSERVED,
    AND FROM OUTSIDE THE TWO ARE IDENTICAL.

That is not a gap in the inventory, it is the reason the three dead-machinery precedents went
unnoticed: rebuild_guard.py, four *_gate.py files with no reachable non-zero exit, and a CI
step gated on a path that never matched inside a job that went green every time. Each was
believed to work because nothing had ever said otherwise.

WHERE THE RECORD IS TAKEN, AND WHY THAT EXACT PLACE. `_refuse` in .githooks/pre-commit is
already handed the offending gate's path on every refusal -- it exists to print it. One
additive line there makes every hook-wired refusal permanent, at the only point in the system
that already knows both the gate and the verdict. Wrapping each check individually would have
meant editing fifty invocation lines belonging to other lanes.

WHAT THIS DELIBERATELY DOES NOT CLAIM:
  - It records REFUSALS and CHAIN-PASSES, not per-check passes. A chain pass means every
    check in the chain returned zero; it does not distinguish a check that examined a
    thousand files from one that examined none.
  - It covers HOOK-WIRED checks only -- 51 of 664. For the other 613 the column stays empty,
    and that emptiness is the finding rather than a defect in this file.
  - The ledger is PER CLONE and untracked (in $GIT_DIR). It is evidence about this working
    copy, never about the project. A fresh clone starts empty, and an empty ledger means
    NOTHING HAS BEEN OBSERVED HERE -- it does not mean nothing has failed.

Usage:
    python scripts/check_ledger.py record <gate-path> <REFUSED|PASSED>
    python scripts/check_ledger.py report
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import subprocess
import sys

LEDGER = "check_ledger.jsonl"


def git_dir():
    out = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True,
                         encoding="utf-8", errors="replace")
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def ledger_path():
    d = git_dir()
    return os.path.join(d, LEDGER) if d else None


def record(gate, verdict):
    """Append one line. NEVER raises: a ledger failure must not block a commit.

    ⛔ THE ONE PLACE FAIL-CLOSED IS WRONG. Everything else in this repo fails closed, and
    this file is the exception on purpose: it is an observer, not a gate. If recording threw,
    a full disk or a read-only .git would refuse commits for every lane -- the bookkeeping
    would have become the outage. Its failure mode is a MISSING ROW, which reads as "not
    observed", which is exactly what it would then be.
    """
    p = ledger_path()
    if not p:
        return 0
    row = {"utc": datetime.datetime.now(datetime.timezone.utc)
                   .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "gate": gate, "verdict": verdict}
    try:
        with io.open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    except OSError:
        pass
    return 0


def read_rows():
    p = ledger_path()
    if not p or not os.path.exists(p):
        return [], p
    rows = []
    with io.open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                # A corrupt line is COUNTED, never skipped -- a ledger that silently drops
                # what it cannot parse is the defect this project keeps finding.
                rows.append({"utc": "?", "gate": "<UNPARSABLE LINE>", "verdict": "?"})
    return rows, p


def report():
    rows, p = read_rows()
    print("CHECK LEDGER: %s" % (p or "no git dir"))
    if not rows:
        print()
        print("EMPTY. Nothing has been OBSERVED in this working copy -- which is not the")
        print("same as nothing having failed. The ledger starts empty in every fresh clone,")
        print("and it fills only from the moment it is wired.")
        return 0
    last_fail, last_pass, counts = {}, None, {}
    for r in rows:
        g, v, t = r.get("gate", "?"), r.get("verdict", "?"), r.get("utc", "?")
        counts[g] = counts.get(g, 0) + 1
        if v == "REFUSED" and (g not in last_fail or t > last_fail[g]):
            last_fail[g] = t
        if v == "PASSED" and (last_pass is None or t > last_pass):
            last_pass = t
    print("rows: %d   distinct gates seen: %d" % (len(rows), len(counts)))
    print("last full chain pass: %s" % (last_pass or "never recorded"))
    print()
    print("WHEN DID IT LAST FAIL -- only gates that have ever refused appear here:")
    for g, t in sorted(last_fail.items(), key=lambda kv: kv[1], reverse=True):
        print("   %-58s %s  (%d record(s))" % (g[:58], t, counts.get(g, 0)))
    silent = sorted(g for g in counts if g not in last_fail)
    if silent:
        print()
        print("SEEN BUT NEVER REFUSED (%d):" % len(silent))
        for g in silent[:15]:
            print("   %s" % g[:70])
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("record")
    r.add_argument("gate")
    r.add_argument("verdict")
    sub.add_parser("report")
    a = ap.parse_args(argv)
    if a.cmd == "record":
        return record(a.gate, a.verdict)
    return report()


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
