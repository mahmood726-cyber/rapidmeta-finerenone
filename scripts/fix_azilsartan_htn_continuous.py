#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rebuild AZILSARTAN_HTN_AUTO_FULL_REVIEW.html as a CONTINUOUS-outcome
(generic inverse-variance mean-difference) review, split into estimands.

THE DEFECT
----------
Blood-pressure change is a continuous outcome in mmHg.  The app encoded it as
a 2x2 event table and pooled a RISK RATIO of 0.98 (0.94-1.03) over integers
that have no registry provenance at all:

    NCT01033071   312/355 vs 317/352
    NCT00818883   101/303 vs 104/306
    NCT00591578   183/327 vs 195/329
    NCT00846365   224/372 vs 204/357

The DENOMINATORS are the real randomised counts of the FIRST TWO registry arms.
The NUMERATORS appear nowhere in the posted results of any of the four studies
(verified by exhaustive scan of every integer in each resultsSection).

Root causes fixed here:

  A2  ContinuousMDEngine exists and is correct, but its dispatch reads
          allOutcomes.find(x => x.shortLabel === outcomeKey)
      and the page runs with outcomeKey === "default", for which that lookup
      always returns undefined.  The continuous engine could therefore never
      fire on this page regardless of the data.  Compounding it, the extraction
      recorded estimandType:"MD" while setting type:"PRIMARY", and the dispatch
      tests type === "CONTINUOUS".  Two independent blockers, so the pool fell
      through to the 2x2 RR path over the fabricated counts.
  A3  sanitizeEffectMeasure()'s vocabulary is ["AUTO","HR","RR","OR"] -- no
      continuous member, so no code path could ever say "MD".
  A4  resolveEffectMeasure() falls through to "RR": trialHasPublishedHR()
      requires hrUCI > 0 and these mean differences are negative.
  A6  Wrong comparator arms.  The data layer took registry arms 1 and 2.  In
      three of the four studies the randomised control is arm 3.

Usage:  python scripts/fix_azilsartan_htn_continuous.py [--check]
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "AZILSARTAN_HTN_AUTO_FULL_REVIEW.html")
PRISMA = os.path.join(ROOT, "vendor", "prisma-flow.js")

CHECK_ONLY = "--check" in sys.argv

applied, skipped, failed = [], [], []


def edit(text, fid, desc, old, new, expect=1, marker=None):
    """Anchored replacement; `marker` decides idempotency when set."""
    if marker is not None:
        if marker in text:
            skipped.append((fid, desc))
            return text
    elif new in text and old not in text:
        skipped.append((fid, desc))
        return text
    n = text.count(old)
    if n != expect:
        failed.append((fid, desc, "anchor count %d != %d" % (n, expect)))
        return text
    applied.append((fid, desc))
    return text.replace(old, new)


h = io.open(APP, encoding="utf-8").read()
orig_h = h

# ===========================================================================
# STAGE 1 -- THE DATA LAYER
#
# Every number below is the ClinicalTrials.gov posted result, cross-checked
# against the primary publication.  For each study the registry supplies an
# ANCOVA adjusted mean difference with a 95% CI against the CORRECT randomised
# comparator; SE = (upper - lower) / (2 * 1.959964).
#
# Cross-check performed before writing these values -- difference of the
# arm-level LS means reproduces the registry ANCOVA MD, and the independent-sum
# SE reproduces the CI-derived SE to within 0.8% in all four studies:
#
#   NCT00846365 Wk8   -37.6 - (-31.5) = -6.10   MD -6.1   SEind/SEci = 1.0063
#   NCT01033071 Wk12  -42.5 - (-37.1) = -5.40   MD -5.3   SEind/SEci = 0.9917
#   NCT00591578 Wk24  -14.93 - (-11.29) = -3.64 MD -3.64  SEind/SEci = 0.9986
#   NCT00818883 Wk6   -35.1 - (-29.5) = -5.60   MD -5.6   SEind/SEci = 1.0009
#
# That cross-check also settles a registry data-entry error: NCT00846365 labels
# its primary-outcome dispersion "Standard Deviation", but 0.83 mmHg cannot be
# an SD of a ~38 mmHg change in n=372.  The ratio above confirms these are
# standard errors, as the sibling outcomes in the same record are labelled.
# Nothing here depends on that judgement: every SE is derived from the
# registry's own published 95% CI, not from the arm-level dispersion.
#
# ESTIMANDS.  The four studies do not answer one question and are not pooled
# as though they did:
#
#   A  azilsartan/chlorthalidone FDC vs olmesartan/HCTZ FDC   (k=2, pooled)
#   B  azilsartan monotherapy vs valsartan 320 mg             (k=1, not pooled)
#   C  chlorthalidone vs HCTZ on azilsartan 40 mg background  (k=1, not pooled,
#      and not an azilsartan effect at all -- both arms receive azilsartan)
#
# Estimand A is harmonised at WEEK 8: it is NCT00846365's registered primary
# timepoint, and NCT01033071 posts Week 8 as a secondary outcome, so no
# extrapolation is needed.  NCT01033071's Week-8 contrast is the difference of
# the posted Week-8 LS means (-39.1 vs -33.5) with SE = sqrt(0.78^2 + 0.77^2);
# that treats the two arm estimates as independent, which the Week-12 check
# above shows is accurate to under 1%.
#
# MULTI-ARM.  Both Estimand-A studies randomise TWO azilsartan/chlorthalidone
# arms against ONE shared olmesartan/HCTZ arm.  Pooling both contrasts would
# double-count that control arm, so the prespecified contrast is the LOWER-dose
# regimen and the higher-dose regimen is reported as a labelled sensitivity
# analysis -- never added to the same pool.
# ===========================================================================

OLD_DATA_START = 'realData:{NCT00846365:{name:"NCT00846365",pmid:"29334491"'
_ALREADY = 'estimand:"A"' in h
if _ALREADY:
    OLD_DATA = None
else:
    _i = h.find(OLD_DATA_START)
    _j = h.find("},async init(){", _i)
    if _i == -1 or _j == -1:
        failed.append(("A1", "realData block", "block boundaries not found"))
        OLD_DATA = None
    else:
        OLD_DATA = h[_i:_j + 1]

ROB = '["low","low","some-concerns","low","some-concerns"]'
ROBSRC = (
    'robSource:"Registry-derived default from the ClinicalTrials.gov design record '
    '(allocation RANDOMIZED, masking QUADRUPLE). NOT a human RoB-2 assessment: '
    'no reviewer has assessed any domain for this study."'
)

