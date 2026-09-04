#!/usr/bin/env python3
"""GATE 16 -- CAN A READER STANDING ON THE PAGE PERFORM THE CHECK THEMSELVES?

Not "does the page have eight tabs". The claim this project makes is a
READER-LEVEL one, and until now it had been demonstrated exactly once, by hand,
on one page. A demonstration does not apply to the next topic. A gate does.

    TAKE AN INCLUDED TRIAL FROM THE PAGE. FIND ITS REGISTRATION BESIDE THE NAME.
    CLICK THROUGH TO THE REGISTRY AND CONFIRM IT. THEN READ WHAT THE PAGE SAYS
    YOU CANNOT CHECK.

WHY THIS IS THE THING WORTH GATING. The comparator Cochrane review for the
dapivirine question was measured by another lane: its abstract names the four
DATABASES it searched and never names the four TRIALS it included -- 3,848
characters, 0 NCT ids, 0 ISRCTN ids, 0 trial acronyms; PMC deposits the
structured abstract only, and the reference lists reachable through Europe PMC
and Crossref are flat and unpartitioned. So a reader CANNOT perform this check
against the counterpart at all. That asymmetry is the entire moat, and it is
worth nothing as an assertion and everything as a number.

THE FOUR CLAUSES, each planted separately below

  1 NAME BESIDE REGISTRATION. Every included trial's name and its registration
    identifier occur within NEAR_WINDOW characters of each other in the rendered
    body. The window is DECLARED, not tuned: 300 characters, chosen before the
    first run and printed in every report.

  2 THE REGISTRATION IS ONE CLICK. Every included registration appears inside an
    <a href> pointing at a registry URL that contains that same id.

    ⚠️ AND RESOLUTION IS CHECKED VIA THE REGISTRY'S API, NEVER ITS HTML. This
    lesson cost a measurement: clinicaltrials.gov is a JavaScript shell, so
    fetching https://clinicaltrials.gov/study/NCT01539226 and searching the
    bytes for "NCT01539226" returns FALSE for a page that is perfectly fine. A
    raw-HTML check here produces a false negative about the registry and reads
    as a defect in our page. The API is the only honest probe, it is sampled
    rather than exhaustive, and the sample size is printed.

  3 EVERY SCREENED RECORD CARRIES A DECISION UNDER A NAMED RULE, AND THE GROUP
    COUNTS SUM TO THE TOTAL. The sum is what makes it checkable: 1,443 records
    in six named groups that add to 1,443 is an auditable statement; "1,443
    records screened" is not.

    ⚠️ THE DECISION IS CARRIED BY THE GROUP, NOT REPEATED ON EVERY ROW. A
    per-row search for a decision token reported "68 of 1,517" on a page where
    every one of 1,443 records is decided -- the instrument looked in the wrong
    place and accused the page. Count the groups and require them to sum.

  4 THE PAGE STATES WHAT A READER CANNOT CHECK. An honest limit beside a strong
    claim is what makes the claim survive. A page that only asserts is weaker
    than one that also declines.

⛔ THIS GATE IS A RATCHET, NOT AN ULTIMATUM. Most of this corpus predates the
format. The baseline records where each page stands; the count may only improve.
A gate that refuses 148 of 149 pages blocks every lane for a debt none of them
incurred -- which this project shipped once already and will not again.
"""
import html as _htmlmod
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                    # noqa: E402

REPO = H.repo_root()
BASELINE = os.path.join(REPO, "scripts", "baselines", "reader_check_baseline.json")

# DECLARED BEFORE THE FIRST RUN AND NOT TUNED AFTERWARDS.
NEAR_WINDOW = 300
API_SAMPLE = 3

# Built with chr(92) so no shell transport can mangle the escape.
SCRIPT_RE = re.compile('<script' + chr(92) + 'b.*?</script>', re.S)

NCT = re.compile(r"\bNCT\d{8}\b")
OTHER_REG = re.compile(r"\b(?:ISRCTN\d{6,8}|ACTRN\d{14}|ChiCTR[-A-Za-z0-9]{6,}"
                       r"|CTRI/\d{4}/\d{2,3}/\d{6}|\d{4}-\d{6}-\d{2})\b")
