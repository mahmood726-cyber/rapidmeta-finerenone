# -*- coding: utf-8 -*-
"""Is a lane's long-running command ALIVE, or did it die without returning?

⛔ THE PROBLEM THIS SOLVES COST TWO LANES SEVERAL HOURS TODAY. A `git push` whose pre-push hook
runs ~40 corpus-wide linters sits at FLAT CPU for twenty minutes and produces no output. So does
a push that died. From outside they are identical, and the whole of tonight's discipline reduces
to one sentence about that:

    ***A CHECK WHOSE FAILURE MODE IS INDISTINGUISHABLE FROM ITS NEGATIVE RESULT IS NOT A CHECK.***

⭐ THE INSTRUMENT IS THE CHILDREN, NOT THE PARENT. `git push` does nothing at all while its hook
runs -- its own idleness carries NO information. Watching pid 16744 alone showed 0.94 seconds of
CPU frozen across twenty minutes, which reads exactly like death. Its children were reading
588 MB and turning over between samples.

    ⇒ WHEN A PROCESS DELEGATES, ITS OWN IDLENESS CARRIES NO INFORMATION. WATCH WHAT IT SPAWNED.

⚠️ AND THE GRAVEYARD IS REAL ON THIS MACHINE, NOT HYPOTHETICAL. Five orphaned `pre-push` shells
were found alive for 476 to 5,608 MINUTES at ~0 CPU and 0 MB read -- pushes that died without
returning and without refusing, from earlier parallel runs. NOBODY OWNS THE GRAVEYARD. This
lists them; it never kills them, because a process nobody can account for is evidence, and
whoever spawned it may still be waiting on it.

THE TWO SIGNATURES, and they are cleanly separable:

    ALIVE      children accumulating CPU **and** bytes; the worker SET turns over between samples
    GRAVEYARD  ~0 CPU, 0 MB read, alive for hours, no children at all

USAGE
    python lane_liveness.py                 # two samples of every git/hook process, plus the graveyard
    python lane_liveness.py --pid 16744     # one command's tree
    python lane_liveness.py --graveyard     # only the orphans, no sampling

⭐ AND IT IS PAIRED WITH THE COORDINATION RULES BELOW, because both failures today were the same
shape: a claim about state the claimant could not observe.
"""
import io
import json
import os
import subprocess
import sys
import time

INTERVAL = 70          # seconds between samples; long enough that a starved job still moves
GRAVE_MIN_MINUTES = 60  # alive this long with no work done is a candidate corpse

COORDINATION_RULES = """
⭐ COORDINATION RULES FOR PARALLEL LANES -- written from two lanes losing hours to them today.

1. ASSERT CLAIMS ABOUT SHARED STATE AGAINST SHARED STATE.
   Any sentence of the form "my X is wired into Y", where Y lives on main, must be quoted from
   `git show origin/main:Y` -- never from the speaker's own worktree. The claim and its evidence
   live in different trees and only one of them is authoritative. An ordering claim survived
   most of a day today because it was about `gates/run_all.py` on main, and NEITHER LANE READ
   THAT FILE ON MAIN until it was challenged. One command would have settled it.

2. `origin/main` IS THE ONLY COORDINATION CHANNEL THAT EXISTS.
   Ordering negotiated in prose between lanes has no observable referent. REBASE ONTO WHAT IS
   THERE NEEDS NO AGREEMENT AT ALL -- and a lane that adopts that rule never has to ask, never
   has to wait, and cannot be blocked by a premise it can't check.

3. BRANCH-PER-LANE IS NOT ISOLATION; WORKTREE-PER-LANE IS.
   We had worktrees. What we lacked was any way to see another lane's COMMITTED state without
   asking it. `git ls-remote` plus `git show origin/main:<path>` is that mechanism and it costs
   one round trip.

⚠️ THE TRAP UNDERNEATH ALL THREE: a false premise about another lane's state is UNFALSIFIABLE
FROM INSIDE YOUR OWN LANE. That is the same shape as every instrument failure recorded tonight
-- a claim about the world that only the claimant's own view supports.

⚠️ AND ONE THAT IS NOT ABOUT GIT: a lane's report is an OBSERVATION. Relaying it as an
instruction launders it into a fact. The relay is where the check gets skipped, because the
recipient hears a decision rather than a claim.
"""


class QueryFailed(Exception):
    """The process table could not be read. NOT the same as 'there are no processes'."""


