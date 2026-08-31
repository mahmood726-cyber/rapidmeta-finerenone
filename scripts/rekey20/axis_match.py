# -*- coding: utf-8 -*-
"""THE TWO-AXIS MATCHER. Scores intervention and condition INDEPENDENTLY over one frame
and returns a NAMED STATE per topic. Nothing is silently dropped.

Reused, not rebuilt: the frame contract, the rule, the normaliser and the containment test
are `frame_contract.py` and `rekey_rule.py` unchanged. What is new is only that the two
limbs are scored apart before they are scored together, so the report can name WHICH ONE
killed each pair.

⛔ THIS DOES NOT LOOSEN `MATCHED`. The conjunction is identical to `scan.py`: an
intervention term and >=min(2, len(cond)) condition terms in title+objectives, re-verified
in `objectives_verbatim` ALONE. A larger MATCHED count than the existing scan is a DEFECT
here, not a result -- it would mean a criterion moved while a diagnostic was being added.

⭐ HASH THE SET, NEVER THE COUNT. Every axis reports a sha256 over its sorted cd_base set.
Two runs that return 6 rows each and disagree about WHICH six are a difference the counts
cannot show and the hashes cannot hide.
"""
import hashlib, io, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame_contract import load_frame, kinds                      # noqa: E402
from rekey_rule import (norm, contains, condition_terms, split_title,   # noqa: E402
                        class_terms_for_drug, rule_fingerprint, assert_fingerprint)
from axis_states import classify, ALL_STATES                      # noqa: E402
import chembl_resolve as CR                                       # noqa: E402

MATCHER_VERSION = "axis_match v1"


