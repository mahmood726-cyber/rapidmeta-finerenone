"""GATE 6 -- a trial name in reader-facing prose must carry its registration.

WHY. A swapped trial name reads perfectly. Two real trials, two real registrations, correct
spelling, plausible order, and nothing on the page contradicts it -- because the name is the
only place the identity is asserted. A swapped name BESIDE ITS REGISTRATION does not read
perfectly: the contradiction becomes visible to a reader and mechanical to a checker.

THREE ARMS.

A -- AT THE GENERATOR. An AST scan of the projector modules for render sites that interpolate
    a trial's name without interpolating a registration in the same rendered unit. This is the
    class fix: a page cannot carry a bare name if the generator cannot emit one.
    `build_app_v2.py`'s contributing-trials row already does the right thing and prints
    `no registry identifier` when there is none -- a stated absence, which is a correct answer.

B -- IN THE SERVED PROSE. Every store-known trial acronym occurring in a delivered page's
    rendered text, and whether a registration sits within 300 characters. Uses the contiguity
    matcher from gate 2, whose false-positive rate is measured, not assumed.

C -- THE REGRESSION, AND IT IS THE POINT. Wherever a pinned registration appears in rendered
    prose, the trial name beside it must be the one the registry gives. The two confirmed
    swaps -- NCT01539226 labelled ASPIRE, NCT01617096 labelled The Ring Study -- are the
    named positives. If this gate ever stops SEEING them it exits VACUOUS, not PASS.
"""
from __future__ import annotations

import ast
import collections
import glob
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402
import textmatch as TM                                                      # noqa: E402
from gate1_trial_identity import PINNED, names_present                      # noqa: E402

WINDOW = 300
ACRONYM = re.compile(r"^(?=.*[A-Z])[A-Z0-9][A-Z0-9\-‑ ]{2,24}$")

# the projector modules -- the things that actually build a delivered page
GENERATORS = ("ssot/build_app_v2.py", "ssot/build_tabbed.py", "ssot/paper_projector.py",
              "outputs/_baseline_projector.py")

NAME_FIELDS = {"name", "label", "trial", "trial_name", "acronym", "short_name"}
REG_FIELDS = {"nct", "registration", "trial_id", "registry_id", "source_url", "url", "doi",
              "pmid"}


def _subscript_names(node):
    """Every field name reached by .get('x') or ['x'] inside this expression."""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "get" and n.args:
            a = n.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.add(a.value)
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) \
                and isinstance(n.slice.value, str):
            out.add(n.slice.value)
    return out


def render_sites(src):
    """(lineno, fields) for every f-string/concatenation that emits HTML with a field in it.

    The unit is the enclosing BinOp/JoinedStr chain -- the thing that becomes one rendered
    fragment -- not the individual placeholder, because the registration is routinely
    interpolated a line below the name inside the same `<tr>`.
    """
    tree = ast.parse(src)
    sites = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.JoinedStr, ast.BinOp, ast.Call)):
            continue
        if isinstance(node, ast.Call):
            continue
        text = ""
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                text += n.value
        if "<" not in text:
            continue
        fields = _subscript_names(node)
        if fields & NAME_FIELDS:
            sites.append((getattr(node, "lineno", 0), fields, text[:80]))
    return sites


# probes: answers fixed before the visitor ran
SITE_PROBES = [
    ("x = f\"<td>{t.get('name')}</td>\"", True, False, "name only"),
    ("x = f\"<td>{t['label']}<br><small>{t.get('nct')}</small></td>\"", True, True,
     "name and nct in one fragment"),
    ("x = f\"<td>{d['n']}</td>\"", False, False, "no name field"),
    ("x = t.get('name')", False, False, "not a render site (no markup)"),
]


