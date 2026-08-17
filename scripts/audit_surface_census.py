"""AUDIT SURFACE CENSUS -- how many review pages can a reader actually check?

WHY THIS EXISTS
    The question was "why does ARNI lack an extraction table?" -- and ARNI has
    one. The real question is why almost nothing else does. This counts it,
    across the whole corpus, so the number is measured rather than recalled.

THE TWO THINGS IT SEPARATES, because they are constantly conflated
    TRIAL-level provenance : a resolvable link per included trial. Widespread.
    VALUE-level provenance : which NUMBER came from which SENTENCE, and whether
                             it was read or derived. The extraction table. Rare.
    A page can carry every trial's registry link and still give a reader no way
    to check a single extracted value. "Has links" is not "is checkable".

THE TWO INSTRUMENTS, because neither alone is correct
    Raw HTML OVER-counts: a regex cannot tell href="...${escapeHtml(t.id)}"
    inside a <script> from an attribute in the document, and counting template
    source once turned 2.2% into 62.8%.
    Rendered text UNDER-counts: it omits whatever is not displayed.
    So: read raw HTML with <script>/<style> BODIES removed for the markup
    figure, and drive a real browser for the rendered figure -- and report both,
    named, because they are claims about different readers.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the extraction tables that exist are CORRECT. This counts
      presence. A page can carry a full table of wrong values and be counted.
    - NOT that a page without one is wrong to lack it. Some pool from sources
      that have no per-value sentence to quote; the census locates them, it does
      not judge them.
    - NOT that a rendered link RESOLVES. It checks shape, not reachability; a
      link to a withdrawn or mistyped NCT counts here and fails elsewhere.
    - NOT anything about the 30 pages the partition declares and disk does not
      have. Those are reported separately and are not folded into any rate.
"""
from __future__ import annotations
import argparse, glob, io, json, os, re, sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTY = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S)
HREF = re.compile(r'href=["\'](https?://[^"\']+)', re.I)
REGISTRY = re.compile(r"clinicaltrials\.gov/study/NCT\d|pubmed\.ncbi\.nlm\.nih\.gov/\d", re.I)
TABLE_SIGNATURE = "Extracted values, and where each came from"


def markup_only(html):
    """Drop program text, KEEP css-hidden content. Both halves matter."""
    return SCRIPTY.sub(" ", html)


def markup_links(html):
    """Links present in the served document, placeholders excluded."""
    out = []
    for u in HREF.findall(markup_only(html)):
        if "${" in u or "{{" in u or u.rstrip().endswith("/study/"):
            continue
        out.append(u)
    return out


def survey_static(pages):
    rows = []
    for p in pages:
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        links = markup_links(t)
        rows.append({
            "page": os.path.basename(p),
            "extraction_table": TABLE_SIGNATURE in t,
            "verbatim_quotes": t.count("<blockquote>"),
            "markup_links": len(links),
            "markup_registry_links": sum(1 for u in links if REGISTRY.search(u)),
        })
    return rows


def survey_rendered(names, port):
    """Links AFTER the page has run. Different claim, different reader."""
    from playwright.sync_api import sync_playwright
    js = """(()=>{const a=[...document.querySelectorAll('a[href^="http"]')].map(x=>x.href);
      return {all:a.length, reg:a.filter(u=>/clinicaltrials\\.gov\\/study\\/NCT\\d|pubmed\\.ncbi\\.nlm\\.nih\\.gov\\/\\d/.test(u)).length};})()"""
    out = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=["--disable-gpu"])
        pg = b.new_page()
        for n in names:
            try:
                pg.goto("http://localhost:%d/%s" % (port, n), wait_until="load", timeout=45000)
                pg.wait_for_timeout(1200)
                r = pg.evaluate(js)
                out.append({"page": n, "rendered_links": r["all"], "rendered_registry": r["reg"]})
            except Exception as ex:
                # A page that will not load is UNMEASURED, never counted as zero.
                # Recording it as 0 links is exactly the silent-omission failure
                # this whole file exists to avoid.
                out.append({"page": n, "rendered_links": None, "rendered_registry": None,
                            "error": str(ex)[:90]})
        b.close()
    return out


def rate(n, d):
    return "%d/%d (%.1f%%)" % (n, d, 100.0 * n / d) if d else "0/0 (n/a)"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--glob", default="*_REVIEW.html")
    ap.add_argument("--partition", default="outputs/corpus_partition.json",
                    help="tier definitions; tiers are surveyed separately")
    ap.add_argument("--rendered", metavar="N", type=int, default=0,
                    help="also measure N pages per tier in a real browser (needs --port served)")
    ap.add_argument("--port", type=int, default=8793)
    ap.add_argument("--json", metavar="PATH", default="")
    a = ap.parse_args()

    os.chdir(a.repo)
    pages = sorted(glob.glob(a.glob))
    rows = survey_static(pages)
    by = {r["page"]: r for r in rows}

    tiers = {"ALL PAGES": [r["page"] for r in rows]}
    missing_declared = {}
    if os.path.exists(a.partition):
        part = json.loads(open(a.partition, encoding="utf-8").read())
        for tier, ids in (part.get("tiers") or {}).items():
            if not isinstance(ids, list):
                continue
            names = [i + "_REVIEW.html" for i in ids]
            tiers[tier] = [n for n in names if n in by]
            gone = [n for n in names if n not in by]
            if gone:
                missing_declared[tier] = gone

    print("AUDIT SURFACE CENSUS -- %d pages matching %s\n" % (len(rows), a.glob))
    print("%-12s %-8s %-22s %-22s %s"
          % ("tier", "pages", "extraction table", "verbatim quotes", "registry link IN MARKUP"))
    for tier, names in tiers.items():
        rs = [by[n] for n in names]
        d = len(rs)
        print("%-12s %-8d %-22s %-22s %s"
              % (tier, d,
                 rate(sum(1 for r in rs if r["extraction_table"]), d),
                 rate(sum(1 for r in rs if r["verbatim_quotes"]), d),
                 rate(sum(1 for r in rs if r["markup_registry_links"]), d)))

    for tier, gone in missing_declared.items():
        print("\n  %s declares %d page(s) that are NOT on disk -- reported, never "
              "folded into a rate:\n    %s" % (tier, len(gone), ", ".join(sorted(gone)[:8])))

    have = [r for r in rows if r["extraction_table"]]
    print("\nPAGES WITH A VALUE-LEVEL AUDIT SURFACE (%d):" % len(have))
    for r in sorted(have, key=lambda x: x["page"]):
        print("   %-46s verbatim quotes=%-4d registry links in markup=%d"
              % (r["page"].replace("_REVIEW.html", ""), r["verbatim_quotes"],
                 r["markup_registry_links"]))

    if a.rendered:
        print("\nRENDERED MEASUREMENT -- what a reader with JavaScript sees.")
        print("Serve the repo first:  python -m http.server %d --bind 127.0.0.1" % a.port)
        for tier, names in tiers.items():
            if tier == "ALL PAGES":
                continue
            sample = names[:a.rendered]
            res = survey_rendered(sample, a.port)
            ok = [r for r in res if r["rendered_registry"] is not None]
            unmeasured = [r for r in res if r["rendered_registry"] is None]
            print("  %-12s %s carry a resolvable registry/PMID link AFTER JS%s"
                  % (tier, rate(sum(1 for r in ok if r["rendered_registry"]), len(ok)),
                     "" if not unmeasured else
                     "   [%d UNMEASURED, not counted as zero]" % len(unmeasured)))

    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), indent=1)
        print("\nrows written to %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
