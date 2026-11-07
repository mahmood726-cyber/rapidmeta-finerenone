#!/usr/bin/env python3
"""Poll registered CT.gov trial statuses with a durable, fail-closed baseline.

A first complete poll establishes a baseline; it is NOT a report of thousands of
clinical changes. Network errors and unparseable/incomplete snapshots must
never overwrite the last validated baseline or trigger an alert.
"""
from __future__ import annotations

import argparse
from datetime import date as calendar_date
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
RETRY_BUDGET_SECONDS = 600.0
COMPARE_KEYS = ("status", "lastUpdatePost", "resultsPost", "completion")


def extract_ncts():
    """Return canonical referenced NCT IDs and their review-page filenames."""
    by_nct = {}
    for page in sorted(ROOT.glob("*_REVIEW.html")):
        html = page.read_text(encoding="utf-8", errors="replace")
        for nct in set(NCT_RE.findall(html)):
            by_nct.setdefault(nct, []).append(page.name)
    return by_nct


def validate_ctgov_date(value):
    """Validate calendar dates without inventing missing day/month precision."""
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", value):
        raise ValueError("invalid CT.gov date representation")
    parts = [int(part) for part in value.split("-")]
    try:
        calendar_date(parts[0], parts[1] if len(parts) > 1 else 1,
                      parts[2] if len(parts) > 2 else 1)
    except ValueError as exc:
        raise ValueError("invalid CT.gov calendar date") from exc
    return value


def validate_record(nct, record):
    if not CANONICAL_NCT_RE.fullmatch(nct):
        raise ValueError(f"noncanonical CT.gov identifier in status map: {nct!r}")
    if not isinstance(record, dict) or "error" in record:
        raise ValueError(f"{nct}: missing, failed or malformed CT.gov status record")
    if set(record) != set(STATUS_KEYS):
        raise ValueError(f"{nct}: unexpected status record keys: {sorted(record)}")
    if not isinstance(record["status"], str) or not record["status"].strip():
        raise ValueError(f"{nct}: overallStatus missing; cannot establish a reliable baseline")
    for key in STATUS_KEYS[1:]:
        try:
            validate_ctgov_date(record[key])
        except ValueError as exc:
            raise ValueError(f"{nct}: invalid {key}: {exc}") from exc
    return record


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or not snapshot:
        raise ValueError("Trial-status snapshot must be a nonempty NCT-to-status object")
    for nct, record in snapshot.items():
        validate_record(nct, record)
    return snapshot


class TransientFetchError(RuntimeError):
    """Timeout, 429 or 5xx: worth a bounded retry; never a permanent verdict."""

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class PermanentFetchError(RuntimeError):
    """Per-NCT outcome recorded in the ledger (kind: not_found | alias)."""

    def __init__(self, nct, kind, canonical=None):
        super().__init__(f"{nct}: {kind}" + (f" -> {canonical}" if canonical else ""))
        self.nct, self.kind, self.canonical = nct, kind, canonical


