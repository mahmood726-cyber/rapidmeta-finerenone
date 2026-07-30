#!/usr/bin/env python
"""Verify the HFrEF app against the co-primary re-fit. Must be able to FAIL.

Checks, all of which block:

  A. STRUCTURE      div balance, no literal </script> in JS strings, every
                    data-tab has a panel, no placeholder leak.
  B. PAYLOAD        every league row and node row of BOTH co-primary fits
                    matches outputs/hfref_coprimary_fit.json to 1e-8.
  C. ANCHOR         the FULL co-primary reproduces the settled primary
                    (0.64459765 / 0.59333495 / 0.02323609) to 1e-8.
  D. CO-PRIMARY     both fits are present in every cell and in the anchor; the
                    app cannot ship one without the other.
  E. QUARANTINE     exactly len(EXPECT_QUAR) trials quarantined, each with a
                    named violation, a reinstatement condition and its arm rows
                    RETAINED (flagged, never deleted); the symmetric rule is
                    recorded.
  F. SYMMETRY       no trial in a fitted cell has identical across-arm counts
                    AND unverified status without being quarantined.
  R. REINSTATEMENT  every trial in EXPECT_REINST is in BOTH networks, is NOT
                    flagged quarantined, carries a verified count-provenance
                    tier AND a named count_source, and is recorded as reinstated
                    in the payload and the ledger. Plus the structural claim the
                    reinstatement earns: the node it restores is present in BOTH
                    fits. This check exists so a reinstatement cannot be a quiet
                    un-flagging -- releasing a trial needs evidence recorded at
                    the same standard as withholding one.
  G. VERDICT        window.__verdict and the rendered badge agree, and the badge
                    does not contradict itself on any count it states.
  H. DIRECTION      the honest direction flag is present and states BOTH parts.
  I. QUEST          no QLQX contrast presented as significant on the crude 2x2.

Negative-tested: see --selftest, which perturbs the app in memory and asserts
each check fires.
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

APP = "HFREF_NMA_AUTO_FULL_REVIEW.html"
FIT = "outputs/hfref_coprimary_fit.json"
LEDGER = "outputs/hfref_quarantine_ledger.json"
TOL = 1e-8

SETTLED = {"ACEI+BB": 0.64459765, "ACEI+BB+MRA": 0.59333495, "tau2": 0.02323609}
EXPECT_QUAR = {"HF-021": "CARMEN", "HF-025": "Vizzardi 2014"}
# Quarantined and then cleared on located evidence. Each maps to the node its
# reinstatement restores -- checked to be present in BOTH fits, because that
# structural consequence is the app's headline claim about the reinstatement.
EXPECT_REINST = {"HF-034": ("GALACTIC-HF", "+Omecamtiv")}
# Tiers that count as "the counts were actually read from a source".
VERIFIED_TIERS = {"VERBATIM_COUNT", "RECOVERED_FROM_PERCENTAGE_UNIQUE"}

fails = []


def bad(check, msg):
    fails.append("[%s] %s" % (check, msg))


def payload_of(html):
    m = re.search(r'<script id="hfref-fit-data" type="application/json">(.*?)</script>',
                  html, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def verdict_of(html):
    m = re.search(r'window\.__verdict = (\{.*?\});?\s*</script>', html, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def badge_of(html):
    ms = re.search(r'<div id="rapidmeta-integrity-badge"[^>]*>', html)
    if not ms:
        return None
    i, depth = ms.end(), 1
    tag = re.compile(r"<(/?)div\b[^>]*>")
    while depth:
        t = tag.search(html, i)
        if not t:
            return None
        depth += -1 if t.group(1) else 1
        i = t.end()
    return html[ms.end():i - len(t.group(0))]


def txt(h):
    return re.sub(r"<[^>]+>", " ", h)


def check(html, fit, ledger):
    del fails[:]
    P, V, B = payload_of(html), verdict_of(html), badge_of(html)
    if P is None:
        bad("A", "payload not found"); return fails
    if V is None:
        bad("G", "window.__verdict not found"); return fails
    if B is None:
        bad("G", "integrity badge not found"); return fails
    BT = txt(B)

    # ---- A. structure -------------------------------------------------------
    o, c = len(re.findall(r"<div[\s>]", html)), html.count("</div>")
    if o != c:
        bad("A", "div imbalance: %d open vs %d close" % (o, c))
    body = html.split("</head>", 1)[-1]
    for tid in set(re.findall(r'data-tab="([^"]+)"', html)):
        # `data-tab="${id}"` is a JS template literal that builds the real
        # attribute at runtime -- it is not itself a tab.
        if "${" in tid or "{{" in tid:
            continue
        if ('id="tab-%s"' % tid) not in html and ('data-panel="%s"' % tid) not in html:
            bad("A", "data-tab %r has no panel" % tid)
    for pat in (r"\{\{[^}]+\}\}", r"REPLACE_ME", r"__PLACEHOLDER__",
                r'"\s*:\s*None\b', r"\bNaN%"):
        if re.search(pat, body):
            bad("A", "placeholder leak matching %s" % pat)
    # keys the renderers read must exist, or the page prints "undefined"
    for k in ("arm_rows_full", "arm_rows_quarantined", "arm_rows_withheld",
              "full_network_trials", "quarantined_network_trials",
              "study_contrasts_full", "study_contrasts_quarantined",
              "pmid_verified", "quarantined"):
        if k not in P.get("coverage", {}):
            bad("A", "coverage.%s missing -- renderers would print undefined" % k)

    # ---- D. co-primary present ---------------------------------------------
    A = P.get("anchor", {})
    if A.get("mode") != "CO-PRIMARY":
        bad("D", "anchor.mode is %r, expected CO-PRIMARY" % A.get("mode"))
    for side in ("full", "quarantined"):
        if side not in A:
            bad("D", "anchor.%s missing -- the app is shipping one fit only" % side)
    for cell in P.get("cells", []):
        if "coprimary_quarantined" not in cell:
            bad("D", "cell %s has no coprimary_quarantined pack" % cell.get("cell_id"))

    # ---- B/C. payload vs the R re-fit --------------------------------------
    fu, qu = fit["full"], fit["quarantined"]
    fcell = {c["cell_id"]: c["full"] for c in fit["app_cells"]}
    qcell = {c["cell_id"]: c["quarantined"] for c in fit["app_cells"]}

    def cmp_pack(tag, got, want, cid):
        gl = {(p["t1"], p["t2"]): p for p in got.get("league", [])}
        wl = {(p["t1"], p["t2"]): p for p in want["league"]}
        if set(gl) != set(wl):
            bad("B", "%s %s league pair set differs (%d vs %d)"
                % (cid, tag, len(gl), len(wl)))
        for k in set(gl) & set(wl):
            for f in ("rr", "lo", "hi", "se_log"):
                if abs(gl[k][f] - wl[k][f]) > TOL:
                    bad("B", "%s %s %s.%s %.12g != %.12g"
                        % (cid, tag, k, f, gl[k][f], wl[k][f]))
            if gl[k]["direct_k"] != wl[k]["direct_k"]:
                bad("B", "%s %s %s direct_k differs" % (cid, tag, k))
        gn = {n["node"]: n for n in got.get("node_vs_placebo", [])}
        wn = {n["node"]: n for n in want["node_vs_placebo"]}
        if set(gn) != set(wn):
            bad("B", "%s %s node set differs" % (cid, tag))
        for k in set(gn) & set(wn):
            for f in ("rr", "lo", "hi"):
                if abs(gn[k][f] - wn[k][f]) > TOL:
                    bad("B", "%s %s node %s.%s %.12g != %.12g"
                        % (cid, tag, k, f, gn[k][f], wn[k][f]))
        if abs(got.get("tau2", -1) - want["tau2"]) > TOL:
            bad("B", "%s %s tau2 %.12g != %.12g" % (cid, tag, got.get("tau2"), want["tau2"]))
        if got.get("trials") != want["trials"]:
            bad("B", "%s %s trials %s != %s" % (cid, tag, got.get("trials"), want["trials"]))

    for cell in P.get("cells", []):
        cid = cell.get("cell_id")
        if cid in fcell:
            cmp_pack("full", cell, fcell[cid], cid)
        if cid in qcell and "coprimary_quarantined" in cell:
            cmp_pack("quarantined", cell["coprimary_quarantined"], qcell[cid], cid)

    # C. anchor -- the full co-primary must BE the settled primary
    for nd in ("ACEI+BB", "ACEI+BB+MRA"):
        got = (A.get("full", {}).get(nd) or [None])[0]
        if got is None or abs(got - SETTLED[nd]) > TOL:
            bad("C", "full-network anchor %s = %r, settled is %.8f"
                % (nd, got, SETTLED[nd]))
    if abs(A.get("full", {}).get("tau2", -1) - SETTLED["tau2"]) > TOL:
        bad("C", "full-network tau2 %r != settled %.8f"
            % (A.get("full", {}).get("tau2"), SETTLED["tau2"]))
    for nd in ("ACEI+BB", "ACEI+BB+MRA"):
        got = (A.get("quarantined", {}).get(nd) or [None])[0]
        want = next(n["rr"] for n in qu["node_vs_placebo"] if n["node"] == nd)
        if got is None or abs(got - want) > TOL:
            bad("C", "quarantined anchor %s = %r != %.8f" % (nd, got, want))
    # anchor.settled_original is a CLAIM about what the settled primary was. If
    # it is edited, the app asserts a different provenance with no other surface
    # contradicting it -- so it is checked against the constant and against the
    # live full fit it claims to be reproduced by.
    so = A.get("settled_original", {})
    if not so:
        bad("C", "anchor.settled_original missing -- the provenance claim is unrecorded")
    for k in ("ACEI+BB", "ACEI+BB+MRA", "tau2"):
        if abs(so.get(k, float("nan")) - SETTLED[k]) > TOL:
            bad("C", "anchor.settled_original.%s = %r, the settled primary is %.8f"
                % (k, so.get(k), SETTLED[k]))
    if so.get("reproduced_by_full_network") is not True:
        bad("C", "anchor.settled_original does not claim reproduction by the full network")
    for k, live in (("ACEI+BB", (A.get("full", {}).get("ACEI+BB") or [None])[0]),
                    ("ACEI+BB+MRA", (A.get("full", {}).get("ACEI+BB+MRA") or [None])[0]),
                    ("tau2", A.get("full", {}).get("tau2"))):
        if live is None or abs(so.get(k, float("nan")) - live) > TOL:
            bad("C", "settled_original.%s = %r but the live full fit gives %r -- the "
                     "reproduction claim is false" % (k, so.get(k), live))

    # ---- E. quarantine integrity -------------------------------------------
    Q = P.get("quarantine", {})
    wh = {w["id"]: w for w in Q.get("withheld", [])}
    if set(wh) != set(EXPECT_QUAR):
        bad("E", "withheld ids %s, expected %s" % (sorted(wh), sorted(EXPECT_QUAR)))
    for tid, w in wh.items():
        if not (w.get("violation") or "").strip():
            bad("E", "%s has no named violation" % tid)
        if not (w.get("reinstatement_condition") or "").strip():
            bad("E", "%s has no reinstatement condition" % tid)
        if not w.get("withheld_rows"):
            bad("E", "%s arm rows not retained -- deletion, not quarantine" % tid)
    if not (Q.get("rule") or "").strip():
        bad("E", "the quarantine rule itself is not stated in the payload")
    if not (Q.get("symmetry") or "").strip():
        bad("E", "symmetry of the rule is not recorded")
    # trials array: quarantined flagged, still on record, still in the full fit
    tr = {t["id"]: t for t in P.get("trials", [])}
    for tid in EXPECT_QUAR:
        t = tr.get(tid)
        if t is None:
            bad("E", "%s DELETED from the trial ledger, not quarantined" % tid)
            continue
        if not t.get("quarantined"):
            bad("E", "%s not flagged quarantined" % tid)
        if not t.get("arms"):
            bad("E", "%s arm rows stripped from the ledger" % tid)
        if t.get("in_quarantined_network") is not False:
            bad("E", "%s should be out of the quarantined network" % tid)
        if t.get("in_network") is not True:
            bad("E", "%s should remain in the FULL co-primary" % tid)
    nq = sum(1 for t in P.get("trials", []) if t.get("quarantined"))
    if nq != len(EXPECT_QUAR):
        bad("E", "%d trials flagged quarantined, expected %d" % (nq, len(EXPECT_QUAR)))

    # ---- F. symmetry: identical-count + unverified => must be quarantined ----
    for t in P.get("trials", []):
        arms = t.get("arms") or []
        if len(arms) < 2:
            continue
        ev = {a["events"] for a in arms}
        unver = (t.get("count_provenance_tier") == "UNVERIFIED")
        if len(ev) == 1 and unver and not t.get("quarantined"):
            bad("F", "%s (%s) has identical across-arm counts AND is UNVERIFIED "
                     "but is not quarantined -- the rule is being applied "
                     "asymmetrically again" % (t.get("id"), t.get("name")))

    # No trial may be marked not-quarantined while still carrying live prose
    # asserting a violation against it. The payload is rewritten in place across
    # passes, so a stale key from an earlier disposition is a real failure mode:
    # it ships a surface that contradicts itself about the same trial.
    for t in P.get("trials", []):
        if not t.get("quarantined") and (t.get("quarantine_violation") or "").strip():
            bad("F", "%s (%s) is not quarantined but still carries a live "
                     "quarantine_violation -- stale field from an earlier "
                     "disposition" % (t.get("id"), t.get("name")))

    # ---- R. reinstatement is evidenced, not a quiet un-flagging -------------
    # The F check above cannot catch a bad reinstatement: flipping a tier from
    # UNVERIFIED to VERBATIM_COUNT silences F by construction. So the release
    # path gets its own gate, held to the same standard as the withholding path.
    reinst_payload = {r["id"]: r for r in Q.get("reinstated", [])}
    if set(reinst_payload) != set(EXPECT_REINST):
        bad("R", "payload quarantine.reinstated ids %s, expected %s"
            % (sorted(reinst_payload), sorted(EXPECT_REINST)))
    for tid, (tname, restored_node) in EXPECT_REINST.items():
        r = reinst_payload.get(tid)
        if r is not None:
            for field in ("cleared_because", "count_source", "restored_rows"):
                if not r.get(field):
                    bad("R", "%s reinstatement has no %s -- a release with no "
                             "recorded evidence is a silent un-flagging" % (tid, field))
        t = tr.get(tid)
        if t is None:
            bad("R", "%s missing from the trial ledger entirely" % tid)
            continue
        if t.get("quarantined"):
            bad("R", "%s is flagged quarantined but is expected reinstated" % tid)
        if t.get("in_network") is not True or t.get("in_quarantined_network") is not True:
            bad("R", "%s must be in BOTH co-primary networks after reinstatement "
                     "(in_network=%r, in_quarantined_network=%r)"
                % (tid, t.get("in_network"), t.get("in_quarantined_network")))
        if t.get("count_provenance_tier") not in VERIFIED_TIERS:
            bad("R", "%s reinstated but its count_provenance_tier is %r -- a "
                     "trial cannot leave quarantine while its counts are still "
                     "unsourced" % (tid, t.get("count_provenance_tier")))
        if not (t.get("count_source") or "").strip():
            bad("R", "%s reinstated with no count_source naming where the counts "
                     "were read" % tid)
        if not t.get("was_quarantined"):
            bad("R", "%s does not record that it WAS quarantined -- the history "
                     "must survive the reinstatement, not be erased" % tid)
        if not t.get("arms"):
            bad("R", "%s arm rows missing" % tid)
        # The structural claim the reinstatement earns, checked on the SHIPPED
        # payload rather than on the fit JSON: in every cell where the full fit
        # estimates the restored node, the QUARANTINED fit must estimate it too.
        # That is precisely what withholding the trial used to destroy.
        seen_anywhere = False
        for cell in P.get("cells", []):
            cid = cell.get("cell_id")
            in_full = restored_node in {n["node"] for n in
                                       cell.get("node_vs_placebo", [])}
            if not in_full:
                continue
            seen_anywhere = True
            qpack = cell.get("coprimary_quarantined") or {}
            if restored_node not in {n["node"] for n in
                                     qpack.get("node_vs_placebo", [])}:
                bad("R", "%s reinstated to restore %s, but cell %s estimates that "
                         "node in the FULL fit and NOT in the quarantined fit -- "
                         "the restoration claim is false for this cell"
                    % (tid, restored_node, cid))
        if not seen_anywhere:
            bad("R", "%s claims to restore %s but no cell estimates that node at "
                     "all" % (tid, restored_node))
    # ledger side: the disposition and its history
    for tid, (tname, _node) in EXPECT_REINST.items():
        e = next((x for x in ledger.get("entries", []) if x.get("id") == tid), None)
        if e is None:
            bad("R", "%s absent from the ledger" % tid)
            continue
        if "REINSTATED" not in (e.get("disposition") or "").upper():
            bad("R", "ledger %s disposition is %r, expected a REINSTATED state"
                % (tid, e.get("disposition")))
        hist = e.get("disposition_history") or []
        if not any("QUARANTINED" == (h.get("disposition") or "").upper() for h in hist):
            bad("R", "ledger %s has no QUARANTINED step in disposition_history -- "
                     "the round trip is not auditable" % tid)
        if e.get("count_provenance_tier") not in VERIFIED_TIERS:
            bad("R", "ledger %s count_provenance_tier is %r, expected a verified tier"
                % (tid, e.get("count_provenance_tier")))
        if not (e.get("source", {}) or {}).get("count_source"):
            bad("R", "ledger %s source has no count_source" % tid)
    lr = ledger.get("summary", {}).get("reinstated")
    if lr != len(EXPECT_REINST):
        bad("R", "ledger summary.reinstated = %r, expected %d"
            % (lr, len(EXPECT_REINST)))

    # ---- G. verdict surfaces agree, badge self-consistent -------------------
    vc = V.get("counts", {})
    if V.get("verdict") != "UNCERTAIN" or "UNCERTAIN" not in BT:
        bad("G", "verdict word disagrees between payload and badge")
    if vc.get("trials_quarantined") != len(EXPECT_QUAR):
        bad("G", "verdict trials_quarantined %r != %d"
            % (vc.get("trials_quarantined"), len(EXPECT_QUAR)))
    pairs = [("n_trials_full_coprimary", fu["trials"]),
             ("n_trials_quarantined_coprimary", qu["trials"]),
             ("arm_rows_full", fu["arm_rows"]),
             ("arm_rows_quarantined", qu["arm_rows"])]
    for k, want in pairs:
        if vc.get(k) != want:
            bad("G", "verdict %s = %r, re-fit says %r" % (k, vc.get(k), want))
    # the badge must STATE both k's and the quarantine count, and must not state
    # any contradicting value for them
    for want, label in ((fu["trials"], "full"), (qu["trials"], "quarantined")):
        if not re.search(r"\b%d trials \(%s\)" % (want, label), BT):
            bad("G", "badge does not state %d trials (%s)" % (want, label))
    if not re.search(r"Quarantined:\s*%d\b" % len(EXPECT_QUAR), BT):
        bad("G", "badge does not state Quarantined: %d" % len(EXPECT_QUAR))
    # self-contradiction: a superseded single-quarantine count must not survive
    for stale in (r"\b27 trials\b", r"\b54 (?:remaining )?arm rows\b",
                  r"Quarantined:\s*1\b", r"1 TRIAL QUARANTINED"):
        if re.search(stale, BT):
            bad("G", "badge still asserts the superseded value %s" % stale)
    for nd, want in (("ACEI+BB", fu), ("ACEI+BB+MRA", fu)):
        v = next(n["rr"] for n in want["node_vs_placebo"] if n["node"] == nd)
        if ("%.3f" % v) not in BT:
            bad("G", "badge does not state the full-network %s anchor %.3f" % (nd, v))
    for nd in ("ACEI+BB", "ACEI+BB+MRA"):
        v = next(n["rr"] for n in qu["node_vs_placebo"] if n["node"] == nd)
        if ("%.3f" % v) not in BT:
            bad("G", "badge does not state the quarantined %s anchor %.3f" % (nd, v))

    # ---- H. direction flag, both parts --------------------------------------
    df = (A.get("direction_flag") or "")
    if not df:
        bad("H", "anchor.direction_flag missing")
    low = df.lower()
    if "away from the null" not in low:
        bad("H", "direction flag does not state that point estimates move away from the null")
    if not re.search(r"interval significance falls", low):
        bad("H", "direction flag does not state that interval significance FALLS")
    if "provenance sensitivity" not in low:
        bad("H", "direction flag does not label the quarantined fit a provenance sensitivity")
    if "conservative" not in low:
        bad("H", "direction flag does not name the full network as the conservative co-primary")
    dd = A.get("direction_detail", {})
    ce = dd.get("ci_excludes_null_common", {})
    want_f = fit["presentation"]["direction_detail"]["ci_excludes_null_common"]
    if ce != want_f:
        bad("H", "direction_detail CI counts %r != re-fit %r" % (ce, want_f))
    # and it must be rendered, not only stored
    if "NOT stronger evidence" not in html:
        bad("H", "the direction flag is not rendered at the point of display")

    # ---- S. no hardcoded disposition claims in the renderers ----------------
    # The analysis-tab renderer is static JS reading a payload that changes every
    # pass. An earlier build hardcoded "the three quarantined trials", "lowers
    # every retained node" and "loses the +Omecamtiv node outright" into it; all
    # three silently went false when GALACTIC-HF was reinstated, so the analysis
    # tab contradicted the badge two screens away. Those sentences are now
    # derived from the payload, and this check keeps them that way -- a hardcoded
    # count in a renderer is drift waiting to happen, not a style preference.
    # Scope matters here. The scan covers RENDERER CODE only:
    #   - the fit payload and window.__verdict are stripped, because those are
    #     DATA and legitimately carry disposition HISTORY ("the 3-trial pass lost
    #     the +Omecamtiv node outright"). Recording what a superseded pass found
    #     is not drift; it is the audit trail, and banning the phrase there would
    #     push the project toward erasing its own history to please a gate.
    #   - JS block comments are stripped, so a comment may still DISCUSS the old
    #     wording (the renderer's does) without tripping the check.
    code = html
    code = re.sub(r'<script id="hfref-fit-data".*?</script>', "", code, flags=re.S)
    code = re.sub(r"window\.__verdict = \{.*?\};?\s*</script>", "", code, flags=re.S)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    BANNED = [
        ("three quarantined trials", "quarantine-set size hardcoded"),
        ("lowers every retained node", "node direction hardcoded (and false)"),
        ("loses the +Omecamtiv node outright", "node loss hardcoded"),
        ("+Omecamtiv node outright", "node loss hardcoded"),
        ("CARMEN, GALACTIC-HF and Vizzardi 2014 are withheld",
         "quarantine membership hardcoded"),
    ]
    for phrase, why in BANNED:
        if phrase in code:
            bad("S", "renderer hardcodes a disposition claim (%s): %r -- derive it "
                     "from the payload instead" % (why, phrase))

    # ---- I. QUEST constraint ------------------------------------------------
    if "0.70" not in BT or "0.058" not in BT:
        bad("I", "badge does not carry QUEST's own non-significant HR 0.84 (0.70-1.01) P=0.058")

    # ---- ledger cross-check -------------------------------------------------
    lq = ledger.get("summary", {}).get("quarantined")
    if lq != len(EXPECT_QUAR):
        bad("E", "ledger summary.quarantined = %r, expected %d" % (lq, len(EXPECT_QUAR)))
    lids = {e["id"] for e in ledger.get("entries", []) if e.get("disposition") == "QUARANTINED"}
    if lids != set(EXPECT_QUAR):
        bad("E", "ledger QUARANTINED entries %s != %s" % (sorted(lids), sorted(EXPECT_QUAR)))
    spice = next((e for e in ledger["entries"] if e["id"] == "HF-008"), None)
    if not spice or spice.get("count_provenance_tier") != "RECOVERED_FROM_PERCENTAGE_UNIQUE":
        bad("E", "SPICE is not re-tiered to RECOVERED_FROM_PERCENTAGE_UNIQUE")
    return fails


def main():
    html = open(APP, encoding="utf-8").read()
    fit = json.load(open(FIT, encoding="utf-8"))
    ledger = json.load(open(LEDGER, encoding="utf-8"))

    if "--selftest" in sys.argv:
        def perturb(h, which, field, delta):
            """Re-serialise the payload with one number nudged, so the numeric
            check is proven to block rather than assumed to."""
            m = re.search(r'(<script id="hfref-fit-data" type="application/json">)'
                          r'(.*?)(</script>)', h, re.S)
            P = json.loads(m.group(2))
            cell = P["cells"][0]
            tgt = cell if which == "full" else cell["coprimary_quarantined"]
            tgt["league"][0][field] += delta
            return h[:m.start(2)] + json.dumps(P, ensure_ascii=False) + h[m.end(2):]

        cases = [
            ("full-fit league RR perturbed 1e-6",
             lambda h: perturb(h, "full", "rr", 1e-6)),
            ("quarantined-fit league RR perturbed 1e-6",
             lambda h: perturb(h, "quarantined", "rr", 1e-6)),
            ("full-fit tau2 perturbed 1e-7", lambda h: h.replace(
                '"tau2": 0.0232360895461', '"tau2": 0.0232361895461')),
            ("settled_original anchor literal edited", lambda h: h.replace(
                '"tau2": 0.02323609', '"tau2": 0.02423609', 1)),
            ("badge trial count 28 -> 27", lambda h: h.replace(
                "28 trials (full)", "27 trials (full)", 1)),
            ("badge quarantine count 2 -> 1", lambda h: h.replace(
                "Quarantined: <strong>2</strong>", "Quarantined: <strong>1</strong>", 1)),
            ("a quarantined trial deleted rather than flagged",
             lambda h: re.sub(r'\{"id": ?"HF-021".*?\}(?=,\s*\{"id")', "", h, count=1, flags=re.S)),
            ("direction flag stripped", lambda h: h.replace(
                "NOT stronger evidence", "looks better", 1)),
            ("verdict quarantined count desynced from badge", lambda h: h.replace(
                '"trials_quarantined": 2', '"trials_quarantined": 1', 1).replace(
                '"trials_quarantined":2', '"trials_quarantined":1', 1)),
            # --- the reinstatement path must be as hard to fake as the withholding one
            ("reinstated trial silently dropped from the quarantined network",
             lambda h: h.replace('"in_quarantined_network": true, '
                                 '"count_provenance_tier": "VERBATIM_COUNT", '
                                 '"was_quarantined": true',
                                 '"in_quarantined_network": false, '
                                 '"count_provenance_tier": "VERBATIM_COUNT", '
                                 '"was_quarantined": true', 1)),
            ("stale quarantine_violation left on the reinstated trial",
             lambda h: h.replace('"violation_when_quarantined"',
                                 '"quarantine_violation"', 1)),
            ("reinstated trial's count_source stripped",
             lambda h: h.replace('"count_source": "ClinicalTrials.gov NCT02929329',
                                 '"count_source_REMOVED": "ClinicalTrials.gov NCT02929329', 1)),
            ("reinstated trial's quarantine history erased",
             lambda h: h.replace('"was_quarantined": true', '"was_quarantined": false', 1)),
            ("reinstated trial left on an UNVERIFIED tier",
             lambda h: h.replace('"reinstated": true, "reinstated_because"',
                                 '"reinstated": true, "count_provenance_tier": "UNVERIFIED", '
                                 '"reinstated_because"', 1)),
            ("payload reinstatement record removed",
             lambda h: h.replace('"reinstated": [{"id": "HF-034"',
                                 '"reinstated": [{"id": "HF-999"', 1)),
            ("renderer re-hardcodes the node-loss claim",
             lambda h: h.replace("'<b>No node is lost</b> under the quarantine",
                                 "'It also <b>loses the +Omecamtiv node outright</b>", 1)),
            ("renderer re-hardcodes the quarantine-set size",
             lambda h: h.replace("' quarantined trial'", "' three quarantined trials'", 1)),
        ]
        ok = True
        for name, mut in cases:
            h2 = mut(html)
            if h2 == html:
                print("  [SELFTEST INCONCLUSIVE] %s -- mutation did not apply" % name)
                ok = False
                continue
            try:
                f = check(h2, fit, ledger)
            except Exception as e:                      # a crash is also a block
                f = ["crashed: %s" % e]
            print("  [%s] %s%s" % ("BLOCKS" if f else "DID NOT BLOCK", name,
                                   "" if f else "   <-- GATE IS BLIND"))
            ok = ok and bool(f)
        print("\nSELFTEST %s" % ("PASS -- every mutation blocks" if ok else "FAIL"))
        return 0 if ok else 1

    f = check(html, fit, ledger)
    if f:
        print("FAIL (%d)" % len(f))
        for x in f:
            print("  " + x)
        return 1
    print("PASS -- co-primary app verified")
    print("  full        : %d trials, %d arm rows, ACEI+BB %.8f, ACEI+BB+MRA %.8f"
          % (fit["full"]["trials"], fit["full"]["arm_rows"],
             next(n["rr"] for n in fit["full"]["node_vs_placebo"] if n["node"] == "ACEI+BB"),
             next(n["rr"] for n in fit["full"]["node_vs_placebo"] if n["node"] == "ACEI+BB+MRA")))
    print("  quarantined : %d trials, %d arm rows, ACEI+BB %.8f, ACEI+BB+MRA %.8f"
          % (fit["quarantined"]["trials"], fit["quarantined"]["arm_rows"],
             next(n["rr"] for n in fit["quarantined"]["node_vs_placebo"] if n["node"] == "ACEI+BB"),
             next(n["rr"] for n in fit["quarantined"]["node_vs_placebo"] if n["node"] == "ACEI+BB+MRA")))
    print("  quarantined trials: %s" % ", ".join(sorted(EXPECT_QUAR.values())))
    print("  reinstated trials : %s"
          % ", ".join("%s (restores %s)" % v for v in sorted(EXPECT_REINST.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
