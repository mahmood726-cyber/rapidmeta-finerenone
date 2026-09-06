# -*- coding: utf-8 -*-
"""reproduce_review.py -- re-run a review from its registered protocol and DIFF the served bytes.

The milestone of the protocol-first loop. A review is reproducible iff, starting from its protocol
committed at a known SHA, the harness regenerates the number a reader meets on the served page. This
tool reports that on THREE axes, because "reproduces" has three distinct meanings and a page can pass
one while failing another:

  RENDER          the served headline == the engine's pooling of the object's OWN stored inputs.
                  (Does the rendered surface faithfully show what the object holds?)
  PROTOCOL        the served result == the answer the REGISTERED PROTOCOL specifies.
                  (Does the review conform to the protocol it was registered under?)
  PIPELINE        the object's inputs can be regenerated autonomously SEARCH->SCREEN->EXTRACT.
                  (Could the harness rebuild the evidence set from scratch, with no human step?)

Each axis returns one of: REPRODUCES / DIFFERS (with the diff) / CANNOT_RUN (naming the missing
component). A reproduction check that has never returned a negative has not been shown capable of
one, so `--selftest` perturbs an input and asserts the RENDER axis flips to DIFFERS.

The pooling engine here is the validated REML pooler; it reproduces the served SGLT2 primary
(0.7636) to 4 dp from the three stored trial effects, which is the evidence it is the right method
for this check. Written in-tree (Codex cannot write files in this sandbox).
"""
from __future__ import annotations
import io, os, re, csv, glob, json, math, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Z = 1.959963985

# ---- pooling engine (REML, log scale) ---------------------------------------------------
def _ci_to_y_se(point, lo, hi):
    return math.log(point), (math.log(hi) - math.log(lo)) / (2 * Z)

def reml_pool(effects):
    """effects: list of (point, lo, hi) on the natural (ratio) scale. Returns (point, lo, hi, tau2, k)."""
    ys, vs = [], []
    for pt, lo, hi in effects:
        y, se = _ci_to_y_se(pt, lo, hi); ys.append(y); vs.append(se * se)
    k = len(ys); tau2 = 0.0
    for _ in range(1000):
        w = [1.0 / (v + tau2) for v in vs]; sw = sum(w)
        mu = sum(a * b for a, b in zip(w, ys)) / sw
        num = sum(wi * wi * ((yi - mu) ** 2 - vi) for wi, yi, vi in zip(w, ys, vs))
        den = sum(wi * wi for wi in w)
        new = max(0.0, num / den + 1.0 / sw)
        if abs(new - tau2) < 1e-13:
            tau2 = new; break
        tau2 = new
    w = [1.0 / (v + tau2) for v in vs]; sw = sum(w)
    mu = sum(a * b for a, b in zip(w, ys)) / sw; se = math.sqrt(1.0 / sw)
    return math.exp(mu), math.exp(mu - Z * se), math.exp(mu + Z * se), tau2, k

# ---- component registry (gap-aware) -----------------------------------------------------
# A stage is available iff a GENERIC, runnable component exists. Bespoke per-review scripts do
# NOT count -- that they exist per-review is the defect the loop exposed, not a capability.
COMPONENTS = {
    "SEARCH":     ("scripts/europepmc_adapter.py",  "generic source adapter"),
    "SCREEN":     ("scripts/screen.py",             "generic every-outcome-rank screener"),
    "EXTRACT":    ("scripts/extract_effect_ci.py",  "generic effect+CI ingestion"),
    "SYNTHESISE": ("__builtin_reml__",              "REML pooler (in this module)"),
    "RENDER":     ("scripts/generate_living_ma_v13.py", "page generator"),
}

def component_status():
    out = {}
    for stage, (path, desc) in COMPONENTS.items():
        avail = (path == "__builtin_reml__") or os.path.exists(os.path.join(ROOT, path))
        out[stage] = (avail, path, desc)
    return out

