#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Number-neutral corpus waves W1-W3 over the finerenone-template clones.

THE SAFETY MODEL, IN ONE PARAGRAPH. 739 of the 749 template pages have no config and
no canonical object: the HTML page is the only copy of its own data. So this tool
never parses and never re-emits per-page data. It performs anchored replacement on
SHARED CODE AND PROSE only, and it proves it did so three independent ways.

  ANCHORING -- FAIL CLOSED. Each anchor locates exactly one region. n == 1 -> apply.
  n == 0 -> SKIP the anchor, log NOT_PRESENT. n > 1 -> ABORT the whole page, log
  AMBIGUOUS. This is the inverse of clone_dashboard.py::replace_one(), which logs a
  skip and returns the source unchanged -- the silent-skip behaviour that let one
  base engine survive into 161 apps. Every touched page must reconcile as
  applied + skipped + aborted, with a reason for each.

  GUARD 1 -- RENDERED NUMBERS, ZERO TOLERANCE. Every number in the page's visible
  text (scripts, styles and comments removed, then tags stripped), as a multiset,
  before and after. Any difference at all discards the page's edit. This is the
  guard that enforces "no displayed quantity moved". It is why every replacement
  string in this file is digit-preserving.

  GUARD 2 -- DATA-SPAN BYTE IDENTITY. realData, allOutcomes, outcomeKeys, TRIALS and
  the evidence arrays must be byte-identical before and after. Not "equivalent" --
  identical. This is the mechanical proof that the extracted trial records were never
  touched, and it holds regardless of what the anchors did.

  GUARD 3 -- SCRIPT-NUMBER ATTRIBUTION. Numbers inside <script> are allowed to move
  only by exactly the amount the applied anchors account for. The engine computes the
  expected delta from each anchor's own before/after text and requires the file-level
  script delta to equal it. An unattributed digit anywhere in the JS discards the page.

Guards 1 and 2 are zero-tolerance. Guard 3 is an identity, not a threshold.

WHAT THIS TOOL DOES NOT DO. It does not touch the eight pages the SSOT rebuild lane
owns. It does not run W4-W7 (HTA removal, k/N, RoB enum, blocking guards) -- those
change displayed numbers and wait for three certified exemplars. It does not repair
the living-search gate, only the false claim that the gate is in service; the repair
needs each review's own PICO and is Tier E.

Usage:
    python corpus_wave.py --stage0 --scratch DIR      # exemplars, scratch copy only
    python corpus_wave.py --pages A.html B.html --apply
    python corpus_wave.py --pages A.html --dry-run    # default
