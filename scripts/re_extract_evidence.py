"""Re-extraction pipeline: populate evidence[] arrays from PubMed abstracts.

For each trial in the 204 "zero-evidence" reviews:
  1. Read the existing pmid from realData
  2. Fetch PubMed abstract via cached MCP call
  3. Score each sentence for relevance to the trial's tE/tN/cE/cN/HR values
  4. If best sentence has ≥2 number matches OR contains 'HR' near the published HR,
     append to evidence[] as {label, source, text, highlights, sourceUrl}
  5. Write back as a patch dict per-review (NOT modifying HTML directly here —
     the apply step is separate, so we can dry-run + diff before mutating).

Idempotency: cache file outputs/extraction_audit/pubmed_cache/<pmid>.json
holds the abstract; the result is keyed by (review, nct, pmid, sha256(abstract)).

Outputs (dry-run):
  outputs/extraction_audit/evidence_patches/<REVIEW>.json
"""
from __future__ import annotations
import csv, json, re, sys, os, io, hashlib, time
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
DATA_DIR = HERE / "outputs" / "extraction_audit" / "data"
CACHE_DIR = HERE / "outputs" / "extraction_audit" / "pubmed_cache"
PATCH_DIR = HERE / "outputs" / "extraction_audit" / "evidence_patches"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
PATCH_DIR.mkdir(parents=True, exist_ok=True)

ZERO_EV = json.loads((HERE / "outputs" / "extraction_audit" / "zero_evidence_reviews.json").read_text(encoding="utf-8"))


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    # Simple period-split; preserves Dr./e.g./i.e. by requiring upper-case start of next sentence
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z\d])", text)
    return [s.strip() for s in raw if s.strip()]


def find_numbers(s: str) -> set[str]:
    """Numbers as raw substrings — int and decimal."""
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", s))


def score_sentence(sent: str, trial: dict) -> tuple[int, list[str]]:
    """How many of the trial's known values appear (as substring) in this sentence?
    Tries multiple representations: raw count, decimal, percent (tE/tN*100), and HR/CI.
    Returns (count, matched_strings).
    """
    nums = find_numbers(sent)
    matched = []

    def try_value(v, label):
        if v is None:
            return False
        try:
            v = float(v)
        except Exception:
            return False
        forms = set()
        iv = int(v)
        if abs(v - iv) < 1e-9:
            forms.add(str(iv))
        forms.add(f"{v:g}")
        forms.add(f"{v:.1f}")
        forms.add(f"{v:.2f}")
        for f in forms:
            if f in nums:
                matched.append(f"{label}={v}")
                return True
        return False

    # Raw counts
    for key in ("tE", "tN", "cE", "cN"):
        try_value(trial.get(key), key)
    # Percent forms: tE/tN, cE/cN
    for num_k, den_k in (("tE", "tN"), ("cE", "cN")):
        try:
            num = float(trial.get(num_k))
            den = float(trial.get(den_k))
            if den > 0:
                pct = 100.0 * num / den
                # try ±0.05 tolerance
                for f in {f"{pct:.1f}", f"{pct:.0f}", f"{pct-0.1:.1f}", f"{pct+0.1:.1f}"}:
                    if f in nums:
                        matched.append(f"{num_k}/{den_k}%={pct:.1f}")
                        break
        except (TypeError, ValueError):
            pass
    # HR + CI
    for key in ("publishedHR", "hrLCI", "hrUCI"):
        try_value(trial.get(key), key)

    return len(set(matched)), list(set(matched))


def build_evidence_for_trial(nct: str, trial: dict, abstract: str, journal: str, doi: str) -> dict | None:
    """Build one evidence entry from the best-matching abstract sentence."""
    if not abstract:
        return None
    sents = split_sentences(abstract)
    has_any_val = any(trial.get(k) is not None for k in ("tE","tN","cE","cN","publishedHR"))
    if not has_any_val:
        return None
    best_score, best_sent, best_matches = 0, None, []
    for s in sents:
        sc, matches = score_sentence(s, trial)
        # bonus for HR/CI keywords near a numeric match
        if sc >= 1 and re.search(r"\b(HR|hazard ratio|95% CI|confidence interval|relative risk|\bRR\b|odds ratio|\bOR\b|primary end|primary outcome|reduction)\b", s, re.IGNORECASE):
            sc += 1
        if sc > best_score:
            best_score, best_sent, best_matches = sc, s, matches

    # Require ≥2 matched values OR (≥1 + HR keyword bonus already applied)
    if best_score < 2 or not best_sent:
        return None
    label_kw = "Primary" if re.search(r"\bprimary\b", best_sent, re.IGNORECASE) else "Outcome"
    # Highlights: extract just the value strings (drop the label prefix)
    highlight_vals = sorted({m.split("=")[-1] for m in best_matches}, key=lambda s: -len(s))[:6]
    return {
        "label": label_kw,
        "source": journal or "PubMed",
        "text": best_sent[:600],
        "highlights": highlight_vals,
        "sourceUrl": f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{trial.get('pmid','')}/",
    }


def get_cache_path(pmid: str) -> Path:
    return CACHE_DIR / f"{pmid}.json"