REGISTRY_HOST = re.compile(
    r"https?://(?:www\.)?(?:clinicaltrials\.gov|isrctn\.com|anzctr\.org\.au"
    r"|chictr\.org\.cn|ctri\.nic\.in|clinicaltrialsregister\.eu"
    r"|trialsearch\.who\.int)", re.I)
DECISION = re.compile(r"\b(INCLUDE[A-Z_]*|EXCLUDE[A-Z_]*|UNDECIDABLE|PASS[A-Z_]*"
                      r"|DEFER[A-Z_]*|WITHHELD)\b")
CANNOT = re.compile(
    r"(?:not recorded|no[t]? established|cannot be checked|is UNKNOWN"
    r"|NOT that |does not establish|no risk-of-bias|is not the same as none"
    r"|withheld|not derivable)", re.I)


def _body(html):
    """Rendered body: after the stylesheet, scripts removed, ENTITIES DECODED.

    An id that appears only inside <script> is not something a reader can see,
    and counting it would credit the page for a check nobody can perform.

    ⛔ AND THE ENTITIES ARE DECODED, WHICH THE FIRST VERSION DID NOT DO. The
    page escapes an apostrophe:

        Efficacy of GSK Biologicals&#x27; Candidate Malaria Vaccine 257049
        &mdash; https://clinicaltrials.gov/study/NCT00866619

    while the store holds a literal apostrophe. A literal match against the
    source therefore failed for a name that IS rendered, adjacent to its
    registration, exactly as clause 1 requires -- and the page was scored as
    failing.

        COMPARE AGAINST WHAT A READER READS, NOT AGAINST THE BYTES.

    This project has the same lesson written down from the other direction,
    where a check against source reported 67 of 71 edits applied and the true
    figure was 46. Markup and entities both break a literal match; both are
    normalised here, once, so that no caller has to remember.
    """
    body = re.sub(SCRIPT_RE, ' ', html.split('</style>', 1)[-1])
    return _htmlmod.unescape(body)


def _panel(body, pid):
    m = re.search(r'<section class="panel" id="%s">(.*?)</section>' % pid, body, re.S)
    return m.group(1) if m else ""


_PAGE_MAP = None


# A RETIRED-REVIEW TOMBSTONE IS A THIRD KIND OF PAGE. Not a review, not a defect.
# scripts/check_page_format.py already knew this; gate 16 did not, and the cost was a
# reported finding that did not exist: 13 pages were counted as "stating no limit on
# what they establish" when they are 2.7-6 KB redirect stubs carrying no tabs, no
# protocol panel and no claims at all --
#
#     "Lenacapavir for HIV pre-exposure prophylaxis: NOT POOLABLE -- COMPARATOR
#      -- retired, answered at lenacapavir-prep"
#
# A page that makes no claim correctly declines nothing. Counting it as a failure of
# clause 4 is the "a control is not data and not a defect, it is a THIRD thing" error,
# and it inflated the c4 population from 0 to 13.
#
# The rule is copied deliberately from check_page_format.py rather than reinvented, so
# the two instruments cannot drift into disagreeing about what a page IS.
TOMBSTONE_RE = re.compile(r"has been retired|Retired review|retired, answered at", re.I)


def is_tombstone(html):
    return bool(TOMBSTONE_RE.search(html)) and len(html) < 20000


def store_for(page):
    """The object behind a page: PAGE_MAP first, the slug convention second.

    ⛔ THE SLUG CONVENTION ALONE IS NOT THE POPULATION, AND THIS GATE'S FIRST RUN
    PROVED IT. Deriving ssot/<lower-hyphen>/<same>.json resolved 59 of 1,427
    delivered pages and reported 4.1% coverage as though the other 1,368 simply
    had no object. 100 of them are named in ssot/PAGE_MAP.json and have one.
    That is reach reported as coverage, in the gate written to report coverage --
    the fifth instance of that class in one night. Read the map.
    """
    global _PAGE_MAP
    if _PAGE_MAP is None:
        mp = os.path.join(REPO, "ssot", "PAGE_MAP.json")
        try:
            with io.open(mp, encoding="utf-8") as fh:
                _PAGE_MAP = json.load(fh)
        except Exception:
            _PAGE_MAP = {}
    rel = _PAGE_MAP.get(page) or _PAGE_MAP.get("./" + page)
    if isinstance(rel, str):
        p = os.path.join(REPO, rel.replace("/", os.sep))
        if os.path.exists(p):
            return p
    slug = re.sub(r"\.html$", "", page).lower().replace("_", "-")
    p = os.path.join(REPO, "ssot", slug, slug + ".json")
    return p if os.path.exists(p) else None


