"""Task D — registered-vs-published primary outcome comparison.

For each trial in hf_publications_22.json, extract candidate "primary outcome"
sentences from the abstract via keyword regex, compute Jaccard token-overlap
against the current registered primary measure, and flag any trial where
the overlap is below 0.50 (likely registered-vs-published drift).

This is COMPare-style methodology (Goldacre 2019). Manual eyeball review of
flagged trials is the recommended follow-up.
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
PUB_IN = OUT_DIR / "hf_publications_22.json"
DIFF_OUT = OUT_DIR / "hf_pub_vs_registered_diff.json"

STOPWORDS = set("of the and or to in on at by for with a an from as is".split())

PRIMARY_KEYWORDS = re.compile(
    r"(?i)"
    r"primary[ -]?(?:end[ -]?point|outcome|composite)"
    r"|(?:end[ -]?point|outcome) (?:was|comprised|consisted|of interest|of the|of all-cause|of cardiovascular)"
)


def tokens(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9\s]", " ", (s or "").lower())
    return {t for t in s.split() if t and t not in STOPWORDS and len(t) > 2}


def jaccard(a: str, b: str) -> float:
    A, B = tokens(a), tokens(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def extract_published_primary_sentences(abstract: str) -> list[str]:
    """Return sentences from the abstract that mention 'primary' something.

    These are the candidate published-primary-outcome strings.
    """
    if not abstract:
        return []
    # Split into sentences (rough, abstract-style)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", abstract)
    return [s.strip() for s in sentences if PRIMARY_KEYWORDS.search(s) and len(s) < 600]


def main() -> int:
    pub = json.load(open(PUB_IN, "r", encoding="utf-8"))

    rows = []
    for t in pub["trials"]:
        nct = t["nct_id"]
        if "error" in t:
            rows.append({"nct_id": nct, "error": t["error"]})
            continue

        cur_primaries = t.get("current_registered_primary") or []
        cur_measure = cur_primaries[0]["measure"] if cur_primaries else None

        if not t.get("primary_abstract"):
            rows.append({"nct_id": nct, "acronym": t.get("acronym"), "error": "no abstract"})
            continue

        candidate_sentences = extract_published_primary_sentences(t["primary_abstract"])
        # Best Jaccard match between cur_measure and any candidate sentence
        best_score, best_sentence = 0.0, None
        for s in candidate_sentences:
            sc = jaccard(cur_measure or "", s)
            if sc > best_score:
                best_score, best_sentence = sc, s

        flag = "registered_vs_published_drift" if best_score < 0.30 else (
            "minor_wording_difference" if best_score < 0.55 else "aligned"
        )

        rows.append({
            "nct_id": nct,
            "acronym": t.get("acronym"),
            "primary_pmid": t.get("primary_pmid"),
            "primary_journal": t.get("primary_journal"),
            "current_registered_measure": cur_measure,
            "n_candidate_pub_sentences": len(candidate_sentences),
            "best_match_sentence": best_sentence,
            "best_match_jaccard": round(best_score, 3),
            "flag": flag,
        })

    summary = {
        "n": len(rows),
        "aligned": sum(1 for r in rows if r.get("flag") == "aligned"),
        "minor_wording_difference": sum(1 for r in rows if r.get("flag") == "minor_wording_difference"),
        "registered_vs_published_drift": sum(1 for r in rows if r.get("flag") == "registered_vs_published_drift"),
        "no_abstract_or_error": sum(1 for r in rows if "error" in r),
    }

    output = {"computed_at": "2026-04-30", "summary": summary, "trials": rows}
    json.dump(output, open(DIFF_OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print("=== n=22 registered-vs-published primary outcome diff ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print()
    print(f"  {'NCT':<12} {'acronym':<22} {'jaccard':>8}  flag")
    for r in rows:
        if "error" in r:
            print(f"  {r['nct_id']:<12} {r.get('acronym') or '?':<22} {'?':>8}  ERROR: {r['error']}")
            continue
        print(f"  {r['nct_id']:<12} {(r.get('acronym') or '?'):<22} {r['best_match_jaccard']:>8.3f}  {r['flag']}")
    print()
    print(f"Wrote {DIFF_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
