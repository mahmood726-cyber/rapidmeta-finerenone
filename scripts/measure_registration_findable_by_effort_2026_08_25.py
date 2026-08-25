"""Are the unregistered-in-record RCTs findable in the registry by hand?

THE QUESTION AND WHY IT SHARPENS THE CLAIM. 137 of 220 RCTs published 2015+ in these Cochrane
meta-analyses carry no registration identifier in their PubMed record. That establishes they
are not auditable *mechanically*. It does not establish they are unauditable.

  If most ARE findable by searching the registry on title and year, the claim becomes
  "auditable only by someone willing to do per-trial detective work" -- which is truer and
  worse, because that labour is exactly what the field assumes nobody will do.

  If most are NOT findable, the claim is stronger still.

Either answer is worth having, so this is run before the claim is written either way.

THE RULE, FIXED BEFORE THE RUN. A registry record counts as the same trial only when the
content-word overlap between the paper title and the registry title reaches JACCARD >= 0.50.
Nothing below that counts, however plausible it looks; and a search returning several records
above threshold is AMBIGUOUS, not found. Titles are compared after dropping a stoplist of
words that carry no identifying information ("randomized", "trial", "study", "effect"...) --
otherwise two unrelated RCTs share half their words by construction and the threshold measures
English rather than identity.

THE NULL, AND IT DECIDES WHETHER ANY OF THIS MEANS ANYTHING. Every paper title is ALSO run as
a search for a DIFFERENT paper: the search returns for paper i are scored against paper i+1's
title. If a shuffled pairing "finds" trials at a similar rate, the matcher is measuring
nothing. At a 0.50 threshold over medical English this is a live risk, not a formality.

WHAT THIS IS NOT. A found registry record is not proof the trial was prospectively registered,
nor that the registration is correct. It is proof only that a determined third party could
reach a plausible registry record from the paper. That is the whole claim.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
SRC = os.path.join(REPO, "outputs", "join_end_to_end_2026_08_25.json")
XML = os.path.join(REPO, "outputs", "pubmed_databank_cache")
CACHE = os.path.join(REPO, "outputs", "ctgov_title_search_cache")
OUT = os.path.join(REPO, "outputs", "registration_findable_by_effort_2026_08_25.json")

CTGOV = ("https://clinicaltrials.gov/api/v2/studies"
         "?query.titles=%s&pageSize=20"
         "&fields=NCTId,BriefTitle,OfficialTitle,StartDate,LeadSponsorName,StudyType")

TITLE = re.compile(r"<ArticleTitle[^>]*>(.*?)</ArticleTitle>", re.S | re.I)
NCT_RE = re.compile(r"NCT\d{8}")
TAG = re.compile(r"<[^>]+>")

THRESHOLD = 0.50

STOP = set("""a an the of for in on to and or with without versus vs by from at as is are be
randomized randomised randomization randomisation trial trials study studies controlled
control group groups patients patient adults children multicentre multicenter multicenter
double blind blinded placebo open label phase efficacy effectiveness safety effect effects
outcome outcomes clinical prospective retrospective pilot comparison compared comparative
treatment therapy management intervention interventions versus among following after before
protocol design methods results conclusion background objective aim""".split())


def words(s):
    s = TAG.sub(" ", s or "").lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return {w for w in s.split() if len(w) > 2 and w not in STOP}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def get(url, key):
    """Cached fetch that distinguishes NO PAYLOAD from A PAYLOAD SAYING ZERO.

    The first version required len(body) > 30. A genuine empty result from this API is
    {"studies":[]} -- SIXTEEN bytes -- so every trial that simply is not in the registry
    failed the guard, retried three times, and was recorded as SEARCH FAILED. The headline
    would then have been "most searches failed" rather than "most trials were not found",
    which is a different claim and an unanswerable one.

    A zero has two readings and only one of them is about the world. The marker, not the
    length, decides whether a payload arrived.
    """
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9]+", "_", key)[:110] + ".json")
    if os.path.exists(fp) and os.path.getsize(fp) > 8:
        return io.open(fp, encoding="utf-8", errors="replace").read()
    for attempt in (1, 2, 3):
        r = subprocess.run(["curl", "-sSL", "-g", "--max-time", "90", url], capture_output=True)
        body = (r.stdout or b"").decode("utf-8", "replace")
        if body.lstrip().startswith("{") and '"studies"' in body:
            io.open(fp, "w", encoding="utf-8").write(body)
            return body
        time.sleep(2 * attempt)
    return None


def search(title):
    """Registry records for this title. None means the search itself failed."""
    import urllib.parse
    q = urllib.parse.quote(" ".join(list(words(title))[:18]), safe="")
    if not q:
        return []
    body = get(CTGOV % q, title[:90])
    if body is None:
        return None
    try:
        out = []
        for st in (json.loads(body).get("studies") or []):
            p = ((st.get("protocolSection") or {}))
            idm = p.get("identificationModule") or {}
            out.append({
                "nct": idm.get("nctId"),
                "title": (idm.get("officialTitle") or idm.get("briefTitle") or ""),
                "sponsor": ((p.get("sponsorCollaboratorsModule") or {})
                            .get("leadSponsor") or {}).get("name"),
            })
        return out
    except Exception:
        return None


def score(paper_title, records):
    """(best_nct, best_j, n_above_threshold) under the pre-stated rule."""
    pw = words(paper_title)
    above = [(jaccard(pw, words(r["title"])), r) for r in (records or [])]
    above = [(j, r) for j, r in above if j >= THRESHOLD]
    above.sort(key=lambda x: -x[0])
    if not above:
        return None, (max([jaccard(pw, words(r["title"])) for r in (records or [])] or [0.0])), 0
    return above[0][1]["nct"], above[0][0], len(above)


def run_controls():
    from instrument_controls import require_controls
    t = "Empagliflozin in patients with chronic kidney disease and heart failure"
    same = [{"nct": "NCT1", "title": "Empagliflozin in chronic kidney disease and heart "
                                     "failure patients", "sponsor": "x"}]
    other = [{"nct": "NCT2", "title": "Vitamin D supplementation for fracture prevention "
                                      "in older women", "sponsor": "y"}]
    n1, j1, c1 = score(t, same)
    n2, j2, c2 = score(t, other)
    require_controls(
        "registration_findable (title matcher)",
        ("the same trial under a reworded title clears the 0.50 rule", c1, 1),
        ("an unrelated trial is FLAGGED as the same trial", c2 > 0, True))


def main():
    run_controls()
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    d = json.load(io.open(SRC, encoding="utf-8"))

    def cached(pmid):
        for ext in (".xml", ".txt"):
            fp = os.path.join(XML, str(pmid) + ext)
            if os.path.exists(fp):
                return io.open(fp, encoding="utf-8", errors="replace").read()
        return None

    targets = []
    for r in d["rows"]:
        if not (r.get("pmid") and r.get("year") and int(r["year"]) >= 2015):
            continue
        x = cached(r["pmid"])
        if x is None or NCT_RE.search(x):
            continue
        if "Randomized Controlled Trial" not in x:
            continue
        m = TITLE.search(x)
        if not m:
            continue
        targets.append({"pmid": r["pmid"], "label": r["label"],
                        "title": TAG.sub(" ", m.group(1)).strip()})

    log("2015+ RCTs with no registration in their PubMed record: %d" % len(targets))
    log("rule fixed before the run: jaccard >= %.2f on content words; 2+ above = AMBIGUOUS"
        % THRESHOLD)
    log("")

    rows, failed = [], 0
    for i, t in enumerate(targets, 1):
        recs = search(t["title"])
        if recs is None:
            failed += 1
            rows.append(dict(t, status="SEARCH FAILED"))
            log("[%3d/%d] %-9s SEARCH FAILED" % (i, len(targets), t["pmid"]))
            continue
        nct, best, nabove = score(t["title"], recs)
        rows.append(dict(t, status="ok", n_returned=len(recs), best_j=round(best, 3),
                         n_above=nabove, nct=nct))
        log("[%3d/%d] %-9s returned=%-3d best=%.2f %s %s"
            % (i, len(targets), t["pmid"], len(recs), best,
               "FOUND" if nabove == 1 else ("AMBIG" if nabove > 1 else "none "), nct or ""))
        time.sleep(0.34)

    # NULL: score each paper's search returns against the NEXT paper's title.
    ok = [r for r in rows if r.get("status") == "ok"]
    nullfound = 0
    for k, r in enumerate(ok):
        other = ok[(k + 1) % len(ok)]
        recs = search(r["title"])
        if not recs:
            continue
        _n, _j, above = score(other["title"], recs)
        if above >= 1:
            nullfound += 1

    found = [r for r in ok if r.get("n_above") == 1]
    ambig = [r for r in ok if (r.get("n_above") or 0) > 1]
    log("")
    log("searched                       : %d   (search failed %d)" % (len(ok), failed))
    log("FOUND, one record over the rule: %d / %d  (%.0f%%)"
        % (len(found), len(ok), 100.0 * len(found) / len(ok) if ok else 0))
    log("AMBIGUOUS, 2+ over the rule    : %d / %d" % (len(ambig), len(ok)))
    log("not found                      : %d / %d"
        % (len(ok) - len(found) - len(ambig), len(ok)))
    log("NULL, a DIFFERENT paper's title: %d / %d  (%.0f%%)"
        % (nullfound, len(ok), 100.0 * nullfound / len(ok) if ok else 0))

    json.dump({"question": "are RCTs with no registration in their PubMed record findable in "
                           "the registry by title search",
               "rule": "jaccard >= 0.50 on content words after a stoplist; 2+ = AMBIGUOUS",
               "claim_limit": "a found record proves a determined third party could REACH a "
                              "plausible registration, not that the trial was prospectively "
                              "registered nor that the registration is correct",
               "n": len(ok), "found": len(found), "ambiguous": len(ambig),
               "search_failed": failed, "null_found": nullfound, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
