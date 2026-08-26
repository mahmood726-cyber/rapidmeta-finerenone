"""REGISTRATION ORDERING -- did the protocol commit precede the search it registers?

WHY THIS EXISTS
    A protocol committed AFTER its search is not a registration. It is a record
    written once the answer was known, and at rest it looks identical to one
    written before. The only thing separating them is two timestamps and the
    willingness to compare them, so this compares them and REFUSES, rather than
    trusting that whoever built the store did it in the right order.

RE-RUNNABLE FROM NOTHING. NO CORPUS STATE.
    Every control below is SYNTHESISED into a temporary directory on each run and
    deleted afterwards. None points at anything under ssot/. This matters more
    than it sounds: a control pinned to a corpus page dies the moment that page is
    fixed or rebuilt, and it dies SILENTLY -- it either starts failing and looks
    like a regression, or it keeps passing for a reason that no longer holds.
    This file therefore states in writing that it depends on no page, no build, no
    network and no clock beyond the strings in its own fixtures. That is a claim
    you can check by deleting the corpus and running it again.

    "It happens to be re-runnable" and "it says it is re-runnable" read the same
    six months from now. This is the second one.

WHY A BARE DATE IS REFUSED AND NOT COERCED
    Sixteen stores record `date_executed: "2026-08-18"`, a bare date. A protocol
    committed at 14:05 and a search run at 09:00 the same day is a VIOLATION, and
    a bare date coerced to midnight PASSES it. Same-day is the normal case, since
    protocol and search land minutes apart. So date-only precision is refused as
    NOT ESTABLISHED rather than compared. Refusing to answer is a complete
    outcome; guessing midnight is not.

WHY THE EARLIEST QUERY TIME, NOT THE SUCCESSFUL ONE
    arni-hfref records a query attempted at 12:19:18Z that returned nothing, and a
    successful one at 12:22:39Z. Comparing against the success would move the
    first-query time three minutes later and make every ordering claim look better
    than it is. The earliest time a store admits to is the one used.

WHAT A FULL PASS DOES NOT ESTABLISH -- written in advance
    - NOT that the protocol was written before the data were seen. This compares
      two recorded timestamps, nothing more.
    - NOT that either timestamp is TRUE. Git author and committer dates are set by
      whoever makes the commit; the databases return hit counts, not times. Only a
      transparency-log entry makes a time third-party. This gate REPORTS whether
      anchors exist and does not yet refuse for their absence.
    - NOT that the search was adequate, the query sensible, or the yield real.
    - NOT anything about stores it SKIPPED. A skip is not a pass. The scope line
      exists because a bare verdict over a mostly-skipped population is precisely
      the defect this repository keeps finding in its own guards.

WHAT THE SKIPPED COUNT MEANS -- READ THIS BEFORE READING THE NUMBER
    The skipped count is NOT a limitation of this gate. It is the portfolio's first
    measure of search quality, and until this file existed there was no such
    measure at all.

    The index carries 80 green TRUSTWORTHY badges. That badge is driven by a
    fabrication-risk score over identifier hygiene -- null PMIDs, nulled NCTs --
    and touches nothing about whether a review was searched, how, or when. Nothing
    in this system previously reported whether a review's search preceded the
    protocol that registers it, because nothing compared the two.

    So when the scope line says `compared 1; skipped 154`, the 154 is the finding.
    It says: one hundred and fifty-four reviews carry no registered protocol whose
    ordering against their search can be checked by anyone.

    TWO DENOMINATORS, AND THEY ANSWER DIFFERENT QUESTIONS. Do not conflate them.
        no protocol commit recorded   -- reported by THIS gate as `skipped`. The
                                         review may have been searched; there is
                                         simply nothing to order the search against.
        no executed search at all     -- reported separately below. A different and
                                         larger problem: not "unverifiable ordering"
                                         but "no search on file".
    A store can be in one, both, or neither. Collapsing them into a single number
    would overstate one and hide the other, which is the class of error this
    repository has spent two days correcting.

EXIT CODES -- because "it passed" and "it never ran" must not look the same
    0  compared at least one store and refused none.
    1  refused at least one store.
    2  NOTHING WAS COMPARED. A non-verdict. The controls still fired, so the gate
       works; it simply had nothing to order. This is deliberately NOT 0: a gate
       that cannot reach its comparison target otherwise reports success to every
       caller that checks only the exit status, which is how a guard can sit
       green for months having examined nothing. A caller that wants to tolerate
       an empty corpus must say so explicitly by accepting 2.
"""
from __future__ import annotations
import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from instrument_controls import require_controls  # noqa: E402

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ssot")

