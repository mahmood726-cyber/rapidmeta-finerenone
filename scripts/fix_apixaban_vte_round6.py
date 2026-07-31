"""Round 6: close the two remaining sourcing gaps and stop GRADE rendering under
a refusal.

G1. AMPLIFY's major-or-CRNM composite and AMPLIFY-EXT's safety outcomes were
    carried as published percentages only, because ClinicalTrials.gov posts them
    as proportions rather than participant counts. scripts/derive_bleeding_counts.py
    proves that each proportion, at the precision posted and over the treated-
    population denominator posted, is matched by exactly ONE integer - 15 of 15
    unique, 0 ambiguous - and every figure NEJM reports independently
    cross-checks. Those counts are now written as real 2x2 outcomes, each with
    its own treated-population denominator (AMPLIFY-EXT safety is 840/811/826,
    NOT the ITT 840/813/829).

G2. The GRADE panels are not among the elements renderEmptyAnalysis clears, so a
    certainty rating computed for a previous scope could survive a refusal. A
    GRADE rating under "no pooled estimate is defined" is exactly the kind of
    orphaned claim this reconstruction removes.

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


def oc(label, title, otype, tE, cE, nT, nC):
    return ('{"shortLabel":%s,"title":%s,"type":%s,"tE":%d,"cE":%d,"nT":%d,"nC":%d,'
            '"matchScore":%d,"estimandType":"RR"}'
            % (_q(label), _q(title), _q(otype), tE, cE, nT, nC,
               95 if otype == "PRIMARY" else 70))


def _q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


# --- AMPLIFY: two further safety outcomes, treated population 2676 / 2689 ----
AMPLIFY_NEW = ",".join([
    oc("MajorOrCRNMBleeding",
       "ISTH major or clinically relevant non-major bleeding (treated population; "
       "denominators differ from ITT)", "SAFETY", 115, 261, 2676, 2689),
    oc("CRNMBleeding",
       "Clinically relevant non-major bleeding (treated population; denominators "
       "differ from ITT)", "SAFETY", 103, 215, 2676, 2689),
])

# --- AMPLIFY-EXT: safety, treated population 840 / 811 / 826 ----------------
AMPLIFY_EXT_NEW = ",".join([
    oc("MajorBleeding_2p5mg",
       "ISTH major bleeding - apixaban 2.5 mg BID vs placebo (treated population)",
       "SAFETY", 2, 4, 840, 826),
    oc("MajorBleeding_5mg",
       "ISTH major bleeding - apixaban 5 mg BID vs the SAME placebo arm (treated population)",
       "SAFETY", 1, 4, 811, 826),
    oc("MajorOrCRNMBleeding_2p5mg",
       "Major or clinically relevant non-major bleeding - apixaban 2.5 mg BID vs placebo "
       "(treated population)", "SAFETY", 27, 22, 840, 826),
    oc("MajorOrCRNMBleeding_5mg",
       "Major or clinically relevant non-major bleeding - apixaban 5 mg BID vs the SAME "
       "placebo arm (treated population)", "SAFETY", 35, 22, 811, 826),
    oc("CRNMBleeding_2p5mg",
       "Clinically relevant non-major bleeding - apixaban 2.5 mg BID vs placebo "
       "(treated population)", "SAFETY", 25, 19, 840, 826),
    oc("CRNMBleeding_5mg",
       "Clinically relevant non-major bleeding - apixaban 5 mg BID vs the SAME placebo arm "
       "(treated population)", "SAFETY", 34, 19, 811, 826),
])

GRADE_CLEAR = (
    'try{["grade-container","grade-profile-container","grade-etd-container"].forEach('
    'function(id){var el=document.getElementById(id);if(el)el.innerHTML='
    '\'<div class="text-xs text-slate-500 italic px-4 py-3">No GRADE certainty rating is '
    'issued: no estimate was produced for this scope.</div>\'});'
    'var es=document.getElementById("grade-etd-section");if(es)es.style.display="none"}catch(e){}'
)


def main():
    src = open(FULL, encoding="utf-8", newline="").read()
    before = len(src)

    # ---- G1a AMPLIFY --------------------------------------------------
    anchor = ('{"shortLabel":"MajorBleeding","title":"ISTH major bleeding (safety population; '
              'denominators differ from ITT)","type":"SAFETY","tE":15,"cE":49,"nT":2676,'
              '"nC":2689,"matchScore":70,"estimandType":"RR"}')
    src = sub_once(src, anchor, anchor + "," + AMPLIFY_NEW,
                   "G1a AMPLIFY: major-or-CRNM 115/2676 vs 261/2689 and CRNM 103/2676 vs "
                   "215/2689 added as real 2x2 outcomes (counts uniquely recovered and proven)")

    # ---- G1b AMPLIFY-EXT ----------------------------------------------
    anchor = ('{"shortLabel":"RecurrentVTEorVTEDeath_5mg","title":"Recurrent symptomatic VTE or '
              'VTE-related death - apixaban 5 mg BID vs the SAME placebo arm (primary)",'
              '"type":"PRIMARY","tE":14,"cE":73,"nT":813,"nC":829,"matchScore":95,'
              '"estimandType":"RR"}')
    src = sub_once(src, anchor, anchor + "," + AMPLIFY_EXT_NEW,
                   "G1b AMPLIFY-EXT: six safety outcomes added with the TREATED-population "
                   "denominators 840/811/826, which differ from the ITT 840/813/829")

    # ---- G1c drop the now-false caveats in the snippets ----------------
    src = sub_once(
        src,
        "Major-or-CRNM bleeding 4.3% vs 9.7% (RR 0.44, 95% CI 0.36-0.55) - reported as a "
        "published effect only; per-arm counts for that composite were not read off a "
        "primary surface, so no 2x2 is claimed for it.",
        "Major-or-CRNM bleeding 115/2676 vs 261/2689 (published RR 0.44, 95% CI 0.36-0.55); "
        "CRNM alone 103/2676 vs 215/2689. Safety counts recovered from the proportions posted "
        "on ClinicalTrials.gov, each uniquely determined at the posted precision over the "
        "posted treated-population denominator.",
        "G1c AMPLIFY snippet no longer says the composite counts are unavailable",
    )
    src = sub_once(
        src,
        "Major bleeding 0.5% / 0.2% / 0.1%; CRNM bleeding 2.3% / 3.0% / "
        "4.2% - published percentages only, per-arm safety counts not read off a primary "
        "surface.",
        "Major bleeding placebo 4/826, apixaban 2.5 mg 2/840, apixaban 5 mg 1/811; CRNM "
        "bleeding placebo 19/826, 2.5 mg 25/840, 5 mg 34/811. Safety counts recovered from the "
        "proportions posted on ClinicalTrials.gov, each uniquely determined at the posted "
        "precision; note the treated-population denominators (840/811/826) differ from the ITT "
        "denominators (840/813/829).",
        "G1d AMPLIFY-EXT snippet now carries the recovered safety counts",
    )

    # ---- G2 GRADE must not survive a refusal ---------------------------
    if GRADE_CLEAR in src:
        skipped.append("G2 GRADE clearing (already applied)")
    else:
        n = 0
        for anchor in ('this.renderEmptyAnalysis(_rmCont);',
                       'this.renderEmptyAnalysis(_rmBlock);'):
            if src.count(anchor) == 1:
                src = src.replace(anchor, anchor + GRADE_CLEAR, 1)
                n += 1
        if n == 2:
            applied.append("G2 GRADE panels are blanked on both refusal paths, so a certainty "
                           "rating cannot outlive the estimate it was computed for")
        else:
            failed.append(f"G2 GRADE clearing (patched {n}/2 refusal paths)")

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
