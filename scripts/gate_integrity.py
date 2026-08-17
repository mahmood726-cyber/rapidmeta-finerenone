"""GATE INTEGRITY -- can this gate fail, and does it do what it says?

THE MECHANISM THIS DETECTS, WHICH IS OUR MOST RECURRENT ONE
    A CHECK THAT REPORTS SUCCESS WITHOUT HAVING PERFORMED THE CHECK.

    Five independent instances, all found in this project:
      1. The pre-push hook printed "Regression check PASS" while `$?` after a
         pipeline read `tail`, so the failure branch was unreachable. Every push
         from that clone was ungated while displaying a green result. 6 of 12
         checkouts still carried it today.
      2. figure_audit passed on pages it could not render -- a hidden or 0x0
         element measured as a silent zero rather than reported unmeasurable.
      3. A source leg returned a clean verdict having read nothing, because a
         corpus-reachable gate handed back our own just-written text.
      4. CHK005's mutation test swept one key and reported the estimate protected;
         the real pooled value was never mutated, so it could not have failed.
      5. The Word-vs-HTML alignment gate compared only the sections BOTH surfaces
         emit, so a section present in one and absent from the other was silently
         OUT OF SCOPE rather than a divergence. The extraction provenance table
         was missing from every Word manuscript this project ever produced and
         nothing could have reported it. A GATE THAT COMPARES ONLY WHAT BOTH
         SURFACES HAVE CAN NEVER DETECT ABSENCE -- the intersection is not the
         expected set, and using it as one converts every missing section into a
         pass. The fix is an expected-section manifest projected from the object,
         so absence FAILS instead of falling outside the comparison.

    The shape is identical in all five: the SUCCESS PATH IS REACHABLE AND THE
    FAILURE PATH IS NOT. A green result is therefore evidence of nothing, and
    nobody investigates a green result -- which is why these survive.

THE GENERAL DETECTOR
    For every gate, ask: WHAT INPUT WOULD MAKE THIS FAIL? Construct it and show it
    failing. A gate with no constructible failing input is not a gate. That single
    question would have caught all five.

WHAT THIS SCRIPT CHECKS MECHANICALLY
    D1 PIPELINE STATUS   `$?` read immediately after a pipeline. Generic: greps
                         every hook and shell script. One line, and it would have
                         caught the hook.
    D2 SCOPE HONESTY     a gate's claimed scope against what it actually globs.
                         The hook's header said "53 apps ... ~60 seconds" while
                         its script globbed 1,449 pages. The false claim is what
                         made bypassing feel reasonable.
    D3 SKIP FLAGS        an advertised escape hatch. A gate that documents its own
                         bypass will be bypassed.
    D4 NO SYS.EXIT       a Python gate that never exits non-zero cannot block.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the gate's LOGIC is correct, only that it is capable of failing and
      honest about its scope. A gate that can fail and checks the wrong thing
      passes here.
    - NOT that the gate is wired up. core.hooksPath unset, or set to a directory
      with no hook file, are separate masks -- both seen today -- and are checked
      by the clone sweep, not by this.
    - NOT that a constructible failing input EXISTS. That question is the real
      detector and it needs a human; this catches four mechanical proxies for it.
"""
from __future__ import annotations
import os, re, sys, io, glob

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PIPE_STATUS = re.compile(r"\|[^\n|]*\n\s*(?:STATUS|RC|rc|status)\s*=\s*\$\?")
BARE_AFTER_PIPE = re.compile(r"^[^#\n]*\|[^\n]*\n\s*\w+=\$\?", re.M)
SCOPE_CLAIM = re.compile(r"(\d[\d,]{1,6})\s*(?:-|\s)?apps?\b", re.I)
GLOB_CALL = re.compile(r"glob\(\s*['\"]([^'\"]+)['\"]")
SKIP = re.compile(r"^\s*if\s*\[\s*\"?\$\{?(SKIP|BYPASS)[A-Z_]*\}?\"?\s*=", re.M)


def check_shell(path, text):
    out = []
    if BARE_AFTER_PIPE.search(text):
        out.append(("D1_PIPELINE_STATUS",
                    "reads $? immediately after a pipeline: that is the LAST stage's "
                    "status, so the failure branch is unreachable"))
    if SKIP.search(text):
        out.append(("D3_SKIP_FLAG", "advertises an environment-variable bypass"))
    return out