# A leading ISO instant. Group 2 is present ONLY when a time-of-day was recorded;
# its absence is what separates "2026-08-18" from "2026-08-18T09:00:00Z".
_ISO = re.compile(
    r"(\d{4}-\d{2}-\d{2})"
    r"(?:[T ](\d{2}:\d{2}:\d{2})(\.\d+)?\s*(Z|[+-]\d{2}:?\d{2})?)?"
)

DATE_ONLY = "DATE_ONLY"

# See EXIT CODES in the module docstring. A non-verdict must not exit 0.
EXIT_NOTHING_COMPARED = 2


def parse_instant(value):
    """Return (sortable_utc_string, kind).

    kind is 'instant', DATE_ONLY, or None. DATE_ONLY is returned rather than a
    midnight guess, so no caller can accidentally compare a date against a time
    and receive a confident wrong answer.
    """
    if not isinstance(value, str):
        return None, None
    m = _ISO.search(value)
    if not m:
        return None, None
    if m.group(2) is None:
        return m.group(1), DATE_ONLY
    off = (m.group(4) or "Z").replace(":", "")
    if off in ("Z", "+0000", "-0000"):
        return m.group(1) + "T" + m.group(2) + "Z", "instant"
    sign = 1 if off[0] == "+" else -1
    delta = datetime.timedelta(hours=int(off[1:3]), minutes=int(off[3:5])) * sign
    base = datetime.datetime.strptime(
        m.group(1) + "T" + m.group(2), "%Y-%m-%dT%H:%M:%S") - delta
    return base.strftime("%Y-%m-%dT%H:%M:%SZ"), "instant"


def protocol_time(obj):
    """Earliest recorded protocol-commit instant, or (None, reason-it-is-absent)."""
    ordering = ((obj.get("registration") or {}).get("ordering") or {})
    cands = []
    value, kind = parse_instant(ordering.get("protocol_committed_utc"))
    if kind == "instant":
        cands.append(value)
    elif kind == DATE_ONLY:
        return None, "protocol commit recorded to date precision only"
    for entry in ((obj.get("protocol") or {}).get("amendment_history") or []):
        if isinstance(entry, dict) and not entry.get("post_dates_first_query"):
            value, kind = parse_instant(entry.get("committed_utc"))
            if kind == "instant":
                cands.append(value)
    if not cands:
        return None, "no protocol commit recorded"
    return min(cands), None


def earliest_query(obj):
    """Earliest time this store ADMITS a query was made -- attempt or execution."""
    times, imprecise = [], []
    ordering = ((obj.get("registration") or {}).get("ordering") or {})
    for key in ("first_query_attempted_utc", "first_query_executed_utc"):
        value, kind = parse_instant(ordering.get(key))
        if kind == "instant":
            times.append(value)
        elif kind == DATE_ONLY:
            imprecise.append("registration.ordering." + key)
    for i, db in enumerate(((obj.get("search") or {}).get("databases") or [])):
        if not isinstance(db, dict):
            continue
        for key in ("executed_utc", "date_executed", "executed_at"):
            value, kind = parse_instant(db.get(key))
            if kind == "instant":
                times.append(value)
            elif kind == DATE_ONLY:
                imprecise.append("search.databases[" + str(i) + "]." + key)
    return (min(times) if times else None), imprecise


def protocol_link_state(root, topic, obj):
    """Does the protocol this store points at actually RESOLVE?

    A protocol that exists, is anchored, and 404s to a reader is anchored to
    nothing anyone can reach. Ten live pages in this corpus cite
    `protocols/name_protocol_v1.0_2026-04-19.md` -- a template placeholder whose
    `name` token was never substituted -- and it shipped unnoticed because a 404
    looks like every other 404. Anchoring makes that worse, not better: it lends
    a broken link the authority of a log entry.

    Returns 'resolves', 'MISSING: <path>', or 'none recorded'.
    """
    refs = []
    reg = obj.get("registration") or {}
    for key in ("protocol_path", "path"):
        v = reg.get(key)
        if isinstance(v, str) and v.endswith(".md"):
            refs.append(v)
    for v in ((obj.get("protocol") or {}).get("path"),):
        if isinstance(v, str) and v.endswith(".md"):
            refs.append(v)
    default = os.path.join(root, topic, "PROTOCOL.md")
    if os.path.isfile(default):
        refs.append("ssot/" + topic + "/PROTOCOL.md")
    if not refs:
        return "none recorded"
    repo = os.path.dirname(root)
    missing = [r for r in dict.fromkeys(refs)
               if not os.path.isfile(os.path.join(repo, r.replace("/", os.sep)))]
    if missing:
        return "MISSING: " + ", ".join(missing)
    return "resolves"


