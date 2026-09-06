# The two build paths

**Written 2026-09-04 because they had never been named anywhere, and two separate errors were
invisible for exactly that reason.** A number about "the corpus" is meaningless until it says
which of these it was measured on. Both errors below were caught only at the end of a night's
work, and neither survives this page existing.

---

## PATH A — autodiscovery

```
scripts/add_topic_autodiscover.py
    TOPICS list (hand-written drug + condition patterns)
        -> find_ncts()  scans an AACT snapshot
        -> outputs/new_topics/<STEM>.json      (n_total, n_pass_all, verdict, enumeration ledger)
        -> clone / generate                    -> *_AUTO_*_REVIEW.html
```

- The trial set is **discovered by search** over a local AACT snapshot.
- What is hand-written is the **question**: 2,229 TOPICS entries under 1,893 distinct stems.
- Carries the enumeration ledger (`retrieved / identity_rejected / dropped_condition /
  dropped_study_type / eligible / cap_applied / discarded_by_cap`).
- The `MAX_PER_TOPIC` bound lives here and nowhere else.

## PATH B — the store objects

```
ssot/PAGE_MAP.json          163 page entries -> 152 distinct objects
    ssot/<app_id>/<app_id>.json      hand-curated, or converted from an existing page
        -> ssot/build_tabbed.py <object.json> <out.html>    -> <PAGE>.html
```

- `find_ncts` **never runs**. `grep "sglt2-hf" scripts/add_topic_autodiscover.py` → `0`.
- The trial set is **hand-authored**, or scraped back out of a page that already had it by
  `scripts/extract_to_ssot.py` — whose own docstring says it recovered no search *"because
  none of those are in the page it read"*.
- 20 of 163 page entries have an executed search; **143 do not**.
- Every page reviewed during the week of 2026-09-01 — `SGLT2_HF`, `TIGECYCLINE_CIAI`,
  `ARNI_HF`, the HFrEF NMA — is Path B.

---

## The two errors this page exists to prevent

**A fix measured on the wrong population** *(Class 99a)*. The `MAX_PER_TOPIC` cap was raised,
measured at `368 → 1,805` across 53 topics, and reported upward as the fix for pages that are
**all Path B**. Raising the cap cannot move them and never could.

**A brief written from the wrong population** *(Class 99g)*. The figure that opened the lane —
`398 trials across 135 topics` — is a **Path-B** number (Path B measures `393 / 152`), and the
entire lane ran on **Path A**.

> **Before quoting a number about "the corpus", say which path it was measured on. If you
> cannot, you do not yet have the number.**

## Which path is a given page on?

```bash
python - <<'EOF'
import json
pm = json.load(open("ssot/PAGE_MAP.json", encoding="utf-8"))
page = "SGLT2_HF_REVIEW.html"
print("PATH B ->", pm[page]) if page in pm else print("not in PAGE_MAP; likely PATH A")
EOF
```

A page in `ssot/PAGE_MAP.json` is Path B. A page matching `*_AUTO_*_REVIEW.html` with a record
under `outputs/new_topics/` is Path A. **Some pages are neither**, and that is a third
population nobody has counted — `VENETOCLAX_CLL_REVIEW.html` is one: not in `PAGE_MAP`, and
its `*_AUTO` sibling is a different topic. **Counting them is an open lead.**

## Open lead — the third population

`PAGE_MAP` holds 163 entries over 152 objects. `outputs/new_topics/` holds 66 tracked records.
The delivered corpus is **~1,427** `*_REVIEW*.html` pages. **The remainder is unattributed to
either path and has never been enumerated.** Any statement of the form "the corpus has N
pages" is a reach figure until it is.
