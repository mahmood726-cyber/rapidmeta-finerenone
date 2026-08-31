# -*- coding: utf-8 -*-
"""Does the INDEX describe the same review the OBJECT describes?

WHY THIS EXISTS -- and it is a class, not an incident.

`scripts/project_index_cards.py` retired a real defect: index cards carried
hand-typed numbers that disagreed with their pages, on all four topics checked.
It fixed that by PROJECTING THE NUMBERS from the object. Its own docstring
states the split:

    THE NUMBERS ARE PROJECTED. Measure, point, interval and k come from the
    object ... so a card cannot disagree with its page about a value.
    THE PROSE IS AUTHORED.

⛔ SO A CARD CANNOT DISAGREE ABOUT A VALUE AND IS FREE TO DISAGREE ABOUT WHAT
THE REVIEW IS. Re-point an object at a different question and the number
updates while the title does not. The result is the worst artefact of the two:
A CORRECT NUMBER UNDER A WRONG NAME, which reads as verified.

The live instance, on the front page, on the topic taken furthest:

    object  : "Dapivirine vaginal ring versus placebo ring for HIV prevention
               in women", trials NCT01539226 + NCT01617096, RR 0.703 k=2
    tile    : "HIV PrEP for AGYW in sub-Saharan Africa (HPTN 082 + FACTS-001)
               -- Pooled: RR 0.703 (0.566 to 0.8731), k=2"
    table   : "HIV PrEP for AGYW in sub-Saharan Africa -- oral PrEP adherence
               23% vs 12%; vaginal TFV gel NULL", v0.1
    PAGE_MAP: "HIV PrEP Modalities for Adolescent Girls and Young Women in
               sub-Saharan Africa NMA"

FOUR DESCRIPTIONS OF ONE URL. The number in the tile is right and everything
naming the review is wrong; HPTN 082 and FACTS-001 appear NOWHERE in the store,
which holds zero occurrences of either. They come from
`scripts/build_3topics_hep_mhealth_agyw.py`, the ORIGINAL builder, which made
this URL an NMA of oral PrEP against tenofovir gel before the object was
re-pointed at the dapivirine ring.

WHY NOTHING CAUGHT IT: `project_index_cards.py --check` compares VALUES. A
title mismatch is invisible to it BY DESIGN, and no other check compares an
index label against its object. This module is that missing check.

    python scripts/audit_index_identity_drift.py            # report
    python scripts/audit_index_identity_drift.py --selftest # prove it fires

NO NETWORK. Reads index.html and the SSOT objects on disk.
"""
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _norm(s):
    """Compare on content words, not on punctuation or case."""
    s = re.sub(r"&[a-z]+;", " ", str(s or ""))
    s = re.sub(r"<[^>]+>", " ", s)
    return set(w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 3)


def object_for(url):
    """SSOT object whose delivered page is `url`, or None.

    The convention is UPPER_SNAKE + _REVIEW.html against a kebab app_id, so the
    mapping is derived rather than tabulated -- a hand-kept table is one more
    surface that can drift, which is the defect this module exists to find."""
    stem = re.sub(r"\.html$", "", url)
    slug = stem.lower().replace("_", "-")
    for cand in (slug, re.sub(r"-review$", "-review", slug)):
        p = os.path.join(ROOT, "ssot", cand, cand + ".json")
        if os.path.exists(p):
            return p
    # Fall back to app_id -- but build the map ONCE.
    #
    # ⚠️ THE FIRST VERSION LOADED EVERY OBJECT FOR EVERY UNMAPPED URL. With
    # ~1,500 linked urls and 161 objects that is a quarter of a million JSON
    # parses, and the audit did not finish. A checker slow enough that nobody
    # runs it protects nothing.
    for path, aid in _appid_map().items():
        if aid == slug:
            return path
    return None


_APPID_CACHE = {}


def _appid_map():
    if _APPID_CACHE:
        return _APPID_CACHE
    for p in glob.glob(os.path.join(ROOT, "ssot", "*", "*.json")):
        if p.endswith(".striptest"):
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict):
            _APPID_CACHE[p] = str(d.get("app_id") or "").lower()
    return _APPID_CACHE


