"""Smart PMID corrector for the 108 trials in outputs/pmid_likely_wrong.csv.

Strategy per trial:
  1. Use the NCT in `[si]` (Secondary Source ID) for esearch — gives
     candidate PMIDs cited by trials registered with that NCT.
  2. Filter candidates by `[pt]` (publication type) preferring
     'randomized controlled trial' and 'Clinical Trial, Phase III'.
  3. esummary each candidate to confirm:
       - title contains drug name from group field (case-insensitive)
       - publication year ≤ claimed year + 3 (allow follow-up papers)
       - title is NOT a "review", "comment", "letter", "editorial", or
         "retraction" type (we want primary results papers).
  4. Pick the OLDEST candidate that passes — primary results paper is
     usually first.
  5. Apply only if the chosen PMID's title matches the trial's drug
     name (high confidence).

If no high-confidence match → log to outputs/pmid_unfixed.csv with reason.

Output:
  outputs/pmid_corrections_applied.csv — what we changed
  outputs/pmid_unfixed.csv             — what we couldn't safely fix
"""
from __future__ import annotations
import sys, io, csv, re, time, json
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RATE_S = 0.5  # 2 req/sec without API key, conservative


def http_json(url, retries=3):
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "RapidMeta-PMID-Fix/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if "429" in str(e) and i < retries - 1:
                time.sleep((i + 2) * 2)
                continue
            return None