def included_ids(canon):
    ids = set()
    for t in (canon.get("inputs") or {}).get("trials") or []:
        if isinstance(t, dict):
            for key in ("nct", "nct_id", "registration", "id"):
                v = t.get(key)
                if isinstance(v, str) and NCT.search(v):
                    ids.add(NCT.search(v).group(0))
    return ids


# ⛔ THERE IS NO LENGTH CAP, AND ADDING ONE WAS A SECOND DEFECT IN THE FIX.
# The first repair capped candidates at 80 characters on the reasoning that a
# 300-character official title is not a name. True -- but 40 pages RENDER their
# long label, and capping it made clause 1 INAPPLICABLE for them rather than
# passing. The headline moved 138 -> 144 while the number of pages actually
# CHECKED for clause 1 fell by 40.
#
#     A FIX THAT IMPROVES THE HEADLINE BY SHRINKING THE DENOMINATOR IS NOT A FIX.
#
# Short candidates are simply tried FIRST, because that is what a reader
# recognises; the long label remains a candidate and still counts if the page
# renders it.


def trial_names(canon):
    """Candidate names PER TRIAL, in the order a reader would recognise them.

    ⛔ THE FIRST VERSION READ `label` AND DEMANDED IT VERBATIM, WHICH IS WHY
    CLAUSE 1 REPORTED SEVEN FAILING PAGES THAT ARE FINE. Some objects store the
    registry's OFFICIAL TITLE in `label` -- 300+ characters, e.g. "A MULTICENTER,
    INTERNATIONAL, PHASE 3, DOUBLE-BLIND, PLACEBO-CONTROLLED, RANDOMIZED STUDY TO
    EVALUATE THE EFFICACY, SAFETY AND TOLERABILITY OF DAILY ORAL DOSING OF
    TAFAMIDIS MEGLUMINE..." -- while the page renders the ACRONYM, which is what
    a reader recognises:

        ATTR-ACT | ... | NCT01994889 | <a href='.../study/NCT01994889'>

    That is exactly what the clause exists to require, and it was scored as a
    failure because a 300-character title appears nowhere on the page. THE PAGE
    WAS RIGHT AND THE INSTRUMENT WAS ASKING THE WRONG QUESTION.

    So: return every candidate a reader might see, and let the clause pass if ANY
    of them sits beside a registration. A trial named by NONE of its candidates
    is a DIFFERENT finding and is reported separately -- "the page names this
    trial by none of the names the store holds" is not the same defect as "the
    name is there and the registration is not", and merging them hid both.
    """
    per_trial = []
    for t in (canon.get("inputs") or {}).get("trials") or []:
        if not isinstance(t, dict):
            continue
        cands = []
        for key in ("acronym", "short_name", "name", "label"):
            v = t.get(key)
            if not isinstance(v, str):
                continue
            for part in re.split(r"\s*/\s*", v.strip()):
                part = part.strip()
                if len(part) >= 4 and part not in cands:
                    cands.append(part)
        if cands:
            per_trial.append(sorted(cands, key=len))
    return per_trial


