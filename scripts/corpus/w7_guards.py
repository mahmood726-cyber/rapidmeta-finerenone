#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W7 -- build-time guards that convert silent data defects into BLOCKED pages.

WHY THESE ARE GUARDS AND NOT FIXES. Every class here needs per-page evidence that does
not exist anywhere in the corpus: which estimand a published number actually is, which
direction an outcome runs in, whether two endpoints are commensurate, which trial a
NULLED: key was supposed to bind to. None of that can be invented at 863x. What CAN be
done mechanically is refuse to let the defect stay silent -- turn it into a countable,
named, per-page backlog item that a human resolves.

WHY THIS DOES NOT EDIT PAGES. A blocked page stays live exactly as it is. Shipping code
that blanks several hundred pooled results the moment a deploy lands would be a far
larger change than the defects it is surfacing, and it would do it without anyone having
read a single one of them. So W7 is a GATE, not a wave: it reads the built HTML, decides
blocked/clear, and writes the backlog. Nothing about a page changes until a human works
the backlog item.

PRECISION IS NOT UNIFORM ACROSS THE SIX, and the report says so per guard. G1, G2, G5
and G6 test for a construct that is either present or absent -- they are exact. G3 and G4
are triage: they narrow 863 pages to a reviewable set, and some of what they surface will
be fine. A triage list presented as a defect list is how a 32:1 over-firing detector ends
up driving 32 unnecessary edits, which is the mistake D16 records in the plan.

Usage:
    python w7_guards.py --root . --out F:\E156\outputs\corpus_blocked_backlog.md
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_wave as W                                        # noqa: E402
import corpus_detectors as CD                                  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --------------------------------------------------------------------------- guards

# D8. The page infers what kind of quantity it is pooling from whether a hazard-ratio
# field happens to be populated. "If a pubHR is present this is an HR, otherwise call it
# an RR" is not a fact about the estimand; it is a fact about which column was filled in.
ESTIMAND_INFER = re.compile(
    r'estimandType:[^,;}]{0,40}\?\?\([^)]{0,60}pubHR\?"HR":"RR"\)')
ESTIMAND_EXPLICIT = re.compile(r'estimandType:"(?:OR|RR|HR)"')
PUBHR_FIELD = re.compile(r"\bpubHR:")

# D14. Two field-name families for the same quantity. A lookup written against one family
# silently misses records written in the other, and the miss falls through to recomputing
# from the 2x2 table -- which pools a different quantity than the evidence card displays.
FAMILY_A = re.compile(r"\bpublishedHR\b|\bhrLCI\b|\bhrUCI\b")
FAMILY_B = re.compile(r"\bpubHR\b|\bpubHR_LCI\b|\bpubHR_UCI\b")

# D9. No page in the corpus carries any direction concept, so every outcome is pooled as
# though smaller is better. That is right for mortality and wrong for response, survival,
# remission and cure. Triage vocabulary, deliberately narrow, and NEVER used to set the
# value -- only to decide whose direction a human must look at.
BENEFIT_SHAPED = re.compile(
    r"\b(response|responder|remission|survival|cure[ds]?|clearance|success|"
    r"achievement|improvement|recovery|eradication|seroconversion|"
    r"sustained virologic|complete response|overall survival)\b", re.I)
DIRECTION_FIELD = re.compile(r"\bdirection\s*:\s*[\"']?(?:higher|lower)_is_better")

# D1. Two independent resolutions of what "default" means. When they disagree the page
# labels one outcome and pools another.
SCOPE_RESOLVER = re.compile(r"applyOutcomeScope")
LABEL_RESOLVER = re.compile(r"outcomeLabel\s*[:=(]")

# D11. A NULLED: key is the marker that a trial identity was voided. A voided identity
# participating as canonical means the page is pooling a record nobody could bind.
NULLED_KEY = re.compile(r"NULLED:")
AUTO_INCLUDE = re.compile(r"AUTO_INCLUDE_TRIAL_IDS\s*=\s*new Set\(\[([^\]]*)\]\)")

