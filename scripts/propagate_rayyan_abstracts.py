#!/usr/bin/env python3
"""
Propagate the Rayyan-style inline-abstract fix across every RapidMeta _REVIEW.html.

Migration, applied idempotently:
  1. Insert the AbstractHydrator namespace immediately before `const ScreenEngine = {`.
  2. Insert `AbstractHydrator.hydrateTrials(this.state.trials)` in init() after the
     `bootstrapSeed.changed` block.
  3. Replace the 200-char preview + "Show Full Abstract" toggle with a single
     always-inline abstract block (white-space: pre-line).

Ground truth for the snippets is CFTR_MODULATORS_NMA_REVIEW.html (commit 47a25a7,
validated 2026-04-22 by user).

Usage:
    python propagate_rayyan_abstracts.py --dry-run            # walk all apps, report action
    python propagate_rayyan_abstracts.py --dry-run --file X   # single-file dry run with diff
    python propagate_rayyan_abstracts.py --apply              # apply to all apps
    python propagate_rayyan_abstracts.py --apply --file X     # apply to one file
"""
from __future__ import annotations
import argparse, difflib, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

HYDRATOR_MARKER = "const AbstractHydrator = {"

# ---------------------------------------------------------------------------
# Edit 1: insert the AbstractHydrator namespace immediately before ScreenEngine.
# Match the exact line, preserving file-level indentation (8 spaces).
# ---------------------------------------------------------------------------
EDIT1_OLD = "        const ScreenEngine = {"
EDIT1_NEW = """\
        /* ── Abstract hydration: Rayyan-style rich abstracts in Screening tab.
           Uses Europe PMC (CORS-friendly) via AutoExtractEngine.fetchAbstract.
           Cache: localStorage keyed by PMID, 90-day TTL.
           Sync pass applies cached abstracts before first render; async pass
           fetches missing ones in parallel and re-renders on each arrival. ── */
        const AbstractHydrator = {
            CACHE_PREFIX: 'rm_abstract_v1_',
            CACHE_TTL_MS: 90 * 24 * 60 * 60 * 1000,

            cacheKey(pmid) { return this.CACHE_PREFIX + String(pmid).trim(); },

            getCached(pmid) {
                try {
                    const raw = localStorage.getItem(this.cacheKey(pmid));
                    if (!raw) return null;
                    const { text, fetchedAt } = JSON.parse(raw);
                    if (!text || !fetchedAt) return null;
                    if (Date.now() - fetchedAt > this.CACHE_TTL_MS) return null;
                    return text;
                } catch (e) { return null; }
            },

            setCached(pmid, text) {
                try {
                    localStorage.setItem(this.cacheKey(pmid), JSON.stringify({ text, fetchedAt: Date.now() }));
                } catch (e) { /* quota exceeded — ignore */ }
            },

            resolvePmid(trial) {
                return String(trial?.pmid
                    ?? trial?.data?.pmid
                    ?? (typeof RapidMeta !== 'undefined' && RapidMeta.realData?.[trial?.id]?.pmid)
                    ?? '').trim() || null;
            },

            /* Only overwrite if the incoming text is richer than what's on the trial.
               Protects search-fetched and hand-authored abstracts from being clobbered. */
            applyToTrial(trial, text) {
                if (!trial || !text) return false;
                const current = String(trial.abstract ?? '');
                if (current && current.length >= text.length) return false;
                trial.abstract = text;
                return true;
            },

            async hydrateTrials(trials) {
                if (!Array.isArray(trials) || trials.length === 0) return;
                let anyChanged = false;

                /* Sync cache pass — applies before caller gets control back */
                trials.forEach(t => {
                    const pmid = this.resolvePmid(t);
                    if (!pmid) return;
                    const cached = this.getCached(pmid);
                    if (cached && this.applyToTrial(t, cached)) anyChanged = true;
                });
                if (anyChanged && typeof ScreenEngine !== 'undefined') {
                    try { ScreenEngine.render?.(); } catch (e) {}
                }

                /* Async fetch pass — in parallel for anything not cached */
                const fetcher = typeof AutoExtractEngine !== 'undefined' ? AutoExtractEngine : null;
                if (!fetcher?.fetchAbstract) return;

                const pending = trials
                    .map(t => ({ trial: t, pmid: this.resolvePmid(t) }))
                    .filter(({ pmid }) => pmid && !this.getCached(pmid));
                if (pending.length === 0) return;

                await Promise.allSettled(pending.map(async ({ trial, pmid }) => {
                    try {
                        const text = await fetcher.fetchAbstract(pmid);
                        if (!text) return;
                        this.setCached(pmid, text);
                        if (this.applyToTrial(trial, text) && typeof ScreenEngine !== 'undefined') {
                            try { ScreenEngine.render?.(); } catch (e) {}
                            try { RapidMeta.save?.(); } catch (e) {}
                        }
                    } catch (e) { /* swallow — trial keeps its snippet as fallback */ }
                }));
            }
        };

        const ScreenEngine = {"""

