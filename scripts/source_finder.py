#!/usr/bin/env python3
"""SOURCE SEARCH: which documents carry extractable data for THIS trial?

A DIFFERENT PROBLEM FROM THE EVIDENCE SEARCH, and the corpus has only had the first.

    evidence search  -- what trials exist for this question?      (built, five sources)
    source search    -- what documents carry the DATA for THIS trial?   (this file)

THE QUERY THAT INVERTS IT: search FULL TEXT for the registration id. Europe PMC indexes
full text for open-access content, so querying NCT01131676 returns every open document that
NAMES that trial -- its own report, its secondary analyses, and the meta-analyses that
extracted it. One call per trial. EMPA-REG OUTCOME returns 217.

Instead of "find meta-analyses about topic X and hope ours is in them", this asks "who has
already extracted this exact trial", which is the question that has an answer.

THE SCREEN IS A DIFFERENT SCREEN, and conflating the two is the trap:

    eligibility screening -- does this TRIAL belong in the review?
    source screening      -- does this DOCUMENT carry data for this trial?

⛔ THE CLASS THAT MUST EXIST: MENTIONS_ONLY. A dose-selection paper can name both trials,
pass every existence check, and report neither. Naming a trial is not reporting it.

⛔ AND THE CLASS THAT MUST NOT BE CONFUSED WITH IT: NOT_ASSESSABLE. A document whose full
text we cannot read is NOT "mentions only" -- that would be inferring absence from our own
inability, which is the same error as recording a 503 as "no new records". The two are
counted separately and never merged.

CONTENT, NOT STATUS. A document counts as carrying data only if a number, an estimate, an
interval, or a methods statement appears NEAR the trial's id in its full text. A 200 is not
a document and length is not content.
"""
import io
import json
import os
import re
import sys
import time

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
UA = {"User-Agent": "rapidmeta-source-finder/1.0 (research use)"}
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"

NCT_RE = re.compile(r"NCT\d{8}")

# Classification vocabulary. Derived from what these documents actually call themselves,
# and applied to TITLE plus ABSTRACT, never to the full text -- a meta-analysis that
# mentions "post hoc" in its discussion is still a meta-analysis.
META = re.compile(r"meta-analy|metaanaly|systematic review|network meta|pooled analys"
                  r"|indirect (treatment )?comparison|umbrella review", re.I)
DESIGN = re.compile(r"rationale and design|study protocol|design and baseline"
                    r"|protocol for a|statistical analysis plan", re.I)
SECONDARY = re.compile(r"post[- ]hoc|secondary analys|prespecified analys|pre-specified "
                       r"analys|subgroup analys|exploratory analys|mediation analys"
                       r"|substudy|sub-study", re.I)
PRIMARY_PT = re.compile(r"randomized controlled trial|clinical trial, phase iii"
                        r"|randomised controlled trial", re.I)

# Evidence that a document carries DATA for a trial, looked for near the id itself.
NUMERIC = re.compile(
    r"\b\d+\s*/\s*\d+\b"                      # 50/83
    r"|\bn\s*=\s*\d+"                          # n = 646
    r"|\b\d+(\.\d+)?\s*%"                      # 89.3%
    r"|\b(hazard|risk|odds|rate)\s+ratio"      # named estimate
    r"|\bHR\b|\bRR\b|\bOR\b|\baHR\b"
    r"|95%\s*(CI|confidence)"                  # an interval
    r"|\bp\s*[<=>]\s*0?\.\d+", re.I)
METHODS = re.compile(r"random(ly|ised|ized) (assigned|allocated)|double[- ]blind"
                     r"|intention[- ]to[- ]treat|primary (end ?point|outcome) was", re.I)


def epmc_search(nct, page_size=100, max_pages=3):
    """Every open document whose indexed text names this trial."""
    # RETRIED WITH BACKOFF, because the alternative is publishing my own request rate as a
    # fact about the literature. A first run over 16 trials took HTTP 503 on 6 of them and
    # printed "candidates=None, examined=0" beside trials that have plenty of documents.
    # That is the third time Europe PMC has rate-limited this session; the fix belongs in
    # the function, not in remembering to retry.
    out, page = [], 1
    while page <= max_pages:
        r = None
        for attempt in range(4):
            try:
                r = requests.get(EPMC + "/search",
                                 params={"query": nct, "format": "json",
                                         "pageSize": page_size, "page": page,
                                         "resultType": "core"},
                                 headers=UA, timeout=60)
            except Exception as e:
                r = None
                err = type(e).__name__
            if r is not None and r.status_code == 200:
                break
            time.sleep(4 * (attempt + 1))
        if r is None:
            return out, {"outcome": "FAILED", "error": err,
                         "_note": "retried 4 times with backoff"}
        if r.status_code != 200:
            return out, {"outcome": "FAILED", "http": r.status_code,
                         "_note": "retried 4 times with backoff; this is the source "
                                  "refusing, not a count of zero"}
        j = r.json()
        res = (j.get("resultList") or {}).get("result") or []
        out += res
        total = int(j.get("hitCount", 0))
        if len(res) < page_size or len(out) >= total:
            return out, {"outcome": "EXECUTED" if total else "EMPTY", "hitCount": total}
        page += 1
        time.sleep(1.0)
    return out, {"outcome": "EXECUTED", "hitCount": int(j.get("hitCount", 0)),
                 "_truncated_at": len(out)}


