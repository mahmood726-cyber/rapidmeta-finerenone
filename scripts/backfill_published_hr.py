"""Backfill publishedHR / hrLCI / hrUCI on audit-first builds from PubMed
abstracts using the V2 RCT extractor.

For each VIABLE audit-first topic:
  - For each trial with a PMID, load the cached abstract.
  - Run V2 EnhancedExtractor on the abstract text.
  - Pick the best HR (or OR/RR) extraction (first in document order; highest
    confidence if tied) as the trial-published effect.
  - Write publishedHR, hrLCI, hrUCI, published_effect_type, published_source
    to the trial's `extracted` block in outputs/new_topics/<STEM>.json.
"""
from __future__ import annotations
import json, sys, io, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path("C:/Projects/rct-extractor-v2/src").resolve()))
from core.enhanced_extractor_v3 import EnhancedExtractor, to_dict  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
TOPICS = HERE / "outputs" / "new_topics"
PUBMED_CACHE = HERE / "outputs" / "extraction_audit" / "pubmed_cache"

# Preferred effect types in order
PREFERRED_TYPES = ("HR", "OR", "RR", "IRR", "ARD", "MD", "SMD")


def pick_best_extraction(extractions):
    """Pick a single 'published' effect estimate from a list of v2 extractions.

    Strategy:
      - Prefer HR > OR > RR > IRR > ARD > MD > SMD.
      - Within a type, prefer the first one with a CI present.
      - Skip extractions where CI is missing (less useful for cross-check).
    """
    by_type = {}
    for e in extractions:
        d = to_dict(e)
        t = d.get("type")
        if t in by_type: continue
        if d.get("ci_lower") is None or d.get("ci_upper") is None: continue
        # Sanity: HR/OR/RR should be positive; reject obvious junk
        es = d.get("effect_size")
        if es is None: continue
        try: es = float(es)
        except: continue
        if t in ("HR","OR","RR","IRR") and (es <= 0 or es > 50): continue
        by_type[t] = d
    for pt in PREFERRED_TYPES:
        if pt in by_type:
            return by_type[pt]
    return None


def load_abstract(pmid):
    p = PUBMED_CACHE / f"{pmid}.json"
    if not p.exists(): return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        title = d.get("title") or ""
        abstract = d.get("abstract") or ""
        if not abstract: return None
        return title + "\n" + abstract
    except Exception:
        return None


def fetch_missing_pmids(pmids, batch_size=50):
    """Fetch missing PMID abstracts from PubMed efetch and persist to cache."""
    missing = [pm for pm in pmids if not (PUBMED_CACHE / f"{pm}.json").exists()]
    if not missing:
        return 0
    PUBMED_CACHE.mkdir(parents=True, exist_ok=True)
    print(f"Fetching {len(missing)} missing PMIDs from PubMed...")
    fetched = 0
    for i in range(0, len(missing), batch_size):
        batch = missing[i:i+batch_size]
        params = {"db": "pubmed", "id": ",".join(batch),
                   "rettype": "abstract", "retmode": "xml"}
        url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
               + urllib.parse.urlencode(params))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                xml_data = r.read()
            root = ET.fromstring(xml_data)
            for art in root.findall(".//PubmedArticle"):
                pmid_el = art.find(".//PMID")
                if pmid_el is None: continue
                pmid = pmid_el.text.strip()
                title_el = art.find(".//ArticleTitle")
                title = ("".join(title_el.itertext()).strip()
                          if title_el is not None else "")
                abs_pieces = []
                for at in art.findall(".//Abstract/AbstractText"):
                    txt = "".join(at.itertext()).strip()
                    if txt: abs_pieces.append(txt)
                abstract = " ".join(abs_pieces)
                year_el = art.find(".//PubDate/Year")
                year = year_el.text if year_el is not None else None
                doi = ""
                for aid in art.findall(".//ArticleId"):
                    if aid.get("IdType") == "doi":
                        doi = (aid.text or "").strip(); break
                journal_el = art.find(".//Journal/Title")
                journal = (journal_el.text or "").strip() if journal_el is not None else ""
                (PUBMED_CACHE / f"{pmid}.json").write_text(
                    json.dumps({"title": title, "abstract": abstract,
                                 "year": (int(year) if year and year.isdigit() else None),
                                 "doi": doi, "journal": journal},
                                ensure_ascii=False),
                    encoding="utf-8")
                fetched += 1
        except Exception as e:
            print(f"  efetch error on batch {i}: {e}")
        time.sleep(0.4)
        if i and i % 200 == 0:
            print(f"  ...fetched {fetched}/{len(missing)} so far")
    print(f"Fetched {fetched}/{len(missing)} new abstracts")
    return fetched


def collect_pmids():
    pmids = set()
    for topic_p in sorted(TOPICS.glob("*.json")):
        try:
            doc = json.loads(topic_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if doc.get("verdict") != "VIABLE": continue
        for trial in doc["trials"]:
            if not all(trial["gates"].values()): continue
            pm = trial["extracted"].get("pmid")
            if pm: pmids.add(pm)
    return pmids


def main():
    # Phase 1: fetch any missing PubMed abstracts so the V2 extractor has text
    all_pmids = collect_pmids()
    print(f"Audit-first PMIDs needed: {len(all_pmids)}")
    fetch_missing_pmids(sorted(all_pmids))

    # Phase 2: run V2 extractor on every available abstract
    ext = EnhancedExtractor()
    stats = {"topics_processed": 0, "trials_processed": 0,
             "trials_with_pmid": 0, "trials_with_cache": 0,
             "extractions_made": 0,
             "by_type": {}}

    for topic_p in sorted(TOPICS.glob("*.json")):
        try:
            doc = json.loads(topic_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if doc.get("verdict") != "VIABLE":
            continue
        stats["topics_processed"] += 1
        any_change = False

        for trial in doc["trials"]:
            if not all(trial["gates"].values()):
                continue
            stats["trials_processed"] += 1
            ex = trial["extracted"]
            pmid = ex.get("pmid")
            if not pmid:
                continue
            stats["trials_with_pmid"] += 1

            text = load_abstract(pmid)
            if not text:
                continue
            stats["trials_with_cache"] += 1

            # Allow re-runs to overwrite (e.g. when regex coverage improves)

            extractions = ext.extract(text)
            if not extractions:
                continue
            best = pick_best_extraction(extractions)
            if not best:
                continue

            stats["extractions_made"] += 1
            t = best["type"]
            stats["by_type"][t] = stats["by_type"].get(t, 0) + 1

            # Snippet around the extraction
            src_text = best.get("source_text") or ""
            ex["published_effect_type"] = t
            ex["published_effect_size"] = best.get("effect_size")
            ex["published_ci_lower"] = best.get("ci_lower")
            ex["published_ci_upper"] = best.get("ci_upper")
            ex["published_source_snippet"] = src_text[:240] if src_text else ""
            ex["published_extractor"] = "rct-extractor-v2"
            any_change = True

        if any_change:
            topic_p.write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                                encoding="utf-8")

    print(f"Topics processed: {stats['topics_processed']}")
    print(f"Trials processed: {stats['trials_processed']}")
    print(f"Trials with PMID: {stats['trials_with_pmid']}")
    print(f"Trials with cached abstract: {stats['trials_with_cache']}")
    print(f"Extractions made: {stats['extractions_made']} "
          f"({100*stats['extractions_made']/max(stats['trials_with_cache'],1):.1f}% of cached)")
    print(f"By type: {stats['by_type']}")


if __name__ == "__main__":
    main()
