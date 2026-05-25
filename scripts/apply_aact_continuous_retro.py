"""Retroactively inject continuous-outcome effects into FULL_REVIEW trials.

For each trial NCT in outputs/pmid_resolver/nct_continuous.json, overwrite
the trial block's `estimandType`, `publishedHR`, `hrLCI`, `hrUCI` (the engine
reads MD/HR/OR/RR from these fields uniformly), and optionally `tMean`,
`tSD`, `cMean`, `cSD` when we have per-arm raw means.

Skips trials that already have a non-null `publishedHR` from the published-
benchmark file (those values are curated and shouldn't be overwritten by
auto-extraction). Idempotent — re-running just no-ops aligned blocks.
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
CONT = json.loads((HERE / "outputs" / "pmid_resolver" / "nct_continuous.json").read_text(encoding="utf-8"))

TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)


def fmt(v):
    return "null" if v is None else (str(v) if isinstance(v, (int, float)) else f"'{v}'")


def set_field(body: str, field: str, value) -> str:
    """Replace `field: <whatever>` with the new value, preserving the comma
    style. If field isn't present, no change."""
    pat = re.compile(rf"\b{field}:\s*(-?[\d.eE+-]+|null|None|'[^']*')")
    return pat.sub(f"{field}: {fmt(value)}", body, count=1)


def patch_trial(nct: str, body: str) -> tuple[str, bool]:
    info = CONT.get(nct)
    if not info:
        return body, False

    # Skip if a non-null publishedHR is already set AND it disagrees with us
    # by more than a small margin — that value was curated, not auto.
    pubhr_m = re.search(r"\bpublishedHR:\s*(-?[\d.eE+-]+|null|None)", body)
    if pubhr_m and pubhr_m.group(1) not in ("null", "None"):
        try:
            cur = float(pubhr_m.group(1))
            if abs(cur - info["effect"]) / max(1e-6, abs(info["effect"])) > 0.05:
                return body, False  # curated -- don't overwrite
        except ValueError:
            pass

    new = body
    new = set_field(new, "estimandType", info["kind"])
    new = set_field(new, "publishedHR", info["effect"])
    new = set_field(new, "hrLCI", info.get("lci"))
    new = set_field(new, "hrUCI", info.get("uci"))
    # The engine also has duplicate `pubHR`/`pubHR_LCI`/`pubHR_UCI` fields.
    new = set_field(new, "pubHR", info["effect"])
    new = set_field(new, "pubHR_LCI", info.get("lci"))
    new = set_field(new, "pubHR_UCI", info.get("uci"))
    # If we have raw per-arm means, set those too so MD/SMD model has the
    # variance structure (the engine prefers tMean/tSD over derived varMD).
    for fld in ("tMean", "tSD", "tN", "cMean", "cSD", "cN"):
        if fld in info:
            new = set_field(new, fld, info[fld])

    # Propagate estimandType to allOutcomes[0]
    ao_re = re.compile(
        r"(allOutcomes:\s*\[\s*\{[^}]*\bestimandType:\s*)'[^']*'"
    )
    new = ao_re.sub(rf"\g<1>'{info['kind']}'", new, count=1)
    # And copy effect+CI into the outcome's effect/lci/uci slot when present
    for src, dst in [("effect", "effect"), ("lci", "lci"), ("uci", "uci")]:
        if info.get(src) is None:
            continue
        ao_eff_re = re.compile(
            rf"(allOutcomes:\s*\[\s*\{{[^}}]*\b{dst}:\s*)(-?[\d.eE+-]+|null)"
        )
        new = ao_eff_re.sub(rf"\g<1>{info[src]}", new, count=1)

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
        p.write_text(new_txt, encoding="utf-8")
    return n


def main():
    targets = sorted(p for p in HERE.glob("*_FULL_REVIEW.html") if p.is_file())
    print(f"Targets: {len(targets):,} FULL_REVIEW files; map size: {len(CONT):,} NCTs")
    tot = files = 0
    for i, p in enumerate(targets, 1):
        n = patch_file(p)
        if n:
            files += 1
            tot += n
        if i % 300 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: trials updated={n}")
    print(f"\nFiles changed: {files:,}, continuous-outcome trials injected: {tot:,}")


if __name__ == "__main__":
    main()
