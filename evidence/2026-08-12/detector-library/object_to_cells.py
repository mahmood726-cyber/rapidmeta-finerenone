"""Feed SSOT canonical objects into the sibling lane's count harness.

D9 (composite-by-summation), D10 (denominator-is-randomised) and D11 (unverified
prior-meta tier) are already implemented there as CHK007 / CHK002 / CHK011, and
better than my sketch -- CHK002 fails closed when EITHER denominator is missing,
which my version would not have. So this adapts rather than reimplements.
"""
import io, os, sys, json, glob, importlib.util
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

H = (r"C:\Users\mahmo\AppData\Roaming\Claude\local-agent-mode-sessions"
     r"\bdc5772c-ca03-473f-9464-80d37a7559d2\44788c9b-d162-4f2e-b3c2-d89031e65ab6"
     r"\local_95f555f3-c719-446f-9f1a-d5253bed5c4e\outputs\rapidmeta_count_harness.py")
spec = importlib.util.spec_from_file_location("harness", H)
hz = importlib.util.module_from_spec(spec)
sys.modules["harness"] = hz   # dataclass resolves __module__ via sys.modules
spec.loader.exec_module(hz)

SS = r"F:\rapidmeta-ssot-shell\ssot"
TIER_MAP = {"T1": "T1", "T2": "T2", "T1+T2": "T1", "T3": "T3", "T4": "T4"}


def cells_for(d):
    out = []
    for t in d["inputs"]["trials"]:
        for oid, b in (t.get("by_outcome") or {}).items():
            for role in ("treatment", "control"):
                c = b.get(role)
                if not isinstance(c, dict) or c.get("events") is None:
                    continue
                tier = str(c.get("source_tier", "")).upper()
                srcs = []
                for tk in ("T1", "T2", "T3", "T4"):
                    if tk in tier:
                        srcs.append({"tier": tk,
                                     "pointer": c.get("source_pointer", ""),
                                     "flagged_unverified": tk == "T4"})
                out.append(hz.Cell(
                    trial=t.get("name") or t["id"], nct=t.get("nct", ""),
                    arm=role, outcome=oid, events=c["events"], analysed=c.get("n"),
                    randomised=c.get("randomised"),
                    population_label=c.get("denominator_is") or "unstated",
                    denominator_reason=(b.get("denominator_note") or "")[:200] or None,
                    provenance=c.get("read_or_derived", "read"),
                    sources=srcs or [{"tier": "T2", "pointer": "unstated"}],
                    identifier_provenance="lookup" if t.get("nct") else None))
            # component endpoints, so CHK007 can test the composite
            for r in ((t.get("component_endpoints") or {}).get("rows") or []):
                tier = str(r.get("source_tier", "")).upper()
                srcs = [{"tier": tk, "pointer": r.get("source_pointer", ""),
                         "flagged_unverified": tk == "T4"}
                        for tk in ("T1", "T2", "T3", "T4") if tk in tier]
                comp = ("first heart-failure hosp" in r["endpoint"].lower()
                        or "cardiovascular death" in r["endpoint"].lower())
                for role, ev, n in (("treatment", r["treatment_events"], r["treatment_n"]),
                                    ("control", r["control_events"], r["control_n"])):
                    out.append(hz.Cell(
                        trial=t.get("name") or t["id"], nct=t.get("nct", ""),
                        arm=role, outcome=r["endpoint"], events=ev, analysed=n,
                        randomised=n, population_label=c.get("denominator_is") or "unstated",
                        provenance=r.get("read_or_derived", "read"),
                        sources=srcs or [{"tier": "T2", "pointer": "unstated"}],
                        identifier_provenance="lookup" if t.get("nct") else None,
                        is_component_of=oid if comp else None))
    return out


rows = []
for j in sorted(glob.glob(os.path.join(SS, "*", "*.json"))):
    d = json.load(open(j, encoding="utf-8"))
    cs = cells_for(d)
    if not cs:
        rows.append((d["app_id"], 0, 0, 0, "no 2x2 cells"))
        continue
    fs = hz.run_checks(cs)
    s = hz.summarise(cs, fs)
    rows.append((d["app_id"], s["cells_total"], s["blocks"], s["warns"], s["verdict"]))
    for f in fs:
        if f.severity in ("BLOCK", "WARN"):
            print("  %-24s %s" % (d["app_id"], f.line()))

print("\n%-26s %6s %7s %6s  %s" % ("app", "cells", "BLOCK", "WARN", "verdict"))
for r in rows:
    print("%-26s %6d %7d %6d  %s" % r)
print("\nTOTAL cells %d | BLOCK %d | WARN %d"
      % (sum(r[1] for r in rows), sum(r[2] for r in rows), sum(r[3] for r in rows)))
