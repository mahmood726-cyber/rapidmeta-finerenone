# -*- coding: utf-8 -*-
"""Screen the BIBLIOGRAPHIC half of the executed dapivirine search, per record.

WHY THIS EXISTS. `scripts/systematic_search_dapivirine.py` retrieved 374 PubMed
records, 1,000 of a reported 1,443 Europe PMC records, 1 ISRCTN record and 63
ClinicalTrials.gov registrations. The object's `screen` block then reports
`candidates_screened: 63`. That is the REGISTRY set alone. The 1,375
bibliographic records were never screened, and the object does not say so --
which makes `coverage_fraction: "2 of 2", search_misses: 0` a registry-internal
recall figure presented as a search-wide one.

That is this project's most repeated defect: a scan reporting its own reach as
the population it covers. It is worse here than the gaps we lost verdicts on in
June, because THOSE WERE DECLARED and this one is not.

WHAT THIS DOES, in order:
  1. Pages Europe PMC properly with cursorMark, so 1,443 means 1,443. The
     existing script capped at pageSize=1000 and correctly refused to call that
     OK; this closes it rather than re-declaring it.
  2. Fetches TITLE AND ABSTRACT for every record, because a title-only screen
     cannot tell a dapivirine ring trial from a paper that cites one.
  3. Deduplicates PubMed against Europe PMC by PMID -- Europe PMC indexes
     MEDLINE, so the two sets overlap heavily and adding them is wrong.
  4. Screens every deduplicated record against ORDERED, DETERMINISTIC rules and
     writes ONE LEDGER ROW PER RECORD: the decision, the rule id that decided
     it, and the FIELD the rule read. A reader can pull any record and check the
     exclusion. Cochrane publishes a handful of near-miss exclusions with
     reasons; it never publishes the screened set.

⚠️ WHAT THIS IS NOT. It is a TITLE-AND-ABSTRACT screen, which is what the first
pass of a Cochrane screen also is. Records with NO ABSTRACT and no decisive
title are recorded as UNDECIDABLE and NAMED -- they are not swept into an
exclusion bucket, because "we could not decide" and "we decided against" are
different facts and only one of them is true.

FREE SOURCES ONLY. NCBI E-utilities and Europe PMC REST, both open, no key.
"""
import datetime
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

UA = "rapidmeta-systematic-review/1.0 (mailto:mahmood726@gmail.com)"

# The SAME concept block as the executed search. Imported by value rather than
# retyped would be better; it is asserted equal by a check at the bottom instead,
# so a divergence fails loudly rather than producing a screen of a different set.
TERMS = ["dapivirine", "dapavirine", "TMC 120", "TMC-120", "TMC120",
         "R 147681", "R-147681", "R147681"]

OUTDIR = "F:/rapidmeta-ssot-shell/evidence/2026-08-30-dapivirine-ahead"

# ---------------------------------------------------------------- signals ----
# Every regex below is a SCREENING INSTRUMENT and the rule that uses it names
# it. An instrument with no measured error rate is an assumption wearing a
# number, so the ledger records which signal fired on which field and a hand
# check of a fixed sample is run separately.

RX_DAPI = re.compile(
    r"dapivirine|dapavirine|TMC[\s\-]?120|R[\s\-]?147681", re.I)

# Randomisation / controlled-trial signal.
RX_TRIAL = re.compile(
    r"randomi[sz]ed|randomi[sz]ation|placebo[\s\-]?controll|"
    r"\bphase\s*(?:3|III|2b|IIb)\b|double[\s\-]?blind|"
    r"\bclinical trial\b|\befficacy trial\b", re.I)

# Vaginal ring signal. Dapivirine has also been trialled as a GEL and a FILM,
# and those are a different intervention for this question.
RX_RING = re.compile(r"\bring\b|\brings\b|intravaginal ring|vaginal ring", re.I)

