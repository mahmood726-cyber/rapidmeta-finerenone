"""Parse PMC full-text XML and inject evidence[] entries.

For each target trial with a PMC full-text:
  1. Extract all sentences from body paragraphs (skip references, tables for now)
  2. Score each sentence against trial's tE/tN/cE/cN/publishedHR
  3. If best sentence has ≥3 matching values, inject as evidence[]
"""
from __future__ import annotations
import json, re, sys, io, math
from pathlib import Path
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
PMC_CACHE = OUT / "pmc_cache"
DRY = "--dry-run" in sys.argv

PMID_TO_PMC = json.loads((PMC_CACHE / "pmid_to_pmc.json").read_text(encoding="utf-8"))


def extract_text_from_pmc(pmc_id: str) -> tuple[str, str, str]:
    """Return (title, body_text, doi) from PMC XML."""
    p = PMC_CACHE / f"PMC{pmc_id}.xml"
    if not p.exists(): return "", "", ""
    try:
        root = ET.parse(p).getroot()
    except Exception:
        return "", "", ""
    # Title
    title_el = root.find(".//article-title")
    title = "".join(title_el.itertext()).strip() if title_el is not None else ""
    # DOI
    doi = ""
    for aid in root.findall(".//article-id"):
        if aid.get("pub-id-type") == "doi":
            doi = (aid.text or "").strip()
            break
    # Body — concat all <p> text inside <body>, skip refs
    body_paragraphs = []
    body = root.find(".//body")
    if body is not None:
        for p_el in body.findall(".//p"):
            txt = "".join(p_el.itertext()).strip()
            if len(txt) >= 50:
                body_paragraphs.append(txt)
    # If no body (some PMCs only have abstract), use abstract
    if not body_paragraphs:
        ab = root.find(".//abstract")
        if ab is not None:
            for p_el in ab.findall(".//p"):
                txt = "".join(p_el.itertext()).strip()
                if len(txt) >= 50:
                    body_paragraphs.append(txt)
    return title, " ".join(body_paragraphs), doi


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z\d])", text)
    return [s.strip() for s in raw if 20 <= len(s.strip()) <= 600]


def find_numbers(s: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", s))


def score_sentence(sent: str, trial: dict) -> tuple[int, list[str]]:
    nums = find_numbers(sent)
    matched = []
    def try_value(v, label):
        if v is None: return False
        try: v = float(v)
        except: return False
        forms = set()
        iv = int(v)
        if abs(v - iv) < 1e-9: forms.add(str(iv))
        forms.add(f"{v:g}"); forms.add(f"{v:.1f}"); forms.add(f"{v:.2f}")
        for f in forms:
            if f in nums:
                matched.append(f"{label}={v}")
                return True
        return False
    for key in ("tE", "tN", "cE", "cN"):
        try_value(trial.get(key), key)
    for num_k, den_k in (("tE","tN"), ("cE","cN")):
        try:
            num = float(trial.get(num_k)); den = float(trial.get(den_k))
            if den > 0:
                pct = 100.0 * num / den
                for f in {f"{pct:.1f}", f"{pct:.0f}", f"{pct-0.1:.1f}", f"{pct+0.1:.1f}"}:
                    if f in nums:
                        matched.append(f"{num_k}/{den_k}%={pct:.1f}")
                        break
        except: pass
    for key in ("publishedHR", "hrLCI", "hrUCI"):
        try_value(trial.get(key), key)
    return len(set(matched)), list(set(matched))


def build_evidence(trial: dict, sentences: list[str], pmc_id: str, doi: str) -> dict | None:
    best_score, best_sent, best_matches = 0, None, []
    for s in sentences:
        sc, matches = score_sentence(s, trial)
        if sc >= 1 and re.search(r"\b(HR|hazard ratio|95% CI|confidence interval|odds ratio|OR|relative risk|RR|primary end|primary outcome)\b", s, re.IGNORECASE):
            sc += 1
        if sc > best_score:
            best_score, best_sent, best_matches = sc, s, matches
    # Higher threshold than abstract — full-text has more sentences to match
    if best_score < 3 or not best_sent: return None
    highlight_vals = sorted({m.split("=")[-1] for m in best_matches}, key=lambda s: -len(s))[:6]
    return {
        "label": "Primary" if re.search(r"\bprimary\b", best_sent, re.IGNORECASE) else "Outcome",
        "source": "PMC full-text",
        "text": best_sent[:600],
        "highlights": highlight_vals,
        "sourceUrl": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/" +
                     (f" doi:{doi}" if doi else ""),
    }


# Identify target trials
target = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        if t.get("evidence"): continue
        pmid = (t.get("pmid") or "").strip()
        if not pmid.isdigit(): continue
        pmc = PMID_TO_PMC.get(pmid)
        if not pmc: continue
        target.append({"review": rv, "nct": nct, "pmid": pmid, "pmc": pmc, "trial": t})

print(f"Target trials with PMC available: {len(target)}")

# Build patches per review
patches = {}
n_built = 0
for t in target:
    title, body, doi = extract_text_from_pmc(t["pmc"])
    if not body: continue
    sentences = split_sentences(body)
    ev = build_evidence(t["trial"], sentences, t["pmc"], doi)
    if not ev: continue
    patches.setdefault(t["review"], {})[t["nct"]] = ev
    n_built += 1

print(f"Evidence entries built (≥3 number matches): {n_built}")


# Apply (similar to apply_evidence_and_null_wrong_pmids.py)
def inject_evidence_in_html(rv_stem: str, patches_for_review: dict) -> tuple[int, list[str]]:
    html_path = HERE / f"{rv_stem}.html"
    if not html_path.exists():
        return 0, [f"file-missing:{rv_stem}.html"]
    txt = html_path.read_text(encoding="utf-8")
    errors = []
    changed = 0
    for nct, ev in patches_for_review.items():
        key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
        m = key_pat.search(txt)
        if not m:
            errors.append(f"{nct}:key-not-found")
            continue
        start = m.end()
        depth = 1; i = start; in_str = None
        while i < len(txt) and depth > 0:
            ch = txt[i]
            if in_str:
                if ch == "\\": i += 2; continue
                if ch == in_str: in_str = None
            else:
                if ch in ('"',"'"): in_str = ch
                elif ch == "{": depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0: break
            i += 1
        if depth != 0:
            errors.append(f"{nct}:unbalanced")
            continue
        close_brace = i
        body = txt[start:close_brace]
        if re.search(r'\bevidence\s*:\s*\[', body):
            continue
        ev_js = "evidence: " + json.dumps([ev], ensure_ascii=False) + ","
        j = close_brace - 1
        while j > start and txt[j] in " \n\r\t": j -= 1
        prefix = txt[:j+1]
        if txt[j] != ",":
            prefix = prefix + ","
        new_txt = prefix + "\n                    " + ev_js + "\n                " + txt[close_brace:]
        txt = new_txt
        changed += 1
    if changed and not DRY:
        html_path.write_text(txt, encoding="utf-8")
    return changed, errors


total_injected = 0
log = []
for rv, p in patches.items():
    n, errs = inject_evidence_in_html(rv, p)
    total_injected += n
    log.append({"review": rv, "injected": n, "errors": errs})

(OUT / "pmc_evidence_injected.json").write_text(
    json.dumps({"total_injected": total_injected, "by_review": log,
                 "summary": {"target_trials": len(target),
                              "evidence_built": n_built,
                              "evidence_injected": total_injected}},
                indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n{'DRY-RUN ' if DRY else ''}Evidence injected from PMC full-text: {total_injected}")
