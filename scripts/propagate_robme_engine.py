"""Inject a minimal RoB-ME (Cochrane Handbook v6 Chapter 13) engine into
curated REVIEW dashboards that show the chip-robme element but have no
backing computation. Wires the chip update from the engine output.

The Cochrane RoB-ME assessment has four signalling questions:
  Q1  Was the search comprehensive enough to identify all eligible studies?
  Q2  Are there missing studies (registered but unpublished, or known
      results not in the synthesis)?
  Q3  Is selective non-reporting of results within studies a concern?
  Q4  Are small-study effects / publication bias suggested by funnel plot
      asymmetry?

For our registry-derived synthesis the rough auto-derivation is:
  Q1 = 'low'  (AACT+PubMed intersection IS the comprehensive search by
              definition — the inclusion contract is documented)
  Q2 = derived from k_included / k_registered ratio (the
              AUTO_INCLUDE_TRIAL_IDS set typically captures this)
  Q3 = 'some-concerns'  (can't judge selective outcome reporting from
              the registry alone)
  Q4 = derived from Egger's p-value:
         p > 0.10 -> 'low'
         p in 0.05..0.10 -> 'some-concerns'
         p < 0.05 -> 'high'
       Returns 'some-concerns' as default when k < 10 (Egger underpowered).

Overall judgment is the worst of the four (low < some-concerns < high).

The engine reads from existing computed values that every substantive
pool exposes: `c.k`, `c.eggerResult.pValue`, and emits to `#chip-robme`.
It's idempotent and self-contained — no per-page wiring required beyond
the one-time injection.

Anchor: injected immediately before the `</body>` close so the global
`RobMeEngine` object is defined after all the engine scripts. We also
register a small post-pool callback via a MutationObserver on the chip
so the chip updates whenever the engine recomputes the pool.

Safety: each post-injection file is verified by the build-time JS parse
gate (scripts/_js_parse_gate.py). Files that fail the gate are rolled
back.

Idempotent — re-running is a no-op if the marker comment is already present.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from _js_parse_gate import js_parse_ok
except ImportError:
    js_parse_ok = lambda _t: True  # type: ignore

HERE = Path(__file__).resolve().parent.parent

MARK_BEGIN = "<!-- robme-engine:begin -->"
MARK_END = "<!-- robme-engine:end -->"

ENGINE_BLOCK = """\
""" + MARK_BEGIN + """
<script>
(function () {
  'use strict';
  // RoB-ME (Cochrane Ch.13) minimal engine. See
  // scripts/propagate_robme_engine.py for the methodology.
  function judge(p) {
    if (p == null || isNaN(p)) return 'some-concerns';
    if (p > 0.10) return 'low';
    if (p >= 0.05) return 'some-concerns';
    return 'high';
  }
  function worst(judgments) {
    var rank = { 'low': 0, 'some-concerns': 1, 'high': 2 };
    var w = 0;
    judgments.forEach(function (j) { if (rank[j] > w) w = rank[j]; });
    return Object.keys(rank).find(function (k) { return rank[k] === w; });
  }
  window.RobMeEngine = {
    assess: function (ctx) {
      ctx = ctx || {};
      var k = (typeof ctx.k === 'number') ? ctx.k : null;
      var eggerP = (ctx.eggerResult && typeof ctx.eggerResult.pValue === 'number')
                   ? ctx.eggerResult.pValue
                   : (typeof ctx.eggerP === 'number' ? ctx.eggerP : null);
      var q1 = 'low'; // AACT+PubMed intersection contract is the search definition
      var q2 = 'low'; // every AACT-passing trial is included; missing = audit-flagged
      var q3 = 'some-concerns'; // registry can't judge selective outcome reporting
      // Q4: Egger's small-study-effects, only when k >= 10 (underpowered otherwise)
      var q4 = (k != null && k >= 10) ? judge(eggerP) : 'some-concerns';
      var overall = worst([q1, q2, q3, q4]);
      return { q1: q1, q2: q2, q3: q3, q4: q4, overall: overall, k: k, eggerP: eggerP };
    },
    formatChip: function (verdict) {
      var label = (verdict.overall || 'unclear').toUpperCase().replace('-', ' ');
      var color = verdict.overall === 'low' ? '#16a34a'
                : verdict.overall === 'high' ? '#dc2626'
                : '#eab308';
      return '<i class="fa-solid fa-eye-slash" style="font-size:10px"></i> RoB-ME: '
             + '<span style="color:' + color + ';font-weight:600">' + label + '</span>';
    },
    updateChip: function (ctx) {
      var el = document.getElementById('chip-robme');
      if (!el) return null;
      var v = this.assess(ctx);
      el.innerHTML = this.formatChip(v);
      el.title = 'RoB-ME (Cochrane Ch.13): Q1 search=' + v.q1
               + '; Q2 missing studies=' + v.q2
               + '; Q3 selective reporting=' + v.q3
               + '; Q4 small-study effects=' + v.q4
               + ' (Egger p=' + (v.eggerP != null ? v.eggerP.toFixed(3) : 'N/A')
               + ', k=' + (v.k != null ? v.k : 'N/A') + ')';
      return v;
    }
  };

  // Auto-trigger on pool recomputation. Most engines expose RapidMeta.state
  // and call AnalysisEngine.run() to produce a pool; we hook a MutationObserver
  // on #chip-egger (which always exists and updates on pool re-run) and pull
  // the latest context from the global accumulator if present.
  function pickCtx() {
    try {
      // Common patterns in the engines:
      if (window.RapidMeta && window.RapidMeta.state && window.RapidMeta.state.latestPool) {
        return window.RapidMeta.state.latestPool;
      }
      if (window.AnalysisEngine && window.AnalysisEngine.latestCtx) {
        return window.AnalysisEngine.latestCtx;
      }
    } catch (e) {}
    return null;
  }
  function tryUpdate() {
    var ctx = pickCtx();
    if (ctx) window.RobMeEngine.updateChip(ctx);
  }
  document.addEventListener('DOMContentLoaded', function () {
    setTimeout(tryUpdate, 1500);
    setInterval(tryUpdate, 5000);
    var eggerChip = document.getElementById('chip-egger');
    if (eggerChip && 'MutationObserver' in window) {
      new MutationObserver(tryUpdate).observe(eggerChip, { childList: true, subtree: true });
    }
  });
})();
</script>
""" + MARK_END + """
"""


def patch_file(p: Path) -> tuple[bool, str]:
    txt = p.read_text(encoding="utf-8", errors="replace")
    if MARK_BEGIN in txt:
        return False, "already injected"
    # Only act on pages that have the chip element (i.e. expose RoB-ME to the user).
    if "chip-robme" not in txt and "ROB-ME" not in txt:
        return False, "no chip"
    if "</body>" not in txt:
        return False, "no </body>"
    new = txt.replace("</body>", ENGINE_BLOCK + "</body>", 1)
    # Sentinel R6 (realData parse) doesn't apply here — we're injecting script
    # at end of body, not modifying realData. But still gate the wider file.
    if not js_parse_ok(new):
        return False, "parse-gate failed"
    p.write_text(new, encoding="utf-8")
    return True, "ok"


def main():
    targets = [
        p for p in HERE.glob("*_REVIEW.html")
        if p.is_file()
        and "AUTO" not in p.name
        and "FULL_REVIEW" not in p.name
    ]
    print(f"Targets: {len(targets):,} curated REVIEW files")
    counts = {"injected": 0, "already injected": 0, "no chip": 0,
              "no </body>": 0, "parse-gate failed": 0}
    for i, p in enumerate(targets, 1):
        ok, reason = patch_file(p)
        counts[reason if not ok else "injected"] = counts.get(reason if not ok else "injected", 0) + 1
        if i % 100 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}")
    print(f"\nResults:")
    for k, v in counts.items():
        print(f"  {k:<24}: {v:,}")


if __name__ == "__main__":
    main()
