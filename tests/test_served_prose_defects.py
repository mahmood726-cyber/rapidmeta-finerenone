# -*- coding: utf-8 -*-
"""FIVE FIXTURES for the reader-facing defects a HUMAN found on the served empagliflozin page while
the census reported `prose clean`. Proven to FAIL on the live bytes as promoted and PASS once fixed.

THE CHECK LOGIC LIVES IN ONE PLACE: scripts/served_prose_checks.py, imported here AND by the census AND
by gates/gate_served_prose.py. An earlier draft of this file kept its OWN copy of the patterns; the copy
drifted (it still flagged 'substantively identical' and bare 'REML', the very corrections the fix
introduced) and reported false defects on a clean page. Two definitions of one check is the drift this
project keeps paying for -- there is now exactly one.

pytest: test_live_page_has_all_five (xfail unless the recorded live snapshot exists) + a self-test that
the checks fire on a synthetic all-defect page and stay silent on a clean one.
Run directly:  python tests/test_served_prose_defects.py <page.html>   (exit 1 if any defect present)
"""
from __future__ import annotations
import io, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import served_prose_checks as C  # noqa: E402

# the synthetic page carrying every defect, and a clean one -- permanent controls (not the live page,
# which is fixed once promoted; a control anchored to a live defect retires when the defect is fixed).
_POS = ("<h2>Comparison</h2><p>the earlier claim that no synthesis pools these</p>"
        "<ul><li><strong>machine readable:</strong> {&#x27;hf&#x27;: {&#x27;hr&#x27;: 0.7}, &#x27;_why_this_is_here&#x27;: &#x27;x&#x27;}</li></ul>"
        "<p>verified word for word against both registrations.</p>"
        "<p>tau-squared 0.0 under REML while fixed-effect inverse-variance is served.</p>"
        "<h2>Screening and search</h2><h2>Screening</h2>")
_NEG = ("<h2>Comparison</h2><p>The two registered titles are substantively identical, differing only by "
        "the word 'the'.</p><ul><li><strong>HF hospitalisation:</strong> HR 0.70</li></ul>"
        "<p>tau-squared 0.0; the pool is fixed-effect inverse-variance on the log scale, and the "
        "random-effect (REML) and fixed-effect estimates coincide.</p><h2>Screening</h2>")


def test_checks_fire_on_synthetic_defect_page():
    fired = {lab for lab, _ in C.scan(_POS)}
    assert len(fired) == len(C.CHECKS), "a check did not fire on the synthetic all-defect page: %s" % fired


def test_checks_silent_on_clean_page():
    assert C.scan(_NEG) == [], "a check false-fired on the clean page: %s" % C.scan(_NEG)


def test_live_snapshot_had_all_five():
    """If the recorded live snapshot is present, it MUST show all five (it is the defect record)."""
    snap = os.path.join(ROOT, "tests", "fixtures", "empag_live_defective_2026_09_08.html")
    if not os.path.exists(snap):
        import pytest
        pytest.skip("live defect snapshot not recorded")
    fired = {lab for lab, _ in C.scan(io.open(snap, encoding="utf-8", errors="replace").read())}
    assert len(fired) == len(C.CHECKS), "the recorded live page must exhibit all five defects: %s" % fired


def run(page):
    html = io.open(page, encoding="utf-8", errors="replace").read()
    res = C.scan(html)
    print("SERVED-PROSE DEFECT FIXTURES -- %s" % page)
    for label, _fn in C.CHECKS:
        hits = next((h for lab, h in res if lab == label), [])
        print("  [%s] %s" % ("DEFECT" if hits else "clean ", label))
        for h in hits[:4]:
            print("        -> %r" % (h,))
    total = sum(len(h) for _, h in res)
    print(">>> %d defect instance(s). %s <<<" % (total, "FAIL" if total else "PASS"))
    return 1 if total else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    page = sys.argv[1] if sys.argv[1:] else os.path.join(ROOT, "preview", "EMPAGLIFLOZIN-HF-AUTO-FULL-REVIEW.html")
    sys.exit(run(page))
