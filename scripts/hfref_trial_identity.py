"""Build the HFrEF trial identity table: PMID by LOOKUP, title READ BACK.

PMIDs/DOIs/registry ids come from F:/E156/hfref-trial-ledger-v3.jsonl, keyed by
the same HF-### id the fit uses. Nothing is recalled from memory: a trial with
no identifier in the ledger is emitted with pmid=null and an explicit
"not recorded in the ledger" note rather than a guessed number.

Titles are then READ BACK from PubMed for every PMID the ledger supplies, and
the read-back title is what the app displays. A PMID whose title cannot be
retrieved is marked unverified rather than captioned from memory.

Writes outputs/hfref_trial_identity.json (cached; --refresh to re-fetch).
"""

import io
import json
import os
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = "F:/E156/hfref-trial-ledger-v3.jsonl"
BUNDLE = os.path.join(ROOT, "outputs", "hfref_nma_bundle.json")
OUT = os.path.join(ROOT, "outputs", "hfref_trial_identity.json")
ESUMMARY = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            "?db=pubmed&retmode=json&id=")


def fetch_titles(pmids):
    """Read titles back from PubMed. Returns {pmid: {...}} for those retrieved."""
    out = {}
    for i in range(0, len(pmids), 20):
        chunk = pmids[i:i + 20]
        url = ESUMMARY + ",".join(chunk)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=60) as fh:
                    res = json.load(fh).get("result", {})
                break
            except Exception as exc:                       # noqa: BLE001
                if attempt == 2:
                    raise SystemExit(f"PubMed read-back failed for {chunk}: {exc}")
                time.sleep(2 * (attempt + 1))
        for p in chunk:
            r = res.get(p)
            if not isinstance(r, dict) or not r.get("title"):
                continue
            out[p] = {
                "title": r["title"].strip(),
                "journal": r.get("source", ""),
                "pubdate": r.get("pubdate", ""),
            }
        time.sleep(0.4)
    return out


def main():
    refresh = "--refresh" in sys.argv
    with open(BUNDLE, encoding="utf-8") as fh:
        bundle = json.load(fh)
    included = bundle["trials"]["included_ids"]

    ledger = {}
    with open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("id"):
                ledger[rec["id"]] = rec

    cache = {}
    if os.path.exists(OUT) and not refresh:
        try:
            with open(OUT, encoding="utf-8") as fh:
                for t in json.load(fh).get("trials", []):
                    if t.get("pmid") and t.get("title"):
                        cache[t["pmid"]] = {
                            "title": t["title"],
                            "journal": t.get("journal", ""),
                            "pubdate": t.get("pubdate", ""),
                        }
        except Exception:                                   # noqa: BLE001
            cache = {}

    rows, need = [], []
    for tid in included:
        rec = ledger.get(tid)
        if rec is None:
            raise SystemExit(f"{tid} is in the fit but not in the ledger")
        idents = rec.get("identifiers") or {}
        pmid = idents.get("pmid")
        if pmid and pmid not in cache:
            need.append(pmid)
        rows.append({
            "id": tid,
            "name": rec.get("name"),
            "pmid": pmid,
            "doi": idents.get("doi"),
            "registry": idents.get("nct"),
            "edge": rec.get("edge"),
        })

    if need:
        print(f"reading back {len(need)} titles from PubMed ...")
        cache.update(fetch_titles(need))

    n_pmid = n_title = 0
    for r in rows:
        pmid = r["pmid"]
        if not pmid:
            r["title"] = None
            r["journal"] = None
            r["pubdate"] = None
            r["identity_note"] = (
                "No PMID/DOI recorded in hfref-trial-ledger-v3.jsonl or the "
                "2026-07-19 discovery ledger."
                + (f" Registry id: {r['registry']}." if r.get("registry") else "")
            )
            r["title_verified"] = False
            continue
        n_pmid += 1
        meta = cache.get(pmid)
        if meta:
            r.update(meta)
            r["title_verified"] = True
            r["identity_note"] = "PMID from the ledger; title read back from PubMed."
            n_title += 1
        else:
            r["title"] = None
            r["journal"] = None
            r["pubdate"] = None
            r["title_verified"] = False
            r["identity_note"] = (
                f"PMID {pmid} from the ledger; title could NOT be read back from "
                "PubMed and is therefore not displayed.")

    out = {
        "schema": "hfref-trial-identity/v1",
        "generated_by": "scripts/hfref_trial_identity.py",
        "pmid_source": LEDGER,
        "title_source": "PubMed esummary (read back, not recalled)",
        "counts": {
            "trials": len(rows),
            "with_pmid": n_pmid,
            "without_pmid": len(rows) - n_pmid,
            "titles_read_back": n_title,
        },
        "trials": rows,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print(f"WROTE {OUT}")
    print(f"  trials={len(rows)}  with PMID={n_pmid}  without={len(rows)-n_pmid}  "
          f"titles read back={n_title}")
    for r in rows:
        if not r["pmid"]:
            print(f"  no PMID: {r['id']} {r['name']}")


if __name__ == "__main__":
    main()
