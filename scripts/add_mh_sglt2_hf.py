"""
Surgical patch: port `mhPoolOR` + `mhPoolRR` methods + call site +
methods.push into SGLT2_HF_REVIEW.html.

Context: REM-ENG-1 V8 from outputs/reverification_triage.md.

Of the three v6.5-non-compliant dashboards identified by
audit_v65_engine_coverage.py, the audit's V8 fail was actually a
naming-convention mismatch for COLCHICINE_CVD and GLP1_CVOT (both
already carry `mhPoolOR`/`mhPoolRR` older-style methods rather than
the IL23 `_mhPool` style). The Sentinel rule was tightened in a
sibling commit to match either style on the substring `mhPool`.

SGLT2_HF, however, genuinely has no MH at all. This script ports the
older-style MH methods + call site directly from COLCHICINE_CVD with
zero structural changes (same indent, same double-blank-line spacing).

Idempotent: skipped if `mhPoolOR` is already in the file.

Usage:
  python scripts/add_mh_sglt2_hf.py [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "SGLT2_HF_REVIEW.html"

# ============================================================================
# Patch 1: insert mhPoolOR + mhPoolRR method definitions before
# computePublishedRatioCore. Anchor is the close-brace of the previous
# engine method (returning plotData/Q/k/df/...) plus the
# computePublishedRatioCore opener.
# ============================================================================

ANCHOR_METHODS = (
    "                return { plotData, Q, k, df, I2, tau2, sWR, pLogOR, pSE, confLevel, zCrit, pOR, lci, uci, hksjLCI, hksjUCI, piLCI, piUCI, qPvalue, eggerResult, fragIdx, fragQuot, I2_lo, I2_hi };\n"
    "\n"
    "\n"
    "            },\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "            computePublishedRatioCore(trials) {"
)
REPLACEMENT_METHODS = (
    "                return { plotData, Q, k, df, I2, tau2, sWR, pLogOR, pSE, confLevel, zCrit, pOR, lci, uci, hksjLCI, hksjUCI, piLCI, piUCI, qPvalue, eggerResult, fragIdx, fragQuot, I2_lo, I2_hi };\n"
    "\n"
    "\n"
    "            },\n"
    "\n"
    "\n"
    "            // ===== v12.0: MANTEL-HAENSZEL FIXED-EFFECT ENGINE =====\n"
    "            // Cochrane Handbook v6.5 §10.4.1: MH preferred over inverse-variance for\n"
    "            // sparse binary outcomes. RBG (Robins-Breslow-Greenland 1986) variance.\n"
    "            // Ported from COLCHICINE_CVD older-style mhPoolOR/mhPoolRR pair.\n"
    "\n"
    "\n"
    "            mhPoolOR(plotData, confLevel) {\n"
    "                const k = plotData.length;\n"
    "                if (k < 2) return null;\n"
    "                const zCrit = normalQuantile(1 - (1 - confLevel) / 2);\n"
    "                let R = 0, S = 0, Pv = 0, Q_num = 0, RpS = 0;\n"
    "                plotData.forEach(d => {\n"
    "                    const a = d.tE, b = d.tN - d.tE, c = d.cE, dd = d.cN - d.cE;\n"
    "                    const N = d.tN + d.cN;\n"
    "                    if (N === 0) return;\n"
    "                    R += (a * dd) / N;\n"
    "                    S += (b * c) / N;\n"
    "                    const Ri = (a * dd) / N, Si = (b * c) / N;\n"
    "                    const Pi = (a + dd) / N, Qi = (b + c) / N;\n"
    "                    Pv += Pi * Ri / 2;\n"
    "                    Q_num += (Pi * Si + Qi * Ri) / 2;\n"
    "                    RpS += Qi * Si / 2;\n"
    "                });\n"
    "                if (S === 0 || R === 0) return null;\n"
    "                const mhOR = R / S;\n"
    "                const logMH = Math.log(mhOR);\n"
    "                const varLog = Pv / (R * R) + Q_num / (R * S) + RpS / (S * S);\n"
    "                const se = Math.sqrt(varLog);\n"
    "                return { pOR: mhOR, lci: Math.exp(logMH - zCrit * se), uci: Math.exp(logMH + zCrit * se), pLogOR: logMH, pSE: se, method: 'MH', k };\n"
    "            },\n"
    "\n"
    "\n"
    "            mhPoolRR(plotData, confLevel) {\n"
    "                const k = plotData.length;\n"
    "                if (k < 2) return null;\n"
    "                const zCrit = normalQuantile(1 - (1 - confLevel) / 2);\n"
    "                let num = 0, den = 0, P2 = 0;\n"
    "                plotData.forEach(d => {\n"
    "                    const a = d.tE, c = d.cE;\n"
    "                    const N = d.tN + d.cN;\n"
    "                    if (N === 0 || d.cN === 0 || d.tN === 0) return;\n"
    "                    num += (a * d.cN) / N;\n"
    "                    den += (c * d.tN) / N;\n"
    "                    P2 += ((d.tE + d.cE) * d.tN * d.cN / (N * N) - a * c / N);\n"
    "                });\n"
    "                if (den === 0 || num === 0) return null;\n"
    "                const mhRR = num / den;\n"
    "                const logMH = Math.log(mhRR);\n"
    "                const varLog = P2 / (num * den);\n"
    "                const se = Math.sqrt(Math.abs(varLog));\n"
    "                return { pOR: mhRR, lci: Math.exp(logMH - zCrit * se), uci: Math.exp(logMH + zCrit * se), pLogOR: logMH, pSE: se, method: 'MH-RR', k };\n"
    "            },\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "\n"
    "            computePublishedRatioCore(trials) {"
)

# ============================================================================
# Patch 2: methods.push for MH between Bayesian and Trim-Fill in the
# Method Sensitivity block.
# ============================================================================

ANCHOR_PUSH = (
    "                if (sub.bayesResult) methods.push({ name: 'Bayesian (CrI)', pOR: sub.bayesResult.postOR, lci: sub.bayesResult.criLo, uci: sub.bayesResult.criHi });\n"
    "\n"
    "\n"
    "                if (sub.tfResult && sub.tfResult.available && sub.tfResult.k0 > 0) {"
)
REPLACEMENT_PUSH = (
    "                if (sub.bayesResult) methods.push({ name: 'Bayesian (CrI)', pOR: sub.bayesResult.postOR, lci: sub.bayesResult.criLo, uci: sub.bayesResult.criHi });\n"
    "\n"
    "\n"
    "                // v12.0: Mantel-Haenszel sensitivity (Cochrane v6.5 §10.4.1).\n"
    "                if (c.plotData && c.plotData.length >= 2 && c.plotData[0].tE > 0 && c.plotData[0].cE > 0) {\n"
    "                    const em = RapidMeta.state.effectMeasure ?? 'OR';\n"
    "                    const isRR = em === 'RR';\n"
    "                    const mhResult = isRR ? this.mhPoolRR(c.plotData, c.confLevel) : this.mhPoolOR(c.plotData, c.confLevel);\n"
    "                    if (mhResult) {\n"
    "                        methods.push({ name: 'Mantel-Haenszel', pOR: mhResult.pOR, lci: mhResult.lci, uci: mhResult.uci });\n"
    "                        RapidMeta.state._mhResult = mhResult;\n"
    "                    }\n"
    "                }\n"
    "\n"
    "\n"
    "                if (sub.tfResult && sub.tfResult.available && sub.tfResult.k0 > 0) {"
)

SENTINEL = "mhPoolOR(plotData, confLevel)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    print("Mode:", "DRY-RUN" if args.dry_run else "WRITE")

    text = TARGET.read_text(encoding="utf-8")
    if SENTINEL in text:
        print(f"  {TARGET.name}: already_patched")
        return 0

    if ANCHOR_METHODS not in text:
        print(f"  {TARGET.name}: ANCHOR_METHODS not found -- abort")
        return 1
    if ANCHOR_PUSH not in text:
        print(f"  {TARGET.name}: ANCHOR_PUSH not found -- abort")
        return 1

    new_text = text.replace(ANCHOR_METHODS, REPLACEMENT_METHODS, 1)
    new_text = new_text.replace(ANCHOR_PUSH, REPLACEMENT_PUSH, 1)

    if not args.dry_run:
        TARGET.write_text(new_text, encoding="utf-8", newline="")
    print(f"  {TARGET.name}: patched (methods + push)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