# ---- path resolution --------------------------------------------------------------------
def resolve_paths(review_id):
    slug = review_id.lower().replace("_", "-")
    obj = os.path.join(ROOT, "ssot", slug, slug + ".json")
    proto = sorted(glob.glob(os.path.join(ROOT, "protocols", review_id.lower() + "_*.json")))
    page_candidates = [review_id.upper() + "_REVIEW.html", review_id.upper() + "_AUTO_FULL_REVIEW.html",
                       slug + ".html"]
    page = next((os.path.join(ROOT, c) for c in page_candidates if os.path.exists(os.path.join(ROOT, c))), None)
    return {"object": obj if os.path.exists(obj) else None,
            "protocol": proto[-1] if proto else None,
            "page": page, "slug": slug}

def registering_sha(protocol_relpath):
    try:
        rel = protocol_relpath.replace(os.sep, "/")  # git wants forward slashes even on Windows
        # decode as utf-8/replace, NOT text=True (locale codec crashes on non-ASCII git output, cp1252)
        out = subprocess.run(["git", "-C", ROOT, "log", "--diff-filter=A", "--format=%H", "--",
                              rel], capture_output=True, timeout=60)
        shas = [s for s in out.stdout.decode("utf-8", "replace").split() if s]
        return shas[-1] if shas else None
    except Exception:
        return None

# ---- the three axes ---------------------------------------------------------------------
def _outcomes_with_pool(obj):
    out = []
    for oid, o in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(o, dict):
            continue
        pt = (o.get("per_trial") or [])
        pooled = o.get("pooled") or {}
        eff = []
        for t in pt:
            p, lo, hi = t.get("point"), t.get("ci_low"), t.get("ci_high")
            if all(isinstance(x, (int, float)) for x in (p, lo, hi)) and p > 0 and lo > 0 and hi > 0:
                eff.append((float(p), float(lo), float(hi)))
        if eff and isinstance(pooled.get("point"), (int, float)):
            out.append((oid, eff, float(pooled["point"]), pooled.get("measure", "?")))
    return out

def axis_render(obj, served_bytes, tol=5e-4):
    """RENDER: engine(object's own per_trial) == object.pooled AND object.pooled shown in served bytes."""
    rows = []
    for oid, eff, stored, meas in _outcomes_with_pool(obj):
        rp = reml_pool(eff)[0]
        engine_ok = abs(rp - stored) < tol
        shown = _num_in_bytes(stored, served_bytes)
        rows.append({"outcome": oid, "k": len(eff), "recomputed": round(rp, 4),
                     "stored": round(stored, 4), "engine_match": engine_ok,
                     "shown_on_page": shown, "measure": meas,
                     "reproduces": engine_ok and shown})
    if not rows:
        return "CANNOT_RUN", rows, "no outcome carries both per-trial inputs and a pooled value"
    verdict = "REPRODUCES" if all(r["reproduces"] for r in rows) else "DIFFERS"
    return verdict, rows, None

def _num_in_bytes(x, served_bytes):
    if served_bytes is None:
        return False
    s = "%.4f" % x
    return s.rstrip("0").rstrip(".") in served_bytes or s in served_bytes

def _protocol_expected(proto):
    """The k and pooled value the registered protocol specifies as the correct answer."""
    st = (proto.get("statistics") or {}).get("disclosure_clause") or {}
    text = st.get("text") or ""
    exp = (proto.get("expected_primary") or {})  # structured, if present
    val = exp.get("pooled_point")
    kexp = exp.get("k")
    if val is None:
        m = re.search(r"k=?\s*(\d+)\s+pool\s*\(HR\s*(0\.\d+)\)", text, re.I)
        if m:
            kexp = kexp or int(m.group(1)); val = float(m.group(2))
    return kexp, val, text

