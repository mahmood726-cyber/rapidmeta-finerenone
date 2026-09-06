# -*- coding: utf-8 -*-
"""extract_effect_ci.py -- generic EXTRACT: a published effect estimate + CI is a POOLABLE input.

The gap the SGLT2 loop exposed: extraction is per-review (~30 bespoke `extract_*` scripts, no
generic home), so every "a published effect IS poolable" fix (cangrelor, bococizumab, DELIVER) had
to be re-learned per review. This is the single home for that class.

A trial that reports only a model-adjusted HR with a CI -- and no 2x2 counts -- is NOT unpoolable.
Its effect+CI IS a poolable input: on the log scale, y=log(point), se=(log(hi)-log(lo))/(2*1.96).
This component turns such a statement into a record the synthesise engine reads alongside
counts-derived effects, and REFUSES a statement that cannot be a valid effect (CI not bracketing the
point, ratio measure <= 0, disordered CI) -- because a silently-wrong poolable input corrupts the
pool with no error.

Provenance is mandatory: every emitted record carries the source quote, an identifier (PMID/NCT),
and the extraction method. Deterministic parsing (regex) needs no model; if a model read a table
into arms, that is a separate recorded decision with prompt/model-id/date -- not done here.

Written in-tree (Codex cannot write files in this sandbox).
"""
from __future__ import annotations
import io, re, math, sys, json

Z = 1.959963985
RATIO_MEASURES = {"HR": "log_HR", "RR": "log_RR", "OR": "log_OR"}
DIFF_MEASURES = {"MD": "MD", "RD": "RD"}
ALL_MEASURES = dict(RATIO_MEASURES, **DIFF_MEASURES)

# "HR 0.80 (95% CI 0.71-0.91)", "HR 0.80 (0.71 to 0.91)", "OR 1.24 (95%CI 1.01, 1.52)"
_NUM = r"[-+]?\d+(?:\.\d+)?"
_EFFECT = re.compile(
    r"\b(HR|RR|OR|MD|RD)\b[^0-9\-+]{0,12}(" + _NUM + r")\s*"
    r"\(?\s*(?:95\s*%?\s*CI[:\s]*)?(" + _NUM + r")\s*(?:to|[-,–−])\s*(" + _NUM + r")\s*\)?",
    re.I)


def parse_effect_string(s):
    """Return (measure_token, point, lo, hi) from a free-text effect statement, or None."""
    m = _EFFECT.search(s or "")
    if not m:
        return None
    tok = m.group(1).upper()
    point, lo, hi = float(m.group(2)), float(m.group(3)), float(m.group(4))
    return tok, point, lo, hi


class ExtractionError(ValueError):
    pass


def to_poolable(measure_token, point, lo, hi, *, source_quote, identifier,
                extraction_method="regex", model=None, date=None):
    """Validate a published effect+CI and emit a poolable record, or raise ExtractionError.

    The record shape matches the object's per_trial entries so the synthesise engine reads it
    directly: {point, ci_low, ci_high, measure, y, se, poolable_input_type, provenance}.
    """
    tok = (measure_token or "").upper()
    if tok not in ALL_MEASURES:
        raise ExtractionError("unknown effect measure %r (want one of %s)" % (measure_token, sorted(ALL_MEASURES)))
    for label, v in (("point", point), ("ci_low", lo), ("ci_high", hi)):
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ExtractionError("%s is not a finite number: %r" % (label, v))
    if lo > hi:
        raise ExtractionError("CI disordered: low %s > high %s" % (lo, hi))
    if not (lo <= point <= hi):
        raise ExtractionError("CI [%s, %s] does not bracket the point %s -- likely a transcription "
                              "error; refusing rather than pooling a wrong input" % (lo, hi, point))
    ratio = tok in RATIO_MEASURES
    if ratio:
        if min(point, lo, hi) <= 0:
            raise ExtractionError("ratio measure %s must be > 0 (got point=%s lo=%s hi=%s)" % (tok, point, lo, hi))
        y = math.log(point); se = (math.log(hi) - math.log(lo)) / (2 * Z)
    else:
        y = float(point); se = (hi - lo) / (2 * Z)
    if se <= 0:
        raise ExtractionError("degenerate CI gives se<=0 (lo==hi); a zero-width CI is not poolable")
    if not source_quote or not identifier:
        raise ExtractionError("provenance required: source_quote and identifier are mandatory")
    prov = {"source_quote": source_quote, "identifier": identifier, "extraction_method": extraction_method}
    if extraction_method == "model":
        if not (model and date):
            raise ExtractionError("extraction_method=model requires model id and date (recorded decision)")
        prov["model"] = model; prov["date"] = date
    return {"point": point, "ci_low": lo, "ci_high": hi, "measure": tok,
            "effect_measure": ALL_MEASURES[tok], "y": y, "se": se,
            "poolable_input_type": "effect_ci_measure", "provenance": prov}


