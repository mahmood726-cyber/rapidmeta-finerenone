"""DENOMINATOR AXIS GATE -- refuses a page that prints one denominator under another's name.

THE DEFECT, THREE PAGES IN A ROW.

    ARNI. The object stores four trials whose `enrolled` sums to 9,779, and arms
    whose `participants` sum to 9,734. The served page says "9,734 randomised
    participants" twice and "9,734 participants" twice; 9,779 appears nowhere on
    it. The analysis set was printed under the word "randomised".

    Bococizumab. 4,449 enrolled, 4,263 randomised to the arms this review asks
    about, 3,969 contributing to the week-12 analysis. Three quantities, one
    label.

Enrolled, randomised and analysed are three different quantities. A reader told
that a pooled estimate rests on 9,734 randomised participants has been told
something false about the design of the evidence, and no amount of correct
arithmetic downstream repairs it.

WHAT THIS GATE DOES

    It reads the RENDERED text of a page -- tags stripped, entities unescaped,
    whitespace collapsed -- because a sentence the reader sees as one string is
    several strings in the file, and a check that searches the source cannot
    find it. It finds every number equal to one of the review-level totals the
    object stores, works out which denominator word that number is bound to in
    the prose, and fails when the word names a different axis from the one the
    number came from.

    It needs no topic knowledge and no ground truth beyond the object. Two of
    our own surfaces disagreeing is the whole test.

THE THREE AXES, AND WHERE EACH IS STORED

    ALLOCATED   sum of inputs.trials[*].enrolled
    REGISTERED  sum of inputs.trials[*].registration_enrolment
    ANALYSED    sum over trials of `participants` on the arms actually used,
                i.e. arms minus anything named in arms_not_used

    An axis whose inputs are not all present is NOT derived and NOT assumed. It
    is recorded as underivable, and any occurrence that would have needed it is
    reported UNDETERMINABLE, which is never a pass.

WHY IT FAILS ONLY ON A CROSS-AXIS MATCH

    A false warning is worse than a missing one, because it discredits the true
    ones. So the gate fails only when the printed number IS, exactly, the stored
    total of a different axis. A number under a denominator word that matches no
    stored axis is reported as unplaceable and never failed: it may be a
    subgroup, a per-trial figure, or an error this gate is not equipped to
    judge. That is a real blind spot and it is printed with every verdict.

WHAT IT CANNOT SEE -- stated here so nobody has to infer it

    * A wrong number coinciding with no stored axis. Reported, never failed.
    * A page carrying no `ssot/<app>/<app>.json` self-reference: NO_RECORD.
      The mapping is taken from the page's own bytes, never from its filename,
      because filenames here have pointed at the wrong object before.
    * Objects whose arms carry no `participants`: the ANALYSED axis is
      underivable and every judgement needing it is UNDETERMINABLE.
    * Denominator words outside the lists below. A new phrasing is invisible.
    * Numbers written as words ("nine thousand"). Digits only.
    * A denominator claim with NO person-noun in its sentence -- "N = 9,734
      randomised". The person-noun is required because without it the gate binds
      "read from the registry on 2026-08-18", "registered Week 12" and
      "bococizumab 150 mg" to a denominator word, and buries the one real
      finding under a dozen manufactured ones. Recall was traded for precision
      deliberately: a warning nobody trusts is worse than no warning.
    * Whether a number is RIGHT. It only asks whether it is under its own name.

USAGE

    python scripts/denominator_axis_gate.py --selftest
    python scripts/denominator_axis_gate.py PAGE.html [PAGE.html ...]
    python scripts/denominator_axis_gate.py --diff origin/main   # DEFAULT SCOPE
    python scripts/denominator_axis_gate.py --all                # opt-in, slow

Exit code follows verdict.py: +1 if anything FAILED, +2 if anything could not be
judged (UNDETERMINABLE, NO_RECORD, TIMED_OUT). An INVALID is never a pass.
"""
from __future__ import annotations

