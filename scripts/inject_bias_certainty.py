"""Codemod: inject the Tier-2 bias & certainty panel into NMA reviews.

Wires three new modules into a single combined panel:
  - vendor/doi-lfk.js                        (Furuya-Kanamori 2018)
  - vendor/comparison-adjusted-funnel.js     (Chaimani-Salanti 2012)
  - vendor/cinema-certainty.js               (Nikolakopoulou 2020)

Idempotent. Skips files already containing `vendor/cinema-certainty.js`.

For each *_NMA_REVIEW.html file:
  1. Insert script tags for all 3 modules right after the existing
     vendor/nma-consistency.js include.
  2. Insert a "Bias and Certainty (Tier 2 Transplants)" panel after the
     existing Network Consistency panel.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

SCRIPT_TAGS = (
    '\n    <!-- Tier-2 transplants: small-study bias + per-edge certainty -->\n'
    '    <script src="vendor/doi-lfk.js"></script>\n'
    '    <script src="vendor/comparison-adjusted-funnel.js"></script>\n'
    '    <script src="vendor/cinema-certainty.js"></script>\n'
)

CONS_INCLUDE_RE = re.compile(r'<script\s+src="vendor/nma-consistency\.js"\s*></script>')
HEAD_CLOSE_RE = re.compile(r'</head>')

# Insert AFTER the existing consistency panel block
EXISTING_CONS_RESULT_DIV = re.compile(
    r'<div id="nmaConsResult"></div>\s*</div>'
)

PANEL_HTML = '''

                            <!-- Tier-2 panel: Doi/LFK + Comparison-adjusted funnel + CINeMA certainty -->
                            <div class="glass p-10 rounded-[40px] border border-slate-800 mt-10">
                                <h3 class="text-sm font-bold opacity-60 uppercase tracking-[0.3em] mb-2">Bias &amp; Certainty (Tier 2 Transplants)</h3>
                                <p class="text-[11px] text-slate-400 mb-4">
                                    Small-study-effects (Doi plot + LFK index, Furuya-Kanamori 2018), comparison-adjusted funnel (Chaimani &amp; Salanti 2012),
                                    and per-pairwise certainty (CINeMA, Nikolakopoulou 2020). Tools chosen for k&lt;10 networks where Egger's test is underpowered.
                                </p>
                                <div class="flex gap-2 items-center mb-4 flex-wrap">
                                    <button id="biasDoiBtn" class="px-4 py-2 text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white rounded">Doi plot + LFK</button>
                                    <button id="biasFunnelBtn" class="px-4 py-2 text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white rounded">Comparison-adjusted funnel</button>
                                    <button id="biasCinemaBtn" class="px-4 py-2 text-xs font-bold bg-violet-600 hover:bg-violet-500 text-white rounded">CINeMA certainty</button>
                                    <select id="biasMeasure" class="px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200">
                                        <option value="RR">RR</option>
                                        <option value="OR">OR</option>
                                    </select>
                                </div>
                                <div id="biasOutput" class="space-y-4"></div>
                            </div>

                            <script>
                            (function () {
                                var lastResult = {};

                                function getCfgAndData() {
                                    return {
                                        cfg: window.NMA_CONFIG,
                                        rd: window.RapidMeta && window.RapidMeta.realData,
                                    };
                                }

                                function trialEffect(t, measure) {
                                    if (!t || t.tE == null || t.tN == null || t.cE == null || t.cN == null) return null;
                                    if (t.tN <= 0 || t.cN <= 0) return null;
                                    if (t.tE > t.tN || t.cE > t.cN || t.tE < 0 || t.cE < 0) return null;
                                    if (t.tE === 0 && t.cE === 0) return null;
                                    var tEa = t.tE, tNa = t.tN, cEa = t.cE, cNa = t.cN;
                                    if (tEa === 0 || cEa === 0 || tEa === tNa || cEa === cNa) {
                                        tEa += 0.5; tNa += 1; cEa += 0.5; cNa += 1;
                                    }
                                    if (measure === 'OR') {
                                        var a = tEa, b = tNa - tEa, c = cEa, d = cNa - cEa;
                                        return { yi: Math.log((a * d) / (b * c)), vi: 1/a + 1/b + 1/c + 1/d };
                                    }
                                    return {
                                        yi: Math.log((tEa / tNa) / (cEa / cNa)),
                                        vi: 1/tEa - 1/tNa + 1/cEa - 1/cNa,
                                    };
                                }

                                function buildAllStudies(rd, cfg, measure) {
                                    var out = [];
                                    (cfg.comparisons || []).forEach(function (c) {
                                        (c.trials || []).forEach(function (nct) {
                                            var t = rd[nct];
                                            var e = trialEffect(t, measure);
                                            if (!e) return;
                                            out.push({ name: (t && t.name) || nct, yi: e.yi, vi: e.vi, edge: c.t1 + ' vs ' + c.t2 });
                                        });
                                    });
                                    return out;
                                }

                                function showError(msg) {
                                    document.getElementById('biasOutput').innerHTML =
                                        '<div style="color:#f87171;font-size:12px;padding:1em;">' + msg + '</div>';
                                }

                                function runDoi() {
                                    var ctx = getCfgAndData();
                                    if (!ctx.rd || !ctx.cfg) return showError('Need realData + NMA_CONFIG.');
                                    var measure = document.getElementById('biasMeasure').value;
                                    var studies = buildAllStudies(ctx.rd, ctx.cfg, measure);
                                    if (studies.length < 3) return showError('Doi/LFK needs k≥3 trials.');
                                    var res = window.DoiLFK.compute(studies);
                                    var div = document.getElementById('biasOutput');
                                    div.innerHTML = '<h4 style="color:#fcd34d;font-size:13px;font-weight:700;margin-bottom:8px;">Doi plot + LFK (pooled across all direct comparisons)</h4><div id="biasDoiInner"></div>';
                                    window.DoiLFK.render('biasDoiInner', res);
                                    lastResult.doi = res;
                                }

                                function runFunnel() {
                                    var ctx = getCfgAndData();
                                    if (!ctx.rd || !ctx.cfg) return showError('Need realData + NMA_CONFIG.');
                                    var measure = document.getElementById('biasMeasure').value;
                                    var res = window.ComparisonAdjustedFunnel.compute(ctx.rd, ctx.cfg, { measure: measure });
                                    var div = document.getElementById('biasOutput');
                                    div.innerHTML = '<h4 style="color:#22d3ee;font-size:13px;font-weight:700;margin-bottom:8px;">Comparison-adjusted funnel (Chaimani &amp; Salanti 2012)</h4><div id="biasFunnelInner"></div>';
                                    window.ComparisonAdjustedFunnel.render('biasFunnelInner', res);
                                    lastResult.funnel = res;
                                }

                                function runCinema() {
                                    var ctx = getCfgAndData();
                                    if (!ctx.rd || !ctx.cfg) return showError('Need realData + NMA_CONFIG.');
                                    if (!window.NMAConsistency || !window.PairwisePool || !window.CinemaCertainty) {
                                        return showError('Required modules not loaded.');
                                    }
                                    var measure = document.getElementById('biasMeasure').value;
                                    // Reuse NMAConsistency to get edge pools + node-split p-values
                                    var cons = window.NMAConsistency.analyze(ctx.rd, ctx.cfg, { measure: measure });
                                    var splitByEdge = {};
                                    (cons.splits || []).forEach(function (s) {
                                        var k = [s.edge.t1, s.edge.t2].sort().join('|');
                                        splitByEdge[k] = s.p;
                                    });
                                    // For each edge, also compute Doi/LFK from its trials individually
                                    var edges = (cons.edges || []).filter(function (e) { return e.pooled; });
                                    var rated = edges.map(function (e) {
                                        var k = [e.t1, e.t2].sort().join('|');
                                        // Per-edge LFK: build study list from this edge only
                                        var trials = (e.trials || [])
                                            .map(function (nct) { return trialEffect(ctx.rd[nct], measure); })
                                            .filter(Boolean);
                                        var lfk = null;
                                        if (trials.length >= 3) {
                                            var d = window.DoiLFK.compute(trials);
                                            if (!d.error) lfk = d.lfk;
                                        }
                                        var rating = window.CinemaCertainty.rateEdge(e.pooled, {
                                            lfk: lfk,
                                            splitP: splitByEdge[k],
                                            isStar: cons.network.isStar,
                                        });
                                        return {
                                            t1: e.t1, t2: e.t2, label: e.t1 + ' vs ' + e.t2,
                                            rating: rating,
                                        };
                                    });
                                    var div = document.getElementById('biasOutput');
                                    div.innerHTML = '<h4 style="color:#c4b5fd;font-size:13px;font-weight:700;margin-bottom:8px;">CINeMA certainty rating per direct comparison</h4><div id="biasCinemaInner"></div>';
                                    window.CinemaCertainty.render('biasCinemaInner', rated);
                                    lastResult.cinema = rated;
                                }

                                document.addEventListener('DOMContentLoaded', function () {
                                    var d = document.getElementById('biasDoiBtn');
                                    var f = document.getElementById('biasFunnelBtn');
                                    var c = document.getElementById('biasCinemaBtn');
                                    if (d) d.addEventListener('click', runDoi);
                                    if (f) f.addEventListener('click', runFunnel);
                                    if (c) c.addEventListener('click', runCinema);
                                });
                            })();
                            </script>
'''


def patch(text: str):
    if 'vendor/cinema-certainty.js' in text:
        return text, "ALREADY"
    cons = CONS_INCLUDE_RE.search(text)
    if cons:
        new_text = text[:cons.end()] + SCRIPT_TAGS + text[cons.end():]
    else:
        head = HEAD_CLOSE_RE.search(text)
        if not head:
            return text, "NO_HEAD"
        new_text = text[:head.start()] + SCRIPT_TAGS + text[head.start():]
    landmark = EXISTING_CONS_RESULT_DIV.search(new_text)
    if not landmark:
        return text, "NO_LANDMARK"
    new_text = new_text[:landmark.end()] + PANEL_HTML + new_text[landmark.end():]
    return new_text, "PATCHED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_NMA_REVIEW.html"))
    print(f"Patching {len(files)} *_NMA_REVIEW.html files ...")

    counts = {"PATCHED": 0, "ALREADY": 0, "NO_HEAD": 0, "NO_LANDMARK": 0}
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status = patch(text)
        counts[status] += 1
        if status == "PATCHED":
            print(f"  PATCH    {hp.name}")
            if not args.dry_run:
                hp.write_text(new_text, encoding="utf-8")
        elif status != "ALREADY":
            print(f"  {status}  {hp.name}")

    print(f"\n=== Summary ===")
    for k, v in counts.items():
        print(f"  {k:15s} {v}")
    if args.dry_run:
        print("  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
