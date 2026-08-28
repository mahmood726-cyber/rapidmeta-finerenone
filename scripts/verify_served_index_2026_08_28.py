"""Count the KEEP set in the LIVE bytes, and prove an unindexed page still serves.

"COMMITTED, NOT SERVED" COST AN HOUR OF MISUNDERSTANDING. A commit proves what a file says in
git. A reader gets whatever GitHub Pages is serving, which is a different thing until the
deploy lands. So this fetches the live URLs and counts what is actually there.

TWO CLAIMS, AND THE SECOND IS THE ONE THAT PROTECTS READERS:

    every surface serves ONLY KEEP entries      -- the reader stops wading
    an UNINDEXED page still returns 200         -- nothing was broken, only unlisted

The second is checked against pages that were deliberately dropped from the indexes. If any
of them 404s, the change did more than it claimed and must be reverted -- "nothing is
deleted" is a promise about the reader's existing links, not about the listings.

CACHE-BUSTED. A CDN can serve a stale copy for minutes and a stale 200 would read exactly
like a successful deploy.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://mahmood726-cyber.github.io/rapidmeta-finerenone/"
OUT = os.path.join(REPO, "outputs", "served_index_2026_08_28.json")

SURFACES = ["index.html", "sitemap.xml", "audit_table.html", "portfolio_pools.html",
            "auto-gallery.html", "index_indicators.json", "outputs/portfolio_index.json"]


def fetch(path):
    url = SITE + path + ("&" if "?" in path else "?") + "cb=%d" % int(time.time())
    r = subprocess.run(["curl", "-sS", "--max-time", "90", "-w", "\n%{http_code}", url],
                       capture_output=True)
    body = (r.stdout or b"").decode("utf-8", "replace")
    if "\n" not in body:
        return None, 0
    body, code = body.rsplit("\n", 1)
    try:
        return body, int(code.strip())
    except ValueError:
        return body, 0


def entries(body, path, reviews):
    if path.endswith(".xml"):
        return set(re.findall(r"<loc>[^<]*?/([A-Za-z0-9_.\-]+\.html)</loc>", body)) & reviews
    if path.endswith(".json"):
        try:
            d = json.loads(body)
        except ValueError:
            return set()
        found = set()

        def walk(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if isinstance(k, str) and k in reviews:
                        found.add(k)
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
            elif isinstance(x, str) and x in reviews:
                found.add(x)
        walk(d)
        return found
    return set(re.findall(r"href\s*=\s*[\"']\.?/?([A-Za-z0-9_.\-]+\.html)[\"'#?]",
                          body)) & reviews


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    keep = set(l.strip() for l in
               io.open(os.path.join(REPO, "outputs", "_ready_keep.txt"), encoding="utf-8")
               if l.strip())
    surf = json.load(io.open(os.path.join(REPO, "outputs", "surfaces_2026_08_28.json"),
                             encoding="utf-8"))
    names = set(s["surface"] for s in surf["surfaces"])
    reviews = set(p for p in os.listdir(REPO)
                  if p.endswith(".html") and os.path.isfile(os.path.join(REPO, p))
                  and p not in names)

    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    say("SERVED verification at %s" % stamp)
    say("KEEP %d   review population %d" % (len(keep), len(reviews)))
    say("")
    say("%-34s %5s %8s %9s %9s" % ("surface (live)", "http", "entries", "in KEEP", "outside"))

    rows, bad = [], []
    for path in SURFACES:
        body, code = fetch(path)
        if code != 200 or body is None:
            say("%-34s %5s   FETCH FAILED" % (path[:34], code))
            bad.append((path, "http %s" % code))
            rows.append({"surface": path, "http": code, "entries": None})
            continue
        e = entries(body, path, reviews)
        outside = e - keep
        say("%-34s %5d %8d %9d %9d" % (path[:34], code, len(e), len(e & keep), len(outside)))
        rows.append({"surface": path, "http": code, "entries": len(e),
                     "in_keep": len(e & keep), "outside_keep": sorted(outside)[:10]})
        if outside:
            bad.append((path, "%d entries outside KEEP" % len(outside)))
        time.sleep(0.4)

    # nothing was deleted: pages dropped from the indexes must still serve
    say("")
    say("UNINDEXED PAGES MUST STILL SERVE -- this is the promise to anyone holding a link")
    dropped = sorted(reviews - keep)
    sample = [dropped[0], dropped[len(dropped) // 3], dropped[2 * len(dropped) // 3],
              dropped[-1]] if len(dropped) > 4 else dropped
    served = []
    for p in sample:
        body, code = fetch(p)
        ok = code == 200 and body is not None and len(body) > 500
        say("   %-52s http %s  %s" % (p[:52], code, "SERVES" if ok else "BROKEN"))
        served.append({"page": p, "http": code, "ok": ok})
        if not ok:
            bad.append((p, "unindexed page no longer serves"))
        time.sleep(0.3)

    say("")
    if bad:
        say("FAILED: %d problem(s)" % len(bad))
        for p, why in bad:
            say("   %-40s %s" % (p[:40], why))
    else:
        say("PASS: every surface serves only KEEP entries, and unindexed pages still serve.")

    json.dump({"checked_at": stamp, "site": SITE, "n_keep": len(keep),
               "surfaces": rows, "unindexed_sample": served,
               "problems": [{"path": p, "why": w} for p, w in bad]},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
