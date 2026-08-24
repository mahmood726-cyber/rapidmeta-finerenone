"""A delegated job's result may not be used until it is shown to have produced output.

THE DEFECT THIS CLOSES, reproduced by another lane tonight:

    `codex exec --sandbox workspace-write "<prompt>"` launched with run_in_background
    silently fails to receive its prompt. Codex prints "Reading additional input from
    stdin...", waits, and EXITS 0 HAVING DONE NOTHING. No output, no file, no error.

    Their tally: 5 of ~8 backgrounded invocations. Every foreground invocation worked.

The dangerous property is not that it fails. It is that it fails EXACTLY LIKE SUCCESS. A
completed notification and exit 0 from a lane that never received its prompt is
indistinguishable from one that did the work -- and for an adversarial hunt the failure mode
is worse still, because a hunt that silently did nothing returns "no defects found", which
reads identically to a clean corpus. That is the silence-as-success family this repo has
been chasing all day: a SKIP counted as a PASS, a gate with no `sys.exit(1)`, a numerical
witness that skipped for want of a baseline.

SO THE RULE IS A PROPERTY, NOT A HABIT: exit code zero is not evidence of work. Bytes are.

    verify(job) must fail unless the job produced non-empty, non-trivial output.

WHAT THE AUDIT OF THIS SESSION FOUND, and why it is in the docstring rather than a comment
somewhere: 16 backgrounded `codex exec` calls ran tonight. EVERY ONE of them printed
"Reading additional input from stdin..." -- the defect's exact signature -- and every one
nonetheless produced between 132 KB and 4 MB of output and wrote the artefact it promised.
The difference was `< /dev/null` on every invocation: with stdin closed the read returns EOF
immediately, Codex falls through to the prompt it already has on argv, and the job runs. The
mitigation and the defect were both already known here; the mitigation is what saved them.

That is not a reason to relax the rule. It is the reason to encode it: the jobs survived
because of a habit, and a habit is not a check.
"""
import io
import os
import sys

# Signatures that a Codex run never got its prompt. Presence alone is NOT failure -- with
# stdin closed the line prints and the run proceeds -- so this is used only to explain a
# job that ALSO produced nothing.
_STDIN_FALLTHROUGH = "Reading additional input from stdin"

# Below this, an "output" is a banner and a prompt echo, not work. Chosen from the observed
# floor: the smallest real Codex report tonight was 132 KB, and the smallest real panel
# response 2.2 KB. 200 bytes is far under both and still excludes every empty case.
_MIN_USEFUL_BYTES = 200

FAILS = []


def check(name, got, want, why):
    ok = got == want
    print("  %-62s %s" % (name, "PASS" if ok else "FAIL"))
    if not ok:
        FAILS.append("%s: expected %r, got %r -- %s" % (name, want, got, why))


def job_produced_output(path, exit_code=0):
    """(usable, reason). THE ONLY function whose answer may gate using a job's result.

    Exit code is accepted but deliberately CANNOT make a job usable on its own. It can only
    make it unusable: a non-zero exit with output is still a failure, while a zero exit with
    no output is the defect this exists for.
    """
    if exit_code != 0:
        return False, "job exited %s" % exit_code
    if not path or not os.path.exists(path):
        return False, "no artefact on disk"
    size = os.path.getsize(path)
    if size == 0:
        return False, "artefact is zero bytes -- the job produced nothing"
    try:
        head = io.open(path, encoding="utf-8", errors="replace").read(4096)
    except OSError as e:
        return False, "artefact unreadable: %s" % e
    # THE BANNER IS "Reading additional input from stdin..." AND THE DOTS ARE PART OF IT.
    # Removing only the phrase left "..." behind, which is not empty, so the banner-only
    # case never got its explanation. Caught by the test above, which is the point of
    # writing the assertion before trusting the function.
    body = head.replace(_STDIN_FALLTHROUGH, "").strip().strip(". \t\r\n")
    if size < _MIN_USEFUL_BYTES:
        why = "artefact is %d bytes -- too small to be a report" % size
        if _STDIN_FALLTHROUGH in head and not body:
            why += "; it contains only the stdin-fallthrough banner, so the prompt never arrived"
        return False, why
    return True, "%d bytes" % size


def main():
    print("PLANT-THE-DEFECT: a delegated job must prove it produced output")
    print()
    import tempfile
    d = tempfile.mkdtemp(prefix="delegated_")

    def w(name, content):
        p = os.path.join(d, name)
        io.open(p, "w", encoding="utf-8").write(content)
        return p

    # 1. THE PLANTED DEFECT ITSELF: exit 0, no file. This is the reproduced failure.
    ok, why = job_produced_output(os.path.join(d, "never_written.txt"), exit_code=0)
    check("exit 0 with NO artefact is refused", ok, False, why)

    # 2. Exit 0 with a zero-byte artefact -- the redirect ran, the job did not.
    ok, why = job_produced_output(w("empty.txt", ""), exit_code=0)
    check("exit 0 with a ZERO-BYTE artefact is refused", ok, False, why)

    # 3. THE EXACT OBSERVED SIGNATURE: the banner and nothing else.
    ok, why = job_produced_output(
        w("banner.txt", "Reading additional input from stdin...\n"), exit_code=0)
    check("exit 0 with only the stdin-fallthrough banner is refused", ok, False, why)
    check("   and the reason names the cause",
          "prompt never arrived" in why, True, why)

    # 4. A short non-empty file is still not a report. Guards against a job that echoes
    #    its prompt, or writes "OK", and is counted as having hunted.
    ok, why = job_produced_output(w("tiny.txt", "no defects found\n"), exit_code=0)
    check("a 17-byte 'no defects found' is refused", ok, False, why)

    # 5. THE REAL SHAPE FROM TONIGHT: banner present, and 300 KB of work behind it.
    #    This must PASS, or the check would have condemned 16 sound jobs.
    ok, why = job_produced_output(
        w("real.txt", "Reading additional input from stdin...\n" + ("finding. " * 4000)),
        exit_code=0)
    check("banner PLUS real output is accepted", ok, True, why)

    # 6. Non-zero exit is never usable, however much it wrote.
    ok, why = job_produced_output(w("big_but_failed.txt", "x" * 5000), exit_code=6)
    check("non-zero exit is refused even with output", ok, False, why)

    # 7. AND THE INVERSE THE RULE EXISTS FOR: exit code alone must not be able to pass a
    #    job. If this ever passes, the check has been reduced to reading $?.
    ok, _why = job_produced_output(None, exit_code=0)
    check("exit 0 with no path at all cannot pass", ok, False, "path was None")

    print()
    if FAILS:
        print("FAILED %d:" % len(FAILS))
        for f in FAILS:
            print("   " + f)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
