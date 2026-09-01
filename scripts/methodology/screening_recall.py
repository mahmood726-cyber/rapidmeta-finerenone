# -*- coding: utf-8 -*-
"""GAP 2 -- screening recall against a known-positive seed set.

Implements PREREG-screening-recall.md EXACTLY. Pre-registration frozen at
git hash-object = 7b2b6fa8114db0643f15530397e733cbf4c6572b

Nothing here is tuned. If a query returns zero it is reported as zero.
"""
import io, json, os, re, sys, time, collections
from urllib.request import urlopen, Request
from urllib.parse import quote

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)

UA = {"User-Agent": "research/1.0 (mailto:mahmood726@gmail.com)"}
E = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PREREG_HASH = "7b2b6fa8114db0643f15530397e733cbf4c6572b"
# NO HARDCODED LOCAL PATH. Set ROBBR_DIR (or ALLMETA_ROB_DIR) to the directory holding
# the RoBBR json files. Fails closed with the required action rather than silently.
ROBBR_DIR = os.environ.get("ROBBR_DIR") or os.environ.get("ALLMETA_ROB_DIR") or "robbr"
MAIN = os.path.join(ROBBR_DIR, "Main_task_Cochrane_test.json")
if not os.path.exists(MAIN):
    raise SystemExit(
        "MISSING INPUT: %s\n"
        "Set ROBBR_DIR to the directory containing RoBBR Main_task_Cochrane_test.json.\n"
        "Fetch: https://huggingface.co/datasets/RoBBR-Benchmark/RoBBR (CC-BY-NC-4.0)"
        % MAIN)

# --- declared in the pre-registration, reproduced verbatim ---
LEAD = re.compile(r"^\s*to\s+(assess|compare|determine|evaluate|investigate)\b", re.I)
STOP = {"effects", "efficacy", "safety", "treatment", "people", "patients", "adults",
        "children", "versus", "for", "of", "in", "the", "and", "with", "on"}
MAX_TERMS = 6
RETMAX = 200


def get(u, tries=4):
    for a in range(tries):
        try:
            return urlopen(Request(u, headers=UA), timeout=120).read().decode("utf-8", "replace")
        except Exception:
            if a == tries - 1:
                return ""
            time.sleep(2 * (a + 1))


def esearch_ids(term, retmax=RETMAX):
    t = get("%s/esearch.fcgi?db=pubmed&retmode=json&retmax=%d&term=%s"
            % (E, retmax, quote(term)))
    if not t:
        return []
    try:
        return json.loads(t, strict=False)["esearchresult"].get("idlist", [])
    except Exception:
        return []


def build_query(objective):
    """Steps 1-5 of the pre-registration, no deviation."""
    s = LEAD.sub("", objective or "").lower()
    toks = re.findall(r"[a-z][a-z\-]+", s)
    terms = [t for t in toks if len(t) >= 4 and t not in STOP]
    seen, keep = set(), []
    for t in terms:
        if t not in seen:
            seen.add(t)
            keep.append(t)
        if len(keep) >= MAX_TERMS:
            break
    return " AND ".join(keep), keep


def doi_to_pmid(doi):
    for field in ("AID", "DOI"):
        ids = esearch_ids('"%s"[%s]' % (doi, field), retmax=5)
        if ids:
            return ids[0]
        time.sleep(0.34)
    return None


