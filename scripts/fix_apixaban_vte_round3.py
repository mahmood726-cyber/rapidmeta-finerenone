"""Round 3 of the APIXABAN_VTE reconstruction: two defects found by the live
render check, not by reading the file.

D1. Question D (postoperative gynaecologic-cancer prophylaxis) rendered
    "No analysis-ready included trials". Root cause: NCT02366871 is registered
    PHASE2, and the ANALYSIS path applies its own phase-II exclusion
    (`isPhaseTwoLike(t?.data?.phase??"")`) at several sites. Round 1 only taught
    the CANONICAL BOOTSTRAP path about rmPhaseEligible, so the trial was seeded
    and then silently dropped downstream. This is the same pressure that made
    the original build record a PHASE2 trial as phase III: fix the filter, do
    not falsify the phase.

D2. Question E (RAMBLE) fell through to "all included studies are double-zero or
    double-complete", which is false. RAMBLE's primary outcome is CONTINUOUS, so
    there is no 2x2 to plot at all. Saying "double-zero" invites the reader to
    believe a risk ratio existed and was merely uninformative.

Sources per number: outputs/apixaban_vte_correction_ledger.json.
"""
import io
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


# The continuous-outcome guard, placed alongside the compatibility gate so both
# refusals share one insertion point in the analysis path.
CONT_GUARD_JS = (
    'const _rmCont=(function(){try{'
    'const ts=(trials??[]).filter(t=>t&&t.data);if(0===ts.length)return"";'
    'const key=RapidMeta.state.selectedOutcome||"default";'
    'const pick=t=>"default"===key?(t.data.allOutcomes??[])[0]'
    ':(t.data.allOutcomes??[]).find(o=>o.shortLabel===key);'
    'const picked=ts.map(pick).filter(Boolean);'
    'if(picked.length!==ts.length)return"";'
    'if(!picked.every(o=>"CONTINUOUS"===String(o.type??"").toUpperCase()))return"";'
    'return"CONTINUOUS OUTCOME \\u2014 no risk ratio exists for this endpoint.\\n"+'
    'picked.map((o,i)=>"\\u2022 "+(ts[i].data.name??ts[i].id)+": "+String(o.title??o.shortLabel??"")).join("\\n")+'
    '"\\nThis endpoint is a score, not a count of events, so no 2x2 table, no risk ratio and no '
    'forest point can be formed from it. It is NOT a double-zero result and it is NOT an '
    'uninformative risk ratio \\u2014 the quantity simply is not a ratio. Where the trial reports '
    'medians with full ranges at single-digit group sizes, converting them to a mean and SD would '
    'mean inventing a distribution for a skewed score, so no standardised mean difference is '
    'computed either. Read the arm-level summary on the trial card."}catch(e){return""}})();'
    'if(_rmCont){RapidMeta.state.results=null,RapidMeta.save(),this.updateStatCards(null),'
    'this.renderDemographics(trials),this.renderEmptyAnalysis(_rmCont);'
    'try{window.__rmShowPoolBlock&&window.__rmShowPoolBlock(_rmCont)}catch(e){}return}'
)


def main():
    src = open(FULL, encoding="utf-8", newline="").read()
    before = len(src)

    # ---- D1: teach EVERY phase-II filter about rmPhaseEligible ----------
    old = 'isPhaseTwoLike(t?.data?.phase??"")'
    new = '(!0!==t?.data?.rmPhaseEligible&&isPhaseTwoLike(t?.data?.phase??""))'
    n = src.count(old)
    if n:
        src = src.replace(old, new)
        applied.append(
            f"D1 phase-II exclusion now honours the reviewed-eligible flag at all {n} analysis-path "
            f"sites (round 1 covered only the canonical bootstrap). NCT02366871 is registered "
            f"PHASE2 and was being seeded and then silently dropped again; the original build "
            f"worked around this by recording its phase as III, which is the falsification this "
            f"reconstruction undoes."
        )
    elif new in src:
        skipped.append("D1 phase-II filters (already applied)")
    else:
        failed.append("D1 phase-II filters (anchor not found)")

    # ---- D2: an honest message for a continuous endpoint ----------------
    src = sub_once(
        src,
        'const _rmBlock=RapidMeta.rmPoolBlockReason?RapidMeta.rmPoolBlockReason(trials):"";',
        CONT_GUARD_JS + 'const _rmBlock=RapidMeta.rmPoolBlockReason?RapidMeta.rmPoolBlockReason(trials):"";',
        "D2 continuous outcomes now report why no ratio exists, instead of falling through to "
        "'all included studies are double-zero or double-complete', which was false for RAMBLE",
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
