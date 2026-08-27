"""Execute one search against one source and record WHICH OF THREE THINGS HAPPENED.

    EXECUTED  the server answered and returned >= 1 record
    EMPTY     the server answered, HTTP 200, and returned exactly 0 records
    FAILED    the server did not answer, or answered with a non-200, or answered
              200 with a payload that is not the shape a count can be read from

WHY THIS IS THREE STATES AND NOT TWO. A search that returned nothing and a search that
was refused look IDENTICAL downstream: both leave you with no records. But one is
evidence about the literature and the other is evidence about the harness, and only the
HTTP status separates them.

THIS IS NOT HYPOTHETICAL. Probing OpenAlex tonight returned:

    HTTP 429  {"error":"Rate limit exceeded",
               "message":"Insufficient budget. This request costs $0.001 but you only
                          have $0 remaining. Resets at midnight UTC",
               "retryAfter":5297}

That body has NO `results` key. A client doing `len(payload.get("results", []))` records
ZERO RECORDS FOUND -- a false negative, which then gets written into a search record,
committed, and anchored in a public transparency log. An anchored false negative is worse
than no record at all, because it is timestamped and looks deliberate.

SAME LAW AS ssot/ctgov_transport.py, WHICH ALREADY STATES IT for the role payload:
    OK / UNREACHABLE / MALFORMED, and "an instrument that could not read must not report
    a negative reading."
This module is that law applied to the SEARCH rather than to the record fetch. The
vocabulary is deliberately parallel and not a second invention.

CLAUDE-SIDE BY NECESSITY. Codex has no network in its sandbox: probed tonight with a
PowerShell-correct command, `curl.exe` returned status=000, no HTTP response at all. An
earlier probe reported NETWORK: NO from a broken command -- `curl` is an alias for
Invoke-WebRequest there and rejects curl flags -- so the first answer was a shell error
wearing a network answer's clothes. The conclusion held; the first evidence for it did not.
"""
import datetime
import json
import urllib.error
import urllib.parse
import urllib.request

EXECUTED = "EXECUTED"
EMPTY = "EMPTY"
FAILED = "FAILED"

UA = "rapidmeta-registration (mailto:mahmood726@gmail.com)"

PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
CTGOV = "https://clinicaltrials.gov/api/v2/studies"
OPENALEX = "https://api.openalex.org/works"
EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ISRCTN = "https://www.isrctn.com/api/query/format/default"

# THE FIVE SOURCES, AND WHAT EACH IS FOR. Verified live before being wired in, not
# taken from a brief:
#   pubmed     NCBI E-utilities. Free, no key.
#   europepmc  ~40M records: all of MEDLINE, plus PMC full text, plus bioRxiv and
#              medRxiv preprints. Free, no key. It RESOLVES FULL TEXT natively, which
#              matters more here than another index would: this corpus has already
#              produced false "abstract only" claims, and a source that can fetch the
#              full text is the one that settles them.
#   ctgov      ClinicalTrials.gov API v2. Free, no key.
#   isrctn     Free XML API, no key. Used as the PROGRAMMATIC STOPGAP for ICTRP:
#              the WHO ICTRP bulk-crawling service is currently unavailable, so the
#              WHO platform itself is portal search plus a data-access request. Which
#              route a search actually used is recorded per query, because "searched
#              ICTRP" via a portal by hand and via an API are different acts.
#   openalex   OPPORTUNISTIC FIFTH. Not paywalled -- an API key plus a modest daily
#              free allowance since February 2026. A "$0 remaining" 429 means today's
#              allowance is spent and it resets at midnight UTC. Money buys throughput,
#              not entry. Use it within the allowance and NEVER BLOCK ON IT: a topic
#              whose OpenAlex limb returns 429 is recorded FAILED for that source and
#              the other four still stand.
#
# NOT SEARCHED, AND SAID PLAINLY IN EVERY PROTOCOL: Embase and CENTRAL. Neither is
# free. Claiming Cochrane-standard coverage without them is precisely the class of
# unbacked method claim this project spent a night removing.
SOURCES = ("pubmed", "europepmc", "ctgov", "isrctn", "openalex")


