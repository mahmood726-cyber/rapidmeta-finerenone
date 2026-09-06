# -*- coding: utf-8 -*-
"""Recall of Galli 2025's 21 GLP-1 CV trials against our Europe PMC search -- a real recall
number on a fixed target, re-runnable.

The question is NOT precision (we deliberately admit eligible-unreported trials the outcome
screen would drop). It is recall: does the Europe PMC search's result set CONTAIN each of the
21 trials Galli included? Tested the same way the control was -- a per-trial membership
sub-query `(OUR_QUERY) AND (identifying terms)` -- so each trial's verdict carries the exact
query that decided it and re-runs.

HONESTY: three of the 21 are author-name trials with no acronym (Kyhl, Chen, Zhang) and two
carry acronyms that are ordinary words (GRADE -- also the certainty tool; SOUL). For those the
identifying terms are author + agent, and a miss is reported as IDENTIFIER_AMBIGUOUS, not as
"not in the corpus" -- a count that quietly folded those into either bucket would be the
throttle-vs-zero error again.
"""
from __future__ import annotations
import io, sys, json
sys.path.insert(0, "scripts")
import europepmc_adapter as ep

# our base search (same as the recorded adapter run)
BASE = ('(semaglutide OR liraglutide OR dulaglutide OR exenatide OR albiglutide OR efpeglenatide '
        'OR lixisenatide OR "glucagon-like peptide") AND (cardiovascular OR MACE OR "cardiovascular '
        'outcomes") AND PUB_TYPE:"Randomized Controlled Trial"')

# identifying terms per trial. acronym trials -> quoted acronym + agent; author trials -> AUTH + agent.
# `ambiguous` marks a name that is an ordinary word, so a bare-acronym match cannot be trusted.
TRIALS = [
    ("ELIXA", '"ELIXA" AND lixisenatide', False),
    ("Kyhl et al.", 'AUTH:"Kyhl" AND exenatide AND myocardial', True),
    ("LEADER", '"LEADER" AND liraglutide', False),
    ("FIGHT", '"FIGHT" AND liraglutide AND "heart failure"', True),
    ("Chen et al.", 'AUTH:"Chen" AND liraglutide AND (NSTEMI OR "non-ST")', True),
    ("SUSTAIN-6", '("SUSTAIN-6" OR "SUSTAIN 6") AND semaglutide', False),
    ("LIVE-Jorsal", '(AUTH:"Jorsal" OR "LIVE") AND liraglutide AND "heart failure"', True),
    ("Zhang et al.", 'AUTH:"Zhang" AND liraglutide AND "heart failure" AND (2017 OR 2016)', True),
    ("EXSCEL", '"EXSCEL" AND exenatide', False),
    ("HARMONY OUTCOMES", '"HARMONY" AND albiglutide', False),
    ("PIONEER-6", '("PIONEER-6" OR "PIONEER 6") AND semaglutide', False),
    ("REWIND", '"REWIND" AND dulaglutide', False),
    ("AMPLITUDE-O", '"AMPLITUDE" AND efpeglenatide', False),
    ("STEP-HFpEF", '"STEP-HFpEF" AND semaglutide', False),
    ("SELECT", '"SELECT" AND semaglutide AND cardiovascular', False),
    ("STEP-HFpEF DM", '("STEP-HFpEF DM" OR "STEP HFpEF DM") AND semaglutide', False),
    ("FLOW", '"FLOW" AND semaglutide AND (kidney OR renal)', True),
    ("GRADE", '"GRADE" AND liraglutide AND (glycemia OR diabetes)', True),
    ("SUMMIT", '"SUMMIT" AND tirzepatide', False),
    ("SOUL", '"SOUL" AND semaglutide AND oral', True),
    ("STRIDE", '"STRIDE" AND semaglutide AND (peripheral OR PAD OR claudication)', True),
]


def measure(out_dir=None):
    results = []
    for name, terms, ambiguous in TRIALS:
        subq = "(%s) AND (%s)" % (BASE, terms)
        state, http, hit, recs, detail = ep.fetch(subq, page_size=5, max_pages=1)
        if state in (ep.RAN_ZERO, ep.RAN_RESULTS):
            if hit and hit >= 1:
                verdict = "FOUND"
            else:
                verdict = "MISS_IDENTIFIER_AMBIGUOUS" if ambiguous else "MISS_NOT_IN_SET"
        else:
            verdict = "NO_ANSWER_%s" % state  # RAN_ERROR/NOT_RUN -- not a miss
        results.append({"trial": name, "membership_query": subq, "state": state,
                        "hit_count": hit, "verdict": verdict,
                        "top_title": (recs[0]["title"][:90] if recs else None)})
    found = sum(1 for r in results if r["verdict"] == "FOUND")
    amb = sum(1 for r in results if r["verdict"] == "MISS_IDENTIFIER_AMBIGUOUS")
    miss = sum(1 for r in results if r["verdict"] == "MISS_NOT_IN_SET")
    noans = sum(1 for r in results if r["verdict"].startswith("NO_ANSWER"))
    rec = {"target": "Galli 2025, 21 GLP-1 CV trials", "base_query": BASE,
           "executed_utc": ep._utc(), "n_target": len(TRIALS),
           "found": found, "miss_not_in_set": miss,
           "miss_identifier_ambiguous": amb, "no_answer": noans, "per_trial": results}
    if out_dir:
        from pathlib import Path
        from datetime import datetime, timezone
        p = Path(out_dir); p.mkdir(parents=True, exist_ok=True)
        f = p / ("galli_recall_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        io.open(f, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, indent=1, ensure_ascii=False))
        rec["_written_to"] = str(f)
    return rec


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    r = measure(out_dir=("evidence/acquisition" if "--write" in sys.argv else None))
    print("Galli 21 recall against the Europe PMC GLP-1 CV RCT search")
    for t in r["per_trial"]:
        print("  %-16s %-26s hit=%s" % (t["trial"], t["verdict"], t["hit_count"]))
    print("\nFOUND %d/21 | not-in-set %d | identifier-ambiguous %d | no-answer %d"
          % (r["found"], r["miss_not_in_set"], r["miss_identifier_ambiguous"], r["no_answer"]))
    if r.get("_written_to"):
        print("written:", r["_written_to"])
