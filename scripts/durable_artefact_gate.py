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
import io, json, os, subprocess, sys, time

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
    ("scripts/harness_gate.py",
     "verification-lane gate: the 20 artefact-decidable detectors", None),
    ("scripts/export_artefact.py",
     "the join -- SSOT object to the shape the detectors read; without it the "
     "gate is invoked and sees nothing", None),
    ("scripts/objects_for_pages.py",
     "explicit page->object map reader; a heuristic here would silently empty "
     "the gate's input", None),
    ("ssot/PAGE_MAP.json",
     "the map itself: which object each built page came from", None),
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


# The sweep walks the entire working tree INCLUDING ignored paths. On this repo
# that walk is by far the most expensive thing the gate does, and it was
# UNBOUNDED: it held a push open for as long as it took, and slowed every
# concurrent lane's `git status` while it ran. A gate is allowed to cost
# something. It is not allowed to cost an unknown amount and never say so.
SWEEP_TIMEOUT_S = float(os.environ.get("DURABLE_GATE_SWEEP_TIMEOUT", "120"))


class Timeout(Exception):
    """The bound was hit.

    Distinct from "the command failed" and from "the command succeeded and
    found nothing". Those are THREE outcomes, and collapsing any two of them
    into one value is precisely the defect this class exists to prevent.
    """


