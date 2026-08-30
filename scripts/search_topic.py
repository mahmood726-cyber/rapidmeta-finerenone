# -*- coding: utf-8 -*-
"""A REPEATABLE search procedure: give it a topic, it runs the search and reports coverage.

⭐ WHY THIS EXISTS RATHER THAN AN EIGHTH COPY OF THE DAPIVIRINE SCRIPT. The dapivirine
search closed the biggest axis loss on the board -- search was raised in five of six blinded
verdicts and lost every one -- but it was written by hand, with its concept block typed in.
Eight topics need eight searches, and if the second costs what the first cost we will never
finish. That is the same lesson this project already learned as "69% bespoke": a capability
that must be re-authored per topic is not a capability.

⇒ SO THE PROCEDURE IS THE ARTEFACT. Given a topic, it derives the concept block, runs the
free sources, screens the registry hits mechanically, and emits a record with a coverage
fraction. Nothing here is dapivirine-specific.

⚠️ WHAT IT DERIVES AND WHAT IT REFUSES TO DERIVE.

DERIVED: the intervention's synonyms, from two free authorities rather than from a guess --
NLM RxNorm (brand, generic, precise ingredient) and MeSH entry terms via E-utilities. That
is what made the dapivirine search work: `TMC 120` and `R 147681` are MeSH entry terms, and
a query without them loses the phase 1/2 and development-programme literature. Deriving
them per topic is the whole point; typing them per topic is what we are escaping.

NOT DERIVED: eligibility. The screen below is MECHANICAL only -- is the drug present, is it
interventional, is it randomised. ⛔ IT DOES NOT JUDGE THE COMPARATOR OR THE OUTCOME, because
those are the review's own PICO and a machine reading a registry record cannot settle them.
Candidates that pass the mechanical screen are emitted for ADJUDICATION and the coverage
fraction REFUSES until every one carries a verdict. On dapivirine three candidates passed
and all three were eligibility exclusions -- oral Truvada comparators and a
service-delivery trial -- and reporting that raw difference as a recall figure would have
manufactured three misses that do not exist.

⚠️ AND THE INTERVENTION TERM IS A CANDIDATE, NOT A FACT. It is extracted from the object's
own title and question and RECORDED in the output so a reader can see what was searched.
If it is wrong the whole search is wrong, so it is surfaced rather than buried.

⛔⛔ MEASURED LIMITATION, 2026-08-30, AND IT QUALIFIES THE COST CLAIM THIS FILE WAS BUILT ON.

Run across 18 live topics at 8.7 s each, the SEARCH generalises and the SCREEN does not.
The mechanical screen's precision is entirely topic-dependent:

    ser109-cdi        4 registrations ->   2 candidates   usable as it stands
    agyw-hiv-prep    56 registrations ->  35 candidates   needs real screening
    arni-hfref      ~.. registrations -> 105 candidates   a whole drug programme
    colchicine-*                      -> 125 candidates   on every one of six topics

⇒ "Topic 2 cost 5.9 seconds" is TRUE OF THE SEARCH AND FALSE OF THE WORK. SER-109 was cheap
because four registrations exist for it. A widely studied drug returns its entire
development programme, and the expensive step -- deciding which of 125 trials match the
review's comparator, population and outcome -- is exactly the step that has NOT been
generalised and cannot be, because it is the review's PICO.

⛔ AND AN INTERVENTION-ONLY CONCEPT BLOCK CANNOT DISTINGUISH TOPICS THAT DIFFER BY
POPULATION. The six colchicine topics -- intracerebral haemorrhage, mixed ASCVD,
pericarditis, peripheral arterial, periprocedural, stroke prevention -- return the IDENTICAL
125 candidates, because the block is built from the drug alone. For those topics this
procedure narrows nothing, and a "gap" computed from its output would be meaningless.

⚠️ SO A LARGE CANDIDATE COUNT IS NOT A SEARCH GAP. Subtracting held trials from candidates
gives a number that looks like missing evidence and is not: on dapivirine three candidates
passed and all three were eligibility exclusions. The coverage fraction therefore REFUSES
until each candidate is adjudicated, and that refusal is the only thing standing between
this procedure and a fabricated recall statistic.
"""
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

