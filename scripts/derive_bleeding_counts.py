"""Recover per-arm bleeding counts for AMPLIFY and AMPLIFY-EXT from the rates
posted on ClinicalTrials.gov, and PROVE each recovery is unambiguous.

ClinicalTrials.gov posts these safety outcomes as a proportion (paramType
NUMBER) together with the treated-population denominator, not as a participant
count. A proportion plus a denominator determines a count only if exactly one
integer rounds to the reported value at the reported precision. This script
searches every integer in [0, N] and accepts the recovery ONLY when the solution
is unique; anything ambiguous is refused and must stay out of the ledger.

That distinction matters: back-computing a count from a rounded percentage is
normally forbidden here precisely because it invents precision. Recovering an
integer that is uniquely determined by a 4-decimal proportion over a
four-figure denominator is not the same operation, and the uniqueness proof is
what separates them. Where NEJM independently reports the same figure, the
cross-check is printed alongside.
"""
import io
import sys
from decimal import Decimal

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# (label, arm, reported proportion as a STRING so its precision is explicit, N)
ROWS = [
    # --- AMPLIFY NCT00643201, treated population ---
    ("AMPLIFY major bleeding", "apixaban", "0.0056", 2676),
    ("AMPLIFY major bleeding", "enox+warf", "0.0182", 2689),
    ("AMPLIFY major or CRNM bleeding", "apixaban", "0.0430", 2676),
    ("AMPLIFY major or CRNM bleeding", "enox+warf", "0.0971", 2689),
    ("AMPLIFY CRNM bleeding", "apixaban", "0.0385", 2676),
    ("AMPLIFY CRNM bleeding", "enox+warf", "0.0800", 2689),
    # --- AMPLIFY-EXT NCT00633893, treated population (840 / 811 / 826) ---
    ("AMPLIFY-EXT major bleeding", "apix 2.5", "0.0024", 840),
    ("AMPLIFY-EXT major bleeding", "apix 5", "0.0012", 811),
    ("AMPLIFY-EXT major bleeding", "placebo", "0.0048", 826),
    ("AMPLIFY-EXT major or CRNM bleeding", "apix 2.5", "0.0321", 840),
    ("AMPLIFY-EXT major or CRNM bleeding", "apix 5", "0.0432", 811),
    ("AMPLIFY-EXT major or CRNM bleeding", "placebo", "0.0266", 826),
    ("AMPLIFY-EXT CRNM bleeding", "apix 2.5", "0.0298", 840),
    ("AMPLIFY-EXT CRNM bleeding", "apix 5", "0.0419", 811),
    ("AMPLIFY-EXT CRNM bleeding", "placebo", "0.0230", 826),
]


def candidates(reported: str, n: int):
    """Every integer x in [0, n] whose x/n rounds to `reported` at its precision."""
    dp = len(reported.split(".")[1])
    target = Decimal(reported)
    out = []
    for x in range(n + 1):
        val = (Decimal(x) / Decimal(n)).quantize(Decimal(1).scaleb(-dp))
        if val == target:
            out.append(x)
    return out


ok, ambiguous = [], []
for label, arm, rep, n in ROWS:
    cands = candidates(rep, n)
    if len(cands) == 1:
        ok.append((label, arm, cands[0], n, rep))
        print(f"UNIQUE   {label:36s} {arm:10s} {cands[0]:>4d}/{n:<5d} "
              f"(reported {rep}, only integer that rounds there)")
    else:
        ambiguous.append((label, arm, cands, n, rep))
        print(f"AMBIGUOUS{label:36s} {arm:10s} candidates={cands} /{n} (reported {rep}) "
              f"-> REFUSED, will not be written")

print(f"\n{len(ok)} unique, {len(ambiguous)} ambiguous")

print("\nCross-checks against the NEJM abstracts (independent of the registry):")
for got, want, what in [
    (15 / 2676, 0.006, "AMPLIFY major bleeding apixaban ~0.6%"),
    (49 / 2689, 0.018, "AMPLIFY major bleeding conventional ~1.8%"),
    (115 / 2676, 0.043, "AMPLIFY major+CRNM apixaban 4.3%"),
    (261 / 2689, 0.097, "AMPLIFY major+CRNM conventional 9.7%"),
    (4 / 826, 0.005, "AMPLIFY-EXT major bleeding placebo 0.5%"),
    (2 / 840, 0.002, "AMPLIFY-EXT major bleeding 2.5 mg 0.2%"),
    (1 / 811, 0.001, "AMPLIFY-EXT major bleeding 5 mg 0.1%"),
    (19 / 826, 0.023, "AMPLIFY-EXT CRNM placebo 2.3%"),
    (25 / 840, 0.030, "AMPLIFY-EXT CRNM 2.5 mg 3.0%"),
    (34 / 811, 0.042, "AMPLIFY-EXT CRNM 5 mg 4.2%"),
]:
    flag = "OK " if abs(got - want) < 0.0006 else "!! "
    print(f"  {flag}{what:48s} recovered {got*100:.2f}% vs published {want*100:.1f}%")

sys.exit(1 if ambiguous else 0)
