#!/usr/bin/env python
"""Adjudicate cross-app PMID conflicts using resolved title/year metadata.

Reads outputs/pmid_conflicts.json (NCT -> [pmids]) and the three saved PubMed
metadata batches, builds a pmid -> {title, year, doi} map, and flags PMIDs whose
title matches DESIGN (rationale/protocol/design) or SUB (post-hoc/subgroup/
extension/follow-up/QoL/economic) patterns. Those are candidate miscitations
where a results record may be pointing at a non-primary paper -- the CREDENCE
pattern. Verification against the app's shown outcome is still required before
any fix.
"""
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# One-off input: the PubMed metadata dumps. Point PMID_METADATA_DIR at the dir
# holding mcp-claude_ai_PubMed-get_article_metadata-*.txt; default in-repo.
BASE = os.environ.get(
    "PMID_METADATA_DIR", os.path.join(REPO, "outputs", "extraction_audit", "pmid_metadata"))
import glob

M = {}
for fn in sorted(glob.glob(os.path.join(BASE, "mcp-claude_ai_PubMed-get_article_metadata-*.txt"))):
    try:
        d = json.load(open(fn, encoding="utf-8"))
    except Exception:
        continue
    if "articles" not in d:
        continue
    for a in d["articles"]:
        pm = str(a["identifiers"].get("pmid"))
        y = a.get("publication_date", {})
        yr = y.get("year") if isinstance(y, dict) else None
        M[pm] = {"t": a.get("title", "") or "", "y": yr,
                 "doi": a["identifiers"].get("doi")}
json.dump(M, open(os.path.join(REPO, "outputs", "pmid_meta.json"), "w"))
print("resolved", len(M), "PMIDs")

DESIGN = re.compile(r"rationale|study design|design of|protocol|baseline charact"
                    r"|methodology|trial design", re.I)
SUB = re.compile(r"post.?hoc|subgroup|sub-study|substudy|exploratory"
                 r"|secondary analysis|long.term|extension|follow.up|\d+-year"
                 r"|open-label ext|pooled analysis|patient-reported"
                 r"|quality of life|health-related|economic|cost-eff", re.I)

def tag_of(p):
    t = M.get(p, {}).get("t", "")
    tag = []
    if DESIGN.search(t):
        tag.append("DESIGN")
    if SUB.search(t):
        tag.append("SUB")
    return "/".join(tag)


conf = json.load(open(os.path.join(REPO, "outputs", "pmid_conflicts.json")))["conflicts"]
allp = {p for ps in conf.values() for p in ps}
unresolved = sorted(p for p in allp if p not in M)
print(f"\nstill-unresolved PMIDs: {len(unresolved)}  {unresolved}")

# A conflict is a CANDIDATE MISCITATION when at least one of its PMIDs is a
# DESIGN/SUB paper AND at least one sibling PMID is a clean (untagged) paper --
# i.e. one app cites the primary-results paper, another cites a design/sub paper.
print("\n=== CANDIDATE MISCITATIONS (design/sub cited where a sibling cites a clean primary) ===")
cand = []
for nct, pmids in conf.items():
    tags = {p: tag_of(p) for p in pmids}
    tagged = [p for p in pmids if tags[p]]
    clean = [p for p in pmids if not tags[p] and p in M]
    if tagged and clean:
        cand.append(nct)
        print(f"\n{nct}:")
        for p in pmids:
            m = M.get(p, {})
            mark = tags[p] or ("primary?" if p in M else "UNRESOLVED")
            print(f"   {p} [{m.get('y','?')}] <{mark}> {m.get('t','')[:66]}")
print(f"\n{len(cand)} candidate-miscitation NCTs require app-level verification.")
