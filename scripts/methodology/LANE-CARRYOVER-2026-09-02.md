# Three things worth copying to other lanes

Written 2026-09-02. Each of these was earned by a defect tonight, not by theory.

---

## 1. Committing into a contended shared worktree — paste-able

**The problem:** several lanes commit into one worktree. `git add` writes to the *shared*
index, so **a staged file belongs to whoever runs `git commit` first** — your paths land in
someone else's commit, or theirs land in yours. Checking out to rebase makes it worse,
because it moves the working tree under every other lane.

**The method: never touch the shared index, never checkout.** Build the commit with plumbing
on a private index, parented directly on `origin/main`:

```bash
cd <worktree>
git fetch origin main -q
export GIT_INDEX_FILE=/some/private/path.index     # NOT .git/index
rm -f "$GIT_INDEX_FILE"
git read-tree origin/main                          # base = the real remote tip
git ls-tree -r <your-commit> -- <your/paths/> | while read mode type sha path; do
    git update-index --add --cacheinfo "$mode,$sha,$path"
done
TREE=$(git write-tree)
COMMIT=$(git commit-tree "$TREE" -p origin/main -F msg.txt)

# PROVE IT BEFORE PUSHING -- this must list your files and nothing else:
git diff --name-status origin/main "$COMMIT"

git push origin "$COMMIT:main"                     # NON-FORCE, on purpose
```

**Why each part matters**

- `GIT_INDEX_FILE` — the whole point. Your staging is invisible to other lanes and theirs to
  you. No lock contention, no cross-contamination, no `index.lock` race.
- **no checkout** — other lanes' working trees are untouched, and your own dirty files stay
  dirty and unstaged. Mine had 8 unrelated modified files throughout; none were swept in.
- `-p origin/main` — the commit is a fast-forward child of the real tip, so it needs no
  rebase and carries none of your branch's other history.
- `git diff --name-status origin/main "$COMMIT"` — **the check that makes it safe.** Read it
  before pushing. If anything appears that you did not intend, stop.
- **non-force push** — if `main` moved while you worked, the push *refuses*. That refusal is
  the feature. `--force-with-lease` would also have been wrong here: it permits the push when
  your *cached* remote ref matches, and the cache is exactly what cannot be trusted (§3).

**Measured tonight:** landed 12 files onto a `main` that was **85 commits ahead** of my
branch, with 8 unrelated files dirty in the same worktree, in one push, with zero conflict
and zero contact with the shared index.

---

## 2. `retmax` is not truncation — it is a BIASED SAMPLE, and it propagates silently

**⛔ Tell the search lane this directly:** it reports 31 rows as `≥` because `retmax=500` /
`pageSize=1000` bind. **A bound cap is being treated as "we saw at least N". That is only
true if the cap is unsorted.**

**The mechanism.** `esearch` returns at most `retmax` ids **and PubMed sorts newest-first**.
So the returned set is not "some of the matches" — it is *the most recent* matches. Any
quantity correlated with publication date is then measured on a systematically skewed slice.
For screening recall this is maximally hostile: the trials a systematic review includes are
*older* than the recency window, so they are exactly what the cap excludes.

- A cap that binds and is **unsorted** → a truncated sample. `≥` is honest.
- A cap that binds and is **sorted** → a **biased** sample. `≥` is *not* honest, and the
  direction of the bias is whatever the sort key is.

**MEASURED:** one query matched **23,864,443** records with 1,000 examined — **0.004%**. The
narrower AND form matched 843 with 200 examined.

**How it surfaced, and this is the transferable part:** an OR strategy scored **worse** than
its own AND sub-query. That is *logically impossible* — OR's result set contains AND's, so
its recall cannot be lower. **An impossibility needs no ground truth to interpret**, which
makes it the cheapest and strongest alarm available. It was the only reason the defect was
found, and the defect was **silently halving a headline**: `4.7% → 10.4%` after repair.

**Repair the failure mode, not the symptom.** Raising `retmax` would have failed again at a
larger corpus. The fix removed the result list entirely — ask membership per item
(`(<query>) AND <id>[UID]` → 1 or 0), which cannot be truncated or sorted. Cost O(items),
not O(corpus).

**Sweep instruction:** anywhere a cap can bind, record whether the endpoint sorts. If it
does, either remove the list (membership test) or state the bias direction — never `≥`.

---

## 3. `git ls-remote` is authoritative; `origin/main` is a cache

`git rev-parse origin/main` reads a **local remote-tracking ref**, last updated by your most
recent `fetch`/`clone`/`push`. It can be arbitrarily stale. `git ls-remote origin main` asks
the server.

**I got this wrong earlier tonight** — read the cached ref, concluded a push had failed, and
reported it as failed. It had succeeded. Two other lanes measured stale local state and drew
*corpus* conclusions from it.

**Rule:** any claim about what is on the remote — landed / not landed / ahead / behind —
must come from `git ls-remote`. Use the cached ref only after an explicit `fetch` in the same
command chain, and prefer `ls-remote` when the claim is going into a report.

Same shape as the `retmax` finding: **a local artefact standing in for the real population.**

---

## 4. A note on priors, since it cost us all night

Sixteen consecutive over-estimates make "too high" *feel* like the safe call. It is a reflex,
not a measurement — and I proved it by over-correcting: after ten optimistic misses I declared
1,750 cardiology reviews and measured 1,216, **44% high**, the error simply relocated.

The prior that finally held (**15%, band 6–35%, outcome 10.4%**) was reasoned from the
mechanism — a strict conjunctive query with no MeSH expansion, no synonyms, no field tags —
and explicitly *not* adjusted for the streak.

**Leaning against a bias relocates it. The fix is to keep declaring and keep scoring.**
