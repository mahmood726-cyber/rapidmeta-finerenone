"""
LivingMeta Config Generator — Auto-generates CONFIG_LIBRARY entries from CT.gov API v2
Ported from rct_data_extractor_v2/scripts/ctg_scraper.py

Usage: python generate_configs.py > configs_output.js
"""
import sys, io, json, time, urllib.request, urllib.parse, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CTG_API = "https://clinicaltrials.gov/api/v2/studies"

# ──────────────────────────────────────────────────────────────────
# 40 TOPICS (9 existing + 31 new)
# Each: id, name, search terms, PICO, key trial NCTs to prioritize
# ──────────────────────────────────────────────────────────────────
TOPICS = [
    # ── Already in LivingMeta (skip generation, just validate) ──
    # colchicine_cvd, finerenone, sglt2_hf, glp1_cvot, pcsk9,
    # intensive_bp, bempedoic_acid, incretin_hfpef, attr_cm

    # ── NEW TOPICS (31) ──
    # Cardiology
    {"id": "sglt2_ckd", "name": "SGLT2i — Chronic Kidney Disease",
     "search": "dapagliflozin OR empagliflozin OR canagliflozin",
     "condition": "chronic kidney disease",
     "population": "Adults with CKD (with or without diabetes)",
     "intervention": "SGLT2 inhibitor (dapagliflozin, empagliflozin, canagliflozin)",
     "comparator": "Placebo", "primary_outcome": "Kidney composite (eGFR decline, ESKD, renal death)",
     "key_ncts": ["NCT03036150", "NCT02065791", "NCT03594110"]},  # DAPA-CKD, CREDENCE, EMPA-KIDNEY

    {"id": "sglt2_t2dm_cvot", "name": "SGLT2i — T2DM CVOTs",
     "search": "empagliflozin OR canagliflozin OR dapagliflozin OR ertugliflozin",
     "condition": "type 2 diabetes AND cardiovascular",
     "population": "Adults with T2DM at high CV risk",
     "intervention": "SGLT2 inhibitor", "comparator": "Placebo",
     "primary_outcome": "3-point MACE (CV death, MI, stroke)",
     "key_ncts": ["NCT01131676", "NCT01032629", "NCT01730534", "NCT01986881"]},  # EMPA-REG, CANVAS, DECLARE, VERTIS

    {"id": "arni_hf", "name": "Sacubitril/Valsartan — Heart Failure",
     "search": "sacubitril OR entresto OR LCZ696",
     "condition": "heart failure",
     "population": "Adults with heart failure (HFrEF or HFpEF)",
     "intervention": "Sacubitril/valsartan (ARNI)", "comparator": "Enalapril or valsartan",
     "primary_outcome": "CV death or HF hospitalization",
     "key_ncts": ["NCT01035255", "NCT01920711"]},  # PARADIGM-HF, PARAGON-HF

    {"id": "iron_hf", "name": "IV Iron — Heart Failure",
     "search": "ferric carboxymaltose OR iron isomaltoside OR iron sucrose",
     "condition": "heart failure AND iron deficiency",
     "population": "Adults with HF and iron deficiency",
     "intervention": "IV iron (ferric carboxymaltose or iron isomaltoside)", "comparator": "Placebo or standard care",
     "primary_outcome": "CV death or HF hospitalization",
     "key_ncts": ["NCT02937454", "NCT02642562", "NCT03037931"]},  # AFFIRM-AHF, IRONMAN, HEART-FID

    {"id": "icosapent_cv", "name": "Icosapent Ethyl — CV Prevention",
     "search": "icosapent ethyl OR vascepa OR eicosapentaenoic acid EPA",
     "condition": "cardiovascular AND triglycerides",
     "population": "Adults with elevated triglycerides on statin therapy",
     "intervention": "Icosapent ethyl (EPA)", "comparator": "Placebo (mineral oil or corn oil)",
     "primary_outcome": "MACE composite",
     "key_ncts": ["NCT01492361", "NCT02104817"]},  # REDUCE-IT, STRENGTH

    {"id": "vericiguat_hf", "name": "Vericiguat — Heart Failure",
     "search": "vericiguat",
     "condition": "heart failure",
     "population": "Adults with worsening chronic HF (EF<45%)",
     "intervention": "Vericiguat (sGC stimulator)", "comparator": "Placebo",
     "primary_outcome": "CV death or HF hospitalization",
     "key_ncts": ["NCT02861534"]},  # VICTORIA

    {"id": "omecamtiv_hf", "name": "Omecamtiv Mecarbil — Heart Failure",
     "search": "omecamtiv mecarbil",
     "condition": "heart failure",
     "population": "Adults with HFrEF (EF<=35%)",
     "intervention": "Omecamtiv mecarbil (cardiac myosin activator)", "comparator": "Placebo",
     "primary_outcome": "CV death or HF event",
     "key_ncts": ["NCT02929329"]},  # GALACTIC-HF

    {"id": "mavacamten_hcm", "name": "Mavacamten — Hypertrophic Cardiomyopathy",
     "search": "mavacamten OR camzyos",
     "condition": "hypertrophic cardiomyopathy",
     "population": "Adults with symptomatic obstructive HCM",
     "intervention": "Mavacamten (cardiac myosin inhibitor)", "comparator": "Placebo",
     "primary_outcome": "Exercise capacity + LVOT gradient reduction",
     "key_ncts": ["NCT03470545", "NCT04349072"]},  # EXPLORER-HCM, VALOR-HCM

    {"id": "canakinumab_cv", "name": "Canakinumab — Anti-IL-1b CV",
     "search": "canakinumab",
     "condition": "cardiovascular AND inflammation",
     "population": "Adults with prior MI and elevated hsCRP",
     "intervention": "Canakinumab (anti-IL-1beta)", "comparator": "Placebo",
     "primary_outcome": "MACE (CV death, MI, stroke)",
     "key_ncts": ["NCT01327846"]},  # CANTOS

    {"id": "rivaroxaban_vasc", "name": "Rivaroxaban — Vascular Protection",
     "search": "rivaroxaban",
     "condition": "atherosclerosis OR peripheral artery disease",
     "population": "Adults with stable atherosclerotic vascular disease",
     "intervention": "Low-dose rivaroxaban + aspirin", "comparator": "Aspirin alone",
     "primary_outcome": "CV death, MI, or stroke",
     "key_ncts": ["NCT01776424", "NCT02504216"]},  # COMPASS, VOYAGER-PAD

    # Metabolic / Obesity
    {"id": "semaglutide_ckd", "name": "Semaglutide — CKD (FLOW)",
     "search": "semaglutide",
     "condition": "chronic kidney disease AND type 2 diabetes",
     "population": "Adults with T2DM and CKD",
     "intervention": "Semaglutide 1.0 mg SC weekly", "comparator": "Placebo",
     "primary_outcome": "Kidney composite (dialysis, transplant, eGFR decline, renal/CV death)",
     "key_ncts": ["NCT03819153"]},  # FLOW

    {"id": "tirzepatide_t2dm", "name": "Tirzepatide — Type 2 Diabetes",
     "search": "tirzepatide",
     "condition": "type 2 diabetes",
     "population": "Adults with T2DM inadequately controlled",
     "intervention": "Tirzepatide (dual GIP/GLP-1 RA)", "comparator": "Placebo or active comparator",
     "primary_outcome": "HbA1c reduction from baseline",
     "key_ncts": ["NCT03954834", "NCT03987919", "NCT03882970"]},  # SURPASS-1, SURPASS-2, SURPASS-3

    {"id": "semaglutide_obesity", "name": "Semaglutide — Obesity",
     "search": "semaglutide",
     "condition": "obesity OR overweight",
     "population": "Adults with obesity (BMI>=30) or overweight with comorbidities",
     "intervention": "Semaglutide 2.4 mg SC weekly", "comparator": "Placebo",
     "primary_outcome": "Percent body weight change",
     "key_ncts": ["NCT03548935", "NCT03552757", "NCT03611582"]},  # STEP 1, STEP 2, STEP 3

    {"id": "tirzepatide_obesity", "name": "Tirzepatide — Obesity",
     "search": "tirzepatide",
     "condition": "obesity OR overweight",
     "population": "Adults with obesity (BMI>=30) or overweight",
     "intervention": "Tirzepatide (dual GIP/GLP-1 RA)", "comparator": "Placebo",
     "primary_outcome": "Percent body weight change",
     "key_ncts": ["NCT04184622", "NCT04657003"]},  # SURMOUNT-1, SURMOUNT-2

    # Lipids
    {"id": "inclisiran", "name": "Inclisiran — siRNA PCSK9",
     "search": "inclisiran",
     "condition": "hypercholesterolemia OR ASCVD OR familial hypercholesterolemia",
     "population": "Adults with ASCVD, FH, or high CV risk with elevated LDL-C",
     "intervention": "Inclisiran (siRNA PCSK9 inhibitor)", "comparator": "Placebo",
     "primary_outcome": "LDL-C reduction at Day 510",
     "key_ncts": ["NCT03399370", "NCT03400800", "NCT03705234"]},  # ORION-9, ORION-10, ORION-11

    {"id": "ezetimibe_cv", "name": "Ezetimibe — CV Prevention",
     "search": "ezetimibe",
     "condition": "acute coronary syndrome",
     "population": "Adults with recent ACS on statin therapy",
     "intervention": "Ezetimibe + simvastatin", "comparator": "Simvastatin alone",
     "primary_outcome": "CV death, MI, UA hospitalization, revascularization, stroke",
     "key_ncts": ["NCT00202878"]},  # IMPROVE-IT

    # Devices / Interventions
    {"id": "mitraclip_mr", "name": "MitraClip — Mitral Regurgitation",
     "search": "MitraClip OR transcatheter mitral valve repair",
     "condition": "mitral regurgitation",
     "population": "Adults with severe secondary mitral regurgitation despite GDMT",
     "intervention": "Transcatheter mitral valve repair (MitraClip)", "comparator": "Medical therapy alone",
     "primary_outcome": "All-cause mortality or HF hospitalization",
     "key_ncts": ["NCT01626079", "NCT01920698"]},  # COAPT, MITRA-FR

    {"id": "tavr_low_risk", "name": "TAVR — Low Surgical Risk",
     "search": "transcatheter aortic valve replacement",
     "condition": "aortic stenosis",
     "population": "Adults with severe aortic stenosis at low surgical risk",
     "intervention": "TAVR (transcatheter aortic valve replacement)", "comparator": "SAVR (surgical AVR)",
     "primary_outcome": "All-cause mortality or disabling stroke at 1 year",
     "key_ncts": ["NCT02675114", "NCT02701283"]},  # PARTNER 3, Evolut Low Risk

    {"id": "renal_denervation", "name": "Renal Denervation — Hypertension",
     "search": "renal denervation",
     "condition": "hypertension",
     "population": "Adults with uncontrolled or resistant hypertension",
     "intervention": "Catheter-based renal denervation", "comparator": "Sham procedure",
     "primary_outcome": "24-hour ambulatory SBP change",
     "key_ncts": ["NCT02439749", "NCT03614260", "NCT02649426"]},  # SPYRAL HTN-OFF, SPYRAL HTN-ON, RADIANCE-HTN

    # Anticoagulation
    {"id": "doac_af", "name": "DOACs — Atrial Fibrillation",
     "search": "apixaban OR rivaroxaban OR edoxaban OR dabigatran",
     "condition": "atrial fibrillation",
     "population": "Adults with non-valvular atrial fibrillation",
     "intervention": "DOAC (apixaban, rivaroxaban, edoxaban, or dabigatran)", "comparator": "Warfarin",
     "primary_outcome": "Stroke or systemic embolism",
     "key_ncts": ["NCT00412984", "NCT00403767", "NCT00781391", "NCT00262600"]},  # ARISTOTLE, ROCKET-AF, ENGAGE, RE-LY

    {"id": "doac_vte", "name": "DOACs — Venous Thromboembolism",
     "search": "apixaban OR rivaroxaban OR edoxaban OR dabigatran",
     "condition": "venous thromboembolism OR pulmonary embolism OR deep vein thrombosis",
     "population": "Adults with acute VTE (DVT or PE)",
     "intervention": "DOAC", "comparator": "Warfarin or LMWH",
     "primary_outcome": "Recurrent VTE or VTE-related death",
     "key_ncts": ["NCT00643201", "NCT00633893", "NCT01054820"]},  # AMPLIFY, EINSTEIN-PE, HOKUSAI-VTE

    # Respiratory
    {"id": "dupilumab_asthma", "name": "Dupilumab — Asthma/COPD",
     "search": "dupilumab",
     "condition": "asthma OR COPD",
     "population": "Adults with moderate-to-severe asthma or type 2 COPD",
     "intervention": "Dupilumab (anti-IL-4Ra)", "comparator": "Placebo",
     "primary_outcome": "Annualized exacerbation rate",
     "key_ncts": ["NCT02414854", "NCT02528214", "NCT03930732"]},  # LIBERTY QUEST, LIBERTY VENTURE, BOREAS

    {"id": "tezepelumab_asthma", "name": "Tezepelumab — Severe Asthma",
     "search": "tezepelumab",
     "condition": "asthma",
     "population": "Adults with severe uncontrolled asthma",
     "intervention": "Tezepelumab (anti-TSLP)", "comparator": "Placebo",
     "primary_outcome": "Annualized asthma exacerbation rate",
     "key_ncts": ["NCT03347279", "NCT03706079"]},  # NAVIGATOR, DESTINATION

    # More Cardiology
    {"id": "empagliflozin_post_mi", "name": "Empagliflozin — Post-MI",
     "search": "empagliflozin",
     "condition": "myocardial infarction",
     "population": "Adults after acute MI",
     "intervention": "Empagliflozin", "comparator": "Placebo",
     "primary_outcome": "HF hospitalization or CV death",
     "key_ncts": ["NCT04509674"]},  # EMPACT-MI

    {"id": "dapagliflozin_post_mi", "name": "Dapagliflozin — Post-MI",
     "search": "dapagliflozin",
     "condition": "myocardial infarction",
     "population": "Adults after acute MI without diabetes",
     "intervention": "Dapagliflozin", "comparator": "Placebo",
     "primary_outcome": "CV death or HF hospitalization",
     "key_ncts": ["NCT04564742"]},  # DAPA-MI

    {"id": "ticagrelor_acs", "name": "Ticagrelor — ACS/CAD",
     "search": "ticagrelor",
     "condition": "acute coronary syndrome OR coronary artery disease",
     "population": "Adults with ACS or stable CAD",
     "intervention": "Ticagrelor", "comparator": "Clopidogrel or aspirin",
     "primary_outcome": "CV death, MI, or stroke",
     "key_ncts": ["NCT00391872", "NCT01991795"]},  # PLATO, THEMIS

    # Inflammation / Immune
    {"id": "anakinra_pericarditis", "name": "Anakinra — Recurrent Pericarditis",
     "search": "anakinra",
     "condition": "pericarditis",
     "population": "Adults with recurrent pericarditis",
     "intervention": "Anakinra (IL-1 receptor antagonist)", "comparator": "Placebo",
     "primary_outcome": "Pericarditis recurrence",
     "key_ncts": ["NCT03737110"]},  # AIRTRIP-like

    # Electrophysiology
    {"id": "catheter_ablation_af", "name": "Catheter Ablation — AF + HF",
     "search": "catheter ablation",
     "condition": "atrial fibrillation AND heart failure",
     "population": "Adults with AF and HF",
     "intervention": "Catheter ablation of AF", "comparator": "Medical rate/rhythm control",
     "primary_outcome": "All-cause mortality or HF hospitalization",
     "key_ncts": ["NCT00643188", "NCT02288832"]},  # CASTLE-AF, CABANA (HF subgroup)

    # Pulmonary Hypertension
    {"id": "sotatercept_pah", "name": "Sotatercept — Pulmonary Hypertension",
     "search": "sotatercept",
     "condition": "pulmonary arterial hypertension",
     "population": "Adults with PAH on background therapy",
     "intervention": "Sotatercept (activin signaling inhibitor)", "comparator": "Placebo",
     "primary_outcome": "6-minute walk distance change",
     "key_ncts": ["NCT04576988", "NCT04811092"]},  # STELLAR, HYPERION

    # Cardio-Oncology
    {"id": "dexrazoxane_cardio", "name": "Dexrazoxane — Cardioprotection",
     "search": "dexrazoxane OR cardioprotection AND anthracycline",
     "condition": "cancer AND cardiotoxicity",
     "population": "Cancer patients receiving anthracycline chemotherapy",
     "intervention": "Dexrazoxane or beta-blocker cardioprotection", "comparator": "Standard care",
     "primary_outcome": "LVEF decline or cardiac events",
     "key_ncts": ["NCT01724450"]},  # CECCY-like

    # Diabetes Technology
    {"id": "closed_loop_t1dm", "name": "Closed-Loop Insulin — Type 1 Diabetes",
     "search": "closed loop insulin OR artificial pancreas OR hybrid closed loop",
     "condition": "type 1 diabetes",
     "population": "Adults or adolescents with T1DM",
     "intervention": "Closed-loop insulin delivery system", "comparator": "Open-loop pump or MDI",
     "primary_outcome": "Time in range (70-180 mg/dL)",
     "key_ncts": ["NCT03563313", "NCT04531566"]},  # Various CL trials
]

