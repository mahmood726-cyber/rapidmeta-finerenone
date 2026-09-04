# Deliberate store/page divergence, opened 2026-09-04 by commit `553c1193`

**A future sweep will find this and report it as `CODE-FIXED, CORPUS-STALE`. It will be right
about the shape and wrong about the cause.** This file exists so the finding resolves to a
decision instead of to a defect.

## What diverges

18 store objects now carry `search.retrieval_remainder` — how many records each search
returned and never retrieved — and **the pages built from them do not render it.**

```
ablation-af-heart-failure          apixaban-vte-prophylaxis     bosentan-pah-combination
ablation-af-medical-therapy        apixaban-vte-treatment       bosentan-pah-monotherapy
alirocumab-lipid                   arni-hfref                   bosentan-ph-not-group1
attr-cm-review                     bempedoic-acid-review        colchicine-cvd-coronary
azilsartan-chlorthalidone-vs-      bococizumab-lipid-review     early-rhythm-control-af
  olmesartan-hctz                  bosentan-pah-children        iv-iron-hf
                                                                sglt2-hf
```

The sharpest instance: `SGLT2_HF_REVIEW.html` still renders **"unscreened remainder 0."** and
still contains `1402` **zero times**, while `ssot/sglt2-hf/sglt2-hf.json` now holds
`retrieval_remainder: {state: PROVED, total: 1402}`.

## Why it was opened deliberately

Regenerating a page is not a side effect of correcting a store object. It requires the
before/after protocol — served sha256, rendered `k`, **every retraction and protected refusal
enumerated by string and re-asserted after** — and doing 18 of those inside a commit whose
subject was the arithmetic would have buried the one that mattered.

> **A divergence you have written down is a decision. The same divergence you have not is the
> defect this project has spent a week cataloguing.**

## What closes it

Per object, in this order:

1. record served `sha256`, rendered `k`, and enumerate by string every retraction, withdrawal
   and protected refusal the page carries
2. `python ssot/build_tabbed.py ssot/<app>/<app>.json <PAGE>.html`
3. assert the new `retrieval_remainder` renders; assert **every enumerated retraction is still
   present**; assert the page is non-empty and plausibly sized
4. fetch from the public URL and compare `sha256`
5. **if any retraction is missing, revert and report**

Until step 5 passes for an object, that object's page is stale **on this field only**. No
other field was touched: `k_unscreened_remainder`, `gap_stated_plainly`, every pooled estimate
and every trial record are byte-identical to what they were before `553c1193`.

## How to check this file is still true

```bash
python - <<'EOF'
import json, re, io
from pathlib import Path
pm = json.load(open("ssot/PAGE_MAP.json", encoding="utf-8"))
stale = []
for page, rel in sorted(pm.items()):
    p = Path(rel)
    if not p.exists():
        continue
    obj = json.loads(p.read_text(encoding="utf-8"))
    blk = (obj.get("search") or {}).get("retrieval_remainder")
    if not blk:
        continue
    html = Path(page)
    if html.exists() and "retrieval_remainder" not in html.read_text(
            encoding="utf-8", errors="replace"):
        stale.append(page)
print(len(stale), "page(s) still stale on this field:", stale[:5])
EOF
```

**When that prints `0`, delete this file.** A divergence record outliving its divergence is
itself a stale artefact.