"""
from __future__ import annotations

import argparse
import collections

import json
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import corpus_detectors as CD  # noqa: E402
import data_spans as _DS  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ARABIC = CD.ARABIC_FINERENONE

# The SSOT rebuild lane is the sole writer of these. Excluded from every wave,
# permanently -- they are being replaced, not patched.
SSOT_OWNED = {
    "ARNI_HF_REVIEW.html", "SGLT2_HF_REVIEW.html", "SOTAGLIFLOZIN_HF_REVIEW.html",
    "ARNI_HFREF_SSOT.html", "ALIROCUMAB_LIPID_SSOT.html", "ANTIMALARIAL_ACT_SSOT.html",
    "COVID19_VACCINES_SSOT.html", "CRYPTOCOCCAL_MENINGITIS_SSOT.html",
    "LENACAPAVIR_PREP_SSOT.html", "MALARIA_VACCINES_SSOT.html",
    "PREVNAR15_PNEUMO_SSOT.html", "RIVAROXABAN_ACS_SSOT.html", "TIGECYCLINE_CIAI_SSOT.html",
}
# Targets of the 8-app rebuild queue: iv-iron, incretin, mavacamten, attr-cm,
# mitral-teer, pcsk9, bempedoic, colchicine. Matched by stem so the queue's own
# naming choices cannot let a page slip back into scope.
QUEUE_STEMS = ("IV_IRON", "INCRETIN", "MAVACAMTEN", "ATTR_CM", "MITRACLIP", "MITRAL_",
               "PCSK9", "BEMPEDOIC", "COLCHICINE", "RIVAROXABAN")


def is_excluded(name: str):
    if name in SSOT_OWNED:
        return "SSOT rebuild lane owns this page"
    up = name.upper()
    for stem in QUEUE_STEMS:
        if up.startswith(stem):
            return f"8-app rebuild queue is rebuilding this topic ({stem})"
    return None


# --------------------------------------------------------------------------- guards

NUM = re.compile(r"\d+(?:[.,]\d+)*")
SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.S | re.I)
STYLE = re.compile(r"<style\b[^>]*>.*?</style>", re.S | re.I)
COMMENT = re.compile(r"<!--.*?-->", re.S)
TAG = re.compile(r"<[^>]+>")


def visible_text(html: str) -> str:
    s = SCRIPT.sub(" ", html)
    s = STYLE.sub(" ", s)
    s = COMMENT.sub(" ", s)
    return TAG.sub(" ", s)


def rendered_numbers(html: str):
    """Numbers as a READER meets them. Script bodies are removed rather than merely
    tag-stripped: a digit in a JS expression is not a displayed quantity, and counting
    it would make this guard impossible to pass for any code fix at all."""
    return collections.Counter(m.group(0).replace(",", "") for m in NUM.finditer(visible_text(html)))


def file_numbers(html: str):
    """Every number anywhere in the file, displayed or not. Used by guard 3, which is
    an identity rather than a threshold: the whole-file delta must equal the sum of the
    deltas the applied anchors themselves account for. Anything else is collateral."""
    return collections.Counter(m.group(0) for m in NUM.finditer(html))


# Inline scripts only, and only ones that are actually JavaScript: a page also carries
# <script type="application/ld+json">, which node cannot parse and which is not code.
INLINE_SCRIPT = re.compile(
    r"<script\b(?![^>]*\bsrc=)(?![^>]*type=[\"'][^\"']*json)[^>]*>(.*?)</script>",
    re.S | re.I)
_NODE_TMP = pathlib.Path(__file__).resolve().parent / "_syntax_tmp.js"


def js_syntax_errors(html: str):
    """Parse every inline <script> with node --check. Returns a list of error summaries.

    Not a lint: a pure parse. It answers the one question the source-level guards
    cannot -- does this file still run. If node is unavailable the check returns a
    sentinel rather than silently passing; a gate that can only report 'clean' is not
    a gate."""
    import subprocess
    errs = []
    blocks = [b for b in INLINE_SCRIPT.findall(html) if b.strip()]
    for i, b in enumerate(blocks):
        try:
            _NODE_TMP.write_text(b, encoding="utf-8")
            # explicit utf-8: node echoes the offending source line, and the default
            # cp1252 decode on Windows raises on any non-latin byte in the page.
            p = subprocess.run(["node", "--check", str(_NODE_TMP)],
                               capture_output=True, text=True, timeout=120,
                               encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return ["NODE_UNAVAILABLE: syntax check did not run"]
        except Exception as e:                                # noqa: BLE001
            return [f"NODE_ERROR: {e}"]
        if p.returncode != 0:
            # node echoes the offending source line, which on a minified page is ~1 MB.
            # Keep the diagnosis, drop the haystack.
            lines = [ln.strip() for ln in (p.stderr or "").splitlines() if ln.strip()]
            diag = next((ln for ln in lines if "Error" in ln and len(ln) < 400), "")
            if not diag:
                diag = next((ln[:160] for ln in lines if "Error" in ln), (p.stderr or "")[:160])
            errs.append(f"block{i}: {diag[:200]}")
    try:
        _NODE_TMP.unlink(missing_ok=True)
    except OSError:
        pass
    return errs


DATA_SPANS = [
    ("realData", re.compile(r"realData=\{.*?\n", re.S)),
    ("allOutcomes", re.compile(r"allOutcomes:\[.*?\]", re.S)),
    ("outcomeKeys", re.compile(r"window\.RapidMeta\.outcomeKeys\s*=\s*\{.*?\};", re.S)),
    ("TRIALS", re.compile(r"\bTRIALS\s*=\s*\[.*?\];", re.S)),
    ("evidence", re.compile(r"evidence:\[.*?\]", re.S)),
    ("AUTO_INCLUDE", re.compile(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new Set\(\[[^\]]*\]\)")),
]


def data_fingerprint(html: str):
    """A fingerprint of every per-page data surface. Must be byte-identical across the
    edit. Uses the raw matched text, not a parse -- parsing is exactly the step this
    whole approach exists to avoid.

    DELEGATED TO data_spans.py, WHICH BRACE-MATCHES. The six regexes that used to live
    in DATA_SPANS included three -- realData, outcomeKeys, TRIALS -- that matched ZERO
    times on all 863 pages, because the corpus writes `realData:{"NCT..."` as an object
    property and the pattern expected an assignment. A span that matches nothing
    contributes (0,0,0) on both sides and therefore always compares equal, so guard 2
    was silently enforcing byte-identity on three spans while claiming six -- and the
    2.9 MB of realData it was named after was not one of the three.

    The replacement finds the spans by brace matching and treats an expected-but-absent
    span as an ERROR. Re-verified after the fix: all 863 pages' data spans are
    byte-identical to origin/main across W1-W4, so nothing was in fact corrupted -- but
    that is now a measurement rather than an assumption.
    """
    fp, missing = _DS.fingerprint(html)
    if missing:
        # Surfaced into the fingerprint itself so the comparison cannot silently pass.
        fp["__missing_required__"] = tuple(sorted(missing))
    return fp


# --------------------------------------------------------------------------- anchors
# Each anchor: id, wave, pattern (regex, must match EXACTLY once), and repl -- either a
# string (re.sub-style backrefs allowed) or a callable(match, page_ctx) -> str.
# `optional` marks anchors whose absence is expected on some lineages.

GROUP_REF = re.compile(r"\\(?:\d|g<)")


class Anchor:
    def __init__(self, aid, wave, klass, pattern, repl, why, optional=False, gate=None):
        self.aid, self.wave, self.klass = aid, wave, klass
        self.rx = re.compile(pattern, re.S)
        self.repl = repl
        self.why = why
        self.optional = optional
        self.gate = gate  # callable(html, path) -> None (ok) or reason-to-skip
        # String replacements are expanded through re.Match.expand, which INTERPRETS
        # backslashes. A JS escape such as \' survives expansion as a literal
        # backslash-quote and, outside a string literal, is a SyntaxError that a
        # source-level number guard cannot see. Caught once in Stage 0 on four
        # exemplars; this refuses the class outright. Use a callable repl instead.
        if isinstance(repl, str):
            for m in re.finditer(r"\\", repl):
                if not GROUP_REF.match(repl[m.start():m.start() + 3]):
                    raise ValueError(
                        f"anchor {aid}: string replacement contains a backslash that is "
                        f"not a group reference; use a callable repl so re.Match.expand "
                        f"never sees it")


MARK = "/*RM-FIX-{}*/"


def _ctx_freeze_date(html):
    m = re.search(r'id="proto-reg-date"[^>]*>([0-9]{4}-[0-9]{2}-[0-9]{2})<', html)
    return m.group(1) if m else None


def _repl_protocol_date(m, ctx):
    fd = ctx["freeze_date"]
    return (f'protocolDate:"{fd}"/*RM-FIX-D18b2 role: protocol-pack freeze date, '
            f'mirrors the displayed Protocol Freeze Date (#proto-reg-date). '
            f'The displayed Last Substantive Amendment is #proto-amend-date.*/')


def _gate_protocol_date(html, path):
    if _ctx_freeze_date(html) is None:
        return "no #proto-reg-date on this page; cannot name the role without inventing a date"
    return None


QA4_BANNER_TEXT = (
    "The headline confidence interval is the Wald interval. The HKSJ sensitivity "
    "interval disagrees with it about whether the null is excluded, so the "
    "significance verdict shown above is interval-dependent.")


def _repl_qa4_banner(m, ctx):
    """Hooked into the RESULTS render, immediately after the page computes its own
    waldSig / hksjSig, and it REUSES those two variables rather than recomputing them.

    Three iterations to get here, each one worth recording:

      1. Attached to the QA4 check object. QAEngine.render() returns early when
         #qa-container is absent and is called from exactly one place -- a "Run QA"
         button -- so the banner only appeared for a reader who clicked it. A warning
         a reader must opt into is the failure this fix exists to correct.
      2. Moved to the results render but with the significance test written by hand as
         c.lci>1||c.uci<1. That is wrong for a continuous outcome, where the null is 0,
         and it only matched the Gen-2 block, leaving ~165 Gen-1 pages uncovered.
      3. This: anchor on the page's OWN `const _nullVal=_isCont?0:1, waldSig=..., hksjSig=...`
         line, which exists exactly once on all 881 template pages of both generations
         and already handles the continuous case. One anchor, full coverage, and the
         predicate is the page's rather than a second copy that could drift from it.

    Built as a callable, not a string, so re.Match.expand never touches it: the emitted
    JS contains quote characters, and expand's backslash handling turned an earlier
    string version into a SyntaxError."""
    icon = '<i class="fa-solid fa-triangle-exclamation mr-2"></i>'
    js = ("try{const _b=document.getElementById('qa4-discordance-banner');"
          "if(_b){const _bad=waldSig!==hksjSig;_b.classList.toggle('hidden',!_bad);"
          "if(_bad)_b.innerHTML='" + icon + QA4_BANNER_TEXT + "';}}catch(e){}")
    return m.group(1) + MARK.format("D17") + js


PAGINATION_CALLSITE = re.compile(
    r'fetchWithTimeout\(ctgovUrl\)\.then\(r=>\{if\(!r\.ok\)throw new Error\("CT\.gov HTTP "'
    r'\+r\.status\);return r\.json\(\)\}\)')


def _gate_pagination_callsite(html, path):
    n = len(PAGINATION_CALLSITE.findall(html))
    if n != 1:
        return (f"the CT.gov promise leg this helper replaces matches {n} times; "
                f"injecting the helper alone would be dead code behind a false claim")
    return None


def _gate_benchmark_keys(html, path):
    """Only drop the inherited finerenone benchmark keys when the page's own outcomes
    do not use them. If they do, removing the key changes what the benchmark panel
    renders, which is per-page work and not a number-neutral edit."""
    inherited = ["Renal40", "Renal57", "KidneyComp", "HF_CV_First", "Hyperkalemia"]
    labels = set(re.findall(r'shortLabel:"([^"]{1,60})"', html))
    labels |= set(re.findall(r'"outcome":"([^"]{1,60})"', html))
    used = [k for k in inherited if k in labels]
    if used:
        return f"page's own outcomes use inherited key(s) {used}; removal would change a rendered benchmark"
    return None


ANCHORS = [
    # ---------------------------------------------------------------- W1
    Anchor(
        "D18b", "W1", "D18b",
        r"Per ICMJE 2023, GitHub commit hash \+ timestamp constitutes a verifiable "
        r"pre-registration record equivalent to PROSPERO for tracking outcome / "
        r"eligibility / analysis-plan changes\.",
        "Retrospective public protocol pack, not prospectively registered. A repository "
        "commit is not a registration record recognised under ICMJE 2023: the GitHub "
        "commit hash and timestamp record when a file changed, which is version control, "
        "not prospective registration, and is not equivalent to a PROSPERO entry.",
        "the page contradicts this claim in its own PRISMA item 24; there is no page on "
        "which the sentence is true. Digit-preserving: one '2023' in, one '2023' out."),

    Anchor(
        "D18b2", "W1", "D18b2",
        r'protocolDate:"\d{4}-\d{2}-\d{2}"',
        _repl_protocol_date,
        "protocolDate is write-only state that disagrees with the displayed dates; "
        "reconcile it to the displayed freeze date and name both roles",
        gate=_gate_protocol_date),

    Anchor(
        "D7a-toggle", "W1", "D7a",
        r"toggleArabic\(\)\{if\(this\._arActive=!this\._arActive,",
        'toggleArabic(){' + MARK.format("D7a") +
        'showToast("Arabic display is disabled on this review: the bundled dictionary was '
        'inherited from another review and is not a translation of this page.");return;'
        'if(this._arActive=!this._arActive,',
        "the dictionary is wrong on both sides on 747 pages -- the value is still the "
        "finerenone token and the English keys came from an intermediate lineage"),

    Anchor(
        "D7a-button", "W1", "D7a",
        r'(<button onclick="RapidMeta\.toggleArabic\(\)")',
        r'\1 style="display:none" data-rm-fix="D7a"',
        "hide the entry point as well as neutralise it"),

    Anchor(
        "D7b-narrative", "W1", "D7b",
        r", a non-steroidal mineralocorticoid receptor antagonist, \$\{effectClause\}",
        " ${effectClause}",
        "the appositive is asserted about whatever drug the clone was retitled to. "
        "FINERENONE_REVIEW.html is excluded by name -- it is the one page where it is true."),

    Anchor(
        "D7b-plain", "W1", "D7b",
        r' reduced the risk of major heart and kidney events by about "',
        ' was associated with a lower risk of the pooled primary outcome, by about "',
        "the cardiorenal endpoint claim is asserted on geographic atrophy and schizophrenia"),

    Anchor(
        "D3a-v119", "W1", "D3a",
        r"if\(this\.state\.trials\?\.length&&!this\.state\._migrated_v119_dual_review_signoff\)"
        r"\{.*?this\.state\._migrated_v119_dual_review_signoff=!0,mutated&&this\.save\(\)\}",
        # Gated on a NEW flag, not on _migrated_v119. Anyone who has already opened
        # the page has the v119 flag set, so a scrub keyed to it would never run for
        # exactly the readers whose state carries the fabricated sign-off. It sets
        # both flags and always saves, so it runs once per reader and never again.
        'if(this.state.trials?.length&&!this.state._migrated_v120_unsealed_signoff_scrub){'
        + MARK.format("D3a") +
        'const unsealed=o=>o&&o.confirmed&&!o.sig1&&!o.sig2&&'
        '"MA"===o.reviewer1&&"SR"===o.reviewer2;'
        'this.state.trials.forEach(t=>{'
        'if(unsealed(t.screenReview)){delete t.screenReview.confirmed,delete t.screenReview.ts2}'
        'if(t.data){if(unsealed(t.data.extractionSignoff))delete t.data.extractionSignoff;'
        'if(unsealed(t.data.robSignoff))delete t.data.robSignoff}});'
        'this.state._migrated_v119_dual_review_signoff=!0,'
        'this.state._migrated_v120_unsealed_signoff_scrub=!0,this.save()}',
        "v119 stamped reviewer1/reviewer2 + confirmed + 'Cochrane RoB 2.0' on every trial "
        "with no human and no seal. The replacement stops stamping AND removes stamps "
        "already written to a returning reader's state. It keys on the missing "
        "cryptographic seal, never on the initials -- MA and SR are real people and a "
        "name-based rule would delete genuine sign-offs."),

    Anchor(
        "D5b-notes", "W1", "D5b",
        r"BENCHMARK_OUTCOME_NOTES=\{[^\n]*?default:\"\"\}",
        'BENCHMARK_OUTCOME_NOTES={default:""}' + MARK.format("D5b"),
        "the notes cite FINEARTS-HF as the reference estimand on reviews that are not "
        "about finerenone. Skipped on a real finerenone review."),

    Anchor(
        "D5b-keys", "W1", "D5b",
        r"BENCHMARK_OUTCOME_MAP=\{([^}]*)\}",
        lambda m, ctx: "BENCHMARK_OUTCOME_MAP={" + ",".join(
            p for p in m.group(1).split(",")
            if p.split(":")[0].strip('"') not in
            ("Renal40", "Renal57", "KidneyComp", "HF_CV_First", "Hyperkalemia")) + "}",
        "finerenone endpoint keys resolving to a benchmark on non-finerenone topics",
        gate=_gate_benchmark_keys),

    # ---------------------------------------------------------------- W2
    Anchor(
        "D17-pooling-row", "W2", "D17",
        r"REML random-effects, HKSJ-adjusted \(inverse-variance weighting\)</td>",
        "REML random-effects (inverse-variance weighting); the headline interval is the "
        "Wald normal-approximation interval. The HKSJ-adjusted interval is reported "
        "alongside it as a sensitivity analysis and does not govern the significance "
        "verdict.</td>",
        "the engine builds the headline interval as exp(pLogOR +/- z*pSE) around the REML "
        "point estimate. HKSJ is a sidecar. Correcting the text makes the page true; "
        "headlining HKSJ instead would change 749 published significance verdicts."),

    Anchor(
        "D17-ai-row", "W2", "D17",
        r"REML\+HKSJ primary with DerSimonian-Laird sensitivity pooling",
        "REML point estimation with a Wald primary interval and an HKSJ sensitivity interval",
        "same declaration, restated in the AI-contribution disclosure"),

    Anchor(
        "D17-annotation", "W2", "D17",
        r"Analysis performed using a REML random-effects model \(HKSJ-adjusted\) with "
        r"\$\{ciPct\}% confidence intervals\. HKSJ correction applied with max\(1, q\*\) safeguard\.",
        "Analysis performed using a REML random-effects model with ${ciPct}% Wald "
        "confidence intervals. The HKSJ-adjusted interval, computed with a max(1, q*) "
        "variance safeguard, is reported as a sensitivity analysis.",
        "figure annotation restated the same claim"),

    Anchor(
        "D17-methods-para", "W2", "D17",
        r"with the Hartung-Knapp-Sidik-Jonkman adjustment of the \"\+confLevel\+\"% "
        r"confidence interval and a Q/\(k−1\) variance-inflation floor to prevent CI "
        r"under-coverage when Q < k−1\.",
        'reporting the "+confLevel+"% Wald confidence interval as the primary interval. '
        'A Hartung-Knapp-Sidik-Jonkman interval with a Q/(k−1) variance-inflation floor, '
        'which prevents CI under-coverage when Q < k−1, is reported alongside it as a '
        'sensitivity analysis.',
        "the methods paragraph asserted the reported interval was HK-adjusted"),

    Anchor(
        "D17-word-export", "W2", "D17",
        r"<strong>Methods:</strong> REML random-effects model \(HKSJ-adjusted\)\.",
        "<strong>Methods:</strong> REML random-effects model; Wald primary interval, "
        "HKSJ sensitivity interval.",
        "the exported Word document repeated the claim"),

    Anchor(
        "D17-qa4-banner", "W2", "D17",
        r'(const _nullVal=_isCont\?0:1,waldSig=c\.lci>_nullVal\|\|c\.uci<_nullVal,'
        r'hksjSig=c\.hksjLCI>_nullVal\|\|c\.hksjUCI<_nullVal,'
        r'hksjCard=hksjEl\.closest\("\.glass"\)\|\|hksjEl\.parentElement;)',
        _repl_qa4_banner,
        "QA4 already computes the Wald-vs-HKSJ discordance and downgrades it to a warn "
        "chip behind a button. This raises it to a banner rendered next to the headline "
        "on every analysis run. Additive: the container is empty and hidden unless the "
        "two intervals actually disagree about whether the null is excluded."),

    Anchor(
        "D17-qa4-container", "W2", "D17",
        r'(<div id="stale-banner" class="hidden stale-banner[^>]*></div>)',
        r'\1'
        r'<div id="qa4-discordance-banner" class="hidden bg-rose-900/50 border '
        r'border-rose-700 text-rose-200 text-xs p-3 rounded-xl mx-6 mt-2 mb-0"></div>',
        "empty container so the banner adds no static text and therefore no static number"),

    Anchor(
        "T6-tau2-label", "W2", "T6",
        r"τ² \(DerSimonian-Laird\)",
        "τ² (REML)",
        "the same sentence already says the REML estimator was used; tau2 = k>=2 ? "
        "tau2_reml : tau2_dl, so the headline tau-squared is the REML fixed-point iterate"),

    Anchor(
        "T6-trace", "W2", "T6",
        r'addTrace\("DerSimonian-Laird \("\+ciPct\+"% CI\)",dlL,dlU',
        'addTrace("REML — Wald ("+ciPct+"% CI)",dlL,dlU',
        "dlL/dlU are r.lci/r.uci -- the Wald interval around the REML point estimate, "
        "not a DerSimonian-Laird fit"),

    Anchor(
        "T6-figcaption", "W2", "T6",
        r"Fig\. — DerSimonian-Laird \(standard\), Hartung-Knapp-Sidik-Jonkman \(adjusted\), "
        r"and Prediction Interval estimates",
        "Fig. — REML with Wald interval (headline), Hartung-Knapp-Sidik-Jonkman "
        "(sensitivity), and Prediction Interval estimates",
        "figure caption named the headline leg after an estimator the page does not fit"),

    # ---------------------------------------------------------------- W3
    Anchor(
        "D13a-src-table", "W3", "D13a",
        r'(<code class="text-\[10px\] text-slate-400 font-mono break-all">'
        r'https://clinicaltrials\.gov/api/v2/studies\?[^<]*?)&amp;filter\.overallStatus=COMPLETED',
        r"\1",
        "displayed source query: a RECRUITING or ACTIVE_NOT_RECRUITING trial is exactly "
        "what a living review exists to catch, and this filter excluded every one"),

    Anchor(
        "D13a-prov-block", "W3", "D13a",
        r'(<code class="text-\[9px\] text-slate-400 font-mono leading-relaxed block break-all">'
        r'https://clinicaltrials\.gov/api/v2/studies\?[^<]*?)&amp;filter\.overallStatus=COMPLETED',
        r"\1",
        "same query, restated in the provenance block"),

    Anchor(
        "D13a-live-query", "W3", "D13a",
        r'(const ctgovUrl="https://clinicaltrials\.gov/api/v2/studies\?[^"]*?)'
        r'&filter\.overallStatus=COMPLETED',
        r"\1",
        "the live acquisition query"),

    Anchor(
        "D13a-checkupdates", "W3", "D13a",
        r'(await fetch\("https://clinicaltrials\.gov/api/v2/studies\?[^"]*?)'
        r'&filter\.overallStatus=COMPLETED',
        r"\1",
        "the user-triggered 'check for updates' query"),

    # D13b is TWO anchors and the helper is gated on the call site existing. A first
    # cut declared ctgovFetchAll and never called it: the fetch still took one page,
    # while the report would have claimed pagination was added. Dead code that backs a
    # false claim is worse than no change, so the helper is only injected when the
    # promise-chain leg it replaces is present exactly once.
    Anchor(
        "D13b-helper", "W3", "D13b",
        r'(const ctgovUrl="https://clinicaltrials\.gov/api/v2/studies\?[^"]*")',
        r'\1' + MARK.format("D13b") +
        r',ctgovFetchAll=async u=>{const out=[];let tok="",guard=0;'
        r'do{const r=await fetchWithTimeout(u+(tok?"&pageToken="+encodeURIComponent(tok):""));'
        r'if(!r.ok)throw new Error("CT.gov HTTP "+r.status);const j=await r.json();'
        r'(j.studies||[]).forEach(x=>out.push(x));'
        r'tok=j.nextPageToken||"";guard++}while(tok&&guard<20);return{studies:out}}',
        "223 pages take a fixed pageSize with no pageToken and drop everything past the "
        "first page silently. The helper follows nextPageToken through fetchWithTimeout, "
        "keeps the same HTTP error contract, and caps at 20 pages.",
        gate=_gate_pagination_callsite),

    Anchor(
        "D13b-wire", "W3", "D13b",
        r'fetchWithTimeout\(ctgovUrl\)\.then\(r=>\{if\(!r\.ok\)throw new Error\("CT\.gov HTTP "'
        r'\+r\.status\);return r\.json\(\)\}\)',
        "ctgovFetchAll(ctgovUrl)",
        "the CT.gov leg of Promise.allSettled; the consumer reads ctResult.value.studies, "
        "which is why the helper returns {studies}"),

    Anchor(
        "D6-freq", "W3", "D6",
        # Anchored to the rendered table cell. The bare sentence also occurs as an
        # English KEY inside the inherited Arabic dictionary, and the fail-closed
        # counter correctly aborted the page until this anchor was made unique.
        r'(<td class="p-4 text-slate-300">)Continuous \(living review\); formal snapshot '
        r"at each new trial publication",
        r"\g<1>"
        "Automated surveillance is not currently in service for this review: the "
        "registry search is user-triggered and its eligibility gate is not keyed to this "
        "review's own population or endpoints. Updates are manual, at no guaranteed "
        "interval.",
        "the claim is false on all 749: the search is button-triggered, the population "
        "regex is frozen on heart-failure/CKD on 737 pages, and the status filter "
        "excluded every open trial"),

    Anchor(
        "D6-version", "W3", "D6",
        r" \(Living Protocol &mdash; auto-updating\)",
        " (Living Protocol &mdash; manually updated)",
        "the protocol does not auto-update"),

    Anchor(
        "T9-predicate", "W3", "T9",
        r"(NMAEngine=\{_getConfig:\(\)=>NMA_CONFIG\?\?RapidMeta\.state\?\.nmaNetwork\?\?null,)",
        r"\1" + MARK.format("T9") +
        r"_isConnected(){const cfg=this._getConfig();if(!cfg)return!1;"
        r"const comps=(cfg.comparisons??[]).filter(c=>c&&c.t1&&c.t2&&(c.trials??[]).length>0);"
        r"if(comps.length<2)return!1;const nbr=new Map();"
        r"comps.forEach(c=>{nbr.has(c.t1)||nbr.set(c.t1,new Set()),nbr.has(c.t2)||nbr.set(c.t2,new Set()),"
        r"nbr.get(c.t1).add(c.t2),nbr.get(c.t2).add(c.t1)});"
        r"for(const arms of nbr.values())if(arms.size>=2)return!0;return!1},",
        "at least two distinct active treatments must share a comparator before an "
        "indirect comparison is even defined. A four-spoke star (four DOACs on a shared "
        "warfarin control) passes; a lone head-to-head does not."),

    Anchor(
        "T9-gate", "W3", "T9",
        r",this\.renderVersionDiff\(\),NMA_CONFIG\)\{const nmaBtn=document\.getElementById"
        r'\("btn-tab-nma"\);nmaBtn&&\(nmaBtn\.style\.display=""\)\}',
        ',this.renderVersionDiff(),!0){const nmaBtn=document.getElementById("btn-tab-nma"),'
        'nmaOk=!!NMA_CONFIG&&NMAEngine._isConnected();'
        'nmaBtn&&(nmaBtn.style.display=nmaOk?"":"none");'
        'if(!nmaOk){const nmaSec=document.getElementById("tab-nma");'
        'nmaSec&&nmaSec.classList.add("hidden")}}',
        "the tab was revealed on NMA_CONFIG being truthy, with no connectivity check"),

    # ---------------------------------------------------------------- W4
    # W4 IS THE FIRST WAVE THAT CHANGES WHAT A READER SEES. Two cards stop being
    # rendered. It is nonetheless STATICALLY number-neutral: every constant it removes
    # (.133, 3e3, the "3-year" label, "$3,000") lives inside <script>, and guard 1
    # counts numbers in the visible text with script bodies removed. So the zero-
    # tolerance static guard stays ON for W4 exactly as it was for W1-W3, and the
    # expected difference is declared and measured at RUNTIME by render_check.py.
    # That is the whole reason the two guards are separate.
    Anchor(
        "D18a-engine", "W4", "D18a",
        r"HTAEngine=\{calculate\(res\)\{.*?\}\},(?=AnalysisEngine=\{)",
        lambda m, ctx: (
            'HTAEngine={calculate(){return null},render(){' + MARK.format("D18a") +
            'const c=document.getElementById("hta-container");c&&(c.innerHTML="")}},'),
        "nnt=Math.abs(1/(.133*(1-or))) asserts a 13.3% baseline event rate on every "
        "topic in the corpus, and costPerEvent multiplies it by a $3,000 price that "
        "exists nowhere in any source. The horizon is a string in a label, not an "
        "input, so the '3-year' NNT is not a 3-year anything. A jurisdiction, price "
        "source, discount rate, horizon and per-review baseline risk cannot be invented "
        "for 650 topics, so the module is removed rather than parameterised. The stub "
        "keeps the call site valid and clears the container.",
        gate=lambda html, path: (
            "CANGRELOR_PCI_REVIEW derives its NNT from the page's own pooled control "
            "event rate and says so; only its cost card is defective. Handled by "
            "D18a-cangrelor-cost instead."
            if path.name == "CANGRELOR_PCI_REVIEW.html" else None)),

    # The hand inspection the plan demanded of the 1-variant outlier, carried out and
    # recorded rather than swept in. CANGRELOR's calculate() sums cE/cN across the
    # page's own included trials, refuses to return anything when the CER is not
    # finite, and captions the NNT with an explicit "this is NOT an established
    # treatment effect" and a real 48-hour horizon. That half is legitimate and is
    # kept. Its cost card is not: it is the same hardcoded 3e3, and it multiplies an
    # ANNUAL price by an NNT defined over 48 hours, which is incoherent on its face.
    Anchor(
        "D18a-cangrelor-cost", "W4", "D18a",
        r'<div>\\n\\n\\n                        <div class="text-\[10px\] text-slate-400 '
        r'uppercase font-bold mb-1">Drug Cost per Event Avoided</div>.*?'
        r'assumed annual cost of \$3,000\.</div>\\n\\n\\n                    </div>',
        lambda m, ctx: MARK.format("D18a") + "",
        "removes only the cost card and leaves the data-derived NNT card standing",
        gate=lambda html, path: (
            None if path.name == "CANGRELOR_PCI_REVIEW.html"
            else "this anchor is for the CANGRELOR variant only")),

    # D18a2 -- restore the NNT guard the older lineage already had. On the pages that
    # carry isHRMode, NNT is suppressed in HR/RR mode because a hazard ratio does not
    # convert to an absolute risk reduction without a baseline hazard. The newer
    # lineage dropped that guard and computes an NNT from a risk-ratio-shaped ARD even
    # when the pooled estimand is a hazard ratio.
    Anchor(
        "D18a2-patient", "W4", "D18a2",
        r"nntValue=avgCER>0&&ard>1e-9\?Math\.ceil\(1/ard\):null,"
        r"nnhValue=avgCER>0&&ard<-1e-9\?Math\.ceil\(1/Math\.abs\(ard\)\):null",
        lambda m, ctx: (
            '_rmIsHR="HR"===RapidMeta.emLabel("short"),' + MARK.format("D18a2") +
            'nntValue=!_rmIsHR&&avgCER>0&&ard>1e-9?Math.ceil(1/ard):null,'
            'nnhValue=!_rmIsHR&&avgCER>0&&ard<-1e-9?Math.ceil(1/Math.abs(ard)):null'),
        "patient-mode NNT/NNH suppressed in HR mode, matching the older lineage"),

    Anchor(
        "D18a2-nyt", "W4", "D18a2",
        r'getElementById\("nyt-kn-nnt"\)\.textContent=nnt',
        lambda m, ctx: ('getElementById("nyt-kn-nnt").textContent=' +
                        MARK.format("D18a2") +
                        '"HR"===RapidMeta.emLabel("short")?"--":nnt'),
        "the report headline NNT tile, guarded the way the older lineage guards it"),

    Anchor(
        "D18a2-waitingroom", "W4", "D18a2",
        r"nntRaw=avgCER>0&&Math\.abs\(1-orVal\)>\.001\?"
        r"Math\.ceil\(1/Math\.abs\(avgCER\*\(1-orVal\)\)\):100,"
        r"affectedPer100=Math\.max\(0,Math\.min\(100,Math\.round\(100/nntRaw\)\)\)",
        lambda m, ctx: (
            '_rmIsHR="HR"===RapidMeta.emLabel("short"),' + MARK.format("D18a2") +
            'nntRaw=_rmIsHR?1/0:avgCER>0&&Math.abs(1-orVal)>.001?'
            'Math.ceil(1/Math.abs(avgCER*(1-orVal))):100,'
            'affectedPer100=_rmIsHR?0:Math.max(0,Math.min(100,Math.round(100/nntRaw)))'),
        "the waiting-room icon array colours 100 human figures from this NNT. In HR "
        "mode it was colouring them from an absolute risk reduction derived from a "
        "hazard ratio, which is not an absolute risk reduction."),

    Anchor(
        "D18a2-wr-label", "W4", "D18a2",
        r'getElementById\("wr-icon-label"\)\.textContent=0===affectedPer100\?'
        r'"No measurable effect per 100 patients":',
        lambda m, ctx: (
            'getElementById("wr-icon-label").textContent=' + MARK.format("D18a2") +
            '_rmIsHR?"Absolute NNT is not shown in HR/RR mode":'
            '0===affectedPer100?"No measurable effect per 100 patients":'),
        "with the figures blanked in HR mode the caption must say why. 'No measurable "
        "effect' would be a claim, and a false one: the quantity is not estimable, "
        "which is not the same as being zero.",
        # THE CALL-SITE GATE, in the form the plan's limit #3 demands. This anchor
        # READS _rmIsHR, which the sibling D18a2-waitingroom anchor DECLARES in the
        # same function. The census found the two anchors do not cover the same pages
        # -- 702 vs 652 -- so on 50 pages this replacement would have referenced an
        # undeclared binding and thrown a ReferenceError at render. The static number
        # guards cannot see that; node --check cannot either, because an undeclared
        # identifier is valid syntax. So the gate tests for the sibling's own output.
        # Testing for the bare name would not do: D18a2-patient introduces an _rmIsHR
        # in a DIFFERENT function scope, and that one is not visible here.
        gate=lambda html, path: (
            None if "affectedPer100=_rmIsHR?0:" in html
            else "D18a2-waitingroom did not apply on this page, so _rmIsHR is not "
                 "declared in this scope; adding a reader would be a ReferenceError")),

    # ---------------------------------------------------------------- W5
    # D12 -- k, N and the control event rate derived from ONE array.
    #
    # The page already contains the right answer and disagrees with itself.
    # GradeProfileEngine derives its cohort from c.plotData; RapidMeta.state.results
    # sets `k: c.k` (= plotData.length) beside `n:` summed over the FULL eligible
    # array. plotData has already dropped the no-published-HR trials in HR mode and
    # the double-zero / double-complete trials in binary mode -- and those dropped
    # trials are exactly what `n` still counts. So N is quoted for a cohort that was
    # never pooled, next to a k that was.
    #
    # The fix is not a new formula. It routes every site through ONE helper, so the
    # agreement between state.results.n and GRADE's totalN stops being a coincidence
    # that has to be re-checked and becomes structural. That agreement is then the
    # detector, exactly as the plan proposed.
    Anchor(
        "D12-helper", "W5", "D12",
        r"(,sanitizeCSVCell=val=>)",
        lambda m, ctx: (
            "," + MARK.format("D12") +
            # A trial with a null cE still randomised real participants, so it counts
            # toward N. It cannot count toward the CER: `(cE ?? 0)` over a real
            # denominator asserts the trial observed zero control events, which drags
            # the pooled rate down and inflates every NNT derived from it. Admitted
            # to the numerator only when BOTH counts are finite.
            "rmPooledCohort=pd=>{const a=Array.isArray(pd)?pd:[];"
            "let n=0,cE=0,cN=0;"
            "for(const d of a){const tn=Number(d?.tN),cn=Number(d?.cN),ce=Number(d?.cE);"
            "Number.isFinite(tn)&&(n+=tn),Number.isFinite(cn)&&(n+=cn),"
            "Number.isFinite(ce)&&Number.isFinite(cn)&&cn>0&&(cE+=ce,cN+=cn)}"
            "return{k:a.length,n,cer:cN>0?cE/cN:0,cerN:cN}},"
            # Same admissibility rule, over trial-shaped records, for the two report
            # surfaces that never receive plotData.
            "rmCerFromTrials=ts=>{let cE=0,cN=0;"
            "for(const t of ts||[]){const ce=Number(t?.data?.cE),cn=Number(t?.data?.cN);"
            "Number.isFinite(ce)&&Number.isFinite(cn)&&cn>0&&(cE+=ce,cN+=cn)}"
            "return cN>0?cE/cN:0}") + m.group(1),
        "one cohort helper, injected beside safeRob, so every consumer shares it"),

    Anchor(
        "D12-state-n", "W5", "D12",
        r"k:c\.k,n:trials\.reduce\(\(a,b\)=>a\+b\.data\.tN\+b\.data\.cN,0\)\.toLocaleString\(\)",
        lambda m, ctx: ("k:c.k," + MARK.format("D12") +
                        "n:rmPooledCohort(c.plotData).n.toLocaleString()"),
        "the headline N, moved onto the same array as the headline k"),

    Anchor(
        "D12-grade-n", "W5", "D12",
        r"totalN=c\.plotData\.reduce\(\(a,d\)=>a\+d\.tN\+d\.cN,0\),"
        r"totalCN=c\.plotData\.reduce\(\(a,d\)=>a\+d\.cN,0\),"
        r"cer=totalCN>0\?c\.plotData\.reduce\(\(a,d\)=>a\+d\.cer\*d\.cN,0\)/totalCN:0",
        lambda m, ctx: (MARK.format("D12") +
                        "totalN=rmPooledCohort(c.plotData).n,"
                        "totalCN=rmPooledCohort(c.plotData).cerN,"
                        "cer=rmPooledCohort(c.plotData).cer"),
        "GRADE was already right about WHICH array, and wrong in two smaller ways: "
        "d.tN+d.cN is NaN on a continuous plotData, which carries md/se and no counts, "
        "and its weighted CER admitted a null-cE trial as zero events. Routing it "
        "through the same helper fixes both and is what makes the agreement detector "
        "meaningful -- two sites that share a function cannot drift apart."),

    Anchor(
        "D12-patient-callsite", "W5", "D12",
        r"updatePatientMode\(c\.pOR,c\.lci,c\.uci,c\.k,trials\)",
        lambda m, ctx: ("updatePatientMode(c.pOR,c.lci,c.uci,c.k,trials,c.plotData)" +
                        MARK.format("D12")),
        "hand the patient module the pooled array as well as the eligible one"),

    # Both body anchors READ the parameter the call-site anchor supplies. Gated on it,
    # for the reason the W4 census taught: rmPooledCohort(undefined) returns a zero
    # cohort, so an ungated body edit would not throw -- it would silently render
    # N = 0 on every page where the call site did not match. A guard that fails loudly
    # is available here only by refusing to apply.
    Anchor(
        "D12-upm-gen2", "W5", "D12",
        r"updatePatientMode\(pOR,lci,uci,k,trials\)\{const effect=interpretRelativeEffect"
        r"\(pOR,lci,uci\),totalN=trials\.reduce\(\(a,b\)=>a\+\(b\.data\?\.tN\?\?0\)\+"
        r"\(b\.data\?\.cN\?\?0\),0\),avgCER=trials\.length>0\?trials\.reduce\(\(a,t\)=>"
        r"a\+\(t\.data\?\.cE\?\?0\)/\(t\.data\?\.cN\?\?1\),0\)/trials\.length:0",
        lambda m, ctx: (
            "updatePatientMode(pOR,lci,uci,k,trials,_pd){" + MARK.format("D12") +
            "const _pc=rmPooledCohort(_pd),"
            "effect=interpretRelativeEffect(pOR,lci,uci),totalN=_pc.n,avgCER=_pc.cer"),
        "the newer lineage averaged per-trial rates unweighted, with a missing cE "
        "counted as zero over a real denominator and a missing cN as a denominator "
        "of 1",
        gate=lambda html, path: (
            None if "updatePatientMode(c.pOR,c.lci,c.uci,c.k,trials,c.plotData)" in html
            else "call site does not pass plotData; the pooled array is not in scope")),

    Anchor(
        "D12-upm-gen1", "W5", "D12",
        r'updatePatientMode\(pOR,lci,uci,k,trials\)\{const isHRMode="HR"==='
        r'\(RapidMeta\.state\.effectMeasure\?\?"OR"\),emShort=RapidMeta\.emLabel\("short"\),'
        r'controlEventRate=pooledControlEventRate\(trials\)',
        lambda m, ctx: (
            "updatePatientMode(pOR,lci,uci,k,trials,_pd){" + MARK.format("D12") +
            'const _pc=rmPooledCohort(_pd),isHRMode="HR"===(RapidMeta.state.effectMeasure'
            '??"OR"),emShort=RapidMeta.emLabel("short"),controlEventRate=_pc.cer'),
        "same reconciliation on the older lineage, whose CER came from the full "
        "eligible array rather than the pooled one",
        gate=lambda html, path: (
            None if "updatePatientMode(c.pOR,c.lci,c.uci,c.k,trials,c.plotData)" in html
            else "call site does not pass plotData; the pooled array is not in scope")),

    Anchor(
        "D12-upm-gen1-n", "W5", "D12",
        r",totalN=trials\.reduce\(\(a,b\)=>a\+\(b\.data\?\.tN\?\?0\)\+\(b\.data\?\.cN\?\?0\),0\),"
        r"controlEventRatePct=",
        lambda m, ctx: "," + MARK.format("D12") + "totalN=_pc.n,controlEventRatePct=",
        "the older lineage's N, in the same const list",
        gate=lambda html, path: (
            None if "const _pc=rmPooledCohort(_pd),isHRMode=" in html
            else "D12-upm-gen1 did not apply, so _pc is not declared in this scope")),

    # The two report surfaces that are handed trial records rather than plotData. N is
    # not recomputed here -- renderNarrative reads it back out of state.results.n,
    # which D12-state-n has already reconciled -- so only the CER needs the fix.
    Anchor(
        "D12-wr-cer", "W5", "D12",
        r"avgCER=included\.length>0\?included\.reduce\(\(a,t\)=>a\+t\.data\.cE/t\.data\.cN,0\)"
        r"/included\.length:\.15",
        lambda m, ctx: (MARK.format("D12") +
                        "avgCER=included.length>0?rmCerFromTrials(included):.15"),
        "waiting-room control event rate: event-weighted, null-count trials excluded"),

    Anchor(
        "D12-narr-cer", "W5", "D12",
        r"avgCER=included\.length>0\?\(included\.reduce\(\(a,t\)=>a\+t\.data\.cE/t\.data\.cN,0\)"
        r"/included\.length\*100\)\.toFixed\(1\):\"--\"",
        lambda m, ctx: (MARK.format("D12") +
                        'avgCER=included.length>0?(100*rmCerFromTrials(included)).toFixed(1)'
                        ':"--"'),
        "the same rate as quoted in the report narrative"),

    Anchor(
        "D12-pooledcer", "W5", "D12",
        r"pooledControlEventRate=\(trials=\[\]\)=>\{let totalCtrlEvents=0,totalCtrlN=0;"
        r"return trials\.forEach\(t=>\{totalCtrlEvents\+=parseInt\(t\?\.data\?\.cE\?\?0,10\)\|\|0,"
        r"totalCtrlN\+=parseInt\(t\?\.data\?\.cN\?\?0,10\)\|\|0\}\),"
        r"totalCtrlN>0\?totalCtrlEvents/totalCtrlN:0\}",
        lambda m, ctx: ("pooledControlEventRate=(trials=[])=>" + MARK.format("D12") +
                        "rmCerFromTrials(trials)"),
        "the older lineage's shared CER helper. `parseInt(cE ?? 0) || 0` turned a "
        "missing count into zero events over a real denominator; the replacement "
        "drops the trial from both sides of the ratio instead."),

    # ---------------------------------------------------------------- W6
    # D4 -- the safeRob enum. `valid.includes(r) ? r : "low"` silently rewrites every
    # token it does not recognise -- "some-concerns", "unclear", "Some concerns", a
    # blank -- into LOW RISK OF BIAS, which is the most favourable value in the scale.
    # A missing assessment is rendered as a clean bill of health, and GRADE then
    # derives a certainty from it.
    #
    # Every change here moves in one direction: less certainty claimed, never more.
    Anchor(
        "D4-saferob", "W6", "D4",
        r'safeRob=rob=>\{const valid=\["low","some","high"\];return Array\.isArray\(rob\)\?'
        r'rob\.map\(r=>valid\.includes\(r\)\?r:"low"\):\["low","low","low","low","low"\]\}',
        lambda m, ctx: (
            "safeRob=rob=>{" + MARK.format("D4") +
            # Hyphen-normalised so "Some concerns", "some_concerns" and "SOME-CONCERNS"
            # all land on the same key. No regex literals: a backslash in a string
            # replacement is refused by this engine, and rightly.
            'const M={low:"low","low-risk":"low",some:"some","some-concerns":"some",'
            '"some-concern":"some",moderate:"some",unclear:"unclear",unknown:"unclear",'
            '"not-reported":"unclear","no-information":"unclear",'
            'high:"high","high-risk":"high","serious":"high"},'
            'nz=r=>{const k=String(r??"").trim().toLowerCase().split("_").join("-")'
            '.split(" ").join("-");return M[k]??"unclear"};'
            # The default for a non-array is "unclear", not "low". An absent RoB
            # assessment is an absent assessment.
            'return Array.isArray(rob)?rob.map(nz)'
            ':["unclear","unclear","unclear","unclear","unclear"]}'),
        "maps some-concerns/unclear correctly and sends anything unrecognised to "
        "unclear rather than to low"),

    # The continuous plotData path never went through safeRob at all -- it defaulted a
    # missing assessment straight to five lows. Routing it through the same function
    # is what makes "every pooled record carries five recognised tokens" true, which
    # in turn is what makes the `?? "low"` default inside the GRADE tallies dead code.
    Anchor(
        "D4-continuous-rob", "W6", "D4",
        r'rob:t\.data\.rob\|\|\["low","low","low","low","low"\]',
        lambda m, ctx: MARK.format("D4") + "rob:safeRob(t.data.rob)",
        "the continuous branch built its own five-low default instead of using safeRob"),

    # BLOCK THE AUTO-DERIVATION. Implemented at the single return site rather than in
    # the tallies, which occur twice and would abort the page. It is also the more
    # honest place: the tallies feed downgrade RULES that only ever inspect .high and
    # .some, so an unclear domain would contribute no downgrade at all and certainty
    # would stay HIGH -- the opposite of the intended direction. Refusing to state a
    # level claims nothing, which is the correct output when the inputs are unknown.
    Anchor(
        "D4-grade-block", "W6", "D4",
        r'return\{certainty:\["HIGH","MODERATE","LOW","VERY LOW"\]\[netLevel\],'
        r'badge:\["grade-high","grade-mod","grade-low","grade-vlow"\]\[netLevel\]',
        lambda m, ctx: (
            MARK.format("D4") +
            'const _robUnclear=data.some(d=>!Array.isArray(d.rob)||d.rob.length<1||'
            'd.rob.some(x=>"unclear"===x));'
            'return{robUnclear:_robUnclear,'
            'certainty:_robUnclear?"NOT DERIVABLE"'
            ':["HIGH","MODERATE","LOW","VERY LOW"][netLevel],'
            'badge:_robUnclear?"grade-vlow"'
            ':["grade-high","grade-mod","grade-low","grade-vlow"][netLevel]'),
        "when any pooled study carries an unrecognised or absent RoB domain the "
        "certainty is not derived. NOT DERIVABLE is not a rating -- it is the refusal "
        "to give one, which is what the evidence supports."),

    Anchor(
        "D4-overall", "W6", "D4",
        r'overallRob=rob\.includes\("high"\)\?"high":rob\.includes\("some"\)\?"some":"low"',
        lambda m, ctx: (MARK.format("D4") +
                        'overallRob=rob.includes("high")?"high"'
                        ':rob.includes("unclear")?"unclear"'
                        ':rob.includes("some")?"some":"low"'),
        "the extraction view's per-trial summary fell through to low for unclear, "
        "which would have undone safeRob one line later"),

    Anchor(
        "D4-cycle", "W6", "D4",
        r'const cycle=\{low:"some",some:"high",high:"low"\}',
        lambda m, ctx: (MARK.format("D4") +
                        'const cycle={low:"some",some:"high",high:"unclear",'
                        'unclear:"low"}'),
        "the manual RoB cycle had no way to reach or leave unclear; without this a "
        "reviewer clicking an unclear badge would silently coerce it to low"),

    Anchor(
        "D4-css", "W6", "D4",
        r"(\.rob-high \{ background-color: #ef4444; \})",
        lambda m, ctx: (m.group(1) +
                        "\n        .rob-unclear { background-color: #94a3b8; }"),
        "there was no .rob-unclear class; without it an unclear badge renders as an "
        "unstyled circle indistinguishable from low"),
]

WAVES = ("W1", "W2", "W3")
ALL_WAVES = ("W1", "W2", "W3", "W4", "W5", "W6")

# One stamp per wave. No digits other than the wave number itself, which is accounted
# for in the anchor delta like any other replacement.
STAMP = "<!--RM-WAVE-{}-APPLIED-->"


def stamp_for(wave):
    return STAMP.format(wave)


# --------------------------------------------------------------------------- engine

class PageResult:
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.applied, self.skipped, self.aborted = [], [], []
        self.status = "PENDING"
        self.guard = {}
        self.detectors_before, self.detectors_after = [], []
        self.new_text = None

    def reconcile(self):
        return len(self.applied) + len(self.skipped) + len(self.aborted)

    def as_dict(self):
        return {
            "page": self.path.name, "status": self.status,
            "applied": self.applied, "skipped": self.skipped, "aborted": self.aborted,
            "anchors_total": self.reconcile(), "guard": self.guard,
            "detectors_before": [f.as_dict() for f in self.detectors_before],
            "detectors_after": [f.as_dict() for f in self.detectors_after],
        }


def process(path, waves=WAVES, ignore_exclusions=False):
    r = PageResult(path)
    before = r.path.read_text(encoding="utf-8", errors="replace")

    excl = None if ignore_exclusions else is_excluded(r.path.name)
    if excl:
        r.status = "EXCLUDED"
        r.skipped.append({"anchor": "*", "reason": "EXCLUDED", "detail": excl})
        return r
    if not CD.is_template_page(before):
        r.status = "NOT_TEMPLATE"
        r.skipped.append({"anchor": "*", "reason": "NOT_TEMPLATE",
                          "detail": "no safeRob; not a finerenone-template clone"})
        return r

    # ---- idempotency -------------------------------------------------------------
    # THE WAVE IS NOT SAFE TO RUN TWICE unless this stamp is honoured. Measured on an
    # already-processed page: 5 of 29 anchors re-matched their own output and applied
    # again -- a second #qa4-discordance-banner div (duplicate DOM id), a second
    # _rmQa4 and a second _isConnected key in the same object literal, a doubled
    # style attribute, and a doubled protocolDate comment. Every guard passed, because
    # none of that moves a number or touches a data span. At batch scale, one retry or
    # one resumed run would have done this silently across hundreds of pages.
    todo = [w for w in waves if stamp_for(w) not in before]
    for w in waves:
        if w not in todo:
            r.skipped.append({"anchor": f"[{w}]", "reason": "WAVE_ALREADY_APPLIED",
                              "detail": f"page already carries {stamp_for(w)}"})
    if not todo:
        r.status = "ALREADY_APPLIED"
        return r

    r.detectors_before = CD.run(before, r.path)
    is_fin = CD.is_finerenone_review(before, r.path)
    ctx = {"freeze_date": _ctx_freeze_date(before), "is_finerenone": is_fin}

    s = before
    expected_script_delta = collections.Counter()

    for a in ANCHORS:
        if a.wave not in todo:
            continue
        # Class-level legitimate-instance exclusions.
        if is_fin and a.klass in ("D7b", "D5b"):
            r.skipped.append({"anchor": a.aid, "reason": "LEGITIMATE_INSTANCE",
                              "detail": "finerenone review: the string/keys are correct here"})
            continue
        hits = list(a.rx.finditer(s))
        if len(hits) == 0:
            r.skipped.append({"anchor": a.aid, "reason": "NOT_PRESENT",
                              "detail": "anchor matched 0 times"})
            continue
        if len(hits) > 1:
            r.aborted.append({"anchor": a.aid, "reason": "AMBIGUOUS",
                              "detail": f"anchor matched {len(hits)} times; refusing to guess"})
            r.status = "ABORTED"
            return r
        if a.gate:
            why = a.gate(s, r.path)
            if why:
                r.skipped.append({"anchor": a.aid, "reason": "GATED", "detail": why})
                continue
        m = hits[0]
        old = m.group(0)
        new = a.repl(m, ctx) if callable(a.repl) else m.expand(a.repl)
        if new == old:
            r.skipped.append({"anchor": a.aid, "reason": "NO_OP", "detail": "replacement equals source"})
            continue
        s = s[:m.start()] + new + s[m.end():]
        d = collections.Counter(x.group(0) for x in NUM.finditer(new))
        d.subtract(collections.Counter(x.group(0) for x in NUM.finditer(old)))
        expected_script_delta.update(d)
        r.applied.append({"anchor": a.aid, "wave": a.wave, "class": a.klass,
                          "why": a.why, "old": old[:600], "new": new[:600],
                          "old_len": len(old), "new_len": len(new)})

    if not r.applied:
        r.status = "NO_CHANGE"
        return r

    # Stamp only the waves that actually ran, so a later run of a different wave is
    # not blocked by this one.
    marks = "".join(stamp_for(w) for w in todo)
    idx = s.rfind("</body>")
    s = (s[:idx] + marks + s[idx:]) if idx != -1 else (s + marks)
    d = collections.Counter(x.group(0) for x in NUM.finditer(marks))
    expected_script_delta.update(d)

    # ---- guard 1: rendered numbers, zero tolerance ------------------------------
    nb, na = rendered_numbers(before), rendered_numbers(s)
    lost, gained = nb - na, na - nb
    r.guard["rendered_numbers"] = {
        "distinct_before": len(nb), "distinct_after": len(na),
        "total_before": sum(nb.values()), "total_after": sum(na.values()),
        "lost": dict(list(lost.items())[:20]), "gained": dict(list(gained.items())[:20]),
        "identical": not lost and not gained,
    }

    # ---- guard 2: per-page data spans, byte identity ---------------------------
    fb, fa = data_fingerprint(before), data_fingerprint(s)
    same_data = fb == fa
    r.guard["data_spans"] = {"identical": same_data,
                             "before": {k: v[:2] for k, v in fb.items()},
                             "after": {k: v[:2] for k, v in fa.items()}}

    # ---- guard 3: whole-file number attribution --------------------------------
    actual = collections.Counter(file_numbers(s))
    actual.subtract(file_numbers(before))
    actual = {k: v for k, v in actual.items() if v}
    expect = {k: v for k, v in expected_script_delta.items() if v}
    attributed = actual == expect
    r.guard["script_numbers"] = {"attributed": attributed,
                                 "actual_delta": dict(list(actual.items())[:20]),
                                 "expected_from_anchors": dict(list(expect.items())[:20])}

    # ---- structural sanity ------------------------------------------------------
    opens = len(re.findall(r"<div[\s>]", s))
    closes = s.count("</div>")
    r.guard["div_balance"] = {"open": opens, "close": closes, "balanced": opens == closes,
                              "before": (len(re.findall(r"<div[\s>]", before)), before.count("</div>"))}
    # Absolute script balance is NOT the test: several pages legitimately contain the
    # token "<script" inside a JS string, so the raw counts do not match even before
    # any edit. What must hold is that the edit did not change them.
    def _script_counts(t):
        return (len(re.findall(r"<script\b", t)), t.count("</script>"))
    sb_c, sa_c = _script_counts(before), _script_counts(s)
    r.guard["script_balance"] = {"before": sb_c, "after": sa_c, "balanced": sb_c == sa_c}

    # ---- guard 4: JS syntax ------------------------------------------------------
    # Guards 1-3 all read the SOURCE. A replacement that breaks JS syntax leaves every
    # number in the file perfect and the page blank. Stage 0 caught exactly that on
    # four exemplars (a backslash-escaped quote surviving re.Match.expand), so the
    # parse is now part of the gate rather than something the browser finds later.
    sy_before, sy_after = js_syntax_errors(before), js_syntax_errors(s)
    new_syntax = [e for e in sy_after if e not in sy_before]
    r.guard["js_syntax"] = {"before_errors": len(sy_before), "after_errors": len(sy_after),
                            "new": new_syntax[:3], "clean": not new_syntax}

    r.detectors_after = CD.run(s, r.path)
    cleared = [f.det for f in r.detectors_before if f.applicable and f.fired
               and not any(g.det == f.det and g.applicable and g.fired for g in r.detectors_after)]
    still = [f.det for f in r.detectors_after if f.applicable and f.fired and f.severity == "BLOCK"]
    r.guard["detectors"] = {"cleared": cleared, "still_firing_BLOCK": still}

    ok = (r.guard["rendered_numbers"]["identical"]
          and same_data and attributed
          and r.guard["div_balance"]["balanced"]
          and r.guard["script_balance"]["balanced"]
          and r.guard["js_syntax"]["clean"])
    r.status = "OK" if ok else "DISCARDED"
    if ok:
        r.new_text = s
    return r


def summarize(results):
    n = collections.Counter(r.status for r in results)
    print("\n" + "=" * 74)
    print("WAVE SUMMARY")
    print("=" * 74)
    for k in sorted(n):
        print(f"  {k:14s} {n[k]}")
    ap = sum(len(r.applied) for r in results)
    sk = sum(len(r.skipped) for r in results)
    ab = sum(len(r.aborted) for r in results)
    print(f"\n  anchors applied={ap}  skipped={sk}  aborted={ab}  (total {ap+sk+ab})")
    bad = [r for r in results if r.status == "DISCARDED"]
    for r in bad:
        print(f"\n  DISCARDED {r.path.name}")
        g = r.guard
        if not g.get("rendered_numbers", {}).get("identical", True):
            print(f"     rendered numbers moved: lost={g['rendered_numbers']['lost']} "
                  f"gained={g['rendered_numbers']['gained']}")
        if not g.get("data_spans", {}).get("identical", True):
            print("     per-page data spans changed -- this must never happen")
        if not g.get("script_numbers", {}).get("attributed", True):
            print(f"     unattributed script numbers: {g['script_numbers']['actual_delta']}")
        if not g.get("div_balance", {}).get("balanced", True):
            print(f"     div balance: {g['div_balance']}")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="*", default=[])
    ap.add_argument("--root", default=".")
    ap.add_argument("--waves", default="W1,W2,W3")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--scratch", default=None,
                    help="copy pages here first and operate on the copies only")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--ignore-exclusions", action="store_true",
                    help="Stage-0 only. The four exemplars are all rebuild-queue topics; "
                         "they are exercised in SCRATCH so the wave can be proven before "
                         "it ever runs on the branch. Refuses to combine with --apply.")
    a = ap.parse_args()
    if a.ignore_exclusions and not a.scratch:
        print("REFUSING: --ignore-exclusions is only permitted with --scratch. The "
              "rebuild queue owns those pages in the repo.")
        return 2

    waves = tuple(w.strip() for w in a.waves.split(",") if w.strip())
    root = pathlib.Path(a.root)
    targets = []
    for p in a.pages:
        q = pathlib.Path(p)
        targets.append(q if q.is_absolute() or q.exists() else root / p)

    if a.scratch:
        sd = pathlib.Path(a.scratch)
        sd.mkdir(parents=True, exist_ok=True)
        copied = []
        for t in targets:
            dst = sd / t.name
            shutil.copy2(t, dst)
            copied.append(dst)
        targets = copied
        print(f"Operating on scratch copies in {sd}")

    results = []
    for t in targets:
        r = process(t, waves, ignore_exclusions=a.ignore_exclusions)
        results.append(r)
        print(f"\n### {t.name}  -> {r.status}")
        for x in r.applied:
            print(f"   APPLIED  {x['anchor']:20s} [{x['wave']}/{x['class']}]")
        for x in r.skipped:
            print(f"   skipped  {x['anchor']:20s} {x['reason']}: {x['detail'][:80]}")
        for x in r.aborted:
            print(f"   ABORTED  {x['anchor']:20s} {x['reason']}: {x['detail'][:80]}")
        if r.guard:
            g = r.guard
            print(f"   guard: rendered-numbers identical={g['rendered_numbers']['identical']} "
                  f"data-spans identical={g['data_spans']['identical']} "
                  f"script-delta attributed={g['script_numbers']['attributed']} "
                  f"divs={g['div_balance']['balanced']}")
            print(f"   detectors cleared: {g['detectors']['cleared']}")
            if g['detectors']['still_firing_BLOCK']:
                print(f"   still firing (BLOCK): {g['detectors']['still_firing_BLOCK']}")
        if r.status == "OK" and (a.apply or a.scratch):
            t.write_text(r.new_text, encoding="utf-8")
            print("   WRITTEN")

    summarize(results)
    if a.json_out:
        pathlib.Path(a.json_out).write_text(
            json.dumps([r.as_dict() for r in results], indent=1, ensure_ascii=False),
            encoding="utf-8")
        print(f"\nreport -> {a.json_out}")
    return 0 if all(r.status in ("OK", "NO_CHANGE", "EXCLUDED", "NOT_TEMPLATE") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
