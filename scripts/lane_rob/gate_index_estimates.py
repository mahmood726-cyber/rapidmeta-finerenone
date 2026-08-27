# -*- coding: utf-8 -*-
"""GATE: every estimate the front door republishes must still match its object.

WHY THIS PAGE AND NOT ANOTHER. index.html is the most-visited page in the corpus, it
republishes pooled estimates for scores of reviews, and it is HAND-MAINTAINED -- no generator
has ever produced it from the objects it quotes. So it is the one surface where a number can
drift from its source silently and indefinitely: correcting a review updates the review, and
nothing updates the front door. Every other rendered estimate in this corpus is derived at
build time from the object; these are transcribed.

WHAT IT CHECKS. Each card names a page and states `Pooled: MEASURE point (low to high), k=N`.
The page resolves through PAGE_MAP to a store, and the store holds `pooled.point`,
`pooled.ci_low`, `pooled.ci_high` per outcome. The card must agree with SOME outcome in its
own store, compared at the precision the card itself displays -- a card showing 0.84 is not
wrong because the object holds 0.8715 at four places, but it is wrong if the object holds
0.87 at two.

FOUR VERDICTS, so nothing is silently dropped and the denominator is never the number of
cards that happened to parse:

  MATCHES        an outcome in the page's store agrees at the displayed precision
  MISMATCH       the store has pooled outcomes and none agrees -- a stale republished number
  NO_STORE       PAGE_MAP does not name the page, so the card cannot be verified at all
  NO_POOLED      the store exists and holds no pooled result to compare against

AND THE FIRST VERSION OF THIS GATE REPORTED PASS ON 19 OF ROUGHLY 116. It parsed only the
structured cards -- `Pooled: MEASURE point (low to high)` inside an anchor -- and every one of
those 19 agreed with its object, so it printed a clean verdict for the front door while some
ninety further estimate-shaped strings on the same page went unread. That is the reach-versus-
coverage defect occurring inside a freshly written gate, which is where it does the most
damage, because a gate's whole output is a claim about a population.

The widened form reads EVERY estimate on the page and sorts it three ways, because they are
not the same kind of claim:

  CARD_POOLED       a structured card claim. Must agree with its object.
  PROSE_SUPERSEDED  prose that explicitly marks the number as old -- withdrawn, corrected,
                    superseded, or the left side of an arrow. It is a claim ABOUT THE PAST and
                    must NOT be expected to match the current object.
  PROSE_UNMARKED    a number in prose with nothing marking it as historical. Nothing verifies
                    these, and they read to a reader exactly like a current estimate.

NO_STORE IS NOT A PASS. A card quoting a number for a page with no object is the least
checkable claim on the site, not the most innocent, and it is counted separately rather than
folded into either arm.
"""
import collections
import html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

CARD = re.compile(
    r'<a\s+href="([A-Za-z0-9_\-]+\.html)"[^>]*class="card[^"]*"\s*>(.*?)</a>', re.S | re.I)
NAME = re.compile(r'class="name"\s*>(.*?)<', re.S)
POOLED = re.compile(
    r"Pooled:\s*([A-Za-z_][A-Za-z_ ]{0,18}?)\s*"
    r"([-\u2212]?\d+(?:\.\d+)?)\s*\(\s*([-\u2212]?\d+(?:\.\d+)?)\s*"
    r"(?:to|\u2013|\u2014|-)\s*([-\u2212]?\d+(?:\.\d+)?)\s*\)")
KEQ = re.compile(r"\bk\s*=\s*(\d+)")


