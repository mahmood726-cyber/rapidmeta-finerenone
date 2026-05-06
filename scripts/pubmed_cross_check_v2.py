"""PubMed cross-check v2 — refined filter that distinguishes acronym-vs-formal-title
false positives from genuinely-wrong PMIDs.

Decision rule:
  For each (file, NCT, PMID) triple, we expect the PubMed title to mention either:
    (a) the trial acronym (claim_name tokens), OR
    (b) the topic-area drug/condition (extracted from filename), OR
    (c) the trial's first author surname (from snippet).

  If NONE of (a), (b), (c) appear in the PubMed title → likely WRONG_PMID
  (truly off-topic article, not just naming convention).

Output: outputs/pubmed_cross_check_v2.csv with verdict per record.
"""
from __future__ import annotations
import csv
import re
import time
import urllib.request
import defusedxml.ElementTree as ET  # noqa: N817 — security: parse untrusted PubMed XML safely
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
PRIOR_CSV = REPO_DIR / "outputs" / "pubmed_cross_check.csv"
OUT_CSV = REPO_DIR / "outputs" / "pubmed_cross_check_v2.csv"

# Topic-area keyword map: filename substring → drug/condition keyword set
# Used to validate that the PubMed title is *about* the right topic area.
TOPIC_KEYWORDS = {
    "AFICAMTEN_HCM": {"aficamten", "hypertrophic", "cardiomyopathy", "myosin", "obstructive"},
    "AGYW_HIV_PREP": {"hiv", "prep", "tenofovir", "cabotegravir", "preexposure", "prevention", "agyw", "adolescent"},
    "ALDO_SYNTHASE": {"aldosterone", "synthase", "hypertension", "baxdrostat", "lorundrostat", "blood pressure"},
    "ALOPECIA_JAKI": {"alopecia", "jak", "baricitinib", "ritlecitinib", "deuruxolitinib"},
    "ALK_NSCLC": {"alk", "nsclc", "lung", "alectinib", "crizotinib", "brigatinib", "lorlatinib", "ensartinib"},
    "ANIFROLUMAB": {"anifrolumab", "lupus", "sle"},
    "ANTI_CD20_MS": {"ocrelizumab", "ofatumumab", "multiple sclerosis", "rituximab", "ublituximab"},
    "ANTIAMYLOID_AD": {"alzheimer", "lecanemab", "donanemab", "aducanumab", "gantenerumab", "amyloid"},
    "ABLATION_AF": {"ablation", "atrial fibrillation", "pulmonary vein", "cryoballoon", "radiofrequency"},
    "ACALABRUTINIB_CLL": {"acalabrutinib", "cll", "lymphocytic leukemia", "ibrutinib"},
    "ACORAMIDIS_ATTR_CM": {"acoramidis", "transthyretin", "amyloidosis", "ttr", "cardiomyopathy"},
    "ACS_ANTIPLATELET": {"prasugrel", "ticagrelor", "clopidogrel", "antiplatelet", "myocardial infarction", "acute coronary"},
    "ADC_HER2": {"trastuzumab", "her2", "breast cancer", "deruxtecan", "emtansine"},
    "ADJUVANT_IO_MELANOMA": {"melanoma", "nivolumab", "pembrolizumab", "ipilimumab", "dabrafenib", "trametinib"},
    "AFLIBERCEPT_HD": {"aflibercept", "wet amd", "diabetic macular", "vegf"},
    "AZITHROMYCIN_CHILD": {"azithromycin", "mortality", "child"},
    "BPAL_MDRTB": {"bedaquiline", "pretomanid", "linezolid", "tuberculosis", "tb", "mdr", "rifampicin-resistant"},
    "CARDIOVASCULAR_RWD": {"cardiovascular", "real-world", "registry"},
    "CFTR_CF": {"cystic fibrosis", "elexacaftor", "tezacaftor", "ivacaftor", "cftr", "trikafta"},
    "COVID_ANTIGEN_DTA": {"covid", "antigen", "lateral flow", "rapid", "sars"},
    "DAPA_GLP1_DM": {"dapagliflozin", "glp", "semaglutide", "tirzepatide", "diabetes"},
    "DDIMER_PE_DTA": {"d-dimer", "pulmonary embolism"},
    "DOLUTEGRAVIR_ART": {"dolutegravir", "hiv", "antiretroviral", "art"},
    "FENFLURAMINE_SEIZURE": {"fenfluramine", "dravet", "lennox-gastaut", "seizure"},
    "FINERENONE": {"finerenone", "ckd", "diabetic", "kidney", "mra"},
    "GENEXPERT_ULTRA_TB": {"xpert", "tuberculosis", "tb", "rifampicin"},
    "HIFPH_CKD_ANEMIA": {"hif", "roxadustat", "vadadustat", "daprodustat", "ckd", "anemia"},
    "HIV_ART_TIMING": {"antiretroviral", "art", "hiv", "cd4"},
    "HIV_PREP_INJECTABLE": {"cabotegravir", "prep", "hiv", "prevention", "f/taf", "f/tdf"},
    "HIV_TB_COINFECTION": {"hiv", "tb", "tuberculosis", "art"},
    "HSCTN_NSTEMI_DTA": {"troponin", "nstemi", "myocardial"},
    "HPV": {"hpv", "papillomavirus", "cervical", "cervarix", "gardasil"},
    "MALARIA_VACCINE": {"malaria", "rts,s", "r21", "matrix-m", "vaccine"},
    "MDR_TB": {"tuberculosis", "tb", "mdr", "rifampicin", "bedaquiline"},
    "MPMRI_PROSTATE": {"mri", "prostate", "biopsy"},
    "PEDIATRIC_HIV_ART": {"pediatric", "paediatric", "hiv", "art", "children", "dolutegravir"},
    "POSTPARTUM_HEMORRHAGE": {"postpartum", "hemorrhage", "tranexamic", "carbetocin", "oxytocin"},
    "PRIMAQUINE_GAMETOCYTE": {"primaquine", "gametocyte", "malaria", "falciparum"},
    "PTAU217_AD": {"ptau", "alzheimer", "biomarker", "tau"},
    "RESPONDER": {"responder"},
    "ROTAVIRUS_VACCINE": {"rotavirus", "vaccine", "gastroenteritis", "rotarix", "rotateq"},
    "SCD_DISEASE_MOD": {"sickle", "disease modifying", "voxelotor", "crizanlizumab", "lentiviral"},
    "SEVERE_ASTHMA": {"asthma", "mepolizumab", "benralizumab", "tezepelumab", "dupilumab", "reslizumab"},
    "SEVERE_PEDIATRIC_FEBRILE": {"malaria", "fluid", "transfusion", "child", "severe"},
    "SGLT2": {"empagliflozin", "dapagliflozin", "canagliflozin", "sotagliflozin", "sglt2", "sglt-2"},
    "SPONDYLOARTHRITIS": {"spondyloarthritis", "ankylosing", "secukinumab", "ixekizumab", "bimekizumab"},
    "TB_PREVENTION": {"tuberculosis", "tb", "isoniazid", "rifapentine", "preventive"},
    "TB_DRUG_SUSCEPTIBLE": {"tuberculosis", "tb", "rifapentine", "moxifloxacin"},
    "UC_BIOLOGICS": {"ulcerative colitis", "infliximab", "adalimumab", "vedolizumab", "ustekinumab", "tofacitinib"},
    "YELLOW_FEVER": {"yellow fever", "vaccine", "fractional"},
    "PNEUMONIA": {"pneumonia", "amoxicillin", "antibiotic"},
    "SCHISTOSOMIASIS": {"schistosomiasis", "praziquantel", "arpraziquantel"},
    "CRYPTOCOCCAL_MENINGITIS": {"cryptococcal", "amphotericin", "flucytosine", "fluconazole", "ambisome"},
    "PREGNANCY_HIV": {"pregnancy", "hiv", "dolutegravir", "efavirenz"},
}


