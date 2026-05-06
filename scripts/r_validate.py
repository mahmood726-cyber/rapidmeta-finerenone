"""R metafor validation harness for the rapidmeta-finerenone corpus.

For each *_REVIEW.html with realData and at least 2 trials:
  1. Extract trials: name, tE, tN, cE, cN  (and publishedHR/CI when present)
  2. Build a CSV per topic: outputs/r_validation/csv/<topic>.csv
  3. Run R metafor pooling (REML + HKSJ + PI Cochrane v6.5 t_{k-1})
     primary scale = log(OR) from 2x2 (escalc measure="OR", to="if0all")
  4. Save outputs/r_validation/<topic>.json with:
       k, pooled_logOR, pooled_se, pooled_OR, ci_low, ci_high,
       tau2, tau2_se, I2, H2, Q, Qdf, Qp, PI_low, PI_high, hksj_floor_applied
  5. Build outputs/r_validation/index.json — manifest of all topics

Skip files with k<2 or no realData.

Usage:
  python scripts/r_validate.py            # full corpus
  python scripts/r_validate.py FILE1 ...  # subset
"""
from __future__ import annotations
import sys, io, re, json, csv, subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parent.parent
RSCRIPT = r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
OUTDIR = REPO / "outputs/r_validation"
CSVDIR = OUTDIR / "csv"
JSONDIR = OUTDIR
OUTDIR.mkdir(parents=True, exist_ok=True)
CSVDIR.mkdir(parents=True, exist_ok=True)

# Regex to capture trial 2x2 from realData entries
TRIAL_RE = re.compile(
    r"'(NCT\d{8})'\s*:\s*\{[^{}]*?"
    r"name:\s*'([^']+?)',[^{}]*?"
    r"(?:baseline:\s*\{[^{}]*?\}\s*,\s*[^{}]*?)?"
    r"tE:\s*([\d.eE+\-]+|null|None|NaN)\s*,[^{}]*?"
    r"tN:\s*([\d.eE+\-]+|null|None|NaN)\s*,[^{}]*?"
    r"cE:\s*([\d.eE+\-]+|null|None|NaN)\s*,[^{}]*?"
    r"cN:\s*([\d.eE+\-]+|null|None|NaN)",
    re.DOTALL,
)


def to_int(s):
    s = (s or "").strip()
    if s.lower() in ("null", "none", "nan", ""): return None
    try:
        v = float(s)
        return int(v)
    except (ValueError, TypeError):
        return None


def extract_trials(text):
    """Return list of dicts: name, tE, tN, cE, cN."""
    rows = []
    for m in TRIAL_RE.finditer(text):
        nct, name, tE, tN, cE, cN = m.groups()
        tE_i, tN_i, cE_i, cN_i = (to_int(x) for x in (tE, tN, cE, cN))
        if None in (tE_i, tN_i, cE_i, cN_i): continue
        if tN_i <= 0 or cN_i <= 0: continue
        if tE_i < 0 or cE_i < 0: continue
        if tE_i > tN_i or cE_i > cN_i: continue
        rows.append({"nct": nct, "name": name, "tE": tE_i, "tN": tN_i,
                     "cE": cE_i, "cN": cN_i})
    return rows


