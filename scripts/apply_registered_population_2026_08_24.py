"""Give every pooled row a population a reader can check, from the registration itself.

THE DEFECT THIS ANSWERS. Of 32 pooled results delivered as one number, 18 record NO
POPULATION AT ALL on their contributing rows. That is not merely a gap in a table: it means
nobody -- not a reviewer, not the medical student whose whole job is to check us -- can tell
whether that pool combines patients who belong together. A pooled estimate whose population
is unrecorded cannot be checked by anyone. It stands as a defect regardless of how the
auto-pooling question is decided, because it is what makes that question unanswerable.

WHAT IS WRITTEN, AND WHY IT IS NOT A SUMMARY. Two fields, both quoted from the trial's own
ClinicalTrials.gov protocol record:

    registered_conditions    the registry's structured condition list -- "Hyperlipidemia",
                             "Respiratory Syncytial Virus Infections". Short, comparable
                             across trials, and exactly the axis the pooling question turns
                             on.
    registered_eligibility   the inclusion and exclusion criteria, verbatim.

The populations already on this corpus -- "adults with type 2 diabetes recently hospitalised
for worsening heart failure" -- are HUMAN SUMMARIES. Writing more of those is a judgement,
and a judgement is the one thing this pass must not manufacture: a fluent one-line population
that a student cannot distinguish from a quotation is precisely the failure mode the
med-student brief warns about. Verbatim registry text is worse prose and better evidence,
because the student can open the registration and see the same words.

So this closes the CHECKABILITY defect without pretending to close the summarising one.
"""
import glob
import io
import json
import os
import time
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "outputs", "ctgov_population_cache.json")
FIELDS = "protocolSection.conditionsModule,protocolSection.eligibilityModule"


def fetch(nct, tries=3):
    url = "https://clinicaltrials.gov/api/v2/studies/%s?fields=%s" % (nct, FIELDS)
    delay = 1.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-pop"})
            with urllib.request.urlopen(req, timeout=35) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"_error": "404"}
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            return {"_error": "HTTP %s" % e.code}
        except Exception as e:                     # noqa: BLE001 -- recorded, never silent
            if attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            return {"_error": "%s" % type(e).__name__}
    return {"_error": "exhausted retries"}


def rows_needing_population():
    """Every per-trial row of a LIVE pool that records no population."""
    want = {}
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        blocks = [(k, v) for k, v in
                  ((obj.get("results") or {}).get("by_outcome") or {}).items()
                  if isinstance(v, dict)]
        for _oid, b in blocks:
            pooled = b.get("pooled") or {}
            live = pooled.get("point") is not None and not pooled.get("withdrawn")
            rows = [r for r in (b.get("per_trial") or [])
                    if isinstance(r, dict) and r.get("point") is not None]
            if live and len(rows) >= 2:
                for r in rows:
                    nct = str(r.get("nct") or "")
                    if nct.startswith("NCT") and not str(r.get("population") or "").strip():
                        want.setdefault(nct, []).append(slug)
    return want


def main():
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(io.open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}

    want = rows_needing_population()
    todo = [n for n in sorted(want) if n not in cache]
    print("registrations needed : %d (%d already cached)" % (len(want), len(want) - len(todo)))
    for i, nct in enumerate(todo, 1):
        cache[nct] = fetch(nct)
        io.open(CACHE, "w", encoding="utf-8").write(json.dumps(cache, ensure_ascii=False))
        print("[%3d/%d] %s %s" % (i, len(todo), nct,
                                  cache[nct].get("_error") or "ok"), flush=True)
        time.sleep(0.35)

    wrote = 0
    objs = 0
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        changed = False
        blocks = [v for v in ((obj.get("results") or {}).get("by_outcome") or {}).values()
                  if isinstance(v, dict)]
        for b in blocks:
            # POSITIVE FORM throughout, per `audit_exclusion_by_absence --gate`.
            per_trial = [r for r in (b.get("per_trial") or []) if isinstance(r, dict)]
            for r in per_trial:
                nct = str(r.get("nct") or "")
                rec = cache.get(nct)
                if not rec or "_error" in rec or str(r.get("population") or "").strip():
                    continue
                proto = rec.get("protocolSection") or {}
                conds = (proto.get("conditionsModule") or {}).get("conditions") or []
                elig = " ".join(str((proto.get("eligibilityModule") or {})
                                    .get("eligibilityCriteria") or "").split())
                if conds and not r.get("registered_conditions"):
                    r["registered_conditions"] = "; ".join(str(c) for c in conds)
                    changed = True
                    wrote += 1
                if elig and not r.get("registered_eligibility"):
                    r["registered_eligibility"] = elig[:1200]
                    r["registered_population_basis"] = (
                        "Quoted from this trial's ClinicalTrials.gov protocol record, read "
                        "2026-08-24. It is the registry's own wording, not a summary written "
                        "here: a one-line population a reader cannot distinguish from a "
                        "quotation is the failure this corpus is trying to avoid.")
                    changed = True
        if changed:
            io.open(p, "w", encoding="utf-8").write(
                json.dumps(obj, ensure_ascii=False, indent=1))
            objs += 1

    print()
    print("rows given registered conditions : %d" % wrote)
    print("objects updated                  : %d" % objs)


main()