# Publication types that cannot themselves be a primary trial report. A
# systematic review is NOT a trial and is excluded HERE -- it belongs to the
# published-synthesis comparison limb, which is a separate screen, and the
# ledger says so rather than dropping it.
SECONDARY_TYPES = {
    "review", "systematic review", "meta-analysis", "editorial", "comment",
    "letter", "news", "biography", "historical article", "case reports",
    "practice guideline", "guideline", "published erratum",
    "retraction of publication", "congress", "address", "interview",
    "introductory journal article", "portrait", "video-audio media",
    "webcast", "bibliography", "directory", "patient education handout",
}


def _curl(url, tries=4, post=None):
    for i in range(tries):
        cmd = ["curl", "-sL", "--max-time", "120", "-A", UA,
               "-w", "\n__H__%{http_code}"]
        if post is not None:
            cmd += ["--data", post]
        cmd.append(url)
        r = subprocess.run(cmd, capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        code = out.rsplit("__H__", 1)[-1].strip() if "__H__" in out else "000"
        body = out.rsplit("\n__H__", 1)[0] if "__H__" in out else out
        if code == "200":
            return body, code
        time.sleep(1.5 * (i + 1))
    return body, code


# ------------------------------------------------------------- retrieval ----
def pubmed_records():
    """374 PMIDs, then title+abstract+pubtype via efetch. Batched at 200."""
    q = " OR ".join('"%s"[All Fields]' % t for t in TERMS)
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"
           "&retmax=5000&retmode=json&term=%s" % urllib.parse.quote(q))
    body, code = _curl(url)
    if code != "200":
        return [], {"status": "FAILED_HTTP_%s" % code, "reported": None,
                    "retrieved": 0, "query": q}
    d = json.loads(body)
    ids = list((d.get("esearchresult") or {}).get("idlist") or [])
    reported = int((d.get("esearchresult") or {}).get("count") or 0)

    recs = []
    for i in range(0, len(ids), 200):
        chunk = ids[i:i + 200]
        f = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        body2, code2 = _curl(f, post="db=pubmed&retmode=xml&id=%s" % ",".join(chunk))
        if code2 != "200":
            continue
        try:
            root = ET.fromstring(body2)
        except ET.ParseError:
            continue
        for art in root.iter("PubmedArticle"):
            pmid = (art.findtext(".//PMID") or "").strip()
            title = " ".join((art.findtext(".//ArticleTitle") or "").split())
            abst = " ".join(" ".join(
                (t.text or "") for t in art.iter("AbstractText")).split())
            ptypes = [(p.text or "").strip().lower()
                      for p in art.iter("PublicationType")]
            year = (art.findtext(".//PubDate/Year")
                    or art.findtext(".//PubDate/MedlineDate") or "")[:4]
            journal = art.findtext(".//Journal/Title") or ""
            # Registration ids appear in DataBankList and in the abstract.
            accs = [(a.text or "").strip() for a in art.iter("AccessionNumber")]
            recs.append({"src": "pubmed", "id": pmid, "pmid": pmid,
                         "title": title, "abstract": abst, "ptypes": ptypes,
                         "year": year, "journal": journal, "accessions": accs})
        time.sleep(0.4)
    return recs, {"status": "OK", "reported": reported, "retrieved": len(recs),
                  "ids_listed": len(ids), "query": q}


