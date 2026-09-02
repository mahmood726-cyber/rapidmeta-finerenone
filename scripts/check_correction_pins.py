"""Every correction record must describe bytes we can still produce.

A correction says WHAT WAS PUBLISHED and WHAT THE CORRECTED ESTIMATOR GIVES. It
is only checkable if a reader can obtain the bytes it is about, so each record
pins a sha256 and states its own rule:

    "The sha256 pins WHICH bytes this correction is about. If the file changes,
     this correction is about the old bytes and must be re-derived, not amended."

This script never amends a pin. It classifies:

    HOLDS            the pinned bytes are the bytes on this branch
    AHEAD_OF_BRANCH  the pin matches a commit we do not have. The record is
                     correct and this branch is behind -- naming the commit
                     turns an alarming "BROKEN" into an actionable "merge that".
    BROKEN           the artefact changed and no known commit explains it.
                     Re-derive the record; do NOT edit the hash.
    ABSENT           the artefact named does not exist here.
    NO_PIN           the record cannot be checked at all, so it is never clean.

KNOWN_NEGATIVE CONTROLS, measured every run. A checker that has only ever said
one thing has not been shown to discriminate: the pair below plants a pin that
must HOLD and a pin that must NOT, and the run refuses if either misbehaves.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORR = os.path.join(REPO, "corrections")
FILE_RE = re.compile(r"^\s*file\s+(\S+)", re.M)
SHA_RE = re.compile(r"^\s*sha256\s+([0-9a-f]{64})", re.M)
CRLF = bytes([13, 10])
LF = bytes([10])

# Branches whose commits may legitimately hold newer bytes than this one.
KNOWN_LANES = ("paper-studio/manuscript-review",)


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def blob_shas(rel, ref):
    """sha256 of `rel` as it stands at `ref`, or None."""
    try:
        out = subprocess.run(["git", "show", "%s:%s" % (ref, rel)], cwd=REPO,
                             capture_output=True)
        if out.returncode != 0:
            return None
        return hashlib.sha256(out.stdout).hexdigest()
    except Exception:
        return None


def _norm(b):
    return b.replace(CRLF, LF)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def classify(rel, pin):
    """Match on three bases and SAY WHICH ONE matched.

    A sha256 over a text file in a repo with line-ending translation does not
    identify content -- it identifies content PLUS the checkout's newline policy.
    Measured 2026-09-01: the same commit is 1590 bytes here (CRLF) and 1534 in the
    committed blob (LF), so a pin taken from a Windows working copy fails on every
    Linux checkout and on CI. Reporting that as BROKEN would blame the artefact for
    a property of the machine, so the basis is reported instead of hidden.
    """
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return "ABSENT", ""
    wt = open(path, "rb").read()
    if _sha(wt) == pin:
        portable = _sha(_norm(wt)) == pin
        return "HOLDS", ("" if portable else
                         "PIN NOT PORTABLE: matches this working copy's CRLF bytes, "
                         "not the committed blob. A Linux checkout reports it broken.")
    if _sha(_norm(wt)) == pin:
        return "HOLDS", "matched on newline-normalised bytes"
    # ⛔ BOTH REF FORMS, AND COUNT THE CONSULTS. A bare branch name resolves ONLY in a
    # working copy that has that branch checked out; a clone holds it only as
    # origin/<name>. Measured: bare -> 8518b5d6d in the source worktree and FATAL in a
    # clone; origin/ -> 0026c6218 in a clone and FATAL in the worktree. They are not two
    # spellings of one ref -- THEY NAME DIFFERENT TREES, 29 commits apart.
    #
    # The old loop did `continue` on a failed lookup and fell through to BROKEN, so
    # "no lane MATCHED" and "no lane could be CONSULTED" returned the same verdict. They
    # are opposite facts, and which one you got depended on whether you were standing in a
    # clone or the worktree. gate20 therefore reported FAIL in every clone and PASS in
    # exactly one working copy, with nothing in its output saying which you were in.
    # ⛔ TWO DIFFERENT FACTS, AND MY FIRST FIX CONFLATED THEM -- THE SAME MISTAKE IT WAS
    # FIXING, ONE LEVEL DOWN. A `git show <ref>:<path>` fails BOTH when the lane cannot be
    # read AND when the path is simply not in that lane. Counting those together made the
    # detector call a genuinely-broken pin UNDETERMINABLE, and its own known-negative
    # control caught it: "a pin matching nothing -> UNDETERMINABLE, expected BROKEN".
    #
    # So REF RESOLVABILITY is tested separately from PATH PRESENCE.
    #   no lane ref resolves at all      -> UNDETERMINABLE (nothing was consulted)
    #   a ref resolves, bytes do not match -> BROKEN (something was consulted and refused)
    #
    # Both ref forms are tried because a bare branch name resolves ONLY in a working copy
    # that has it checked out, and a clone holds it only as origin/<name>. Measured: bare
    # -> 8518b5d6d in the worktree and FATAL in a clone; origin/ -> 0026c6218 in a clone and
    # FATAL in the worktree. They are not two spellings of one ref: they name DIFFERENT
    # TREES, 29 commits apart.
    readable = 0
    for lane in KNOWN_LANES:
        for ref in (lane, "origin/" + lane):
            if subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"],
                              cwd=REPO, capture_output=True).returncode != 0:
                continue
            readable += 1
            out = subprocess.run(["git", "show", "%s:%s" % (ref, rel)], cwd=REPO,
                                 capture_output=True)
            if out.returncode != 0:
                continue                      # the ref is fine; this PATH is not in it
            blob = out.stdout
            # the lane's WORKING copy is what a pin taken on Windows would hash
            if (_sha(blob) == pin or _sha(_norm(blob)) == pin
                    or _sha(blob.replace(LF, CRLF)) == pin):
                cmt = subprocess.run(["git", "log", "-1", "--format=%h %s", ref, "--", rel],
                                     cwd=REPO, capture_output=True, text=True,
                                     encoding="utf-8", errors="replace").stdout.strip()
                return "AHEAD_OF_BRANCH", "%s carries these bytes: %s" % (ref, cmt[:80])
    if readable == 0:
        return ("UNDETERMINABLE_NO_LANE_REFS",
                "none of the %d known lane(s) resolves here, in either form"
                % len(KNOWN_LANES))
    return "BROKEN", ("%d lane ref(s) read, none produces the pinned bytes on any newline "
                      "basis" % readable)


def controls():
    """A pin that must hold and a pin that must not. Both, or the run is blind."""
    tmp = os.path.join(REPO, "corrections", "__control_probe.tmp")
    ok = True
    lines = []
    with io.open(tmp, "w", encoding="utf-8") as fh:
        fh.write("control payload, not a correction\n")
    good = sha_of(tmp)
    bad = "0" * 64
    rel = os.path.relpath(tmp, REPO).replace("\\", "/")
    v1, _ = classify(rel, good)
    v2, _ = classify(rel, bad)
    os.remove(tmp)
    lines.append("   control: a pin matching the bytes    -> %-16s expected HOLDS" % v1)
    lines.append("   control: a pin matching nothing      -> %-16s expected BROKEN" % v2)
    ok = (v1 == "HOLDS") and (v2 == "BROKEN")
    return ok, lines


def main():
    ok, lines = controls()
    print("CORRECTION PIN CHECK")
    for l in lines:
        print(l)
    if not ok:
        print("\nREFUSED: the checker did not discriminate on its own controls, "
              "so no verdict below is trustworthy and none is printed.")
        return 2
    print("   both controls held.\n")

    if not os.path.isdir(CORR):
        print("no corrections/ directory")
        return 0
    names = sorted(n for n in os.listdir(CORR) if n.endswith(".md"))
    rows, tally = [], {}
    for n in names:
        t = io.open(os.path.join(CORR, n), encoding="utf-8").read()
        mf, ms = FILE_RE.search(t), SHA_RE.search(t)
        if not (mf and ms):
            v, why, rel, pin = "NO_PIN", "no file+sha256 pair in the record", "", ""
        else:
            rel, pin = mf.group(1), ms.group(1)
            v, why = classify(rel, pin)
        tally[v] = tally.get(v, 0) + 1
        rows.append({"record": n, "artefact": rel, "pin": pin, "verdict": v, "note": why})
        print("   %-42s %-16s %s" % (n, v, why))

    print("\n   kinds: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(tally.items())))
    print("   denominator: %d records in corrections/" % len(names))
    with io.open(os.path.join(REPO, "corrections", "PIN_STATUS.json"), "w",
                 encoding="utf-8") as fh:
        json.dump({"checked_utc": "2026-09-01", "kinds": tally, "records": rows,
                   "rule": "a pin is never amended; a changed artefact means the "
                           "record is about the old bytes and must be re-derived"},
                  fh, indent=1)
    # AHEAD_OF_BRANCH is not a pass and not a failure: it is a merge that has not
    # happened. It exits 1 so nothing can render these as verified, and names why.
    hard = tally.get("BROKEN", 0) + tally.get("ABSENT", 0) + tally.get("NO_PIN", 0)
    soft = tally.get("AHEAD_OF_BRANCH", 0)
    if hard:
        print("\n   REFUSE: %d record(s) cannot be verified on any known branch." % hard)
        return 1
    if soft:
        print("\n   HOLD: %d record(s) pin bytes that exist on another lane. They are "
              "correct and unverifiable HERE until that lane merges." % soft)
        return 1
    print("\n   all records verify against this branch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
