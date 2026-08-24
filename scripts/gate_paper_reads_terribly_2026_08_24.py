"""BLOCK a page whose prose is empty, circular, or about another topic.

WHY THIS EXISTS, AND WHY THE EXISTING LINT IS NOT IT. `lint_paper_reads_as_prose.py`
measures MACHINE VOCABULARY -- field paths, snake_case, bare NCTs, raw statistics -- and it
does that well. It scored the delivered POSACONAZOLE page at 16% and passed every one of
the sentences Mahmood actually bounced off, because those sentences are well-formed
English. Six rounds of "fixed" were reported against an instrument that cannot express this
defect. That is the recurrence, and a new instrument is the only thing that closes it.

THE DIFFERENCE IN ONE LINE. That lint asks "does this read like a machine wrote it?"
This one asks "does this sentence say anything, and is it about this topic?"

FIVE BLOCKING CLASSES, each taken from a sentence on the delivered page.

  EMPTY_REFUSAL        `<strong>Refused:</strong>` with no subject after it. This project's
                       contract with a reader is that an absent section is named. A refusal
                       naming nothing breaks that promise while looking like it keeps it.
                       Rendered twice on each of 145 pages.

  HOLLOW_NOUN          a declared placeholder standing where a reader expects a name --
                       "the clinical quantity this page pools" as an OUTCOME NAME, spliced
                       by the projector into 22 slots on one page including two figure
                       legends and the Summary of Findings.

  CIRCULAR             a sentence whose complement repeats its subject: "The outcome sought
                       is the clinical quantity this page pools." Says the outcome is the
                       outcome. Grammatical, and empty.

  VERDICT_AS_TITLE     an audit verdict in the <title>, the H1 or the review-question slot
                       -- "Posaconazole Fungal: NOT POOLABLE -- no registration declares a
                       clinical endpoint at any rank". The verdict is true and belongs in
                       Results, which already carries it. In the title it destroys the
                       page's identity for every reader, starting with the browser tab.

  FOREIGN_TOPIC        a worked example written about one topic emitted onto another's
                       page. A reader of the POSACONAZOLE antifungal page met patisiran,
                       vutrisiran and eplontersen -- three transthyretin-amyloidosis drugs
                       -- in its Summary of Findings, on 123 pages.

CONTROLS RUN FIRST AND THE GATE REFUSES TO REPORT WITHOUT THEM. A guard that cannot fail
is verification theatre, and this repo has shipped one: a pre-push hook that printed
"Regression check PASS" at 0/1522 fully-ok. Each class below is proved against a fragment
that MUST trip it and a fragment that MUST NOT, and a control mismatch is a hard exit
before a single page is read.

TWO KNOWN FALSE-POSITIVE MODES, CONSTRUCTED BY AN ADVERSARIAL PASS AND KEPT ON PURPOSE.
A page that DISCUSSES this vocabulary rather than using it will block: a sentence quoting
"the clinical quantity this page pools" to explain the defect trips HOLLOW_NOUN, and a
sentence saying "unlike attr-pn-review, this review does not combine patisiran against its
own saline placebo" trips FOREIGN_TOPIC. Both are accepted, because no delivered systematic
review should be discussing this generator's placeholder vocabulary -- if one ever does, it
is a page worth a human look. Narrowing either check to avoid them would cost false
negatives on the defect itself, and a missed defect is what six rounds of this already cost.

Exit 1 on any BLOCK. That is the point of it.
"""
import io
import os
import re
import sys
import glob
import html as htmllib

# GUARDED, AND THE GUARD IS THE POINT. Reassigning sys.stdout at module level closes the
# buffer the IMPORTER already wrapped, so any script that imports this gate dies at its
# first print with "I/O operation on closed file" -- which is exactly how the rebuild driver
# failed on its first run. Wrapping only under __main__ keeps the UTF-8 console fix for
# direct invocation and leaves an importer's stdout alone.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------------------
# Declared vocabularies. Enumerated, never inferred -- same discipline as the topic synonym
# sets: what is listed is checked, and anything not listed passes rather than being guessed
# at. A false BLOCK costs more trust than a missed one, because it teaches bypassing.
# ---------------------------------------------------------------------------------------
HOLLOW_NOUNS = (
    "the clinical quantity this page pools",
    "the quantity this page pools",
    "the outcome this page reports",
    "the clinical outcome of interest",
)

VERDICT_IN_TITLE = re.compile(
    r"\b(NOT POOLABLE|NOT ESTABLISHED|NOT ASSESSABLE|NOT COMPARABLE)\b", re.I)

# A topic-specific worked example that must not appear on a page that is not about it.
FOREIGN_EXAMPLES = (
    ("attr-pn-review", re.compile(
        r"patisiran against its own saline placebo", re.I)),
)

