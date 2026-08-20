"""Every path that emits an outcome must call BOTH pool_referral and pool_findings.

WHY, AND IT IS THE SECOND INSTANCE IN TWELVE HOURS. `pool_referral()` and `pool_findings()`
were written the same night, to fix registry class 65 -- a correct finding recorded on an
object with no consumer obliged to render it. They were wired into the REPORTED branch of
the results section. THE DECLINED BRANCH CALLED NEITHER, and a finding on an outcome with no
pooled point therefore existed for us and not for the reader. Class 65 surviving on the one
path nobody re-read, inside the mechanism built to end class 65.

One declined outcome across 155 objects was affected. THE SMALL BLAST RADIUS IS NOT THE
POINT -- the property that matters is that it was ZERO-VISIBILITY: nothing failed, nothing
warned, and the object looked complete.

SO THIS ENUMERATES THE PATHS RATHER THAN WAITING FOR A THIRD. A path "emits an outcome" if
it loops over `results.by_outcome` and appends a paragraph or a table keyed to that outcome.
Each must call both functions, or say why it does not -- and "why not" is a real answer for
several of them, which is why this REPORTS rather than blocks.

NOT EVERY LOOP NEEDS THEM. A loop that builds a risk-of-bias table, or collects verbatim R
output, is not the place a reader meets the estimate. The rule is about the paths where the
ESTIMATE ITSELF is rendered, because that is where a referral or a finding qualifies it.
"""
import ast
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

TARGET = os.path.join(REPO, "ssot", "paper_projector.py")
# THE LOOP VARIABLE IS NOT ALWAYS `by_outcome`. The two paths that matter most --
# the REPORTED and DECLINED branches of the results section -- iterate lists built
# from by_outcome and named `reported` and `declined`, so a pattern keyed on the
# literal `by_outcome` MISSES EXACTLY THE PATHS THIS FILE EXISTS TO CHECK. The first
# cut did, found 5 estimate paths and 0 calling both, and named none of the two real
# ones. Third time tonight a reader of mine narrowed its own population; the
# known-answer floor below exists so it fails loudly instead.
LOOP = re.compile(r"for\s+\w+\s*,\s*\w+\s+in\s+(?:.*by_outcome|reported|declined)")
EMITS = re.compile(r"s\.paras\.append|s\.add\(|s\.add_table\(|rows\.append")
CALLS_REF = re.compile(r"pool_referral\(")
CALLS_FND = re.compile(r"pool_findings\(")
# A loop that renders the ESTIMATE, as opposed to a table of something else.
ESTIMATE = re.compile(r'pooled|\bp\[|p\.get\("point"\)|ci_prose|measure_words')

# Paths deliberately exempt, with the reason. An exemption that does not say why is the
# thing this file exists to prevent.
EXEMPT = {
    "figure_legends": "renders a LEGEND TABLE, not the estimate sentence; the referral and "
                      "the finding belong beside the number in Results, not under a figure.",
    "statistical_output": "quotes model output VERBATIM; interleaving prose would corrupt "
                          "the quotation, which is the one thing that section guarantees.",
    "risk_of_bias": "renders per-result BIAS JUDGEMENTS, not the pooled estimate.",
    "certainty": "renders GRADE ratings per outcome; the referral qualifies the estimate, "
                 "and the estimate is not here.",
    "methods_synthesis": "describes the MODEL, not the result.",
}


def enclosing_section(lines, i):
    """The Section(key, ...) this line sits under, searching backwards."""
    for j in range(i, -1, -1):
        m = re.search(r'Section\("([a-z_]+)"', lines[j])
        if m:
            return m.group(1)
    return "<unknown>"


