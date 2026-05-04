"""PubMed cross-check v3 — more robust signal: PubMed title vs trial snippet text.

Hypothesis: A correct PMID's title will share at least 2 substantial tokens (4+ chars,
non-stopword, non-trial-marker) with the snippet's `group:` text, which contains
~200-500 chars describing drug, condition, comparator, sample size, etc.

A wrong PMID (potato browning, face transplantation, scapular morphology) will share
0 tokens with the snippet for any trial topic.

Decision rule:
  - Compute set of normalized tokens from PubMed title.
  - Compute set of normalized tokens from snippet text.
  - shared = |title_tokens ∩ snippet_tokens|
  - Verdict: WRONG_PMID iff shared <= 1 AND no shared first-author surname

Re-uses v1 fetched data via outputs/pubmed_cross_check.csv (no new PubMed calls).
"""
from __future__ import annotations
import csv
import re
from pathlib import Path

REPO_DIR = Path("C:/Projects/Finrenone")
PRIOR_CSV = REPO_DIR / "outputs" / "pubmed_cross_check.csv"
OUT_CSV = REPO_DIR / "outputs" / "pubmed_cross_check_v3.csv"

STOPWORDS = {
    "a", "an", "the", "of", "in", "for", "to", "and", "or", "with", "vs", "versus",
    "study", "trial", "phase", "randomized", "randomised", "double", "blind",
    "open", "label", "controlled", "placebo", "comparison", "evaluation",
    "efficacy", "safety", "treatment", "patients", "patient", "subjects",
    "evaluate", "compare", "assess", "single", "multicentre", "multicenter",
    "multi", "centre", "center", "international", "global", "trial.",
    "prospective", "retrospective", "non-inferiority", "noninferiority",
    "superiority", "design", "result", "results", "endpoint", "primary",
    "secondary", "outcome", "outcomes", "adult", "adults", "year", "years",
    "month", "months", "week", "weeks", "day", "days", "across", "between",
    "from", "after", "before", "during", "until", "than", "their", "them",
    "this", "that", "these", "those", "they", "have", "has", "had", "been",
    "were", "was", "will", "would", "could", "should", "may", "must", "can",
    "received", "receive", "treated", "given", "showed", "found", "demonstrate",
    "compared", "versus", "approximately", "estimated", "approximately",
    "intent", "treatment-emergent", "regimen", "regimens", "dose", "doses",
    "weeks", "weekly", "daily", "every", "data", "analysis", "analyses",
}

# Reuse v1 data — load PubMed title/year/journal/authors via the v1 CSV
def load_v1() -> list[dict]:
    return list(csv.DictReader(PRIOR_CSV.open(encoding="utf-8")))


def normalize_tokens(s: str) -> set[str]:
    if not s:
        return set()
    raw = re.split(r"[^a-z0-9]+", s.lower())
    return {t for t in raw if len(t) >= 4 and t not in STOPWORDS}


# Need to re-extract snippet text from review HTMLs (v1 didn't save it)
PMID_BLOCK_RE = re.compile(
    r"'(NCT\d+(?:_[A-Za-z0-9]+)?|LEGACY-[A-Za-z0-9-]+)'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)'[^}]*?"
    r"pmid:\s*'(\d+)'",
    re.DOTALL,
)


def load_snippets() -> dict[tuple[str, str], str]:
    """{(file, key): snippet_text}."""
    out = {}
    for hp in REPO_DIR.glob("*_REVIEW.html"):
        text = hp.read_text(encoding="utf-8", errors="replace")
        for m in PMID_BLOCK_RE.finditer(text):
            key = m.group(1)
            block_start = m.start()
            block_end = text.find("},", m.end())
            if block_end == -1:
                block_end = m.end() + 4000
            block = text[block_start:min(block_end, block_start + 4000)]
            gm = re.search(r"group:\s*'([^']+)'", block, re.DOTALL)
            sm = re.search(r"snippet:\s*'([^']+)'", block, re.DOTALL)
            txt = (gm.group(1) if gm else "") + " " + (sm.group(1) if sm else "")
            out[(hp.name, key)] = txt
    return out


def main():
    rows = load_v1()
    print(f"Loaded {len(rows)} v1 findings")
    snippets = load_snippets()
    print(f"Loaded snippets for {len(snippets)} (file, key) pairs")

    out_rows = []
    for r in rows:
        pmid = r["pmid"]
        snippet = snippets.get((r["file"], r["key"]), "")

        if not r["pubmed_title"]:
            v3_verdict = "PMID_NOT_FOUND"
            shared_count = 0
            shared_examples = ""
        else:
            title_tokens = normalize_tokens(r["pubmed_title"])
            snippet_tokens = normalize_tokens(snippet)
            shared = title_tokens & snippet_tokens
            shared_count = len(shared)
            shared_examples = ", ".join(sorted(shared)[:6])
            # Year-mismatch overlay
            year_diff_str = r.get("year_diff", "")
            year_bad = False
            try:
                year_bad = abs(int(year_diff_str)) > 1
            except (ValueError, TypeError):
                pass

            if shared_count == 0:
                # Author check as last-resort safeguard
                authors_in_snip = int(r.get("authors_in_snippet", "0") or "0")
                if authors_in_snip == 0:
                    v3_verdict = "WRONG_PMID"
                else:
                    v3_verdict = "OK_AUTHOR_MATCH"  # author surname appears in snippet
            elif shared_count == 1:
                v3_verdict = "WEAK_OVERLAP"  # might be real, might not
            else:
                v3_verdict = "OK"

            if year_bad and v3_verdict == "OK":
                v3_verdict = "YEAR_MISMATCH"

        out_rows.append({
            **r,
            "v3_verdict": v3_verdict,
            "title_snippet_overlap": shared_count,
            "shared_tokens": shared_examples,
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    by_v3: dict[str, int] = {}
    for r in out_rows:
        by_v3[r["v3_verdict"]] = by_v3.get(r["v3_verdict"], 0) + 1
    print(f"\n=== v3 verdict counts (n={len(out_rows)}) ===")
    for k in sorted(by_v3.keys()):
        print(f"  {k:30s} {by_v3[k]}")

    real = [r for r in out_rows if r["v3_verdict"] in ("WRONG_PMID", "PMID_NOT_FOUND", "YEAR_MISMATCH")]
    print(f"\n=== {len(real)} real defects ===\n")
    for r in real:
        print(f"  [{r['v3_verdict']:20s}] {r['file'][:55]:55s} {r['key']:18s} pmid={r['pmid']}")
        print(f"     claim: {r['claim_name'][:50]:50s} year={r['claim_year']}")
        print(f"     pubmed: {r['pubmed_title'][:80]}")
        print()


if __name__ == "__main__":
    main()
