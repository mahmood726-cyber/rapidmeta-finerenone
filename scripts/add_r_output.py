import io, sys, json, re, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
P = r"F:\rapidmeta-ssot-shell\ssot\arni-hfref\arni-hfref.json"
d = json.load(open(P, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
r_out = json.load(open(r"F:\claude-temp\arni\r_out.json", encoding="utf-8"))
res = d["results"]["by_outcome"]["cvdeath_or_hfh_first"]

# --- the gate: the quoted text must agree with the projected numbers ----------
# A quotation that disagrees with the number printed beside it is worse than no
# quotation, because it looks like provenance. So the agreement is CHECKED at the
# point the quotation is stored, and refuses to write if it fails.
prim = r_out["primary_pooled"]["output"]
k_q = int(re.search(r"\(k = (\d+)", prim).group(1))
i2_q = float(re.search(r"I\^2 .*?:\s+([\d.]+)%", prim).group(1))
q_q = float(re.search(r"Q\(df = \d+\) = ([\d.]+)", prim).group(1))
est_q, lo_q, hi_q = (float(x) for x in re.search(
    r"^\s*(-?[\d.]+)\s+[\d.]+\s+-?[\d.]+\s+[\d.]+\s+(-?[\d.]+)\s+(-?[\d.]+)",
    prim, re.M).groups())

import math
k_o = res.get("k") or len(res.get("per_trial") or [])
checks = [
    ("k", k_q, k_o, 0),
    ("I2", i2_q, res["heterogeneity"]["i2"], 0.01),
    ("Q", q_q, res["heterogeneity"]["q"], 0.001),
    ("pooled point", math.exp(est_q), res["pooled"]["point"], 5e-4),
    ("ci_low", math.exp(lo_q), res["pooled"]["ci_low"], 5e-4),
    ("ci_high", math.exp(hi_q), res["pooled"]["ci_high"], 5e-4),
]
bad = []
print("AGREEMENT: quoted R output against the projected object values")
for name, quoted, projected, tol in checks:
    ok = abs(float(quoted) - float(projected)) <= tol
    bad += [] if ok else [name]
    print("  %-13s quoted=%-12s projected=%-12s %s"
          % (name, round(float(quoted), 6), round(float(projected), 6),
             "OK" if ok else "MISMATCH"))
if bad:
    raise SystemExit("REFUSED: quoted R output disagrees with the object on %s"
                     % ", ".join(bad))

res["r_output"] = collections.OrderedDict(
    _why="Every result below carries the VERBATIM printed output of the call that "
         "produced it, captured with capture.output() rather than re-typed. A bare "
         "number can only be checked against the object that produced it, and the "
         "object is ours; a quoted metafor call carries its own k, its own "
         "estimator, its own heterogeneity and its own package version, so a "
         "reader can audit the provenance without trusting us. It would have made "
         "this project's worst defect visible on sight: a printed k = 4 sitting "
         "under a leave-one-out panel drawn from three studies is obvious, where a "
         "bare 0.839 is not.",
    _agreement_checked="The quoted output is parsed and compared against the "
         "projected values at the moment it is stored -- k, I-squared, Q and the "
         "back-transformed estimate with its interval. A quotation that disagrees "
         "with the number printed beside it is worse than no quotation, because it "
         "looks like provenance. The write refuses if they disagree.",
    _environment=r_out["primary_pooled"]["environment"],
    blocks=collections.OrderedDict(
        (k, collections.OrderedDict(label=v["label"], call=v["call"],
                                    output=v["output"]))
        for k, v in r_out.items()),
)
json.dump(d, open(P, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\nstored %d verbatim R blocks; agreement verified on 6 quantities"
      % len(r_out))
