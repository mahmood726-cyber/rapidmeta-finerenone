#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Fix: when the screening filter matches zero trials (e.g. 'Show Excluded'
on an app with only confirmed-include seeds), the detail pane retains
stale content from the last-selected included trial. Makes it look like
the filter is broken.

Fix: when queue is empty after filter change, write a placeholder into
#screen-detail so the stale abstract is replaced.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

OLD = (
    "                }).join('');\n"
    "                if (queue.length > 0) this.select(Math.min(this.activeIdx, queue.length - 1));\n"
    "                this.updateMetrics();"
)

NEW = (
    "                }).join('');\n"
    "                if (queue.length > 0) {\n"
    "                    this.select(Math.min(this.activeIdx, queue.length - 1));\n"
    "                } else {\n"
    "                    /* Empty queue (e.g. 'Show Excluded' on an app with no excluded trials)\n"
    "                       — clear the detail pane so the previously-selected include doesn't\n"
    "                       linger and look like the filter is broken. */\n"
    "                    const detail = document.getElementById('screen-detail');\n"
    "                    if (detail) {\n"
    "                        const label = activeFilter === 'include' ? 'included'\n"
    "                                    : activeFilter === 'exclude' ? 'excluded'\n"
    "                                    : 'matching';\n"
    "                        const hint = activeFilter === 'exclude'\n"
    "                            ? 'Run a CT.gov/PubMed/OpenAlex search from the Search tab, or mark a trial as excluded via the Screening sign-off panel.'\n"
    "                            : activeFilter === 'include'\n"
    "                                ? 'Confirm a trial as included from the Screening sign-off panel.'\n"
    "                                : 'Seed trials via Run Precision Extractor or the search tools.';\n"
    "                        detail.innerHTML = '<div class=\"max-w-4xl mx-auto text-center text-slate-500 italic py-20\"><i class=\"fa-solid fa-filter-circle-xmark text-3xl text-slate-700 mb-4\"></i><div class=\"text-sm mb-2\">No ' + label + ' trials in scope.</div><div class=\"text-[11px] text-slate-600\">' + hint + '</div></div>';\n"
    "                    }\n"
    "                }\n"
    "                this.updateMetrics();"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if "Empty queue (e.g. 'Show Excluded'" in text:
        return f"SKIP {path.name}: already-migrated"
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    if work.count(OLD) != 1:
        return f"FAIL {path.name}: OLD matched {work.count(OLD)} times (expected 1)"
    work = work.replace(OLD, NEW, 1)
    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply): ap.error("pass --dry-run or --apply")
    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        r = apply_to_file(p, dry_run=args.dry_run)
        if r.startswith("OK"): ok += 1
        elif r.startswith("SKIP"): skip += 1
        else: fail += 1
        if not r.startswith("SKIP"): print(r)
    print(f"\nSummary: {len(targets)} | {ok} fix | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
