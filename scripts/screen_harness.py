"""SCREENING HARNESS. Rebuilt 2026-08-16 after two failed runs.

WHAT FAILED, AND WHY THIS IS A REDO RATHER THAN A PATCH
  Run 1  crashed the Codex Windows sandbox printing a large Unicode preview of a
         334 KB abstract file: orchestrator_helper_exit_nonzero -1073741502.
         Its own recovery was to NARROW THE TASK -- "switching to targeted phrase
         checks rather than dumping all abstracts" -- which would have produced
         keyword matching over some records, presented as a screening log.
  Run 2  drifted onto F:\\E156\\rewrite-workbook.txt, a file with nothing to do
         with the task, then died writing to F:\\tmp\\ outside its working dir.

  Neither produced a decision. The dangerous one is run 1: a screener under
  pressure silently reducing its own scope, with the artefact still shaped like a
  screening log. Every assertion below exists to make that specific failure loud.

THE FIVE ASSERTIONS -- each can fail, and each is demonstrated failing in --selftest
  A1 RECORD COUNT   parsed records must equal the retrieval count. A parser that
                    silently merges two records and drops one produced 67 of 68
                    here, and the tally looked plausible. Keyed on PMID, asserted
                    against the esearch id set, not against a hand-counted number.
  A2 RECALL         HARD PRECONDITION, checked BEFORE any screening. The search
                    must retrieve the trials already in the object. A CTgov query
                    returned NCT06618976 and NCT05562063 -- neither SOLOIST-WHF nor
                    SCORED, the two trials the review pools. A search that misses
                    known-included trials fails before screening starts.
  A3 COVERAGE       every retrieved record must carry a decision. Fewer decisions
                    than records is a partial screen, and a partial screen that
                    reads complete is the artefact we are trying not to produce.
  A4 NO DRIFT       the run declares which files it read. Reading anything outside
                    the declared scope is a FAILURE, not a warning.
  A5 WRITES IN CWD  every output path must be inside the working directory.

WHAT A FULL PASS DOES NOT ESTABLISH -- in advance, as standing practice
  - NOT that the screening DECISIONS are correct. This checks that every record was
    decided, by a declared screener, from declared inputs. Whether the judgement is
    right is what the second screener and adjudication are for.
  - NOT that the search was complete (see search_recall_gate: recall against your
    own included set is a floor, not a ceiling).
  - NOT that the included set is the right one for the question.
"""
from __future__ import annotations
import json, os, re, sys, io

# Reassign stdout ONLY when run as a script. At import this closes the caller's
# own wrapper -- a second TextIOWrapper over the same buffer collects the first and
# shuts the underlying stream, so the importer dies on
# "ValueError: I/O operation on closed file" at its next print. That is the
# module-level-stdout trap this project already has on record for breaking pytest
# collection; a harness meant to be imported must not spring it.
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


class ScreenFailure(Exception):
    pass


def parse_records(raw_path, expected_ids):
    """Slice on PMID, never on ordinal numbering. A1."""
    t = open(raw_path, encoding="utf-8", errors="replace").read()
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"PMID:\s*(\d+)", t)]
    recs, prev = [], 0
    for pos, pm in marks:
        recs.append({"pmid": pm, "body": re.sub(r"\s+", " ", t[prev:pos + 30])})
        prev = pos + 30
    got = [r["pmid"] for r in recs]
    if set(got) != set(expected_ids):
        miss, extra = sorted(set(expected_ids) - set(got)), sorted(set(got) - set(expected_ids))
        raise ScreenFailure("A1 RECORD COUNT: parsed %d, retrieval said %d. missing=%s extra=%s"
                            % (len(got), len(expected_ids), miss[:5], extra[:5]))
    if len(got) != len(set(got)):
        raise ScreenFailure("A1 RECORD COUNT: duplicate pmids in parse")
    return recs


def assert_recall(corpus_text, trials):
    """A2. HARD PRECONDITION -- runs before screening, not after."""
    missed = []
    for t in trials:
        nct, name = t.get("nct"), t.get("name")
        if not ((nct and nct in corpus_text) or (name and len(name) > 2 and name in corpus_text)):
            missed.append("%s/%s" % (name, nct))
    if missed:
        raise ScreenFailure("A2 RECALL: the search does not retrieve trials the object "
                            "already includes: %s. A search that misses known-included "
                            "trials is not a search strategy." % missed)
    return len(trials)


