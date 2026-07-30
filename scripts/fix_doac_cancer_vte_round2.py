"""Round 2 of the cancer-associated-VTE rebuild: evidence base, PRISMA honesty,
and the small-k publication-bias claims.

Depends on scripts/fix_doac_cancer_vte.py having run first. Anchor-based and
fail-closed in the same way.

Run:  python scripts/fix_doac_cancer_vte_round2.py
"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TARGET = os.path.join(ROOT, 'DOAC_CANCER_VTE_REVIEW.html')

RSQ = '’'   # right single quotation mark, as used in the file
NBSP = '&mdash;'

EDITS = []


def edit(tag, old, new, count=1):
    EDITS.append((tag, old, new, count))


# --------------------------------------------------------------------------
# The panel documenting every eligible study that is NOT in the primary pool.
# Values verified 2026-07-30 against the trial primaries, ClinicalTrials.gov
# API v2 and the ISRCTN registry. See the correction ledger.
# --------------------------------------------------------------------------

PANEL = '''
                        <div id="unpooled-eligible" class="mt-6 bg-amber-500/5 border border-amber-500/30 rounded-xl p-5">
                            <h4 class="text-[11px] font-bold uppercase tracking-widest text-amber-300 mb-1">Eligible studies that are NOT in the primary quantitative synthesis</h4>
                            <p class="text-[11px] text-slate-400 mb-4">These three randomised trials meet every eligibility criterion in Section 3. They are part of this review. None of them is in the primary pooled estimate, and the reason is given for each. Any statement that this is &ldquo;a living systematic review of four trials&rdquo; is a statement about the pooled analysis only, not about the evidence base.</p>
                            <div class="overflow-x-auto">
                            <table class="w-full text-[11px] text-left">
                                <thead class="text-[9px] uppercase tracking-widest text-slate-500 border-b border-slate-700">
                                    <tr><th class="p-2">Trial</th><th class="p-2">Registration</th><th class="p-2">Recurrent VTE</th><th class="p-2">Major bleeding</th><th class="p-2">Why it is not in the primary pool</th></tr>
                                </thead>
                                <tbody class="divide-y divide-slate-800/60 align-top">
                                    <tr>
                                        <td class="p-2 font-bold text-slate-200">CASTA-DIVA<br><span class="font-normal text-slate-500">Planquette 2021<br>Chest 161:781-790<br>PMID 34627853</span></td>
                                        <td class="p-2 text-slate-400">NCT02746185<br>Phase III<br>n = 158 randomised</td>
                                        <td class="p-2 text-slate-300">4/74 rivaroxaban vs 6/84 dalteparin<br>cumulative 6.4% vs 10.1%<br>SHR 0.75 (0.21&ndash;2.66)</td>
                                        <td class="p-2 text-slate-300">1/74 vs 3/84<br>cumulative 1.4% vs 3.7%<br>SHR 0.36 (0.04&ndash;3.43)</td>
                                        <td class="p-2 text-amber-200">Two estimand mismatches. The reported effect is a SUBDISTRIBUTION hazard ratio in a competing-risks model, not the cause-specific hazard ratio the other four report; and its primary outcome additionally counts &ldquo;worsening of pulmonary vascular or venous obstruction&rdquo;, which the other four do not count as recurrent VTE. Carried as a pre-specified sensitivity analysis instead (see below).</td>
                                    </tr>
                                    <tr>
                                        <td class="p-2 font-bold text-slate-200">CANVAS<br><span class="font-normal text-slate-500">Schrag 2023<br>JAMA 329:1924-1933<br>PMID 37266947</span></td>
                                        <td class="p-2 text-slate-400">NCT02744092<br>Phase NA (pragmatic)<br>n = 671 randomised</td>
                                        <td class="p-2 text-slate-300">6.1% of 330 vs 8.8% of 308<br>difference &minus;2.7%<br>1-sided 95% CI &minus;100% to 0.7%</td>
                                        <td class="p-2 text-slate-300">5.2% vs 5.6%<br>difference &minus;0.4%<br>1-sided 95% CI to 2.5%</td>
                                        <td class="p-2 text-amber-200">No hazard ratio exists to pool. The trial reports a risk DIFFERENCE with a ONE-SIDED confidence interval, and the registry posts percentages rather than event counts, so integer events cannot be recovered without assumption. It is also a comparative-effectiveness design in which clinician and patient chose the specific agent and dose, and the control arm permitted fondaparinux, which is not an LMWH.</td>
                                    </tr>
                                    <tr>
                                        <td class="p-2 font-bold text-slate-200">CONKO-011<br><span class="font-normal text-slate-500">Riess 2015 (design)<br>Dtsch Med Wochenschr<br>140 Suppl 1:S22-3<br>PMID 26069043</span></td>
                                        <td class="p-2 text-slate-400">NCT02583191<br>Phase III<br>TERMINATED, n = 246</td>
                                        <td class="p-2 text-slate-500">Not reported</td>
                                        <td class="p-2 text-slate-500">Not reported</td>
                                        <td class="p-2 text-amber-200">No outcome data exist to extract. The trial was terminated, ClinicalTrials.gov carries no posted results, and no results publication was found. Its registered primary outcome was patient-reported treatment satisfaction, not recurrent VTE. Classified as an eligible study awaiting classification. NOTE: NCT02583191 identifies THIS trial. An earlier version of this page attached SELECT-D&rsquo;s data to it; SELECT-D is registered as ISRCTN86712308.</td>
                                    </tr>
                                </tbody>
                            </table>
                            </div>
                            <div class="mt-4 pt-3 border-t border-amber-500/20 text-[11px] text-slate-300">
                                <span class="font-bold text-amber-300">Pre-specified sensitivity analysis, k = 5.</span>
                                Adding CASTA-DIVA to the four cause-specific hazard ratios gives HR <span class="font-mono text-slate-100">0.61 (95% CI 0.45&ndash;0.84)</span>, HKSJ <span class="font-mono text-slate-100">0.39&ndash;0.97</span>, &tau;&sup2; 0.0126, I&sup2; 8.5%.
                                The primary four-trial estimate is HR <span class="font-mono text-slate-100">0.58 (0.39&ndash;0.86)</span>, HKSJ <span class="font-mono text-slate-100">0.29&ndash;1.18</span>, &tau;&sup2; 0.0490, I&sup2; 30.0%.
                                Both were computed in <span class="font-mono">scripts/doac_cancer_vte_pool.py</span> and reproduced to six decimal places in R 4.6.0 / metafor 5.0.1 by <span class="font-mono">scripts/doac_cancer_vte_pool.R</span>.
                                The direction is the same either way; the width of the interval is not, and the HKSJ interval crosses 1 in the primary analysis.
                            </div>
                        </div>
'''

PRISMA_NOTE = '''
                        <div id="prisma-provenance-note" class="mt-4 bg-rose-500/5 border border-rose-500/30 rounded-xl p-4 text-[11px] text-slate-300 leading-relaxed">
                            <span class="font-bold uppercase tracking-widest text-rose-300 text-[10px] block mb-2">How to read these counts</span>
                            <span class="font-bold text-slate-100">The search runs live every time this page loads.</span>
                            The record counts above are whatever ClinicalTrials.gov, Europe PMC and OpenAlex returned at the moment of loading, so they change between loads and between readers. They are not a frozen search. A frozen, dated snapshot must be exported from the Search tab before any count on this page is cited or submitted.
                            <br><br>
                            <span class="font-bold text-slate-100">Most retrieved records carry no screening decision.</span>
                            A record counts as screened only when a reviewer has recorded include or exclude against it. Records still marked as search results have not been screened by anyone; the auto-screening relevance score is a triage aid and is not a screening decision. Any node above that implies every retrieved record was screened is describing the queue, not reviewer work.
                            <br><br>
                            <span class="font-bold text-slate-100">Screening was not dual and independent.</span>
                            The four pooled trials were entered from a curated reference list rather than reached through this queue. The review therefore does not meet the AMSTAR 2 requirement for duplicate study selection, and should not be described as if it did.
                        </div>
'''


def main():
    raw = open(TARGET, 'rb').read()
    had_bom = raw.startswith(b'\xef\xbb\xbf')
    src = raw.decode('utf-8-sig')

    build_edits()

    for tag, old, new, count in EDITS:
        found = src.count(old)
        if found != count:
            sys.exit('ANCHOR MISMATCH [%s]: expected %d, found %d\n  anchor: %.200s'
                     % (tag, count, found, old))
        src = src.replace(old, new)

    out = src.encode('utf-8')
    if had_bom:
        out = b'\xef\xbb\xbf' + out
    with open(TARGET, 'wb') as fh:
        fh.write(out)

    print('applied %d anchored edits (round 2)' % len(EDITS))
    for tag, _, _, _ in EDITS:
        print('  -', tag)


def build_edits():
    # -- publication-bias claims that k = 4 cannot support --------------------
    edit('narrative: Egger at k = 4 was reported as a finding; it is not interpretable',
         'eggerNote="--"!==r.eggerP?parseFloat(r.eggerP)<.1?" Egger%ss regression test raises '
         'concern for small-study effects.":" Egger%ss regression test shows no significant '
         'evidence of publication bias.":""' % (RSQ, RSQ),
         'eggerNote=parseInt(r.k,10)>=10?"--"!==r.eggerP?parseFloat(r.eggerP)<.1?" Egger%ss '
         'regression test raises concern for small-study effects.":" Egger%ss regression test '
         'shows no significant evidence of publication bias.":"":` Publication bias was NOT '
         'assessed: with ${r.k} studies, Egger%ss test, trim-and-fill and the Copas sensitivity '
         'sweep have almost no power and their output is not interpretable. They are shown on the '
         'Analysis tab for completeness and must not be read as evidence either for or against '
         'small-study effects.`' % (RSQ, RSQ, RSQ))

    # -- the two evidence-base panels ----------------------------------------
    edit('report: document the eligible studies that are not in the pool',
         '<div id="prisma-flow-container" class="bg-slate-950/50 rounded-xl p-4 border '
         'border-slate-800"></div>',
         '<div id="prisma-flow-container" class="bg-slate-950/50 rounded-xl p-4 border '
         'border-slate-800"></div>' + PRISMA_NOTE + PANEL)

    # -- the standing claim in the review title/subhead ----------------------
    edit('subhead: say what the k refers to',
         '`${r.k} randomized controlled trials enrolling ${r.n} patients, synthesized using '
         'random-effects meta-analysis.`',
         '`${r.k} randomized controlled trials enrolling ${r.n} patients in the pooled estimate, '
         'synthesized using DerSimonian-Laird random effects. Three further eligible trials '
         '(CASTA-DIVA, CANVAS, CONKO-011) are part of this review but are not in this pool - see '
         '"Eligible studies that are NOT in the primary quantitative synthesis" below.`')


if __name__ == '__main__':
    main()
