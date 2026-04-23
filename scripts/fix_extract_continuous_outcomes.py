#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Two fixes for the Extract tab when trials have continuous-outcome
realData (tE=null, cE=null, publishedHR=null — only allOutcomes[].md/.se):

  FIX 1: Default-scope filter respects _outcomeExcluded
  ------------------------------------------------------
  ExtractEngine.render() bypassed the outcome-scope filter for
  `selectedOutcome === 'default'`, always returning ALL trials. This
  causes trials like PARAGLIDE-HF (whose only outcome is CONTINUOUS
  NTproBNP, no MACE) to appear in the default CV-composite pool
  display even though they don't have the matching outcome.

  After fix: default scope respects _outcomeExcluded like other scopes.
  Trials without a MACE entry in allOutcomes are hidden from the
  "Matched CV Composite (default)" pool.

  FIX 2: Continuous-outcome card body replaces Events/Total 0/N
  -------------------------------------------------------------
  The Extract data-card renders `Events 0 / Total N 233 (0.0%)` for
  continuous-outcome trials because `d?.tE ?? 0` coerces null to 0.
  For a reader, "0 events" looks like a data error.

  After fix: if the trial's data is continuous (tE===null AND cE===null),
  the card replaces the two-arm event grid with a clear amber-bordered
  notice explaining the outcome is continuous, pointing to the Source
  Evidence Extracts below for the actual effect estimate, and displaying
  arm sample sizes (n = tN vs cN).
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

# ---------------------------------------------------------------------------
# Fix 1: filter respects _outcomeExcluded for default scope
# ---------------------------------------------------------------------------
FIX1_OLD = (
    "                const includedScoped = includedAll.filter(t => {\n"
    "                    if (!t?.data) return selectedOutcome === 'default';\n"
    "                    if (selectedOutcome === 'default') return true;\n"
    "                    return !t.data._outcomeExcluded;\n"
    "                });"
)
FIX1_NEW = (
    "                const includedScoped = includedAll.filter(t => {\n"
    "                    if (!t?.data) return selectedOutcome === 'default';\n"
    "                    // No bypass for 'default' — trials without a MACE-compatible outcome\n"
    "                    // (e.g. PARAGLIDE-HF with only CONTINUOUS NTproBNP) must be filtered\n"
    "                    // out of the default CV-composite pool display.\n"
    "                    return !t.data._outcomeExcluded;\n"
    "                });"
)

# ---------------------------------------------------------------------------
# Fix 2: replace the 32-line Events/Total grid with a conditional that
# renders a continuous-outcome notice when tE AND cE are null.
# The OLD block is the grid-cols-2 gap-8 block with both arm inputs.
# Captures exactly the `<div class="grid grid-cols-2 gap-8">` section.
# ---------------------------------------------------------------------------
FIX2_OLD = (
    '                            <div class="grid grid-cols-2 gap-8">\n'
    '                                <div>\n'
    '                                    <div class="text-[10px] font-bold uppercase tracking-widest text-emerald-400/70 mb-3">Treatment Arm</div>\n'
    '                                    <div class="flex items-center gap-3">\n'
    '                                        <div>\n'
    '                                            <label class="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Events${this._provDotHtml(t, \'tE\')}</label>\n'
    '                                            <input type="number" onchange="ExtractEngine.upd(\'${trialIdArg}\', \'tE\', this.value)" value="${d?.tE ?? 0}" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-lg text-emerald-400 font-bold outline-none font-mono mt-1">\n'
    '                                        </div>\n'
    '                                        <span class="opacity-20 text-2xl font-bold mt-4">/</span>\n'
    '                                        <div>\n'
    '                                            <label class="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Total N${this._provDotHtml(t, \'tN\')}</label>\n'
    '                                            <input type="number" onchange="ExtractEngine.upd(\'${trialIdArg}\', \'tN\', this.value)" value="${d?.tN ?? 0}" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-lg text-slate-300 outline-none font-mono mt-1">\n'
    '                                        </div>\n'
    '                                        <div class="mt-4 text-[10px] text-emerald-400/60 font-mono font-bold">${erT}</div>\n'
    '                                    </div>\n'
    '                                </div>\n'
    '                                <div>\n'
    '                                    <div class="text-[10px] font-bold uppercase tracking-widest text-rose-400/70 mb-3">Control Arm</div>\n'
    '                                    <div class="flex items-center gap-3">\n'
    '                                        <div>\n'
    '                                            <label class="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Events${this._provDotHtml(t, \'cE\')}</label>\n'
    '                                            <input type="number" onchange="ExtractEngine.upd(\'${trialIdArg}\', \'cE\', this.value)" value="${d?.cE ?? 0}" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-lg text-rose-400 font-bold outline-none font-mono mt-1">\n'
    '                                        </div>\n'
    '                                        <span class="opacity-20 text-2xl font-bold mt-4">/</span>\n'
    '                                        <div>\n'
    '                                            <label class="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Total N${this._provDotHtml(t, \'cN\')}</label>\n'
    '                                            <input type="number" onchange="ExtractEngine.upd(\'${trialIdArg}\', \'cN\', this.value)" value="${d?.cN ?? 0}" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-lg text-slate-300 outline-none font-mono mt-1">\n'
    '                                        </div>\n'
    '                                        <div class="mt-4 text-[10px] text-rose-400/60 font-mono font-bold">${erC}</div>\n'
    '                                    </div>\n'
    '                                </div>\n'
    '                            </div>'
)