# ---------------------------------------------------------------------------
# Edit 2: hook the hydrator call into init() after the bootstrap-seed block.
# ---------------------------------------------------------------------------
EDIT2_OLD = """                const bootstrapSeed = !this.hasAnalysisReadyTrials() ? this.ensureCanonicalAnalysisSeed() : { changed: false, seeded: [] };
                if (bootstrapSeed.changed) {
                    this.state.results = null;
                    this.save();
                }"""

EDIT2_NEW = EDIT2_OLD + """
                /* Rayyan-style abstract hydration: apply cached abstracts synchronously,
                   then fetch any missing ones in parallel (non-blocking). Falls back to
                   the per-trial snippet if the PMID lookup fails or the user is offline. */
                try { AbstractHydrator.hydrateTrials(this.state.trials); } catch (e) {}"""

# ---------------------------------------------------------------------------
# Edit 3a: replace the preview+toggle variable block.
# Python raw-string-ish literal kept single-line per original source line.
# ---------------------------------------------------------------------------
EDIT3A_OLD = """                /* Full abstract toggle (Task 6: D2) */
                const hasFullAbstract = (t.abstract ?? '').length > 200;
                const abstractPreview = hasFullAbstract ? escapeHtml(t.abstract.slice(0, 200)) + '...' : escapeHtml(absText);
                const fullAbstractToggle = hasFullAbstract
                    ? '<button type="button" class="text-[10px] text-slate-500 hover:text-slate-300 mt-2 underline" aria-expanded="false" onclick="const el=this.nextElementSibling;el.classList.toggle(\\'hidden\\');const exp=!el.classList.contains(\\'hidden\\');this.setAttribute(\\'aria-expanded\\',exp);this.textContent=exp?\\'Collapse Abstract\\':\\'Show Full Abstract\\'">Show Full Abstract</button><div class="hidden text-[13px] text-slate-400 mt-2 leading-[1.7] max-h-64 overflow-y-auto pr-2" style="font-family: Georgia, serif;">' + SearchEngine._highlightScreening(escapeHtml(t.abstract), screenHits) + '</div>'
                    : '';"""

EDIT3A_NEW = """                /* Full abstract — always rendered inline, no truncation, no toggle.
                   Rayyan-style: the whole abstract is there from first paint so the
                   reviewer doesn't have to click to read it. Section breaks in
                   structured PubMed abstracts (BACKGROUND/METHODS/RESULTS/CONCLUSIONS)
                   are preserved via `white-space: pre-line`. */
                const abstractHtml = (t.abstract ?? '').trim()
                    ? SearchEngine._highlightScreening(escapeHtml(t.abstract), screenHits)
                    : escapeHtml(absText);"""

# ---------------------------------------------------------------------------
# Edit 3b: replace the markup paragraph + toggle insertion with the inline block.
# ---------------------------------------------------------------------------
EDIT3B_OLD = """                    <div class="bg-slate-950 p-8 rounded-[30px] border border-slate-800 shadow-2xl">
                        <h3 class="text-[10px] opacity-50 font-bold uppercase tracking-[0.3em] mb-5 flex items-center gap-2"><i class="fa-solid fa-file-lines" style="font-size:11px"></i> Abstract <span class="text-[9px] text-slate-600 ml-2">(screening keywords highlighted)</span></h3>
                        <p class="text-[15px] text-slate-300 leading-[1.8] font-medium" style="font-family: Georgia, serif;">${SearchEngine._highlightScreening(abstractPreview, screenHits)}</p>
                        ${fullAbstractToggle}
                    </div>"""

EDIT3B_NEW = """                    <div class="bg-slate-950 p-8 rounded-[30px] border border-slate-800 shadow-2xl">
                        <h3 class="text-[10px] opacity-50 font-bold uppercase tracking-[0.3em] mb-5 flex items-center gap-2"><i class="fa-solid fa-file-lines" style="font-size:11px"></i> Abstract <span class="text-[9px] text-slate-600 ml-2">(screening keywords highlighted)</span></h3>
                        <div class="text-[15px] text-slate-300 leading-[1.8] font-medium" style="font-family: Georgia, serif; white-space: pre-line;">${abstractHtml}</div>
                    </div>"""

# ---------------------------------------------------------------------------
# VARIANT B — for older apps that never had the preview-toggle at all.
# They use `const abstractPreview = escapeHtml(absText);` directly and a plain
# <p> render. We keep `abstractPreview` as the variable name (no need to rename)
# and only swap the <p> for a <div white-space: pre-line>.
# ---------------------------------------------------------------------------
VARB_ABSTRACT_PREVIEW_LINE = "                const abstractPreview = escapeHtml(absText);"

