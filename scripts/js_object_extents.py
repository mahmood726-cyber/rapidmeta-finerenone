"""
Shared JS-object brace-walker utility.

Used in three+ places before this refactor (Sentinel rule's _find_block_end,
audit_data_integrity.py's parse_realdata, dose-response engine extractor).
Centralised here so future code can import rather than re-implement.

The walker is intentionally simple: it counts {} pairs forward from a given
start offset and returns the offset of the matching close. It does NOT
attempt to be a real JS parser — it's confused by braces inside strings or
template literals. For RapidMeta dashboards this is fine because object
literals don't contain raw '{' or '}' inside their string values (the
templates use parentheses or have escaped them where they exist).

Public API:
    find_block_end(text, start)
        Walk forward from `start` (which should be at or before an opening
        '{'). Returns offset of the matching close '}', or -1 if unbalanced.

    extract_object_literal(text, anchor_pattern)
        Find the FIRST regex match of `anchor_pattern` (e.g. r'realData\\s*:\\s*\\{')
        and return the (open_offset, close_offset, body) tuple, or None.

    line_of(text, offset)
        Convenience: 1-based line number containing `offset`.

Examples:
    >>> from js_object_extents import find_block_end
    >>> src = "x = { a: 1, b: { c: 2 } }; y = 3;"
    >>> find_block_end(src, 4)   # opening { at offset 4
    24                            # closing } at offset 24
"""
from __future__ import annotations
import re
from typing import Optional, Tuple


def find_block_end(text: str, start: int, max_walk: int = 1_000_000) -> int:
    """Walk forward from `start` and return the offset of the '}' that
    closes the first '{' encountered at or after `start`. Returns -1 if
    unbalanced or if `max_walk` chars elapse without closing.

    Caveats: doesn't track strings/template literals. For HTML+JS files
    where object literals don't contain raw braces inside strings, this is
    fine.
    """
    depth = 0
    started = False
    limit = min(len(text), start + max_walk)
    for j in range(start, limit):
        c = text[j]
        if c == '{':
            depth += 1
            started = True
        elif c == '}':
            depth -= 1
            if started and depth == 0:
                return j
    return -1


def extract_object_literal(text: str, anchor_pattern: str) -> Optional[Tuple[int, int, str]]:
    """Find the first regex match of `anchor_pattern`, then return
    (open_offset, close_offset, body) where body is the contents between
    the matched `{` and its closing `}`.

    `anchor_pattern` should match up to and including the opening '{'.
    Example: r'realData\\s*:\\s*\\{' to find the realData literal.

    Returns None if no match or unbalanced.
    """
    m = re.search(anchor_pattern, text)
    if not m:
        return None
    # Find the '{' (assumed to be at or just before m.end())
    brace_open = text.rfind('{', m.start(), m.end() + 1)
    if brace_open < 0:
        # Pattern didn't include the brace; look forward
        brace_open = text.find('{', m.end())
        if brace_open < 0:
            return None
    end = find_block_end(text, brace_open)
    if end < 0:
        return None
    return (brace_open, end, text[brace_open + 1:end])


def line_of(text: str, offset: int) -> int:
    """1-based line number containing `offset`."""
    return text.count('\n', 0, offset) + 1


# Self-test on import (cheap; no I/O)
if __name__ == '__main__':
    src = "x = { a: 1, b: { c: 2 } }; y = 3;"
    assert find_block_end(src, 4) == 24, f'simple nested: got {find_block_end(src, 4)}'
    assert find_block_end(src, 0) == 24, 'walks past leading non-brace chars'
    assert find_block_end("{ unclosed", 0) == -1, 'unbalanced returns -1'
    assert line_of("a\nb\nc", 4) == 3, 'line_of'
    res = extract_object_literal("foo = {x: 1, y: 2}; bar=3", r'foo\s*=\s*\{')
    assert res is not None and res[2] == 'x: 1, y: 2', f'extract: {res}'
    print('js_object_extents: self-tests pass')
