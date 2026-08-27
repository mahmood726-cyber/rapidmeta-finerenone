# Registration stream — paused position, 2026-08-27

Corpus fixing became the priority; the four-source searches and the remaining question
authoring were cut. Everything below is preserved, nothing is half-written, and this
file is the position a later run resumes from.

Branch: `registration/batch-138`.

---

## What is COMPLETE and anchored

Five topics went the whole way: protocol authored, committed, pushed, anchored in the
public transparency log, searched, search record committed and anchored. Two ends
bracketed by third-party times in every case.

| topic | protocol anchor | search anchor |
|---|---|---|
| `finerenone-cv` | logIndex 2604694652 | logIndex 2604754261 |
| `empagliflozin-hf-auto-full-review` | 2605627307 | 2605693104 (+ screening 2605766019, adjudication 2606218011) |
| `antimalarial-act` | 2606041205 | 2606136300 |
| `colchicine-pericarditis` | 2608365599 | 2608497387 |
| `dabigatran-vte-extended` | 2608402596 | 2608529882 |

Ten anchors total. All verified by fetching the entry back and comparing its hash to the
bytes at the named commit. Recipe and public key: `ssot/registration/VERIFY.md`.

## What is DRAFTED but NOT a registration

**23 protocols**, one per topic, committed only so the work survives the pause. Each
carries a banner saying what it is not. **None is anchored. None has been searched.**

Their own Status lines, written by the drafting model, call them registrations. Those
lines are WRONG and are deliberately left unedited so the drafts are preserved exactly
as generated; the banner above each one says so. One of them, `sglt2-hf`, asserts
registration "BY COMMIT AND PUBLIC TRANSPARENCY LOG" — a log entry that was never made.
That is the sharpest reason the banner exists.

To resume: for each topic, commit → push → anchor → record the log index → search →
record → anchor. Strictly per topic. A batch that anchors ten protocols and then runs
ten searches has anchored nothing meaningful.

## What is AUTHORED but not adjudicated

**43 review questions**, two families cold, on topics whose stored questions could not
be registered as written.

- 13 both families authored a question
- 23 both families said UNANSWERABLE
- 7 split

Ten of the 43 were adjudicated and anchored: `ssot/registration/
QUESTION-ADJUDICATIONS-BATCH-1.json`, logIndex 2612701169. The remaining 33 have drafts
in the run record but no adjudication.

**Setting matters and must not be pooled.** Those 43 ran with openai at `xhigh` — the
inherited default from `~/.codex/config.toml`, which is the highest valid level for
gpt-5.5. Later work is pinned to `high`, one step below. A split direction and a
caveats-per-answer rate are properties of the configuration as well as the model, so a
resumed run starts a new denominator rather than extending this one.

## What was DELIBERATELY not done

**23 topics were not searched, on purpose.** Both families independently called their
questions UNANSWERABLE, so their scope is unresolved. Searching a topic whose question
cannot be written is work that gets repeated once the scope changes. Establishing that
split before spending capacity avoided searching a third of the corpus twice.

---

## Counts, as they stand

```
topic directories                        155
  retired tombstones                      14   never author, never search
  verdict-only                            67   built to record a verdict, not a pool
  live reviews                            74

live reviews complete (protocol+search)    5
live reviews drafted, unanchored          23
live reviews searchable once adjudicated  21
scope unresolved, deliberately unsearched 23

questions authored, two families          43
  adjudicated and anchored                10
  drafted, not adjudicated                33

transparency-log anchors made             11
searches executed                          5 topics
searches failed                            1 query (antimalarial PubMed, 24 boolean
                                           operators against an interface cap of 20 —
                                           recorded as the first-attempt time, which is
                                           the time the ordering test uses)
searches recorded EMPTY                    1 query (isrctn, a genuine HTTP 200 with zero
                                           records — not a failure)
```

## Sources, as verified live rather than as briefed

PubMed, Europe PMC, ClinicalTrials.gov all free and answering. ISRCTN free XML API,
answering — used as the programmatic stopgap for ICTRP, because the WHO bulk-crawling
service is unavailable and the WHO portal was not searched. OpenAlex is **not paywalled**:
an API key plus a modest daily free allowance, so a `$0 remaining` 429 means the day's
allowance is spent and it resets at midnight UTC. It was reported here as "unusable" for
several hours, which was true of that moment and wrong as a characterisation.

**Not searched, and to be said plainly in every protocol: Embase and CENTRAL.** Neither
is free. Claiming Cochrane-standard coverage without them is the class of unbacked method
claim this work exists to remove.

Measured rate: **2.4 seconds per topic for five sources.** The search was never the
bottleneck. Protocol drafting at 12 concurrent Codex jobs runs ~34 s/topic; the serial
anchor-then-search chain is the whole cost, and it is serial by necessity rather than by
oversight.

## Open, and not mine to decide

- `outputs/FIX-RUN-STANDING-ORDERS.md` **does not exist** — not in `outputs/`, not
  anywhere under `F:` at depth ≤4, not on any remote branch, and never committed in this
  repository's history. It was cited as the standing orders for an unattended run. Its
  §6b was relayed in full and is actionable; the rest is unread and is not being inferred.
- `out/ESCALATIONS.jsonl` does not exist either.
- `PRIOR_META_TABLE` as a provenance tier: not yet checked against the declared tier
  vocabulary, and not invented.
- `sotagliflozin-hf` is held, unauthored: under another lane's review and Mahmood's
  question-reframe decision.
