"""EXTERNAL DEPENDENCY CENSUS -- can this page show its provenance from its own bytes?

WHY THIS EXISTS
    The argument of this whole project is that a reader without journal access
    can check us. A page that fetches its provenance from a third party at load
    is not checkable; it is CHECKABLE ON A GOOD DAY. When that third party rate-
    limits, is down, is blocked by a firewall, or has simply changed its API, the
    reader sees an unsourced page AND HAS NO WAY TO KNOW WHY. There is no error
    state that says "the sources exist but could not be fetched"; there is just a
    page with less on it.

    Measured 2026-08-17: 19 of 21 sampled pages issue third-party requests on
    load, and ALL NINETEEN received HTTP 429 from api.openalex.org in the same
    run. This is not bad luck on one page. The provenance layer of most of the
    corpus was failing, everywhere, at the moment it was measured, and nothing on
    any page said so. The only two pages with zero outbound requests were the two
    built to the current standard.

    Also fetched by ~874 pages: cdnjs.cloudflare.com and webr.r-wasm.org. Those
    are not data, they are CODE -- the R runtime used for statistical
    cross-validation is itself downloaded from a third party at read time. A
    reproducibility claim that depends on a CDN being up is a weaker claim than
    it appears, and it degrades silently.

READ SCRIPT SOURCE HERE, DELIBERATELY
    Elsewhere in this repo the rule is to drop <script> bodies, because program
    text is not page content. This file asks the opposite question -- "does this
    page's CODE call out?" -- so script source is exactly the right thing to
    read. Same rule, attribute content to its context, pointing the other way.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the page is correct, or that its embedded provenance is complete.
      Self-contained and wrong is entirely possible.
    - NOT that every referenced host is FETCHED. The static arm finds mentions;
      only the rendered arm sees requests. They disagree, and both are reported.
    - NOT that a page with zero outbound requests renders everything a reader
      needs; it establishes only that nothing was needed FROM ELSEWHERE.
    - NOT anything about outbound LINKS. A link a reader may click is not a
      dependency; a fetch the page makes on their behalf is.
"""
from __future__ import annotations
import argparse, collections, glob, io, os, random, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPTY = re.compile(r"<(script|style)\b[^>]*>(.*?)</\1\s*>", re.I | re.S)
HOST = re.compile(r"https?://([a-z0-9][a-z0-9.-]*\.[a-z]{2,})", re.I)
# Hosts that indicate a DATA or CODE dependency rather than a citation link.
DEPENDENCY_HINT = ("api.", "ebi.ac.uk", "openalex", "crossref", "europepmc",
                   "cdnjs", "r-wasm", "unpkg", "jsdelivr", "googleapis")


def hosts_in_scripts(html):
    seen = set()
    for m in SCRIPTY.finditer(html):
        for h in HOST.findall(m.group(2)):
            seen.add(h.lower())
    return seen


def static_arm(files):
    per_host = collections.Counter()
    flagged = {}
    for p in files:
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        hs = hosts_in_scripts(t)
        dep = {h for h in hs if any(k in h for k in DEPENDENCY_HINT)}
        if dep:
            flagged[os.path.basename(p)] = dep
        for h in hs:
            per_host[h] += 1
    return per_host, flagged


def rendered_arm(names, port, wait_ms):
    """What actually goes out on load. A page that will not load is UNMEASURED."""
    from playwright.sync_api import sync_playwright
    rows = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=["--disable-gpu"])
        for n in names:
            ctx = b.new_context()
            pg = ctx.new_page()
            reqs, bad = [], []
            pg.on("request", lambda r: reqs.append(r.url)
                  if r.url.startswith("http") and "localhost" not in r.url else None)
            pg.on("response", lambda r: bad.append((r.status, r.url))
                  if r.status >= 400 and "localhost" not in r.url else None)
            try:
                pg.goto("http://localhost:%d/%s" % (port, n), wait_until="load", timeout=60000)
                pg.wait_for_timeout(wait_ms)
                rows.append({"page": n, "outbound": len(reqs),
                             "hosts": sorted({r.split("/")[2] for r in reqs}),
                             "failed": [(s, u.split("/")[2]) for s, u in bad]})
            except Exception as ex:
                rows.append({"page": n, "outbound": None, "hosts": [], "failed": [],
                             "error": str(ex)[:80]})
            ctx.close()
        b.close()
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--glob", default="*_REVIEW.html")
    ap.add_argument("--rendered", type=int, default=0, metavar="N",
                    help="also load N random pages in a browser (repo must be served on --port)")
    ap.add_argument("--port", type=int, default=8795)
    ap.add_argument("--wait", type=int, default=3500)
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()

    os.chdir(a.repo)
    files = sorted(glob.glob(a.glob))
    per_host, flagged = static_arm(files)
    n = len(files)
    print("EXTERNAL DEPENDENCY CENSUS -- %d pages\n" % n)
    print("hosts referenced in SCRIPT bodies (a mention, not yet a request):")
    for h, c in per_host.most_common(14):
        mark = "  <-- dependency" if any(k in h for k in DEPENDENCY_HINT) else ""
        print("   %-34s %5d  (%4.1f%%)%s" % (h, c, 100.0 * c / n, mark))
    print("\npages referencing at least one DATA or CODE host: %d / %d (%.1f%%)"
          % (len(flagged), n, 100.0 * len(flagged) / n))

    if a.rendered:
        random.seed(a.seed)
        sample = random.sample(files, min(a.rendered, len(files)))
        rows = rendered_arm(sample, a.port, a.wait)
        measured = [r for r in rows if r["outbound"] is not None]
        unmeasured = [r for r in rows if r["outbound"] is None]
        withreq = [r for r in measured if r["outbound"]]
        failing = [r for r in measured if r["failed"]]
        print("\nRENDERED ARM -- what actually leaves the browser on load")
        for r in rows:
            if r["outbound"] is None:
                print("   %-42s UNMEASURED (%s)" % (r["page"][:42], r.get("error", "")[:40]))
                continue
            print("   %-42s outbound=%-3d %s%s"
                  % (r["page"].replace("_REVIEW.html", "")[:42], r["outbound"],
                     r["hosts"][:3], "  FAILED:%s" % r["failed"][:2] if r["failed"] else ""))
        print("\n   %d/%d issue third-party requests; %d/%d had a FAILING third-party "
              "response%s" % (len(withreq), len(measured), len(failing), len(measured),
                              "   [%d UNMEASURED, never counted as clean]" % len(unmeasured)
                              if unmeasured else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
