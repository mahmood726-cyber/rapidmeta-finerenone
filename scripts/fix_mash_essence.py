#!/usr/bin/env python
"""Fix the ESSENCE MASH record in MASH_DRUGS_REVIEW.html.

It was filed under NCT05633147 -- which is actually a linaprazan-glurate GERD
study -- and carried wrong counts/effect (165/400 vs 56/400, RR 2.95). ESSENCE
is NCT04822181 (semaglutide MASH). Per the primary publication (Sanyal et al,
NEJM 2025, PMID 40305708, DOI 10.1056/NEJMoa2413258), part-1 interim (week 72,
n=800, 2:1): resolution of steatohepatitis without worsening fibrosis occurred in
62.9% of 534 (=336) semaglutide vs 34.3% of 266 (=91) placebo -> RR 1.84
[1.54, 2.20].

Fixes: NCT key NCT05633147 -> NCT04822181 (label map + realData), counts
165/400/56/400 -> 336/534/91/266, effect 2.95 -> 1.84 (Wald log-RR CI),
year 2024 -> 2025, pmid null -> 40305708. Binary-safe, asserting, idempotent.
"""
from __future__ import annotations
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(REPO, "MASH_DRUGS_REVIEW.html")

REPLACEMENTS = [
    (b'"NULLED:NCT05633147"', b'"NULLED:NCT04822181"', 2),
    (b'name:"ESSENCE",baseline:{n:800,age:56},pmid:null,phase:"III",year:2024,'
     b'tE:165,tN:400,cE:56,cN:400',
     b'name:"ESSENCE",baseline:{n:800,age:56},pmid:"40305708",phase:"III",'
     b'year:2025,tE:336,tN:534,cE:91,cN:266', 1),
    (b'publishedHR:2.95,hrLCI:2.24,hrUCI:3.88',
     b'publishedHR:1.84,hrLCI:1.54,hrUCI:2.2', 1),
    (b'tE:165,cE:56,type:"PRIMARY",matchScore:95,effect:2.95,lci:2.24,uci:3.88',
     b'tE:336,cE:91,type:"PRIMARY",matchScore:95,effect:1.84,lci:1.54,uci:2.2', 1),
]


def main():
    data = open(PATH, "rb").read()
    if b'"NULLED:NCT04822181"' in data:
        print("already fixed (idempotent no-op)")
        return 0
    for old, new, n in REPLACEMENTS:
        assert data.count(old) == n, f"expected {n} of {old[:40]!r}, got {data.count(old)}"
        data = data.replace(old, new)
    open(PATH, "wb").write(data)
    print("fixed ESSENCE: NCT04822181, 336/534 vs 91/266, RR 1.84 [1.54,2.2], "
          "pmid 40305708")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