def assert_coverage(recs, decisions):
    """A3."""
    undecided = [r["pmid"] for r in recs if r["pmid"] not in decisions]
    if undecided:
        raise ScreenFailure("A3 COVERAGE: %d of %d records carry no decision: %s"
                            % (len(undecided), len(recs), undecided[:6]))
    return len(decisions)


def assert_no_drift(files_read, allowed_dir):
    """A4."""
    ad = os.path.abspath(allowed_dir).lower()
    out = [f for f in files_read if not os.path.abspath(f).lower().startswith(ad)]
    if out:
        raise ScreenFailure("A4 DRIFT: the run read files outside its scope: %s. A lane "
                            "reading unrelated files while claiming to screen is producing "
                            "output that looks like work." % out[:4])
    return len(files_read)


def assert_writes_in_cwd(paths, cwd):
    """A5."""
    c = os.path.abspath(cwd).lower()
    out = [p for p in paths if not os.path.abspath(p).lower().startswith(c)]
    if out:
        raise ScreenFailure("A5 WRITES: output outside the working directory: %s" % out[:4])
    return len(paths)


def selftest() -> int:
    """Every assertion demonstrated FAILING, then passing. A harness whose
    self-test cannot fail is the thing this project has spent a day removing."""
    ok = True

    def expect_fail(label, fn):
        nonlocal ok
        try:
            fn()
        except ScreenFailure as e:
            print("  %-34s FAILS as it must: %s" % (label, str(e)[:96]))
            return
        print("  %-34s DID NOT FAIL -- assertion is inert" % label)
        ok = False

    def expect_pass(label, fn):
        nonlocal ok
        try:
            fn()
            print("  %-34s passes on the good case" % label)
        except ScreenFailure as e:
            print("  %-34s FAILED on the good case: %s" % (label, e))
            ok = False

    base = r"F:\E156\outputs\pilot-sotagliflozin"
    raw = os.path.join(base, "abstracts.txt")
    rec = json.loads(open(os.path.join(base, "SEARCH_sotagliflozin.json"),
                          encoding="utf-8", errors="replace").read())
    ids = rec["pubmed"]["ids"]
    corpus = open(raw, encoding="utf-8", errors="replace").read()

    print("A1 record count")
    expect_fail("  one id withheld from the set", lambda: parse_records(raw, ids[:-1]))
    expect_pass("  full id set", lambda: parse_records(raw, ids))

    print("A2 recall (hard precondition)")
    expect_fail("  ctgov arm only -- the real miss",
                lambda: assert_recall(json.dumps(rec["ctgov"]),
                                      [{"nct": "NCT03521934", "name": "SOLOIST-WHF"},
                                       {"nct": "NCT03315143", "name": "SCORED"}]))
    expect_pass("  pubmed corpus",
                lambda: assert_recall(corpus, [{"nct": "NCT03521934", "name": "SOLOIST-WHF"},
                                               {"nct": "NCT03315143", "name": "SCORED"}]))

    recs = parse_records(raw, ids)
    print("A3 coverage")
    expect_fail("  decisions for all but three",
                lambda: assert_coverage(recs, {r["pmid"]: "INCLUDE" for r in recs[:-3]}))
    expect_pass("  a decision per record",
                lambda: assert_coverage(recs, {r["pmid"]: "EXCLUDE" for r in recs}))

    print("A4 drift")
    expect_fail("  read rewrite-workbook.txt (run 2)",
                lambda: assert_no_drift([raw, r"F:\E156\rewrite-workbook.txt"], base))
    expect_pass("  in-scope reads only", lambda: assert_no_drift([raw], base))

    print("A5 writes in cwd")
    expect_fail("  write to F:/tmp (run 2)",
                lambda: assert_writes_in_cwd([r"F:\tmp\sota_parsed_records.jsonl"], base))
    expect_pass("  write inside cwd",
                lambda: assert_writes_in_cwd([os.path.join(base, "SCREEN_A.tsv")], base))

    print("\n-> SELFTEST PASS" if ok else "\n-> SELFTEST FAILED (an assertion is inert)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else 0)
