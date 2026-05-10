"""Master fixer for extraction-audit P0/P1 defects.

Applies four fixes in one pass per affected review HTML:

  Fix-1  QUARANTINE-SYNTHETIC: remove every trial matching the 4-of-4 LLM
         synthetic fingerprint (NCT in NCT05000xxx/NCT06xxxxxxxx blocks +
         empty/missing PMID + year ≥ 2024 + baseline.n == 2 × tN).

  Fix-2  QUARANTINE-LIKELY-SYNTHETIC: remove every trial matching 3-of-4
         (real-looking NCT but the other three smoking-gun fields). Agent 6
         spot-check confirmed 0/8 are genuine.

  Fix-3  NULL-FAKE-PMID: set `pmid: null` for trials whose pmid matches the
         fabricated /^379377[67]\\d[a-zA-Z]+$/ family.

  Fix-4  CAP-EVENTS: where tE > tN or cE > cN AND the trial is NOT in the
         quarantine set (so it's a real-anchor trial with a numeric error),
         cap events at the corresponding N and append an audit note.

Quarantined trials are archived to
  outputs/extraction_audit/quarantine/<REVIEW_STEM>.json
so the action is reversible.

Idempotent: re-running on already-fixed HTML yields zero further mutations.

Usage:
  python scripts/fix_extraction_defects.py --dry-run    # report only
  python scripts/fix_extraction_defects.py              # apply
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Re-use the extractor's JS-object → JSON converter
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_realdata import find_balanced_object, js_object_to_json, extract_var  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "outputs" / "extraction_audit" / "data"
QUARANTINE_DIR = REPO / "outputs" / "extraction_audit" / "quarantine"
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
SWEEP_FILE = REPO / "outputs" / "synthetic_fixture_sweep.json"
FINDINGS_CSV = REPO / "outputs" / "extraction_audit" / "findings.csv"
FIX_REPORT = REPO / "outputs" / "extraction_audit" / "fix_report.json"

FAKE_PMID_RE = re.compile(r"^\d+[a-zA-Z]+$")  # any digits-then-letters PMID is malformed
                                                # (real PMIDs are pure integers; the
                                                # 37937770[a-z]/37937775[a-z]/37937760[a-z]
                                                # families all match this)
SYNTH_NCT_5_RE = re.compile(r"^NCT05000\d{3}$")  # NCT05000xxx synthetic block
SYNTH_NCT_6_RE = re.compile(r"^NCT06\d{7}$")     # NCT06xxxxxxx (only ~22 in corpus, all synth)


def _is_finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def trial_synthetic_fingerprint(nct: str, t: dict) -> int:
    """Return how many of the 4 fingerprint criteria the trial hits.
    >= 3 → quarantine.
    """
    score = 0
    # C1: synthetic NCT range
    if SYNTH_NCT_5_RE.match(nct) or SYNTH_NCT_6_RE.match(nct):
        score += 1
    # C2: empty/null/non-numeric PMID OR fake-PMID family
    pmid = t.get("pmid")
    if pmid in (None, ""):
        score += 1
    elif isinstance(pmid, str) and FAKE_PMID_RE.match(pmid):
        score += 1
    elif isinstance(pmid, str) and not pmid.strip().isdigit():
        score += 1
    # C3: year 2024+
    yr = t.get("year")
    if _is_finite(yr) and yr >= 2024:
        score += 1
    # C4: baseline.n exactly == 2 × tN (un-reconciled halving)
    base = t.get("baseline") or {}
    base_n = base.get("n") if isinstance(base, dict) else None
    tN = t.get("tN")
    if _is_finite(base_n) and _is_finite(tN) and tN > 0 and base_n == 2 * tN:
        score += 1
    return score


def trial_has_fake_pmid(t: dict) -> bool:
    pmid = t.get("pmid")
    return isinstance(pmid, str) and bool(FAKE_PMID_RE.match(pmid))


def trial_has_events_over_n(t: dict) -> tuple[bool, bool]:
    """Returns (tE_bad, cE_bad). Bad means: tE > tN, tE < 0, or tN ≤ 0
    (likewise for cE/cN). Negative events indicate field overload (MD
    stored in the event slot)."""
    tE, tN, cE, cN = (t.get(k) for k in ("tE", "tN", "cE", "cN"))
    tE_bad = _is_finite(tE) and _is_finite(tN) and tN > 0 and (tE > tN or tE < 0)
    cE_bad = _is_finite(cE) and _is_finite(cN) and cN > 0 and (cE > cN or cE < 0)
    return tE_bad, cE_bad


def serialize_realdata_js(rd: dict) -> str:
    """Emit a clean JS object literal for the realData value.
    Strategy: JSON is a subset of JS for object literals — JS engines parse
    JSON-formatted text as a valid object literal. ensure_ascii=False keeps
    non-ASCII characters readable in the source.
    """
    return json.dumps(rd, indent=2, ensure_ascii=False)


def find_realdata_block(text: str) -> tuple[int, int] | None:
    """Locate the value-side of `realData: { ... }` (object literal property)
    or `var/const/let realData = { ... }` (declaration). Returns (start, end)
    of the object literal (start at `{`, end after `}`).
    """
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


def fix_review(review_stem: str, dry_run: bool) -> dict:
    """Apply all four fixes to one review HTML file. Returns a per-review report."""
    html_path = REPO / f"{review_stem}.html"
    data_path = DATA_DIR / f"{review_stem}.json"
    report = {
        "review": review_stem,
        "quarantined_synthetic": [],   # NCTs hard-removed (synthetic fingerprint ≥ 3)
        "nulled_pmids": [],             # NCTs with fake PMID nulled
        "capped_events": [],            # NCTs with tE/cE capped at N
        "skipped_reason": None,
    }
    if not html_path.exists():
        report["skipped_reason"] = "html missing"
        return report
    if not data_path.exists():
        report["skipped_reason"] = "data json missing"
        return report

    doc = json.loads(data_path.read_text(encoding="utf-8"))
    rd = doc.get("realData")
    if not isinstance(rd, dict):
        report["skipped_reason"] = "realData not parsed"
        return report

    # Identify trials
    quarantine_keys: list[str] = []
    nulled_keys: list[str] = []
    cap_actions: list[tuple[str, dict, str]] = []  # (nct, action, reason)

    for nct, t in list(rd.items()):
        if not isinstance(t, dict):
            continue
        score = trial_synthetic_fingerprint(nct, t)
        if score >= 3:
            quarantine_keys.append(nct)
            continue
        # Real-anchor trial path
        if trial_has_fake_pmid(t):
            nulled_keys.append(nct)
        tE_bad, cE_bad = trial_has_events_over_n(t)
        if tE_bad or cE_bad:
            cap_actions.append((nct, t, f"tE_bad={tE_bad} cE_bad={cE_bad}"))

    if not (quarantine_keys or nulled_keys or cap_actions):
        return report  # nothing to do

    # Build mutated realData
    mutated = {}
    quarantined_archive = {}
    for nct, t in rd.items():
        if nct in quarantine_keys:
            quarantined_archive[nct] = t
            continue
        new_t = dict(t) if isinstance(t, dict) else t
        if nct in nulled_keys:
            new_t["pmid"] = None
            note = f"(audit 2026-05-10: PMID was {t.get('pmid')!r} — fabricated 37937770/5 family; nulled)"
            new_t.setdefault("_audit_notes", []).append(note)
        # Caps
        for cap_nct, cap_t, _reason in cap_actions:
            if cap_nct != nct:
                continue
            tE, tN, cE, cN = (new_t.get(k) for k in ("tE", "tN", "cE", "cN"))
            cap_note_parts = []
            if _is_finite(tE) and _is_finite(tN) and tN > 0:
                if tE < 0:
                    cap_note_parts.append(f"tE {tE}→null (negative — field-overload MD)")
                    new_t["tE"] = None
                elif tE > tN:
                    cap_note_parts.append(f"tE {tE}→{tN}")
                    new_t["tE"] = tN
            if _is_finite(cE) and _is_finite(cN) and cN > 0:
                if cE < 0:
                    cap_note_parts.append(f"cE {cE}→null (negative — field-overload MD)")
                    new_t["cE"] = None
                elif cE > cN:
                    cap_note_parts.append(f"cE {cE}→{cN}")
                    new_t["cE"] = cN
            if cap_note_parts:
                note = "(audit 2026-05-10: events>N capped — " + ", ".join(cap_note_parts) + ")"
                new_t.setdefault("_audit_notes", []).append(note)
        mutated[nct] = new_t

    # Locate the realData block in HTML and replace
    text = html_path.read_text(encoding="utf-8", errors="replace")
    block = find_realdata_block(text)
    if block is None:
        report["skipped_reason"] = "realData block not found in HTML"
        return report
    start, end = block
    new_block = serialize_realdata_js(mutated)
    new_text = text[:start] + new_block + text[end:]

    report["quarantined_synthetic"] = quarantine_keys
    report["nulled_pmids"] = nulled_keys
    report["capped_events"] = [n for n, _, _ in cap_actions]

    if dry_run:
        return report

    # Archive quarantined trials
    if quarantined_archive:
        qpath = QUARANTINE_DIR / f"{review_stem}.json"
        existing = {}
        if qpath.exists():
            try:
                existing = json.loads(qpath.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        existing.update(quarantined_archive)
        qpath.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    # Write modified HTML
    html_path.write_text(new_text, encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="don't write any files")
    ap.add_argument("--limit", type=int, default=0, help="only process N reviews (debug)")
    args = ap.parse_args()

    index = json.loads((DATA_DIR / "_index.json").read_text(encoding="utf-8"))
    targets = [e for e in index if e.get("has_realData")]
    if args.limit:
        targets = targets[: args.limit]
    print(f"Targets: {len(targets)} reviews{' (DRY RUN)' if args.dry_run else ''}")
    reports: list[dict] = []
    n_quarantined_trials = 0
    n_nulled_pmids = 0
    n_capped = 0
    n_reviews_touched = 0
    n_reviews_skipped = 0
    for entry in targets:
        try:
            r = fix_review(entry["stem"], args.dry_run)
        except Exception as e:
            r = {"review": entry["stem"], "skipped_reason": f"exception: {type(e).__name__}: {e}"}
        reports.append(r)
        if r.get("skipped_reason"):
            n_reviews_skipped += 1
        elif r["quarantined_synthetic"] or r["nulled_pmids"] or r["capped_events"]:
            n_reviews_touched += 1
            n_quarantined_trials += len(r["quarantined_synthetic"])
            n_nulled_pmids += len(r["nulled_pmids"])
            n_capped += len(r["capped_events"])
    summary = {
        "dry_run": args.dry_run,
        "reviews_targeted": len(targets),
        "reviews_touched": n_reviews_touched,
        "reviews_skipped": n_reviews_skipped,
        "trials_quarantined": n_quarantined_trials,
        "pmids_nulled": n_nulled_pmids,
        "trials_events_capped": n_capped,
    }
    if not args.dry_run:
        FIX_REPORT.write_text(
            json.dumps({"summary": summary, "per_review": reports}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    print(json.dumps(summary, indent=2))
    # Top-15 reviews by changes for transparency
    ranked = sorted(reports, key=lambda r: -(len(r.get("quarantined_synthetic", [])) +
                                              len(r.get("nulled_pmids", [])) +
                                              len(r.get("capped_events", []))))
    print("\nTop 15 reviews by mutation count:")
    for r in ranked[:15]:
        n = (len(r.get("quarantined_synthetic", [])) +
             len(r.get("nulled_pmids", [])) +
             len(r.get("capped_events", [])))
        if n == 0:
            break
        print(f"  {n:3d}  {r['review']}: "
              f"quar={len(r['quarantined_synthetic'])} "
              f"pmid={len(r['nulled_pmids'])} "
              f"cap={len(r['capped_events'])}")


if __name__ == "__main__":
    main()
