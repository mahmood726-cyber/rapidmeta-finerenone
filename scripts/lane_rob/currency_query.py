# -*- coding: utf-8 -*-
"""GENERATOR COMPONENT: what has appeared since the comparator stopped looking.

THE CLINICAL POINT, AND IT IS THE ONE A GUIDELINE READER ACTUALLY HAS. A review is not wrong
because it is old; it is INCOMPLETE BY A KNOWN AMOUNT, and the amount is nameable. The doctor
in Laos reading a 2021 synthesis needs to know that its evidence stops in August 2020 and what
has landed since -- not that it is "somewhat dated".

⛔ THE DATE THAT MATTERS IS THE SEARCH DATE, NOT THE PUBLICATION DATE, and the two differ by
enough to change the answer. The dapivirine comparator was published 13 March 2021 and searched
"up to August 2020" -- quoting its own abstract. Measured from publication the gap is 5 years 5
months; measured from the search date, 6 years. Using the publication date understates every
gap in the corpus, always in the same direction.

⛔ DERIVE OR REFUSE, THREE WAYS:
  - no comparator identified            -> say so; do not call the review current
  - comparator found, search date not stated in what we hold -> say so; do NOT fall back to the
    publication date, because a plausible wrong number is worse than a stated gap
  - the query did not run                -> NOT_YET_ATTEMPTED, explicitly

⚠️ AND "NOTHING FOUND" MUST NEVER RENDER AS "NOTHING HAS CHANGED". Those are different claims:
one is about our search, the other about the world. This is the same distinction that put "no
FDA review of this product exists" on a live page, and the whole reason that sentence is now a
detector class. The renderer here is written so the wording cannot collapse the two even when
the result set is empty.
"""
import io
import json
import os
import re
import sys
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

UA = {"User-Agent": "rob-lane/1.0 (mahmood726@gmail.com)"}
EUT = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CTG = "https://clinicaltrials.gov/api/v2/studies"
TODAY = "2026-08-29"
MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December")

# States, borrowed verbatim from data_finder so the vocabulary does not fork.
OBTAINED, NOT_YET_FOUND, NOT_YET_ATTEMPTED = "OBTAINED", "NOT_YET_FOUND", "NOT_YET_ATTEMPTED"


def _json(url, timeout=60):
    return json.loads(urlopen(Request(url, headers=UA), timeout=timeout).read()
                      .decode("utf-8", "replace"))


def _text(url, timeout=60):
    return urlopen(Request(url, headers=UA), timeout=timeout).read().decode("utf-8", "replace")


def comparator_pmid(canon):
    """The DESIGNATED comparator's PMID, or None. It is never guessed.

    ⛔ THE FIRST VERSION SCAVENGED THE FIRST PMID IN THE OBJECT, and on the pilot that was
    42149895 -- an adherence review of OBSERVATIONAL studies. The component then reported a
    search date of December 2024 and "7 trials have reported since", all of it derived from a
    review that answers a different question. The page's actual comparator is the Cochrane
    review, 33719075.

    Taking the first thing that matches the shape of an identifier is not identification. Which
    published review answers the same question is a judgement, so the object must RECORD it and
    this function must refuse when it has not.
    """
    pc = canon.get("published_comparison") or {}
    pmid = pc.get("designated_comparator_pmid")
    return str(pmid) if pmid else None


def comparator_candidates(canon):
    """PMIDs the object mentions, so a refusal can name what it declined to choose between."""
    seen = []
    for m in re.finditer(r"\bPMID[: ]*(\d{6,8})\b", json.dumps(canon, ensure_ascii=False)):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def _sentence_containing(text, start, end):
    """The sentence spanning [start, end). A full stop inside 'ClinicalTrials.gov' is not one."""
    bounds = [(mm.end(), mm.start() + 1)
              for mm in re.finditer(r"(?<=[a-z0-9])\.\s+(?=[A-Z])", text)]
    s = max([0] + [b[0] for b in bounds if b[0] <= start])
    e = min([len(text)] + [b[1] for b in bounds if b[1] >= end])
    return text[s:e].strip()


