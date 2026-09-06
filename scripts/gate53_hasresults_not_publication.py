# -*- coding: utf-8 -*-
"""Gate 53 -- `hasResults=false` is a fact about ClinicalTrials.gov, not about the trial.

A trial held as ELIGIBLE_NO_RESULTS_YET because the registry posted no structured results has NOT
been shown to lack evidence: a journal publication, regulatory report or conference paper may
report it in full. Such a holding must become PUBLICATION_SEARCH_REQUIRED, never a terminal
"eligible, no results yet". This is the reviewers' highest-value single fix -- five named instances
(ANSWER-HF, Mokadem, APROPOS, AVERT, and the class "fixed" once weeks ago on the instance not the
class), and it lost real pivotal trials (AVERT: NEJM, VTE 12/288 vs 28/275).

DETECTOR, per TRIAL RECORD (not per nested blob -- the naive walk flagged 1356 NCTs by matching
every trial nested under any 'no results' text). A record is a dict carrying its own nct/study_id;
it fires if ITS OWN scalar fields say the holding rests on registry-results-absence.

CONTROLS (must fire): AVERT NCT02048865, APROPOS NCT00097357, Mokadem NCT04462003.

CAVEAT stated, not hidden: 91 records carry this holding; the ACTIONABLE subset is those whose
trial is COMPLETED (a completed trial has a publication to find; an ongoing one legitimately has
none yet). Completion status is not uniformly recorded, so this reports the holding population and
names the fixtures as the proven-completed core. Reach is not coverage.
"""
from __future__ import annotations
import io, re, json, os, glob, sys

ABSENT = re.compile(r"no results yet|hasResults[=:\s]+[Ff]alse|results (?:not|never|are not) "
                    r"(?:yet )?posted|eligible[^.]{0,40}no results|no (?:posted )?results "
                    r"(?:section|posted|available)", re.I)


def _trial_records(o):
    out = []
    def w(x):
        if isinstance(x, dict):
            if any(k in x for k in ("nct", "nct_id", "study_id", "registration")):
                out.append(x)
            for v in x.values():
                w(v)
        elif isinstance(x, list):
            for v in x:
                w(v)
    w(o)
    return out


def scan(objs_dir="ssot"):
    objs = [p for p in glob.glob(os.path.join(objs_dir, "*", "*.json"))
            if "sources" not in p and os.path.basename(p)[:-5] == os.path.basename(os.path.dirname(p))]
    hits = []
    for p in objs:
        aid = os.path.basename(p)[:-5]
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for tr in _trial_records(d):
            own = " ".join(str(v) for v in tr.values() if isinstance(v, str))
            if ABSENT.search(own):
                nct = tr.get("nct") or tr.get("nct_id") or tr.get("study_id") or "?"
                hits.append((aid, str(nct)))
    return hits


FIXTURES = {"NCT02048865": "AVERT", "NCT00097357": "APROPOS", "NCT04462003": "Mokadem"}


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    hits = scan()
    ncts = {n for _, n in hits}

    def _member(key, coll):  # explicit membership so an id-named key is not read as a substring test
        return key in coll
    fired = {nct: _member(nct, ncts) for nct in FIXTURES}
    print("GATE 53 -- ELIGIBLE_NO_RESULTS_YET held on registry-results-absence")
    for nct, name in FIXTURES.items():
        print("  CONTROL %-9s (%s) fires: %s (must be True)" % (name, nct, fired[nct]))
    if not all(fired.values()):
        print("  *** a fixture did not fire -- detector not trustworthy ***")
        raise SystemExit(1)
    print("  holdings: %d trial records, %d distinct NCTs" % (len(hits), len(ncts)))
    print("  -> DO NOT bulk-relabel. PUBLICATION_SEARCH_REQUIRED is a TASK, not a verdict. Each")
    print("     trial resolves to one of THREE states, and NOT_YET_SEARCHED must render as an")
    print("     OPEN TASK on its review (else a silent exclusion becomes a silent to-do):")
    print("       PUBLISHED_RESULTS_FOUND | SEARCHED_NONE_FOUND | NOT_YET_SEARCHED")
    raise SystemExit(0)
