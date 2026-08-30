# -*- coding: utf-8 -*-
"""Recover a BORROWED outcome from the primary trials — for any topic, any outcome.

⛔ THE GENERAL FORM OF THE AXIS LOSS, AND IT WILL BE TRUE OF ALL EIGHT TOPICS:
***A REVIEW WHOSE OUTCOMES ARE BORROWED FROM ITS COMPARATOR CANNOT BE DECISIVELY BETTER THAN IT
ON SCOPE.*** On that axis it is a copy of the thing it is being compared with. Blinded judges
gave outcome scope to the comparator 0 of 2, and every topic that leans on a Cochrane review for
a number will lose the same way.

⚠️ AND THE FIRST FIX FOR IT WAS ITSELF BESPOKE, which is the same defect one level up.
`apply_sti_primary_read_2026_08_30.py` hardcoded two trials, five organism names and two source
dictionaries: it recovers dapivirine's STI outcomes and nothing else. **A BESPOKE FIX IS AS
UNSCALABLE AS A BESPOKE PAGE** -- seven more topics would have cost seven more afternoons. This
module is that script's content removed and its METHOD kept.

WHAT IT TAKES AND WHAT IT LANDS.

    recover(canon, fetch)   ->  for every row whose tier is BORROWED, read the topic's own
                                trial primaries and land a typed `primary_read` block.

The trials come from the object's `sources` registry, never from an argument, so the component
cannot be pointed at the wrong evidence. The outcome TERM comes from the row's own name. The
fetch function is INJECTED, so the module is testable offline and carries no vendor dependency.

⭐ THREE RETRIEVAL STATES, AND THE THIRD IS THE ONE THAT KEEPS GETTING COLLAPSED:

    RETRIEVED_QUALITATIVE_ONLY    the document was read; it states a direction, gives no figure
    RETRIEVED_NO_VALUE            the document was read; the value is NOT IN IT
    NOT_RETRIEVABLE_OPEN_ACCESS   the document COULD NOT BE READ AT ALL

The third is a fact about THIS REVIEW'S REACH, not about the trial -- a paywalled trial may
report the outcome perfectly well. Collapsing it into "no data" reports our limitation as a
property of the evidence, which is the same error as a scan reporting its own reach as coverage.

⛔ WHAT IT WILL NOT DO. It will not write a NUMBER into a row. Reading a figure out of a
retrieved document and typing it as a result is extraction, and extraction needs its own
verification; this component establishes only WHETHER the primary carries the outcome and, when
the primary speaks qualitatively, quotes it verbatim. A component that could silently invent a
value is worse than the borrowed row it replaces.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

MARKER = "primary_read"

BORROWED_TIERS = ("prior-meta table (unverified)", "prior-meta table", "comparator")

STATE_QUALITATIVE = "RETRIEVED_QUALITATIVE_ONLY"
STATE_NO_VALUE = "RETRIEVED_NO_VALUE"
STATE_UNREADABLE = "NOT_RETRIEVABLE_OPEN_ACCESS"

# A sentence carrying the outcome term AND a comparative reading, with no digits, is the
# qualitative form. With digits it is a figure this component refuses to extract.
_COMPARATIVE = ("similar", "no difference", "no significant", "comparable", "did not differ",
                "no material difference", "equally", "same rate", "no effect")


def _utf8_stdout():
    """Wrap stdout ONCE. Two functions each wrapping it closed the first wrapper's buffer.

    ⛔ THIS EXACT BUG IS IN THE PROJECT'S OWN LESSONS FILE -- "re-wrap wraps the SAME
    underlying buffer, and when the module's wrapper is dropped and garbage-collected it closes
    that buffer, so the second wrapper dies at the first print". I wrote the module carrying the
    rule and reproduced the defect inside it, which is the argument for a guard rather than a
    remembered convention.
    """
    if getattr(sys.stdout, "_recovery_wrapped", False):
        return
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    sys.stdout._recovery_wrapped = True


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


def _terms(outcome_name):
    """Search terms for an outcome. The row's own name, plus its first word.

    ⚠️ DELIBERATELY NOT A SYNONYM TABLE. A hand-built list of medical synonyms is the thing that
    has to be rewritten per topic, and it is also the thing that gets tuned against the document
    being searched. The row NAMES the outcome; if a trial calls it something else entirely, that
    is a genuine limit and is reported as one rather than papered over.
    """
    n = re.sub(r"\s*\(.*?\)\s*", " ", (outcome_name or "")).strip().lower()
    out = {n}
    head = n.split(",")[0].split(" and ")[0].strip()
    if head:
        out.add(head)
        first = head.split()[0]
        if len(first) > 5:
            out.add(first)
    return sorted(t for t in out if len(t) > 4)


def trial_sources(canon):
    """The topic's OWN trial primaries, from its sources registry. Never an argument."""
    src = canon.get("sources")
    out = []
    if isinstance(src, dict):
        for key, v in src.items():
            if not isinstance(v, dict):
                continue
            tier = str(v.get("tier") or v.get("layer") or "").lower()
            if "trial" in tier or v.get("layer_rank") == 1:
                out.append((key, v))
    return out


