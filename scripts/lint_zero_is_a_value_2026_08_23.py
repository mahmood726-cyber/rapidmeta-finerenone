"""A legitimate zero tested for truthiness. `k`, `point`, `I2`, `tau2`, event counts, p-values.

# no-control: routed through require_controls. POSITIVE is the line Codex found --
# `if pl.get("point")` in build_tabbed's summary table, which rendered "not pooled" for a
# pooled point of exactly 0.0 beside a computed interval. NEGATIVE is a truthiness test on a
# field where zero is NOT legitimate (a title, a name, a reason string), which must not be
# flagged. If either lands wrong the scan is not reading what it claims.

WHY THIS SHAPE AND NOT THAT ONE LINE. `if pl.get("point")` is false for 0.0, and for a MEAN
DIFFERENCE or a RISK DIFFERENCE zero is the null result -- the most ordinary output a
meta-analysis can produce. The cell hid the one value it most needed to show. The same line
passed `r.get("k")` through the formatter, so `k = 0` had the same problem.

IT WAS LATENT, NOT FIRING: no object currently holds `pooled.point == 0`, which is exactly why
nothing caught it. A defect that needs a value the corpus has never produced is invisible to
every test written from the corpus, and it fires the first time the corpus produces an ordinary
result.

FIELDS WHERE ZERO IS A FINDING, NOT AN ABSENCE:

    point, ci_low, ci_high   0 is the null for MD/RD, and a CI bound of 0 is commonplace
    k                        0 studies is a state a page must be able to say
    I2, tau2                 I2 = 0 IS COMMON IN THIS CORPUS AND IS A RESULT -- "no observed
                             heterogeneity" -- not a missing value
    events, n_events         0 events in an arm is data; the zero-cell correction exists for it
    p, p_value               a p of 0 (below display precision) is a real report
    downgrades, serious      0 GRADE downgrades is what HIGH certainty MEANS

THE GENERAL RULE: use `is not None` for anything numeric. `or` and bare truthiness are for
strings and containers, where empty and absent are the same thing. For a number they are not.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "zero_is_a_value_2026_08_23.json")

SOURCES = ["ssot/build_tabbed.py", "ssot/projectors.py", "ssot/projectors2.py",
           "ssot/build_app_v2.py", "ssot/paper_projector.py"]

# Numeric fields where zero is a legitimate, meaningful value.
NUMERIC = (r"point|ci_low|ci_high|\bk\b|i2|I2|tau2|tau_2|events|n_events|"
           r"p_value|\bp\b|downgrades|serious|weight|se|var|z|q_stat|df|"
           r"n_analysed|n_randomised|enrolled")

# `if x.get("field")` / `if x["field"]` / `x.get("field") or ...` / `if not x.get("field")`
# THE TERNARY FORM MUST BE IN HERE AND WAS NOT. The line this lint exists for is
# `("%s %s (%s to %s)" % (...) if pl.get("point") else "not pooled")` -- a conditional
# EXPRESSION, where the token after the test is `else`, not `:` or `and`. The first version
# required a statement terminator and therefore could not see its own founding case. The
# hand-set control refused before any count was printed.
PATTERNS = [
    re.compile(r"""if\s+[\w\.]+\.get\(\s*["'](%s)["']\s*\)\s*(?::|and\b|or\b|else\b|\))"""
               % NUMERIC),
    re.compile(r"""[\w\.]+\.get\(\s*["'](%s)["']\s*\)\s+or\s+""" % NUMERIC),
    re.compile(r"""if\s+not\s+[\w\.]+\.get\(\s*["'](%s)["']\s*\)""" % NUMERIC),
    re.compile(r"""if\s+[\w]+\[\s*["'](%s)["']\s*\]\s*(?::|and\b|or\b|else\b|\))""" % NUMERIC),
]
SAFE = re.compile(r"is\s+not\s+None|is\s+None|isinstance|!=\s*None")


def scan_text(src):
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        s = line.strip()
        if s.startswith("#") or SAFE.search(line):
            continue
        for pat in PATTERNS:
            m = pat.search(line)
            if m:
                out.append((i, m.group(1), re.sub(r"\s+", " ", s)[:110]))
                break
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    positive = 'if pl.get("point") else "not pooled"'
    negative = 'if canon.get("title") else ""'
    require_controls(
        "zero_is_a_value",
        ("the line Codex found -- `if pl.get(\"point\")` -- is detected",
         bool(scan_text(positive)), True),
        ("a truthiness test on a STRING field (`title`) is not flagged -- empty and absent "
         "are the same thing for a string",
         bool(scan_text(negative)), True))

    findings, per_file = [], {}
    for rel in SOURCES:
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            continue
        hits = scan_text(io.open(p, encoding="utf-8", errors="replace").read())
        if hits:
            per_file[rel] = len(hits)
        for line, field, text in hits:
            findings.append({"file": rel, "line": line, "field": field, "text": text})

    print("")
    print("ZERO TESTED FOR TRUTHINESS, %d source file(s)" % len(SOURCES))
    print("")
    print("   sites where a legitimate zero would be read as absent   %3d" % len(findings))
    for rel, n in sorted(per_file.items(), key=lambda kv: -kv[1]):
        print("      %-34s %3d" % (rel, n))
    print("")
    for f in findings[:30]:
        print("   %-26s:%-5d [%s]  %s"
              % (f["file"].split("/")[-1], f["line"], f["field"], f["text"][:74]))
    print("")
    print("I2 = 0 IS COMMON IN THIS CORPUS AND IS A RESULT -- 'no observed heterogeneity' --")
    print("not a missing value. 0 events is data. 0 GRADE downgrades is what HIGH certainty")
    print("MEANS. Use `is not None` for numbers; bare truthiness is for strings and")
    print("containers, where empty and absent are the same thing. For a number they are not.")
    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"findings": findings, "per_file": per_file},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    if findings:
        sys.exit("REFUSED: %d site(s) test a legitimate zero for truthiness. A defect that "
                 "needs a value the corpus has never produced is invisible to every test "
                 "written from the corpus, and fires the first time an ordinary result "
                 "appears." % len(findings))


if __name__ == "__main__":
    main()
