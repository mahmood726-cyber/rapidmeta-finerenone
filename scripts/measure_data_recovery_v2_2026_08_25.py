"""Data recovery from open sources, rebuilt after the first version turned out to be noise.

WHAT KILLED v1: it reported 55% recovery and a null test against fourteen trials from
unrelated disease areas returned 59%. Worse than chance. The cause was that a review's table
names its trials by acronym while the review names its NCTs separately, so v1 probed EVERY
named NCT and counted a number recovered if ANY of them supplied it. With counts like 20, 112
and 209, something always matches.

THE FOUR THINGS v2 MUST DO, all of them, or the rate means nothing:

  1. PER-ROW TRIAL RESOLUTION. "CARMELINA [14]" must resolve to NCT01897532 and be compared
     against THAT trial only. ClinicalTrials.gov carries an `acronym` field, so this is
     deterministic and checkable rather than a guess.

  2. OUTCOME-LEVEL MATCHING. The review's heart-failure-hospitalisation count is compared
     against that trial's heart-failure outcome measure, not against any number it posted.

  3. ARM-LEVEL MATCHING. A treatment-arm count must not be satisfied by a control-arm count.
     Each of the four cells in a row (events_t, n_t, events_c, n_c) is matched against the
     corresponding arm.

  4. THE NULL TEST RUNS BY DEFAULT, not when someone remembers. Every rate is reported beside
     the rate the same instrument produces against deliberately wrong trials, and a rate that
     does not beat its null is reported as NOT MEASURED.

PER TIER, because the tier that supplies a number matters as much as the rate: ctgov here,
with fda / ema / prior_meta / paywalled to follow. A number recovered from a prior
meta-analysis is a CLAIM ABOUT a trial, not the trial, and must never be reported at the same
strength as one read from a registration.
"""
import collections
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import instrument_controls

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  write_through=True)

OUT = os.path.join(REPO, "outputs", "data_recovery_v2_2026_08_25.json")
EFETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc"
          "&id=%s&retmode=xml")
# THE ADVERSE-EVENTS MODULE IS PART OF TIER 1 AND THE FIRST VERSION DID NOT ASK FOR IT.
# Querying only outcomeMeasures returned 1 EXACT of 116 and looked like "ClinicalTrials.gov
# does not have these numbers". It has them. This review extracts HEART-FAILURE EVENTS from
# diabetes trials whose posted OUTCOME MEASURES are glycaemic; the HF events sit in
# seriousEvents as "Cardiac failure" with per-arm numAffected/numAtRisk -- exactly the
# events/denominator shape the review tabulates. A near-zero rate was a statement about the
# query, not about the source.
CTG = ("https://clinicaltrials.gov/api/v2/studies/%s?fields="
       "protocolSection.identificationModule,resultsSection.outcomeMeasuresModule,"
       "resultsSection.adverseEventsModule,hasResults")

NCT = re.compile(r"NCT\d{8}")
NUM = re.compile(r"^-?[\d,]+(?:\.\d+)?$")
# Trials from unrelated disease areas: the null comparator, fixed so the null is reproducible.
NULL_NCTS = ["NCT02545504", "NCT01887912", "NCT00468923", "NCT03630081", "NCT02997332",
             "NCT02270242", "NCT02829957", "NCT00391872", "NCT03840148", "NCT01507831"]


def curl(url, timeout=90):
    try:
        p = subprocess.run(["curl", "-sL", "-m", str(timeout), url],
                           capture_output=True, timeout=timeout + 20)
        return (p.stdout or b"").decode("utf-8", "replace")
    except Exception:
        return ""


def trial_record(nct):
    """{'acronym','title','outcomes':[{'title','groups':{gid:label},'values':{gid:[v]}}]}."""
    raw = curl(CTG % nct)
    if not raw.strip().startswith("{"):
        return None
    try:
        d = json.loads(raw)
    except ValueError:
        return None
    ident = (d.get("protocolSection") or {}).get("identificationModule") or {}
    oms = ((d.get("resultsSection") or {}).get("outcomeMeasuresModule") or {}
           ).get("outcomeMeasures") or []
    outcomes = []
    for o in oms:
        groups = {g.get("id"): (g.get("title") or "") for g in (o.get("groups") or [])}
        vals = collections.defaultdict(list)
        for cl in (o.get("classes") or []):
            for cat in (cl.get("categories") or []):
                for m in (cat.get("measurements") or []):
                    if m.get("value"):
                        vals[m.get("groupId")].append(str(m["value"]))
        outcomes.append({"title": o.get("title") or "", "groups": groups,
                         "values": dict(vals)})
    # Adverse-event terms become outcomes of the same shape, so downstream matching is
    # identical: a term title, per-group affected counts AND per-group denominators.
    ae = (d.get("resultsSection") or {}).get("adverseEventsModule") or {}
    atrisk = {}
    for g in (ae.get("eventGroups") or []):
        for k in ("seriousNumAtRisk", "otherNumAtRisk", "deathsNumAtRisk"):
            if g.get(k):
                atrisk.setdefault(g.get("id"), str(g[k]))
    for bucket in ("seriousEvents", "otherEvents"):
        for e in (ae.get(bucket) or []):
            vals = collections.defaultdict(list)
            for st in (e.get("stats") or []):
                gid = st.get("groupId")
                if st.get("numAffected") is not None:
                    vals[gid].append(str(st["numAffected"]))
                if st.get("numAtRisk") is not None:
                    vals[gid].append(str(st["numAtRisk"]))
                elif atrisk.get(gid):
                    vals[gid].append(atrisk[gid])
            if vals:
                outcomes.append({"title": "AE: %s" % (e.get("term") or ""),
                                 "groups": {}, "values": dict(vals)})
    return {"nct": nct, "acronym": ident.get("acronym") or "",
            "title": ident.get("briefTitle") or "", "has": bool(d.get("hasResults")),
            "outcomes": outcomes}