def extract_from_text(text, *, identifier, source_quote=None, extraction_method="regex"):
    """Parse a statement and emit a poolable record in one call (raises if unparseable/invalid)."""
    parsed = parse_effect_string(text)
    if not parsed:
        raise ExtractionError("no effect+CI pattern found in %r" % (text[:60],))
    tok, point, lo, hi = parsed
    return to_poolable(tok, point, lo, hi, source_quote=source_quote or text.strip(),
                       identifier=identifier, extraction_method=extraction_method)


# ---- self-test: the DELIVER k=4 closure + the refusals ----------------------------------
def _selftest():
    ok, rows = True, []
    def chk(name, cond):
        nonlocal ok; ok &= bool(cond); rows.append((name, "OK" if cond else "*** FAIL ***"))

    # DELIVER's published 2-component HR, the exact input the SGLT2 object drops
    rec = extract_from_text("2-component HR 0.80 (95% CI 0.71-0.91)", identifier="NCT03619213")
    chk("DELIVER 'HR 0.80 (0.71-0.91)' parses & validates", rec and abs(rec["point"] - 0.80) < 1e-9)
    chk("  emitted on log scale (y=log 0.80)", abs(rec["y"] - math.log(0.80)) < 1e-12)
    chk("  poolable_input_type=effect_ci_measure", rec["poolable_input_type"] == "effect_ci_measure")

    # THE CLOSURE: 3 stored SGLT2 trials + this DELIVER record should pool to the protocol's k=4 0.774
    try:
        import importlib.util, os
        spec = importlib.util.spec_from_file_location("rr", os.path.join(os.path.dirname(__file__), "reproduce_review.py"))
        rr = importlib.util.module_from_spec(spec); spec.loader.exec_module(rr)
        k3 = [(0.75, 0.65, 0.85), (0.75, 0.65, 0.86), (0.79, 0.69, 0.90)]
        k4 = k3 + [(rec["point"], rec["ci_low"], rec["ci_high"])]
        pooled_k4 = rr.reml_pool(k4)[0]
        chk("EXTRACT closes the SGLT2 k=4 gap: pool(3 stored + DELIVER) ~ 0.774",
            abs(round(pooled_k4, 4) - 0.7738) < 6e-4)
    except Exception as e:
        chk("EXTRACT closes the SGLT2 k=4 gap (pooler import)", False); rows[-1] = (rows[-1][0] + " [%s]" % e, "*** FAIL ***")

    def refuses(fn):
        try:
            fn(); return False
        except ExtractionError:
            return True

    chk("CI not bracketing point refused", refuses(lambda: to_poolable("HR", 0.80, 0.85, 0.91, source_quote="x", identifier="y")))
    chk("ratio measure <= 0 refused", refuses(lambda: to_poolable("HR", 0.0, 0.0, 0.5, source_quote="x", identifier="y")))
    chk("disordered CI refused", refuses(lambda: to_poolable("RR", 0.80, 0.91, 0.71, source_quote="x", identifier="y")))
    chk("unknown measure refused", refuses(lambda: to_poolable("ZZ", 1.0, 0.5, 1.5, source_quote="x", identifier="y")))
    chk("zero-width CI refused", refuses(lambda: to_poolable("HR", 0.80, 0.80, 0.80, source_quote="x", identifier="y")))
    chk("missing provenance refused", refuses(lambda: to_poolable("HR", 0.80, 0.71, 0.91, source_quote="", identifier="")))
    chk("model extraction w/o model-id+date refused",
        refuses(lambda: to_poolable("HR", 0.80, 0.71, 0.91, source_quote="x", identifier="y", extraction_method="model")))
    # a MD (difference-scale) input works on the natural scale
    md = to_poolable("MD", -19.8, -28.9, -10.6, source_quote="sTST", identifier="NCTxxxx")
    chk("difference-scale MD pooled on natural scale", abs(md["y"] - (-19.8)) < 1e-9 and md["se"] > 0)
    return ok, rows


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv[1:] or len(sys.argv) == 1:
        ok, rows = _selftest()
        print("extract_effect_ci selftest")
        for n, v in rows:
            print("  %-58s %s" % (n, v))
        print("\n%s" % ("ALL PASS" if ok else "FAILURES ABOVE"))
        raise SystemExit(0 if ok else 1)
    # CLI: parse one statement -> emit the poolable record as JSON
    text = sys.argv[1]; ident = sys.argv[2] if len(sys.argv) > 2 else "UNKNOWN"
    print(json.dumps(extract_from_text(text, identifier=ident), indent=2))