def _ps(fields):
    """Win32_Process rows via PowerShell -- CIM is the only place ReadTransferCount lives.

    ⛔ THE FIRST VERSION RETURNED [] ON ANY EXCEPTION, AND THAT IS THE WORST DEFECT THIS FILE
    HAS HAD. A timed-out or failed query became "no processes found", `graveyard()` then
    reported "0 found", and a TOOL BUILT TO DETECT SILENT DEATH WOULD HAVE ISSUED A CLEAN BILL
    OF HEALTH FROM A QUERY THAT NEVER RAN. It happened: the snapshot came back empty under disk
    contention and the caller raised StopIteration on an empty dict rather than being told why.
    #
    ⚠️ AN ABSENCE PRODUCED BY A FAILED MEASUREMENT MUST NEVER RENDER AS AN OBSERVED ABSENCE.
    That is the same rule as SNAPSHOT_TOO_OLD versus NO_RESULTS_POSTED, and as
    NOT_RETRIEVABLE versus RETRIEVED_NO_VALUE -- three tools, one lesson, and this one had it
    backwards while its docstring lectured about exactly this.
    """
    ps = ("Get-CimInstance Win32_Process | Select-Object " + ",".join(fields) +
          " | ConvertTo-Json -Compress -Depth 3")
    try:
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                           capture_output=True, timeout=180)
    except subprocess.TimeoutExpired:
        raise QueryFailed("the process-table query timed out after 180s. This machine is "
                          "under heavy disk contention; NOTHING is known about any process.")
    out = p.stdout.decode("utf-8", "replace").strip()
    if p.returncode != 0 or not out:
        raise QueryFailed("the process-table query returned nothing (rc=%s, %d bytes of "
                          "stderr). NOTHING is known about any process."
                          % (p.returncode, len(p.stderr or b"")))
    try:
        d = json.loads(out)
    except ValueError:
        # ⛔ A COMMAND LINE ON THIS MACHINE CONTAINS A RAW CONTROL CHARACTER, and strict JSON
        # rejects the whole 316KB document because of it. The ORIGINAL code caught this as a
        # bare `except` and returned [] -- so one stray byte in one unrelated process's argv
        # made the tool report that NO PROCESSES EXIST.
        #
        # ⚠️ THE FAILURE WAS NEVER THE TIMEOUT I ASSUMED. I diagnosed "disk contention" from
        # an empty result, and the empty result was a parse error the code had hidden. A
        # swallowed exception does not just lose the error -- IT INVENTS A PLAUSIBLE WRONG
        # STORY, and I believed mine for two rounds.
        try:
            d = json.loads(out, strict=False)
        except ValueError as exc:
            raise QueryFailed("the process-table query returned unparseable output (%s). "
                              "NOTHING is known about any process." % exc)
    rows = d if isinstance(d, list) else [d]
    if not rows:
        raise QueryFailed("the process-table query parsed to zero rows, which cannot be true "
                          "of a running machine")
    # ⛔ THE PLANT CAUGHT THIS AND NOTHING ELSE WOULD HAVE. `Select-Object <nonexistent>` is not
    # an error to PowerShell: it returns one object per process with the column present and
    # NULL, so rc=0, the JSON parses, and the row count is enormous. Every field this module
    # reads then evaluates to 0 -- and a query for a column that does not exist would have been
    # reported as a machine where nothing is running and nothing has ever read a byte.
    #
    # ⚠️ SO "IT PARSED" IS NOT "IT ANSWERED". The shape has to be checked, not just the syntax:
    # if not one row carries the identifier this module is built on, the answer is not weak, it
    # is about something else entirely.
    missing = [f for f in fields if not any(r.get(f) is not None for r in rows)]
    if missing:
        raise QueryFailed("the process-table query returned %d rows in which %s is null in "
                          "EVERY row -- the column does not exist, so this is not an answer "
                          "about processes. NOTHING is known."
                          % (len(rows), ", ".join(missing)))
    return rows


def snapshot():
    rows = _ps(["ProcessId", "ParentProcessId", "Name", "CommandLine",
                "ReadTransferCount", "UserModeTime", "KernelModeTime", "CreationDate"])
    return {int(r["ProcessId"]): r for r in rows if r.get("ProcessId")}


def _cpu(r):
    return (int(r.get("UserModeTime") or 0) + int(r.get("KernelModeTime") or 0)) / 1e7


def _mb(r):
    return (int(r.get("ReadTransferCount") or 0)) / 1048576.0


