"""Apply the ctgov recheck verdicts to the suspect apps' realData.

For every trial flagged by scripts/ctgov_recheck_counts.py:
  FIXABLE_BINARY + clean ctgov 2x2  -> overwrite tE/tN/cE/cN with source counts
  everything else (single-arm, continuous, ambiguous, no-results) -> NULL the
      tE/tN/cE/cN (and any negative publishedHR) so the trial is honestly
      non-poolable instead of carrying fabricated/impossible numbers.

Safety:
  * edits ONLY the numeric values of tE/tN/cE/cN/publishedHR inside the exact
    span of the target trial object -- never reformats the block, never adds keys.
  * idempotent (re-running is a no-op once applied).
  * refuses to touch any app in BENCHMARK_PROTECT (curated/benchmarked apps).
  * re-reads each file with the validator parser afterwards and reverts the file
    if realData no longer parses.
  * --dry-run by default; --apply to write.
"""
from __future__ import annotations
import argparse, io, json, re, sys, importlib.util
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
CACHE = HERE / "outputs" / "ctgov_cache"
REPORT = HERE / "outputs" / "ctgov_recheck_report.json"

sys.path.insert(0, str(HERE / "scripts"))
from _ctgov_extract import extract_2x2  # noqa: E402

_spec = importlib.util.spec_from_file_location("vv", HERE / "validate_living_ma_portfolio.py")
vv = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(vv)

# Never edit curated/benchmarked flagship apps.
BENCHMARK_PROTECT = set(vv.BENCHMARKS.keys()) if hasattr(vv, "BENCHMARKS") else set()


def _trial_span(html, nct):
    """Return (start, end) of the `"NCT…": { … }` object in the realData block."""
    rd = html.find("realData:")
    if rd < 0:
        return None
    m = re.search(rf'["\']{re.escape(nct)}["\']\s*:\s*\{{', html[rd:])
    if not m:
        return None
    obj_start = rd + m.end() - 1  # at the '{'
    depth = 0
    for k in range(obj_start, len(html)):
        if html[k] == "{":
            depth += 1
        elif html[k] == "}":
            depth -= 1
            if depth == 0:
                return (rd + m.start(), k + 1)
    return None


def _set_field(span_text, field, value):
    """Replace `field: <num|null>` value inside one trial object's text."""
    val = "null" if value is None else str(int(value) if float(value).is_integer() else value)
    pat = re.compile(rf'(["\']?{field}["\']?\s*:\s*)(-?[\d.]+|null)')
    new, n = pat.subn(rf'\g<1>{val}', span_text, count=1)
    return new if n else span_text


def apply_to_html(html, nct, counts):
    """counts = dict(tE,tN,cE,cN) or None (=null all). Returns new html or None."""
    span = _trial_span(html, nct)
    if not span:
        return None
    s, e = span
    body = html[s:e]
    new_body = body
    fields = {"tE": None, "tN": None, "cE": None, "cN": None} if counts is None else counts
    for f, v in fields.items():
        new_body = _set_field(new_body, f, v)
    # also clear a negative publishedHR (the MD-in-HR artefact) when nulling
    if counts is None and re.search(r'publishedHR["\']?\s*:\s*-[\d.]', new_body):
        new_body = _set_field(new_body, "publishedHR", None)
    if new_body == body:
        return html  # nothing changed (idempotent)
    return html[:s] + new_body + html[e:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rep = json.loads(REPORT.read_text(encoding="utf-8"))
    rows = rep["results"]
    if args.limit:
        rows = rows[:args.limit]

    stats = {"fixed": 0, "nulled": 0, "skipped_protected": 0, "no_span": 0, "parse_revert": 0, "files": set()}
    by_file = {}
    for r in rows:
        app = r["app"]
        stem = app.replace("_REVIEW.html", "").replace(".html", "")
        base = stem.split("_AUTO")[0]
        if any(base.startswith(b) or b == base for b in BENCHMARK_PROTECT):
            stats["skipped_protected"] += 1
            continue
        counts = None
        if r["verdict"] == "FIXABLE_BINARY":
            cf = CACHE / f"{r['nct']}.json"
            if cf.exists():
                got = extract_2x2(json.loads(cf.read_text(encoding="utf-8")))
                if got:
                    counts = {k: got[k] for k in ("tE", "tN", "cE", "cN")}
        by_file.setdefault(app, []).append((r["nct"], counts))

    for app, edits in by_file.items():
        p = HERE / app
        if not p.exists():
            continue
        html = p.read_text(encoding="utf-8", errors="replace")
        orig = html
        local_fixed = local_nulled = 0
        for nct, counts in edits:
            new = apply_to_html(html, nct, counts)
            if new is None:
                stats["no_span"] += 1
                continue
            if new != html:
                html = new
                if counts is None:
                    local_nulled += 1
                else:
                    local_fixed += 1
        if html != orig:
            # validate: realData must still parse and contain trials
            if not vv.extract_real_data(html):
                stats["parse_revert"] += 1
                continue
            stats["fixed"] += local_fixed
            stats["nulled"] += local_nulled
            stats["files"].add(app)
            if args.apply:
                p.write_text(html, encoding="utf-8")

    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}:")
    print(f"  trials fixed (source counts): {stats['fixed']}")
    print(f"  trials nulled (honest non-poolable): {stats['nulled']}")
    print(f"  protected (benchmarked) skipped: {stats['skipped_protected']}")
    print(f"  no span found: {stats['no_span']}   parse-revert (file skipped): {stats['parse_revert']}")
    print(f"  files touched: {len(stats['files'])}")


if __name__ == "__main__":
    main()
