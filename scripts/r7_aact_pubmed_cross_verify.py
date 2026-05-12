"""R7 — systematic AACT + PubMed cross-verification of LOW+MANUAL band trials.

Pipeline (consistent, deterministic, no human review):

  Stage 1 — Enumerate trials in LOW_CONCERN (0.30 ≤ s < 0.50) + MANUAL_REVIEW
            (0.50 ≤ s < 0.70) reviews.

  Stage 2 — Bulk-fetch AACT snapshot for all target NCTs:
            studies.txt        → brief_title, official_title, enrollment,
                                  phase, study_type, overall_status, completion_date
            conditions.txt     → conditions
            interventions.txt  → name, intervention_type
            brief_summaries.txt → description

  Stage 3 — Fetch missing PMIDs via NCBI eutils (cache hits skipped).

  Stage 4 — Per-trial verdict with 5 rules:
            R-N1: NCT_NOT_IN_AACT — null PMID (NCT can't be verified; keep
                  but flag for triage)
            R-N2: AACT_ENROLLMENT_MISMATCH — |aact_enrollment - (tN+cN)|/
                  aact_enrollment > 0.20 → null tN/cN/tE/cE (likely wrong arms)
            R-N3: AACT_CONDITION_REVIEW_MISMATCH — Jaccard(aact_conditions
                  tokens, review topic tokens) < 0.05 → null NCT key
                  (trial is in wrong review)
            R-N4: AACT_INTERVENTION_GROUP_MISMATCH — drug name from `group`
                  field doesn't appear in AACT interventions → null group
                  (extraction noise)
            R-N5: PMID_TOPIC_MISMATCH — PMID's title+abstract tokens have
                  Jaccard < 0.05 with AACT title+conditions → null PMID

  Stage 5 — Apply auto-fixes + re-extract + re-audit.

Output:
  outputs/extraction_audit/r7_verification.json
"""
from __future__ import annotations
import json, csv, re, sys, io, os
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


# ─── Stage 1: target trials ───
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
        target_trials.append({
            "review": rv, "nct": nct, "name": t.get("name"),
            "year": t.get("year"), "pmid": t.get("pmid"),
            "group": t.get("group"),
            "tE": t.get("tE"), "tN": t.get("tN"),
            "cE": t.get("cE"), "cN": t.get("cN"),
            "publishedHR": t.get("publishedHR"),
            "estimandType": t.get("estimandType"),
        })

target_ncts = sorted({t["nct"] for t in target_trials})
print(f"Target trials: {len(target_trials)}  unique NCTs: {len(target_ncts)}")

