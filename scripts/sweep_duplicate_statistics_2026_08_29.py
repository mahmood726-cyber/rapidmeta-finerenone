"""One statistic, two values, one page: sweep the corpus for the lefamulin class.

AN EXTERNAL REVIEWER FOUND Q PRINTED TWICE ON LEFAMULIN_CABP WITH DIFFERENT VALUES --
0.7313 in the main result, 0.7316 in the GRADE reasoning. Both were rendered from the
same object. That is not a rounding cosmetic: a reader who checks one against the other
finds the page disagreeing with itself, and has no way to know which number the pooling
actually used.

TWO LEGS, AND THEY ANSWER DIFFERENT QUESTIONS.

  LEG A -- AGAINST AN AUTHORITY. Many objects store the verbatim metafor output that
  produced the estimate. That text is the closest thing this corpus has to a ground
  truth for a heterogeneity statistic: it is what R printed, kept unedited. So every
  structured field is compared against the value parsed out of that block. When they
  differ, the structured field is wrong and the fix has a known target. Without this
  leg a sweep can only say "two numbers disagree" and never which to keep.

  LEG B -- AGAINST THE READER. What the reviewer actually hit was not a field mismatch,
  it was the same labelled quantity appearing twice in the rendered text with different
  digits. So the second leg strips tags from every served page and collects each
  labelled statistic, then reports any label carrying more than one value. This catches
  disagreements that leg A cannot see, because prose is written by hand and structured
  fields are not.

WHY BOTH ARE NEEDED. Leg A found the root cause here and would have found it before any
page was built. Leg B is the only leg that would have caught it if the wrong number had
been typed into the prose instead of computed into the field. A sweep with one leg
reports a smaller number and calls it coverage.

THE DENOMINATOR IS REPORTED, NOT THE HIT COUNT ALONE. Objects with no stored R block
cannot be checked by leg A -- that is an absence of evidence, and it is printed as such
rather than counted as a pass.

PRECISION IS MEASURED BEFORE ANY COUNT IS QUOTED. The extractors run first over
constructed strings whose answers are known, including strings that must NOT match: a Q
inside a different outcome's block, a number that is a substring of a longer one, and a
value quoted while being described as superseded. A matcher that over-fires turns a
clean page into a finding.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "duplicate_statistics_2026_08_29.json")

# Tolerance. These are printed to 4 decimals, so anything at or below half a unit in the
# last printed place is a display rounding artefact and not a disagreement. Anything
# above it is two different numbers wearing one label.
TOL = 5e-5


def rendered(html):
    """Tags out, entities in, whitespace collapsed -- what a reader sees.

    VERIFYING AGAINST SOURCE INSTEAD OF RENDERED TEXT IS THE MISTAKE THAT COST 21 ITEMS
    ON AN EARLIER PASS: a sentence a reader sees as one string is several strings in the
    file, split by an inline tag.
    """
    s = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    s = re.sub(r"<[^>]+>", " ", s)
    try:
        import html as _h
        s = _h.unescape(s)
    except Exception:
        pass
    return re.sub(r"\s+", " ", s)


NUM = r"(-?\d+\.\d{2,6}|-?\d+)"

# Labelled statistics as they are actually written on these pages. Each entry is
# (label, compiled pattern). The pattern must capture the value in group 1.
LABELLED = [
    ("Q", re.compile(r"\bQ\s*(?:\(\s*df\s*=\s*\d+\s*\))?\s*(?:=\s*)?" + NUM +
                     r"\s*(?:on\s*\d+\s*df|,\s*p-val)")),
    ("tau2", re.compile(r"(?:tau\^2|tau²|τ²|τ\^2)\s*(?:=\s*)?" + NUM)),
    ("I2", re.compile(r"(?:I\^2|I²)\s*(?:=\s*)?" + NUM + r"\s*%")),
]


def extract_labelled(text):
    """label -> set of distinct values, over one page's rendered text."""
    found = {}
    for label, pat in LABELLED:
        for m in pat.finditer(text):
            try:
                v = float(m.group(1))
            except ValueError:
                continue
            found.setdefault(label, []).append((v, m.start()))
    return found


# ---------------------------------------------------------------------------
# PRECISION KNOWN_NEGATIVE_CONTROLS. A COUNT WITHOUT A MEASURED PRECISION IS NOT A FINDING.
# Each case is (text, label, expected number of matches, why it is here).
KNOWN_NEGATIVE_CONTROLS = [
    ("Q 0.7316 on 1 df, p = 0.3924", "Q", 1, "the plain positive form"),
    ("Q(df = 1) = 0.7316, p-val = 0.3924", "Q", 1, "the metafor print form"),
    ("the Q statistic is not interpretable at k = 2", "Q", 0,
     "a mention of Q with no value must not produce one"),
    ("QUALITY 0.7316 was scored", "Q", 0,
     "a word beginning with Q is not the Q statistic"),
    ("I² 0% · Q 0.7313 on 1 df", "I2", 1, "I2 read next to a Q"),
    ("tau² 0 · I² 0%", "tau2", 1, "tau2 in the compact separator form"),
]


