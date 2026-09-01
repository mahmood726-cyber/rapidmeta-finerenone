# -*- coding: utf-8 -*-
"""PLANT: prove the published-correction guard fires, and that it is CALLED.

⛔ THE NAMED POSITIVE IS SYNTHETIC, AND THE FIRST VERSION OF THIS FILE GOT THAT
WRONG. It picked a real page carrying a real correction --
ABLATION_AF_HEART_FAILURE_REVIEW.html -- and asserted the guard fired on it.

    A CONTROL ANCHORED TO A LIVE DEFECT RETIRES ITSELF THE MOMENT THE DEFECT IS
    FIXED, AND THEN PASSES FOREVER LOOKING HEALTHY.

Reword that page's correction, or repin its must_render, and the control either
selects a different page silently or stops testing anything -- while still
printing PASS. The same class was proven twice in this project already: a
control keyed to a live artefact is correct locally, meaningless later, and
silent about the difference.

So the case that DECIDES the verdict is built in memory: a synthetic page, a
synthetic corrections entry, and a sentence that exists nowhere else. It cannot
be fixed out from under the test, and it cannot pass for the wrong reason.

A live page is still exercised afterwards -- but as a SMOKE CHECK that is
reported and cannot make the plant pass. If it stops finding a qualifying page,
that is printed as a fact about the corpus, not swallowed.

FIVE ASSERTIONS

  1 SYNTHETIC: the guard passes a page whose pinned sentence is present
  2 SYNTHETIC: the guard REFUSES the same page with that sentence removed,
    naming the page and quoting the correction
  3 SYNTHETIC: a page whose correction could not be pinned is refused outright
  4 an absent list refuses -- an absent list is not an empty list
  5 the guard is WIRED: build_tabbed.py calls it immediately before the write

⭐ NOTHING ON DISK IS TOUCHED. The planted defect is made in memory, so there is
no restore to get wrong -- and a restore verified by anything short of a byte
comparison is how a test leaves damage behind.

    python scripts/plant_correction_survives_rebuild.py
"""
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "ssot"))

PROTECTED = {"BEMPEDOIC_ACID_REVIEW.html", "CANGRELOR_PCI_REVIEW.html",
             "INCRETIN_HFpEF_REVIEW.html", "ARNI_HF_REVIEW.html"}

# A sentence that exists in no delivered page, so a false pass is impossible.
SENTINEL = ("__CONTROL__ an earlier version of this synthetic page reported a "
            "pooled estimate that was never real, and this sentence is the only "
            "place it is recorded __CONTROL__")

SYNTH_PAGE = "__SYNTHETIC_CORRECTION_CONTROL__.html"
SYNTH_HTML = ("<style>x</style><section class='panel' id='pn-protocol'>"
              "<p>%s</p></section>" % SENTINEL)
SYNTH_UNPINNABLE = "__SYNTHETIC_UNPINNABLE_CONTROL__.html"


def _list_with(entries):
    """Write a corrections list containing exactly the given entries."""
    fd, path = tempfile.mkstemp(suffix=".json", prefix="plant_corrections_")
    os.close(fd)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"pages": entries}, ensure_ascii=False, indent=1))
    return path


def live_smoke(dnr, out):
    """Exercise a real page too -- reported, never decisive."""
    p = os.path.join(ROOT, "scripts", "baselines", "published_corrections.json")
    if not os.path.exists(p):
        out("  SMOKE  no corrections list on disk; no live page exercised")
        return
    with io.open(p, encoding="utf-8") as fh:
        pages = json.load(fh).get("pages", {})
    absent = 0
    for name, rec in sorted(pages.items()):
        if rec.get("class") != "PUBLISHED_CORRECTION" or not rec.get("must_render"):
            continue
        if name in PROTECTED or "HFREF" in name or "ARNI" in name:
            continue
        fp = os.path.join(ROOT, name)
        # POSITIVE FORM, AND THE ABSENT ONES ARE COUNTED. `if not os.path.exists:
        # continue` inside a loop over the corpus drops a candidate before it is
        # counted anywhere, so the smoke check could silently examine nothing and
        # still print a line. audit_exclusion_by_absence refused this file for it
        # and was right.
        if os.path.exists(fp):
            pass
        else:
            absent += 1
            continue
        with io.open(fp, encoding="utf-8", errors="replace") as fh:
            html = fh.read()
        try:
            dnr.check_correction_survives(fp, html)
            out("  SMOKE  live page %s accepted as it stands (%d bytes)"
                % (name, len(html)))
        except SystemExit as exc:
            out("  SMOKE  live page %s REFUSED as it stands: %s"
                % (name, str(exc)[:120]))
            out("         (reported, not decisive -- the verdict is the synthetic case)")
        return
    out("  SMOKE  no live page qualifies: %d listed page(s) are absent from disk, "
        "the rest are unpinned or protected. That is a fact about the corpus, "
        "not a pass." % absent)