def tiles_from_index(html):
    """(url, label) for every anchor to a review page, with the visible text."""
    out = []
    for m in re.finditer(r'href=["\']([A-Z0-9_]+\.html)["\'][^>]*>(.{0,400}?)</a>',
                         html, re.S):
        url, inner = m.group(1), m.group(2)
        txt = re.sub(r"<[^>]+>", " ", inner)
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt:
            out.append((url, txt))
    return out


# Trial-acronym / programme-code shapes an index label might name.
# HPTN 082, FACTS-001, EMPA-REG, MTN-020, DISCOVER -- the things a card uses to
# say WHICH trials a pool is over.
_ENTITY = re.compile(r"\b([A-Z][A-Z0-9]{2,}(?:[- ]?\d{2,4})?)\b")
# ⚠️ THE WORD-BOUNDARY ANCHORS IN THE PATTERN ABOVE WERE ONCE LITERAL
# BACKSPACE CHARACTERS (0x08). Written through a non-raw string, the two
# escapes collapsed, so the pattern demanded a backspace either side of
# every token and MATCHED NOTHING, EVER. The audit then reported
# 'ENTITY DRIFT: 0 of 44' -- a reassuring zero produced by a regex that
# cannot fire, on the one check written to catch a live front-page defect.
# grep rendered the backspace as empty space, so the line read correctly
# on inspection and only repr() showed it. The selftest below now asserts
# the pattern finds the two REAL entities, so this cannot recur silently.
_ENTITY_STOP = {"NMA", "HIV", "RSV", "CKD", "AF", "VTE", "PREP", "DOAC", "SGLT",
                "SGLT2", "MACE", "CVOT", "ACS", "COPD", "LRTI", "TDF", "FTC",
                "TAF", "LA", "CI", "RR", "OR", "HR", "MD", "AGYW", "USA", "UK",
                "WHO", "FDA", "EMA", "PMID", "NCT", "AND", "THE", "FOR", "WITH",
                "III", "II", "IV", "MDR", "TB", "ACT", "CABP", "PSA", "RA",
                # Clinical abbreviations the first run flagged as trials.
                # 6 of 44 fired and only ONE named actual trials; these four
                # were MRSA, ASCVD, TMVR and LMIC -- a pathogen, a condition, a
                # procedure and a setting. Reporting them beside a real finding
                # is how a check gets ignored.
                "MRSA", "ASCVD", "TMVR", "LMIC", "CAP", "HAP", "VAP", "CKD",
                "ESRD", "COVID", "SARS", "BMI", "LDL", "HDL", "GFR"}


def entities_in(label):
    """Trial/programme names a label asserts."""
    out = set()
    for m in _ENTITY.finditer(str(label or "")):
        tok = m.group(1).strip()
        base = re.split(r"[- ]", tok)[0]
        if base in _ENTITY_STOP or len(base) < 3:
            continue
        out.add(tok)
    return out


def entity_drift(label, obj_blob):
    """⭐ THE SHARP TEST, and the one that actually discriminates.

    Word overlap between an index label and an object title conflates a
    SYNONYM with a DIFFERENT REVIEW: "SGLT2i in CKD" shares almost no words
    with "Canagliflozin, dapagliflozin and empagliflozin in kidney disease" and
    is the same review. Flagging it teaches a reader to ignore the check.

    A label that NAMES A TRIAL THE OBJECT HAS NEVER HEARD OF is different in
    kind. It is not shorter vocabulary; it is an assertion about which studies
    the pool is over, and the store can adjudicate it. AGYW's card names HPTN
    082 and FACTS-001; the store contains ZERO occurrences of either.
    """
    named = entities_in(label)
    if not named:
        return []
    blob = obj_blob.upper()
    missing = []
    for e in sorted(named):
        squashed = re.sub(r"[- ]", "", e).upper()
        if e.upper() in blob or squashed in re.sub(r"[- ]", "", blob):
            continue
        missing.append(e)
    return missing


