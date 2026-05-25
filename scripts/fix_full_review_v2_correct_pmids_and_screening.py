"""v2 fix — applied on top of fix_full_review_python_isms_and_inject_pmids.py.

Two issues the v1 fix introduced or did not address:

  (A) Wrong abstracts. v1 injected PMIDs from AACT study_references whose type
      could be `BACKGROUND` (cited literature, not the trial's own publication).
      The trial's actual paper has type `RESULT` (and `DERIVED` is also OK —
      auto-derived from PubMed-NCT cross-link). 60k+ NCTs only have BACKGROUND
      entries, so v1 happily injected a citation-of-unrelated-paper PMID and
      AbstractHydrator then displayed that paper's abstract. **Fix**: rebuild
      nct_to_pmid.json from RESULT+DERIVED only, then:
        - wipe any PMID in a FULL_REVIEW that does NOT match the new map (it's
          either BACKGROUND-tainted or a manually-curated PMID — we keep
          curated ones because they only live in *_REVIEW.html, never in
          *_FULL_REVIEW.html which is auto-generated);
        - re-inject the correct PMID where the new map has a RESULT/DERIVED
          PMID for the NCT.

  (B) Screening tab CT.gov links broken. The render template at ScreenEngine
      uses `t.data?.ctgovUrl` to decide whether to wrap the NCT id in an
      anchor. But for trials that have NOT been auto-extracted yet (which is
      the default state when the user opens the Screening tab), `t.data` is
      either missing or has no `ctgovUrl`. Result: the NCT shows as plain text
      with no link. **Fix**: change the conditional to construct the URL from
      `t.id` when it matches `/^NCT\\d+$/`, which is always known and always
      valid.

Idempotent: re-running on already-v2-fixed files is a no-op.
"""
from __future__ import annotations
import json
import re
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
NCT_PMID = json.loads((HERE / "outputs" / "pmid_resolver" / "nct_to_pmid.json").read_text(encoding="utf-8"))

# Trial block boundary (same as v1).
TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)

# pmid: 'whatever' inside a trial block.
PMID_RE = re.compile(r"pmid:\s*(?P<q>['\"])(?P<val>\d*)(?P=q)")

# Screening render template — old vs new.
SCREEN_OLD = (
    "${t.data?.ctgovUrl ? `<a href=\"${escapeHtml(t.data.ctgovUrl)}\" target=\"_blank\" rel=\"noopener\" "
    "class=\"underline decoration-dotted hover:text-blue-400\" "
    "title=\"Open CT.gov record (verify extraction against source)\" "
    "onclick=\"event.stopPropagation();\">${escapeHtml(t.id.length > 20 ? t.id.slice(0, 20) + '...' : t.id)} ↗</a>` "
    ": escapeHtml(t.id.length > 20 ? t.id.slice(0, 20) + '...' : t.id)}"
)
SCREEN_NEW = (
    "${(function(){"
    "var u = t.data && t.data.ctgovUrl ? t.data.ctgovUrl : "
    "(typeof t.id === 'string' && /^NCT\\d{7,8}/.test(t.id) ? 'https://clinicaltrials.gov/study/' + t.id.match(/^NCT\\d{7,8}/)[0] : null);"
    "var label = escapeHtml(t.id && t.id.length > 20 ? t.id.slice(0, 20) + '...' : (t.id || ''));"
    "return u ? '<a href=\"' + escapeHtml(u) + '\" target=\"_blank\" rel=\"noopener\" "
    "class=\"underline decoration-dotted hover:text-blue-400\" "
    "title=\"Open CT.gov record (verify extraction against source)\" "
    "onclick=\"event.stopPropagation();\">' + label + ' ↗</a>' : label;"
    "})()}"
)


def fix_pmids_in_block(body: str, nct: str) -> tuple[str, int, int]:
    """Returns (new_body, replaced_count, wiped_count).

    Logic per `NCT`:
      - If map has correct PMID: ensure pmid:'<correct>'.
        - If current pmid matches: no-op.
        - If current pmid differs or is empty: replace.
      - If map has no PMID for this NCT: wipe to pmid:'' (don't show wrong abstract).
    """
    info = NCT_PMID.get(nct)
    correct = info["pmid"] if info else ""
    m = PMID_RE.search(body)
    if not m:
        return body, 0, 0
    current = m.group("val") or ""
    if current == correct:
        return body, 0, 0
    new = f"pmid: '{correct}'"
    new_body = PMID_RE.sub(new, body, count=1)
    return new_body, (1 if correct else 0), (1 if (current and not correct) else 0)


def fix_file(p: Path) -> dict:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt

    # --- Pass A: PMID re-injection (correct/wipe) ---
    replaced = wiped = trials = 0

    def _sub_trial(m: re.Match) -> str:
        nonlocal replaced, wiped, trials
        nct = m.group(1)
        body = m.group("body")
        trials += 1
        new_body, r, w = fix_pmids_in_block(body, nct)
        replaced += r
        wiped += w
        if new_body == body:
            return m.group(0)
        return f"'{nct}': {{{new_body}}}"

    txt = TRIAL_BLOCK_RE.sub(_sub_trial, txt)

    # --- Pass B: screening CT.gov link fallback ---
    screen_fix = 0
    if SCREEN_OLD in txt:
        txt = txt.replace(SCREEN_OLD, SCREEN_NEW)
        screen_fix = 1

    if txt != orig:
        p.write_text(txt, encoding="utf-8")
    return {
        "trials": trials,
        "pmid_replaced": replaced,
        "pmid_wiped": wiped,
        "screen_fix": screen_fix,
    }


def main():
    targets = sorted(p for p in HERE.glob("*_FULL_REVIEW.html") if p.is_file())
    print(f"Targets: {len(targets):,} FULL_REVIEW files")
    totals = {"trials": 0, "pmid_replaced": 0, "pmid_wiped": 0, "screen_fix": 0, "changed": 0}
    for i, p in enumerate(targets, 1):
        before = p.read_text(encoding="utf-8", errors="replace")
        s = fix_file(p)
        after = p.read_text(encoding="utf-8", errors="replace")
        if before != after:
            totals["changed"] += 1
        for k in ("trials", "pmid_replaced", "pmid_wiped", "screen_fix"):
            totals[k] += s[k]
        if i <= 5 or i % 200 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}: trials={s['trials']} pmid_repl={s['pmid_replaced']} pmid_wipe={s['pmid_wiped']} screen={s['screen_fix']}")
    print()
    print(f"Files touched              : {totals['changed']:,}")
    print(f"Trial blocks scanned       : {totals['trials']:,}")
    print(f"PMIDs re-injected (correct): {totals['pmid_replaced']:,}")
    print(f"PMIDs wiped (was wrong)    : {totals['pmid_wiped']:,}")
    print(f"Screening fallbacks patched: {totals['screen_fix']:,}")


if __name__ == "__main__":
    main()
