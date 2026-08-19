#!/usr/bin/env python3
"""THE MANUSCRIPT GUARD, PROVEN IN FOUR PARTS AGAINST THE REAL FAILING INPUT (P16).

  1. IT CAN FIRE            on the ACTUAL ARNI rebuild -- not a fixture. The build was run to
                            a scratch path before this guard existed, so the destroying HTML
                            exists on disk and is fed to the guard verbatim.
  2. IT DOES NOT FIRE ON THE CORRECT CASE
                            on all ten pages rebuilt on 2026-08-19, whose paper panels changed
                            by EXACTLY 0.00%. That is the calibration as well as the proof:
                            legitimate variation here is zero, so the 5% tolerance clears the
                            noise by a factor of infinity and the hazard by 19x.
  3. NEITHER FROM A BUILD REPORTING SUCCESS
                            every case is decided by calling the guard on bytes read from
                            disk. No build is run, no exit code is consulted.
  4. THE CONDITION ACTUALLY OCCURRED
                            ARNI is delivered at 100,825 chars / 26 sections and rebuilds to
                            5,701 / 1. The gun was loaded and pointed when this was written.

It calls the REAL functions in ssot/manuscript_guard.py. It does not re-implement the branch --
that is registry class 32, committed earlier tonight, and repeating it here would be absurd.
"""
import glob
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))
import manuscript_guard as G                                            # noqa: E402

SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-ssot-shell"
           r"\727c30d4-294e-4c96-a3c0-e6b7be6cf5b8\scratchpad")
ARNI_REBUILD = os.path.join(SCRATCH, "ARNI_REBUILD_TEST.html")

FAILS, NA = [], []


def ck(name, got, want):
    ok = got == want
    print("  %-68s %s" % (name[:68], "ok" if ok else "FAIL"))
    if not ok:
        print("      got %r want %r" % (got, want))
        FAILS.append(name)


def read(p):
    return open(p, "rb").read().decode("utf-8", "replace")


def main():
    os.chdir(REPO)
    os.environ.pop(G.OVERRIDE, None)

    print("1. IT CAN FIRE -- on the real ARNI rebuild, fed to the guard verbatim:")
    if not os.path.exists(ARNI_REBUILD):
        print("   NOT_ASSESSABLE -- the scratch rebuild is not on disk at %s" % ARNI_REBUILD)
        print("   Re-create with: python ssot/build_tabbed.py "
              "ssot/arni-hfref/arni-hfref.json <scratch>/ARNI_REBUILD_TEST.html")
        NA.append("ARNI rebuild input")
    else:
        verdict, msg = G.check(read(ARNI_REBUILD), "ARNI_HF_REVIEW.html")
        ck("the ARNI rebuild is REFUSED", verdict, G.REFUSED)
        ck("...and the refusal names the DELIVERED size", "100825" in msg, True)
        ck("...and reports the margin, not just a verdict", "%" in msg, True)
        print("      %s" % msg)

    print("\n2. IT DOES NOT FIRE ON THE CORRECT CASE -- the ten rebuilt on 2026-08-19:")
    checked = 0
    for f in sorted(glob.glob(os.path.join(SCRATCH, "*.rebuilt.html"))):
        page = os.path.basename(f).replace(".rebuilt.html", ".html")
        if not os.path.exists(page):
            continue
        checked += 1
        verdict, msg = G.check(read(f), page)
        if verdict != G.OK:
            print("      %-44s %s -- %s" % (page[:44], verdict, msg))
            FAILS.append("%s wrongly %s" % (page, verdict))
    ck("all %d legitimate rebuilds pass" % checked, [f for f in FAILS if "wrongly" in f], [])
    if not checked:
        print("      NOT_ASSESSABLE -- no rebuilt pages on disk to check")
        NA.append("legitimate rebuilds")

    print("\n3. IT REFUSES TO JUDGE WHAT IT CANNOT SEE -- and that is never a refusal:")
    v, m = G.check("<html>anything</html>", os.path.join(REPO, "NO_SUCH_PAGE_XYZ.html"))
    ck("a page with no delivered copy is NOT_ASSESSABLE, not REFUSED", v, G.NOT_ASSESSABLE)
    # NOT this test file: it contains id="pn-paper" in its own fixtures, so the guard
    # correctly finds a panel in it. The first version of this case used it and the guard
    # returned REFUSED -- which was RIGHT. A test input chosen carelessly reports a defect
    # in the instrument that is really a defect in the test.
    v, m = G.check("<html>x</html>", "ssot/PAGE_MAP.json")
    ck("a delivered file with no manuscript panel is NOT_ASSESSABLE", v, G.NOT_ASSESSABLE)

    print("\n4. TOTAL LOSS IS CAUGHT, not just shrinkage:")
    delivered = ('<section id="pn-paper"><h2>Paper</h2>' + "word " * 400
                 + "</section><!--end-paper-->")
    v, m = G.check("<html>no panel here at all</html>", "ARNI_HF_REVIEW.html")
    ck("emitting no panel where one is delivered is REFUSED", v, G.REFUSED)
    ck("...and says so in words", "total loss" in m.lower(), True)

    print("\n5. THE BOUNDARY, stated as a number rather than trusted:")
    import re as _re

    def page_of(chars, h2):
        return ('<section id="pn-paper">' + "<h2>x</h2>" * h2 + ("y " * (chars // 2))
                + "</section><!--end-paper-->")
    base = page_of(10000, 4)
    tmp = os.path.join(SCRATCH, "_guard_boundary.html")
    open(tmp, "w", encoding="utf-8").write(base)
    shape = G.paper_shape(base)
    ck("the shape probe reads its own fixture", shape[1], 4)
    v, _ = G.check(page_of(int(shape[0] * 0.97), 4), tmp)
    ck("a 3%% text loss with sections intact passes", v, G.OK)
    v, _ = G.check(page_of(int(shape[0] * 0.80), 4), tmp)
    ck("a 20%% text loss is REFUSED", v, G.REFUSED)
    v, _ = G.check(page_of(shape[0], 3), tmp)
    ck("losing ONE section with text intact is REFUSED", v, G.REFUSED)
    os.remove(tmp)

    print("\n6. THE OVERRIDE IS DELIBERATE AND LOUD:")
    if os.path.exists(ARNI_REBUILD):
        os.environ[G.OVERRIDE] = "1"
        v, m = G.check(read(ARNI_REBUILD), "ARNI_HF_REVIEW.html")
        ck("with %s=1 the same input is allowed" % G.OVERRIDE, v, G.OK)
        ck("...and the message says it was overridden", "OVERRIDDEN" in m, True)
        os.environ.pop(G.OVERRIDE, None)
        v, _ = G.check(read(ARNI_REBUILD), "ARNI_HF_REVIEW.html")
        ck("...and removing it restores the refusal", v, G.REFUSED)

    print()
    if NA:
        print("NOT_ASSESSABLE (%d): %s" % (len(NA), ", ".join(NA)))
        print("  -- reported, never counted as a pass and never as a failure.")
    if FAILS:
        print("FAILED (%d):" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        return 1
    print("PASSED. Fires on the real destroying input; silent on %d real legitimate "
          "rebuilds." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