def europepmc_records():
    """cursorMark paging. The existing script stopped at the pageSize cap and
    said so; this fetches the remainder rather than re-declaring the gap."""
    q = " OR ".join('"%s"' % t for t in TERMS)
    recs, seen, cursor, reported, pages = [], set(), "*", None, 0
    while True:
        url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%s"
               "&format=json&pageSize=1000&resultType=core&cursorMark=%s"
               % (urllib.parse.quote(q), urllib.parse.quote(cursor)))
        body, code = _curl(url)
        if code != "200":
            return recs, {"status": "FAILED_HTTP_%s" % code, "reported": reported,
                          "retrieved": len(recs), "pages": pages, "query": q}
        try:
            d = json.loads(body)
        except ValueError:
            return recs, {"status": "FAILED_UNPARSEABLE", "reported": reported,
                          "retrieved": len(recs), "pages": pages, "query": q}
        pages += 1
        if reported is None:
            reported = d.get("hitCount")
        res = (d.get("resultList") or {}).get("result") or []
        new = 0
        for r in res:
            key = "%s:%s" % (r.get("source"), r.get("id"))
            if key in seen:
                continue
            seen.add(key)
            new += 1
            pt = r.get("pubTypeList") or {}
            ptypes = [str(x).strip().lower()
                      for x in (pt.get("pubType") or [])]
            recs.append({"src": "europepmc", "id": key,
                         "pmid": (r.get("pmid") or "").strip(),
                         "title": " ".join((r.get("title") or "").split()),
                         "abstract": " ".join((r.get("abstractText") or "").split()),
                         "ptypes": ptypes, "year": str(r.get("pubYear") or ""),
                         "journal": ((r.get("journalInfo") or {}).get("journal")
                                     or {}).get("title") or "",
                         "accessions": []})
        nxt = d.get("nextCursorMark")
        if not res or new == 0 or not nxt or nxt == cursor:
            break
        cursor = nxt
        time.sleep(0.3)
        if pages > 12:                     # a bound, not a silent truncation
            return recs, {"status": "PAGE_BOUND_HIT", "reported": reported,
                          "retrieved": len(recs), "pages": pages, "query": q}
    status = "OK" if (isinstance(reported, int) and len(recs) >= reported) \
        else "SHORT_OF_REPORTED"
    return recs, {"status": status, "reported": reported,
                  "retrieved": len(recs), "pages": pages, "query": q}