import argparse
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

# --------------------------------------------------------------------------
# the axes

ALLOCATED, REGISTERED, ANALYSED = "ALLOCATED", "REGISTERED", "ANALYSED"

# The word lists are deliberately short and deliberately literal. Every entry is
# a word this corpus actually uses beside a denominator; nothing is here on the
# grounds that it might appear one day.
AXIS_WORDS = {
    ALLOCATED: ("randomised", "randomized", "allocated", "enrolled", "enrolment",
                "enrollment", "recruited"),
    REGISTERED: ("registered", "registry"),
    ANALYSED: ("analysed", "analyzed", "contributing", "contributed",
               "analysable", "analyzable"),
}
WORD_TO_AXIS = {w: ax for ax, ws in AXIS_WORDS.items() for w in ws}

# "4 randomised TRIALS" counts trials, not people. Binding a participant total to
# that word would manufacture a warning out of ordinary English, which is the
# failure mode this gate is least allowed to have.
TRIAL_NOUNS = ("trial", "trials", "study", "studies", "comparison", "comparisons",
               "arm", "arms", "controlled", "crossover", "cluster", "design",
               "designs", "evidence", "record", "records", "report", "reports")

# A denominator counts PEOPLE. Without this the gate binds "Read from the
# registry on 2026-08-18" and "registered Week 12" and "bococizumab 150 mg" to a
# denominator word, and the one real finding on the page is buried under a dozen
# manufactured ones. A warning nobody can trust is worse than no warning.
PERSON_NOUNS = ("participant", "participants", "patient", "patients", "people",
                "person", "persons", "subject", "subjects", "individual",
                "individuals", "adult", "adults", "child", "children", "infant",
                "infants", "woman", "women", "man", "men")

_NUM_RE = re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{2,7}\b")
_WINDOW = 60            # characters either side of the number
_MIN_REVIEW_TOTAL = 10  # below this a "total" is not a denominator worth binding


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


def _num(tok):
    return int(tok.replace(",", ""))


# --------------------------------------------------------------------------
# reading the artefacts

# An inline tag is deleted, a block tag becomes a space. Both halves matter and
# each was learned from a defect: replacing EVERY tag with a space turns
# "9<span>50</span>" into "9 50" and the number disappears from the check;
# replacing every tag with nothing turns "<p>a</p><p>b</p>" into "ab" and
# manufactures words that were never on the page.
_INLINE = ("a|abbr|b|bdi|bdo|big|cite|code|del|dfn|em|font|i|ins|kbd|label|mark|"
           "output|q|rp|rt|ruby|s|samp|small|span|strike|strong|sub|sup|time|tt|"
           "u|var|wbr")
_INLINE_RE = re.compile(r"(?i)</?(?:%s)\b[^>]*>" % _INLINE)


