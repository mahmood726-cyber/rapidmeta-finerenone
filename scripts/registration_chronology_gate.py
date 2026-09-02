"""REGISTRATION CHRONOLOGY GATE -- a protocol cannot be prospective to work already done.

THE DEFECT. ARNI's page claims prospective registration. Its object holds
`search.databases[*].executed_utc` = 2026-08-12T12:22:39Z, while
`screening.records[*].checked_on` reads 2026-08-09 on five records and
2026-08-10 on four, and `built` = 2026-08-09. Nine of thirteen screening
decisions predate the protocol commit at 2026-08-12T11:27:47Z, and the whole
object was built three days before it.

WHY THE OBJECT'S OWN CHRONOLOGY CHECK MISSED IT. It compared two timestamps --
the protocol commit and the first executed query -- found them in the right
order, and recorded `verdict: established`. Both are metadata. The object even
says so in its own reason field: "Git author and committer dates are set by
whoever makes the commit, and no commit in this repository is signed." The
timestamps that were not in the right order were the ones written INTO the
content, and nothing was reading those.

    METADATA IS SETTABLE AND CONTENT IS NOT. One of this repository's own
    commits demonstrated it. So this gate reads `checked_on`, `executed_utc`,
    `built` and `capture_date` -- fields the review wrote about its own work --
    and treats a commit date only as the CLAIM under test, never as evidence
    for it.

THE THREE RULES

    SEARCH_PRECEDES_SCREENING
        The earliest executed query must precede every screening decision. A
        decision dated before the search that produced the record it decides on
        is a decision taken on a different corpus.

    CONTENT_PREDATES_REGISTRATION
        No content timestamp may precede the protocol/registration time the
        object claims prospectiveness from. `built` is a content timestamp.

    PROSPECTIVE_CLAIM_NEEDS_A_CLEAN_CHRONOLOGY
        Where either of the above is inverted, a claim of prospective
        registration fails, AND the page must instead say the review was
        retrospectively formalised and disclose the chronology. A disclosed
        inversion passes; an undisclosed one does not.

WHAT IT CANNOT SEE -- printed with every verdict

    * A review that records no dates. NO_RECORD, never a pass. This is the
      common case and the coverage line says how common.
    * A date that is simply wrong. The gate checks ORDER, not truth; a
      backdated `checked_on` defeats it exactly as a backdated commit defeats
      the check it replaces. It narrows the surface, it does not close it.
    * Work done before any timestamp was written at all.
    * Prospectiveness claims phrased outside the marker list below.
    * Times of day where only a date is recorded: a date-only `checked_on` is
      compared at its END of day, so the gate never fails on a same-day
      ordering it cannot resolve.

USAGE

    python scripts/registration_chronology_gate.py --selftest
    python scripts/registration_chronology_gate.py ssot/<app>/<app>.json [--page p.html]
    python scripts/registration_chronology_gate.py --diff origin/main   # DEFAULT
    python scripts/registration_chronology_gate.py --all

Exit code: +1 if anything FAILED, +2 if anything could not be judged.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html as _html
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PASS, FAIL, UNDET, NA = "PASS", "FAIL", "UNDETERMINABLE", "NOT_APPLICABLE"

# Claims of prospectiveness. Deliberately literal; a new phrasing is invisible
# and that is stated in the docstring rather than papered over.
_PROSPECTIVE = (
    "prospective registration", "prospectively registered",
    "registered prospectively", "evidence of prospective registration",
    "registered before the search", "protocol was registered before",
    "precedes the first executed query", "prospectively specified protocol",
)
# What an honest inversion looks like when it is disclosed.
_DISCLOSED = (
    "retrospectively formalised", "retrospectively formalized",
    "retrospective registration", "registered retrospectively",
    "not prospectively registered", "not a prospective registration",
    "registered after the search", "the protocol postdates",
)

_INLINE = ("a|abbr|b|bdi|bdo|big|cite|code|del|dfn|em|font|i|ins|kbd|label|mark|"
           "output|q|rp|rt|ruby|s|samp|small|span|strike|strong|sub|sup|time|tt|"
           "u|var|wbr")
_INLINE_RE = re.compile(r"(?i)</?(?:%s)\b[^>]*>" % _INLINE)


def rendered_text(html):
    txt = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    txt = _INLINE_RE.sub("", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", _html.unescape(txt))


_TS = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?")


def parse_time(value, end_of_day=False):
    """A UTC datetime from any of the shapes this corpus writes.

    A DATE-ONLY value is resolved to the END of its day when it is being
    compared as the LATER side, so the gate never fails on an ordering it
    cannot actually resolve. Same-day is not evidence of inversion.
    """
    if not isinstance(value, str):
        return None
    m = _TS.search(value)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if m.group(4) is None:
        return (_dt.datetime(y, mo, d, 23, 59, 59) if end_of_day
                else _dt.datetime(y, mo, d, 0, 0, 0))
    return _dt.datetime(y, mo, d, int(m.group(4)), int(m.group(5)),
                        int(m.group(6) or 0))


def as_list(value):
    """A list, or [] for anything that is not one.

    THE CORPUS DOES NOT KEEP THE SHAPE ITS SCHEMA IMPLIES. Some objects store
    `screening.excluded` as an INTEGER -- a count rather than a collection --
    and iterating it killed a corpus sweep on the first such object, so
    everything after it was never examined at all. A crash mid-sweep is worse
    than a wrong verdict, because the wrong verdict is visible and the
    unexamined remainder is not.
    """
    return value if isinstance(value, list) else []


class Finding(object):
    def __init__(self, rule, where, state, detail):
        self.rule, self.where, self.state, self.detail = rule, where, state, detail

    def as_dict(self):
        return {"rule": self.rule, "where": self.where, "state": self.state,
                "detail": self.detail}


# --------------------------------------------------------------------------
# content timestamps -- and ONLY content timestamps

def search_times(obj):
    out = []
    for i, db in enumerate(as_list((obj.get("search") or {}).get("databases"))):
        if not isinstance(db, dict):
            continue
        t = parse_time(db.get("executed_utc"))
        if t:
            out.append(("search.databases[%d].executed_utc" % i, t))
    t = parse_time((obj.get("search") or {}).get("capture_date"))
    if t and not out:
        out.append(("search.capture_date", t))
    return out


def screening_times(obj):
    out = []
    scr = obj.get("screening") or {}
    for key in ("records", "excluded", "screened", "corpus"):
        for i, r in enumerate(as_list(scr.get(key))):
            if not isinstance(r, dict):
                continue
            for field in ("checked_on", "decided_on", "screened_on"):
                # END of day: a date-only decision on the SAME day as the search
                # is not an inversion this gate can resolve, and it will not
                # claim one.
                t = parse_time(r.get(field), end_of_day=True)
                if t:
                    out.append(("screening.%s[%d].%s" % (key, i, field), t,
                                r.get("trial") or r.get("nct") or r.get("pmid")))
    return out


def registration_claim_time(obj):
    reg = obj.get("registration") or {}
    order = reg.get("ordering") or {}
    for field in ("protocol_committed_utc", "registered_utc", "protocol_utc"):
        t = parse_time(order.get(field) or reg.get(field))
        if t:
            return "registration.ordering.%s" % field, t
    return None, None


# --------------------------------------------------------------------------

def rule_search_precedes_screening(obj):
    st = search_times(obj)
    dt = screening_times(obj)
    if not st and not dt:
        return [Finding("SEARCH_PRECEDES_SCREENING", "search/screening", NA,
                        "this object records neither a search execution time "
                        "nor a screening decision time")]
    if not st:
        return [Finding("SEARCH_PRECEDES_SCREENING", "search", UNDET,
                        "%d screening decision(s) are dated but no search "
                        "execution time is recorded, so the order cannot be "
                        "established" % len(dt))]
    if not dt:
        return [Finding("SEARCH_PRECEDES_SCREENING", "screening", UNDET,
                        "the search records an execution time but no screening "
                        "decision is dated, so the order cannot be established")]
    where0, first = min(st, key=lambda x: x[1])
    early = [(w, t, who) for (w, t, who) in dt if t < first]
    # THE DENOMINATOR IS DATED DECISIONS, NOT ALL DECISIONS, and the difference
    # is printed. An undated decision is not a later one; counting it as one
    # would make the gate report a reach figure as a coverage figure.
    total = _screening_record_count(obj)
    undated = max(total - len(dt), 0)
    if early:
        names = sorted({str(x[2]) for x in early if x[2]})[:6]
        return [Finding(
            "SEARCH_PRECEDES_SCREENING", where0, FAIL,
            "%d of %d DATED screening decision(s) predate the earliest executed "
            "query (%s at %s); the other %d of %d record(s) carry no date at "
            "all and are outside this comparison. Earliest decision %s. %s. A "
            "decision taken before the search that retrieved the record is a "
            "decision about a different corpus."
            % (len(early), len(dt), where0, first.isoformat(), undated, total,
               min(x[1] for x in early).isoformat(),
               ("Trials: " + ", ".join(names)) if names else "No trial named"))]
    return [Finding("SEARCH_PRECEDES_SCREENING", where0, PASS,
                    "%d dated screening decision(s) (of %d record(s), %d "
                    "undated), all at or after the earliest executed query %s"
                    % (len(dt), total, undated, first.isoformat()))]


def _screening_record_count(obj):
    scr = obj.get("screening") or {}
    return sum(len(as_list(scr.get(k)))
               for k in ("records", "excluded", "screened", "corpus"))


def rule_content_predates_registration(obj):
    where, reg = registration_claim_time(obj)
    if not reg:
        return [Finding("CONTENT_PREDATES_REGISTRATION", "registration", NA,
                        "this object claims no registration time")]
    content = []
    t = parse_time(obj.get("built"), end_of_day=True)
    if t:
        content.append(("built", t))
    content += [(w, t) for (w, t, _who) in screening_times(obj)]
    if not content:
        return [Finding("CONTENT_PREDATES_REGISTRATION", "registration", UNDET,
                        "a registration time is claimed but the object carries "
                        "no content timestamp to check it against")]
    early = [(w, t) for (w, t) in content if t < reg]
    if early:
        w0, t0 = min(early, key=lambda x: x[1])
        return [Finding(
            "CONTENT_PREDATES_REGISTRATION", where, FAIL,
            "%d content timestamp(s) predate the registration time this object "
            "claims (%s). The earliest is %s = %s. A protocol cannot be "
            "prospective to work the object itself records as already done."
            % (len(early), reg.isoformat(), w0, t0.isoformat()))]
    return [Finding("CONTENT_PREDATES_REGISTRATION", where, PASS,
                    "%d content timestamp(s), none before the claimed "
                    "registration %s" % (len(content), reg.isoformat()))]


def claims_and_disclosures(obj, page_text):
    """Prospectiveness claims, and disclosures of the opposite, on both surfaces."""
    blob = json.dumps(obj, ensure_ascii=False).lower()
    surfaces, disclosed = [], []
    for text, where in ((blob, "the object"),
                        ((page_text or "").lower(), "the page")):
        if not text:
            continue
        for p in _PROSPECTIVE:
            if p in text:
                surfaces.append((where, p))
        for p in _DISCLOSED:
            if p in text:
                disclosed.append((where, p))
    return surfaces, disclosed


def rule_claim_needs_clean_chronology(obj, page_text, inverted, judged):
    surfaces, disclosed = claims_and_disclosures(obj, page_text)

    if not judged:
        # NOTHING WAS CHECKED. Returning a pass from here is exactly how a gate
        # with no evidence reports a clean result, which is the failure mode the
        # third state exists to prevent.
        return [Finding("PROSPECTIVE_CLAIM_NEEDS_A_CLEAN_CHRONOLOGY",
                        "registration", NA,
                        "no chronology could be established either way, so a "
                        "prospectiveness claim can here be neither upheld nor "
                        "refused")]
    if not inverted:
        return [Finding("PROSPECTIVE_CLAIM_NEEDS_A_CLEAN_CHRONOLOGY",
                        "registration", PASS,
                        "the chronology is not inverted; %d prospectiveness "
                        "claim(s) stand" % len(surfaces))]
    out = []
    for where in sorted({w for w, _ in surfaces}):
        phrases = sorted({p for w, p in surfaces if w == where})
        out.append(Finding(
            "PROSPECTIVE_CLAIM_NEEDS_A_CLEAN_CHRONOLOGY", where, FAIL,
            "%s claims prospectiveness in %d place(s) -- %s -- while the "
            "object's own content puts work before the protocol. The claim must "
            "be withdrawn, or replaced with a retrospective-formalisation "
            "statement that discloses the chronology."
            % (where, len(phrases), "; ".join(repr(p) for p in phrases))))
    if not disclosed:
        out.append(Finding(
            "PROSPECTIVE_CLAIM_NEEDS_A_CLEAN_CHRONOLOGY", "registration", FAIL,
            "the chronology is inverted and no surface says so. A review whose "
            "content predates its protocol must say it was retrospectively "
            "formalised and show the dates."))
    elif not surfaces:
        out.append(Finding(
            "PROSPECTIVE_CLAIM_NEEDS_A_CLEAN_CHRONOLOGY", "registration", PASS,
            "the chronology is inverted and disclosed: %s"
            % "; ".join("%s says %r" % d for d in disclosed[:3])))
    return out


# --------------------------------------------------------------------------

def judge_object(path, repo, page_path=None):
    rec = {"object": os.path.relpath(path, repo).replace(os.sep, "/"),
           "page": None, "state": None, "detail": "", "findings": []}
    try:
        with open(path, "rb") as fh:
            obj = json.loads(fh.read().decode("utf-8", "replace"))
    except Exception as exc:
        rec["state"] = "NO_RECORD"
        rec["detail"] = "object unreadable: %s" % exc
        return rec

    page_text = None
    if page_path and os.path.exists(page_path):
        with open(page_path, "rb") as fh:
            page_text = rendered_text(fh.read().decode("utf-8", "replace"))
        rec["page"] = os.path.relpath(page_path, repo).replace(os.sep, "/")

    fs = rule_search_precedes_screening(obj) + \
        rule_content_predates_registration(obj)
    inverted = [f for f in fs if f.state == FAIL]
    judged = any(f.state in (PASS, FAIL) for f in fs)
    claims, disclosed = claims_and_disclosures(obj, page_text)

    # A DISCLOSED inversion is not a defect. The requirement is not that every
    # review be prospective -- it is that a review which is not says so and
    # shows the dates. So where the inversion is disclosed and prospectiveness
    # is claimed nowhere, the ordering findings are recorded as disclosed rather
    # than failed. They are still printed in full: a fact the reader is owed
    # does not stop being a fact because somebody owned up to it.
    if inverted and disclosed and not claims:
        for f in inverted:
            f.state = PASS
            f.detail = ("INVERTED AND DISCLOSED (%s). %s"
                        % ("; ".join("%s says %r" % d for d in disclosed[:2]),
                           f.detail))
        inverted = []

    fs += rule_claim_needs_clean_chronology(obj, page_text, bool(inverted),
                                            judged)
    rec["findings"] = [f.as_dict() for f in fs]

    states = {f["state"] for f in rec["findings"]}
    rec["state"] = (FAIL if FAIL in states else
                    UNDET if UNDET in states else
                    PASS if PASS in states else NA)
    if rec["state"] == NA:
        rec["detail"] = "no dated chronology on this object"
    return rec


# --------------------------------------------------------------------------
# scope / reporting

def _is_canonical(rel):
    p = rel.split("/")
    return len(p) == 3 and p[0] == "ssot" and p[2] == p[1] + ".json"


def diff_objects(base, repo):
    r = subprocess.run(["git", "diff", "--name-only", "%s...HEAD" % base,
                        "--", "ssot/*.json"], cwd=repo, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None, (r.stderr or "").strip()[:200]
    out = []
    for n in r.stdout.split("\n"):
        n = n.strip()
        p = os.path.join(repo, n.replace("/", os.sep))
        if n and _is_canonical(n) and os.path.exists(p):
            out.append(p)
    return out, None


def all_objects(repo):
    root = os.path.join(repo, "ssot")
    if not os.path.isdir(root):
        return []
    return [os.path.join(root, n, n + ".json") for n in sorted(os.listdir(root))
            if os.path.exists(os.path.join(root, n, n + ".json"))]


def report(records, n_in_scope, scope_note, wall, cpu, not_reached):
    fails = [r for r in records if r["state"] == FAIL]
    undet = [r for r in records if r["state"] in (UNDET, "NO_RECORD", "TIMED_OUT")]
    passes = [r for r in records if r["state"] == PASS]
    na = [r for r in records if r["state"] == NA]

    for r in fails:
        print("\nFAIL  %s%s" % (r["object"],
                                "  (page %s)" % r["page"] if r["page"] else ""))
        for f in [x for x in r["findings"] if x["state"] == FAIL]:
            print("      [%s] %s" % (f["rule"], f["where"]))
            print("      %s" % f["detail"])
    for r in undet:
        print("\n%-14s %s" % (r["state"], r["object"]))
        for f in [x for x in r["findings"] if x["state"] == UNDET][:3]:
            print("      [%s] %s" % (f["rule"], f["detail"]))

    reach = {}
    for r in records:
        for f in r["findings"]:
            d = reach.setdefault(f["rule"], {PASS: 0, FAIL: 0, UNDET: 0, NA: 0})
            d[f["state"]] += 1

    print("\n" + "-" * 74)
    print("COVERAGE   %d of %d %s" % (len(records), n_in_scope, scope_note))
    print("           %d PASS, %d FAIL, %d could not be judged, %d record no "
          "dates at all" % (len(passes), len(fails), len(undet), len(na)))
    print("PER RULE   (a rule that judged nothing reads NOT OBSERVED, not SAFE)")
    for rule in sorted(reach):
        d = reach[rule]
        judged = d[PASS] + d[FAIL] + d[UNDET]
        print("           %-46s %s"
              % (rule[:46],
                 "NOT OBSERVED -- 0 judged, %d not applicable" % d[NA]
                 if judged == 0 else
                 "%d judged: %d pass, %d fail, %d undeterminable (%d n/a)"
                 % (judged, d[PASS], d[FAIL], d[UNDET], d[NA])))
    print("BLIND TO   a review with no dates; a date that is simply wrong (order "
          "is checked,")
    print("           not truth); work done before any timestamp was written; "
          "prospectiveness")
    print("           claims phrased outside the marker list. Commit dates are "
          "NOT used as")
    print("           evidence here -- only as the claim under test.")
    if not_reached:
        print("           NOT REACHED: %d object(s)" % len(not_reached))
    print("COST       %.2fs wall, %.2fs CPU" % (wall, cpu))
    if not records:
        print("VERDICT    NOT OBSERVED -- nothing in scope carried an object.")
    return (1 if fails else 0) + (2 if (undet or not_reached) else 0)


# --------------------------------------------------------------------------
# self-test

def _obj(search="2026-08-12T12:22:39Z", checked=("2026-08-13",),
         built="2026-08-13", reg="2026-08-12T11:27:47Z", note=None):
    o = {"built": built,
         "search": {"databases": [{"database": "PubMed",
                                   "executed_utc": search}]},
         "screening": {"records": [{"trial": "T%d" % i, "checked_on": c}
                                   for i, c in enumerate(checked)]},
         "registration": {"ordering": {"protocol_committed_utc": reg}}}
    if note:
        o["manuscript"] = {"registration_note_for_editor": note}
    return o


def selftest():
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="chrono_")
    try:
        seq = [0]

        def run(label, obj, want, rule=None, page=None):
            seq[0] += 1
            d = os.path.join(root, "ssot", "__control_%02d" % seq[0])
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "__control_%02d.json" % seq[0])
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            pg = None
            if page is not None:
                pg = os.path.join(root, "p%02d.html" % seq[0])
                with open(pg, "w", encoding="utf-8") as fh:
                    fh.write(page)
            r = judge_object(p, root, pg)
            fired = {f["rule"] for f in r["findings"] if f["state"] == FAIL}
            good = r["state"] == want and (rule is None or rule in fired)
            print("  %-14s expected %-14s %-8s %s"
                  % (r["state"], want, "correct" if good else "WRONG", label))
            return good

        ok = True
        print("=== each plant must fire before its fix is allowed to pass ===")

        ok &= run("clean chronology: protocol, then search, then screening",
                  _obj(), PASS)

        # ARNI, exactly: search 08-12, decisions 08-09 and 08-10, built 08-09.
        ok &= run("PLANT: nine decisions dated before the search (ARNI's dates)",
                  _obj(checked=("2026-08-09",) * 5 + ("2026-08-10",) * 4,
                       built="2026-08-09"),
                  FAIL, "SEARCH_PRECEDES_SCREENING")

        ok &= run("PLANT: the same object also built before its own protocol",
                  _obj(checked=("2026-08-09",), built="2026-08-09"),
                  FAIL, "CONTENT_PREDATES_REGISTRATION")

        ok &= run("PLANT: an inverted chronology carrying a prospective claim",
                  _obj(checked=("2026-08-09",), built="2026-08-09",
                       note="The commit precedes the first executed query by a "
                            "recorded margin, which is stronger evidence of "
                            "prospective registration than a registry entry."),
                  FAIL, "PROSPECTIVE_CLAIM_NEEDS_A_CLEAN_CHRONOLOGY")

        ok &= run("FIX of that plant: the claim is withdrawn and the inversion "
                  "disclosed",
                  _obj(checked=("2026-08-09",), built="2026-08-09",
                       note="This review was retrospectively formalised: "
                            "screening on 2026-08-09 preceded the protocol "
                            "commit on 2026-08-12."),
                  PASS)

        # A SAME-DAY date-only decision must NOT be read as an inversion.
        ok &= run("a date-only decision on the SAME day as the search is not an "
                  "inversion this gate can resolve",
                  _obj(search="2026-08-12T12:22:39Z", checked=("2026-08-12",),
                       built="2026-08-13"), PASS)

        ok &= run("no dates at all: NOT_APPLICABLE, never a pass",
                  {"screening": {}, "search": {}}, NA)

        ok &= run("decisions dated but no search time: UNDETERMINABLE",
                  {"screening": {"records": [{"checked_on": "2026-08-09"}]},
                   "search": {"databases": [{"database": "PubMed"}]}}, UNDET)

        ok &= run("PLANT: the prospective claim on the PAGE, object inverted",
                  _obj(checked=("2026-08-09",), built="2026-08-09"),
                  FAIL, "PROSPECTIVE_CLAIM_NEEDS_A_CLEAN_CHRONOLOGY",
                  page="<html><body><p>This review was prospectively "
                       "regist<em>ered</em>.</p></body></html>")

        print("\nself-test %s" % ("PASSED" if ok else "FAILED"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------

def run_controls():
    """Both controls, before any count is printed.

    THE CONTROLS ARE SYNTHETIC ON PURPOSE. A control anchored to a live corpus
    item retires itself the moment the defect is fixed: it then either fails and
    looks like a regression, or passes for the wrong reason. These are
    constructed, pinned in this file, and cannot drift. The negative side is not
    optional -- over-flagging is this gate's failure mode, and a false finding
    discredits the true ones.
    """
    import shutil
    import tempfile

    from instrument_controls import require_controls

    root = tempfile.mkdtemp(prefix="chrono_ctl_")
    try:
        def write(name, obj):
            d = os.path.join(root, "ssot", name)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name + ".json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(obj, fh)
            return p

        p1 = write("__control_inverted",
                   _obj(checked=("2026-08-09",) * 5 + ("2026-08-10",) * 4,
                        built="2026-08-09",
                        note="The commit precedes the first executed query by a "
                             "recorded margin, which is stronger evidence of "
                             "prospective registration than a registry entry."))
        p2 = write("__control_ordered", _obj())
        require_controls(
            "registration_chronology_gate",
            positive=("a synthetic object whose screening predates its own "
                      "search while it claims prospective registration",
                      judge_object(p1, root)["state"], FAIL),
            negative=("protocol, then search, then screening, in that order",
                      judge_object(p2, root)["state"], FAIL))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("objects", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--page")
    ap.add_argument("--diff", metavar="BASE")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--timeout-seconds", type=float, default=300.0)
    ap.add_argument("--json", metavar="PATH")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    # NOTHING IS PRINTED BEFORE THE CONTROLS HOLD.
    run_controls()

    repo = os.path.abspath(a.repo)
    not_reached = []
    if a.objects:
        objs = [os.path.abspath(p) for p in a.objects]
        scope_note = "object(s) named on the command line"
    elif a.all:
        objs = all_objects(repo)
        scope_note = "canonical object(s) under ssot/"
    else:
        base = a.diff or "origin/main"
        objs, err = diff_objects(base, repo)
        if objs is None:
            print("INVALID: cannot compute the diff against %s: %s" % (base, err))
            return 2
        scope_note = "canonical object(s) changed against %s" % base

    t0, c0 = time.time(), time.process_time()
    deadline = t0 + a.timeout_seconds
    records = []
    for i, p in enumerate(objs):
        if time.time() > deadline:
            not_reached = objs[i:]
            print("TIMED_OUT after %.1fs: %d object(s) were not reached."
                  % (a.timeout_seconds, len(not_reached)))
            break
        records.append(judge_object(p, repo, a.page if len(objs) == 1 else None))
    wall, cpu = time.time() - t0, time.process_time() - c0

    rc = report(records, len(objs), scope_note, wall, cpu, not_reached)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"records": records, "scope": scope_note,
                       "n_in_scope": len(objs),
                       "not_reached": [os.path.basename(p) for p in not_reached],
                       "wall_seconds": wall, "cpu_seconds": cpu}, fh, indent=1)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
