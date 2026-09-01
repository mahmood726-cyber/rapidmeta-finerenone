# -*- coding: utf-8 -*-
"""RANK EVERY PAGE BY DISTANCE TO FULL MOAT STANDARD. No guessing which is closest.

Seven components, each measured, each reported SEPARATELY so nothing is hidden
inside a single score:

    tabs_with_content   of the ruled eight -- CONTENT, never presence. A tab that
                        only declines is honest and is already counted under c4;
                        counting it again as content is the metric-flattery this
                        project refuses.
    clauses             gate16 c1-c4, applicable ones only
    correction          PRESENT / UNPINNED / NOT_LISTED / DROPPED
    keep                on outputs/_ready_keep.txt -- a page not surfaced is not done
    hta                 reader_renderings_2026_08_30.renderings.hta EXISTS
    guideline           all five inputs the guideline view's informed cells read
    builds              not measured here; a separate cold-clone question

⛔ THE HTA COLUMN DOES NOT ASK absolute_effect. It was believed for a while that
the HTA tab was gated on the absolute-effect deriver. It is not: projectors.py
gives that tab exactly one card, hta_card -> _one_reader_card(canon, "hta"), which
reads reader_renderings_2026_08_30. Fixing the deriver would not add one tab to
one page. The column asks the field the template actually reads.
"""
import glob
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RK = "reader_renderings_2026_08_30"


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def guideline_inputs(canon):
    """The five INFORMED cells of AGYW's view, by the field each one read."""
    bo = ((canon.get("results") or {}) if isinstance(canon.get("results"), dict)
          else {}).get("by_outcome") or {}
    vals = list(bo.values()) if isinstance(bo, dict) else []
    return {
        "pooled_point": any(isinstance(r, dict) and isinstance(r.get("pooled"), dict)
                            and r["pooled"].get("point") is not None for r in vals),
        "grade_certainty": any(isinstance(r, dict) and (r.get("grade") or {}).get("certainty")
                               for r in vals),
        "harms_block": any(k.startswith("harms") for k in canon.keys()),
        "registry_extraction": any(k.startswith("registry_extraction") for k in canon.keys()),
        "per_arm_events": any(
            isinstance(t, dict) and isinstance(t.get("arms"), list)
            and any(isinstance(a, dict) and a.get("events") is not None for a in t["arms"])
            for t in ((canon.get("inputs") or {}).get("trials") or [])),
    }


def main():
    m = load("g16", "gates/gate16_reader_can_check.py")
    mm = load("mm", "scripts/moat_standard_served.py")
    req = mm.required_tabs()
    keep = set(l.strip() for l in io.open(os.path.join(REPO, "outputs", "_ready_keep.txt"),
                                          encoding="utf-8") if l.strip())
    cp = os.path.join(REPO, "scripts", "baselines", "published_corrections.json")
    corr = json.load(io.open(cp, encoding="utf-8")).get("pages", {}) \
        if os.path.exists(cp) else {}

    # ---- KNOWN-ANSWER CONTROL -------------------------------------------------
    # AGYW is the one page measured at full standard. If the ranker does not put it
    # at 8/8 content with hta=True, the ranker is broken and no ranking is printed.
    control = "AGYW_HIV_PREP_REVIEW.html"

    rows = []
    pages = [p for p in m.pages() if m.store_for(p)]
    for page in pages:
        sp = m.store_for(page)
        try:
            html = io.open(os.path.join(REPO, page), encoding="utf-8", errors="replace").read()
            canon = json.load(io.open(sp, encoding="utf-8"))
        except Exception as exc:
            rows.append((page, "READ_FAILED:%s" % type(exc).__name__, 0, 0, 0, "-", False, False, {}))
            continue
        if m.is_tombstone(html):
            rows.append((page, "TOMBSTONE", 0, 0, 0, "-", False, False, {}))
            continue
        body = m._body(html)
        content = sum(1 for _, hint in req if mm.tab_has_content(body, "pn-" + hint)[1])
        try:
            cl, _ = m.assess(page, html, canon)
        except Exception:
            cl = {}
        ap = [k for k, v in cl.items() if v is not None]
        got = sum(1 for k in ap if cl[k])
        rec = corr.get(page)
        cstate = ("NOT_LISTED" if not rec else
                  ("PRESENT" if rec.get("class") != "PUBLISHED_CORRECTION"
                   else ("UNPINNED" if not rec.get("must_render") else "PRESENT")))
        hta = isinstance((canon.get(RK) or {}).get("renderings", {}).get("hta"), dict) \
            if isinstance(canon.get(RK), dict) else False
        gi = guideline_inputs(canon)
        rows.append((page, "OK", content, got, len(ap), cstate,
                     page in keep, hta, gi))

    ok = [r for r in rows if r[1] == "OK"]
    ctrl = [r for r in ok if r[0] == control]
    print("  KNOWN-ANSWER CONTROL -- expected beside observed")
    if not ctrl:
        print("    %s  expected content 8/8 hta=True   observed: NOT EVALUATED"
              % control)
        print("  REFUSED: the control page was not evaluated. No ranking printed.")
        return 3
    c = ctrl[0]
    okc = (c[2] == len(req) and c[7])
    print("    %-30s expected content %d/%d hta=True   observed content %d/%d hta=%s   %s"
          % (control, len(req), len(req), c[2], len(req), c[7],
             "ok" if okc else "*** WRONG ***"))
    if not okc:
        print("  REFUSED: the control did not measure as known. No ranking printed.")
        return 3
    print("")

    print("  pages with a store evaluated : %d" % len(ok))
    print("  named non-OK states          : %s"
          % (", ".join("%s=%d" % (s, sum(1 for r in rows if r[1] == s))
                       for s in sorted(set(r[1] for r in rows if r[1] != "OK")))
             or "none"))
    print("")

    def score(r):
        return (r[2], r[3] - (r[4] - r[3]), r[6], r[7], sum(r[8].values()))

    print("  TOP 12 BY DISTANCE TO FULL STANDARD (content, then clauses, then keep)")
    print("  %-42s cont clauses corr        keep hta guide_inputs" % "page")
    for r in sorted(ok, key=score, reverse=True)[:12]:
        print("  %-42s %d/%d  %d/%-3d  %-11s %-4s %-4s %d/5"
              % (r[0][:42], r[2], len(req), r[3], r[4], r[5],
                 "YES" if r[6] else "-", "YES" if r[7] else "-", sum(r[8].values())))
    print("")
    full = [r for r in ok if r[2] == len(req) and r[3] == r[4] and r[6] and r[7]]
    print("  AT FULL STANDARD (content, all clauses, listed, hta) : %d" % len(full))
    for r in full:
        print("     %s" % r[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
