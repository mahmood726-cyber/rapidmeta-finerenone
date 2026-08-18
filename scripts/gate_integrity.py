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

    THE COMPANION RULE, AND THE ONE THIS PROJECT HAS HAD TO RE-LEARN FOUR TIMES:

        A VERDICT THAT MEANS "I COULD NOT CHECK" IS NEVER A PASS.
        NOT_APPLICABLE IS NEVER A PASS.
        UNCHECKABLE IS NEVER A PASS.
        UNMEASURED IS NEVER A PASS.
        AND NONE OF THEM MAY BE COUNTED INTO A CLEAN DENOMINATOR.

    This is stated HERE, once, because it has been restated locally in four gates
    and four copies of one rule drift apart. Each of the four earned it against a
    real artefact:

      card_alignment_gate      an audit-first card is UNCHECKABLE by construction.
                               Folding those into the pass count reported "0.0%
                               drift" over 1.2% of the corpus -- a reassuring
                               headline computed over the sliver that could be
                               read, with the enormous unmeasured remainder
                               presented as if it were not there.
      declared_contrast_gate   a two-arm registration returns NOT_APPLICABLE. Only
                               one contrast is possible, so the trial can neither
                               exhibit the defect nor clear itself of it. Counting
                               those as passes would let a corpus of two-arm trials
                               report 100% clean while establishing nothing.
      arm_identity_gate        arm labels that identify nothing ('1' vs '2') are
                               UNCHECKABLE. The gate that returned PASS on finding
                               nothing to inspect is how eleven properties were
                               once claimed where four were established.
      estimand_definition_gate a definition containing an unrecognised event term
                               is UNCHECKABLE and OUTRANKS both PASS and WITHDRAWN,
                               because a partial reading that reports agreement is
                               the CKD false agreement.

    THE TEST FOR WHETHER A VERDICT IS BEING MISCOUNTED: ask what the check would
    report over a corpus in which it can see NOTHING AT ALL. If the answer is
    anything other than "nothing was established", the not-a-pass verdicts are
    leaking into the pass count.

    AND A PROPORTION MUST CARRY ITS COMPARABLE FRACTION INLINE OR REFUSE TO
    RENDER. "0.0% drift" and "0.0% drift over 6 of 514 cards" are different
    claims, and only the second one is true.

    The shape is identical in all five: the SUCCESS PATH IS REACHABLE AND THE
    FAILURE PATH IS NOT. A green result is therefore evidence of nothing, and
    nobody investigates a green result -- which is why these survive.

    SIXTH INSTANCE, AND THE FIRST ON THE MEASURING SIDE RATHER THAN THE CHECKING
    SIDE. A lane nearly reported the extraction table as MISSING from a page that
    has it: its text extractor returned 0 occurrences of "Sources" in 101,864
    characters, and was wrong. The instrument silently omitted content. It caught
    itself only because a second read of the raw HTML contradicted it.

    A MEASUREMENT INSTRUMENT THAT SILENTLY OMITS CONTENT IS THE SAME MECHANISM AS
    A GATE PASSING HAVING READ NOTHING. In both, the failure is invisible because
    the output is well formed: "0 occurrences" and "PASS" are equally ordinary
    results, and neither carries any signal that the input was incomplete.

    SO THE RULE IS: any page-content check must read RAW HTML, never rendered-text
    extraction. But the rule has a second half, and missing it produced a wrong
    number within the hour of adopting the first half:

        RAW HTML DOES NOT MISS HIDDEN CONTENT. IT OVER-COUNTS SOURCE AS CONTENT.

    A census of resolvable source links over raw HTML returned "62.8% of pages
    carry a registry or PubMed link". They do not. The matches were JavaScript
    TEMPLATE SOURCE inside <script> -- href="https://clinicaltrials.gov/study/
    ${escapeHtml(t.id)}" -- counted as links because a raw-HTML regex cannot tell
    a string literal in a program from an attribute in a document. Recomputed with
    <script>/<style> BODIES dropped and ${...} placeholders excluded, the figure
    was 2.2%.

    LOGGED AS A RULE REGRESSION, NOT JUST A MISTAKE. "Read raw HTML, never
    rendered-text extraction" was ADOPTED AS A RULE in response to the
    under-counting instance, and within the hour it made a measurement WORSE than
    no rule at all: 62.8% against a true 2.2%, a factor of forty, AND IT ERRED IN
    THE REASSURING DIRECTION -- it said the corpus was well sourced when it is
    not. A rule that fails toward comfort will not be questioned, because its
    output is the answer everyone hoped for.

    So rules earn the same treatment as gates: state what a rule does NOT
    establish at the moment it is adopted, and re-derive one number under the new
    rule and the old one before trusting it. The half-rule was correct about what
    it was reacting to and silently wrong about everything else, which is the
    normal shape of a rule written from a single incident.

    Neither instrument alone is correct:
        rendered text   omits what is not displayed   -> UNDER-counts
        raw HTML        includes what is not content  -> OVER-counts
    Read raw HTML so nothing hidden is lost, then ATTRIBUTE CONTENT TO ITS
    CONTEXT: script and style bodies are program text, not page content. Note
    this is the same correction already applied to index_markup_gate, which on
    its first run flagged three anchors inside a script comment -- the corpus has
    now taught this lesson twice in one day, in opposite directions.

    AND WHEN A PAGE BUILDS ITS OWN DOM, SAY WHICH ONE YOU MEASURED. "In the
    served markup" and "after JavaScript runs" are different claims about
    different readers. On this corpus they differ by a factor of forty: 2.2% of
    pages carry a resolvable registry link in the markup, while 27 of 31 sampled
    pages carry one once the page has run. Reporting either alone, without
    naming which, is a true sentence that misleads.

