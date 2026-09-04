"""Every rendered Contributing-trials table must have exactly `k` data rows.

WHAT THIS CATCHES, AND WHY IT IS NOT A STYLE CHECK. The projector builds the
Contributing-trials table from `inputs.trials[*].by_outcome`, while the pooled
estimate is computed from `results.by_outcome.<oid>.per_trial`. Those are two
containers, and nothing kept them in step:

    ANY WRITE THAT ADDS A TRIAL TO `results...per_trial` OR INCREMENTS `k`
    WITHOUT WRITING `inputs.trials[*].by_outcome` SILENTLY TRUNCATES THE
    RENDERED TABLE.

The reader sees WHICH trials contributed but not WHAT EACH CONTRIBUTED, so the
pool stops being checkable from the page -- which is the whole claim the corpus
rests on. Alirocumab's two missing rows are NCT02289963 and NCT02585778 --
positions 7 and 8 of per_trial, i.e. exactly the pair added by the k=6 -> k=8
recovery, which wrote per_trial and k and not inputs.trials.

THIS IS A DEFECT AGAINST AN EXISTING STANDARD, NOT A NEW REQUIREMENT. Pages in
this corpus already satisfy the assertion. That distinction matters: we have
imposed new requirements on ourselves by accident before.

PROVEN BEFORE THE FIX, NOT AFTER -- AND THAT WINDOW IS PERISHABLE.

    A MUST-FIRE CASE IS A PERISHABLE ASSET. EVERY DEFECT WE REPAIR DESTROYS THE
    EVIDENCE THAT THE DETECTOR FOR IT WORKS, AND THE ONLY WINDOW IS BEFORE THE
    REPAIR.

So this gate was widened and re-proven against the UNREPAIRED corpus, not after.
`--selftest` re-asserts that it can still distinguish the two states.

PAIRING IS SCOPED, NOT POSITIONAL. An earlier version paired the i-th `k` with
the i-th table by document order. SGLT2_HF_REVIEW carries THREE Contributing
tables against TWO pooled lines (its withdrawn pool prints no estimator line),
so that page fell out as `unpairable` -- the gate could not see the page that
prompted it. Each table is now paired with the LAST k declared in the window
between it and the previous table.

AMBIGUITY FAILS CLOSED. A bare `k = N` is not always a declaration: SGLT2_HF
contains the prose "An interval is shown from k = 4", which is not that
section's k. So the structured `estimator X, k = N` wins where present; the bare
form is accepted only when the window holds exactly ONE distinct value, and any
ambiguity is reported as NOT_ASSESSABLE by name rather than guessed.

COVERAGE IS REPORTED, NOT ASSUMED. Every not-assessable page is named. A finding
count is scoped to the assessable fraction and never to the population.
"""
import io
import os
import re
import sys
import glob
import json

def _utf8_stdout():
    """UTF-8 stdout, but ONLY when run as a script.

    A module-level `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, ...)` closes
    the caller's wrapper on plain import, and any importer that installed its own
    then dies at its next print with "I/O operation on closed file". This gate is
    meant to be importable -- other lanes reuse `assess()` -- so the reassignment
    is guarded rather than run at import time.
    """
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CONTRIB_RE = re.compile(
    r"<caption>Table\s+\d+\.\s*Contributing trials</caption>(.*?)</table>", re.S)
K_STRUCT_RE = re.compile(r"estimator\s+[A-Za-z\-]+,\s*k\s*=\s*(\d+)")
K_BARE_RE = re.compile(r"\bk\s*=\s*(\d+)")


def tables_with_k(html):
    """[(rows, k, how)] -- each table paired with the k declared in ITS window."""
    out = []
    prev_end = 0
    for m in CONTRIB_RE.finditer(html):
        window = html[prev_end:m.start()]
        rows = len(re.findall(r"<tr", m.group(1))) - 1
        struct = K_STRUCT_RE.findall(window)
        if struct:
            out.append((rows, int(struct[-1]), "estimator-line"))
        else:
            bare = set(K_BARE_RE.findall(window))
            if len(bare) == 1:
                out.append((rows, int(bare.pop()), "bare-k"))
            elif len(bare) == 0:
                out.append((rows, None, "no-k-in-window"))
            else:
                out.append((rows, None, "ambiguous-k:%s" % ",".join(sorted(bare))))
        prev_end = m.end()
    return out