NEW_DATA = (
    'realData:{'
    # ---------------- Estimand A, study 1 ----------------
    'NCT00846365:{name:"Cushman 2018 (AZL-M/CTD vs OLM/HCTZ)",pmid:"29334491",'
    'doi:"10.1097/HJH.0000000000001647",phase:"III",year:2018,'
    'tE:null,cE:null,tN:372,cN:356,md:-6.1,se:1.1735,estimand:"A",'
    'group:"Estimand A - azilsartan medoxomil/chlorthalidone FDC vs olmesartan/HCTZ FDC",'
    'allOutcomes:[{shortLabel:"AZLCTD_vs_OLMHCTZ_SBP",'
    'title:"Change from baseline to Week 8 in trough, sitting, clinic systolic BP - '
    'azilsartan medoxomil/chlorthalidone 20-40/12.5-25 mg vs olmesartan medoxomil/HCTZ '
    '20-40/12.5-25 mg (registered PRIMARY endpoint, exact timepoint match)",'
    'type:"CONTINUOUS",estimandType:"MD",md:-6.1,se:1.1735,nT:372,nC:356,matchScore:100}],'
    'rob:' + ROB + ',' + ROBSRC + ','
    'snippet:"NCT00846365 (Cushman 2018, J Hypertens 36:947-956). Registered primary endpoint: '
    'change from baseline to Week 8 in trough sitting clinic SBP. Posted ANCOVA adjusted mean '
    'difference, azilsartan/chlorthalidone 20-40/12.5-25 mg vs olmesartan/HCTZ 20-40/12.5-25 mg: '
    '-6.1 mmHg (95% CI -8.4 to -3.8), p<0.001. Arm LS means -37.6 / -38.2 / -31.5 mmHg. '
    'Higher-dose arm (40-80/12.5-25 mg) vs the same comparator: -6.7 (-9.1 to -4.4) - reported '
    'as sensitivity only, never pooled with the lower-dose contrast (shared control arm).",'
    'sourceUrl:"https://clinicaltrials.gov/study/NCT00846365",'
    'ctgovUrl:"https://clinicaltrials.gov/study/NCT00846365",evidence:[]},'
    # ---------------- Estimand C ----------------
    'NCT00818883:{name:"Bakris 2012 (chlorthalidone vs HCTZ)",pmid:"22939358",'
    'doi:"10.1016/j.amjmed.2012.05.023",phase:"III",year:2012,'
    'tE:null,cE:null,tN:303,cN:306,md:-5.6,se:1.3776,estimand:"C",separateEstimand:!0,'
    'group:"Estimand C - chlorthalidone vs hydrochlorothiazide, azilsartan 40 mg in BOTH arms",'
    'allOutcomes:[{shortLabel:"CTD_vs_HCTZ_SBP",'
    'title:"Change from baseline to Week 6 in trough, sitting, clinic systolic BP - '
    'azilsartan medoxomil 40 mg/chlorthalidone vs azilsartan medoxomil 40 mg + HCTZ '
    '(registered PRIMARY endpoint analysis)",'
    'type:"CONTINUOUS",estimandType:"MD",md:-5.6,se:1.3776,nT:303,nC:306,matchScore:100}],'
    'rob:' + ROB + ',' + ROBSRC + ','
    'snippet:"NCT00818883 (Bakris 2012, Am J Med 125:1229.e1-e10). BOTH randomised arms receive '
    'azilsartan medoxomil 40 mg; the randomised contrast is the diuretic partner, chlorthalidone '
    'vs hydrochlorothiazide. This is NOT an azilsartan effect and is not pooled with Estimand A. '
    'Posted ANCOVA adjusted mean difference at the Week 6 primary analysis: -5.6 mmHg '
    '(95% CI -8.3 to -2.9), p<0.001; arm LS means -35.1 vs -29.5. Week 10: -5.0 (-7.5 to -2.5), '
    'arm LS means -37.8 vs -32.8.",'
    'sourceUrl:"https://clinicaltrials.gov/study/NCT00818883",'
    'ctgovUrl:"https://clinicaltrials.gov/study/NCT00818883",evidence:[]},'
    # ---------------- Estimand A, study 2 ----------------
    'NCT01033071:{name:"Cushman 2012 (AZL-M/CTD vs OLM/HCTZ)",pmid:"22710649",'
    'doi:"10.1161/HYPERTENSIONAHA.111.188284",phase:"III",year:2012,'
    'tE:null,cE:null,tN:355,cN:364,md:-5.6,se:1.096,estimand:"A",'
    'group:"Estimand A - azilsartan medoxomil/chlorthalidone FDC vs olmesartan/HCTZ FDC",'
    'allOutcomes:[{shortLabel:"AZLCTD_vs_OLMHCTZ_SBP",'
    'title:"Change from baseline to Week 8 in trough, sitting, clinic systolic BP - '
    'azilsartan medoxomil/chlorthalidone 20-40/12.5-25 mg vs olmesartan medoxomil/HCTZ '
    '20-40/12.5-25 mg (registered SECONDARY timepoint, used to harmonise with the Week 8 '
    'primary of NCT00846365; this study\'s own primary is Week 12)",'
    'type:"CONTINUOUS",estimandType:"MD",md:-5.6,se:1.096,nT:355,nC:364,matchScore:95}],'
    'rob:' + ROB + ',' + ROBSRC + ','
    'snippet:"NCT01033071 (Cushman 2012, Hypertension 60:310-318). Registered PRIMARY endpoint is '
    'Week 12, not Week 8. Week 12 posted ANCOVA adjusted mean difference vs olmesartan/HCTZ: '
    '-5.3 mmHg (95% CI -7.6 to -3.1); arm LS means -42.5 / -44.0 / -37.1. For the Week 8 '
    'harmonised analysis the contrast is the difference of the posted Week 8 secondary LS means '
    '(-39.1 vs -33.5 mmHg) = -5.6 mmHg, SE sqrt(0.78^2+0.77^2) = 1.096, 95% CI -7.75 to -3.45. '
    'Higher-dose arm at Week 8: -5.9 mmHg - sensitivity only, never pooled with the lower-dose '
    'contrast (shared control arm).",'
    'sourceUrl:"https://clinicaltrials.gov/study/NCT01033071",'
    'ctgovUrl:"https://clinicaltrials.gov/study/NCT01033071",evidence:[]},'
    # ---------------- Estimand B ----------------
    'NCT00591578:{name:"Sica 2011 (azilsartan vs valsartan)",pmid:"21762358",'
    'doi:"10.1111/j.1751-7176.2011.00482.x",phase:"III",year:2011,'
    'tE:null,cE:null,tN:327,cN:328,md:-3.64,se:0.9949,estimand:"B",separateEstimand:!0,'
    'group:"Estimand B - azilsartan medoxomil monotherapy vs valsartan 320 mg monotherapy",'
    'allOutcomes:[{shortLabel:"AZL_vs_VAL_ABPM",'
    'title:"Change from baseline to Week 24 in 24-hour mean AMBULATORY systolic BP - '
    'azilsartan medoxomil 40 mg vs valsartan 320 mg (registered PRIMARY endpoint)",'
    'type:"CONTINUOUS",estimandType:"MD",md:-3.64,se:0.9949,nT:327,nC:328,matchScore:100}],'
    'rob:' + ROB + ',' + ROBSRC + ','
    'snippet:"NCT00591578 (Sica 2011, J Clin Hypertens 13:467-472). Monotherapy comparison against '
    'valsartan 320 mg, and the registered primary endpoint is 24-HOUR AMBULATORY systolic BP at '
    'Week 24 - a different measurement modality and timepoint from the clinic-BP estimands, so it '
    'is not pooled with them. Posted ANCOVA adjusted mean difference, azilsartan 40 mg vs '
    'valsartan: -3.64 mmHg (95% CI -5.59 to -1.69), p<0.001; arm LS means -14.93 / -15.32 / -11.29. '
    'Azilsartan 80 mg vs valsartan: -4.03 (-6.01 to -2.06) - sensitivity only (shared control arm).",'
    'sourceUrl:"https://clinicaltrials.gov/study/NCT00591578",'
    'ctgovUrl:"https://clinicaltrials.gov/study/NCT00591578",evidence:[]}}'
)

