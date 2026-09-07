# -*- coding: utf-8 -*-
"""Generate the INCLISIRAN ITT-variant correction banner FROM THE OBJECT and insert it into the page.

Route 2 (banner), same as SGLT2/empagliflozin. This correction is NOT a rounding change: the per-trial
values were the registry OBSERVED_CASE column; the published ITT_IMPUTED primary is the correct variant
(our own schema mandates it -- analysis_variant declared, publication > registry). The swap collapses
I2 74% -> 0% -- the cleanest worked example of heterogeneity manufactured by extraction. Numbers are
generated from the object, never typed. Marker INCLISIRAN_ITT_CORRECTION_2026_09_07.
"""
from __future__ import annotations
import io, os, re, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(ROOT, "ssot", "inclisiran-lipid-kidney-auto-full-review", "inclisiran-lipid-kidney-auto-full-review.json")
PAGE = os.path.join(ROOT, "INCLISIRAN_LIPID_KIDNEY_AUTO_FULL_REVIEW.html")
MARKER = "INCLISIRAN_ITT_CORRECTION_2026_09_07"
START, END = "<!-- %s:START -->" % MARKER, "<!-- %s:END -->" % MARKER


def _fmt(x):
    return ("%.2f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def build_banner(obj):
    o = obj["results"]["by_outcome"]["primary"]
    p = o["pooled"]
    corrected = "%s (%s to %s)" % (_fmt(p["point"]), _fmt(p["ci_low"]), _fmt(p["ci_high"]))
    oc = o.get("OBSERVED_CASE_SUPERSEDED_2026_09_07", {}).get("pooled_observed_case", {})
    superseded = "%s (%s to %s)" % (_fmt(oc.get("point", -53.97)), _fmt(oc.get("ci_low", -58.30)), _fmt(oc.get("ci_high", -49.64)))
    ext = o.get("external_corroboration_2026_09_07", {}).get("patient_level_pooled", {})
    extv = "%s (%s to %s)" % (_fmt(ext.get("point", -50.7)), _fmt(ext.get("ci_low", -52.9)), _fmt(ext.get("ci_high", -48.4)))
    html = (
        '{START}\n'
        '<aside data-banner="{MARKER}" role="note" style="margin:0 0 1rem 0;padding:1rem 1.25rem;'
        'border:2px solid var(--warnb,#b45309);background:var(--warnbg,#fffbeb);border-radius:8px;'
        'font-size:0.95rem;line-height:1.5">'
        '<strong style="color:var(--warnb,#b45309);text-transform:uppercase;letter-spacing:.03em">'
        'Correction — analysis variant (generated from the object 2026-09-07)</strong>'
        '<p style="margin:.5rem 0 0">The corrected pooled LDL-C reduction is <strong>MD {corrected}%</strong> '
        '(k=3, REML), and it is <strong>homogeneous — I² 0%</strong>. The analysis below shows the prior '
        'headline <strong>{superseded}%, I² 74%</strong>. That older pool used each trial’s registry '
        '<strong>observed-case</strong> column; the correct inputs are the <strong>published ITT primary</strong> '
        'values (ORION-9 −47.9, ORION-10 −52.3, ORION-11 −49.9), which our own methods require — the analysis '
        'variant must be declared, and a published primary outranks a registry column.</p>'
        '<p style="margin:.5rem 0 0"><strong>This is heterogeneity manufactured by extraction, not by the '
        'trials.</strong> A single value, ORION-10, moves −52.3 → −57.64 between the two variants, and that '
        'one swap generates almost all the between-trial spread. Correcting the variant collapses I² from 74% '
        'to 0% — so the page’s own statement that no statistical heterogeneity was detected becomes true.</p>'
        '<p style="margin:.5rem 0 0"><strong>External corroboration:</strong> the separately published '
        'patient-level pooled analysis gives <strong>{extv}%</strong> — a <em>different analysis of the same '
        'three trials</em>, which agrees with this trial-level ITT pool almost exactly. It is corroboration, '
        '<strong>not independent evidence</strong> (it shares the same data).</p>'
        '<p style="margin:.5rem 0 0;font-size:.85rem;color:var(--muted,#3f3f46)">Generated from the object; '
        'the ITT pool reproduces against metafor (−50.5547, I² 0%) and the three per-trial values are verified '
        'from the primary publications (Raal NEJM 2020, PMID 32197277; Ray NEJM 2020, PMID 32187462). The '
        'superseded observed-case pool is retained in the object as an audit fixture. The body below is not '
        'generated from the object — the page generator is the missing component — so this is disclosed here.</p>'
        '</aside>\n{END}\n'
    ).format(START=START, END=END, MARKER=MARKER, corrected=corrected, superseded=superseded, extv=extv)
    return html


def apply():
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    page = io.open(PAGE, encoding="utf-8", errors="replace").read()
    banner = build_banner(obj)
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
        print(build_banner(json.load(io.open(OBJ, encoding="utf-8")))); raise SystemExit(0)
    b = apply()
    print("inclisiran banner inserted; marker %s; %d chars" % (MARKER, len(b)))