def main():
    import do_not_rebuild as dnr

    say = print
    say("PLANT: published-correction guard")
    say("  named positive: SYNTHETIC, built in memory, anchored to nothing live")
    say("")
    ok = True
    real_list = dnr.CORRECTIONS
    tmps = []

    try:
        # ---- 1 and 2: pinned sentence present, then removed ------------------
        lst = _list_with({SYNTH_PAGE: {"class": "PUBLISHED_CORRECTION",
                                       "must_render": SENTINEL}})
        tmps.append(lst)
        dnr.CORRECTIONS = lst
        path = os.path.join(ROOT, SYNTH_PAGE)

        try:
            dnr.check_correction_survives(path, SYNTH_HTML)
            say("  1 PASS  guard accepts a synthetic page carrying its pinned sentence")
        except SystemExit as exc:
            say("  1 *** FAIL *** guard refuses a page that DOES carry it: %s"
                % str(exc)[:150])
            ok = False

        stripped = SYNTH_HTML.replace(SENTINEL, "")
        try:
            dnr.check_correction_survives(path, stripped)
            say("  2 *** FAIL *** guard ACCEPTED a page with the correction removed. "
                "It cannot report the thing it exists for.")
            ok = False
        except SystemExit as exc:
            msg = str(exc)
            named = SYNTH_PAGE in msg and "DROPPED IT" in msg
            quoted = SENTINEL[:40] in msg
            say("  2 PASS  guard refuses the same page with the sentence removed")
            say("          names the page: %s   quotes the correction: %s"
                % (named, quoted))
            if not (named and quoted):
                ok = False

        # ---- 3: a correction that could not be pinned ------------------------
        lst2 = _list_with({SYNTH_UNPINNABLE: {"class": "PUBLISHED_CORRECTION",
                                              "must_render": None}})
        tmps.append(lst2)
        dnr.CORRECTIONS = lst2
        try:
            dnr.check_correction_survives(os.path.join(ROOT, SYNTH_UNPINNABLE),
                                          "<style>x</style><p>anything</p>")
            say("  3 *** FAIL *** an UNPINNABLE correction was rebuilt anyway")
            ok = False
        except SystemExit as exc:
            say("  3 PASS  an unpinnable correction refuses the rebuild outright")

        # ---- 4: absent list ---------------------------------------------------
        dnr.CORRECTIONS = os.path.join(ROOT, "scripts", "baselines",
                                       "__absent_for_the_plant.json")
        try:
            dnr.check_correction_survives(path, SYNTH_HTML)
            say("  4 *** FAIL *** an ABSENT list was treated as an empty one")
            ok = False
        except SystemExit as exc:
            say("  4 PASS  an absent list refuses rather than passing")

    finally:
        dnr.CORRECTIONS = real_list
        for t in tmps:
            try:
                os.remove(t)
            except Exception:
                pass

    # ---- 5: the guard is actually CALLED ------------------------------------
    with io.open(os.path.join(ROOT, "ssot", "build_tabbed.py"), encoding="utf-8") as fh:
        src = fh.read().split("\n")
    call = [i for i, l in enumerate(src) if "check_correction_survives(" in l]
    write = [i for i, l in enumerate(src)
             if l.strip().startswith('open(out, "w"') and ".write(_html)" in l]
    if call and write and 0 < (write[0] - call[0]) <= 3:
        say("  5 PASS  build_tabbed.py calls it %d line(s) before the write"
            % (write[0] - call[0]))
    else:
        say("  5 *** FAIL *** not called immediately before the write (call=%s "
            "write=%s). A guard nothing invokes is not operative." % (call, write))
        ok = False

    say("")
    live_smoke(dnr, say)
    say("")
    say("  %s" % ("PLANT PROVEN on a synthetic control: the guard refuses a dropped "
                  "correction, refuses an unpinnable one, refuses an absent list, and "
                  "is invoked before the write."
                  if ok else
                  "PLANT NOT PROVEN -- read the failures above. Until this passes, no "
                  "page may be rebuilt."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
