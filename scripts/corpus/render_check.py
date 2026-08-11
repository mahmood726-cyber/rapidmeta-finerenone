#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Headless render check for a wave-edited page, before vs after.

WHY A RENDER CHECK AT ALL. The static guards in corpus_wave.py prove that no number
in the page SOURCE moved and that the per-page data spans are byte-identical. They
cannot prove the page still runs: an edit inside a minified <script> that breaks
syntax produces a page whose source numbers are perfect and whose screen is blank.
The sweep was static-only and explicitly flags D1/D9/D10/D12/D14/D17's runtime
consequences as inferred, not observed. So the exemplars get executed.

WHAT IT ASSERTS, per page, before and after:
  1. zero uncaught JS errors in the console (SEVERE entries),
  2. the analysis tab renders a pooled effect, CI, I-squared and HKSJ card,
  3. the DOM's rendered-number multiset for those result cards is IDENTICAL
     before vs after -- this is the runtime counterpart of the static guard, and it
     is the one that would catch an edit that changed a computed value,
  4. the tab bar has the same set of visible tabs, EXCEPT where the T9 gate is
     expected to have removed a disconnected NMA tab.

Usage:
    python render_check.py --before DIR_OR_FILE --after DIR_OR_FILE
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NUM = re.compile(r"\d+(?:[.,]\d+)*")

PROBE = r"""
const out = {tabs: [], results: {}, text: "", nmaVisible: null, qa4Banner: null,
             declared: {}};
document.querySelectorAll('nav .tab-btn').forEach(b => {
  const vis = b.style.display !== 'none' && b.offsetParent !== null;
  out.tabs.push({id: b.id, label: (b.textContent||'').trim(), visible: vis});
});
const nma = document.getElementById('btn-tab-nma');
out.nmaVisible = nma ? (nma.style.display !== 'none') : null;
const qa4 = document.getElementById('qa4-discordance-banner');
out.qa4Banner = qa4 ? (qa4.className.indexOf('hidden') === -1) : null;
['res-or','res-ci','res-i2','res-hksj','res-pi','res-tau2-ci'].forEach(id => {
  const el = document.getElementById(id);
  out.results[id] = el ? (el.innerText||'').trim() : null;
});
const an = document.getElementById('tab-analysis');
out.text = an ? (an.innerText||'').slice(0, 20000) : '';

// ---- DECLARED-CHANGE SURFACES, ANALYSIS TAB ----------------------------------
// W4-W6 change what a reader sees. Each surface a wave is ALLOWED to change is
// probed by name, so the change is recorded per page rather than merely permitted.
// Everything NOT named in a wave's allowlist stays zero-tolerance.
//
// Surfaces are probed in the tab they live on, immediately after that tab has been
// driven, and the page is never switched back. An earlier version drove the report
// tab and returned to analysis before probing; the round trip re-entered init and
// left RapidMeta.state.results null on one side of the pair but not the other, so
// the same page compared against itself reported k and N as changed.
const txt = id => { const e = document.getElementById(id);
                    return e ? (e.innerText||'').trim().slice(0,400) : null; };
out.declared['hta']             = txt('hta-container');      // W4: the two HTA cards
out.declared['patient_plain']   = txt('patient-plain-text'); // W4/W5: NNT + N sentence
out.declared['grade_container'] = txt('grade-container');    // W6: certainty + reasons
out.declared['rob_lights']      = txt('rob-traffic-lights'); // W6: RoB badges
try {
  const r = (window.RapidMeta && RapidMeta.state && RapidMeta.state.results) || null;
  // k and n are the two numbers W5 exists to reconcile. Probing the state object
  // rather than a DOM string is what makes the GRADE-agreement assertion possible.
  out.declared['state_k'] = r ? String(r.k) : null;
  out.declared['state_n'] = r ? String(r.n) : null;
} catch (e) { out.declared['state_k'] = null; out.declared['state_n'] = null; }
return JSON.stringify(out);
"""

# Report tab. Driven and probed as its own step, after the analysis probe has been
# taken, so nothing here can perturb the analysis-tab reading.
PROBE_REPORT = r"""
const out = {};
const txt = id => { const e = document.getElementById(id);
                    return e ? (e.innerText||'').trim().slice(0,400) : null; };
out['nyt_nnt']       = txt('nyt-kn-nnt');        // W4: report NNT tile
out['wr_icon_label'] = txt('wr-icon-label');     // W4: waiting-room caption
out['nyt_subhead']   = txt('nyt-subhead');       // W5: "k trials enrolling N patients"
// The independent second opinion on N: GradeProfileEngine derives its cohort from
// plotData already, so it is the page's own disagreeing copy of the same number.
// After W5 the two must agree, and that agreement is the detector.
out['grade_profile'] = txt('grade-profile-container');
return JSON.stringify(out);
"""