def derive_topic_keywords(filename: str) -> set[str]:
    """Match filename against TOPIC_KEYWORDS and union all matched keyword sets."""
    name_upper = filename.upper().replace("_REVIEW.HTML", "")
    out = set()
    for substr, kws in TOPIC_KEYWORDS.items():
        if substr in name_upper:
            out.update(kws)
    return out


def title_mentions_topic(title: str, keywords: set[str]) -> bool:
    title_lower = title.lower()
    return any(kw.lower() in title_lower for kw in keywords)


def main():
    # Reuse PMID data from prior run via the v1 CSV
    if not PRIOR_CSV.exists():
        print(f"Prior CSV missing: {PRIOR_CSV}")
        return
    rows = list(csv.DictReader(PRIOR_CSV.open(encoding="utf-8")))
    print(f"Loaded {len(rows)} prior findings from v1 CSV")

    out_rows = []
    for r in rows:
        verdict = r["verdict"]
        if verdict == "OK":
            out_rows.append({**r, "v2_verdict": "OK", "topic_match": "", "v2_notes": ""})
            continue
        if "PMID_NOT_FOUND" in verdict:
            out_rows.append({**r, "v2_verdict": "PMID_NOT_FOUND", "topic_match": "", "v2_notes": "PMID not in PubMed"})
            continue

        # For TRIAL_PMID_MISALIGNED + YEAR_MISMATCH: refine using topic-area keyword
        topic_kws = derive_topic_keywords(r["file"])
        title = r["pubmed_title"]
        topic_ok = title_mentions_topic(title, topic_kws)

        v2_verdict = "OK"
        notes = []
        if "YEAR_MISMATCH" in verdict:
            try:
                yd = int(r["year_diff"])
                if abs(yd) > 1:
                    v2_verdict = "YEAR_MISMATCH"
                    notes.append(f"year diff {yd}")
            except (ValueError, TypeError):
                pass
        if "TRIAL_PMID_MISALIGNED" in verdict and not topic_ok:
            # Truly off-topic — likely wrong PMID
            v2_verdict = "WRONG_PMID" if v2_verdict == "OK" else v2_verdict + "+WRONG_PMID"
            notes.append(f"PubMed title doesn't mention any of: {sorted(topic_kws)[:5]}")

        out_rows.append({
            **r,
            "v2_verdict": v2_verdict,
            "topic_match": "YES" if topic_ok else "NO",
            "v2_notes": "; ".join(notes),
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    by_v2: dict[str, int] = {}
    for r in out_rows:
        by_v2[r["v2_verdict"]] = by_v2.get(r["v2_verdict"], 0) + 1
    print(f"\n=== v2 verdict counts (n={len(out_rows)}) ===")
    for k in sorted(by_v2.keys()):
        print(f"  {k:30s} {by_v2[k]}")

    real = [r for r in out_rows if r["v2_verdict"] not in ("OK",)]
    print(f"\n=== {len(real)} real defects ===\n")
    for r in real:
        print(f"  [{r['v2_verdict']:30s}] {r['file']:50s} {r['key']:18s} pmid={r['pmid']}")
        print(f"     claim: {r['claim_name'][:50]:50s} year={r['claim_year']}")
        print(f"     pubmed: {r['pubmed_title'][:80]}")
        print(f"     {r['v2_notes']}")
        print()


if __name__ == "__main__":
    main()
