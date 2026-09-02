"""PHASE 3 - measure, before ingesting anything.

For each selected comparator: their k, the trials we already hold, the trials we do NOT
hold NAMED, and the trials excluded by a declared scope reason with that reason quoted.

Nothing here ingests. The output is a report.

Three provenance grades appear on every field:
  MEASURED  - read from structured XML, or from a PubMed databank record
  INFERRED  - lifted from prose inside a structurally-located section, with the
              matched sentence quoted so it can be checked
  CLAIMED   - carried through from an upstream artefact without re-measurement

The join key problem is the whole difficulty: their included studies carry PMIDs, our
holdings carry NCT ids. A study we cannot resolve to a common key is reported
UNRESOLVABLE, never as "we do not hold it".
"""
import argparse
import csv
import json
import io
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_included as X  # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

METHODS_SEC_RE = re.compile(r"method|search strateg|data source|eligib|study selection|literature", re.I)
MONTHS = (r"January|February|March|April|May|June|July|August|September|October|November|December|"
          r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec")
SEARCH_VERB_RE = re.compile(r"search|databases were|we queried|inception", re.I)
DATE_RE = re.compile(r"(?:(%s)[a-z]*\.?\s+)?((?:19|20)\d{2})" % MONTHS, re.I)
CLOSE_CUE_RE = re.compile(r"\b(?:up to|until|through|thru|to|as of|on)\b", re.I)
NUMWORD = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
           "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
           "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
           "twenty": 20}
# `\b` fires INSIDE a hyphenated number-word: "Sixty-four trials were included" matched
# "four" and reported k=4 for a review of 64. A hyphen or a word char before the token means
# we are inside a compound, not at its start.
DECLARED_K_RE = re.compile(
    r"(?<![-‐-―\w])(\d{1,3}|%s)\s+(?:eligible\s+|unique\s+|relevant\s+)?"
    r"(?:randomi[sz]ed[- ]?(?:controlled\s+)?)?(?:clinical\s+)?"
    r"(trials?|studies|RCTs?|articles)\b[^.]{0,60}?\b(?:were\s+|was\s+)?(?:includ|eligible|met)" % "|".join(NUMWORD),
    re.I,
)
DESIGN_TOKENS = [
    ("randomised_controlled_trial", re.compile(r"\brandomi[sz]ed\b|\bRCT\b|\bcross-?over trial\b", re.I)),
    ("cluster_randomised", re.compile(r"cluster[- ]randomi[sz]ed", re.I)),
    ("cohort", re.compile(r"\bcohort\b", re.I)),
    ("case_control", re.compile(r"case[- ]control", re.I)),
    ("observational", re.compile(r"\bobservational\b|\bregistry\b|\bretrospective\b|\bprospective observational\b", re.I)),
    ("single_arm", re.compile(r"single[- ]arm|non-?randomi[sz]ed", re.I)),
]


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.;])\s+", text) if s.strip()]


def section_text(root, title_re):
    out = []
    for sec in root.iter("sec"):
        t = X.text_of(sec.find("title"))
        if t and title_re.search(t):
            out.append(X.text_of(sec))
    return " ".join(out)


def abstract_text(root):
    ab = root.find(".//article-meta//abstract")
    return X.text_of(ab)


def infer_search_close(root):
    """INFERRED. Bounded to the Methods section, quoted so it can be checked."""
    body = section_text(root, METHODS_SEC_RE)
    if not body:
        return {"value": None, "status": "NOT_FOUND", "quote": None,
                "why": "no section whose title matches the methods/search family"}
    best = None
    for s in sentences(body):
        if not SEARCH_VERB_RE.search(s):
            continue
        for m in DATE_RE.finditer(s):
            pre = s[max(0, m.start() - 40):m.start()]
            if not CLOSE_CUE_RE.search(pre):
                continue
            year = int(m.group(2))
            if not 1990 <= year <= 2027:
                continue
            val = ("%s %d" % (m.group(1), year)) if m.group(1) else str(year)
            if best is None or year >= best[1]:
                best = (val, year, s[:300])
    if best is None:
        return {"value": None, "status": "NOT_FOUND", "quote": None,
                "why": "methods section found, but no search sentence with a close-date cue"}
    return {"value": best[0], "status": "INFERRED", "quote": best[2], "why": None}