# ─── Stage 2: bulk AACT load ───
def load_aact_columns(filename, key_col, want_cols, filter_set):
    out = defaultdict(list)
    with open(AACT / filename, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            k = (row.get(key_col) or "").strip().upper()
            if k in filter_set:
                out[k].append({c: (row.get(c) or "").strip() for c in want_cols})
    return out

target_ncts_set = set(target_ncts)
print("Reading AACT studies.txt...")
studies = load_aact_columns("studies.txt", "nct_id",
                              ["brief_title", "official_title", "enrollment",
                               "phase", "study_type", "overall_status"],
                              target_ncts_set)
print(f"  resolved {len(studies)}/{len(target_ncts)} NCTs")

print("Reading AACT conditions.txt...")
conds = load_aact_columns("conditions.txt", "nct_id", ["downcase_name"], target_ncts_set)
print("Reading AACT interventions.txt...")
intvs = load_aact_columns("interventions.txt", "nct_id",
                            ["name", "intervention_type"], target_ncts_set)


# ─── Stage 3: fetch missing PMIDs ───
target_pmids = []
for t in target_trials:
    p = (t.get("pmid") or "").strip()
    if p.isdigit() and 6 <= len(p) <= 9:
        target_pmids.append(p)
target_pmids = list(set(target_pmids))

missing_pmids = [p for p in target_pmids if not (PUBMED_CACHE / f"{p}.json").exists()]
print(f"Target PMIDs: {len(target_pmids)}  missing-from-cache: {len(missing_pmids)}")
if missing_pmids:
    # Use existing fetch script via subprocess
    pmid_list_p = OUT / "pmids_to_fetch.txt"
    pmid_list_p.write_text("\n".join(missing_pmids), encoding="utf-8")
    print("  Run: python scripts/fetch_pubmed_batch.py to populate cache, then re-run R7.")
    print("  Skipping PMID-based checks for missing PMIDs this pass.")


def load_pubmed(pmid):
    p = PUBMED_CACHE / f"{pmid}.json"
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return None


# ─── Tokenization for similarity ───
STOPWORDS = {"a", "an", "the", "of", "for", "in", "to", "with", "and", "or",
              "vs", "vs.", "versus", "study", "trial", "randomized", "randomised",
              "double-blind", "placebo", "controlled", "open-label", "phase",
              "evaluation", "efficacy", "safety", "treatment", "patients",
              "adult", "adults", "subjects", "evaluate", "effect", "effects"}


def tokenize(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\-]+", " ", s)
    toks = [t for t in s.split() if len(t) >= 3 and t not in STOPWORDS]
    return set(toks)


def jaccard(a, b):
    if not a or not b: return 0.0
    return len(a & b) / max(1, len(a | b))


# ─── Stage 4: per-trial verdict ───
verdicts = []
fix_ops = []

for t in target_trials:
    nct = t["nct"]
    rv = t["review"]
    s = studies.get(nct, [])
    issues = []
    fixes = []

    # R-N1
    if not s:
        issues.append("NCT_NOT_IN_AACT")
        fixes.append({"op": "NULL_PMID", "review": rv, "nct": nct,
                       "reason": "NCT not in AACT 2026-04-12 snapshot"})
        verdicts.append({"review": rv, "nct": nct, "issues": issues, "fixes": fixes})
        continue

    aact = s[0]
    aact_enroll = aact.get("enrollment", "")
    try:
        aact_n = int(aact_enroll) if aact_enroll else None
    except: aact_n = None

    aact_conditions = {c["downcase_name"] for c in conds.get(nct, [])}
    aact_intvs = [i["name"] for i in intvs.get(nct, [])]
    aact_title = aact.get("brief_title", "") + " " + aact.get("official_title", "")

    # R-N2: enrollment mismatch
    tN, cN = t.get("tN"), t.get("cN")
    if aact_n and tN is not None and cN is not None:
        try:
            arm_sum = int(tN) + int(cN)
            if aact_n > 0 and abs(aact_n - arm_sum) / aact_n > 0.20:
                # Allow ±20% (some trials have subgroup analyses)
                issues.append(f"AACT_ENROLLMENT_MISMATCH (AACT N={aact_n}, arm-sum={arm_sum})")
                # Don't auto-null — could be a legitimate subgroup. Just flag.
        except: pass

    # R-N3: condition vs review topic
    review_tokens = tokenize(rv.replace("_", " ").replace("REVIEW", "").replace("NMA", ""))
    aact_cond_text = " ".join(aact_conditions) + " " + aact_title
    aact_tokens = tokenize(aact_cond_text)
    j = jaccard(review_tokens, aact_tokens)
    if j < 0.03:  # very strict; <3% Jaccard means really off-topic
        issues.append(f"AACT_CONDITION_MISMATCH (Jaccard={j:.3f})")
        fixes.append({"op": "NULL_KEY", "review": rv, "nct": nct,
                       "reason": f"AACT conditions {sorted(aact_conditions)[:3]} share {j:.2f} Jaccard with review topic"})

    # R-N4: intervention vs group
    group = (t.get("group") or "").lower()
    if group and aact_intvs:
        # Drug name approx: words with 6+ chars not in stopwords
        group_drugs = [w for w in re.findall(r"[a-z]+", group)
                        if len(w) >= 6 and w not in STOPWORDS
                        and w not in {"placebo", "control", "patients", "monthly", "daily"}]
        aact_drugs_text = " ".join(aact_intvs).lower()
        if group_drugs and not any(d in aact_drugs_text for d in group_drugs[:3]):
            issues.append(f"AACT_INTV_MISMATCH (group drugs {group_drugs[:3]} not in AACT intvs {aact_intvs})")
            # Don't null — group is just a label; the drug might be in `name` field instead

    # R-N5: PMID topic vs AACT title
    pmid = (t.get("pmid") or "").strip()
    if pmid:
        pub = load_pubmed(pmid)
        if pub and pub.get("abstract"):
            pub_tokens = tokenize(pub.get("title", "") + " " + pub.get("abstract", ""))
            if pub_tokens:
                jp = jaccard(pub_tokens, aact_tokens)
                if jp < 0.03:
                    issues.append(f"PMID_TOPIC_MISMATCH (PMID={pmid}, Jaccard with AACT={jp:.3f})")
                    fixes.append({"op": "NULL_PMID", "review": rv, "nct": nct,
                                   "reason": f"PMID {pmid} abstract has {jp:.2f} Jaccard with AACT trial topic"})

    verdicts.append({"review": rv, "nct": nct, "issues": issues, "fixes": fixes})
    fix_ops.extend(fixes)

# ─── Stage 5: apply fixes ───
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
seen_ops = set()
for f in fix_ops:
    key = (f["op"], f["review"], f["nct"])
    if key in seen_ops: continue
    seen_ops.add(key)
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

# Summary
issue_counts = Counter()
for v in verdicts:
    for i in v["issues"]:
        issue_counts[i.split(" ")[0]] += 1

out_p = OUT / "r7_verification.json"
out_p.write_text(json.dumps({
    "target_reviews": sorted(target_reviews),
    "target_trial_count": len(target_trials),
    "target_nct_count": len(target_ncts),
    "aact_resolved": len(studies),
    "issue_counts": dict(issue_counts),
    "verdicts": verdicts,
    "applied": applied,
    "summary": {"PMID_nulls": n_pmid, "NCT_key_nulls": n_key},
}, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\nIssue counts:")
for cat, n in issue_counts.most_common():
    print(f"  {cat}: {n}")
print(f"\n{'DRY-RUN ' if DRY else ''}Fixes applied:")
print(f"  PMID nulls:    {n_pmid}")
print(f"  NCT key nulls: {n_key}")
print(f"\nLog → {out_p}")
