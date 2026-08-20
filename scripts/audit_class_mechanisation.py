"""For each defect class opened tonight: IS THERE A COMMAND THAT FAILS WHEN IT RECURS?

Documentation failed as a control under the best conditions it will ever get. The heredoc
class was breached NINE TIMES by an author who understood it completely; the tenth was
stopped by a hook that does not care whether anyone understands it. So the registry's class
count is not an answer to "can this happen again". THIS FILE IS.

THREE STATES, AND THE THIRD IS THE HONEST ONE.

    PROVEN       a command exits non-zero when the defect recurs AND has been demonstrated
                 to fail on a real instance -- a self-test that constructs a failing input,
                 or a recorded refusal. This is the question as asked. Whether the command
                 is WIRED INTO A HOOK is reported beside it, because a gate nobody runs is
                 still a gate, but hooking a reporting sweep would be the wrong fix.
    UNPROVEN     a command exists and can exit non-zero, but nothing has shown it firing.
    DOCUMENTED   there is prose in DEFECT-REGISTRY.md and nothing that refuses. The class
                 is recorded, not controlled.

HOW EACH COLUMN IS ESTABLISHED, because a table of my own assertions would be the same
failure one level up:

    exists       os.path.exists on the named command
    can_fail     the module is parsed and searched for a REACHABLE non-zero exit --
                 sys.exit with a non-empty/non-zero argument, SystemExit, or a raise. A
                 file that only prints cannot fail, whatever its name says.
    hooked       the command's name appears in .githooks/pre-commit or .githooks/pre-push
    fired        the instrument carries its own falsification: a positive control, a graft
                 test, a constructed failing input from the real corpus. Asserted by name
                 in the table below and CHECKED here by looking for the marker in the file.

WHAT THIS FILE DOES NOT CLAIM. `fired` is evidence that the instrument has been shown to
refuse SOMETHING, not that it would catch every recurrence. And a class marked DOCUMENTED
is not a class that has been ignored -- it is one whose control is a person remembering,
which is the control that has already failed nine times in this repository.

THE NAMING LOOPHOLE, RECORDED BECAUSE IT IS THE MECHANISM. `scripts/lint_gate_can_fail.py`
already enforces "a file named *_gate.py must be able to fail", and it was written after
four files named gate turned out to be triage tools. EVERY INSTRUMENT WRITTEN SINCE HAS
BEEN NAMED `lint_*` OR `audit_*`, so none of them is subject to it. Nobody evaded the rule;
the rule was scoped to a filename and the filenames moved. This file exits non-zero when a
class in its own table has no failing command, which is the same promise applied to the
registry rather than to a name.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = [os.path.join(REPO, ".githooks", "pre-commit"),
         os.path.join(REPO, ".githooks", "pre-push"),
         os.path.join(REPO, ".githooks", "pre-commit-staging")]

# A reachable non-zero exit. sys.exit() and sys.exit(0) and sys.exit(None) do NOT count.
NONZERO = re.compile(
    r"sys\.exit\(\s*(?!0\s*\)|\)|None\s*\))|raise\s+SystemExit\(\s*(?!0\s*\)|\))"
    r"|SENTINEL_BLOCK|return\s+1\s*$", re.M)

# (class, one-line name, command or None, marker proving it has fired, notes)
CLASSES = [
    ("44", "an instrument that cannot tell 'nothing to do' from 'did nothing'",
     "scripts/lint_no_false_allclear.py", None, ""),
    ("--", "THE ACCUSING DIRECTION -- four wrong accusations in one night, none caught "
     "by the instrument that made them",
     "scripts/lint_instrument_declares_a_control.py", "PROOF PASSED",
     "--prove writes an uncontrolled instrument and requires a refusal, then requires the "
     "declared exemption to lift it. HOOKED 2026-08-20."),
    ("45", "a batch operation needs a predicate false when it did not run",
     "scripts/test_apply_reml_guard.py", "skipTest",
     "the two after-the-pass proofs SKIP rather than pass when unrun"),
    ("46", "a field's own prose naming a defence that does not exist",
     "scripts/lint_method_claim_has_a_field.py", None,
     "the graft test constructs a failing input from a real object"),
    ("47", "a resolver returning a container where a leaf was named",
     "scripts/audit_path_resolvers.py", None,
     "returned NOT_ASSESSABLE across 782 files, which is the only reason its own broken "
     "extraction did not read as a clean corpus"),
    ("48", "the instruments are a larger source of defects than the data",
     None, None, "a measurement, not a defect with a detector"),
    ("49", "the skip criterion selected live pages out of a corpus-wide fix",
     "scripts/audit_exclusion_by_absence.py", "PROOF PASSED",
     "--gate ratchets the 125 negative guards INSIDE a corpus-wide loop; --prove requires "
     "an unbaselined guard to come back NEW and the corpus as it stands to report none. "
     "HOOKED 2026-08-20. The 1,300-guard population is NOT gated -- a check that blocks on "
     "a population blocks everything."),
    ("50", "a page-scale compliance apparatus asserting rigour no result required",
     "scripts/lint_self_describing_safety_claim.py", None, ""),
    ("51", "an unexpectedly large number from a new measurement needs checking first",
     None, None, "a discipline, and no command expresses it"),
    ("52", "a check reporting zero has two readings and only one is reassuring",
     "scripts/regression_check.py", None,
     "MECHANISED AT THE SITE OF TWO OF ITS THREE INSTANCES: every page is now asked whether "
     "`arni_hf_protocol` occurs AT ALL, and a zero from a marker seen nowhere prints "
     "NOT_ASSESSABLE instead of contributing a clean verdict to the BLOCKING set. UNPROVEN "
     "and stated as such -- proving it needs a browser run over the corpus, which has not "
     "happened since the change. instrument_controls.zero_has_a_reading is the shared form."),
    ("53", "one figure defensible under two disagreeing definitions -- report both",
     None, None, ""),
    ("54", "a flag certifying one half of a question, read as certifying both",
     "scripts/audit_mixed_contrast_pools.py", "NEGATIVE_CONTROL",
     "positive AND negative control, both required to pass before any count prints"),
    ("55", "arm roles contradicted by the object's own other fields",
     "scripts/lint_arm_roles_contradict_the_object.py", "PROOF PASSED",
     "--gate ratchets the ten known contradictions; --prove requires an unbaselined one to "
     "come back NEW. THE BASELINE IS NOT A CLEARANCE -- FOURIER's swapped arms still carry "
     "their counts and icosapent's arms table still tells a reader the treatment was "
     "placebo. It records that they are SEEN."),
]


def can_fail(rel):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return False
    src = io.open(path, encoding="utf-8", errors="replace").read()
    # Strip the docstring so prose about exiting does not count as an exit.
    body = src
    for q in ('"""', "'''"):
        if body.lstrip().startswith(q):
            end = body.find(q, body.find(q) + 3)
            if end > 0:
                body = body[end + 3:]
            break
    if NONZERO.search(body):
        return True
    # A PYTEST FILE FAILS THROUGH `assert`, NOT THROUGH sys.exit. The first version of this
    # check scored scripts/test_apply_reml_guard.py -- fourteen proofs, two of which SKIP
    # rather than pass when unrun -- as unable to fail. A mechanisation audit that cannot
    # see the one mechanism already in place is the defect it was written to measure.
    if not os.path.basename(rel).startswith("test_"):
        return False
    return re.search(r"^\s*assert\s|self\.assert\w+\(", body, re.M) is not None


