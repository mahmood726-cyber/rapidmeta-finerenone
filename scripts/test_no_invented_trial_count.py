"""A count in a sentence served to a reader must come from the object, not from memory.

THE DEFECT. `ssot/projectors.py` emitted, as a module constant, the readiness detail

    "The included set is a named TWO-TRIAL programme rather than the yield of a
     database search."

for every topic whose search declares no strategy. The word "two" was read from nothing.

MEASURED on the served surface before the fix, by
`scripts/measure_defect_classes.measure_two_trial_sentence`:

    146  served pages render the sentence
     18  record a k_included_in_object that can be checked
     13  of those 18 CONTRADICT it -- k of 1, 3, 4, 5, 6, 7 and 8
      5  agree
    128  record no k at all: NOT CHECKABLE, which is not agreement

5 + 13 = 18 checkable, and 18 + 128 = 146. The counts reconcile to the population.

HOW THIS TEST FIRES AGAINST THE PRE-FIX FILE. It reads the projector and looks for a
hard-coded number-word inside that sentence. Against the parent the literal is there and
the test fails; after the fix the count is interpolated from the object and there is no
literal to find.

    git show origin/main:ssot/projectors.py > "$SCRATCH/projectors.prefix.py"
    python scripts/test_no_invented_trial_count.py --source "$SCRATCH/projectors.prefix.py"
    -> FAIL       (post-fix: PASS)

WHAT IS DELIBERATELY NOT CHANGED, AND IS ASSERTED HERE. The disclosure -- "Nothing on this
page should be read as though a systematic search had been performed" -- is CORRECT, is
protected, and is the only true half of its contradiction with `P1_executed_search`. The
cheapest way to make the count check pass would be to delete the sentence, which would
resolve that contradiction in exactly the wrong direction. So the disclosure surviving is
a test in its own right, and it fails if the sentence goes.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: A number-word or digit inside this sentence would be an INVENTED count.
_INVENTED = re.compile(
    r"named\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+)[\s-]*trial", re.I)


def _joined(text):
    """Adjacent Python string literals joined, so a sentence split across source lines
    reads as one string.

    NEEDED ON THIS TEST'S FIRST RUN. Interpolating the count split the protected disclosure
    across a concatenation break -- `"... read as though a systematic search "` then
    `"had been performed."` -- and a raw source search reported the sentence as DELETED.
    That is this lane's founding defect one altitude down: a check reading different bytes
    from the ones the reader receives.
    """
    return re.sub(r'"\s*(?:#[^\n]*)?\n\s*"', "", text)


def _source(source_path):
    path = Path(source_path) if source_path else (ROOT / "ssot" / "projectors.py")
    return path, path.read_text(encoding="utf-8", errors="replace")


def _docstring_lines(text):
    """0-based line numbers occupied by module, class and function docstrings.

    SCOPE, NOT LENIENCY. This test asks whether a count is hard-coded in a sentence SERVED
    TO A READER. A docstring is never served, so a count in one is documentation. On this
    test's own first run the only post-fix failure was the worked example inside the
    projector helper's docstring -- an illustration of the fix behaving correctly.
    Excluding docstrings is correct scoping; rewording the documentation to dodge the
    regex would have been the other thing, and would have left the test asserting less
    than it claims.
    """
    import ast
    out = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out                     # unparseable: exclude nothing, flag everything
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
            continue
        body = getattr(node, "body", None) or []
        first = body[0] if body else None
        is_docstring = (isinstance(first, ast.Expr)
                        and isinstance(first.value, ast.Constant)
                        and isinstance(first.value.value, str))
        if is_docstring:
            out.update(range(first.lineno - 1, getattr(first, "end_lineno", first.lineno)))
    return out


def test_no_hardcoded_count_in_the_readiness_detail(source_path=None):
    path, text = _source(source_path)
    lines = text.splitlines()
    docs = _docstring_lines(text)
    problems = []
    for m in _INVENTED.finditer(text):
        n = text[:m.start()].count("\n")
        # A COMMENT is the record of the defect; a DOCSTRING is documentation. Neither is
        # served to a reader, and neither is what this test is about.
        if lines[n].lstrip().startswith("#") or n in docs:
            continue
        problems.append(
            "%s:%d emits a hard-coded trial count (%r) in a sentence served to readers. "
            "The count must come from k_cascade.k_included_in_object, and a topic stating "
            "no k must carry no number." % (path.name, n + 1, m.group(0)))
    return problems


def test_the_count_is_read_from_the_object(source_path=None):
    path, text = _source(source_path)
    if "k_included_in_object" in text and "a named programme of trials" in text:
        return []
    return ["the projector neither reads k_included_in_object for this sentence nor offers "
            "the no-number form, so a topic recording no k has no correct rendering."]


def test_the_protected_disclosure_survives(source_path=None):
    path, text = _source(source_path)
    if "as though a systematic search had been performed" in _joined(text):
        return []
    return ["the readiness disclosure has been removed. It is PROTECTED: it is the only "
            "TRUE half of the contradiction with P1_executed_search, and deleting it "
            "resolves that contradiction in the wrong direction. Removing the sentence is "
            "the cheapest way to pass the count check and it is not permitted."]


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    source = argv[argv.index("--source") + 1] if "--source" in argv else None
    checks = [
        ("no hard-coded trial count in the readiness detail",
         test_no_hardcoded_count_in_the_readiness_detail(source)),
        ("the count is read from the object, with a no-number form",
         test_the_count_is_read_from_the_object(source)),
        ("the protected disclosure survives",
         test_the_protected_disclosure_survives(source)),
    ]
    failed = 0
    print("file under test: %s\n" % (source or "ssot/projectors.py"))
    for name, problems in checks:
        if problems:
            failed += len(problems)
            print("FAIL  %s" % name)
            for p in problems:
                print("        - %s" % p)
        else:
            print("PASS  %s" % name)
    if failed:
        print("\n%d problem(s)." % failed)
        return 1
    print("\nNo invented counts, and the disclosure is intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