def assess(page, html, canon):
    """Return (clause_results, evidence). Each clause is True / False / None(n.a.)."""
    body = _body(html)
    ids = included_ids(canon)
    names = trial_names(canon)
    ev = {}

    # ---- clause 1: name beside registration ------------------------------
    if not names or not ids:
        c1 = None
        ev["c1"] = "no trial names or no registrations in the object"
    else:
        ok = unnamed = 0
        for cands in names:
            seen_any = False
            hit = False
            for nm in cands:
                for m in re.finditer(re.escape(nm), body):
                    seen_any = True
                    w = body[max(0, m.start() - NEAR_WINDOW):m.end() + NEAR_WINDOW]
                    if NCT.search(w) or OTHER_REG.search(w):
                        hit = True
                        break
                if hit:
                    break
            if hit:
                ok += 1
            elif not seen_any:
                unnamed += 1
        c1 = (ok == len(names))
        ev["c1"] = ("%d of %d trial(s) have a registration within %d chars of a "
                    "name the page renders%s"
                    % (ok, len(names), NEAR_WINDOW,
                       "; %d named by NONE of the store's candidates" % unnamed
                       if unnamed else ""))

    # ---- clause 2: the registration is one click --------------------------
    if not ids:
        c2 = None
        ev["c2"] = "the object records no registration"
    else:
        linked = set()
        # BOTH QUOTE STYLES, AND THE FIRST VERSION HAD ONLY ONE.
        # This matched href="..." and the generator emits
        # href='...' -- so clause 2 reported "0 of 2
        # registration(s) are a registry link" for pages whose links are
        # perfectly good, and a corpus figure of 98 failing pages was
        # substantially this regex rather than the corpus.
        #
        # Same class as an extractor requiring a forward slash against a log
        # printing backslashes, caught hours earlier the same night: A QUOTE
        # STYLE IS A SEPARATOR, and a separator class that excludes the one
        # character actually in use fails toward a smaller, cleaner-looking
        # number. The failure direction is always the flattering one.
        # BOTH QUOTE STYLES. Built from chr() because the pattern must contain
        # a double quote, a single quote AND a backslash, and every attempt to
        # write it literally through a shell produced either a SyntaxError or a
        # silently wrong pattern. chr(92) is the backslash that a heredoc turns
        # into 0x08 when written as an escape -- which is how a dead regex sat
        # inside a green gate earlier tonight.
        _QS = chr(34) + chr(39)
        _BS = chr(92)
        _A = re.compile(
            '<a' + _BS + 'b[^>]*href=[' + _QS + ']([^' + _QS + ']+)['
            + _QS + '][^>]*>(.*?)</a>', re.S)
        for m in _A.finditer(body):
            href = m.group(1)
            if not REGISTRY_HOST.search(href):
                continue
            for nct in set(NCT.findall(href)) | set(NCT.findall(
                    re.sub(r"<[^>]+>", "", m.group(2)))):
                if nct in href:
                    linked.add(nct)
        c2 = ids.issubset(linked)
        ev["c2"] = "%d of %d registration(s) are a registry link containing the id" % (
            len(ids & linked), len(ids))

    # ---- clause 3: decided records, and the groups SUM --------------------
    sc = _panel(body, "pn-screen")
    groups = re.findall(
        r'<details class="screen-group"[^>]*>\s*<summary[^>]*>(.*?)</summary>', sc, re.S)
    if not groups:
        c3 = None
        ev["c3"] = "no screening ledger rendered on this page"
    else:
        named, total = 0, 0
        for g in groups:
            flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", g))
            n = re.search(r"(\d[\d,]*)\s+record", flat)
            if DECISION.search(flat):
                named += 1
            if n:
                total += int(n.group(1).replace(",", ""))
        claimed = 0
        m = re.search(r"(\d[\d,]*)\s*(?:of|/)\s*(\d[\d,]*)\s*record", sc, re.I)
        if m:
            claimed = int(m.group(2).replace(",", ""))
        c3 = (named == len(groups)) and total > 0 and (claimed in (0, total))
        ev["c3"] = ("%d group(s), %d carry a named decision, records sum to %d%s"
                    % (len(groups), named, total,
                       "" if claimed in (0, total) else " but the page claims %d" % claimed))

    # ---- clause 4: what a reader cannot check -----------------------------
    hits = CANNOT.findall(body)
    c4 = len(hits) > 0
    ev["c4"] = "%d statement(s) of what is not established" % len(hits)

    return {"c1": c1, "c2": c2, "c3": c3, "c4": c4}, ev


