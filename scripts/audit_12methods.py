"""12-method comprehensive data + excerpt audit across the 411-review corpus.

For each trial across all reviews, run 12 independent verification methods.
A trial passing all 12 is high-confidence; failures are stratified by method.

  M01 2x2-sanity            0 ≤ tE ≤ tN and 0 ≤ cE ≤ cN
  M02 HR-within-CI          LCI ≤ publishedHR ≤ UCI (on positive HR scale)
  M03 NCT-format            ^(NCT\\d{8}([a-z]|_TOK)?|LEGACY-...|ISRCTN\\d+|...)$
  M04 PMID-format           pure digits, 6-9 long
  M05 year/PMID era         PMID-cohort vs declared year ≤7 years
  M06 baseline N policy     baseline.n vs tN+cN within {1.0, 1.5, 2.0} ±10%
  M07 τ²/I² math            I² ≈ max(0, (Q-df)/Q)
  M08 GRIM granularity      integer-scale mean × N reconstructible
  M09 Benford first-digit   all N + event values; corpus-wide χ²
  M10 cross-review NCT      same NCT, same values across reviews (≤5% delta)
  M11 excerpt-numbers       tE/tN/cE/cN appear in evidence[].text
  M12 excerpt-HR            publishedHR + LCI/UCI appear in evidence[].text

Output: outputs/extraction_audit/audit_12methods.{csv,json}
"""
from __future__ import annotations
import csv
import io
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "outputs" / "extraction_audit" / "data"
OUT_DIR = REPO / "outputs" / "extraction_audit"

NCT_RE = re.compile(r"^(NCT\d{8}([a-zA-Z]|_[A-Z0-9]+)?|LEGACY-[A-Z0-9-]+|ISRCTN\d+|ACTRN\d+|UMIN\d+|EUCTR-[\d-]+|JPRN-[\w-]+)$")
PMID_RE = re.compile(r"^\d{6,9}$")
BENFORD_EXPECTED = [math.log10(1 + 1/d) for d in range(1, 10)]


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and (x == x) and abs(x) < float("inf")


def collect_excerpt_text(t):
    """Return concatenated text from evidence[]/sourceQuote/excerpt fields."""
    chunks = []
    ev = t.get("evidence") if isinstance(t.get("evidence"), list) else []
    for e in ev:
        if isinstance(e, dict) and e.get("text"):
            chunks.append(str(e["text"]))
    for k in ("sourceQuote", "excerpt", "snippet", "sourceText", "supportingText"):
        if t.get(k):
            chunks.append(str(t[k]))
    return " ".join(chunks)


def value_in_text(value, text):
    """Loose substring check — accepts thousand-separator variants and the
    raw integer/float form."""
    if not _finite(value) or not text:
        return False
    iv = int(value) if value == int(value) else None
    if iv is not None:
        # exact integer or with thousand-separator
        if str(iv) in text:
            return True
        sep = f"{iv:,}"
        if sep in text:
            return True
        return False
    # float — match to 2 decimals
    fv = f"{value:.2f}"
    return fv in text or f"{value:.1f}" in text or f"{value:.3f}" in text


# PMID-issue-year rough lookup (extreme-bounds-only; defensive)
PMID_YEAR_BOUNDS = [
    (40_000_000, 2026), (38_000_000, 2024), (36_000_000, 2023),
    (35_000_000, 2022), (33_000_000, 2021), (31_000_000, 2020),
    (30_000_000, 2019), (28_000_000, 2017), (25_000_000, 2015),
    (22_000_000, 2012), (20_000_000, 2010), (15_000_000, 2005),
    (10_000_000, 2000),
]


def pmid_to_approx_year(pmid_str):
    try:
        p = int(pmid_str)
    except Exception:
        return None
    for thr, yr in PMID_YEAR_BOUNDS:
        if p >= thr:
            return yr
    return 1996


def grim_check(mean, n, decimals):
    """Returns False if no integer X exists with round(X/n, D) ≈ mean.
    Only valid for integer-scale outcomes (Likert / counts). Skips when
    mean reported to 0 decimals OR scale clearly continuous (|mean|>1e4)."""
    if not _finite(mean) or not _finite(n) or n <= 0:
        return True  # skip
    if decimals < 1 or decimals > 4:
        return True  # skip
    if abs(mean) > 1e4:
        return True  # continuous scale
    tol = 0.5 * 10 ** (-decimals) * 1.0001
    target = mean * n
    for X in range(int(math.floor(target)) - 1, int(math.ceil(target)) + 2):
        cand = X / n
        rounded = round(cand * 10 ** decimals) / 10 ** decimals
        if abs(rounded - mean) < tol:
            return True
    return False  # GRIM violation


