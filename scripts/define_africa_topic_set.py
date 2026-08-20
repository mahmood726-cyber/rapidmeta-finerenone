"""Which topics relate to Africa, by REGISTERED LOCATIONS rather than by name?

A NAME IS NOT A CRITERION. `rotavirus-vaccine-africa-review` says Africa and
`agyw-hiv-prep-review` does not, yet both are wholly African-sited. Selecting by topic name
would have caught one and missed the other, and would have been editorial rather than
checkable. This selects on the registrations.

THE INPUT WAS NOT ALREADY HELD, AND THAT IS THE FIRST FINDING. Only 6 of 155 objects carry
any location key at all, so registered locations had to be FETCHED -- 352 of 353 NCTs
returned by ClinicalTrials.gov API v2; the one that did not is named, not dropped.

THREE MEASURES, BECAUSE THEY DISAGREE AND THE DISAGREEMENT IS INFORMATION:

  ANY          at least one trial with at least one African site. Broad: it catches every
               multinational trial that ran a few sites in South Africa or Egypt, which is
               most large cardiology trials, and it is NOT a claim that the topic is about
               Africa.
  MAJORITY BY SITE COUNT      more than half the topic's registered sites are in Africa.
  MAJORITY BY PARTICIPANT COUNT  more than half the topic's enrolled participants come from
               trials that are themselves majority-African-sited.

RECOMMENDED: MAJORITY BY SITE COUNT. Participant-majority can flip on a single trial --
`dabigatran-vte-cerebral` qualifies on 400 of 672 participants from one trial while only 2
of its 40 sites are African -- and enrolment is a per-TRIAL number, so attributing it to a
country is an inference the registry does not support. Site count is counted where the
registry actually records it.

CAUTION, MEASURED: the site-majority set contains DUPLICATE TOPICS. Nine objects cover six
distinct subjects. Counting the objects would overstate the work by half.

DEFINES A SET. Starts nothing.
"""
import io
import json
import os
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls          # noqa: E402

CACHE = os.path.join(REPO, "outputs", "nct_locations.json")
API = ("https://clinicaltrials.gov/api/v2/studies?filter.ids=%s"
       "&fields=protocolSection.identificationModule.nctId,"
       "protocolSection.contactsLocationsModule.locations,"
       "protocolSection.designModule.enrollmentInfo&pageSize=50")

AFRICA = {
    "Algeria", "Angola", "Benin", "Botswana", "Burkina Faso", "Burundi", "Cabo Verde",
    "Cameroon", "Central African Republic", "Chad", "Comoros", "Congo",
    "Congo, The Democratic Republic of the", "Democratic Republic of the Congo",
    "Cote D'Ivoire", "Côte d'Ivoire", "Ivory Coast", "Djibouti", "Egypt",
    "Equatorial Guinea", "Eritrea", "Eswatini", "Swaziland", "Ethiopia", "Gabon",
    "Gambia", "Gambia, The", "Ghana", "Guinea", "Guinea-Bissau", "Kenya", "Lesotho",
    "Liberia", "Libya", "Libyan Arab Jamahiriya", "Madagascar", "Malawi", "Mali",
    "Mauritania", "Mauritius", "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria",
    "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles", "Sierra Leone",
    "Somalia", "South Africa", "South Sudan", "Sudan", "Tanzania",
    "Tanzania, United Republic of", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
}


def topic_ncts():
    import glob
    out = {}
    for p in sorted(glob.glob(os.path.join(REPO, "ssot", "*", "*.json"))):
        t = os.path.basename(os.path.dirname(p))
        if os.path.basename(p) != t + ".json":
            continue
        try:
            o = json.load(io.open(p, encoding="utf-8"))
        except ValueError:
            continue
        ids = [tr.get("nct") for tr in ((o.get("inputs") or {}).get("trials") or [])
               if tr.get("nct")]
        if ids:
            out[t] = ids
    return out


