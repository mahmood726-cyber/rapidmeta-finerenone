"""How many pooled results combine trials in MATERIALLY DIFFERENT populations?

THE QUESTION, AND WHY IT IS A NUMBER RATHER THAN A PRINCIPLE. A blind reviewer reading the
sotagliflozin draft under the med-student brief said the generator's worst act was one it
performed silently:

    "It entirely bypasses the human judgement required for meta-analysis eligibility. It
     automatically pools two very different trials just because they share a drug and a
     metric, bypassing the fundamental clinical question a reviewer must answer: SHOULD we
     combine these populations?"

SOLOIST-WHF enrolled adults with type 2 diabetes recently hospitalised for worsening heart
failure. SCORED enrolled adults with type 2 diabetes and chronic kidney disease, in whom
heart failure was NOT an entry requirement. They share a drug, a comparator and an endpoint
definition. Whether they share a QUESTION is a clinical judgement, and the generator made it
by not asking.

Whether that matters at the scale of the corpus is a different question from whether it
matters in principle, and it is the one that decides what to do:

    two pages   -> fix the pages
    thirty      -> it changes how many pages are entitled to a headline number at all

SO THIS COUNTS, IT DOES NOT ADJUDICATE. It cannot tell whether two populations are
"materially different" -- that is the very judgement being discussed. What it CAN do is find
every pool whose contributing trials describe their populations in DIFFERENT WORDS, and
report the pair so a person can read them side by side. A pool whose trials describe the
same population identically needs no judgement; every other pool needs one, and this counts
how many.

TWO SIGNALS, DELIBERATELY SEPARATED, because they mean different things:

  DIFFERING TEXT  the per-result `population` strings are not identical after normalising
                  whitespace and case. Weak on its own -- two trials can describe the same
                  patients in different words -- so it is reported as "needs a human look",
                  not as a defect.

  DIVERGENT TERMS one population names a clinical entity the other does not, drawn from a
                  list of entry criteria that CHANGE WHO IS IN THE TRIAL: a condition that
                  is required in one and absent in the other. This is the stronger signal
                  and it is the one to act on.

The second is still not a verdict. It is a shortlist.
"""
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Entry criteria whose presence or absence changes WHICH PATIENTS ARE IN THE TRIAL. Not a
# vocabulary of diseases -- a vocabulary of population-defining clauses. Each is checked as
# a whole phrase so that "heart failure" in one population and nothing comparable in the
# other is visible, rather than every shared word being counted as agreement.
_ENTRY_TERMS = (
    "heart failure", "chronic kidney disease", "kidney disease", "renal impairment",
    "type 2 diabetes", "type 1 diabetes", "diabetes", "hospitalised", "hospitalized",
    "acute", "chronic", "reduced ejection fraction", "preserved ejection fraction",
    "atrial fibrillation", "myocardial infarction", "stroke", "hypertension",
    "dialysis", "transplant", "cirrhosis", "pregnan", "paediatric", "pediatric",
    "children", "adults", "elderly", "statin", "insulin", "prior cardiovascular",
    "established cardiovascular", "cardiovascular risk", "high risk", "secondary prevention",
    "primary prevention", "treatment-naive", "treatment naive", "relapsed", "refractory",
    "metastatic", "advanced", "early", "severe", "moderate", "mild",
)


def norm(s):
    return " ".join(str(s or "").lower().split())


# A TERM CAN BE NAMED IN ORDER TO EXCLUDE IT, AND THAT IS THE OPPOSITE OF SHARING IT.
#
# SCORED's population reads "...and cardiovascular risk; heart failure was NOT an entry
# requirement". A plain substring test finds "heart failure" there and concludes SCORED and
# SOLOIST-WHF AGREE about heart failure -- when that clause is the single sharpest
# difference between them, and the whole reason the pool is worth a second look.
#
# This is the negated-counts failure recorded in my own lessons file: a pattern that matches
# a keyword without checking the preceding words silently reads "Not Randomized 1,807" as a
# randomised count. Same shape, different corpus.
#
# An excluded term is returned tagged rather than dropped, because "required here, excluded
# there" is a STRONGER divergence signal than simple absence, and collapsing it to absence
# would lose that.
_NEGATION = re.compile(
    r"(?:\bnot\b|\bno\b|\bwithout\b|\bexclud\w*|\babsent\b|\bnon-?\b)[^.;]{0,40}$")


