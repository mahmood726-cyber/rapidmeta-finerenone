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


ROUTES = ("pmc", "europepmc_free_pdf", "publisher_doi")


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
        ident = {"pmc": source.get("pmcid"),
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
