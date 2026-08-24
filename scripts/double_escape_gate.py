"""DOUBLE ESCAPE -- an entity that reached the reader as literal characters.

WHY THIS EXISTS
    TOOLING-QUEUE item 2 has recorded this as an UNSWEPT CLASS since the jump-list
    fix: "every other place that extracts text from generated markup and re-emits
    it has the same hazard." It has now produced a defect on three separate
    occasions, the third of them written by someone who had just read the queue
    item:

      1. _anchor_headings returned ESCAPED text and the caller escaped again, so
         readers saw the literal characters &middot; and &#x27; -- live on four of
         the seven v1 pages, and it had polluted the generated anchor ids.
      2. An em-dash FALLBACK escaped when it should not have been.
      3. Two cards added 2026-08-18 used the HTML entity "&mdash;" as a fallback
         string and passed it through p(), which escapes. A reader saw &amp;mdash;.

    The queue's own prescription is this check, and it is written here rather than
    argued about: NO BUILT PAGE MAY CONTAIN "&amp;" FOLLOWED BY A KNOWN ENTITY
    NAME. It fails toward ALARM -- the worst it can do is complain about a page
    that legitimately discusses HTML entities in prose, which is rare and visible.

    THE POINT IS NOT THE THREE DEFECTS. It is that "knowing a rule does not apply
    it; only a check does" has now been demonstrated five times in one session,
    twice by the author of the rule. A class that keeps recurring after being
    written down is a class that needs a checker, not another paragraph.

WHAT THIS DOES NOT ESTABLISH -- written in advance
    - NOT that escaping is correct everywhere. It catches DOUBLE encoding of named
      and numeric entities. Text escaped zero times -- raw "<" reaching the
      markup -- is a different defect and this does not look for it.
    - NOT that a clean page has no entity problems. An entity mangled some other
      way (&mdash written without its semicolon, say) is invisible here.
    - NOTHING about pages it was not run on. The corpus figure it prints carries
      its denominator for that reason.

USAGE
    python scripts/double_escape_gate.py <page.html> [...]
    python scripts/double_escape_gate.py --selftest
    python scripts/double_escape_gate.py --corpus        # every *_REVIEW.html here
"""
from __future__ import annotations
import glob
import io
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Named entities this corpus actually emits, plus the numeric form. Deliberately a
# LIST rather than "&amp;\w+;" -- the broad pattern matches ordinary prose such as
# "AT&amp;T; and then" and a checker that cries wolf gets switched off.
ENTITIES = ("middot", "mdash", "ndash", "nbsp", "amp", "lt", "gt", "quot", "apos",
            "times", "minus", "sup2", "deg", "hellip", "rsquo", "lsquo", "ldquo",
            "rdquo", "eacute", "uuml", "sect", "para", "dagger", "permil")
# CLAIM A, cold lane, CONFIRMED and LATENT (0 occurrences in delivered pages).
# `#x?` matched `&amp;#x27;` and missed `&amp;#X27;`. Both decode identically in every
# HTML parser, so the uppercase form could have shipped a reader-visible literal past a
# gate that reported PASS. Fixed because the hole is real, not because it caught
# anything: the corpus currently carries zero doubly-encoded entities of either case.
PATTERN = re.compile(r"&amp;(?:#[xX]?[0-9a-fA-F]+|(?:%s));" % "|".join(ENTITIES))

# EVERY HIT IN THIS CORPUS TODAY IS INSIDE A <script>, AND ALL SIX ARE THE SAME LINE:
#
#     .replace(/&amp;mdash;/g, "&mdash;")
#
# The gate was matching the SEARCH PATTERN OF THE CODE THAT REPAIRS THE VERY THING THE
# GATE HUNTS. That is `a probe keyed to the string a fix removes` -- a shape on this
# project's own hunt list, and the cold lane that reviewed this file answered `No
# finding` for it. The reviewer read the checker and could not see the corpus; the
# corpus is where this one lives.
#
# The fix is NOT to drop script content. A string in a script CAN reach a reader -- if
# it is written into the DOM as text, `&amp;mdash;` renders literally. Whether a given
# occurrence does that is a judgement about the code, so the gate makes neither call:
# it FAILS on reader-visible markup and reports in-script occurrences separately as
# owed-a-read. Three states, not a quieter two.
SCRIPT = re.compile(r"<script\b.*?</script\s*>", re.S | re.I)


def _reader_visible(html):
    """The page with every script region blanked, LENGTH PRESERVED so offsets hold."""
    return SCRIPT.sub(lambda m: " " * len(m.group(0)), html)


