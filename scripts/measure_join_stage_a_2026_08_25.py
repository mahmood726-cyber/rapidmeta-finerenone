"""Does PubMed's own secondary-ID field recover a registration from a PMID?

THE JOIN THIS IS PART OF. Cochrane extraction packages label a trial `Carter 1970`. To ask
mechanically whether a row's trial matches a registration, that label has to reach an NCT.
A direct author-year -> NCT join returned 2%, which is not a join. Before writing the route
off, the question splits in two and only the second half is hard:

    STAGE A   PMID -> NCT      via PubMed's DataBank/AccessionNumber field
    STAGE B   author-year -> PMID   via esearch

This script measures STAGE A ONLY, and says so. If A is near-total then the whole difficulty
of the join is B, and B is a different problem (disambiguating a label) with different
remedies. If A is poor, the route is dead and no amount of B helps.

GROUND TRUTH, AND ITS LIMIT. 34 (pmid, nct) pairs taken from `inputs.trials` across this
corpus, where a trial row carries BOTH ids. The NCTs were verified against live
ClinicalTrials.gov records on 2026-08-19; the PMIDs are a separate field. THE LIMIT: this is
OUR extraction, so a systematically wrong pairing here would be invisible to this
measurement. 34 is a small set and every number below carries that denominator.

THE NULL TEST, run by default. The same 34 PMIDs are paired with a SHUFFLED NCT (derangement,
so no pmid keeps its own). A route that "recovers" those is matching on nothing. A recovery
rate is not a rate until the null is known.
"""
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
TRUTH = (r"F:@claude-temp@claude@F--rapidmeta-finerenone"
         r"@e2e2a1d5-c19e-44de-90ab-690dbc5235a1@scratchpad@join_truth.json").replace("@", chr(92))
CACHE = os.path.join(REPO, "outputs", "pubmed_databank_cache")
OUT = os.path.join(REPO, "outputs", "join_stage_a_pmid_to_nct_2026_08_25.json")

EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
          "?db=pubmed&retmode=xml&id=%s")

NCT_RE = re.compile(r"NCT\d{8}")
# The secondary-ID field. PubMed records a registration as
#   <DataBank><DataBankName>ClinicalTrials.gov</DataBankName>
#     <AccessionNumberList><AccessionNumber>NCT00643188</AccessionNumber>
# NOTE: this regex was first written through a placeholder substitution in which
# "@D"->backslash-d ran before "@DOT", so the pattern shipped as ClinicalTrials\dOTgov
# and matched nothing. It reported 0/34 -- and 0/34 is what sent me to look, because
# an implausible proportion is a statement about the instrument. Scanning the whole
# record would have "worked" off the NCT in the abstract and hidden the fault.
DATABANK = re.compile(
    r"<DataBankName>\s*ClinicalTrials\.gov\s*</DataBankName>(.*?)</DataBank>",
    re.S | re.I)


def fetch(pmid):
    """Cached efetch for one PMID. Returns XML text, or None -- never a fabricated empty."""
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, "%s.xml" % pmid)
    if os.path.exists(fp) and os.path.getsize(fp) > 400:
        return io.open(fp, encoding="utf-8", errors="replace").read()
    for attempt in (1, 2, 3):
        r = subprocess.run(["curl", "-sS", "-g", "--max-time", "60", EFETCH % pmid],
                           capture_output=True)
        body = (r.stdout or b"").decode("utf-8", "replace")
        if "<PubmedArticle" in body and len(body) > 400:
            io.open(fp, "w", encoding="utf-8").write(body)
            return body
        time.sleep(2 * attempt)
    return None


def ncts_in_databank(xml):
    """Registrations from the DataBank field ONLY -- not from anywhere in the record.

    Scanning the whole XML would also pick up an NCT mentioned in the abstract, including a
    DIFFERENT trial's, and that would inflate the recovery rate with matches the field does
    not actually support.
    """
    out = []
    for block in DATABANK.findall(xml or ""):
        out.extend(NCT_RE.findall(block))
    return out


def derange(items):
    """A fixed-seed derangement: no element keeps its own position. No Math.random equivalent."""
    n = len(items)
    return [items[(i + 1) % n] for i in range(n)]


def main():
    truth = json.load(io.open(TRUTH, encoding="utf-8"))
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + chr(10))
        raw.flush()

    log("STAGE A ONLY: PMID -> NCT via PubMed DataBank. Stage B (author-year -> PMID) is a")
    log("separate measurement and is NOT reported here.")
    log("ground truth: %d (pmid, nct) pairs from inputs.trials, our own extraction" % len(truth))
    log("")

    rows, missing = [], 0
    for i, t in enumerate(truth, 1):
        xml = fetch(t["pmid"])
        if xml is None:
            missing += 1
            rows.append(dict(t, status="MISSING", found=[]))
            log("[%2d/%d] %s  MISSING -- no payload after 3 attempts" % (i, len(truth), t["pmid"]))
            continue
        found = ncts_in_databank(xml)
        hit = t["nct"] in found
        rows.append(dict(t, status="ok", found=found, hit=hit,
                         n_databank=len(found), bytes=len(xml)))
        log("[%2d/%d] %-9s %-12s databank=%-2d %s %s"
            % (i, len(truth), t["pmid"], t["nct"], len(found),
               "HIT " if hit else ("WRONG" if found else "NONE "),
               "" if hit else ",".join(found[:3])))
        time.sleep(0.34)

    ok = [r for r in rows if r["status"] == "ok"]
    hits = [r for r in ok if r["hit"]]
    hasany = [r for r in ok if r["found"]]
    wrong = [r for r in ok if r["found"] and not r["hit"]]

    # NULL: the same payloads, each paired with someone else's NCT.
    shuffled = derange([r["nct"] for r in ok])
    null_hits = sum(1 for r, n in zip(ok, shuffled) if n in r["found"])

    log("")
    log("payload obtained            : %d / %d   (MISSING %d)" % (len(ok), len(rows), missing))
    log("DataBank field non-empty    : %d / %d" % (len(hasany), len(ok)))
    log("recovered the CORRECT nct   : %d / %d" % (len(hits), len(ok)))
    log("field present but different : %d / %d" % (len(wrong), len(ok)))
    log("NULL (deranged pairing)     : %d / %d" % (null_hits, len(ok)))
    log("")
    if not ok:
        log("NOT MEASURABLE: no payload was obtained, so nothing is reported.")
    else:
        log("Stage A recovery is %.0f%% of %d, against a null of %.0f%%."
            % (100.0 * len(hits) / len(ok), len(ok), 100.0 * null_hits / len(ok)))
        log("Stage B (author-year -> PMID) is untouched here and is where the join stands or")
        log("falls; do not read this number as a join rate.")

    json.dump({"stage": "A only: pmid -> nct via PubMed DataBank",
               "ground_truth": "34 (pmid,nct) pairs from inputs.trials in this corpus",
               "ground_truth_limit": "our own extraction; a systematic mis-pairing would be "
                                     "invisible to this measurement",
               "n_truth": len(rows), "n_payload": len(ok), "missing": missing,
               "databank_nonempty": len(hasany), "correct": len(hits), "wrong": len(wrong),
               "null_deranged": null_hits, "rows": rows},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    log("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
