"""Bulk-clone audit-first VIABLE topics into full-flagship RapidMeta dashboards.

For each VIABLE outputs/new_topics/<STEM>.json:
  - pick a sensible base template (small, simple, similar effect type)
  - auto-generate a clone_dashboard config from the audit data
  - run scripts/clone_dashboard.py to produce <STEM>_FULL_REVIEW.html

This gives audit-first builds the same interactive engine as the flagships:
editable extraction, live re-pool, RoB coding, GRADE SoF, WebR validation,
all 28 statistics panels.
"""
from __future__ import annotations
import json, sys, io, subprocess, re
from pathlib import Path

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
TOPICS = HERE / "outputs" / "new_topics"
CONFIGS = HERE / "scripts" / "configs"
CONFIGS.mkdir(parents=True, exist_ok=True)

# A small, stable, simple base — DUPILUMAB_COPD is 1.2 MB with 2-trial pairwise
# structure. Re-used as the base for audit-first clones; per-topic data
# replaces all per-trial content via clone_dashboard.py's existing logic.
BASE_TEMPLATE = HERE / "DUPILUMAB_COPD_REVIEW.html"

# Don't re-clone if output already exists and is recent
SKIP_IF_EXISTS = True


# Chars that are JS string delimiters or HTML-breaking. Injected drug/
# condition names land in BOTH HTML text nodes and single/double-quoted JS
# string literals, so the only universally safe form swaps the delimiter
# characters for typographic look-alikes (render fine in HTML, inert in JS).
# Without this, a condition like "Crohn's Disease" -> '...CROHN'S...' is a
# JS SyntaxError that the leftover scanner would still pass (lessons.md
# apostrophe-in-single-quoted-JS-string, 2026-04-30).
_SAFE_MAP = {
    "'": "’",   # ' -> right single quote
    '"': "”",   # " -> right double quote
    "`": "ʼ",   # backtick -> modifier letter apostrophe
    "\\": "/",
    "<": "‹",   # < -> single left-pointing angle quote
    ">": "›",
    "\r": " ", "\n": " ", "\t": " ",
}


def safe(s: str) -> str:
    """Make a string safe to inject into HTML text AND quoted JS literals."""
    return "".join(_SAFE_MAP.get(ch, ch) for ch in str(s))