def anchor_state(obj):
    reg = obj.get("registration") or {}
    a = reg.get("anchor") or reg.get("anchors") or {}
    if not isinstance(a, dict):
        return "malformed"
    have = (bool(a.get("protocol")), bool(a.get("search")))
    return {(True, True): "both", (True, False): "protocol only",
            (False, True): "search only", (False, False): "none"}[have]


def judge(obj):
    """Return (verdict, detail). Verdicts: PASS, REFUSE, SKIP."""
    ptime, why = protocol_time(obj)
    if ptime is None:
        return "SKIP", why
    qtime, imprecise = earliest_query(obj)
    if qtime is None:
        if imprecise:
            return "REFUSE", (
                "search time recorded to DATE precision only at "
                + ", ".join(imprecise[:3])
                + " -- cannot be ordered against a same-day commit")
        return "SKIP", "no search time recorded"
    if qtime < ptime:
        return "REFUSE", "search ran " + qtime + " BEFORE protocol commit " + ptime
    note = ""
    if imprecise:
        note = " (also carries date-only fields: " + ", ".join(imprecise[:2]) + ")"
    return "PASS", "protocol " + ptime + " precedes earliest query " + qtime + note


def is_topic_store(root, name):
    """POSITIVE property: a topic store IS a directory holding <name>/<name>.json.

    Stated positively and reported, never used as a silent skip. A negative guard
    inside a corpus loop decides what a sweep reaches, and an item dropped before
    it is counted leaves a denominator that looks like coverage. So a directory
    that is not a store is CARRIED as its own kind and appears in the scope line;
    it is not `continue`d past.
    """
    return os.path.isfile(os.path.join(root, name, name + ".json"))


def scan(root):
    """Return one row per DIRECTORY under `root`, plus the count of loose files.

    Every branch here is written as the positive property it means. There is no
    `continue` past an absence, because a negative guard inside a corpus loop
    decides what a sweep reaches, and an item dropped before it is counted leaves
    a denominator that reads as coverage. A directory that is not a topic store is
    carried as its own kind and named in the scope line.

    The population IS the set of directories. Loose files beside them -- the topic
    data modules, the appliers -- are not candidate stores; they are counted and
    reported so the arithmetic over the listing is complete rather than assumed.
    """
    rows, loose = [], 0
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            if os.path.isdir(os.path.join(root, name)):
                if is_topic_store(root, name):
                    path = os.path.join(root, name, name + ".json")
                    try:
                        with open(path, encoding="utf-8") as fh:
                            obj = json.load(fh)
                    except Exception as exc:
                        rows.append((name, "REFUSE",
                                     "unreadable: " + type(exc).__name__, "n/a", False, "n/a"))
                    else:
                        verdict, detail = judge(obj)
                        qtime, imprecise = earliest_query(obj)
                        has_search = bool(qtime) or bool(imprecise)
                        rows.append((name, verdict, detail, anchor_state(obj), has_search,
                                     protocol_link_state(root, name, obj)))
                else:
                    rows.append((name, "NOT_A_STORE",
                                 "directory holds no " + name + ".json", "n/a", False, "n/a"))
            else:
                loose += 1
    return rows, loose


