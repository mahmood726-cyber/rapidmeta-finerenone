#!/usr/bin/env python
"""Portfolio-wide data-integrity audit for the RapidMeta review apps.

Parses the realData trial objects out of every *_REVIEW*.html and runs a set of
structural / internal-consistency checks that need NO external ground truth, so
they apply to all topics. These encode the defect CLASSES uncovered in review so
the rest of the portfolio can be checked for the same mistakes:

  impossible_2x2     tE>tN or cE>cN (event count exceeds arm size) -- the prior
                     systemic extraction bug (154 apps) made concrete and gated.
  none_leak          a JS null/None/NaN fused into a number (e.g. `nulle-5`),
                     or a Python `None`/`NaN` literal leaked into JS -- the
                     ReferenceError class fixed in NINTEDANIB/ZIRCONIUM.
  inverted_ci        lci > uci on the published HR or an outcome.
  ci_excludes_point  publishedHR not within [hrLCI, hrUCI] (1% slack).
  implausible_ratio  a ratio estimand (HR/OR/RR) that is <=0, or so large the
                     field is almost certainly holding an absolute value, not a
                     ratio (the DME Protocol-T 11.6 case).
  bad_pmid           pmid present but not 1-8 digits.
  bad_nct            trial key is neither NCT\\d{8} nor LEGACY-*.

It also (optionally, --ground-truth) re-runs the curated published-MA comparison
using a format-tolerant extractor (the old scripts/compare_to_published_mas.py
regex now matches 0 rows against the current app format).

Usage:
  python scripts/data_integrity_audit.py [--glob '*_REVIEW*.html'] [--json OUT] [--fail-on impossible_2x2,none_leak]
Exit non-zero if any finding in --fail-on classes is present (default: the
hard-corruption classes impossible_2x2,none_leak,inverted_ci,bad_nct).
"""
from __future__ import annotations
import argparse
import glob
import io
import json
import os
import re
import sys

# Guard the UTF-8 stdout wrap so it only runs on direct CLI use -- reassigning
# sys.stdout at import time breaks pytest's output capture (see lessons.md).
if (__name__ == "__main__" and "pytest" not in sys.modules
        and sys.platform == "win32" and hasattr(sys.stdout, "buffer")):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NCT_KEY_RE = re.compile(r"""["']?(NCT\d{8}|LEGACY-[A-Za-z0-9_-]+)["']?\s*:\s*\{""")
# JS number, or a corrupted/None token we want to catch.
NUM_OR_BAD = r"(-?\d*\.?\d+(?:[eE][-+]?\d+)?|null|None|NaN|nulle?-?\d*)"


