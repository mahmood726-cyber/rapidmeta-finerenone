#!/usr/bin/env python
"""Detect presentation-layer drift in a built RapidMeta dashboard.

A recurring generator-class defect: a data-layer correction lands (pooled
estimate, estimand, trial set) but the *presentation* layer keeps the
superseded state -- verdict JSON, badge text, badge COLOUR, banners, config
flags, meta description, include-gates and generated manuscript prose.

The pooled numbers are right; what the page *says about them* is wrong.
That is invisible to numeric validation, so it needs its own gate.

Usage:
    python scripts/presentation_layer_sweep.py APP.html [APP2.html ...]
    python scripts/presentation_layer_sweep.py --json APP.html

Exit codes:
    0  no findings
    1  one or more findings (so it can gate a build)
    2  usage / unreadable input

Every check reports the evidence string it matched, so a finding can be
confirmed by grep without rerunning this tool.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Verdicts that mean "not clean". A badge painted success-green over one of
# these is a false-green: the colour contradicts the machine-readable state.
NON_CLEAN_VERDICTS = {"UNVERIFIED", "UNCERTAIN", "FAIL", "BLOCKED", "REJECT"}

# Success-greens observed across the corpus (tailwind emerald/green ramps).
SUCCESS_GREENS = {
    "#15803d", "#16a34a", "#22c55e", "#166534", "#14532d",
    "#059669", "#10b981", "#047857", "#065f46",
}

# Ratio measures. If the primary estimand is a continuous mean difference,
# none of these may appear as the active effectMeasure.
RATIO_MEASURES = {"RR", "OR", "HR"}

# Deciding "is this review's primary estimand continuous?" by keyword presence
# is unreliable: every dashboard carries generic methods boilerplate that
# mentions a mean difference once or twice. Density separates them cleanly --
# a genuinely MD-primary review mentions it ~27 times; a legitimate HR/RR
# review mentions it 1-2 times. Below this threshold we do not claim to know.
MD_DENSITY_THRESHOLD = 10
MD_PHRASE_RE = re.compile(r"mean[- ]difference", re.I)

# NOTE: there is deliberately no built-in list of "retired" provenance strings.
# Whether "verified against ClinicalTrials.gov" is a stale claim or a true one
# depends on the app -- in one file it is retired boilerplate, in another it is
# an accurate statement about 6/6 trials. The tool cannot know which without
# being told, and guessing produces false positives on clean apps. Per-app
# retired strings come from --retired. Every default check below is instead a
# *contradiction* between two surfaces of the same file, which is self-evidencing.

# Prose asserting dual human screening, paired with the audit counter that
# records how much dual screening actually happened.
# Must be an ASSERTION that dual screening happened, not merely a UI heading.
# "Two-Reviewer Screening Sign-off" is a panel title (an affordance); the defect
# is prose claiming the work was *conducted*. Requiring an assertive verb keeps
# the check on the manuscript sentence that would travel into a submission.
DUAL_CLAIM_RE = re.compile(
    r"(?:conducted|performed|completed|undertook|carried out)"
    r"[^.<]{0,90}?"
    r"(?:two-reviewer screening|dual[- ]reviewer screening|"
    r"independent duplicate screening|dual human screening)",
    re.I,
)
DUAL_RECORD_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s+dual human (?:screening|extraction)", re.I)

# A live include-gate keyed on year, e.g. !(year&&year<2019)
DATE_GATE_RE = re.compile(r"year\s*[<>]=?\s*(19|20)\d{2}")
# Text asserting date is NOT an eligibility axis.
NO_DATE_POLICY_RE = re.compile(
    r"(?:publication|enrol(?:l)?ment)[^.<]{0,60}date[^.<]{0,80}"
    r"(?:not an eligibility criterion|is not a criterion|no longer)",
    re.I,
)

NOT_POOLED_RE = re.compile(r"Not a pooled meta-analysis", re.I)

WORD_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
# Two shapes assert a TOTAL trial count:
#   (a) an explicit noun phrase -- "five included trials"
#   (b) a totalising qualifier   -- "all five trials", "only five studies"
# Bare "three studies reported X" is legitimate SUBSET language and must not
# be flagged, which is why plain "<number> trials" is not matched on its own.
WORD_TRIALS_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:included trials|included studies|primary publications|"
    r"randomised trials|randomized trials)"
    r"|\b(?:all|only|with|across the)\s+"
    r"(one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:trials|studies)\b",
    re.I,
)


def _clip(s: str, n: int = 110) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _find_verdict(text: str) -> dict | None:
    """Extract the window.__verdict object if present."""
    m = re.search(r"window\.__verdict\s*=\s*(\{.*?\});", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _status_badge_backgrounds(text: str) -> list[tuple[str, str]]:
    """Return (colour, evidence) for every role="status" element with a bg colour."""
    out = []
    for m in re.finditer(r'role="status"[^>]{0,400}', text):
        frag = m.group(0)
        for c in re.finditer(r"background:\s*(#[0-9a-fA-F]{6})", frag):
            out.append((c.group(1).lower(), _clip(frag, 150)))
    return out


def check_badge_colour(text: str, verdict: dict | None) -> list[dict]:
    if not verdict:
        return []
    v = str(verdict.get("verdict", "")).upper()
    if v not in NON_CLEAN_VERDICTS:
        return []
    findings = []
    for colour, evidence in _status_badge_backgrounds(text):
        if colour in SUCCESS_GREENS:
            findings.append({
                "check": "badge-colour-vs-verdict",
                "severity": "high",
                "detail": (
                    f'status badge painted success-green {colour} while '
                    f'window.__verdict reports "{v}"'
                ),
                "evidence": evidence,
            })
    return findings


def _is_md_primary(text: str) -> bool:
    """True only when the app is densely built around a mean difference."""
    return len(MD_PHRASE_RE.findall(text)) >= MD_DENSITY_THRESHOLD


# Assertive "we passed" wording. A badge may legitimately *name* a non-clean
# verdict ("UNVERIFIED - AUTOMATED OUTPUT"); what it may not do is assert that
# checks passed while the verdict object says otherwise. Colour and text are
# two halves of the same false-green -- fixing one and not the other still
# leaves the reader with a passing impression.
BADGE_PASS_RE = re.compile(
    r"(?:INTERNAL )?CHECKS PASSED|ALL CHECKS PASSED|VALIDATION PASSED|"
    r"SUBMISSION[- ]READY|FULLY VERIFIED|AUDIT PASSED",
    re.I,
)


NEGATION_RE = re.compile(r"\b(?:not|non|never|no)\b[\s\-—]*$", re.I)

# Phrases that scope a count to a subset rather than the whole review.
SCOPE_QUALIFIER_RE = re.compile(
    r"\s*(?:in|for|with|reporting|contributing|that report)\b[^.<]{0,40}?"
    r"(?:pooled|estimand|this outcome|this analysis|this stratum|subgroup|"
    r"sensitivity|data)",
    re.I,
)


def check_badge_text(text: str, verdict: dict | None) -> list[dict]:
    """Badge text asserting a pass while the verdict object is not clean."""
    if not verdict:
        return []
    v = str(verdict.get("verdict", "")).upper()
    if v not in NON_CLEAN_VERDICTS:
        return []
    findings = []
    for m in re.finditer(r'role="status"[^>]{0,400}(?:>.{0,600})?', text, re.S):
        frag = m.group(0)
        hit = BADGE_PASS_RE.search(frag)
        # "NOT SUBMISSION-READY" contains "SUBMISSION-READY". A badge that
        # negates the phrase is honest, and flagging it would train people to
        # ignore this check. Inspect the run-up before believing the match.
        if hit and NEGATION_RE.search(frag[max(0, hit.start() - 14): hit.start()]):
            hit = None
        if hit:
            findings.append({
                "check": "badge-text-vs-verdict",
                "severity": "high",
                "detail": (
                    f'status badge asserts "{hit.group(0)}" while '
                    f'window.__verdict reports "{v}"'
                ),
                "evidence": _clip(frag[max(0, hit.start() - 60): hit.end() + 90], 160),
            })
            break
    return findings


def check_effect_measure(text: str) -> list[dict]:
    findings = []
    pot = re.search(r'primaryOutcomeType\s*:\s*"([a-z]+)"', text)
    continuous = _is_md_primary(text)
    # Scan every occurrence: the first hit is often a sanitiser default
    # (effectMeasure:"AUTO"), which would mask the real config below it.
    if continuous:
        seen = set()
        for em in re.finditer(r'effectMeasure\s*:\s*"([A-Z]+)"', text):
            measure = em.group(1)
            if measure in RATIO_MEASURES and measure not in seen:
                seen.add(measure)
                findings.append({
                    "check": "effect-measure-vs-estimand",
                    "severity": "high",
                    "detail": (
                        f'active effectMeasure "{measure}" is a ratio measure, but '
                        f"the app carries continuous mean-difference markers"
                    ),
                    "evidence": _clip(em.group(0)),
                })
    if pot and continuous and pot.group(1) == "binary":
        findings.append({
            "check": "outcome-type-vs-estimand",
            "severity": "high",
            "detail": 'primaryOutcomeType "binary" on an app with continuous MD markers',
            "evidence": _clip(pot.group(0)),
        })
    return findings


def check_retired_provenance(text: str, retired: list[str]) -> list[dict]:
    """Caller-supplied strings that must be absent from this specific app."""
    findings = []
    for s in retired:
        if s.lower() in text.lower():
            findings.append({
                "check": "retired-provenance-string",
                "severity": "medium",
                "detail": f"caller-supplied retired string still present: {s!r}",
                "evidence": s,
            })
    return findings


def check_dual_screening(text: str) -> list[dict]:
    """Prose claiming dual screening while the audit records little or none."""
    claim = DUAL_CLAIM_RE.search(text)
    if not claim:
        return []
    findings = []
    for m in DUAL_RECORD_RE.finditer(text):
        done, total = int(m.group(1)), int(m.group(2))
        if done < total:
            findings.append({
                "check": "dual-screening-claim-vs-record",
                "severity": "critical",
                "detail": (
                    f"prose asserts dual/two-reviewer screening but the audit "
                    f"records {done}/{total} -- this travels into manuscript text"
                ),
                "evidence": _clip(
                    text[max(0, claim.start() - 40): claim.end() + 80]
                ) + " || " + _clip(m.group(0)),
            })
            break
    return findings


def check_date_gate(text: str) -> list[dict]:
    policy = NO_DATE_POLICY_RE.search(text)
    if not policy:
        return []
    findings = []
    for m in DATE_GATE_RE.finditer(text):
        ctx = text[max(0, m.start() - 90): m.end() + 60]
        # A mention inside an explanatory comment is not a live gate.
        if "/*" in ctx and "*/" in ctx[ctx.find("/*"):]:
            continue
        findings.append({
            "check": "date-gate-vs-stated-policy",
            "severity": "high",
            "detail": (
                "page states publication/enrolment date is not an eligibility "
                "criterion, but a live year gate remains in include logic"
            ),
            "evidence": _clip(ctx, 150),
        })
        break
    return findings


# --- the generator rule: NOT IMPLEMENTED, deliberately -----------------------
# The dominant corpus defect is inference COMPUTED on the prespecified model but
# DISPLAYED from a laxer one (cancer-VTE showed patient-facing benefit + an NNT
# off the uncorrected DL interval 0.39-0.86 while the prespecified HKSJ interval
# 0.286-1.180 crossed the null).
#
# Four lexical detectors for this were built and all four were rejected here:
#   1. flag a bare .uci/.lci significance decision  -> 32 false positives on 8
#      known-good apps; the helper legitimately branches on both intervals.
#   2. same, but skip windows containing "hksj"     -> missed the real defect,
#      because the helper DOES contain an hkOK branch.
#   3. broaden the token to hk(sj|OK|Lo|Hi)         -> then nothing flags at all.
#   4. move the check to the CALL SITE arguments    -> correct in principle and
#      verified by hand on the real call
#      (updatePatientMode(c.pOR,c.lci,c.uci,...)), but it would not fire
#      reproducibly from the module and the cause was not identified.
#
# The reason is structural, not a bug to grind out: WHICH interval reaches a
# display surface is a DATA-FLOW property. The helper can branch on HKSJ and
# still be handed DL by its caller -- which is exactly what cancer-VTE did. A
# regex over source text cannot see that without following the values.
#
# What would actually work, in rough order of cost:
#   - a naming convention the generator enforces (display functions accept a
#     single `prespecified` interval object, never loose lci/uci), which then IS
#     greppable;
#   - a runtime assertion in the generator: display helpers refuse to render a
#     significance/benefit claim unless handed the prespecified bound;
#   - an AST/data-flow pass over the emitted JS rather than a text scan.
#
# Shipping an unvalidated critical-severity check would be worse than shipping
# none: it would train reviewers to ignore this class. Left to a cross-family
# gate, which HAS caught it reliably (Codex found it on cancer-VTE by reading
# the call site and reproducing the pool).

def check_not_pooled_banner(text: str, verdict: dict | None) -> list[dict]:
    m = NOT_POOLED_RE.search(text)
    if not m:
        return []
    if not verdict:
        return []
    # "Not pooled" is HONEST when the app genuinely pooled nothing. The right
    # comparator is n_trials_pooled, NOT n_trials_seen: an app can legitimately
    # SEE 4 trials, find their estimands incommensurable, and pool 0. Comparing
    # against n_trials_seen manufactures a contradiction out of a correct
    # disclosure -- caught by a cross-family adversary on APIXABAN_AF, which
    # carries "n_trials_seen": 4 with "n_trials_pooled": 0.
    # Match the FAMILY, not an enumerated list: verdicts appear as
    # NOT_POOLABLE, BLOCKED_NOT_POOLABLE and similar. An exact-match list
    # silently false-positives on every variant it forgot.
    v = str(verdict.get("verdict", "")).upper().replace("-", "_")
    if "NOT_POOLABLE" in v:
        return []
    counts = verdict.get("counts") or {}
    pooled = counts.get("n_trials_pooled")
    if pooled is not None:
        k = pooled
    else:
        k = counts.get("n_trials_seen")
    if k is not None and k >= 2:
        return [{
            "check": "not-pooled-banner-vs-pooled-data",
            "severity": "high",
            "detail": (
                f'banner says "Not a pooled meta-analysis" while the verdict '
                f"reports n_trials_seen={k}"
            ),
            "evidence": _clip(text[max(0, m.start() - 40): m.end() + 140]),
        }]
    return []


def check_trial_count_words(text: str, verdict: dict | None) -> list[dict]:
    """Spelled-out trial counts that disagree with n_trials_seen."""
    if not verdict:
        return []
    k = (verdict.get("counts") or {}).get("n_trials_seen")
    if not isinstance(k, int) or k < 1:
        return []
    findings = []
    seen_words = set()
    for m in WORD_TRIALS_RE.finditer(text):
        # "only two studies IN THE POOLED ESTIMAND" is a scoped subset, not a
        # total: a 4-trial review can have 2 trials contributing to one pooled
        # outcome. A trailing scope qualifier disqualifies the match.
        if SCOPE_QUALIFIER_RE.match(text[m.end(): m.end() + 40]):
            continue
        # group 1 = explicit noun phrase, group 2 = totalising qualifier
        word = (m.group(1) or m.group(2)).lower()
        if WORD_NUM.get(word) != k and word not in seen_words:
            seen_words.add(word)
            findings.append({
                "check": "spelled-trial-count-vs-verdict",
                "severity": "medium",
                "detail": (
                    f'text says "{m.group(0)}" but verdict reports n_trials_seen={k}'
                ),
                "evidence": _clip(text[max(0, m.start() - 70): m.end() + 70]),
            })
    return findings


def sweep(path: Path, retired: list[str]) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    verdict = _find_verdict(text)
    findings: list[dict] = []
    findings += check_badge_colour(text, verdict)
    findings += check_badge_text(text, verdict)
    findings += check_effect_measure(text)
    findings += check_retired_provenance(text, retired)
    findings += check_dual_screening(text)
    findings += check_date_gate(text)
    findings += check_not_pooled_banner(text, verdict)
    findings += check_trial_count_words(text, verdict)
    for f in findings:
        f["file"] = path.name
    return findings


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def main(argv: list[str] | None = None) -> int:
    # Dashboards carry non-cp1252 glyphs (warning signs, primes, dashes).
    # Without this, printing evidence raises UnicodeEncodeError on a stock
    # Windows console and the gate dies mid-report instead of reporting.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("apps", nargs="+", help="built dashboard HTML file(s)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--retired", action="append", default=[],
                    help="extra string that must be absent (repeatable)")
    args = ap.parse_args(argv)

    all_findings: list[dict] = []
    for raw in args.apps:
        p = Path(raw)
        if not p.is_file():
            print(f"ERROR: not a file: {p}", file=sys.stderr)
            return 2
        all_findings += sweep(p, args.retired)

    all_findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), f["file"]))

    if args.json:
        print(json.dumps(all_findings, indent=2))
    else:
        if not all_findings:
            print(f"PASS: no presentation-layer drift in {len(args.apps)} app(s)")
        else:
            for f in all_findings:
                print(f"[{f['severity'].upper():8}] {f['file']}: {f['check']}")
                print(f"           {f['detail']}")
                print(f"           evidence: {f['evidence']}")
            print(f"\n{len(all_findings)} finding(s) across {len(args.apps)} app(s)")
    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
