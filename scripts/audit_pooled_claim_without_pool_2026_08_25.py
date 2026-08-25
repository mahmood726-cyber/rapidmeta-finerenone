"""An abstract that reports agreement between trials the page refuses to pool.

FOUND BY THE STUDENT PERSONA, NOT BY US. Across the corpus panel the same
contradiction came back on page after page: the abstract says

    "The trials agreed closely (I-squared 0%)"

while the body of the same page says the trials are not pooled, or that zero
pooled outcomes were rated. The student flagged it as the worst thing a novice
can be handed -- a confident sentence they would not question, sitting on top of
an analysis that does not exist.

THE PANEL NAMED FIVE. THAT IS REVIEWER REACH, NOT A POPULATION. The panel read
107 pages and flagged whichever contradiction it happened to quote; a page can
carry this defect and be flagged for something else instead. So this measures
every page, and reports the count against the corpus denominator.

WHAT COUNTS AS THE DEFECT, and it is deliberately narrow:

  a heterogeneity/agreement sentence in the ABSTRACT
  AND a statement anywhere on the page that there is no pooled result

A FIRST VERSION OF THIS COUNTED 38 AND 19 OF THEM WERE NOT DEFECTS. It matched
any abstract carrying an I-squared anywhere against any page saying 'not pooled'
anywhere. But most pages do BOTH legitimately: they pool outcome X and report its
heterogeneity, and separately decline to pool outcome Y and say so. The abstract
sentence 'RR 0.87 (0.79 to 0.95) across 2 trials; the trials agreed closely' is a
correct report of a pool that exists. What misleads is the BARE form -- an
agreement statistic with NO estimate attached to it -- on a page that pools
nothing. So the discriminator is whether the agreement claim carries its own
point estimate, and the negative controls now include the legitimate shape.

Either alone is fine. An abstract may report I-squared for a real pool; a page
may legitimately decline to pool and say so. It is the CONJUNCTION that misleads,
because the reader meets the abstract first and has no reason to read on.

A CONTROL RUNS BEFORE ANY COUNT IS BELIEVED. The instrument is handed a page
built to contain the defect and a page built without it, and must separate them.
A detector that cannot fail cannot be trusted to report zero.
"""
import io
import json
import os
import re
import subprocess
import sys

import instrument_controls

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The projector writes agreement in words, with the statistic in brackets. Match the
# statistic, not the adjective, so a reworded adjective does not slip past.
AGREED = re.compile(r"I-squared\s*[0-9]", re.I)

# The page saying, in any of the forms the projector uses, that nothing was pooled.
NO_POOL = [
    re.compile(r"are not pooled", re.I),
    re.compile(r"no pooled estimate", re.I),
    re.compile(r"0 pooled outcome", re.I),
    re.compile(r"no combined result", re.I),
    re.compile(r"nothing yet to pool", re.I),
    re.compile(r"there is no pooled", re.I),
]

# A pooled point estimate: a ratio or difference with a confidence interval beside it.
#
# THIS PATTERN HAS NOW BEEN WRONG TWICE, BOTH TIMES INFLATING THE COUNT.
#   * It listed the ratio measures and omitted "mean difference", which is what every
#     continuous outcome in this corpus reports -- LDL-C, blood pressure, triglycerides.
#   * It required the interval to open on a digit. Continuous outcomes LOWER things, so
#     their intervals open on a minus: "mean difference -5.69 (-7.3 to -4.08)".
# Seven pages were reported as claiming agreement without a pool while their abstracts
# reported a pooled mean difference in the same sentence. The pages were right and the
# instrument was wrong -- the third over-flagging of the week -- so both shapes are now
# negative controls rather than a comment.
ESTIMATE = re.compile(
    r"(?:RR|OR|HR|RD|SMD|MD|risk ratio|odds ratio|hazard ratio|mean difference|"
    r"risk difference|rate ratio)"
    r"[^.;]{0,60}-?[0-9]+(?:[.][0-9]+)?[^.;]{0,60}[(]\s*-?[0-9]", re.I)

# The page disowning the pool at the point it gives the statistic.
DISOWNED = re.compile(r"withdrawn|is not an estimate|retracted|already said so", re.I)

PAPER = re.compile(r'id="pn-paper"(.*?)(?:id="pn-[a-z]|<!--\s*end-paper)', re.S)
ABSTRACT = re.compile(r"(?is)>\s*Abstract\s*<.{0,24000}")


def text_of(html_fragment):
    seg = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html_fragment)
    seg = re.sub(r"<[^>]+>", " ", seg)
    return re.sub(r"\s+", " ", seg)


def examine(html):
    """Return (has_defect, quoted_agreement, quoted_refusal) for one page's paper panel."""
    m = PAPER.search(html)
    if not m:
        return None, "", ""
    panel = m.group(1)
    whole = text_of(panel)
    am = ABSTRACT.search(panel)
    abstract = text_of(am.group(0)) if am else whole[:6000]

    ag = AGREED.search(abstract)
    if not ag:
        return False, "", ""
    # THE DISCRIMINATOR. An agreement statistic that arrives WITH a point estimate is
    # reporting a pool that exists. A bare one is a statistic about nothing.
    window = abstract[max(0, ag.start() - 300):ag.end() + 60]
    if ESTIMATE.search(window):
        return False, "", ""
    # AN I-SQUARED CITED AS THE REASON THERE IS NO POOL IS THE OPPOSITE OF THIS DEFECT.
    # ACS_ANTIPLATELET gives four numbered reasons for withdrawing its combination, and the
    # fourth is "the heterogeneity already said so: i-squared 91.0%". That is the statistic
    # doing exactly the work it should. The defect is a BARE agreement claim standing where
    # a result belongs; a disclaimed one is a justification. Exempt only where the page
    # disowns the pool AT the statistic, within the same passage.
    if DISOWNED.search(abstract[max(0, ag.start() - 500):ag.end() + 500]):
        return False, "", ""
    for pat in NO_POOL:
        rm = pat.search(whole)
        if rm:
            i = max(0, ag.start() - 90)
            j = max(0, rm.start() - 70)
            return True, abstract[i:ag.start() + 40].strip(), whole[j:rm.end() + 50].strip()
    return False, "", ""