# ⭐ POSTED RESULTS FIRST, AND THIS ORDER IS A FINDING RATHER THAN A PREFERENCE.
#
# The route that recovered a real outcome on this topic was not a full text at all. The Ring
# Study's ClinicalTrials.gov entry posts a PRESPECIFIED SECONDARY outcome measure -- "The
# Incidence of Curable STIs", COUNT_OF_PARTICIPANTS, 24 months -- with its definition verbatim
# and a complete 2x2: 682/1271 against 315/624. That is a poolable result, and it arrived from
# the file this project had already downloaded and was reading only for identifiers and dates.
#
# ⇒ ***CT.GOV POSTED RESULTS ARE A DATA SOURCE, NOT A METADATA SOURCE.*** Treating the registry
# as a place that holds NCTs and enrolment dates left a countable outcome unread on disk.
#
# ⚠️ AND IT IS THE ONLY ROUTE THAT NEEDS NO PUBLISHER AT ALL. No paywall, no bot protection, no
# PMC deposit -- so a reader anywhere can repeat the read, which is the property this project
# claims and the one a full-text route cannot promise. PMC, which I originally treated as
# definitive, was the least useful of the four tried on this topic.
ROUTES = ("registry_results", "pmc", "europepmc_free_pdf", "publisher_doi")


