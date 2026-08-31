# -*- coding: utf-8 -*-
"""Ingest the Embase RIS export and build a BLINDED eligibility worksheet.

⭐ BLINDED BY CONSTRUCTION, NOT BY DISCIPLINE. The worksheet this emits has NO column
saying whether we already hold a record, and this module never loads our included set. The
join happens in a SECOND pass (`join_to_ours`) that runs only after eligibility is fixed
and written to disk. An eligibility judgement made while looking at our own coverage is a
judgement about our performance, and it would quietly convert the calibration into a
self-assessment.

⚠️ WHAT THE DENOMINATOR IS. The calibration measures TRIALS, not records. 1,044 Embase
records will contain conference abstracts, secondary analyses, PK sub-studies and reviews
of the same handful of trials. So the pipeline is:

    records -> deduplicate -> resolve to TRIALS -> blinded eligibility screen -> M
    then, separately:  M joined to our included set -> N

⭐ THE CHEMICAL-NAME FLAG, AND WHY IT IS HERE. Ovid's expansion of the Emtree drug term
showed SIX chemical-name variants of dapivirine that a free-source search on the word
"dapivirine" cannot reach. A record indexed ONLY under such a form is exactly where an
Embase-only trial would hide. `chemical_name_only` marks those, so the calibration can
answer the mechanism question rather than asserting it either way.

⚠️ AND A RECORD IS NOT A TRIAL. Resolution to a trial is by registry identifier where one
is present, and by explicit acronym otherwise. Anything that resolves to NEITHER is
reported as UNRESOLVED and must be read by a person -- it is never silently dropped, because
a dropped record is a denominator shrinking without a decision.
"""
import io
import json
import os
import re
import sys
from collections import OrderedDict

# Registry identifier shapes. Bounded patterns, per the ReDoS rule.
REG_PATTERNS = [
    ("NCT", r"\bNCT\d{8}\b"),
    ("ISRCTN", r"\bISRCTN\d{8}\b"),
    ("PACTR", r"\bPACTR\d{12,20}\b"),
    ("ACTRN", r"\bACTRN\d{14}\b"),
    ("ChiCTR", r"\bChiCTR[-A-Za-z0-9]{4,20}\b"),
    ("CTRI", r"\bCTRI/\d{4}/\d{2,3}/\d{6}\b"),
    ("IRCT", r"\bIRCT\d{11,20}[Nn]\d{1,3}\b"),
    ("DRKS", r"\bDRKS\d{8}\b"),
    ("EudraCT", r"\b\d{4}-\d{6}-\d{2}\b"),
    ("jRCT", r"\bjRCT[0-9a-z]{8,12}\b"),
]

# Trial acronyms for this question, from the published literature -- used ONLY to resolve a
# record to a trial when no registry id is present, never to decide eligibility.
ACRONYMS = ["ASPIRE", "MTN-020", "MTN 020", "RING STUDY", "IPM 027", "IPM-027",
            "HOPE", "MTN-025", "MTN 025", "DREAM", "IPM 032", "IPM-032",
            "REACH", "MTN-034", "MTN 034", "MTN-023", "IPM 030", "MTN-024", "IPM 031"]

# The six chemical-name forms Ovid reported, normalised for matching.
CHEMICAL_FORMS = [
    "trimethylanilino) 2 pyrimidinylamino]benzonitrile",
    "trimethylanilino) 2 pyrimidylamino]benzonitrile",
    "trimethylanilino)pyrimidin 2 ylamino]benzonitrile",
    "trimethylphenyl)amino] 2 pyrimidinyl]amino]benzonitrile",
    "trimethylphenyl)amino] 2 pyrimidyl]amino]benzonitrile",
    "trimethylphenyl)amino]pyrimidin 2 yl]amino]benzonitrile",
    "benzonitrile",
]
PLAIN_NAMES = ["dapivirine", "dapavirine", "tmc120", "tmc 120", "tmc-120",
               "r147681", "r 147681", "r-147681"]


def parse_ris(text):
    """RIS -> list of records. Tolerant of the field variants Ovid emits."""
    records, cur = [], None
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", line)
        if m:
            tag, val = m.group(1), m.group(2)
            if tag == "TY":
                if cur:
                    records.append(cur)
                cur = OrderedDict()
            if cur is None:
                cur = OrderedDict()
            cur.setdefault(tag, []).append(val)
        elif cur is not None and line.strip():
            # continuation of the previous field
            if cur:
                last = next(reversed(cur))
                cur[last][-1] += " " + line.strip()
    if cur:
        records.append(cur)
    return records


def _blob(rec):
    return " ".join(v for vals in rec.values() for v in vals)


def _norm(s):
    return re.sub(r"\s+", " ", (s or "")).lower()


def summarise(rec):
    blob = _blob(rec)
    n = _norm(blob)
    ids = []
    for name, pat in REG_PATTERNS:
        for hit in re.findall(pat, blob, re.I):
            ids.append(hit.upper() if name != "CTRI" else hit)
    acro = sorted({a for a in ACRONYMS if a.lower() in n})
    has_plain = any(p in n for p in PLAIN_NAMES)
    has_chem = any(c in n for c in CHEMICAL_FORMS)
    return {
        "title": (rec.get("TI") or rec.get("T1") or [""])[0][:300],
        "year": (rec.get("PY") or rec.get("Y1") or [""])[0][:10],
        "type": (rec.get("TY") or [""])[0],
        "journal": (rec.get("JO") or rec.get("JF") or rec.get("T2") or [""])[0][:120],
        "abstract_present": bool(rec.get("AB")),
        "registry_ids": sorted(set(ids)),
        "acronyms": acro,
        # ⭐ the mechanism flag: reachable ONLY by a chemical name
        "chemical_name_only": bool(has_chem and not has_plain),
        "mentions_plain_name": has_plain,
    }