UA = "rapidmeta-systematic-review/1.0 (mailto:mahmood726@gmail.com)"

# Words that are never the intervention, so a title-derived candidate does not become
# "adults" or "compared". Deliberately small: over-filtering here loses real drug names.
STOP = set("""a an the of for in on with versus vs compared comparison against and or to
does do is are what how much adults adult patients people women men children infants
effect effects efficacy safety trial trials study studies review randomised randomized
placebo controlled outcome outcomes risk reduce reduces reducing change from baseline
treatment therapy prevention among after before during high low first total""".split())


def _curl(url, tries=4):
    for i in range(tries):
        r = subprocess.run(["curl", "-sL", "--max-time", "60", "-A", UA,
                            "-w", "\n__H__%{http_code}", url], capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        code = out.rsplit("__H__", 1)[-1].strip() if "__H__" in out else "000"
        body = out.rsplit("\n__H__", 1)[0]
        if code == "200":
            return body, code
        if code.startswith("5") or code in ("000", "429"):
            if i < tries - 1:
                time.sleep(2 * (i + 1))
                continue
        return body, code
    return "", "000"


def _json(url):
    b, c = _curl(url)
    if c != "200":
        return None, "FAILED_HTTP_%s" % c
    try:
        return json.loads(b), "OK"
    except ValueError:
        return None, "FAILED_UNPARSEABLE"


# ------------------------------------------------------------------ concept derivation

def candidate_intervention(obj):
    """The intervention term, taken from the object's OWN title and question.

    Returns (term, how_it_was_derived). ⚠️ A CANDIDATE, not a fact -- surfaced in the
    output because if it is wrong every count below is wrong.
    """
    title = str(obj.get("title") or "")
    q = str(obj.get("question") or "")
    # The first content word of the title is the intervention in this corpus's naming
    # convention ("Dapivirine vaginal ring versus placebo ring...").
    for src, label in ((title, "object title"), (q, "object question")):
        for w in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", src):
            if w.lower() in STOP:
                continue
            return w, "first content word of the %s: %r" % (label, src[:80])
    return None, "no title or question on this object"


# Words that describe a study rather than a population, stripped before the population
# terms are built. Kept small on purpose: over-filtering loses real condition words.
POP_STOP = set("""adults adult patients people women men children infant infants
participants subjects with without versus compared placebo controlled randomised
randomized trial trials study studies effect effects each own registered primary
outcome outcomes what does how much reduce reduces reducing change baseline from
treatment therapy prevention risk high low first total the a an of for in on and or
to is are its their""".split())


def population_terms(obj, intervention):
    """The POPULATION arm of the block, derived from the object's own title and question.

    ⛔ THIS IS USED TO SCREEN, NEVER TO SEARCH, AND THE DISTINCTION IS THE WHOLE POINT.
    ANDing a population block into the query would cost recall -- a trial that never spells
    the condition in its title would vanish -- and recall is what the drug-only block exists
    to protect. So the search stays broad and the SCREEN gains a population signal.

    ⚠️ WITHOUT THIS THE PROCEDURE CANNOT TELL SIX TOPICS APART. colchicine-pericarditis,
    colchicine-stroke-prevention, colchicine-mixed-ascvd, colchicine-periprocedural,
    colchicine-peripheral-arterial and colchicine-intracerebral-haemorrhage all returned the
    IDENTICAL 125 candidates on 2026-08-30, because the block was built from the drug alone.
    A procedure that narrows nothing on precisely the topics where narrowing matters is not
    a procedure.
    """
    src = " ".join([str(obj.get("title") or ""), str(obj.get("question") or "")])
    iv = (intervention or "").lower()
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z-]{3,}", src)]
    terms = []
    for w in words:
        lw = w.lower()
        if lw in POP_STOP or lw == iv or lw in iv or iv in lw:
            continue
        if lw not in [t.lower() for t in terms]:
            terms.append(w)
    return terms[:12]