def main():
    d = json.load(io.open(MAIN, encoding="utf-8"))
    byobj = collections.defaultdict(set)
    for r in d.values():
        if r.get("objective") and r.get("paper_doi"):
            byobj[r["objective"]].add(r["paper_doi"])
    eligible = {k: v for k, v in byobj.items() if len(v) >= 3}
    print("PREREG    frozen at %s" % PREREG_HASH)
    print("MEASURED  objectives total %d, eligible (>=3 seeds) %d"
          % (len(byobj), len(eligible)))
    print("          cmd: python screening_recall.py")
    print("")

    # ---- resolve seeds ----
    allseeds = sorted({doi for v in eligible.values() for doi in v})
    print("MEASURED  resolving %d distinct seed DOIs to PMIDs..." % len(allseeds))
    doi2pmid = {}
    for i, doi in enumerate(allseeds, 1):
        doi2pmid[doi] = doi_to_pmid(doi)
        if i % 20 == 0:
            print("          %d/%d resolved (%d hits)"
                  % (i, len(allseeds), sum(1 for v in doi2pmid.values() if v)))
    resolved = {k: v for k, v in doi2pmid.items() if v}
    print("MEASURED  seeds resolvable to a PMID: %d/%d ; unresolvable %d (EXCLUDED from "
          "the denominator, per pre-registration)"
          % (len(resolved), len(allseeds), len(allseeds) - len(resolved)))
    print("")

    # ---- KNOWN-ANSWER control: a resolved PMID must be retrievable by PMID ----
    probe_pmid = sorted(resolved.values())[0]
    back = esearch_ids("%s[UID]" % probe_pmid, retmax=5)
    ka = probe_pmid in back
    print("CONTROL   KNOWN-ANSWER: PMID %s retrievable by direct query -- %s"
          % (probe_pmid, "PASS" if ka else "FAIL"))

    # ---- NEGATIVE control: an unrelated query must score zero ----
    neg = set(esearch_ids("quantum chromodynamics"))
    neghit = len(neg & set(resolved.values()))
    print("CONTROL   NEGATIVE: unrelated query overlaps seeds in %d cases -- %s"
          % (neghit, "PASS" if neghit == 0 else "FAIL"))
    print("")

    # ---- the measurement ----
    rows, tot_hit, tot_seed = [], 0, 0
    for obj, dois in sorted(eligible.items()):
        seeds = {doi2pmid[x] for x in dois if doi2pmid.get(x)}
        if not seeds:
            continue
        q, terms = build_query(obj)
        got = set(esearch_ids(q)) if q else set()
        hit = len(got & seeds)
        rows.append({"objective": obj[:95], "query": q, "n_terms": len(terms),
                     "seeds_resolvable": len(seeds), "retrieved": len(got), "hits": hit,
                     "recall": hit / float(len(seeds))})
        tot_hit += hit
        tot_seed += len(seeds)
        print("  %-2d seeds  %-4d retrieved  %d hit  recall %.2f  | %s"
              % (len(seeds), len(got), hit, hit / float(len(seeds)), q[:62]))
        time.sleep(0.34)

    micro = tot_hit / float(tot_seed) if tot_seed else 0.0
    macro = sum(r["recall"] for r in rows) / len(rows) if rows else 0.0
    mustfire = any(r["hits"] > 0 for r in rows)
    print("")
    print("CONTROL   MUST-FIRE: at least one review retrieves >=1 of its own seeds -- %s"
          % ("PASS" if mustfire else "FAIL -- harness broken, not the search"))
    print("")
    print("=== RESULT, reported as pre-registered ===")
    print("  reviews scored        : %d" % len(rows))
    print("  resolvable seeds      : %d" % tot_seed)
    print("  seeds retrieved       : %d" % tot_hit)
    print("  MICRO RECALL          : %.3f   <-- headline" % micro)
    print("  macro recall          : %.3f" % macro)
    print("  reviews with 0 recall : %d" % sum(1 for r in rows if r["hits"] == 0))
    print("  reviews with 100%%     : %d" % sum(1 for r in rows if r["recall"] >= 1.0))
    print("")
    print("  DECLARED PRIOR was 40%% (band 20-65%%). Outcome: %.1f%% -- prior %s"
          % (100 * micro, "HELD" if 0.20 <= micro <= 0.65 else "MISSED"))
    json.dump({"prereg_hash": PREREG_HASH, "micro": micro, "macro": macro,
               "seeds": tot_seed, "hits": tot_hit, "rows": rows,
               "controls": {"known_answer": ka, "negative": neghit == 0,
                            "must_fire": mustfire}},
              io.open("screening_recall_result.json", "w", encoding="utf-8"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
