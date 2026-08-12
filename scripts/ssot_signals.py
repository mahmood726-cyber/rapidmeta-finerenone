"""SSOT-aware regression signals.

The existing seven signals in regression_check.py were written for AUTO pages and
every one of them is shaped by that architecture: they look for seeded trials in
JavaScript state, a RoB banner element, a WebR tag, and a pool computed in the
browser. An SSOT page has none of those BY DESIGN -- it carries no engine, no
runtime state and no WebR, because every number is projected at build time.

Until today the gate could not fail, so the mismatch was invisible. Now that it
can fail, running the AUTO signals against an SSOT page would block every push
touching one, for the sole reason that the page is the architecture we are moving
towards. This module supplies the signals that actually mean something for a
projected page, and `classify()` decides which set applies.

Each signal is written so that it can fail, and each is proved against a
deliberately broken page before it is trusted -- the same bar as every other
detector in the library.
"""
import re

# ---------------------------------------------------------------- classify


def classify(html):
    """AUTO | SSOT | STUB | UNKNOWN, from the page itself, not from its filename.

    Filenames lie: ARNI_HF_REVIEW.html is an SSOT page and MITRAL_FUNCMR_REVIEW.html
    is an AUTO page, and both end in _REVIEW.html.
    """
    if len(html) < 20000 and "opening the full" in html.lower():
        return "STUB"
    if "RapidMeta" in html and re.search(r"<script[^>]*>", html):
        # an engine page: carries the app object and a script that builds state
        if "AnalysisEngine" in html or "switchTab" in html or "realData" in html:
            return "AUTO"
    if 'class="panel"' in html and "Submission readiness:" in html:
        return "SSOT"
    if re.search(r"<script", html) is None and "canonical object" in html:
        return "SSOT"
    return "UNKNOWN"


# ---------------------------------------------------------------- signals
# Each returns None when clean, or a short reason string when it fires.


def sig_no_verdict(html, text):
    """An SSOT page must carry the computed readiness verdict.

    It is the one claim on the page that is a verdict rather than a projection,
    it sits above the tab strip so it cannot be buried, and its absence means the
    build lost the one surface that tells a reader what the page is.
    """
    if "Submission readiness:" not in text:
        return "no computed readiness verdict rendered"
    # ANCHORED. Codex defeated the unanchored form with "READYISH", which matched
    # the READY prefix and passed a verdict that is not one of the three states.
    if not re.search(r"Submission readiness:\s*"
                     r"(READY|NOT READY|NOT YET DETERMINED)(?![A-Za-z])", text):
        return "readiness verdict present but not one of the three computed states"
    return None


def sig_constant_verdict(html, text):
    """The banner must not be the old hardcoded string.

    `NOT SUBMISSION-READY` was a constant that no object state could change -- a
    disclaimer wearing a verdict's clothes. If it reappears, a build has regressed
    to a claim that cannot fail.
    """
    # Only in a BADGE or BANNER slot, not anywhere in prose. Codex defeated the
    # naive form with a page that merely describes the old label historically --
    # "NOT SUBMISSION-READY was the old label" -- which is legitimate text about a
    # fixed defect, not the defect returning. A guard that cannot tell a defect
    # from a description of it will be switched off by whoever writes the history.
    if re.search(r"""class=["'][^"']*(?:badge|banner)[^"']*["'][^>]*>\s*"""
                 r"NOT SUBMISSION-READY", html):
        return "hardcoded NOT SUBMISSION-READY banner is back"
    return None


def sig_empty_panel(html, text):
    """No tab may render empty. D12, as a gate signal.

    A section that exists is a claim that the section is populated; the Paper
    Studio shipped once as a heading over an empty textarea and a reader read the
    whole page as hollow because of it.
    """
    bad = []
    for m in re.finditer(r'<section class="panel" id="(pn-[a-z]+)"(.*?)</section>',
                         html, re.S):
        pid, body = m.group(1), m.group(2)
        t = re.sub(r"<[^>]+>", " ", body)
        t = re.sub(r"\s+", " ", t).strip()
        data = len(re.findall(r"<(?:table|svg|li)[ >/]", body))
        if len(t) < 600 or data < 1:
            bad.append("%s(%dc,%dd)" % (pid, len(t), data))
    return ("empty or stub panel: " + ", ".join(bad)) if bad else None


def sig_no_projection_footer(html, text):
    """The projection claim must be on the page.

    Its absence means the page was not produced by the SSOT generator, or that the
    footer was lost -- either way the reader has no statement of what the numbers
    are derived from.
    """
    return (None if "projected from a single canonical object" in text
            else "projection provenance footer missing")


def sig_placeholder_leak(html, text):
    """Unfilled tokens reaching a reader.

    The corpus has shipped `None`, `n participants` and `{{...}}` before; the
    detector exists because the leak reached 1110 dashboards.
    """
    # VALUE POSITION, not anywhere in the prose. The first cut matched \bNone\b
    # against the stripped text and fired on this page's own caption -- "None of
    # these three is this review's primary result" -- which is the English word
    # opening a sentence, not a leaked Python None. That is the third time today a
    # token guard produced a false positive from naive tokenisation, after the
    # &#x27; entity in the docx check and the 2.5e-05 split in the numeral guard.
    # The fix is the same each time: match where the defect actually appears. A
    # leaked None renders as an ENTIRE cell, or as the whole value after a label,
    # or at the end of a URL. It is never mid-sentence.
    hits = []
    for pat, label in ((r">\s*(?:None|undefined|NaN)\s*<", "bare None/undefined/NaN in a value slot"),
                       (r":\s*(?:None|undefined|NaN)\s*[<\n]", "None/undefined/NaN after a label"),
                       (r"/None\b", "URL ending in /None")):
        if re.search(pat, html):
            hits.append(label)
    for pat, label in ((r"\{\{[^}]+\}\}", "{{token}}"),
                       (r"\bn participants\b", "n participants"),
                       (r"\bNone trials\b", "None trials")):
        if re.search(pat, text):
            hits.append(label)
    return ("placeholder leaked: " + ", ".join(hits)) if hits else None


def sig_unsourced_two_human_claim(html, text):
    """A human-verification claim with no attestation behind it.

    The worst sentence this page could carry. D13, as a gate signal: the claim may
    appear only alongside the submission-tier statement it is computed from.
    """
    claim = re.search(r"check(?:ed)?\s+by\s+two\s+human|two\s+human\s+reviewers", text, re.I)
    if not claim:
        return None
    if "Submission readiness: READY" in text:
        return None
    return ("page claims human duplicate checking while the computed verdict is "
            "not READY")


def sig_k_asserted_settled(html, text):
    """k presented as settled while the object holds undetermined records.

    Two records are behind paywalls; a page that says 'the three trials that
    exist' is wrong in a way a reader cannot detect.
    """
    if re.search(r"the (three|3) trials that exist", text, re.I):
        return "k asserted as settled ('the three trials that exist')"
    return None


SSOT_SIGNALS = {
    "no_verdict": sig_no_verdict,
    "constant_verdict": sig_constant_verdict,
    "empty_panel": sig_empty_panel,
    "no_projection_footer": sig_no_projection_footer,
    "placeholder_leak": sig_placeholder_leak,
    "unsourced_two_human_claim": sig_unsourced_two_human_claim,
    "k_asserted_settled": sig_k_asserted_settled,
}


def run(html, text):
    """Returns {signal: reason} for every signal that fires."""
    out = {}
    for name, fn in SSOT_SIGNALS.items():
        r = fn(html, text)
        if r:
            out[name] = r
    return out
