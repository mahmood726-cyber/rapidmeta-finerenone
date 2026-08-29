# -*- coding: utf-8 -*-
"""SPLIT: a light main paper, and a downloadable appendix carrying everything else.

TWO PROBLEMS, ONE COMPONENT. A 7 MB page a phone in Dhaka cannot open, and a length that makes
a long review unreadable. Cochrane cannot easily do this because their format IS the document;
ours is generated, so the split is a rendering decision rather than an editorial one.

⛔ NOTHING IS REMOVED. Every section lands in exactly one of the two outputs and the split is
CHECKED, not asserted: a section that appears in neither, or in both, is a build refusal. That
is the difference between splitting a document and losing half of it -- and this project has
already shipped a "fix" that deleted the middle of a page because a pattern ran to the wrong
delimiter.

WHAT GOES IN THE MAIN PAPER. The question, the estimate, what it means in absolute terms, the
certainty, the harms, the recommendation, the limitations, and a link to the appendix. That is
what a clinician needs to act, and it is the part that must open on a metered connection.

WHAT GOES IN THE APPENDIX. The apparatus: audit trail, per-trial extraction, provenance,
integrity detail, method notes, and the figure downloads that are 81% of current page weight.

⚠️ AND THE INTEGRITY SECTION STAYS IN THE MAIN PAPER. It is content a reader and a judge weigh,
not apparatus -- moving it to an appendix would quietly undo standing orders §10 by relocation
rather than by deletion, which is exactly how a protection dies without anyone deciding to
remove it.
"""
import io
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))

# ⚠️ THIS CLASSIFIER IS WRONG FOR GENERATED PAGES AND THE FIX IS NOT MORE KEYWORDS.
#
# Measured on IV_IRON_HF_REVIEW: the split is structurally perfect -- 38 sections, every one in
# exactly one output, 7,080 KB down to a 134 KB main paper -- and CLINICALLY BACKWARDS. It sent
# "Time to a first cardiovascular death or hospitalisation for heart failure" and "Time to death
# from any cause" to the APPENDIX, and kept four sections headed only "Pooled result" in the
# main paper. A clinician would open the light page and find no named outcome.
#
# The cause is that this list was written against ONE hand-built page's vocabulary. Adding the
# generator's phrasings would fit it to a second instance and fail on the third. The right fix
# is to classify by SECTION ROLE emitted by the generator -- outcome, apparatus, provenance --
# rather than by heading text, which means a generator change and a role attribute per section.
# Recorded rather than patched, because patching keywords here is the bespoke trap in miniature.
#
# Section headings that belong in the main paper. Matched on the rendered heading text.
MAIN = [
    "the question", "what is actually being estimated", "included studies", "result",
    "absolute terms", "interval methods", "which counts were used", "risk of bias",
    "age", "safety", "clinician", "since these trials", "population",
    "follow-up", "limitations", "relation to previously published",
    "what was checked before this page was published",
]


def _sections(html):
    """Split on <h2>. Returns [(heading_text, html_chunk)] plus the preamble."""
    parts = re.split(r"(?i)(?=<h2[\s>])", html)
    out = []
    for chunk in parts:
        m = re.match(r"(?is)<h2[^>]*>(.*?)</h2>", chunk)
        head = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
        out.append((head, chunk))
    return out


def _is_main(head):
    h = head.lower()
    return any(k in h for k in MAIN)


def split(html):
    secs = _sections(html)
    main, appx = [], []
    for head, chunk in secs:
        if not head:                       # preamble: title, styles, stamp
            main.append(chunk)
            continue
        (main if _is_main(head) else appx).append(chunk)
    return "".join(main), "".join(appx), secs


def strip_raster_downloads(html):
    """Move the undisplayed PNG download links out of the main paper.

    They are 81% of page weight and no reader sees them: the figures on screen are inline SVG.
    The link is replaced by a pointer to the appendix rather than deleted, so the feature is
    relocated and not lost.
    """
    return re.sub(
        r'<a[^>]*download="[^"]*\.png"[^>]*href="data:image/png;base64,[A-Za-z0-9+/=]+"[^>]*>'
        r'(.*?)</a>',
        r'<span class="mono">\1 &mdash; in the appendix</span>', html, flags=re.S | re.I)


