r"""Fix cp1252-roundtrip em-dash mojibake in HTML files.

Background
----------
A prior generation step opened a UTF-8 source containing em-dash chars
('-') in a cp1252-default editor and re-saved as UTF-8. Each em-dash
became the 8-byte sequence ``c3 a2 e2 82 ac e2 80 9d`` (UTF-8 of the
cp1252 misdecode ``-EUR"``).

Scan via ``scripts/_inspect_mojibake.py`` confirms there is exactly ONE
mojibake pattern in this repo, in exactly one place per file (an
R-script comment line: ``... Bayesian) <mojibake> HR``), across 1,306
files. No other cp1252 mojibake byte sequences are present.

Fix
---
Replace the 8-byte mojibake with the 3-byte UTF-8 em-dash ``e2 80 94``.
Operates on bytes, not text, so encoding-stable. Idempotent: the source
bytes vanish after pass-1, so a second run is a no-op.
"""
from __future__ import annotations
import sys, io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

MOJI = b"\xc3\xa2\xe2\x82\xac\xe2\x80\x9d"   # cp1252-roundtrip em-dash
EM_DASH = b"\xe2\x80\x94"                    # UTF-8 em-dash


def patch_file(p: Path) -> tuple[bool, int]:
    """Return (changed, count). count is replacements made."""
    try:
        b = p.read_bytes()
    except OSError:
        return False, 0
    if MOJI not in b:
        return False, 0
    new = b.replace(MOJI, EM_DASH)
    n = b.count(MOJI)
    p.write_bytes(new)
    return True, n


def main():
    # Root-level dashboards AND e156-submission/assets mirrors. Don't touch
    # scripts/audit_40_checks.py — its mojibake byte literals are the auditor's
    # own detection patterns and must be preserved.
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    submission_assets = HERE / "e156-submission" / "assets"
    if submission_assets.exists():
        targets += sorted(p for p in submission_assets.glob("*.html") if p.is_file())
    total_files = 0
    total_replacements = 0
    for i, p in enumerate(targets, 1):
        changed, n = patch_file(p)
        if changed:
            total_files += 1
            total_replacements += n
        if i % 500 == 0:
            print(f"  [{i}/{len(targets)}]  files fixed so far: {total_files}")
    print(f"\nFiles modified: {total_files}")
    print(f"Total replacements: {total_replacements}")


if __name__ == "__main__":
    main()