def audit():
    idx = os.path.join(ROOT, "index.html")
    if not os.path.exists(idx):
        return {"state": "NO_INDEX", "path": idx}
    html = open(idx, encoding="utf-8", errors="replace").read()
    tiles = tiles_from_index(html)

    by_url = {}
    for url, txt in tiles:
        by_url.setdefault(url, []).append(txt)

    rows, drift, agree, unmapped, ghosted = [], [], 0, [], []
    ghosted_hard, ghosted_soft = [], []
    for url, labels in sorted(by_url.items()):
        obj_path = object_for(url)
        if not obj_path:
            unmapped.append(url)
            continue
        try:
            d = json.load(open(obj_path, encoding="utf-8"))
        except Exception:
            unmapped.append(url)
            continue
        otitle = str(d.get("title") or "")
        ow = _norm(otitle)
        if not ow:
            continue
        # A label AGREES if it shares a decent share of the object's content
        # words. Exact equality is the wrong test: the index legitimately
        # shortens titles, and a strict comparison would report the whole
        # corpus as drifted and be ignored within a day.
        # ⚠️ START BELOW ZERO. With `best = 0.0` a label scoring exactly 0.00
        # never updates `best_txt`, so the report printed an EMPTY index label
        # for precisely the entries that had drifted furthest -- the detection
        # was right and the evidence for it was blank. A reviewer reading that
        # output would have concluded the extractor was broken and ignored a
        # correct finding.
        best, best_txt = -1.0, ""
        for txt in labels:
            lw = _norm(txt)
            if not lw:
                continue
            share = len(ow & lw) / float(len(ow))
            if share > best:
                best, best_txt = share, txt
        blob = json.dumps(d, ensure_ascii=False)
        ghosts = entity_drift(best_txt, blob)
        rows.append((url, round(best, 2), otitle, best_txt, ghosts))
        if ghosts:
            # TWO TIERS BY PRECISION, because one number hiding two very
            # different confidences is how a check loses its audience. A token
            # carrying DIGITS ("HPTN 082", "FACTS-001", "MTN-020") is a trial
            # or programme code and the object should contain it. A bare
            # all-caps token may be a trial or may be a clinical abbreviation,
            # and those need a human.
            hard = [g for g in ghosts if re.search(r"\d", g)]
            (ghosted_hard if hard else ghosted_soft).append(
                (url, hard or ghosts, otitle, best_txt))
            ghosted.append((url, ghosts, otitle, best_txt))
        if best < 0.34:
            drift.append((url, round(best, 2), otitle, best_txt))
        else:
            agree += 1

    return {"state": "OK", "n_urls_linked": len(by_url),
            "n_mapped_to_an_object": len(rows), "n_unmapped": len(unmapped),
            "unmapped_sample": unmapped[:8],
            "agree": agree, "drift": drift, "rows": rows,
            "ghosted": ghosted, "ghosted_hard": ghosted_hard,
            "ghosted_soft": ghosted_soft}


def selftest():
    """⭐ A CHECK THAT HAS NEVER FIRED IS NOT PROVEN.

    Two synthetic pairs, scored through the real comparison: one where the
    index label describes the same review as the object, one where it
    describes a different one. Both are DISCARDED and never enter a count.
    """
    same_obj = "Dapivirine vaginal ring versus placebo ring for HIV prevention in women"
    same_lbl = "Dapivirine vaginal ring versus placebo ring, HIV prevention"
    diff_lbl = "HIV PrEP for AGYW in sub-Saharan Africa (HPTN 082 + FACTS-001)"
    ow = _norm(same_obj)
    s_same = len(ow & _norm(same_lbl)) / float(len(ow))
    s_diff = len(ow & _norm(diff_lbl)) / float(len(ow))
    assert s_same >= 0.34, ("SELFTEST FAILED: a matching label scored %.2f and "
                            "would have been reported as drift." % s_same)
    assert s_diff < 0.34, ("SELFTEST FAILED: the REAL divergent label scored "
                           "%.2f and would have passed. The check cannot fire "
                           "on the defect it was written for." % s_diff)
    # ⭐ AND ASSERT THE ENTITY PATTERN ACTUALLY MATCHES. It once compiled to a
    # pattern requiring literal backspace characters and found nothing on every
    # input, reporting a clean "0 of 44". A pattern is not proven by compiling.
    ents = entities_in(diff_lbl)
    assert "HPTN 082" in ents and "FACTS-001" in ents, (
        "SELFTEST FAILED: the entity pattern did not find HPTN 082 and "
        "FACTS-001 in the real divergent label. It found %r. A pattern that "
        "matches nothing reports a reassuring zero." % (sorted(ents),))
    ghosts = entity_drift(diff_lbl, "a store that mentions neither trial")
    assert set(ghosts) == {"HPTN 082", "FACTS-001"}, ghosts

    return {"matching_label_scores": round(s_same, 2),
            "entity_pattern_finds": sorted(ents),
            "entity_drift_on_the_real_case": sorted(ghosts),
            "the_real_divergent_label_scores": round(s_diff, 2),
            "threshold": 0.34,
            "both_controls_are_synthetic_and_discarded": True}


