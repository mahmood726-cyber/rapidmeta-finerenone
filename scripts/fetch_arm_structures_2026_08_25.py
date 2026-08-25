"""Fetch registered ARM STRUCTURE for every NCT id the corpus names, and cache it.

WHY THIS EXISTS. The trial-identity rule in ssot/trial_identity.py decides whether a trial
studies a topic's drug by reading which ARM each intervention sits in. Nothing in the corpus
stores that: the objects keep a trial's official title and sometimes its conditions, and the
matcher's own source (AACT) is not on this machine and now sits behind a login.

ClinicalTrials.gov API v2 returns exactly what is needed, publicly and without credentials:

    GET /api/v2/studies/<NCT>?fields=protocolSection.armsInterventionsModule

~2 KB per trial, 349 distinct ids across the corpus.

A FETCH FAILURE IS A FAILURE, NEVER AN ABSENCE. This is the same rule as "a network error
must not become hasResults: false". A trial whose fetch errors is recorded with status
"error" and its message; it is NEVER written as an empty arm list, because downstream
`studies_subject` treats an empty arm list as "structure unknown, do not judge" and a
silently-empty record would be indistinguishable from a trial that genuinely has no arms
registered. One means "we could not look", the other means "there is nothing there", and
conflating them is how a gate learns to pass everything.

POLITE. Sequential, with a delay between calls, and CACHED: a re-run reads the cache and
issues no request for anything already held. Re-running this is cheap and safe.
"""
import io
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "outputs", "arm_structures_cache.jsonl")
API = ("https://clinicaltrials.gov/api/v2/studies/%s"
       "?fields=protocolSection.armsInterventionsModule,"
       "protocolSection.identificationModule")
DELAY = 0.4          # seconds between requests


def load_cache():
    cache = {}
    if os.path.exists(CACHE):
        for line in io.open(CACHE, encoding="utf-8"):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("nct"):
                cache[d["nct"]] = d
    return cache


def corpus_ncts():
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    out = {}
    for page, rel in sorted(pmap.items()):
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        try:
            o = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        for t in ((o.get("inputs") or {}).get("trials") or []):
            if not isinstance(t, dict):
                continue
            n = t.get("nct") or t.get("trial_id")
            if isinstance(n, str) and n.upper().startswith("NCT"):
                out.setdefault(n.strip(), []).append(page)
    return out


def fetch(nct):
    """(record, ok). Never returns an empty-arms record for a failed fetch."""
    try:
        p = subprocess.run(["curl", "-s", "-m", "45", "-w", "\\n%{http_code}", API % nct],
                           capture_output=True, timeout=60)
        raw = (p.stdout or b"").decode("utf-8", "replace")
    except Exception as e:
        return {"nct": nct, "status": "error", "error": "%s: %s" % (type(e).__name__, e)}, False
    if "\n" not in raw:
        return {"nct": nct, "status": "error", "error": "no response body"}, False
    body, code = raw.rsplit("\n", 1)
    code = code.strip()
    if code != "200":
        return {"nct": nct, "status": "error", "error": "HTTP %s" % code}, False
    try:
        d = json.loads(body)
    except ValueError:
        return {"nct": nct, "status": "error", "error": "response was not JSON"}, False
    ps = d.get("protocolSection") or {}
    mod = ps.get("armsInterventionsModule") or {}
    groups = []
    for a in (mod.get("armGroups") or []):
        groups.append({"type": (a.get("type") or "").upper(),
                       "label": a.get("label"),
                       "interventionNames": a.get("interventionNames") or []})
    return {"nct": nct, "status": "ok",
            "title": (ps.get("identificationModule") or {}).get("briefTitle"),
            "armGroups": groups,
            # DISTINCT from a failed fetch. This trial really registers no arm groups.
            "no_arms_registered": len(groups) == 0}, True


def main():
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    want = corpus_ncts()
    cache = load_cache()
    todo = [n for n in sorted(want) if n not in cache or cache[n].get("status") != "ok"]

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("NCT ids named by the corpus : %d" % len(want))
    log("already cached OK           : %d" % sum(1 for n in want if cache.get(n, {}).get("status") == "ok"))
    log("to fetch                    : %d   (delay %.1fs, sequential)" % (len(todo), DELAY))
    ok = err = 0
    for i, nct in enumerate(todo, 1):
        rec, good = fetch(nct)
        with io.open(CACHE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if good:
            ok += 1
        else:
            err += 1
            log("  [%3d/%d] %-12s ERROR %s" % (i, len(todo), nct, rec.get("error")))
        if i % 25 == 0:
            log("  [%3d/%d] ok=%d err=%d" % (i, len(todo), ok, err))
        time.sleep(DELAY)

    cache = load_cache()
    good = [n for n in want if cache.get(n, {}).get("status") == "ok"]
    noarms = [n for n in good if cache[n].get("no_arms_registered")]
    failed = [n for n in want if cache.get(n, {}).get("status") != "ok"]
    log("")
    log("cached OK                    : %d of %d" % (len(good), len(want)))
    log("  of those, no arms REGISTERED (a real property, not a fetch failure): %d" % len(noarms))
    log("fetch FAILED or never fetched: %d   <- recorded as failures, never as 'no arms'"
        % len(failed))
    for n in failed[:15]:
        log("     %-12s %s" % (n, cache.get(n, {}).get("error", "not attempted")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
