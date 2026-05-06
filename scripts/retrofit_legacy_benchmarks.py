#!/usr/bin/env python3
# sentinel:skip-file - developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Retrofit benchmark machinery onto the 3 legacy apps that never had it.

Apps: COLCHICINE_CVD, GLP1_CVOT, SGLT2_HF.

Strategy: after the existing /*RM-BRIDGE*/ script tag, inject a self-
contained IIFE that:
  1. Defines the app-specific PUBLISHED_META_BENCHMARKS + BENCHMARK_OUTCOME_MAP
  2. Waits for window.RapidMeta + generateManuscriptText to exist
  3. Attaches getSelectedBenchmarkEntries() to RapidMeta
  4. Monkey-patches generateManuscriptText() to append a benchmark
     comparison paragraph at the bottom of #manuscript-text

Non-invasive - doesn't touch the original IIFE, any realData block, any
engine definition. If the retrofit fails (missing DOM, RapidMeta never
initializes, etc.) the app falls back silently to its original behavior.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

SENTINEL = "/*BENCHMARK-RETROFIT-v1*/"

SPECS = {
    "COLCHICINE_CVD_REVIEW.html": {
        "benchmarks": [
            {"label": "LoDoCo2 colchicine 0.5 mg vs placebo (chronic CAD)", "citation": "Nidorf 2020",
             "year": 2020, "measure": "HR", "estimate": 0.69, "lci": 0.57, "uci": 0.83,
             "k": 1, "n": 5522,
             "scope": "Colchicine 0.5 mg QD vs placebo in chronic CAD; CV death, spontaneous MI, ischemic stroke, or ischemia-driven coronary revascularization. NEJM 2020;383:1838-1847."},
            {"label": "COLCOT colchicine 0.5 mg post-MI", "citation": "Tardif 2019",
             "year": 2019, "measure": "HR", "estimate": 0.77, "lci": 0.61, "uci": 0.96,
             "k": 1, "n": 4745,
             "scope": "Colchicine 0.5 mg QD vs placebo within 30 days post-MI; CV death, resuscitated cardiac arrest, MI, stroke, or urgent hospitalization for angina leading to revascularization. NEJM 2019;381:2497-2505."},
        ],
    },
    "GLP1_CVOT_REVIEW.html": {
        "benchmarks": [
            {"label": "Sattar GLP-1 CVOT meta-analysis", "citation": "Sattar 2021",
             "year": 2021, "measure": "HR", "estimate": 0.86, "lci": 0.80, "uci": 0.93,
             "k": 8, "n": 60080,
             "scope": "GLP-1 RAs vs placebo in T2D; 3-point MACE (CV death + nonfatal MI + nonfatal stroke). Lancet Diabetes Endocrinol 2021;9:653-662."},
        ],
    },
    "SGLT2_HF_REVIEW.html": {
        "benchmarks": [
            {"label": "Vaduganathan 5-trial pooled analysis (SGLT2i HF)", "citation": "Vaduganathan 2022",
             "year": 2022, "measure": "HR", "estimate": 0.77, "lci": 0.72, "uci": 0.82,
             "k": 5, "n": 21947,
             "scope": "SGLT2i across EF spectrum; CV death or first HHF (DAPA-HF + EMPEROR-Reduced + DELIVER + EMPEROR-Preserved + SOLOIST-WHF). Lancet 2022;400:757-767."},
            {"label": "Jhund 5-trial HFrEF-only pool (SGLT2i)", "citation": "Jhund 2022",
             "year": 2022, "measure": "HR", "estimate": 0.78, "lci": 0.72, "uci": 0.84,
             "k": 5, "n": 21947,
             "scope": "SGLT2i pooled across HF spectrum; CV death or HHF subcomponent. Nat Med 2022;28:1956-1964."},
        ],
    },
}


