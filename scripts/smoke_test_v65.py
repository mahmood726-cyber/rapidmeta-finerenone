"""
Smoke test the Cochrane v6.5 stat-card pipeline across a sample of dashboards.

For each dashboard, opens it via Playwright, calls AnalysisEngine.run() (or
the DTA equivalent), reads the new stat cards (res-tau2-ci, res-i2,
res-hksj, res-pi, chip-robme), and reports any console errors.

Note: this script is a TEMPLATE / reference. Run via the playwright MCP
tool from inside Claude rather than as a standalone script, since the
MCP playwright integration handles the browser lifecycle.

Coverage list:
  Pairwise binary: IL23_PSORIASIS, DUPILUMAB_AD, JAKI_AD
  Pairwise continuous: FARICIMAB_NAMD, ALDO_SYNTHASE_NMA, AFLIBERCEPT_HD
  Pairwise HR: DOAC_AF, GLP1_CVOT, COLCHICINE_CVD
  NMA: ALOPECIA_JAKI_NMA, ANTIVEGF_NAMD_NMA, ATOPIC_DERM_NMA
  DTA: COVID_ANTIGEN_DTA, DDIMER_PE_DTA, GENEXPERT_ULTRA_TB_DTA,
       MPMRI_PROSTATE_DTA, PTAU217_AD_DTA, HSCTN_NSTEMI_DTA

Pass criteria (per dashboard):
  - 0 console errors (404s for r_validation_log_*.json and favicon.ico
    are tolerated)
  - res-tau2-ci populated with finite values OR 'N/A (k<2)'
  - res-hksj populated
  - chip-robme shows one of: low/some/high/manual verdict
"""
COVERAGE = {
    'pairwise_binary': ['IL23_PSORIASIS', 'DUPILUMAB_AD', 'JAKI_AD'],
    'pairwise_continuous': ['FARICIMAB_NAMD', 'ALDO_SYNTHASE_NMA', 'AFLIBERCEPT_HD'],
    'pairwise_hr': ['DOAC_AF', 'GLP1_CVOT', 'COLCHICINE_CVD'],
    'nma': ['ALOPECIA_JAKI_NMA', 'ANTIVEGF_NAMD_NMA', 'ATOPIC_DERM_NMA'],
    'dta': [
        'COVID_ANTIGEN_DTA', 'DDIMER_PE_DTA', 'GENEXPERT_ULTRA_TB_DTA',
        'MPMRI_PROSTATE_DTA', 'PTAU217_AD_DTA', 'HSCTN_NSTEMI_DTA',
    ],
}

if __name__ == '__main__':
    print("This script is a coverage manifest.")
    print("Use the playwright MCP tool to step through the COVERAGE dict.")
    for kind, files in COVERAGE.items():
        print(f"  {kind}: {len(files)} dashboards")
        for f in files:
            print(f"    - {f}_REVIEW.html")
