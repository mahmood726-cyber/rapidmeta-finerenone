# -*- coding: utf-8 -*-
"""STAGE the comparator texts for the scored run. Fetch, record WHICH text, refuse to guess.

⛔⛔ THE TEXT SOURCE IS A FIELD, NOT A FOOTNOTE. A rubric scored on an ABSTRACT and a rubric
scored on a FULL TEXT are not comparable. This project has already measured what that
substitution does: swapping a Cochrane objectives statement (one or two sentences) for an
abstract (~250 words) moved `MATCHED` from 6/20 to 16/20 **with no rule change at all**. So
every staged record carries `text_source` ∈ {oa_full_text, abstract, unavailable} and no
consumer may pool across them.

⭐ AND A DETECTOR CONTROL, because "full text" is a claim. A fetch that returns something the
same length as the abstract is not full text, whatever the endpoint is called. Every
`oa_full_text` record is required to be materially longer than that record's own abstract,
and one that is not is DOWNGRADED to `abstract` and named.

⛔ THE TEXTS ARE STAGED OUTSIDE THE REPO. ~20 open-access papers is megabytes of third-party
text; the repo gets the MANIFEST -- pmid, source, chars, sha256, licence, path -- which is
what a later run needs to prove it scored the same bytes.

⚠️ THE COMPARATOR LIST IS READ FROM ANOTHER LANE'S WORKTREE, BY EXPLICIT PATH, AND HASHED.
`TWENTY_COMPARATORS.json` is owned by the surfaces lane. Reading it across worktrees is fine;
reading it without recording WHICH version was read is not, so its sha256 goes in the
manifest. That file's own header warns its frame `doi` field is KNOWN WRONG -- the extractor
walked into ReferenceList -- so DOIs here come from the file's per-PMID resolved field, never
from a frame.

FREE SOURCES ONLY: Europe PMC REST. No key.

PREDICTION, recorded before the run:
    of 20 distinct comparator PMIDs, I predict 12-17 return genuine OA full text.
    Mechanism: the selection rule required open access, but OPEN_ACCESS in a bibliographic
    record means the ARTICLE is free, not that Europe PMC holds a machine-readable full text
    for it -- those are different facts and the second is rarer. I expect the gap to be the
    finding.
"""
import hashlib
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)

COMPARATORS = "F:/rapidmeta-xsurface/TWENTY_COMPARATORS.json"
STAGE = "F:/claude-temp/scored-run/texts"
MANIFEST = "../../evidence/2026-09-01-scored-run/comparator_text_manifest.json"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
MIN_FULLTEXT_RATIO = 2.0     # full text must be >= 2x its own abstract, declared before use


def _get(url, tries=4, as_json=False):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as fh:
                b = fh.read()
            return (json.loads(b.decode("utf-8")) if as_json
                    else b.decode("utf-8", "replace")), "OK"
        except Exception as e:                                   # noqa: BLE001
            if a == tries - 1:
                return None, "ERROR_%s" % type(e).__name__
            time.sleep(1.5 + 2.0 * a)
    return None, "ERROR"


def core(pmid):
    d, st = _get("%s/search?query=EXT_ID:%s&format=json&resultType=core"
                 % (EPMC, urllib.parse.quote(pmid)), as_json=True)
    if not d:
        return None, st
    res = (d.get("resultList") or {}).get("result") or []
    return (res[0] if res else None), ("OK" if res else "NO_RECORD")


def full_text(pmcid):
    """Europe PMC full-text XML, OA subset only."""
    if not pmcid:
        return None, "NO_PMCID"
    t, st = _get("%s/%s/fullTextXML" % (EPMC, pmcid))
    return t, st


def strip_xml(x):
    import re
    x = re.sub(r"(?s)<(ref-list|back|front)\b.*?</\1>", " ", x or "")
    x = re.sub(r"(?s)<[^>]+>", " ", x)
    return " ".join(x.split())


def downgrade_decision(body_chars, abstract_chars):
    """-> True if a claimed full text must be DOWNGRADED to abstract. The ONE place the
    rule lives, so the probe below exercises the same code the run does."""
    return bool(body_chars and abstract_chars
                and body_chars < MIN_FULLTEXT_RATIO * abstract_chars)


