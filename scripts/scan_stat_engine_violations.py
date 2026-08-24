"""Scan curated REVIEW files (no AUTO suffix) for the 7 statistical-methodology
rule violations the user surfaced. Identifies the 18 dashboards that need a
back-port from the FINERENONE_REVIEW reference implementation.

Rules and signatures detected:
  R-REML-primary    : has `tau2_dl` but no `tau2_reml` reference
                      (engine still uses DL for sWR weights)
  R-Qprofile-tau2   : has `tau2` references but no `qProfileTau2CI` helper
                      OR helper exists but is never invoked
  R-qchisq-df1      : `qchisq` exists but the df===1 closed-form branch
                      is missing (saturates via Wilson-Hilferty at small df)
  R-PI-k-1          : PI computation uses `tQuantile(*, k - 2)` instead of
                      Cochrane v6.5 `k - 1`
  R-RoB-ME-wired    : has `ROB-ME` UI chip but no `robMe` / `RobMeEngine` JS
                      implementation
  R-MH-pool         : binary outcomes present but no Mantel-Haenszel pooling
                      block (`mh_or`, `mantelHaenszel`, etc.)
  R-REML-iteration  : has `tau2_reml` declared but no iteration block
                      (`tau2_reml + _delta`, fisher-scoring style)

Writes:
  outputs/stat_engine/violations.json
  outputs/stat_engine/violations.md
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "stat_engine"
OUT.mkdir(parents=True, exist_ok=True)


def has_substantive_engine(txt: str) -> bool:
    """Heuristic: the page has its own pooling engine if it has BOTH a
    `sWR` weighting loop (random-effects accumulator) AND a `qchisq` helper.
    Pages without one (e.g. utility pages, NMA-only pages with bespoke engines)
    are out of scope for this scan."""
    return ("sWR" in txt) and ("qchisq" in txt) and ("tQuantile" in txt)


def violations_in(txt: str) -> list[str]:
    out = []

    # R-REML-primary: must have tau2_reml AND must select it as primary
    has_dl = "tau2_dl" in txt
    has_reml = "tau2_reml" in txt
    # KEYED TO THE PROPERTY, NOT TO THE REFERENCE PAGE'S PUNCTUATION.
    #
    # Both alternatives below required a form the corpus does not write. The first wanted
    # PARENTHESES around the condition -- `const tau2 = (k>=2) ? ...` -- and every one of
    # 745 pages writes `const tau2=k>=2?tau2_reml:tau2_dl` with no parentheses at all. The
    # second wanted `tau2 = tau2_reml` directly adjacent, which a ternary never produces.
    #
    # So `selects_reml` computed False on 745 pages that select REML CORRECTLY, and the
    # branch below then flagged every one of them. THE PUBLISHED ARTEFACT SAYS "Violating:
    # 301" AND ACCUSES ALL 301 OF THIS RULE, WRONGLY. An audit that cries wolf at 301 pages
    # gets switched off, and is then worth nothing on the day it is right.
    #
    # The property is "the ternary selects tau2_reml over tau2_dl", however it is spaced.
    selects_reml = bool(
        re.search(r"tau2\s*=\s*[^;]{0,80}\?\s*tau2_reml\s*:\s*tau2_dl", txt)
        or re.search(r"tau2\s*=\s*tau2_reml\b", txt)
    )
    if has_dl and not has_reml:
        out.append("R-REML-primary")
    elif has_dl and has_reml and not selects_reml:
        out.append("R-REML-primary")

    # R-Qprofile-tau2: helper missing OR never invoked
    has_qp_helper = "qProfileTau2CI" in txt
    has_qp_invocation = bool(re.search(r"qProfileTau2CI\s*\(", txt))
    invocations = len(re.findall(r"qProfileTau2CI\s*\(", txt))
    if not has_qp_helper:
        out.append("R-Qprofile-tau2")
    elif invocations < 2:  # def + at least one call
        out.append("R-Qprofile-tau2")

    # R-qchisq-df1: qchisq function exists; check whether the df === 1 branch exists
    if "qchisq" in txt:
        # Look for `df === 1` (closed-form) inside qchisq def
        m = re.search(r"const\s+qchisq\s*=\s*\([^)]*\)\s*=>\s*\{([\s\S]*?)\};", txt)
        if not m:
            m = re.search(r"function\s+qchisq\s*\([^)]*\)\s*\{([\s\S]*?)\}", txt)
        if m:
            body = m.group(1)
            if "df === 1" not in body and "df==1" not in body and "df ==1" not in body:
                out.append("R-qchisq-df1")
        # else: can't locate; assume violation
        elif not re.search(r"qchisq\s*=.*df\s*===?\s*1", txt):
            out.append("R-qchisq-df1")

    # R-PI-k-1: any PI compute with `k - 2` in the df slot
    if re.search(r"tQuantile\s*\([^,]+,\s*k\s*-\s*2\s*\)", txt) and "prediction" in txt.lower():
        # Confirm it's the PI t-critical (not some other tQuantile use)
        if re.search(r"tCritPI\s*=\s*tQuantile\([^,]+,\s*k\s*-\s*2\s*\)", txt) \
                or re.search(r"piSE[\s\S]{0,200}tQuantile\([^,]+,\s*k\s*-\s*2", txt):
            out.append("R-PI-k-1")

    # R-RoB-ME-wired: has chip-robme but no robMe / RobMeEngine implementation
    if "ROB-ME" in txt or "chip-robme" in txt:
        if not re.search(r"\bRobMe\b|robMe[A-Z]|computeRobMe|robme_", txt):
            out.append("R-RoB-ME-wired")

    # R-MH-pool: page deals with binary outcomes (tE/cE present) but no MH pool
    has_binary = bool(re.search(r"\btE:\s*\d+,\s*tN:", txt))
    has_mh = bool(re.search(r"mantel|m_h\b|mantelHaenszel|\bMH_OR\b|mhPool", txt, re.IGNORECASE))
    if has_binary and not has_mh:
        out.append("R-MH-pool")

    # R-REML-iteration: tau2_reml declared but iteration block missing
    if "tau2_reml" in txt:
        if not re.search(r"tau2_reml\s*\+\s*_delta", txt) \
                and not re.search(r"_delta\s*=.*?tau2_reml", txt):
            out.append("R-REML-iteration")

    return out


def main():
    targets = [
        p for p in HERE.glob("*_REVIEW.html")
        if p.is_file()
        and "AUTO" not in p.name
        and "FULL_REVIEW" not in p.name
    ]
    print(f"Scanning {len(targets):,} curated REVIEW files...")

    per_file: dict[str, list[str]] = {}
    rule_count: dict[str, int] = {}
    for p in targets:
        txt = p.read_text(encoding="utf-8", errors="replace")
        if not has_substantive_engine(txt):
            continue
        v = violations_in(txt)
        if v:
            per_file[p.name] = v
            for r in v:
                rule_count[r] = rule_count.get(r, 0) + 1

    print(f"\nViolating dashboards: {len(per_file)}")
    print("Rule frequencies:")
    for r, n in sorted(rule_count.items(), key=lambda kv: -kv[1]):
        print(f"  {r:<22}: {n}")

    print("\nPer-file violations:")
    for f in sorted(per_file):
        print(f"  {f}: {', '.join(per_file[f])}")

    (OUT / "violations.json").write_text(json.dumps({
        "dashboards": per_file,
        "rule_count": rule_count,
        "scanned": len(targets),
        "reference": "FINERENONE_REVIEW.html",
    }, indent=2), encoding="utf-8")

    md = ["# Stat-engine violations\n",
          f"Reference: `FINERENONE_REVIEW.html` (all rules pass).\n",
          f"Scanned: {len(targets)} curated REVIEW files.\n",
          f"Violating: {len(per_file)}.\n\n## Per-file\n"]
    for f in sorted(per_file):
        md.append(f"### {f}\n")
        for r in per_file[f]:
            md.append(f"- `{r}`\n")
        md.append("\n")
    (OUT / "violations.md").write_text("".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
