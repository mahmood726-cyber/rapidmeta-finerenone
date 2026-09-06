# -*- coding: utf-8 -*-
"""Re-run the Path-A audit for the NOT_VIABLE topics, with the fixed matcher and real abstracts.

WHY RE-RUNNING IS THE LEVER AND THE CAP IS NOT. Measured over the 14 NOT_VIABLE topics: the
cap killed exactly ONE. What killed the others was WHICH eight the old matcher handed the
audit. Its own comment at add_topic_autodiscover.py:5285 says it returned

    "the FIRST `max_per_topic` matches in arbitrary interventions.txt file order"

so the eight audited for VENETOCLAX_CLL_AUTO were recent registrations with no posted
results -- all eight failed gate E -- while seven of them are still in the pool, ranked far
down. The current matcher ranks by pivotal score (+2 late phase, +1 RESULTS POSTED) then
enrolment, and its head-8 has posted baselines for 8 of 8.

    THE CAP COST CANDIDATES. THE ARBITRARY FILE-ORDER SELECTION COST TOPICS. A topic is
    written off on the sample the selector happened to hand it, and eight arbitrary rows
    from a 460-row pool is not a sample of anything.

Staleness was checked and ruled out: those eight have overall baseline rows in the April
snapshot (7 of 8) and the August one (8 of 8), so the difference is ORDERING, not the
registry catching up.

WHAT THIS RUNS. The real gates, over two populations, for every NOT_VIABLE topic that has a
recorded pool:

    HEAD-8    the first 8 of the CURRENT ranked pool -- what the OLD cap would now keep
    POOL      every eligible candidate -- what the raised cap keeps

Both are audited with gate D DECIDED, because PubMed is reachable and the abstracts are
fetched with the pipeline's own efetch block, extracted verbatim rather than reimplemented.
A verdict computed with gate D undecidable would not be a verdict, and the whole point of
this lane is not to confuse the two.

A DEFECT IN THAT FETCH, NAMED HERE BECAUSE THIS FILE DEPENDS ON IT. The pipeline's efetch
loop ends `except Exception as e: print(f"  efetch error: {e}")`. A batch that fails leaves
its PMIDs out of `pubmed_meta` entirely, and the six-boolean gate D then reads that as the
abstract disagreeing. A network error becomes evidence about a trial. This file routes gate
D through screening_states, which separates "no PMID linked", "abstract never fetched" and
"abstract disagrees", and it REPORTS how many landed in each -- so a run degraded by a
failed batch announces itself instead of returning quiet exclusions.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
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
OLD_CAP = 8


def matcher_ns():
    src = SOURCE.read_text(encoding="utf-8")
    i = src.index("DRUG_SYNS = {")
    j = src.index("    return kept") + len("    return kept")
    ns = {"re": re, "os": os}
    exec(compile(src[i:j], str(SOURCE), "exec"), ns)
    return ns, src


def read_bar(src):
    m = re.search(r'"VIABLE" if topic_audit\["n_pass_all"\] >= (\d+) else "NOT_VIABLE"', src)
    if not m:
        raise SystemExit("REFUSED: cannot read the viability bar out of the source.")
    return int(m.group(1))


def fetch_pubmed(pmids, say):
    """The pipeline's own efetch block, same URL, same parse, same batch size.

    Returns (meta, n_batches, n_failed_batches). The failure count is RETURNED rather than
    printed and forgotten, because a batch that failed silently removes its PMIDs from the
    evidence and the six-boolean gate reads that as disagreement.
    """
    meta, failed, batches = {}, 0, 0
    pmids = sorted(set(p for p in pmids if p and p.isdigit()))
    BATCH = 50
    for i in range(0, len(pmids), BATCH):
        batch = pmids[i:i + BATCH]
        batches += 1
        params = {"db": "pubmed", "id": ",".join(batch),
                  "rettype": "abstract", "retmode": "xml"}
        url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
               + urllib.parse.urlencode(params))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapidmeta/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                root = ET.fromstring(r.read())
            for art in root.findall(".//PubmedArticle"):
                el = art.find(".//PMID")
                if el is None:
                    continue
                pmid = (el.text or "").strip()
                t = art.find(".//ArticleTitle")
                title = "".join(t.itertext()).strip() if t is not None else ""
                pieces = []
                for at in art.findall(".//Abstract/AbstractText"):
                    txt = "".join(at.itertext()).strip()
                    if txt:
                        pieces.append(txt)
                meta[pmid] = {"title": title, "abstract": " ".join(pieces)}
        except Exception as exc:  # noqa: BLE001 -- counted, not swallowed
            failed += 1
            say("    efetch batch %d FAILED: %s" % (batches, str(exc)[:90]))
        time.sleep(0.4)
    say("    pubmed: %d PMIDs requested, %d returned, %d of %d batches failed"
        % (len(pmids), len(meta), failed, batches))
    return meta, batches, failed


def load_rows(aact, ncts, say):
    csv.field_size_limit(10 ** 9)
    want = {n: True for n in ncts}
    out = {k: defaultdict(list) for k in
           ("studies", "baseline", "design_outs", "intv", "cond")}
    refs = defaultdict(list)
    spec = [("studies.txt", "studies", ("brief_title",)),
            ("baseline_counts.txt", "baseline",
             ("ctgov_group_code", "count", "scope", "units")),
            ("design_outcomes.txt", "design_outs", ("outcome_type", "measure")),
            ("interventions.txt", "intv", ("name",)),
            ("conditions.txt", "cond", ("downcase_name",))]
    for fname, key, cols in spec:
        p = aact / fname
        if not p.exists():
            say("    %-24s MISSING" % fname)
            continue
        n = 0
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f, delimiter="|"):
                nct = (row.get("nct_id") or "").strip().upper()
                if want.get(nct):
                    n += 1
                    out[key][nct].append({c: (row.get(c) or "").strip() for c in cols})
        say("    %-24s %d rows" % (fname, n))
    rp = aact / "study_references.txt"
    if rp.exists():
        with open(rp, "r", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f, delimiter="|"):
                nct = (row.get("nct_id") or "").strip().upper()
                if want.get(nct):
                    pmid = (row.get("pmid") or "").strip()
                    if pmid.isdigit():
                        if "result" in (row.get("reference_type") or "").lower():
                            refs[nct].insert(0, pmid)
                        else:
                            refs[nct].append(pmid)
        say("    %-24s %d registrations carry a PMID"
            % ("study_references.txt", len(refs)))
    else:
        say("    study_references.txt MISSING -- gate D undecidable for everything")
    return out, refs


def controls(mb, ds, cs):
    def mk(title, baseline):
        return S.classify(
            nct="NCT00000001",
            topic={"drug_patterns": ["dapagliflozin"],
                   "condition_patterns": ["heart failure"]},
            aact_rows=[{"brief_title": "t"}],
            intvs=["dapagliflozin 10 mg"], conds=["heart failure"],
            pmids=["111"], pubmed_meta={"111": {"title": title, "abstract": ""}},
            baseline_rows=baseline,
            design_outcome_rows=[{"outcome_type": "Primary", "measure": "m"}],
            match_blob=mb, drug_syns=ds, cond_syns=cs)["disposition"]
    two = [{"ctgov_group_code": "BG0", "count": "10", "scope": "overall",
            "units": "Participants"},
           {"ctgov_group_code": "BG1", "count": "20", "scope": "overall",
            "units": "Participants"}]
    one = [{"ctgov_group_code": "BG0", "count": "30", "scope": "overall",
            "units": "Participants"}]
    return mk("Dapagliflozin in heart failure", two), mk("Dapagliflozin in heart failure", one)


def main(argv):
    out_path = Path(argv[1]) if len(argv) > 1 else None
    aact_env = os.environ.get("AACT_DIR", "")
    ns, src = matcher_ns()
    mb, ds, cs = ns["_match_blob"], ns["DRUG_SYNS"], ns["COND_SYNS"]
    bar = read_bar(src)
    print("VIABILITY BAR read from source: n_pass_all >= %d" % bar)

    pos, neg = controls(mb, ds, cs)
    require_controls(
        "rerun_path_a_named_sample",
        ("fabricated candidate, matching abstract and two posted arms", pos, S.INCLUDED),
        ("same but ONE posted arm", neg, S.INCLUDED),
    )

    topics = []
    for p in sorted(TOPICS_DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("verdict") != "NOT_VIABLE":
            continue
        rec = RECORDS / p.name
        if not rec.exists():
            continue
        r = json.loads(rec.read_text(encoding="utf-8"))
        delivered = [t["extracted"]["nct"] for t in d.get("trials", [])
                     if (t.get("extracted") or {}).get("nct")]
        topics.append({"stem": p.stem, "pool": r.get("nct_ids", []),
                       "drug_patterns": r["drug_patterns"],
                       "condition_patterns": r["condition_patterns"],
                       "delivered_ncts": delivered,
                       "delivered_n_total": d.get("n_total"),
                       "delivered_n_pass_all": d.get("n_pass_all")})
    print("NOT_VIABLE topics with a recorded pool: %d" % len(topics))
    if not topics:
        print("NOT_RUN -- nothing to re-run. This is not a reading of zero resurrections.")
        return 1
    if not aact_env:
        print("AACT READING: NOT_RUN -- AACT_DIR unset. Nothing audited; NOT a reading of "
              "zero resurrections.")
        return 0

    aact = Path(aact_env)
    union = sorted({n for t in topics for n in t["pool"]}
                   | {n for t in topics for n in t["delivered_ncts"]})
    print("")
    print("SNAPSHOT %s -- %d distinct registrations" % (aact.name, len(union)))
    t0 = time.time()
    data, refs = load_rows(aact, union, lambda s: print(s))
    pm_needed = [v[0] for v in refs.values() if v]
    meta, nb, nfail = fetch_pubmed(pm_needed, lambda s: print(s))
    print("    read in %.0fs" % (time.time() - t0))
    if nfail:
        print("    WARNING: %d of %d efetch batches failed. Gate D is UNDECIDABLE for the "
              "PMIDs they carried, and is reported as such rather than as disagreement."
              % (nfail, nb))

    def audit(ncts, topic):
        inc = 0
        dstate = defaultdict(int)
        for nct in ncts:
            r = S.classify(
                nct=nct, topic=topic,
                aact_rows=data["studies"].get(nct, []),
                intvs=[x["name"] for x in data["intv"].get(nct, [])],
                conds=[x["downcase_name"] for x in data["cond"].get(nct, [])],
                pmids=refs.get(nct, []), pubmed_meta=meta,
                baseline_rows=data["baseline"].get(nct, []),
                design_outcome_rows=data["design_outs"].get(nct, []),
                match_blob=mb, drug_syns=ds, cond_syns=cs)
            if r["disposition"] == S.INCLUDED:
                inc += 1
            dstate[r["states"]["D_pmid_topic_match"][0]] += 1
        return inc, dict(dstate)

    rows = []
    for t in topics:
        topic = {"drug_patterns": t["drug_patterns"],
                 "condition_patterns": t["condition_patterns"]}
        head = t["pool"][:OLD_CAP]
        inc_head, d_head = audit(head, topic)
        inc_pool, d_pool = audit(t["pool"], topic)
        # The DELIVERED eight, re-audited under today's data, so the comparison separates
        # "the selector changed" from "the registry changed".
        inc_delivered, _ = audit(t["delivered_ncts"], topic)
        rows.append({
            "stem": t["stem"], "pool_size": len(t["pool"]),
            "delivered_ncts": t["delivered_ncts"],
            "current_head_ncts": head,
            "overlap_delivered_vs_head": len(set(t["delivered_ncts"]) & set(head)),
            "delivered_n_pass_all": t["delivered_n_pass_all"],
            "passed_delivered_reaudited": inc_delivered,
            "passed_current_head8": inc_head,
            "passed_full_pool": inc_pool,
            "verdict_head8": "VIABLE" if inc_head >= bar else "NOT_VIABLE",
            "verdict_pool": "VIABLE" if inc_pool >= bar else "NOT_VIABLE",
            "gateD_head": d_head, "gateD_pool": d_pool,
        })

    rows.sort(key=lambda r: -r["pool_size"])
    print("")
    print("%-40s %5s %4s %4s %4s %4s  %s"
          % ("TOPIC", "pool", "ovl", "del", "hd8", "pool", "verdict head8 -> pool"))
    for r in rows:
        print("%-40s %5d %4d %4d %4d %4d  %s -> %s"
              % (r["stem"][:40], r["pool_size"], r["overlap_delivered_vs_head"],
                 r["passed_delivered_reaudited"], r["passed_current_head8"],
                 r["passed_full_pool"], r["verdict_head8"], r["verdict_pool"]))

    res_head = [r for r in rows if r["verdict_head8"] == "VIABLE"]
    res_pool = [r for r in rows if r["verdict_pool"] == "VIABLE"]
    cap_only = [r for r in res_pool if r["verdict_head8"] != "VIABLE"]
    print("")
    print("topics re-audited                                   %d" % len(rows))
    print("VIABLE on the CURRENT head-8 (old cap, new matcher)  %d  <- re-running alone"
          % len(res_head))
    print("VIABLE on the FULL POOL (raised cap)                 %d" % len(res_pool))
    print("VIABLE only once the cap is raised                   %d" % len(cap_only))
    print("total zero-overlap topics (delivered 8 vs head 8)    %d of %d"
          % (sum(1 for r in rows if r["overlap_delivered_vs_head"] == 0), len(rows)))

    if out_path:
        out_path.write_text(json.dumps(
            {"instrument": "rerun_path_a_named_sample_2026_09_04",
             "snapshot": aact.name, "bar": bar, "old_cap": OLD_CAP,
             "pubmed_batches": nb, "pubmed_batches_failed": nfail,
             "viable_on_head8": len(res_head), "viable_on_pool": len(res_pool),
             "viable_only_with_raised_cap": len(cap_only),
             "rows": rows}, indent=2), encoding="utf-8")
        print("")
        print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
