"""Audit RoB-2 (Risk of Bias 2.0) completeness across the corpus.

RoB-2 has 5 domains: D1 Randomization, D2 Deviations from intended
intervention, D3 Missing outcome data, D4 Measurement of the outcome,
D5 Selection of the reported result.

Each trial in realData has a `rob:` field — array of 5 strings,
typically ['low','low','low','low','low'] when populated as a stub.
This audit:
  1. Counts trial-rows with a rob array present
  2. Counts those that look like stubs (all-low or all-some)
  3. Identifies trials with NO rob array at all
  4. Flags reviews where >50% of trials have stub-quality RoB

Output: outputs/rob2_completeness.csv with one row per trial.
"""
from __future__ import annotations
import sys, io, csv, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

TRIAL_RE = re.compile(
    r"'(NCT\d+(?:[A-Z]|_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?",
    re.DOTALL,
)

ROB_RE = re.compile(
    r"'(NCT\d+(?:[A-Z]|_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"rob:\s*\[([^\]]+)\]",
    re.DOTALL,
)


def classify(rob_str):
    """Given the captured rob array contents, classify completeness."""
    if not rob_str:
        return "NO_ROB"
    items = re.findall(r"'([^']+)'", rob_str)
    if len(items) != 5:
        return f"INCOMPLETE_{len(items)}"
    if all(i == 'low' for i in items):
        return "ALL_LOW_STUB"
    if all(i == items[0] for i in items):
        return f"UNIFORM_{items[0].upper()}"
    return "VARIED"


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    rows = []
    print(f"Scanning {len(files)} review HTMLs for RoB completeness ...")
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        # Map NCT → name
        names = {}
        for m in TRIAL_RE.finditer(text):
            names[m.group(1)] = m.group(2)
        # Map NCT → rob array
        for m in ROB_RE.finditer(text):
            nct = m.group(1)
            rob = m.group(2)
            cls = classify(rob)
            rows.append({
                "file": hp.name,
                "nct": nct,
                "name": names.get(nct, ""),
                "rob_class": cls,
                "rob_raw": rob.strip()[:200],
            })
        # Also flag trials with NO rob field
        rob_ncts = set(m.group(1) for m in ROB_RE.finditer(text))
        for nct, name in names.items():
            if nct not in rob_ncts:
                rows.append({
                    "file": hp.name,
                    "nct": nct,
                    "name": name,
                    "rob_class": "NO_ROB",
                    "rob_raw": "",
                })

    out = REPO / "outputs" / "rob2_completeness.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    counts = {}
    for r in rows:
        counts[r["rob_class"]] = counts.get(r["rob_class"], 0) + 1
    print(f"\n=== RoB completeness across {len(rows)} trial-rows ===")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * v / len(rows)
        print(f"  {k:20s} {v:5d}  ({pct:.1f}%)")

    # Per-file score: % of trials with VARIED RoB
    by_file = {}
    for r in rows:
        by_file.setdefault(r["file"], []).append(r["rob_class"])
    well_documented = 0
    stub_only = 0
    for f, cs in by_file.items():
        varied = sum(1 for c in cs if c == "VARIED")
        if varied / len(cs) >= 0.5:
            well_documented += 1
        elif all(c in ("ALL_LOW_STUB", "NO_ROB", "UNIFORM_LOW") for c in cs):
            stub_only += 1
    print(f"\n  Well-documented files (≥50% VARIED): {well_documented}")
    print(f"  Stub-only files: {stub_only}")
    print(f"\n  Output: {out}")


if __name__ == "__main__":
    main()
