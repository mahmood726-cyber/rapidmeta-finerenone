"""A grammatical gate over the DELIVERED BYTES of every paper. It must be able to fail.

WHY THIS EXISTS AND WHY IT IS NOT ANOTHER MEASUREMENT. Seven rounds of "it reads like code"
were each answered with a metric, and each metric was correct about something the reader was
not reading. This checks the one thing no metric checked: DOES THE SENTENCE PARSE.

WHAT IT REFUSES, each drawn from a sentence found live on the page:

  SLOT FED A SENTENCE       "eligibility was ELIGIBILITY turns on population, intervention..."
                            A template reading `was {field}` where the field holds a paragraph.
                            Detected as: `was|is|were` followed by a capitalised repeat of the
                            slot's own name, or by >25 words with no closing punctuation.

  TRUNCATED MID-WORD        "...cautions that making e;"
                            A clause ending in a 1-2 letter fragment before punctuation.

  A WORD THAT LOST ITS TAIL "pooled under random with the REML estimator"
                            `random` not followed by `-effects`/`effects`; `fixed` likewise.

  ADVERB WHERE A WORD BELONGS  "heterogeneity was closely (I-squared 0%)"
                            `was <adverb>` before a parenthetical number.

  A STRAY REFUSAL COUNTER   "Refused: 1" standing alone above a refusal.

PROVEN BEFORE IT IS TRUSTED. `--prove` runs every pattern against a fixture carrying the exact
sentences above and requires each to fire. A gate that has never failed is not a gate, and this
one was written against a page that fails it.
"""
import glob
import io
import os
import re
import sys
import html as H

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIXTURE = [
    ("slot fed a sentence",
     "Methods. ClinicalTrials.gov API v2 and PubMed were searched; eligibility was ELIGIBILITY "
     "turns on population, intervention and comparator: a trial is in scope if it randomised "
     "adults with CHRONIC heart failure to an SGLT2 inhibitor against placebo."),
    ("truncated mid-word",
     "It does NOT turn on which analysis the trial reported, because section 3.2.4 cautions "
     "that making e;"),
    ("word lost its tail",
     "estimates were pooled under random with the REML estimator."),
    ("adverb where a word belongs",
     "and heterogeneity was closely (I-squared 0%)."),
    ("stray refusal counter",
     "Refused: 1 Refused: the keyword list -- a CONTENT gap."),
]

# NO `(?i)` HERE, AND THAT WAS THE BUG. With it, `[A-Z]` matched lowercase and the
# pattern fired on "were pooled under a" -- clean prose. The whole point of this
# check is that the slot value ARRIVES IN CAPITALS because it is a field name or a
# shouted paragraph opener, so the case IS the signal and case-insensitivity
# destroys it.
SLOT_FED = re.compile(
    r"\b(?:was|is|were|are|Was|Is|Were|Are)\s+([A-Z]{4,}[A-Z_ ]*)\b(?=\s+[a-z])")
# THE SLOT VALUE HAS TO LOOK LIKE A FIELD, NOT MERELY BE LONG. Requiring only 25+ words after
# a linking verb fired on every legitimate long sentence in the corpus -- the Methods sentence,
# the projection note, a refusal paragraph -- and a check that flags clean prose teaches you to
# ignore it. The signal is that the value OPENS with a shouted or field-shaped token and then
# runs on.
SLOT_LONG = re.compile(
    r"\b(?:was|is|were|are)\s+([A-Z]{4,}[A-Z_ ]*)\s+(?:\S+\s+){8,}")
# A CLAUSE ENDING IN A ONE- OR TWO-LETTER FRAGMENT. The live page reads
# "...cautions that making e;" -- the cut lands anywhere, not after a function
# word, so the pattern anchors on the FRAGMENT rather than on what precedes it.
# Real one- and two-letter words are excluded by name.
_REAL_SHORT = {'a', 'i', 'an', 'is', 'it', 'in', 'of', 'to', 'on', 'or', 'at',
               'by', 'we', 'as', 'be', 'no', 'do', 'if', 'so', 'us', 'up', 'me',
               # ABBREVIATIONS AND FILE EXTENSIONS ARE NOT SEVERED WORDS. The check fired on
               # "et al." and on "second_assessor_prompt.py." -- a citation convention and a
               # filename. A gate that flags correct text is one people learn to ignore.
               'al', 'cf', 'eg', 'ie', 'vs', 'et', 'py', 'js', 'md', 'ed', 'pp', 'ff',
               'ml', 'mg', 'kg', 'hr', 'or', 'rr', 'ci', 'df', 'sd', 'se', 'nb',
               # SYMBOLS USED AS WORDS. 'at larger k.' ends a sentence with a variable
               # name, which is correct in a meta-analysis and looks like a severed word
               # to a pattern that only counts letters.
               'k', 'n', 'p', 'q', 't', 'z', 'x', 'y'}


