"""Keep Codex and agy saturated independently of whoever is writing.

WHY A DAEMON AND NOT A SEQUENCE OF CALLS. Ten lanes across a whole session is not hard use,
and the reason was structural: each vendor call was a STEP in the writer's sequence --
launch, await, read, report, launch. A separate machine idles for the whole of every step
that is not its own. This owns the queue instead: it keeps N Codex and M agy processes
alive at all times, starts the next task the instant one lands, and never waits for anyone.

DETACHED ON PURPOSE. Earlier lanes died when the shell that spawned them was killed by an
unrelated timeout. These are started with CREATE_NEW_PROCESS_GROUP / DETACHED_PROCESS on
Windows and setsid elsewhere, so a lane outlives the thing that launched it.

THE QUEUE IS A DIRECTORY. Drop a .task JSON in `outputs/lanes/queue/`; the daemon picks it
up on its next tick. So work can be added while it runs, which is the point -- a lane
finishing with nothing queued is the failure to avoid.

STATUS IS A FILE, NOT A MEMORY. `outputs/lanes/status.json` carries launched/running/done
counts and every lane's state, so throughput can be reported as a number by anyone, at any
time, without asking the daemon anything.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANES = os.path.join(REPO, "outputs", "lanes")
QUEUE = os.path.join(LANES, "queue")
# A THIRD DIRECTORY, BECAUSE TWO WERE NOT ENOUGH.
#
# The task file used to stay in QUEUE for as long as its lane ran, and the fill loop picks
# the first matching task in QUEUE. So on every tick it re-picked a task that was ALREADY
# RUNNING, overwrote the process handle in `running`, and the original was never reaped:
# 19 launches, 1 process, 0 returns, and the queue count never moved. It was relaunching
# the same lane against a live vendor quota.
#
# A task now MOVES to RUNNING at spawn, so QUEUE means pending and only pending. On restart
# anything left in RUNNING is requeued, because a lane that was mid-flight at a crash did
# not finish.
RUNNING = os.path.join(LANES, "running")
DONE = os.path.join(LANES, "done")
OUT = os.path.join(LANES, "out")
STATUS = os.path.join(LANES, "status.json")

MAX = {"codex": 4, "agy": 2}
TICK = 10
# A lane that has produced no bytes for this long is hung, not thinking.
STALL_SECONDS = 2400


def _mkdirs():
    for d in (LANES, QUEUE, RUNNING, DONE, OUT):
        os.makedirs(d, exist_ok=True)


def _bin(engine):
    """The REAL executable, not the name on PATH.

    `codex` on PATH is a shell wrapper with no extension; CreateProcess cannot run it, so
    every spawn returned WinError 2 and 83 lanes 'completed' in ninety seconds with a
    one-line failure each. A status code reporting the wrapper rather than the work -- the
    exact shape on this daemon's own hunt list, in the daemon.
    """
    import shutil
    if os.name == "nt":
        cand = {"codex": ["codex.cmd", "codex.exe"], "agy": ["agy.exe", "agy.cmd"]}[engine]
    else:
        cand = [engine]
    for c in cand:
        p = shutil.which(c)
        if p:
            return p
    raise FileNotFoundError("no executable for %s among %s" % (engine, cand))


def _spawn(engine, prompt_path, out_path):
    """THE PROMPT GOES DOWN STDIN, NOT ARGV.

    Passed as an argument, a prompt with a source file inlined blows the Windows command
    line at about 8 KB: "The command line is too long", four lanes dead in seconds, exit
    status non-zero and nothing to show for it. And inlining the file is the whole point --
    four exploratory Codex passes produced no verdict while the fifth, handed the file,
    answered in 7,791 tokens. So the size is not negotiable and the transport had to change.

    `codex exec -` and bare `agy` both read a prompt from stdin; verified by a real
    completion on each before this was written, not from the help text.
    """
    exe = _bin(engine)
    cmd = [exe, "exec", "--skip-git-repo-check", "-"] if engine == "codex" else [exe]
    fh = io.open(out_path, "wb")
    # NO DETACHED_PROCESS. `codex` is codex.cmd, a BATCH FILE, and a batch file launched
    # detached produced a live process that wrote nothing at all: 0 bytes after ten minutes
    # while agy -- a real .exe on the same daemon, same transport -- returned normally. The
    # same prompt file through the same `codex exec -` in the foreground answered in under
    # four minutes, which is what separated the transport from the launch flags.
    #
    # The daemon is already detached from any shell by nohup, so its children do not need to
    # be detached from IT. A new process group is kept so a stall can be killed without
    # taking the daemon with it.
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    # STDIN IS THE PROMPT FILE ITSELF, NOT A PIPE THIS PROCESS FEEDS.
    #
    # Piping it deadlocked the whole daemon. A prompt with a module inlined runs to a couple
    # of hundred kilobytes; a Windows pipe buffer is about 64. `proc.stdin.write` blocked
    # waiting for a detached child to drain it, and the daemon is single-threaded, so
    # everything stopped: alive for three minutes, status file never written once, one lane
    # launched and nothing reaped. A daemon that cannot report is worse than one that is
    # down, because the stale status file from the previous run reads as current.
    #
    # Handing the OS a file descriptor removes the participant that was blocking.
    pf = io.open(prompt_path, "rb")
    try:
        proc = subprocess.Popen(cmd, cwd=REPO, stdin=pf, stdout=fh,
                                stderr=subprocess.STDOUT, **kw)
    finally:
        pf.close()
    return proc, fh


def _requeue_orphans():
    """Anything left in RUNNING did not finish. A crash is not a completion."""
    n = 0
    for f in sorted(os.listdir(RUNNING)):
        if f.endswith(".task"):
            os.replace(os.path.join(RUNNING, f), os.path.join(QUEUE, f))
            n += 1
    return n


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    _mkdirs()
    orphans = _requeue_orphans()
    running = {}          # name -> dict
    launched = done = failed = 0
    started = time.time()
    idle_ticks = 0
    while True:
        # --- reap
        for name in list(running):
            r = running[name]
            if r["proc"].poll() is None:
                size = os.path.getsize(r["out"]) if os.path.isfile(r["out"]) else 0
                if size != r["size"]:
                    r["size"], r["last"] = size, time.time()
                elif time.time() - r["last"] > STALL_SECONDS:
                    r["proc"].kill()
                continue
            r["fh"].close()
            done += 1
            rc = r["proc"].returncode
            if rc != 0:
                failed += 1
            # THE DAEMON MUST SURVIVE ITS OWN DIRECTORIES BEING EDITED WHILE IT RUNS.
            #
            # That is not an edge case, it is the DESIGN: the queue is a directory so
            # that work can be added and withdrawn without stopping anything. Tonight I
            # withdrew 95 agy tasks to rebuild their packets and deleted the .task files
            # of lanes that were still in flight. The reap called os.replace on one, got
            # FileNotFoundError, and the whole daemon died -- eleven minutes of both
            # pools idle, with a stale status file that read as current.
            #
            # A supervisor that dies because one bookkeeping file vanished is not a
            # supervisor. Losing the record of a finished lane costs a re-run; losing the
            # daemon costs the night.
            try:
                os.replace(r["task"], os.path.join(DONE, os.path.basename(r["task"])))
            except OSError:
                pass
            running.pop(name)

        # --- fill
        for engine in ("codex", "agy"):
            live = sum(1 for r in running.values() if r["engine"] == engine)
            while live < MAX[engine]:
                nxt = None
                # THE POSITIVE PROPERTY, NOT THE ABSENCE OF ITS OPPOSITE. This read
                # `if not f.endswith(".task"): continue` inside the loop, and
                # `audit_exclusion_by_absence --gate` refused the commit for it: a negative
                # guard inside a corpus-wide loop says what a thing is NOT, which is
                # satisfied by anything at all -- a partial write, a temp file, an editor
                # backup. What is meant is that the file IS a task, and that is now what is
                # written.
                for f in sorted(x for x in os.listdir(QUEUE) if x.endswith(".task")):
                    # Same reason: a task can be withdrawn between the listing and the
                    # read. Skip it rather than fall over.
                    try:
                        t = json.load(io.open(os.path.join(QUEUE, f), encoding="utf-8"))
                    except (OSError, ValueError):
                        continue
                    if t.get("engine") == engine:
                        nxt = (f, t)
                        break
                if not nxt:
                    break
                f, t = nxt
                name = f[:-5]
                out_path = os.path.join(OUT, name + ".out")
                try:
                    proc, fh = _spawn(engine, os.path.join(REPO, t["prompt"]), out_path)
                except Exception as exc:
                    failed += 1
                    io.open(out_path, "w", encoding="utf-8").write("SPAWN FAILED: %s" % exc)
                    os.replace(os.path.join(QUEUE, f), os.path.join(DONE, f))
                    continue
                # MOVED OUT OF THE QUEUE AT SPAWN. This is the fix: QUEUE now means
                # pending and only pending, so the fill loop cannot re-pick a live lane.
                task_running = os.path.join(RUNNING, f)
                try:
                    os.replace(os.path.join(QUEUE, f), task_running)
                except OSError:
                    # Withdrawn under us between the read and the move; the lane is
                    # already spawned, so let it run and record it where it now is.
                    task_running = os.path.join(RUNNING, f)
                running[name] = {"engine": engine, "proc": proc, "fh": fh,
                                 "out": out_path, "size": 0, "last": time.time(),
                                 "task": task_running,
                                 "started": time.time()}
                launched += 1
                live += 1

        queued = len([f for f in os.listdir(QUEUE) if f.endswith(".task")])
        json.dump({
            "launched": launched, "returned": done, "failed": failed,
            "running": len(running), "queued": queued,
            "uptime_s": int(time.time() - started),
            "requeued_orphans_at_start": orphans,
            "by_engine": {e: sum(1 for r in running.values() if r["engine"] == e)
                          for e in MAX},
            "live": sorted((n, int(time.time() - r["started"]),
                            os.path.getsize(r["out"]) if os.path.isfile(r["out"]) else 0)
                           for n, r in running.items()),
        }, io.open(STATUS, "w", encoding="utf-8"), indent=1)

        if not running and not queued:
            idle_ticks += 1
            # NOT A SILENT EXIT. An empty queue is the failure the operator asked to be told
            # about, so it is written where a report can read it rather than just stopping.
            if idle_ticks >= 6:
                json.dump({"launched": launched, "returned": done, "failed": failed,
                           "running": 0, "queued": 0,
                           "POOLS_IDLE": "both pools have had nothing to do for a minute",
                           "uptime_s": int(time.time() - started)},
                          io.open(STATUS, "w", encoding="utf-8"), indent=1)
                return
        else:
            idle_ticks = 0
        time.sleep(TICK)


if __name__ == "__main__":
    main()