def sha_set(bases):
    """sha256 over the SORTED SET, so it is an identity of WHICH rows and not HOW MANY."""
    h = hashlib.sha256()
    for b in sorted(set(bases)):
        h.update(b.encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()


def prepare(frame_path):
    rows = load_frame(frame_path)
    reviews = [r for r in rows if r["record_kind"] == "review"]
    for r in reviews:
        r["_all"] = norm((r["title"] or "") + " " + (r["objectives_verbatim"] or ""))
        r["_obj"] = norm(r["objectives_verbatim"]) if r["objectives_verbatim"] else None
    return rows, reviews


def _cond_need(cond):
    """⚠️ THE VACUOUS GUARD, AND IT IS THE POINT OF THE FILE.

    With `cond == []` the natural expression `len(hits) >= min(2, len(cond))` becomes
    `0 >= 0` -- TRUE FOR EVERY ROW. An empty condition list would not return zero, it would
    match the ENTIRE FRAME, and the topic would report 1,186 candidates as though its
    condition were universally satisfied. That is `all([])` in numeric clothing.

    Refusing here is not defensive tidiness: the two topics with no condition connective in
    their title have exactly this term list.
    """
    if not cond:
        raise ValueError("condition term list is empty; the caller must REFUSE, not score")
    return min(2, len(cond))


def axis_intervention(reviews, terms, field="_all"):
    """rows where ANY intervention term appears. Independent of the condition."""
    if not terms:
        raise ValueError("intervention term list is empty; the caller must REFUSE")
    hits = {}
    for r in reviews:
        hay = r[field]
        if hay is None:
            continue
        t = [x for x in terms if contains(hay, x)]
        if t:
            hits[r["cd_base"]] = t
    return hits


def axis_condition(reviews, cond, field="_all"):
    """rows where >= need condition terms appear. Independent of the intervention."""
    need = _cond_need(cond)
    hits = {}
    for r in reviews:
        hay = r[field]
        if hay is None:
            continue
        c = [x for x in cond if contains(hay, x)]
        if len(c) >= need:
            hits[r["cd_base"]] = c
    return hits


def term_liveness(reviews, terms):
    """How many rows each term matches ALONE.

    ⭐ A ZERO PRODUCED BY A DEAD TERM IS NOT A NEGATIVE RESULT. And a match carried by one
    bare fragment is the failure mode that made `olmesartan-htn` verify against two
    endothelin-antagonist reviews on a shared two-word suffix.
    """
    return {t: sum(1 for r in reviews if contains(r["_all"], t)) for t in terms}


def score(reviews, iterms, cterms):
    """-> full record with a NAMED STATE. The only entry point; plants use it too."""
    rec = {"intervention_terms": list(iterms), "condition_terms": list(cterms),
           "have_intervention_terms": bool(iterms), "have_condition_terms": bool(cterms)}
    if not iterms or not cterms:
        st, why = classify(0, 0, 0, 0, bool(iterms), bool(cterms))
        rec.update({"state": st, "reason": why, "vacuous": True,
                    "axis_intervention": None, "axis_condition": None,
                    "both": None, "verified": None,
                    "vacuous_axes": ([] if iterms else ["intervention"]) +
                                    ([] if cterms else ["condition"])})
        return rec

    ih = axis_intervention(reviews, iterms)
    ch = axis_condition(reviews, cterms)
    both = sorted(set(ih) & set(ch))

    by_base = {r["cd_base"]: r for r in reviews}
    verified, unverifiable, unverified = [], [], []
    for b in both:
        r = by_base[b]
        if r["_obj"] is None:
            unverifiable.append(b)
            continue
        oi = [x for x in iterms if contains(r["_obj"], x)]
        oc = [x for x in cterms if contains(r["_obj"], x)]
        if oi and len(oc) >= _cond_need(cterms):
            verified.append(b)
        else:
            unverified.append(b)

    st, why = classify(len(ih), len(ch), len(both), len(verified), True, True)
    rec.update({
        "state": st, "reason": why, "vacuous": False, "vacuous_axes": [],
        "axis_intervention": {"n": len(ih), "sha256": sha_set(ih),
                              "liveness": term_liveness(reviews, iterms)},
        "axis_condition": {"n": len(ch), "sha256": sha_set(ch),
                           "liveness": term_liveness(reviews, cterms)},
        "both": {"n": len(both), "sha256": sha_set(both), "bases": both},
        "verified": {"n": len(verified), "sha256": sha_set(verified), "bases": verified},
        "unverifiable_null_objectives": unverifiable,
        "retrieved_but_unverified": unverified,
    })
    return rec


def terms_for(drug_record):
    """drug -> (drug terms, class terms). Same single source scan.py uses."""
    name = (drug_record or {}).get("pref_name") or ""
    dt = [x for x in [norm(name).strip()] if x]
    ct, fail = class_terms_for_drug(drug_record)
    return dt, ct, fail


def synth(title):
    """A synthetic topic built from a title, through the rule -- the controls' path."""
    inter, cond = split_title(title)
    tok = [w for w in inter.split() if len(w) > 3]
    d = CR.resolve(tok[0]) if tok else None
    dt, ct, _ = terms_for(d)
    return sorted(set(dt) | set(ct)), (condition_terms(cond) if cond else [])


def ref(frame_path, twenty_path):
    """THE ARTEFACT CONTROL. Proves WHICH bytes were read, not that reading succeeded."""
    rows = load_frame(frame_path)
    doc = json.load(io.open(twenty_path, encoding="utf-8"))
    assert_fingerprint(doc.get("rule_fingerprint") if isinstance(doc, dict) else None,
                       twenty_path, "rekey20/axis_match.py")
    return {
        "matcher": MATCHER_VERSION,
        "rule_fingerprint": rule_fingerprint(),
        "frame_path": frame_path,
        "frame_bytes": os.path.getsize(frame_path),
        "frame_rows": len(rows),
        "frame_base_set_sha256": sha_set(r["cd_base"] for r in rows),
        "frame_kinds": dict(kinds(rows)),
        "twenty_path": twenty_path,
        "twenty_bytes": os.path.getsize(twenty_path),
        "twenty_app_id_set_sha256": sha_set(t["app_id"] for t in doc["topics"]),
        "twenty_n": len(doc["topics"]),
    }
