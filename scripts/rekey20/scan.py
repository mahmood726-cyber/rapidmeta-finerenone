# -*- coding: utf-8 -*-
"""THE SCAN. Three arms over one frame. Controls run FIRST and gate the counts.

  arm A   -- intervention terms = the DRUG only            (what the corpus is keyed by)
  arm B   -- intervention terms = the CLASS only           (the re-key, as a replacement)
  arm AuB -- intervention terms = drug + class             (the re-key, as operated)

Everything else is identical across arms: the same frame, the same condition terms, the
same matcher, the same verification. The ONLY difference is the intervention term set.

  CANDIDATE  row is a REVIEW, and (an intervention term appears in title+objectives)
             and (>=2 of the condition terms appear in title+objectives)
  VERIFIED   the same two limbs both hold inside `objectives_verbatim` ALONE -- a second
             field, so verification is not a re-run of retrieval on the same bytes
  UNVERIFIABLE  objectives_verbatim is null. null means UNOBTAINABLE from the source.
             These are reported as their own bucket and are NEVER scored either way.
"""
import io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from frame_contract import load_frame, FrameRefused, kinds
from rekey_rule import (norm, contains, split_title, condition_terms, class_phrases,
                        class_terms_for_drug, rule_fingerprint, assert_fingerprint)
import chembl_resolve as CR

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
FRAME = "F:/claude-temp/pend/cdsr_frame_cardiology.jsonl"

rows = load_frame(FRAME)
K = kinds(rows)
reviews = [r for r in rows if r["record_kind"] == "review"]
for r in reviews:
    r["_all"] = norm((r["title"] or "") + " " + (r["objectives_verbatim"] or ""))
    r["_obj"] = norm(r["objectives_verbatim"] or "") if r["objectives_verbatim"] else None


def match(row, terms, cond, field):
    hay = row["_all"] if field == "all" else row["_obj"]
    if hay is None:
        return None
    it = [t for t in terms if contains(hay, t)]
    ct = [c for c in cond if contains(hay, c)]
    need = min(2, len(cond)) if cond else 99
    if it and len(ct) >= need:
        return {"intervention_hits": it, "condition_hits": ct}
    return None


def scan(terms, cond):
    cand, ver, unver = [], [], []
    if not terms or not cond:
        return cand, ver, unver
    for r in reviews:
        m = match(r, terms, cond, "all")
        if not m:
            continue
        cand.append((r, m))
        if r["_obj"] is None:
            unver.append((r, m))
            continue
        mo = match(r, terms, cond, "obj")
        if mo:
            ver.append((r, mo))
    return cand, ver, unver


def arms(drug_terms, class_terms, cond):
    return {"A_drug": scan(drug_terms, cond),
            "B_class": scan(class_terms, cond),
            "AuB": scan(sorted(set(drug_terms) | set(class_terms)), cond)}


# ------------------------------------------------- ONE SOURCE FOR THE RULE
# The controls and the measured arm MUST derive their terms by the same path. They did
# not: the controls called class_phrases() live while the twenty read class_phrases
# frozen into twenty.json before Amendment 2, so the positive control certified a
# splitter the twenty never used. Both call sites now go through terms_for(), and
# nothing reads a frozen class term.
def terms_for(drug_record):
    """drug record -> (drug terms, class terms). THE ONLY PLACE EITHER IS COMPUTED.

    Class terms come from rekey_rule.class_terms_for_drug, which carries R4 AND its
    F4/F5/F6 refusals -- the same function build_pool.py uses. One source means the
    whole rule, not just the splitter.
    """
    name = (drug_record or {}).get("pref_name") or ""
    dt = [x for x in [norm(name).strip()] if x]
    ct, _fail = class_terms_for_drug(drug_record)
    return dt, ct


# ---------------------------------------------------------------- CONTROLS
def synth(title):
    inter, cond = split_title(title)
    tok = [w for w in inter.split() if len(w) > 3]
    d = CR.resolve(tok[0])
    dt, ct = terms_for(d)
    return dt, ct, condition_terms(cond)


CONTROLS = [
    # (name, synthetic title, kind, assertion)
    ("P1 must-match", "Atenolol in hypertension", "must_contain", "CD002003"),
    ("P2 must-match", "Ambrisentan in pulmonary arterial hypertension", "must_contain", "CD004434"),
    ("N1 must-not-match", "Ambrisentan in atrial fibrillation", "must_be_zero", None),
    ("N2 must-not-match", "Atenolol in pulmonary arterial hypertension", "must_be_zero", None),
]

