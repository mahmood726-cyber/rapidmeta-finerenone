export const meta = {
  name: 'ctgov-reextract-2x2',
  description: 'Semantically re-extract verified 2x2 counts for nulled trials from cached ctgov records',
  phases: [
    { title: 'Extract', detail: 'one agent per trial: pick efficacy outcome + arms, compute 2x2' },
    { title: 'Verify', detail: 'independent adversarial re-derivation of each proposal' },
  ],
}

const work = [{"nct": "NCT00534313", "drug": "Abatacept", "condition": "Psa"}, {"nct": "NCT03284957", "drug": "Abemaciclib", "condition": "Breast"}, {"nct": "NCT04527380", "drug": "Adalimumab", "condition": "Psa"}, {"nct": "NCT05108922", "drug": "Aducanumab", "condition": "Ad"}, {"nct": "NCT00701415", "drug": "Agalsidase", "condition": "Beta Fabry"}, {"nct": "NCT01576484", "drug": "Alirocumab", "condition": "Lipid"}, {"nct": "NCT00805740", "drug": "Anidulafungin", "condition": "Candida"}, {"nct": "NCT01304238", "drug": "Argatroban", "condition": "Hit"}, {"nct": "NCT03019406", "drug": "Avalglucosidase", "condition": ""}, {"nct": "NCT03105336", "drug": "Axicabtagene", "condition": "Lymphoma"}, {"nct": "NCT02677922", "drug": "Azacitidine", "condition": "Mds"}, {"nct": "NCT03570749", "drug": "Baricitinib", "condition": "Aa"}, {"nct": "NCT03828292", "drug": "Belantamab", "condition": "Myeloma"}, {"nct": "NCT00732940", "drug": "Belimumab", "condition": "Lupus"}, {"nct": "NCT01286272", "drug": "Bendamustine", "condition": "Lymphoma"}, {"nct": "NCT03766685", "drug": "Bimekizumab", "condition": "Psoriasis 2"}, {"nct": "NCT05228730", "drug": "Bnt162B2", "condition": "Vaccine"}, {"nct": "NCT01421667", "drug": "Brentuximab", "condition": "Ptcl"}, {"nct": "NCT03624036", "drug": "Brexucabtagene", "condition": "Lymphoma"}, {"nct": "NCT04533737", "drug": "Brez", "condition": "Psoriasis"}, {"nct": "NCT02706626", "drug": "Brigatinib", "condition": "Alk Nsclc"}, {"nct": "NCT02985957", "drug": "Cabazitaxel", "condition": "Prostate"}, {"nct": "NCT01658878", "drug": "Cabozantinib", "condition": "Hcc"}, {"nct": "NCT02335944", "drug": "Capmatinib", "condition": "Lung"}, {"nct": "NCT01945281", "drug": "Caspofungin", "condition": "Fungal"}, {"nct": "NCT02475733", "drug": "Ceftazidime", "condition": "Avibactam"}, {"nct": "NCT03217136", "drug": "Ceftolozane", "condition": "Infection"}, {"nct": "NCT03230838", "drug": "Ceftolozane", "condition": "Taz"}, {"nct": "NCT02943460", "drug": "Cilofexor", "condition": "Fxr Psc"}, {"nct": "NCT03196284", "drug": "Concizumab", "condition": "Hema"}, {"nct": "NCT02349048", "drug": "Daclatasvir", "condition": "Hcv"}, {"nct": "NCT02262728", "drug": "Daclatasvir", "condition": "Hcv"}, {"nct": "NCT01858389", "drug": "Dacomitinib", "condition": "Lung"}, {"nct": "NCT03660683", "drug": "Dapagliflozin", "condition": "T2D Cv"}, {"nct": "NCT03446612", "drug": "Daprodustat", "condition": "Anaemia"}, {"nct": "NCT01782495", "drug": "Dasabuvir", "condition": "Chronic Hepatitis"}, {"nct": "NCT02486406", "drug": "Dasabuvir", "condition": "Chronic Hepatitis"}, {"nct": "NCT02487199", "drug": "Dasabuvir", "condition": "Hepatitis C"}, {"nct": "NCT03794349", "drug": "Dinutuximab", "condition": "Neuroblastoma"}, {"nct": "NCT05139810", "drug": "Donidalorsen", "condition": "Hae"}, {"nct": "NCT02652260", "drug": "Doravirine", "condition": "Hiv"}, {"nct": "NCT01396239", "drug": "Duchenne", "condition": "Gene Therapy"}, {"nct": "NCT03633617", "drug": "Dupilumab", "condition": "Eoe"}, {"nct": "NCT03534323", "drug": "Duvelisib", "condition": "Leukemia"}, {"nct": "NCT02925494", "drug": "Elagolix", "condition": "Fibroids"}, {"nct": "NCT00943111", "drug": "Eliglustat", "condition": "Gaucher"}, {"nct": "NCT01241292", "drug": "Elotuzumab", "condition": "Myeloma"}, {"nct": "NCT03269136", "drug": "Elranatamab", "condition": "Mm"}, {"nct": "NCT03473743", "drug": "Erdafitinib", "condition": "Bladder"}, {"nct": "NCT00957047", "drug": "Eslicarbazepine", "condition": "Epilepsy"}, {"nct": "NCT02451696", "drug": "Everolimus", "condition": "Tuberous"}, {"nct": "NCT00790400", "drug": "Everolimus", "condition": "Tuberous"}, {"nct": "NCT02975349", "drug": "Evobrutinib", "condition": "Ms"}, {"nct": "NCT01857583", "drug": "Fondaparinux", "condition": ""}, {"nct": "NCT02052778", "drug": "Futibatinib", "condition": "Btc"}, {"nct": "NCT02476890", "drug": "Gefapixant", "condition": "Cough"}, {"nct": "NCT03390296", "drug": "Gemtuzumab", "condition": "Leukemia"}, {"nct": "NCT01716156", "drug": "Grazoprevir", "condition": "Hepatitis C"}, {"nct": "NCT02332707", "drug": "Grazoprevir", "condition": "Hepatitis C"}, {"nct": "NCT01506141", "drug": "Idursulfase", "condition": "Mps2"}, {"nct": "NCT00920647", "drug": "Idursulfase", "condition": "Mps2"}, {"nct": "NCT01838200", "drug": "Ipilimumab", "condition": "Melanoma"}, {"nct": "NCT01646177", "drug": "Ixekizumab", "condition": "Psoriasis"}, {"nct": "NCT04070326", "drug": "Lanadelumab", "condition": "Hae"}, {"nct": "NCT00741338", "drug": "Laronidase", "condition": "Mps1"}, {"nct": "NCT00384774", "drug": "Lasmiditan", "condition": "Acute"}, {"nct": "NCT02605304", "drug": "Ledipasvir", "condition": "Hcv"}, {"nct": "NCT02421211", "drug": "Ledipasvir", "condition": "Hcv"}, {"nct": "NCT04811040", "drug": "Lenacapavir", "condition": "Hiv"}, {"nct": "NCT03739866", "drug": "Lenacapavir", "condition": "Hiv"}, {"nct": "NCT02432274", "drug": "Lenvatinib", "condition": "Dtc"}, {"nct": "NCT03442764", "drug": "Mavacamten", "condition": "Ohcm"}, {"nct": "NCT01897714", "drug": "Melphalan", "condition": "Flufenamide"}, {"nct": "NCT04649060", "drug": "Melphalan", "condition": "Flufenamide"}, {"nct": "NCT01970371", "drug": "Meropenem", "condition": ""}, {"nct": "NCT01093573", "drug": "Midostaurin", "condition": "Aml"}, {"nct": "NCT03807778", "drug": "Mobocertinib", "condition": "Egfr"}, {"nct": "NCT03094052", "drug": "Neratinib", "condition": "Breast"}, {"nct": "NCT03439891", "drug": "Nivolumab", "condition": "Hcc"}, {"nct": "NCT03186677", "drug": "Nonacog", "condition": "Beta Hemb"}, {"nct": "NCT01024010", "drug": "Ofatumumab", "condition": "Cll"}, {"nct": "NCT00512070", "drug": "Olanzapine", "condition": "Bipolar"}, {"nct": "NCT01116648", "drug": "Olaparib", "condition": "Ovarian2"}, {"nct": "NCT02719574", "drug": "Olutasidenib", "condition": "Aml"}, {"nct": "NCT00949078", "drug": "Omalizumab", "condition": "Food Allergy"}, {"nct": "NCT03381729", "drug": "Onasemnogene", "condition": "Sma"}, {"nct": "NCT03907397", "drug": "Palforzia", "condition": "Peanut"}, {"nct": "NCT04009291", "drug": "Palopegteriparatide", "condition": "Hpp"}, {"nct": "NCT03848065", "drug": "Pcv13", "condition": "Vaccine"}, {"nct": "NCT02588833", "drug": "Pegcetacoplan", "condition": "Pnh"}, {"nct": "NCT02475213", "drug": "Pembrolizumab", "condition": "Bladder"}, {"nct": "NCT02393248", "drug": "Pemigatinib", "condition": "Btc"}, {"nct": "NCT03219216", "drug": "Pibrentasvir", "condition": "Hepatitis C"}, {"nct": "NCT03067129", "drug": "Pibrentasvir", "condition": "Hepatitis C"}, {"nct": "NCT02966795", "drug": "Pibrentasvir", "condition": "Hepatitis C"}, {"nct": "NCT01096849", "drug": "Plazomicin", "condition": "Infection"}, {"nct": "NCT02382939", "drug": "Prader", "condition": "Human Gh"}, {"nct": "NCT02037984", "drug": "Prevnar15", "condition": "Pneumo"}, {"nct": "NCT00787891", "drug": "Rabeprazole", "condition": "Gerd"}, {"nct": "NCT02956746", "drug": "Rabies", "condition": "Vaccine"}, {"nct": "NCT04558918", "drug": "Ravulizumab", "condition": "Pnh"}, {"nct": "NCT00814671", "drug": "Rifapentine", "condition": "Tb"}, {"nct": "NCT04124965", "drug": "Rozanolixizumab", "condition": "Mg"}, {"nct": "NCT04650854", "drug": "Rozanolixizumab", "condition": "Mg"}, {"nct": "NCT03840200", "drug": "Rucaparib", "condition": "Ovarian"}, {"nct": "NCT04530344", "drug": "Ruxolitinib", "condition": "Vitiligo"}, {"nct": "NCT01307098", "drug": "Sebelipase", "condition": "Lal"}, {"nct": "NCT01636687", "drug": "Secukinumab", "condition": "Psoriasis"}, {"nct": "NCT02609048", "drug": "Seladelpar", "condition": "Pbc"}, {"nct": "NCT02970942", "drug": "Semaglutide", "condition": "Nash"}, {"nct": "NCT03987074", "drug": "Semaglutide", "condition": "Nash"}, {"nct": "NCT00159874", "drug": "Sildenafil", "condition": "Pah"}, {"nct": "NCT01689532", "drug": "Sirukumab", "condition": "Arthritis Rheumatoid"}, {"nct": "NCT02024087", "drug": "Sorafenib", "condition": "Hcc"}, {"nct": "NCT00975806", "drug": "Sunitinib", "condition": "Rcc"}, {"nct": "NCT01391130", "drug": "Sunitinib", "condition": "Rcc"}, {"nct": "NCT01132690", "drug": "Taliglucerase", "condition": "Gaucher"}, {"nct": "NCT01411228", "drug": "Taliglucerase", "condition": "Gaucher"}, {"nct": "NCT04166773", "drug": "Tirzepatide", "condition": "Nash"}, {"nct": "NCT02706873", "drug": "Upadacitinib", "condition": "Ra"}, {"nct": "NCT02760264", "drug": "Vamorolone", "condition": "Dmd2"}, {"nct": "NCT03038399", "drug": "Vamorolone", "condition": "Dmd2"}, {"nct": "NCT00867139", "drug": "Zanamivir", "condition": "Flu"}, {"nct": "NCT03189524", "drug": "Zanubrutinib", "condition": "Lymphoma"}]

