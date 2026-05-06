"""Revert PMID 'corrections' that replaced an actually-correct PMID with
a newer/sub-analysis paper.

Reason: the v3 classifier flagged some entries as WRONG_PMID when the old
PMID was actually correct (e.g., title contained the drug name but the
classifier missed it). The smart corrector then accepted the esearch
suggestion which often was a follow-up paper.

Detection: for each correction in pmid_corrections_applied.csv, check
whether the OLD esummary_title contains the drug name from the trial's
group field. If yes, the old PMID was correct and we should revert.
"""
from __future__ import annotations
import sys, io, csv, re, time, json
from pathlib import Path
from urllib.request import urlopen, Request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent


def extract_group(file_path: Path, nct: str) -> str:
    text = file_path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(
        rf"'{re.escape(nct)}'\s*:\s*\{{[^}}]*?group:\s*'([^']+?)'",
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1) if m else ""


def drug_keywords(group: str, claim: str) -> list[str]:
    head = (group or "")[:300]
    words = re.findall(r"[A-Za-z]{5,}\d?", head)
    cn_words = re.findall(r"[A-Za-z]{5,}", claim)
    seen = set()
    out = []
    skip = {"trial", "study", "phase", "patient", "patients", "treatment",
            "induction", "maintenance", "placebo", "active", "control",
            "double", "blind", "open", "label", "primary", "secondary",
            "endpoint", "weekly", "daily", "monthly", "year", "years"}
    for w in words + cn_words:
        wl = w.lower()
        if wl in skip:
            continue
        if wl not in seen:
            seen.add(wl)
            out.append(wl)
    return out


def main():
    src = REPO / "outputs" / "pmid_corrections_applied.csv"
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    print(f"Reviewing {len(rows)} corrections ...")

    revert_keep = []  # corrections to KEEP (old was wrong, new is right)
    revert_undo = []  # corrections to REVERT (old was correct, new replaced it wrongly)

    for r in rows:
        old_title = (r.get("esummary_title") or "").lower()
        if not old_title:
            # Can't tell; keep the correction
            revert_keep.append(r)
            continue
        fpath = REPO / r["file"]
        if not fpath.exists():
            revert_keep.append(r)
            continue
        group = extract_group(fpath, r["nct"])
        kws = drug_keywords(group, r["claimed_name"])
        # If old title contains a 7+-char drug keyword, old was correct → revert
        old_was_correct = any(len(k) >= 7 and k in old_title for k in kws)
        if old_was_correct:
            revert_undo.append(r)
        else:
            revert_keep.append(r)

    # Apply reverts
    print(f"\n  Keeping (old was wrong): {len(revert_keep)}")
    print(f"  Reverting (old was correct): {len(revert_undo)}")

    for r in revert_undo:
        fpath = REPO / r["file"]
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8", errors="replace")
        new_str = f"pmid: '{r['new_pmid']}'"
        old_str = f"pmid: '{r['pmid']}'"
        if new_str in text:
            text = text.replace(new_str, old_str, 1)
            fpath.write_text(text, encoding="utf-8")
            print(f"  REVERTED {r['file'][:35]:35s} {r['claimed_name'][:25]:25s} {r['new_pmid']} -> {r['pmid']}")

    print(f"\nSummary:")
    print(f"  Original corrections:    {len(rows)}")
    print(f"  Reverts (old correct):   {len(revert_undo)}")
    print(f"  Net corrections:          {len(rows) - len(revert_undo)}")

    out = REPO / "outputs" / "pmid_corrections_final.csv"
    if revert_keep:
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(revert_keep[0].keys()))
            w.writeheader()
            w.writerows(revert_keep)
        print(f"  Final corrections list:  {out}")


if __name__ == "__main__":
    main()
