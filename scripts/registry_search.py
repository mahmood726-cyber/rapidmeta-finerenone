# -*- coding: utf-8 -*-
"""ICTRP, done the only way it can be done freely: query the PRIMARY REGISTRIES directly.

WHY NOT THE ICTRP PORTAL. `trialsearch.who.int/robots.txt` is `User-agent: * / Disallow: /`
-- the whole site -- and its result grid returns `NoAccess.aspx` to a scripted page-2
request, so a result set cannot be enumerated even setting robots aside. We do not scrape
it. ⭐ AN INDEX IS NOT A SOURCE: ICTRP aggregates 18 primary registries, and those are the
sources of record. This queries them.

⭐ AND IT IS FREE, WHICH IS NOW A SCOPE RULE. Mahmood, 2026-08-30: "Embase is not available
in Laos and Uganda." A method that depends on a subscription cannot be reproduced by the
reader it is for, and verifiable-not-authoritative is the axis this project wins on. Every
endpoint below is free to anyone with a browser.

⚠️⚠️ FIVE STATES, AND THE FOURTH IS THE ONE THAT MATTERS.

    OK              records were parsed. A real result.
    EMPTY           the registry SAID it found nothing. Also a real result.
    INDETERMINATE   HTTP 200, no records parsed, AND NO "no results" MESSAGE. The page
                    renders its results in the browser, so what we hold is a shell.
    FAILED          transport or HTTP error. An absence of evidence, not evidence.
    ROBOTS_REFUSED  the host disallows automated access.
    NO_ENDPOINT     we have not established a free query endpoint for this registry.

⭐ INDETERMINATE EXISTS BECAUSE FOUR OF FIVE REGISTRIES TESTED RETURNED IT. DRKS, ANZCTR,
EU-CTR and ChiCTR all answered 200 with zero parseable identifiers and no "nothing found"
banner -- EU-CTR even echoes the drug name in its page title, which a careless parser would
read as a hit. Recording those as EMPTY would convert "our parser cannot see this registry"
into "this registry holds no such trial", which is a statement about the world we have not
earned. It is the same defect as reporting a scan's reach as its coverage, arriving through
an HTTP client.

⚠️ AND THE COVERAGE FIGURE IS OF DETERMINATE ANSWERS, NOT OF QUERIES SENT. "We searched 18
registries" is the unfalsifiable sentence this file exists to replace. What is reportable
is: of the 18 primary registries the WHO network lists, how many returned an answer we can
act on.
"""
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

OK, EMPTY, INDETERMINATE = "OK", "EMPTY", "INDETERMINATE"
FAILED, ROBOTS_REFUSED, NO_ENDPOINT = "FAILED", "ROBOTS_REFUSED", "NO_ENDPOINT"
DETERMINATE = (OK, EMPTY)

# "No results" wording, per registry where known. ⚠️ A registry whose wording we have NOT
# established can never return EMPTY -- it returns INDETERMINATE instead. That asymmetry is
# deliberate: EMPTY is a claim about the world and must be earned.
NO_RESULT_PATTERNS = re.compile(
    r"no (?:results?|records?|trials?|studies|study|matches?) (?:were )?(?:found|match)"
    r"|0 results?\b|nothing found|no trial found|search returned no", re.I)

# Endpoint per registry. Only free, non-robots-disallowed paths.
# ⚠️ ISRCTN's robots.txt disallows /search and permits /api/query -- so the API is the
# sanctioned route and the search UI is not. That distinction is per-path, not per-host.
REGISTRIES = {
    "ISRCTN": {"url": "https://www.isrctn.com/api/query/format/default?q={q}",
               "id": r"ISRCTN\d{8}",
               "note": "robots.txt disallows /search; /api/query is permitted"},
    "DRKS": {"url": "https://drks.de/search/en/trial/search?query={q}",
             "id": r"DRKS\d{8}"},
    "ANZCTR": {"url": "https://www.anzctr.org.au/TrialSearch.aspx?searchTxt={q}"
                      "&ddlSearch=Registered",
               "id": r"ACTRN\d{14}"},
    "EU-CTR": {"url": "https://www.clinicaltrialsregister.eu/ctr-search/search?query={q}",
               "id": r"\b\d{4}-\d{6}-\d{2}\b"},
    "ChiCTR": {"url": "https://www.chictr.org.cn/searchproj.html?title={q}",
               "id": r"ChiCTR[-\w]{6,20}"},
    "jRCT": {"url": "https://jrct.mhlw.go.jp/search?language=en&keyword={q}",
             "id": r"jRCT[0-9a-z]{8,12}"},
    "IRCT": {"url": "https://www.irct.ir/search?query={q}", "id": r"IRCT\d{11,20}N\d{1,3}"},
    "CRiS": {"url": None, "id": None,
             "note": "robots.txt is a blanket Disallow: / -- not queried"},
    "CTIS": {"url": None, "id": None,
             "note": "public API answered HTTP 403 to an unauthenticated client"},
    "TCTR": {"url": None, "id": r"TCTR\d{11}",
             "note": "no free query endpoint established"},
    "PACTR": {"url": None, "id": r"PACTR\d{12,20}",
              "note": "record pages return a 3,679-byte JS shell with no trial content"},
    "ReBec": {"url": None, "id": r"RBR-[0-9a-z]{6,10}",
              "note": "no free query endpoint established"},
    "CTRI": {"url": None, "id": r"CTRI/\d{4}/\d{2,3}/\d{6}",
             "note": "no free query endpoint established"},
    "RPCEC": {"url": None, "id": None, "note": "host unreachable when probed"},
    "REPEC": {"url": None, "id": None, "note": "no free query endpoint established"},
    "SLCTR": {"url": None, "id": r"SLCTR/\d{4}/\d{3}",
              "note": "no free query endpoint established"},
    "LBCTR": {"url": None, "id": None, "note": "no free query endpoint established"},
    "ITMCTR": {"url": None, "id": None, "note": "no free query endpoint established"},
}
ICTRP_PRIMARY_REGISTRY_COUNT = 18


