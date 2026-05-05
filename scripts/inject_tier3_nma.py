"""Codemod: inject Tier-3 NMA error-detection methods into NMA reviews.

Adds three new vendor modules to all 20 *_NMA_REVIEW.html files:
  - vendor/poth.js                — Wigle 2025 hierarchy precision
  - vendor/q-decomposition.js     — Krahn-König 2013 within/between Q
  - vendor/contribution-matrix.js — Papakonstantinou 2018 evidence streams

Idempotent. Skips files already containing `vendor/q-decomposition.js`.

Inserts script tags after vendor/cinema-certainty.js and adds three
buttons to the existing Bias & Certainty panel (so we don't proliferate
panels — they're conceptually all NMA validity diagnostics).
"""
from __future__ import annotations
import sys, io, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path("C:/Projects/Finrenone")

SCRIPT_TAGS = (
    '\n    <!-- Tier-3 NMA error-detection (Wigle 2025 POTH; Krahn 2013 Q-decomp; Papakonstantinou 2018 contribution) -->\n'
    '    <script src="vendor/poth.js"></script>\n'
    '    <script src="vendor/q-decomposition.js"></script>\n'
    '    <script src="vendor/contribution-matrix.js"></script>\n'
)

CINEMA_INCLUDE_RE = re.compile(r'<script\s+src="vendor/cinema-certainty\.js"\s*></script>')
HEAD_CLOSE_RE = re.compile(r'</head>')

# Existing landmark: the row of 3 buttons in the Bias & Certainty panel.
# We append 3 more buttons after the CINeMA button.
EXISTING_BUTTON_ROW = re.compile(
    r'(<button id="biasCinemaBtn"[^>]*>CINeMA certainty</button>)'
)

NEW_BUTTONS = (
    r'\1\n'
    '                                    <button id="biasPothBtn" class="px-4 py-2 text-xs font-bold bg-pink-600 hover:bg-pink-500 text-white rounded">POTH</button>\n'
    '                                    <button id="biasQdecompBtn" class="px-4 py-2 text-xs font-bold bg-orange-600 hover:bg-orange-500 text-white rounded">Q decomposition</button>\n'
    '                                    <button id="biasContribBtn" class="px-4 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white rounded">Contribution matrix</button>'
)

# We also need to wire the three new handlers. Append a script block AFTER
# the existing inline IIFE in the bias panel.
EXISTING_INLINE_END = re.compile(
    r'(\}\)\(\);\s*</script>\s*\n)(\s*</div>\s*\n\s*</div>\s*\n\s*</div>)?'
)

