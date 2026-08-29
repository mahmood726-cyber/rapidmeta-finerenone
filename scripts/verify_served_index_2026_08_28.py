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

# THE FIRST VERSION OF THIS FLOOR COUNTED THE WRONG SET AND ACCUSED THE WRONG THING.
# It counted cards BOTH in the KEEP list AND carrying a dated readiness state, against a
# floor of 19. On 2026-08-29 it read 17 and reported "readiness flags dropped ... removing
# them is fabrication by deletion". No flag had been removed: the served file held 23
# cards and all 23 carried a state, unchanged across the file's entire history. What moved
# was KEEP MEMBERSHIP -- the intersection, not the flags.
#
# A check must measure the property it names. The property is "no card silently loses its
# not-ready flag", which is a statement about the FILE, not about its overlap with a list
# that is expected to move. Two assertions replace the one:
#
#   every card that exists carries a dated state   -- nothing was stripped
#   the number of cards has not fallen             -- nothing was deleted wholesale
#
# Neither can be satisfied by changing what is indexed, which is the loophole the old form
# had, and neither can be quietly lowered to make a run pass.
CARDS_FLOOR = 23


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


# KNOWN_NEGATIVE control for the entry matcher. A COUNT WITHOUT A MEASURED PRECISION IS NOT
# A FINDING -- this lane has said so to two other lanes tonight, and gate 2 correctly said it
# back. `entries()` decides what an index ADVERTISES, so a matcher that over-counts turns a
# clean surface into a violation and one that under-counts certifies a dirty one.
#
# The negatives are strings that LOOK like a page reference and must not be counted: a name
# that is not a review page, one inside a prose sentence rather than a link, and one that is
# a prefix of a real page but not equal to it.
KNOWN_NEGATIVES_HTML = [
    ('<a href="methods.html">methods</a>', "methods.html is not a review page"),
    ('mentions ARNI_HF_REVIEW.html in prose, not as a link',
     "a bare mention is not a navigable entry"),
    ('<a href="ARNI_HF_REVIEW_OLD.html">x</a>',
     "a longer name that merely starts with a real one"),
]


