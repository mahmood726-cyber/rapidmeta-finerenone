"""Section 6: resolve every corpus PMID to a DOI, and audit the DOIs we hold.

WHY THIS IS NOT A TITLE-MATCHING JOB. A silently wrong DOI is worse than a
missing one: it keys the row to a DIFFERENT PAPER, and every downstream join then
succeeds against the wrong article. The protocol therefore fixes the order --
NCBI idconv/esummary first, Crossref reverse lookup only as a last resort, and
only on a CONJUNCTION of title similarity AND author AND year AND journal. Title
score alone is exactly how a confident wrong answer gets produced.

This lane implements the first two steps, which are authoritative: PubMed's own
esummary articleids. Crossref is not reached here because every PMID we hold is
already a PubMed record, so the authoritative mapping exists without inference.
Rows esummary cannot resolve stay UNRESOLVED. They are not guessed.

THE AUDIT IS THE POINT. A local preflight found 32 of 187 held DOIs disagreeing
with the cache; twelve were checked live and ALL TWELVE were wrong on our side,
pointing at unrelated papers -- a Lancet health-policy editorial under a trial
PMID, an NEJM image-in-clinical-medicine under another. So this does not just
fill blanks, it re-checks what we already claim to know.

Network note: Codex's sandbox refuses outbound sockets (WinError 10013), which is
why this runs here rather than there.
"""
import glob
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

E = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
BATCH = 200            # esummary accepts 200 ids per POST-sized GET comfortably
PAUSE = 0.36
OUT = os.path.join("outputs", "doi_section6_resolved.json")

PMID_DOI = re.compile(
    r'pmid\s*:\s*["\'](\d{6,9})["\'](?:[^}]{0,400}?doi\s*:\s*["\']([^"\']{6,120})["\'])?',
    re.I)


def harvest():
    """Every (pmid, held_doi) pair the corpus asserts, with the file that says it."""
    pairs = {}
    files = sorted(glob.glob("*_REVIEW.html"))
    for f in files:
        try:
            s = open(f, encoding="utf-8", errors="replace").read()
        except Exception:                                    # noqa: BLE001
            continue
        for m in PMID_DOI.finditer(s):
            pmid, doi = m.group(1), (m.group(2) or "").strip().lower()
            rec = pairs.setdefault(pmid, {"held": set(), "files": set()})
            if doi:
                rec["held"].add(doi)
            rec["files"].add(f)
    return pairs, len(files)


def esummary(ids):
    u = E + "esummary.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
    for a in range(4):
        try:
            r = urllib.request.Request(u, headers={"User-Agent": "nafis-doi/1.0"})
            with urllib.request.urlopen(r, timeout=60) as h:
                b = h.read()
            if b[:1] != b"{":
                raise ValueError("non-JSON payload")
            return json.loads(b.decode("utf-8")).get("result", {})
        except Exception:                                    # noqa: BLE001
            if a == 3:
                return None
            time.sleep(1.5 * (2 ** a))
    return None


def live_doi(v):
    for a in (v.get("articleids") or []):
        if a.get("idtype") == "doi":
            return (a.get("value") or "").strip().lower()
    return None


def main():
    pairs, nfiles = harvest()
    ids = sorted(pairs)
    print("scanned %d review files | distinct PMIDs %d | of which assert a DOI %d"
          % (nfiles, len(ids), sum(1 for p in pairs.values() if p["held"])))
    resolved, unresolved, failed_batches = {}, [], 0
    t0 = time.time()
    for i in range(0, len(ids), BATCH):
        chunk = ids[i:i + BATCH]
        res = esummary(chunk)
        if res is None:
            failed_batches += 1
            continue
        for k, v in res.items():
            if k == "uids" or not isinstance(v, dict):
                continue
            resolved[k] = {"doi": live_doi(v), "title": (v.get("title") or "")[:180],
                           "journal": v.get("fulljournalname") or v.get("source"),
                           "year": (v.get("pubdate") or "")[:4]}
        time.sleep(PAUSE)
        if (i // BATCH) % 3 == 0:
            el = time.time() - t0
            print("  %d/%d PMIDs | %.0f/s" % (min(i + BATCH, len(ids)), len(ids),
                                              len(resolved) / el if el else 0))
    agree = wrong = only_live = no_doi_anywhere = 0
    wrongs = []
    for p in ids:
        held = pairs[p]["held"]
        live = (resolved.get(p) or {}).get("doi")
        if not live:
            if not held:
                no_doi_anywhere += 1
            unresolved.append(p)
            continue
        if not held:
            only_live += 1
            continue
        if any(h == live for h in held):
            agree += 1
        else:
            wrong += 1
            wrongs.append({"pmid": p, "held": sorted(held), "live": live,
                           "live_title": (resolved.get(p) or {}).get("title"),
                           "files": sorted(pairs[p]["files"])[:6],
                           "file_count": len(pairs[p]["files"])})
    checkable = agree + wrong
    out = {
        "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "route": "NCBI esummary articleids (authoritative). Crossref NOT used: "
                 "every row already carries a PubMed identifier, so no inference "
                 "is needed and none is made.",
        "review_files_scanned": nfiles,
        "distinct_pmids": len(ids),
        "pmids_resolved_to_a_doi": len(resolved),
        "pmids_unresolved": len(unresolved),
        "failed_batches": failed_batches,
        "held_doi_checkable": checkable,
        "held_doi_agrees": agree,
        "held_doi_wrong": wrong,
        "wrong_rate_pct": round(100.0 * wrong / checkable, 2) if checkable else None,
        "rate_denominator": "PMIDs where we hold a DOI AND PubMed returns one "
                            "(applicable rows, not corpus total)",
        "doi_available_but_not_held": only_live,
        "no_doi_on_either_side": no_doi_anywhere,
        "wrong_examples": sorted(wrongs, key=lambda x: -x["file_count"])[:60],
    }
    os.makedirs("outputs", exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n--- section 6, measured ---")
    print("distinct PMIDs            : %d" % len(ids))
    print("resolved by esummary      : %d" % len(resolved))
    print("unresolved (left blank)   : %d" % len(unresolved))
    print("held DOIs checkable       : %d" % checkable)
    print("  agree with PubMed       : %d" % agree)
    print("  WRONG                   : %d  (%.2f%% of checkable)"
          % (wrong, 100.0 * wrong / checkable if checkable else 0))
    print("DOI available, none held  : %d" % only_live)
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