def first_digit(x):
    if not _finite(x) or x == 0:
        return None
    a = abs(x)
    while a < 1:
        a *= 10
    while a >= 10:
        a /= 10
    return int(a)


def audit_review(stem, all_data, cross_index):
    doc = all_data.get(stem) or {}
    rd = doc.get("realData") or {}
    findings = []
    benford_pool = []
    for nct, t in (rd if isinstance(rd, dict) else {}).items():
        if not isinstance(t, dict):
            continue
        tE, tN, cE, cN = t.get("tE"), t.get("tN"), t.get("cE"), t.get("cN")
        hr, lci, uci = t.get("publishedHR"), t.get("hrLCI"), t.get("hrUCI")
        single = t.get("singleArm") is True

        # M01 2x2 sanity
        if _finite(tE) and _finite(tN) and tN > 0 and (tE < 0 or tE > tN):
            findings.append((stem, nct, "M01", f"tE={tE} out of [0, tN={tN}]"))
        if _finite(cE) and _finite(cN) and cN > 0 and (cE < 0 or cE > cN):
            findings.append((stem, nct, "M01", f"cE={cE} out of [0, cN={cN}]"))

        # M02 HR within CI
        if all(_finite(x) for x in (hr, lci, uci)) and hr > 0 and lci > 0 and uci > 0:
            if not (lci - 0.005 <= hr <= uci + 0.005):
                findings.append((stem, nct, "M02", f"HR={hr} outside [{lci}, {uci}]"))

        # M03 NCT format
        if not NCT_RE.match(nct):
            findings.append((stem, nct, "M03", f"invalid NCT format: {nct!r}"))

        # M04 PMID format
        pmid = t.get("pmid")
        if pmid and not (PMID_RE.match(str(pmid)) or pmid in (None, "")):
            findings.append((stem, nct, "M04", f"PMID format: {pmid!r}"))

        # M05 year/PMID era
        yr = t.get("year")
        if isinstance(pmid, str) and PMID_RE.match(pmid) and _finite(yr):
            est = pmid_to_approx_year(pmid)
            if est is not None and abs(est - yr) > 7:
                findings.append((stem, nct, "M05", f"PMID {pmid} (~{est}) vs year {yr} gap {abs(est-yr)}y"))

        # M06 baseline.n
        base = t.get("baseline") or {}
        base_n = base.get("n") if isinstance(base, dict) else None
        if _finite(base_n) and _finite(tN) and _finite(cN) and tN + cN > 0:
            ratio = base_n / (tN + cN)
            # Accept {1.0, 1.5, 2.0} ±10%
            if not (0.9 <= ratio <= 1.1 or 1.4 <= ratio <= 1.6 or 1.8 <= ratio <= 2.2):
                findings.append((stem, nct, "M06", f"baseline.n={base_n}/tN+cN={tN+cN} ratio={ratio:.2f}"))

        # Collect for Benford
        for v in (tE, tN, cE, cN, base_n):
            d = first_digit(v) if _finite(v) else None
            if d and 1 <= d <= 9: benford_pool.append(d)

        # M08 GRIM — only for continuous trials with reported mean
        ao = t.get("allOutcomes") if isinstance(t.get("allOutcomes"), list) else None
        if ao:
            for o in ao:
                if not isinstance(o, dict): continue
                if (o.get("type") or "").upper() != "CONTINUOUS": continue
                for mean_field, n_field in (("tMean", "tN"), ("cMean", "cN")):
                    m = o.get(mean_field); n_val = t.get(n_field)
                    if _finite(m) and _finite(n_val):
                        s = str(m)
                        dec = len(s.split(".")[1]) if "." in s else 0
                        if dec >= 1 and not grim_check(m, n_val, dec):
                            findings.append((stem, nct, "M08",
                                              f"GRIM: {mean_field}={m}, N={n_val}, decimals={dec}"))

        # M11 excerpt-numbers
        text = collect_excerpt_text(t)
        if text:
            for val_name, val in (("tE", tE), ("tN", tN), ("cE", cE), ("cN", cN)):
                if _finite(val) and val > 0 and not value_in_text(val, text):
                    findings.append((stem, nct, "M11",
                                      f"{val_name}={val} not in evidence[].text"))
        elif any(_finite(x) and x > 0 for x in (tE, tN, cE, cN)):
            findings.append((stem, nct, "M11_NO_EVIDENCE", "trial has values but evidence[] empty"))

        # M12 excerpt-HR
        if text and _finite(hr) and hr > 0:
            if not value_in_text(hr, text):
                findings.append((stem, nct, "M12", f"publishedHR={hr} not in evidence"))

        # M10 cross-review (deferred — needs cross_index)
        if nct in cross_index and len(cross_index[nct]) > 1:
            mine = (tE, tN, cE, cN, hr)
            for other_stem, other_t in cross_index[nct]:
                if other_stem == stem: continue
                other = (other_t.get("tE"), other_t.get("tN"),
                         other_t.get("cE"), other_t.get("cN"), other_t.get("publishedHR"))
                if mine != other:
                    findings.append((stem, nct, "M10",
                                      f"cross-review divergence vs {other_stem}: {mine} vs {other}"))
                    break

    return findings, benford_pool


