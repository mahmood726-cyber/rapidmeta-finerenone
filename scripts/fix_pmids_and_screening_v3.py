"""v3 — single, correctness-focused pass.

The user reported two screening-tab regressions on top of the v1/v2 fixes:
  (a) CT.gov links broken in screening
  (b) Wrong abstracts shown for some trials

This script:

  1. Rebuilds and uses an AACT-verified NCT->PMID map (built upstream in
     outputs/pmid_resolver/nct_to_pmid.json) where the picking rule is
     `min(int(pmid))` over {RESULT, DERIVED} entries — i.e. prefer the oldest
     RESULT/DERIVED reference per NCT, which is overwhelmingly the trial's
     original primary publication. BACKGROUND entries are excluded because
     they're sponsor-cited foundational literature, NOT the trial's paper.
     Concrete examples this fixes:
        NCT01860976 (ASTRAEA, abatacept PsA): lite hardcoded extension paper
          31245054; correct primary is 28473423 (Mease 2017).
        NCT01001494 (ACCORD I, aclidinium COPD): lite hardcoded 28074135;
          correct primary is 22441743 (Jones 2012).

  2. For each FULL_REVIEW + AUTO_2_FULL_REVIEW + REVIEW_FULL_REVIEW file:
     a. Replace every trial-block pmid with the AACT-verified one (or wipe to
        '' if no AACT pub is known — better than wrong-abstract).
     b. Patch the ScreenEngine render template so the NCT id always links to
        CT.gov via a runtime URL fallback, even before extraction has populated
        `t.data.ctgovUrl`.

  3. For each *_AUTO_REVIEW.html (lite audit-first) file:
     a. Replace embedded `PMID <n>` hardcoded link text + href with the AACT
        primary PMID — fixes both the link target AND the abstract that the
        client-side hydrator (added in upgrade_auto_review_lite.py) will fetch.
     b. Refresh the embedded NCT_PMID JSON island so the hydrator uses the
        new, correct PMIDs.

Idempotent. Safe to re-run.
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
NCT_RE = re.compile(r"NCT\d{7,8}")

# -----------------------------------------------------------------------------
# FULL_REVIEW (and AUTO_2_FULL_REVIEW + REVIEW_FULL_REVIEW)
# -----------------------------------------------------------------------------
TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)
PMID_RE = re.compile(r"pmid:\s*(?P<q>['\"])(?P<val>\d*)(?P=q)")

# Screening render template — v2-patched form (the form we previously installed).
SCREEN_OLD_V1 = (
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


def fix_pmid_in_block(body: str, nct: str) -> tuple[str, bool, bool]:
    """Return (new_body, replaced_with_correct, wiped_because_unknown)."""
    info = NCT_PMID.get(nct)
    correct = info["pmid"] if info else ""
    m = PMID_RE.search(body)
    if not m:
        return body, False, False
    current = m.group("val") or ""
    if current == correct:
        return body, False, False
    new_body = PMID_RE.sub(f"pmid: '{correct}'", body, count=1)
    return new_body, (correct != ""), (correct == "" and current != "")


def patch_full_review(p: Path) -> dict:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt
    n_replaced = n_wiped = n_trials = 0

    def _sub_trial(m: re.Match) -> str:
        nonlocal n_replaced, n_wiped, n_trials
        nct = m.group(1)
        body = m.group("body")
        n_trials += 1
        new_body, repl, wipe = fix_pmid_in_block(body, nct)
        if repl:
            n_replaced += 1
        if wipe:
            n_wiped += 1
        if new_body == body:
            return m.group(0)
        return f"'{nct}': {{{new_body}}}"

    txt = TRIAL_BLOCK_RE.sub(_sub_trial, txt)

    screen_fix = 0
    if SCREEN_OLD_V1 in txt:
        txt = txt.replace(SCREEN_OLD_V1, SCREEN_NEW)
        screen_fix = 1

    if txt != orig:
        p.write_text(txt, encoding="utf-8")
    return {
        "trials": n_trials,
        "pmid_replaced": n_replaced,
        "pmid_wiped": n_wiped,
        "screen_fix": screen_fix,
    }


# -----------------------------------------------------------------------------
# AUTO_REVIEW lite — patch embedded PMID link
# -----------------------------------------------------------------------------
# Pattern: NCT-anchor followed by " · " and a PMID anchor. We replace just the
# PMID anchor and its label. NCT is the key for the lookup.
LITE_PMID_LINK_RE = re.compile(
    r'(<a href="https://clinicaltrials\.gov/study/(NCT\d{7,8})"[^>]*>NCT\d{7,8}</a>\s*·\s*)'
    r'<a href="https://pubmed\.ncbi\.nlm\.nih\.gov/\d+/"[^>]*>PMID \d+</a>'
)
LITE_NO_PMID_LINK_RE = re.compile(
    r'(<a href="https://clinicaltrials\.gov/study/(NCT\d{7,8})"[^>]*>NCT\d{7,8}</a>)'
    r'(\s*·\s*\d{4}|\s*</span>)'
)


def patch_lite(p: Path) -> dict:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt
    n_link_fix = n_link_add = n_link_wipe = 0

    # Replace existing pmid links with AACT-verified pmid.
    def _sub_existing(m: re.Match) -> str:
        nonlocal n_link_fix, n_link_wipe
        nct = m.group(2)
        info = NCT_PMID.get(nct)
        if not info:
            n_link_wipe += 1
            # Strip the pmid anchor entirely, leaving the NCT and surrounding
            # " · " separator from the prefix group (re-render the prefix without
            # the trailing dot since we have no PMID to display).
            return m.group(1).rstrip("· \t\n")
        n_link_fix += 1
        return (
            m.group(1)
            + f'<a href="https://pubmed.ncbi.nlm.nih.gov/{info["pmid"]}/" target="_blank">PMID {info["pmid"]}</a>'
        )

    txt = LITE_PMID_LINK_RE.sub(_sub_existing, txt)

    # For NCT links that DIDN'T have a PMID link (lite page never had one
    # because topic_doc.json had no pmid), add one now if AACT knows it. We
    # match the form `NCT...</a>{...}` where the content after `</a>` is a
    # " · YYYY" or `</span>` boundary. Insert the PMID link before that.
    def _sub_missing(m: re.Match) -> str:
        nonlocal n_link_add
        nct_anchor = m.group(1)
        nct = m.group(2)
        rest = m.group(3)
        info = NCT_PMID.get(nct)
        if not info:
            return m.group(0)
        n_link_add += 1
        return (
            nct_anchor
            + f' · <a href="https://pubmed.ncbi.nlm.nih.gov/{info["pmid"]}/" target="_blank">PMID {info["pmid"]}</a>'
            + rest
        )

    txt = LITE_NO_PMID_LINK_RE.sub(_sub_missing, txt)

    # Refresh the embedded NCT_PMID JSON island so the abstract hydrator uses
    # the corrected PMIDs.
    ncts = sorted(set(NCT_RE.findall(txt)))
    local_map = {n: NCT_PMID[n] for n in ncts if n in NCT_PMID}
    if "rapidmeta-abstract-hydrator" in txt and local_map:
        # Find and replace the var NCT_PMID = {...}; line.
        nct_var_re = re.compile(
            r"(<!-- rapidmeta-abstract-hydrator:begin -->[\s\S]*?var NCT_PMID = )"
            r"(\{[^;]*\});",
            re.MULTILINE,
        )
        new_json = json.dumps(local_map, separators=(",", ":"))
        # Use a lambda to avoid backref interpretation in the replacement string.
        txt = nct_var_re.sub(lambda mm: mm.group(1) + new_json + ";", txt, count=1)

    if txt != orig:
        p.write_text(txt, encoding="utf-8")
    return {
        "link_fixed": n_link_fix,
        "link_added": n_link_add,
        "link_wiped": n_link_wipe,
    }


# -----------------------------------------------------------------------------
def main():
    full_targets = sorted(p for p in HERE.glob("*_FULL_REVIEW.html") if p.is_file())
    print(f"=== FULL_REVIEW pass ({len(full_targets):,} files) ===")
    f_totals = {"trials": 0, "pmid_replaced": 0, "pmid_wiped": 0, "screen_fix": 0, "changed": 0}
    for i, p in enumerate(full_targets, 1):
        before = p.read_text(encoding="utf-8", errors="replace")
        s = patch_full_review(p)
        if p.read_text(encoding="utf-8", errors="replace") != before:
            f_totals["changed"] += 1
        for k in ("trials", "pmid_replaced", "pmid_wiped", "screen_fix"):
            f_totals[k] += s[k]
        if i % 200 == 0:
            print(f"  [{i}/{len(full_targets)}] {p.name}")
    print(
        f"  FULL: touched={f_totals['changed']:,} trials={f_totals['trials']:,} "
        f"pmid_replaced={f_totals['pmid_replaced']:,} pmid_wiped={f_totals['pmid_wiped']:,} "
        f"screen_fix={f_totals['screen_fix']:,}"
    )

    lite_targets = sorted(HERE.glob("*_AUTO_REVIEW.html"))
    # Filter out anything that's actually a FULL_REVIEW.
    lite_targets = [p for p in lite_targets if "_FULL_REVIEW" not in p.name]
    print(f"\n=== AUTO_REVIEW lite pass ({len(lite_targets):,} files) ===")
    l_totals = {"link_fixed": 0, "link_added": 0, "link_wiped": 0, "changed": 0}
    for i, p in enumerate(lite_targets, 1):
        before = p.read_text(encoding="utf-8", errors="replace")
        s = patch_lite(p)
        if p.read_text(encoding="utf-8", errors="replace") != before:
            l_totals["changed"] += 1
        for k in ("link_fixed", "link_added", "link_wiped"):
            l_totals[k] += s[k]
        if i % 150 == 0:
            print(f"  [{i}/{len(lite_targets)}] {p.name}")
    print(
        f"  LITE: touched={l_totals['changed']:,} link_fixed={l_totals['link_fixed']:,} "
        f"link_added={l_totals['link_added']:,} link_wiped={l_totals['link_wiped']:,}"
    )


if __name__ == "__main__":
    main()