if _ALREADY:
    skipped.append(("A1", "realData rebuilt as source-verified continuous estimands"))
elif OLD_DATA:
    h = h.replace(OLD_DATA, NEW_DATA)
    applied.append(("A1", "realData rebuilt as source-verified continuous estimands"))

# ===========================================================================
# STAGE 2 -- make the continuous engine reachable, and the labels honest
# ===========================================================================

# A2 -- the continuous dispatch could never fire under the "default" outcome key.
h = edit(
    h, "A2", "continuous dispatch resolves allOutcomes[0] under the default key",
    'if(trials.some(t=>{const o=t.data?.allOutcomes?.find(x=>x.shortLabel===outcomeKey);'
    'return o&&"CONTINUOUS"===o.type})&&void 0!==ContinuousMDEngine)',
    # Under outcomeKey "default" the shortLabel lookup ALWAYS misses, so the
    # continuous branch was unreachable on any page that does not explicitly
    # select a named outcome. Fall back to the first declared outcome, which is
    # exactly what applyOutcomeScope() itself uses for the default key.
    'if(trials.some(t=>{const _os=t.data?.allOutcomes??[],'
    'o="default"===outcomeKey?_os[0]:_os.find(x=>x.shortLabel===outcomeKey);'
    'return o&&"CONTINUOUS"===o.type})&&void 0!==ContinuousMDEngine)',
)

# A3 -- admit a continuous member into the effect-measure vocabulary.
h = edit(
    h, "A3", "effect-measure vocabulary admits MD",
    'return["AUTO","HR","RR","OR"].includes(em)?em:"AUTO"}',
    'return["AUTO","HR","RR","OR","MD"].includes(em)?em:"AUTO"}',
)

# A4 -- resolve to MD whenever the analysed set is continuous.
OLD_RESOLVE = (
    'resolveEffectMeasure(opts={}){const requested=this.sanitizeEffectMeasure('
    'opts.effectMeasure??this.state.effectMeasure);if("AUTO"!==requested){const long=void 0;'
    'return{requested,effective:requested,short:requested,long:{OR:"Odds Ratio",RR:"Risk Ratio",'
    'HR:"Hazard Ratio"}[requested]??requested,isAuto:!1}}const trials=Array.isArray(opts.trials)?'
    'opts.trials.filter(t=>t?.data):this.getScopedIncludedTrials({requireData:!0}),'
    'useHR=trials.length>0&&trials.every(t=>this.trialHasPublishedHR(t)),effective=useHR?"HR":"RR",'
    'long=void 0;return{requested:"AUTO",effective,short:effective,long:useHR?"Hazard Ratio":"Risk Ratio",isAuto:!0}}'
)
NEW_RESOLVE = (
    # Checked BEFORE the requested-measure branch so the ratio toggle cannot
    # paint a ratio label onto a mean difference.
    'trialIsContinuousMD(trial){const d=trial?.data;if(!d)return!1;'
    'if("MD"===String(d.estimandType??"").toUpperCase())return!0;'
    'if(null!=d.md&&null!=d.se)return!0;'
    'return Boolean((d.allOutcomes??[]).some(o=>"CONTINUOUS"===String(o?.type??"").toUpperCase()))},'
    'resolveEffectMeasure(opts={}){const requested=this.sanitizeEffectMeasure('
    'opts.effectMeasure??this.state.effectMeasure);'
    'const _tr=Array.isArray(opts.trials)?opts.trials.filter(t=>t?.data):'
    'this.getScopedIncludedTrials({requireData:!0});'
    'if(_tr.length>0&&_tr.every(t=>this.trialIsContinuousMD(t)))'
    'return{requested,effective:"MD",short:"MD",long:"Mean Difference",isAuto:!0,isContinuous:!0};'
    'if("AUTO"!==requested){const long=void 0;'
    'return{requested,effective:requested,short:requested,long:{OR:"Odds Ratio",RR:"Risk Ratio",'
    'HR:"Hazard Ratio",MD:"Mean Difference"}[requested]??requested,isAuto:!1}}const trials=_tr,'
    'useHR=trials.length>0&&trials.every(t=>this.trialHasPublishedHR(t)),effective=useHR?"HR":"RR",'
    'long=void 0;return{requested:"AUTO",effective,short:effective,long:useHR?"Hazard Ratio":"Risk Ratio",isAuto:!0}}'
)
h = edit(h, "A4", "resolveEffectMeasure returns MD for continuous corpora",
         OLD_RESOLVE, NEW_RESOLVE)

