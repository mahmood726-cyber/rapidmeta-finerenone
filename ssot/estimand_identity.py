"""Are two outcome definitions the SAME QUANTITY? Three answers, and one of them is "ask a human".

WHY A SEPARATE MODULE FROM text_match.

Detector 2 correctly forced the estimand assessor off raw string equality. Routing it
through `text_match` then MOVED the error to a place where it looked solved:

    "Intent-to-Treat (ITT) Analysis" vs "ITT Analysis"
        -> the SAME quantity in different words. text_match says DIFFERENT. Wrong.

    "Fasting LDL-C" vs "LDL-C"
        -> whether these are one quantity is a METHODOLOGICAL JUDGEMENT, not a string
           question. text_match says DIFFERENT. That is not wrong so much as unearned.

    "percent change in LDL-C at week 12" vs "... at week 52"
        -> nearly identical words, genuinely different quantities.

A normaliser cannot separate these, and reporting an UNDECIDABLE comparison as a FAIL
would put a false defect claim on a live page -- the same class as every other mistake
tonight, in the position where it does the most damage.

SO: enumerate what is safe, refuse what is not, and NEVER interpolate between them.
DIFFERENT is asserted only when a DECLARED DISCRIMINATOR can be named. Everything else
that is not an exact match after declared synonyms is UNDECIDABLE and goes to a human
with the question stated.
"""

import re

SAME = "SAME"
DIFFERENT = "DIFFERENT"
UNDECIDABLE = "UNDECIDABLE"

VERSION = "estimand-identity-v1 (2026-08-18)"

# ---------------------------------------------------------------------------
# SAFE, ENUMERABLE EQUIVALENCES. A reader can inspect and disagree with every row.
# Nothing is inferred; if an abbreviation is not on this list it does not expand.
# ---------------------------------------------------------------------------
SYNONYMS = [
    ("itt", "intent to treat"),
    ("intention to treat", "intent to treat"),
    ("cv", "cardiovascular"),
    ("ldl c", "ldl cholesterol"),
    ("ldl", "ldl cholesterol"),
    ("hdl c", "hdl cholesterol"),
    ("6mwd", "six minute walk distance"),
    ("6 minute walk distance", "six minute walk distance"),
    ("kccq", "kansas city cardiomyopathy questionnaire"),
    ("mace", "major adverse cardiovascular events"),
    ("isth", "international society on thrombosis and haemostasis"),
    ("international society on thrombosis and hemostasis",
     "international society on thrombosis and haemostasis"),
    ("hf", "heart failure"),
    ("all cause mortality", "death from any cause"),
]

# ---------------------------------------------------------------------------
# DECLARED DISCRIMINATORS. Only these license an assertion of DIFFERENT.
# ---------------------------------------------------------------------------

# Two definitions naming different timepoints are different quantities.
_TIMEPOINT = re.compile(r"\b(?:week|month|day|year)s?\s*(\d+)\b", re.I)

# Named quantity families. Definitions whose family SETS differ are different quantities.
# A family is only listed where the distinction is not a matter of judgement.
FAMILIES = {
    "bleeding": ("bleed", "haemorrhag", "hemorrhag"),
    "stroke_or_embolism": ("stroke", "systemic embolism", "embolic"),
    "mortality": ("mortality", "death", "died"),
    "hospitalisation": ("hospitali", "admission"),
    "ldl": ("ldl",),
    # 6MWT was missing here and ATTRibute-CM's hierarchy carries it. The module returned
    # UNDECIDABLE rather than SAME, so it published nothing false -- but an incomplete
    # family list makes a real difference invisible, which is the quieter half of the same
    # error. Missing keys fail toward silence, not toward a wrong claim, and that is the
    # only reason this was survivable.
    "walk_distance": ("walk distance", "6mwd", "6mwt", "six minute walk", "6 minute walk"),
    "biomarker": ("nt probnp", "ntprobnp", "bnp", "troponin", "hba1c"),
    "quality_of_life": ("kccq", "quality of life", "questionnaire"),
    "thrombosis": ("thrombos", "thromboembol", "dvt", "pulmonary embolism"),
    "blood_pressure": ("blood pressure", "systolic", "diastolic"),
}

_PAREN = re.compile(r"\([^)]*\)")
_PUNCT = re.compile(r"[^\w\s]")
_WS = re.compile(r"\s+")


def _norm(s):
    s = _PAREN.sub(" ", str(s or "").lower())
    s = _PUNCT.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    for a, b in SYNONYMS:                       # declared expansions only
        s = re.sub(r"\b%s\b" % re.escape(a), b, s)
    return _WS.sub(" ", s).strip()


def _families(s):
    return {name for name, keys in FAMILIES.items() if any(k in s for k in keys)}


def _timepoints(s):
    return set(_TIMEPOINT.findall(s))


def compare(a, b):
    """Return (verdict, reason). DIFFERENT only when a discriminator can be NAMED."""
    na, nb = _norm(a), _norm(b)
    if na == nb:
        return SAME, "identical after declared synonym expansion"

    ta, tb = _timepoints(na), _timepoints(nb)
    if ta and tb and ta != tb:
        return DIFFERENT, f"different timepoints: {sorted(ta)} vs {sorted(tb)}"

    fa, fb = _families(na), _families(nb)
    if fa and fb and fa != fb:
        only_a, only_b = sorted(fa - fb), sorted(fb - fa)
        return DIFFERENT, (f"different quantity families: {sorted(fa)} vs {sorted(fb)}"
                           + (f"; only in first: {only_a}" if only_a else "")
                           + (f"; only in second: {only_b}" if only_b else ""))

    return UNDECIDABLE, (
        f"no declared discriminator separates these, and they are not identical after "
        f"synonym expansion. THIS IS A METHODOLOGICAL JUDGEMENT, not a string question: "
        f"are {a!r} and {b!r} the same quantity? Asserting a difference here would put an "
        f"unearned defect claim on a page.")


def compare_all(defs):
    """defs = [(key, definition)]. Returns (verdict, reason, per-pair detail)."""
    if len(defs) < 2:
        return UNDECIDABLE, "fewer than two definitions to compare", []
    first_key, first = defs[0]
    detail, worst = [], SAME
    for k, d in defs[1:]:
        v, why = compare(first, d)
        detail.append((k, v, why))
        if v == DIFFERENT:
            worst = DIFFERENT
        elif v == UNDECIDABLE and worst != DIFFERENT:
            worst = UNDECIDABLE
    if worst == SAME:
        return SAME, f"all {len(defs)} definitions are one quantity ({VERSION})", detail
    if worst == DIFFERENT:
        named = [f"{k}: {why}" for k, v, why in detail if v == DIFFERENT]
        return DIFFERENT, "; ".join(named[:3]), detail
    und = [k for k, v, _ in detail if v == UNDECIDABLE]
    return UNDECIDABLE, f"undecidable against {first_key}: {und[:4]} -- needs a human", detail
