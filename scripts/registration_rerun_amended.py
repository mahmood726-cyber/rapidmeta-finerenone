"""Run the CORRECTED query for sglt2-mace-cvot-review and publish BOTH results.

THE ORDERING DISCIPLINE APPLIED TO A RE-RUN. The same rule that governs a first search
governs an amended one: the document authorising it must be committed before it runs.
Here that document is Amendment 2, and this script REFUSES to query unless the committed
blob of the governing protocol actually contains it. The guard is the point -- an
amendment that exists only in the working tree authorises nothing.

WHAT IS NOT DONE: the original result is not replaced, moved, or deleted. It stays in
`databases` exactly as recorded. The corrected run is appended under `amended_search`.

    Changing a strategy after seeing its result is the defect.
    Changing it after DISCLOSING the result is method.

Both queries and both sets of counts sit side by side so a reader can see the difference
the correction made, which is the only way the correction can be judged.
"""
import datetime
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

S = r"F:\claude-temp\claude\C--Users-mahmo\f842b4e4-f3de-4ce2-83d8-0adf7aa7cfb1\scratchpad"
WT = os.path.join(S, "main-wt")
sys.path.insert(0, os.path.join(WT, "ssot"))
from search_harness import run as srun, EXECUTED, EMPTY, FAILED  # noqa: E402

TOPIC = "sglt2-mace-cvot-review"
GOV = "protocols/sglt2_mace_cvot_protocol_v1.1_2026-04-20.md"
CORRECTED = "SGLT2 inhibitor major adverse cardiovascular events"


def now():
    t = datetime.datetime.now(datetime.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (t.microsecond // 1000)


def git(*a):
    return subprocess.run(["git", "-C", WT] + list(a), capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.strip()


# ---- THE GUARD -------------------------------------------------------------------
sha = git("rev-parse", "HEAD")
committed = subprocess.run(["git", "-C", WT, "show", sha + ":" + GOV],
                           capture_output=True).stdout
if b"Amendment 2" not in committed:
    print("REFUSED: the committed governing protocol does not contain Amendment 2.")
    print("An amendment that exists only in the working tree authorises nothing, and a")
    print("corrected query run under it would be exactly the post-hoc change the")
    print("amendment exists to avoid. No query issued.")
    sys.exit(2)
if CORRECTED.encode() not in committed:
    print("REFUSED: the committed amendment does not name this query string.")
    print("   expected in the commit: %s" % CORRECTED)
    print("Running a query the amendment did not declare would make the amendment")
    print("decorative. No query issued.")
    sys.exit(2)
print("GUARD PASSED: Amendment 2 is committed at %s and names the corrected query." % sha[:9])
print()

# ---- run the corrected query ------------------------------------------------------
drug = "empagliflozin"
qs = {
    "pubmed": {"db": "pubmed", "retmode": "json", "retmax": 100, "term": CORRECTED},
    "europepmc": {"query": CORRECTED, "format": "json", "pageSize": 25},
    "ctgov": {"query.term": CORRECTED, "pageSize": 50, "countTotal": "true"},
    "isrctn": {"q": drug},
}
recs, first = [], None
for src in ("pubmed", "europepmc", "ctgov", "isrctn"):
    r = srun(src, qs[src])
    first = first or r["attempted_utc"]
    recs.append(r)
    print("  %-11s %-9s n=%s" % (src, r["outcome"], r.get("n_records")))

# ---- append, never replace --------------------------------------------------------
p = os.path.join(WT, "ssot", TOPIC, "SEARCH-RECORD.json")
obj = json.load(open(p, encoding="utf-8"))
orig = [{"source": s.get("source"), "outcome": s.get("outcome"),
         "n_records": s.get("n_records")} for s in obj["databases"] if "outcome" in s]
obj["amended_search"] = {
    "_what_this_is": ("A corrected re-run under Amendment 2 of the governing protocol. It "
                      "does NOT replace the original search, which remains in 'databases' "
                      "with its own counts."),
    "authorised_by": {"protocol": GOV, "amendment": "Amendment 2 -- 2026-08-29",
                      "committed_at": sha},
    "why": ("The original query was derived from this topic's title, which is four "
            "ClinicalTrials.gov outcome-measure strings joined with '|'. Truncated, it "
            "became 'Multiple trial-declared outcomes Time' -- four generic English words "
            "naming no drug and no condition. Every source returned EXECUTED. AN EXECUTED "
            "SEARCH IS NOT A VALID ONE."),
    "original_query": obj.get("query_text"),
    "original_counts": orig,
    "corrected_query": CORRECTED,
    "corrected_query_derivation": ("the topic's declared scope (SGLT2, MACE, CVOT) and its "
                                   "two trials, EMPA-REG OUTCOME NCT01131676 and "
                                   "DECLARE-TIMI 58 NCT01730534 -- NOT its title"),
    "first_query_attempted_utc": first,
    "databases": recs,
    "three_counts": {k: sum(1 for r in recs if r["outcome"] == k)
                     for k in (EXECUTED, EMPTY, FAILED)},
    "written_utc": now(),
}
open(p, "w", encoding="utf-8", newline="").write(
    json.dumps(obj, ensure_ascii=False, indent=1))
print()
print("BOTH RESULTS NOW STAND SIDE BY SIDE:")
print("  original  %-46s %s" % (obj["query_text"][:46],
                                [(o["source"], o["n_records"]) for o in orig]))
print("  corrected %-46s %s" % (CORRECTED[:46],
                                [(r["source"], r.get("n_records")) for r in recs]))
