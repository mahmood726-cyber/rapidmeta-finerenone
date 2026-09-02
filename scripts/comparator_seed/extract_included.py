"""PHASE 2 - extract a comparator's INCLUDED-STUDY list from structured JATS.

No prose regex. An included study is a reference *cited from the study-characteristics
table* (route TABLE) or from an included-studies section (route SECTION). Both are
positions in the XML tree, not strings in a sentence. Identifier fields (NCT, PMID,
DOI) are matched as identifiers, which is a different thing from matching prose.

A field that is null was LOOKED FOR AND NOT FOUND; every record carries
`fields_not_found` naming which, so null can never be read as "the field does not apply".

Self-test (`--selftest`) runs a planted document the extractor MUST match, and a
negative document it MUST report as NOT_FOUND rather than as an empty success.
"""
import argparse
import glob
import hashlib
import json
import io
import os
import re
import sys
import xml.etree.ElementTree as ET

# Guarded: a module-level stdout reassignment closes the caller's wrapper on import.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TABLE_CAPTION_RE = re.compile(
    r"characteristic|included stud|studies included|study selection|"
    r"summary of (the )?(included )?(stud|trial)|overview of (the )?(stud|trial)|"
    r"included trial|trial characteristic|baseline characteristic",
    re.I,
)
SECTION_TITLE_RE = re.compile(
    r"included stud|studies included|characteristics of (the )?(included )?stud|"
    r"study characteristic|description of stud",
    re.I,
)
# `\bNCT\d{8}\b` fails on run-together citation text ("...2019NCT12345678"): there is no
# word boundary between a digit and "N", so the id is silently missed. Caught by the planted
# case. A preceding DIGIT is the normal run-together case and must be allowed; only a
# preceding LETTER means we are inside a longer token. A 9th digit means it is not an NCT id.
NCT_RE = re.compile(r"(?<![A-Za-z])NCT\d{8}(?!\d)")
ACRONYM_RE = re.compile(r"\b([A-Z][A-Z0-9]{2,}(?:[-\u2010-\u2015][A-Z0-9]+)*)\b")
ACRONYM_STOP = {
    "RCT", "RCTS", "CI", "OR", "RR", "HR", "SD", "SE", "USA", "UK", "WHO", "NCT",
    "PRISMA", "GRADE", "MD", "SMD", "NA", "ITT", "PP", "AE", "SAE", "BMI", "II",
    "III", "IV", "VI", "PICO", "MESH", "PROSPERO", "DOI", "PMID", "ISRCTN", "AND",
    "THE", "NOT", "FOR", "NR", "NS", "ALL", "ANY", "TWO", "ONE", "PDF", "HTML",
}


