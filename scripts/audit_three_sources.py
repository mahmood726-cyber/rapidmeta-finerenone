"""Which of the three required sources does each store actually hold a query for?

READ THE STORES, NOT THE PAGES. The question is whether the search RAN, which only the
object can answer; a page can render empty over a sound object and can render confidently
over an empty one.

KEY PRESENCE, NOT TRUTHINESS. Every lookup below tests `"k" in d` before reading. `.get()`
conflates an ABSENT key with a key present and null, and those mean different things here:
absent means nobody recorded a search, null means someone recorded that there wasn't one.
That exact idiom voided a cross-family judgement earlier tonight.

VOCABULARY IS DERIVED, NOT TYPED. There is no store-side resolver in this repository -- the
only source vocabulary is page-side (`l.source === 'pubmed'` in fix_prisma_svg_zeros.py) and
it does not classify the store's `database` strings. So rather than retype a guess list, the
distinct `database` values are enumerated FROM THE CORPUS and printed in full, and the
classifier is applied to that enumeration where it can be checked by eye. A hand-typed path
list produced a false "missing snapshot" report a few hours ago; this is the same failure
one field over.
"""
import io, json, os, re, sys
from collections import Counter

sys_path_added = os.path.dirname(os.path.abspath(__file__))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
S = r"F:\claude-temp\claude\C--Users-mahmo\f842b4e4-f3de-4ce2-83d8-0adf7aa7cfb1\scratchpad"
SSOT = os.path.join(S, "main-wt", "ssot")

sys.path.insert(0, sys_path_added)
from instrument_controls import require_controls  # noqa: E402

# Applied to the DERIVED enumeration below, which is printed so the mapping is auditable.
CLASSIFY = [
    ("pubmed", re.compile(r"pubmed|medline|e-?utilit|esearch|entrez", re.I)),
    ("openalex", re.compile(r"openalex|open\s*alex", re.I)),
    ("ctgov", re.compile(r"clinicaltrials|ct\.gov|ctgov|aact", re.I)),
]
QUERY_KEYS = ("query_as_executed", "query", "query_string", "query_parameters")


def classify(name):
    hits = [k for k, rx in CLASSIFY if rx.search(name or "")]
    return hits


def audit():
    rows, vocab, unclassified = [], Counter(), Counter()
    for topic in sorted(os.listdir(SSOT)):
        d = os.path.join(SSOT, topic)
        f = os.path.join(d, topic + ".json")
        if not os.path.isdir(d) or not os.path.isfile(f):
            continue
        obj = json.load(open(f, encoding="utf-8"))

        # --- key presence at every level, never .get() truthiness ---------------
        # Written as POSITIVE branches. Every topic reaches a row and NOTHING is
        # `continue`d past: a negative guard inside a corpus loop decides what a sweep
        # reaches, and an item dropped before it is counted leaves a denominator that
        # reads as coverage. The distinction between the four absent-ish states below
        # IS the finding here, so each one is named rather than collapsed.
        blank = {"pubmed": False, "openalex": False, "ctgov": False, "n_db": 0}
        if "search" in obj:
            search = obj["search"]
            if isinstance(search, dict):
                if "databases" in search:
                    dbs = search["databases"]
                    if isinstance(dbs, list):
                        found = {"pubmed": False, "openalex": False, "ctgov": False}
                        n_with_query = 0
                        for entry in dbs:
                            if isinstance(entry, dict):
                                name = entry["database"] if "database" in entry else ""
                                vocab[name] += 1
                                has_query = any(k in entry for k in QUERY_KEYS)
                                if has_query:
                                    n_with_query += 1
                                tags = classify(name)
                                if tags:
                                    # a source counts only if a QUERY was recorded for
                                    # it, not merely a name
                                    for t in tags:
                                        if has_query:
                                            found[t] = True
                                else:
                                    unclassified[name] += 1
                            else:
                                # a non-dict entry is its own kind, counted and named
                                unclassified["<non-dict databases entry>"] += 1
                        rows.append({"topic": topic, "state": "databases present",
                                     "n_db": len(dbs), "n_with_query": n_with_query,
                                     **found})
                    else:
                        rows.append({"topic": topic,
                                     "state": "databases KEY PRESENT BUT NOT A LIST",
                                     **blank})
                else:
                    rows.append({"topic": topic,
                                 "state": "search PRESENT, NO databases KEY", **blank})
            else:
                rows.append({"topic": topic,
                             "state": "search KEY PRESENT BUT NOT A DICT", **blank})
        else:
            rows.append({"topic": topic, "state": "NO search KEY", **blank})
    return rows, vocab, unclassified


