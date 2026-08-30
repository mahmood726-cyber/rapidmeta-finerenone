# -*- coding: utf-8 -*-
"""ICTRP (WHO trialsearch.who.int) as a SEARCHED SOURCE, not a named one.

WHY THIS EXISTS. ICTRP was ruled into the search set on 2026-08-28 as source 4, for the
one thing no other source in the set reaches: trials registered OUTSIDE the United
States -- the Chinese, Indian, Iranian, Pan-African and European registries. It was
ruled in and then not run, and a blinded panel noticed the gap. This runs it.

WHAT IT RECORDS, AND WHY EACH FIELD IS THERE.

  term        the exact query string. A search without its query is not reproducible.
  utc         when it ran. Registry contents change; a result set without a date is a
              claim about no particular moment.
  sha256      of the concatenated result HTML. This is the project's standing rule that
              an observation carries a content hash, so a later disagreement can be
              settled against the bytes that produced it rather than by re-running and
              hoping. It is the same discipline that made an earlier contamination audit
              exact rather than anecdotal.
  reported_count  what the SERVER says it found.
  n_ids       what we actually PARSED.

  ⚠️ THE TWO COUNTS ARE REPORTED SEPARATELY AND ARE NEVER RECONCILED SILENTLY. The first
  page of a dapivirine search says 52 records and yields 10 identifiers, because the
  grid paginates. Reporting 10 as the result would be this project's most-repeated
  defect -- a scan reporting its own reach as the population. If pagination stops early
  the status is TRUNCATED and the two numbers disagree in the record, visibly.

THREE STATUSES, NOT TWO. `FAILED` (the host refused or the transport broke), `EMPTY`
(it answered and found nothing), and `OK` are different facts about a search and the
standing orders require them counted separately. An EMPTY result is evidence; a FAILED
one is an absence of evidence, and folding them together turns a broken search into a
finding about the literature.

TRANSPORT IS CURL, DELIBERATELY. urllib is served 403 by this host and curl is not.
Recorded here rather than left for the next reader to rediscover.
"""
import sys, io, re, os, json, html as _h, hashlib, datetime, subprocess
import urllib.parse, tempfile

BASE = "https://trialsearch.who.int/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
MAX_PAGES = 60

# Registry prefixes that are NOT ClinicalTrials.gov. This is what ICTRP buys us, and it
# is reported as a fraction rather than asserted.
NON_CTGOV = re.compile(r'^(?!NCT)', re.I)


def _curl(args):
    r = subprocess.run(["curl", "-s", "--max-time", "90", "-A", UA] + args,
                       capture_output=True)
    return r.stdout.decode("utf-8", "replace"), r.returncode


def _hidden(page):
    out = {}
    for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', page, re.I):
        t = m.group(0)
        n = re.search(r'name="([^"]+)"', t)
        v = re.search(r'value="([^"]*)"', t)
        if n:
            out[n.group(1)] = _h.unescape(v.group(1) if v else "")
    return out


def _post(jar, fields):
    fd, pf = tempfile.mkstemp(suffix=".post")
    os.close(fd)
    with open(pf, "w", encoding="utf-8") as fh:
        fh.write(urllib.parse.urlencode(fields))
    try:
        return _curl(["-b", jar, "-c", jar, "-X", "POST", "--data-binary", "@" + pf,
                      "-H", "Content-Type: application/x-www-form-urlencoded",
                      "-H", "Referer: " + BASE, BASE])
    finally:
        os.unlink(pf)


def _ids(page):
    return {urllib.parse.unquote(x)
            for x in re.findall(r'TrialID=([A-Za-z0-9%/._-]+)', page)}


def search(term, max_pages=MAX_PAGES):
    """Run one ICTRP query to exhaustion. Returns a record, never raises for a miss."""
    jar = tempfile.mktemp(suffix=".ictrp.cookies")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    home, rc = _curl(["-c", jar, BASE])
    if rc != 0 or len(home) < 1000:
        return {"source": "ICTRP", "term": term, "utc": started, "status": "FAILED",
                "reason": "home page rc=%s len=%d" % (rc, len(home))}

    fields = _hidden(home)
    fields["TextBox1"] = term
    fields["Button1"] = "Search"
    page, rc = _post(jar, fields)
    if rc != 0 or len(page) < 500:
        return {"source": "ICTRP", "term": term, "utc": started, "status": "FAILED",
                "reason": "search post rc=%s len=%d" % (rc, len(page))}

    m = re.search(r'(\d[\d,]*)\s*(?:records?|trials?)\s*(?:found|match)', page, re.I)
    reported = int(m.group(1).replace(",", "")) if m else None

    ids = set(_ids(page))
    blobs = [page]
    pages_fetched = 1
    truncated_reason = None

    # ASP.NET grid paging: __doPostBack('GridView1','Page$N'). The grid only ever
    # advertises a window of page numbers, so walk N upward rather than trusting the
    # links, and stop when a page yields nothing new.
    n = 2
    while n <= max_pages:
        f = _hidden(page)
        f["__EVENTTARGET"] = "GridView1"
        f["__EVENTARGUMENT"] = "Page$%d" % n
        f.pop("Button1", None)
        f["TextBox1"] = term
        nxt, rc = _post(jar, f)
        if rc != 0 or len(nxt) < 500:
            truncated_reason = "page %d rc=%s len=%d" % (n, rc, len(nxt))
            break
        new = _ids(nxt) - ids
        if not new:
            page = nxt
            break
        ids |= new
        blobs.append(nxt)
        page = nxt
        pages_fetched += 1
        n += 1
    else:
        truncated_reason = "hit max_pages=%d" % max_pages

    ids = sorted(ids)
    non_ct = [i for i in ids if not i.upper().startswith("NCT")]
    sha = hashlib.sha256("".join(blobs).encode("utf-8", "replace")).hexdigest()

    status = "OK" if ids else "EMPTY"
    complete = (reported is not None and len(ids) >= reported)
    if status == "OK" and not complete:
        status = "TRUNCATED"

    return {"source": "ICTRP",
            "endpoint": BASE,
            "term": term,
            "utc": started,
            "status": status,
            "reported_count": reported,
            "n_ids": len(ids),
            "pages_fetched": pages_fetched,
            "truncated_reason": truncated_reason,
            "sha256": sha,
            "ids": ids,
            "non_ctgov_ids": non_ct,
            "n_non_ctgov": len(non_ct)}


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    term = " ".join(sys.argv[1:]) or "dapivirine"
    rec = search(term)
    print(json.dumps(rec, indent=1, ensure_ascii=False))
