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
    except Exception:
        return None
    return None


def run(source, params, timeout=60):
    """Execute one query. Returns a record that always states which of three happened."""
    base = {"pubmed": PUBMED, "ctgov": CTGOV, "openalex": OPENALEX}[source]
    url = base + "?" + urllib.parse.urlencode(params, doseq=True)
    rec = {"source": source, "url": url, "params": dict(params),
           "attempted_utc": _now()}

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

    r = run("openalex", {"search": "finerenone", "per-page": 2})
    print("  openalex (budget $0)  -> " + r["outcome"] + "  http=" + str(r["http_status"]))
    print("      " + str(r.get("failure", ""))[:150])
    checks.append(("a non-200 is FAILED, not EMPTY", r["outcome"] == FAILED))
    checks.append(("a FAILED never carries n_records=0", r["n_records"] is None))

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