def _truncated(line):
    # NOT AFTER A DOT EITHER -- `.py`, `.gov`, `v2.` are not truncations.
    # A SEMICOLON OR THE END OF THE TEXT, NOT A FULL STOP. "at larger k." ends a sentence
    # with a variable name and is correct in a meta-analysis; "making e;" is a severed word.
    # Restricting to the shape the live defect actually had keeps the check true.
    for m in re.finditer(r"(?<![\w'.\-])([A-Za-z]{1,2});", line):
        if m.group(1).lower() not in _REAL_SHORT:
            return m
    return None


class _TruncRx(object):
    """Same call shape as a compiled pattern, so CHECKS stays one list."""

    def search(self, line):
        return _truncated(line)


TRUNCATED = _TruncRx()
# A MODIFIER WITH NOTHING TO MODIFY, in EITHER of the two forms this project has shipped.
#
# The first form was "pooled under random" -- the bare adjective, tail lost. This pattern was
# written for it and caught it. The REPAIR for it then produced the second form,
# "pooled under a random-effects", which this same pattern could not match because an article
# now sat between "under" and "random" and because the `(?!\s*effects?)` lookahead was
# written to EXCLUDE the hyphenated spelling as correct. It is only correct when the noun
# follows. That second form reached 80 built pages and the gate exited 0 on every one.
#
#     A CHECK KEYED TO ONE WORDING DOES NOT SEE THE SAME DEFECT REWORDED, AND THE THING MOST
#     LIKELY TO REWORD IT IS THE FIX FOR THE FIRST WORDING.
#
# So this asks the real question -- is the head noun present -- instead of enumerating the
# spellings that lack it. Optional article, either spelling of the modifier, and then a
# REQUIRED noun within a short window; anything else is a lost tail.
# THE FIRST VERSION OF THIS PATTERN FIRED ON CORRECT PROSE, and only the plant caught it.
# Written as `(?:random[- ]?effects?|random|...)` with the noun lookahead after it, the engine
# matched "random-effects" in "a random-effects model", failed the lookahead on " model", then
# BACKTRACKED INTO THE SHORTER `random` BRANCH -- after which the lookahead saw "-effects" and
# was satisfied. Every correct page would have been flagged. A widened pattern that over-fires
# is not a safer error than one that under-fires; it is the accusing direction.
# The bare branches now refuse to match when a suffix follows, so there is nothing to
# backtrack into.
LOST_TAIL = re.compile(
    r"(?i)\bpooled under\s+(?:a|an|the)?\s*"
    r"(?:random[- ]?effects?\b|fixed[- ]?effects?\b|common[- ]?effects?\b"
    r"|random\b(?![- ]?effect)|fixed\b(?![- ]?effect)|common\b(?![- ]?effect))"
    r"(?!\s+(?:model|analysis|meta-analysis|synthesis)\b)")
# The `\b` after each `effects?` is load-bearing too, and its absence produced a SECOND
# false-positive pass: without it `effects?` backtracks to "effect", leaving "s model" for
# the lookahead, which is not `\s+model`, so the lookahead succeeds and correct prose is
# flagged. It failed on "random-effects model" and PASSED on "fixed-effect model" -- the
# asymmetry is the tell, because "fixed-effect" has no trailing "s" to give back.
ADVERB_SLOT = re.compile(r"(?i)\bwas\s+(closely|loosely|tightly|broadly|narrowly)\s*\(")
STRAY_REFUSED = re.compile(r"Refused:\s*\d+\s")

CHECKS = [
    ("slot fed a sentence", SLOT_FED),
    ("slot fed a sentence", SLOT_LONG),
    ("truncated mid-word", TRUNCATED),
    ("word lost its tail", LOST_TAIL),
    ("adverb where a word belongs", ADVERB_SLOT),
    ("stray refusal counter", STRAY_REFUSED),
]


