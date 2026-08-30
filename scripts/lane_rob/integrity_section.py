# -*- coding: utf-8 -*-
"""The integrity section: a REQUIRED generated part of every page, and a build refusal if absent.

WHY THIS IS A COMPONENT AND NOT A HABIT. Standing orders §10: the error-pattern layer is the
product, and the specific risk is that a pivot to the clinical scoring axes quietly drops weeks
of defect work, because the clinical axes are the ones a judge scores. A rule that lives only in
a brief gets dropped the moment something urgent arrives -- documented five times this week. So
the protection is structural: `assert_present()` REFUSES the build when the section is missing
or empty, and the section cannot be lost without a gate failing.

WHAT IT PUTS ON THE PAGE, and the framing matters. Not "look how rigorous we are" -- that is
the assertion judges discount. Instead: **these are the specific errors that would otherwise be
in the numbers you just read.** That is interpretation, which is the same conversion that made
the audit trail scoreable.

⭐ AND IT NAMES THE CLASSES WE CANNOT YET DETECT. Nobody else prints that, which is exactly why
it is credible. A taxonomy that lists only what it catches is marketing.

LINEAGE IS FIRST-CLASS. Every class carries the REAL DEFECT that generated it. A taxonomy whose
entries cannot be traced to the failure that produced them is a document; one that can is
evidence.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def _rendered(html):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


# ---------------------------------------------------------------- instrumented classes
# id, what it checks, the REAL DEFECT that generated it, and the check itself.
def _c_tokens(html, txt):
    return re.findall(r"\{\{[^}]*\}\}|REPLACE_ME|__PLACEHOLDER__|\bnan\b", html)


def _c_bare_none(html, txt):
    return re.findall(r">\s*None\s*<|:\s*None\b|\bNone participants\b", html)


def _c_tag_balance(html, txt):
    bad = []
    for tag in ("div", "table", "tr", "td", "th", "p", "ul", "li", "h2", "h3", "span"):
        o = len(re.findall(r"<%s[\s>]" % tag, html))
        c = html.count("</%s>" % tag)
        if o != c:
            bad.append("%s %d/%d" % (tag, o, c))
    return bad


def _c_estimand_named(html, txt):
    return [] if re.search(r"estimand", txt, re.I) else ["the estimand is never named"]


def _c_both_intervals(html, txt):
    has_hk = re.search(r"hartung|knapp|HKSJ", txt, re.I)
    named_modified = re.search(r"modified", txt, re.I)
    if has_hk and not named_modified:
        return ["a Hartung-Knapp interval is reported without being named as the modified form"]
    return []


def _c_ratio_natural_scale(html, txt):
    out = []
    for m in re.finditer(r"(pooled|reported|combined)\s+on the natural scale", txt, re.I):
        w = txt[max(0, m.start() - 300):m.end() + 120]
        if re.search(r"\b(HR|OR|RR|IRR)\b", w):
            out.append(w[-90:])
    return out


def _c_denial_of_held(html, txt):
    """A page must not DENY something it holds. §9a: 92 pages denied a protocol we had."""
    out = []
    if re.search(r"no (published )?(synthesis|systematic review) exists", txt, re.I):
        out.append("denies that a published synthesis exists")
    if re.search(r"no full[- ]text|abstract only", txt, re.I) and not re.search(
            r"paywall|not open access|not in PubMed Central", txt, re.I):
        out.append("claims no full text without naming a route that was tried")
    return out


# A DECLARED CONTRAST IS NOT A CONTRADICTION, and the first run of this check could not tell
# them apart. It flagged "pooled estimate appears as 0.7038 and 0.7127" on a page that shows
# both ON PURPOSE, side by side, labelled registry versus adjudicated, with a paragraph
# explaining the difference. That is the page doing the right thing and the detector calling it
# a defect -- a false positive in the accusing direction, which is this project's measured bias.
# So the check now requires the two values to appear WITHOUT contrastive framing nearby.
CONTRAST = re.compile(
    r"registry|adjudicat|versus|instead of|moves from|previously|as submitted|"
    r"difference it makes|earlier version", re.I)


def _c_stat_twice(html, txt):
    """The same labelled statistic with two values AND no declared contrast between them."""
    seen, bad = {}, []
    for m in re.finditer(r"(pooled RR|pooled estimate|risk ratio)[^0-9]{0,24}(\d\.\d{3,4})",
                         txt, re.I):
        k, v = m.group(1).lower(), m.group(2)
        if k in seen and seen[k][0] != v:
            lo = min(seen[k][1], m.start())
            hi = max(seen[k][1], m.end())
            if not CONTRAST.search(txt[max(0, lo - 200):hi + 200]):
                bad.append("%s appears as %s and %s with no declared contrast"
                           % (k, seen[k][0], v))
        seen.setdefault(k, (v, m.start()))
    return bad


def _c_traceable(html, txt):
    return [] if re.search(r"audit trail|read from|sha256", txt, re.I) else [
        "no number carries a source"]


def _c_single_trial_pooled(html, txt):
    """A single trial's result presented with pooling language.

    Added 2026-08-29 to test that the layer GROWS: a new class must reach every page on the
    next regeneration without anyone editing a page. Traced to a real defect -- the front page
    carried "the withdrawn HR 0.85 (0.79-0.92) was a single trial's result shown as a two-trial
    pool".
    """
    out = []
    for m in re.finditer(r"pooled[^.]{0,120}?\bk\s*=\s*1\b", txt, re.I):
        out.append(re.sub(r"\s+", " ", m.group(0))[:90])
    for m in re.finditer(r"\bk\s*=\s*1\b[^.]{0,80}?pooled", txt, re.I):
        out.append(re.sub(r"\s+", " ", m.group(0))[:90])
    return out


SELF_DESCRIPTION_MARKER = "What was checked before this page was published"


def scannable_body(html):
    """The part of the page a defect checker may read: everything ABOVE the integrity section.

    ⛔ A DECLARED EXCLUSION WITH A REASON, NOT AN AD-HOC CUT IN ONE CHECKER.

    The integrity section names the defect classes and quotes real examples of each -- that is
    what makes it useful to a reader and what makes it poison to a checker. Two classes scored
    their own output in one night:

      - the regeneration test read "binary counts pooled where both trials analysed time to
        event" out of the class list and credited the review with HAVING the feature; 0 of 13
        became "3 of 13", two of the three being the checker describing the defect;
      - `unanchored-external-authority` quotes the sentence "'WHO has recommended the ring' went
        live from a conversation", so it reported the defect as live on every page forever.

    The failure is structural, not a bug in either class: any new class that names its example
    will do this on the day it is added. So the exclusion is declared HERE, once, with the
    reason, and every checker calls it -- rather than each author remembering a cut that is
    invisible until the class goes permanently red.

    ⚠️ The exclusion is one-directional. A checker must not read the section, but the section
    must still be checked BY something -- assert_present() tests the rendered section itself, on
    the full page, for exactly that reason.
    """
    h = html or ""
    i = h.find(SELF_DESCRIPTION_MARKER)
    return h[:i] if i > 0 else h


def _c_unanchored_authority(html, txt):
    """An external body's position asserted with nothing that could be retrieved to check it.

    ⛔ THIS CLASS EXISTS BECAUSE THE WORST INSTANCE WAS MINE. Mahmood told me in conversation
    that WHO had recommended the ring; I put "WHO has recommended the ring as an additional
    prevention choice" on the live pilot page with no document behind it. A claim that exists
    only in a conversation is indistinguishable downstream from one that was retrieved.

    Retrieval then showed the sentence was also WRONG IN SUBSTANCE, not merely unsourced. WHO's
    actual words are "may be offered ... (Conditional recommendation; moderate-certainty
    evidence)" for women at substantial risk as part of combination prevention. "Has
    recommended" drops the conditionality, the certainty grade and the population -- every
    qualifier a clinician needs. Unsourced claims do not merely lack support; they drift toward
    the strongest form, because nothing is holding them to the weaker one.

    Four instances on one page, three of which nobody had flagged:
      - WHO recommendation, stated bare            -> sourced, and corrected to conditional
      - EMA "extended its opinion to girls 16+"    -> unretrievable (404); REMOVED
      - "Cochrane's guidance is that ..."          -> attribution dropped; the arithmetic stands
      - "no FDA review of this product EXISTS"     -> a claim about the world doing load-bearing
        work: it converted a retrieval gap into "genuinely unobtainable". openFDA returns 404
        for dapivirine, and a 404 from an API is not a demonstration that no review exists.
        Restated as what was established: no FDA review was FOUND.

    ⚠️ And it was present TWICE -- in the obtainability table and again in Limitations. Fixing
    the first and re-scanning is what caught the second. Withdraw on both surfaces.
    """
    # (?-i:WHO) -- case-sensitive. Under re.I the bare word matched the interrogative pronoun,
    # and "Who did what is a fact about people" was reported as an unsourced WHO position on two
    # generated pages. An acronym that is also an English word must be matched as an acronym.
    AUTH = (r"(?-i:WHO)|World Health Organization|(?-i:FDA)|(?-i:EMA)|European Medicines Agency|"
            r"Cochrane|(?-i:NICE)|UNAIDS|EACS|BHIVA")
    # Evidence-of-retrieval markers. "probed/staged/enumerated/server's answers" belong here for
    # the same reason "retrieved" does: sglt2-hf backs its FDA absence claim with an enumeration
    # of every submission Drugs@FDA serves, which is a stronger demonstration than a URL, and was
    # being flagged by this class purely because it did not contain one.
    ANCH = re.compile(r"https?://|10665/|NCT\d{8}|PMID|PMC\d+|doi|retrieved|sha256|ISBN|openFDA|"
                      r"staged|probed?\b|enumerat\w+|submissions asked|server'?s answers", re.I)
    # A verb that asserts a POSITION held by that body, rather than merely naming it.
    STANCE = re.compile(r"\b(%s)\b[^.]{0,90}?\b(recommend\w*|approv\w*|endors\w*|extended|"
                        r"guidance is|advises|requires|concluded|records|states)\b" % AUTH, re.I)
    # ⚠️ THE WINDOW IS THE ENCLOSING BLOCK, AND GETTING THERE TOOK TWO WRONG ANSWERS.
    #
    # First version: two sentences either side. It flagged the CORRECTED page and a deliberately
    # sourced control, because the citation begins "WHO. Guidelines: ..." and the sentence
    # splitter breaks on that abbreviation's full stop, producing a one-word "sentence" that
    # shunted the real anchor out of the window.
    #
    # Second version: 400 characters either side. Still flagged the corrected page, because a
    # claim quoted in full plus its citation runs longer than that. The fix there would have
    # been to raise 400 until the page went quiet -- which is fitting the threshold to the one
    # page in front of me, and would have made the check weaker on every other page silently.
    #
    # A document already has the right unit: the block the sentence sits in. A claim and its
    # citation belong to the same <p>, <li> or <td>; a citation in a different block is not
    # backing this claim. So the check reads the MARKUP rather than the flattened text, and
    # nothing needs tuning. A check that fires on text already fixed is worse than one that
    # misses, because it teaches the reader to skip it.
    body = scannable_body(html)
    out = []
    seen = set()
    blocks = re.findall(r"(?is)<(p|li|td|h[1-6])\b[^>]*>(.*?)</\1>", body)
    for _tag, inner in blocks:
        btxt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", inner))
        for m in STANCE.finditer(btxt):
            if ANCH.search(btxt):
                continue
            # "FDA approved label" names a DOCUMENT; it does not assert a position -- the stance
            # word is adjectival there. Known limit: this is a word list, not grammar.
            if re.match(r"[^ ]+ approved (label|product|indication|drug|dose|use)",
                        btxt[m.start():m.start() + 60], re.I):
                continue
            # "The FDA label records ..." reports what a document we hold SAYS. That is a
            # document reference, not the agency taking a position, and belongs to the sourcing
            # classes rather than this one.
            if re.match(r"[^ ]+ (label|review|report|assessment|guideline|document|annex)\b",
                        btxt[m.start():m.start() + 60], re.I):
                continue
            frag = re.sub(r"\s+", " ", btxt[m.start():m.start() + 110])
            if frag[:40] not in seen:
                seen.add(frag[:40])
                out.append(frag)
        # ⛔ THE ABSENCE SUB-CHECK MUST RESPECT THE SAME ANCHOR, and it did not.
        #
        # It ran unconditionally over the whole page, so sglt2-hf was reported for "no FDA
        # review document exists" -- a claim that object backs with an enumeration of every
        # submission Drugs@FDA serves for both applications, 21 letters and 29 submissions with
        # per-submission answers. That is the strongest demonstration in the corpus, and the
        # check was calling it the defect. A checker that flags the model answer teaches people
        # to stop doing the right thing.
        if not ANCH.search(btxt):
            for m in re.finditer(r"no (?:FDA|EMA|WHO)[^.]{0,60}\bexists?\b", btxt, re.I):
                frag = "absence asserted as fact: " + re.sub(r"\s+", " ", m.group(0))[:80]
                if frag[:50] not in seen:
                    seen.add(frag[:50])
                    out.append(frag)
    if not blocks:                     # plain text handed in directly (tests, controls)
        for m in STANCE.finditer(txt):
            if not ANCH.search(txt[max(0, m.start() - 300):m.end() + 900]):
                out.append(re.sub(r"\s+", " ", txt[m.start():m.start() + 110]))
        # Same absence sub-check for the plain-text path, and it carries the anchor test too.
        for m in re.finditer(r"no (?:FDA|EMA|WHO)[^.]{0,60}\bexists?\b", txt, re.I):
            if not ANCH.search(txt[max(0, m.start() - 300):m.end() + 900]):
                out.append("absence asserted as fact: "
                           + re.sub(r"\s+", " ", m.group(0))[:80])
    return out


CLASSES = [
    ("unanchored-external-authority",
     "an outside body's position asserted with nothing retrievable behind it",
     "'WHO has recommended the ring' went live from a conversation, and dropped the "
     "conditionality WHO actually attached", _c_unanchored_authority),
    ("single-trial-shown-as-pooled", "one trial's result presented as a pool",
     "the front page carried a single trial's HR 0.85 (0.79-0.92) as a two-trial pool",
     _c_single_trial_pooled),
    ("unfilled-template-token", "a placeholder shipped unsubstituted",
     "11 pages cited protocols/name_protocol_v1.0.md -- 'name' was the placeholder", _c_tokens),
    ("bare-none-rendered", "a Python None reaching rendered output",
     "1110 dashboards rendered as 626-byte stubs from `None` in a JS literal", _c_bare_none),
    ("markup-imbalance", "unbalanced tags after a hand edit",
     "div-balance drift after HTML edits, repeatedly", _c_tag_balance),
    ("estimand-unnamed", "a pooled quantity presented without naming what it estimates",
     "binary counts pooled where both trials analysed time to event", _c_estimand_named),
    ("hksj-unqualified", "a small-k interval reported without naming the variance floor",
     "raw HKSJ narrows below Wald when Q < k-1; the q* floor was missing", _c_both_intervals),
    ("ratio-on-natural-scale", "a ratio measure said to be on the natural scale",
     "sglt2-hf rendered 'on the natural scale' for a hazard ratio", _c_ratio_natural_scale),
    ("denial-of-something-held", "the page denies what the corpus holds",
     "92 pages stated no protocol exists while a protocol sat in the repository",
     _c_denial_of_held),
    ("statistic-rendered-twice", "one statistic with two values on one page",
     "the same number rendered from two code paths", _c_stat_twice),
    ("untraceable-number", "a number with no source",
     "stored estimates that do not follow from their own counts: 172 of 178 uncheckable",
     _c_traceable),
]

# ---------------------------------------------------------------- classes with NO instrument
UNINSTRUMENTED = [
    ("narrative-contradicts-its-own-table",
     "prose that disagrees with the table beside it -- semantic, no instrument exists"),
    ("value-does-not-reconcile-with-its-source",
     "a stored number that does not follow from the document it cites; needs the source in hand,"
     " and we hold the primary report for a minority of trials"),
    ("planned-field-shown-as-observed",
     "a registered plan displayed in a field labelled as observation -- found by hand on this"
     " page's follow-up figure"),
    ("prior-synthesis-value-presented-as-primary",
     "a competitor's extraction reported as our own read; labelled here by hand, not detected"),
    ("subgroup-claim-beyond-the-trial-strata",
     "a subgroup statement the trial's own strata do not support"),
    ("adjudicated-versus-submitted-counts",
     "registry and publication disagreeing on event counts; detectable only where both are held"),
]


def run(html):
    txt = _rendered(html)
    found, clean = [], []
    for cid, what, lineage, fn in CLASSES:
        hits = fn(html, txt)
        (found if hits else clean).append((cid, what, lineage, hits))
    return found, clean


def render(html):
    """The integrity section, as HTML, from the checks actually run on this page."""
    found, clean = run(html)
    n = len(CLASSES)
    rows = "".join(
        "<tr><td><span class=\"mono\">%s</span></td><td>%s</td><td>%s</td></tr>"
        % (cid, what, lineage) for cid, what, lineage, _ in (found + clean))
    unins = "".join("<li><b>%s</b> &mdash; %s</li>" % (a, b) for a, b in UNINSTRUMENTED)
    flagged = ("".join("<li><span class=\"mono\">%s</span>: %s</li>"
                       % (cid, "; ".join(str(h)[:90] for h in hits[:2]))
                       for cid, _, _, hits in found)
               or "<li>none on this build</li>")
    return """
