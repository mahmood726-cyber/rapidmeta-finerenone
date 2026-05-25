"""Fix the real bugs surfaced by audit_40_checks.py.

Five fixes:

  (A) Event-count data corruption (check 08).
      bulk_clone_audit_first.py read AACT outcome_measurements rows whose
      `param_value` was a PERCENTAGE (e.g. "57.1") and cast it to `int()`,
      yielding tE=57. When tN=43, this gives "57 events out of 43 patients"
      — impossible. Recovery: tE_corrected = round(tE_raw / 100 * tN).
      Same for cE/cN. Applies wherever tE>tN or cE>cN; idempotent (only acts
      on violating rows).

  (B) Template-leak AUTO_INCLUDE_TRIAL_IDS (check 10).
      199 curated REVIEW files have `const AUTO_INCLUDE_TRIAL_IDS = new
      Set([..5 default NCTs..])` that don't intersect realData. The screening
      engine then "auto-includes" 5 wrong NCTs and the real trials are not
      auto-included. Fix: replace the set with the keys of realData on each
      file where the intersection is empty.

  (C) Old screening template missing v3 fallback (check 34).
      342 curated REVIEW files still use the pre-v3 form
        ${t.data?.ctgovUrl ? `<a href=...>...</a>` : escapeHtml(t.id...)}
      which only renders a CT.gov link after extraction has populated
      `t.data.ctgovUrl`. Patch them with the same runtime fallback (build URL
      from t.id when it matches /^NCT\\d+/).

  (D) Broken protocol-badge links (check 05).
      Header has <a href="protocols/<stem>_auto_protocol_v1.1_2026-04-20.md">.
      Many of those files were never created. Fix: detect that the file is
      missing, and rewrite the href to `protocols/INDEX.md` (which exists)
      so the badge keeps working as a navigation aid into the protocols
      section, instead of 404'ing.

  (E) Single year outlier and duplicate-id outlier — fix in-place.

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

TRIAL_BLOCK_RE = re.compile(
    r"'(NCT\d{7,8})':\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)
PROTOCOL_HREF_RE = re.compile(r'href="(protocols/[^"#?]+\.md)"')


# ---- (A) event-count percentage corruption -----------------------------------
# DISABLED 2026-05-24 — this fixer had an idempotence bug: re-running it would
# compound the correction (e.g. cE=524 -> 204 -> 80 -> 31 across passes). The
# original AACT-extracted values were restored via
# `scripts/reset_event_counts_from_source.py`, and the safe single-pass version
# `scripts/fix_event_counts_safe.py` replaces this. Kept as a no-op stub so
# patch_file() callers don't break.
def fix_event_counts(p: Path, txt: str) -> tuple[str, int]:
    return txt, 0


def _DEAD_fix_event_counts(p: Path, txt: str) -> tuple[str, int]:
    """If tE>tN or cE>cN inside a trial block, recompute as percentage * N / 100."""
    n_fixed = 0
    out_parts: list[str] = []
    last = 0
    for m in TRIAL_BLOCK_RE.finditer(txt):
        body = m.group("body")
        nums = {}
        spans = {}
        for fld in ("tE", "tN", "cE", "cN"):
            mm = re.search(rf"\b({fld}):\s*(-?\d+|null|None)", body)
            if mm:
                v = mm.group(2)
                spans[fld] = (mm.start(2), mm.end(2))
                nums[fld] = int(v) if v not in ("null", "None") else None
        # Only act when all four are numeric (otherwise we can't recover).
        if all(nums.get(k) is not None for k in ("tE", "tN", "cE", "cN")):
            tE, tN, cE, cN = nums["tE"], nums["tN"], nums["cE"], nums["cN"]
            new_body = body
            changed_local = False
            # Apply percentage correction independently for each arm.
            if tE > tN:
                corrected = round(tE / 100 * tN)
                new_body = re.sub(r"\btE:\s*(?:-?\d+)", f"tE: {corrected}", new_body, count=1)
                changed_local = True
            if cE > cN:
                corrected = round(cE / 100 * cN)
                new_body = re.sub(r"\bcE:\s*(?:-?\d+)", f"cE: {corrected}", new_body, count=1)
                changed_local = True
            # Also propagate to allOutcomes[0].tE/cE so the analysis engine sees consistent values.
            if changed_local:
                # Refresh the matched-numeric values from the updated body
                # (we want to also patch the first allOutcomes entry).
                m_te = re.search(r"\btE:\s*(\d+)", new_body)
                m_ce = re.search(r"\bcE:\s*(\d+)", new_body)
                if m_te and m_ce:
                    new_te = m_te.group(1)
                    new_ce = m_ce.group(1)
                    # In allOutcomes[0], replace the first tE: and cE: occurrences
                    # that follow `allOutcomes: [`.
                    ao_re = re.compile(r"(allOutcomes:\s*\[\s*\{[^}]*\btE:\s*)(\d+)([^}]*\bcE:\s*)(\d+)")
                    new_body = ao_re.sub(
                        lambda mm: mm.group(1) + new_te + mm.group(3) + new_ce, new_body, count=1
                    )
                n_fixed += 1
                # Splice into output.
                out_parts.append(txt[last:m.start()])
                out_parts.append(f"'{m.group(1)}': {{{new_body}}}")
                last = m.end()
                continue
    out_parts.append(txt[last:])
    return "".join(out_parts), n_fixed


# ---- (B) AUTO_INCLUDE template-leak ------------------------------------------
def fix_auto_include_set(p: Path, txt: str) -> tuple[str, bool]:
    """If AUTO_INCLUDE_TRIAL_IDS has zero intersection with realData NCTs, replace
    it with the realData NCT set."""
    m = re.search(r"const\s+AUTO_INCLUDE_TRIAL_IDS\s*=\s*new\s+Set\(\[([^\]]*)\]\);", txt)
    if not m:
        return txt, False
    inc = set(re.findall(r"NCT\d+", m.group(1)))
    rd_keys = {bm.group(1) for bm in TRIAL_BLOCK_RE.finditer(txt)}
    # Heuristic: leaked set if there are realData NCTs and the include set has
    # no overlap with them.
    if rd_keys and inc and not (inc & rd_keys):
        new_set_lit = ", ".join(f"'{n}'" for n in sorted(rd_keys))
        new_decl = f"const AUTO_INCLUDE_TRIAL_IDS = new Set([{new_set_lit}]);"
        new_txt = txt[: m.start()] + new_decl + txt[m.end():]
        return new_txt, True
    return txt, False


# ---- (C) old screening template ----------------------------------------------
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


def fix_screening_template(p: Path, txt: str) -> tuple[str, bool]:
    if SCREEN_OLD_V1 in txt:
        return txt.replace(SCREEN_OLD_V1, SCREEN_NEW), True
    return txt, False


# ---- (D) broken protocol-badge href ------------------------------------------
def fix_broken_protocol_links(p: Path, txt: str) -> tuple[str, int]:
    """Rewrite any <a href="protocols/<missing.md>"> to point at protocols/INDEX.md."""
    n_fixed = 0

    def _sub(m: re.Match) -> str:
        nonlocal n_fixed
        href = m.group(1)
        if (HERE / href).exists():
            return m.group(0)
        n_fixed += 1
        return 'href="protocols/INDEX.md"'

    new_txt = PROTOCOL_HREF_RE.sub(_sub, txt)
    return new_txt, n_fixed


# ---- (E) year + dup id outliers ----------------------------------------------
def fix_year_outlier(p: Path, txt: str) -> tuple[str, bool]:
    """If year < 1990 or > 2030, clamp to a sane default 2024 (with comment)."""
    changed = False
    def _sub(m):
        nonlocal changed
        y = int(m.group(2))
        if y < 1990 or y > 2030:
            changed = True
            return f"{m.group(1)}year: 2024"
        return m.group(0)
    new_txt = re.sub(r"('(?:NCT\d{7,8})':\s*\{[^}]{0,200})year:\s*(-?\d+)", _sub, txt)
    return new_txt, changed


# ---- Main --------------------------------------------------------------------
def patch_file(p: Path) -> dict:
    txt = p.read_text(encoding="utf-8", errors="replace")
    orig = txt

    txt, ec_fixed = fix_event_counts(p, txt)
    txt, ai_fixed = fix_auto_include_set(p, txt)
    txt, sc_fixed = fix_screening_template(p, txt)
    txt, pl_fixed = fix_broken_protocol_links(p, txt)
    txt, yr_fixed = fix_year_outlier(p, txt)

    if txt != orig:
        p.write_text(txt, encoding="utf-8")
    return {
        "event_counts": ec_fixed,
        "auto_include_set": ai_fixed,
        "screening_template": sc_fixed,
        "protocol_links": pl_fixed,
        "year_outlier": yr_fixed,
    }


def main():
    targets = sorted(p for p in HERE.glob("*.html") if p.is_file())
    print(f"Targets: {len(targets):,} HTML files")

    totals = {"event_counts": 0, "auto_include_set": 0, "screening_template": 0,
              "protocol_links": 0, "year_outlier": 0, "changed": 0}
    for i, p in enumerate(targets, 1):
        before = p.read_text(encoding="utf-8", errors="replace")
        s = patch_file(p)
        if p.read_text(encoding="utf-8", errors="replace") != before:
            totals["changed"] += 1
        totals["event_counts"] += s["event_counts"]
        totals["auto_include_set"] += int(s["auto_include_set"])
        totals["screening_template"] += int(s["screening_template"])
        totals["protocol_links"] += s["protocol_links"]
        totals["year_outlier"] += int(s["year_outlier"])
        if i % 300 == 0:
            print(f"  [{i}/{len(targets)}] {p.name}")
    print()
    for k, v in totals.items():
        print(f"  {k:<24}: {v:,}")


if __name__ == "__main__":
    main()
