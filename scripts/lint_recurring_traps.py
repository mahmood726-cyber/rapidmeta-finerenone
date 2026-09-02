# -*- coding: utf-8 -*-
"""Four traps that recurred WITH THE RULE ALREADY WRITTEN DOWN. Now checks in the path.

    stdout double-wrap        5 occurrences, each time "it looked like a different situation"
    unanchored substring      9
    control bytes in source   heredocs eat backslashes; `\\b` collapses to a literal 0x08
    except-swallows-import    an ImportError caught by `except Exception: continue`,
                              producing a CORPUS CONCLUSION from a module that never loaded

⭐ WHY A LINT AND NOT A NOTE. Every one of these was already written down when it recurred.
A RULE RECALLED BY SITUATION FAILS WHEN THE SITUATION IS DISGUISED -- the fifth stdout wrap
did not look like the first four, and the ninth substring match did not look like a
substring match, it looked like "checking whether the id is on the page". The defence has to
sit in the path, not in a document somebody has to remember to have read.

⛔ DETECTION IS BY `ast` AND BY BYTES, NOT BY REGEX OVER SOURCE. Using a regex to find
unanchored-regex bugs is how you get a lint with the defect it polices. The one regex-shaped
check here -- control bytes -- reads the file as BYTES precisely because grep renders 0x08
as blank and the offending line looks correct on screen.

⭐ EVERY CHECK SHIPS WITH A CASE THAT MUST FIRE (`--selftest`). A detector that has only ever
returned negatives is indistinguishable from a broken one, and that is most dangerous when
the zero flatters us. `--selftest` runs each detector over a synthetic file that MUST trip
it, and REFUSES if any detector reports clean. Number-absence cannot distinguish a real
absence from a broken detector; this is how that is settled.

⚠️ RATCHET, NOT ULTIMATUM. The corpus predates the rules, so a bare gate would refuse every
lane -- the exact defect that made check_page_format refuse 148 of 149 pages. The baseline
records today's violations; a file may not gain a NEW one. Existing ones are OWED, NOT
CLEARED.

    python scripts/lint_recurring_traps.py            report
    python scripts/lint_recurring_traps.py --selftest prove every detector can fire
    python scripts/lint_recurring_traps.py --gate     refuse on NEW violations
    python scripts/lint_recurring_traps.py --write-baseline
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import os
import shutil
import tempfile
import subprocess
import sys
import time


_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_BASELINE = os.path.join(_HERE, "baselines", "recurring_traps_baseline.json")

# Control bytes that must never appear in source. 0x09 tab, 0x0a LF, 0x0d CR are legal.
_BAD_BYTES = set(range(0x00, 0x09)) | {0x0B, 0x0C} | set(range(0x0E, 0x20))

# Identifier-ish names whose containment test is almost always meant as identity.
# ⚠️ NOT "names I expect to see" -- this list came from the nine real occurrences.
_ID_NAMES = ("nct", "pmid", "doi", "trial_id", "cd", "pubn", "acronym", "accession",
             "identifier", "trial", "reg_id", "registration")


def _is_id_name(node):
    if isinstance(node, ast.Name):
        n = node.id.lower()
    elif isinstance(node, ast.Attribute):
        n = node.attr.lower()
    elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
            and isinstance(node.slice.value, str):
        n = str(node.slice.value).lower()
    else:
        return False
    return any(k == n or n.startswith(k + "_") or n.endswith("_" + k) for k in _ID_NAMES)


class _Trap(ast.NodeVisitor):
    def __init__(self):
        self.hits = []

    # (1) stdout double-wrap at MODULE scope
    def visit_Assign(self, node):
        for t in node.targets:
            # ⭐ EXTENDED 2026-09-01 by the counterpart lane, which had independently built
            # a second stdout lint. TWO LINTS POLICING ONE TRAP IS HOW A TRAP SURVIVES BOTH,
            # so that one is retired and its two extra arms are folded in here:
            #   `sys.stderr`  -- same mechanism, same closed buffer, same ValueError
            #   module-level `try:` body -- see _mark_module_scope; it RUNS AT IMPORT
            if (isinstance(t, ast.Attribute) and t.attr in ("stdout", "stderr")
                    and isinstance(t.value, ast.Name) and t.value.id == "sys"
                    and getattr(node, "_module_scope", True)):
                self.hits.append(("stdout_double_wrap", node.lineno,
                                  "sys.%s reassigned at module scope" % t.attr))
        self.generic_visit(node)

    # (2) unanchored substring used as an identity test
    def visit_Compare(self, node):
        for op, cmp_ in zip(node.ops, node.comparators):
            if isinstance(op, ast.In) and _is_id_name(node.left):
                self.hits.append(("unanchored_substring", node.lineno,
                                  "identifier used in a substring test"))
        self.generic_visit(node)

    # (4) a handler that swallows an ImportError and continues
    def visit_Try(self, node):
        has_import = any(isinstance(n, (ast.Import, ast.ImportFrom))
                         for b in node.body for n in ast.walk(b))
        if not has_import:
            self.generic_visit(node)
            return
        for h in node.handlers:
            broad = h.type is None or (isinstance(h.type, ast.Name)
                                       and h.type.id in ("Exception", "BaseException"))
            swallows = all(isinstance(s, (ast.Pass, ast.Continue)) for s in h.body)
            if broad and swallows:
                self.hits.append(("except_swallows_import", h.lineno,
                                  "an ImportError here becomes a silent skip"))
        self.generic_visit(node)


def _mark_module_scope(tree):
    """Only module-level assignments count for (1). One inside `if __name__` is fine.

    ⛔ A MODULE-LEVEL `try:` BODY IS STILL MODULE SCOPE. It runs at import exactly like a bare
    statement, so `try: sys.stdout = ... except Exception: pass` closes the caller's buffer
    just the same -- and reads as MORE careful, which is why it survives review. Marked here
    rather than in the visitor so the two paths cannot drift apart.

    ⚠️ `if __name__` is deliberately NOT propagated: it is the sanctioned fix.
    """
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child._module_scope = isinstance(node, ast.Module)
    for node in tree.body:
        if isinstance(node, ast.Try):
            for sub in node.body:
                sub._module_scope = True


def _scan_bytes(raw, path):
    """Detectors over BYTES. Returns hits, or None if the source does not parse.

    ONE detector path for both the worktree and a revision -- a second copy of a traversal
    is a second copy of every bug not yet found in it.
    """
    hits = []
    for i, line in enumerate(raw.split(chr(10).encode()), 1):
        bad = sorted({b for b in line if b in _BAD_BYTES})
        if bad:
            hits.append(("control_bytes", i,
                         "literal %s in source -- grep renders it blank"
                         % ", ".join("0x%02x" % b for b in bad)))
    try:
        tree = ast.parse(raw.decode("utf-8", "replace"), filename=path)
    except SyntaxError:
        return hits, False          # byte-level hits survive; the AST ones cannot be known
    _mark_module_scope(tree)
    t = _Trap()
    t.visit(tree)
    return hits + t.hits, True


def scan(path):
    """(hits, state) -- state names why a file yielded nothing, so a zero is readable."""
    raw, why = None, None
    for attempt in (0, 1):
        # RETRY ONCE, DELIBERATELY. Four lanes write this worktree; a file held open for a
        # few milliseconds is a LOCK, not a verdict. This is not softening the check -- the
        # caller still REFUSES below if the second read fails. What it removes is the
        # transient that would make a fail-closed gate fire at random.
        try:
            raw = open(path, "rb").read()
            break
        except OSError as exc:
            why = exc
            if attempt == 0:
                time.sleep(0.15)
    if raw is None:
        return [], "UNREADABLE: %s" % why
    hits, parsed = _scan_bytes(raw, path)
    return hits, "SCANNED" if parsed else "UNPARSABLE: %s" % os.path.basename(path)


def _staged_py():
    """Repo-relative .py paths staged for this commit.

    A git failure RAISES. Returning an empty list would make the hook check NOTHING and
    pass, which is the vacuous pass this repo keeps finding.

    text=True decodes with the LOCALE codec (cp1252 here); lint_subprocess_decode.py
    refused this very line inside the hook, before this lint got to speak. Encoding named.
    """
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                         cwd=_ROOT, capture_output=True,
                         encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise SystemExit("REFUSED: could not list staged files (%s). A hook that cannot see "
                         "the commit must not pass it." % out.stderr.strip()[:160])
    return [l.strip().replace(chr(92), "/") for l in out.stdout.splitlines()
            if l.strip().endswith(".py")]


def _rev_py_files(rev):
    """Every .py at REV, from the object store -- no checkout, no worktree."""
    out = subprocess.run(["git", "ls-tree", "-r", "--name-only", rev],
                         cwd=_ROOT, capture_output=True, encoding="utf-8",
                         errors="replace")
    if out.returncode != 0:
        raise SystemExit("REFUSED: cannot list %s (%s)" % (rev, out.stderr.strip()[:140]))
    return sorted(l.strip() for l in out.stdout.splitlines() if l.strip().endswith(".py"))


def _rev_blob(rev, path):
    """(bytes, state) for one blob at REV. A failure is NAMED, never returned as empty."""
    out = subprocess.run(["git", "show", "%s:%s" % (rev, path)], cwd=_ROOT,
                         capture_output=True)
    if out.returncode != 0:
        return None, "UNREADABLE: %s" % out.stderr.decode("utf-8", "replace").strip()[:90]
    return out.stdout, "READ"


def assess_rev(rev):
    """Scan every .py AT A REVISION. Same detectors, same shapes, different source of bytes.

    WHY THIS EXISTS, AND IT IS NOT A CONVENIENCE. A baseline is only correct for the tree
    it was measured on. This worktree sits on a branch 304 commits BEHIND origin/main, so a
    baseline built from these files would omit whatever main has that this branch does not --
    and the first person to run the gate on main would meet a wall of violations reported as
    NEW that have in fact been there for weeks. That is the ultimatum failure again: a gate
    that refuses everything is as useless as one that refuses nothing.
    """
    found, states, unscanned = {}, {}, []
    allfiles = _rev_py_files(rev)
    for rel in allfiles:
        raw, st = _rev_blob(rev, rel)
        if raw is None:
            states["UNREADABLE"] = states.get("UNREADABLE", 0) + 1
            unscanned.append((rel, st))
            continue
        hits, parsed = _scan_bytes(raw, rel)
        if not parsed:
            states["UNPARSABLE"] = states.get("UNPARSABLE", 0) + 1
            unscanned.append((rel, "UNPARSABLE at %s" % rev))
            continue
        states["SCANNED"] = states.get("SCANNED", 0) + 1
        if hits:
            found[rel] = sorted({(k, l) for k, l, _w in hits})
    # The POPULATION is returned, never inferred from the survivors -- a count of files that
    # produced a hit is not a count of files measured, and the sum check below depends on it.
    return found, states, unscanned, allfiles


def assess(rels, root=None):
    """Scan a list of repo-relative paths. Returns (found, states, UNSCANNED).

    ⛔ EXTRACTED SO THE SELFTEST EXERCISES THIS CODE AND NOT A COPY OF IT. The refusal in
    main() is a two-line consequence of `unscanned` being right; a selftest that rebuilt the
    loop would prove its own reimplementation correct and prove nothing about the gate --
    which is the shape of a control that is green and worthless.
    """
    root = _ROOT if root is None else root
    found, states, unscanned = {}, {}, []
    for rel in rels:
        hits, state = scan(os.path.join(root, rel))
        kind = state.split(":")[0]
        states[kind] = states.get(kind, 0) + 1
        if kind != "SCANNED":
            unscanned.append((rel, state))
        if hits:
            found[rel] = sorted({(k, l) for k, l, _w in hits})
    return found, states, unscanned


def candidates():
    """EVERY tracked .py under the repo -- enumerated, never grepped for expected names.

    ⛔ HALF THIS WEEK'S FALSE ABSENCES CAME FROM SEARCHING FOR A NAME. `grep 'len(records)'`
    found nothing because the variable was `recs`. This walks the tree instead.
    """
    out = []
    for base, _dirs, files in os.walk(_ROOT):
        parts = base.replace("\\", "/").split("/")
        if any(p in (".git", "__pycache__", "node_modules", "vendor") for p in parts):
            continue
        for fn in files:
            if fn.endswith(".py"):
                out.append(os.path.relpath(os.path.join(base, fn), _ROOT).replace("\\", "/"))
    return sorted(out)


SELFTEST_SRC = '''
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer)      # (1) must fire
def f(nct, page):
    if nct in page:                                    # (2) must fire
        return True
try:
    import nonexistent_module_xyz
except Exception:
    pass                                               # (4) must fire
'''


def _plant(*lines):
    """Join literal lines into a source string. NO ESCAPE SEQUENCES -- the arms below are
    plant sources, and a backslash in a plant is one more thing that can be eaten in
    transit and turn a firing plant into a silent one."""
    return chr(10).join(lines) + chr(10)


# ⭐ THE TWO FOLDED-IN ARMS, EACH PLANTED SEPARATELY WITH A CLEAN SIBLING. Without the
# siblings a detector that refuses EVERYTHING passes both plants, and a check that can only
# refuse is a wall, not a check.
_WRAP_O = "io.TextIOWrapper(sys.stdout.buffer)"
_WRAP_E = "io.TextIOWrapper(sys.stderr.buffer)"
_ARM_CASES = (
    ("ARM stderr: sys.stderr at module scope",
     _plant("import io, sys", "sys.stderr = " + _WRAP_E), 1),
    ("ARM try: rebind in a module-level try body",
     _plant("import io, sys", "try:", "    sys.stdout = " + _WRAP_O,
            "except Exception:", "    pass"), 1),
    ("sibling: guarded by __main__ -- the sanctioned fix",
     _plant("import io, sys", "if __name__ == '__main__':",
            "    sys.stdout = " + _WRAP_O), 0),
    ("sibling: inside a function",
     _plant("import io, sys", "def s():", "    sys.stdout = " + _WRAP_O), 0),
    ("sibling: guarded rebind inside a module-level try",
     _plant("import io, sys", "try:", "    if __name__ == '__main__':",
            "        sys.stdout = " + _WRAP_O, "except Exception:", "    pass"), 0),
)


def _arm_selftest():
    """-> n_failed. Runs the folded arms through the REAL path (_mark_module_scope, then
    visit), because a check that searches different bytes than the real path is the very
    defect this file exists to catch -- and that mistake was made once already, ON THIS FILE,
    by the lane contributing these arms."""
    bad = 0
    print("  -- folded arms (stderr / module-level try) --")
    for label, src, want in _ARM_CASES:
        tree = ast.parse(src)
        _mark_module_scope(tree)
        t = _Trap()
        t.visit(tree)
        got = len([h for h in t.hits if h[0] == "stdout_double_wrap"])
        ok = got == want
        bad += 0 if ok else 1
        print("  %-52s hits=%d want=%d %s" % (label, got, want, "OK" if ok else "FAIL"))
    return bad


def selftest():
    """Every detector, fired on a case that MUST trip it. Refuses if any reports clean."""
    print("SELFTEST -- each detector on an input that MUST trip it\n")
    tmp = os.path.join(_HERE, "__control_traps_selftest.py")
    src = SELFTEST_SRC + "\nBAD = '\\x08literal control byte'\n"   # (3) must fire
    with open(tmp, "wb") as fh:
        fh.write(src.replace("\\x08", "\x08").encode("utf-8"))
    try:
        hits, state = scan(tmp)
    finally:
        os.remove(tmp)
    got = {k for k, _l, _w in hits}
    want = {"stdout_double_wrap", "unanchored_substring", "except_swallows_import",
            "control_bytes"}
    for k in sorted(want):
        ok = k in got
        print("  %s  %s" % ("FIRES" if ok else "SILENT -- DETECTOR IS DEAD", k))
    missing = want - got
    print("\n  scan state: %s" % state)
    if missing:
        print("\nREFUSED: %d detector(s) returned CLEAN on an input built to trip them: %s"
              % (len(missing), ", ".join(sorted(missing))))
        print("A detector that has only ever returned negatives is indistinguishable from a "
              "broken one.")
        return 1
    # ⛔ THE COVERAGE PATH NEEDS A CASE THAT MUST FIRE TOO, AND IT DID NOT HAVE ONE.
    # Four detectors were proven able to fire; NOTHING proved the lint noticed a file it
    # could not read. It could not: an unreadable file returned zero hits and left the set
    # in silence, so a baseline written during a lock omitted that file and the next run
    # accused it. Both states are fired here against a directory built to produce them, and
    # through assess() -- the same function main() uses.
    tmpd = tempfile.mkdtemp(prefix="__control_unscanned_")
    try:
        with open(os.path.join(tmpd, "broken.py"), "w", encoding="utf-8") as fh:
            fh.write("def f(")   # a syntax error, so this file CANNOT be parsed
        _f, _st, unscanned = assess(["broken.py", "never_written.py"], root=tmpd)
        kinds = {st.split(":")[0] for _r, st in unscanned}
        named = {r for r, _st in unscanned}
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    cover_bad = []
    for want_kind, want_file in (("UNPARSABLE", "broken.py"),
                                 ("UNREADABLE", "never_written.py")):
        ok = want_kind in kinds and want_file in named
        print("  %s  %s (%s)" % ("FIRES" if ok else "SILENT -- FILE WOULD BE DROPPED",
                                 want_kind, want_file))
        if not ok:
            cover_bad.append(want_kind)
    if cover_bad:
        print()
        print("REFUSED: the lint did not notice a file it could not check: %s"
              % ", ".join(cover_bad))
        print("A count of files that happened to be readable is not a count of the "
              "population, and this lint exists to say so.")
        return 1

    # ⛔ THE HOOK CALLS --staged, AND A REFACTOR DELETED THE FUNCTION THAT SERVES IT.
    # Nothing noticed: tree-wide mode still worked, the selftest still passed, and the only
    # broken path was the one the hook uses -- where a crash refuses EVERY commit. A check
    # whose failure mode is "block everyone" needs its entry point exercised, not assumed.
    try:
        staged_ok = isinstance(_staged_py(), list)
    except SystemExit:
        staged_ok = True                     # a REFUSAL is a working entry point
    except Exception as exc:                 # noqa: BLE001 -- any breakage at all
        print("  BROKEN  --staged entry point: %s" % exc)
        staged_ok = False
    print("  %s  --staged entry point (what the hook calls)"
          % ("WORKS " if staged_ok else "BROKEN"))
    if not staged_ok:
        print()
        print("REFUSED: the hook calls --staged and that path does not run. A crash there "
              "refuses every commit in the repo.")
        return 1

    arm_bad = _arm_selftest()
    if arm_bad:
        print("\nREFUSED: %d folded arm(s) wrong. The widening is NOT proven."
              % arm_bad)
        return 1
    print("\nAll %d detectors fired and %d folded arms are correct. A zero from this "
          "lint now means something." % (len(want), len(_ARM_CASES)))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    # ⛔ GATING IS THE DEFAULT, AND THAT IS FORCED BY HOW THE RUNNER INVOKES CHECKS.
    # gates/run_repo_checks.py does subprocess.run([sys.executable, path]) -- NO ARGS. A
    # check whose blocking behaviour hides behind a flag is therefore registered as a check
    # that CANNOT FAIL, which is the precise defect this repo has measured: of 200
    # check-shaped scripts, 156 were never invoked at all. `--report` opts out; nothing
    # opts in.
    ap.add_argument("--gate", action="store_true", help="(default; kept for explicitness)")
    ap.add_argument("--report", action="store_true", help="report only, never refuse")
    ap.add_argument("--from-rev", dest="from_rev",
                    help="measure a REVISION's blobs instead of the worktree "
                         "(a baseline is only correct for the tree it was measured on)")
    ap.add_argument("--staged", action="store_true",
                    help="judge ONLY the .py files staged in this commit (hook mode)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--write-baseline", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    # ⛔ SCOPED TO THE COMMIT, BECAUSE FOUR LANES SHARE THIS WORKTREE AND A TREE-WIDE
    # HOOK MAKES EVERY LANE'S VIOLATION BLOCK EVERY OTHER LANE'S COMMIT. That already
    # happened tonight: another lane created scripts/oa2/ carrying the house stdout idiom,
    # and a tree-wide gate refused MY commit for THEIR files -- the same shape as the format
    # checker that refused 148 of 149 pages and blocked a push for hours.
    #
    # ⭐ THIS IS AIMING, NOT LOOSENING, AND THE DIFFERENCE IS TESTABLE: every violation still
    # blocks the commit that INTRODUCES it, because that commit stages that file. What it
    # stops is a violation blocking a commit that does not touch it. The alternative fix --
    # baselining another lane's new rows -- would have been the loosening one, and it is the
    # fix this baseline's own note already ruled out: it hides a violation from its owner.
    if a.from_rev:
        found, states, unscanned, files = assess_rev(a.from_rev)
        print("MEASURED AT REVISION: %s (blobs, no checkout)" % a.from_rev)
    elif a.staged:
        files = [f for f in _staged_py() if os.path.exists(os.path.join(_ROOT, f))]
        if not files:
            print("no .py staged in this commit -- this lint has nothing to say about it.")
            return 0
    else:
        files = candidates()
    if not a.from_rev:
        found, states, unscanned = assess(files)

    total = sum(len(v) for v in found.values())
    print("CANDIDATES ENUMERATED (every tracked .py, not grepped): %d" % len(files))
    for k, v in sorted(states.items()):
        print("   %-12s %5d" % (k, v))
    # ⛔ THE KINDS MUST SUM TO THE POPULATION. A denominator that disagrees with its own
    # population cannot pass, whatever it says about the corpus.
    if sum(states.values()) != len(files):
        print("REFUSED: file states sum to %d, not %d." % (sum(states.values()), len(files)))
        return 1

    # ⛔ A FILE THAT WAS NOT READ WAS NOT CHECKED, AND THIS LINT HAD THAT DEFECT ITSELF.
    # `scan()` has always returned a STATE naming why a file yielded nothing, and the caller
    # tallied the states and CARRIED ON. So an unreadable file contributed zero hits and left
    # the violation set silently -- and a baseline written in that moment OMITS the file, after
    # which the very next run accuses it of a NEW violation it has carried since August.
    # That is exactly what happened: baseline 321/296, next run 322/297, the difference being
    # scripts/cross_check_external.py:42 -- a real violation, wrongly labelled new.
    #
    # An unchecked file is precisely where a new violation hides, so both modes refuse and
    # both NAME the files. A count of files that happened to be readable is not a count of
    # the population, and this is the tool that exists to say so.
    if unscanned:
        print()
        print("REFUSED: %d file(s) could not be checked, so this run cannot speak for the "
              "population." % len(unscanned))
        for rel, state in unscanned[:20]:
            print("   %-58s %s" % (rel[:58], state[:90]))
        if len(unscanned) > 20:
            print("   ... and %d more" % (len(unscanned) - 20))
        print("A file that was not read was not checked. The read is already retried once, "
              "so this is not a transient lock.")
        return 1

    by_kind = {}
    for rel, hs in found.items():
        for k, _l in hs:
            by_kind[k] = by_kind.get(k, 0) + 1
    print("\nVIOLATIONS: %d across %d file(s)" % (total, len(found)))
    for k, v in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        print("   %-24s %4d" % (k, v))

    if a.write_baseline:
        os.makedirs(os.path.dirname(_BASELINE), exist_ok=True)
        with open(_BASELINE, "w", encoding="utf-8") as fh:
            json.dump({"_what": "violations present when the lint was introduced; a file "
                                "may not gain a NEW one. These are OWED, NOT CLEARED.",
                       "files": {k: [list(x) for x in v] for k, v in found.items()}},
                      fh, indent=1, sort_keys=True)
        print("\nbaseline written: %d file(s)" % len(found))
        return 0

    if not a.report:
        base = {}
        if os.path.exists(_BASELINE):
            with open(_BASELINE, encoding="utf-8") as fh:
                base = {k: {tuple(x) for x in v}
                        for k, v in json.load(fh).get("files", {}).items()}
        new = {}
        for rel, hs in found.items():
            fresh = {(k, l) for k, l in hs} - base.get(rel, set())
            # A line MOVING is not a new violation; a new KIND in a file is.
            fresh = {(k, l) for k, l in fresh
                     if k not in {bk for bk, _bl in base.get(rel, set())}}
            if fresh:
                new[rel] = sorted(fresh)
        if not base:
            print("\nREFUSED: no baseline. Run --write-baseline deliberately; a gate with "
                  "no baseline would refuse the whole corpus, which is as useless as one "
                  "that refuses nothing and louder about it.")
            return 1
        if new:
            print("\nREFUSED: %d file(s) gained a NEW trap kind." % len(new))
            for rel, hs in sorted(new.items())[:20]:
                for k, l in hs:
                    print("   %s:%d  %s" % (rel, l, k))
            return 1
        print("\nNO FILE GAINED A NEW TRAP. %d baselined violation(s) remain OWED, not "
              "cleared." % total)
    return 0


if __name__ == "__main__":
    # GUARDED, BECAUSE THIS LINT REFUSED ITS OWN FILE FOR THE FIRST TRAP IT DETECTS.
    # A module-scope rebind closes the buffer of any caller that imports this module,
    # and the selftest names this exact guard as the sanctioned fix. It would have been
    # absurd to baseline it.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
