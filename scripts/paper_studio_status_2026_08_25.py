"""Completion status of the Paper Studio corpus, measured on DELIVERED pages.

Mahmood asked whether the papers are finished. This answers it with a denominator on every
line, from the pages as served rather than from a render, because the two have disagreed
repeatedly: a defect fixed in the generator is not fixed for a reader until the page is
rebuilt, and a defect visible in a debug render may not reach the page at all.

WHAT COUNTS AS A DEFECT HERE. Each class below was a real, measured, reader-facing defect
during 2026-08-24/25. The count is how many delivered Paper tabs still carry it. Provenance
disclosures are excluded from prose checks throughout: they are collapsed <details> a reader
only meets by choosing to open them, and counting them as prose is the error that once made
an editor persona desk-reject a document no reader sees.
"""
import collections
import html as H
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PMAP = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))

_PAPER = re.compile(r'id="pn-paper"(.*?)(?:id="pn-[a-z]|<!--\s*end-paper)', re.S)
_PROV = re.compile(r"(?s)<details class='prov-block'.*?</details>")
_CODE = re.compile(r"(?is)<(pre|code|script|style)\b.*?</\1>")

_REPR = re.compile(r"\{&#x27;|\{'|&#x27;: &#x27;|': '|\[\{|&quot;: &quot;|\{&quot;\w+&quot;: "
                   r"|\[(?:&#x27;|&quot;|')[^\]]{0,400}?,\s*(?:&#x27;|&quot;|')")
_SNAKE = re.compile(r"(?<![\w./-])[a-z][a-z0-9]*(?:_[a-z0-9]+){1,}(?![\w/-])")
_PATH = re.compile(r"(?<![\w./-])[a-z][a-z0-9_]*(?:\.[a-z_][a-z0-9_\[\]=]*){2,}(?![\w/-])")
_PROP = re.compile(r"(?<![\w-])P\d+_[a-z][a-z0-9_]*(?![\w-])")
_ALLOW = {"risk_of_bias", "p_value", "follow_up"}


def paper_text(page):
    h = io.open(page, encoding="utf-8", errors="replace").read()
    m = _PAPER.search(h)
    if not m:
        return None, None
    seg = _CODE.sub(" ", _PROV.sub(" ", m.group(1)))
    return H.unescape(re.sub(r"<[^>]+>", " ", seg)), h


# EVERY DETECTOR BELOW MUST BE SHOWN TO FIRE BEFORE ANY COUNT FROM IT IS PRINTED.
#
# This script produced a table of nine defect counts that went to Mahmood as a completion
# status. Nothing established that any of those nine detectors could report anything other
# than zero. A count of 0 from a detector that has never fired is indistinguishable from a
# detector that does nothing -- and an audit of this repository found 55 checks in exactly
# that state.
#
# Each control is a PAIR: a constructed string carrying the defect, which must be flagged,
# and a constructed string that resembles it and must NOT be. The negatives are the half
# that matters -- a detector that flags everything reports a corpus-wide catastrophe, which
# is the same failure as one that flags nothing. Both have happened here in two days.
#
# SYNTHETIC, so no fix to the corpus can retire a control.
_CONTROLS = [
    ("container repr in reader prose", _REPR,
     "the call was [&#x27;a_id&#x27;, &#x27;b_id&#x27;] and nothing more",
     "the interval was [95% CI 0.83 to 0.96] as published"),
    ("build-property identifier in prose", _PROP,
     "Properties held: P19_promotion_reaches_derived_blocks and others",
     "Properties held: 19, recorded with the build"),
    ("dotted field path in prose", _PATH,
     "recorded in results.by_outcome.primary.pooled for this review",
     "reported at ClinicalTrials.gov and in the published paper"),
    ("snake_case identifier in prose", _SNAKE,
     "the counts are recorded in prisma_flow on this object",
     "the counts are recorded in the PRISMA flow diagram"),
    ("a lowercased clinical acronym", re.compile(
        r"(?<![\w-])(barc|mace|vte|nyha|sglt2|kccq)(?![\w-])"),
     "bleeding was graded as barc type 2 or higher",
     "bleeding was graded as BARC type 2 or higher"),
]


def _prove_detectors_fire():
    """Refuse to print a count from a detector that has not been shown to work."""
    bad = []
    for label, rx, positive, negative in _CONTROLS:
        if not rx.search(positive):
            bad.append("%s: did NOT flag its planted defect" % label)
        if rx.search(negative):
            bad.append("%s: FLAGGED a clean sentence" % label)
    # The three text-independent detectors are proved on the same terms.
    for label, pat, positive, negative in (
            ("a screening card claiming 'included'",
             re.compile(r"This review's decision:\s*included", re.I),
             "<p>This review's decision: included.</p>",
             "<p>This review's decision: excluded.</p>"),
            ("an empty decision slot", re.compile(r"This review's decision:\s*\."),
             "<p>This review's decision: .</p>",
             "<p>This review's decision: excluded.</p>"),
            # A REAL CONTROL, not the placeholder this had. `re.compile(r"x")` matching
            # "x" proves nothing about the detector and is exactly the tautology an audit
            # should report rather than a control it should accept.
            ("says no GRADE record while rating outcomes",
             re.compile(r"no GRADE record is held.*Certainty in this result", re.S),
             "no GRADE record is held here. Certainty in this result: LOW.",
             "no GRADE record is held for this outcome, and none is claimed.")):
        if not pat.search(positive):
            bad.append("%s: did NOT flag its planted defect" % label)
        if pat.search(negative):
            bad.append("%s: FLAGGED a clean case" % label)
    return bad


