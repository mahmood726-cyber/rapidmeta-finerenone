"""Rebuild the DOAC-vs-LMWH cancer-associated-VTE review app from source-verified data.

Anchor-based, fail-closed: every replacement asserts its anchor occurs the expected
number of times before touching the file, so the script re-applies cleanly on a
current origin/main checkout and refuses to run on a file it does not recognise.

Sourcing for every number is in outputs/doac_cancer_vte_correction_ledger.json.
Pooled values are recomputed by scripts/doac_cancer_vte_pool.py and cross-validated
in R/metafor by scripts/doac_cancer_vte_pool.R.

Run:  python scripts/fix_doac_cancer_vte.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TARGET = os.path.join(ROOT, 'DOAC_CANCER_VTE_REVIEW.html')

EDITS = []


def edit(tag, old, new, count=1):
    EDITS.append((tag, old, new, count))


# ---------------------------------------------------------------------------
# 1. CANONICAL TRIAL DATA (realData)
#
#    Verified 2026-07-30 against the trial primaries and the ClinicalTrials.gov
#    API v2 posted-results sections. See the correction ledger for per-number
#    provenance. The FIRST entry of allOutcomes is the review's default outcome.
# ---------------------------------------------------------------------------

HOKUSAI_ELIG = (
    'AACT-derived (auto-populated 2026-05-04). Sex: ALL; min age 18 Years; healthy volunteers: f. '
    'CRITERIA: "Inclusion Criteria:~* Male or female subjects with age ≥ 18 years or the otherwise '
    'legal lower age according to the country of residence;~* Confirmed acute lower extremity proximal '
    'DVT or PE for which long term treatment with low molecular weight heparin (LMWH) is indicated;~* '
    'Cancer, other than basal-cell or squamous-cell carcinoma of the skin;~* Able to provide written '
    'informed consent.~Exclusion Criteria:~* Thrombectomy, insertion of a caval filter, or use of a '
    'fibrinolytic agent to treat th...'
)

CARAVAGGIO_ELIG = (
    'AACT-derived (auto-populated 2026-05-04). Sex: ALL; min age 18 Years; healthy volunteers: f. '
    'CRITERIA: "Inclusion Criteria:~* Consecutive patients with a newly diagnosed, objectively '
    'confirmed: symptomatic or unsuspected, proximal lower-limb DVT or symptomatic PE or unsuspected '
    'PE in a segmental or more proximal pulmonary artery;~* Any type of cancer (other than basal-cell '
    'or squamous-cell carcinoma of the skin, primary brain tumor or intracerebral metastasis and acute '
    'leukemia);~* Signed and dated informed consent of the patient, available before the start of any '
    'specific trial procedure.~Exclus...'
)

ADAM_ELIG = (
    'AACT-derived (auto-populated 2026-05-04). Sex: ALL; min age 18 Years; healthy volunteers: f. '
    'CRITERIA: "Inclusion Criteria:~* Confirmed acute lower extremity or upper extremity (jugular, '
    'innominate, subclavian, axillary, brachial) DVT, PE, splanchnic (hepatic, portal, splenic, '
    'mesenteric, renal, gonadal), or cerebral vein thrombosis~* Active cancer defined as metastatic '
    'disease and/or any evidence of cancer on cross-sectional or positron emission tomography (PET) '
    'imaging, cancer related surgery, chemotherapy or radiation therapy within the past 6 months; '
    'note: non-melanoma skin cancer does not me...'
)

SELECTD_ELIG = (
    'ISRCTN86712308 registry record (verified 2026-07-30). Phase III; target enrolment 530; '
    'prospective, randomised, open-label, multicentre pilot study of dalteparin vs rivaroxaban in '
    'patients with active cancer and symptomatic PE, incidental PE, or symptomatic lower-extremity '
    'proximal DVT, with a second randomisation on treatment duration in residual-vein-thrombosis '
    'positive patients. Primary outcome: VTE recurrence rate from randomisation to first recurrence.'
)


def rd():
    """The corrected realData object, emitted as compact JS matching the file's style."""
    return (
        '{'
        # ---------------- HOKUSAI VTE Cancer ----------------
        'NCT02073682:{baseline:{n:1046,age:63.9,female:47,cancer_gi:26,pct_female:46.9},'
        'name:"HOKUSAI VTE-Cancer",pmid:"29231094",doi:"10.1056/NEJMoa1711948",phase:"III",year:2018,'
        'registryId:"NCT02073682",'
        'tE:41,tN:522,cE:59,cN:524,group:"Edoxaban",'
        'publishedHR:.71,hrLCI:.476,hrUCI:1.059,estimandType:"HR",'
        'allOutcomes:['
        '{shortLabel:"VTE",title:"Recurrent VTE (trial secondary outcome, overall study period)",'
        'tE:41,cE:59,type:"SECONDARY",pubHR:.71,pubHR_LCI:.476,pubHR_UCI:1.059,estimandType:"HR",'
        'timepoint:"12 months"},'
        '{shortLabel:"MajBleed",title:"Major bleeding (overall study period)",'
        'tE:36,cE:21,type:"SECONDARY",pubHR:1.77,pubHR_LCI:1.03,pubHR_UCI:3.04,estimandType:"HR",'
        'timepoint:"12 months"},'
        '{shortLabel:"Composite",title:"Recurrent VTE OR major bleeding (trial PRIMARY outcome)",'
        'tE:67,cE:71,type:"PRIMARY",pubHR:.97,pubHR_LCI:.696,pubHR_UCI:1.359,estimandType:"HR",'
        'timepoint:"12 months"}],'
        'rob:["low","some","low","low","low"],'
        'robSource:"RoB 2, manual. Open-label administration (CT.gov masking NONE) but all efficacy and '
        'bleeding outcomes were adjudicated by an independent committee blinded to treatment allocation '
        '(NEJM 2018;378:615-624, Methods).",'
        'snippet:"N Engl J Med 2018; 378:615-624",'
        'sourceUrl:"https://doi.org/10.1056/NEJMoa1711948",'
        'ctgovUrl:"https://clinicaltrials.gov/study/NCT02073682",'
        'evidence:['
        '{label:"Recurrent VTE (review primary outcome)",source:"ClinicalTrials.gov NCT02073682 posted '
        'results, secondary outcome measure",text:"Number of Participants With Recurrent Venous '
        'Thromboembolism (VTE) During the Overall Study Period: 41 of 522 (edoxaban) vs 59 of 524 '
        '(dalteparin). Posted analysis: Cox proportional hazard HR 0.71 (95% CI 0.476 to 1.059), '
        'p=0.0931. The NEJM report gives the same counts as 7.9% vs 11.3%.",'
        'highlights:["41","522","59","524","0.71"],'
        'sourceUrl:"https://clinicaltrials.gov/study/NCT02073682?tab=results"},'
        '{label:"NOT the review outcome: trial primary composite",source:"NEJM 2018; 378:615-624",'
        'text:"A primary-outcome event (composite of recurrent VTE OR major bleeding) occurred in 67 of '
        'the 522 patients (12.8%) in the edoxaban group as compared with 71 of the 524 patients (13.5%) '
        'in the dalteparin group (hazard ratio, 0.97; 95% CI, 0.70 to 1.36; P=0.006 for noninferiority). '
        'These 67/71 counts are the COMPOSITE and must not be used as recurrent VTE.",'
        'highlights:["67","522","71","524","0.97","composite"],'
        'sourceUrl:"https://doi.org/10.1056/NEJMoa1711948"},'
        '{label:"Major bleeding",source:"NEJM 2018; 378:615-624",'
        'text:"Major bleeding occurred in 36 patients (6.9%) in the edoxaban group and in 21 patients '
        '(4.0%) in the dalteparin group; HR 1.77 (95% CI 1.03 to 3.04). The registry posts a narrower '
        'ON-TREATMENT count of 32 vs 16 for the same trial; the overall-study-period counts are used '
        'here to match the recurrent-VTE time window.",'
        'highlights:["36","21","1.77"],'
        'sourceUrl:"https://doi.org/10.1056/NEJMoa1711948"},'
        '{label:"Eligibility (AACT-derived)",source:"AACT 2026-04-12 eligibilities.txt",'
        'text:' + js_str(HOKUSAI_ELIG) + ',highlights:["AACT-derived"]}]},'

        # ---------------- SELECT-D ----------------
        'ISRCTN86712308:{baseline:{n:406,age:67,female:43,cancer_gi:12},'
        'name:"SELECT-D",pmid:"29746227",doi:"10.1200/JCO.2018.78.8034",phase:"III",year:2018,'
        'registryId:"ISRCTN86712308",'
        'tE:8,tN:203,cE:18,cN:203,group:"Rivaroxaban",'
        'publishedHR:.43,hrLCI:.19,hrUCI:.99,estimandType:"HR",'
        'allOutcomes:['
        '{shortLabel:"VTE",title:"Recurrent VTE at 6 months (trial PRIMARY outcome)",'
        'tE:8,cE:18,nT:203,nC:203,type:"PRIMARY",pubHR:.43,pubHR_LCI:.19,pubHR_UCI:.99,'
        'estimandType:"HR",timepoint:"6 months"},'
        '{shortLabel:"MajBleed",title:"Major bleeding at 6 months",'
        'tE:null,cE:null,nT:203,nC:203,type:"SAFETY",pubHR:1.83,pubHR_LCI:.68,pubHR_UCI:4.96,'
        'estimandType:"HR",timepoint:"6 months"}],'
        'rob:["low","some","low","low","low"],'
        'robSource:"RoB 2, manual. Open-label; recurrent VTE and bleeding events reviewed by a blinded '
        'independent endpoint-adjudication process reported in J Clin Oncol 2018;36:2017-2023.",'
        'snippet:"J Clin Oncol 2018; 36(20):2017-2023",'
        'sourceUrl:"https://doi.org/10.1200/JCO.2018.78.8034",'
        'ctgovUrl:"https://www.isrctn.com/ISRCTN86712308",'
        'evidence:['
        '{label:"Recurrent VTE (review primary outcome)",source:"J Clin Oncol 2018; 36:2017-2023",'
        'text:"A total of 203 patients were randomly assigned to each group. Twenty-six patients '
        'experienced recurrent VTE (dalteparin, n = 18; rivaroxaban, n = 8). The 6-month cumulative VTE '
        'recurrence rate was 11% (95% CI, 7% to 16%) with dalteparin and 4% (95% CI, 2% to 9%) with '
        'rivaroxaban (hazard ratio 0.43; 95% CI, 0.19 to 0.99).",'
        'highlights:["203","8","18","0.43","4%","11%"],'
        'sourceUrl:"https://doi.org/10.1200/JCO.2018.78.8034"},'
        '{label:"Major bleeding",source:"J Clin Oncol 2018; 36:2017-2023",'
        'text:"The 6-month cumulative rate of major bleeding was 4% (95% CI, 2% to 8%) for dalteparin '
        'and 6% (95% CI, 3% to 11%) for rivaroxaban (HR 1.83; 95% CI, 0.68 to 4.96). CRUDE EVENT COUNTS '
        'ARE NOT REPORTED IN THE ACCESSIBLE SOURCE; the 6% and 4% figures are cumulative incidences and '
        'are deliberately NOT stored as event counts. The hazard ratio is carried instead.",'
        'highlights:["6%","4%","1.83"],'
        'sourceUrl:"https://doi.org/10.1200/JCO.2018.78.8034"},'
        '{label:"Trial registration",source:"ISRCTN registry, verified 2026-07-30",'
        'text:' + js_str(SELECTD_ELIG) + ',highlights:["ISRCTN86712308","Phase III"],'
        'sourceUrl:"https://www.isrctn.com/ISRCTN86712308"}]},'

        # ---------------- ADAM VTE ----------------
        'NCT02585713:{baseline:{n:300,age:64.4,female:40.4,cancer_gi:16},'
        'name:"ADAM VTE",pmid:"31630479",doi:"10.1111/jth.14662",phase:"III",year:2020,'
        'registryId:"NCT02585713",'
        'tE:1,tN:145,cE:9,cN:142,group:"Apixaban",'
        'publishedHR:.099,hrLCI:.013,hrUCI:.78,estimandType:"HR",'
        'allOutcomes:['
        '{shortLabel:"VTE",title:"Recurrent VTE (trial SECONDARY outcome)",'
        'tE:1,cE:9,type:"SECONDARY",pubHR:.099,pubHR_LCI:.013,pubHR_UCI:.78,estimandType:"HR",'
        'timepoint:"6 months"},'
        '{shortLabel:"MajBleed",title:"Major bleeding (trial PRIMARY outcome)",'
        'tE:0,cE:2,type:"PRIMARY",pubHR:null,pubHR_LCI:null,pubHR_UCI:null,estimandType:"RR",'
        'timepoint:"6 months"}],'
        'rob:["low","some","low","low","low"],'
        'robSource:"RoB 2, manual. Open-label; outcomes adjudicated by an independent committee blinded '
        'to allocation (J Thromb Haemost 2020;18:411-421).",'
        'snippet:"J Thromb Haemost 2020; 18(2):411-421",'
        'sourceUrl:"https://doi.org/10.1111/jth.14662",'
        'ctgovUrl:"https://clinicaltrials.gov/study/NCT02585713",'
        'evidence:['
        '{label:"Recurrent VTE (review primary outcome)",source:"J Thromb Haemost 2020; 18:411-421",'
        'text:"Recurrent VTE occurred in 0.7% of apixaban, compared to 6.3% of dalteparin patients '
        '[HR 0.099, 95% confidence interval 0.013-0.780, P=.0281]. With 145 and 142 patients in the '
        'primary analysis this is 1 of 145 vs 9 of 142. Recurrent VTE is time-to-event, NOT a '
        'continuous endpoint.",'
        'highlights:["0.7%","6.3%","0.099","145","142"],'
        'sourceUrl:"https://doi.org/10.1111/jth.14662"},'
        '{label:"Major bleeding (this trial\'s PRIMARY outcome)",'
        'source:"J Thromb Haemost 2020; 18:411-421",'
        'text:"The primary outcome was major bleeding. Major bleeding occurred in 0% of 145 patients '
        'receiving apixaban, compared with 1.4% of 142 patients receiving dalteparin [P=.138; hazard '
        'ratio NOT ESTIMABLE because of 0 bleeding events in the apixaban group] - that is 0/145 vs '
        '2/142. ClinicalTrials.gov posts the same outcome as 0% vs 2.1%, a discordance of one event '
        'against the publication; the published 0 vs 2 counts are used.",'
        'highlights:["0%","1.4%","145","142","not estimable"],'
        'sourceUrl:"https://doi.org/10.1111/jth.14662"},'
        '{label:"Eligibility (AACT-derived)",source:"AACT 2026-04-12 eligibilities.txt",'
        'text:' + js_str(ADAM_ELIG) + ',highlights:["AACT-derived"]}]},'

        # ---------------- CARAVAGGIO ----------------
        'NCT03045406:{baseline:{n:1155,age:67.2,female:56.5,cancer_gi:31},'
        'name:"CARAVAGGIO",pmid:"32223112",doi:"10.1056/NEJMoa1915103",phase:"III",year:2020,'
        'registryId:"NCT03045406",'
        'tE:32,tN:576,cE:46,cN:579,group:"Apixaban",'
        'publishedHR:.63,hrLCI:.37,hrUCI:1.07,estimandType:"HR",'
        'allOutcomes:['
        '{shortLabel:"VTE",title:"Recurrent VTE (trial PRIMARY outcome)",'
        'tE:32,cE:46,type:"PRIMARY",pubHR:.63,pubHR_LCI:.37,pubHR_UCI:1.07,estimandType:"HR",'
        'timepoint:"6 months"},'
        '{shortLabel:"MajBleed",title:"Major bleeding (principal safety outcome)",'
        'tE:22,cE:23,type:"SAFETY",pubHR:.82,pubHR_LCI:.4,pubHR_UCI:1.69,estimandType:"HR",'
        'timepoint:"6 months"}],'
        'rob:["low","some","low","low","low"],'
        'robSource:"RoB 2, manual. Open-label administration with BLINDED CENTRAL OUTCOME ADJUDICATION, '
        'stated in the NEJM 2020;382:1599-1607 design description.",'
        'snippet:"N Engl J Med 2020; 382:1599-1607",'
        'sourceUrl:"https://doi.org/10.1056/NEJMoa1915103",'
        'ctgovUrl:"https://clinicaltrials.gov/study/NCT03045406",'
        'evidence:['
        '{label:"Recurrent VTE (review primary outcome)",source:"NEJM 2020; 382:1599-1607",'
        'text:"Recurrent venous thromboembolism occurred in 32 of 576 patients (5.6%) in the apixaban '
        'group and in 46 of 579 patients (7.9%) in the dalteparin group (hazard ratio, 0.63; 95% CI, '
        '0.37 to 1.07; P<0.001 for noninferiority). ClinicalTrials.gov posts the identical 32/576 and '
        '46/579.",'
        'highlights:["32","576","46","579","0.63"],'
        'sourceUrl:"https://doi.org/10.1056/NEJMoa1915103"},'
        '{label:"Major bleeding",source:"NEJM 2020; 382:1599-1607",'
        'text:"Major bleeding occurred in 22 patients (3.8%) in the apixaban group and in 23 patients '
        '(4.0%) in the dalteparin group (hazard ratio, 0.82; 95% CI, 0.40 to 1.69; P=0.60).",'
        'highlights:["22","23","0.82"],'
        'sourceUrl:"https://doi.org/10.1056/NEJMoa1915103"},'
        '{label:"Eligibility (AACT-derived)",source:"AACT 2026-04-12 eligibilities.txt",'
        'text:' + js_str(CARAVAGGIO_ELIG) + ',highlights:["AACT-derived"]}]}'
        '}'
    )