def pair_by_nearest(text, nct, radius=120):
    """Which pinned trial does the name paired with this registration belong to?

    PAIRS ON THE RENDERING CONVENTION, NOT ON RAW DISTANCE. This corpus renders
    `NAME <mdash> https://clinicaltrials.gov/study/NCTxxxxxxxx`, so a name PRECEDING the
    registration is its label and a name following it is the next row. Raw nearest-character
    distance got this wrong on a real page: the 44-character URL made `FOCUS 2` closer to
    NCT00509106 than its own label `FOCUS 1`, and the CORRECT ceftaroline pair read as a swap.
    A name that follows is used only when nothing precedes within the radius.

    THE RADIUS IS 120 CHARACTERS AND THAT IS DERIVED, NOT PICKED. A label and its registration
    are rendered adjacently; the longest separator this corpus emits between them is
    ` &mdash; https://clinicaltrials.gov/study/` at 43 characters, so 120 accommodates it with
    margin and excludes everything else. At 1200 the pairing swept in ordinary prose --
    "both contributing trials set a minimum age of 18 years on their registrations --
    NCT01539226 and NCT01617096" -- where the names sit 250 to 1100 characters away and are
    not labelling anything. That produced disagreement between occurrences on the same page
    and the gate reported AMBIGUOUS for a swap it had correctly seen twice. A co-occurrence is
    not a pairing, and the difference between them is a distance.

    Every occurrence of the registration is evaluated. Disagreement between occurrences is
    AMBIGUOUS -- a first-class answer, because a layout that pairs inconsistently is not
    evidence of a swap.

    Returns (verdict, evidence); verdict in {None, 'AGREES', 'SWAPPED', 'AMBIGUOUS'}.
    """
    occs = list(re.finditer(re.escape(nct), text))
    if not occs:
        return None, None
    names = []
    for other, spec in PINNED.items():
        for alias in spec["aliases"]:
            for om in re.finditer(r"(?<![a-z0-9])" + re.escape(alias.strip()) + r"(?![a-z0-9])",
                                  text, re.I):
                names.append((om.start(), om.end(), other))
    if not names:
        return None, None

    verdicts, evidence = set(), None
    for m in occs:
        before = [(m.start() - e, s0, e, t) for s0, e, t in names
                  if e <= m.start() and m.start() - e <= radius]
        after = [(s0 - m.end(), s0, e, t) for s0, e, t in names
                 if s0 >= m.end() and s0 - m.end() <= radius]
        pool = before or after
        if not pool:
            continue
        pool.sort()
        d0 = pool[0][0]
        ties = {t for d, _, _, t in pool if d == d0}
        if len(ties) > 1:
            verdicts.add("AMBIGUOUS")
            continue
        _, s0, e, nearest = pool[0]
        verdicts.add("AGREES" if nearest == nct else "SWAPPED")
        if evidence is None:
            lo, hi = max(0, s0 - 40), min(len(text), e + 140)
            evidence = {"named": [nearest], "context": text[lo:hi],
                        "paired_on": "preceding" if before else "following"}
    if not verdicts:
        return None, None
    if len(verdicts) > 1:
        return "AMBIGUOUS", evidence
    return verdicts.pop(), evidence


# ARM C'S KNOWN-NEGATIVE CONTROL: the ceftaroline pair is CORRECT in the store, so a page
# rendering it must NOT be called a swap. Keyed to an answer fixed outside this gate --
# ClinicalTrials.gov -- and it is the control that caught the window artefact.
ARM_C_NEGATIVES = [
    ("FOCUS 1 NCT00509106 ... FOCUS 2 NCT00621504", "NCT00509106"),
    ("FOCUS 1 NCT00509106 ... FOCUS 2 NCT00621504", "NCT00621504"),
    ("The Ring Study NCT01539226 and ASPIRE NCT01617096", "NCT01539226"),
    ("The Ring Study NCT01539226 and ASPIRE NCT01617096", "NCT01617096"),
    ("Contributing trials: FOCUS 2 (NCT00621504) 0.88; FOCUS 1 (NCT00509106) 0.91",
     "NCT00621504"),
    # ADDED AFTER A REAL-DATA FAILURE, and recorded as such. The reference-list rendering on
    # CEFTAROLINE_AUTO_FULL_REVIEW.html put a 44-character URL between a label and its id, so
    # raw nearest-distance paired NCT00509106 with FOCUS 2 and called the correct pair a swap.
    # The control did not catch it; the corpus did. Extending the control after the corpus
    # finds a case is legitimate; tuning the matcher until the ORIGINAL control passes is not.
    ("Included studies FOCUS 1 &mdash; https://clinicaltrials.gov/study/NCT00509106 "
     "FOCUS 2 &mdash; https://clinicaltrials.gov/study/NCT00621504 CAP China", "NCT00509106"),
    ("Included studies FOCUS 1 &mdash; https://clinicaltrials.gov/study/NCT00509106 "
     "FOCUS 2 &mdash; https://clinicaltrials.gov/study/NCT00621504 CAP China", "NCT00621504"),
]


