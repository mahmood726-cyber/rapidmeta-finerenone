# -*- coding: utf-8 -*-
"""POST-HOC, EXPLORATORY -- NOT part of PREREG-screening-recall.md.

The pre-registered result was 4.7%. Before believing that as a property of the SEARCH
rather than of the HARNESS, the harness must be shown capable of returning a HIGH number.
A measurement device that has only ever produced one terrible value is indistinguishable
from a broken one.

So this scores three further strategies against the identical seed set. These figures are
EXPLORATORY. The pre-registered headline remains 4.7% and is not replaced by anything here.
"""
import io, json, os, re, sys, time, collections

sys.path.insert(0, ".")
import screening_recall as S  # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)


def build(objective, max_terms, joiner):
    s = S.LEAD.sub("", objective or "").lower()
    toks = re.findall(r"[a-z][a-z\-]+", s)
    terms = [t for t in toks if len(t) >= 4 and t not in S.STOP]
    seen, keep = set(), []
    for t in terms:
        if t not in seen:
            seen.add(t)
            keep.append(t)
        if len(keep) >= max_terms:
            break
    return (" %s " % joiner).join(keep)


def run(eligible, doi2pmid, max_terms, joiner, label, retmax=200):
    hit = tot = zero = 0
    for obj, dois in sorted(eligible.items()):
        seeds = {doi2pmid[x] for x in dois if doi2pmid.get(x)}
        if not seeds:
            continue
        q = build(obj, max_terms, joiner)
        got = set(S.esearch_ids(q, retmax=retmax)) if q else set()
        h = len(got & seeds)
        hit += h
        tot += len(seeds)
        zero += (1 if not got else 0)
        time.sleep(0.34)
    print("  %-34s micro %.3f  (%d/%d)   empty-result queries: %d"
          % (label, hit / float(tot) if tot else 0, hit, tot, zero))
    return hit / float(tot) if tot else 0.0


def main():
    d = json.load(io.open(S.MAIN, encoding="utf-8"))
    byobj = collections.defaultdict(set)
    for r in d.values():
        if r.get("objective") and r.get("paper_doi"):
            byobj[r["objective"]].add(r["paper_doi"])
    eligible = {k: v for k, v in byobj.items() if len(v) >= 3}
    cache = "seed_pmid_cache.json"
    if os.path.exists(cache):
        doi2pmid = json.load(io.open(cache, encoding="utf-8"))
    else:
        res = json.load(io.open("screening_recall_result.json", encoding="utf-8"))
        doi2pmid = {}
        allseeds = sorted({x for v in eligible.values() for x in v})
        for doi in allseeds:
            doi2pmid[doi] = S.doi_to_pmid(doi)
        json.dump(doi2pmid, io.open(cache, "w", encoding="utf-8"))
    print("POST-HOC, EXPLORATORY -- pre-registered headline stays 4.7%")
    print("cmd: python screening_variants.py")
    print("")
    print("  strategy                           result")
    run(eligible, doi2pmid, 6, "AND", "6 terms AND  (pre-registered)")
    run(eligible, doi2pmid, 3, "AND", "3 terms AND  (less conjunction)")
    run(eligible, doi2pmid, 6, "OR", "6 terms OR   (recall-oriented)")
    run(eligible, doi2pmid, 6, "OR", "6 terms OR, retmax 1000", retmax=1000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
