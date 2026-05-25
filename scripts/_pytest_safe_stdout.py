"""Helper to fix the well-documented pytest-capture-vs-stdout-reassignment bug.

Several scripts in this repo do:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                       errors="replace")

at module-load time so they don't crash on Windows when printing non-ASCII.
But this CLOSES the original stdout file pytest uses for capture, breaking
ALL subsequent collection ("ValueError: I/O operation on closed file").

The fix per CLAUDE.md/lessons.md is: only reassign when NOT under pytest.

This module batch-patches every fixer script in scripts/ to wrap its stdout
reassignment in `if "pytest" not in sys.modules:` so the tests can import
them safely. Idempotent.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

PAT = re.compile(
    r'^if hasattr\(sys\.stdout, "buffer"\):\n'
    r'    sys\.stdout = io\.TextIOWrapper\(sys\.stdout\.buffer, encoding="utf-8", errors="replace"\)\n',
    re.MULTILINE,
)

REPL = (
    'if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):\n'
    '    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")\n'
)


def main():
    n_fixed = 0
    for p in HERE.glob("*.py"):
        if p.name in ("_pytest_safe_stdout.py", "_disp_types_audit.py"):
            continue
        txt = p.read_text(encoding="utf-8")
        if 'sys.stdout = io.TextIOWrapper' not in txt:
            continue
        if 'pytest' in txt and 'sys.modules' in txt:
            continue  # already guarded
        new_txt = PAT.sub(REPL, txt, count=1)
        if new_txt != txt:
            p.write_text(new_txt, encoding="utf-8")
            n_fixed += 1
            print(f"  guarded: {p.name}")
    print(f"\nGuarded {n_fixed} scripts.")


if __name__ == "__main__":
    main()
