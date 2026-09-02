# -*- coding: utf-8 -*-
"""Rewrite a module docstring as a RAW literal without changing what it says.

WHY THIS EXISTS, and the lesson is bigger than the fix:
  These files were deleted by a runaway loop and restored byte-perfectly from history.
  THE RESTORE BROUGHT THE HISTORICAL DEFECT BACK WITH THEM. Byte-identity to the past
  answers "did I restore it"; it does not answer "is it acceptable now". I verified the
  first question and never asked the second.

WHAT MAKES THIS SAFE:
  Adding `r` to a docstring CHANGES WHAT IT SAYS unless the doubled backslashes are halved
  at the same time -- and halving them wrongly changes it the other way. So the value is
  computed BEFORE and AFTER and the write is REFUSED unless they are identical. The proof
  is per file and is printed. A fix that cannot prove it preserved meaning is a rewrite.
"""
import ast
import io
import os
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)


def module_docstring_span(src):
    """Return (start, end, literal_source) for the module docstring, or None."""
    tree = ast.parse(src)
    if not tree.body:
        return None
    node = tree.body[0]
    if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)):
        return None
    seg = ast.get_source_segment(src, node.value)
    if seg is None:
        return None
    start = src.index(seg)
    return start, start + len(seg), seg


def rawify(lit):
    """Turn a normal triple-quoted literal into a raw one with halved backslashes."""
    if lit.startswith(("r", "R")):
        return None                      # already raw, nothing to do
    if not lit.startswith('"""'):
        return None                      # only handle the triple-double form
    body = lit[3:-3]
    new_body = body.replace("\\\\", "\\")
    if new_body.endswith("\\"):
        return None                      # a raw string may not end in a backslash
    if '"""' in new_body:
        return None
    return 'r"""' + new_body + '"""'


def fix(path, apply=False):
    # newline="" ON READ AS WELL AS WRITE. Reading with universal newlines and
    # writing with newline="" silently converted CRLF -> LF across the WHOLE file,
    # turning a 3-line docstring fix into a 442-line diff. Preserve what was there.
    src = io.open(path, encoding="utf-8", newline="").read()
    span = module_docstring_span(src)
    if not span:
        print("  %-24s no module docstring -- skipped" % os.path.basename(path))
        return False
    a, b, lit = span
    new_lit = rawify(lit)
    if new_lit is None:
        print("  %-24s already raw or not convertible -- skipped" % os.path.basename(path))
        return False

    old_val = ast.literal_eval(lit)
    try:
        new_val = ast.literal_eval(new_lit)
    except Exception as exc:
        print("  %-24s REFUSED: new literal does not parse (%s)"
              % (os.path.basename(path), type(exc).__name__))
        return False

    same = (old_val == new_val)
    print("  %-24s old==new: %-5s  (%d chars, %d doubled backslashes halved)"
          % (os.path.basename(path), same, len(old_val),
             lit.count("\\\\")))
    if not same:
        # show the first divergence so the refusal is diagnosable, not just a "no"
        for i, (x, y) in enumerate(zip(old_val, new_val)):
            if x != y:
                print("       first divergence at %d: %r -> %r" % (i, old_val[i:i+40],
                                                                   new_val[i:i+40]))
                break
        print("       REFUSED -- the rewrite would change what the docstring says")
        return False

    if not apply:
        print("       would write (dry run)")
        return True
    out = src[:a] + new_lit + src[b:]
    # final proof on the WHOLE FILE: it must still parse and the docstring must be identical
    if ast.get_docstring(ast.parse(out), clean=False) != old_val:
        print("       REFUSED at final check -- whole-file docstring differs")
        return False
    io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("       WRITTEN")
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    print("mode: %s" % ("APPLY" if apply else "DRY RUN"))
    ok = 0
    for p in args:
        ok += bool(fix(p, apply))
    print("%d file(s) %s" % (ok, "written" if apply else "would change"))
