#!/usr/bin/env python
"""Reorganize index.html into a single, alphabetized, specialty-based layout.

Problem: the landing page mixes two schemes -- a hand-curated set of specialty
sections (Neurology, Oncology, ...) plus an 8-section cardiorenal topic cluster,
AND a giant 584-card "Audit-first builds" dump that is not grouped by specialty
at all. This merges everything into one alphabetized specialty list.

Strategy:
  * Cards already inside a curated specialty section inherit that section's
    specialty (ground truth) -- with the cardiorenal cluster mapped to
    Cardiology / Nephrology / Endocrinology.
  * Cards in the ungrouped dumps (Audit-first builds, Global Health) are
    classified by a keyword map over the filename (then card title).
  * Utilities, E156, and the portfolio-scan section are kept as-is (non-specialty).

Card HTML is preserved verbatim; the script only re-buckets and re-emits. It
asserts that NO card is lost (count in == count out) and that div balance is
unchanged. --dry-run prints the per-specialty distribution and the Other bucket.
"""
from __future__ import annotations
import argparse
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(REPO, "index.html")

# curated section title -> specialty (None = keep as a non-specialty section)
SECTION_SPECIALTY = {
    "Heart Failure": "Cardiology", "Lipid-Lowering": "Cardiology",
    "Anti-Inflammatory": "Cardiology", "Blood Pressure": "Cardiology",
    "Rhythm": "Cardiology", "Anticoagulation": "Cardiology",
    "Renal": "Nephrology",
    "Diabetes": "Endocrinology", "Endocrinology": "Endocrinology",
    "Neurology": "Neurology", "Oncology": "Oncology",
    "Infectious Disease": "Infectious Disease", "Gastroenterology": "Gastroenterology",
    "Respiratory": "Respiratory", "Rheumatology": "Rheumatology",
    "Ophthalmology": "Ophthalmology", "Psychiatry": "Psychiatry",
    "Hepatology": "Hepatology", "Women's Health": "Women's Health",
    "Dermatology": "Dermatology",
    # ungrouped dumps -> classify by keyword
    "Global Health": "_CLASSIFY_", "Audit-first builds": "_CLASSIFY_",
}
# kept verbatim, not specialty-grouped
KEEP_SECTIONS = ("Utilities", "E156 submission", "All 77 pooled results")