def posted_results(nct, root=None):
    """Every posted outcome measure for this trial, from the registry payload already on disk.

    ⭐ THIS NEEDS NO NETWORK AND NO PUBLISHER. The payload is fetched once for identifiers and
    then read again here for RESULTS -- which is the whole point: the file was already there.

    -> list of {title, description, type, param_type, time_frame, groups, counts, denoms}
    """
    p = os.path.join(root or os.path.join(REPO, "evidence", "acquisition"), nct, "registry.txt")
    if not os.path.exists(p):
        return []
    try:
        d = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return []
    rs = d.get("resultsSection") or {}
    out = []
    for om in ((rs.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []):
        counts, denoms = {}, {}
        for cl in om.get("classes") or []:
            for cat in cl.get("categories") or []:
                for m in cat.get("measurements") or []:
                    counts[m.get("groupId")] = m.get("value")
        for dn in om.get("denoms") or []:
            for cnt in dn.get("counts") or []:
                denoms[cnt.get("groupId")] = cnt.get("value")
        out.append({
            "title": om.get("title"), "description": om.get("description"),
            "type": om.get("type"), "param_type": om.get("paramType"),
            "time_frame": om.get("timeFrame"), "unit": om.get("unitOfMeasure"),
            "groups": {g.get("id"): g.get("title") for g in om.get("groups") or []},
            "counts": counts, "denoms": denoms,
        })
    return out


def match_posted(nct, terms, root=None):
    """The posted outcome measure matching these terms, if exactly one does. -> dict or None.

    ⛔ EXACTLY ONE. Two matching measures is an ambiguity a component may not resolve by
    picking the first -- that is the first-hit selector this project has now been bitten by
    three times. Ambiguity is reported, never silently narrowed.
    """
    hits = []
    for om in posted_results(nct, root):
        blob = ("%s %s" % (om.get("title") or "", om.get("description") or "")).lower()
        if any(t in blob for t in terms):
            hits.append(om)
    return hits[0] if len(hits) == 1 else None


# ⛔⛔⛔ HARD RULE: CT.GOV POSTED RESULTS ARE A MANDATORY ROUTE FOR EVERY OUTCOME.
#
# Not a fallback and not a corroboration -- a REQUIRED attempt, whose result is recorded even
# when it yields nothing. ⚠️ A RULE THAT IS MERELY AVAILABLE GETS SKIPPED; A RULE WHOSE ABSENCE
# IS VISIBLE DOES NOT. So an outcome with no attempt recorded is INCOMPLETE and the object can
# say so, which is the difference between a convention and a gate.
#
# WHY THIS IS THE STRONGEST ROUTE WE HAVE, and it took a lost axis to notice: it needs NO full
# text, no subscription, no publisher and no PMC deposit. It is free-source by construction and
# a reader anywhere can repeat the read. PMC -- which this module originally treated as
# definitive -- was the least useful of four routes tried on the topic that prompted this.
CTGOV_POSTED = "POSTED"                       # counts obtained
CTGOV_NO_RESULTS = "NO_RESULTS_POSTED"        # the registry has no results section
CTGOV_OTHER_OUTCOME = "POSTED_DIFFERENT_OUTCOME"   # results exist, this outcome is not among them
CTGOV_NO_TERM_MATCH = "POSTED_BUT_NO_TERM_MATCHED"  # results exist; OUR terms matched none of them
CTGOV_NOT_ATTEMPTED = "NOT_ATTEMPTED"         # nobody looked

CTGOV_STATE_MEANING = {
    CTGOV_POSTED: "the registry posts this outcome and its counts were read",
    CTGOV_NO_RESULTS: "this trial has posted no results section at all",
    CTGOV_OTHER_OUTCOME: ("the trial HAS posted results, and this outcome is not among the "
                          "measures it posted"),
    CTGOV_NO_TERM_MATCH: (
        "⛔ THE TRIAL HAS POSTED RESULTS AND OUR SEARCH TERMS MATCHED NONE OF THEM. This "
        "is a statement about THIS REVIEW'S MATCHING, not about the registry, and the two were "
        "conflated in the first version of this component: it reported POSTED_DIFFERENT_OUTCOME "
        "for the dapivirine STI outcome, which the registry posts as “The Incidence of "
        "Curable STIs”. The row calls it “sexually transmitted infections” and "
        "the registry calls it “STIs”, so no term matched — and a miss by our "
        "matcher was rendered as an absence in the evidence. ⚠️ EVERY POSTED "
        "TITLE IS LISTED BESIDE THIS STATE so the miss is visible in one glance rather than "
        "believed."),
    CTGOV_NOT_ATTEMPTED: ("⛔ NOBODY LOOKED. This is not an absence of data and must never "
                          "render as one — it is an absence of a check."),
}


def _registry_version(nct, root=None):
    """What VERSION of the registry record a figure came from. Results change over time."""
    p = os.path.join(root or os.path.join(REPO, "evidence", "acquisition"), nct, "registry.txt")
    if not os.path.exists(p):
        return None
    import hashlib
    raw = io.open(p, "rb").read()
    try:
        d = json.loads(raw.decode("utf-8"))
    except Exception:
        return {"sha256": hashlib.sha256(raw).hexdigest(), "unparseable": True}
    st = ((d.get("protocolSection") or {}).get("statusModule") or {})
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "last_update_posted": (st.get("lastUpdatePostDateStruct") or {}).get("date"),
        "results_first_posted": (st.get("resultsFirstPostDateStruct") or {}).get("date"),
        "status_verified": st.get("statusVerifiedDate"),
        "staged_as": "evidence/acquisition/%s/registry.txt" % nct,
    }


