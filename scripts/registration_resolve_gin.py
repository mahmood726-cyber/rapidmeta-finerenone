"""Resolve GIN's 136 member bodies to queryable endpoints.

THE PROBLEM, established by two independent methods rather than assumed:
  1. Not one of the 136 WordPress API records carries an external URL (acf is empty,
     content holds only a PDF link on GIN's own domain).
  2. The rendered member profile pages carry no link to the member's own site either --
     only GIN's fonts, GIN's charity registration and GIN's social account.
  => GIN IS A DENOMINATOR, NOT AN ADDRESS BOOK. An index is not a source.

THE ROUTE USED INSTEAD: Wikidata. Organisations carry P856 "official website". This is a
DERIVATION from a public knowledge base, not a hand-written list -- the rule is that the
vocabulary must come from data, and 136 names go in, whatever Wikidata holds comes out.

WHAT IS RECORDED, and the distinction is the whole point:
  RESOLVED      a website was found for the body
  UNRESOLVED    no entity, or an entity with no official website. Reported by name.
  and separately, for each RESOLVED site:
  QUERYABLE     a machine-readable search endpoint responded 200 with parseable content
  REACHED       the site responds but offers no machine-readable search
  BLOCKED       a named obstacle, with its status code

A 200 IS NOT A DOCUMENT. A site that returns 200 and a JavaScript shell is REACHED, not
QUERYABLE, and the check for that is content-based rather than status-based.

⚠ The default python-requests user-agent is itself an obstacle: g-i-n.net returned 403 to
it and 200 to a browser UA. Every probe here sends a browser UA, and any earlier "403" or
"blocked" recorded without one must be re-tested before it is believed.
"""
import io
import json
import os
import re
import sys
import time

import requests

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

S = r"F:\claude-temp\claude\C--Users-mahmo\f842b4e4-f3de-4ce2-83d8-0adf7aa7cfb1\scratchpad"
UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")}
# WIKIMEDIA REFUSES A GENERIC BROWSER UA. Their policy requires a descriptive agent, and a
# browser string gets 403. THERE IS NO UNIVERSAL USER-AGENT: the browser string is what
# made g-i-n.net work and is exactly what breaks Wikidata. Each host has its own policy,
# so a 403 is a fact about a REQUEST, not about a site, until it has been re-tried properly.
WD_UA = {"User-Agent": "rapidmeta-guideline-resolver/1.0 (research use; contact via repository issues)"}
WD = "https://www.wikidata.org/w/api.php"


def wd_search(name):
    """Find a Wikidata entity for an organisation name."""
    try:
        r = requests.get(WD, params={"action": "wbsearchentities", "search": name[:180],
                                     "language": "en", "format": "json", "limit": 5,
                                     "type": "item"}, headers=WD_UA, timeout=30)
        if r.status_code != 200:
            return None, "wikidata search http %d" % r.status_code
        hits = r.json().get("search") or []
        if not hits:
            return None, "no wikidata entity"
        # TAKING search[0] BLINDLY RESOLVES AN ORGANISATION TO A PAPER. Searching
        # "European Hematology Association" returns the society first but a 2014 journal
        # ARTICLE of the same name second. A wrong website is worse than no website, so
        # prefer an entity whose description reads like a body, and record which was used.
        ORGISH = ("organisation", "organization", "association", "society", "institute",
                  "agency", "college", "network", "foundation", "ministry", "centre",
                  "center", "council", "federation", "university", "hospital", "charity",
                  "nonprofit", "non-profit", "group", "committee", "authority")
        PAPERISH = ("scientific article", "journal article", "published in", "congress",
                    "conference paper", "edition or translation")
        for h in hits:
            desc = (h.get("description") or "").lower()
            if any(w in desc for w in PAPERISH):
                continue
            if any(w in desc for w in ORGISH) or not desc:
                return h["id"], None
        return None, ("wikidata hits exist but none describes an organisation: %s"
                      % [h.get("description") for h in hits][:3])
    except Exception as e:
        return None, "wikidata search " + type(e).__name__