def full_text(rec):
    """Full text XML for an open-access record, or None. None means NOT ASSESSABLE.

    ⚠ THE FIRST VERSION OF THIS RETURNED None FOR ALL 40 CANDIDATES, and the run reported
    "content: NOT_ASSESSABLE 40" -- which reads as a fact about the literature and was a
    fact about my URL. Europe PMC's /{source}/{id}/fullTextXML 404s here for every record
    tried, including a long-standing open-access article whose full text certainly exists.
    Testing against that known-good case is what separated "the endpoint is wrong" from
    "these articles have no text"; without it the broken fetch would have been published as
    a finding about open-access coverage.

    NCBI's PMC efetch is used instead: it returns 90KB of JATS for the same article.
    """
    pmcid = rec.get("pmcid")
    if not pmcid:
        return None
    try:
        r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                         params={"db": "pmc", "id": pmcid.replace("PMC", ""),
                                 "retmode": "xml"}, headers=UA, timeout=60)
        return r.text if r.status_code == 200 and len(r.content) > 2000 else None
    except Exception:
        return None


def carries_data(text, nct, window=600):
    """Does a number, estimate, interval or methods statement sit NEAR this trial's id?

    Near, not anywhere: a meta-analysis is full of numbers, and the question is whether any
    of them is attached to THIS trial. The window is generous and the test is still
    imperfect -- it is evidence, not proof, and it is reported as such.
    """
    hits = [m.start() for m in re.finditer(nct, text)]
    if not hits:
        return False, 0, None
    for i in hits:
        seg = text[max(0, i - window): i + window]
        if NUMERIC.search(seg) or METHODS.search(seg):
            snippet = re.sub(r"\s+", " ", seg)
            return True, len(hits), snippet[:220]
    return False, len(hits), None


def classify(rec, ft, nct):
    """Source class for one document. CONTENT decides mentions-only, never the title."""
    title = rec.get("title") or ""
    abst = rec.get("abstractText") or ""
    head = title + " " + abst
    pt = " ".join((rec.get("pubTypeList") or {}).get("pubType") or [])

    kind = None
    if META.search(head):
        kind = "META_ANALYSIS_CONTAINING_IT"
    elif DESIGN.search(head):
        kind = "DESIGN_OR_PROTOCOL"
    elif SECONDARY.search(head):
        kind = "SECONDARY_ANALYSIS"
    elif PRIMARY_PT.search(pt):
        kind = "CANDIDATE_PRIMARY_REPORT"

    if ft is None:
        return {"class": kind or "UNCLASSIFIED",
                "content": "NOT_ASSESSABLE",
                "_why": ("full text not open, so whether it carries data for this trial "
                         "cannot be decided. NOT the same as mentions-only.")}
    has, n_mentions, snip = carries_data(ft, nct)
    if not has:
        return {"class": "MENTIONS_ONLY", "content": "NO_DATA_NEAR_ID",
                "n_mentions": n_mentions,
                "_why": ("the id appears but no count, estimate, interval or methods "
                         "statement sits near it. Naming a trial is not reporting it.")}
    return {"class": kind or "CARRIES_DATA_UNCLASSIFIED", "content": "CARRIES_DATA",
            "n_mentions": n_mentions, "evidence": snip}


def find_for_trial(nct, cap=40):
    recs, status = epmc_search(nct)
    out = {"nct": nct, "search": status, "n_candidates": len(recs), "documents": []}
    for rec in recs[:cap]:
        ft = full_text(rec)
        c = classify(rec, ft, nct)
        out["documents"].append({
            "pmid": rec.get("pmid"), "id": rec.get("id"), "source": rec.get("source"),
            "year": rec.get("pubYear"), "open_access": rec.get("isOpenAccess") == "Y",
            "title": (rec.get("title") or "")[:130], **c})
        time.sleep(0.4)   # NCBI: <=3 req/s
    if len(recs) > cap:
        out["_capped"] = ("Examined the first %d of %d candidates. The rest are NOT "
                          "clean and NOT absent -- they were not looked at."
                          % (cap, len(recs)))
    from collections import Counter
    out["by_class"] = dict(Counter(d["class"] for d in out["documents"]))
    out["by_content"] = dict(Counter(d["content"] for d in out["documents"]))
    return out


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ncts = [a for a in sys.argv[1:] if NCT_RE.fullmatch(a)]
    if not ncts:
        print("usage: source_finder.py NCT00000000 [NCT...]")
        sys.exit(2)
    results = []
    for n in ncts:
        r = find_for_trial(n)
        results.append(r)
        print("%s  candidates=%-4s examined=%-3d  %s" % (
            n, r["search"].get("hitCount"), len(r["documents"]),
            " ".join("%s=%d" % (k.replace("_", "-")[:22], v)
                     for k, v in sorted(r["by_class"].items()))))
        print("      content: %s" % r["by_content"])
    out = os.path.join(SSOT, "registration", "source-finder-run.json")
    json.dump({"_what_this_is": "per-trial source search", "trials": results},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("written: %s" % out)
