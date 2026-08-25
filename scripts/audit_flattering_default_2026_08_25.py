"""Where does a MISSING value fall through to a decision, count, status or judgement?

THE RULE THIS SWEEPS FOR. A missing field is evidence about our schema. It is never evidence
about a trial, a result, or a check. Where nothing can be read, the output must say so.

THE CONFIRMED INSTANCE. `ssot/projectors2.py` rendered a screening decision as `disposition`,
else "excluded" if `criteria_failed`, else **"included"** -- so 695 of 799 records, including
225 stored EXCLUDED, were displayed to readers as included. The absence of a legacy key
became the most flattering possible answer.

THE ONE THAT ERRS SAFE, and it is the same shape: `projectors.py` counts "records with
eligibility undetermined" as `disposition and not criteria_failed`, so verdict-carrying
records are invisible and the limitation UNDER-reports. Under-reporting a limitation flatters
too; it is only less visible.

Two instances is a pattern, so this sweeps deliberately rather than waiting for a hunt to
trip over the third.

WHAT IT LOOKS FOR, BY SHAPE. A conditional expression or `.get(..., default)` whose FALLBACK
is a decision-like or status-like literal -- "included", "excluded", "low", "none", 0, True --
rather than an explicit absence. It is a lead generator, not a verdict: every hit needs a
human to decide whether the default asserts something the data does not say.

CONTROL FIRST. The sweep must find the known instance -- the screening fallback as it was
written -- before any list from it is read.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Literals that ASSERT something when they stand in for a missing value. A default of "" or
# None or "not recorded" is an explicit absence and is exactly what this wants to see.
_ASSERTIVE = (
    "included", "excluded", "eligible", "low", "high", "moderate", "none", "ok", "pass",
    "passed", "clean", "held", "yes", "no", "true", "false", "0", "1", "complete",
    "unknown", "n/a",
)

# `else <assertive literal>` closing a conditional expression, and `.get(k, <assertive>)`.
_ELSE = re.compile(
    r"""else\s+["'](?P<lit>[A-Za-z0-9/ ]{1,12})["']""")
_GET = re.compile(
    r"""\.get\([^,()]+,\s*(?P<lit>["'][A-Za-z0-9/ ]{1,12}["']|True|False|0|1)\s*\)""")


def assertive(lit):
    return lit.strip().strip("\"'").lower() in _ASSERTIVE


def scan(path):
    hits = []
    try:
        src = io.open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return hits
    for rx in (_ELSE, _GET):
        for m in rx.finditer(src):
            lit = m.group("lit")
            if not assertive(lit):
                continue
            line = src[:m.start()].count("\n") + 1
            ctx = " ".join(src[max(0, m.start() - 130):m.end() + 20].split())
            hits.append((line, lit.strip().strip("\"'"), ctx[-160:]))
    return hits


def main():
    # CONTROL: the screening fallback exactly as it was written must be found.
    probe = ('decided = (p(str(r["disposition"])) if r.get("disposition")\n'
             '           else ("excluded" if r.get("criteria_failed") else "included"))')
    found = any(assertive(m.group("lit")) for m in _ELSE.finditer(probe))
    print("CONTROL: the known screening fallback is detected -> %s" % found)
    negative = 'x = a if a else ""'
    clean = not any(assertive(m.group("lit")) for m in _ELSE.finditer(negative))
    print("CONTROL: an explicit-absence default is NOT flagged -> %s" % clean)
    if not (found and clean):
        print("REFUSED: a control failed. No list is printed.")
        return 2
    print()

    rows = []
    for base in ("ssot", "scripts"):
        for root, dirs, files in os.walk(os.path.join(REPO, base)):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in [f for f in files if f.endswith(".py")]:
                p = os.path.join(root, fn)
                if os.path.basename(p) == os.path.basename(__file__):
                    continue
                for line, lit, ctx in scan(p):
                    rows.append((os.path.relpath(p, REPO), line, lit, ctx))

    L = ["FALLBACKS WHOSE DEFAULT ASSERTS SOMETHING: %d" % len(rows), "",
         "Each is a LEAD, not a verdict. The question for every one is whether a missing",
         "value here produces a claim the data does not support -- a decision, a count, a",
         "status or a judgement -- rather than an explicit absence.", ""]
    for path, line, lit, ctx in sorted(rows):
        L.append("  %s:%d  default=%r" % (path, line, lit))
        L.append("      ...%s" % ctx)
    io.open(os.path.join(REPO, "outputs", "flattering_defaults_2026_08_25.txt"),
            "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:60]))
    return 0


sys.exit(main())
