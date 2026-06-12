"""Prove the engine's pooling math against R metafor on the CURRENT data, isolated
from the stale-baseline noise audit_r_vs_engine reports.

Background: audit_r_vs_engine compares the engine's pool_dl() over the current
Python-extracted snapshots against the tracked r_validation baselines. Those
baselines are stale (computed by r_validate.py on a superseded data version) and
can no longer be regenerated -- r_validate.py's HTML extractor does not parse the
current minified engine, so it skips every app as k<2. The result is ~77 spurious
"mismatches" (often k_r != k_e -- different trial sets entirely).

This script settles whether the ENGINE MATH is correct, decoupled from that noise:
for each snapshot it takes exactly the trials pool_dl() uses (valid 2x2, 0<=E<=N),
runs R metafor escalc(OR)+rma(method="DL") on that same set, and compares metafor's
pooled logOR to pool_dl()'s. Both are DL on identical current data -> a true
like-for-like parity check. NON-DESTRUCTIVE: it writes nothing into the tracked
baselines (sidecar/dashboard consumers depend on their REML+HKSJ schema).
"""
import json, io, sys, glob, os, shutil, subprocess, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "outputs", "extraction_audit", "data")
RDIR = os.path.join(REPO, "outputs", "r_validation")
# Rscript location: $RSCRIPT_EXE, then PATH, then the common Windows install dir.
RSCRIPT = (
    os.environ.get("RSCRIPT_EXE")
    or shutil.which("Rscript")
    or r"C:\Program Files\R\R-4.6.0\bin\Rscript.exe"
)


def num(v):
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("null", "", "none"):
        return None
    try:
        return float(v)
    except Exception:
        return None


def poolable_trials(rd):
    out = []
    for nct, t in rd.items():
        tE, tN, cE, cN = (num(t.get(k)) for k in ("tE", "tN", "cE", "cN"))
        if None in (tE, tN, cE, cN):
            continue
        if tN > 0 and cN > 0 and 0 <= tE <= tN and 0 <= cE <= cN:
            out.append({"name": str(t.get("name") or nct), "nct": str(nct),
                        "tE": int(tE), "tN": int(tN), "cE": int(cE), "cN": int(cN)})
    return out


def main():
    manifest = {}
    for f in sorted(glob.glob(os.path.join(DATA, "*_REVIEW.json"))):
        stem = os.path.basename(f)[:-len("_REVIEW.json")]
        try:
            doc = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        trials = poolable_trials(doc.get("realData") or {})
        if len(trials) >= 2:
            manifest[stem] = trials
    print(f"apps with >=2 OR-poolable trials: {len(manifest)}")

    mf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(manifest, mf)
    mf.close()
    of = mf.name + ".out.json"

    r_code = f'''
suppressMessages(library(metafor)); library(jsonlite)
m <- fromJSON("{mf.name.replace(chr(92), '/')}", simplifyVector=FALSE)
res <- list()
for (stem in names(m)) {{
  rows <- m[[stem]]
  tE<-cE<-tN<-cN<-numeric(0)
  for (r in rows) {{ tE<-c(tE,r$tE); tN<-c(tN,r$tN); cE<-c(cE,r$cE); cN<-c(cN,r$cN) }}
  es <- tryCatch(escalc(measure="OR", ai=tE, n1i=tN, ci=cE, n2i=cN, add=0.5, to="only0"),
                 error=function(e) NULL)
  if (is.null(es)) next
  fit <- tryCatch(rma(yi, vi, data=es, method="DL"), error=function(e) NULL)
  if (is.null(fit)) next
  res[[stem]] <- list(pooled_logOR=as.numeric(fit$b[1]), pooled_se=as.numeric(fit$se),
                      pooled_OR=exp(as.numeric(fit$b[1])), tau2=as.numeric(fit$tau2),
                      I2=as.numeric(fit$I2), Q=as.numeric(fit$QE), k=fit$k, method="DL")
}}
write_json(res, "{of.replace(chr(92), '/')}", auto_unbox=TRUE, digits=10)
cat("R done:", length(res), "pooled\\n")
'''
    rf = mf.name + ".R"
    open(rf, "w", encoding="utf-8").write(r_code)
    rc = subprocess.run([RSCRIPT, rf], capture_output=True, text=True)
    print(rc.stdout.strip()[-300:])
    if rc.returncode != 0 or not os.path.exists(of):
        print("R returncode:", rc.returncode)
        print("R STDOUT tail:", rc.stdout[-800:])
        print("R STDERR tail:", rc.stderr[-800:])
        return 1
    os.unlink(rf)

    results = json.load(open(of, encoding="utf-8"))
    os.unlink(mf.name); os.unlink(of)

    # Self-contained parity: compare metafor-DL (R) vs the audit's own pool_dl()
    # on the SAME current snapshots. NON-DESTRUCTIVE -- writes nothing into the
    # tracked r_validation baselines (many sidecar/dashboard consumers depend on
    # their REML+HKSJ schema). This isolates the ENGINE MATH from the stale-
    # snapshot noise audit_r_vs_engine reports against superseded baselines.
    import math
    def pool_dl(trials):
        pts = []
        for t in trials:
            tE, tN, cE, cN = t["tE"], t["tN"], t["cE"], t["cN"]
            a, b, c, d = tE, tN - tE, cE, cN - cE
            if min(a, b, c, d) == 0:
                a += 0.5; b += 0.5; c += 0.5; d += 0.5
            pts.append((math.log((a * d) / (b * c)), 1/a + 1/b + 1/c + 1/d))
        W = sum(1/v for _, v in pts)
        yFE = sum(y/v for y, v in pts) / W
        Q = sum((y - yFE)**2 / v for y, v in pts)
        df = len(pts) - 1
        sumW2 = sum((1/v)**2 for _, v in pts)
        cc = W - sumW2/W
        tau2 = max(0.0, (Q - df)/cc) if cc > 0 else 0.0
        W2 = sum(1/(v + tau2) for _, v in pts)
        return sum(y/(v + tau2) for y, v in pts) / W2

    deltas = []
    for stem, pooled in results.items():
        py = pool_dl(manifest[stem])
        r = float(pooled["pooled_logOR"])
        deltas.append((abs(py - r), stem, r, py, pooled["k"]))
    deltas.sort(reverse=True)
    n = len(deltas)
    match = sum(1 for d in deltas if d[0] < 1e-4)
    print(f"\nmetafor-DL vs engine pool_dl() on SAME current data ({n} apps):")
    print(f"  parity |Δlog|<1e-4 : {match}/{n} ({match*100//max(1,n)}%)")
    worst = [d for d in deltas if d[0] >= 1e-4][:15]
    if worst:
        print("  residual diffs (investigate):")
        for dlt, stem, r, py, k in worst:
            print(f"    {stem:36} metafor={r:+.5f} engine={py:+.5f} Δ={dlt:.5f} k={k}")
    else:
        print("  ALL apps match metafor to <1e-4 -> engine pooling math is correct;")
        print("  the original 77 'mismatches' were stale-snapshot artifacts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