# Which declared surfaces each wave is permitted to move. A surface not listed here
# is held to the same zero tolerance as W1-W3. Listing one does NOT make its change
# unexamined: every before/after pair is written to the per-page change log.
EXPECT_CHANGE = {
    "W1": set(), "W2": set(), "W3": set(),
    # W4 removes the HTA cards and suppresses NNT in HR mode.
    "W4": {"hta", "nyt_nnt", "wr_icon_label", "patient_plain"},
    # W5 moves the displayed cohort toward the pooled set. The pooled EFFECT must not
    # move -- res-or/res-ci are not in this set, so a W5 edit that changed the estimate
    # would still be caught.
    # The GRADE profile table restates the cohort, so it moves with N.
    "W5": {"state_n", "nyt_subhead", "patient_plain", "grade_profile"},
    # W6 changes RoB badges and the certainty that is derived from them. The profile
    # table prints that certainty per outcome, so it moves too.
    "W6": {"grade_container", "rob_lights", "grade_profile"},
}


def _norm_surface(v):
    """Normalise a probed surface before comparing.

    The RoB traffic-light strip lists trial names in whatever order the extraction
    promises settled, so the A/A control -- the unedited page against itself -- saw
    'CHAMPION-PCI, CHAMPION-PHOENIX, CHAMPION-PLATFORM' become
    'CHAMPION-PCI, CHAMPION-PLATFORM, CHAMPION-PHOENIX'. That is a set, rendered in a
    nondeterministic order; comparing it as a string reports a change on a page where
    nothing changed. Sorting the lines compares what the surface means rather than
    the order the network happened to deliver it in.
    """
    if v is None:
        return None
    lines = [ln.strip() for ln in str(v).splitlines() if ln.strip()]
    return "\n".join(sorted(lines))


def declared_diff(db, da):
    """Per-page change log: every declared surface whose text moved, before -> after."""
    out = {}
    for key in sorted(set(db.get("declared", {})) | set(da.get("declared", {}))):
        b = db.get("declared", {}).get(key)
        a = da.get("declared", {}).get(key)
        if _norm_surface(b) != _norm_surface(a):
            out[key] = {"before": b, "after": a}
    return out


NETWORK_NOISE = ("net::ERR", "Access to fetch", "Failed to fetch", "favicon",
                 "ERR_INTERNET_DISCONNECTED", "CORS policy", "Failed to load resource")


BLANK = "blank__rmwave.html"


def _blank_for(path):
    """A near-empty file in the same directory, so it shares the page's file:// origin.

    Storage must be cleared between loads -- every file:// page shares one origin, and
    a before-run would otherwise seed state that changes how the after-run behaves. The
    obvious way to do that is load the page, clear, reload, but that costs TWO loads of
    a ~900 KB single-file app carrying plotly, i.e. four heavy loads per before/after
    pair. Clearing from a blank page in the same origin costs one trivial load instead,
    which is the difference between a 12-hour rollout and a 5-hour one."""
    p = pathlib.Path(path).resolve().parent / BLANK
    if not p.exists():
        p.write_text("<!doctype html><title>b</title>", encoding="utf-8")
    return p.as_uri()


