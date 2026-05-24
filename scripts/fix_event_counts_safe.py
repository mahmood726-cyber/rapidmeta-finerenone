"""Safe, single-pass event-count correction.

For each FULL_REVIEW trial block:
  If tE > tN (impossible event count):
    - If 0 < tE <= 100  -> tE is a percentage that AACT stored as a measure.
      Recover with round(tE / 100 * tN).
    - Else (tE > 100)   -> not a percentage; not recoverable. Set tE = null
      so the analysis engine excludes the trial from pooling instead of
      pooling impossible counts.
  Same for cE/cN.

Idempotent because after this pass, no surviving tE/cE will satisfy
`tE > tN`: percentages have been converted to plausible counts, and
non-percentages are null.

Also propagates to allOutcomes[0].tE / cE so the analysis engine sees
consistent values.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)


def correct_field(raw: int | None, N: int | None) -> int | None | str:
    """Return one of:
        - int(correct count) if percentage recovery applied (or original was ok)
        - 'null' (string sentinel for JS null) if unrecoverable
        - None to indicate no change needed (when raw is already valid or None)
    """
    if raw is None or N is None or N <= 0:
        return None  # no change
    if raw <= N:
        return None  # already valid count
    if 0 < raw <= 100:
        return round(raw / 100 * N)
    return "null"


def patch_body(body: str) -> tuple[str, bool, bool]:
    """Returns (new_body, corrected_t, corrected_c)."""
    def extract(field):
        m = re.search(rf"\b{field}:\s*(-?\d+|null|None)", body)
        if not m:
            return None
        v = m.group(1)
        return int(v) if v not in ("null", "None") else None

    tE, tN, cE, cN = extract("tE"), extract("tN"), extract("cE"), extract("cN")
    new_body = body
    t_changed = c_changed = False

    new_tE = correct_field(tE, tN)
    if new_tE is not None:
        repl = "null" if new_tE == "null" else str(new_tE)
        new_body = re.sub(r"\btE:\s*(?:-?\d+|null|None)", f"tE: {repl}", new_body, count=1)
        t_changed = True

    new_cE = correct_field(cE, cN)
    if new_cE is not None:
        repl = "null" if new_cE == "null" else str(new_cE)
        new_body = re.sub(r"\bcE:\s*(?:-?\d+|null|None)", f"cE: {repl}", new_body, count=1)
        c_changed = True

    # Propagate to allOutcomes[0].tE / .cE so the analysis engine reads the
    # same values used in pooling.
    if t_changed or c_changed:
        # Read the new tE and cE back from the patched body.
        new_te_m = re.search(r"\btE:\s*(-?\d+|null)", new_body)
        new_ce_m = re.search(r"\bcE:\s*(-?\d+|null)", new_body)
        if new_te_m and new_ce_m:
            te_val = new_te_m.group(1)
            ce_val = new_ce_m.group(1)
            ao_re = re.compile(
                r"(allOutcomes:\s*\[\s*\{[^}]*\btE:\s*)(-?\d+|null)([^}]*\bcE:\s*)(-?\d+|null)"
            )
            new_body = ao_re.sub(
                lambda m: m.group(1) + te_val + m.group(3) + ce_val, new_body, count=1
            )

    return new_body, t_changed, c_changed


def patch_file(p: Path) -> tuple[int, int]:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt
    n_pct_t = n_pct_c = n_null = 0
    out_parts = []
    last = 0
    for m in TRIAL_BLOCK_RE.finditer(txt):
        body = m.group("body")
        new_body, t_changed, c_changed = patch_body(body)
        if new_body != body:
            out_parts.append(txt[last:m.start()])
            out_parts.append(f"'{m.group(1)}': {{{new_body}}}")
            last = m.end()
            if t_changed:
                if "null" in re.search(r"\btE:\s*(\S+)", new_body).group(1):
                    n_null += 1
                else:
                    n_pct_t += 1
            if c_changed:
                if "null" in re.search(r"\bcE:\s*(\S+)", new_body).group(1):
                    n_null += 1
                else:
                    n_pct_c += 1
    out_parts.append(txt[last:])
    new_txt = "".join(out_parts)
    if new_txt != orig:
        p.write_text(new_txt, encoding="utf-8")
    return n_pct_t + n_pct_c, n_null


def main():
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    print(f"Targets: {len(targets):,} HTML files (FULL_REVIEW + REVIEW + AUTO_REVIEW lite)")
    pct_total = null_total = files_changed = 0
    for i, p in enumerate(targets, 1):
        pct, n = patch_file(p)
        if pct or n:
            files_changed += 1
        pct_total += pct
        null_total += n
        if i % 300 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: pct={pct} null={n}")
    print(f"\nFiles changed: {files_changed:,}")
    print(f"Percentage recoveries: {pct_total:,}")
    print(f"Unrecoverable nulled : {null_total:,}")


if __name__ == "__main__":
    main()
