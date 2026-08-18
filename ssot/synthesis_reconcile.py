"""Reconciling a published synthesis to registration IDs. The three things scaling needed.

1. TABLE SELECTION BY STRUCTURE, NOT BY CAPTION -- AND IT IS STILL NOT SUFFICIENT.
   Caption matching picked a THERAPIES table on PMC13466188. The structural replacement
   tests for PER-ROW BIBLIOGRAPHIC CROSS-REFERENCES, on the reasoning that an
   included-studies table has them and a therapies table does not.

   IT PICKS THE SAME WRONG TABLE. `Disease-modifying therapies for ATTRv-PN approved in
   Germany` scores 6/6 rows cited, because each THERAPY row cites its own pivotal trial.
   The property is real and it does not discriminate: presence of per-row citations is
   necessary for an included-studies table and not sufficient.

   THIS IS NOT FIXED. `select_included_table` currently returns a table that must not be
   used for a collapse claim, and any caller must treat its output as a CANDIDATE requiring
   confirmation, not as the included set. Scaling is blocked on this and no volume run may
   use it. The next attempt should test what the ROWS ARE -- one row per STUDY, carrying a
   sample size and an effect or an arm count -- rather than how they are cited.

2. A FALLBACK THAT CARRIES ITS EVIDENCE LEVEL.
   Rows with no <xref> can still be resolved from their own text -- first author and year --
   through the same two hops. That is WEAKER, and it says so, the way the identity
   classifier labels an arm-label match as weak evidence rather than silently equating it
   with an intervention-record match.

3. PUBLICATION TYPE FROM SEVERAL SIGNALS, WITH UNCATEGORISED KEPT WHOLE.
   35 of 75 landed in OTHER on one article. That is not a coverage gap in one field so much
   as reliance on one field. Registration presence, PublicationType, and the abstract's own
   design language are independent signals. UNCATEGORISED remains its own state and is never
   distributed across the others to make a rate look complete.
"""
import collections
import re

TAGS = re.compile(r"<[^>]+>")
TABLE_WRAP = re.compile(r"<table-wrap\b.*?</table-wrap>", re.S)
ROW = re.compile(r"<tr\b.*?</tr>", re.S)
XREF_BIBR = re.compile(r'<xref[^>]*ref-type="bibr"[^>]*rid="([^"]+)"')
CAPTION = re.compile(r"<caption\b.*?</caption>", re.S)

STRONG, WEAK = "strong", "weak"


# --------------------------------------------------------------------------- 1
def _data_rows(table):
    """Rows that are not the header. A <thead> row is not a study."""
    body = re.search(r"<tbody\b.*?</tbody>", table, re.S)
    return ROW.findall(body.group(0)) if body else ROW.findall(table)[1:]


def select_included_table(xml, min_cited_fraction=0.5, min_rows=3):
    """Return (table, evidence) or (None, reason). Structural test, then refuse on ties."""
    qualifying = []
    for t in TABLE_WRAP.findall(xml):
        rows = _data_rows(t)
        if len(rows) < min_rows:
            continue
        cited = sum(1 for r in rows if XREF_BIBR.search(r))
        frac = cited / len(rows)
        if frac >= min_cited_fraction:
            cap = CAPTION.search(t)
            qualifying.append((t, len(rows), cited, frac,
                               TAGS.sub(" ", cap.group(0)).strip()[:70] if cap else ""))

    if not qualifying:
        return None, ("NOT-ASSESSABLE: no table has per-row bibliographic cross-references. "
                      "The included-studies table may exist and still be unreadable this "
                      "way -- this is not evidence that the synthesis lacks one.")
    if len(qualifying) > 1:
        return None, ("REFUSED: %d tables qualify structurally (%s). Choosing between them "
                      "is exactly how a therapies table was selected before."
                      % (len(qualifying), "; ".join(q[4][:34] for q in qualifying)))
    t, n, cited, frac, cap = qualifying[0]
    return t, f"{cited}/{n} rows ({frac:.0%}) carry a bibliographic xref; caption {cap!r}"


