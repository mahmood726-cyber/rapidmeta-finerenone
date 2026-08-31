# -*- coding: utf-8 -*-
"""What IS this document? A content assertion, and a kind label -- never a choice between them.

TWO RULINGS IMPLEMENTED HERE.

RULING 2 -- LENGTH IS NOT A CONTENT ASSERTION. A publisher landing page is long, well-formed,
and contains no trial report. That is how "a 200 is not a document" bit the rebuild lane, and a
4000-character floor does not catch it: the landing page clears it comfortably. So the test
asks what a trial report MUST contain -- a methods section AND a results section, and ideally a
participant count or an effect estimate -- rather than how much text arrived.

⚠️ AND THE THRESHOLD WAS NOT RAISED. Making one instrument agree with another by moving its
number is the failure this project refused twice tonight; this is the third refusal. The floor
stays at 4000 and a separate, structural question is asked.

RULING 1 -- TWO DOCUMENTS FOR ONE TRIAL IS RICHER, NOT A CONFLICT. 20 of 21 shared trials
resolved to different content because each lane found a different paper. Neither is wrong. The
defect would be pretending a trial has one canonical file, and we already know that failure's
shape: a dose-selection paper stood in for a results report today and named both registrations,
so every existence check passed.

  So each document is LABELLED by what it is -- primary report, supplement, protocol/SAP,
  erratum, secondary analysis, or not-a-report -- and an assessment cites WHICH DOCUMENT
  ANSWERED WHICH DOMAIN. Nothing is discarded and nothing is promoted to canonical.

⚠️ THE LABELS ARE KEYWORD-DERIVED AND THEIR ERROR RATE IS UNMEASURED. This is a screening
instrument. It reports a kind and the evidence for it, and anything it cannot place is
UNCLASSIFIED rather than defaulted to the commonest label.
"""
import io
import re
import sys

# Structure a trial report must have. Headed sections, not passing mentions: "methods" appears
# in any abstract, so the probe requires it in a heading-like position.
SEC_METHODS = re.compile(r"(?:^|\n|\.\s|>)\s*(?:2\.?\s*)?(methods?|materials and methods|"
                         r"patients and methods|study design)\b", re.I)
SEC_RESULTS = re.compile(r"(?:^|\n|\.\s|>)\s*(?:3\.?\s*)?(results?|findings)\b", re.I)
N_PARTICIPANTS = re.compile(
    r"\b(?:n\s*=\s*\d{2,6}|\d{2,6}\s+(?:patients|participants|subjects|women|men|adults|"
    r"children)\b|randomi[sz]ed\s+\d{2,6})", re.I)
EFFECT = re.compile(
    r"\b(?:hazard ratio|risk ratio|odds ratio|rate ratio|mean difference|\bHR\b|\bRR\b|"
    r"\bOR\b)\s*[,:=]?\s*\d|\d\.\d{1,3}\s*\(\s*95\s*%", re.I)

# ⚠️ A SYSTEMATIC REVIEW HAS METHODS AND RESULTS TOO, so the structural test cannot tell it
# from a trial report and must not be asked to. This kind is checked FIRST, and it was missing:
# the first run of this classifier called a 27-trial meta-analysis of antidiabetic agents a
# PRIMARY_REPORT for EMPA-REG, because it had both sections. That inflated "70 primary reports"
# and made a downstream sweep compare registry arm sizes against a review that never states
# them. The structural test was right about structure and wrong about kind.
KINDS = [
    ("SYSTEMATIC_REVIEW", re.compile(
        r"systematic review|meta[- ]analys[ie]s|\bPRISMA\b|network meta[- ]analysis|"
        r"we searched (?:PubMed|MEDLINE|Embase|the Cochrane)", re.I)),
    ("PROTOCOL_OR_SAP", re.compile(
        r"statistical analysis plan|clinical (?:study|trial) protocol|protocol amendment|"
        r"\bSAP\b\s+version", re.I)),
    ("ERRATUM", re.compile(r"\berratum\b|\bcorrigendum\b|correction to:|retraction of", re.I)),
    ("SECONDARY_ANALYSIS", re.compile(
        r"post[- ]hoc analysis|secondary analysis|exploratory analysis|subgroup analysis of|"
        r"pooled analysis of|cost[- ]effectiveness|economic evaluation", re.I)),
    ("SUPPLEMENT", re.compile(r"supplementary appendix|supplemental (?:material|content)|"
                              r"online[- ]only appendix", re.I)),
]


def rendered(raw):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()


