"""Do these registrations actually have POSTED RESULTS? One pass, so bucket 2 has a size.

WHY THIS RUNS BEFORE ANYONE PRICES THE WORK. Bucket 2 -- arm-level event counts, follow-up
duration, harms -- is the only thing standing between these reviews and clinical usefulness,
and it splits cleanly in two: a registration WITH posted results carries all three as
structured data (automatable), and one WITHOUT carries none of them, so a person must open
the paper and transcribe (irreducible).

The corpus records evidence of a results posting for 124 of 157 trials and says nothing
about the other 33. NOTHING ABOUT is not the same as NOT POSTED -- this pipeline never
asked. Costing 33 trials of manual extraction against a denominator nobody measured is how
this session already produced one badly wrong estimate (a 90-minute job reported as 15.7
hours), and the fix then was the same as the fix now: measure the denominator first.

WHAT IT ASKS, AND WHAT IT DOES NOT. `hasResults` from the ClinicalTrials.gov v2 API, plus
the primary-outcome time frame and the enrolment count, which are the follow-up and
denominator fields bucket 2 wants and which exist on the PROTOCOL section whether or not
results were ever posted. It writes a JSON ledger and changes no object: this is a
measurement, and applying it is a separate decision.

CACHED AND RESUMABLE. Every response is written to disk before the next request, so an
interrupted run resumes instead of restarting, and a rerun costs nothing. Rate-limited to
one request every 0.4s with bounded retries -- an API that starts refusing must not be
hammered, and a 429 must not be recorded as "no results".

AN ERROR IS RECORDED AS AN ERROR. A request that fails is stored as `"error"`, never as
`hasResults: false`. A network failure counted as a negative finding is the silence-as-
success family this repo has spent the day on: it would quietly move trials from the
automatable column into the manual one and inflate the estimate nobody could then check.
"""
import glob
import io
import json
import os
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "outputs", "ctgov_results_probe_cache.json")
OUT = os.path.join(REPO, "outputs", "ctgov_results_probe_2026_08_24.json")
FIELDS = ",".join([
    "protocolSection.identificationModule.nctId",
    "protocolSection.designModule.enrollmentInfo",
    "protocolSection.outcomesModule.primaryOutcomes",
    "hasResults",
])
PAUSE = 0.4


def ab_trials():
    """Every trial on a topic that holds at least one readable estimate."""
    out = {}
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        # POSITIVE FORM THROUGHOUT. `audit_exclusion_by_absence --gate` refuses a loop that
        # defines its subject by what it skips, and the reason applies exactly here: this
        # probe exists to produce a DENOMINATOR, and a loop that `continue`s past the cases
        # it does not like cannot tell you how many there were. Comprehensions that state
        # what a member IS leave the counts visible.
        blocks = [b for b in ((obj.get("results") or {}).get("by_outcome") or {}).values()
                  if isinstance(b, dict)]
        readable = [r for b in blocks for r in (b.get("per_trial") or [])
                    if isinstance(r, dict) and r.get("point") is not None]
        if readable:
            trials = [t for t in ((obj.get("inputs") or {}).get("trials") or [])
                      if isinstance(t, dict)]
            for nct in [str(t.get("nct") or "").strip() for t in trials]:
                if nct.upper().startswith("NCT"):
                    out.setdefault(nct, []).append(slug)
    return out


def fetch(nct, tries=3):
    url = ("https://clinicaltrials.gov/api/v2/studies/%s?fields=%s" % (nct, FIELDS))
    delay = 1.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-probe"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"_error": "404 not found"}
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            return {"_error": "HTTP %s" % e.code}
        except Exception as e:              # noqa: BLE001 -- recorded, never silent
            if attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            return {"_error": "%s: %s" % (type(e).__name__, str(e)[:90])}
    return {"_error": "exhausted retries"}


def main():
    trials = ab_trials()
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(io.open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}

    todo = [n for n in sorted(trials) if n not in cache]
    print("A/B trials with an NCT : %d" % len(trials))
    print("already cached         : %d" % (len(trials) - len(todo)))
    print("to fetch               : %d" % len(todo))
    for i, nct in enumerate(todo, 1):
        cache[nct] = fetch(nct)
        # WRITTEN BEFORE THE NEXT REQUEST, so an interrupted run resumes.
        io.open(CACHE, "w", encoding="utf-8").write(
            json.dumps(cache, ensure_ascii=False, indent=1))
        state = ("ERROR " + cache[nct]["_error"]) if "_error" in cache[nct] \
            else ("results posted" if cache[nct].get("hasResults") else "NO results posted")
        print("[%3d/%d] %-12s %s" % (i, len(todo), nct, state), flush=True)
        time.sleep(PAUSE)

    posted, none, errors = [], [], []
    followup = enrolment = 0
    for nct in sorted(trials):
        rec = cache.get(nct) or {}
        if "_error" in rec:
            errors.append((nct, rec["_error"]))
            continue
        if rec.get("hasResults"):
            posted.append(nct)
        else:
            none.append(nct)
        proto = rec.get("protocolSection") or {}
        if ((proto.get("designModule") or {}).get("enrollmentInfo") or {}).get("count"):
            enrolment += 1
        prim = (proto.get("outcomesModule") or {}).get("primaryOutcomes") or []
        if any(o.get("timeFrame") for o in prim if isinstance(o, dict)):
            followup += 1

    L = ["CLINICALTRIALS.GOV RESULTS-POSTING PROBE — %d A/B trials with an NCT" % len(trials),
         "",
         "  results POSTED (arm counts, follow-up, adverse events are structured data)"
         "  : %d" % len(posted),
         "  NO results posted (a person must read the published report)"
         "               : %d" % len(none),
         "  could not be determined (recorded as errors, NOT as absent results)"
         "       : %d" % len(errors),
         "",
         "  primary-outcome TIME FRAME available on the protocol record : %d" % followup,
         "  enrolment count available on the protocol record            : %d" % enrolment,
         "",
         "FOLLOW-UP DURATION is on the PROTOCOL record, which every registration has,",
         "whether or not results were ever posted. It does not depend on this split at all.",
         ""]
    if none:
        L.append("TRIALS WITH NO POSTED RESULTS — the manual residue of bucket 2:")
        for n in none:
            L.append("   %-12s %s" % (n, ", ".join(sorted(set(trials[n])))[:60]))
        L.append("")
    if errors:
        L.append("UNDETERMINED (must be re-probed before any estimate is quoted):")
        for n, why in errors:
            L.append("   %-12s %s" % (n, why))

    io.open(OUT, "w", encoding="utf-8").write(json.dumps(
        {"trials": {n: {"topics": sorted(set(trials[n])),
                        "hasResults": (cache.get(n) or {}).get("hasResults"),
                        "error": (cache.get(n) or {}).get("_error")}
                    for n in sorted(trials)},
         "posted": len(posted), "not_posted": len(none), "undetermined": len(errors)},
        ensure_ascii=False, indent=1))
    io.open(os.path.join(REPO, "outputs", "bucket2_probe_2026_08_24.txt"),
            "w", encoding="utf-8").write("\n".join(L))
    print()
    print("\n".join(L))


main()