def infer_declared_k(root):
    """INFERRED, LOW CONFIDENCE. A review's abstract states subgroup counts in the same
    grammar as its total ("four trials with metformin"), so any single match may be a
    subgroup. Take the LARGEST candidate in the abstract, keep every candidate, and quote
    the winning sentence. This is a cross-check on k_extracted, never a substitute for it.
    """
    for where, txt in (("abstract", abstract_text(root)),
                       ("results_section", section_text(root, re.compile(r"^result", re.I)))):
        if not txt:
            continue
        cands = []
        for s in sentences(txt):
            for m in DECLARED_K_RE.finditer(s):
                tok = m.group(1).lower()
                n = NUMWORD.get(tok)
                if n is None:
                    try:
                        n = int(tok)
                    except ValueError:
                        continue
                if 1 <= n <= 500:
                    cands.append((n, s[:300]))
        if cands:
            n, s = max(cands, key=lambda c: c[0])
            return {"value": n, "status": "INFERRED_LOW_CONFIDENCE", "where": where,
                    "quote": s, "all_candidates": sorted({c[0] for c in cands})}
    return {"value": None, "status": "NOT_FOUND", "where": None, "quote": None,
            "all_candidates": []}


def row_text_for_rids(root):
    """rid -> the table row text it was cited from. Structural: the row is an ancestor."""
    out = {}
    for tw in root.iter("table-wrap"):
        cap = " ".join([X.text_of(tw.find("label")), X.text_of(tw.find("caption"))]).strip()
        if not X.TABLE_CAPTION_RE.search(cap):
            continue
        for tr in tw.iter("tr"):
            rids = X.bibr_rids(tr)
            if not rids:
                continue
            txt = X.text_of(tr)
            for rid in rids:
                out.setdefault(rid, txt[:400])
    return out


def classify_design(row):
    """INFERRED, from the structurally-located characteristics row. Reason is quoted."""
    if not row:
        return {"value": None, "status": "NOT_FOUND", "quote": None}
    hits = [name for name, rx in DESIGN_TOKENS if rx.search(row)]
    if not hits:
        return {"value": None, "status": "NOT_FOUND", "quote": row[:200]}
    # A row saying "randomised" wins over a co-occurring "prospective".
    for pref in ("cluster_randomised", "randomised_controlled_trial"):
        if pref in hits:
            return {"value": pref, "status": "INFERRED", "quote": row[:200]}
    return {"value": hits[0], "status": "INFERRED", "quote": row[:200]}


def eget(endpoint, params, retries=4):
    params = dict(params)
    params.setdefault("tool", "rapidmeta-comparator-seed")
    params.setdefault("email", "mahmood726@gmail.com")
    url = "%s/%s.fcgi?%s" % (EUTILS, endpoint, urllib.parse.urlencode(params))
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as fh:
                return fh.read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (i + 1))
    raise RuntimeError("%s failed: %s" % (endpoint, last))


def resolve_pmids_to_nct(pmids, cache_path):
    """MEASURED: PubMed DataBank ClinicalTrials.gov accession numbers."""
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            cache = json.load(fh)
    need = sorted({p for p in pmids if p and p not in cache})
    for start in range(0, len(need), 150):
        chunk = need[start:start + 150]
        raw = eget("efetch", {"db": "pubmed", "id": ",".join(chunk), "retmode": "xml"})
        root = X.strip_ns(ET.ElementTree(ET.fromstring(raw))).getroot()
        seen = set()
        for art in root.iter("PubmedArticle"):
            pm = art.find(".//MedlineCitation/PMID")
            if pm is None:
                continue
            pid = X.text_of(pm)
            seen.add(pid)
            ncts = []
            for db in art.iter("DataBank"):
                name = X.text_of(db.find("DataBankName"))
                if name and name.lower().startswith("clinicaltrials"):
                    for acc in db.iter("AccessionNumber"):
                        v = X.text_of(acc)
                        if X.NCT_RE.fullmatch(v or ""):
                            ncts.append(v)
            cache[pid] = sorted(set(ncts))
        # A PMID PubMed did not return is a distinct state from one with no NCT.
        for p in chunk:
            if p not in seen:
                cache[p] = None
        print("  pubmed resolve %d/%d" % (min(start + 150, len(need)), len(need)))
        time.sleep(0.4)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=0, sort_keys=True)
    return cache