# keyword -> specialty, checked in order (first hit wins). Filename is uppercased.
RULES = [
    # --- disambiguate the known-tricky tokens FIRST ---
    ("Oncology", ["_RENAL", "AXITINIB", "CABOZANTINIB", "BEVACIZUMAB", "EVEROLIMUS_RENAL", "RCC", "RENAL_CELL"]),
    ("Rheumatology", ["JAK_RA", "JAKI_RA", "_RA_", "RHEUMATOID", "PSA_", "_PSA", "PSORIATIC_ARTH", "AXSPA", "SPONDYL", "GOUT", "VASCULITIS", "SJOGREN", "SCLERODERMA", "DERMATOMYOSITIS", "STILL", "POLYMYALGIA"]),
    ("Dermatology", ["PSORIASIS", "_PSO_", "_PSO.", "ATOPIC", "JAKI_AD", "_AD_REVIEW", "ALOPECIA", "HIDRADENITIS", "URTICARIA", "VITILIGO", "ACNE", "ECZEMA", "DUPILUMAB_AD", "LEBRIKIZUMAB", "PRURIGO", "DERM"]),
    ("Hepatology", ["HEPATITIS", "HCV", "HBV", "HEP_B", "HEP_D", "HEP_C", "NASH", "MASH", "NAFLD", "CIRRHOSIS", "BULEVIRTIDE", "_PBC", "CHOLESTAT", "LIVER", "HEPATOCELL", "PORTAL_HYPERT"]),
    ("Infectious Disease", ["HIV", "_PREP", "_ART_", "ANTIRETRO", "COVID", "_TB_", "_TB.", "MDR_TB", "MDRTB", "TUBERCUL", "ANTIBIOTIC", "_ABX", "FUNGAL", "ANTIFUNGAL", "_CDI", "C_DIFF", "_CMV", "_RSV", "MALARIA", "DENGUE", "MPOX", "SEPSIS", "CARBAPENEM", "CEFTAZIDIME", "CEFIDEROCOL", "LEFAMULIN", "MENINGITIS", "INFLUENZA", "NIRSEVIMAB", "LETERMOVIR", "PNEUMON", "INFECT", "_CAP_", "CABP", "HAP_VAP", "DORAVIRINE", "DOLUTEGRAVIR", "LENACAPAVIR"]),
    ("Oncology", ["CANCER", "TUMOR", "TUMOUR", "NSCLC", "_LUNG", "BREAST", "PROSTATE", "OVARIAN", "MELANOMA", "LYMPHOMA", "_AML", "_CLL", "_CRC", "COLORECTAL", "GASTRIC", "PANCREA", "MYELOMA", "_MM_", "LEUKEM", "CAR_T", "CART_", "_CART", "PEMBROLIZUMAB", "NIVOLUMAB", "ATEZOLIZUMAB", "DURVALUMAB", "OLAPARIB", "_PARP", "CDK", "_ADC", "HER2", "_ALK", "KRAS", "BRAF", "CHECKPOINT", "_PD1", "PDL1", "_IO_", "RADIOLIGAND", "LUTETIUM", "PSMA", "MYELOFIBROSIS", "_MF_", "_MDS", "CINV", "SBRT", "BRIGATINIB", "OSIMERTINIB", "AMIVANTAMAB", "LAZERTINIB", "ELRANATAMAB", "BISPECIFIC", "CHOLANGIO", "CERVICAL", "ENDOMETRIAL_IO", "HEAD_NECK", "ESOPHAG", "BLADDER", "UROTHEL", "HCC", "RCC", "FGFR", "AR_NEXT_GEN", "ARPI", "DAROLUTAMIDE", "ENZALUTAMIDE", "CAPIVASERTIB", "INAVOLISIB", "ELACESTRANT", "TROP2", "DESTINY", "ZANUBRUTINIB", "BTKI", "VEN_FLT3", "QUIZARTINIB", "AML", "NEOADJUVANT"]),
    ("Hematology", ["HEMOPHILIA", "_ITP", "SICKLE", "_SCD", "THALASSEMIA", "_VWD", "_PNH", "FITUSIRAN", "CONCIZUMAB", "VOXELOTOR", "MITAPIVAT", "CROVALIMAB", "FACTOR_PROPHYLAXIS", "COMPLEMENT_C5", "ICATIBANT", "_HAE", "ANGIOEDEMA"]),
    ("Cardiology", ["_HF_", "_HF.", "HFPEF", "HFREF", "HEART_FAIL", "CARDIOMYOPATHY", "_HCM", "MAVACAMTEN", "AFICAMTEN", "MITRACLIP", "MITRAL", "_TEER", "COAPT", "SOTATERCEPT", "SELEXIPAG", "_PAH", "ATTR_CM", "ACORAMIDIS", "TAFAMIDIS", "LIPID", "INCLISIRAN", "PCSK9", "EVOLOCUMAB", "ALIROCUMAB", "ATHEROSCLER", "ANTICOAG", "APIXABAN", "RIVAROXABAN", "DABIGATRAN", "EDOXABAN", "WARFARIN", "DOAC", "_VTE", "ABLATION", "_AF_", "_AF.", "ATRIAL_FIB", "ANTIARRHYTH", "BLOOD_PRESSURE", "HYPERTENS", "CANGRELOR", "PCI", "CABG", "ACUTE_HF", "FCM_HF", "DCD_HEART", "ICH_"]),
    ("Nephrology", ["_CKD", "KIDNEY", "DIALYSIS", "NEPHRO", "IGAN", "IGA_NEPH", "GLOMERUL", "HYPERKAL", "ANEMIA_CKD", "EPOETIN", "FINERENONE", "LUPUS_NEPH", "VOCLOSPORIN", "BARDOXOLONE", "HIFPH", "ADPKD", "POLYCYSTIC", "FSGS", "DAPROD"]),
    ("Endocrinology", ["_T2D", "_T1D", "DIABET", "INSULIN", "ICODEC", "OBESITY", "TIRZEPATIDE", "SEMAGLUTIDE", "_GLP1", "GLP_1", "SGLT2", "DAPAGLIFLOZIN", "EMPAGLIFLOZIN", "CANAGLIFLOZIN", "OSTEOPOROSIS", "ROMOSOZUMAB", "DENOSUMAB", "FRACTURE", "FRAGILITY", "THYROID", "ACROMEGALY", "ADRENAL", "HYPERPARA", "GROWTH_HORMONE", "EFPEGLENATIDE", "RETATRUTIDE", "FCRN", "MASH_DRUGS"]),
    ("Neurology", ["MIGRAINE", "CGRP", "ALZHEIMER", "ANTIAMYLOID", "DONANEMAB", "ADUCANUMAB", "LECANEMAB", "_MS_", "_MS.", "MULTIPLE_SCLER", "ANTI_CD20_MS", "BTK_MS", "BTKI_MS", "TOLEBRUTINIB", "EPILEPSY", "SEIZURE", "FENFLURAMINE", "_CBD_", "PARKINSON", "_ALS", "TOFERSEN", "_SMA", "NUSINERSEN", "ONASEMNOGENE", "_DMD", "DUCHENNE", "ETEPLIRSEN", "MYASTHENIA", "NMOSD", "STROKE", "_ICH", "NARCOLEPSY", "ATTR_PN", "INOTERSEN", "PATISIRAN", "VUTRISIRAN", "HATTR", "POLYNEURO", "S1P"]),
    ("Respiratory", ["ASTHMA", "_COPD", "_IPF", "PULMONARY_FIB", "BRONCHIECTASIS", "CYSTIC_FIBROSIS", "CFTR", "_CF_", "NIV_", "HFNC", "RESPIRATORY", "TEZEPELUMAB", "BENRALIZUMAB", "MEPOLIZUMAB", "DUPILUMAB_COPD", "EOSINOPHIL"]),
    ("Gastroenterology", ["_IBD", "CROHN", "_UC_", "_UC.", "ULCERATIVE", "COLITIS", "ETRASIMOD", "MIRIKIZUMAB", "USTEKINUMAB", "VEDOLIZUMAB", "_CD_REVIEW", "_CD_AUTO", "RISANKIZUMAB_CD", "GERD", "EOSINOPHILIC_ESO", "GASTRO"]),
    ("Ophthalmology", ["RETINOPATHY", "MACULAR", "DRY_EYE", "UVEITIS", "_AMD", "GEOGRAPHIC_ATROPHY", "GLAUCOMA", "DIABETIC_RETIN", "OPHTHAL", "_DME"]),
    ("Psychiatry", ["DEPRESSION", "SCHIZO", "_MDD", "_PPD", "PSYCHEDELIC", "ESKETAMINE", "BIPOLAR", "ANXIETY", "_PTSD", "PSILOCYBIN", "ZURANOLONE"]),
    ("Women's Health", ["ENDOMETRIOSIS", "ELAGOLIX", "_GNRH", "MENOPAUSE", "FEZOLINETANT", "_VMS", "CONTRACEPT", "FIBROID", "HOT_FLASHES", "VASOMOTOR", "VVC", "OTESECONAZOLE", "POSTPARTUM"]),
    ("Rheumatology", ["LUPUS", "_SLE", "ANIFROLUMAB", "BELIMUMAB", "ARTHRITIS"]),  # after onco/derm to avoid stealing
    ("Dermatology", ["BARICITINIB", "UPADACITINIB", "BIMEKIZUMAB", "GUSELKUMAB", "ADALIMUMAB_PSO", "_IL23", "IL_PSORIASIS", "IL23"]),
    ("Vaccines & Global Health", ["VACCINE", "HPV", "ROTAVIRUS", "AGYW", "_AFRICA", "GLOBAL_HEALTH", "AZITHROMYCIN_CHILD", "CHILD_MORTALITY"]),
    # --- long-tail (run after the main rules; catch remaining Others) ---
    ("Infectious Disease", ["PRIMAQUINE", "GAMETOCYTE", "SCHISTOSOMIASIS", "PRAZIQUANTEL", "AMOXICILLIN", "_AOM", "ANIDULAFUNGIN", "CANDIDA", "CEFEPIME", "CEFTAROLINE", "CIPROFLOXACIN", "_UTI", "SARSCOV2", "CVNCOV", "FEXINIDAZOLE", "_HAT_", "IVERMECTIN", "_LF_", "ISONIAZID", "LTBI", "LINEZOLID", "MRSA", "MOXIFLOXACIN", "_HZV", "MENACWY", "MEN_ACWY", "PREVNAR", "PNEUMO", "TB_DRUG"]),
    ("Neurology", ["GANTENERUMAB", "MEMANTINE", "DEMENTIA", "_GMG", "_MG_AUTO", "MYASTHENIA", "ROZANOLIXIZUMAB", "ZILUCOPLAN", "RITUXIMAB_MG", "ECULIZUMAB_GMG", "ELAMIPRETIDE"]),
    ("Oncology", ["GIST", "BRENTUXIMAB", "HODGKIN", "PTCL", "DINUTUXIMAB", "NEUROBLASTOMA", "PEMIGATINIB", "_BTC", "MELPHALAN", "SELUMETINIB", "_NF1", "TRASTUZUMAB", "PALIFERMIN", "MUCOSITIS", "MOMELOTINIB"]),
    ("Hematology", ["SCD_", "AGRYLIN", "_ET_", "ARGATROBAN", "_HIT", "AVATROMBOPAG", "CAPLACIZUMAB", "_TTP", "DEFEROXAMINE", "_IRON", "ISOMALTOSIDE", "FERUMOXYTOL", "_IDA", "EMICIZUMAB", "ANDEXANET", "SUTIMLIMAB", "_CAD", "LUSPATERCEPT", "THAL", "FONDAPARINUX"]),
    ("Cardiology", ["SARTAN", "_HTN", "LISINOPRIL", "STATIN", "SACUBITRIL", "HEARTFAIL", "ETRIPAMIL", "SUPRAVENTRIC", "HOFH", "EVINACUMAB", "MIPOMERSEN"]),
    ("Psychiatry", ["BREXPIPRAZOLE", "AGITATION", "SMOKING", "BUPROPION", "CYTISINICLINE", "VARENICLINE", "NICOTINE", "TOBACCO", "DARIDOREXANT", "INSOMNIA", "GUANFACINE", "ADHD", "HALOPERIDOL", "DELIRIUM", "METHADONE", "_OUD", "NALMEFENE", "_AUD"]),
    ("Endocrinology", ["FABRY", "AGALSIDASE", "AVALGLUCOSIDASE", "POMPE", "ELIGLUSTAT", "GAUCHER", "IDURSULFASE", "_MPS", "SAPROPTERIN", "_PKU", "SEBELIPASE", "_LAL", "PRADER", "_GH_", "OSILODROSTAT", "CUSHING", "PASIREOTIDE"]),
    ("Nephrology", ["HYPERPHOS", "LUMASIRAN", "_PH1", "OXALURIA"]),
    ("Gastroenterology", ["_IBS", "ELUXADOLINE", "PLECANATIDE", "LINACLOTIDE", "LUBIPROSTONE", "_CIC", "_OIC", "METHYLNALTREXONE", "NALDEMEDINE", "_EOE", "EOSINOPHILIC_ESO"]),
    ("Hepatology", ["_PSC", "CILOFEXOR", "_FXR", "_PFIC", "MARALIXIBAT", "ODEVIXIBAT"]),
    ("Ophthalmology", ["_GA_", "AVACINCAPTAD", "DEXAMETHASONE_IMPLANT", "RANIBIZUMAB", "_DR_REVIEW", "_DR_AUTO"]),
    ("Rheumatology", ["BEHCET", "APREMILAST", "SJIA", "CANAKINUMAB", "_OA_", "FASINUMAB", "TANEZUMAB", "_AXIAL"]),
    ("Respiratory", ["_COUGH", "GEFAPIXANT", "_CRS", "MOMETASONE", "UMECLIDINIUM", "VILANTEROL", "LORATADINE", "_RHIN", "OMALIZUMAB_NASAL", "NASAL"]),
    ("Urology", ["_OAB", "FESOTERODINE", "VIBEGRON", "_BPH", "OVERACTIVE_BLADDER"]),
    ("Allergy & Immunology", ["FOOD_ALLERGY", "PALFORZIA", "PEANUT", "VIASKIN"]),
    ("Women's Health", ["_PPH", "PPH_", "RELUGOLIX", "MENSTRUAL"]),
    ("Neurology", ["TUBEROUS"]),
    ("Vaccines & Global Health", ["HZV", "SAM_SIMPLIFIED", "SAM_PROTOCOL"]),
    ("Dermatology", ["NEMOLIZUMAB", "RUXOLITINIB_AD", "TRALOKINUMAB", "PIMECROLIMUS", "DUPILUMAB", "_AD_AUTO", "PED_AD"]),
]


