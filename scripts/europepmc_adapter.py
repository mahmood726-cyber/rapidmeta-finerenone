# -*- coding: utf-8 -*-
"""Europe PMC search as a REGISTERED, RE-RUNNABLE adapter.

The point is not the answer once; it is that the meta re-runs. So this emits the same five
things the registry adapter does, and refuses to ship without them:

  1. THE EXECUTED QUERY, VERBATIM -- the exact string sent, not a description of intent.
  2. THE EXECUTION DATE and the endpoint (Europe PMC has no snapshot id; the date is it).
  3. A DENOMINATOR, and the FUNNEL beneath it -- hitCount before any of our filters, then each
     filter's effect recorded separately with its rule id, so a reader sees the funnel and not
     just the survivors. A search that reports only what it kept is a claim, not a search.
  4. EVERY RECORD with its include/exclude decision and the id of the rule that decided it.
  5. FOUR distinguishable states, because three is not enough and the missing one is the one
     that keeps biting us:
        NOT_RUN      -- we never asked (endpoint disabled, precondition failed).
        RAN_ERROR    -- we asked and the answer is unusable (HTTP error, throttle, bad JSON).
        RAN_ZERO     -- we asked, it worked, and nothing matched.
        RAN_RESULTS  -- we asked, it worked, and n matched.
     RAN_ERROR is NOT NOT_RUN and is NOT RAN_ZERO. A throttle read as "posts nothing" has cost
     us at least four times; a throttle read as "we didn't look" is just as wrong.

AND: a filter's zero is untrusted until a KNOWN-POSITIVE has been shown to pass. `control` runs
the query with a record we already hold for the topic and records whether it came back. A zero
with no passing control is reported as UNPROVEN, never as recall.

No API key. Server-side urllib, so the sandbox CORS limit on a browser origin does not apply.
`--selftest` exercises the state machine and the funnel on synthetic responses with no network,
so the harness itself is reproducible.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ENDPOINT = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

NOT_RUN = "NOT_RUN"
RAN_ERROR = "RAN_ERROR"
RAN_ZERO = "RAN_ZERO"
RAN_RESULTS = "RAN_RESULTS"


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch(query, page_size=100, max_pages=5, _transport=None):
    """Execute one Europe PMC search. Returns (state, http_status, hit_count, records, detail).

    state is one of the four constants. `_transport` lets the selftest inject a canned response
    without a network call; in production it is the real urlopen. A transport that raises maps to
    RAN_ERROR (asked, unusable) -- never to RAN_ZERO or NOT_RUN.
    """
    records = []
    hit_count = None
    cursor = "*"
    for page in range(max_pages):
        params = {"query": query, "format": "json", "resultType": "core",
                  "pageSize": str(page_size), "cursorMark": cursor}
        url = ENDPOINT + "?" + urllib.parse.urlencode(params)
        try:
            if _transport is not None:
                status, body = _transport(url, page)
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-harness/1.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    status, body = r.getcode(), r.read().decode("utf-8", "replace")
        except Exception as e:  # connection refused, throttle, timeout -> asked, unusable
            return RAN_ERROR, None, hit_count, records, "transport: %s" % (str(e)[:120])
        if status != 200:
            return RAN_ERROR, status, hit_count, records, "HTTP %s" % status
        try:
            data = json.loads(body)
        except Exception as e:
            return RAN_ERROR, status, hit_count, records, "bad JSON: %s" % (str(e)[:80])
        hit_count = data.get("hitCount", hit_count)
        results = (data.get("resultList") or {}).get("result", []) or []
        for r in results:
            # pubType lives in pubTypeList.pubType (a list) on core records; fall back to a bare
            # string so the synthetic selftest, which uses the simple form, still exercises this.
            pt = "; ".join((r.get("pubTypeList") or {}).get("pubType") or []) or (r.get("pubType") or "")
            records.append({"pmid": r.get("pmid"), "pmcid": r.get("pmcid"), "doi": r.get("doi"),
                            "title": r.get("title"), "year": r.get("pubYear"),
                            "pubType": pt, "source": r.get("source"),
                            "isOpenAccess": r.get("isOpenAccess")})
        nxt = data.get("nextCursorMark")
        if not nxt or nxt == cursor or not results:
            break
        cursor = nxt
    if hit_count is None:
        return RAN_ERROR, 200, None, records, "no hitCount in response"
    state = RAN_RESULTS if (hit_count and records) else RAN_ZERO
    return state, 200, hit_count, records, "hitCount=%s, pulled=%d" % (hit_count, len(records))


# --- screening rules, declared as data so the funnel can quote the rule id verbatim ----------
def _is_rct(rec):
    pt = (rec.get("pubType") or "").lower()
    return "randomized controlled trial" in pt or "randomised controlled trial" in pt


def _year_ge(rec, lo):
    try:
        return int(rec.get("year") or 0) >= lo
    except Exception:
        return False


FILTERS = [
    ("F1_pub_type_rct", "pubType names a randomized controlled trial", _is_rct),
    ("F2_year_ge_2000", "publication year >= 2000", lambda r: _year_ge(r, 2000)),
]


def screen(records):
    """Apply FILTERS in order, recording each step's effect. Returns (kept, funnel, decisions)."""
    funnel = []
    survivors = list(records)
    for rid, desc, fn in FILTERS:
        before = len(survivors)
        survivors = [r for r in survivors if fn(r)]
        funnel.append({"rule_id": rid, "rule": desc, "in": before,
                       "kept": len(survivors), "dropped": before - len(survivors)})
    kept_ids = {(r.get("pmid"), r.get("doi")) for r in survivors}
    decisions = []
    for r in records:
        inc = (r.get("pmid"), r.get("doi")) in kept_ids
        # name the FIRST rule that would exclude it, for a legible per-record reason
        rid = "included"
        if not inc:
            for frid, _d, fn in FILTERS:
                if not fn(r):
                    rid = frid; break
        decisions.append({"pmid": r.get("pmid"), "doi": r.get("doi"), "year": r.get("year"),
                          "title": (r.get("title") or "")[:140],
                          "decision": "include" if inc else "exclude", "rule_id": rid})
    return survivors, funnel, decisions