def check_scope(hook_text, script_path):
    """Claimed app count in the hook header vs what the script really globs.

    A repaired gate that DOCUMENTS the old false claim must not be flagged for
    quoting it. The first sweep fired on the fixed hook because its header
    explains "the header claimed 53 apps" as part of the repair note - the
    detector was reading a description of the defect as the defect. Any scope
    claim inside a historical block is skipped.
    """
    if re.search(r"WHY THIS FILE WAS REWRITTEN|previous version|was rewritten|"
                 r"the header claimed", hook_text, re.I):
        return []
    m = SCOPE_CLAIM.search(hook_text)
    if not m or not script_path or not os.path.exists(script_path):
        return []
    claimed = int(m.group(1).replace(",", ""))
    st = open(script_path, encoding="utf-8", errors="replace").read()
    g = GLOB_CALL.search(st)
    if not g:
        return []
    root = os.path.dirname(os.path.dirname(os.path.abspath(script_path)))
    actual = len(glob.glob(os.path.join(root, g.group(1))))
    if actual and abs(actual - claimed) > max(5, 0.25 * claimed):
        return [("D2_SCOPE_DISHONEST",
                 "header claims %d apps; the script globs %r and matches %d -- a "
                 "factor of %.1f" % (claimed, g.group(1), actual, actual / max(claimed, 1)))]
    return []


def check_python_gate(path, text):
    if "sys.exit" not in text and "raise SystemExit" not in text:
        return [("D4_NO_EXIT", "no sys.exit anywhere: this gate cannot return non-zero")]
    return []


def scan(roots):
    findings = []
    for root in roots:
        for hook in glob.glob(os.path.join(root, ".githooks", "*")) + \
                    glob.glob(os.path.join(root, ".git", "hooks", "*")):
            # only real hook files: a README in .githooks is documentation, and
            # flagging it was noise that inflated the first sweep.
            if not os.path.isfile(hook) or hook.endswith((".sample", ".md", ".txt")):
                continue
            if os.path.basename(hook) not in (
                    "pre-push", "pre-commit", "commit-msg", "pre-receive",
                    "prepare-commit-msg", "post-checkout"):
                continue
            t = open(hook, encoding="utf-8", errors="replace").read()
            for c, w in check_shell(hook, t):
                findings.append((hook, c, w))
            sp = os.path.join(root, "scripts", "regression_check.py")
            for c, w in check_scope(t, sp):
                findings.append((hook, c, w))
        # D4 applies ONLY to scripts a hook actually invokes. Globbing *gate* and
        # *check* swept in aggregate_multi_agent.py and friends -- reporting tools
        # that were never gates. A detector that flags non-gates for not being
        # gates is measuring the wrong population, and it inflated the first
        # sweep to 217 findings, most of them meaningless.
        invoked = set()
        for hook in glob.glob(os.path.join(root, ".githooks", "pre-*")):
            if os.path.isfile(hook):
                ht = open(hook, encoding="utf-8", errors="replace").read()
                for mm in re.finditer(r"scripts/([A-Za-z0-9_]+\.py)", ht):
                    invoked.add(os.path.join(root, "scripts", mm.group(1)))
        for py in sorted(invoked):
            if not os.path.exists(py):
                continue
            t = open(py, encoding="utf-8", errors="replace").read()
            for c, w in check_python_gate(py, t):
                findings.append((py, c, w))
    return findings


def selftest() -> int:
    """The broken hook is kept as a fixture. A detector proved only on the fixed
    version is the same defect one level up."""
    ok = True
    broken = r"F:\claude-temp\finerenone-pre-push.BROKEN.bak"
    if os.path.exists(broken):
        t = open(broken, encoding="utf-8", errors="replace").read()
        hits = {c for c, _ in check_shell(broken, t)}
        p1 = "D1_PIPELINE_STATUS" in hits
        p3 = "D3_SKIP_FLAG" in hits
        print("  POSITIVE the broken hook: D1 pipeline-status %s, D3 skip-flag %s"
              % ("FIRES" if p1 else "SILENT -- WRONG", "FIRES" if p3 else "SILENT -- WRONG"))
        ok &= p1 and p3
    else:
        print("  POSITIVE fixture absent -- NOT PROVEN"); ok = False
    fixed = r"F:\rapidmeta-ssot-shell\.githooks\pre-push"
    if os.path.exists(fixed):
        t = open(fixed, encoding="utf-8", errors="replace").read()
        hits = {c for c, _ in check_shell(fixed, t)}
        clean = not hits
        print("  NEGATIVE the repaired hook: %s"
              % ("SILENT" if clean else "FIRES on %s -- WRONG" % sorted(hits)))
        ok &= clean
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the broken hook passing, which is a gate "
          "that cannot fail being certified as a gate.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    roots = sys.argv[1:] or [r"F:\rapidmeta-ssot-shell", r"F:\rapidmeta-finerenone"]
    f = scan(roots)
    print("gates scanned across %d root(s); findings: %d" % (len(roots), len(f)))
    for path, code, why in f:
        print("  %-14s %s\n      %s" % (code, path, why))
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
