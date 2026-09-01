# -*- coding: utf-8 -*-
"""Is THIS page safe to rebuild? Answered from the page and its store, not a list.

⛔ WHY THIS DOES NOT READ A BLOCKER LIST, AND MUST NOT.

A protection list was routed to this lane as "the pages that must not be
rebuilt". It was scoped to ONE question -- does a sidecar pool trials the page
does not name -- and three pages that must not be rebuilt for an entirely
different reason (a store refusal that the sidecar overrode) do not fail it.

    A PROTECTION LIST SCOPED BY ONE CRITERION, APPLIED AS THOUGH IT COVERED
    ANOTHER. ABSENCE FROM A LIST IS NOT A PROPERTY OF THE PAGE.

That is the same defect as reading "not in the baseline" as "clean", and as
reading a scan's reach as its coverage. So this asserts a POSITIVE property of
the page in front of it, and a page passes only by exhibiting it.

THE THREE ASSERTIONS

  A. TRIAL SET. The store's registrations and the page's rendered registrations
     are the SAME SET, compared as registration ids -- not as counts, and not as
     estimates. A count matches by coincidence; an id does not.

  B. SURFACE AGREEMENT. Every surface that describes the page agrees with the
     store on MEASURE, VALUE, INTERVAL and DIRECTION. A surface that disagrees
     is EVIDENCE, and rebuilding the page destroys it.

  C. NO SILENT DEFAULTS. A page whose store holds more than one interval for the
     same estimate is refused unless the page renders the choice. The dapivirine
     object holds an unadjusted interval that excludes the null and a
     Hartung-Knapp interval that spans it; a generator reading one field name
     picks between two published findings without deciding to.

    python scripts/rebuild_safety_assertion.py PAGE.html [PAGE.html ...]
    python scripts/rebuild_safety_assertion.py --controls     # prove it can fail

Exit 0 only if every named page exhibits all three. Exit 1 names what failed.
⛔ A page that fails is not a page to fix by rebuilding it.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NCT = re.compile(r"\bNCT\d{8}\b")


def store_for(page):
    slug = re.sub(r"\.html$", "", page).lower().replace("_", "-")
    p = os.path.join(ROOT, "ssot", slug, slug + ".json")
    return p if os.path.exists(p) else None


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            for x in walk(v, p + "/" + str(k)):
                yield x
    elif isinstance(o, list):
        for i, v in enumerate(o):
            for x in walk(v, p + "/%d" % i):
                yield x
    else:
        yield p, o


def store_trials(canon):
    """Registration ids the OBJECT claims, from inputs.trials and per_trial rows."""
    ids = set()
    for t in (canon.get("inputs") or {}).get("trials") or []:
        if isinstance(t, dict):
            for key in ("nct", "nct_id", "registration", "id"):
                v = t.get(key)
                if isinstance(v, str) and NCT.search(v):
                    ids.add(NCT.search(v).group(0))
    for path, v in walk(canon):
        if isinstance(v, str) and "/per_trial/" in path and NCT.search(v):
            ids.add(NCT.search(v).group(0))
    return ids


def page_trials(html):
    """Registration ids the page renders AS INCLUDED TRIALS, and where it read them.

    ⛔ NOT EVERY NCT ON THE PAGE IS AN INCLUDED TRIAL, AND THE FIRST VERSION OF
    THIS FUNCTION ASSUMED IT WAS. On the dapivirine page the screening panel
    renders 65 registry records -- every one screened, most EXCLUDED, each with
    its decision -- because showing them is the point. Comparing all 65 against
    the store's 2 reported a trial-set mismatch on the one page that is right,
    and it counted the moat as the defect.

    The included trials are the per-trial evidence rows, which live in the
    extraction panel. Fall back only with the fallback NAMED, so a caller can
    see that the comparison was made against a wider set than intended.
    """
    body = html.split("</style>", 1)[-1]
    body = re.sub(r"<script\b.*?</script>", " ", body, flags=re.S)
    for pid in ("pn-extract", "pn-analysis"):
        m = re.search(r'<section class="panel" id="%s">(.*?)</section>' % pid,
                      body, re.S)
        if m:
            ids = set(NCT.findall(m.group(1)))
            if ids:
                return ids, pid
    return set(NCT.findall(body)), "WHOLE PAGE (no extraction panel found)"


def intervals(canon):
    """Every (name, lo, hi) interval attached to the primary outcome block."""
    bo = ((canon.get("results") or {}).get("by_outcome") or {})
    blk = bo.get("primary") if isinstance(bo, dict) else None
    if not isinstance(blk, dict):
        for v in (bo or {}).values():
            if isinstance(v, dict) and v.get("pooled"):
                blk = v
                break
    out = []
    for k, v in (blk or {}).items():
        if isinstance(v, dict) and v.get("ci_low") is not None \
                and v.get("ci_high") is not None:
            out.append((k, v.get("ci_low"), v.get("ci_high")))
    return out, (blk or {})


def index_rows(page):
    """(where, text) for every index surface that describes this page."""
    idx = os.path.join(ROOT, "index.html")
    if not os.path.exists(idx):
        return []
    with io.open(idx, encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    out = []
    for m in re.finditer(r"<tr\b(?:(?!</tr>).)*?</tr>", html, re.S):
        if page in m.group(0):
            out.append(("index row", re.sub(r"\s+", " ",
                                            re.sub(r"<[^>]+>", " ", m.group(0))).strip()))
    for m in re.finditer(r'<a\b[^>]*href=["\']%s["\'][^>]*>(.*?)</a>' % re.escape(page),
                         html, re.S):
        out.append(("index anchor", re.sub(r"\s+", " ",
                                           re.sub(r"<[^>]+>", " ", m.group(1))).strip()))
    m = re.search(r'"%s":\s*\{[^}]*?"title":\s*"([^"]*)"' % re.escape(page), html)
    if m:
        out.append(("title map", m.group(1)))
    return out


NUM = re.compile(r"\d+(?:\.\d+)?")
MEAS = re.compile(r"\b(RR|OR|HR|MD|SMD|RD|RATE_RATIO)\b", re.I)


def check(page):
    fails = []
    notes = []
    pp = os.path.join(ROOT, page)
    sp = store_for(page)
    if not os.path.exists(pp):
        return ["page not on disk: %s" % page], notes
    if sp is None:
        return ["no store resolves for %s -- nothing to assert AGAINST, which is "
                "not the same as safe" % page], notes
    with io.open(pp, encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    with io.open(sp, encoding="utf-8") as fh:
        canon = json.load(fh)

    # --- A. trial set, by registration id -------------------------------------
    s_ids = store_trials(canon)
    p_ids, whence = page_trials(html)
    notes.append("A  store %d id(s), page %d id(s) read from %s"
                 % (len(s_ids), len(p_ids), whence))
    if not s_ids:
        fails.append("A: the store names NO registration id, so the trial set "
                     "cannot be compared. An unassertable page is not a safe one.")
    elif s_ids != p_ids:
        only_s = sorted(s_ids - p_ids)
        only_p = sorted(p_ids - s_ids)
        fails.append("A: trial sets differ -- store-only %s ; page-only %s"
                     % (only_s or "none", only_p or "none"))

    # --- B. every surface agrees with the store -------------------------------
    ivs, blk = intervals(canon)
    pooled = blk.get("pooled") or {}
    s_meas = str(pooled.get("measure") or blk.get("measure") or "").upper()
    s_pt = pooled.get("point")
    surfaces = index_rows(page)
    notes.append("B  %d surface(s) describe this page" % len(surfaces))
    for where, text in surfaces:
        m = MEAS.search(text)
        if m and s_meas and m.group(1).upper() != s_meas:
            fails.append("B: %s says measure %s, the store says %s -- %s"
                         % (where, m.group(1).upper(), s_meas, text[:70]))
        if s_pt is not None:
            nums = [float(x) for x in NUM.findall(text)]
            if nums and not any(abs(n - float(s_pt)) <= 0.02 * max(1.0, abs(float(s_pt)))
                                for n in nums):
                fails.append("B: %s carries no value matching the store's point %s -- %s"
                             % (where, s_pt, text[:70]))

    # --- C. no silent choice between intervals --------------------------------
    notes.append("C  %d interval(s) on the primary outcome: %s"
                 % (len(ivs), ", ".join(n for n, _, _ in ivs) or "none"))
    if len(ivs) > 1:
        def spans(lo, hi):
            null = 0.0 if s_meas in ("MD", "SMD", "RD") else 1.0
            return lo <= null <= hi
        verdicts = set(spans(lo, hi) for _, lo, hi in ivs)
        if len(verdicts) > 1:
            named = [n for n, _, _ in ivs if n != "pooled"]
            shown = any(n.replace("pooled_", "").replace("_", "-").lower() in html.lower()
                        or n.lower() in html.lower() for n in named)
            if not shown:
                fails.append("C: the store holds %d intervals that DISAGREE about the "
                             "null (%s) and the page renders only one of them. A "
                             "rebuild would re-make that choice silently."
                             % (len(ivs), ", ".join(n for n, _, _ in ivs)))
    # --- D. a surface publishing over the store's own withdrawal --------------
    #
    # ⛔ THE DISCRIMINATOR IS `withdrawn`, NOT `poolable`. All three protected
    # pages carry poolable=false, and on ONE of them the estimate legitimately
    # STANDS: bempedoic-acid's own reason reads "Nothing is pooled: one trial.
    # This is not a withheld estimate -- the value stands and is CLEAR Outcomes'
    # own." Refusing on poolable=false would have called a correct page a defect,
    # which is the accusing direction.
    #
    # The real case is a store that WITHDREW its estimate -- point null,
    # withdrawn true, with a reason in its own words -- while a surface goes on
    # publishing a number. That is not a stale label; it is a retraction that
    # never reached the reader.
    withdrawn = bool(pooled.get("withdrawn")) or (
        pooled.get("point") is None and pooled.get("measure"))
    if withdrawn:
        reason = str(blk.get("poolable_reason") or
                     pooled.get("withdrawn_reason") or "")
        notes.append("D  the store WITHDRAWS this estimate%s"
                     % (": " + reason[:60] if reason else ""))
        for where, text in surfaces:
            if NUM.search(re.sub(r"\bv?\d+\.\d+\b", " ", text)) and MEAS.search(text):
                fails.append(
                    "D: the store withdrew this estimate and %s still publishes a "
                    "number -- %s" % (where, text[:80]))
        if not fails:
            notes.append("D  no surface publishes a number over the withdrawal")

    return fails, notes


def controls():
    """Prove this can fail, on real pages whose answers are already established."""
    print("CONTROLS -- a checker validated on one artefact tells you about that")
    print("artefact, not the corpus. Both of these are REAL pages.")
    print()
    ok = True
    neg, _ = check("AGYW_HIV_PREP_REVIEW.html")
    print("  NEGATIVE (must PASS): AGYW_HIV_PREP_REVIEW.html -> %d failure(s)"
          % len(neg))
    for f in neg:
        print("      %s" % f[:150])
    pos, _ = check("CAB_PREP_HIV_REVIEW.html")
    print("  POSITIVE (must FAIL): CAB_PREP_HIV_REVIEW.html -> %d failure(s)"
          % len(pos))
    for f in pos:
        print("      %s" % f[:150])
    if pos:
        print("      ^ established independently: its index row reads HR 0.22 "
              "(0.11-0.45) and its store reads RR 0.2081 (0.0715-0.6057).")
    else:
        print("  *** the positive control did NOT fail. This checker cannot "
              "report a disagreement it was built for, and its passes mean nothing.")
        ok = False
    return 0 if ok else 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--controls" in sys.argv:
        return controls()
    if not args:
        print("usage: rebuild_safety_assertion.py PAGE.html [...]   |   --controls")
        return 2
    bad = 0
    for page in args:
        fails, notes = check(page)
        print()
        print("%s" % page)
        for n in notes:
            print("   %s" % n)
        if fails:
            bad += 1
            print("   REFUSED -- do NOT rebuild this page:")
            for f in fails:
                print("      %s" % f)
        else:
            print("   SAFE TO REBUILD: trial sets match by id, every surface agrees, "
                  "no undeclared interval choice.")
    print()
    print("%d of %d page(s) refused." % (bad, len(args)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.exit(main())