def names_trial(text, nct):
    """Does this document NAME the trial it was joined to?

    The sharpest question and the one nobody asked. A document retrieved by searching an NCT
    is not thereby ABOUT that trial: Europe PMC returns anything citing it, and the first hit
    is often a review. If the document never states the registration, the join is a citation
    link and not an identity.
    """
    return bool(nct) and nct in text.replace(" ", "")


def assess(text):
    """Is this a trial report, and what kind? Returns the evidence, not just a verdict."""
    ev = {
        "chars": len(text),
        "has_methods": bool(SEC_METHODS.search(text)),
        "has_results": bool(SEC_RESULTS.search(text)),
        "has_participant_count": bool(N_PARTICIPANTS.search(text)),
        "has_effect_estimate": bool(EFFECT.search(text)),
    }
    # THE ASSERTION: structure, not size. Both sections are required; a landing page has
    # neither, however long it is.
    ev["is_a_report"] = ev["has_methods"] and ev["has_results"]
    kind = None
    for name, pat in KINDS:
        if pat.search(text[:60000]):
            kind = name
            break
    if kind is None:
        kind = "PRIMARY_REPORT" if ev["is_a_report"] else "NOT_A_REPORT"
    if not ev["is_a_report"] and kind in ("PRIMARY_REPORT",):
        kind = "UNCLASSIFIED"
    ev["kind"] = kind
    return ev


LANDING_PAGE = """<html><head><title>Article | Journal of Examples</title></head><body>
<nav>Home About Subscribe Institutional access Sign in Register Help Contact Privacy Cookies
Browse by subject Browse by issue Advanced search Alerts RSS Permissions Reprints</nav>
<h1>Effect of an intervention on an outcome: a randomised trial</h1>
<p>Authors: A Person, B Person, C Person, D Person, E Person</p>
<p>Abstract available to subscribers. Purchase this article for 24 hours of access, or sign in
through your institution to continue reading. Access options include institutional login,
society membership, and personal subscription. Related articles from this journal are listed
below, along with citation tools, metrics, figures and sharing options for this content.</p>
<p>%s</p></body></html>""" % ("Recommended articles and citing articles appear here. " * 120)


def plant():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    lp = rendered(LANDING_PAGE)
    a = assess(lp)
    print("PLANT -- a publisher landing page, %d rendered chars (clears the 4000 floor)" % a["chars"])
    assert a["chars"] > 4000, a["chars"]
    assert a["is_a_report"] is False, a
    print("   is_a_report=False, kind=%s   [PASS]" % a["kind"])
    real = ("Introduction. Background text. Methods We conducted a phase 3, randomized, "
            "double-blind trial. 2629 women were randomized. Results A total of 168 HIV-1 "
            "infections occurred. The hazard ratio was 0.73 (95% CI 0.59 to 0.91). Discussion.")
    b = assess(real)
    assert b["is_a_report"] is True and b["has_effect_estimate"], b
    print("   real report: is_a_report=True, kind=%s, effect=%s   [PASS]"
          % (b["kind"], b["has_effect_estimate"]))
    print("")
    print("Both directions watched. The floor was NOT raised; a structural question was added.")
    return 0


if __name__ == "__main__":
    if "--plant" in sys.argv:
        raise SystemExit(plant())
    import collections
    import glob
    import json
    import os
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    files = sorted(glob.glob(r"F:\claude-temp\pend\out\fulltext\*.xml"))
    kinds, rep = collections.Counter(), collections.Counter()
    rows = []
    for f in files:
        try:
            t = rendered(io.open(f, encoding="utf-8", errors="replace").read())
        except OSError:
            continue
        a = assess(t)
        kinds[a["kind"]] += 1
        rep["report" if a["is_a_report"] else "NOT a report"] += 1
        rows.append({"file": os.path.basename(f), **a})
    print("")
    print("WHAT THE 317 RETRIEVED DOCUMENTS ACTUALLY ARE")
    print("")
    print("  documents classified            %4d  == the denominator" % len(rows))
    for k, v in rep.most_common():
        print("     %-16s %4d   %5.1f%%" % (k, v, 100.0 * v / len(rows)))
    print("")
    print("  by kind:")
    for k, v in kinds.most_common():
        print("     %-20s %4d   %5.1f%%" % (k, v, 100.0 * v / len(rows)))
    print("")
    for k in ("has_participant_count", "has_effect_estimate"):
        n = sum(1 for r in rows if r[k])
        print("  %-24s %4d   %5.1f%%" % (k, n, 100.0 * n / len(rows)))
    json.dump(rows, io.open(r"F:\claude-temp\pend\out\document_kinds.json", "w",
                            encoding="utf-8"), indent=1)
    print("")
    print("  detail -> document_kinds.json")
    print("  ⚠️ Keyword-derived labels with an UNMEASURED error rate. A screening instrument.")
