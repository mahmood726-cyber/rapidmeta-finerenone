#!/usr/bin/env python
"""Inventory every cardiology RapidMeta app: topic, data reality, trial count,
and the state of BOTH verdict surfaces (window.__verdict and the visible badge).

Written for the cardio upgrade program (2026-07-30). Read-only: touches no app file.

Usage:
    python scripts/cardio_inventory.py                 # -> outputs/cardio_inventory.json
    python scripts/cardio_inventory.py --all           # inventory every app, not just cardio
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict

# Only rewrap when run as a script. A module-level reassignment closes the
# importer's stdout and breaks pytest capture (rules/lessons.md).
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------
# Cardiology taxonomy. Keys are matched case-insensitively against the app
# filename stem AND the <title>. Each entry maps to a cardiology sub-domain.
# Deliberately drug-name-keyed (lessons.md: "Drug names, not class names").
# --------------------------------------------------------------------------
CARDIO_TAXONOMY: dict[str, list[str]] = {
    "Heart failure": [
        "HFREF", "HFPEF", "HFMREF", "HEART_FAILURE", "HEARTFAILURE", r"\bHF\b", "_HF_", "_HF$",
        "SACUBITRIL", "VALSARTAN", "ENTRESTO", "IVABRADINE", "VERICIGUAT", "OMECAMTIV",
        "DIGOXIN", "LEVOSIMENDAN", "MILRINONE", "TOLVAPTAN", "FINERENONE_HF",
        "SPIRONOLACTONE", "EPLERENONE", "TORSEMIDE", "FUROSEMIDE", "MAVACAMTEN",
        "ACORAMIDIS", "TAFAMIDIS", "VUTRISIRAN", "PATISIRAN", "CARDIOMYOPATHY",
        "AMYLOID", "CARDIAC_AMYLOIDOSIS", "OMECAMTIV", "ISTAROXIME", "DAPAGLIFLOZIN_HF",
        "EMPAGLIFLOZIN_HF", "SOTAGLIFLOZIN", "CARDIAC_RESYNC", "_ATTR_CM", "ATTR_CM",
        "ELAMIPRETIDE",
    ],
    "MI / ACS / IHD": [
        "_MI_", "_MI$", "STEMI", "NSTEMI", "_ACS_", "_ACS$", "MYOCARDIAL",
        "INFARCT", "ISCHEMIC_HEART", "ISCHAEMIC_HEART", "ANGINA", "CORONARY",
        "_CAD_", "_CAD$", "_PCI_", "_PCI$", "STENT", "THROMBOLY", "TENECTEPLASE",
        "ALTEPLASE_MI", "STREPTOKINASE", "RANOLAZINE", "TRIMETAZIDINE",
        "CARDIAC_ARREST", "CARDIOGENIC_SHOCK", "REVASCULAR", "CABG",
    ],
    "Atrial fibrillation / arrhythmia": [
        "_AF_", "_AF$", "ATRIAL_FIB", "ATRIALFIB", "AFIB", "FLUTTER",
        "AMIODARONE", "DRONEDARONE", "FLECAINIDE", "SOTALOL", "PROPAFENONE",
        "DOFETILIDE", "VERNAKALANT", "ABLATION", "ARRHYTHM",
        "VENTRICULAR_TACH", "_VT_", "SUPRAVENTRICULAR", "ETRIPAMIL",
    ],
    "Hypertension (systemic)": [
        "_HTN_", "_HTN$", "BLOOD_PRESSURE", "INTENSIVE_BP", "AMLODIPINE", "LISINOPRIL",
        "RAMIPRIL", "PERINDOPRIL", "ENALAPRIL", "LOSARTAN", "OLMESARTAN",
        "TELMISARTAN", "IRBESARTAN", "CANDESARTAN", "AZILSARTAN", "CHLORTHALIDONE",
        "HYDROCHLOROTHIAZIDE", "INDAPAMIDE", "NEBIVOLOL", "BISOPROLOL",
        "METOPROLOL", "CARVEDILOL", "ATENOLOL", "LABETALOL", "CLONIDINE",
        "ALISKIREN", "BAXDROSTAT", "LORUNDROSTAT", "APROCITENTAN", "ZILEBESIRAN",
        "RENAL_DENERV", "PREECLAMP", "HYPERTENSION", "HYPERTENSIVE",
    ],
    "Pulmonary hypertension / pulmonary vascular": [
        "PULMONARY_ARTERIAL", "_PAH_", "_PAH$", "PULMONARY_HYPERTENS",
        "MACITENTAN", "BOSENTAN", "AMBRISENTAN", "RIOCIGUAT", "SELEXIPAG",
        "TREPROSTINIL", "SOTATERCEPT", "TADALAFIL_PAH", "_CTEPH_", "CTEPH",
    ],
    "Lipids": [
        "STATIN", "ATORVASTATIN", "ROSUVASTATIN", "SIMVASTATIN", "PRAVASTATIN",
        "PITAVASTATIN", "LOVASTATIN", "FLUVASTATIN", "EZETIMIBE", "BEMPEDOIC",
        "EVOLOCUMAB", "ALIROCUMAB", "INCLISIRAN", "PCSK9", "LIPID", "DYSLIPID",
        "CHOLESTEROL", "_LDL_", "_LDL$", "HYPERCHOLESTER", "TRIGLYCERID",
        "FENOFIBRATE", "GEMFIBROZIL", "ICOSAPENT", "OMEGA_3", "OBICETRAPIB",
        "LOMITAPIDE", "MIPOMERSEN", "EVINACUMAB", "PELACARSEN", "OLPASIRAN",
        "LEPODISIRAN", "PLOZASIRAN", "VOLANESORSEN", "LIPOPROTEIN",
    ],
    "Anticoagulation / VTE": [
        "APIXABAN", "RIVAROXABAN", "EDOXABAN", "DABIGATRAN", "WARFARIN",
        "_DOAC_", "ANTICOAG", "HEPARIN", "ENOXAPARIN", "DALTEPARIN",
        "FONDAPARINUX", "ARGATROBAN", "BIVALIRUDIN", "_VTE_", "_VTE$",
        "VENOUS_THROMB", "_DVT_", "_DVT$", "PULMONARY_EMBOL", "_PE_",
        "ABELACIMAB", "MILVEXIAN", "ASUNDEXIAN", "ANDEXANET", "IDARUCIZUMAB",
        "THROMBOPROPH", "ATRIAL_THROMB",
    ],
    "Antiplatelet": [
        "ASPIRIN", "CLOPIDOGREL", "TICAGRELOR", "PRASUGREL", "CANGRELOR",
        "TIROFIBAN", "EPTIFIBATIDE", "ABCIXIMAB", "DIPYRIDAMOLE",
        "ANTIPLATELET", "CILOSTAZOL", "VORAPAXAR", "_DAPT_", "_DAPT$",
    ],
    "Valvular / structural": [
        "VALV", "AORTIC_STENOSIS", "_TAVR_", "_TAVI_", "MITRAL", "TRICUSPID",
        "MITRACLIP", "_TEER_", "TEER",
        "AORTIC_REGURG", "ENDOCARDITIS", "_PFO_", "PATENT_FORAMEN",
        "LEFT_ATRIAL_APPEND", "_LAAO_", "AORTIC_ANEURYSM", "AORTIC_DISSECT",
    ],
    "Cardiac devices / procedures": [
        "PACEMAKER", "_ICD_", "_ICD$", "DEFIBRILL", "_CRT_", "_CRT$",
        "RESYNCHRON", "_ECMO_", "_LVAD_", "VENTRICULAR_ASSIST",
        "HEART_TRANSPLANT", "_DCD_HT", "CARDIAC_REHAB",
        "CARDIAC_CONTRACTILITY", "INTRAVASCULAR_LITHOTRIPSY",
    ],
    "Pericardial / myocarditis": [
        "PERICARD", "MYOCARDITIS", "COLCHICINE_CVD", "COLCHICINE_PERICARD",
        "ANAKINRA_PERICARD", "RILONACEPT",
    ],
    "Stroke (cardioembolic/cerebrovascular)": [
        "STROKE", "_TIA_", "CEREBROVASC", "CAROTID", "INTRACEREBRAL_HEM",
        "TENECTEPLASE_STROKE", "THROMBECTOMY",
    ],
    "Peripheral arterial": [
        "PERIPHERAL_ARTER", "_PAD_", "_PAD$", "CLAUDICATION", "CRITICAL_LIMB",
    ],
    "CV prevention / cardiorenal CV outcomes (adjacent)": [
        "CARDIOVASCULAR", "_CVD_", "_CVD$", "_CV_OUTCOME", "CV_DEATH",
        "MACE", "CARDIOPROTECT", "CARDIOTOX", "PRIMARY_PREVENT",
        "_CVOT_", "CVOT", "MEDITERRANEAN_DIET_CV", "CARDIORENAL",
        "HYPERKALEMIA_K_BINDER", "FINERENONE",
    ],
}

# Non-cardiac apps that would otherwise trip a broad token. Checked FIRST.
# Kept deliberately minimal — an over-broad exclusion silently drops real cardio
# apps (an earlier `_PE(D|DIATRIC)` rule dropped PEDIATRIC_HF_DAPA_NMA).
# Every entry below was confirmed non-cardiac by reading the app's own <title>.
CARDIO_EXCLUDE = [
    r"^_TXA_NONCARDIAC",          # explicitly non-cardiac surgery
    r"^_POSTOP_AKI",              # renal outcome, cardiac-surgery setting only
    r"^_REMIMAZOLAM",             # anaesthetic hypotension, not cardiology
    r"^_HEMODIALYSIS_AV_ACCESS",  # dialysis access, not cardiac
    # --- substring false positives (the reason these are enumerated, not guessed)
    r"^_ELAFIBRANOR",             # "elAFIBranor" tripped the AFIB token
    r"^_MENACYW",                 # "volunTEER" tripped the TEER token
    r"^_HEAD_NECK_CRT",           # CRT here = chemoradiotherapy, not resynchronisation
    r"^_ANTIAMYLOID_AD",          # Alzheimer's anti-amyloid, not cardiac amyloidosis
    r"^_NETARSUDIL",              # OCULAR hypertension
    # --- right drug class, non-cardiac indication (title-confirmed)
    r"^_ATTR_PN",                 # ATTR polyneuropathy, not ATTR-CM
    r"^_PATISIRAN_POLYNEUROPATHY",
    r"^_TOLVAPTAN_ADPKD",         # ADPKD, not HF decongestion
    r"^_SOTAGLIFLOZIN_T1D",       # T1D glycaemia, not HF
    r"^_PYROXAMINE",              # codename stub; content is sotagliflozin T1D
    r"^_FENOFIBRATE_DR",          # diabetic retinopathy endpoint
    r"^_ELAMIPRETIDE",            # primary mitochondrial disease
    r"^_AGRYLIN_ET",              # essential thrombocythemia
    r"^_BURADIRAGAB",             # codename stub; content is rituximab AAV/IgG4-RD
]

# Apps whose filename does not describe their content. Confirmed by reading each
# app's own <title>; the mapped topic is what the app actually contains.
FILENAME_CONTENT_MISMATCH = {
    "TIRZEPATIDE_ARDS": "Andexanet alfa for FXa-inhibitor reversal",
    "ICAGEN": "Edoxaban TIMI-48 cancer-VTE",
    "PYROXAMINE": "Sotagliflozin in T1D",
    "BURADIRAGAB": "Rituximab in AAV / IgG4-RD",
}

# App classes where the intervention-MA recipe only partly applies.
DTA_PROGNOSTIC = {"DDIMER_PE_DTA", "HSCTN_NSTEMI_DTA", "PROGNOSTIC_HSTN_PAD"}


def _norm(stem: str) -> str:
    return "_" + stem.upper().replace("-", "_") + "_"


def classify(stem: str, title: str) -> tuple[str | None, str]:
    """Return (cardio_domain or None, matched_token)."""
    hay = _norm(stem)
    hay_title = " " + (title or "").upper() + " "
    for pat in CARDIO_EXCLUDE:
        if re.search(pat, hay):
            return None, ""
    for domain, tokens in CARDIO_TAXONOMY.items():
        for tok in tokens:
            pat = tok if tok.startswith(("\\", "_")) or tok.endswith(("$", "\\b")) else tok
            # Bare words: require a token boundary in the underscore-normalised stem.
            probe = pat if re.search(r"[\\^$]", pat) else pat
            try:
                if re.search(probe, hay):
                    return domain, tok
            except re.error:
                if probe in hay:
                    return domain, tok
    # Second pass: title-level cardiology words that the filename may not carry.
    for domain, tokens in CARDIO_TAXONOMY.items():
        for tok in tokens:
            plain = tok.strip("_$\\b^").replace("_", " ")
            if len(plain) >= 6 and plain in hay_title:
                return domain, "title:" + tok
    return None, ""


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------
RE_TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
RE_VERDICT = re.compile(r"window\.__verdict\s*=\s*(\{.*?\});", re.S)
RE_BADGE = re.compile(r'<div id="rapidmeta-integrity-badge"', re.I)
RE_BADGE_HEAD = re.compile(
    r'<div id="rapidmeta-integrity-badge".*?<strong[^>]*>(.*?)</strong>', re.S | re.I
)
RE_BADGE_TRIALS = re.compile(r"Trials:\s*(?:</?\w+[^>]*>\s*)*<strong>\s*([0-9]+)\s*</strong>", re.I)
RE_FABRISK = re.compile(r"Fabrication-risk score:\s*<strong>\s*([0-9.]+)\s*</strong>", re.I)
RE_REALDATA = re.compile(r"realData\s*:\s*\{")
RE_PMID = re.compile(r'pmid\s*:\s*"?(\d{5,9})"?')
RE_NCT_ANY = re.compile(r"\b(NCT\d{8})\b")


def depth1_keys(block: str) -> list[str]:
    """Enumerate the depth-1 property names of a JS object literal.

    Regex-for-`NCT\\d{8}:` is not enough: real ledgers use quoted keys
    (`"NCT01507831":`) and suffixed keys (`NCT01206062_SENIOR:`), and an
    NCT-shaped regex silently returns 0 for both — a false "EMPTY" verdict.
    """
    keys: list[str] = []
    if not block.startswith("{"):
        return keys
    i, n, depth, quote = 1, len(block), 1, None
    expect_key = True
    while i < n:
        c = block[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "\"'":
            if depth == 1 and expect_key:
                j = i + 1
                buf = []
                while j < n and block[j] != c:
                    if block[j] == "\\":
                        j += 2
                        continue
                    buf.append(block[j])
                    j += 1
                # Only a key if the next non-space char is ':'
                k = j + 1
                while k < n and block[k] in " \t\r\n":
                    k += 1
                if k < n and block[k] == ":":
                    keys.append("".join(buf))
                    expect_key = False
                    i = k + 1
                    continue
            quote = c
            i += 1
            continue
        if c in "{[":
            depth += 1
            i += 1
            continue
        if c in "}]":
            depth -= 1
            if depth == 0:
                break
            i += 1
            continue
        if c == "," and depth == 1:
            expect_key = True
            i += 1
            continue
        if depth == 1 and expect_key and (c.isalnum() or c in "_$"):
            j = i
            while j < n and (block[j].isalnum() or block[j] in "_$"):
                j += 1
            k = j
            while k < n and block[k] in " \t\r\n":
                k += 1
            if k < n and block[k] == ":":
                keys.append(block[i:j])
                expect_key = False
                i = k + 1
                continue
            i = j
            continue
        i += 1
    return keys


def balanced_slice(s: str, start: int, open_ch: str = "{", close_ch: str = "}") -> str:
    """Slice from the first open_ch at/after `start` to its balanced close.
    String-aware so braces inside JS strings don't unbalance the count."""
    i = s.find(open_ch, start)
    if i < 0:
        return ""
    depth, j, n = 0, i, len(s)
    quote = None
    while j < n:
        c = s[j]
        if quote:
            if c == "\\":
                j += 2
                continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return s[i : j + 1]
        j += 1
    return ""


