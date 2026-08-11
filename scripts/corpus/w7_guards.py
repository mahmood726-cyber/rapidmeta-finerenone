#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W7 -- build-time guards that convert silent data defects into BLOCKED pages.

WHY GUARDS AND NOT FIXES. Every class here needs per-page evidence that exists nowhere
in the corpus: which estimand a published number actually is, which direction an outcome
runs in, whether two endpoints are commensurate, which trial a NULLED: key was supposed
to bind to. None of that can be invented at 863x. What CAN be done mechanically is
refuse to let the defect stay silent -- turn it into a countable, named, per-page
backlog item that a human resolves.

WHY THIS EDITS NOTHING. A blocked page stays live exactly as it is. Shipping code that
blanks several hundred pooled results the moment a deploy lands would be a far larger
change than the defects it surfaces, and would make it without anyone having read one of
them. W7 is a GATE: it reads the built HTML, decides blocked/clear, writes the backlog.

THE GUARDS RUN AGAINST PER-PAGE DATA, NOT SHARED TEMPLATE CODE. The first version of
this file tested the whole file and blocked 863 of 863 -- a tautology, not a backlog,
because the constructs it was matching are template code present on every page by
construction. A guard has to distinguish pages, so it reads only the extracted data
spans (realData, allOutcomes, evidence, AUTO_INCLUDE_TRIAL_IDS) via data_spans.py.

PRECISION IS NOT UNIFORM, and the report says so per guard. `exact` guards test a
construct that is present or absent in the page's own data. `triage` guards narrow the
corpus to a reviewable set and some of what they surface will be fine on inspection.
Presenting a triage list as a defect list is how an over-firing detector drives
unnecessary edits -- the mistake D16 records in the plan, where 33 flags held 1 real one.

Usage:
    python w7_guards.py --root . --out F:\E156\outputs\corpus_blocked_backlog.md
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_wave as W                                        # noqa: E402
import corpus_detectors as CD                                  # noqa: E402
import data_spans as DS                                        # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SHORTLABEL = re.compile(r"shortLabel:\"([^\"]{0,60})\"")
ESTIMAND = re.compile(r"estimandType:\"([A-Za-z]{2,3})\"")
TITLE = re.compile(r"title:\"([^\"]{0,200})\"")
FAM_A = re.compile(r"\b(?:publishedHR|hrLCI|hrUCI):")
FAM_B = re.compile(r"\b(?:pubHR|pubHR_LCI|pubHR_UCI):")
NULLED = re.compile(r"NULLED:")
TYPE_PRIMARY = re.compile(r"type:\"PRIMARY\"")

# An auto-generated slug: a long unbroken lowercase-alphanumeric run, which is what the
# registry-derived placeholder looks like ("participantswith1newmorp"). A real endpoint
# label has spaces.
PLACEHOLDER_LABEL = re.compile(r"^[a-z0-9]{18,}$")

# Direction vocabulary, deliberately narrow, matched against the page's own outcome
# TITLES only. Never used to SET a direction -- only to decide whose direction a human
# has to look at. The plan is explicit that inferring direction from an endpoint title
# is not safe ("Remaining eligible for SRT" reads as good to a token matcher).
BENEFIT_SHAPED = re.compile(
    r"\b(?:overall survival|progression[- ]free survival|\bOS\b|\bPFS\b|"
    r"response|responder|ACR\d\d|EASI\d\d|PASI\d\d|remission|"
    r"achiev\w*|cure[ds]?|clearance|eradication|seroconversion|"
    r"recovery|improvement|success)\b", re.I)
DIRECTION_FIELD = re.compile(r"direction\s*:\s*[\"']?(?:higher|lower)_is_better")

# Topics whose reviews legitimately may not pool. Protected from retirement by policy.
NONPOOL_TOPIC = re.compile(
    r"VACCIN|PNEUMO|PREVNAR|ROTAVIRUS|HPV_|INFLUENZA|MENINGOCOC|TYPHOID|"
    r"BCG_|POLIO|MEASLES|DENGUE|RSV_|IMMUNI[SZ]", re.I)


def page_data(s: str) -> str:
    ex = DS.extract(s)
    return "".join(ex["realData"]) + "".join(ex["allOutcomes"]) + "".join(ex["evidence"])


