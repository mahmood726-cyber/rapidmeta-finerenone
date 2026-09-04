"""An external authority named with no anchor in the same block, read from DISPLAYED bytes.

AN UNSOURCED CLAIM DOES NOT MERELY LACK SUPPORT. IT DRIFTS TO ITS STRONGEST FORM, because
nothing holds it to the weaker one. "WHO has recommended the ring" lost the
conditionality, the certainty grade, the population and the combination framing -- every
qualifier a clinician needs in order to act on it. The sentence is shorter, more
confident, and wrong in the direction that matters.

THIS IS THE DISPLAYED-BYTES LEG, AND IT IS DELIBERATELY THE COMPLEMENT OF THE OTHER
LANE'S. A sibling detector for this class exists in another lane and is not in this tree;
duplicating it would produce a second number for one fact, which is the failure this
project names most often. Where the two disagree, that is a finding to REPORT, not to
reconcile quietly.

What this leg uniquely sees is what a reader actually receives. A check elsewhere passed a
page that RENDERED sentence[:300] while the check itself read the whole stored sentence:
the anchor existed in the data and was cut off before the reader. Reading the served HTML
makes that impossible -- whatever truncation the builder applied is already in the bytes
being searched.

BLOCK, NOT PAGE. "In the same block" is the whole rule and cannot be checked against
flattened page text: a page-wide search finds a year in the footer and calls a claim in
the header anchored. The HTML is split at its own element boundaries and each block is
judged alone.

WHAT COUNTS AS AN ANCHOR: something a reader could follow or date -- a four-digit year, a
DOI or URL, a registration id, a located document with a version or section, or an
explicit accessed date. Not a bare institution name.

THREE DISCRIMINATIONS, EACH PAID FOR BY A MEASURED FALSE POSITIVE ON LIVE DATA.

  1,115 -> 74   A TOOL IS NOT A CLAIMANT. The first run returned 1,115 hits and the great
                majority were "Cochrane RoB-2 (per-domain traffic light)" -- the label of
                the instrument this corpus applies, on nearly every page. Demanding a
                citation for it would accuse ~840 pages of a defect none of them has.
  27 -> 26      THE PRONOUN IN EMPHATIC CAPITALS. This prose writes emphasis in capitals,
                so COLCHICINE_CVD_REVIEW carries "the person WHO has seen it". Measured 1
                of 27. Case-sensitivity was supposed to separate organisation from pronoun
                and on this corpus it does not.
  and back      BUT ONLY IF EVERY OCCURRENCE IS A PRONOUN. Suppressing a block because it
                contained one pronoun killed a real claim: "WHO recommends it for women
                who are at risk" holds both, and the organisation is the subject.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "unanchored_authority_2026_08_30.json")

# Named external authorities. Case-sensitive for the acronyms on purpose.
AUTHORITY = re.compile(
    r"\b(WHO|World Health Organization|World Health Organisation|"
    r"FDA|Food and Drug Administration|EMA|European Medicines Agency|"
    r"NICE|MHRA|CDC|USPSTF|IARC|KDIGO|GOLD|IDSA|EACS|ESC|AHA|ACC|"
    r"CADTH|PBAC|IQWiG|ICER|Cochrane)\b")

# The authority must be the SUBJECT OF AN ASSERTION, not a noun inside a method name.
CLAIM_VERB = re.compile(
    r"(?i)\b(recommend\w*|approv\w*|advis\w*|state[sd]?|says?|conclud\w*|"
    r"requir\w*|warn\w*|endors\w*|designat\w*|classif\w*|authoris\w*|authoriz\w*|"
    r"licen[sc]\w*|mandat\w*|urg\w*|has found|found that|guidance|guideline\w*|"
    r"position statement|has determined)\b")

# A tool, instrument or standard being NAMED makes the mention a method statement.
TOOL_CONTEXT = re.compile(
    r"(?i)(RoB[- ]?2|risk of bias|handbook|checklist|criteria|tool|scale|instrument|"
    r"traffic light|GRADE|framework|template|reporting standard|PRISMA)")

# An antecedent immediately before WHO makes THAT occurrence a relative pronoun. Anchored
# at the end so it is tested against the text preceding one specific occurrence, never
# against the whole block -- the block-wide version suppressed real claims.
ANTECEDENT = re.compile(
    r"(?i)\b(person|people|those|anyone|someone|everyone|one|reviewer|reviewers|"
    r"clinician|clinicians|patient|patients|participant|participants|author|authors|"
    r"woman|women|man|men|reader|readers|colleague|colleagues)\s+$")

ANCHOR = re.compile(
    r"(\b(19|20)\d{2}\b"                       # a year
    r"|10\.\d{4,9}/[^\s\"'<>]+"                # a DOI
    r"|https?://[^\s\"'<>]+"                   # a URL
    r"|\bNCT\d{8}\b|\bPMID\s*\d+|\bPMC\d+"     # an identifier
    r"|\bsection\s+\d|\bversion\s+[\w.]+"      # a located document
    r"|\bread\s+(on\s+)?\d|\baccessed\b"       # an explicit read date
    r"|\bv\d+\.\d+)", re.I)

# A TABLE ROW IS ONE SEMANTIC UNIT. `td` and `th` were block boundaries until 2026-09-04,
# so a citation table -- the place a page's anchors are most rigorously supplied -- read as
# unanchored: the title sat in one cell and its resolvable link in the cell beside it, and
# the split put the anchor outside the block. Measured on AGYW_HIV_PREP_REVIEW, five of seven
# findings were PubMed titles whose PMIDs (37606684, 25224620, 41859069, 41084700, 32708182)
# were one cell away and clickable.
#
#     SPLITTING AT </td> MAKES A PAGE LOOK UNANCHORED AT EXACTLY THE PLACE ITS ANCHORS ARE
#     MOST RIGOROUSLY SUPPLIED.
#
# Rows are the unit now. This makes the sweep report LESS, which is the shape of a loosened
# check, so `must_still_fire()` below proves the true positives survive -- including an
# unanchored claim inside a table row with no anchor anywhere in that row.
BLOCK_SPLIT = re.compile(
    r"(?is)</(p|li|tr|h1|h2|h3|h4|h5|h6|div|section|blockquote|figcaption|caption)>")

# A PAGE DISCLOSING A FINDING MUST NOT BE FLAGGED FOR THE DISCLOSURE.
#
# AGYW's seventh finding WAS THE PAGE'S OWN DISCLOSURE OF ITS FOURTH, re-detected as an
# eighth instance of itself. A detector that cannot tell MAKING a claim from REPORTING THAT
# ONE WAS MADE penalises disclosure, and the penalty compounds with thoroughness -- it
# selects against the behaviour this project most wants.
#
# ⛔ KEYED ON THE REGISTER'S MARKUP AND POSITION, NEVER ON THE WORDS THE GATE REPORTS. Keying
# on "unanchored" would let any page immunise itself by quoting the finding. The idiom is a
# defect-class id in a `mono` span at the head of the block, followed by a colon -- the
# page's findings-register shape, which prose cannot fall into by accident.
DISCLOSURE = re.compile(r'(?is)<span class="mono">[a-z0-9_.-]{4,60}</span>\s*:')


def blocks(html):
    """The page's own element boundaries, as displayed text."""
    body = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    out = []
    for chunk in BLOCK_SPLIT.split(body):
        if not chunk or len(chunk) < 3:
            continue
        if DISCLOSURE.search(chunk):
            continue
        # A HYPERLINK IS AN ANCHOR, AND STRIPPING TAGS FIRST MADE IT INVISIBLE.
        #
        # ANCHOR asks for "something a reader could follow or date" and a URL is the
        # canonical case -- but a link's URL lives in the `href` ATTRIBUTE, and this
        # function removed every tag before testing. So a block reading
        # `<a href="https://pubmed.ncbi.nlm.nih.gov/41084700/">41084700</a>` was judged on
        # the bare digits "41084700", which match no anchor pattern: the year rule needs a
        # word boundary before 19xx/20xx and there is none mid-number.
        #
        #     THE MOST FOLLOWABLE THING ON THE PAGE -- A CLICKABLE LINK -- WAS THE ONE FORM
        #     OF ANCHOR THIS SWEEP COULD NOT SEE.
        #
        # The hrefs are appended to the visible text so ANCHOR tests what a reader can
        # actually follow. This is additive: a block with no link is judged exactly as
        # before.
        hrefs = " ".join(re.findall(r"""(?i)href=["']([^"']+)["']""", chunk))
        text = re.sub(r"<[^>]+>", " ", chunk)
        if hrefs:
            text = text + " " + hrefs
        try:
            import html as _h
            text = _h.unescape(text)
        except Exception:
            pass
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            out.append(text)
    return out