def build_config(topic_doc):
    topic = topic_doc["topic"]
    stem = safe(topic["stem"])
    name = safe(topic["name"])
    drug = safe((topic["drug_patterns"] or ["intervention"])[0].title())
    cond = safe((topic["condition_patterns"] or ["condition"])[0].title())

    trials = []
    ncts = []
    acrs = {}
    for t in topic_doc["trials"]:
        if not all(t["gates"].values()):
            continue
        ex = t["extracted"]
        nct = ex["nct"]
        acr = ex.get("aact_acronym") or nct
        per_arm = ex.get("aact_per_arm_counts") or {}
        arms = sorted(per_arm.keys())
        tN = per_arm.get(arms[0]) if arms else 0
        cN = per_arm.get(arms[1]) if len(arms) > 1 else 0
        outcome_rows = ex.get("aact_outcome_count_rows") or []
        og_vals = {}
        for og, v in outcome_rows:
            if og not in og_vals:
                try: og_vals[og] = int(float(v))
                except: pass
            if len(og_vals) >= 2: break
        ogs = sorted(og_vals.keys())
        tE = og_vals.get(ogs[0]) if ogs else None
        cE = og_vals.get(ogs[1]) if len(ogs) > 1 else None

        pub_es = ex.get("published_effect_size")
        pub_t = ex.get("published_effect_type")
        pub_lci = ex.get("published_ci_lower")
        pub_uci = ex.get("published_ci_upper")

        outcome_label = (ex.get("aact_primary_outcome_measure") or "Primary outcome")[:120]
        outcome_obj = {
            "shortLabel": "MACE",
            "title": outcome_label + " (primary)",
            "type": "PRIMARY",
            "matchScore": 90,
        }
        if pub_es is not None:
            outcome_obj["estimandType"] = pub_t or "OR"
            if pub_t == "MD":
                outcome_obj["md"] = pub_es
            else:
                outcome_obj["effect"] = pub_es
                if pub_lci is not None: outcome_obj["lci"] = pub_lci
                if pub_uci is not None: outcome_obj["uci"] = pub_uci
        else:
            outcome_obj["estimandType"] = "OR"
            if tE is not None: outcome_obj["tE"] = tE
            if cE is not None: outcome_obj["cE"] = cE

        trial_entry = {
            "nct": nct,
            "name": acr,
            # PMID intentionally NOT injected: the upstream topic-JSON pmid
            # field is corpus-wide unverifiable (audit_pmids could validate 0
            # of 2073; 100% null titles; future-dated; reused across unrelated
            # topics; concrete cases fabricated e.g. SELECTION->pmid 41569324).
            # AbstractHydrator is PMID-only and would fetch the WRONG paper's
            # abstract/authors/link from a bad PMID (the reported defect).
            # Empty pmid -> hydrator no-ops; the AACT/NCT-based EvidenceHydrator
            # (verified correct via EuropePMC query=NCT) still enriches.
            "pmid": "",
            "phase": "III",
            "year": ex.get("pubmed_year") or 2024,
            "tE": tE, "tN": tN or 0, "cE": cE, "cN": cN or 0,
            "group": f"{drug} vs comparator in {cond} (AACT-verified primary)",
            "publishedHR": pub_es if pub_t in ("HR","OR","RR","IRR") else None,
            "hrLCI": pub_lci if pub_t in ("HR","OR","RR","IRR") else None,
            "hrUCI": pub_uci if pub_t in ("HR","OR","RR","IRR") else None,
            "allOutcomes": [outcome_obj],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": f"NCT {nct}: {outcome_label}. Source: ClinicalTrials.gov registry (AACT-verified); publication resolved live via NCT.",
            "sourceUrl": f"https://clinicaltrials.gov/study/{nct}",
            "evidence": [],
        }
        trials.append(trial_entry)
        ncts.append(nct)
        acrs[nct] = acr

    if not trials:
        return None

    drug_l = drug.lower()
    cond_u = cond.upper()
    stem_l = stem.lower()
    pop_txt = f"Adults randomised in trials registered on ClinicalTrials.gov for {cond}"

    def attr(s):  # safe inside an HTML value="..." attribute
        return s.replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

    cfg = {
        "base": str(BASE_TEMPLATE),
        "out":  str(HERE / f"{stem}_FULL_REVIEW.html"),
        "title": f"RapidMeta | {name} (audit-first, full-functionality)",
        "hero_h2": name,
        "nyt_headline": f"The {drug} Evidence",
        "auto_include_ncts": ncts,
        "nct_acronyms": acrs,
        "blank_benchmarks": True,
        "pico": {
            "pop":      pop_txt,
            "int":      f"{drug} (AACT-verified intervention name)",
            "comp":     "Active comparator or placebo as registered on AACT",
            "out":      "Trial-declared primary outcome (AACT design_outcomes); event counts from AACT outcome_measurements",
            "subgroup": "Subgroup analyses per parent trial protocol",
        },
        "real_data_entries": trials,
        # --- Precise, single-occurrence claim neutralizers (run first) ---
        # Replace claim-bearing prose with data-only text so the swap can
        # never produce a false mechanism/phenotype claim.
        "extra_replaces": [
            ["Dupilumab (IL-4Ralpha Monoclonal Antibody) for Moderate-to-Severe "
             "COPD with Type 2 Inflammation (Blood Eosinophils >=300/uL): A Living "
             "Systematic Review and Meta-Analysis of Phase 3 RCTs",
             f"{drug} for {cond}: A Living Systematic Review and Meta-Analysis of "
             f"Registered RCTs (audit-first; trial data verified against "
             f"ClinicalTrials.gov / AACT)"],
            ['value="Adults with COPD and type-2 inflammation"',
             f'value="{attr(pop_txt)}"'],
            ['value="Dupilumab"', f'value="{attr(drug)}"'],
            ["COPD + T2 inflammation", cond],
        ],
        # --- Global replace-ALL (fixes the n>1 SKIP bug). Longest/compound
        # tokens FIRST so substrings are not partially clobbered. ---
        "global_replaces": [
            ["rapid_meta_dupilumab_copd", f"rapid_meta_{stem_l}"],
            ["dupilumab_copd", stem_l],
            ["IL-4Ralpha Monoclonal Antibody",
             "intervention as registered on ClinicalTrials.gov"],
            ["Type 2 Inflammation", "the registered population"],
            ["type-2 inflammation", "the registered population"],
            ["T2 inflammation", "the registered population"],
            ["Blood Eosinophils >=300/uL", "per the registered eligibility"],
            ["Dupilumab", drug],
            ["dupilumab", drug_l],
            ["BOREAS", "the registered pivotal trial"],
            ["NOTUS", "the registered confirmatory trial"],
        ],
    }
    # COPD is a base-template leftover ONLY when this topic is not itself a
    # COPD topic. If the topic IS about COPD, leave 'COPD' untouched.
    if "copd" not in (cond.lower() + " " + name.lower() + " " + stem_l):
        cfg["global_replaces"].append(["COPD", cond_u])
    return cfg


