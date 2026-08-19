#!/usr/bin/env python3
"""RUN A DELEGATION AND REFUSE TO CALL IT DONE ON AN EXIT CODE ALONE.

WHY THIS EXISTS, AND IT IS NOT A CONVENIENCE WRAPPER. Three delegations were launched in one
minute and all three returned **exit code 0 having done nothing**:

    codex exec ... - < /dev/null      ->  "No prompt provided via stdin."   exit 0
    agy --print   < /dev/null         ->  "flag needs an argument: -print"  + usage dump

The house rule is that `codex exec` must have stdin CLOSED or it hangs. The other house rule is
that a long prompt is piped in. THOSE TWO RULES CONTRADICT EACH OTHER: `< /dev/null` overrides
the pipe, the CLI finds no prompt, prints one line and exits SUCCESSFULLY. A background job
reports "completed (exit code 0)" and a lane that trusts the exit code reads an empty file and
believes the seat had nothing to say.

    AN EXIT CODE IS NOT AN ANSWER. P29 says a filter asserts an EXPECTED COUNT, not merely a
    successful exit, and this is that rule applied to a whole seat.

So: the prompt goes in as an ARGUMENT, stdin is closed, and the result is REFUSED unless it is
long enough and matches an expected shape the caller names in advance.

USAGE
    python scripts/delegate.py codex <prompt-file> <out-file> [--min-chars N] [--expect REGEX]
    python scripts/delegate.py agy   <prompt-file> <out-file> [--min-chars N] [--expect REGEX]
                                                              [--expect-count N]
"""
import io
import os
import re
import shutil
import subprocess
import sys

USAGE_SIGNS = ("No prompt provided", "flag needs an argument", "Usage of", "Usage:",
               "unknown flag", "not inside a trusted directory")


def run(seat, prompt_path, out_path, min_chars=200, expect=None, expect_count=None,
        timeout=3000):
    with io.open(prompt_path, "r", encoding="utf-8") as fh:
        prompt = fh.read()
    # RESOLVE THE EXECUTABLE, because on Windows these are `.CMD` and `.EXE` shims that
    # `subprocess` cannot find from a bare name without a shell. The bare name raised
    # `FileNotFoundError: [WinError 2]` -- and the launcher still reported exit 0 to the
    # harness, which is this file's own failure mode happening to this file.
    exe = shutil.which(seat)
    if not exe:
        print("REFUSED: %r is not on PATH. A seat that cannot be found has not been asked."
              % seat)
        return 2
    if seat == "codex":
        cmd = [exe, "exec", "-s", "workspace-write", "--skip-git-repo-check", prompt]
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    elif seat == "agy":
        cmd = [exe, "--print", prompt]
        cwd = "F:/claude-temp"
    else:
        print("unknown seat %r" % seat)
        return 2

    # STDIN CLOSED, PROMPT IN ARGV. The two house rules stop contradicting each other only
    # when the prompt stops travelling through stdin.
    with open(os.devnull, "rb") as devnull:
        p = subprocess.run(cmd, stdin=devnull, capture_output=True, timeout=timeout, cwd=cwd)
    out = (p.stdout or b"").decode("utf-8", "replace")
    err = (p.stderr or b"").decode("utf-8", "replace")
    body = out if len(out) >= len(err) else err
    with io.open(out_path, "w", encoding="utf-8") as fh:
        fh.write(body)

    problems = []
    if p.returncode != 0:
        problems.append("exit %d" % p.returncode)
    for s in USAGE_SIGNS:
        if s.lower() in body[:2000].lower():
            problems.append("the CLI printed %r -- IT NEVER RAN THE PROMPT" % s)
            break
    if len(body.strip()) < min_chars:
        problems.append("only %d chars of output, below the %d the caller required"
                        % (len(body.strip()), min_chars))
    if expect and not re.search(expect, body, re.I | re.M):
        problems.append("the expected pattern %r is absent" % expect)
    if expect_count is not None and expect:
        n = len(re.findall(expect, body, re.I | re.M))
        if n < expect_count:
            problems.append("matched the expected pattern %d time(s), fewer than the %d "
                            "answers the caller required" % (n, expect_count))

    print("seat        %s" % seat)
    print("exit        %d" % p.returncode)
    print("chars       %d" % len(body.strip()))
    print("written     %s" % out_path)
    if problems:
        print("\nREFUSED -- this delegation did NOT produce a usable answer:")
        for x in problems:
            print("   %s" % x)
        print("\nThe exit code alone would have called this a success.")
        return 1
    print("\nACCEPTED -- output present and matches the shape the caller named in advance.")
    return 0


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    seat, prompt_path, out_path = argv[1], argv[2], argv[3]
    kw = {}
    for i, a in enumerate(argv):
        if a == "--min-chars":
            kw["min_chars"] = int(argv[i + 1])
        elif a == "--expect":
            kw["expect"] = argv[i + 1]
        elif a == "--expect-count":
            kw["expect_count"] = int(argv[i + 1])
        elif a == "--timeout":
            kw["timeout"] = int(argv[i + 1])
    return run(seat, prompt_path, out_path, **kw)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        _rc = main(sys.argv)
    except Exception as _exc:                                # noqa: BLE001
        # AN EXCEPTION IS A REFUSAL, NEVER A PASS. The first version let a FileNotFoundError
        # propagate and the surrounding harness still recorded "completed (exit code 0)".
        print("REFUSED: the delegation raised %s: %s" % (type(_exc).__name__, _exc))
        _rc = 2
    sys.exit(_rc)