def search_date(pmid):
    """The date the comparator's own text says its search stops. Quoted, never inferred."""
    try:
        x = _text("%s/efetch.fcgi?db=pubmed&retmode=xml&id=%s" % (EUT, pmid), timeout=90)
    except Exception as e:
        return {"state": NOT_YET_ATTEMPTED, "why": "%s: %s" % (type(e).__name__, str(e)[:70])}
    ab = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
                " ".join(re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", x, re.S))))
    pat = re.compile(r"(?:up to|through|until|to)\s+((?:%s)\s+\d{4})" % MONTHS, re.I)
    for m in pat.finditer(ab):
        window = ab[max(0, m.start() - 260):m.end() + 60]
        if re.search(r"search|databases|registers?|CENTRAL|MEDLINE|Embase", window, re.I):
            sent = _sentence_containing(ab, m.start(), m.end())
            # ⛔ THE QUOTE MUST CONTAIN THE DATE IT IS OFFERED AS EVIDENCE FOR.
            # Two wrong versions shipped through this line in one sitting: the first cut at the
            # period inside "ClinicalTrials.gov" and began "gov, WHO International Clinical
            # Trials Registry Platform"; the second, fixing that, walked to the wrong boundary
            # and quoted "In addition, we contacted relevant organisations" -- a sentence with
            # no date in it at all, offered as the source of the date. The assertion below is
            # the one that catches both, and it is the check that should have been written
            # first: a quotation that does not contain the thing it evidences is not evidence.
            if m.group(1).lower() not in sent.lower():
                sent = window.strip()
            # ⛔ AND THE CHECK MUST RUN ON THE STRING THAT IS DISPLAYED, NOT THE ONE BEFORE IT.
            #
            # The assertion above passed while the page still showed a quote with no date in it,
            # because the quote was truncated to 300 characters AFTERWARDS and the date sat at
            # character 340. Verified one string, rendered another -- the same shape as checking
            # an edit against source while the reader sees rendered text, and as an adjudicator
            # searching a haystack different from the one it displayed. Truncate first, then
            # check, and centre the window on the date when the sentence is too long.
            quote = sent[:300]
            if m.group(1).lower() not in quote.lower():
                i = sent.lower().find(m.group(1).lower())
                quote = ("..." + sent[max(0, i - 240):i + len(m.group(1)) + 40]).strip()
            return {"state": OBTAINED, "date": m.group(1), "quote": quote}
    return {"state": NOT_YET_FOUND,
            "why": "the abstract we hold does not state a search cut-off; the full text may"}


def _iso(d):
    m = re.match(r"(%s)\s+(\d{4})" % MONTHS, d, re.I)
    if not m:
        return None
    mm = ("january february march april may june july august september october november december"
          ).split().index(m.group(1).lower()) + 1
    return "%s-%02d-01" % (m.group(2), mm)


def new_since(canon, since_iso, known_ncts):
    """Registered trials that have REPORTED since the comparator stopped looking."""
    q = canon.get("title") or canon.get("question") or ""
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z-]{4,}", q)
             if w.lower() not in ("versus", "against", "placebo", "compared", "comparison",
                                  "adults", "women", "patients", "people", "across", "trials",
                                  "randomised", "randomized", "report", "spectrum", "first")]
    term = " ".join(words[:3])
    if not term:
        return {"state": NOT_YET_ATTEMPTED, "why": "no query term could be derived from the title"}
    url = ("%s?query.term=%s&pageSize=100&fields=protocolSection.identificationModule.nctId,"
           "protocolSection.identificationModule.briefTitle,"
           "protocolSection.statusModule.resultsFirstPostDateStruct,"
           "protocolSection.statusModule.primaryCompletionDateStruct,"
           "protocolSection.statusModule.overallStatus" % (CTG, quote_plus(term)))
    try:
        d = _json(url, timeout=90)
    except Exception as e:
        return {"state": NOT_YET_ATTEMPTED, "term": term,
                "why": "%s: %s" % (type(e).__name__, str(e)[:70])}
    rows = []
    for st in (d.get("studies") or []):
        ps = st.get("protocolSection") or {}
        ident = ps.get("identificationModule") or {}
        stat = ps.get("statusModule") or {}
        nct = ident.get("nctId")
        if not nct or nct in known_ncts:
            continue
        rp = ((stat.get("resultsFirstPostDateStruct") or {}).get("date") or "")
        pc = ((stat.get("primaryCompletionDateStruct") or {}).get("date") or "")
        # ⛔ A PLANNED COMPLETION DATE IS NOT A REPORT, and the first version counted it as one.
        #
        # It accepted primaryCompletionDate whether or not that date had arrived, so the pilot
        # rendered "7 registered trials have REPORTED since December 2024" and then listed
        # "completed 2028-12-30 RECRUITING" -- trials that have not finished, let alone
        # reported. `planned-field-shown-as-observed` is already a named class in the integrity
        # taxonomy; this is that class, produced by the component written to improve the page.
        #
        # Only a results-first-posted date is a report. A past completion with no results is a
        # different and weaker thing, and is counted separately rather than merged in.
        if rp and rp >= since_iso:
            bucket = "reported"
        elif pc and since_iso <= pc <= TODAY:
            bucket = "completed_no_results"
        else:
            continue
        rows.append({"nct": nct, "title": (ident.get("briefTitle") or "")[:110],
                     "bucket": bucket, "reported": rp or None, "completed": pc or None,
                     "status": stat.get("overallStatus")})
    rows.sort(key=lambda r: (r["reported"] or r["completed"] or ""), reverse=True)
    return {"state": OBTAINED, "term": term, "searched": len(d.get("studies") or []),
            "rows": rows,
            "n_reported": sum(1 for r in rows if r["bucket"] == "reported"),
            "n_completed": sum(1 for r in rows if r["bucket"] == "completed_no_results")}


