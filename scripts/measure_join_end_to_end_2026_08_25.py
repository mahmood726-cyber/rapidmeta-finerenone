"""End to end: a real Cochrane label, through to a registration, with its own null.

WHAT THIS IS. The three stages measured separately this week are run as one pipeline on REAL
Cochrane labels rather than labels reconstructed from PubMed records:

    Study label ("Carter 1970")
      -> the review's own bibliography, via review_doi + Crossref
      -> that reference's DOI
      -> PMID, via the NCBI id converter
      -> NCT, via PubMed's DataBank secondary-id field

NO STAGE RATE IS MULTIPLIED. Each stage's survivors are counted directly and the end-to-end
figure is labels-with-an-NCT over labels-attempted, one denominator, measured not derived.
Multiplying 75% x 97% x 94% from three different samples is the error this project has
corrected twice this week and will not commit here.

THE NULL, AND IT MATTERS MORE AT THIS SCALE. Every label is also run against a DIFFERENT
review's bibliography (a fixed derangement: review i is scored against review i+1). A label
that resolves there resolved on nothing. With 886 labels and bibliographies of a few hundred
references, spurious surname+year agreement is not a remote possibility -- it is the thing
most likely to inflate this number, so it is measured rather than assumed away.

SAMPLE, FIXED BEFORE THE RUN. Every 15th of the 595 .rda files in Pairwise70/data,
alphabetical: 40 reviews, 886 distinct study labels. The rule is stated so the sample is
reproducible and was not chosen after seeing which reviews behaved.

WHAT COUNTS AS RESOLVED. Exactly ONE reference in the bibliography matches the label. Two or
more is NOT resolved -- it is the 3% collision case, and counting it as a hit would be
counting a coin flip as a join. Matching is strict on year by default; a +/-1 year variant is
reported separately and never merged into the primary figure.

ACRONYM LABELS. `HYVET 2008` names a trial, not an author, so surname matching cannot reach
it. Those are matched against reference titles instead, counted separately, and never
silently folded into the surname rate.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\p70")
# argv[1]/argv[2] let the SAME pipeline run the widened sample, so the replication is the
# same instrument on more data rather than a second instrument that might differ.
LABELS = (sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRATCH, "labels.json"))
CR_CACHE = os.path.join(SCRATCH, "crossref")
ID_CACHE = os.path.join(SCRATCH, "idconv")
XML_CACHE = os.path.join(REPO, "outputs", "pubmed_databank_cache")
OUT = (sys.argv[2] if len(sys.argv) > 2
       else os.path.join(REPO, "outputs", "join_end_to_end_2026_08_25.json"))

CROSSREF = "https://api.crossref.org/works/%s"
# The v1.0 path 301s to this one. Without curl -L the old URL returned an HTML
# redirect page; the payload guard refused it (expect="records") so nothing was
# cached or fabricated -- but 0 of 620 PMIDs is what sent me to look, again.
IDCONV = ("https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
          "?ids=%s&format=json&tool=rapidmeta&email=mahmood726@gmail.com")
EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
          "?db=pubmed&retmode=xml&id=%s")

NCT_RE = re.compile(r"NCT\d{8}")
DATABANK = re.compile(
    r"<DataBankName>\s*ClinicalTrials\.gov\s*</DataBankName>(.*?)</DataBank>", re.S | re.I)
LABEL_RE = re.compile(r"^(.+?)\s+(\d{4})[a-z]?$")


def get(url, cache_dir, key, expect):
    """Cached fetch. Returns text, or None -- an empty payload is never passed off as data."""
    os.makedirs(cache_dir, exist_ok=True)
    fp = os.path.join(cache_dir, re.sub(r"[^A-Za-z0-9]+", "_", key)[:110] + ".txt")
    if os.path.exists(fp) and os.path.getsize(fp) > 40:
        return io.open(fp, encoding="utf-8", errors="replace").read()
    for attempt in (1, 2, 3):
        r = subprocess.run(["curl", "-sSL", "-g", "--max-time", "90", url],
                           capture_output=True)
        body = (r.stdout or b"").decode("utf-8", "replace")
        if expect in body and len(body) > 40:
            io.open(fp, "w", encoding="utf-8").write(body)
            return body
        time.sleep(2 * attempt)
    return None


def references(doi):
    """The review's own reference list. None when Crossref has no record; [] when it has none."""
    body = get(CROSSREF % doi, CR_CACHE, doi, '"message"')
    if body is None:
        return None
    try:
        m = json.loads(body)["message"]
    except Exception:
        return None
    out = []
    for r in (m.get("reference") or []):
        au = (r.get("author") or "").strip().lower()
        yr = (r.get("year") or "").strip()
        title = ((r.get("article-title") or "") + " " + (r.get("unstructured") or "")).lower()
        out.append({"author": au, "year": yr, "doi": r.get("DOI"), "title": title})
    return out