def ctgov_attempt(nct, terms, root=None, retrieved_utc=None):
    """THE MANDATORY ATTEMPT. Always returns a record; never returns nothing.

    ⭐ THE REGISTRY'S OWN DEFINITION TRAVELS WITH THE NUMBER, VERBATIM. A composite and its
    components are different quantities, and the definition is the only thing that stops them
    being pooled: "the percentage of participants testing positive for any STI (gonorrhoea,
    chlamydia, trichomonas, syphilis)" is not chlamydia, and a table that shows the number
    without the sentence invites exactly that mistake.
    """
    rec = {"nct": nct, "terms_searched": sorted(terms),
           "retrieved_utc": retrieved_utc or "unrecorded",
           "registry_version": _registry_version(nct, root)}
    oms = posted_results(nct, root)
    if not oms:
        rec["state"] = CTGOV_NO_RESULTS
        rec["meaning"] = CTGOV_STATE_MEANING[CTGOV_NO_RESULTS]
        return rec
    rec["posted_outcome_measures"] = len(oms)
    om = match_posted(nct, terms, root)
    if not om:
        # ⛔ "OUR TERMS FOUND NOTHING" IS NOT "THE TRIAL POSTED SOMETHING ELSE". Only the
        # first is knowable from here, so only the first is claimed.
        rec["state"] = CTGOV_NO_TERM_MATCH
        rec["meaning"] = CTGOV_STATE_MEANING[CTGOV_NO_TERM_MATCH]
        rec["what_was_posted"] = [o.get("title") for o in oms][:20]
        rec["how_to_resolve"] = (
            "Read the titles above. If one of them IS this outcome under another name, the "
            "row's name and the registry's differ and a human should say which measure "
            "applies; the component will not guess, because a wrong match here silently "
            "attributes another outcome's counts to this row.")
        return rec
    rec["state"] = CTGOV_POSTED
    rec["meaning"] = CTGOV_STATE_MEANING[CTGOV_POSTED]
    rec["title"] = om.get("title")
    rec["definition_verbatim"] = om.get("description")
    rec["declared_type"] = om.get("type")
    rec["param_type"] = om.get("param_type")
    rec["time_frame"] = om.get("time_frame")
    rec["unit"] = om.get("unit")
    rec["groups"] = om.get("groups")
    rec["counts"] = om.get("counts")
    rec["denoms"] = om.get("denoms")
    rec["poolable"] = len(om.get("counts") or {}) >= 2 and len(om.get("denoms") or {}) >= 2
    return rec


def outcomes_missing_ctgov_attempt(canon):
    """Every outcome row with NO ct.gov attempt recorded. -> list of (outcome_id, row name).

    ⛔ THIS IS WHAT MAKES THE RULE A RULE. An outcome that was never checked against the
    registry is INCOMPLETE, and a component that cannot name those outcomes leaves the rule
    depending on somebody remembering it.
    """
    missing = []
    for oid, block in (((canon.get("results") or {}).get("by_outcome")) or {}).items():
        if not isinstance(block, dict):
            continue
        for row in ((block.get("other_outcomes") or {}).get("rows")) or []:
            if not isinstance(row, dict):
                continue
            if not row.get("ctgov_results"):
                missing.append((oid, row.get("outcome") or "(unnamed row)"))
    return missing


def read_one(source, terms, fetch, routes=ROUTES):
    """Read ONE primary for these terms, trying EVERY route before declaring it unreadable.

    ⛔ THE FIRST VERSION DECLARED NOT_RETRIEVABLE_OPEN_ACCESS ON A SINGLE FAILED ROUTE, AND IT
    WAS WRONG ABOUT A REAL DOCUMENT. PubMed returns no PMCID for the Ring Study (PMID 27959766),
    so this function returned "no open-access full text exists to read" and the page carried
    that state. Europe PMC records a FREE PDF at the publisher for the same article; it fetched
    on the first attempt, 590,025 bytes, and contained a section devoted to the outcome with
    per-group rates and intervals.

    ⇒ ***A "NOT RETRIEVABLE" VERDICT THAT RESTS ON ONE ROUTE HAVING FAILED IS A STATEMENT ABOUT
    THE ROUTE, NOT ABOUT THE DOCUMENT.*** The state was correct about PMC and wrong about
    reachability, and the difference was a second route nobody tried. It is the same error as
    a scan reporting its own reach as coverage, and here it cost a real primary-source figure.

    ⚠️ SO THE UNREADABLE STATE NOW NAMES EVERY ROUTE THAT WAS TRIED. A state that cannot say
    what was attempted is not falsifiable by the next person, and this one was believed for
    hours precisely because it looked definitive.

    `fetch` is called as fetch(identifier, route) when it accepts two arguments, and
    fetch(identifier) otherwise, so an existing single-route fetch keeps working.
    """
    tried = []

    def _call(ident, route):
        tried.append({"route": route, "identifier": ident})
        try:
            return fetch(ident, route)
        except TypeError:
            return fetch(ident)

    text = None
    for route in routes:
        ident = {"registry_results": source.get("nct"),
                 "pmc": source.get("pmcid"),
                 "europepmc_free_pdf": source.get("pmid"),
                 "publisher_doi": source.get("doi")}.get(route)
        if not ident:
            tried.append({"route": route, "identifier": None,
                          "skipped": "the object records no identifier for this route"})
            continue
        text = _call(ident, route)
        if text:
            break

    if not text:
        return STATE_UNREADABLE, {
            "why": ("every retrieval route recorded for this report was tried and none "
                    "returned a full text. ⚠️ This is a fact about THIS REVIEW'S "
                    "REACH, not about the trial, which may report the outcome perfectly well "
                    "in a document reachable another way."),
            "routes_tried": tried,
            "checked": sorted(terms)}
    low = text.lower()
    hits = [t for t in terms if t in low]
    if not hits:
        return STATE_NO_VALUE, {
            "why": ("the full text was read and none of the terms for this outcome appear in "
                    "it at all."),
            "checked": sorted(terms), "chars_read": len(text)}
    for s in _sentences(text):
        sl = s.lower()
        if any(t in sl for t in hits) and any(c in sl for c in _COMPARATIVE):
            return (STATE_QUALITATIVE if not re.search(r"\d", s) else STATE_NO_VALUE), {
                "why": ("the trial states a direction for this outcome and gives no figure "
                        "in that sentence." if not re.search(r"\d", s) else
                        "the trial mentions this outcome with numbers present; ⛔ NO "
                        "VALUE IS EXTRACTED HERE because reading a figure out of prose is "
                        "extraction and needs its own verification."),
                "verbatim": s, "checked": sorted(terms), "chars_read": len(text)}
    return STATE_NO_VALUE, {
        "why": ("the term appears but no sentence states a comparative reading for it, so the "
                "report carries no usable statement of this outcome."),
        "checked": sorted(terms), "matched_terms": hits, "chars_read": len(text)}


