# -*- coding: utf-8 -*-
"""DETECTOR: non-inferiority trials pooled and presented as superiority.

THE HARM, AND WHY THIS CLASS IS DIFFERENT FROM THE REST. A non-inferiority trial is designed to
show a treatment is NOT MEANINGFULLY WORSE than a comparator, within a pre-specified margin.
Pool such trials and present the result as an ordinary effect estimate and the reader is
invited to read "not meaningfully worse" as "better". The margin is chosen precisely to make
that reading available, so the design does the misleading for you.

⇒ It is one of the few classes that make a reader act in the WRONG DIRECTION rather than merely
act on a weak number. That is why it outranks larger classes.

WHAT IT JOINS, BECAUSE THE DATA ALREADY EXISTS AND NOTHING JOINED IT:

  out/blind-review/noninferiority_trials.json   46 registered NI trials
  the registry record                           analyses[].nonInferiorityComment / Type
  the store                                     which trials each pooled topic contains
  the delivered page                            whether a margin or the design is disclosed

DETERMINISTIC. No model calls, no network at run time, no judgement. Every input is a file.

⛔ IT REFUSES A VACUUM. If the NI list is missing, or no topic yields a contributing trial, it
REFUSES rather than reporting a clean pass -- a detector that cannot fail is not a detector, and
this project has shipped that mistake five times. `--plant` proves both directions on a literal
fixture before any corpus number is believed.
"""
import collections
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
os.chdir(REPO)

NI_LIST = "out/blind-review/noninferiority_trials.json"
CACHES = [os.path.join(REPO, ".ctgov-raw-cache"),
          r"F:\rapidmeta-ssot-shell\.ctgov-raw-cache"]

# The page discloses the design: it names non-inferiority AND a margin, or names the design
# at minimum. Two separate questions -- naming it is weaker than stating the margin.
NAMES_NI = re.compile(r"non[- ]inferior|noninferior", re.I)
STATES_MARGIN = re.compile(
    r"margin[^.]{0,60}?(?:\d+\.\d+|\d+\s*%)|"
    r"(?:\d+\.\d+|\d+\s*%)[^.]{0,40}?\bmargin\b", re.I)
# An explicit DENIAL that the registry contradicts is worse than silence: silence is an
# omission, a denial is a false statement a reader may rely on.
DENIES_NI = re.compile(
    r"registration fields fetched do not use the word|"
    r"(?:no|not a)\s+non[- ]?inferiority(?:\s+design)?\b|"
    r"does not (?:use|state|declare)[^.]{0,40}non[- ]?inferior", re.I)


def rendered(raw):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def ni_registrations():
    """The 46 registered NI trials. Missing file is a REFUSAL, never an empty set."""
    if not os.path.exists(NI_LIST):
        return None
    try:
        d = json.load(io.open(NI_LIST, encoding="utf-8"))
    except Exception:
        return None
    if isinstance(d, list):
        return {x for x in d if isinstance(x, str) and x.startswith("NCT")}
    rows = d.get("trials") or d.get("rows") or []
    out = set()
    for r in rows:
        s = json.dumps(r)
        m = re.search(r"NCT\d{8}", s)
        if m:
            out.add(m.group(0))
    return out or None


def registry_margin(nct):
    """The margin the registry STATES, from the typed field. None when it states none."""
    for c in CACHES + [os.path.join(REPO, "ssot")]:
        if not os.path.isdir(c):
            continue
        pats = ([os.path.join(c, nct + "*.json")] if c.endswith("-raw-cache")
                else [os.path.join(c, "*", "sources", nct + "*.ctgov.json")])
        for pat in pats:
            for f in glob.glob(pat):
                try:
                    d = json.load(io.open(f, encoding="utf-8"))
                except Exception:
                    continue
                s = json.dumps(d)
                if "nonInferiority" not in s:
                    continue
                m = re.search(r'"nonInferiorityComment"\s*:\s*"([^"]{4,400})"', s)
                t = re.search(r'"nonInferiorityType"\s*:\s*"([^"]+)"', s)
                if m or t:
                    return {"comment": m.group(1) if m else None,
                            "type": t.group(1) if t else None, "source": os.path.basename(f)}
    return None


def page_for(topic):
    """The delivered page for a topic, via PAGE_MAP -- the stated mapping, not a guess."""
    f = os.path.join("ssot", "PAGE_MAP.json")
    if os.path.exists(f):
        try:
            m = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            m = {}
        for page, store in m.items():
            if isinstance(store, str) and os.path.basename(os.path.dirname(store)) == topic:
                if os.path.exists(os.path.basename(page)):
                    return os.path.basename(page)
    return None


def scan(topics=None):
    ni = ni_registrations()
    if ni is None:
        return None, "REFUSED: the non-inferiority registration list is missing or unreadable"
    rows = []
    for p in sorted(glob.glob("ssot/*/*.json")):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        if topics and t not in topics:
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        trials = set()
        for tr in ((o.get("inputs") or {}).get("trials") or []):
            if isinstance(tr, dict) and tr.get("nct"):
                trials.add(tr["nct"])
        for oid, rr in (((o.get("results") or {}).get("by_outcome")) or {}).items():
            for r in (rr.get("per_trial") or []):
                if isinstance(r, dict) and r.get("nct"):
                    trials.add(r["nct"])
        if not trials:
            continue
        hits = sorted(trials & ni)
        if not hits:
            continue
        pg = page_for(t)
        txt = ""
        if pg:
            try:
                txt = rendered(io.open(pg, "rb").read().decode("utf-8", "replace"))
            except OSError:
                pg = None
        margins = {n: registry_margin(n) for n in hits}
        rows.append({
            "topic": t, "page": pg,
            "n_trials": len(trials), "n_ni": len(hits), "ni_trials": hits,
            "all_contributing_are_ni": len(hits) == len(trials),
            "registry_states_a_margin": sum(1 for v in margins.values() if v),
            "page_names_ni": bool(txt and NAMES_NI.search(txt)),
            "page_states_margin": bool(txt and STATES_MARGIN.search(txt)),
            "page_denies_ni": bool(txt and DENIES_NI.search(txt)),
            "margins": {k: v for k, v in margins.items() if v},
        })
    return rows, None


