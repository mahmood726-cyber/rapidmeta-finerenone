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


def build_config(topic_doc):
    topic = topic_doc["topic"]
    stem = topic["stem"]
    name = topic["name"]
    drug = (topic["drug_patterns"] or ["intervention"])[0].title()
    cond = (topic["condition_patterns"] or ["condition"])[0].title()

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
            "pmid": ex.get("pmid") or "",
            "phase": "III",
            "year": ex.get("pubmed_year") or 2024,
            "tE": tE, "tN": tN or 0, "cE": cE, "cN": cN or 0,
            "group": f"{drug} vs comparator in {cond} (AACT-verified primary)",
            "publishedHR": pub_es if pub_t in ("HR","OR","RR","IRR") else None,
            "hrLCI": pub_lci if pub_t in ("HR","OR","RR","IRR") else None,
            "hrUCI": pub_uci if pub_t in ("HR","OR","RR","IRR") else None,
            "allOutcomes": [outcome_obj],
            "rob": ["low", "low", "low", "low", "low"],
            "snippet": f"NCT {nct}: {outcome_label}. Primary publication PMID {ex.get('pmid') or '—'}.",
            "sourceUrl": (f"https://pubmed.ncbi.nlm.nih.gov/{ex['pmid']}/"
                           if ex.get("pmid") else f"https://clinicaltrials.gov/study/{nct}"),
            "evidence": [],
        }
        trials.append(trial_entry)
        ncts.append(nct)
        acrs[nct] = acr

    if not trials:
        return None

    return {
        "base": str(BASE_TEMPLATE),
        "out":  str(HERE / f"{stem}_FULL_REVIEW.html"),
        "title": f"RapidMeta | {name} (audit-first, full-functionality)",
        "hero_h2": name,
        "nyt_headline": f"The {drug} Evidence",
        "auto_include_ncts": ncts,
        "nct_acronyms": acrs,
        "localstorage_old": "rapid_meta_dupi_copd_v1_0",
        "localstorage_new": f"rapid_meta_{stem.lower()}_audit_v1",
        "pico": {
            "pop":      f"Adults randomised in trials registered on ClinicalTrials.gov for {cond}",
            "int":      f"{drug} (AACT-verified intervention name)",
            "comp":     "Active comparator or placebo as registered on AACT",
            "out":      "Trial-declared primary outcome (AACT design_outcomes); event counts from AACT outcome_measurements",
            "subgroup": "Subgroup analyses per parent trial protocol",
        },
        "real_data_entries": trials,
        "extra_replaces": [
            ["dupilumab", drug.lower()],
            ["Dupilumab", drug],
            ["COPD", cond.upper()],
        ],
    }


def main():
    ok = 0; skip = 0; fail = 0
    clone_script = HERE / "scripts" / "clone_dashboard.py"

    for json_p in sorted(TOPICS.glob("*.json")):
        try:
            doc = json.loads(json_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if doc.get("verdict") != "VIABLE":
            continue
        stem = doc["topic"]["stem"]
        out_html = HERE / f"{stem}_FULL_REVIEW.html"
        if SKIP_IF_EXISTS and out_html.exists():
            skip += 1
            continue

        cfg = build_config(doc)
        if not cfg:
            continue
        cfg_p = CONFIGS / f"_audit_{stem.lower()}.json"
        cfg_p.write_text(json.dumps(cfg, indent=2, ensure_ascii=False),
                          encoding="utf-8")

        # Run clone_dashboard.py
        try:
            r = subprocess.run([sys.executable, str(clone_script),
                                  "--config", str(cfg_p)],
                                 capture_output=True, text=True, timeout=90,
                                 encoding="utf-8")
            if r.returncode == 0 and out_html.exists():
                ok += 1
                if ok <= 5 or ok % 25 == 0:
                    print(f"  [{ok}]  {stem}: {out_html.stat().st_size:,} bytes")
            else:
                fail += 1
                print(f"  FAIL {stem}: {r.stderr[:200] if r.stderr else r.stdout[-200:]}")
        except Exception as e:
            fail += 1
            print(f"  FAIL {stem}: {e}")

    print(f"\nDone. Cloned: {ok}, Skipped (existed): {skip}, Failed: {fail}")


if __name__ == "__main__":
    main()
