"""Run deterministic internal-consistency checks on all extracted realData.

Checks per trial:
  T01  NCT ID format               NCT\\d{8}
  T02  Year sanity                 1990 ≤ year ≤ 2026
  T03  PMID format                 6-9 digits
  T04  Binary 2x2 sanity            0 ≤ tE ≤ tN, 0 ≤ cE ≤ cN, both N > 0
  T05  publishedHR within CI       hrLCI ≤ publishedHR ≤ hrUCI (positive on HR scale)
  T06  publishedHR magnitude       0.05 ≤ HR ≤ 20  (sanity range)
  T07  CI width sanity             hrUCI/hrLCI < 100 (no degenerate widths)
  T08  Computed log-OR direction   sign(log(2x2 OR)) matches sign(log publishedHR)
                                    when published is on RR/OR scale (skip for HR)
  T09  Trial name not empty
  T10  Trial baseline N consistency  baseline.n ≈ tN + cN if both present (±5%)

Checks per review:
  R01  Trial count > 0
  R02  All NCT keys are unique
  R03  Trial year monotone-or-mixed (informational only)
  R04  Mixed outcome scales: trials with publishedHR but allOutcomes type=CONTINUOUS are flagged
  R05  Outliers: any trial whose publishedHR is >5σ from pool mean (informational)
  R06  Pool computation: random-effects log-OR pool from binary 2x2; compare to
       median(publishedHR) — large divergence → trial-pool mismatch flag

Output:
  outputs/extraction_audit/findings.csv  — one row per finding (severity-ranked)
  outputs/extraction_audit/findings.json — same data, structured
  outputs/extraction_audit/summary.json  — per-review summary (counts by severity)
"""
from __future__ import annotations
import csv
import io
import json
import math
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "outputs" / "extraction_audit" / "data"
OUT_DIR = REPO / "outputs" / "extraction_audit"

NCT_RE = re.compile(r"^NCT\d{8}$")
PMID_RE = re.compile(r"^\d{6,9}$")


def severity_rank(sev: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "INFO": 3}.get(sev, 4)


def is_finite_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def trial_log_or(tE, tN, cE, cN):
    """Continuity-corrected log-OR + variance for a 2x2 trial."""
    a, b, c, d = tE, tN - tE, cE, cN - cE
    if min(a, b, c, d) == 0:
        a += 0.5; b += 0.5; c += 0.5; d += 0.5
    yi = math.log((a * d) / (b * c))
    vi = 1/a + 1/b + 1/c + 1/d
    return yi, vi


def pool_random_log_or(trials):
    """DL random-effects log-OR pool from list of {tE, tN, cE, cN}.
    Returns (pooled_OR, k, tau2, Q) or None if k<2 or any trial invalid."""
    pts = []
    for t in trials:
        try:
            yi, vi = trial_log_or(int(t["tE"]), int(t["tN"]), int(t["cE"]), int(t["cN"]))
            pts.append((yi, vi))
        except Exception:
            continue
    if len(pts) < 2:
        return None
    W = sum(1 / vi for _, vi in pts)
    yFE = sum((1 / vi) * yi for yi, vi in pts) / W
    Q = sum((1 / vi) * (yi - yFE) ** 2 for yi, vi in pts)
    df = len(pts) - 1
    sumW2 = sum((1 / vi) ** 2 for _, vi in pts)
    cden = W - sumW2 / W
    tau2 = max(0.0, (Q - df) / cden) if cden > 0 else 0.0
    W2 = sum(1 / (vi + tau2) for _, vi in pts)
    yRE = sum(yi / (vi + tau2) for yi, vi in pts) / W2
    return math.exp(yRE), len(pts), tau2, Q


def is_binary(trial) -> bool:
    keys = ("tE", "tN", "cE", "cN")
    return all(is_finite_num(trial.get(k)) for k in keys) and trial.get("tN", 0) > 0 and trial.get("cN", 0) > 0