# A5 -- emLabel must not say "Log Mean Difference" or "P(MD < 1)".
OLD_EMLABEL = (
    'emLabel(format){const resolved=this.resolveEffectMeasure(),em=resolved.effective,'
    'long=resolved.long,pooled=void 0,map=void 0;return{short:em,long,'
)
NEW_EMLABEL = (
    'emLabel(format){const resolved=this.resolveEffectMeasure(),em=resolved.effective,'
    'long=resolved.long,pooled=void 0,map=void 0;'
    'if("MD"===em)return{short:"MD",long:"Mean Difference",'
    'pooled:"Pooled Mean Difference in SBP (mmHg)",'
    'log:"Mean difference (mmHg)",'
    'pLt1:"P(MD < 0)",pLt1Html:"P(MD &lt; 0)"}[format]??"MD";'
    'return{short:em,long,'
)
h = edit(h, "A5", "emLabel MD-aware (mmHg scale, null is 0)",
         OLD_EMLABEL, NEW_EMLABEL)

# A6 -- only Estimand A enters the pool.  A study flagged separateEstimand
# answers a different question and must not be averaged into it.
h = edit(
    h, "A6", "separate-estimand studies are held out of the pooled analysis",
    'if(!selectedOutcome)continue;const ranked=[...outcomes]',
    # Set AFTER the outcome branch above, which resets _outcomeExcluded on
    # every call, so the flag cannot be silently cleared by a rescope.
    'if(t.data.separateEstimand)t.data._outcomeExcluded=!0;'
    'if(!selectedOutcome)continue;const ranked=[...outcomes]',
    marker="t.data.separateEstimand)t.data._outcomeExcluded",
)

# A7 -- the ledger label for those studies.
h = edit(
    h, "A7", "ledger labels held-out studies as a separate estimand",
    'trial?.data?._outcomeExcluded?"Endpoint out of scope"',
    'trial?.data?.separateEstimand?"Separate estimand (not pooled)":'
    'trial?.data?._outcomeExcluded?"Endpoint out of scope"',
    marker='"Separate estimand (not pooled)"',
)

# ===========================================================================
# STAGE 3 -- retire the outputs that require an event table, and fix the
# ratio-scale captions.  Nothing is deleted from the DOM: panels are hidden at
# render time with an explicit reason, so the page cannot silently drop a panel
# a reader expected to find.
# ===========================================================================

OLD_DESC_CHAIN = 'setDesc("desc-loo","Omitting each study in turn, pooled log"+emS+" ranges from "'
NEW_DESC_CHAIN = (
    '(()=>{const _cont="MD"===emS;'
    # L'Abbe (event incidence), NNT (1/ARR), risk difference and the TSA Z-curve
    # (RIS is an event-count calculation) are undefined without event data.
    'const _evOnly=[["plot-labbe","L\'Abbe plot"],["plot-nnt","NNT / clinical-utility curve"],'
    '["plot-tsa","Trial Sequential Analysis (Z-curve)"]];'
    '_evOnly.forEach(([pid,label])=>{const el=document.getElementById(pid);if(!el)return;'
    'const panel=el.closest(".col-span-1")||el.parentElement;if(!panel)return;'
    'if(_cont){panel.dataset.suppressed="continuous";panel.style.display="none";'
    'const d=document.getElementById(pid.replace("plot-","desc-"));'
    'if(d)d.textContent=label+" not applicable: the pooled outcome is a continuous mean '
    'difference in mmHg and these trials report no event counts.";}'
    'else{if("continuous"===panel.dataset.suppressed){panel.style.display="";'
    'delete panel.dataset.suppressed;}}});'
    # The fragility index modifies event counts; it has no meaning here.
    'if(_cont){const fc=document.getElementById("chip-fragility")||document.getElementById("stat-fragility");'
    'if(fc){fc.className="stat-chip stat-chip-blue";fc.innerHTML='
    '\'<i class="fa-solid fa-shield-halved" style="font-size:10px"></i> '
    'Fragility: N/A (continuous outcome)\';}}'
    '})(),'
    'setDesc("desc-loo","Omitting each study in turn, pooled log"+emS+" ranges from "'
)
h = edit(h, "B1", "event-only panels hidden with a stated reason on the MD scale",
         OLD_DESC_CHAIN, NEW_DESC_CHAIN, marker="_evOnly")

h = edit(
    h, "B2", "leave-one-out caption on the MD scale",
    'setDesc("desc-loo","Omitting each study in turn, pooled log"+emS+" ranges from "'
    '+looRange[0].toFixed(3)+" to "+looRange[1].toFixed(3)+" ("+emS+" "'
    '+Math.exp(looRange[0]).toFixed(2)+"–"+Math.exp(looRange[1]).toFixed(2)+"). "',
    'setDesc("desc-loo","MD"===emS'
    '?"With only two studies in the pooled estimand, omitting either leaves a single trial; '
    'the range of single-study estimates is "'
    '+looRange[0].toFixed(2)+" to "+looRange[1].toFixed(2)+" mmHg. "'
    ':"Omitting each study in turn, pooled log"+emS+" ranges from "'
    '+looRange[0].toFixed(3)+" to "+looRange[1].toFixed(3)+" ("+emS+" "'
    '+Math.exp(looRange[0]).toFixed(2)+"–"+Math.exp(looRange[1]).toFixed(2)+"). "',
)

h = edit(
    h, "B3", "cumulative caption on the MD scale",
    '+" over time, with the final cumulative log"+emS+" = "+tr3X[tr3X.length-1].toFixed(3)+".',
    '+" over time, with the final cumulative "+("MD"===emS?"mean difference = "'
    '+tr3X[tr3X.length-1].toFixed(2)+" mmHg":"log"+emS+" = "'
    '+tr3X[tr3X.length-1].toFixed(3))+".',
)

h = edit(
    h, "B4", "Galbraith caption states the correct standardized effect",
    'setDesc("desc-galbraith","Studies plotted as standardized effect (z = log"+emS+"/SE)',
    'setDesc("desc-galbraith","Studies plotted as standardized effect '
    '(z = "+("MD"===emS?"MD":"log"+emS)+"/SE)',
)

# B5 -- at k=2 the small-study-effect diagnostics are not merely low-powered,
# they are undefined.  Egger's regression needs k>=3; trim-and-fill and
# meta-regression need considerably more.
h = edit(
    h, "B5", "funnel caption states that k=2 makes bias diagnostics undefined",
    'setDesc("desc-funnel","Contour-enhanced funnel plot with significance regions '
    '(p < 0.01, 0.05, 0.10). Visual symmetry around the pooled estimate suggests absence '
    'of publication bias."',
    'setDesc("desc-funnel","Contour-enhanced funnel plot with significance regions '
    '(p < 0.01, 0.05, 0.10). With k = 2 studies in the pooled estimand, funnel asymmetry, '
    'Egger regression (needs k >= 3), trim-and-fill and meta-regression are all UNDEFINED or '
    'uninformative. This plot cannot establish either the presence or the absence of '
    'publication bias, and no such claim is made."',
)

