"""v3 PMID classifier — pulls the trial's group field from each source HTML
and uses it as the strongest match signal. NEJM/Lancet titles use drug
names; group fields list drug names. Matching them is the right test.

Approach:
  1. Read each *_REVIEW.html once, build a {(file, NCT): {name, group}}
     index.
  2. For each row in outputs/pmid_audit.csv:
     a. acronym in title (5+ char from claimed_name)            -> OK_ACRONYM
     b. drug name from group field (capitalized 5+ char) in title -> OK_DRUG
     c. condition keyword from filename in title                 -> OK_TOPIC
     d. else                                                     -> WRONG_PMID
"""
from __future__ import annotations
import sys, io, csv, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
IN_CSV = REPO / "outputs" / "pmid_audit.csv"
OUT_CSV = REPO / "outputs" / "pmid_audit_v3.csv"

# Capture trial blocks with name + group
TRIAL_RE = re.compile(
    r"'(NCT\d+(?:[A-Z]|_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"group:\s*'([^']+?)'",
    re.DOTALL,
)


def normalize(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def build_group_index():
    idx = {}
    for hp in sorted(REPO.glob("*_REVIEW.html")):
        text = hp.read_text(encoding="utf-8", errors="replace")
        for m in TRIAL_RE.finditer(text):
            nct = m.group(1)
            group = m.group(3)
            idx[(hp.name, nct)] = group
    return idx


# Stop words for keyword extraction
STOP = {
    "trial", "study", "phase", "the", "of", "in", "and", "vs", "for", "a", "an",
    "with", "without", "high", "low", "moderate", "severe", "patients", "subjects",
    "trial", "rct", "n", "as", "at", "by", "or", "to", "is", "on", "post", "pre",
    "primary", "secondary", "endpoint", "outcome", "outcomes", "active", "control",
    "placebo", "vs", "versus", "lower", "higher", "early", "late", "any", "all",
    "than", "from", "more", "less", "this", "that", "first", "second", "third",
    "open", "label", "double", "blind", "treatment", "compared", "year", "weekly",
    "daily", "monthly", "annually", "evaluating", "evaluation", "comparing",
    "treated", "extension", "follow", "report", "analysis", "based", "induction",
    "maintenance", "post-hoc", "ITT", "PP",
}


def classify(row, group_idx):
    title = row.get("esummary_title", "")
    if not title:
        return "NOT_FOUND"
    nt = normalize(title)
    cn = row.get("claimed_name", "")
    fname = row["file"]

    # (a) Trial acronym in title
    acros = re.findall(r"[A-Z][A-Z0-9\-]{2,}", cn)
    for a in acros:
        if normalize(a) in nt:
            return "OK_ACRONYM"

    # (b) Drug name from group field — case-insensitive, any 5+-char word
    group = group_idx.get((fname, row["nct"]), "")
    if group:
        head = group[:300]  # first 300 chars usually has drug+condition
        # All 5+-char words (case-insensitive)
        words = re.findall(r"[A-Za-z]{5,}\d?", head)
        # Try most-specific words first (longer = more diagnostic)
        candidates = sorted(set(words), key=lambda w: -len(w))
        for w in candidates:
            wl = w.lower()
            if wl in STOP:
                continue
            # Skip generic descriptors
            if wl in {"daily", "weekly", "monthly", "phase", "trial", "study",
                       "vs", "placebo", "control", "active", "primary",
                       "secondary", "endpoint", "patient", "patients", "with",
                       "without", "treatment", "year", "years", "open",
                       "label", "double", "blind"}:
                continue
            if wl in nt:
                return "OK_DRUG"

    # (c) Topic keywords from file name (split by underscore)
    fname_root = fname.replace("_REVIEW.html", "").replace("_NMA", "")
    fname_parts = [p for p in re.split(r"[_\-]+", fname_root) if len(p) > 2 and p.lower() not in STOP]
    matched = sum(1 for p in fname_parts if normalize(p) in nt)
    if matched >= 1 and any(len(p) >= 5 for p in fname_parts if normalize(p) in nt):
        return "OK_TOPIC"
    if matched >= 2:
        return "OK_TOPIC"

    return "WRONG_PMID"


def main():
    print("Building group-field index from source HTMLs ...")
    group_idx = build_group_index()
    print(f"  {len(group_idx)} (file, NCT) entries indexed")

    rows = list(csv.DictReader(open(IN_CSV, encoding="utf-8")))
    print(f"\nReclassifying {len(rows)} rows ...")

    counts = {}
    for r in rows:
        new_status = classify(r, group_idx)
        counts[new_status] = counts.get(new_status, 0) + 1
        r["status_v3"] = new_status

    # Write v3
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\n=== v3 status distribution ===")
    total = sum(counts.values())
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k:18s} {v:4d}  ({100*v/total:.1f}%)")

    n_wrong = counts.get("WRONG_PMID", 0)
    print(f"\n  Total OK (any path): {total - n_wrong} ({100*(total-n_wrong)/total:.1f}%)")
    print(f"  Truly WRONG_PMID:    {n_wrong} ({100*n_wrong/total:.1f}%)")

    print(f"\n=== Sample remaining WRONG_PMID ===")
    shown = 0
    for r in rows:
        if r["status_v3"] == "WRONG_PMID" and shown < 30:
            g = group_idx.get((r["file"], r["nct"]), "")[:60]
            print(f"  {r['file'][:32]:32s} pmid={r['pmid']} claim={r['claimed_name'][:30]:30s}")
            print(f"    title: {r['esummary_title'][:70]}")
            print(f"    group: {g}")
            if r['suggested_pmid']:
                print(f"    sugg : {r['suggested_pmid']} ({r['suggested_title'][:50]})")
            shown += 1


if __name__ == "__main__":
    main()