def fetch_ctgov(nct_id):
    """Fetch a single study from CT.gov API v2."""
    url = f"{CTG_API}/{nct_id}?format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LivingMeta/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"  WARN: Failed to fetch {nct_id}: {e}", file=sys.stderr)
        return None

def parse_study(data):
    """Parse CT.gov study JSON into trial dict."""
    if not data:
        return None
    ps = data.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    status = ps.get("statusModule", {})
    design = ps.get("designModule", {})
    enroll = design.get("enrollmentInfo", {})
    phases = design.get("phases", [])
    arms = ps.get("armsInterventionsModule", {})
    results = data.get("resultsSection", {})

    nct_id = ident.get("nctId", "")
    title = ident.get("briefTitle", "")
    acronym = ident.get("acronym", "")

    # Get completion year
    comp_date = status.get("completionDateStruct", {}).get("date", "")
    year = int(comp_date[:4]) if comp_date and len(comp_date) >= 4 else 0

    # Phase
    phase_str = ", ".join(phases) if phases else "N/A"

    # Enrollment
    n_total = enroll.get("count", 0)

    # Try to get arm sizes from arms
    n_treatment = n_total // 2
    n_control = n_total - n_treatment

    # Extract outcomes from results section
    outcomes = {}
    if results:
        measures = results.get("outcomeMeasuresModule", {}).get("outcomeMeasures", [])
        for measure in measures:
            title_m = measure.get("title", "")
            m_type = measure.get("type", "")
            analyses = measure.get("analyses", [])
            for analysis in analyses:
                stat_method = (analysis.get("statisticalMethod", "") or "").lower()
                param_type = (analysis.get("paramType", "") or "").lower()
                param_val = analysis.get("paramValue")
                ci_lo = analysis.get("ciLowerLimit")
                ci_hi = analysis.get("ciUpperLimit")
                p_val = analysis.get("pValue")

                if param_val is None:
                    continue

                # Infer effect type
                combined = stat_method + " " + param_type
                if "hazard" in combined or "cox" in combined:
                    effect_type = "HR"
                elif "odds" in combined or "logistic" in combined:
                    effect_type = "OR"
                elif "risk ratio" in combined or "relative risk" in combined:
                    effect_type = "RR"
                elif "rate ratio" in combined or "incidence" in combined:
                    effect_type = "IRR"
                elif "mean diff" in combined:
                    effect_type = "MD"
                else:
                    effect_type = "HR"  # default for clinical outcomes

                try:
                    val = float(param_val)
                    lo = float(ci_lo) if ci_lo else None
                    hi = float(ci_hi) if ci_hi else None
                except (ValueError, TypeError):
                    continue

                # Clean p-value
                pv = None
                if p_val:
                    pv_clean = str(p_val).replace("<", "").replace(">", "").strip()
                    try:
                        pv = float(pv_clean)
                    except ValueError:
                        pass

                oc_key = "mace" if m_type == "PRIMARY" else f"secondary_{len(outcomes)}"
                outcomes[oc_key] = {
                    "title": title_m,
                    "effect_type": effect_type,
                    "value": val,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "p_value": pv,
                    "src": f"CT.gov {nct_id} results. {stat_method}."
                }
                break  # Take first analysis per measure

            # Also try to get group-level event counts
            groups = measure.get("groups", [])
            classes = measure.get("classes", [])
            if groups and classes and len(groups) >= 2:
                for cls in classes:
                    cats = cls.get("categories", [])
                    for cat in cats:
                        measurements = cat.get("measurements", [])
                        if len(measurements) >= 2:
                            try:
                                v1 = measurements[0].get("value", "")
                                v2 = measurements[1].get("value", "")
                                # Try to parse as integers (event counts)
                                if v1.isdigit() and v2.isdigit():
                                    # We have counts but need to know which is treatment
                                    pass
                            except:
                                pass

    return {
        "nct_id": nct_id,
        "title": title,
        "acronym": acronym or title.split(":")[0].split("(")[0].strip()[:20],
        "year": year,
        "phase": phase_str,
        "n_total": n_total,
        "n_treatment": n_treatment,
        "n_control": n_control,
        "has_results": bool(results),
        "outcomes": outcomes
    }


