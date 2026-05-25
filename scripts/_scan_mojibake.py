r"""Scan HTML files for the cp1252-roundtrip mojibake byte sequences.

These are leading bytes of UTF-8 -> cp1252-misdecode -> UTF-8 reencode
chains, which manifest as en-dash, em-dash, curly quotes showing up as
``\xc3\xa2\xe2\x82\xac\x...`` in the file bytes.

Run from repo root: ``python scripts/_scan_mojibake.py``.
"""
import sys, io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
MOJI_PREAMBLE = b"\xc3\xa2\xe2\x82\xac"


def scan():
    hits = 0
    samples = []
    for p in HERE.glob("*.html"):
        try:
            b = p.read_bytes()
        except OSError:
            continue
        if MOJI_PREAMBLE in b:
            hits += 1
            if len(samples) < 8:
                samples.append((p.name, b.count(MOJI_PREAMBLE)))
    print(f"files with mojibake: {hits}")
    for name, n in samples:
        print(f"  {name}  ({n} occurrences)")


if __name__ == "__main__":
    scan()
