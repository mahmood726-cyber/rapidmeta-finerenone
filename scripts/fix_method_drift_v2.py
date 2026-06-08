"""Second-pass stat-method drift sweep.

Rewrites the remaining DerSimonian-Laird PRIMARY-pooling claims to REML (the
engine's actual default: _remlHksjPool / estimator='REML') and aligns the two
new ICU/anaesthesia metas' prediction-interval df to the corpus k-1 (Cochrane
v6.5) convention. Spares legitimate DL usages: comparison-plot traces/captions,
R sensitivity code (res_dl), method-registry/dropdown labels, and explicit
"(sensitivity)" mentions.

Every modified file is re-checked with jscheck; a file that fails is reverted.
Run with --dry-run to preview counts without writing.
"""
import glob, subprocess, sys, io, os, argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MINUS = "−"  # U+2212 unicode minus used in the PI text

# (old, new, label) — exact substring swaps, all inside JS string literals / display text
PAIRS = [
    ("DerSimonian-Laird random-effects model with Hartung-Knapp-Sidik-Jonkman adjustment to pool",
     "REML random-effects model with Hartung-Knapp-Sidik-Jonkman adjustment to pool",
     "A:primary-pool-template"),
    ("DerSimonian-Laird random-effects + HKSJ + Cochrane v6.5 prediction interval",
     "REML random-effects + HKSJ + Cochrane v6.5 prediction interval",
     "B:primary-pool-PI"),
    ("DerSimonian-Laird τ² with Hartung-Knapp-Sidik-Jonkman",
     "REML τ² with Hartung-Knapp-Sidik-Jonkman",
     "C:primary-tau2-HKSJ"),
    (f"intervals computed with k{MINUS}2 degrees of freedom per Higgins et al",
     f"intervals computed with k{MINUS}1 degrees of freedom per Cochrane Handbook v6.5",
     "D:PI-df-k1"),
    ("DerSimonian-Laird+REML+HKSJ pooling",
     "REML+HKSJ primary with DerSimonian-Laird sensitivity pooling",
     "E:boilerplate-reorder"),
    ("نموذج DerSimonian-Laird للتأثيرات العشوائية",
     "نموذج REML للتأثيرات العشوائية",
     "F:arabic-primary-align"),
]


def jscheck(fn):
    r = subprocess.run([sys.executable, "scripts/jscheck.py", fn],
                       capture_output=True, text=True)
    return "[JS-OK]" in (r.stdout + r.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from collections import Counter
    applied = Counter()
    files_changed = reverted = 0

    for fn in sorted(glob.glob("*REVIEW*.html")):
        s = open(fn, encoding="utf-8").read()
        orig = s
        local = Counter()
        for old, new, label in PAIRS:
            c = s.count(old)
            if c:
                s = s.replace(old, new)
                local[label] += c
        if s == orig:
            continue
        if args.dry_run:
            for k, v in local.items():
                applied[k] += v
            files_changed += 1
            continue
        open(fn, "w", encoding="utf-8").write(s)
        if not jscheck(fn):
            open(fn, "w", encoding="utf-8").write(orig)  # revert
            reverted += 1
            print(f"  REVERTED (jscheck fail): {fn}")
            continue
        for k, v in local.items():
            applied[k] += v
        files_changed += 1

    print(f"\n{'DRY-RUN ' if args.dry_run else ''}files changed: {files_changed}, reverted: {reverted}")
    print("replacements by pattern:")
    for k, v in sorted(applied.items()):
        print(f"  {k:28} {v}")


if __name__ == "__main__":
    main()
