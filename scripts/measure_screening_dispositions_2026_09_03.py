# -*- coding: utf-8 -*-
"""How many screening exclusions are exclusions, and how many are nobody having looked.

WHAT THIS COUNTS. For a NAMED sample of topics it screens EVERY candidate in the eligible
pool -- not the head the ingestion bound keeps -- and classifies each one INCLUDED,
EXCLUDED or UNDECIDABLE using scripts/screening_states.py, the same module `audit_nct`
calls. The denominator is the pool, and it is printed beside every count.

WHY THE THIRD STATE IS THE POINT. `audit_nct` records six gates as booleans, so a gate
returns False both when the evidence disagrees and when the evidence was never there. Gate D
reads a PMID from AACT and an abstract from PubMed: it is False when the abstract disagrees,
False when no PMID was ever linked, and False when PubMed was unreachable. All three are
written out the same way and the topic becomes NOT_VIABLE.

    AN UNREACHABLE NETWORK IS NOT EVIDENCE ABOUT A TRIAL. Recorded as a gate failure it
    becomes exactly that, and the output looks identical to a screen that ran.

Gates E and F have the same shape: a trial with no posted baseline rows is recorded as not
having two arms, and a trial with no design_outcomes rows as having no known primary
outcome. Not posted, read as not so.

THE CONTROLS ARE SYNTHETIC AND THEY TEST BOTH DIRECTIONS, because the failure mode here is
symmetric and a one-sided control would miss half of it:

    POSITIVE  a fabricated candidate whose PubMed abstract IS present and DISAGREES must
              come back EXCLUDED. Without it, a classifier that answered UNDECIDABLE to
              everything would look like a triumphant discovery.
    NEGATIVE  a fabricated candidate identical except that the abstract is MISSING must NOT
              come back EXCLUDED. That is the direction in which the old code was wrong, so
              it is the direction this instrument must be shown not to repeat.

WHAT THIS DOES NOT CLAIM. Not that the undecidable candidates are good trials, and not that
they would pass if the data arrived. Only that they were never assessed, that the number of
them was never written down, and that they are currently counted as failures.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screening_states as S  # noqa: E402
from instrument_controls import require_controls  # noqa: E402

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "scripts" / "add_topic_autodiscover.py"
RECORDS = ROOT / "evidence" / "enumeration"
SLICE_START = "DRUG_SYNS = {"
SLICE_END = "    return kept"


def load_matcher():
    src = SOURCE.read_text(encoding="utf-8")
    i = src.index(SLICE_START)
    j = src.index(SLICE_END) + len(SLICE_END)
    ns = {"re": re, "os": os}
    exec(compile(src[i:j], str(SOURCE), "exec"), ns)
    return ns


def _fake(topic_drug="dapagliflozin", abstract=None, pmid="111"):
    return dict(nct="NCT00000001",
                topic={"drug_patterns": [topic_drug], "condition_patterns": ["heart failure"]},
                aact_rows=[{"brief_title": "t"}],
                intvs=["dapagliflozin 10 mg"], conds=["heart failure"],
                pmids=[pmid] if pmid else [],
                pubmed_meta=({pmid: {"title": abstract, "abstract": ""}}
                             if abstract is not None else {}),
                baseline_rows=[{"ctgov_group_code": "BG0", "count": "10", "scope": "overall",
                                "units": "Participants"},
                               {"ctgov_group_code": "BG1", "count": "20", "scope": "overall",
                                "units": "Participants"}],
                design_outcome_rows=[{"outcome_type": "Primary", "measure": "m"}])


def controls(match_blob, drug_syns, cond_syns):
    """(positive_disposition, negative_disposition) from fabricated candidates."""
    pos = S.classify(match_blob=match_blob, drug_syns=drug_syns, cond_syns=cond_syns,
                     **_fake(abstract="a study of something entirely unrelated"))
    neg = S.classify(match_blob=match_blob, drug_syns=drug_syns, cond_syns=cond_syns,
                     **_fake(abstract=None))
    return pos["disposition"], neg["disposition"]


def load_for(aact, ncts, say):
    """Only the rows belonging to the pool, so the read stays inside memory."""
    csv.field_size_limit(10 ** 9)
    want = {n: True for n in ncts}
    out = {"studies": defaultdict(list), "baseline": defaultdict(list),
           "design_outs": defaultdict(list), "refs": defaultdict(list),
           "intv": defaultdict(list), "cond": defaultdict(list)}
    spec = [("studies.txt", "studies", ("brief_title", "acronym", "start_date")),
            ("baseline_counts.txt", "baseline",
             ("ctgov_group_code", "count", "scope", "units")),
            ("design_outcomes.txt", "design_outs", ("outcome_type", "measure")),
            ("interventions.txt", "intv", ("name",)),
            ("conditions.txt", "cond", ("downcase_name",))]
    for fname, key, cols in spec:
        path = aact / fname
        if not path.exists():
            say("    %-26s MISSING -- every gate reading it becomes UNDECIDABLE" % fname)
            continue
        n = 0
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f, delimiter="|"):
                nct = (row.get("nct_id") or "").strip().upper()
                if want.get(nct):
                    n += 1
                    out[key][nct].append({c: (row.get(c) or "").strip() for c in cols})
        say("    %-26s %d rows for the pool" % (fname, n))

    refs = aact / "study_references.txt"
    if refs.exists():
        n = 0
        with open(refs, "r", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f, delimiter="|"):
                nct = (row.get("nct_id") or "").strip().upper()
                if want.get(nct):
                    pmid = (row.get("pmid") or "").strip()
                    if pmid.isdigit():
                        n += 1
                        if "result" in (row.get("reference_type") or "").lower():
                            out["refs"][nct].insert(0, pmid)
                        else:
                            out["refs"][nct].append(pmid)
        say("    %-26s %d linked PMIDs for the pool" % ("study_references.txt", n))
    else:
        say("    %-26s MISSING -- gate D is UNDECIDABLE for every candidate"
            % "study_references.txt")
    return out


def main(argv):
    out_path = Path(argv[1]) if len(argv) > 1 else None
    aact_env = os.environ.get("AACT_DIR", "")
    ns = load_matcher()
    mb, ds, cs = ns["_match_blob"], ns["DRUG_SYNS"], ns["COND_SYNS"]

    pos, neg = controls(mb, ds, cs)
    require_controls(
        "measure_screening_dispositions",
        ("fabricated candidate whose abstract IS present and disagrees", pos, S.EXCLUDED),
        ("fabricated candidate identical but with NO abstract retrieved", neg, S.EXCLUDED),
    )

    records = sorted(RECORDS.glob("*.json")) if RECORDS.exists() else []
    print("SAMPLE   %d executed-search records under %s"
          % (len(records), RECORDS.relative_to(ROOT)))
    if not records:
        print("NOT_RUN -- there are no search records to screen. This is not a reading of "
              "zero undecidable.")
        return 1
    if not aact_env:
        print("AACT READING: NOT_RUN -- AACT_DIR is unset. Nothing was screened, and this "
              "is NOT a reading of zero undecidable.")
        return 0

    aact = Path(aact_env)
    docs = []
    pool = []
    for p in records:
        d = json.loads(p.read_text(encoding="utf-8"))
        docs.append(d)
        pool.extend(d.get("nct_ids", []))
    pool_unique = sorted(set(pool))
    print("POOL     %d candidates across %d topics (%d distinct registrations)"
          % (len(pool), len(docs), len(pool_unique)))
    t0 = time.time()
    data = load_for(aact, pool_unique, lambda s: print(s))
    print("    read in %.0fs" % (time.time() - t0))

    # PUBMED IS NOT CONSULTED HERE, and that is stated rather than left to be discovered in
    # the numbers. This instrument reads a local snapshot only, so every candidate whose
    # gate D needs an abstract is UNDECIDABLE by construction -- which is exactly the state
    # the pipeline currently records as a failure, and the thing being counted.
    pubmed_meta = {}
    print("    PubMed: NOT CONSULTED by this instrument (local snapshot only), so gate D "
          "is UNDECIDABLE wherever it needs an abstract")

    rows = []
    for d in docs:
        # Read as FIELDS. A record that only carries its predicate inside a sentence
        # forces every reader to parse prose, and the first such reader here reached
        # for a regex and an eval before the schema was fixed instead.
        topic_patterns = {"drug_patterns": d["drug_patterns"],
                          "condition_patterns": d["condition_patterns"]}
        disps, per_gate = [], defaultdict(lambda: defaultdict(int))
        for nct in d.get("nct_ids", []):
            r = S.classify(
                nct=nct,
                topic=topic_patterns,
                aact_rows=data["studies"].get(nct, []),
                intvs=[x["name"] for x in data["intv"].get(nct, [])],
                conds=[x["downcase_name"] for x in data["cond"].get(nct, [])],
                pmids=data["refs"].get(nct, []),
                pubmed_meta=pubmed_meta,
                baseline_rows=data["baseline"].get(nct, []),
                design_outcome_rows=data["design_outs"].get(nct, []),
                match_blob=mb, drug_syns=ds, cond_syns=cs)
            disps.append(r["disposition"])
            for g, (state, _why) in r["states"].items():
                per_gate[g][state] += 1
        t = S.tally(disps)
        rows.append({"topic": d["topic"], "pool": len(d.get("nct_ids", [])),
                     "tally": t,
                     "per_gate": {g: dict(v) for g, v in per_gate.items()}})

    print("")
    print("%-44s %7s %9s %9s %12s" % ("TOPIC", "pool", "INCLUDED", "EXCLUDED", "UNDECIDABLE"))
    for r in sorted(rows, key=lambda r: -r["pool"]):
        print("%-44s %7d %9d %9d %12d"
              % (r["topic"][:44], r["pool"], r["tally"][S.INCLUDED],
                 r["tally"][S.EXCLUDED], r["tally"][S.UNDECIDABLE]))

    tot_pool = sum(r["pool"] for r in rows)
    tot = {k: sum(r["tally"][k] for r in rows)
           for k in (S.INCLUDED, S.EXCLUDED, S.UNDECIDABLE)}
    print("")
    print("candidates screened          %d   (the DENOMINATOR: the eligible pool, not the "
          "ingested head)" % tot_pool)
    for k in (S.INCLUDED, S.EXCLUDED, S.UNDECIDABLE):
        print("%-28s %d   %.1f%%" % (k, tot[k], 100.0 * tot[k] / max(tot_pool, 1)))
    print("")
    print("THE COLLAPSE THIS MEASURES: under the six-boolean scheme every UNDECIDABLE above "
          "is recorded as a gate failure and counted with the exclusions.")
    gate_roll = defaultdict(lambda: defaultdict(int))
    for r in rows:
        for g, v in r["per_gate"].items():
            for state, n in v.items():
                gate_roll[g][state] += n
    print("")
    print("%-26s %8s %8s %12s" % ("GATE", "PASS", "EXCLUDE", "UNDECIDABLE"))
    for g in S.GATE_ORDER:
        v = gate_roll.get(g, {})
        print("%-26s %8d %8d %12d"
              % (g, v.get(S.PASS, 0), v.get(S.EXCLUDE, 0), v.get(S.UNDECIDABLE, 0)))

    if out_path:
        out_path.write_text(json.dumps(
            {"instrument": "measure_screening_dispositions_2026_09_03",
             "snapshot": aact.name, "topics": len(rows),
             "denominator_candidates": tot_pool, "totals": tot,
             "pubmed_consulted": False,
             "per_gate": {g: dict(v) for g, v in gate_roll.items()},
             "rows": rows}, indent=2), encoding="utf-8")
        print("")
        print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