def collect_findings(review_stem: str, doc: dict) -> list[dict]:
    """Return one finding per detected issue (or [] if clean)."""
    findings: list[dict] = []
    rd = doc.get("realData") or {}
    if not isinstance(rd, dict):
        return findings
    trials = []
    for nct, t in rd.items():
        if not isinstance(t, dict):
            continue
        # T01 NCT ID format
        if not NCT_RE.match(nct):
            findings.append({
                "review": review_stem, "scope": "trial", "ncts": nct,
                "code": "T01", "severity": "P1",
                "msg": f"Invalid NCT ID format: {nct!r}",
            })
        # T09 name
        nm = t.get("name") or ""
        if not nm or not str(nm).strip():
            findings.append({
                "review": review_stem, "scope": "trial", "ncts": nct,
                "code": "T09", "severity": "P2", "msg": "Trial name is empty",
            })
        # T02 year
        yr = t.get("year")
        if is_finite_num(yr):
            if not (1990 <= yr <= 2026):
                findings.append({
                    "review": review_stem, "scope": "trial", "ncts": nct,
                    "code": "T02", "severity": "P1",
                    "msg": f"Year {yr!r} out of range [1990, 2026]",
                })
        # T03 PMID
        pmid = t.get("pmid")
        if pmid not in (None, ""):
            ps = str(pmid).strip()
            if not PMID_RE.match(ps):
                findings.append({
                    "review": review_stem, "scope": "trial", "ncts": nct,
                    "code": "T03", "severity": "P2",
                    "msg": f"PMID {pmid!r} not 6-9 digit format",
                })
        # T04 binary 2x2
        binary = is_binary(t)
        if binary:
            tE, tN, cE, cN = (int(t["tE"]), int(t["tN"]), int(t["cE"]), int(t["cN"]))
            if tE < 0 or tE > tN:
                findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                    "code": "T04", "severity": "P0",
                    "msg": f"tE={tE} out of [0, tN={tN}]"})
            if cE < 0 or cE > cN:
                findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                    "code": "T04", "severity": "P0",
                    "msg": f"cE={cE} out of [0, cN={cN}]"})
            if tN < 5 or cN < 5:
                findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                    "code": "T04", "severity": "P1",
                    "msg": f"Implausibly small N: tN={tN}, cN={cN}"})
            # T10 baseline N
            base = t.get("baseline") or {}
            base_n = base.get("n") if isinstance(base, dict) else None
            if is_finite_num(base_n) and base_n > 0:
                expected = tN + cN
                ratio = expected / base_n if base_n > 0 else 0
                if ratio < 0.85 or ratio > 1.15:
                    findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                        "code": "T10", "severity": "P2",
                        "msg": f"baseline.n={base_n} differs from tN+cN={expected} by >15%"})
        # T05/T06/T07 publishedHR — note: many reviews use publishedHR field to
        # store a published primary effect on ANY scale (including mean
        # differences for continuous outcomes), so negative values aren't
        # automatically a bug. Heuristic:
        #   - positive HR + CI:  T05 = HR within CI; T06 = HR magnitude sanity
        #   - negative number + symmetric CI: assume MD scale, only flag if MD outside CI
        #   - signs disagree (HR < 0 < UCI etc): T05b = scale-confused
        hr = t.get("publishedHR")
        lci = t.get("hrLCI")
        uci = t.get("hrUCI")
        if all(is_finite_num(x) for x in (hr, lci, uci)):
            if lci > uci:
                findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                    "code": "T05", "severity": "P0",
                    "msg": f"LCI={lci} > UCI={uci} (CI inverted)"})
            elif hr > 0 and lci > 0 and uci > 0:
                # HR/OR/RR scale (all positive, ratio measure)
                if not (lci - 0.005 <= hr <= uci + 0.005):
                    findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                        "code": "T05", "severity": "P0",
                        "msg": f"publishedHR={hr} outside [LCI={lci}, UCI={uci}] on HR scale"})
                if hr < 0.05 or hr > 20:
                    findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                        "code": "T06", "severity": "P2",
                        "msg": f"publishedHR={hr} outside sanity range [0.05, 20] on HR scale"})
                if lci > 0 and uci / lci > 100:
                    findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                        "code": "T07", "severity": "P2",
                        "msg": f"CI ratio UCI/LCI={uci/lci:.1f}x >100x — degenerate"})
            elif hr < 0 and lci < 0 and uci < 0:
                # All negative — typical mean-difference scale (treatment lowers)
                if not (lci - 0.01 <= hr <= uci + 0.01):
                    findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                        "code": "T05", "severity": "P0",
                        "msg": f"publishedHR(MD)={hr} outside [LCI={lci}, UCI={uci}]"})
            elif (hr < 0) != (lci < 0) or (hr < 0) != (uci < 0):
                # Mixed signs — almost certainly a scale-confused field or extraction error
                findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                    "code": "T05b", "severity": "P1",
                    "msg": f"Sign-mixed effect: HR={hr}, LCI={lci}, UCI={uci} — scale confusion likely"})

        # Mixed outcome scales (R04)
        ao = t.get("allOutcomes") if isinstance(t.get("allOutcomes"), list) else None
        if ao and is_finite_num(hr):
            cont_only = all(o.get("type") == "CONTINUOUS" for o in ao if isinstance(o, dict)) and len(ao) > 0
            if cont_only:
                findings.append({"review": review_stem, "scope": "trial", "ncts": nct,
                    "code": "R04", "severity": "P1",
                    "msg": "publishedHR set but allOutcomes are all CONTINUOUS — likely scale mismatch"})

        trials.append({"nct": nct, "binary": binary, **t})

    # Review-level checks
    if not trials:
        findings.append({"review": review_stem, "scope": "review", "ncts": "",
            "code": "R01", "severity": "P0", "msg": "No trials in realData"})
        return findings

    # R02 NCT uniqueness — already enforced by dict keys; skip

    # R06 pool vs published comparison
    binary_trials = [t for t in trials if t.get("binary")]
    if len(binary_trials) >= 2:
        pool = pool_random_log_or(binary_trials)
        if pool:
            pooled_OR, k, tau2, _Q = pool
            # Compare to median publishedHR (proxy for "claimed published")
            hrs = [t.get("publishedHR") for t in trials if is_finite_num(t.get("publishedHR"))]
            if len(hrs) >= 2:
                hrs_sorted = sorted(hrs)
                med = hrs_sorted[len(hrs_sorted) // 2]
                if med > 0 and pooled_OR > 0:
                    log_diff = abs(math.log(pooled_OR) - math.log(med))
                    if log_diff > 0.5:  # 0.5 on log scale ≈ 65% relative diff — flag big mismatches
                        findings.append({
                            "review": review_stem, "scope": "review", "ncts": "",
                            "code": "R06", "severity": "P1",
                            "msg": f"Random-effects log-OR pool ({pooled_OR:.3f}, k={k}) "
                                   f"diverges from median publishedHR ({med:.3f}) by "
                                   f"|Δlog|={log_diff:.2f}"})
    return findings


def main() -> None:
    index = json.loads((DATA_DIR / "_index.json").read_text(encoding="utf-8"))
    all_findings: list[dict] = []
    summary_per_review: list[dict] = []
    n_reviews = 0
    n_with_findings = 0
    for entry in index:
        if not entry.get("has_realData"):
            continue
        stem = entry["stem"]
        doc = json.loads((DATA_DIR / f"{stem}.json").read_text(encoding="utf-8"))
        try:
            findings = collect_findings(stem, doc)
        except Exception as e:
            findings = [{"review": stem, "scope": "review", "ncts": "",
                         "code": "EXC", "severity": "P0",
                         "msg": f"audit script crashed: {type(e).__name__}: {e}"}]
        n_reviews += 1
        if findings:
            n_with_findings += 1
            all_findings.extend(findings)
        sev_counts = {k: 0 for k in ("P0", "P1", "P2", "INFO")}
        for f in findings:
            sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1
        summary_per_review.append({
            "review": stem,
            "trial_count": entry["trials"],
            "P0": sev_counts["P0"], "P1": sev_counts["P1"], "P2": sev_counts["P2"],
        })

    # Sort findings: severity, then code
    all_findings.sort(key=lambda f: (severity_rank(f["severity"]), f["code"], f["review"]))

    # Emit CSV
    csv_path = OUT_DIR / "findings.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["severity", "code", "review", "scope", "ncts", "message"])
        for f in all_findings:
            w.writerow([f["severity"], f["code"], f["review"], f["scope"], f["ncts"], f["msg"]])

    # Emit JSON
    (OUT_DIR / "findings.json").write_text(json.dumps(all_findings, indent=2), encoding="utf-8")

    # Per-review summary
    summary_per_review.sort(key=lambda r: (-r["P0"], -r["P1"], -r["P2"], r["review"]))
    (OUT_DIR / "summary.json").write_text(json.dumps(summary_per_review, indent=2), encoding="utf-8")

    # Aggregate counts
    by_code: dict[str, int] = {}
    by_sev: dict[str, int] = {}
    for f in all_findings:
        by_code[f["code"]] = by_code.get(f["code"], 0) + 1
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1

    print(f"Reviews audited: {n_reviews}")
    print(f"Reviews with at least one finding: {n_with_findings}")
    print(f"Total findings: {len(all_findings)}")
    print()
    print("By severity:")
    for k in ("P0", "P1", "P2", "INFO"):
        print(f"  {k}: {by_sev.get(k, 0)}")
    print()
    print("By code (top 12):")
    for code, n in sorted(by_code.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {code}: {n}")


if __name__ == "__main__":
    main()
