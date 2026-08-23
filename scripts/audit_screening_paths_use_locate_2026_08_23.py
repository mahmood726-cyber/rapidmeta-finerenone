"""Which inclusion-deciding paths route through `topic_identity.locate()`, and which do not.

# no-control: routed through require_controls. POSITIVE is
# `consolidate_ablation_medical_screen_2026_08_19.py` -- the screener that produced 6 of the 9
# wrong decisions -- which must be found as an inclusion-decider. NEGATIVE is
# `instrument_controls.py`, which decides nothing about inclusion and must not be listed.

THE DEFECT THIS ENUMERATES THE EXPOSURE FOR. 1,939 persisted screening decisions were checked
against their source text: 1,930 correct, 9 wrong, 0 with unlocatable provenance. All nine are
one class and all nine ADD a trial that should not be there:

    BOTH ARMS RECEIVE THE INTERVENTION, AND THE RANDOMISED CONTRAST IS SOMETHING ELSE.

    NCT07389941  "Catheter ablation for AF plus semaglutide" vs "Catheter ablation for AF and
                 no GLP-1 receptor therapy" -- EVERY patient is ablated. The contrast is
                 semaglutide. Stored ELIGIBLE in an ablation-versus-medical-therapy review.

Six of 621 in `ablation_medical`, three of 551 in `rhythm_control`. The other eight screening
outputs are clean at 703 of 703.

THE DISCRIMINATOR ALREADY EXISTS AND IS NOT A NEW ONE. `ssot/topic_identity.py:369` records
the EASi-HF case verbatim -- vicadrostat/empagliflozin against placebo/empagliflozin, with
empagliflozin scored experimental because it APPEARS in an experimental arm while being given
to everyone -- and measures 7 of 43 trials on sglt2-hf, a 16% overcount in the adding
direction, on exactly the add-on designs that dominate modern cardiology. `locate()` was
reframed on 2026-08-19 to ask WHAT WAS RANDOMISED rather than WHERE THE TOPIC DRUG APPEARS.

WRITING A SECOND DISCRIMINATOR IS HOW `dual_screening` AND `duplicate_screening` HAPPENED.
This audit therefore does not propose one; it finds which deciders bypass the one that exists.

TWO OF TEN OUTPUTS WERE FOUND BECAUSE SOMEONE AUDITED TWO FILES. THE KNOWN DEFECT IS NEVER THE
POPULATION -- sixth time today.
"""
from __future__ import annotations

import ast
import glob
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "screening_paths_locate_2026_08_23.json")

# A file DECIDES INCLUSION when it writes an eligibility verdict.
DECIDES = re.compile(
    r"(?:ELIGIBLE_NO_RESULTS_YET|[\"']ELIGIBLE[\"']|[\"']INCLUDE[\"']|[\"']EXCLUDE[\"']|"
    r"screening_decision|eligibility_verdict|\bdecision\b\s*[:=]\s*[\"'](?:in|out|eligible))")
# It ROUTES CORRECTLY when it reaches topic_identity.locate().
USES_LOCATE = re.compile(r"topic_identity|from\s+topic_identity|\blocate\s*\(")


def files():
    for pat in ("scripts/*.py", "ssot/*.py"):
        for p in sorted(glob.glob(os.path.join(REPO, pat))):
            yield p


def classify(path):
    try:
        src = io.open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    # Strings and comments count for DECIDES (the verdict is a literal), but `locate` must be
    # a real call, not a mention -- the same distinction that cost the arm-role lint five
    # false positives when it matched its own docstring.
    if not DECIDES.search(src):
        return None
    calls_locate = False
    try:
        tree = ast.parse(src)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                nm = (f.attr if isinstance(f, ast.Attribute)
                      else f.id if isinstance(f, ast.Name) else "")
                if nm == "locate":
                    calls_locate = True
                    break
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                mods = [a.name for a in n.names] + [getattr(n, "module", "") or ""]
                if any("topic_identity" in str(m) for m in mods):
                    calls_locate = True
    except SyntaxError:
        calls_locate = bool(USES_LOCATE.search(src))
    return calls_locate


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    rows = {}
    for p in files():
        v = classify(p)
        if v is None:
            continue
        rows[os.path.relpath(p, REPO).replace("\\", "/")] = v

    ctrl = "scripts/consolidate_ablation_medical_screen_2026_08_19.py"
    require_controls(
        "screening_paths_use_locate",
        ("the ablation screener that produced 6 of the 9 wrong decisions is found as an "
         "inclusion-decider", ctrl in rows, True),
        ("instrument_controls.py decides no inclusion and is not listed",
         "scripts/instrument_controls.py" in rows, True))

    uses = sorted(k for k, v in rows.items() if v)
    bypass = sorted(k for k, v in rows.items() if not v)

    print("")
    print("PATHS THAT DECIDE INCLUSION: %d" % len(rows))
    print("")
    print("   route through topic_identity.locate()   %3d   %5.1f%%"
          % (len(uses), 100.0 * len(uses) / max(1, len(rows))))
    print("   BYPASS it                               %3d   %5.1f%%"
          % (len(bypass), 100.0 * len(bypass) / max(1, len(rows))))
    print("")
    print("   BYPASSING, BY NAME:")
    for k in bypass[:40]:
        print("      %s" % k)
    if len(bypass) > 40:
        print("      ... and %d more" % (len(bypass) - 40))
    print("")
    print("THE DISCRIMINATOR EXISTS AND IS CORRECT ON THIS SHAPE. `locate()` asks what was")
    print("RANDOMISED, not where the topic drug appears, and it already measures a 16%")
    print("overcount in the adding direction on sglt2-hf. Every path above that bypasses it")
    print("is deciding inclusion by some other rule, and two of ten were found only because")
    print("somebody audited two files.")
    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    json.dump({"deciders": rows, "uses_locate": uses, "bypass": bypass},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("")
    print("written: %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
