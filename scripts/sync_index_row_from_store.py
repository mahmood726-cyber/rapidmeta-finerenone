# -*- coding: utf-8 -*-
"""The index row and the index tile must come from the SAME place: the store.

WHY THIS EXISTS. AGYW_HIV_PREP_REVIEW.html was described four ways at one URL:

    tile anchor     Dapivirine vaginal ring versus placebo ring ... RR 0.703, k=2
    table anchor    HIV PrEP for AGYW in sub-Saharan Africa
    table cells     oral PrEP adherence 23% vs 12%; vaginal TFV gel  NULL   v0.1
    JS title map    HIV PrEP Modalities ... NMA

The tile is PROJECTED from the store, so it followed when the topic was
re-specified from an oral-PrEP/TFV-gel network to a dapivirine-ring pairwise
comparison. The row and the title map are LITERALS, written once by
scripts/build_3topics_hep_mhealth_agyw.py at topic-creation time -- its docstring
still reads "AGYW_HIV_PREP_NMA: HPTN 082 oral PrEP adherence + FACTS-001
tenofovir gel" -- and literals do not follow anything.

    ONE SURFACE PROJECTED AND ONE SURFACE AUTHORED IS NOT TWO DESCRIPTIONS OF
    ONE REVIEW. IT IS TWO REVIEWS SHARING A URL, AND ONLY ONE OF THEM EXISTS.

⛔ SO THIS DOES NOT "CORRECT THE TEXT". It derives the row from the object, which
is the only thing that stops it drifting again the next time a topic is
re-specified. Correcting the text by hand would have fixed today and guaranteed
tomorrow.

    python scripts/sync_index_row_from_store.py                # report, exit 1 on drift
    python scripts/sync_index_row_from_store.py --apply PAGE   # rewrite one page's row

The report is corpus-wide and names its denominator. --apply is per page and
deliberate: a sweep that rewrites 149 rows from stores of varying completeness is
how a display defect becomes a data defect.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "index.html")

ROW_RE = re.compile(r"<tr\b(?:(?!</tr>).)*?</tr>", re.S)
HREF_RE = re.compile(r'href=["\']([A-Za-z0-9_.-]+\.html)["\']')
ANCHOR_RE = re.compile(r'(<a\b[^>]*href=["\'][A-Za-z0-9_.-]+\.html["\'][^>]*>)(.*?)(</a>)', re.S)
CELL_RE = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S)
MAP_RE_T = '"%s":\\s*\\{[^}]*?"title":\\s*"((?:[^"\\\\]|\\\\.)*)"'


def flat(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def store_for(url):
    slug = re.sub(r"\.html$", "", url).lower().replace("_", "-")
    p = os.path.join(ROOT, "ssot", slug, slug + ".json")
    return p if os.path.exists(p) else None


def facts(path):
    """title, k and the pooled estimate, read from the object and nowhere else."""
    with io.open(path, encoding="utf-8") as fh:
        c = json.load(fh)
    title = str(c.get("title") or "").strip()
    res = c.get("results")
    bo = res.get("by_outcome") if isinstance(res, dict) else None
    blk = (bo or {}).get("primary") if isinstance(bo, dict) else None
    if not isinstance(blk, dict):
        for v in (bo or {}).values():
            if isinstance(v, dict) and v.get("pooled"):
                blk = v
                break
    pooled = (blk or {}).get("pooled") or {}
    k = (blk or {}).get("k")
    if k is None:
        tr = c.get("inputs", {}).get("trials")
        k = len(tr) if isinstance(tr, list) else None
    pt, lo, hi = pooled.get("point"), pooled.get("ci_low"), pooled.get("ci_high")
    meas = pooled.get("measure") or (blk or {}).get("measure") or ""
    if pt is None:
        est = ""
    elif lo is None or hi is None:
        est = "%s %s" % (meas, pt)
    else:
        est = "%s %.4g (%.4g–%.4g)" % (meas, pt, lo, hi)
    return title, k, est.strip()


def rows_by_url(html):
    out = {}
    for m in ROW_RE.finditer(html):
        h = HREF_RE.search(m.group(0))
        if h:
            out.setdefault(h.group(1), []).append(m)
    return out


def main():
    argv = sys.argv[1:]
    apply_to = None
    if "--apply" in argv:
        i = argv.index("--apply")
        if i + 1 >= len(argv):
            print("REFUSED: --apply needs a page name.")
            return 2
        apply_to = argv[i + 1]

    with io.open(INDEX, encoding="utf-8") as fh:
        html = fh.read()
    rows = rows_by_url(html)

    checked = drift = nostore = 0
    findings = []
    for url in sorted(rows):
        sp = store_for(url)
        if sp is None:
            nostore += 1
            continue
        checked += 1
        title, k, est = facts(sp)
        for m in rows[url]:
            cells = [flat(c) for c in CELL_RE.findall(m.group(0))]
            a = ANCHOR_RE.search(m.group(0))
            row_title = flat(a.group(2)) if a else ""
            row_est = cells[3] if len(cells) > 3 else ""
            bad = []
            if title and row_title and title.lower() not in row_title.lower() \
                    and row_title.lower() not in title.lower():
                bad.append(("title", row_title, title))
            if est and row_est and not row_est.startswith(str(est).split(" ")[0]):
                bad.append(("estimate", row_est, est))
            if bad:
                drift += 1
                findings.append((url, bad))

    print("INDEX ROW vs STORE")
    print("  rows linking a review page   : %d" % len(rows))
    print("  ...whose store resolves      : %d   <- the denominator" % checked)
    print("  ...with no store on disk     : %d   (not checked, not cleared)" % nostore)
    print("  ROWS DISAGREEING WITH THEIR OWN OBJECT: %d of %d" % (drift, checked))
    for url, bad in findings:
        print()
        print("  %s" % url)
        for what, got, want in bad:
            print("     row   %-9s %s" % (what, got[:88]))
            print("     store %-9s %s" % (what, str(want)[:88]))

    if apply_to is None:
        return 1 if drift else 0

    sp = store_for(apply_to)
    if sp is None:
        print()
        print("REFUSED: no store resolves for %s, so there is nothing to derive "
              "the row FROM. Writing a row from anything else is how the two "
              "surfaces diverged in the first place." % apply_to)
        return 2
    title, k, est = facts(sp)
    if not title:
        print()
        print("REFUSED: %s carries no title. A row derived from an empty field "
              "is not a fix." % os.path.basename(sp))
        return 2

    before = html
    for m in rows_by_url(html).get(apply_to, []):
        row = m.group(0)
        new = ANCHOR_RE.sub(lambda a: a.group(1) + title + a.group(3), row, count=1)
        cells = CELL_RE.findall(new)
        if len(cells) > 3 and est:
            old_cell = cells[3]
            idx = new.find(old_cell)
            if idx >= 0:
                new = new[:idx] + est + new[idx + len(old_cell):]
        html = html.replace(row, new, 1)

    pat = re.compile(MAP_RE_T % re.escape(apply_to))
    mm = pat.search(html)
    if mm:
        html = html[:mm.start(1)] + title + html[mm.end(1):]

    if html == before:
        print()
        print("nothing to write: the row and the title map already match the object.")
        return 0
    with io.open(INDEX, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    print()
    print("REWROTE the index row and the title map for %s FROM %s"
          % (apply_to, os.path.relpath(sp, ROOT)))
    print("   title : %s" % title)
    print("   k     : %s" % k)
    print("   pooled: %s" % est)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.exit(main())