# ===========================================================================
# STAGE 4 -- reader-facing surfaces
# ===========================================================================

h = edit(
    h, "C1", "visual abstract states the real enrolment era (was 'Post-2015')",
    '<div class="va-label">Acquisition Era</div><div class="va-value">Post-2015 Enrollment</div>',
    # The four studies enrolled 2008-2010 and published 2011-2018. "Post-2015"
    # conflated a publication year with an enrolment window and was false for
    # every included study.
    '<div class="va-label">Enrolment Period</div><div class="va-value">2008&ndash;2010 '
    '(published 2011&ndash;2018)</div>',
)

h = edit(
    h, "C2", "scientific verdict names the BP endpoint, not a CV composite",
    'verdictOutcome={default:"the matched cardiovascular composite endpoint"',
    'verdictOutcome={default:"change from baseline in systolic blood pressure (mmHg)"',
)

h = edit(
    h, "C3", "narrative names the BP endpoint, not a CKD cardiovascular composite",
    'ocProse={default:"the matched cardiovascular composite endpoint across CKD trials"',
    'ocProse={default:"change from baseline in systolic blood pressure (mmHg) across '
    'the pooled hypertension estimand"',
)

# ===========================================================================
# STAGE 5 -- protocol.  As shipped, the eligibility criteria excluded all four
# of the review's own included studies.
# ===========================================================================

h = edit(
    h, "D1", "PICO comparator is active, not placebo",
    'value="Placebo" aria-label="Comparator (PICO)"',
    'value="Active antihypertensive comparator (olmesartan/HCTZ; valsartan 320 mg; '
    'azilsartan+HCTZ). No placebo-controlled trial is included." aria-label="Comparator (PICO)"',
)

h = edit(
    h, "D2", "PICO population is the clinical population, not a registry query",
    'value="Adults randomised in trials registered on ClinicalTrials.gov for Hypertension" '
    'aria-label="Population (PICO)"',
    'value="Adults with stage 2 primary (essential) hypertension" aria-label="Population (PICO)"',
)

h = edit(
    h, "D3", "PICO intervention names the actual regimens",
    'value="Azilsartan" aria-label="Intervention (PICO)"',
    'value="Azilsartan medoxomil, as monotherapy or as a fixed-dose combination with '
    'chlorthalidone" aria-label="Intervention (PICO)"',
)

h = edit(
    h, "D4", "PICO primary outcome is an estimand-specific mean difference",
    'value="Change From Baseline to Week 8 in Trough, Sitting, Clinic Systolic Blood Pressure." '
    'aria-label="Outcome (PICO)"',
    'value="Adjusted mean difference (mmHg) in change from baseline in systolic BP at a '
    'harmonised timepoint, analysed separately within each estimand (A: clinic SBP at Week 8; '
    'B: 24-h ambulatory SBP at Week 24; C: clinic SBP at Week 6)" aria-label="Outcome (PICO)"',
)

h = edit(
    h, "D5", "subgroup plan is not an asthma/COPD template",
    'value="Blood eosinophils, smoking status, ICS use" aria-label="Subgroup analyses"',
    # Inherited verbatim from a respiratory template; none of these variables
    # exists in any of the four studies.
    'value="None. The only poolable estimand contains k = 2 studies, which cannot support '
    'subgroup analysis or meta-regression." aria-label="Subgroup analyses"',
)

h = edit(
    h, "D6", "eligibility: comparator criterion no longer excludes every included study",
    '<td class="p-3 text-slate-300">Placebo, sham, or standard of care</td>'
    '<td class="p-3 text-slate-400">Active comparator without placebo arm</td>',
    '<td class="p-3 text-slate-300">Any randomised antihypertensive comparator, active or '
    'placebo. All four included studies are active-controlled.</td>'
    '<td class="p-3 text-slate-400">Single-arm or open-label extension without a randomised '
    'comparator</td>',
)

h = edit(
    h, "D7", "eligibility: outcome criterion matches the review's actual outcome",
    '<td class="p-3 text-slate-300">&ge;1 primary cardiovascular efficacy endpoint (mortality, '
    'stroke, MI, VTE, composite MACE) with extractable data</td>'
    '<td class="p-3 text-slate-400">Biomarker-only, PK-only, no event data</td>',
    # As shipped this demanded a clinical CV endpoint and excluded "biomarker-only",
    # which excludes all four included studies -- the review pools blood pressure.
    '<td class="p-3 text-slate-300">Change from baseline in systolic BP (trough sitting clinic '
    'BP, or 24-h ambulatory BP) with an adjusted mean difference and a measure of precision</td>'
    '<td class="p-3 text-slate-400">No extractable BP change; PK-only. NOTE: this review reports '
    'NO clinical cardiovascular outcome (mortality, stroke, MI, MACE). Blood-pressure lowering is '
    'a surrogate and the two are not interchangeable.</td>',
)

h = edit(
    h, "D8", "eligibility: pre-2015 publication-date exclusion removed (corpus policy)",
    '<td class="p-3 text-slate-400">Pre-2015; duplicate cohorts; editorials, letters, reviews</td>',
    # Corpus policy: eligibility is by PICO/scope and data availability, never by
    # date. The four primary publications are 2011-2018 and were never excludable.
    '<td class="p-3 text-slate-400">Duplicate cohorts; editorials, letters, reviews. No '
    'publication-date restriction is applied.</td>',
)

h = edit(
    h, "D9", "eligibility: follow-up threshold no longer excludes half the review",
    '<td class="p-3 text-slate-300">&ge;12 weeks (primary outcome assessment)</td>'
    '<td class="p-3 text-slate-400">&lt;12 weeks or acute/single-dose studies</td>',
    # ">=12 weeks" excluded NCT00846365 (8 wk) and NCT00818883 (6/10 wk).
    '<td class="p-3 text-slate-300">&ge;6 weeks at the analysed timepoint</td>'
    '<td class="p-3 text-slate-400">Acute or single-dose studies</td>',
)

# D10 -- the live pre-2015 screening rule, not just the protocol table.
h = edit(
    h, "D10", "pre-2015 auto-exclusion rule removed from the screening code",
    't.year<2015&&(t.status="exclude",t.reason="Era Restriction: Pre-2015.")',
    # Kept as a no-op expression so the surrounding comma-chain is unchanged.
    'void 0',
)

