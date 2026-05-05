"""Re-classify outputs/pmid_audit.csv with a smarter title-match heuristic
that uses the trial's group field + filename keywords + claimed_name.

Original audit's heuristic only matched on trial acronym, which fails for
NEJM/Lancet-style titles ("Trastuzumab Deruxtecan in HER2-Low Advanced
Breast Cancer" — clearly DESTINY-Breast04 — was flagged WRONG).

v2 heuristic, in priority order:
  (a) Title contains the trial acronym (e.g., DESTINY-Breast04)        -> OK
  (b) Title contains the primary drug name from group field (longest
      capitalized run before " | " or numeric dose)                    -> OK_DRUG
  (c) Title contains ≥2 keywords from filename normalized
      (e.g., "ACS antiplatelet" -> "ACS", "antiplatelet")               -> OK_TOPIC
  (d) Else                                                              -> WRONG_PMID
"""
from __future__ import annotations
import sys, io, csv, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")
IN_CSV = REPO / "outputs" / "pmid_audit.csv"
OUT_CSV = REPO / "outputs" / "pmid_audit_v2.csv"

# Map filename root -> condition keywords
FILE_KEYWORDS = {
    "ACS_ANTIPLATELET": ["coronary", "acute", "myocardial", "antiplatelet", "ticagrelor", "prasugrel", "clopidogrel", "stent", "PCI"],
    "ACALABRUTINIB_CLL": ["chronic lymphocytic", "CLL", "BTK", "lymphocytic leukemia"],
    "ACORAMIDIS_ATTR_CM": ["transthyretin", "ATTR", "amyloid", "cardiomyopathy"],
    "ADC_HER2_ADJUVANT": ["HER2", "breast", "adjuvant", "trastuzumab"],
    "ADC_HER2_LOW": ["HER2-low", "HER2", "breast", "trastuzumab"],
    "ADC_HER2": ["HER2", "breast", "trastuzumab", "emtansine"],
    "ADJUVANT_IO_MELANOMA": ["melanoma", "adjuvant", "ipilimumab", "nivolumab", "pembrolizumab", "checkpoint"],
    "AFICAMTEN_HCM": ["aficamten", "obstructive", "cardiomyopathy", "hypertrophic", "myosin"],
    "AGYW_HIV_PREP": ["pre-exposure", "PrEP", "HIV", "prophylaxis", "tenofovir", "adolescent"],
    "ALDO_SYNTHASE": ["aldosterone", "synthase", "hypertension", "blood pressure"],
    "ALK_NSCLC": ["ALK", "alectinib", "crizotinib", "non-small-cell", "lung cancer", "NSCLC"],
    "ALOPECIA_JAKI": ["alopecia", "baricitinib", "ritlecitinib", "JAK"],
    "ANIFROLUMAB_SLE": ["anifrolumab", "lupus", "SLE", "interferon"],
    "ANTIAMYLOID_AD": ["amyloid", "Alzheimer", "donanemab", "lecanemab", "aducanumab", "CDR-SB"],
    "ANTIPSYCHOTICS_SCHIZO": ["schizophrenia", "antipsychotic", "olanzapine", "risperidone"],
    "ANTIVEGF_NAMD": ["age-related", "macular", "VEGF", "ranibizumab", "aflibercept", "wet"],
    "ATOPIC_DERM": ["atopic", "dermatitis", "dupilumab", "eczema", "tralokinumab"],
    "ATTR_CM": ["transthyretin", "ATTR", "amyloid", "cardiomyopathy", "tafamidis"],
    "ATTR_PN": ["transthyretin", "ATTR", "amyloid", "polyneuropathy", "patisiran"],
    "BIMEKIZUMAB_PSORIASIS": ["bimekizumab", "psoriasis", "IL-17", "PASI"],
    "BLINATUMOMAB_BCP_ALL": ["blinatumomab", "leukemia", "lymphoblastic", "ALL"],
    "BTKI_CLL": ["BTK", "ibrutinib", "acalabrutinib", "zanubrutinib", "CLL", "lymphocytic"],
    "CAB_PREP_HIV": ["cabotegravir", "PrEP", "HIV", "long-acting"],
    "CABOTEGRAVIR_HIV_ART": ["cabotegravir", "rilpivirine", "HIV", "long-acting"],
    "CARDIORENAL_DKD": ["finerenone", "kidney", "diabetic", "albuminuria"],
    "CD_BIOLOGICS": ["Crohn", "infliximab", "adalimumab", "ustekinumab", "vedolizumab", "biologic"],
    "CFTR_MODULATORS": ["cystic fibrosis", "CFTR", "ivacaftor", "lumacaftor", "elexacaftor"],
    "CGRP_MIGRAINE": ["migraine", "erenumab", "fremanezumab", "CGRP"],
    "CHOLERA_OCV": ["cholera", "vibrio", "vaccine", "Shanchol"],
    "COLCHICINE_CVD": ["colchicine", "cardiovascular"],
    "COVID_ORAL_ANTIVIRALS": ["COVID", "SARS-CoV-2", "nirmatrelvir", "molnupiravir"],
    "CRYPTOCOCCAL_MENINGITIS": ["cryptococcal", "meningitis", "amphotericin", "fluconazole"],
    "DELANDISTROGENE_DMD": ["Duchenne", "muscular", "delandistrogene", "elevidys", "DMD"],
    "DESTINY_BREAST": ["trastuzumab deruxtecan", "HER2", "breast"],
    "DIABETIC_MACULAR_EDEMA": ["macular edema", "diabetic", "ranibizumab", "aflibercept", "DME"],
    "DIABETIC_RETINOPATHY": ["retinopathy", "diabetic", "ranibizumab", "aflibercept", "panretinal"],
    "DOAC_AF": ["atrial fibrillation", "anticoagulant", "DOAC", "rivaroxaban", "apixaban", "edoxaban", "dabigatran", "warfarin"],
    "DOAC_VTE": ["thromboembolism", "DOAC", "rivaroxaban", "apixaban"],
    "DOLUTEGRAVIR_ART_SSA": ["dolutegravir", "HIV", "ART", "antiretroviral"],
    "DORAVIRINE_HIV": ["doravirine", "HIV", "antiretroviral"],
    "DUPILUMAB_COPD": ["dupilumab", "COPD", "exacerbation"],
    "EBOLA_VACCINE": ["Ebola", "vaccine", "rVSV"],
    "EFGARTIGIMOD_MG": ["myasthenia", "FcRn", "efgartigimod"],
    "ETRASIMOD_UC": ["ulcerative colitis", "etrasimod", "S1P"],
    "EVT_BASILAR": ["basilar", "thrombectomy", "ischemic stroke"],
    "FENFLURAMINE_SEIZURE": ["Dravet", "fenfluramine", "epilepsy", "seizure"],
    "FRAGILITY_FRACTURE": ["osteoporosis", "fracture", "denosumab", "romosozumab", "teriparatide", "bisphosphonate"],
    "GLP1_CVOT": ["GLP-1", "liraglutide", "semaglutide", "dulaglutide", "cardiovascular"],
    "GLP1_MASH": ["NASH", "MASH", "GLP-1", "semaglutide", "liver"],
    "HCC_1L": ["hepatocellular", "atezolizumab", "bevacizumab", "tremelimumab", "HCC"],
    "HEMOPHILIA_GENE_THERAPY": ["hemophilia", "factor IX", "factor VIII", "gene therapy", "AAV"],
    "HEPATITIS_HCV_DAA": ["hepatitis C", "HCV", "sofosbuvir", "velpatasvir", "glecaprevir"],
    "HER2_LOW_ADC": ["HER2-low", "trastuzumab deruxtecan", "sacituzumab", "datopotamab", "breast"],
    "HF_QUADRUPLE": ["heart failure", "SGLT2", "dapagliflozin", "empagliflozin"],
    "HFREF_QUADRUPLE": ["heart failure", "ARNI", "sacubitril", "valsartan"],
    "HIDRADENITIS_SUPPURATIVA": ["hidradenitis", "adalimumab", "secukinumab", "bimekizumab"],
    "HIFPH_CKD_ANEMIA": ["anemia", "kidney", "roxadustat", "vadadustat", "daprodustat"],
    "HIV_ART_FIRSTLINE": ["dolutegravir", "efavirenz", "tenofovir", "first-line", "HIV"],
    "HIV_ART_TIMING": ["HIV", "ART", "timing", "early"],
    "HIV_LA_PREP": ["lenacapavir", "cabotegravir", "PrEP", "long-acting", "HIV"],
    "HIV_PREP_INJECTABLE": ["cabotegravir", "PrEP", "long-acting", "HIV"],
    "HIV_TB_COINFECTION_ART_TIMING": ["tuberculosis", "HIV", "co-infection", "ART", "timing"],
    "HPV_DOSE_REDUCTION": ["HPV", "human papillomavirus", "vaccine", "single-dose", "cervical"],
    "HPV_VACCINE_SCHEDULES": ["HPV", "papillomavirus", "vaccine", "schedule"],
    "HYDROCORTISONE_SEPTIC_SHOCK": ["septic shock", "hydrocortisone", "corticosteroid", "sepsis"],
    "ICU_SEDATION": ["sedation", "intensive care", "dexmedetomidine", "propofol"],
    "IL23_PSORIASIS": ["IL-23", "guselkumab", "risankizumab", "psoriasis"],
    "IL23_PSA": ["IL-23", "psoriatic arthritis", "guselkumab"],
    "IL_PSORIASIS": ["IL-17", "IL-23", "psoriasis", "secukinumab", "ixekizumab"],
    "INCRETINS_T2D": ["GLP-1", "semaglutide", "tirzepatide", "type 2 diabetes", "HbA1c"],
    "INSULIN_ICODEC": ["insulin", "icodec", "weekly", "diabetes"],
    "INTENSIVE_BP": ["blood pressure", "hypertension", "intensive"],
    "IO_CHEMO_NSCLC_1L": ["pembrolizumab", "atezolizumab", "platinum", "non-small-cell", "NSCLC"],
    "JAK_RA": ["rheumatoid arthritis", "tofacitinib", "baricitinib", "upadacitinib", "JAK"],
    "JAK_UC": ["ulcerative colitis", "tofacitinib", "filgotinib", "upadacitinib", "JAK"],
    "JAKI_AD": ["atopic dermatitis", "abrocitinib", "upadacitinib", "JAK"],
    "JAKI_RA": ["rheumatoid arthritis", "tofacitinib", "baricitinib", "filgotinib", "JAK"],
    "KRAS_G12C": ["KRAS", "sotorasib", "adagrasib", "G12C", "lung"],
    "LEBRIKIZUMAB_AD": ["lebrikizumab", "atopic dermatitis", "eczema", "IL-13"],
    "LENACAPAVIR_PREP": ["lenacapavir", "PrEP", "HIV", "capsid"],
    "MALARIA_ACT": ["malaria", "artemisinin", "lumefantrine", "ACT"],
    "MALARIA_VACCINE": ["malaria", "vaccine", "RTS,S", "R21"],
    "MDR_TB_SHORTENED": ["tuberculosis", "MDR-TB", "bedaquiline", "pretomanid", "linezolid"],
    "MEDITERRANEAN_DIET_CV": ["mediterranean diet", "cardiovascular", "PREDIMED"],
    "MIGRAINE_ACUTE": ["migraine", "acute", "rimegepant", "ubrogepant", "lasmiditan"],
    "MITAPIVAT_THALASSEMIA": ["mitapivat", "thalassemia", "hemoglobin", "PK activator"],
    "MM_1L": ["multiple myeloma", "daratumumab", "bortezomib", "lenalidomide"],
    "NEOADJUVANT_IO_NSCLC": ["nivolumab", "pembrolizumab", "neoadjuvant", "lung", "NSCLC"],
    "NIRSEVIMAB_INFANT_RSV": ["nirsevimab", "RSV", "respiratory syncytial", "infant"],
    "OBESITY_DRUGS": ["obesity", "weight", "tirzepatide", "semaglutide", "liraglutide"],
    "OSIMERTINIB_EGFR_NSCLC": ["osimertinib", "EGFR", "NSCLC", "non-small-cell"],
    "PAH_THERAPY": ["pulmonary arterial hypertension", "PAH", "macitentan", "selexipag", "ambrisentan"],
    "PARP_ARPI_MCRPC": ["PARP", "olaparib", "talazoparib", "prostate", "mCRPC"],
    "PARP_OVARIAN": ["PARP", "olaparib", "niraparib", "ovarian", "BRCA"],
    "PBC_PPAR": ["primary biliary", "elafibranor", "seladelpar", "cholangitis"],
    "PCSK9_LIPID": ["PCSK9", "evolocumab", "alirocumab", "LDL"],
    "PEDIATRIC_HIV_ART": ["pediatric", "children", "HIV", "ART"],
    "PHYSICAL_REHAB_OLDER": ["older", "rehabilitation", "physical", "frailty"],
    "PI3K_AKT_BC": ["PI3K", "alpelisib", "AKT", "breast"],
    "POLYCYTHEMIA_VERA": ["polycythemia vera", "ruxolitinib", "interferon"],
    "POSTPARTUM_HEMORRHAGE": ["postpartum hemorrhage", "tranexamic", "oxytocin"],
    "PPH_BUNDLE": ["postpartum hemorrhage", "bundle", "tranexamic", "E-MOTIVE"],
    "PRIMAQUINE_GAMETOCYTE_DR": ["primaquine", "malaria", "gametocyte", "Plasmodium falciparum"],
    "PSA_BIOLOGICS": ["psoriatic arthritis", "secukinumab", "ixekizumab", "adalimumab"],
    "RCC_1L": ["renal cell", "renal cancer", "axitinib", "pembrolizumab", "cabozantinib"],
    "RENAL_DENERV": ["renal denervation", "hypertension", "SPYRAL"],
    "RISANKIZUMAB_CD": ["risankizumab", "Crohn", "IL-23"],
    "ROMOSOZUMAB_OP": ["romosozumab", "osteoporosis", "fracture"],
    "ROTAVIRUS_VACCINE_AFRICA": ["rotavirus", "vaccine", "Africa", "Rotarix", "RotaTeq"],
    "RSV_VACCINE_OLDER": ["respiratory syncytial", "RSV", "vaccine", "older"],
    "RUSFERTIDE_PV": ["rusfertide", "polycythemia", "iron"],
    "SCD_DISEASE_MOD": ["sickle cell", "voxelotor", "L-glutamine", "exa-cel"],
    "SEPSIS_RESUSCITATION": ["sepsis", "fluid", "resuscitation", "septic shock"],
    "SEVERE_ASTHMA": ["severe asthma", "tezepelumab", "benralizumab", "mepolizumab"],
    "SEVERE_PEDIATRIC_FEBRILE_AFRICA": ["pediatric", "febrile", "Africa", "antimalarial"],
    "SGLT2_HF": ["SGLT2", "dapagliflozin", "empagliflozin", "heart failure"],
    "SGLT2_MACE_CVOT": ["SGLT2", "empagliflozin", "canagliflozin", "cardiovascular"],
    "SGLT2I_HF": ["SGLT2", "dapagliflozin", "empagliflozin", "heart failure"],
    "SPONDYLOARTHRITIS": ["axial spondyloarthritis", "ankylosing", "secukinumab", "bimekizumab", "ixekizumab"],
    "TB_PREVENTION": ["latent tuberculosis", "isoniazid", "rifampicin", "rifapentine"],
    "TDXD_HER2LOW_BC": ["trastuzumab deruxtecan", "HER2-low", "breast"],
    "TEPLIZUMAB_T1D": ["teplizumab", "type 1 diabetes", "anti-CD3"],
    "TIRZEPATIDE_OBESITY": ["tirzepatide", "obesity", "weight"],
    "TNK_VS_TPA_STROKE": ["tenecteplase", "alteplase", "stroke", "thrombolysis"],
    "UC_BIOLOGICS": ["ulcerative colitis", "infliximab", "adalimumab", "vedolizumab", "ustekinumab"],
    "UPADACITINIB_CD": ["upadacitinib", "Crohn", "JAK"],
    "VENETOCLAX_AML": ["venetoclax", "acute myeloid", "AML", "azacitidine"],
    "VENETOCLAX_CLL": ["venetoclax", "CLL", "lymphocytic", "BCL2"],
    "VITAMIN_D_FRACTURE_FALL": ["vitamin D", "fracture", "fall"],
    "VITILIGO": ["vitiligo", "ruxolitinib", "tofacitinib"],
    "VOCLOSPORIN_LN": ["voclosporin", "lupus nephritis"],
    "WOMAN_2": ["postpartum hemorrhage", "tranexamic"],
    "ZOLBETUXIMAB_GASTRIC": ["zolbetuximab", "gastric", "claudin"],
    "ZURANOLONE_PPD": ["zuranolone", "postpartum depression"],
}