# AN ABSENCE MARKER SPLICED INTO A SENTENCE. Acceptable standing alone in its own table
# cell -- a reader understands "not recorded" there. A defect when a sentence is composed
# AROUND it, because the sentence then asserts something the marker means was never
# recorded. Anchored on a preceding lower-case word or comma so a marker that opens its own
# cell or sentence is left alone: that is the whole distinction, and 366 legitimate own-slot
# uses depend on it.
SENTINEL_SPLICE = re.compile(
    r"[a-z0-9,;:.)\]–—-][\x20\u00a0]*(?:not recorded|not available|not stated|no record|"
    r"not established|not captured)[\x20\u00a0]+on the page this object was "
    r"(?:extracted|built) from", re.I)

EMPTY_REFUSAL = re.compile(r"<strong>\s*Refused:\s*</strong>(?:\s|&nbsp;|&#160;| )*"
                           r"(?:<sup[^>]*>.*?</sup>)?(?:\s|&nbsp;|&#160;| )*"
                           r"(?:</div>|<)", re.I)

# "The outcome sought is the clinical quantity this page pools." The circularity is NOT a
# repeated noun -- the two nouns differ -- it is that the COMPLEMENT names the page instead
# of naming a thing. The first draft of this pattern required the same noun on both sides,
# and its own control caught it passing the exact sentence it was written for. That is what
# the negative-and-positive control pair is for, and it earned its place on the first run.
CIRCULAR = re.compile(
    r"\bThe\s+(?:outcome|quantity|endpoint|estimand)\b[^.]{0,40}?\bis\s+the\b"
    r"[^.]{0,60}?\bthis\s+(?:page|review)\s+(?:pools|reports|analyses|analyzes)\b", re.I)


def visible_text(html):
    h = re.sub(r"(?is)<(script|style|svg)\b.*?</\1>", " ", html)
    h = re.sub(r"(?is)<!--.*?-->", " ", h)
    h = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|section|td|th)>", "\n", h)
    return re.sub(r"[ \t]+", " ", htmllib.unescape(re.sub(r"(?s)<[^>]+>", " ", h)))


def head_slots(html):
    """The three slots a reader meets first: browser tab, H1, review-question row."""
    slots = []
    m = re.search(r"(?is)<title>(.*?)</title>", html)
    if m:
        slots.append(("title", htmllib.unescape(m.group(1)).strip()))
    m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", html)
    if m:
        slots.append(("h1", htmllib.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).strip()))
    m = re.search(r"(?is)Review question \(PICO\)</th><td>(.*?)</td>", html)
    if m:
        slots.append(("review-question",
                      htmllib.unescape(re.sub(r"<[^>]+>", " ", m.group(1))).strip()))
    return slots


def slugs_of(page_name):
    """The slug tokens a delivered page belongs to, as a SET.

    A REAL COLLECTION, NOT A STRING. This took a bare string until the pre-commit linter
    `lint_string_where_collection_expected.py` refused the commit and named the exact call
    site. It was right: `owner in "attr-pn-review-page.html"` is a SUBSTRING test, so a
    one-character owner would have matched everything and an owner that merely appears
    inside a longer topic name would have silently suppressed a real finding. Exact set
    membership cannot fail in either direction.
    """
    stem = os.path.splitext(os.path.basename(page_name))[0].lower().replace("_", "-")
    return {stem, stem.replace("-auto-full-review", "").replace("-review", "")}


def findings_for(path, html, page_slugs):
    out = []
    text = visible_text(html)

    n = len(EMPTY_REFUSAL.findall(html))
    if n:
        out.append(("EMPTY_REFUSAL", "%d refusal(s) naming nothing" % n))

    for hollow in HOLLOW_NOUNS:
        c = len(re.findall(re.escape(hollow), text, re.I))
        if c:
            out.append(("HOLLOW_NOUN", "%r x%d" % (hollow, c)))

    n = len(SENTINEL_SPLICE.findall(text))
    if n:
        m2 = SENTINEL_SPLICE.search(text)
        out.append(("SENTINEL_SPLICE", "x%d, e.g. %r"
                    % (n, re.sub(r"\s+", " ", text[max(0, m2.start() - 70):m2.end()])[-110:])))

    m = CIRCULAR.search(text)
    if m:
        out.append(("CIRCULAR", re.sub(r"\s+", " ", m.group(0))[:110]))

    for slot, val in head_slots(html):
        if VERDICT_IN_TITLE.search(val):
            out.append(("VERDICT_AS_TITLE", "%s: %s" % (slot, val[:100])))

    for owner, rx in FOREIGN_EXAMPLES:
        if owner in page_slugs:
            continue                      # the page it was written about may carry it
        if rx.search(text):
            out.append(("FOREIGN_TOPIC", "carries the %s worked example" % owner))
    return out


