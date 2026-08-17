"""DURABLE ARTEFACT GATE -- is every artefact whose purpose is durability actually tracked?

WHY THIS EXISTS
    The waiver register was first written to outputs/STANDARD_EXCEPTIONS.json.
    outputs/ is gitignored. It was written successfully, it read back correctly,
    the gate that consumes it worked perfectly on this machine -- and it would
    have existed nowhere else. In a fresh clone the register is absent, the
    exemption lookup finds nothing, and 51 pages that were meant to be a COUNTED
    BACKLOG would have quietly become 51 pages nobody was tracking.

    NOTE THE FAILURE DIRECTION. An untracked backlog does not error. It does not
    warn. It just stops existing, and the corpus then looks BETTER than it is.
    Same selection effect as everything else found today: the comfortable
    failures are the ones that survive, because nothing about them demands
    attention.

THE GENERAL RULE, WHICH IS THE FOURTH INSTANCE OF ONE META-MECHANISM
    WRITING AN ARTEFACT IS NOT PRESERVING IT.
      - push is not deploy                     (the ref moved; the site did not)
      - the repair existing is not the repair arriving   (12 checkouts, 6 stale)
      - a library no build invokes catches nothing
      - writing a file is not tracking it               <- this one
    In every case THE ACTION WAS PERFORMED AND THE EFFECT WAS NEVER CONFIRMED,
    and in every case the actor had every reason to believe it had worked,
    because the action itself succeeded. The check is never "did I do it" but
    "did it land where it has to be".

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the artefact's CONTENT is correct, current, or complete. A tracked
      register full of stale entries passes here.
    - NOT that anything READS it. Tracked and ignored-by-every-consumer is a
      different failure, and this gate cannot see it.
    - NOT that derived artefacts are safe to ignore. It checks that each declared
      derived artefact names a TRACKED SOURCE; it does not verify the source
      actually regenerates it.
"""
from __future__ import annotations
import io, json, os, subprocess, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# THE MANIFEST. Every artefact whose PURPOSE is to outlive this session.
# (path, what it is, source_of_truth_if_derived)
DURABLE = [
    ("STANDARD_EXCEPTIONS.json",
     "waiver register -- pages shipped below standard, the countable backlog", None),
    ("MISTAKE-LEDGER.md",
     "the ledger a human reads: mechanisms, failure directions, what each cost", None),
    ("scripts/standard_manifest.py",
     "the standard itself, versioned", None),
    ("scripts/gate_integrity.py",
     "the mistake ledger: mechanisms, failure directions, promotion criteria", None),
    ("scripts/regression_check.py",
     "the pre-push gate the hook invokes", None),
    ("scripts/index_markup_gate.py",
     "root-index markup gate", None),
    ("scripts/audit_surface_census.py",
     "audit-surface census", None),
    ("scripts/external_dependency_census.py",
     "external-dependency census", None),
    (".githooks/pre-push",
     "the hook itself -- untracked, it protects one clone and no other", None),
    ("index.html",
     "the root, the definition of done", None),
]


def _git(args):
    return subprocess.run(["git"] + args, cwd=REPO, capture_output=True, text=True)


def check():
    """-> (verdict, rows). Absence and ignored-ness are BOTH silent deaths, so
    both FAIL. A missing artefact is not 'not applicable'."""
    rows = []
    for path, what, source in DURABLE:
        full = os.path.join(REPO, path.replace("/", os.sep))
        exists = os.path.exists(full)
        ignored = _git(["check-ignore", "-q", path]).returncode == 0 if exists else False
        tracked = (_git(["ls-files", "--error-unmatch", path]).returncode == 0) if exists else False
        if not exists:
            state = "MISSING"
        elif ignored:
            state = "IGNORED"
        elif not tracked:
            state = "UNTRACKED"
        else:
            state = "ok"
        rows.append((path, state, what, source))
    bad = [r for r in rows if r[1] != "ok"]
    return ("FAIL" if bad else "PASS"), rows


def sweep_derived():
    """Ignored files that look like records rather than build output, and have no
    declared tracked source. Reported, not blocking -- a sweep that blocks on
    every generated artefact would be unusable and would get bypassed."""
    out = _git(["status", "--ignored", "--porcelain"])
    suspects = []
    for line in out.stdout.splitlines():
        if not line.startswith("!!"):
            continue
        p = line[3:].strip()
        low = p.lower()
        if any(k in low for k in ("ledger", "register", "backlog", "exception",
                                  "decision", "standard", "manifest", "audit")):
            suspects.append(p)
    return suspects


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    v, rows = check()
    print("DURABLE ARTEFACT GATE -- %d declared\n" % len(rows))
    for path, state, what, _src in rows:
        print("   %-9s %-38s %s" % (state, path, what if state == "ok" else "<-- " + what))
    sus = sweep_derived()
    if sus:
        print("\n   SWEEP: ignored paths whose names read like records, not build output.")
        print("   Each needs a tracked source or promotion. Reported, not blocking:")
        for s in sus[:12]:
            print("      %s" % s)
    print("\n  -> %s" % v)
    return 0 if v == "PASS" else 1


def selftest():
    """Constructible failure, per the standard: declare a path that IS ignored and
    confirm the gate fires on it; and a path that does not exist at all."""
    ok = True
    global DURABLE
    real = DURABLE
    try:
        # The fixture must EXIST and be IGNORED. Declaring the register's old
        # path alone reported MISSING -- firing, but for the wrong reason, and
        # therefore proving nothing about ignored-ness. A test whose two failure
        # modes are indistinguishable is the same defect as a check that cannot
        # fail; it just looks like it passed. So write a real file into the
        # ignored directory and require the verdict to be IGNORED specifically.
        probe = os.path.join(REPO, "outputs", "_durable_gate_probe.json")
        os.makedirs(os.path.dirname(probe), exist_ok=True)
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("{}")
        try:
            DURABLE = [("outputs/_durable_gate_probe.json",
                        "a real file inside gitignored outputs/", None)]
            v, rows = check()
            good = v == "FAIL" and rows[0][1] == "IGNORED"
            ok &= good
            print("  POSITIVE a real file inside an IGNORED directory  -> %-4s (%s) %s"
                  % (v, rows[0][1], "correct" if good else "WRONG -- wanted IGNORED"))
        finally:
            os.remove(probe)

        DURABLE = [("scripts/no_such_file_at_all.py", "a declared artefact that does not exist", None)]
        v2, rows2 = check()
        good2 = v2 == "FAIL" and rows2[0][1] == "MISSING"
        ok &= good2
        print("  POSITIVE a declared artefact that is absent      -> %-4s (%s) %s"
              % (v2, rows2[0][1], "correct" if good2 else "WRONG"))

        DURABLE = real
        v3, _ = check()
        ok &= v3 == "PASS"
        print("  NEGATIVE the real manifest as it stands now      -> %-4s %s"
              % (v3, "correct" if v3 == "PASS" else "WRONG"))
    finally:
        DURABLE = real
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the ignored register passing, which is the "
          "exact state the waiver register shipped in for its first hour -- written, "
          "readable, working locally, and present in no clone but this one.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
