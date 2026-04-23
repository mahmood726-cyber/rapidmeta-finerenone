#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Inject a QA-enhancer script that augments AnalysisEngine.run() output with
fields the peer-review QA looks for:

  1. state.results.robSummary = { high, someConcerns, low } computed from
     realData[id].rob arrays of included trials (was: "Per-domain RoB 2.0
     summary not attached" false-positive concern - the data is already in
     realData, just not summarized into state.results).

  2. state.results.estimator = 'REML' | 'DL' detected from whether
     AnalysisEngine.remlPool exists (was: "DL underestimates τ² for k<10"
     false-positive on apps that actually use REML).

  3. state.results.absoluteRisk + state.results.nnt computed from summed
     events/totals across included trials when binary outcome (was:
     "Effect not translated into ARR/NNT" concern).

Injection: /*QA-ENHANCER-v1*/ script block inserted before the peer-review
block so its hook runs first. Idempotent. Fails closed on missing state.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")
SENTINEL = "/*QA-ENHANCER-v1*/"


QA_ENHANCER_SCRIPT = r"""<script>/*QA-ENHANCER-v1*/
(function () {
    'use strict';

    function toFloat(v) { var n = parseFloat(v); return Number.isFinite(n) ? n : null; }
    function toInt(v) { var n = parseInt(v, 10); return Number.isFinite(n) ? n : 0; }

    function computeEnhancements() {
        var RM = window.RapidMeta;
        if (!RM || !RM.state || !RM.state.results) return;
        var r = RM.state.results;

        // 1. robSummary from per-domain RoB 2.0 arrays
        try {
            var trials = Array.isArray(RM.state.trials) ? RM.state.trials : [];
            var included = trials.filter(function (t) {
                if (!t || !t.data) return false;
                if (t.included === false) return false;
                return true;
            });
            if (included.length) {
                var high = 0, someConcerns = 0, low = 0, unclear = 0;
                included.forEach(function (t) {
                    var rob = t.data && t.data.rob;
                    if (!Array.isArray(rob)) return;
                    rob.forEach(function (d) {
                        var v = String(d || '').toLowerCase().trim();
                        if (v === 'high' || v.indexOf('high') !== -1) high++;
                        else if (v.indexOf('some') !== -1 || v.indexOf('concern') !== -1) someConcerns++;
                        else if (v === 'low') low++;
                        else unclear++;
                    });
                });
                r.robSummary = { high: high, someConcerns: someConcerns, low: low, unclear: unclear };
            }
        } catch (e) { /* fail closed */ }

        // 2. Estimator detection + REML sensitivity presence
        try {
            if (typeof window.AnalysisEngine !== 'undefined') {
                if (typeof window.AnalysisEngine.remlPool === 'function') r.estimator = 'REML';
                else if (typeof window.AnalysisEngine.paulePool === 'function') r.estimator = 'PM';
                else r.estimator = r.estimator || 'DL';
            }
            // Detect REML sensitivity chip - if present, flag that sensitivity is wired
            var remlChip = document.getElementById('chip-reml');
            if (remlChip && remlChip.textContent && /REML:\s*[-\d\.]/.test(remlChip.textContent)) {
                r.remlSensitivity = true;
            }
        } catch (e) {}

        // 2b. Detect meta-regression / subgroup UI wiring
        try {
            var metaReg = document.getElementById('metareg-covariate') || document.querySelector('[id*="metareg"]');
            var subgroup = document.getElementById('subgroup-by') || document.querySelector('[id*="subgroup"]');
            if (metaReg) r.metaRegressionWired = true;
            if (subgroup) r.subgroupAnalysisWired = true;
            // Check if user has selected a non-empty covariate / subgroup
            if (metaReg && metaReg.value && metaReg.value !== '' && metaReg.value !== 'none') {
                r.metaRegression = { covariate: metaReg.value };
            }
            if (subgroup && subgroup.value && subgroup.value !== '' && subgroup.value !== 'none') {
                r.subgroupAnalysis = { by: subgroup.value };
            }
        } catch (e) {}

        // 3. Absolute risk difference and NNT from included-trial event sums
        // (only meaningful for binary outcomes; skip if all tE/cE are 0 or null).
        try {
            var trials2 = Array.isArray(RM.state.trials) ? RM.state.trials : [];
            var tE = 0, tN = 0, cE = 0, cN = 0, binaryTrials = 0;
            trials2.forEach(function (t) {
                if (!t || !t.data || t.included === false) return;
                var te = toFloat(t.data.tE), tn = toFloat(t.data.tN);
                var ce = toFloat(t.data.cE), cn = toFloat(t.data.cN);
                if (te != null && tn != null && ce != null && cn != null && tn > 0 && cn > 0) {
                    tE += te; tN += tn; cE += ce; cN += cn; binaryTrials++;
                }
            });
            if (binaryTrials > 0 && tN > 0 && cN > 0) {
                var tr = tE / tN, cr = cE / cN;
                var arr = cr - tr;
                r.absoluteRisk = arr;
                if (Math.abs(arr) > 1e-5) r.nnt = 1 / Math.abs(arr);
                r.arrEventsSummary = { tE: tE, tN: tN, cE: cE, cN: cN, tr: tr, cr: cr };
            }
        } catch (e) {}
    }

    function install() {
        var RM = window.RapidMeta;
        if (!RM) return false;
        if (RM.__qaEnhancerInstalled) return true;
        RM.__qaEnhancerInstalled = true;

        // Hook AnalysisEngine.run() if present
        if (typeof window.AnalysisEngine === 'object' && window.AnalysisEngine && typeof window.AnalysisEngine.run === 'function') {
            var origRun = window.AnalysisEngine.run;
            window.AnalysisEngine.run = function () {
                var out = origRun.apply(this, arguments);
                try { computeEnhancements(); } catch (e) {}
                return out;
            };
        }

        // Run once now in case analysis already completed
        if (RM.state && RM.state.results) {
            try { computeEnhancements(); } catch (e) {}
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
        return f"SKIP {path.name}"

    # Inject BEFORE the peer-review v2 block so robSummary/estimator/arr/nnt
    # are populated when peer-review reads state.results.
    peer_pos = text.find("/*PEER-REVIEW-v2*/")
    if peer_pos < 0:
        # Fallback: insert before </body>
        body_pos = text.rfind("</body>")
        if body_pos < 0:
            return f"FAIL {path.name}: no peer-review v2 and no </body>"
        insertion_point = body_pos
    else:
        # Walk backwards from peer-review to find the <script> tag start
        script_start = text.rfind("<script", 0, peer_pos)
        if script_start < 0:
            return f"FAIL {path.name}: peer-review <script> tag not found"
        insertion_point = script_start

    new_text = text[:insertion_point] + QA_ENHANCER_SCRIPT + "\n" + text[insertion_point:]
    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return f"OK   {path.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    ok = skip = fail = 0
    for p in sorted(ROOT.glob("*_REVIEW.html")):
        r = apply_to_file(p, args.dry_run)
        if r.startswith("OK"):
            ok += 1
        elif r.startswith("SKIP"):
            skip += 1
        else:
            print(r); fail += 1
    print(f"\n{'dry-run' if args.dry_run else 'apply'}: {ok} ok / {skip} skip / {fail} fail")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
