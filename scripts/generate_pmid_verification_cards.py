"""
Phase (3) of the citation-consistency triage: verification cards.

For every PROBABLE / AMBIGUOUS / NO_PUBMED_HITS / INSUFFICIENT_SNIPPET
row in outputs/pmid_corrections.csv, generate a Markdown card that
the user (or a Makerere cohort member) can verify in seconds.

Each card shows:
  - Dashboard + trial name + current (wrong) PMID
  - The dashboard's snippet text (what the trial CLAIMS to be)
  - The PubMed reality of the current PMID (what the PMID ACTUALLY
    points to -- almost always an unrelated paper)
  - Top 3 candidate replacement PMIDs from the auto-propose run
  - A search link to PubMed pre-filled with the parsed snippet
  - A "no match -- needs manual search" affordance

Output: outputs/pmid_verification_cards.md (one file, all cards
grouped by dashboard).

Design intent: matches the RapidMeta verify-don't-extract pattern
from feedback_makerere_student_workload.md. Validator picks one of:
  - "use proposed PMID X"
  - "use a different PMID (paste here)"
  - "no PubMed match -- mark sourceUrl as the canonical CT.gov page"

The validator's choice is recorded in a sibling decisions CSV that
apply_pmid_corrections.py can later read and apply.

Usage:
  python scripts/generate_pmid_verification_cards.py
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(r"C:\Projects\Finrenone")
CORRECTIONS_CSV = ROOT / "outputs" / "pmid_corrections.csv"
OUT_MD = ROOT / "outputs" / "pmid_verification_cards.md"
OUT_DECISIONS = ROOT / "outputs" / "pmid_verification_decisions.csv"


def pubmed_search_url(parsed_surname: str, parsed_year, trial_name: str) -> str:
    parts = []
    if trial_name:
        parts.append(f'"{trial_name}"[Title/Abstract]')
    if parsed_surname:
        parts.append(f'{parsed_surname}[Author]')
    if parsed_year:
        parts.append(f'{parsed_year}[PDAT]')
    q = " AND ".join(parts) if parts else trial_name
    return f"https://pubmed.ncbi.nlm.nih.gov/?term={urllib.parse.quote(q)}"


def parse_candidates(s: str) -> list[dict]:
    """Parse 'pmid(score,author,year) | pmid2(score,author,year) | ...' into
    a list of {pmid, score, author, year}."""
    out = []
    if not s:
        return out
    for chunk in s.split("|"):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            pmid_part, rest = chunk.split("(", 1)
            score_part, rest2 = rest.split(",", 1)
            author_part, year_part = rest2.rsplit(",", 1)
            out.append({
                "pmid": pmid_part.strip(),
                "score": score_part.strip(),
                "author": author_part.strip(),
                "year": year_part.rstrip(")").strip(),
            })
        except ValueError:
            continue
    return out


def render_card(idx: int, row: dict) -> str:
    s = []
    s.append(f"### [{idx:03}] {row['dashboard']} — {row['trial_name']}")
    s.append("")
    s.append(f"- **Status:** `{row['status']}`")
    s.append(f"- **Current (wrong) PMID:** [{row['current_pmid']}](https://pubmed.ncbi.nlm.nih.gov/{row['current_pmid']}/)")
    s.append(f"- **What the dashboard claims (snippet):**")
    s.append(f"  > {row['snippet']}")
    s.append(f"- **What the current PMID actually points to:**")
    s.append(f"  parsed by audit: `{row.get('parsed_surname','?')} {row.get('parsed_year','?')}` — see PMID link above for the disagreement.")
    s.append("")
    cands = parse_candidates(row.get('candidates', ''))
    if cands:
        s.append("**Top auto-search candidates:**")
        s.append("")
        s.append("| Score | PMID | Author | Year | |")
        s.append("|---:|---|---|---|---|")
        for c in cands:
            s.append(f"| {c['score']} | [{c['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{c['pmid']}/) | {c['author']} | {c['year']} | [view](https://pubmed.ncbi.nlm.nih.gov/{c['pmid']}/) |")
        s.append("")
        if row['status'] == 'PROBABLE':
            s.append(f"_Auto-propose suggested top candidate **{cands[0]['pmid']}** but score margin is too small for unambiguous apply. Verify manually._")
        elif row['status'] == 'AMBIGUOUS':
            s.append(f"_Multiple candidates have similar scores; auto-propose declined to pick._")
    else:
        s.append("**No PubMed candidates found by the auto-search.** Likely the snippet is missing key metadata (no author/year).")
    s.append("")
    search_url = pubmed_search_url(row.get('parsed_surname',''), row.get('parsed_year',''), row['trial_name'])
    s.append(f"**[Search PubMed manually →]({search_url})**")
    s.append("")
    s.append(f"- **Decision:**")
    s.append(f"  - [ ] Use proposed PMID `{cands[0]['pmid'] if cands else '____'}`")
    s.append(f"  - [ ] Use a different PMID: `__________`")
    s.append(f"  - [ ] No PubMed match — mark sourceUrl as the CT.gov page only")
    s.append(f"  - [ ] Skip (snippet is wrong, not the PMID)")
    s.append("")
    s.append("---")
    s.append("")
    return "\n".join(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corrections", type=Path, default=CORRECTIONS_CSV)
    ap.add_argument("--out-md", type=Path, default=OUT_MD)
    ap.add_argument("--out-decisions-csv", type=Path, default=OUT_DECISIONS)
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    with args.corrections.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    cards = [r for r in rows if r['status'] in ('PROBABLE', 'AMBIGUOUS', 'NO_PUBMED_HITS', 'INSUFFICIENT_SNIPPET', 'ALL_LOOKUPS_FAILED')]
    cards.sort(key=lambda r: (r['dashboard'], r['trial_name']))

    md = []
    md.append("# PMID Verification Cards")
    md.append("")
    md.append(f"Generated by `scripts/generate_pmid_verification_cards.py` from")
    md.append(f"`outputs/pmid_corrections.csv`. {len(cards)} cards covering rows that")
    md.append(f"the auto-propose pass could not resolve unambiguously.")
    md.append("")
    md.append("## How to use")
    md.append("")
    md.append("Each card shows the dashboard's current claim (wrong PMID), what")
    md.append("PubMed says about that PMID, the top auto-search candidates with")
    md.append("their scores, and a link to search PubMed manually. Tick one box.")
    md.append("Once a card is decided, record the decision in")
    md.append("`outputs/pmid_verification_decisions.csv` (template provided)")
    md.append("and re-run `scripts/apply_pmid_corrections.py` after expanding it")
    md.append("to read the decisions CSV.")
    md.append("")
    md.append("## Status legend")
    md.append("")
    md.append("- **PROBABLE** — top auto-search candidate has a decent score but")
    md.append("  margin over runner-up was too small for safe auto-apply. Most")
    md.append("  of these are right; just need a quick eyeball on the title.")
    md.append("- **AMBIGUOUS** — multiple candidates have similar scores; pick by hand.")
    md.append("- **NO_PUBMED_HITS** — esearch returned 0; snippet may name the")
    md.append("  trial in a way PubMed doesn't index, or the trial published in a")
    md.append("  non-PubMed venue.")
    md.append("- **INSUFFICIENT_SNIPPET** — snippet had no author/year for auto-search.")
    md.append("")
    md.append("## Cards")
    md.append("")
    by_status: dict[str, int] = {}
    by_dashboard: dict[str, int] = {}
    for r in cards:
        by_status[r['status']] = by_status.get(r['status'], 0) + 1
        by_dashboard[r['dashboard']] = by_dashboard.get(r['dashboard'], 0) + 1
    md.append("**Card counts by status:**")
    md.append("")
    for k, v in sorted(by_status.items(), key=lambda x: -x[1]):
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("---")
    md.append("")

    for i, r in enumerate(cards, 1):
        md.append(render_card(i, r))

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text("\n".join(md), encoding="utf-8")

    # Companion decisions CSV template (one row per card, blank decision col)
    fields = ["card_idx", "dashboard", "trial_name", "current_pmid", "status",
              "decision", "decided_pmid", "decided_url", "decider_id", "decided_at_iso", "note"]
    with args.out_decisions_csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(cards, 1):
            w.writerow({
                "card_idx": i,
                "dashboard": r['dashboard'],
                "trial_name": r['trial_name'],
                "current_pmid": r['current_pmid'],
                "status": r['status'],
                "decision": "",  # use|skip|none
                "decided_pmid": "",
                "decided_url": "",
                "decider_id": "",
                "decided_at_iso": "",
                "note": "",
            })

    print(f"Generated {len(cards)} cards.")
    print(f"  by status: {by_status}")
    print(f"  affecting {len(by_dashboard)} dashboards")
    print(f"Output: {args.out_md}")
    print(f"Decisions CSV template: {args.out_decisions_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