def selftest():
    """⭐ DETECTOR CONTROL. The run staged 20 of 20 as full text and downgraded NOTHING, so
    the downgrade branch was never exercised by real data -- and a control that never fires
    is a guess, not a control. These prove it CAN fire and that it DISCRIMINATES."""
    cases = [
        ("plant: 'full text' shorter than 2x its abstract", 1800, 1200, True),
        ("plant: 'full text' EQUAL to its abstract", 1800, 1800, True),
        ("clean sibling: a genuine full text (17x)", 31510, 1800, False),
        ("clean sibling: exactly at the 2.0x threshold", 3600, 1800, False),
        ("edge: no abstract to compare against -> cannot downgrade", 500, 0, False),
    ]
    ok = True
    print("=== DETECTOR CONTROL for the downgrade branch ===")
    for label, body, abst, want in cases:
        got = downgrade_decision(body, abst)
        ok = ok and (got == want)
        print("   %-52s body=%-6d abs=%-5d -> %-5s want %-5s %s"
              % (label, body, abst, got, want, "OK" if got == want else "FAIL"))
    print("   %s" % ("all hold -- the branch fires, and does not fire on a real full text"
                     if ok else "⛔ CONTROL FAILED"))
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    raw = io.open(COMPARATORS, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    src_sha = hashlib.sha256(raw).hexdigest()
    pairs = doc["comparators"]
    pmids = sorted({p["comparator_pmid"] for p in pairs})

    os.makedirs(STAGE, exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)

    print("=== REF ===")
    print("   source list   %s" % COMPARATORS)
    print("   source sha256 %s" % src_sha[:16])
    print("   pairs %d  ->  DISTINCT comparator PMIDs %d" % (len(pairs), len(pmids)))
    print("   ⚠️ 20 comparators produce 24 pairs. The pair count is NOT a review count.")
    print("   staging dir   %s   (texts OUTSIDE the repo; manifest inside)" % STAGE)
    print("")
    print("   %-12s %-9s %9s %9s %-10s %s"
          % ("pmid", "source", "abs_chars", "txt_chars", "licence", "note"))

    out = []
    for pmid in pmids:
        rec, st = core(pmid)
        time.sleep(0.3)
        if rec is None:
            out.append({"pmid": pmid, "text_source": "unavailable", "status": st})
            print("   %-12s %-9s %9s %9s %-10s %s" % (pmid, "UNAVAIL", "-", "-", "-", st))
            continue
        abstract = (rec.get("abstractText") or "").strip()
        pmcid = rec.get("pmcid")
        lic = rec.get("license") or "-"
        ft, fst = (full_text(pmcid) if rec.get("isOpenAccess") == "Y" else (None, "NOT_OA"))
        time.sleep(0.3)
        body = strip_xml(ft) if ft else ""
        note = ""
        if downgrade_decision(len(body), len(abstract)):
            # ⭐ THE DETECTOR CONTROL. A "full text" no longer than its own abstract is not
            # full text; the endpoint returning 200 is not the claim being made.
            note = "DOWNGRADED: fullTextXML only %.1fx the abstract" % (
                len(body) / float(len(abstract)))
            body = ""
        if body:
            source, text = "oa_full_text", body
        elif abstract:
            source, text = "abstract", abstract
        else:
            source, text = "unavailable", ""
        path = ""
        if text:
            path = os.path.join(STAGE, "%s.%s.txt" % (pmid, source))
            io.open(path, "w", encoding="utf-8").write(text)
        out.append({"pmid": pmid, "pmcid": pmcid, "text_source": source,
                    "abstract_chars": len(abstract), "text_chars": len(text),
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None,
                    "licence": lic, "is_open_access": rec.get("isOpenAccess"),
                    "fulltext_status": fst, "path": path, "note": note,
                    "title": (rec.get("title") or "")[:200]})
        print("   %-12s %-9s %9d %9d %-10s %s"
              % (pmid, source, len(abstract), len(text), str(lic)[:10], note or fst))

    from collections import Counter
    c = Counter(r["text_source"] for r in out)
    print("")
    print("=== STAGED ===")
    for k in ("oa_full_text", "abstract", "unavailable"):
        print("   %-14s %2d" % (k, c.get(k, 0)))
    print("   %-14s %2d   sums: %s" % ("TOTAL", sum(c.values()),
                                       "HOLDS" if sum(c.values()) == len(pmids) else "BROKEN"))
    down = [r for r in out if r.get("note")]
    print("")
    print("   DOWNGRADED by the length control: %d" % len(down))
    for r in down:
        print("      %-12s %s" % (r["pmid"], r["note"]))
    print("")
    print("   ⛔ oa_full_text and abstract records MAY NOT BE POOLED in any score.")
    print("     `text_source` is a field on every record for exactly that reason.")

    json.dump({"source_list": COMPARATORS, "source_sha256": src_sha,
               "min_fulltext_ratio": MIN_FULLTEXT_RATIO,
               "pairs": len(pairs), "distinct_pmids": len(pmids),
               "records": out}, io.open(MANIFEST, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("")
    print("   manifest: %s" % MANIFEST)


if __name__ == "__main__":
    main()