def rendered_text(html):
    """What the reader sees, not what the file holds.

    Markup splits a sentence into several strings; a check that searches the
    source for a sentence the reader sees as one cannot find it, and if its
    logic is "not found, therefore fine", every markup-spanning sentence scores
    as clean. Strip first, then search.
    """
    txt = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    txt = _INLINE_RE.sub("", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = _html.unescape(txt)
    return re.sub(r"\s+", " ", txt)


_OBJ_REF_RE = re.compile(r"ssot/([A-Za-z0-9_-]+)/\1\.json")
_DATA_STORE_RE = re.compile(r"""(?i)\bdata-store\s*=\s*["']\s*(ssot/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+\.json)\s*["']""")


def object_path_for(raw_html, repo):
    """The object a page names IN ITS OWN BYTES, and which carrier said so.

    Never derived from the filename. One object in this repository is delivered
    as two pages under different names, and a filename-derived map pointed at
    the legacy one for weeks without anybody noticing.

    Two carriers exist and both are read, because the corpus uses both: the
    structural `data-store` attribute on <html>, and a plain mention of the path
    in the prose. The attribute wins when present -- it is what the build wrote,
    not what a sentence happens to say. Note that the attribute does NOT survive
    tag-stripping, so this resolution reads the RAW bytes; the number scan below
    reads the RENDERED text. Those are different questions and each is asked of
    the surface that can answer it.
    """
    m = _DATA_STORE_RE.search(raw_html)
    if m:
        rel, carrier = m.group(1), "data-store attribute"
    else:
        hits = sorted({x.group(0) for x in _OBJ_REF_RE.finditer(raw_html)})
        if len(hits) != 1:
            return None, None, ("no data-store attribute and no object path in "
                                "the page" if not hits else
                                "no data-store attribute, and the page names %d "
                                "different objects: %s"
                                % (len(hits), ", ".join(hits)))
        rel, carrier = hits[0], "path named in the page body"
    p = os.path.join(repo, rel.replace("/", os.sep))
    if not os.path.exists(p):
        return None, carrier, ("page names %s (%s), which is not present in this "
                               "tree" % (rel, carrier))
    return p, carrier, rel


def axis_totals(obj):
    """Return ({axis: total}, {axis: why-not}) for one object.

    An axis is derived only when EVERY trial supplies its input. A partial sum
    is a different quantity from the total it would be mistaken for, and
    reporting one would make this gate the very defect it exists to catch.
    """
    trials = as_list((obj.get("inputs") or {}).get("trials"))
    totals, why = {}, {}
    if not trials:
        return totals, {"*": "object carries no inputs.trials"}

    def _sum(field):
        vals = []
        for t in trials:
            v = t.get(field)
            if isinstance(v, bool) or not isinstance(v, int):
                return None, "%s has no integer %s" % (t.get("id", "?"), field)
            vals.append(v)
        return sum(vals), None

    for axis, field in ((ALLOCATED, "enrolled"),
                        (REGISTERED, "registration_enrolment")):
        tot, miss = _sum(field)
        if tot is None:
            why[axis] = miss
        else:
            totals[axis] = tot

    analysed, miss = 0, None
    for t in trials:
        not_used = {str(x) for x in as_list(t.get("arms_not_used"))}
        arms = [a for a in as_list(t.get("arms"))
                if isinstance(a, dict) and str(a.get("label", "")) not in not_used]
        if not arms:
            miss = "%s has no usable arms" % t.get("id", "?")
            break
        for a in arms:
            p = a.get("participants")
            if isinstance(p, bool) or not isinstance(p, int):
                miss = "%s arm %r has no integer participants" % (
                    t.get("id", "?"), str(a.get("label", ""))[:30])
                break
            analysed += p
        if miss:
            break
    if miss:
        why[ANALYSED] = miss
    else:
        totals[ANALYSED] = analysed
    return totals, why


# --------------------------------------------------------------------------
# binding a number to a denominator word

def bound_words(text, start, end):
    """Denominator words bound to the number at [start:end).

    A word counts as bound when it sits inside the window, in the same sentence,
    with NO other number between it and this one, and is not immediately
    qualifying a trial noun.
    """
    out = []
    before = text[max(0, start - _WINDOW):start]
    after = text[end:end + _WINDOW]
    if ". " in before:
        before = before.rsplit(". ", 1)[1]
    if ". " in after:
        after = after.split(". ", 1)[0]

    # A denominator counts people. No person-noun in the sentence window means
    # this number is a year, a week, a dose or an outcome index, and binding it
    # to "registered" or "randomised" would manufacture a finding.
    sentence = (before + " " + text[start:end] + " " + after).lower()
    if not any(re.search(r"\b%s\b" % n, sentence) for n in PERSON_NOUNS):
        return out

    for seg, side in ((before, "before"), (after, "after")):
        low = seg.lower()
        for m in re.finditer(r"[a-z]+", low):
            axis = WORD_TO_AXIS.get(m.group(0))
            if not axis:
                continue
            between = seg[m.end():] if side == "before" else seg[:m.start()]
            if _NUM_RE.search(between):
                continue
            nxt = re.match(r"[a-z]+", low[m.end():].lstrip())
            if nxt and nxt.group(0) in TRIAL_NOUNS:
                continue
            out.append((axis, m.group(0), side, seg.strip()))
    return out


def judge_page(page_path, repo, deadline=None):
    """One page, one record. Never returns a bare boolean."""
    with open(page_path, "rb") as fh:
        html = fh.read().decode("utf-8", "replace")
    text = rendered_text(html)

    rec = {"page": os.path.relpath(page_path, repo).replace(os.sep, "/"),
           "object": None, "carrier": None, "state": None, "detail": "",
           "findings": [], "unplaceable": [], "totals": {}, "underivable": {}}

    obj_path, carrier, note = object_path_for(html, repo)
    rec["carrier"] = carrier
    if obj_path is None:
        rec["state"] = "NO_RECORD"
        rec["detail"] = note
        return rec
    rec["object"] = note

    try:
        with open(obj_path, "rb") as fh:
            obj = json.loads(fh.read().decode("utf-8", "replace"))
    except Exception as exc:
        rec["state"] = "NO_RECORD"
        rec["detail"] = "object unreadable: %s" % exc
        return rec

    totals, why = axis_totals(obj)
    rec["totals"], rec["underivable"] = dict(totals), dict(why)
    if not totals:
        rec["state"] = "UNDETERMINABLE"
        rec["detail"] = "no denominator axis derivable: %s" % why
        return rec

    by_value = {}
    for ax, tot in totals.items():
        if tot >= _MIN_REVIEW_TOTAL:
            by_value.setdefault(tot, set()).add(ax)

    seen = set()
    for m in _NUM_RE.finditer(text):
        if deadline and time.time() > deadline:
            rec["state"] = "TIMED_OUT"
            rec["detail"] = "deadline reached while scanning this page"
            return rec
        val = _num(m.group(0))
        bound = bound_words(text, m.start(), m.end())
        if not bound:
            continue
        owners = by_value.get(val) or set()
        for axis, word, _side, quote in bound:
            key = (val, word)
            stored = totals.get(axis)
            # ORDER MATTERS HERE. The axis the WORD names is asked about first,
            # and an axis this object cannot supply is UNDETERMINABLE even when
            # the number happens to match some other axis. Reaching the
            # value-matching branch first is how a claim nobody could check
            # falls through to a clean negative -- the exact shape that produced
            # a trunk-wide false verdict on this repository.
            if stored is None:
                if val >= _MIN_REVIEW_TOTAL and key not in seen:
                    seen.add(key)
                    rec["findings"].append(
                        {"kind": "UNDETERMINABLE", "value": val, "word": word,
                         "word_axis": axis, "value_axis": sorted(owners),
                         "reason": why.get(axis, "axis not derivable"),
                         "quote": quote[:200]})
                continue
            if stored == val:
                continue                        # printed under its own name
            if axis in owners:
                continue                        # coincident axes: nothing collapsed
            if not owners:
                if key not in seen:
                    seen.add(key)
                    rec["unplaceable"].append({"value": val, "word": word,
                                               "quote": quote[:160]})
                continue
            rec["findings"].append(
                {"kind": "COLLAPSE", "value": val, "word": word,
                 "word_axis": axis, "word_axis_total": stored,
                 "value_axis": sorted(owners), "quote": quote[:200]})

    if any(f["kind"] == "COLLAPSE" for f in rec["findings"]):
        rec["state"] = "FAIL"
    elif any(f["kind"] == "UNDETERMINABLE" for f in rec["findings"]):
        rec["state"] = "UNDETERMINABLE"
    else:
        rec["state"] = "PASS"
    return rec


# --------------------------------------------------------------------------
# scope

def diff_pages(base, repo):
    """The pages THIS push changes. Diff scope, not tree scope, by default.

    A tree-scoped gate makes every lane answerable for every other lane's work,
    and in a repository with a hundred live worktrees that is how a lane comes
    to fail on somebody else's already-accepted commit.
    """
    r = subprocess.run(["git", "diff", "--name-only", "%s...HEAD" % base,
                        "--", "*.html"], cwd=repo, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None, (r.stderr or "").strip()[:200]
    out = []
    for n in r.stdout.split("\n"):
        n = n.strip()
        if not n:
            continue
        p = os.path.join(repo, n.replace("/", os.sep))
        if os.path.exists(p):
            out.append(p)
    return out, None


def all_pages(repo):
    return [os.path.join(repo, n) for n in sorted(os.listdir(repo))
            if n.endswith(".html")]


# --------------------------------------------------------------------------
# reporting

def report(records, n_in_scope, scope_note, wall, cpu, not_reached):
    fails = [r for r in records if r["state"] == "FAIL"]
    undet = [r for r in records
             if r["state"] in ("UNDETERMINABLE", "NO_RECORD", "TIMED_OUT")]
    passes = [r for r in records if r["state"] == "PASS"]

    for r in fails:
        print("\nFAIL  %s  (object %s)" % (r["page"], r["object"]))
        print("      stored totals: %s"
              % ", ".join("%s=%s" % kv for kv in sorted(r["totals"].items())))
        for f in [x for x in r["findings"] if x["kind"] == "COLLAPSE"]:
            print("      %s is printed under the word %r, which names %s "
                  "(stored %s)."
                  % (f["value"], f["word"], f["word_axis"], f["word_axis_total"]))
            print("          %s is the stored total for %s."
                  % (f["value"], "/".join(f["value_axis"])))
            print("          ...%s..." % f["quote"])
    for r in undet:
        print("\n%-14s %s -- %s"
              % (r["state"], r["page"],
                 r["detail"][:160] or "denominator claims this object cannot "
                                      "answer"))
        if r["underivable"]:
            print("      axes not derivable: %s"
                  % "; ".join("%s (%s)" % kv
                              for kv in sorted(r["underivable"].items())))
        for f in [x for x in r["findings"] if x["kind"] == "UNDETERMINABLE"][:6]:
            print("      %s is printed under the word %r, which names %s -- and "
                  "%s has no stored total here."
                  % (f["value"], f["word"], f["word_axis"], f["word_axis"]))
            print("          ...%s..." % f["quote"])

    n_unplaceable = sum(len(r["unplaceable"]) for r in records)
    print("\n" + "-" * 74)
    print("COVERAGE   %d of %d %s" % (len(records), n_in_scope, scope_note))
    print("           %d PASS, %d FAIL, %d could not be judged"
          % (len(passes), len(fails), len(undet)))
    if not_reached:
        print("           NOT REACHED: %d page(s): %s"
              % (len(not_reached),
                 ", ".join(os.path.basename(p) for p in not_reached[:6])))
    print("BLIND TO   %d number(s) sat beside a denominator word and matched no "
          "stored axis." % n_unplaceable)
    print("           Reported, never failed: a subgroup total, a per-trial "
          "figure and a plain")
    print("           error are indistinguishable to this gate. A zero here "
          "reads NOT OBSERVED,")
    print("           not SAFE.")
    print("COST       %.2fs wall, %.2fs CPU" % (wall, cpu))
    if not records:
        print("VERDICT    NOT OBSERVED -- nothing in scope carried a page to read.")
    return (1 if fails else 0) + (2 if (undet or not_reached) else 0)


# --------------------------------------------------------------------------
# self-test: the plant must fire BEFORE the fix is allowed to pass

_OBJ = {
    "app_id": "__control_denominator",
    "inputs": {"trials": [
        {"id": "t1", "enrolled": 600, "registration_enrolment": 600,
         "arms": [{"label": "a", "participants": 280},
                  {"label": "b", "participants": 290}]},
        {"id": "t2", "enrolled": 400, "registration_enrolment": 400,
         "arms": [{"label": "a", "participants": 190},
                  {"label": "b", "participants": 190}]}]},
}
# ALLOCATED = 1000, REGISTERED = 1000, ANALYSED = 950.

_REF = "ssot/__control_denominator/__control_denominator.json"
_PLANTED = ("<html><body><p>Two trials contributing <strong>950</strong> "
            "randomised participants met all eligibility conditions.</p>"
            "<p><code>" + _REF + "</code></p></body></html>")
_FIXED = ("<html><body><p>Two trials randomised <strong>1,000</strong> "
          "participants, of whom <strong>950</strong> contributed to the "
          "analysis.</p><p><code>" + _REF + "</code></p></body></html>")
_MARKUP_SPANNING = ("<html><body><p>The pooled estimate rests on 9<span>50</span>"
                    " random<em>ised</em> participants.</p><p>" + _REF
                    + "</p></body></html>")
_NO_OBJECT = "<html><body><p>950 randomised participants.</p></body></html>"
_TRIAL_NOUN = ("<html><body><p>Across 2 randomised trials and 950 participants "
               "the estimate held.</p><p>" + _REF + "</p></body></html>")


def _build_controls(root):
    """Write the planted and the fixed control page into `root`, return their paths."""
    d = os.path.join(root, "ssot", "__control_denominator")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "__control_denominator.json"), "w",
              encoding="utf-8") as fh:
        json.dump(_OBJ, fh)
    out = {}
    for name, body in (("planted.html", _PLANTED), ("fixed.html", _FIXED)):
        p = os.path.join(root, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
        out[name] = p
    return out


def run_controls():
    """Both controls, before any count is printed.

    THE CONTROLS ARE SYNTHETIC ON PURPOSE. A control anchored to a live corpus
    item retires itself the moment the defect is fixed: it then either fails and
    looks like a regression, or passes for the wrong reason. These two are
    constructed, pinned in this file, and cannot drift -- the positive carries
    the collapse and must FAIL, the negative carries the same totals correctly
    labelled and must NOT fail. The negative side is not optional here, because
    over-flagging is this gate's failure mode: a false denominator warning would
    discredit the true ones.
    """
    import shutil
    import tempfile

    from instrument_controls import require_controls

    root = tempfile.mkdtemp(prefix="denomgate_ctl_")
    try:
        pages = _build_controls(root)
        require_controls(
            "denominator_axis_gate",
            positive=("a synthetic page printing the ANALYSED total under the "
                      "word 'randomised'",
                      judge_page(pages["planted.html"], root)["state"], "FAIL"),
            negative=("the same totals, each under its own name",
                      judge_page(pages["fixed.html"], root)["state"], "FAIL"))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def selftest():
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="denomgate_")
    try:
        d = os.path.join(root, "ssot", "__control_denominator")
        os.makedirs(d)
        with open(os.path.join(d, "__control_denominator.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(_OBJ, fh)

        def page(name, body):
            p = os.path.join(root, name)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(body)
            return p

        cases = [
            ("PLANT: the analysis set printed under the word 'randomised'",
             "planted.html", _PLANTED, "FAIL"),
            ("FIX of that plant: each total under its own name",
             "fixed.html", _FIXED, "PASS"),
            ("PLANT: the same collapse split across markup",
             "markup.html", _MARKUP_SPANNING, "FAIL"),
            ("a page naming no object is NO_RECORD, never a pass",
             "noobj.html", _NO_OBJECT, "NO_RECORD"),
            ("'2 randomised trials' must NOT bind the participant total",
             "trialnoun.html", _TRIAL_NOUN, "PASS"),
        ]
        ok = True
        print("=== the plant must fire before the fix is allowed to pass ===")
        for label, name, body, want in cases:
            got = judge_page(page(name, body), root)["state"]
            good = got == want
            ok = ok and good
            print("  %-14s expected %-14s %-8s %s"
                  % (got, want, "correct" if good else "WRONG", label))

        # THE THIRD STATE, which is where the real corpus lives. The bococizumab
        # object supplies `enrolled` on one trial of six, so ALLOCATED and
        # REGISTERED are not derivable, while its page prints "4,449
        # participants as registered". A claim nobody could check must not fall
        # through to a clean negative.
        d2 = os.path.join(root, "ssot", "__control_partial")
        os.makedirs(d2)
        with open(os.path.join(d2, "__control_partial.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"inputs": {"trials": [
                {"id": "t1", "enrolled": 600,
                 "arms": [{"label": "a", "participants": 280},
                          {"label": "b", "participants": 290}]},
                {"id": "t2",
                 "arms": [{"label": "a", "participants": 190},
                          {"label": "b", "participants": 190}]}]}}, fh)
        ref2 = "ssot/__control_partial/__control_partial.json"

        r = judge_page(page("partial.html",
                            "<html><body><p>1,000 participants as registered.</p>"
                            "<p>" + ref2 + "</p></body></html>"), root)
        good = (r["state"] == "UNDETERMINABLE"
                and any(f["kind"] == "UNDETERMINABLE" for f in r["findings"])
                and ALLOCATED in r["underivable"])
        ok = ok and good
        print("  %-14s expected %-14s %-8s %s"
              % (r["state"], "UNDETERMINABLE", "correct" if good else "WRONG",
                 "a claim under an axis this object cannot supply"))

        r = judge_page(page("unplaceable.html",
                            "<html><body><p>777 participants contributed to the "
                            "analysis.</p><p>" + ref2 + "</p></body></html>"),
                       root)
        good = r["state"] == "PASS" and bool(r["unplaceable"])
        ok = ok and good
        print("  %-14s expected %-14s %-8s %s"
              % (r["state"], "PASS", "correct" if good else "WRONG",
                 "a number matching no stored axis is reported, never failed"))

        print("\nself-test %s" % ("PASSED" if ok else "FAILED"))
        return 0 if ok else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pages", nargs="*")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--diff", metavar="BASE",
                    help="scope to pages changed against BASE (default scope)")
    ap.add_argument("--all", action="store_true",
                    help="scope to every page at the repository root -- opt-in")
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--timeout-seconds", type=float, default=600.0)
    ap.add_argument("--json", metavar="PATH")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    # NOTHING IS PRINTED BEFORE THE CONTROLS HOLD.
    run_controls()

    repo = os.path.abspath(a.repo)
    not_reached = []
    if a.pages:
        pages = [os.path.abspath(p) for p in a.pages]
        scope_note = "page(s) named on the command line"
    elif a.all:
        pages = all_pages(repo)
        scope_note = "page(s) at the repository root"
    else:
        base = a.diff or "origin/main"
        pages, err = diff_pages(base, repo)
        if pages is None:
            print("INVALID: cannot compute the diff against %s: %s" % (base, err))
            print("A gate that cannot establish its own scope reports that, "
                  "rather than checking nothing and calling it a pass.")
            return 2
        scope_note = "page(s) changed against %s" % base

    t0, c0 = time.time(), time.process_time()
    deadline = t0 + a.timeout_seconds
    records = []
    for i, p in enumerate(pages):
        if time.time() > deadline:
            not_reached = pages[i:]
            print("TIMED_OUT after %.1fs: %d page(s) were not reached."
                  % (a.timeout_seconds, len(not_reached)))
            break
        records.append(judge_page(p, repo, deadline=deadline))
    wall, cpu = time.time() - t0, time.process_time() - c0

    rc = report(records, len(pages), scope_note, wall, cpu, not_reached)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"records": records, "scope": scope_note,
                       "n_in_scope": len(pages),
                       "not_reached": [os.path.basename(p) for p in not_reached],
                       "wall_seconds": wall, "cpu_seconds": cpu}, fh, indent=1)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