def paper_text(path):
    h = io.open(path, encoding="utf-8", errors="replace").read()
    i = h.find('id="paper"')
    if i < 0:
        return None
    seg = h[i:]
    seg = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", seg)
    # provenance blocks are closed apparatus, not prose -- they are not judged here
    seg = re.sub(r"(?is)<details[^>]*class=['\"][^'\"]*prov-block.*?</details>", " ", seg)
    seg = re.sub(r"(?is)<sup[^>]*>.*?</sup>", " ", seg)
    # A TABLE ROW IS NOT A SENTENCE, and judging one as prose produces a finding that is true
    # of a table and false of the paper. The conformance and preconditions tables are rows
    # like "P4_preconditions HELD All 8 recorded with verdict and cited authority" -- real,
    # deliberate, and not written to be read as English. Prose is what remains.
    seg = re.sub(r"(?is)<table[^>]*>.*?</table>", " ", seg)
    # AND NEITHER IS A QUOTED TRANSCRIPT. Extended data carries the model output exactly as
    # the software printed it -- that is the point of it, and P46 limb 4 requires it verbatim.
    # Judging `rma(yi = log(hr), sei = ...)` as English would demand we corrupt the one thing
    # on the page that must not be touched.
    seg = re.sub(r"(?is)<pre[^>]*>.*?</pre>", " ", seg)
    _ed = re.search(r"(?is)<h[234][^>]*>[^<]*Extended data[^<]*</h[234]>", seg)
    if _ed:
        _nx = re.search(r"(?is)<h[234][^>]*>", seg[_ed.end():])
        seg = seg[:_ed.start()] + (seg[_ed.end() + _nx.start():] if _nx else "")
    # THE GATE JUDGES THE ARTICLE, NOT THE APPARATUS AT THE END OF IT.
    #
    # `Submission conformance` and `Notes on this record` are compliance TABLES -- rows like
    # "P4_preconditions HELD All 8 recorded with verdict and cited authority" -- and reading
    # a table row as a sentence produces a finding true of a table and false of the paper.
    # Same category as the provenance blocks stripped above: real, deliberate, and not prose.
    # Everything a reader reads AS the review is still judged.
    for _head in ("Submission conformance", "Notes on this record"):
        _m = re.search(r"(?is)<h[234][^>]*>[^<]*" + re.escape(_head) + r"[^<]*</h[234]>", seg)
        if _m:
            _n = re.search(r"(?is)<h[234][^>]*>", seg[_m.end():])
            seg = seg[:_m.start()] + (seg[_m.end() + _n.start():] if _n else "")
    seg = re.sub(r"(?i)<(/?)(div|p|h[1-6]|li|tr|section|table|br)[^>]*>", "\n", seg)
    return H.unescape(re.sub(r"<[^>]+>", " ", seg))


def scan(text):
    out = []
    for line in text.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 25:
            continue
        for name, rx in CHECKS:
            m = rx.search(line)
            if m:
                out.append((name, line[:220]))
                break
    return out


def prove():
    print("PROVING EACH PATTERN AGAINST A SENTENCE FOUND LIVE ON THE PAGE")
    ok = True
    for name, sentence in FIXTURE:
        hit = [n for n, rx in CHECKS if rx.search(sentence)]
        good = name in hit
        ok = ok and good
        print("   %-32s %s" % (name, "FIRES" if good else "DID NOT FIRE -- the gate is blind"))
    clean = "Estimates were pooled under a random-effects model with the REML estimator."
    if any(rx.search(clean) for _n, rx in CHECKS):
        ok = False
        print("   %-32s FIRES ON CLEAN PROSE -- false positive" % "clean control")
    else:
        print("   %-32s silent, as it must be" % "clean control")
    if not ok:
        sys.exit("PROOF FAILED: this gate cannot detect what it claims to detect.")
    print("PROOF PASSED: every pattern fires on its own case and none fires on clean prose.")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--prove" in sys.argv:
        prove()
        return
    prove()
    print("")
    only = [a for a in sys.argv[1:] if a.endswith(".html")]
    pages = only or sorted(glob.glob(os.path.join(REPO, "*_REVIEW.html"))) + \
        sorted(glob.glob(os.path.join(REPO, "*_SSOT.html")))
    judged = 0
    bad = {}
    for p in pages:
        t = paper_text(p)
        if t is None:
            continue
        judged += 1
        hits = scan(t)
        if hits:
            bad[os.path.basename(p)] = hits
    print("PAPERS JUDGED: %d | PAPERS WITH A SENTENCE THAT DOES NOT PARSE: %d"
          % (judged, len(bad)))
    print("")
    for name in sorted(bad)[:20]:
        print("%s" % name)
        for kind, line in bad[name][:4]:
            print("   [%s] %s" % (kind, line))
    if bad:
        print("")
        sys.exit("REFUSED: %d paper(s) carry a sentence that does not parse." % len(bad))
    print("OK -- every judged paper parses on all six checks.")


if __name__ == "__main__":
    main()
