#!/usr/bin/env python3
# sentinel:skip-file — developer tool; hardcoded ROOT is intentional (local Finrenone checkout only)
"""Propagate the defensive evidence re-hydration in ExtractEngine.setView
(CFTR post-48dee0b fix) to all 98 other _REVIEW.html apps. Without this,
runPrecision's t.data = {...realData[id]} replacement wipes evidence and
subsequent view switches show the empty-extracts placeholder.
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

SENTINEL = "/* Defensive re-hydration"

OLD = (
    "            setView(view) {\n"
    "                this.currentView = view;\n"
    "                ['data', 'demographics', 'rob'].forEach(v => {\n"
    "                    const el = document.getElementById('extract-view-' + v);\n"
    "                    if (v === view) el.classList.remove('hidden'); else el.classList.add('hidden');\n"
    "                });\n"
    "                document.querySelectorAll('.extract-view-btn').forEach(btn => {\n"
    "                    if (btn.dataset.view === view) btn.classList.add('active'); else btn.classList.remove('active');\n"
    "                });\n"
    "                this.render();\n"
    "            },"
)

NEW = (
    "            setView(view) {\n"
    "                this.currentView = view;\n"
    "                ['data', 'demographics', 'rob'].forEach(v => {\n"
    "                    const el = document.getElementById('extract-view-' + v);\n"
    "                    if (v === view) el.classList.remove('hidden'); else el.classList.add('hidden');\n"
    "                });\n"
    "                document.querySelectorAll('.extract-view-btn').forEach(btn => {\n"
    "                    if (btn.dataset.view === view) btn.classList.add('active'); else btn.classList.remove('active');\n"
    "                });\n"
    "                /* Defensive re-hydration: if trial.data.evidence was wiped between views\n"
    "                   (e.g. runPrecision replaces t.data with a fresh realData copy that has\n"
    "                   evidence:[]), re-apply from the EvidenceHydrator's localStorage cache\n"
    "                   so Demographics + RoB + Data Entry all see the same items. */\n"
    "                try {\n"
    "                    if (typeof EvidenceHydrator !== 'undefined' && Array.isArray(RapidMeta.state.trials)) {\n"
    "                        for (const t of RapidMeta.state.trials) {\n"
    "                            if (!t?.id?.startsWith?.('NCT')) continue;\n"
    "                            const cached = EvidenceHydrator.getCached(t.id);\n"
    "                            if (cached && cached.length) EvidenceHydrator.applyToTrial(t, cached);\n"
    "                        }\n"
    "                    }\n"
    "                } catch (e) { /* swallow */ }\n"
    "                this.render();\n"
    "            },"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if SENTINEL in text:
        return f"SKIP {path.name}: already-migrated"
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    if work.count(OLD) != 1:
        return f"FAIL {path.name}: OLD matched {work.count(OLD)} times (expected 1)"
    work = work.replace(OLD, NEW, 1)
    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}"


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
    print(f"\nSummary: {len(targets)} | {ok} migrate | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail: sys.exit(1)


if __name__ == "__main__":
    main()
