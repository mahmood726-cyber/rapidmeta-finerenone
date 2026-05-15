"""Second ship gate: verify a cloned dashboard's inline JS still PARSES.

The leftover scanner proves no base token survived; it does NOT prove the
clone is a working app. An unescaped apostrophe injected into a single-quoted
JS string literal (e.g. condition "Crohn's Disease") is a SyntaxError that
the leftover scanner passes but that breaks the entire dashboard
(lessons.md, 2026-04-30). This module extracts every inline <script> block
and runs `node --check` (syntax only, no execution -> browser globals are
irrelevant) on each.

Returns [] if clean, else [(block_index, first_error_line), ...].
"""
from __future__ import annotations
import io, os, re, subprocess, sys, tempfile

_SCRIPT_RE = re.compile(
    r"<script\b([^>]*)>(.*?)</script\s*>", re.IGNORECASE | re.DOTALL)


def _has_src(attrs: str) -> bool:
    return re.search(r"\bsrc\s*=", attrs, re.IGNORECASE) is not None


def _is_module(attrs: str) -> bool:
    return re.search(r'type\s*=\s*["\']module["\']', attrs, re.IGNORECASE) is not None


def check(html_path: str):
    src = io.open(html_path, "r", encoding="utf-8", errors="replace").read()
    problems = []
    for idx, m in enumerate(_SCRIPT_RE.finditer(src)):
        attrs, body = m.group(1), m.group(2)
        if _has_src(attrs):
            continue
        t = re.search(r'type\s*=\s*["\']([^"\']+)["\']', attrs or "", re.IGNORECASE)
        if t and t.group(1).lower() not in ("module", "text/javascript",
                                            "application/javascript", ""):
            continue  # JSON-LD, template, etc. — not executable JS
        if not body.strip():
            continue
        suffix = ".mjs" if _is_module(attrs) else ".js"
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False,
                                         encoding="utf-8") as fh:
            fh.write(body)
            tmp = fh.name
        try:
            r = subprocess.run(["node", "--check", tmp],
                                capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                err = (r.stderr or r.stdout or "").strip().splitlines()
                first = next((ln for ln in err if "SyntaxError" in ln
                              or "Error" in ln), err[0] if err else "?")
                problems.append((idx, first.strip()[:200]))
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: jscheck.py FILE.html", file=sys.stderr)
        return 2
    p = sys.argv[1]
    if not os.path.isfile(p):
        print(f"not a file: {p}", file=sys.stderr)
        return 2
    probs = check(p)
    if not probs:
        print(f"  [JS-OK] {os.path.basename(p)}")
        return 0
    print(f"  [JS-BROKEN] {os.path.basename(p)}  ({len(probs)} bad script blocks)")
    for idx, err in probs:
        print(f"      block #{idx}: {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
