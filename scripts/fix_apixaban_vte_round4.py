"""Round 4 of the APIXABAN_VTE reconstruction: two presentation-truth defects
found by the live render check.

P1. Stale refusal text under a live plot. renderEmptyAnalysis writes its message
    into the plot containers' innerHTML; Plotly then draws INTO the same element
    without clearing it, so after switching from an incompatible scope to a
    single-question scope the words "NOT POOLABLE - the selected trials answer 5
    different questions" remained in the DOM underneath a perfectly valid
    single-trial forest. A refusal notice that outlives the condition it
    describes is its own presentation lie.

P2. "Across 1 large clinical trials involving 19 patients". The patient-facing
    summary hardcodes a plural and the word "large". With every question now at
    k = 1 that is ungrammatical, and calling RAMBLE's 19 participants a "large
    clinical trial" is false. Rewritten to state single-trial evidence plainly.

Sources per number: outputs/apixaban_vte_correction_ledger.json.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FULL = "APIXABAN_VTE_AUTO_FULL_REVIEW.html"

applied, skipped, failed = [], [], []

PLOT_IDS = (
    '["plot-forest","plot-subgroup","plot-cumulative","plot-tsa","plot-loo","plot-labbe",'
    '"plot-galbraith","plot-nnt","plot-funnel","plot-baujat","plot-posterior","plot-metareg",'
    '"plot-copas","plot-power","plot-egger","plot-rob-bar","plot-ci-compare","plot-forest-nyt",'
    '"plot-sensitivity","plot-influence"]'
)

# Clear any previous refusal notice before a real analysis draws.
CLEAR_JS = (
    'try{' + PLOT_IDS + '.forEach(function(id){var el=document.getElementById(id);'
    'if(el&&/NOT POOLABLE|CONTINUOUS OUTCOME|No analysis-ready|No plottable contrast|'
    'Pooling refused/.test(el.textContent||"")){try{window.Plotly&&Plotly.purge(el)}catch(e){}'
    'el.innerHTML=""}})}catch(e){}'
)

# k-aware, honest patient prose.
COUNT_PHRASE = (
    "${1===k?'One randomised trial':k+' randomised trials'} with "
    "${totalN.toLocaleString()} participants"
)


def sub_all(text, old, new, tag):
    n = text.count(old)
    if n:
        applied.append(f"{tag} ({n} occurrence(s))")
        return text.replace(old, new)
    if new and new in text:
        skipped.append(tag + " (already applied)")
        return text
    failed.append(tag + " (anchor not found)")
    return text


def main():
    src = open(FULL, encoding="utf-8", newline="").read()
    before = len(src)

    # ---- P1: clear a stale refusal before drawing a real analysis -------
    anchor = 'try{window.__rmHidePoolBlock&&window.__rmHidePoolBlock()}catch(e){}'
    n = src.count(anchor)
    if CLEAR_JS in src:
        skipped.append("P1 stale-refusal clearing (already applied)")
    elif n == 1:
        src = src.replace(anchor, anchor + CLEAR_JS, 1)
        applied.append(
            "P1 plot containers are cleared of any previous refusal notice before a real "
            "analysis draws; 'NOT POOLABLE' text was surviving underneath a valid single-trial "
            "forest after a scope change"
        )
    else:
        failed.append(f"P1 stale-refusal clearing (anchor count={n})")

    # ---- P2: honest, k-aware patient prose ------------------------------
    src = sub_all(
        src,
        "Across ${k} large clinical trials involving ${totalN.toLocaleString()} patients, "
        "apixaban showed a meaningful benefit.",
        COUNT_PHRASE + " reported a benefit of apixaban. This review does NOT pool trials, "
        "so this is single-trial evidence, not a synthesised estimate.",
        "P2a patient prose (benefit): 'Across 1 large clinical trials' corrected and the "
        "single-trial nature stated",
    )
    src = sub_all(
        src,
        "Across ${k} large clinical trials involving ${totalN.toLocaleString()} patients, "
        "apixaban was associated with more ${outcomeText}.",
        COUNT_PHRASE + " reported more ${outcomeText} with apixaban. This review does NOT pool "
        "trials, so this is single-trial evidence, not a synthesised estimate.",
        "P2b patient prose (harm): same correction",
    )

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
