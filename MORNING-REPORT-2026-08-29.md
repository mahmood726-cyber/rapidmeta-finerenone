# Morning report — RoB lane, overnight 28→29 Aug

Written to be true rather than encouraging. Every number carries its denominator.

## ⛔ First: a finding was retracted overnight, and it was mine

**"An open-path review will systematically under-assess industry-funded trials" is REFUTED.**
It was proposed for the defect taxonomy. It must not go in.

| funder | n | reachable |
|---|---|---|
| INDUSTRY | 214 | **205 — 96%** |
| OTHER | 121 | **97 — 80%** |
| NIH | 7 | 6 — 86% |
| FED | 5 | 5 — 100% |
| OTHER_GOV | 4 | 2 — 50% |
| NETWORK | 2 | 2 — 100% |
| **ALL** | **353** | **317 — 90%** |

Industry trials are **more** reachable, ratio 1.19 the other way. The claim came from two
trials — ASPIRE deposited, Ring Study paywalled — one per arm, and the corpus reverses it.

⚠️ **And the refutation is narrower than it looks.** "Reachable" here means *any* paper linked
to the trial has retrievable full text — **not** that the primary report does, which is what
the dapivirine case turned on. Industry trials attract many secondary papers. The sharper
question is still open and needs an NCT→primary-publication link the corpus does not hold.

## ✅ What is measured, with denominators

**Assessor accuracy against a human expert panel** — the first this project has had.
Dapivirine ring, 2 trials × 5 domains: **4 of 10 cells agree with Cochrane.** Split:
**4 of 4 (100%) where we hold the evidence; 0 of 6 (0%) where we do not.** Every disagreement
is an absence, not a difference. ⚠️ Cross-tool (Cochrane used RoB 1), secondary source
(Cochrane's own table is paywalled — `isOpenAccess=N`, no PMCID), and both trials carried
identical judgements from every party, so **this is one comparison, not ten. It demonstrates
the method; it is not an accuracy estimate.**

**Multi-route retrieval works and is now the standard.** `scripts/lane_rob/multiroute_retrieve.py`
— Europe PMC → NCBI efetch → PMC direct → DOI, recording which succeeded, never returning a bare
"inaccessible". Planted both ways: the deposit Europe PMC 404s is served by efetch (44,179
rendered characters); a PMCID that cannot exist fails every route.
⚠️ **`efetch` returns HTTP 200 for a non-existent PMCID.** Only the rendered-character floor
rejected it — an HTTP-code check would have recorded a fabricated document as retrieved.

**Corpus-wide: 43 of 317 reachable trials (14%) are reachable ONLY via efetch.** A single-index
retrieval understates our reach by an eighth.

**Adjudication triage.** 330 paired domain cells: 197 agree (59.7%), 133 disagree (40.3%).
**All 133 are class A** — reader 2 returned verdicts with no signalling responses. **Zero cells
are adjudicable today; the queue is a re-ask queue.** Separately, **21 of 435** stored verdicts
do not follow from their own signalling responses under the published tables, every one toward
**more** risk (15 raise a domain to HIGH, which changes GRADE — third-party-facing, needs a
human read).

## ⚠️ What is blocked, and by what

**Access claims cannot be audited.** 155 stores, 20 carry an access claim, 59 claims total.
**5 named an identifier and all 5 were FALSE — retrievable, all via Europe PMC on the first
route.** But **54 of 59 name nothing to re-test.** They can be neither confirmed nor refuted.
⇒ **The larger defect is not that the claims are wrong; it is that they are unfalsifiable.**
An assertion of absence with no identifier and no named route is not a finding about a
document — it is a finding about whichever API was asked once.

**D5 retrieval.** 10 gaps, 0 closed. No protocol or SAP posted for any of the 9 trials, on
either the API field or the CDN path — established against a route proven to work on two other
trials in the same programme.

**Reader 2 signalling responses** — the precondition for classes B, C and D existing at all.

## Needs a ruling

1. **The 21 re-derivations** — 15 raise a domain to HIGH and change GRADE.
2. **The 54 unfalsifiable access claims** — rewrite each to name an identifier and the routes
   tried, or withdraw it. Rewriting is honest; withdrawing changes what pages say.
3. **SPIRE scope, 6 trials or 8** — the two outcomes trials are the only ones whose protocols
   we hold.

## Not done

`agy` unspent — no genuine cross-family judgement has arisen. Nothing run corpus-wide beyond
read-only measurement. No store was written.
