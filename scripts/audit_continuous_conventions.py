"""
Portfolio audit: continuous outcome conventions.

Companion to scripts/audit_mitt_vs_allocated.py. Walks every dashboard,
extracts continuous trial entries (allOutcomes with type:'CONTINUOUS'),
and flags rows whose tN/cN/md/se combination warrants a human spot-check
against the published primary analysis.

Concerns this audit surfaces (heuristics, not verdicts):

* LSMD_NOT_DECLARED   -- title/snippet/group does not mention LSMD,
                         least-squares mean, ANCOVA, or MMRM. Risk:
                         dashboard's `md` may be raw arithmetic mean
                         difference even though the trial's primary was
                         model-based.
* MMRM_NOT_DECLARED   -- similar but specific to repeated-measures
                         designs (longitudinal / change-from-baseline).
* COMPLETER_RISK      -- tN/cN looks like completer-only counts (asym-
                         metric arms, or tN+cN noticeably below the
                         randomized total in the narrative).
* ROUND_HUNDRED_TN/CN -- denominator ends in 00 (often a planned
                         target).
* EQUAL_ARMS          -- tN==cN with both >=50 (possible mITT, possible
                         allocated, requires check).
* BIG_TRIAL           -- tN+cN >= 1000.
* SE_IMPLAUSIBLE_SMALL -- |se/md| < 0.05 (very tight; usually fine if
                         the trial is large but worth a sanity check
                         for scale or unit mistakes).
* SE_IMPLAUSIBLE_LARGE -- |se/md| > 1.0 (CI crosses zero; pooled sign
                         is fragile -- not a bug, but worth surfacing).
* SIGN_MISMATCH       -- title says "negative favours treatment" but md
                         is positive (or vice versa).

Usage:
  python scripts/audit_continuous_conventions.py
  python scripts/audit_continuous_conventions.py --csv outputs/continuous_audit.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Projects\Finrenone")
DEFAULT_CSV = ROOT / "outputs" / "continuous_audit.csv"

NAME_RE    = re.compile(r"\bname:\s*'([^']+)'")
PMID_RE    = re.compile(r"\bpmid:\s*'([^']*)'")
PHASE_RE   = re.compile(r"\bphase:\s*'([^']*)'")
YEAR_RE    = re.compile(r"\byear:\s*(\d+)")
TN_RE      = re.compile(r"\btN:\s*(null|\d+)")
CN_RE      = re.compile(r"\bcN:\s*(null|\d+)")
GROUP_RE   = re.compile(r"\bgroup:\s*'((?:[^'\\]|\\.)*)'")
SNIPPET_RE = re.compile(r"\bsnippet:\s*'((?:[^'\\]|\\.)*)'")

NCT_PAIR_RE = re.compile(r"'(NCT\d{8})'\s*:\s*'([^']+)'")

# A CONTINUOUS allOutcome line. We require type:'CONTINUOUS' and at least
# `md:` numeric. SE is optional (some entries derive SE from mean+sd).
CONT_OUTCOME_RE = re.compile(
    r"\{[^{}]*\btype:\s*'CONTINUOUS'[^{}]*\}",
    re.DOTALL,
)
MD_RE     = re.compile(r"\bmd:\s*(-?\d+(?:\.\d+)?)")
SE_RE     = re.compile(r"\bse:\s*(\d+(?:\.\d+)?)")
TITLE_RE  = re.compile(r"\btitle:\s*'((?:[^'\\]|\\.)*)'")
SHORT_RE  = re.compile(r"\bshortLabel:\s*'([^']*)'")


def parse_int(token: str | None) -> int | None:
    if token is None or token == "null":
        return None
    try:
        return int(token)
    except ValueError:
        return None


def parse_float(token: str | None) -> float | None:
    if token is None:
        return None
    try:
        return float(token)
    except ValueError:
        return None


def grab(rx: re.Pattern, text: str) -> str | None:
    m = rx.search(text)
    return m.group(1) if m else None


def build_nct_map(text: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for m in NCT_PAIR_RE.finditer(text):
        nct, name = m.group(1), m.group(2)
        mapping.setdefault(name, nct)
    return mapping


def find_trial_blocks(text: str) -> list[tuple[int, int, str]]:
    """Return (start, end, block_text) for every top-level trial entry.

    Anchors on `name: '...', pmid:` to find each `real_data_entries[i]`
    object literal. We need the full block (which contains both the
    header tN/cN line and the inner allOutcomes array) so we can pair
    a CONTINUOUS outcome with its trial-level fields.
    """
    blocks: list[tuple[int, int, str]] = []
    for m in re.finditer(r"\bname:\s*'[^']+'\s*,\s*pmid:", text):
        idx = m.start()
        # Walk backward to opening brace.
        depth = 0
        start = None
        for i in range(idx, -1, -1):
            ch = text[i]
            if ch == '}':
                depth += 1
            elif ch == '{':
                if depth == 0:
                    start = i
                    break
                depth -= 1
        if start is None:
            continue
        depth = 0
        end = None
        for j in range(start, len(text)):
            ch = text[j]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        if end is None:
            continue
        blocks.append((start, end, text[start:end]))
    # Deduplicate.
    seen: set[tuple[int, int]] = set()
    unique: list[tuple[int, int, str]] = []
    for s, e, b in blocks:
        if (s, e) in seen:
            continue
        seen.add((s, e))
        unique.append((s, e, b))
    return unique


def find_continuous_outcomes(block: str) -> list[str]:
    """Return CONTINUOUS allOutcome object literals inside one trial block."""
    return [m.group(0) for m in CONT_OUTCOME_RE.finditer(block)]


def declares_lsmd(blob: str) -> bool:
    blob_l = blob.lower()
    needles = (
        "lsmd", "least-squares mean", "least squares mean",
        "least-square mean", "ls mean", "ls-mean",
        "ancova", "ancova-adjusted",
    )
    return any(n in blob_l for n in needles)


def declares_mmrm(blob: str) -> bool:
    blob_l = blob.lower()
    needles = (
        "mmrm", "mixed model", "mixed-effect model",
        "repeated measures", "repeated-measures",
    )
    return any(n in blob_l for n in needles)


def compute_flags(*, tN: int | None, cN: int | None,
                  md: float | None, se: float | None,
                  title: str, group: str, snippet: str,
                  pico_out: str = "") -> list[str]:
    flags: list[str] = []
    # Per-outcome declaration sources: title, group (trial header), snippet.
    blob = f"{title} {group} {snippet}"
    # Dashboard-level declaration source: PICO `out` field. Treated as a
    # blanket declaration for every continuous outcome in that dashboard
    # (added portfolio-wide 2026-04-30 by scripts/add_lsmd_disclaimer.py).
    blob_pico = f"{blob} {pico_out}"

    # Denominator heuristics (same as binary audit).
    if tN is not None and tN > 0 and tN % 100 == 0:
        flags.append("ROUND_HUNDRED_TN")
    if cN is not None and cN > 0 and cN % 100 == 0:
        flags.append("ROUND_HUNDRED_CN")
    if tN is not None and cN is not None and tN == cN and tN >= 50:
        flags.append("EQUAL_ARMS")
    if tN is not None and cN is not None and (tN + cN) >= 1000:
        flags.append("BIG_TRIAL")

    # Asymmetric arm sizes -> possible completer-only convention
    # (1:1 designs with substantial differential dropout look like this).
    if tN is not None and cN is not None and tN > 0 and cN > 0:
        ratio = max(tN, cN) / min(tN, cN)
        if ratio >= 1.25:
            flags.append("ARM_ASYMMETRIC")

    # Analytic-method declaration. Only meaningful for primary-style
    # change-from-baseline outcomes; flag when omitted at BOTH the
    # per-outcome level and the dashboard-level PICO.
    is_change = any(tok in blob.lower() for tok in (
        "change", "from baseline", "difference from", "least", "mmrm", "ancova",
    ))
    if is_change and not declares_lsmd(blob_pico):
        flags.append("LSMD_NOT_DECLARED")
    if is_change and not declares_mmrm(blob_pico):
        flags.append("MMRM_NOT_DECLARED")

    # MITT_MENTIONED stays useful as a positive tag.
    blob_l = blob.lower()
    if any(tok in blob_l for tok in (" itt", "intent-to-treat", "intent to treat",
                                     "mitt", "modified-itt", "modified itt",
                                     "modified intent")):
        flags.append("MITT_MENTIONED")

    # SE plausibility checks.
    if md is not None and se is not None and md != 0:
        rel = abs(se / md)
        if rel < 0.05:
            flags.append("SE_IMPLAUSIBLE_SMALL")
        if rel > 1.0:
            flags.append("SE_IMPLAUSIBLE_LARGE")

    # Sign mismatch: "negative favours" but md > 0, or "positive favours"
    # but md < 0.
    if md is not None:
        bl = blob.lower()
        neg_favours = "negative favours" in bl or "negative favors" in bl or "lower is better" in bl
        pos_favours = "positive favours" in bl or "positive favors" in bl or "higher is better" in bl
        if neg_favours and md > 0:
            flags.append("SIGN_MISMATCH")
        if pos_favours and md < 0:
            flags.append("SIGN_MISMATCH")

    return flags


PICO_OUT_RE = re.compile(
    r"protocol:\s*\{\s*pop:\s*'(?:[^'\\]|\\.)*',\s*int:\s*'(?:[^'\\]|\\.)*',\s*comp:\s*'(?:[^'\\]|\\.)*',\s*out:\s*'((?:[^'\\]|\\.)*)'"
)


def scan_dashboard(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    nct_map = build_nct_map(text)
    pico_match = PICO_OUT_RE.search(text)
    pico_out = pico_match.group(1) if pico_match else ""
    rows: list[dict] = []
    for _, _, block in find_trial_blocks(text):
        # Trial header fields (pull from first line of the block).
        first_line = block.splitlines()[0] if block else ""
        # Some trial blocks are multi-line; combine the first ~3 lines for
        # header parsing.
        header = "\n".join(block.splitlines()[:5])
        tN = parse_int(grab(TN_RE, header))
        cN = parse_int(grab(CN_RE, header))
        name = grab(NAME_RE, header) or ""
        nct = nct_map.get(name, "")
        phase = grab(PHASE_RE, header) or ""
        year = grab(YEAR_RE, header) or ""
        group = grab(GROUP_RE, header) or ""
        snippet = grab(SNIPPET_RE, block) or ""

        outcomes = find_continuous_outcomes(block)
        if not outcomes:
            continue
        for outcome in outcomes:
            md = parse_float(grab(MD_RE, outcome))
            se = parse_float(grab(SE_RE, outcome))
            title = grab(TITLE_RE, outcome) or ""
            short = grab(SHORT_RE, outcome) or ""
            flags = compute_flags(
                tN=tN, cN=cN, md=md, se=se,
                title=title, group=group, snippet=snippet,
                pico_out=pico_out,
            )
            rows.append({
                "dashboard": path.name,
                "trial_name": name,
                "nct": nct,
                "pmid": grab(PMID_RE, header) or "",
                "phase": phase,
                "year": year,
                "outcome_short": short,
                "outcome_title": title[:140],
                "tN": "" if tN is None else tN,
                "cN": "" if cN is None else cN,
                "md": "" if md is None else md,
                "se": "" if se is None else se,
                "flags": ";".join(flags),
                "group": group[:200],
                "snippet": snippet[:200],
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit continuous outcome conventions")
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args()

    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    dashboards = sorted(p for p in args.root.glob("*_REVIEW.html") if p.is_file())
    print(f"Scanning {len(dashboards)} dashboards under {args.root}")

    all_rows: list[dict] = []
    for p in dashboards:
        all_rows.extend(scan_dashboard(p))

    args.csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dashboard", "trial_name", "nct", "pmid", "phase", "year",
              "outcome_short", "outcome_title", "tN", "cN", "md", "se",
              "flags", "group", "snippet"]
    with args.csv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)

    def n(tag: str) -> int:
        return sum(1 for r in all_rows if tag in r["flags"])

    print(f"Total continuous outcomes audited: {len(all_rows)}")
    print(f"  with at least one flag:          {sum(1 for r in all_rows if r['flags'])}")
    print(f"  LSMD_NOT_DECLARED:               {n('LSMD_NOT_DECLARED')}")
    print(f"  MMRM_NOT_DECLARED:               {n('MMRM_NOT_DECLARED')}")
    print(f"  ARM_ASYMMETRIC (>=1.25:1):       {n('ARM_ASYMMETRIC')}")
    print(f"  ROUND_HUNDRED_TN:                {n('ROUND_HUNDRED_TN')}")
    print(f"  ROUND_HUNDRED_CN:                {n('ROUND_HUNDRED_CN')}")
    print(f"  EQUAL_ARMS:                      {n('EQUAL_ARMS')}")
    print(f"  BIG_TRIAL:                       {n('BIG_TRIAL')}")
    print(f"  SE_IMPLAUSIBLE_SMALL:            {n('SE_IMPLAUSIBLE_SMALL')}")
    print(f"  SE_IMPLAUSIBLE_LARGE:            {n('SE_IMPLAUSIBLE_LARGE')}")
    print(f"  SIGN_MISMATCH:                   {n('SIGN_MISMATCH')}")
    print(f"  MITT_MENTIONED (already):        {n('MITT_MENTIONED')}")
    print(f"CSV written: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