def main():
    if "--selftest" in sys.argv:
        print("INDEX IDENTITY DRIFT -- SELFTEST")
        print(json.dumps(selftest(), indent=1, ensure_ascii=False))
        return
    r = audit()
    if r["state"] != "OK":
        print("REFUSED: %s" % r)
        return
    print("INDEX IDENTITY DRIFT -- does the index describe the same review?")
    print()
    print("  review URLs linked from index.html : %d" % r["n_urls_linked"])
    print("  mapped to an SSOT object           : %d  <- the denominator"
          % r["n_mapped_to_an_object"])
    print("  NOT mapped (no object found)       : %d" % r["n_unmapped"])
    for u in r["unmapped_sample"]:
        print("      %s" % u)
    print()
    n = r["n_mapped_to_an_object"]
    print("  index label AGREES with object title : %d of %d" % (r["agree"], n))
    print("  DRIFTED (shares < 34%% of title words): %d of %d"
          % (len(r["drift"]), n))
    print()
    if r["drift"]:
        print("  DRIFTED ENTRIES, worst first:")
        for url, share, otitle, label in sorted(r["drift"], key=lambda x: x[1])[:25]:
            print("    %-38s overlap %.2f" % (url[:38], share))
            print("        object : %s" % otitle[:96])
            print("        index  : %s" % label[:96])
    print()
    hard = r.get("ghosted_hard") or []
    soft = r.get("ghosted_soft") or []
    print("  " + "=" * 68)
    print("  ⭐ ENTITY DRIFT -- the index names a trial the object never mentions")
    print()
    print("  TIER 1, HIGH CONFIDENCE -- the named token carries digits, so it is")
    print("  a trial or programme code and the object should contain it.")
    print("     %d of %d mapped entries" % (len(hard), n))
    for url, ghosts, otitle, label in hard:
        print("    %-38s names %s" % (url[:38], ", ".join(ghosts)))
        print("        object : %s" % otitle[:92])
        print("        index  : %s" % label[:92])
    print()
    print("  TIER 2, NEEDS A HUMAN -- a bare all-caps token the object lacks.")
    print("  May be a trial, may be a clinical abbreviation.")
    print("     %d of %d mapped entries" % (len(soft), n))
    for url, ghosts, otitle, label in soft:
        print("    %-38s names %s" % (url[:38], ", ".join(ghosts)))
    print("  " + "=" * 68)
    print()
    print("  ⚠️ THE WORD-OVERLAP FIGURE ABOVE HAS POOR SPECIFICITY. It flags")
    print("     'SGLT2i in CKD' against 'Canagliflozin, dapagliflozin and")
    print("     empagliflozin in kidney disease' -- the same review in shorter")
    print("     vocabulary. ENTITY DRIFT is the discriminating signal.")
    print()
    print("  ⚠️ THIS IS AN IDENTITY CHECK, NOT A VALUE CHECK. "
          "project_index_cards.py already")
    print("     guarantees the NUMBERS agree. Nothing until now compared what "
          "the index SAYS")
    print("     the review IS against what the object says it is.")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