def split_label(s):
    """('carter', '1970') from 'Carter 1970'. None when the label is not of that form."""
    m = LABEL_RE.match((s or "").strip())
    if not m:
        return None
    return m.group(1).strip().lower(), m.group(2)


def match(refs, token, year, slack=0, by_title=False):
    """References matching this label. Returns the list, so the caller can see ambiguity."""
    hits = []
    for r in refs:
        if not r["year"]:
            continue
        try:
            dy = abs(int(r["year"]) - int(year))
        except ValueError:
            continue
        if dy > slack:
            continue
        if by_title:
            if token and re.search(r"\b" + re.escape(token) + r"\b", r["title"]):
                hits.append(r)
        elif r["author"] and r["author"] == token:
            hits.append(r)
    return hits


def doi_to_pmid(dois):
    """Batch DOI -> PMID. Returns a dict; a DOI absent from the result has no PMID, which is
    a real answer and is recorded as such rather than retried into a fabricated one."""
    out = {}
    batch = [d for d in dois if d]
    for i in range(0, len(batch), 50):
        chunk = batch[i:i + 50]
        body = get(IDCONV % ",".join(chunk), ID_CACHE, "b%04d_%s" % (i, chunk[0]), "records")
        if body is None:
            continue
        try:
            for rec in (json.loads(body).get("records") or []):
                if rec.get("doi") and rec.get("pmid"):
                    out[rec["doi"].lower()] = str(rec["pmid"])
        except Exception:
            pass
        time.sleep(0.34)
    return out


ESEARCH_DOI = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
               "?db=pubmed&retmode=json&term=%s%%5BAID%%5D")


def doi_to_pmid_pubmed(doi):
    """DOI -> PMID across ALL of PubMed, not just PMC.

    The NCBI id converter answers only for records IN PMC. On the first run it resolved 218
    of 620 and returned "Identifier not found in PMC" for the rest -- including a 1970 Lancet
    paper that is perfectly well indexed in PubMed. Reporting that 218 as the route's yield
    would have measured PMC deposit coverage and called it a join rate.

    Returns a PMID only when the DOI identifies EXACTLY ONE record. More than one is not an
    identification.
    """
    import urllib.parse
    q = urllib.parse.quote(doi, safe="")
    body = get(ESEARCH_DOI % q, ID_CACHE, "aid_" + doi, "esearchresult")
    if body is None:
        return None
    try:
        res = json.loads(body).get("esearchresult") or {}
        ids = res.get("idlist") or []
        return ids[0] if len(ids) == 1 else None
    except Exception:
        return None


def pmid_to_nct(pmid):
    pmid = str(pmid)   # the id converter returns it as an int
    body = get(EFETCH % pmid, XML_CACHE, pmid, "<PubmedArticle")
    if body is None:
        return None
    found = []
    for blk in DATABANK.findall(body):
        found.extend(NCT_RE.findall(blk))
    return found


def run_controls():
    from instrument_controls import require_controls
    refs = [{"author": "carter", "year": "1970", "doi": "10.1/a", "title": "hyvet trial"},
            {"author": "coope", "year": "1986", "doi": "10.1/b", "title": "other"},
            {"author": "carter", "year": "1970", "doi": "10.1/c", "title": "dup"}]
    one = match(refs, "coope", "1986")
    two = match(refs, "carter", "1970")
    none = match(refs, "nobody", "1999")
    require_controls(
        "join_end_to_end (matcher)",
        ("a label with exactly one matching reference resolves to 1", len(one), 1),
        ("a label with NO matching reference is FLAGGED as resolved", len(none) == 1, True))
    require_controls(
        "join_end_to_end (ambiguity)",
        ("a label matching two references returns both, so it is not counted resolved",
         len(two), 2),
        ("two matches would be counted as resolved", len(two) == 1, True))


