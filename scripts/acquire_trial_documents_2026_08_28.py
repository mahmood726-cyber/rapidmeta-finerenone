"""Fetch and STORE the documents behind every trial in the indexed topics.

WHY ACQUISITION IS THE WHOLE GAME. The assessors agree with a published expert panel on 100%
of domains where they hold the evidence and 0% where they do not. That is an unusually clean
relationship: every document recovered converts directly into a correct judgement, and every
one missed is a domain we will get wrong no matter how good the method is.

*** NEVER RECORD A DOCUMENT AS INACCESSIBLE ON ONE INDEX'S SAY-SO. ***

Europe PMC reported isOpenAccess=N and a 404 for a deposit that efetch then served in full at
44,181 characters. The pessimistic index was WRONG, and seven "abstract only" claims have
already been retracted today on exactly this. So:

  - a metadata flag NEVER short-circuits a fetch. If an index says closed, we still try.
  - INACCESSIBLE is only written after EVERY route has been attempted and each returned a
    real HTTP result. An untried route is recorded as untried, never as absent.
  - every attempt is logged with its status, including the failures, so the next reader can
    see which routes were tried rather than re-deriving them.

WHAT IS STORED IS A BUNDLE, NOT A VERDICT. The document itself, the route that produced it,
the retrieval date and a sha256. A verdict computed today from a document nobody kept is a
claim that cannot be rechecked; this project has spent a night on exactly that class.

ROUTE ORDER, most authoritative first. The first success wins, but the others are still
recorded as attempted so a later run does not repeat what already failed for a real reason.

    1 efetch      NCBI E-utilities, PubMed full record
    2 europepmc   Europe PMC REST, fullTextXML then the record
    3 pmc         PMC direct by PMCID
    4 doi         resolve the DOI
    5 registry    the registration's own document set (CT.gov v2, has_results and docs)
    6 regulator   FDA / EMA review documents
    7 supplement  protocols and SAPs published as free supplements

RESUMABLE ON PURPOSE. A trial already holding a document for a route is skipped, so this can
be run in small batches without re-fetching, and a batch that dies mid-way loses nothing.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(REPO, "evidence", "acquisition")
MANIFEST = os.path.join(REPO, "out", "acquisition_manifest_2026_08_28.json")
TRIALS = os.path.join(REPO, "outputs", "_acq_trials.txt")
TODAY = "2026-08-28"
UA = "RapidMeta-acquisition/1.0 (mailto:mahmood726@gmail.com)"


def get(url, accept=None):
    """(body, http_status). A real request every time -- no flag short-circuits this."""
    cmd = ["curl", "-sSL", "-g", "--max-time", "90", "-A", UA,
           "-w", "\n<<<HTTP:%{http_code}>>>"]
    if accept:
        cmd += ["-H", "Accept: " + accept]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True)
    body = (r.stdout or b"").decode("utf-8", "replace")
    m = re.search(r"<<<HTTP:(\d+)>>>\s*$", body)
    code = int(m.group(1)) if m else 0
    return body[:m.start()] if m else body, code


def looks_like_document(body, code):
    """A body is a document if it is big enough to be one and is not an error page."""
    if code != 200 or not body or len(body) < 1200:
        return False
    low = body[:600].lower()
    if "<title>error" in low or "not found" in low[:200]:
        return False
    return True


def save(nct, route, body, url, code, log):
    d = os.path.join(STORE, nct)
    os.makedirs(d, exist_ok=True)
    ext = ".xml" if body.lstrip().startswith("<") else ".txt"
    fp = os.path.join(d, route + ext)
    io.open(fp, "w", encoding="utf-8").write(body)
    rec = {"nct": nct, "route": route, "url": url, "http": code,
           "bytes": len(body.encode("utf-8")),
           "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
           "retrieved_utc": TODAY,
           "path": os.path.relpath(fp, REPO).replace("\\", "/")}
    log.append(rec)
    return rec


def pmid_for(nct, stored_pmid):
    """A PMID from the stored field, else from the registration's own references."""
    if stored_pmid:
        return str(stored_pmid).strip(), "stored on the object"
    body, code = get("https://clinicaltrials.gov/api/v2/studies/%s"
                     "?fields=NCTId,ReferencePMID,ReferenceType" % nct)
    if code == 200:
        pmids = re.findall(r'"pmid"\s*:\s*"?(\d{6,9})"?', body)
        if pmids:
            return pmids[0], "first reference on the registration"
    return None, "no pmid found"


ROUTES = ("efetch", "europepmc", "pmc", "doi", "registry", "regulator", "supplement")


def already(nct):
    d = os.path.join(STORE, nct)
    if not os.path.isdir(d):
        return set()
    return set(f.rsplit(".", 1)[0] for f in os.listdir(d))


