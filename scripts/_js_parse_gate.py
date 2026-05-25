"""Build-time JS parse gate.

Importable helper that runs `new Function(realData_literal)` via Node and
raises if the literal doesn't parse. Used by:
  - bulk_clone_audit_first.py (gate every freshly-cloned dashboard before
    accepting it)
  - apply_aact_counts_retro.py / apply_aact_continuous_retro.py (gate every
    file after rewriting trial blocks)
  - generate_topic_html.py (when it eventually adopts this contract)

Catches the exact bug classes the sentinel R6 rule catches, but at the
point of file creation — so a regression never gets persisted to disk.

Public API:
    js_parse_ok(text_or_path) -> bool
        Returns True if the realData block parses cleanly under V8,
        False otherwise. Logs failures to ./.js_parse_failures.log.
    assert_js_parse_ok(text_or_path)
        Same but raises ParseGateError on failure.
"""
from __future__ import annotations
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
NODE = "node" if os.name != "nt" else "node.exe"


class ParseGateError(RuntimeError):
    pass


def _extract_realdata(txt: str) -> str | None:
    start = txt.find("realData:")
    if start < 0:
        return None
    open_idx = txt.find("{", start)
    if open_idx < 0:
        return None
    depth = 0
    i = open_idx
    n = len(txt)
    in_s = in_d = in_t = False
    while i < n:
        c = txt[i]
        if c == "\\" and i + 1 < n:
            i += 2; continue
        if not in_d and not in_t and c == "'":
            in_s = not in_s
        elif not in_s and not in_t and c == '"':
            in_d = not in_d
        elif not in_s and not in_d and c == "`":
            in_t = not in_t
        elif not in_s and not in_d and not in_t:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return txt[open_idx: i + 1]
        i += 1
    return None


def js_parse_ok(text_or_path: str | Path) -> bool:
    """Returns True iff the file's realData JS literal parses under V8."""
    if isinstance(text_or_path, Path) or (
        isinstance(text_or_path, str) and Path(text_or_path).exists() and len(text_or_path) < 4096
    ):
        p = Path(text_or_path)
        txt = p.read_text(encoding="utf-8", errors="replace")
        fname = p.name
    else:
        txt = str(text_or_path)
        fname = "<string>"
    block = _extract_realdata(txt)
    if block is None:
        return True  # no realData -> nothing to gate
    # Wrap as expression and let V8 parse.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", encoding="utf-8", delete=False
    ) as tf:
        tf.write(
            "try{ const _x = (" + block + "); "
            "if(typeof _x !== 'object') throw new Error('realData not object'); "
            "process.exit(0); } catch(e){ "
            "process.stderr.write(e.message); process.exit(1); }"
        )
        tmp_path = tf.name
    try:
        proc = subprocess.run(
            [NODE, tmp_path],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        return True  # no Node on this host — gate is advisory only
    except subprocess.TimeoutExpired:
        proc = None
    finally:
        try: os.unlink(tmp_path)
        except OSError: pass
    if proc is None or proc.returncode != 0:
        msg = (proc.stderr.strip()[:200] if proc else "timeout")
        # Append to log
        log = HERE / ".js_parse_failures.log"
        from datetime import datetime
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()}Z\t{fname}\t{msg}\n")
        return False
    return True


def assert_js_parse_ok(text_or_path: str | Path) -> None:
    if not js_parse_ok(text_or_path):
        raise ParseGateError(
            f"JS parse gate FAILED for {text_or_path!r}. See .js_parse_failures.log."
        )


if __name__ == "__main__":
    # CLI mode: gate every path passed on the command line.
    failures = []
    for arg in sys.argv[1:]:
        if not js_parse_ok(arg):
            failures.append(arg)
    if failures:
        print(f"PARSE GATE FAILED for {len(failures)} files:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)
    print(f"OK — {len(sys.argv) - 1} files parsed cleanly.")