ORIGINAL_40 = set()
_o = os.path.join(SCRATCH, "sample.txt")
if os.path.exists(_o):
    ORIGINAL_40 = {x.strip() for x in io.open(_o, encoding="utf-8") if x.strip()}


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    reviews = json.load(io.open(LABELS, encoding="utf-8"))
    reviews = [r for r in reviews if r.get("review_doi")]
    log("reviews: %d   labels: %d"
        % (len(reviews), sum(len(r.get("studies") or []) for r in reviews)))
    log("")

    # bibliographies first, so the null can be built from the same objects
    bibs, bib_missing = {}, []
    for i, r in enumerate(reviews, 1):
        refs = references(r["review_doi"])
        if refs is None:
            bib_missing.append(r["file"])
            log("[%2d/%d] %-28s BIBLIOGRAPHY MISSING" % (i, len(reviews), r["file"][:28]))
            continue
        bibs[r["file"]] = refs
        log("[%2d/%d] %-28s refs=%d" % (i, len(reviews), r["file"][:28], len(refs)))
        time.sleep(0.2)

    usable = [r for r in reviews if r["file"] in bibs]
    order = [r["file"] for r in usable]
    # NULL: review i scored against review i+1's bibliography. Fixed, no randomness.
    null_of = {f: order[(k + 1) % len(order)] for k, f in enumerate(order)}

    rows = []
    for r in usable:
        refs = bibs[r["file"]]
        nrefs = bibs[null_of[r["file"]]]
        for st in (r.get("studies") or []):
            lab = st.get("study") or ""
            parts = split_label(lab)
            rec = {"review": r["file"], "label": lab,
                   "held_out": r["file"] not in ORIGINAL_40}
            if parts is None:
                rec["stage"] = "label not of the form <name> <year>"
                rows.append(rec)
                continue
            token, year = parts
            rec["token"], rec["year"] = token, year
            hits = match(refs, token, year)
            kind = "surname"
            if not hits:
                hits = match(refs, token, year, by_title=True)
                kind = "title" if hits else "surname"
            rec["kind"] = kind
            rec["n_hits"] = len(hits)
            rec["hits_slack1"] = len(match(refs, token, year, slack=1))
            nh = match(nrefs, token, year) or match(nrefs, token, year, by_title=True)
            rec["null_hits"] = len(nh)
            if len(hits) == 1:
                rec["stage"] = "resolved_in_bibliography"
                rec["ref_doi"] = hits[0]["doi"]
            elif len(hits) > 1:
                rec["stage"] = "ambiguous_in_bibliography"
            else:
                rec["stage"] = "absent_from_bibliography"
            rows.append(rec)

    resolved = [r for r in rows if r.get("stage") == "resolved_in_bibliography"]
    with_doi = [r for r in resolved if r.get("ref_doi")]
    log("")
    log("resolving %d reference DOIs to PMIDs" % len(with_doi))
    pm = doi_to_pmid([r["ref_doi"] for r in with_doi])
    got_pmid = 0
    for r in with_doi:
        p = pm.get((r["ref_doi"] or "").lower())
        if p:
            r["pmid"], r["pmid_via"] = p, "pmc_idconv"
            got_pmid += 1
    rest = [r for r in with_doi if not r.get("pmid")]
    log("  %d resolved via the PMC converter; %d fall back to PubMed-wide esearch"
        % (got_pmid, len(rest)))
    for i, r in enumerate(rest, 1):
        p = doi_to_pmid_pubmed(r["ref_doi"])
        if p:
            r["pmid"], r["pmid_via"] = p, "pubmed_aid"
            got_pmid += 1
        if i % 50 == 0:
            log("     esearch %d/%d" % (i, len(rest)))
        time.sleep(0.34)

    withp = [r for r in with_doi if r.get("pmid")]
    log("fetching %d PubMed records for the DataBank field" % len(withp))
    for i, r in enumerate(withp, 1):
        ncts = pmid_to_nct(r["pmid"])
        if ncts is None:
            r["nct_stage"] = "MISSING"
        elif ncts:
            r["nct"] = ncts[0]
            r["nct_stage"] = "ok"
        else:
            r["nct_stage"] = "no databank field"
        if i % 25 == 0:
            log("   %d/%d" % (i, len(withp)))
        time.sleep(0.34)

    n = len(rows)
    withnct = [r for r in rows if r.get("nct")]
    nullres = [r for r in rows if r.get("null_hits") == 1]
    log("")
    log("LABELS ATTEMPTED                    : %d   (one denominator, all figures below)" % n)
    log("  not of the form <name> <year>     : %d" % sum(
        1 for r in rows if r.get("stage", "").startswith("label not")))
    log("  absent from its own bibliography  : %d" % sum(
        1 for r in rows if r.get("stage") == "absent_from_bibliography"))
    log("  ambiguous (2+ refs)               : %d" % sum(
        1 for r in rows if r.get("stage") == "ambiguous_in_bibliography"))
    log("  RESOLVED to one reference         : %d" % len(resolved))
    log("    of which the ref carries a DOI  : %d" % len(with_doi))
    log("    of which a PMID was found       : %d" % got_pmid)
    log("    of which a DataBank NCT exists  : %d" % len(withnct))
    log("")
    log("END TO END, label -> NCT            : %d / %d  (%.1f%%)"
        % (len(withnct), n, 100.0 * len(withnct) / n if n else 0))
    log("NULL, resolved in ANOTHER review's bibliography : %d / %d  (%.1f%%)"
        % (len(nullres), n, 100.0 * len(nullres) / n if n else 0))
    log("")
    log("bibliographies not obtained         : %d review(s) %s"
        % (len(bib_missing), ",".join(bib_missing[:4])))
    log("year-slack +/-1 is recorded per row and is NOT in the figure above.")

    json.dump({"sample_rule": "every 15th of the 595 .rda files in Pairwise70/data, "
                              "alphabetical; fixed before the run",
               "denominator": "labels attempted; no stage rates are multiplied",
               "n_labels": n, "n_reviews": len(usable),
               "bibliographies_missing": bib_missing,
               "resolved": len(resolved), "with_doi": len(with_doi), "with_pmid": got_pmid,
               "end_to_end_nct": len(withnct), "null_resolved": len(nullres),
               "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
