"""My own verdicts, split by what they actually rest on. Two honesty checks."""
import collections
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rows = json.load(io.open("outputs/reject_charges_2026_08_24.json", encoding="utf-8"))

print("CHECK 1 -- CONFIRMED is doing two different jobs. Which?")
kinds = collections.Counter()
for r in rows:
    if r["verdict"] != "CONFIRMED":
        continue
    kinds["narrower scope phrase the notice drops"
          if r["evidence"].startswith("object holds a narrower form")
          else "object holds the guard, which is true of 68 objects regardless"] += 1
for k, n in kinds.most_common():
    print("   %-62s %3d" % (k, n))
print("   -> only the FIRST kind confirms THIS charge. The second confirms the")
print("      guard-not-projected finding again, which is already known and counted.")

print("")
print("CHECK 2 -- is NOT_IN_NOTICE a fact about the charge, or about my locator?")
notin = [r for r in rows if r["verdict"] == "NOT_IN_NOTICE"]
elsewhere = 0
nowhere = 0
for r in notin:
    topic = r["topic"]
    p = os.path.join("ssot", topic, topic + ".json")
    if not os.path.isfile(p):
        continue
    blob = re.sub(r"\s+", " ", io.open(p, encoding="utf-8", errors="replace").read()).lower()
    frag = re.sub(r"\s+", " ", r["charge"]).strip().lower()[:50]
    if frag and frag in blob:
        elsewhere += 1
    else:
        nowhere += 1
print("   NOT_IN_NOTICE charges                  %3d" % len(notin))
print("   ...whose text IS elsewhere in the object %3d   <- my locator, not the charge"
      % elsewhere)
print("   ...not found anywhere in the object      %3d   <- genuinely unlocatable" % nowhere)
print("")
print("   An empty probe is a statement about the probe until proven otherwise. Here it is")
print("   proven otherwise for many of them: the charges quote the OBJECT, and I searched only")
print("   the NOTICE.")
