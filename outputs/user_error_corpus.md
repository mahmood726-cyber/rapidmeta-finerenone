# User-caught error corpus (RapidMeta)

Assembled from every artifact we can evidence. **Counted, not assumed.**

- **Attributed user reports (a human read the source and told us): 1**
- **Machine-surfaced by that report (the 1→128 cascade): 128**
- **Total labelled rows: 129**

## Flag-recall on user-caught errors (the metric that decides the project)
- Of the 1 attributed user-caught error(s), our gates had already flagged: **0/1**.
- **n=1 is far too thin to be a real flag-recall number — say so.** The one evidenced case, our gate did NOT catch (it silently skipped blank 0/0 cells and used the HR). That is a **missing gate**, now added (see scripts/build_gate.py blank_counts_with_effect).

## Error classes

- blank/zero 2x2 count cells (N>=30): 68
- no effect + blank counts (under-extraction): 42
- real effect (HR) + blank binary counts: 18
- blank/missing 2x2 count cells: 1

## The honest headline
"Tons of user-reported errors" is **NOT evidenced in artifacts** beyond ONE attributed report — because **zero apps have an error-reporting mechanism**, so reports arrived out-of-band (email/verbal to the owner) and were never captured. The ONE evidenced report DID demonstrate the loop (it cascaded to 128 defects, 5 fixed immediately) — so the mechanism is real, but the **volume is unmeasured**. Fix: the in-app "Report an error" capture (scripts/add_error_report_button.py) so every future report becomes a counted, labelled corpus row.