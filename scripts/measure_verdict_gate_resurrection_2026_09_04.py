# -*- coding: utf-8 -*-
"""How many topics the verdict gate killed on a sample the cap chose for it.

THE STAGE NOBODY HAD NAMED. `add_topic_autodiscover.py` ends each topic with

    topic_audit["verdict"] = "VIABLE" if topic_audit["n_pass_all"] >= 2 else "NOT_VIABLE"

and a NOT_VIABLE topic produces no page at all. `n_pass_all` counts the candidates that
passed all six gates -- among the ones that were AUDITED, which is the head the cap kept.

    VENETOCLAX_CLL_AUTO: pool 460 -> capped 8 -> audited 8 -> passed 0 -> NO PAGE.

    THE CAP AND THE VERDICT GATE COMPOUND. The cap chooses the sample; the gate judges the
    TOPIC on it. 452 candidates were never looked at, and the topic was written off on the
    eight that happened to survive an array bound.

WHAT THIS MEASURES, AND THE LIMIT IS THE POINT. For every NOT_VIABLE topic that has a
recorded pool, it screens the WHOLE pool -- not the audited head -- and counts the
candidates that pass every gate this machine can actually decide.

    GATE D IS NOT DECIDABLE HERE. It needs a PubMed abstract and this instrument does not
    consult PubMed, so D comes back UNDECIDABLE for every candidate. That is stated, not
    hidden, and it is why the output is an UPPER BOUND on resurrection: a topic reported
    here as a resurrection candidate has >= 2 candidates passing A, B, C, E and F, and
    still has to survive D once someone fetches the abstracts.

    AN UPPER BOUND IS THE HONEST SHAPE FOR THIS QUESTION. The claim being tested is that
    the verdict gate killed topics it should not have. A lower bound could not test it and
    a point estimate would be a fiction.

THE COMPARISON THAT ISOLATES THE CAP. The same count is taken twice: over the whole pool,
and over the first 8 in the pool's own ranked order -- the head the cap kept. If a topic
clears the bar on the pool and not on the head, the cap is what killed it, and that is
separable from a topic that fails on both.
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
TOPICS_DIR = ROOT / "outputs" / "new_topics"
SLICE_START = "DRUG_SYNS = {"
SLICE_END = "    return kept"

# The bar the pipeline applies. Read from the source rather than retyped, so this cannot
# drift away from the rule it is measuring.
VIABLE_AT = 2
# The bound the delivered corpus was built under.
OLD_CAP = 8

# The gates this machine can decide offline. D is excluded BY NAME rather than by being
# quietly left out of a loop.
OFFLINE_GATES = ("A_aact_exists", "B_drug_in_intvs", "C_condition_in_aact",
                 "E_two_arms", "F_primary_outcome_known")
NETWORK_GATE = "D_pmid_topic_match"


def load_matcher():
    src = SOURCE.read_text(encoding="utf-8")
    i = src.index(SLICE_START)
    j = src.index(SLICE_END) + len(SLICE_END)
    ns = {"re": re, "os": os}
    exec(compile(src[i:j], str(SOURCE), "exec"), ns)
    return ns, src


def verify_the_bar(src):
    """The threshold this instrument reports against must be the one the source applies."""
    m = re.search(r'"VIABLE" if topic_audit\["n_pass_all"\] >= (\d+) else "NOT_VIABLE"', src)
    if not m:
        raise SystemExit(
            "REFUSED: could not locate the verdict rule in %s. This instrument reports how "
            "many topics clear a bar; if it cannot read the bar out of the source it would "
            "be reporting against a remembered number. NO COUNT IS PRINTED." % SOURCE.name)
    return int(m.group(1))


def controls(mb, ds, cs):
    """A candidate that must pass every offline gate, and one that must not.

    POSITIVE  complete AACT rows, two arms, a primary outcome -> all five offline gates PASS.
              Without it, an instrument whose row-loading silently returned nothing would
              report every topic unresurrectable and look like a sober negative result.
    NEGATIVE  identical but with ONE posted arm -> E must EXCLUDE, so the candidate must NOT
              count toward resurrection. That is the direction in which this instrument
              would manufacture a revival that is not there.
    """
    def mk(baseline):
        return S.classify(
            nct="NCT00000001",
            topic={"drug_patterns": ["dapagliflozin"],
                   "condition_patterns": ["heart failure"]},
            aact_rows=[{"brief_title": "t"}],
            intvs=["dapagliflozin 10 mg"], conds=["heart failure"],
            pmids=[], pubmed_meta={},
            baseline_rows=baseline,
            design_outcome_rows=[{"outcome_type": "Primary", "measure": "m"}],
            match_blob=mb, drug_syns=ds, cond_syns=cs)

    two = [{"ctgov_group_code": "BG0", "count": "10", "scope": "overall",
            "units": "Participants"},
           {"ctgov_group_code": "BG1", "count": "20", "scope": "overall",
            "units": "Participants"}]
    one = [{"ctgov_group_code": "BG0", "count": "30", "scope": "overall",
            "units": "Participants"}]
    return passes_offline(mk(two)), passes_offline(mk(one))


def passes_offline(result):
    """True when every gate decidable without a network comes back PASS."""
    return all(result["states"][g][0] == S.PASS for g in OFFLINE_GATES)


def load_rows(aact, ncts, say):
    csv.field_size_limit(10 ** 9)
    want = {n: True for n in ncts}
    out = {k: defaultdict(list) for k in
           ("studies", "baseline", "design_outs", "intv", "cond")}
    spec = [("studies.txt", "studies", ("brief_title",)),
            ("baseline_counts.txt", "baseline",
             ("ctgov_group_code", "count", "scope", "units")),
            ("design_outcomes.txt", "design_outs", ("outcome_type", "measure")),
            ("interventions.txt", "intv", ("name",)),
            ("conditions.txt", "cond", ("downcase_name",))]
    for fname, key, cols in spec:
        p = aact / fname
        if not p.exists():
            say("    %-24s MISSING -- gates reading it become UNDECIDABLE" % fname)
            continue
        n = 0
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f, delimiter="|"):
                nct = (row.get("nct_id") or "").strip().upper()
                if want.get(nct):
                    n += 1
                    out[key][nct].append({c: (row.get(c) or "").strip() for c in cols})
        say("    %-24s %d rows for the pools" % (fname, n))
    return out


def main(argv):
    out_path = Path(argv[1]) if len(argv) > 1 else None
    aact_env = os.environ.get("AACT_DIR", "")
    ns, src = load_matcher()
    mb, ds, cs = ns["_match_blob"], ns["DRUG_SYNS"], ns["COND_SYNS"]

    bar = verify_the_bar(src)
    print("VERDICT RULE read from %s: VIABLE requires n_pass_all >= %d" % (SOURCE.name, bar))
    if bar != VIABLE_AT:
        print("NOTE: the source bar (%d) differs from this file's constant (%d); the "
              "SOURCE wins and is what is reported against." % (bar, VIABLE_AT))

    pos, neg = controls(mb, ds, cs)
    require_controls(
        "measure_verdict_gate_resurrection",
        ("fabricated candidate with complete rows, passes all offline gates", pos, True),
        ("same candidate with ONE posted arm, passes all offline gates", neg, True),
    )

    # The population: NOT_VIABLE topics that have BOTH a delivered verdict and a pool.
    dead = []
    for p in sorted(TOPICS_DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("verdict") != "NOT_VIABLE":
            continue
        rec = RECORDS / p.name
        if not rec.exists():
            dead.append((p.stem, None, d.get("n_total"), d.get("n_pass_all")))
            continue
        r = json.loads(rec.read_text(encoding="utf-8"))
        dead.append((p.stem, r.get("nct_ids", []), d.get("n_total"), d.get("n_pass_all")))

    with_pool = [t for t in dead if t[1]]
    without = [t for t in dead if not t[1]]
    print("NOT_VIABLE topics                 %d" % len(dead))
    print("  with a recorded pool            %d" % len(with_pool))
    print("  without one (NOT_ASSESSABLE)    %d  %s"
          % (len(without), ", ".join(t[0] for t in without[:6])))
    if not with_pool:
        print("NOT_RUN -- no NOT_VIABLE topic has a recorded pool, so nothing was screened. "
              "This is NOT a reading of zero resurrections.")
        return 1
    if not aact_env:
        print("AACT READING: NOT_RUN -- AACT_DIR unset. Nothing screened; NOT a reading of "
              "zero resurrections.")
        return 0

    aact = Path(aact_env)
    pool_union = sorted({n for _s, ids, _a, _b in with_pool for n in ids})
    print("")
    print("SNAPSHOT %s -- %d distinct registrations across %d pools"
          % (aact.name, len(pool_union), len(with_pool)))
    t0 = time.time()
    data = load_rows(aact, pool_union, lambda s: print(s))
    print("    read in %.0fs" % (time.time() - t0))
    print("    PubMed NOT CONSULTED: gate %s is UNDECIDABLE for every candidate, so every "
          "count below is an UPPER BOUND." % NETWORK_GATE)

    rows = []
    for stem, ids, n_total, n_pass in with_pool:
        topic_rec = json.loads((RECORDS / (stem + ".json")).read_text(encoding="utf-8"))
        topic = {"drug_patterns": topic_rec["drug_patterns"],
                 "condition_patterns": topic_rec["condition_patterns"]}
        ok_pool = 0
        ok_head = 0
        for idx, nct in enumerate(ids):
            r = S.classify(
                nct=nct, topic=topic,
                aact_rows=data["studies"].get(nct, []),
                intvs=[x["name"] for x in data["intv"].get(nct, [])],
                conds=[x["downcase_name"] for x in data["cond"].get(nct, [])],
                pmids=[], pubmed_meta={},
                baseline_rows=data["baseline"].get(nct, []),
                design_outcome_rows=data["design_outs"].get(nct, []),
                match_blob=mb, drug_syns=ds, cond_syns=cs)
            if passes_offline(r):
                ok_pool += 1
                if idx < OLD_CAP:
                    ok_head += 1
        rows.append({"stem": stem, "pool": len(ids), "delivered_n_total": n_total,
                     "delivered_n_pass_all": n_pass,
                     "pass_offline_in_pool": ok_pool,
                     "pass_offline_in_first_%d" % OLD_CAP: ok_head,
                     "resurrects_on_pool": ok_pool >= bar,
                     "resurrects_on_head": ok_head >= bar})

    rows.sort(key=lambda r: -r["pool"])
    print("")
    print("%-40s %6s %8s %9s %s" % ("TOPIC", "pool", "pass/pool", "pass/head8", "verdict"))
    for r in rows:
        v = ("RESURRECTS (cap was the cause)" if r["resurrects_on_pool"]
             and not r["resurrects_on_head"] else
             "resurrects on head too" if r["resurrects_on_pool"] else "stays NOT_VIABLE")
        print("%-40s %6d %8d %9d  %s"
              % (r["stem"][:40], r["pool"], r["pass_offline_in_pool"],
                 r["pass_offline_in_first_%d" % OLD_CAP], v))

    res = [r for r in rows if r["resurrects_on_pool"]]
    cap_caused = [r for r in res if not r["resurrects_on_head"]]
    print("")
    print("topics measured                                  %d" % len(rows))
    print("clear the bar (>=%d) on the FULL POOL             %d" % (bar, len(res)))
    print("clear it on the pool but NOT on the capped head   %d  <- the cap killed these"
          % len(cap_caused))
    print("candidates behind the measured topics             %d"
          % sum(r["pool"] for r in rows))
    print("")
    print("UPPER BOUND. Gate %s could not be decided here; each of these still has to "
          "survive it." % NETWORK_GATE)

    if out_path:
        out_path.write_text(json.dumps(
            {"instrument": "measure_verdict_gate_resurrection_2026_09_04",
             "snapshot": aact.name, "bar_read_from_source": bar,
             "old_cap": OLD_CAP, "offline_gates": list(OFFLINE_GATES),
             "network_gate_undecidable": NETWORK_GATE,
             "pubmed_consulted": False,
             "not_viable_total": len(dead),
             "not_viable_with_pool": len(with_pool),
             "clear_bar_on_pool": len(res),
             "cap_caused": len(cap_caused),
             "rows": rows}, indent=2), encoding="utf-8")
        print("")
        print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