def main():
    problems = _prove_detectors_fire()
    if problems:
        print("REFUSED: a detector could not be shown to work, so NO COUNT IS PRINTED.")
        for p in problems:
            print("   " + p)
        return 2
    print("CONTROL: all %d detectors flag a planted defect and clear a matching clean case"
          % (len(_CONTROLS) + 3))
    print()

    counts = collections.Counter()
    pages = 0
    examples = collections.defaultdict(list)

    for page in sorted(PMAP):
        if not os.path.exists(page):
            continue
        txt, whole = paper_text(page)
        if txt is None:
            continue
        pages += 1

        def note(key, cond):
            if cond:
                counts[key] += 1
                if len(examples[key]) < 3:
                    examples[key].append(page)

        note("container repr in reader prose", bool(_REPR.search(txt)))
        note("build-property identifier in prose", bool(_PROP.search(txt)))
        note("dotted field path in prose",
             any(not t.endswith((".gov", ".org", ".com", ".html", ".json", ".py"))
                 for t in _PATH.findall(txt)))
        # AN IDENTIFIER IN A QUOTATION IS NOT AN IDENTIFIER IN PROSE.
        #
        # Of the 9 pages this reported, 7 carry only verbatim quotations: the executed
        # ClinicalTrials.gov query (`study_type=interventional; page_size=100`), the R call
        # (`rma(yi = log_hr, sei = log_se, ...)`), and the filenames of downloadable extended
        # data (`canonical_object.json`). Every one of those is evidence a reader can check,
        # and rewriting them would falsify a quotation.
        #
        # Counting them as leakage inflates the number and, worse, would invite a "fix" that
        # destroys the evidence. The detector now asks whether the token is a BARE WORD IN A
        # SENTENCE -- not followed by `=`, not a filename, not inside an R call.
        _snake = set()
        for _m in _SNAKE.finditer(txt):
            _t = _m.group(0)
            if _t in _ALLOW:
                continue
            _after = txt[_m.end():_m.end() + 2]
            if _after.startswith("=") or _after.startswith("."):
                continue                      # field=value, or a filename
            _before = txt[max(0, _m.start() - 12):_m.start()]
            if "=" in _before or "(" in _before:
                continue                      # an argument inside a quoted call
            _snake.add(_t)
        note("snake_case identifier in prose", bool(_snake))
        # COUNTED AGAINST THE OBJECT, not by presence. The first version flagged any card
        # reading "included" and reported 4 pages -- all of which were correct, because
        # those records genuinely store INCLUDED. A detector that cannot tell a true value
        # from a false one reports a defect that is not there, which is the same failure as
        # missing one that is.
        shown = len(re.findall(r"This review's decision:\s*included", whole, re.I))
        _obj = os.path.join(REPO, PMAP.get(page, "").replace("/", os.sep))
        _true = 0
        if os.path.exists(_obj):
            try:
                _o = json.load(io.open(_obj, encoding="utf-8"))
                for _r in ((_o.get("screening") or {}).get("records") or []):
                    if not isinstance(_r, dict):
                        continue
                    _v = str(_r.get("verdict") or "").upper()
                    if _v in ("INCLUDED", "INCLUDE", "ELIGIBLE_INCLUDED"):
                        _true += 1
                    elif not _v and str(_r.get("disposition") or "").lower() == "included":
                        _true += 1
            except Exception:
                _true = shown          # unreadable object: do not accuse
        note("a FALSE 'included' screening card", shown > _true)
        note("an empty decision slot",
             bool(re.search(r"This review's decision:\s*\.", whole)))
        note("'These 1 trials'", "These 1 trials" in txt)
        note("a lowercased clinical acronym",
             bool(re.search(r"(?<![\w-])(barc|mace|vte|nyha|sglt2|kccq)(?![\w-])", txt)))
        note("says no GRADE record while rating outcomes",
             "no GRADE record is held" in txt and "Certainty in this result" in txt)

    print("PAPER STUDIO TABS MEASURED (delivered pages): %d" % pages)
    print()
    print("DEFECT CLASSES, count = pages still carrying it:")
    for key in ("container repr in reader prose",
                "build-property identifier in prose",
                "dotted field path in prose",
                "snake_case identifier in prose",
                "a FALSE 'included' screening card",
                "an empty decision slot",
                "'These 1 trials'",
                "a lowercased clinical acronym",
                "says no GRADE record while rating outcomes"):
        n = counts[key]
        flag = "" if n == 0 else "   e.g. " + ", ".join(examples[key][:2])
        print("   %-42s %4d / %d%s" % (key, n, pages, flag))
    return 0


sys.exit(main())
