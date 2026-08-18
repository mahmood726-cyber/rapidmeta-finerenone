# Retractions

**Both claims below were relayed onward as findings. Both were wrong.** Written out in
full because the record is reader-facing in a way the code is not, and because an
unwritten correction is one that did not happen.

---

## 1. "852 of 852 V2 pages are empty templates"

Quoted as originally written, 2026-08-18:

> **852 OF 852 V2 PAGES ARE EMPTY TEMPLATES. Not "mostly". Every one.**

**The measurement was correct. The interpretation was wrong, in the alarming direction.**

`ARNI_HF_REVIEW.html` and `GEPOTIDACIN_URINARY_TRACT_AUTO_FULL_REVIEW.html` are **two
different kinds of artefact sharing a file extension**:

| | V1 — e.g. ARNI | V2 — e.g. Gepotidacin |
|---|---|---|
| values | **static text in the served bytes** | computed in-browser at runtime |
| state | none | `localStorage`, per visitor |
| trials | written in | seeded, then acquired in-browser |
| what it is | **a published review** | **an analysis application** |

**A blank V2 page is not a failed review. It is an un-run tool.** Counting 852 instances
of an application as delivery failures was a category error, and it produced a projector
written to patch values into something that recomputes them by design.

**What survives, and it is a real reader-facing problem:** 852 blank analysis tools sit on
the index alongside published reviews, **with nothing telling a reader which they are
about to open.**

---

## 2. "No object-to-page generator exists anywhere in this corpus"

Quoted as originally written:

> **NO SCRIPT IN THIS REPOSITORY READS `PAGE_MAP` AND WRITES A TOPIC PAGE.**

**The narrow claim is true. The conclusion drawn from it was false.** The generator stack
was present the whole time:

| file | what it is |
|---|---|
| `ssot/build_tabbed.py` | 897 lines. `argv[1]` = object, `argv[2]` = output page |
| `ssot/build_app_v2.py` | the flat control, emits the pre-tab layout byte-identically |
| `ssot/projectors.py` | 84 KB, 37 callables, imports cleanly |
| `ssot/projectors2.py`, `ssot/paper.py`, `ssot/make_docx.py` | further surfaces |

**It is keyed by object path, not by `PAGE_MAP`, and it lives in `ssot/` rather than
`scripts/`.** Four searches across four rounds missed it for that single reason.

**`scripts/project_topic_page.py`, written this week, is a reconstruction of a working
system.** It stays in the tree as a record of the error, not as a tool.

---

## What both retractions have in common

Each began with a correct measurement and an inference that ran past it. **"Every V2 page
is blank" was true; "therefore the corpus is undelivered" was not. "Nothing reads
`PAGE_MAP` and writes a page" was true; "therefore no generator exists" was not.**

The distance between the two, in both cases, was a category the measurement could not see.