def rxnorm_synonyms(term):
    """NLM RxNorm. Free, no key. Returns names, or an empty list with a status."""
    d, st = _json("https://rxnav.nlm.nih.gov/REST/rxcui.json?name=%s&search=2"
                  % urllib.parse.quote(term))
    if st != "OK":
        return [], st
    ids = ((d.get("idGroup") or {}).get("rxnormId")) or []
    if not ids:
        return [], "NO_RXCUI"
    out = set()
    d2, st2 = _json("https://rxnav.nlm.nih.gov/REST/rxcui/%s/allProperties.json"
                    "?prop=names" % ids[0])
    if st2 != "OK":
        return [], st2
    for p in (((d2 or {}).get("propConceptGroup") or {}).get("propConcept") or []):
        v = (p.get("propValue") or "").strip()
        if 2 < len(v) < 60:
            out.add(v)
    return sorted(out), "OK"


def mesh_entry_terms(term):
    """MeSH entry terms, including SUPPLEMENTARY CONCEPT records.

    ⭐ THIS IS THE STEP THAT EARNED ITS PLACE. Dapivirine is only a Supplementary Concept in
    MeSH, and its entry terms `TMC 120` and `R 147681` are what the early literature uses.
    A concept block without them silently loses that end of the record -- which is exactly
    the kind of miss nobody notices, because the search still returns plenty.
    """
    d, st = _json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=mesh"
                  "&retmode=json&retmax=3&term=%s" % urllib.parse.quote(term))
    if st != "OK":
        return [], st
    ids = ((d.get("esearchresult") or {}).get("idlist")) or []
    if not ids:
        return [], "NO_MESH_RECORD"
    body, code = _curl("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=mesh"
                       "&rettype=full&retmode=text&id=%s" % ",".join(ids))
    if code != "200":
        return [], "FAILED_HTTP_%s" % code
    terms = set()
    for m in re.finditer(r"^Entry Terms?:?\s*(.*)$", body, re.M):
        pass
    # The MeSH text report lists entry terms one per line after "Entry Terms:".
    blocks = re.split(r"\n\s*\n", body)
    for b in blocks:
        if re.search(r"entry term", b, re.I):
            for line in b.splitlines()[1:]:
                v = line.strip(" \t-")
                if 2 < len(v) < 60 and not v.lower().startswith("entry term"):
                    terms.add(v)
    return sorted(terms), "OK"


def build_concept_block(obj):
    term, how = candidate_intervention(obj)
    rec = {"candidate_intervention": term, "derived_how": how,
           "warning": ("A CANDIDATE, not a fact. If this term is wrong every count below "
                       "is wrong, so it is reported rather than assumed.")}
    if not term:
        rec["status"] = "NO_INTERVENTION_DERIVED"
        rec["terms"] = []
        return rec
    rx, rx_st = rxnorm_synonyms(term)
    mesh, mesh_st = mesh_entry_terms(term)
    terms = {term}
    terms |= {t for t in rx if re.search(r"[A-Za-z]", t)}
    terms |= {t for t in mesh if re.search(r"[A-Za-z]", t)}
    rec.update({"rxnorm_status": rx_st, "rxnorm_names": rx,
                "mesh_status": mesh_st, "mesh_entry_terms": mesh,
                "terms": sorted(terms), "status": "OK"})
    return rec


# ------------------------------------------------------------------------ the sources

def _query(terms):
    return " OR ".join('"%s"' % t for t in terms)


