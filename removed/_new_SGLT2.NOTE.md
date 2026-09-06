# `_new_SGLT2.html` — relocated from the repo root, 2026-09-04

## What it is

A **draft of the k=4 harmonised SGLT2-HF page** — the analysis this project established is
correct at `HR 0.774 (0.724–0.828)` and could not publish only because DELIVER's harmonised
two-component input could not be sourced.

Its own `<title>` reads: *"SGLT2 inhibitors against placebo in chronic heart failure across
the ejection fraction spectrum: the four randomised outcome trials that report cardiovascular
death or a worsening heart failure event as a time-to-first hazard ratio."*

Content probes that identify it, and distinguish it from the served page:

| probe | this file | served `SGLT2_HF_REVIEW.html` |
|---|---|---|
| `0.7636` | 11 | 14 |
| `Contributing trials` | 8 | 3 |
| `152.7` / `156.7` / `160.4` | 0 / 0 / 0 | present |
| `20725` | 0 | 2 |
| bytes | 3,460,804 | 3,918,595 |

So it carries **none** of the served page's absolute-effect grid values or its `20725`
denominator, and it is a four-trial page where the served one is the k=3 / k=2 split with the
four-trial pool withdrawn. It is not a copy of anything currently published.

## Identity

```
original path : _new_SGLT2.html   (repo root, UNTRACKED)
destination   : removed/_new_SGLT2.html
sha256        : 025a9572ada303042af04fc36fcfd62241a03e0252172c9ed075ca5d5a60eb18
bytes         : 3,460,804
mtime         : 2026-09-03 21:29:09
```

Relocated by **copy → sha256 verified at the destination → original deleted**, never by move.
The hash above was equal at both ends before the original was removed.

## Authorship is UNESTABLISHED — neither claimed nor disclaimed

`_new_SGLT2.html` is a path **named** by the assistant lane while preparing a targeted
regeneration that was withdrawn before any build ran, and that lane has no record of executing
a build to it. It is not claiming authorship it cannot evidence, and it is not disclaiming it
conveniently. Mahmood was asked whether the file is his and has not answered.

**Treat authorship as open indefinitely. Silence is not a resolution.** Nothing here should be
read as establishing who made it.

## Why it was moved rather than left, and rather than deleted

Left in the repo root it was reported as *untracked, therefore harmless*. That was wrong:

> **UNTRACKED DEBRIS IS INVISIBLE TO GIT AND VISIBLE TO THE GATES. It is harmless to the
> published surface and it fails a gate for everyone on this tree.**

`gate14` (unanchored authority) scans the **working tree**, not the commit, and produced
**2 of its 9 findings** against this file. The gates' page population is the repo root only
(`pages() = os.listdir(REPO)` filtered to `*_REVIEW*.html` — and the root scan that caught this
one is broader still), so a subdirectory is out of scope while the root is not.

Deleting it was rejected: it is a draft of the one page we most want to be able to publish, and
its ownership is unresolved. `removed/` is this repository's existing, **tracked** convention for
withdrawn pages — 77 of them — and it is a subdirectory, so the file is preserved, versioned, and
out of the scanned root.

## What has NOT been done

- Nothing was verified about its analysis. The `HR 0.774` figure above is this project's own
  reproduction, not a claim about what this file computes.
- It is not published, not linked, and was never reachable: it returned **HTTP 404** at
  `https://mahmood726-cyber.github.io/rapidmeta-finerenone/_new_SGLT2.html` while it sat at the
  root, and it was never committed to `main`.
