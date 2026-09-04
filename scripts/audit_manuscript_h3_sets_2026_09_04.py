"""Corpus audit: which delivered pages would LOSE manuscript h3 sections on rebuild.

READ-ONLY. Projects each object in memory and compares heading SETS against the
delivered page. Writes no HTML, touches no delivered file, runs no build. Therefore
it disables no guard -- there is no build here for a guard to judge.

Heading sets, not byte counts: a page can grow while the manuscript loses sections,
and a size check scores that an improvement.
"""
import io
import json
import os
import re
import sys
import traceback

# The repo root is the parent of whichever directory this file sits in. The
# previous default was a hard-coded sandbox mount belonging to one session
# (/sessions/<name>/mnt/rmfw), which resolves nowhere for anybody else -- so the
# script ran only where it was written. An absolute path naming one machine is
# not a default, it is a single-user assumption wearing a default's clothes.
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "ssot"))

import build_tabbed as bt          # noqa: E402
import manuscript_guard as mg      # noqa: E402

H3 = re.compile(r"<h3[^>]*>(.*?)</h3>", re.S)
TAG = re.compile(r"<[^>]+>")


def h3set(seg):
    import html as _h
    out = []
    for m in H3.findall(seg):
        t = _h.unescape(TAG.sub("", m)).strip()
        t = re.sub(r"\s+", " ", t)
        if t:
            out.append(t)
    return out


def delivered_panel(path):
    try:
        h = io.open(path, "rb").read().decode("utf-8", "replace")
    except OSError:
        return None, None
    i = h.find('id="pn-paper"')
    j = h.find("<!--end-paper-->")
    if i < 0 or j <= i:
        return h, None
    return h, h[i:j]


def _controls():
    """Known-answer cases, SYNTHETIC and therefore not retirable by a repair.

    The obvious positive control here was ALIROCUMAB_LIPID_SSOT, which really
    did lose six headings on rebuild -- and the projector patch of 2026-09-04
    fixed it, which would have retired the control the same day it was written.
    A repair disarms the detector that found it, so a must-fire case anchored to
    a live corpus defect is a perishable asset. These two are built from
    literals: they cannot be retired by fixing anything.

    The positive is the exact shape the audit exists to catch -- a heading
    delivered to a reader that the projection does not account for. The negative
    is the case it is most likely to get wrong: a projection that RENAMES and
    REORDERS every heading while losing none. Renaming is the normal, harmless
    behaviour, and an audit that flagged it would fire on almost every page and
    be switched off within a week.
    """
    delivered = "<h3>Discussion</h3><h3>Conclusions</h3><h3>Keywords</h3>"
    loses = "<h3>Discussion</h3><h3>Keywords</h3>"
    renamed = "<h3>Keywords</h3><h3>Conclusion</h3><h3>Discussion</h3>"

    def lost_between(a, b):
        return [x for x in h3set(a) if x not in set(h3set(b))]

    return (("a heading delivered to a reader and absent from the projection is LOST",
             lost_between(delivered, loses) == ["Conclusions"], True),
            ("a projection that renames and reorders but loses nothing is NOT flagged",
             bool(lost_between(delivered, renamed)), False))


