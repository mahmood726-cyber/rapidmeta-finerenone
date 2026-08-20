"""Move the Paper panel from a record's register into a paper's. No content changes.

MAHMOOD READ THE DELIVERED `SGLT2_HF_REVIEW.html#paper` AND CALLED IT "COMPUTER CODE". He is
the second reader to bounce off that manuscript AFTER the `#paper` anchor was created and
the section order was fixed, so the ordering was necessary and was not what either of them
met. Measured on the delivered bytes by `scripts/lint_paper_reads_as_prose.py`: 84 of 299
sentences carry machine vocabulary, 28%, and 2,172 of 7,173 across the 99 pages that have a
Paper panel. THE UNIFORMITY IS THE DIAGNOSIS -- 28% to 41% on every page is what a projector
defect looks like, not what one topic's prose looks like.

THIS IS A REGISTER CHANGE AND NOT A CONTENT CHANGE. Nothing is paraphrased away. Every
estimate, every registration id, every registered outcome text and every field path stays
reachable. They stop standing inside sentences.

FIVE EDITS.

1. THE PROVENANCE ARROW MOVES OUT OF THE SENTENCE FLOW AND STAYS VISIBLE.
   `build_tabbed.py` appended `<small class='muted'>&larr; results.by_outcome.x.
   heterogeneity.i2</small>` to EVERY paragraph and EVERY table caption -- 65 on the SGLT2
   page, 1,233 across the corpus, the single largest source of field names in a reader's
   eye. It is the transparency property and it is not deleted. Each paragraph now carries a
   superscript number and each section ends with a VISIBLE numbered list of its sources.
   NOT A HOVER: a hover is invisible to anyone who does not know to hover, and invisible
   provenance is the metadata-only disclosure the regression check was just repaired for.

2. THE k-CASCADE STOPS PRETENDING TO BE A SENTENCE.
   "k0 surfaced 56; k2 role located 56; k3 experimental 49; k4 comparator 1; k5 background
   6; kNA not assessable 0; k included in object 4; k unscreened remainder 0" was a TABLE
   FLATTENED INTO PROSE by `key.replace("_", " ")`. It is the worst section on the page --
   24 machine sentences of 37. It becomes a table with worded row labels, and every count
   is unchanged.

3. AN ESTIMAND KEY IS NOT A NOUN A READER KNOWS.
   "For cvdeath_or_whf_first, a random model was fitted with the REML estimator" becomes
   "For cardiovascular death or hospitalisation for heart failure, first event, ...". The
   key is still in the provenance list, where a reader who wants it can see it.

4. I-SQUARED AND TAU-SQUARED ARE GLOSSED, NOT DROPPED.
   "Between-trial heterogeneity was I-squared 0%, tau-squared 0, Q 0.384, degrees of freedom
   2." keeps every number and gains the clause that says what they mean.

5. STORAGE PRECISION GOES; THE ESTIMATE STAYS AT THE PRECISION THE DATA SUPPORTS.
   0.7576 is not a three-significant-figure claim. The verbatim R block is untouched --
   a reader checking the arithmetic needs exactly those characters, and P46's fourth
   criterion requires them.

WHAT IS NOT TOUCHED. `Statistical output, quoted verbatim` is machine vocabulary BY DESIGN
and is excluded from the measurement by name; that exclusion is the check's negative
control. And the four reader-facing sections -- Abstract, Introduction, Discussion,
Conclusions -- come to EIGHT SENTENCES on this page, three of them single-line refusals.
NOTHING HERE FIXES THAT. It is P47, it is content the object does not hold, and no projector
change produces it. What this pass fixes is the Methods and Results, which on that page ARE
the manuscript, which is why a reader met them and called them code.
"""
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(REPO, "ssot", "build_tabbed.py")
PROJ = os.path.join(REPO, "ssot", "paper_projector.py")


def read(p):
    return io.open(p, encoding="utf-8", errors="strict").read()


