#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Inject a REML/PM (Paule-Mandel) pool retrofit into all 99 apps.

Reason: peer-review flags DL estimator for k<10 unless an REML/PM
sensitivity is computed. The QA-enhancer detects apps that already have
REML (FINERENONE, COLCHICINE_CVD). This retrofit COMPUTES REML/PM for apps
that don't.

Implementation: Paule-Mandel iteration (equivalent to REML for the mixed-
effects meta-analysis likelihood and usually robust at small k per
advanced-stats.md). Extracts per-trial (y, v) from realData based on
effect measure (OR / RR / HR / MD), iterates tau^2 until
Q_PM(tau^2) = k-1, then pools with random-effects weights and 95% CI.

Attaches to RapidMeta.state.results:
  - tau2Reml         (Paule-Mandel tau^2)
  - remlResult       { estimator: 'PM', measure, tau2, logEffect, se,
                       effect, lci, uci, k }
  - remlSensitivity  true  (so peer-review suppresses DL concern)

Injection: immediately before the QA-enhancer script so its hook wraps
AnalysisEngine.run() FIRST (innermost wrapper). Chain becomes:
   original -> REML-retrofit -> QA-enhancer -> peer-review

After original runs, REML callback fires (populates remlResult), then
QA-enhancer callback fires (sees remlSensitivity=true, skips DL concern
indirectly via peer-review later).

Idempotent (sentinel /*REML-RETROFIT-v1*/). Fails closed when per-trial
data can't be extracted (non-standard measure, missing fields).
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")
SENTINEL = "/*REML-RETROFIT-v1*/"


