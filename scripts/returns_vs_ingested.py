"""RETURNS vs INGESTED -- the number that proves whether the adapter is needed.

If the registry would return 200 under a declared eligibility filter and the page
ingested 20, the defect is INGESTION, not retrieval. This joins the adapter's
screening ledger (the RETURNS side) to the served page's own "Included studies"
section (the INGESTED side) and reports the gap.

Both sides are read from a pinned surface:
  RETURNS  -- a screening ledger, which records its snapshot folder AND the
              snapshot's measured data date.
  INGESTED -- a git blob at origin/main, quoted by sha. Not the working tree:
              the served page and the working-tree page are different objects
              with the same filename, and on SGLT2_HF they differ by 3.1 MB.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":                 # guarded: importing this must not
    sys.stdout = io.TextIOWrapper(         # close the importer's stdout
        sys.stdout.buffer, encoding="utf-8", errors="replace")

REF = "origin/main"
INCL = re.compile(
    rb'id="extract-included-studies">Included studies</h3>(.*?)</ul>', re.S)
NCT = re.compile(rb"NCT\d{8}")

# topic stem -> the served pages that carry that topic's synthesis
TOPIC_PAGES = {
    "SGLT2_HF": ["SGLT2_HF_REVIEW.html", "SGLT2I_HF_NMA_REVIEW.html"],
    "FINERENONE_CKD": ["FINERENONE_REVIEW.html", "FINERENONE_CV_REVIEW.html"],
    "APIXABAN_VTE": ["APIXABAN_VTE_TREATMENT_REVIEW.html",
                     "APIXABAN_VTE_PROPHYLAXIS_REVIEW.html"],
}


def ingested(repo, page):
    """Return (blob_sha, [NCT...]) from the served blob, or (None, None) when
    the page has no 'Included studies' section -- which is NOT_FOUND (the
    extractor cannot speak about this page), never 'this page ingests nothing'."""
    r = subprocess.run(["git", "-C", repo, "rev-parse", "%s:%s" % (REF, page)],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode:
        return None, None
    sha = r.stdout.strip()
    blob = subprocess.run(["git", "-C", repo, "cat-file", "blob", sha],
                          capture_output=True).stdout
    m = INCL.search(blob)
    if not m:
        return sha, None
    return sha, sorted(set(x.decode() for x in NCT.findall(m.group(1))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="F:/rapidmeta-finerenone")
    ap.add_argument("--ledgers", default="C:/claude-temp/regadapt/out")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    led = Path(args.ledgers)
    rows = []
    for stem in sorted(TOPIC_PAGES):
        lp = led / ("%s.screening_ledger.json" % stem)
        rp = led / ("%s.search_record.json" % stem)
        if not lp.exists():
            print("  ! NOT_FOUND: no ledger for %s -- skipping (this is a "
                  "missing measurement, not a zero)" % stem)
            continue
        L = json.loads(lp.read_text(encoding="utf-8"))
        R = json.loads(rp.read_text(encoding="utf-8"))
        cands = L["candidates"]
        inc = [c for c in cands if c["decision"] == "INCLUDE"]
        inc_ids = {c["nct_id"] for c in inc}

        page_rows, union = [], set()
        for page in TOPIC_PAGES[stem]:
            sha, got = ingested(args.repo, page)
            page_rows.append({"page": page, "blob": (sha or "")[:12],
                              "ingested": got,
                              "n_ingested": (len(got) if got is not None else None),
                              "extractor": ("ok" if got is not None
                                            else "NOT_FOUND: no included-studies section")})
            if got:
                union |= set(got)

        # eligible, late-phase, registry results already posted, not ingested:
        # the immediately checkable part of the gap.
        checkable = [c for c in inc
                     if c["nct_id"] not in union
                     and c["registry_results_posted"]
                     and c["phase"] in ("phase3", "phase4", "phase2/phase3")]

        rows.append({
            "topic": stem,
            "snapshot_folder": L["snapshot_folder"],
            "snapshot_data_date": L["snapshot_data_date"],
            "returned_candidates": L["denominator"],
            "eligible_after_filter": len(inc),
            "ingested_union": sorted(union),
            "n_ingested": len(union),
            "pages": page_rows,
            "controls": R["positive_controls"]["status"],
            "ingested_not_eligible": sorted(union - inc_ids),
            "never_screened_checkable": [
                {"nct_id": c["nct_id"], "enrollment": c["enrollment"],
                 "phase": c["phase"], "brief_title": c["brief_title"][:80]}
                for c in checkable],
            "n_never_screened_checkable": len(checkable),
        })

    print("\nRETURNS vs INGESTED   (RETURNS from AACT %s / data date %s;"
          % (rows[0]["snapshot_folder"], rows[0]["snapshot_data_date"])
          if rows else "no rows")
    print("                       INGESTED from git %s blobs)\n" % REF)
    hdr = ("%-16s %10s %10s %9s %8s %10s"
           % ("topic", "returned", "eligible", "ingested", "ctrls", "gap*"))
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print("%-16s %10d %10d %9d %8s %10d"
              % (r["topic"], r["returned_candidates"], r["eligible_after_filter"],
                 r["n_ingested"], r["controls"], r["n_never_screened_checkable"]))
    print("\n* gap = eligible AND late-phase AND registry results already posted "
          "AND not ingested\n  (the immediately checkable part of the gap, not "
          "the whole of it)")

    for r in rows:
        if r["ingested_not_eligible"]:
            print("\n  %s ingests %d trial(s) the filter did NOT mark eligible: %s"
                  % (r["topic"], len(r["ingested_not_eligible"]),
                     ", ".join(r["ingested_not_eligible"])))
            print("    -> the filter is under-inclusive here, or the page is "
                  "over-inclusive. Resolve before either number is quoted.")

    out = Path(args.out) if args.out else led / "returns_vs_ingested.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
