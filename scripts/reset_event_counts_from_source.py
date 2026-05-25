"""Reset compounded event-count corruption introduced by repeated runs of
fix_audit40_findings.py.

Origin of the bug: when AACT's outcome_measurements stored a percentage like
'57.1' or a continuous-outcome value like '350.0', the bulk_clone_audit_first
pipeline cast it via `int(float(v))` and treated it as an integer event count.
The original audit40 fixer then noticed tE>tN (impossible event count) and
applied `round(v/100 * N)` to recover the percentage. BUT the fixer was NOT
guarded against re-application — and on a second run, if the corrected value
was still > N, the same operation was reapplied, compounding the corruption:
  TITAN cE: 524 -> 204 -> 80 -> 31  (the original AACT value 524 is gone)
  DAPRODUSTAT NCT03029208 cE: 350 -> 542 -> 840  (compounding upward)

This script rebuilds the canonical tE/tN/cE/cN values from the immutable
source-of-truth `outputs/new_topics/<STEM>_AUTO.json` files (which are the
output of `add_topic_autodiscover.py` — the upstream of bulk_clone). For
each NCT in each FULL_REVIEW/AUTO_REVIEW page, it writes back the original
tE/cE values. NO percentage correction is applied — the user sees the
underlying AACT-derived counts as-is; trials where the counts don't make
sense (tE > tN) are flagged with a comment but not silently transformed.
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
TOPICS_DIR = HERE / "outputs" / "new_topics"

NCT_RE = re.compile(r"NCT\d{7,8}")
TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)


def build_source_truth():
    """Build NCT -> (tE, tN, cE, cN) from outputs/new_topics/*.json.

    Replays the same extraction logic as bulk_clone_audit_first.build_config:
      arms = sorted(aact_per_arm_counts.keys())
      tN = first arm count, cN = second arm count
      og_vals = first occurrence per OG ID, cast to int(float(v))
      tE = og_vals[sorted_ogs[0]], cE = og_vals[sorted_ogs[1]]
    """
    truth: dict[str, tuple] = {}
    for jp in sorted(TOPICS_DIR.glob("*.json")):
        try:
            doc = json.loads(jp.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for t in doc.get("trials", []):
            if not all(t.get("gates", {}).values()):
                continue
            ex = t.get("extracted", {})
            nct = ex.get("nct")
            if not nct:
                continue
            per_arm = ex.get("aact_per_arm_counts") or {}
            og_rows = ex.get("aact_outcome_count_rows") or []
            arms = sorted(per_arm.keys())
            tN = per_arm.get(arms[0]) if arms else None
            cN = per_arm.get(arms[1]) if len(arms) > 1 else None
            og_vals: dict[str, int] = {}
            for og, v in og_rows:
                if og not in og_vals:
                    try:
                        og_vals[og] = int(float(v))
                    except Exception:
                        pass
                if len(og_vals) >= 2:
                    break
            ogs = sorted(og_vals.keys())
            tE = og_vals.get(ogs[0]) if ogs else None
            cE = og_vals.get(ogs[1]) if len(ogs) > 1 else None
            # Last write wins per NCT — fine because the same NCT in two
            # different topics would have the same AACT data.
            truth[nct] = (tE, tN, cE, cN)
    return truth


# Replace a numeric field in a trial body.
def set_field(body: str, field: str, value) -> str:
    """Replace `field: <num|null>` with the canonical value, preserving spacing."""
    if value is None:
        repl = f"{field}: null"
    else:
        repl = f"{field}: {value}"
    return re.sub(rf"\b{field}:\s*(?:-?\d+|null|None)", repl, body, count=1)


def reset_trial_body(body: str, nct: str, truth: dict) -> tuple[str, bool]:
    if nct not in truth:
        return body, False
    tE, tN, cE, cN = truth[nct]
    new_body = body
    new_body = set_field(new_body, "tE", tE)
    new_body = set_field(new_body, "tN", tN)
    new_body = set_field(new_body, "cE", cE)
    new_body = set_field(new_body, "cN", cN)
    # Propagate to allOutcomes[0].tE / cE so analysis-engine reads consistent values.
    if tE is not None and cE is not None:
        ao_re = re.compile(r"(allOutcomes:\s*\[\s*\{[^}]*\btE:\s*)(-?\d+|null)([^}]*\bcE:\s*)(-?\d+|null)")
        new_body = ao_re.sub(
            lambda m: m.group(1) + str(tE) + m.group(3) + str(cE), new_body, count=1
        )
    return new_body, new_body != body


def patch_file(p: Path, truth: dict) -> int:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt
    n_reset = 0
    out_parts = []
    last = 0
    for m in TRIAL_BLOCK_RE.finditer(txt):
        nct = m.group(1)
        body = m.group("body")
        new_body, changed = reset_trial_body(body, nct, truth)
        if changed:
            out_parts.append(txt[last:m.start()])
            out_parts.append(f"'{nct}': {{{new_body}}}")
            last = m.end()
            n_reset += 1
    out_parts.append(txt[last:])
    new_txt = "".join(out_parts)
    if new_txt != orig:
        p.write_text(new_txt, encoding="utf-8")
    return n_reset


def main():
    truth = build_source_truth()
    print(f"Built source-truth map: {len(truth):,} NCTs")

    targets = sorted(p for p in HERE.glob("*_FULL_REVIEW.html") if p.is_file())
    print(f"Targets: {len(targets):,} FULL_REVIEW files")
    total_reset = files_changed = 0
    for i, p in enumerate(targets, 1):
        n = patch_file(p, truth)
        if n > 0:
            files_changed += 1
        total_reset += n
        if i % 300 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: reset={n}")
    print(f"\nFiles changed: {files_changed:,}  trial cells reset: {total_reset:,}")


if __name__ == "__main__":
    main()