def fetch_status(nct):
    """Fetch and validate one study, raising on transport/shape/ID mismatch.

    404/410 -> PermanentFetchError("not_found"); timeout/429/5xx ->
    TransientFetchError; a payload for a DIFFERENT canonical nctId is accepted
    only as an alias when the HTTP client was actually redirected to that
    study (final URL ends with that id). Any other mismatch still aborts.
    """
    if not CANONICAL_NCT_RE.fullmatch(nct):
        raise ValueError(f"Invalid registry identifier: {nct!r}")
    url = f"{CT_API}{urllib.parse.quote(nct)}?fields={FIELDS}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-living-ma/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            final_url = getattr(response, "geturl", lambda: None)()
            data = load_unique_json(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("non-object API response")
        ps = data.get("protocolSection")
        if not isinstance(ps, dict):
            raise ValueError("protocolSection missing")
        identifying = ps.get("identificationModule", {})
        got = identifying.get("nctId") if isinstance(identifying, dict) else None
        if got != nct:
            redirected = (isinstance(final_url, str) and isinstance(got, str)
                          and CANONICAL_NCT_RE.fullmatch(got) is not None
                          and urllib.parse.urlparse(final_url).path.rstrip("/").rsplit("/", 1)[-1] == got)
            if redirected:
                raise PermanentFetchError(nct, "alias", canonical=got)
            raise ValueError("NCT ID missing or not equal to queried study")
        status = ps.get("statusModule")
        if not isinstance(status, dict):
            raise ValueError("statusModule missing")
        def date(key):
            if key not in status:
                return None
            entry = status[key]
            if not isinstance(entry, dict) or not isinstance(entry.get("date"), str):
                raise ValueError(f"{key}: malformed present CT.gov dateStruct")
            return validate_ctgov_date(entry["date"])
        record = {
            "status": status.get("overallStatus"),
            "lastUpdatePost": date("lastUpdatePostDateStruct"),
            "resultsPost": date("resultsFirstPostDateStruct"),
            "studyPost": date("studyFirstPostDateStruct"),
            "completion": date("completionDateStruct"),
        }
        return validate_record(nct, record)
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            raise PermanentFetchError(nct, "not_found") from exc
        if exc.code == 429 or exc.code >= 500:
            retry_after = None
            try:
                retry_after = float(exc.headers.get("Retry-After")) if exc.headers else None
            except (TypeError, ValueError):
                pass
            raise TransientFetchError(f"{nct}: CT.gov HTTP {exc.code}", retry_after) from exc
        raise RuntimeError(f"{nct}: CT.gov fetch/validation failed: HTTP {exc.code}") from exc
    except (TimeoutError, urllib.error.URLError) as exc:
        raise TransientFetchError(f"{nct}: CT.gov transport error: {exc}") from exc
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{nct}: CT.gov fetch/validation failed: {exc}") from exc


def fetch_with_retry(nct, budget, sleep=time.sleep, attempts=4):
    """Retry transient errors with capped exponential backoff.

    `budget` is a shared {"left": seconds} dict so a bad API day cannot stall
    the ~3,500-ID poll indefinitely; when spent, the transient error is raised
    (fail closed). Permanent outcomes are never retried.
    """
    for attempt in range(attempts):
        try:
            return fetch_status(nct)
        except TransientFetchError as exc:
            delay = min(exc.retry_after if exc.retry_after is not None else 2 ** attempt, 30)
            if attempt == attempts - 1 or delay > budget["left"]:
                raise
            budget["left"] -= delay
            sleep(delay)


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


def load_unique_json(text):
    """Reject ambiguous duplicate keys in snapshots and live registry responses."""
    def reject_duplicates(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError(f"ambiguous duplicate JSON key: {key!r}")
            obj[key] = value
        return obj
    return json.loads(text, object_pairs_hook=reject_duplicates)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--ledger", help="default: <snapshot>.ledger.json")
    parser.add_argument("--max-unresolved-fraction", type=float, default=0.01)
    args = parser.parse_args(argv)
    max_unresolved = args.max_unresolved_fraction
    snap_path = ROOT / args.snapshot
    ledger_path = ROOT / (args.ledger or args.snapshot + ".ledger.json")
    report_path = ROOT / args.report
    report_path.unlink(missing_ok=True)
    by_nct = extract_ncts()
    if not by_nct:
        raise RuntimeError("No canonical NCTs found: refusing an empty snapshot")
    previous = None
    if snap_path.exists():
        previous = validate_snapshot(load_unique_json(snap_path.read_text(encoding="utf-8")))
    ledger_path.unlink(missing_ok=True)
    current, ledger = {}, {}
    budget = {"left": RETRY_BUDGET_SECONDS}
    for number, nct in enumerate(sorted(by_nct), 1):
        try:
            current[nct] = fetch_with_retry(nct, budget)
        except PermanentFetchError as exc:
            # Recorded, never dropped. An alias is NEVER stored under the
            # canonical id (that would overwrite a different study's record).
            ledger[nct] = {"kind": exc.kind, "canonical": exc.canonical,
                           "carried_forward": bool(previous and nct in previous)}
            if previous and nct in previous:
                current[nct] = previous[nct]  # keep census; ledger says it is stale
        if number % 20 == 0:
            time.sleep(0.5)
    atomic_write(ledger_path, json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    if len(ledger) > max_unresolved * len(by_nct):
        raise RuntimeError(
            f"{len(ledger)}/{len(by_nct)} NCTs unresolved (404/alias), above the "
            f"{max_unresolved:.1%} threshold; baseline preserved: {sorted(ledger)[:20]}")
    if ledger:
        print(f"Ledger: {len(ledger)} unresolved NCTs recorded in {ledger_path.name}: {sorted(ledger)[:20]}")
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