REML_SCRIPT = r"""<script>/*REML-RETROFIT-v1*/
(function () {
    'use strict';

    function toF(v) { var n = parseFloat(v); return Number.isFinite(n) ? n : null; }
    function allFinite() { for (var i = 0; i < arguments.length; i++) { if (!Number.isFinite(arguments[i])) return false; } return true; }

    function includedTrials() {
        var RM = window.RapidMeta;
        var arr = (RM && RM.state && RM.state.trials) || [];
        return arr.filter(function (t) { return t && t.data && t.included !== false; });
    }

    function detectMeasure() {
        var RM = window.RapidMeta;
        var s = RM.state || {};
        var m = s.effectMeasure || s.measure || s.effect;
        if (m && typeof m === 'string') return m.toUpperCase();
        // Heuristic on first included trial
        var trials = includedTrials();
        if (!trials.length) return 'OR';
        var d = trials[0].data;
        if (d.publishedHR != null) return 'HR';
        if (d.tMean != null || d.tSD != null) return 'MD';
        return 'OR';
    }

    function binaryEffect(d, measure) {
        var tE = toF(d.tE), tN = toF(d.tN), cE = toF(d.cE), cN = toF(d.cN);
        if (tE == null || tN == null || cE == null || cN == null) return null;
        if (tN <= 0 || cN <= 0) return null;
        var tNonE = tN - tE, cNonE = cN - cE;
        if (tNonE < 0 || cNonE < 0) return null;
        var add = (tE === 0 || tNonE === 0 || cE === 0 || cNonE === 0) ? 0.5 : 0;
        var a = tE + add, b = tNonE + add, c = cE + add, e = cNonE + add;
        if (a <= 0 || b <= 0 || c <= 0 || e <= 0) return null;
        var y, v;
        if (measure === 'RR') {
            var pt = a / (a + b), pc = c / (c + e);
            if (pt <= 0 || pc <= 0) return null;
            y = Math.log(pt / pc);
            v = (1 / a) - (1 / (a + b)) + (1 / c) - (1 / (c + e));
        } else {
            // OR default (also used as fallback for HR when publishedHR unavailable)
            y = Math.log(a * e / (b * c));
            v = 1 / a + 1 / b + 1 / c + 1 / e;
        }
        if (!Number.isFinite(y) || !Number.isFinite(v) || v <= 0) return null;
        return { y: y, v: v };
    }

    function hrFromPublished(d) {
        var hr = toF(d.publishedHR), lo = toF(d.hrLCI), hi = toF(d.hrUCI);
        if (hr == null || lo == null || hi == null) return null;
        if (hr <= 0 || lo <= 0 || hi <= 0) return null;
        var y = Math.log(hr);
        var se = (Math.log(hi) - Math.log(lo)) / (2 * 1.959964);
        if (!Number.isFinite(se) || se <= 0) return null;
        return { y: y, v: se * se };
    }

    function mdFromCont(d) {
        var tMean = toF(d.tMean), tSD = toF(d.tSD), tN = toF(d.tN);
        var cMean = toF(d.cMean), cSD = toF(d.cSD), cN = toF(d.cN);
        if (tMean == null || tSD == null || tN == null || cMean == null || cSD == null || cN == null) return null;
        if (tN <= 0 || cN <= 0 || tSD < 0 || cSD < 0) return null;
        var v = (tSD * tSD) / tN + (cSD * cSD) / cN;
        if (!Number.isFinite(v) || v <= 0) return null;
        return { y: tMean - cMean, v: v };
    }

    function perTrialEffects(measure) {
        var trials = includedTrials();
        var eff = [];
        trials.forEach(function (t) {
            var d = t.data, e = null;
            if (measure === 'MD' || measure === 'SMD') {
                e = mdFromCont(d);
            } else if (measure === 'HR') {
                e = hrFromPublished(d) || binaryEffect(d, 'OR');  // fallback
            } else {
                e = binaryEffect(d, measure);
                if (!e) e = hrFromPublished(d);
            }
            if (e && Number.isFinite(e.y) && Number.isFinite(e.v) && e.v > 0) eff.push(e);
        });
        return eff;
    }

    function pauleMandelTau2(y, v) {
        var k = y.length;
        if (k < 2) return 0;
        var tau2 = 0;
        var target = k - 1;
        for (var iter = 0; iter < 200; iter++) {
            var w = v.map(function (vi) { return 1 / (vi + tau2); });
            var sumW = w.reduce(function (a, b) { return a + b; }, 0);
            if (!(sumW > 0)) break;
            var yBar = 0;
            for (var i = 0; i < k; i++) yBar += y[i] * w[i];
            yBar /= sumW;
            var Q = 0;
            for (var j = 0; j < k; j++) { var d = y[j] - yBar; Q += w[j] * d * d; }
            var diff = Q - target;
            if (Math.abs(diff) < 1e-5) break;
            var slope = 0;
            for (var m = 0; m < k; m++) { var dm = y[m] - yBar; slope += -w[m] * w[m] * dm * dm; }
            if (!Number.isFinite(slope) || Math.abs(slope) < 1e-14) break;
            var t2new = Math.max(0, tau2 + diff / slope);
            if (!Number.isFinite(t2new)) break;
            if (Math.abs(t2new - tau2) < 1e-9) { tau2 = t2new; break; }
            tau2 = t2new;
        }
        return tau2;
    }

    function poolWith(y, v, tau2, confLevel) {
        var z = 1.959964;
        if (confLevel && confLevel > 0 && confLevel < 1) {
            // Approximate z from confLevel (assumes normal CI)
            var alpha = 1 - confLevel;
            // Use well-known mapping
            if (Math.abs(confLevel - 0.95) < 0.001) z = 1.959964;
            else if (Math.abs(confLevel - 0.90) < 0.001) z = 1.644854;
            else if (Math.abs(confLevel - 0.99) < 0.001) z = 2.575829;
            // else stay at default 1.959964
        }
        var k = y.length;
        var w = v.map(function (vi) { return 1 / (vi + tau2); });
        var sumW = w.reduce(function (a, b) { return a + b; }, 0);
        var effect = 0;
        for (var i = 0; i < k; i++) effect += y[i] * w[i];
        effect /= sumW;
        var se = 1 / Math.sqrt(sumW);
        return { effect: effect, se: se, lo: effect - z * se, hi: effect + z * se };
    }

    function computeREML() {
        var RM = window.RapidMeta;
        if (!RM || !RM.state || !RM.state.results) return;
        var r = RM.state.results;
        if (r.remlSensitivity && r.remlResult) return;  // already done

        var measure = detectMeasure();
        var effects = perTrialEffects(measure);
        if (effects.length < 2) return;

        var y = effects.map(function (e) { return e.y; });
        var v = effects.map(function (e) { return e.v; });
        var tau2 = pauleMandelTau2(y, v);
        var pool = poolWith(y, v, tau2, r.confLevel || RM.state.confLevel || 0.95);
        var onNat = (measure === 'OR' || measure === 'RR' || measure === 'HR');

        r.tau2Reml = tau2;
        r.remlResult = {
            estimator: 'PM',  // Paule-Mandel (~REML for most cases, recommended for small k)
            measure: measure,
            tau2: tau2,
            logEffect: pool.effect,
            se: pool.se,
            effect: onNat ? Math.exp(pool.effect) : pool.effect,
            lci: onNat ? Math.exp(pool.lo) : pool.lo,
            uci: onNat ? Math.exp(pool.hi) : pool.hi,
            k: effects.length,
        };
        r.remlSensitivity = true;
    }

    function install() {
        var RM = window.RapidMeta;
        if (!RM) return false;
        if (RM.__remlRetrofitInstalled) return true;
        RM.__remlRetrofitInstalled = true;

        if (typeof window.AnalysisEngine === 'object' && window.AnalysisEngine && typeof window.AnalysisEngine.run === 'function') {
            var origRun = window.AnalysisEngine.run;
            window.AnalysisEngine.run = function () {
                var out = origRun.apply(this, arguments);
                try { computeREML(); } catch (e) { /* fail closed */ }
                return out;
            };
        }
        if (RM.state && RM.state.results) {
            try { computeREML(); } catch (e) {}
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
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if SENTINEL in text:
        return f"SKIP {path.name}"

    # Inject immediately before QA-enhancer so REML hook wraps FIRST
    # (innermost; its callback runs before QA-enhancer's callback, so
    # QA-enhancer sees remlSensitivity=true and remlResult populated).
    qa_pos = text.find("/*QA-ENHANCER-v1*/")
    if qa_pos < 0:
        # Fallback: before peer-review
        qa_pos = text.find("/*PEER-REVIEW-v2*/")
        if qa_pos < 0:
            body_pos = text.rfind("</body>")
            if body_pos < 0:
                return f"FAIL {path.name}: no anchor"
            insertion_point = body_pos
        else:
            script_start = text.rfind("<script", 0, qa_pos)
            if script_start < 0:
                return f"FAIL {path.name}: peer-review <script> not found"
            insertion_point = script_start
    else:
        script_start = text.rfind("<script", 0, qa_pos)
        if script_start < 0:
            return f"FAIL {path.name}: QA-enhancer <script> not found"
        insertion_point = script_start

    new_text = text[:insertion_point] + REML_SCRIPT + "\n" + text[insertion_point:]
    out = new_text.replace("\n", "\r\n") if crlf else new_text
    if not dry_run:
        path.write_bytes(out.encode("utf-8"))
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
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
