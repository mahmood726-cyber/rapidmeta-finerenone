"""Who links to the pages we are about to remove? Report before anything moves.

TWO QUESTIONS AND ONLY ONE IS ANSWERABLE FROM HERE. Saying so is the point:

  INTERNAL  which surfaces in this repository link to these pages. Fully measurable, by
            searching every tracked file rather than by recalling which surfaces exist.
  EXTERNAL  who outside this repository links to them. NOT MEASURABLE with the instruments
            available in this lane: it needs a backlink index, server logs or a referrer
            report, none of which is reachable here.

Reporting "0 external referrers" would be a claim about the world derived from an instrument
that cannot see the world. The honest output is NOT MEASURABLE, named, with what would be
needed to measure it -- because a reader of this report must be able to tell "nobody links
this" from "we did not look".

WHY THE INTERNAL HALF IS SEARCHED, NOT LISTED. A page removed from six surfaces and left on a
seventh is still in the reader's way, and the seventh is the one nobody remembered. So this
greps every tracked text file for each page name rather than checking a list of known
surfaces.

Usage: referrer_check_2026_08_28.py <list.txt>
"""
import collections
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "referrer_check_2026_08_28.json")

TEXTY = (".html", ".json", ".md", ".xml", ".txt", ".js", ".css", ".py")


def main():
    listfile = sys.argv[1]
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    targets = [l.strip().split(chr(9))[0] for l in io.open(listfile, encoding="utf-8")
               if l.strip()]
    tset = set(targets)
    say("pages under consideration: %d" % len(targets))
    say("")

    # every tracked text file, from git rather than from a walk
    tracked = subprocess.run(["git", "ls-files"], capture_output=True, cwd=REPO)
    files = [f for f in tracked.stdout.decode("utf-8", "replace").split(chr(10))
             if f.strip() and f.lower().endswith(TEXTY)]
    say("tracked text files searched: %d" % len(files))

    refs = collections.defaultdict(set)     # page -> {referring file}
    surfaces = collections.Counter()
    for f in files:
        if f in tset:                       # a target linking to another target is not a
            continue                        # discovery surface; it is going away too
        fp = os.path.join(REPO, f)
        try:
            body = io.open(fp, encoding="utf-8", errors="replace").read()
        except (OSError, MemoryError):
            continue
        for t in targets:
            if t in body:
                refs[t].add(f)
                surfaces[f] += 1

    linked = {t: sorted(v) for t, v in refs.items() if v}
    say("")
    say("INTERNAL REFERRERS -- measured by searching every tracked text file")
    say("  pages linked from at least one surface : %d / %d" % (len(linked), len(targets)))
    say("  pages linked from NO surface           : %d / %d"
        % (len(targets) - len(linked), len(targets)))
    say("")
    say("  referring surfaces, most links first:")
    for f, n in surfaces.most_common(20):
        say("    %-58s %5d page(s)" % (f[:58], n))
    if len(surfaces) > 20:
        say("    ... and %d more surface(s)" % (len(surfaces) - 20))
    say("")
    say("EXTERNAL REFERRERS -- NOT MEASURABLE from this lane.")
    say("  No backlink index, server log or referrer report is reachable here. Reporting")
    say("  zero would be a claim about the world from an instrument that cannot see it.")
    say("  To measure: a search-engine backlink query, or the host's access logs.")

    json.dump({"internal": {"searched_files": len(files),
                            "pages_linked": len(linked),
                            "pages_unlinked": len(targets) - len(linked),
                            "surfaces": dict(surfaces),
                            "by_page": linked},
               "external": "NOT MEASURABLE -- no backlink index, server log or referrer "
                           "report reachable from this lane; zero would be a claim about "
                           "the world from an instrument that cannot see it"},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
