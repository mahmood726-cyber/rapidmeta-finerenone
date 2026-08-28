"""The part of a gate that cannot be left to discipline.

WHY THIS FILE EXISTS. Every rule in FIX-RUN-STANDING-ORDERS that this project has broken twice
was, at the time it was broken, WRITTEN DOWN AND OWNED. A rule in a document fires only when
the author already knows which rule applies -- which is the part that goes wrong. So the rules
below are not documented here, they are ENFORCED here: a gate that does not satisfy them
cannot report a result at all.

Three enforcements, each closing a failure this project has actually suffered:

1. A NAMED POSITIVE MUST BE SEEN.   `Gate.expect_case()` registers a case the gate was built to
   find. `Gate.saw()` records that the gate's own traversal reached it. If a registered case is
   never seen, the gate exits VACUOUS -- never PASS. On 2026-08-28 three separate filters each
   hid the one case an instrument was built to find and nothing in the output said so.

2. A COUNT WITHOUT A MEASURED PRECISION IS NOT A FINDING.   A gate that calls
   `requires_control()` cannot reach PASS or FAIL until `control()` has been given a
   known-negative set and the measured false-positive rate computed. The rate prints beside
   the count, always.

3. NUMERATOR AND DENOMINATOR, AND KINDS BEFORE COUNTS.   `report()` refuses unless `kinds()`
   was called. NOT-ASSESSABLE is its own kind and is never folded into PASS.

Exit codes -- distinct on purpose, because "could not look" and "looked and found nothing"
have been conflated in this repository before and read as a pass both times:
    0  PASS      every registered case seen, no findings
    1  FAIL      findings
    2  VACUOUS   a registered case was never seen, or a required control was never supplied
    3  BROKEN    the gate could not run (missing input, parse failure, kinds never enumerated)
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys
import time

if hasattr(sys.stdout, "buffer") and os.environ.get("_GATE_WRAPPED") != "1":
    # Guarded. An unguarded module-level stdout reassignment closes a caller's wrapper on
    # import, and has killed three verifiers in this repo in one session.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.environ["_GATE_WRAPPED"] = "1"

PASS, FAIL, VACUOUS, BROKEN = 0, 1, 2, 3
VERDICT_NAME = {PASS: "PASS", FAIL: "FAIL", VACUOUS: "VACUOUS", BROKEN: "BROKEN"}


class Gate:
    def __init__(self, name, what):
        self.name = name
        self.what = what
        self._expected = {}
        self._seen = set()
        self._findings = []
        self._kinds = None
        self._control = None
        self._needs_control = False
        self._notes = []
        self._broken = []
        self._t0 = time.time()

    # -- 1. named positives -------------------------------------------------
    def expect_case(self, case_id, description):
        """A case this gate was built to find. Never reaching it is a FAILURE, not a pass."""
        self._expected[case_id] = description
        return case_id

    def saw(self, case_id):
        """Called from inside the traversal when the case is actually reached."""
        self._seen.add(case_id)

    def seen_all(self):
        return not (set(self._expected) - self._seen)

    # -- 2. known-negative control -----------------------------------------
    def requires_control(self):
        """Declare that this gate matches text, so a known-negative control is mandatory."""
        self._needs_control = True

    def control(self, n_negatives, n_false_positives, examples=()):
        """n items that MUST NOT match, and how many did."""
        if n_negatives <= 0:
            raise ValueError("a control with no negatives measures nothing")
        self._control = (int(n_negatives), int(n_false_positives), list(examples)[:5])

    def fp_rate(self):
        if not self._control:
            return None
        n, fp, _ = self._control
        return fp / n

    # -- 3. kinds, then counts ---------------------------------------------
    def kinds(self, mapping):
        """Enumerate the KINDS of item in the population before reporting its size."""
        self._kinds = dict(mapping)

    def note(self, text):
        self._notes.append(text)

    def broken(self, text):
        self._broken.append(text)

    def finding(self, key, detail, numerator=None, denominator=None):
        self._findings.append({"key": key, "detail": detail,
                               "numerator": numerator, "denominator": denominator})

    def n_findings(self):
        return len(self._findings)

    # -- report -------------------------------------------------------------
    def report(self, denominator=None, max_show=40):
        out = []
        w = out.append
        w("")
        w("=" * 78)
        w("GATE " + self.name)
        w("  " + self.what)
        w("-" * 78)

        status = PASS

        if self._broken:
            for b in self._broken:
                w("  BROKEN: " + b)
            status = BROKEN

        if self._kinds is None:
            w("  BROKEN: kinds() was never called. Kinds before counts.")
            status = BROKEN
        else:
            w("  kinds in population:")
            for k, v in self._kinds.items():
                w("      %7s  %s" % (v, k))

        if self._expected:
            missed = [c for c in self._expected if c not in self._seen]
            w("  named positives: %d/%d SEEN" % (len(self._expected) - len(missed),
                                                 len(self._expected)))
            for c, d in self._expected.items():
                w("      [%-8s] %s: %s" % ("SEEN" if c in self._seen else "NOT SEEN", c, d))
            if missed:
                w("")
                w("  VACUOUS: a case this gate was built to find was never reached by its own")
                w("  traversal. That is a filter hiding the motivating case, not a clean run.")
                if status == PASS:
                    status = VACUOUS

        if self._needs_control:
            if not self._control:
                w("")
                w("  VACUOUS: this gate matches text and no known-negative control was")
                w("  supplied. A count without a measured precision is not a finding.")
                if status == PASS:
                    status = VACUOUS
            else:
                n, fp, ex = self._control
                w("  known-negative control: %d/%d matched  (measured false-positive rate %.1f%%)"
                  % (fp, n, 100.0 * fp / n))
                for e in ex:
                    w("      false positive: " + str(e))

        for note in self._notes:
            w("  note: " + note)

        if self._findings:
            w("")
            w("  FINDINGS: %d" % len(self._findings))
            for f in self._findings[:max_show]:
                frac = " [%s/%s]" % (f["numerator"], f["denominator"]) if f["denominator"] else ""
                w("      %s%s: %s" % (f["key"], frac, f["detail"]))
            if len(self._findings) > max_show:
                w("      ... and %d more (full list in the JSON artefact)"
                  % (len(self._findings) - max_show))
            if status == PASS:
                status = FAIL
        else:
            w("")
            w("  findings: 0")

        if denominator is not None:
            w("  denominator examined: %s" % denominator)
        w("  elapsed: %.1fs" % (time.time() - self._t0))
        w("  VERDICT: " + VERDICT_NAME[status])
        w("=" * 78)
        print("\n".join(out))
        return status

    def as_json(self):
        return {
            "gate": self.name,
            "what": self.what,
            "kinds": self._kinds,
            "expected_cases": self._expected,
            "cases_seen": sorted(self._seen),
            "cases_not_seen": sorted(set(self._expected) - self._seen),
            "control": ({"negatives": self._control[0],
                         "false_positives": self._control[1],
                         "fp_rate": self.fp_rate(),
                         "examples": self._control[2]} if self._control else None),
            "notes": self._notes,
            "findings": self._findings,
        }


# --------------------------------------------------------------------------
# shared corpus access
# --------------------------------------------------------------------------
def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def topic_objects(repo=None):
    """Every SSOT topic object, by the only rule that resolves them: dir name == file stem.

    Returns (paths, kinds). The KINDS are returned rather than a bare count because a
    denominator assembled without them has changed by more than half four times here.
    """
    repo = repo or repo_root()
    paths = []
    kinds = {"topic object (ssot/<t>/<t>.json)": 0, "other json under ssot/<t>/": 0}
    for p in sorted(glob.glob(os.path.join(repo, "ssot", "*", "*.json"))):
        if os.path.basename(p)[:-5] == os.path.basename(os.path.dirname(p)):
            paths.append(p)
            kinds["topic object (ssot/<t>/<t>.json)"] += 1
        else:
            kinds["other json under ssot/<t>/"] += 1
    return paths, kinds


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def walk(x, path=""):
    """Every (path, node). Lists keep their index, so a finding can be re-found."""
    yield path, x
    if isinstance(x, dict):
        for k, v in x.items():
            for r in walk(v, path + "." + str(k)):
                yield r
    elif isinstance(x, list):
        for i, v in enumerate(x):
            for r in walk(v, path + "[" + str(i) + "]"):
                yield r


def topic_id(path):
    return os.path.basename(os.path.dirname(path))


# ---------------------------------------------------------------------------
# SHARED APPEND-ONLY ARTEFACTS
# ---------------------------------------------------------------------------
APPEND_ONLY = ("out/ESCALATIONS.jsonl",)


def append_only(path, lines):
    """Append to a shared log and REFUSE to truncate it.

    WHY THIS EXISTS. On 2026-08-28 this lane wrote `cat > out/ESCALATIONS.jsonl` instead of
    `>>` and destroyed 18 records written by other lanes. It was recovered from git and caught
    only because `git status` said MODIFIED rather than ADDED -- luck, not a gate. It was the
    THIRD shared artefact silently damaged by a routine operation that night.

    A shared append-only log is exactly the file a lane will clobber, because every lane
    creates it the same way on first use and `>` is one character from `>>`.
    """
    before = os.path.getsize(path) if os.path.exists(path) else 0
    with open(path, "a", encoding="utf-8") as fh:
        for line in lines:
            fh.write(line.rstrip(chr(10)) + chr(10))
    after = os.path.getsize(path)
    if after < before:
        raise IOError("%s SHRANK from %d to %d bytes on an append. Refusing to continue."
                      % (path, before, after))
    return before, after


def assert_append_only_intact(gate, repo=None):
    """A shared append-only artefact must never hold FEWER RECORDS than its committed version.

    LINES ARE THE CONTRACT; BYTES ARE ONLY A SIGNAL. The first version compared raw bytes and
    immediately false-positived on this very file: normalising CRLF to LF removed 24 bytes
    while the record count stayed at 27, and the gate reported "an append-only artefact
    shrank, which means a routine `>` destroyed another lane's records". That is a false
    accusation, and it ran in the direction of ACCUSING THE SUBJECT -- the dangerous
    direction, because a check that is wrong toward "you broke something" reads as the check
    working.

    So: the record count must never fall, and bytes are compared only after normalising line
    endings on BOTH sides, where a drop is a NOTE rather than a finding.
    """
    import subprocess
    crlf = (chr(13) + chr(10)).encode()
    lf = chr(10).encode()
    repo = repo or repo_root()
    for rel in APPEND_ONLY:
        full = os.path.join(repo, rel)
        if not os.path.exists(full):
            gate.note("append-only artefact %s is absent; nothing to compare." % rel)
            continue
        with open(full, "rb") as fh:
            now_norm = fh.read().replace(crlf, lf)
        now_lines = len([x for x in now_norm.split(lf) if x.strip()])
        try:
            head_raw = subprocess.run(["git", "show", "HEAD:" + rel], cwd=repo,
                                      capture_output=True, check=True).stdout
        except Exception:
            gate.note("%s is not in HEAD yet; no baseline to compare." % rel)
            continue
        head_norm = head_raw.replace(crlf, lf)
        head_lines = len([x for x in head_norm.split(lf) if x.strip()])

        if now_lines < head_lines:
            gate.finding("SHARED-ARTEFACT-LOST-RECORDS",
                         "%s holds %d records against %d at HEAD. An append-only artefact "
                         "lost records, which means a routine `>` destroyed another lane's "
                         "work. Recover with: git show HEAD:%s"
                         % (rel, now_lines, head_lines, rel),
                         numerator=now_lines, denominator=head_lines)
        elif len(now_norm) < len(head_norm):
            gate.note("append-only %s: %d records (HEAD %d) -- record count intact, but %d "
                      "fewer bytes after newline normalisation. Content was rewritten, not "
                      "lost; read the diff."
                      % (rel, now_lines, head_lines, len(head_norm) - len(now_norm)))
        else:
            gate.note("append-only intact: %s %d records (HEAD %d), %d bytes normalised "
                      "(HEAD %d)" % (rel, now_lines, head_lines, len(now_norm),
                                     len(head_norm)))


def ratchet(gate, name, keys, what, escalated=None):
    """Freeze what exists; refuse what is new. Returns the NEW keys only.

    WHY A RATCHET RATHER THAN A HARD BLOCK. Four of these gates fail on the corpus as it
    stands, for real reasons. A hook that blocks every push on a pre-existing backlog is a
    hook that gets bypassed within a day, and a bypassed gate is worse than no gate because it
    still reads as protection. So the existing findings are FROZEN BY NAME -- listed, counted,
    and pointed at their escalation -- and the gate refuses anything that is not on that list.
    The class cannot grow; that is the property that was missing.

    RETIRED ENTRIES ARE REPORTED, NEVER REQUIRED. A frozen entry that disappears is the fix
    landing. Requiring it to stay would make the control retire itself at the moment of
    success, which is the failure this file's own named-positive rule exists to prevent.

    THE FREEZE FILE IS THE HONEST PART: a PASS from a ratcheted gate means "no new instances",
    never "clean". Both numbers print, every run.
    """
    path = os.path.join(repo_root(), "gates", name)
    now = sorted(set(keys))
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"frozen_utc": "2026-08-28", "what": what,
                       "escalated_to": escalated or "out/ESCALATIONS.jsonl",
                       "count": len(now), "keys": now}, fh, indent=1)
        gate.note("FROZEN for the first time at %d known findings. A PASS from here means "
                  "NO NEW instances, never 'clean'." % len(now))
        return []
    frozen = set(load(path)["keys"])
    new = [k for k in now if k not in frozen]
    retired = sorted(frozen - set(now))
    gate.note("ratchet: %d frozen, %d now, %d retired, %d NEW. A PASS means no new instances, "
              "not a clean corpus." % (len(frozen), len(now), len(retired), len(new)))
    if retired:
        gate.note("  retired since the freeze (remove them from %s): %s"
                  % (name, ", ".join(retired[:5])))
    return new