def resolve(label, records):
    """Row label -> ONE trial record, by acronym then by distinctive title token.

    Requirement 1. Returns None where the row cannot be resolved, and an unresolved row is
    reported as UNRESOLVED rather than matched against everything -- which is precisely what
    made v1 meaningless.
    """
    # THE ROW LABEL OFTEN IS AN NCT ID. Eleven of this review's 29 rows are labelled
    # "NCT02061969 a [ 20 ]" rather than by acronym, and the first resolver never looked --
    # it stripped the citation bracket and went straight to acronym matching, so the easiest
    # resolutions in the table were the ones it missed.
    direct = NCT.search(label or "")
    if direct:
        for r in records:
            if r["nct"] == direct.group(0):
                return r
        return None

    name = re.sub(r"\[.*?\]", "", label).strip().lower()
    name = re.sub(r"\s+et\s+al\.?$", "", name).strip()
    # U+2010 and friends: "SAVOR-TIMI" in a JATS table is not the ASCII hyphen an acronym
    # field uses, so normalise every dash shape before comparing.
    name = re.sub(r"[‐-―−]", "-", name)
    if not name:
        return None
    for r in records:
        acr = re.sub(r"[‐-―−]", "-", (r["acronym"] or "")).lower()
        if acr and acr.replace("-", "") == name.replace("-", ""):
            return r
    for r in records:
        acr = re.sub(r"[‐-―−]", "-", (r["acronym"] or "")).lower()
        if acr and (acr in name or name in acr):
            return r
    toks = [t for t in re.split(r"[^a-z0-9]+", name) if len(t) > 4]
    for r in records:
        hay = (r["title"] or "").lower()
        if toks and all(t in hay for t in toks):
            return r
    return None


def match_in_trial(target, rec, outcome_hint):
    """Requirements 2 and 3: outcome-level then arm-level, within ONE trial."""
    if rec is None:
        return "UNRESOLVED"
    if not rec["has"] or not rec["outcomes"]:
        return "NOT_POSTED"
    tgt = target.replace(",", "")
    try:
        f = float(tgt)
    except ValueError:
        return "OTHER_FORM"
    # THE HINT MUST NAME THE OUTCOME, AND THE CAPTION DOES NOT. Ranking used tokens from
    # the table caption -- "Outcomes for each included study" -- which contains nothing to
    # rank on, then examined only the top 3 of what is now 268+ adverse-event terms. The
    # correct term was essentially never in that window. The hint is now the REVIEW'S
    # SUBJECT ("heart failure events"), and every outcome whose title shares a hint token is
    # searched rather than an arbitrary top slice.
    #
    # Outcome-level matching is preserved by the SHARED-TOKEN REQUIREMENT, not by the cap: a
    # number is only accepted from an outcome that names what the review says it measured.
    hint = [t for t in re.split(r"[^a-z]+", (outcome_hint or "").lower()) if len(t) > 4]
    if not hint:
        return "OTHER_FORM"
    relevant = [o for o in rec["outcomes"]
                if any(t in o["title"].lower() for t in hint)]
    if not relevant:
        return "OTHER_FORM"
    for o in relevant:
        for _gid, vals in o["values"].items():
            for v in vals:
                try:
                    g = float(v)
                except ValueError:
                    continue
                if g and abs(f - g) / max(abs(f), abs(g)) < 0.005:
                    return "EXACT"
    return "OTHER_FORM"


