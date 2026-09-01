# -*- coding: utf-8 -*-
"""Apply the FROZEN rule to the infectious-disease topics. Does the lane carry over?

⛔ NOT ONE LINE OF THE RULE CHANGES. `rekey_rule` is imported and used exactly as
`build_pool.py` uses it for cardiology -- same split, same ChEMBL resolution, same F0-F6
failure states, same `class_terms_for_drug`. If it behaves badly on this specialty that is a
FINDING and it ships as one.

⭐ WHY A SEPARATE FILE RATHER THAN A FLAG ON build_pool.py. `build_pool.py` produced the
twenty and `pool.json` that everything downstream is keyed to; adding a specialty parameter
would make one script the source of two populations and invite exactly the frozen-vs-live
drift that once let an amendment reach the controls and not the twenty. This reuses the
rule and owns its own output.

⚠️ THE QUESTION IS NOT "how many pass" BUT "WHERE DOES IT LOSE THEM". A lower pass rate
caused by worse TITLES is a finding about the objects; one caused by the rule mishandling
antimicrobials is a finding about the rule. Only the per-state breakdown separates them, so
every failure state is counted and every topic is named under one.
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from rekey_rule import (split_title, condition_terms, STOP,             # noqa: E402
                        class_terms_for_drug, rule_fingerprint)
import chembl_resolve as CR                                             # noqa: E402

ROOT = "F:/rapidmeta-ssot-shell"
SPECIALTY = "infectious-disease"
BASE = "../../evidence/2026-08-31-rekey/corrected/pool.json"
OUT = "../../evidence/2026-08-31-axis/id_pool.json"


def main():
    # THE POPULATION, PARTITIONED INTO NAMED KINDS BEFORE ANY COUNT.
    dirs = sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "")))
    has_object, absent = [], []
    for d in dirs:
        n = os.path.basename(os.path.normpath(d))
        f = os.path.join(d, n + ".json")
        (has_object if os.path.exists(f) else absent).append((n, f) if os.path.exists(f) else n)
    if len(has_object) + len(absent) != len(dirs):
        raise SystemExit("partition loses items")

    cache = CR._cache()
    topics = []
    for name, f in has_object:
        o = json.load(io.open(f, encoding="utf-8"))
        sp = o.get("specialty")
        sp = sp.get("value") if isinstance(sp, dict) else sp
        if sp != SPECIALTY:
            continue
        title = str(o.get("title") or "").strip()
        rec = {"app_id": name, "title": title, "fail": [], "drugs": [], "class_phrases": []}
        if title == "":
            rec["fail"].append("F0_NO_TITLE")
            topics.append(rec)
            continue
        inter, cond = split_title(title)
        rec["intervention_span"], rec["condition_span"] = inter, cond
        if cond is None:
            rec["fail"].append("F1_NO_CONDITION")
        rec["condition_terms"] = condition_terms(cond) if cond else []
        toks = [t for t in re.split(r"[^A-Za-z]+", inter)
                if len(t) > 3 and t.lower() not in STOP]
        hits = {}
        for t in toks:
            r = CR.resolve(t, cache=cache, save=False)
            if r and not r.get("error"):
                hits[r["pref_name"]] = r
        CR._save(cache)
        rec["tokens_queried"] = toks
        rec["drugs"] = sorted(hits)
        if len(hits) == 0:
            rec["fail"].append("F2_NO_DRUG")
        elif len(hits) > 1:
            rec["fail"].append("F3_MULTI_DRUG")
        else:
            drug = list(hits.values())[0]
            rec["drug"] = drug
            ph, cfail = class_terms_for_drug(drug)
            if cfail:
                rec["fail"].append(cfail)
            else:
                rec["class_phrases"] = ph
        topics.append(rec)

    base = json.load(io.open(BASE, encoding="utf-8"))
    bc = Counter(t["fail"][0] if t.get("fail") else "DRUG_KEYED_AND_REKEYABLE"
                 for t in base["topics"])
    nb = len(base["topics"])
    c = Counter(t["fail"][0] if t["fail"] else "DRUG_KEYED_AND_REKEYABLE" for t in topics)
    n = len(topics)

    print("=== REF ===")
    print("   rule fingerprint  %s   FROZEN -- identical to the cardiology run"
          % rule_fingerprint()[:16])
    print("   specialty         %s" % SPECIALTY)
    print("   topics            %d   (cardiology baseline: %d)" % (n, nb))
    print("")
    print("=== WHERE THE RULE LOSES THEM -- cardiology vs infectious disease ===")
    print("   %-28s %13s %13s" % ("state", "cardiology", "infectious"))
    for k in sorted(set(bc) | set(c), key=lambda x: -(c.get(x, 0))):
        print("   %-28s %5d %4.0f%%   %5d %4.0f%%"
              % (k, bc.get(k, 0), 100.0 * bc.get(k, 0) / nb,
                 c.get(k, 0), 100.0 * c.get(k, 0) / n))
    print("   %-28s %5d          %5d" % ("TOTAL", nb, n))
    ok = c.get("DRUG_KEYED_AND_REKEYABLE", 0)
    print("")
    print("   carried end-to-end: %d of %d = %.0f%%   (cardiology %d of %d = %.0f%%)"
          % (ok, n, 100.0 * ok / n, bc.get("DRUG_KEYED_AND_REKEYABLE", 0), nb,
             100.0 * bc.get("DRUG_KEYED_AND_REKEYABLE", 0) / nb))

    print("")
    print("=== ⭐ IS IT THE RULE OR THE TITLES? ===")
    title_side = sum(c.get(k, 0) for k in ("F0_NO_TITLE", "F1_NO_CONDITION"))
    rule_side = sum(c.get(k, 0) for k in ("F2_NO_DRUG", "F3_MULTI_DRUG", "F4_NO_CLASS",
                                          "F5_MODALITY_CLASS", "F6_CIRCULAR_CLASS"))
    bt = sum(bc.get(k, 0) for k in ("F0_NO_TITLE", "F1_NO_CONDITION"))
    br = sum(bc.get(k, 0) for k in ("F2_NO_DRUG", "F3_MULTI_DRUG", "F4_NO_CLASS",
                                    "F5_MODALITY_CLASS", "F6_CIRCULAR_CLASS"))
    print("   lost to the TITLE  (F0+F1) : ID %2d (%.0f%%)   cardiology %2d (%.0f%%)"
          % (title_side, 100.0 * title_side / n, bt, 100.0 * bt / nb))
    print("   lost to the DRUG/CLASS step: ID %2d (%.0f%%)   cardiology %2d (%.0f%%)"
          % (rule_side, 100.0 * rule_side / n, br, 100.0 * br / nb))
    print("   ⇒ a loss on the TITLE side is a finding about the OBJECTS;")
    print("     a loss on the DRUG/CLASS side is a finding about the RULE.")

    print("")
    print("=== VACCINES -- the case the rule was never designed for ===")
    vac = [t for t in topics
           if re.search(r"(?i)vaccin|prevnar|menacwy|men acwy|acyw|recombinant", t["title"])]
    print("   vaccine-shaped topics: %d" % len(vac))
    for t in vac:
        print("      %-46s %-20s drugs=%s"
              % (t["app_id"], t["fail"][0] if t["fail"] else "REKEYED", t["drugs"] or "-"))
    print("   ⚠️ a vaccine is not a molecule with a USAN stem. F2_NO_DRUG is the CORRECT")
    print("     outcome; a vaccine that RESOLVES to some molecule is the identity defect.")

    print("")
    print("=== EVERY TOPIC, NAMED UNDER ONE STATE ===")
    for t in sorted(topics, key=lambda x: (x["fail"][0] if x["fail"] else "", x["app_id"])):
        print("   %-46s %-24s %s"
              % (t["app_id"], t["fail"][0] if t["fail"] else "DRUG_KEYED_AND_REKEYABLE",
                 ", ".join(t["drugs"])[:40]))

    json.dump({"rule_fingerprint": rule_fingerprint(), "specialty": SPECIALTY,
               "topics": topics}, io.open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("")
    print("   written: %s" % OUT)


if __name__ == "__main__":
    main()
