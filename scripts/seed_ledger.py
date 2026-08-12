"""Seed the no-regression ledger for every app, before anything is regenerated.

An app cannot adopt the prototype until its verified state is in the ledger, or
the first rebuild has nothing to protect it. The corpus is about to receive
identity fixes, atlas corrections and eventually a shell regeneration, and every
one of those is a rebuild -- so seeding is ordering-critical, not tidy.

Two kinds of app, both seeded:
  SSOT  -- state read from the canonical object (scripts/regression_guard.state_of)
  AUTO  -- state read from the `realData` blob embedded in the page, which is
           where an AUTO app's verified cells actually live

Coverage is reported as a fraction, and apps that yield no extractable state are
named rather than counted as covered. An app silently missing from the ledger is
an app the guard cannot protect, which is the failure this exists to prevent.
"""
import io, os, re, sys, json, glob, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location(
    "rg", os.path.join(ROOT, "scripts", "regression_guard.py"))
rg = importlib.util.module_from_spec(spec)
sys.modules["rg"] = rg
spec.loader.exec_module(rg)

NUM = re.compile(r"-?\d+(?:\.\d+)?")


def auto_state(path):
    """Verified cells of an AUTO page, from its embedded realData.

    Deliberately conservative: only fields that carry a study quantity count as
    cells. Prose and layout are not protected by this guard -- the prose guard
    covers those -- and counting them would make every cosmetic edit a regression.
    """
    app = os.path.basename(path).replace(".html", "")
    try:
        s = open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return None
    i = s.find("realData:{")
    if i < 0:
        i = s.find("realData: {")
    if i < 0:
        return None
    # brace-match the object literal
    j = s.index("{", i)
    depth, k = 0, j
    while k < len(s):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    blob = s[j:k + 1]
    cells, trials = set(), set()
    for m in re.finditer(r'"?(NULLED:)?(NCT\d{8})"?\s*:\s*\{', blob):
        nct = m.group(2)
        nulled = bool(m.group(1))
        trials.add("%s::trial::%s%s" % (app, nct, "::NULLED" if nulled else ""))
        seg = blob[m.end():m.end() + 1400]
        for f in ("tE", "cE", "tN", "cN", "publishedHR", "hrLCI", "hrUCI",
                  "pmid", "year"):
            mm = re.search(r'\b%s\s*:\s*("?[^,}"]+"?)' % f, seg)
            if mm and mm.group(1).strip() not in ("null", '""'):
                cells.add("%s::cell::%s::%s" % (app, nct, f))
    if not trials:
        return None
    return {"app": app, "cells": cells, "trials": trials,
            "citations": set(), "screened": set(), "k": {}}


led = rg.load_ledger()
ssot_ok, auto_ok, skipped = [], [], []

for j in sorted(glob.glob(os.path.join(ROOT, "ssot", "*", "*.json"))):
    try:
        obj = json.load(open(j, encoding="utf-8"))
    except Exception:
        continue
    if "results" not in obj or "inputs" not in obj:
        continue
    st = rg.state_of(obj)
    led = rg.update_ledger(led, st)
    ssot_ok.append((st["app"], len(st["cells"]), len(st["trials"])))

pages = sorted(glob.glob(os.path.join(ROOT, "*_REVIEW.html")))
for p in pages:
    st = auto_state(p)
    if st is None:
        skipped.append(os.path.basename(p))
        continue
    led = rg.update_ledger(led, st)
    auto_ok.append((st["app"], len(st["cells"]), len(st["trials"])))

os.makedirs(os.path.dirname(rg.LEDGER), exist_ok=True)
json.dump(led, open(rg.LEDGER, "w", encoding="utf-8"), indent=1)

tot_apps = len(ssot_ok) + len(auto_ok)
cells = sum(len(v["cells"]) for v in led["apps"].values())
trials = sum(len(v["trials"]) for v in led["apps"].values())
print("SSOT objects seeded : %d" % len(ssot_ok))
print("AUTO pages seeded   : %d of %d root pages" % (len(auto_ok), len(pages)))
print("no extractable state: %d (named below, NOT counted as covered)" % len(skipped))
print()
print("LEDGER COVERAGE     : %d apps | %s verified cells | %s trial keys"
      % (tot_apps, f"{cells:,}", f"{trials:,}"))
print("coverage fraction   : %d/%d = %.1f%% of root pages, plus %d SSOT objects"
      % (len(auto_ok), len(pages), 100.0 * len(auto_ok) / max(1, len(pages)),
         len(ssot_ok)))
print()
print("first 8 not seeded  :", skipped[:8])
