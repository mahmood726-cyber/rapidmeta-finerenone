"""An abstract claiming a database search the Methods section says was never run.

THE WORST OF THE 10 CONFIRMED HIGH-SEVERITY FINDINGS, because it is the only one where the
page asserts something FALSE about its own method rather than something incomplete.

AZILSARTAN_CLD_VS_OLM_HCTZ, adjudicated CONFIRMED / HIGH:

    abstract:  "ClinicalTrials.gov API v2 and PubMed (ncbi e-utilities esearch) were
                searched"
    methods:   "No bibliographic search for primary trials was run"

Both sentences are on the same page. One of them is not true. And it is the abstract -- the
part a reader meets first and the only part most readers read -- that carries the claim.

WHY THIS MATTERS MORE THAN THE OTHER NINE. The corpus panel found that 118 of 145
desk-rejections quote the Methods sentence, "No bibliographic search for primary trials was
run". That disclosure is the single most expensive thing this corpus says about itself, and
we have been treating it as the honest cost of a deliberate method. If some pages ALSO claim
in the abstract that PubMed was searched, then the corpus is not paying that cost
consistently -- it is disclosing in one section and claiming the opposite in another, which
is worse than either alone.

THE PANEL NAMED ONE PAGE. That is reviewer reach and nothing more, exactly as "five pages"
turned out to be fifteen for the i2 defect. This measures every page.

AND IT IS CONTROLLED AGAINST OVER-FLAGGING, which is now the failure mode of record: four
separate instruments on 2026-08-25 manufactured defect classes that did not exist. The
positive control is the page the adjudicator confirmed. The negatives are the two legitimate
shapes -- a page that ran a real search and says so, and a page that says only that it did
not search.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls

PAPER = re.compile(r'id="pn-paper"(.*?)(?:id="pn-[a-z]|<!--\s*end-paper)', re.S)
ABSTRACT = re.compile(r"(?is)>\s*Abstract\s*<.{0,24000}")

# The abstract asserting that a bibliographic database was searched.
#
# The inline (?i) is written ONCE and only at the start; a second one mid-pattern is a
# PatternError on Python 3.11+, which is how the first version of this file failed to
# compile at all. The flag belongs in the re.I argument, not repeated in the string.
CLAIMS_SEARCH = re.compile(
    r"(pubmed|medline|embase|cochrane central|e-?utilities|esearch)[^.]{0,120}"
    r"(were|was)\s+searched"
    r"|(we|the authors)\s+searched[^.]{0,80}(pubmed|medline|embase|cochrane)", re.I)

# The page stating plainly that no bibliographic search happened.
DENIES_SEARCH = re.compile(
    r"no bibliographic search[^.]{0,60}(was|were)?\s*run"
    r"|no bibliographic search for primary trials", re.I)


def text_of(frag):
    frag = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", frag)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", frag))


def not_executed_names(objpath):
    """Source names the OBJECT records as never searched. The authority, not the prose."""
    try:
        o = json.load(io.open(objpath, encoding="utf-8"))
    except Exception:
        return None
    dbs = (o.get("search") or {}).get("databases") or []
    items = dbs.values() if isinstance(dbs, dict) else dbs
    out = []
    for d in items:
        if not isinstance(d, dict):
            continue
        q = str(d.get("query_as_executed") or "").upper()
        un = str(d.get("what_is_unexamined") or "").upper()
        if "NOT EXECUTED" in q or ("NO " in un and "SEARCH WAS RUN" in un):
            nm = str(d.get("database") or d.get("name") or "").split("--")[0].strip()
            if nm:
                out.append(nm)
    return out


def _first_word(name):
    """'PubMed (NCBI E-utilities esearch)' -> 'pubmed'. The token an abstract would use."""
    return re.split(r"[ (]", name.strip())[0].lower()


def examine(html, objpath=None):
    """(has_defect, abstract_claim, what_the_object_says).

    THE FIRST VERSION MATCHED PROSE AGAINST PROSE and reported 5 pages. Three were real; two
    -- both APIXABAN_VTE pages -- named PubMed in the abstract and had GENUINELY RUN a PubMed
    search, while separately stating that no bibliographic search was run to find the primary
    TRIALS. Both sentences were true and about different things. Prose cannot tell those
    apart, so this now asks the OBJECT which sources were never searched, and flags a page
    only when the abstract claims one of THOSE was searched.
    """
    m = PAPER.search(html)
    if not m:
        return None, "", ""
    panel = m.group(1)
    am = ABSTRACT.search(panel)
    abstract = text_of(am.group(0)) if am else text_of(panel)[:6000]
    if not CLAIMS_SEARCH.search(abstract):
        return False, "", ""
    if objpath is None:
        return False, "", ""
    never = not_executed_names(objpath)
    if not never:
        return False, "", ""
    low = abstract.lower()
    for nm in never:
        tok = _first_word(nm)
        if len(tok) > 3 and tok in low:
            i = low.find(tok)
            return True, abstract[max(0, i - 90):i + 60].strip(),                 "the object records %r as never searched" % nm
    return False, "", ""


def control():
    """Positive is the adjudicated page WITH its object. Negatives are the two true shapes."""
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    page = "AZILSARTAN_CLD_VS_OLM_HCTZ_REVIEW.html"
    ppath = os.path.join(REPO, page)
    if not (os.path.exists(ppath) and page in pmap):
        raise instrument_controls.ControlFailed(
            "REFUSED: the control page or its object is missing, so the positive control "
            "could not run. NO COUNT IS PRINTED.")
    real = examine(io.open(ppath, encoding="utf-8", errors="replace").read(),
                   os.path.join(REPO, pmap[page]))[0]

    # THE SHAPE THE PROSE-ONLY VERSION GOT WRONG: named PubMed, and really ran it.
    neg_page = "APIXABAN_VTE_PROPHYLAXIS_REVIEW.html"
    neg_real = True
    if os.path.exists(os.path.join(REPO, neg_page)) and neg_page in pmap:
        neg_real = examine(
            io.open(os.path.join(REPO, neg_page), encoding="utf-8", errors="replace").read(),
            os.path.join(REPO, pmap[neg_page]))[0]

    instrument_controls.require_controls(
        "abstract-claims-a-search-the-object-says-never-ran",
        ("AZILSARTAN_CLD_VS_OLM_HCTZ_REVIEW.html, adjudicated CONFIRMED/HIGH against "
         "the object by a second family", real, True),
        ("APIXABAN_VTE_PROPHYLAXIS_REVIEW.html, which names PubMed and really ran it",
         neg_real, True))
    return True


def main():
    control()
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    hits, examined, claims_only, denies_only = [], 0, 0, 0
    for page in sorted(pmap):
        p = os.path.join(REPO, page)
        if not os.path.exists(p):
            continue
        html = io.open(p, encoding="utf-8", errors="replace").read()
        bad, a, b = examine(html, os.path.join(REPO, pmap[page]))
        if bad is None:
            continue
        examined += 1
        panel = PAPER.search(html).group(1)
        whole = text_of(panel)
        am = ABSTRACT.search(panel)
        abstract = text_of(am.group(0)) if am else whole[:6000]
        if CLAIMS_SEARCH.search(abstract):
            claims_only += 1
        if not_executed_names(os.path.join(REPO, pmap[page])):
            denies_only += 1
        if bad:
            hits.append((page, a, b))

    print()
    print("pages with a paper panel                              : %d" % examined)
    print("  abstract asserts a bibliographic database was searched: %d" % claims_only)
    print("  object records at least one source as never searched  : %d" % denies_only)
    print("  BOTH, on the same page                                : %d" % len(hits))
    print()
    for page, a, b in hits:
        print("  %s" % page)
        print("      abstract : ...%s" % " ".join(a.split())[-130:])
        print("      object   : %s" % b)
    out = os.path.join(REPO, "outputs", "search_claim_contradiction_2026_08_25.json")
    json.dump({"examined": examined, "claims": claims_only, "denies": denies_only,
               "pages": [h[0] for h in hits]},
              io.open(out, "w", encoding="utf-8"), indent=1)
    print()
    print("written: %s" % os.path.relpath(out, REPO))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