def _escape_js(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _render_benchmark_entry(b: dict) -> str:
    return (
        "{ "
        f"label: '{_escape_js(b['label'])}', "
        f"citation: '{_escape_js(b['citation'])}', "
        f"year: {b['year']}, "
        f"measure: '{b['measure']}', "
        f"estimate: {b['estimate']}, "
        f"lci: {b['lci']}, "
        f"uci: {b['uci']}, "
        f"k: {b['k']}, "
        f"n: {b['n']}, "
        f"scope: '{_escape_js(b['scope'])}' "
        "}"
    )


def build_retrofit_script(benchmarks: list) -> str:
    entries = ",\n            ".join(_render_benchmark_entry(b) for b in benchmarks)
    return f"""<script>{SENTINEL}
(function () {{
    const PUBLISHED_META_BENCHMARKS = {{
        MACE: [
            {entries}
        ]
    }};
    const BENCHMARK_OUTCOME_MAP = {{ default: 'MACE', MACE: 'MACE' }};

    let tries = 0;
    function ready() {{
        if (tries++ > 120) return;
        if (!window.RapidMeta || typeof window.generateManuscriptText !== 'function') {{
            return setTimeout(ready, 100);
        }}
        install();
    }}

    function install() {{
        if (window.RapidMeta.__benchmarkRetrofitInstalled) return;
        window.RapidMeta.__benchmarkRetrofitInstalled = true;

        window.RapidMeta.publishedMetaBenchmarks = PUBLISHED_META_BENCHMARKS;
        window.RapidMeta.getSelectedBenchmarkEntries = function (outcomeKey) {{
            const k = BENCHMARK_OUTCOME_MAP[String(outcomeKey != null ? outcomeKey : 'default')] || null;
            return k ? (PUBLISHED_META_BENCHMARKS[k] || []) : [];
        }};

        const orig = window.generateManuscriptText;
        window.generateManuscriptText = function () {{
            const result = orig.apply(this, arguments);
            try {{
                renderBenchmarkParagraph();
            }} catch (e) {{ /* fall back silently */ }}
            return result;
        }};

        // If manuscript already rendered, re-render now.
        if (window.RapidMeta.state && window.RapidMeta.state.results) {{
            try {{ renderBenchmarkParagraph(); }} catch (e) {{}}
        }}
    }}

    function renderBenchmarkParagraph() {{
        const container = document.getElementById('manuscript-text');
        if (!container) return;
        const r = window.RapidMeta.state && window.RapidMeta.state.results;
        if (!r || r.or == null || r.or === '--') return;

        // Clear any prior retrofit paragraph so we don't stack.
        container.querySelectorAll('.benchmark-retrofit').forEach(n => n.remove());

        const entries = window.RapidMeta.getSelectedBenchmarkEntries('default');
        if (!entries.length) return;

        const currentOr = parseFloat(r.or);
        const currentLci = parseFloat(r.lci);
        const currentUci = parseFloat(r.uci);

        const lines = entries.map(function (b) {{
            const pointInside = Number.isFinite(currentOr) && currentOr >= b.lci && currentOr <= b.uci;
            const ciOverlap = Number.isFinite(currentLci) && Number.isFinite(currentUci)
                ? (currentLci <= b.uci && currentUci >= b.lci) : false;
            const verdict = pointInside ? 'inside published CI'
                : ciOverlap ? 'overlaps published CI'
                : 'diverges from published CI';
            const nStr = typeof b.n === 'number' ? b.n.toLocaleString() : String(b.n);
            return '<li><b>' + b.label + '</b> (' + b.citation + '): ' + b.measure + ' ' +
                b.estimate.toFixed(2) + ' [' + b.lci.toFixed(2) + ', ' + b.uci.toFixed(2) + '], k=' +
                b.k + ', n=' + nStr + '. Current pooled ' + r.or + ' ' + verdict +
                '. <i class="text-slate-500">' + b.scope + '</i></li>';
        }}).join('');

        const p = document.createElement('div');
        p.className = 'benchmark-retrofit mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-300';
        p.innerHTML = '<b class="uppercase tracking-widest text-slate-400 text-[10px]">Published meta-analysis comparator</b>' +
            '<ul class="mt-2 space-y-2 list-disc pl-4">' + lines + '</ul>';
        container.appendChild(p);
    }}

    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', ready);
    }} else {{
        ready();
    }}
}})();
</script>
"""


def apply_to_file(path: pathlib.Path, benchmarks: list, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if SENTINEL in text:
        return f"SKIP {path.name}: already-retrofitted"
    # Find RM-BRIDGE script tag end and inject after it.
    anchor = "/*RM-BRIDGE*/"
    anchor_pos = text.find(anchor)
    if anchor_pos < 0:
        return f"FAIL {path.name}: RM-BRIDGE anchor not found"
    # Find the closing </script> after RM-BRIDGE
    close_tag = "</script>"
    close_pos = text.find(close_tag, anchor_pos)
    if close_pos < 0:
        return f"FAIL {path.name}: RM-BRIDGE </script> not found"
    insertion_point = close_pos + len(close_tag)

    script = build_retrofit_script(benchmarks)
    new_text = text[:insertion_point] + "\n" + script + text[insertion_point:]

    if not dry_run:
        path.write_text(new_text, encoding="utf-8", newline="")
    return f"OK   {path.name}: benchmark retrofit injected ({len(benchmarks)} entries)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    ok = fail = skip = 0
    for name, spec in SPECS.items():
        p = ROOT / name
        if not p.exists():
            print(f"MISS {name}: not found")
            fail += 1
            continue
        r = apply_to_file(p, spec["benchmarks"], args.dry_run)
        print(r)
        if r.startswith("OK"):
            ok += 1
        elif r.startswith("SKIP"):
            skip += 1
        else:
            fail += 1
    print(f"\nLegacy retrofit: {ok} OK / {skip} skip / {fail} fail / {'dry-run' if args.dry_run else 'apply'}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
