# -*- coding: utf-8 -*-
"""Refit the artefacts feeding the five pages rebuilt right now.

The I2/tau2 contradiction sweep flags nothing on these five -- but NOT FLAGGED IS
NOT CLEAN. That check only fires when I2 > 0. An artefact storing tau2 = 0 BESIDE
I2 = 0 is internally consistent and therefore invisible to it, while still being a
stale zero: REML can return a positive tau2 where Q <= df leaves I2 at zero.

So these are refitted with the SHIPPED estimator and, where inputs allow, against
metafor. A rebuild re-publishes whatever the artefact holds, so a stale zero here
becomes a freshly published wrong number.
"""
import importlib.util
import io
import json
import os

R = r"F:\rapidmeta-ssot-shell\outputs\r_validation"
SRC = r"F:\rapidmeta-ssot-shell\scripts\build_binary_sidecar.py"
TARGETS = ("APIXABAN_VTE_AUTO_FULL.json", "AZILSARTAN_HTN_AUTO_FULL.json",
           "ARNI_HF.json", "APIXABAN_ACS_AUTO_FULL.json",
           "APIXABAN_AF_AUTO_FULL.json", "BOCOCIZUMAB_LIPID_AUTO_FULL.json")

spec = importlib.util.spec_from_file_location("bs", SRC)
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)

rows, forR = [], []
for fn in TARGETS:
    p = os.path.join(R, fn)
    if not os.path.exists(p):
        rows.append((fn, "FILE_ABSENT", None, None, None))
        continue
    d = json.load(io.open(p, encoding="utf-8"))
    tr = d.get("trials") or []
    yi = [t.get("yi") for t in tr if isinstance(t, dict)]
    vi = [t.get("vi") for t in tr if isinstance(t, dict)]
    stored = d.get("tau2")
    if not yi or len(yi) < 2 or any(v is None for v in yi + vi):
        rows.append((fn, "UNCHECKABLE_NO_STORED_ROWS", stored, None, d.get("generated_on")))
        continue
    now = bs.reml_tau2(yi, vi)
    st = float(stored) if isinstance(stored, (int, float)) else None
    state = ("STALE" if st is not None and abs(now - st) > 1e-6 else "agrees")
    rows.append((fn, state, stored, now, d.get("generated_on")))
    forR.append({"file": fn, "yi": yi, "vi": vi})

print("%-40s %-26s %-14s %-14s %s"
      % ("artefact", "verdict", "stored tau2", "shipped now", "generated_on"))
for fn, state, stored, now, gen in rows:
    print("%-40s %-26s %-14s %-14s %s"
          % (fn[:40], state, stored, ("%.7f" % now) if now is not None else "-", gen))

json.dump(forR, io.open("rebuild_inputs.json", "w", encoding="utf-8"), indent=1)
print()
print("wrote rebuild_inputs.json for the metafor cross-check (%d artefacts)" % len(forR))
