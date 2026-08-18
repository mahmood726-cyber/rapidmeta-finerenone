# Paths: the three kinds of error, and how many routes a value can take

An organising principle, made operational rather than noted. Three kinds of path, and the
ledger rules sorted by which one each guards.

---

## Route count — measured, and it is worse than it reads

| | n |
|---|---|
| HTML pages in the repo | **1,486** |
| canonical objects | 146 |
| pages projected from an object (`PAGE_MAP`) | **88** |
| pages carrying an `AUTO_INCLUDE_TRIAL_IDS` JavaScript seed | **854** |
| pages carrying a hand-authored banner | 96 |
| objects carrying `inputs.trials` | 120 |

**88 of 1,486 pages are on the straight path — 5.9%.**

**And 854 pages carry a second, independent route for the same fact.** Trial identity
reaches a page both through `inputs.trials` on the object and through a JavaScript
`AUTO_INCLUDE_TRIAL_IDS` set embedded in the page. **Two routes to one value, and they have
already diverged**: the topic-blind residue list, where `NCT01035255` was seeded on
sacubitril pages and was residue elsewhere, was exactly this divergence.

**Fewer routes is not tidiness.** Every multi-route value in this corpus has diverged: the
cards, the Word renderer, the jump lists, the seeds. **Not one has stayed in sync on its
own.**

---

## Class 1 — the straight path: one route, source to reader

`registry → canonical object → projected surface`

**Every defect found this week came from a departure from it.** Cards authored instead of
projected. Jump lists hand-kept. Banners hand-authored. A manuscript renderer that never
received the extraction section. An index the hook never gated. **Not one defect came from
the straight path being followed and failing.**

That is the strongest structural claim in the programme and it is now measured: **the
94.1% of pages not on it are where every divergence lives.**

---

## Class 2 — going astray: error from not knowing

**Cured by measurement, and the record here is good.**

| | caught before reporting? |
|---|---|
| PAGE_MAP "0 of 28 reproducible" | yes |
| Class 4 screen "18 flags" (really 2) | yes |
| pending classifier "31 pending" (really 1) | yes |
| I² sweep "10–7" (really 10–1) | yes |
| verifier "6 files changed" (really 0) | yes |
| re-derivation "4 non-reproducing" (really 0) | **no — escalated, then retracted** |

**Five of six caught before reporting; one reached the user and was retracted.** All six
shared a shape: **they looked like a finding.** A measurement error producing a boring
result would have been investigated at leisure or never.

**These rules stay as prose, because prose is the right medium for them.** They are
judgement, not procedure — "check the mechanism, not just the correlation" cannot be
mechanised without knowing what the mechanism is.

---

## Class 3 — knowing and not doing: the expensive class

**Documentation has never once fixed one of these. Only enforcement has.**

| rule | broken how | status |
|---|---|---|
| net-deleting writes must be refused | `guard_write` **bypassed by a direct write** | **MECHANICAL** — `.githooks/pre-commit`, tested with a real refusal |
| never heredoc a regex or backticked prose | broken **three times** by its author, incl. this session's `-m` | **PROSE ONLY** |
| stage by path, never `git add -A` | broken **immediately after being written** | **PROSE ONLY** |
| substring matching is not identity | broken **inside the tool built to enforce it** | **PROSE ONLY** |
| decode subprocess bytes explicitly, never `text=True` | broken in the verifier, this session | **PROSE ONLY** |

**Four of five are prose only.** By the standing instruction — *anything in the third class
is made mechanical or deleted* — **each needs a mechanical form or removal**, because a
class-3 rule existing only as prose is worse than no rule: it creates the belief that the
failure is covered.

**What mechanical form each takes:**

- **`git add -A`** → a pre-commit hook that refuses a commit staging paths outside a
  declared set. Cheap, and the pre-commit hook already exists to host it.
- **heredoc / backtick** → a wrapper that writes scripts to a file and executes the file,
  making the shell never see the content. **The behaviour already exists as a habit and
  fails under time pressure, which is the definition of a class-3 rule.**
- **`text=True`** → a lint rule; one grep over `scripts/` and it is enforceable today.
- **substring matching** → the hardest, because "is this an identity comparison?" is not
  syntactically decidable. **Candidate for deletion-as-a-rule and replacement with a typed
  identifier helper**, which makes the correct thing the easy thing rather than the
  remembered thing.

**The model is the pre-commit hook. The counter-example is `guard_write`** — a helper that
must be called, was not called, and therefore guarded nothing.

---

## What this classification does not establish

**NOT that class 3 is the largest class** — it is the most expensive per instance, and this
table holds five rules against a ledger with far more. A full pass over every ledger entry
has **not** been done; these five are the ones with a demonstrated breach on record.

**NOT that the route count is complete.** It counts three routes it can detect by grep.
Hand-authored card text, the Word renderer path and the jump lists are known additional
routes and are **not** in the table because no reliable signal for them was written.
**The true route count is higher than four.**