def controls(rows):
    """Known answers, checked before any corpus figure is printed.

    POSITIVE -- iv-iron-hf holds ClinicalTrials.gov and NOT PubMed. That answer was
    established INDEPENDENTLY of this code: an external reviewer reported it from the
    page before this instrument existed. If the classifier cannot reproduce the one
    answer somebody else already found, it is not trusted for the other 154.

    NEGATIVE -- bempedoic-acid-review must NOT come back holding nothing. It holds a
    PubMed query and a ClinicalTrials query in its store. Over-reporting absence is this
    instrument's failure direction: the headline is a count of what is MISSING, so a
    classifier that fails to recognise a source it should recognise makes the corpus
    look worse than it is, and the number would be quoted. A detector that can only say
    "missing" is not a detector.

    THE FIRST NEGATIVE CONTROL WAS finerenone-cv AND IT FAILED, CORRECTLY. That topic
    was searched tonight -- PubMed and ClinicalTrials, both anchored -- and the store
    still reads NO search KEY, because the records went into a sidecar
    SEARCH-RECORD.json and never reached the store's `search` key. The classifier was
    right and my assumption was wrong. The control is repointed at a store-backed topic
    so that it tests the classifier rather than the wiring, and the wiring gap it
    exposed is recorded rather than absorbed: all five topics searched tonight are
    invisible to this audit, to build_to_standard.py, and to the page's Search tab.
    """
    idx = {r["topic"]: r for r in rows}
    pos = idx.get("iv-iron-hf", {})
    pos_actual = (pos.get("ctgov"), pos.get("pubmed"), pos.get("openalex"))
    neg = idx.get("bempedoic-acid-review", {})
    neg_actual = not (neg.get("pubmed") or neg.get("ctgov") or neg.get("openalex"))
    require_controls(
        "audit_three_sources",
        positive=("iv-iron-hf holds ctgov, not pubmed, not openalex "
                  "(established by an external review, not by this code)",
                  pos_actual, (True, False, False)),
        negative=("bempedoic-acid-review reported as holding NO source at all",
                  neg_actual, True))


if __name__ == "__main__":
    rows, vocab, unclassified = audit()
    controls(rows)
    n = len(rows)
    print("DERIVED VOCABULARY -- every distinct `database` string in the corpus")
    print("(printed in full so the classification can be checked by eye)\n")
    for name, k in vocab.most_common():
        print("  x%-3d [%s]  %s" % (k, ",".join(classify(name)) or "UNCLASSIFIED", name[:96]))
    if unclassified:
        print("\n  UNCLASSIFIED STRINGS (%d distinct) -- these are counted in NO source"
              % len(unclassified))
        for name, k in unclassified.most_common():
            print("    x%-3d %s" % (k, name[:96] or "<empty>"))

    pm = [r for r in rows if r["pubmed"]]
    oa = [r for r in rows if r["openalex"]]
    ct = [r for r in rows if r["ctgov"]]
    all3 = [r for r in rows if r["pubmed"] and r["openalex"] and r["ctgov"]]
    none = [r for r in rows if not (r["pubmed"] or r["openalex"] or r["ctgov"])]
    print("\n" + "=" * 68)
    print("THE SPLIT, DENOMINATOR %d TOPIC STORES" % n)
    print("  hold a PubMed query          : %3d  (%d%%)" % (len(pm), 100 * len(pm) // n))
    print("  hold an OpenAlex query       : %3d  (%d%%)" % (len(oa), 100 * len(oa) // n))
    print("  hold a ClinicalTrials query  : %3d  (%d%%)" % (len(ct), 100 * len(ct) // n))
    print("  hold ALL THREE               : %3d  (%d%%)" % (len(all3), 100 * len(all3) // n))
    print("  hold NONE of the three       : %3d  (%d%%)" % (len(none), 100 * len(none) // n))
    print()
    states = Counter(r["state"] for r in rows)
    print("  WHY none -- and an absent key is not the same as a null one:")
    for k, v in states.most_common():
        print("    %3d  %s" % (v, k))
    print("\n  CT.gov ONLY (the IV-iron pattern): %d"
          % len([r for r in rows if r["ctgov"] and not r["pubmed"] and not r["openalex"]]))
    print("  PubMed + CT.gov, no OpenAlex     : %d"
          % len([r for r in rows if r["pubmed"] and r["ctgov"] and not r["openalex"]]))
    json.dump(rows, open(os.path.join(S, "source_audit.json"), "w", encoding="utf-8"),
              indent=1)
    print("\nwrote source_audit.json")

    # ----------------------------------------------------------------------------
    # EXIT CONTRACT. lint_gate_can_fail refused the first version because it returns
    # a verdict and could only ever exit 0, and it was right: a file that reports on
    # conformance without being able to refuse is a survey wearing a gate's clothes.
    #
    # The standard is THREE SOURCES: PubMed, OpenAlex, ClinicalTrials.gov.
    #   exit 0  every topic in scope holds a query for all three
    #   exit 1  at least one does not -- the corpus does not meet the standard
    #   exit 2  no topic stores were found at all: a NON-VERDICT, not a pass
    # `--survey` reports and exits 0, for when you want the numbers without a verdict.
    #
    # Today this exits 1 with 155 non-conforming, which is the true state and is
    # exactly what the gate is for. It will keep failing until the searches are run,
    # and that is the point: the number cannot quietly become normal.
    # ----------------------------------------------------------------------------
    if not rows:
        print("\nNO TOPIC STORES FOUND -- non-verdict, not a pass.")
        raise SystemExit(2)
    if "--survey" in sys.argv:
        raise SystemExit(0)
    missing = [r for r in rows
               if not (r["pubmed"] and r["openalex"] and r["ctgov"])]
    if missing:
        print("\nREFUSED: %d of %d topics do not hold a query for all three required "
              "sources." % (len(missing), len(rows)))
        print("A page carrying the words 'systematic review' over a store with no "
              "search key is the claim this gate exists to refuse.")
        for r in missing[:8]:
            have = [k for k in ("pubmed", "openalex", "ctgov") if r[k]]
            print("    " + r["topic"] + ": holds " + (", ".join(have) or "none")
                  + "  [" + r["state"] + "]")
        if len(missing) > 8:
            print("    ... and %d more (all in source_audit.json)" % (len(missing) - 8))
        raise SystemExit(1)
    print("\nALL %d topics hold a query for all three required sources." % len(rows))
    raise SystemExit(0)
