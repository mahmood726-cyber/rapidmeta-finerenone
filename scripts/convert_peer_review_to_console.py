#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Convert the visible peer-review panel (v1) to a console-only finding reporter (v2).

Rationale: user confirmed the peer review is a QA/lint tool for catching
analysis errors, not a deliverable that should appear in the manuscript.

Changes per file:
  1. Strip the entire <script>/*PEER-REVIEW-v1*/...</script> block that
     rendered the editor + 4 reviewer cards inside #manuscript-text.
  2. Inject a fresh <script>/*PEER-REVIEW-v2*/...</script> block at the same
     location. The v2 block keeps the same 4 reviewer logic (methodologist,
     clinical, biostatistical, patient representative) + editor reconciliation,
     but emits output only to the DevTools console:
        console.group('[Synthesis QA] Peer-review findings')
          Editor decision: ...
          groupCollapsed each reviewer:
            concerns -> console.warn
     and exposes RapidMeta.peerReviewFindings for programmatic access /
     tests. No DOM insertion; no impact on manuscript text or exports.

Idempotent (sentinel /*PEER-REVIEW-v2*/). Runs on all 99 _REVIEW.html files.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

V1_START = "<script>/*PEER-REVIEW-v1*/"
V2_SENTINEL = "/*PEER-REVIEW-v2*/"