def _curl(url, tries=3):
    for i in range(tries):
        r = subprocess.run(["curl", "-sL", "--max-time", "45", "-A", UA,
                            "-w", "\n__H__%{http_code}", url], capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        code = out.rsplit("__H__", 1)[-1].strip() if "__H__" in out else "000"
        body = out.rsplit("\n__H__", 1)[0]
        if code == "200":
            return body, code
        if code.startswith("5") or code == "000":
            if i < tries - 1:
                time.sleep(2 * (i + 1))
                continue
        return body, code
    return "", "000"


def _text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def query(code, term):
    """One registry, one term. Never claims EMPTY without the registry saying so."""
    spec = REGISTRIES.get(code) or {}
    rec = {"registry": code, "term": term,
           "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "endpoint": spec.get("url"), "note": spec.get("note")}
    if not spec.get("url"):
        rec["status"] = (ROBOTS_REFUSED if "Disallow" in (spec.get("note") or "")
                         else NO_ENDPOINT)
        rec["ids"] = []
        return rec
    url = spec["url"].format(q=term)
    body, http = _curl(url)
    rec["http"] = http
    rec["bytes"] = len(body)
    rec["sha256_16"] = hashlib.sha256(body.encode("utf-8", "replace")).hexdigest()[:16]
    if http != "200":
        rec["status"] = FAILED
        rec["ids"] = []
        return rec
    ids = sorted(set(re.findall(spec["id"], body))) if spec.get("id") else []
    txt = _text(body)
    rec["ids"] = ids
    rec["n_ids"] = len(ids)
    if ids:
        rec["status"] = OK
    elif NO_RESULT_PATTERNS.search(txt):
        rec["status"] = EMPTY
        rec["empty_because"] = "the registry stated it found nothing"
    else:
        rec["status"] = INDETERMINATE
        rec["indeterminate_because"] = (
            "HTTP 200 with no parseable identifier AND no 'nothing found' message. The "
            "results are almost certainly rendered in the browser, so what was fetched is "
            "a shell. This is NOT evidence the registry holds no such trial.")
    return rec


def search_all(term):
    rows = [query(c, term) for c in REGISTRIES]
    by = {}
    for r in rows:
        by.setdefault(r["status"], []).append(r["registry"])
    determinate = [r for r in rows if r["status"] in DETERMINATE]
    return {"term": term,
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "denominator": ICTRP_PRIMARY_REGISTRY_COUNT,
            "denominator_source": ("WHO ICTRP network primary registries, read "
                                   "2026-08-30"),
            "n_determinate": len(determinate),
            "by_status": by,
            "ids": sorted({i for r in rows for i in r.get("ids", [])}),
            "rows": rows}


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    term = " ".join(sys.argv[1:]) or "dapivirine"
    res = search_all(term)
    print("REGISTRY SEARCH -- term %r" % res["term"])
    print("  denominator: %d primary registries (%s)"
          % (res["denominator"], res["denominator_source"]))
    print("  DETERMINATE answers: %d/%d" % (res["n_determinate"], res["denominator"]))
    print()
    for r in res["rows"]:
        print("  %-8s %-15s %s" % (r["registry"], r["status"],
                                   (", ".join(r.get("ids") or [])
                                    or r.get("note") or "")[:70]))
    print()
    print("  identifiers found: %s" % (", ".join(res["ids"]) or "none"))
    print()
    print("  ⚠️ INDETERMINATE is NOT zero trials. It means the page renders results in the")
    print("     browser and we hold a shell. Reporting it as EMPTY would turn 'our parser")
    print("     cannot see this' into 'this registry holds nothing'.")
    out = os.environ.get("REG_OUT", "F:/claude-temp/registry_search.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print("  written to %s" % out)