THE MATCHED PAIR -- THE CLEANEST EVIDENCE IN THIS FILE
    Two probes, one root cause, opposite failure directions, wildly different
    survival times. This is the selection principle demonstrated rather than
    argued.

    ROOT CAUSE, both cases: A PROBE THAT ESTABLISHES SOMETHING ANSWERS, NEVER
    THAT THE RIGHT THING ANSWERS.

    FALSE DEATH -- the agy liveness probe queried the wrong model pool and
      reported a seat dead that was fully alive. Cost: an entire verification
      family stood down. CAUGHT THE SAME DAY, because "the seat is dead" is an
      alarming result and somebody immediately went and looked.

    FALSE LIFE -- the regression gate probed `curl -sf .../index.html` on port
      8787 and reused whatever answered. What answered was a SIBLING WORKING TREE
      of the same repository on a different branch. The gate loaded, measured and
      PASSED pages that were not the pages being pushed -- ARNI at 912,140 bytes
      over the wire against 6,147,695 on disk. SURVIVED ALL DAY, and every green
      it produced was relayed upward as confidence, because "regression check
      PASS" is exactly what everyone wanted to read.

    Same defect class. One was caught in hours, the other ran a full day feeding
    false assurance into reports, AND THE ONLY DIFFERENCE WAS WHICH DIRECTION IT
    FAILED IN. Nothing about the false-life version was subtler or better hidden.
    It simply never gave anyone a reason to look.

    Note also that clones make hash- and size-comparison useless as an identity
    check here: two working trees of one repository agree on most files most of
    the time, so any comparison of EXISTING content passes constantly. The only
    probe another directory cannot satisfy is a NONCE -- content that did not
    exist anywhere a moment ago. And the response to a failed identity check is
    REFUSE (exit 2), not warn: a gate reading another directory is worse than no
    gate, because no gate at least never produces a green.

THE PAYOFF CASE FOR "A GATE NEEDS A CONSTRUCTIBLE FAILING INPUT"
    The wrong-tree defect was not found by looking for it. It was found because
    the three-state verdict needed a fixture that could FAIL, the real pages
    could not produce one (the double-load warms the cache, so they always
    passed), and a purpose-built fixture therefore had to be written -- which
    then 404'd against a server that was returning 200 for every real page.

    THE DISCIPLINE DID NOT MERELY VERIFY THE CHECK IT WAS APPLIED TO. IT
    DISCOVERED AN UNRELATED AND MUCH LARGER DEFECT. That is the argument for the
    standard, and it belongs here rather than in a footnote: insisting on a
    constructible failure forces you to interact with the system in a way that
    passing tests never do, and the discrepancies you trip over on the way are
    frequently worth more than the check you set out to build.

