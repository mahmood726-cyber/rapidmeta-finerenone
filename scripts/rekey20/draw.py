# -*- coding: utf-8 -*-
import io, json, os, random, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sys as _s; _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rekey_rule import rule_fingerprint, assert_fingerprint
_doc = json.load(io.open("pool.json", encoding="utf-8"))
assert_fingerprint(_doc.get("rule_fingerprint") if isinstance(_doc, dict) else None,
                   "pool.json", "rekey20/draw.py")
pool = _doc["topics"]
drug_keyed = [t for t in pool
              if t["drugs"] and "F2_NO_DRUG" not in t["fail"] and "F3_MULTI_DRUG" not in t["fail"]
              and "F0_NO_TITLE" not in t["fail"] and "EXCLUDED_BY_INSTRUCTION" not in t["fail"]]
ids = sorted(t["app_id"] for t in drug_keyed)
assert len(ids) == 32, len(ids)
chosen = set(random.Random(20260831).sample(ids, 20))
sel = [t for t in drug_keyed if t["app_id"] in chosen]
json.dump({"rule_fingerprint": rule_fingerprint(), "seed": 20260831, "topics": sel},
          io.open("twenty.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("pool 32 -> drawn 20 at seed 20260831")
print("")
print("%-48s %-18s %s" % ("app_id", "rule outcome", "class phrases (the re-key)"))
for t in sorted(sel, key=lambda x: x["app_id"]):
    f = t["fail"][0] if t["fail"] else "REKEYED"
    print("%-48s %-18s %s" % (t["app_id"], f, "; ".join(t["class_phrases"])[:70] or "-- none --"))
from collections import Counter
print("")
for k, v in Counter((t["fail"][0] if t["fail"] else "REKEYED") for t in sel).most_common():
    print("  %-20s %d" % (k, v))