def js_str(s):
    """Emit a JS single-quoted string literal with the few characters that matter escaped."""
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def main():
    if not os.path.exists(TARGET):
        sys.exit('missing target: %s' % TARGET)
    raw = open(TARGET, 'rb').read()
    had_bom = raw.startswith(b'\xef\xbb\xbf')
    src = raw.decode('utf-8-sig')
    if had_bom:
        # The file ships with a UTF-8 BOM on main. That is a pre-existing corpus-wide
        # condition, not something this fix introduces, so it is preserved byte-for-byte
        # rather than silently changed here.
        print('note: target carries a UTF-8 BOM (pre-existing); preserving it')

    build_edits(src)

    applied = []
    for tag, old, new, count in EDITS:
        found = src.count(old)
        if found != count:
            sys.exit('ANCHOR MISMATCH [%s]: expected %d occurrence(s), found %d.\n  anchor: %.160s'
                     % (tag, count, found, old))
        src = src.replace(old, new)
        applied.append(tag)

    out = src.encode('utf-8')
    if had_bom:
        out = b'\xef\xbb\xbf' + out
    with open(TARGET, 'wb') as fh:
        fh.write(out)

    print('applied %d anchored edits to %s' % (len(applied), os.path.basename(TARGET)))
    for t in applied:
        print('  -', t)