def txt(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def page_map():
    f = os.path.join("ssot", "PAGE_MAP.json")
    m = json.load(io.open(f, encoding="utf-8")) if os.path.exists(f) else {}
    return {os.path.basename(k): v for k, v in m.items()
            if isinstance(v, str) and os.path.exists(v)}


def dp(s):
    """decimal places the card chose to display -- the precision the claim is made at"""
    return len(s.split(".")[1]) if "." in s else 0


def agrees(shown, held):
    if held is None:
        return False
    try:
        return round(float(held), dp(shown)) == round(float(shown), dp(shown))
    except (TypeError, ValueError):
        return False


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    pm = page_map()
    raw = io.open("index.html", encoding="utf-8", errors="replace").read()
    cards = CARD.findall(raw)
    rows, no_estimate = [], 0
    for page, body in cards:
        t = txt(body)
        m = POOLED.search(t)
        if not m:
            no_estimate += 1              # BOTH ARMS: a card need not quote a number
            continue
        meas, pt, lo, hi = m.groups()
        k = KEQ.search(t)
        rec = {"page": page, "name": txt(NAME.search(body).group(1)) if NAME.search(body) else "",
               "measure": meas.strip(), "point": pt, "lo": lo, "hi": hi,
               "k": k.group(1) if k else None}
        store = pm.get(page)
        if not store:
            rec["verdict"] = "NO_STORE"
            rows.append(rec)
            continue
        try:
            obj = json.load(io.open(store, encoding="utf-8"))
        except Exception:
            rec["verdict"] = "NO_POOLED"
            rows.append(rec)
            continue
        by = ((obj.get("results") or {}).get("by_outcome") or {})
        cands = [(oid, o.get("pooled"), o.get("k")) for oid, o in by.items()
                 if isinstance(o, dict) and isinstance(o.get("pooled"), dict)]
        if not cands:
            rec["verdict"] = "NO_POOLED"
            rows.append(rec)
            continue
        best = None
        for oid, pl, kk in cands:
            if (agrees(pt, pl.get("point")) and agrees(lo, pl.get("ci_low"))
                    and agrees(hi, pl.get("ci_high"))):
                best = (oid, kk)
                break
        if best:
            rec["verdict"] = "MATCHES"
            rec["outcome"] = best[0]
            rec["k_held"] = best[1]
            rec["k_agrees"] = (rec["k"] is None or str(best[1]) == rec["k"])
        else:
            rec["verdict"] = "MISMATCH"
            rec["held"] = [{"outcome": oid,
                            "pooled": "%s (%s to %s)" % (pl.get("point"), pl.get("ci_low"),
                                                         pl.get("ci_high"))}
                           for oid, pl, _ in cands[:4]]
        rows.append(rec)

    # EVERY estimate on the page, not only the ones inside a card.
    plain = txt(raw)
    ANY = re.compile(r"(?<![\d.])[-−]?\d{1,4}(?:\.\d+)?\s*\(\s*"
                     r"(?:95\s*%?\s*)?(?:CI|CrI)?[^)\d]{0,12}"
                     r"[-−]?\d{1,4}(?:\.\d+)?\s*(?:to|–|—|-|,)\s*"
                     r"[-−]?\d{1,4}(?:\.\d+)?\s*\)")
    OLD_MARK = re.compile(
        r"(withdraw|supersed|corrected|replac|previously|formerly|was|no longer|"
        r"→|->|&rarr;|retract|earlier)", re.I)
    carded = {(r["point"], r["lo"], r["hi"]) for r in rows}
    prose = collections.Counter()
    unmarked = []
    for m in ANY.finditer(plain):
        nums = re.findall(r"[-−]?\d{1,4}(?:\.\d+)?", m.group(0))
        if len(nums) >= 3 and (nums[0], nums[1], nums[2]) in carded:
            prose["CARD_POOLED"] += 1
            continue
        win = plain[max(0, m.start() - 150):m.end() + 90]
        if OLD_MARK.search(win):
            prose["PROSE_SUPERSEDED"] += 1
        else:
            prose["PROSE_UNMARKED"] += 1
            unmarked.append((m.group(0)[:34], re.sub(r"\s+", " ", win)[-120:]))

    c = collections.Counter(r["verdict"] for r in rows)
    print("")
    print("GATE -- estimates republished on the front door, against their objects")
    print("")
    print("  cards on index.html                          %4d" % len(cards))
    print("  cards quoting no pooled estimate             %4d" % no_estimate)
    print("  cards quoting an estimate                    %4d  == the denominator" % len(rows))
    print("")
    for k in ("MATCHES", "MISMATCH", "NO_STORE", "NO_POOLED"):
        print("     %-12s %4d   %5.1f%%" % (k, c[k], 100.0 * c[k] / len(rows) if rows else 0))
    print("     %-12s %4d   == the population" % ("sum", sum(c.values())))
    print("")
    kdis = [r for r in rows if r["verdict"] == "MATCHES" and not r.get("k_agrees")]
    print("  matched on the estimate but NOT on k         %4d" % len(kdis))
    for r in kdis[:8]:
        print("     %-40s card k=%s   object k=%s"
              % (r["page"][:40], r["k"], r.get("k_held")))
    print("")
    bad = [r for r in rows if r["verdict"] == "MISMATCH"]
    for r in bad[:14]:
        print("   MISMATCH  %-38s card: %s %s (%s to %s)"
              % (r["page"][:38], r["measure"], r["point"], r["lo"], r["hi"]))
        for h in r.get("held", [])[:3]:
            print("             object holds %-30s %s" % (h["outcome"][:30], h["pooled"]))
    ns = [r for r in rows if r["verdict"] == "NO_STORE"]
    if ns:
        print("")
        print("  NO_STORE -- a number on the front door for a page with no object:")
        for r in ns[:12]:
            print("     %-40s %s %s (%s to %s)"
                  % (r["page"][:40], r["measure"], r["point"], r["lo"], r["hi"]))
    tot = sum(prose.values())
    print("")
    print("  EVERY estimate-shaped string on the page   %4d  == the real denominator" % tot)
    for k in ("CARD_POOLED", "PROSE_SUPERSEDED", "PROSE_UNMARKED"):
        print("     %-18s %4d   %5.1f%%" % (k, prose[k], 100.0 * prose[k] / tot if tot else 0))
    print("")
    print("  UNMARKED PROSE ESTIMATES -- nothing verifies these and nothing marks them old:")
    for e, ctx in unmarked[:12]:
        print("     %-34s ...%s" % (e, ctx[-96:]))
    json.dump(rows, io.open(r"F:\claude-temp\pend\index_estimates.json", "w",
                            encoding="utf-8"), indent=1)
    print("")
    if bad or ns:
        print("VERDICT: REFUSED. %d republished estimate(s) disagree with their object and "
              "%d cannot be verified against any object." % (len(bad), len(ns)))
        return 1
    print("VERDICT: the %d STRUCTURED card estimates all agree with their objects." % len(rows))
    print("         %d further estimates sit in prose. %d are marked as superseded and are"
          % (prose["PROSE_SUPERSEDED"] + prose["PROSE_UNMARKED"], prose["PROSE_SUPERSEDED"]))
    print("         claims about the past; %d carry no such marker and nothing checks them."
          % prose["PROSE_UNMARKED"])
    print("         This is NOT a pass for the page. It is a pass for the %d cards."
          % len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
