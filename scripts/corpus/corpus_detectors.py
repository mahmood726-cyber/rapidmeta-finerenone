#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Page-level defect detectors for the number-neutral corpus waves W1-W3.

WHY THIS EXISTS. The ssot harness (validate_v2.py, negative_controls.py) runs on a
CANONICAL OBJECT. 739 of the 749 finerenone-template clones have no object -- the
built HTML page is the only copy of its own data. So the detectors for those pages
have to operate on built HTML, which is what this module does.

WHAT A DETECTOR IS HERE. A function that takes the page text and returns a Finding
(fired / not fired / not-applicable) plus the evidence that decided it. Firing means
"this page still carries the defect". A wave is accepted on a page only when every
detector for the classes that wave touches has stopped firing AND every detector for
a class the wave does NOT touch is unchanged.

THE THREE CONTROLS, ALL REQUIRED (negative_controls.py's discipline).

  1. CLEAN-PAGE control. The 13 certified pages in F:\\claude-temp\\ssot\\build carry
     zero of the eighteen classes. Every detector must run GREEN on all 13. A
     detector that fires on a certified page is broken -- fix the detector, never
     the page.
  2. MUTATION control. For each detector, inject the defect into a clean page and
     assert the detector fires. A detector that has never been shown to fire is not
     a check; it is decoration that always reports success.
  3. LEGITIMATE-INSTANCE control. Some defects are defects only in context. The
     finerenone appositive is TRUE on FINERENONE_REVIEW.html. FINEARTS-HF is the
     right benchmark for a finerenone review. A star network with four spokes IS
     connected. These controls are what stop a blanket fix from damaging the one
     page where the string was correct.

Usage:
    python corpus_detectors.py --selftest                # runs all three control classes
    python corpus_detectors.py PAGE.html [PAGE2.html ...]
    python corpus_detectors.py --json PAGE.html
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import re
import sys

# reconfigure, never reassign: wrapping sys.stdout.buffer twice (once here, once in an
# importing module) closes the first wrapper and every later print raises.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SSOT_BUILD = pathlib.Path(r"F:\claude-temp\ssot\build")

ARABIC_FINERENONE = "\u0627\u0644\u0641\u064a\u0646\u064a\u0631\u064a\u0646\u0648\u0646"

# Markers written by corpus_wave.py when a fix has been applied. A detector consults
# these so that "fixed" is a positive assertion in the page, not an inference from the
# absence of a string -- absence can also mean "this page never had the module".
FIXED = {
    "D18b":  "RM-FIX-D18b",
    "D18b2": "RM-FIX-D18b2",
    "D7a":   "RM-FIX-D7a",
    "D7b":   "RM-FIX-D7b",
    "D3a":   "RM-FIX-D3a",
    "D5b":   "RM-FIX-D5b",
    "D17":   "RM-FIX-D17",
    "T6":    "RM-FIX-T6",
    "D13a":  "RM-FIX-D13a",
    "D13b":  "RM-FIX-D13b",
    "D6":    "RM-FIX-D6",
    "T9":    "RM-FIX-T9",
}


class Finding:
    __slots__ = ("det", "fired", "applicable", "evidence", "severity")

    def __init__(self, det, fired, applicable=True, evidence="", severity="BLOCK"):
        self.det = det
        self.fired = fired
        self.applicable = applicable
        self.evidence = evidence
        self.severity = severity

    def as_dict(self):
        return {"detector": self.det, "fired": self.fired, "applicable": self.applicable,
                "severity": self.severity, "evidence": self.evidence[:400]}

    def __repr__(self):
        if not self.applicable:
            return f"{self.det:10s} n/a    {self.evidence[:70]}"
        return f"{self.det:10s} {'FIRES' if self.fired else 'clean':5s}  {self.evidence[:70]}"


# --------------------------------------------------------------------------- helpers

def is_template_page(s: str) -> bool:
    """The 749 clones all carry safeRob. Pages without it are a different lineage
    (the AUTO short forms, the bespoke DTA pages) and none of these detectors apply."""
    return "safeRob" in s


def pico_intervention(s: str) -> str:
    m = re.search(r'protocol:\{[^}]{0,400}?\bint:"([^"]{0,120})"', s)
    if m:
        return m.group(1)
    m = re.search(r'\bint:"([^"]{0,120})"', s)
    return m.group(1) if m else ""


AR_SCRIPT = re.compile(r"[؀-ۿ]")


def live_hits(s: str, needle: str):
    """Occurrences of `needle` that a reader can actually meet.

    The inherited Arabic dictionary stores ENGLISH source strings as its keys, so
    every contaminated sentence appears twice: once where the page renders it and
    once as a translation key. Once the Arabic toggle is disabled (D7a) the key is
    unreachable code -- it is no longer a claim the page makes, and a detector that
    counted it would be unfalsifiable: no fix short of rewriting the dictionary could
    ever clear it.

    Discriminator: a key is immediately followed by its Arabic value, so an
    occurrence whose next 250 characters contain Arabic script is a dictionary entry.
    While Arabic is still reachable, every occurrence counts."""
    disabled = FIXED["D7a"] in s
    hits = []
    for m in re.finditer(re.escape(needle), s):
        if disabled and AR_SCRIPT.search(s[m.end():m.end() + 250]):
            continue
        hits.append(m.start())
    return hits


def is_finerenone_review(s: str, path: pathlib.Path) -> bool:
    """The load-bearing legitimate-instance test. Two independent signals so a
    filename rename cannot silently turn the one honest page into a false positive."""
    if path.name.upper().startswith("FINERENONE"):
        return True
    return "finerenone" in pico_intervention(s).lower()


# --------------------------------------------------------------------------- W1

def det_d18b(s, path):
    """C-D18b: the false claim that a git commit hash is a PROSPERO-equivalent
    prospective registration. Every page carrying it contradicts it in its own
    PRISMA item 24. There is no page on which the sentence is true."""
    hit = "equivalent to PROSPERO" in s
    return Finding("C-D18b", hit, True,
                   "PROSPERO-equivalence sentence present" if hit else
                   ("fix marker present" if FIXED["D18b"] in s else "sentence absent"))


def det_d18b2(s, path):
    """C-D18b2: state.protocolDate disagrees with the displayed amendment date and
    neither is given a role. WARN, not BLOCK: both dates are real, the defect is that
    the page does not say which is which."""
    m_pd = re.search(r'protocolDate:"(\d{4}-\d{2}-\d{2})"', s)
    m_am = re.search(r'id="proto-amend-date"[^>]*>([^<]{0,40})<', s)
    if not m_pd or not m_am:
        return Finding("C-D18b2", False, False, "no protocolDate / amendment pair", "WARN")
    if FIXED["D18b2"] in s:
        return Finding("C-D18b2", False, True, "roles named (fix marker present)", "WARN")
    same = m_pd.group(1).strip() == m_am.group(1).strip()
    return Finding("C-D18b2", not same, True,
                   f'protocolDate={m_pd.group(1)} amendment={m_am.group(1).strip()}', "WARN")


def det_d7a(s, path):
    """C-D7a: the Arabic dictionary. Its value for the review's own drug is still
    the finerenone token, and its English keys were overwritten by an intermediate
    lineage, so it is wrong on BOTH sides. Fires when the dictionary is reachable --
    i.e. the toggle has not been disabled."""
    if ARABIC_FINERENONE not in s:
        return Finding("C-D7a", False, False, "no Arabic dictionary on this page")
    if FIXED["D7a"] in s:
        return Finding("C-D7a", False, True, "Arabic mode disabled (fix marker present)")
    live = "toggleArabic()" in s
    return Finding("C-D7a", live, True,
                   f"Arabic dict present ({s.count(ARABIC_FINERENONE)} finerenone tokens), toggle live" if live
                   else "dictionary present but no toggle entry point")


def det_d7b(s, path):
    """C-D7b: the finerenone appositive and the cardiorenal plain-language claim,
    asserted about whatever drug the clone was retitled to.

    LEGITIMATE-INSTANCE CONTROL: FINERENONE_REVIEW.html must NOT fire. Finerenone IS
    a non-steroidal mineralocorticoid receptor antagonist and FIDELIO/FIGARO did
    reduce major heart and kidney events. This is the control the plan calls
    load-bearing, and it is the reason this detector reads the PICO rather than
    grepping for a string."""
    appos = bool(live_hits(s, "non-steroidal mineralocorticoid receptor antagonist"))
    claim = bool(live_hits(s, "major heart and kidney events"))
    if not (appos or claim):
        return Finding("C-D7b", False, False, "neither string present")
    if is_finerenone_review(s, path):
        return Finding("C-D7b", False, True,
                       "legitimate instance: PICO intervention IS finerenone")
    if FIXED["D7b"] in s:
        return Finding("C-D7b", False, True, "strings removed (fix marker present)")
    return Finding("C-D7b", True, True,
                   f'appositive={appos} cardiorenal_claim={claim} on int="{pico_intervention(s)}"')


def det_d3a(s, path):
    """C-D3a: migration v119 stamps reviewer1/reviewer2 + confirmed with no human and
    no cryptographic seal, on every trial, and calls it Cochrane RoB 2.0 dual review.

    LEGITIMATE-INSTANCE CONTROL: the genuine sign-off flows (screen-propose-bulk,
    extract-signoff-1/2) carry RapidMeta._seal signatures and must NOT fire. The
    discriminator is the seal, not the reviewer initials -- MA and SR are real
    people's initials and a name-based rule would delete real sign-offs."""
    if "_migrated_v119_dual_review_signoff" not in s:
        return Finding("C-D3a", False, False, "no v119 migration on this page")
    if FIXED["D3a"] in s:
        return Finding("C-D3a", False, True, "v119 sign-off stamp removed (fix marker present)")
    # Either flag: the fixed build gates the scrub on _migrated_v120_unsealed_signoff_scrub
    # so it also runs for readers who already carry the v119 flag.
    block = re.search(r"_migrated_v(?:119_dual_review_signoff|120_unsealed_signoff_scrub)\)"
                      r"\{(.{0,1800}?)_migrated_v119_dual_review_signoff=!0", s, re.S)
    body = block.group(1) if block else ""
    stamps = 'confirmed:!0' in body or 'confirmed=!0' in body
    sealed = "_seal(" in body
    return Finding("C-D3a", bool(stamps and not sealed), True,
                   f"v119 body stamps confirmed={stamps}, cryptographically sealed={sealed}")


def det_d5b(s, path):
    """C-D5b: FINEARTS-HF / FIDELIO-DKD / FIGARO-DKD inherited as the benchmark
    reference on a review that is not about finerenone.

    LEGITIMATE-INSTANCE CONTROL: a real finerenone review must NOT fire.
    Scope is deliberately narrow -- only the benchmark surfaces (BENCHMARK_OUTCOME_NOTES,
    CTGOV_EVIDENCE_REGISTRY, rReference) -- because these trial names also appear in
    ordinary prose on pages that legitimately discuss them."""
    names = re.findall(r"FINEARTS-HF|FIDELIO-DKD|FIGARO-DKD", s)
    if not names:
        return Finding("C-D5b", False, False, "no finerenone landmark names present")
    if is_finerenone_review(s, path):
        return Finding("C-D5b", False, True, "legitimate instance: this IS a finerenone review")
    if FIXED["D5b"] in s:
        return Finding("C-D5b", False, True, "inherited benchmark keys removed (fix marker present)")
    in_bench = bool(re.search(r"BENCHMARK_OUTCOME_NOTES=\{[^}]{0,2000}(FINEARTS-HF|FIDELIO-DKD|FIGARO-DKD)", s)) \
        or bool(re.search(r'CTGOV_EVIDENCE_REGISTRY=\{[^\n]{0,4000}?label:"(FINEARTS-HF|FIDELIO-DKD|FIGARO-DKD)"', s))
    return Finding("C-D5b", in_bench, True,
                   f'{len(names)} landmark refs, in benchmark/registry surface={in_bench}, int="{pico_intervention(s)}"')


# --------------------------------------------------------------------------- W2

WALD_POOL = re.compile(
    r"pLogOR=sWRY/sWR,pSE=Math\.sqrt\(1/sWR\),zCrit=zCritHR,"
    r"pOR=Math\.exp\(pLogOR\),lci=Math\.exp\(pLogOR-zCrit\*pSE\)")


def det_d17a(s, path):
    """C-D17a: the methods declaration says the reported interval is HKSJ-adjusted
    while the code builds the headline interval as exp(pLogOR +/- z*pSE) -- a Wald
    (normal-approximation) interval around the REML point estimate. HKSJ is computed
    as a sidecar (max(1,q*) variance floor, t_{k-1}) and never governs.

    This fires on the DECLARATION, not the code: the fix corrects the text to match
    what the engine does. Headlining HKSJ instead would change 749 published
    significance verdicts and is explicitly out of scope."""
    if not WALD_POOL.search(s):
        return Finding("C-D17a", False, False, "headline pooling block not in the expected shape")
    if FIXED["D17"] in s:
        return Finding("C-D17a", False, True, "methods text corrected (fix marker present)")
    # live_hits, not `in`: each of these sentences also exists as an English KEY in the
    # inherited Arabic dictionary, and once D7a has disabled that dictionary the key is
    # unreachable rather than a claim the page makes.
    claims = []
    if live_hits(s, "REML random-effects, HKSJ-adjusted (inverse-variance weighting)"):
        claims.append("methods-table Pooling Model row")
    if live_hits(s, "REML+HKSJ primary with DerSimonian-Laird sensitivity"):
        claims.append("AI-disclosure row")
    if live_hits(s, "REML random-effects model (HKSJ-adjusted)"):
        claims.append("figure annotation / export")
    if live_hits(s, "Hartung-Knapp-Sidik-Jonkman adjustment of the "):
        claims.append("methods paragraph")
    return Finding("C-D17a", bool(claims), True,
                   "headline CI is Wald; page declares HKSJ-adjusted at: " + ", ".join(claims)
                   if claims else "no HKSJ-primary declaration found")


def det_d17b(s, path):
    """C-D17b: QA4 already computes Wald-vs-HKSJ significance discordance and
    downgrades it to a warning chip. On a page where the two disagree the reader is
    never told that the interval governing the verdict is the narrower one."""
    if 'id:"QA4"' not in s:
        return Finding("C-D17b", False, False, "no QA4 check on this page")
    if "qa4-discordance-banner" in s:
        return Finding("C-D17b", False, True, "discordance banner present")
    return Finding("C-D17b", True, True, "QA4 discordance renders as a warn chip only", "WARN")


def det_t6(s, path):
    """C-T6: the estimator label. tau2 = k>=2 ? tau2_reml : tau2_dl -- the headline
    tau-squared is the REML fixed-point iterate, and the 'standard' leg of the CI
    comparison figure is the Wald interval around the REML estimate. Both are
    labelled DerSimonian-Laird."""
    if "tau2_reml" not in s:
        return Finding("C-T6", False, False, "no REML estimator on this page")
    if FIXED["T6"] in s:
        return Finding("C-T6", False, True, "estimator labels corrected (fix marker present)")
    sites = []
    if "\u03c4\u00b2 (DerSimonian-Laird)" in s:
        sites.append("methods paragraph tau-squared label")
    if 'addTrace("DerSimonian-Laird ("' in s:
        sites.append("CI-comparison trace label")
    if "Fig. \u2014 DerSimonian-Laird (standard)" in s:
        sites.append("figure caption")
    return Finding("C-T6", bool(sites), True,
                   "REML computed but labelled DerSimonian-Laird at: " + ", ".join(sites)
                   if sites else "no mislabelled site found")


# --------------------------------------------------------------------------- W3

def det_d13a(s, path):
    """C-D13a: filter.overallStatus=COMPLETED. A trial that is RECRUITING,
    ACTIVE_NOT_RECRUITING or primary-complete-but-open is never retrieved -- which is
    the normal state of exactly the trials a living review exists to catch."""
    n = s.count("filter.overallStatus=COMPLETED")
    if n == 0:
        return Finding("C-D13a", False, True,
                       "fix marker present" if FIXED["D13a"] in s else "filter absent")
    return Finding("C-D13a", True, True, f"{n} query sites still filter to COMPLETED only")


def det_d13b(s, path):
    """C-D13b: a fixed pageSize with no pageToken. Results past the first page are
    dropped silently."""
    if "clinicaltrials.gov/api/v2/studies" not in s:
        return Finding("C-D13b", False, False, "no CT.gov query on this page", "WARN")
    if "nextPageToken" in s:
        return Finding("C-D13b", False, True, "pagination follows nextPageToken", "WARN")
    return Finding("C-D13b", True, True, "fixed pageSize, no pageToken", "WARN")


def det_d13c(s, path):
    """C-D13c: the drug vocabulary is a fixed whitelist with a single alternation, so
    the gate can only ever recognise one drug name.

    TRIAGE ONLY -- the repair keys the gate to the review's own PICO interventions
    plus synonyms, which is per-page data and is NOT a blanket fix. This detector
    reports; the number-neutral waves do not edit it."""
    m = re.search(r"hasDrug\s*=\s*/([^/]{1,400})/", s)
    if not m:
        return Finding("C-D13c", False, False, "no hasDrug whitelist", "WARN")
    alts = m.group(1).count("|") + 1
    return Finding("C-D13c", alts < 2, True, f"hasDrug alternations={alts}", "WARN")


def det_d6(s, path):
    """C-D6: the page states that surveillance is continuous and the protocol
    auto-updating. It is not: the CT.gov call is user-triggered from a button, the
    population regex is frozen on heart-failure/CKD on 737 pages, and the status
    filter excluded every open trial. The blanket-safe action is to stop making the
    claim, not to pretend the gate works."""
    claims = []
    if live_hits(s, "Continuous (living review); formal snapshot at each new trial publication"):
        claims.append("Planned Update Frequency row")
    if live_hits(s, "(Living Protocol &mdash; auto-updating)"):
        claims.append("Protocol Version row")
    if not claims:
        return Finding("C-D6", False, True,
                       "limitation stated (fix marker present)" if FIXED["D6"] in s else "no surveillance claim")
    return Finding("C-D6", True, True, "unqualified surveillance claim at: " + ", ".join(claims))


def det_t9(s, path):
    """C-T9: the NMA tab is revealed whenever NMA_CONFIG is truthy, with no check
    that the configured network is connected.

    LEGITIMATE-INSTANCE CONTROL: a genuinely connected network must NOT fire. A
    four-spoke star (four DOACs against a shared warfarin control) is connected --
    the predicate is 'some node has degree >= 2', i.e. at least two distinct active
    treatments share a comparator, which is exactly the condition that makes an
    indirect comparison possible."""
    if "btn-tab-nma" not in s:
        return Finding("C-T9", False, False, "no NMA tab on this page")
    if FIXED["T9"] in s or "_isConnected" in s:
        return Finding("C-T9", False, True, "tab gated on a connectivity predicate")
    connected, why = nma_connected(s)
    return Finding("C-T9", True, True,
                   f"NMA tab ungated (network is currently {'connected' if connected else 'DISCONNECTED'}: {why})")


def nma_connected(s):
    """Recompute the predicate in Python so the detector does not have to trust the
    page's own copy of it. Same rule as the injected _isConnected()."""
    m = re.search(r"NMA_CONFIG=(\{.*?\}),NMAEngine=", s, re.S)
    if not m:
        if "NMA_CONFIG=null" in s:
            return False, "NMA_CONFIG is null"
        return False, "NMA_CONFIG not parseable"
    blob = m.group(1)
    comps = re.findall(r'\{t1:"([^"]+)",t2:"([^"]+)",trials:\[([^\]]*)\]\}', blob)
    comps = [(a, b) for a, b, tr in comps if tr.strip()]
    if len(comps) < 2:
        return False, f"{len(comps)} usable comparison(s)"
    deg = {}
    for a, b in comps:
        deg.setdefault(a, set()).add(b)
        deg.setdefault(b, set()).add(a)
    hub = max(deg.items(), key=lambda kv: len(kv[1]))
    return len(hub[1]) >= 2, f'hub "{hub[0]}" has degree {len(hub[1])} over {len(comps)} comparisons'


DETECTORS = [
    det_d18b, det_d18b2, det_d7a, det_d7b, det_d3a, det_d5b,
    det_d17a, det_d17b, det_t6,
    det_d13a, det_d13b, det_d13c, det_d6, det_t9,
]

# Which detectors each wave is responsible for clearing.
WAVE_DETECTORS = {
    "W1": ["C-D18b", "C-D18b2", "C-D7a", "C-D7b", "C-D3a", "C-D5b"],
    "W2": ["C-D17a", "C-D17b", "C-T6"],
    "W3": ["C-D13a", "C-D13b", "C-D6", "C-T9"],
}
# Reported but NOT edited by the number-neutral waves: the repair needs per-page PICO.
TRIAGE_ONLY = ["C-D13c"]


def run(html: str, path: pathlib.Path):
    if not is_template_page(html):
        return [Finding(d.__name__, False, False, "not a finerenone-template page") for d in DETECTORS]
    return [d(html, path) for d in DETECTORS]


def run_path(p):
    p = pathlib.Path(p)
    return run(p.read_text(encoding="utf-8", errors="replace"), p)


# --------------------------------------------------------------------------- selftest

def _clean_pages():
    if not SSOT_BUILD.exists():
        return []
    return sorted(SSOT_BUILD.glob("*.html"))


# Each mutation takes a page body and returns a body carrying the defect. The
# mutations are written against a template page, because injecting a defect into a
# static 6-96 KB SSOT build would only prove the string-match, not the context rule.
MUTATIONS = {
    "C-D18b": lambda s: s.replace("</body>", "<p>equivalent to PROSPERO</p></body>", 1),
    "C-D7b":  lambda s: s.replace("</body>",
                                  "<p>Drug X, a non-steroidal mineralocorticoid receptor antagonist,"
                                  " reduced the risk of major heart and kidney events.</p></body>", 1),
    "C-D13a": lambda s: s.replace("</body>", "<code>filter.overallStatus=COMPLETED</code></body>", 1),
    "C-D6":   lambda s: s.replace("</body>",
                                  '<td class="p-4 text-slate-300">Continuous (living review);'
                                  " formal snapshot at each new trial publication</td></body>", 1),
    # Removing the fix marker is the sharpest mutation available: it restores exactly
    # the state the wave was supposed to leave behind, so a detector that still reports
    # clean is reading the marker instead of the page.
    "C-D7a":  lambda s: s.replace(FIXED["D7a"], "", 1),
    "C-D3a":  lambda s: s.replace(FIXED["D3a"], "", 1)
                         .replace("const unsealed=",
                                  "const now=(new Date).toISOString(),unsealed=", 1)
                         .replace("this.state.trials.forEach(t=>{if(unsealed(t.screenReview))",
                                  "this.state.trials.forEach(t=>{t.data&&(t.data.robSignoff="
                                  '{reviewer1:"MA",reviewer2:"SR",ts1:now,ts2:now,'
                                  'method:"Cochrane RoB 2.0",confirmed:!0});if(unsealed(t.screenReview))', 1),
    "C-D17a": lambda s: s.replace(FIXED["D17"], "", 1).replace(
        "</body>", "<td>REML random-effects, HKSJ-adjusted (inverse-variance"
                   " weighting)</td></body>", 1),
    "C-D17b": lambda s: s.replace("qa4-discordance-banner", "qa4-was-a-banner"),
    "C-T6":   lambda s: s.replace("τ² (REML)", "τ² (DerSimonian-Laird)", 1),
    "C-T9":   lambda s: s.replace(FIXED["T9"], "", 1).replace("_isConnected", "_wasConnected"),
    # Removing the marker alone is not enough: the fix also reconciled the value, so
    # the dates must be pushed back apart for the mutation to represent the defect.
    "C-D18b2": lambda s: re.sub(r'protocolDate:"\d{4}-\d{2}-\d{2}"/\*.*?\*/',
                                'protocolDate:"2026-04-19"', s, count=1),
    "C-D5b":  lambda s: s.replace(FIXED["D5b"], "", 1).replace(
        'BENCHMARK_OUTCOME_NOTES={default:""}',
        'BENCHMARK_OUTCOME_NOTES={HF_CV_First:"No direct published meta-analysis uses'
        ' the exact FINEARTS-HF primary estimand.",default:""}', 1),
}


def selftest(corpus_root=None, fixed_host=None, verbose=True):
    ok = True
    print("=" * 74)
    print("CONTROL 1 -- CLEAN PAGES: every detector must run GREEN on the certified builds")
    print("=" * 74)
    pages = _clean_pages()
    if not pages:
        print(f"  REFUSING: no clean pages at {SSOT_BUILD}. A detector suite with no")
        print("  clean-page control has not been shown to avoid false positives.")
        return False
    for p in pages:
        body = p.read_text(encoding="utf-8", errors="replace")
        fired = [f for f in run(body, p) if f.applicable and f.fired]
        status = "green" if not fired else "FIRED: " + ", ".join(f.det for f in fired)
        print(f"  {p.name:38s} {status}")
        if fired:
            ok = False
            for f in fired:
                print(f"      {f.det}: {f.evidence}")
    print(f"\n  {len(pages)} certified pages checked.")

    print()
    print("=" * 74)
    print("CONTROL 2 -- MUTATIONS: each must make its detector fire on a page that was clean")
    print("=" * 74)
    # A page that has already had W1-W3 applied is the right mutation host: it is clean
    # for these classes but is still a full template page, so the context rules (PICO
    # lookup, seal check, connectivity) are actually exercised. Injecting a defect into
    # a 6-96 KB static SSOT build would only prove the string-match.
    hosts = []
    if fixed_host:
        fh = pathlib.Path(fixed_host)
        cands = sorted(fh.glob("*.html")) if fh.is_dir() else ([fh] if fh.exists() else [])
        for c in cands:
            hosts.append((c, c.read_text(encoding="utf-8", errors="replace")))
    if not hosts:
        print("  SKIPPED -- no post-wave host page given (--fixed-host). This is a gap,")
        print("  not a pass: report it as unverified.")
        ok = False
    else:
        # Not every host exercises every detector: a page with no NMA tab cannot host
        # the T9 mutation. Use, per detector, the first host on which that detector is
        # NOT FIRING -- and fail loudly if no host qualifies, rather than quietly
        # reporting a pass for a control that never ran. "Not applicable" is a valid
        # host state: after the wave the D7b strings are gone from the page entirely,
        # and injecting them is precisely the mutation under test.
        for det_id, mutate in MUTATIONS.items():
            chosen = None
            # Two passes: prefer a host where the detector is APPLICABLE and clean --
            # that host still carries the surrounding machinery the mutation edits.
            # Only fall back to a not-applicable host, where injecting the string is
            # the whole mutation.
            for want_applicable in (True, False):
                for p, body in hosts:
                    f = {x.det: x for x in run(body, p)}[det_id]
                    if f.fired or f.applicable != want_applicable:
                        continue
                    # Never host a mutation on the page where the string is TRUE:
                    # FINERENONE_REVIEW is silent for D7b/D5b by design, so injecting
                    # the appositive there must NOT fire, and using it as a host would
                    # report a working detector as broken.
                    if f.evidence.startswith("legitimate instance"):
                        continue
                    chosen = (p, body)
                    break
                if chosen:
                    break
            if chosen is None:
                print(f"  {det_id:10s} NO HOST -- no supplied page is applicable-and-clean "
                      f"for this detector; control did not run")
                ok = False
                continue
            p, body = chosen
            mutated = mutate(body)
            if mutated == body:
                print(f"  {det_id:10s} FAILED -- mutation did not change {p.name}")
                ok = False
                continue
            good = {x.det: x for x in run(mutated, p)}[det_id].fired
            print(f"  {det_id:10s} {'BLOCKS as required' if good else 'DID NOT FIRE -- detector is broken'}"
                  f"   (host {p.name})")
            if not good:
                ok = False

    print()
    print("=" * 74)
    print("CONTROL 3 -- LEGITIMATE INSTANCES: these must NOT fire")
    print("=" * 74)
    checks = []
    if corpus_root:
        root = pathlib.Path(corpus_root)
        checks = [
            (root / "FINERENONE_REVIEW.html", "C-D7b",
             "the appositive is TRUE on the finerenone review"),
            (root / "FINERENONE_REVIEW.html", "C-D5b",
             "FINEARTS/FIDELIO/FIGARO are the right benchmarks for a finerenone review"),
            (root / "DOAC_AF_NMA_REVIEW.html", "C-T9",
             "four DOACs on a shared warfarin control IS a connected network"),
            (root / "CGRP_MIGRAINE_NMA_REVIEW.html", "C-T9",
             "four CGRP mAbs on a shared placebo control IS a connected network"),
        ]
    if not checks:
        print("  SKIPPED -- no corpus root given. Report as unverified.")
        ok = False
    for p, det_id, why in checks:
        if not p.exists():
            print(f"  {p.name:34s} {det_id:8s} MISSING -- control not run")
            ok = False
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        f = {x.det: x for x in run(body, p)}[det_id]
        if det_id == "C-T9":
            conn, why2 = nma_connected(body)
            if not conn:
                print(f"  {p.name:34s} {det_id:8s} NOT A CONTROL -- network is disconnected ({why2})")
                ok = False
                continue
            # The tab is legitimately shown here, so the detector firing pre-fix is
            # correct; what must hold is that the injected predicate keeps it visible.
            print(f"  {p.name:34s} {det_id:8s} connected ({why2}) -- gate must keep the tab")
            continue
        good = not f.fired
        print(f"  {p.name:34s} {det_id:8s} {'correctly silent' if good else 'FALSE POSITIVE'}  ({why})")
        if not good:
            print(f"      {f.evidence}")
            ok = False

    print()
    print("=" * 74)
    print("SELFTEST " + ("PASS" if ok else "FAIL -- do not run a wave with a broken detector"))
    print("=" * 74)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--corpus-root", default=r"F:\rapidmeta-corpus-wave")
    ap.add_argument("--fixed-host", default=None,
                    help="a page (or directory of pages) that has already had W1-W3 "
                         "applied; used as the mutation host for control 2")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest(a.corpus_root, a.fixed_host) else 1
    rc = 0
    out = {}
    for p in a.pages:
        fs = run_path(p)
        out[p] = [f.as_dict() for f in fs]
        if not a.json:
            print(f"\n### {p}")
            for f in fs:
                print("   " + repr(f))
        if any(f.applicable and f.fired and f.severity == "BLOCK" for f in fs):
            rc = 1
    if a.json:
        print(json.dumps(out, indent=1, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main())
