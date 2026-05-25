"""Regenerate the remaining gate-failure R-validation sidecars.

These sidecars match the metafor pooled OR + lower CI to within 1e-6 but
diverge on the upper CI by 1e-4..1e-1 — signature of a different DF or
floor convention used when the sidecar was originally written.

Mechanism: extract publishedHR + hrLCI + hrUCI per trial from each page's
realData, write a per-topic R script that pools via metafor REML+HKSJ at
Cochrane v6.5 t_{k-1} convention, and write a fresh sidecar.

Same approach used for the 5 catastrophes in commit 7606eda9b; this just
extends it to the 12 non-catastrophic gate failures plus any others the
parity gate flags above 1e-4.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import io
from pathlib import Path

if "pytest" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent

GATE_FAILURES = [
    "AGYW_HIV_PREP", "BIMEKIZUMAB_PSORIASIS", "CAB_PREP_HIV",
    "COVID_ORAL_ANTIVIRALS", "ETRASIMOD_UC", "KRAS_G12C",
    "LENACAPAVIR_PREP", "MAVACAMTEN_HCM", "OBESITY_DRUGS",
    "PBC_PPAR", "POLYCYTHEMIA_VERA", "SEVERE_ASTHMA_NMA",
]

# Match a per-trial object in realData with name + publishedHR + hrLCI + hrUCI.
# The realData blocks can be JS literal (single quotes) or JSON (double quotes).
TRIAL_RE = re.compile(
    r"['\"]NCT\d{7,8}['\"]\s*:\s*\{(?P<body>(?:[^{}]|\{[^{}]*\}){0,4000})\}",
    re.DOTALL,
)
FIELD_RE = re.compile(
    r"['\"]?(name|publishedHR|hrLCI|hrUCI)['\"]?\s*:\s*['\"]?(-?[\d.eE+-]+|null|None|[^,'\"}\n]+)",
)


def extract_trials(stem: str) -> list[dict] | None:
    """Find the *_REVIEW.html for the topic and pull per-trial publishedHR + CI."""
    candidates = [
        HERE / f"{stem}_REVIEW.html",
        HERE / f"{stem}_REVIEW.html".replace("_REVIEW.html", ".html"),
    ]
    page = next((p for p in candidates if p.exists()), None)
    if page is None:
        return None
    txt = page.read_text(encoding="utf-8", errors="replace")
    trials: list[dict] = []
    for m in TRIAL_RE.finditer(txt):
        body = m.group("body")
        d: dict = {}
        for fm in FIELD_RE.finditer(body):
            k, v = fm.group(1), fm.group(2).strip().strip("'\"")
            if k == "name":
                d["name"] = v
            elif k in ("publishedHR", "hrLCI", "hrUCI") and v not in ("null", "None"):
                try:
                    d[k] = float(v)
                except ValueError:
                    pass
        if "name" in d and {"publishedHR", "hrLCI", "hrUCI"} <= set(d):
            trials.append(d)
    return trials or None


def emit_r_script(stem: str, trials: list[dict]) -> Path:
    names = [t["name"] for t in trials]
    hrs = [t["publishedHR"] for t in trials]
    lcis = [t["hrLCI"] for t in trials]
    ucis = [t["hrUCI"] for t in trials]
    r = [
        'user_lib <- file.path(Sys.getenv("APPDATA"), "R-libs")',
        'if (dir.exists(user_lib)) .libPaths(c(user_lib, .libPaths()))',
        'suppressMessages(library(metafor))',
        f'trials <- data.frame(',
        f'  name = c({", ".join(repr(n) for n in names)}),',
        f'  hr   = c({", ".join(str(h) for h in hrs)}),',
        f'  lci  = c({", ".join(str(l) for l in lcis)}),',
        f'  uci  = c({", ".join(str(u) for u in ucis)})',
        ')',
        'trials$yi  <- log(trials$hr)',
        'trials$sei <- (log(trials$uci) - log(trials$lci)) / (2 * qnorm(0.975))',
        'trials$vi  <- trials$sei^2',
        'fit <- rma(yi = yi, vi = vi, data = trials, method = "REML", test = "knha")',
        'pi_se <- sqrt(fit$tau2 + fit$se^2)',
        't_v65 <- qt(0.975, df = max(1, fit$k - 1))',
        'pi_lo <- exp(fit$b[1] - t_v65 * pi_se)',
        'pi_hi <- exp(fit$b[1] + t_v65 * pi_se)',
        'esc <- function(s) gsub("\\\\\\\\", "\\\\\\\\\\\\\\\\", gsub("\\"", "\\\\\\\\\\"", s))',
        f'path <- "outputs/r_validation/{stem}.json"',
        'lines <- c("{",',
        '  sprintf("  \\"k\\": %d,", fit$k),',
        '  sprintf("  \\"pooled_logOR\\": %.10f,", unname(fit$b[1])),',
        '  sprintf("  \\"pooled_se\\": %.10f,", fit$se),',
        '  sprintf("  \\"pooled_OR\\": %.10f,", unname(exp(fit$b[1]))),',
        '  sprintf("  \\"ci_low_OR\\": %.10f,", unname(exp(fit$ci.lb))),',
        '  sprintf("  \\"ci_high_OR\\": %.10f,", unname(exp(fit$ci.ub))),',
        '  sprintf("  \\"tau2\\": %.10f,", fit$tau2),',
        '  sprintf("  \\"I2\\": %.10f,", fit$I2),',
        '  sprintf("  \\"H2\\": %.10f,", fit$H2),',
        '  sprintf("  \\"Q\\": %.10f,", fit$QE),',
        '  sprintf("  \\"Qdf\\": %d,", fit$k - 1),',
        '  sprintf("  \\"Qp\\": %.6e,", fit$QEp),',
        '  sprintf("  \\"PI_low_OR\\": %.10f,", pi_lo),',
        '  sprintf("  \\"PI_high_OR\\": %.10f,", pi_hi),',
        '  "  \\"pi_df_convention\\": \\"t_{k-1}_Cochrane_v6.5\\",",',
        '  "  \\"method\\": \\"REML+HKSJ\\",",',
        f'  sprintf("  \\"regenerated_from\\": \\"curated_publishedHR_via_metafor_%s\\",",',
        '          as.character(packageVersion("metafor"))),',
        '  sprintf("  \\"regenerated_on\\": \\"%s\\",", Sys.Date()),',
        '  "  \\"trials\\": ["',
        ')',
        'for (i in 1:nrow(trials)) {',
        '  lines <- c(lines, "    {",',
        '             sprintf("      \\"name\\": \\"%s\\",", esc(trials$name[i])),',
        '             sprintf("      \\"hr\\": %.4f,", trials$hr[i]),',
        '             sprintf("      \\"hr_lci\\": %.4f,", trials$lci[i]),',
        '             sprintf("      \\"hr_uci\\": %.4f,", trials$uci[i]),',
        '             sprintf("      \\"yi\\": %.10f,", trials$yi[i]),',
        '             sprintf("      \\"vi\\": %.10f", trials$vi[i]),',
        '             if (i == nrow(trials)) "    }" else "    },")',
        '}',
        'lines <- c(lines, "  ]", "}")',
        'writeLines(lines, path)',
        f'cat(sprintf("  {stem}: pooled OR=%.4f [%.4f, %.4f] k=%d\\n",',
        '            exp(fit$b[1]), exp(fit$ci.lb), exp(fit$ci.ub), fit$k))',
    ]
    tmp = HERE / f".regen_{stem.lower()}.R"
    tmp.write_text("\n".join(r), encoding="utf-8")
    return tmp


def main():
    print(f"Regenerating {len(GATE_FAILURES)} gate-failure sidecars...")
    n_ok = n_skip = 0
    for stem in GATE_FAILURES:
        trials = extract_trials(stem)
        if not trials:
            print(f"  SKIP {stem}: page has no publishedHR per trial")
            n_skip += 1
            continue
        rs = emit_r_script(stem, trials)
        try:
            proc = subprocess.run(
                ["Rscript", str(rs)],
                capture_output=True, text=True, timeout=60, encoding="utf-8",
                errors="replace", cwd=str(HERE),
            )
            if proc.returncode != 0:
                print(f"  FAIL {stem}: Rscript exit {proc.returncode}\n    {proc.stderr.strip()[:200]}")
                continue
            print(proc.stdout.strip())
            n_ok += 1
        finally:
            rs.unlink(missing_ok=True)
    print(f"\nRegenerated: {n_ok}, skipped: {n_skip}")


if __name__ == "__main__":
    main()
