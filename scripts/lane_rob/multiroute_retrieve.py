# -*- coding: utf-8 -*-
"""The multi-route retriever, and the only sanctioned way to record document access.

WHY THIS REPLACES SINGLE-INDEX LOOKUPS. Europe PMC reports the ASPIRE deposit as
`isOpenAccess=N` and its `fullTextXML` endpoint returns 404. NCBI `efetch` served the same
record in full -- 44,181 rendered characters. **Two indexes over one deposit disagreed about
whether it exists and the pessimistic one was wrong.** Corpus-wide, 43 of 317 reachable trials
(14%) are reachable ONLY via `efetch`, so a single-index retrieval understates our reach by an
eighth and reports paywalls that are not there.

⚠️ THREE PROPERTIES, NOT ONE FIELD. `inPMC`, `isOpenAccess` and MACHINE-RETRIEVABLE are
different things. A record may be in PMC, not in the open-access subset, and still served in
full by a different endpoint. Collapsing them into one boolean is what produced the false
"abstract only" claims.

THE CONTRACT. `retrieve()` tries every route in order and returns which one succeeded. It never
returns a bare "inaccessible": it returns the list of routes attempted with each one's status,
so a later reader can tell "we tried four things" from "we asked one API". A document is
recorded as unreachable only when EVERY route has been tried and named.
"""
import io
import json
import os
import re
import subprocess

UA = "rapidmeta-rob-lane/1.0 (+research use; contact via repository)"


def _curl(url, dest, timeout=45):
    try:
        r = subprocess.run(
            ["curl", "-s", "-L", "-A", UA, "--max-time", str(timeout), "-o", dest,
             "-w", "%{http_code}|%{size_download}|%{content_type}"],
            capture_output=True, timeout=timeout + 30, input=None) if False else \
            subprocess.run(
                ["curl", "-s", "-L", "-A", UA, "--max-time", str(timeout), "-o", dest,
                 "-w", "%{http_code}|%{size_download}|%{content_type}", url],
                capture_output=True, timeout=timeout + 30)
        parts = r.stdout.decode("ascii", "replace").split("|")
        code = parts[0].strip() if parts else "ERR"
        size = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 0
        ctype = parts[2].strip() if len(parts) > 2 else ""
        return code, size, ctype
    except Exception as e:
        return "ERR:%s" % type(e).__name__, 0, ""


def _rendered(path):
    """Characters of actual text, not bytes of markup -- a 404 HTML page is large and empty."""
    try:
        raw = io.open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return 0
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip())


# MINIMUM RENDERED TEXT FOR A HIT. An error page from a publisher is typically 1-3k rendered
# characters of navigation; a full text is tens of thousands. 4000 is deliberately generous
# and every borderline result keeps its measured size so the threshold can be re-argued.
MIN_TEXT = 4000

# ⛔ A 200 IS NOT A DOCUMENT, AND A 000 IS NOT A PAYWALL.
#
# Both halves were learned the hard way. NCBI efetch returns 200 for a PMCID that cannot
# exist, so a status-code check records a fabricated document as retrieved -- the rendered-text
# floor is what rejects it. And curl returns 000 when there is NO NETWORK AT ALL: Codex jobs
# have none, and `curl.exe` there yields status=000 for every URL. A 000 written into an
# attempts list is indistinguishable from a genuine refusal, so a script run inside such a job
# would record the whole corpus as unreachable and the number would be wrong in the direction
# we least want -- understating our access, and looking like a paywall finding.
#
# THE SAME SCRIPT RUN IN TWO PLACES IS TWO DIFFERENT INSTRUMENTS. So a network absence gets its
# own status, never counts as a route failure, and every record says where it executed.
NETWORK_ABSENT = ("000", "0", "ERR")


def _absent(code):
    return str(code).startswith("ERR") or str(code) in NETWORK_ABSENT


def _where():
    """Where this fetch executed. A record without it cannot be compared with another."""
    import socket
    return {"host": socket.gethostname(),
            "context": os.environ.get("LANE_CONTEXT") or "unrecorded"}


