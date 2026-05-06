"""Extract trial baseline characteristics via regex from the `group:` field
text and inject as `baseline: {n, age, pct_female, followup}` on each
realData entry. Idempotent.

Sources of baseline text in our corpus:
  - `group: '...'` typically contains the population description
    (e.g., 'Patients aged 60 years (mean), 47% female, n=4668...')
  - Some trials have a `baseline: {n, age, female}` object already

Regex patterns (best-effort; flagged confidence):
  age           — 'mean age \d+', 'median age \d+', 'aged \d+ years'
  pct_female    — '\d+% female', '\d+ women', '\d+ \(\d+%\) female'
  followup      — 'follow-up X months', 'X-year follow-up', 'X mo' near outcome
  n             — fallback to tN + cN

Output: outputs/baseline_extraction.csv with what each trial got + a
file-level inject report.
"""
from __future__ import annotations
import sys, io, csv, re, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent

# Match a complete trial entry: name, group, plus tN+cN we'll need
TRIAL_RE = re.compile(
    r"('NCT\d+(?:[A-Z]|_[A-Za-z0-9]+)?'\s*:\s*\{[^}]*?"
    r"name:\s*'([^']+?)',[^}]*?"
    r"tN:\s*([\d.eE+\-]+|null|None|NaN)[^}]*?"
    r"cN:\s*([\d.eE+\-]+|null|None|NaN)[^}]*?"
    r"group:\s*'([^']+?)')",
    re.DOTALL,
)


def parse_int(s):
    if s is None: return None
    s = str(s).strip()
    if s.lower() in ('null', 'none', 'nan'): return None
    try:
        v = float(s)
        return int(v) if v == int(v) else int(v)
    except (ValueError, TypeError):
        return None


def extract_age(text):
    """Best-effort mean age extraction."""
    # Mean age N years
    m = re.search(r'mean\s+age\D{0,5}(\d{2,3}(?:\.\d)?)\s*(?:years|y\b|yo\b)?', text, re.IGNORECASE)
    if m: return float(m.group(1))
    # Median age N
    m = re.search(r'median\s+age\D{0,5}(\d{2,3}(?:\.\d)?)\s*(?:years|y\b|yo\b)?', text, re.IGNORECASE)
    if m: return float(m.group(1))
    # Aged N years
    m = re.search(r'\baged?\s+(\d{2,3}(?:\.\d)?)\s*(?:years|y\b|yo\b)', text, re.IGNORECASE)
    if m: return float(m.group(1))
    # "age N (SD..)"
    m = re.search(r'\bage\s*[:=]?\s*(\d{2,3}(?:\.\d)?)\s*(?:years|y\b|yo\b|\(SD)', text, re.IGNORECASE)
    if m: return float(m.group(1))
    return None


def extract_pct_female(text):
    """Best-effort percent female."""
    # "X% female" or "X% women"
    m = re.search(r'(\d{1,2}(?:\.\d)?)\s*%\s+(?:female|women)', text, re.IGNORECASE)
    if m: return float(m.group(1))
    m = re.search(r'(?:female|women)\D{0,10}(\d{1,2}(?:\.\d)?)\s*%', text, re.IGNORECASE)
    if m: return float(m.group(1))
    # "X (Y%) female" — extract the percentage
    m = re.search(r'\(\s*(\d{1,2}(?:\.\d)?)\s*%\s*\)\s+(?:female|women)', text, re.IGNORECASE)
    if m: return float(m.group(1))
    # "n=X (Y%) women"
    m = re.search(r'(?:female|women)[^,;.]{0,30}(\d{1,2}(?:\.\d)?)\s*%', text, re.IGNORECASE)
    if m:
        v = float(m.group(1))
        if 0 <= v <= 100: return v
    # "Sex: ALL" — undifferentiated, return None
    return None