THE OTHER META-MECHANISM -- THE ACTION SUCCEEDED, THE EFFECT WAS NEVER CONFIRMED
    Four instances, and it may be the most productive pattern in this file:

        PUSH IS NOT DEPLOY               the ref moved; the site served the old bytes
        THE REPAIR EXISTING IS NOT THE REPAIR ARRIVING
                                         the hook was fixed; 6 of 12 checkouts still ran the old one
        A LIBRARY NO BUILD INVOKES CATCHES NOTHING
                                         the detector was correct and was never called
        WRITING AN ARTEFACT IS NOT PRESERVING IT
                                         the waiver register was written into gitignored outputs/;
                                         it wrote fine, read back fine, and existed in no clone

    In every one the actor had every reason to believe it had worked, BECAUSE THE
    ACTION ITSELF SUCCEEDED AND REPORTED SUCCESS. `git push` exits 0. The editor
    saves. `open(path, "w")` returns. Nothing anywhere is lying; the confirmation
    simply answers a different question from the one that matters.

    THE QUESTION IS NEVER "DID I DO IT". IT IS "DID IT LAND WHERE IT HAS TO BE."
    Those come apart whenever an artefact must cross a boundary to take effect --
    a deploy, a clone, a working tree, an import. Every such boundary needs its
    own confirmation, taken FROM THE FAR SIDE: fetch the served bytes, run the
    hook from a second checkout, assert the detector was invoked, ask git whether
    the file is tracked.

    And note the direction, which is why all four survived: EVERY ONE FAILS
    TOWARD COMFORT. An untracked backlog does not error, it quietly stops
    existing, and the corpus then looks better than it is.

THE MECHANISM BEHIND THE MECHANISM -- WHICH DIRECTION DOES THE FAILURE POINT?
    Ask of every check, gate, rule and instrument: WHEN THIS IS WRONG, IS ITS
    OUTPUT ALARMING OR REASSURING?

        Fails toward ALARM   -> someone investigates -> it gets fixed or removed.
                                It cannot survive long, because a false alarm is
                                expensive to whoever is standing next to it.
        Fails toward COMFORT -> nobody investigates a green result -> it survives
                                indefinitely, and its survival is mistaken for
                                its being correct.

    EVERY MECHANISM FOUND IN THIS PROJECT FAILED TOWARD COMFORT. That is not
    coincidence, it is SELECTION. The alarming ones were all removed years ago by
    whoever got tired of them; what remains in any long-lived codebase is
    disproportionately the set of checks that are wrong in the pleasant direction.

      - the pre-push hook that printed PASS because $? read `tail`   -> comfort
      - figure_audit scoring an unrenderable element as zero         -> comfort
      - a source leg verifying against our own just-written text     -> comfort
      - a mutation test that never mutated the value it protects     -> comfort
      - an alignment gate comparing only the intersection, so every
        MISSING section was out of scope rather than a divergence    -> comfort
      - a text extractor silently dropping content: "0 occurrences"  -> comfort
      - "read raw HTML", which counted <script> template source and
        reported 62.8% sourced against a true 2.2%                   -> comfort

    Seven mechanisms, seven in the same direction, zero in the other. A set that
    lopsided is not a sample of our mistakes -- it is a sample of the mistakes
    that were ABLE TO LAST.

    PRACTICAL CONSEQUENCE, and the reason this is written here rather than
    admired: comfortable failure modes cannot be found by waiting for them to
    cause trouble, because not causing trouble is precisely their property. They
    have to be hunted deliberately. So when adding any check, write down its
    comfortable failure mode FIRST -- the specific way it could report success
    having established nothing -- and then construct that input and confirm it
    blocks. If you cannot construct it, you have not understood the check yet.

    And prefer designs where the comfortable direction is unavailable: a manifest
    of EXPECTED sections rather than a comparison of shared ones; UNMEASURED as a
    distinct verdict from PASS; an unloadable page recorded as unmeasured rather
    than as zero links. In each case the fix was not a better check but a shape in
    which silence cannot be read as success.

PROMOTION CRITERION -- REPLAY A REAL PAST DEFECT
    A synthetic failing input proves a detector CAN fire. It does not prove the
    detector DISCRIMINATES: a rule that fires on everything also passes that test.
    Where a real past defect exists, replay it, and require the detector to fire on
    it AND stay silent on the parts that were genuinely fine.

    Worked example: the section-manifest gate was run against ARNI's pre-port
    manuscript docmodel taken from git. It fired on extraction_provenance -- the
    one section actually missing -- and passed certainty, pooled_result,
    published_comparison, risk_of_bias and screening, all five of which were fine.
    A synthetic deletion could not have established that.

    Free discriminating cases already sitting in this repo's history, most of which
    no detector has yet been run against:
      - the inverted provenance conditional in build_app_v2
      - the hardcoded _DOCMODEL that put ARNI's manuscript on four other pages
      - the ordinal-split parser that merged two screening records into one
      - the unicode-minus comparison that made -71.31 read as +71.31
      - the substring classifier matching AF_ inside TAF_TDF, TAVI inside roTAVIrus
      - the citation-year "correction" that changed a value to make a test pass
    A detector promoted without being run against at least one of these has been
    tested only against its author's imagination.

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
