"""Arm role must be READ from the `role` field, never derived from position or label order.

# no-control: the planted control runs every invocation -- a fixture containing
# `sorted(per_arm.keys())` followed by an `[0]` index must be detected, and the fixed form must
# not be. The lint refuses to report on real source unless both hold.

THE DEFECT, FOUND BY CODEX AT THREE SITES:

    scripts/bulk_clone_audit_first.py:147     arms = sorted(per_arm.keys()); tN = arms[0]
    scripts/bulk_clone_audit_first.py:157     ogs  = sorted(og_vals.keys());  tE = ogs[0]
    scripts/reset_event_counts_from_source.py same shape

`BG_CONTROL` sorts before `BG_EXPERIMENTAL`. Every effect built that way inverts, and this
project has already published an object saying empagliflozin was worse than placebo from
exactly this class.

IT NEVER BIT THE STORED CORPUS, and the reason is the finding worth keeping: the objects store
arms as a list with an EXPLICIT `role`, so DIRECTION IS RECORDED RATHER THAN INFERRED. A sweep
of 155 objects and 407 trials found ZERO trials whose first arm label sorts as a control. The
mechanism has never been handed the input it needs.

THAT IS NOT A REASON TO LEAVE IT. Not producing a bad object is luck about labels, not a
guarantee -- the same standing as the zero-drop, which was latent on every page and is now
fixed on every page. This lint is what keeps the fix from being undone by someone tidying a
sort back in.

WHAT IS FLAGGED: a sorted() over something arm-shaped or outcome-group-shaped whose result is
then indexed positionally. What is NOT: sorting for display, for stable iteration, or for a
deterministic report -- none of those decide which arm is the treatment.
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "arm_role_sorted_2026_08_23.json")

ARMISH = r"(?:per_arm|arms|arm_groups|og_vals|outcome_groups|groups|result_groups)"
# `x = sorted(<armish>...)` on one line, and a positional index of that name within a few lines
SORTED_ARMS = re.compile(r"(\w+)\s*=\s*sorted\(\s*%s" % ARMISH)
POSITIONAL = re.compile(r"\[\s*0\s*\]|\[\s*1\s*\]")

PLANTED = (
    'per_arm = ex.get("aact_per_arm_counts") or {}\n'
    'arms = sorted(per_arm.keys())\n'
    'tN = per_arm.get(arms[0]) if arms else 0\n')
FIXED = (
    'per_arm = ex.get("aact_per_arm_counts") or {}\n'
    'arms = _arm_order(per_arm)\n'
    'tN = per_arm.get(arms[0]) if arms else 0\n')


def scan(src):
    """AST, NOT TEXT. The first version matched its own docstring and `ssot/arm_roles.py`'s
    explanation of the defect -- five false positives out of eleven, an instrument reading its
    own documentation as data for the second time today. A `sorted()` call is a Call node; a
    sentence about `sorted()` is a string constant, and only one of them runs."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
            continue
        fn = node.value.func
        if not (isinstance(fn, ast.Name) and fn.id == "sorted"):
            continue
        arg = ast.dump(node.value.args[0]) if node.value.args else ""
        if not re.search(ARMISH, arg):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if not names:
            continue
        # is that name later indexed positionally?
        for other in ast.walk(tree):
            if (isinstance(other, ast.Subscript)
                    and isinstance(other.value, ast.Name)
                    and other.value.id in names
                    and isinstance(getattr(other, "slice", None), ast.Constant)
                    and other.slice.value in (0, 1)):
                out.append((node.lineno, "sorted(%s...) then [%s]"
                            % (names[0], other.slice.value)))
                break
    return out


def prove():
    if not scan(PLANTED):
        sys.exit("PROOF FAILED: the planted `sorted(per_arm.keys())` + `[0]` was not detected. "
                 "Nothing reported.")
    if scan(FIXED):
        sys.exit("PROOF FAILED: the fixed form was flagged. Nothing reported.")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    prove()
    findings = []
    for root in ("scripts", "ssot"):
        d = os.path.join(REPO, root)
        if not os.path.isdir(d):
            continue
        # THE POSITIVE PROPERTY, STATED: the population is Python source. A non-.py file has
        # no AST and cannot contain a sorted-position arm read, so this selects the set that
        # can hold the defect rather than excluding one that might.
        for n in sorted(x for x in os.listdir(d) if x.endswith(".py")):
            p = os.path.join(d, n)
            for line, text in scan(io.open(p, encoding="utf-8", errors="replace").read()):
                findings.append({"file": "%s/%s" % (root, n), "line": line, "text": text})

    print("ARM ROLE FROM SORT ORDER   (control: passed -- a planted sort+index is detected, "
          "the fixed form is not)")
    print("")
    print("   sites deriving an arm by sorted position   %3d" % len(findings))
    for f in findings[:20]:
        print("      %-46s:%-5d %s" % (f["file"], f["line"], f["text"][:60]))
    print("")
    print("DIRECTION IS RECORDED, NOT INFERRED: the objects carry `role` on every arm, which")
    print("is why this never bit the corpus. That is the protection -- not the sort order --")
    print("and `ssot/arm_roles.py` is where a caller reads it.")
    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"findings": findings}, io.open(OUT, "w", encoding="utf-8"), indent=1)
    if findings:
        sys.exit("REFUSED: %d site(s) decide which arm is the treatment by sorted position. "
                 "`BG_CONTROL` sorts before `BG_EXPERIMENTAL`." % len(findings))


if __name__ == "__main__":
    main()
