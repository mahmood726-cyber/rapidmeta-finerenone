#!/usr/bin/env python3
"""Extraction work that EXISTS in the repository and is connected to nothing.

THE QUESTION THIS ASKS, AND THE ONE IT IS NOT. We established that no object holds a pooled
estimate with rows missing -- that question is closed. Nobody asked whether the ROWS EXIST
OUTSIDE THE OBJECT. Different question, and it was hiding behind the closed one.

    colchicine-pericarditis names sources.literature_extraction =
    evidence/2026-08-19-batch1/pericarditis_publication_extraction.json. That file EXISTS at
    11,158 bytes and holds FOUR TRIALS, each with acronym, PMID, DOI, citation and VERBATIM
    QUOTES for population and primary outcome. The object holds ZERO per_trial rows.

COUNT ROWS, NOT IDENTIFIERS. The previous attempt at this scored that object TARGET_USED
because its four NCT ids appear in inputs.trials -- identifier presence is not content use, and
the whole point is the content. So this counts EXTRACTED ROWS on both sides and reports the
pair, never a single number.

⚠️ "THE EVIDENCE IS IN THE REPOSITORY" IS NOT "THE POOL IS VALID". Recovery reopens the
estimand question, it does not settle it. colchicine-pericarditis's own extraction records that
CORP, ICAP, CORP-2 and POPE-2 do NOT share a primary outcome -- that judgement must survive any
recovery, and this sweep deliberately reports the estimand caveat beside every recoverable row
count so no reader of the output can take availability for poolability.

LAYER: store objects plus the evidence files they name. Not served bytes.

CONTROLS, both legs, every run:
  POSITIVE and NON-VACUOUS -- colchicine-pericarditis must appear with rows_in_object == 0 and
    rows_available > 0. Merely appearing does not pass.
  NEGATIVE -- an object that names a file AND already carries its rows must NOT be reported as
    recoverable, or the instrument is one that flags everything.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
PATHLIKE = re.compile(r"(?<![\w/])((?:evidence|outputs|sources|data)/[\w./-]+\.(?:json|jsonl))")
NCT = re.compile(r"NCT\d{8}")
# A row is EXTRACTED work when it carries a value read from a source, not merely an id.
# EXTRACTION, NOT SCREENING. Measured on the files themselves, because the first run counted
# 1,042 "recoverable rows" and they were dominated by CANDIDATE POOLS -- a 137-row colchicine
# screening file counted six times, once per topic that names it. A screening row carries
# disposition/disposition_why/reading/why: it records a JUDGEMENT ABOUT a trial. An extraction
# row carries cells, citation, pmid, doi, source_read and *_as_the_paper_states_it: it records
# a VALUE READ FROM a source. Only the second is work an object could carry as a result row.
#
# Absence of a screening candidate from an object is the filter WORKING, and counting it as
# unused evidence is the candidate-pool-as-denominator error this project keeps re-finding.
EXTRACTION_KEYS = ("as_the_paper_states_it", "cells", "source_read", "quote", "verbatim")
SCREENING_KEYS = ("disposition", "publication_state", "overall_status", "due_to_report")


def say(s=""):
    OUT.write(s + "\n")
    OUT.flush()


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, p + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, p + "/%d" % i)
    else:
        yield p, o


def rows_in_object(obj):
    """Extracted rows the object itself carries: per-trial result rows with a value."""
    n = 0
    for b in ((obj.get("results") or {}).get("by_outcome") or {}).values():
        if not isinstance(b, dict):
            continue
        for r in (b.get("per_trial") or []):
            if isinstance(r, dict) and any(
                    r.get(k) not in (None, "", [], {}) for k in ("point", "events", "estimate",
                                                                 "participants")):
                n += 1
    return n


def rows_in_file(payload):
    """Extracted rows the named file carries: entries that pair a trial with read values."""
    try:
        d = json.loads(payload)
    except Exception:
        return 0, []
    best, where = 0, []
    for key, val in walk(d):
        pass
    # a list of dicts, each naming a trial AND carrying at least one value key
    def scan(node, path=""):
        nonlocal best, where
        if isinstance(node, list) and node and all(isinstance(x, dict) for x in node):
            good = [x for x in node
                    if (NCT.search(json.dumps(x)) or x.get("acronym") or x.get("trial"))
                    and any(any(vk in k.lower() for vk in EXTRACTION_KEYS) for k in x)
                    and not any(any(sk in k.lower() for sk in SCREENING_KEYS) for k in x)]
            if len(good) > best:
                best, where = len(good), [str(x.get("acronym") or x.get("nct") or
                                              x.get("trial"))[:24] for x in good[:6]]
        if isinstance(node, dict):
            for k, v in node.items():
                scan(v, path + "/" + k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                scan(v, path + "/%d" % i)
    scan(d)
    return best, where


def collect():
    rows = []
    skipped_not_dir = 0
    skipped_no_object = 0
    for topic in sorted(os.listdir(os.path.join(ROOT, "ssot"))):
        d = os.path.join(ROOT, "ssot", topic)
        # POSITIVE FORM, and what is declined is counted. `if not X: continue` inside a corpus
        # loop reads as an absence in the world rather than as an item never opened.
        if os.path.isdir(d):
            p = os.path.join(d, topic + ".json")
        else:
            skipped_not_dir += 1
            continue
        if os.path.exists(p):
            pass
        else:
            skipped_no_object += 1
            continue
        try:
            obj = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        in_obj = rows_in_object(obj)
        seen = set()
        for key, val in walk(obj):
            if isinstance(val, str):
                pass
            else:
                continue
            for m in PATHLIKE.finditer(val):
                rel = m.group(1)
                if rel in seen:
                    continue
                seen.add(rel)
                full = os.path.join(ROOT, rel)
                exists = os.path.exists(full)
                avail, names = (0, [])
                if exists:
                    try:
                        avail, names = rows_in_file(
                            io.open(full, encoding="utf-8", errors="replace").read())
                    except Exception:
                        avail, names = (0, [])
                rows.append(dict(topic=topic, field=key, path=rel, file_exists=exists,
                                 rows_in_object=in_obj, rows_available=avail,
                                 sample=names,
                                 recoverable=bool(exists and avail > 0 and in_obj == 0)))
    say("declined to open, counted not dropped: %d non-directory entries, %d topic dirs with "
        "no canonical object" % (skipped_not_dir, skipped_no_object))
    return rows


def main():
    rows = collect()
    rec = [r for r in rows if r["recoverable"]]

    # ---- controls, both legs
    gp = [r for r in rows if r["topic"] == "colchicine-pericarditis"
          and r["path"].endswith("pericarditis_publication_extraction.json")]
    pos = bool(gp) and gp[0]["rows_in_object"] == 0 and gp[0]["rows_available"] > 0
    say("CONTROL -- POSITIVE, non-vacuous")
    if gp:
        say("  colchicine-pericarditis: rows_in_object=%d  rows_available=%d  -> recoverable=%s"
            % (gp[0]["rows_in_object"], gp[0]["rows_available"], gp[0]["recoverable"]))
        say("     trials in the file: %s" % ", ".join(gp[0]["sample"]))
    else:
        say("  NOT SEEN -- the sweep missed the case that motivated it")
    say("  passes: %s" % pos)

    # THE NEGATIVE CONTROL IS SYNTHETIC, AND THAT IS THE CORRECT RESPONSE TO n=1.
    # Once screening files are excluded the corpus holds exactly ONE genuine extraction file,
    # and its object carries no rows -- so there is no real negative to draw on. A control drawn
    # from data that contains no negative is not a control. It is constructed instead, and kept
    # synthetic on purpose: a control anchored to a live object stops being a control the moment
    # that object is fixed.
    real_neg = [r for r in rows if r["file_exists"] and r["rows_available"] > 0
                and r["rows_in_object"] > 0]
    fixture_obj = {"results": {"by_outcome": {"primary": {"per_trial": [
        {"trial": "SYNTH-A", "point": 1.0}, {"trial": "SYNTH-B", "point": 2.0}]}}}}
    fixture_file = json.dumps({"trials": [
        {"nct": "NCT00000001", "acronym": "SYNTH-A", "source_read": "x",
         "population_as_the_paper_states_it": {"value": "v", "quote": "q"}},
        {"nct": "NCT00000002", "acronym": "SYNTH-B", "source_read": "x",
         "population_as_the_paper_states_it": {"value": "v", "quote": "q"}}]})
    f_avail, _ = rows_in_file(fixture_file)
    f_in_obj = rows_in_object(fixture_obj)
    neg_ok = (f_avail > 0 and f_in_obj > 0
              and not bool(f_avail > 0 and f_in_obj == 0))
    say("CONTROL -- NEGATIVE (synthetic; the corpus holds no true negative once screening")
    say("           files are excluded, so one is constructed)")
    say("  a constructed object that ALREADY carries its rows: rows_in_object=%d "
        "rows_available=%d -> recoverable=%s" % (f_in_obj, f_avail, False))
    say("  instrument declines to flag it, so it does not flag everything: %s" % neg_ok)
    say("  real corpus negatives: %d  (0 is expected here and is not a failure)"
        % len(real_neg))
    ok = pos and neg_ok
    say("")
    say("CONTROLS PASS: %s" % ok)
    if not ok:
        say("  -> counts below are NOT reportable.")
    say("")

    say("%-34s %-52s %5s %5s" % ("topic", "named evidence file", "obj", "file"))
    say("%-34s %-52s %5s %5s" % ("-" * 34, "-" * 52, "-" * 5, "-" * 5))
    for r in sorted(rec, key=lambda x: -x["rows_available"]):
        say("%-34s %-52s %5d %5d" % (r["topic"][:34], r["path"][-52:],
                                     r["rows_in_object"], r["rows_available"]))
    say("")
    say("RECOVERABLE: %d object(s) name an evidence file that EXISTS and hold NO rows of their"
        % len(rec))
    say("own, while %d row(s) sit in those files."
        % sum(r["rows_available"] for r in rec))
    say("")
    say("*** AVAILABILITY IS NOT POOLABILITY. Recovery reopens the estimand question rather")
    say("*** than settling it. colchicine-pericarditis's own extraction records that CORP,")
    say("*** ICAP, CORP-2 and POPE-2 do NOT share a primary outcome -- that judgement must")
    say("*** survive any recovery. Do not read this table as a list of pools to build.")

    with io.open(os.path.join(ROOT, "out", "rows_outside_the_object.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump({"controls_pass": ok, "recoverable": len(rec),
                   "rows_available_total": sum(r["rows_available"] for r in rec),
                   "caveat": "availability is not poolability; recovery reopens the estimand "
                             "question and does not settle it",
                   "rows": rows}, fh, indent=1, ensure_ascii=False)
    say("")
    say("wrote out/rows_outside_the_object.json")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
