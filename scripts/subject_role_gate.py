"""Does the topic's named drug appear in the EXPERIMENTAL arm of at least one included trial?

THE FAILING INPUT, which is the promotion criterion and this one has a real one.
`FIDAXOMICIN_CDI` seeds three trials. Fidaxomicin is the COMPARATOR in all three and
EXPERIMENTAL IN NONE. The outcome limb PASSES -- recurrence is shared across all three at
some rank -- and the topic still closes, because a page titled for a drug that is the
control arm everywhere is not asking the question its title asks.

NONE OF THE FOUR EXISTING PRECONDITIONS CATCHES THAT. Eligibility-versus-k, null
comparator, sibling fields and the marker prefix are all internal-consistency checks; this
is a ROLE failure between the topic's title and the registry's arm typing. It is the fourth
instance of the shape -- OLMESARTAN, DABIGATRAN_AF, LENACAPAVIR and now FIDAXOMICIN -- and
it has never had a check.

WHAT IT DOES. Take the topic's subject token from its own name, then ask the registry
whether that token appears in an arm typed EXPERIMENTAL in ANY seeded trial. If it appears
only in comparator arms, the page is titled for the control.

THREE REASONS THIS IS A TRIAGE AND NOT A VERDICT, each demonstrated:
  1. ARM TYPES LIE. RE-LY typed all three of its arms ACTIVE_COMPARATOR, including the
     experimental ones. A trial with no EXPERIMENTAL arm at all is UNASSESSABLE here, not
     failing.
  2. THE SUBJECT TOKEN IS A GUESS. A topic named for a class, a population or a comparison
     has no single drug to look for, and a short token matches inside longer words --
     substring is not identity, which this project has broken inside the tool built to
     enforce it.
  3. A DRUG CAN BE THE SUBJECT WITHOUT BEING EXPERIMENTAL in a specific trial and the topic
     still be sound, if other trials carry it.

So: a flag means READ THE TRIALS. It never means the topic is wrong.
"""
from __future__ import annotations
import io
import json
import os
import re
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://clinicaltrials.gov/api/v2/studies/{}?format=json"
CACHE = os.path.join(REPO, ".subjectrole-cache.json")
cache = json.load(io.open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
# tokens that are not a drug: populations, designs, comparisons, diseases
NOT_A_DRUG = {"review", "auto", "full", "infection", "prep", "hiv", "cdi", "cdiff", "taz",
              "healthy", "volunteers", "injectable", "act", "lf", "acwy", "men", "covid",
              "fungal", "candida", "infect", "urinary", "tract", "pneumo", "cabp", "cap",
              "rsv", "infant", "agyw"}


def arms(nct):
    if nct in cache:
        return cache[nct]
    out = None
    try:
        req = urllib.request.Request(API.format(nct), headers={"User-Agent": "rm-subj"})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
        out = [{"type": a.get("type") or "",
                "text": ((a.get("label") or "") + " " +
                         " ".join(a.get("interventionNames") or [])).lower()}
               for a in (((d.get("protocolSection") or {})
                          .get("armsInterventionsModule") or {}).get("armGroups") or [])]
    except Exception:
        out = None
    cache[nct] = out
    time.sleep(0.06)
    return out


def subject_of(name):
    tok = name.split("-")[0].lower()
    return tok if len(tok) >= 5 and tok not in NOT_A_DRUG else None


def main() -> int:
    ss = os.path.join(REPO, "ssot")
    flags, unassessable, ok = [], [], 0
    for d in sorted(os.listdir(ss)):
        f = os.path.join(ss, d, d + ".json")
        if not os.path.exists(f):
            continue
        subj = subject_of(d)
        if not subj:
            continue
        try:
            o = json.load(io.open(f, encoding="utf-8"))
        except Exception:
            continue
        ncts = [str(t.get("nct") or "") for t in ((o.get("inputs") or {}).get("trials") or [])
                if str(t.get("nct") or "").startswith("NCT")]
        if not ncts:
            continue
        exp_hit = comp_hit = typed = 0
        for n in ncts:
            a = arms(n)
            if not a:
                continue
            if any(x["type"] == "EXPERIMENTAL" for x in a):
                typed += 1
            for x in a:
                if subj in x["text"]:
                    if x["type"] == "EXPERIMENTAL":
                        exp_hit += 1
                    else:
                        comp_hit += 1
        json.dump(cache, io.open(CACHE, "w", encoding="utf-8", newline="\n"),
                  ensure_ascii=False)
        if not typed:
            unassessable.append((d, subj, len(ncts), "no trial types an EXPERIMENTAL arm"))
        elif exp_hit == 0 and comp_hit > 0:
            flags.append((d, subj, len(ncts), comp_hit))
        elif exp_hit == 0:
            unassessable.append((d, subj, len(ncts), "subject token found in no arm"))
        else:
            ok += 1

    print("topics with a resolvable subject token and seeded trials: %d"
          % (len(flags) + len(unassessable) + ok))
    print()
    print("FLAGGED -- subject appears ONLY in comparator arms: %d" % len(flags))
    for d, s, k, c in flags:
        print("   %-42s subject %r in %d comparator arm(s), 0 experimental"
              % (d[:41], s, c))
    print()
    print("subject found in an experimental arm: %d" % ok)
    print("UNASSESSABLE (not a pass): %d" % len(unassessable))
    for d, s, k, why in unassessable[:10]:
        print("   %-42s %s" % (d[:41], why))
    print()
    print("TRIAGE, NEVER A VERDICT. Arm types lie -- RE-LY typed all three of its arms")
    print("ACTIVE_COMPARATOR. The subject token is a guess. A flag means READ THE TRIALS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