h = edit(
    h, "D11", "a commit timestamp is not equivalent to PROSPERO registration",
    'Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration '
    'record equivalent to PROSPERO for tracking outcome / eligibility / analysis-plan changes.',
    # The GitHub history is a genuine change-tracking record and that claim is
    # kept. What it is not is a prospective registration in a review registry.
    'The GitHub commit hash and timestamp are a verifiable CHANGE-TRACKING record for outcome, '
    'eligibility and analysis-plan amendments. They are not a prospective registration: this '
    'review is not registered in PROSPERO or any review registry, and the protocol was written '
    'after the included studies were identified.',
)

# ---------------------------------------------------------------------------
# The Arabic UI dictionary is keyed on the English source text.  Every string
# corrected above left a dead key behind, so the Arabic build would either fall
# back to untranslated English or keep asserting the retired claim.
# ---------------------------------------------------------------------------

h = edit(
    h, "D12", "Arabic dictionary: enrolment era key follows the corrected English",
    '"Acquisition Era":"فترة الاستحواذ","Post-2015 Enrollment":"التسجيل بعد 2015"',
    '"Enrolment Period":"فترة التسجيل"',
    expect=2,
)

h = edit(
    h, "D13", "Arabic dictionary: primary result is not a MACE result",
    '"Primary Result":"نتيجة MACE الأولية"',
    '"Primary Result":"النتيجة الأولية"',
    expect=2,
)

h = edit(
    h, "D14", "Arabic dictionary: no pre-2015 exclusion",
    '"Pre-2015; duplicate cohorts; editorials, letters, reviews":'
    '"قبل 2015؛ أفواج مكررة؛ افتتاحيات، رسائل، مراجعات"',
    '"Duplicate cohorts; editorials, letters, reviews. No publication-date restriction is applied.":'
    '"أفواج مكررة؛ افتتاحيات، رسائل، مراجعات. لا يُطبَّق أي قيد على تاريخ النشر."',
)

h = edit(
    h, "D15", "Arabic dictionary: comparator exclusion follows the corrected English",
    '"Active comparator without placebo arm":"مقارنة فعالة بدون ذراع وهمي"',
    '"Single-arm or open-label extension without a randomised comparator":'
    '"دراسة أحادية الذراع أو امتداد مفتوح التسمية بدون مقارِن عشوائي"',
)

# D17 -- the PICO <input value="..."> attributes are only the initial paint.
# syncUI() writes state.protocol into #p-pop/#p-int/#p-comp/#p-out on every
# render, so the JS defaults are the real source and would overwrite the
# corrected fields at runtime.  Fix both, or the visible fix is cosmetic.
h = edit(
    h, "D17", "protocol state defaults match the corrected PICO (syncUI overwrites the inputs)",
    'state:{protocol:{pop:"Adults randomised in trials registered on ClinicalTrials.gov for '
    'Hypertension",int:"Azilsartan (AACT-verified intervention name)",'
    'comp:"Active comparator or placebo as registered on AACT",'
    'out:"Trial-declared primary outcome (AACT design_outcomes); event counts from AACT '
    'outcome_measurements",subgroup:"Subgroup analyses per parent trial protocol",'
    'query:"",rctOnly:!0,post2015:!0}',
    'state:{protocol:{pop:"Adults with stage 2 primary (essential) hypertension",'
    'int:"Azilsartan medoxomil, as monotherapy or as a fixed-dose combination with chlorthalidone",'
    'comp:"Active antihypertensive comparator (olmesartan/HCTZ; valsartan 320 mg; '
    'azilsartan+HCTZ). No placebo-controlled trial is included.",'
    'out:"Adjusted mean difference (mmHg) in change from baseline in systolic BP at a harmonised '
    'timepoint, analysed separately within each estimand. Continuous outcome - no event counts.",'
    'subgroup:"None. The only poolable estimand contains k = 2 studies, which cannot support '
    'subgroup analysis or meta-regression.",'
    # post2015 retired with the rest of the date-based eligibility (corpus policy).
    'query:"",rctOnly:!0,post2015:!1}',
)

# D18 -- the same retired PICO text is served to search engines and social cards.
OLD_META = (
    'Azilsartan (AACT-verified intervention name); Adults randomised in trials registered on '
    'ClinicalTrials.gov for Hypertension; Trial-declared primary outcome (AAC'
)
NEW_META = (
    'Azilsartan medoxomil in stage 2 primary hypertension; adjusted mean difference in systolic '
    'blood pressure (mmHg) across three separate estimands; 4 records, 2 pooled; UNVERIFIED '
    'automated output, not a validated meta-analysis'
)
h = edit(h, "D18", "meta description and JSON-LD carry the corrected scope",
         OLD_META, NEW_META, expect=2)

# D16 -- clone contamination surviving in the i18n map: the English key names
# sacubitril/valsartan and the Arabic value names finerenone, in an azilsartan
# hypertension review.  The English DOM title is "Azilsartan in HTN", so the key
# never matched and the entry was dead as well as wrong.
h = edit(
    h, "D16", "i18n title contamination (sacubitril key -> finerenone value) removed",
    '"Sacubitril/Valsartan in Heart Failure":"الفينيرينون في أمراض القلب والكلى والأيض"',
    '"Azilsartan in HTN":"أزيلسارتان في ارتفاع ضغط الدم"',
    expect=2,
)

# ===========================================================================
# STAGE 6 -- integrity surfaces.  Both verdict surfaces reported "2 trials"
# over a 4-study ledger, and a green PASSED badge over a review whose pooled
# estimate was invalid.
# ===========================================================================

h = edit(
    h, "E1", "green INTERNAL CHECKS PASSED badge replaced by the real state",
    '<strong style="font-size:14px;letter-spacing:0.04em;">INTERNAL CHECKS PASSED</strong>'
    '<span style="font-size:11.5px;">Fabrication-risk score: <strong>0.275</strong> '
    '· Trials: <strong>2</strong></span>',
    '<strong style="font-size:14px;letter-spacing:0.04em;">UNVERIFIED — '
    'AUTOMATED OUTPUT, NOT A VALIDATED META-ANALYSIS</strong>'
    '<span style="font-size:11.5px;">Records: <strong>4</strong> '
    '· Pooled: <strong>2</strong> (Estimand A) '
    '· Dual screening: <strong>0/4</strong> '
    '· Dual extraction: <strong>0/4</strong> '
    '· Human RoB-2: <strong>0/4</strong></span>',
)