def specialty_for(href, name):
    s = (href + " " + name).upper()
    for spec, kws in RULES:
        for kw in kws:
            if kw in s:
                return spec
    return "Other"


CARD_RE = re.compile(r'<a\s+href="([^"]+\.html)"[^>]*class="card[^"]*"[^>]*>.*?</a>', re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    html = open(PATH, "rb").read().decode("utf-8", "replace")
    parts = re.split(r'(<h2[^>]*>)', html)
    preamble = parts[0]

    buckets = {}          # specialty -> [card_html, ...]
    keep_blocks = []      # (orig_index, block_html) for non-specialty sections
    footer = ""
    in_count = 0
    sections = []
    for i in range(1, len(parts), 2):
        head = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        title_raw = body.split("</h2>")[0]
        title = re.sub(r"<[^>]+>", "", title_raw).replace("&amp;", "&").strip()
        rest = body.split("</h2>", 1)[1] if "</h2>" in body else body
        sections.append((title, head, title_raw, rest))

    # The last section's `rest` contains the page footer after its grid. Detect by
    # splitting the LAST section's grid out.
    out_sections = []
    for idx, (title, head, title_raw, rest) in enumerate(sections):
        cards = CARD_RE.findall_iter if False else CARD_RE.finditer(rest)
        card_htmls = [m.group(0) for m in CARD_RE.finditer(rest)]
        in_count += len(card_htmls)

        keep = next((k for k in KEEP_SECTIONS if title.startswith(k)), None)
        spec = None
        for key, sp in SECTION_SPECIALTY.items():
            if title.startswith(key):
                spec = sp
                break

        block = head + title_raw + "</h2>" + rest  # this section's own full block
        if keep or spec is None:
            # keep verbatim (Utilities, E156, portfolio-scan, anything unmapped)
            keep_blocks.append((idx, title, block))
            continue
        if spec == "_CLASSIFY_":
            for h in card_htmls:
                href = re.search(r'href="([^"]+)"', h).group(1)
                nm = re.search(r'class="name">([^<]*)', h)
                buckets.setdefault(specialty_for(href, nm.group(1) if nm else ""),
                                   []).append(h)
        else:
            buckets.setdefault(spec, []).extend(card_htmls)

    # footer = everything after the last section's grid closes (preserving the
    # page-wrapper closing divs + </body>). The grid has no nested divs, so its
    # close is the first </div> after '<div class="grid">'.
    last_rest = sections[-1][3]
    gi = last_rest.find('<div class="grid">')
    gclose = last_rest.find("</div>", gi) if gi >= 0 else -1
    footer = last_rest[gclose + len("</div>"):] if gclose >= 0 else ""

    out_count = sum(len(v) for v in buckets.values())
    other = buckets.get("Other", [])

    print(f"cards in: {in_count}  classified into buckets: {out_count}  "
          f"Other: {len(other)}")
    print("\nper-specialty counts:")
    for sp in sorted(buckets):
        print(f"  {sp:26} {len(buckets[sp])}")
    if other:
        print("\nOTHER (unclassified) hrefs:")
        for h in other:
            print("   ", re.search(r'href="([^"]+)"', h).group(1))

    if args.dry_run:
        return 0

    # ---- rebuild ----
    SPECIAL_FIRST = [b for b in keep_blocks if "Utilities" in b[1] or "E156" in b[1]]
    SPECIAL_LAST = [b for b in keep_blocks if "All 77 pooled" in b[1]]
    other_keep = [b for b in keep_blocks
                  if b not in SPECIAL_FIRST and b not in SPECIAL_LAST]

    def grid_section(spec, cards):
        return (f"<h2>{spec}</h2>\n  <div class=\"grid\">\n    "
                + "\n    ".join(cards) + "\n  </div>\n\n  ")

    body_out = preamble
    # 1) clinical specialties first, alphabetized
    for sp in sorted(b for b in buckets if b != "Other"):
        body_out += grid_section(sp, buckets[sp])
    if "Other" in buckets:
        body_out += grid_section("Other / Cross-Specialty", buckets["Other"])
    # 2) any unmapped non-special sections, preserved verbatim
    for _, _, blk in other_keep:
        body_out += blk
    # 3) Utilities + E156 (tools) after the clinical content
    for _, _, blk in SPECIAL_FIRST:
        body_out += blk
    # 4) portfolio-scan section, then 5) the original page footer
    for _, _, blk in SPECIAL_LAST:
        body_out += blk
    body_out += footer

    # card-count + brace/div safety
    final_cards = len(CARD_RE.findall(body_out))
    assert final_cards == in_count, f"card count changed {in_count} -> {final_cards}"
    if html.count("<div") - html.count("</div>") != body_out.count("<div") - body_out.count("</div>"):
        raise SystemExit("div balance changed -- aborting")

    open(PATH, "wb").write(body_out.encode("utf-8"))
    print(f"\nWROTE index.html  ({final_cards} cards preserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