# Continuous-outcome notice replacing the arms grid when tE AND cE are null.
# Uses IIFE to detect continuous locally without touching outer let/const scope.
FIX2_NEW = (
    '                            ${(() => {\n'
    '                                const _isContinuous = (d?.tE == null && d?.cE == null);\n'
    '                                if (_isContinuous) {\n'
    '                                    const _contOutcome = (d?.allOutcomes ?? []).find(o => o?.type === \'CONTINUOUS\') ?? {};\n'
    '                                    const _contTitle = _contOutcome.title || \'a continuous outcome (see Source Evidence Extracts)\';\n'
    '                                    return `<div class="p-6 rounded-2xl border border-amber-500/30 bg-amber-500/5">\n'
    '                                        <div class="text-[10px] font-bold uppercase tracking-widest text-amber-400/80 mb-2"><i class="fa-solid fa-chart-line mr-1"></i>Continuous outcome &mdash; events display not applicable</div>\n'
    '                                        <div class="text-[13px] text-slate-200 mb-3">Primary endpoint: <span class="font-semibold text-amber-200">${escapeHtml(_contTitle)}</span></div>\n'
    '                                        <div class="text-[11px] text-slate-400 leading-relaxed">This trial reports a continuous effect (mean difference or ratio of change), not a 2&times;2 event table. The published effect estimate and 95% CI appear in the <strong>Source Evidence Extracts</strong> panel below. The 2&times;2 event fields are intentionally null and are excluded from OR/RR pooling. HR pooling also skips this trial unless a <code>publishedHR</code> is declared.</div>\n'
    '                                        <div class="grid grid-cols-2 gap-6 mt-4">\n'
    '                                            <div><div class="text-[9px] uppercase tracking-widest text-slate-500 font-bold mb-1">Treatment n</div><div class="text-2xl font-mono font-bold text-emerald-400">${d?.tN ?? \'--\'}</div></div>\n'
    '                                            <div><div class="text-[9px] uppercase tracking-widest text-slate-500 font-bold mb-1">Control n</div><div class="text-2xl font-mono font-bold text-rose-400">${d?.cN ?? \'--\'}</div></div>\n'
    '                                        </div>\n'
    '                                    </div>`;\n'
    '                                }\n'
    '                                return `<div class="grid grid-cols-2 gap-8">\n'
    '                                <div>\n'
    '                                    <div class="text-[10px] font-bold uppercase tracking-widest text-emerald-400/70 mb-3">Treatment Arm</div>\n'
    '                                    <div class="flex items-center gap-3">\n'
    '                                        <div>\n'
    '                                            <label class="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Events${this._provDotHtml(t, \'tE\')}</label>\n'
    '                                            <input type="number" onchange="ExtractEngine.upd(\'${trialIdArg}\', \'tE\', this.value)" value="${d?.tE ?? 0}" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-lg text-emerald-400 font-bold outline-none font-mono mt-1">\n'
    '                                        </div>\n'
    '                                        <span class="opacity-20 text-2xl font-bold mt-4">/</span>\n'
    '                                        <div>\n'
    '                                            <label class="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Total N${this._provDotHtml(t, \'tN\')}</label>\n'
    '                                            <input type="number" onchange="ExtractEngine.upd(\'${trialIdArg}\', \'tN\', this.value)" value="${d?.tN ?? 0}" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-lg text-slate-300 outline-none font-mono mt-1">\n'
    '                                        </div>\n'
    '                                        <div class="mt-4 text-[10px] text-emerald-400/60 font-mono font-bold">${erT}</div>\n'
    '                                    </div>\n'
    '                                </div>\n'
    '                                <div>\n'
    '                                    <div class="text-[10px] font-bold uppercase tracking-widest text-rose-400/70 mb-3">Control Arm</div>\n'
    '                                    <div class="flex items-center gap-3">\n'
    '                                        <div>\n'
    '                                            <label class="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Events${this._provDotHtml(t, \'cE\')}</label>\n'
    '                                            <input type="number" onchange="ExtractEngine.upd(\'${trialIdArg}\', \'cE\', this.value)" value="${d?.cE ?? 0}" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-lg text-rose-400 font-bold outline-none font-mono mt-1">\n'
    '                                        </div>\n'
    '                                        <span class="opacity-20 text-2xl font-bold mt-4">/</span>\n'
    '                                        <div>\n'
    '                                            <label class="text-[9px] uppercase tracking-widest text-slate-500 font-bold">Total N${this._provDotHtml(t, \'cN\')}</label>\n'
    '                                            <input type="number" onchange="ExtractEngine.upd(\'${trialIdArg}\', \'cN\', this.value)" value="${d?.cN ?? 0}" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-lg text-slate-300 outline-none font-mono mt-1">\n'
    '                                        </div>\n'
    '                                        <div class="mt-4 text-[10px] text-rose-400/60 font-mono font-bold">${erC}</div>\n'
    '                                    </div>\n'
    '                                </div>\n'
    '                            </div>`;\n'
    '                            })()}'
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text

    statuses = []

    # Fix 1 — filter
    if "// No bypass for 'default'" in work:
        statuses.append("fix1-filter:skip")
    elif work.count(FIX1_OLD) == 1:
        work = work.replace(FIX1_OLD, FIX1_NEW, 1)
        statuses.append("fix1-filter:OK")
    else:
        statuses.append(f"fix1-filter:fail(matches={work.count(FIX1_OLD)})")

    # Fix 2 — continuous-outcome display. If the canonical Events/Total grid
    # doesn't exist in this app (3 legacy apps have a divergent layout),
    # we skip fix 2 for that app without failing the whole file: those apps
    # don't have continuous-outcome trials anyway, so the display fix is
    # a no-op for them.
    if "Continuous outcome &mdash; events display not applicable" in work:
        statuses.append("fix2-display:skip(already)")
    elif work.count(FIX2_OLD) == 1:
        work = work.replace(FIX2_OLD, FIX2_NEW, 1)
        statuses.append("fix2-display:OK")
    elif work.count(FIX2_OLD) == 0:
        statuses.append("fix2-display:skip(legacy-template)")
    else:
        statuses.append(f"fix2-display:fail(matches={work.count(FIX2_OLD)})")

    any_fail = any("fail(" in s for s in statuses)
    any_change = any(s.endswith(":OK") for s in statuses)

    if any_fail:
        return f"FAIL {path.name}: {'; '.join(statuses)}"
    if not any_change:
        return f"SKIP {path.name}: already-migrated (both fixes)"
    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}: {'; '.join(statuses)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply): ap.error("pass --dry-run or --apply")
    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        r = apply_to_file(p, dry_run=args.dry_run)
        if r.startswith("OK"): ok += 1
        elif r.startswith("SKIP"): skip += 1
        else: fail += 1
        if not r.startswith("SKIP"): print(r)
    print(f"\nSummary: {len(targets)} | {ok} fix | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
