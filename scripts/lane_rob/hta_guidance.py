# -*- coding: utf-8 -*-
"""SOURCE CLASS: HTA bodies and guidance, added to the retrieval ladder.

⚠️ FDA AND EMA DO NOT DO HTA, and conflating them would put the wrong document behind the wrong
claim. Regulators decide MARKET AUTHORISATION -- efficacy, safety, the approved indication and
the label warnings, which CONSTRAIN any recommendation. HTA bodies decide whether it is worth
paying for, and their committee papers carry the reasoning, the thresholds and the values
actually used. Both belong on the ladder; they answer different questions.

WHAT THIS RUNG UNIQUELY SUPPLIES, and it is data rather than opinion: real willingness-to-pay
thresholds, and the values a committee actually applied. We cannot compute those from trials at
any price.

⭐ WHO ESSENTIAL MEDICINES IS THE STRONGEST ENTRY FOR THIS AUDIENCE. EML applications and
committee decisions ARE evidence-to-decision reasoning, for exactly the settings these readers
work in, and they are public. No Cochrane review links to any of it.

⛔ NARROW ON PURPOSE. WHO and NICE first, end to end, before CADTH, PBAC, HAS, IQWiG or ICER. A
layer strong in two places beats one thin in eight, and the regression risk of eight half-built
probes is real.

⚠️ AND THE THREE STATES ARE NOT OPTIONAL HERE. A body having NO GUIDANCE on a drug is a REAL
ANSWER -- verified by reading the result page and finding "No results found" -- and it is
completely different from a fetch that failed. This module distinguishes:
     FOUND            content retrieved and it names the intervention
     ABSENT_VERIFIED  the body was searched, it answered, and it holds nothing
     BLOCKED          the route refused us (403, bot protection)
     NOT_YET          no working route is implemented for this body
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))
CACHE = r"F:\claude-temp\pend\hta"
UA = "Mozilla/5.0 (compatible; rapidmeta-research/1.0)"

FOUND, ABSENT, BLOCKED, NOT_YET = "FOUND", "ABSENT_VERIFIED", "BLOCKED", "NOT_YET"


def _fetch(url, dest):
    os.makedirs(CACHE, exist_ok=True)
    r = subprocess.run(["curl", "-s", "-L", "-A", UA, "--max-time", "60", "-o", dest,
                        "-w", "%{http_code}|%{size_download}"],
                       capture_output=True, timeout=120) if False else subprocess.run(
        ["curl", "-s", "-L", "-A", UA, "--max-time", "60", "-o", dest,
         "-w", "%{http_code}|%{size_download}", url], capture_output=True, timeout=120)
    code, _, size = r.stdout.decode("ascii", "replace").partition("|")
    return code.strip(), int(size or 0)


def _text(p):
    try:
        h = io.open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))


def nice(term):
    """NICE published guidance. ⚠️ ASSERTS ON CONTENT: a 200 with 'No results found' is an
    ABSENT_VERIFIED, which is a real answer about NICE, not a failure of ours."""
    dest = os.path.join(CACHE, "nice_%s.html" % re.sub(r"\W+", "_", term)[:30])
    code, size = _fetch("https://www.nice.org.uk/guidance/published?q=%s" % term, dest)
    if code != "200":
        return {"body": "NICE", "state": BLOCKED, "http": code,
                "note": "the route refused; this says nothing about NICE's holdings"}
    t = _text(dest)
    if re.search(r"No results found", t, re.I):
        return {"body": "NICE", "state": ABSENT, "http": code,
                "evidence": "the search returned and reported no results",
                "note": "NICE holds no published guidance for this term"}
    if term.lower() in t.lower():
        return {"body": "NICE", "state": FOUND, "http": code, "chars": len(t)}
    return {"body": "NICE", "state": ABSENT, "http": code,
            "evidence": "page returned without naming the term"}


def who_iris(term):
    """WHO IRIS. Its discover API returns 403 to automated access and its HTML endpoint returns
    a JavaScript shell of 755 characters -- reachable but empty, which is the 'a 200 is not a
    document' case exactly."""
    dest = os.path.join(CACHE, "iris_%s.html" % re.sub(r"\W+", "_", term)[:30])
    code, size = _fetch("https://iris.who.int/discover?query=%s" % term, dest)
    t = _text(dest)
    if code != "200":
        return {"body": "WHO IRIS", "state": BLOCKED, "http": code}
    if len(t) < 2000:
        return {"body": "WHO IRIS", "state": BLOCKED, "http": code, "chars": len(t),
                "note": "200 with a %d-character shell: a client-rendered page, not content"
                        % len(t)}
    return {"body": "WHO IRIS", "state": FOUND if term.lower() in t.lower() else ABSENT,
            "http": code, "chars": len(t)}


def who_publication(item_id, term):
    """A named WHO publication landing page. Reachable; the landing page is NOT the guideline."""
    dest = os.path.join(CACHE, "who_%s.html" % item_id)
    code, size = _fetch("https://www.who.int/publications/i/item/%s" % item_id, dest)
    if code != "200":
        return {"body": "WHO publication", "state": BLOCKED, "http": code, "id": item_id}
    t = _text(dest)
    named = term.lower() in t.lower()
    return {"body": "WHO publication", "id": item_id, "http": code, "chars": len(t),
            "state": FOUND if named else ABSENT,
            "note": None if named else
            ("the landing page is reachable and does not name the intervention; the "
             "recommendation text is in the guideline PDF, which is a route this module "
             "does not yet implement")}


def who_eml(term):
    """WHO Essential Medicines List. NO WORKING ROUTE YET -- two API paths return 404."""
    return {"body": "WHO EML", "state": NOT_YET,
            "note": "two candidate API paths on list.essentialmeds.org returned 404; the "
                    "EML is published as PDFs and a web app, and neither is wired here"}


def probe(term, who_items=()):
    out = [nice(term), who_iris(term), who_eml(term)]
    for i in who_items:
        out.append(who_publication(i, term))
    return out


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    term = sys.argv[1] if len(sys.argv) > 1 else "dapivirine"
    rows = probe(term, who_items=("9789240031593",))
    print("")
    print("HTA AND GUIDANCE RUNG -- term: %s" % term)
    print("")
    for r in rows:
        print("  %-18s %-16s %s" % (r["body"], r["state"], r.get("note") or
                                    r.get("evidence") or "http %s, %s chars"
                                    % (r.get("http"), r.get("chars"))))
    print("")
    print("  FOUND %d · ABSENT_VERIFIED %d · BLOCKED %d · NOT_YET %d"
          % (sum(1 for r in rows if r["state"] == FOUND),
             sum(1 for r in rows if r["state"] == ABSENT),
             sum(1 for r in rows if r["state"] == BLOCKED),
             sum(1 for r in rows if r["state"] == NOT_YET)))
    print("")
    print("  ⚠️ ABSENT_VERIFIED is a real answer about the body. BLOCKED and NOT_YET say")
    print("     nothing about what the body holds -- only about our reach.")
    json.dump(rows, io.open(os.path.join(CACHE, "probe_%s.json" % term), "w",
                            encoding="utf-8"), indent=1)