def report(rows, label, loose=0):
    total = len(rows)
    passed = [r for r in rows if r[1] == "PASS"]
    refused = [r for r in rows if r[1] == "REFUSE"]
    skipped = [r for r in rows if r[1] == "SKIP"]
    not_store = [r for r in rows if r[1] == "NOT_A_STORE"]
    reasons = {}
    for r in skipped:
        reasons[r[2]] = reasons.get(r[2], 0) + 1
    bits = "; ".join(str(v) + " " + k
                     for k, v in sorted(reasons.items(), key=lambda x: -x[1]))
    print("[" + label + "] directories " + str(total)
          + "; compared " + str(len(passed) + len(refused))
          + "; PASS " + str(len(passed))
          + "; REFUSED " + str(len(refused)) + "; skipped " + str(len(skipped))
          + ((" (" + bits + ")") if bits else "")
          + "; not a topic store " + str(len(not_store))
          + "; loose files (not candidates) " + str(loose))
    for name, _v, detail, _a, _h, _l in not_store:
        print("    not-a-store  " + name + ": " + detail)
    stores = [r for r in rows if r[1] != "NOT_A_STORE"]
    no_search = [r for r in stores if not r[4]]
    print("")
    print("  WHAT THESE NUMBERS MEAN -- the skipped count is not a limitation of this")
    print("  gate, it is the portfolio's first measure of search quality. Until this")
    print("  file existed nothing compared a search against the protocol registering it.")
    print("  TWO DENOMINATORS, DIFFERENT QUESTIONS, NOT INTERCHANGEABLE:")
    print("    " + str(len(skipped)) + " of " + str(len(stores))
          + " stores have NO PROTOCOL COMMIT to order a search against")
    print("    " + str(len(no_search)) + " of " + str(len(stores))
          + " stores hold NO EXECUTED SEARCH at all")
    broken = [r for r in stores if isinstance(r[5], str) and r[5].startswith("MISSING")]
    print("    " + str(len(broken)) + " of " + str(len(stores))
          + " stores point at a protocol file that DOES NOT RESOLVE")
    for r in broken[:10]:
        print("        broken link  " + r[0] + ": " + r[5])
    print("  A store may be in one, both or neither. Collapsing them overstates one")
    print("  and hides the other.")
    for name, _v, detail, _a, _h, _l in refused:
        print("    REFUSED  " + name + ": " + detail)
    for name, _v, detail, anch, _h, link in passed:
        print("    pass     " + name + ": " + detail + "  [anchors: " + anch
              + "; protocol link: " + link + "]")
    return len(passed) + len(refused), len(refused)


# ---------------------------------------------------------------------------------
# CONTROLS. Synthesised here, in a temp tree, deleted afterwards. Pinned to no page.
# ---------------------------------------------------------------------------------
def _store(protocol_utc, query_utc, query_key="executed_utc"):
    return {
        "registration": {"ordering": {"protocol_committed_utc": protocol_utc}},
        "search": {"databases": [{"database": "synthetic", query_key: query_utc}]},
    }


FIXTURES = {
    # MUST REFUSE: the search ran one minute BEFORE the protocol was committed.
    "__control_violation": (
        _store("2026-01-01T12:00:00Z", "2026-01-01T11:59:00Z"), "REFUSE"),
    # MUST PASS: the search ran one minute after.
    "__control_clean": (
        _store("2026-01-01T12:00:00Z", "2026-01-01T12:01:00Z"), "PASS"),
    # MUST REFUSE: same day, but the search time is a BARE DATE. Coercing it to
    # midnight would PASS this, which is the entire reason it is here.
    "__control_date_only": (
        _store("2026-01-01T12:00:00Z", "2026-01-01", "date_executed"), "REFUSE"),
    # MUST REPORT A BROKEN LINK: the store points at a protocol file that is not
    # there. Without this fixture the link check is VACUOUS -- across the whole
    # corpus it currently returns "resolves" or "none recorded" and can never fire,
    # which is indistinguishable from a corpus with no broken links. Ten live pages
    # in this repository cite a template placeholder that 404s, so the failure mode
    # is real and unobserved, not hypothetical.
    "__control_broken_protocol_link": (
        {"registration": {"protocol_path": "ssot/__control_broken_protocol_link/NOPE.md",
                          "ordering": {"protocol_committed_utc": "2026-01-01T12:00:00Z"}},
         "search": {"databases": [
             {"database": "synthetic", "executed_utc": "2026-01-01T12:01:00Z"}]}}, "PASS"),
    # MUST SKIP: nothing to compare against. A skip must never read as a pass.
    "__control_no_protocol": (
        {"search": {"databases": [
            {"database": "synthetic", "executed_utc": "2026-01-01T12:01:00Z"}]}}, "SKIP"),
}


# ---------------------------------------------------------------------------------
# REAL-CORPUS CONTROLS, PINNED TO AN IMMUTABLE COMMIT.
#
# Two rules meet here and they pull opposite ways. `instrument_controls` requires a
# POSITIVE and a NEGATIVE drawn from REAL corpus items, because the failure mode it
# was built for is over-flagging real pages, and only a real page catches that. The
# separate rule this file is built under says a control must never be pinned to a
# corpus page, because such a control dies silently the moment the page is fixed.
#
# Both are right. The resolution is the one the register itself records: a control
# must be synthetic OR PINNED TO AN IMMUTABLE VERSION. These are real corpus items
# read with `git show <sha>:<path>`, so the bytes cannot move under the control. The
# synthetic fixtures above stay, because they prove the MECHANISM -- refuse, pass,
# refuse-a-bare-date, skip -- which no single real page exercises.
#
# If git cannot produce the pinned bytes, this RAISES. A control that quietly does
# not run is the thing the whole file is about.
# ---------------------------------------------------------------------------------
PIN = "ba3a641d679ffec384cb455ce7700fac38ba3e9b"  # on main, public, immutable

