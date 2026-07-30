#!/usr/bin/env python
"""Remove publication/enrolment DATE as an eligibility axis from
RIVAROXABAN_VASC_REVIEW.html.

Policy (Mahmood, 2026-07-30): the "exclude pre-2015" rule was a legacy artifact
of a CT.gov-only sourcing era. Evidence is now also sourced from FDA and EMA
documents, supplements of previous meta-analyses, and open-access full texts, so
a trial's age no longer predicts whether usable data can be obtained. Eligibility
is decided on PICO/scope plus verified data availability - never on date.

Consequence for this review: ATLAS ACS 2 (2012) is no longer "ineligible because
it is pre-2015". It is judged on scope alone, where it still sits outside a
stable-ASCVD/PAD dual-pathway question (acute ACS within 7 days, aspirin +/-
thienopyridine background, placebo comparator). The date-based contradiction the
external review flagged disappears; the scope question remains open and is now
the only thing stated.

Fail-closed: every anchor must match its expected count or nothing is written.
Run from the repo root.
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TARGET = Path("RIVAROXABAN_VASC_REVIEW.html")

PATCHES = [
    # ------------------------------------------------------------------
    # 1. Live auto-screen filter. This one actually excluded records, so it
    #    is the substantive change - not just wording.
    # ------------------------------------------------------------------
    # The filter is the else-branch of a ternary, so it is replaced with
    # `void 0` rather than deleted - dropping the branch outright would leave
    # `cond ? A :` and break the parse.
    (
        "auto-screen era filter (functional)",
        '."):t.year<2015&&(t.status="exclude",t.reason="Era Restriction: Pre-2015.")',
        '."):void 0',
        1,
    ),
    # ------------------------------------------------------------------
    # 2. Protocol eligibility table (visible criteria grid).
    # ------------------------------------------------------------------
    (
        "eligibility table - publication row",
        '<td class="p-3 text-slate-300">Published or registered; any language</td>'
        '<td class="p-3 text-slate-400">Pre-2015; duplicate cohorts; editorials, letters, reviews</td>',
        '<td class="p-3 text-slate-300">Any language, any year. Published, registered, or '
        'retrievable from a regulatory dossier (FDA/EMA), a previous meta-analysis supplement, '
        'or open-access full text</td>'
        '<td class="p-3 text-slate-400">Duplicate cohorts; editorials, letters, reviews; '
        'no retrievable outcome data. Publication date is NOT an exclusion criterion.</td>',
        1,
    ),
    # ------------------------------------------------------------------
    # 3. Visual abstract badge that asserted a post-2015 evidence base.
    # ------------------------------------------------------------------
    (
        "visual abstract era badge",
        '<div class="va-label">Acquisition Era</div>'
        '<div class="va-value">Post-2015 Enrollment</div>',
        '<div class="va-label">Evidence Sources</div>'
        '<div class="va-value">Registry, regulatory &amp; published</div>',
        1,
    ),
    # ------------------------------------------------------------------
    # 4. Stale protocol flag (declared once, never read).
    # ------------------------------------------------------------------
    (
        "protocol post2015 flag",
        'rctOnly:!0,post2015:!0}',
        'rctOnly:!0}',
        1,
    ),
    # ------------------------------------------------------------------
    # 5. Arabic locale entries mirroring the removed criteria.
    # ------------------------------------------------------------------
    (
        "ar locale - publication inclusion",
        '"Published or registered; any language":"منشورة أو مسجلة؛ أي لغة"',
        '"Any language, any year. Published, registered, or retrievable from a regulatory dossier '
        '(FDA/EMA), a previous meta-analysis supplement, or open-access full text":'
        '"أي لغة، أي سنة. منشورة أو مسجلة أو يمكن استخراجها من ملف تنظيمي (FDA/EMA) أو ملحق '
        'تحليل وصفي سابق أو نص كامل مفتوح الوصول"',
        1,
    ),
    (
        "ar locale - publication exclusion",
        '"Pre-2015; duplicate cohorts; editorials, letters, reviews":'
        '"قبل 2015؛ أفواج مكررة؛ افتتاحيات، رسائل، مراجعات"',
        '"Duplicate cohorts; editorials, letters, reviews; no retrievable outcome data. '
        'Publication date is NOT an exclusion criterion.":'
        '"أفواج مكررة؛ افتتاحيات، رسائل، مراجعات؛ لا توجد بيانات نتائج قابلة للاستخراج. '
        'تاريخ النشر ليس معياراً للاستبعاد."',
        1,
    ),
    (
        "ar locale - era badge",
        '"Acquisition Era":"فترة الاستحواذ","Post-2015 Enrollment":"التسجيل بعد 2015"',
        '"Evidence Sources":"مصادر الأدلة","Registry, regulatory & published":'
        '"السجلات والجهات التنظيمية والمنشورات"',
        2,
    ),
]


def main():
    if not TARGET.exists():
        print("FAIL: run from repo root")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    applied = []

    for name, old, new, count in PATCHES:
        found = src.count(old)
        if found != count:
            print(f"FAIL [{name}]: expected {count}, found {found}")
            print(f"  anchor head: {old[:110]}...")
            return 1
        src = src.replace(old, new, count)
        applied.append(name)

    # Nothing may still assert a date-based eligibility rule.
    for banned in ("Pre-2015", "Post-2015 Enrollment", "Era Restriction", "year<2015"):
        if banned in src:
            print(f"FAIL: '{banned}' still present after patching")
            return 1

    TARGET.write_text(src, encoding="utf-8", newline="\n")
    print(f"OK: {len(applied)} date-eligibility sites removed")
    for a in applied:
        print(f"  - {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