def check_complete(original, main, appx):
    """Every section in exactly one output. Refuses on a loss OR a duplication."""
    o = {h for h, _ in _sections(original) if h}
    m = {h for h, _ in _sections(main) if h}
    a = {h for h, _ in _sections(appx) if h}
    lost = o - (m | a)
    both = m & a
    return lost, both


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    src = sys.argv[1] if len(sys.argv) > 1 else "DAPIVIRINE_RING_PILOT_REVIEW.html"
    html = io.open(src, encoding="utf-8", errors="replace").read()
    m, a, secs = split(html)
    m_light = strip_raster_downloads(m)

    # ⛔ CHECK THE BYTES THAT ARE WRITTEN, NOT THE ONES BEFORE THE LAST TRANSFORM.
    #
    # This read `check_complete(html, m, a)` while line below writes `m_light` --
    # strip_raster_downloads() runs in between. The completeness guarantee, which is the whole
    # reason this component is allowed to split a document at all, was being made about a string
    # that is not the one delivered.
    #
    # Harmless as it happens: the transform replaces <a download> anchors and cannot remove an
    # <h2>. That is luck, not design, and it is exactly the shape that put a dateless quotation
    # on the page tonight -- a check on the sentence, a render of sentence[:300].
    lost, both = check_complete(html, m_light, a)
    print("")
    print("SPLIT -- %s" % os.path.basename(src))
    print("  sections found                    %3d" % len([h for h, _ in secs if h]))
    print("  in the main paper                 %3d" % len([h for h, _ in _sections(m) if h]))
    print("  in the appendix                   %3d" % len([h for h, _ in _sections(a) if h]))
    print("")
    if lost or both:
        print("  REFUSED: sections lost %s ; in both %s" % (sorted(lost)[:3], sorted(both)[:3]))
        return 2
    print("  every section in exactly one output   [PASS]")
    print("")
    print("  original          %8.1f KB" % (len(html.encode("utf-8")) / 1000))
    print("  main paper        %8.1f KB" % (len(m.encode("utf-8")) / 1000))
    print("  main, raster out  %8.1f KB" % (len(m_light.encode("utf-8")) / 1000))
    print("  appendix          %8.1f KB" % (len(a.encode("utf-8")) / 1000))
    band = ("green" if len(m_light.encode("utf-8")) < 500_000
            else "amber" if len(m_light.encode("utf-8")) < 2_000_000 else "red")
    print("  main paper band   %8s" % band)
    print("")
    print("  in the appendix:")
    for h, _ in _sections(a):
        if h:
            print("     %s" % h[:70])
    # ⛔ A GENERIC NAME IN A SHARED ROOT IS A COLLISION WAITING FOR A SECOND LANE.
    #
    # This wrote split_main.html and split_appendix.html into the shared scratch root -- two
    # names so generic that any other lane splitting any other document overwrites them, with no
    # error. It is the same class that made the regeneration test order-dependent tonight, where
    # one shared regen_test.html meant each topic was compared against the previous topic's page
    # and dapivirine REFUSED TO BUILD depending on what ran before it.
    #
    # Gate 9 caught this one. It also mis-attributed it: the ratchet is keyed on file:line, so
    # inserting a comment above the path retired "line 140" and reported "line 150" as NEW. The
    # instance was real either way, so it is removed rather than re-frozen -- names now derive
    # from the input document, under a directory the caller may name.
    out = (sys.argv[2] if len(sys.argv) > 2
           else os.environ.get("ROB_SPLIT_OUT") or tempfile.mkdtemp(prefix="rob_split_"))
    os.makedirs(out, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]", "_", os.path.splitext(os.path.basename(src))[0])[:60]
    mp = os.path.join(out, stem + ".main.html")
    ap = os.path.join(out, stem + ".appendix.html")
    io.open(mp, "w", encoding="utf-8").write(m_light)
    io.open(ap, "w", encoding="utf-8").write(a)
    print("")
    print("  -> %s" % mp)
    print("  -> %s" % ap)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