def run_sources(terms):
    rows = []
    q = " OR ".join('"%s"[All Fields]' % t for t in terms)
    d, st = _json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"
                  "&retmax=500&retmode=json&term=%s" % urllib.parse.quote(q))
    n = int((((d or {}).get("esearchresult") or {}).get("count")) or 0) if d else None
    got = len((((d or {}).get("esearchresult") or {}).get("idlist")) or []) if d else 0
    rows.append({"source": "PubMed", "status": st if st != "OK" else
                 ("TRUNCATED" if (n or 0) > got else "OK"),
                 "reported": n, "retrieved": got, "query": q})

    q2 = _query(terms)
    d2, st2 = _json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%s"
                    "&format=json&pageSize=1000&resultType=idlist"
                    % urllib.parse.quote(q2))
    hits = (d2 or {}).get("hitCount")
    res = ((d2 or {}).get("resultList") or {}).get("result") or []
    rows.append({"source": "Europe PMC",
                 "status": st2 if st2 != "OK" else
                 ("TRUNCATED" if isinstance(hits, int) and len(res) < hits else "OK"),
                 "reported": hits, "retrieved": len(res), "query": q2})

    ncts, ct_status = set(), []
    for param in ("query.intr", "query.term"):
        body, code = _curl("https://clinicaltrials.gov/api/v2/studies?%s=%s&pageSize=200"
                           "&fields=NCTId,BriefTitle,OverallStatus,Phase,"
                           "DesignAllocation,StudyType,InterventionName,EnrollmentCount"
                           % (param, urllib.parse.quote(q2)))
        if code != "200":
            ct_status.append("FAILED_HTTP_%s" % code)
            continue
        ncts |= set(re.findall(r"NCT\d{8}", body))
        ct_status.append("OK")
    rows.append({"source": "ClinicalTrials.gov (intr ∪ term)",
                 "status": "OK" if "OK" in ct_status else ";".join(ct_status),
                 "reported": None, "retrieved": len(ncts), "query": q2})
    return rows, sorted(ncts)


def mechanical_screen(ncts, terms, pop_terms=None):
    """⛔ MECHANICAL ONLY. Never judges comparator or outcome -- those are the PICO.

    Candidates are additionally flagged for POPULATION OVERLAP with the review's own
    question. ⚠️ THE FLAG RANKS, IT DOES NOT EXCLUDE: a trial whose registry record never
    spells the condition is not thereby ineligible, and dropping it would be the mechanical
    screen quietly deciding the P of the PICO. Candidates with no overlap are still
    emitted, marked, and still require adjudication.
    """
    if not ncts:
        return {"candidates": [], "excluded": {}, "note": "no registrations returned"}
    body, code = _curl("https://clinicaltrials.gov/api/v2/studies?filter.ids=%s"
                       "&pageSize=400&fields=NCTId,BriefTitle,OverallStatus,Phase,"
                       "DesignAllocation,StudyType,InterventionName,EnrollmentCount"
                       % urllib.parse.quote(",".join(ncts)))
    if code != "200":
        return {"candidates": [], "excluded": {}, "note": "FAILED_HTTP_%s" % code}
    try:
        j = json.loads(body)
    except ValueError:
        return {"candidates": [], "excluded": {}, "note": "FAILED_UNPARSEABLE"}
    rx = re.compile("|".join(re.escape(t) for t in terms), re.I)
    poprx = (re.compile("|".join(re.escape(t) for t in pop_terms), re.I)
             if pop_terms else None)
    cands, excl = [], {"drug_not_named": 0, "not_interventional": 0,
                       "not_randomised": 0, "withdrawn_zero_participants": 0}
    withdrawn = []
    for s in j.get("studies") or []:
        p = s.get("protocolSection") or {}
        idm = p.get("identificationModule") or {}
        des = p.get("designModule") or {}
        arm = p.get("armsInterventionsModule") or {}
        st = (p.get("statusModule") or {}).get("overallStatus")
        n = (des.get("enrollmentInfo") or {}).get("count")
        blob = (idm.get("briefTitle") or "") + " " + " ".join(
            i.get("name", "") for i in (arm.get("interventions") or []))
        nct = idm.get("nctId")
        if not rx.search(blob):
            excl["drug_not_named"] += 1
            continue
        if des.get("studyType") != "INTERVENTIONAL":
            excl["not_interventional"] += 1
            continue
        if st == "WITHDRAWN" or n == 0:
            excl["withdrawn_zero_participants"] += 1
            withdrawn.append(nct)
            continue
        if (des.get("designInfo") or {}).get("allocation") != "RANDOMIZED":
            excl["not_randomised"] += 1
            continue
        conds = " ".join((p.get("conditionsModule") or {}).get("conditions") or [])
        hay = blob + " " + conds
        hits = sorted({m.group(0).lower() for m in poprx.finditer(hay)}) if poprx else []
        # ⚠️ TWO DISTINCT TERMS, NOT ONE. A single generic word is not a population match.
        # Measured 2026-08-30: with a one-hit rule, "Thromboprophylaxis After Trauma"
        # scored as intracerebral haemorrhage on the word "after", and a chronic kidney
        # disease trial scored as stroke prevention on "disease". Requiring two distinct
        # terms drops those while keeping the true ones -- the SER-109 trials match
        # clostridium, difficile AND infection. The rule is arbitrary in the way any
        # threshold is; it is stated rather than tuned until the answer looked good.
        cands.append({"nct": nct, "title": (idm.get("briefTitle") or "")[:110],
                      "phase": ",".join(des.get("phases") or []), "enrolment": n,
                      "population_overlap": hits,
                      "population_matched": len(hits) >= 2,
                      "ELIGIBLE": None, "ELIGIBILITY_REASON": ""})
    return {"candidates": cands, "excluded": excl, "withdrawn_named": withdrawn,
            "screen_is": ("MECHANICAL ONLY: drug named, interventional, randomised, "
                          "actually enrolled. It does NOT judge the comparator or the "
                          "outcome -- those are the review's PICO and must be adjudicated "
                          "by a person.")}


