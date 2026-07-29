"""Independently verify HFREF_NMA_AUTO_FULL_REVIEW.html against the R fit.

The app's payload (script#hfref-fit-data) and this repository's R artefacts
were built by two SEPARATE code paths from the same settled fit. This gate
compares them. Agreement is therefore evidence, not a tautology: the payload
is not derived from the artefacts it is checked against.

  outputs/hfref_nma_bundle.json    covariance + arm-level table   (stage 1)
  outputs/hfref_league_table.json  105 contrasts with real CIs    (stage 2)
  outputs/hfref_multiverse.json    4 computed + 6 withdrawn       (stage 3)

Exits non-zero on any failure. Every check below was exercised against
deliberately broken input before being trusted.
"""

import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "HFREF_NMA_AUTO_FULL_REVIEW.html")
OUTDIR = os.path.join(ROOT, "outputs")
TOL = 1e-8          # the payload is serialised at 11 significant digits

FAILS, PASSES = [], []


def check(ok, msg):
    (PASSES if ok else FAILS).append(msg)
    print(("  PASS  " if ok else "  FAIL  ") + msg)


def load(n):
    with open(os.path.join(OUTDIR, n), encoding="utf-8") as fh:
        return json.load(fh)


def fit_payload(html):
    m = re.search(r'<script[^>]*id="hfref-fit-data"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("script#hfref-fit-data not found in the app")
    return json.loads(m.group(1))


def reldev(a, b):
    return abs(a - b) / max(abs(b), 1e-30)


def main():
    with open(APP, encoding="utf-8") as fh:
        html = fh.read()
    F = fit_payload(html)
    league = load("hfref_league_table.json")
    mv = load("hfref_multiverse.json")
    bundle = load("hfref_nma_bundle.json")

    print("A. ANCHOR (independently re-derived in R, stage 1/2)")
    a = F.get("anchor", {})
    check(a.get("passed") is True, "payload declares the anchor passed")
    for node, want in (("ACEI+BB+MRA", (0.59333495, 0.348, 1.011)),
                       ("ACEI+BB", (0.64459765, 0.433, 0.959))):
        got = a.get(node)
        check(got is not None and abs(got[0] - want[0]) < 1e-8
              and abs(got[1] - want[1]) < 5e-4 and abs(got[2] - want[2]) < 5e-4,
              f"{node} = {got[0]:.8f} ({got[1]:.3f}-{got[2]:.3f}) "
              f"vs {want[0]:.8f} ({want[1]:.3f}-{want[2]:.3f})")

    primary = [c for c in F["cells"] if c["cell_id"] == "OURS-STRICT"]
    check(len(primary) == 1, "exactly one OURS-STRICT primary cell")
    primary = primary[0]
    check(abs(primary["tau2"] - 0.02323609) < 1e-8,
          f"tau2 = {primary['tau2']:.8f} (0.02323609)")

    print("B. TRANSPORT (payload vs independently-built R artefacts)")
    mine = {tuple(sorted((c["treat1"], c["treat2"]))): c for c in league["contrasts"]}
    worst, at, n = 0.0, "", 0
    for c in primary["league"]:
        s = mine.get(tuple(sorted((c["t1"], c["t2"]))))
        if s is None:
            check(False, f"payload league row absent from R artefact: {c['t1']} vs {c['t2']}")
            continue
        for k in ("rr", "lo", "hi"):
            d = reldev(c[k], s[k])
            if d > worst:
                worst, at = d, f"{c['t1']} vs {c['t2']}.{k}"
        n += 1
    check(worst < TOL and n == 105,
          f"{n} league rows agree, max rel dev {worst:.3e} ({at or 'exact'})")

    mn = {x["node"]: x for x in league["node_vs_reference"]}
    wn = max(reldev(x[k], mn[x["node"]][k])
             for x in primary["node_vs_placebo"] for k in ("rr", "lo", "hi"))
    check(wn < TOL, f"{len(primary['node_vs_placebo'])} node rows agree, max rel dev {wn:.3e}")

    msrc = {c["cell_id"]: {x["node"]: x for x in c["nodes"]}
            for c in mv["cells"] if c.get("computed")}
    wm, nm = 0.0, 0
    for c in F["cells"]:
        s = msrc.get(c["cell_id"])
        check(s is not None, f"computed cell {c['cell_id']} exists in the R multiverse")
        if not s:
            continue
        for x in c["node_vs_placebo"]:
            if x["node"] in s:
                for k in ("rr", "lo", "hi"):
                    wm = max(wm, reldev(x[k], s[x["node"]][k]))
                    nm += 1
    check(wm < TOL, f"{nm} multiverse estimates across {len(F['cells'])} cells agree, max rel dev {wm:.3e}")

    print("C. COUNTS (counted, never padded)")
    for c in F["cells"]:
        check(c["estimable_pairs"] == 105 and len(c["league"]) == 105,
              f"{c['cell_id']}: estimable_pairs={c['estimable_pairs']}, league rows={len(c['league'])}")
    check(all(c["estimable_pairs"] != 44 for c in F["cells"]),
          "no cell reports the legacy padded 44")
    check(len(F["nma_config"]["treatments"]) == 15,
          f"{len(F['nma_config']['treatments'])} nodes (15)")
    check(len(F["nma_config"]["comparisons"]) == 16,
          f"{len(F['nma_config']['comparisons'])} direct edges (16)")
    check(len(F["study_contrasts"]) == 30, f"{len(F['study_contrasts'])} study contrasts (30)")

    print("D. MULTIVERSE (4 computed, 6 withdrawn, no estimate on withdrawn)")
    check(len(F["cells"]) == 4, f"{len(F['cells'])} computed cells (4)")
    check(len(F["withdrawn_cells"]) == 6, f"{len(F['withdrawn_cells'])} withdrawn cells (6)")
    check(all(w.get("estimate") is None for w in F["withdrawn_cells"]),
          "every withdrawn cell has estimate = null")
    check(all(w.get("reason") for w in F["withdrawn_cells"]),
          "every withdrawn cell states its withdrawal reason")
    check(all(w.get("coords") for w in F["withdrawn_cells"]),
          "every withdrawn cell carries its author coordinates")
    leaked = [w["cell_id"] for w in F["withdrawn_cells"]
              if re.search(r'"(rr|lo|hi|tau2)"\s*:\s*-?[0-9]', json.dumps(w))]
    check(not leaked, f"no numeric estimate leaked into a withdrawn cell {leaked or ''}")
    check(sum(1 for c in F["cells"] if c.get("tier") == "PRIMARY") == 1,
          "exactly one cell is tiered PRIMARY")

    print("E. EXTRACTION COVERAGE")
    cov = F["coverage"]
    check(cov["network_trials"] == bundle["trials"]["n_included"] == 28,
          f"network trials = {cov['network_trials']} (28)")
    check(cov["extraction_substantiated"] == cov["network_trials"],
          f"extraction substantiates {cov['extraction_substantiated']}/{cov['network_trials']} network trials")
    check(cov["arm_rows"] == bundle["trials"]["n_arms"] == 57,
          f"arm rows = {cov['arm_rows']} (57)")
    check(len(F["trials"]) == 28, f"{len(F['trials'])} trial rows")
    check(cov["pmid_verified"] + cov["pmid_missing"] == cov["network_trials"],
          f"{cov['pmid_verified']} with PMID + {cov['pmid_missing']} without == {cov['network_trials']}")
    real_missing = [t["id"] for t in F["trials"] if not t.get("pmid")]
    check(len(real_missing) == cov["pmid_missing"],
          f"declared pmid_missing={cov['pmid_missing']} matches the {len(real_missing)} rows with no PMID {real_missing}")
    ids = {t["id"] for t in F["trials"]}
    check(ids == set(bundle["trials"]["included_ids"]),
          "trial rows cover exactly the fitted network's trials")

    print("F. NO DONOR RESIDUE IN CLAIM-BEARING SLOTS")
    for bad, what in (
            ("SACUBITRIL_VALSARTAN_HF_AUTO_FULL_REVIEW", "donor app URL in JSON-LD"),
            ("published sacubitril pooled analyses", "sacubitril benchmark footnote")):
        check(bad not in html, f"no {what}")
    low = html.lower()
    for v in ("semaglutide", "liraglutide", "dulaglutide", "exenatide",
              "lixisenatide", "albiglutide", "efpeglenatide", "tirzepatide",
              "glp-1", "glp1"):
        check(v not in low, f"no GLP-1 base vocabulary: {v}")

    print("G. STRUCTURE")
    o, c = len(re.findall(r"<div[\s>]", html)), html.count("</div>")
    check(o == c, f"div balance {o}/{c}")
    ids_all = re.findall(r'\sid="([^"]+)"', html)
    dupes = sorted({i for i in ids_all if ids_all.count(i) > 1})
    check(not dupes, f"unique element ids ({len(ids_all)}){' dupes: ' + str(dupes) if dupes else ''}")
    # a bare "{{" is not a placeholder: JS template literals legitimately
    # contain ${{...}[k]} object-literal lookups. Match the token FORM instead.
    ph = re.findall(r"\{\{\s*[A-Za-z_][\w.]*\s*\}\}", html)
    ph += [p for p in ("REPLACE_ME", "__PLACEHOLDER__", "TODO_FILL") if p in html]
    check(not ph, f"no unfilled placeholder tokens {ph[:5] or ''}")
    check(not re.search(r":\s*None[,}\]]", html), "no Python None leaked into JS")
    check("switchTab(id){" in html.replace(" ", ""), "RapidMeta.switchTab is defined")
    check(len(re.findall(r'<section id="tab-[a-z]+"', html)) == 7,
          f"{len(re.findall(chr(60)+'section id=.tab-[a-z]+.', html))} tab sections (7)")

    print()
    print(f"{len(PASSES)} passed, {len(FAILS)} failed")
    if FAILS:
        print("VERDICT: FAIL")
        for f in FAILS:
            print("   - " + f)
        sys.exit(1)
    print("VERDICT: PASS")


if __name__ == "__main__":
    main()
