#!/usr/bin/env python
"""
Generate v12 upgrades for ATTR_CM_REVIEW.html and INCRETIN_HFpEF_REVIEW.html
by cloning BEMPEDOIC_ACID_REVIEW.html and replacing trial data.
"""

import re
import os
import json
import shutil
import sys

# Import the transform function and helpers from the original generator
sys.path.insert(0, r"C:\Users\user\Downloads\Finrenone")

TEMPLATE_PATH = r"C:\Users\user\Downloads\Finrenone\BEMPEDOIC_ACID_REVIEW.html"
OUTPUT_DIR = r"C:\Users\user\Downloads\Finrenone"


def escape_js_str(s):
    if not s:
        return ""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")


# ============================================================
# APP DEFINITIONS
# ============================================================

APPS = [
    # ── 1. ATTR-CM (Transthyretin Cardiac Amyloidosis) ──
    {
        "filename": "ATTR_CM_REVIEW.html",
        "title_short": "ATTR-CM Therapies",
        "title_long": "Therapies for Transthyretin Amyloid Cardiomyopathy (ATTR-CM): A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "ATTR-CM Therapies",
        "drug_name_lower": "attr-cm therapies",
        "drug_regex_pattern": r"\btafamidis\b|\bacoramidis\b|\bvutrisiran\b|\bpatisiran\b|\battr\b|\binotersen\b",
        "drug_class": "ATTR-CM Therapy",
        "va_heading": "ATTR-CM: Stabilizers, RNAi & Antisense",
        "nyt_heading": "The ATTR-CM Treatment Evidence",
        "storage_key": "attr_cm",
        "protocol": {
            "pop": "Adults with Transthyretin Amyloid Cardiomyopathy (ATTR-CM), wild-type or hereditary",
            "int": "TTR Stabilizer (Tafamidis, Acoramidis), RNAi (Vutrisiran), or Antisense (Patisiran)",
            "comp": "Placebo",
            "out": "All-Cause Mortality",
            "subgroup": "Drug class (Stabilizer vs RNAi vs Antisense), TTR variant (wild-type vs hereditary), NYHA class",
            "secondary": "Cardiovascular hospitalization; 6MWD change; NT-proBNP change; quality of life (KCCQ)",
        },
        "search_term": "transthyretin amyloid cardiomyopathy",
        "search_term_ctgov": "transthyretin AND cardiac amyloidosis",
        "effect_measure": "HR",
        "effect_measure_buttons": "HR",
        "population_desc": "Adults with ATTR-CM (wild-type or hereditary)",
        "eligibility_intervention": "TTR Stabilizer, RNAi Silencer, or Antisense Oligonucleotide as primary experimental drug",
        "eligibility_intervention_exclude": "Non-cardiac ATTR (polyneuropathy-only); gene therapy; diflunisal (off-label); non-randomized studies",
        "eligibility_participants": "Adults >=18 years with confirmed ATTR-CM (biopsy or nuclear scintigraphy)",
        "nct_acronyms": {
            "NCT01994889": "ATTR-ACT",
            "NCT03860935": "ATTRibute-CM",
            "NCT05534659": "HELIOS-B",
            "NCT03997383": "APOLLO-B",
        },
        "auto_include_ids": ["NCT01994889", "NCT03860935", "NCT05534659", "NCT03997383"],
        "known_trial_aliases": {
            "NCT01994889": ["attr-act", "attr act", "tafamidis"],
            "NCT03860935": ["attribute-cm", "attribute cm", "acoramidis"],
            "NCT05534659": ["helios-b", "helios b", "vutrisiran"],
            "NCT03997383": ["apollo-b", "apollo b", "patisiran cardiac"],
        },
        "trials": {
            "NCT01994889": {
                "name": "ATTR-ACT", "phase": "III", "year": 2018,
                "tE": 78, "tN": 264, "cE": 76, "cN": 177, "group": "ATTR-CM (mixed)",
                "publishedHR": 0.70, "hrLCI": 0.51, "hrUCI": 0.96,
                "baseline": {"n": 441, "age": 74.5, "female": 10.0, "wtATTR": 76.0, "nyha_III": 31.8},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "All-cause mortality", "tE": 78, "cE": 76, "type": "PRIMARY", "pubHR": 0.70, "pubHR_LCI": 0.51, "pubHR_UCI": 0.96},
                    {"shortLabel": "CVH", "title": "CV-related hospitalization (frequency)", "tE": 138, "cE": 107, "type": "SECONDARY", "pubHR": 0.68, "pubHR_LCI": 0.56, "pubHR_UCI": 0.81},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2018; 379:1007-1016",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1805689",
                "evidence": [
                    {"label": "All-Cause Mortality", "source": "Maurer MS et al. NEJM 2018; 379:1007-1016 (Table 2)", "text": "All-cause mortality occurred in 78 of 264 (29.5%) tafamidis vs 76 of 177 (42.9%) placebo patients (HR 0.70; 95% CI, 0.51-0.96). Tafamidis 80 mg and 20 mg were pooled. 30-month follow-up.", "highlights": ["78", "264", "76", "177", "0.70"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1805689"},
                    {"label": "CV Hospitalization", "source": "Maurer MS et al. NEJM 2018; 379:1007-1016", "text": "CV-related hospitalizations: 0.48 per year with tafamidis vs 0.70 per year with placebo (rate ratio 0.68; 95% CI, 0.56-0.81; P<0.001).", "highlights": ["0.48", "0.70", "0.68"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa1805689"},
                ],
            },
            "NCT03860935": {
                "name": "ATTRibute-CM", "phase": "III", "year": 2024,
                "tE": 79, "tN": 409, "cE": 52, "cN": 202, "group": "ATTR-CM (mixed)",
                "publishedHR": 0.72, "hrLCI": 0.51, "hrUCI": 1.02,
                "baseline": {"n": 632, "age": 77.0, "female": 8.5, "wtATTR": 82.0, "nyha_III": 29.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "All-cause mortality", "tE": 79, "cE": 52, "type": "PRIMARY", "pubHR": 0.72, "pubHR_LCI": 0.51, "pubHR_UCI": 1.02},
                    {"shortLabel": "CVH", "title": "CV hospitalization or urgent CV visit", "tE": 120, "cE": 84, "type": "SECONDARY", "pubHR": 0.60, "pubHR_LCI": 0.45, "pubHR_UCI": 0.79},
                ],
                "rob": ["low", "low", "some", "low", "low"],
                "snippet": "N Engl J Med 2024; 390:132-142",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2305434",
                "evidence": [
                    {"label": "All-Cause Mortality", "source": "Gillmore JD et al. NEJM 2024; 390:132-142", "text": "All-cause mortality: 79 of 409 (19.3%) in acoramidis group vs 52 of 202 (25.7%) in placebo group (HR 0.72; 95% CI, 0.51-1.02; P=0.065). Hierarchical win-ratio analysis was co-primary.", "highlights": ["79", "409", "52", "202", "0.72"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2305434"},
                ],
            },
            "NCT05534659": {
                "name": "HELIOS-B", "phase": "III", "year": 2024,
                "tE": 53, "tN": 326, "cE": 79, "cN": 329, "group": "ATTR-CM (mixed)",
                "publishedHR": 0.67, "hrLCI": 0.47, "hrUCI": 0.95,
                "baseline": {"n": 655, "age": 75.0, "female": 7.5, "wtATTR": 80.0, "nyha_III": 26.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "All-cause mortality", "tE": 53, "cE": 79, "type": "PRIMARY", "pubHR": 0.67, "pubHR_LCI": 0.47, "pubHR_UCI": 0.95},
                    {"shortLabel": "CVH", "title": "Recurrent CV events", "tE": 98, "cE": 134, "type": "SECONDARY", "pubHR": 0.72, "pubHR_LCI": 0.56, "pubHR_UCI": 0.93},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2024; 391:2113-2123",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2404584",
                "evidence": [
                    {"label": "All-Cause Mortality + Recurrent CV Events", "source": "Fontana M et al. NEJM 2024", "text": "In the overall population, vutrisiran reduced all-cause mortality (53/326 [16.3%] vs 79/329 [24.0%]; HR 0.67; 95% CI, 0.47-0.95) and recurrent CV events (HR 0.72; 95% CI, 0.56-0.93; P=0.01).", "highlights": ["53", "326", "79", "329", "0.67"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2404584"},
                ],
            },
            "NCT03997383": {
                "name": "APOLLO-B", "phase": "III", "year": 2022,
                "tE": 10, "tN": 181, "cE": 10, "cN": 179, "group": "ATTR-CM (mixed)",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 360, "age": 75.0, "female": 8.0, "wtATTR": 83.0, "nyha_III": 28.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "All-cause mortality", "tE": 10, "cE": 10, "type": "EXPLORATORY"},
                    {"shortLabel": "6MWD", "title": "Change in 6MWD from baseline", "tE": None, "cE": None, "type": "SECONDARY"},
                ],
                "rob": ["low", "low", "some", "low", "low"],
                "snippet": "Circulation 2023; 148:1403-1413",
                "sourceUrl": "https://doi.org/10.1161/CIRCULATIONAHA.123.066353",
                "evidence": [
                    {"label": "Functional Capacity", "source": "Berk JL et al. Circulation 2023", "text": "Patisiran stabilized 6MWD and NT-proBNP vs placebo in ATTR-CM patients at 12 months. All-cause mortality was 10/181 (5.5%) vs 10/179 (5.6%), underpowered for this endpoint. Primary endpoint was 6MWD change.", "highlights": ["10", "181", "10", "179"], "sourceUrl": "https://doi.org/10.1161/CIRCULATIONAHA.123.066353"},
                ],
            },
        },
        "benchmarks": {
            "MACE": [
                {"label": "Garcia-Pavia et al. meta-analysis", "citation": "Garcia-Pavia 2024", "year": 2024, "measure": "RR", "estimate": 0.72, "lci": 0.58, "uci": 0.88, "k": 4, "n": 2088, "scope": "ATTR-CM disease-modifying therapies pooled (ACM)"},
            ],
        },
        "ctgov_registry": {},
        "nma_ids": ["NCT01994889", "NCT03860935", "NCT05534659", "NCT03997383"],
        "nma_label": "ATTR-CM Therapies vs Placebo",
        "nma_indirect_label": "Stabilizers vs RNAi Silencers (Indirect)",
    },

    # ── 2. Incretin-Based Therapies in HFpEF ──
    {
        "filename": "INCRETIN_HFpEF_REVIEW.html",
        "title_short": "Incretin Therapies in HFpEF",
        "title_long": "Incretin-Based Therapies (GLP-1 RA, GIP/GLP-1 RA) for Heart Failure with Preserved Ejection Fraction: A Living Systematic Review and Meta-Analysis of Randomized Controlled Trials",
        "drug_name": "Incretin-Based Therapies",
        "drug_name_lower": "incretin-based therapies",
        "drug_regex_pattern": r"\bsemaglutide\b|\btirzepatide\b|\bglp-?1\b|\bincretin\b|\bgip\b|\bmounjaro\b|\bwegovy\b|\bozempic\b",
        "drug_class": "Incretin-Based Therapy",
        "va_heading": "Incretin Therapies in HFpEF with Obesity",
        "nyt_heading": "The Incretin HFpEF Evidence",
        "storage_key": "incretin_hfpef",
        "protocol": {
            "pop": "Adults with HFpEF (EF >=45%), BMI >=30, NYHA Class II-IV",
            "int": "Incretin-Based Therapies (Semaglutide 2.4 mg, Tirzepatide 15 mg)",
            "comp": "Placebo",
            "out": "KCCQ-CSS Change from Baseline (Co-Primary)",
            "subgroup": "Drug class (GLP-1 RA vs GIP/GLP-1 RA), Diabetes status (T2DM vs no DM), Baseline BMI",
            "secondary": "Body weight change; 6MWD; CRP; worsening HF events; CV death or WHF composite",
        },
        "search_term": "semaglutide tirzepatide heart failure",
        "search_term_ctgov": "incretin AND heart failure AND preserved ejection fraction",
        "effect_measure": "HR",
        "effect_measure_buttons": "HR",
        "population_desc": "Adults with HFpEF and obesity (BMI >=30)",
        "eligibility_intervention": "Incretin-based therapy (GLP-1 RA or GIP/GLP-1 RA) as primary experimental drug",
        "eligibility_intervention_exclude": "Incretin therapy for T2DM without HFpEF; weight management trials without HF endpoint; open-label extensions",
        "eligibility_participants": "Adults >=18 years with HFpEF (EF >=45%), BMI >=30, NYHA II-IV",
        "nct_acronyms": {
            "NCT04788511": "STEP-HFpEF",
            "NCT04916470": "STEP-HFpEF DM",
            "NCT04847557": "SUMMIT",
        },
        "auto_include_ids": ["NCT04788511", "NCT04916470", "NCT04847557"],
        "known_trial_aliases": {
            "NCT04788511": ["step-hfpef", "step hfpef"],
            "NCT04916470": ["step-hfpef dm", "step hfpef dm", "step-hfpef-dm"],
            "NCT04847557": ["summit", "summit trial"],
        },
        "trials": {
            "NCT04788511": {
                "name": "STEP-HFpEF", "phase": "III", "year": 2023,
                "tE": 1, "tN": 263, "cE": 12, "cN": 266, "group": "HFpEF no DM",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 529, "age": 69.0, "female": 44.7, "bmi": 37.8, "lvef": 57.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "KCCQ-CSS change from baseline (points)", "tE": 1, "cE": 12, "type": "CO-PRIMARY", "md": 7.8, "se": 2.2449},
                    {"shortLabel": "BW", "title": "Body weight change (%)", "tE": None, "cE": None, "type": "CO-PRIMARY", "md": -10.7, "se": 0.6378},
                    {"shortLabel": "6MWD", "title": "6-minute walk distance (m)", "tE": None, "cE": None, "type": "SECONDARY", "md": 20.3, "se": 6.5816},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2023; 389:1069-1084",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2306963",
                "evidence": [
                    {"label": "Co-Primary: KCCQ-CSS", "source": "Kosiborod MN et al. NEJM 2023;389:1069-1084, Table 2", "text": "Change from baseline in KCCQ-CSS at 52 weeks: semaglutide +16.6 vs placebo +8.7 points (ETD 7.8; 95% CI 3.4 to 12.2; P<0.001).", "highlights": ["7.8", "3.4", "12.2", "P<0.001"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2306963"},
                    {"label": "Co-Primary: Body Weight", "source": "Kosiborod MN et al. NEJM 2023;389:1069-1084, Table 2", "text": "Body weight change at 52 weeks: semaglutide -13.3% vs placebo -2.6% (ETD -10.7%; 95% CI -11.9 to -9.4; P<0.001).", "highlights": ["-10.7%", "-13.3%", "-2.6%", "P<0.001"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2306963"},
                    {"label": "Worsening HF Events", "source": "Kosiborod MN et al. NEJM 2023;389:1069-1084", "text": "Worsening HF events: 1 (0.4%) with semaglutide vs 12 (4.5%) with placebo.", "highlights": ["1 (0.4%)", "12 (4.5%)"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2306963"},
                ],
            },
            "NCT04916470": {
                "name": "STEP-HFpEF DM", "phase": "III", "year": 2024,
                "tE": 7, "tN": 310, "cE": 18, "cN": 306, "group": "HFpEF + T2DM",
                "publishedHR": None, "hrLCI": None, "hrUCI": None,
                "baseline": {"n": 616, "age": 69.0, "female": 42.4, "bmi": 36.7, "lvef": 57.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "KCCQ-CSS change from baseline (points)", "tE": 7, "cE": 18, "type": "CO-PRIMARY", "md": 7.3, "se": 1.6071},
                    {"shortLabel": "BW", "title": "Body weight change (%)", "tE": None, "cE": None, "type": "CO-PRIMARY", "md": -6.4, "se": 0.6122},
                    {"shortLabel": "6MWD", "title": "6-minute walk distance (m)", "tE": None, "cE": None, "type": "SECONDARY", "md": 14.3, "se": 5.4082},
                ],
                "rob": ["low", "low", "low", "low", "low"],
                "snippet": "N Engl J Med 2024; 390:1394-1407",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2313917",
                "evidence": [
                    {"label": "Co-Primary: KCCQ-CSS", "source": "Kosiborod MN et al. NEJM 2024;390:1394-1407, Table 2", "text": "KCCQ-CSS at 52 weeks: ETD 7.3 points (95% CI 4.1 to 10.4; P<0.001). Consistent benefit across pre-specified subgroups.", "highlights": ["7.3", "4.1", "10.4", "P<0.001"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2313917"},
                    {"label": "Co-Primary: Body Weight", "source": "Kosiborod MN et al. NEJM 2024;390:1394-1407, Table 2", "text": "Body weight: ETD -6.4% (95% CI -7.6 to -5.2; P<0.001).", "highlights": ["-6.4%", "-7.6", "-5.2"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2313917"},
                    {"label": "Worsening HF Events", "source": "Kosiborod MN et al. NEJM 2024;390:1394-1407", "text": "Worsening HF: 7 (2.3%) vs 18 (5.9%).", "highlights": ["7 (2.3%)", "18 (5.9%)"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2313917"},
                ],
            },
            "NCT04847557": {
                "name": "SUMMIT", "phase": "III", "year": 2024,
                "tE": 29, "tN": 364, "cE": 52, "cN": 367, "group": "HFpEF +/- T2DM",
                "publishedHR": 0.62, "hrLCI": 0.41, "hrUCI": 0.95,
                "baseline": {"n": 731, "age": 65.0, "female": 47.7, "bmi": 38.3, "lvef": 54.0},
                "allOutcomes": [
                    {"shortLabel": "MACE", "title": "CV death or worsening HF (composite)", "tE": 29, "cE": 52, "type": "PRIMARY", "pubHR": 0.62, "pubHR_LCI": 0.41, "pubHR_UCI": 0.95},
                    {"shortLabel": "KCCQ", "title": "KCCQ-CSS change from baseline (points)", "tE": None, "cE": None, "type": "SECONDARY", "md": 6.9, "se": 1.8622},
                    {"shortLabel": "BW", "title": "Body weight change (%)", "tE": None, "cE": None, "type": "SECONDARY", "md": -11.6, "se": 0.6378},
                    {"shortLabel": "6MWD", "title": "6-minute walk distance (m)", "tE": None, "cE": None, "type": "SECONDARY", "md": 18.3, "se": 4.2857},
                ],
                "rob": ["low", "low", "low", "some", "low"],
                "snippet": "N Engl J Med 2024 (SUMMIT trial)",
                "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2410027",
                "evidence": [
                    {"label": "Primary: CV Death or WHF", "source": "Packer M et al. NEJM 2024 (SUMMIT), Table 2", "text": "CV death or worsening HF: HR 0.62 (95% CI 0.41-0.95; P=0.026). Events: 36 (9.9%) vs 56 (15.3%).", "highlights": ["HR 0.62", "0.41-0.95", "P=0.026"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2410027"},
                    {"label": "KCCQ-CSS", "source": "Packer M et al. NEJM 2024 (SUMMIT)", "text": "KCCQ-CSS change at 52 weeks: ETD 6.9 points (95% CI 3.3 to 10.6; P<0.001).", "highlights": ["6.9", "3.3", "10.6"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2410027"},
                    {"label": "Body Weight & 6MWD", "source": "Packer M et al. NEJM 2024 (SUMMIT)", "text": "Body weight: ETD -11.6% (95% CI -12.9 to -10.4). 6MWD: ETD 18.3 m (95% CI 9.9 to 26.7). Both P<0.001.", "highlights": ["-11.6%", "18.3 m"], "sourceUrl": "https://www.nejm.org/doi/full/10.1056/NEJMoa2410027"},
                ],
            },
        },
        "benchmarks": {},
        "ctgov_registry": {},
        "nma_ids": ["NCT04788511", "NCT04916470", "NCT04847557"],
        "nma_label": "Incretin Therapies vs Placebo",
        "nma_indirect_label": "GLP-1 RA vs GIP/GLP-1 RA (Indirect)",
    },
]


# ============================================================
# Import transform function from the original generator
# ============================================================

from generate_new_apps import transform_template


def main():
    print(f"Reading template: {TEMPLATE_PATH}")
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        template = f.read()

    print(f"Template: {len(template.splitlines())} lines, {len(template)} chars")

    for app in APPS:
        filename = app["filename"]
        output_path = os.path.join(OUTPUT_DIR, filename)
        backup_path = output_path.replace('.html', '.v11.bak.html')

        # Backup old file if it exists
        if os.path.exists(output_path):
            print(f"\nBacking up {filename} -> {os.path.basename(backup_path)}")
            shutil.copy2(output_path, backup_path)

        print(f"\nGenerating v12 {filename}...")
        result = transform_template(template, app)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)

        line_count = len(result.splitlines())
        print(f"  -> {output_path} ({line_count} lines, {len(result)} chars)")

        # Basic validation
        div_open = len(re.findall(r'<div[\s>]', result))
        div_close = result.count('</div>')
        script_open = result.count('<script')
        script_close_safe = result.count("${'<'}/script>")
        script_close_real = result.count('</script>')

        print(f"  Div balance: {div_open} open, {div_close} close (delta={div_open - div_close})")
        print(f"  Script tags: {script_open} <script, {script_close_real} </script> (safe escapes: {script_close_safe})")

        # Check no leftover "bempedoic" references
        leftover = len(re.findall(r'bempedoic', result, re.IGNORECASE))
        if leftover > 0:
            print(f"  WARNING: {leftover} leftover 'bempedoic' references!")
        else:
            print(f"  No leftover 'bempedoic' references.")

        # Check unique storage key
        storage_hits = len(re.findall(re.escape(app["storage_key"]), result))
        print(f"  Storage key '{app['storage_key']}' found {storage_hits} times.")

    print("\nDone!")


if __name__ == "__main__":
    main()