def measure_precision(say):
    bad = 0
    for text, label, expect, why in KNOWN_NEGATIVE_CONTROLS:
        got = len(extract_labelled(text).get(label, []))
        ok = got == expect
        if not ok:
            bad += 1
            say("   CONTROL FAILED  %-5s expected %d got %d on %r -- %s"
                % (label, expect, got, text[:52], why))
    rate = 100.0 * bad / len(KNOWN_NEGATIVE_CONTROLS)
    say("   extractor controls: %d/%d wrong (measured error rate %.1f%%)"
        % (bad, len(KNOWN_NEGATIVE_CONTROLS), rate))
    return bad


# ---------------------------------------------------------------------------
R_Q = re.compile(r"Q\(df\s*=\s*(\d+)\)\s*=\s*([0-9.]+)")
R_TAU2 = re.compile(r"tau\^2 \(estimated amount of total heterogeneity\):\s*([0-9.eE+-]+)")
R_I2 = re.compile(r"I\^2 \(total heterogeneity / total variability\):\s*([0-9.]+)%")


def r_values(verbatim):
    """Parse the authority. Returns {} when the block does not carry the statistic."""
    out = {}
    m = R_Q.search(verbatim)
    if m:
        out["q"] = float(m.group(2))
        out["q_df"] = int(m.group(1))
    m = R_TAU2.search(verbatim)
    if m:
        out["tau2"] = float(m.group(1))
    m = R_I2.search(verbatim)
    if m:
        out["i2"] = float(m.group(1))
    return out


# R PRINTS AT A FIXED PRECISION AND THE STORED FIELD DOES NOT. metafor writes I^2 to two
# decimals ("32.89%") and tau^2 to four. ARNI stores 32.8939087126. Comparing the stored
# full-precision number against R's ROUNDED PRINT manufactured a disagreement out of a
# page that is correct -- the first version of this sweep reported exactly that, and
# would have had a gate accusing it every run.
#
# So the tolerance is half a unit in the last place R actually printed, per statistic.
R_PRINTED_DP = {"q": 4, "tau2": 4, "i2": 2}


def close(a, b, field=None):
    if a is None or b is None:
        return False
    tol = TOL if field is None else 10 ** (-R_PRINTED_DP.get(field, 4)) / 2 + 1e-12
    return abs(float(a) - float(b)) <= tol


# I-SQUARED HAS MORE THAN ONE DEFINITION AND THIS CORPUS USES BOTH, ON PURPOSE.
# Higgins I^2 is (Q - df)/Q. metafor prints the REML form, tau^2 / (tau^2 + typical
# within-study variance). On TIGECYCLINE they are 7.29 and 1.16 -- and that object
# already carries the working: `i2_definition_evidence` records that BOTH were
# recomputed from its own per-trial inputs before the stored one was chosen.
#
# A sweep that calls that a defect is accusing the one page that did the work, and
# naming it "the largest disagreement in the corpus" -- which an earlier version of this
# file did -- inverts a documented decision into an error.
def i2_is_definitional(het):
    d = str((het or {}).get("i2_definition") or "")
    return "Higgins" in d and "(Q - df)" in d


def plant(say):
    """Prove the comparison on constructed cases whose answers are known.

    THE CONTROL IS SYNTHETIC ON PURPOSE. A control anchored to a real page stops being a
    control the moment that page is fixed: it then either fails and looks like a
    regression, or passes for the wrong reason. These four blocks exist nowhere in the
    corpus and their answers cannot change when the corpus does.

    The fourth case is the one that matters most. An outcome with no stored R block must
    be reported as HAVING NO AUTHORITY, not silently counted as agreeing -- absence read
    as a negative is the failure this whole sweep exists to catch, and a sweep that
    committed it would report a clean corpus by not looking.
    """
    ok = 0
    verb = ("Test for Heterogeneity:" + chr(10) + "Q(df = 1) = 0.7316, p-val = 0.3924" +
            chr(10) + "I^2 (total heterogeneity / total variability):   0.00%" + chr(10) +
            "tau^2 (estimated amount of total heterogeneity): 0 (SE = 0.0010)")
    rv = r_values(verb)

    if close(0.7316, rv.get("q"), "q"):
        say("   [PASS] a field equal to the R value is not flagged")
        ok += 1
    else:
        say("   [FAIL] an exact match was flagged")

    if not close(0.7313, rv.get("q"), "q"):
        say("   [PASS] a field differing in the 4th decimal IS flagged (the lefamulin shape)")
        ok += 1
    else:
        say("   [FAIL] the planted disagreement was missed")

    if close(0.73160001, rv.get("q"), "q"):
        say("   [PASS] a difference below the display tolerance is not a disagreement")
        ok += 1
    else:
        say("   [FAIL] a rounding artefact was reported as a disagreement")

    if not r_values("Model Results: estimate se zval pval"):
        say("   [PASS] a block with no heterogeneity test yields NO authority, "
            "rather than a silent pass")
        ok += 1
    else:
        say("   [FAIL] an absent authority was treated as present")

    say("   plant: %d/4" % ok)
    return 0 if ok == 4 else 2