def main():
    # An instrument that walks the corpus and prints a count must declare a case
    # whose answer is already known, or its zero is untestable. Added 2026-09-04
    # after scripts/lint_instrument_declares_a_control.py refused this file.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from instrument_controls import require_controls  # noqa: E402
    pos, neg = _controls()
    require_controls("audit_manuscript_h3_sets_2026_09_04",
                     positive=pos, negative=neg)

    page_map = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"),
                                 encoding="utf-8"))
    rows = []
    for page, rel in sorted(page_map.items()):
        path = os.path.join(REPO, page)
        objp = os.path.join(REPO, rel)
        rec = {"page": page, "obj": rel}
        if not os.path.exists(path):
            rec["status"] = "NO_DELIVERED_FILE"
            rows.append(rec)
            continue
        full, panel = delivered_panel(path)
        if panel is None:
            rec["status"] = "NO_PANEL_DELIVERED"
            rows.append(rec)
            continue
        if not os.path.exists(objp):
            rec["status"] = "NO_OBJECT"
            rows.append(rec)
            continue
        try:
            canon = json.load(io.open(objp, encoding="utf-8"))
        except Exception as exc:                      # noqa: BLE001
            rec["status"] = "OBJECT_UNREADABLE: %s" % exc
            rows.append(rec)
            continue
        try:
            newp = bt._paper_panel(canon)
        except Exception as exc:                      # noqa: BLE001
            rec["status"] = "PROJECTOR_RAISED: %s: %s" % (type(exc).__name__, exc)
            rec["trace"] = traceback.format_exc()[-400:]
            rows.append(rec)
            continue
        old_h, new_h = h3set(panel), h3set(newp)
        olds, news = set(old_h), set(new_h)
        lost = [x for x in old_h if x not in news]
        gained = [x for x in new_h if x not in olds]
        fake = 'id="pn-paper"' + newp + "<!--end-paper-->"
        oshape = mg.paper_shape(full)
        nshape = mg.paper_shape(fake)
        rec.update({
            "status": "OK",
            "delivered_h3": len(old_h), "projected_h3": len(new_h),
            "lost": lost, "gained": gained,
            "delivered_chars": oshape[0] if oshape else None,
            "projected_chars": nshape[0] if nshape else None,
            "docmodel": os.path.exists(
                os.path.join(os.path.dirname(objp), "manuscript_docmodel.json")),
            "has_manuscript_block": isinstance(canon.get("manuscript"), dict),
        })
        if rec["delivered_chars"]:
            rec["pct"] = 100.0 * (rec["projected_chars"] - rec["delivered_chars"]) \
                / rec["delivered_chars"]
        rows.append(rec)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_h3.json")
    with io.open(out, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(rows, indent=1))
    print("wrote %s  (%d pages)" % (out, len(rows)))

    # A REACHABLE FAILURE, added 2026-09-04. `main()` returned None, so
    # `sys.exit(main())` was `sys.exit(0)` on every input: this file returned a
    # verdict and could not fail. `scripts/lint_gate_can_fail.py` refused every
    # commit in the worktree because of it, and the linter was right --
    # measured the same day, six pre-push gates printed "clean" while examining
    # nothing, which is what a check that cannot fail looks like from outside.
    #
    # The condition this audit exists to detect is a delivered manuscript
    # heading that the projection does not account for. That is now what makes
    # it exit non-zero. Nothing else about it changed: it still writes no HTML,
    # touches no delivered file and runs no build.
    #
    # The three NOT_RUN classes are counted and reported SEPARATELY and do not
    # fail the run. A page whose object is unreadable, or whose projector
    # raised, has not been shown to be healthy -- it has not been examined, and
    # folding it into either a pass or a failure would state something the
    # audit does not know.
    losing = [r for r in rows if r.get("status") == "OK" and r.get("lost")]
    not_run = [r for r in rows
               if str(r.get("status", "")).startswith(
                   ("OBJECT_UNREADABLE", "PROJECTOR_RAISED", "NO_OBJECT"))]
    examined = [r for r in rows if r.get("status") == "OK"]
    print("examined %d of %d pages; NOT_RUN %d (unreadable object, projector "
          "raised, or no object)" % (len(examined), len(rows), len(not_run)))
    for r in not_run:
        print("  NOT_RUN  %-52s %s" % (r["page"], r.get("status")))
    if losing:
        print("\nFAIL: %d page(s) would LOSE delivered manuscript heading(s) on "
              "rebuild." % len(losing))
        for r in losing:
            print("  %-52s -%d h3  %s"
                  % (r["page"], len(r["lost"]), ", ".join(r["lost"][:6])))
        print("\nA lost heading is not a cosmetic diff. On ALIROCUMAB_LIPID_SSOT "
              "an evicted section took a pooled estimate with it, while the page "
              "GREW -- so a size check scored that an improvement.")
        return 1
    print("\nOK: no page loses a delivered manuscript heading on rebuild.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