VARB_P_OLD = """                        <p class="text-[15px] text-slate-300 leading-[1.8] font-medium" style="font-family: Georgia, serif;">${SearchEngine._highlightScreening(abstractPreview, screenHits)}</p>"""

VARB_P_NEW = """                        <div class="text-[15px] text-slate-300 leading-[1.8] font-medium" style="font-family: Georgia, serif; white-space: pre-line;">${SearchEngine._highlightScreening(abstractPreview, screenHits)}</div>"""


def migrate(text: str) -> tuple[str, list[str]]:
    """Atomic: returns (migrated_text, statuses). If any edit fails, the ORIGINAL
    text is returned unchanged so we never write a partially-migrated file.
    Both the input and the patch strings are LF-normalised so CRLF files match."""
    statuses = []
    if HYDRATOR_MARKER in text:
        return text, ["skip: already-migrated (AbstractHydrator present)"]

    # Remember the original line-ending so we can restore it after the replacements.
    original_uses_crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if original_uses_crlf else text

    # Variant detection: apps with the toggle pattern get VARIANT A; those
    # without (older, simpler template) get VARIANT B. Detect by the toggle's
    # distinctive leading comment.
    has_toggle = "/* Full abstract toggle (Task 6: D2) */" in work

    if has_toggle:
        edit_sequence = (
            ("edit1-hydrator-namespace",   EDIT1_OLD,  EDIT1_NEW),
            ("edit2-init-hook",            EDIT2_OLD,  EDIT2_NEW),
            ("edit3a-toggle-variables",    EDIT3A_OLD, EDIT3A_NEW),
            ("edit3b-inline-markup",       EDIT3B_OLD, EDIT3B_NEW),
        )
        variant = "A"
    else:
        # Variant B: no toggle to remove, just tighten the render tag.
        edit_sequence = (
            ("edit1-hydrator-namespace",   EDIT1_OLD,          EDIT1_NEW),
            ("edit2-init-hook",            EDIT2_OLD,          EDIT2_NEW),
            ("edit3b-p-to-div-preline",    VARB_P_OLD,         VARB_P_NEW),
        )
        variant = "B"

    statuses.append(f"variant={variant}")

    scratch = work
    for label, old, new in edit_sequence:
        hit = scratch.count(old)
        if hit != 1:
            return text, statuses + [f"fail: {label} marker matched {hit} times (expected 1)"]
        scratch = scratch.replace(old, new, 1)
        statuses.append(f"{label}: OK")

    migrated = scratch.replace("\n", "\r\n") if original_uses_crlf else scratch
    return migrated, statuses


def process(path: pathlib.Path, dry_run: bool) -> tuple[str, list[str], str | None]:
    """Read file, migrate, write if !dry_run. Return (path_str, statuses, diff_or_None)."""
    original = path.read_text(encoding="utf-8", newline="")
    migrated, statuses = migrate(original)
    diff = None
    if migrated != original:
        diff = f"+{len(migrated) - len(original)} chars"
        if not dry_run:
            path.write_text(migrated, encoding="utf-8", newline="")
    return str(path.name), statuses, diff


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Report action without writing")
    ap.add_argument("--apply", action="store_true", help="Apply changes to disk")
    ap.add_argument("--file", type=str, default=None, help="Restrict to one filename (basename) under the Finrenone root")
    args = ap.parse_args()

    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")
    if args.dry_run and args.apply:
        ap.error("--dry-run and --apply are mutually exclusive")

    if args.file:
        p = pathlib.Path(args.file)
        # Accept either an absolute path or a basename under ROOT.
        targets = [p if p.is_absolute() else (ROOT / args.file)]
        if not targets[0].exists():
            sys.exit(f"file not found: {targets[0]}")
    else:
        targets = sorted(ROOT.glob("*_REVIEW.html"))

    migrated_ok, skipped, failed = 0, 0, 0
    for p in targets:
        name, statuses, diff = process(p, dry_run=args.dry_run)
        last = statuses[-1] if statuses else ""
        if last.startswith("fail:"):
            failed += 1
            print(f"FAIL  {name:50s}  {last}")
        elif last.startswith("skip:"):
            skipped += 1
            print(f"SKIP  {name:50s}  {last}")
        else:
            migrated_ok += 1
            tag = "DRY" if args.dry_run else "APPLIED"
            print(f"{tag:7s} {name:50s}  {', '.join(statuses)}  ({diff or 'no-op'})")

    total = len(targets)
    print()
    print(f"Summary: {total} files  |  {migrated_ok} migrate  |  {skipped} skip  |  {failed} fail  |  mode={'dry-run' if args.dry_run else 'apply'}")
    if failed and args.apply:
        sys.exit(1)


if __name__ == "__main__":
    main()
