#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rebuild ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html as a CONTINUOUS-outcome
(generic inverse-variance mean-difference) review.

The six included ODYSSEY trials contribute one outcome only: percent change in
calculated LDL-C from baseline to Week 24 (ITT).  That is a mean difference in
PERCENTAGE POINTS.  The app was rendering it as a RISK RATIO.

Root causes fixed here (each verified in a live render before the fix):

  R1  RapidMeta.sanitizeEffectMeasure() vocabulary is ["AUTO","HR","RR","OR"].
      There is no continuous member, so no code path can ever say "MD".
  R2  resolveEffectMeasure() falls through to "RR" because trialHasPublishedHR()
      requires hrUCI > 0 and the mean differences are negative.
  R3  desc-forest prose exponentiates the pooled MD (Math.exp(-61.59) -> 0.00)
      and computes pctRed = 100*(1-or) = 100*(1-(-54.33)) = 5533.
  R4  updateStatCards() clamps the HKSJ bound with Math.max(.001, lci) -- a
      ratio-scale positivity guard applied to a mean difference, so the true
      -64.13 renders as 0.00.  The pre-existing isContinuous branch applies the
      same clamp, so the continuous path was broken too.
  R5  The engine computes tau2_dl and tau2_reml, returns only tau2 (= REML),
      and stats-ext.js prints that single value as BOTH "REML" and "DL".
  R6  stats-ext.js reads res.i2; the engine returns res.I2.  Case mismatch ->
      NaN -> "I2 = --" beside "88%" elsewhere on the same page.
  R7  The continuous engine never populates plotData tN/cN, so the forest
      caption reports "N = 0" over 3,674 randomised participants.
  R8  eggerResult is hardcoded {sufficient:false} in the continuous engine, and
      the chip then claims "N/A (k < 3)" at k = 6.

Idempotent and anchor-based: re-running is a no-op, and the anchors are short
unique substrings so the script survives unrelated corpus-wide edits.

