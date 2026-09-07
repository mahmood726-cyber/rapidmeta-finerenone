# -*- coding: utf-8 -*-
"""Minimal in-place correction disclosure for the PROTECTED ARNI page (no regeneration).

Per Mahmood: ARNI_HF_REVIEW.html is a protected page -- targeted correction only, no regeneration, a
MINIMAL in-place disclosure. This inserts one small note (generated from the object, numbers never
typed) before <h1>, disclosing the k=4 -> k=5 PIONEER correction, that the finding MOVES (gate 16),
and that the formal GRADE is withdrawn to PENDING. Marker ARNI_K5_PIONEER_CORRECTION_2026_09_07.
"""
from __future__ import annotations
import io, os, re, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(ROOT, "ssot", "arni-hfref", "arni-hfref.json")
PAGE = os.path.join(ROOT, "ARNI_HF_REVIEW.html")
MARKER = "ARNI_K5_PIONEER_CORRECTION_2026_09_07"
START, END = "<!-- %s:START -->" % MARKER, "<!-- %s:END -->" % MARKER


def _fmt(x):
    return ("%.3f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def build(obj):
    o = obj["results"]["by_outcome"]["cvdeath_or_hfh_first"]
    am = o["k5_amendment_2026_09_07"]
    k5 = am["k5_pool"]
    wald = "%s (%s–%s)" % (_fmt(k5["point"]), _fmt(k5["wald_ci"][0]), _fmt(k5["wald_ci"][1]))
    hksj = "%s–%s" % (_fmt(k5["hksj_ci"][0]), _fmt(k5["hksj_ci"][1]))
    k4 = o.get("pooled", {})  # the object's headline stays k=4, consistent with its panels
    return (
        '{START}\n'
        '<aside data-banner="{MARKER}" role="note" style="margin:0 0 1rem 0;padding:.9rem 1.1rem;'
        'border:2px solid var(--warnb,#b45309);background:var(--warnbg,#fffbeb);border-radius:8px;'
        'font-size:.93rem;line-height:1.5">'
        '<strong style="color:var(--warnb,#b45309);text-transform:uppercase;letter-spacing:.03em">'
        'Correction (generated from the object 2026-09-07)</strong>'
        '<p style="margin:.4rem 0 0">PIONEER-HF was previously excluded on OUTCOME — a defect, now fixed. '
        'Its CV-death-or-HF-rehospitalisation result, <strong>HR 0.58 (0.39–0.87)</strong> (Morrow, '
        '<em>Circulation</em> 2019, PMID 30955360), is added, making this <strong>k=5</strong>. The pooled '
        'estimate moves from k=4 {k4pt} to <strong>HR {wald}</strong> (Wald, REML).</p>'
        '<p style="margin:.4rem 0 0"><strong>The finding moves, and both intervals are reported.</strong> '
        'The Wald interval now <strong>excludes 1</strong> (a significant benefit); the Hartung-Knapp '
        'interval — the honest one at k=5 with I² ≈ 20% — is <strong>{hksj}</strong> and still '
        '<strong>includes 1</strong>. The conclusion is interval-dependent.</p>'
        '<p style="margin:.4rem 0 0">PIONEER is stabilised <em>acute decompensated</em> HFrEF; under this '
        'review’s eligibility it belongs, and any future exclusion must be on <strong>population, not '
        'outcome</strong>. The formal <strong>GRADE is withdrawn to PENDING</strong>: ANSWER-HF and PIONEER '
        'are unadjudicated, so a certainty rating has no basis yet.</p>'
        '</aside>\n{END}\n'
    ).format(START=START, END=END, MARKER=MARKER, wald=wald, hksj=hksj, k4pt=_fmt(k4.get("point", 0.8715)))


def apply():
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    page = io.open(PAGE, encoding="utf-8", errors="replace").read()
    note = build(obj)
    page = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", page, flags=re.S)
    m = re.search(r"<h1\b", page)
    if not m:
        raise SystemExit("no <h1> anchor")
    page = page[:m.start()] + note + page[m.start():]
    io.open(PAGE, "w", encoding="utf-8").write(page)
    return note


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--print" in sys.argv[1:]:
        print(build(json.load(io.open(OBJ, encoding="utf-8")))); raise SystemExit(0)
    n = apply()
    print("ARNI minimal disclosure inserted; marker %s; %d chars" % (MARKER, len(n)))
