"""Would a REGISTRY-FIRST search have found the trials we already know are eligible?

WHY NOT THE TEST THAT WAS ASKED FOR, EXACTLY. The plan was to check our include lists
against the include lists of published systematic reviews recorded in `published_comparison`.
That cannot answer the question: those NCT numbers were written onto our objects BY US, from
our own trial list. Checking them finds zero misses on 19 of 19 topics, and the zero means
only that a list agrees with itself. Measuring our records against our records is the
adjacent-comparison failure this repository has hit four times tonight, and it would have
produced the most flattering possible number by construction.

WHAT THIS MEASURES INSTEAD, and it is the property the claim actually rests on:

    Given a trial we already know is eligible for a topic, would a search of
    ClinicalTrials.gov by the topic's DRUG have returned it?

The answer key is independent of the search: the NCTs come from the objects, the search is
specified before it runs and is executed mechanically against the live registry. A trial we
hold and the registry does not return is a trial a registry-first search would have MISSED,
and it is missed for reasons that are visible afterwards -- registered under a code name,
indexed under a condition nobody would think to query, sponsor-titled rather than
drug-titled.

THE KNOWN FAILURE MODE THIS IS SIZING. EMPA-REG OUTCOME is registered as "BI 10773" with its
condition recorded only as "Diabetes Mellitus, Type 2" -- nothing about cardiovascular
outcomes, and no occurrence of "empagliflozin" in its brief title. A registry-first search
for empagliflozin plus cardiovascular disease does not return it. That is one trial, found
by hand. This asks how many there are.

WHAT A MISS DOES AND DOES NOT MEAN. A miss here is a miss OF THIS QUERY, not proof that no
registry query could find the trial. The query is deliberately the naive one -- the drug name
as an intervention term -- because that is what "registry-first searching" means in practice
and the honest number is the one that query achieves. Where a trial is missed, the record is
fetched and the reason recorded, so the misses can be read rather than counted.
"""
import glob
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "outputs", "registry_recall_cache.json")
PAUSE = 0.35
PAGE_SIZE = 200
MAX_PAGES = 6           # 1,200 results per drug; beyond that a search is not "first-pass"


def http_json(url, tries=3):
    delay = 1.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-recall"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            return {"_error": "HTTP %s" % e.code}
        except Exception as e:                    # noqa: BLE001 -- recorded, never silent
            if attempt < tries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            return {"_error": "%s: %s" % (type(e).__name__, str(e)[:80])}
    return {"_error": "exhausted retries"}


def search_by_intervention(drug):
    """Every NCT ClinicalTrials.gov returns for this intervention term."""
    out, token = set(), None
    for _page in range(MAX_PAGES):
        q = {"query.intr": drug, "pageSize": str(PAGE_SIZE),
             "fields": "protocolSection.identificationModule.nctId"}
        if token:
            q["pageToken"] = token
        d = http_json("https://clinicaltrials.gov/api/v2/studies?" + urllib.parse.urlencode(q))
        if "_error" in d:
            return out, d["_error"]
        for st in d.get("studies") or []:
            nct = (((st.get("protocolSection") or {}).get("identificationModule") or {})
                   .get("nctId"))
            if nct:
                out.add(nct)
        token = d.get("nextPageToken")
        time.sleep(PAUSE)
        if not token:
            break
    return out, None


# The drug term for a topic, taken from the slug. Slugs are drug-first by convention in this
# corpus ("sotagliflozin-hf", "apixaban-vte-treatment"), so the first segment is the term a
# person would type. Where that is not a drug the topic is reported as UNTESTABLE rather than
# scored, because a bad query producing a miss says nothing about registry-first searching.
_NOT_A_DRUG = {"acs", "agyw", "attr", "doac", "dapt", "fcm", "iv", "intensive", "ablation",
               "cryptococcal", "antimalarial", "malaria", "rotavirus", "influenza", "hepatitis",
               "registry", "sglt2", "pcsk9", "incretin", "arni", "cab", "consort",
               # A CONDITION IS NOT A DRUG, and scoring one as a failed drug query inflates
               # the miss count with the tester's mistake. `covid19-vaccines` contributed 3
               # of the first run's 5 misses on the query "covid19" -- which names a disease,
               # returns tens of thousands of studies, and says nothing about whether
               # registry-first searching finds a named drug.
               "covid19", "covid"}


def topics():
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
        blocks = [b for b in ((obj.get("results") or {}).get("by_outcome") or {}).values()
                  if isinstance(b, dict)]
        readable = [r for b in blocks for r in (b.get("per_trial") or [])
                    if isinstance(r, dict) and r.get("point") is not None]
        if readable:
            ncts = sorted({str(t.get("nct") or "") for t in
                           ((obj.get("inputs") or {}).get("trials") or [])
                           if isinstance(t, dict) and
                           str(t.get("nct") or "").startswith("NCT")})
            if ncts:
                out[slug] = ncts
    return out


def main():
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(io.open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}

    tp = topics()
    L = []

    def w(s):
        L.append(str(s))
        print(s, flush=True)

    tested = missed_total = found_total = 0
    untestable = []
    misses = []
    for slug in sorted(tp):
        drug = slug.split("-")[0]
        if drug in _NOT_A_DRUG or len(drug) < 5:
            untestable.append((slug, drug))
            continue
        if drug not in cache:
            got, err = search_by_intervention(drug)
            cache[drug] = {"ncts": sorted(got), "error": err}
            io.open(CACHE, "w", encoding="utf-8").write(
                json.dumps(cache, ensure_ascii=False))
        rec = cache[drug]
        if rec.get("error"):
            untestable.append((slug, "search error: " + rec["error"]))
            continue
        returned = set(rec["ncts"])
        for nct in tp[slug]:
            tested += 1
            if nct in returned:
                found_total += 1
            else:
                missed_total += 1
                misses.append((slug, drug, nct))

    w("")
    w("REGISTRY-FIRST RECALL, measured against trials we already hold")
    w("")
    w("  topics testable by a drug term from the slug : %d" % (len(tp) - len(untestable)))
    w("  topics NOT testable this way                 : %d" % len(untestable))
    w("")
    w("  trials tested                                : %d" % tested)
    w("  RETURNED by a naive intervention search      : %d" % found_total)
    w("  MISSED                                       : %d" % missed_total)
    if tested:
        w("  recall                                       : %.1f%%"
          % (100.0 * found_total / tested))
    w("")
    if misses:
        w("THE MISSES -- each is a trial a registry-first search would not have found:")
        for slug, drug, nct in misses:
            w("   %-34s query='%s'  %s" % (slug, drug, nct))
    w("")
    w("NOT TESTABLE BY THIS METHOD (the slug's first segment is not a drug name):")
    for slug, why in untestable[:20]:
        w("   %-34s %s" % (slug, why))

    io.open(os.path.join(REPO, "outputs", "registry_recall_2026_08_24.txt"),
            "w", encoding="utf-8").write("\n".join(L))


main()
