"""Hunt for DIAMOND-style outcome_content_change events in the 269 pool.

Strategy: strip both stopwords AND framework-language tokens (time, occurrence,
number, subjects, included, first, cumulative, incidence, etc.) before
computing Jaccard between v1 measure and current measure. What remains is
content tokens (death, hospitalization, MACE, troponin, biomarker, etc.).

Trials with content-Jaccard < 0.30 AND title-Jaccard < 0.50 are flagged
as candidates for outcome-content change. Manual eyeball confirmation
required for each candidate (DIAMOND-validation precedent).
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT_DIR = Path(__file__).parent
V1 = OUT_DIR / "hf_history_v1_198.json"
CURRENT = OUT_DIR / "hf_outcomes_269_current.json"
DIFF = OUT_DIR / "hf_v1_vs_current_269.json"
RESULT = OUT_DIR / "hf_content_change_candidates.json"

STOPWORDS = set("of the and or to in on at by for with a an from as is".split())

# Framework / statistical / time-keyword tokens — strip these to leave content
FRAMEWORK_TOKENS = set("""
time occurrence number subjects participants included first cumulative incidence
rate count change baseline week month year day from until between within during
mean median total all-cause primary secondary outcome endpoint composite measure
hierarchical assessed measured determined evaluated proportion percentage
duration follow-up follow up baseline-to randomization randomisation up
analysis cutoff date through approximately approximatley study completion
group treatment arm placebo
""".split())

# Stable content tokens we expect across the HF P3/P4 universe
HF_CONTENT_TOKENS = set("""
cv cardiovascular death deaths mortality myocardial infarction mi stroke
hospitalization hospitalisation hospitalizations hospitalisations urgent visit
heart failure hf hhf systolic diastolic ejection fraction lvef hfref hfpef
nyha ad hoc nt-probnp probnp troponin biomarker
exercise capacity 6mwd six-minute walking distance kccq kansas
quality life qol qol kccq-css kccq-os kccq-tss
serum potassium k+ sodium hemoglobin hb iron ferritin
mace adverse event cardiac
""".split())


def tokens_raw(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9\s]", " ", (s or "").lower())
    return {t for t in s.split() if t and t not in STOPWORDS and len(t) > 2}


def tokens_content(s: str) -> set[str]:
    """Tokens with stopwords AND framework tokens removed."""
    return tokens_raw(s) - FRAMEWORK_TOKENS


def jaccard(A: set[str], B: set[str]) -> float:
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def main() -> int:
    v1 = json.load(open(V1, "r", encoding="utf-8"))
    cur = json.load(open(CURRENT, "r", encoding="utf-8"))
    v1_by = {t["nct_id"]: t for t in v1["trials"]}

    rows = []
    for c in cur["trials"]:
        nct = c["nct_id"]
        v1_row = v1_by.get(nct)
        if not v1_row or "error" in c or not v1_row.get("ok"):
            continue
        v1_block = v1_row.get("primary_outcome_block") or ""
        v1_lines = [l.strip() for l in v1_block.splitlines() if l.strip()]
        v1_measure = v1_lines[1] if len(v1_lines) > 1 else None
        cur_primaries = c.get("registered_primary", []) or []
        cur_measure = cur_primaries[0]["measure"] if cur_primaries else None
        if not v1_measure or not cur_measure:
            continue

        title_jac = jaccard(tokens_raw(v1_measure), tokens_raw(cur_measure))
        content_jac = jaccard(tokens_content(v1_measure), tokens_content(cur_measure))

        # If both score low, it's a content-change candidate
        is_candidate = content_jac < 0.30 and title_jac < 0.50
        rows.append({
            "nct_id": nct,
            "acronym": c.get("acronym"),
            "lead_sponsor_class": c.get("lead_sponsor_class"),
            "lead_sponsor": c.get("lead_sponsor"),
            "phase": c.get("phase"),
            "overall_status": c.get("overall_status"),
            "v1_measure": v1_measure[:200],
            "current_measure": cur_measure[:200],
            "title_jaccard": round(title_jac, 3),
            "content_jaccard": round(content_jac, 3),
            "is_content_change_candidate": is_candidate,
        })

    candidates = [r for r in rows if r["is_content_change_candidate"]]
    candidates.sort(key=lambda r: r["content_jaccard"])

    summary = {
        "n_total": len(rows),
        "n_candidates": len(candidates),
        "candidate_rate_pct": round(len(candidates) / len(rows) * 100, 1) if rows else 0,
    }

    output = {"computed_at": "2026-04-30", "summary": summary, "candidates": candidates,
              "all_rows": rows}
    json.dump(output, open(RESULT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"=== Content-change candidate detector (n={len(rows)} trials) ===")
    print(f"  Candidates: {len(candidates)} ({summary['candidate_rate_pct']}%)")
    print()
    print(f"=== Top {min(20, len(candidates))} candidates (lowest content-Jaccard first) ===")
    for c in candidates[:20]:
        print(f"  {c['nct_id']} {(c.get('acronym') or '?')[:18]:<18} sponsor={c.get('lead_sponsor_class')[:8]:<8} content={c['content_jaccard']:>5.3f} title={c['title_jaccard']:>5.3f}")
        print(f"    v1: {c['v1_measure'][:140]}")
        print(f"    cu: {c['current_measure'][:140]}")
        print()

    print(f"Wrote {RESULT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