def check(html):
    # CLAIM B, cold lane, CONFIRMED and LATENT (no caller passes a non-string).
    # `html or ""` turned 0, None and any non-text payload into an empty string and
    # returned PASS -- zero conflated with absent, and a checker that reports PASS on
    # input it never examined is the worst of the three possible answers. There is no
    # such caller today; there is also no reason for this function to be the one that
    # decides an unreadable payload is clean.
    if not isinstance(html, str):
        return ("REFUSED", "not text: %s" % type(html).__name__, [])
    visible = _reader_visible(html)
    hits = [m.group(0) for m in PATTERN.finditer(visible)]
    in_script = len(PATTERN.findall(html)) - len(hits)
    if not hits:
        if in_script:
            return ("NOTE",
                    "%d doubly-encoded entit%s inside <script> only -- not reader-visible "
                    "as markup, owed a read for whether the string reaches the DOM"
                    % (in_script, "y" if in_script == 1 else "ies"), [])
        return "PASS", "no doubly-encoded entity", []
    seen = {}
    for h in hits:
        seen[h] = seen.get(h, 0) + 1
    return ("FAIL",
            "%d doubly-encoded entit%s: %s" % (
                len(hits), "y" if len(hits) == 1 else "ies",
                ", ".join("%s x%d" % (k, v) for k, v in sorted(seen.items()))),
            hits)


def selftest() -> int:
    ok = True
    cases = [
        # The three real defects, as bytes.
        ("REPLAY 1 jump list: heading escaped twice",
         "<p class='toc'><a href='#x'>PARAGON-HF &amp;middot; PMID 314757</a></p>", "FAIL"),
        ("REPLAY 2 an apostrophe in a registry title",
         "<td>named in the page&amp;#x27;s include list</td>", "FAIL"),
        ("REPLAY 3 the em-dash fallback I wrote today",
         "<td>&amp;mdash;</td>", "FAIL"),
        # The same content, correct.
        ("correct: a real entity, encoded once",
         "<p>PARAGON-HF &middot; PMID 314757</p>", "PASS"),
        ("correct: a literal em dash character needs no entity",
         "<td>" + chr(8212) + "</td>", "PASS"),
        ("correct: an escaped ampersand in ordinary prose",
         "<p>AT&amp;T and Johnson &amp; Johnson</p>", "PASS"),
        # The false-alarm shape this pattern is deliberately narrowed against.
        ("NOT a hit: an escaped ampersand followed by a word and a semicolon",
         "<p>Smith &amp; Jones; then the others</p>", "PASS"),
    ]
    for label, html, want in cases:
        v, why, _ = check(html)
        good = v == want
        ok &= good
        print("  %-56s -> %-5s (want %-5s) %s"
              % (label[:56], v, want, "correct" if good else "WRONG"))
        if not good:
            print("        " + why)
    print("\nWHAT A FAILURE WOULD LOOK LIKE: any of the first three replays passing. Each "
          "is bytes taken from a page this project actually served.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] == "--selftest":
        return selftest()
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if sys.argv[1] == "--corpus":
        paths = sorted(glob.glob(os.path.join(repo, "*_REVIEW*.html")))
    else:
        paths = sys.argv[1:]
    bad, scanned, unreadable, noted = [], 0, [], []
    for p in paths:
        try:
            html = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            # CLAIM C, cold lane, CONFIRMED and LIVE. A NAMED PATH THAT CANNOT BE READ
            # WAS SKIPPED SILENTLY, and with every path unreadable the gate printed
            # `scanned 0 page(s)` and exited 0. A gate asked about a page it could not
            # open reported success about it.
            #
            # This is the shape already burned into this project once: a pre-push hook
            # that printed PASS at 0/1522 fully-ok. A check that cannot fail is not a
            # check. An unreadable path the caller NAMED is an error about the caller's
            # request, not an absence to route around.
            unreadable.append(p)
            continue
        scanned += 1
        v, why, _ = check(html)
        if v == "FAIL":
            bad.append((os.path.basename(p), why))
        elif v == "NOTE":
            noted.append((os.path.basename(p), why))
    for name, why in bad:
        print("  FAIL  %-52s %s" % (name[:52], why[:110]))
    if unreadable:
        print("\nREFUSED: %d named path(s) could not be read, so this gate has no"
              " answer about them:" % len(unreadable))
        for p in unreadable[:10]:
            print("    %s" % p)
        return 2
    for name, why in noted[:10]:
        print("  NOTE  %-52s %s" % (name[:52], why[:110]))
    if noted:
        print("  ...%d page(s) noted. NOTE is not PASS: it is `this gate cannot tell`,"
              " and it does not block." % len(noted))
    print("\nscanned %d page(s); %d carry a doubly-encoded entity" % (scanned, len(bad)))
    if scanned and not bad:
        print("-> PASS over %d pages. This says nothing about pages not scanned." % scanned)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
