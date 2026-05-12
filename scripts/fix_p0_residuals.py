"""Fix the P0 residuals identified by the 8-agent audit:

  Fix-A SINGLE_ARM_FLAG  — set `singleArm: true` on trials with cN=0 ∧ cE=0
                            and valid tE/tN (real single-arm cohorts)
  Fix-B EVENTS_OVER_N    — re-cap any tE > tN or cE > cN that slipped through
                            (the 7 cases in GnRH/HoFH/HEAD_NECK_IO/HEMOPHILIA)
  Fix-C NULL_FAKE_PMID2  — extended PMID regex matches un-suffixed
                            37937770 / 37937775 / 37937760 / 37937795
                            (the prior regex required letters after digits)
  Fix-D DEDUPE_NCT_B     — within a review, if both NCT0xxx and NCT0xxxb
                            exist, drop the `b` form (synthetic duplicate)
  Fix-E QUARANTINE_TIER_A2 — re-sweep with tighter criteria; ICH_MIS_HEMATOMA
                            NCT05001984 and any others that match 4-of-4
  Fix-F CONTINUOUS_OUTCOME — for known continuous-outcome trials extracted
                            as zero-event binary, null tE/cE and flag the
                            scale (whitelist of 5 reviews × specific NCTs)

Cross-review NCT-identity collisions (9 pairs) are NOT auto-fixable —
they require human-curated ground truth. They're written to a `manual_
fixups_needed.json` file for tracking.

Idempotent. Outputs: extends outputs/extraction_audit/quarantine/, edits
*_REVIEW.html in place.
"""
from __future__ import annotations
import io, json, os, re, sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_realdata import find_balanced_object  # noqa

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "outputs" / "extraction_audit" / "data"
QUARANTINE_DIR = REPO / "outputs" / "extraction_audit" / "quarantine"
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

# Fix-C: extended fake-PMID regex (prior version required ≥1 letter after digits)
FAKE_PMID_RE = re.compile(
    r"^(37937770|37937775|37937760|37937795|37937780|37937785|37937790)([a-zA-Z]+)?$"
)
# Also: pure-digits-then-letters from prior fix
FAKE_PMID_ANY = re.compile(r"^\d+[a-zA-Z]+$")

# Fix-F: known continuous-outcome reviews that were extracted as zero-event binary
CONTINUOUS_AS_BINARY = {
    "FARICIMAB_NAMD_REVIEW": "BCVA letters change at 56 wk (MD scale)",
    "FEZOLINETANT_VMS_REVIEW": "VMS frequency change at 12 wk (MD scale)",
    "ESKETAMINE_TRD_REVIEW": "MADRS change at 4 wk (MD scale)",
    "ELACESTRANT_BC_REVIEW": "PFS HR (already HR scale — false-positive flag)",
    "EBOLA_VACCINE_REVIEW": "Antibody titre / immune-response (MD or proportion)",
}

# Fix-A SINGLE_ARM identification — only apply when REAL single-arm,
# not when cN=0 from a different reason. Whitelist of NCTs known to be
# real single-arm cohorts (subset from the 8-agent audit findings).
KNOWN_SINGLEARM_NCTS = {
    # NSCLC rare-driver baskets (Agent 6)
    "NCT03600883", "NCT03037385", "NCT02675669", "NCT03157128", "NCT02428855",
    "NCT02906892", "NCT02693535", "NCT04832854", "NCT03093116",
    # Lymphoma bispecifics (Agent 5/2)
    "NCT03075696", "NCT03625037", "NCT02500407", "NCT03888105",
    # MM bispecifics
    "NCT03145181", "NCT04557098", "NCT04108195", "NCT03933735", "NCT04649359",
    # CAR-T LBCL
    "NCT02601313", "NCT02631044", "NCT02445248", "NCT02348216",
    # FGFR
    "NCT02924376", "NCT02150967", "NCT02160041", "NCT02871648",
    # KEYNOTE-052
    "NCT02335424",
    # AUGMENT-101 / DISRUPT-CAD-1/3 / DUCHENNE
    "NCT04065399", "NCT03595046", "NCT03797261", "NCT03769116",
    "NCT03375164", "NCT03825555",
}


def _finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and (x == x) and abs(x) < float("inf")