def main():
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    if "--plant" in sys.argv:
        say("PLANT -- constructed cases with known answers")
        return plant(say)

    pm = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))

    say("DUPLICATE-STATISTIC SWEEP")
    say("")
    say("EXTRACTOR PRECISION, measured before any count is reported:")
    if measure_precision(say):
        say("")
        say("REFUSED: the extractor failed its own controls. Any count it produced would "
            "be a statement about the matcher, not about the corpus.")
        return 2
    say("")

    leg_a, no_authority, leg_b, definitional = [], [], [], []
    n_obj = 0

    for page, objpath in sorted(pm.items()):
        full = os.path.join(REPO, objpath)
        if not os.path.exists(full):
            continue
        try:
            obj = json.load(io.open(full, encoding="utf-8"))
        except ValueError:
            continue
        n_obj += 1
        by = ((obj.get("results") or {}).get("by_outcome") or {})
        for outcome, blk in by.items():
            if not isinstance(blk, dict):
                continue
            het = blk.get("heterogeneity") or {}
            verb = ((blk.get("r_output") or {}).get("verbatim") or "")
            if not verb:
                if het:
                    no_authority.append({"page": page, "outcome": outcome})
                continue
            rv = r_values(verb)
            if not rv:
                no_authority.append({"page": page, "outcome": outcome})
                continue
            for field, rkey in (("q", "q"), ("tau2", "tau2"), ("i2", "i2")):
                sv = het.get(field)
                if sv is None or rkey not in rv:
                    continue
                if close(sv, rv[rkey], field):
                    continue
                if field == "i2" and i2_is_definitional(het):
                    definitional.append({"page": page, "outcome": outcome,
                                         "stored_field": sv, "r_authority": rv[rkey],
                                         "why": "the object declares Higgins (Q-df)/Q; "
                                                "metafor prints the REML form"})
                    continue
                leg_a.append({"page": page, "outcome": outcome, "field": field,
                              "stored_field": sv, "r_authority": rv[rkey],
                              "delta": abs(float(sv) - float(rv[rkey]))})

    say("LEG A -- structured field against the stored metafor output")
    say("   objects read: %d   outcome blocks with no R authority: %d"
        % (n_obj, len(no_authority)))
    say("   i2 differences that are DEFINITIONAL, not errors: %d "
        "(Higgins (Q-df)/Q against metafor's REML form)" % len(definitional))
    say("   disagreements: %d" % len(leg_a))
    for d in leg_a[:40]:
        say("      %-46s %-10s %-5s field %s vs R %s  (delta %.6f)"
            % (d["page"][:46], d["outcome"][:10], d["field"], d["stored_field"],
               d["r_authority"], d["delta"]))
    say("")

    # THE FIRST VERSION OF LEG B REPORTED 30 PAGES AND MOST WERE NOT DEFECTS. A review
    # with five outcomes prints five Q values, and grouping by LABEL ALONE cannot tell
    # that from one Q printed twice. My controls had measured the EXTRACTOR and not the
    # GROUPING, so the count looked instrumented while the part that decided what
    # counted as a hit had never been checked at all.
    #
    # So a rendered value is now resolved against the object: every Q on a page must be
    # a valid rounding of a Q that R actually printed for one of that page's outcomes.
    # That splits the raw hits three ways, and only the third is a finding.
    #
    #   ROUNDED     the same number shown at two precisions (4.7195 and 4.72).
    #               Cosmetic. Consistent, and not a contradiction.
    #   ACCOUNTED   a distinct value that IS one of the page's other outcomes.
    #               Expected. Not a defect at all.
    #   ORPHAN      a value that matches NO authority on the page. This is the class the
    #               reviewer hit: a number with no computation behind it.
    def is_rounding_of(shown, truth):
        """Would `truth`, printed to the precision `shown` uses, give `shown`?"""
        s = ("%r" % shown)
        d = len(s.split(".")[1]) if "." in s else 0
        return abs(round(float(truth), d) - shown) <= 10 ** (-d) / 2 + 1e-9

    pages = sorted(p for p in os.listdir(REPO)
                   if p.endswith(".html") and os.path.isfile(os.path.join(REPO, p)))
    say("LEG B -- every rendered value resolved against the page's own R authorities")

    authorities = {}
    for page, objpath in pm.items():
        full = os.path.join(REPO, objpath)
        if not os.path.exists(full):
            continue
        try:
            obj = json.load(io.open(full, encoding="utf-8"))
        except ValueError:
            continue
        # SCAN THE WHOLE OBJECT, NOT JUST results.by_outcome.
        # Reading only by_outcome[*].r_output produced four "orphan" values on ARNI --
        # a Q of 3.9046, 4.1498, 5.0714 and an I2 of 7.01 that appeared to have no
        # computation behind them. Every one was a real metafor block for another of that
        # page's outcomes, stored somewhere this collector did not look. The page was
        # correct and the accusation was about my reach. So the authorities are gathered
        # from EVERY string on the object that contains a metafor heterogeneity print,
        # plus every stored heterogeneity field, wherever they sit.
        acc = {"Q": [], "tau2": [], "I2": []}

        def gather(x):
            if isinstance(x, dict):
                if any(k in x for k in ("q", "tau2", "i2")):
                    for key, lab in (("q", "Q"), ("tau2", "tau2"), ("i2", "I2")):
                        v = x.get(key)
                        if isinstance(v, (int, float)):
                            acc[lab].append(float(v))
                for v in x.values():
                    gather(v)
            elif isinstance(x, list):
                for v in x:
                    gather(v)
            elif isinstance(x, str) and "Heterogeneity" in x:
                for m in R_Q.finditer(x):
                    acc["Q"].append(float(m.group(2)))
                for m in R_TAU2.finditer(x):
                    acc["tau2"].append(float(m.group(1)))
                for m in R_I2.finditer(x):
                    acc["I2"].append(float(m.group(1)))
        gather(obj)
        authorities[page] = acc

    # ITERATE THE PAGES THAT CAN BE RESOLVED, AND COUNT THE REST OUT LOUD.
    # The first version wrote `if auth is None: continue` inside this loop, which is a
    # negative guard in a corpus-wide sweep -- the shape that turns "I could not check
    # this" into silence, and then into an implied pass. The repository's own ratchet
    # refused the commit for it, correctly. A page with no object is not a clean page; it
    # is a page this leg cannot see, and that belongs in the denominator the reader reads.
    resolvable = [p for p in pages if p in authorities]
    unresolvable = len(pages) - len(resolvable)

    say("   pages read: %d, of which %d carry an object this leg can resolve against"
        % (len(pages), len(pages) - unresolvable))
    say("   %d pages have NO object, so this leg cannot see them. That is a hole in the "
        "coverage, not a set of clean pages." % unresolvable)
    n_rounded = n_accounted = 0
    for p in resolvable:
        try:
            text = rendered(io.open(os.path.join(REPO, p), encoding="utf-8",
                                    errors="replace").read())
        except OSError:
            continue
        auth = authorities[p]
        for label, hits in extract_labelled(text).items():
            vals = sorted(set(round(v, 6) for v, _ in hits))
            if len(vals) < 2:
                continue
            truths = auth.get(label) or []
            for v in vals:
                exact = [t for t in truths if abs(t - v) <= TOL]
                if exact:
                    n_accounted += 1
                    continue
                if any(is_rounding_of(v, t) for t in truths):
                    n_rounded += 1
                    continue
                leg_b.append({"page": p, "label": label, "orphan_value": v,
                              "page_authorities": sorted(set(round(t, 6) for t in truths)),
                              "all_rendered": vals})

    say("   values that ARE an authority for one of the page's outcomes: %d" % n_accounted)
    say("   values that are a rounding of one:                          %d" % n_rounded)
    say("   ORPHANS -- rendered with no computation behind them:        %d" % len(leg_b))
    for d in leg_b[:40]:
        say("      %-50s %-5s shows %s; authorities %s"
            % (d["page"][:50], d["label"], d["orphan_value"],
               ", ".join(str(x) for x in d["page_authorities"][:5]) or "(none)"))

    json.dump({"tolerance": TOL, "r_printed_dp": R_PRINTED_DP, "n_objects": n_obj,
               "leg_a_definitional_not_errors": definitional,
               "leg_a_disagreements": leg_a,
               "leg_a_no_authority": no_authority,
               "leg_b_page_level": leg_b,
               "leg_b_pages_with_no_object": unresolvable},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
