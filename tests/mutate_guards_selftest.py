#!/usr/bin/env python
"""
Mutation self-test for assets/js/rapidmeta-guards.js.

RM-J04: a gate that cannot fail is verification theatre. This script re-seeds each of the
original shipped defects into the guard module, runs the unit suite, and asserts that the
corresponding tests FAIL. It restores the file afterwards, on every path.

Usage:
    python tests/mutate_guards_selftest.py          # exit 0 only if every seed is caught

Each seed is the ACTUAL shipped code, cited to the artifact that recorded it.
"""
import io
import re
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
GUARDS = ROOT / "assets" / "js" / "rapidmeta-guards.js"
SUITE = "tests/test_rapidmeta_guards.mjs"

# (id, description, source-artifact, find, replace, expect_substring_in_failing_test_name)
SEEDS = [
    (
        "S1-saferob",
        'safeRob resolves an unknown rating to "low" (every Some-Concerns -> Low, corpus-wide)',
        "IRON §4(1) / BUG-CAT #2",
        'return v === undefined ? "some" : v;',
        'return v === undefined ? "low" : v;',
        "safeRob",
    ),
    (
        "S2-estimand-default-hr",
        "an untagged estimand defaults to HR instead of blocking (the RM-A02 denylist)",
        "ARNI c641f552f",
        'if (!isPresent(tag)) block("G00", "ESTIMAND_MISSING", "no estimandType on the record");',
        'if (!isPresent(tag)) return "HR";',
        "estimand",
    ),
    (
        "S3-continuous-into-ratio",
        "a non-ratio estimand is admitted to an HR/OR/RR model",
        "ARNI c641f552f / BUG-CAT guard 1",
        'if (spec.scale !== "ratio") {',
        'if (false) {',
        "ratio model",
    ),
    (
        "S4-false-green",
        "the badge may claim a pass over a non-STABLE verdict",
        "HARNESS F-05 / APIXABAN B1",
        'if (s.word !== "STABLE") block(G, "FALSE_GREEN_VERDICT",',
        'if (false) block(G, "FALSE_GREEN_VERDICT",',
        "green",
    ),
    (
        "S5-rate-as-proportion",
        "a person-time rate is treated as a proportion and multiplied by a denominator",
        "APIXABAN §2.1",
        "if (RATE_UNIT_RE.test(u)) {",
        "if (false) {",
        "unitOfMeasure",
    ),
    (
        "S6-silent-endpoint-fallback",
        "a missing scope silently falls back to the trial's first outcome row",
        "IRON §1 Defect 1 / BUG-CAT guard 3",
        "    if (hits.length === 0) {\n      return {\n        ok: false, blocked: true, row: null,",
        "    if (hits.length === 0) {\n      return {\n        ok: true, blocked: false, row: rows[0],",
        "fallback",
    ),
    (
        "S7-peto-hr",
        'the Peto estimator may be labelled "HR"',
        "BUG-CAT guard 2",
        'block(G, "ESTIMATOR_MEASURE_MISLABEL",',
        'return { measure: forced, forced: true, estimator: key }; if (false) block(G, "ESTIMATOR_MEASURE_MISLABEL",',
        "Peto",
    ),
    (
        "S8-missing-as-zero",
        "a missing count coerces to 0 instead of NA",
        "ARNI ea1a8fea1",
        "  function naOrNumber(x) {\n    if (!isPresent(x)) return NA;",
        "  function naOrNumber(x) {\n    if (!isPresent(x)) return 0;",
        "NA",
    ),
    (
        "S9-mechanism-deleted",
        "the tamper-evident public-push mechanism may be deleted (the over-correction)",
        "ARNI 554b6f2a2 -> ce187425e",
        "if (o.requireMechanism !== false && !MECHANISM_RE.test(t)) {",
        "if (false) {",
        "mechanism",
    ),
    (
        "S10-mixed-polarity-pool",
        "a good outcome and a bad outcome may be pooled on one scale",
        "RIFA §2.3 (P0)",
        "if (keys.length > 1) {\n      block(G, \"MIXED_POLARITY_POOL\",",
        "if (false) {\n      block(G, \"MIXED_POLARITY_POOL\",",
        "polarity",
    ),    (
        "S11-negative-hr",
        "a negative or out-of-range ratio is accepted into an HR/OR/RR field",
        "bempedoic LDL-C selector: 'Pooled Hazard Ratio = -19.50'",
        'if (n <= 0) block(G, "RATIO_FIELD_NON_POSITIVE",',
        'if (false) block(G, "RATIO_FIELD_NON_POSITIVE",',
        "ratio range",
    ),
    (
        "S12-integrity-gate-warns",
        "the fail-closed integrity gate warns instead of blocking",
        "bempedoic reviewer recommendation #9",
        'if (fails.length) {\n      block(G, "INTEGRITY_GATE_FAILED", fails.join("; "));\n    }',
        'if (false) {\n      block(G, "INTEGRITY_GATE_FAILED", fails.join("; "));\n    }',
        "integrity gate",
    ),
    (
        "S13-composite-mismatch",
        "MACE-3 may be pooled with MACE-4",
        "PCSK9 FOURIER (revasc) vs ODYSSEY (CHD death); bempedoic Wisdom vs CLEAR Outcomes",
        'block(G, "COMPONENT_SET_MISMATCH",',
        'return { ok: true }; block(G, "COMPONENT_SET_MISMATCH",',
        "composite",
    ),
    (
        "S14-watchlist-off-topic",
        "a wholly off-topic monitoring watchlist is accepted",
        "PCSK9 + bempedoic both tracking the finerenone programme",
        'block(G, "WATCHLIST_WRONG_TOPIC",',
        'return { ok: true }; block(G, "WATCHLIST_WRONG_TOPIC",',
        "watchlist",
    ),
    (
        "S15-persisted-resurrection",
        "a stale localStorage profile may carry its quarantined rows into the analysis",
        "commit 9d37dce08: a pre-fix profile still rendered RR 0.03 (0.00-0.52)",
        "if (quarantinedIds[id]) {\n        purged.push({ id: id, why: \"quarantined in the authoritative ledger\" });\n        return;\n      }",
        "if (false) {\n        purged.push({ id: id, why: \"quarantined in the authoritative ledger\" });\n        return;\n      }",
        "resurrect",
    ),
    (
        "S16-persisted-result-restored",
        "a persisted pooled estimate is carried forward on hydrate",
        "commit 9d37dce08 (returning-visitor safety)",
        "      pooledResult: null,",
        "      pooledResult: p.pooledResult,",
        "resurrect",
    ),
]


