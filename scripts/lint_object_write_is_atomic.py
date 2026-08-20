"""Does anything open an SSOT object for writing before it has the bytes to write?

THE INCIDENT, 2026-08-20. `ssot/apply_container_repr_2026_08_20.py` ran

    io.open(path, "w", encoding="utf-8", newline="\\n")

where the backslash had been doubled by the tool that wrote the line. Python opened the
file -- WHICH TRUNCATES IT -- and then raised `ValueError: illegal newline value` while
constructing the TextIOWrapper. THE FAILURE HAPPENED AFTER THE DESTRUCTION AND BEFORE THE
WRITE. `ssot/apixaban-vte-prophylaxis/apixaban-vte-prophylaxis.json` was zero bytes.

IT WAS RECOVERABLE ONLY BECAUSE IT HAD BEEN COMMITTED. That is luck standing in for a
guard.

AND NOTHING IN THIS PROJECT WAS WATCHING FOR IT. Every guard here protects the corpus from
a BAD WRITE -- `ssot_net_deletion_check.py` compares keys before and after, the appliers
compare `_walk()` sets, `manuscript_guard.py` refuses a shrunken manuscript. All of them
compare the new content to the old. THERE WAS NO NEW CONTENT. A file of zero bytes does not
parse, so a checker that loads both sides never reaches its comparison; it raises, and on a
`--apply` run that already crashed, nobody was there to read the traceback.

    Would the net-delete check have caught it before commit? It runs at pre-commit, and it
    WOULD have -- `json.load` on an empty file raises and the hook exits non-zero. So the
    zero-byte object could not have been committed. That is a real second line and it is
    worth stating: the window was between the crash and the next commit, and in that window
    the working tree held nothing. The recovery came from git, not from the check.

THE STANDING PREFERENCE IS TO MAKE THE CLASS IMPOSSIBLE RATHER THAN DETECTABLE.
`ssot/atomic_write.py` serialises to a string FIRST, writes a sibling temp file, fsyncs it,
and only then renames over the target. A rename is atomic on NTFS and on POSIX: the target
is either the old bytes or the new bytes, never zero. A failure anywhere before the rename
leaves the original untouched.

WHAT THIS FILE CHECKS. Every `open(..., "w")` (or `"wb"`, `"w+"`) whose path expression
mentions an object or a delivered page, in `ssot/` and `scripts/`, that is NOT routed
through `atomic_write`. Ratcheted: the existing population is baselined and MUST NOT GROW,
because rewriting every writer in one unreviewed pass is the shape of half of
DEFECT-REGISTRY.md.

THREE STATES. A file this cannot parse is reported as UNPARSED, not as clean.
"""
import io
import os
import re
import sys
import ast
import json
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls
BASELINE = os.path.join(REPO, "scripts", "baselines", "object_write_baseline.json")

WRITE_MODE = re.compile(r"^[wa]b?\+?$")
TARGETY = re.compile(r"ssot|OBJ\b|_REVIEW|\.json|\.html|obj_path|page|LEDGER|out_path",
                     re.I)


def writes_in(path):
    """-> (list of (line, snippet), parsed_ok)."""
    src = io.open(path, encoding="utf-8", errors="replace").read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [], False
    lines = src.split("\n")
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = getattr(fn, "attr", None) or getattr(fn, "id", None)
        if name not in ("open",):
            continue
        mode = None
        if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
            mode = node.args[1].value
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
        if not isinstance(mode, str) or not WRITE_MODE.match(mode):
            continue
        ln = getattr(node, "lineno", 0)
        snippet = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""
        # The line's own context decides whether the target is corpus content.
        ctx = " ".join(lines[max(0, ln - 3):ln + 1])
        if not TARGETY.search(ctx):
            continue
        if "atomic_write" in ctx or "atomic_write" in snippet:
            continue
        hits.append((ln, snippet[:96]))
    return hits, True