def arm_a(gate, repo):
    kinds = collections.Counter()
    bare = []
    for rel in GENERATORS:
        path = os.path.join(repo, rel)
        if not os.path.exists(path):
            kinds["generator module absent"] += 1
            continue
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        try:
            sites = render_sites(src)
        except SyntaxError as exc:
            gate.broken("%s did not parse: %s" % (rel, exc))
            continue
        # DEDUPE BY (file, line). `ast.walk` yields every nested BinOp of one f-string
        # chain, so a single `<tr>` reported 20 times and the count was of AST nodes, not
        # render sites. A count of the wrong unit is the commonest error in this repository.
        best = {}
        for lineno, fields, snippet in sites:
            prev = best.get(lineno, set())
            best[lineno] = prev | fields
        for lineno in sorted(best):
            fields = best[lineno]
            kinds["render site naming a trial"] += 1
            if fields & REG_FIELDS:
                kinds["  with a registration in the same fragment"] += 1
            else:
                kinds["  with NO registration in the same fragment"] += 1
                bare.append("%s:%d  fields=%s" % (rel, lineno, sorted(fields & NAME_FIELDS)))
    return bare, kinds


def arm_bc(gate, repo, cases):
    page_map = H.load(os.path.join(repo, "ssot", "PAGE_MAP.json"))
    by_topic = collections.defaultdict(list)
    for page, objpath in page_map.items():
        by_topic[os.path.basename(os.path.dirname(objpath))].append(page)

    paths, _ = H.topic_objects(repo)
    acronyms = collections.defaultdict(set)
    for p in paths:
        obj = H.load(p)
        for tr in ((obj.get("inputs") or {}).get("trials") or []):
            if not isinstance(tr, dict):
                continue
            for k in ("name", "label", "trial", "acronym"):
                v = tr.get(k)
                if isinstance(v, str) and ACRONYM.match(v.strip()) and len(v.strip()) <= 25:
                    acronyms[H.topic_id(p)].add(v.strip())

    kinds = collections.Counter()
    bare_prose, swaps = [], []
    for topic, names in sorted(acronyms.items()):
        page = next((x for x in by_topic.get(topic, [])
                     if os.path.exists(os.path.join(repo, x))), None)
        if not page:
            kinds["topic has acronyms but no delivered page"] += 1
            continue
        with io.open(os.path.join(repo, page), encoding="utf-8", errors="replace") as fh:
            text = TM.page_text(fh.read())
        for n in sorted(names):
            occ = TM.occurrences(text, n)
            if not occ:
                kinds["acronym in the store, absent from the page"] += 1
                continue
            kinds["trial name in rendered prose"] += 1
            if TM.matches_contiguous(text, n, window=WINDOW):
                kinds["  with a registration within %dc" % WINDOW] += 1
            else:
                kinds["  with NO registration within %dc" % WINDOW] += 1
                bare_prose.append("%s: %r on %s" % (topic, n, page))

    # ARM C RUNS OVER EVERY DELIVERED PAGE, NOT OVER ARM B'S SURVIVORS.
    #
    # It was nested inside the acronym loop first, and the harness caught it: neither named
    # positive was ever SEEN, so the gate exited VACUOUS. `agyw-hiv-prep-review` labels its
    # trials "ASPIRE / MTN-020" and "The Ring Study", and the acronym filter admits neither --
    # a slash, and a lower-case word. The motivating case was hidden by a filter written three
    # functions away, which is the exact failure this gate was built to make impossible.
    #
    # AND IT PAIRS BY NEAREST NAME, NOT BY A WINDOW. A 300-character window around the first
    # occurrence of an NCT reported all four pinned trials as swapped, including the
    # ceftaroline pair that is CORRECT: both names appear inside one table, so the window
    # contained both and any set that was not exactly {this trial} looked like a swap. That is
    # page layout read as content -- the same defect gate 2 exists to measure -- and it shipped
    # here because arm C had no control of its own. It has one now, below, and the CORRECT
    # ceftaroline pair is what it is keyed to.
    for page in sorted(os.path.basename(x)
                       for x in glob.glob(os.path.join(repo, "*_REVIEW.html"))):
        full = os.path.join(repo, page)
        with io.open(full, encoding="utf-8", errors="replace") as fh:
            text = TM.page_text(fh.read())
        for nct in PINNED:
            verdict, evidence = pair_by_nearest(text, nct)
            if verdict is None:
                continue
            gate.saw("prose:" + nct)
            if verdict == "AGREES":
                kinds["pinned registration, nearest name AGREES with the registry"] += 1
            elif verdict == "AMBIGUOUS":
                kinds["pinned registration, nearest name AMBIGUOUS -- not assessable"] += 1
            else:
                kinds["pinned registration, nearest name is a DIFFERENT pinned trial"] += 1
                swaps.append((page, nct, evidence["named"], evidence["context"]))
    return bare_prose, swaps, kinds