def text_of(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def strip_ns(tree):
    for el in tree.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
        for k in list(el.attrib):
            if "}" in k:
                el.attrib[k.split("}", 1)[1]] = el.attrib.pop(k)
    return tree


def parse_refs(root):
    """rid -> structured reference record."""
    refs = {}
    for ref in root.iter("ref"):
        rid = ref.get("id")
        if not rid:
            continue
        raw = text_of(ref)
        surnames = [text_of(s) for s in ref.iter("surname")]
        years = [text_of(y) for y in ref.iter("year")]
        titles = [text_of(t) for t in ref.iter("article-title")]
        ids = {}
        for pid in ref.iter("pub-id"):
            t = pid.get("pub-id-type")
            if t:
                ids[t.lower()] = text_of(pid)
        nct = NCT_RE.search(raw)
        rec = {
            "rid": rid,
            "first_author": surnames[0] if surnames else None,
            "year": years[0] if years else None,
            "title": titles[0] if titles else None,
            "pmid": ids.get("pmid"),
            "doi": ids.get("doi"),
            "nct": nct.group(0) if nct else None,
            "acronym": None,
            "raw_citation": raw[:400] or None,
        }
        src = (rec["title"] or "") + " " + (raw[:200] if not rec["title"] else "")
        cands = [a for a in ACRONYM_RE.findall(src) if a.upper() not in ACRONYM_STOP]
        rec["acronym"] = cands[0] if cands else None
        refs[rid] = rec
    return refs


def bibr_rids(el):
    out = []
    for x in el.iter("xref"):
        if (x.get("ref-type") or "") == "bibr":
            for rid in (x.get("rid") or "").split():
                out.append(rid)
    return out


def extract(root):
    """Return (included_rids, route, evidence, refs). Never a silent empty."""
    refs = parse_refs(root)

    best = None
    for tw in root.iter("table-wrap"):
        cap = " ".join([text_of(tw.find("label")), text_of(tw.find("caption"))]).strip()
        if not TABLE_CAPTION_RE.search(cap):
            continue
        rids = [r for r in dict.fromkeys(bibr_rids(tw)) if r in refs]
        if len(rids) >= 2 and (best is None or len(rids) > len(best[0])):
            best = (rids, "TABLE", cap[:200])
    if best:
        return best[0], best[1], best[2], refs

    for sec in root.iter("sec"):
        title = text_of(sec.find("title"))
        if not title or not SECTION_TITLE_RE.search(title):
            continue
        rids = [r for r in dict.fromkeys(bibr_rids(sec)) if r in refs]
        if len(rids) >= 2 and (best is None or len(rids) > len(best[0])):
            best = (rids, "SECTION", title[:200])
    if best:
        return best[0], best[1], best[2], refs

    return [], "NOT_FOUND", "no study-characteristics table or included-studies section with >=2 cited refs", refs


# efetch emits the PMC id under either pub-id-type, depending on the depositing publisher.
# Keying on one of them silently nulls the provenance field on the other half of the corpus.
META_XPATH = {
    "doi": ['.//article-meta/article-id[@pub-id-type="doi"]'],
    "pmid": ['.//article-meta/article-id[@pub-id-type="pmid"]'],
    "pmcid": ['.//article-meta/article-id[@pub-id-type="pmc"]',
              './/article-meta/article-id[@pub-id-type="pmcid"]'],
}


def article_meta(root):
    out = {}
    for k, xps in META_XPATH.items():
        out[k] = None
        for xp in xps:
            v = text_of(root.find(xp))
            if v:
                out[k] = v
                break
    out["title"] = text_of(root.find(".//article-meta//article-title")) or None
    out["journal"] = text_of(root.find(".//journal-meta//journal-title")) or None
    yr = root.find('.//article-meta//pub-date[@pub-type="epub"]/year')
    if yr is None:
        yr = root.find(".//article-meta//pub-date/year")
    out["year"] = text_of(yr) or None
    return out


def process_file(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    root = strip_ns(ET.ElementTree(ET.fromstring(raw))).getroot()
    meta = article_meta(root)
    if not meta["pmcid"]:
        # The filename is the id efetch was asked for. Provenance must never be null.
        m = re.match(r"PMC(\d+)\.xml$", os.path.basename(path))
        meta["pmcid"] = m.group(1) if m else None
        meta["pmcid_source"] = "filename"
    else:
        meta["pmcid_source"] = "article-id"
    # Publishers deposit the id both with and without the "PMC" prefix; normalise so a
    # join on pmcid cannot silently miss half the corpus.
    if meta["pmcid"]:
        meta["pmcid"] = re.sub(r"^PMC", "", meta["pmcid"].strip())
    rids, route, evidence, refs = extract(root)
    included = []
    for rid in rids:
        r = dict(refs[rid])
        nf = [k for k in ("first_author", "year", "acronym", "nct", "pmid", "doi") if not r.get(k)]
        r["fields_not_found"] = nf
        r["found_via"] = "FOUND_VIA_COMPARATOR"
        r["seed_source_pmcid"] = meta["pmcid"]
        r["seed_source_doi"] = meta["doi"]
        included.append(r)
    return {
        **meta,
        "source_file": os.path.basename(path),
        "source_sha256": hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest(),
        "n_refs_total": len(refs),
        "extraction_route": route,
        "extraction_evidence": evidence,
        "k_extracted": len(included),
        "included_studies": included,
    }


PLANTED_POSITIVE = """<article>
<front><journal-meta><journal-title>Planted J</journal-title></journal-meta>
<article-meta><article-id pub-id-type="doi">10.0000/planted</article-id>
<article-id pub-id-type="pmc">PMC0000001</article-id>
<title-group><article-title>Planted review of widgets</article-title></title-group>
<pub-date pub-type="epub"><year>2020</year></pub-date></article-meta></front>
<body><sec><title>Results</title>
<table-wrap id="t1"><label>Table 1</label><caption><p>Characteristics of included studies</p></caption>
<table><tr><td>ALPHA <xref ref-type="bibr" rid="r1">1</xref></td></tr>
<tr><td>BETA <xref ref-type="bibr" rid="r2">2</xref></td></tr>
<tr><td>GAMMA <xref ref-type="bibr" rid="r3">3</xref></td></tr></table></table-wrap>
<p>Background cite <xref ref-type="bibr" rid="r4">4</xref>.</p></sec></body>
<back><ref-list>
<ref id="r1"><element-citation><name><surname>Smith</surname></name><article-title>ALPHA trial of widgets</article-title><year>2018</year><pub-id pub-id-type="pmid">11111111</pub-id></element-citation></ref>
<ref id="r2"><element-citation><name><surname>Jones</surname></name><article-title>BETA trial</article-title><year>2019</year>NCT12345678</element-citation></ref>
<ref id="r3"><element-citation><name><surname>Lee</surname></name><article-title>GAMMA study</article-title><year>2021</year></element-citation></ref>
<ref id="r4"><element-citation><name><surname>Background</surname></name><article-title>Not a trial</article-title><year>2001</year></element-citation></ref>
</ref-list></back></article>"""

PLANTED_NEGATIVE = PLANTED_POSITIVE.replace(
    "<caption><p>Characteristics of included studies</p></caption>",
    "<caption><p>Search strategy for MEDLINE</p></caption>",
).replace("<title>Results</title>", "<title>Discussion</title>")


def selftest():
    ok = True
    root = strip_ns(ET.ElementTree(ET.fromstring(PLANTED_POSITIVE))).getroot()
    rids, route, ev, refs = extract(root)
    got = [refs[r]["acronym"] for r in rids]
    exp = ["ALPHA", "BETA", "GAMMA"]
    print("POSITIVE  route=%-8s k=%d acronyms=%s" % (route, len(rids), got))
    if route != "TABLE" or len(rids) != 3 or got != exp:
        print("  FAIL: planted case must yield exactly %s via TABLE" % exp)
        ok = False
    if "r4" in rids:
        print("  FAIL: background reference r4 leaked into the included set")
        ok = False
    if refs["r1"]["pmid"] != "11111111" or refs["r2"]["nct"] != "NCT12345678":
        print("  FAIL: identifier fields not lifted")
        ok = False
    if refs["r3"]["pmid"] is not None:
        print("  FAIL: absent pmid must be null")
        ok = False
    # Identifier traps: a 9-digit run and a letter-prefixed token are not NCT ids.
    for bad in ("NCT123456789", "XNCT12345678", "aNCT12345678"):
        if NCT_RE.search("ref text 2019" + bad):
            print("  FAIL: %s must not match as an NCT id" % bad)
            ok = False
    for good in ("2019NCT12345678", " NCT12345678.", "(NCT12345678)"):
        if not NCT_RE.search(good):
            print("  FAIL: %r must match as an NCT id" % good)
            ok = False

    root = strip_ns(ET.ElementTree(ET.fromstring(PLANTED_NEGATIVE))).getroot()
    rids, route, ev, _ = extract(root)
    print("NEGATIVE  route=%-8s k=%d" % (route, len(rids)))
    if route != "NOT_FOUND" or rids:
        print("  FAIL: a document with no characteristics table must report NOT_FOUND")
        ok = False

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cache", default=r"C:/claude-temp/comparator-seed/xml")
    ap.add_argument("--out", default=r"C:/claude-temp/comparator-seed/work/extracted.json")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    if args.selftest:
        raise SystemExit(selftest())

    files = sorted(glob.glob(os.path.join(args.cache, "PMC*.xml")))
    if args.limit:
        files = files[: args.limit]
    rows, broken = [], []
    for p in files:
        try:
            rows.append(process_file(p))
        except Exception as exc:  # noqa: BLE001
            broken.append({"file": os.path.basename(p), "error": "%s: %s" % (type(exc).__name__, exc)})
    routes = {}
    for r in rows:
        routes[r["extraction_route"]] = routes.get(r["extraction_route"], 0) + 1
    missing = sorted(glob.glob(os.path.join(args.cache, "PMC*.MISSING")))
    payload = {
        "n_xml_files": len(files),
        "n_efetch_missing": len(missing),
        "n_parse_errors": len(broken),
        "parse_errors": broken,
        "routes": routes,
        "articles": rows,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
    print("files=%d  efetch_missing=%d  parse_errors=%d  routes=%s" % (
        len(files), len(missing), len(broken), routes))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
