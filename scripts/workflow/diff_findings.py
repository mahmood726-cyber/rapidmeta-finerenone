#!/usr/bin/env python3
# sentinel:skip-file
"""Compare validated, complete harvests; absence of observations is not resolution."""
import argparse
from collections import Counter
from datetime import datetime
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = "_harvest.json"
STATUSES = {"ok", "skipped", "failed", "pending"}


class HarvestError(ValueError):
    """Invalid data, including a claimed completeness that cannot be verified."""


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HarvestError(f"{path}: cannot read JSON: {exc}") from exc


def validate_findings(findings, source):
    if not isinstance(findings, dict):
        raise HarvestError(f"{source}: findings must be an object, got {type(findings).__name__}")
    editor = findings.get("editor")
    if not isinstance(editor, dict) or not isinstance(editor.get("decision"), str) or not editor["decision"]:
        raise HarvestError(f"{source}: findings.editor.decision must be a nonempty string")
    reviewers = findings.get("reviewers")
    if not isinstance(reviewers, list):
        raise HarvestError(f"{source}: findings.reviewers must be an array (explicit [] is valid)")
    for i, reviewer in enumerate(reviewers):
        loc = f"{source}: findings.reviewers[{i}]"
        if not isinstance(reviewer, dict) or not isinstance(reviewer.get("role"), str) or not reviewer["role"]:
            raise HarvestError(f"{loc}.role must be a nonempty string")
        concerns = reviewer.get("concerns")
        if not isinstance(concerns, list) or any(not isinstance(c, str) for c in concerns):
            raise HarvestError(f"{loc}.concerns must be an array of strings (explicit [] is valid)")


def normalize_record(data, source):
    if not isinstance(data, dict):
        raise HarvestError(f"{source}: expected a harvest record object, got {type(data).__name__}")
    app = data.get("app")
    if not isinstance(app, str) or not re.fullmatch(r"[\w.-]+_REVIEW\.html", app):
        raise HarvestError(f"{source}: expected an app filename ending in _REVIEW.html")
    findings = data.get("findings")
    status = data.get("status")
    if status is not None and (not isinstance(status, str) or status not in STATUSES - {"pending"}):
        raise HarvestError(f"{source}: unsupported record status {status!r}")
    if not any(key in data for key in ("findings", "error", "status", "timestamp", "state", "durationMs")):
        raise HarvestError(f"{source}: record is missing findings and harvest metadata")
    if data.get("error") is not None and (not isinstance(data["error"], str) or not data["error"]):
        raise HarvestError(f"{source}: error must be a nonempty string")
    if isinstance(findings, dict) and ("editor" in findings or "reviewers" in findings):
        if data.get("error") or findings.get("error") or findings.get("skipped"):
            raise HarvestError(f"{source}: successful findings conflict with error/skipped markers")
    elif isinstance(findings, dict) and findings.get("error") is not None:
        if not isinstance(findings["error"], str) or not findings["error"]:
            raise HarvestError(f"{source}: findings.error must be a nonempty string")
    # These are the observed legacy harvester shapes, not empty successful reviews.
    if data.get("error") or (isinstance(findings, dict) and findings.get("error")):
        inferred = "failed"
    elif findings is None or (isinstance(findings, dict) and findings.get("skipped") is True):
        inferred = "skipped"
    else:
        validate_findings(findings, source)
        inferred = "ok"
    if status is not None and status != inferred:
        raise HarvestError(f"{source}: status {status!r} contradicts findings ({inferred})")
    record = dict(data)
    record["status"] = inferred
    if inferred == "skipped":
        record["reason"] = data.get("reason") or (findings or {}).get("reason") or "missing-findings"
    if inferred == "failed":
        record["error"] = data.get("error") or findings["error"]
    return record


def load_dir(directory: pathlib.Path) -> dict:
    """Accept per-page objects or arrays of records; reject unrelated audit JSON."""
    if not directory.is_dir():
        raise HarvestError(f"{directory}: harvest directory does not exist")
    records = {}
    for path in sorted(directory.glob("*.json")):
        if path.name == MANIFEST:
            continue
        data = read_json(path)
        values = data if isinstance(data, list) else [data]
        if not values:
            raise HarvestError(f"{path}: empty record array has no app identities")
        for i, value in enumerate(values):
            source = f"{path}[{i}]" if isinstance(data, list) else str(path)
            record = normalize_record(value, source)
            app = record["app"].removesuffix(".html")
            if app in records:
                raise HarvestError(f"{source}: duplicate app {record['app']}")
            records[app] = record
    return records


