"""HARMONY Outcomes (NCT02465515) checksum + provenance test.

Locks the 2026-07-18 fix (commit 8b2eaeac0) against regression.

Two invariants:

1. COMPOSITE CHECKSUM. HARMONY's primary endpoint is a 3-point MACE
   (CV death + nonfatal MI + nonfatal stroke), so the three component
   objects MUST sum exactly to the MACE object:
        CVD 102/109 + MI 160/228 + Stroke 76/91  ==  MACE 338/428
   This is the arithmetic that proves the card<->object fix is coherent
   rather than merely self-consistent. 338/428 is HARMONY's published
   primary result (Hernandez AF et al, Lancet 2018;392:1519-1529).

2. SENTINEL PROVENANCE. MI and Stroke carry effect:0,lci:0,uci:0 -- the
   "no applicable ratio" sentinel -- because the published HR 0.75 (MI) /
   0.86 (stroke) are TOTAL (fatal+nonfatal) estimates while these counts
   are nonfatal-only. Any object using that sentinel MUST carry an
   effectNote saying why, or the app silently shows "--" with no reason.

Run:  python scripts/test_harmony_checksum.py    |    pytest scripts/test_harmony_checksum.py
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, os.pardir, "GLP1_CVOT_REVIEW.html")


def _harmony_span():
    """(doc, start, end) of HARMONY's allOutcomes array, anchored on its
    published primary 338/428 -- not on a fragile source string (the file
    has 10 'Hernandez AF' citations, incl. the Table 3 adverse-event card)."""
    d = open(APP, encoding="utf-8", errors="replace").read()
    anchor = re.search(r"allOutcomes:\[[^\]]*tE:338,cE:428", d)
    assert anchor, "HARMONY allOutcomes (MACE 338/428) not found"
    return d, anchor.start()


def _harmony_objects():
    d, k = _harmony_span()
    start = d.find("[", k)
    depth = 0
    end = start
    for x in range(start, len(d)):
        if d[x] == "[":
            depth += 1
        elif d[x] == "]":
            depth -= 1
            if depth == 0:
                end = x
                break
    out = {}
    for m in re.finditer(r"\{[^{}]*\}", d[start:end + 1]):
        s = m.group(0)
        lbl = re.search(r'shortLabel:"([^"]*)"', s)
        te = re.search(r"tE:(\d+)", s)
        ce = re.search(r"cE:(\d+)", s)
        eff = re.search(r"effect:([\d.]+)", s)
        if lbl and te and ce:
            out[lbl.group(1)] = {
                "tE": int(te.group(1)), "cE": int(ce.group(1)),
                "effect": eff.group(1) if eff else None,
                "effectNote": ('effectNote:"' in s),
                "raw": s,
            }
    return out


def test_components_sum_to_mace():
    o = _harmony_objects()
    for k in ("MACE", "CVD", "MI", "Stroke"):
        assert k in o, f"HARMONY missing {k}"
    tE = o["CVD"]["tE"] + o["MI"]["tE"] + o["Stroke"]["tE"]
    cE = o["CVD"]["cE"] + o["MI"]["cE"] + o["Stroke"]["cE"]
    assert (tE, cE) == (o["MACE"]["tE"], o["MACE"]["cE"]), (
        f"3-pt MACE checksum FAILED: components {tE}/{cE} != MACE "
        f'{o["MACE"]["tE"]}/{o["MACE"]["cE"]}')
    assert (o["MACE"]["tE"], o["MACE"]["cE"]) == (338, 428), (
        "HARMONY MACE is not the published 338/428")


def test_zero_sentinel_carries_provenance():
    o = _harmony_objects()
    for label, rec in o.items():
        if rec["effect"] in ("0", "0.0"):
            assert rec["effectNote"], (
                f"{label} uses the effect:0 sentinel but carries no effectNote "
                "explaining why no ratio is shown")


def test_card_text_matches_objects():
    """The human-readable card must agree with the object it sits beside.
    Scoped to HARMONY's trial segment (its allOutcomes -> the next trial's)."""
    d, k = _harmony_span()
    nxt = d.find("allOutcomes:[", k + 10)
    seg = d[k: nxt if nxt > 0 else len(d)]
    o = _harmony_objects()
    checked = 0
    for label, pat in (("CVD", r"Cardiovascular death: (\d+) \([\d.]+%\)[^.]*?vs (\d+)"),
                       ("ACM", r"All-cause mortality: (\d+) \([\d.]+%\)[^.]*?vs (\d+)"),
                       ("MI", r"Nonfatal MI: (\d+) \([\d.]+%\)[^.]*?vs (\d+)"),
                       ("Stroke", r"Nonfatal stroke: (\d+) \([\d.]+%\)[^.]*?vs (\d+)")):
        m = re.search(pat, seg)
        if not m:
            continue
        checked += 1
        assert (int(m.group(1)), int(m.group(2))) == (o[label]["tE"], o[label]["cE"]), (
            f"{label} card {m.group(1)}/{m.group(2)} != object "
            f'{o[label]["tE"]}/{o[label]["cE"]}')
    assert checked >= 2, f"expected >=2 HARMONY card lines to verify, found {checked}"


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_") and callable(f):
            f()
            print("PASS", n)
    ob = _harmony_objects()
    print("  components %d/%d == MACE %d/%d" % (
        ob["CVD"]["tE"] + ob["MI"]["tE"] + ob["Stroke"]["tE"],
        ob["CVD"]["cE"] + ob["MI"]["cE"] + ob["Stroke"]["cE"],
        ob["MACE"]["tE"], ob["MACE"]["cE"]))
    print("all HARMONY checksum tests passed")