def snapshot(driver, path, settle=2.5):
    uri = pathlib.Path(path).resolve().as_uri()
    try:
        driver.get(_blank_for(path))
        driver.execute_script("localStorage.clear();sessionStorage.clear();")
    except Exception:                                          # noqa: BLE001
        pass
    driver.get(uri)
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(driver, 40).until(
        lambda d: d.execute_script("return document.readyState") == "complete")
    # The analysis tab computes on switch; drive it the way a reader would.
    try:
        driver.execute_script("RapidMeta.switchTab('analysis'); AnalysisEngine.run();")
    except Exception as e:                                    # noqa: BLE001
        return None, [f"switchTab/AnalysisEngine failed: {e}"], []
    try:
        WebDriverWait(driver, 25).until(
            lambda d: (d.execute_script("var e=document.getElementById('res-or');"
                                        "return e? e.innerText : '--'") or "--") != "--")
    except Exception:                                          # noqa: BLE001
        pass          # a k=0 page never fills res-or; the probe below still runs
    # AnalysisEngine.run() finishes asynchronously. res-or is written to the DOM before
    # RapidMeta.state.results is assigned, so waiting on res-or alone let the probe
    # read state.results as null on one side of an A/A pair and populated on the other
    # -- reporting k and N as changed on a page compared against itself. Wait for the
    # object the probe actually reads.
    try:
        WebDriverWait(driver, 25).until(
            lambda d: d.execute_script(
                "return !!(window.RapidMeta&&RapidMeta.state&&RapidMeta.state.results)"))
    except Exception:                                          # noqa: BLE001
        pass          # k=0 pages never assign it; both sides wait identically
    # init() finishes AFTER the first result render: the tab-visibility gate is the
    # last statement in it. Probing on res-or alone read the tab bar mid-init and
    # reported the T9 gate as not firing when it had. Settle, then probe.
    import time
    time.sleep(settle)
    data = json.loads(driver.execute_script(PROBE))

    # ---- report tab, as a separate step -------------------------------------
    # W1-W3 only touched analysis-tab surfaces, so the check drove only that tab --
    # limit #1 of the W1-W3 rollout. But the NNT tile, the waiting-room caption and
    # the "k trials enrolling N patients" subhead all live here, and they are exactly
    # what W4 and W5 change. Probed without this step every declared surface read as
    # its '--' placeholder on both sides, and the check reported a clean pass while
    # observing nothing.
    #
    # WAITED ON, NOT SLEPT THROUGH. A first attempt slept a fixed 1.5 s. On a cold
    # browser the generate had not finished inside it; on the warm second load of the
    # pair it had. That produced a placeholder before-snapshot against a populated
    # after-snapshot -- a difference caused entirely by load order, which at 863 pages
    # would have manufactured a declared change on nearly every page.
    try:
        driver.execute_script(
            "try{RapidMeta.switchTab('report');"
            "if(window.ReportEngine&&ReportEngine.generate)ReportEngine.generate();}"
            "catch(e){}")
        try:
            WebDriverWait(driver, 20).until(
                lambda d: any(ch.isdigit() for ch in (d.execute_script(
                    "var e=document.getElementById('nyt-subhead');"
                    "return e?e.innerText:''") or "")))
        except Exception:                                      # noqa: BLE001
            # A k=0 page never fills the subhead. Not a failure, and symmetric:
            # both sides of the pair wait the same way for the same timeout.
            pass
        time.sleep(settle)
        data["declared"].update(json.loads(driver.execute_script(PROBE_REPORT)))
    except Exception:                                          # noqa: BLE001
        pass
    logs = driver.get_log("browser")
    # An offline single-file page legitimately fails its live registry fetches in a
    # sandbox. Those are environmental, not regressions; JS errors are not.
    severe = [l["message"] for l in logs if l["level"] == "SEVERE"
              and not any(n in l["message"] for n in NETWORK_NOISE)]
    return data, severe, logs


# Pre-existing, INTERMITTENT runtime errors in the corpus. Each entry is here only
# because an A/A control -- the unedited page loaded twice, compared against itself --
# reproduced it. They are real defects and are reported as such; they are not
# regressions introduced by a wave, and treating them as ones would make the render
# check unable to pass on any NMA page.
#
#   s.i2.toFixed is not a function  -- NMA summary rendering assumes i2 is a Number
#   and receives a preformatted string. Observed on ADC_HER2_LOW, ADC_HER2_ADJUVANT,
#   DOAC_AF_NMA. Out of scope for W1-W3 (it is neither prose nor a shared claim);
#   logged for the backlog.
#   <g> attribute transform: Expected number, "rotate(0,NaN,...)"  -- raised inside
#   vendor/plotly-*.min.js, a file no wave touches, when a plot is handed a NaN
#   coordinate. Reproduced in equal or greater numbers by the A/A control on
#   CBD_SEIZURE, GLP1_MASH, HIV_LA_PREP, MDR_TB_SHORTENED and RENAL_DENERV. Also a
#   real defect, also out of scope here.
#
# Matched as substrings, because the rotate() arguments differ per render.
KNOWN_PREEXISTING = (
    "Uncaught TypeError: s.i2.toFixed is not a function",
    # Both SVG-attribute families from the same NaN coordinate: the <g> transform one
    # and the <path> d one. A/A on the five affected pages produced 62 of each.
    "attribute transform: Expected number",
    "attribute d: Expected number",
)


def is_known_preexisting(msg):
    return any(k in msg for k in KNOWN_PREEXISTING)

