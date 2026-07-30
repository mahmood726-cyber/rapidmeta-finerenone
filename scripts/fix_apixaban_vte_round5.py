"""Round 5 of the APIXABAN_VTE reconstruction: the last two presentation-truth
defects, both found by the live render check.

P3. "The studies so far include 5,244 patients across 1 trials." A third
    patient-facing template (the not-significant branch) carries the same
    hardcoded plural as the two fixed in round 4, and it frames a single trial
    as a body of accumulating evidence.

P4. Stale patient numbers survive a scope change. When the analysis is refused -
    either because the set is not poolable or because the endpoint is continuous
    - the guards return before updatePatientMode runs, so the patient panel and
    the plain-language gauge keep displaying the PREVIOUS question's numbers.
    Selecting RAMBLE showed "400 patients", which belongs to the gynaecologic
    trial. Numbers that outlive the analysis that produced them are exactly the
    class of defect this reconstruction exists to remove, so the guards now
    clear those surfaces explicitly.

Sources per number: outputs/apixaban_vte_correction_ledger.json.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FULL = "APIXABAN_VTE_AUTO_FULL_REVIEW.html"

applied, skipped, failed = [], [], []

# Blank every patient-facing surface, so a refusal never leaves the previous
# question's numbers on screen.
CLEAR_PATIENT_JS = (
    'try{[["patient-headline",""],["patient-plain-text",""],["patient-nnt-visual",""],'
    '["wr-gauge-text","--"],["wr-gauge-value","--"],["wr-or-display","--"],'
    '["wr-plain-message",""],["wr-icon-label",""],["wr-signal-text",""],'
    '["nyt-kn-or","--"],["nyt-kn-nnt","--"],["nyt-kn-i2","--"],["nyt-kn-k","--"],'
    '["nyt-narrative",""],["nyt-annotation",""],'
    '["va-n","--"],["va-or","--"],["va-ci","--"]].forEach(function(p){'
    'var el=document.getElementById(p[0]);if(el){if("INPUT"===el.tagName)el.value=p[1];'
    'else el.textContent=p[1]}});'
    'var _tl=document.getElementById("patient-traffic-light");'
    'if(_tl){_tl.className="patient-traffic-light";_tl.innerHTML="";'
    '_tl.setAttribute("aria-label","No result: analysis declined")}}catch(e){}'
)


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


def main():
    src = open(FULL, encoding="utf-8", newline="").read()
    before = len(src)

    # ---- P3: the not-significant patient template -----------------------
    src = sub_once(
        src,
        "`The studies so far include ${totalN.toLocaleString()} patients across ${k} trials. "
        "More evidence may be needed to draw a firm conclusion.`",
        "`${1===k?'One randomised trial':k+' randomised trials'} with "
        "${totalN.toLocaleString()} participants. The confidence interval includes no "
        "difference, so this trial does not establish a benefit or a harm for this outcome. "
        "This review does NOT pool trials, so this is single-trial evidence, not a synthesised "
        "estimate.`",
        "P3 patient prose (not significant): 'across 1 trials' corrected, and the single-trial "
        "nature plus the meaning of an interval spanning no difference now stated",
    )

    # ---- P4: clear patient surfaces on both refusal paths ----------------
    for anchor, tag in [
        ('this.renderDemographics(trials),this.renderEmptyAnalysis(_rmCont);',
         "P4a patient surfaces cleared when a continuous endpoint is declined"),
        ('this.renderDemographics(trials),this.renderEmptyAnalysis(_rmBlock);',
         "P4b patient surfaces cleared when an incompatible set is declined"),
    ]:
        n = src.count(anchor)
        if n == 1:
            src = src.replace(anchor, anchor + CLEAR_PATIENT_JS, 1)
            applied.append(tag)
        elif CLEAR_PATIENT_JS in src and src.count(CLEAR_PATIENT_JS) >= 1 and n == 0:
            skipped.append(tag + " (already applied)")
        else:
            failed.append(f"{tag} (anchor count={n})")

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