def build_edits(src):
    # -- 1. realData -------------------------------------------------------
    i = src.find('realData:{')
    if i < 0:
        sys.exit('realData not found')
    j = src.index('{', i)
    k = match_brace(src, j)
    edit('realData: corrected 4-trial canonical extraction', src[j:k + 1], rd())

    # -- 2. auto-include id set (SELECT-D re-keyed off CONKO-011's NCT) -----
    edit('AUTO_INCLUDE_TRIAL_IDS: NCT02583191 (CONKO-011) -> ISRCTN86712308 (SELECT-D)',
         'AUTO_INCLUDE_TRIAL_IDS=new Set(["NCT02073682","NCT02583191","NCT02585713","NCT03045406"])',
         'AUTO_INCLUDE_TRIAL_IDS=new Set(["NCT02073682","ISRCTN86712308","NCT02585713","NCT03045406"])')

    edit('NMAEngine trial id list: same re-key',
         '["NCT02073682","NCT02583191","NCT02585713","NCT03045406"].filter(id=>!RapidMeta.state.excludedTrials',
         '["NCT02073682","ISRCTN86712308","NCT02585713","NCT03045406"].filter(id=>!RapidMeta.state.excludedTrials')

    # -- 3. remaining id maps ---------------------------------------------
    edit('KNOWN_TRIAL_ALIASES: SELECT-D was aliased to CONKO-011\'s NCT',
         'KNOWN_TRIAL_ALIASES={NCT02073682:["hokusai vte-cancer","hokusai"],'
         'NCT02583191:["select-d","select d"],NCT02585713:["adam vte","adam"],'
         'NCT03045406:["caravaggio"]}',
         'KNOWN_TRIAL_ALIASES={NCT02073682:["hokusai vte-cancer","hokusai"],'
         'ISRCTN86712308:["select-d","select d"],NCT02585713:["adam vte","adam"],'
         'NCT03045406:["caravaggio"],NCT02746185:["casta-diva","casta diva"],'
         'NCT02744092:["canvas"],NCT02583191:["conko-011","conko 011"]}')

    edit('nctAcronyms: NCT02583191 labelled SELECT-D; it is CONKO-011',
         'nctAcronyms:{NCT02073682:"HOKUSAI VTE-Cancer",NCT02583191:"SELECT-D",'
         'NCT02585713:"ADAM VTE",NCT03045406:"CARAVAGGIO"}',
         'nctAcronyms:{NCT02073682:"HOKUSAI VTE-Cancer",ISRCTN86712308:"SELECT-D",'
         'NCT02585713:"ADAM VTE",NCT03045406:"CARAVAGGIO",NCT02746185:"CASTA-DIVA",'
         'NCT02744092:"CANVAS",NCT02583191:"CONKO-011"}')

    # -- 4. published-benchmark scope text (Hokusai 0.71 is NOT the composite)
    edit('benchmark scope: Hokusai HR 0.71 is the recurrent-VTE component, not the composite',
         'scope:"Edoxaban vs dalteparin in cancer-associated VTE; recurrent VTE or major bleeding at '
         '12 mo. NEJM 2018;378:615-624."',
         'scope:"Edoxaban vs dalteparin in cancer-associated VTE; RECURRENT VTE component at 12 mo '
         '(the trial primary was the composite of recurrent VTE or major bleeding, HR 0.97, 0.70-1.36). '
         'NEJM 2018;378:615-624; ClinicalTrials.gov NCT02073682 posted results."')

    # -- 5. PROTOCOL: registration claim -----------------------------------
    edit('protocol: delete the PROSPERO-equivalence claim',
         'Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration '
         'record equivalent to PROSPERO for tracking outcome / eligibility / analysis-plan changes.',
         'The GitHub commit hash and timestamp give a verifiable, tamper-evident record of when each '
         'protocol change was made. That is NOT a prospective registration and is NOT equivalent to '
         'PROSPERO: this protocol was written after the trials it synthesises were published, and the '
         'review is not registered in PROSPERO or OSF.')

    # -- 6. PROTOCOL: PICO -------------------------------------------------
    #
    #    NOTE: the external review reported the PICO as blank. It is not. The five
    #    PICO cells are <input> elements whose values live in state.protocol, and
    #    innerText-style page scraping does not see an input's value. They were
    #    populated but thin. This edit sharpens them; it does not fill a blank.
    #    The same object carries a dead `post2015` flag, which is the machine-readable
    #    form of the date criterion being removed and is switched off here.
    edit('protocol seed: sharpen the (already populated) PICO and clear the post-2015 flag',
         'state:{protocol:{pop:"Adults with Active Cancer and Acute VTE",'
         'int:"DOAC (Apixaban, Edoxaban, or Rivaroxaban)",'
         'comp:"LMWH (Dalteparin or Enoxaparin)",out:"Recurrent VTE",'
         'subgroup:"DOAC type (Apixaban vs Edoxaban vs Rivaroxaban), Cancer type (GI vs non-GI), '
         'VTE type (PE vs DVT)",query:"",rctOnly:!0,post2015:!0}',
         'state:{protocol:{pop:%s,int:%s,comp:%s,out:%s,subgroup:%s,query:"",rctOnly:!0,post2015:!1}'
         % (js_str(PICO['Population']), js_str(PICO['Intervention']), js_str(PICO['Comparator']),
            js_str(PICO['Primary Outcome']), js_str(PICO['Subgroup Plan'])))

    for iid, field in (('p-pop', 'Population'), ('p-int', 'Intervention'), ('p-comp', 'Comparator'),
                       ('p-out', 'Primary Outcome'), ('p-subgroup', 'Subgroup Plan')):
        m = [x for x in ATTR_VALUES if x[0] == iid][0]
        edit('PICO markup default: %s' % field,
             'id="%s" class="w-full bg-transparent outline-none font-medium text-slate-200" '
             'value="%s"' % (iid, m[1]),
             'id="%s" class="w-full bg-transparent outline-none font-medium text-slate-200" '
             'value="%s"' % (iid, html_attr(PICO[field])))

    # -- 7. PROTOCOL: eligibility table ------------------------------------
    edit('eligibility: comparator criterion would have excluded every trial in the review',
         '<td class="p-3 font-bold text-slate-400">Comparator</td><td class="p-3 text-slate-300">'
         'Placebo, sham, or standard of care</td><td class="p-3 text-slate-400">Active comparator '
         'without placebo arm</td>',
         '<td class="p-3 font-bold text-slate-400">Comparator</td><td class="p-3 text-slate-300">'
         'Therapeutic-dose low-molecular-weight heparin (dalteparin, tinzaparin, enoxaparin) as the '
         'active control. This review has no placebo comparison and none is possible: withholding '
         'anticoagulation in acute cancer-associated VTE is not ethical.</td>'
         '<td class="p-3 text-slate-400">Vitamin-K-antagonist-only, DOAC-vs-DOAC, or unfractionated-'
         'heparin-only comparisons; single-arm designs</td>')

    edit('eligibility: MACE/CV endpoint criterion is template contamination',
         '<td class="p-3 font-bold text-slate-400">Outcomes</td><td class="p-3 text-slate-300">'
         '&ge;1 primary cardiovascular efficacy endpoint (mortality, stroke, MI, VTE, composite MACE) '
         'with extractable data</td>',
         '<td class="p-3 font-bold text-slate-400">Outcomes</td><td class="p-3 text-slate-300">'
         'Objectively confirmed recurrent VTE reported as a relative time-to-event effect or as arm-'
         'level events and denominators. Secondary: ISTH major bleeding, CRNMB, all-cause mortality.'
         '</td>')

    edit('eligibility: remove the pre-2015 date criterion (eligibility is by PICO, never by date)',
         '<td class="p-3 font-bold text-slate-400">Publication</td><td class="p-3 text-slate-300">'
         'Published or registered; any language</td><td class="p-3 text-slate-400">Pre-2015; '
         'duplicate cohorts; editorials, letters, reviews</td>',
         '<td class="p-3 font-bold text-slate-400">Publication</td><td class="p-3 text-slate-300">'
         'Published or registered; any language; any year. Eligibility is decided by PICO, scope and '
         'data availability only. Where a trial predates the indexed full-text window, data are taken '
         'from prior meta-analysis supplements, then FDA/EMA documents, then open-access sources.</td>'
         '<td class="p-3 text-slate-400">Duplicate cohorts; editorials, letters, narrative reviews. '
         'NO DATE CRITERION.</td>')

    edit('eligibility: phase criterion, aligned to the registered phase of record',
         '<td class="p-3 font-bold text-slate-400">Phase</td><td class="p-3 text-slate-300">Phase III '
         'or IV</td><td class="p-3 text-slate-400">Phase I/II (including IIa/IIb), PK/PD, dose-finding, '
         'bioequivalence, first-in-human</td>',
         '<td class="p-3 font-bold text-slate-400">Phase</td><td class="p-3 text-slate-300">Phase III '
         'or IV as recorded in the trial registry of record. SELECT-D is registered Phase III on '
         'ISRCTN86712308 although its publication describes it as a pilot; the registry phase '
         'governs.</td><td class="p-3 text-slate-400">Phase I/II (including IIa/IIb), PK/PD, '
         'dose-finding, bioequivalence, first-in-human</td>')

    # -- 8. PROTOCOL: impossible method claims -----------------------------
    # The rendered "Effect Measure" row is written by JS, not by the static markup. With
    # state.effectMeasure = "HR" it produced "Hazard Ratio (HR) computed on log scale;
    # 0.5 continuity correction for zero cells" - an impossible method, because a hazard
    # ratio cannot be reconstructed from a 2x2 table and a continuity correction is an
    # OR/RR device. Fixed at the generator.
    edit('effect-measure caption: an HR cannot be reconstructed from a 2x2 table',
         '`${long} (${short}) computed on log scale; 0.5 continuity correction for zero cells`',
         '"HR"===short?`Hazard Ratio (HR) pooled on the log scale by generic inverse variance from '
         'the published hazard ratio and its confidence interval. Hazard ratios are NEVER '
         'reconstructed from 2x2 counts: an HR depends on event timing a 2x2 table does not carry, '
         'and the 0.5 continuity correction is an odds-ratio / risk-ratio device that does not apply '
         'to it.`:`${long} (${short}) computed on log scale from 2x2 counts; 0.5 continuity '
         'correction for zero cells`')

    edit('protocol: pin one primary pooling model instead of three different claims',
         '<td class="p-3 font-bold text-slate-400">Pooling Model</td><td class="p-3 text-slate-300">'
         'REML random-effects, HKSJ-adjusted (inverse-variance weighting)</td>',
         '<td class="p-3 font-bold text-slate-400">Pooling Model</td>'
         '<td class="p-3 text-slate-300">DerSimonian-Laird random effects on log HR by generic '
         'inverse variance. This is the single primary model. REML and Paule-Mandel are reported as '
         'sensitivity estimators only. Because k = 4, both DL and REML are known to be imprecise for '
         'tau-squared, so the HKSJ interval is reported alongside every DL interval and is the '
         'interval that should be quoted.</td>')

    edit('protocol: Bayesian module refers to OR while the review pools HR',
         'half-normal prior on &tau;; posterior OR + CrI + P(OR&lt;1)',
         'half-normal prior on &tau;; posterior HR + CrI + P(HR&lt;1)')

    edit('protocol: meta-regression refers to log-OR while the review pools HR',
         'WLS on log-OR; covariates: Year, Phase, Indication',
         'WLS on log HR; covariates: Year, Phase, Indication. NOT INTERPRETABLE at k = 4 and reported '
         'for completeness only')

    edit('protocol: GRADE imprecision MID stated on the OR scale',
         'CI crosses MID (OR = 0.80 or 1.25) or optimal information size not met',
         'CI crosses MID (HR = 0.80 or 1.25) or optimal information size not met')

    edit('protocol: cross-validation claim names OR',
         'independent replication of pooled OR, CI, &tau;&sup2;',
         'independent replication of pooled HR, CI, &tau;&sup2;')

    edit('protocol: AMSTAR-11 row must match the pinned primary model',
         '<td class="p-3 text-emerald-400">Section 8: DL RE + HKSJ, R/Python cross-validated</td>',
         '<td class="p-3 text-emerald-400">Section 8: DerSimonian-Laird random effects with HKSJ '
         'intervals, cross-validated in R 4.6.0 / metafor 5.0.1 and in Python '
         '(scripts/doac_cancer_vte_pool.R and .py)</td>')

    edit('protocol: PubMed search string too narrow to retrieve eligible trials',
         'doac cancer venous thromboembolism AND (TITLE:randomized OR PUB_TYPE:"Randomized '
         'Controlled Trial" OR PUB_TYPE:"Clinical Trial") AND SRC:MED',
         '(doac OR "direct oral anticoagulant" OR apixaban OR rivaroxaban OR edoxaban OR dabigatran) '
         'AND (dalteparin OR tinzaparin OR enoxaparin OR "low molecular weight heparin" OR LMWH) AND '
         '("cancer associated thrombosis" OR "cancer associated venous thromboembolism" OR (cancer '
         'AND ("venous thromboembolism" OR "pulmonary embolism" OR "deep vein thrombosis"))) AND '
         '(TITLE:randomized OR PUB_TYPE:"Randomized Controlled Trial" OR PUB_TYPE:"Clinical Trial") '
         'AND SRC:MED', count=3)  # protocol table, search panel, and the live Europe PMC query

    edit('protocol: OpenAlex search string equally narrow',
         'search=doac cancer venous thromboembolism&amp;filter=concepts.id:C71924100&amp;per_page=50',
         'search=(apixaban OR rivaroxaban OR edoxaban OR dabigatran OR direct oral anticoagulant) '
         '(dalteparin OR tinzaparin OR enoxaparin OR low molecular weight heparin) cancer associated '
         'thrombosis&amp;filter=concepts.id:C71924100&amp;per_page=200', count=2)

    edit('live registry query: broaden and drop the COMPLETED-only status filter',
         'https://clinicaltrials.gov/api/v2/studies?query.intr=direct oral anticoagulant AND cancer '
         'AND thromboembolism&pageSize=100&filter.overallStatus=COMPLETED',
         'https://clinicaltrials.gov/api/v2/studies?query.intr=(apixaban OR rivaroxaban OR edoxaban '
         'OR dabigatran OR direct oral anticoagulant) AND (dalteparin OR tinzaparin OR enoxaparin OR '
         'low molecular weight heparin)&query.cond=cancer AND venous thromboembolism&pageSize=200')

    edit('protocol + search panel: registry search string equally narrow, and a status filter '
         'that hid the terminated trial the review had mis-identified',
         'query.intr=direct oral anticoagulant AND cancer AND thromboembolism&amp;pageSize=100&amp;'
         'filter.overallStatus=COMPLETED',
         'query.intr=(apixaban OR rivaroxaban OR edoxaban OR dabigatran OR direct oral '
         'anticoagulant) AND (dalteparin OR tinzaparin OR enoxaparin OR low molecular weight '
         'heparin)&amp;query.cond=cancer AND venous thromboembolism&amp;pageSize=200 &mdash; NO '
         'overallStatus filter: terminated and withdrawn trials must be retrieved so they can be '
         'adjudicated rather than silently missed', count=2)

    # -- 9. NARRATIVE: kill the finerenone/CV template contamination -------
    edit('narrative: DOACs are not an MRA and the comparator is not placebo',
         'narrative=`DOACs, a non-steroidal mineralocorticoid receptor antagonist, ${effectClause} '
         'compared with placebo across',
         'narrative=`Direct oral anticoagulants (apixaban, rivaroxaban, edoxaban) ${effectClause} '
         'compared with therapeutic-dose low-molecular-weight heparin across')

    edit('narrative: default outcome prose was a CKD cardiovascular composite',
         'ocProse={default:"the matched cardiovascular composite endpoint across CKD trials",'
         'MACE:"the cardiovascular composite endpoint",',
         'ocProse={default:"objectively confirmed recurrent venous thromboembolism",'
         'VTE:"objectively confirmed recurrent venous thromboembolism",'
         'MajBleed:"ISTH major bleeding",'
         'Composite:"the composite of recurrent venous thromboembolism or major bleeding",'
         'MACE:"the cardiovascular composite endpoint",')

    edit('verdict banner: same contamination on the visual-abstract verdict line',
         'verdictOutcome={default:"the matched cardiovascular composite endpoint",'
         'MACE:"the cardiovascular composite endpoint",',
         'verdictOutcome={default:"objectively confirmed recurrent venous thromboembolism",'
         'VTE:"objectively confirmed recurrent venous thromboembolism",'
         'MajBleed:"ISTH major bleeding",'
         'Composite:"the composite of recurrent venous thromboembolism or major bleeding",'
         'MACE:"the cardiovascular composite endpoint",')

    edit('forest caption: placebo/MACE contamination',
         'Fig. — Forest plot of doacs vs placebo for MACE composite (random-effects, DL estimator)',
         'Fig. — Forest plot of direct oral anticoagulants vs low-molecular-weight heparin for '
         'recurrent venous thromboembolism (random-effects, DL estimator)')

    edit('visual abstract: the acquisition-era badge restates the deleted date criterion',
         '<div class="va-label">Acquisition Era</div><div class="va-value">Post-2015 Enrollment</div>',
         '<div class="va-label">Comparator</div><div class="va-value">Therapeutic-dose LMWH</div>')

    # -- 10. Fragility index: FI = 0 is not robustness ---------------------
    edit('fragility: "FI = 0 means robust" is backwards and is removed',
         'fragNote=void 0!==r.fragIdx?` The fragility index is <span class="nyt-stat-inline">'
         '${r.fragIdx}</span>, meaning ${0===r.fragIdx?"the result is robust to event modifications":'
         'r.fragIdx+" event modification(s) across trials would reverse statistical significance"}.`:""',
         'fragNote=void 0!==r.fragIdx&&r.fragIdx>0?` The fragility index is <span class='
         '"nyt-stat-inline">${r.fragIdx}</span>, meaning ${r.fragIdx} event modification(s) across '
         'trials would reverse statistical significance.`:" The fragility index is not informative '
         'for this analysis: it is defined for a pool of 2x2 counts, and the primary estimate is '
         'pooled from published hazard ratios."')

    # -- 10b. estimator label vs estimator actually used --------------------
    #
    #    results.estimator, the CI-comparison legend and the protocol all say
    #    DerSimonian-Laird, but the headline weights used tau2_reml. On the corrected
    #    data that is the difference between HR 0.62 (0.46-0.83, tau2 ~ 0, REML) and
    #    HR 0.58 (0.39-0.86, tau2 = 0.0490, DL) - reported next to a DL-derived
    #    I2 of 30%, i.e. random-effects heterogeneity shown beside fixed-effect
    #    weights. Verified against R metafor 5.0.1: DL tau2 0.048966 -> 0.5808
    #    (0.3909-0.8630); REML tau2 0.000002 -> 0.6162 (0.4589-0.8275).
    #    The pinned primary model is DL, so the code is made to match the label.
    edit('headline estimator: computed REML while labelled DL; pin DL as the protocol says',
         'const tau2=k>=2?tau2_reml:tau2_dl,_qpYi=plotData.map(d=>d.logOR)',
         'const tau2=tau2_dl,_tau2RemlSensitivity=k>=2?tau2_reml:tau2_dl,'
         '_qpYi=plotData.map(d=>d.logOR)')

    # -- 10c. Paule-Mandel solver sign error --------------------------------
    #
    #    Newton on f(t) = Q(t) - (k-1) needs t <- t - f/f'. The code used t + f/f'.
    #    f' is negative, so whenever Q > k-1 - which is exactly when heterogeneity
    #    exists - the step went negative, was clamped to 0 by Math.max, and the loop
    #    exited on the no-change test reporting tau2 = 0. The Paule-Mandel estimator,
    #    the one the app itself describes as "recommended for small k", could
    #    therefore only ever return zero. On this data the correct value is 0.144808
    #    (R metafor 5.0.1, method="PM"); the app returned 0.
    edit('Paule-Mandel tau2: Newton step had the wrong sign and always returned 0',
         'var t2new = Math.max(0, tau2 + diff / slope);',
         'var t2new = Math.max(0, tau2 - diff / slope);')

    # -- 11. NNT/NNH: never assert either when the interval spans the null --
    edit('NNT/NNH: suppress both when the confidence interval crosses 1',
         'nnt="harm"===effect.direction&&nnhValue?`NNH ${nnhValue}`:nntValue?nntValue.toString():"--"',
         'nnt=effect.significant?"harm"===effect.direction&&nnhValue?`NNH ${nnhValue}`:'
         '"benefit"===effect.direction&&nntValue?nntValue.toString():"--":"--"')

    edit('NNT/NNH sentence: only when the interval excludes the null',
         'absoluteRiskSentence="benefit"===effect.direction&&nntValue?',
         'absoluteRiskSentence=!effect.significant?" Because the confidence interval includes no '
         'effect, neither a number needed to treat nor a number needed to harm is reported: both '
         'would assert a direction the data do not establish.":"benefit"===effect.direction&&nntValue?')

    edit('waiting-room pictogram: do not paint people as harmed on a non-significant interval',
         'iconContainer.innerHTML=icons,document.getElementById("wr-icon-label").textContent='
         '0===affectedPer100?"No measurable effect per 100 patients":affectedPer100+" out of 100 '
         'patients "+(isBenefit?"benefit":isHarm?"may be harmed":"affected")',
         'iconContainer.innerHTML=icons,document.getElementById("wr-icon-label").textContent='
         '0===affectedPer100?"No measurable effect per 100 patients":affectedPer100+" out of 100 '
         'patients "+(isBenefit?"benefit":isHarm?"may be harmed":"may be affected - the result could '
         'be a benefit or a harm")')

    # The L'Abbe caption asserted "below the line = benefit" unconditionally, which is
    # wrong when the plotted outcome is a harm (major bleeding): below the line then means
    # fewer bleeds, which is a safety signal, not efficacy. Made outcome-aware.
    edit('L\'Abbe caption: "below the line = benefit" is wrong for a harm outcome',
         'setDesc("desc-labbe","Each point represents one trial. Points below the diagonal line of '
         'equality indicate lower event rates in the "+(RapidMeta.state.protocol?.int??"intervention")'
         '+" arm compared to control. Clustering below the line supports the pooled estimate of '
         'benefit.")',
         'setDesc("desc-labbe","Each point represents one trial. Points below the diagonal line of '
         'equality indicate lower event rates in the "+(RapidMeta.state.protocol?.int??"intervention")'
         '+" arm compared to control. "+("MajBleed"===String(RapidMeta.state.selectedOutcome??"")?'
         '"The plotted outcome is major bleeding, which is a HARM: points below the line are trials '
         'with fewer bleeds on the DOAC arm, which is a safety finding and not a treatment benefit.":'
         '"The plotted outcome is recurrent VTE, which is the event the treatment is meant to '
         'prevent: points below the line are trials with fewer recurrences on the DOAC arm.")+'
         '" At k = 4 the scatter cannot support any inference about heterogeneity or asymmetry.")')


