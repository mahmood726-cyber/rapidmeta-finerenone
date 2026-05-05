"""Codemod: inject the PairwisePool live-repool widget into NMA reviews.

Idempotent. Safe to run twice. Skips files that:
  1. Already contain `vendor/pairwise-pool.js` (already patched).
  2. Don't have the `nma-league-container` landmark (no canonical insertion
     point — we don't risk a guess on these).

For each remaining file:
  A. Insert  `<script src="vendor/pairwise-pool.js"></script>`  BEFORE the
     final </head> in the document (i.e. the real closing head, not any
     <head> embedded inside an exported-PDF template).
  B. Insert a "Live Re-pool from Raw 2x2 (verifier)" panel + inline script
     immediately after the league-table .glass panel — same insertion the
     POC used on GLP1_CVOT and UC_BIOLOGICS.

Use the EXACT same widget block as those POCs so the corpus stays uniform.
Run with --dry-run first per scripts/lessons.md codemod-discipline rule.
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

SCRIPT_TAG = (
    '\n    <!-- PairwisePool: live re-pool from raw 2x2 (DL+REML+HKSJ+PI per Cochrane v6.5) -->\n'
    '    <script src="vendor/pairwise-pool.js"></script>\n'
)

# Block to insert immediately after the league-table .glass panel close.
WIDGET_BLOCK = '''


                        <!-- Live Re-pool panel (PairwisePool transplant from TruthCert-PairwisePro) -->
                        <div class="glass p-10 rounded-[40px] border border-slate-800">
                            <h3 class="text-sm font-bold opacity-60 uppercase tracking-[0.3em] mb-2">Live Re-pool from Raw 2&times;2 (verifier)</h3>
                            <p class="text-[11px] text-slate-400 mb-4">
                                Re-pools the trial-level raw event counts in <code>realData</code> using DerSimonian-Laird random-effects + HKSJ + Cochrane v6.5 prediction interval (t<sub>k-1</sub>).
                                Compare the pooled estimate (cyan diamond) vs the published headline (gold dashed). Per-trial rows show the
                                back-transformed RR with 95% CI and RE weight.
                            </p>
                            <div class="flex gap-2 items-center mb-4">
                                <button id="ppPoolBtn" class="px-4 py-2 text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white rounded transition">Re-pool from raw counts</button>
                                <select id="ppMeasureSel" class="px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded text-slate-200">
                                    <option value="RR">Risk ratio (RR)</option>
                                    <option value="OR">Odds ratio (OR)</option>
                                </select>
                                <span id="ppStatus" class="text-[11px] text-slate-500"></span>
                            </div>
                            <div id="ppForest"></div>
                        </div>

                        <script>
                        (function () {
                            function getTrials() {
                                // Canonical path on this corpus: window.RapidMeta.realData
                                var rd = null;
                                try { rd = window.RapidMeta && window.RapidMeta.realData; } catch (e) {}
                                if (!rd) {
                                    try { rd = window.RapidMeta && window.RapidMeta.state && window.RapidMeta.state.protocol && window.RapidMeta.state.protocol.realData; } catch (e) {}
                                }
                                if (!rd) {
                                    for (var k in window) {
                                        var v = window[k];
                                        if (v && typeof v === 'object' && !Array.isArray(v)) {
                                            var keys = Object.keys(v);
                                            if (keys.length && keys[0].startsWith('NCT')) {
                                                var probe = v[keys[0]];
                                                if (probe && probe.tE != null && probe.tN != null && probe.cE != null) {
                                                    rd = v; break;
                                                }
                                            }
                                        }
                                    }
                                }
                                if (!rd) return [];
                                return Object.keys(rd).map(function (key) {
                                    var t = rd[key];
                                    return {
                                        name: t.name || key,
                                        tE: t.tE, tN: t.tN, cE: t.cE, cN: t.cN,
                                        publishedHR: t.publishedHR
                                    };
                                });
                            }

                            function getReferenceEffect(trials) {
                                var hrs = trials.map(function (t) { return t.publishedHR; }).filter(function (v) { return v && isFinite(v) && v > 0; });
                                if (!hrs.length) return null;
                                hrs.sort(function (a, b) { return a - b; });
                                return hrs[Math.floor(hrs.length / 2)];
                            }

                            function go() {
                                var measure = document.getElementById('ppMeasureSel').value;
                                var trials = getTrials();
                                var status = document.getElementById('ppStatus');
                                var container = document.getElementById('ppForest');
                                if (!trials.length) {
                                    status.textContent = 'No realData found.';
                                    container.innerHTML = '<div style="color:#f87171;font-size:12px;padding:1em;">Could not locate realData on this page.</div>';
                                    return;
                                }
                                var res = window.PairwisePool.pool2x2(trials, { measure: measure });
                                if (res.error) {
                                    status.textContent = res.error;
                                    container.innerHTML = '<div style="color:#f87171;font-size:12px;padding:1em;">' + res.error + '</div>';
                                    return;
                                }
                                var ref = getReferenceEffect(trials);
                                window.PairwisePool.renderForest(container, res, { referenceEffect: ref });
                                status.textContent = 'k=' + res.k_used + ' trials pooled · τ²=' + res.tau2.toFixed(3) + ' · I²=' + res.I2.toFixed(0) + '% · ' + measure + '=' + res.mu.toFixed(3) + ' (' + res.ci_lo.toFixed(2) + '–' + res.ci_hi.toFixed(2) + ')';
                            }

                            document.addEventListener('DOMContentLoaded', function () {
                                var btn = document.getElementById('ppPoolBtn');
                                if (btn) btn.addEventListener('click', go);
                            });
                        })();
                        </script>


'''


def find_league_close(text: str) -> int | None:
    """Find byte position immediately after the .glass panel that contains
    `id="nma-league-container"`. Returns position right after the panel's
    closing </div>, or None if landmark not found / structure unexpected."""
    m = re.search(r'id="nma-league-container"', text)
    if not m:
        return None
    # Walk backward to find the enclosing `<div class="glass ...` opener.
    pre = text[:m.start()]
    open_re = re.compile(r'<div class="glass[^"]*"[^>]*>', re.IGNORECASE)
    opens = list(open_re.finditer(pre))
    if not opens:
        return None
    open_pos = opens[-1].start()
    # Walk forward from open_pos counting <div / </div> until balanced.
    depth = 0
    i = open_pos
    while i < len(text):
        m_open = text.find('<div', i)
        m_close = text.find('</div>', i)
        if m_close == -1:
            return None
        if m_open != -1 and m_open < m_close:
            depth += 1
            i = m_open + 4
        else:
            depth -= 1
            i = m_close + 6
            if depth == 0:
                return i
    return None


def find_real_head_close(text: str) -> int | None:
    """Find the </head> that closes the real document head (first one in source)."""
    m = re.search(r'</head>', text)
    return m.start() if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Stop after N file patches (0 = all)")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_NMA_REVIEW.html"))
    print(f"Scanning {len(files)} *_NMA_REVIEW.html files ...")

    patched, skip_already, skip_no_landmark, errors = 0, 0, 0, 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")

        if 'vendor/pairwise-pool.js' in text:
            skip_already += 1
            continue

        head_pos = find_real_head_close(text)
        league_end = find_league_close(text)
        if head_pos is None or league_end is None:
            skip_no_landmark += 1
            print(f"  SKIP {hp.name}: missing landmark ({'no </head>' if head_pos is None else 'no league container'})")
            continue

        # Apply later position FIRST so earlier positions remain valid.
        new_text = text[:league_end] + WIDGET_BLOCK + text[league_end:]
        head_pos2 = find_real_head_close(new_text)
        new_text = new_text[:head_pos2] + SCRIPT_TAG + new_text[head_pos2:]

        if not args.dry_run:
            hp.write_text(new_text, encoding="utf-8")
        patched += 1
        print(f"  PATCH {hp.name}")
        if args.limit and patched >= args.limit:
            print(f"  --limit {args.limit} reached, stopping.")
            break

    print(f"\n=== Summary ===")
    print(f"  Patched:           {patched}")
    print(f"  Already-fixed:     {skip_already}")
    print(f"  Skipped (no NMA):  {skip_no_landmark}")
    print(f"  Errors:            {errors}")
    if args.dry_run:
        print("\n  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
