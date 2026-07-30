"""Round 2 of the APIXABAN_VTE reconstruction.

Round 1 rebuilt the ledger, retired the pre-2015 rule and installed the
fail-closed estimand-compatibility gate. This round closes the surfaces that
survive the gate because they are prose or provenance rather than computed
statistics:

  - CTGOV_EVIDENCE_REGISTRY was literally {}, which is why the provenance panel
    reported "No source", "0/2 CT.gov results", "0 CT.gov-backed" and "no
    protocol/SAP" for trials that plainly have all four. Populated from the
    registry records fetched 2026-07-30.
  - "The fragility index was 0, indicating the result is robust" - FI = 0 means
    the result was never statistically significant. This is backwards.
  - The exported Python validation script hardcodes 'Hazard Ratio' and
    'DL Random-Effects' regardless of what was actually run.
  - A per-question scope selector, so each of the five questions can be viewed
    on its own rather than only as a blocked incompatible set.

Sources per number: outputs/apixaban_vte_correction_ledger.json.
"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FULL = "APIXABAN_VTE_AUTO_FULL_REVIEW.html"

applied, skipped, failed = [], [], []


def sub_once(text, old, new, tag, *, required=True):
    n = text.count(old)
    if n == 1:
        applied.append(tag)
        return text.replace(old, new, 1)
    if new and new in text:
        skipped.append(tag + " (already applied)")
        return text
    (failed if required else skipped).append(f"{tag} (anchor count={n})")
    return text


# ---------------------------------------------------------------------------
# R1. Honest provenance registry.
#     Every flag below was read off the ClinicalTrials.gov API v2 record on
#     2026-07-30. resultsPosted is true for all five because all five have a
#     posted results section. protocolDocument / sapDocument reflect the
#     registry's documentSection; their CONTENTS were not read, which the
#     ledger records under not_done.
# ---------------------------------------------------------------------------
REGISTRY_JS = (
    'CTGOV_EVIDENCE_REGISTRY={'
    'NCT00643201:{label:"AMPLIFY",resultsPosted:!0,protocolDocument:!0,sapDocument:!0,'
    'publicationSource:"PubMed PMID 23808982 (N Engl J Med 2013;369:799-808)",'
    'publicationDate:"2013-07-01",'
    'note:"Registry results + primary publication abstract, both read 2026-07-30. Full text not read."},'
    'NCT00633893:{label:"AMPLIFY-EXT",resultsPosted:!0,protocolDocument:!0,sapDocument:!0,'
    'publicationSource:"PubMed PMID 23216615 (N Engl J Med 2013;368:699-708)",'
    'publicationDate:"2013-02-21",'
    'note:"Three-arm trial; both apixaban doses share one placebo arm. Full text not read."},'
    'NCT03266783:{label:"COBRRA",resultsPosted:!0,protocolDocument:!0,sapDocument:!0,'
    'publicationSource:"PubMed PMID 41812192 (N Engl J Med 2026;394:1051-1060)",'
    'publicationDate:"2026-03-12",'
    'note:"Screened and adjudicated INCLUDE on 2026-07-30. Full text not read."},'
    'NCT02366871:{label:"Guntupalli 2020 (gyn-onc prophylaxis)",resultsPosted:!0,'
    'protocolDocument:!0,sapDocument:!0,'
    'publicationSource:"PubMed PMID 32589230 (JAMA Netw Open 2020;3(6):e207410)",'
    'publicationDate:"2020-06-01",'
    'note:"Registry attaches a combined Prot_SAP_001.pdf and an ICF. Contents not read. '
    'Registered PHASE2. The corpus file matched this trial to PMID 32641236, which is the '
    'adherence subanalysis, not the primary report."},'
    'NCT02829957:{label:"RAMBLE",resultsPosted:!0,protocolDocument:!0,sapDocument:!0,'
    'publicationSource:"",publicationDate:"",'
    'note:"NO journal publication found on PubMed; the registry record is the only source. '
    'The registry attaches a Study Protocol (Prot_000.pdf) AND a separate Statistical Analysis '
    'Plan (SAP_001.pdf); contents not read. Previously mis-matched to PMID 26272306, which is a '
    'BACKGROUND citation in this trial\'s own reference list, not a report of this trial."}'
    '}'
)

# ---------------------------------------------------------------------------
# R7. Per-question scope selector.
# ---------------------------------------------------------------------------
SCOPE_UI_JS = r"""
rmQuestions(){
  const seen=new Map();
  for(const id of Object.keys(this.realData??{})){
    const q=this.realData[id]?.rmQuestion; if(!q) continue;
    if(!seen.has(q)) seen.set(q,[]);
    seen.get(q).push(this.realData[id]?.name??id);
  }
  return [...seen.entries()].map(([q,names])=>({q,names}));
},
rmSetQuestion(q){
  this.state.rmQuestion=String(q??"");
  this.save();
  try{ AnalysisEngine.render(); }catch(e){}
  try{ this.rmRenderQuestionBar(); }catch(e){}
},
rmRenderQuestionBar(){
  const host=document.getElementById("rm-question-bar"); if(!host) return;
  const cur=String(this.state.rmQuestion??"");
  const qs=this.rmQuestions();
  host.innerHTML=
    '<div style="font-size:11px;text-transform:uppercase;letter-spacing:.14em;'+
    'color:#94a3b8;font-weight:700;margin-bottom:8px">Review scope &mdash; five separate '+
    'questions, analysed one at a time</div>'+
    '<div style="display:flex;flex-wrap:wrap;gap:8px">'+
    ['<button data-rmq="" style="'+(cur===""?"background:#7f1d1d;border-color:#f87171;color:#fecaca":"background:#1e293b;border-color:#334155;color:#cbd5e1")+
      ';border-width:1px;border-style:solid;border-radius:999px;padding:6px 14px;font-size:12px;'+
      'font-weight:600;cursor:pointer">All five (not poolable)</button>']
      .concat(qs.map(o=>'<button data-rmq="'+escapeHtml(o.q)+'" style="'+
        (cur===o.q?"background:#134e4a;border-color:#2dd4bf;color:#ccfbf1":"background:#1e293b;border-color:#334155;color:#cbd5e1")+
        ';border-width:1px;border-style:solid;border-radius:999px;padding:6px 14px;font-size:12px;'+
        'font-weight:600;cursor:pointer" title="'+escapeHtml(o.names.join(", "))+'">'+
        escapeHtml(o.q)+' (k='+o.names.length+')</button>')).join("")+
    '</div>';
  host.querySelectorAll("button[data-rmq]").forEach(b=>{
    b.addEventListener("click",()=>this.rmSetQuestion(b.getAttribute("data-rmq")));
  });
},"""

# The fail-closed banner the analysis path calls into.
BANNER_JS = r"""
<script data-rm-poolblock="1">
/* Fail-closed pool-block banner. The analysis path calls these when the
   estimand-compatibility gate refuses to pool, so the refusal is visible at the
   top of the page and not only inside the emptied plot panels. */
