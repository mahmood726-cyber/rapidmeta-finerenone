"""Second resolution route for the GIN bodies Wikidata's label matcher could not find.

WHY A SECOND ROUTE RATHER THAN MORE OF THE FIRST. 80 of the 104 unresolved returned "no
wikidata entity". That is a statement about wbsearchentities, which matches LABELS and
ALIASES only -- it fails on any body whose Wikidata label differs from the string GIN
prints, which is most non-English and most national bodies. More attempts down the same
route would return the same answer more confidently.

THE ROUTE: Wikipedia full-text search, which indexes article BODIES, then follow the
article to its Wikidata item and read P856. An organisation is often described in an
article whose title is not its GIN name.

WHAT IS STILL NOT CLAIMED. A resolution is a candidate address, not a source. It is
probed separately, and a wrong address is worse than none -- the first route resolved ECRI
to the Council of Europe and Covidence to WHO, and both were caught only by reading all 35
by hand. This route is at least as prone to that, so its output is marked
`route2_needs_hand_check` and is NOT merged into the resolved count until checked.
"""
import io
import json
import os
import sys
import time

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

S = r"F:\claude-temp\claude\C--Users-mahmo\f842b4e4-f3de-4ce2-83d8-0adf7aa7cfb1\scratchpad"
WP = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "rapidmeta-guideline-resolver/1.0 (research use)"}


def wiki_search(name):
    """Full-text search for the organisation, returning candidate article titles."""
    try:
        r = requests.get(WP, params={"action": "query", "list": "search",
                                     "srsearch": name[:200], "srlimit": 3,
                                     "format": "json"}, headers=UA, timeout=30)
        if r.status_code != 200:
            return [], "wikipedia search http %d" % r.status_code
        return [h["title"] for h in (r.json().get("query", {}).get("search") or [])], None
    except Exception as e:
        return [], "wikipedia search " + type(e).__name__


def wiki_to_site(title):
    """Article -> Wikidata item -> P856 official website, plus the external link the
    article itself carries. Two independent hints are better than one."""
    try:
        r = requests.get(WP, params={"action": "query", "prop": "pageprops|extlinks",
                                     "titles": title, "ellimit": 60, "format": "json"},
                         headers=UA, timeout=30)
        if r.status_code != 200:
            return None, None
        pages = (r.json().get("query", {}).get("pages") or {})
        for _, pg in pages.items():
            qid = (pg.get("pageprops") or {}).get("wikibase_item")
            links = [e.get("*") for e in (pg.get("extlinks") or []) if e.get("*")]
            return qid, links
    except Exception:
        pass
    return None, None


def wd_site(qid):
    try:
        r = requests.get("https://www.wikidata.org/w/api.php",
                         params={"action": "wbgetclaims", "entity": qid,
                                 "property": "P856", "format": "json"},
                         headers=UA, timeout=30)
        if r.status_code != 200:
            return None
        for c in ((r.json().get("claims") or {}).get("P856") or []):
            v = (((c.get("mainsnak") or {}).get("datavalue") or {}).get("value"))
            if isinstance(v, str) and v.startswith("http"):
                return v
    except Exception:
        return None
    return None


if __name__ == "__main__":
    p = os.path.join(S, "gin_resolved.json")
    rows = json.load(open(p, encoding="utf-8"))
    todo = [r for r in rows if not r.get("site")]
    print("bodies still unresolved after route 1: %d" % len(todo))
    print()
    found = 0
    for i, r in enumerate(todo, 1):
        titles, why = wiki_search(r["name"])
        if not titles:
            r.setdefault("route2", {})["result"] = why or "no wikipedia article"
            time.sleep(0.4)
            continue
        qid, links = wiki_to_site(titles[0])
        site = wd_site(qid) if qid else None
        r["route2"] = {"wikipedia_article": titles[0], "wikidata": qid,
                       "candidate_site": site,
                       "article_external_links": (links or [])[:5],
                       "route2_needs_hand_check": True,
                       "_caution": ("Route 1 resolved ECRI to the Council of Europe and "
                                    "Covidence to WHO. A candidate is not an address "
                                    "until a human has looked at it.")}
        if site:
            found += 1
        time.sleep(0.5)
        if i % 20 == 0:
            print("  %d/%d tried, %d candidates" % (i, len(todo), found))
    json.dump(rows, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("ROUTE 2 RESULT, against the GIN denominator of %d:" % len(rows))
    print("  already resolved by route 1                 %d"
          % sum(1 for r in rows if r.get("site")))
    print("  NEW CANDIDATES from route 2 (unverified)    %d" % found)
    print("  still nothing                               %d"
          % sum(1 for r in rows
                if not r.get("site") and not (r.get("route2") or {}).get("candidate_site")))
    print()
    print("Candidates are NOT counted as resolved. A wrong address is worse than none.")