def recover(canon, fetch, only=None):
    """Land a `primary_read` block on every borrowed row. -> (changed, skipped_by_kind)."""
    res = ((canon.get("results") or {}).get("by_outcome") or {})
    sources = trial_sources(canon)
    changed, skipped = [], {"no borrowed tier": 0, "already read": 0, "no trial source": 0}
    for oid, block in res.items():
        if not isinstance(block, dict):
            continue
        rows = ((block.get("other_outcomes") or {}).get("rows")) or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = row.get("outcome") or ""
            if only and name not in only:
                continue
            if str(row.get("tier") or "").strip().lower() not in BORROWED_TIERS:
                skipped["no borrowed tier"] += 1
                continue
            if row.get(MARKER):
                skipped["already read"] += 1
                continue
            if not sources:
                skipped["no trial source"] += 1
                continue
            terms = _terms(name)
            per = {}
            for key, src in sources:
                state, ev = read_one(src, terms, fetch)
                per[key] = dict(ev, state=state, source={
                    k: src.get(k) for k in
                    ("pmid", "pmcid", "doi", "what", "tier", "retrieved_utc") if src.get(k)})
            row[MARKER] = {
                "outcome_terms_searched": terms,
                "by_source": per,
                "states": sorted({v["state"] for v in per.values()}),
                "what_this_establishes": (
                    "The primary trials were READ for this outcome. Where a state reads "
                    "%s the document was read and the value is not in it; where it reads %s "
                    "the document could not be read at all, which is a limit of this review "
                    "rather than of the trial." % (STATE_NO_VALUE, STATE_UNREADABLE)),
                "why_the_borrowed_figure_stands": (
                    "The comparator remains the only source this review holds for a figure on "
                    "this outcome. It is retained, still labelled as the comparator's, and it "
                    "is now KNOWN rather than assumed that no primary-source alternative is "
                    "reachable."),
            }
            changed.append((oid, name, row[MARKER]["states"]))
    return changed, skipped