def measure_matcher_precision(reviews, say):
    """Run the negatives through the real matcher and PRINT the rate, never assume it."""
    fp = 0
    for text, why in KNOWN_NEGATIVES_HTML:
        if entries(text, "index.html", reviews):
            fp += 1
            say("   CONTROL FAILED: matched %r -- %s" % (text[:48], why))
    rate = (100.0 * fp / len(KNOWN_NEGATIVES_HTML)) if KNOWN_NEGATIVES_HTML else 0.0
    say("   known-negative control: %d/%d matched (measured false-positive rate %.1f%%)"
        % (fp, len(KNOWN_NEGATIVES_HTML), rate))
    return fp


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
    say("MATCHER PRECISION, measured before any count is reported:")
    measure_matcher_precision(reviews, say)
    say("")
    say("%-34s %5s %8s %9s %9s" % ("surface (live)", "http", "entries", "in KEEP", "outside"))

    rows, bad, bodies = [], [], {}
    for path in SURFACES:
        body, code = fetch(path)
        bodies[path] = body
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

    # A BYTE MATCH ON AN UNCHANGED PAGE PROVES NOTHING. This asserts a string that did not
    # exist on the live site before today's change, so a stale CDN copy, a cached response,
    # or a site served from somewhere else all fail it. It also settles the origin question
    # by construction: only bytes built from this repository can carry this.
    say("")
    say("CHANGED-TODAY MARKERS -- a stale or foreign copy cannot carry these")
    markers = [("index.html", "ready-index-note", "the banner added today"),
               ("index.html", "Pooled: HR 0.7636", "SGLT2_HF card description, "
                                                   "rewritten today from its withdrawal text")]
    for path, needle, what in markers:
        body, code = fetch(path)
        present = bool(body) and needle in body
        say("   %-22s %-22s %s   (%s)" % (path, needle, "PRESENT" if present else "ABSENT",
                                          what))
        if not present:
            bad.append((path, "changed-today marker %r absent from the live bytes" % needle))

    # EVERY RULED_IN PAGE MUST BE ON THE SERVED INDEX. A ruling that survives only while
    # someone remembers it is not a ruling. ARNI and the HFrEF network are in the index by
    # Mahmood's explicit instruction and FAIL the criterion -- ARNI on leg 4, HFrEF on leg 1 --
    # so nothing in the four legs will ever put them back. They are carried as first-class
    # members of the keep list, and this asserts that against the LIVE bytes rather than
    # against the repository.
    say("")
    say("RULED_IN PAGES MUST BE ON THE SERVED INDEX")
    try:
        ri = json.load(io.open(os.path.join(REPO, "outputs",
                                            "ready_index_2026_08_28.json"), encoding="utf-8"))
        ruled = [a["page"] for a in (ri.get("admitted_by_ruling") or [])]
    except (OSError, ValueError):
        ruled = []
    idx = bodies.get("index.html") or ""
    if not ruled:
        say("   NOT ASSESSABLE: no admitted_by_ruling entries found to check against")
        bad.append(("index.html", "the ruled-in list could not be read, so this gate did "
                                  "not run -- that is an absence, not a pass"))
    for page in ruled:
        carded = bool(re.search(re.escape(page) + r'"[^>]*class="card', idx))
        say("   %-44s carded on the live index: %s" % (page[:44], carded))
        if not carded:
            bad.append(("index.html",
                        "RULED_IN page %s is not on the served index. It fails the criterion "
                        "by design and only the ruling puts it there, so its absence means "
                        "the ruling was dropped by a regeneration." % page))

    # THE not-ready FLAGS MUST SURVIVE. This is a standing order expressed as a CHECK,
    # because a convention that depends on someone remembering gets broken by the next
    # person in a hurry and fails silently.
    #
    # "Ready" carries two meanings here. This index selects reviews that carry a POOLED
    # RESULT. The card flag reports readiness to PUBLISH, and these reviews are not ready --
    # seven external reviews on 2026-08-28 scored them between 23 and 40 out of 100. An
    # index that implied they were finished would be the worst thing on the site.
    #
    # So removing these flags without a real readiness assessment to replace them would be
    # FABRICATION BY DELETION, and this fails if the count drops.
    say("")
    say("STANDING ORDER: the dated not-ready flags must not be deleted")
    try:
        doc = json.loads(bodies.get("index_indicators.json") or "{}") or {}
    except ValueError:
        doc = {}
    cards = doc.get("cards") or {}
    # The date is the FILE's _measured. `readiness` carries only a state, and
    # internal.measured dates the identifier audit -- a different measurement.
    when = doc.get("_measured")
    n_cards = sum(1 for v in cards.values() if isinstance(v, dict))
    n_flag = sum(1 for v in cards.values()
                 if isinstance(v, dict) and (v.get("readiness") or {}).get("state") and when)
    stripped = n_cards - n_flag
    say("   cards in the served file: %d (floor %d)" % (n_cards, CARDS_FLOOR))
    say("   of those, carrying a DATED readiness state: %d; WITHOUT one: %d"
        % (n_flag, stripped))
    if stripped:
        bad.append(("index_indicators.json",
                    "%d card(s) exist with no dated readiness state. Removing a not-ready "
                    "flag without a replacement assessment is fabrication by deletion."
                    % stripped))
    if n_cards < CARDS_FLOOR:
        bad.append(("index_indicators.json",
                    "the served file carries %d cards, below the floor of %d -- cards were "
                    "deleted rather than reassessed" % (n_cards, CARDS_FLOOR)))
    say("   (%d of these cards are in KEEP. That overlap is NOT the test: it moves "
        "whenever index membership moves, and the previous version of this check read "
        "such a move as a deletion.)"
        % sum(1 for k, v in cards.items()
              if isinstance(v, dict) and (k + ".html") in keep))

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