NEW_HANDLERS = '''
                            <script>
                            (function () {
                                function getCfgAndData() {
                                    return {
                                        cfg: window.NMA_CONFIG,
                                        rd: window.RapidMeta && window.RapidMeta.realData,
                                    };
                                }

                                function showError(msg) {
                                    document.getElementById('biasOutput').innerHTML =
                                        '<div style="color:#f87171;font-size:12px;padding:1em;">' + msg + '</div>';
                                }

                                function runPoth() {
                                    var ctx = getCfgAndData();
                                    if (!ctx.cfg) return showError('Need NMA_CONFIG.');
                                    if (!window.POTH) return showError('POTH module not loaded.');
                                    // Build approximate SUCRA from network fits via NMAEngine if available.
                                    // Fall back to assigning equal SUCRA if no engine output.
                                    var treatments = (ctx.cfg.treatments || []).map(function (t) {
                                        var s = 0.5;
                                        try {
                                            if (window.NMAEngine && window.NMAEngine.computePScores) {
                                                var ps = window.NMAEngine.computePScores();
                                                if (ps && ps[t] != null) s = ps[t];
                                            }
                                        } catch (e) {}
                                        return { treatment: t, sucra: s };
                                    });
                                    var ranko = window.POTH.fromSUCRA(treatments);
                                    var res = window.POTH.compute(ranko);
                                    var div = document.getElementById('biasOutput');
                                    div.innerHTML = '<h4 style="color:#f9a8d4;font-size:13px;font-weight:700;margin-bottom:8px;">POTH (Precision Of Treatment Hierarchy, Wigle 2025)</h4><div id="biasPothInner"></div>';
                                    window.POTH.render('biasPothInner', res, { fromSucra: true });
                                }

                                function runQdecomp() {
                                    var ctx = getCfgAndData();
                                    if (!ctx.rd || !ctx.cfg) return showError('Need realData + NMA_CONFIG.');
                                    if (!window.QDecomposition) return showError('QDecomposition module not loaded.');
                                    var measure = document.getElementById('biasMeasure').value;
                                    var res = window.QDecomposition.compute(ctx.rd, ctx.cfg, { measure: measure });
                                    var div = document.getElementById('biasOutput');
                                    div.innerHTML = '<h4 style="color:#fb923c;font-size:13px;font-weight:700;margin-bottom:8px;">Q decomposition: heterogeneity vs inconsistency (Krahn-König 2013)</h4><div id="biasQdecompInner"></div>';
                                    window.QDecomposition.render('biasQdecompInner', res);
                                }

                                function runContrib() {
                                    var ctx = getCfgAndData();
                                    if (!ctx.rd || !ctx.cfg) return showError('Need realData + NMA_CONFIG.');
                                    if (!window.ContributionMatrix) return showError('ContributionMatrix module not loaded.');
                                    var measure = document.getElementById('biasMeasure').value;
                                    var res = window.ContributionMatrix.compute(ctx.rd, ctx.cfg, { measure: measure });
                                    var div = document.getElementById('biasOutput');
                                    div.innerHTML = '<h4 style="color:#6ee7b7;font-size:13px;font-weight:700;margin-bottom:8px;">Contribution matrix (Papakonstantinou 2018)</h4><div id="biasContribInner"></div>';
                                    window.ContributionMatrix.render('biasContribInner', res);
                                }

                                document.addEventListener('DOMContentLoaded', function () {
                                    var p = document.getElementById('biasPothBtn');
                                    var q = document.getElementById('biasQdecompBtn');
                                    var c = document.getElementById('biasContribBtn');
                                    if (p) p.addEventListener('click', runPoth);
                                    if (q) q.addEventListener('click', runQdecomp);
                                    if (c) c.addEventListener('click', runContrib);
                                });
                            })();
                            </script>
'''


def patch(text):
    if 'vendor/q-decomposition.js' in text:
        return text, "ALREADY"
    cinema = CINEMA_INCLUDE_RE.search(text)
    if cinema:
        text = text[:cinema.end()] + SCRIPT_TAGS + text[cinema.end():]
    else:
        head = HEAD_CLOSE_RE.search(text)
        if not head:
            return text, "NO_HEAD"
        text = text[:head.start()] + SCRIPT_TAGS + text[head.start():]

    btn_match = EXISTING_BUTTON_ROW.search(text)
    if not btn_match:
        return text, "NO_BUTTON_ROW"
    text = EXISTING_BUTTON_ROW.sub(NEW_BUTTONS, text, count=1)

    # Inject the new handler block right AFTER the Tier-2 IIFE closes.
    # The unique landmark is the line that wires biasCinemaBtn:
    #   if (c) c.addEventListener('click', runCinema);
    # followed shortly by the IIFE close `})();</script>`.
    TIER2_IIFE_END = re.compile(
        r"(if \(c\) c\.addEventListener\('click', runCinema\);\s*\n\s*\}\);\s*\n\s*\}\)\(\);\s*\n\s*</script>)",
        re.MULTILINE,
    )
    new_text, n = TIER2_IIFE_END.subn(r'\1' + NEW_HANDLERS, text, count=1)
    if n == 0:
        return text, "NO_HANDLER_INSERTION_POINT"
    return new_text, "PATCHED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(REPO.glob("*_NMA_REVIEW.html"))
    print(f"Patching {len(files)} *_NMA_REVIEW.html files ...")

    counts = {"PATCHED": 0, "ALREADY": 0, "NO_HEAD": 0, "NO_BUTTON_ROW": 0, "NO_HANDLER_INSERTION_POINT": 0}
    for hp in files:
        text = hp.read_text(encoding="utf-8", errors="replace")
        new_text, status = patch(text)
        counts[status] = counts.get(status, 0) + 1
        if status == "PATCHED":
            print(f"  PATCH    {hp.name}")
            if not args.dry_run:
                hp.write_text(new_text, encoding="utf-8")
        elif status != "ALREADY":
            print(f"  {status}  {hp.name}")

    print(f"\n=== Summary ===")
    for k, v in counts.items():
        print(f"  {k:30s} {v}")
    if args.dry_run:
        print("  DRY RUN — no files written.")


if __name__ == "__main__":
    main()