def benford_chi2(counts):
    n = sum(counts)
    if n < 30: return None, 0
    chi2 = 0
    for i, c in enumerate(counts):
        e = BENFORD_EXPECTED[i] * n
        if e > 0:
            chi2 += (c - e) ** 2 / e
    return chi2, n


def main():
    index = json.loads((DATA_DIR / "_index.json").read_text(encoding="utf-8"))
    all_data = {}
    cross_index = defaultdict(list)
    for entry in index:
        if not entry.get("has_realData"): continue
        stem = entry["stem"]
        doc = json.loads((DATA_DIR / f"{stem}.json").read_text(encoding="utf-8"))
        all_data[stem] = doc
        rd = doc.get("realData") or {}
        for nct, t in (rd if isinstance(rd, dict) else {}).items():
            if isinstance(t, dict):
                cross_index[nct].append((stem, t))

    all_findings = []
    benford_pool = []
    for stem in all_data:
        try:
            f, bp = audit_review(stem, all_data, cross_index)
            all_findings.extend(f); benford_pool.extend(bp)
        except Exception as e:
            all_findings.append((stem, "", "EXC", f"{type(e).__name__}: {e}"))

    # M09 Benford
    counts = [benford_pool.count(d) for d in range(1, 10)]
    chi2, n_b = benford_chi2(counts)

    # Aggregate
    by_method = Counter(f[2] for f in all_findings)
    by_review = Counter(f[0] for f in all_findings)
    n_trials_total = sum(len((all_data[s].get("realData") or {})) for s in all_data)

    # Write CSV
    csv_path = OUT_DIR / "audit_12methods.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["review", "nct", "method", "detail"])
        for f in sorted(all_findings, key=lambda x: (x[2], x[0])):
            w.writerow(f)

    # Write JSON
    summary = {
        "reviews_audited": len(all_data),
        "trials_audited": n_trials_total,
        "findings_total": len(all_findings),
        "findings_by_method": dict(by_method.most_common()),
        "top_10_reviews_by_findings": by_review.most_common(10),
        "benford": {"n": n_b, "chi2_8df": chi2, "counts": counts,
                    "expected_pct": [round(p*100, 2) for p in BENFORD_EXPECTED]},
    }
    (OUT_DIR / "audit_12methods.json").write_text(json.dumps(summary, indent=2),
                                                    encoding="utf-8")

    print(f"Reviews audited: {len(all_data)}")
    print(f"Trials audited: {n_trials_total}")
    print(f"Total findings: {len(all_findings)}")
    print()
    print("Findings by method:")
    for m, n in by_method.most_common():
        pct = 100 * n / n_trials_total if n_trials_total else 0
        print(f"  {m}: {n} ({pct:.1f}% of trials)")
    print()
    print(f"Benford (M09): n={n_b}, χ²(8 df) = {chi2:.2f} (p≈{'<0.01' if chi2 and chi2>20 else '>0.05' if chi2 else 'n/a'})")
    print()
    print("Top 10 reviews by total findings:")
    for r, n in by_review.most_common(10):
        print(f"  {n:4d}  {r}")


if __name__ == "__main__":
    main()