(function(){
  var ID="rm-poolblock-banner";
  window.__rmShowPoolBlock=function(msg){
    try{
      var el=document.getElementById(ID);
      if(!el){el=document.createElement("div");el.id=ID;
        (document.body||document.documentElement).appendChild(el);}
      el.setAttribute("style","position:fixed;top:0;left:0;right:0;z-index:2147483645;"+
        "font:600 13px/1.5 system-ui,Segoe UI,Arial,sans-serif;background:#2b1416;color:#ffd7d5;"+
        "border-bottom:3px solid #f85149;padding:10px 16px;box-shadow:0 2px 10px rgba(0,0,0,.5);"+
        "max-height:38vh;overflow:auto;white-space:pre-wrap");
      el.textContent="⛔ "+String(msg||"");
    }catch(e){}
  };
  window.__rmHidePoolBlock=function(){
    try{var el=document.getElementById(ID); if(el) el.remove();}catch(e){}
  };
})();
</script>
</body>"""


def main():
    src = open(FULL, encoding="utf-8", newline="").read()
    before = len(src)

    # ---- R1 provenance registry ----------------------------------------
    src = sub_once(src, "CTGOV_EVIDENCE_REGISTRY={}", REGISTRY_JS,
                   "R1 CTGOV_EVIDENCE_REGISTRY populated: it was {} , which is why the provenance "
                   "panel reported 'No source' / '0/2 CT.gov results' / '0 CT.gov-backed' / "
                   "'no protocol/SAP' for trials that have all four")

    # ---- R2 remaining cardiorenal fallbacks (minified anchors) ----------
    src = sub_once(src, '?.protocol?.out??"MACE Composite"', '?.protocol?.out??""',
                   "R2a protocol-outcome fallback was 'MACE Composite'", required=False)
    src = sub_once(src, '?.endpointLabel??"MACE")', '?.endpointLabel??"")',
                   "R2b reviewer-endpoint fallback was 'MACE'", required=False)

    # ---- R3 last user-visible slug -------------------------------------
    src = sub_once(
        src,
        "in favor of apixaban_vte_auto",
        "in favor of apixaban",
        "R3 last user-visible topic-slug exposure in the GRADE/verdict prose",
    )

    # ---- R4 the fragility-index inversion ------------------------------
    #   FI = 0 does not mean robust. It means the result was not statistically
    #   significant to begin with, so no event needs to change to overturn it.
    src = sub_once(
        src,
        '0===parseInt(r.fragIdx)?"The fragility index was 0, indicating the result is robust to '
        'single-event modifications."',
        '0===parseInt(r.fragIdx)?"The fragility index was 0. This does NOT indicate robustness: a '
        'fragility index of 0 means the result was not statistically significant in the first '
        'place, so no event needs to be reassigned to overturn it."',
        "R4a manuscript prose: 'FI 0 = robust' inverted the meaning of the fragility index",
    )
    src = sub_once(
        src,
        '${0===r.fragIdx?"the result is robust to event modifications"',
        '${0===r.fragIdx?"the result was not statistically significant, so no event reassignment '
        'is needed to overturn it - a fragility index of 0 is NOT evidence of robustness"',
        "R4b narrative annotation: same inversion",
    )
    src = sub_once(
        src,
        'status:fi>=8?"pass":fi>=3?"warn":fi>0?"fail":"warn",detail:fi>0?"FI = "+fi:"N/A (HR mode or NS result)"',
        'status:fi>=8?"pass":fi>=3?"warn":fi>0?"fail":"fail",detail:fi>0?"FI = "+fi:'
        '"FI = 0 or not applicable - a fragility index of 0 means the result was not statistically '
        'significant, not that it is robust"',
        "R4c QA8 check no longer records a zero fragility index as a warn with an ambiguous note",
        required=False,
    )

    # ---- R5 exported validation script honesty --------------------------
    src = src.replace(
        "ax.set_xlabel('Hazard Ratio'); ax.set_title('Forest Plot (DL Random-Effects)')",
        "ax.set_xlabel('Risk Ratio'); ax.set_title('Single-trial estimates - NOT pooled')",
    )
    n = src.count("ax.set_title('Forest Plot (DL Random-Effects)')")
    if n:
        src = src.replace(
            "ax.set_title('Forest Plot (DL Random-Effects)')",
            "ax.set_title('Single-trial estimates - NOT pooled')",
        )
        applied.append(f"R5 exported Python validation script no longer hardcodes 'Hazard Ratio' "
                       f"and 'DL Random-Effects' when neither was used ({n + 1} label(s) corrected)")
    else:
        skipped.append("R5 exported-script labels (already applied)")

    # ---- R6 dead NMA engine pointing at three foreign trials -------------
    src = sub_once(
        src,
        '["NCT01035255","NCT01920711","NCT02924727"].filter(id=>!RapidMeta.state.excludedTrials?.[id])',
        '[].filter(id=>!RapidMeta.state.excludedTrials?.[id])',
        "R6 NMA engine referenced three NCTs that are not in this review (foreign template "
        "residue) and labelled its contrast 'Apixaban vs Placebo'; neutralised",
    )
    src = sub_once(
        src,
        'direct:{label:"Apixaban vs Placebo",k:trialData.length}',
        'direct:{label:"Not applicable - this review runs no network meta-analysis",k:trialData.length}',
        "R6b NMA contrast label",
        required=False,
    )

    # ---- R7 question scope selector -------------------------------------
    src = sub_once(
        src,
        "getScopedIncludedTrials(opts={}){const requireData=!1!==opts.requireData,"
        "requirePositiveN=Boolean(opts.requirePositiveN);return(this.state.trials??[]).filter(t=>",
        SCOPE_UI_JS.strip() + "\ngetScopedIncludedTrials(opts={}){const requireData=!1!==opts.requireData,"
        "requirePositiveN=Boolean(opts.requirePositiveN),_rmQ=String(this.state.rmQuestion??\"\");"
        "return(this.state.trials??[]).filter(t=>(!_rmQ||String(t.data?.rmQuestion??\"\")===_rmQ)&&",
        "R7 per-question scope: getScopedIncludedTrials now filters on the declared question, so "
        "each of the five can be viewed on its own instead of only as a blocked set",
    )

    # host element for the scope bar, above the analysis banner
    src = sub_once(
        src,
        '<div class="rm-nonpool-banner"',
        '<div id="rm-question-bar" style="background:#0f172a;border:1px solid #334155;'
        'border-radius:10px;padding:12px 15px;margin-bottom:14px"></div><div class="rm-nonpool-banner"',
        "R7b scope-selector host element added above the analysis banner",
    )

    # render the bar whenever the analysis renders
    src = sub_once(
        src,
        "const _rmBlock=RapidMeta.rmPoolBlockReason?RapidMeta.rmPoolBlockReason(trials):\"\";",
        "try{RapidMeta.rmRenderQuestionBar&&RapidMeta.rmRenderQuestionBar()}catch(e){}"
        "const _rmBlock=RapidMeta.rmPoolBlockReason?RapidMeta.rmPoolBlockReason(trials):\"\";",
        "R7c scope bar re-renders with the analysis",
    )

    # ---- R8 fail-closed banner hooks -------------------------------------
    # NB: three other "</body>" occurrences live inside JS string literals that
    #     build the exported HTML reports. Only the document's own closing tag,
    #     which is the one immediately preceding </html>, may be targeted.
    if 'data-rm-poolblock="1"' in src:
        skipped.append("R8 pool-block banner (already applied)")
    else:
        anchor = "</script></body>\n\n\n</html>"
        n = src.count(anchor)
        if n == 1:
            src = src.replace(anchor, "</script>" + BANNER_JS.strip() + "\n\n\n</html>", 1)
            applied.append("R8 fail-closed pool-block banner installed (fixed, unmissable, "
                           "states the refusal reason at the top of the page)")
        else:
            failed.append(f"R8 pool-block banner (document </body> anchor count={n})")

    open(FULL, "w", encoding="utf-8", newline="").write(src)

    print(f"{FULL}: {before:,} -> {len(src):,} bytes\n")
    print(f"APPLIED ({len(applied)}):")
    for a in applied:
        print("  +", a)
    if skipped:
        print(f"\nSKIPPED ({len(skipped)}):")
        for s in skipped:
            print("  .", s)
    if failed:
        print(f"\nFAILED ({len(failed)}):")
        for f in failed:
            print("  !", f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
