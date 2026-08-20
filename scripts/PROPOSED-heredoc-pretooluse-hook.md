# Refusing the heredoc at the point of use — a proposal, not an installation

**Fifteenth instance in this project, third in one session, and every one of them by someone
who had just read the rule forbidding it.** That is the finding. Nothing about the authors is
careless: the path is available, it looks like it works, and it fails silently in a way that
only shows up later as a literal `0x08` byte or a mangled `\n`.

## Why the commit path cannot refuse it

The existing gates are wired and they work:

```
scripts/lint_control_chars.py    control characters in tracked text
scripts/lint_escape_hazards.py   escape hazards in pattern literals
```

Both catch the **consequences**. Neither can catch the **cause**, and the reason is structural:

> **A heredoc is how a file is authored. It is not what is committed.** By the time a gate
> at the commit path can see anything, the heredoc has already run and either corrupted the
> content or not. Asking the pre-commit hook to refuse heredocs is asking it to detect a
> process from its output — which it can only do when the process happened to leave damage.

So a commit gate is the wrong layer. It is not that nobody wrote it; it cannot exist there.

## What would actually refuse it

A **PreToolUse hook** in the harness, which sees the Bash invocation *before* it runs. Sketch,
for `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/refuse_heredoc.py"
          }
        ]
      }
    ]
  }
}
```

with `scripts/refuse_heredoc.py` reading the tool input from stdin, matching `<<\s*'?[A-Za-z_]`
in the command, and exiting non-zero with a message naming the alternative (write the file with
an editor tool, then run it).

**Deliberately not installed in this session.** Adding a harness-level interceptor is a new
mechanism with its own blast radius — it can refuse *every* Bash call if the matcher or the
exit convention is wrong — and it is being proposed at the end of a long session in which the
author's own recoverable-error rate was rising. That is exactly the risky final step the
previous lane declined, and declining it is the same judgement.

**Two things the next lane should check before installing it:**

1. **The exit-code convention.** A PreToolUse hook that exits non-zero on a *parse failure*
   rather than on a *match* would block all Bash. Test it against a known-good command first
   and confirm the command still runs.
2. **Whether `.claude/` should be tracked here.** No `.claude/` directory exists in this repo
   today and nothing ignores one. Committing harness configuration is a decision about how
   the repo is used, not just a fix, and it should be taken deliberately.

## The narrow version, if the full hook is unwanted

A `refuse_heredoc.py` that runs as a **manual pre-flight** — `python scripts/refuse_heredoc.py
"<command>"` — gives no enforcement and is therefore worth very little. **A check that has to
be remembered is the same class of thing as the rule that has to be remembered, and the rule
is what already failed fifteen times.** If it is not enforced at the point of use, prefer to
leave it documented and spend the effort elsewhere.