def badge_block(s: str) -> str:
    m = RE_BADGE.search(s)
    if not m:
        return ""
    # Walk balanced <div>...</div> from the badge's opening tag.
    i = m.start()
    depth, j, n = 0, i, len(s)
    while j < n:
        if s.startswith("<div", j):
            depth += 1
            j += 4
            continue
        if s.startswith("</div>", j):
            depth -= 1
            j += 6
            if depth == 0:
                return s[i:j]
            continue
        j += 1
    return s[i : i + 6000]


def scan(path: str) -> dict:
    s = open(path, encoding="utf-8", errors="replace").read()
    stem = os.path.basename(path)
    rec: dict = {"file": stem, "bytes": len(s)}

    m = RE_TITLE.search(s)
    rec["title"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

    # ---- surface A: window.__verdict
    mv = RE_VERDICT.search(s)
    if mv:
        raw = mv.group(1)
        try:
            v = json.loads(raw)
        except Exception:
            v = None
        if v is None:
            rec["verdict_obj"] = {"_unparsed": raw[:400]}
            rec["verdict"] = None
            rec["verdict_trials"] = None
        else:
            rec["verdict_obj"] = v
            rec["verdict"] = v.get("verdict")
            counts = v.get("counts") or {}
            rec["verdict_trials"] = counts.get("n_trials_seen")
            rec["p0_total"] = v.get("p0_total")
            rec["verdict_reasons"] = v.get("reasons") or []
            rec["p1p2_total"] = sum(
                int(val or 0)
                for key, val in counts.items()
                if key.startswith(("P1_", "P2_"))
            )
    else:
        rec["verdict"] = "ABSENT"
        rec["verdict_trials"] = None
        rec["p1p2_total"] = None
        rec["verdict_reasons"] = []

    # ---- surface B: visible integrity badge
    blk = badge_block(s)
    rec["badge_present"] = bool(blk)
    if blk:
        mh = RE_BADGE_HEAD.search(blk)
        rec["badge_headline"] = re.sub(r"<[^>]+>", "", mh.group(1)).strip() if mh else ""
        mt = RE_BADGE_TRIALS.search(blk)
        rec["badge_trials"] = int(mt.group(1)) if mt else None
        mf = RE_FABRISK.search(blk)
        rec["fab_risk"] = float(mf.group(1)) if mf else None
        rec["badge_colour"] = (
            "green" if "#15803d" in blk[:400]
            else "amber" if ("#b45309" in blk[:400] or "#92400e" in blk[:400])
            else "red" if ("#7c2d12" in blk[:400] or "#991b1b" in blk[:400] or "#b91c1c" in blk[:400])
            else "other"
        )
        rec["badge_text"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", blk)).strip()[:1400]
    else:
        rec["badge_headline"] = ""
        rec["badge_trials"] = None
        rec["fab_risk"] = None
        rec["badge_colour"] = None
        rec["badge_text"] = ""

    # ---- data reality: the realData ledger
    md = RE_REALDATA.search(s)
    if md:
        block = balanced_slice(s, md.end() - 1)
        rec["realdata_bytes"] = len(block)
        keys = depth1_keys(block)
        rec["realdata_trials"] = len(set(keys))
        rec["realdata_keys"] = sorted(set(keys))
        rec["realdata_ncts"] = sorted(set(RE_NCT_ANY.findall(" ".join(keys))))
        rec["realdata_pmids"] = sorted(set(RE_PMID.findall(block)))
        # A key that is not NCT-shaped cannot be registry-concorded.
        rec["keys_without_nct"] = sorted(
            k for k in set(keys) if not RE_NCT_ANY.search(k)
        )
        rec["has_real_data"] = rec["realdata_trials"] > 0
    else:
        rec["realdata_bytes"] = 0
        rec["realdata_trials"] = 0
        rec["realdata_keys"] = []
        rec["realdata_ncts"] = []
        rec["realdata_pmids"] = []
        rec["keys_without_nct"] = []
        rec["has_real_data"] = False

    # ---- agreement between the two surfaces
    bt, vt, rt = rec["badge_trials"], rec["verdict_trials"], rec["realdata_trials"]
    counts_seen = [x for x in (bt, vt, rt) if isinstance(x, int)]
    rec["counts_agree"] = (len(set(counts_seen)) <= 1) if counts_seen else None

    head = (rec["badge_headline"] or "").upper()
    badge_green = rec["badge_colour"] == "green" or "PASSED" in head
    rec["badge_claims_pass"] = badge_green
    # False-green: a green/PASSED badge over a verdict that is not clean.
    verdict_clean = (rec.get("p0_total") == 0) and (rec.get("p1p2_total") == 0)
    rec["false_green"] = bool(
        badge_green and rec["verdict"] not in ("ABSENT", None) and not verdict_clean
    )
    rec["badge_verdict_mismatch"] = bool(
        badge_green and rec["verdict"] in ("UNSTABLE", "FAIL", "UNCERTAIN", "BLOCKED")
    )
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="inventory every app, not just cardio")
    ap.add_argument("--out", default=os.path.join(REPO, "outputs", "cardio_inventory.json"))
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(REPO) if f.endswith("_REVIEW.html"))
    rows, skipped = [], 0
    for fn in files:
        stem = re.sub(r"(_AUTO)?(_FULL)?_REVIEW\.html$", "", fn)
        path = os.path.join(REPO, fn)
        # Title is needed for classification, so read lazily-but-once.
        try:
            head = open(path, encoding="utf-8", errors="replace").read(4000)
        except OSError:
            continue
        mt = RE_TITLE.search(head)
        title = mt.group(1) if mt else ""
        domain, tok = classify(stem, title)
        if domain is None and not args.all:
            skipped += 1
            continue
        rec = scan(path)
        rec["stem"] = stem
        rec["domain"] = domain
        rec["match_token"] = tok
        rec["filename_content_mismatch"] = FILENAME_CONTENT_MISMATCH.get(stem)
        rec["app_class"] = "DTA/prognostic" if stem in DTA_PROGNOSTIC else "intervention-MA"
        # A "…- opening the full RapidMeta…" title means a redirect stub, not an app.
        rec["is_redirect_stub"] = "opening the full RapidMeta" in rec["title"]
        rows.append(rec)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"generated_for": "cardio upgrade program", "n": len(rows),
                   "n_skipped_noncardio": skipped, "apps": rows}, fh, indent=1)

    by_dom: dict[str, list] = defaultdict(list)
    for r in rows:
        by_dom[r["domain"] or "(all-mode: non-cardio)"].append(r)
    print(f"scanned {len(files)} review files; matched {len(rows)}; skipped {skipped}")
    for dom in sorted(by_dom):
        rs = by_dom[dom]
        withdata = sum(1 for r in rs if r["has_real_data"])
        fg = sum(1 for r in rs if r["false_green"])
        dis = sum(1 for r in rs if r["counts_agree"] is False)
        print(f"  {dom:<52} files={len(rs):>4}  with-data={withdata:>4}  false-green={fg:>4}  count-disagree={dis:>3}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
