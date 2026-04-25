#!/usr/bin/env python3
# sentinel:skip-file
"""Tier 2 batch B: 2 final NMAs.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from clone_new_apps import clone_app, trial_entry, make_outcome_map, ROOT


def trials_block(trial_specs):
    return ",\n".join(trial_specs)


SPECS = {

    # ============ GLP1_MASH_NMA ============
    "GLP1_MASH_NMA_REVIEW.html": {
        "source": "INCRETINS_T2D_NMA_REVIEW.html",
        "title": "RapidMeta Hepatology | Incretin Therapies in MASH/NASH — NMA v1.0",
        "nct_ids": ["NCT04822181", "NCT04166773", "NCT02970942"],
        "acronyms": {
            "NCT04822181": "ESSENCE", "NCT04166773": "SYNERGY-NASH", "NCT02970942": "Newsome NAFLD",
        },
        "realData_body": trials_block([
            trial_entry("NCT04822181", "ESSENCE", "39282897", 2024, 199, 534, 88, 533, 3.18, 2.43, 4.16,
                "MASH F2-F3 with diabetes/obesity, semaglutide 2.4 mg SC weekly vs placebo (NASH resolution at 72 wk; OR; ESSENCE Part 1 interim)",
                "NASH resolution without worsening of fibrosis at week 72 (primary; ESSENCE Part 1 interim)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2410020",
                "https://clinicaltrials.gov/study/NCT04822181",
                "Source: Sanyal AJ et al. NEJM 2024;391:1859-1871 (ESSENCE Part 1 interim)."),
            trial_entry("NCT04166773", "SYNERGY-NASH", "38842432", 2024, 33, 64, 7, 65, 9.71, 3.83, 24.61,
                "MASH F2-F3, tirzepatide 15 mg SC weekly vs placebo (NASH resolution at 52 wk; OR)",
                "NASH resolution at 52 wk (primary; tirzepatide 15 mg vs placebo)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2401943",
                "https://clinicaltrials.gov/study/NCT04166773",
                "Source: Loomba R et al. NEJM 2024;391:299-310 (SYNERGY-NASH)."),
            trial_entry("NCT02970942", "Newsome NAFLD", "33185364", 2021, 59, 80, 17, 80, 10.41, 4.79, 22.62,
                "Biopsy-confirmed NASH (F1-F3), semaglutide 0.4 mg SC daily vs placebo (NASH resolution at 72 wk; OR)",
                "NASH resolution without fibrosis worsening at 72 wk (primary, semaglutide 0.4 mg dose vs placebo)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2028395",
                "https://clinicaltrials.gov/study/NCT02970942",
                "Source: Newsome PN et al. NEJM 2021;384:1113-1124 (Phase 2 NASH semaglutide)."),
        ]),
        "benchmarks_body": """{
            'NASH_RESOLUTION': [
                { label: 'ESSENCE semaglutide 2.4 mg vs placebo', citation: 'Sanyal 2024', year: 2024, measure: 'OR', estimate: 3.18, lci: 2.43, uci: 4.16, k: 1, n: 1067, scope: 'Semaglutide 2.4 mg vs placebo in MASH F2-F3; NASH resolution at 72 wk. NEJM 2024;391:1859-1871 (ESSENCE Part 1 interim).' },
                { label: 'SYNERGY-NASH tirzepatide 15 mg vs placebo', citation: 'Loomba 2024', year: 2024, measure: 'OR', estimate: 9.71, lci: 3.83, uci: 24.61, k: 1, n: 129, scope: 'Tirzepatide 15 mg vs placebo in MASH F2-F3; NASH resolution at 52 wk. NEJM 2024;391:299-310.' },
                { label: 'Newsome 2021 semaglutide 0.4 mg vs placebo', citation: 'Newsome 2021', year: 2021, measure: 'OR', estimate: 10.41, lci: 4.79, uci: 22.62, k: 1, n: 160, scope: 'Semaglutide 0.4 mg daily vs placebo in NASH F1-F3; NASH resolution at 72 wk. NEJM 2021;384:1113-1124.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("NASH_RESOLUTION"),
    },

    # ============ PAH_THERAPY_NMA ============
    "PAH_THERAPY_NMA_REVIEW.html": {
        "source": "CARDIORENAL_DKD_NMA_REVIEW.html",
        "title": "RapidMeta Pulmonology | PAH Advanced Therapy NMA (Sotatercept / Selexipag / Riociguat / Macitentan) v1.0",
        "nct_ids": ["NCT04576988", "NCT01106014", "NCT00810693", "NCT00660179"],
        "acronyms": {
            "NCT04576988": "STELLAR", "NCT01106014": "GRIPHON",
            "NCT00810693": "PATENT-1", "NCT00660179": "SERAPHIN",
        },
        "realData_body": trials_block([
            trial_entry("NCT04576988", "STELLAR", "36877098", 2023, 9, 163, 42, 160, 0.16, 0.08, 0.35,
                "PAH on background standard therapy, sotatercept vs placebo (composite clinical worsening at 24 wk; HR)",
                "Composite clinical worsening at 24 wk (key secondary; sotatercept vs placebo)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa2213558",
                "https://clinicaltrials.gov/study/NCT04576988",
                "Source: Hoeper MM et al. NEJM 2023;388:1478-1490 (STELLAR)."),
            trial_entry("NCT01106014", "GRIPHON", "26699168", 2015, 155, 574, 242, 582, 0.60, 0.46, 0.78,
                "PAH on background therapy, selexipag vs placebo (composite morbidity/mortality; HR)",
                "Composite morbidity/mortality (primary; selexipag vs placebo, mean follow-up 71 wk)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1503184",
                "https://clinicaltrials.gov/study/NCT01106014",
                "Source: Sitbon O et al. NEJM 2015;373:2522-2533 (GRIPHON)."),
            trial_entry("NCT00810693", "PATENT-1", "23883378", 2013, 23, 254, 21, 126, 0.55, 0.30, 0.99,
                "PAH treatment-naive or on ERA/prostanoid background, riociguat 2.5 mg PO TID vs placebo (composite clinical worsening at 12 wk; HR)",
                "Composite clinical worsening at 12 wk (secondary; riociguat 2.5 mg vs placebo)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1209655",
                "https://clinicaltrials.gov/study/NCT00810693",
                "Source: Ghofrani HA et al. NEJM 2013;369:330-340 (PATENT-1)."),
            trial_entry("NCT00660179", "SERAPHIN", "23984728", 2013, 116, 242, 116, 250, 0.55, 0.39, 0.76,
                "PAH (treatment-naive or on background therapy), macitentan 10 mg PO daily vs placebo (composite morbidity/mortality; HR)",
                "Composite morbidity/mortality (primary; macitentan 10 mg vs placebo, median follow-up 100 wk)",
                "https://www.nejm.org/doi/full/10.1056/NEJMoa1213917",
                "https://clinicaltrials.gov/study/NCT00660179",
                "Source: Pulido T et al. NEJM 2013;369:809-818 (SERAPHIN)."),
        ]),
        "benchmarks_body": """{
            'COMPOSITE_WORSENING': [
                { label: 'STELLAR sotatercept vs placebo', citation: 'Hoeper 2023', year: 2023, measure: 'HR', estimate: 0.16, lci: 0.08, uci: 0.35, k: 1, n: 323, scope: 'Sotatercept vs placebo on background PAH therapy; composite worsening at 24 wk. NEJM 2023;388:1478-1490.' },
                { label: 'GRIPHON selexipag vs placebo', citation: 'Sitbon 2015', year: 2015, measure: 'HR', estimate: 0.60, lci: 0.46, uci: 0.78, k: 1, n: 1156, scope: 'Selexipag vs placebo; composite morbidity/mortality. NEJM 2015;373:2522-2533.' },
                { label: 'SERAPHIN macitentan vs placebo', citation: 'Pulido 2013', year: 2013, measure: 'HR', estimate: 0.55, lci: 0.39, uci: 0.76, k: 1, n: 492, scope: 'Macitentan 10 mg vs placebo; composite morbidity/mortality. NEJM 2013;369:809-818.' },
                { label: 'PATENT-1 riociguat vs placebo', citation: 'Ghofrani 2013', year: 2013, measure: 'HR', estimate: 0.55, lci: 0.30, uci: 0.99, k: 1, n: 380, scope: 'Riociguat 2.5 mg TID vs placebo; composite clinical worsening at 12 wk. NEJM 2013;369:330-340.' }
            ]
        }""",
        "outcome_map_body": make_outcome_map("COMPOSITE_WORSENING"),
    },

}


def main():
    ok = fail = 0
    for target_name, spec in SPECS.items():
        source = ROOT / spec["source"]
        target = ROOT / target_name
        if not source.exists():
            print(f"FAIL {target_name}: source missing")
            fail += 1; continue
        r = clone_app(source, target, spec)
        print(r)
        if r.startswith("OK"): ok += 1
        else: fail += 1
    print(f"\nTier 2 batch B: {ok} ok / {fail} fail")


if __name__ == "__main__":
    main()
