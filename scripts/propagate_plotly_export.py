#!/usr/bin/env python3
"""Inject the Plotly SVG + 300-DPI PNG export modebar buttons into every
RapidMeta _REVIEW.html. Idempotent — skips if `__rmExportPatched` already
present. Anchors on `const KNOWN_TRIAL_ALIASES = {` which is universal across
all apps in the portfolio.

Usage:
    python scripts/propagate_plotly_export.py --dry-run
    python scripts/propagate_plotly_export.py --apply
"""
import argparse, pathlib, sys

ROOT = pathlib.Path(r"C:\Projects\Finrenone")

ANCHOR = "        const KNOWN_TRIAL_ALIASES = {"

PATCH = (
    "        /* ── Plotly export hook: every chart gets SVG + 300-DPI PNG buttons in\n"
    "           the modebar so reviewers can grab journal-ready figures. The apps\n"
    "           historically passed `displayModeBar: false` to suppress the toolbar;\n"
    "           we override that so our buttons are always visible. SVG is the\n"
    "           lossless path for journals that demand TIFF/EPS — convert in\n"
    "           Inkscape/Illustrator. ── */\n"
    "        (function installPlotlyExportButtons() {\n"
    "            if (typeof Plotly === 'undefined' || Plotly.__rmExportPatched) return;\n"
    "            const _origNewPlot = Plotly.newPlot;\n"
    "            const _origReact   = Plotly.react;\n"
    "            const buildButtons = (gd) => ([\n"
    "                {\n"
    "                    name: 'Download SVG (lossless)',\n"
    "                    title: 'Download SVG (lossless — best for journal submission)',\n"
    "                    icon: Plotly.Icons.disk,\n"
    "                    click: function (g) {\n"
    "                        const fn = (g && g.id) ? g.id.replace(/[^a-z0-9_-]+/gi, '_') : 'figure';\n"
    "                        Plotly.downloadImage(g, { format: 'svg', filename: fn, height: g.layout?.height || 600, width: g.layout?.width || 900 });\n"
    "                    }\n"
    "                },\n"
    "                {\n"
    "                    name: 'Download PNG @ 300 DPI',\n"
    "                    title: 'Download PNG at ~300 DPI (4x scale) — journal-quality raster',\n"
    "                    icon: Plotly.Icons.camera,\n"
    "                    click: function (g) {\n"
    "                        const fn = (g && g.id) ? g.id.replace(/[^a-z0-9_-]+/gi, '_') : 'figure';\n"
    "                        Plotly.downloadImage(g, { format: 'png', scale: 4, filename: fn, height: g.layout?.height || 600, width: g.layout?.width || 900 });\n"
    "                    }\n"
    "                }\n"
    "            ]);\n"
    "            const enrich = (cfg) => Object.assign({}, cfg || {}, {\n"
    "                displayModeBar: true,             /* override any displayModeBar:false in caller */\n"
    "                displaylogo: false,\n"
    "                modeBarButtonsToRemove: ['toImage'], /* drop Plotly's default low-res PNG; ours replace it */\n"
    "                modeBarButtonsToAdd: buildButtons(),\n"
    "                responsive: cfg?.responsive !== false\n"
    "            });\n"
    "            Plotly.newPlot = function (gd, data, layout, config) { return _origNewPlot.call(this, gd, data, layout, enrich(config)); };\n"
    "            Plotly.react   = function (gd, data, layout, config) { return _origReact.call(this, gd, data, layout, enrich(config)); };\n"
    "            Plotly.__rmExportPatched = true;\n"
    "        })();\n"
    "\n"
)


def apply_to_file(path: pathlib.Path, dry_run: bool) -> str:
    text = path.read_text(encoding="utf-8", newline="")
    if "__rmExportPatched" in text:
        return f"SKIP {path.name}: already-migrated"
    crlf = "\r\n" in text
    work = text.replace("\r\n", "\n") if crlf else text
    if work.count(ANCHOR) != 1:
        return f"FAIL {path.name}: anchor matched {work.count(ANCHOR)} times (expected 1)"
    work = work.replace(ANCHOR, PATCH + ANCHOR, 1)
    if not dry_run:
        out = work.replace("\n", "\r\n") if crlf else work
        path.write_text(out, encoding="utf-8", newline="")
    return f"OK   {path.name}: +{len(work) - len(text.replace(chr(13)+chr(10), chr(10)) if crlf else text)} chars"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    targets = sorted(ROOT.glob("*_REVIEW.html"))
    ok = skip = fail = 0
    for p in targets:
        result = apply_to_file(p, dry_run=args.dry_run)
        if result.startswith("OK"): ok += 1
        elif result.startswith("SKIP"): skip += 1
        else: fail += 1
        if result.startswith(("FAIL", "SKIP")) or args.dry_run:
            print(result)
    print(f"\nSummary: {len(targets)} files | {ok} migrate | {skip} skip | {fail} fail | mode={'dry-run' if args.dry_run else 'apply'}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