def guards_for(name: str, s: str, data: str) -> list[dict]:
    out = []
    labels = SHORTLABEL.findall(data)
    estimands = ESTIMAND.findall(data)
    titles = TITLE.findall(data)

    # ---- G1 estimand-required (exact) --------------------------------------
    # Every pooled outcome must declare what kind of quantity it is. Where it does
    # not, the engine infers it from whether a hazard-ratio field happens to be
    # populated -- a fact about which column was filled in, not about the estimand.
    if labels and len(estimands) < len(labels):
        out.append({
            "guard": "estimand-required", "klass": "D8", "precision": "exact",
            "evidence": f"{len(labels)} outcome record(s) but only {len(estimands)} "
                        f"explicit estimandType declaration(s); the remainder are "
                        f"inferred from pubHR presence"})

    # ---- G2 accessor with a 2x2 fallback (exact) ---------------------------
    a, b = len(FAM_A.findall(data)), len(FAM_B.findall(data))
    if a and b:
        out.append({
            "guard": "accessor-no-2x2-fallback", "klass": "D14", "precision": "exact",
            "evidence": f"this page's OWN data uses both field-name families "
                        f"({a} publishedHR/hrLCI, {b} pubHR/pubHR_LCI); a lookup "
                        f"written for one silently misses the other and falls through "
                        f"to recomputing from the 2x2 table, which pools a different "
                        f"quantity than the evidence card displays"})

    # ---- G3 direction plumbing defaulted (triage) --------------------------
    if not DIRECTION_FIELD.search(s):
        hits = sorted({h.lower() for t in titles for h in BENEFIT_SHAPED.findall(t)})
        if hits:
            out.append({
                "guard": "direction-defaulted", "klass": "D9", "precision": "triage",
                "evidence": f"no direction field exists anywhere in the corpus, so "
                            f"every outcome pools as though smaller is better; this "
                            f"page's own outcome titles include {hits[:5]}"})

    # ---- G4 incommensurate pool (triage) -----------------------------------
    prim = len(TYPE_PRIMARY.findall(data))
    distinct = sorted(set(estimands))
    if len(distinct) > 1:
        out.append({
            "guard": "incommensurate-pool", "klass": "D10", "precision": "triage",
            "evidence": f"records declare {len(distinct)} different estimand types "
                        f"{distinct}; pooling across them mixes quantities"})
    elif prim > 1 and len(set(titles)) > 1:
        out.append({
            "guard": "incommensurate-pool", "klass": "D10", "precision": "triage",
            "evidence": f"{prim} records typed PRIMARY with differing titles; whether "
                        f"they share an endpoint is a per-page judgement"})

    # ---- G5 unresolved outcome identity (exact) ----------------------------
    ph = sorted({l for l in labels if PLACEHOLDER_LABEL.match(l)})
    if ph:
        out.append({
            "guard": "single-outcome-resolver", "klass": "D1", "precision": "exact",
            "evidence": f"{len(ph)} outcome label(s) are unresolved registry slugs "
                        f"rather than endpoint names, e.g. {ph[:3]}; the outcome a "
                        f"reader is shown was never adjudicated"})

    # ---- G7 inadmissible counts (exact) ------------------------------------
    # Found by the render gate, not by design: AFICAMTEN_HCM_REVIEW renders res-or as
    # literally "NaN" -- before any wave, so it is not ours -- and plotly then throws
    # on rotate(0,NaN,...) because the NaN reaches an axis coordinate.
    #
    # The mechanism is in the binary pooling path. A record whose cE is null passes the
    # double-zero filter (0 !== null), gets a continuity correction of 0, and yields
    # c = null + 0 = 0, so logEff = log(a/b/0) = Infinity and vi = Infinity. Its weight
    # is 1/Infinity = 0, which looks harmless -- but Q accumulates w*logEff*logEff =
    # 0 * Infinity * Infinity = NaN, and NaN propagates through Q, I-squared, tau-squared
    # and the whole summary. One unusable count silently voids the entire analysis.
    #
    # This is the D20 class the plan scoped to W4b, which was not commissioned here. The
    # guard does not fix it; it makes the pages countable.
    counts = re.findall(r"\b([tc][EN]):(null|undefined|\"\"|NaN)", data)
    if counts:
        kinds = sorted({k for k, _ in counts})
        out.append({
            "guard": "inadmissible-counts", "klass": "D20", "precision": "exact",
            "evidence": f"{len(counts)} non-numeric count field(s) {kinds} in pooled "
                        f"records; in the binary path one of these makes Q, I2 and tau2 "
                        f"NaN and the pooled estimate renders as NaN"})

    # ---- G6 NULLED canonical key (exact, build-breaking) -------------------
    if NULLED.search(data):
        ex = DS.extract(s)
        auto = "".join(ex["AUTO_INCLUDE"])
        canonical = "NULLED:" in auto
        out.append({
            "guard": "nulled-canonical-key", "klass": "D11", "precision": "exact",
            "evidence": f"{len(NULLED.findall(data))} NULLED: key(s) in page data"
                        + (", participating as canonical in AUTO_INCLUDE_TRIAL_IDS"
                           if canonical else "")})
    return out


