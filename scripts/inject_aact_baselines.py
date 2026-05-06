"""Enrich realData baseline objects with AACT-extracted age and pct_female.

For each NCT in outputs/aact_baselines.json:
  - Find that NCT's block in each *_REVIEW.html
  - If `baseline: {...}` exists in that block: merge missing keys (age, pct_female)
  - If not: inject `baseline: { age, pct_female }` after `name: '...',`

Idempotent: never overwrites an existing key.
"""
from __future__ import annotations
import sys, io, re, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
baselines = json.loads((REPO / "outputs/aact_baselines.json").read_text())

# Regex to find a single trial block
def find_trial_block_bounds(text, nct):
    """Find balanced { } block for a given NCT. Returns (start, end) or None."""
    pattern = re.compile(r"'" + re.escape(nct) + r"'\s*:\s*\{")
    m = pattern.search(text)
    if not m:
        return None
    start = m.end() - 1  # position of opening {
    depth = 1
    i = start + 1
    n = len(text)
    while i < n and depth > 0:
        c = text[i]
        if c == "'":
            # Skip string literal (handle escaped quotes)
            i += 1
            while i < n and text[i] != "'":
                if text[i] == "\\":
                    i += 2
                else:
                    i += 1
            i += 1
        elif c == "{":
            depth += 1
            i += 1
        elif c == "}":
            depth -= 1
            i += 1
        else:
            i += 1
    if depth != 0:
        return None
    return (m.start(), i)


def parse_baseline_keys(block):
    """Return dict of existing baseline keys."""
    m = re.search(r"baseline:\s*\{([^{}]*)\}", block)
    if not m:
        return None, None
    existing_str = m.group(0)
    inner = m.group(1)
    keys = set()
    for k in re.findall(r"(\w+)\s*:", inner):
        keys.add(k)
    return existing_str, keys


def enrich_block(block, age, pf):
    """Enrich a trial block with age/pct_female. Returns (new_block, changed)."""
    existing_str, keys = parse_baseline_keys(block)
    additions = []
    if age is not None and "age" not in (keys or set()):
        additions.append(f"age: {age}")
    if pf is not None and "pct_female" not in (keys or set()):
        additions.append(f"pct_female: {pf}")
    if not additions:
        return block, False
    if existing_str is None:
        # No baseline yet — inject after name:
        new_obj = "baseline: {" + ", ".join(additions) + "},"
        new_block = re.sub(
            r"(name:\s*'[^']+?',)",
            r"\1 " + new_obj,
            block,
            count=1,
        )
        return new_block, new_block != block
    # Merge: insert at end of existing baseline
    inner_match = re.search(r"baseline:\s*\{([^{}]*)\}", block)
    inner = inner_match.group(1).rstrip().rstrip(",")
    new_inner = inner + (", " if inner.strip() else "") + ", ".join(additions)
    new_obj = f"baseline: {{{new_inner}}}"
    new_block = block.replace(existing_str, new_obj, 1)
    return new_block, True


def patch_file(text, baselines):
    """Apply enrichment for every NCT we have baselines for."""
    changes = 0
    # Find every NCT that appears in this file AND we have baseline data for
    for nct, rec in baselines.items():
        bounds = find_trial_block_bounds(text, nct)
        if not bounds:
            continue
        s, e = bounds
        block = text[s:e]
        new_block, changed = enrich_block(block, rec.get("age"), rec.get("pct_female"))
        if changed:
            text = text[:s] + new_block + text[e:]
            changes += 1
    return text, changes


def main():
    files = sorted(REPO.glob("*_REVIEW.html"))
    print(f"Scanning {len(files)} files with {len(baselines)} NCTs of AACT data ...")
    total_changes = 0
    files_modified = 0
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, n = patch_file(text, baselines)
        if n > 0:
            hp.write_text(new_text, encoding="utf-8")
            total_changes += n
            files_modified += 1
    print(f"\n=== Summary ===")
    print(f"  Trials enriched: {total_changes}")
    print(f"  Files modified:  {files_modified}")


if __name__ == "__main__":
    main()