def main(argv):
    repo = H.repo_root()
    gate = H.Gate("6  NCT BESIDE THE NAME",
                  "a trial name in reader-facing prose must carry its registration, and the "
                  "name beside a registration must be the one the registry gives")
    gate.requires_control()

    cases = {}
    for nct in ("NCT01539226", "NCT01617096"):
        cases[nct] = gate.expect_case(
            "prose:" + nct,
            "%s appears in served prose with a pinned trial name beside it (%s)"
            % (nct, PINNED[nct]["name"]))

    # control for arm A's site detector
    wrong = []
    for src, is_site, has_reg, why in SITE_PROBES:
        sites = render_sites(src)
        got_site = bool(sites)
        got_reg = bool(sites and (sites[0][1] & REG_FIELDS))
        if got_site != is_site or (is_site and got_reg != has_reg):
            wrong.append(why)
    negatives = [p for p in SITE_PROBES if not p[1]]
    fp = sum(1 for src, _, _, _ in negatives if render_sites(src))
    # arm C's negatives: correct pairings that must NOT read as swaps
    c_fp = []
    for text, nct in ARM_C_NEGATIVES:
        v, ev = pair_by_nearest(text, nct)
        if v == "SWAPPED":
            c_fp.append("%s in %r read as SWAPPED" % (nct, text[:50]))
    gate.control(len(negatives) + len(ARM_C_NEGATIVES), fp + len(c_fp), wrong + c_fp)
    if wrong:
        gate.broken("arm A's render-site detector failed its probes: " + "; ".join(wrong))

    bare_gen, kinds_a = arm_a(gate, repo)
    bare_prose, swaps, kinds_bc = arm_bc(gate, repo, cases)

    if "--plant" in argv:
        bare_gen.append("ssot/__planted.py:1  fields=['label']")
        gate.note("PLANTED: a generator render site emitting a bare trial name")

    merged = dict(kinds_a)
    merged.update(kinds_bc)
    gate.kinds(merged)

    bare_keys = H.ratchet(gate, "GATE6_KNOWN_BARE_SITES.json", bare_gen,
                          "generator render sites emitting a trial name with no registration "
                          "in the same rendered fragment.")
    if os.path.exists(os.path.join(repo, "gates", "GATE6_KNOWN_BARE_SITES.json")):
        bare_gen = bare_keys
    swap_keys = ["%s %s" % (p, n) for p, n, _, _ in swaps]
    new_swaps = set(H.ratchet(gate, "GATE6_KNOWN_SWAPS.json", swap_keys,
                              "served pages rendering a pinned registration beside the wrong "
                              "pinned trial name.",
                              escalated="out/ESCALATIONS.jsonl 2026-08-28T15:05Z"))
    if os.path.exists(os.path.join(repo, "gates", "GATE6_KNOWN_SWAPS.json")):
        swaps = [x for x in swaps if "%s %s" % (x[0], x[1]) in new_swaps]
    for site in bare_gen:
        gate.finding("GENERATOR-EMITS-A-BARE-TRIAL-NAME",
                     "%s interpolates a trial name with no registration in the same rendered "
                     "fragment. A reader receives an identity claim with nothing beside it to "
                     "contradict." % site,
                     numerator=len(bare_gen), denominator=kinds_a.get(
                         "render site naming a trial", 0))
    for page, nct, named, near in swaps:
        gate.finding("SWAPPED-NAME-BESIDE-A-REGISTRATION",
                     "%s renders %s next to %s; the registry says %s. Context: %r"
                     % (page, nct, " and ".join(PINNED[n]["name"] for n in named),
                        PINNED[nct]["name"], near),
                     numerator=len(swaps), denominator=len(PINNED))

    gate.note("arm B counts prose names WITHOUT a registration nearby: %d of %d"
              % (kinds_bc.get("  with NO registration within %dc" % WINDOW, 0),
                 kinds_bc.get("trial name in rendered prose", 0)))
    gate.note("arm B is reported, not enforced, in this run: %d bare prose names is a class "
              "fix at the generator (arm A), not 155 page edits." % len(bare_prose))

    art = os.path.join(repo, "out", "gate6_nct_beside_name.json")
    os.makedirs(os.path.dirname(art), exist_ok=True)
    with open(art, "w", encoding="utf-8") as fh:
        json.dump({"gate": gate.as_json(), "generator_bare_sites": bare_gen,
                   "prose_bare_names": bare_prose,
                   "swaps": [{"page": p, "nct": n, "named": nm} for p, n, nm, _ in swaps]},
                  fh, indent=1)

    return gate.report(denominator="%d generator render sites; %d trial names in served prose"
                                   % (kinds_a.get("render site naming a trial", 0),
                                      kinds_bc.get("trial name in rendered prose", 0)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
