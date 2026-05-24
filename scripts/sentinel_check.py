"""Pre-push (or pre-commit) sentinel that blocks regressions of every bug class
this session repaired. Run on a set of files passed on the CLI; exit 0 = pass,
exit 1 = block. Designed to be invoked from a git pre-push hook OR from CI.

Rules (each rule = one past-incident bug class):

  R1_python_None_in_js_value_position
      `: None,` or `: None}` in JS object literal context.
      Past incident: commit 4917069b8 - 1,123 FULL_REVIEW dashboards loaded
      as static shells because JS treats `None` as undefined identifier ->
      ReferenceError -> entire RapidMeta object never constructs.

  R2_unescaped_apostrophe_in_single_quoted_js_string
      A single-quoted JS string containing an apostrophe-letter pair like
      `'investigator's choice'` closes the string early, then `s choice'`
      becomes invalid JS. Detected ELACESTRANT_BC_REVIEW.html.

  R3_git_conflict_markers
      `<<<<<<<` / `=======` / `>>>>>>>` left in the file. Detected
      PTAU217_AD_DTA_REVIEW.html (`Unexpected token '<<'`).

  R4_impossible_event_counts
      Any trial block with tE > tN or cE > cN (events exceed sample size).
      Past incident: bulk_clone_audit_first.py extracted AACT percentages as
      integer event counts. fix_event_counts_safe.py now corrects this;
      sentinel prevents new occurrences.

  R5_plotly_title_injection
      The exact injected fragment `${escapeHtml(document.title || "RapidMeta`
      that broke 4 review files by closing Plotly's bundled SVG string early.

  R6_javascript_realData_parses
      Extract the `realData: { ... }` JS literal and verify it parses.
      Belt-and-braces backup for R1/R2/R3 - catches anything they miss.

Exit codes:
  0 = clean (no rule violations)
  1 = blocked (at least one rule violation; details printed to stderr)

Usage:
    python scripts/sentinel_check.py [file1.html file2.html ...]
        (no args -> scan every *.html in repo root)

Bypass (logged):
    SENTINEL_BYPASS=1 python scripts/sentinel_check.py ...
        (will still scan + report, exits 0, appends to .sentinel_bypass.log)
"""
from __future__ import annotations
import os
import re
import sys
import io
import json
import subprocess
from pathlib import Path
from typing import Callable

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)
NONE_VALUE_RE = re.compile(r":\s+None(?=[,}\]\s])")
CONFLICT_RE = re.compile(r"^(<<<<<<< |=======$|>>>>>>> )", re.MULTILINE)
PLOTLY_BAD = '${escapeHtml(document.title || "RapidMeta'


def mask_strings(t: str) -> str:
    out = []
    i = 0
    n = len(t)
    while i < n:
        c = t[i]
        if c in ("'", '"'):
            quote = c
            j = i + 1
            while j < n and t[j] != quote:
                if t[j] == "\\":
                    j += 2
                else:
                    j += 1
            out.append(" " * max(1, j - i + 1))
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


# ---- Rules ------------------------------------------------------------------
def r1_python_none(path: Path, txt: str) -> list[str]:
    out = []
    masked = mask_strings(txt)
    for m in NONE_VALUE_RE.finditer(masked):
        ctx = txt[max(0, m.start() - 20): m.end() + 5]
        out.append(f"R1 None-in-JS-value: ...{ctx.strip()[:100]}")
        if len(out) >= 3:
            break
    return out


def r2_apostrophe_in_js_string(path: Path, txt: str) -> list[str]:
    """Targeted detector for the specific bug class fixed in ELACESTRANT_BC:
    a single-quoted JS string in a known content field (pop:/int:/comp:/out:/
    subgroup:/title:/group:/snippet:/name:/label:) whose value contains an
    unescaped apostrophe that closes the string early.

    The smoking-gun pattern is `field: '...word's word...'` where the `'s`
    breaks the string. We match that exact shape and require an alphanumeric
    word right after the rogue `'` (the JS parser then sees an identifier).

    Avoiding the false-positive class (`{x:'neutral', significant: ...}`)
    requires that after the closing `'` we expect comma/parens/semicolon, NOT
    an alpha character. This rule fires only when the next char is alpha.
    """
    out = []
    # Fields where the bug is plausible.
    field_re = re.compile(
        r"\b(pop|int|comp|out|subgroup|title|group|snippet|name|label|notes|"
        r"description|comment|legend|footnote|caption|aboutText|abstract):\s*'"
    )
    for m in field_re.finditer(txt):
        # Walk forward from m.end() looking for the first unescaped '
        i = m.end()
        n = len(txt)
        while i < n:
            if txt[i] == "\\":
                i += 2
                continue
            if txt[i] == "'":
                # End of string candidate. If next char is alpha, that's the bug.
                if i + 1 < n and txt[i + 1].isalpha():
                    ctx = txt[max(0, i - 40): i + 40]
                    line_no = txt[: i].count("\n") + 1
                    out.append(f"R2 unescaped apostrophe in `{m.group(1)}:` line {line_no}: ...{ctx.strip()[:100]}")
                    if len(out) >= 5:
                        return out
                break
            if txt[i] == "\n":
                break  # most field values are single-line; stop scanning
            i += 1
    return out


