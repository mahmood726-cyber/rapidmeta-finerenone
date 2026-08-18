"""Known-answer test for ssot/topic_identity.locate() BEFORE trusting any of its output.

Two questions, and the second is the one that matters:

  Q1. Given the RAW ClinicalTrials.gov v2 shape (protocolSection.armsInterventionsModule),
      does locate() get NCT02789917 right? Expected: EXPERIMENTAL via the title-only branch,
      because apixaban appears nowhere but the title and there IS an EXPERIMENTAL arm.

  Q2. Given the shape the MCP search tool actually returns (flattened: no protocolSection,
      no armGroups, no arm types), what does locate() say? If it says NOT_ASSESSABLE for a
      trial whose answer we know, the instrument is not wired to its transport, and every
      count produced through that path is void rather than conservative.
"""
import sys

sys.path.insert(0, "F:/rapidmeta-ssot-shell/ssot")

import topic_identity as T

SYNS = T.synonyms_for("apixaban")

# --- Q1: the RAW v2 shape, transcribed from the live record for NCT02789917. ------------
RAW = {
    "protocolSection": {
        "identificationModule": {
            "briefTitle": "APixaban vs. PhenpRocoumon in Patients With ACS and AF: APPROACH-ACS-AF",
            "officialTitle": ("APixaban Versus PhenpRocoumon: Oral AntiCoagulation Plus "
                              "Antiplatelet tHerapy in Patients With Acute Coronary Syndrome "
                              "and Atrial Fibrillation"),
            "orgStudyIdInfo": {"id": "APPROACH-ACS-AF"},
        },
        "armsInterventionsModule": {
            "armGroups": [
                {"label": "Dual therapy (incl. NOAC)", "type": "EXPERIMENTAL",
                 "interventionNames": ["Other: Dual Therapy"]},
                {"label": "Triple therapy (incl. VKA)", "type": "ACTIVE_COMPARATOR",
                 "interventionNames": ["Other: Triple Therapy"]},
            ],
            "interventions": [
                {"name": "Dual Therapy", "type": "OTHER", "otherNames": []},
                {"name": "Triple Therapy", "type": "OTHER", "otherNames": []},
            ],
        },
    }
}

# --- Q2: the shape mcp c-trials actually hands back (verbatim field names). --------------
MCP = {
    "nct_id": "NCT02789917",
    "title": ("APixaban Versus PhenpRocoumon: Oral AntiCoagulation Plus Antiplatelet "
              "tHerapy in Patients With Acute Coronary Syndrome and Atrial Fibrillation"),
    "brief_title": "APixaban vs. PhenpRocoumon in Patients With ACS and AF: APPROACH-ACS-AF",
    "interventions": ["Dual Therapy", "Triple Therapy"],
    "conditions": ["Acute Coronary Syndrome", "Atrial Fibrillation"],
}

# --- A correct-negative, so a pass cannot be a pass-everything. -------------------------
NEGATIVE = {
    "protocolSection": {
        "identificationModule": {"briefTitle": "Dabigatran versus warfarin in AF (RE-LY)"},
        "armsInterventionsModule": {
            "armGroups": [
                {"label": "Dabigatran 150mg", "type": "EXPERIMENTAL",
                 "interventionNames": ["Drug: Dabigatran"]},
                {"label": "Warfarin", "type": "ACTIVE_COMPARATOR",
                 "interventionNames": ["Drug: Warfarin"]},
            ],
            "interventions": [
                {"name": "Dabigatran", "otherNames": ["Pradaxa"]},
                {"name": "Warfarin", "otherNames": []},
            ],
        },
    }
}

CASES = [
    ("Q1 raw-v2  NCT02789917", RAW, T.EXPERIMENTAL),
    ("Q2 mcp     NCT02789917", MCP, T.EXPERIMENTAL),
    ("negative   RE-LY(no apixaban)", NEGATIVE, T.NOT_ASSESSABLE),
]

fails = 0
for name, study, expected in CASES:
    role, ev = T.locate(study, SYNS)
    ok = role == expected
    fails += (not ok)
    print(f"[{'ok ' if ok else 'MISS'}] {name}")
    print(f"        got={role}  expected={expected}")
    print(f"        evidence: {ev}")

print()
print(f"{len(CASES) - fails}/{len(CASES)} known answers reproduced.")
sys.exit(1 if fails else 0)
