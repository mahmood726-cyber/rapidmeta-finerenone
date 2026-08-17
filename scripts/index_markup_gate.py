"""INDEX MARKUP GATE -- is the root index's link tree well formed, and do its cards point at pages that exist?

WHY THIS EXISTS
    On 2026-08-17 the FINERENONE card was superseded and a new card added beside
    it. The edit rewrote the old card's <span class="pub"> text but never closed
    it, so the NEW card was emitted INSIDE the old card's anchor:

        <a href="FINERENONE_REVIEW.html" ...><span class="pub">Superseded ...
            <a href="FINERENONE_CV_REVIEW.html" ...>...</a></span></a>

    An <a> inside an <a> is not valid HTML and no two browsers repair it the same
    way. The root index is the definition of done -- the surface Mahmood actually
    checks -- and it shipped with the new card reachable only by accident.

    Worse than the defect: MY OWN VERIFICATION SAID "ABSENT" FOR THE OLD CARD AND
    I ALMOST REPORTED SUCCESS ANYWAY, because the regex for the new card happened
    to match the inner anchor. The check that found the new card was passing for
    a reason unrelated to correctness. That is the fifth instance this week of a
    check reporting success without having performed the check, and the reason
    this gate tests STRUCTURE (a stack of open anchors) rather than presence.

    The repo has carried a div-balance rule for large HTML apps since long before
    this. Nobody had attached the same idea to the index, which is the one file
    edited by hand on nearly every deploy.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the card TEXT is true. A perfectly nested card can quote an
      estimate that no longer matches the page; card_alignment_gate owns that,
      and this gate passing says nothing about it.
    - NOT that a page which SHOULD have a card has one. This walks the cards that
      exist; it cannot see a review that was never linked.
    - NOT that the linked page is correct, current, or non-superseded -- only
      that the file is there to be served.
    - NOT that the rest of the index's markup is valid. It checks anchor nesting
      and card->file resolution, not tables, headings or scripts.
"""
from __future__ import annotations
import os, re, sys, io

# Guarded: reassigning stdout AT IMPORT closes the caller's wrapper and the
# importer dies on "I/O operation on closed file" at its next print.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SSOT = r"F:\rapidmeta-ssot-shell"
ANCHOR = re.compile(r"<a\b[^>]*>|</a\s*>", re.I)
HREF = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.I)


SCRIPTY = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S)


def _markup_only(html):
    """Blank out <script>/<style> bodies, PRESERVING LENGTH so reported offsets
    still point into the real file. The index's own chip-injector contains the
    string '<a> inside <a>' in a comment explaining why it avoids exactly this
    defect -- and the first run of this gate flagged that comment as the defect.
    The repo's div-balance rule has always carried the same 'exclude JS' caveat;
    it had to be rediscovered here because the rule was prose, not code."""
    return SCRIPTY.sub(lambda m: " " * len(m.group(0)), html)


def nesting_faults(html):
    """-> list of (offset, href_of_inner, href_of_outer) for every <a> opened
    while another <a> is still open. Stack-based: a fragment test cannot see
    this, because each anchor is individually well formed."""
    stack, faults = [], []
    for m in ANCHOR.finditer(_markup_only(html)):
        tok = m.group(0)
        if tok.lower().startswith("</"):
            if stack:
                stack.pop()
        else:
            h = HREF.search(tok)
            href = h.group(1) if h else "(no href)"
            if stack:
                faults.append((m.start(), href, stack[-1]))
            stack.append(href)
    return faults, len(stack)


def dead_cards(html, root):
    """Card hrefs that resolve to no file on disk. Local targets only."""
    dead = []
    for m in re.finditer(r'<a\b[^>]*class\s*=\s*["\'][^"\']*\bcard\b[^"\']*["\'][^>]*>', html, re.I):
        h = HREF.search(m.group(0))
        if not h:
            continue
        u = h.group(1).split("#")[0].split("?")[0]
        if not u or u.startswith(("http", "mailto:", "data:", "//")):
            continue
        if not os.path.exists(os.path.join(root, u.replace("/", os.sep))):
            dead.append(u)
    return sorted(set(dead))