def axis_protocol(obj, proto, tol=5e-4):
    """PROTOCOL: served/object primary == the answer the registered protocol specifies."""
    kexp, val, text = _protocol_expected(proto)
    outs = _outcomes_with_pool(obj)
    if not outs:
        return "CANNOT_RUN", {"reason": "object has no reproducible primary outcome"}
    # primary = the outcome with the most trials (the harmonised pool)
    oid, eff, stored, meas = max(outs, key=lambda r: len(r[1]))
    if val is None:
        return "CANNOT_RUN", {"reason": "protocol specifies no expected pooled value",
                              "object_primary": {"outcome": oid, "k": len(eff), "pooled": round(stored, 4)}}
    conforms = abs(stored - val) < tol and (kexp is None or kexp == len(eff))
    diff = {"outcome": oid, "protocol_expects": {"k": kexp, "pooled": val},
            "object_has": {"k": len(eff), "pooled": round(stored, 4)},
            "delta_pooled": round(stored - val, 4)}
    return ("REPRODUCES" if conforms else "DIFFERS"), diff

def axis_pipeline(status):
    gaps = [s for s in ("SEARCH", "SCREEN", "EXTRACT") if not status[s][0]]
    if gaps:
        return "CANNOT_RUN", gaps
    return "REPRODUCES", []

# ---- driver -----------------------------------------------------------------------------
def reproduce(review_id):
    p = resolve_paths(review_id)
    status = component_status()
    rpt = {"review_id": review_id, "paths": {k: (os.path.relpath(v, ROOT) if v else None)
                                             for k, v in p.items() if k != "slug"}}
    if not p["object"]:
        rpt["verdict"] = "CANNOT_RUN"; rpt["reason"] = "no object found at ssot/%s/%s.json" % (p["slug"], p["slug"])
        return rpt
    obj = json.load(io.open(p["object"], encoding="utf-8"))
    proto = json.load(io.open(p["protocol"], encoding="utf-8")) if p["protocol"] else None
    served = io.open(p["page"], encoding="utf-8", errors="replace").read() if p["page"] else None

    rpt["registering_sha"] = registering_sha(os.path.relpath(p["protocol"], ROOT)) if p["protocol"] else None
    rpt["components"] = {s: ("available" if a else "GAP -> " + path) for s, (a, path, _) in status.items()}

    rv, rrows, rnote = axis_render(obj, served)
    rpt["RENDER"] = {"verdict": rv, "outcomes": rrows, "note": rnote}
    if proto is not None:
        pv, pdiff = axis_protocol(obj, proto)
        rpt["PROTOCOL"] = {"verdict": pv, "detail": pdiff}
    else:
        rpt["PROTOCOL"] = {"verdict": "CANNOT_RUN", "detail": {"reason": "no registered protocol found"}}
    plv, pgaps = axis_pipeline(status)
    rpt["PIPELINE"] = {"verdict": plv, "gaps": pgaps}

    # headline verdict = does the served review conform to its registered protocol?
    rpt["verdict"] = rpt["PROTOCOL"]["verdict"]
    return rpt

