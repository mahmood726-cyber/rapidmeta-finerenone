"""Resolve cross-review NCT-identity collisions against AACT 2026-04-12.

For each NCT in outputs/extraction_audit/collision_working_set.json, pull from
local AACT snapshot:
  - studies.txt  → brief_title, official_title, overall_status, enrollment, phase
  - conditions.txt → conditions
  - interventions.txt → interventions (name + type)
  - brief_summaries.txt → summary text

Then for each conflicting review, compute a topic-overlap score (token Jaccard
between the review-stem normalized + the AACT-fetched title/conditions/interventions)
and emit a resolution row per (NCT, review) pair.

Output: outputs/extraction_audit/nct_collision_resolutions.json
"""
from __future__ import annotations
import csv, json, re, sys, os, io
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

AACT = Path("D:/AACT-storage/AACT/2026-04-12")
HERE = Path(__file__).resolve().parent.parent
WORK = HERE / "outputs" / "extraction_audit" / "collision_working_set.json"
OUT = HERE / "outputs" / "extraction_audit" / "nct_collision_resolutions.json"

with open(WORK, "r", encoding="utf-8") as f:
    working = json.load(f)

target_ncts = set(working.keys())
print(f"[1/5] Target NCTs: {len(target_ncts)} → {sorted(target_ncts)}")


def read_pipe_table(path: Path, key_col: str, want_cols: list[str], filter_set: set[str]):
    """Streaming pipe-delimited reader. AACT uses | as delimiter."""
    out: dict[str, list[dict]] = defaultdict(list)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            k = (row.get(key_col) or "").strip().upper()
            if k in filter_set:
                out[k].append({c: (row.get(c) or "").strip() for c in want_cols})
    return out


print("[2/5] Reading studies.txt…")
studies = read_pipe_table(AACT / "studies.txt", "nct_id",
                           ["brief_title", "official_title", "overall_status",
                            "enrollment", "phase", "study_type"], target_ncts)
print(f"     resolved {len(studies)}/{len(target_ncts)} NCTs in studies.txt")

print("[3/5] Reading conditions.txt…")
conds = read_pipe_table(AACT / "conditions.txt", "nct_id",
                         ["downcase_name"], target_ncts)

print("[4/5] Reading interventions.txt…")
intvs = read_pipe_table(AACT / "interventions.txt", "nct_id",
                         ["name", "intervention_type"], target_ncts)

print("[5/5] Reading brief_summaries.txt…")
sums = read_pipe_table(AACT / "brief_summaries.txt", "nct_id",
                        ["description"], target_ncts)

STOP = {"of", "the", "and", "for", "in", "a", "an", "to", "or", "with",
        "vs", "versus", "trial", "study", "review", "nma", "rct", "phase",
        "open", "label", "double", "blind", "blinded", "placebo", "controlled",
        "randomized", "randomised", "multicentre", "multicenter", "international",
        "multinational", "vs.", "v.", "new", "treatment", "patients", "subjects"}


def tokens(s: str) -> set[str]:
    s = (s or "").lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    return {t for t in s.split() if len(t) >= 3 and t not in STOP}


def score(review_stem: str, nct_info: dict) -> float:
    """Topic-overlap score: token Jaccard of review stem vs AACT title+conditions+intvs+summary."""
    rev_toks = tokens(review_stem.replace("_", " "))
    aact_text = " ".join([
        nct_info.get("brief_title", ""),
        nct_info.get("official_title", ""),
        " ".join(nct_info.get("conditions", [])),
        " ".join(nct_info.get("interventions", [])),
        nct_info.get("summary", ""),
    ])
    aact_toks = tokens(aact_text)
    if not rev_toks or not aact_toks:
        return 0.0
    inter = rev_toks & aact_toks
    union = rev_toks | aact_toks
    return len(inter) / max(1, len(union)), sorted(inter)


resolutions = {}
for nct, review_entries in working.items():
    st = studies.get(nct, [])
    if not st:
        resolutions[nct] = {
            "nct": nct, "aact_status": "NOT_FOUND_IN_AACT",
            "reviews": [r["review"] for r in review_entries],
            "decision": "MANUAL_REVIEW — NCT missing from AACT 2026-04-12 snapshot",
        }
        continue
    info = {
        "brief_title": st[0].get("brief_title", ""),
        "official_title": st[0].get("official_title", ""),
        "overall_status": st[0].get("overall_status", ""),
        "phase": st[0].get("phase", ""),
        "enrollment": st[0].get("enrollment", ""),
        "conditions": sorted({c["downcase_name"] for c in conds.get(nct, [])}),
        "interventions": sorted({i["name"] for i in intvs.get(nct, [])}),
        "intervention_types": sorted({i["intervention_type"] for i in intvs.get(nct, [])}),
        "summary": (sums.get(nct, [{}])[0].get("description", "") if sums.get(nct) else "")[:500],
    }
    per_review = []
    for entry in review_entries:
        rv = entry["review"]
        s, common = score(rv, info)
        per_review.append({
            "review": rv,
            "topic_overlap_score": round(s, 3),
            "shared_tokens": common,
        })
    per_review.sort(key=lambda r: -r["topic_overlap_score"])
    # Decision: highest-overlap review keeps; others flagged
    if per_review:
        best = per_review[0]
        keeper = best["review"]
        losers = [r["review"] for r in per_review[1:] if r["topic_overlap_score"] < best["topic_overlap_score"] - 0.05]
        ambiguous = [r["review"] for r in per_review[1:] if r["review"] not in losers]
        resolutions[nct] = {
            "nct": nct,
            "aact_status": "RESOLVED",
            "aact_info": info,
            "scoring": per_review,
            "decision_keeper": keeper,
            "decision_losers": losers,
            "decision_ambiguous": ambiguous,
        }
    print(f"  {nct}: best={per_review[0]['review']}@{per_review[0]['topic_overlap_score']:.3f} "
          f"vs {[(r['review'], r['topic_overlap_score']) for r in per_review[1:]]}")

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(resolutions, f, indent=2)
print(f"\nWrote {OUT}")
print(f"NCTs RESOLVED: {sum(1 for r in resolutions.values() if r['aact_status']=='RESOLVED')}/{len(resolutions)}")