def coverage(root=None):
    """How many borrowed rows exist across the corpus, and how many this could read.

    ⛔ EVERY SKIP IS A COUNTED KIND. A component that reports what it changed, without what it
    passed over, reports its reach as coverage.
    """
    _utf8_stdout()
    root = root or os.path.join(REPO, "ssot")
    candidates = sorted(os.listdir(root))
    objs = 0
    borrowed = readable = unreadable = 0
    skipped = {"no object file": [], "UNREADABLE OBJECT": [], "no other_outcomes": 0}
    for d in candidates:
        p = os.path.join(root, d, d + ".json")
        if not os.path.exists(p):
            skipped["no object file"].append(d)
            continue
        try:
            c = json.load(io.open(p, encoding="utf-8"))
        except Exception as exc:
            skipped["UNREADABLE OBJECT"].append("%s (%s)" % (d, type(exc).__name__))
            continue
        objs += 1
        srcs = trial_sources(c)
        has = False
        for block in (((c.get("results") or {}).get("by_outcome")) or {}).values():
            if not isinstance(block, dict):
                continue
            for row in ((block.get("other_outcomes") or {}).get("rows")) or []:
                if not isinstance(row, dict):
                    continue
                has = True
                if str(row.get("tier") or "").strip().lower() in BORROWED_TIERS:
                    borrowed += 1
                    if any(s.get("pmcid") for _, s in srcs):
                        readable += 1
                    else:
                        unreadable += 1
        if not has:
            skipped["no other_outcomes"] += 1
    print("")
    print("COVERAGE -- outcome_recovery")
    print("  candidates under ssot/                 %5d" % len(candidates))
    print("  objects read                           %5d" % objs)
    for k in ("no object file", "UNREADABLE OBJECT"):
        if skipped[k]:
            print("  SKIPPED, %-28s %5d   %s"
                  % (k, len(skipped[k]), ", ".join(skipped[k][:3])
                     + (" ..." if len(skipped[k]) > 3 else "")))
    print("  SKIPPED, %-28s %5d" % ("object has no other_outcomes", skipped["no other_outcomes"]))
    print("")
    print("  BORROWED ROWS IN THE CORPUS            %5d   <- the population this addresses"
          % borrowed)
    print("    with a PMCID-bearing primary         %5d   %s"
          % (readable, "readable" if readable else ""))
    print("    with no readable primary at all      %5d   -> %s" % (unreadable, STATE_UNREADABLE))
    print("")
    print("  ⚠️ A borrowed row is not a defect. It is a row whose number came from the")
    print("     comparator, and the axis is lost whether or not that was the right call.")
    return 0


# ---------------------------------------------------------------- plants


def _fake_fetch(table):
    return lambda pmcid: table.get(pmcid)


MODEL = {
    "sources": {
        "TRIAL_A": {"tier": "trial report", "pmcid": "PMC1", "pmid": "1", "what": "Trial A"},
        "TRIAL_B": {"tier": "trial report", "pmid": "2", "what": "Trial B, not in PMC"},
    },
    "results": {"by_outcome": {"primary": {"other_outcomes": {"rows": [
        {"outcome": "Chlamydia", "tier": "prior-meta table (unverified)",
         "effect": "RR 0.97 (0.89 to 1.07)"},
        {"outcome": "Gonorrhoea", "tier": "prior-meta table (unverified)"},
        {"outcome": "Death", "tier": "trial report", "effect": "no material difference"},
    ]}}}},
}


def plant_routes():
    """⛔ THE REGRESSION TEST FOR THE VERDICT I GOT WRONG.

    A source with NO PMCID but a reachable publisher PDF must be READ, not declared unreachable.
    That is exactly the Ring Study: PubMed has no PMCID, Europe PMC has a free PDF, and the
    first version of this function returned NOT_RETRIEVABLE_OPEN_ACCESS without trying it.

    ⚠️ AND THE OPPOSITE CASE MUST STILL REFUSE, with every attempted route NAMED. A state that
    cannot say what it tried is not falsifiable by the next person to look, which is why the
    wrong verdict stood for hours: it read as definitive.
    """
    _utf8_stdout()
    no_pmcid = {"pmid": "27959766", "doi": "10.1056/NEJMoa1602046", "tier": "trial report"}
    body = ("Secondary objectives included sexually transmitted infections. The overall "
            "incidence rates of sexually transmitted infections were similar in the two "
            "trial groups.")

    def fetch_pmc_only(ident, route=None):
        return body if route == "pmc" else None

    def fetch_publisher(ident, route=None):
        return body if route == "europepmc_free_pdf" else None

    def fetch_nothing(ident, route=None):
        return None

    s1, e1 = read_one(no_pmcid, ["sexually transmitted"], fetch_pmc_only)
    s2, e2 = read_one(no_pmcid, ["sexually transmitted"], fetch_publisher)
    s3, e3 = read_one(no_pmcid, ["sexually transmitted"], fetch_nothing)

    ok_1 = s1 == STATE_UNREADABLE            # PMC route unavailable AND nothing else answered
    ok_2 = s2 == STATE_QUALITATIVE           # the second route rescued it
    ok_3 = s3 == STATE_UNREADABLE and len(e3.get("routes_tried") or []) >= 3
    print("")
    print("PLANT -- retrieval routes (regression for a verdict this module got WRONG)")
    print("   no PMCID, only PMC offered      -> %-28s [%s]"
          % (s1, "PASS" if ok_1 else "FAIL"))
    print("   no PMCID, publisher PDF exists  -> %-28s [%s]   <- the one that was wrong"
          % (s2, "PASS" if ok_2 else "FAIL"))
    print("   nothing reachable anywhere      -> %-28s [%s]"
          % (s3, "PASS" if ok_3 else "FAIL"))
    print("   routes named in the refusal: %s"
          % ", ".join(r["route"] for r in (e3.get("routes_tried") or [])))
    print("   ⚠️ a state that cannot say what it TRIED is not falsifiable, which is")
    print("      why the wrong verdict stood: it read as definitive.")
    assert ok_1, "a single available route did not behave"
    assert ok_2, "a document reachable by a second route was declared unreachable -- THE BUG"
    assert ok_3, "an unreachable document did not name the routes tried"
    return 0