def build_worksheet(ris_path, out_path):
    text = open(ris_path, encoding="utf-8", errors="replace").read()
    recs = [summarise(r) for r in parse_ris(text)]

    # Resolve records to TRIALS. A record with no identifier and no acronym is UNRESOLVED
    # and is listed for a human -- never dropped.
    trials, unresolved = {}, []
    for r in recs:
        key = r["registry_ids"][0] if r["registry_ids"] else (
            r["acronyms"][0] if r["acronyms"] else None)
        if key is None:
            unresolved.append(r)
            continue
        t = trials.setdefault(key, {"trial_key": key, "n_records": 0,
                                    "registry_ids": set(), "acronyms": set(),
                                    "titles": [], "any_chemical_name_only": False})
        t["n_records"] += 1
        t["registry_ids"].update(r["registry_ids"])
        t["acronyms"].update(r["acronyms"])
        if len(t["titles"]) < 3:
            t["titles"].append(r["title"])
        t["any_chemical_name_only"] |= r["chemical_name_only"]

    rows = []
    for k, t in sorted(trials.items()):
        rows.append({"trial_key": k,
                     "registry_ids": sorted(t["registry_ids"]),
                     "acronyms": sorted(t["acronyms"]),
                     "n_records": t["n_records"],
                     "example_titles": t["titles"],
                     "reachable_only_by_chemical_name": t["any_chemical_name_only"],
                     # ⭐ THE COLUMN THE SCREENER FILLS. Nothing else is pre-filled, and
                     # there is deliberately NO column saying whether we hold it.
                     "ELIGIBLE": None,
                     "ELIGIBILITY_REASON": ""})

    out = {
        "source_ris": os.path.basename(ris_path),
        "n_records_parsed": len(recs),
        "n_records_unresolved": len(unresolved),
        "n_candidate_trials": len(rows),
        "n_records_chemical_name_only": sum(1 for r in recs if r["chemical_name_only"]),
        "eligibility_criterion": (
            "Randomised comparison of a DAPIVIRINE VAGINAL RING against a PLACEBO VAGINAL "
            "RING, reporting HIV-1 seroconversion. An open-label extension with no placebo "
            "arm, a crossover against oral PrEP, and a phase 2a safety study are all "
            "INELIGIBLE -- and being ineligible is not being missed."),
        "blinding": (
            "This worksheet carries NO information about which trials our search already "
            "holds, and this module never loads our included set. Fill ELIGIBLE before "
            "running the join."),
        "trials": rows,
        "unresolved_records": unresolved,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return out


def join_to_ours(worksheet_path, ours):
    """SECOND PASS ONLY. Refuses if eligibility has not been filled in."""
    w = json.load(open(worksheet_path, encoding="utf-8"))
    unscreened = [t["trial_key"] for t in w["trials"] if t.get("ELIGIBLE") is None]
    if unscreened:
        return {"status": "REFUSED",
                "reason": ("%d candidate trial(s) have no eligibility judgement yet (%s). "
                           "The join is the SECOND pass and running it now would let our "
                           "own coverage inform the screen, which is the one thing this "
                           "calibration must not do."
                           % (len(unscreened), ", ".join(unscreened[:6])))}
    ours = {str(o).upper() for o in ours}
    eligible = [t for t in w["trials"] if t.get("ELIGIBLE") is True]
    held = [t for t in eligible if set(i.upper() for i in t["registry_ids"]) & ours]
    missed = [t for t in eligible if t not in held]
    return {"status": "OK",
            "M_eligible_trials": len(eligible),
            "N_held_by_free_sources": len(held),
            "recovery": (float(len(held)) / len(eligible)) if eligible else None,
            "embase_only_eligible_trials": [t["trial_key"] for t in missed],
            "of_those_reachable_only_by_chemical_name":
                [t["trial_key"] for t in missed
                 if t.get("reachable_only_by_chemical_name")]}


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print("usage: embase_calibration_screen.py <export.ris> [worksheet.json]")
        sys.exit(2)
    ris = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "F:/claude-temp/rm-dapivirine-2026-08-31/embase_worksheet.json"
    r = build_worksheet(ris, out)
    print("records parsed                 : %d" % r["n_records_parsed"])
    print("records with no trial resolved : %d  (listed, never dropped)"
          % r["n_records_unresolved"])
    print("candidate TRIALS               : %d" % r["n_candidate_trials"])
    print("records reachable ONLY by a chemical name : %d"
          % r["n_records_chemical_name_only"])
    print()
    for t in r["trials"][:40]:
        print("  %-22s recs=%-4d chem_only=%-5s %s"
              % (t["trial_key"], t["n_records"],
                 t["reachable_only_by_chemical_name"],
                 (t["example_titles"][0] if t["example_titles"] else "")[:70]))
    print()
    print("worksheet -> %s   (ELIGIBLE column is empty by design)" % out)
