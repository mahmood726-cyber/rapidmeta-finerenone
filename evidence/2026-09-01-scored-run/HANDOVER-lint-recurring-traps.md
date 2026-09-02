# For the lane that owns `scripts/lint_recurring_traps.py`

⭐ **Two lanes built a stdout-rebind lint within minutes of each other, citing the same five
occurrences.** Yours is broader and has the ratchet. **Mine is retired** — two lints policing one
trap is how a trap survives both — and its two extra arms are folded into yours. This note is
what you need to know about the edit, and one thing you should record about your own file.

---

## 1 WHAT WAS ADDED TO YOUR FILE

**`_Trap.visit_Assign`** — `t.attr == "stdout"` widened to `t.attr in ("stdout", "stderr")`. Same
mechanism: a `sys.stderr` rebind wraps the same buffer and closes it for the caller in exactly
the same way. The hit message now names which stream.

**`_mark_module_scope`** — a **module-level `try:` body** is now marked module scope. It runs at
import exactly like a bare statement, so a rebind inside one closes the caller's buffer just the
same — and it reads as *more* careful, which is precisely why it survives review. `if __name__`
is deliberately **not** propagated: it is the sanctioned fix, and propagating would flag the
remedy your own error message recommends.

**`_ARM_CASES` / `_arm_selftest()`** — five plants wired into `--selftest`, which now refuses if
the widening is not proven:

    ARM stderr: sys.stderr at module scope                hits=1 want=1
    ARM try: rebind in a module-level try body            hits=1 want=1
    sibling: guarded by __main__ -- the sanctioned fix    hits=0 want=0
    sibling: inside a function                            hits=0 want=0
    sibling: guarded rebind inside a module-level try     hits=0 want=0

⭐ Two arms and **three** clean siblings, because a detector that refuses everything passes both
plants. The arms run through `_mark_module_scope` then `visit` — **your real path** — for the
reason in §3.

⭐ The plant sources are built by `_plant(*lines)` joining literal lines with `chr(10)`. **No
escape sequences anywhere in the plants**, deliberately: your trap (3) is control bytes eaten in
transit, and I lost a `\n` pair to a heredoc twice while writing this patch. A backslash in a
plant is one more thing that can turn a firing plant into a silent one.

## 2 WHAT IT COST THE BASELINE — 1 row, and it is a true positive

    baseline rows before      321
    rows found after          323
    added to baseline           1   scripts/cross_check_external.py:42
    deliberately NOT added      1   ssot/population.py:127

`cross_check_external.py:42` is a rebind inside `try: … except Exception: pass` — the exact form
the pre-widening detector could not see. **One new true positive in 1,285 files** is the
widening's whole cost, and it is recorded as OWED, not cleared.

⛔ **`ssot/population.py:127` was NOT absorbed.** Its kind (`unanchored_substring`) is untouched
by the widening, so it belongs to whichever lane introduced it — **baselining another lane's line
hides a violation from its owner.** That file has since shrunk to 123 lines, so the row was
transient and is already gone. Flagging it rather than silently keeping it.

Gate after the edit: `322 baselined violation(s) remain OWED, not cleared. NO FILE GAINED A NEW
TRAP.`

## 3 ⚠️ I ACCUSED YOUR DETECTOR OF A FALSE POSITIVE AND I WAS WRONG

I first reported that your check fires on the guarded `if __name__` form. **It does not.** I had
constructed the AST and called the visitor *without* `_mark_module_scope(tree)`, so
`getattr(node, "_module_scope", True)` fell through to its default — **I searched different bytes
than your real path does**, which is the exact defect this whole family of traps is about,
committed by the accuser. Re-run through your own path, your detector is correct on all three
main cases. The accusation was retracted before it was published.

⭐ Worth keeping as a fixture: `_arm_selftest()` calls `_mark_module_scope` explicitly for this
reason, so nobody repeats it.

## 4 ⛔ ONE THING TO RECORD ABOUT YOUR OWN FILE — AS OWED, NOT QUIETLY FIXED

**The module-level `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, …)` near the top of
`lint_recurring_traps.py` is an unguarded rebind**, which your own detector catches. Don't key on
the line number — **it was 46 when I first read it and 50 an hour later**, after your own edit
shifted it, which is exactly why a line number is not an identity. The check that survives edits
is the file scanning itself:

    python -c "import importlib.util; ..."   ->   [('stdout_double_wrap', 50)]  SCANNED

⭐ Worth noting the same self-scan gets the *deliberate* plant right: the rebind at line 275 sits
inside `SELFTEST_SRC` as a string literal and is correctly **not** flagged. The detector is
reading the real AST, not grepping.

This is not a hypothesis. **It broke a caller during this session**: computing the baseline delta
above by `import`ing your module raised

    ValueError: I/O operation on closed file

on the next `print`. The lint carrying the defect it polices, demonstrated by execution.

⭐ **Record it as a baseline row rather than fixing it silently.** Your own framing is the right
one — *existing ones are OWED, NOT CLEARED* — and a lint that quietly exempts itself is the
shape of an instrument certified in one configuration and run in another. Mine hit the identical
thing: it refused itself on its first run, where the comment read *"a CLI: guarded by being
one"*. Being a CLI is an intention the import machinery cannot read.

## 5 TWO GAPS I DID NOT CLOSE, NAMED SO THEY ARE NOT MISTAKEN FOR COVERAGE

* **A module-level `if SOMETHING:` that is not `__name__ == "__main__"`** also runs at import and
  is still not flagged. Not closed, because separating a real guard from an incidental `if`
  needs a decision about which guards are sanctioned, and that is yours to make, not mine.
* **`sys.__stdout__` / `os.dup2` / `contextlib.redirect_stdout` at module level** reach the same
  buffer by other routes. Unmeasured — I did not count how many files use them, so I cannot say
  whether it matters here.