def routes_for(pmcid=None, pmid=None, doi=None):
    """Ordered routes. Europe PMC first because it is cheapest, publisher last."""
    r = []
    if pmcid:
        p = str(pmcid).replace("PMC", "")
        r.append(("europepmc",
                  "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC%s/fullTextXML" % p))
        r.append(("ncbi_efetch",
                  "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                  "?db=pmc&id=%s&rettype=xml" % p))
        r.append(("pmc_direct", "https://pmc.ncbi.nlm.nih.gov/articles/PMC%s/" % p))
    if pmid:
        r.append(("europepmc_by_pmid",
                  "https://www.ebi.ac.uk/europepmc/webservices/rest/MED/%s/fullTextXML" % pmid))
    if doi:
        r.append(("doi_resolver", "https://doi.org/%s" % doi))
    return r


def retrieve(pmcid=None, pmid=None, doi=None, out_dir=None, save_as=None):
    """Try every route in order. Return a record naming EVERY attempt and its status.

    Never returns a bare inaccessible: `attempts` lists each route with its HTTP code and the
    rendered-character count, so "we tried four things" is distinguishable from "we asked one
    API" by anyone reading the record later.
    """
    out_dir = out_dir or os.environ.get("TEMP", ".")
    tmp = os.path.join(out_dir, "_mr_tmp")
    # THE RECORD MUST NAME THE DOCUMENT AND FINGERPRINT IT. Two lanes retrieved the same 21
    # trials and got DIFFERENT CONTENT for 20 of them, because each resolved the trial to a
    # different paper. Neither manifest could show it alone: one stored the identifier and no
    # hash, the other a hash and no identifier, so "same trial" was mistaken for "same
    # document". A trial is not a document. Both fields travel from here on.
    rec = {"pmcid": pmcid, "pmid": pmid, "doi": doi, "attempts": [],
           "route": None, "rendered_chars": 0, "saved_to": None,
           "document_id": pmcid or (("PMID:" + str(pmid)) if pmid else doi),
           "sha256": None, "executed_at": _where(), "network_absent": False}
    for name, url in routes_for(pmcid, pmid, doi):
        code, size, ctype = _curl(url, tmp)
        chars = _rendered(tmp) if code == "200" and size else 0
        rec["attempts"].append({"route": name, "http": code, "bytes": size,
                                "content_type": ctype[:40], "rendered_chars": chars})
        if code == "200" and chars >= MIN_TEXT:
            rec["route"] = name
            rec["rendered_chars"] = chars
            try:
                import hashlib
                rec["sha256"] = hashlib.sha256(io.open(tmp, "rb").read()).hexdigest()
            except OSError:
                pass
            if save_as:
                try:
                    with io.open(tmp, "rb") as s, io.open(save_as, "wb") as d:
                        d.write(s.read())
                    rec["saved_to"] = save_as
                except OSError:
                    pass
            return rec
    # EVERY ROUTE FAILED -- but WHY decides what this record means. If every attempt returned a
    # network-absence code, nothing was learned about the document and the result is
    # INDETERMINATE, not negative.
    att = rec["attempts"]
    rec["network_absent"] = bool(att) and all(_absent(a["http"]) for a in att)
    return rec


def summarise(rec):
    """One honest sentence about a retrieval, for a store field or a log line."""
    if rec.get("route"):
        return ("retrieved via %s, %d rendered characters, after %d route(s) tried"
                % (rec["route"], rec["rendered_chars"], len(rec["attempts"])))
    tried = ", ".join("%s=%s" % (a["route"], a["http"]) for a in rec["attempts"])
    if rec.get("network_absent"):
        return ("INDETERMINATE -- every route returned a network-absence code (%s). Nothing "
                "was learned about this document; this run had no network. NOT a paywall and "
                "NOT a refusal, and it must not be recorded as either." % tried)
    return ("NOT retrieved. Every route was tried and named: %s. This is a statement about "
            "these routes, not about whether the document exists." % (tried or "none available"))


if __name__ == "__main__":
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    a = dict(x.split("=", 1) for x in sys.argv[1:] if "=" in x)
    r = retrieve(pmcid=a.get("pmcid"), pmid=a.get("pmid"), doi=a.get("doi"))
    print(json.dumps(r, indent=1))
    print(summarise(r))