# ---- self-test: prove the RENDER axis can return a NEGATIVE ------------------------------
def selftest():
    ok = True; rows = []
    def chk(name, cond):
        nonlocal ok; ok &= bool(cond); rows.append((name, "OK" if cond else "*** FAIL ***"))
    # a synthetic object: three trials that pool to a known value, shown on a synthetic page
    eff = [(0.75, 0.65, 0.85), (0.75, 0.65, 0.86), (0.79, 0.69, 0.90)]
    pooled = round(reml_pool(eff)[0], 4)
    obj = {"results": {"by_outcome": {"primary": {
        "per_trial": [{"point": p, "ci_low": lo, "ci_high": hi} for p, lo, hi in eff],
        "pooled": {"point": pooled, "measure": "HR"}}}}}
    served = "the pooled HR is %s and that is the answer" % pooled
    v_clean, _, _ = axis_render(obj, served)
    chk("clean object REPRODUCES (engine==stored, shown on page)", v_clean == "REPRODUCES")
    # PERTURB one input -> the engine result no longer equals the stored pooled -> DIFFERS
    import copy
    bad = copy.deepcopy(obj); bad["results"]["by_outcome"]["primary"]["per_trial"][0]["point"] = 0.60
    v_pert, prows, _ = axis_render(bad, served)
    chk("perturbing an input flips RENDER to DIFFERS", v_pert == "DIFFERS")
    chk("  and the diff names the moved recompute vs stored", prows and prows[0]["recomputed"] != prows[0]["stored"])
    # a value NOT shown on the page must also fail the render axis
    v_hidden, _, _ = axis_render(obj, "a page that never prints the number")
    chk("pooled value absent from served bytes -> DIFFERS", v_hidden == "DIFFERS")
    # PROTOCOL axis: a protocol expecting a different k/value must DIFFER
    proto = {"expected_primary": {"k": 4, "pooled_point": 0.7738}}
    pv, _ = axis_protocol(obj, proto)
    chk("protocol expecting k=4 0.7738 DIFFERS from k=3 object", pv == "DIFFERS")
    proto_ok = {"expected_primary": {"k": 3, "pooled_point": pooled}}
    pv2, _ = axis_protocol(obj, proto_ok)
    chk("protocol expecting the object's own k/value REPRODUCES", pv2 == "REPRODUCES")
    return ok, rows

def _print_report(r):
    print("=" * 78)
    print("reproduce_review: %s" % r["review_id"])
    print("  registered at SHA: %s" % (r.get("registering_sha") or "(none)"))
    for k, v in (r.get("paths") or {}).items():
        print("  %-9s %s" % (k + ":", v))
    if "components" in r:
        print("  components:")
        for s, st in r["components"].items():
            print("    %-11s %s" % (s, st))
    if r.get("verdict") == "CANNOT_RUN" and "RENDER" not in r:
        print("\n  VERDICT: CANNOT_RUN -- %s" % r.get("reason")); return
    for axis in ("RENDER", "PROTOCOL", "PIPELINE"):
        a = r.get(axis) or {}
        print("\n  [%s] %s" % (axis, a.get("verdict")))
        if axis == "RENDER":
            for o in a.get("outcomes", []):
                print("    %-28s k=%d recompute=%s stored=%s engine=%s shown=%s -> %s"
                      % (o["outcome"][:28], o["k"], o["recomputed"], o["stored"],
                         o["engine_match"], o["shown_on_page"], "REPRODUCES" if o["reproduces"] else "DIFFERS"))
            if a.get("note"): print("    note: %s" % a["note"])
        elif axis == "PROTOCOL":
            d = a.get("detail") or {}
            if "protocol_expects" in d:
                print("    outcome %s" % d["outcome"])
                print("    protocol expects: k=%s pooled=%s" % (d["protocol_expects"]["k"], d["protocol_expects"]["pooled"]))
                print("    object has:       k=%s pooled=%s   (delta %s)"
                      % (d["object_has"]["k"], d["object_has"]["pooled"], d["delta_pooled"]))
            else:
                print("    %s" % d.get("reason"))
        elif axis == "PIPELINE":
            if a.get("gaps"):
                print("    autonomous rebuild blocked -- missing generic components: %s" % ", ".join(a["gaps"]))
    print("\n  >>> VERDICT (protocol-conformance): %s <<<" % r.get("verdict"))
    print("=" * 78)

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if "--selftest" in args:
        ok, rows = selftest()
        print("reproduce_review selftest (must show it can return a NEGATIVE)")
        for n, v in rows:
            print("  %-58s %s" % (n, v))
        print("\n%s" % ("ALL PASS" if ok else "FAILURES ABOVE"))
        raise SystemExit(0 if ok else 1)
    if not args:
        print("usage: reproduce_review.py <review_id> [--selftest]"); raise SystemExit(2)
    _print_report(reproduce(args[0]))
    raise SystemExit(0)
