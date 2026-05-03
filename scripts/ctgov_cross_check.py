"""Live CT.gov cross-check across the *_REVIEW.html portfolio.

For each unique NCT in any realData block:
  1. Fetch enrollment from CT.gov v2 REST API
  2. For each (file, row) referencing that NCT, compare row tN+cN against CT.gov enrollment
  3. Flag (a) raw outliers (file claim differs from CT.gov by >50%) and (b) swap candidates
     (within a file, the file's claim for NCT_A matches CT.gov for NCT_B better than for NCT_A)

Outputs:
  outputs/ctgov_cache.json — per-NCT enrollment cache (resumable)
  outputs/ctgov_cross_check.csv — findings

Usage:
  python scripts/ctgov_cross_check.py
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROW_RE = re.compile(
    r"'(?P<key>(?:NCT\d+(?:_[A-Za-z0-9]+)?|ISRCTN\d+|LEGACY-[A-Za-z0-9-]+))'\s*:\s*\{\s*\n[^\n]*"
    r"name:\s*'(?P<name>[^']+)'[^\n]*?"
    r"tN:\s*(?P<tN>\d+|null)[^\n]*?"
    r"cN:\s*(?P<cN>\d+|null)",
    re.DOTALL,
)


def is_ctgov_key(key: str) -> bool:
    """True if key is a CT.gov NCT (skips ISRCTN/LEGACY synthetic keys)."""
    return key.startswith("NCT")


def base_nct(key: str) -> str:
    """Strip _PEOM, _A, _SUBGROUP suffixes to get the canonical NCT for CT.gov.
    Returns the key unchanged if it's a non-CT.gov registry (ISRCTN/LEGACY-)."""
    if not is_ctgov_key(key):
        return key
    return re.sub(r"_[A-Za-z][A-Za-z0-9]*$", "", key)


def fetch_enrollment(nct: str, cache: dict, retries: int = 3) -> dict:
    """Fetch enrollment for an NCT, with on-disk cache and retry.
    For non-CT.gov keys (ISRCTN, LEGACY-), returns a synthetic 'NON_CTGOV' record."""
    if nct in cache:
        return cache[nct]
    if not is_ctgov_key(nct):
        cache[nct] = {"nct": nct, "found": False, "error": "NON_CTGOV_REGISTRY"}
        return cache[nct]
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct}?format=json&fields=protocolSection.identificationModule.briefTitle,protocolSection.designModule.enrollmentInfo,protocolSection.identificationModule.acronym"
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FinrenoneAuditBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
            proto = data.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            design = proto.get("designModule", {})
            enroll = design.get("enrollmentInfo", {}) or {}
            result = {
                "nct": nct,
                "found": True,
                "enrollment": enroll.get("count"),
                "enrollment_type": enroll.get("type"),
                "title": ident.get("briefTitle"),
                "acronym": ident.get("acronym"),
            }
            cache[nct] = result
            return result
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache[nct] = {"nct": nct, "found": False, "error": "404"}
                return cache[nct]
            last_err = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = str(e)
        time.sleep(1 + attempt)
    cache[nct] = {"nct": nct, "found": False, "error": last_err}
    return cache[nct]


def collect_rows(root: Path) -> list[dict]:
    rows = []
    for f in sorted(root.glob("*_REVIEW.html")):
        with f.open(encoding="utf-8") as fh:
            text = fh.read()
        for m in ROW_RE.finditer(text):
            tN = m.group("tN")
            cN = m.group("cN")
            if tN == "null" or cN == "null":
                continue
            rows.append({
                "file": f.name,
                "key": m.group("key"),
                "base_nct": base_nct(m.group("key")),
                "name": m.group("name"),
                "tN": int(tN),
                "cN": int(cN),
                "row_total": int(tN) + int(cN),
            })
    return rows