def first_pass_tag(name: str, data: str, fired: list[dict]) -> tuple[str, str]:
    if NONPOOL_TOPIC.search(name):
        return ("legitimately-non-poolable",
                "vaccine/immunisation topic: reporting per-trial efficacy without a "
                "pooled diamond is correct here. Policy protects it from retirement.")
    names = {f["guard"] for f in fired}
    exact = [f for f in fired if f["precision"] == "exact"]
    if "nulled-canonical-key" in names:
        return ("likely-retire",
                "a voided trial identity participates as canonical; re-resolving the "
                "binding needs the registry and the publication read per trial")
    if len(exact) >= 3:
        return ("likely-retire",
                f"{len(exact)} exact guards fire together; the evidence base needs "
                f"rebuilding rather than patching")
    return ("fixable",
            "the firing guards are single-field or shared-code problems")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default=r"F:\E156\outputs\corpus_blocked_backlog.md")
    ap.add_argument("--json-out", default=r"F:\E156\outputs\corpus_blocked_backlog.json")
    a = ap.parse_args()

    root = pathlib.Path(a.root)
    rows, clear, excluded = [], [], []
    for p in sorted(root.glob("*.html")):
        if W.is_excluded(p.name):
            excluded.append(p.name)
            continue
        s = p.read_text(encoding="utf-8", errors="replace")
        if not CD.is_template_page(s):
            continue
        data = page_data(s)
        fired = guards_for(p.name, s, data)
        if not fired:
            clear.append(p.name)
            continue
        tag, why = first_pass_tag(p.name, data, fired)
        rows.append({"page": p.name, "guards": fired, "tag": tag, "why": why})

    by_guard = collections.Counter()
    prec = {}
    for r in rows:
        for f in r["guards"]:
            by_guard[f["guard"]] += 1
            prec[f["guard"]] = (f["klass"], f["precision"])
    by_tag = collections.Counter(r["tag"] for r in rows)
    total = len(rows) + len(clear)

    L = ["# W7 — blocked-page backlog\n"]
    L.append(f"Generated by `scripts/corpus/w7_guards.py` over **{total}** eligible "
             f"template pages ({len(excluded)} excluded by policy — the build lane owns "
             f"those).\n")
    L.append("**A blocked page stays live exactly as it is.** These guards edit "
             "nothing and W7 ships no page change. Blocking means the page is enrolled "
             "here, where each item gets at most **two** root-cause fix attempts before "
             "retirement — and where a topic that legitimately does not pool is **not a "
             "defect** and is never retired for it.\n")
    L.append(f"| | |\n|---|--:|\n| Pages blocked | **{len(rows)}** |\n"
             f"| Pages clear | {len(clear)} |\n| Total eligible | {total} |\n")

    L.append("\n## Guards\n")
    L.append("| Guard | Class | Pages | Precision |\n|---|---|--:|---|")
    for g, n in by_guard.most_common():
        k, pr = prec[g]
        L.append(f"| `{g}` | {k} | {n} | {pr} |")
    L.append("\n`exact` — the construct is present or absent in the page's own data and "
             "the guard tests it directly. `triage` — the guard narrows the corpus to a "
             "reviewable set; some of what it surfaces will be fine on inspection. The "
             "two are reported separately because treating a triage list as a defect "
             "list is how an over-firing detector drives unnecessary edits.\n")

    L.append("\n## First-pass disposition\n")
    L.append("| Tag | Pages |\n|---|--:|")
    for t, n in by_tag.most_common():
        L.append(f"| {t} | {n} |")
    L.append("")

    for tag in ("legitimately-non-poolable", "likely-retire", "fixable"):
        sel = [r for r in rows if r["tag"] == tag]
        if not sel:
            continue
        L.append(f"\n## {tag} — {len(sel)} pages\n")
        if tag == "legitimately-non-poolable":
            L.append("**Not defects. Do not retire these for not pooling.**\n")
        L.append("| Page | Guards |\n|---|---|")
        for r in sorted(sel, key=lambda x: x["page"]):
            L.append(f"| `{r['page']}` | "
                     + ", ".join(f"`{f['guard']}`" for f in r["guards"]) + " |")

    L.append("\n## Per-page evidence\n")
    for r in sorted(rows, key=lambda x: x["page"]):
        L.append(f"\n### `{r['page']}` — {r['tag']}\n")
        L.append(f"_{r['why']}_\n")
        for f in r["guards"]:
            L.append(f"- **{f['guard']}** ({f['klass']}, {f['precision']}): "
                     f"{f['evidence']}")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    if a.json_out:
        pathlib.Path(a.json_out).write_text(
            json.dumps({"blocked": rows, "clear": clear, "excluded": excluded},
                       indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"eligible {total} | blocked {len(rows)} | clear {len(clear)}")
    for g, n in by_guard.most_common():
        print(f"  {g:28s} {n:4d}  ({prec[g][1]})")
    print("  --")
    for t, n in by_tag.most_common():
        print(f"  {t:28s} {n:4d}")
    print(f"\nbacklog -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
