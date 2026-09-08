# -*- coding: utf-8 -*-
"""GATE: a served page must carry none of the five reader-facing prose defects a HUMAN found on the
promoted empagliflozin page while the census reported `prose clean`.

The census missed them because its check searched html-escaped bytes with an unescaped pattern (a dict
repr rendered as {&#x27;k&#x27;:...} never matched a literal-quote regex) and its truncation test was a
hardcoded snapshot of one past string. Those were never checks. This gate uses the canonical
served_prose_checks (tag-strip + html.unescape) and is DISCOVERED by clearance automatically (its
gate_ prefix), so it participates in every page's promotion without being hand-listed.

Given a page path (argv[1], as clearance passes), it fires on that page. With no arg it scans every
generated page. Controls are synthetic and permanent so they cannot retire when the live defect is fixed.
"""
from __future__ import annotations
import io, os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H            # noqa: E402
import served_prose_checks as C  # noqa: E402

# synthetic controls: one page carrying every defect, one clean. Permanent (not the live page).
_POS = ("<h2>Comparison</h2><p>the earlier claim that no synthesis pools these</p>"
        "<ul><li><strong>machine readable:</strong> {&#x27;hf&#x27;: {&#x27;hr&#x27;: 0.7}, &#x27;_why_this_is_here&#x27;: &#x27;x&#x27;}</li></ul>"
        "<p>verified word for word against both registrations.</p>"
        "<p>tau-squared 0.0 under REML while fixed-effect inverse-variance is served.</p>"
        "<h2>Screening and search</h2><h2>Screening</h2>")
_NEG = ("<h2>Comparison</h2><p>The two registered titles are substantively identical, differing only by "
        "the word 'the'.</p><ul><li><strong>HF hospitalisation:</strong> HR 0.70</li></ul>"
        "<p>tau-squared 0.0; the pool is fixed-effect inverse-variance on the log scale.</p>"
        "<h2>Screening and search</h2>")


def main(argv):
    gate = H.Gate("SERVED PROSE HAS NO READER-FACING DEFECT",
                  "no truncated clause, dict repr, false 'word for word', method mismatch, or duplicate absence block")
    named = gate.expect_case("__synthetic_all_five_defects__", "a page carrying all five defects must fire")
    gate.requires_control()
    pos_fires = bool(C.scan(_POS))
    neg_clean = not C.scan(_NEG)
    if pos_fires:
        gate.saw(named)
    gate.control(1, 0 if neg_clean else 1, [] if neg_clean else ["clean synthetic page flagged"], accuses=True)
    if not pos_fires:
        gate.broken("positive control did not fire -- the checks themselves are inert")

    pages = [argv[0]] if argv else sorted(
        glob.glob(os.path.join(H.repo_root(), "out", "generated", "*.html")) +
        glob.glob(os.path.join(H.repo_root(), "preview", "*.html")))
    n = 0
    for p in pages:
        if not os.path.exists(p):
            continue
        n += 1
        html = io.open(p, encoding="utf-8", errors="replace").read()
        for label, hits in C.scan(html):
            gate.finding(os.path.basename(p), "%s -- e.g. %r" % (label, hits[0]))
    gate.kinds({"pages scanned": n, "defect classes": len(C.CHECKS)})
    gate.coverage(n, n, "every scanned page read as a reader sees it (unescaped)")
    return gate.report(denominator="%d page(s)" % n)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
