# -*- coding: utf-8 -*-
"""Fetch FDA review documents for a drug application, by READING the index, not guessing.

WHY THIS EXISTS, and it is the same lesson three times over.

A regulatory review is the only free source this project has found that answers RoB 2's
D2 -- the analysis population -- for the large trials whose primary reports are paywalled.
Getting at one means resolving a drug to an application to a set of documents, and every
shortcut in that chain has already failed here:

  1 GUESSING THE FILENAME. "{base}Orig1s000StatR.pdf" is correct for a 2015 approval and
    404s for every 2020+ one, because FDA replaced separate Medical and Statistical
    Reviews with a single INTEGRATED REVIEW. The suffix is `IntegratedR.pdf`, and a
    plausible guess of `IntegratedReview.pdf` also 404s. ⚠️ THE INDEX PAGE DECLARES WHICH
    DOCUMENTS EXIST -- `pdfFiles = {statR: 0, medR: 0, integratedR: 1}` -- and builds each
    filename from `pdfBaseName`. Read that, and the guessing stops.

  2 MATCHING THE DRUG BY NAME. `openfda.generic_name:"apixaban"` returns `ANDA209810`, a
    GENERIC application carrying zero reviews, because generics are approved on
    bioequivalence and never get one. The innovator NDA is a different record. A name
    match is a filter, not an identity.

  3 TRUSTING THE RESPONSE. FDA serves a 17,737-byte HTML error page for a missing PDF,
    with HTTP 200 after redirects in some paths. Saved under a `.pdf` name and passed to
    a text extractor it yields a page of navigation furniture, which a keyword scan will
    happily report on. ⚠️ EVERY DOWNLOAD IS SIZE-CHECKED AND MAGIC-CHECKED, and anything
    that is not a real PDF is refused by name rather than kept.

⚠️ AND THE BOUNDARY OF THE WHOLE SOURCE CLASS, worth stating wherever it is used: a drug
that was never approved has no FDA review. `bococizumab` was discontinued in development,
so its absence here is a FACT ABOUT THE DRUG and not a retrieval failure. Those two must
never be summed into one "not available" count.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

UA = "rapidmeta-systematic-review/1.0 (mailto:mahmood726@gmail.com)"
API = "https://api.fda.gov/drug/drugsfda.json"

# The review documents worth reading for risk of bias, in the order they answer most.
# Keys are the index page's own flag names; values are the suffixes it builds.
REVIEW_SUFFIX = {
    "integratedR": "IntegratedR",
    "multidisciplineR": "MultidisciplineR",
    "statR": "StatR",
    "medR": "MedR",
    "sumR": "SumR",
    "clinPharmR": "ClinPharmR",
    "crossR": "CrossR",
    "otherR": "OtherR",
}
# What each answers, so a caller can ask for the cheapest document that could settle it.
ANSWERS = {
    "integratedR": ("D1", "D2", "D3"),
    "multidisciplineR": ("D1", "D2", "D3"),
    "statR": ("D2", "D3"),
    "medR": ("D1", "D3"),
    "sumR": ("D2",),
}

PDF_MAGIC = b"%PDF-"
MIN_PDF_BYTES = 40000          # the FDA 404 page is ~17.7 kB; a real review is far larger


def _curl(url, out=None, timeout=300):
    args = ["curl", "-sL", "--max-time", str(timeout), "-A", UA,
            "-w", "%{http_code}"]
    if out:
        args += ["-o", out]
    args.append(url)
    r = subprocess.run(args, capture_output=True)
    tail = r.stdout.decode("utf-8", "replace")
    code = tail[-3:] if len(tail) >= 3 else "000"
    return (tail[:-3] if not out else ""), code


def application_for(drug, prefer_nda=True):
    """Resolve a drug name to an application. Returns (application_number, status).

    ⚠️ PREFERS AN NDA/BLA OVER AN ANDA. A generic application has no review, so resolving
    to one and reporting "no review" would be a statement about our lookup dressed as a
    statement about the drug.
    """
    body, code = _curl("%s?search=openfda.generic_name:%%22%s%%22&limit=20"
                       % (API, drug.replace(" ", "+")))
    if code != "200":
        return None, "API_HTTP_%s" % code
    try:
        res = json.loads(body).get("results") or []
    except ValueError:
        return None, "API_UNPARSEABLE"
    if not res:
        return None, "NO_APPLICATION_FOUND"
    ranked = sorted(res, key=lambda a: 0 if str(a.get("application_number", ""))
                    .upper().startswith(("NDA", "BLA")) else 1)
    if prefer_nda and not str(ranked[0].get("application_number", "")).upper().startswith(
            ("NDA", "BLA")):
        return ranked[0].get("application_number"), "ONLY_GENERIC_APPLICATION_FOUND"
    return ranked[0].get("application_number"), "OK"


def review_index(app_number):
    """Find the approval-package index page for an application, from the API's own list."""
    body, code = _curl("%s?search=application_number:%%22%s%%22&limit=1"
                       % (API, app_number))
    if code != "200":
        return None, "API_HTTP_%s" % code
    try:
        res = json.loads(body).get("results") or []
    except ValueError:
        return None, "API_UNPARSEABLE"
    if not res:
        return None, "NO_APPLICATION"
    urls = []
    for s in res[0].get("submissions") or []:
        for doc in (s.get("application_docs") or []):
            if str(doc.get("type", "")).lower() == "review":
                urls.append(doc.get("url"))
    if not urls:
        return None, "NO_REVIEW_DOCUMENT_LISTED"
    toc = next((u for u in urls if u and u.lower().endswith((".html", ".htm"))), None)
    return (toc or urls[0]), "OK"


