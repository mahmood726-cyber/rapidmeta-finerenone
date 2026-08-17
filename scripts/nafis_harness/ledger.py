"""THE MISTAKE LEDGER -- one row per mistake, and every row must end in a mechanism.

    "we need to log every mistake we have made so doesn't happen again"
    "so it should be easier each time"                        -- Mahmood

The second line is the specification. This is not an archive. Its purpose is to
make page N+1 cheaper than page N, so an entry that records a mistake without
reducing future cost has not been logged, only remembered. Every row therefore
carries a `guard` -- a named, locatable artefact -- or `NONE`, stated plainly.

THE FIELD THAT DOES THE MOST WORK IS `fix_scope`.
Twice in one day a repair existed and had not arrived everywhere: the pre-push
hook was repaired in some of twelve clones, and a `sys.stdout` defect was fixed
in one module while three siblings carried it. An INSTANCE fix is how a logged
mistake recurs anyway. `fix_scope="instance"` is therefore counted as unguarded
at the class level, not as done.

GUARD STATES -- three, not two, for the same reason verdicts are three-state:
    WIRED     an artefact that runs by itself: a hook, a build gate, a CI step.
              It would fire on a recurrence without anyone choosing to look.
    AVAILABLE a detector exists and is self-tested, but nothing calls it on the
              corpus yet. `nafis_harness` is a library; a library that no build
              invokes catches nothing. Counting AVAILABLE as caught is exactly
              the "CLEAN absorbing unchecked" error (EB-024, 54 apps).
    NONE      no mechanism. This is the work queue.

PROVENANCE TIERS, carried from TAXONOMY.md Sec 0:
    F  read verbatim from a file named in `source`
    R  operator-relayed (Mahmood or another lane), not file-backed here
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


WIRED, AVAILABLE, NONE = "WIRED", "AVAILABLE", "NONE"
INSTANCE, CLASS, NOT_FIXED = "instance", "class", "not-fixed"


@dataclass(frozen=True)
class Row:
    id: str
    believed: str                 # what we believed
    truth: str                    # what was true
    caught_by: str                # how it was actually caught
    autonomous_catch: bool        # would ANYTHING have caught it with no human looking?
    mechanism: str                # taxonomy class
    guard: str                    # named artefact, or "NONE"
    guard_state: str              # WIRED | AVAILABLE | NONE
    fix_scope: str                # instance | class | not-fixed
    source: str                   # where this row is sourced from
    tier: str                     # F | R
    note: str = ""

    @property
    def guarded_at_class_level(self) -> bool:
        return self.guard_state in (WIRED, AVAILABLE) and self.fix_scope == CLASS


# =============================================================================
# ROWS
# =============================================================================
# Sourced. Nothing here is reconstructed from memory; `tier` says which are
# operator-relayed and `source` names the file for the rest.

GATE = "scripts/gate_integrity.py"
REG = "F:/E156/ERROR-REVERSAL-REGISTRY.md"
LIB = "evidence/2026-08-12/search-and-screening/13_ERROR_LIBRARY.md"
RULES = "evidence/2026-08-12/search-and-screening/14_RULE_TESTS_AND_SPECIFICATIONS.md"
DEFECT = "evidence/2026-08-12/count-recovery/DEFECT_LEDGER_cardiology_mortality_atlas.md"
NEGEV = "synthesis-audit/METHODS_negative_evidence.md"
RPT6 = "evidence/2026-08-12/chagas-recovery/corpus_provenance_audit_running_report_6.md"
ROUTE = "evidence/2026-08-12/chagas-recovery/answer_hf_route_log.md"
HARNESS = "HARNESS.md"

ROWS: list[Row] = [

    # ---------------------------------------------------------------- M-GATE
    # "A CHECK THAT REPORTS SUCCESS WITHOUT HAVING PERFORMED THE CHECK."
    # gate_integrity.py: "our most recurrent one". FIVE instances in that file.
    Row("G-01", "the pre-push hook was gating every push",
        "`$?` was read after a pipeline ending in `tail`, so the failure branch "
        "was unreachable; every push from that clone was ungated while printing "
        "'Regression check PASS'",
        "a human read the hook", False, "M-GATE-CANNOT-FAIL",
        f"{GATE} D1_PIPELINE_STATUS + selftest keeps the broken hook as a fixture",
        WIRED, CLASS, GATE, "F",
        "D1 greps every hook and shell script, so the class is covered, not the file"),

    Row("G-02", "the repaired hook was in force across the estate",
        "6 of 12 checkouts still carried the broken hook",
        "a clone sweep", False, "M-INSTANCE-FIX",
        "clone sweep (referenced in gate_integrity.py); NOT a standing artefact",
        NONE, INSTANCE, GATE, "F",
        "gate_integrity.py states the clone sweep is out of its own scope: "
        "'NOT that the gate is wired up... checked by the clone sweep, not by this'"),

    Row("G-03", "figure_audit had checked the pages it passed",
        "it passed pages it could not render; a hidden or 0x0 element was "
        "measured as a silent zero rather than reported unmeasurable",
        "later inspection", False, "M-GATE-CANNOT-FAIL",
        "NONE -- nothing distinguishes 'measured zero' from 'could not measure' "
        "in a renderer; no detector covers it",
        NONE, NOT_FIXED, GATE, "F",
        "this is the three-state failure in a renderer: zero and unmeasurable "
        "share a cell"),

    Row("G-04", "a source leg had verified against the source",
        "it returned a clean verdict having read nothing, because a "
        "corpus-reachable gate handed back our own just-written text",
        "later inspection", False, "M4-SELF-VALIDATION",
        "CHK005_EXTERNAL_REFERENT (per-key locators + document id)",
        AVAILABLE, CLASS, GATE, "F",
        "the harness closes it; nothing in the build calls the harness yet"),

    Row("G-05", "CHK005's mutation test showed the pooled estimate protected",
        "the sweep mutated one key of six -- the pooled value was never mutated, "
        "so the test could not have failed",
        "the corpus lane's mutant set", False, "M-GATE-CANNOT-FAIL",
        "check.py run_vacuity list-returning mutators; test_vacuity_sweeps_every_"
        "key_not_the_alphabetically_first",
        AVAILABLE, CLASS, GATE, "F",
        "MY defect, found by another lane. Recorded here because a ledger of "
        "other people's mistakes is the artefact it was built to prevent"),

    Row("G-06", "the Word/HTML alignment gate compared the manuscripts",
        "it compared only the sections BOTH surfaces emit, so a section present "
        "in one and absent from the other was OUT OF SCOPE rather than a "
        "divergence. The extraction provenance table was missing from every Word "
        "manuscript this project ever produced",
        "a human noticed the missing section", False, "M8-LAYER-SUBSTITUTION",
        "expected-section manifest projected from the object, so absence FAILS "
        "(specified in gate_integrity.py; promotion criterion replayed against "
        "ARNI's pre-port docmodel)",
        WIRED, CLASS, GATE, "F",
        "'A GATE THAT COMPARES ONLY WHAT BOTH SURFACES HAVE CAN NEVER DETECT "
        "ABSENCE -- the intersection is not the expected set'"),

    Row("G-07", "the scope sweep was finding real defects",
        "217 findings, most meaningless: it globbed *gate*/*check* and swept in "
        "reporting tools that were never gates, and it fired on the REPAIRED hook "
        "because the header explains the old false claim as part of the repair "
        "note -- reading a description of the defect as the defect",
        "the lane inspected its own findings", False, "M-DETECTOR-FALSE-POSITIVE",
        f"{GATE} check_scope historical-block skip + D4 restricted to "
        "hook-invoked scripts",
        WIRED, CLASS, GATE, "F",
        "the fix narrowed the population; both repairs are in the shipped file"),

    Row("G-08", "the hook's stated scope was its real scope",
        "the header said '53 apps ... ~60 seconds' while the script globbed 1,449 "
        "pages. The false claim is what made bypassing feel reasonable",
        "a human read both", False, "M7-FRAME-OVERCLAIM",
        f"{GATE} D2_SCOPE_DISHONEST", WIRED, CLASS, GATE, "F", ""),

    # ---------------------------------------------------------- build/render
    Row("B-01", "the provenance conditional selected the right branch",
        "it was inverted",
        "listed in gate_integrity.py as a free discriminating case", False,
        "M-BUILD-PATH",
        "NONE -- named as an untested discriminating case, no detector run on it",
        NONE, NOT_FIXED, GATE, "F",
        "gate_integrity.py: 'most of which no detector has yet been run against'"),

    Row("B-02", "each page carried its own manuscript docmodel",
        "a hardcoded _DOCMODEL put ARNI's manuscript on four other pages",
        "listed as a free discriminating case", False, "M-BUILD-PATH",
        "CHK026_WRONG_REASON_ABSENCE_PANEL / CHK030_BUILD_MODE_BLIND_TEXT",
        AVAILABLE, CLASS, GATE, "F",
        "brief said 'every tabbed build'; the file says 'four other pages'. "
        "Recorded as the file states it"),

    Row("B-03", "converted pages explained their own absences",
        "they rendered ARNI's absence text -- 'reconciled against published "
        "syntheses rather than produced by a database search' -- true of ARNI "
        "and false of a converted page; would have shipped on 28 pages",
        "caught pre-ship by the corpus lane", False, "M-BUILD-PATH",
        "CHK026_WRONG_REASON_ABSENCE_PANEL", AVAILABLE, CLASS,
        "operator-relayed; mechanism corroborated by B-02 in " + GATE, "R",
        "'A panel stating the wrong reason for an absence is worse than a blank "
        "one: the blank makes no claim, this makes a false one'"),

    Row("B-04", "internal markers stayed internal",
        "'NOT RECOVERABLE FROM THE PAGE' was visible to readers nine times",
        "corpus lane", False, "M-RENDER-LEAK",
        "CHK027_SENTINEL_LEAK", AVAILABLE, CLASS, "operator-relayed", "R",
        "positive NOT verifiable in my mount: two bash scans timed out and a host "
        "Grep returned nothing, which per EB-022 is not a zero"),

    Row("B-05", "the text extractor read the whole page",
        "it silently dropped hidden tab panels",
        "corpus lane", False, "M1-DEAD-PLATE",
        "NONE for the extractor; degrade_test.py measures panel visibility but is "
        "a report, not a gate",
        NONE, NOT_FIXED, "operator-relayed; degrade_test.py is [F]", "R",
        "degrade_test.py already prints '*** N/M PANELS HIDDEN WITH NO CONTROL TO "
        "OPEN THEM ***' -- the observation exists and nothing consumes it"),

    Row("B-06", "the Word renderer emitted an extraction section",
        "it never did, in any manuscript the project produced",
        "a human", False, "M8-LAYER-SUBSTITUTION",
        "expected-section manifest (see G-06)", WIRED, CLASS, GATE, "F",
        "same repair as G-06; listed separately because the renderer defect and "
        "the gate's blindness are two mistakes, not one"),

    # ------------------------------------------------------------- parsing
    Row("P-01", "the screening parser split records correctly",
        "an ordinal-split parser merged two screening records into one",
        "listed as a free discriminating case", False, "M-PARSER",
        "NONE -- no detector run on it", NONE, NOT_FIXED, GATE, "F",
        "one of the three screening-parser defects in the brief; the other two "
        "are UNSOURCED and are not given rows"),

    Row("P-02", "numeric comparison handled the corpus's characters",
        "an ASCII-only regex read &minus;71.31 as +71.31; 2 of 7 reported "
        "conflicts were the lane's own defect",
        "the lane checked its own conflicts", False, "M-PARSER",
        "CHK029_SIGN_NORMALISATION (+ the en-dash-range false positive pinned)",
        AVAILABLE, CLASS, f"{GATE} line 48 [F]; the 2-of-7 count is [R]", "F",
        "'A comparison that silently mis-signs a number is worse than one that "
        "fails'"),

    Row("P-03", "the specialty classifier matched specialties",
        "substring matching: AF_ inside TAF_TDF, TAVI inside roTAVIrus",
        "listed as a free discriminating case", False, "M3-MATCH-WITHOUT-REFERENT",
        "CHK002_TOKEN_MATCH (field-scoped + token-bounded)", AVAILABLE, CLASS,
        GATE, "F", ""),

    # ------------------------------------------------------- data / identity
    Row("D-01", "the atlas rows were validated",
        "TWILIGHT carried two irreconcilable denominator pairs; Location B's "
        "denominators exceed the registered randomised total by 2098 and its "
        "death count is 4.3x the registry's, while reproducing its own HR to "
        "three decimals",
        "the count-recovery sweep, 71 days later", False, "M4-SELF-VALIDATION",
        "CHK005_EXTERNAL_REFERENT", AVAILABLE, CLASS, DEFECT, "F",
        "'Consistency does not authenticate a row'"),

    Row("D-02", "classes[20] pooled mortality",
        "TWILIGHT's row is a composite of death, MI and stroke masquerading as "
        "all-cause mortality; the pool (k=2) is invalid",
        "read at source after the denominator work", False, "M6-WRONG-POOL",
        "CHK009_POOL_IDENTITY (outcome/population/window required per row)",
        AVAILABLE, CLASS, DEFECT, "F", ""),

    Row("D-03", "'CANVAS Program' identified the pooled trial",
        "its NCT points at CANVAS alone -- 4330 of 10,143 -- a silent 57% "
        "under-count of the denominator",
        "a lane hit it and stopped", False, "M5-SURFACE-IDENTITY",
        "CHK006_IDENTITY_KEY (registry acronym + enrolment-vs-weight)",
        AVAILABLE, CLASS, DEFECT, "F",
        "'This lane hit it and stopped; the next one may not'"),

    Row("D-04", "corpus trial labels matched their NCTs",
        "19 of 34 adjudicated rows were wrong, including ORION-11 recorded on "
        "ORION-4's NCT -- a 16,124-patient outcomes trial as a 1,617-patient "
        "lipid trial -- and COAST-V on PREVENT (wrong drug, sponsor, population)",
        "a bijection test plus one registry call per conflict", True,
        "M5-SURFACE-IDENTITY",
        "CHK006_IDENTITY_KEY; the full 2,279-NCT cache specified in report #6 "
        "Sec 5 is UNRUN",
        AVAILABLE, CLASS, RPT6, "F",
        "the ONLY row with autonomous_catch=True: the bijection test found the "
        "conflicts mechanically. It is blind to a consistently-applied wrong NCT"),

    Row("D-05", "PARACHUTE-HF and ANSWER-HF were interchangeable for this cell",
        "ANSWER-HF has no CV-death-or-HF-hospitalisation composite at all; the "
        "composite was carried over from PARACHUTE-HF. 'We have been asking this "
        "trial for a cell it never defined'",
        "an adjudication after four rounds of retrieval", False,
        "M5-SURFACE-IDENTITY",
        "CHK006_IDENTITY_KEY refuses identity from a label", AVAILABLE, CLASS,
        ROUTE, "F", ""),

    Row("D-06", "a k=4 headline described the panel beneath it",
        "the panel was k=3; every number individually correct, about different "
        "pools",
        "a human", False, "M6-WRONG-POOL", "CHK009_POOL_IDENTITY", AVAILABLE,
        CLASS, "operator-relayed", "R", ""),

    Row("D-07", "the estimate and its interval described the recorded sample",
        "MAVACAMTEN's claimed OR 6.67 (2.09-21.30) implies SE 0.5922; the "
        "recorded arms 45/123 vs 22/128 imply SE 0.2999 and OR 2.780. Estimate "
        "and interval both came from elsewhere",
        "the corpus lane's precision sweep", False, "M-PRECISION-MISMATCH",
        "CHK016_PRECISION_SAMPLE_MISMATCH", AVAILABLE, CLASS,
        "operator-relayed; arithmetic verified independently", "R",
        "needs only the row -- no source, no registry, no network"),

    Row("D-08", "a k=2 pool with I2=0 showed two trials agreeing",
        "both entries carried the bit-identical estimate -0.15082288973458366; "
        "inverse-variance pooling of one repeated value returns it regardless of "
        "weights, so the I2=0 is an artefact of the duplication",
        "the corpus lane", False, "M5-SURFACE-IDENTITY",
        "CHK017_DUP1_BIT_EQUALITY", AVAILABLE, CLASS, "operator-relayed", "R", ""),

    Row("D-09", "the ablation card and its page said the same thing",
        "the card contradicted the page",
        "corpus lane", False, "M-MULTI-SURFACE",
        "CHK025_MULTI_SURFACE_DISAGREEMENT (has a known false positive on "
        "rounding)", AVAILABLE, CLASS, "operator-relayed", "R", ""),

    Row("D-10", "the extractor object was a usable referent",
        "DOAC_CANCER_VTE's object (OR 0.7290) contradicts a source-verified card "
        "(HR 0.55); the object had already been disqualified as a referent that "
        "morning, and converting would have put it on the page",
        "the corpus lane, pre-ship", False, "M4-SELF-VALIDATION",
        "CHK028_DISQUALIFIED_REFERENT_PROMOTED (hard block, sourced wins)",
        AVAILABLE, CLASS, "operator-relayed", "R", ""),

    # ------------------------------------------------------ absence / search
    Row("A-01", "'not encountered' recorded a search",
        "PMID 34395116 sat in the corpus reporting exactly the class asserted "
        "absent; the sentence was prose, not a search",
        "us, one step later", False, "M1-DEAD-PLATE",
        "Rule 4 v2 execution record; CHK007_ABSENCE_SCREEN", AVAILABLE, CLASS,
        LIB, "F", "'The rule as written would have licensed that sentence rather "
        "than caught it'"),

    Row("A-02", "the registered search missed no randomised trial",
        "the claim was measured against 44 of a 244-synthesis frame -- 18% -- by "
        "a method structurally blind to preprints",
        "running the frame query", False, "M7-FRAME-OVERCLAIM",
        "CHK008_FRAME_DENOMINATOR", AVAILABLE, CLASS, LIB, "F", ""),

    Row("A-03", "backward citation had found records the databases missed",
        "it found none; two studies were matched by surname and sample size and "
        "were already in the corpus",
        "resolving the reference list to PMIDs", False, "M5-SURFACE-IDENTITY",
        "CHK006_IDENTITY_KEY", AVAILABLE, CLASS, LIB, "F", ""),

    Row("A-04", "Europe PMC had no record",
        "the fetch returned HTTP 429; a rate-limited request returns the same "
        "thing whether the record exists or not",
        "the lane asked what the instrument could have shown", False,
        "M1-DEAD-PLATE", "CHK001_RETRIEVAL_ABSENCE", AVAILABLE, CLASS, NEGEV,
        "F", ""),

    Row("A-05", "the OpenAthens pass-through failed",
        "a ref-based click returned without error having silently no-op'd; a "
        "coordinate click worked immediately",
        "retrying by another route", False, "M2-NO-ERROR-AS-EFFECT",
        "CHK003_ACTION_EFFECT", AVAILABLE, CLASS, NEGEV, "F", ""),

    Row("A-06", "institutional access opens at most 6 of 15 closed records",
        "the probe counted a full-text HOSTING table; entitlement is resolved at "
        "the end of a link-resolver chain and is not represented in a holdings "
        "table at all. The claim was backwards and had reached the spine of the "
        "paper",
        "a human asking what the instrument measured", False,
        "M8-LAYER-SUBSTITUTION",
        "CHK012_LAYER_MATCH -- PARTIAL: fires only when both layers are labelled",
        AVAILABLE, INSTANCE, NEGEV, "F",
        "the known hard case. validator-validation-protocol.md Sec 6 marks this "
        "class NOT CAUGHT by any coverage, mutation or vacuity criterion"),

    Row("A-07", "the Ioannidis paper is blocked at Tier 4",
        "a title search in the wrong database, stopped at hop zero; the record "
        "is four hops further on and the paper is entitled, with a PDF offered",
        "working the chain", False, "M9-CHAIN-ABANDONED",
        "CHK010_CHAIN_EXHAUSTION", AVAILABLE, CLASS, NEGEV, "F", ""),

    Row("A-08", "PMID 17715249 was entitled",
        "LibKey rendered a DOWNLOAD PDF button, which renders from metadata and "
        "does not prove delivery. No PDF was ever seen",
        "the account holder clicked it himself and got nowhere", False,
        "M2-NO-ERROR-AS-EFFECT", "CHK003_ACTION_EFFECT + CHK012_LAYER_MATCH",
        AVAILABLE, CLASS, NEGEV, "F",
        "the sign-flipped case: 'it was the good news'"),

    Row("A-09", "a domain-restricted search was restricted",
        "WebSearch's allowed_domains is silently ignored by the backend; two "
        "'no EMA document exists' verdicts were reached through it",
        "the lane distrusted them", False, "M1-DEAD-PLATE",
        "CHK014_FILTER_FIRED (registry P34, now code)", AVAILABLE, CLASS, REG,
        "F", "'Both were correctly discarded -- but only because the lane "
        "distrusted them'"),

    Row("A-10", "a Chinese-language search ran",
        "PubMed discarded every CJK character and returned 471,547 hits; the "
        "search never ran and looked exactly as though it had",
        "the hit count", False, "M1-DEAD-PLATE",
        "CHK015_HIT_COUNT_SANITY (registry P33, now code)", AVAILABLE, CLASS,
        REG, "F", ""),

    # ------------------------------------------------------------ corrections
    Row("C-01", "the citation year needed correcting",
        "the 'correction' changed a value to make a test pass -- the correction "
        "was itself the error",
        "listed as a free discriminating case", False, "M10-BAD-CORRECTION",
        "CHK011_CORRECTION_BURDEN (requires a newly retrieved source)",
        AVAILABLE, CLASS, GATE, "F",
        "gate_integrity.py's phrasing is sharper than my earlier record: not a "
        "wrong field, but a value changed to make a test pass"),

    Row("C-02", "'a bash zero is not a zero' made the live toolchain safe",
        "the rule wrongly acquitted the whole live toolchain and misled runs for "
        "~7 hours; a directory-Grep zero is not a zero either",
        "a dead-regex branch test", False, "M10-BAD-CORRECTION",
        "CHK011_CORRECTION_BURDEN", AVAILABLE, CLASS, REG, "F",
        "the correction re-interpreted the same mount instead of retrieving a "
        "new source -- the discriminator CHK011 encodes"),

    Row("C-03", "two published syntheses had pooled cohorts and discordant "
        "composites undeclared",
        "both had declared the practice in their own methods; 2 of 3 accusations "
        "were withdrawn on verification",
        "verification before publication", False, "M10-BAD-CORRECTION",
        "Rule 1 v2 (scope to the claim, search three locations)", AVAILABLE,
        CLASS, LIB, "F",
        "'They are the reason the remaining entry can be relied on'"),

    Row("C-04", "requiring per-key provenance fixed CHK005",
        "it broke the honest caller: Arm A fell 7/7 -> 2/7, five real kills "
        "becoming five refusals",
        "the benchmark lane's mutant set", True, "M10-BAD-CORRECTION",
        "provenance now gates the AGREEMENT path only; "
        "test_unprovenanced_referent_still_reports_a_disagreement",
        AVAILABLE, CLASS, HARNESS, "F",
        "MY defect. My own mutation suite scored it 0 survivors and clean"),

    Row("C-05", "an off-by-one enrolment inside the tolerance band was fine",
        "CHK006 returned PASS on 33758 -> 33759 because 1 is far inside "
        "max(0.1*enrol, 50); a tolerance says the instrument cannot resolve "
        "differences of that size and must not clear them",
        "the benchmark lane's mutant set", True, "M-GATE-CANNOT-FAIL",
        "CHK006_IDENTITY_KEY now returns INVALID inside the band unless "
        "enrolment_delta_explained is supplied", AVAILABLE, CLASS, HARNESS, "F",
        "MY defect, found by a mutant my own suite had no case for"),

    # ------------------------------------------------------- rules / process
    Row("R-01", "five propagated rules would catch their classes",
        "three of five needed repair, and Rules 4 and 5 were incapable of firing "
        "on the failures they existed to prevent; Rule 5 v2 then fired on the "
        "library that defined it",
        "adversarial testing before propagation", True, "M11-UNFIRED-RULE",
        "Registry.register raises without a must_fire_on and a must_be_silent_on "
        "fixture; controls re-run every execution", AVAILABLE, CLASS, RULES, "F",
        "'a rule that cannot fire is not a rule'"),

    Row("R-02", "a sys.stdout defect was fixed",
        "it was fixed in one module while three siblings carried it",
        "a human", False, "M-INSTANCE-FIX", "NONE", NONE, INSTANCE,
        "operator-relayed", "R",
        "no artefact sweeps sibling modules for a repaired defect. This is the "
        "same shape as G-02"),

    Row("R-03", "81 commits were unpushed work at risk",
        "forcing that push would have destroyed the day's work",
        "Mahmood did not act on the advice", False, "M-ADVICE-UNVERIFIED",
        "NONE", NONE, NOT_FIXED, "operator-relayed (Mahmood, this session)", "R",
        "no mechanism proposed. An assistant's own claim about repository state "
        "is an extraction like any other and had no witness, no instrument "
        "declaration, and no statement of what the opposite would have looked "
        "like. It is the highest-severity unguarded row in this ledger"),

    # =========================================================== 2026-08-17
    # The wrong-tree gate, and the matched pair that explains the whole ledger.

    Row("W-01", "every regression PASS today was measured against the pages "
        "being pushed",
        "regression_check.py hardcoded localhost:8787, and that port was held by "
        "a SIBLING WORKING TREE of the same repo on a different branch. ARNI came "
        "over the wire at 912,140 bytes against 6,147,695 on disk. Every green "
        "verdict all day was measured against files that were not being pushed",
        "a fixture that should have 404'd returned 200", False,
        "M-GATE-CANNOT-FAIL",
        ".githooks/pre-push nonce block: a value written into THIS tree and "
        "fetched over HTTP, refusing with a port switch if it does not return",
        WIRED, CLASS, "F:/rapidmeta-ssot-shell/.githooks/pre-push lines 144-176",
        "F",
        "WHY A NONCE AND NOT A HASH: two clones of one repo agree on file content "
        "constantly, so any content comparison passes. Only a value that did not "
        "exist a moment ago cannot be satisfied by a stranger. 'index.html "
        "answering proves SOMETHING is there. It cannot prove it is us.'"),

    Row("W-02", "the vendor probe and the regression probe were both checking "
        "what they named",
        "both hit the wrong target. The agy probe hit the wrong quota pool and "
        "reported a FALSE DEATH -- caught within minutes. The regression probe "
        "hit the wrong working tree and reported FALSE LIFE -- survived the whole "
        "day, including being relayed to Mahmood as evidence things were fine",
        "the false death by its own alarm; the false life by an unrelated fixture",
        False, "M-SELECTION-BY-COMFORT",
        "the nonce (W-01) closes the identity half; nothing closes the general "
        "case of a probe that cannot name its target",
        WIRED, INSTANCE,
        "F:/rapidmeta-ssot-shell/.githooks/pre-push lines 144-155 [F]; the agy "
        "quota-pool half is operator-relayed", "R",
        "*** THE HEADLINE ROW. Same root cause, opposite direction, and the "
        "survival time is explained entirely by which way it failed. A false "
        "death interrupts you; a false life congratulates you. The comfortable "
        "failure is the one that lasts, and that is not a fact about "
        "attention -- it is a selection effect on which errors get investigated. "
        "It is the sharpest evidence in this ledger for FINDINGS.md Finding 2. ***"),

    Row("W-03", "requiring a constructible failing input was a discipline cost",
        "it paid for itself immediately and sideways: a fixture built only to "
        "prove a detector COULD fail got a 200 where it should have got a 404, "
        "which is how the wrong-tree defect (W-01) was found at all",
        "constructing the failing input", True, "M-DISCIPLINE-PAYOFF",
        "gate_integrity.py promotion criterion: 'For every gate, ask: WHAT INPUT "
        "WOULD MAKE THIS FAIL? Construct it and show it failing.'",
        WIRED, CLASS, "F:/rapidmeta-ssot-shell/scripts/gate_integrity.py", "F",
        "Logged as the ARGUMENT FOR THE STANDARD, not a footnote: the discipline "
        "discovered an unrelated and larger defect while verifying something "
        "else. That is the return on it, and it is not hypothetical"),

    Row("W-04", "the render flakiness had a diagnosis",
        "two confident diagnoses, both wrong -- a rate limiter (mine) and stale "
        "browser state (the lane's). It was neither: the value was being sampled "
        "before it settled",
        "testing both hypotheses", False, "M-CONFIDENT-WRONG-DIAGNOSIS",
        "NONE -- no artefact. Recorded because the diagnoses were CHEAP: both "
        "were testable, and being wrong cost minutes",
        NONE, NOT_FIXED, "operator-relayed", "R",
        "worth a row precisely because they were wrong and harmless. A wrong "
        "diagnosis that is cheap to test is not a defect in judgement; it is the "
        "system working. Contrast R-03, where the wrong claim was not testable "
        "and would have destroyed a day"),

    Row("W-05", "these checks measured what they asserted",
        "three assert more than they measure: `zero_included` (since renamed "
        "`no_studies_rendered`, which is what it actually observes), the RoB "
        "banner signal, and my raw-HTML rule",
        "renaming one of them exposed the pattern", False, "M-OVER-ASSERTION",
        "NONE as code. The rename is the only repair, and it is one instance of "
        "three",
        NONE, INSTANCE, "operator-relayed", "R",
        "the general form: a check's NAME is a claim about what it observed, and "
        "nothing tests the name against the observation. `no_studies_rendered` is "
        "true; `zero_included` was a claim about the object from a measurement of "
        "the page"),

    Row("W-06", "the harness was built, therefore the harness was delivered",
        "it lives in a Cowork session outputs directory that is NOT A GIT "
        "REPOSITORY. `git rev-parse --show-toplevel` returns 'not a git "
        "repository'. 27 files, 116 passing tests, zero of them tracked, "
        "committed or pushed. The corpus lane searched F: to depth 4, 40 commits "
        "on every branch, and every commit that ever added a *HANDOFF* file, and "
        "found nothing -- correctly, because nothing is there",
        "the corpus lane could not find it and said so", False,
        "M-INSTANCE-FIX",
        "NONE -- and the durable_artefact_gate this project already ships would "
        "have caught it: verdict UNTRACKED",
        NONE, NOT_FIXED,
        "measured this session: git rev-parse in "
        "local_758bb69d-.../outputs returns not-a-repository", "F",
        "*** MINE, and it is the pattern arriving at the lane that wrote the "
        "pattern down. G-02 logged a hook repaired in 6 of 12 clones; R-02 "
        "logged a defect fixed in 1 of 4 modules; this logs a harness delivered "
        "to 0 of 1 repositories. The repair existing is not the repair arriving, "
        "and I wrote that sentence before committing the instance. Worth noting "
        "that I ran durable_artefact_gate's own criteria against everything "
        "EXCEPT my own output. ***"),

    Row("W-07", "the rise from 10.9% to 15.7% was the nonce fix landing",
        "NO ROW MOVED FROM AVAILABLE TO WIRED. The three extra WIRED rows -- "
        "W-01, W-02, W-03 -- are new rows that were already guarded when "
        "written, and W-03's guard is gate_integrity.py's promotion criterion, "
        "which predates today and is not the nonce. Holding the row set fixed at "
        "the original 46, the figure is unchanged at 10.9%",
        "the corpus lane asked me to name the three rows that moved", False,
        "M7-FRAME-OVERCLAIM",
        "test_ledger.py now asserts no row is described as having moved without "
        "a before/after state recorded",
        AVAILABLE, CLASS, "measured this session against ROWS", "F",
        "a denominator that grows by five while the numerator grows by three "
        "raises a percentage without anything being guarded. I reported the rise "
        "as evidence of progress. It was arithmetic"),

    Row("R-04", "search breadth was adequate",
        "UNKNOWN -- 0 confirmed breadth failures against 22 checking failures, "
        "and both instruments that measure breadth are field-internal",
        "not caught; not measured", False, "M-UNMEASURED",
        "NONE -- CHK031_SEARCH_RECALL is written but HELD OUT of the registry "
        "because no real positive exists, so it guards nothing today",
        NONE, NOT_FIXED, RPT6, "F",
        "'Zero breadth failures remains NOT YET CAUGHT'"),
]


# =============================================================================
# MEASUREMENT -- computed, never typed
# =============================================================================

def effective_guard_state(row: Row, gate_installed: bool) -> str:
    """WIRED is DETECTED, not declared.

    A row guarded by an artefact-decidable detector becomes WIRED the moment the
    harness gate is actually installed in a repo -- and not one moment earlier,
    however much work went into building the detector. `wiring.detect()` supplies
    `gate_installed`; nothing here can set it.
    """
    if row.guard_state != AVAILABLE:
        return row.guard_state
    if not gate_installed:
        return AVAILABLE
    from .artefact import ARTEFACT_DECIDABLE
    for tok in row.guard.replace("(", " ").replace(")", " ").split():
        if tok.rstrip(";,.") in ARTEFACT_DECIDABLE:
            return WIRED
    return AVAILABLE


def summarise(rows: list[Row] | None = None, *,
              gate_installed: bool | None = None) -> dict:
    rows = ROWS if rows is None else rows
    if gate_installed is None:
        from .wiring import detect
        gate_installed = detect()["installed"]
    n = len(rows)
    states = {r.id: effective_guard_state(r, gate_installed) for r in rows}
    by_state: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    by_mech: dict[str, int] = {}
    for r in rows:
        st = states[r.id]
        by_state[st] = by_state.get(st, 0) + 1
        by_scope[r.fix_scope] = by_scope.get(r.fix_scope, 0) + 1
        by_mech[r.mechanism] = by_mech.get(r.mechanism, 0) + 1

    wired = by_state.get(WIRED, 0)
    available = by_state.get(AVAILABLE, 0)
    none = by_state.get(NONE, 0)
    class_scoped = sum(1 for r in rows if r.guarded_at_class_level)
    autonomous = sum(1 for r in rows if r.autonomous_catch)

    return {
        "rows": n,
        "gate_installed": gate_installed,
        "by_guard_state": by_state,
        "by_fix_scope": by_scope,
        "by_mechanism": dict(sorted(by_mech.items(), key=lambda kv: -kv[1])),
        # THE HEADLINE, three ways, because one number would hide the answer
        "caught_today_if_wired_only": round(wired / n, 3),
        "caught_today_if_harness_invoked": round((wired + available) / n, 3),
        "unguarded": round(none / n, 3),
        "guarded_at_class_level": round(class_scoped / n, 3),
        "caught_autonomously_when_it_happened": round(autonomous / n, 3),
        "tier_F": sum(1 for r in rows if r.tier == "F"),
        "tier_R": sum(1 for r in rows if r.tier == "R"),
    }


def unguarded_queue(rows: list[Row] | None = None) -> list[Row]:
    """The work queue: no mechanism, or a mechanism applied only to the instance."""
    rows = ROWS if rows is None else rows
    return sorted([r for r in rows
                   if r.guard_state == NONE or r.fix_scope == INSTANCE],
                  key=lambda r: (r.guard_state != NONE, r.id))


def to_dicts(rows: list[Row] | None = None) -> list[dict]:
    return [asdict(r) for r in (ROWS if rows is None else rows)]
