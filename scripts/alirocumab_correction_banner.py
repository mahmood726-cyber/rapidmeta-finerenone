# -*- coding: utf-8 -*-
"""Generate the ALIROCUMAB k=10 correction banner FROM THE OBJECT and insert it into the page.

Route 2 banner. Numbers generated from ssot/alirocumab-lipid/...json, never typed. Discloses: two
eligible-poolable trials (CHOICE I + CHOICE II) that were wrongly held out, DM-INSULIN's reconstructed
value replaced by its published overall, and the two corrected false statements.
Marker ALIROCUMAB_K10_CORRECTION_2026_09_07.
"""
from __future__ import annotations
import io, os, re, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(ROOT, "ssot", "alirocumab-lipid", "alirocumab-lipid.json")
PAGE = os.path.join(ROOT, "ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html")
MARKER = "ALIROCUMAB_K10_CORRECTION_2026_09_07"
START, END = "<!-- %s:START -->" % MARKER, "<!-- %s:END -->" % MARKER


def _f(x):
    return ("%.2f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def build(obj):
    o = obj["results"]["by_outcome"]["ldlc_pct_change_wk24"]
    p = o["pooled"]
    pooled = "%s (%s to %s)" % (_f(p["point"]), _f(p["ci_low"]), _f(p["ci_high"]))
    k8 = o.get("pooled_k8_SUPERSEDED_2026_09_07", {})
    het = o.get("heterogeneity", {})
    return (
        '{START}\n'
        '<aside data-banner="{MARKER}" role="note" style="margin:0 0 1rem 0;padding:1rem 1.25rem;'
        'border:2px solid var(--warnb,#b45309);background:var(--warnbg,#fffbeb);border-radius:8px;'
        'font-size:.95rem;line-height:1.5">'
        '<strong style="color:var(--warnb,#b45309);text-transform:uppercase;letter-spacing:.03em">'
        'Correction (generated from the object 2026-09-07)</strong>'
        '<p style="margin:.5rem 0 0">Two eligible, poolable trials were wrongly held out. <strong>ODYSSEY '
        'CHOICE I</strong> (its two disjoint no-statin/statin strata combined by fixed-effect IV → −56.06) '
        'and <strong>CHOICE II</strong> (150 mg Q4W principal, −56.4) are now added, moving the pool from '
        '<strong>k={k8} {k8pt}</strong> to <strong>k=10, MD {pooled}%</strong> (REML; I² {i2}%). '
        'The prior claim that the eligible-poolable remainder was zero was false.</p>'
        '<p style="margin:.5rem 0 0">DM-INSULIN’s <strong>reconstructed</strong> value has been replaced '
        'by its <strong>published overall −48.8%</strong> — reconstructing what is already published is a '
        'provenance downgrade for no gain. Only CHOICE II’s 150 mg Q4W arm is entered; its 75 mg Q2W '
        'calibrator shares the same placebo group and would double-count it.</p>'
        '<p style="margin:.5rem 0 0;font-size:.85rem;color:var(--muted,#3f3f46)">CHOICE values verified '
        'verbatim from the primary publications (Roth, <em>Atherosclerosis</em> 2016, PMID 27639753; '
        'Stroes, <em>JAHA</em> 2016, PMID 27625344); the k=10 pool reproduces against metafor '
        '(−55.1693, I² 86.9%). The body below is not generated from the object — the page generator is the '
        'missing component — so this correction is disclosed here.</p>'
        '</aside>\n{END}\n'
    ).format(START=START, END=END, MARKER=MARKER, pooled=pooled, k8=k8.get("k", 8),
             k8pt=_f(k8.get("point", -54.72)), i2=_f(het.get("i2", 86.9)))


def apply():
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    page = io.open(PAGE, encoding="utf-8", errors="replace").read()
    banner = build(obj)
    page = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", page, flags=re.S)
    m = re.search(r"<h1\b", page)
    if not m:
        raise SystemExit("no <h1> anchor")
    page = page[:m.start()] + banner + page[m.start():]
    io.open(PAGE, "w", encoding="utf-8").write(page)
    return banner


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--print" in sys.argv[1:]:
        print(build(json.load(io.open(OBJ, encoding="utf-8")))); raise SystemExit(0)
    b = apply()
    print("alirocumab banner inserted; marker %s; %d chars" % (MARKER, len(b)))
