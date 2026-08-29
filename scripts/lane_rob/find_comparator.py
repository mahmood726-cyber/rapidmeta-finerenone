# -*- coding: utf-8 -*-
"""COMPONENT: find the best published comparator for a review, and date it.

WHY A COMPONENT. Every future review needs its best published comparator identified before it
can be judged, and "is there a Cochrane review of this question, how old is it, and can we read
it" is a query rather than an essay. Built once, run on any topic.

⚠️ EUROPE PMC'S JOURNAL FIELD DOES NOT FIND THESE. `JOURNAL:"Cochrane database of systematic
reviews"` returns 0 hits for a review we hold in full. PubMed's journal field returns 158 for
the same question. The component uses NCBI E-utilities for that reason, and the reason is
recorded because a future maintainer will otherwise "simplify" it back.

⛔ IT PROPOSES CANDIDATES; IT DOES NOT ASSERT A PICO MATCH. Deciding that a review answers the
same question is a judgement, and this project's rule is that irreducible judgement is named
rather than automated. Each candidate is returned with its title and date for confirmation, and
a topic with no confirmed match is reported as UNMATCHED rather than silently dropped.

THREE DATES, AND THEY ARE NOT INTERCHANGEABLE:
  publication date   when the review appeared -- from the record
  SEARCH date        when its evidence stops -- inside the text, and the one that matters
  our currency       today

The gap that matters is SEARCH date to today, not publication to today. A 2021 review that
searched to August 2020 has a five-year evidence gap, not a four-year one.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
EUT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
OUT = r"F:\claude-temp\pend\out\comparators.json"

STOP = set("""versus vs and or for in the of a an with without to at on by from
review systematic meta analysis pooled trial trials randomised randomized controlled
placebo change percent week weeks month months year years outcome outcomes""".split())


def terms_from_title(title):
    """Intervention and condition words, by a STATED rule rather than a guess.

    Words before 'versus' are the intervention; words after 'for'/'in' are the condition.
    Anything else is dropped. The rule is crude and is printed with the result so a reader can
    see what was searched rather than trusting that something sensible was.
    """
    t = re.sub(r"[^A-Za-z0-9 \-]", " ", title or "")
    low = t.lower()
    iv = low.split(" versus ")[0] if " versus " in low else low
    cond = ""
    m = re.search(r"\b(?:for|in)\b(.*)$", low)
    if m:
        cond = m.group(1)
    words = [w for w in (iv + " " + cond).split() if w not in STOP and len(w) > 3]
    seen, out = set(), []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out[:4]


def _get(url, dest):
    subprocess.run(["curl", "-s", "-L", "--max-time", "45", "-o", dest, url],
                   capture_output=True, timeout=90)
    try:
        return json.load(io.open(dest, encoding="utf-8"))
    except Exception:
        return None


def search_cochrane(words, tmp):
    if not words:
        return []
    # ⚠️ PROPER URL QUOTING, AND TWO TERMS NOT THREE. The first version built the query with
    # subprocess.list2cmdline, which escapes quotes for a Windows command line and emitted
    # `\%22Cochrane...` -- a broken field name that matched nothing. It also ANDed three terms.
    # Both faults pointed the same way: the component returned 0 candidates for dapivirine, the
    # ONE topic whose Cochrane review we hold in full. A known-answer control catching its own
    # component is the only reason the 8-of-28 figure was not reported as a finding.
    from urllib.parse import quote_plus
    q = '"Cochrane Database Syst Rev"[Journal] AND ' + " AND ".join(words[:2])
    d = _get("%s/esearch.fcgi?db=pubmed&retmode=json&retmax=5&term=%s"
             % (EUT, quote_plus(q)), tmp)
    if not d:
        return []
    return ((d.get("esearchresult") or {}).get("idlist") or [])


def summarise(pmids, tmp):
    if not pmids:
        return []
    d = _get("%s/esummary.fcgi?db=pubmed&retmode=json&id=%s" % (EUT, ",".join(pmids)), tmp)
    out = []
    for p in pmids:
        r = ((d or {}).get("result") or {}).get(p) or {}
        if r:
            out.append({"pmid": p, "title": r.get("title"), "pubdate": r.get("pubdate"),
                        "journal": r.get("fulljournalname")})
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    ready = json.load(io.open(r"F:\claude-temp\pend\ready.json", encoding="utf-8"))
    topics = list(ready.get("keep") or [])
    for a in (ready.get("admitted_by_ruling") or []):
        topics.append({"page": a["page"], "title": a.get("title") or a["page"], "object": ""})
    print("indexed topics                        %3d  == the denominator" % len(topics))
    tmp = os.path.join(os.environ.get("TEMP", "."), "_cmp.json")
    rows = []
    for i, t in enumerate(topics, 1):
        words = terms_from_title(t.get("title") or t["page"])
        pmids = search_cochrane(words, tmp)
        cands = summarise(pmids, tmp)
        rows.append({"page": t["page"], "title": t.get("title"), "search_terms": words,
                     "n_candidates": len(cands), "candidates": cands})
        print("  %-44s %-34s %d candidate(s)"
              % (t["page"][:44], "+".join(words[:3])[:34], len(cands)))
        time.sleep(0.4)
    n_any = sum(1 for r in rows if r["n_candidates"])
    print("")
    print("  topics with >=1 Cochrane candidate    %3d   %.0f%%"
          % (n_any, 100.0 * n_any / len(rows)))
    print("  topics with NONE                      %3d   <- UNMATCHED, not 'no comparator'"
          % (len(rows) - n_any))
    json.dump(rows, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("  detail -> comparators.json")
    print("")
    print("  ⚠️ Candidates only. A PICO match is a judgement and is not asserted here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