def timestamp(value, source):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone is required")
        return parsed
    except (AttributeError, TypeError, ValueError) as exc:
        raise HarvestError(f"{source}: expected an ISO timestamp with timezone, got {value!r}") from exc


def load_manifest(directory, records):
    path = directory / MANIFEST
    if not path.exists():
        return None  # Legacy mixed root has no verifiable scope or completion.
    manifest = read_json(path)
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
        raise HarvestError(f"{path}: expected harvest manifest schemaVersion 1")
    timestamp(manifest.get("startedAt"), path)
    if manifest.get("finishedAt") is not None:
        end = timestamp(manifest["finishedAt"], path)
        if end < timestamp(manifest["startedAt"], path):
            raise HarvestError(f"{path}: finishedAt precedes startedAt")
    pages = manifest.get("pages")
    if not isinstance(pages, list):
        raise HarvestError(f"{path}: pages must be an array")
    seen = set()
    counts = Counter()
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get("status"), str) or page["status"] not in STATUSES:
            raise HarvestError(f"{path}: each page must have a known status")
        app = page.get("app")
        if not isinstance(app, str) or not re.fullmatch(r"[\w.-]+_REVIEW\.html", app) or app in seen:
            raise HarvestError(f"{path}: invalid or duplicate page identity {app!r}")
        seen.add(app)
        counts[page["status"]] += 1
        record = records.get(app.removesuffix(".html"))
        if page["status"] == "pending":
            if record is not None:
                raise HarvestError(f"{path}: pending page {app} already has a record")
        elif record is None or record["status"] != page["status"]:
            raise HarvestError(f"{path}: page {app} status disagrees with its record")
    if set(records) != {p["app"].removesuffix(".html") for p in pages if p["status"] != "pending"}:
        raise HarvestError(f"{path}: manifest scope disagrees with record files")
    for key, expected in {"total": len(pages), **{s: counts[s] for s in STATUSES}}.items():
        if type(manifest.get(key)) is not int or manifest[key] != expected:
            raise HarvestError(f"{path}: {key} count should be {expected}, got {manifest.get(key)!r}")
    if manifest.get("scope") not in {"full", "subset"}:
        raise HarvestError(f"{path}: scope must be full or subset")
    complete = bool(pages) and counts["ok"] == len(pages) and manifest["scope"] == "full" and manifest.get("finishedAt") is not None
    if type(manifest.get("complete")) is not bool or manifest["complete"] != complete:
        raise HarvestError(f"{path}: complete flag contradicts coverage/status/finishedAt")
    return manifest


def find_prior_dir(current: pathlib.Path) -> pathlib.Path | None:
    """Newest verified complete snapshot before current; never use mixed root JSON."""
    current_manifest = read_json(current / MANIFEST)
    current_start = timestamp(current_manifest.get("startedAt"), current / MANIFEST)
    candidates = []
    for directory in sorted(current.parent.iterdir()):
        if not directory.is_dir() or directory == current or not (directory / MANIFEST).exists():
            continue
        records = load_dir(directory)
        manifest = load_manifest(directory, records)
        finished = manifest.get("finishedAt")
        if manifest["complete"] and timestamp(finished, directory / MANIFEST) < current_start:
            candidates.append((timestamp(finished, directory / MANIFEST), directory.name, directory))
    return max(candidates)[2] if candidates else None


def concerns_by_role(findings):
    out = {}
    for reviewer in findings["reviewers"]:
        out.setdefault(reviewer["role"], set()).update(reviewer["concerns"])
    return out