def extract_followup(text):
    """Best-effort follow-up duration in MONTHS."""
    # "median follow-up X months/years"
    m = re.search(r'(?:median|mean)?\s*follow.?up\D{0,15}(\d+(?:\.\d+)?)\s*(months?|mo\b|years?|yrs?\b|y\b|wks?|weeks?)', text, re.IGNORECASE)
    if m:
        v = float(m.group(1))
        unit = m.group(2).lower()
        if 'wk' in unit or 'week' in unit: return v / 4.345
        if 'y' in unit and 'mo' not in unit: return v * 12
        return v
    # "X-year follow-up" / "X-month follow-up"
    m = re.search(r'(\d+(?:\.\d+)?)[\s-]+(year|month|mo|yr|wk|week)\D{0,5}follow.?up', text, re.IGNORECASE)
    if m:
        v = float(m.group(1))
        unit = m.group(2).lower()
        if 'wk' in unit or 'week' in unit: return v / 4.345
        if 'y' in unit: return v * 12
        return v
    # Trial duration mentioned without "follow-up"
    m = re.search(r'(?:over|during|across|at)\s+(\d+(?:\.\d+)?)[\s-]+(year|month|mo)', text, re.IGNORECASE)
    if m:
        v = float(m.group(1))
        unit = m.group(2).lower()
        if 'y' in unit: return v * 12
        return v
    # "wk N" or "week N" (treatment endpoint duration)
    m = re.search(r'(?:wk|week)s?\s+(\d{1,3})\b', text, re.IGNORECASE)
    if m:
        return float(m.group(1)) / 4.345
    return None


def extract_for_trial(group_text, tN, cN):
    """Compute baseline object."""
    n = (tN or 0) + (cN or 0)
    age = extract_age(group_text)
    pct_f = extract_pct_female(group_text)
    fu = extract_followup(group_text)
    out = {}
    if n > 0: out['n'] = n
    if age is not None: out['age'] = age
    if pct_f is not None: out['pct_female'] = pct_f
    if fu is not None: out['followup'] = round(fu, 1)
    return out


def already_has_baseline(block_text):
    return bool(re.search(r'baseline:\s*\{', block_text))


def patch_file(text):
    """Inject baseline objects in-place. Returns (new_text, n_added)."""
    out_chunks = []
    last = 0
    n_added = 0
    rows = []
    for m in TRIAL_RE.finditer(text):
        block, name, tN_s, cN_s, group = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        if already_has_baseline(block):
            continue
        tN = parse_int(tN_s)
        cN = parse_int(cN_s)
        baseline = extract_for_trial(group, tN, cN)
        rows.append({"name": name, **baseline})
        if not baseline:
            continue
        # Insert "baseline: {...}, " right after `name: '...'` field
        baseline_str = json.dumps(baseline)
        # Convert to JS-style (single quotes around keys keep, but we'll go bare)
        baseline_js = "{" + ", ".join(f"{k}: {json.dumps(v)}" for k, v in baseline.items()) + "}"
        # Inject right after the "name: '...',"
        new_block = re.sub(
            r"(name:\s*'[^']+?',)",
            r"\1 baseline: " + baseline_js + ",",
            block,
            count=1,
        )
        out_chunks.append(text[last:m.start()])
        out_chunks.append(new_block)
        last = m.end()
        n_added += 1
    out_chunks.append(text[last:])
    return "".join(out_chunks), n_added, rows


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Scanning {len(files)} files ...")
    total_added = 0
    all_rows = []
    files_modified = 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, n_added, rows = patch_file(text)
        for r in rows:
            r["file"] = hp.name
            all_rows.append(r)
        if n_added > 0:
            hp.write_text(new_text, encoding="utf-8")
            total_added += n_added
            files_modified += 1

    out = REPO / "outputs" / "baseline_extraction.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ['file', 'name', 'n', 'age', 'pct_female', 'followup']
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in all_rows:
            w.writerow(r)

    print(f"\n=== Summary ===")
    print(f"  Trials with baseline added: {total_added}")
    print(f"  Files modified:             {files_modified}")
    n_with_age = sum(1 for r in all_rows if r.get('age'))
    n_with_pf = sum(1 for r in all_rows if r.get('pct_female'))
    n_with_fu = sum(1 for r in all_rows if r.get('followup'))
    n_total = len(all_rows)
    print(f"  Coverage:")
    print(f"    age:        {n_with_age}/{n_total} ({100*n_with_age/max(1,n_total):.0f}%)")
    print(f"    pct_female: {n_with_pf}/{n_total} ({100*n_with_pf/max(1,n_total):.0f}%)")
    print(f"    followup:   {n_with_fu}/{n_total} ({100*n_with_fu/max(1,n_total):.0f}%)")
    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
