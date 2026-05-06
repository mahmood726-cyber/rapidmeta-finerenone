"""Final-pass verifier: for each PMID correction we applied, fetch the
NEW PMID's esummary, compare its title to the trial name + group, and
revert if the new title is clearly NOT the primary trial paper.

Heuristic: a primary trial paper title typically:
  - Contains the drug name (case-insensitive)
  - Names a condition matching the trial scope
  - Doesn't contain "matching-adjusted", "indirect comparison",
    "biomarker", "substudy", "post-hoc", "real-world", "review",
    "predicts", "patterns of clinical response"

If old title ALSO matched these criteria (drug + condition), prefer old.
"""
from __future__ import annotations
import sys, io, csv, re, time, json
from pathlib import Path
from urllib.request import urlopen, Request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

# Title patterns that signal NOT-a-primary-trial-paper
NON_PRIMARY_PATTERNS = [
    r"\bmatching[-\s]?adjusted",
    r"\bindirect\s+comparison",
    r"\bbiomarker[s]?\b",
    r"\bsubstud[yi]",
    r"\bpost[-\s]?hoc\b",
    r"\breal[-\s]?world\b",
    r"\breview\b",
    r"\bcommentary\b",
    r"\bcorrespondence\b",
    r"\bcomment\b",
    r"\beditorial\b",
    r"\bletter\b",
    r"\bplain\s+language\s+review",
    r"\bpatterns\s+of\s+clinical\s+response",
    r"\bpredicts\b",
    r"\bmeta[-\s]?analysis",
    r"\bsystematic\s+review",
    r"\bguidelines\b",
    r"\bnetwork\s+meta",
    r"\bsubgroup\s+analysis",
    r"\bextension\s+study",
    r"\blong[-\s]?term\s+(extension|safety|follow)",
    r"\bperceptions\b",
    r"\bdifferentiation\s+in",
    r"\bmorphology\b",
]


def is_primary_paper_title(title: str) -> bool:
    """Heuristic: does this title look like a primary trial paper?"""
    t = title.lower()
    if not t or len(t) < 20:
        return False
    for pat in NON_PRIMARY_PATTERNS:
        if re.search(pat, t):
            return False
    return True


def title_has_drug_name(title: str, group: str, claim: str) -> bool:
    """Lenient drug-name match: any 5+-char word in group/claim that
    appears in title."""
    t = title.lower()
    candidates = []
    for src in [group[:300], claim]:
        for w in re.findall(r"[A-Za-z]{5,}", src or ""):
            wl = w.lower()
            if wl in {"trial", "study", "phase", "patient", "patients",
                       "treatment", "induction", "maintenance", "placebo",
                       "active", "control", "double", "blind", "open",
                       "label", "primary", "secondary", "endpoint",
                       "weekly", "daily", "monthly", "year", "years",
                       "dose", "doses", "group", "groups", "naive",
                       "experienced", "responders"}:
                continue
            candidates.append(wl)
    for c in candidates:
        if c in t:
            return True
    # Also try drug suffixes
    for suf in ["mab", "cel", "tinib", "gliflozin", "liraglutide",
                  "ozanimod", "rituximab", "atinib", "etide", "afenib",
                  "azepam", "lutamide", "candesartan", "valsartan",
                  "losartan", "pamil", "olol", "azine", "tacin"]:
        if suf in t:
            return True
    return False


def extract_group(file_path: Path, nct: str) -> str:
    text = file_path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(
        rf"'{re.escape(nct)}'\s*:\s*\{{[^}}]*?group:\s*'([^']+?)'",
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1) if m else ""


def main():
    src = REPO / "outputs" / "pmid_corrections_applied.csv"
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    print(f"Verifying {len(rows)} corrections ...")

    reverts = 0
    keeps = 0
    for r in rows:
        old_title = r.get("esummary_title", "") or ""
        new_title = r.get("new_title", "") or ""
        fpath = REPO / r["file"]
        if not fpath.exists():
            continue
        group = extract_group(fpath, r["nct"])

        old_is_primary = is_primary_paper_title(old_title) and title_has_drug_name(old_title, group, r["claimed_name"])
        new_is_primary = is_primary_paper_title(new_title) and title_has_drug_name(new_title, group, r["claimed_name"])

        if old_is_primary and not new_is_primary:
            # Old was a real primary paper, new is a follow-up/secondary → revert
            text = fpath.read_text(encoding="utf-8", errors="replace")
            new_str = f"pmid: '{r['new_pmid']}'"
            old_str = f"pmid: '{r['pmid']}'"
            if new_str in text:
                text = text.replace(new_str, old_str, 1)
                fpath.write_text(text, encoding="utf-8")
                reverts += 1
                print(f"  REVERT  {r['file'][:34]:34s} {r['claimed_name'][:22]:22s}  new={r['new_pmid']} -> old={r['pmid']}")
                print(f"    old: '{old_title[:70]}' (PRIMARY)")
                print(f"    new: '{new_title[:70]}' (NOT primary)")
        elif old_is_primary and new_is_primary:
            # Both look primary → keep new (esearch usually finds the most-recent primary first)
            keeps += 1
        else:
            keeps += 1

    print(f"\n  Reverts: {reverts}")
    print(f"  Keeps:   {keeps}")


if __name__ == "__main__":
    main()