h = edit(
    h, "E1b", "audit sentence no longer claims a completed multi-source audit",
    'Multi-source audit completed (AACT 2026-04-12 + PubMed + 10 internal-consistency rounds). '
    'Routine pre-publication human spot-check recommended.',
    # Effect estimates were re-extracted from the ClinicalTrials.gov posted
    # results and cross-checked against the primary publications during the
    # 2026-07-30 rebuild. Screening, dual extraction and RoB remain undone.
    'Effect estimates re-extracted from the ClinicalTrials.gov posted results and cross-checked '
    'against the primary publications (Cushman 2012/2018, Bakris 2012, Sica 2011). Screening was '
    'single-reviewer and automated; dual extraction and human risk-of-bias assessment have NOT '
    'been performed. This page is not a validated meta-analysis.',
)

h = edit(
    h, "E2", "badge colour no longer reads as a pass",
    'font-size:13.5px;border-bottom:3px solid #14532d;line-height:1.55;',
    'font-size:13.5px;border-bottom:3px solid #b45309;line-height:1.55;',
)

h = edit(
    h, "E3", "machine verdict agrees with the reader-facing verdict",
    '{"verdict": "STABLE", "counts": {"P0_internal": 0, "P0_aact_nct_missing": 0, "P0_grim": 0, '
    '"P1_aact_concord": 2, "P1_fi_critical": 0, "P1_fi_warn": 0, "P1_pi_gap": 0, '
    '"P2_evidence_incomplete": 2, "n_trials_seen": 2, "P2_aact_advisory": 2}, '
    '"reasons": ["2 AACT title/registry advisory", "2 AACT outcome-direction divergence(s)", '
    '"2 trial(s) missing evidence rows"], "p0_total": 0}',
    '{"verdict": "UNVERIFIED", "counts": {"P0_internal": 0, "P0_aact_nct_missing": 0, '
    '"P0_grim": 0, "P1_aact_concord": 0, "P1_fi_critical": 0, "P1_fi_warn": 0, "P1_pi_gap": 0, '
    '"P2_evidence_incomplete": 4, "n_trials_seen": 4, "n_pooled": 2, "P2_aact_advisory": 0}, '
    '"reasons": ["4 records in the ledger; only 2 are pooled (Estimand A)", '
    '"0/4 dual screening, 0/4 dual extraction, 0/4 human RoB-2 assessment", '
    '"risk-of-bias domains are registry-derived defaults, not reviewer judgements", '
    '"k = 2 in the pooled estimand: heterogeneity, small-study-effect and subgroup '
    'diagnostics are undefined or uninformative"], "p0_total": 0}',
)

# ---------------------------------------------------------------------------
# E4 -- the Overmind "COMPARISON CHECK" banner was itself wrong.  NCT00818883
# randomises azilsartan medoxomil 40 mg in BOTH arms at the SAME dose; the
# randomised contrast is the diuretic partner.  Calling it a dose comparison
# misdescribes the only thing the trial actually randomised.  The banner is
# injected into both the full app and its redirect stub.
# ---------------------------------------------------------------------------
OLD_BANNER = (
    "&#9888; <b>COMPARISON CHECK</b> &mdash; azilsartan appears in all arms of NCT00818883 "
    "(dose-comparison only) &mdash; this trial compares doses, not azilsartan vs control."
)
NEW_BANNER = (
    "&#9888; <b>COMPARISON CHECK</b> &mdash; NCT00818883 gives azilsartan medoxomil 40 mg in "
    "BOTH arms at the same dose. It is not a dose comparison: the randomised contrast is the "
    "diuretic partner, chlorthalidone vs hydrochlorothiazide. It measures no azilsartan effect "
    "and is held out of the pooled estimand."
)
h = edit(h, "E4", "comparison-check banner describes the real randomised contrast",
         OLD_BANNER, NEW_BANNER)

# ===========================================================================
# STAGE 7 -- PRISMA flow.  The shipped fallback emits a literal 0 for the
# upstream boxes while filling the downstream boxes from realData, which
# renders more studies included than were ever identified.
# ===========================================================================
pf = io.open(PRISMA, encoding="utf-8").read()
orig_pf = pf

pf = edit(
    pf, "F1", "PRISMA never renders more included than identified",
    "    // If no trials are tracked but realData has entries, derive minimal counts\n"
    "    if (counts.total_search === 0 && counts.in_nma > 0) {\n"
    "      counts.included_qualitative = counts.in_nma;\n"
    "      counts.fulltext = counts.in_nma;\n"
    "    }\n",
    "    // If no screening ledger is loaded yet, the upstream counts are genuinely\n"
    "    // unknown -- they are NOT zero. Emitting 0 here produced an impossible\n"
    "    // flow (0 identified, k included). Mark them not-recorded instead.\n"
    "    if (counts.total_search === 0 && counts.in_nma > 0) {\n"
    "      counts.included_qualitative = counts.in_nma;\n"
    "      counts.fulltext = counts.in_nma;\n"
    "      counts.total_search = null;\n"
    "      counts.screened = null;\n"
    "      counts.not_recorded = true;\n"
    "    }\n",
)

pf = edit(
    pf, "F2", "PRISMA boxes render 'not recorded' rather than a false 0",
    "    t2.textContent = 'k = ' + count;",
    "    // A null count means the ledger does not record this stage; printing\n"
    "    // 'k = 0' would assert something the data cannot support.\n"
    "    if (count === null || count === undefined) {\n"
    "      t2.setAttribute('font-size', '11');\n"
    "      t2.setAttribute('fill', '#fbbf24');\n"
    "      t2.textContent = 'not recorded';\n"
    "    } else {\n"
    "      t2.textContent = 'k = ' + count;\n"
    "    }",
    marker="not recorded",
)

