"""Task 7: measure what our own design filter throws away.

THE DEFECT THIS MEASURES. Our registered searches append a randomised-trial
filter. A meta-analysis OF randomised trials was excluded by it, because its
title and abstract never use the word "randomised" -- the trials it pools are
randomised, the paper describing them need not say so. That is a live defect in
our method, not a hypothetical, and its size has never been measured.

HOW ELIGIBILITY IS DECIDED, AND WHY NOT BY ME. Asking a model whether each lost
record "should have been included" would substitute judgement for measurement and
would not be reproducible. Instead the test uses PubMed's OWN publication-type
field: a record the filter dropped that MEDLINE types as a Randomized Controlled
Trial, a Meta-Analysis, or a Systematic Review is a record our filter should have
surfaced. That is a registry-grade fact about the record, not an opinion about it.

WHAT THE RATE DIVIDES BY. Applicable rows, never corpus total: the denominator is
records the unfiltered query returned, not topics and not corpus size. Both
numerator and denominator are reported for every rate.

Codex prepared the 1,858-topic query ledger but could not execute it -- its
sandbox refuses outbound sockets (WinError 10013). This lane has network, so the
split is: Codex builds the work list, this executes it.
"""
import csv
import io
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

LEDGER = r"F:\claude-temp\rapidmeta_build_lane_2026-08-13\filter_blindspot_BLOCKED.csv"
OUT = os.path.join("outputs", "filter_blindspot_measured.json")
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PAUSE = 0.36
RETMAX = 200          # EXPLICIT. The default is 20 and would silently truncate.

# MEDLINE publication types that make a dropped record a real miss.
ELIGIBLE_PT = {"Randomized Controlled Trial", "Meta-Analysis",
               "Systematic Review", "Controlled Clinical Trial"}


def _get(url, tries=3):
    for a in range(tries):
        try:
            r = urllib.request.Request(url, headers={
                "User-Agent": "nafis-blindspot/1.0", "Accept": "application/json"})
            with urllib.request.urlopen(r, timeout=45) as h:
                b = h.read()
            if b[:1] not in (b"{", b"["):
                raise ValueError("non-JSON payload")
            return json.loads(b.decode("utf-8"))
        except Exception:                                     # noqa: BLE001
            if a == tries - 1:
                return None
            time.sleep(1.2 * (2 ** a))
    return None


def esearch(term):
    u = EUTILS + "esearch.fcgi?" + urllib.parse.urlencode({
        "db": "pubmed", "term": term, "retmode": "json", "retmax": str(RETMAX)})
    d = _get(u)
    if not d:
        return None
    r = d.get("esearchresult") or {}
    return set(r.get("idlist") or []), int(r.get("count") or 0)


def esummary(pmids):
    """Publication types for up to 200 PMIDs."""
    if not pmids:
        return {}
    u = EUTILS + "esummary.fcgi?" + urllib.parse.urlencode({
        "db": "pubmed", "id": ",".join(sorted(pmids)[:200]), "retmode": "json"})
    d = _get(u)
    if not d:
        return {}
    res = d.get("result") or {}
    out = {}
    for k, v in res.items():
        if k == "uids" or not isinstance(v, dict):
            continue
        out[k] = set(v.get("pubtype") or [])
    return out


def main():
    n_sample = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    rows = list(csv.DictReader(open(LEDGER, encoding="utf-8-sig")))
    rows = [r for r in rows if r.get("filtered_query") and r.get("unfiltered_query")]
    random.seed(11)
    sample = random.sample(rows, min(n_sample, len(rows)))
    print("ledger topics %d | sampled %d" % (len(rows), len(sample)))

    tot_unf = tot_filt = tot_lost = tot_lost_eligible = 0
    topics_with_loss = 0
    worst = []
    t0 = time.time()
    done = failed = 0

    for i, r in enumerate(sample, 1):
        f = esearch(r["filtered_query"])
        time.sleep(PAUSE)
        u = esearch(r["unfiltered_query"])
        time.sleep(PAUSE)
        if f is None or u is None:
            failed += 1
            continue
        fids, fcount = f
        uids, ucount = u
        lost = uids - fids
        tot_unf += len(uids)
        tot_filt += len(fids)
        tot_lost += len(lost)
        done += 1
        if lost:
            topics_with_loss += 1
            pts = esummary(lost)
            time.sleep(PAUSE)
            el = [p for p, t in pts.items() if t & ELIGIBLE_PT]
            tot_lost_eligible += len(el)
            if el:
                worst.append({"topic": r["topic"], "lost": len(lost),
                              "lost_eligible": len(el),
                              "filtered_query": r["filtered_query"],
                              "example_pmids": sorted(el)[:5]})
        if i % 20 == 0:
            e = time.time() - t0
            print("  %d/%d | %.1f topic/s | lost %d, of which typed eligible %d"
                  % (i, len(sample), i / e if e else 0, tot_lost, tot_lost_eligible))

    res = {
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ledger_source": LEDGER,
        "ledger_topics": len(rows),
        "sampled_topics": len(sample),
        "topics_measured": done,
        "topics_failed": failed,
        "retmax_per_query": RETMAX,
        "eligible_publication_types": sorted(ELIGIBLE_PT),
        "records_unfiltered": tot_unf,
        "records_filtered": tot_filt,
        "records_lost_to_filter": tot_lost,
        "records_lost_that_medline_types_eligible": tot_lost_eligible,
        "topics_losing_at_least_one_record": topics_with_loss,
        "blind_spot_rate_pct": round(100.0 * tot_lost_eligible / tot_unf, 2) if tot_unf else None,
        "blind_spot_denominator": "records the unfiltered query returned (applicable rows, not corpus total)",
        "loss_rate_pct": round(100.0 * tot_lost / tot_unf, 2) if tot_unf else None,
        "share_of_lost_that_was_eligible_pct": round(100.0 * tot_lost_eligible / tot_lost, 2) if tot_lost else None,
        "caveat": ("retmax caps each query at %d records, so topics with more hits "
                   "are measured on their first %d only. This UNDERSTATES loss on "
                   "large topics and the direction of that bias is stated rather "
                   "than corrected." % (RETMAX, RETMAX)),
        "worst_topics": sorted(worst, key=lambda x: -x["lost_eligible"])[:25]}
    os.makedirs("outputs", exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n--- measured blind spot ---")
    print("topics measured        : %d (failed %d)" % (done, failed))
    print("records unfiltered     : %d" % tot_unf)
    print("records filtered       : %d" % tot_filt)
    print("lost to the filter     : %d  (%.2f%% of unfiltered)"
          % (tot_lost, 100.0 * tot_lost / tot_unf if tot_unf else 0))
    print("of those, MEDLINE-typed RCT/MA/SR: %d" % tot_lost_eligible)
    print("BLIND SPOT             : %.2f%% of applicable records"
          % (100.0 * tot_lost_eligible / tot_unf if tot_unf else 0))
    print("share of lost that was eligible: %.1f%%"
          % (100.0 * tot_lost_eligible / tot_lost if tot_lost else 0))
    print("topics losing >=1 record: %d/%d" % (topics_with_loss, done))
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
