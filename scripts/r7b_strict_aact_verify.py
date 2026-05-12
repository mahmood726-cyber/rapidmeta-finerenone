"""R7b — Strict, consistent AACT cross-verification.

Three rules — each fires only on UNAMBIGUOUS contradictions where no
acronym-expansion is needed:

R-S1: NCT_NOT_IN_AACT_SNAPSHOT
  The NCT doesn't exist at all in AACT 2026-04-12. Single signal but
  deterministic — null PMID (preserve trial row; flag for re-extract).

R-S2: AACT_INTERVENTION_HARD_MISMATCH
  The drug name from extracted `group` field doesn't appear in ANY AACT
  intervention name (case-insensitive substring), AND AACT lists at least
  3 interventions (so it's not an underspecified registration).
  Action: null PMID + group (preserve NCT but mark provenance broken).

R-S3: TRIPLE_SIGNAL_WRONG_NCT
  All three must fire:
    a) Drug from group not in any AACT intervention (R-S2)
    b) Enrollment is >2× off between AACT and (tN+cN)
    c) No drug-name word (≥6 chars) from group appears in AACT brief_title
  Action: NULL_KEY — the NCT genuinely belongs to a different trial.

R-S4: PMID_AACT_TOPIC_MISMATCH
  Both:
    a) PMID title+abstract contains no drug-name word from AACT interventions
    b) PMID title+abstract contains none of AACT's condition tokens
  Action: NULL_PMID.

This is intentionally more conservative than R7a — fewer false positives.
"""
from __future__ import annotations
import json, csv, re, sys, io
from pathlib import Path
from collections import defaultdict, Counter

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "outputs" / "extraction_audit"
DATA = OUT / "data"
PUBMED_CACHE = OUT / "pubmed_cache"
AACT = Path("D:/AACT-storage/AACT/2026-04-12")
DRY = "--dry-run" in sys.argv

scores = json.loads((OUT / "fabrication_risk_scores.json").read_text(encoding="utf-8"))
target_reviews = {r["review"] for r in scores
                   if 0.30 <= r["score"] < 0.70 and not r["already_quarantined"]}
print(f"Target reviews: {len(target_reviews)}")

target_trials = []
for json_p in sorted(DATA.glob("*.json")):
    if json_p.name.startswith("_"): continue
    rv = json_p.stem
    if rv not in target_reviews: continue
    try: d = json.loads(json_p.read_text(encoding="utf-8"))
    except: continue
    rd = d.get("realData") or {}
    if not isinstance(rd, dict): continue
    for nct, t in rd.items():
        if not isinstance(t, dict): continue
        if nct.startswith("NULLED:"): continue
        if not re.match(r"^NCT\d{8}$", nct): continue
        target_trials.append({"review": rv, "nct": nct, **t})

target_ncts = sorted({t["nct"] for t in target_trials})
print(f"Target trials: {len(target_trials)}  unique NCTs: {len(target_ncts)}")


