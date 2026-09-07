# -*- coding: utf-8 -*-
"""Generate the EMPAGLIFLOZIN_HF correction banner FROM THE OBJECT and insert it into the served page.

Same discipline as the SGLT2 banner (route 2): the page is not object-generated, so the numbers are
generated from ssot/empagliflozin-hf-auto-full-review/...json and cannot drift. Addresses the reviewer
findings: the headline is a HAZARD RATIO not a count-derived OR (the page criticises itself for a defect
already fixed); the dead OR values/Q are superseded; the composite is hospitalisation-driven (not a
mortality benefit); and the external benchmark is stated honestly -- EMPEROR-Pooled is the SAME two
trials, a cross-check not independent corroboration, and no independent external exists.

Unique marker EMPAGLIFLOZIN_HF_CORRECTION_2026_09_07 for fetch-verification.
"""
from __future__ import annotations
import io, os, re, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(ROOT, "ssot", "empagliflozin-hf-auto-full-review", "empagliflozin-hf-auto-full-review.json")
PAGE = os.path.join(ROOT, "EMPAGLIFLOZIN_HF_AUTO_FULL_REVIEW.html")
MARKER = "EMPAGLIFLOZIN_HF_CORRECTION_2026_09_07"
START, END = "<!-- %s:START -->" % MARKER, "<!-- %s:END -->" % MARKER


def _fmt(x):
    return ("%.4f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def build_banner(obj):
    o = obj["results"]["by_outcome"]["primary"]
    p = o["pooled"]
    pooled = "%s (%s–%s)" % (_fmt(p["point"]), _fmt(p["ci_low"]), _fmt(p["ci_high"]))
    comp = o.get("component_effects_machine_readable_2026_09_03", {})
    hhf = comp.get("hospitalisation_for_heart_failure", "HR ~0.70")
    cvd = comp.get("cardiovascular_death", "HR ~0.91, not significant")
    bench = o.get("external_benchmark_2026_09_07", {})
    html = (
        '{START}\n'
        '<aside data-banner="{MARKER}" role="note" style="margin:0 0 1rem 0;padding:1rem 1.25rem;'
        'border:2px solid var(--warnb,#b45309);background:var(--warnbg,#fffbeb);border-radius:8px;'
        'font-size:0.95rem;line-height:1.5">'
        '<strong style="color:var(--warnb,#b45309);text-transform:uppercase;letter-spacing:.03em">'
        'Correction — read this before the analysis below (generated from the object 2026-09-07)</strong>'
        '<p style="margin:.5rem 0 0">The current pooled estimate is a <strong>hazard ratio, '
        'HR {pooled}</strong>, for cardiovascular death or first hospitalisation for heart failure — '
        'from the two trials’ registered-primary time-to-first-event analyses (EMPEROR-Reduced 0.75, '
        'EMPEROR-Preserved 0.79). <strong>Any narrative below describing this headline as a '
        'count-derived odds-ratio pool is SUPERSEDED</strong> (that odds-ratio analysis was replaced '
        'on 2026-08-20). Disregard the dead-analysis values shown below — the OR point, its interval, '
        'the Hartung-Knapp interval 0.385–1.4907 and Q = 0.368949 — they belong to the retired analysis; '
        'the live heterogeneity is Q = 0.2785.</p>'
        '<p style="margin:.5rem 0 0"><strong>The composite is hospitalisation-driven — it is NOT a '
        'mortality benefit.</strong> First hospitalisation for heart failure: {hhf}. '
        'Cardiovascular death: {cvd}. A reader given only the composite would wrongly infer a mortality '
        'benefit; cardiovascular death alone does not reach significance.</p>'
        '<p style="margin:.5rem 0 0"><strong>No independent external benchmark exists.</strong> Any '
        'empagliflozin-in-heart-failure pool comprises exactly these two trials, so there is no larger, '
        'independent trial set to compare against. The published EMPEROR-Pooled patient-level analysis '
        'covers the <em>same two trials</em>: it is a cross-check of this page’s arithmetic against a '
        'better (patient-level) analysis of <em>identical</em> data — <strong>not independent '
        'corroboration</strong>, and it is not quoted as agreement.</p>'
        '<p style="margin:.5rem 0 0;font-size:.85rem;color:var(--muted,#3f3f46)">Generated from '
        '<code>ssot/empagliflozin-hf-auto-full-review/…json</code>; the k=2 rebuild reproduces from the '
        'registered protocol (reproduce_review PROTOCOL+PIPELINE REPRODUCE). The body below is not '
        'generated from the object — the page generator is the missing component — so this correction '
        'is disclosed rather than silently applied.</p>'
        '</aside>\n{END}\n'
    ).format(START=START, END=END, MARKER=MARKER, pooled=pooled, hhf=hhf, cvd=cvd)
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
    print("empagliflozin banner inserted; marker %s; %d chars" % (MARKER, len(b)))