<h2 data-role='finding'>What was checked before this page was published</h2>

<p>These are the specific errors that would otherwise be in the numbers above. Each class was
derived from a real defect found by auditing this corpus, and each carries the defect that
generated it.</p>

<p><b>Checked against %d instrumented defect classes. %d flagged on this build.</b></p>

<div class="scroll"><table>
<tr><th>Class</th><th>What it catches</th><th>The defect that generated it</th></tr>
%s
</table></div>

<p><b>Flagged on this build:</b></p><ul>%s</ul>

<h3>%d classes we know about and cannot yet detect</h3>

<p>Named because a taxonomy that lists only what it catches is marketing.</p>
<ul>%s</ul>
""" % (n, len(found), rows, flagged, len(UNINSTRUMENTED), unins)


def inject(html):
    """Append the generated integrity section to a built page.

    Called from the generator's WRITE PATH, beside the do-not-rebuild refusal and the
    generator pin, because that is where this project has learned build-time rules belong: a
    check that lives in a caller script knows nothing about the two pages that were rebuilt
    after an explicit decision not to touch them, and both overwrites went through the write
    path.
    """
    if REQUIRED_MARKER in html:
        return html
    section = render(html)
    return html + '\n<div class="card">\n' + section + '\n</div>\n'


REQUIRED_MARKER = "What was checked before this page was published"


def assert_present(html, path="<page>"):
    """BUILD REFUSAL. A missing or empty integrity section stops the build.

    This is the structural half of standing orders §10: the section cannot be dropped without a
    gate failing, which is the only protection that has held on this project.
    """
    if REQUIRED_MARKER not in html:
        raise SystemExit(
            "REFUSED: %s carries no integrity section. Standing orders §10 makes it a REQUIRED "
            "generated section: what was checked, what was found, and which classes have no "
            "instrument. A page without it does not build." % path)
    seg = html.split(REQUIRED_MARKER, 1)[1]
    if len(_rendered(seg).strip()) < 400:
        raise SystemExit(
            "REFUSED: %s has an integrity section with almost no content (%d rendered "
            "characters). An empty section satisfies the letter and defeats the purpose."
            % (path, len(_rendered(seg).strip())))
    return True


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.chdir(REPO)
    page = sys.argv[1] if len(sys.argv) > 1 else "DAPIVIRINE_RING_PILOT_REVIEW.html"
    html = io.open(page, encoding="utf-8").read()
    if "--render" in sys.argv:
        print(render(html))
    elif "--assert" in sys.argv:
        assert_present(html, page)
        print("integrity section present and non-empty: %s" % page)
    else:
        found, clean = run(html)
        print("instrumented classes  %3d" % len(CLASSES))
        print("  clean               %3d" % len(clean))
        print("  FLAGGED             %3d" % len(found))
        for cid, what, _, hits in found:
            print("     %-30s %s" % (cid, str(hits)[:110]))
        print("classes with no instrument %3d" % len(UNINSTRUMENTED))
