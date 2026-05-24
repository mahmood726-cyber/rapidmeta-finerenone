"""Apply AACT design metadata as an RoB-2 heuristic across the portfolio.

For each `'NCT...': { ... }` trial block in every *_FULL_REVIEW.html (and the
fewer *_REVIEW.html / *_AUTO_REVIEW.html that use the same shape):

  rob: ['low','low','low','low','low']   <-- stubbed, every trial. unscientific.

We replace it with a heuristic derived from AACT designs.txt:

  D1 Randomization process
    allocation == 'RANDOMIZED'     -> 'low'
    allocation == 'NON_RANDOMIZED' -> 'high'
    else (NA / blank)              -> 'some-concerns'

  D2 Deviations from intended interventions
    masking in (QUADRUPLE, TRIPLE) -> 'low'
    masking == DOUBLE              -> 'low'
    masking == SINGLE              -> 'some-concerns'
    masking == NONE                -> 'high'
    else                           -> 'some-concerns'

  D3 Missing outcome data
    Cannot infer from AACT alone   -> 'some-concerns' (conservative default)

  D4 Outcome measurement
    outcomes_assessor_masked == 'true'             -> 'low'
    masking in (QUADRUPLE,TRIPLE,DOUBLE)           -> 'low'
    masking == SINGLE                              -> 'some-concerns'
    masking == NONE                                -> 'high'
    else                                           -> 'some-concerns'

  D5 Selection of reported result
    Always 'some-concerns' (cannot judge from registry alone — needs
    cross-check with published primary outcome).

This is honestly labelled in a new comment field added to each trial:
  robSource: 'AACT 2026-04-12 designs.txt heuristic (registry-derived, not
              a full RoB-2 reading of trial reports)'

Sentinel-style note: the JS object literal can carry hyphens like 'some-concerns'
in a single-quoted string, which the analysis engine's RoB chip renderer
already handles (it maps low/some-concerns/high -> green/amber/red).

Idempotent: existing rob arrays of length 5 are replaced; the field
`robSource` is upserted.
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
DESIGN = json.loads((HERE / "outputs" / "pmid_resolver" / "nct_design.json").read_text(encoding="utf-8"))

TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)


def rob_for(nct: str) -> tuple[list[str], str]:
    """Return (rob5, source_label)."""
    d = DESIGN.get(nct)
    if not d:
        return ["some-concerns"] * 5, "no AACT design record"

    alloc = d.get("allocation") or ""
    masking = d.get("masking") or ""
    assess = (d.get("outcomes_assessor_masked") or "").lower()

    # D1
    if alloc == "RANDOMIZED":
        d1 = "low"
    elif alloc == "NON_RANDOMIZED":
        d1 = "high"
    else:
        d1 = "some-concerns"

    # D2
    if masking in ("QUADRUPLE", "TRIPLE", "DOUBLE"):
        d2 = "low"
    elif masking == "SINGLE":
        d2 = "some-concerns"
    elif masking == "NONE":
        d2 = "high"
    else:
        d2 = "some-concerns"

    d3 = "some-concerns"  # can't infer from registry

    # D4
    if assess == "true":
        d4 = "low"
    elif masking in ("QUADRUPLE", "TRIPLE", "DOUBLE"):
        d4 = "low"
    elif masking == "SINGLE":
        d4 = "some-concerns"
    elif masking == "NONE":
        d4 = "high"
    else:
        d4 = "some-concerns"

    d5 = "some-concerns"

    src = f"AACT designs: alloc={alloc or '∅'}, masking={masking or '∅'}, assessor_masked={assess or '∅'}"
    return [d1, d2, d3, d4, d5], src


ROB_RE = re.compile(r"rob:\s*\[(?P<inner>[^\]]*)\]")
ROBSRC_RE = re.compile(r"robSource:\s*'[^']*'\s*,?")


def patch_trial(nct: str, body: str) -> tuple[str, bool]:
    rob5, src = rob_for(nct)
    rob_lit = "rob: [" + ", ".join(f"'{r}'" for r in rob5) + "]"
    new_body = ROB_RE.sub(rob_lit, body, count=1)
    if new_body == body:
        # No rob field at all — don't insert (it's not in this block schema).
        return body, False
    # Upsert robSource. Place it right after rob: [...] when present.
    src_lit = f"robSource: '{src.replace(chr(39), chr(8217))}'"
    if "robSource:" in new_body:
        new_body = ROBSRC_RE.sub(src_lit + ", ", new_body, count=1)
    else:
        # Insert after the closing ] of rob: [...]
        new_body = re.sub(
            r"(rob:\s*\[[^\]]*\]\s*,?)",
            lambda m: m.group(1) + " " + src_lit + ",",
            new_body,
            count=1,
        )
    return new_body, new_body != body


def patch_file(p: Path) -> tuple[int, int]:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt
    n_changed = n_trials = 0
    out = []
    last = 0
    for m in TRIAL_BLOCK_RE.finditer(txt):
        n_trials += 1
        new_body, changed = patch_trial(m.group(1), m.group("body"))
        if changed:
            out.append(txt[last:m.start()])
            out.append(f"'{m.group(1)}': {{{new_body}}}")
            last = m.end()
            n_changed += 1
    out.append(txt[last:])
    new_txt = "".join(out)
    if new_txt != orig:
        p.write_text(new_txt, encoding="utf-8")
    return n_changed, n_trials


def main():
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    print(f"Targets: {len(targets):,} HTML files")
    tot_changed = tot_trials = files_changed = 0
    for i, p in enumerate(targets, 1):
        n_c, n_t = patch_file(p)
        if n_c:
            files_changed += 1
        tot_changed += n_c
        tot_trials += n_t
        if i % 300 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: trials_with_rob_updated={n_c} trial_blocks={n_t}")
    print(f"\nFiles changed: {files_changed:,}")
    print(f"Trial blocks scanned: {tot_trials:,}")
    print(f"Trial RoB arrays updated: {tot_changed:,}")


if __name__ == "__main__":
    main()
