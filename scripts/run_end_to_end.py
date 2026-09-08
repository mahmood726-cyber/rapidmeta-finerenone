# -*- coding: utf-8 -*-
"""END-TO-END review loop for ONE review, START to END, writing the PAPER to a CANDIDATE location.

The standing loop, not a re-render:
  PROTOCOL (committed; the add-commit SHA is the registration) -> SEARCH/SCREEN/EXTRACT/SYNTHESISE
  (run_review) -> PAPER (generate_review_page, tabbed) -> DOUBLE-CHECK (three axes + tab criterion +
  retraction-preservation diff + the served-value gates).

SAFETY: writes ONLY to preview/<REVIEW>.html. It NEVER overwrites a served page. A review is cleared to
overwrite its served page ONLY if it passes all three axes AND the tab criterion AND the retraction diff.
arni-hfref and the HFrEF NMA are refused outright.

RESULT: four states, never collapsed to a pass rate. Per review, per axis:
  RAN_RESULTS  it ran and produced a comparison (REPRODUCES or DIFFERS -- both are results)
  RAN_ZERO     it ran and legitimately produced nothing (0 eligible trials / no reproducible pool)
  RAN_ERROR    it crashed
  NOT_RUN      an input is absent (CANNOT_RUN) -- a failure to test, never a pass; HARNESS_FAULT if
               the inputs WERE present.
"""
from __future__ import annotations
import io, os, sys, json, subprocess, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTECTED = {"arni-hfref", "hfref-nma", "hfref_nma"}


def _load(mod, path):
    spec = importlib.util.spec_from_file_location(mod, os.path.join(ROOT, "scripts", path))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


# Clearance DISCOVERS every gate rather than consulting a hand-list -- a hand-list is how gates ended
# up outside clearance in the first place, and the next gate would do the same. A gate added next week
# is consulted automatically. A gate that is deliberately non-blocking must be REGISTERED here with a
# reason (rendered on the page), because an opt-in gate is not a gate.
CLEARANCE_NONBLOCKING = {
    # gate: reason it does not block a single page's promotion (still runs in CI)
    "gate8_caller_and_wiring.py": "meta-gate on the gate suite's wiring, not a page property",
    "gate9_shared_scratch.py": "lint on the shared-scratch convention, not a page property",
    "gate13_nonraw_regex_escape.py": "static-analysis of .py source, not a page property",
    "gate7_blast_radius.py": "a pre-edit precondition, not a served-page check",
    "gate_kinds.py": "library/helper, not a standalone gate",
    "gate_integrity.py": "suite-integrity meta-check, not a page property",
    "gate_layer_vs_defect_layer_2026_08_26_audit.py": "a one-off audit, not a standing page gate",
}


def _discover_gates():
    """Every gate file the harness owns (gates/ + scripts/gate*.py), minus the registered non-blocking."""
    import glob as _g
    found = sorted(set(_g.glob(os.path.join(ROOT, "gates", "gate*.py"))) |
                   set(_g.glob(os.path.join(ROOT, "scripts", "gate*.py"))))
    out = []
    for p in found:
        name = os.path.basename(p)
        if name in ("gate_kinds.py",) or name in CLEARANCE_NONBLOCKING:
            continue
        out.append(p)
    return out


def _consult_gates(slug, candidate):
    """DISCOVER every gate and report which FIRE on THIS review (slug in a finding). A gate that cannot
    run at all is reported (fail-closed: an unrunnable gate on a page it should assess is not a pass)."""
    firing = []
    for path in _discover_gates():
        name = os.path.basename(path)
        # pass the candidate page as an arg: page-gates use it; corpus-scan gates ignore trailing args.
        for args in ([sys.executable, path, candidate] if candidate else [sys.executable, path],):
            try:
                p = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=180)
                out = (p.stdout + p.stderr).decode("utf-8", "replace")
            except Exception as e:
                firing.append((name, "GATE_ERROR:%s" % str(e)[:40])); out = ""
            for line in out.splitlines():
                if slug in line and not any(t in line.lower() for t in ("control", "negative", "synthetic", "silent")):
                    firing.append((name, line.strip()[:100])); break
    return firing


