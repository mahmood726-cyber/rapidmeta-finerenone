#!/usr/bin/env python3
# sentinel:skip-file
"""Diff today's findings harvest against the most recent prior one.

Report includes: (a) apps whose editor decision changed, (b) newly-fired
concerns (not present in prior run), (c) newly-resolved concerns.

Writes .workflow-state/findings_diff.md only if there is a real diff -
otherwise no file and the workflow's hashFiles check suppresses the issue.
"""
import argparse, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_dir(d: pathlib.Path) -> dict:
    out = {}
    if not d.exists():
        return out
    for jp in sorted(d.glob("*.json")):
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            continue
        out[jp.stem] = data
    return out


def find_prior_dir(current: pathlib.Path) -> pathlib.Path | None:
    root_dir = current.parent
    if not root_dir.exists():
        return None
    siblings = sorted([p for p in root_dir.iterdir() if p.is_dir() and p != current])
    return siblings[-1] if siblings else None


def concerns_by_role(findings):
    if not findings or not isinstance(findings, dict):
        return {}
    out = {}
    for rv in findings.get("reviewers", []) or []:
        out[rv.get("role", "unknown")] = set(rv.get("concerns", []) or [])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    curr_dir = ROOT / args.current
    curr = load_dir(curr_dir)
    if not curr:
        print("No findings in current run; nothing to diff.")
        return 0

    prior_dir = find_prior_dir(curr_dir)
    prior = load_dir(prior_dir) if prior_dir else {}

    diffs = []
    for app, cur in sorted(curr.items()):
        prev = prior.get(app, {}) if prior else {}
        cur_fx = cur.get("findings") or {}
        prev_fx = prev.get("findings") or {}

        cur_editor = (cur_fx.get("editor") or {}).get("decision")
        prev_editor = (prev_fx.get("editor") or {}).get("decision")
        cur_roles = concerns_by_role(cur_fx)
        prev_roles = concerns_by_role(prev_fx)

        new_concerns = []
        resolved_concerns = []
        for role in set(cur_roles) | set(prev_roles):
            new_set = cur_roles.get(role, set()) - prev_roles.get(role, set())
            gone_set = prev_roles.get(role, set()) - cur_roles.get(role, set())
            for c in new_set:
                new_concerns.append((role, c))
            for c in gone_set:
                resolved_concerns.append((role, c))

        editor_changed = cur_editor != prev_editor and prev_editor is not None

        if editor_changed or new_concerns or resolved_concerns:
            diffs.append({
                "app": app,
                "editor_old": prev_editor,
                "editor_new": cur_editor,
                "editor_changed": editor_changed,
                "new": new_concerns,
                "resolved": resolved_concerns,
            })

    if not diffs:
        print("No material diff vs prior run.")
        return 0

    rep = ROOT / args.report
    rep.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Peer-review findings diff",
        "",
        f"Apps with material change vs prior harvest: **{len(diffs)}**",
        "",
        f"- Current run: `{curr_dir.name}`",
        f"- Prior run:   `{prior_dir.name if prior_dir else '(none)'}`",
        "",
    ]
    for d in diffs:
        lines.append(f"## {d['app']}")
        if d["editor_changed"]:
            lines.append(f"- **Editor decision:** `{d['editor_old']}` -> `{d['editor_new']}`")
        if d["new"]:
            lines.append("- **New concerns:**")
            for role, c in d["new"]:
                lines.append(f"  - *{role}:* {c}")
        if d["resolved"]:
            lines.append("- **Resolved concerns:**")
            for role, c in d["resolved"]:
                lines.append(f"  - *{role}:* {c}")
        lines.append("")
    rep.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote diff report with {len(diffs)} app(s) to {rep}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