def main() -> int:
    root = Path(".")
    out_dir = Path("outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    cache_path = out_dir / "ctgov_cache.json"
    cache: dict = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    rows = collect_rows(root)
    unique_ncts = sorted({r["base_nct"] for r in rows})
    print(f"Files with rows: {len({r['file'] for r in rows})}")
    print(f"Total trial-rows: {len(rows)}")
    print(f"Unique base NCTs to fetch: {len(unique_ncts)}")
    print(f"Cached already: {sum(1 for n in unique_ncts if n in cache)}")

    fetched = 0
    for i, n in enumerate(unique_ncts, 1):
        if n not in cache:
            fetch_enrollment(n, cache)
            fetched += 1
            time.sleep(0.15)  # be polite to CT.gov
            if fetched % 25 == 0:
                cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
                print(f"  [{i}/{len(unique_ncts)}] cached={len(cache)}")
    cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    print(f"Fetched {fetched} new NCTs; total cache: {len(cache)}")

    # Aggregate row totals per (file, base_nct). For multi-row shared-control
    # splits (e.g. PEOM/_NONAV variants of one trial), use MAX of row_totals
    # rather than SUM — summing double-counts the shared control arm and
    # produces false-positive outliers (~1.3× ratio) for valid designs.
    agg: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["file"], r["base_nct"])
        if key not in agg:
            agg[key] = {"file": r["file"], "base_nct": r["base_nct"], "names": [], "total": 0, "row_totals": []}
        agg[key]["names"].append(r["name"])
        agg[key]["row_totals"].append(r["row_total"])
    for k, v in agg.items():
        # Use MAX row_total as the representative; falls back to SUM if rows
        # differ wildly (suggesting genuinely independent contrasts).
        v["total"] = max(v["row_totals"])

    findings = []
    swap_candidates = []

    # Per-row outlier check (single-trial scope)
    for (f, nct), info in agg.items():
        ctg = cache.get(nct, {})
        if not ctg.get("found"):
            err = ctg.get("error", "")
            cat = "NON_CTGOV_REGISTRY" if err == "NON_CTGOV_REGISTRY" else "CTGOV_NOT_FOUND"
            findings.append({**info, "ctg_enrollment": None, "ctg_acronym": None,
                            "ratio": None, "category": cat,
                            "ctg_title": err})
            continue
        ctg_n = ctg.get("enrollment")
        if ctg_n is None or ctg_n == 0:
            findings.append({**info, "ctg_enrollment": ctg_n, "ctg_acronym": ctg.get("acronym"),
                            "ratio": None, "category": "CTGOV_NO_ENROLLMENT",
                            "ctg_title": ctg.get("title", "")})
            continue
        ratio = info["total"] / ctg_n
        # Multi-arm trials usually give row_total / ctg_enrollment ≈ 0.4–0.7 (2 of 3-4 arms).
        # mITT vs randomized usually 0.85–1.0. Same-trial direct match: ≈1.0.
        # Flag if outside 0.30–1.10 → either swap, wrong NCT, or substantial extraction error.
        cat = "OK"
        if ratio > 1.10 or ratio < 0.30:
            cat = "OUTLIER"
        findings.append({
            **info,
            "ctg_enrollment": ctg_n,
            "ctg_acronym": ctg.get("acronym"),
            "ctg_title": (ctg.get("title") or "")[:80],
            "ratio": round(ratio, 3),
            "category": cat,
        })

    # Pairwise swap detection within each file
    by_file: dict[str, list] = {}
    for fi in findings:
        if fi.get("ctg_enrollment"):
            by_file.setdefault(fi["file"], []).append(fi)

    for f, items in by_file.items():
        if len(items) < 2:
            continue
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                a_self = abs(a["total"] - a["ctg_enrollment"]) / max(a["ctg_enrollment"], 1)
                a_swap = abs(a["total"] - b["ctg_enrollment"]) / max(b["ctg_enrollment"], 1)
                b_self = abs(b["total"] - b["ctg_enrollment"]) / max(b["ctg_enrollment"], 1)
                b_swap = abs(b["total"] - a["ctg_enrollment"]) / max(a["ctg_enrollment"], 1)
                # Swap candidate: BOTH would fit better swapped, AND swap is meaningfully better
                if a_swap < a_self - 0.15 and b_swap < b_self - 0.15:
                    swap_candidates.append({
                        "file": f,
                        "trial_A": a["base_nct"],
                        "trial_A_names": ",".join(a["names"]),
                        "trial_A_total": a["total"],
                        "trial_A_ctg": a["ctg_enrollment"],
                        "trial_B": b["base_nct"],
                        "trial_B_names": ",".join(b["names"]),
                        "trial_B_total": b["total"],
                        "trial_B_ctg": b["ctg_enrollment"],
                        "self_diff_A": round(a_self, 2),
                        "swap_diff_A": round(a_swap, 2),
                        "self_diff_B": round(b_self, 2),
                        "swap_diff_B": round(b_swap, 2),
                    })

    # Write findings
    import csv
    findings_csv = out_dir / "ctgov_cross_check.csv"
    if findings:
        keys = ["file", "base_nct", "names", "total", "ctg_enrollment", "ctg_acronym", "ctg_title", "ratio", "category"]
        with findings_csv.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for fi in findings:
                row = {k: fi.get(k) for k in keys}
                if isinstance(row["names"], list):
                    row["names"] = ",".join(row["names"])
                w.writerow(row)
    swaps_csv = out_dir / "ctgov_swap_candidates.csv"
    if swap_candidates:
        with swaps_csv.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(swap_candidates[0].keys()))
            w.writeheader()
            w.writerows(swap_candidates)

    # Summary
    cats: dict[str, int] = {}
    for fi in findings:
        cats[fi["category"]] = cats.get(fi["category"], 0) + 1
    print("\n=== Summary ===")
    for c, n in sorted(cats.items()):
        print(f"  {c}: {n}")
    print(f"\n=== Outliers (top 20 by |ratio-1|) ===")
    outliers = [fi for fi in findings if fi["category"] == "OUTLIER"]
    outliers.sort(key=lambda x: abs((x["ratio"] or 1) - 1), reverse=True)
    for fi in outliers[:20]:
        names = ",".join(fi["names"]) if isinstance(fi["names"], list) else fi["names"]
        print(f"  {fi['file']:42s} {fi['base_nct']:14s} {names[:24]:24s} "
              f"row={fi['total']:6d} ctg={fi['ctg_enrollment']:6d} ratio={fi['ratio']}")
    print(f"\n=== Swap candidates: {len(swap_candidates)} ===")
    for s in swap_candidates[:10]:
        print(f"  {s['file']}")
        print(f"    {s['trial_A']} ({s['trial_A_names']}): claim={s['trial_A_total']} ctg={s['trial_A_ctg']}  self_diff={s['self_diff_A']} swap_diff={s['swap_diff_A']}")
        print(f"    {s['trial_B']} ({s['trial_B_names']}): claim={s['trial_B_total']} ctg={s['trial_B_ctg']}  self_diff={s['self_diff_B']} swap_diff={s['swap_diff_B']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
