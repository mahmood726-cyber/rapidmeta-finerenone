"""Rebuild every PAGE_MAP page after the reads-terribly repair, one at a time, and gate it.

SEQUENTIAL BY INSTRUCTION. Another lane is reclaiming disk and C: was full this morning, so
this runs one build at a time and writes nothing to C:. A parallel fan-out here would race
that lane for space during a 157-page run.

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


def main():
    if not GATE.run_controls():
        sys.exit("REFUSED: the gate's own controls failed, so nothing it says is evidence.")

    page_map = json.load(open(os.path.join(SSOT, "PAGE_MAP.json"), encoding="utf-8"))
    os.makedirs(BACKUP, exist_ok=True)
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    pages = sorted(only) if only else sorted(page_map)

    rows = []
    t0 = time.time()
    for i, page in enumerate(pages, 1):
        obj = os.path.join(REPO, page_map[page].replace("/", os.sep))
        dst = os.path.join(REPO, page)
        if not os.path.exists(obj):
            rows.append({"page": page, "state": "OBJECT_MISSING"})
            print("  [%3d/%d] %-52s OBJECT MISSING" % (i, len(pages), page))
            continue
        if os.path.exists(dst):
            shutil.copy2(dst, os.path.join(BACKUP, page))
        before = GATE.findings_for(dst, open(dst, encoding="utf-8", errors="replace").read(),
                                   page.lower().replace("_", "-")) if os.path.exists(dst) else []
        r = subprocess.run([sys.executable, "build_tabbed.py", obj, dst],
                           cwd=SSOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            rows.append({"page": page, "state": "BUILD_FAILED",
                         "tail": r.stdout.decode("utf-8", "replace")[-400:]})
            print("  [%3d/%d] %-52s BUILD FAILED" % (i, len(pages), page))
            continue
        after = GATE.findings_for(dst, open(dst, encoding="utf-8", errors="replace").read(),
                                  page.lower().replace("_", "-"))
        rows.append({"page": page, "state": "OK" if not after else "STILL_BLOCKED",
                     "before": [c for c, _ in before], "after": [c for c, _ in after]})
        print("  [%3d/%d] %-52s %2d -> %2d  %s"
              % (i, len(pages), page, len(before), len(after),
                 "clean" if not after else ",".join(c for c, _ in after)))
        with io.open(LEDGER, "w", encoding="utf-8") as fh:
            json.dump({"elapsed_s": round(time.time() - t0), "rows": rows}, fh, indent=2)

    ok = sum(1 for r in rows if r["state"] == "OK")
    still = [r for r in rows if r["state"] == "STILL_BLOCKED"]
    bad = [r for r in rows if r["state"] in ("BUILD_FAILED", "OBJECT_MISSING")]
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
