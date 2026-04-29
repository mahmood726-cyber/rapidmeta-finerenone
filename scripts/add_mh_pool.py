"""
Add Mantel-Haenszel (MH) OR pool as a sensitivity scenario alongside Peto OR.

Per Cochrane Handbook v6.5 §10.4.1: MH is preferred over inverse-variance for
binary outcomes when events are sparse. RBG (Robins-Breslow-Greenland 1986)
variance formula used for log-MH-OR SE.

Adds:
- _mhPool(plotData, zCrit) method right after _petoPool.
- Scenario push in the sensitivity scenarios block, right after the Peto
  push, with same useHR / hasRare gating logic.

Idempotent: skipped if _mhPool already in src.

Usage: python scripts/add_mh_pool.py [--dry-run]
"""
import argparse
import io
import os
import sys

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.environ.get(
    'RAPIDMETA_REPO_ROOT',
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

# 1. Insert _mhPool method right after _petoPool (anchor: closing brace of _petoPool)
PETO_OLD = (
    "                return { or: Math.exp(logOR), lci: Math.exp(logOR - zCrit * se), uci: Math.exp(logOR + zCrit * se), pValue: 2 * (1 - normalCDF(Math.abs(logOR / se))) };\n"
    "\n"
    "\n"
    "            },\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "            _remlHksjPool(plotData, confLevel) {"
)
PETO_NEW = (
    "                return { or: Math.exp(logOR), lci: Math.exp(logOR - zCrit * se), uci: Math.exp(logOR + zCrit * se), pValue: 2 * (1 - normalCDF(Math.abs(logOR / se))) };\n"
    "\n"
    "\n"
    "            },\n"
    "\n"
    "\n"
    "            // Mantel-Haenszel OR with Robins-Breslow-Greenland (1986) variance.\n"
    "            // Cochrane Handbook v6.5 §10.4.1: preferred over inverse-variance for\n"
    "            // sparse binary data. No 0.5 correction required.\n"
    "            _mhPool(plotData, zCrit) {\n"
    "                let sumR = 0, sumS = 0;\n"
    "                let sumPR = 0, sumPS_QR = 0, sumQS = 0;\n"
    "                plotData.forEach(d => {\n"
    "                    const a = d.tE, b = d.tN - d.tE, c = d.cE, dd = d.cN - d.cE;\n"
    "                    const N = a + b + c + dd;\n"
    "                    if (N <= 0) return;\n"
    "                    const Ri = (a * dd) / N;\n"
    "                    const Si = (b * c) / N;\n"
    "                    const Pi = (a + dd) / N;\n"
    "                    const Qi = (b + c) / N;\n"
    "                    sumR += Ri;\n"
    "                    sumS += Si;\n"
    "                    sumPR += Pi * Ri;\n"
    "                    sumPS_QR += Pi * Si + Qi * Ri;\n"
    "                    sumQS += Qi * Si;\n"
    "                });\n"
    "                if (sumR <= 0 || sumS <= 0) return { or: NaN, lci: NaN, uci: NaN, pValue: NaN };\n"
    "                const logOR = Math.log(sumR / sumS);\n"
    "                const var_log = sumPR / (2 * sumR * sumR)\n"
    "                              + sumPS_QR / (2 * sumR * sumS)\n"
    "                              + sumQS / (2 * sumS * sumS);\n"
    "                const se = Math.sqrt(Math.max(0, var_log));\n"
    "                const lci = Math.exp(logOR - zCrit * se);\n"
    "                const uci = Math.exp(logOR + zCrit * se);\n"
    "                const pValue = 2 * (1 - normalCDF(Math.abs(logOR / se)));\n"
    "                return { or: Math.exp(logOR), lci, uci, pValue };\n"
    "            },\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "            _remlHksjPool(plotData, confLevel) {"
)

# 2. Add MH scenario push right after the Peto scenario block (both branches).
SCENARIO_OLD = (
    "                if (!useHR) {\n"
    "\n"
    "\n"
    "                    const hasRare = plotData.some(d => (d.ter != null && d.ter < 0.05) || (d.cer != null && d.cer < 0.05));\n"
    "\n"
    "\n"
    "                    if (hasRare) {\n"
    "\n"
    "\n"
    "                        const petoResult = this._petoPool(plotData, zCrit);\n"
    "\n"
    "\n"
    "                        scenarios.push(this._classify('Peto OR', petoResult.or, petoResult.lci, petoResult.uci, petoResult.pValue, k, pOR, lci, uci));\n"
    "\n"
    "\n"
    "                    } else {\n"
    "\n"
    "\n"
    "                        scenarios.push({ label: 'Peto OR', or: null, lci: null, uci: null, pValue: null, k, concordance: 'grey', note: 'N/A \\u2014 no rare-event studies' });\n"
    "\n"
    "\n"
    "                    }\n"
    "\n"
    "\n"
    "                } else {\n"
    "\n"
    "\n"
    "                    scenarios.push({ label: 'Peto OR', or: null, lci: null, uci: null, pValue: null, k, concordance: 'grey', note: 'N/A \\u2014 Peto requires event counts' });\n"
    "\n"
    "\n"
    "                }"
)
SCENARIO_NEW = (
    SCENARIO_OLD
    + "\n"
    + "\n"
    + "                // Scenario 3b: Mantel-Haenszel OR (Cochrane v6.5 §10.4.1 sparse-data preference)\n"
    + "                if (!useHR) {\n"
    + "                    const _hasCounts = plotData.every(d => d.tE != null && d.cE != null && d.tN != null && d.cN != null);\n"
    + "                    if (_hasCounts) {\n"
    + "                        const mhResult = this._mhPool(plotData, zCrit);\n"
    + "                        if (Number.isFinite(mhResult.or)) {\n"
    + "                            scenarios.push(this._classify('Mantel-Haenszel OR', mhResult.or, mhResult.lci, mhResult.uci, mhResult.pValue, k, pOR, lci, uci));\n"
    + "                        } else {\n"
    + "                            scenarios.push({ label: 'Mantel-Haenszel OR', or: null, lci: null, uci: null, pValue: null, k, concordance: 'grey', note: 'N/A \\u2014 zero pooled cell sum' });\n"
    + "                        }\n"
    + "                    } else {\n"
    + "                        scenarios.push({ label: 'Mantel-Haenszel OR', or: null, lci: null, uci: null, pValue: null, k, concordance: 'grey', note: 'N/A \\u2014 missing event counts' });\n"
    + "                    }\n"
    + "                } else {\n"
    + "                    scenarios.push({ label: 'Mantel-Haenszel OR', or: null, lci: null, uci: null, pValue: null, k, concordance: 'grey', note: 'N/A \\u2014 MH requires event counts' });\n"
    + "                }"
)

FIXED_MARKER = "_mhPool"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    print(f'Mode: {"DRY-RUN" if args.dry_run else "APPLY"}')
    files = sorted(
        f for f in os.listdir(ROOT)
        if f.endswith('_REVIEW.html') and not f.endswith('.bak.html')
    )
    summary = {'changed': 0, 'unchanged': 0, 'no_anchor': 0}
    for fname in files:
        path = os.path.join(ROOT, fname)
        src = open(path, 'r', encoding='utf-8').read()
        if FIXED_MARKER in src:
            summary['unchanged'] += 1
            continue
        if PETO_OLD not in src:
            summary['no_anchor'] += 1
            continue
        out = src.replace(PETO_OLD, PETO_NEW, 1)
        if SCENARIO_OLD in out:
            out = out.replace(SCENARIO_OLD, SCENARIO_NEW, 1)
        if not args.dry_run:
            open(path, 'w', encoding='utf-8').write(out)
        summary['changed'] += 1
    print(f'Summary: {summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