def probe_api(ids, out):
    """Resolve a SAMPLE via the registry API. Never via the registry's HTML."""
    import urllib.request
    ok, tried, errs = 0, 0, []
    for nct in sorted(ids)[:API_SAMPLE]:
        tried += 1
        u = ("https://clinicaltrials.gov/api/v2/studies/%s"
             "?fields=NCTId,BriefTitle" % nct)
        try:
            req = urllib.request.Request(u, headers={
                "User-Agent": "rapidmeta-gate16/1.0 (mailto:mahmood726@gmail.com)"})
            d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8"))
            got = (d.get("protocolSection", {}).get("identificationModule", {})
                   .get("nctId"))
            ok += 1 if got == nct else 0
            if got != nct:
                errs.append("%s resolved to %r" % (nct, got))
        except Exception as exc:
            errs.append("%s: %s" % (nct, str(exc)[:60]))
    out("  clause 2 RESOLUTION, sampled via the API (never the registry's HTML,")
    out("  which is a JS shell and returns a false negative): %d of %d resolved"
        % (ok, tried))
    for e in errs:
        out("     %s" % e)
    return ok, tried, errs


# =========================================================================================
# FOUR CLAUSES, FOUR PLANTS, EACH PAIRED WITH A CASE THAT MUST PASS.
#
# ⛔ A GATE WITH FOUR ARMS AND ONE DEAD ONE PASSES REVIEW BY EYE. That happened in this
# repo tonight: an audit whose negative control was wired to the value a correct run
# returns had never printed a count since the day it was written, and it looked fine.
# Planting the whole gate proves the gate; it does not prove any single arm.
#
# EACH PLANT IS PAIRED. A clause that always fails is as useless as one that never does,
# so every plant carries a sibling that must PASS through the same code path. A clause
# only counts as proven when its plant FAILS and its sibling PASSES.
#
# THESE ARE SYNTHETIC, IN MEMORY, AND TOUCH NOTHING ON DISK. A plant that mutates a
# delivered page has to restore it, and a restore that is verified by anything short of a
# byte comparison is how a test leaves damage behind. Nothing is written, so nothing can
# fail to be restored.
# =========================================================================================

_HEAD = "<style>x</style>"


def _synthetic(name, nct, *, linked=True, near=True, groups=None, limits=True):
    """Build a page whose four clauses are independently controllable."""
    reg = ('<a href="https://clinicaltrials.gov/study/%s">%s</a>' % (nct, nct)
           if linked else "<span>%s</span>" % nct)
    if near:
        trial = "<p>%s %s</p>" % (name, reg)
    else:
        trial = "<p>%s</p>%s<p>%s</p>" % (name, "<p>filler</p>" * 60, reg)
    screen = ""
    if groups:
        rows = []
        for label, n, decided in groups:
            head = ("%s &mdash; %d records." % (label, n)) if decided else                    ("group &mdash; %d records." % n)
            rows.append('<details class="screen-group"><summary>%s</summary>'
                        '<table><tr><td>r</td></tr></table></details>' % head)
        screen = ('<section class="panel" id="pn-screen">%s</section>' % "".join(rows))
    lim = ("<p>Whether they were prespecified is not recorded on this object.</p>"
           if limits else "<p>Everything here is established.</p>")
    return (_HEAD + '<section class="panel" id="pn-extract">%s</section>%s%s'
            % (trial, screen, lim))


def _store(name, nct):
    return {"inputs": {"trials": [{"label": name, "nct": nct}]}}


