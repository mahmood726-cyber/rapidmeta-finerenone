r"""How many pages now disagree with the sidecar that backs them?

WHY THIS EXISTS
    The 232-file swap corrected the sidecars. It did not touch the pages, and
    131 of those sidecars changed their numbers. So a page may now render an
    odds ratio its own sidecar no longer supports.

    That is worse than the state before the swap in one specific way: before,
    page and sidecar agreed on a wrong number; now they disagree and nothing
    says so. The swap was verified three ways and every check was scoped to
    the FILE I CHANGED -- none asked what consumes it. This measures the
    consumer.

WHAT IS COMPARED
    OLD   the pooled_OR the sidecar held BEFORE the swap, recovered from git
    NEW   the pooled_OR the sidecar holds now
    PAGE  the bytes of <STEM>_REVIEW.html

    A page is DISAGREEING when it renders the OLD value and not the NEW one.
    A page is UPDATED when it renders the NEW value.
    A page that renders NEITHER does not show this number at all, and is
    counted separately rather than assumed to be either.

INSTRUMENT CHECK FIRST
    A sweep that reports "0 disagreeing" is worthless unless it can detect a
    disagreement. ATEZOLIZUMAB_BLADDER is known to carry the old value
    (0.69344) and not the new one (2.0244), so it is checked first and the
    sweep refuses to report if it cannot see that.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SERVED = os.path.join(ROOT, "outputs", "r_validation")


def old_value(stem, field="pooled_OR", ref="HEAD~1"):
    """The value the sidecar held before the swap, read from git."""
    rel = "outputs/r_validation/%s.json" % stem
    p = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (ref, rel)],
                       capture_output=True)
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout.decode("utf-8", "replace")).get(field)
    except Exception:
        return None


def page_for(stem):
    for suffix in ("_REVIEW.html", "_FULL_REVIEW.html"):
        cand = os.path.join(ROOT, stem + suffix)
        if os.path.exists(cand):
            return cand
    # sidecar stems drop the _FULL_REVIEW suffix; try adding it back
    cand = os.path.join(ROOT, stem.replace("_AUTO_FULL", "_AUTO_FULL_REVIEW")
                        + ".html")
    if os.path.exists(cand):
        return cand
    return None


def renders(path, value):
    """Does the page carry this number, at the precision pages use?

    Pages round; the sidecar stores more digits. So match on a prefix at 3
    and 4 decimal places rather than the full float, and accept either.
    Matching the full float would report every page as not-rendering, which
    is the flattering direction and would hide the problem.
    """
    if value is None:
        return False
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return False
    for dp in (4, 3):
        s = ("%%.%df" % dp) % value
        if re.search(re.escape(s) + r"\d*", src):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="HEAD~1",
                    help="git ref holding the pre-swap sidecars")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    # ---- instrument check
    probe = "ATEZOLIZUMAB_BLADDER_AUTO_FULL"
    pp = page_for(probe)
    po, pn = old_value(probe, ref=a.ref), None
    try:
        pn = json.load(open(os.path.join(SERVED, probe + ".json"),
                            encoding="utf-8")).get("pooled_OR")
    except Exception:
        pass
    print("INSTRUMENT CHECK on a page known to carry the old value")
    print("  page        %s" % (os.path.basename(pp) if pp else "NOT FOUND"))
    print("  old %.5f renders: %s" % (po or -1, renders(pp, po) if pp else "n/a"))
    print("  new %.5f renders: %s" % (pn or -1, renders(pp, pn) if pp else "n/a"))
    detects = bool(pp) and renders(pp, po) and (renders(pp, pn) is False)
    print("  can this sweep see a disagreement: %s" % detects)
    if detects is False:
        print("  *** NO VERDICT -- the sweep cannot detect the known case ***")
        return 2
    print("")

    stems = sorted(os.path.basename(p)[:-5]
                   for p in __import__("glob").glob(os.path.join(SERVED, "*.json"))
                   if not os.path.basename(p).startswith("_"))
    if a.limit:
        stems = stems[:a.limit]

    c = Counter()
    disagreeing = []
    for stem in stems:
        try:
            new = json.load(open(os.path.join(SERVED, stem + ".json"),
                                 encoding="utf-8")).get("pooled_OR")
        except Exception:
            c["sidecar_unreadable"] += 1
            continue
        old = old_value(stem, ref=a.ref)
        if old is None:
            c["no_pre_swap_version"] += 1
            continue
        if new is None or old == new:
            c["sidecar_unchanged"] += 1
            continue
        page = page_for(stem)
        if page is None:
            c["changed_but_no_page"] += 1
            continue
        r_old, r_new = renders(page, old), renders(page, new)
        if r_old and (r_new is False):
            c["PAGE_DISAGREES"] += 1
            disagreeing.append((stem, old, new))
        elif r_new:
            c["page_updated"] += 1
        else:
            c["page_shows_neither"] += 1

    print("PAGE vs SIDECAR, after the swap")
    for k in ("PAGE_DISAGREES", "page_updated", "page_shows_neither",
              "changed_but_no_page", "sidecar_unchanged",
              "no_pre_swap_version", "sidecar_unreadable"):
        print("  %-24s %d" % (k, c.get(k, 0)))
    print("  identity: %d == %d sidecars : %s"
          % (sum(c.values()), len(stems),
             "HOLDS" if sum(c.values()) == len(stems) else "FAILS"))
    print("")
    print("  DISAGREEING PAGES, first 20 -- the page shows the pre-swap value")
    for stem, old, new in disagreeing[:20]:
        print("      %-42s page %.4f  sidecar %.4f" % (stem[:42], old, new))
    if len(disagreeing) > 20:
        print("      ... and %d more" % (len(disagreeing) - 20))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
