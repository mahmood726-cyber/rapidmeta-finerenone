# SPIRE trial protocols retrieved 2026-08-27 — and what they do NOT close

## What was retrieved

| file | trial | Pfizer protocol | bytes | sha256 (first 16) |
|---|---|---|---|---|
| `NCT01975376_Prot_000.pdf` | SPIRE-1 | B1481022, Final Protocol Amendment 2, 12 Feb 2016 | 5,408,559 | `3555e507637f5a94` |
| `NCT01975389_Prot_000.pdf` | SPIRE-2 | B1481038, Final Protocol, Amendment 2, 12 Feb 2016 | 4,487,900 | `e452e8f9c3245425` |

Source: `https://cdn.clinicaltrials.gov/large-docs/<last-2-of-NCT>/<NCT>/Prot_000.pdf`.
168 and 167 pages respectively; both verified as `%PDF-` on disk at the sizes above.

## They close ZERO of this review's ten D5 judgements

This must be stated first because the retrieval was authorised on the expectation that it
would convert those judgements into real assessments. **It does not, and the reason is
scope, not quality.**

Both documents are **trial-specific protocols for the two cardiovascular OUTCOMES trials.**
Neither mentions SPIRE-HR, SPIRE-LDL, SPIRE-FH, SPIRE-LL, SPIRE-SI or SPIRE-AI — the six
lipid-lowering studies that constitute this review's pool. A protocol for B1481022 is not the
analysis plan for SPIRE-HR, and RoB 2 domain 5 asks what *that trial's* plan specified.

So the D5 position is unchanged: **10 gaps, 0 closed**, all ten still `NOT_RETRIEVED_BY_US`.

## What they ARE good for

The SPIRE programme is **eight trials — six lipid-lowering plus these two outcomes trials** —
and this review pools six. Whether the outcomes trials belong in it is an open scoping
question going to Mahmood in a batch with the other scoping findings.

**If that ruling adds them, D5 is already answerable for both, because the plan documents are
here.** That is the whole value of this retrieval: it is pre-positioned evidence for a
decision not yet made, not a closed gap. Recorded as conditional rather than banked.

## The route, since the earlier probe missed it

`documentSection.largeDocumentModule` in the API v2 record returned nothing for these trials,
but the CDN path serves the file directly. **Probe with a plain GET, never a ranged one**: a
`Range: 0-0` request returns `206` for every filename including ones that cannot exist
(`ICF_000.pdf`, `Prot_SAP_001.pdf`), so it is an instrument that can only say "present". A
plain GET discriminates cleanly — `200`/`application/pdf` against `404`/`text/html`.

Re-probed with the working route, **all nine trials behind the ten D5 judgements still have
no protocol and no SAP.** That negative is now stronger than the original, because the route
has been demonstrated to work on trials in the same programme.