def _git(args, timeout=None):
    """Bounded git.

    timeout=None preserves the old behaviour for the cheap per-path calls
    (check-ignore / ls-files, one process per declared artefact, milliseconds
    each). Only the whole-tree walk passes an explicit bound, and only that
    caller has to handle Timeout.
    """
    try:
        return subprocess.run(["git"] + args, cwd=REPO, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        raise Timeout("git %s exceeded %.1fs" % (" ".join(args), timeout or 0))


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


def sweep_derived(timeout=None, runner=None):
    """Ignored files that look like records rather than build output, and have
    no declared tracked source. Reported, not blocking -- a sweep that blocked
    on every generated artefact would be unusable and would get bypassed.

    RETURNS (state, suspects, elapsed_s, limit_s) -- NOT a bare list.

    THE DEFECT THIS SIGNATURE FIXES. This used to return a plain list, from an
    unbounded walk. When the walk did not complete -- killed, aborted, or still
    running when something gave up on it -- stdout was empty, the loop ran zero
    times, and the function returned []. That is THE SAME VALUE a walk that
    completed and found nothing returns. main() printed the SWEEP block only
    when the list was non-empty, so a sweep that never ran printed NOTHING and
    the gate went on to report its verdict regardless.

    NOTE THE FAILURE DIRECTION. It is the same one this whole file was written
    about. The silent outcome was the CLEAN-LOOKING one: a sweep that did not
    happen was indistinguishable from a sweep that found no problem, so the
    corpus looked better than it was and nothing demanded attention. So the
    three outcomes are now three named states:

        "ok"        the walk COMPLETED. suspects may legitimately be empty.
        "TIMED_OUT" the walk hit the bound. Says NOTHING about the corpus.
        "NOT_RUN"   the walk failed or was aborted. Also says NOTHING.

    Only "ok" is evidence. TIMED_OUT and NOT_RUN are the ABSENCE of evidence,
    and must never be rendered as its presence.

    runner= is injected by the selftest so the bound can be exercised against a
    process that provably cannot finish inside it.
    """
    limit = SWEEP_TIMEOUT_S if timeout is None else timeout
    run = runner or _git
    t0 = time.monotonic()
    try:
        out = run(["status", "--ignored", "--porcelain"], timeout=limit)
    except Timeout:
        return ("TIMED_OUT", [], time.monotonic() - t0, limit)
    except Exception as exc:              # any other failure is still NOT a pass
        sys.stderr.write("   sweep runner raised: %r" % (exc,) + chr(10))
        return ("NOT_RUN", [], time.monotonic() - t0, limit)
    elapsed = time.monotonic() - t0

    if getattr(out, "returncode", 0) != 0:
        return ("NOT_RUN", [], elapsed, limit)

    suspects = []
    for line in (out.stdout or "").splitlines():
        if not line.startswith("!!"):
            continue
        p = line[3:].strip()
        low = p.lower()
        if any(k in low for k in ("ledger", "register", "backlog", "exception",
                                  "decision", "standard", "manifest", "audit")):
            suspects.append(p)
    return ("ok", suspects, elapsed, limit)


def main():
    if "--selftest" in sys.argv[1:]:
        return selftest()
    strict_sweep = "--strict-sweep" in sys.argv[1:]
    v, rows = check()
    print("DURABLE ARTEFACT GATE -- %d declared\n" % len(rows))
    for path, state, what, _src in rows:
        print("   %-9s %-38s %s" % (state, path, what if state == "ok" else "<-- " + what))
    state, sus, elapsed, limit = sweep_derived()

    # A GATE SHOULD PRINT ITS OWN LIMITS. Unconditional: this line is the only
    # way a reader can tell "the sweep found nothing" from "the sweep did not
    # finish", and the only place the cost of this gate is visible to whoever
    # is waiting on it.
    print()
    print("   SWEEP  state=%s  wall=%.1fs  bound=%.0fs  hit_bound=%s"
          % (state, elapsed, limit, "YES" if state == "TIMED_OUT" else "no"))

    if state == "ok":
        if sus:
            print("   ignored paths whose names read like records, not build output.")
            print("   Each needs a tracked source or promotion. Reported, not blocking:")
            for s in sus[:12]:
                print("      %s" % s)
        else:
            print("   walk COMPLETED and found no ignored record-like paths.")
    else:
        print("   THE SWEEP DID NOT RUN TO COMPLETION. THIS IS NOT A CLEAN RESULT.")
        print("   It reports nothing about the corpus either way. Re-run with")
        print("   DURABLE_GATE_SWEEP_TIMEOUT=<seconds> raised to get a verdict.")

    print()
    print("  -> %s   (manifest check; sweep=%s)" % (v, state))
    if strict_sweep and state != "ok":
        print("  -> --strict-sweep: a sweep that did not complete is a FAILURE here.")
        return 1
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

        # ---- THE BOUND. A guard with no failing fixture is not a guard. ----
        # Five cases, because the entire defect was that three distinct
        # outcomes shared one representation ([]). Each must be individually
        # distinguishable, and (d) exists so that "everything times out" cannot
        # pass -- otherwise this is again a check that can only print one thing.
        print()
        print("  THE SWEEP BOUND -- outcomes that MUST NOT collapse:")

        # (a) A REAL timeout, through the real subprocess timeout= path: a
        #     process that provably cannot finish inside the bound. Not a
        #     simulated exception -- the bound itself is what has to work.
        def slow_runner(args, timeout=None):
            try:
                return subprocess.run(
                    [sys.executable, "-c", "import time; time.sleep(30)"],
                    capture_output=True, timeout=timeout)
            except subprocess.TimeoutExpired:
                raise Timeout("slow probe exceeded %.2fs" % (timeout or 0))

        s_a, _, el_a, _ = sweep_derived(timeout=0.5, runner=slow_runner)
        good_a = (s_a == "TIMED_OUT" and 0.4 <= el_a < 25)
        ok &= good_a
        print("    (a) REAL process that CANNOT finish in 0.5s -> %-9s wall=%.2fs %s"
              % (s_a, el_a, "correct" if good_a else "WRONG -- wanted TIMED_OUT"))

        # (b) The aborted walk: nonzero rc, empty stdout. PRE-FIX THIS RETURNED
        #     [] AND WAS INDISTINGUISHABLE FROM (d). This is the regression.
        class _Aborted:
            stdout, stderr, returncode = "", "killed", -9
        s_b, _, _, _ = sweep_derived(timeout=5,
                                     runner=lambda a, timeout=None: _Aborted())
        good_b = (s_b == "NOT_RUN")
        ok &= good_b
        print("    (b) walk ABORTED (rc=-9, empty stdout)      -> %-9s %s"
              % (s_b, "correct" if good_b else "WRONG -- wanted NOT_RUN"))

        # (c) Runner raises something unexpected -> still must not read as pass.
        def _boom(a, timeout=None):
            raise OSError("git not on PATH")
        s_c, _, _, _ = sweep_derived(timeout=5, runner=_boom)
        good_c = (s_c == "NOT_RUN")
        ok &= good_c
        print("    (c) runner raises OSError                   -> %-9s %s"
              % (s_c, "correct" if good_c else "WRONG -- wanted NOT_RUN"))

        # (d) POSITIVE CONTROL: a walk that really completed and really found
        #     nothing. Without it, a gate that returned TIMED_OUT for
        #     everything would pass (a)-(c).
        class _Clean:
            stdout, stderr, returncode = "", "", 0
        s_d, sus_d, _, _ = sweep_derived(timeout=5,
                                         runner=lambda a, timeout=None: _Clean())
        good_d = (s_d == "ok" and sus_d == [])
        ok &= good_d
        print("    (d) walk COMPLETED, found nothing           -> %-9s %s"
              % (s_d, "correct" if good_d else "WRONG -- wanted ok"))

        # (e) The regression itself, stated as an assertion.
        distinct = len({s_a, s_b, s_d}) == 3
        ok &= distinct
        print("    (e) timed-out / aborted / clean are DISTINCT-> %-9s %s"
              % (str(distinct), "correct" if distinct else "WRONG -- states collapsed"))
    finally:
        DURABLE = real
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the ignored register passing, which is the "
          "exact state the waiver register shipped in for its first hour -- written, "
          "readable, working locally, and present in no clone but this one.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