def main():
    gate = "--gate" in sys.argv
    require_controls(
        "audit_outcome_paths_call_both",
        positive=("a loop over by_outcome that appends a paragraph is detected",
                  bool(LOOP.search("for oid, blk in (get(obj, 'results.by_outcome')).items():")),
                  True),
        negative=("an unrelated for-loop is detected as an outcome path",
                  bool(LOOP.search("for x in range(10):")), True))

    src = io.open(TARGET, encoding="utf-8").read()
    try:
        ast.parse(src)
    except SyntaxError as exc:
        sys.exit("PROOF FAILED: %s does not parse (%s). A reader that cannot parse its "
                 "target cannot report a clean result." % (TARGET, exc))
    lines = src.split("\n")

    paths = []
    for i, ln in enumerate(lines):
        if not LOOP.search(ln):
            continue
        # 60, NOT 40. The reported branch opens at line 1133 and calls pool_findings() at
        # 1173 -- exactly forty lines later, so a 40-line window EXCLUDED IT BY ONE and
        # reported the one path known to be correct as missing its call.
        body = "\n".join(lines[i:i + 60])
        if not EMITS.search(body):
            continue
        paths.append({
            "line": i + 1,
            "section": enclosing_section(lines, i),
            "renders_estimate": bool(ESTIMATE.search(body)),
            "referral": bool(CALLS_REF.search(body)),
            "findings": bool(CALLS_FND.search(body)),
            "src": ln.strip()[:76],
        })

    if not paths:
        print("NOT_ASSESSABLE: no outcome-emitting loop found in %s. That is a broken "
              "reader, not a clean projector." % os.path.relpath(TARGET, REPO))
        return 2

    # KNOWN-ANSWER FLOOR. The results section iterates `reported` and `declined`; both are
    # outcome-emitting estimate paths and both are known to exist. A reader that cannot see
    # them is measuring its own regex, not the projector.
    seen_loops = {p["src"] for p in paths}
    for must in ("in reported:", "in declined:"):
        if not any(must in s for s in seen_loops):
            sys.exit("PROOF FAILED: this reader did not find the loop `%s`, which is known "
                     "to exist in the results section and is the path the declined-branch "
                     "defect was found on. An all-clear from it would mean nothing." % must)

    # An estimate path may still be EXEMPT, provided the reason is recorded. A summary
    # section repeating a number qualified elsewhere is not where the qualification belongs;
    # an exemption with NO stated reason is exactly what this file exists to catch.
    est = [p for p in paths if p["renders_estimate"] and p["section"] not in EXEMPT]
    exempted = [p for p in paths if p["renders_estimate"] and p["section"] in EXEMPT]
    both = [p for p in est if p["referral"] and p["findings"]]
    neither = [p for p in est if not p["referral"] and not p["findings"]]
    one = [p for p in est if (p["referral"] or p["findings"]) and p not in both]

    print("")
    print("OUTCOME-EMITTING PATHS IN paper_projector.py: %d" % len(paths))
    print("   of which render the ESTIMATE                %d" % len(est))
    print("      call BOTH referral and findings          %d of %d" % (len(both), len(est)))
    print("      call ONLY ONE                            %d of %d" % (len(one), len(est)))
    print("      call NEITHER                             %d of %d" % (len(neither), len(est)))
    print("   estimate paths EXEMPT with a recorded reason %d" % len(exempted))
    print("   render something else (table, quote, rating) %d"
          % (len(paths) - len(est) - len(exempted)))

    print("")
    print("ESTIMATE PATHS AND THEIR STATE:")
    for p in est:
        mark = "OK" if (p["referral"] and p["findings"]) else "MISSING"
        print("   line %-5d [%-20s] ref=%-5s fnd=%-5s  %s"
              % (p["line"], p["section"][:20], p["referral"], p["findings"], mark))

    print("")
    print("NON-ESTIMATE PATHS -- exempt where a reason is recorded:")
    for p in paths:
        if p["renders_estimate"]:
            continue
        why = EXEMPT.get(p["section"])
        print("   line %-5d [%-20s] %s"
              % (p["line"], p["section"][:20], why or "NO REASON RECORDED -- read this one"))

    unexplained = [p for p in paths
                   if not p["renders_estimate"] and p["section"] not in EXEMPT]
    failed = bool(neither) or bool(one)
    print("")
    print("non-estimate paths with NO recorded reason: %d" % len(unexplained))
    if failed:
        print("FAILED: an estimate path does not call both. A referral or a finding that")
        print("does not render is a finding that exists for us and not for the reader.")
    return 1 if (gate and failed) else 0


if __name__ == "__main__":
    sys.exit(main())
