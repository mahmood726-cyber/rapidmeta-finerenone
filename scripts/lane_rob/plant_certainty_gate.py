# -*- coding: utf-8 -*-
"""Plant the defect in the certainty gate, and prove the gate OBSERVES rather than CONSTRUCTS.

THE TRAP THIS IS ANSWERING. Four instruments today reported populations they had themselves
created -- one hardcoded the very field that makes a label render and reported 104 defects
against a true 6. A gate that pattern-matches a string IT invented is measuring its own
imagination. So there are two questions here, not one:

  CAN IT FAIL?   plant a page that violates, watch it refuse; plant one that complies,
                 watch it pass.
  IS THE STRING THE RENDERER'S?  the pattern must match text the GENERATOR emits, proven by
                 finding the literal in the generator source, not by asserting it.

The second is the one the four instruments failed.
"""
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
GATE = os.path.join("scripts", "lane_rob",
                    "gate_no_certainty_over_unadjudicated_rob.py")

fails = 0


def check(label, got, want):
    global fails
    ok = got == want
    if not ok:
        fails += 1
    print("   %-6s %-64s %s" % ("PASS" if ok else "FAIL", label, got))
    if not ok:
        print("            expected %r" % (want,))


# ---------------------------------------------------------------------------------------
# 1. IS THE PATTERN THE RENDERER'S? Find the literal the gate greps for in the generator
#    that emits it. If it is not there, the gate is matching a shape nobody produces.
# ---------------------------------------------------------------------------------------
print("CONSTRUCT-OR-OBSERVE: does the gate's pattern target text the generator emits?")
gen = io.open(os.path.join("ssot", "projectors2.py"), encoding="utf-8").read()
emits_certainty = "Certainty: %s" in gen
print("      generator emits the literal 'Certainty: %s'  ->", emits_certainty)
check("the level string is the generator's, not the gate's", emits_certainty, True)
gate_src = io.open(GATE, encoding="utf-8").read()
check("the gate greps for that same literal shape",
      bool(re.search(r'Certainty:\\s\*\(low', gate_src)), True)
# and it must NOT be satisfied by anything the gate itself writes into the page
check("the gate writes nothing to any page",
      ("open(" in gate_src and ', "w"' not in gate_src and "'w'" not in gate_src), True)
print("")

# ---------------------------------------------------------------------------------------
# 2. CAN IT FAIL? Two synthetic pages, in a scratch dir, on a real topic that HAS pending
#    outcomes so the gate's precondition is genuinely met.
# ---------------------------------------------------------------------------------------
print("PLANTED PAGES -- built on a real topic whose outcomes really are PENDING")
TOPIC = "iv-iron-hf"
SHELL = '<html><body><p>%s</p><p>ssot/' + TOPIC + '/appraisal/x.json</p></body></html>'
tmpdir = os.path.join(REPO, "_plant_tmp")
os.makedirs(tmpdir, exist_ok=True)
violating = os.path.join("_plant_tmp", "PLANT_VIOLATING.html")
complying = os.path.join("_plant_tmp", "PLANT_COMPLYING.html")
io.open(os.path.join(REPO, violating), "w", encoding="utf-8").write(
    SHELL % "Certainty: low Started at high")
io.open(os.path.join(REPO, complying), "w", encoding="utf-8").write(
    SHELL % "Certainty: Pending &mdash; not rated")


def run(page):
    """Run the gate on one page. Verdict is read from OUTPUT, not from exit status --
    a status read through a pipe is the pipe's, and that has bitten twice tonight."""
    r = subprocess.run([sys.executable, GATE, page], capture_output=True, cwd=REPO)
    out = r.stdout.decode("utf-8", "replace")
    if "VERDICT: REFUSED" in out:
        return "refused"
    if "VERDICT: PASS" in out:
        return "pass"
    return "no verdict line: %r" % out[-120:]


check("a page rendering a LEVEL where the resolver says pending -> refused",
      run(violating), "refused")
check("a page rendering PENDING -> passes", run(complying), "pass")
print("")

for f in (violating, complying):
    os.remove(os.path.join(REPO, f))
os.rmdir(tmpdir)
print("scratch pages removed; the gate wrote nothing and neither did this.")
print("")
print("ALL CONTROLS HELD" if not fails else "%d CONTROL(S) FAILED" % fails)
raise SystemExit(1 if fails else 0)
