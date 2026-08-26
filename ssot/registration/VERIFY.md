# Verifying a registration anchor

Reviews in this repository are registered by committing their protocol to this
public repository **before the search runs**, and anchoring both ends in
[Rekor](https://rekor.sigstore.dev), the public Sigstore transparency log.

This file is the recipe for checking that yourself. It needs no cooperation from
us and no account anywhere.

---

## What the anchor establishes, and what it does not

**Establishes.** The protocol text existed **no later than** the log's
`integratedTime`. That time is set by the transparency log, not by us, and the
log is append-only and publicly auditable. It also establishes that whoever holds
the key below signed exactly those bytes.

**Does not establish.** It does not prove when the commit was made — git author
and committer dates are supplied by whoever makes the commit and can be set to
any value, and commits here are unsigned. It does not prove that no earlier or
parallel version of the protocol existed elsewhere. It does not prove the data
had not already been seen, and it says nothing about the independence of the
people who wrote it.

**The limitation a referee is entitled to know:** *the log time is independent of
us; the key custody is not.* The private half of the signing key is held by this
project and is deliberately **not** in this repository. A stranger can verify that
the text existed by the log time and that we signed it. A stranger cannot verify
that we did not hold an earlier version of the same text. That is weaker than a
notary and considerably stronger than a git timestamp, and the difference is
stated here rather than left to be discovered.

---

## The signing key

Public half: [`rekor-signing-key.pub.pem`](./rekor-signing-key.pub.pem) — ECDSA
P-256. The private half never enters this repository, is not published, and is
held by the project.

---

## The recipe

For any anchored artefact you need three things, all recorded in the review's own
search record under `registration.anchor`: the **commit** the bytes live at, the
**path**, and the Rekor **uuid** (or `logIndex`).

**1 — Fetch the log entry.**

```
curl -s https://rekor.sigstore.dev/api/v1/log/entries/<uuid>
```

Read `integratedTime` (Unix seconds — that is the third-party time) and
base64-decode `body` to get `spec.data.hash.value`, the sha256 the log holds.

**2 — Hash the file at that commit.** Not the file at `main`; the file at the
commit named in the record, because `main` moves.

```
git show <commit>:<path> | sha256sum
```

**3 — Compare.** The two hashes must be identical. If they are, the bytes you can
read at that commit are the bytes that were in the log at `integratedTime`.

**4 — Check the ordering.** The search record's `ordering` block carries
`protocol_anchored_utc` and the query times. Every query time must fall **after**
the protocol's `integratedTime` and **before** the search record's. Two
third-party times bracketing the operation is the whole claim.

Note the ordering test uses the **earliest** query time, including a failed
attempt, not the first successful one — reporting only the success would move the
first-query time later and flatter the claim.

---

## Worked example — `finerenone-cv`, the first prospectively anchored search here

```
protocol commit        3872817c06c92bad152cc4d076ea23b2f611012c
protocol path          ssot/finerenone-cv/PROTOCOL.md
protocol sha256        7220ad588145ee338f936a6799fea6766d4b467f04994dd2198f2ea759fb2633
protocol Rekor         logIndex 2604694652   integratedTime 2026-08-26T17:59:41Z

first query ATTEMPT    2026-08-26T18:00:30.227Z
first query executed   2026-08-26T18:00:48.163Z

search record commit   fe926bf4f25e4c72a6535bdabc0eab75d4373119
search record path     ssot/finerenone-cv/SEARCH-RECORD.json
search record sha256   ec452d245ebf2a79602d14de321a77be1c6fefd2d58af0ef0f41579520ed9d9e
search record Rekor    logIndex 2604754261   integratedTime 2026-08-26T18:04:45Z
```

The bracket: `17:59:41Z  <  every query  <  18:04:45Z`, both bounds set by the
log rather than by us.

---

## Why not PROSPERO, and why not a git timestamp alone

A PROSPERO entry can be edited and its history is not public in the same way. A
git timestamp is author-supplied and forgeable — a commit made at
`2026-08-26T14:58:55Z` can be produced reporting `2019-01-01T00:00:00Z`, and
GitHub stores and displays what it is given. An earlier version of this project's
protocol standard claimed the commit timestamp was "set by the repository and not
by the authors". That was false and was corrected by amendment rather than edited
out.

The transparency log is what replaces that false claim with a true and narrower
one.
