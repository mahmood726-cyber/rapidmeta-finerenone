"""Shared I/O utilities for the cardiology mortality atlas pipeline.

Centralizes UTF-8 stdout wrapping (Windows cp1252 crashes on unicode prints)
and Markdown table cell escaping (formula injection guard for Excel/Sheets,
plus literal `|` escape so trial titles don't break tables).
"""
import io
import re
import sys
from pathlib import Path

# All scripts share this base directory — resolved from this module's location
BASE_DIR = Path(__file__).resolve().parent


def ensure_utf8_stdout():
    """Wrap sys.stdout in UTF-8 with errors='replace'.

    Idempotent: safe to call multiple times. Required on Windows where the
    default cp1252 codec crashes on unicode characters in print().
    """
    if not isinstance(sys.stdout, io.TextIOWrapper):
        return
    if sys.stdout.encoding and sys.stdout.encoding.lower().replace('-', '') == 'utf8':
        return
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding='utf-8', errors='replace'
        )
    except (AttributeError, ValueError):
        pass  # already wrapped or non-buffer stdout (test capture)


# Cells starting with these characters are interpreted as formulas by
# Excel/Google Sheets if a Markdown table is pasted into a spreadsheet.
# Per OWASP "CSV Injection" advice, prepend a single quote.
_FORMULA_PREFIXES = ('=', '+', '@', '\t', '\r')


def md_cell(value):
    """Escape a value for safe inclusion in a Markdown table cell.

    Handles:
      - None / non-string values via str() coercion
      - Literal pipe `|` (would break table columns) → `\\|`
      - Newlines / carriage returns → space
      - Formula injection (cells starting with =,+,@,\\t,\\r) → prepend `'`
    """
    if value is None:
        return ''
    s = str(value)
    # Strip newlines first (would break the row)
    s = s.replace('\r', ' ').replace('\n', ' ')
    # Escape pipes
    s = s.replace('|', '\\|')
    # Formula injection guard
    if s and s[0] in _FORMULA_PREFIXES:
        s = "'" + s
    return s


# NCT identifier validation — used by mining script before URL construction
_NCT_RE = re.compile(r'^NCT\d{8}$')


def is_valid_nct(nct_id):
    """Return True iff `nct_id` is a well-formed CT.gov NCT identifier."""
    return bool(nct_id) and isinstance(nct_id, str) and _NCT_RE.match(nct_id) is not None