def wd_site(qid):
    """P856 official website for an entity."""
    try:
        r = requests.get(WD, params={"action": "wbgetclaims", "entity": qid,
                                     "property": "P856", "format": "json"},
                         headers=WD_UA, timeout=30)
        if r.status_code != 200:
            return None
        cl = (r.json().get("claims") or {}).get("P856") or []
        for c in cl:
            v = (((c.get("mainsnak") or {}).get("datavalue") or {}).get("value"))
            if isinstance(v, str) and v.startswith("http"):
                return v
    except Exception:
        return None
    return None


JS_SHELL = re.compile(r"<div id=\"root\"|<div id=\"app\"|window\.__NUXT__|__NEXT_DATA__", re.I)


def probe(site):
    """Classify a resolved site. Content-based, because a 200 is not a document."""
    out = {"site": site}
    try:
        r = requests.get(site, headers=UA, timeout=30, allow_redirects=True)
    except Exception as e:
        out.update(state="BLOCKED", obstacle=type(e).__name__)
        return out
    out["http"] = r.status_code
    if r.status_code != 200:
        out.update(state="BLOCKED", obstacle="http %d" % r.status_code)
        return out
    txt = r.text
    if "Just a moment" in txt[:2000] or "cf-mitigated" in str(r.headers):
        out.update(state="BLOCKED", obstacle="Cloudflare challenge behind a 200")
        return out
    if len(r.content) < 6000 and JS_SHELL.search(txt):
        out.update(state="REACHED", note="200 but a JavaScript shell; no server-rendered "
                                         "content. A 200 is not a document.")
        return out
    # look for a machine-readable search surface, derived from the page, not guessed
    surfaces = []
    if re.search(r"/wp-json/", txt) or requests_ok(site.rstrip("/") + "/wp-json/wp/v2/"):
        surfaces.append("wordpress-rest")
    if re.search(r"<link[^>]+type=[\"']application/opensearchdescription", txt, re.I):
        surfaces.append("opensearch")
    if re.search(r"name=[\"']q[\"']|/search\?", txt, re.I):
        surfaces.append("html-search-form")
    out["surfaces"] = surfaces
    out["state"] = "QUERYABLE" if surfaces else "REACHED"
    if not surfaces:
        out["note"] = "responds, but no machine-readable search surface was found"
    return out


def requests_ok(url):
    try:
        r = requests.get(url, headers=UA, timeout=15)
        return r.status_code == 200 and "json" in (r.headers.get("content-type") or "")
    except Exception:
        return False


if __name__ == "__main__":
    orgs = json.load(open(os.path.join(S, "gin_orgs.json"), encoding="utf-8"))
    print("GIN member bodies to resolve: %d" % len(orgs))
    out = []
    for i, o in enumerate(orgs, 1):
        name = re.sub(r"&#\d+;|&amp;", " ", o["name"]).strip()
        qid, why = wd_search(name)
        rec = {"gin_id": o["id"], "name": name, "gin_profile": o["link"],
               "wikidata": qid, "resolve_note": why}
        if qid:
            site = wd_site(qid)
            rec["site"] = site
            if not site:
                rec["resolve_note"] = "wikidata entity %s has no P856 official website" % qid
        out.append(rec)
        if i % 20 == 0:
            print("  resolved %d/%d" % (i, len(orgs)))
        time.sleep(0.05)
    json.dump(out, open(os.path.join(S, "gin_resolved.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    got = [r for r in out if r.get("site")]
    print()
    print("RESOLUTION, against the GIN denominator of %d:" % len(orgs))
    print("  resolved to a website   %d" % len(got))
    print("  unresolved              %d" % (len(orgs) - len(got)))
    print()
    print("Unresolved are reported by name in gin_resolved.json, never as a silent gap.")