# --------------------------------------------------------------------------- 2
_AUTHOR_YEAR = re.compile(r"([A-Z][a-z]{2,})\s*(?:et al\.?|,)?[^0-9]{0,40}((?:19|20)\d{2})")


def row_fallback_query(row_xml):
    """First author + year from the row's own text. WEAK, and labelled so."""
    text = TAGS.sub(" ", row_xml)
    text = re.sub(r"\s+", " ", text).strip()
    m = _AUTHOR_YEAR.search(text)
    if not m:
        return None, "no author-year pattern in row text"
    author, year = m.group(1), m.group(2)
    return (f"{author}[Author] AND {year}[dp]",
            f"WEAK: row text only, author={author!r} year={year}")


# --------------------------------------------------------------------------- 3
_DESIGN_RCT = re.compile(
    r"\b(randomi[sz]ed|randomly assigned|double[- ]blind|placebo[- ]controlled|"
    r"parallel[- ]group|crossover trial)\b", re.I)
_DESIGN_OBS = re.compile(
    r"\b(retrospective|prospective cohort|observational|registry study|case[- ]control|"
    r"real[- ]world)\b", re.I)
_NOT_STUDY = re.compile(r"\b(we review|this review|narrative review|consensus|guideline)\b", re.I)

CLASSES = ("REGISTERED_TRIAL", "TRIAL_UNREGISTERED_ERA", "TRIAL_GENUINELY_UNRESOLVED",
           "NOT_A_TRIAL", "UNCATEGORISED")


def classify_record(rec, unregistered_before=2005):
    """Several independent signals. Returns (class, evidence). UNCATEGORISED stays whole."""
    ncts = rec.get("ncts") or []
    year = rec.get("year")
    pts = [t.lower() for t in (rec.get("pubtypes") or [])]
    abstract = rec.get("abstract") or ""
    journal = (rec.get("journal") or "").lower()

    if ncts:
        return "REGISTERED_TRIAL", f"carries registration {ncts[0]}"

    sig = []
    if any("review" in t or "meta-analysis" in t or "guideline" in t for t in pts):
        sig.append("pubtype=review/meta/guideline")
    if any("comment" in t or "editorial" in t or "letter" in t for t in pts):
        sig.append("pubtype=comment/editorial/letter")
    if _NOT_STUDY.search(abstract):
        sig.append("abstract states it is a review/consensus")
    if "review" in journal:
        sig.append("journal name contains 'review'")
    if sig:
        return "NOT_A_TRIAL", "; ".join(sig)

    trial_sig = []
    if any("clinical trial" in t or "randomized" in t for t in pts):
        trial_sig.append("pubtype=clinical trial")
    if _DESIGN_RCT.search(abstract):
        trial_sig.append("abstract carries randomised-design language")
    if _DESIGN_OBS.search(abstract):
        trial_sig.append("abstract carries observational-design language")
    if trial_sig:
        if year and year < unregistered_before:
            return "TRIAL_UNREGISTERED_ERA", f"{'; '.join(trial_sig)}; published {year}"
        return "TRIAL_GENUINELY_UNRESOLVED", "; ".join(trial_sig)

    if year and year < unregistered_before:
        return "TRIAL_UNREGISTERED_ERA", f"published {year}, before registration was required"

    # NOT distributed into the others to flatter a rate.
    return "UNCATEGORISED", (f"no registration, no decisive pubtype, no design language"
                             f"{'' if abstract else ', and no abstract retrieved'}")


def tally(classified):
    c = collections.Counter(v[0] for v in classified.values())
    return {k: c.get(k, 0) for k in CLASSES}


def rate_is_quotable(counts, max_uncategorised_fraction=0.25):
    """A denominator whose biggest class is 'other' is not a denominator."""
    total = sum(counts.values())
    if not total:
        return False, "no records"
    frac = counts.get("UNCATEGORISED", 0) / total
    if frac > max_uncategorised_fraction:
        return False, (f"UNCATEGORISED is {frac:.0%} of {total}; no rate may be quoted from "
                       f"this denominator")
    return True, f"UNCATEGORISED {frac:.0%} of {total}"