def plants(out):
    NAME, ID = "The Ring Study", "NCT01539226"
    GOOD_GROUPS = [("INCLUDE", 2, True), ("EXCLUDE", 8, True)]
    BAD_GROUPS = [("INCLUDE", 2, True), ("unlabelled", 8, False)]
    cases = [
        ("c1", "trial name far from any registration",
         _synthetic(NAME, ID, near=False, groups=GOOD_GROUPS),
         _synthetic(NAME, ID, near=True, groups=GOOD_GROUPS)),
        ("c2", "registration present but not a registry link",
         _synthetic(NAME, ID, linked=False, groups=GOOD_GROUPS),
         _synthetic(NAME, ID, linked=True, groups=GOOD_GROUPS)),
        ("c3", "a screening group carrying no named decision",
         _synthetic(NAME, ID, groups=BAD_GROUPS),
         _synthetic(NAME, ID, groups=GOOD_GROUPS)),
        ("c4", "a page stating no limit on what it establishes",
         _synthetic(NAME, ID, groups=GOOD_GROUPS, limits=False),
         _synthetic(NAME, ID, groups=GOOD_GROUPS, limits=True)),
    ]
    canon = _store(NAME, ID)
    ok = True
    out("  PLANTS -- one per clause, each paired with a case that must PASS")
    for clause, what, planted, clean in cases:
        cl_bad, ev_bad = assess("__plant.html", planted, canon)
        cl_ok, ev_ok = assess("__plant.html", clean, canon)
        fired = (cl_bad.get(clause) is False)
        clean_ok = (cl_ok.get(clause) is True)
        verdict = "PROVEN" if (fired and clean_ok) else "*** NOT PROVEN ***"
        out("    %s  %-46s plant=%s clean=%s  %s"
            % (clause, what[:46],
               "FAIL" if fired else str(cl_bad.get(clause)),
               "PASS" if clean_ok else str(cl_ok.get(clause)), verdict))
        out("        planted: %s" % ev_bad.get(clause, ""))
        out("        clean  : %s" % ev_ok.get(clause, ""))
        if not (fired and clean_ok):
            ok = False
    out("  %s" % ("all four clauses proven: each plant fails and each sibling passes"
                  if ok else
                  "AT LEAST ONE CLAUSE IS NOT PROVEN -- it cannot report, and every "
                  "count this gate prints that depends on it means nothing"))
    return ok


def pages():
    out = []
    for fn in sorted(os.listdir(REPO)):
        if fn.endswith(".html") and fn.isupper() is False and "_REVIEW" in fn:
            out.append(fn)
    return out