# Answer established INDEPENDENTLY of this gate: protocol commit 973f031 has git
# committer time 2026-08-12T11:27:47Z (verified against `git log`), and the search
# capture records the first query ATTEMPT at 12:19:18Z. Commit precedes attempt, so
# the established answer is PASS. Nothing here is inferred by the logic under test.
POSITIVE_TOPIC = "arni-hfref"
# A store with no protocol commit at all. It must come back SKIP. Refusing it would
# accuse 154 unregistered topics of a violation they have not committed, which is
# over-flagging in the direction that matters.
NEGATIVE_TOPIC = "bempedoic-acid-review"


def _pinned_store(sha, topic):
    """Read <topic>.json as it stood at `sha`. Raises if git cannot supply it."""
    path = "ssot/" + topic + "/" + topic + ".json"
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proc = subprocess.run(["git", "-C", repo, "show", sha + ":" + path],
                          capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(
            "REFUSED: cannot read the pinned control " + path + " at " + sha[:9]
            + " (" + proc.stderr.decode("utf-8", "replace").strip()[:160] + "). The "
            "controls did not run, so no corpus verdict is reported. A control that "
            "silently does not run is indistinguishable from one that passed.")
    return json.loads(proc.stdout.decode("utf-8"))


def corpus_controls():
    pos_verdict = judge(_pinned_store(PIN, POSITIVE_TOPIC))[0]
    neg_verdict = judge(_pinned_store(PIN, NEGATIVE_TOPIC))[0]
    require_controls(
        "registration_ordering_gate",
        positive=(POSITIVE_TOPIC + " @" + PIN[:9] + " (ordering established from git)",
                  pos_verdict, "PASS"),
        negative=(NEGATIVE_TOPIC + " @" + PIN[:9] + " (no protocol commit)",
                  neg_verdict, "REFUSE"),
    )


def self_test():
    """Prove the gate can BOTH refuse and pass before any corpus number is believed."""
    tmp = tempfile.mkdtemp(prefix="ordering_gate_fixtures_")
    try:
        for name, (obj, _expected) in FIXTURES.items():
            d = os.path.join(tmp, name)
            os.makedirs(d)
            with open(os.path.join(d, name + ".json"), "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
        rows = {r[0]: r for r in scan(tmp)[0]}
        ok = True
        print("CONTROLS (synthetic, temp tree, deleted after this run):")
        for name, (_obj, expected) in FIXTURES.items():
            got = rows.get(name, (name, "MISSING", "fixture not scanned", "n/a", False, "n/a"))
            good = got[1] == expected
            extra = ""
            if name == "__control_broken_protocol_link":
                # the verdict is not what this fixture is for -- the LINK state is.
                link_ok = isinstance(got[5], str) and got[5].startswith("MISSING")
                good = good and link_ok
                extra = "  link=" + str(got[5])
            ok = ok and good
            print("    " + ("ok  " if good else "FAIL") + " " + name
                  + ": expected " + expected + ", got " + got[1] + " -- " + got[2] + extra)
        return ok, len(FIXTURES)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    controls_ok, n_fixtures = self_test()
    if not controls_ok:
        raise SystemExit(
            "ABORTED: the gate failed its own controls. No corpus verdict is reported, "
            "because a gate that cannot refuse a planted violation has not been shown "
            "to check anything.")
    print("    controls: " + str(n_fixtures) + "/" + str(n_fixtures)
          + " behaved as specified -- this gate can refuse AND pass.\n")
    corpus_controls()
    print()
    corpus_rows, n_loose = scan(ROOT)
    compared, n_refused = report(corpus_rows, "ssot", n_loose)
    if n_refused:
        raise SystemExit(1)
    if compared == 0:
        print("\nNOTE: 0 stores were COMPARED. That is a NON-VERDICT, not a pass. The gate "
              "ran and its controls fired, so it works; the corpus simply carries nothing "
              "it can order yet. Exiting " + str(EXIT_NOTHING_COMPARED) + " so that a caller "
              "can tell this apart from a pass -- see EXIT CODES in the module docstring.")
        raise SystemExit(EXIT_NOTHING_COMPARED)
    raise SystemExit(0)