FAILING_RE = re.compile(r"^\s*\u2716\s+(.+?)\s*\(\d", re.M)


def run_suite():
    """Return (pass_count, fail_count, failing_test_names) from `node --test`."""
    p = subprocess.run(
        ["node", "--test", SUITE],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = (p.stdout or "") + (p.stderr or "")
    passed = failed = None
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("ℹ pass "):
            passed = int(s.split()[-1])
        elif s.startswith("ℹ fail "):
            failed = int(s.split()[-1])
    if passed is None or failed is None:
        raise RuntimeError("could not parse node --test output:\n" + out[-4000:])
    names = sorted({n.strip() for n in FAILING_RE.findall(out)})
    return passed, failed, names


def main():
    original = GUARDS.read_text(encoding="utf-8", newline="")
    print("=" * 78)
    print("MUTATION SELF-TEST — assets/js/rapidmeta-guards.js")
    print("=" * 78)

    base_pass, base_fail, _ = run_suite()
    print(f"\nBASELINE: {base_pass} pass / {base_fail} fail")
    if base_fail != 0:
        print("BASELINE IS NOT GREEN — fix the suite before mutation testing.")
        return 2

    results, uncaught, unapplied = [], [], []
    try:
        for sid, desc, src, find, repl, expect in SEEDS:
            if find not in original:
                unapplied.append((sid, desc))
                print(f"\n[{sid}] SEED DID NOT APPLY — pattern absent. Guard code has drifted.")
                continue
            GUARDS.write_text(original.replace(find, repl, 1), encoding="utf-8", newline="")
            p, f, names = run_suite()
            # `f > 0` alone is not proof: ANY failure would satisfy it. The seed is only CAUGHT
            # when the test written FOR that defect is among the failures.
            hit = [n for n in names if expect.lower() in n.lower()]
            caught = f > 0 and bool(hit)
            results.append((sid, desc, src, p, f, caught))
            print(f"\n[{sid}] re-seed: {desc}")
            print(f"        source: {src}")
            print(f"        result: {p} pass / {f} fail  ->  {'CAUGHT' if caught else 'NOT CAUGHT'}")
            print(f"        expect: a failing test matching {expect!r} -> "
                  + (f"{hit[0][:78]!r}" if hit else f"NOT FOUND (failures: {names[:3]})"))
            if not caught:
                uncaught.append((sid, desc + ("" if f else " [no test failed at all]")
                                 + ("" if hit else f" [wrong test failed: {names[:2]}]")))
    finally:
        GUARDS.write_text(original, encoding="utf-8", newline="")

    rp, rf, _ = run_suite()
    print(f"\nRESTORED: {rp} pass / {rf} fail")

    print("\n" + "=" * 78)
    caught_n = sum(1 for r in results if r[5])
    print(f"SEEDS APPLIED: {len(results)}/{len(SEEDS)}   CAUGHT: {caught_n}/{len(results)}")
    ok = (rf == 0) and not uncaught and not unapplied
    if unapplied:
        print("SEEDS THAT DID NOT APPLY (guard code drifted — the self-test is stale):")
        for sid, desc in unapplied:
            print(f"  - {sid}: {desc}")
    if uncaught:
        print("UNCAUGHT DEFECTS (the suite is theatre for these):")
        for sid, desc in uncaught:
            print(f"  - {sid}: {desc}")
    print("VERDICT:", "SELFTEST PASS" if ok else "SELFTEST FAIL")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