def cache_get(pmid: str) -> dict | None:
    p = get_cache_path(pmid)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def cache_set(pmid: str, payload: dict):
    p = get_cache_path(pmid)
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def collect_pmids_to_fetch() -> list[tuple[str, str, str]]:
    """Return list of (review, nct, pmid) for trials needing evidence."""
    out = []
    for entry in ZERO_EV:
        rv = entry["review"]
        json_p = DATA_DIR / f"{rv}.json"
        if not json_p.exists():
            continue
        try:
            d = json.loads(json_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        rd = d.get("realData") or {}
        if not isinstance(rd, dict):
            continue
        for nct, t in rd.items():
            if not isinstance(t, dict):
                continue
            if t.get("evidence") and len(t.get("evidence", [])) >= 1:
                continue  # already has evidence
            pmid = (t.get("pmid") or "").strip()
            if not pmid or not pmid.isdigit() or len(pmid) < 6 or len(pmid) > 9:
                continue
            out.append((rv, nct, pmid))
    return out


def report():
    todo = collect_pmids_to_fetch()
    by_rv = defaultdict(int)
    for rv, _, _ in todo:
        by_rv[rv] += 1
    print(f"Trials needing re-extraction: {len(todo)}")
    print(f"Reviews touched:              {len(by_rv)}")
    print(f"Unique PMIDs to fetch:        {len(set(p for _,_,p in todo))}")
    print(f"Already cached PMIDs:         {sum(1 for p in {p for _,_,p in todo} if cache_get(p))}")
    return todo


def detect_wrong_pmid(nct: str, trial: dict, cache: dict) -> tuple[bool, str]:
    """Return (is_wrong, reason). Topic-sanity check: the abstract or title
    should contain SOMETHING relating to the trial (acronym, NCT, intervention).
    """
    if not cache or not cache.get("abstract"):
        return False, "no-abstract"
    blob = (cache.get("title", "") + " " + cache.get("abstract", "")).lower()
    # Look for NCT in text
    if nct.lower() in blob:
        return False, "nct-in-abstract"
    # Look for acronym (the 'name' field, e.g. 'STRIVE')
    name = (trial.get("name") or "").strip()
    if name and len(name) >= 3:
        if name.lower() in blob:
            return False, "acronym-in-abstract"
    # Look for any NCT in the abstract at all
    nct_in_abs = re.findall(r"NCT\d{8}", blob, re.IGNORECASE)
    if nct_in_abs and nct.upper() not in [n.upper() for n in nct_in_abs]:
        return True, f"abstract-cites-different-NCT:{nct_in_abs[0]}"
    # If trial 'group' field has an intervention drug name, look for it
    group = (trial.get("group") or "").lower()
    drug_words = [w for w in re.findall(r"\b[a-z]+\b", group) if len(w) >= 6
                   and w not in {"placebo", "control", "patients", "treatment", "patient"}]
    if drug_words and not any(d in blob for d in drug_words[:3]):
        return True, f"no-intervention-overlap:{','.join(drug_words[:3])}"
    return False, "ambiguous"


if __name__ == "__main__":
    todo = report()
    print()
    if "--list-pmids" in sys.argv:
        pmids = sorted({p for _, _, p in todo})
        out_list = HERE / "outputs" / "extraction_audit" / "pmids_to_fetch.txt"
        out_list.write_text("\n".join(pmids), encoding="utf-8")
        print(f"PMIDs list -> {out_list} ({len(pmids)} PMIDs)")
    if "--detect-wrong-pmid" in sys.argv:
        wrong = []
        for rv, nct, pmid in todo:
            cache = cache_get(pmid)
            if not cache: continue
            json_p = DATA_DIR / f"{rv}.json"
            d = json.loads(json_p.read_text(encoding="utf-8"))
            trial = (d.get("realData") or {}).get(nct, {})
            is_wrong, reason = detect_wrong_pmid(nct, trial, cache)
            if is_wrong:
                wrong.append({"review": rv, "nct": nct, "pmid": pmid,
                              "trial_name": trial.get("name"),
                              "trial_group": trial.get("group"),
                              "reason": reason,
                              "abstract_snippet": cache.get("abstract", "")[:120]})
        out_p = HERE / "outputs" / "extraction_audit" / "wrong_pmids.json"
        out_p.write_text(json.dumps(wrong, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Detected {len(wrong)} likely-wrong PMIDs -> {out_p}")
        # Top reviews
        from collections import Counter
        c = Counter(w["review"] for w in wrong)
        print("Top reviews:")
        for rv, n in c.most_common(15):
            print(f"  {n:4d}  {rv}")
    if "--apply" in sys.argv:
        # Process cached PMIDs only, build patches
        patches = defaultdict(dict)
        n_built = n_skipped = 0
        for rv, nct, pmid in todo:
            cache = cache_get(pmid)
            if not cache or not cache.get("abstract"):
                n_skipped += 1
                continue
            json_p = DATA_DIR / f"{rv}.json"
            d = json.loads(json_p.read_text(encoding="utf-8"))
            trial = (d.get("realData") or {}).get(nct, {})
            ev = build_evidence_for_trial(nct, trial, cache.get("abstract", ""),
                                           cache.get("journal", ""), cache.get("doi", ""))
            if not ev:
                n_skipped += 1
                continue
            patches[rv][nct] = ev
            n_built += 1
        for rv, p in patches.items():
            out_p = PATCH_DIR / f"{rv}.json"
            out_p.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nBuilt {n_built} evidence entries (skipped {n_skipped} without sufficient abstract match)")
        print(f"Patches -> {PATCH_DIR}")