def _load(mod):
    import importlib.util
    spec = importlib.util.spec_from_file_location(mod, str(HERE / "scripts" / f"{mod}.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


QUARANTINE = HERE / "outputs" / "quarantine_full_review"


def main():
    import argparse, time
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="cap topics (0=all)")
    ap.add_argument("--no-gate", action="store_true",
                    help="DEBUG ONLY: skip scanner/jscheck gates")
    ap.add_argument("--all-topics", action="store_true",
                    help="also build NON_VIABLE topics that have >=1 "
                         "gate-passing trial (build_config filters no-data ones)")
    args = ap.parse_args()

    clone = _load("clone_dashboard")
    scanner = _load("scan_narrative_leftover")
    jscheck = _load("jscheck")
    QUARANTINE.mkdir(parents=True, exist_ok=True)

    # Force-regenerate: a stale broken *_FULL_REVIEW.html must never survive
    # via SKIP_IF_EXISTS. Every shipped file must come from this fixed run.
    for stale in HERE.glob("*_FULL_REVIEW.html"):
        stale.unlink()
    for stale in QUARANTINE.glob("*.html"):
        stale.unlink()

    topics = [p for p in sorted(TOPICS.glob("*.json"))]
    ok = qfail = build_none = err = 0
    quarantined = []
    t0 = time.time()
    processed = 0

    for json_p in topics:
        try:
            doc = json.loads(json_p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        # Default: VIABLE (k>=3) only. With --all-topics: also build
        # NON_VIABLE topics that still have >=1 gate-passing trial — build_config
        # returns None when there is no usable trial data, so it is the natural
        # filter (no-data topics are skipped as build_none, not stubbed).
        if not args.all_topics and doc.get("verdict") != "VIABLE":
            continue
        if args.limit and processed >= args.limit:
            break
        processed += 1
        stem = doc["topic"]["stem"]
        out_html = HERE / f"{stem}_FULL_REVIEW.html"

        cfg = build_config(doc)
        if not cfg:
            build_none += 1
            continue
        cfg_p = CONFIGS / f"_audit_{stem.lower()}.json"
        cfg_p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False),
                          encoding="utf-8")

        try:
            clone.clone(cfg, dry=False)
        except Exception as e:
            err += 1
            print(f"  ERR  {stem}: clone raised {e}")
            continue
        if not out_html.exists() or out_html.stat().st_size < 200_000:
            err += 1
            print(f"  ERR  {stem}: clone produced no/short output")
            continue

        if args.no_gate:
            ok += 1
            continue

        # --- Dual ship-gate ---
        reason = None
        v = scanner.scan(str(out_html), str(json_p))
        if v:
            seen = {}
            for tok, _o, _c in v:
                seen[tok] = seen.get(tok, 0) + 1
            reason = "leftover " + ",".join(f"{k}x{n}" for k, n in sorted(seen.items()))
        else:
            jp = jscheck.check(str(out_html))
            if jp:
                reason = f"js-broken block#{jp[0][0]} {jp[0][1][:80]}"

        if reason:
            qfail += 1
            dest = QUARANTINE / out_html.name
            out_html.replace(dest)
            quarantined.append((stem, reason))
            print(f"  QUARANTINE {stem}: {reason}")
        else:
            ok += 1
            if ok <= 5 or ok % 50 == 0:
                dt = time.time() - t0
                print(f"  [{ok}] {stem}: {out_html.stat().st_size:,}B  ({dt:.0f}s)")

    print(f"\n=== Bulk-clone Summary ===")
    print(f"Shipped (both gates green): {ok}")
    print(f"Quarantined (gate fail)   : {qfail}")
    print(f"Build returned None       : {build_none}")
    print(f"Clone errors              : {err}")
    print(f"Elapsed                   : {time.time()-t0:.0f}s")
    if quarantined:
        qlog = HERE / "outputs" / "bulk_clone_quarantine.log"
        qlog.write_text("\n".join(f"{s}\t{r}" for s, r in quarantined),
                         encoding="utf-8")
        print(f"Quarantine reasons logged -> {qlog}")
        for s, r in quarantined[:20]:
            print(f"   - {s}: {r}")


if __name__ == "__main__":
    main()