# D10. Endpoint keys and estimand types actually present in the pooled data.
OUTCOME_KEY = re.compile(r'\bkey:"([^"]{1,40})"')
ESTIMAND_ANY = re.compile(r'estimandType:"([A-Z]{2})"')

# Topics whose reviews legitimately do not pool. Not defects, and explicitly protected
# from retirement by policy: a vaccine review that reports per-trial efficacy without a
# pooled diamond is doing the right thing, and so is a Cochrane-style narrative synthesis.
NONPOOL_TOPIC = re.compile(
    r"VACCIN|PNEUMO|PREVNAR|ROTAVIRUS|\bHPV\b|INFLUENZA|MENINGOCOC|TYPHOID|"
    r"MALARIA_VACC|COVID19_VACC|BCG_|POLIO|MEASLES|DENGUE|RSV_", re.I)
NONPOOL_DECLARED = re.compile(
    r"not pooled|no pooled estimate|narrative synthesis|pooling was not|"
    r"meta-analysis was not (?:performed|undertaken)", re.I)


def guards_for(name: str, s: str) -> list[dict]:
    """Return the guards that fire on this page, each with its evidence."""
    out = []

    # ---- G1 estimand-required (exact) --------------------------------------
    if ESTIMAND_INFER.search(s):
        explicit = len(ESTIMAND_EXPLICIT.findall(s))
        pubhr = len(PUBHR_FIELD.findall(s))
        if pubhr > explicit:
            out.append({
                "guard": "estimand-required",
                "klass": "D8",
                "precision": "exact",
                "evidence": f"estimandType inferred from pubHR presence; "
                            f"{pubhr} pubHR field(s) vs {explicit} explicit "
                            f"estimandType declaration(s)"})

    # ---- G2 accessor with a 2x2 fallback (exact) ---------------------------
    if FAMILY_A.search(s) and FAMILY_B.search(s):
        out.append({
            "guard": "accessor-no-2x2-fallback",
            "klass": "D14",
            "precision": "exact",
            "evidence": "both field-name families present (publishedHR/hrLCI and "
                        "pubHR/pubHR_LCI); a lookup miss falls through to the 2x2 "
                        "recomputation instead of blocking"})

    # ---- G3 direction plumbing defaulted (triage) --------------------------
    if not DIRECTION_FIELD.search(s):
        hits = sorted({h.lower() for h in BENEFIT_SHAPED.findall(s)})
        if hits:
            out.append({
                "guard": "direction-defaulted",
                "klass": "D9",
                "precision": "triage",
                "evidence": f"no direction field anywhere; benefit-shaped outcome "
                            f"vocabulary present: {hits[:6]}"})

    # ---- G4 incommensurate pool (triage) -----------------------------------
    keys = {k for k in OUTCOME_KEY.findall(s)}
    ests = {e for e in ESTIMAND_ANY.findall(s)}
    if len(ests) > 1:
        out.append({
            "guard": "incommensurate-pool",
            "klass": "D10",
            "precision": "triage",
            "evidence": f"pooled records declare more than one estimand type: "
                        f"{sorted(ests)}"})
    elif len(keys) > 1:
        out.append({
            "guard": "incommensurate-pool",
            "klass": "D10",
            "precision": "triage",
            "evidence": f"pooled records span {len(keys)} endpoint keys: "
                        f"{sorted(keys)[:6]}"})

    # ---- G5 single outcome resolver (exact) --------------------------------
    if SCOPE_RESOLVER.search(s) and LABEL_RESOLVER.search(s):
        out.append({
            "guard": "single-outcome-resolver",
            "klass": "D1",
            "precision": "exact",
            "evidence": "applyOutcomeScope and outcomeLabel resolve 'default' "
                        "independently; nothing forces them to agree"})

    # ---- G6 NULLED canonical key (exact, build-breaking) -------------------
    if NULLED_KEY.search(s):
        m = AUTO_INCLUDE.search(s)
        canonical = bool(m and "NULLED:" in m.group(1))
        out.append({
            "guard": "nulled-canonical-key",
            "klass": "D11",
            "precision": "exact",
            "evidence": (f"{len(NULLED_KEY.findall(s))} NULLED: key(s); "
                         f"{'participating as canonical in AUTO_INCLUDE_TRIAL_IDS'
                            if canonical else 'present in page data'}")})
    return out


def first_pass_tag(name: str, s: str, fired: list[dict]) -> tuple[str, str]:
    """fixable / likely-retire / legitimately-non-poolable, with a reason."""
    if NONPOOL_TOPIC.search(name):
        return ("legitimately-non-poolable",
                "vaccine/immunisation topic: per-trial efficacy without a pooled "
                "diamond is correct here, and policy protects it from retirement")
    if NONPOOL_DECLARED.search(s):
        return ("legitimately-non-poolable",
                "the page itself declares that results are not pooled")
    names = {f["guard"] for f in fired}
    if "nulled-canonical-key" in names:
        return ("likely-retire",
                "a voided trial identity is participating as canonical; the binding "
                "cannot be re-resolved without reading the registry and the "
                "publication for each trial")
    if len([f for f in fired if f["precision"] == "exact"]) >= 3:
        return ("likely-retire",
                "three or more exact guards fire; the page's evidence base needs "
                "rebuilding rather than patching")
    return ("fixable",
            "the firing guards are shared-code or single-field problems")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default=r"F:\E156\outputs\corpus_blocked_backlog.md")
    ap.add_argument("--json-out", default=None)
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
        fired = guards_for(p.name, s)
        if not fired:
            clear.append(p.name)
            continue
        tag, why = first_pass_tag(p.name, s, fired)
        rows.append({"page": p.name, "guards": fired, "tag": tag, "why": why})

    by_guard = collections.Counter()
    for r in rows:
        for f in r["guards"]:
            by_guard[f["guard"]] += 1
    by_tag = collections.Counter(r["tag"] for r in rows)
    total = len(rows) + len(clear)

    L = []
    L.append("# W7 — blocked-page backlog\n")
    L.append(f"**Generated:** by `scripts/corpus/w7_guards.py` over {total} eligible "
             f"template pages ({len(excluded)} excluded by policy — the build lane "
             f"owns those).\n")
    L.append("**A blocked page stays live exactly as it is.** These guards do not edit "
             "pages and W7 ships no page change. Blocking means the page is enrolled in "
             "this backlog, where each item gets at most two root-cause fix attempts "
             "before retirement — and where a topic that legitimately does not pool is "
             "not a defect and is never retired for it.\n")
    L.append(f"| | |\n|---|--:|\n| Pages blocked | **{len(rows)}** |\n"
             f"| Pages clear | {len(clear)} |\n| Total eligible | {total} |\n")

    L.append("\n## Guards, and how much to trust each\n")
    L.append("| Guard | Class | Pages | Precision |\n|---|---|--:|---|")
    prec = {}
    for r in rows:
        for f in r["guards"]:
            prec[f["guard"]] = (f["klass"], f["precision"])
    for g, n in by_guard.most_common():
        k, pr = prec[g]
        L.append(f"| `{g}` | {k} | {n} | {pr} |")
    L.append("\n**exact** = the construct is either present or absent and the guard "
             "tests for it directly. **triage** = the guard narrows the corpus to a "
             "reviewable set and some of what it surfaces will be fine on inspection. "
             "Treating a triage list as a defect list is how an over-firing detector "
             "drives unnecessary edits; both are reported separately for that reason.\n")

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
        L.append("| Page | Guards | Why this tag |\n|---|---|---|")
        for r in sorted(sel, key=lambda x: x["page"]):
            gs = ", ".join(f"`{f['guard']}`" for f in r["guards"])
            L.append(f"| `{r['page']}` | {gs} | {r['why']} |")

    L.append("\n## Per-page evidence\n")
    for r in sorted(rows, key=lambda x: x["page"]):
        L.append(f"\n### `{r['page']}` — {r['tag']}\n")
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
        print(f"  {g:28s} {n}")
    print("  --")
    for t, n in by_tag.most_common():
        print(f"  {t:28s} {n}")
    print(f"\nbacklog -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
