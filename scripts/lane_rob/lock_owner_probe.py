# -*- coding: utf-8 -*-
"""Establish whether any live process owns the index.lock, WITHOUT grepping ps output.

WHY NOT ps | grep. A NUL byte anywhere in that output flips grep to binary mode, and it
then prints "Binary file matches" or nothing at all -- and "nothing at all" is
indistinguishable from "no such process". That happened twice in one hour in this exact
safety check. A liveness test whose failure mode is silence is not a liveness test.

TWO INDEPENDENT POSITIVE TESTS instead:

  1 STRUCTURED PROCESS LIST. `tasklist /FO CSV` parsed as CSV, matched on the image name
    field. No text scanning, no shell pipeline, no encoding to misread.
  2 THE FILE ITSELF. On Windows a rename fails while another process holds the file open.
    Renaming the lock aside and back is a POSITIVE test of ownership: if it succeeds,
    nothing holds it. This tests the actual resource rather than a proxy for it.

Both must agree before anything is removed. The probe renames and restores; it never
deletes -- deletion is a separate, explicit step.
"""
import csv
import io
import os
import subprocess
import sys
import time
import hashlib

# GUARDED. A module-level stdout reassignment closes the CALLER's stdout the moment
# this file is imported, and every script here is now importable -- three separate
# checks of this lane's own output died that way before it was fixed at the source.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
LOCK = r"F:\rapidmeta-finerenone\.git\worktrees\rapidmeta-ssot-shell\index.lock"


def processes():
    """Structured process list. Returns [(image, pid), ...]."""
    out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                         capture_output=True).stdout.decode("utf-8", "replace")
    rows = []
    for r in csv.reader(io.StringIO(out)):
        if len(r) >= 2:
            rows.append((r[0], r[1]))
    return rows


def main():
    print("TEST 1 -- structured process list (tasklist /FO CSV, parsed as CSV)")
    procs = processes()
    print("   processes enumerated                  %4d" % len(procs))
    if not procs:
        sys.exit("ABORTED: the process list came back empty, which is not a credible "
                 "answer. A test that cannot see any process cannot report an absence.")
    gits = [(n, p) for n, p in procs if n.lower() in ("git.exe", "git-remote-https.exe")]
    print("   git processes                         %4d" % len(gits))
    # "ANY GIT IS LIVE" IS TOO BLUNT AND WOULD NEVER CLEAR. Other lanes run transient
    # read-only queries constantly -- `git log`, `git show`, `git cat-file` -- and none of
    # them writes an index, so none can own an index.lock. What matters is whether an
    # INDEX-WRITING command is running. Command lines are read structurally from CIM, not
    # scraped, for the same reason the process list is.
    READERS = ("log", "show", "cat-file", "rev-parse", "rev-list", "status", "diff",
               "ls-files", "for-each-ref", "describe", "blame", "grep", "worktree")
    ps1 = ("Get-CimInstance Win32_Process -Filter \"Name='git.exe'\" | "
           "ForEach-Object { $_.ProcessId.ToString() + '|' + $_.CommandLine }")
    raw = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps1],
                         capture_output=True).stdout.decode("utf-8", "replace")
    writers = []
    for line in raw.splitlines():
        if "|" not in line:
            continue
        pid, cmd = line.split("|", 1)
        toks = cmd.split()
        verb = next((t for t in toks[1:] if not t.startswith("-")), "")
        kind = "read-only" if verb in READERS else "MAY WRITE THE INDEX"
        print("      pid %-7s %-20s %s" % (pid.strip(), kind, cmd.strip()[:70]))
        if kind != "read-only":
            writers.append(pid.strip())
    gits = writers

    print("")
    print("TEST 2 -- does anything hold the file? (rename-aside-and-back)")
    if not os.path.exists(LOCK):
        sys.exit("ABORTED: the lock is already gone. Nothing to do.")
    st = os.stat(LOCK)
    digest = hashlib.sha256(open(LOCK, "rb").read()).hexdigest()
    print("   path    %s" % LOCK)
    print("   size    %d bytes" % st.st_size)
    print("   mtime   %s" % time.strftime("%Y-%m-%d %H:%M:%S",
                                          time.localtime(st.st_mtime)))
    print("   sha256  %s" % digest)
    probe = LOCK + ".ownerprobe"
    held = None
    try:
        os.rename(LOCK, probe)
        held = False
        os.rename(probe, LOCK)
    except OSError as ex:
        held = True
        print("   rename REFUSED: %s" % ex)
    print("   file is held open by another process:  %s" % held)
    if os.path.exists(probe) and not os.path.exists(LOCK):
        os.rename(probe, LOCK)
        print("   (probe restored)")

    print("")
    if gits or held:
        print("VERDICT: DO NOT CLEAR. %s"
              % ("a git process is live" if gits else "the file is held open"))
        raise SystemExit(2)
    print("VERDICT: no git process in the structured list, and nothing holds the file.")
    print("Both independent tests agree. Safe to clear as a separate explicit step.")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
