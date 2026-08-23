"""Do the 17 pages in the `no_review_done` bucket actually hold nothing?

THE ANSWER IS NO. ZERO OF THE 17 HOLD NOTHING. The bucket is an artefact of a probe that
read ONE payload shape, and the instruction to retire these 17 as objects that "hold
nothing -- no title, no results, nothing to project" rests on a premise this instrument
disproves for all seventeen.

WHAT THE ORIGINAL PROBE ASKED. `audit_no_identifier_pages_hold_data_2026_08_23.py` reads
the brace-matched body of `realData:{...}` and looks for two things inside it: an `NCT`
identifier, and an arm block matching `tE:<digits> ... tN:<digits> ... cE:<digits>`. A page
with neither was placed in `no_review_done`, glossed "neither -- no trial-level data at
all". That gloss is what "hold nothing" is quoting.

THE THREE WAYS THAT PROBE MISSES DATA THAT IS PRESENT, each observed on a real page here:

  1. THE LEDGER SHAPE.        `HFREF_NMA_AUTO_FULL_REVIEW.html` carries a network ledger --
                              `{"id":"HF-023","name":"EMPHASIS-HF","pmid":"21073363",
                              "doi":"10.1056/NEJMoa1009492","nct":"NCT00232180",
                              "arms":[{"treat":"ACEI+BB","events":213,"n":1373},
                              {"treat":"ACEI+BB+MRA","events":171,"n":1364}]}` and eight
                              more like it, with verification notes and one recorded PMID
                              correction. None of it is inside `realData`, so the probe
                              reported it as holding no trial-level data at all. Retiring
                              this page would delete the best-evidenced network in the
                              legacy corpus.

  2. THE PMID KEY.            `METFORMIN_T2D_AUTO_FULL_REVIEW.html` has a populated
                              `realData` keyed by `"PMID:7623902"` -- the Multicenter
                              Metformin Study Group (DeFronzo & Goodman 1995), Protocol 1,
                              metformin monotherapy vs placebo, phase III, tN 143, cN 146.
                              The probe searched that body for `NCT\\d{8}` and found none,
                              because the record is keyed by PMID.

  3. `tE` IS NULL, NOT ABSENT. The same record carries `tE:null,cE:null` because the
                              outcome is continuous. The arm regex requires `tE:<digits>`,
                              so a continuous-outcome trial with real arm sizes reads as no
                              arm block.

AND THE REMAINING FIFTEEN HOLD IDENTIFIERS. Each carries an `nctAcronyms` map naming 2-6
specific trials, several with acronyms the review recorded by hand (`NCT00500656:"FAST2"`,
`NCT00997204:"EASSI"`). Their `realData` is genuinely `{}` -- no results were extracted --
but a page that names six trials it identified is not a page where no review was done. The
honest statement about those fifteen is "trials identified, no results extracted", which is
a different retirement from the one instructed, and a different one from the merge-and-
absorb tombstones the PCSK9 style was written for.

WHY THIS IS REPORTED RATHER THAN ACTED ON. Retiring a page is outward-facing and not
cheaply reversible: it replaces served bytes a reader can reach. The instruction's premise
is false for 17 of 17, and choosing what to do with a page that identified trials but
extracted no results is a judgement about the evidence, not a projection or a lookup.

THE TEMPLATE `tE:` COUNT IS NOISE AND IS REPORTED SO. Every one of the seventeen shows
exactly three `tE:<digits>` occurrences, including the pages that hold nothing else. Those
are the engine's hardcoded default trial array -- the same four ids the original probe
already excludes by name -- and counting them as page data would report every legacy page
as data-bearing. Reported as a separate column so a later reader does not rediscover it.

CONTROLS. The positive is ABALOPARATIDE_OSTEO, hand-read in the original probe's own
docstring (NCT01343004, tE:4 tN:690 cE:30 cN:711) and NOT a member of the seventeen, so it
does not die when the seventeen change. The negative is a SYNTHETIC FIXTURE built in this
file -- a page body holding only the four template identifiers and an empty `realData` --
because a negative keyed to a corpus page would expire the moment that page is repaired.
That is the control-with-an-expiry-date lesson, and it has cost six instances.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUCKETS = os.path.join(REPO, "outputs", "no_identifier_data_state_2026_08_23.json")
OUT = os.path.join(REPO, "outputs", "no_review_done_is_shape_bound_2026_08_23.json")

TEMPLATE_IDS = {"NCT01035255", "NCT01920711", "NCT02924727", "NCT05901831"}

NCT = re.compile(r"NCT\d{8}")
ACRO_MAP = re.compile(r"nctAcronyms\s*:\s*\{([^}]*)\}")
LEDGER_NCT = re.compile(r'"nct"\s*:\s*"NCT\d{8}"')
ARMS_ARRAY = re.compile(r'"arms"\s*:\s*\[\s*\{')
EVENTS_N = re.compile(r'"events"\s*:\s*\d+\s*,\s*"n"\s*:\s*\d+')
TE_TEMPLATE = re.compile(r"\btE\s*:\s*\d+")
PMID_ANY = re.compile(r'"?pmid"?\s*[:=]\s*"?\d{6,9}')
DOI_ANY = re.compile(r'"doi"\s*:\s*"10\.')
REALDATA = re.compile(r"realData\s*[:=]\s*\{")
# a realData record keyed by PMID rather than NCT -- miss #2
PMID_KEYED = re.compile(r'"PMID:\d{6,9}"\s*:\s*\{')
# arm sizes present with a null event count -- miss #3
TN_WITH_NULL_TE = re.compile(r"tE\s*:\s*null[^}]{0,120}?\btN\s*:\s*\d+")


def realdata_body(text):
    """The brace-matched body of realData, exactly as the original probe reads it."""
    m = REALDATA.search(text)
    if not m:
        return ""
    i, depth = m.end(), 1
    while i < len(text) and depth:
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    return text[m.end():i]


def original_probe(text):
    """What `audit_no_identifier_pages_hold_data` concluded, reproduced here so the two
    readings sit side by side rather than being argued about."""
    body = realdata_body(text)
    ids = sorted(set(NCT.findall(body)) - TEMPLATE_IDS)
    arms = re.findall(r"\btE\s*:\s*\d+.{0,80}?\btN\s*:\s*\d+.{0,120}?\bcE\s*:\s*\d+",
                      body, re.S)
    return {"realdata_nct": len(ids), "realdata_tE_arms": len(arms),
            "realdata_bytes": len(body)}


def shape_agnostic(text):
    """Every shape trial-level data has been observed to take on a legacy page."""
    m = ACRO_MAP.search(text)
    acro = sorted(set(NCT.findall(m.group(1))) - TEMPLATE_IDS) if m else []
    return {
        "nct_anywhere": len(sorted(set(NCT.findall(text)) - TEMPLATE_IDS)),
        "nct_acronym_map": len(acro),
        "acronyms_named": sorted(
            set(re.findall(r'NCT\d{8}\s*:\s*"([A-Za-z][\w\-]{1,20})"', text))) if m else [],
        "ledger_trials": len(LEDGER_NCT.findall(text)),
        "ledger_arm_arrays": len(ARMS_ARRAY.findall(text)),
        "ledger_events_n_pairs": len(EVENTS_N.findall(text)),
        "pmid_keyed_records": len(PMID_KEYED.findall(text)),
        "arm_sizes_with_null_events": len(TN_WITH_NULL_TE.findall(text)),
        "pmid_occurrences": len(PMID_ANY.findall(text)),
        "doi_occurrences": len(DOI_ANY.findall(text)),
        "template_tE_noise": len(TE_TEMPLATE.findall(text)),
    }


def verdict(s):
    """Three states, named. Never a fourth called 'probably'."""
    if s["ledger_trials"] and s["ledger_arm_arrays"]:
        return "HOLDS_A_TRIAL_LEDGER"
    if s["pmid_keyed_records"]:
        return "HOLDS_A_RESULTS_RECORD_KEYED_BY_PMID"
    if s["nct_acronym_map"]:
        return "HOLDS_IDENTIFIERS_ONLY"
    return "HOLDS_NOTHING"


# The synthetic negative. Built here so it cannot expire when the corpus is repaired.
FIXTURE_EMPTY = (
    'var trialData=["NCT01035255","NCT01920711","NCT02924727","NCT05901831"];'
    "RapidMeta={realData:{},nctAcronyms:{},init(){}};"
)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if not os.path.isfile(BUCKETS):
        sys.exit("REFUSED: %s missing." % os.path.relpath(BUCKETS, REPO))
    names = json.load(io.open(BUCKETS, encoding="utf-8"))["by_bucket"]["no_review_done"]

    pos = os.path.join(REPO, "ABALOPARATIDE_OSTEO_AUTO_FULL_REVIEW.html")
    ptext = io.open(pos, encoding="utf-8", errors="replace").read() if os.path.isfile(pos) else ""
    ps = shape_agnostic(ptext)
    require_controls(
        "no_review_done_is_shape_bound",
        ("ABALOPARATIDE_OSTEO holds NCT01343004 with per-arm counts (hand-read in the "
         "original probe's docstring) -- shape-agnostic read gives nct_anywhere=%d"
         % ps["nct_anywhere"], ps["nct_anywhere"] >= 1, True),
        ("the synthetic empty fixture -- four template ids and realData:{} -- must not be "
         "read as holding anything; verdict came back %r"
         % verdict(shape_agnostic(FIXTURE_EMPTY)),
         verdict(shape_agnostic(FIXTURE_EMPTY)) != "HOLDS_NOTHING", True))

    rows, tally = {}, {}
    for n in names:
        p = os.path.join(REPO, n)
        if not os.path.isfile(p):
            rows[n] = {"verdict": "NOT_ON_DISK"}
            tally["NOT_ON_DISK"] = tally.get("NOT_ON_DISK", 0) + 1
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        s = shape_agnostic(t)
        v = verdict(s)
        rows[n] = {"verdict": v, "shape_agnostic": s, "original_probe": original_probe(t)}
        tally[v] = tally.get(v, 0) + 1

    print("")
    print("THE %d PAGES THE BUCKET CALLS `no_review_done` -- what do they hold, read by"
          % len(names))
    print("EVERY SHAPE trial-level data takes on a legacy page rather than by one?")
    print("")
    for v in ("HOLDS_A_TRIAL_LEDGER", "HOLDS_A_RESULTS_RECORD_KEYED_BY_PMID",
              "HOLDS_IDENTIFIERS_ONLY", "HOLDS_NOTHING", "NOT_ON_DISK"):
        print("   %-40s %5d" % (v, tally.get(v, 0)))
    print("   %-40s %5d   == the bucket" % ("sum", sum(tally.values())))
    if sum(tally.values()) != len(names):
        sys.exit("REFUSED: does not close.")
    print("")
    for n in names:
        r = rows[n]
        if r["verdict"] == "NOT_ON_DISK":
            print("   %-52s NOT_ON_DISK" % n)
            continue
        s = r["shape_agnostic"]
        print("   %-52s %s" % (n, r["verdict"]))
        print("        ledger %d trials / %d arm arrays / %d events-n pairs; "
              "acronym map %d; pmid-keyed %d; pmid %d; doi %d; template tE noise %d"
              % (s["ledger_trials"], s["ledger_arm_arrays"], s["ledger_events_n_pairs"],
                 s["nct_acronym_map"], s["pmid_keyed_records"], s["pmid_occurrences"],
                 s["doi_occurrences"], s["template_tE_noise"]))
        if s["acronyms_named"]:
            print("        acronyms the review recorded: %s"
                  % ", ".join(s["acronyms_named"]))
    print("")
    print("THE BUCKET'S OWN GLOSS -- \"neither identifiers nor arm-level data\" -- IS TRUE")
    print("OF THE `realData` KEY AND OF NOTHING ELSE. Both probes are honest; they ask")
    print("different questions. What is not honest is retiring a page on the strength of")
    print("the narrower one while telling a reader it held nothing.")
    print("")
    print("NOTHING HAS BEEN RETIRED. This instrument writes a file and changes no page.")

    json.dump({"asked": "does the no_review_done bucket mean the page holds nothing",
               "answer": "no -- 0 of %d hold nothing" % len(names),
               "tally": tally, "rows": rows,
               "the_three_misses": {
                   "ledger_shape": "trial ledger outside realData (HFREF_NMA)",
                   "pmid_keyed": "realData keyed by PMID not NCT (METFORMIN_T2D)",
                   "te_is_null": "continuous outcome, tE:null, arm sizes present"},
               "nothing_was_retired": True},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
