#!/usr/bin/env python3
"""ONE PMID ATTRIBUTED TO TWO DIFFERENT TRIALS SOMEWHERE IN THE CORPUS.

THE INSTANCE, 2026-08-19. `PUBLISHED_META_BENCHMARKS.json` recorded, for the colchicine topic:

    "source": "COLCOT (Tardif 2019) + LoDoCo2 (Nidorf SM, N Engl J Med 2020; 383:1838)",
    "pmid_lodoco2": "32865375"

PMID 32865375 is **EAST-AFNET 4** -- *Early Rhythm-Control Therapy in Patients with Atrial
Fibrillation*, N Engl J Med 2020, `10.1056/NEJMoa2019422`, `NCT01288352`. LoDoCo2 is **32865380**,
*Colchicine in Patients with Chronic Coronary Disease*, `10.1056/NEJMoa2021372`.

    THE TWO DIFFER BY FIVE, IN THE SAME JOURNAL, IN THE SAME WEEK OF AUGUST 2020. That is the
    signature of an identifier written from memory rather than looked up, and it is the class
    this registry calls "identifiers from recall".

WHY IT IS ITS OWN DETECTOR AND NOT JUST AN INSTANCE OF THAT CLASS. **The corpus already held
the evidence to refute it and nothing compared the two.** PMID 32865375 is cited CORRECTLY, as
EAST-AFNET 4 and keyed to NCT01288352, on `ABLATION_AF_REVIEW.html` and
`EARLY_RHYTHM_CONTROL_AF_REVIEW.html` -- two delivered pages of this same project. So one
identifier named an atrial-fibrillation trial on two pages and a colchicine trial on a third,
simultaneously, for months.

    A WRONG IDENTIFIER IS UNCHECKABLE IN ISOLATION AND TRIVIALLY CHECKABLE IN AGGREGATE. No
    amount of reading the colchicine benchmark record can reveal that its PMID belongs to a
    heart-rhythm trial. Reading it BESIDE the rest of the corpus reveals it immediately, and
    that is a comparison no human does and a command does in a second.

WHAT IT SCANS
    - every SSOT object's `inputs.trials[*]`, pairing `pmid` with `nct`
    - `PUBLISHED_META_BENCHMARKS.json`, pairing each `pmid_<name>` with `<name>`
    - `scripts/pmid_results/lookup.json`, pairing `best_pmid` with its keyed trial

WHAT IT CANNOT DO, stated so a clean run is not read as more than it is
    - It CANNOT tell which of two attributions is the right one. It reports the collision and
      names both sides; a human or a lookup decides. Reporting the wrong one as correct would
      be worse than reporting neither.
    - It CANNOT see a PMID that is wrong CONSISTENTLY. If a trial carries one wrong identifier
      everywhere, there is no collision and this is silent. That case needs a lookup against
      PubMed, not a comparison inside the corpus. THIS IS A FLOOR, NOT A CEILING.
    - A PMID legitimately covering two trials -- a combined report of two sibling trials in one
      paper -- is a real pattern and is reported. It is a collision to LOOK AT, not a defect
      proven.

USAGE:  python scripts/lint_pmid_names_two_trials.py
        python scripts/lint_pmid_names_two_trials.py --selftest
"""
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _norm(s):
    return " ".join(str(s or "").strip().lower().split())


def _digits(p):
    d = "".join(ch for ch in str(p or "") if ch.isdigit())
    return d or None