print("=== FRAME, kinds named before any number ===")
for k, v in K.most_common():
    print("   %-10s %d" % (k, v))
print("   reviews scanned: %d   (protocols cannot be a counterpart and are not scanned)" % len(reviews))
print("")
print("=== CONTROLS -- both directions. If either fails, NO COUNT IS PRINTED. ===")
cfail = []
for name, title, kind, arg in CONTROLS:
    dt, ct, cond = synth(title)
    res = arms(dt, ct, cond)
    _, ver, _ = res["B_class"]
    bases = [r["cd_base"] for r, _ in ver]
    if kind == "must_contain":
        ok = arg in bases
        detail = "class arm verified %d rows; %s %s" % (len(bases), arg, "PRESENT" if ok else "ABSENT")
        # The instrument must also have FAILED on the drug arm, or the control does not
        # exercise the effect under test.
        _, vA, _ = res["A_drug"]
        detail += "; drug arm verified %d" % len(vA)
    else:
        ok = len(bases) == 0
        detail = "class arm verified %d rows %s" % (len(bases), bases[:4])
        # THE CONTROL'S OWN ARGUMENTS. A zero produced by a dead term is not a negative
        # result, it is a broken control. Each half must be live on its own.
        live_i = sum(1 for r in reviews if any(contains(r["_all"], t) for t in ct))
        live_c = sum(1 for r in reviews if sum(1 for c in cond if contains(r["_all"], c)) >= min(2, len(cond)))
        detail += "; term liveness: class matches %d rows alone, condition matches %d rows alone" % (live_i, live_c)
        if live_i == 0 or live_c == 0:
            ok = False
            detail += "  <-- DEAD TERM: this zero says nothing"
    print("   %-20s %-46s %s" % (name, title, "PASS" if ok else "FAIL"))
    print("        %s" % detail)
    if not ok:
        cfail.append(name)

if cfail:
    print("")
    print("CONTROLS FAILED: %s -- NO COUNT PRINTED." % ", ".join(cfail))
    sys.exit(1)

# ---------------------------------------------------------------- THE TWENTY
print("")
print("=== THE TWENTY ===")
_twenty_doc = json.load(io.open("twenty.json", encoding="utf-8"))
# REFUSE a draw built under a different rule than the one now loaded.
assert_fingerprint(_twenty_doc.get("rule_fingerprint") if isinstance(_twenty_doc, dict) else None,
                   "twenty.json", "rekey20/scan.py")
twenty = _twenty_doc["topics"]
out = []
for t in sorted(twenty, key=lambda x: x["app_id"]):
    # Terms come from terms_for(), the same path the controls use. The frozen
    # class_phrases in twenty.json are provenance, never scored.
    dt, ct = terms_for(t.get("drug") or {})
    cond = t["condition_terms"]
    res = arms(dt, ct, cond)
    rec = {"app_id": t["app_id"], "title": t["title"],
           "rule_outcome": (t["fail"][0] if t["fail"] else "REKEYED"),
           "drug_terms": dt, "class_terms": ct, "condition_terms": cond, "arms": {}}
    for k, (cand, ver, unver) in res.items():
        rec["arms"][k] = {
            "candidates": len(cand), "verified": len(ver), "unverifiable_null_obj": len(unver),
            "verified_bases": [{"cd_base": r["cd_base"], "title": r["title"],
                                "intervention_hits": m["intervention_hits"],
                                "condition_hits": m["condition_hits"],
                                "objectives_verbatim": r["objectives_verbatim"]}
                               for r, m in ver],
        }
    out.append(rec)
    a, b, u = (rec["arms"]["A_drug"], rec["arms"]["B_class"], rec["arms"]["AuB"])
    print("  %-46s %-18s A %d/%d   B %d/%d   AuB %d/%d"
          % (t["app_id"], rec["rule_outcome"],
             a["verified"], a["candidates"], b["verified"], b["candidates"],
             u["verified"], u["candidates"]))

json.dump(out, io.open("scan_result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("")
for arm in ("A_drug", "B_class", "AuB"):
    tp = sum(1 for r in out if r["arms"][arm]["verified"] > 0)
    cd = sum(r["arms"][arm]["candidates"] for r in out)
    vf = sum(r["arms"][arm]["verified"] for r in out)
    un = sum(r["arms"][arm]["unverifiable_null_obj"] for r in out)
    print("  %-8s topics with >=1 verified: %2d/20   candidates %3d -> verified %3d   (unverifiable, null objectives: %d)"
          % (arm, tp, cd, vf, un))
print("")
print("  written: scan_result.json")
