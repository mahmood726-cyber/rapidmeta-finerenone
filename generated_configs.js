
// ═══════════════════════════════════════════════════════════
// DEPRECATED — 2026-04-10
// These configs were for embedding into HTML apps as CONFIG_LIBRARY entries.
// They are SUPERSEDED by the 26 APPS definitions in generate_living_ma_v13.py,
// which is now the single source of truth for all living MA app generation.
// This file is retained for reference only. Do not use for new apps.
// Generated: 2026-03-14 21:13
// ═══════════════════════════════════════════════════════════

  /* ============================================================ */
  /* SGLT2I — CHRONIC KIDNEY DISEASE */
  /* ============================================================ */
  sglt2_ckd: {
    id: "sglt2_ckd", name: "SGLT2i — Chronic Kidney Disease", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with CKD (with or without diabetes)",
      intervention: "SGLT2 inhibitor (dapagliflozin, empagliflozin, canagliflozin)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "Kidney composite (eGFR decline, ESKD, renal death)", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(dapagliflozin OR empagliflozin OR canagliflozin) AND (chronic kidney disease) AND (COMPLETED)",
      pubmed: "(dapagliflozin OR empagliflozin OR canagliflozin) AND (chronic kidney disease) AND (randomized controlled trial[pt])",
      openalex: "dapagliflozin OR empagliflozin OR canagliflozin AND chronic kidney disease AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "SGLT2 inhibitor (dapagliflozin, empagliflozin, canagliflozin) vs Placebo", "Reports Kidney composite"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "Dapa-CKD", nctId: "NCT03036150", year: 2020, phase: "PHASE3",
        population: "Adults with CKD (with or without diabetes)", nTotal: 4304, nTreatment: 2152, nControl: 2152,
        status: "Published", reference: "See CT.gov NCT03036150",
        outcomes: {
          mace: { tE: 0, tN: 2152, cE: 0, cN: 2152, hr: 0.61, hrLo: 0.51, hrHi: 0.72, src: 'CT.gov NCT03036150 results. regression, cox.' },
          secondary_1: { tE: 0, tN: 2152, cE: 0, cN: 2152, hr: 0.56, hrLo: 0.45, hrHi: 0.68, src: 'CT.gov NCT03036150 results. regression, cox.' },
          secondary_2: { tE: 0, tN: 2152, cE: 0, cN: 2152, hr: 0.71, hrLo: 0.55, hrHi: 0.92, src: 'CT.gov NCT03036150 results. regression, cox.' },
          secondary_3: { tE: 0, tN: 2152, cE: 0, cN: 2152, hr: 0.69, hrLo: 0.53, hrHi: 0.88, src: 'CT.gov NCT03036150 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Dapa-CKD: N=4,304. See CT.gov for full results."
      },
      { id: "CREDENCE", nctId: "NCT02065791", year: 2018, phase: "PHASE3",
        population: "Adults with CKD (with or without diabetes)", nTotal: 4401, nTreatment: 2200, nControl: 2201,
        status: "Published", reference: "See CT.gov NCT02065791",
        outcomes: {
          mace: { tE: 0, tN: 2200, cE: 0, cN: 2201, hr: 0.7, hrLo: 0.59, hrHi: 0.82, src: 'CT.gov NCT02065791 results. cox proportional hazard.' },
          secondary_1: { tE: 0, tN: 2200, cE: 0, cN: 2201, hr: 0.69, hrLo: 0.57, hrHi: 0.83, src: 'CT.gov NCT02065791 results. cox proportional hazard.' },
          secondary_2: { tE: 0, tN: 2200, cE: 0, cN: 2201, hr: 0.8, hrLo: 0.67, hrHi: 0.95, src: 'CT.gov NCT02065791 results. cox proportional hazard.' },
          secondary_3: { tE: 0, tN: 2200, cE: 0, cN: 2201, hr: 0.61, hrLo: 0.47, hrHi: 0.8, src: 'CT.gov NCT02065791 results. cox proportional hazards.' },
          secondary_4: { tE: 0, tN: 2200, cE: 0, cN: 2201, hr: 0.66, hrLo: 0.53, hrHi: 0.81, src: 'CT.gov NCT02065791 results. cox proportional hazards.' },
          secondary_5: { tE: 0, tN: 2200, cE: 0, cN: 2201, hr: 0.78, hrLo: 0.61, hrHi: 1.0, src: 'CT.gov NCT02065791 results. cox proportional hazards.' },
          secondary_6: { tE: 0, tN: 2200, cE: 0, cN: 2201, hr: 0.83, hrLo: 0.68, hrHi: 1.02, src: 'CT.gov NCT02065791 results. cox proportional hazard.' },
          secondary_7: { tE: 0, tN: 2200, cE: 0, cN: 2201, hr: 0.74, hrLo: 0.63, hrHi: 0.86, src: 'CT.gov NCT02065791 results. cox proportional hazards.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "CREDENCE: N=4,401. See CT.gov for full results."
      },
      { id: "EMPA-KIDNEY", nctId: "NCT03594110", year: 2024, phase: "PHASE3",
        population: "Adults with CKD (with or without diabetes)", nTotal: 6609, nTreatment: 3304, nControl: 3305,
        status: "Published", reference: "See CT.gov NCT03594110",
        outcomes: {
          mace: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.79, hrLo: 0.72, hrHi: 0.87, src: 'CT.gov NCT03594110 results. .' },
          secondary_1: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.84, hrLo: 0.63, hrHi: 1.12, src: 'CT.gov NCT03594110 results. regression, cox.' },
          secondary_2: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.86, hrLo: 0.76, hrHi: 0.98, src: 'CT.gov NCT03594110 results. joint frailty model.' },
          secondary_3: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.87, hrLo: 0.68, hrHi: 1.11, src: 'CT.gov NCT03594110 results. regression, cox.' },
          secondary_4: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.71, hrLo: 0.62, hrHi: 0.81, src: 'CT.gov NCT03594110 results. regression, cox.' },
          secondary_5: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.83, hrLo: 0.59, hrHi: 1.17, src: 'CT.gov NCT03594110 results. regression, cox.' },
          secondary_6: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.72, hrLo: 0.59, hrHi: 0.89, src: 'CT.gov NCT03594110 results. regression, cox.' },
          secondary_7: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.79, hrLo: 0.72, hrHi: 0.87, src: 'CT.gov NCT03594110 results. .' },
          secondary_8: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.81, hrLo: 0.72, hrHi: 0.9, src: 'CT.gov NCT03594110 results. .' },
          secondary_9: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: 0.74, hrLo: 0.64, hrHi: 0.87, src: 'CT.gov NCT03594110 results. .' },
          secondary_10: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: -0.24, hrLo: -0.38, hrHi: -0.11, src: 'CT.gov NCT03594110 results. mixed models analysis.' },
          secondary_11: { tE: 0, tN: 3304, cE: 0, cN: 3305, hr: -12.0, hrLo: -42.0, hrHi: 17.0, src: 'CT.gov NCT03594110 results. regression, linear.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "EMPA-KIDNEY: N=6,609. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* SGLT2I — T2DM CVOTS */
  /* ============================================================ */
  sglt2_t2dm_cvot: {
    id: "sglt2_t2dm_cvot", name: "SGLT2i — T2DM CVOTs", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with T2DM at high CV risk",
      intervention: "SGLT2 inhibitor",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "3-point MACE (CV death, MI, stroke)", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(empagliflozin OR canagliflozin OR dapagliflozin OR ertugliflozin) AND (type 2 diabetes AND cardiovascular) AND (COMPLETED)",
      pubmed: "(empagliflozin OR canagliflozin OR dapagliflozin OR ertugliflozin) AND (type 2 diabetes AND cardiovascular) AND (randomized controlled trial[pt])",
      openalex: "empagliflozin OR canagliflozin OR dapagliflozin OR ertugliflozin AND type 2 diabetes AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "SGLT2 inhibitor vs Placebo", "Reports 3-point MACE"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "BI 10773", nctId: "NCT01131676", year: 2015, phase: "PHASE3",
        population: "Adults with T2DM at high CV risk", nTotal: 7064, nTreatment: 3532, nControl: 3532,
        status: "Published", reference: "See CT.gov NCT01131676",
        outcomes: {
          mace: { tE: 0, tN: 3532, cE: 0, cN: 3532, hr: 0.86, hrLo: 0.74, hrHi: 0.99, src: 'CT.gov NCT01131676 results. cox proportional hazards model.' },
          secondary_1: { tE: 0, tN: 3532, cE: 0, cN: 3532, hr: 0.89, hrLo: 0.78, hrHi: 1.01, src: 'CT.gov NCT01131676 results. cox proportional hazards model.' },
          secondary_2: { tE: 0, tN: 3532, cE: 0, cN: 3532, hr: 1.28, hrLo: 0.7, hrHi: 2.33, src: 'CT.gov NCT01131676 results. cox proportional hazards model.' },
          secondary_3: { tE: 0, tN: 3532, cE: 0, cN: 3532, hr: 0.65, hrLo: 0.5, hrHi: 0.85, src: 'CT.gov NCT01131676 results. cox proportional hazards model.' },
          secondary_4: { tE: 0, tN: 3532, cE: 0, cN: 3532, hr: 0.95, hrLo: 0.87, hrHi: 1.04, src: 'CT.gov NCT01131676 results. cox proportional hazards model.' },
          secondary_5: { tE: 0, tN: 3532, cE: 0, cN: 3532, hr: 0.62, hrLo: 0.54, hrHi: 0.72, src: 'CT.gov NCT01131676 results. cox proportional hazards model.' },
          secondary_6: { tE: 0, tN: 3532, cE: 0, cN: 3532, hr: 0.62, hrLo: 0.54, hrHi: 0.7, src: 'CT.gov NCT01131676 results. cox proportional hazards model.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "BI 10773: N=7,064. See CT.gov for full results."
      },
      { id: "CANVAS", nctId: "NCT01032629", year: 2017, phase: "PHASE3",
        population: "Adults with T2DM at high CV risk", nTotal: 4330, nTreatment: 2165, nControl: 2165,
        status: "Published", reference: "See CT.gov NCT01032629",
        outcomes: {
          mace: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: 0.93, hrLo: 0.78, hrHi: 1.12, src: 'CT.gov NCT01032629 results. cox proportional hazard model.' },
          secondary_1: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: 2.79, hrLo: -1.571, hrHi: 7.154, src: 'CT.gov NCT01032629 results. ancova.' },
          secondary_2: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: 0.8, hrLo: 0.67, hrHi: 0.97, src: 'CT.gov NCT01032629 results. regression, logistic.' },
          secondary_3: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: -0.03, hrLo: -0.429, hrHi: 0.374, src: 'CT.gov NCT01032629 results. .' },
          secondary_4: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: 0.87, hrLo: 0.8, hrHi: 0.94, src: 'CT.gov NCT01032629 results. .' },
          secondary_5: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: 1.68, hrLo: 0.599, hrHi: 2.755, src: 'CT.gov NCT01032629 results. .' },
          secondary_6: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: -0.27, hrLo: -0.355, hrHi: -0.177, src: 'CT.gov NCT01032629 results. .' },
          secondary_7: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: -0.58, hrLo: -0.794, hrHi: -0.374, src: 'CT.gov NCT01032629 results. .' },
          secondary_8: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: -2.96, hrLo: -3.472, hrHi: -2.454, src: 'CT.gov NCT01032629 results. .' },
          secondary_9: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: -2.96, hrLo: -3.998, hrHi: -1.914, src: 'CT.gov NCT01032629 results. .' },
          secondary_10: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: 0.02, hrLo: -0.04, hrHi: 0.07, src: 'CT.gov NCT01032629 results. .' },
          secondary_11: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: 0.18, hrLo: 0.105, hrHi: 0.259, src: 'CT.gov NCT01032629 results. .' },
          secondary_12: { tE: 0, tN: 2165, cE: 0, cN: 2165, hr: 0.02, hrLo: -0.04, hrHi: 0.076, src: 'CT.gov NCT01032629 results. .' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "CANVAS: N=4,330. See CT.gov for full results."
      },
      { id: "DECLARE-TIMI58", nctId: "NCT01730534", year: 2018, phase: "PHASE3",
        population: "Adults with T2DM at high CV risk", nTotal: 17190, nTreatment: 8595, nControl: 8595,
        status: "Published", reference: "See CT.gov NCT01730534",
        outcomes: {
          mace: { tE: 0, tN: 8595, cE: 0, cN: 8595, hr: 0.83, hrLo: 0.73, hrHi: 0.95, src: 'CT.gov NCT01730534 results. regression, cox.' },
          secondary_1: { tE: 0, tN: 8595, cE: 0, cN: 8595, hr: 0.76, hrLo: 0.67, hrHi: 0.87, src: 'CT.gov NCT01730534 results. regression, cox.' },
          secondary_2: { tE: 0, tN: 8595, cE: 0, cN: 8595, hr: 0.93, hrLo: 0.82, hrHi: 1.04, src: 'CT.gov NCT01730534 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "DECLARE-TIMI58: N=17,190. See CT.gov for full results."
      },
      { id: "Cardiovascular Outco", nctId: "NCT01986881", year: 2019, phase: "PHASE3",
        population: "Adults with T2DM at high CV risk", nTotal: 8246, nTreatment: 4123, nControl: 4123,
        status: "Published", reference: "See CT.gov NCT01986881",
        outcomes: {
          mace: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.75, hrLo: -0.98, hrHi: -0.53, src: 'CT.gov NCT01986881 results. clda model.' },
          secondary_1: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.88, hrLo: 0.75, hrHi: 1.034, src: 'CT.gov NCT01986881 results. cox proportional hazards model.' },
          secondary_2: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.92, hrLo: 0.767, hrHi: 1.113, src: 'CT.gov NCT01986881 results. cox proportional hazards model.' },
          secondary_3: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.81, hrLo: 0.63, hrHi: 1.036, src: 'CT.gov NCT01986881 results. cox proportional hazards model.' },
          secondary_4: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.92, hrLo: 0.823, hrHi: 1.038, src: 'CT.gov NCT01986881 results. cox proportional hazards model.' },
          secondary_5: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 1.04, hrLo: 0.861, hrHi: 1.259, src: 'CT.gov NCT01986881 results. cox proportional hazards model.' },
          secondary_6: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 1.06, hrLo: 0.82, hrHi: 1.365, src: 'CT.gov NCT01986881 results. cox proportional hazards model.' },
          secondary_7: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.7, hrLo: 0.539, hrHi: 0.902, src: 'CT.gov NCT01986881 results. cox proportional hazards model.' },
          secondary_8: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.93, hrLo: 0.797, hrHi: 1.081, src: 'CT.gov NCT01986881 results. cox proportional hazards model.' },
          secondary_9: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 1.01, hrLo: 0.898, hrHi: 1.131, src: 'CT.gov NCT01986881 results. .' },
          secondary_10: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.82, hrLo: 0.716, hrHi: 0.945, src: 'CT.gov NCT01986881 results. .' },
          secondary_11: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.5, hrLo: -0.55, hrHi: -0.46, src: 'CT.gov NCT01986881 results. clda model.' },
          secondary_12: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.48, hrLo: -0.54, hrHi: -0.43, src: 'CT.gov NCT01986881 results. constrained longitudinal data analysis.' },
          secondary_13: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.37, hrLo: -0.45, hrHi: -0.3, src: 'CT.gov NCT01986881 results. constrained longitudinal data analysis.' },
          secondary_14: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.31, hrLo: -0.41, hrHi: -0.21, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_15: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -17.56, hrLo: -19.49, hrHi: -15.63, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_16: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -2.78, hrLo: -3.45, hrHi: -2.1, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_17: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -3.15, hrLo: -3.85, hrHi: -2.45, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_18: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -2.72, hrLo: -3.57, hrHi: -1.86, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_19: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -2.6, hrLo: -3.68, hrHi: -1.52, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_20: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.96, hrLo: -1.37, hrHi: -0.56, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_21: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.81, hrLo: -1.22, hrHi: -0.39, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_22: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.67, hrLo: -1.19, hrHi: -0.16, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_23: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.78, hrLo: -1.46, hrHi: -0.1, src: 'CT.gov NCT01986881 results. constrained longitudinal data analysis.' },
          secondary_24: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -1.92, hrLo: -2.07, hrHi: -1.77, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_25: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -2.45, hrLo: -2.67, hrHi: -2.24, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_26: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -2.53, hrLo: -2.83, hrHi: -2.22, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_27: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -2.53, hrLo: -2.97, hrHi: -2.1, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_28: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -1.78, hrLo: -2.41, hrHi: -1.15, src: 'CT.gov NCT01986881 results. .' },
          secondary_29: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.88, hrLo: -1.58, hrHi: -0.18, src: 'CT.gov NCT01986881 results. .' },
          secondary_30: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.25, hrLo: -0.59, hrHi: 1.08, src: 'CT.gov NCT01986881 results. .' },
          secondary_31: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 1.48, hrLo: 0.31, hrHi: 2.66, src: 'CT.gov NCT01986881 results. .' },
          secondary_32: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.9, hrLo: -2.8, hrHi: 0.9, src: 'CT.gov NCT01986881 results. .' },
          secondary_33: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 1.3, hrLo: -5.8, hrHi: 8.4, src: 'CT.gov NCT01986881 results. .' },
          secondary_34: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 1.4, hrLo: -17.7, hrHi: 20.4, src: 'CT.gov NCT01986881 results. .' },
          secondary_35: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 7.9, hrLo: -5.1, hrHi: 20.5, src: 'CT.gov NCT01986881 results. .' },
          secondary_36: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 0.0, hrLo: -2.9, hrHi: 3.0, src: 'CT.gov NCT01986881 results. .' },
          secondary_37: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -25.4, hrLo: -32.84, hrHi: -17.96, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_38: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -1.88, hrLo: -2.37, hrHi: -1.13, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_39: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 2.49, hrLo: 1.61, hrHi: 3.83, src: 'CT.gov NCT01986881 results. regression, logistic.' },
          secondary_40: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -2.32, hrLo: -4.35, hrHi: -0.3, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_41: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.38, hrLo: -1.56, hrHi: 0.81, src: 'CT.gov NCT01986881 results. clda model.' },
          secondary_42: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -12.22, hrLo: -27.03, hrHi: 2.06, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_43: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.52, hrLo: -1.79, hrHi: 0.75, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_44: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 1.48, hrLo: 0.52, hrHi: 4.17, src: 'CT.gov NCT01986881 results. regression, logistic.' },
          secondary_45: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 2.73, hrLo: -2.0, hrHi: 7.45, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_46: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 1.98, hrLo: -0.91, hrHi: 4.86, src: 'CT.gov NCT01986881 results. clda model.' },
          secondary_47: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -31.37, hrLo: -40.68, hrHi: -22.07, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_48: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -1.94, hrLo: -2.65, hrHi: -1.24, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_49: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: 4.1, hrLo: 2.0, hrHi: 8.42, src: 'CT.gov NCT01986881 results. regression, logistic.' },
          secondary_50: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.85, hrLo: -4.0, hrHi: 2.3, src: 'CT.gov NCT01986881 results. clda.' },
          secondary_51: { tE: 0, tN: 4123, cE: 0, cN: 4123, hr: -0.68, hrLo: -2.6, hrHi: 1.25, src: 'CT.gov NCT01986881 results. clda.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Cardiovascular Outco: N=8,246. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* SACUBITRIL/VALSARTAN — HEART FAILURE */
  /* ============================================================ */
  arni_hf: {
    id: "arni_hf", name: "Sacubitril/Valsartan — Heart Failure", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with heart failure (HFrEF or HFpEF)",
      intervention: "Sacubitril/valsartan (ARNI)",
      comparator: "Enalapril or valsartan",
      outcomes: [
        { id: "mace", name: "CV death or HF hospitalization", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(sacubitril OR entresto OR LCZ696) AND (heart failure) AND (COMPLETED)",
      pubmed: "(sacubitril OR entresto OR LCZ696) AND (heart failure) AND (randomized controlled trial[pt])",
      openalex: "sacubitril OR entresto OR LCZ696 AND heart failure AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Sacubitril/valsartan (ARNI) vs Enalapril or valsartan", "Reports CV death or HF hospitalization"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "PARADIGM-HF", nctId: "NCT01035255", year: 2014, phase: "PHASE3",
        population: "Adults with heart failure (HFrEF or HFpEF)", nTotal: 8442, nTreatment: 4221, nControl: 4221,
        status: "Published", reference: "See CT.gov NCT01035255",
        outcomes: { mace: { tE: 0, tN: 4221, cE: 0, cN: 4221 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "PARADIGM-HF: N=8,442. See CT.gov for full results."
      },
      { id: "PARAGON-HF", nctId: "NCT01920711", year: 2019, phase: "PHASE3",
        population: "Adults with heart failure (HFrEF or HFpEF)", nTotal: 4822, nTreatment: 2411, nControl: 2411,
        status: "Published", reference: "See CT.gov NCT01920711",
        outcomes: {
          mace: { tE: 0, tN: 2411, cE: 0, cN: 2411, hr: 0.8698, hrLo: 0.7526, hrHi: 1.0052, src: 'CT.gov NCT01920711 results. proportional rates model (lwyy).' },
          secondary_1: { tE: 0, tN: 2411, cE: 0, cN: 2411, hr: 1.0264, hrLo: -0.0047, hrHi: 2.0576, src: 'CT.gov NCT01920711 results. mixed models analysis.' },
          secondary_2: { tE: 0, tN: 2411, cE: 0, cN: 2411, hr: 1.4475, hrLo: 1.1294, hrHi: 1.8552, src: 'CT.gov NCT01920711 results. repeated measures cumulative odds model.' },
          secondary_3: { tE: 0, tN: 2411, cE: 0, cN: 2411, hr: 0.5041, hrLo: 0.3312, hrHi: 0.7673, src: 'CT.gov NCT01920711 results. cox\'s proportional hazards model.' },
          secondary_4: { tE: 0, tN: 2411, cE: 0, cN: 2411, hr: 0.9696, hrLo: 0.8352, hrHi: 1.1255, src: 'CT.gov NCT01920711 results. cox\'s proportional hazards model.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "PARAGON-HF: N=4,822. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* IV IRON — HEART FAILURE */
  /* ============================================================ */
  iron_hf: {
    id: "iron_hf", name: "IV Iron — Heart Failure", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with HF and iron deficiency",
      intervention: "IV iron (ferric carboxymaltose or iron isomaltoside)",
      comparator: "Placebo or standard care",
      outcomes: [
        { id: "mace", name: "CV death or HF hospitalization", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(ferric carboxymaltose OR iron isomaltoside OR iron sucrose) AND (heart failure AND iron deficiency) AND (COMPLETED)",
      pubmed: "(ferric carboxymaltose OR iron isomaltoside OR iron sucrose) AND (heart failure AND iron deficiency) AND (randomized controlled trial[pt])",
      openalex: "ferric carboxymaltose OR iron isomaltoside OR iron sucrose AND heart failure AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "IV iron (ferric carboxymaltose or iron isomaltoside) vs Placebo or standard care", "Reports CV death or HF hospitalization"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "Affirm-AHF", nctId: "NCT02937454", year: 2020, phase: "PHASE4",
        population: "Adults with HF and iron deficiency", nTotal: 1132, nTreatment: 566, nControl: 566,
        status: "Published", reference: "See CT.gov NCT02937454",
        outcomes: {
          mace: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.79, hrLo: 0.62, hrHi: 1.01, src: 'CT.gov NCT02937454 results. negative binomial model.' },
          secondary_1: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.8, hrLo: 0.64, hrHi: 1.0, src: 'CT.gov NCT02937454 results. negative binomial model.' },
          secondary_2: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.74, hrLo: 0.58, hrHi: 0.94, src: 'CT.gov NCT02937454 results. negative binomial model.' },
          secondary_3: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.96, hrLo: 0.7, hrHi: 1.32, src: 'CT.gov NCT02937454 results. regression, cox.' },
          secondary_4: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.8, hrLo: 0.66, hrHi: 0.98, src: 'CT.gov NCT02937454 results. regression, cox.' },
          secondary_5: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.67, hrLo: 0.47, hrHi: 0.97, src: 'CT.gov NCT02937454 results. negative binomial model.' },
          secondary_6: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.73, hrLo: 0.59, hrHi: 0.92, src: 'CT.gov NCT02937454 results. regression, cox.' },
          secondary_7: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.77, hrLo: 0.63, hrHi: 0.94, src: 'CT.gov NCT02937454 results. regression, cox.' },
          secondary_8: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 0.99, hrLo: 0.75, hrHi: 1.31, src: 'CT.gov NCT02937454 results. regression, cox.' },
          secondary_9: { tE: 0, tN: 566, cE: 0, cN: 566, hr: 1.14, hrLo: 0.93, hrHi: 1.39, src: 'CT.gov NCT02937454 results. generalised estimating equations (gee).' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Affirm-AHF: N=1,132. See CT.gov for full results."
      },
      { id: "IRONMAN", nctId: "NCT02642562", year: 2022, phase: "PHASE4",
        population: "Adults with HF and iron deficiency", nTotal: 1160, nTreatment: 580, nControl: 580,
        status: "Published", reference: "See CT.gov NCT02642562",
        outcomes: { mace: { tE: 0, tN: 580, cE: 0, cN: 580 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "IRONMAN: N=1,160. See CT.gov for full results."
      },
      { id: "HEART-FID", nctId: "NCT03037931", year: 2023, phase: "PHASE3",
        population: "Adults with HF and iron deficiency", nTotal: 3065, nTreatment: 1532, nControl: 1533,
        status: "Published", reference: "See CT.gov NCT03037931",
        outcomes: { mace: { tE: 0, tN: 1532, cE: 0, cN: 1533 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "HEART-FID: N=3,065. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* ICOSAPENT ETHYL — CV PREVENTION */
  /* ============================================================ */
  icosapent_cv: {
    id: "icosapent_cv", name: "Icosapent Ethyl — CV Prevention", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with elevated triglycerides on statin therapy",
      intervention: "Icosapent ethyl (EPA)",
      comparator: "Placebo (mineral oil or corn oil)",
      outcomes: [
        { id: "mace", name: "MACE composite", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(icosapent ethyl OR vascepa OR eicosapentaenoic acid EPA) AND (cardiovascular AND triglycerides) AND (COMPLETED)",
      pubmed: "(icosapent ethyl OR vascepa OR eicosapentaenoic acid EPA) AND (cardiovascular AND triglycerides) AND (randomized controlled trial[pt])",
      openalex: "icosapent ethyl OR vascepa OR eicosapentaenoic acid EPA AND cardiovascular AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Icosapent ethyl (EPA) vs Placebo (mineral oil or corn oil)", "Reports MACE composite"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "REDUCE-IT", nctId: "NCT01492361", year: 2018, phase: "PHASE3",
        population: "Adults with elevated triglycerides on statin therapy", nTotal: 8179, nTreatment: 4089, nControl: 4090,
        status: "Published", reference: "See CT.gov NCT01492361",
        outcomes: {
          mace: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.75, hrLo: 0.68, hrHi: 0.83, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_1: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.74, hrLo: 0.65, hrHi: 0.83, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_2: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.75, hrLo: 0.66, hrHi: 0.86, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_3: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.69, hrLo: 0.58, hrHi: 0.81, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_4: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.65, hrLo: 0.55, hrHi: 0.78, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_5: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.8, hrLo: 0.66, hrHi: 0.98, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_6: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.68, hrLo: 0.53, hrHi: 0.87, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_7: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.72, hrLo: 0.55, hrHi: 0.93, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_8: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.77, hrLo: 0.69, hrHi: 0.86, src: 'CT.gov NCT01492361 results. log rank.' },
          secondary_9: { tE: 0, tN: 4089, cE: 0, cN: 4090, hr: 0.87, hrLo: 0.74, hrHi: 1.02, src: 'CT.gov NCT01492361 results. log rank.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "REDUCE-IT: N=8,179. See CT.gov for full results."
      },
      { id: "STRENGTH", nctId: "NCT02104817", year: 2020, phase: "PHASE3",
        population: "Adults with elevated triglycerides on statin therapy", nTotal: 13078, nTreatment: 6539, nControl: 6539,
        status: "Published", reference: "See CT.gov NCT02104817",
        outcomes: {
          mace: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 0.99, hrLo: 0.9, hrHi: 1.09, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_1: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 0.94, hrLo: 0.84, hrHi: 1.05, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_2: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 1.05, hrLo: 0.93, hrHi: 1.19, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_3: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 1.01, hrLo: 0.87, hrHi: 1.16, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_4: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 0.91, hrLo: 0.81, hrHi: 1.02, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_5: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 0.85, hrLo: 0.75, hrHi: 0.97, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_6: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 1.09, hrLo: 0.9, hrHi: 1.31, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_7: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 1.12, hrLo: 0.89, hrHi: 1.41, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_8: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 1.13, hrLo: 0.97, hrHi: 1.31, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_9: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 1.18, hrLo: 0.97, hrHi: 1.42, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_10: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 0.94, hrLo: 0.83, hrHi: 1.08, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_11: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 0.84, hrLo: 0.63, hrHi: 1.12, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_12: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 0.97, hrLo: 0.81, hrHi: 1.17, src: 'CT.gov NCT02104817 results. regression, cox.' },
          secondary_13: { tE: 0, tN: 6539, cE: 0, cN: 6539, hr: 1.14, hrLo: 0.9, hrHi: 1.45, src: 'CT.gov NCT02104817 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "STRENGTH: N=13,078. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* VERICIGUAT — HEART FAILURE */
  /* ============================================================ */
  vericiguat_hf: {
    id: "vericiguat_hf", name: "Vericiguat — Heart Failure", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with worsening chronic HF (EF<45%)",
      intervention: "Vericiguat (sGC stimulator)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "CV death or HF hospitalization", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(vericiguat) AND (heart failure) AND (COMPLETED)",
      pubmed: "(vericiguat) AND (heart failure) AND (randomized controlled trial[pt])",
      openalex: "vericiguat AND heart failure AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Vericiguat (sGC stimulator) vs Placebo", "Reports CV death or HF hospitalization"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "VICTORIA", nctId: "NCT02861534", year: 2019, phase: "PHASE3",
        population: "Adults with worsening chronic HF (EF<45%)", nTotal: 5050, nTreatment: 2525, nControl: 2525,
        status: "Published", reference: "See CT.gov NCT02861534",
        outcomes: {
          secondary_0: { tE: 0, tN: 2525, cE: 0, cN: 2525, hr: 0.93, hrLo: 0.81, hrHi: 1.06, src: 'CT.gov NCT02861534 results. cox proportional hazard model.' },
          secondary_1: { tE: 0, tN: 2525, cE: 0, cN: 2525, hr: 0.9, hrLo: 0.81, hrHi: 1.0, src: 'CT.gov NCT02861534 results. cox proportional hazard model.' },
          mace: { tE: 0, tN: 2525, cE: 0, cN: 2525, hr: 0.9, hrLo: 0.82, hrHi: 0.98, src: 'CT.gov NCT02861534 results. cox proportional hazard model.' },
          secondary_3: { tE: 0, tN: 2525, cE: 0, cN: 2525, hr: 0.91, hrLo: 0.84, hrHi: 0.99, src: 'CT.gov NCT02861534 results. andersen-gill model.' },
          secondary_4: { tE: 0, tN: 2525, cE: 0, cN: 2525, hr: 0.9, hrLo: 0.83, hrHi: 0.98, src: 'CT.gov NCT02861534 results. cox proportional hazard model.' },
          secondary_5: { tE: 0, tN: 2525, cE: 0, cN: 2525, hr: 0.95, hrLo: 0.84, hrHi: 1.07, src: 'CT.gov NCT02861534 results. cox proportional hazard model.' },
          secondary_6: { tE: 0, tN: 2525, cE: 0, cN: 2525, hr: 1.2, hrLo: -0.3, hrHi: 2.8, src: 'CT.gov NCT02861534 results. miettinen & nurminen method.' },
          secondary_7: { tE: 0, tN: 2525, cE: 0, cN: 2525, hr: 0.6, hrLo: -0.5, hrHi: 1.6, src: 'CT.gov NCT02861534 results. miettinen & nurminen method.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "VICTORIA: N=5,050. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* OMECAMTIV MECARBIL — HEART FAILURE */
  /* ============================================================ */
  omecamtiv_hf: {
    id: "omecamtiv_hf", name: "Omecamtiv Mecarbil — Heart Failure", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with HFrEF (EF<=35%)",
      intervention: "Omecamtiv mecarbil (cardiac myosin activator)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "CV death or HF event", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(omecamtiv mecarbil) AND (heart failure) AND (COMPLETED)",
      pubmed: "(omecamtiv mecarbil) AND (heart failure) AND (randomized controlled trial[pt])",
      openalex: "omecamtiv mecarbil AND heart failure AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Omecamtiv mecarbil (cardiac myosin activator) vs Placebo", "Reports CV death or HF event"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "GALACTIC-HF", nctId: "NCT02929329", year: 2020, phase: "PHASE3",
        population: "Adults with HFrEF (EF<=35%)", nTotal: 8256, nTreatment: 4128, nControl: 4128,
        status: "Published", reference: "See CT.gov NCT02929329",
        outcomes: {
          mace: { tE: 0, tN: 4128, cE: 0, cN: 4128, hr: 0.92, hrLo: 0.86, hrHi: 0.99, src: 'CT.gov NCT02929329 results. regression, cox.' },
          secondary_1: { tE: 0, tN: 4128, cE: 0, cN: 4128, hr: 1.01, hrLo: 0.92, hrHi: 1.11, src: 'CT.gov NCT02929329 results. regression, cox.' },
          secondary_2: { tE: 0, tN: 4128, cE: 0, cN: 4128, hr: -0.46, hrLo: -1.4, hrHi: 0.48, src: 'CT.gov NCT02929329 results. .' },
          secondary_3: { tE: 0, tN: 4128, cE: 0, cN: 4128, hr: 0.95, hrLo: 0.87, hrHi: 1.03, src: 'CT.gov NCT02929329 results. regression, cox.' },
          secondary_4: { tE: 0, tN: 4128, cE: 0, cN: 4128, hr: 1.0, hrLo: 0.92, hrHi: 1.09, src: 'CT.gov NCT02929329 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "GALACTIC-HF: N=8,256. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* MAVACAMTEN — HYPERTROPHIC CARDIOMYOPATHY */
  /* ============================================================ */
  mavacamten_hcm: {
    id: "mavacamten_hcm", name: "Mavacamten — Hypertrophic Cardiomyopathy", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with symptomatic obstructive HCM",
      intervention: "Mavacamten (cardiac myosin inhibitor)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "Exercise capacity + LVOT gradient reduction", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(mavacamten OR camzyos) AND (hypertrophic cardiomyopathy) AND (COMPLETED)",
      pubmed: "(mavacamten OR camzyos) AND (hypertrophic cardiomyopathy) AND (randomized controlled trial[pt])",
      openalex: "mavacamten OR camzyos AND hypertrophic cardiomyopathy AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Mavacamten (cardiac myosin inhibitor) vs Placebo", "Reports Exercise capacity + LVOT gradient reduction"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "EXPLORER-HCM", nctId: "NCT03470545", year: 2020, phase: "PHASE3",
        population: "Adults with symptomatic obstructive HCM", nTotal: 251, nTreatment: 125, nControl: 126,
        status: "Published", reference: "See CT.gov NCT03470545",
        outcomes: { mace: { tE: 0, tN: 125, cE: 0, cN: 126 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "EXPLORER-HCM: N=251. See CT.gov for full results."
      },
      { id: "VALOR-HCM", nctId: "NCT04349072", year: 2024, phase: "PHASE3",
        population: "Adults with symptomatic obstructive HCM", nTotal: 112, nTreatment: 56, nControl: 56,
        status: "Published", reference: "See CT.gov NCT04349072",
        outcomes: {
          mace: { tE: 0, tN: 56, cE: 0, cN: 56, hr: 58.93, hrLo: 43.989, hrHi: 73.868, src: 'CT.gov NCT04349072 results. cochran-mantel-haenszel.' },
          secondary_1: { tE: 0, tN: 56, cE: 0, cN: 56, hr: 41.07, hrLo: 24.481, hrHi: 57.662, src: 'CT.gov NCT04349072 results. cochran-mantel-haenszel.' },
          secondary_2: { tE: 0, tN: 56, cE: 0, cN: 56, hr: 9.45, hrLo: 4.868, hrHi: 14.041, src: 'CT.gov NCT04349072 results. mixed models analysis.' },
          secondary_3: { tE: 0, tN: 56, cE: 0, cN: 56, hr: 0.33, hrLo: 0.266, hrHi: 0.421, src: 'CT.gov NCT04349072 results. mixed models analysis.' },
          secondary_4: { tE: 0, tN: 56, cE: 0, cN: 56, hr: 0.53, hrLo: 0.406, hrHi: 0.7, src: 'CT.gov NCT04349072 results. mixed models analysis.' },
          secondary_5: { tE: 0, tN: 56, cE: 0, cN: 56, hr: -37.2, hrLo: -48.08, hrHi: -26.24, src: 'CT.gov NCT04349072 results. ancova.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "VALOR-HCM: N=112. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* CANAKINUMAB — ANTI-IL-1B CV */
  /* ============================================================ */
  canakinumab_cv: {
    id: "canakinumab_cv", name: "Canakinumab — Anti-IL-1b CV", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with prior MI and elevated hsCRP",
      intervention: "Canakinumab (anti-IL-1beta)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "MACE (CV death, MI, stroke)", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(canakinumab) AND (cardiovascular AND inflammation) AND (COMPLETED)",
      pubmed: "(canakinumab) AND (cardiovascular AND inflammation) AND (randomized controlled trial[pt])",
      openalex: "canakinumab AND cardiovascular AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Canakinumab (anti-IL-1beta) vs Placebo", "Reports MACE"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "CANTOS", nctId: "NCT01327846", year: 2019, phase: "PHASE3",
        population: "Adults with prior MI and elevated hsCRP", nTotal: 10066, nTreatment: 5033, nControl: 5033,
        status: "Published", reference: "See CT.gov NCT01327846",
        outcomes: {
          mace: { tE: 0, tN: 5033, cE: 0, cN: 5033, hr: 0.86, hrLo: 0.75, hrHi: 0.99, src: 'CT.gov NCT01327846 results. log rank.' },
          secondary_1: { tE: 0, tN: 5033, cE: 0, cN: 5033, hr: 0.82, hrLo: 0.72, hrHi: 0.94, src: 'CT.gov NCT01327846 results. log rank.' },
          secondary_2: { tE: 0, tN: 5033, cE: 0, cN: 5033, hr: 1.01, hrLo: 0.83, hrHi: 1.23, src: 'CT.gov NCT01327846 results. log rank.' },
          secondary_3: { tE: 0, tN: 5033, cE: 0, cN: 5033, hr: 0.87, hrLo: 0.77, hrHi: 0.99, src: 'CT.gov NCT01327846 results. regression, cox.' },
          secondary_4: { tE: 0, tN: 5033, cE: 0, cN: 5033, hr: 0.93, hrLo: 0.79, hrHi: 1.1, src: 'CT.gov NCT01327846 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "CANTOS: N=10,066. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* RIVAROXABAN — VASCULAR PROTECTION */
  /* ============================================================ */
  rivaroxaban_vasc: {
    id: "rivaroxaban_vasc", name: "Rivaroxaban — Vascular Protection", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with stable atherosclerotic vascular disease",
      intervention: "Low-dose rivaroxaban + aspirin",
      comparator: "Aspirin alone",
      outcomes: [
        { id: "mace", name: "CV death, MI, or stroke", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(rivaroxaban) AND (atherosclerosis OR peripheral artery disease) AND (COMPLETED)",
      pubmed: "(rivaroxaban) AND (atherosclerosis OR peripheral artery disease) AND (randomized controlled trial[pt])",
      openalex: "rivaroxaban AND atherosclerosis OR peripheral artery disease AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Low-dose rivaroxaban + aspirin vs Aspirin alone", "Reports CV death, MI, or stroke"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "COMPASS", nctId: "NCT01776424", year: 2021, phase: "PHASE3",
        population: "Adults with stable atherosclerotic vascular disease", nTotal: 27395, nTreatment: 13697, nControl: 13698,
        status: "Published", reference: "See CT.gov NCT01776424",
        outcomes: {
          mace: { tE: 0, tN: 13697, cE: 0, cN: 13698, hr: 1.7, hrLo: 1.4, hrHi: 2.05, src: 'CT.gov NCT01776424 results. log rank.' },
          secondary_1: { tE: 0, tN: 13697, cE: 0, cN: 13698, hr: 0.72, hrLo: 0.63, hrHi: 0.83, src: 'CT.gov NCT01776424 results. log rank.' },
          secondary_2: { tE: 0, tN: 13697, cE: 0, cN: 13698, hr: 0.74, hrLo: 0.65, hrHi: 0.85, src: 'CT.gov NCT01776424 results. log rank.' },
          secondary_3: { tE: 0, tN: 13697, cE: 0, cN: 13698, hr: 0.82, hrLo: 0.71, hrHi: 0.96, src: 'CT.gov NCT01776424 results. log rank.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "COMPASS: N=27,395. See CT.gov for full results."
      },
      { id: "VOYAGER PAD", nctId: "NCT02504216", year: 2020, phase: "PHASE3",
        population: "Adults with stable atherosclerotic vascular disease", nTotal: 6564, nTreatment: 3282, nControl: 3282,
        status: "Published", reference: "See CT.gov NCT02504216",
        outcomes: {
          mace: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 1.43, hrLo: 0.97, hrHi: 2.1, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_1: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 0.8, hrLo: 0.71, hrHi: 0.91, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_2: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 0.88, hrLo: 0.79, hrHi: 0.99, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_3: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 0.72, hrLo: 0.62, hrHi: 0.85, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_4: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 0.89, hrLo: 0.79, hrHi: 0.99, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_5: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 0.86, hrLo: 0.76, hrHi: 0.96, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_6: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 1.08, hrLo: 0.92, hrHi: 1.27, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_7: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 0.61, hrLo: 0.37, hrHi: 1.0, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_8: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 1.42, hrLo: 1.1, hrHi: 1.84, src: 'CT.gov NCT02504216 results. log rank.' },
          secondary_9: { tE: 0, tN: 3282, cE: 0, cN: 3282, hr: 1.29, hrLo: 0.95, hrHi: 1.76, src: 'CT.gov NCT02504216 results. log rank.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "VOYAGER PAD: N=6,564. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* SEMAGLUTIDE — CKD (FLOW) */
  /* ============================================================ */
  semaglutide_ckd: {
    id: "semaglutide_ckd", name: "Semaglutide — CKD (FLOW)", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with T2DM and CKD",
      intervention: "Semaglutide 1.0 mg SC weekly",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "Kidney composite (dialysis, transplant, eGFR decline, renal/CV death)", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(semaglutide) AND (chronic kidney disease AND type 2 diabetes) AND (COMPLETED)",
      pubmed: "(semaglutide) AND (chronic kidney disease AND type 2 diabetes) AND (randomized controlled trial[pt])",
      openalex: "semaglutide AND chronic kidney disease AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Semaglutide 1.0 mg SC weekly vs Placebo", "Reports Kidney composite"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "FLOW", nctId: "NCT03819153", year: 2024, phase: "PHASE3",
        population: "Adults with T2DM and CKD", nTotal: 3533, nTreatment: 1766, nControl: 1767,
        status: "Published", reference: "See CT.gov NCT03819153",
        outcomes: {
          mace: { tE: 0, tN: 1766, cE: 0, cN: 1767, hr: 0.76, hrLo: 0.66, hrHi: 0.88, src: 'CT.gov NCT03819153 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "FLOW: N=3,533. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* TIRZEPATIDE — TYPE 2 DIABETES */
  /* ============================================================ */
  tirzepatide_t2dm: {
    id: "tirzepatide_t2dm", name: "Tirzepatide — Type 2 Diabetes", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with T2DM inadequately controlled",
      intervention: "Tirzepatide (dual GIP/GLP-1 RA)",
      comparator: "Placebo or active comparator",
      outcomes: [
        { id: "mace", name: "HbA1c reduction from baseline", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(tirzepatide) AND (type 2 diabetes) AND (COMPLETED)",
      pubmed: "(tirzepatide) AND (type 2 diabetes) AND (randomized controlled trial[pt])",
      openalex: "tirzepatide AND type 2 diabetes AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Tirzepatide (dual GIP/GLP-1 RA) vs Placebo or active comparator", "Reports HbA1c reduction from baseline"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "SURPASS-1", nctId: "NCT03954834", year: 2020, phase: "PHASE3",
        population: "Adults with T2DM inadequately controlled", nTotal: 478, nTreatment: 239, nControl: 239,
        status: "Published", reference: "See CT.gov NCT03954834",
        outcomes: {
          mace: { tE: 0, tN: 239, cE: 0, cN: 239, hr: -1.91, hrLo: -2.18, hrHi: -1.63, src: 'CT.gov NCT03954834 results. mixed models analysis.' },
          secondary_1: { tE: 0, tN: 239, cE: 0, cN: 239, hr: -6.3, hrLo: -7.8, hrHi: -4.7, src: 'CT.gov NCT03954834 results. mixed models analysis.' },
          secondary_2: { tE: 0, tN: 239, cE: 0, cN: 239, hr: 49.0, hrLo: 21.12, hrHi: 113.67, src: 'CT.gov NCT03954834 results. regression, logistic.' },
          secondary_3: { tE: 0, tN: 239, cE: 0, cN: 239, hr: -1.5, hrLo: -11.9, hrHi: 8.9, src: 'CT.gov NCT03954834 results. mixed models analysis.' },
          secondary_4: { tE: 0, tN: 239, cE: 0, cN: 239, hr: 40.28, hrLo: 7.74, hrHi: 209.71, src: 'CT.gov NCT03954834 results. regression, logistic.' },
          secondary_5: { tE: 0, tN: 239, cE: 0, cN: 239, hr: -37.7, hrLo: -44.1, hrHi: -31.2, src: 'CT.gov NCT03954834 results. mixed models analysis.' },
          secondary_6: { tE: 0, tN: 239, cE: 0, cN: 239, hr: 12.4, hrLo: 6.43, hrHi: 23.94, src: 'CT.gov NCT03954834 results. regression, logistic.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "SURPASS-1: N=478. See CT.gov for full results."
      },
      { id: "SURPASS-2", nctId: "NCT03987919", year: 2021, phase: "PHASE3",
        population: "Adults with T2DM inadequately controlled", nTotal: 1879, nTreatment: 939, nControl: 940,
        status: "Published", reference: "See CT.gov NCT03987919",
        outcomes: {
          mace: { tE: 0, tN: 939, cE: 0, cN: 940, hr: -0.51, hrLo: -0.64, hrHi: -0.38, src: 'CT.gov NCT03987919 results. mixed models analysis.' },
          secondary_1: { tE: 0, tN: 939, cE: 0, cN: 940, hr: -0.23, hrLo: -0.36, hrHi: -0.1, src: 'CT.gov NCT03987919 results. mixed models analysis.' },
          secondary_2: { tE: 0, tN: 939, cE: 0, cN: 940, hr: -1.7, hrLo: -2.6, hrHi: -0.7, src: 'CT.gov NCT03987919 results. mixed models analysis.' },
          secondary_3: { tE: 0, tN: 939, cE: 0, cN: 940, hr: 1.54, hrLo: 1.06, hrHi: 2.23, src: 'CT.gov NCT03987919 results. regression, logistic.' },
          secondary_4: { tE: 0, tN: 939, cE: 0, cN: 940, hr: -7.3, hrLo: -11.7, hrHi: -3.0, src: 'CT.gov NCT03987919 results. mixed models analysis.' },
          secondary_5: { tE: 0, tN: 939, cE: 0, cN: 940, hr: 1.58, hrLo: 1.2, hrHi: 2.08, src: 'CT.gov NCT03987919 results. regression, logistic.' },
          secondary_6: { tE: 0, tN: 939, cE: 0, cN: 940, hr: -0.24, hrLo: -0.5, hrHi: 0.03, src: 'CT.gov NCT03987919 results. ancova.' },
          secondary_7: { tE: 0, tN: 939, cE: 0, cN: 940, hr: 1.86, hrLo: 1.35, hrHi: 2.57, src: 'CT.gov NCT03987919 results. regression, logistic.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "SURPASS-2: N=1,879. See CT.gov for full results."
      },
      { id: "SURPASS-3", nctId: "NCT03882970", year: 2021, phase: "PHASE3",
        population: "Adults with T2DM inadequately controlled", nTotal: 1444, nTreatment: 722, nControl: 722,
        status: "Published", reference: "See CT.gov NCT03882970",
        outcomes: {
          mace: { tE: 0, tN: 722, cE: 0, cN: 722, hr: -0.86, hrLo: -1.0, hrHi: -0.72, src: 'CT.gov NCT03882970 results. mixed models analysis.' },
          secondary_1: { tE: 0, tN: 722, cE: 0, cN: 722, hr: -0.59, hrLo: -0.73, hrHi: -0.45, src: 'CT.gov NCT03882970 results. mixed models analysis.' },
          secondary_2: { tE: 0, tN: 722, cE: 0, cN: 722, hr: -9.8, hrLo: -10.8, hrHi: -8.8, src: 'CT.gov NCT03882970 results. mixed models analysis.' },
          secondary_3: { tE: 0, tN: 722, cE: 0, cN: 722, hr: 7.5, hrLo: 2.4, hrHi: 12.5, src: 'CT.gov NCT03882970 results. mixed models analysis.' },
          secondary_4: { tE: 0, tN: 722, cE: 0, cN: 722, hr: 3.45, hrLo: 2.38, hrHi: 5.01, src: 'CT.gov NCT03882970 results. regression, logistic.' },
          secondary_5: { tE: 0, tN: 722, cE: 0, cN: 722, hr: 29.78, hrLo: 18.35, hrHi: 48.35, src: 'CT.gov NCT03882970 results. regression, logistic.' },
          secondary_6: { tE: 0, tN: 722, cE: 0, cN: 722, hr: -0.26, hrLo: -0.57, hrHi: 0.05, src: 'CT.gov NCT03882970 results. ancova.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "SURPASS-3: N=1,444. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* SEMAGLUTIDE — OBESITY */
  /* ============================================================ */
  semaglutide_obesity: {
    id: "semaglutide_obesity", name: "Semaglutide — Obesity", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with obesity (BMI>=30) or overweight with comorbidities",
      intervention: "Semaglutide 2.4 mg SC weekly",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "Percent body weight change", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(semaglutide) AND (obesity OR overweight) AND (COMPLETED)",
      pubmed: "(semaglutide) AND (obesity OR overweight) AND (randomized controlled trial[pt])",
      openalex: "semaglutide AND obesity OR overweight AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Semaglutide 2.4 mg SC weekly vs Placebo", "Reports Percent body weight change"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "STEP 1", nctId: "NCT03548935", year: 2021, phase: "PHASE3",
        population: "Adults with obesity (BMI>=30) or overweight with comorbiditi", nTotal: 1961, nTreatment: 980, nControl: 981,
        status: "Published", reference: "See CT.gov NCT03548935",
        outcomes: {
          mace: { tE: 0, tN: 980, cE: 0, cN: 981, hr: 11.22, hrLo: 8.88, hrHi: 14.19, src: 'CT.gov NCT03548935 results. regression, logistic.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "STEP 1: N=1,961. See CT.gov for full results."
      },
      { id: "STEP 2", nctId: "NCT03552757", year: 2020, phase: "PHASE3",
        population: "Adults with obesity (BMI>=30) or overweight with comorbiditi", nTotal: 1210, nTreatment: 605, nControl: 605,
        status: "Published", reference: "See CT.gov NCT03552757",
        outcomes: {
          mace: { tE: 0, tN: 605, cE: 0, cN: 605, hr: 4.88, hrLo: 3.58, hrHi: 6.64, src: 'CT.gov NCT03552757 results. regression, logistic.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "STEP 2: N=1,210. See CT.gov for full results."
      },
      { id: "STEP 3", nctId: "NCT03611582", year: 2020, phase: "PHASE3",
        population: "Adults with obesity (BMI>=30) or overweight with comorbiditi", nTotal: 611, nTreatment: 305, nControl: 306,
        status: "Published", reference: "See CT.gov NCT03611582",
        outcomes: {
          mace: { tE: 0, tN: 305, cE: 0, cN: 306, hr: 6.11, hrLo: 4.04, hrHi: 9.26, src: 'CT.gov NCT03611582 results. regression, logistic.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "STEP 3: N=611. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* TIRZEPATIDE — OBESITY */
  /* ============================================================ */
  tirzepatide_obesity: {
    id: "tirzepatide_obesity", name: "Tirzepatide — Obesity", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with obesity (BMI>=30) or overweight",
      intervention: "Tirzepatide (dual GIP/GLP-1 RA)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "Percent body weight change", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(tirzepatide) AND (obesity OR overweight) AND (COMPLETED)",
      pubmed: "(tirzepatide) AND (obesity OR overweight) AND (randomized controlled trial[pt])",
      openalex: "tirzepatide AND obesity OR overweight AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Tirzepatide (dual GIP/GLP-1 RA) vs Placebo", "Reports Percent body weight change"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "SURMOUNT-1", nctId: "NCT04184622", year: 2024, phase: "PHASE3",
        population: "Adults with obesity (BMI>=30) or overweight", nTotal: 2539, nTreatment: 1269, nControl: 1270,
        status: "Published", reference: "See CT.gov NCT04184622",
        outcomes: {
          mace: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 23.99, hrLo: 17.43, hrHi: 33.02, src: 'CT.gov NCT04184622 results. regression, logistic.' },
          secondary_1: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -10.7, hrLo: -11.2, hrHi: -10.1, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_2: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 19.03, hrLo: 14.15, hrHi: 25.6, src: 'CT.gov NCT04184622 results. regression, logistic.' },
          secondary_3: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 17.08, hrLo: 11.83, hrHi: 24.66, src: 'CT.gov NCT04184622 results. regression, logistic.' },
          secondary_4: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 36.93, hrLo: 18.37, hrHi: 74.22, src: 'CT.gov NCT04184622 results. regression, logistic.' },
          secondary_5: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -11.2, hrLo: -12.3, hrHi: -10.0, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_6: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 2.3, hrLo: 1.6, hrHi: 2.9, src: 'CT.gov NCT04184622 results. ancova.' },
          secondary_7: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -22.7, hrLo: -25.6, hrHi: -19.8, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_8: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -4.91, hrLo: -6.4, hrHi: -3.41, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_9: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 7.65, hrLo: 5.85, hrHi: 9.49, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_10: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -6.8, hrLo: -7.9, hrHi: -5.7, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_11: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -41.2, hrLo: -44.9, hrHi: -37.3, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_12: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -13.2, hrLo: -15.3, hrHi: -11.1, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_13: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 0.06, hrLo: 0.03, hrHi: 0.13, src: 'CT.gov NCT04184622 results. regression, cox.' },
          secondary_14: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 0.12, hrLo: 0.07, hrHi: 0.21, src: 'CT.gov NCT04184622 results. regression, cox.' },
          secondary_15: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -5.1, hrLo: -5.5, hrHi: -4.6, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_16: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -0.33, hrLo: -0.36, hrHi: -0.3, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_17: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -8.59, hrLo: -9.97, hrHi: -7.2, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_18: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -6.06, hrLo: -8.32, hrHi: -3.75, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_19: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -23.3, hrLo: -26.1, hrHi: -20.4, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_20: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -11.3, hrLo: -16.1, hrHi: -6.2, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_21: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: -4.2, hrLo: -5.0, hrHi: -3.5, src: 'CT.gov NCT04184622 results. mixed models analysis.' },
          secondary_22: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 29.79, hrLo: 17.73, hrHi: 50.05, src: 'CT.gov NCT04184622 results. regression, logistic.' },
          secondary_23: { tE: 0, tN: 1269, cE: 0, cN: 1270, hr: 7.7, hrLo: 5.6, hrHi: 9.8, src: 'CT.gov NCT04184622 results. ancova.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "SURMOUNT-1: N=2,539. See CT.gov for full results."
      },
      { id: "SURMOUNT-2", nctId: "NCT04657003", year: 2023, phase: "PHASE3",
        population: "Adults with obesity (BMI>=30) or overweight", nTotal: 938, nTreatment: 469, nControl: 469,
        status: "Published", reference: "See CT.gov NCT04657003",
        outcomes: {
          mace: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 10.75, hrLo: 7.3, hrHi: 15.84, src: 'CT.gov NCT04657003 results. regression, logistic.' },
          secondary_1: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 20.94, hrLo: 13.06, hrHi: 33.58, src: 'CT.gov NCT04657003 results. regression, logistic.' },
          secondary_2: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 28.38, hrLo: 13.81, hrHi: 58.31, src: 'CT.gov NCT04657003 results. regression, logistic.' },
          secondary_3: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 28.54, hrLo: 9.73, hrHi: 83.73, src: 'CT.gov NCT04657003 results. regression, logistic.' },
          secondary_4: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -10.3, hrLo: -11.7, hrHi: -8.8, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_5: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -3.7, hrLo: -4.2, hrHi: -3.2, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_6: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -1.97, hrLo: -2.15, hrHi: -1.8, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_7: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 28.01, hrLo: 17.21, hrHi: 45.59, src: 'CT.gov NCT04657003 results. regression, logistic.' },
          secondary_8: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 42.11, hrLo: 25.61, hrHi: 69.26, src: 'CT.gov NCT04657003 results. regression, logistic.' },
          secondary_9: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 42.55, hrLo: 20.46, hrHi: 88.5, src: 'CT.gov NCT04657003 results. regression, logistic.' },
          secondary_10: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -46.79, hrLo: -52.67, hrHi: -40.91, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_11: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -7.8, hrLo: -9.2, hrHi: -6.4, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_12: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -4.61, hrLo: -7.11, hrHi: -2.03, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_13: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -3.36, hrLo: -7.36, hrHi: 0.81, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_14: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 7.02, hrLo: 4.4, hrHi: 9.71, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_15: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -23.3, hrLo: -27.5, hrHi: -18.9, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_16: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -24.2, hrLo: -28.6, hrHi: -19.6, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_17: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -8.74, hrLo: -12.04, hrHi: -5.32, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_18: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -23.61, hrLo: -28.62, hrHi: -18.24, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_19: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -6.2, hrLo: -8.0, hrHi: -4.4, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_20: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -2.4, hrLo: -3.5, hrHi: -1.3, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_21: { tE: 0, tN: 469, cE: 0, cN: 469, hr: -17.6, hrLo: -25.5, hrHi: -8.9, src: 'CT.gov NCT04657003 results. mixed models analysis.' },
          secondary_22: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 1.8, hrLo: 0.7, hrHi: 2.9, src: 'CT.gov NCT04657003 results. ancova.' },
          secondary_23: { tE: 0, tN: 469, cE: 0, cN: 469, hr: 6.9, hrLo: 4.1, hrHi: 9.7, src: 'CT.gov NCT04657003 results. ancova.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "SURMOUNT-2: N=938. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* INCLISIRAN — SIRNA PCSK9 */
  /* ============================================================ */
  inclisiran: {
    id: "inclisiran", name: "Inclisiran — siRNA PCSK9", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with ASCVD, FH, or high CV risk with elevated LDL-C",
      intervention: "Inclisiran (siRNA PCSK9 inhibitor)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "LDL-C reduction at Day 510", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(inclisiran) AND (hypercholesterolemia OR ASCVD OR familial hypercholesterolemia) AND (COMPLETED)",
      pubmed: "(inclisiran) AND (hypercholesterolemia OR ASCVD OR familial hypercholesterolemia) AND (randomized controlled trial[pt])",
      openalex: "inclisiran AND hypercholesterolemia OR ASCVD OR familial hypercholesterolemia AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Inclisiran (siRNA PCSK9 inhibitor) vs Placebo", "Reports LDL-C reduction at Day 510"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "ORION-10", nctId: "NCT03399370", year: 2019, phase: "PHASE3",
        population: "Adults with ASCVD, FH, or high CV risk with elevated LDL-C", nTotal: 1561, nTreatment: 780, nControl: 781,
        status: "Published", reference: "See CT.gov NCT03399370",
        outcomes: {
          mace: { tE: 0, tN: 780, cE: 0, cN: 781, hr: -53.78, hrLo: -56.23, hrHi: -51.33, src: 'CT.gov NCT03399370 results. ancova.' },
          secondary_1: { tE: 0, tN: 780, cE: 0, cN: 781, hr: -54.12, hrLo: -57.37, hrHi: -50.88, src: 'CT.gov NCT03399370 results. ancova.' },
          secondary_2: { tE: 0, tN: 780, cE: 0, cN: 781, hr: -53.28, hrLo: -55.75, hrHi: -50.8, src: 'CT.gov NCT03399370 results. ancova.' },
          secondary_3: { tE: 0, tN: 780, cE: 0, cN: 781, hr: -83.8, hrLo: -89.25, hrHi: -77.34, src: 'CT.gov NCT03399370 results. ancova.' },
          secondary_4: { tE: 0, tN: 780, cE: 0, cN: 781, hr: -33.13, hrLo: -35.3, hrHi: -30.97, src: 'CT.gov NCT03399370 results. ancova.' },
          secondary_5: { tE: 0, tN: 780, cE: 0, cN: 781, hr: -43.09, hrLo: -45.5, hrHi: -40.67, src: 'CT.gov NCT03399370 results. ancova.' },
          secondary_6: { tE: 0, tN: 780, cE: 0, cN: 781, hr: -47.36, hrLo: -50.25, hrHi: -44.47, src: 'CT.gov NCT03399370 results. ancova.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "ORION-10: N=1,561. See CT.gov for full results."
      },
      { id: "ORION-11", nctId: "NCT03400800", year: 2019, phase: "PHASE3",
        population: "Adults with ASCVD, FH, or high CV risk with elevated LDL-C", nTotal: 1617, nTreatment: 808, nControl: 809,
        status: "Published", reference: "See CT.gov NCT03400800",
        outcomes: {
          mace: { tE: 0, tN: 808, cE: 0, cN: 809, hr: -49.17, hrLo: -51.57, hrHi: -46.77, src: 'CT.gov NCT03400800 results. ancova.' },
          secondary_1: { tE: 0, tN: 808, cE: 0, cN: 809, hr: -51.87, hrLo: -55.01, hrHi: -48.72, src: 'CT.gov NCT03400800 results. ancova.' },
          secondary_2: { tE: 0, tN: 808, cE: 0, cN: 809, hr: -48.94, hrLo: -51.39, hrHi: -46.48, src: 'CT.gov NCT03400800 results. ancova.' },
          secondary_3: { tE: 0, tN: 808, cE: 0, cN: 809, hr: -79.27, hrLo: -81.97, hrHi: -76.57, src: 'CT.gov NCT03400800 results. ancova.' },
          secondary_4: { tE: 0, tN: 808, cE: 0, cN: 809, hr: -29.79, hrLo: -31.78, hrHi: -27.81, src: 'CT.gov NCT03400800 results. ancova.' },
          secondary_5: { tE: 0, tN: 808, cE: 0, cN: 809, hr: -38.94, hrLo: -41.21, hrHi: -36.67, src: 'CT.gov NCT03400800 results. ancova.' },
          secondary_6: { tE: 0, tN: 808, cE: 0, cN: 809, hr: -43.32, hrLo: -46.04, hrHi: -40.6, src: 'CT.gov NCT03400800 results. ancova.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "ORION-11: N=1,617. See CT.gov for full results."
      },
      { id: "ORION-4", nctId: "NCT03705234", year: 2049, phase: "PHASE3",
        population: "Adults with ASCVD, FH, or high CV risk with elevated LDL-C", nTotal: 16124, nTreatment: 8062, nControl: 8062,
        status: "Published", reference: "See CT.gov NCT03705234",
        outcomes: { mace: { tE: 0, tN: 8062, cE: 0, cN: 8062 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "ORION-4: N=16,124. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* EZETIMIBE — CV PREVENTION */
  /* ============================================================ */
  ezetimibe_cv: {
    id: "ezetimibe_cv", name: "Ezetimibe — CV Prevention", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with recent ACS on statin therapy",
      intervention: "Ezetimibe + simvastatin",
      comparator: "Simvastatin alone",
      outcomes: [
        { id: "mace", name: "CV death, MI, UA hospitalization, revascularization, stroke", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(ezetimibe) AND (acute coronary syndrome) AND (COMPLETED)",
      pubmed: "(ezetimibe) AND (acute coronary syndrome) AND (randomized controlled trial[pt])",
      openalex: "ezetimibe AND acute coronary syndrome AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Ezetimibe + simvastatin vs Simvastatin alone", "Reports CV death, MI, UA hospitalization, revascularization, stroke"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "IMPROVE-IT", nctId: "NCT00202878", year: 2014, phase: "PHASE3",
        population: "Adults with recent ACS on statin therapy", nTotal: 18144, nTreatment: 9072, nControl: 9072,
        status: "Published", reference: "See CT.gov NCT00202878",
        outcomes: {
          mace: { tE: 0, tN: 9072, cE: 0, cN: 9072, hr: 0.936, hrLo: 0.887, hrHi: 0.988, src: 'CT.gov NCT00202878 results. cox proportional hazard model.' },
          secondary_1: { tE: 0, tN: 9072, cE: 0, cN: 9072, hr: 0.948, hrLo: 0.903, hrHi: 0.996, src: 'CT.gov NCT00202878 results. cox proportional hazard model.' },
          secondary_2: { tE: 0, tN: 9072, cE: 0, cN: 9072, hr: 0.912, hrLo: 0.847, hrHi: 0.983, src: 'CT.gov NCT00202878 results. cox proportional hazard model.' },
          secondary_3: { tE: 0, tN: 9072, cE: 0, cN: 9072, hr: 0.945, hrLo: 0.897, hrHi: 0.996, src: 'CT.gov NCT00202878 results. cox proportional hazard model.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "IMPROVE-IT: N=18,144. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* MITRACLIP — MITRAL REGURGITATION */
  /* ============================================================ */
  mitraclip_mr: {
    id: "mitraclip_mr", name: "MitraClip — Mitral Regurgitation", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with severe secondary mitral regurgitation despite GDMT",
      intervention: "Transcatheter mitral valve repair (MitraClip)",
      comparator: "Medical therapy alone",
      outcomes: [
        { id: "mace", name: "All-cause mortality or HF hospitalization", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(MitraClip OR transcatheter mitral valve repair) AND (mitral regurgitation) AND (COMPLETED)",
      pubmed: "(MitraClip OR transcatheter mitral valve repair) AND (mitral regurgitation) AND (randomized controlled trial[pt])",
      openalex: "MitraClip OR transcatheter mitral valve repair AND mitral regurgitation AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Transcatheter mitral valve repair (MitraClip) vs Medical therapy alone", "Reports All-cause mortality or HF hospitalization"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "COAPT", nctId: "NCT01626079", year: 2024, phase: "NA",
        population: "Adults with severe secondary mitral regurgitation despite GD", nTotal: 776, nTreatment: 388, nControl: 388,
        status: "Published", reference: "See CT.gov NCT01626079",
        outcomes: {
          mace: { tE: 0, tN: 388, cE: 0, cN: 388, hr: 0.966, hrLo: 0.948, hrHi: null, src: 'CT.gov NCT01626079 results. z test using kaplan meier survival.' },
          secondary_1: { tE: 0, tN: 388, cE: 0, cN: 388, hr: 0.76, hrLo: 0.6, hrHi: 0.96, src: 'CT.gov NCT01626079 results. joint fraility model.' },
          secondary_2: { tE: 0, tN: 388, cE: 0, cN: 388, hr: 1.61, hrLo: 1.29, hrHi: 2.04, src: 'CT.gov NCT01626079 results. finkelstein-schoenfeld analysis.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "COAPT: N=776. See CT.gov for full results."
      },
      { id: "MITRA-FR", nctId: "NCT01920698", year: 2019, phase: "NA",
        population: "Adults with severe secondary mitral regurgitation despite GD", nTotal: 304, nTreatment: 152, nControl: 152,
        status: "Published", reference: "See CT.gov NCT01920698",
        outcomes: { mace: { tE: 0, tN: 152, cE: 0, cN: 152 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "MITRA-FR: N=304. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* TAVR — LOW SURGICAL RISK */
  /* ============================================================ */
  tavr_low_risk: {
    id: "tavr_low_risk", name: "TAVR — Low Surgical Risk", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with severe aortic stenosis at low surgical risk",
      intervention: "TAVR (transcatheter aortic valve replacement)",
      comparator: "SAVR (surgical AVR)",
      outcomes: [
        { id: "mace", name: "All-cause mortality or disabling stroke at 1 year", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(transcatheter aortic valve replacement) AND (aortic stenosis) AND (COMPLETED)",
      pubmed: "(transcatheter aortic valve replacement) AND (aortic stenosis) AND (randomized controlled trial[pt])",
      openalex: "transcatheter aortic valve replacement AND aortic stenosis AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "TAVR (transcatheter aortic valve replacement) vs SAVR (surgical AVR)", "Reports All-cause mortality or disabling stroke at 1 year"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "P3", nctId: "NCT02675114", year: 2029, phase: "NA",
        population: "Adults with severe aortic stenosis at low surgical risk", nTotal: 1000, nTreatment: 500, nControl: 500,
        status: "Published", reference: "See CT.gov NCT02675114",
        outcomes: { mace: { tE: 0, tN: 500, cE: 0, cN: 500 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "P3: N=1,000. See CT.gov for full results."
      },
      { id: "Medtronic Evolut Tra", nctId: "NCT02701283", year: 2026, phase: "NA",
        population: "Adults with severe aortic stenosis at low surgical risk", nTotal: 2223, nTreatment: 1111, nControl: 1112,
        status: "Published", reference: "See CT.gov NCT02701283",
        outcomes: {
          mace: { tE: 0, tN: 1111, cE: 0, cN: 1112, hr: 0.999, hrLo: null, hrHi: null, src: 'CT.gov NCT02701283 results. bayesian.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Medtronic Evolut Tra: N=2,223. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* RENAL DENERVATION — HYPERTENSION */
  /* ============================================================ */
  renal_denervation: {
    id: "renal_denervation", name: "Renal Denervation — Hypertension", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with uncontrolled or resistant hypertension",
      intervention: "Catheter-based renal denervation",
      comparator: "Sham procedure",
      outcomes: [
        { id: "mace", name: "24-hour ambulatory SBP change", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(renal denervation) AND (hypertension) AND (COMPLETED)",
      pubmed: "(renal denervation) AND (hypertension) AND (randomized controlled trial[pt])",
      openalex: "renal denervation AND hypertension AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Catheter-based renal denervation vs Sham procedure", "Reports 24-hour ambulatory SBP change"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "SPYRAL PIVOTAL - SPY", nctId: "NCT02439749", year: 2023, phase: "NA",
        population: "Adults with uncontrolled or resistant hypertension", nTotal: 366, nTreatment: 183, nControl: 183,
        status: "Published", reference: "See CT.gov NCT02439749",
        outcomes: { mace: { tE: 0, tN: 183, cE: 0, cN: 183 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "SPYRAL PIVOTAL - SPY: N=366. See CT.gov for full results."
      },
      { id: "RADIANCE-II", nctId: "NCT03614260", year: 2027, phase: "NA",
        population: "Adults with uncontrolled or resistant hypertension", nTotal: 225, nTreatment: 112, nControl: 113,
        status: "Published", reference: "See CT.gov NCT03614260",
        outcomes: { mace: { tE: 0, tN: 112, cE: 0, cN: 113 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "RADIANCE-II: N=225. See CT.gov for full results."
      },
      { id: "RADIANCE-HTN", nctId: "NCT02649426", year: 2025, phase: "NA",
        population: "Adults with uncontrolled or resistant hypertension", nTotal: 282, nTreatment: 141, nControl: 141,
        status: "Published", reference: "See CT.gov NCT02649426",
        outcomes: { mace: { tE: 0, tN: 141, cE: 0, cN: 141 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "RADIANCE-HTN: N=282. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* DOACS — ATRIAL FIBRILLATION */
  /* ============================================================ */
  doac_af: {
    id: "doac_af", name: "DOACs — Atrial Fibrillation", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with non-valvular atrial fibrillation",
      intervention: "DOAC (apixaban, rivaroxaban, edoxaban, or dabigatran)",
      comparator: "Warfarin",
      outcomes: [
        { id: "mace", name: "Stroke or systemic embolism", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(apixaban OR rivaroxaban OR edoxaban OR dabigatran) AND (atrial fibrillation) AND (COMPLETED)",
      pubmed: "(apixaban OR rivaroxaban OR edoxaban OR dabigatran) AND (atrial fibrillation) AND (randomized controlled trial[pt])",
      openalex: "apixaban OR rivaroxaban OR edoxaban OR dabigatran AND atrial fibrillation AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "DOAC (apixaban, rivaroxaban, edoxaban, or dabigatran) vs Warfarin", "Reports Stroke or systemic embolism"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "ARISTOTLE", nctId: "NCT00412984", year: 2011, phase: "PHASE3",
        population: "Adults with non-valvular atrial fibrillation", nTotal: 20976, nTreatment: 10488, nControl: 10488,
        status: "Published", reference: "See CT.gov NCT00412984",
        outcomes: {
          mace: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.79, hrLo: 0.66, hrHi: 0.95, src: 'CT.gov NCT00412984 results. cox proportional hazards model.' },
          secondary_1: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.69, hrLo: 0.6, hrHi: 0.8, src: 'CT.gov NCT00412984 results. cox proportional hazards model.' },
          secondary_2: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.89, hrLo: 0.8, hrHi: 1.0, src: 'CT.gov NCT00412984 results. cox proportional hazards model.' },
          secondary_3: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.92, hrLo: 0.74, hrHi: 1.13, src: 'CT.gov NCT00412984 results. cox proportional hazards model.' },
          secondary_4: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.77, hrLo: 0.69, hrHi: 0.86, src: 'CT.gov NCT00412984 results. cox proportional hazards model.' },
          secondary_5: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.8, hrLo: 0.67, hrHi: 0.95, src: 'CT.gov NCT00412984 results. cox proportional hazards model.' },
          secondary_6: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.68, hrLo: 0.61, hrHi: 0.75, src: 'CT.gov NCT00412984 results. cox proportional hazard model.' },
          secondary_7: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.71, hrLo: 0.68, hrHi: 0.75, src: 'CT.gov NCT00412984 results. cox proportional hazard model.' },
          secondary_8: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.46, hrLo: 0.35, hrHi: 0.6, src: 'CT.gov NCT00412984 results. cox proportional hazard model.' },
          secondary_9: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.57, hrLo: 0.46, hrHi: 0.7, src: 'CT.gov NCT00412984 results. cox proportional hazard model.' },
          secondary_10: { tE: 0, tN: 10488, cE: 0, cN: 10488, hr: 0.74, hrLo: 0.65, hrHi: 0.83, src: 'CT.gov NCT00412984 results. cox proportional hazard model.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "ARISTOTLE: N=20,976. See CT.gov for full results."
      },
      { id: "An Efficacy and Safe", nctId: "NCT00403767", year: 2010, phase: "PHASE3",
        population: "Adults with non-valvular atrial fibrillation", nTotal: 14269, nTreatment: 7134, nControl: 7135,
        status: "Published", reference: "See CT.gov NCT00403767",
        outcomes: {
          mace: { tE: 0, tN: 7134, cE: 0, cN: 7135, hr: 1.03, hrLo: 0.96, hrHi: 1.11, src: 'CT.gov NCT00403767 results. cox proportional hazards model.' },
          secondary_1: { tE: 0, tN: 7134, cE: 0, cN: 7135, hr: 0.86, hrLo: 0.74, hrHi: 0.99, src: 'CT.gov NCT00403767 results. cox proportional hazards model.' },
          secondary_2: { tE: 0, tN: 7134, cE: 0, cN: 7135, hr: 0.85, hrLo: 0.74, hrHi: 0.96, src: 'CT.gov NCT00403767 results. cox proportional hazards model.' },
          secondary_3: { tE: 0, tN: 7134, cE: 0, cN: 7135, hr: 0.85, hrLo: 0.7, hrHi: 1.03, src: 'CT.gov NCT00403767 results. cox proportional hazards model.' },
          secondary_4: { tE: 0, tN: 7134, cE: 0, cN: 7135, hr: 0.23, hrLo: 0.09, hrHi: 0.61, src: 'CT.gov NCT00403767 results. cox proportional hazards model.' },
          secondary_5: { tE: 0, tN: 7134, cE: 0, cN: 7135, hr: 0.81, hrLo: 0.63, hrHi: 1.06, src: 'CT.gov NCT00403767 results. cox proportional hazards model.' },
          secondary_6: { tE: 0, tN: 7134, cE: 0, cN: 7135, hr: 0.89, hrLo: 0.73, hrHi: 1.1, src: 'CT.gov NCT00403767 results. cox proportional hazards model.' },
          secondary_7: { tE: 0, tN: 7134, cE: 0, cN: 7135, hr: 0.85, hrLo: 0.7, hrHi: 1.02, src: 'CT.gov NCT00403767 results. cox proportional hazards model.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "An Efficacy and Safe: N=14,269. See CT.gov for full results."
      },
      { id: "EngageAFTIMI48", nctId: "NCT00781391", year: 2013, phase: "PHASE3",
        population: "Adults with non-valvular atrial fibrillation", nTotal: 21105, nTreatment: 10552, nControl: 10553,
        status: "Published", reference: "See CT.gov NCT00781391",
        outcomes: {
          mace: { tE: 0, tN: 10552, cE: 0, cN: 10553, hr: 0.87, hrLo: 0.709, hrHi: 1.068, src: 'CT.gov NCT00781391 results. log rank.' },
          secondary_1: { tE: 0, tN: 10552, cE: 0, cN: 10553, hr: 0.87, hrLo: 0.786, hrHi: 0.959, src: 'CT.gov NCT00781391 results. log rank.' },
          secondary_2: { tE: 0, tN: 10552, cE: 0, cN: 10553, hr: 0.89, hrLo: 0.806, hrHi: 0.972, src: 'CT.gov NCT00781391 results. log rank.' },
          secondary_3: { tE: 0, tN: 10552, cE: 0, cN: 10553, hr: 0.9, hrLo: 0.823, hrHi: 0.981, src: 'CT.gov NCT00781391 results. log rank.' },
          secondary_4: { tE: 0, tN: 10552, cE: 0, cN: 10553, hr: 0.8, hrLo: 0.707, hrHi: 0.914, src: 'CT.gov NCT00781391 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "EngageAFTIMI48: N=21,105. See CT.gov for full results."
      },
      { id: "Randomized Evaluatio", nctId: "NCT00262600", year: 0, phase: "PHASE3",
        population: "Adults with non-valvular atrial fibrillation", nTotal: 18113, nTreatment: 9056, nControl: 9057,
        status: "Published", reference: "See CT.gov NCT00262600",
        outcomes: {
          mace: { tE: 0, tN: 9056, cE: 0, cN: 9057, hr: 0.9, hrLo: 0.74, hrHi: 1.1, src: 'CT.gov NCT00262600 results. regression, cox.' },
          secondary_1: { tE: 0, tN: 9056, cE: 0, cN: 9057, hr: 0.93, hrLo: 0.83, hrHi: 1.04, src: 'CT.gov NCT00262600 results. regression, cox.' },
          secondary_2: { tE: 0, tN: 9056, cE: 0, cN: 9057, hr: 0.98, hrLo: 0.87, hrHi: 1.11, src: 'CT.gov NCT00262600 results. regression, cox.' },
          secondary_3: { tE: 0, tN: 9056, cE: 0, cN: 9057, hr: 0.8, hrLo: 0.7, hrHi: 0.93, src: 'CT.gov NCT00262600 results. regression, cox.' },
          secondary_4: { tE: 0, tN: 9056, cE: 0, cN: 9057, hr: 0.3, hrLo: 0.19, hrHi: 0.45, src: 'CT.gov NCT00262600 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Randomized Evaluatio: N=18,113. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* DOACS — VENOUS THROMBOEMBOLISM */
  /* ============================================================ */
  doac_vte: {
    id: "doac_vte", name: "DOACs — Venous Thromboembolism", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with acute VTE (DVT or PE)",
      intervention: "DOAC",
      comparator: "Warfarin or LMWH",
      outcomes: [
        { id: "mace", name: "Recurrent VTE or VTE-related death", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(apixaban OR rivaroxaban OR edoxaban OR dabigatran) AND (venous thromboembolism OR pulmonary embolism OR deep vein thrombosis) AND (COMPLETED)",
      pubmed: "(apixaban OR rivaroxaban OR edoxaban OR dabigatran) AND (venous thromboembolism OR pulmonary embolism OR deep vein thrombosis) AND (randomized controlled trial[pt])",
      openalex: "apixaban OR rivaroxaban OR edoxaban OR dabigatran AND venous thromboembolism OR pulmonary embolism OR deep vein thrombosis AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "DOAC vs Warfarin or LMWH", "Reports Recurrent VTE or VTE-related death"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "Efficacy and Safety", nctId: "NCT00643201", year: 2013, phase: "PHASE3",
        population: "Adults with acute VTE (DVT or PE)", nTotal: 5614, nTreatment: 2807, nControl: 2807,
        status: "Published", reference: "See CT.gov NCT00643201",
        outcomes: {
          mace: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.839, hrLo: 0.5965, hrHi: 1.1802, src: 'CT.gov NCT00643201 results. yanagawa-tango-hiejima.' },
          secondary_1: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.8151, hrLo: 0.6146, hrHi: 1.0812, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_2: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.7994, hrLo: 0.5737, hrHi: 1.1137, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_3: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.6236, hrLo: 0.4682, hrHi: 0.8306, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_4: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.5532, hrLo: 0.4658, hrHi: 0.6569, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_5: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.6347, hrLo: 0.3735, hrHi: 1.0787, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_6: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 1.0935, hrLo: 0.6363, hrHi: 1.8793, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_7: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.7521, hrLo: 0.356, hrHi: 1.5889, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_8: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.6539, hrLo: 0.3419, hrHi: 1.2508, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_9: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.7934, hrLo: 0.5287, hrHi: 1.1906, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_10: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.307, hrLo: 0.1728, hrHi: 0.5452, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_11: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.441, hrLo: 0.3566, hrHi: 0.5453, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_12: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.4793, hrLo: 0.3815, hrHi: 0.6022, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_13: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.6182, hrLo: 0.5432, hrHi: 0.7034, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' },
          secondary_14: { tE: 0, tN: 2807, cE: 0, cN: 2807, hr: 0.5937, hrLo: 0.5318, hrHi: 0.6629, src: 'CT.gov NCT00643201 results. cochran-mantel-haenszel.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Efficacy and Safety: N=5,614. See CT.gov for full results."
      },
      { id: "Efficacy and Safety", nctId: "NCT00633893", year: 2012, phase: "PHASE3",
        population: "Adults with acute VTE (DVT or PE)", nTotal: 2711, nTreatment: 1355, nControl: 1356,
        status: "Published", reference: "See CT.gov NCT00633893",
        outcomes: {
          mace: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.2422, hrLo: 0.1476, hrHi: 0.3975, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_1: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.2891, hrLo: 0.1902, hrHi: 0.4395, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_2: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.2799, hrLo: 0.1844, hrHi: 0.4247, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_3: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.2615, hrLo: 0.1593, hrHi: 0.4292, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_4: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.6087, hrLo: 0.3653, hrHi: 1.0145, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_5: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.647, hrLo: 0.3543, hrHi: 1.1813, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_6: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.5794, hrLo: 0.3215, hrHi: 1.0443, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_7: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.6577, hrLo: 0.3874, hrHi: 1.1169, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_8: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 0.485, hrLo: 0.0891, hrHi: 2.6391, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_9: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 1.2027, hrLo: 0.6897, hrHi: 2.0975, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_10: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 1.2928, hrLo: 0.7158, hrHi: 2.3348, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_11: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 1.2579, hrLo: 0.9064, hrHi: 1.7457, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' },
          secondary_12: { tE: 0, tN: 1355, cE: 0, cN: 1356, hr: 1.2374, hrLo: 0.9276, hrHi: 1.6507, src: 'CT.gov NCT00633893 results. cochran-mantel-haenszel.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Efficacy and Safety: N=2,711. See CT.gov for full results."
      },
      { id: "Study to Assess the", nctId: "NCT01054820", year: 2010, phase: "PHASE4",
        population: "Adults with acute VTE (DVT or PE)", nTotal: 123, nTreatment: 61, nControl: 62,
        status: "Published", reference: "See CT.gov NCT01054820",
        outcomes: { mace: { tE: 0, tN: 61, cE: 0, cN: 62 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Study to Assess the: N=123. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* DUPILUMAB — ASTHMA/COPD */
  /* ============================================================ */
  dupilumab_asthma: {
    id: "dupilumab_asthma", name: "Dupilumab — Asthma/COPD", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with moderate-to-severe asthma or type 2 COPD",
      intervention: "Dupilumab (anti-IL-4Ra)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "Annualized exacerbation rate", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(dupilumab) AND (asthma OR COPD) AND (COMPLETED)",
      pubmed: "(dupilumab) AND (asthma OR COPD) AND (randomized controlled trial[pt])",
      openalex: "dupilumab AND asthma OR COPD AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Dupilumab (anti-IL-4Ra) vs Placebo", "Reports Annualized exacerbation rate"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "Evaluation of Dupilu", nctId: "NCT02414854", year: 2017, phase: "PHASE3",
        population: "Adults with moderate-to-severe asthma or type 2 COPD", nTotal: 1902, nTreatment: 951, nControl: 951,
        status: "Published", reference: "See CT.gov NCT02414854",
        outcomes: {
          mace: { tE: 0, tN: 951, cE: 0, cN: 951, hr: 0.13, hrLo: 0.08, hrHi: 0.18, src: 'CT.gov NCT02414854 results. mixed models analysis.' },
          secondary_1: { tE: 0, tN: 951, cE: 0, cN: 951, hr: 9.41, hrLo: 5.74, hrHi: 13.07, src: 'CT.gov NCT02414854 results. mixed models analysis.' },
          secondary_2: { tE: 0, tN: 951, cE: 0, cN: 951, hr: 0.402, hrLo: 0.307, hrHi: 0.526, src: 'CT.gov NCT02414854 results. negative binomial regression model.' },
          secondary_3: { tE: 0, tN: 951, cE: 0, cN: 951, hr: 0.15, hrLo: 0.09, hrHi: 0.21, src: 'CT.gov NCT02414854 results. mixed models analysis.' },
          secondary_4: { tE: 0, tN: 951, cE: 0, cN: 951, hr: 0.326, hrLo: 0.234, hrHi: 0.454, src: 'CT.gov NCT02414854 results. negative binomial regression model.' },
          secondary_5: { tE: 0, tN: 951, cE: 0, cN: 951, hr: 0.24, hrLo: 0.16, hrHi: 0.32, src: 'CT.gov NCT02414854 results. mixed models analysis.' },
          secondary_6: { tE: 0, tN: 951, cE: 0, cN: 951, hr: 0.834, hrLo: 0.608, hrHi: 1.144, src: 'CT.gov NCT02414854 results. negative binomial regression model.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Evaluation of Dupilu: N=1,902. See CT.gov for full results."
      },
      { id: "VENTURE", nctId: "NCT02528214", year: 2017, phase: "PHASE3",
        population: "Adults with moderate-to-severe asthma or type 2 COPD", nTotal: 210, nTreatment: 105, nControl: 105,
        status: "Published", reference: "See CT.gov NCT02528214",
        outcomes: {
          mace: { tE: 0, tN: 105, cE: 0, cN: 105, hr: 28.24, hrLo: 15.81, hrHi: 40.67, src: 'CT.gov NCT02528214 results. ancova.' },
          secondary_1: { tE: 0, tN: 105, cE: 0, cN: 105, hr: 3.98, hrLo: 2.06, hrHi: 7.67, src: 'CT.gov NCT02528214 results. regression, logistic.' },
          secondary_2: { tE: 0, tN: 105, cE: 0, cN: 105, hr: 4.48, hrLo: 2.39, hrHi: 8.39, src: 'CT.gov NCT02528214 results. regression, logistic.' },
          secondary_3: { tE: 0, tN: 105, cE: 0, cN: 105, hr: 2.57, hrLo: 1.4, hrHi: 4.73, src: 'CT.gov NCT02528214 results. regression, logistic.' },
          secondary_4: { tE: 0, tN: 105, cE: 0, cN: 105, hr: 2.74, hrLo: 1.47, hrHi: 5.1, src: 'CT.gov NCT02528214 results. regression, logistic.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "VENTURE: N=210. See CT.gov for full results."
      },
      { id: "BOREAS", nctId: "NCT03930732", year: 2023, phase: "PHASE3",
        population: "Adults with moderate-to-severe asthma or type 2 COPD", nTotal: 939, nTreatment: 469, nControl: 470,
        status: "Published", reference: "See CT.gov NCT03930732",
        outcomes: {
          mace: { tE: 0, tN: 469, cE: 0, cN: 470, hr: -0.324, hrLo: -0.508, hrHi: -0.14, src: 'CT.gov NCT03930732 results. negative binomial model.' },
          secondary_1: { tE: 0, tN: 469, cE: 0, cN: 470, hr: 0.083, hrLo: 0.042, hrHi: 0.125, src: 'CT.gov NCT03930732 results. mmrm model.' },
          secondary_2: { tE: 0, tN: 469, cE: 0, cN: 470, hr: 0.083, hrLo: 0.038, hrHi: 0.128, src: 'CT.gov NCT03930732 results. mmrm model.' },
          secondary_3: { tE: 0, tN: 469, cE: 0, cN: 470, hr: 0.124, hrLo: 0.045, hrHi: 0.203, src: 'CT.gov NCT03930732 results. mmrm model.' },
          secondary_4: { tE: 0, tN: 469, cE: 0, cN: 470, hr: 0.127, hrLo: 0.042, hrHi: 0.212, src: 'CT.gov NCT03930732 results. mmrm model.' },
          secondary_5: { tE: 0, tN: 469, cE: 0, cN: 470, hr: -3.363, hrLo: -5.459, hrHi: -1.266, src: 'CT.gov NCT03930732 results. mmrm model.' },
          secondary_6: { tE: 0, tN: 469, cE: 0, cN: 470, hr: 1.439, hrLo: 1.096, hrHi: 1.89, src: 'CT.gov NCT03930732 results. regression, logistic.' },
          secondary_7: { tE: 0, tN: 469, cE: 0, cN: 470, hr: -1.137, hrLo: -1.823, hrHi: -0.45, src: 'CT.gov NCT03930732 results. mmrm model.' },
          secondary_8: { tE: 0, tN: 469, cE: 0, cN: 470, hr: -0.418, hrLo: -0.728, hrHi: -0.109, src: 'CT.gov NCT03930732 results. negative binomial model.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "BOREAS: N=939. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* TEZEPELUMAB — SEVERE ASTHMA */
  /* ============================================================ */
  tezepelumab_asthma: {
    id: "tezepelumab_asthma", name: "Tezepelumab — Severe Asthma", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with severe uncontrolled asthma",
      intervention: "Tezepelumab (anti-TSLP)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "Annualized asthma exacerbation rate", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(tezepelumab) AND (asthma) AND (COMPLETED)",
      pubmed: "(tezepelumab) AND (asthma) AND (randomized controlled trial[pt])",
      openalex: "tezepelumab AND asthma AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Tezepelumab (anti-TSLP) vs Placebo", "Reports Annualized asthma exacerbation rate"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "NAVIGATOR", nctId: "NCT03347279", year: 2020, phase: "PHASE3",
        population: "Adults with severe uncontrolled asthma", nTotal: 1061, nTreatment: 530, nControl: 531,
        status: "Published", reference: "See CT.gov NCT03347279",
        outcomes: {
          mace: { tE: 0, tN: 530, cE: 0, cN: 531, hr: 0.59, hrLo: 0.46, hrHi: 0.75, src: 'CT.gov NCT03347279 results. negative binomial.' },
          secondary_1: { tE: 0, tN: 530, cE: 0, cN: 531, hr: 0.13, hrLo: 0.08, hrHi: 0.18, src: 'CT.gov NCT03347279 results. mixed models analysis.' },
          secondary_2: { tE: 0, tN: 530, cE: 0, cN: 531, hr: 0.33, hrLo: 0.2, hrHi: 0.47, src: 'CT.gov NCT03347279 results. mixed models analysis.' },
          secondary_3: { tE: 0, tN: 530, cE: 0, cN: 531, hr: -0.33, hrLo: -0.46, hrHi: -0.2, src: 'CT.gov NCT03347279 results. mixed models analysis.' },
          secondary_4: { tE: 0, tN: 530, cE: 0, cN: 531, hr: -0.11, hrLo: -0.19, hrHi: -0.04, src: 'CT.gov NCT03347279 results. mixed models analysis.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "NAVIGATOR: N=1,061. See CT.gov for full results."
      },
      { id: "DESTINATION", nctId: "NCT03706079", year: 2022, phase: "PHASE3",
        population: "Adults with severe uncontrolled asthma", nTotal: 951, nTreatment: 475, nControl: 476,
        status: "Published", reference: "See CT.gov NCT03706079",
        outcomes: {
          secondary_0: { tE: 0, tN: 475, cE: 0, cN: 476, hr: 0.42, hrLo: 0.35, hrHi: 0.51, src: 'CT.gov NCT03706079 results. .' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "DESTINATION: N=951. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* EMPAGLIFLOZIN — POST-MI */
  /* ============================================================ */
  empagliflozin_post_mi: {
    id: "empagliflozin_post_mi", name: "Empagliflozin — Post-MI", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults after acute MI",
      intervention: "Empagliflozin",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "HF hospitalization or CV death", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(empagliflozin) AND (myocardial infarction) AND (COMPLETED)",
      pubmed: "(empagliflozin) AND (myocardial infarction) AND (randomized controlled trial[pt])",
      openalex: "empagliflozin AND myocardial infarction AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Empagliflozin vs Placebo", "Reports HF hospitalization or CV death"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "EMPACT-MI", nctId: "NCT04509674", year: 2023, phase: "PHASE3",
        population: "Adults after acute MI", nTotal: 6522, nTreatment: 3261, nControl: 3261,
        status: "Published", reference: "See CT.gov NCT04509674",
        outcomes: {
          mace: { tE: 0, tN: 3261, cE: 0, cN: 3261, hr: 0.9, hrLo: 0.76, hrHi: 1.06, src: 'CT.gov NCT04509674 results. regression, cox.' },
          secondary_1: { tE: 0, tN: 3261, cE: 0, cN: 3261, hr: 0.87, hrLo: 0.68, hrHi: 1.1, src: 'CT.gov NCT04509674 results. negative binomial regression.' },
          secondary_2: { tE: 0, tN: 3261, cE: 0, cN: 3261, hr: 0.92, hrLo: 0.78, hrHi: 1.07, src: 'CT.gov NCT04509674 results. negative binomial regression.' },
          secondary_3: { tE: 0, tN: 3261, cE: 0, cN: 3261, hr: 0.87, hrLo: 0.7654, hrHi: 0.9978, src: 'CT.gov NCT04509674 results. negative binomial regression.' },
          secondary_4: { tE: 0, tN: 3261, cE: 0, cN: 3261, hr: 1.06, hrLo: 0.83, hrHi: 1.35, src: 'CT.gov NCT04509674 results. negative binomial regression.' },
          secondary_5: { tE: 0, tN: 3261, cE: 0, cN: 3261, hr: 1.03, hrLo: 0.81, hrHi: 1.31, src: 'CT.gov NCT04509674 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "EMPACT-MI: N=6,522. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* DAPAGLIFLOZIN — POST-MI */
  /* ============================================================ */
  dapagliflozin_post_mi: {
    id: "dapagliflozin_post_mi", name: "Dapagliflozin — Post-MI", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults after acute MI without diabetes",
      intervention: "Dapagliflozin",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "CV death or HF hospitalization", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(dapagliflozin) AND (myocardial infarction) AND (COMPLETED)",
      pubmed: "(dapagliflozin) AND (myocardial infarction) AND (randomized controlled trial[pt])",
      openalex: "dapagliflozin AND myocardial infarction AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Dapagliflozin vs Placebo", "Reports CV death or HF hospitalization"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "DAPA-MI", nctId: "NCT04564742", year: 2023, phase: "PHASE3",
        population: "Adults after acute MI without diabetes", nTotal: 4017, nTreatment: 2008, nControl: 2009,
        status: "Published", reference: "See CT.gov NCT04564742",
        outcomes: {
          mace: { tE: 0, tN: 2008, cE: 0, cN: 2009, hr: 1.34, hrLo: 1.2, hrHi: 1.5, src: 'CT.gov NCT04564742 results. win ratio analysis.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "DAPA-MI: N=4,017. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* TICAGRELOR — ACS/CAD */
  /* ============================================================ */
  ticagrelor_acs: {
    id: "ticagrelor_acs", name: "Ticagrelor — ACS/CAD", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with ACS or stable CAD",
      intervention: "Ticagrelor",
      comparator: "Clopidogrel or aspirin",
      outcomes: [
        { id: "mace", name: "CV death, MI, or stroke", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(ticagrelor) AND (acute coronary syndrome OR coronary artery disease) AND (COMPLETED)",
      pubmed: "(ticagrelor) AND (acute coronary syndrome OR coronary artery disease) AND (randomized controlled trial[pt])",
      openalex: "ticagrelor AND acute coronary syndrome OR coronary artery disease AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Ticagrelor vs Clopidogrel or aspirin", "Reports CV death, MI, or stroke"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "PLATO", nctId: "NCT00391872", year: 2009, phase: "PHASE3",
        population: "Adults with ACS or stable CAD", nTotal: 18624, nTreatment: 9312, nControl: 9312,
        status: "Published", reference: "See CT.gov NCT00391872",
        outcomes: { mace: { tE: 0, tN: 9312, cE: 0, cN: 9312 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "PLATO: N=18,624. See CT.gov for full results."
      },
      { id: "THEMIS", nctId: "NCT01991795", year: 2019, phase: "PHASE3",
        population: "Adults with ACS or stable CAD", nTotal: 19271, nTreatment: 9635, nControl: 9636,
        status: "Published", reference: "See CT.gov NCT01991795",
        outcomes: {
          mace: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 0.9, hrLo: 0.81, hrHi: 0.99, src: 'CT.gov NCT01991795 results. regression, cox.' },
          secondary_1: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 1.02, hrLo: 0.88, hrHi: 1.18, src: 'CT.gov NCT01991795 results. regression, cox.' },
          secondary_2: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 0.84, hrLo: 0.71, hrHi: 0.98, src: 'CT.gov NCT01991795 results. regression, cox.' },
          secondary_3: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 0.8, hrLo: 0.64, hrHi: 0.99, src: 'CT.gov NCT01991795 results. regression, cox.' },
          secondary_4: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 0.98, hrLo: 0.87, hrHi: 1.1, src: 'CT.gov NCT01991795 results. regression, cox.' },
          secondary_5: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 2.32, hrLo: 1.82, hrHi: 2.94, src: 'CT.gov NCT01991795 results. regression, cox.' },
          secondary_6: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 2.49, hrLo: 2.02, hrHi: 3.07, src: 'CT.gov NCT01991795 results. regression, cox.' },
          secondary_7: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 2.41, hrLo: 1.98, hrHi: 2.93, src: 'CT.gov NCT01991795 results. regression, cox.' },
          secondary_8: { tE: 0, tN: 9635, cE: 0, cN: 9636, hr: 4.04, hrLo: 3.32, hrHi: 4.92, src: 'CT.gov NCT01991795 results. regression, cox.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "THEMIS: N=19,271. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* ANAKINRA — RECURRENT PERICARDITIS */
  /* ============================================================ */
  anakinra_pericarditis: {
    id: "anakinra_pericarditis", name: "Anakinra — Recurrent Pericarditis", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with recurrent pericarditis",
      intervention: "Anakinra (IL-1 receptor antagonist)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "Pericarditis recurrence", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(anakinra) AND (pericarditis) AND (COMPLETED)",
      pubmed: "(anakinra) AND (pericarditis) AND (randomized controlled trial[pt])",
      openalex: "anakinra AND pericarditis AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Anakinra (IL-1 receptor antagonist) vs Placebo", "Reports Pericarditis recurrence"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "RHAPSODY", nctId: "NCT03737110", year: 2022, phase: "PHASE3",
        population: "Adults with recurrent pericarditis", nTotal: 86, nTreatment: 43, nControl: 43,
        status: "Published", reference: "See CT.gov NCT03737110",
        outcomes: {
          mace: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 0.04, hrLo: 0.01, hrHi: 0.18, src: 'CT.gov NCT03737110 results. log rank.' },
          secondary_1: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 12.727, hrLo: 2.438, hrHi: 66.428, src: 'CT.gov NCT03737110 results. cochran-mantel-haenszel.' },
          secondary_2: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 51.2, hrLo: 34.5, hrHi: 68.0, src: 'CT.gov NCT03737110 results. ancova.' },
          secondary_3: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 10.0, hrLo: 2.136, hrHi: 46.826, src: 'CT.gov NCT03737110 results. cochran-mantel-haenszel.' },
          secondary_4: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 8.37, hrLo: 1.317, hrHi: 53.188, src: 'CT.gov NCT03737110 results. cochran-mantel-haenszel.' },
          secondary_5: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 10.906, hrLo: 3.051, hrHi: 38.981, src: 'CT.gov NCT03737110 results. cochran-mantel-haenszel.' },
          secondary_6: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 51.9, hrLo: 33.8, hrHi: 70.1, src: 'CT.gov NCT03737110 results. ancova.' },
          secondary_7: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 40.5, hrLo: 25.3, hrHi: 55.8, src: 'CT.gov NCT03737110 results. ancova.' },
          secondary_8: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 30.522, hrLo: 4.262, hrHi: 218.552, src: 'CT.gov NCT03737110 results. cochran-mantel-haenszel.' },
          secondary_9: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 14.432, hrLo: 3.439, hrHi: 60.574, src: 'CT.gov NCT03737110 results. cochran-mantel-haenszel.' },
          secondary_10: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 75.7, hrLo: 56.8, hrHi: 94.6, src: 'CT.gov NCT03737110 results. normal approximation.' },
          secondary_11: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 0.13, hrLo: 0.05, hrHi: 0.32, src: 'CT.gov NCT03737110 results. log rank.' },
          secondary_12: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 0.07, hrLo: 0.02, hrHi: 0.22, src: 'CT.gov NCT03737110 results. log rank.' },
          secondary_13: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 0.74, hrLo: 0.12, hrHi: 4.46, src: 'CT.gov NCT03737110 results. log rank.' },
          secondary_14: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 0.36, hrLo: 0.07, hrHi: 1.87, src: 'CT.gov NCT03737110 results. log rank.' },
          secondary_15: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 0.0, hrLo: null, hrHi: null, src: 'CT.gov NCT03737110 results. log rank.' },
          secondary_16: { tE: 0, tN: 43, cE: 0, cN: 43, hr: 0.015, hrLo: 0.002, hrHi: 0.108, src: 'CT.gov NCT03737110 results. cochran-mantel-haenszel.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "RHAPSODY: N=86. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* CATHETER ABLATION — AF + HF */
  /* ============================================================ */
  catheter_ablation_af: {
    id: "catheter_ablation_af", name: "Catheter Ablation — AF + HF", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with AF and HF",
      intervention: "Catheter ablation of AF",
      comparator: "Medical rate/rhythm control",
      outcomes: [
        { id: "mace", name: "All-cause mortality or HF hospitalization", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(catheter ablation) AND (atrial fibrillation AND heart failure) AND (COMPLETED)",
      pubmed: "(catheter ablation) AND (atrial fibrillation AND heart failure) AND (randomized controlled trial[pt])",
      openalex: "catheter ablation AND atrial fibrillation AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Catheter ablation of AF vs Medical rate/rhythm control", "Reports All-cause mortality or HF hospitalization"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "CASTLE-AF", nctId: "NCT00643188", year: 2017, phase: "PHASE4",
        population: "Adults with AF and HF", nTotal: 398, nTreatment: 199, nControl: 199,
        status: "Published", reference: "See CT.gov NCT00643188",
        outcomes: { mace: { tE: 0, tN: 199, cE: 0, cN: 199 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "CASTLE-AF: N=398. See CT.gov for full results."
      },
      { id: "AuTop", nctId: "NCT02288832", year: 2022, phase: "PHASE2, PHASE3",
        population: "Adults with AF and HF", nTotal: 6800, nTreatment: 3400, nControl: 3400,
        status: "Published", reference: "See CT.gov NCT02288832",
        outcomes: { mace: { tE: 0, tN: 3400, cE: 0, cN: 3400 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "AuTop: N=6,800. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* SOTATERCEPT — PULMONARY HYPERTENSION */
  /* ============================================================ */
  sotatercept_pah: {
    id: "sotatercept_pah", name: "Sotatercept — Pulmonary Hypertension", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults with PAH on background therapy",
      intervention: "Sotatercept (activin signaling inhibitor)",
      comparator: "Placebo",
      outcomes: [
        { id: "mace", name: "6-minute walk distance change", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(sotatercept) AND (pulmonary arterial hypertension) AND (COMPLETED)",
      pubmed: "(sotatercept) AND (pulmonary arterial hypertension) AND (randomized controlled trial[pt])",
      openalex: "sotatercept AND pulmonary arterial hypertension AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Sotatercept (activin signaling inhibitor) vs Placebo", "Reports 6-minute walk distance change"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "A Study of Sotaterce", nctId: "NCT04576988", year: 2022, phase: "PHASE3",
        population: "Adults with PAH on background therapy", nTotal: 324, nTreatment: 162, nControl: 162,
        status: "Published", reference: "See CT.gov NCT04576988",
        outcomes: {
          mace: { tE: 0, tN: 162, cE: 0, cN: 162, hr: 40.8, hrLo: 27.53, hrHi: 54.14, src: 'CT.gov NCT04576988 results. aligned rank stratified wilcoxon (arsw).' },
          secondary_1: { tE: 0, tN: 162, cE: 0, cN: 162, hr: -234.6, hrLo: -288.37, hrHi: -180.75, src: 'CT.gov NCT04576988 results. arsw test.' },
          secondary_2: { tE: 0, tN: 162, cE: 0, cN: 162, hr: -441.6, hrLo: -573.54, hrHi: -309.61, src: 'CT.gov NCT04576988 results. arsw test.' },
          secondary_3: { tE: 0, tN: 162, cE: 0, cN: 162, hr: 0.163, hrLo: 0.076, hrHi: 0.347, src: 'CT.gov NCT04576988 results. log rank.' },
          secondary_4: { tE: 0, tN: 162, cE: 0, cN: 162, hr: -0.26, hrLo: -0.49, hrHi: -0.04, src: 'CT.gov NCT04576988 results. arsw test.' },
          secondary_5: { tE: 0, tN: 162, cE: 0, cN: 162, hr: -0.13, hrLo: -0.256, hrHi: -0.014, src: 'CT.gov NCT04576988 results. arsw test.' },
          secondary_6: { tE: 0, tN: 162, cE: 0, cN: 162, hr: -0.16, hrLo: -0.399, hrHi: 0.084, src: 'CT.gov NCT04576988 results. arsw test.' }
        },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "A Study of Sotaterce: N=324. See CT.gov for full results."
      },
      { id: "HYPERION", nctId: "NCT04811092", year: 2025, phase: "PHASE3",
        population: "Adults with PAH on background therapy", nTotal: 321, nTreatment: 160, nControl: 161,
        status: "Published", reference: "See CT.gov NCT04811092",
        outcomes: { mace: { tE: 0, tN: 160, cE: 0, cN: 161 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "HYPERION: N=321. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* DEXRAZOXANE — CARDIOPROTECTION */
  /* ============================================================ */
  dexrazoxane_cardio: {
    id: "dexrazoxane_cardio", name: "Dexrazoxane — Cardioprotection", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Cancer patients receiving anthracycline chemotherapy",
      intervention: "Dexrazoxane or beta-blocker cardioprotection",
      comparator: "Standard care",
      outcomes: [
        { id: "mace", name: "LVEF decline or cardiac events", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(dexrazoxane OR cardioprotection AND anthracycline) AND (cancer AND cardiotoxicity) AND (COMPLETED)",
      pubmed: "(dexrazoxane OR cardioprotection AND anthracycline) AND (cancer AND cardiotoxicity) AND (randomized controlled trial[pt])",
      openalex: "dexrazoxane OR cardioprotection AND anthracycline AND cancer AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Dexrazoxane or beta-blocker cardioprotection vs Standard care", "Reports LVEF decline or cardiac events"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "Ceccy", nctId: "NCT01724450", year: 2017, phase: "PHASE3",
        population: "Cancer patients receiving anthracycline chemotherapy", nTotal: 200, nTreatment: 100, nControl: 100,
        status: "Published", reference: "See CT.gov NCT01724450",
        outcomes: { mace: { tE: 0, tN: 100, cE: 0, cN: 100 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Ceccy: N=200. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

  /* ============================================================ */
  /* CLOSED-LOOP INSULIN — TYPE 1 DIABETES */
  /* ============================================================ */
  closed_loop_t1dm: {
    id: "closed_loop_t1dm", name: "Closed-Loop Insulin — Type 1 Diabetes", version: "1.0.0", lastUpdated: "2026-03-14",
    pico: {
      population: "Adults or adolescents with T1DM",
      intervention: "Closed-loop insulin delivery system",
      comparator: "Open-loop pump or MDI",
      outcomes: [
        { id: "mace", name: "Time in range (70-180 mg/dL)", primary: true },
        { id: "acm", name: "All-Cause Mortality", primary: false },
      ]
    },
    searchStrategy: {
      ctgov: "(closed loop insulin OR artificial pancreas OR hybrid closed loop) AND (type 1 diabetes) AND (COMPLETED)",
      pubmed: "(closed loop insulin OR artificial pancreas OR hybrid closed loop) AND (type 1 diabetes) AND (randomized controlled trial[pt])",
      openalex: "closed loop insulin OR artificial pancreas OR hybrid closed loop AND type 1 diabetes AND randomized"
    },
    subgroups: {},
    eligibility: { include: ["Phase III RCT", "Closed-loop insulin delivery system vs Open-loop pump or MDI", "Reports Time in range"], exclude: ["Phase I/II", "Non-randomized", "Pediatric"] },
    trials: [
      { id: "DCLP3", nctId: "NCT03563313", year: 2019, phase: "NA",
        population: "Adults or adolescents with T1DM", nTotal: 168, nTreatment: 84, nControl: 84,
        status: "Published", reference: "See CT.gov NCT03563313",
        outcomes: { mace: { tE: 0, tN: 84, cE: 0, cN: 84 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "DCLP3: N=168. See CT.gov for full results."
      },
      { id: "Preterm Functional E", nctId: "NCT04531566", year: 2022, phase: "NA",
        population: "Adults or adolescents with T1DM", nTotal: 50, nTreatment: 25, nControl: 25,
        status: "Published", reference: "See CT.gov NCT04531566",
        outcomes: { mace: { tE: 0, tN: 25, cE: 0, cN: 25 } },
        rob: { domains: ["low","low","low","low","low"], overall: "low", text: "Phase III RCT." },
        evidenceText: "Preterm Functional E: N=50. See CT.gov for full results."
      },
    ],
    ghostProtocols: [], ongoingTrials: [], publishedBenchmarks: []
  },