Usage:  python scripts/fix_alirocumab_lipid_continuous.py [--check]
"""
import io
import re
import sys
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html")
STATS_EXT = os.path.join(ROOT, "stats-ext.js")

CHECK_ONLY = "--check" in sys.argv

applied, skipped, failed = [], [], []


def edit(text, fid, desc, old, new, expect=1, marker=None):
    """Anchored replacement.

    Idempotency is decided by `marker` -- a short token unique to the inserted
    code -- because the two obvious heuristics both fail here:
      * `new in text` breaks when a LATER edit rewrites part of what this edit
        inserted, so `new` is no longer present verbatim;
      * `old not in text` breaks for insertion-style edits where `new` is built
        as prefix + old, so `old` is still present and the edit re-applies,
        duplicating the inserted block.
    """
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


# ---------------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------------
h = io.open(APP, encoding="utf-8").read()
orig_h = h

# --- R1 -- admit a continuous member into the effect-measure vocabulary ------
h = edit(
    h, "R1", "effect-measure vocabulary admits MD",
    'return["AUTO","HR","RR","OR"].includes(em)?em:"AUTO"}',
    'return["AUTO","HR","RR","OR","MD"].includes(em)?em:"AUTO"}',
)

# --- R2 -- resolve to MD whenever the analysed set is continuous ------------
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
    # A trial is continuous when the extraction declares an MD estimand or a
    # CONTINUOUS outcome type.  Checked BEFORE the requested-measure branch so
    # the ratio toggle cannot paint a ratio label onto a mean difference.
    'trialIsContinuousMD(trial){const d=trial?.data;if(!d)return!1;'
    'if("MD"===String(d.estimandType??"").toUpperCase())return!0;'
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
h = edit(h, "R2", "resolveEffectMeasure returns MD for continuous corpora",
         OLD_RESOLVE, NEW_RESOLVE)

# --- R2b -- emLabel must not say "Log Mean Difference" or "P(MD < 1)" -------
OLD_EMLABEL = (
    'emLabel(format){const resolved=this.resolveEffectMeasure(),em=resolved.effective,'
    'long=resolved.long,pooled=void 0,map=void 0;return{short:em,long,'
)
NEW_EMLABEL = (
    'emLabel(format){const resolved=this.resolveEffectMeasure(),em=resolved.effective,'
    'long=resolved.long,pooled=void 0,map=void 0;'
    'if("MD"===em)return{short:"MD",long:"Mean Difference",'
    'pooled:"Pooled Mean Difference (Random-Effects)",'
    'log:"Mean difference (percentage points)",'
    'pLt1:"P(MD < 0)",pLt1Html:"P(MD &lt; 0)"}[format]??"MD";'
    'return{short:em,long,'
)
h = edit(h, "R2b", "emLabel MD-aware (no log scale, null is 0)",
         OLD_EMLABEL, NEW_EMLABEL)

# --- R5/R7/R8 -- continuous engine: return tau2_dl, real N, real Egger ------
OLD_RET = (
    'qPvalue:chi2Pvalue(Q,df),eggerResult:{sufficient:!1},fragIdx:0,fragQuot:"0.0",isContinuous:!0,plotData}'
)
NEW_RET = (
    'qPvalue:chi2Pvalue(Q,df),eggerResult:_contEgger(plotData),fragIdx:null,fragQuot:null,'
    'isContinuous:!0,tau2_dl,plotData}'
)
h = edit(h, "R5/R8", "continuous engine returns tau2_dl and a real Egger test",
         OLD_RET, NEW_RET)

# Egger's regression test on the MD scale: regress y_i/se_i on 1/se_i and test
# the intercept (Egger 1997).  Flagged exploratory at k < 10 (low power).
OLD_HELPER = 'function renderPlotNotice(id,msg){'
NEW_HELPER = (
    'function _contEgger(plotData){const k=plotData.length;'
    'if(k<3)return{sufficient:!1,reason:"k < 3"};'
    'const sn=plotData.map(d=>({y:d.md,se:Math.sqrt(d.vi)})).filter(d=>Number.isFinite(d.y)&&d.se>0);'
    'if(sn.length<3)return{sufficient:!1,reason:"k < 3"};'
    'const n=sn.length,X=sn.map(d=>1/d.se),Y=sn.map(d=>d.y/d.se),'
    'mx=X.reduce((a,b)=>a+b,0)/n,my=Y.reduce((a,b)=>a+b,0)/n;'
    'let sxx=0,sxy=0;for(let i=0;i<n;i++){sxx+=(X[i]-mx)**2;sxy+=(X[i]-mx)*(Y[i]-my)}'
    'if(!(sxx>0))return{sufficient:!1,reason:"degenerate"};'
    'const slope=sxy/sxx,inter=my-slope*mx;'
    'let rss=0;for(let i=0;i<n;i++){const e=Y[i]-(inter+slope*X[i]);rss+=e*e}'
    'const s2=rss/(n-2),seInt=Math.sqrt(s2*(1/n+mx*mx/sxx)),t=inter/seInt,'
    'p=tPvalue2tail(t,n-2);'
    # NOTE: the chip consumer reads eggerResult.pValue (capital V).
    'return{sufficient:!0,intercept:inter,se:seInt,t,pValue:p,k:n,'
    'exploratory:n<10,scale:"MD"}}'
    'function renderPlotNotice(id,msg){'
)
h = edit(h, "R8b", "Egger regression implemented for the MD scale",
         OLD_HELPER, NEW_HELPER, marker="function _contEgger")

# R7: carry the randomised denominators into plotData so the caption can state N.
h = edit(
    h, "R7", "continuous plotData carries per-arm N (was N = 0)",
    'plotData.push({id:t.id,name:t.data.name||t.id,year:t.data.year||2020,md:o.md,se:o.se,'
    'vi,w_fixed:1/vi,rob:t.data.rob||["low","low","low","low","low"]})',
    'plotData.push({id:t.id,name:t.data.name||t.id,year:t.data.year||2020,md:o.md,se:o.se,'
    'vi,w_fixed:1/vi,tN:parseInt(t.data.tN??0,10)||0,cN:parseInt(t.data.cN??0,10)||0,'
    'rob:t.data.rob||["low","low","low","low","low"]})',
)

# R7b: tE/cE were defaulted to 0, which manufactures a zero-event 2x2 table for
# every trial. That fake table is what fed the L'Abbe plot, the NNT curve and the
# fragility index. Leave them null so those panels can detect that there are no
# event data at all rather than reading "0 events in both arms".
h = edit(
    h, "R7b", "no fabricated zero-event 2x2 table on the continuous path",
    'd.tE=d.tE??0,d.cE=d.cE??0,d.tN=d.tN??0,d.cN=d.cN??0});',
    'd.tE=d.tE??null,d.cE=d.cE??null,d.tN=d.tN??0,d.cN=d.cN??0});',
)

# --- R4 -- do not clamp a mean difference to be positive --------------------
OLD_HKSJ = (
    'if(_isCont){const _hkLo=Math.max(.001,c.hksjLCI),_hkHi=Math.min(999,c.hksjUCI),'
    '_hkCapped=c.hksjLCI<.001||c.hksjUCI>999;'
    'hksjEl.innerText=`${_hkLo.toFixed(2)} — ${_hkHi>100?">100":_hkHi.toFixed(2)}${_hkCapped?" *":""}`}'
)
NEW_HKSJ = (
    # A mean difference is unbounded on both sides; the ratio positivity clamp
    # turned the true lower bound -64.13 into 0.00.
    'if(_isCont){hksjEl.innerText=`${c.hksjLCI.toFixed(2)} — ${c.hksjUCI.toFixed(2)}`}'
)
h = edit(h, "R4", "HKSJ bound no longer clamped to be positive on the MD scale",
         OLD_HKSJ, NEW_HKSJ)

# --- R3 -- forest caption: mean difference, not an exponentiated ratio ------
OLD_DESC = (
    'setDesc("desc-forest","Pooled "+emS+" = "+pOR.toFixed(2)+" ("+clPct+"% CI: "'
    '+Math.exp(pLogOR-zCrit*pSE).toFixed(2)+"–"+Math.exp(pLogOR+zCrit*pSE).toFixed(2)'
    '+") across "+data.length+" trials (N = "+totalN.toLocaleString()+"). "'
    '+(sig?"The result is statistically significant, suggesting a "+pctRed+"% "+dirWord+" "'
    '+effNoun+" with "+(RapidMeta.state.protocol?.int??"the intervention")+".":'
    '"The confidence interval crosses 1.0, indicating no statistically significant difference.")'
)
NEW_DESC = (
    'setDesc("desc-forest",("MD"===emS)?('
    # Continuous branch: raw bounds, null = 0, percentage points, and an
    # explicit statement that this is a biomarker difference and not a risk.
    '"Pooled mean difference = "+pOR.toFixed(2)+" percentage points ("+clPct+"% CI: "'
    '+(pLogOR-zCrit*pSE).toFixed(2)+" to "+(pLogOR+zCrit*pSE).toFixed(2)'
    '+") across "+data.length+" trials (N = "+totalN.toLocaleString()+"). "'
    '+((pLogOR+zCrit*pSE)<0||(pLogOR-zCrit*pSE)>0'
    '?"At Week 24 "+(RapidMeta.state.protocol?.int??"the intervention")+" produced a "'
    '+Math.abs(pOR).toFixed(1)+"-percentage-point "+(pOR<0?"greater reduction":"smaller reduction")'
    '+" in calculated LDL-C than the comparator; effects varied across trials."'
    ':"The confidence interval includes 0, the null value for a mean difference.")'
    '+" This is a lipid-biomarker difference in percentage points; it is not a risk ratio and "'
    '+"does not by itself quantify any cardiovascular event risk."'
    '):('
    '"Pooled "+emS+" = "+pOR.toFixed(2)+" ("+clPct+"% CI: "'
    '+Math.exp(pLogOR-zCrit*pSE).toFixed(2)+"–"+Math.exp(pLogOR+zCrit*pSE).toFixed(2)'
    '+") across "+data.length+" trials (N = "+totalN.toLocaleString()+"). "'
    '+(sig?"The result is statistically significant, suggesting a "+pctRed+"% "+dirWord+" "'
    '+effNoun+" with "+(RapidMeta.state.protocol?.int??"the intervention")+".":'
    '"The confidence interval crosses 1.0, indicating no statistically significant difference.")'
    ')'
)
h = edit(h, "R3", "forest caption states a mean difference (kills 5533% and 0.00-0.00)",
         OLD_DESC, NEW_DESC)

# `sig` is computed by exponentiating; make it scale-aware so the significance
# colouring and the subgroup captions stop testing a mean difference against 1.
OLD_SIG = (
    'sig=pOR<1&&Math.exp(pLogOR+zCrit*pSE)<1||pOR>1&&Math.exp(pLogOR-zCrit*pSE)>1,'
    'dirWord=pOR<1?"lower":pOR>1?"higher":"similar",'
)
NEW_SIG = (
    'sig=("MD"===RapidMeta.emLabel("short")'
    '?((pLogOR+zCrit*pSE)<0||(pLogOR-zCrit*pSE)>0)'
    ':(pOR<1&&Math.exp(pLogOR+zCrit*pSE)<1||pOR>1&&Math.exp(pLogOR-zCrit*pSE)>1)),'
    'dirWord=pOR<1?"lower":pOR>1?"higher":"similar",'
)
h = edit(h, "R3b", "significance test uses null = 0 on the MD scale",
         OLD_SIG, NEW_SIG)

# R8c: the "not computed" fallback hardcoded "k < 3", which is a false statement
# at k = 6. State the actual reason the test was not run.
h = edit(
    h, "R8c", "Egger fallback states the real reason instead of a false k < 3",
    '''eggerChip.innerHTML='<i class="fa-solid fa-chart-line" style="font-size:10px"></i> Egger’s: N/A (k < 3)';const robmeChip''',
    '''eggerChip.innerHTML=`<i class="fa-solid fa-chart-line" style="font-size:10px"></i> Egger’s: not computed${c.eggerResult?.reason?" ("+c.eggerResult.reason+")":""}`;const robmeChip''',
)

# ===========================================================================
# STAGE 2 -- retire the dichotomous-only outputs and fix the ratio-scale
# captions.  Nothing here is deleted from the DOM: the event-based panels are
# hidden at render time with an explicit reason, so the page cannot silently
# drop a panel a reader expected to find.
# ===========================================================================

# D1 -- hide the panels that require a 2x2 event table, and say why.
OLD_DESC_CHAIN = 'setDesc("desc-loo","Omitting each study in turn, pooled log"+emS+" ranges from "'
NEW_DESC_CHAIN = (
    '(()=>{const _cont="MD"===emS;'
    # L\'Abbe (event incidence), NNT curve (1/ARR) and the TSA Z-curve (RIS is
    # an event-count calculation) are undefined without event data.
    'const _evOnly=[["plot-labbe","L\'Abbe plot"],["plot-nnt","NNT / clinical-utility curve"],'
    '["plot-tsa","Trial Sequential Analysis (Z-curve)"]];'
    '_evOnly.forEach(([pid,label])=>{const el=document.getElementById(pid);if(!el)return;'
    'const panel=el.closest(".col-span-1")||el.parentElement;if(!panel)return;'
    'if(_cont){panel.dataset.suppressed="continuous";panel.style.display="none";'
    'const d=document.getElementById(pid.replace("plot-","desc-"));'
    'if(d)d.textContent=label+" not applicable: the pooled outcome is a continuous mean '
    'difference and these trials report no event counts.";}'
    'else{if("continuous"===panel.dataset.suppressed){panel.style.display="";'
    'delete panel.dataset.suppressed;}}});'
    # The fragility index is a count-modification procedure; it has no meaning here.
    'if(_cont){const fc=document.getElementById("chip-fragility")||document.getElementById("stat-fragility");'
    'if(fc){fc.className="stat-chip stat-chip-blue";fc.innerHTML='
    '\'<i class="fa-solid fa-shield-halved" style="font-size:10px"></i> '
    'Fragility: N/A (continuous outcome)\';}}'
    '})(),'
    'setDesc("desc-loo","Omitting each study in turn, pooled log"+emS+" ranges from "'
)
h = edit(h, "D1", "event-only panels hidden with a stated reason on the MD scale",
         OLD_DESC_CHAIN, NEW_DESC_CHAIN, marker="_evOnly")

# D2 -- leave-one-out caption: no exp(), no "log" prefix on a mean difference.
h = edit(
    h, "D2", "leave-one-out caption on the MD scale (was 'logMD ... (MD 0.00-0.00)')",
    'setDesc("desc-loo","Omitting each study in turn, pooled log"+emS+" ranges from "'
    '+looRange[0].toFixed(3)+" to "+looRange[1].toFixed(3)+" ("+emS+" "'
    '+Math.exp(looRange[0]).toFixed(2)+"–"+Math.exp(looRange[1]).toFixed(2)+"). "',
    'setDesc("desc-loo","MD"===emS'
    '?"Omitting each study in turn, the pooled mean difference ranges from "'
    '+looRange[0].toFixed(2)+" to "+looRange[1].toFixed(2)+" percentage points. "'
    ':"Omitting each study in turn, pooled log"+emS+" ranges from "'
    '+looRange[0].toFixed(3)+" to "+looRange[1].toFixed(3)+" ("+emS+" "'
    '+Math.exp(looRange[0]).toFixed(2)+"–"+Math.exp(looRange[1]).toFixed(2)+"). "',
)

# D3 -- cumulative caption: a cumulative mean difference is not a "log RR".
h = edit(
    h, "D3", "cumulative caption on the MD scale (was 'cumulative logRR')",
    '+" over time, with the final cumulative log"+emS+" = "+tr3X[tr3X.length-1].toFixed(3)+".',
    '+" over time, with the final cumulative "+("MD"===emS?"mean difference = "'
    '+tr3X[tr3X.length-1].toFixed(2)+" percentage points":"log"+emS+" = "'
    '+tr3X[tr3X.length-1].toFixed(3))+".',
)

# D4 -- Galbraith is valid for a continuous pool, but z is MD/SE, not logRR/SE.
h = edit(
    h, "D4", "Galbraith caption states the correct standardized effect",
    'setDesc("desc-galbraith","Studies plotted as standardized effect (z = log"+emS+"/SE)',
    'setDesc("desc-galbraith","Studies plotted as standardized effect '
    '(z = "+("MD"===emS?"MD":"log"+emS)+"/SE)',
)

# D5 -- the funnel caption asserted absence of publication bias unconditionally,
# then appended an Egger result that could contradict it in the same sentence.
h = edit(
    h, "D5", "funnel caption no longer asserts absence of publication bias a priori",
    'setDesc("desc-funnel","Contour-enhanced funnel plot with significance regions '
    '(p < 0.01, 0.05, 0.10). Visual symmetry around the pooled estimate suggests absence '
    'of publication bias."',
    'setDesc("desc-funnel","Contour-enhanced funnel plot with significance regions '
    '(p < 0.01, 0.05, 0.10). Funnel asymmetry is assessed by the Egger test reported below, '
    'not by visual inspection alone; with k < 10 both are exploratory and cannot establish '
    'either presence or absence of publication bias."',
)

# D6 -- the R validation script built an escalc() 2x2 call over null event
# fields.  Emit the generic inverse-variance script that actually reproduces
# the pooled number when the outcome is continuous.
OLD_R = (
    'const emR=effectSpec.effective,rScript=`# RapidMeta v11.0 R-Validation (DL + HKSJ + Bayesian) — ${emR}'
)
NEW_R = (
    'const emR=effectSpec.effective;'
    'if("MD"===emR){const _md=trials.map(t=>{const o=(t.data?.allOutcomes??[])'
    '.find(x=>null!=x?.md)??t.data;return{n:escStr(t.data?.name||t.id),md:o?.md,se:o?.se}})'
    '.filter(d=>null!=d.md&&null!=d.se);'
    'const rScriptMD=`# RapidMeta R-Validation — generic inverse-variance, continuous outcome\\n\\n\\n'
    '# Outcome: percent change in calculated LDL-C from baseline to Week 24 (ITT).\\n\\n\\n'
    '# yi are mean differences in PERCENTAGE POINTS; the null value is 0, not 1.\\n\\n\\n'
    'library(metafor)\\n\\n\\ndat <- data.frame(\\n\\n\\n'
    '  trial = c(${_md.map(d=>`"${d.n}"`).join(",")}),\\n\\n\\n'
    '  yi = c(${_md.map(d=>d.md).join(",")}),\\n\\n\\n'
    '  sei = c(${_md.map(d=>d.se).join(",")})\\n\\n\\n)\\n\\n\\n'
    '# Primary: REML random effects with Hartung-Knapp-Sidik-Jonkman inference\\n\\n\\n'
    'res <- rma(yi = yi, sei = sei, data = dat, method = "REML", test = "knha", level = ${100*cl})\\n\\n\\n'
    'print(res)\\n\\n\\n'
    '# Pre-specified sensitivity: DerSimonian-Laird tau^2\\n\\n\\n'
    'res_dl <- rma(yi = yi, sei = sei, data = dat, method = "DL", level = ${100*cl})\\n\\n\\n'
    'print(res_dl)\\n\\n\\n'
    '# Prediction interval (Cochrane v6.5, t with k-1 df)\\n\\n\\npredict(res, level = ${100*cl})\\n\\n\\n'
    '# Small-study effects (exploratory at k < 10)\\n\\n\\nregtest(res, model = "lm")\\n\\n\\n'
    '# Forest plot on the mean-difference scale\\n\\n\\n'
    'forest(res, slab = dat$trial, xlab = "Mean difference in LDL-C change (percentage points)")`;'
    'return void(document.getElementById("r-code-text").innerText=rScriptMD)}'
    'const rScript=`# RapidMeta v11.0 R-Validation (DL + HKSJ + Bayesian) — ${emR}'
)
h = edit(h, "D6", "R validation emits continuous GIV code (was escalc over null 2x2)",
         OLD_R, NEW_R)

# ===========================================================================
# STAGE 3 -- the reader-facing surfaces (visual abstract, scientific verdict,
# waiting-room / patient panel).  These only populate after "Generate Output",
# which is why they carried the worst of the errors: "5533% lower risk",
# "1 out of 100 patients benefit", "0.95% CI", "I2 undefined%".
# ===========================================================================

# P1/P2 -- visual abstract: confLevel is stored as a FRACTION (0.95), so
# `${r.confLevel??"95"}% CI` rendered "0.95% CI"; and the field is I2, not i2,
# so `${r.i2}%` rendered "undefined%".  Also round the CI for display.
OLD_VA = (
    # NOTE: this sits inside a comma-expression chain, so the chain must be
    # terminated with ';' before any `const` can be introduced.
    'document.getElementById("va-or").innerText=r.or,'
    'document.getElementById("va-ci").innerText=`${r.lci} — ${r.uci} (${r.confLevel??"95"}% CI)`,'
    'document.getElementById("va-i2").innerText=`${r.i2}%`;const sofCIHeader='
    'document.getElementById("sof-ci-header");sofCIHeader&&(sofCIHeader.innerText=`${r.confLevel??"95"}% CI`);'
)
NEW_VA = (
    'document.getElementById("va-or").innerText=r.or;'
    'const _clPct=(v=>{const n=parseFloat(v);return Number.isFinite(n)?(n<=1?Math.round(100*n):Math.round(n)):95})'
    '(r.confLevel),_fmt=v=>{const n=parseFloat(v);return Number.isFinite(n)?n.toFixed(2):String(v??"--")};'
    'document.getElementById("va-ci").innerText=`${_fmt(r.lci)} — ${_fmt(r.uci)} (${_clPct}% CI)`,'
    'document.getElementById("va-i2").innerText=(()=>{const _i2=r.I2??r.i2;const n=parseFloat(_i2);'
    'return Number.isFinite(n)?`${n.toFixed(0)}%`:"--"})();const sofCIHeader='
    'document.getElementById("sof-ci-header");sofCIHeader&&(sofCIHeader.innerText=`${_clPct}% CI`);'
)
h = edit(h, "P1/P2", "visual abstract: real 95% CI label, rounded bounds, real I2",
         OLD_VA, NEW_VA, marker="_clPct=(v=>")

# P3 -- scientific verdict: on the MD scale interpretRelativeEffect() returns
# 100*(1-(-54.33)) = 5533, and the endpoint name came from a cardiovascular
# template map. Both are replaced for continuous pools.
OLD_VERDICT = (
    'effect=interpretRelativeEffect(r.or,r.lci,r.uci),neutralDirection=parseFloat(r.or)<=1?"reduction":"increase",'
    'verdictText="benefit"===effect.direction?`Evidence base consisting of ${phaseText} trials shows a robust '
    '${effect.pct}% reduction in ${verdictOutcome[outcomeKey]??"the selected endpoint"}.`'
)
NEW_VERDICT = (
    'effect=interpretRelativeEffect(r.or,r.lci,r.uci),neutralDirection=parseFloat(r.or)<=1?"reduction":"increase",'
    '_isMD="MD"===RapidMeta.emLabel("short"),'
    '_mdPt=parseFloat(r.or),_mdLo=parseFloat(r.lci),_mdHi=parseFloat(r.uci),'
    '_mdOutcome=RapidMeta.outcomeLabel?.(outcomeKey)||"the registered continuous outcome",'
    'verdictText=_isMD?('
    '(_mdHi<0||_mdLo>0)'
    '?`Evidence base consisting of ${phaseText} trials shows a ${Math.abs(_mdPt).toFixed(1)}-percentage-point '
    '${_mdPt<0?"greater reduction":"greater increase"} in ${_mdOutcome} than the comparator '
    '(mean difference, ${_clPct}% CI ${_mdLo.toFixed(2)} to ${_mdHi.toFixed(2)}); effects varied across trials. '
    'This is a lipid-biomarker difference and does not by itself establish a cardiovascular outcome benefit.`'
    ':`Evidence base consisting of ${phaseText} trials estimates a mean difference of ${_mdPt.toFixed(2)} '
    'percentage points in ${_mdOutcome}, but the ${_clPct}% CI includes 0.`'
    '):"benefit"===effect.direction?`Evidence base consisting of ${phaseText} trials shows a robust '
    '${effect.pct}% reduction in ${verdictOutcome[outcomeKey]??"the selected endpoint"}.`'
)
h = edit(h, "P3", "scientific verdict states a mean difference (was '5533% reduction in the matched CV composite')",
         OLD_VERDICT, NEW_VERDICT)

# P4 -- waiting room: the NNT pictogram, the relative-risk-reduction gauge and
# the per-100 icon array are all dichotomous constructions.  Route continuous
# pools to a panel that states the biomarker difference in plain language.
OLD_WR = 'renderWaitingRoom(r,included){const orVal=parseFloat(r.or),'
NEW_WR = (
    '_renderWaitingRoomMD(r,included){const set=(id,t)=>{const e=document.getElementById(id);e&&(e.textContent=t)},'
    'hide=id=>{const e=document.getElementById(id);if(e){const p=e.closest("div")||e;p.style.display="none"}};'
    'const pt=parseFloat(r.or),lo=parseFloat(r.lci),hi=parseFloat(r.uci),sig=hi<0||lo>0,'
    'oc=RapidMeta.outcomeLabel?.(String(RapidMeta.state.selectedOutcome??"default"))||"the registered outcome";'
    # the pictogram and gauge have no continuous meaning -> remove them outright
    'hide("wr-icon-array");hide("wr-gauge-canvas");'
    'set("wr-icon-label","Not applicable: this review pools a continuous laboratory measurement, '
    'so there is no count of patients with or without an event.");'
    'set("wr-gauge-value",(pt<0?"":"+")+pt.toFixed(1)+" pp");'
    'set("wr-gauge-text",Math.abs(pt).toFixed(1)+"-percentage-point "+(pt<0?"greater reduction":"greater increase")'
    '+" in LDL cholesterol vs placebo");'
    'set("wr-or-display",r.or);'
    'const dot=document.getElementById("wr-signal-dot"),st=document.getElementById("wr-signal-text"),'
    'col=sig?(pt<0?"#22c55e":"#ef4444"):"#eab308";'
    'dot&&(dot.style.background=col);st&&(st.textContent=sig?(pt<0?"Significant Reduction":"Significant Increase")'
    ':"Not Significant",st.style.color=col);'
    'set("wr-plain-message",sig'
    '?"Across "+r.k+" trials with "+r.n+" patients, alirocumab lowered LDL cholesterol by about "'
    '+Math.abs(pt).toFixed(0)+" percentage points more than placebo at 24 weeks. That is a cholesterol '
    'measurement, not a count of heart attacks or strokes — these six trials did not measure whether '
    'that difference prevents cardiovascular events."'
    ':"Across "+r.k+" trials with "+r.n+" patients, the difference in LDL cholesterol change was not '
    'statistically distinguishable from no difference.")},'
    'renderWaitingRoom(r,included){if(r?.isContinuous||"MD"===RapidMeta.emLabel("short"))'
    'return this._renderWaitingRoomMD(r,included);const orVal=parseFloat(r.or),'
)
h = edit(h, "P4", "waiting room: no NNT pictogram / RRR gauge on a continuous outcome",
         OLD_WR, NEW_WR, marker="_renderWaitingRoomMD")

# ===========================================================================
# STAGE 4 -- the long-form narrative.  renderNarrative() carried most of the
# remaining defects at once: "0.95% CI", "I2 undefined%", "5533% reduction",
# the CKD/cardiovascular-composite endpoint name, the NNT sentence, the
# fragility sentence and "the null value of 1.0 in favor of
# alirocumab_lipid_auto".  Continuous pools get their own narrative.
# ===========================================================================

# N0 -- one shared confidence-level formatter. confLevel is a FRACTION (0.95);
# every `r.confLevel??"95"` therefore printed "0.95% CI".
h = edit(
    h, "N0", "global confidence-level percentage helper",
    'function renderPlotNotice(id,msg){',
    'function _clPctOf(v){const n=parseFloat(v);'
    'return Number.isFinite(n)?(n<=1?Math.round(100*n):Math.round(n)):95}'
    'function renderPlotNotice(id,msg){',
    marker="function _clPctOf",
)
h = edit(
    h, "N0b", 'all "0.95% CI" labels render as "95% CI"',
    'r.confLevel??"95"', '_clPctOf(r.confLevel)', expect=4,
)

# N1 -- continuous narrative.
OLD_NARR = 'renderNarrative(r,included){const effect=interpretRelativeEffect(r.or,r.lci,r.uci),'
NEW_NARR = (
    '_renderNarrativeMD(r,included){const set=(id,t)=>{const e=document.getElementById(id);e&&(e.textContent=t)},'
    'ciPct=_clPctOf(r.confLevel),i2n=parseFloat(r.I2??r.i2),'
    'pt=parseFloat(r.or),lo=parseFloat(r.lci),hi=parseFloat(r.uci),sig=hi<0||lo>0,'
    'oc=RapidMeta.outcomeLabel?.(String(RapidMeta.state.selectedOutcome??"default"))'
    '||"the registered continuous outcome",'
    '_e=escapeHtml,'
    'i2Interp=i2n<25?"negligible":i2n<50?"low":i2n<75?"moderate":"substantial";'
    'set("nyt-subhead",`${r.k} randomized controlled trials enrolling ${r.n} patients, '
    'synthesized using random-effects meta-analysis of mean differences.`);'
    'set("nyt-kn-or",r.or);'
    # NNT is undefined for a continuous outcome; label the tile honestly.
    'set("nyt-kn-nnt","n/a");'
    'const nntLbl=document.getElementById("nyt-kn-nnt")?.nextElementSibling;'
    'nntLbl&&(nntLbl.textContent="NNT (not applicable)");'
    'set("nyt-kn-i2",Number.isFinite(i2n)?i2n.toFixed(0)+"%":"--");'
    'set("nyt-kn-k",r.k);'
    'const orLbl=document.getElementById("nyt-kn-or-label");'
    'orLbl&&(orLbl.textContent="Pooled mean difference (pp)");'
    'const hksjNote=Number.isFinite(parseFloat(r.hksjLCI))'
    '?` The HKSJ-adjusted ${ciPct}% CI is <span class="nyt-stat-inline">'
    '${_e(parseFloat(r.hksjLCI).toFixed(2))} to ${_e(parseFloat(r.hksjUCI).toFixed(2))}</span>, '
    'accounting for estimation uncertainty in between-study variance.`:"",'
    'piNote=Number.isFinite(parseFloat(r.piLCI))'
    '?` The ${ciPct}% prediction interval (<span class="nyt-stat-inline">'
    '${_e(parseFloat(r.piLCI).toFixed(2))} to ${_e(parseFloat(r.piUCI).toFixed(2))}</span>) '
    'indicates the range of true effects expected in a future similar study.`:"",'
    'egg=r.eggerResult,'
    'eggerNote=egg&&egg.sufficient'
    '?` Egger\\u2019s regression on the mean-difference scale gives intercept '
    '${_e(egg.intercept.toFixed(2))}, p = ${_e(egg.pValue<.001?"<0.001":egg.pValue.toFixed(3))}; '
    'with k = ${_e(r.k)} (< 10) this test has low power and is reported as exploratory only, '
    'so it can neither establish nor exclude small-study effects.`:"",'
    'narrative=`Alirocumab ${sig'
    '?`produced a statistically significant <span class="nyt-stat-inline">'
    '${_e(Math.abs(pt).toFixed(1))} percentage-point</span> '
    '${pt<0?"greater reduction":"greater increase"} in ${_e(oc)}`'
    ':`was associated with a <span class="nyt-stat-inline">${_e(pt.toFixed(2))} percentage-point</span> '
    'difference in ${_e(oc)} that was not statistically distinguishable from no difference`} '
    'compared with placebo across <span class="nyt-stat-inline">${_e(r.k)}</span> trials enrolling '
    '<span class="nyt-stat-inline">${_e(r.n)}</span> patients. The pooled mean difference was '
    '<span class="nyt-stat-inline">${_e(pt.toFixed(2))}</span> percentage points (${ciPct}% CI: '
    '<span class="nyt-stat-inline">${_e(lo.toFixed(2))} to ${_e(hi.toFixed(2))}</span>), '
    '${sig?"with the confidence interval excluding the null value of 0":"with the confidence interval including the null value of 0"}.'
    '${hksjNote}${piNote} Heterogeneity was ${_e(i2Interp)} (I\\u00b2 = '
    '<span class="nyt-stat-inline">${_e(Number.isFinite(i2n)?i2n.toFixed(0):"--")}%</span>), so the '
    'per-trial effects are not interchangeable and the prediction interval is the more honest summary '
    'of what a new trial might show.${eggerNote} This is a lipid-biomarker endpoint measured at 24 weeks; '
    'none of these six trials was designed or powered for cardiovascular events, so no statement about '
    'cardiovascular risk follows from this pooled estimate.`;'
    'document.getElementById("nyt-narrative").innerHTML=narrative;'
    'set("nyt-annotation",`Analysis performed using a REML random-effects model of mean differences '
    '(HKSJ-adjusted) with ${ciPct}% confidence intervals. HKSJ correction applied with max(1, q*) '
    'safeguard. Prediction intervals computed with k\\u22121 degrees of freedom per the Cochrane '
    'Handbook (v6.5).`)},'
    'renderNarrative(r,included){'
    'if(r?.isContinuous||"MD"===RapidMeta.emLabel("short"))return this._renderNarrativeMD(r,included);'
    'const effect=interpretRelativeEffect(r.or,r.lci,r.uci),'
)
h = edit(h, "N1", "long-form narrative rewritten for a continuous outcome",
         OLD_NARR, NEW_NARR, marker="_renderNarrativeMD")

# ===========================================================================
# STAGE 5 -- residual leaks on the summary table and the export paths.
# ===========================================================================

# X1 -- neither engine ever sets `i2`; both return `I2`. Every `r.i2` read was
# therefore undefined, which is why the SoF row and the exports printed
# "undefined%". This is a read-side fix and changes no computation.
# The replacement itself ends in "r.i2", so the rewrite must skip any occurrence
# that is ALREADY preceded by "r.I2??" -- otherwise a second pass would produce
# (r.I2??(r.I2??r.i2)). A negative lookbehind makes this self-idempotent, and
# unlike a whole-file guard it is not tripped by the (r.I2??r.i2) that earlier
# stages of this script legitimately introduce.
_X1 = re.compile(r"(?<!r\.I2\?\?)\br\.i2\b")
n_i2 = len(_X1.findall(h))
if n_i2:
    h = _X1.sub("(r.I2??r.i2)", h)
    applied.append(("X1", "r.i2 -> (r.I2 ?? r.i2) at %d sites (was 'undefined%%')" % n_i2))
else:
    skipped.append(("X1", "r.i2 -> (r.I2 ?? r.i2)"))

# X2 -- confidence level on the two export paths (JSON bundle, HTML report)
# printed the fraction, e.g. "0.95%".
h = edit(
    h, "X2", "JSON export states 95% not 0.95%",
    'confLevel:r.confLevel+"%"', 'confLevel:_clPctOf(r.confLevel)+"%"',
)
h = edit(
    h, "X2b", "HTML export states 95% not 0.95%",
    '(${r.confLevel}% CI:', '(${_clPctOf(r.confLevel)}% CI:',
)

# X3 -- the outcome summary row printed full float precision.
h = edit(
    h, "X3", "outcome summary row rounds the CI",
    '<td class="p-3 text-right font-mono">${r.lci} - ${r.uci}</td>',
    '<td class="p-3 text-right font-mono">${Number.isFinite(parseFloat(r.lci))'
    '?parseFloat(r.lci).toFixed(2)+" to "+parseFloat(r.uci).toFixed(2)'
    ':`${r.lci} - ${r.uci}`}</td>',
)

# X4 -- the internal slug leaked into reader-visible CT.gov panel text.
h = edit(
    h, "X4", "CT.gov delta panel names the drug, not the internal slug",
    '`${tracked} CT.gov-tracked alirocumab_lipid_auto record${1===tracked?"":"s"} are being monitored`',
    '`${tracked} CT.gov-tracked alirocumab record${1===tracked?"":"s"} are being monitored`',
)
h = edit(
    h, "X4b", "operator hint no longer exposes the internal slug as prose",
    'text:"Run `python ctgov_history_harvest.py` for the alirocumab_lipid_auto watchlist, '
    'then import the generated history pack before claiming true protocol drift."',
    'text:"Harvest the CT.gov version history for this review\'s watchlist and import the '
    'generated history pack before claiming true protocol drift."',
)

# ===========================================================================
# STAGE 6 -- GRADE.  The continuous dispatch lives in AnalysisEngine.run(),
# but GradeProfileEngine.generateAll() calls computeCore() directly and so
# pooled these six trials as a 2x2 OR over null event fields.  Everything
# downstream then read NaN:
#   * "MD NaN [NaN, NaN]" in the relative-effect column;
#   * _plainLanguage() compares lci<1 && uci<1 -- every NaN comparison is
#     false, so it fell through to "probably results in little to no
#     difference", the exact opposite of a -54 pp effect;
#   * computeGradeAssessment() could not see the (NaN) CI, so it never applied
#     the imprecision/inconsistency downgrades and returned MODERATE, while
#     the analysis tab -- which does use the continuous pool -- returned LOW.
#     That is the source of the Low-vs-Moderate contradiction.
# ===========================================================================
h = edit(
    h, "G1", "GRADE profile pools continuous outcomes with the continuous engine",
    'if(0===analyzed.length)return;const c=AnalysisEngine.computeCore(analyzed);',
    'if(0===analyzed.length)return;'
    'const _isCont=void 0!==ContinuousMDEngine&&analyzed.some(t=>{'
    'const o=t.data?.allOutcomes?.find(x=>x.shortLabel===oc.key);'
    'return o&&"CONTINUOUS"===String(o.type??"").toUpperCase()});'
    'const c=_isCont?(ContinuousMDEngine.pool(oc.key,analyzed)||AnalysisEngine.computeCore(analyzed))'
    ':AnalysisEngine.computeCore(analyzed);if(!c)return;',
    marker="_isCont=void 0!==ContinuousMDEngine",
)

# G2 -- absolute-risk columns are undefined without event data; print "n/a"
# rather than a fabricated 0 per 1000.
h = edit(
    h, "G2", "GRADE absolute-risk columns read n/a on a continuous outcome",
    'cerPer1000:Math.round(1e3*cer),ardPer1000:`${ardPt} (${ardLo} to ${ardHi})`,',
    'cerPer1000:c.isContinuous?"n/a":Math.round(1e3*cer),'
    'ardPer1000:c.isContinuous?"n/a (continuous outcome)":`${ardPt} (${ardLo} to ${ardHi})`,',
)

# G3 -- plain language for a mean difference. The null is 0, and the effect is
# expressed in percentage points, not as a percentage of a risk.
h = edit(
    h, "G3", "GRADE plain language handles a mean difference (was 'little to no difference')",
    '_plainLanguage(or,lci,uci,outcome,certainty="MODERATE"){const ocLow=String(outcome??"").toLowerCase(),'
    '_drug=RapidMeta.state.protocol?.int??"The intervention",',
    '_plainLanguage(or,lci,uci,outcome,certainty="MODERATE"){const ocLow=String(outcome??"").toLowerCase(),'
    '_drug=RapidMeta.state.protocol?.int??"The intervention",'
    '_isMD="MD"===RapidMeta.emLabel("short"),'
    '_hedgeMD="HIGH"===certainty?"":"MODERATE"===certainty?"probably ":"LOW"===certainty?"may ":"",'
    '_mdMsg=(()=>{if(!_isMD)return null;'
    'const p=parseFloat(or),l=parseFloat(lci),u=parseFloat(uci);'
    'if(![p,l,u].every(Number.isFinite))return `The pooled effect on ${ocLow} could not be estimated.`;'
    'if("VERY LOW"===certainty)return `The evidence is very uncertain about the effect of ${_drug} on ${ocLow}.`;'
    'return (u<0||l>0)'
    '?`${_drug} ${_hedgeMD}produces a ${Math.abs(p).toFixed(1)}-percentage-point '
    '${p<0?"greater reduction":"greater increase"} in ${ocLow} than the comparator '
    '(mean difference ${p.toFixed(2)}, 95% CI ${l.toFixed(2)} to ${u.toFixed(2)}). '
    'This is a laboratory measurement, not a clinical event rate.`'
    ':`${_drug} ${_hedgeMD}results in little to no difference in ${ocLow} '
    '(mean difference ${p.toFixed(2)}, 95% CI ${l.toFixed(2)} to ${u.toFixed(2)}).`})();'
    'if(_mdMsg)return _mdMsg;',
    marker="_mdMsg",
)

# ===========================================================================
# STAGE 7 -- protocol, eligibility and the integrity surfaces.
# ===========================================================================

# E1 -- eligibility required event data that none of the six trials provides.
# The protocol is rewritten around the lipid-efficacy question the review
# actually answers.  A CV-outcomes review of alirocumab (ODYSSEY OUTCOMES) is a
# different review with a different corpus and is not interchangeable.
h = edit(
    h, "E1", "eligibility rebuilt around lipid efficacy (was: requires 2x2 event data)",
    '<td class="p-3 text-slate-300">&ge;1 clinical cardiovascular or renal endpoint with '
    'extractable 2&times;2 data</td><td class="p-3 text-slate-400">Biomarker-only, PK-only, '
    'no event data</td>',
    '<td class="p-3 text-slate-300">Percent change in calculated LDL-C from baseline to '
    'Week&nbsp;24 (ITT), reported as a between-group mean difference with a variance or '
    'confidence interval</td><td class="p-3 text-slate-400">No Week-24 LDL-C contrast; '
    'lipid change reported without any measure of precision; single-arm change scores only. '
    '<em class="text-slate-500">Clinical cardiovascular event outcomes are outside the scope '
    'of this review and are addressed by a separate CV-outcomes review; the two are not '
    'interchangeable.</em></td>',
)

# E2 -- corpus policy: eligibility is by PICO/scope and data availability, never
# by date. The "Pre-2015" exclusion is removed outright.
h = edit(
    h, "E2", "pre-2015 date exclusion removed (corpus policy: no date-based eligibility)",
    '<td class="p-3 text-slate-400">Pre-2015; duplicate cohorts; editorials, letters, reviews</td>',
    '<td class="p-3 text-slate-400">Duplicate cohorts; editorials, letters, reviews. '
    '<em class="text-slate-500">No publication-date restriction is applied: eligibility is '
    'determined by PICO/scope and data availability only.</em></td>',
)

# E3 -- the subgroup plan was inherited from a respiratory template.
h = edit(
    h, "E3", "subgroup plan was asthma/COPD template residue (eosinophils, ICS use)",
    'value="Blood eosinophils, smoking status, ICS use" aria-label="Subgroup analyses"',
    'value="Dose regimen (150 mg Q2W fixed vs 75 mg Q2W with blinded up-titration); '
    'familial hypercholesterolaemia vs non-FH population; region" aria-label="Subgroup analyses"',
)

# E4 -- the statistical protocol was written around HR/RR/OR and 2x2 counts.
h = edit(
    h, "E4", "statistical protocol prespecifies ONE primary continuous estimator",
    '<td id="protocol-em-desc" class="p-3 text-slate-300">Primary analysis uses published '
    'hazard ratios when available; otherwise risk ratios from 2x2 counts. Odds ratios are '
    'retained for sensitivity analysis.</td>',
    '<td id="protocol-em-desc" class="p-3 text-slate-300">Between-group <strong>mean '
    'difference in percentage points</strong> for percent change in calculated LDL-C from '
    'baseline to Week&nbsp;24, pooled by generic inverse-variance. The null value is 0. '
    'Ratio measures (HR/RR/OR), risk differences and NNT are not defined for this estimand '
    'and are not reported.</td>',
)
h = edit(
    h, "E4b", "primary tau2 estimator prespecified as REML with DL as labelled sensitivity",
    '<td class="p-3 text-slate-300">REML random-effects, HKSJ-adjusted (inverse-variance weighting)</td>',
    '<td class="p-3 text-slate-300"><strong>Primary:</strong> random-effects generic '
    'inverse-variance with <strong>REML</strong> &tau;&sup2; and Hartung-Knapp-Sidik-Jonkman '
    'inference (t, df = k&minus;1). <strong>Pre-specified sensitivity:</strong> '
    'DerSimonian-Laird &tau;&sup2;, reported separately and never substituted for the '
    'primary estimate.</td>',
)
h = edit(
    h, "E4c", "heterogeneity row names the primary estimator (was 'DL estimator')",
    '<td class="p-3 text-slate-300">Cochran Q (p-value), I&sup2; (%), &tau;&sup2; (DL estimator)</td>',
    '<td class="p-3 text-slate-300">Cochran Q (p-value), I&sup2; (%) with Q-profile CI, '
    '&tau;&sup2; (REML primary; DL reported as sensitivity)</td>',
)

# E5 -- "Post-2015 Enrollment" conflated publication year with enrolment.
h = edit(
    h, "E5", "acquisition-era tile no longer confuses publication year with enrolment",
    '<div class="va-label">Acquisition Era</div><div class="va-value">Post-2015 Enrollment</div>',
    '<div class="va-label">Primary Publication Years</div><div class="va-value">2015&ndash;2016</div>',
)

# E6 -- a git commit timestamp is a change-tracking record, not a prospective
# registration; PROSPERO equivalence is not a claim this page can make.
h = edit(
    h, "E6", "removed the 'equivalent to PROSPERO' claim",
    'Per ICMJE 2023, GitHub commit hash + timestamp constitutes a verifiable pre-registration '
    'record equivalent to PROSPERO for tracking outcome / eligibility / analysis-plan changes.',
    'The GitHub commit hash and timestamp provide a verifiable, tamper-evident record of when '
    'each protocol change was made. This is a change-tracking record only: it is created '
    'alongside the analysis rather than before it, and it is <strong>not</strong> equivalent '
    'to a prospective PROSPERO or OSF registration. This review is not prospectively registered.',
)

# E7 -- the integrity badge asserted "INTERNAL CHECKS PASSED" over a hardcoded
# "Trials: 2" while the ledger holds 6, and window.__verdict said the same.
# Both surfaces are corrected to the real count and to a state the evidence
# supports.  n_trials_seen and the P1/P2 counts were all 2 for the same reason:
# they are inherited boilerplate, not measurements of this page.
h = edit(
    h, "E7", "integrity badge: real trial count, no unearned green pass",
    '<div id="rapidmeta-integrity-badge" role="status" style="background:#15803d;',
    '<div id="rapidmeta-integrity-badge" role="status" style="background:#b45309;',
)
h = edit(
    h, "E7b", "badge text states 6 trials and what has NOT been done",
    '<strong style="font-size:14px;letter-spacing:0.04em;">INTERNAL CHECKS PASSED</strong>'
    '<span style="font-size:11.5px;">Fabrication-risk score: <strong>0.275</strong> '
    '· Trials: <strong>2</strong></span>',
    '<strong style="font-size:14px;letter-spacing:0.04em;">AUTOMATED CHECKS ONLY – '
    'NOT INDEPENDENTLY REVIEWED</strong><span style="font-size:11.5px;">Trials: '
    '<strong>6</strong> · human dual screening: <strong>0/6</strong> · '
    'human dual extraction: <strong>0/6</strong> · human risk-of-bias: '
    '<strong>0/6</strong> (registry-derived defaults)</span>',
)
h = edit(
    h, "E7d", "badge body states what the automated audit did and did not cover",
    'Multi-source audit completed (AACT 2026-04-12 + PubMed + 10 internal-consistency rounds). '
    'Routine pre-publication human spot-check recommended.',
    'All six included effect estimates and 95% CIs were verified against the '
    'ClinicalTrials.gov posted results for their NCT records and match exactly. '
    'Screening, data extraction and risk-of-bias assessment have NOT been independently '
    'performed by a second human reviewer; the risk-of-bias domains shown are '
    'registry-derived defaults, not human judgements. Do not cite this page as a '
    'peer-reviewed or independently verified synthesis.',
)
h = edit(
    h, "E7c", "window.__verdict reports 6 trials and an unverified state",
    'window.__verdict = {"verdict": "STABLE", "counts": {"P0_internal": 0, '
    '"P0_aact_nct_missing": 0, "P0_grim": 0, "P1_aact_concord": 2, "P1_fi_critical": 0, '
    '"P1_fi_warn": 0, "P1_pi_gap": 0, "P2_evidence_incomplete": 2, "n_trials_seen": 2, '
    '"P2_aact_advisory": 2}, "reasons": ["2 AACT title/registry advisory", '
    '"2 AACT outcome-direction divergence(s)", "2 trial(s) missing evidence rows"], "p0_total": 0};',
    'window.__verdict = {"verdict": "UNVERIFIED", "counts": {"P0_internal": 0, '
    '"P0_aact_nct_missing": 0, "P0_grim": 0, "P1_aact_concord": 0, "P1_fi_critical": 0, '
    '"P1_fi_warn": 0, "P1_pi_gap": 0, "P2_evidence_incomplete": 0, "n_trials_seen": 6, '
    '"P2_aact_advisory": 0}, "reasons": ["6/6 included trials verified against '
    'ClinicalTrials.gov posted results (effect estimates and 95% CIs match exactly)", '
    '"0/6 dual human screening", "0/6 dual human extraction", '
    '"0/6 human risk-of-bias assessment - RoB domains are registry-derived defaults", '
    '"continuous mean-difference pool; no event data and therefore no fragility index, '
    'NNT or TSA"], "p0_total": 0};',
)

# ===========================================================================
# STAGE 8 -- the shared vendor stat panels.
#
# vendor/*.js panels under #stats-tab-host assume a 2x2 corpus. Over this
# review's null event fields they produced, verified live before this fix:
#     r-validation-badge      OR 0.12 [0.00 - 5.2e+31] . k=3   (wrong k too)
#     grade-sof-panel         Certainty: Moderate . OR 0.50 [0.10-2.51]
#     rr-sensitivity-panel    RR 0.51 [0.10-2.50] vs OR 0.50
#     bayesian-sensitivity    OR 0.49 [0.09-2.69]
#     nnt-panel               NNT undefined . pooled RD 0.0%
#     cumulative-ma-panel     "CI still crosses null"  (it does not)
#     pi-convention-panel     PI [0.06, 4.13] . scale log-OR
#     tau2-qprofile-panel     tau2 = 0 . scale log-OR      (real REML tau2 = 71.22)
#     funnel-diagnostics      Peters test -- defined for binary outcomes only
#
# These are corpus-shared files, so rather than edit them this suppressor lives
# in the app and hides them only when THIS page's pool is continuous. Nothing
# is lost: the Analysis tab already reports the prediction interval, tau2,
# cumulative MA, funnel and Egger on the mean-difference scale, and the
# vendor continuous-outcome-panel already reports MD -54.33 correctly.
# ===========================================================================
SUPPRESSOR = """
<script>
/* Continuous-outcome guard for the shared vendor stat panels.
   Scoped to this page; vendor files are untouched. */