def verdict(r):
    if r["page_denies_ni"]:
        return "DENIAL_CONTRADICTED_BY_REGISTRY"
    if not r["page_names_ni"]:
        return "UNDISCLOSED_NI_DESIGN"
    if not r["page_states_margin"]:
        return "NAMED_BUT_NO_MARGIN"
    return "DISCLOSED"


FIXTURE_TOPIC = "__control_ni_fixture"


def plant():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("PLANT -- literal fixture, both directions")
    d = os.path.join("ssot", FIXTURE_TOPIC)
    os.makedirs(d, exist_ok=True)
    obj = {"inputs": {"trials": [{"nct": "NCT00084266"}, {"nct": "NCT99999999"}]}}
    fp = os.path.join(d, FIXTURE_TOPIC + ".json")
    io.open(fp, "w", encoding="utf-8").write(json.dumps(obj))
    try:
        rows, err = scan(topics={FIXTURE_TOPIC})
        assert err is None and len(rows) == 1, (err, rows)
        r = rows[0]
        assert r["n_ni"] == 1 and r["n_trials"] == 2, r
        assert verdict(r) == "UNDISCLOSED_NI_DESIGN", verdict(r)
        print("   NI trial in a pooled topic, no page disclosure -> %s   [PASS]" % verdict(r))
        # CLEAN CASE: a topic whose trials are not registered NI must not be flagged at all.
        obj2 = {"inputs": {"trials": [{"nct": "NCT99999998"}, {"nct": "NCT99999999"}]}}
        io.open(fp, "w", encoding="utf-8").write(json.dumps(obj2))
        rows2, err2 = scan(topics={FIXTURE_TOPIC})
        assert err2 is None and rows2 == [], rows2
        print("   no registered NI trial -> not flagged                [PASS]")
    finally:
        for f in glob.glob(os.path.join(d, "*")):
            os.remove(f)
        os.rmdir(d)
    assert not os.path.exists(d), d
    print("   fixture removed and its absence asserted             [PASS]")
    # REFUSES A VACUUM.
    global NI_LIST
    keep, NI_LIST = NI_LIST, "out/blind-review/__does_not_exist.json"
    rows3, err3 = scan()
    NI_LIST = keep
    assert rows3 is None and err3 and err3.startswith("REFUSED"), (rows3, err3)
    print("   missing NI list -> REFUSES, does not pass            [PASS]")
    print("")
    print("Both directions watched, vacuum refused, fixture restored.")
    return 0


def main():
    if "--plant" in sys.argv:
        return plant()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    rows, err = scan()
    if err:
        print(err)
        return 2
    if not rows:
        print("REFUSED: no pooled topic contains a registered non-inferiority trial. That is "
              "either a true zero or a broken join, and this detector cannot tell which -- so "
              "it refuses rather than reporting a clean pass.")
        return 2
    v = collections.Counter(verdict(r) for r in rows)
    print("")
    print("DETECTOR -- non-inferiority trials pooled and presented as superiority")
    print("")
    print("  pooled topics containing >=1 registered NI trial   %4d  == the denominator"
          % len(rows))
    for k in ("DENIAL_CONTRADICTED_BY_REGISTRY", "UNDISCLOSED_NI_DESIGN",
              "NAMED_BUT_NO_MARGIN", "DISCLOSED"):
        print("     %-34s %4d" % (k, v[k]))
    allni = [r for r in rows if r["all_contributing_are_ni"]]
    print("")
    print("  topics where EVERY contributing trial is NI        %4d  <- the pooled ratio is"
          % len(allni))
    print("                                                          built entirely from")
    print("                                                          non-inferiority designs")
    for r in allni:
        print("     %-30s %d/%d trials   registry states a margin for %d   verdict %s"
              % (r["topic"][:30], r["n_ni"], r["n_trials"], r["registry_states_a_margin"],
                 verdict(r)))
    den = [r for r in rows if r["page_denies_ni"]]
    if den:
        print("")
        print("  PAGES CARRYING A DENIAL THE REGISTRY CONTRADICTS   %4d" % len(den))
        for r in den:
            print("     %-30s page=%s  NI trials=%d" % (r["topic"][:30], r["page"], r["n_ni"]))
    withm = [r for r in rows if r["registry_states_a_margin"]]
    print("")
    print("  topics where the registry states an explicit margin %3d" % len(withm))
    print("  topics whose PAGE states any margin                 %3d"
          % sum(1 for r in rows if r["page_states_margin"]))
    out = r"F:\claude-temp\pend\out\noninferiority_detector.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump([{**r, "verdict": verdict(r)} for r in rows],
              io.open(out, "w", encoding="utf-8"), indent=1)
    print("")
    print("  detail -> noninferiority_detector.json")
    return 1 if (v["DENIAL_CONTRADICTED_BY_REGISTRY"] or v["UNDISCLOSED_NI_DESIGN"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