def only_pronouns(b):
    """True when EVERY uppercase WHO in this block is a relative pronoun."""
    for m in re.finditer(r"\bWHO\b", b):
        if not ANTECEDENT.search(b[max(0, m.start() - 24):m.start()]):
            return False
    return True


def decide(b):
    """The whole rule in one place, so the controls exercise what the sweep runs."""
    names = sorted(set(AUTHORITY.findall(b)))
    if not names:
        return False
    if names == ["WHO"] and only_pronouns(b):
        return False
    if TOOL_CONTEXT.search(b):
        return False
    if not CLAIM_VERB.search(b):
        return False
    return not ANCHOR.search(b)


# --------------------------------------------------------------------------
# KNOWN-NEGATIVE CONTROLS. (block, must_flag, why)
KNOWN_NEGATIVE_CONTROLS = [
    ("WHO has recommended the ring.", True,
     "the reported instance: an authority asserted with nothing to follow"),
    ("WHO conditionally recommends the ring for women at substantial risk "
     "(WHO guideline, 2021).", False,
     "the same claim with a year -- anchored, and it must not be flagged"),
    ("It is not clear who wrote the protocol.", False,
     "the lowercase pronoun is not the World Health Organization"),
    ("Cochrane Handbook section 10.4.4 gives the formula.", False,
     "an authority named inside a located citation is anchored by the section"),
    ("Pooled RR 0.87 (0.79 to 0.96), k = 4.", False,
     "a block with no authority in it at all must never be flagged"),
    ("The FDA approved it.", True,
     "a regulator asserted with no date is undatable, and approvals get withdrawn"),
    ("See https://www.who.int/publications/i/item/9789240031593 for the guidance.", False,
     "a URL is followable even though the authority appears only inside it"),
    ("Cochrane RoB-2 (per-domain traffic light)", False,
     "NAMING THE TOOL USED is a method statement, not a claim attributed to Cochrane. "
     "This exact string was the majority of the first run's 1,115 hits"),
    ("Risk of bias was assessed with RoB 2 (Cochrane).", False,
     "the same thing in a sentence: the authority is the tool's provenance, not a claimant"),
    ("WHO recommends the ring for women at substantial risk.", True,
     "an authority as the subject of a recommendation, undated -- the reported class"),
    ("the choice must not be made by the person WHO has seen it", False,
     "THE PRONOUN IN EMPHATIC CAPITALS. Real prose from COLCHICINE_CVD_REVIEW, and the "
     "measured false positive of the first live run: 1 of 27"),
    ("the guidance was written by the clinicians WHO recommend it", False,
     "THE CONTROL THAT ACTUALLY EXERCISES THE PRONOUN BRANCH. The line above passed while "
     "the pronoun test was DEAD -- its boundaries had become backspaces -- because the "
     "claim-verb filter rejected it first, for carrying no claim verb. A control satisfied "
     "by a different branch certifies nothing about the branch it was written for. This "
     "one carries a claim verb, so it REACHES the pronoun test and can only pass if that "
     "test works"),
    ("WHO recommends it for women who are at risk.", True,
     "the organisation AND a pronoun in one block. Suppressing on any pronoun killed this "
     "real claim; the test is now per-occurrence"),
]