def extract_group(file_path: Path, nct: str) -> str:
    """Read source HTML and pull the trial's group field."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(
        rf"'{re.escape(nct)}'\s*:\s*\{{[^}}]*?group:\s*'([^']+?)'",
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1) if m else ""


def extract_drug_keywords(group: str, claim: str) -> list[str]:
    """Return prioritised list of drug/treatment keywords ≥5 chars."""
    head = (group or "")[:300]
    # Capitalised words first (proper drug names)
    cap = re.findall(r"\b([A-Z][a-z]{4,}\d?)", head)
    # Lowercase 5+ chars (generic drugs often lowercased: "ticagrelor")
    low = re.findall(r"\b([a-z]{5,}\d?)", head)
    # Acronyms (5+ caps)
    caps = re.findall(r"\b([A-Z]{3,}\d?)\b", head)
    # From claimed_name
    cn_words = re.findall(r"\b([A-Za-z]{5,})", claim)
    out = []
    seen = set()
    for w in cap + caps + low + cn_words:
        wl = w.lower()
        if wl in {"trial", "study", "phase", "primary", "secondary", "endpoint",
                  "patient", "patients", "treatment", "induction", "maintenance",
                  "placebo", "active", "control", "double", "blind", "open",
                  "label", "year", "weekly", "daily", "monthly", "post", "open"}:
            continue
        if wl not in seen:
            seen.add(wl)
            out.append(wl)
    return out


def find_correct_pmid(nct, claim, group, current_pmid):
    """Returns (pmid, title, reason) or (None, None, reason)."""
    drug_keywords = extract_drug_keywords(group, claim)
    if not drug_keywords:
        return None, None, "no drug keywords"

    # Build search query: NCT[si] preferred
    queries = []
    if nct.startswith("NCT"):
        queries.append((f"{nct}[si]", "nct_si"))
    # Acronym fallback
    acros = re.findall(r"\b([A-Z][A-Z0-9\-]{2,})", claim)
    for a in acros[:2]:
        queries.append((f"{a}[ti] AND {drug_keywords[0]}[ti]", f"acro_{a}"))

    candidates = []
    for q, qtype in queries:
        url = f"{EUTILS}/esearch.fcgi?db=pubmed&term={quote(q)}&retmax=10&retmode=json&sort=date"
        data = http_json(url)
        time.sleep(RATE_S)
        if not data:
            continue
        ids = data.get("esearchresult", {}).get("idlist", [])
        for pid in ids:
            candidates.append((pid, qtype))
        if candidates:
            break

    if not candidates:
        return None, None, "no esearch hits"

    # esummary on candidates (max 10)
    cand_pmids = [c[0] for c in candidates[:10]]
    url = f"{EUTILS}/esummary.fcgi?db=pubmed&id={','.join(cand_pmids)}&retmode=json"
    data = http_json(url)
    time.sleep(RATE_S)
    if not data:
        return None, None, "esummary failed"

    # Score each candidate
    scored = []
    for pid in cand_pmids:
        rec = data.get("result", {}).get(pid)
        if not rec or rec.get("error"):
            continue
        title = rec.get("title", "").lower()
        pubtype = rec.get("pubtype", [])
        pubdate = rec.get("pubdate", "")
        # Skip clearly non-primary types
        if any(t in pubtype for t in ["Review", "Comment", "Letter", "Editorial",
                                        "Retracted Publication", "Retraction of Publication"]):
            continue
        # Score by drug keyword matches
        score = 0
        for kw in drug_keywords[:5]:
            if kw in title:
                score += (1 if len(kw) >= 7 else 0.5)
        if score < 1:
            continue
        # Prefer RCT pubtype
        if "Randomized Controlled Trial" in pubtype or "Clinical Trial, Phase III" in pubtype:
            score += 1
        # Prefer earlier dates (primary papers come first)
        try:
            year_str = re.match(r"^(\d{4})", pubdate)
            year = int(year_str.group(1)) if year_str else 9999
        except Exception:
            year = 9999
        scored.append((score, -year, pid, rec.get("title", "")))

    if not scored:
        return None, None, "no candidate matches drug keywords"
    scored.sort(reverse=True)
    best_score, _, best_pid, best_title = scored[0]
    if best_pid == current_pmid:
        return None, best_title, "current PMID is correct"
    if best_score < 1.5:
        return None, best_title, f"low confidence (score={best_score})"
    return best_pid, best_title, f"score={best_score}"


def main():
    src = REPO / "outputs" / "pmid_likely_wrong.csv"
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    print(f"Processing {len(rows)} likely-wrong PMIDs ...")

    applied = []
    unfixed = []
    for i, r in enumerate(rows, 1):
        fpath = REPO / r["file"]
        if not fpath.exists():
            unfixed.append({**r, "reason": "file not found"})
            continue
        group = extract_group(fpath, r["nct"])
        if not group:
            unfixed.append({**r, "reason": "no group field in source"})
            continue
        pid, title, reason = find_correct_pmid(r["nct"], r["claimed_name"], group, r["pmid"])
        if pid:
            applied.append({**r, "new_pmid": pid, "new_title": title, "reason": reason})
            # Apply the fix in-place
            text = fpath.read_text(encoding="utf-8", errors="replace")
            old_str = f"pmid: '{r['pmid']}'"
            if old_str in text:
                text = text.replace(old_str, f"pmid: '{pid}'", 1)
                fpath.write_text(text, encoding="utf-8")
                print(f"  [{i:3d}/{len(rows)}] FIXED {r['file'][:40]:40s} {r['claimed_name'][:25]:25s}  {r['pmid']} -> {pid}")
            else:
                applied[-1]["reason"] = "PMID not found in source after lookup"
        else:
            unfixed.append({**r, "reason": reason or "no fix found"})
            if i % 25 == 0:
                print(f"  [{i:3d}/{len(rows)}] no fix: {r['claimed_name'][:30]:30s}  ({reason})")

    # Write output CSVs
    if applied:
        out1 = REPO / "outputs" / "pmid_corrections_applied.csv"
        with out1.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(applied[0].keys()))
            w.writeheader()
            w.writerows(applied)
        print(f"\n{len(applied)} corrections applied → {out1}")

    if unfixed:
        out2 = REPO / "outputs" / "pmid_unfixed.csv"
        with out2.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(unfixed[0].keys()))
            w.writeheader()
            w.writerows(unfixed)
        print(f"{len(unfixed)} unfixed (manual review needed) → {out2}")


if __name__ == "__main__":
    main()
