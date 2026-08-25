"""Findable-by-effort, v4: title AND year AND sponsor. Ceiling measured on a FRESH set.

WHY A FOURTH VERSION. v3 established a ceiling: searching the registry by title recovers the
correct record for 42 of 128 trials whose registration is KNOWN to exist (33%), and 10 of its
31 confident matches are the wrong trial. That is too weak to establish absence. Before
concluding that the 137 unregistered-in-record RCTs are simply unfindable, the obvious
strengthening deserves a measurement: title search is only one of the three things a human
would actually use. A person doing this by hand also knows roughly WHEN the trial ran and WHO
ran it.

THE THREE SIGNALS, and each is used for a different job:

  TITLE    retrieval and identification. Candidates are pooled across all three AND tiers
           (4 longest content words, then 3, then 2) rather than stopping at the first tier
           that returns anything -- v3 stopped early and saw fewer candidates than it could.
  YEAR     a filter, not a scorer. A trial's registry start date must fall in
           [publication year - 12, publication year + 2]. Trials start before they publish,
           sometimes long before, and occasionally a registration post-dates the paper.
  SPONSOR  a TIE-BREAKER only. Lead sponsor tokens are compared against the paper's author
           affiliations. It never promotes a candidate over the title threshold; it only
           chooses between candidates already over it. Sponsor names and affiliations agree
           too loosely to carry identification on their own.

THE SAMPLE IS FRESH, AND THIS MATTERS. v4 was designed AFTER seeing how the 128 behaved under
v3, so those 128 are BURNED as a validation set -- tuning against them and then reporting on
them would fit the design to the sample and destroy the only honest measurement of the
instrument. The ceiling here is therefore measured on known-registered papers drawn from the
WIDENED run, which v4 has never seen.

WHAT A RESULT WOULD MEAN. If the ceiling rises materially, the 137 can be tested and the
auditability claim can be stated as "recoverable only by per-trial detective work". If it does
not, the finding stands as it is: the identifier is not substitutable by effort.

Usage:  python measure_findable_v4_...py <join_json> [--ceiling|--targets]
"""
import html
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
XML = os.path.join(REPO, "outputs", "pubmed_databank_cache")
CACHE = os.path.join(REPO, "outputs", "ctgov_title_search_cache")

CTGOV = ("https://clinicaltrials.gov/api/v2/studies"
         "?query.titles=%s&pageSize=50"
         "&fields=NCTId,BriefTitle,OfficialTitle,StartDate,LeadSponsorName,StudyType")