# --------------------------------------------------------------------------
# SEGMENTATION CONTROLS. (html, must_flag, why)
#
# The list above tests `decide()` on ready-made blocks, so it cannot see a segmentation
# defect: it never runs `blocks()`. Both false positives fixed on 2026-09-04 were invisible
# to it for that reason -- the rule was right and the block handed to it was wrong.
#
#     A CONTROL THAT SKIPS THE STEP THAT BROKE CERTIFIES THE STEP THAT DIDN'T.
#
# These run the whole path, HTML in, verdict out. The first two are the must-still-catch
# cases for the row-level split: the fix makes the sweep report LESS, and a change that only
# ever removes findings is indistinguishable from a loosened check unless the true positives
# are held down by name.
SEGMENTATION_CONTROLS = [
    ("<p>WHO has recommended the ring for women at substantial risk.</p>", True,
     "MUST STILL FIRE: an unanchored claim in ordinary prose. The row-level split must not "
     "reach it"),
    ("<table><tr><td>Guidance</td>"
     "<td>WHO has recommended the ring for women at substantial risk.</td>"
     "<td>no source recorded</td></tr></table>", True,
     "MUST STILL FIRE: the same claim inside a table row with NO anchor anywhere in the "
     "row. Widening the unit to the row must not grant a row an anchor it does not have"),
    ("<table><tr>"
     "<td><a href='https://pubmed.ncbi.nlm.nih.gov/41084700/'>41084700</a></td>"
     "<td>FDA-Approved HIV-1 Capsid Inhibition With Lenacapavir: A Paradigm Shift in "
     "Pre-exposure Prophylaxis.</td></tr></table>", False,
     "THE CITATION-TABLE FALSE POSITIVE. Two defects in one block: the split at </td> put "
     "the link outside the title's block, and stripping tags before the anchor test hid "
     "the href even when it was inside. Five of AGYW's seven findings were this"),
    ("<ul><li><span class=\"mono\">unanchored-external-authority</span>: "
     "FDA-Approved HIV-1 Capsid Inhibition With Lenacapavir: A Paradigm Shift in "
     "Pre-exposure Pr; FDA-Approved Drugs.</li></ul>", False,
     "THE PAGE'S OWN DISCLOSURE, re-detected as a further instance of itself. Keyed on the "
     "register's markup, never on the words this sweep reports -- keying on 'unanchored' "
     "would let any page immunise itself by quoting the finding"),
    ("<p>Unlike an unanchored-external-authority finding, this one is solid: "
     "WHO has recommended the ring for women at substantial risk.</p>", True,
     "THE IMMUNISATION ATTACK, and the reason the exclusion is keyed on markup. This block "
     "contains the exact defect-class id this sweep reports, in ordinary prose, and it "
     "MUST STILL BE FLAGGED. A keyword-keyed exclusion would let any page buy silence for "
     "the price of naming the check -- and the pages most likely to name it are the ones "
     "with the most to hide"),
]