# --------------------------------------------------------------- screen -----
def screen_one(r, ncts_held, ncts_screened):
    """Ordered rules. FIRST MATCH WINS, so the disposition is deterministic and
    the rule id is reproducible from the record alone.

    ⚠️ TWO COMPARISON SETS AND THEY ANSWER DIFFERENT QUESTIONS. `ncts_held` is
    the 2 trials this review pools; `ncts_screened` is the 63 registrations the
    registry search retrieved. A record naming a registration in the 63 tells us
    NOTHING about a search miss -- the registry search already found it. Only a
    record naming a registration OUTSIDE the 63 is a candidate search miss, and
    that is the only comparison that can measure recall. The first version of
    this rule compared against the 2 and would have reported 18 unmatched
    registrations as if they were misses when every one of them was retrieved.

    Returns (decision, rule_id, reason, field_read)."""
    title = r["title"] or ""
    abst = r["abstract"] or ""
    ta = (title + " \n " + abst).strip()
    has_abs = bool(abst)

    # R1 -- the record carries no dapivirine mention in title or abstract.
    if not RX_DAPI.search(ta):
        if not has_abs:
            return ("UNDECIDABLE", "R1b",
                    "No dapivirine term in the title and NO ABSTRACT IS "
                    "INDEXED, so absence of the term is not evidence of "
                    "absence of the drug. Named rather than excluded.",
                    "title (abstract absent)")
        return ("EXCLUDE", "R1",
                "Neither dapivirine nor any development code appears in the "
                "title or the abstract. The record matched the query in full "
                "text or in its reference list, so it is not a report OF a "
                "dapivirine study.", "title+abstract")

    # R2 -- publication type cannot be a primary trial report.
    sec = [p for p in r["ptypes"] if p in SECONDARY_TYPES]
    if sec and not RX_TRIAL.search(title):
        return ("EXCLUDE", "R2",
                "Publication type is %s and the title carries no "
                "randomised-trial signal. A secondary or non-report record "
                "cannot be a primary trial report. Systematic reviews excluded "
                "HERE belong to the published-synthesis comparison, which is a "
                "separate screen." % "/".join(sorted(set(sec))),
                "publication_type + title")

    # R3 -- no randomisation or controlled-trial signal anywhere.
    if not RX_TRIAL.search(ta):
        if not has_abs:
            return ("UNDECIDABLE", "R3b",
                    "Dapivirine is named but the title carries no "
                    "randomised-trial signal and NO ABSTRACT IS INDEXED. "
                    "Named rather than excluded.", "title (abstract absent)")
        return ("EXCLUDE", "R3",
                "Dapivirine is named but neither the title nor the abstract "
                "carries a randomisation, placebo-control, blinding or "
                "phase 2b/3 signal.", "title+abstract")

    # R4 -- dapivirine trial, but not the ring formulation.
    if not RX_RING.search(ta):
        return ("EXCLUDE", "R4",
                "A dapivirine trial signal is present but no vaginal-ring "
                "signal. Dapivirine has also been trialled as a gel and a "
                "film, which are a different intervention for this question.",
                "title+abstract")

    # PASS. Resolve against the registry set where the record names an id.
    ids = set(re.findall(r"NCT\d{8}", ta)) | {a for a in r["accessions"]
                                              if a.startswith("NCT")}
    if ids & ncts_held:
        return ("PASS_INCLUDED_TRIAL", "R5a",
                "Passes the title-and-abstract screen and names a registration "
                "this review POOLS: %s"
                % ", ".join(sorted(ids & ncts_held)), "title+abstract+accession")
    if ids and ids <= ncts_screened:
        return ("PASS_ALREADY_RETRIEVED", "R5b",
                "Passes the screen and names registration(s) the REGISTRY "
                "SEARCH ALREADY RETRIEVED and screened: %s. Not a search miss; "
                "the registry screen's own exclusion applies."
                % ", ".join(sorted(ids)), "title+abstract+accession")
    if ids:
        outside = sorted(ids - ncts_screened)
        return ("PASS_OUTSIDE_REGISTRY_SET", "R5c",
                "⚠️ Passes the screen and names registration(s) the registry "
                "search did NOT retrieve: %s. CANDIDATE SEARCH MISS -- must be "
                "resolved by hand." % ", ".join(outside),
                "title+abstract+accession")
    return ("PASS_NO_ID", "R5d",
            "Passes the title-and-abstract screen and names no registration "
            "id, so it cannot be resolved against the registry set from the "
            "abstract alone. Must be resolved by hand.", "title+abstract")


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()

    pm, pm_meta = pubmed_records()
    ep, ep_meta = europepmc_records()

    # The 63-NCT registry set from the executed search. Read from the object so
    # the two screens cannot silently diverge.
    obj = json.load(open("F:/rapidmeta-ssot-shell/ssot/agyw-hiv-prep-review/"
                         "agyw-hiv-prep-review.json", encoding="utf-8"))
    se = obj.get("search_executed_2026_08_30") or {}
    assert se.get("concept_block") == TERMS, (
        "CONCEPT BLOCK DIVERGED from the executed search -- this screen would "
        "be of a different set. object=%r here=%r" % (se.get("concept_block"), TERMS))
    ncts_held = {t["nct"] for t in obj["inputs"]["trials"]}

    # The 63 registrations the registry search retrieved. Read from the raw
    # search output, which is copied INTO the evidence directory rather than
    # left in a scratch path -- a comparison set that lives outside the repo is
    # not reproducible by the reader.
    raw_path = os.path.join(OUTDIR, "REGISTRY_SEARCH_RAW.json")
    if not os.path.exists(raw_path):
        raise SystemExit(
            "REGISTRY_SEARCH_RAW.json is absent at %s. The recall comparison "
            "cannot be made without the retrieved registration set, and "
            "comparing against the 2 included trials instead would report "
            "every companion paper as a search miss. Re-run "
            "scripts/systematic_search_dapivirine.py and copy its output "
            "here." % raw_path)
    ncts_screened = set(json.load(open(raw_path, encoding="utf-8"))
                        ["ctgov_union_ids"])
    assert ncts_held <= ncts_screened, (
        "The included trials are not inside the retrieved set -- the search "
        "output and the object disagree about what was retrieved. held=%r "
        "missing=%r" % (sorted(ncts_held), sorted(ncts_held - ncts_screened)))

    # ------------------------------------------------------ NEGATIVE TEST ---
    # A guard that has never fired is not proven. Two SYNTHETIC records are put
    # through the same rules: one that MUST come out as a candidate search miss
    # and one that MUST be excluded. They are scored, asserted, and then
    # DISCARDED -- they never enter the ledger and never enter a denominator,
    # because a control is neither data nor a defect and code that knows only
    # two kinds mishandles it.
    _probe_pass = {"title": ("A randomised, double-blind, placebo-controlled "
                             "phase 3 trial of a dapivirine vaginal ring "
                             "(NCT99999999)"),
                   "abstract": "", "ptypes": [], "accessions": []}
    _probe_excl = {"title": "Editorial: the future of HIV prevention",
                   "abstract": ("We reflect on dapivirine and other agents. No "
                                "new data are presented."),
                   "ptypes": ["editorial"], "accessions": []}
    _d1 = screen_one(_probe_pass, ncts_held, ncts_screened)
    _d2 = screen_one(_probe_excl, ncts_held, ncts_screened)
    assert _d1[0] == "PASS_OUTSIDE_REGISTRY_SET", (
        "NEGATIVE TEST FAILED: a planted randomised dapivirine-ring trial "
        "naming an unretrieved registration was NOT flagged as a candidate "
        "search miss. It scored %r. The screen cannot report a miss rate until "
        "it can produce one." % (_d1,))
    assert _d2[0] == "EXCLUDE", (
        "NEGATIVE TEST FAILED: a planted editorial was not excluded. It scored "
        "%r." % (_d2,))
    negative_test = {
        "what": ("Two synthetic records put through the same rules before the "
                 "real screen runs: one that must be flagged as a candidate "
                 "search miss, one that must be excluded."),
        "planted_miss_scored": _d1[0] + " / " + _d1[1],
        "planted_editorial_scored": _d2[0] + " / " + _d2[1],
        "both_passed": True,
        "controls_are_not_in_the_denominator": (
            "The two probes are discarded after scoring. They are not in "
            "`ledger` and not in `records_screened`. A control that enters the "
            "counted population has stopped being a control."),
    }

    # Dedup: PMID where present, else source:id. Europe PMC indexes MEDLINE, so
    # ADDING the two counts would double-count most of the corpus.
    merged, by_key, dups = [], {}, 0
    for r in pm + ep:
        key = ("pmid:" + r["pmid"]) if r.get("pmid") else (r["src"] + ":" + r["id"])
        if key in by_key:
            dups += 1
            by_key[key]["also_in"].append(r["src"])
            # Prefer whichever copy actually has an abstract.
            if not by_key[key]["abstract"] and r["abstract"]:
                by_key[key]["abstract"] = r["abstract"]
            if not by_key[key]["ptypes"]:
                by_key[key]["ptypes"] = r["ptypes"]
            continue
        r = dict(r)
        r["key"] = key
        r["also_in"] = [r["src"]]
        by_key[key] = r
        merged.append(r)

    ledger, counts = [], {}
    for r in merged:
        dec, rule, reason, field = screen_one(r, ncts_held, ncts_screened)
        counts[dec] = counts.get(dec, 0) + 1
        ledger.append({"key": r["key"], "pmid": r["pmid"], "src": r["also_in"],
                       "year": r["year"], "journal": r["journal"],
                       "title": r["title"], "has_abstract": bool(r["abstract"]),
                       "ptypes": r["ptypes"], "decision": dec, "rule": rule,
                       "reason": reason, "field_read": field})

    out = {
        "_what": ("Per-record title-and-abstract screen of the BIBLIOGRAPHIC "
                  "half of the executed dapivirine search. One row per "
                  "deduplicated record."),
        "executed_utc": started,
        "concept_block": TERMS,
        "sources": {"pubmed": pm_meta, "europepmc": ep_meta},
        "denominator": {
            "pubmed_records": len(pm),
            "europepmc_records": len(ep),
            "sum_before_dedup": len(pm) + len(ep),
            "duplicates_removed": dups,
            "records_screened": len(merged),
            "_what_the_denominator_is_of": (
                "DEDUPLICATED BIBLIOGRAPHIC RECORDS returned by the two free "
                "bibliographic sources for the concept block. It is NOT the "
                "literature, and it is NOT the registry set of 63 "
                "registrations, which is screened separately."),
        },
        "decisions": counts,
        "rules": {
            "R1": "no dapivirine term in title or abstract -> EXCLUDE",
            "R1b": "no dapivirine term in title AND no abstract -> UNDECIDABLE",
            "R2": "secondary publication type and no trial signal in title -> EXCLUDE",
            "R3": "no randomisation/control/phase signal -> EXCLUDE",
            "R3b": "no trial signal in title AND no abstract -> UNDECIDABLE",
            "R4": "trial signal but no vaginal-ring signal -> EXCLUDE",
            "R5a": "passes; names an NCT this review pools",
            "R5b": "passes; names an NCT the registry search already retrieved -- NOT a miss",
            "R5c": "passes; names an NCT the registry search did NOT retrieve -- CANDIDATE MISS",
            "R5d": "passes; names no id -- resolve by hand",
        },
        "negative_test": negative_test,
        "comparison_sets": {
            "ncts_pooled_by_this_review": sorted(ncts_held),
            "ncts_retrieved_by_the_registry_search": len(ncts_screened),
            "_why_two": (
                "A record naming one of the 63 retrieved registrations is not "
                "evidence of a search miss -- the registry search found it. "
                "Only a registration OUTSIDE the 63 can be one."),
        },
        "ledger": ledger,
    }
    os.makedirs(OUTDIR, exist_ok=True)
    path = os.path.join(OUTDIR, "BIBLIOGRAPHIC_SCREEN.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

    print("BIBLIOGRAPHIC SCREEN -- dapivirine, free sources only")
    print("executed %s" % started)
    print()
    print("  PubMed      status=%-18s reported=%-6s retrieved=%d"
          % (pm_meta["status"], pm_meta.get("reported"), pm_meta["retrieved"]))
    print("  Europe PMC  status=%-18s reported=%-6s retrieved=%d  pages=%s"
          % (ep_meta["status"], ep_meta.get("reported"), ep_meta["retrieved"],
             ep_meta.get("pages")))
    print()
    print("  %d + %d = %d before dedup; %d duplicates removed; %d SCREENED"
          % (len(pm), len(ep), len(pm) + len(ep), dups, len(merged)))
    print()
    for k in sorted(counts):
        print("    %-20s %5d / %d screened" % (k, counts[k], len(merged)))
    print()
    passes = [r for r in ledger if r["decision"].startswith("PASS")]
    und = [r for r in ledger if r["decision"] == "UNDECIDABLE"]
    print("  PASSED (%d of %d) -- every one named:" % (len(passes), len(merged)))
    for r in passes:
        print("    [%s] %s (%s) %s" % (r["rule"], r["pmid"] or r["key"],
                                       r["year"], r["title"][:110]))
    print()
    print("  UNDECIDABLE (%d of %d) -- named, NOT excluded" % (len(und), len(merged)))
    for r in und[:40]:
        print("    [%s] %s (%s) %s" % (r["rule"], r["pmid"] or r["key"],
                                       r["year"], r["title"][:110]))
    if len(und) > 40:
        print("    ... %d more in the ledger" % (len(und) - 40))
    print()
    print("  written to %s" % path)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