def plant():
    """⭐ BOTH WAYS, AND THE THIRD STATE MUST SURVIVE.

    A readable primary that mentions the outcome qualitatively -> RETRIEVED_QUALITATIVE_ONLY.
    A readable primary that does not mention it at all         -> RETRIEVED_NO_VALUE.
    A primary with no PMCID                                    -> NOT_RETRIEVABLE_OPEN_ACCESS.
    ⛔ And a row that is NOT borrowed must be left alone: a component that "improves" a
    trial-report row is rewriting evidence it was not asked about.
    """
    _utf8_stdout()
    canon = json.loads(json.dumps(MODEL))
    fetch = _fake_fetch({"PMC1": (
        "Methods. We enrolled 100 women. Results. Incident chlamydia occurred at a similar "
        "rate in the two groups. No other infections were assessed.")})
    changed, skipped = recover(canon, fetch)
    by = {name: states for _, name, states in changed}
    rows = {r["outcome"]: r for r in
            canon["results"]["by_outcome"]["primary"]["other_outcomes"]["rows"]}

    ok_q = by.get("Chlamydia") and STATE_QUALITATIVE in by["Chlamydia"]
    ok_n = by.get("Gonorrhoea") and STATE_NO_VALUE in by["Gonorrhoea"]
    ok_u = all(STATE_UNREADABLE in v for v in by.values())
    ok_left = MARKER not in rows["Death"]
    quote = (rows["Chlamydia"][MARKER]["by_source"]["TRIAL_A"].get("verbatim") or "")
    ok_quote = "similar rate" in quote

    print("")
    print("PLANT -- outcome_recovery, three states and one refusal")
    print("   readable primary, qualitative mention   %-34s [%s]"
          % (by.get("Chlamydia"), "PASS" if ok_q else "FAIL"))
    print("   readable primary, outcome absent        %-34s [%s]"
          % (by.get("Gonorrhoea"), "PASS" if ok_n else "FAIL"))
    print("   primary with no PMCID                   %-34s [%s]"
          % (STATE_UNREADABLE, "PASS" if ok_u else "FAIL"))
    print("   verbatim carried, not paraphrased       %-34s [%s]"
          % (quote[:34], "PASS" if ok_quote else "FAIL"))
    print("   REFUSAL: a trial-report row is untouched %-33s [%s]"
          % ("Death has no primary_read", "PASS" if ok_left else "FAIL"))
    print("   skipped, by kind: %s" % json.dumps(skipped))
    print("   ⚠️ no NUMBER is ever written into a row. Extraction needs its own")
    print("      verification; a component that could invent a value is worse than the")
    print("      borrowed row it replaces.")
    for cond, msg in ((ok_q, "qualitative state not detected"),
                      (ok_n, "absent outcome not typed RETRIEVED_NO_VALUE"),
                      (ok_u, "unreadable primary not typed NOT_RETRIEVABLE_OPEN_ACCESS"),
                      (ok_quote, "verbatim not carried"),
                      (ok_left, "a non-borrowed row was modified")):
        assert cond, msg
    return 0


if __name__ == "__main__":
    raise SystemExit(plant() or plant_routes() or coverage())
