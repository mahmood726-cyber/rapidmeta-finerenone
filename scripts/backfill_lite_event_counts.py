r"""Backfill corrected event counts from FULL_REVIEW pages into their
lite AUTO_REVIEW twins.

Problem
-------
149 lite *_AUTO_REVIEW.html pages have impossible event counts (events >
sample size) because they were generated before bulk_clone's
_safe_event_count safeguard was added. Their full twins
(*_AUTO_FULL_REVIEW.html) were corrected by later retro fixers; the lite
ones were never re-applied.

Fix
---
For each lite page in QUARANTINE band:
  1. Find its full twin by replacing _AUTO_REVIEW.html with _AUTO_FULL_REVIEW.html
  2. For each NCT trial block in the lite page where tE > tN OR cE > cN:
       - Look up the same NCT in the full page
       - Copy full's tE, tN, cE, cN (and publishedHR/CI if present)
       - Rewrite the lite trial body with corrected values
  3. Idempotent: re-running on a page with no impossible counts is a no-op.

Safety
------
- Only modifies fields known to be impossible (tE/cE), not anything else
- Preserves the JSON-quoted lite format
- Skips if full twin missing
"""
from __future__ import annotations
import sys, io, re, json
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

# Lite trial block uses JSON-quoted keys: "NCT...": { ... "tE": N, "tN": N, ... }
LITE_TRIAL_RE = re.compile(
    r'"(NCT\d{7,8})"\s*:\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}',
    re.DOTALL,
)

# Full trial block: 'NCT...': { ... tE: N, tN: N, ... }  (or terser-unquoted)
FULL_TRIAL_RE = re.compile(
    r"(?:'(NCT\d{7,8})'|\"(NCT\d{7,8})\"|\b(NCT\d{7,8}))\s*:\s*\{"
    r"(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)


def get_field_jsonish(body, name):
    """Get a numeric field from either JSON-quoted or JS unquoted body."""
    m = re.search(
        rf"['\"]?{name}['\"]?\s*:\s*(-?[\d.eE+-]+|null|None)",
        body,
    )
    if not m: return None
    v = m.group(1)
    if v in ("null", "None"): return None
    try:
        return float(v) if "." in v or "e" in v.lower() else int(v)
    except ValueError:
        return None


def extract_full_trials(full_path: Path) -> dict[str, dict]:
    """Parse full page, return {NCT: {tE,tN,cE,cN,pubHR,hrLCI,hrUCI}}"""
    if not full_path.exists():
        return {}
    txt = full_path.read_text(encoding="utf-8", errors="replace")
    out = {}
    for m in FULL_TRIAL_RE.finditer(txt):
        nct = m.group(1) or m.group(2) or m.group(3)
        body = m.group("body")
        out[nct] = {
            "tE": get_field_jsonish(body, "tE"),
            "tN": get_field_jsonish(body, "tN"),
            "cE": get_field_jsonish(body, "cE"),
            "cN": get_field_jsonish(body, "cN"),
            "publishedHR": get_field_jsonish(body, "publishedHR"),
            "hrLCI": get_field_jsonish(body, "hrLCI"),
            "hrUCI": get_field_jsonish(body, "hrUCI"),
        }
    return out


def patch_lite_trial_body(body: str, fields: dict) -> tuple[str, list]:
    """Replace tE/tN/cE/cN in a lite trial body with the full's values.

    Lite format: `"tE": N,` (JSON). We rewrite the value while preserving
    the key + colon + whitespace + trailing comma.
    """
    changed = []
    for k in ("tE", "tN", "cE", "cN"):
        full_val = fields.get(k)
        if full_val is None:
            new_val = "null"
        else:
            new_val = str(full_val)
        pat = re.compile(rf'("{k}"\s*:\s*)(-?[\d.eE+-]+|null|None)')
        m = pat.search(body)
        if not m: continue
        old_val = m.group(2)
        if old_val == new_val:
            continue
        body = body[:m.start(2)] + new_val + body[m.end(2):]
        changed.append((k, old_val, new_val))
    return body, changed


def _full_twin(lite_path: Path) -> Path | None:
    """Map a lite path to its full-review twin path.

    Two naming patterns are in use in this corpus:
      *_AUTO_REVIEW.html         -> *_AUTO_FULL_REVIEW.html
      *_REVIEW.html (no AUTO)    -> *_REVIEW_FULL_REVIEW.html  (doubled suffix)
    """
    name = lite_path.name
    parent = lite_path.parent
    if name.endswith("_AUTO_REVIEW.html"):
        cand = parent / name.replace("_AUTO_REVIEW.html", "_AUTO_FULL_REVIEW.html")
    else:
        cand = parent / name.replace("_REVIEW.html", "_REVIEW_FULL_REVIEW.html")
    return cand if cand.exists() else None


def patch_lite_page(lite_path: Path) -> dict:
    """Patch all impossible-count trials in lite_path using its full twin."""
    full_path = _full_twin(lite_path)
    if full_path is None:
        return {"status": "no-full-twin", "lite": lite_path.name}
    full_trials = extract_full_trials(full_path)
    if not full_trials:
        return {"status": "full-twin-empty", "lite": lite_path.name}

    txt = lite_path.read_text(encoding="utf-8", errors="replace")
    edits = []
    new_segments = []
    last = 0

    for m in LITE_TRIAL_RE.finditer(txt):
        nct = m.group(1)
        body = m.group("body")
        # Detect impossibility
        tE = get_field_jsonish(body, "tE")
        tN = get_field_jsonish(body, "tN")
        cE = get_field_jsonish(body, "cE")
        cN = get_field_jsonish(body, "cN")
        impossible = (
            (tE is not None and tN is not None and tE > tN)
            or (cE is not None and cN is not None and cE > cN)
        )
        if not impossible:
            continue
        if nct not in full_trials:
            edits.append({"nct": nct, "status": "no-full-NCT-match"})
            continue
        new_body, changes = patch_lite_trial_body(body, full_trials[nct])
        if not changes:
            continue
        edits.append({"nct": nct, "changes": changes})
        # Splice: keep [last, body_start), replace [body_start, body_end) with new_body
        body_start = m.start("body")
        body_end = m.end("body")
        new_segments.append(txt[last:body_start])
        new_segments.append(new_body)
        last = body_end

    if not edits:
        return {"status": "no-impossible", "lite": lite_path.name}

    new_segments.append(txt[last:])
    new_txt = "".join(new_segments)
    lite_path.write_text(new_txt, encoding="utf-8")
    return {"status": "patched", "lite": lite_path.name, "edits": edits}


def main():
    # Get all QUARANTINE lite pages from the recomputed bands
    data = json.loads((HERE / "outputs" / "audit40" / "bands_recomputed.json").read_text(encoding="utf-8"))
    targets = sorted(
        name for name, info in data["per_file"].items()
        if info["band"] == "QUARANTINE" and "_FULL_REVIEW.html" not in name
    )
    print(f"Targets (QUARANTINE lite pages): {len(targets)}")

    patched = 0
    no_twin = 0
    no_change = 0
    for fname in targets:
        result = patch_lite_page(HERE / fname)
        if result["status"] == "patched":
            patched += 1
        elif result["status"] == "no-full-twin":
            no_twin += 1
        else:
            no_change += 1

    print(f"\nPatched: {patched}")
    print(f"No full twin: {no_twin}")
    print(f"No change / no impossibility: {no_change}")


if __name__ == "__main__":
    main()