def compare_records(current, prior):
    """Only observed successful pairs may produce changes or resolutions."""
    diffs = []
    for app, record in sorted(current.items()):
        previous = prior.get(app)
        if record["status"] != "ok" or (previous and previous["status"] != "ok"):
            continue
        cur_fx = record["findings"]
        # New pages are identified as such; no prior page is not a zero-concern review.
        prev_fx = previous["findings"] if previous else {"editor": {"decision": None}, "reviewers": []}
        cur_roles, prev_roles = concerns_by_role(cur_fx), concerns_by_role(prev_fx)
        new, removed = [], []
        for role in sorted(set(cur_roles) | set(prev_roles)):
            new.extend((role, c) for c in sorted(cur_roles.get(role, set()) - prev_roles.get(role, set())))
            removed.extend((role, c) for c in sorted(prev_roles.get(role, set()) - cur_roles.get(role, set())))
        old, decision = prev_fx["editor"]["decision"], cur_fx["editor"]["decision"]
        changed = previous is not None and old != decision
        if changed or new or removed:
            diffs.append({"app": app, "editor_old": old, "editor_new": decision,
                          "editor_changed": changed, "new_page": previous is None,
                          "new": new, "resolved": removed})
    return diffs


def set_outputs(complete, publish):
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"complete={str(complete).lower()}\npublish={str(publish).lower()}\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--status-report", default=".workflow-state/findings_status.md")
    args = parser.parse_args(argv)
    current_dir, report, status_report = (ROOT / args.current, ROOT / args.report, ROOT / args.status_report)
    report.parent.mkdir(parents=True, exist_ok=True)
    status_report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)  # A tracked report from an older run must never trigger an issue.
    set_outputs(False, False)
    try:
        current = load_dir(current_dir)
        manifest = load_manifest(current_dir, current)
        counts = Counter(r["status"] for r in current.values())
        lines = ["# Peer-review harvest status", "", f"- Current snapshot: `{current_dir.name}`",
                 f"- Observed records: {counts['ok']} successful / {counts['skipped']} skipped / {counts['failed']} failed"]
        if manifest is None:
            lines += ["", "Comparison blocked: no harvest manifest; coverage and completeness are unverified."]
            status_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(lines[-1])
            return 0
        lines += [f"- Scope: {manifest['scope']}; total {manifest['total']}; pending {manifest['pending']}",
                  f"- Complete: {str(manifest['complete']).lower()}"]
        if not manifest["complete"]:
            lines += ["", "Comparison blocked: incomplete harvest. No concern is inferred resolved; no comparison issue or baseline replacement is permitted."]
        else:
            prior_dir = find_prior_dir(current_dir)
            if prior_dir is None:
                lines += ["", "No verified complete prior snapshot. This complete run establishes a baseline; no changes are inferred."]
                set_outputs(True, False)
            else:
                prior = load_dir(prior_dir)
                diffs = compare_records(current, prior)
                removed_pages = sorted(set(prior) - set(current))
                lines += [f"- Complete prior snapshot: `{prior_dir.name}`",
                          f"- Materially changed pages: {len(diffs)}; pages absent from current scope: {len(removed_pages)}"]
                if removed_pages:
                    lines += ["", "Pages absent from the current scope have NOT been classified as resolved:"] + [f"- `{p}`" for p in removed_pages]
                if diffs:
                    text = ["# Peer-review findings diff", "", "Both harvests have verified complete coverage of their declared page scopes.",
                            f"- Current: `{current_dir.name}` ({manifest['ok']}/{manifest['total']} successful)",
                            f"- Prior: `{prior_dir.name}`", "",
                            "Resolved below means no longer emitted by that page's reviewer, not independent scientific adjudication.", ""]
                    if removed_pages:
                        text += [f"{len(removed_pages)} prior pages are absent from the current scope; their concerns remain unassessed.", ""]
                    for diff in diffs:
                        text.append(f"## {diff['app']}")
                        if diff["new_page"]:
                            text.append("- Newly observed page; concerns were not assessed in the prior scope.")
                        if diff["editor_changed"]:
                            text.append(f"- **Editor decision:** `{diff['editor_old']}` -> `{diff['editor_new']}`")
                        for key, title in [("new", "New concerns"), ("resolved", "Resolved concerns (no longer emitted)")]:
                            if diff[key]:
                                text.append(f"- **{title}:**")
                                text.extend(f"  - *{role}:* {concern}" for role, concern in diff[key])
                        text.append("")
                    report.write_text("\n".join(text) + "\n", encoding="utf-8")
                set_outputs(True, bool(diffs))
        status_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(lines[-1])
        return 0
    except HarvestError as exc:
        status_report.write_text(f"# Peer-review harvest status\n\nComparison rejected: {exc}\n", encoding="utf-8")
        print(f"Harvest validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