def check(path, root=None):
    root = root or os.path.dirname(os.path.abspath(path))
    html = open(path, encoding="utf-8", errors="replace").read()
    faults, unclosed = nesting_faults(html)
    dead = dead_cards(html, root)
    verdict = "FAIL" if (faults or unclosed or dead) else "PASS"
    return verdict, faults, unclosed, dead


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SSOT, "index.html")
    v, faults, unclosed, dead = check(path)
    print("%s" % os.path.basename(path))
    print("  nested anchors : %d" % len(faults))
    if len(faults) > 1:
        print("      (FIX THE FIRST ONE. A single unclosed anchor makes every card after it "
              "look nested; the rest of this list is cascade, not %d separate defects.)" % len(faults))
    for off, inner, outer in faults[:10]:
        print("      at %d  <a href=%s> opened inside <a href=%s>" % (off, inner, outer))
    print("  unclosed <a>   : %d" % unclosed)
    print("  dead card links: %d %s" % (len(dead), dead[:6] if dead else ""))
    print("  -> %s" % v)
    return 0 if v == "PASS" else 1


def selftest():
    """POSITIVE: the real 2026-08-17 defect, verbatim. NEGATIVE: the repaired
    index, and a card whose target genuinely exists."""
    ok = True
    BROKEN = ('<div class="grid">\n'
              '<a href="FINERENONE_REVIEW.html" class="card ckd"><span class="name">Finerenone (FIDELITY)'
              '</span><span class="pub">Superseded &mdash; rebuilt from source as '
              '<a href="FINERENONE_CV_REVIEW.html">Finerenone CV composite</a>\n'
              '<a href="FINERENONE_CV_REVIEW.html" class="card ckd"><span class="name">Finerenone CV'
              '</span><span class="pub">Published: HR 0.8655</span></a></span></a>\n</div>')
    faults, unclosed = nesting_faults(BROKEN)
    good = len(faults) == 2
    ok &= good
    print("  POSITIVE the real nested-card defect        -> %d nested anchor(s) %s"
          % (len(faults), "correct" if good else "WRONG (expected 2)"))
    for off, inner, outer in faults:
        print("        <a href=%s> inside <a href=%s>" % (inner, outer))

    # Written out in full, NOT derived from BROKEN by str.replace. Deriving it
    # was the first attempt and both replaces silently no-opped, so the negative
    # fixture was the positive fixture and the selftest "failed" for the wrong
    # reason. str.replace returns a copy whether or not it matched; a fixture
    # that can quietly become a duplicate of its own opposite proves nothing.
    REPAIRED = ('<div class="grid">\n'
                '<a href="FINERENONE_REVIEW.html" class="card ckd"><span class="name">Finerenone (FIDELITY)'
                '</span><span class="pub">Superseded &mdash; rebuilt from source as Finerenone CV composite'
                '</span></a>\n'
                '<a href="FINERENONE_CV_REVIEW.html" class="card ckd"><span class="name">Finerenone CV'
                '</span><span class="pub">Published: HR 0.8655</span></a>\n</div>')
    assert REPAIRED != BROKEN, "negative fixture is identical to the positive one"
    faults2, unclosed2 = nesting_faults(REPAIRED)
    good2 = not faults2
    ok &= good2
    print("  NEGATIVE the same cards, correctly closed   -> %d nested anchor(s) %s"
          % (len(faults2), "correct" if good2 else "WRONG"))

    live = os.path.join(SSOT, "index.html")
    if os.path.exists(live):
        v, f, u, d = check(live)
        ok &= v == "PASS"
        print("  NEGATIVE the live root index                -> %-4s %s"
              % (v, "correct" if v == "PASS" else "WRONG: nested=%d unclosed=%d dead=%s" % (len(f), u, d[:4])))

    print("\nWHAT A FAILURE WOULD LOOK LIKE: the nested-card defect passing, which is "
          "exactly what shipped to the root index and what my own presence-regex "
          "reported as fine; or the repaired index failing, because a gate nobody "
          "can satisfy gets bypassed and then rots.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
