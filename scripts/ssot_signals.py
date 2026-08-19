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
    # A REDIRECT STUB IS A STUB BY CONSTRUCTION (added 2026-08-16).
    # Checked FIRST and on structure, not on wording. A page carrying a meta
    # refresh exists to send the reader elsewhere; it has no analysis, so the SSOT
    # signals -- readiness verdict, projection footer -- cannot apply to it and
    # firing them only blocks a legitimate consolidation.
    #
    # Found when SOTAGLIFLOZIN_HF_AUTO_FULL was consolidated into a stub pointing at
    # the canonical page. The stub was classified SSOT and blocked, because its own
    # EXPLANATORY PROSE contains the phrase "canonical object" and the branch below
    # matches that phrase on any script-free page. The pre-existing STUB branch
    # missed it because that branch keys on the phrase "opening the full".
    #
    # Two phrase-matching rules disagreeing about a 1.6 KB redirect is the argument
    # for structure over vocabulary: the honest fix is to detect the refresh, not to
    # reword the page until the classifier is satisfied. Rewording to dodge a gate
    # leaves the gate wrong and the next stub blocked.
    if re.search(r'<meta[^>]+http-equiv=["\']?refresh', html, re.I):
        return "STUB"
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
                     r"(READY|NOT READY|NOT YET DETERMINED)(?![-\w])", text):
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
    if re.search(r"""class=["'][^"']*\b(?:badge|banner)\b[^"']*["'][^>]*>(?:\s|<[^>]+>)*"""
                 r"NOT SUBMISSION-READY", html):
        return "hardcoded NOT SUBMISSION-READY banner is back"
    return None


# A DECLARED ABSENCE IS NOT AN EMPTY PANEL, and the difference is the whole of
# what the standard asks for. Property 1 reads: "Eight-tab shell, NO EMPTY TAB;
# ABSENT SECTIONS RENDER AN HONEST STATE NAMING WHAT IS MISSING AND WHY."
#
# The check below could not tell those two apart. It measured length and counted
# tables, so a panel reading "Not held in this object. No search strategy was
# recoverable from the published page this object was extracted from, so no
# query, date or yield can be shown" scored 156 characters and zero tables and
# was reported as a stub -- the same verdict as a heading over an empty textarea,
# which is the defect it was built for.
#
# That is a check reporting something other than what it measures, and it fails
# toward ALARM: it convicts the pages that did the honest thing. Left alone it
# teaches whoever meets it to pad honest states with filler until they clear 600
# characters, which is strictly worse for a reader than the terse truth.
#
# THE COMFORTABLE DIRECTION IS AVAILABLE HERE AND IS CLOSED DELIBERATELY. If the
# mere PRESENCE of an absent-state element excused a panel, any hollow tab could
# be silenced by emitting an empty one. So the exemption requires the absent
# state to CARRY ITS REASON: at least MIN_REASON characters of text inside the
# absent-state element itself. An empty or one-word absent-state does not exempt
# anything and the panel is still reported.
MIN_REASON = 60
ABSENT_STATE = re.compile(
    r"<(\w+)[^>]*class=['\"][^'\"]*absent-state[^'\"]*['\"][^>]*>(.*?)</\1\s*>",
    re.S | re.I)


def _declared_absent(body):
    """(True, chars) when this panel states its own absence and says why."""
    best = 0
    for m in ABSENT_STATE.finditer(body):
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        best = max(best, len(t))
    return best >= MIN_REASON, best


def sig_empty_panel(html, text):
    """No tab may render empty. D12, as a gate signal.

    A section that exists is a claim that the section is populated; the Paper
    Studio shipped once as a heading over an empty textarea and a reader read the
    whole page as hollow because of it.

    A panel that DECLARES its absence and gives the reason is not that defect --
    it is the property being met. See MIN_REASON above for the bar it must clear
    and why the bar exists.
    """
    bad = []
    # Attribute order. `<section id=... class="panel">` is the same element and
    # slipped past a pattern that assumed class came first.
    for m in re.finditer(r'<section\b(?=[^>]*class="[^"]*panel)'
                         r'(?=[^>]*id="(pn-[a-z]+)")[^>]*>(.*?)</section>',
                         html, re.S):
        pid, body = m.group(1), m.group(2)
        t = re.sub(r"<[^>]+>", " ", body)
        t = re.sub(r"\s+", " ", t).strip()
        data = len(re.findall(r"<(?:table|svg|li)[ >/]", body))
        if len(t) < 600 or data < 1:
            declared, n = _declared_absent(body)
            if declared:
                continue
            bad.append("%s(%dc,%dd,absent-state reason %dc)" % (pid, len(t), data, n))
    return ("empty or stub panel: " + ", ".join(bad)) if bad else None


def sig_no_projection_footer(html, text):
    """The projection claim must be on the page.

    Its absence means the page was not produced by the SSOT generator, or that the
    footer was lost -- either way the reader has no statement of what the numbers
    are derived from.
    """
    # A NEGATED sentence contains the phrase, so "this page is NOT projected
    # from a single canonical object" satisfied the check that exists to
    # confirm the opposite.
    if re.search(r"\b(?:not|never|isn.t)\s+projected from a single canonical "
                 r"object", text, re.I):
        return "page DENIES the projection claim this footer should make"
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
    for pat, label in ((r">\s*(?:None|undefined|NaN)\s*[.,;:!?]?\s*<", "bare None/undefined/NaN in a value slot"),
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
    # A MENTION IS NOT A CLAIM, AND THIS IS THE THIRD TIME IN THIS FILE. The docstring above
    # already records two: "Submission readiness: READYISH" containing "READY", and `\bNone\b`
    # matching the English word mid-sentence. The third is a page that DENIES the claim:
    #
    #   "The two independent screens were performed by two MODEL FAMILIES, NOT BY TWO PEOPLE.
    #    A reader of 'screened in duplicate' would ordinarily assume TWO HUMAN REVIEWERS, so
    #    this field says what was actually done."
    #
    # That sentence exists to prevent exactly the misreading this signal guards against, and
    # the signal fired on it. A guard that blocks the disclaimer while passing the assertion is
    # inverted. Scoped to the sentence containing the match, a nearby denial means the page is
    # DISOWNING human duplicate checking, not asserting it.
    seg = text[max(0, claim.start() - 300):claim.end() + 200]
    if re.search(r"not\s+by\s+two\s+people|not\s+two\s+human|rather\s+than\s+by\s+two|"
                 r"would\s+ordinarily\s+assume|model\s+famil|not\s+performed\s+by\s+two",
                 seg, re.I):
        return None
    # Substring, not state. "Submission readiness: READYISH" contains
    # "Submission readiness: READY" and silenced the worst claim the page
    # can carry. Anchored to the exact state.
    if re.search(r"Submission readiness:\s*READY(?![-\w])", text):
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