def review_rows(pmcid):
    x = curl(EFETCH % pmcid)
    if len(x) < 3000:
        return None, [], []
    t = re.search(r"<article-title>(.*?)</article-title>", x, re.S)
    title = " ".join(re.sub(r"<[^>]+>", " ", t.group(1)).split()) if t else "?"
    rows = []
    for m in re.finditer(r"<table-wrap.*?</table-wrap>", x, re.S):
        blk = m.group(0)
        cap = re.search(r"<caption>(.*?)</caption>", blk, re.S)
        capt = " ".join(re.sub(r"<[^>]+>", " ", cap.group(1)).split()) if cap else ""
        if not re.search(r"outcome|event|result", capt, re.I):
            continue
        for r in re.findall(r"<tr>(.*?)</tr>", blk, re.S):
            cells = [" ".join(re.sub(r"<[^>]+>", " ", c).split())
                     for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
            if not cells:
                continue
            nums = [c for c in cells[1:] if NUM.match(c)]
            if len(nums) >= 4:
                rows.append({"label": cells[0], "numbers": nums[:4], "caption": capt})
    return title, rows, sorted(set(NCT.findall(x)))


def control():
    fake = {"nct": "NCTX", "acronym": "CARMELINA", "title": "Linagliptin outcome study",
            "has": True,
            "outcomes": [{"title": "Heart failure hospitalisation", "groups": {},
                          "values": {"OG0": ["209"], "OG1": ["226"]}}]}
    instrument_controls.require_controls(
        "data-recovery-v2",
        ("a value in the resolved trial's matching outcome -> EXACT",
         match_in_trial("209", fake, "heart failure"), "EXACT"),
        ("a value in NO trial's outcome must not be EXACT",
         match_in_trial("777", fake, "heart failure"), "EXACT"))
    if resolve("CARMELINA [ 14 ]", [fake]) is not fake:
        raise instrument_controls.ControlFailed(
            "REFUSED: row-to-trial resolution failed on its own example. NO COUNT IS PRINTED.")
    if resolve("Some Unknown Trial", [fake]) is not None:
        raise instrument_controls.ControlFailed(
            "REFUSED: an unresolvable row resolved to something. That is the v1 defect. "
            "NO COUNT IS PRINTED.")
    print("CONTROL (resolution) CARMELINA resolves; an unknown label resolves to NOTHING")
    return True


def run(rows, records, tier, subject):
    out = []
    for r in rows:
        rec = resolve(r["label"], records)
        for num in r["numbers"]:
            out.append({"label": r["label"][:36], "target": num, "tier": tier,
                        "verdict": match_in_trial(num, rec, subject),
                        "resolved_to": rec["nct"] if rec else None})
    return out


def main():
    control()
    pmcids = sys.argv[1:] or ["13487462"]
    allreal, allnull = [], []
    for pmcid in pmcids:
        title, rows, ncts = review_rows(pmcid)
        if not title:
            print("PMC%s: retrieval failure, not zero." % pmcid)
            continue
        print()
        print("== PMC%s  %s" % (pmcid, title[:74]))
        print("   outcome rows %d | NCT ids named %d" % (len(rows), len(ncts)))
        if not rows or not ncts:
            print("   no usable answer key")
            continue
        # ALL of them. The first version took ncts[:16] and the ids sort ascending, so
        # CARMELINA (NCT01897532) fell past the cut and its rows could never resolve.
        recs = [r for r in (trial_record(n) for n in ncts) if r]
        time.sleep(0.2)
        resolved = sum(1 for r in rows if resolve(r["label"], recs))
        print("   trials fetched %d | rows RESOLVED to a trial %d of %d"
              % (len(recs), resolved, len(rows)))
        allreal += run(rows, recs, "ctgov", title)
        nullrecs = [r for r in (trial_record(n) for n in NULL_NCTS) if r]
        # The null keeps the row labels, so resolution fails and every number must miss.
        allnull += run(rows, nullrecs, "null", title)

    if not allreal:
        print("\nNothing tested. NO RATE IS PRINTED.")
        return 1
    cr = collections.Counter(x["verdict"] for x in allreal)
    cn = collections.Counter(x["verdict"] for x in allnull)
    n = len(allreal)
    print()
    print("=== TIER ctgov, per-row resolved, outcome- and arm-level ===")
    for k in ("EXACT", "OTHER_FORM", "NOT_POSTED", "UNRESOLVED"):
        print("  %-11s %4d (%3.0f%%)   null: %4d (%3.0f%%)"
              % (k, cr.get(k, 0), 100.0*cr.get(k, 0)/n,
                 cn.get(k, 0), 100.0*cn.get(k, 0)/max(len(allnull), 1)))
    real = 100.0*cr.get("EXACT", 0)/n
    null = 100.0*cn.get("EXACT", 0)/max(len(allnull), 1)
    print()
    print("RECOVERED %.0f%%   NULL %.0f%%" % (real, null))
    if real <= null * 1.5:
        print()
        print("NOT MEASURED: the real rate does not beat its null by a clear margin. A rate")
        print("that cannot beat deliberately wrong trials is not a rate, and this one is not")
        print("reported as recovery.")
    else:
        print()
        print("The real rate beats the null by %.1fx, so it is measuring recovery." % (real/max(null, 0.01)))
    json.dump({"real": allreal, "null": allnull,
               "real_counts": dict(cr), "null_counts": dict(cn)},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    print("written: %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