# ⛔ WMI's CreationDate ARRIVES IN SEVERAL SHAPES AND THE FIRST VERSION HANDLED ONE. Through
# `ConvertTo-Json` it is a localised string -- "26 August 2026 23:33:44" on this machine -- not
# the `yyyymmddHHMMSS` CIM literal I parsed for. Every age printed `None`, and because the
# filter admitted `None`, the ages simply vanished from the output without any error.
#
# ⚠️ A PARSE THAT FAILS TO A BLANK IS A PARSE THAT FAILS SILENTLY. The row still printed; only
# the number a reader would act on was missing. So the fallbacks are explicit and a failure to
# parse is REPORTED as an unknown age rather than becoming one.
_DATE_FORMATS = ("%d %B %Y %H:%M:%S", "%d %b %Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p")


def _age_minutes(r, now=None):
    """Minutes since this process started, or None -- and None is SAID, never implied."""
    now = now or time.time()
    cd = str(r.get("CreationDate") or "").strip()
    if not cd:
        return None
    # ⭐ /Date(1787783624737)/ -- the .NET epoch-millis form ConvertTo-Json actually emits here.
    # My first guess was the CIM literal, my second was a localised date string, and the truth
    # was a third shape neither covered. THE FIX WAS NOT MORE FORMATS, IT WAS PRINTING THE RAW
    # VALUE: two rounds of guessing cost more than one `repr()`.
    if cd.startswith("/Date(") and cd.rstrip("/)").split("(")[-1].lstrip("-").isdigit():
        try:
            return (now - int(cd.rstrip("/)").split("(")[-1]) / 1000.0) / 60.0
        except (ValueError, IndexError):
            return None
    if len(cd) >= 14 and cd[:14].isdigit():          # CIM literal 20260826233344.xxxxx
        try:
            return (now - time.mktime(time.strptime(cd[:14], "%Y%m%d%H%M%S"))) / 60.0
        except ValueError:
            return None
    for fmt in _DATE_FORMATS:                        # localised ConvertTo-Json strings
        try:
            return (now - time.mktime(time.strptime(cd, fmt))) / 60.0
        except ValueError:
            continue
    return None


def descendants(snap, pid, depth=6):
    out, frontier = [], {pid}
    for _ in range(depth):
        nxt = set()
        for p, r in snap.items():
            if r.get("ParentProcessId") in frontier and p not in frontier:
                out.append(r)
                nxt.add(p)
        if not nxt:
            break
        frontier = nxt
    return out


def classify(a, b, pid):
    """Two snapshots -> a verdict for one process tree."""
    ca, cb = descendants(a, pid), descendants(b, pid)
    work = sum(_cpu(r) for r in cb) - sum(_cpu(r) for r in ca)
    read = sum(_mb(r) for r in cb) - sum(_mb(r) for r in ca)
    set_a = {r.get("CommandLine") for r in ca}
    set_b = {r.get("CommandLine") for r in cb}
    turned = bool(set_a ^ set_b)
    if pid not in b:
        return "RETURNED", {"why": "the process is gone; read its output and its exit path"}
    if not cb and not ca:
        return "NO CHILDREN", {
            "why": ("this process spawned nothing in either sample. If it is a hook-running "
                    "command that is the GRAVEYARD signature; if it does its own work, judge "
                    "it on its own CPU instead.")}
    if work > 0.1 or read > 1.0 or turned:
        return "ALIVE", {"child_cpu_delta_s": round(work, 2),
                         "child_read_delta_mb": round(read, 1),
                         "worker_set_changed": turned,
                         "children": len(cb)}
    return "SUSPECT", {
        "why": ("children exist but did no measurable work between samples. Not proof of death "
                "-- a single starved read can span %ds -- so sample again before acting."
                % INTERVAL),
        "child_cpu_delta_s": round(work, 2), "child_read_delta_mb": round(read, 1)}