def main(argv):
    gate = H.Gate("16 READER CAN CHECK",
                  "a reader can take a trial from the page, find its registration "
                  "beside the name, and confirm it in the registry")
    gate.requires_control()

    ref = os.environ.get("GATE16_REF") or "working tree"
    try:
        import subprocess
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                              capture_output=True, timeout=120).stdout.decode().strip()
    except Exception:
        head = "unknown"

    say = (lambda s: sys.stdout.write(s + "\n"))
    say("  REF READ: %s at %s -- three page counts have been three different"
        % (ref, head))
    say("  populations in one night, so the ref is printed before any number.")

    if "--plant" in argv:
        if not plants(say):
            return 3
        say("")

    gate.expect_case("c1-fail", "a page whose trial name carries no nearby registration")
    gate.expect_case("c2-fail", "a page whose registration is not a registry link")
    # CLAUSE 4 HAS ZERO INSTANCES IN THIS CORPUS AND IS DELIBERATELY NOT A NAMED
    # POSITIVE. It was one, and the gate went VACUOUS the moment tombstones were
    # excluded -- because the only pages "failing" it were 2.7 KB retirement stubs
    # that make no claims at all. Every genuine page in this corpus states a limit
    # on what it establishes, which is a result worth having rather than a gap.
    #
    # Declaring a case that cannot occur makes every run vacuous, and vacuous is
    # worse than failing: it reads as a pass. So clause 4 is proven by PLANT
    # (--plant: plant=FAIL clean=PASS) and its corpus instance count is stated
    # here as zero. The day a page fails it, this note is what tells the next
    # reader the arm had never been exercised on real data until then.
    gate.note("clause 4 has ZERO instances in this corpus -- every assessable page "
              "states a limit on what it establishes. The clause is proven by plant, "
              "not by a corpus positive, and that is recorded rather than implied.")
    gate.expect_case("pass", "a page that satisfies every applicable clause")

    kinds = {}
    results = {}
    all_pages = pages()
    examined = 0
    for page in all_pages:
        sp = store_for(page)
        if sp is None:
            kinds["no store resolves -- not assessable, not passed"] = \
                kinds.get("no store resolves -- not assessable, not passed", 0) + 1
            continue
        try:
            with io.open(os.path.join(REPO, page), encoding="utf-8", errors="replace") as fh:
                html = fh.read()
            with io.open(sp, encoding="utf-8") as fh:
                canon = json.load(fh)
        except Exception:
            kinds["unreadable page or store"] = kinds.get("unreadable page or store", 0) + 1
            continue
        if is_tombstone(html):
            kinds["retired-review tombstone -- a third kind, excluded and named"] = \
                kinds.get("retired-review tombstone -- a third kind, excluded and named",
                          0) + 1
            continue
        examined += 1
        cl, ev = assess(page, html, canon)
        results[page] = (cl, ev)
        applicable = [k for k, v in cl.items() if v is not None]
        passed = [k for k in applicable if cl[k]]
        if len(passed) == len(applicable) and applicable:
            kinds["READER CAN CHECK -- every applicable clause"] = \
                kinds.get("READER CAN CHECK -- every applicable clause", 0) + 1
            gate.saw("pass")
        else:
            for k in applicable:
                if not cl[k]:
                    kinds["fails clause %s" % k] = kinds.get("fails clause %s" % k, 0) + 1
                    if k == "c1":
                        gate.saw("c1-fail")
                    if k == "c2":
                        gate.saw("c2-fail")
                    if k == "c4":
                        gate.saw("c4-fail")

    # ---------------- pinned c1 case, because the corpus one was REPAIRED ----
    #
    # A CONTROL ANCHORED TO A LIVE CORPUS DEFECT RETIRES ITSELF THE MOMENT THE DEFECT
    # IS FIXED. On 2026-09-04 ALIROCUMAB_LIPID_AUTO_FULL_REVIEW was the LAST page in
    # this corpus failing clause 1: its Contributing-trials table rendered 6 rows under
    # a headline stating k=8, so two trials -- NCT02289963 and NCT02585778 -- were named
    # nowhere near a registration. Repairing that truncation (02a056a31) satisfied c1
    # and left this gate VACUOUS on its own motivating case: it went BROKEN and refused
    # to print a count, which is the correct behaviour and is why the state was noticed.
    #
    # SO THE REPAIR SPENT THE CONTROL. Every repair silently disarms the detector that
    # found it unless that detector's case is synthetic or pinned. This is the pinned
    # form: the ACTUAL pre-repair bytes, not an approximation of them --
    #
    #     gates/GATE16_C1_PINNED.html        1,344,077 B, sha256 0e3b1046866754d6...
    #     gates/GATE16_C1_PINNED_STORE.json  the store as it stood beside them
    #     taken from b77214332dd634e510907ce09d1cac18b1d2deeb:ALIROCUMAB_LIPID_AUTO_FULL_REVIEW.html
    #
    # IT IS ASSESSED THROUGH THE SAME assess() AS EVERY OTHER PAGE and no clause was
    # touched to accommodate it. It is NOT added to `results`, so it cannot enter the
    # ratchet, the counts or the false-positive rate: it does one thing, which is to
    # keep `c1-fail` reachable. Following clause 4's precedent, its provenance is stated
    # on the page rather than implied -- but unlike clause 4 this arm is NOT downgraded
    # to a note, because a clause with a real historical instance should keep having to
    # prove it can fail. Weakening the control would need its owner; strengthening it
    # does not.
    pin_html = os.path.join(REPO, "gates", "GATE16_C1_PINNED.html")
    pin_store = os.path.join(REPO, "gates", "GATE16_C1_PINNED_STORE.json")
    if os.path.exists(pin_html) and os.path.exists(pin_store):
        try:
            with io.open(pin_html, encoding="utf-8", errors="replace") as fh:
                _ph = fh.read()
            with io.open(pin_store, encoding="utf-8") as fh:
                _pc = json.load(fh)
            _pcl, _pev = assess("GATE16_C1_PINNED.html", _ph, _pc)
            if _pcl.get("c1") is False:
                gate.saw("c1-fail")
                gate.note("c1-fail was reached via the PINNED fixture, not the corpus: "
                          "%s. The corpus instance was repaired on 2026-09-04 and this "
                          "clause now has ZERO live instances." % _pev.get("c1", ""))
            else:
                gate.broken("the pinned c1 fixture no longer fails clause 1. A pinned "
                            "control that stops firing has been altered or the clause "
                            "has changed underneath it; either way this gate can no "
                            "longer prove it detects what it claims to.")
        except Exception as exc:
            gate.broken("the pinned c1 fixture could not be read (%s), so clause 1 has "
                        "no reachable positive case." % type(exc).__name__)
    else:
        gate.broken("the pinned c1 fixture is missing, so clause 1 has no reachable "
                    "positive case and no count from this gate is trustworthy.")

    # ---------------- controls, counted from the SAME traversal -------------
    neg = "AGYW_HIV_PREP_REVIEW.html"
    fp = 0
    examples = []
    if neg in results:
        cl, ev = results[neg]
        bad = [k for k, v in cl.items() if v is False]
        if bad:
            fp = 1
            examples.append("%s flagged on %s -- %s"
                            % (neg, ",".join(bad), "; ".join(ev[k] for k in bad)))
    else:
        gate.broken("the known-negative control %s was not reached by the traversal, "
                    "so the false-positive rate is unmeasured and no count is "
                    "trustworthy." % neg)
    n_neg = 1 if neg in results else 0
    gate.control(n_neg, fp, examples)

    # ---------------- ratchet -----------------------------------------------
    base = {}
    if os.path.exists(BASELINE):
        with io.open(BASELINE, encoding="utf-8") as fh:
            base = json.load(fh).get("pages", {})

    def score(cl):
        ap = [k for k, v in cl.items() if v is not None]
        return sum(1 for k in ap if cl[k]), len(ap)

    for page, (cl, ev) in sorted(results.items()):
        got, ap = score(cl)
        was = base.get(page)
        if was is None:
            if ap and got < ap:
                gate.finding("NEW-PAGE-BELOW-THE-READER-CHECK",
                             "%s is not in the baseline and passes %d of %d applicable "
                             "clause(s): %s" % (page, got, ap,
                                                "; ".join("%s %s" % (k, ev[k])
                                                          for k in ("c1", "c2", "c3", "c4")
                                                          if cl[k] is False)),
                             numerator=got, denominator=ap)
        elif got < was:
            gate.finding("READER-CHECK-REGRESSED",
                         "%s fell from %d to %d of %d applicable clause(s): %s"
                         % (page, was, got, ap,
                            "; ".join("%s %s" % (k, ev[k])
                                      for k in ("c1", "c2", "c3", "c4")
                                      if cl[k] is False)),
                         numerator=got, denominator=ap)

    # ---------------- distribution, printed before any verdict --------------
    dist = {}
    for page, (cl, ev) in results.items():
        got, ap = score(cl)
        dist["%d of %d" % (got, ap)] = dist.get("%d of %d" % (got, ap), 0) + 1
    say("")
    say("  READER-CHECK DISTRIBUTION over %d assessable page(s):" % len(results))
    for k in sorted(dist, reverse=True):
        say("     %-10s %4d page(s)" % (k, dist[k]))
    full = sum(v for k, v in dist.items() if k.split(" of ")[0] == k.split(" of ")[-1])
    say("")
    say("  ⭐ PAGES A READER CAN FULLY CHECK: %d of %d assessable (%d delivered "
        "review pages in total)" % (full, len(results), len(all_pages)))

    if "--api" in argv:
        for page, (cl, ev) in sorted(results.items()):
            sp = store_for(page)
            with io.open(sp, encoding="utf-8") as fh:
                ids = included_ids(json.load(fh))
            if ids:
                probe_api(ids, say)
                break

    gate.kinds(kinds)
    gate.coverage(examined, len(all_pages),
                  "delivered review pages whose slug does not resolve to an SSOT "
                  "object -- NOT assessable, and counted as a named kind rather "
                  "than dropped from the denominator")
    return gate.report(denominator="%d delivered review page(s), %d assessable, "
                                   "window %d chars"
                                   % (len(all_pages), len(results), NEAR_WINDOW))


if __name__ == "__main__":
    # NO sys.stdout REASSIGNMENT HERE, DELIBERATELY. gates/_harness.py already
    # installs a UTF-8 wrapper at import time. Wrapping sys.stdout.buffer a
    # second time gives two wrappers over one buffer, and when either is
    # collected it CLOSES that buffer -- the next print dies with
    # "I/O operation on closed file". This gate did exactly that on its first
    # run. Use the wrapper the harness installed.
    sys.exit(main(sys.argv[1:]))
