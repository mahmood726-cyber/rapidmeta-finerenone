"""Stage B: can an author-year label find the paper? Recall AND ambiguity, both.

STAGE A IS DONE. `measure_join_stage_a_2026_08_25.py` recovered 32 of 34 registrations from
a PMID via PubMed's DataBank field, null 0%, and -- the property that matters most -- ZERO
cases where the field held a DIFFERENT trial's registration. When it is present it is right.
So the join author-year -> NCT is not blocked at stage A. It is blocked here.

WHAT A COCHRANE LABEL ACTUALLY IS. `Carter 1970`, `Coope 1986`, `SHEP 1991` -- a surname or
an acronym, plus a year. That is the entire identifier a third party receives. This measures
what such a label can recover.

TWO NUMBERS, AND REPORTING ONLY THE FIRST WOULD BE THE ERROR:

  RECALL     is the true PMID anywhere in what the label returns?
  AMBIGUITY  how many records come back? A true PMID sitting among 400 hits is not a join,
             it is a haystack that contains a needle.

So the reportable quantity is not recall but RESOLVED: the true PMID returned AND a result
set small enough to act on. Thresholds are stated before the run rather than chosen after
seeing the data: n<=1 resolved, n<=5 resolvable with one more field, n>5 not resolvable.

LABELS ARE BUILT FROM THE RECORD, NOT FROM OUR TRIAL NAMES. For each of the 34, the first
author surname and publication year are read out of the cached PubMed XML and the label is
"Surname Year" -- the form Cochrane uses. Building it from our own acronym would test a
different thing, because an acronym is a far stronger identifier than a surname.

NULL TEST. Each surname is paired with a year seven off. A label that still resolves is
resolving on the surname alone, which for a prolific author is not identification.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_X = os.path.join(REPO, "outputs", "pubmed_databank_cache")
CACHE_S = os.path.join(REPO, "outputs", "pubmed_esearch_cache")
STAGE_A = os.path.join(REPO, "outputs", "join_stage_a_pmid_to_nct_2026_08_25.json")
OUT = os.path.join(REPO, "outputs", "join_stage_b_label_to_pmid_2026_08_25.json")

ESEARCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
           "?db=pubmed&retmax=200&retmode=json&term=%s")

LASTNAME = re.compile(r"<LastName>([^<]{1,60})</LastName>")
YEAR = re.compile(r"<PubDate>.*?<Year>(\d{4})</Year>", re.S)
ARTICLE_YEAR = re.compile(r"<ArticleDate[^>]*>\s*<Year>(\d{4})</Year>", re.S)


def label_from_xml(xml):
    """(surname, year) as a Cochrane label would be formed. None if either is absent."""
    a = LASTNAME.search(xml or "")
    y = YEAR.search(xml or "") or ARTICLE_YEAR.search(xml or "")
    if not a or not y:
        return None
    return a.group(1).strip(), y.group(1)


def esearch(term):
    """Cached esearch. Returns (idlist, count), or None -- never an empty passed off as zero."""
    os.makedirs(CACHE_S, exist_ok=True)
    key = re.sub(r"[^A-Za-z0-9]+", "_", term)[:90]
    fp = os.path.join(CACHE_S, key + ".json")
    if os.path.exists(fp) and os.path.getsize(fp) > 20:
        try:
            d = json.load(io.open(fp, encoding="utf-8"))
            return d.get("idlist", []), d.get("count")
        except ValueError:
            pass
    url = ESEARCH % term.replace(" ", "+").replace("[", "%5B").replace("]", "%5D")
    for attempt in (1, 2, 3):
        # -g so a bracketed field tag is not read as a curl glob. That bug once fired twelve
        # requests in zero seconds and returned nothing at all.
        r = subprocess.run(["curl", "-sS", "-g", "--max-time", "60", url],
                           capture_output=True)
        body = (r.stdout or b"").decode("utf-8", "replace")
        try:
            res = (json.loads(body).get("esearchresult") or {})
            ids = res.get("idlist")
            if ids is None:
                raise ValueError("no idlist in payload")
            rec = {"idlist": ids, "count": int(res.get("count", len(ids)))}
            io.open(fp, "w", encoding="utf-8").write(json.dumps(rec))
            return rec["idlist"], rec["count"]
        except Exception:
            time.sleep(2 * attempt)
    return None


def main():
    a = json.load(io.open(STAGE_A, encoding="utf-8"))
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    log("STAGE B: author-year label -> PMID. Stage A (PMID -> NCT) measured 32/34 separately.")
    log("Thresholds stated up front: resolved n<=1, resolvable-with-one-field n<=5, else not.")
    log("")

    rows = []
    for i, r in enumerate(a["rows"], 1):
        pmid = r["pmid"]
        fp = os.path.join(CACHE_X, "%s.xml" % pmid)
        if not os.path.exists(fp):
            rows.append({"pmid": pmid, "status": "no cached record"})
            continue
        xml = io.open(fp, encoding="utf-8", errors="replace").read()
        lab = label_from_xml(xml)
        if lab is None:
            rows.append({"pmid": pmid, "status": "no label derivable"})
            log("[%2d] %-9s NO LABEL (surname or year absent from the record)" % (i, pmid))
            continue
        surname, year = lab
        got = esearch("%s[Author] AND %s[dp]" % (surname, year))
        if got is None:
            rows.append({"pmid": pmid, "label": "%s %s" % (surname, year),
                         "status": "MISSING"})
            log("[%2d] %-9s %-26s MISSING -- no payload after 3 attempts"
                % (i, pmid, surname + " " + year))
            continue
        ids, count = got
        nyear = str(int(year) - 7)
        ngot = esearch("%s[Author] AND %s[dp]" % (surname, nyear))
        nids, ncount = ngot if ngot else ([], None)
        rows.append({"pmid": pmid, "nct": r.get("nct"), "label": "%s %s" % (surname, year),
                     "status": "ok", "count": count, "recall": pmid in ids,
                     "null_count": ncount, "null_recall": pmid in nids})
        log("[%2d] %-9s %-26s n=%-5s %-7s null n=%s"
            % (i, pmid, surname + " " + year, count,
               "RECALL" if pmid in ids else "absent", ncount))
        time.sleep(0.34)

    ok = [r for r in rows if r.get("status") == "ok"]
    rec = [r for r in ok if r["recall"]]
    res1 = [r for r in rec if r["count"] <= 1]
    res5 = [r for r in rec if r["count"] <= 5]
    nullrec = [r for r in ok if r.get("null_recall")]
    log("")
    log("labels measured               : %d" % len(ok))
    log("true PMID returned (recall)   : %d / %d" % (len(rec), len(ok)))
    log("  and n<=1  RESOLVED          : %d / %d" % (len(res1), len(ok)))
    log("  and n<=5  needs one field   : %d / %d" % (len(res5), len(ok)))
    log("  recalled but n>5            : %d / %d" % (len(rec) - len(res5), len(ok)))
    log("NULL (year shifted 7) recall  : %d / %d" % (len(nullrec), len(ok)))
    if ok:
        counts = sorted(r["count"] for r in ok)
        log("median result-set size        : %d   (max %d)" % (counts[len(ok) // 2], counts[-1]))
        log("")
        log("Recall is %d/%d but RESOLVED is %d/%d. Reporting recall alone would describe a"
            % (len(rec), len(ok), len(res1), len(ok)))
        log("haystack as a join.")
    else:
        log("NOT MEASURABLE: no label produced a payload, so nothing is reported.")

    json.dump({"stage": "B: author-year label -> PMID via esearch",
               "thresholds": "resolved n<=1; resolvable-with-one-more-field n<=5; stated "
                             "before the run rather than after seeing the data",
               "n": len(ok), "recall": len(rec), "resolved_n1": len(res1),
               "resolvable_n5": len(res5), "null_recall": len(nullrec), "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
