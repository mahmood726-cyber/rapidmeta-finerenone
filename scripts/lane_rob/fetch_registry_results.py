# -*- coding: utf-8 -*-
"""Fetch the FULL registry record -- results section included -- for every trial we hold a paper for.

WHY THIS IS A SEPARATE STEP. The local cache holds 1,267 registry records and only 11 of them
carry a results section: the cache was built protocol-only. So a registry-versus-publication
comparison cannot run against it, and running one anyway would have produced "306 trials
matched" out of 306 trials where the registry side was simply absent -- a denominator made of
nothing, which is the defect this project has hit most often.

RESUMABLE, one JSON per trial on disk, and it records what it did NOT get rather than dropping
it. A trial whose registry record carries no results is a real state ("results never posted"),
distinct from a fetch that failed, and the two are counted separately.
"""
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
OUT = r"F:\claude-temp\pend\out\registry_full"
POP = r"F:\claude-temp\pend\out\regpub_population.json"
LOG = r"F:\claude-temp\pend\out\registry_fetch.jsonl"
DONE = r"F:\claude-temp\pend\out\REGISTRY-FETCH.DONE"


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    os.makedirs(OUT, exist_ok=True)
    pop = json.load(io.open(POP, encoding="utf-8"))
    ncts = pop["both"]
    done = set()
    if os.path.exists(LOG):
        for ln in io.open(LOG, encoding="utf-8"):
            try:
                done.add(json.loads(ln)["nct"])
            except Exception:
                pass
    todo = [n for n in ncts if n not in done]
    print("trials in scope %d, already fetched %d, fetching %d" % (len(ncts), len(done), len(todo)))
    with io.open(LOG, "a", encoding="utf-8") as fh:
        for i, n in enumerate(todo, 1):
            dest = os.path.join(OUT, n + ".json")
            r = subprocess.run(
                ["curl", "-s", "--max-time", "60", "-o", dest,
                 "-w", "%{http_code}|%{size_download}",
                 "https://clinicaltrials.gov/api/v2/studies/%s" % n],
                capture_output=True, timeout=120)
            code, _, size = r.stdout.decode("ascii", "replace").partition("|")
            has_results = False
            try:
                d = json.load(io.open(dest, encoding="utf-8"))
                has_results = bool(d.get("resultsSection"))
            except Exception:
                pass
            fh.write(json.dumps({"nct": n, "http": code.strip(),
                                 "bytes": int(size or 0), "has_results": has_results}) + "\n")
            fh.flush()
            if i % 25 == 0:
                print("  %d/%d" % (i, len(todo)))
            time.sleep(0.25)
    rows = [json.loads(l) for l in io.open(LOG, encoding="utf-8") if l.strip()]
    ok = sum(1 for r in rows if r["http"] == "200")
    res = sum(1 for r in rows if r["has_results"])
    io.open(DONE, "w", encoding="utf-8").write(
        "fetched %d of %d; http200 %d; carry a results section %d\n"
        % (len(rows), len(ncts), ok, res))
    print("fetched %d | http200 %d | WITH results %d | results never posted %d"
          % (len(rows), ok, res, ok - res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
