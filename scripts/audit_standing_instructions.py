"""For each standing instruction that constrains what a command may do: what enforces it?

"AN INSTRUCTION ENFORCED BY A GUARD THAT HAPPENS TO COVER IT IS NOT ENFORCED; IT IS LUCKY."

That sentence was written after the paper rollout ATTEMPTED TO REBUILD `ARNI_HF_REVIEW.html`
-- an instruction in force all night, on a page whose manuscript is an authored docmodel the
projector reproduces at about 11%. The batch runner had no exclusion for it. What stopped
the build was `ssot/manuscript_guard.py` refusing on MANUSCRIPT_SHRINK: A DIFFERENT GUARD,
WRITTEN FOR A DIFFERENT REASON, THAT HAPPENED TO COVER THE CASE. ARNI is byte-identical to
HEAD and nothing was lost. The instruction was still unenforced.

THIS IS THE MECHANISATION QUESTION APPLIED TO INSTRUCTIONS RATHER THAN DEFECT CLASSES, and
it is asked the same way: is there a command that FAILS when the instruction is breached,
and has it been SHOWN to fail?

    ENFORCED    a command refuses the breach, and it is wired into a hook.
    COINCIDENT  something refuses it, but that something was written for another purpose and
                covers this case by accident. It can stop covering it without anyone
                noticing, because nothing names the dependency. THE ARNI STATE.
    CONVENTION  nothing refuses it. It holds because a person remembers, and the heredoc
                rule was breached NINE times by an author who had just read it -- so
                "convention" is not a mild state.

EVERY ROW IS CHECKED RATHER THAN ASSERTED: the named command must exist, must contain a
reachable non-zero exit, and must appear in a hook for ENFORCED. A row whose command cannot
be found is reported as such, not silently downgraded.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = [os.path.join(REPO, ".githooks", n)
         for n in ("pre-commit", "pre-push", "pre-commit-staging")]

NONZERO = re.compile(
    r"sys\.exit\(\s*(?!0\s*\)|\)|None\s*\))|raise\s+SystemExit\(\s*(?!0\s*\)|\))"
    r"|require_controls\s*\(|exit 1")

# (instruction, command or None, claimed_state, note)
INSTRUCTIONS = [
    ("Never author content through a shell heredoc -- the transport turns \\b into 0x08",
     "scripts/lint_control_chars.py", "ENFORCED",
     "Breached NINE times by an author who had just read the rule, and TWICE MORE tonight "
     "by me. The tenth was stopped by this hook, which does not care whether anyone "
     "understands it. THE ARGUMENT FOR MECHANISM IS THIS ROW."),

    ("Never net-delete from ssot/**/*.json",
     "scripts/ssot_net_deletion_check.py", "ENFORCED",
     "Walks the key sets of both versions. Note the gap it does NOT cover: a ZERO-BYTE "
     "object has no key set to walk, so it raises rather than reporting -- which blocked "
     "the commit, but by crashing rather than by judging."),

    ("Do not `git add -A`; stage by path",
     ".githooks/pre-commit-staging", "ENFORCED",
     "Refuses staged paths outside the declared set; STAGING_WIDE=1 is the deliberate "
     "override and it is logged in the message rather than silent."),

    ("Do not rebuild ARNI_HF_REVIEW.html",
     "scripts/rebuild_paper_corpus_2026_08_20.py", "ENFORCED",
     "AS OF 2026-08-20 ONLY, and only for THIS rollout. Before that it was COINCIDENT: the "
     "batch runner had no exclusion and ssot/manuscript_guard.py stopped the build for an "
     "unrelated reason. Any OTHER batch runner written tomorrow inherits nothing -- the "
     "DO_NOT_REBUILD list lives in one script, not in a shared module."),

    ("A file named *_gate.py must be able to fail",
     "scripts/lint_gate_can_fail.py", "ENFORCED",
     "And it is SCOPED TO A FILENAME. Every instrument written since has been named lint_ "
     "or audit_, so none is subject to it. Nobody evaded the rule; the filenames moved."),

    ("Verify delivery against the PUBLIC host, never localhost",
     "scripts/verify_delivered_bytes.py", "CONVENTION",
     "The script exists and is correct. NOTHING REQUIRES IT TO BE RUN before a delivery "
     "claim -- the largest instance in DEFECT-REGISTRY.md is a delivery check that never "
     "left the machine, and the remedy was the script, not a gate that calls it."),

    ("Confirm BOTH refs moved; main is the Pages deploy ref",
     None, "CONVENTION",
     "`git ls-remote` by hand. A push to the feature branch alone creates a remote branch "
     "and triggers NO deploy, and nothing says so at push time."),

    ("One writer per repo -- do not run two processes against the same state",
     "scripts/rebuild_paper_corpus_2026_08_20.py", "COINCIDENT",
     "A lockfile now covers THIS rollout, added after two concurrent runs rolled back two "
     "correctly-built pages. NOTHING covers the general case: two appliers, or an applier "
     "and a build, can still run together."),

    ("A quoted field must not be rewritten by a formatter",
     "ssot/apply_container_repr_2026_08_20.py", "COINCIDENT",
     "The QUOTED_KEYS list lives inside ONE applier, added after that applier reworded "
     "bempedoic-acid-review's `verbatim` field. The next applier inherits nothing."),

    ("Do not rename or redirect a delivered page",
     None, "CONVENTION",
     "The tombstone discipline. Nothing checks it; it nearly overwrote a 722 KB dashboard."),

    ("Report P46 and P47 together, with the provenance-refusal count",
     None, "CONVENTION",
     "A reporting instruction. scripts/p46_queue.py and audit_p46_closure_quality.py "
     "produce the numbers; nothing requires both to be quoted."),
]


def can_fail(rel):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return None
    src = io.open(path, encoding="utf-8", errors="replace").read()
    body = src
    for q in ('"""', "'''"):
        if body.lstrip().startswith(q):
            end = body.find(q, body.find(q) + 3)
            if end > 0:
                body = body[end + 3:]
            break
    return bool(NONZERO.search(body))