def object_for(page_path):
    """The SSOT object behind a page, or None. Filename -> slug, then variants."""
    root = os.path.dirname(os.path.abspath(page_path))
    name = os.path.basename(page_path)
    slug = name[:-5].lower().replace("_", "-")
    exact = os.path.join(root, "ssot", slug, slug + ".json")
    if os.path.exists(exact):
        return exact
    for cand in sorted(glob.glob(os.path.join(root, "ssot", slug, "*.json"))):
        if "RECORD" not in os.path.basename(cand).upper():
            return cand
    for trim in ("-auto-full-review", "-review", "-ssot"):
        stem = slug[:-len(trim)] if slug.endswith(trim) else slug
        for cand in sorted(glob.glob(os.path.join(root, "ssot", stem + "*", "*.json"))):
            if "RECORD" not in os.path.basename(cand).upper():
                return cand
    return None


def outcomes_by_k(obj_path):
    """{k: per_trial_row_count} for each outcome the object records."""
    try:
        with open(obj_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return None
    out = {}
    for outcome in (data.get("results", {}).get("by_outcome", {}) or {}).values():
        if isinstance(outcome, dict) and outcome.get("k") is not None:
            out[int(outcome["k"])] = len(outcome.get("per_trial") or [])
    return out


def assess(path):
    """Assert rows == k ONLY where the object holds per-trial rows to render.

    NARROWING THE UNIT, NOT THE STRICTNESS. 20 pages declare a pool whose object
    holds NO per-trial rows. An empty table is the only honest rendering there,
    so firing on them would have created pressure to relax the assertion -- and
    the damage would have come from that pressure, not from the fix. They get a
    named non-passing state instead, because "pool declared, no per-trial rows in
    the object" is a FINDING (the estimate may not be regenerable from its own
    object) and must never be recorded as a pass.
    """
    html = open(path, "rb").read().decode("utf-8", "replace")
    pairs = tables_with_k(html)
    if not pairs:
        return "NO_TABLE", []
    if all(k is None for _, k, _ in pairs):
        return "NOT_ASSESSABLE", pairs

    obj = object_for(path)
    if obj is None:
        return "NO_OBJECT", pairs
    by_k = outcomes_by_k(obj)
    if by_k is None:
        return "OBJECT_UNREADABLE", pairs

    # ORDER MATTERS. A COMPLETE TABLE IS OK WHATEVER FILLED IT. An earlier
    # ordering tested `per_trial == 0` before `rows == k`, which put pages that
    # render correctly (APIXABAN_ACS k=2 rows=2, MITRAL_FUNCMR k=3 rows=3, ...)
    # into the not-a-pass bucket: their rows come from inputs.trials[*].by_outcome
    # while `per_trial` happens to be empty -- the MIRROR of the defect this gate
    # hunts. Judge the rendered artefact first; consult the object only to decide
    # whether an INCOMPLETE table had anything available to render.
    bad, unrenderable, unmatched = [], [], []
    for rows, k, how in pairs:
        if k is None:
            continue
        if rows == k:
            continue
        if k not in by_k:
            unmatched.append((rows, k, how))
        elif by_k[k] == 0:
            unrenderable.append((rows, k, "no per_trial rows in object"))
        else:
            bad.append((rows, k, how))
    if bad:
        return "VIOLATION", bad
    if unrenderable:
        return "POOL_DECLARED_NO_PER_TRIAL", unrenderable
    if unmatched:
        return "NOT_ASSESSABLE", unmatched
    return "OK", pairs


def selftest():
    head = "<caption>Table 5. Contributing trials</caption><tr><th>h</th></tr>"
    row = "<tr><td>a</td></tr>"
    cases = [
        ("complete",   "<p>estimator REML, k = 3.</p>" + head + row * 3 + "</table>", False),
        ("truncated",  "<p>estimator REML, k = 3.</p>" + head + row + "</table>", True),
        ("empty",      "<p>estimator REML, k = 3.</p>" + head + "</table>", True),
        ("bare-k",     "<p>pooled over k = 2.</p>" + head + row + "</table>", True),
        ("prose-trap", "<p>estimator REML, k = 2.</p><p>shown from k = 4</p>"
                       + head + row * 2 + "</table>", False),
    ]
    ok = True
    for label, doc, want in cases:
        pairs = tables_with_k(doc)
        fires = any(k is not None and k != rows for rows, k, _ in pairs)
        good = fires == want
        ok &= good
        print("  selftest %-11s pairs=%s fires=%s expected=%s %s"
              % (label, pairs, fires, want, "OK" if good else "*** FAIL ***"))
    if not ok:
        print("SELFTEST FAILED -- this gate cannot tell the two states apart.")
        return 1
    print("  selftest: the gate can report a failure, and resists the prose trap.")
    return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = sorted(glob.glob(os.path.join(root, "*.html")))
    kinds = {"OK": [], "VIOLATION": [], "NO_TABLE": [], "NOT_ASSESSABLE": [],
             "POOL_DECLARED_NO_PER_TRIAL": [], "NO_OBJECT": [], "OBJECT_UNREADABLE": []}
    detail = {}
    for p in files:
        verdict, info = assess(p)
        name = os.path.basename(p)
        kinds[verdict].append(name)
        detail[name] = info

    assessable = len(kinds["OK"]) + len(kinds["VIOLATION"])
    print("GATE  contributing-table rows == k")
    print("  population    : %d *.html at the repo root" % len(files))
    for key in ("NO_TABLE", "NOT_ASSESSABLE", "NO_OBJECT", "OBJECT_UNREADABLE",
                "POOL_DECLARED_NO_PER_TRIAL", "OK", "VIOLATION"):
        print("      %-16s %5d" % (key, len(kinds[key])))
    print("  COVERAGE      : %d of %d pages carry a table AND declare a usable k."
          % (assessable, len(files)))
    print("                  Findings below are scoped to that fraction.")
    for name in kinds["NOT_ASSESSABLE"] + kinds["NO_OBJECT"]:
        print("      not assessable: %-46s %s"
              % (name, [how for _, _, how in detail[name]]))
    if kinds["POOL_DECLARED_NO_PER_TRIAL"]:
        print()
        print("  POOL DECLARED, NO PER-TRIAL ROWS IN THE OBJECT: %d -- NOT a pass."
              % len(kinds["POOL_DECLARED_NO_PER_TRIAL"]))
        print("  An empty table is the only honest rendering here. Whether the estimate")
        print("  is regenerable from its own object is NOT ESTABLISHED. Separate lead.")
        for name in kinds["POOL_DECLARED_NO_PER_TRIAL"]:
            for rows, k, _ in detail[name]:
                print("      %-50s k=%-3d rows=%d" % (name, k, rows))
    print()
    if kinds["VIOLATION"]:
        print("  VIOLATIONS: %d of %d assessable" % (len(kinds["VIOLATION"]), assessable))
        for name in kinds["VIOLATION"]:
            for rows, k, how in detail[name]:
                print("      %-50s k=%-3d rows=%-3d missing=%-3d [%s]"
                      % (name, k, rows, k - rows, how))
        print()
        print("  A reader of these pages can see WHICH trials contributed but not")
        print("  WHAT EACH CONTRIBUTED, so the pool is not checkable from the page.")
        return 1
    print("  VIOLATIONS: 0 of %d assessable." % assessable)
    return 0


if __name__ == "__main__":
    _utf8_stdout()
    sys.exit(main(sys.argv[1:]))