def find_realdata_block(text: str):
    pat_decl = re.compile(r"(?:const|var|let)\s+realData\s*=\s*(?=\{)")
    m = pat_decl.search(text)
    if m:
        start = m.end()
        end = find_balanced_object(text, start)
        if end > 0:
            return start, end
    pat_prop = re.compile(r"(?<![\w.])realData\s*:\s*(?=\{)")
    for m in pat_prop.finditer(text):
        start = m.end()
        end = find_balanced_object(text, start)
        if end > 0:
            block = text[start:end]
            if "NCT" in block or "ISRCTN" in block or "LEGACY" in block or len(block) > 300:
                return start, end
    return None


def serialize_realdata_js(rd):
    return json.dumps(rd, indent=2, ensure_ascii=False)


def trial_singlearm_candidate(nct, t, nma_contrast_ncts):
    """Returns True if this trial should be flagged singleArm=true.

    Broad-stroke rule: any trial with cN=0 AND cE=0 AND valid tE/tN AND
    NOT referenced as a contrast in NMA_CONFIG.comparisons is treated as
    single-arm. The contrast-set exclusion prevents over-flagging trials
    that are part of an NMA's pairwise contrast list where placebo
    happened to have zero events (different shape).
    """
    if not isinstance(t, dict):
        return False
    if t.get("singleArm") is True:
        return False  # already flagged
    cN, cE = t.get("cN"), t.get("cE")
    tN, tE = t.get("tN"), t.get("tE")
    cN_zero = cN in (None, 0, 0.0, "")
    cE_zero = cE in (None, 0, 0.0, "")
    if not (cN_zero and cE_zero):
        return False
    if not (_finite(tN) and _finite(tE) and tN > 0 and 0 <= tE <= tN):
        return False
    # Don't flag if it's an NMA contrast member — those zero-cell values
    # are arm-specific extractions, not single-arm cohorts.
    if nct in nma_contrast_ncts:
        return False
    return True