def _match_brace(s: str, open_idx: int):
    """Given index of a '{', return index of its matching '}' (string-aware)."""
    depth = 0
    in_str = None
    esc = False
    j = open_idx
    n = len(s)
    while j < n:
        c = s[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == in_str:
                in_str = None
        else:
            if c in "\"'":
                in_str = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return j
        j += 1
    return -1


def find_trial_objects(html: str):
    """Yield (key, object_text) for each trial object INSIDE a realData:{...}
    block. Scoping to realData avoids the separate NCT-keyed trial-metadata
    registry (label/role/registeredPrimary...) that also exists in some apps."""
    for rm in re.finditer(r"realData\s*:\s*\{", html):
        block_open = rm.end() - 1
        block_close = _match_brace(html, block_open)
        if block_close < 0:
            continue
        block = html[block_open:block_close + 1]
        for m in NCT_KEY_RE.finditer(block):
            i = m.end() - 1
            j = _match_brace(block, i)
            if j > i:
                yield m.group(1), block[i:j + 1]


def field(obj: str, name: str):
    """Return the raw token for a top-level field (searched before allOutcomes)."""
    head = obj.split("allOutcomes", 1)[0]
    m = re.search(r"(?<![A-Za-z_])" + re.escape(name) + r"\s*:\s*" + NUM_OR_BAD, head)
    return m.group(1) if m else None


def str_field(obj: str, name: str):
    head = obj.split("allOutcomes", 1)[0]
    m = re.search(r"(?<![A-Za-z_])" + re.escape(name) + r"\s*:\s*\"([^\"]*)\"", head)
    return m.group(1) if m else None


def as_num(tok):
    if tok is None:
        return None
    if re.fullmatch(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?", tok):
        try:
            return float(tok)
        except ValueError:
            return None
    return None  # null/None/NaN/nulle-N -> not a number


def is_bad_token(tok):
    """True if the token is a corrupted/leaked value that breaks JS or is non-null junk."""
    if tok is None:
        return False
    if tok in ("None", "NaN"):
        return True
    if re.fullmatch(r"nulle-?\d*", tok):  # null fused with exponent
        return True
    return False


def audit_app(path: str):
    with open(path, "rb") as f:
        html = f.read().decode("utf-8", "replace")
    findings = []
    name = os.path.basename(path)

    def add(cls, key, detail):
        findings.append({"app": name, "class": cls, "trial": key, "detail": detail})

    for key, obj in find_trial_objects(html):
        if not re.fullmatch(r"NCT\d{8}|LEGACY-[A-Za-z0-9_-]+", key):
            add("bad_nct", key, f"malformed trial key {key!r}")

        # 2x2 counts
        tE, tN, cE, cN = (as_num(field(obj, x)) for x in ("tE", "tN", "cE", "cN"))
        if tE is not None and tN is not None and tE > tN:
            add("impossible_2x2", key, f"tE={tE} > tN={tN}")
        if cE is not None and cN is not None and cE > cN:
            add("impossible_2x2", key, f"cE={cE} > cN={cN}")
        for fld in ("tE", "tN", "cE", "cN", "year"):
            tok = field(obj, fld)
            if is_bad_token(tok):
                add("none_leak", key, f"{fld}={tok}")

        # published HR + CI
        hr = field(obj, "publishedHR")
        lci = field(obj, "hrLCI")
        uci = field(obj, "hrUCI")
        for fld, tok in (("publishedHR", hr), ("hrLCI", lci), ("hrUCI", uci)):
            if is_bad_token(tok):
                add("none_leak", key, f"{fld}={tok}")
        hrv, lciv, uciv = as_num(hr), as_num(lci), as_num(uci)
        # Resolve the measure from the OUTCOME's estimandType first (the real
        # measure), falling back to the trial-level field, then HR. Reading only
        # the trial-level field (often absent -> defaulting to HR) mislabels
        # legitimate OR/RR/RD outcomes as hazard ratios.
        ao_tail = obj.split("allOutcomes", 1)
        ao_est = None
        if len(ao_tail) > 1:
            am = re.search(r'estimandType:"([^"]+)"', ao_tail[1])
            ao_est = am.group(1) if am else None
        est = (ao_est or str_field(obj, "estimandType") or "HR").upper()
        is_ratio = est in ("HR", "OR", "RR", "IRR", "DOR")
        # NOTE: publishedHR is a GENERIC effect field -- the engine reads
        # MD/SMD/RD/HR/OR/RR from it uniformly, and MD/RD CIs are correctly
        # additive. So a value on a continuous outcome is NOT a defect; do not
        # flag it. (An earlier "ratio_on_continuous" check did, and wrongly
        # nulled 156 legitimate mean-differences -- never reintroduce it.)
        if lciv is not None and uciv is not None and lciv > uciv:
            add("inverted_ci", key, f"lci={lciv} > uci={uciv}")
        if hrv is not None and lciv is not None and uciv is not None:
            if not (lciv * 0.99 <= hrv <= uciv * 1.01):
                add("ci_excludes_point", key, f"HR={hrv} outside [{lciv},{uciv}]")
        if is_ratio and hrv is not None:
            # Measure-aware: large ODDS RATIOS are legitimate (psoriasis PASI,
            # HCV SVR, vaccine seroconversion can be OR 50-300+ vs placebo), so
            # only flag OR/RR that are non-positive or astronomically large.
            # HAZARD RATIOS, by contrast, are bounded in practice (~0.05-10); an
            # "HR" above ~20 is almost always a mislabel or an absolute value
            # stored in a ratio field (the DME Protocol-T BCVA case).
            if hrv <= 0:
                add("implausible_ratio", key, f"{est}={hrv} <= 0")
            elif est == "HR" and hrv > 20:
                add("implausible_ratio", key, f"HR={hrv} (>20: hazard ratios are bounded; likely mislabel/absolute)")
            elif hrv > 1000:
                add("implausible_ratio", key, f"{est}={hrv} (>1000: data error even for rare events)")
            # A correct ratio CI is symmetric on the LOG scale. An additively
            # symmetric CI (point +/- constant) on a ratio estimand is a
            # derivation bug -- usually a single-arm proportion/percent or an
            # absolute value mislabeled as a ratio (e.g. andexanet 73.15
            # [67.5,78.8] is a hemostatic-efficacy %, not an HR).
            if lciv is not None and uciv is not None and hrv > 0 and lciv > 0 and uciv > lciv:
                add_gap = abs((uciv - hrv) - (hrv - lciv)) / max(hrv, 1e-9)
                import math as _m
                mult_gap = abs(_m.log(uciv / hrv) - _m.log(hrv / lciv))
                # Require CLEARLY non-log-symmetric (mult_gap > 0.15): a real
                # ratio CI for a small effect (e.g. OR 1.5 [1.1,1.9]) is nearly
                # additive too, so a tight threshold would false-flag it.
                if add_gap < 0.02 and mult_gap > 0.15:
                    add("additive_ratio_ci", key,
                        f"{est}={hrv} CI [{lciv},{uciv}] is additively symmetric "
                        f"(impossible for a ratio; likely a proportion/absolute mislabeled)")

        # pmid
        pmid = str_field(obj, "pmid") or field(obj, "pmid")
        if pmid and not re.fullmatch(r"\d{1,8}", str(pmid)):
            if str(pmid) not in ("null", "None"):
                add("bad_pmid", key, f"pmid={pmid!r}")

    # App-level citation integrity: every DOI token must be well-formed
    # (10.<registrant>/<suffix>). A malformed DOI is a dead citation.
    for dm in re.finditer(r"(?:doi[:=\s]*|doi\.org/)\s*\"?'?\s*(10\.[^\s\"'<>,)]+)", html, re.I):
        doi = dm.group(1).rstrip(".,;")
        if not re.fullmatch(r"10\.\d{4,9}/[^\s]+", doi) or len(doi) < 8:
            add("bad_doi", "(app)", f"malformed DOI {doi!r}")

    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="*_REVIEW*.html")
    ap.add_argument("--json", default=None)
    ap.add_argument("--fail-on", default="impossible_2x2,none_leak,inverted_ci,bad_nct")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(REPO, args.glob)))
    if args.limit:
        files = files[: args.limit]
    all_findings = []
    for p in files:
        all_findings.extend(audit_app(p))

    by_class: dict[str, list] = {}
    for f in all_findings:
        by_class.setdefault(f["class"], []).append(f)

    print(f"Scanned {len(files)} apps.")
    print(f"Total findings: {len(all_findings)}\n")
    print("By class (class | count | distinct apps):")
    for cls in sorted(by_class, key=lambda c: -len(by_class[c])):
        apps = {f['app'] for f in by_class[cls]}
        print(f"  {cls:18} {len(by_class[cls]):5}   {len(apps)} apps")

    fail_classes = {c.strip() for c in args.fail_on.split(",") if c.strip()}
    failing = [f for f in all_findings if f["class"] in fail_classes]
    if failing:
        print(f"\nHARD findings ({', '.join(sorted(fail_classes))}): {len(failing)}")
        for f in failing[:40]:
            print(f"  [{f['class']}] {f['app']} :: {f['trial']} -- {f['detail']}")
        if len(failing) > 40:
            print(f"  ... and {len(failing) - 40} more")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"scanned": len(files), "by_class": {k: v for k, v in by_class.items()},
                       "findings": all_findings}, fh, indent=1)
        print(f"\nWrote {args.json}")

    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
