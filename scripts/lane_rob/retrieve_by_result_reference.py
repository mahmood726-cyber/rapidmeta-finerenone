# -*- coding: utf-8 -*-
"""Retrieve trial reports by the join that MEANS "this document reports this trial".

THE JOIN WE HAVE BEEN USING IS WRONG AND THE NUMBERS SAY SO. The harvest resolved each trial to
the first PMCID Europe PMC returns for an NCT search. That search returns anything CITING the
trial, so 196 of 317 retrieved documents are systematic reviews and only 31 are a trial's own
primary report. 317 of 317 RETRIEVED and 31 PRIMARY REPORTS are different facts, and the first
does not imply the second.

⇒ THE AUTHORITATIVE JOIN IS THE REGISTRY'S OWN: `protocolSection.referencesModule.references[]`
with `type == "RESULT"`. That is the sponsor saying "this publication reports this trial". It is
sparse -- 55 of 317 trials, 215 PMIDs -- and covering 17.4% PROPERLY is worth more than covering
100% wrongly.

⚠️ THE OTHER 1,927 REFERENCES ARE type=DERIVED, which is the same citation link Europe PMC gives
and is exactly what produced the bad join. They are not used.

Resumable. One row per PMID with the route that succeeded, the document kind, and whether the
retrieved text NAMES the trial it was joined to.
"""
import collections
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
sys.path.insert(0, HERE)
import multiroute_retrieve as MR  # noqa: E402
import document_kind as DK  # noqa: E402

SRC = r"F:\claude-temp\pend\out\registry_result_pmids.json"
OUT_DIR = r"F:\claude-temp\pend\out\result_reports"
LOG = r"F:\claude-temp\pend\out\result_reference_join.jsonl"
DONE = r"F:\claude-temp\pend\out\RESULT-JOIN.DONE"


def pmid_to_pmcid(pmid):
    """NCBI's own id converter. Returns a PMCID or None -- None is a real state."""
    tmp = os.path.join(OUT_DIR, "_idconv.json")
    # ⚠️ -L AND THE CURRENT ENDPOINT. The first run used the old idconv path WITHOUT following
    # redirects, so every one of 215 lookups received a 301 HTML page, every pmcid came back
    # None, and the job reported "attempted 215; retrieved 0". Reported as a finding that would
    # have read "RESULT publications are not deposited in PMC" -- a false statement about the
    # world produced by a missing curl flag. Zero of a large denominator is a diagnosis, never
    # a result.
    subprocess.run(
        ["curl", "-s", "-L", "--max-time", "45", "-o", tmp,
         "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids=%s&format=json" % pmid],
        capture_output=True, timeout=90)
    try:
        d = json.load(io.open(tmp, encoding="utf-8"))
        for r in (d.get("records") or []):
            if r.get("pmcid"):
                return r["pmcid"]
    except Exception:
        pass
    return None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    src = json.load(io.open(SRC, encoding="utf-8"))
    pairs = [(n, p) for n, ps in src.items() for p in ps]
    print("trials naming a RESULT publication   %4d" % len(src))
    print("RESULT pmids named                   %4d  == the denominator" % len(pairs))
    done = set()
    if os.path.exists(LOG):
        for ln in io.open(LOG, encoding="utf-8"):
            try:
                r = json.loads(ln)
                done.add((r["nct"], r["pmid"]))
            except Exception:
                pass
    todo = [x for x in pairs if x not in done]
    print("already done %d, doing %d" % (len(done), len(todo)))
    with io.open(LOG, "a", encoding="utf-8") as fh:
        for i, (nct, pmid) in enumerate(todo, 1):
            pmcid = pmid_to_pmcid(pmid)
            rec = {"nct": nct, "pmid": pmid, "pmcid": pmcid, "route": None,
                   "kind": None, "names_trial": None, "rendered_chars": 0}
            if pmcid:
                dest = os.path.join(OUT_DIR, "%s_%s.xml" % (nct, pmcid))
                r = MR.retrieve(pmcid=pmcid, out_dir=OUT_DIR, save_as=dest)
                rec["route"] = r.get("route")
                rec["rendered_chars"] = r.get("rendered_chars")
                rec["sha256"] = r.get("sha256")
                if r.get("route"):
                    t = DK.rendered(io.open(dest, encoding="utf-8", errors="replace").read())
                    a = DK.assess(t)
                    rec["kind"] = a["kind"]
                    rec["names_trial"] = DK.names_trial(t, nct)
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if i % 20 == 0:
                print("  %d/%d" % (i, len(todo)))
            time.sleep(0.3)
    rows = [json.loads(l) for l in io.open(LOG, encoding="utf-8") if l.strip()]
    got = [r for r in rows if r.get("route")]
    kinds = collections.Counter(r["kind"] for r in got)
    trials_with = len({r["nct"] for r in got if r.get("kind") == "PRIMARY_REPORT"})
    print("")
    print("  RESULT pmids attempted            %4d" % len(rows))
    print("  with a PMC deposit                %4d" % sum(1 for r in rows if r.get("pmcid")))
    print("  full text retrieved               %4d" % len(got))
    print("  by kind:")
    for k, v in kinds.most_common():
        print("     %-20s %4d" % (k, v))
    print("")
    print("  TRIALS now holding a PRIMARY REPORT via this join   %4d" % trials_with)
    print("  (previous join, first Europe PMC hit per NCT:         31 of 317)")
    io.open(DONE, "w", encoding="utf-8").write(
        "attempted %d; retrieved %d; trials with a primary report %d\n"
        % (len(rows), len(got), trials_with))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
