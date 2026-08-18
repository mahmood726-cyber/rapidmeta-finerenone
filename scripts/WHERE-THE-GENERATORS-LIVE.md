# Executable code has TWO homes in this repository

**`scripts/`** — audits, gates, screens, triage. Things that **inspect**.

**`ssot/`** — the page generators. Things that **write**.

| file | what it is |
|---|---|
| `ssot/build_tabbed.py` | **the tabbed page builder.** `python ssot/build_tabbed.py <object.json> <out.html>` |
| `ssot/build_app_v2.py` | the **flat control** — emits the pre-tab layout byte-identically, and is what every A/B is measured against |
| `ssot/projectors.py` | 37 renderers: `forest_svg`, `funnel_svg`, `scatter_svg`, `rob_traffic_light_svg`, `prisma_flow_svg`, `visual_abstract_svg`, `verdict_card`, `readiness` |
| `ssot/projectors2.py` · `ssot/paper.py` · `ssot/make_docx.py` | further surfaces from the same objects |

## Why this file exists

**Four searches across four rounds of one week concluded that no page generator existed.**
Every one looked in `scripts/`, because that is where tools live. The generators are filed
with the data they project — defensible as cohesion, and invisible to anyone searching by
expectation.

**The rule that would have found it immediately: search by NAME from the artefact's own
record, before searching by LOCATION from your expectations.** Three of our own records
named it in plain text throughout:

- `STATUS.md` — *"built through the tabbed projector"*
- a CSS comment inside `ARNI_HF_REVIEW.html` — *"emitted per-tab in `projectors.py`"*
- that page's build stamp — the generating commit

**Nothing here should be moved.** Paths are referenced across the tree; a move would break
them. **This pointer is the fix.**
