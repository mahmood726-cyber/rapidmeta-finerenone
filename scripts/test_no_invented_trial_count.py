"""A count in a rendered sentence must come from the object, not from the author's memory.

THE DEFECT. `ssot/projectors.py` emitted, as a module constant, the readiness detail

    "The included set is a named TWO-TRIAL programme rather than the yield of a
     database search."

for every topic whose search declares no strategy. The word "two" was read from nothing.

MEASURED on the served surface before the fix:

    146 of 1464 served pages render the sentence
     18 of those record a k_included_in_object that can be checked
     13 of the 18 CONTRADICT it -- k of 1, 3, 4, 5, 6, 7 and 8
    128 record no k at all and are NOT CHECKABLE, which is not the same as agreeing

This is the "a stated trial count contradicts the actual k" class -- five sightings across
the external reviews, including "named two-trial programme" on a three-trial ceftaroline
page and on a k=1 bempedoic page -- with its emitter finally located.

HOW THIS TEST FIRES AGAINST THE PRE-FIX FILE. It reads the projector as text and looks for
a hard-coded number-word inside the readiness detail. Against the parent commit that string
is present and the test fails; after the fix the count is interpolated from
`k_cascade.k_included_in_object` and there is no literal to find.

    git show gh/main:ssot/projectors.py > "$SCRATCH/projectors.prefix.py"
    python scripts/test_no_invented_trial_count.py --source "$SCRATCH/projectors.prefix.py"
    -> FAIL      (post-fix: PASS)

WHAT IS DELIBERATELY NOT CHANGED. The disclosure itself -- "Nothing on this page should be
read as though a systematic search had been performed" -- is correct, is protected as R10 in
PROTECTED-REFUSALS-2026-09-02.md, and stays word for word. Only the invented count goes. A
page whose object states no k now says "a named programme of trials", with no number, rather
than guessing one.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Number-words and digits that would be an INVENTED count if they sit in this sentence.
_INVENTED = re.compile(
    r"named\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+)[\s-]*trial", re.I)


def test_no_hardcoded_count_in_the_readiness_detail(source_path=None):
    path = Path(source_path) if source_path else (ROOT / "ssot" / "projectors.py")
    text = path.read_text(encoding="utf-8", errors="replace")
    problems = []
    for m in _INVENTED.finditer(text):
        line = text[:m.start()].count("\n") + 1
        # An occurrence inside a COMMENT is the record of the defect, not the defect.
        line_text = text.splitlines()[line - 1].lstrip()
        if line_text.startswith("#"):
            continue
        problems.append(
            "%s:%d emits a hard-coded trial count (%r) in a sentence served to readers. "
            "The count must come from k_cascade.k_included_in_object, and where the object "
            "states no k the sentence must carry no number."
            % (path.name, line, m.group(0)))
    return problems


def _joined(text):
    """Adjacent Python string literals joined, so a sentence split across source lines reads
    as one string.

    THIS TEST NEEDED IT ON ITS FIRST RUN. Interpolating the count split the disclosure
    across a concatenation break -- `"... should be read as though a systematic search "`
    then `"had been performed."` -- and a raw source search reported the protected sentence
    as DELETED. That is the same defect the whole lane exists for, one altitude down: a
    check searching different bytes from the ones the reader receives.
    """
    return re.sub(r'"\s*(?:#[^\n]*)?\n\s*"', "", text)


def test_the_disclosure_survives(source_path=None):
    """The sentence this lane must NOT lose while removing the count."""
    path = Path(source_path) if source_path else (ROOT / "ssot" / "projectors.py")
    text = _joined(path.read_text(encoding="utf-8", errors="replace"))
    if "as though a systematic search had been performed" in text:
        return []
    return ["the readiness disclosure has been removed. It is PROTECTED (R10): it is the "
            "only TRUE half of the contradiction with P1, and deleting it would resolve "
            "that contradiction in the wrong direction."]


def test_the_count_is_read_from_the_object(source_path=None):
    path = Path(source_path) if source_path else (ROOT / "ssot" / "projectors.py")
    text = path.read_text(encoding="utf-8", errors="replace")
    if "k_included_in_object" in text and "a named programme of trials" in text:
        return []
    return ["the projector neither reads k_included_in_object for this sentence nor "
            "provides the no-number form, so a topic with no recorded k has no correct "
            "rendering available."]


def main(argv):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    source = argv[argv.index("--source") + 1] if "--source" in argv else None
    label = source or "ssot/projectors.py"
    checks = [
        ("no hard-coded trial count in the readiness detail",
         test_no_hardcoded_count_in_the_readiness_detail(source)),
        ("the count is read from the object, with a no-number form",
         test_the_count_is_read_from_the_object(source)),
        ("the protected disclosure survives", test_the_disclosure_survives(source)),
    ]
    failed = 0
    print("file under test: %s\n" % label)
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
    print("\nNo invented counts.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