TITLE = re.compile(r"<ArticleTitle[^>]*>(.*?)</ArticleTitle>", re.S | re.I)
AFFIL = re.compile(r"<Affiliation>(.*?)</Affiliation>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
NCT_RE = re.compile(r"NCT\d{8}")

THRESHOLD = 0.50
YEAR_LO, YEAR_HI = 12, 2

import measure_registration_findable_by_effort_2026_08_25 as V3

words = V3.words
jaccard = V3.jaccard


def get(url, key):
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


def parse(body):
    out = []
    for st in (json.loads(body).get("studies") or []):
        p = (st.get("protocolSection") or {})
        idm = p.get("identificationModule") or {}
        sm = p.get("statusModule") or {}
        start = ((sm.get("startDateStruct") or {}).get("date") or "")
        out.append({
            "nct": idm.get("nctId"),
            "title": (idm.get("officialTitle") or idm.get("briefTitle") or ""),
            "sponsor": ((p.get("sponsorCollaboratorsModule") or {})
                        .get("leadSponsor") or {}).get("name") or "",
            "start_year": (start[:4] if re.match(r"^\d{4}", start or "") else None),
        })
    return out


def candidates(title):
    """Pooled across ALL tiers, deduped by NCT. None means the search itself failed."""
    terms = sorted(words(title), key=len, reverse=True)
    if not terms:
        return []
    seen, pooled = set(), []
    import urllib.parse
    for tier in (4, 3, 2):
        if len(terms) < tier:
            continue
        q = urllib.parse.quote(" ".join(terms[:tier]), safe="")
        body = get(CTGOV % q, "v4and%d_%s" % (tier, title[:78]))
        if body is None:
            return None
        try:
            recs = parse(body)
        except Exception:
            return None
        for r in recs:
            if r["nct"] and r["nct"] not in seen:
                seen.add(r["nct"])
                pooled.append(r)
    return pooled


def decide(paper_title, pub_year, affils, recs):
    """(picked_nct, best_j, n_above, n_after_year) under the pre-stated v4 rule."""
    pw = words(paper_title)
    inwin = []
    for r in (recs or []):
        if r["start_year"] and pub_year:
            try:
                d = int(pub_year) - int(r["start_year"])
            except ValueError:
                d = 0
            if not (-YEAR_HI <= d <= YEAR_LO):
                continue
        inwin.append(r)
    scored = [(jaccard(pw, words(r["title"])), r) for r in inwin]
    above = sorted([(j, r) for j, r in scored if j >= THRESHOLD], key=lambda x: -x[0])
    best = max([j for j, _ in scored] or [0.0])
    if not above:
        return None, best, 0, len(inwin)
    if len(above) > 1:
        # SPONSOR breaks a tie and never creates one.
        aw = words(" ".join(affils or []))
        above.sort(key=lambda x: (-x[0], -jaccard(aw, words(x[1]["sponsor"]))))
    return above[0][1]["nct"], above[0][0], len(above), len(inwin)


def cached(pmid):
    for ext in (".xml", ".txt"):
        fp = os.path.join(XML, str(pmid) + ext)
        if os.path.exists(fp):
            return io.open(fp, encoding="utf-8", errors="replace").read()
    return None


def paper(pmid):
    x = cached(pmid)
    if not x:
        return None
    m = TITLE.search(x)
    if not m:
        return None
    return {"title": TAG.sub(" ", m.group(1)).strip(),
            "affils": [TAG.sub(" ", a) for a in AFFIL.findall(x)[:4]],
            "has_nct": bool(NCT_RE.search(x)),
            "is_rct": "Randomized Controlled Trial" in x}


def run_controls():
    from instrument_controls import require_controls
    t = "Empagliflozin in patients with chronic kidney disease and heart failure"
    same = [{"nct": "NCT1", "title": "Empagliflozin in chronic kidney disease and heart "
             "failure patients", "sponsor": "Boehringer", "start_year": "2018"}]
    other = [{"nct": "NCT2", "title": "Vitamin D for fracture prevention in older women",
              "sponsor": "NIH", "start_year": "2018"}]
    outwin = [dict(same[0], start_year="1985")]
    n1, _j, c1, _w = decide(t, "2020", ["Boehringer"], same)
    n2, _j, c2, _w = decide(t, "2020", ["Boehringer"], other)
    n3, _j, c3, _w = decide(t, "2020", ["Boehringer"], outwin)
    require_controls(
        "findable_v4 (title+year)",
        ("the same trial inside the year window clears the rule", c1, 1),
        ("an unrelated trial is FLAGGED as the same trial", c2 > 0, True))
    require_controls(
        "findable_v4 (year filter)",
        ("a matching title OUTSIDE the year window is excluded", c3, 0),
        ("the year filter excludes a trial INSIDE the window", c1 == 0, True))


def main():
    run_controls()
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        REPO, "outputs", "join_end_to_end_wide_2026_08_25.json")
    mode = sys.argv[2] if len(sys.argv) > 2 else "--ceiling"
    burned = set()
    narrow = os.path.join(REPO, "outputs", "join_end_to_end_2026_08_25.json")
    if os.path.exists(narrow):
        burned = {str(r.get("pmid")) for r in json.load(io.open(narrow, encoding="utf-8"))["rows"]
                  if r.get("pmid")}

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    if not os.path.exists(src):
        log("NOT MEASURABLE: %s does not exist." % os.path.relpath(src, REPO))
        return 1

    rows = json.load(io.open(src, encoding="utf-8"))["rows"]
    targets = []
    for r in rows:
        pm = str(r.get("pmid") or "")
        if not pm or pm in burned:
            continue
        p = paper(pm)
        if not p:
            continue
        if mode == "--ceiling" and not (r.get("nct") and p["has_nct"]):
            continue
        if mode == "--targets" and (p["has_nct"] or not p["is_rct"]):
            continue
        targets.append(dict(p, pmid=pm, nct=r.get("nct"), year=r.get("year")))

    log("mode %s   targets %d   (excluded %d PMIDs burned by v3's validation set)"
        % (mode, len(targets), len(burned)))
    log("rule: pooled tiers 4/3/2, year window [-%d,+%d], jaccard >= %.2f, sponsor breaks ties"
        % (YEAR_LO, YEAR_HI, THRESHOLD))
    log("")

    out, failed, hit_set, over, correct = [], 0, 0, 0, 0
    for i, t in enumerate(targets, 1):
        recs = candidates(t["title"])
        if recs is None:
            failed += 1
            out.append(dict(t, status="SEARCH FAILED"))
            continue
        nct, best, above, inwin = decide(t["title"], t.get("year"), t["affils"], recs)
        in_set = bool(t.get("nct")) and any(r["nct"] == t["nct"] for r in recs)
        ok = bool(t.get("nct")) and nct == t["nct"]
        hit_set += 1 if in_set else 0
        over += 1 if above >= 1 else 0
        correct += 1 if ok else 0
        out.append(dict(t, status="ok", pooled=len(recs), in_window=inwin,
                        best_j=round(best, 3), n_above=above, picked=nct, correct=ok))
        if i % 10 == 0 or i <= 5:
            log("[%3d/%d] %-9s pooled=%-3d win=%-3d best=%.2f %s"
                % (i, len(targets), t["pmid"], len(recs), inwin, best,
                   "CORRECT" if ok else ("picked " + str(nct) if nct else "none")))
        time.sleep(0.34)

    n = sum(1 for r in out if r.get("status") == "ok")
    log("")
    log("searched                        : %d  (failed %d)" % (n, failed))
    if not n:
        log("NOT MEASURABLE: nothing searched.")
        return 1
    if mode == "--ceiling":
        log("true NCT anywhere in pooled set : %d / %d  (%.0f%%)"
            % (hit_set, n, 100.0 * hit_set / n))
        log("cleared the rule                : %d / %d  (%.0f%%)" % (over, n, 100.0 * over / n))
        log("PICKED the true NCT             : %d / %d  (%.0f%%)"
            % (correct, n, 100.0 * correct / n))
        log("")
        log("v3 on its own (now burned) sample: 33%% in-set, 16%% picked correct.")
        log("This sample is fresh -- v4 has never seen it.")
    else:
        log("cleared the rule (a candidate registration found): %d / %d  (%.0f%%)"
            % (over, n, 100.0 * over / n))
        log("Interpretable ONLY against the ceiling measured by --ceiling on fresh data.")

    dst = os.path.join(REPO, "outputs", "findable_v4_%s_2026_08_25.json"
                       % mode.strip("-"))
    json.dump({"mode": mode, "rule": "pooled tiers 4/3/2; year window [-12,+2]; jaccard "
                                     ">=0.50; sponsor breaks ties only",
               "burned_excluded": len(burned), "n": n, "search_failed": failed,
               "in_set": hit_set, "cleared": over, "picked_correct": correct, "rows": out},
              io.open(dst, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(dst, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