R_SCRIPT = r'''
suppressPackageStartupMessages({ library(metafor); library(jsonlite) })

args <- commandArgs(trailingOnly = TRUE)
csv_in <- args[1]
json_out <- args[2]

dat <- read.csv(csv_in, stringsAsFactors = FALSE)
k <- nrow(dat)

if (k < 2) {
  jsonlite::write_json(list(error = "k<2", k = k), json_out, auto_unbox = TRUE)
  quit(status = 0)
}

# escalc — log OR with continuity correction only when needed
es <- tryCatch(
  metafor::escalc(measure = "OR",
                  ai = tE, n1i = tN, ci = cE, n2i = cN,
                  data = dat, to = "only0", add = 0.5,
                  drop00 = FALSE),
  error = function(e) NULL
)
if (is.null(es) || all(is.na(es$yi))) {
  jsonlite::write_json(list(error = "escalc_failed", k = k), json_out, auto_unbox = TRUE)
  quit(status = 0)
}

# REML + HKSJ
res <- tryCatch(
  metafor::rma(yi = es$yi, vi = es$vi, method = "REML", test = "knha"),
  error = function(e) NULL
)
if (is.null(res)) {
  # Fallback DL if REML fails
  res <- tryCatch(
    metafor::rma(yi = es$yi, vi = es$vi, method = "DL", test = "knha"),
    error = function(e) NULL
  )
}
if (is.null(res)) {
  jsonlite::write_json(list(error = "rma_failed", k = k), json_out, auto_unbox = TRUE)
  quit(status = 0)
}

# HKSJ floor: max(1, Q/(k-1)) — metafor handles HKSJ but not the floor;
# we report whether floor would have applied.
Q <- as.numeric(res$QE)
df <- k - 1
phi <- max(1, Q / df)
hksj_floor_applied <- (Q < df)

# Prediction interval (Cochrane v6.5 t_{k-1}): pred() default in metafor uses k-2
# We compute t_{k-1} convention manually for repro alignment:
tau2 <- as.numeric(res$tau2)
se_b <- as.numeric(res$se)
b <- as.numeric(res$b)
tcrit <- qt(0.975, df = max(1, k - 1))
pi_se <- sqrt(tau2 + se_b^2)
PI_low <- b - tcrit * pi_se
PI_high <- b + tcrit * pi_se

# CI from rma (already HKSJ when test="knha")
ci_low <- as.numeric(res$ci.lb)
ci_high <- as.numeric(res$ci.ub)

out <- list(
  k = k,
  pooled_logOR = b,
  pooled_se = se_b,
  pooled_OR = exp(b),
  ci_low_OR = exp(ci_low),
  ci_high_OR = exp(ci_high),
  tau2 = tau2,
  I2 = as.numeric(res$I2),
  H2 = as.numeric(res$H2),
  Q = Q,
  Qdf = df,
  Qp = as.numeric(res$QEp),
  PI_low_OR = exp(PI_low),
  PI_high_OR = exp(PI_high),
  pi_df_convention = "t_{k-1}_Cochrane_v6.5",
  hksj_floor_applied = hksj_floor_applied,
  method = paste0(res$method, "+HKSJ"),
  trials = lapply(seq_len(k), function(i) list(
    name = dat$name[i],
    nct = dat$nct[i],
    tE = dat$tE[i], tN = dat$tN[i],
    cE = dat$cE[i], cN = dat$cN[i],
    yi = es$yi[i], vi = es$vi[i]
  ))
)
jsonlite::write_json(out, json_out, auto_unbox = TRUE, pretty = TRUE, digits = 6)
'''


_R_SCRIPT_PATH = OUTDIR / "_validate.R"
_R_SCRIPT_PATH.write_text(R_SCRIPT, encoding="utf-8")


def run_r(csv_path: Path, json_path: Path):
    proc = subprocess.run(
        [RSCRIPT, str(_R_SCRIPT_PATH), str(csv_path), str(json_path)],
        capture_output=True, text=True, timeout=60,
    )
    return proc.returncode, proc.stdout, proc.stderr


def topic_name(hp: Path):
    return hp.stem.replace("_REVIEW", "")


def main(argv):
    files = (
        [REPO / a for a in argv]
        if argv
        else sorted(REPO.glob("*_REVIEW.html"))
    )
    print(f"Validating {len(files)} files via R metafor 4.8.0 (REML+HKSJ) ...")

    manifest = []
    n_validated = 0
    n_skipped_lowK = 0
    n_failed = 0

    for hp in files:
        topic = topic_name(hp)
        text = hp.read_text(encoding="utf-8", errors="replace")
        trials = extract_trials(text)
        if len(trials) < 2:
            n_skipped_lowK += 1
            continue
        # Write CSV
        csv_path = CSVDIR / f"{topic}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["nct", "name", "tE", "tN", "cE", "cN"])
            w.writeheader()
            for r in trials:
                w.writerow(r)
        # Run R
        json_path = JSONDIR / f"{topic}.json"
        rc, _stdout, stderr = run_r(csv_path, json_path)
        if rc != 0 or not json_path.exists():
            n_failed += 1
            print(f"  FAIL {topic}: rc={rc} {stderr[:200]}")
            continue
        try:
            res = json.loads(json_path.read_text())
        except Exception as e:
            n_failed += 1
            print(f"  FAIL {topic}: parse {e}")
            continue
        if "error" in res:
            n_failed += 1
            continue
        n_validated += 1
        manifest.append({
            "topic": topic,
            "file": hp.name,
            "k": res["k"],
            "pooled_OR": res.get("pooled_OR"),
            "ci_low": res.get("ci_low_OR"),
            "ci_high": res.get("ci_high_OR"),
            "I2": res.get("I2"),
            "tau2": res.get("tau2"),
        })

    manifest.sort(key=lambda r: r["topic"])
    (OUTDIR / "index.json").write_text(json.dumps({
        "engine": "R 4.5.2 + metafor 4.8.0",
        "method": "REML + HKSJ + PI t_{k-1} (Cochrane v6.5)",
        "generated": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "n_validated": n_validated,
        "n_skipped_lowK": n_skipped_lowK,
        "n_failed": n_failed,
        "topics": manifest,
    }, indent=2))

    print(f"\n=== Summary ===")
    print(f"  Validated:   {n_validated}")
    print(f"  Skipped k<2: {n_skipped_lowK}")
    print(f"  Failed:      {n_failed}")
    print(f"  Manifest:    {OUTDIR / 'index.json'}")


if __name__ == "__main__":
    main(sys.argv[1:])
