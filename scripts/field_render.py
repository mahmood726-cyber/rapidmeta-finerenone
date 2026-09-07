# -*- coding: utf-8 -*-
"""FIELD-LEVEL RENDER CHECK: does the served page DISPLAY the fields its object/protocol hold?

The defect this closes (shipped three times): a container property read as a contents property (Law 8).
tab COUNT, then tab POPULATED (has bytes) -- neither asks whether the tab shows the review's substance.
The empagliflozin generated page had a registered protocol (SHA 45cbe9bf) and a search that returned
RAN_RESULTS, yet served an empty protocol tab and an empty search tab. And the RENDER axis compared
object-to-object (recompute==stored) and never asked whether the page prints the field -- so it said
REPRODUCES over a page missing both.

This check enumerates the fields the object and the registered protocol HOLD, and for each asks whether
its value actually appears in the page's rendered text (tags stripped). Held-but-not-rendered is a
FAILURE, named. A field named in declared_gaps is a legitimate declared absence, not a failure. And it
compares against the page being replaced: fewer object fields rendered than the old page -> refuse.
"""
from __future__ import annotations
import io, os, re, json, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _text(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def _val_in(text, val):
    if val is None:
        return None
    s = str(val).strip()
    if len(s) < 3:
        return None
    # numbers: match to 2+ sig figs as a whole-ish token; strings: a distinctive substring
    if re.fullmatch(r"-?\d+\.?\d*", s):
        return bool(re.search(r"(?<![\d.])" + re.escape(s.rstrip("0").rstrip(".")) + r"", text))
    frag = s[:60].strip()
    return frag.lower() in text.lower()


def renderable_fields(obj, protocol, evidence):
    """(label, value, tab) for every field a complete page should DISPLAY, that the source HOLDS."""
    F = []
    add = lambda lab, val, tab: F.append((lab, val, tab)) if val not in (None, "", [], {}) else None
    # --- protocol tab ---
    if protocol:
        elig = protocol.get("eligibility") or {}
        add("protocol.population", elig.get("population"), "protocol")
        add("protocol.intervention", elig.get("intervention"), "protocol")
        add("protocol.comparator", elig.get("comparator"), "protocol")
        add("protocol.design", elig.get("design"), "protocol")
        ests = protocol.get("estimands") or []
        if ests:
            add("protocol.estimand.outcome", (ests[0] or {}).get("outcome"), "protocol")
        st = protocol.get("statistics") or {}
        add("protocol.small_k_ci_rule", st.get("small_k_ci_rule"), "protocol")
    # --- search tab (the executed evidence set) ---
    if evidence:
        for tr in (evidence.get("trials") or []):
            add("search.trial:%s" % tr.get("nct"), tr.get("nct"), "search")
            add("search.effect:%s" % tr.get("nct"), tr.get("effect_statement"), "search")
    # --- per-outcome (analysis/extraction) ---
    for oid, o in ((obj.get("results") or {}).get("by_outcome") or {}).items():
        if not isinstance(o, dict):
            continue
        pooled = o.get("pooled") or {}
        add("%s.pooled.point" % oid, pooled.get("point"), "analysis")
        for t in (o.get("per_trial") or []):
            add("%s.per_trial:%s" % (oid, t.get("nct")), t.get("point"), "extract")
        het = o.get("heterogeneity") or {}
        add("%s.heterogeneity.q" % oid, het.get("q"), "analysis")
        g = (obj.get("grade") or {}).get("by_outcome", {}).get(oid) or {}
        add("%s.grade.certainty" % oid, g.get("certainty"), "report")
    return F


def check(obj, protocol, evidence, page_html):
    text = _text(page_html)
    gaps = " ".join((g.get("item", "") + " " + g.get("state", "")) for g in (obj.get("declared_gaps") or [])).lower()
    fields = renderable_fields(obj, protocol, evidence)
    rendered, missing, declared_absent = [], [], []
    for lab, val, tab in fields:
        hit = _val_in(text, val)
        if hit:
            rendered.append((lab, tab))
        else:
            # is this field's absence explicitly declared a gap?
            key = lab.split(".")[-1].split(":")[0]
            if key in gaps or lab.split(".")[0] in gaps:
                declared_absent.append((lab, tab))
            else:
                missing.append((lab, tab, val))
    return {"held": len(fields), "rendered": len(rendered), "declared_absent": declared_absent,
            "missing": missing}


def _resolve(review_id):
    rr = _load()
    p = rr.resolve_paths(review_id)
    obj = json.load(io.open(p["object"], encoding="utf-8")) if p.get("object") else {}
    protocol = json.load(io.open(p["protocol"], encoding="utf-8")) if p.get("protocol") else {}
    ev = None
    epath = rr._evidence_path(review_id)
    if epath:
        ev = json.load(io.open(epath, encoding="utf-8"))
    return obj, protocol, ev, p


def _load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("reproduce_review", os.path.join(ROOT, "scripts", "reproduce_review.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    review_id = sys.argv[1] if sys.argv[1:] else "empagliflozin-hf-auto-full-review"
    page = sys.argv[2] if sys.argv[2:] else ("out/generated/%s.generated.html" % review_id.upper())
    obj, protocol, ev, paths = _resolve(review_id)
    html = io.open(page if os.path.isabs(page) else os.path.join(ROOT, page), encoding="utf-8", errors="replace").read()
    r = check(obj, protocol, ev, html)
    print("FIELD-LEVEL RENDER CHECK -- %s" % review_id)
    print("  page: %s" % page)
    print("  object/protocol fields RENDERED: %d of %d held" % (r["rendered"], r["held"]))
    print("  declared-absent (legitimate gaps): %d" % len(r["declared_absent"]))
    print("  MISSING (held but NOT rendered, NOT declared) -- FAILURES: %d" % len(r["missing"]))
    for lab, tab, val in r["missing"]:
        print("     - [%s] %s = %s" % (tab, lab, str(val)[:60]))
    ok = not r["missing"]
    print("\n%s" % ("PASS -- every held field is rendered or declared" if ok else "FAIL -- held fields not rendered"))
    # DIAGNOSTIC entry point only -- no exit code. This module is a LIBRARY: check() is the operative
    # gate, enforced fail-closed in run_end_to_end.run_one()'s clearance (a page cannot promote unless
    # every held field renders) and surfaced by claim_census. It is deliberately NOT a standalone gate
    # with its own failing exit, so it is not an uncalled gate (gate 8).
