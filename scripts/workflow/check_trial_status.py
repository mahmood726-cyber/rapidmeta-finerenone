#!/usr/bin/env python3
# sentinel:skip-file
"""Nightly: poll CT.gov v2 API for every NCT referenced in any *_REVIEW.html
and detect status changes (results newly posted, study closed, protocol
amended, last-update-submit-date changed since yesterday's snapshot).

Writes:
  .workflow-state/trial_status_snapshot.json  - today's status map
  .workflow-state/trial_status_report.md      - markdown diff vs prior run
                                                (only if diff non-empty)
"""
import argparse, json, pathlib, re, sys, time, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root
CT_API = "https://clinicaltrials.gov/api/v2/studies/"
FIELDS = "NCTId,OverallStatus,LastUpdatePostDate,ResultsFirstPostDate,StudyFirstPostDate,CompletionDate"

NCT_RE = re.compile(r"NCT\d{7,8}")


def extract_ncts():
    """Scan every *_REVIEW.html for NCT IDs, return {nct: [app_name, ...]}."""
    by_nct = {}
    for p in sorted(ROOT.glob("*_REVIEW.html")):
        text = p.read_text(encoding="utf-8", errors="replace")
        for nct in set(NCT_RE.findall(text)):
            by_nct.setdefault(nct, []).append(p.name)
    return by_nct


def fetch_status(nct):
    """Query CT.gov v2 for this NCT; return compact status dict or None."""
    url = f"{CT_API}{urllib.parse.quote(nct)}?fields={FIELDS}&format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta-living-ma/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        ps = data.get("protocolSection", {})
        status = ps.get("statusModule", {})
        return {
            "status":         status.get("overallStatus"),
            "lastUpdatePost": status.get("lastUpdatePostDateStruct", {}).get("date"),
            "resultsPost":    status.get("resultsFirstPostDateStruct", {}).get("date"),
            "studyPost":      status.get("studyFirstPostDateStruct", {}).get("date"),
            "completion":     status.get("completionDateStruct", {}).get("date"),
        }
    except Exception as e:
        return {"error": str(e)[:120]}


def diff_snapshots(prev, curr):
    """Return list of (nct, old_dict, new_dict) for trials whose status changed."""
    changes = []
    for nct, new in curr.items():
        old = prev.get(nct)
        if old is None:
            changes.append((nct, None, new))
            continue
        # Consider interesting if status, resultsPost, or lastUpdatePost changed.
        for k in ("status", "resultsPost", "lastUpdatePost", "completion"):
            if old.get(k) != new.get(k):
                changes.append((nct, old, new))
                break
    return changes


def format_report(changes, by_nct):
    lines = [
        "# Trial accrual report",
        "",
        f"Detected {len(changes)} trial(s) with status or results changes since the prior run.",
        "",
    ]
    for nct, old, new in changes:
        apps = ", ".join(by_nct.get(nct, []))
        lines.append(f"## {nct}")
        lines.append(f"- Apps: {apps or '(none)'}")
        lines.append(f"- Old: `{old}`")
        lines.append(f"- New: `{new}`")
        lines.append(f"- CT.gov: https://clinicaltrials.gov/study/{nct}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    snap_path = ROOT / args.snapshot
    rep_path = ROOT / args.report
    snap_path.parent.mkdir(parents=True, exist_ok=True)

    by_nct = extract_ncts()
    if not by_nct:
        print("No NCTs found in any *_REVIEW.html", file=sys.stderr)
        return 0

    prev = {}
    if snap_path.exists():
        try:
            prev = json.loads(snap_path.read_text(encoding="utf-8"))
        except Exception:
            prev = {}

    curr = {}
    for i, nct in enumerate(sorted(by_nct), 1):
        curr[nct] = fetch_status(nct)
        # Rate-limit courtesy: 50 req/sec is well under CT.gov cap; sleep 0.05s
        if i % 20 == 0:
            time.sleep(0.5)

    snap_path.write_text(json.dumps(curr, indent=2, sort_keys=True), encoding="utf-8")

    changes = diff_snapshots(prev, curr)
    if changes:
        rep_path.parent.mkdir(parents=True, exist_ok=True)
        rep_path.write_text(format_report(changes, by_nct), encoding="utf-8")
        print(f"Wrote report with {len(changes)} change(s) to {rep_path}")
    else:
        # Remove stale report so the workflow's hashFiles check skips issue creation
        if rep_path.exists():
            rep_path.unlink()
        print("No changes since prior run.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