(function () {
  var RATIO_ONLY = {
    'r-validation-badge':        'R metafor cross-validation runs an escalc() 2x2 model; this review has no event counts. The continuous validation script is in Analysis \\u2192 R code.',
    'grade-sof-panel':           'The GRADE SoF panel computes risk-with-control / risk-with-intervention from event counts. See the GRADE Evidence Profile in Scientific Output, which reports this outcome as a mean difference.',
    'rr-sensitivity-panel':      'RR-vs-OR sensitivity is undefined without event counts.',
    'bayesian-sensitivity-panel':'This Bayesian panel places its prior on a log-odds scale.',
    'nnt-panel':                 'NNT and risk difference are undefined for a continuous outcome.',
    'cumulative-ma-panel':       'This panel accumulates on the log-OR scale. The cumulative mean-difference plot is in Analysis \\u2192 panel 3.',
    'pi-convention-panel':       'This panel reports the prediction interval on the log-OR scale. The mean-difference prediction interval is in Analysis \\u2192 Stats.',
    'tau2-qprofile-panel':       'This panel estimates tau-squared on the log-OR scale. The mean-difference tau-squared (REML) is in Analysis \\u2192 Stats.',
    'funnel-diagnostics-panel':  "Peters' test is defined for binary outcomes only. Egger's test on the mean-difference scale is reported in Analysis \\u2192 Stats."
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

# There are several "</body>" strings in the file (export templates embed one),
# so target the document's own closing tag: the last one.
if "rmContSuppressed" in h:
    skipped.append(("V1", "ratio-only vendor stat panels suppressed"))
else:
    _idx = h.rfind("</body>")
    if _idx == -1:
        failed.append(("V1", "vendor panel suppressor", "no </body> found"))
    else:
        h = h[:_idx] + SUPPRESSOR + h[_idx:]
        applied.append(("V1", "ratio-only vendor stat panels suppressed with a stated reason"))

# ===========================================================================
# STAGE 9 -- PRISMA flow.
#
# On a clean load the diagram rendered:
#     identified 0 | screened 0 | full-text 6 | included 6 | synthesis 6
# which is arithmetically impossible -- more records were included than were
# ever identified. The cause is the fallback below: it fires when
# RapidMeta.state.trials is still empty (the diagram renders before the
# canonical seed populates the ledger) and fills in the downstream boxes from
# realData while leaving the upstream boxes at a literal 0.
#
# NOTE ON THE EXTERNAL REVIEW: it reported "144 identified, 0 duplicates, 25
# excluded at screening -> 119 full-text, 25 excluded -> 94 remaining but 6
# included (88 unaccounted)". Those numbers are NOT reproducible from a clean
# load of this page -- they reflect a session in which a live search had been
# run. The defect is real; the specific arithmetic quoted is not what the page
# serves.
# ===========================================================================
pf_path = os.path.join(ROOT, "vendor", "prisma-flow.js")
pf = io.open(pf_path, encoding="utf-8").read()
orig_pf = pf

pf = edit(
    pf, "PR1", "PRISMA never renders more included than identified",
    "    // If no trials are tracked but realData has entries, derive minimal counts\n"
    "    if (counts.total_search === 0 && counts.in_nma > 0) {\n"
    "      counts.included_qualitative = counts.in_nma;\n"
    "      counts.fulltext = counts.in_nma;\n"
    "    }\n",
    "    // If no screening ledger is loaded yet, the upstream counts are genuinely\n"
    "    // unknown -- they are NOT zero. Emitting 0 here produced an impossible\n"
    "    // flow (0 identified, 6 included). Mark them not-recorded instead.\n"
    "    if (counts.total_search === 0 && counts.in_nma > 0) {\n"
    "      counts.included_qualitative = counts.in_nma;\n"
    "      counts.fulltext = counts.in_nma;\n"
    "      counts.total_search = null;\n"
    "      counts.screened = null;\n"
    "      counts.not_recorded = true;\n"
    "    }\n",
)

pf = edit(
    pf, "PR2", "PRISMA boxes render 'not recorded' rather than a false 0",
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
    # the replacement re-contains the anchor, so match on the inserted token
    marker="not recorded",
)

# ---------------------------------------------------------------------------
# stats-ext.js  (shared file -- both edits are strictly backwards-compatible:
# they prefer a new field and fall back to the existing one when absent)
# ---------------------------------------------------------------------------
s = io.open(STATS_EXT, encoding="utf-8").read()
orig_s = s

s = edit(
    s, "R5b", "stats-ext prints the real DL tau2 when the engine supplies it",
    "    const dl = typeof res.tau2 === 'number' ? res.tau2 : parseFloat(res.tau2);",
    "    // res.tau2 is the REML estimate on every current engine path, so printing it\n"
    "    // as \"DL\" made the two columns identical by construction. Prefer the\n"
    "    // engine's explicit DL estimate when present; fall back for older builds.\n"
    "    const _dlRaw = (res.tau2_dl !== undefined && res.tau2_dl !== null) ? res.tau2_dl : res.tau2;\n"
    "    const dl = typeof _dlRaw === 'number' ? _dlRaw : parseFloat(_dlRaw);",
)

s = edit(
    s, "R6", "stats-ext reads res.I2 (engine field) not res.i2",
    "    const i2 = typeof res.i2 === 'number' ? res.i2 : parseFloat(res.i2);",
    "    // The engine returns I2 (capital); reading res.i2 yielded NaN and rendered\n"
    "    // \"I2 = --\" beside the correct 88% on the same page.\n"
    "    const _i2Raw = (res.I2 !== undefined && res.I2 !== null) ? res.I2 : res.i2;\n"
    "    const i2 = typeof _i2Raw === 'number' ? _i2Raw : parseFloat(_i2Raw);",
)

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


def syntax_gate(html_text, js_text):
    """Syntax-check every inline <script> block plus stats-ext.js with node.

    scripts/_js_parse_gate.py did NOT catch an illegal `const` spliced into a
    comma-expression chain in the main 600 KB block, so this gate checks each
    block independently and must pass before anything is written.
    """
    import subprocess
    import tempfile

    problems = []
    blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html_text, re.S)
    targets = [("stats-ext.js", js_text)]
    for i, b in enumerate(blocks):
        if not b.strip():
            continue
        # JSON-LD blocks are data, not script
        if b.strip().startswith("{") and '"@context"' in b[:200]:
            continue
        targets.append(("inline block %d" % i, b))
    for label, code in targets:
        fd, path = tempfile.mkstemp(suffix=".js")
        os.close(fd)
        io.open(path, "w", encoding="utf-8").write(code)
        try:
            r = subprocess.run(["node", "--check", path], capture_output=True)
            if r.returncode != 0:
                err = r.stderr.decode("utf-8", errors="replace")
                m = re.search(r"(SyntaxError.*)", err)
                problems.append("%s: %s" % (label, m.group(1) if m else err[-200:]))
        finally:
            os.unlink(path)
    return problems


probs = syntax_gate(h, s)
for _lbl, _code in (("vendor/prisma-flow.js", pf),):
    import subprocess as _sp
    import tempfile as _tf
    _fd, _p = _tf.mkstemp(suffix=".js")
    os.close(_fd)
    io.open(_p, "w", encoding="utf-8").write(_code)
    try:
        _r = _sp.run(["node", "--check", _p], capture_output=True)
        if _r.returncode != 0:
            _e = _r.stderr.decode("utf-8", errors="replace")
            _m = re.search(r"(SyntaxError.*)", _e)
            probs.append("%s: %s" % (_lbl, _m.group(1) if _m else _e[-200:]))
    finally:
        os.unlink(_p)
if probs:
    print("SYNTAX GATE FAILED -- nothing written:")
    for p in probs:
        print("  ! " + p)
    sys.exit(1)
print("syntax gate: all inline blocks + stats-ext.js parse cleanly")

if CHECK_ONLY:
    print("check-only: no files written")
    sys.exit(0)

if h != orig_h:
    io.open(APP, "w", encoding="utf-8", newline="").write(h)
    print("wrote %s" % os.path.basename(APP))
if s != orig_s:
    io.open(STATS_EXT, "w", encoding="utf-8", newline="").write(s)
    print("wrote %s" % os.path.basename(STATS_EXT))
if pf != orig_pf:
    io.open(pf_path, "w", encoding="utf-8", newline="").write(pf)
    print("wrote vendor/prisma-flow.js")