def terms_in(s):
    t = norm(s)
    out = set()
    for w in _ENTRY_TERMS:
        for m in re.finditer(re.escape(w), t):
            before = t[max(0, m.start() - 45):m.start()]
            after = t[m.end():m.end() + 45]
            negated = bool(_NEGATION.search(before)) or bool(
                re.match(r"[^.;]{0,25}\b(?:was|were|is|are)\s+not\b", after))
            out.add(("NOT " + w) if negated else w)
    return out


def main():
    L = []

    def w(s):
        L.append(str(s))

    pooled_total = 0
    pools_one_pop = 0
    pools_text_differs = 0
    pools_terms_diverge = 0
    pools_no_pop = 0
    topics_affected = set()
    detail = []

    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        slug = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != slug + ".json":
            continue
        try:
            with io.open(p, encoding="utf-8") as fh:
                obj = json.load(fh)
        except Exception:
            continue
        # POSITIVE FORM, and `audit_exclusion_by_absence --gate` is right to insist on it:
        # iterate the blocks that ARE outcome records, rather than skipping the ones that
        # are not. A loop that defines its subject by what it discards cannot say how many
        # it was supposed to have.
        blocks = [(k, v) for k, v in
                  ((obj.get("results") or {}).get("by_outcome") or {}).items()
                  if isinstance(v, dict)]
        for oid, blk in blocks:
            pooled = blk.get("pooled") or {}
            # ONLY POOLS THAT ACTUALLY REACHED A READER AS ONE NUMBER. A withdrawn pool
            # already tells the reader it was not combined, which is the honest state this
            # measurement is asking about -- counting it as a defect would punish the very
            # behaviour under discussion.
            if pooled.get("point") is None or pooled.get("withdrawn"):
                continue
            rows = [r for r in (blk.get("per_trial") or [])
                    if isinstance(r, dict) and r.get("point") is not None]
            if len(rows) < 2:
                continue
            pooled_total += 1
            # POPULATION, OR THE REGISTRY'S OWN CONDITION LIST WHERE NO SUMMARY EXISTS.
            # Reading only `population` kept reporting 18 pools as unrecorded after the
            # registered conditions had been written onto their rows -- a measurement that
            # cannot see a fix is a measurement that will keep reporting a defect that is
            # gone, which is the same class of error as one that cannot see a defect at all.
            named = [x for x in ((norm(r.get("population"))
                                  or norm(r.get("registered_conditions")))
                                 for r in rows) if x]
            # THREE STATES, EACH COUNTED AS ITSELF. The earlier form skipped the
            # no-population case with `if not named: continue`, which reads as "these do
            # not matter" when in fact they are the LARGEST group and the reason this
            # measurement cannot answer the question for the whole corpus. 18 of 32 pools
            # record no population at all: the honest headline is "7 confirmed, 18
            # unmeasurable", and a loop that continues past them cannot say so.
            if len(named) < len(rows) or len(named) == 0:
                pools_no_pop += 1
            elif len(set(named)) == 1:
                pools_one_pop += 1
            else:
                pools_text_differs += 1
            if len(named) < 2 or len(set(named)) == 1:
                continue
            sets = [terms_in(x) for x in named]
            union, inter = set().union(*sets), set.intersection(*sets)
            diverging = union - inter
            if diverging:
                pools_terms_diverge += 1
                topics_affected.add(slug)
                detail.append((slug, oid, sorted(diverging)[:6], named))

    w("POOLED RESULTS DELIVERED AS ONE NUMBER FROM >=2 TRIALS: %d" % pooled_total)
    w("")
    w("   every contributing trial describes the SAME population : %d" % pools_one_pop)
    w("   no population recorded on the contributing rows        : %d" % pools_no_pop)
    w("   populations described DIFFERENTLY                      : %d" % pools_text_differs)
    w("      of those, naming DIVERGENT ENTRY CRITERIA           : %d" % pools_terms_diverge)
    w("")
    w("TOPICS CARRYING AT LEAST ONE SUCH POOL: %d" % len(topics_affected))
    w("")
    w("THE SHORTLIST -- each needs a person to say whether these are one question:")
    w("")
    for slug, oid, div, pops in detail:
        w("  %s / %s" % (slug, oid))
        w("     differing entry criteria: %s" % ", ".join(div))
        for i, x in enumerate(pops[:3], 1):
            w("     trial %d: %s" % (i, x[:150]))
        w("")

    out = os.path.join(REPO, "outputs", "pooling_across_populations_2026_08_24.txt")
    io.open(out, "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:60]))


main()
