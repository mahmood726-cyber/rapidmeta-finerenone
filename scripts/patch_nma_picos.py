"""
Fix template-leaked HF-quadruple PICOs in 32 NMA dashboards.

Audit revealed that almost every *_NMA_REVIEW.html had:
  pop:  'Adults with chronic HFrEF (LVEF <=40%, NYHA II-IV)'
  int:  'Empagliflozin, Dapagliflozin, or Sacubitril/Valsartan'
  out:  'CV death or HF hospitalization composite'
- a leak from the HF_QUADRUPLE_NMA template that was never replaced.

Each per-file PICO below is sourced from the dashboard's actual indication
(filename + landmark trial conventions). NMAs where the HF PICO is correct
(HF_QUADRUPLE_NMA, SGLT2I_HF_NMA) are skipped.

Usage:
    python scripts/patch_nma_picos.py --dry-run
    python scripts/patch_nma_picos.py
"""
import argparse, os, re, sys

ROOT = os.environ.get('RAPIDMETA_REPO_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Per-file correct PICO: (pop, int, comp, out, subgroup)
PICO = {
    'ACS_ANTIPLATELET_NMA_REVIEW.html': (
        'Adults post-acute coronary syndrome or post-PCI', 'P2Y12 inhibitor (ticagrelor, prasugrel, clopidogrel) + aspirin', 'Aspirin alone or alternate P2Y12', 'Composite CV death, MI, or stroke', 'ACS subtype (STEMI vs NSTE-ACS), age, prior MI'),
    'ADC_HER2_ADJUVANT_NMA_REVIEW.html': (
        'Adults with HER2+ early breast cancer with residual disease post-neoadjuvant therapy', 'Trastuzumab emtansine (T-DM1) or trastuzumab deruxtecan (T-DXd)', 'Trastuzumab', 'Invasive disease-free survival', 'Hormone-receptor status, residual disease burden, prior taxane'),
    'ADC_HER2_LOW_NMA_REVIEW.html': (
        'Adults with HER2-low metastatic breast cancer', 'Trastuzumab deruxtecan (T-DXd) or datopotamab deruxtecan (Dato-DXd)', "Physician's-choice chemotherapy", 'Progression-free survival', 'HR status, prior lines, liver metastases'),
    'ADC_HER2_NMA_REVIEW.html': (
        'Adults with HER2+ metastatic breast cancer (post-trastuzumab)', 'Trastuzumab deruxtecan (T-DXd) or trastuzumab emtansine (T-DM1)', "Physician's-choice chemotherapy or T-DM1", 'Progression-free survival', 'Brain metastases, hormone-receptor status, prior lines'),
    'ANTIAMYLOID_AD_NMA_REVIEW.html': (
        "Early Alzheimer's disease (MCI or mild AD with confirmed amyloid)", 'Anti-amyloid monoclonal antibody (lecanemab, donanemab, aducanumab)', 'Placebo', 'CDR-SB change at 18 months', 'APOE4 status, baseline CDR, amyloid burden'),
    'ANTIPSYCHOTICS_SCHIZO_NMA_REVIEW.html': (
        'Adults with schizophrenia (acute or maintenance)', 'Second-generation antipsychotic (olanzapine, risperidone, quetiapine, aripiprazole, lurasidone, paliperidone, ziprasidone)', 'Placebo or active comparator', 'PANSS total score change at endpoint', 'Acute vs maintenance, dose, treatment duration'),
    'ANTIVEGF_NAMD_NMA_REVIEW.html': (
        'Adults with neovascular age-related macular degeneration', 'Anti-VEGF agent (faricimab, aflibercept, ranibizumab, brolucizumab)', 'Sham or alternate anti-VEGF', 'BCVA letter-score change at week 48-52', 'Treatment-naive vs experienced, baseline CRT, lesion type'),
    'ANTI_CD20_MS_NMA_REVIEW.html': (
        'Adults with relapsing-remitting multiple sclerosis', 'Anti-CD20 monoclonal antibody (ocrelizumab, ofatumumab, ublituximab, rituximab)', 'Active comparator (interferon, teriflunomide)', 'Annualized relapse rate', 'Disease activity, prior DMT exposure, age'),
    'ATOPIC_DERM_NMA_REVIEW.html': (
        'Adults / adolescents with moderate-to-severe atopic dermatitis', 'Biologic or JAK inhibitor (dupilumab, abrocitinib, upadacitinib, baricitinib, lebrikizumab, tralokinumab, nemolizumab)', 'Placebo', 'EASI-75 response at 16 weeks', 'Age (adult vs adolescent), prior systemic exposure, baseline severity'),
    'BTKI_CLL_NMA_REVIEW.html': (
        'Adults with chronic lymphocytic leukemia (treatment-naive or relapsed/refractory)', 'BTK inhibitor (ibrutinib, acalabrutinib, zanubrutinib, pirtobrutinib)', 'Chemoimmunotherapy or alternate BTKi', 'Progression-free survival', 'Treatment line, IGHV mutation, del(17p)/TP53'),
    'CARDIORENAL_DKD_NMA_REVIEW.html': (
        'Adults with diabetic kidney disease (T2D + albuminuric CKD)', 'Finerenone, SGLT2 inhibitor, or GLP-1 receptor agonist', 'Placebo on top of RAS-blockade', 'Renal composite (eGFR decline, kidney failure, renal/CV death)', 'Baseline eGFR, baseline UACR, prior cardiovascular disease'),
    'CD_BIOLOGICS_NMA_REVIEW.html': (
        "Adults with moderate-to-severe Crohn's disease", 'Biologic or small molecule (ustekinumab, risankizumab, vedolizumab, infliximab, adalimumab, upadacitinib)', 'Placebo or alternate biologic', 'Clinical remission at induction (week 12)', 'Biologic-naive vs experienced, disease activity, fistulizing disease'),
    'CFTR_MODULATORS_NMA_REVIEW.html': (
        'Patients with cystic fibrosis carrying responsive CFTR mutation(s) (>=12 years typically)', 'CFTR modulator (elexacaftor/tezacaftor/ivacaftor, tezacaftor/ivacaftor, lumacaftor/ivacaftor, ivacaftor)', 'Placebo or alternate modulator', 'Absolute change in ppFEV1 at week 24', 'Genotype (homozygous F508del vs heterozygous), age, baseline ppFEV1'),
    'CGRP_MIGRAINE_NMA_REVIEW.html': (
        'Adults with episodic or chronic migraine', 'Anti-CGRP therapy (erenumab, fremanezumab, galcanezumab, eptinezumab, atogepant, rimegepant)', 'Placebo', 'Change in monthly migraine days at 12 weeks', 'Episodic vs chronic, prior preventive failures, medication-overuse'),
    'DOAC_AF_NMA_REVIEW.html': (
        'Adults with non-valvular atrial fibrillation at risk for stroke', 'Direct oral anticoagulant (apixaban, rivaroxaban, edoxaban, dabigatran)', 'Warfarin', 'Stroke or systemic embolism', 'CHA2DS2-VASc, age, baseline renal function'),
    'DOAC_VTE_NMA_REVIEW.html': (
        'Adults with acute venous thromboembolism', 'Direct oral anticoagulant (apixaban, rivaroxaban, edoxaban, dabigatran)', 'LMWH/warfarin', 'Recurrent VTE', 'PE vs DVT, provoked vs unprovoked, cancer-associated'),
    'GLP1_CVOT_NMA_REVIEW.html': (
        'Adults with type 2 diabetes at high cardiovascular risk', 'GLP-1 receptor agonist (liraglutide, semaglutide, dulaglutide, albiglutide, oral semaglutide, exenatide-LAR)', 'Placebo on top of standard care', '3-point MACE (CV death, nonfatal MI, nonfatal stroke)', 'Baseline ASCVD vs risk factors, age, baseline HbA1c'),
    'GLP1_MASH_NMA_REVIEW.html': (
        'Adults with metabolic dysfunction-associated steatohepatitis (MASH/NASH)', 'GLP-1 RA or dual/triple agonist (semaglutide, liraglutide, tirzepatide, retatrutide, survodutide)', 'Placebo', 'NASH resolution and/or fibrosis improvement at 52 weeks', 'Baseline fibrosis stage (F2 vs F3), T2DM status, BMI'),
    'HCC_1L_NMA_REVIEW.html': (
        'Adults with advanced hepatocellular carcinoma (first-line, BCLC C or unresectable B)', 'Immunotherapy combination (atezolizumab+bevacizumab, durvalumab+tremelimumab) or TKI (sorafenib, lenvatinib)', 'Sorafenib', 'Overall survival', 'Etiology (HBV/HCV/MAFLD), Child-Pugh class, baseline AFP'),
    'HER2_LOW_ADC_NMA_REVIEW.html': (
        'Adults with HER2-low metastatic breast cancer', 'Antibody-drug conjugate (trastuzumab deruxtecan, datopotamab deruxtecan)', "Physician's-choice chemotherapy", 'Progression-free survival', 'HR status, prior chemotherapy lines, liver metastases'),
    'IL_PSORIASIS_NMA_REVIEW.html': (
        'Adults with moderate-to-severe chronic plaque psoriasis', 'IL-17, IL-23, or IL-12/23 inhibitor (secukinumab, ixekizumab, brodalumab, guselkumab, risankizumab, tildrakizumab, ustekinumab, bimekizumab)', 'Placebo or alternate biologic', 'PASI-90 response at week 16', 'Biologic-naive vs experienced, baseline PASI, BSA'),
    'INCRETINS_T2D_NMA_REVIEW.html': (
        'Adults with type 2 diabetes', 'Incretin therapy (GLP-1 RA: semaglutide/dulaglutide/liraglutide; GIP/GLP-1: tirzepatide; DPP-4i)', 'Placebo or alternate anti-hyperglycemic', 'HbA1c change at week 26', 'Baseline HbA1c, baseline BMI, background therapy'),
    'JAKI_RA_NMA_REVIEW.html': (
        'Adults with moderate-to-severe rheumatoid arthritis', 'JAK inhibitor (tofacitinib, baricitinib, upadacitinib, filgotinib)', 'Placebo or methotrexate', 'ACR-50 response at 12-24 weeks', 'csDMARD-experienced vs bDMARD-experienced, age, CV risk'),
    'MIGRAINE_ACUTE_NMA_REVIEW.html': (
        'Adults with acute migraine attack', 'Acute migraine therapy (triptans, gepants: rimegepant/ubrogepant, lasmiditan)', 'Placebo or alternate acute therapy', 'Pain freedom at 2 hours', 'Migraine subtype, prior triptan response, opioid/NSAID overuse'),
    'MM_1L_NMA_REVIEW.html': (
        'Adults with newly-diagnosed multiple myeloma (transplant-eligible or ineligible)', 'Quadruplet or triplet induction (Dara-VRd, VRd, KRd, Dara-Rd, Rd)', 'Triplet without daratumumab (VRd or Rd)', 'Progression-free survival', 'Transplant eligibility, cytogenetic risk, age'),
    'OBESITY_DRUGS_NMA_REVIEW.html': (
        'Adults with overweight/obesity', 'GLP-1 / GIP / glucagon agonist (semaglutide 2.4 mg, tirzepatide, retatrutide, liraglutide 3 mg, naltrexone-bupropion, orlistat)', 'Placebo', 'Percent body-weight change at 68 weeks', 'Baseline BMI, T2DM status, sex'),
    'PAH_THERAPY_NMA_REVIEW.html': (
        'Adults with pulmonary arterial hypertension (WHO Group 1, FC II-III)', 'PAH therapy (sotatercept, riociguat, macitentan, ambrisentan, ambrisentan+tadalafil, selexipag)', 'Placebo on top of background therapy', 'Change in 6-minute walk distance at week 24', 'PAH etiology, background therapy, REVEAL 2.0 risk'),
    'PCSK9_LIPID_NMA_REVIEW.html': (
        'Adults with ASCVD or HeFH on maximally tolerated statin', 'PCSK9-targeting therapy (evolocumab, alirocumab, inclisiran)', 'Placebo or alternate PCSK9 strategy', 'Percent LDL-C change from baseline', 'Primary vs secondary prevention, statin tolerance, baseline LDL-C'),
    'PSA_BIOLOGICS_NMA_REVIEW.html': (
        'Adults with active psoriatic arthritis', 'Biologic or targeted synthetic DMARD (TNFi, IL-17, IL-23, JAKi)', 'Placebo or alternate biologic', 'ACR-20 response at 16-24 weeks', 'Biologic-naive vs experienced, predominant manifestation (joint vs axial vs skin)'),
    'RCC_1L_NMA_REVIEW.html': (
        'Adults with advanced or metastatic renal cell carcinoma (first-line)', 'IO-doublet (pembrolizumab+axitinib, nivolumab+ipilimumab, pembrolizumab+lenvatinib, avelumab+axitinib) or TKI', 'Sunitinib', 'Overall survival or progression-free survival', 'IMDC risk (favorable/intermediate/poor), histology, sarcomatoid features'),
    'SEVERE_ASTHMA_NMA_REVIEW.html': (
        'Adults with severe uncontrolled asthma on standard-of-care', 'Asthma biologic (mepolizumab, benralizumab, reslizumab, dupilumab, omalizumab, tezepelumab)', 'Placebo', 'Annual exacerbation rate', 'Eosinophil phenotype, IgE level, T2-high vs T2-low'),
    'SPONDYLOARTHRITIS_NMA_REVIEW.html': (
        'Adults with axial spondyloarthritis (radiographic AS or non-radiographic axSpA)', 'Biologic or JAKi (TNFi, IL-17, JAKi)', 'Placebo or alternate biologic', 'ASAS-40 response at 12-16 weeks', 'AS vs nr-axSpA, biologic-naive vs experienced, HLA-B27'),
    'UC_BIOLOGICS_NMA_REVIEW.html': (
        'Adults with moderate-to-severe ulcerative colitis', 'Biologic or small molecule (vedolizumab, ustekinumab, infliximab, adalimumab, golimumab, tofacitinib, upadacitinib, mirikizumab, etrasimod)', 'Placebo or alternate biologic', 'Clinical remission at induction (week 8-12)', 'Biologic-naive vs experienced, baseline Mayo score, prior anti-TNF failure'),
    'ALOPECIA_JAKI_NMA_REVIEW.html': (
        'Adults / adolescents with severe alopecia areata (>=50% scalp hair loss)', 'JAK inhibitor (baricitinib, ritlecitinib, brepocitinib, deuruxolitinib)', 'Placebo', 'SALT score response (SALT <=20) at week 24-36', 'Baseline severity (alopecia totalis/universalis vs patchy), disease duration, age'),
}


PROTO_LINE_RE = re.compile(
    r"protocol:\s*\{\s*pop:\s*'(?:\\'|[^'])*',\s*int:\s*'(?:\\'|[^'])*',\s*comp:\s*'(?:\\'|[^'])*',\s*out:\s*'(?:\\'|[^'])*',\s*subgroup:\s*'(?:\\'|[^'])*',(\s*query:\s*'[^']*',\s*rctOnly:\s*\w+,\s*post2015:\s*\w+\s*)\}"
)


def js_escape(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def build_protocol_literal(pop, intv, comp, out, sub, tail):
    return (f"protocol: {{ pop: '{js_escape(pop)}', int: '{js_escape(intv)}', "
            f"comp: '{js_escape(comp)}', out: '{js_escape(out)}', subgroup: '{js_escape(sub)}',"
            f"{tail}}}")


def patch_file(path, pop, intv, comp, out, sub, dry=False):
    src = open(path, 'r', encoding='utf-8').read()
    matches = list(PROTO_LINE_RE.finditer(src))
    if len(matches) == 0:
        return False, 'NO_MATCH'
    if len(matches) > 1:
        return False, f'AMBIGUOUS ({len(matches)})'
    m = matches[0]
    tail = m.group(1)
    new_literal = build_protocol_literal(pop, intv, comp, out, sub, tail)
    new_src = src[:m.start()] + new_literal + src[m.end():]
    if new_src == src:
        return False, 'NO_CHANGE'
    if not dry:
        open(path, 'w', encoding='utf-8').write(new_src)
    return True, new_literal[:120] + '...'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    summary = {'changed': 0, 'unchanged': 0, 'errors': 0}
    for fname, (pop, intv, comp, out, sub) in PICO.items():
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            print(f'\n[ERROR] {fname}: not found')
            summary['errors'] += 1
            continue
        try:
            changed, info = patch_file(path, pop, intv, comp, out, sub, dry=args.dry_run)
            tag = 'CHANGED' if changed else 'no-op'
            print(f'  [{tag}] {fname}: {info}')
            summary['changed' if changed else 'unchanged'] += 1
        except Exception as e:
            print(f'\n[ERROR] {fname}: {e}')
            summary['errors'] += 1
    print(f'\nTotal NMA files patched: {summary}')
    return 0 if summary['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
