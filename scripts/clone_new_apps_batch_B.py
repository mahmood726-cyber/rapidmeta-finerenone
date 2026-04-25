#!/usr/bin/env python3
# sentinel:skip-file
"""Tier 1 batch B: 4 more post-2015 pairwise apps.
Reuses clone_new_apps.py utilities.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from clone_new_apps import clone_app, trial_entry, make_outcome_map, ROOT

SPECS = {

    # ============ SOTATERCEPT_PAH ============
    "SOTATERCEPT_PAH_REVIEW.html": {
        "source": "MAVACAMTEN_HCM_REVIEW.html",
        "title": "RapidMeta Cardiology | Sotatercept (Activin Signaling Inhibitor) in PAH v1.0",
        "nct_ids": ["NCT04576988"],
        "acronyms": {"NCT04576988": "STELLAR"},
        "realData_body": trial_entry(
            "NCT04576988", "STELLAR", "36877098", 2023, 9, 163, 42, 160, 0.16, 0.08, 0.35,
            "PAH on background standard therapy, sotatercept vs placebo (composite clinical worsening at 24 wk, HR)",
            "Composite clinical worsening (death, lung transplantation, hospitalization >24 h for PAH, listing for transplant, atrial septostomy, or PAH worsening) at 24 wk (key secondary, HR)",
            "https://www.nejm.org/doi/full/10.1056/NEJMoa2213558",
            "https://clinicaltrials.gov/study/NCT04576988",
            "Source: Hoeper MM et al. NEJM 2023;388:1478-1490 (STELLAR)."
        ),
        "benchmarks_body": """{
            'CLINICAL_WORSENING': [
                { label: 'STELLAR sotatercept vs placebo', citation: 'Hoeper 2023', year: 2023, measure: 'HR', estimate: 0.16, lci: 0.08, uci: 0.35, k: 1, n: 323, scope: 'Sotatercept vs placebo on background PAH therapy; composite clinical worsening at 24 wk. NEJM 2023;388:1478-1490.' },
                { label: 'GRIPHON selexipag vs placebo', citation: 'Sitbon 2015', year: 2015, measure: 'HR', estimate: 0.60, lci: 0.46, uci: 0.78, k: 1, n: 1156, scope: 'Selexipag vs placebo in PAH; composite morbidity/mortality. NEJM 2015;373:2522-2533. (Class comparator.)' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("CLINICAL_WORSENING"),
    },

    # ============ VORASIDENIB_GLIOMA ============
    "VORASIDENIB_GLIOMA_REVIEW.html": {
        "source": "PARP_OVARIAN_REVIEW.html",
        "title": "RapidMeta Onco | Vorasidenib (IDH1/2 Inhibitor) in IDH-Mutant Low-Grade Glioma v1.0",
        "nct_ids": ["NCT04164901"],
        "acronyms": {"NCT04164901": "INDIGO"},
        "realData_body": trial_entry(
            "NCT04164901", "INDIGO", "37272516", 2023, 28, 168, 67, 163, 0.39, 0.27, 0.56,
            "IDH1/2-mutant grade 2 oligodendroglioma or astrocytoma post-resection, vorasidenib 40 mg PO daily vs placebo (PFS HR)",
            "Imaging-based progression-free survival (primary, IDH-mutant grade 2 glioma, central radiology review)",
            "https://www.nejm.org/doi/full/10.1056/NEJMoa2304194",
            "https://clinicaltrials.gov/study/NCT04164901",
            "Source: Mellinghoff IK et al. NEJM 2023;389:589-601 (INDIGO)."
        ),
        "benchmarks_body": """{
            'IMAGING_PFS': [
                { label: 'INDIGO vorasidenib vs placebo', citation: 'Mellinghoff 2023', year: 2023, measure: 'HR', estimate: 0.39, lci: 0.27, uci: 0.56, k: 1, n: 331, scope: 'Vorasidenib vs placebo in IDH1/2-mutant grade 2 glioma post-resection; imaging-based PFS. NEJM 2023;389:589-601.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("IMAGING_PFS"),
    },

    # ============ DONANEMAB_AD_SOLO ============
    "DONANEMAB_AD_SOLO_REVIEW.html": {
        "source": "ANTIAMYLOID_AD_REVIEW.html",
        "title": "RapidMeta Neurology | Donanemab (Anti-Amyloid mAb) in Early Alzheimer's Disease v1.0",
        "nct_ids": ["NCT04437511"],
        "acronyms": {"NCT04437511": "TRAILBLAZER-ALZ 2"},
        "realData_body": trial_entry(
            "NCT04437511", "TRAILBLAZER-ALZ 2", "37459141", 2023, 246, 860, 297, 876, 0.84, 0.71, 0.99,
            "Early symptomatic AD with confirmed amyloid + low/medium tau, donanemab 700-1400 mg IV Q4W vs placebo (CDR-SB worsening events at 76 wk, HR proxy)",
            "Disease progression (composite of CDR-SB worsening, MCI->AD conversion, or treatment discontinuation for clinical decline) at 76 wk; primary continuous endpoint was iADRS slope",
            "https://jamanetwork.com/journals/jama/fullarticle/2807533",
            "https://clinicaltrials.gov/study/NCT04437511",
            "Source: Sims JR et al. JAMA 2023;330:512-527 (TRAILBLAZER-ALZ 2). Primary endpoint was iADRS slope (LSM diff +3.25, 95% CI 1.88-4.62 favoring donanemab); count surrogates approximate."
        ),
        "benchmarks_body": """{
            'COG_DECLINE': [
                { label: 'TRAILBLAZER-ALZ 2 donanemab (low/med tau)', citation: 'Sims 2023', year: 2023, measure: 'HR', estimate: 0.84, lci: 0.71, uci: 0.99, k: 1, n: 1736, scope: 'Donanemab vs placebo in early AD with low/medium tau; cognitive-decline composite at 76 wk. JAMA 2023;330:512-527. (Primary was iADRS continuous; HR is approximate from KM curves.)' },
                { label: 'CLARITY-AD lecanemab vs placebo', citation: 'van Dyck 2023', year: 2023, measure: 'MD', estimate: -0.45, lci: -0.67, uci: -0.23, k: 1, n: 1795, scope: 'Lecanemab vs placebo in early AD; CDR-SB change at 18 mo. NEJM 2023;388:9-21. (Class comparator.)' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("COG_DECLINE"),
    },

    # ============ VOCLOSPORIN_LN ============
    "VOCLOSPORIN_LN_REVIEW.html": {
        "source": "ANIFROLUMAB_SLE_REVIEW.html",
        "title": "RapidMeta Rheum/Renal | Voclosporin (Calcineurin Inhibitor) in Lupus Nephritis v1.0",
        "nct_ids": ["NCT03021499"],
        "acronyms": {"NCT03021499": "AURORA 1"},
        "realData_body": trial_entry(
            "NCT03021499", "AURORA 1", "33971155", 2021, 73, 179, 40, 178, 2.36, 1.46, 3.81,
            "Active lupus nephritis class III/IV/V, voclosporin 23.7 mg PO BID + MMF + steroid taper vs placebo + MMF + steroid taper (complete renal response at 52 wk, OR)",
            "Complete renal response at week 52 (primary, composite UPCR <=0.5 mg/mg + eGFR >=60 or no decrease >20% + low-dose steroid + no rescue therapy)",
            "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)00578-X/fulltext",
            "https://clinicaltrials.gov/study/NCT03021499",
            "Source: Rovin BH et al. Lancet 2021;397:2070-2080 (AURORA 1)."
        ),
        "benchmarks_body": """{
            'RENAL_RESPONSE': [
                { label: 'AURORA 1 voclosporin + MMF vs MMF alone', citation: 'Rovin 2021', year: 2021, measure: 'OR', estimate: 2.65, lci: 1.64, uci: 4.27, k: 1, n: 357, scope: 'Voclosporin + MMF vs placebo + MMF in active lupus nephritis; complete renal response at 52 wk. Lancet 2021;397:2070-2080.' },
                { label: 'BLISS-LN belimumab + standard care', citation: 'Furie 2020', year: 2020, measure: 'OR', estimate: 1.55, lci: 1.07, uci: 2.25, k: 1, n: 448, scope: 'Belimumab + standard induction/maintenance vs placebo in active lupus nephritis; primary efficacy renal response at 104 wk. NEJM 2020;383:1117-1128. (Class comparator.)' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("RENAL_RESPONSE"),
    },

}


def main():
    ok = fail = skip = 0
    for target_name, spec in SPECS.items():
        source = ROOT / spec["source"]
        target = ROOT / target_name
        if not source.exists():
            print(f"FAIL {target_name}: source missing")
            fail += 1
            continue
        r = clone_app(source, target, spec)
        print(r)
        if r.startswith("OK"):
            ok += 1
        elif r.startswith("SKIP"):
            skip += 1
        else:
            fail += 1
    print(f"\nbatch B: {ok} ok / {skip} skip / {fail} fail")


if __name__ == "__main__":
    main()