def run(topic, query, control=None, out_dir=None, _transport=None):
    """Execute, screen, prove the control, and build the record. Writes it if out_dir given."""
    state, http, hit, records, detail = fetch(query, _transport=_transport)
    rec = {
        "source": "europe_pmc",
        "database": "Europe PMC REST search",
        "tool": ENDPOINT,
        "topic": topic,
        "executed_utc": _utc(),
        "state": state,
        "state_detail": detail,
        "http_status": http,
        "query_as_executed": query,
    }
    if state in (RAN_ZERO, RAN_RESULTS):
        survivors, funnel, decisions = screen(records)
        rec["denominator"] = {"hit_count": hit, "records_pulled": len(records),
                              "note": "hit_count is Europe PMC's total BEFORE our filters; "
                                      "records_pulled is what paging retrieved"}
        rec["funnel"] = funnel
        rec["kept"] = len(survivors)
        rec["records"] = decisions
    else:
        # RAN_ERROR or NOT_RUN: no denominator is claimable. Say so; do not write a 0.
        rec["denominator"] = None
        rec["funnel"] = None
        rec["records"] = None
        rec["why_no_denominator"] = ("state is %s: a denominator would be a number we did not "
                                     "obtain. RAN_ERROR is not zero results." % state)
    # control: a zero is untrusted until a known-positive passes the SAME query. Tested by a
    # sub-query (query AND EXT_ID:pmid) so the answer is definitive regardless of how many pages
    # we paged -- a control that only scans the pulled sample can report a false UNPROVEN.
    if control and control.get("pmid"):
        subq = "(%s) AND EXT_ID:%s AND SRC:MED" % (query, control["pmid"])
        cstate, chttp, chit, _cr, cdetail = fetch(subq, page_size=1, max_pages=1, _transport=_transport)
        if cstate in (RAN_ZERO, RAN_RESULTS):
            found = bool(chit and chit >= 1)
            verdict = ("PROVEN_FIRES -- the known-positive passes this exact query" if found else
                       "UNPROVEN -- known-positive does NOT pass this query; its zero/low count "
                       "is not trustworthy as recall, the query is too narrow")
        else:
            found = None
            verdict = "CONTROL_%s -- could not test the known-positive (%s)" % (cstate, cdetail)
        rec["control"] = {"known_positive": control, "control_query": subq,
                          "found_in_results": found, "verdict": verdict}
    if out_dir:
        from pathlib import Path
        p = Path(out_dir); p.mkdir(parents=True, exist_ok=True)
        f = p / ("europepmc_%s_%s.json" % (topic, datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")))
        io.open(f, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, indent=1, ensure_ascii=False))
        rec["_written_to"] = str(f)
    return rec


# --------------------------------------------------------------------------------------------
def _selftest():
    out, ok = [], True

    def check(name, cond):
        nonlocal ok
        ok &= bool(cond); out.append((name, "OK" if cond else "*** FAIL ***"))

    def canned(payload_pages):
        def t(url, page):
            return payload_pages[page] if page < len(payload_pages) else (200, json.dumps(
                {"hitCount": payload_pages[0][1] and json.loads(payload_pages[0][1]).get("hitCount"),
                 "resultList": {"result": []}}))
        return t

    # RAN_RESULTS: two records, one RCT 2020, one non-RCT 1990
    body = json.dumps({"hitCount": 2, "resultList": {"result": [
        {"pmid": "1", "title": "A trial", "pubYear": "2020", "pubType": "Randomized Controlled Trial"},
        {"pmid": "2", "title": "A review", "pubYear": "1990", "pubType": "review"}]}})
    r = run("t", "q", control={"pmid": "1"}, _transport=lambda u, p: (200, body) if p == 0 else (200, json.dumps({"hitCount": 2, "resultList": {"result": []}})))
    check("RAN_RESULTS state", r["state"] == RAN_RESULTS)
    check("denominator = raw hitCount (2), before filters", r["denominator"]["hit_count"] == 2)
    check("funnel records F1 dropping the non-RCT (2->1)", r["funnel"][0]["in"] == 2 and r["funnel"][0]["kept"] == 1)
    check("per-record decision names the excluding rule",
          any(d["decision"] == "exclude" and d["rule_id"] == "F1_pub_type_rct" for d in r["records"]))
    check("control PROVEN when known-positive returns", r["control"]["found_in_results"] and "PROVEN" in r["control"]["verdict"])

    # RAN_ZERO: hitCount 0, empty -> distinct from error, control UNPROVEN
    z = run("t", "q", control={"pmid": "X"}, _transport=lambda u, p: (200, json.dumps({"hitCount": 0, "resultList": {"result": []}})))
    check("RAN_ZERO state (asked, nothing matched)", z["state"] == RAN_ZERO)
    check("RAN_ZERO still carries a denominator of 0", z["denominator"]["hit_count"] == 0)
    check("control UNPROVEN when known-positive absent", not z["control"]["found_in_results"] and "UNPROVEN" in z["control"]["verdict"])

    # RAN_ERROR: transport raises (throttle) -> NOT zero, NOT not-run, no denominator
    def boom(u, p): raise OSError("Connection reset (throttled)")
    e = run("t", "q", _transport=boom)
    check("RAN_ERROR when transport raises (throttle)", e["state"] == RAN_ERROR)
    check("RAN_ERROR claims NO denominator (not a 0)", e["denominator"] is None)
    check("RAN_ERROR is distinct from RAN_ZERO", e["state"] != RAN_ZERO)

    # RAN_ERROR on HTTP 429
    h = run("t", "q", _transport=lambda u, p: (429, "rate limited"))
    check("HTTP 429 -> RAN_ERROR, not zero", h["state"] == RAN_ERROR and h["denominator"] is None)

    return ok, out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--topic")
    ap.add_argument("--query")
    ap.add_argument("--control-pmid")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if a.selftest:
        good, rows = _selftest()
        print("europepmc_adapter selftest")
        for n, v in rows:
            print("  %-58s %s" % (n, v))
        print("\n%s" % ("ALL PASS" if good else "FAILURES ABOVE"))
        return 0 if good else 1
    if not a.query:
        print("need --query (or --selftest)"); return 2
    ctrl = {"pmid": a.control_pmid} if a.control_pmid else None
    rec = run(a.topic or "adhoc", a.query, control=ctrl, out_dir=a.out_dir)
    print(json.dumps(rec, indent=1, ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
