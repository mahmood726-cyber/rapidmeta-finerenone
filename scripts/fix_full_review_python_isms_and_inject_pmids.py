"""Fix two bugs in every *_FULL_REVIEW.html shipped by bulk_clone_audit_first.py.

Bug 1 (P0 — kills the entire app):
  The clone emitted Python `None` literals (e.g. `publishedHR: None,`) inside JS
  object literals.  JavaScript treats `None` as an undefined identifier, throws
  ReferenceError mid-evaluation, and the whole `RapidMeta` object is never
  constructed. Visible effect: no trials, no abstracts, no analysis — the page
  loads as a static shell. Fix: replace JS-value-position `None` with `null`.

Bug 2 (P1 — abstracts never appear):
  Every trial entry has `pmid: ''` because the upstream topic-JSON PMID was
  unverifiable. AbstractHydrator is PMID-only, so it no-ops, and trials show
  only their AACT "snippet" — not the published abstract. Fix: resolve a
  verified PMID per NCT from AACT's `study_references` table (RESULT >
  DERIVED > BACKGROUND) and inject it into `pmid: '<pmid>'`.

Touches both *_AUTO_FULL_REVIEW.html and the 13 oddly-named *_REVIEW_FULL_REVIEW.html
clones. Leaves curated *_REVIEW.html (no AUTO suffix) untouched — those are
hand-authored flagships and should not be re-patched.

Idempotent: re-running on already-fixed files is a no-op.
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
NCT_PMID = json.loads((HERE / "outputs" / "pmid_resolver" / "nct_to_pmid.json").read_text(encoding="utf-8"))

# JS-value-position `None`: preceded by ': ' (object value) and followed by ',' '}' ']' or whitespace.
# Will NOT match "None declared" in HTML text (preceded by '>') or "'None declared'" in JS strings.
NONE_VALUE_RE = re.compile(r":(\s+)None(?=[,}\]\s])")

# realData trial entry: 'NCT12345678': { ... pmid: '', ... }
# We replace the literal `pmid: ''` (or `pmid: ""`) immediately following the NCT key,
# scoped to the next ~600 chars (single entry block) so we never cross trial boundaries.
TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)

EMPTY_PMID_RE = re.compile(r"pmid:\s*(?P<q>['\"])(?P=q)")


def fix_file(p: Path) -> tuple[int, int, int]:
    """Return (none_replacements, pmid_injections, trials_seen)."""
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt

    # --- Pass 1: None -> null in JS value position ---
    n_count = 0

    def _sub_none(m: re.Match) -> str:
        nonlocal n_count
        n_count += 1
        return ":" + m.group(1) + "null"

    txt = NONE_VALUE_RE.sub(_sub_none, txt)

    # --- Pass 2: inject verified PMID into each trial block whose pmid:'' is empty ---
    p_count = 0
    trials = 0

    def _sub_trial(m: re.Match) -> str:
        nonlocal p_count, trials
        nct = m.group(1)
        body = m.group("body")
        trials += 1
        info = NCT_PMID.get(nct)
        if not info:
            return m.group(0)
        pmid = info["pmid"]

        def _replace_pmid(mm: re.Match) -> str:
            return f"pmid: '{pmid}'"

        new_body, n = EMPTY_PMID_RE.subn(_replace_pmid, body, count=1)
        if n == 0:
            return m.group(0)
        p_count += 1
        return f"'{nct}': {{{new_body}}}"

    txt = TRIAL_BLOCK_RE.sub(_sub_trial, txt)

    if txt != orig:
        p.write_text(txt, encoding="utf-8")
    return n_count, p_count, trials


def main():
    # Glob `*_FULL_REVIEW.html` catches *_AUTO_FULL_REVIEW (1093), the 13
    # *_REVIEW_FULL_REVIEW double-suffix clones, and 17 *_AUTO_2_FULL_REVIEW
    # v2 variants. Filter out cardiology_mortality_atlas / dashboard / etc.
    targets = sorted(
        p for p in HERE.glob("*_FULL_REVIEW.html") if p.is_file()
    )
    print(f"Targets: {len(targets)} FULL_REVIEW files")

    tot_none = tot_pmid = tot_trials = files_touched = 0
    for i, p in enumerate(targets, 1):
        n, pm, tr = fix_file(p)
        if n or pm:
            files_touched += 1
        tot_none += n
        tot_pmid += pm
        tot_trials += tr
        if i <= 5 or i % 200 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: None={n} pmidInjected={pm} trials={tr}")
    print()
    print(f"Files touched          : {files_touched:,}")
    print(f"`None` -> `null`       : {tot_none:,}")
    print(f"PMIDs injected         : {tot_pmid:,}")
    print(f"Trial blocks seen      : {tot_trials:,}")


if __name__ == "__main__":
    main()
