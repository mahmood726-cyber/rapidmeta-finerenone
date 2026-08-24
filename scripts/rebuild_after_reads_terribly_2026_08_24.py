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
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
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


def _flush(path, t0, rows):
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump({"elapsed_s": round(time.time() - t0), "rows": rows}, fh, indent=2)


def main():
    if not GATE.run_controls():
        sys.exit("REFUSED: the gate's own controls failed, so nothing it says is evidence.")

    page_map = json.load(open(os.path.join(SSOT, "PAGE_MAP.json"), encoding="utf-8"))
    os.makedirs(BACKUP, exist_ok=True)
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    pages = sorted(only) if only else sorted(page_map)

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
            _flush(LEDGER, t0, rows)
    else:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for i, row in enumerate(ex.map(one, pages), 1):
                rows.append(row)
                print("  [%3d/%d] %-52s %s" % (i, len(pages), row["page"], _fmt(row)))
                _flush(LEDGER, t0, rows)
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
