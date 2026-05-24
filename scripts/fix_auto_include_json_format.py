"""Many NMA REVIEW files (e.g. AD_PEDIATRIC_BIOLOGIC_NMA_REVIEW) store realData
as a JSON-style object (`"NCT...": { "name": ... }`), not the JS literal form
(`'NCT...': { name: ... }`). The original audit40 fixer only matched the
single-quoted JS form, so its AUTO_INCLUDE leak fix missed these files.

This fixer reads both forms and replaces AUTO_INCLUDE_TRIAL_IDS with the union
of NCT keys found in either form, whenever the current AUTO_INCLUDE set has
zero intersection with the realData keys.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
# Match both 'NCT12345': and "NCT12345":
TRIAL_KEY_RE = re.compile(r"['\"](NCT\d{7,8})['\"]\s*:\s*\{")
INC_RE = re.compile(r"const\s+AUTO_INCLUDE_TRIAL_IDS\s*=\s*new\s+Set\(\[([^\]]*)\]\);")


def extract_realdata_keys(txt: str) -> set[str]:
    """Find the realData block (or whichever realData literal is present) and
    return the set of NCT keys inside it."""
    rd_idx = txt.find("realData:")
    if rd_idx < 0:
        return set()
    open_idx = txt.find("{", rd_idx)
    if open_idx < 0:
        return set()
    # Naive brace matching is unreliable due to strings; instead scan forward
    # until we encounter `},\n            async ` or `}\n            ,\n  async`
    # (markers from the surrounding object). Cheap heuristic: bound by 200 KB.
    block = txt[open_idx: open_idx + 200_000]
    # Trim to first `},\n` followed by a known sibling key like `async init` or
    # `nctAcronyms`, `state:`, etc. — anything that signifies end of realData.
    end_match = re.search(
        r"\}\s*,\s*\n\s+(async\s+\w+\(|state\s*:|nctAcronyms\s*:|aliases\s*:|trials\s*:)",
        block,
    )
    if end_match:
        block = block[: end_match.start() + 1]
    return {m.group(1) for m in TRIAL_KEY_RE.finditer(block)}


def patch_file(p: Path) -> dict:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt

    inc_m = INC_RE.search(txt)
    if not inc_m:
        return {"changed": False, "reason": "no AUTO_INCLUDE"}
    inc = set(re.findall(r"NCT\d{7,8}", inc_m.group(1)))
    real = extract_realdata_keys(txt)
    if not real:
        return {"changed": False, "reason": "no realData NCTs detected"}
    if inc & real:
        return {"changed": False, "reason": "already overlaps"}

    # Replace.
    new_lit = ", ".join(f"'{n}'" for n in sorted(real))
    new_decl = f"const AUTO_INCLUDE_TRIAL_IDS = new Set([{new_lit}]);"
    new_txt = txt[: inc_m.start()] + new_decl + txt[inc_m.end():]
    if new_txt != orig:
        p.write_text(new_txt, encoding="utf-8")
        return {"changed": True, "n_real": len(real), "n_old_inc": len(inc)}
    return {"changed": False, "reason": "noop"}


def main():
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    print(f"Targets: {len(targets):,} HTML files")
    changed = 0
    for i, p in enumerate(targets, 1):
        s = patch_file(p)
        if s.get("changed"):
            changed += 1
            if changed <= 10 or changed % 20 == 0:
                print(f"  [{i}/{len(targets)}] {p.name}: real={s['n_real']} old_inc={s['n_old_inc']}")
        if i % 300 == 0:
            print(f"  scanned [{i}/{len(targets)}]")
    print(f"\nFiles fixed: {changed:,}")


if __name__ == "__main__":
    main()