log(`re-extracting ${work.length} trials from cached ctgov records`)
const CACHE = 'F:/rapidmeta-finerenone/outputs/ctgov_cache'

const EXTRACT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['nct','usable','tE','tN','cE','cN','outcome','treatment_arm','control_arm','pct_derived','confidence','reasoning'],
  properties: {
    nct: { type: 'string' },
    usable: { type: 'boolean' },
    tE: { type: ['integer','null'] }, tN: { type: ['integer','null'] },
    cE: { type: ['integer','null'] }, cN: { type: ['integer','null'] },
    outcome: { type: 'string' }, treatment_arm: { type: 'string' }, control_arm: { type: 'string' },
    pct_derived: { type: 'boolean' }, confidence: { type: 'string', enum: ['high','medium','low'] },
    reasoning: { type: 'string' },
  },
}
const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['nct','confirmed','tE','tN','cE','cN','verdict'],
  properties: {
    nct: { type: 'string' }, confirmed: { type: 'boolean' },
    tE: { type: ['integer','null'] }, tN: { type: ['integer','null'] },
    cE: { type: ['integer','null'] }, cN: { type: ['integer','null'] },
    verdict: { type: 'string' },
  },
}

function extractPrompt(w) {
  return `You are extracting a 2x2 contingency table (treatment vs control event counts) from a ClinicalTrials.gov study record, for a binary-outcome meta-analysis.

Trial: ${w.nct} - drug "${w.drug}" for condition "${w.condition}".
Read this file (ctgov API v2 study JSON): ${CACHE}/${w.nct}.json

Steps:
1. In resultsSection.outcomeMeasuresModule.outcomeMeasures, choose the PRIMARY EFFICACY BINARY outcome - the clinically meaningful responder/event endpoint for ${w.drug} in ${w.condition} (e.g. response rate, remission, MACE, exacerbation, relapse, seizure-freedom). Do NOT use a pure adverse-event/death safety count unless mortality IS the efficacy endpoint. Skip continuous endpoints (mean change, percent-change in a lab value).
2. Pick exactly TWO arms: the active ${w.drug} arm (for dose-ranging trials, the approved/pivotal dose) and the control arm (placebo / standard of care / comparator). The chosen outcome must report data for both.
3. Per arm get N = analysed participants (the outcome denoms.counts; fall back to the arm baseline N) and events = participants with the outcome. If the outcome value is a PERCENTAGE, compute events = round(percentage/100 * N) and set pct_derived=true.
4. Return tE,tN (treatment) and cE,cN (control).

Hard rules:
- tE<=tN and cE<=cN and tN>0 and cN>0 must all hold.
- If the study is single-arm, has no posted binary efficacy outcome, or you cannot confidently identify the outcome AND both arms, set usable=false with null counts. Failing closed is correct - a wrong 2x2 is worse than none.
Return ONLY the structured object.`
}
function verifyPrompt(prop, w) {
  return `Adversarially verify a proposed 2x2 extraction from a ClinicalTrials.gov record. Assume it may be WRONG.

Trial: ${w.nct} (${w.drug} / ${w.condition}).
Independently read: ${CACHE}/${w.nct}.json
Proposal: usable=${prop.usable}, outcome="${prop.outcome}", treatment="${prop.treatment_arm}" tE=${prop.tE}/tN=${prop.tN}, control="${prop.control_arm}" cE=${prop.cE}/cN=${prop.cN}.

Re-derive the correct 2x2 yourself from the JSON, then judge:
- Is the chosen outcome the right PRIMARY EFFICACY BINARY endpoint (not safety/continuous)?
- Are treatment and control arms correct (not swapped; right dose; control really placebo/SoC)?
- Do tE/tN/cE/cN match the source (incl. correct percentage to count conversion)? Is tE<=tN, cE<=cN?

If fully correct: confirmed=true, echo counts, verdict="CONFIRM ...".
If right outcome/arms but wrong numbers: fix them, confirmed=true, verdict="CORRECTED ...".
If outcome/arms wrong, study single-arm, or no valid binary efficacy 2x2: confirmed=false, null counts, verdict="REJECT ...".`
}

const results = await pipeline(
  work,
  (w) => agent(extractPrompt(w), { label: `extract:${w.nct}`, phase: 'Extract', schema: EXTRACT_SCHEMA, agentType: 'Explore' }),
  (prop, w) => {
    if (!prop || !prop.usable) return { nct: w.nct, confirmed: false, tE: null, tN: null, cE: null, cN: null, verdict: 'REJECT extractor unusable' }
    return agent(verifyPrompt(prop, w), { label: `verify:${w.nct}`, phase: 'Verify', schema: VERIFY_SCHEMA, agentType: 'Explore' })
      .then((v) => ({ ...v, drug: w.drug, condition: w.condition, outcome: prop.outcome }))
  }
)
const confirmed = results.filter(Boolean).filter((r) => r.confirmed && r.tE != null && r.tN != null && r.cE != null && r.cN != null && r.tE <= r.tN && r.cE <= r.cN && r.tN > 0 && r.cN > 0)
log(`confirmed ${confirmed.length} of ${work.length} trials with verified 2x2`)
return { confirmed, total: work.length, rejected: work.length - confirmed.length }