def write(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def sub_once(src, old, new, what):
    if old not in src:
        sys.exit("REFUSED: %s -- the text this pass was written against is not present. "
                 "Re-read before writing." % what)
    if src.count(old) != 1:
        sys.exit("REFUSED: %s -- %d occurrences, expected exactly one."
                 % (what, src.count(old)))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------------------
# 1. THE PROVENANCE FOOTNOTE COLUMN
# ---------------------------------------------------------------------------------------
OLD_RENDER = '''    for s in secs:
        out.append("<h3>%s</h3>" % e(s.heading))
        for text, fields in s.paras:
            out.append("<p>%s<br><small class='muted'>&larr; %s</small></p>"
                       % (e(text), e(", ".join(fields))))
        # A PROJECTED TABLE. Every cell is escaped -- the cells are object values, and an
        # object value containing markup must render as text and never as markup. The
        # caption carries the same field trace a paragraph does, because a table asserts
        # as much as a sentence and is read with more trust.
        for caption, headers, rows, fields in getattr(s, "tables", []):
            out.append("<table><caption>%s<br><small class='muted'>&larr; %s</small>"
                       "</caption>" % (e(caption), e(", ".join(fields))))
            out.append("<tr>%s</tr>" % "".join("<th>%s</th>" % e(h) for h in headers))
            for row in rows:
                out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % e(c) for c in row))
            out.append("</table>")
        for what, missing in s.refusals:
            out.append("<div class='absent-state' role='note'><strong>Refused:</strong> %s "
                       "&mdash; no field: <code>%s</code></div>"
                       % (e(what), e(", ".join(missing))))'''

NEW_RENDER = '''    for s in secs:
        out.append("<h3>%s</h3>" % e(s.heading))
        # THE PROVENANCE COLUMN. Every paragraph, table and refusal in this section used to
        # carry its field path INSIDE the flow -- "<p>text<br><small>&larr;
        # results.by_outcome.x.heterogeneity.i2</small></p>" -- 1,233 times across the
        # corpus and the largest single source of field names in a reader's eye. The
        # transparency property is not weakened: each statement now carries a superscript
        # and the section ENDS WITH A VISIBLE NUMBERED LIST of its sources.
        #
        # DELIBERATELY NOT A HOVER. A hover is invisible to anyone who does not know to
        # hover, and provenance a reader cannot see exists is the same defect as a
        # withdrawal declared only in a meta tag -- which is the reading this project just
        # repaired in regression_check.py. A reader must be able to SEE that the sources
        # are there before deciding whether to read them.
        sources = []

        def _mark(fields):
            """Register this statement's fields; return the superscript to print."""
            sources.append(", ".join(fields))
            return ("<sup class='prov-ref' title='source %d for this section'>%d</sup>"
                    % (len(sources), len(sources)))

        for text, fields in s.paras:
            out.append("<p>%s%s</p>" % (e(text), _mark(fields)))
        # A PROJECTED TABLE. Every cell is escaped -- the cells are object values, and an
        # object value containing markup must render as text and never as markup. The
        # caption carries the same field trace a paragraph does, because a table asserts
        # as much as a sentence and is read with more trust.
        for caption, headers, rows, fields in getattr(s, "tables", []):
            out.append("<table><caption>%s%s</caption>" % (e(caption), _mark(fields)))
            out.append("<tr>%s</tr>" % "".join("<th>%s</th>" % e(h) for h in headers))
            for row in rows:
                out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % e(c) for c in row))
            out.append("</table>")
        for what, missing in s.refusals:
            out.append("<div class='absent-state' role='note'><strong>Refused:</strong> "
                       "%s%s</div>" % (e(what), _mark(missing)))
        if sources:
            out.append("<div class='prov-block'><p class='prov-title'>Where the statements "
                       "in this section come from, in order</p><ol class='prov-list'>")
            for src in sources:
                out.append("<li><code>%s</code></li>" % e(src))
            out.append("</ol></div>")'''

# The panel's own opening sentence describes the old rendering.
OLD_LEDE = ('''           "<p class='muted'>Every paragraph below is PROJECTED from a field of this "
           "object, and names it. <strong>A section with no field behind it is not "
           "written</strong> &mdash; it is refused, by name, so a reader can tell an absent "
           "procedure from an unmentioned one.</p>"]''')
NEW_LEDE = ('''           "<p class='muted'>Every statement below is projected from a field of this "
           "object. The superscripts are sources: each section ends with the fields its "
           "statements came from, in order. <strong>A section with no field behind it is "
           "not written</strong> &mdash; it is refused, by name, so a reader can tell an "
           "absent procedure from an unmentioned one.</p>"]''')


# ---------------------------------------------------------------------------------------
# 2. THE k-CASCADE AS A TABLE
# ---------------------------------------------------------------------------------------
OLD_CASCADE = '''    if kc:
        parts = [("%s %s" % (k.replace("_", " "), v)) for k, v in kc.items()
                 if isinstance(v, int)]
        s.paras.append(("k is reported at every stage rather than as a single number: %s."
                        % "; ".join(parts), ["k_cascade"]))'''

NEW_CASCADE = '''    if kc:
        # A TABLE, NOT A SENTENCE. This was `key.replace("_", " ")` joined with semicolons,
        # which produced "k0 surfaced 56; k2 role located 56; k3 experimental 49; k4
        # comparator 1; k5 background 6; kNA not assessable 0" -- a table flattened into
        # prose, and the single worst section of the SGLT2 page a reader called computer
        # code. EVERY COUNT BELOW IS THE SAME NUMBER; only the rendering changed. A key
        # with no worded label keeps its raw form rather than being silently dropped.
        rows = [[_CASCADE_LABELS.get(k, k.replace("_", " ")), str(v)]
                for k, v in kc.items() if isinstance(v, int)]
        s.tables.append((
            "Records at every stage of screening. k is reported at each stage rather than "
            "as a single number, because each stage is what the instrument at that stage "
            "could actually decide.",
            ["Stage", "Records"], rows, ["k_cascade"]))'''

CASCADE_LABELS = '''
# WORDED ROW LABELS FOR THE SCREENING CASCADE. `k3_experimental` is a key; "Named the
# intervention rather than a comparator or background therapy" is what it means. A key
# absent from this map renders with underscores replaced -- degraded, not dropped, because
# a stage silently missing from the table would understate the screening.
_CASCADE_LABELS = {
    "k0_surfaced": "Records surfaced by the executed searches",
    "k1_deduplicated": "After removing duplicate registrations",
    "k2_role_located": "Records where the topic drug's role in the trial could be located",
    "k3_experimental": "Records where the topic drug is the randomised intervention",
    "k4_comparator": "Records where the topic drug is the comparator instead",
    "k5_background": "Records where the topic drug is background therapy in both arms",
    "kNA_not_assessable": "Records where the role could not be decided either way",
    "k_included_in_object": "Trials included in this review",
    "k_unscreened_remainder": "Surfaced records not yet screened",
    "k3_corrected_from": "Earlier value of the intervention count, before correction",
}

'''


# ---------------------------------------------------------------------------------------
# 3. THE ESTIMAND KEY IS NOT A NOUN A READER KNOWS
# ---------------------------------------------------------------------------------------
OLD_SYNTH = '''        if model and est:
            s.paras.append(("For %s, a %s model was fitted with the %s estimator."
                            % (oid, model, est),'''
NEW_SYNTH = '''        if model and est:
            # THE OUTCOME'S NAME, NOT ITS KEY. This read "For cvdeath_or_whf_first, a random
            # model was fitted" -- a database key as the subject of an English sentence. The
            # key is still reachable: it is in this paragraph's source list.
            s.paras.append(("For %s, a %s model was fitted with the %s estimator."
                            % (_outcome_words(obj, oid), model, est),'''

OUTCOME_WORDS = '''
def _outcome_words(obj, oid):
    """The outcome's registered name, falling back to the key made readable.

    NEVER SILENTLY EMPTY. A missing name degrades to the key with underscores replaced,
    which is worse prose and is still true; returning "" would delete the subject of the
    sentence.
    """
    for o in (obj.get("outcomes") or []):
        if isinstance(o, dict) and o.get("id") == oid:
            nm = (o.get("name") or "").strip()
            if nm:
                return nm[0].lower() + nm[1:] if nm[0].isupper() else nm
    return oid.replace("_", " ")

'''


# ---------------------------------------------------------------------------------------
# 4. I-SQUARED AND TAU-SQUARED, GLOSSED
# ---------------------------------------------------------------------------------------
OLD_HET = '''            ht = "Between-trial heterogeneity was I-squared %s%%" % disp(het["i2"])
            for extra, label in (("tau2", "tau-squared"), ("q", "Q"), ("df", "degrees of "
                                                                      "freedom")):
                if het.get(extra) is not None:
                    ht += ", %s %s" % (label, disp(het[extra]))
                    hf.append("results.by_outcome.%s.heterogeneity.%s" % (oid, extra))
            ht += "."'''

NEW_HET = '''            # GLOSSED, NOT DROPPED. Every number here is the number that was there.
            # "I-squared 0%, tau-squared 0, Q 0.384, degrees of freedom 2" is four
            # statistics and no sentence; a reader who does not already know what they are
            # cannot use them, and a reader who does loses nothing by being told.
            _i2 = disp(het["i2"])
            ht = ("The trials' results were %s consistent with one another: I-squared, the "
                  "share of the variation between them that is more than chance alone "
                  "would produce, was %s%%" % (_i2_words(het["i2"]), _i2))
            _tail = []
            for extra, label in (
                    ("tau2", "the estimated variance of the true effects between trials "
                             "(tau-squared) was"),
                    ("q", "the heterogeneity test statistic Q was"),
                    ("df", "on degrees of freedom")):
                if het.get(extra) is not None:
                    _tail.append("%s %s" % (label, disp(het[extra])))
                    hf.append("results.by_outcome.%s.heterogeneity.%s" % (oid, extra))
            if _tail:
                ht += "; " + ", ".join(_tail)
            ht += "."'''

I2_WORDS = '''
def _i2_words(i2):
    """A plain-English band for I-squared. Handbook 10.10.2 gives overlapping ranges and
    warns against a mechanical reading, so the words are DELIBERATELY loose and the number
    is always printed beside them. This describes; it does not grade."""
    try:
        v = float(i2)
    except (TypeError, ValueError):
        return "of unstated"
    if v < 30:
        return "closely"
    if v < 60:
        return "moderately"
    if v < 75:
        return "loosely"
    return "poorly"

'''


def main():
    dry = "--apply" not in sys.argv
    b = read(BUILD)
    p = read(PROJ)

    b = sub_once(b, OLD_LEDE, NEW_LEDE, "the Paper panel's opening sentence")
    b = sub_once(b, OLD_RENDER, NEW_RENDER, "the paragraph/table/refusal renderer")

    if "_CASCADE_LABELS" not in p:
        anchor = "def disp(x, sig=3):"
        if anchor not in p:
            sys.exit("REFUSED: cannot locate an insertion point in paper_projector.py.")
        p = p.replace(anchor, CASCADE_LABELS.lstrip("\\n") + OUTCOME_WORDS.lstrip("\\n")
                      + I2_WORDS.lstrip("\\n") + anchor, 1)
    p = sub_once(p, OLD_CASCADE, NEW_CASCADE, "the k-cascade sentence")
    p = sub_once(p, OLD_SYNTH, NEW_SYNTH, "the model/estimator sentence")
    p = sub_once(p, OLD_HET, NEW_HET, "the heterogeneity sentence")

    print("build_tabbed.py   : lede + provenance footnote column")
    print("paper_projector.py: k-cascade table, outcome names, glossed heterogeneity")
    if dry:
        print("DRY RUN -- pass --apply to write")
        return
    write(BUILD, b)
    write(PROJ, p)
    print("wrote both")


if __name__ == "__main__":
    main()