def load_aact(filename, key_col, want_cols, filter_set):
    out = defaultdict(list)
    with open(AACT / filename, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            k = (row.get(key_col) or "").strip().upper()
            if k in filter_set:
                out[k].append({c: (row.get(c) or "").strip() for c in want_cols})
    return out


target_set = set(target_ncts)
print("Loading AACT…")
studies = load_aact("studies.txt", "nct_id",
                     ["brief_title", "official_title", "enrollment"], target_set)
conds = load_aact("conditions.txt", "nct_id", ["downcase_name"], target_set)
intvs = load_aact("interventions.txt", "nct_id", ["name"], target_set)
print(f"  AACT resolved: {len(studies)}/{len(target_ncts)}")

STOPWORDS = {"a","an","the","of","for","in","to","with","and","or","vs","vs.",
              "versus","study","trial","randomized","randomised","double-blind",
              "placebo","controlled","open-label","phase","evaluation","efficacy",
              "safety","treatment","patients","adult","adults","subjects",
              "evaluate","effect","effects","drug","new","placebo-controlled",
              "extension","monthly","daily","weekly","oral","intravenous","subcutaneous",
              # Geographic / cohort descriptors
              "french","brazilian","italian","spanish","european","asian","american",
              "japanese","chinese","african","british","canadian","german",
              "cohort","registry","real-world","singapore","argentine","russian",
              "nordic","scandinavian","atlantic","pacific","mediterranean",
              # Study-design descriptors
              "frontline","resistant","refractory","recurrent","relapsed","advanced",
              "metastatic","localized","early","late","newly","established",
              "proceed","followup","follow","baseline","week","year","month",
              "primary","secondary","tertiary","cluster","crossover",
              # Method words
              "analysis","analyses","results","outcome","outcomes",
              "sensitivity","subgroup","exploratory","posthoc"}


def drug_words(group: str) -> list[str]:
    """Words ≥6 chars from group field, excluding common dose/route terms."""
    if not group: return []
    out = []
    for w in re.findall(r"[a-z]+", group.lower()):
        if len(w) >= 6 and w not in STOPWORDS:
            out.append(w)
    return out


def load_pubmed(pmid):
    p = PUBMED_CACHE / f"{pmid}.json"
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return None


# Per-trial verdicts
fixes = []
issue_counts = Counter()
for t in target_trials:
    nct = t["nct"]; rv = t["review"]
    s = studies.get(nct, [])
    if not s:
        issue_counts["NCT_NOT_IN_AACT_SNAPSHOT"] += 1
        fixes.append({"rule": "R-S1", "op": "NULL_PMID", "review": rv, "nct": nct,
                       "reason": "NCT not in AACT 2026-04-12 snapshot"})
        continue
    aact = s[0]
    aact_title = (aact.get("brief_title", "") + " " + aact.get("official_title", "")).lower()
    aact_intvs = [i["name"] for i in intvs.get(nct, [])]
    aact_intvs_text = " ".join(aact_intvs).lower()
    aact_conditions = {c["downcase_name"] for c in conds.get(nct, [])}
    try: aact_n = int(aact.get("enrollment", "") or 0)
    except: aact_n = 0

    # R-S2 check
    gws = drug_words(t.get("group") or "")
    intv_hard_mismatch = False
    if gws and len(aact_intvs) >= 3:
        # Hard mismatch = NONE of top-3 drug words appear in AACT intvs
        if not any(d in aact_intvs_text for d in gws[:3]):
            intv_hard_mismatch = True
            issue_counts["AACT_INTV_HARD_MISMATCH"] += 1

    # R-S3 check (triple)
    enroll_2x_off = False
    if aact_n > 0:
        try:
            arm_sum = int(t.get("tN") or 0) + int(t.get("cN") or 0)
            if arm_sum > 0 and (arm_sum / aact_n > 2 or aact_n / max(arm_sum, 1) > 2):
                enroll_2x_off = True
        except: pass

    drug_in_title = any(d in aact_title for d in gws[:3]) if gws else False

    if intv_hard_mismatch and enroll_2x_off and not drug_in_title:
        issue_counts["TRIPLE_SIGNAL_WRONG_NCT"] += 1
        fixes.append({"rule": "R-S3", "op": "NULL_KEY", "review": rv, "nct": nct,
                       "reason": f"intv+enroll(2x)+title mismatch — drug {gws[:3]} not in AACT title nor any of {len(aact_intvs)} interventions; AACT N={aact_n} vs arm-sum={t.get('tN')}+{t.get('cN')}"})
        continue  # NULL_KEY supersedes lesser actions

    if intv_hard_mismatch:
        fixes.append({"rule": "R-S2", "op": "NULL_PMID", "review": rv, "nct": nct,
                       "reason": f"drug {gws[:3]} not in AACT interventions {aact_intvs[:3]}"})

    # R-S4: PMID topic vs AACT (drug-name + condition overlap)
    pmid = (t.get("pmid") or "").strip()
    if pmid:
        pub = load_pubmed(pmid)
        if pub and pub.get("abstract"):
            text = (pub.get("title", "") + " " + pub.get("abstract", "")).lower()
            # AACT-derived "anchors"
            aact_drugs = [re.sub(r"\W+", " ", n.lower()).strip() for n in aact_intvs]
            aact_drug_words = set()
            for x in aact_drugs:
                for w in x.split():
                    if len(w) >= 6 and w not in STOPWORDS:
                        aact_drug_words.add(w)
            cond_words = set()
            for c in aact_conditions:
                for w in re.findall(r"[a-z]+", c.lower()):
                    if len(w) >= 5 and w not in STOPWORDS:
                        cond_words.add(w)
            drug_overlap = any(d in text for d in aact_drug_words)
            cond_overlap = any(c in text for c in cond_words)
            if not drug_overlap and not cond_overlap:
                issue_counts["PMID_AACT_TOPIC_MISMATCH"] += 1
                fixes.append({"rule": "R-S4", "op": "NULL_PMID", "review": rv, "nct": nct,
                               "reason": f"PMID {pmid} contains no AACT drug-word ({sorted(aact_drug_words)[:3]}) or condition-word ({sorted(cond_words)[:3]})"})


# Apply
def find_block(txt, nct):
    key_pat = re.compile(r'(["\'])' + re.escape(nct) + r'\1\s*:\s*\{')
    m = key_pat.search(txt)
    if not m: return None
    start = m.end(); depth = 1; i = start; in_str = None
    while i < len(txt) and depth > 0:
        ch = txt[i]
        if in_str:
            if ch == "\\": i += 2; continue
            if ch == in_str: in_str = None
        else:
            if ch in ('"', "'"): in_str = ch
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: return (m.start(), i+1, start, i)
        i += 1
    return None


def null_field_in_block(txt, body_start, body_end, field):
    body = txt[body_start:body_end]
    new_body, n = re.subn(
        r'((["\']?)' + re.escape(field) + r'\2\s*:\s*)(?:["\'][^"\']*["\']|[0-9.eE+-]+|true|false)(?=\s*[,}])',
        r'\1null', body, flags=re.IGNORECASE)
    if n == 0: return txt, False
    return txt[:body_start] + new_body + txt[body_end:], True


def null_key(txt, nct):
    nulled = f"NULLED:{nct}"
    if nulled in txt: return txt, 0
    pat = re.compile(r'(["\'])(' + re.escape(nct) + r')(\1)(\s*:)')
    new_txt, n = pat.subn(
        lambda m: f'{m.group(1)}NULLED:{m.group(2)}{m.group(3)}{m.group(4)}', txt)
    return new_txt, n


applied = []
n_pmid = n_key = 0
seen = set()
for f in fixes:
    key = (f["op"], f["review"], f["nct"])
    if key in seen: continue
    seen.add(key)
    rv, nct, op = f["review"], f["nct"], f["op"]
    html_path = HERE / f"{rv}.html"
    if not html_path.exists():
        applied.append({**f, "status": "FILE_MISSING"})
        continue
    txt = html_path.read_text(encoding="utf-8")
    if op == "NULL_PMID":
        block = find_block(txt, nct)
        if not block:
            applied.append({**f, "status": "BLOCK_NOT_FOUND"})
            continue
        _, _, bs, be = block
        new_txt, ok = null_field_in_block(txt, bs, be, "pmid")
        if ok:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            applied.append({**f, "status": "NULLED_PMID"})
            n_pmid += 1
        else:
            applied.append({**f, "status": "PMID_ALREADY_NULL"})
    elif op == "NULL_KEY":
        new_txt, n = null_key(txt, nct)
        if n > 0:
            if not DRY: html_path.write_text(new_txt, encoding="utf-8")
            applied.append({**f, "status": "NULLED_KEY"})
            n_key += 1
        elif f"NULLED:{nct}" in txt:
            applied.append({**f, "status": "ALREADY_NULLED"})

out_p = OUT / "r7b_verification.json"
out_p.write_text(json.dumps({
    "issue_counts": dict(issue_counts),
    "fixes_proposed": len(fixes),
    "applied": applied,
    "summary": {"PMID_nulls": n_pmid, "NCT_key_nulls": n_key},
}, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\nIssue counts:")
for k, v in issue_counts.most_common():
    print(f"  {k}: {v}")
print(f"\n{'DRY-RUN ' if DRY else ''}Fixes applied:")
print(f"  PMID nulls (R-S1+S2+S4):  {n_pmid}")
print(f"  NCT key nulls (R-S3):     {n_key}")
print(f"\nLog → {out_p}")