def file_to_keywords(fname):
    root = fname.replace("_REVIEW.html", "").replace("_NMA", "")
    if root in FILE_KEYWORDS:
        return FILE_KEYWORDS[root]
    # Fallback: split on underscore
    return [t.lower() for t in re.split(r"[_\-]+", root) if len(t) > 2]


def normalize(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def reclassify(row):
    title = row.get("esummary_title", "")
    if not title:
        return "NOT_FOUND"
    nt = normalize(title)
    cn = row.get("claimed_name", "")
    # (a) Acronym match
    acros = re.findall(r"[A-Z][A-Z0-9\-]{2,}", cn)
    for a in acros:
        if normalize(a) in nt:
            return "OK_ACRONYM"
    # (b) Drug name from filename keywords + claimed name
    fname_kw = file_to_keywords(row["file"])
    matched_kw = [k for k in fname_kw if normalize(k) in nt]
    if len(matched_kw) >= 2:
        return "OK_KEYWORDS"
    if len(matched_kw) == 1 and len(matched_kw[0].split()) >= 2:
        return "OK_KEYWORDS"  # Multi-word keyword counts as 2
    # (c) Drug name from claimed_name (capitalized words longer than 4 chars)
    cn_drug_words = [w for w in re.findall(r"[A-Za-z]{5,}", cn) if w[0].isupper() and w.lower() not in {"trial", "study", "phase", "induction", "maintenance"}]
    for w in cn_drug_words:
        if normalize(w) in nt:
            return "OK_DRUG"
    return "WRONG_PMID"


def main():
    rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8")))
    print(f"Reclassifying {len(rows)} rows ...")

    counts = {"OK_ACRONYM": 0, "OK_KEYWORDS": 0, "OK_DRUG": 0, "WRONG_PMID": 0, "NOT_FOUND": 0}
    out = []
    for r in rows:
        new_status = reclassify(r)
        counts[new_status] = counts.get(new_status, 0) + 1
        r["status_v2"] = new_status
        out.append(r)

    # Write v2
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    print(f"\n=== v2 status distribution ===")
    total = sum(counts.values())
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:18s} {v:4d}  ({100*v/total:.1f}%)")

    n_truly_wrong = counts.get("WRONG_PMID", 0)
    print(f"\n  Total OK (any path): {total - n_truly_wrong} ({100*(total-n_truly_wrong)/total:.1f}%)")
    print(f"  Truly WRONG_PMID:    {n_truly_wrong} ({100*n_truly_wrong/total:.1f}%)")

    # Show truly-wrong samples
    print(f"\n=== Sample truly WRONG_PMID (likely real errors) ===")
    shown = 0
    for r in out:
        if r["status_v2"] == "WRONG_PMID" and shown < 30:
            print(f"  {r['file'][:32]:32s} pmid={r['pmid']} claim={r['claimed_name'][:32]:32s}")
            print(f"    got: {r['esummary_title'][:80]}")
            if r['suggested_pmid']:
                print(f"    suggested: {r['suggested_pmid']} ({r['suggested_title'][:60]})")
            shown += 1


if __name__ == "__main__":
    main()