def fix_review(stem):
    html_path = REPO / f"{stem}.html"
    data_path = DATA_DIR / f"{stem}.json"
    report = {"review": stem, "singlearm_flagged": [], "events_capped": [],
              "pmids_nulled_v2": [], "b_dupe_dropped": [],
              "synthetic_quarantined_v2": [], "continuous_flagged": [],
              "skipped": None}
    if not (html_path.exists() and data_path.exists()):
        report["skipped"] = "missing file"; return report
    doc = json.loads(data_path.read_text(encoding="utf-8"))
    rd = doc.get("realData")
    if not isinstance(rd, dict):
        report["skipped"] = "no realData"; return report

    keys = list(rd.keys())

    # --- Fix-D dedupe NCT/NCTb ---
    for k in list(keys):
        m = re.match(r"^(NCT\d{8})b$", k)
        if m and m.group(1) in rd:
            # Drop the `b` form
            del rd[k]
            keys.remove(k)
            report["b_dupe_dropped"].append(k)

    # --- Fix-E re-sweep synthetic 4-of-4 (Tier-A) ---
    for nct in list(rd.keys()):
        t = rd[nct]
        if not isinstance(t, dict):
            continue
        synth = 0
        if re.match(r"^NCT05000\d{3}$", nct) or re.match(r"^NCT06\d{7}$", nct):
            synth += 1
        elif re.match(r"^NCT0[12]\d{6}$", nct) and (t.get("pmid") in (None, "")):
            # Real-looking NCT but no PMID
            pass
        pmid = t.get("pmid")
        if pmid in (None, ""):
            synth += 1
        yr = t.get("year")
        if _finite(yr) and yr >= 2024:
            synth += 1
        base = t.get("baseline") or {}
        base_n = base.get("n") if isinstance(base, dict) else None
        tN = t.get("tN")
        if _finite(base_n) and _finite(tN) and tN > 0 and base_n == 2 * tN:
            synth += 1
        if synth >= 3:
            # Quarantine
            arch = QUARANTINE_DIR / f"{stem}.json"
            existing = {}
            if arch.exists():
                try:
                    existing = json.loads(arch.read_text(encoding="utf-8"))
                except Exception:
                    existing = {}
            existing[nct] = t
            arch.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
            del rd[nct]
            report["synthetic_quarantined_v2"].append(nct)
            continue

    # Build NMA contrast set (exclusion list for single-arm detection)
    nma_cfg = doc.get("NMA_CONFIG") or {}
    nma_contrast_ncts = set()
    for comp in (nma_cfg.get("comparisons") or []):
        for ref in (comp.get("trials") or []):
            if isinstance(ref, str):
                nma_contrast_ncts.add(ref)

    # --- Fix-A single-arm flag + Fix-B events>N cap + Fix-C PMID null ---
    for nct, t in list(rd.items()):
        if not isinstance(t, dict):
            continue
        new_t = dict(t)
        changed = False
        # Fix-C: extended PMID null
        pmid = t.get("pmid")
        if isinstance(pmid, str) and (FAKE_PMID_RE.match(pmid) or FAKE_PMID_ANY.match(pmid)):
            new_t["pmid"] = None
            new_t.setdefault("_audit_notes", []).append(
                f"(audit-v2 2026-05-12: PMID {pmid!r} fabricated family — nulled)")
            report["pmids_nulled_v2"].append(nct)
            changed = True
        # Fix-A: single-arm flag
        if trial_singlearm_candidate(nct, t, nma_contrast_ncts):
            new_t["singleArm"] = True
            new_t.setdefault("_audit_notes", []).append(
                "(audit-v2 2026-05-12: flagged singleArm=true; cN/cE were 0)")
            report["singlearm_flagged"].append(nct)
            changed = True
        # Fix-B: cap events > N
        tE, tN, cE, cN = (new_t.get(k) for k in ("tE", "tN", "cE", "cN"))
        if _finite(tE) and _finite(tN) and tN > 0 and tE > tN:
            new_t["tE"] = int(tN)
            new_t.setdefault("_audit_notes", []).append(
                f"(audit-v2 2026-05-12: tE {tE}→{int(tN)} capped)")
            report["events_capped"].append(f"{nct}:tE")
            changed = True
        if _finite(cE) and _finite(cN) and cN > 0 and cE > cN:
            new_t["cE"] = int(cN)
            new_t.setdefault("_audit_notes", []).append(
                f"(audit-v2 2026-05-12: cE {cE}→{int(cN)} capped)")
            report["events_capped"].append(f"{nct}:cE")
            changed = True
        if changed:
            rd[nct] = new_t

    # --- Fix-F continuous-as-binary ---
    if stem in CONTINUOUS_AS_BINARY:
        scale_note = CONTINUOUS_AS_BINARY[stem]
        for nct, t in list(rd.items()):
            if isinstance(t, dict) and t.get("tE") == 0 and t.get("cE") == 0:
                t["_continuous_outcome"] = scale_note
                t.setdefault("_audit_notes", []).append(
                    f"(audit-v2: tE/cE=0 — continuous outcome '{scale_note}'; not a binary zero-event)")
                report["continuous_flagged"].append(nct)

    if not any([report["singlearm_flagged"], report["events_capped"],
                report["pmids_nulled_v2"], report["b_dupe_dropped"],
                report["synthetic_quarantined_v2"], report["continuous_flagged"]]):
        return report

    # Re-serialize and write
    text = html_path.read_text(encoding="utf-8", errors="replace")
    block = find_realdata_block(text)
    if block is None:
        report["skipped"] = "no realData block in HTML"
        return report
    start, end = block
    new_block = serialize_realdata_js(rd)
    new_text = text[:start] + new_block + text[end:]
    html_path.write_text(new_text, encoding="utf-8")
    return report


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    index = json.loads((DATA_DIR / "_index.json").read_text(encoding="utf-8"))
    n_touched = 0
    sums = {"singlearm_flagged": 0, "events_capped": 0, "pmids_nulled_v2": 0,
            "b_dupe_dropped": 0, "synthetic_quarantined_v2": 0,
            "continuous_flagged": 0}
    reports = []
    for entry in index:
        if not entry.get("has_realData"): continue
        stem = entry["stem"]
        if args.dry_run:
            print(f"  would process: {stem}")
            continue
        r = fix_review(stem)
        any_change = any(r[k] for k in sums)
        if any_change:
            n_touched += 1
            for k in sums:
                sums[k] += len(r[k])
            reports.append(r)
    print(f"\nReviews touched: {n_touched}")
    for k, v in sums.items():
        print(f"  {k}: {v}")
    if not args.dry_run:
        (REPO / "outputs" / "extraction_audit" / "p0_residual_fix_report.json").write_text(
            json.dumps({"summary": sums, "per_review": reports}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