def search(topic, root="."):
    path = os.path.join(root, "ssot", topic, "%s.json" % topic)
    if not os.path.exists(path):
        return {"topic": topic, "status": "OBJECT_NOT_FOUND", "path": path}
    obj = json.load(open(path, encoding="utf-8"))
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cb = build_concept_block(obj)
    if not cb.get("terms"):
        return {"topic": topic, "status": "NO_CONCEPT_BLOCK", "concept_block": cb}
    pop = population_terms(obj, cb.get("candidate_intervention"))
    cb["population_terms"] = pop
    cb["population_terms_are_for"] = (
        "SCREENING ONLY, never the query. ANDing them into the search would cost recall.")
    rows, ncts = run_sources(cb["terms"])
    scr = mechanical_screen(ncts, cb["terms"], pop)
    return {"topic": topic, "status": "OK", "executed_utc": started,
            "question": obj.get("question"), "title": obj.get("title"),
            "concept_block": cb, "sources": rows,
            "registrations": len(ncts), "screen": scr,
            "coverage_fraction": {
                "status": "REFUSED_PENDING_ADJUDICATION",
                "because": ("%d candidate(s) passed the mechanical screen and none has an "
                            "eligibility verdict yet. A raw difference is not a recall "
                            "figure." % len(scr.get("candidates") or []))},
            "sha256_16": hashlib.sha256(
                json.dumps(rows, sort_keys=True).encode()).hexdigest()[:16]}


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    topic = sys.argv[1] if len(sys.argv) > 1 else "agyw-hiv-prep-review"
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    t0 = time.time()
    r = search(topic, root)
    el = time.time() - t0
    print("TOPIC: %s   (%s)" % (topic, r["status"]))
    if r["status"] != "OK":
        print(json.dumps(r, indent=1)[:800]); sys.exit(0)
    cb = r["concept_block"]
    print("  candidate intervention : %r  (%s)"
          % (cb["candidate_intervention"], cb["derived_how"][:70]))
    print("  RxNorm %-14s MeSH %s" % (cb["rxnorm_status"], cb["mesh_status"]))
    print("  concept block (%d terms): %s" % (len(cb["terms"]), cb["terms"][:10]))
    print()
    for s in r["sources"]:
        print("  %-34s %-16s reported=%-7s retrieved=%s"
              % (s["source"], s["status"], s["reported"], s["retrieved"]))
    sc = r["screen"]
    print()
    print("  registrations: %d | passed mechanical screen: %d | excluded: %s"
          % (r["registrations"], len(sc.get("candidates") or []), sc.get("excluded")))
    for c in (sc.get("candidates") or [])[:12]:
        print("     %-12s %-8s n=%-6s %s" % (c["nct"], c["phase"], c["enrolment"],
                                             c["title"][:58]))
    print()
    print("  coverage: %s" % r["coverage_fraction"]["status"])
    print("  %s" % r["coverage_fraction"]["because"])
    print("\n  WALL CLOCK: %.1f s" % el)
    out = os.environ.get("TOPIC_SEARCH_OUT",
                         "F:/claude-temp/search_%s.json" % topic)
    json.dump(r, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("  written to %s" % out)
