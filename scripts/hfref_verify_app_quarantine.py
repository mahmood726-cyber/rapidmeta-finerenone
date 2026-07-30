#!/usr/bin/env python
"""Verify the HFrEF app after the CARMEN quarantine.

Checks, and exits non-zero on any failure:
  A. structural   -- div balance, no literal </script> inside a script body,
                     every tab panel referenced by the tab bar exists.
  B. payload      -- the embedded cells match outputs/hfref_quarantine_primary.json
                     row for row (league, node rows, tau2, structure).
  C. agreement    -- the two verdict surfaces (window.__verdict and the
                     #rapidmeta-integrity-badge prose) state the SAME numbers.
  D. quarantine   -- CARMEN is flagged and absent from every fitted comparison;
                     no trial is silently dropped; every named violation is present.
  E. QUEST        -- no QLQX contrast is presented as significant on the crude 2x2.
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

APP = "HFREF_NMA_AUTO_FULL_REVIEW.html"
FIT = "outputs/hfref_quarantine_primary.json"
TOL = 1e-9

fails, warns = [], []


def bad(msg):
    fails.append(msg)


html = open(APP, encoding="utf-8").read()
fit = json.load(open(FIT, encoding="utf-8"))
after = {c["cell_id"]: c["after"] for c in fit["app_cells"]}
before = {c["cell_id"]: c["before"] for c in fit["app_cells"]}
ps, pb = after["OURS-STRICT"], before["OURS-STRICT"]

# ---------------------------------------------------------------- A. structure
opens = len(re.findall(r"<div[\s>]", html))
closes = len(re.findall(r"</div>", html))
if opens != closes:
    bad("div balance: %d <div> vs %d </div> (delta %+d)" % (opens, closes, opens - closes))

for sm in re.finditer(r"<script\b[^>]*>(.*?)</script>", html, re.S):
    body = sm.group(1)
    if "</script>" in body:
        bad("literal </script> inside a script body at offset %d" % sm.start())

tabs = set(re.findall(r'data-tab="([^"]+)"', html))
tabs.discard("${id}")
for t in sorted(tabs):
    if not re.search(r'id="tab-%s"' % re.escape(t), html):
        bad("tab bar references data-tab=%r but no #tab-%s panel exists" % (t, t))

for tok in ("REPLACE_ME", "__PLACEHOLDER__", "TODO_FILL"):
    if tok in html:
        bad("unpopulated template token %r present" % tok)
# Mustache/Jinja style {{ name }} only. Bare "{{" also occurs in legitimate JS
# (e.g. `${{OR:"Odds Ratio"}[em]}`), so match a templated identifier, not the
# brace pair alone.
for mm in re.finditer(r"\{\{\s*[A-Za-z_][\w.\-]*\s*\}\}", html):
    bad("unpopulated template token %r present" % mm.group(0))
# Python None / f-string fallbacks leaking into rendered output or the payload.
for pat in (r"\bNone (?:trials|participants|patients)\b", r":\s*None\b",
            r"/None\b", r"\bn participants\b"):
    for mm in re.finditer(pat, html):
        bad("placeholder leak %r at offset %d" % (mm.group(0), mm.start()))
        break

# ------------------------------------------------------------------ B. payload
m = re.search(r'<script id="hfref-fit-data" type="application/json">(.*?)</script>', html, re.S)
if not m:
    bad("script#hfref-fit-data missing")
    P = None
else:
    P = json.loads(m.group(1))

if P:
    for cid, exp in after.items():
        cell = next((c for c in P["cells"] if c["cell_id"] == cid), None)
        if cell is None:
            bad("cell %s missing from payload" % cid)
            continue
        if cell["trials"] != exp["trials"]:
            bad("%s trials %s != re-fit %s" % (cid, cell["trials"], exp["trials"]))
        if abs(cell["tau2"] - exp["tau2"]) > TOL:
            bad("%s tau2 %.12f != re-fit %.12f" % (cid, cell["tau2"], exp["tau2"]))
        if cell["structure"]["icdf"] != exp["structure"]["icdf"]:
            bad("%s icdf mismatch" % cid)
        if len(cell["league"]) != len(exp["league"]):
            bad("%s league rows %d != %d" % (cid, len(cell["league"]), len(exp["league"])))
            continue
        key = lambda p: "|".join(sorted([p["t1"], p["t2"]]))
        mine = {key(p): p for p in exp["league"]}
        worst, at = 0.0, ""
        for p in cell["league"]:
            s = mine.get(key(p))
            if s is None:
                bad("%s league row %s not in re-fit" % (cid, key(p)))
                continue
            for f in ("rr", "lo", "hi"):
                dv = abs(p[f] - s[f]) / max(abs(s[f]), 1e-30)
                if dv > worst:
                    worst, at = dv, key(p) + "." + f
            if int(p["direct_k"]) != int(s["direct_k"]):
                bad("%s direct_k mismatch on %s" % (cid, key(p)))
        if worst > 1e-8:
            bad("%s league max rel dev %.3e at %s" % (cid, worst, at))
        nmine = {n["node"]: n for n in exp["node_vs_placebo"]}
        for n in cell["node_vs_placebo"]:
            s = nmine.get(n["node"])
            if s is None:
                bad("%s node %s not in re-fit" % (cid, n["node"]))
                continue
            for f in ("rr", "lo", "hi"):
                if abs(n[f] - s[f]) / max(abs(s[f]), 1e-30) > 1e-8:
                    bad("%s node %s.%s mismatch" % (cid, n["node"], f))

# ---------------------------------------------------------------- C. agreement
mv = re.search(r"window\.__verdict = (\{.*?\});?\s*</script>", html, re.S)
if not mv:
    bad("window.__verdict not found")
    V = None
else:
    V = json.loads(mv.group(1))

mb = re.search(r'<div id="rapidmeta-integrity-badge"[^>]*>(.*?)(?=<!-- a11y|<main|<header)', html, re.S)
badge = mb.group(1) if mb else ""
if not badge:
    bad("integrity badge prose not found")

if V and badge:
    if V["verdict"] != "UNCERTAIN":
        bad("verdict is %r, expected UNCERTAIN" % V["verdict"])
    if "UNCERTAIN" not in badge:
        bad("badge prose does not state the verdict UNCERTAIN")
    c = V["counts"]
    # every number the badge asserts must equal the machine payload
    pairs = [
        ("network trials", c["n_trials_seen"], ps["trials"]),
        ("contrasts", c["contrasts_checked"], ps["contrasts"]),
        ("icdf_after", c["icdf_after"], ps["structure"]["icdf"]),
        ("icdf_before", c["icdf_before"], pb["structure"]["icdf"]),
        ("ci excl 1", c["nma_ci_excludes_1"], ps["counts"]["ci_excludes_null"]),
        ("ci excl 1 before", c["nma_ci_excludes_1_before_quarantine"],
         pb["counts"]["ci_excludes_null"]),
        ("findings open", c["findings_open"], 0),
        ("quarantined", c["trials_quarantined"], 1),
        ("counts changed", c["count_values_changed"], 0),
    ]
    for nm, got, want in pairs:
        if got != want:
            bad("verdict counts.%s = %r but re-fit says %r" % (nm, got, want))
    # LABEL-ANCHORED extraction. Substring presence is too weak: the trial count
    # and the contrast count are both 27, so a bare `"27" in badge` test passes
    # even when the badge's *trial* figure has been corrupted. Each number is
    # therefore pulled from the phrase that gives it its meaning.
    def pull(name, pattern, ngroups=1):
        mm = re.search(pattern, badge)
        if not mm:
            bad("badge prose has no %s claim matching %r" % (name, pattern))
            return None
        g = tuple(int(x) if x.isdigit() else float(x) for x in mm.groups())
        return g[0] if ngroups == 1 else g

    a_bb = next(x for x in ps["node_vs_placebo"] if x["node"] == "ACEI+BB")
    b_bb = next(x for x in pb["node_vs_placebo"] if x["node"] == "ACEI+BB")
    a_bm = next(x for x in ps["node_vs_placebo"] if x["node"] == "ACEI+BB+MRA")
    b_bm = next(x for x in pb["node_vs_placebo"] if x["node"] == "ACEI+BB+MRA")

    claims = [
        ("badge trial count", pull("trial count", r"<b>Network:</b>\s*(\d+) trials"),
         c["n_trials_seen"]),
        ("badge contrast count", pull("contrast count", r"/\s*(\d+) contrasts"),
         c["contrasts_checked"]),
        ("badge ICDF", pull("ICDF", r"ICDF unchanged at (\d+)"), c["icdf_after"]),
        ("badge purely-indirect", pull("purely-indirect", r"<b>(\d+) of (\d+)</b>\s*CI-excludes-1", 2),
         (c["nma_ci_excludes_1_purely_indirect"], c["nma_ci_excludes_1"])),
        ("badge cyclomatic move", pull("cyclomatic", r"cyclomatic (\d+) &rarr; (\d+)", 2),
         (pb["structure"]["cyclomatic"], ps["structure"]["cyclomatic"])),
        ("badge CI-excl move", pull("CI-excl move", r"CI-excludes-1 rises (\d+) &rarr; (\d+)", 2),
         (c["nma_ci_excludes_1_before_quarantine"], c["nma_ci_excludes_1"])),
        ("badge ACEI+BB move",
         pull("ACEI+BB move", r"ACEI\+BB (\d+\.\d+) &rarr; (\d+\.\d+)", 2),
         (round(b_bb["rr"], 3), round(a_bb["rr"], 3))),
        ("badge ACEI+BB+MRA move",
         pull("ACEI+BB+MRA move", r"ACEI\+BB\+MRA (\d+\.\d+) &rarr; (\d+\.\d+)", 2),
         (round(b_bm["rr"], 3), round(a_bm["rr"], 3))),
    ]
    for nm, got, want in claims:
        if got is None:
            continue
        if got != want:
            bad("VERDICT SURFACES DISAGREE: %s states %r, window.__verdict/re-fit says %r"
                % (nm, got, want))
    idc = sum(1 for p in ps["league"]
              if (p["lo"] > 1 or p["hi"] < 1) and p["direct_k"] == 0)
    if c["nma_ci_excludes_1_purely_indirect"] != idc:
        bad("purely-indirect count %d != recomputed %d"
            % (c["nma_ci_excludes_1_purely_indirect"], idc))

# --------------------------------------------------------------- D. quarantine
VIOL = "no death data in source; 14/14/14 unsourced; primary is LVESVI"
if P:
    q = P.get("quarantine")
    if not q:
        bad("payload carries no quarantine record")
    else:
        w = q.get("withheld", [])
        if len(w) != 1 or w[0]["trial"] != "CARMEN":
            bad("quarantine.withheld is not exactly [CARMEN]")
        elif w[0]["violation"] != VIOL:
            bad("CARMEN violation string differs from the ledger wording")
        elif len(w[0].get("withheld_rows", [])) != 3:
            bad("CARMEN's 3 arm rows are not retained in the payload")
    carmen = next((t for t in P["trials"] if t.get("id") == "HF-021"), None)
    if carmen is None:
        bad("CARMEN was DELETED from the trial ledger; it must be retained and flagged")
    else:
        if not carmen.get("quarantined"):
            bad("CARMEN not flagged quarantined")
        if carmen.get("in_network"):
            bad("CARMEN still marked in_network")
    for cmp_ in P["nma_config"]["comparisons"]:
        if "CARMEN" in cmp_["trials"]:
            bad("CARMEN still listed on edge %s vs %s" % (cmp_["t1"], cmp_["t2"]))
    if any(c_["t1"] == "ACEI+BB" and c_["t2"] == "BB" for c_ in P["nma_config"]["comparisons"]):
        bad("edge ACEI+BB vs BB survived although CARMEN was its only trial")
    n_flagged = sum(1 for t in P["trials"] if t.get("quarantined"))
    if n_flagged != 1:
        bad("expected exactly 1 quarantined trial, found %d" % n_flagged)
    if P["coverage"]["network_trials"] != ps["trials"]:
        bad("coverage.network_trials %d != %d" % (P["coverage"]["network_trials"], ps["trials"]))
    # the re-sourced identifiers must actually be in the ledger
    for tid, pmid in (("HF-008", "10740141"), ("HF-019", "10653828")):
        t = next((x for x in P["trials"] if x.get("id") == tid), None)
        if t is None or t.get("pmid") != pmid:
            bad("%s does not carry the corrected PMID %s" % (tid, pmid))
    if any(t.get("pmid") == "10477530" for t in P["trials"]):
        bad("the superseded RESOLVD PMID 10477530 is still present")

# -------------------------------------------------------------------- E. QUEST
if "0.058" not in html:
    bad("QUEST's own non-significant result (P=0.058) is not stated anywhere in the app")
if "0.70-1.01" not in html and "0.70&ndash;1.01" not in html:
    bad("QUEST's reported CI 0.70-1.01 is not stated in the app")

# ------------------------------------------------------------------- verdict
print("=" * 72)
for w in warns:
    print("WARN: " + w)
if fails:
    print("FAILURES (%d):" % len(fails))
    for f in fails:
        print("  - " + f)
    print("VERDICT: FAIL")
    sys.exit(1)
print("checks passed: structure, payload row-for-row, verdict-surface agreement, "
      "quarantine integrity, QUEST presentation")
print("VERDICT: PASS")
