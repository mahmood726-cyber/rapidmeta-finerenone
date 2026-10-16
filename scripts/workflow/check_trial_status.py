#!/usr/bin/env python3
"""Poll registered CT.gov trial statuses with a durable, fail-closed baseline.

A first complete poll establishes a baseline; it is NOT a report of thousands of
clinical changes. Network errors and unparseable/incomplete snapshots must
never overwrite the last validated baseline or trigger an alert.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
CT_API = "https://clinicaltrials.gov/api/v2/studies/"
FIELDS = "NCTId,OverallStatus,LastUpdatePostDate,ResultsFirstPostDate,StudyFirstPostDate,CompletionDate"
NCT_RE = re.compile(r"(?<![A-Za-z0-9_])NCT\d{8}(?!\d)")
CANONICAL_NCT_RE = re.compile(r"NCT\d{8}\Z")
STATUS_KEYS = ("status", "lastUpdatePost", "resultsPost", "studyPost", "completion")
COMPARE_KEYS = ("status", "lastUpdatePost", "resultsPost", "completion")


def extract_ncts():
    """Return canonical referenced NCT IDs and their review-page filenames."""
    by_nct = {}
    for page in sorted(ROOT.glob("*_REVIEW.html")):
        html = page.read_text(encoding="utf-8", errors="replace")
        for nct in set(NCT_RE.findall(html)):
            by_nct.setdefault(nct, []).append(page.name)
    return by_nct


def validate_record(nct, record):
    if not CANONICAL_NCT_RE.fullmatch(nct):
        raise ValueError(f"noncanonical CT.gov identifier in status map: {nct!r}")
    if not isinstance(record, dict) or "error" in record:
        raise ValueError(f"{nct}: missing, failed or malformed CT.gov status record")
    if set(record) != set(STATUS_KEYS):
        raise ValueError(f"{nct}: unexpected status record keys: {sorted(record)}")
    if not isinstance(record["status"], str) or not record["status"].strip():
        raise ValueError(f"{nct}: overallStatus missing; cannot establish a reliable baseline")
    if any(record[key] is not None and not isinstance(record[key], str)
           for key in STATUS_KEYS[1:]):
        raise ValueError(f"{nct}: a date field is not text/null")
    return record


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or not snapshot:
        raise ValueError("Trial-status snapshot must be a nonempty NCT-to-status object")
    for nct, record in snapshot.items():
        validate_record(nct, record)
    return snapshot


def fetch_status(nct):
    """Fetch and validate one study, raising on transport/shape/ID mismatch."""
    if not CANONICAL_NCT_RE.fullmatch(nct):
        raise ValueError(f"Invalid registry identifier: {nct!r}")
    url = f"{CT_API}{urllib.parse.quote(nct)}?fields={FIELDS}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-living-ma/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("non-object API response")
        ps = data.get("protocolSection")
        if not isinstance(ps, dict):
            raise ValueError("protocolSection missing")
        identifying = ps.get("identificationModule", {})
        if not isinstance(identifying, dict) or identifying.get("nctId") != nct:
            raise ValueError("NCT ID missing or not equal to queried study")
        status = ps.get("statusModule")
        if not isinstance(status, dict):
            raise ValueError("statusModule missing")
        def date(key):
            entry = status.get(key)
            return entry.get("date") if isinstance(entry, dict) else None
        record = {
            "status": status.get("overallStatus"),
            "lastUpdatePost": date("lastUpdatePostDateStruct"),
            "resultsPost": date("resultsFirstPostDateStruct"),
            "studyPost": date("studyFirstPostDateStruct"),
            "completion": date("completionDateStruct"),
        }
        return validate_record(nct, record)
    except (ValueError, OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{nct}: CT.gov fetch/validation failed: {exc}") from exc


def diff_snapshots(prev, curr):
    """List verified changes; None previous snapshot is FIRST BASELINE, not a change."""
    validate_snapshot(curr)
    if prev is None:
        return []
    validate_snapshot(prev)
    # Preserve >=95% overlap precisely, without integer flooring: 1/2 and
    # 177/3530 removals must NOT silently pass the census-integrity gate.
    retained = len(prev.keys() & curr.keys())
    if retained * 20 < len(prev) * 19:
        raise ValueError(f"NCT census collapsed: only {retained}/{len(prev)} previously monitored IDs remain")
    changed = []
    # Compare the union. Disappearing portfolio references are provenance
    # changes, NOT evidence that CT.gov deleted or withdrew a study.
    for nct in sorted(prev.keys() | curr.keys()):
        old = prev.get(nct)
        new = curr.get(nct)
        if old is None or new is None or any(old[k] != new[k] for k in COMPARE_KEYS):
            changed.append((nct, old, new))
    return changed


def format_report(changes, by_nct):
    altered = sum(old is not None and new is not None for _, old, new in changes)
    newly_tracked = sum(old is None for _, old, _ in changes)
    removed_from_portfolio = sum(new is None for _, _, new in changes)
    lines = ["# ClinicalTrials.gov status-change and portfolio-coverage audit", "",
             f"Previously tracked registry status/date changes: **{altered}**",
             f"Newly tracked portfolio NCT IDs (not registry changes): **{newly_tracked}**",
             f"No longer referenced by review pages (not CT.gov withdrawals): **{removed_from_portfolio}**", "",
             "Changes compare two complete validated polls. Portfolio entry/exit does not establish a",
             "new, withdrawn or deleted registry study. Verify primary records before clinical claims.", ""]
    for nct, old, new in changes:
        if old is None:
            kind = "new portfolio reference; NOT a newly registered or newly changed CT.gov trial"
        elif new is None:
            kind = "removed from local monitored pages; NOT an established registry withdrawal"
        else:
            kind = "status/date difference in two validated CT.gov observations"
        lines.extend([f"## {nct}",
                      f"- Type: {kind}",
                      f"- Current app references: {', '.join(by_nct.get(nct, [])) or '(none; prior associations not preserved in this snapshot)'}",
                      f"- Previous: `{json.dumps(old, sort_keys=True)}`",
                      f"- Current: `{json.dumps(new, sort_keys=True)}`",
                      f"- Registry: https://clinicaltrials.gov/study/{nct}", ""])
    return "\n".join(lines)


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    snap_path = ROOT / args.snapshot
    report_path = ROOT / args.report
    report_path.unlink(missing_ok=True)
    by_nct = extract_ncts()
    if not by_nct:
        raise RuntimeError("No canonical NCTs found: refusing an empty snapshot")
    previous = None
    if snap_path.exists():
        previous = validate_snapshot(json.loads(snap_path.read_text(encoding="utf-8")))
    current = {}
    for number, nct in enumerate(sorted(by_nct), 1):
        current[nct] = fetch_status(nct)
        if number % 20 == 0:
            time.sleep(0.5)
    validate_snapshot(current)
    changes = diff_snapshots(previous, current)  # validates census BEFORE overwrite
    atomic_write(snap_path, json.dumps(current, indent=2, sort_keys=True) + "\n")
    if previous is None:
        print(f"First complete poll: established {len(current)}-trial baseline without a false change report")
    elif changes:
        atomic_write(report_path, format_report(changes, by_nct))
        print(f"Detected {len(changes)} registry-record or portfolio-reference differences in two complete polls")
    else:
        print(f"No comparable changes across {len(current)} tracked trials")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as error:
        print(f"FAIL-CLOSED trial-accrual monitor: {error}", file=sys.stderr)
        sys.exit(1)
