"""Round 7: stop the automated GRADE engine issuing a certainty rating this
review has not earned.

Round 6 blanked GRADE on the two refusal paths, but every question in this
review is k = 1 and the single-trial path still runs the automated engine. The
live render showed COBRRA rendering "Certainty HIGH, No downgrading required" -
an unadjudicated HIGH on one open-label trial.

That is wrong twice over. GRADE's inconsistency and publication-bias domains are
not assessable from a single study at all, so "no downgrading required" is not a
finding, it is an artefact of having nothing to compare. And this review's own
not-done list states GRADE has not been re-derived for the new question set; an
engine that keeps emitting ratings makes that statement false on the page.

The engine is therefore suppressed for k < 2 and replaced with an explicit
statement of what is and is not assessable. A rating can be reinstated when a
human has actually done the assessment.

Sources per number: outputs/apixaban_vte_correction_ledger.json.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FULL = "APIXABAN_VTE_AUTO_FULL_REVIEW.html"

applied, skipped, failed = [], [], []

# Guard placed at the top of renderGRADE. The minified signature is
# renderGRADE(I2,lci,uci,data,...), and inside it k is derived as data.length,
# so the contributing-trial count for the current scope is data.length.
GRADE_GUARD = (
    'renderGRADE(I2,lci,uci,data,piLCI,piUCI,hksjLCI,hksjUCI){'
    'try{const _k=(data&&data.length)||0;'
    'if(_k<2){'
    '["grade-container","grade-profile-container","grade-etd-container"].forEach(function(id){'
    'const el=document.getElementById(id);if(el)el.innerHTML='
    '\'<div style="padding:14px 16px;border:1px solid #b45309;background:#42210b;\'+'
    '\'border-radius:10px;color:#fed7aa;font-size:13px;line-height:1.6">\'+'
    '\'<b>No GRADE certainty rating is issued for this question.</b><br>\'+'
    '\'This question rests on a single trial. Two of GRADE\\u2019s five domains \'+'
    '\'\\u2014 inconsistency and publication bias \\u2014 cannot be assessed from one \'+'
    '\'study, so an automated rating of \\u201cno downgrading required\\u201d would be an \'+'
    '\'artefact of having nothing to compare, not a finding. Risk of bias, \'+'
    '\'indirectness and imprecision have not been independently adjudicated for \'+'
    '\'this question set either. Read the single-trial estimate and its \'+'
    '\'confidence interval directly.\'+\'</div>\'});'
    'const es=document.getElementById("grade-etd-section");if(es)es.style.display="none";'
    'return}'
    'const es2=document.getElementById("grade-etd-section");'
    'if(es2)es2.style.display="";}catch(e){}'
)


def main():
    src = open(FULL, encoding="utf-8", newline="").read()
    before = len(src)

    anchor = ("renderGRADE(I2,lci,uci,data,piLCI,piUCI,hksjLCI,hksjUCI){"
              "const container=document.getElementById(\"grade-container\")")
    n = src.count(anchor)
    if "No GRADE certainty rating is issued for this question" in src:
        skipped.append("GRADE k<2 suppression (already applied)")
    elif n == 1:
        src = src.replace(anchor, GRADE_GUARD + 'const container=document.getElementById("grade-container")', 1)
        applied.append(
            "GRADE engine suppressed for k<2. The live render showed COBRRA rendering "
            "'Certainty HIGH, No downgrading required' from a single open-label trial; "
            "inconsistency and publication bias are not assessable from one study, and this "
            "review has not adjudicated the other three domains for the new question set."
        )
    else:
        failed.append(f"GRADE k<2 suppression (anchor count={n})")

    open(FULL, "w", encoding="utf-8", newline="").write(src)

    print(f"{FULL}: {before:,} -> {len(src):,} chars\n")
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
