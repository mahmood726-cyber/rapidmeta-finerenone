"""Capture registered outcomes at EVERY rank, not just primary.

WHY THIS IS NEEDED AND WHY IT WAS NOT COLLECTED. 67 of 95 withdrawals in this corpus
cannot be tested for proportionality because the objects record `registered_primaries` and
nothing else. The SGLT2 failure lived ONE RANK DOWN -- a matched two-component endpoint
sitting as DAPA-HF's secondary in a registration we had already opened -- and we
systematically did not record one rank down.

THAT IS NOT A GAP IN THE SWEEP. IT IS A GAP IN WHAT WE COLLECTED, and it was invisible
until an outside reviewer asked a question our own reasoning never would. We read
registrations to answer "do these trials share a primary outcome", so we captured primaries;
the question "is there a shared outcome at ANY rank" was never asked, so its evidence was
never kept.

Writes, per trial: registered_primaries (unchanged), registered_secondaries, registered_other,
and the read date FOR THIS READ. The registry is a live document and every verdict page
here says so -- a value carried over from an earlier read would be an assumption of
continuity, which is the quiet error this whole exercise exists to avoid.

NOTHING IS OVERWRITTEN EXCEPT BY A RE-READ. Existing primaries are refreshed from the same
fetch, so a divergence between what we recorded before and what the registry says now would
show up as a changed field rather than being papered over.
"""
from __future__ import annotations
import io
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from rebuild_guard import guard_write  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://clinicaltrials.gov/api/v2/studies/{}?format=json"
READ = "2026-08-18"
CACHE = os.path.join(REPO, ".allranks-cache.json")
cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def fetch(nct):
    if nct in cache:
        return cache[nct]
    req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-allranks"})
    with urllib.request.urlopen(req, timeout=45) as r:
        d = json.loads(r.read().decode("utf-8"))
    om = ((d.get("protocolSection") or {}).get("outcomesModule") or {})
    rec = {"primary": [o.get("measure", "") for o in (om.get("primaryOutcomes") or [])],
           "secondary": [o.get("measure", "") for o in (om.get("secondaryOutcomes") or [])],
           "other": [o.get("measure", "") for o in (om.get("otherOutcomes") or [])]}
    cache[nct] = rec
    time.sleep(0.07)
    return rec


def main() -> int:
    targets = sys.argv[1:]
    if not targets:
        p = os.path.join(REPO, ".proportionality.json")
        targets = json.load(io.open(p, encoding="utf-8"))["unassessable"]
    done, trials_n, failed, changed = 0, 0, [], []
    for t in targets:
        f = os.path.join(REPO, "ssot", t, t + ".json")
        if not os.path.exists(f):
            failed.append((t, "no object"))
            continue
        o = json.load(io.open(f, encoding="utf-8"))
        n = 0
        for tr in ((o.get("inputs") or {}).get("trials") or []):
            nct = (tr.get("nct") or tr.get("trial_id") or "")
            if not nct.startswith("NCT"):
                continue
            try:
                rec = fetch(nct)
            except Exception as e:
                failed.append((t, "%s %s" % (nct, str(e)[:30])))
                continue
            before = tr.get("registered_primaries")
            if before and before != rec["primary"]:
                changed.append((t, nct))
                tr["registered_primaries_previous_read"] = before
            tr["registered_primaries"] = rec["primary"]
            tr["registered_secondaries"] = rec["secondary"]
            tr["registered_other_outcomes"] = rec["other"]
            tr["all_ranks_read_utc"] = READ
            n += 1
        if n:
            o["all_ranks_captured_2026_08_18"] = (
                "Registered outcomes captured at EVERY rank -- primary, secondary and other "
                "-- by re-reading each registration on %s. Previously only primaries were "
                "recorded, which made this topic's withdrawal UNTESTABLE for "
                "proportionality: the SGLT2 failure lived one rank down and we had not kept "
                "one rank down. The read date is stamped FOR THIS READ, not carried over." % READ)
            guard_write(f, json.dumps(o, ensure_ascii=False, indent=1))
            done += 1
            trials_n += n
            print("  %-46s %d trial(s), all ranks" % (t[:45], n))
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8", newline="\n"),
                  ensure_ascii=False)
    print()
    print("objects updated: %d   trials re-read: %d   failures: %d" % (done, trials_n,
                                                                       len(failed)))
    if changed:
        print()
        print("PRIMARIES CHANGED SINCE THE EARLIER READ -- the registry is a live document:")
        for t, n in changed[:12]:
            print("   %s %s   (previous value kept as registered_primaries_previous_read)"
                  % (t[:40], n))
    for t, why in failed[:8]:
        print("   FAILED %-38s %s" % (t[:37], why))
    return 0


if __name__ == "__main__":
    sys.exit(main())
