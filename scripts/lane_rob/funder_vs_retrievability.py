# -*- coding: utf-8 -*-
"""Does the FUNDER of a trial decide whether we can assess its risk of bias?

THE HYPOTHESIS, from the dapivirine pair. ASPIRE was NIH-funded, deposited in PMC, and its
manuscript answers 4 of 5 signalling questions. The Ring Study was industry-funded, is not in
PMC, and answers none. Same review, same domains, same difficulty -- different funder.

IF THAT GENERALISES IT IS A BIAS IN THE BIAS ASSESSMENT, and it runs in the direction that
matters: an open-path review systematically under-assesses industry-funded trials, which are
the trials most likely to carry sponsor influence and therefore the ones a risk-of-bias
assessment most needs to examine.

⚠️ THREE PROPERTIES, NOT ONE FIELD. `inPMC`, `isOpenAccess` and MACHINE-RETRIEVABLE are
different, and this project treated them as one until Europe PMC returned 404 for a deposit
that NCBI efetch served in full. So every trial is probed on BOTH routes and the route that
succeeded is recorded. A document is never marked unreachable on one index's say-so.

OUTPUT is one JSONL row per trial: nct, funder class, linked PMIDs, inPMC/isOpenAccess flags,
whether Europe PMC served full text, whether NCBI efetch served it, and which route won.
"""
import collections
import glob
import io
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)
OUT = r"F:\claude-temp\pend\funder_retrievability.jsonl"
CACHES = [os.path.join(REPO, ".ctgov-raw-cache"),
          r"F:\rapidmeta-ssot-shell\.ctgov-raw-cache"]


def curl(url, dest):
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "45", "-o", dest,
                            "-w", "%{http_code}|%{size_download}", url],
                           capture_output=True, timeout=90)
        code, _, size = r.stdout.decode("ascii", "replace").partition("|")
        return code.strip(), int(size or 0)
    except Exception:
        return "ERR", 0


def store_ncts():
    ncts = set()
    for p in sorted(glob.glob("ssot/*/*.json")):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for tr in ((o.get("inputs") or {}).get("trials") or []):
            if isinstance(tr, dict) and tr.get("nct"):
                ncts.add(tr["nct"])
        for oid, rr in (((o.get("risk_of_bias") or {}).get("by_outcome")) or {}).items():
            for rid in (rr or {}):
                if str(rid).startswith("NCT"):
                    ncts.add(rid)
    return ncts


def funder_index():
    """nct -> lead sponsor class, from every local record we hold. Both caches and sources."""
    idx = {}
    files = list(glob.glob("ssot/*/sources/*.ctgov.json"))
    for c in CACHES:
        if os.path.isdir(c):
            files += [os.path.join(c, f) for f in os.listdir(c) if f.endswith(".json")]
    for f in files:
        m = re.search(r"(NCT\d+)", os.path.basename(f))
        if not m or m.group(1) in idx:
            continue
        try:
            d = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        ps = d.get("protocolSection") or (d.get("study") or {}).get("protocolSection") or {}
        c2 = (((ps.get("sponsorCollaboratorsModule") or {}).get("leadSponsor")) or {}).get("class")
        if c2:
            idx[m.group(1)] = c2
    return idx


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    ncts = sorted(store_ncts())
    fund = funder_index()
    have = [n for n in ncts if n in fund]
    print("distinct NCTs in stores        %4d  == the denominator" % len(ncts))
    print("with a funder class on disk    %4d   %5.1f%%" % (len(have), 100.0 * len(have) / len(ncts)))
    print("no local registration record   %4d   %5.1f%%  <- NOT counted as any funder class"
          % (len(ncts) - len(have), 100.0 * (len(ncts) - len(have)) / len(ncts)))
    c = collections.Counter(fund[n] for n in have)
    for k, v in c.most_common():
        print("   %-18s %4d" % (k, v))
    print("")
    done = set()
    if os.path.exists(OUT):
        for ln in io.open(OUT, encoding="utf-8"):
            try:
                done.add(json.loads(ln)["nct"])
            except Exception:
                pass
    todo = [n for n in have if n not in done]
    print("already probed %d, probing %d" % (len(done), len(todo)))
    tmp = os.path.join(os.environ.get("TEMP", "."), "_fr_probe.json")
    with io.open(OUT, "a", encoding="utf-8") as fh:
        for i, n in enumerate(todo, 1):
            rec = {"nct": n, "funder": fund[n]}
            code, size = curl(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%s"
                "&resultType=core&format=json&pageSize=10" % n, tmp)
            pmcids, oa, inpmc = [], [], []
            if code == "200":
                try:
                    d = json.load(io.open(tmp, encoding="utf-8"))
                    for x in ((d.get("resultList") or {}).get("result") or []):
                        if x.get("pmcid"):
                            pmcids.append(x["pmcid"])
                            oa.append(x.get("isOpenAccess"))
                            inpmc.append(x.get("inPMC"))
                except Exception:
                    pass
            rec.update(n_pmc=len(pmcids), any_oa=("Y" in oa), any_inpmc=("Y" in inpmc))
            # THE TWO ROUTES, BOTH TRIED, ON THE FIRST DEPOSIT ONLY -- enough to decide
            # whether the trial is reachable at all without fetching every linked paper.
            rec["epmc_fulltext"] = rec["efetch_fulltext"] = False
            if pmcids:
                p0 = pmcids[0]
                c1, s1 = curl("https://www.ebi.ac.uk/europepmc/webservices/rest/%s/fullTextXML" % p0, tmp)
                rec["epmc_fulltext"] = (c1 == "200" and s1 > 4000)
                c2, s2 = curl("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                              "?db=pmc&id=%s&rettype=xml" % p0.replace("PMC", ""), tmp)
                rec["efetch_fulltext"] = (c2 == "200" and s2 > 4000)
                rec["pmcid"] = p0
            rec["route"] = ("epmc" if rec["epmc_fulltext"] else
                            ("efetch_only" if rec["efetch_fulltext"] else "none"))
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if i % 20 == 0:
                print("  %d/%d" % (i, len(todo)))
            time.sleep(0.34)
    print("done -> %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