def documents_declared(toc_url):
    """Read the index page's OWN declaration of which documents exist.

    Returns (base_url_dir, pdf_base_name, {flag: True/False}). This is the step that
    replaces guessing: the page carries `pdfBaseName` and a `pdfFiles` map, and builds
    each link as pdfBaseName + Suffix + '.pdf'.
    """
    body, code = _curl(toc_url)
    if code != "200":
        return None, None, {}, "TOC_HTTP_%s" % code
    m = re.search(r'var\s+pdfBaseName\s*=\s*"([^"]+)"', body)
    if not m:
        return None, None, {}, "NO_PDF_BASE_NAME"
    base = m.group(1)
    flags = {}
    blk = re.search(r'var\s+pdfFiles\s*=\s*\{(.*?)\}', body, re.S)
    if blk:
        for k, v in re.findall(r'(\w+)\s*:\s*([01])', blk.group(1)):
            flags[k] = (v == "1")
    return toc_url.rsplit("/", 1)[0], base, flags, "OK"


def fetch_reviews(drug, outdir, want=("integratedR", "multidisciplineR", "statR", "medR")):
    """The whole chain, with every step's failure named separately."""
    rec = {"drug": drug, "documents": [], "status": None}
    app, st = application_for(drug)
    rec["application_number"], rec["application_status"] = app, st
    if not app:
        rec["status"] = st
        return rec
    toc, st = review_index(app)
    rec["index_url"], rec["index_status"] = toc, st
    if not toc:
        rec["status"] = st
        return rec
    d, base, flags, st = documents_declared(toc)
    rec["pdf_base_name"], rec["declared"] = base, {k: v for k, v in flags.items() if v}
    if st != "OK":
        rec["status"] = st
        return rec
    os.makedirs(outdir, exist_ok=True)
    got = 0
    for flag in want:
        if not flags.get(flag):
            continue
        url = "%s/%s%s.pdf" % (d, base, REVIEW_SUFFIX[flag])
        path = os.path.join(outdir, "%s_%s.pdf" % (drug.replace(" ", "_"), flag))
        _, code = _curl(url, out=path)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        head = open(path, "rb").read(5) if size else b""
        # ⚠️ REFUSE AN ERROR PAGE WEARING A .pdf NAME.
        ok = (code == "200" and size >= MIN_PDF_BYTES and head == PDF_MAGIC)
        if not ok and os.path.exists(path):
            os.remove(path)
        rec["documents"].append({"flag": flag, "url": url, "http": code,
                                 "bytes": size, "is_pdf": head == PDF_MAGIC,
                                 "kept": ok,
                                 "answers": list(ANSWERS.get(flag, ()))})
        got += 1 if ok else 0
        time.sleep(1)
    rec["status"] = "OK" if got else ("DECLARED_BUT_NONE_FETCHABLE" if rec["declared"]
                                      else "NO_REVIEW_DOCUMENTS_DECLARED")
    rec["n_kept"] = got
    return rec


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    drugs = sys.argv[1:] or ["finerenone"]
    outdir = os.environ.get("FDA_OUTDIR", "F:/claude-temp/fda")
    allrecs = []
    for d in drugs:
        r = fetch_reviews(d, outdir)
        allrecs.append(r)
        print("%-16s app=%-12s %-28s kept=%s"
              % (d, r.get("application_number"), r["status"], r.get("n_kept", 0)))
        for doc in r["documents"]:
            print("      %-18s http=%s %8d bytes  pdf=%s kept=%s  answers=%s"
                  % (doc["flag"], doc["http"], doc["bytes"], doc["is_pdf"],
                     doc["kept"], ",".join(doc["answers"])))
    with open(os.path.join(outdir, "fetch_log.json"), "w", encoding="utf-8") as fh:
        json.dump(allrecs, fh, indent=1)
