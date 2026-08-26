# -*- coding: utf-8 -*-
"""Three separately-earned indicators per index card. One badge became three.

WHAT WAS WRONG. The index injected a single coloured dot per card from a threshold on one
number, and the dot's tooltip read "TRUSTWORTHY (score <0.30) -- multi-source audit passed".
Measured against the delivered index: 80 cards carried the green dot and ZERO of the 80 sat
on a page that says READY. 16 of cardiology's 18 say NOT READY in their own banner.

AND THE UNDERLYING QUANTITY IS NARROWER THAN THE LABEL BY TWO STEPS. The score is a weighted
FABRICATION-RISK measure over eight extraction components -- null PMIDs, nulled NCTs, trials
with no evidence, agent-flag density, cross-review flags, single-arm-with-HR, generic drug
names, unverifiable published values. Every one is identifier hygiene of the EXTRACTION.
None of them touches pooling, heterogeneity, risk of bias, certainty, or whether the
estimand is the registered one. A record at 0.297 -- five of its ten trials carrying a null
PMID -- classifies OK and was labelled "multi-source audit passed". 54 of the 128 pages
scoring exactly zero are single-trial reviews: one trial with a clean identifier scores
perfectly. The error is not a mislabelled good measure. The measure is narrow, the label is
two steps removed from it, and the direction of the error is always flattering.

THE THREE, AND WHY THEY ARE NOT COMBINED. A composite would reintroduce the defect wearing
three badges instead of one: it would let a passing extraction check carry a page that has
no validity assessment and says it is not ready.

  internal    what the extraction audit measured, named as what it is, WITH ITS DATE.
  validity    NOT ASSESSED on every page, because no scientific-validity assessment exists
              anywhere in this corpus. Left explicitly unpopulated with the reason stated.
              Deriving it from the extraction checks is the exact conflation being removed.
  readiness   the page's OWN submission-readiness banner, read from its rendered text.

ABSENT MUST NOT READ AS NEUTRAL. 36 of cardiology's 54 cards have no record in the audit
file at all, so they showed no dot -- an absence sitting beside green, which a reader
resolves in the flattering direction. NOT_MEASURED is now a state with its own mark, not a
blank.

STALENESS IS PART OF THE CLAIM. The audit file is dated and the badge SAYS the date. A live
green claim served from a file that predates the work on the page is a provenance failure in
the one place a reader looks first.

THE PROCESS LINE says what was actually done and stops there: N AI readers of different
families, whether an adjudication is recorded, and that no human has verified it. Zero
objects in this corpus hold an adjudication record, so that limb reads negative on every
page. That is the true state and it is not softened.
"""
from __future__ import annotations

import collections
import datetime
import html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from instrument_controls import require_controls  # noqa: E402

SCORES = os.path.join(REPO, "outputs", "extraction_audit", "fabrication_risk_scores.json")
# AT THE REPO ROOT, DELIBERATELY. `.gitignore` carries `outputs/*.json`, so writing this
# beside the audit data would have left it untracked and undeployed -- and the page fetches
# it at runtime, so the failure would not be a missing file, it would be a live homepage
# rendering the ellipsis placeholders where every number belongs. The old audit file escapes
# that pattern only because it sits one directory deeper. A data file the site FETCHES has
# to live where the site can serve it.
OUT = os.path.join(REPO, "index_indicators.json")