def _axis_state(verdict, has_input):
    if verdict in ("REPRODUCES", "DIFFERS"):
        return "RAN_RESULTS", verdict
    if verdict == "CANNOT_RUN":
        return "NOT_RUN", "input absent"
    return "RAN_ERROR", verdict


def run_one(review_id):
    rr = _load("reproduce_review", "reproduce_review.py")
    gen = _load("generate_review_page", "generate_review_page.py")
    rv = _load("run_review", "run_review.py")
    cc = _load("content_completeness", "content_completeness.py")
    slug = review_id.lower().replace("_", "-")
    rep = {"review": review_id, "slug": slug}

    if slug in PROTECTED:
        rep["verdict"] = "REFUSED_PROTECTED"; return rep

    # 1. PROTOCOL -- the registration is the add-commit SHA of the protocol file
    paths = rr.resolve_paths(review_id)
    rep["protocol_registered"] = bool(paths.get("protocol"))
    rep["registration_sha"] = rr.registering_sha(os.path.relpath(paths["protocol"], ROOT)) if paths.get("protocol") else None

    # 2. SEARCH/SCREEN/EXTRACT/SYNTHESISE via the autonomous orchestrator
    try:
        auto = rv.run(review_id)
        if "error" in auto:
            rep["pipeline_stage"] = ("RAN_ZERO", auto["error"]) if "evidence" in auto["error"] or "protocol" in auto["error"] else ("NOT_RUN", auto["error"])
        elif auto.get("k", 0) == 0:
            rep["pipeline_stage"] = ("RAN_ZERO", "0 trials screened INCLUDE")
        else:
            rep["pipeline_stage"] = ("RAN_RESULTS", "k=%s pooled=%s" % (auto["k"], (auto.get("pooled") or {}).get("point")))
    except Exception as e:
        rep["pipeline_stage"] = ("RAN_ERROR", repr(e)[:120])

    # 3. PAPER -- generate the tabbed page to the CANDIDATE location (never a served path)
    try:
        gen.generate_page(review_id)
        src = os.path.join(ROOT, review_id.upper() + ".generated.html")
        cand_dir = os.path.join(ROOT, "preview"); os.makedirs(cand_dir, exist_ok=True)
        cand = os.path.join(cand_dir, review_id.upper() + ".html")
        io.open(cand, "w", encoding="utf-8").write(io.open(src, encoding="utf-8").read())
        rep["paper_candidate"] = os.path.relpath(cand, ROOT)
    except Exception as e:
        rep["paper_candidate"] = None; rep["paper_error"] = repr(e)[:120]

    # 4. DOUBLE-CHECK -- three axes against the CANDIDATE page
    axes = {}
    if rep.get("paper_candidate"):
        r = rr.reproduce(review_id, page_override=rep["paper_candidate"])
        for ax in ("RENDER", "PROTOCOL", "PIPELINE"):
            st, why = _axis_state(r.get(ax, {}).get("verdict"), True)
            axes[ax] = {"state": st, "detail": why}
        rep["harness_fault"] = r.get("HARNESS_FAULT")
        # tab criterion + retraction diff
        orig = paths.get("page")
        if orig and os.path.exists(orig):
            o = io.open(orig, encoding="utf-8", errors="replace").read()
            g = io.open(os.path.join(ROOT, rep["paper_candidate"]), encoding="utf-8", errors="replace").read()
            td = cc.tab_delta(o, g)
            rep["tab_criterion"] = {"ok": td["ok"], "original": td["original_populated_tabs"], "generated": td["generated_populated_tabs"]}
            # retraction-preservation: no superseded number the object holds may be served on the candidate
            import re as _re
            obj = json.load(io.open(paths["object"], encoding="utf-8")) if paths.get("object") else {}
            # RETRACTION PRESERVATION has two halves, and neither is my own crude number match (a
            # Handbook section like "10.10.2" is not a dead statistic):
            #  (a) the object's retraction RECORDS survive -- true by construction (generation never
            #      writes the object); confirm it still carries superseded/withdrawn fields.
            #  (b) no dead value is SERVED live on the candidate -- the canonical check is
            #      reproduce_review._superseded_served_live (context-aware, excludes current values),
            #      which is exactly what the RENDER axis runs. Use it directly here, not a reimplementation.
            retraction_records = len(_re.findall(r"superseded|withdrawn|deprecated|claim_withdrawn", json.dumps(obj), _re.I))
            served_dead = sorted(rr._superseded_served_live(obj, g) or [])
            rep["retraction_diff"] = {"ok": (retraction_records > 0 and not served_dead),
                                      "retraction_records_in_object": retraction_records,
                                      "dead_values_served": served_dead}
    rep["axes"] = axes

    # FIELD-LEVEL RENDER: every field the object/protocol HOLDS must be rendered or declared-absent.
    # A container measure (tabs populated) cannot see an empty protocol tab; this can. It is the check
    # whose absence let a page with an empty protocol+search section clear and ship.
    if rep.get("paper_candidate"):
        try:
            frc = _load("field_render", "field_render.py")
            obj_f, proto_f, ev_f, _ = frc._resolve(review_id)
            g = io.open(os.path.join(ROOT, rep["paper_candidate"]), encoding="utf-8", errors="replace").read()
            fr = frc.check(obj_f, proto_f, ev_f, g)
            rep["field_render"] = {"ok": not fr["missing"], "rendered": fr["rendered"], "held": fr["held"],
                                   "missing": [m[0] for m in fr["missing"]], "declared_absent": len(fr["declared_absent"])}
        except Exception as e:
            rep["field_render"] = {"ok": False, "error": repr(e)[:120]}

    # CLAIM-LEVEL CENSUS: every rendered claim identified by tuple (not value); the mortality-mislabel
    # class (a real number under the wrong outcome) + debug prose + field coverage, all named.
    if rep.get("paper_candidate"):
        try:
            cen = _load("claim_census", "claim_census.py")
            c = cen.run(review_id, rep["paper_candidate"])
            rep["census"] = {"mislabels": len(c["mislabels"]), "not_in_object": len(c["not_in_object"]),
                             "prose": len(c["prose"]), "field_missing": len(c["field"]["missing"]),
                             "rendered_estimates": len(c["claims"])}
        except Exception as e:
            rep["census"] = {"error": repr(e)[:120]}

    # GATE CONSULTATION: every page/object-firing gate participates in clearance (no opt-in gates).
    if rep.get("paper_candidate"):
        firing = _consult_gates(slug, rep["paper_candidate"])
        rep["gates_firing"] = firing

    # CLEARANCE to overwrite the served page: three axes REPRODUCE, tab ok, retraction ok, every held
    # field rendered-or-declared, the claim census clean, AND no page/object-firing gate fires on it.
    cen = rep.get("census", {})
    cleared = (all(axes.get(a, {}).get("detail") == "REPRODUCES" for a in ("RENDER", "PROTOCOL", "PIPELINE"))
               and rep.get("tab_criterion", {}).get("ok") and rep.get("retraction_diff", {}).get("ok")
               and rep.get("field_render", {}).get("ok") and not rep.get("harness_fault")
               and cen.get("mislabels") == 0 and cen.get("not_in_object") == 0 and cen.get("prose") == 0
               and not rep.get("gates_firing"))
    rep["cleared_to_serve"] = bool(cleared)
    return rep


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    for rid in (sys.argv[1:] or ["empagliflozin-hf-auto-full-review"]):
        r = run_one(rid)
        print("=" * 78)
        print("REVIEW %s" % r["review"])
        print("  protocol registered: %s  SHA=%s" % (r.get("protocol_registered"), (r.get("registration_sha") or "")[:12]))
        print("  pipeline (SEARCH..SYNTHESISE): %s -- %s" % r.get("pipeline_stage", ("NOT_RUN", "")))
        print("  PAPER candidate: %s" % r.get("paper_candidate"))
        for ax in ("RENDER", "PROTOCOL", "PIPELINE"):
            a = r.get("axes", {}).get(ax, {})
            print("    %-9s %-12s %s" % (ax, a.get("state", "NOT_RUN"), a.get("detail", "")))
        if r.get("harness_fault"):
            print("  !!! HARNESS_FAULT: %s" % r["harness_fault"])
        print("  tab criterion: %s" % r.get("tab_criterion"))
        print("  retraction diff: %s" % r.get("retraction_diff"))
        print("  >>> CLEARED TO SERVE: %s <<<" % r.get("cleared_to_serve"))
    raise SystemExit(0)