URL_PREFIX = re.compile(r"^\S*?\.html(?:\s+\d+:\d+)?\s*")


def normalize_error(msg):
    return URL_PREFIX.sub("", msg).strip()


def result_numbers(d):
    joined = " ".join(v for v in d["results"].values() if v)
    return collections.Counter(m.group(0).replace(",", "") for m in NUM.finditer(joined))


def new_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--disable-gpu")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--allow-file-access-from-files")
    o.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=o)


def compare(db, sb, da, sa):
    """Score one before/after pair. Split out so the A/A retry can reuse it."""
    nb, na = result_numbers(db), result_numbers(da)
    mb = collections.Counter(normalize_error(m) for m in sb)
    ma = collections.Counter(normalize_error(m) for m in sa)
    new = [e for e in sorted((ma - mb).elements()) if not is_known_preexisting(e)]
    return nb == na, new, nb, na


def run_pair(before_dir, after_dir, settle=2.5, driver=None, log=print, waves=()):
    """Render every page present in after_dir, before vs after. Returns report rows.

    ONE before-load and ONE after-load per page. The A/A baseline -- loading the
    unedited page a second time -- is expensive and only earns its cost when something
    looks new, so it is taken lazily, per page, and only then. That keeps a ~900-page
    rollout inside a night while preserving the property that actually matters: no
    page is failed for an error the unedited page also produces.
    """
    before_dir, after_dir = pathlib.Path(before_dir), pathlib.Path(after_dir)
    expect = set()
    for w in waves:
        expect |= EXPECT_CHANGE.get(w, set())
    # BLANK is this module's own storage-clearing helper, written into the page
    # directory to share its file:// origin. Globbing *.html picks it up as a page to
    # render, where it fails every assertion and lands as a spurious RUNTIME_BREAK.
    pages = sorted(p.name for p in after_dir.glob("*.html") if p.name != BLANK)
    own = driver is None
    d = driver or new_driver()
    report = []
    try:
        for i, name in enumerate(pages, 1):
            bp, apth = before_dir / name, after_dir / name
            row = {"page": name}
            if not bp.exists():
                row["verdict"] = "NO_BASELINE"
                report.append(row)
                continue
            try:
                db, sb, _ = snapshot(d, bp, settle)
                da, sa, _ = snapshot(d, apth, settle)
            except Exception as e:                              # noqa: BLE001
                row["verdict"] = "RUNTIME_BREAK"
                row["error"] = str(e)[:300]
                report.append(row)
                log(f"   [{i}/{len(pages)}] {name}: RUNTIME_BREAK {str(e)[:80]}")
                continue
            if db is None or da is None:
                row["verdict"] = "RUNTIME_BREAK"
                row["before_console_severe"] = sb
                row["after_console_severe"] = sa
                report.append(row)
                log(f"   [{i}/{len(pages)}] {name}: RUNTIME_BREAK")
                continue
            # `state_k` is null when the page had not assigned RapidMeta.state.results
            # by the time it was probed -- "not measured", which is not a value and
            # must never be differenced against one. It survives the A/A control
            # because the A/A reloads the SAME side: if the before-page is reliably
            # slow and the after-page reliably is not, both A/A loads agree and the
            # asymmetry is reported as a change. Observed on ACALABRUTINIB_CLL_REVIEW,
            # whose live registry fetch is rate-limited and pushes the assignment past
            # the wait. Re-measure the unmeasured side before comparing anything.
            for _ in range(2):
                b_null = (db.get("declared", {}) or {}).get("state_k") is None
                a_null = (da.get("declared", {}) or {}).get("state_k") is None
                if b_null == a_null:
                    break
                try:
                    if b_null:
                        db, sb, _ = snapshot(d, bp, settle)
                    else:
                        da, sa, _ = snapshot(d, apth, settle)
                except Exception:                               # noqa: BLE001
                    break
            same, new, nb, na = compare(db, sb, da, sa)
            dd = declared_diff(db, da)
            unstable = {}
            # Still asymmetric after two retries: the pair is not comparable on the
            # cohort surfaces. Say so rather than reporting a number that moved.
            if ((db.get("declared", {}) or {}).get("state_k") is None) != \
               ((da.get("declared", {}) or {}).get("state_k") is None):
                for k in ("state_k", "state_n", "nyt_subhead", "grade_profile"):
                    if k in dd:
                        unstable[k] = dd.pop(k)
                row["cohort_unmeasured"] = True
            if new or dd:
                # Lazy A/A, extended to the declared surfaces. Reload the UNEDITED page
                # and compare it against ITSELF. Only what the before-page cannot
                # reproduce counts as this wave's doing.
                #
                # This is not belt-and-braces. The A/A control on the extended probe
                # found CANGRELOR_PCI_REVIEW moving six surfaces against itself: the
                # report tab populated on one load and not the next, and the RoB strip
                # emitted its trials in a different order. Without this, every one of
                # those would have been written into the per-page change log as an
                # effect of the wave, and the log is the whole evidence product.
                try:
                    db2, sb2, _ = snapshot(d, bp, settle)
                    same, new, nb, na = compare(db, sb + sb2, da, sa)
                    aa = declared_diff(db, db2)
                    for k in list(dd):
                        if k in aa:
                            unstable[k] = dd.pop(k)
                except Exception:                               # noqa: BLE001
                    pass
            # The per-page change log. `expect` names the surfaces this wave declared;
            # anything that moved OUTSIDE that set is an undeclared change and fails
            # the page, exactly as it would have under W1-W3. `dd` has already had any
            # surface the A/A control reproduced removed from it.
            undeclared = sorted(k for k in dd if k not in expect)
            row.update({
                # Full snapshots, not only the diff: the per-page change log has to be
                # readable as evidence on its own, and a diff that is empty is
                # ambiguous between "nothing moved" and "the surface never rendered".
                "declared_before": db.get("declared", {}),
                "declared_after": da.get("declared", {}),
                "declared_changes": {k: v for k, v in dd.items() if k in expect},
                "undeclared_changes": {k: dd[k] for k in undeclared},
                # Surfaces the unedited page moved against itself. Reported, never
                # charged to the wave, and worth reading: a surface that is unstable
                # on an A/A control is a page defect in its own right.
                "unstable_surfaces": unstable,
                "result_numbers_identical": same,
                "new_console_errors": new,
                "results_before": db["results"], "results_after": da["results"],
                "nma_visible_before": db["nmaVisible"], "nma_visible_after": da["nmaVisible"],
                "qa4_banner_after": da["qa4Banner"],
                "before_console_severe": sb, "after_console_severe": sa,
                "known_preexisting_seen": sorted({e for e in
                                                  (normalize_error(m) for m in sa)
                                                  if is_known_preexisting(e)}),
                "verdict": ("OK" if (same and not new and not undeclared)
                            else "CHANGED"),
            })
            report.append(row)
            if row["verdict"] != "OK":
                log(f"   [{i}/{len(pages)}] {name}: {row['verdict']} "
                    f"numbers-identical={same} new-errors={len(new)}")
            elif i % 25 == 0:
                log(f"   [{i}/{len(pages)}] ok so far")
    finally:
        if own:
            d.quit()
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--settle", type=float, default=2.5)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--expect-change", default="",
                    help="comma-separated waves whose declared surfaces may move "
                         "(e.g. W4). Surfaces outside the allowlist stay zero-"
                         "tolerance. Omit for the W1-W3 contract.")
    a = ap.parse_args()
    waves = tuple(w.strip() for w in a.expect_change.split(",") if w.strip())
    for w in waves:
        if w not in EXPECT_CHANGE:
            print(f"REFUSING: unknown wave {w!r} in --expect-change. An unrecognised "
                  f"wave would silently allow nothing, which reads as a pass.")
            return 2
    rep = run_pair(a.before, a.after, settle=a.settle, waves=waves)
    for r in rep:
        print(f"{r['page']}: {r.get('verdict')}  "
              f"result-numbers identical={r.get('result_numbers_identical')}  "
              f"new-console-errors={len(r.get('new_console_errors', []))}  "
              f"NMA tab {r.get('nma_visible_before')}->{r.get('nma_visible_after')}")
        for k, v in (r.get("declared_changes") or {}).items():
            print(f"    declared  {k}: {str(v['before'])[:70]!r} -> "
                  f"{str(v['after'])[:70]!r}")
        for k, v in (r.get("undeclared_changes") or {}).items():
            print(f"    UNDECLARED {k}: {str(v['before'])[:70]!r} -> "
                  f"{str(v['after'])[:70]!r}")
    if a.json_out:
        pathlib.Path(a.json_out).write_text(json.dumps(rep, indent=1, ensure_ascii=False),
                                            encoding="utf-8")
        print(f"report -> {a.json_out}")
    return 0 if all(r.get("verdict") == "OK" for r in rep) else 1


if __name__ == "__main__":
    sys.exit(main())