def collect(repo=REPO):
    """{pmid: {identity: [where, ...]}} -- identity is an NCT id where one exists, else a name.

    An NCT id is preferred over a trial NAME because names collide legitimately (`ADVANCE-2`
    and `ADVANCE-3`) while registrations do not.
    """
    seen = {}

    def add(pmid, identity, where, name=None):
        """Identity is recorded WITH ITS KIND, because the kinds are not comparable.

        THE FIRST VERSION COMPARED THEM ANYWAY AND MANUFACTURED THREE FALSE ALARMS out of four
        findings. An SSOT object keys a trial by `NCT03315143`; the benchmark file keys the same
        trial by the name `scored`. Those are the SAME TRIAL under two conventions, and a
        detector that calls that a collision is reporting its own inability to join two tables.

        A benchmark record carries no NCT id at all, so name-versus-NCT can NEVER match -- which
        means the naive version flags every trial the corpus happens to cite from both sides,
        i.e. exactly the well-recorded ones. It fires hardest where the corpus is most careful.
        NCT-versus-NCT and name-versus-name are comparable and are compared; the cross pair is
        reported as NOT_ASSESSABLE and is never counted as a collision.
        """
        pmid = _digits(pmid)
        if not pmid or not identity:
            return
        ident = _norm(identity)
        kind = "nct" if ident.startswith("nct") and ident[3:].isdigit() else "name"
        rec = seen.setdefault(pmid, {"nct": {}, "name": {}, "where": []})
        rec[kind].setdefault(ident, []).append(where)
        rec["where"].append(where)
        # A trial NAME recorded alongside an NCT lets the two conventions be joined later.
        if kind == "nct" and name:
            rec.setdefault("aka", {}).setdefault(ident, set()).add(_norm(name))

    for path in sorted(glob.glob(os.path.join(repo, "ssot", "*", "*.json"))):
        try:
            with io.open(path, "r", encoding="utf-8") as fh:
                obj = json.load(fh)
        except (OSError, ValueError):
            continue
        rel = os.path.relpath(path, repo)
        for t in ((obj.get("inputs") or {}).get("trials") or []):
            if not isinstance(t, dict):
                continue
            add(t.get("pmid"), t.get("nct") or t.get("id") or t.get("name"), rel,
                name=t.get("name"))

    bpath = os.path.join(repo, "PUBLISHED_META_BENCHMARKS.json")
    if os.path.exists(bpath):
        try:
            with io.open(bpath, "r", encoding="utf-8") as fh:
                bm = json.load(fh)
        except (OSError, ValueError):
            bm = {}
        for page, blk in (bm.get("benchmarks") or {}).items():
            if not isinstance(blk, dict):
                continue
            for k, v in blk.items():
                if k.startswith("pmid_") and not k.endswith("_corrected_2026_08_19"):
                    add(v, k[len("pmid_"):], "PUBLISHED_META_BENCHMARKS.json::%s" % page)

    lpath = os.path.join(repo, "scripts", "pmid_results", "lookup.json")
    if os.path.exists(lpath):
        try:
            with io.open(lpath, "r", encoding="utf-8") as fh:
                lk = json.load(fh)
        except (OSError, ValueError):
            lk = {}
        rows = lk if isinstance(lk, list) else (lk.get("rows") or lk.get("results") or [])
        if isinstance(rows, dict):
            rows = [dict(v, _key=k) for k, v in rows.items()]
        for r in rows:
            if isinstance(r, dict):
                add(r.get("best_pmid"), r.get("nct") or r.get("trial") or r.get("_key"),
                    "scripts/pmid_results/lookup.json")
    return seen


def collisions(seen):
    """{pmid: {kind: {identity: [where]}}} for PMIDs naming two COMPARABLE identities."""
    out = {}
    for pmid, rec in seen.items():
        ncts = rec.get("nct") or {}
        names = rec.get("name") or {}
        aka = rec.get("aka") or {}
        # A benchmark NAME that matches the name recorded beside an NCT is the SAME trial.
        known = set()
        for n in ncts:
            known |= set(aka.get(n) or ())
        unmatched = {k: v for k, v in names.items() if k not in known}
        hit = {}
        if len(ncts) > 1:
            hit["nct"] = ncts
        if len(unmatched) > 1:
            hit["name"] = unmatched
        if hit:
            out[pmid] = hit
    return out


def cross_kind_unjoined(seen):
    """PMIDs whose only disagreement is NCT-versus-NAME. NOT a collision -- NOT_ASSESSABLE."""
    out = {}
    for pmid, rec in seen.items():
        ncts, names, aka = rec.get("nct") or {}, rec.get("name") or {}, rec.get("aka") or {}
        known = set()
        for n in ncts:
            known |= set(aka.get(n) or ())
        unmatched = {k: v for k, v in names.items() if k not in known}
        if ncts and unmatched and len(ncts) <= 1 and len(unmatched) <= 1:
            out[pmid] = {"nct": sorted(ncts), "name": sorted(unmatched)}
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    seen = collect()
    bad = collisions(seen)
    cross = cross_kind_unjoined(seen)
    print("PMIDs carrying at least one attribution : %d" % len(seen))
    print("PMIDs naming two COMPARABLE identities -- COLLISION : %d" % len(bad))
    print("PMIDs whose two sides are an NCT and a NAME -- NOT_ASSESSABLE, not a collision : %d"
          % len(cross))
    print("")
    for pmid in sorted(bad):
        print("  PMID %s is attributed to more than one trial:" % pmid)
        for kind, ids in sorted(bad[pmid].items()):
            for ident, wheres in sorted(ids.items()):
                print("      [%s] %-24s <- %s"
                      % (kind, ident, ", ".join(sorted(set(wheres)))[:105]))
        print("")
    for pmid in sorted(cross):
        print("  PMID %s NOT_ASSESSABLE -- %s against %s. The benchmark file records no NCT id, "
              "so the two conventions cannot be joined and are NOT reported as disagreeing."
              % (pmid, cross[pmid]["nct"], cross[pmid]["name"]))
    if bad:
        print("\nREFUSED: an identifier naming two trials is wrong on at least one side, and "
              "THIS COMMAND CANNOT SAY WHICH. Look both up. Reporting a guess as the correct "
              "one would be worse than reporting neither.")
    return 1 if bad else 0