def measure_segmentation(say):
    bad = 0
    for html, must, why in SEGMENTATION_CONTROLS:
        got = any(decide(b) for b in blocks(html))
        if got != must:
            bad += 1
            say("   SEGMENTATION CONTROL FAILED  expected %-5s got %-5s -- %s"
                % (must, got, why))
    say("   segmentation: %d/%d wrong" % (bad, len(SEGMENTATION_CONTROLS)))
    return bad


def measure_precision(say):
    bad = 0
    for text, must, why in KNOWN_NEGATIVE_CONTROLS:
        got = decide(text)
        if got != must:
            bad += 1
            say("   CONTROL FAILED  expected %-5s got %-5s on %r -- %s"
                % (must, got, text[:52], why))
    rate = 100.0 * bad / len(KNOWN_NEGATIVE_CONTROLS)
    say("   controls: %d/%d wrong (measured error rate %.1f%%)"
        % (bad, len(KNOWN_NEGATIVE_CONTROLS), rate))
    return bad + measure_segmentation(say)


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    say("UNANCHORED-AUTHORITY SWEEP -- displayed bytes, block by block")
    say("")
    say("PRECISION, measured before any count is reported:")
    if measure_precision(say):
        say("")
        say("REFUSED: the detector failed its own controls. Any count would be a statement "
            "about the matcher, not about the corpus.")
        return 2
    if "--plant" in sys.argv:
        say("")
        say("PLANT -- constructed blocks with known answers")
        ok = 0
        for text, must, why in KNOWN_NEGATIVE_CONTROLS:
            good = decide(text) == must
            ok += 1 if good else 0
            say("   [%s] %s" % ("PASS" if good else "FAIL", why[:104]))
        say("   plant: %d/%d" % (ok, len(KNOWN_NEGATIVE_CONTROLS)))
        return 0 if ok == len(KNOWN_NEGATIVE_CONTROLS) else 2
    say("")

    pages = sorted(f for f in os.listdir(REPO)
                   if f.endswith(".html") and os.path.isfile(os.path.join(REPO, f)))
    findings, unreadable = [], []
    n_blocks = n_with_authority = n_pages_read = 0
    n_claims = n_tool = n_bare = n_pronoun = 0

    for page in pages:
        try:
            html = io.open(os.path.join(REPO, page), encoding="utf-8",
                           errors="replace").read()
            page_blocks = blocks(html)
        except OSError:
            unreadable.append(page)
            page_blocks = None
        if page_blocks is not None:
            n_pages_read += 1
            for b in page_blocks:
                n_blocks += 1
                names = sorted(set(AUTHORITY.findall(b)))
                if names:
                    n_with_authority += 1
                    if names == ["WHO"] and only_pronouns(b):
                        n_pronoun += 1
                    elif TOOL_CONTEXT.search(b):
                        n_tool += 1
                    elif CLAIM_VERB.search(b):
                        n_claims += 1
                        if not ANCHOR.search(b):
                            findings.append({"page": page, "authorities": names,
                                             "block": b[:400]})
                    else:
                        n_bare += 1

    bypage = {}
    for f in findings:
        bypage.setdefault(f["page"], []).append(f)

    say("SCOPE, before the counts")
    say("   delivered pages read:                %d" % n_pages_read)
    say("   pages that could not be read:        %d" % len(unreadable))
    say("   blocks examined:                     %d" % n_blocks)
    say("   blocks naming an external authority: %d" % n_with_authority)
    say("      the authority is the SUBJECT OF A CLAIM:            %d" % n_claims)
    say("      it NAMES A TOOL used -- a method statement:         %d" % n_tool)
    say("      every uppercase WHO is a relative PRONOUN:          %d" % n_pronoun)
    say("      a bare mention with no assertion attached:          %d" % n_bare)
    say("")
    say("UNANCHORED -- an authority making a claim with nothing in the block to follow "
        "or date: %d" % len(findings))
    say("   across %d pages" % len(bypage))
    say("")
    for page in sorted(bypage, key=lambda p: -len(bypage[p])):
        say("   %-52s %d" % (page[:52], len(bypage[page])))
    say("")
    say("EVERY FINDING, as a reader receives it:")
    for f in findings:
        say("   %-40s %-16s %s" % (f["page"][:40], ",".join(f["authorities"])[:16],
                                   f["block"][:110]))

    json.dump({"n_pages_read": n_pages_read, "unreadable": unreadable,
               "n_blocks": n_blocks, "n_blocks_with_authority": n_with_authority,
               "n_claims": n_claims, "n_tool_mentions": n_tool,
               "n_pronoun_blocks": n_pronoun, "n_bare_mentions": n_bare,
               "findings": findings},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
