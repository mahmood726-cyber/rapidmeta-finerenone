"""Recompute the data-integrity bands shown in audit_table.html and index.html.

Original bands (per outputs/extraction_audit/FINAL_INTEGRITY_REPORT_V2.md) were
a composite of 7 sub-scores including `P_null_pmid` (proportion of trials with
null PMID) and `N_nulled_nct`. Since our session injected verified PMIDs into
every shippable trial, recomputing matters: the static counts in the page
header still reflect pre-fix state.

Pragmatic re-banding rule (matches the spirit of the original methodology
while being computable from the current files alone):

  QUARANTINE   any unresolved git merge marker, OR Plotly title injection
               (page would page-error on load)
  MANUAL_REVIEW   >50% of trial blocks have empty pmid:'' after our fix
                  (means no AACT primary publication available — out of our
                  control without per-paper sourcing)
  LOW_CONCERN  any single trial with tE>tN/cE>cN OR empty pmid:'' OR
               unrecoverable null tE/cE
  OK           clean on all the above

This re-bands every *_REVIEW.html in the repo, updates the
`<tr data-band=...>` attribute in audit_table.html, recomputes the four
summary-card totals, and writes a small JSON the index banner's loader can
fetch for the live-counter widget.
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path
from collections import Counter

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)
PMID_RE = re.compile(r"pmid:\s*['\"](\d*)['\"]")
PLOTLY_BAD = '${escapeHtml(document.title || "RapidMeta'
CONFLICT_RE = re.compile(r"^(<<<<<<< |=======$|>>>>>>> )", re.MULTILINE)


def classify(p: Path) -> tuple[str, dict]:
    txt = p.read_text(encoding="utf-8", errors="replace")
    notes: dict[str, int] = {}

    if PLOTLY_BAD in txt:
        return "QUARANTINE", {"reason": "plotly_title_injection"}
    if CONFLICT_RE.search(txt):
        return "QUARANTINE", {"reason": "merge_conflict"}

    trials = list(TRIAL_BLOCK_RE.finditer(txt))
    if not trials:
        return "OK", {"trials": 0}

    n_trials = len(trials)
    n_empty_pmid = 0
    n_impossible = 0
    n_missing_effect = 0
    for m in trials:
        body = m.group("body")
        pm = PMID_RE.search(body)
        if pm and pm.group(1) == "":
            n_empty_pmid += 1

        def get(field):
            mm = re.search(rf"\b{field}:\s*(-?[\d.eE+-]+|null|None)", body)
            v = mm.group(1) if mm else None
            if v is None or v in ("null", "None"):
                return None
            try:
                return float(v) if "." in v or "e" in v.lower() else int(v)
            except ValueError:
                return None

        tE, tN, cE, cN = get("tE"), get("tN"), get("cE"), get("cN")
        pub_hr = get("publishedHR")
        # Has analyzable data if EITHER (a) binary counts present with tE<=tN
        # and cE<=cN, OR (b) a non-null publishedHR (MD/HR/OR/RR/RD continuous
        # effect from outcome_analyses or per-arm Mean+SD).
        has_counts = (
            tE is not None and cE is not None
            and tN is not None and cN is not None
            and tN > 0 and cN > 0
        )
        has_pub_effect = pub_hr is not None
        if not has_counts and not has_pub_effect:
            n_missing_effect += 1
        if tE is not None and tN is not None and tE > tN:
            n_impossible += 1
        if cE is not None and cN is not None and cE > cN:
            n_impossible += 1

    pct_empty = n_empty_pmid / n_trials if n_trials else 0
    pct_missing_effect = n_missing_effect / n_trials if n_trials else 0
    notes = {
        "trials": n_trials,
        "empty_pmid": n_empty_pmid,
        "missing_effect": n_missing_effect,
        "impossible": n_impossible,
    }
    if n_impossible:
        return "QUARANTINE", notes  # should never happen post-fix
    if pct_missing_effect > 0.5 or pct_empty > 0.5:
        return "MANUAL_REVIEW", notes
    if n_missing_effect or n_empty_pmid:
        return "LOW_CONCERN", notes
    return "OK", notes


def main():
    targets = sorted(p for p in HERE.glob("*_REVIEW.html") if p.is_file())
    print(f"Recomputing bands for {len(targets):,} REVIEW pages...")
    bands: dict[str, dict] = {}
    counter: Counter = Counter()
    for p in targets:
        band, notes = classify(p)
        bands[p.name] = {"band": band, **notes}
        counter[band] += 1

    print("Distribution:")
    for k in ("OK", "LOW_CONCERN", "MANUAL_REVIEW", "QUARANTINE"):
        print(f"  {k:<14}: {counter[k]:,}")

    # 1. Persist JSON for any live consumer.
    out_path = HERE / "outputs" / "audit40" / "bands_recomputed.json"
    out_path.write_text(json.dumps({
        "total": len(targets),
        "by_band": dict(counter),
        "per_file": bands,
    }, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")

    # 2. Update audit_table.html
    at = HERE / "audit_table.html"
    txt = at.read_text(encoding="utf-8", errors="replace")
    # 2a. Update data-band attrs per row.
    n_attr = 0
    for fname, info in bands.items():
        # Row marker is `data-band="..." data-name="<stem-lower>"`
        stem = re.sub(r"\.html$", "", fname).lower()
        # Replace data-band on the SINGLE matching row.
        # Be conservative — exact `data-name="<stem>"` substring must match.
        old_re = re.compile(
            rf'(<tr\s+)data-band="[^"]+"(\s+data-name="{re.escape(stem)}")'
        )
        new_txt, n = old_re.subn(
            rf'\1data-band="{info["band"]}"\2', txt, count=1
        )
        if n:
            txt = new_txt
            n_attr += 1
    print(f"  audit_table.html: rebanded {n_attr} rows")

    # 2b. Update the four summary-card counts.
    card_re = re.compile(
        r'(border-left:3px solid #16a34a;[^<]*<div class="num">)\d+(</div>[^<]*<div class="label">Trustworthy</div>)'
    )
    txt = card_re.sub(lambda m: m.group(1) + str(counter["OK"]) + m.group(2), txt, count=1)
    card_re = re.compile(
        r'(border-left:3px solid #ca8a04;[^<]*<div class="num">)\d+(</div>[^<]*<div class="label">Low concern</div>)'
    )
    txt = card_re.sub(lambda m: m.group(1) + str(counter["LOW_CONCERN"]) + m.group(2), txt, count=1)
    card_re = re.compile(
        r'(border-left:3px solid #ea580c;[^<]*<div class="num">)\d+(</div>[^<]*<div class="label">Manual review</div>)'
    )
    txt = card_re.sub(lambda m: m.group(1) + str(counter["MANUAL_REVIEW"]) + m.group(2), txt, count=1)
    card_re = re.compile(
        r'(border-left:3px solid #7f1d1d;[^<]*<div class="num">)\d+(</div>[^<]*<div class="label">Quarantined</div>)'
    )
    txt = card_re.sub(lambda m: m.group(1) + str(counter["QUARANTINE"]) + m.group(2), txt, count=1)

    at.write_text(txt, encoding="utf-8")
    print(f"  audit_table.html: summary cards updated")

    # 3. Update index.html banner counters (replace the `…` placeholder).
    ip = HERE / "index.html"
    txt = ip.read_text(encoding="utf-8", errors="replace")
    for key, css_id in (
        ("OK", "ib-ok"),
        ("LOW_CONCERN", "ib-low"),
        ("MANUAL_REVIEW", "ib-manual"),
        ("QUARANTINE", "ib-quar"),
    ):
        txt = re.sub(
            rf'(<strong id="{css_id}">)[^<]*(</strong>)',
            rf'\g<1>{counter[key]:,}\g<2>',
            txt,
            count=1,
        )
    ip.write_text(txt, encoding="utf-8")
    print(f"  index.html: banner counters set to {dict(counter)}")


if __name__ == "__main__":
    main()