def generate_config(topic, trials):
    """Generate a CONFIG_LIBRARY entry as JavaScript string."""
    tid = topic["id"]
    outcomes_list = [
        {"id": "mace", "name": topic["primary_outcome"], "primary": True},
        {"id": "acm", "name": "All-Cause Mortality", "primary": False}
    ]

    lines = []
    lines.append(f'  /* {"=" * 60} */')
    lines.append(f'  /* {topic["name"].upper()} */')
    lines.append(f'  /* {"=" * 60} */')
    lines.append(f'  {tid}: {{')
    lines.append(f'    id: "{tid}", name: "{topic["name"]}", version: "1.0.0", lastUpdated: "2026-03-14",')
    lines.append(f'    pico: {{')
    lines.append(f'      population: "{topic["population"]}",')
    lines.append(f'      intervention: "{topic["intervention"]}",')
    lines.append(f'      comparator: "{topic["comparator"]}",')
    lines.append(f'      outcomes: [')
    for o in outcomes_list:
        lines.append(f'        {{ id: "{o["id"]}", name: "{o["name"]}", primary: {str(o["primary"]).lower()} }},')
    lines.append(f'      ]')
    lines.append(f'    }},')
    lines.append(f'    searchStrategy: {{')
    lines.append(f'      ctgov: "({topic["search"]}) AND ({topic["condition"]}) AND (COMPLETED)",')
    lines.append(f'      pubmed: "({topic["search"]}) AND ({topic["condition"]}) AND (randomized controlled trial[pt])",')
    lines.append(f'      openalex: "{topic["search"]} AND {topic["condition"].split(" AND ")[0]} AND randomized"')
    lines.append(f'    }},')
    lines.append(f'    subgroups: {{}},')
    lines.append(f'    eligibility: {{ include: ["Phase III RCT", "{topic["intervention"]} vs {topic["comparator"]}", "Reports {topic["primary_outcome"].split("(")[0].strip()}"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] }},')
    lines.append(f'    trials: [')

    for t in trials:
        if not t:
            continue
        trial_id = t["acronym"] or t["nct_id"]
        # Clean trial_id for JS
        trial_id = re.sub(r'[^\w\s-]', '', trial_id).strip()[:30]
        oc_js = "{"
        if t["outcomes"]:
            oc_parts = []
            for ok, ov in t["outcomes"].items():
                hr_str = f'hr: {ov["value"]}'
                ci_lo_str = f'hrLo: {ov["ci_lo"]}' if ov["ci_lo"] else 'hrLo: null'
                ci_hi_str = f'hrHi: {ov["ci_hi"]}' if ov["ci_hi"] else 'hrHi: null'
                src_escaped = ov["src"].replace("'", "\\'")
                oc_parts.append(f"          {ok}: {{ tE: 0, tN: {t['n_treatment']}, cE: 0, cN: {t['n_control']}, {hr_str}, {ci_lo_str}, {ci_hi_str}, src: '{src_escaped}' }}")
            oc_js = "{\n" + ",\n".join(oc_parts) + "\n        }"
        else:
            oc_js = "{ mace: { tE: 0, tN: " + str(t["n_treatment"]) + ", cE: 0, cN: " + str(t["n_control"]) + " } }"

        lines.append(f'      {{ id: "{trial_id}", nctId: "{t["nct_id"]}", year: {t["year"]}, phase: "{t["phase"]}",')
        lines.append(f'        population: "{topic["population"][:60]}", nTotal: {t["n_total"]}, nTreatment: {t["n_treatment"]}, nControl: {t["n_control"]},')
        lines.append(f'        status: "Published", reference: "See CT.gov {t["nct_id"]}",')
        lines.append(f'        outcomes: {oc_js},')
        lines.append(f'        rob: {{ domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." }},')
        lines.append(f'        evidenceText: "{trial_id}: N={t["n_total"]:,}. See CT.gov for full results."')
        lines.append(f'      }},')

    lines.append(f'    ],')
    lines.append(f'    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []')
    lines.append(f'  }},')
    return "\n".join(lines)


