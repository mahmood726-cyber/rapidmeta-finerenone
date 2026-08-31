# -*- coding: utf-8 -*-
"""Apply the rule to every cardiology topic. Emits the pool + every failure state."""
import io, json, os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from rekey_rule import (split_title, condition_terms, class_phrases, STOP, norm,
                        class_terms_for_drug, rule_fingerprint)
import chembl_resolve as CR

ROOT = "F:/rapidmeta-ssot-shell"
# Instructed exclusions. Named, not silently dropped.
EXCLUDE = {"arni-hfref", "sacubitril-heartfail", "sacubitril-valsartan-hf"}
EXCLUDE_REASON = ("ARNI and the HFrEF NMA are excluded by instruction; sacubitril topics are "
                  "ARNI under another name")

cache = CR._cache()

# STATE THE POSITIVE PROPERTY, AND MAKE THE SKIP VISIBLE.
#
# This block used to read `if not os.path.exists(f): continue`, which silently dropped
# every ssot/ directory that holds no object of its own name. The count it then printed --
# "56 cardiology topics" -- was a REACH figure with the skip invisible inside it: a
# directory that vanished before it was counted cannot appear in any denominator derived
# from that number. Refused by scripts/audit_exclusion_by_absence.py --gate, correctly.
#
# The population is now partitioned into NAMED KINDS and the partition is asserted to
# lose nothing. A directory with no object is not a defect and is not a topic; it is a
# third kind of item, and it is reported by name rather than by absence.
candidate_dirs = sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "")))
has_object, absent_object = [], []
for d in candidate_dirs:
    name = os.path.basename(os.path.normpath(d))
    f = os.path.join(d, name + ".json")
    if os.path.exists(f):
        has_object.append((name, f))
    else:
        absent_object.append(name)

if len(has_object) + len(absent_object) != len(candidate_dirs):
    raise SystemExit(
        "%s\n  rule: the partition loses items -- %d dirs examined, %d with an object, "
        "%d named absent. A scan may not report a count whose parts do not sum to the "
        "population it walked\n  found by: scripts/rekey20/build_pool.py"
        % (os.path.join(ROOT, "ssot"), len(candidate_dirs), len(has_object), len(absent_object)))

topics = []
for name, f in has_object:
    o = json.load(io.open(f, encoding="utf-8"))
    sp = o.get("specialty")
    spv = sp.get("value") if isinstance(sp, dict) else sp
    if spv != "cardiology":
        continue
    title = str(o.get("title") or "").strip()
    rec = {"app_id": name, "title": title, "fail": [], "drugs": [], "class_phrases": []}
    if name in EXCLUDE:
        rec["fail"].append("EXCLUDED_BY_INSTRUCTION")
        topics.append(rec)
        continue
    # `title == ""` states the property; `not title` states its absence. F0 is a real kind
    # of topic -- one whose title was never authored -- not a hole in the scan.
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
        # R4 and its three refusals live in ONE function, shared with scan.py.
        ph, cfail = class_terms_for_drug(drug)
        if cfail:
            rec["fail"].append(cfail)
        else:
            rec["class_phrases"] = ph
    topics.append(rec)

json.dump({"rule_fingerprint": rule_fingerprint(), "topics": topics},
          io.open("pool.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

from collections import Counter
print("=== POPULATION, with its composition, before any topic count ===")
print("  ssot/ directories walked          : %d" % len(candidate_dirs))
print("    carrying an object of their name: %d" % len(has_object))
print("    NAMED ABSENT (no <name>.json)   : %d   %s"
      % (len(absent_object), ", ".join(absent_object) if absent_object else ""))
print("    partition sums to the walk      : %d + %d == %d  HOLDS"
      % (len(has_object), len(absent_object), len(candidate_dirs)))
print("  of the %d objects, cardiology     : %d" % (len(has_object), len(topics)))
print("")
print("=== KINDS IN THE POPULATION, named before any number ===")
c = Counter(t["fail"][0] if t["fail"] else "DRUG_KEYED_AND_REKEYABLE" for t in topics)
for k, v in c.most_common():
    print("  %-28s %d" % (k, v))
print("")
drugkeyed = [t for t in topics if "F2_NO_DRUG" not in t["fail"]
             and "F3_MULTI_DRUG" not in t["fail"]
             and "F0_NO_TITLE" not in t["fail"]
             and "EXCLUDED_BY_INSTRUCTION" not in t["fail"] and t["drugs"]]
print("DRUG-KEYED (exactly one drug in the intervention span): %d" % len(drugkeyed))
rekeyable = [t for t in drugkeyed if t["class_phrases"]]
print("  of which the rule yields a usable class : %d" % len(rekeyable))
print("  of which the rule FAILS to yield a class: %d" % (len(drugkeyed) - len(rekeyable)))
for t in drugkeyed:
    if not t["class_phrases"]:
        d = t.get("drug") or {}
        print("      %-46s %-18s %s" % (t["app_id"], t["fail"][0] if t["fail"] else "?",
                                        (d.get("usan_stem_definition") or "(no stem)")[:60]))
