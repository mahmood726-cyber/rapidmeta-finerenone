# -*- coding: utf-8 -*-
"""Detached overnight job: multi-route full-text retrieval for every trial we can name.

RUNS WITHOUT A LANE ALIVE. No orchestration, no model calls, no store writes. It reads the
trial list this lane already produced, retrieves through every route in order, saves what it
gets, and writes its own report and completion marker so the result can be read from the file
tomorrow by someone who was not here.

RESUMABLE AND HONEST ABOUT PROGRESS. One JSONL row per trial, flushed immediately, so the
output file GROWS while it works -- a job that silently no-ops is otherwise indistinguishable
from one that is running, which is the failure shape this project has hit five times.

WHAT IT WILL NOT DO. It does not judge, it does not write to any store, and it does not record
a document as unreachable on one index's say-so: every route is tried and each attempt keeps
its status. "Retrieved" means a route returned at least MIN_TEXT rendered characters -- HTTP
200 is not enough, because NCBI efetch returns 200 for a PMCID that cannot exist.
"""
import collections
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, HERE)
import multiroute_retrieve as MR  # noqa: E402

OUT_DIR = r"F:\claude-temp\pend\out"
TEXT_DIR = os.path.join(OUT_DIR, "fulltext")
JSONL = os.path.join(OUT_DIR, "fulltext_harvest.jsonl")
REPORT = os.path.join(OUT_DIR, "FULLTEXT-HARVEST-REPORT.md")
DONE = os.path.join(OUT_DIR, "FULLTEXT-HARVEST.DONE")
SRC = r"F:\claude-temp\pend\funder_retrievability.jsonl"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    os.makedirs(TEXT_DIR, exist_ok=True)
    rows = []
    for ln in io.open(SRC, encoding="utf-8"):
        if ln.strip():
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    targets = [r for r in rows if r.get("pmcid")]
    print("trials with a funder class      %4d" % len(rows))
    print("of those, naming a PMC deposit  %4d  == the denominator for this job" % len(targets))
    print("with NO deposit to retrieve     %4d  <- not failures, nothing to fetch"
          % (len(rows) - len(targets)))

    done = set()
    if os.path.exists(JSONL):
        for ln in io.open(JSONL, encoding="utf-8"):
            try:
                done.add(json.loads(ln)["nct"])
            except Exception:
                pass
    todo = [r for r in targets if r["nct"] not in done]
    print("already harvested %d, harvesting %d" % (len(done), len(todo)))

    with io.open(JSONL, "a", encoding="utf-8") as fh:
        for i, r in enumerate(todo, 1):
            dest = os.path.join(TEXT_DIR, "%s_%s.xml" % (r["nct"], r["pmcid"]))
            rec = MR.retrieve(pmcid=r["pmcid"], out_dir=OUT_DIR, save_as=dest)
            fh.write(json.dumps({"nct": r["nct"], "funder": r.get("funder"),
                                 "pmcid": r["pmcid"], "route": rec.get("route"),
                                 "rendered_chars": rec.get("rendered_chars"),
                                 "attempts": rec.get("attempts"),
                                 "saved_to": rec.get("saved_to")}) + "\n")
            fh.flush()
            if i % 25 == 0:
                print("  %d/%d" % (i, len(todo)))
            time.sleep(0.3)

    all_rows = [json.loads(l) for l in io.open(JSONL, encoding="utf-8") if l.strip()]
    byroute = collections.Counter(r.get("route") or "NONE" for r in all_rows)
    byfund = collections.defaultdict(lambda: collections.Counter())
    for r in all_rows:
        c = byfund[r.get("funder") or "UNKNOWN"]
        c["n"] += 1
        c["got"] += 1 if r.get("route") else 0
    got = sum(1 for r in all_rows if r.get("route"))
    with io.open(REPORT, "w", encoding="utf-8") as f:
        f.write("# Full-text harvest, multi-route — overnight 28→29 Aug\n\n")
        f.write("Detached job. No model calls, no store writes, no judgement.\n\n")
        f.write("- trials with a funder class: **%d**\n" % len(rows))
        f.write("- of those naming a PMC deposit: **%d** == the denominator\n" % len(targets))
        f.write("- with no deposit to retrieve: **%d** (not failures — nothing to fetch)\n"
                % (len(rows) - len(targets)))
        f.write("- attempted: **%d**\n- **full text retrieved: %d (%.0f%%)**\n\n"
                % (len(all_rows), got, 100.0 * got / len(all_rows) if all_rows else 0))
        f.write("## By route that succeeded\n\n| route | n |\n|---|---|\n")
        for k, v in byroute.most_common():
            f.write("| %s | %d |\n" % (k, v))
        f.write("\n## By funder class\n\n| funder | n | retrieved | % |\n|---|---|---|---|\n")
        for k in sorted(byfund, key=lambda x: -byfund[x]["n"]):
            c = byfund[k]
            f.write("| %s | %d | %d | %.0f%% |\n"
                    % (k, c["n"], c["got"], 100.0 * c["got"] / c["n"] if c["n"] else 0))
        f.write("\n⚠️ **Retrieved means a document arrived, not that it answers a domain.** "
                "'Answerable' is not 'answered'.\n")
        f.write("\n⚠️ **A route returning HTTP 200 is not evidence of a document** — NCBI "
                "efetch returns 200 for a PMCID that cannot exist. Every hit here cleared a "
                "rendered-text floor of %d characters.\n" % MR.MIN_TEXT)
    io.open(DONE, "w", encoding="utf-8").write(
        "completed %d of %d\n" % (len(all_rows), len(targets)))
    print("report -> %s" % REPORT)
    print("marker -> %s" % DONE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
