# -*- coding: utf-8 -*-
"""Fetch per-arm serious adverse events and deaths from ClinicalTrials.gov v2.

⛔ RETRIEVAL ONLY. This composes nothing. Every value is a registry field with the
field path recorded beside it, so a reader can fetch the same URL and check it.

⛔ ARMS ARE KEYED FROM THE eventGroup TITLE, NEVER FROM ITS INDEX. AGYW's own
registry block records why: on NCT01539226 the group index means DIFFERENT ARMS IN
DIFFERENT MODULES of the same registration -- baseline, flow and adverse events put
PLACEBO at 000 while the outcome module puts it at 001. An extraction keyed on the
index is silently transposed, and a transposed harms table reverses the direction of
every safety statement on the page. This script CHECKS for that inversion across
four modules and REFUSES a trial whose modules disagree, rather than picking one.

⛔ WRITES TO A PARALLEL LOCATION. Nothing is replaced in place, so the block can be
diffed before any store is touched.

    python scripts/retrieve_registry_harms.py PAGE.html --out parallel.json
"""
import importlib.util
import io
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
UA = {"User-Agent": "rapidmeta-registry-harms/1.0 (mailto:mahmood726@gmail.com)"}
API = "https://clinicaltrials.gov/api/v2/studies/%s"

# The known answer. DAPA-HF placebo arm, deaths, read 2026-09-01. If the extractor
# returns anything else for this trial, no block is written: an extractor that has
# lost its arm keying produces a plausible table with the arms REVERSED, and that is
# not detectable by inspecting the output.
CONTROL = {"nct": "NCT03036124", "arm": "placebo",
           "deaths_affected": 333, "deaths_at_risk": 2368}

NON_ALNUM = re.compile(r"[^a-z0-9]+")
GROUP_PREFIX = re.compile(r"^[A-Z]+")


def fetch(nct):
    req = urllib.request.Request(API % nct, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))


def _norm(s):
    return NON_ALNUM.sub(" ", str(s or "").lower()).strip()