def match_brace(s, j):
    """String-aware brace matcher; returns the index of the '}' closing s[j] == '{'."""
    backslash = chr(92)
    d = 0
    k = j
    n = len(s)
    while k < n:
        c = s[k]
        if c in '"\'`':
            q = c
            k += 1
            while k < n:
                if s[k] == backslash:
                    k += 2
                    continue
                if s[k] == q:
                    break
                k += 1
        elif c == '{':
            d += 1
        elif c == '}':
            d -= 1
            if d == 0:
                return k
        k += 1
    raise ValueError('unbalanced braces')


def html_attr(s):
    return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')


# The literal value="..." defaults present in the markup on origin/main.
ATTR_VALUES = [
    ('p-pop', 'Patients with cancer-associated VTE'),
    ('p-int', 'DOAC (apixaban, edoxaban, rivaroxaban)'),
    ('p-comp', 'LMWH (dalteparin)'),
    ('p-out', 'Recurrent VTE'),
    ('p-subgroup', 'Cancer type (GI vs other), bleeding risk, platelets'),
]

PICO = {
    'Population': (
        'Adults (≥ 18 years) with active cancer and acute, objectively confirmed symptomatic or '
        'incidental venous thromboembolism (proximal lower-limb deep-vein thrombosis, pulmonary '
        'embolism, or both) requiring therapeutic anticoagulation.'),
    'Intervention': (
        'A direct oral anticoagulant at a therapeutic treatment dose - apixaban, rivaroxaban, '
        'edoxaban or dabigatran - given for at least 3 months.'),
    'Comparator': (
        'Therapeutic-dose low-molecular-weight heparin, principally dalteparin. There is no placebo '
        'comparator and none is possible in this indication.'),
    'Primary Outcome': (
        'Objectively confirmed recurrent venous thromboembolism, pooled as a relative time-to-event '
        'effect (hazard ratio).'),
    'Subgroup Plan': (
        'Pre-specified but NOT PERFORMED - at k = 4 no subgroup or meta-regression analysis is '
        'interpretable. Had power allowed: DOAC agent, gastrointestinal versus non-gastrointestinal '
        'primary tumour, index event (PE versus DVT), and treatment duration.'),
}


if __name__ == '__main__':
    main()