CARD = re.compile(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*\bcard\b[^"]*"[^>]*>', re.S)

# BOUNDED, AND IT STOPS AT THE STATE. An unbounded [A-Z ]+ ran on into the next sentence and
# returned "NOT READY C" -- the C of "Computed from this object's own state". A capture that
# swallows the following word is a capture that will silently invent a state.
READY_RE = re.compile(r"Submission readiness:\s*(READY|NOT READY|NOT YET DETERMINED)\b")
TOMB_RE = re.compile(r"Retired review|This review has been retired", re.I)
TWO_RE = re.compile(r"by two assessors reading independently")
ONE_RE = re.compile(r"\bOne assessor\b")
ROB_RE = re.compile(r"[Rr]isk of bias was assessed with")
NOADJ_RE = re.compile(r"[Nn]o adjudication has been performed")
ADJ_RE = re.compile(r"adjudicated by|adjudication recorded")
# THE WORD IS SHARED BY TWO DIFFERENT THINGS AND ONE OF THEM IS EVERYWHERE. Trials
# adjudicate ENDPOINTS -- "all suspected efficacy events were adjudicated by the Central
# Events Committee" -- and that has nothing to do with two risk-of-bias assessors resolving
# a disagreement. Searching the whole page flagged DOAC_AF_REVIEW as having a recorded
# adjudication because its trials had a CEC. That is the SAME conflation this whole change
# exists to remove -- two meanings joined by a shared word, erring in the flattering
# direction -- so the search is scoped to the risk-of-bias section rather than the page.
ROB_SECTION = re.compile(
    r"Risk of bias in the included results(.*?)(?:Certainty of the evidence|"
    r"Comparison with published syntheses|Limitations|Sources for this section)", re.S)


def _rob_scope(t):
    m = ROB_SECTION.search(t)
    return m.group(1) if m else ""

INTERNAL_FROM_CLASS = {
    "OK": "CHECKS_PASSED",
    "LOW_CONCERN": "SOME_FLAGS",
    "MANUAL_REVIEW": "MANY_FLAGS",
    "QUARANTINE": "QUARANTINED",
}


def rendered(raw):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def read_page(path):
    """What the PAGE says about itself. Never a number this function could not establish."""
    if not os.path.isfile(path):
        return {"readiness": "TARGET_MISSING", "n_ai_readers": None,
                "adjudication_recorded": False, "rob_recorded": False}
    t = rendered(io.open(path, encoding="utf-8", errors="replace").read())
    if TOMB_RE.search(t):
        ready = "RETIRED"
    else:
        m = READY_RE.search(t)
        ready = m.group(1).replace(" ", "_") if m else "NOT_STATED"
    n = 2 if TWO_RE.search(t) else (1 if ONE_RE.search(t) else None)
    return {
        "readiness": ready,
        "n_ai_readers": n,
        "rob_recorded": bool(ROB_RE.search(t) or n),
        # AN ADJUDICATION IS RECORDED ONLY WHERE ONE IS. Zero pages today. This reads the
        # page rather than asserting the corpus-wide fact, so it flips by itself on the
        # first page that records one, with no edit here.
        "adjudication_recorded": bool(
            ROB_RE.search(t) and not NOADJ_RE.search(t) and ADJ_RE.search(_rob_scope(t))),
    }


def build(root=None):
    root = root or REPO
    src = io.open(os.path.join(root, "index.html"), encoding="utf-8",
                  errors="replace").read()
    scores = {r["review"]: r for r in json.load(io.open(SCORES, encoding="utf-8"))}
    measured = datetime.datetime.utcfromtimestamp(
        os.path.getmtime(SCORES)).strftime("%Y-%m-%d")
    out = {}
    for m in CARD.finditer(src):
        href = m.group(1).split("#")[0]
        stem = re.sub(r"\.html$", "", href.split("/")[-1], flags=re.I)
        rec = scores.get(stem)
        page = read_page(os.path.join(root, href.replace("/", os.sep)))
        out[stem] = {
            "href": href,
            "internal": {
                "state": INTERNAL_FROM_CLASS.get((rec or {}).get("classification"),
                                                 "NOT_MEASURED"),
                "score": (rec or {}).get("score"),
                "n_trials": (rec or {}).get("n_trials"),
                "measured": measured if rec else None,
            },
            # NEVER COMPUTED. Present as a field so its absence is visible in the data
            # rather than inferred from the fact that nothing renders.
            "validity": {"state": "NOT_ASSESSED"},
            "readiness": {"state": page["readiness"]},
            "process": {
                "n_ai_readers": page["n_ai_readers"],
                "adjudication_recorded": page["adjudication_recorded"],
                "human_verified": False,
                "rob_recorded": page["rob_recorded"],
            },
        }
    return out, measured


# A SYNTHETIC PAGE THAT SAYS READY. The headline finding is "zero cards say READY", and that
# is only a finding if the parser CAN return READY. Without this, the identical output would
# be produced by a regex that never matches -- a claim about the corpus that is really a
# claim about a pattern.
FIXTURE_READY = ("<html><body><p>Submission readiness: READY</p>"
                 "<p>Risk of bias was assessed with RoB 2 at the level of each reported "
                 "result, by two assessors reading independently.</p></body></html>")
FIXTURE_NOT = ("<html><body><p>Submission readiness: NOT READY</p>"
               "<p>Computed from this object's own state.</p></body></html>")

# THE CEC CASE, KEPT AS A FIXTURE. A page with a risk-of-bias section that says no
# adjudication was performed, and trial prose elsewhere describing ENDPOINT adjudication by
# a committee. It must come back NOT adjudicated. This is the real defect that reached the
# generated data before it was caught, so it is pinned synthetically rather than to
# DOAC_AF_REVIEW, which would stop testing anything the day that page is rebuilt.
FIXTURE_CEC = (
    "<html><body><p>Submission readiness: NOT READY</p>"
    "<h3>Risk of bias in the included results</h3>"
    "<p>Risk of bias was assessed with RoB 2 at the level of each reported result, by two "
    "assessors reading independently. No adjudication has been performed.</p>"
    "<h3>Certainty of the evidence</h3>"
    "<p>All suspected efficacy events were adjudicated by the Central Events Committee "
    "(CEC).</p></body></html>")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "f.html")
        io.open(p, "w", encoding="utf-8").write(FIXTURE_READY)
        got_ready = read_page(p)
        io.open(p, "w", encoding="utf-8").write(FIXTURE_NOT)
        got_not = read_page(p)
    require_controls(
        "index_indicators_readiness_parser",
        ("a synthetic page saying READY must parse as READY -- otherwise 'no card says "
         "READY' is a claim about this regex and not about the corpus; got %r"
         % got_ready["readiness"], got_ready["readiness"], "READY"),
        ("a synthetic page saying NOT READY must NOT parse as READY; got %r"
         % got_not["readiness"], got_not["readiness"], "READY"))
    require_controls(
        "index_indicators_reader_count",
        ("the READY fixture states two assessors and must report 2; got %r"
         % got_ready["n_ai_readers"], got_ready["n_ai_readers"], 2),
        ("the NOT-READY fixture states no assessors and must NOT report a count; got %r"
         % got_not["n_ai_readers"], got_not["n_ai_readers"], 2))

    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "c.html")
        io.open(p, "w", encoding="utf-8").write(FIXTURE_CEC)
        got_cec = read_page(p)
    require_controls(
        "index_indicators_adjudication_scope",
        ("the CEC fixture states two assessors and must still report 2 readers; got %r"
         % got_cec["n_ai_readers"], got_cec["n_ai_readers"], 2),
        ("endpoint adjudication by a Central Events Committee is NOT a risk-of-bias "
         "adjudication and must not be recorded as one; got %r"
         % got_cec["adjudication_recorded"], got_cec["adjudication_recorded"], True))

    data, measured = build()
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"_measured": measured,
                    "_what": ("Three separately-earned indicators per card. `internal` is "
                              "the extraction identifier audit and measures nothing about "
                              "the synthesis. `validity` is never computed. `readiness` is "
                              "the page's own banner."),
                    "cards": data}, indent=1, ensure_ascii=False))
    print("")
    print("INDICATORS over %d card(s) on the delivered index" % len(data))
    print("")
    for limb in ("internal", "validity", "readiness"):
        c = collections.Counter(v[limb]["state"] for v in data.values())
        print("  %-10s %s" % (limb, ", ".join("%s %d" % kv for kv in c.most_common())))
    proc = collections.Counter(
        ("%s AI reader(s)" % v["process"]["n_ai_readers"])
        if v["process"]["n_ai_readers"] else "no reader count stated"
        for v in data.values())
    print("  %-10s %s" % ("process", ", ".join("%s %d" % kv for kv in proc.most_common())))
    print("  %-10s %d" % ("adjudicated",
                          sum(1 for v in data.values()
                              if v["process"]["adjudication_recorded"])))
    print("")
    print("  audit file measured %s -- the badge states this date" % measured)
    print("  -> %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