MARKER = "<h2>What has changed since these trials were last synthesised</h2>"


def render(canon):
    out = [MARKER]
    pmid = comparator_pmid(canon)
    if not pmid:
        cands = comparator_candidates(canon)
        out.append("<p><b>No comparator is designated for this question</b>, so this page does "
                   "not state how current it is relative to one. Which published review answers "
                   "the same question is a judgement, and this component refuses to make it by "
                   "taking whichever identifier appears first &mdash; doing exactly that "
                   "produced a search date from an adherence review of observational studies on "
                   "an earlier run.%s</p>"
                   % (" The object mentions PMIDs %s; none is marked as the comparator."
                      % ", ".join(cands[:6]) if cands else ""))
        return "".join(out)
    sd = search_date(pmid)
    if sd["state"] != OBTAINED:
        out.append("<p><b>The comparator's search cut-off could not be established</b> "
                   "(PMID %s; %s). This page therefore states no evidence gap. The publication "
                   "date is <i>not</i> used as a substitute: a review is incomplete from the day "
                   "it stopped searching, not from the day it appeared, and substituting one for "
                   "the other would understate every gap in the same direction.</p>"
                   % (pmid, sd.get("why", "")[:120]))
        return "".join(out)
    since = _iso(sd["date"])
    known = set(re.findall(r"NCT\d{8}", json.dumps(canon, ensure_ascii=False)))
    out.append("<p>The comparator (PMID %s) searched <b>up to %s</b>, in its own words: "
               "&ldquo;<i>%s</i>&rdquo; Everything below has become readable since that date.</p>"
               % (pmid, sd["date"], re.sub(r"[<>]", "", sd["quote"])[:240]))
    res = new_since(canon, since, known)
    if res["state"] != OBTAINED:
        out.append("<p><b>The currency query did not run</b> (%s). This page does not claim that "
                   "nothing has appeared since %s &mdash; it claims only that it has not "
                   "looked.</p>" % (res.get("why", "")[:110], sd["date"]))
        return "".join(out)
    rows = res["rows"]
    if not rows:
        # ⛔ THE EMPTY CASE IS WHERE THE TWO CLAIMS COLLAPSE, so it is written most carefully.
        out.append("<p><b>No registered trial outside those already included has reported since "
                   "%s</b> in the %d records ClinicalTrials.gov returned for &ldquo;%s&rdquo;. "
                   "That is the result of one register searched with one term &mdash; it is not "
                   "a statement that nothing has changed, and a trial reported elsewhere, or "
                   "indexed under other words, would not appear here.</p>"
                   % (sd["date"], res["searched"], res["term"]))
        return "".join(out)
    out.append("<p>Outside the trials already included, <b>%d ha%s posted results</b> since %s "
               "and <b>%d passed a primary completion date without posting any</b> &mdash; "
               "from %d records returned for &ldquo;%s&rdquo;. A trial still recruiting, with a "
               "completion date in the future, is not counted here as having reported. None is "
               "pooled; they are listed because a reader deciding whether to rely on this page "
               "is entitled to know what it has not weighed.</p>"
               % (res["n_reported"], "s" if res["n_reported"] == 1 else "ve", sd["date"],
                  res["n_completed"], res["searched"], res["term"]))
    out.append("<div class=\"scroll\"><table><tr><th>Registration</th><th>Trial</th>"
               "<th>Results posted</th><th>Status</th></tr>")
    for r in rows[:12]:
        out.append("<tr><td><span class=\"mono\">%s</span></td><td>%s</td><td>%s</td>"
                   "<td>%s</td></tr>"
                   % (r["nct"], re.sub(r"[<>]", "", r["title"]),
                      ("results posted " + r["reported"]) if r["bucket"] == "reported"
                      # ⛔ DO NOT SAY "COMPLETED" WHEN THE REGISTRY SAYS RECRUITING.
                      # NCT06250504 carries a primary completion date of 2026-04-30 and a status
                      # of RECRUITING: the date passed, the trial did not stop. Calling that
                      # "completed" is the planned-versus-observed confusion one level down from
                      # the one this component was just fixed for.
                      else ("primary completion date %s passed; no results posted"
                            % (r["completed"] or "?")),
                      r["status"] or ""))
    out.append("</table></div>")
    if len(rows) > 12:
        out.append("<p>%d further records are not listed here.</p>" % (len(rows) - 12))
    return "".join(out)


def inject(html, canon):
    if MARKER in html:
        return html
    return html + "\n<div class=\"card\">\n" + render(canon) + "\n</div>\n"


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.chdir(os.path.dirname(os.path.dirname(HERE)))
    for path in sys.argv[1:] or ["ssot/agyw-hiv-prep-review/agyw-hiv-prep-review.json"]:
        canon = json.load(io.open(path, encoding="utf-8"))
        print("=" * 78)
        print(os.path.basename(path))
        print(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", render(canon)))[:1200])
