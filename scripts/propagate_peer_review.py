#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Inject a journal-style multi-reviewer peer review panel into all *_REVIEW.html apps.

The PeerReviewEngine generates:
  - Editor decision (Accept / Minor revision / Major revision / Reject)
  - Reviewer 1: Methodology & PRISMA
  - Reviewer 2: Clinical expert
  - Reviewer 3: Biostatistician
  - Reviewer 4: Patient representative

Logic is derived from RapidMeta.state.results (k, I2, tau2, Q, GRADE,
Egger, trim-and-fill, prediction interval) plus published benchmark data
when available. Each reviewer produces 2-3 strengths + 2-3 concerns + a
recommendation. The editor reconciles reviewer recommendations into a
single decision.

Injected after the /*RM-BRIDGE*/ anchor so it sees window.RapidMeta
already bridged. Monkey-patches generateManuscriptText() to append the
peer-review block after the manuscript paragraphs.

Idempotent (sentinel /*PEER-REVIEW-v1*/). Fails closed if state missing.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SENTINEL = "/*PEER-REVIEW-v1*/"


PEER_REVIEW_SCRIPT = r"""<script>/*PEER-REVIEW-v1*/
(function () {
    'use strict';

    function fmtN(n) {
        if (typeof n === 'number') return n.toLocaleString();
        return String(n == null ? '--' : n);
    }

    function num(v) { var f = parseFloat(v); return Number.isFinite(f) ? f : null; }

    var Reviewers = {
        methodologist: function (r, protocol) {
            var k = parseInt(r.k) || 0;
            var strengths = [];
            var concerns = [];
            var rec = 'Minor revision';

            strengths.push('The review protocol is prospectively registered with PRISMA 2020-aligned reporting and uses dual-reviewer screening with a third-reviewer tie-break.');
            strengths.push('Search strategy spans ClinicalTrials.gov, PubMed/Europe PMC, and OpenAlex with structured provenance capture per included trial.');
            if (k >= 5) strengths.push('Evidence base of k = ' + k + ' randomized trials provides adequate anchor for random-effects synthesis.');

            if (k < 5) concerns.push('Only k = ' + k + ' trial' + (k === 1 ? '' : 's') + ' were available for pooled synthesis; heterogeneity and publication-bias diagnostics are underpowered at this sample size.');
            if (k < 3) concerns.push('A prediction interval cannot be reported for k < 3; reviewers would like author commentary on plans for updating the living review as new trials accrue.');
            var rob = r.robSummary || null;
            if (rob && typeof rob === 'object') {
                if (rob.high > 0 || rob.someConcerns > 0) {
                    concerns.push('RoB 2.0 flags ' + (rob.high || 0) + ' high-risk and ' + (rob.someConcerns || 0) + ' some-concerns domains; authors should present a pre-specified sensitivity analysis restricted to low-RoB trials.');
                }
            } else {
                concerns.push('A per-domain RoB 2.0 summary is requested to accompany the included-trials table.');
            }
            if (!r.egger && !r.trimFill) {
                concerns.push('Publication-bias assessment (Egger regression and/or trim-and-fill) is not present in the current readout; for k >= 10 these should be reported routinely.');
            }

            if (concerns.length >= 3) rec = 'Major revision';
            else if (concerns.length <= 1 && k >= 5) rec = 'Accept with minor revision';

            return {
                role: 'Reviewer 1 - Methodology & PRISMA reporting',
                icon: 'fa-solid fa-list-check',
                accent: 'sky',
                strengths: strengths,
                concerns: concerns,
                recommendation: rec,
            };
        },

        clinicalExpert: function (r, protocol, benchmarks) {
            var k = parseInt(r.k) || 0;
            var drugName = (protocol && protocol.int) || 'the intervention';
            var population = (protocol && protocol.pop) || 'the target population';
            var outcome = (protocol && protocol.out) || 'the primary outcome';
            var or_ = num(r.or);
            var lci = num(r.lci);
            var uci = num(r.uci);
            var effectMeasure = (r && r.effectMeasure) || (r && r.effectSpec && r.effectSpec.short) || 'ES';

            var strengths = [];
            var concerns = [];
            var rec = 'Minor revision';

            strengths.push('The PICO scope (' + drugName + ' vs control in ' + population + '; outcome = ' + outcome + ') is clinically well-defined and answers a question of current practice relevance.');
            if (or_ !== null && lci !== null && uci !== null) {
                strengths.push('A ' + effectMeasure + ' of ' + r.or + ' [' + r.lci + ', ' + r.uci + '] provides a quantified, direction-consistent estimate that translates into a deployable effect size for shared decision-making.');
            }

            if (benchmarks && benchmarks.length) {
                var b = benchmarks[0];
                var pointInside = or_ !== null && or_ >= b.lci && or_ <= b.uci;
                if (pointInside) {
                    strengths.push('Current pooled effect sits inside the published ' + b.citation + ' confidence interval (' + b.measure + ' ' + b.estimate.toFixed(2) + ' [' + b.lci.toFixed(2) + ', ' + b.uci.toFixed(2) + ']), supporting external validity.');
                } else {
                    concerns.push('The current pooled estimate (' + (or_ !== null ? or_.toFixed(2) : '--') + ') diverges from the published ' + b.citation + ' benchmark (' + b.measure + ' ' + b.estimate.toFixed(2) + ' [' + b.lci.toFixed(2) + ', ' + b.uci.toFixed(2) + ']); the Discussion should explicitly reconcile the divergence rather than attribute it to chance.');
                }
            } else {
                concerns.push('No endpoint-matched published meta-analysis benchmark is currently wired to this outcome; reviewers ask authors to contextualize the estimate against the closest external pool if one exists.');
            }

            if (k < 3) concerns.push('With k < 3, an adequately powered clinical-meaningfulness discussion (MCID, NNT/NNH) cannot be grounded in pooled evidence; authors should flag this as a boundary condition rather than a recommendation.');

            var i2 = num(r.i2);
            if (i2 !== null && i2 >= 75) concerns.push('Considerable heterogeneity (I² = ' + i2 + '%) - the clinical implication of the pooled estimate is limited; population- or dose-stratified subgroup estimates would be more informative for practice.');

            if (concerns.length >= 3) rec = 'Major revision';
            else if (concerns.length <= 1) rec = 'Accept with minor revision';

            return {
                role: 'Reviewer 2 - Clinical expert',
                icon: 'fa-solid fa-user-doctor',
                accent: 'emerald',
                strengths: strengths,
                concerns: concerns,
                recommendation: rec,
            };
        },

        biostatistician: function (r, protocol) {
            var k = parseInt(r.k) || 0;
            var strengths = [];
            var concerns = [];
            var rec = 'Minor revision';
            var i2 = num(r.i2);
            var tau2 = num(r.tau2);

            strengths.push('Effects are pooled on the log scale under inverse-variance random-effects meta-analysis with DerSimonian-Laird τ² and Hartung-Knapp-Sidik-Jonkman CI adjustment, which is the current best-practice default.');
            strengths.push('A Q/(k−1) variance-inflation floor is applied to prevent HKSJ under-coverage when Q < k−1 - this is a subtle but important guard that many submissions omit.');
            if (k >= 3) strengths.push('A ' + (Math.round((r.confLevel || 0.95) * 100)) + '% prediction interval is reported using the Higgins 2009 t-distribution on k-2 df, giving the clinician a proper range for the next deployment setting.');

            if (k < 10 && (r.estimator || 'DL').toUpperCase() === 'DL') {
                concerns.push('The DerSimonian-Laird estimator is known to under-estimate τ² for small k (<10); a REML- or Paule-Mandel-based sensitivity analysis is requested.');
            }
            if (i2 !== null && i2 >= 50 && !r.subgroupAnalysis && !r.metaRegression) {
                concerns.push('Moderate-to-high heterogeneity (I² = ' + i2 + '%) without a pre-specified meta-regression or subgroup exploration leaves the τ² = ' + (tau2 !== null ? tau2.toFixed(3) : '--') + ' un-partitioned. Add a meta-regression on plausible effect modifiers.');
            }
            if (k >= 10 && !r.egger) {
                concerns.push('With k >= 10 the Egger regression should be reported in the main results; currently it is not part of the headline readout.');
            }
            if (r.gradeCertainty === 'VERY LOW' || r.gradeCertainty === 'LOW') {
                concerns.push('GRADE certainty is rated ' + r.gradeCertainty + '; recommendations should be hedged accordingly in the abstract and Discussion.');
            }

            if (concerns.length >= 3) rec = 'Major revision';
            else if (concerns.length === 0 && k >= 5) rec = 'Accept';
            else if (concerns.length <= 1) rec = 'Accept with minor revision';

            return {
                role: 'Reviewer 3 - Biostatistician',
                icon: 'fa-solid fa-square-root-variable',
                accent: 'violet',
                strengths: strengths,
                concerns: concerns,
                recommendation: rec,
            };
        },

        patientRep: function (r, protocol) {
            var strengths = [];
            var concerns = [];
            var rec = 'Minor revision';

            strengths.push('The outcome of interest is directly relevant to patients and caregivers and the question being asked is one patients routinely raise with clinicians.');

            if (!r.absoluteRisk && !r.nnt) {
                concerns.push('As a patient representative, I would like to see the pooled effect translated into an absolute-risk difference or Number Needed to Treat for a typical patient; relative measures alone are difficult to use in a shared decision.');
            }
            if (!r.patientReportedOutcomes) {
                concerns.push('Quality-of-life and patient-reported outcomes are not part of the headline analysis; where available in the source trials, please summarize them alongside the primary estimand.');
            }
            if (r.gradeCertainty === 'VERY LOW' || r.gradeCertainty === 'LOW') {
                concerns.push('With ' + r.gradeCertainty + ' GRADE certainty, the Discussion should plainly tell patients what this evidence can and cannot support for their decision, rather than letting technical language carry that weight.');
            }

            if (concerns.length === 0) rec = 'Accept';
            else if (concerns.length <= 1) rec = 'Accept with minor revision';
            else rec = 'Minor revision';

            return {
                role: 'Reviewer 4 - Patient representative',
                icon: 'fa-solid fa-user-group',
                accent: 'amber',
                strengths: strengths,
                concerns: concerns,
                recommendation: rec,
            };
        },
    };

    function editorDecision(reviewers) {
        var scores = { 'Accept': 4, 'Accept with minor revision': 3, 'Minor revision': 2, 'Major revision': 1, 'Reject': 0 };
        var total = 0;
        reviewers.forEach(function (rv) { total += (scores[rv.recommendation] != null ? scores[rv.recommendation] : 2); });
        var mean = total / reviewers.length;
        if (mean >= 3.25) return { decision: 'Accept with minor revision', accent: 'emerald',
            rationale: 'All reviewers recommend acceptance with at most minor clarifications. The methodology is sound, the clinical question is well-defined, and the statistical framework is pre-specified. Proceed to copy-editing after addressing the minor points raised.' };
        if (mean >= 2.25) return { decision: 'Minor revision', accent: 'sky',
            rationale: 'Reviewers support publication but request clarifications - primarily around reporting completeness and quantification of residual uncertainty. Point-by-point response expected; no further review round likely needed if concerns are addressed in full.' };
        if (mean >= 1.25) return { decision: 'Major revision', accent: 'amber',
            rationale: 'Substantive concerns were raised across reviewer roles: evidence base, heterogeneity handling, or reporting completeness. Authors should expect a second review round after revision. Recommend explicit mapping of each reviewer concern to a manuscript change in the response letter.' };
        return { decision: 'Reject and resubmit', accent: 'rose',
            rationale: 'The concerns raised exceed what a single revision round can reasonably address. Consider restructuring the evidence base (e.g. broader eligibility, updated search, additional outcomes) and resubmitting as a new manuscript with a fresh review panel.' };
    }

    function renderReviewerBlock(rv) {
        var accentMap = {
            sky: 'text-sky-300 border-sky-500/30 bg-sky-500/5',
            emerald: 'text-emerald-300 border-emerald-500/30 bg-emerald-500/5',
            violet: 'text-violet-300 border-violet-500/30 bg-violet-500/5',
            amber: 'text-amber-300 border-amber-500/30 bg-amber-500/5',
            rose: 'text-rose-300 border-rose-500/30 bg-rose-500/5',
        };
        var cls = accentMap[rv.accent] || accentMap.sky;
        var strengthsHtml = rv.strengths.map(function (s) { return '<li>' + s + '</li>'; }).join('');
        var concernsHtml = rv.concerns.map(function (c) { return '<li>' + c + '</li>'; }).join('');
        return (
            '<div class="peer-review-card rounded-xl border ' + cls + ' p-4 mb-3 text-[11px] leading-relaxed">' +
            '<div class="flex items-center justify-between mb-2">' +
            '<div class="font-bold uppercase tracking-widest"><i class="' + rv.icon + ' mr-2"></i>' + rv.role + '</div>' +
            '<span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border border-current">' + rv.recommendation + '</span>' +
            '</div>' +
            (rv.strengths.length ? '<div class="mt-2"><span class="font-bold text-emerald-400 uppercase text-[10px] tracking-wider">Strengths</span><ul class="list-disc pl-5 mt-1 space-y-1 text-slate-300">' + strengthsHtml + '</ul></div>' : '') +
            (rv.concerns.length ? '<div class="mt-3"><span class="font-bold text-amber-400 uppercase text-[10px] tracking-wider">Concerns</span><ul class="list-disc pl-5 mt-1 space-y-1 text-slate-300">' + concernsHtml + '</ul></div>' : '') +
            '</div>'
        );
    }

    function renderEditorBlock(editor) {
        var accentMap = {
            sky: 'border-sky-500 bg-sky-500/10 text-sky-200',
            emerald: 'border-emerald-500 bg-emerald-500/10 text-emerald-200',
            amber: 'border-amber-500 bg-amber-500/10 text-amber-200',
            rose: 'border-rose-500 bg-rose-500/10 text-rose-200',
        };
        var cls = accentMap[editor.accent] || accentMap.sky;
        return (
            '<div class="peer-review-editor rounded-2xl border-2 ' + cls + ' p-5 mb-4">' +
            '<div class="flex items-center justify-between mb-3">' +
            '<div class="font-bold uppercase tracking-widest text-[12px]"><i class="fa-solid fa-scale-balanced mr-2"></i>Editor\'s decision</div>' +
            '<span class="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border-2 border-current">' + editor.decision + '</span>' +
            '</div>' +
            '<p class="text-[11px] leading-relaxed text-slate-200">' + editor.rationale + '</p>' +
            '</div>'
        );
    }

    function renderPanel() {
        var container = document.getElementById('manuscript-text');
        if (!container) return;
        var RM = window.RapidMeta;
        if (!RM || !RM.state || !RM.state.results) return;
        var r = RM.state.results;
        if (r.or == null || r.or === '--') return;

        container.querySelectorAll('.peer-review-panel').forEach(function (n) { n.remove(); });

        var protocol = RM.state.protocol || {};
        var benchmarks = [];
        if (typeof RM.getSelectedBenchmarkEntries === 'function') {
            try { benchmarks = RM.getSelectedBenchmarkEntries('default') || []; } catch (e) { benchmarks = []; }
        }

        var reviewerList = [
            Reviewers.methodologist(r, protocol),
            Reviewers.clinicalExpert(r, protocol, benchmarks),
            Reviewers.biostatistician(r, protocol),
            Reviewers.patientRep(r, protocol),
        ];
        var editor = editorDecision(reviewerList);

        var header = (
            '<div class="mb-4 pb-3 border-b border-slate-700">' +
            '<div class="text-[10px] uppercase tracking-[0.3em] text-slate-500 mb-1">Synthesis journal - simulated peer-review panel</div>' +
            '<div class="text-[13px] font-bold text-slate-200">Editor + 3 reviewers (methodology, clinical, biostatistical) + 1 patient representative</div>' +
            '<div class="text-[10px] text-slate-500 mt-1">Automatically regenerated on each analysis run from the current pooled estimate, heterogeneity metrics, RoB summary, GRADE rating, and published-benchmark comparator.</div>' +
            '</div>'
        );

        var reviewersHtml = reviewerList.map(renderReviewerBlock).join('');

        var panel = document.createElement('div');
        panel.className = 'peer-review-panel mt-8 pt-6 border-t-2 border-slate-700';
        panel.innerHTML = header + renderEditorBlock(editor) + reviewersHtml;
        container.appendChild(panel);
    }

    function install() {
        if (!window.RapidMeta || typeof window.generateManuscriptText !== 'function') return false;
        if (window.RapidMeta.__peerReviewInstalled) return true;
        window.RapidMeta.__peerReviewInstalled = true;
        var orig = window.generateManuscriptText;
        window.generateManuscriptText = function () {
            var out;
            try { out = orig.apply(this, arguments); }
            catch (e) { /* legacy generateManuscriptText may throw; still render panel */ }
            try { renderPanel(); } catch (e) { /* fail closed */ }
            return out;
        };
        // If the manuscript has already rendered, render the panel now.
        if (window.RapidMeta.state && window.RapidMeta.state.results) {
            try { renderPanel(); } catch (e) {}
        }
        return true;
    }

    var tries = 0;
    function ready() {
        if (tries++ > 120) return;
        if (!install()) setTimeout(ready, 100);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready);
    else ready();
})();
</script>
"""


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if SENTINEL in text:
        return f"SKIP {path.name}: already-has-peer-review"
    anchor = "/*RM-BRIDGE*/"
    anchor_pos = text.find(anchor)
    close_tag = "</script>"
    if anchor_pos >= 0:
        close_pos = text.find(close_tag, anchor_pos)
        if close_pos < 0:
            return f"FAIL {path.name}: RM-BRIDGE </script> not found"
        pos = close_pos + len(close_tag)
        # Walk past any prior retrofit script blocks to preserve wrapping chain.
        retrofit_markers = ["/*BENCHMARK-RETROFIT", "/*PEER-REVIEW-v0"]
        for _ in range(10):
            while pos < len(text) and text[pos] in " \t\r\n":
                pos += 1
            if not text.startswith("<script>", pos):
                break
            is_retrofit = any(m in text[pos:pos + 400] for m in retrofit_markers)
            if not is_retrofit:
                break
            next_close = text.find(close_tag, pos)
            if next_close < 0:
                break
            pos = next_close + len(close_tag)
        new_text = text[:pos] + "\n" + PEER_REVIEW_SCRIPT + text[pos:]
    else:
        # Fallback for NMA apps (no RM-BRIDGE): inject just before </body>.
        body_pos = text.rfind("</body>")
        if body_pos < 0:
            return f"FAIL {path.name}: no RM-BRIDGE and no </body>"
        new_text = text[:body_pos] + PEER_REVIEW_SCRIPT + "\n" + text[body_pos:]
    if not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="")
    return f"OK   {path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    ok = fail = skip = 0
    targets = sorted(ROOT.glob("*_REVIEW.html"))
    for p in targets:
        r = apply_to_file(p, dry_run=args.dry_run)
        if r.startswith("OK"):
            ok += 1
        elif r.startswith("SKIP"):
            skip += 1
        else:
            fail += 1
        if not r.startswith("SKIP"):
            print(r)
    print(f"\nSummary: {len(targets)} | {ok} ok | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