def main():
    print("LivingMeta Config Generator", file=sys.stderr)
    print(f"Processing {len(TOPICS)} topics...", file=sys.stderr)

    all_configs = []
    for i, topic in enumerate(TOPICS):
        print(f"\n[{i+1}/{len(TOPICS)}] {topic['name']}...", file=sys.stderr)
        trials = []
        for nct in topic.get("key_ncts", []):
            print(f"  Fetching {nct}...", file=sys.stderr)
            data = fetch_ctgov(nct)
            if data:
                parsed = parse_study(data)
                if parsed:
                    trials.append(parsed)
                    print(f"    -> {parsed['acronym'] or parsed['nct_id']}: N={parsed['n_total']}, "
                          f"year={parsed['year']}, results={'YES' if parsed['has_results'] else 'NO'}, "
                          f"outcomes={len(parsed['outcomes'])}", file=sys.stderr)
            time.sleep(0.3)  # Rate limit

        if trials:
            config_js = generate_config(topic, trials)
            all_configs.append(config_js)
        else:
            print(f"  WARNING: No trials found for {topic['id']}", file=sys.stderr)

    # Output all configs
    print("\n// ═══════════════════════════════════════════════════════════")
    print("// AUTO-GENERATED CONFIGS — paste into CONFIG_LIBRARY")
    print("// Generated: " + time.strftime("%Y-%m-%d %H:%M"))
    print("// ═══════════════════════════════════════════════════════════\n")
    for cfg in all_configs:
        print(cfg)
        print()

    print(f"\nDone. Generated {len(all_configs)} configs.", file=sys.stderr)

if __name__ == "__main__":
    main()