CONSOLE_REVIEW_SCRIPT = r"""<script>/*PEER-REVIEW-v2*/
(function () {
    'use strict';

    function num(v) { var f = parseFloat(v); return Number.isFinite(f) ? f : null; }

    var Reviewers = {
        methodologist: function (r, protocol) {
            var k = parseInt(r.k) || 0;
            var concerns = [];
            if (k < 5) concerns.push('Only k=' + k + ' trial' + (k === 1 ? '' : 's') + ' available; heterogeneity and publication-bias diagnostics are underpowered.');
            if (k < 3) concerns.push('Prediction interval not definable for k<3; flag as boundary condition.');
            var rob = r.robSummary || null;
            if (rob && typeof rob === 'object' && ((rob.high || 0) > 0 || (rob.someConcerns || 0) > 0)) {
                concerns.push('RoB 2.0: ' + (rob.high || 0) + ' high-risk + ' + (rob.someConcerns || 0) + ' some-concerns domains; add low-RoB sensitivity analysis.');
            } else if (!rob) {
                concerns.push('Per-domain RoB 2.0 summary not attached to the included-trials table.');
            }
            if (k >= 10 && !r.egger && !r.trimFill) {
                concerns.push('Publication-bias assessment (Egger / trim-and-fill) absent despite k>=10.');
            }
            var rec = concerns.length >= 3 ? 'Major revision' : (concerns.length <= 1 && k >= 5) ? 'Accept with minor revision' : 'Minor revision';
            return { role: 'Methodology & PRISMA', concerns: concerns, recommendation: rec };
        },

        clinicalExpert: function (r, protocol, benchmarks) {
            var k = parseInt(r.k) || 0;
            var or_ = num(r.or);
            var concerns = [];
            if (benchmarks && benchmarks.length) {
                var b = benchmarks[0];
                var pointInside = or_ !== null && or_ >= b.lci && or_ <= b.uci;
                if (!pointInside) {
                    concerns.push('Pooled ' + (or_ !== null ? or_.toFixed(2) : '--') + ' diverges from ' + b.citation + ' benchmark (' + b.measure + ' ' + b.estimate.toFixed(2) + ' [' + b.lci.toFixed(2) + ', ' + b.uci.toFixed(2) + ']); Discussion should reconcile explicitly.');
                }
            } else {
                concerns.push('No endpoint-matched published benchmark wired to this outcome.');
            }
            if (k < 3) concerns.push('k<3 - clinical meaningfulness (MCID, NNT) cannot be grounded in pooled evidence.');
            var i2 = num(r.i2);
            if (i2 !== null && i2 >= 75) concerns.push('I² = ' + i2 + '% (considerable); show subgroup/strata estimates alongside pooled.');
            var rec = concerns.length >= 3 ? 'Major revision' : (concerns.length <= 1) ? 'Accept with minor revision' : 'Minor revision';
            return { role: 'Clinical expert', concerns: concerns, recommendation: rec };
        },

        biostatistician: function (r, protocol) {
            var k = parseInt(r.k) || 0;
            var i2 = num(r.i2);
            var tau2 = num(r.tau2);
            var concerns = [];
            // DL concern suppressed when REML sensitivity chip is wired and showing a result.
            if (k < 10 && (r.estimator || 'DL').toUpperCase() === 'DL' && !r.remlSensitivity) {
                concerns.push('DL estimator under-estimates τ² for k<10; add REML/Paule-Mandel sensitivity.');
            }
            if (i2 !== null && i2 >= 50 && !r.subgroupAnalysis && !r.metaRegression) {
                if (r.subgroupAnalysisWired || r.metaRegressionWired) {
                    concerns.push('I²=' + i2 + '% - subgroup / meta-regression UI present but no covariate selected; run the exploration.');
                } else {
                    concerns.push('I²=' + i2 + '% without meta-regression / subgroup exploration; τ²=' + (tau2 !== null ? tau2.toFixed(3) : '--') + ' left un-partitioned.');
                }
            }
            if (k >= 10 && !r.egger && !r.eggerP) {
                concerns.push('Egger regression missing from headline readout despite k>=10.');
            }
            if (r.gradeCertainty === 'VERY LOW' || r.gradeCertainty === 'LOW') {
                concerns.push('GRADE ' + r.gradeCertainty + '; hedge Abstract and Discussion accordingly.');
            }
            var rec = concerns.length >= 3 ? 'Major revision' : concerns.length === 0 && k >= 5 ? 'Accept' : (concerns.length <= 1) ? 'Accept with minor revision' : 'Minor revision';
            return { role: 'Biostatistician', concerns: concerns, recommendation: rec };
        },

        patientRep: function (r, protocol) {
            var concerns = [];
            if (!r.absoluteRisk && !r.nnt) concerns.push('Effect not translated into absolute-risk difference / NNT for shared decision.');
            if (!r.patientReportedOutcomes) concerns.push('QoL / PROs not in headline analysis.');
            if (r.gradeCertainty === 'VERY LOW' || r.gradeCertainty === 'LOW') {
                concerns.push('Plain-language framing for patients needed given ' + r.gradeCertainty + ' certainty.');
            }
            var rec = concerns.length === 0 ? 'Accept' : concerns.length <= 1 ? 'Accept with minor revision' : 'Minor revision';
            return { role: 'Patient representative', concerns: concerns, recommendation: rec };
        },
    };

    function editorDecision(reviewers) {
        var scores = { 'Accept': 4, 'Accept with minor revision': 3, 'Minor revision': 2, 'Major revision': 1, 'Reject': 0 };
        var total = 0;
        reviewers.forEach(function (rv) { total += (scores[rv.recommendation] != null ? scores[rv.recommendation] : 2); });
        var mean = total / reviewers.length;
        if (mean >= 3.25) return { decision: 'Accept with minor revision', rationale: 'All reviewers support publication after minor clarifications.' };
        if (mean >= 2.25) return { decision: 'Minor revision', rationale: 'Reviewers support publication but want clarifications on reporting completeness and residual uncertainty.' };
        if (mean >= 1.25) return { decision: 'Major revision', rationale: 'Substantive concerns across reviewer roles; expect a second review round.' };
        return { decision: 'Reject and resubmit', rationale: 'Concerns exceed what a single revision can address; consider restructuring the evidence base.' };
    }

    function runReview() {
        var RM = window.RapidMeta;
        if (!RM || !RM.state || !RM.state.results) return null;
        var r = RM.state.results;
        if (r.or == null || r.or === '--') return null;

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

        if (typeof console !== 'undefined' && console.group) {
            var totalConcerns = 0;
            reviewerList.forEach(function (rv) { totalConcerns += rv.concerns.length; });
            console.group('%c[Synthesis QA] Peer-review findings (' + totalConcerns + ' concerns, editor: ' + editor.decision + ')', 'color:#38bdf8;font-weight:bold');
            console.log('Editor: ' + editor.decision + ' — ' + editor.rationale);
            reviewerList.forEach(function (rv) {
                if (rv.concerns.length === 0) {
                    console.log('%c✓ ' + rv.role + ' — ' + rv.recommendation + ' (no concerns)', 'color:#10b981');
                } else {
                    console.groupCollapsed('%c⚠ ' + rv.role + ' — ' + rv.recommendation + ' (' + rv.concerns.length + ')', 'color:#f59e0b');
                    rv.concerns.forEach(function (c) { console.warn(c); });
                    console.groupEnd();
                }
            });
            console.groupEnd();
        }

        RM.peerReviewFindings = { editor: editor, reviewers: reviewerList };
        return RM.peerReviewFindings;
    }

    function install() {
        if (!window.RapidMeta) return false;
        if (window.RapidMeta.__peerReviewInstalled) return true;
        window.RapidMeta.__peerReviewInstalled = true;
        window.RapidMeta.runPeerReview = runReview;

        if (typeof window.generateManuscriptText === 'function') {
            var orig = window.generateManuscriptText;
            window.generateManuscriptText = function () {
                var out;
                try { out = orig.apply(this, arguments); }
                catch (e) { /* legacy may throw; still run review */ }
                try { runReview(); } catch (e) { /* fail closed */ }
                return out;
            };
        }
        // If manuscript already rendered at install time, run once.
        if (window.RapidMeta.state && window.RapidMeta.state.results) {
            try { runReview(); } catch (e) {}
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


V1_BLOCK_RE = re.compile(
    r"\n?<script>/\*PEER-REVIEW-v1\*/[\s\S]*?</script>\s*\n?",
    re.MULTILINE,
)


def strip_and_replace(text: str) -> tuple:
    """Remove v1 block + any rendered .peer-review-panel residue; inject v2."""
    if V2_SENTINEL in text:
        return text, "SKIP: already-v2"

    v1_count = len(V1_BLOCK_RE.findall(text))
    if v1_count == 0:
        return text, "SKIP: no-v1-present"
    if v1_count > 1:
        return text, f"FAIL: {v1_count} v1 blocks (expected 1)"

    new_text = V1_BLOCK_RE.sub("\n", text, count=1)

    # Insert v2 at the same logical point - after the last existing </script>
    # before </body>. This mirrors where the old v1 tag lived (past the RM-BRIDGE
    # + retrofit chain) without needing to remember the exact anchor.
    body_pos = new_text.rfind("</body>")
    if body_pos < 0:
        return text, "FAIL: no </body> anchor for v2 injection"

    new_text = new_text[:body_pos] + CONSOLE_REVIEW_SCRIPT + "\n" + new_text[body_pos:]
    return new_text, "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    ok = skip = fail = 0
    for p in sorted(ROOT.glob("*_REVIEW.html")):
        text = p.read_text(encoding="utf-8", newline="")
        new_text, status = strip_and_replace(text)
        if status == "OK":
            if not args.dry_run:
                p.write_text(new_text, encoding="utf-8")
            ok += 1
        elif status.startswith("SKIP"):
            skip += 1
        else:
            print(f"FAIL {p.name}: {status}")
            fail += 1

    print(f"\n{'dry-run' if args.dry_run else 'apply'}: {ok} converted / {skip} skipped / {fail} failed")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