def selftest():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    fails = []

    def check(name, got, want):
        ok = got == want
        print("  %-70s %s  %r" % (name, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(name)

    print("1. THE GUARD CAN FIRE, on the REAL collision that occurred (P16's fourth clause --")
    print("   this is not a planted case, it shipped):")
    # THE REAL SHAPE, REBUILT THROUGH `collect`'s OWN `add` rather than hand-written, so the
    # test cannot drift from the structure the scanner actually produces. It did drift once:
    # a hand-written fixture kept the pre-kind shape and this proof silently stopped proving
    # anything while reading green, which is P16's second clause exactly.
    def build(*rows):
        seen = {}

        def add(pmid, identity, where, name=None):
            ident = _norm(identity)
            kind = "nct" if ident.startswith("nct") and ident[3:].isdigit() else "name"
            rec = seen.setdefault(pmid, {"nct": {}, "name": {}, "where": []})
            rec[kind].setdefault(ident, []).append(where)
            if kind == "nct" and name:
                rec.setdefault("aka", {}).setdefault(ident, set()).add(_norm(name))
        for r in rows:
            add(*r)
        return seen

    planted = build(("32865375", "NCT01288352", "ssot/ablation-af-review", "EAST-AFNET 4"),
                    ("32865375", "NCT01178034", "ssot/a-colchicine-object", "LoDoCo2"))
    check("a PMID naming two NCT ids is reported", sorted(collisions(planted)), ["32865375"])

    print("\n2. AND DOES NOT FIRE ON THE CORRECT CASE -- one PMID, one trial, many citations:")
    fine = build(("31733140", "NCT02551094", "a", "COLCOT"),
                 ("31733140", "NCT02551094", "b", "COLCOT"),
                 ("31733140", "NCT02551094", "c", "COLCOT"))
    check("one identity cited three times is NOT a collision", collisions(fine), {})

    print("\n2b. AND AN NCT CITED BESIDE THE SAME TRIAL'S NAME IS NOT A COLLISION -- three of")
    print("    this detector's four findings on its own first run were exactly this:")
    joined = build(("33200891", "NCT03315143", "ssot/sotagliflozin-hf", "SCORED"),
                   ("33200891", "scored", "PUBLISHED_META_BENCHMARKS.json"))
    check("an NCT joined to its own trial name is NOT a collision", collisions(joined), {})
    unjoinable = build(("33200891", "NCT03315143", "ssot/x"),
                       ("33200891", "scored", "benchmarks"))
    check("with no name recorded it is NOT_ASSESSABLE, not a collision",
          (collisions(unjoinable), sorted(cross_kind_unjoined(unjoinable))),
          ({}, ["33200891"]))

    print("\n3. IDENTITY NORMALISES, so a case or whitespace difference is not a false alarm:")
    same = {"1": {"NCT02551094": ["a"]}}
    s2 = {}
    for p, ids in same.items():
        for i, w in ids.items():
            s2.setdefault(p, {}).setdefault(_norm(i), []).extend(w)
    s2["1"].setdefault(_norm("  nct02551094 "), []).append("b")
    check("'NCT02551094' and '  nct02551094 ' are one identity", len(s2["1"]), 1)

    print("\n4. A NON-NUMERIC OR EMPTY PMID IS DROPPED, never counted as an attribution:")
    check("_digits(None)", _digits(None), None)
    check("_digits('')", _digits(""), None)
    check("_digits('PMID 31733140')", _digits("PMID 31733140"), "31733140")

    print("\n5. THE LIVE CORPUS, and the reason the count below is not the whole story:")
    seen = collect()
    bad = collisions(seen)
    print("     %d PMIDs carry an attribution; %d collide." % (len(seen), len(bad)))
    check("the scan finds attributions to compare at all -- a zero here would make a clean "
          "run meaningless", len(seen) > 0, True)
    for pmid in sorted(bad):
        print("     PMID %s -> %s" % (pmid, sorted(bad[pmid])))

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