def _now():
    t = datetime.datetime.now(datetime.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (t.microsecond // 1000)


def _fetch(url, timeout=60):
    """Return (http_status, body_bytes, transport_error). Never raises."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), None
    except urllib.error.HTTPError as e:
        # A NON-200 WITH A BODY. This is the case that must never read as EMPTY:
        # the body often parses as JSON and simply has no results key.
        return e.code, e.read(), None
    except Exception as e:
        return None, b"", type(e).__name__ + ": " + str(e)[:200]


def _count(source, payload):
    """Read the count from the shape this source uses. Return None if unreadable.

    None means MALFORMED, which is a FAILURE. It must never be coerced to 0 -- that
    coercion is exactly how a refused search becomes an anchored false negative.
    """
    try:
        if source == "pubmed":
            r = payload["esearchresult"]
            return int(r["count"]), r.get("idlist") or []
        if source == "ctgov":
            ids = [s["protocolSection"]["identificationModule"]["nctId"]
                   for s in (payload.get("studies") or [])]
            total = payload["totalCount"] if "totalCount" in payload else len(ids)
            return int(total), ids
        if source == "openalex":
            return int(payload["meta"]["count"]), [
                w.get("doi") for w in (payload.get("results") or [])]
        if source == "europepmc":
            ids = [r.get("id") for r in
                   ((payload.get("resultList") or {}).get("result") or [])]
            return int(payload["hitCount"]), ids
    except Exception:
        return None
    return None


def _count_xml(source, body):
    """ISRCTN answers in XML, so its count is read from an attribute, not a key.

    Kept separate from _count so that an XML source can never fall through the JSON
    path and be scored MALFORMED for the wrong reason -- the failure would look
    identical and would be recorded against the registry rather than against us.
    """
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(body.decode("utf-8", "replace"))
        total = root.attrib.get("totalCount")
        if total is None:
            return None
        ids = []
        for el in root.iter():
            v = el.attrib.get("publicIdentifierCanonical")
            if v:
                ids.append(v)
        return int(total), ids
    except Exception:
        return None


def run(source, params, timeout=60):
    """Execute one query. Returns a record that always states which of three happened."""
    base = {"pubmed": PUBMED, "ctgov": CTGOV, "openalex": OPENALEX,
            "europepmc": EUROPEPMC, "isrctn": ISRCTN}[source]
    url = base + "?" + urllib.parse.urlencode(params, doseq=True)
    rec = {"source": source, "url": url, "params": dict(params),
           "attempted_utc": _now()}
    if source == "isrctn":
        # Recorded on the query itself, because "we searched ICTRP" is not one act.
        # The WHO platform's bulk crawl is unavailable, so ICTRP coverage here comes
        # via ISRCTN's own API, and a reader must be able to see which route ran.
        rec["ictrp_route"] = ("ISRCTN free XML API, used as the programmatic stopgap for "
                              "ICTRP. The WHO ICTRP bulk-crawling service is unavailable; "
                              "the WHO portal itself was NOT searched by this query.")

    status, body, transport_error = _fetch(url, timeout)
    rec["completed_utc"] = _now()
    rec["http_status"] = status
    rec["response_bytes"] = len(body)

    if transport_error is not None:
        rec.update(outcome=FAILED, n_records=None, ids=[],
                   failure="TRANSPORT: " + transport_error)
        return rec
    if status != 200:
        snippet = body.decode("utf-8", "replace")[:300]
        rec.update(outcome=FAILED, n_records=None, ids=[],
                   failure="HTTP " + str(status) + ": " + snippet,
                   WHY_NOT_EMPTY=("The server answered with a non-200. Its body may parse "
                                  "as JSON and may have no results key, which is how a "
                                  "refusal becomes a false zero. It is a FAILURE."))
        return rec
    if source == "isrctn":
        counted = _count_xml(source, body)
    else:
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception as e:
            rec.update(outcome=FAILED, n_records=None, ids=[],
                       failure="UNPARSEABLE 200: " + type(e).__name__)
            return rec
        counted = _count(source, payload)
    if counted is None:
        rec.update(outcome=FAILED, n_records=None, ids=[],
                   failure="MALFORMED 200: the count field this source uses was not "
                           "present or not readable. NOT coerced to zero.")
        return rec

    total, ids = counted
    rec.update(n_records=total, ids=ids[:200],
               outcome=EMPTY if total == 0 else EXECUTED)
    if total == 0:
        rec["WHY_EMPTY_IS_A_RESULT"] = ("HTTP 200 and a readable count of zero. The server "
                                        "answered and the literature is what is empty. This "
                                        "is a finding; a FAILED is not.")
    return rec


def tally(records):
    """Three counts, never two."""
    return {EXECUTED: sum(1 for r in records if r["outcome"] == EXECUTED),
            EMPTY: sum(1 for r in records if r["outcome"] == EMPTY),
            FAILED: sum(1 for r in records if r["outcome"] == FAILED)}


# ------------------------------------------------------------------------------------
# SELF-TEST. Proves the module can report all three, using a REAL refusal rather than a
# simulated one where possible. A harness that has only ever reported success is one
# nobody has tested.
# ------------------------------------------------------------------------------------
def self_test():
    import io as _io, sys as _sys
    _sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("SELF-TEST -- can this harness report all three outcomes?\n")
    checks = []

    r = run("ctgov", {"query.cond": "pericarditis", "pageSize": 1, "countTotal": "true"})
    print("  ctgov live            -> " + r["outcome"] + "  http=" + str(r["http_status"])
          + "  n=" + str(r["n_records"]))
    checks.append(("can report EXECUTED", r["outcome"] == EXECUTED))

    r = run("ctgov", {"query.cond": "zzzznosuchconditionexists12345", "pageSize": 1,
                      "countTotal": "true"})
    print("  ctgov nonsense query  -> " + r["outcome"] + "  http=" + str(r["http_status"])
          + "  n=" + str(r["n_records"]))
    checks.append(("can report EMPTY on a real 200/0", r["outcome"] == EMPTY))

    r = run("europepmc", {"query": "finerenone AND chronic kidney disease",
                          "format": "json", "pageSize": 2})
    print("  europepmc live        -> " + r["outcome"] + "  http=" + str(r["http_status"])
          + "  n=" + str(r["n_records"]))
    checks.append(("europepmc reads its count", r["outcome"] == EXECUTED))

    r = run("isrctn", {"q": "colchicine"})
    print("  isrctn live (XML)     -> " + r["outcome"] + "  http=" + str(r["http_status"])
          + "  n=" + str(r["n_records"]))
    checks.append(("an XML source reads its count", r["outcome"] == EXECUTED))
    checks.append(("the ICTRP route is recorded", "ictrp_route" in r))

    r = run("openalex", {"search": "finerenone", "per-page": 2})
    print("  openalex              -> " + r["outcome"] + "  http=" + str(r["http_status"])
          + "  n=" + str(r["n_records"]))
    # OpenAlex is the opportunistic fifth: EXECUTED inside the daily allowance, FAILED
    # with a 429 once it is spent. BOTH are correct behaviour and neither blocks a topic,
    # so this asserts only that whichever happened was classified honestly -- never that
    # it succeeded. An assertion that OpenAlex must succeed would make a free allowance
    # into a hard dependency.
    checks.append(("openalex is EXECUTED or FAILED, never silently EMPTY",
                   r["outcome"] in (EXECUTED, FAILED)))
    checks.append(("a FAILED never carries n_records=0",
                   r["outcome"] != FAILED or r["n_records"] is None))

    r = run("ctgov", {"query.cond": "x"}, timeout=0.001)
    print("  ctgov forced timeout  -> " + r["outcome"] + "  " + str(r.get("failure"))[:60])
    checks.append(("a transport error is FAILED", r["outcome"] == FAILED))

    print()
    ok = True
    for label, passed in checks:
        print("    " + ("ok  " if passed else "FAIL") + " " + label)
        ok = ok and passed
    return ok


if __name__ == "__main__":
    import sys as _s
    raise SystemExit(0 if self_test() else 1)
