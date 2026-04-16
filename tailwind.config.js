/** Tailwind build config for Finrenone shipped HTML.
 *  Scans all non-backup HTML at repo root plus e156-submission/assets.
 *  Output: tailwind.min.css (replaces cdn.tailwindcss.com runtime compile).
 */
module.exports = {
  content: [
    './LivingMeta.html',
    './META_DASHBOARD.html',
    './AutoManuscript.html',
    './FINERENONE_REVIEW.html',
    './SGLT2_HF_REVIEW.html',
    './GLP1_CVOT_REVIEW.html',
    './COLCHICINE_CVD_REVIEW.html',
    './ABLATION_AF_REVIEW.html',
    './ARNI_HF_REVIEW.html',
    './ATTR_CM_REVIEW.html',
    './BEMPEDOIC_ACID_REVIEW.html',
    './DOAC_CANCER_VTE_REVIEW.html',
    './INCRETIN_HFpEF_REVIEW.html',
    './INTENSIVE_BP_REVIEW.html',
    './IV_IRON_HF_REVIEW.html',
    './LIPID_HUB_REVIEW.html',
    './MAVACAMTEN_HCM_REVIEW.html',
    './PCSK9_REVIEW.html',
    './AutoGRADE.html',
    './e156-submission/assets/*.html',
    '../PFA_AF_LivingMeta/*.html',
    '../Tricuspid_TEER_LivingMeta/*.html',
    '../LivingMeta_Watchman_Amulet/*.html'
  ],
  theme: { extend: {} },
  plugins: []
};