PRE_FIX = "fa7ef6686"          # the last commit before the projector suppression landed


def control():
    """Refuse to report anything unless the known answers come back known.

    THE POSITIVE IS A REAL PAGE, NOT A SYNTHETIC ONE. After the projector fix no page in
    the worktree carries this defect, so a planted-only control would be an instrument
    proving it agrees with itself. FINERENONE_REVIEW.html AS COMMITTED AT %s does carry
    it, and its answer was established independently -- the student persona quoted the
    sentence before any of this code existed. That page is permanent in git history, so
    this control cannot retire itself the way the last one did.

    The negative is the shape that actually fooled this instrument: a pooled MEAN
    DIFFERENCE with a negative lower limit, beside a page that declines to pool something
    else. Seven pages were accused on that shape.
    """ % PRE_FIX
    r = subprocess.run(["git", "show", "%s:FINERENONE_REVIEW.html" % PRE_FIX],
                       capture_output=True, cwd=REPO)
    if r.returncode != 0:
        raise instrument_controls.ControlFailed(
            "REFUSED: the control page %s:FINERENONE_REVIEW.html could not be read, so the "
            "positive control could not run. An instrument whose positive control did not "
            "execute is not a checked instrument. NO COUNT IS PRINTED." % PRE_FIX)
    real_positive = examine(r.stdout.decode("utf-8", "replace"))[0]

    neg_real = ('<div id="pn-paper"><h2>Abstract</h2><p>MmHg change from baseline in systolic '
                'blood pressure: mean difference -5.69 (-7.3 to -4.08) across 2 trials; the '
                'trials agreed closely (I-squared 0%).</p>'
                '<p>0 pooled outcome(s) were rated.</p></div><div id="pn-other">')

    instrument_controls.require_controls(
        "pooled-claim-without-pool",
        ("FINERENONE_REVIEW.html at %s, the page the student quoted" % PRE_FIX,
         real_positive, True),
        ("a pooled mean difference with a negative lower limit beside a declined outcome",
         examine(neg_real)[0], True))

    # The remaining shapes this instrument has been wrong about, each kept because each one
    # cost a false accusation. A failure here raises for the same reason as the two above.
    others = {
        "an abstract that pools and reports the heterogeneity of what it pooled":
            ('<div id="pn-paper"><h2>Abstract</h2><p>The trials agreed closely '
             '(I-squared 0%).</p><p>The pooled estimate is 0.81.</p></div>'
             '<div id="pn-other">'),
        "a page that reports no estimate and says so, with no agreement claim":
            ('<div id="pn-paper"><h2>Abstract</h2><p>No estimate is reported.</p>'
             '<p>These 4 trials are not pooled.</p></div><div id="pn-other">'),
        "a pooled ratio beside a different outcome that was declined":
            ('<div id="pn-paper"><h2>Abstract</h2><p>Time to death from any cause, as a '
             'hazard ratio: 0.978 (0.752 to 1.27) across 2 trials; the trials agreed '
             'closely (I-squared 0%).</p><p>No pooled estimate was produced for this '
             'outcome.</p></div><div id="pn-other">'),
        "an i2 cited as the REASON a pool was withdrawn":
            ('<div id="pn-paper"><h2>Abstract</h2><p>(4) the heterogeneity already said so: '
             'I-squared 91.0%. Withdrawn: the displayed value is not an estimate.</p>'
             '<p>These 4 trials are not pooled.</p></div><div id="pn-other">'),
    }
    for label, page in sorted(others.items()):
        if examine(page)[0]:
            raise instrument_controls.ControlFailed(
                "REFUSED: pooled-claim-without-pool FLAGS THE CASE IT MUST NOT -- %s. "
                "Accusing in the wrong direction is what this instrument has already done "
                "twice. NO COUNT IS PRINTED." % label)
        print("CONTROL (negative) pooled-claim-without-pool: %s -> clean" % label)
    return True


def main():
    control()          # raises ControlFailed before any count is printed
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    hits, examined, nopanel = [], 0, 0
    for page in sorted(pmap):
        p = os.path.join(REPO, page)
        if not os.path.exists(p):
            continue
        html = io.open(p, encoding="utf-8", errors="replace").read()
        bad, a, b = examine(html)
        if bad is None:
            nopanel += 1
            continue
        examined += 1
        if bad:
            hits.append((page, a, b))

    print()
    print("pages in PAGE_MAP with a paper panel : %d   (%d without one)" % (examined, nopanel))
    print("pages whose ABSTRACT reports agreement between trials the page does NOT pool: %d"
          % len(hits))
    print()
    for page, a, b in hits:
        print("  %s" % page)
        print("      abstract says : ...%s" % " ".join(a.split())[-120:])
        print("      page also says: ...%s" % " ".join(b.split())[:120])
    out = os.path.join(REPO, "outputs", "pooled_claim_without_pool_2026_08_25.json")
    json.dump({"examined": examined, "pages": [h[0] for h in hits]},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print()
    print("written: %s" % os.path.relpath(out, REPO))
    # A GATE THAT CANNOT FAIL IS NOT A GATE. This exits non-zero on any hit, and the
    # control above proves the detector can produce a hit -- so a zero here is a
    # measurement, not the silence of a broken instrument.
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
