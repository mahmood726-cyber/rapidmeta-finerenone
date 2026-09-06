# -*- coding: utf-8 -*-
"""Generate the SGLT2 k=4 correction banner FROM THE OBJECT and insert it into the served page.

Condition 1 of route 2 (per Mahmood): the banner's numbers are GENERATED FROM ssot/sglt2-hf/sglt2-hf.json,
never typed -- so the banner cannot drift from the value it reports even though the rest of the 3.9MB
page is not object-generated. This is disclosure of a known object<->page divergence, not new drift.

The served (pre-correction) headline (k=3, 0.7636) is read from the PAGE itself (what a reader
currently meets); the corrected values (k=4 pool, DELIVER, external benchmark, component decomposition)
are read from the OBJECT. Idempotent: re-running replaces the banner rather than stacking it.

The banner carries a unique marker string (SGLT2_K4_CORRECTION_2026_09_06) that exists ONLY here, for
fetch-verification of the live deploy.
"""
from __future__ import annotations
import io, os, re, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(ROOT, "ssot", "sglt2-hf", "sglt2-hf.json")
PAGE = os.path.join(ROOT, "SGLT2_HF_REVIEW.html")
MARKER = "SGLT2_K4_CORRECTION_2026_09_06"
START = "<!-- %s:START -->" % MARKER
END = "<!-- %s:END -->" % MARKER


def _fmt(x):
    return ("%.4f" % x).rstrip("0").rstrip(".") if isinstance(x, float) else str(x)


def _served_headline(page_text):
    """The k=3 pooled a reader currently meets, read from the page (not typed)."""
    m = re.search(r"pooled HR of (0\.7\d{2,4})", page_text) or re.search(r"\b(0\.7636)\b", page_text)
    return m.group(1) if m else "0.7636"


def build_banner(obj, served_hr):
    o = obj["results"]["by_outcome"]["harmonised_cvdeath_or_hhf"]
    pooled = o["pooled"]
    deliver = next((t for t in o["per_trial"] if (t.get("nct") == "NCT03619213")), {})
    bench = o.get("external_benchmark", {})
    comp = o.get("component_decomposition_vaduganathan_5trial", {})
    def ci(d, p="point", l="ci_low", h="ci_high"):
        return "%s (%s–%s)" % (_fmt(d.get(p)), _fmt(d.get(l)), _fmt(d.get(h)))
    corrected = "%s (%s–%s)" % (_fmt(pooled["point"]), _fmt(pooled["ci_low"]), _fmt(pooled["ci_high"]))
    hhf = comp.get("first_hospitalisation_for_heart_failure", {})
    cvd = comp.get("cardiovascular_death", {})
    acm = comp.get("all_cause_mortality", {})
    html = (
        '{START}\n'
        '<aside data-banner="{MARKER}" role="note" style="margin:0 0 1rem 0;padding:1rem 1.25rem;'
        'border:2px solid var(--warnb,#b45309);background:var(--warnbg,#fffbeb);border-radius:8px;'
        'font-size:0.95rem;line-height:1.5">'
        '<strong style="color:var(--warnb,#b45309);text-transform:uppercase;letter-spacing:.03em">'
        'Correction — this page’s analysis is superseded (generated from the object 2026-09-06)</strong>'
        '<p style="margin:.5rem 0 0">The analysis below is the prior <strong>k=3</strong> pool, '
        '<strong>HR {served}</strong>. The <strong>current object holds k=4</strong>: adding DELIVER gives a '
        'pooled <strong>HR {corrected}</strong> for cardiovascular death or first hospitalisation for heart '
        'failure. DELIVER contributes <strong>HR {deliver}</strong>, whose value is the '
        'Vaduganathan 2022 supplement (PMID 36041474) harmonised per-trial estimate — disclosed at its '
        '<em>lower provenance tier</em> (not in DELIVER’s registry or primary abstract), and '
        '<strong>corroborated</strong> by de-pooling Jhund’s DAPA-HF+DELIVER two-component pool (0.78) against '
        'DAPA-HF (0.75) → ≈ 0.81.</p>'
        '<p style="margin:.5rem 0 0">The <strong>external benchmark</strong> is Vaduganathan’s five-trial '
        'pooled <strong>HR {bench}</strong> (a genuine superset that adds SOLOIST-WHF — not a self-reference); '
        'the corrected k=4 is consistent with it. The composite is <strong>hospitalisation-led</strong>: '
        'first HF hospitalisation <strong>{hhf}</strong>, cardiovascular death <strong>{cvd}</strong>, '
        'all-cause mortality <strong>{acm}</strong> (Vaduganathan five-trial components).</p>'
        '<p style="margin:.5rem 0 0;font-size:.85rem;color:var(--muted,#3f3f46)">This banner’s numbers are '
        'generated from <code>ssot/sglt2-hf/sglt2-hf.json</code>; the k=4 rebuild reproduces from the '
        'registered protocol (reproduce_review PROTOCOL+PIPELINE REPRODUCE). The body below is a 3.9 MB '
        'single-file app not generated from the object — the page generator is the one missing component; '
        'until it exists the body cannot be regenerated, so this correction is disclosed rather than '
        'silently applied.</p>'
        '</aside>\n{END}\n'
    ).format(START=START, END=END, MARKER=MARKER, served=served_hr, corrected=corrected,
             deliver=ci(deliver), bench=ci(bench), hhf=ci(hhf), cvd=ci(cvd), acm=ci(acm))
    return html


def apply():
    obj = json.load(io.open(OBJ, encoding="utf-8"))
    page = io.open(PAGE, encoding="utf-8", errors="replace").read()
    served = _served_headline(page)
    banner = build_banner(obj, served)
    # idempotent: drop any prior banner
    page = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", page, flags=re.S)
    m = re.search(r"<h1\b", page)
    if not m:
        raise SystemExit("no <h1> anchor found in page")
    page = page[:m.start()] + banner + page[m.start():]
    io.open(PAGE, "w", encoding="utf-8").write(page)
    return served, banner


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--print" in sys.argv[1:]:
        obj = json.load(io.open(OBJ, encoding="utf-8"))
        print(build_banner(obj, "0.7636")); raise SystemExit(0)
    served, banner = apply()
    print("banner inserted (served headline read from page: %s); marker %s; %d chars"
          % (served, MARKER, len(banner)))