# ---------------------------------------------------------------------------------------
# CONTROLS. Every class proved able to fire AND able to stay quiet, before any page is read.
# ---------------------------------------------------------------------------------------
CONTROLS = (
    ("EMPTY_REFUSAL", True,
     "<div class='absent-state'><strong>Refused:</strong> <sup>1</sup></div>"),
    ("EMPTY_REFUSAL", False,
     "<div class='absent-state'><strong>Refused:</strong> the keyword list<sup>1</sup></div>"),
    # An entity rather than a space is still an empty refusal to a reader.
    ("EMPTY_REFUSAL", True,
     "<div class='absent-state'><strong>Refused:</strong>&nbsp;<sup>1</sup></div>"),
    ("HOLLOW_NOUN", True,
     "<p>Figure 1. Forest plot -- the clinical quantity this page pools.</p>"),
    ("HOLLOW_NOUN", False,
     "<p>Figure 1. Forest plot -- all-cause mortality at 12 months.</p>"),
    ("CIRCULAR", True,
     "<p>The outcome sought is the clinical quantity this page pools.</p>"),
    ("CIRCULAR", False,
     "<p>The outcome sought is the quantity this review was asked to pool.</p>"),
    ("VERDICT_AS_TITLE", True,
     "<title>Posaconazole Fungal: NOT POOLABLE -- no registration declares an endpoint</title>"),
    ("VERDICT_AS_TITLE", False,
     "<title>Posaconazole in invasive fungal prophylaxis</title>"),
    ("SENTINEL_SPLICE", True,
     "<p>It identifies no trial that can be pooled, against not recorded on the page "
     "this object was extracted from.</p>"),
    # THE COLON-PREFIXED FORM. An adversarial pass constructed this and then found 72 of
    # them live on 38 delivered pages; the first pattern anchored on `[a-z,]` and saw none.
    ("SENTINEL_SPLICE", True,
     "<p>Known limitation of the screen: not recorded on the page this object was "
     "extracted from</p>"),
    # USE vs MENTION. ROSUVASTATIN legitimately QUOTES the marker while explaining that
    # "checked and failed" is a different state from "never recorded" -- a true and useful
    # distinction -- and an earlier separator class that included quote characters blocked
    # the page for saying it. A gate that blocks a correct page is a gate people learn to
    # bypass, so the quote characters came back out and this is the control that keeps them
    # out. The bypass they were added for was enumerated but never observed; this false
    # positive was observed.
    ("SENTINEL_SPLICE", False,
     "<p>Checked on 2026-08-20 and failed, which is a different state from the "
     "'not recorded on the page this object was extracted from' this object carries.</p>"),
    ("SENTINEL_SPLICE", False,
     "<td>not recorded on the page this object was extracted from</td>"),
    # THE FALSE POSITIVE THE FIRST DRAFT PRODUCED, KEPT AS A CONTROL. A header cell and its
    # value cell are adjacent in the markup; strip the tags and "Comparator" runs straight
    # into the marker on the next line. The first pattern used `\s+`, which matches a
    # NEWLINE, so it read six own-slot table rows as spliced sentences on one page. It now
    # requires a literal space, so a cell boundary breaks the match and only prose matches.
    ("SENTINEL_SPLICE", False,
     "<tr><th>Comparator</th><td>not recorded on the page this object was extracted from"
     "</td></tr>"),
    ("FOREIGN_TOPIC", True,
     "<p>the pool combines patisiran against its own saline placebo, and more.</p>"),
    ("FOREIGN_TOPIC", False,
     "<p>the pool combines two azole regimens against standard therapy.</p>"),
)


def run_controls():
    ok = True
    for cls, must_fire, fragment in CONTROLS:
        fired = any(c == cls for c, _ in findings_for("<control>", fragment, {"control-topic"}))
        if fired != must_fire:
            print("  CONTROL FAILED  %-18s expected fire=%s, got %s"
                  % (cls, must_fire, fired))
            ok = False
    print("  controls: %d checks, %s" % (len(CONTROLS), "all held" if ok else "FAILED"))
    return ok


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("-")]
    pages = argv or sorted(glob.glob(os.path.join(REPO, "*_REVIEW.html")))
    print("gate_paper_reads_terribly -- controls first")
    if not run_controls():
        print("\nCONTROLS FAILED. The gate is not trustworthy; no page was judged.")
        return 2

    blocked = {}
    for p in pages:
        try:
            html = open(p, encoding="utf-8", errors="replace").read()
        except Exception as exc:
            print("  unreadable %s: %s" % (p, exc))
            continue
        f = findings_for(p, html, slugs_of(p))
        if f:
            blocked[os.path.basename(p)] = f

    print("\npages read: %d   pages BLOCKED: %d" % (len(pages), len(blocked)))
    by_class = {}
    for name, fs in blocked.items():
        for cls, _ in fs:
            by_class[cls] = by_class.get(cls, 0) + 1
    for cls in sorted(by_class):
        print("    %-18s %d page(s)" % (cls, by_class[cls]))
    for name in sorted(blocked)[:40]:
        print("\n  %s" % name)
        for cls, detail in blocked[name]:
            print("      %-18s %s" % (cls, detail))
    if len(blocked) > 40:
        print("\n  ... and %d more blocked pages not listed." % (len(blocked) - 40))
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