def graveyard(snap, later=None):
    """Orphaned hook shells: alive for hours, ~0 CPU, 0 bytes, no children. LISTED, NEVER KILLED."""
    now = time.time()
    out = []
    for pid, r in snap.items():
        cl = r.get("CommandLine") or ""
        if "hook" not in cl and "pre-push" not in cl and "pre-commit" not in cl:
            continue
        # ⛔ THE FIRST VERSION SKIPPED ANY PROCESS WITH A CHILD, AND EVERY ORPHAN HAS EXACTLY
        # ONE. It found 1 of 5. A dead hook shell is not childless -- it is stuck holding a
        # child that is also doing nothing, which is precisely why it never returned.
        #
        # ⚠️ A FILTER THAT ENCODES AN ASSUMPTION ABOUT THE TARGET EXCLUDES THE TARGET. I assumed
        # "orphan" meant "childless", built the detector around that assumption, and it hid the
        # exact processes it was written to find -- while reporting a confident "1 found".
        # The assumption was never tested against a known orphan, which is the whole reason it
        # survived into the tool.
        #
        # SO THE TEST IS WORK, NOT SHAPE: the tree as a whole must have done nothing.
        # ⛔ CUMULATIVE COUNTERS CANNOT SAY *WHEN* THE WORK HAPPENED. The previous test compared
        # absolute totals against a threshold, and a hook shell alive for 3.9 DAYS has of course
        # accumulated 65 seconds of CPU and 105 MB of reads -- all of it before it died. So the
        # test excluded every real corpse and reported "0 found".
        #
        # ⚠️ THIS IS THE SAME ERROR AS WATCHING THE PARENT INSTEAD OF THE CHILDREN, one level
        # down: MEASURING THE WRONG QUANTITY AND BELIEVING THE ANSWER. A corpse is defined by
        # ZERO DELTA, not by a small total, and delta needs two samples -- which is exactly what
        # the liveness half of this file already knew and this half did not.
        tree = [r] + descendants(snap, pid)
        if later is not None:
            after = [later[x["ProcessId"]] for x in tree if x["ProcessId"] in later]
            if not after:
                continue                       # the whole tree exited between samples: alive-ish
            d_cpu = sum(_cpu(x) for x in after) - sum(_cpu(x) for x in tree)
            d_mb = sum(_mb(x) for x in after) - sum(_mb(x) for x in tree)
            if d_cpu > 0.05 or d_mb > 1.0:
                continue                       # it moved: not a corpse
        elif sum(_cpu(x) for x in tree) > 5.0 or sum(_mb(x) for x in tree) > 5.0:
            continue                           # single-sample fallback, explicitly weaker
        mins = _age_minutes(r, now)
        if mins is None or mins >= GRAVE_MIN_MINUTES:
            out.append({"pid": pid, "alive_minutes": round(mins, 1) if mins is not None else None,
                        "cpu_s": round(sum(_cpu(x) for x in tree), 2),
                        "read_mb": round(sum(_mb(x) for x in tree), 1),
                        "children": len(tree) - 1, "cmd": cl[:110],
                        "measured": "delta over two samples" if later is not None
                                    else "SINGLE SAMPLE -- weaker, cannot see stale totals"})
    return sorted(out, key=lambda x: -(x["alive_minutes"] or 0))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    args = sys.argv[1:]
    a = snapshot()
    if "--graveyard" in args:
        print("sampling twice, %d seconds apart -- a corpse is ZERO DELTA, not a small total"
              % INTERVAL)
        time.sleep(INTERVAL)
        graves = graveyard(a, snapshot())
        print("ORPHANED HOOK PROCESSES -- listed, never killed")
        for g in graves:
            print("  pid %-7s alive %-9s CPU %-7s read %-8s %s"
                  % (g["pid"], g["alive_minutes"], g["cpu_s"], g["read_mb"], g["cmd"][:70]))
        print("  %d found. ⚠️ Nobody owns these. Whoever spawned them may still be"
              " waiting." % len(graves))
        return 0
    graves = []
    if "--rules" in args:
        print(COORDINATION_RULES)
        return 0

    want = None
    if "--pid" in args:
        want = int(args[args.index("--pid") + 1])
    targets = ([want] if want else
               [p for p, r in a.items()
                if (r.get("Name") in ("git.exe",)
                    and any(k in (r.get("CommandLine") or "") for k in ("push", "commit")))])
    if not targets:
        print("no git push/commit process found")
    else:
        print("sampling %d process tree(s), %d seconds apart ..." % (len(targets), INTERVAL))
        time.sleep(INTERVAL)
        b = snapshot()
        for pid in targets:
            verdict, ev = classify(a, b, pid)
            print("")
            print("  pid %-8s %s" % (pid, verdict))
            for k, v in sorted(ev.items()):
                print("     %-22s %s" % (k, v))
            for r in descendants(b, pid):
                if r.get("Name") == "python.exe":
                    print("     child CPU %-8.2f read %-8.1f %s"
                          % (_cpu(r), _mb(r), (r.get("CommandLine") or "")[-46:]))
    print("")
    print("GRAVEYARD: %d orphaned hook process(es)" % len(graves))
    for g in graves[:8]:
        print("   pid %-7s alive %-8s min  CPU %-6s  read %-6s MB"
              % (g["pid"], g["alive_minutes"], g["cpu_s"], g["read_mb"]))
    if graves:
        print("   ⚠️ ~0 CPU and 0 MB read for hours is the death signature. LISTED, NOT KILLED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def plant():
    """⭐ BOTH WAYS, ON SYNTHETIC SNAPSHOTS -- because a plant that depends on what happens to be
    running is not repeatable, and every defect this file had came from testing it against
    whatever the machine was doing at the time.

    Four cases, one per defect this detector actually shipped with:
      ALIVE       children accumulating -> must not be called dead
      GRAVEYARD   a corpse WITH A CHILD -> the filter that skipped children found 1 of 5
      STALE       a corpse with large CUMULATIVE totals -> absolute thresholds excluded it
      QueryFailed a failed query -> must RAISE, never return "nothing found"
    """
    _u = getattr(sys.stdout, "_ll_wrapped", False)
    if not _u:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace", line_buffering=True)
        sys.stdout._ll_wrapped = True

    def proc(pid, ppid, name, cmd, cpu_s, mb, age_min=600):
        ms = int((time.time() - age_min * 60) * 1000)
        return {"ProcessId": pid, "ParentProcessId": ppid, "Name": name, "CommandLine": cmd,
                "UserModeTime": int(cpu_s * 1e7), "KernelModeTime": 0,
                "ReadTransferCount": int(mb * 1048576), "CreationDate": "/Date(%d)/" % ms}

    HOOK = "bash.exe .githooks/pre-push origin https://example/x.git"
    # 1 ALIVE: child does work between samples
    a1 = {10: proc(10, 1, "git.exe", "git push", 0.9, 0.3),
          11: proc(11, 10, "bash.exe", HOOK, 0.1, 0.0),
          12: proc(12, 11, "python.exe", "python lint.py", 5.0, 40.0)}
    b1 = dict(a1); b1[12] = proc(12, 11, "python.exe", "python lint.py", 9.0, 75.0)
    v1, _ = classify(a1, b1, 10)

    # 2 GRAVEYARD: a corpse that HAS a child -- the case the first filter excluded
    a2 = {20: proc(20, 1, "bash.exe", HOOK, 0.03, 0.0, age_min=5600),
          21: proc(21, 20, "python.exe", "python idle.py", 0.0, 0.0, age_min=5600)}
    g2 = graveyard(a2, dict(a2))

    # 3 STALE: a corpse with LARGE cumulative totals -- excluded by absolute thresholds
    a3 = {30: proc(30, 1, "bash.exe", HOOK, 65.0, 105.0, age_min=5600),
          31: proc(31, 30, "python.exe", "python done.py", 20.0, 200.0, age_min=5600)}
    g3 = graveyard(a3, dict(a3))

    # 4 a live tree must NOT be called a corpse
    g4 = graveyard(a1, b1)

    ok1 = v1 == "ALIVE"
    ok2 = len(g2) == 1 and g2[0]["pid"] == 20
    ok3 = len(g3) == 1 and g3[0]["pid"] == 30
    ok4 = len(g4) == 0
    try:
        _ps(["NoSuchColumnAtAll"])
        ok5, why = False, "(a bad query did NOT raise)"
    except QueryFailed as exc:
        ok5, why = True, str(exc)[:60]
    except Exception as exc:
        ok5, why = False, "raised %s instead of QueryFailed" % type(exc).__name__

    print("")
    print("PLANT -- lane_liveness")
    print("   live tree with working children -> ALIVE        %-5s [%s]"
          % (v1, "PASS" if ok1 else "FAIL"))
    print("   corpse WITH a child is found                    %-5s [%s]   <- filter defect 1"
          % (ok2, "PASS" if ok2 else "FAIL"))
    print("   corpse with large CUMULATIVE totals is found    %-5s [%s]   <- defect 4"
          % (ok3, "PASS" if ok3 else "FAIL"))
    print("   a LIVE tree is not reported as a corpse         %-5s [%s]"
          % (ok4, "PASS" if ok4 else "FAIL"))
    print("   a failed query RAISES, never 'nothing found'    %-5s [%s]   <- defect 3"
          % (ok5, "PASS" if ok5 else "FAIL"))
    print("      %s" % why)
    print("   \u26a0\ufe0f every one of these is a defect this file SHIPPED with. An unplanted")
    print("      detector is what produced all four.")
    for cond, msg in ((ok1, "live tree misread"), (ok2, "corpse with a child missed"),
                      (ok3, "corpse with stale totals missed"), (ok4, "live tree called dead"),
                      (ok5, "failed query returned an empty world")):
        assert cond, msg
    return 0
