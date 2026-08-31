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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import search_ids  # noqa: E402  -- the one definition of the `ids` field, shared

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
    """Run the free sources and record, for each, THE SET IT RETURNED -- not only the count.

    ⭐ THE `ids` FIELD IS THE POINT OF THIS FUNCTION NOW. Every identifier below was already
    in hand -- PubMed's `idlist`, Europe PMC's `result` array, the NCTs parsed out of the
    ClinicalTrials.gov body -- and every one of them was thrown away, leaving a `retrieved`
    count that nothing could recompute. Unique yield, pairwise overlap and a coverage
    fraction are all derivable from the sets and NONE of them is derivable from the counts.

    ⛔ AND A FAILED SOURCE GETS `ids: null` WITH A REASON, NEVER `ids: []`. An empty list is
    a claim that the source ran and found nothing. A source that returned HTTP 500 has made
    no claim at all, and recording it as an empty set would let every other source score the
    records it never saw as uniquely its own. See scripts/search_ids.py.
    """
    rows = []
    q = " OR ".join('"%s"[All Fields]' % t for t in terms)
    d, st = _json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"
                  "&retmax=500&retmode=json&term=%s" % urllib.parse.quote(q))
    pm = (((d or {}).get("esearchresult") or {}).get("idlist")) or [] if d else None
    n = int((((d or {}).get("esearchresult") or {}).get("count")) or 0) if d else None
    got = len(pm) if pm is not None else 0
    row = {"source": "PubMed", "status": st if st != "OK" else
           ("TRUNCATED" if (n or 0) > got else "OK"),
           "reported": n, "retrieved": got, "query": q}
    row.update(search_ids.make("pmid", ids=pm) if pm is not None else
               search_ids.make("pmid", absent_because="the PubMed request did not return a "
                                                      "parseable response (%s)" % st))
    rows.append(row)

    q2 = _query(terms)
    d2, st2 = _json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%s"
                    "&format=json&pageSize=1000&resultType=idlist"
                    % urllib.parse.quote(q2))
    hits = (d2 or {}).get("hitCount")
    res = ((d2 or {}).get("resultList") or {}).get("result") or [] if d2 else None
    # Europe PMC's own key namespace -- PMC/PPR/ETH/PAT prefixes and bare MED accessions.
    # Stored in ITS namespace, not translated into PMIDs, because a translation is a lossy
    # join and the record must say what THIS source returned.
    epmc = [r.get("id") for r in res if r.get("id")] if res is not None else None
    # ⚠️ THREE COUNTS HERE, NOT TWO, AND THEY ARE CARRIED SEPARATELY. `reported` is what the
    # server says it holds, `result_rows` is what it sent, and `retrieved` is how many of
    # those rows carried an identifier we could store. A result row with no `id` would make
    # the last two differ, and folding them would hide a record we cannot name while still
    # counting it.
    row = {"source": "Europe PMC",
           "status": st2 if st2 != "OK" else
           ("TRUNCATED" if isinstance(hits, int) and len(epmc or []) < hits else "OK"),
           "reported": hits, "result_rows": len(res or []),
           "retrieved": len(epmc or []), "query": q2}
    row.update(search_ids.make("europepmc", ids=epmc) if epmc is not None else
               search_ids.make("europepmc",
                               absent_because="the Europe PMC request did not return a "
                                              "parseable response (%s)" % st2))
    rows.append(row)

    # ⚠️ THE TWO ARMS ARE RECORDED SEPARATELY AS WELL AS UNIONED. On dapivirine the
    # intervention arm was a STRICT SUBSET of the free-text arm and contributed nothing
    # unique -- a fact that was only visible once the identifier sets were carried, and that
    # the union count alone can never show. The condition for retiring the arm is stated in
    # ctgov()'s docstring in systematic_search_dapivirine.py and needs three topics; keeping
    # per-arm ids here is what makes those three topics measurable instead of re-argued.
    ncts, ct_status, arms = set(), [], []
    for param in ("query.intr", "query.term"):
        body, code = _curl("https://clinicaltrials.gov/api/v2/studies?%s=%s&pageSize=200"
                           "&fields=NCTId,BriefTitle,OverallStatus,Phase,"
                           "DesignAllocation,StudyType,InterventionName,EnrollmentCount"
                           % (param, urllib.parse.quote(q2)))
        arm = {"param": param}
        if code != "200":
            ct_status.append("FAILED_HTTP_%s" % code)
            arm["status"] = "FAILED_HTTP_%s" % code
            arm.update(search_ids.make("nct", absent_because="HTTP %s -- the arm did not "
                                                             "answer" % code))
            arms.append(arm)
            continue
        got_ids = sorted(set(re.findall(r"NCT\d{8}", body)))
        ncts |= set(got_ids)
        ct_status.append("OK")
        arm["status"] = "OK"
        arm.update(search_ids.make("nct", ids=got_ids))
        arms.append(arm)
    row = {"source": "ClinicalTrials.gov (intr U term)",
           "status": "OK" if "OK" in ct_status else ";".join(ct_status),
           "reported": None, "retrieved": len(ncts), "query": q2, "arms": arms}
    row.update(search_ids.make("nct", ids=sorted(ncts)) if "OK" in ct_status else
               search_ids.make("nct", absent_because="no ClinicalTrials.gov arm answered "
                                                     "(%s)" % ";".join(ct_status)))
    rows.append(row)

    # ⭐ THE COUNT WE PUBLISH IS NOW CHECKABLE AGAINST THE SET, WHICH IS THE WHOLE POINT.
    # `retrieved` is the assertion target, not `reported`: `reported` is what the server SAID
    # it holds and the gap between them is the TRUNCATED status, which is a separate finding
    # and must not be collapsed into this one.
    for r in rows:
        ok, detail = search_ids.reconcile(r, r.get("retrieved"))
        r["ids_reconcile"] = {"ok": ok, "detail": detail,
                              "state": search_ids.state(r)}
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
    # ⭐ THE SENTENCE A SUBSCRIPTION REVIEW CANNOT WRITE, as data. Derived from the sets and
    # not computable from the counts, which is the entire reason the sets are now carried.
    #
    # ⚠️ WHICH CROSS-NAMESPACE PAIRS MEAN SOMETHING, AND THE FIRST LIVE RUN CORRECTED ME.
    #
    # I wrote here that a pair of sources in different namespaces can only ever intersect in
    # zero, so no such pair is interpretable. THE FIRST RUN FALSIFIED IT: on ser109-cdi,
    # PubMed returned 77 and Europe PMC 548, and they share 76. Europe PMC's namespace
    # CONTAINS PubMed's -- its bare-numeric accessions are the MED source, which is MEDLINE,
    # which is PMIDs. The overlap is real and PubMed's unique yield of 1 is a real finding.
    #
    # ⇒ THE CORRECT RULE IS ABOUT CONTAINMENT, NOT ABOUT DIFFERENCE. Two namespaces are
    # comparable when one is drawn from the other (europepmc contains pmid). They are NOT
    # comparable when they are disjoint by construction (nct against pmid), and there a zero
    # intersection is arithmetic about id schemes rather than evidence about two searches.
    # Every row carries `id_namespace` so a reader can apply that test rather than trust it.
    pairs = [(r["source"], r) for r in rows]
    arm_pairs = [("%s [%s]" % (r["source"], a["param"]), a)
                 for r in rows for a in (r.get("arms") or [])]
    derived = {
        "unique_yield": search_ids.unique_yield(pairs),
        "pairwise_overlap": search_ids.pairwise_overlap(pairs),
        "ctgov_arm_unique_yield": search_ids.unique_yield(arm_pairs) if arm_pairs else None,
        "namespaces": {r["source"]: r.get("id_namespace") for r in rows},
        "namespace_comparability_rule": (
            "A pair is interpretable when one namespace is DRAWN FROM the other -- Europe "
            "PMC's bare-numeric accessions are MEDLINE records, so europepmc contains pmid "
            "and their overlap is real evidence. A pair whose namespaces are disjoint by "
            "construction (nct against pmid) can only ever show 0, and that zero is "
            "arithmetic about id schemes, not evidence about two searches. MEASURED, not "
            "assumed: on ser109-cdi PubMed returned 77 and Europe PMC 548, sharing 76."),
    }
    return {"topic": topic, "status": "OK", "executed_utc": started,
            "question": obj.get("question"), "title": obj.get("title"),
            "concept_block": cb, "sources": rows, "derived": derived,
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
        print("  %-34s %-16s reported=%-7s retrieved=%-6s ids=%s [%s]"
              % (s["source"], s["status"], s["reported"], s["retrieved"],
                 "null" if s.get("ids") is None else len(s["ids"]),
                 s["ids_reconcile"]["state"]))
        if s["ids_reconcile"]["ok"] is False:
            print("      IDS DO NOT RECONCILE: %s" % s["ids_reconcile"]["detail"])
    uy = r["derived"]["unique_yield"]
    print()
    print("  UNIQUE YIELD  (sources counted %d, skipped %s, candidates %d)"
          % (uy["sources_counted"], uy["sources_skipped"] or "{}", uy["candidates"]))
    for lab, v in sorted(uy["per_source"].items()):
        print("     %-34s returned %-6d unique %d" % (lab, v["returned"], v["unique"]))
    print("     %-34s %d" % ("union", uy["union"]))
    print("  ⚠️ a pair is interpretable only where one namespace is drawn from the other")
    print("     -- see derived.namespace_comparability_rule")
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
