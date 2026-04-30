"""
Portfolio audit: mITT vs allocated denominators.

Scans every *_REVIEW.html dashboard in C:\\Projects\\Finrenone\\ for trial entries
with binary event counts (tE, tN, cE, cN). Emits a CSV the user can spot-check
to decide whether tN/cN match the published primary analysis (mITT) or were
inadvertently filled with randomized-allocation counts.

Heuristic flags (NOT verdicts -- prompts for human review):
  * ROUND_HUNDRED_TN : tN ends in 00 (often a planned target, not actual mITT)
  * ROUND_HUNDRED_CN : cN ends in 00
  * EQUAL_ARMS       : tN == cN, both >=50 (1:1 designs usually have small
                       post-rand attrition; identical mITT counts deserve
                       a check)
  * BIG_TRIAL        : tN+cN >= 1000 (high-impact; small denominator error
                       moves pooled estimates noticeably)
  * MITT_MENTIONED   : group/snippet text already says ITT/mITT/modified
  * MULTI_ARM_POOL   : group mentions pooled/combined sham/placebo arms
                       (mITT pooling decision present; verify cN sums match)

The script does NOT call out to PubMed/CT.gov. Verification is manual.

Usage:
  python scripts/audit_mitt_vs_allocated.py
  python scripts/audit_mitt_vs_allocated.py --csv outputs/mitt_audit.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Projects\Finrenone")
DEFAULT_CSV = ROOT / "outputs" / "mitt_audit.csv"

NAME_RE    = re.compile(r"\bname:\s*'([^']+)'")
PMID_RE    = re.compile(r"\bpmid:\s*'([^']*)'")
PHASE_RE   = re.compile(r"\bphase:\s*'([^']*)'")
YEAR_RE    = re.compile(r"\byear:\s*(\d+)")
TE_RE      = re.compile(r"\btE:\s*(null|\d+)")
TN_RE      = re.compile(r"\btN:\s*(null|\d+)")
CE_RE      = re.compile(r"\bcE:\s*(null|\d+)")
CN_RE      = re.compile(r"\bcN:\s*(null|\d+)")
GROUP_RE   = re.compile(r"\bgroup:\s*'((?:[^'\\]|\\.)*)'")
SNIPPET_RE = re.compile(r"\bsnippet:\s*'((?:[^'\\]|\\.)*)'")

NCT_PAIR_RE = re.compile(r"'(NCT\d{8})'\s*:\s*'([^']+)'")


def parse_int(token: str | None) -> int | None:
    if token is None or token == "null":
        return None
    try:
        return int(token)
    except ValueError:
        return None


def grab(rx: re.Pattern, line: str) -> str | None:
    m = rx.search(line)
    return m.group(1) if m else None


def build_nct_map(text: str) -> dict[str, str]:
    """Map trial display name -> NCT id from any nctAcronyms-like dictionary."""
    mapping: dict[str, str] = {}
    for m in NCT_PAIR_RE.finditer(text):
        nct, name = m.group(1), m.group(2)
        # First occurrence wins (later overrides ignored).
        mapping.setdefault(name, nct)
    return mapping


def line_is_trial_entry(line: str) -> bool:
    return (
        ("name:" in line)
        and ("tE:" in line)
        and ("tN:" in line)
        and ("cE:" in line)
        and ("cN:" in line)
    )


def compute_flags(tN: int | None, cN: int | None, group: str, snippet: str) -> list[str]:
    flags: list[str] = []
    if tN is not None and tN > 0 and tN % 100 == 0:
        flags.append("ROUND_HUNDRED_TN")
    if cN is not None and cN > 0 and cN % 100 == 0:
        flags.append("ROUND_HUNDRED_CN")
    if tN is not None and cN is not None and tN == cN and tN >= 50:
        flags.append("EQUAL_ARMS")
    if tN is not None and cN is not None and (tN + cN) >= 1000:
        flags.append("BIG_TRIAL")
    blob = f"{group} {snippet}".lower()
    if any(tok in blob for tok in (" itt", "intent-to-treat", "intent to treat",
                                   "mitt", "modified-itt", "modified itt",
                                   "modified intent")):
        flags.append("MITT_MENTIONED")
    if any(tok in blob for tok in ("combined sham", "pooled sham", "pooled placebo",
                                   "vs combined", "all comparator", "combined control")):
        flags.append("MULTI_ARM_POOL")
    return flags


def scan_dashboard(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    nct_map = build_nct_map(text)
    rows: list[dict] = []
    for line in text.splitlines():
        if not line_is_trial_entry(line):
            continue
        tE = parse_int(grab(TE_RE, line))
        tN = parse_int(grab(TN_RE, line))
        cE = parse_int(grab(CE_RE, line))
        cN = parse_int(grab(CN_RE, line))
        # Only audit BINARY trials (those with at least one event count).
        if tE is None and cE is None:
            continue
        if tN is None and cN is None:
            continue
        name = grab(NAME_RE, line) or ""
        nct = nct_map.get(name, "")
        group = grab(GROUP_RE, line) or ""
        snippet = grab(SNIPPET_RE, line) or ""
        flags = compute_flags(tN, cN, group, snippet)
        rows.append({
            "dashboard": path.name,
            "trial_name": name,
            "nct": nct,
            "phase": grab(PHASE_RE, line) or "",
            "year": grab(YEAR_RE, line) or "",
            "tE": "" if tE is None else tE,
            "tN": "" if tN is None else tN,
            "cE": "" if cE is None else cE,
            "cN": "" if cN is None else cN,
            "flags": ";".join(flags),
            "group": group[:300],
            "snippet": snippet[:300],
            "pmid": grab(PMID_RE, line) or "",
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit binary tN/cN denominators against mITT convention")
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Output CSV path")
    ap.add_argument("--root", type=Path, default=ROOT, help="Dashboard root")
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    dashboards = sorted(p for p in args.root.glob("*_REVIEW.html") if p.is_file())
    print(f"Scanning {len(dashboards)} dashboards under {args.root}")

    all_rows: list[dict] = []
    for p in dashboards:
        rows = scan_dashboard(p)
        all_rows.extend(rows)

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dashboard", "trial_name", "nct", "pmid", "phase", "year",
              "tE", "tN", "cE", "cN", "flags", "group", "snippet"]
    with args.csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)

    flagged = [r for r in all_rows if r["flags"]]
    big = [r for r in all_rows if "BIG_TRIAL" in r["flags"]]
    rh_t = [r for r in all_rows if "ROUND_HUNDRED_TN" in r["flags"]]
    rh_c = [r for r in all_rows if "ROUND_HUNDRED_CN" in r["flags"]]
    eq = [r for r in all_rows if "EQUAL_ARMS" in r["flags"]]
    mp = [r for r in all_rows if "MULTI_ARM_POOL" in r["flags"]]
    mi = [r for r in all_rows if "MITT_MENTIONED" in r["flags"]]

    print(f"Total binary trials audited:    {len(all_rows)}")
    print(f"  with at least one flag:       {len(flagged)}")
    print(f"  BIG_TRIAL (n>=1000):          {len(big)}")
    print(f"  ROUND_HUNDRED_TN:             {len(rh_t)}")
    print(f"  ROUND_HUNDRED_CN:             {len(rh_c)}")
    print(f"  EQUAL_ARMS (tN==cN, >=50):    {len(eq)}")
    print(f"  MULTI_ARM_POOL:               {len(mp)}")
    print(f"  MITT_MENTIONED (already):     {len(mi)}")
    print(f"CSV written: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
