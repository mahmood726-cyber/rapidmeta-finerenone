"""Rebuild every PAGE_MAP page after the reads-terribly repair, one at a time, and gate it.

CONCURRENCY IS A DIAL, DEFAULT 1, AND THE REASON IT MOVED IS ON THE RECORD. This ran
strictly sequentially while C: was full and another lane was reclaiming disk -- a parallel
fan-out would have raced it for space across a 157-page run. C: is back to ~34 GB and the
papers are now the machine's stated priority, so `--workers N` exists. Each build spawns
Chrome to rasterise figures, so N is small and the run REPORTS DISK before and after; a
worker count that starves C: is worse than a slow run.

EACH PAGE IS GATED IMMEDIATELY AFTER IT IS WRITTEN, not at the end. A 100-minute run that
discovers at minute 95 that the first page regressed is the same failure as a four-hour
batch that dies at hour three: the information existed at minute one and was not read.

THE OLD BYTES ARE KEPT for every page, so a regression is answerable with the file rather
than with a rebuild. `build_tabbed.py` runs its own manuscript guard against the delivered
copy and REFUSES a build that loses more than 5% of the text or any section, so a page that
comes back shorter has already been stopped before this script sees it.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import time

if __name__ == "__main__":
    # write_through=True, AND THE REASON IS THAT `-u` DOES NOT REACH THIS WRAPPER.
    #
    # `python -u` makes PYTHON'S OWN stdout unbuffered. This line then REPLACES that stdout
    # with a wrapper of its own, and a TextIOWrapper around a pipe is block-buffered by
    # default -- so a 163-page run launched with `-u` wrote a 0-BYTE LOG for 47 minutes
    # while it was working normally. Another lane read the empty log, could not see the
    # denominator, divided the correct rate by 1,473 instead of 163, and reported a 15.7
    # hour ETA for a 90 minute job.
    #
    # A LONG JOB THAT CANNOT SAY WHERE IT IS, IS A JOB NOBODY CAN VERIFY -- and the failure
    # is silent, because the work is fine and only the reporting is gone.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", write_through=True)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
BACKUP = os.path.join(REPO, "outputs", "reads_terribly_backup_2026_08_24")
LEDGER = os.path.join(REPO, "outputs", "reads_terribly_rebuild_2026_08_24.json")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_paper_reads_terribly_2026_08_24 as GATE


def _fmt(row):
    if row["state"] == "BUILD_FAILED":
        return "BUILD FAILED"
    return ("%2d -> %2d  %s" % (len(row.get("before") or []), len(row.get("after") or []),
                                "clean" if not row.get("after")
                                else ",".join(row["after"])))


def _flush(path, t0, rows, total=None):
    """Write the ledger, and put the progress line INSIDE it.

    During the run this file was the only thing that could answer "where is it?", because
    stdout was silently swallowed. A progress summary belongs where the durable record is,
    not only in a stream that can be lost.
    """
    el = time.time() - t0
    done = len(rows)
    rate = (done / el * 60) if el > 0 else 0
    left = (total - done) if total else None
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump({"elapsed_s": round(el),
                   "progress": "%d of %s pages, %.1f/min, ETA %s"
                               % (done, total if total else "?", rate,
                                  ("%.0f min" % (left / rate)) if (left and rate) else "?"),
                   "total_pages": total,
                   "rows": rows}, fh, indent=2)


def main():
    if not GATE.run_controls():
        sys.exit("REFUSED: the gate's own controls failed, so nothing it says is evidence.")

    page_map = json.load(open(os.path.join(SSOT, "PAGE_MAP.json"), encoding="utf-8"))
    os.makedirs(BACKUP, exist_ok=True)
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    pages = sorted(only) if only else sorted(page_map)

    # --stale: only pages OLDER than the inputs that produce them.
    #
    # Objects and generator code both changed repeatedly while a 163-page run was in
    # flight, so a page built at minute 5 does not carry a fix committed at minute 40.
    # Re-running the whole corpus to catch that is hours; asking which pages are actually
    # behind their inputs is seconds. mtime is the right comparison here because every
    # writer in this repo writes through os.replace, so a page's mtime is the moment its
    # bytes were produced.
    if "--stale" in sys.argv:
        gen = max(os.path.getmtime(os.path.join(SSOT, f))
                  for f in ("paper_projector.py", "build_app_v2.py", "build_tabbed.py"))
        def _is_current(pg):
            """A page is CURRENT when its bytes are at least as new as everything that
            produces them. Stated as the positive property on purpose: `if not
            os.path.exists(dst): continue` inside the loop is the shape
            `audit_exclusion_by_absence.py` refuses, and it is right to -- a per-item
            absence test reads as "skip this one" where what the caller needs to know is
            "which pages are behind their inputs".
            """
            dst = os.path.join(REPO, pg)
            src = os.path.join(REPO, page_map[pg].replace("/", os.sep))
            newest_input = max(gen, os.path.getmtime(src)) if os.path.exists(src) else gen
            return os.path.exists(dst) and os.path.getmtime(dst) >= newest_input

        stale = [pg for pg in pages if not _is_current(pg)]
        print("  --stale: %d of %d pages are older than their object or the generator"
              % (len(stale), len(pages)))
        pages = stale
        if not pages:
            print("  nothing stale. Every page is at least as new as its inputs.")
            return 0

    # THE POSITIVE PROPERTY, ASSERTED ONCE, BEFORE THE LOOP.
    #
    # This began as `if not os.path.exists(obj): continue` inside the loop, and the
    # pre-commit gate `audit_exclusion_by_absence.py` refused the commit for it. It was
    # right, and the reason is this repo's own history: a per-item skip states a NEGATIVE
    # property ("this one had no object") once per item, where the thing worth knowing is
    # the POSITIVE one -- EVERY page in PAGE_MAP resolves to an object that exists. A run
    # that skips four pages and reports 153 OK looks identical to a run that covered
    # everything, which is how a coverage gap survives a green report.
    #
    # Asserted here it fails LOUDLY and BEFORE any build, naming every unresolved page.
    unresolved = [p for p in pages
                  if not os.path.exists(os.path.join(REPO, page_map[p].replace("/", os.sep)))]
    if unresolved:
        sys.exit("REFUSED: %d of %d pages in PAGE_MAP name an object that does not exist "
                 "on disk. Nothing has been built.\n    %s"
                 % (len(unresolved), len(pages), "\n    ".join(unresolved)))
    print("  precondition: all %d pages resolve to an object on disk." % len(pages))

    workers = 1
    for a in sys.argv[1:]:
        if a.startswith("--workers"):
            workers = max(1, int(a.split("=")[1]) if "=" in a else 1)
    print("  free on C: %.1f GB   F: %.1f GB   workers=%d"
          % (shutil.disk_usage("C:\\").free / 2**30,
             shutil.disk_usage(REPO).free / 2**30, workers))

    def one(page):
        obj = os.path.join(REPO, page_map[page].replace("/", os.sep))
        dst = os.path.join(REPO, page)
        if os.path.exists(dst):
            shutil.copy2(dst, os.path.join(BACKUP, page))
        before = GATE.findings_for(dst, open(dst, encoding="utf-8", errors="replace").read(),
                                   GATE.slugs_of(page)) if os.path.exists(dst) else []
        r = subprocess.run([sys.executable, "build_tabbed.py", obj, dst],
                           cwd=SSOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            return {"page": page, "state": "BUILD_FAILED",
                    "tail": r.stdout.decode("utf-8", "replace")[-400:]}
        after = GATE.findings_for(dst, open(dst, encoding="utf-8", errors="replace").read(),
                                  GATE.slugs_of(page))
        return {"page": page, "state": "OK" if not after else "STILL_BLOCKED",
                "before": [c for c, _ in before], "after": [c for c, _ in after]}

    rows = []
    t0 = time.time()
    if workers == 1:
        it = ((p, one(p)) for p in pages)
        for i, (page, row) in enumerate(it, 1):
            rows.append(row)
            print("  [%3d/%d] %-52s %s" % (i, len(pages), page, _fmt(row)))
            _flush(LEDGER, t0, rows, len(pages))
    else:
        # as_completed, NOT map. `ex.map` yields IN SUBMISSION ORDER, so one slow item
        # holds back every result behind it: MALARIA_VACCINES_REVIEW is a 7.5 MB page that
        # took over 30 minutes, and while it ran the ledger sat frozen at 109 of 163 even
        # though three other workers had raced on to the R's. A progress file that stalls
        # for half an hour on a healthy job is indistinguishable from a hung one -- which
        # is the same failure as the 0-byte log, in a second place.
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(one, pg): pg for pg in pages}
            for i, fut in enumerate(as_completed(futs), 1):
                try:
                    row = fut.result()
                except Exception as exc:                       # noqa: BLE001
                    row = {"page": futs[fut], "state": "BUILD_FAILED",
                           "tail": "driver exception: %r" % (exc,)}
                rows.append(row)
                print("  [%3d/%d] %-52s %s" % (i, len(pages), row["page"], _fmt(row)))
                _flush(LEDGER, t0, rows, len(pages))
    print("  free on C: %.1f GB after the run" % (shutil.disk_usage("C:\\").free / 2**30))

    ok = sum(1 for r in rows if r["state"] == "OK")
    still = [r for r in rows if r["state"] == "STILL_BLOCKED"]
    bad = [r for r in rows if r["state"] == "BUILD_FAILED"]
    fixed = sum(1 for r in rows if r.get("before") and not r.get("after"))
    print("\nrebuilt %d pages in %d min" % (len(rows), (time.time() - t0) / 60))
    print("  clean after rebuild : %d" % ok)
    print("  were blocked, now clean: %d" % fixed)
    print("  STILL BLOCKED       : %d" % len(still))
    for r in still[:25]:
        print("      %-52s %s" % (r["page"], ",".join(r["after"])))
    print("  build failed/missing: %d" % len(bad))
    for r in bad[:15]:
        print("      %-52s %s" % (r["page"], r["state"]))
    return 1 if (still or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