# ===========================================================================
# STAGE 8 -- the shared vendor stat panels assume a 2x2 corpus.  Suppressed
# from the app side only when THIS page's pool is continuous; the corpus-shared
# vendor files are untouched.
# ===========================================================================
SUPPRESSOR = """
<script>
/* Continuous-outcome guard for the shared vendor stat panels.
   Scoped to this page; vendor files are untouched. */
(function () {
  var RATIO_ONLY = {
    'r-validation-badge':        'R metafor cross-validation runs an escalc() 2x2 model; this review has no event counts. The continuous validation script is in Analysis \\u2192 R code.',
    'grade-sof-panel':           'The GRADE SoF panel computes risk-with-control / risk-with-intervention from event counts. This outcome is a mean difference in mmHg.',
    'rr-sensitivity-panel':      'RR-vs-OR sensitivity is undefined without event counts.',
    'bayesian-sensitivity-panel':'This Bayesian panel places its prior on a log-odds scale.',
    'nnt-panel':                 'NNT and absolute risk difference are undefined for a continuous outcome.',
    'cumulative-ma-panel':       'This panel accumulates on the log-OR scale. The cumulative mean-difference plot is in Analysis.',
    'pi-convention-panel':       'This panel reports the prediction interval on the log-OR scale, and with k = 2 a prediction interval is not estimable in any case.',
    'tau2-qprofile-panel':       'This panel estimates tau-squared on the log-OR scale. With k = 2, tau-squared is not identifiable.',
    'funnel-diagnostics-panel':  "Peters' test is defined for binary outcomes only, and small-study-effect tests require k >= 3."
  };
  function isContinuous() {
    try {
      var r = window.RapidMeta && RapidMeta.state && RapidMeta.state.results;
      if (r && r.isContinuous) return true;
      return !!(window.RapidMeta && RapidMeta.emLabel && RapidMeta.emLabel('short') === 'MD');
    } catch (e) { return false; }
  }
  function apply() {
    var cont = isContinuous();
    Object.keys(RATIO_ONLY).forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      if (cont) {
        if (el.dataset.rmContSuppressed === '1') return;
        el.dataset.rmContSuppressed = '1';
        el.style.display = 'none';
        if (!document.getElementById('note-' + id)) {
          var note = document.createElement('div');
          note.id = 'note-' + id;
          note.style.cssText = 'margin:6px 0;padding:8px 10px;border-left:3px solid #b45309;'
            + 'background:rgba(180,83,9,0.08);color:#94a3b8;font-size:11px;line-height:1.5;';
          note.textContent = 'Panel not applicable to this review (continuous outcome). '
            + RATIO_ONLY[id];
          el.parentNode.insertBefore(note, el);
        }
      } else if (el.dataset.rmContSuppressed === '1') {
        delete el.dataset.rmContSuppressed;
        el.style.display = '';
        var n = document.getElementById('note-' + id);
        if (n) n.remove();
      }
    });
  }
  var host = document.getElementById('stats-tab-host') || document.body;
  try { new MutationObserver(apply).observe(host, { childList: true, subtree: true }); } catch (e) {}
  document.addEventListener('DOMContentLoaded', apply);
  [400, 1200, 2500, 5000].forEach(function (t) { setTimeout(apply, t); });
})();
</script>
"""

if "rmContSuppressed" in h:
    skipped.append(("G1", "ratio-only vendor stat panels suppressed"))
else:
    _idx = h.rfind("</body>")
    if _idx == -1:
        failed.append(("G1", "vendor panel suppressor", "no </body> found"))
    else:
        h = h[:_idx] + SUPPRESSOR + h[_idx:]
        applied.append(("G1", "ratio-only vendor stat panels suppressed with a stated reason"))

# ---------------------------------------------------------------------------
if failed:
    print("FAILED ANCHORS:")
    for fid, desc, why in failed:
        print("  [%s] %s -- %s" % (fid, desc, why))

print("applied=%d skipped(idempotent)=%d failed=%d" % (len(applied), len(skipped), len(failed)))
for fid, desc in applied:
    print("  + [%s] %s" % (fid, desc))
for fid, desc in skipped:
    print("  = [%s] %s (already applied)" % (fid, desc))

if failed:
    sys.exit(1)


def syntax_gate(html_text, extra):
    """Syntax-check every inline <script> block plus the listed JS files.

    One node process compiles every block via vm.Script.  Spawning `node
    --check` per block (~40 processes) took over ten minutes on a loaded
    machine, which is long enough that the gate gets skipped -- and a gate that
    is skipped is not a gate.
    """
    import json
    import shutil
    import subprocess
    import tempfile

    blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html_text, re.S)
    targets = list(extra)
    for i, b in enumerate(blocks):
        if not b.strip():
            continue
        # JSON-LD blocks are data, not script.
        if b.strip().startswith("{") and '"@context"' in b[:200]:
            continue
        targets.append(("inline block %d" % i, b))

    workdir = tempfile.mkdtemp(prefix="azil_syntax_")
    try:
        manifest = []
        for i, (label, code) in enumerate(targets):
            p = os.path.join(workdir, "b%03d.js" % i)
            io.open(p, "w", encoding="utf-8").write(code)
            manifest.append({"label": label, "path": p})
        mpath = os.path.join(workdir, "manifest.json")
        io.open(mpath, "w", encoding="utf-8").write(u"%s" % json.dumps(manifest))
        runner = os.path.join(workdir, "run.js")
        io.open(runner, "w", encoding="utf-8").write(
            u"const fs=require('fs'),vm=require('vm');\n"
            u"const m=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));\n"
            u"const out=[];\n"
            u"for(const e of m){\n"
            u"  const src=fs.readFileSync(e.path,'utf8');\n"
            u"  try{ new vm.Script(src,{filename:e.label}); }\n"
            u"  catch(err){ out.push(e.label+': '+String(err.message)); }\n"
            u"}\n"
            u"process.stdout.write(JSON.stringify(out));\n"
        )
        r = subprocess.run(["node", runner, mpath], capture_output=True)
        if r.returncode != 0:
            return ["syntax gate could not run: "
                    + r.stderr.decode("utf-8", errors="replace")[-300:]]
        return json.loads(r.stdout.decode("utf-8", errors="replace") or "[]")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# The redirect stub carries the same injected banner and is a separately served
# URL, so it must not keep asserting the retired claim.
# ---------------------------------------------------------------------------
STUB = os.path.join(ROOT, "AZILSARTAN_HTN_AUTO_REVIEW.html")
st = io.open(STUB, encoding="utf-8").read()
orig_st = st
st = edit(st, "E4b", "redirect stub: comparison-check banner corrected",
          OLD_BANNER, NEW_BANNER)

probs = syntax_gate(h, [("vendor/prisma-flow.js", pf)])
if probs:
    print("SYNTAX GATE FAILED -- nothing written:")
    for p in probs:
        print("  ! " + p)
    sys.exit(1)
print("syntax gate: all inline blocks + vendor/prisma-flow.js parse cleanly")

if CHECK_ONLY:
    print("check-only: no files written")
    sys.exit(0)

if h != orig_h:
    io.open(APP, "w", encoding="utf-8", newline="").write(h)
    print("wrote %s" % os.path.basename(APP))
if pf != orig_pf:
    io.open(PRISMA, "w", encoding="utf-8", newline="").write(pf)
    print("wrote vendor/prisma-flow.js")
if st != orig_st:
    io.open(STUB, "w", encoding="utf-8", newline="").write(st)
    print("wrote %s" % os.path.basename(STUB))