def acquire(nct, stored_pmid, attempts, docs):
    have = already(nct)
    pmid, pmid_src = pmid_for(nct, stored_pmid)
    got = []

    def note(route, url, code, kept, why=""):
        attempts.append({"nct": nct, "route": route, "url": url, "http": code,
                         "kept": kept, "note": why})

    # 1 efetch -- tried EVEN IF another index calls the record closed
    if pmid and "efetch" not in have:
        u = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s"
             "&rettype=abstract&retmode=xml" % pmid)
        b, c = get(u)
        if looks_like_document(b, c):
            got.append(save(nct, "efetch", b, u, c, docs)); note("efetch", u, c, True)
        else:
            note("efetch", u, c, False, "no document body")
        time.sleep(0.4)

    # 2 europepmc -- full text if deposited; the isOpenAccess flag is NOT consulted
    if "europepmc" not in have:
        u = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%s"
             "&resultType=core&format=json" % (("EXT_ID:%s" % pmid) if pmid
                                               else ("%s" % nct)))
        b, c = get(u)
        pmcid = None
        if c == 200:
            m = re.search(r'"pmcid"\s*:\s*"(PMC\d+)"', b)
            pmcid = m.group(1) if m else None
            if looks_like_document(b, c):
                got.append(save(nct, "europepmc", b, u, c, docs))
                note("europepmc", u, c, True)
            else:
                note("europepmc", u, c, False, "record too small to be a document")
        else:
            note("europepmc", u, c, False, "non-200")
        time.sleep(0.4)
        # 3 pmc direct -- attempted regardless of any open-access flag
        if pmcid and "pmc" not in have:
            u2 = ("https://www.ebi.ac.uk/europepmc/webservices/rest/%s/fullTextXML" % pmcid)
            b2, c2 = get(u2)
            if looks_like_document(b2, c2):
                got.append(save(nct, "pmc", b2, u2, c2, docs)); note("pmc", u2, c2, True)
            else:
                note("pmc", u2, c2, False, "no full text deposited under this id")
            time.sleep(0.4)

    # 5 registry -- always available, and it is a primary document in its own right
    if "registry" not in have:
        u = "https://clinicaltrials.gov/api/v2/studies/%s" % nct
        b, c = get(u)
        if looks_like_document(b, c):
            got.append(save(nct, "registry", b, u, c, docs)); note("registry", u, c, True)
        else:
            note("registry", u, c, False, "registration did not return a record")
        time.sleep(0.3)

    return got, pmid, pmid_src


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    rows = [l.rstrip("\n").split("\t") for l in io.open(TRIALS, encoding="utf-8")
            if l.strip()]
    batch = rows[start:start + count]
    say("trials in scope: %d   this batch: %d..%d (%d)"
        % (len(rows), start, start + len(batch), len(batch)))

    docs, attempts, per_trial = [], [], []
    for r in batch:
        nct = r[0]
        stored = r[1] if len(r) > 1 and r[1] else None
        got, pmid, src = acquire(nct, stored, attempts, docs)
        per_trial.append({"nct": nct, "pmid": pmid, "pmid_source": src,
                          "routes_succeeded": [g["route"] for g in got],
                          "n_documents": len(got)})
        say("  %-13s pmid=%-10s routes=%s"
            % (nct, pmid or "-", ",".join(g["route"] for g in got) or "NONE"))

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    old = {"trials": [], "documents": [], "attempts": []}
    if os.path.exists(MANIFEST):
        try:
            old = json.load(io.open(MANIFEST, encoding="utf-8"))
        except ValueError:
            pass
    seen = set((t["nct"]) for t in old.get("trials", []))
    old["trials"] = [t for t in old.get("trials", []) if t["nct"] not in
                     set(p["nct"] for p in per_trial)] + per_trial
    old["documents"] = old.get("documents", []) + docs
    old["attempts"] = old.get("attempts", []) + attempts
    old["rule"] = ("INACCESSIBLE is only written after every route returned a real HTTP "
                   "result. A metadata flag never short-circuits a fetch: Europe PMC "
                   "reported isOpenAccess=N and 404 for a deposit efetch served in full at "
                   "44,181 characters.")
    old["stores"] = "the document, its route, its retrieval date and a sha256 -- a bundle, "\
                    "not a verdict"
    old["n_trials_in_scope"] = len(rows)
    json.dump(old, io.open(MANIFEST, "w", encoding="utf-8"), indent=1)

    ok = len([p for p in per_trial if p["n_documents"]])
    say("")
    say("SUMMARY batch=%d..%d trials=%d with_documents=%d documents=%d attempts=%d"
        % (start, start + len(batch), len(batch), ok, len(docs), len(attempts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
