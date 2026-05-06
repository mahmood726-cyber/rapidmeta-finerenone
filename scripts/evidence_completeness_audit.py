"""Evidence-completeness audit — scan every realData NCT block in every *_REVIEW.html
for presence of these critical evidence rows:

  1. Demographics — age, sex, race breakdown (the user-flagged gap on PEGCETACOPLAN)
  2. Eligibility — explicit inclusion/exclusion criteria (incl. "GA secondary to AMD" specificity)
  3. Safety / AE — denominator-consistent adverse-event counts (mITT vs safety-set)

For each trial, output presence-flag for each category, plus an overall "completeness score"
0-3. Trials with score < 2 are flagged as evidence-thin.

Output: outputs/evidence_completeness_audit.csv

Heuristic match (case-insensitive substring on the `label:` field):
  - Demographics: 'demographic' OR 'baseline' (within an evidence row, not the snippet)
  - Eligibility: 'eligibility' OR 'inclusion' OR 'exclusion criteria'
  - Safety: 'safety' OR 'adverse' OR 'AE' (label-level)
"""
from __future__ import annotations
import csv
import re
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
OUT_CSV = REPO_DIR / "outputs" / "evidence_completeness_audit.csv"


NCT_BLOCK_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'",
    re.DOTALL,
)


def find_trial_blocks(text: str) -> list[tuple[str, str, int, int]]:
    """Return [(key, name, block_start, block_end), ...] for each NCT block in realData."""
    out = []
    for m in NCT_BLOCK_RE.finditer(text):
        key = m.group(1)
        name = m.group(2)
        block_start = m.start()
        # Find end of this trial's object (next `},` at depth 0)
        depth = 0
        i = text.find("{", m.end())
        if i == -1:
            continue
        block_end = i
        while block_end < len(text):
            c = text[block_end]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            block_end += 1
        out.append((key, name, block_start, block_end))
    return out


def has_evidence_label(block: str, keywords: list[str]) -> bool:
    """Does the block have an `evidence` row whose `label:` contains any keyword (case-insensitive)?"""
    # Find evidence array
    em = re.search(r"evidence:\s*\[", block)
    if not em:
        return False
    # Find each label: 'XXX' inside the evidence array
    labels = re.findall(r"label:\s*'([^']+)'", block[em.end():])
    for label in labels:
        low = label.lower()
        for kw in keywords:
            if kw.lower() in low:
                return True
    return False


def main():
    review_files = sorted(REPO_DIR.glob("*_REVIEW.html"))
    print(f"Scanning {len(review_files)} review HTMLs for evidence-row completeness...\n")

    findings = []
    for hp in review_files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        blocks = find_trial_blocks(text)
        for key, name, bs, be in blocks:
            block = text[bs:be]
            has_demo = has_evidence_label(block, ["demographic", "baseline character"])
            has_elig = has_evidence_label(block, ["eligibility", "inclusion", "exclusion criteria"])
            has_safety = has_evidence_label(block, ["safety", "adverse", "tolerab", " ae ", "AE)", "AE,", "AE "])
            score = sum([has_demo, has_elig, has_safety])
            findings.append({
                "file": hp.name,
                "key": key,
                "name": name[:40],
                "demographics": "Y" if has_demo else "N",
                "eligibility": "Y" if has_elig else "N",
                "safety_ae": "Y" if has_safety else "N",
                "score_3": score,
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(findings[0].keys()))
        w.writeheader()
        w.writerows(findings)

    # Summary
    total = len(findings)
    by_score: dict[int, int] = {}
    for f in findings:
        by_score[f["score_3"]] = by_score.get(f["score_3"], 0) + 1

    print(f"=== Per-trial evidence-row completeness ({total} trial-rows in {len(review_files)} files) ===")
    for s in sorted(by_score.keys()):
        print(f"  Score {s}/3 (Demo+Elig+Safety): {by_score[s]} trial-rows ({100*by_score[s]/total:.1f}%)")

    # Per-category coverage
    n_demo = sum(1 for f in findings if f["demographics"] == "Y")
    n_elig = sum(1 for f in findings if f["eligibility"] == "Y")
    n_safety = sum(1 for f in findings if f["safety_ae"] == "Y")
    print(f"\n=== Per-category coverage ===")
    print(f"  Demographics row: {n_demo}/{total} ({100*n_demo/total:.1f}%)")
    print(f"  Eligibility row:  {n_elig}/{total} ({100*n_elig/total:.1f}%)")
    print(f"  Safety/AE row:    {n_safety}/{total} ({100*n_safety/total:.1f}%)")

    # File-level: how many files have every-trial-complete (score 3 for all rows)
    by_file: dict[str, list[int]] = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f["score_3"])
    files_complete = sum(1 for fn, scores in by_file.items() if min(scores) >= 3)
    files_thin = sum(1 for fn, scores in by_file.items() if min(scores) <= 1)
    print(f"\n=== File-level ===")
    print(f"  Fully evidence-complete (every trial >= 3/3): {files_complete}/{len(by_file)}")
    print(f"  Evidence-thin (any trial <= 1/3):              {files_thin}/{len(by_file)}")

    # Top 30 evidence-thin files (those with most low-score trials)
    file_thin_count: dict[str, int] = {}
    for fn, scores in by_file.items():
        thin = sum(1 for s in scores if s <= 1)
        if thin > 0:
            file_thin_count[fn] = thin
    print(f"\n=== Top evidence-thin files (most score<=1 trials) ===")
    for fn, n in sorted(file_thin_count.items(), key=lambda x: -x[1])[:30]:
        print(f"  {fn}: {n} thin-trial-rows")

    print(f"\nWritten: {OUT_CSV}")


if __name__ == "__main__":
    main()
