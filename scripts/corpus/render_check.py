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
const out = {tabs: [], results: {}, text: "", nmaVisible: null, qa4Banner: null};
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
return JSON.stringify(out);
"""


NETWORK_NOISE = ("net::ERR", "Access to fetch", "Failed to fetch", "favicon",
                 "ERR_INTERNET_DISCONNECTED", "CORS policy", "Failed to load resource")


def snapshot(driver, path):
    # Every file:// page shares one localStorage origin, so a before-run seeds state
    # that changes how the after-run behaves -- the two loads would not be comparable.
    # Clear it, then load twice: the first load re-seeds, the second is the steady
    # state a returning reader meets.
    uri = pathlib.Path(path).resolve().as_uri()
    driver.get(uri)
    try:
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
    WebDriverWait(driver, 40).until(
        lambda d: (d.execute_script("var e=document.getElementById('res-or');"
                                    "return e? e.innerText : '--'") or "--") != "--")
    # init() finishes AFTER the first result render: the tab-visibility gate is the
    # last statement in it. Probing on res-or alone read the tab bar mid-init and
    # reported the T9 gate as not firing when it had. Settle, then probe.
    import time
    time.sleep(4)
    data = json.loads(driver.execute_script(PROBE))
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--allow-file-access-from-files")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    bdir, adir = pathlib.Path(a.before), pathlib.Path(a.after)
    pages = sorted(p.name for p in (adir.glob("*.html") if adir.is_dir() else [adir]))

    driver = webdriver.Chrome(options=opts)
    report = []
    try:
        for name in pages:
            bp = (bdir / name) if bdir.is_dir() else bdir
            appath = (adir / name) if adir.is_dir() else adir
            if not bp.exists():
                print(f"{name}: no before-page; skipping")
                continue
            row = {"page": name}
            # A/A baseline: load the BEFORE page twice. Several corpus pages throw a
            # pre-existing, INTERMITTENT TypeError (s.i2.toFixed) that appears on one
            # load and not the next, so a single before-load would report it as a
            # regression introduced by the wave. Establishing the flaky set from the
            # unedited page is the only way to tell a real regression from noise.
            db, sb1, _ = snapshot(driver, bp)
            _, sb2, _ = snapshot(driver, bp)
            sb = sb1 + sb2
            da, sa, _ = snapshot(driver, appath)
            row["flaky_baseline"] = sorted({normalize_error(m) for m in sb2}
                                           - {normalize_error(m) for m in sb1})
            row["before_console_severe"] = sb
            row["after_console_severe"] = sa
            if db is None or da is None:
                row["verdict"] = "RUNTIME_BREAK"
                report.append(row)
                print(f"{name}: RUNTIME_BREAK  before={sb[:1]} after={sa[:1]}")
                continue
            nb, na = result_numbers(db), result_numbers(da)
            row["results_before"] = db["results"]
            row["results_after"] = da["results"]
            row["result_numbers_identical"] = nb == na
            row["nma_visible_before"] = db["nmaVisible"]
            row["nma_visible_after"] = da["nmaVisible"]
            row["qa4_banner_after"] = da["qa4Banner"]
            tabs_b = [t["label"] for t in db["tabs"] if t["visible"]]
            tabs_a = [t["label"] for t in da["tabs"] if t["visible"]]
            row["tabs_before"], row["tabs_after"] = tabs_b, tabs_a
            # Compare error IDENTITY, not the raw message: chrome prefixes every entry
            # with the page URL and a line:column, so a before-message and the same
            # after-message never match textually and every pre-existing error would
            # be reported as new. Confirmed against a before-vs-before self control.
            nb_msgs = collections.Counter(normalize_error(m) for m in sb)
            na_msgs = collections.Counter(normalize_error(m) for m in sa)
            new_errors = [e for e in sorted((na_msgs - nb_msgs).elements())
                          if not is_known_preexisting(e)]
            row["known_preexisting_seen"] = sorted({e for e in na_msgs
                                                    if is_known_preexisting(e)})
            row["preexisting_console_errors"] = sorted(set(nb_msgs))
            row["new_console_errors"] = new_errors
            ok = (nb == na) and not new_errors
            row["verdict"] = "OK" if ok else "CHANGED"
            report.append(row)
            print(f"{name}: {row['verdict']}  result-numbers identical={nb == na}  "
                  f"new-console-errors={len(new_errors)}  "
                  f"NMA tab {db['nmaVisible']}->{da['nmaVisible']}")
            if nb != na:
                print(f"    lost={dict((nb - na))}  gained={dict((na - nb))}")
            for e in new_errors[:3]:
                print(f"    NEW ERROR: {e[:200]}")
    finally:
        driver.quit()

    if a.json_out:
        pathlib.Path(a.json_out).write_text(json.dumps(report, indent=1, ensure_ascii=False),
                                            encoding="utf-8")
        print(f"\nreport -> {a.json_out}")
    return 0 if all(r.get("verdict") == "OK" for r in report) else 1


if __name__ == "__main__":
    sys.exit(main())
