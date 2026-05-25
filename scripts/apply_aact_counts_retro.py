"""Retroactively apply the param_type-aware AACT counts to FULL_REVIEW pages.

Reads outputs/pmid_resolver/nct_counts.json (built by
build_aact_counts_with_param_type.py). For each trial block whose NCT is in
the map, overwrites tE/tN/cE/cN AND the matching allOutcomes[0].tE/cE so the
analysis engine reads consistent values.

This supersedes the value-vs-N heuristic in fix_event_counts_safe.py for
trials AACT actually has outcome_measurements for; trials with no AACT
outcomes are untouched (their counts came from elsewhere or are null).

Idempotent — re-running just no-ops every block that's already aligned.
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
COUNTS = json.loads((HERE / "outputs" / "pmid_resolver" / "nct_counts.json").read_text(encoding="utf-8"))

TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)


def set_field(body: str, field: str, value) -> str:
    repl = "null" if value is None else str(int(value))
    return re.sub(rf"\b{field}:\s*(?:-?\d+|null|None)", f"{field}: {repl}", body, count=1)


def patch_trial(nct: str, body: str) -> tuple[str, bool]:
    info = COUNTS.get(nct)
    if not info:
        return body, False
    new = body
    new = set_field(new, "tE", info["tE"])
    new = set_field(new, "tN", info["tN"])
    new = set_field(new, "cE", info["cE"])
    new = set_field(new, "cN", info["cN"])
    # Propagate to allOutcomes[0].tE / cE
    ao_re = re.compile(
        r"(allOutcomes:\s*\[\s*\{[^}]*\btE:\s*)(-?\d+|null)([^}]*\bcE:\s*)(-?\d+|null)"
    )
    new = ao_re.sub(lambda m: m.group(1) + str(info["tE"]) + m.group(3) + str(info["cE"]), new, count=1)
    return new, new != body


def patch_file(p: Path) -> int:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt
    n = 0
    out_parts = []
    last = 0
    for m in TRIAL_BLOCK_RE.finditer(txt):
        new_body, changed = patch_trial(m.group(1), m.group("body"))
        if changed:
            out_parts.append(txt[last:m.start()])
            out_parts.append(f"'{m.group(1)}': {{{new_body}}}")
            last = m.end()
            n += 1
    out_parts.append(txt[last:])
    new_txt = "".join(out_parts)
    if new_txt != orig:
        # E2 build-time JS parse gate: verify the new file's realData literal
        # parses under V8 before persisting. If it doesn't, ROLL BACK to the
        # original — the user can investigate via .js_parse_failures.log.
        try:
            from _js_parse_gate import js_parse_ok
        except ImportError:
            js_parse_ok = lambda _t: True
        if not js_parse_ok(new_txt):
            print(f"  ROLLBACK {p.name}: JS parse gate failed; original kept")
            return 0
        p.write_text(new_txt, encoding="utf-8")
    return n


def main():
    targets = sorted(p for p in HERE.glob("*_FULL_REVIEW.html") if p.is_file())
    print(f"Targets: {len(targets):,} FULL_REVIEW files")
    tot = files = 0
    for i, p in enumerate(targets, 1):
        n = patch_file(p)
        if n:
            files += 1
            tot += n
        if i % 300 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: trials updated={n}")
    print(f"\nFiles changed: {files:,}, trials re-extracted: {tot:,}")


if __name__ == "__main__":
    main()
