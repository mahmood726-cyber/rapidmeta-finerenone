# Paper Studio — defect list, layer attribution, severity rank

Round 1, rubric v1.1. Scope: the `pn-paper` tab of the cardiology and infectious-disease
metas. **Nothing here is closed. Mahmood closes.**

## 0. A defect I committed, in the first person

**I ran two populations inside one lane and did not notice.** My mechanical checks took their
scope from `ssot/PAGE_MAP.json`. My reviewer runs took theirs from the specialty sections of
`index.html`. Those are different lists, and I used both for a week of counting without ever
asking whether they were the same.

They differed by three pages. **Two were full manuscripts that never reached a reviewer** —
`LENACAPAVIR_PREP_SSOT` and `PCSK9_INHIBITORS_CV_REVIEW`. The cause was retirement stubs:
**14 of the 15 sub-20KB links in those sections carry `rapidmeta:page-state` + `absorbed-by`
+ a canonical link, and only ONE carries `http-equiv=refresh`.** A resolver following
meta-refresh alone resolves 1 of 15.

**And the disagreement was visible in my own output the entire time.** Both missing
manuscripts appear in my D3 contradiction list — the mechanical checks reached them; the
reviewers never did. A page present in one of my lists and absent from the other looked like
a curiosity instead of what it was. I have spent the week finding this exact class in other
people's code.

The standing check that follows, and now blocks:
**`scripts/lint_scope_derivations_agree.py`** — index-derived scope, after following every
retirement marker, must equal PAGE_MAP-derived scope. Its selftest plants a paper-tab page
missing from PAGE_MAP and **requires the gate to refuse**, then removes it and requires a
pass, so it is shown to discriminate rather than merely to complain. Current state:
`104 index-derived, 103 with a paper tab in PAGE_MAP, 1 excluded for having no paper tab
(HFREF_NMA_AUTO_FULL_REVIEW.html), 0 unexplained.`

Two corrections to that gate before it was trusted, both mine, both the class it audits:
its first refusal said pages "carry a paper tab" when the one it named does not, and its
first PASS line said "the same 104" while printing 104 and 103.

## 1. Round 1 result — 25 of 25 reviewed

**Coverage: 23 of 25 (92%) at first pass; 25 of 25 (100%) after the two late-added pages.**
Both are reported as round 1, flagged late-added, not folded in silently.

| | cardiology | ID | total |
|---|---|---|---|
| manuscripts | 18 | 7 | **25** |
| PASS (both families required) | 0 | 0 | **0** |
| FAIL | 18 | 7 | **25** |
| calls returning real bytes | — | — | **50 of 50** |

## 2. Defects, by layer — with the ARNI column

`ARNI_HF_REVIEW` is the **only page of 149 not projected by `paper_projector.py`**. It is an
authored manuscript in `ssot/arni-hfref/` rendered by `ssot/wysiwyg.py`, and it is four times
longer than anything else in the corpus. **No projector fix reaches it.**

| # | defect | layer | reach | **ARNI twin needed?** |
|---|---|---|---|---|
| D1 | LOO clause contradicts its own count | **generator** `projectors2.py:777` + `add_visual_abstract.py:135` | 6 of 12 sentences, 5 pages | **no** — ARNI emits none |
| D2 | caption asserts CI crosses null when it excludes it | **generator**, same function | >=27 of 36 captions, 23 pages | **no** — ARNI emits none |
| D3 | Methods asserts RoB 2 while the page denies any assessment | **generator, key schism** | **24 pages** (20 backed, 4 unbacked) | **YES — and ARNI is the ONLY `rob2.*` object, so it is the one page the fix must not break** |
| D4 | no executed search record | **stored record** | 143 of 163 objects; **62 of 62 ID** | n/a — record, not projection |
| D5 | GRADE imprecision without OIS inputs | **stored record** | 4 cite OIS, **0 state inputs** | n/a |
| D6 | duplicate forest-plot control ids | **template** | 5 of 149 | **UNKNOWN — ARNI not yet checked** |
| D7 | broken in-page tab anchors | **template** | **148 anchors on 143 of 149 pages** | **YES** |
| D8 | source provenance (published vs FDA) | not attributed | unmeasured | unknown |

**D3 correction:** 24 pages, not the 45 first reported. My matcher counted the projector's own
refusal — *"The claim that risk of bias was assessed with a named tool"* — as an assertion of
it, scoring 25 correctly-refusing pages as defective. Re-measured with both controls.

## 3. Attribution, decided BEFORE the rebuild

The RoB lane's reader fix moves 82 pages. Deciding this after seeing which numbers improve is
how borrowed credit gets rationalised, so the columns are fixed now:

- **fixed by us** — a change this lane made to the generator, template, or object.
- **fixed by another lane** — resolved by the RoB reader fix or any other lane's rebuild,
  with no change from us. **Every D3 instance that clears on rebuild belongs here.**
- **still open** — unchanged.

Round 2 reports all three separately or it reports nothing.

## 4. Severity rank — all 25

Structural prerequisites missing from the object. Mechanical, not model-judged.

**TIER 1 — no structural gap; failing on prose and consistency only. The reachable passes (3).**
`IV_IRON_HF` (4 pools) · `SGLT2_HF` (2) · `BOCOCIZUMAB_LIPID` (1). All three carry D3, and
D1/D2 are generator fixes — **these three are one generator pass from a real attempt.**

**TIER 2 — one or two gaps (4).**
`ALIROCUMAB_LIPID` (eligibility) · `ARNI_HF` (PRISMA) · `AZILSARTAN_HTN` (RoB) ·
`INCLISIRAN_LIPID_KIDNEY` (search, PRISMA)

**TIER 3 — three or more gaps; no reachable path without new evidence (18).**
- **All seven ID manuscripts are here.** Six share one identical missing set — search, PRISMA,
  eligibility. That is one ID-wide gap, not six page defects, and **no amount of writing moves
  any ID page.**
- `LENACAPAVIR_PREP_SSOT` is the deepest in the corpus: six gaps, zero pools.
- The eight pool-nothing cardiology pages sit here, missing five each.
- `SOTAGLIFLOZIN_HF` — the externally reviewed page — is Tier 3 (search, PRISMA, GRADE).

**Effort concentrates on 7 pages. The other 18 need evidence, not prose.** 18 of 25 failing for
want of a search is D4 restated per page, not eighteen separate problems.
