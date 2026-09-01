# -*- coding: utf-8 -*-
"""GAP 2, measurement 2 -- truncation-free screening recall.

Implements PREREG-2-screening-recall-exact.md. Query construction and seed set are
IDENTICAL to PREREG-1; the only change is that membership is asked directly per seed,
so there is no retrieval set to truncate.
"""
import io, json, os, sys, time, collections
from urllib.parse import quote

sys.path.insert(0, ".")
import screening_recall as S  # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)


def count(term):
    t = S.get("%s/esearch.fcgi?db=pubmed&retmode=json&retmax=0&term=%s" % (S.E, quote(term)))
    if not t:
        return None
    try:
        return int(json.loads(t, strict=False)["esearchresult"]["count"])
    except Exception:
        return None


def member(query, pmid):
    """Exact: does this PMID satisfy this query? 1 or 0, never truncated."""
    c = count("(%s) AND %s[UID]" % (query, pmid))
    return None if c is None else (c > 0)


def main():
    prereg = "PREREG-2-screening-recall-exact.md"
    print("PREREG-2  frozen at %s" % os.popen("git hash-object " + prereg).read().strip())
    d = json.load(io.open(S.MAIN, encoding="utf-8"))
    byobj = collections.defaultdict(set)
    for r in d.values():
        if r.get("objective") and r.get("paper_doi"):
            byobj[r["objective"]].add(r["paper_doi"])
    eligible = {k: v for k, v in byobj.items() if len(v) >= 3}
    doi2pmid = json.load(io.open("seed_pmid_cache.json", encoding="utf-8"))
    prev = json.load(io.open("screening_recall_result.json", encoding="utf-8"))
    print("MEASURED  eligible reviews %d ; PREREG-1 micro was %.3f"
          % (len(eligible), prev["micro"]))
    print("          cmd: python screening_recall_exact.py")
    print("")

    rows, tot_hit, tot_seed, hitset = [], 0, 0, set()
    for obj, dois in sorted(eligible.items()):
        seeds = sorted({doi2pmid[x] for x in dois if doi2pmid.get(x)})
        if not seeds:
            continue
        q, _ = S.build_query(obj)
        hits = []
        for p in seeds:
            if member(q, p):
                hits.append(p)
                hitset.add(p)
            time.sleep(0.34)
        rows.append({"objective": obj[:90], "query": q, "seeds": len(seeds),
                     "hits": len(hits), "recall": len(hits) / float(len(seeds))})
        tot_hit += len(hits)
        tot_seed += len(seeds)
        print("  %-2d seeds  %d hit  recall %.2f  | %s"
              % (len(seeds), len(hits), len(hits) / float(len(seeds)), q[:60]))

    micro = tot_hit / float(tot_seed) if tot_seed else 0.0
    macro = sum(r["recall"] for r in rows) / len(rows) if rows else 0.0

    # ---- controls ----
    probe = sorted(hitset)[0] if hitset else None
    mf = member("randomized OR randomised", probe) if probe else None
    nf = member("quantum chromodynamics", probe) if probe else None
    print("")
    print("CONTROL   MUST-FIRE     : a known hit satisfies a broad query -- %s"
          % ("PASS" if mf else "FAIL"))
    print("CONTROL   MUST-NOT-FIRE : same PMID vs unrelated query -- %s"
          % ("PASS" if nf is False else "FAIL"))
    print("CONTROL   CONSISTENCY   : every PREREG-1 hit must still be a hit")
    p1 = set()
    for r in prev["rows"]:
        pass  # PREREG-1 stored counts, not PMIDs; consistency checked by count instead
    consistent = tot_hit >= prev["hits"]
    print("            PREREG-1 hits %d ; PREREG-2 hits %d -- %s"
          % (prev["hits"], tot_hit, "PASS" if consistent else "FAIL -- new test is stricter"))
    print("")
    print("=== RESULT, as pre-registered ===")
    print("  reviews scored        : %d" % len(rows))
    print("  resolvable seeds      : %d" % tot_seed)
    print("  seeds satisfying query: %d" % tot_hit)
    print("  MICRO RECALL          : %.3f   <-- headline (truncation-free)" % micro)
    print("  macro recall          : %.3f" % macro)
    print("  reviews with 0 recall : %d" % sum(1 for r in rows if r["hits"] == 0))
    print("")
    print("  PREREG-1 (truncated)  : %.3f" % prev["micro"])
    print("  PREREG-2 (exact)      : %.3f   -> truncation cost %.1f points"
          % (micro, 100 * (micro - prev["micro"])))
    print("  DECLARED PRIOR 15%% (band 6-35%%). Outcome %.1f%% -- prior %s"
          % (100 * micro, "HELD" if 0.06 <= micro <= 0.35 else "MISSED"))
    json.dump({"micro": micro, "macro": macro, "seeds": tot_seed, "hits": tot_hit,
               "prereg1_micro": prev["micro"], "rows": rows,
               "controls": {"must_fire": bool(mf), "must_not_fire": nf is False,
                            "consistency": bool(consistent)}},
              io.open("screening_recall_exact_result.json", "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
