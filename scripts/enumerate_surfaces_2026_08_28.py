"""Which files can a READER NAVIGATE from? Found by searching, and by what a file DOES.

THE LAST ENUMERATION FOUND EIGHT and four of them nobody would have listed -- auto-gallery,
EVIDENCE_GAPS, index_indicators.json, portfolio_pools. A hand-written list of surfaces is a
list of the surfaces someone remembered, which is not the same population.

TWO DEFINITIONS HAD TO BE FIXED BEFORE THIS WORKED, and both were denominator errors:

  1. "every root-level .html" is NOT the population of review pages. index.html,
     audit_table.html and portfolio_pools.html are root-level .html files, so excluding
     "review pages" from the scan excluded the five most important SURFACES. The first run
     of this file did exactly that and reported sitemap and two JSON files as the only
     surfaces, silently missing index.html.

  2. "any quoted page name in a JSON file" is NOT a navigable reference. That matched every
     evidence archive, lane prompt and rebuild backup written this week -- 143 files, almost
     none of them reachable by a reader.

SO A SURFACE IS DEFINED BY WHAT IT DOES, NOT BY WHERE IT SITS OR WHAT IT MENTIONS:

    it is served as part of the site (root level, or a JSON the site fetches), AND
    it carries navigable references to at least MIN_ENTRIES review pages

A page linking to a handful of others is CONTENT -- a review citing a sibling review. A file
linking to dozens is a listing. The threshold is stated, and the files just below it are
printed so the cut can be seen rather than trusted.

ARCHIVES ARE EXCLUDED BY PATH AND COUNTED. outputs/lanes/, backups and evidence directories
are not reachable by a reader, and rewriting an evidence archive to change what it says would
falsify the record.
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "surfaces_2026_08_28.json")

MIN_ENTRIES = 10

# JSON the site fetches at runtime. Named because it is NOT root-level and would otherwise be
# missed -- portfolio_index.json was found only by searching last time.
FETCHED_JSON = ("outputs/portfolio_index.json",)

ARCHIVE_MARKERS = ("outputs/lanes/", "backup", "evidence/", "out/", "/prompts/")

# KEYED BY PAGE IS NOT THE SAME AS LISTING PAGES. These two pass the link-count test because
# their keys are page names, but they are DATA the review pages themselves consume, not
# places a reader navigates from. Stripping them would delete benchmark and exception
# evidence belonging to pages that continue to serve.
DATA_NOT_SURFACE = {
    "PUBLISHED_META_BENCHMARKS.json":
        "published meta-analysis benchmarks used for validation, fetched BY review pages",
    "STANDARD_EXCEPTIONS.json":
        "a register of pages touched without being brought to v1 -- a record, not a listing",
}

NAME = r"([A-Za-z0-9_.\-]+\.html)"
NAV_HREF = re.compile(r"href\s*=\s*[\"']\.?/?" + NAME + r"[\"'#?]")
NAV_LOC = re.compile(r"<loc>[^<]*?/" + NAME + r"</loc>")
NAV_JSON = re.compile(r"[\"']" + NAME + r"[\"']\s*[,:\]\}]")


def tracked():
    r = subprocess.run(["git", "ls-files"], capture_output=True, cwd=REPO)
    return [l for l in r.stdout.decode("utf-8", "replace").splitlines() if l]


def links_in(body):
    nav = set()
    for rx in (NAV_HREF, NAV_LOC, NAV_JSON):
        for m in rx.finditer(body):
            nav.add(m.group(1))
    return nav


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    root_html = set(p for p in os.listdir(REPO)
                    if p.endswith(".html") and os.path.isfile(os.path.join(REPO, p)))
    keep = set(l.strip() for l in
               io.open(os.path.join(REPO, "outputs", "_ready_keep.txt"), encoding="utf-8")
               if l.strip())
    say("root-level .html files : %d" % len(root_html))
    say("KEEP set               : %d" % len(keep))

    files = tracked()
    cands, n_archive = [], 0
    for rel in files:
        if any(m in rel for m in ARCHIVE_MARKERS):
            n_archive += 1
            continue
        served = ("/" not in rel and rel.lower().endswith((".html", ".xml", ".json")))
        if served or rel in FETCHED_JSON:
            cands.append(rel)
    say("tracked files          : %d" % len(files))
    say("archive paths excluded : %d" % n_archive)
    say("candidates served      : %d" % len(cands))
    say("")

    scored = []
    for rel in cands:
        fp = os.path.join(REPO, rel)
        if not os.path.exists(fp) or os.path.getsize(fp) > 40 * 1024 * 1024:
            continue
        body = io.open(fp, encoding="utf-8", errors="replace").read()
        nav = links_in(body) & root_html
        nav.discard(rel)
        if nav:
            scored.append((rel, nav))

    scored.sort(key=lambda x: -len(x[1]))
    surfaces = [(r, n) for r, n in scored
                if len(n) >= MIN_ENTRIES and r not in DATA_NOT_SURFACE]
    demoted = [(r, n) for r, n in scored
               if len(n) >= MIN_ENTRIES and r in DATA_NOT_SURFACE]
    surface_names = set(r for r, _ in surfaces)
    # the population a surface can advertise = root pages that are not themselves surfaces
    reviews = root_html - surface_names

    say("DISCOVERY SURFACES (>= %d review links)" % MIN_ENTRIES)
    say("%-44s %8s %8s %9s" % ("surface", "entries", "in KEEP", "not KEEP"))
    for rel, nav in surfaces:
        r = nav & reviews
        say("%-44s %8d %8d %9d" % (rel[:44], len(r), len(r & keep), len(r - keep)))
    say("")
    say("PASSED THE LINK TEST BUT ARE DATA, NOT LISTINGS -- excluded by name, with a reason")
    for rel, nav in demoted:
        say("   %-44s %4d   %s" % (rel[:44], len(nav), DATA_NOT_SURFACE[rel]))
    say("")
    say("JUST BELOW THE CUT -- printed so the threshold can be seen, not trusted")
    for rel, nav in [(r, n) for r, n in scored if len(n) < MIN_ENTRIES][:10]:
        say("   %-44s %d" % (rel[:44], len(nav)))

    json.dump({"min_entries": MIN_ENTRIES, "n_tracked": len(files),
               "n_archive_excluded": n_archive, "n_root_html": len(root_html),
               "n_review_pages": len(reviews), "keep": sorted(keep), "n_keep": len(keep),
               "surfaces": [{"surface": r, "entries": len(n & reviews),
                             "in_keep": len((n & reviews) & keep),
                             "not_keep": len((n & reviews) - keep)}
                            for r, n in surfaces],
               "data_not_surface": {r: DATA_NOT_SURFACE[r] for r, _ in demoted},
               "below_cut": [{"surface": r, "entries": len(n)}
                             for r, n in scored if len(n) < MIN_ENTRIES],
               "note": "a surface is defined by DOING listing work (many review links), not "
                       "by file extension or by mentioning a page name"},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("review pages (root html that are not surfaces): %d" % len(reviews))
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