def group_titles(doc):
    """Group id -> title, per module, so a disagreement is visible not assumed."""
    rs = doc.get("resultsSection") or {}
    out = {}
    ae = (rs.get("adverseEventsModule") or {}).get("eventGroups") or []
    out["adverseEvents"] = {g.get("id"): g.get("title") for g in ae}
    pf = (rs.get("participantFlowModule") or {}).get("groups") or []
    out["participantFlow"] = {g.get("id"): g.get("title") for g in pf}
    bl = (rs.get("baselineCharacteristicsModule") or {}).get("groups") or []
    out["baseline"] = {g.get("id"): g.get("title") for g in bl}
    om = (rs.get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []
    first = (om[0].get("groups") if om else []) or []
    out["outcome"] = {g.get("id"): g.get("title") for g in first}
    return out


def inversion_check(titles):
    """Do the modules agree on which SUFFIX carries which arm title?

    Compares the numeric suffix of each group id against its normalised title.
    'Total' rows are ignored -- they exist only in the baseline module and are
    not an arm. Returns (agrees, detail)."""
    # ⛔ COMPARED SPACE-FREE, AND THE FIRST VERSION WAS NOT.
    # Keyed on _norm(), DAPA-HF was REFUSED because its outcome module writes
    # "Dapa 10 mg" while the other three write "Dapa 10mg". One space, read as an
    # arm inversion. The refusal was safe -- it failed toward refusing -- and it
    # was still wrong, and it would have cost the trial silently.
    #
    # Space-free is the right key and it does not weaken the check: an INVERSION
    # is treatment where control should be, which differs in WORDS. No inversion
    # has ever consisted of a space. Anything this now lets through differs only
    # in punctuation or spacing, which is not an arm swap.
    seen = {}
    for mod, mapping in titles.items():
        for gid, title in (mapping or {}).items():
            if _norm(title) == "total":
                continue
            suffix = GROUP_PREFIX.sub("", str(gid or ""))
            seen.setdefault(suffix, {})[mod] = _norm(title).replace(" ", "")
    detail = {}
    agrees = True
    for suffix, per_mod in sorted(seen.items()):
        detail[suffix] = per_mod
        if len(set(per_mod.values())) > 1:
            agrees = False
    return agrees, detail


def rr(e1, n1, e0, n0):
    """Risk ratio with a log interval, or None when it is undefined.

    ⛔ NO CONTINUITY CORRECTION. This is retrieval, not pooling: a zero cell is
    reported as a zero cell and the ratio is left undefined. Adding 0.5 here would
    manufacture an estimate the registry does not support."""
    if not all(isinstance(v, int) for v in (e1, n1, e0, n0)):
        return None
    if n1 <= 0 or n0 <= 0 or e1 <= 0 or e0 <= 0:
        return None
    point = (float(e1) / n1) / (float(e0) / n0)
    se = math.sqrt(1.0 / e1 - 1.0 / n1 + 1.0 / e0 - 1.0 / n0)
    return {"point": round(point, 4),
            "ci_low": round(point * math.exp(-1.96 * se), 4),
            "ci_high": round(point * math.exp(1.96 * se), 4),
            "se_log_rr": round(se, 6),
            "method": "log risk ratio, Katz interval, no continuity correction"}


def arms_for(doc):
    """Per-arm counts keyed BY TITLE, with the role read from the title."""
    ae = (doc.get("resultsSection") or {}).get("adverseEventsModule") or {}
    out = []
    for g in ae.get("eventGroups") or []:
        t = _norm(g.get("title"))
        role = "control" if ("placebo" in t or "comparator" in t) else "treatment"
        out.append({"role": role, "title": g.get("title"),
                    "deaths_affected": g.get("deathsNumAffected"),
                    "deaths_at_risk": g.get("deathsNumAtRisk"),
                    "serious_affected": g.get("seriousNumAffected"),
                    "serious_at_risk": g.get("seriousNumAtRisk")})
    return out


def load_gate():
    p = os.path.join(REPO, "gates", "gate16_reader_can_check.py")
    spec = importlib.util.spec_from_file_location("g16", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def plant_inversion_check(out):
    """The space-free key must still REFUSE a real inversion.

    ⛔ THIS PLANT EXISTS BECAUSE THE FIX NEEDED ONE. Loosening a comparison to
    clear a false alarm is the most natural way to disable a check entirely, and
    a check that has stopped firing looks exactly like a corpus with no defects.
    Each case below is paired: the clean sibling must PASS through the same path
    that the planted defect must FAIL."""
    swapped = {
        "adverseEvents": {"EG000": "Dapa 10mg", "EG001": "Placebo"},
        "participantFlow": {"FG000": "Dapa 10mg", "FG001": "Placebo"},
        "baseline": {"BG000": "Dapa 10mg", "BG001": "Placebo", "BG002": "Total"},
        "outcome": {"OG000": "Placebo", "OG001": "Dapa 10 mg"},
    }
    spacing = {
        "adverseEvents": {"EG000": "Dapa 10mg", "EG001": "Placebo"},
        "participantFlow": {"FG000": "Dapa 10mg", "FG001": "Placebo"},
        "baseline": {"BG000": "Dapa 10mg", "BG001": "Placebo", "BG002": "Total"},
        "outcome": {"OG000": "Dapa 10 mg", "OG001": "Placebo"},
    }
    cases = [
        ("a REAL inversion (outcome module swaps the arms)", swapped, False),
        ("spacing only -- the false alarm that forced this fix", spacing, True),
    ]
    ok = True
    out("  PLANT -- the inversion check must refuse a swap and allow a space")
    for what, titles, expect_agree in cases:
        agrees, _ = inversion_check(titles)
        mark = "ok" if agrees == expect_agree else "*** WRONG ***"
        out("    %-52s agrees=%-5s expected=%-5s %s"
            % (what, agrees, expect_agree, mark))
        if agrees != expect_agree:
            ok = False
    return ok


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--plant" in sys.argv:
        return 0 if plant_inversion_check(print) else 1
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    if not args:
        print("usage: retrieve_registry_harms.py PAGE.html --out FILE.json")
        return 2
    page = args[0]

    m = load_gate()
    sp = m.store_for(page)
    if sp is None:
        print("REFUSED: no store resolves for %s" % page)
        return 3
    with io.open(sp, encoding="utf-8") as fh:
        canon = json.load(fh)
    trials = (canon.get("inputs") or {}).get("trials") or []
    ncts = [t.get("nct") for t in trials if isinstance(t, dict) and t.get("nct")]
    print("  page   : %s" % page)
    print("  store  : %s" % os.path.relpath(sp, REPO).replace(os.sep, "/"))
    print("  trials : %d  %s" % (len(ncts), ", ".join(ncts)))
    print("")

    per_trial = {}
    kinds = {}
    control_seen = None

    def bump(k):
        kinds[k] = kinds.get(k, 0) + 1

    for nct in ncts:
        try:
            doc = fetch(nct)
        except urllib.error.HTTPError as exc:
            state = "HTTP_%s" % exc.code
            per_trial[nct] = {"state": state}
            bump(state)
            print("  %-13s %s" % (nct, state))
            continue
        except Exception as exc:
            state = "FETCH_FAILED:%s" % type(exc).__name__
            per_trial[nct] = {"state": state}
            bump(state)
            print("  %-13s %s" % (nct, state))
            continue

        titles = group_titles(doc)
        agrees, detail = inversion_check(titles)
        arms = arms_for(doc)
        roles = sorted(a["role"] for a in arms)

        if not agrees:
            per_trial[nct] = {"state": "ARM_CODES_DISAGREE_ACROSS_MODULES",
                              "group_titles_by_suffix": detail}
            bump("ARM_CODES_DISAGREE_ACROSS_MODULES")
            print("  %-13s REFUSED -- modules disagree on arm codes" % nct)
            continue
        if roles != ["control", "treatment"]:
            per_trial[nct] = {"state": "ARMS_NOT_A_TREATMENT_CONTROL_PAIR",
                              "titles": [a["title"] for a in arms]}
            bump("ARMS_NOT_A_TREATMENT_CONTROL_PAIR")
            print("  %-13s REFUSED -- %d arm(s): %s"
                  % (nct, len(arms),
                     ", ".join(str(a["title"]) for a in arms)))
            continue

        tr = next(a for a in arms if a["role"] == "treatment")
        co = next(a for a in arms if a["role"] == "control")
        if nct == CONTROL["nct"]:
            control_seen = {"deaths_affected": co["deaths_affected"],
                            "deaths_at_risk": co["deaths_at_risk"]}
        ps = doc.get("protocolSection") or {}
        el = ps.get("eligibilityModule") or {}
        locs = (ps.get("contactsLocationsModule") or {}).get("locations") or []
        per_trial[nct] = {
            "state": "EXTRACTED",
            "arm_keying": "from the eventGroup TITLE, not its index; modules agree",
            "group_titles_by_suffix": detail,
            "treatment_arm_title": tr["title"],
            "control_arm_title": co["title"],
            "deaths": {
                "treatment": {"events": tr["deaths_affected"],
                              "n": tr["deaths_at_risk"]},
                "control": {"events": co["deaths_affected"],
                            "n": co["deaths_at_risk"]},
                "rr": rr(tr["deaths_affected"], tr["deaths_at_risk"],
                         co["deaths_affected"], co["deaths_at_risk"]),
                "path": "resultsSection.adverseEventsModule.eventGroups[].deathsNumAffected",
            },
            "serious_adverse_events": {
                "treatment": {"events": tr["serious_affected"],
                              "n": tr["serious_at_risk"]},
                "control": {"events": co["serious_affected"],
                            "n": co["serious_at_risk"]},
                "rr": rr(tr["serious_affected"], tr["serious_at_risk"],
                         co["serious_affected"], co["serious_at_risk"]),
                "path": "resultsSection.adverseEventsModule.eventGroups[].seriousNumAffected",
            },
            "eligibility": {"sex": el.get("sex"),
                            "minimum_age": el.get("minimumAge"),
                            "maximum_age": el.get("maximumAge"),
                            "path": "protocolSection.eligibilityModule"},
            "countries": sorted(set(l.get("country") for l in locs
                                    if l.get("country"))),
            "source_url": API % nct,
        }
        bump("EXTRACTED")
        print("  %-13s EXTRACTED  serious tx %s/%s vs ctrl %s/%s   deaths %s/%s vs %s/%s"
              % (nct, tr["serious_affected"], tr["serious_at_risk"],
                 co["serious_affected"], co["serious_at_risk"],
                 tr["deaths_affected"], tr["deaths_at_risk"],
                 co["deaths_affected"], co["deaths_at_risk"]))
        time.sleep(0.3)

    print("")
    print("  KNOWN-ANSWER CONTROL -- expected beside observed")
    observed = ("%s/%s" % (control_seen["deaths_affected"],
                           control_seen["deaths_at_risk"])
                if control_seen else "NOT REACHED")
    print("    %s %s deaths   expected %s/%s   observed %s"
          % (CONTROL["nct"], CONTROL["arm"], CONTROL["deaths_affected"],
             CONTROL["deaths_at_risk"], observed))
    ok = bool(control_seen
              and control_seen["deaths_affected"] == CONTROL["deaths_affected"]
              and control_seen["deaths_at_risk"] == CONTROL["deaths_at_risk"])
    if not ok:
        print("    *** WRONG ***")
        print("  REFUSED: the control did not reproduce. Nothing written -- an")
        print("  extractor that has lost its arm keying yields a plausible table")
        print("  with the arms REVERSED, which inspecting the output cannot catch.")
        return 3
    print("    ok")
    print("")
    print("  KINDS -- these sum to the trial population, by design")
    for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
        print("    %-40s %d" % (k, v))
    print("    %-40s %d  <- the denominator" % ("TOTAL", sum(kinds.values())))

    block = {
        "_what": ("Serious adverse events and deaths, per arm, from "
                  "ClinicalTrials.gov POSTED RESULTS, read by machine. Nothing "
                  "here is transcribed and nothing here is composed."),
        "_source_field": "resultsSection.adverseEventsModule.eventGroups",
        "_arm_keying": ("From the eventGroup TITLE, never its index. The group "
                        "index means different arms in different modules on some "
                        "registrations, and a transposed harms table reverses the "
                        "direction of every safety statement built on it. A trial "
                        "whose modules disagree is REFUSED, not guessed."),
        "_what_this_does_NOT_add": (
            "⚠️ THIS IS NOT A FULL HARMS REVIEW. It reports the two summary "
            "categories the registry posts -- serious adverse events and deaths -- "
            "per arm, with denominators. It does not extract the MedDRA "
            "system-organ-class tables, does not adjudicate, and does not pool."),
        "_why_the_registry_and_not_the_papers": (
            "The registry gives the counts in a fixed schema with a per-arm "
            "denominator, so the extraction is checkable field by field against a "
            "URL any reader can fetch."),
        "per_trial": per_trial,
    }
    if out_path:
        with io.open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(block, ensure_ascii=False, indent=1) + "\n")
        print("")
        print("  WROTE PARALLEL FILE (no store touched): %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