def load_holdings(repo):
    """Our trial holdings, from every source, with the disagreement reported not hidden."""
    src = {}
    p = os.path.join(repo, "outputs", "nct_to_apps.json")
    with open(p, encoding="utf-8") as fh:
        n2a = json.load(fh)
    # 16 NCTs map to >20 apps each; that is clone contamination, not evidence of holding.
    contaminated = {k for k, v in n2a.items() if len(v) > 20}
    src["nct_to_apps"] = set(n2a) - contaminated
    p = os.path.join(repo, "outputs", "corpus_ncts.txt")
    with open(p, encoding="utf-8") as fh:
        src["corpus_ncts"] = {t.strip() for t in fh if t.strip().startswith("NCT")}
    pmids = set()
    p = os.path.join(repo, "outputs", "pubmed_nct_linkage.csv")
    linkage_nct = set()
    with open(p, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("pmid"):
                pmids.add(row["pmid"].strip())
            for f in ("claim_nct", "pubmed_registered_ncts"):
                for v in re.findall(r"NCT\d{8}", row.get(f) or ""):
                    linkage_nct.add(v)
    src["pubmed_nct_linkage"] = linkage_nct
    union = set().union(*src.values())
    return {"by_source": {k: sorted(v) for k, v in src.items()},
            "contaminated_excluded": sorted(contaminated),
            "held_nct": union, "held_pmid": pmids}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/f/rapidmeta-finerenone")
    ap.add_argument("--cache", default=r"C:/claude-temp/comparator-seed/xml")
    ap.add_argument("--work", default=r"C:/claude-temp/comparator-seed/work")
    ap.add_argument("--firewall", default=r"C:/claude-temp/comparator-seed/stage/outputs/comparator_seed_firewall.json")
    ap.add_argument("--per-field", type=int, default=20)
    ap.add_argument("--min-k", type=int, default=4)
    args = ap.parse_args()

    with open(os.path.join(args.work, "extracted.json"), encoding="utf-8") as fh:
        ex = json.load(fh)
    with open(os.path.join(args.work, "comparator_candidates.json"), encoding="utf-8") as fh:
        cand = {c["pmcid"]: c for c in json.load(fh)["candidates"]}
    with open(args.firewall, encoding="utf-8") as fh:
        fwj = json.load(fh)
    blocked = set(fwj["scored_comparator_dois"])
    fw_topics = set(fwj["scored_topics"])

    arts = {a["pmcid"]: a for a in ex["articles"]}
    pool, fw_drops = [], []
    for pmcid, a in arts.items():
        if a["extraction_route"] == "NOT_FOUND" or a["k_extracted"] < args.min_k:
            continue
        if (a["doi"] or "").strip().lower() in blocked:
            fw_drops.append({"pmcid": pmcid, "doi": a["doi"], "title": a["title"]})
            continue
        c = cand.get(pmcid) or {"fields": [], "terms": []}
        a = dict(a)
        a["fields"] = c["fields"]
        a["terms"] = sorted(set(c["terms"]))
        pool.append(a)

    # Select for TOPIC SPREAD, not for k: at most 2 per search term, then fill by k.
    selected = []
    for field in ("cardiology", "infectious_disease"):
        inf = [a for a in pool if field in a["fields"]]
        inf.sort(key=lambda a: (-a["k_extracted"], a["pmcid"]))
        per_term, chosen = {}, []
        for a in inf:
            key = a["terms"][0] if a["terms"] else "?"
            if per_term.get(key, 0) >= 2:
                continue
            per_term[key] = per_term.get(key, 0) + 1
            chosen.append(a)
            if len(chosen) >= args.per_field:
                break
        for a in inf:
            if len(chosen) >= args.per_field:
                break
            if a not in chosen:
                chosen.append(a)
        for a in chosen:
            a = dict(a)
            a["field"] = field
            selected.append(a)
    seen, dedup = set(), []
    for a in selected:
        if a["pmcid"] in seen:
            continue
        seen.add(a["pmcid"])
        dedup.append(a)
    selected = dedup
    print("pool=%d  firewall_drops=%d  selected=%d" % (len(pool), len(fw_drops), len(selected)))

    # Enrich from the cached XML.
    for a in selected:
        path = os.path.join(args.cache, a["source_file"])
        with open(path, encoding="utf-8", errors="replace") as fh:
            root = X.strip_ns(ET.ElementTree(ET.fromstring(fh.read()))).getroot()
        a["search_close_date"] = infer_search_close(root)
        a["declared_k"] = infer_declared_k(root)
        rows = row_text_for_rids(root)
        for s in a["included_studies"]:
            s["design"] = classify_design(rows.get(s["rid"]))

    # Resolve to a common key.
    pmids = [s["pmid"] for a in selected for s in a["included_studies"] if s["pmid"]]
    print("resolving %d PMIDs to NCT via PubMed databank records" % len(set(pmids)))
    p2n = resolve_pmids_to_nct(pmids, os.path.join(args.work, "pmid_to_nct.json"))

    hold = load_holdings(args.repo)
    held_nct, held_pmid = hold["held_nct"], hold["held_pmid"]
    print("holdings: %d NCT (union), %d PMID; %d contaminated NCTs excluded" % (
        len(held_nct), len(held_pmid), len(hold["contaminated_excluded"])))

    # POSITIVE CONTROL on the join: an NCT we certainly hold must report HELD, and a
    # synthetic NCT that cannot exist must not. A join that can only say "no" is not a join.
    probe_held = sorted(hold["by_source"]["corpus_ncts"])[:3]
    probe_absent = ["NCT99999999", "NCT00000001"]
    bad = [n for n in probe_held if n not in held_nct] + [n for n in probe_absent if n in held_nct]
    if bad or not probe_held:
        raise SystemExit("FATAL: holdings join control failed on %s" % (bad or "empty probe"))
    print("join control: %s -> HELD, %s -> absent  PASS" % (probe_held, probe_absent))

    # TOPIC-SIDE FIREWALL. Blocking by comparator DOI is only half the rule: a comparator
    # with an unblocked DOI can still be ABOUT a scored topic, and seeding that topic from
    # it is the thing the firewall exists to prevent. The DOI check cannot see this, because
    # the collision is in the subject matter, not the identifier. Conservative screen: a
    # distinctive token (>=5 chars) shared between a scored topic key and the comparator
    # title flags the pair for the per-trial PICO mapping to adjudicate at ingest time.
    generic = {"REVIEW", "TRIAL", "TRIALS", "STUDY", "STUDIES", "THERAPY", "PATIENTS",
               "DISEASE", "ACUTE", "CHRONIC", "RISK", "OUTCOME", "OUTCOMES", "CARDIAC",
               "HEART", "BLOOD", "CANCER", "ADULT", "ADULTS", "AUTO", "FULL", "NEW"}
    # Exact token equality flagged DENGUE_VACCINE for a COVID review (generic token
    # "VACCINE") and MISSED COVID19_VACCINES for the same review, because the scored key
    # spells it COVID19 (digit) and VACCINES (plural) while the title yields COVID and
    # VACCINE. A screen that over-flags on a generic token while under-flagging the exact
    # collision is not failing closed, it has a hole. Normalise: drop digits, singularise.
    def stem(tok):
        return re.sub(r"\d+", "", tok).rstrip("S")

    topic_tokens = {}
    for key in fw_topics:
        toks = {stem(t) for t in key.split("_") if len(stem(t)) >= 4 and t not in generic}
        if toks:
            topic_tokens[key] = toks
    for a in selected:
        raw = set(re.findall(r"[A-Za-z0-9]{4,}", (a["title"] or "").upper())) - generic
        title_toks = {stem(t) for t in raw if len(stem(t)) >= 4}
        hits = sorted(k for k, toks in topic_tokens.items() if toks & title_toks)
        a["topic_firewall"] = {
            "collides_with_scored_topics": hits,
            "verdict": "BLOCKED_PENDING_PICO_ADJUDICATION" if hits else "CLEAR",
            "note": ("this comparator shares a distinctive term with a scored topic; it may "
                     "not seed that topic, and the per-trial PICO mapping must adjudicate "
                     "before any ingest" if hits else "no scored topic shares a distinctive term"),
        }

    totals = {"HELD": 0, "NOT_HELD": 0, "UNRESOLVABLE_NO_REGISTRY_ID": 0,
              "UNRESOLVABLE_NO_PMID": 0, "OUT_OF_SCOPE_DESIGN": 0, "COMPANION_PAPER": 0}
    for a in selected:
        seen_nct = {}
        for s in a["included_studies"]:
            ncts = []
            if s["nct"]:
                ncts.append(s["nct"])
            if s["pmid"] and p2n.get(s["pmid"]):
                ncts.extend(p2n[s["pmid"]])
            ncts = sorted(set(ncts))
            s["resolved_ncts"] = ncts
            # A review cites a trial's main paper and its companion papers as separate
            # references. They are one trial. Counting them separately inflates both
            # "their k" and any missing-trial count.
            dup = next((n for n in ncts if n in seen_nct), None)
            if dup:
                s["status"] = "COMPANION_PAPER"
                s["status_reason"] = "same trial %s as reference %s" % (dup, seen_nct[dup])
                totals["COMPANION_PAPER"] = totals.get("COMPANION_PAPER", 0) + 1
                continue
            for n in ncts:
                seen_nct[n] = s["rid"]
            design = (s.get("design") or {}).get("value")
            if design and design not in ("randomised_controlled_trial", "cluster_randomised"):
                s["status"] = "OUT_OF_SCOPE_DESIGN"
                s["status_reason"] = "comparator's own characteristics row calls this %s" % design
            elif ncts and any(n in held_nct for n in ncts):
                s["status"] = "HELD"
                s["status_reason"] = "NCT in our holdings"
            elif s["pmid"] and s["pmid"] in held_pmid:
                s["status"] = "HELD"
                s["status_reason"] = "PMID in outputs/pubmed_nct_linkage.csv"
            elif ncts:
                s["status"] = "NOT_HELD"
                s["status_reason"] = "resolved to %s, absent from our holdings" % ",".join(ncts)
            elif s["pmid"] and p2n.get(s["pmid"]) is not None:
                # PubMed knows this record and it carries NO ClinicalTrials.gov accession.
                # Our holdings are keyed by NCT (plus a 489-PMID index). Such a study cannot
                # be answered either way by this instrument. Calling it NOT_HELD would
                # manufacture a missing trial out of a key mismatch.
                s["status"] = "UNRESOLVABLE_NO_REGISTRY_ID"
                s["status_reason"] = ("PubMed record %s carries no ClinicalTrials.gov accession; "
                                      "an NCT-keyed holdings store cannot answer this" % s["pmid"])
            else:
                s["status"] = "UNRESOLVABLE_NO_PMID"
                s["status_reason"] = "no NCT in the citation and no PMID PubMed would resolve"
            totals[s["status"]] = totals.get(s["status"], 0) + 1
        c = {}
        for s in a["included_studies"]:
            c[s["status"]] = c.get(s["status"], 0) + 1
        a["counts"] = c
        # Their k, with companion papers collapsed to one trial each.
        a["k_distinct_trials"] = a["k_extracted"] - c.get("COMPANION_PAPER", 0)

    out = {
        "_doc": "PHASE 3. Measurement only. Nothing here has been ingested.",
        "firewall_applied": {
            "blocked_comparator_dois": len(blocked),
            "candidates_dropped_by_firewall": fw_drops,
        },
        "corpus": {
            "xml_fetched": ex["n_xml_files"],
            "efetch_missing": ex["n_efetch_missing"],
            "parse_errors": ex["n_parse_errors"],
            "extraction_routes": ex["routes"],
            "pool_after_min_k_%d" % args.min_k: len(pool),
            "selected": len(selected),
        },
        "holdings": {
            "by_source_sizes": {k: len(v) for k, v in hold["by_source"].items()},
            "union_nct": len(held_nct),
            "pmid_index": len(held_pmid),
            "contaminated_ncts_excluded": hold["contaminated_excluded"],
        },
        "totals": totals,
        "comparators": selected,
    }
    dest = os.path.join(args.work, "phase3_report.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print("totals:", json.dumps(totals))
    print("wrote", dest)


if __name__ == "__main__":
    main()
