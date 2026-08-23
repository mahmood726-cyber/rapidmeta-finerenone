"""Answer the withholding question at every registered rank for attr-pn-review.

# no-control: an edit, not a detector. Its control is that every rank recorded here comes
# from a live registry read whose outcome titles are stored verbatim; the run refuses if a
# registration returns no outcome module at all, rather than recording an empty read as a
# read.

WHY THIS EXISTS AND WHAT IT DOES NOT DO. `scripts/lint_withholding_asked.py` refused the
attr-pn withdrawal because the topic declines to pool with no evidence that any rank below
the primary was ever read. It is right to refuse: twice in this project a topic that
"did not pool" had a harmonisable SECONDARY, and on `sglt2-hf` and
`apixaban-vte-prophylaxis` that secondary became a real pooled estimate.

So the question is asked here properly, by reading each registration's PRIMARY, SECONDARY
and OTHER outcome titles from ClinicalTrials.gov and storing them verbatim on the trial.
Nothing is supplied to satisfy a gate: `all_ranks_read_utc` is written only for a trial
whose ranks were actually fetched in this run.

AND THE ANSWER DOES NOT DISSOLVE THIS WITHDRAWAL, WHICH IS THE POINT WORTH RECORDING. The
obstacle on this topic is not that the trials measure different things -- they measure the
same thing, and `estimand_established` is TRUE and stays true. The obstacle is that two of
three contrasts are against a BORROWED historical control. A comparator is a property of
the DESIGN, not of the outcome rank: reading NEURO-TTRansform's secondaries cannot make
its comparator randomised or concurrent, and reading HELIOS-A's cannot give it a placebo
arm it does not have. Whatever ranks these registrations declare, every one of them is
measured against the same borrowed groups.

That is the difference between this refusal and the two the gate was built from. There,
the obstacle lived in WHICH outcome was being compared, so a different outcome could
dissolve it. Here it lives in WHAT the outcome is compared against, and no outcome can.
The distinction is recorded on the object so the gate's question is answered rather than
routed around.
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(REPO, "ssot", "attr-pn-review", "attr-pn-review.json")
API = ("https://clinicaltrials.gov/api/v2/studies/%s"
       "?fields=protocolSection.outcomesModule")
TODAY = "2026-08-23"

WHY_RANK_CANNOT_HELP = (
    "READING EVERY RANK DOES NOT DISSOLVE THIS REFUSAL, AND THAT IS WHY THE RANKS ARE "
    "RECORDED RATHER THAN TREATED AS AN ANSWER. The obstacle on this topic is the "
    "COMPARATOR, not the outcome: two of the three contributing contrasts are measured "
    "against a BORROWED historical control rather than a randomised concurrent one. A "
    "comparator is a property of the trial's DESIGN, so it is the same at every rank -- "
    "reading NEURO-TTRansform's secondaries cannot make its comparator randomised, and "
    "reading HELIOS-A's cannot give it the placebo arm it does not have. This is the "
    "opposite shape from the two refusals that turned into pools when the question was "
    "asked properly (sglt2-hf, apixaban-vte-prophylaxis): there the obstacle lived in "
    "WHICH outcome was compared, and a different outcome dissolved it. Here it lives in "
    "WHAT the outcome is compared against, and no outcome can.")


def fetch_ranks(nct):
    with urllib.request.urlopen(API % nct, timeout=90) as r:
        d = json.load(r)
    om = (d.get("protocolSection") or {}).get("outcomesModule") or {}
    out = {}
    for key, rank in (("primaryOutcomes", "PRIMARY"),
                      ("secondaryOutcomes", "SECONDARY"),
                      ("otherOutcomes", "OTHER")):
        out[rank] = [str((o or {}).get("measure", "")).strip()
                     for o in (om.get(key) or [])]
    if not any(out.values()):
        return None
    return out


def count_keys(x):
    if isinstance(x, dict):
        return len(x) + sum(count_keys(v) for v in x.values())
    if isinstance(x, list):
        return sum(count_keys(v) for v in x)
    return 0


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    apply = "--apply" in sys.argv
    raw = io.open(OBJ, encoding="utf-8", newline="").read()
    obj = json.loads(raw)
    before = count_keys(obj)

    print("")
    print("attr-pn-review -- every registered rank, read from the registry")
    print("")
    touched = 0
    for tr in (obj.get("inputs") or {}).get("trials") or []:
        nct = tr.get("nct") or tr.get("id")
        if not nct:
            continue
        ranks = fetch_ranks(nct)
        if ranks is None:
            sys.exit("REFUSED: %s returned no outcomes module. An empty read is not a read, "
                     "and recording it as one is how a gate gets satisfied by a string."
                     % nct)
        print("   %-14s %-18s PRIMARY %d   SECONDARY %d   OTHER %d"
              % (nct, tr.get("name", "")[:18], len(ranks["PRIMARY"]),
                 len(ranks["SECONDARY"]), len(ranks["OTHER"])))
        for r in ("SECONDARY", "OTHER"):
            for m in ranks[r][:3]:
                print("        %-9s %s" % (r, m[:96]))
        if apply:
            tr["registered_secondaries"] = ranks["SECONDARY"]
            tr["registered_other_outcomes"] = ranks["OTHER"]
            tr["all_ranks_read_utc"] = TODAY
            tr["all_ranks_read_source"] = API % nct
            touched += 1

    print("")
    print("   %s" % WHY_RANK_CANNOT_HELP[:110])
    print("")
    if not apply:
        print("   dry run -- pass --apply to write")
        return
    blk = ((obj.get("results") or {}).get("by_outcome") or {}).get("primary") or {}
    pooled = blk.get("pooled") or {}
    if not pooled.get("withdrawn"):
        sys.exit("REFUSED: this topic is not withdrawn, so the note below would describe "
                 "a state it is not in.")
    pooled["why_reading_every_rank_does_not_change_this"] = WHY_RANK_CANNOT_HELP
    after = count_keys(obj)
    if after < before:
        sys.exit("REFUSED: the object lost keys (%d -> %d)." % (before, after))
    nl = "\r\n" if "\r\n" in raw else "\n"
    body = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
    io.open(OBJ, "w", encoding="utf-8", newline="").write(
        body.replace("\n", nl) if nl != "\n" else body)
    print("   %d trial(s) now carry all_ranks_read_utc; keys %d -> %d (net-additive)"
          % (touched, before, after))


if __name__ == "__main__":
    main()
