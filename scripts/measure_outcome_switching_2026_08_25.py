"""Does the published primary outcome match the one that was registered?

THE PROSPECTIVE-REGISTRATION GAP, ANSWERED FROM THE OTHER SIDE. Cochrane requires a
prospectively registered protocol; this corpus has none, 0 of 156. Registration exists to
prevent outcome switching -- a team choosing, after seeing the data, to report a different
primary than the one they committed to.

Registry-first identification puts us somewhere a protocol cannot. We read the REGISTERED
primary outcome before we read any publication, so we are positioned to DETECT switching
rather than merely to avoid committing it. A protocol stops one team switching. This detects
switching by anyone.

THE DENOMINATOR IS SMALL AND IT IS NOT RANDOM, and that is stated wherever the number is.
Only 26 of 422 trial records carry BOTH a registered primary outcome and a PMID for the
trial's publication. Those 26 are the trials for which a PMID happened to be recorded during
earlier work -- a convenience sample, not a sample of the corpus. Nothing here generalises to
the other 396 and no rate is projected onto them.

THREE STATES, because two would force a guess:

  CONSISTENT   the abstract states a primary endpoint and it shares its substance with the
               registered one
  DIVERGENT    the abstract states a primary endpoint and it does NOT -- a CANDIDATE for
               switching, never a finding. Endpoints are described in different words by
               different authors, so every candidate needs reading before it is called
               anything.
  UNDECIDABLE  the abstract states no primary endpoint in a form this can find. Not a pass.

WHY DETERMINISTIC RATHER THAN A MODEL. A model comparison of 26 endpoint pairs would produce
26 claims needing their own audit, which is the trade this project spent 2026-08-25 learning
not to make. Token overlap is crude, and crude in a KNOWN direction: it under-detects
agreement between differently-worded synonyms, so it over-produces DIVERGENT candidates. That
is the safe direction here, because a candidate is read before it counts and a missed
candidate never is.
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
import instrument_controls

INPUTS = os.path.join(REPO, "outputs", "_switch_inputs.json")
CACHE = os.path.join(REPO, "outputs", "abstract_cache_2026_08_25.jsonl")
OUT = os.path.join(REPO, "outputs", "outcome_switching_2026_08_25.json")

EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
          "?db=pubmed&retmode=text&rettype=abstract&id=%s")

# How an abstract names its primary endpoint. Deliberately several phrasings; a miss here
# produces UNDECIDABLE, never a false CONSISTENT.
PRIMARY_SENT = re.compile(
    r"(?:the\s+)?(?:pre-?specified\s+|co-)?primary\s+(?:composite\s+)?"
    r"(?:outcome|end\s?point|efficacy\s+(?:outcome|end\s?point)|measure)s?\b"
    r"[^.]{0,400}", re.I)

_STOP = {"the", "a", "an", "of", "or", "and", "to", "in", "for", "with", "at", "by", "was",
         "were", "is", "are", "from", "on", "as", "that", "this", "which", "first",
         "occurrence", "number", "participants", "patients", "time", "up", "months",
         "years", "week", "weeks", "day", "days", "change", "baseline", "primary",
         "outcome", "outcomes", "endpoint", "endpoints", "end", "point", "points",
         "composite", "measure", "measures", "study", "trial", "rate", "incidence"}


def words(s):
    return {w for w in re.split(r"[^a-z0-9]+", (s or "").lower())
            if len(w) > 3 and w not in _STOP}


def fetch_abstract(pmid):
    """(text, ok). A failed fetch is recorded as a failure, never as an empty abstract."""
    try:
        p = subprocess.run(["curl", "-sL", "-m", "45", "-w", "\n%{http_code}", EFETCH % pmid],
                           capture_output=True, timeout=60)
        raw = (p.stdout or b"").decode("utf-8", "replace")
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)
    if "\n" not in raw:
        return None, "no response body"
    body, code = raw.rsplit("\n", 1)
    if code.strip() != "200":
        return None, "HTTP %s" % code.strip()
    if len(body.strip()) < 200:
        return None, "response too short to be an abstract (%d bytes)" % len(body.strip())
    return body, "ok"


def compare(registered, abstract):
    """(state, overlap, quoted). Never guesses when the abstract names no primary."""
    m = PRIMARY_SENT.search(abstract or "")
    if not m:
        return "UNDECIDABLE", None, ""
    said = " ".join(m.group(0).split())
    rw = words(" ".join(registered) if isinstance(registered, list) else registered)
    aw = words(said)
    if not rw:
        return "UNDECIDABLE", None, said[:200]
    overlap = len(rw & aw) / float(len(rw))
    # 0.34 chosen so that one shared substantive term out of three counts as agreement --
    # deliberately generous, because the failure mode being avoided is calling a differently
    # worded but identical endpoint a divergence.
    return ("CONSISTENT" if overlap >= 0.34 else "DIVERGENT"), round(overlap, 3), said[:260]


def control():
    """Known answers, both directions, before any count is printed."""
    same = compare(["All-cause mortality or worsening heart failure requiring unplanned "
                    "hospitalization"],
                   "The primary outcome was a composite of all-cause mortality or worsening "
                   "heart failure requiring unplanned hospitalization.")
    diff = compare(["Percent change in LDL cholesterol from baseline to week 24"],
                   "The primary endpoint was the incidence of adjudicated major adverse "
                   "cardiovascular events.")
    none = compare(["Anything at all"], "This abstract describes methods and says nothing "
                                        "about which endpoint came first.")
    instrument_controls.require_controls(
        "outcome-switching",
        ("an abstract restating its registered primary in the same words -> CONSISTENT",
         same[0], "CONSISTENT"),
        ("an abstract naming a completely different endpoint -> must not be CONSISTENT",
         diff[0], "CONSISTENT"))
    if none[0] != "UNDECIDABLE":
        raise instrument_controls.ControlFailed(
            "REFUSED: an abstract that names no primary endpoint came back %r instead of "
            "UNDECIDABLE. NO COUNT IS PRINTED." % none[0])
    print("CONTROL (third state) an abstract naming no primary endpoint -> UNDECIDABLE")
    return True


def main():
    control()
    if not os.path.exists(INPUTS):
        print("REFUSED: %s missing." % os.path.relpath(INPUTS, REPO))
        return 2
    d = json.load(io.open(INPUTS, encoding="utf-8"))
    pm, regs = d["pm_by_nct"], d["regs"]
    pairs = sorted([(n, pm[n]) for n in pm if n in regs])

    cache = {}
    if os.path.exists(CACHE):
        for line in io.open(CACHE, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("pmid"):
                cache[r["pmid"]] = r

    rows, failed = [], []
    for nct, pmid in pairs:
        rec = cache.get(pmid)
        if not rec or rec.get("status") != "ok":
            text, why = fetch_abstract(pmid)
            rec = {"pmid": pmid, "status": "ok" if text else "error",
                   "why": why, "text": text or ""}
            with io.open(CACHE, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            time.sleep(0.4)
        if rec.get("status") != "ok":
            failed.append((nct, pmid, rec.get("why")))
            continue
        state, ov, said = compare(regs[nct], rec["text"])
        rows.append({"nct": nct, "pmid": pmid, "state": state, "overlap": ov,
                     "registered": regs[nct], "abstract_says": said})

    n = len(rows)
    cnt = {s: sum(1 for r in rows if r["state"] == s) for s in
           ("CONSISTENT", "DIVERGENT", "UNDECIDABLE")}
    print()
    print("trial records in the whole corpus                    : 422")
    print("with BOTH a registered primary and a publication PMID: %d" % len(pairs))
    print("abstracts retrieved                                  : %d   (%d failed)"
          % (n, len(failed)))
    print()
    print("  CONSISTENT  %2d" % cnt["CONSISTENT"])
    print("  DIVERGENT   %2d   <- CANDIDATES for outcome switching, not findings" % cnt["DIVERGENT"])
    print("  UNDECIDABLE %2d   <- the abstract names no primary endpoint. Not a pass." % cnt["UNDECIDABLE"])
    print()
    print("THE DENOMINATOR IS A CONVENIENCE SAMPLE. These %d are the trials for which a PMID"
          % len(pairs))
    print("happened to be recorded in earlier work. No rate here is projected onto the other")
    print("%d trial records, and none should be." % (422 - len(pairs)))
    if cnt["DIVERGENT"]:
        print()
        print("candidates, each needing to be read before it is called anything:")
        for r in rows:
            if r["state"] == "DIVERGENT":
                print("  %s (pmid %s, overlap %.2f)" % (r["nct"], r["pmid"], r["overlap"]))
                print("     registered: %s" % str(r["registered"])[:110])
                print("     abstract  : %s" % r["abstract_says"][:110])
    if failed:
        print()
        print("fetch failures, recorded as failures and not as absent abstracts: %d" % len(failed))
        for f in failed[:8]:
            print("   %-13s pmid %-9s %s" % f)
    json.dump({"n_corpus_records": 422, "n_with_both": len(pairs), "rows": rows,
               "failed": failed}, io.open(OUT, "w", encoding="utf-8"), indent=1)
    print()
    print("written: %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