def r3_conflict_markers(path: Path, txt: str) -> list[str]:
    out = []
    for m in CONFLICT_RE.finditer(txt):
        line_no = txt[: m.start()].count("\n") + 1
        out.append(f"R3 git conflict marker at line {line_no}: {m.group(1).strip()}")
        if len(out) >= 3:
            break
    return out


def r4_impossible_event_counts(path: Path, txt: str) -> list[str]:
    out = []
    for tm in TRIAL_BLOCK_RE.finditer(txt):
        body = tm.group("body")

        def get(field):
            mm = re.search(rf"\b{field}:\s*(-?\d+|null|None)", body)
            v = mm.group(1) if mm else None
            return int(v) if v and v not in ("null", "None") else None

        tE, tN, cE, cN = get("tE"), get("tN"), get("cE"), get("cN")
        if tE is not None and tN is not None and tE > tN:
            out.append(f"R4 tE>tN in {tm.group(1)}: tE={tE} tN={tN}")
        if cE is not None and cN is not None and cE > cN:
            out.append(f"R4 cE>cN in {tm.group(1)}: cE={cE} cN={cN}")
        if len(out) >= 5:
            break
    return out


def r5_plotly_title_injection(path: Path, txt: str) -> list[str]:
    if PLOTLY_BAD in txt:
        return [f"R5 Plotly SVG-title injection (closes string early): {PLOTLY_BAD[:80]}..."]
    return []


def r6_realdata_parses(path: Path, txt: str) -> list[str]:
    """Use Node to validate the realData object literal. Skipped if Node missing."""
    # Cheap presence check first.
    if "realData:" not in txt:
        return []
    node = "node" if os.name != "nt" else "node.exe"
    # Quick smoke: extract the literal, wrap, eval. We use a tiny inline script.
    start = txt.find("realData:")
    open_idx = txt.find("{", start)
    if open_idx < 0:
        return []
    # Naive brace match (string-aware enough for the well-formed corpus; if
    # this fails on a corrupted file it's a separate violation worth surfacing).
    depth = 0
    end = -1
    i = open_idx
    n = len(txt)
    in_s = False
    in_d = False
    in_t = False
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
                    end = i
                    break
        i += 1
    if end < 0:
        return ["R6 realData block extends past the end of file (string-aware brace match failed)"]
    block = txt[open_idx: end + 1]
    try:
        proc = subprocess.run(
            [node, "-e", "try{new Function('return ('+process.argv[1]+')')()}catch(e){console.error(e.message);process.exit(1)}", block],
            capture_output=True, text=True, timeout=20,
            encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        return []  # No Node, skip
    except subprocess.TimeoutExpired:
        return ["R6 realData parse timed out"]
    if proc.returncode != 0:
        return [f"R6 realData object literal does not parse: {proc.stderr.strip()[:200]}"]
    return []


RULES: list[tuple[str, Callable[[Path, str], list[str]]]] = [
    ("R1_python_None", r1_python_none),
    ("R2_apostrophe", r2_apostrophe_in_js_string),
    ("R3_conflict_markers", r3_conflict_markers),
    ("R4_event_counts", r4_impossible_event_counts),
    ("R5_plotly_title", r5_plotly_title_injection),
    ("R6_realdata_parses", r6_realdata_parses),
]


def main():
    args = sys.argv[1:]
    if args:
        files = [Path(a) for a in args if a.endswith(".html") and Path(a).is_file()]
    else:
        files = sorted(p for p in HERE.glob("*.html") if p.is_file())

    print(f"Sentinel scanning {len(files)} files with {len(RULES)} rules...")

    total_findings = 0
    findings_by_file: dict[str, list[str]] = {}
    for p in files:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            findings_by_file[p.name] = [f"R0 read error: {e!r}"]
            total_findings += 1
            continue
        file_hits = []
        for name, rule in RULES:
            try:
                hits = rule(p, txt) or []
            except Exception as e:
                hits = [f"{name} rule crashed: {e!r}"]
            file_hits.extend(hits)
        if file_hits:
            findings_by_file[p.name] = file_hits
            total_findings += len(file_hits)

    if findings_by_file:
        print(f"\nBLOCK — {total_findings} violations in {len(findings_by_file)} files:", file=sys.stderr)
        for f, hits in sorted(findings_by_file.items()):
            print(f"\n  {f}:", file=sys.stderr)
            for h in hits:
                print(f"    {h}", file=sys.stderr)
        if os.environ.get("SENTINEL_BYPASS") == "1":
            log_path = HERE / ".sentinel_bypass.log"
            with log_path.open("a", encoding="utf-8") as f:
                from datetime import datetime
                f.write(f"\n=== {datetime.utcnow().isoformat()}Z bypass ===\n")
                f.write(json.dumps(findings_by_file, indent=2))
            print(f"\nSENTINEL_BYPASS=1 — exiting 0 (logged to {log_path.name})", file=sys.stderr)
            return 0
        return 1

    print(f"OK — 0 violations across {len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
