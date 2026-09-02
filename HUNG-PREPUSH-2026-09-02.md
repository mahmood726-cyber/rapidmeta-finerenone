# Four `pre-push` hooks were hung for up to 6.5 hours, holding four stale HTTP servers

**2026-09-02 ~02:45. Terminated after the list below was published. If you were pushing and it
stopped, this is why — and nothing of yours was lost. Read the last section.**

## What was found

Not a slow chain. A **hang**. Four `pre-push` processes had accumulated **0.02–0.03 CPU
seconds** across **101 to 391 minutes** of wall clock. A process that has used three
hundredths of a second in six and a half hours is not working.

| pre-push PID | age | CPU | leaked server PID | port | server CPU |
|---|---|---|---|---|---|
| 1208 | **391 min** | 0.03 s | 9124 | 8787 | 4.14 s |
| 16128 | **354 min** | 0.02 s | 1464 | 8799 | 3.64 s |
| 16452 | **335 min** | 0.02 s | 18260 | 8800 | 3.66 s |
| 21932 | **101 min** | 0.02 s | 11300 | 8801 | 1.36 s |

> Only the process table says a commit is alive. **CPU time says whether it progresses.**

`.githooks/pre-push` starts `python -m http.server $PORT` in the background and relies on
`trap cleanup EXIT` to stop it. **The trap only fires on exit, and these never exited**, so
each hang leaks a server that holds its port for the rest of the night.

## Why this was also a correctness problem, not only a throughput one

Probed immediately before termination:

```
port 8787   index.html 200   CHECK-INVENTORY-2026-09-02.md 200
port 8799   index.html 200   CHECK-INVENTORY-2026-09-02.md 404
port 8800   index.html 200   CHECK-INVENTORY-2026-09-02.md 404
port 8801   index.html 200   CHECK-INVENTORY-2026-09-02.md 404
```

**All four answer `index.html`. Three are serving trees frozen hours ago.** A probe of
`index.html` proves *something* is there; it cannot prove it is *you*. That is precisely the
2026-08-17 incident recorded in the hook itself — a sibling worktree held 8787 and a day's
regression verdicts were measured against the wrong bytes, 912,140 over the wire against
6,147,695 on disk.

The nonce probe was added to close that. **It closes half of it:**

```
probe nonce on 8787  ->  not us  ->  fall back to 8799        (single step, only)
probe nonce on 8799  ->  not us  ->  start server on 8799
                                      ^ if a leaked server already holds 8799 this
                                        fails silently for "address in use"...
                                      ...and NOTHING re-probes the nonce afterwards.
```

**The guard checks its precondition and never its postcondition.** With three leaked servers
holding 8799–8801, the identical 2026-08-17 defect can recur one port over, and the hook will
report green having measured another tree entirely.

**Fix (two lines, sequenced after in-flight pushes clear):** re-probe the nonce *after*
`sleep 2` and refuse on mismatch. A guard that can only report "a server answered" is not a
guard — same lesson as vendor liveness, already written in that file's own comments.

## What was terminated, and what it cost you

Only processes matching **all** of: named `pre-push`, **zero CPU**, **older than 60 minutes**
— plus the `http.server` child each one leaked. Matched **by PID**, never by a shared string.
CPU was re-read immediately before each kill, because an hours-old reading is a claim about
the past.

**A killed `git push` is not destructive.** Refs update atomically: your push either already
landed or it did not, and if it did not, re-running it loses nothing. No commit, no object and
no staged work is affected by terminating the hook process. The only thing destroyed was four
processes that had done nothing for hours and four servers answering with stale bytes.

If your push has not landed, **just push again** — the ports are now free, so the hook will
start a server on 8787 serving *your* tree instead of falling back onto someone else's.