def hooked(rel):
    name = os.path.basename(rel)
    for h in HOOKS:
        if os.path.exists(h) and name in io.open(h, encoding="utf-8",
                                                 errors="replace").read():
            return True
    return False


def main():
    print("WHAT ENFORCES EACH STANDING INSTRUCTION?")
    print("Checked, not asserted: the command must exist, must hold a reachable non-zero")
    print("exit, and must appear in a hook before a row reads ENFORCED.")
    print("")
    tally = {}
    for instr, cmd, claimed, note in INSTRUCTIONS:
        if cmd is None:
            state, detail = "CONVENTION", "no command named"
        else:
            cf = can_fail(cmd)
            if cf is None:
                state, detail = "MISSING", "the named command is not on disk: %s" % cmd
            elif not cf:
                state, detail = "CONVENTION", "%s exists but cannot fail" % cmd
            elif claimed == "COINCIDENT":
                state, detail = "COINCIDENT", cmd
            elif hooked(cmd) or cmd.startswith(".githooks"):
                state, detail = "ENFORCED", cmd
            else:
                state, detail = "COINCIDENT", "%s can fail but is in no hook" % cmd
        tally[state] = tally.get(state, 0) + 1
        print("[%-10s] %s" % (state, instr))
        print("             %s" % detail)
        print("             %s" % note)
        print("")

    print("ENFORCED   %d   a command refuses the breach and a hook runs it"
          % tally.get("ENFORCED", 0))
    print("COINCIDENT %d   something refuses it, written for another purpose or wired "
          "nowhere" % tally.get("COINCIDENT", 0))
    print("CONVENTION %d   nothing refuses it; it holds because a person remembers"
          % tally.get("CONVENTION", 0))
    print("MISSING    %d   the row names a command that is not there"
          % tally.get("MISSING", 0))
    print("")
    print("THIS LIST IS NOT THE INSTRUCTIONS. It is the instructions SOMEBODY WROTE DOWN")
    print("HERE. There is no inventory of standing instructions in this project, so a rule")
    print("absent from this file is indistinguishable from a rule that does not exist --")
    print("which is the same shape as the defect the file is about.")


if __name__ == "__main__":
    main()