def fetch(want, cache):
    todo = [n for n in want if n not in cache]
    for i in range(0, len(todo), 20):
        chunk = todo[i:i + 20]
        try:
            with urllib.request.urlopen(API % ",".join(chunk), timeout=60) as fh:
                d = json.loads(fh.read().decode("utf-8"))
        except Exception as exc:                            # noqa: BLE001
            print("   batch FAILED (%s); these stay UNFETCHED and are named: %s"
                  % (type(exc).__name__, ",".join(chunk)))
            continue
        got = set()
        for st in d.get("studies", []):
            ps = st.get("protocolSection", {})
            nid = (ps.get("identificationModule") or {}).get("nctId")
            if not nid:
                continue
            locs = (ps.get("contactsLocationsModule") or {}).get("locations") or []
            enr = (ps.get("designModule") or {}).get("enrollmentInfo") or {}
            cache[nid] = {"countries": [l.get("country") for l in locs if l.get("country")],
                          "n_sites": len(locs), "enrolment": enr.get("count")}
            got.add(nid)
        for n in chunk:
            if n not in got:
                cache.setdefault(n, {"countries": [], "n_sites": 0, "enrolment": None,
                                     "not_returned": True})
        time.sleep(0.4)
    return cache


def main():
    require_controls(
        "define_africa_topic_set",
        positive=("a South African site counts as African", "South Africa" in AFRICA, True),
        negative=("a non-African country counts as African", "United States" in AFRICA, True))

    per = topic_ncts()
    want = sorted({n for ids in per.values() for n in ids})
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(io.open(CACHE, encoding="utf-8"))
    if "--fetch" in sys.argv:
        cache = fetch(want, cache)
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8"), indent=0)
    held = [n for n in want if cache.get(n) and not cache[n].get("not_returned")]
    if not held:
        print("NOT_ASSESSABLE: no locations cached. Run with --fetch first. A set defined "
              "on no locations would be a set defined on topic names.")
        return 2

    rows, unfetched = [], []
    for topic, ncts in sorted(per.items()):
        s_af = s_all = e_af = e_all = t_af = 0
        for n in ncts:
            rec = cache.get(n)
            if not rec or rec.get("not_returned"):
                unfetched.append((topic, n))
                continue
            cs = rec.get("countries") or []
            af = [c for c in cs if c in AFRICA]
            s_af += len(af)
            s_all += len(cs)
            e = rec.get("enrolment")
            if isinstance(e, int):
                e_all += e
                if cs and len(af) > len(cs) / 2.0:
                    e_af += e
            if af:
                t_af += 1
        rows.append({"topic": topic, "n": len(ncts), "t_af": t_af, "s_af": s_af,
                     "s_all": s_all, "e_af": e_af, "e_all": e_all})

    N = len(rows)
    any_af = [r for r in rows if r["t_af"] > 0]
    maj_s = [r for r in rows if r["s_all"] and r["s_af"] > r["s_all"] / 2.0]
    maj_e = [r for r in rows if r["e_all"] and r["e_af"] > r["e_all"] / 2.0]

    print("")
    print("TOPICS WITH AT LEAST ONE REGISTERED NCT: %d" % N)
    print("locations held for %d of %d NCTs" % (len(held), len(want)))
    if unfetched:
        print("NCTs the registry did not return, NAMED not dropped: %s"
              % "; ".join("%s:%s" % x for x in unfetched))
    print("")
    print("1. ANY African trial site                 %d of %d" % (len(any_af), N))
    print("2. MAJORITY African by SITE count         %d of %d" % (len(maj_s), N))
    print("3. MAJORITY African by PARTICIPANT count  %d of %d" % (len(maj_e), N))
    print("")
    print("THE RECOMMENDED SET -- majority by site count:")
    for r in sorted(maj_s, key=lambda x: -(x["s_af"] / max(x["s_all"], 1))):
        print("   %-38s %2d trial(s)  %3d/%-3d sites  %6d/%-6d participants"
              % (r["topic"][:38], r["n"], r["s_af"], r["s_all"], r["e_af"], r["e_all"]))

    # DUPLICATE TOPICS INSIDE THE SET. One subject held as two objects would be counted
    # twice, and this corpus has that shape in several places.
    import itertools
    names = [r["topic"] for r in maj_s]
    pairs = []
    for a, b in itertools.combinations(sorted(names), 2):
        sa, sb = set(per[a]), set(per[b])
        inter = sa & sb
        if inter and (len(inter) == len(sa) or len(inter) == len(sb)):
            pairs.append((a, b, len(inter), len(sa), len(sb)))
    print("")
    print("DUPLICATE TOPICS INSIDE THE RECOMMENDED SET: %d pair(s)" % len(pairs))
    for a, b, i, na, nb in pairs:
        print("   %-34s %-34s shares %d/%d and %d/%d NCTs" % (a[:34], b[:34], i, na, i, nb))
    print("   %d objects cover %d distinct subjects."
          % (len(maj_s), len(maj_s) - len(pairs)))
    print("")
    print("DEFINES A SET. Starts nothing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