def _controls():
    """CONSTRUCTED FIXTURES, NOT LIVE FILES -- registry class 58.

    A positive control that says "the corpus currently contains a non-atomic write" stops
    asserting anything the day the last one is converted. These two strings keep failing if
    the detector breaks, however clean ssot/ becomes.

    AND THE FIXTURES ARE BUILT WITH A FILE TOOL, NOT A HEREDOC. The first attempt at this
    function was authored through a shell heredoc and every `\\n` inside its string literals
    arrived as a real newline, producing four unterminated string literals. That is the
    heredoc class, twice in one session, by an author who had recorded it earlier the same
    night. The rule is not "be careful"; the rule is "do not author content through a
    shell", and this file exists to make a different class impossible for the same reason.
    """
    import tempfile
    import shutil
    d = tempfile.mkdtemp(prefix="atomic_ctl_")
    try:
        bad = os.path.join(d, "writer_bad.py")
        good = os.path.join(d, "writer_good.py")
        bad_src = [
            "import io",
            'obj_path = "ssot/x/x.json"',
            'with io.open(obj_path, "w", encoding="utf-8") as fh:',
            '    fh.write("{}")',
        ]
        good_src = [
            "import atomic_write",
            'obj_path = "ssot/x/x.json"',
            "atomic_write.write_json(obj_path, {})",
        ]
        io.open(bad, "w", encoding="utf-8", newline=chr(10)).write(chr(10).join(bad_src))
        io.open(good, "w", encoding="utf-8", newline=chr(10)).write(chr(10).join(good_src))
        bad_hits, ok_bad = writes_in(bad)
        good_hits, ok_good = writes_in(good)
        if not (ok_bad and ok_good):
            raise SystemExit("REFUSED: a control fixture did not parse. A control that "
                             "cannot be read is not a control.")
        require_controls(
            "lint_object_write_is_atomic",
            positive=("a writer that opens an object path for 'w' directly",
                      bool(bad_hits), True),
            negative=("a writer routed through atomic_write", bool(good_hits), True))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    gate = "--gate" in sys.argv
    _controls()
    found, unparsed = {}, []
    for path in sorted(glob.glob(os.path.join(REPO, "ssot", "*.py"))
                       + glob.glob(os.path.join(REPO, "scripts", "*.py"))):
        rel = os.path.relpath(path, REPO).replace("\\", "/")
        if rel.endswith("lint_object_write_is_atomic.py"):
            continue
        hits, ok = writes_in(path)
        if not ok:
            unparsed.append(rel)
            continue
        for ln, snippet in hits:
            found["%s:%d" % (rel, ln)] = snippet

    print("NON-ATOMIC WRITES TO CORPUS CONTENT: %d" % len(found))
    print("UNPARSED (reported, not skipped): %d" % len(unparsed))
    for rel in unparsed[:5]:
        print("    %s" % rel)

    present = sorted(found)
    if not os.path.exists(BASELINE):
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        json.dump({
            "written": "2026-08-20",
            "why": ("`io.open(path, 'w', newline='\\\\n')` TRUNCATED an object and then "
                    "raised on the illegal newline value -- the failure landed AFTER the "
                    "destruction and BEFORE the write, and the object was zero bytes. Every "
                    "guard in this project compares new content to old; there was no new "
                    "content. THIS COUNT MUST NEVER RISE; new writers use "
                    "ssot/atomic_write.py, which renames over the target so it holds either "
                    "the old bytes or the new bytes and never none."),
            "writes": present,
        }, io.open(BASELINE, "w", encoding="utf-8", newline="\n"), indent=1,
            ensure_ascii=False)
        print("wrote baseline with %d writes" % len(present))
        return

    known = set(json.load(io.open(BASELINE, encoding="utf-8")).get("writes") or [])
    new = sorted(set(present) - known)
    healed = sorted(known - set(present))
    if healed:
        print("%d baselined write(s) are gone or now atomic." % len(healed))
    if new:
        print("")
        print("REFUSED: %d NEW non-atomic write(s) to corpus content:" % len(new))
        for k in new:
            print("    %s" % k)
            print("        %s" % found[k])
        print("")
        print("Use ssot/atomic_write.py: serialise to a string, write a temp sibling, fsync,")
        print("rename over the target. A crash before the rename leaves the original intact.")
        if gate:
            sys.exit(1)
    else:
        print("NO NEW NON-ATOMIC WRITE. The baseline has not risen.")


if __name__ == "__main__":
    main()
