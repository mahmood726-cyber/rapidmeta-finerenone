"""The known positive for the findable-by-effort search. Run this BEFORE believing "not found".

WHY THIS EXISTS. The findable-by-effort measurement asks whether a trial with no registration
in its PubMed record can still be located in the registry by title search. It answers "not
found" for most of them. That answer is only meaningful if the search can find a trial that IS
there -- otherwise "not found" is a fact about the search.

THE KNOWN POSITIVE, and the project already has one. 87 papers in the same sample DO carry a
registration in their PubMed DataBank field, so their NCT is known independently of this
search. Running the identical query for those papers asks:

    when the answer is known to exist, how often does the search return it?

That number is the CEILING on the findable measurement. If it is high, "not found" means not
registered under a findable title. If it is low, the findable measurement cannot support any
claim at all and must be reported as NOT MEASURABLE rather than as a low rate.

This is rule 00c applied before the fact rather than after: the collinearity linter's first
run emitted six plausible flags and missed the one real case, because a known positive existed
and was not used. One exists here too.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
SRC = os.path.join(REPO, "outputs", "join_end_to_end_2026_08_25.json")
XML = os.path.join(REPO, "outputs", "pubmed_databank_cache")
OUT = os.path.join(REPO, "outputs", "findable_known_positive_2026_08_25.json")

import measure_registration_findable_by_effort_2026_08_25 as F

TITLE = re.compile(r"<ArticleTitle[^>]*>(.*?)</ArticleTitle>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
NCT_RE = re.compile(r"NCT\d{8}")
DATABANK = re.compile(
    r"<DataBankName>\s*ClinicalTrials\.gov\s*</DataBankName>(.*?)</DataBank>", re.S | re.I)


def cached(pmid):
    for ext in (".xml", ".txt"):
        fp = os.path.join(XML, str(pmid) + ext)
        if os.path.exists(fp):
            return io.open(fp, encoding="utf-8", errors="replace").read()
    return None


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    rows = json.load(io.open(SRC, encoding="utf-8"))["rows"]
    targets = []
    for r in rows:
        if not (r.get("nct") and r.get("pmid")):
            continue
        x = cached(r["pmid"])
        if not x:
            continue
        m = TITLE.search(x)
        if not m:
            continue
        targets.append({"pmid": r["pmid"], "nct": r["nct"],
                        "title": TAG.sub(" ", m.group(1)).strip()})

    log("papers whose registration is KNOWN from the DataBank field: %d" % len(targets))
    log("running the identical title search used by the findable measurement")
    log("")

    hit_any, hit_top, over_rule, failed, rows_out = 0, 0, 0, 0, []
    import time
    for i, t in enumerate(targets, 1):
        recs = F.search(t["title"])
        if recs is None:
            failed += 1
            rows_out.append(dict(t, status="SEARCH FAILED"))
            continue
        ncts = [r["nct"] for r in recs]
        in_set = t["nct"] in ncts
        nct, best, above = F.score(t["title"], recs)
        top = (nct == t["nct"])
        hit_any += 1 if in_set else 0
        hit_top += 1 if top else 0
        over_rule += 1 if above >= 1 else 0
        rows_out.append(dict(t, status="ok", returned=len(recs), in_set=in_set,
                             best_j=round(best, 3), n_above=above, picked=nct))
        log("[%3d/%d] %-9s %-12s returned=%-3d %s best=%.2f %s"
            % (i, len(targets), t["pmid"], t["nct"], len(recs),
               "IN-SET " if in_set else "absent ", best,
               "PICKED-CORRECT" if top else ("picked " + str(nct) if nct else "")))
        time.sleep(0.34)

    n = len([r for r in rows_out if r.get("status") == "ok"])
    log("")
    log("searched                                  : %d  (search failed %d)" % (n, failed))
    if not n:
        log("NOT MEASURABLE: no search returned a payload.")
        return 1
    log("true NCT anywhere in the returned set     : %d / %d  (%.0f%%)"
        % (hit_any, n, 100.0 * hit_any / n))
    log("a record cleared the %.2f rule            : %d / %d  (%.0f%%)"
        % (F.THRESHOLD, over_rule, n, 100.0 * over_rule / n))
    log("the record it picked WAS the true NCT     : %d / %d  (%.0f%%)"
        % (hit_top, n, 100.0 * hit_top / n))
    log("")
    log("THIS IS THE CEILING. The findable-by-effort rate cannot exceed it, and if this is")
    log("low then 'not found' there is a fact about the search rather than about the registry.")

    json.dump({"role": "known positive / ceiling for the findable-by-effort measurement",
               "n": n, "search_failed": failed, "true_nct_in_returned_set": hit_any,
               "cleared_threshold": over_rule, "picked_correct": hit_top,
               "threshold": F.THRESHOLD, "rows": rows_out},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