def hooked(rel):
    name = os.path.basename(rel)
    for h in HOOKS:
        if os.path.exists(h):
            if name in io.open(h, encoding="utf-8", errors="replace").read():
                return True
    return False


def fired(rel, marker):
    if not marker:
        return False
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return False
    return marker in io.open(path, encoding="utf-8", errors="replace").read()


def main():
    gate = "--gate" in sys.argv
    rows = []
    for cls, name, cmd, marker, note in CLASSES:
        if not cmd:
            rows.append((cls, name, "", False, False, False, "DOCUMENTED", note))
            continue
        exists = os.path.exists(os.path.join(REPO, cmd))
        cf = exists and can_fail(cmd)
        hk = exists and hooked(cmd)
        fr = exists and fired(cmd, marker)
        # PROVEN is Mahmood's question exactly: a command that FAILS when this recurs, and
        # HAS BEEN SHOWN to fail on a real instance. `hooked` is reported beside it because
        # a gate nobody runs is a gate, but it is not what was asked -- and hooking a
        # reporting sweep would be the wrong fix for the wrong column.
        if cf and fr:
            state = "PROVEN"
        elif cf:
            state = "UNPROVEN"
        else:
            state = "DOCUMENTED"
        rows.append((cls, name, cmd, cf, hk, fr, state, note))

    print("CAN TONIGHT'S CLASSES REFUSE? -- %d classes opened 2026-08-20" % len(rows))
    print("")
    print("%-4s %-6s %-9s %-7s %-7s %s" % ("cls", "fails", "hooked", "fired", "state",
                                           "command"))
    print("-" * 100)
    for cls, name, cmd, cf, hk, fr, state, note in rows:
        print("%-4s %-6s %-9s %-7s %-7s %s"
              % (cls, "yes" if cf else "NO", "yes" if hk else "no",
                 "yes" if fr else "no", state, cmd or "(none)"))
        print("       %s" % name)
        if note:
            print("       -- %s" % note)

    counts = {}
    for r in rows:
        counts[r[6]] = counts.get(r[6], 0) + 1
    print("")
    print("MECHANISED AND PROVEN   %d" % counts.get("PROVEN", 0))
    print("MECHANISED AND UNPROVEN %d" % counts.get("UNPROVEN", 0))
    print("DOCUMENTED ONLY         %d" % counts.get("DOCUMENTED", 0))
    print("")
    print("A CLASS IN THE THIRD BUCKET IS RECORDED, NOT CONTROLLED. Its control is a person")
    print("remembering, and that control has already failed nine times in this repository.")

    if gate:
        undone = [r for r in rows if r[6] == "DOCUMENTED" and r[2]]
        if undone:
            print("")
            print("REFUSED: %d class(es) name a command that cannot fail." % len(undone))
            for r in undone:
                print("    class %s -> %s" % (r[0], r[2]))
            sys.exit(1)


if __name__ == "__main__":
    main()
