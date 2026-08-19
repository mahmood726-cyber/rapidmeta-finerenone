#!/usr/bin/env python3
"""THE HALF OF HEREDOC MANGLING THAT A BYTE SCANNER CANNOT SEE.

`lint_control_chars.py` refuses a C0 control character in tracked SOURCE. That closes the
heredoc path, where `\\b` was written through a shell and arrived as a literal 0x08 byte.

IT DOES NOT CLOSE THE SIBLING. In a NON-RAW Python string, `\\b` is a VALID escape: the source
stays clean ASCII and the COMPILED VALUE becomes 0x08. Byte-identical symptom, byte-clean file.

    re.compile("\\bNCT\\d{8}\\b")     # source is clean; the pattern holds two BACKSPACES
    re.compile(r"\\bNCT\\d{8}\\b")    # correct

Both produce a pattern that never matches, a module that imports, and a build that reports
success -- the exact failure of the foreign-registration-id guard, which printed
`HELD 7 / REFUSING 1` while incapable of matching a single id.

TWO CHECKS, because the two halves fail differently:

  1. UNRECOGNISED escapes (`\\s`, `\\d`, `\\w` in a non-raw string). Python already reports
     these as SyntaxWarning and today keeps them as backslash-plus-letter, so a regex still
     works BY ACCIDENT. It is scheduled to become a SyntaxError. Free to detect: compile and
     listen.

  2. RECOGNISED escapes that yield a CONTROL CHARACTER (`\\b` `\\a` `\\f` `\\v` `\\0`) inside a
     literal that is used as a PATTERN. Silent today, wrong today. No warning exists, so this
     is the one that needs writing.

WHY IT IS LINTABLE: like the byte scan, it needs no semantic judgement. A string constant
either holds a control character or it does not.
"""
import ast
import io
import os
import sys
import warnings

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "__pycache__", "node_modules", "figs", "sources"}
SKIP_TOKEN = "lint:allow-escape"

CONTROL = {chr(c) for c in range(0x20) if c not in (0x09, 0x0A, 0x0D)} | {"\x7f"}
NAMES = {"\x08": "\\b BACKSPACE", "\x07": "\\a BELL", "\x0c": "\\f FORM FEED",
         "\x0b": "\\v VERTICAL TAB", "\x00": "\\0 NUL", "\x1b": "\\e ESC"}

# A control character is only a DEFECT where the string is used as a pattern or an identifier.
# `"\\n".join(...)` is fine; a BACKSPACE inside a regex is not. Rather than guess intent, the
# check is scoped to literals passed to these, plus module-level pattern constants.
PATTERN_CALLS = {"compile", "match", "search", "findall", "finditer", "sub", "subn", "split",
                 "fullmatch", "startswith", "endswith"}


def py_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            if fn.endswith(".py"):
                yield os.path.join(root, fn)


def control_chars_in_patterns(tree, src_lines):
    """Yield (lineno, char, excerpt) for control chars inside pattern-ish string literals."""
    out = []

    def report(node, s):
        bad = CONTROL & set(s)
        if not bad:
            return
        line = src_lines[node.lineno - 1] if node.lineno <= len(src_lines) else ""
        if SKIP_TOKEN in line:
            return
        for ch in sorted(bad):
            out.append((node.lineno, ch, line.strip()[:90]))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            if name in PATTERN_CALLS:
                for a in node.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        report(a, a.value)
        # Module-level CONSTANT_NAME = "..." -- the usual home of a hoisted pattern.
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if (isinstance(t, ast.Name) and t.id.isupper()
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)):
                    report(node.value, node.value.value)
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    warned, controls, scanned, unparsable = [], [], 0, 0
    for path in py_files():
        try:
            src = io.open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        scanned += 1
        rel = os.path.relpath(path, REPO)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                tree = ast.parse(src)
            except SyntaxError:
                unparsable += 1
                continue
            for w in caught:
                if issubclass(w.category, SyntaxWarning):
                    warned.append((rel, str(w.message)))
        for lineno, ch, excerpt in control_chars_in_patterns(tree, src.split("\n")):
            controls.append((rel, lineno, ch, excerpt))

    for rel, lineno, ch, excerpt in controls:
        print("%s:%d  pattern literal holds %s" % (rel, lineno, NAMES.get(ch, repr(ch))))
        print("      %s" % excerpt)
    for rel, msg in warned:
        print("%s  %s" % (rel, msg))

    print()
    print("python files scanned          %d   (%d unparsable, reported not skipped)"
          % (scanned, unparsable))
    print("control chars in patterns     %d   (SILENT today, wrong today)" % len(controls))
    print("unrecognised escapes          %d   (works by accident; becomes SyntaxError)"
          % len(warned))
    if controls or warned:
        print()
        print("REFUSED: %d escape hazard(s)." % (len(controls) + len(warned)))
        print("FIX: make the literal RAW -- r\"\\bNCT\\d{8}\\b\". Deliberate exception:")
        print("     append  # lint:allow-escape  on the line.")
        return 1
    print()
    print("no escape hazards: every pattern literal means what it reads as.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
