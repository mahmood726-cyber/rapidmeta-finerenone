# -*- coding: utf-8 -*-
"""Is a delivered page at FULL MOAT STANDARD, judged on the bytes a reader receives?

⛔ gate16 READS THE WORKTREE. THIS READS THE SERVED SITE. Those are different
populations and have disagreed by a full deploy cycle tonight: a worktree build
scored 8 of 8 tabs while the live page served 6, because the push had not
happened. Every claim here is about what a reader can do RIGHT NOW.

FULL MOAT STANDARD, per page, all measured on the fetched bytes:

    c1  every included trial's name sits within 300 chars of a registration
    c2  every registration is a link to a registry URL containing that id
    c3  every screened record carries a decision under a named rule, groups summing
    c4  the page states what a reader cannot check
    tabs        how many of the RULED EIGHT the served nav carries
    correction  if the page is listed as carrying a published correction,
                is that correction still in the served bytes

⛔ NO TOPIC SILENTLY DROPS OUT. A page that does not resolve, does not fetch, or
returns a non-200 is recorded as a NAMED STATE -- NO_PAGE / FETCH_FAILED /
HTTP_<code> -- never as an absence from a list. Absence from a list is not a
property of a page, and acting on one is how a protection list scoped to one
criterion gets read as clearance for another.

    python scripts/moat_standard_served.py [PAGE.html ...]     # default: all assessable
    python scripts/moat_standard_served.py --topics topics.txt # one page or topic per line

Prints MEASURED beside every observation and the command that produced it.
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "gates"))

SITE = "https://mahmood726-cyber.github.io/rapidmeta-finerenone/"
UA = {"User-Agent": "rapidmeta-moat-standard/1.0 (mailto:mahmood726@gmail.com)",
      "Cache-Control": "no-cache", "Pragma": "no-cache"}


# =========================================================================================
# TABS PRESENT vs TABS WITH CONTENT, AND THE TWO NUMBERS NEVER MERGE.
#
# ⛔ THE FIRST VERSION COUNTED PRESENCE AND CALLED IT THE MOAT STANDARD. A rebuild took five
# pages from 6/8 to 8/8 by adding two tabs that say
#
#     "Not held in this object. No guideline view is held in this object."
#
# 383 characters against 723,751 on a populated tab. That is not a rendering difference, it
# is a different artefact wearing the same tab name -- and it would have scored 148 pages as
# full moat standard on tabs that decline.
#
#     A TAB THAT DECLINES IS HONEST AND IT IS NOT THE DELIVERABLE.
#
# It is genuinely valuable and it is already counted, under clause c4 -- "the page states
# what a reader cannot check". Counting it TWICE, once as content, is the metric-flattery
# this project exists to refuse. Every other instrument defect found here failed toward
# alarm; this one failed toward success, which is why it nearly shipped.
#
# THE RULE, STATED BEFORE THE FIRST RUN AND NOT TUNED AFTERWARDS, AND STRUCTURAL RATHER THAN
# A CHARACTER THRESHOLD -- a threshold is a number someone adjusts until the corpus looks
# right, and the generator already marks its own declinations:
#
#     A tab carries CONTENT if, after removing every <div class="absent-state"> block, the
#     panel still contains at least one EVIDENCE-BEARING element: a table row, a list item,
#     a paragraph, or a figure.
#
#     A HEADING ALONE DOES NOT COUNT. A heading names a section that is not there.
# =========================================================================================
ABSENT_BLOCK = re.compile(r"<div[^>]*class=[\"']absent-state[\"'][^>]*>.*?</div>", re.S | re.I)
EVIDENCE = re.compile(r"<(?:tr|li|p|svg|table|img)\b", re.I)


def tab_has_content(body, panel_id):
    """(present, has_content) for one panel, structurally."""
    m = re.search(r'<section class="panel" id="%s">(.*?)</section>' % panel_id, body, re.S)
    if not m:
        return False, False
    seg = ABSENT_BLOCK.sub(" ", m.group(1))
    return True, bool(EVIDENCE.search(seg))


def plant_content_detector(out):
    """The detector MUST score a declination-only tab as EMPTY."""
    mk = lambda inner: '<section class="panel" id="pn-x">%s</section>' % inner
    cases = [
        ("a declination only",
         mk('<div class="absent-state" role="note"><strong>Not held in this object.</strong>'
            ' <p>No guideline view is held in this object.</p></div>'), False),
        ("a real table row", mk("<table><tr><td>ATTR-ACT</td></tr></table>"), True),
        ("a heading only", mk("<h3>Guideline</h3>"), False),
        ("a declination AND a real row",
         mk('<div class="absent-state"><p>Not held.</p></div>'
            "<table><tr><td>x</td></tr></table>"), True),
    ]
    ok = True
    out("  PLANT -- the content detector must not credit a declination")
    for what, html, want in cases:
        _, got = tab_has_content(html, "pn-x")
        mark = "ok" if got == want else "*** WRONG ***"
        out("    %-30s content=%-5s expected=%-5s %s" % (what, got, want, mark))
        if got != want:
            ok = False
    return ok


def load_gate():
    import importlib.util
    p = os.path.join(ROOT, "gates", "gate16_reader_can_check.py")
    spec = importlib.util.spec_from_file_location("g16", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def gate_commit():
    r = subprocess.run(["git", "log", "-1", "--format=%h %s",
                        "--", "gates/gate16_reader_can_check.py"],
                       cwd=ROOT, capture_output=True, timeout=200)
    return r.stdout.decode("utf-8", "replace").strip()


def remote_ref():
    r = subprocess.run(["git", "ls-remote", "origin", "main"],
                       cwd=ROOT, capture_output=True, timeout=300)
    out = r.stdout.decode("utf-8", "replace").split()
    return out[0][:12] if out else "UNREADABLE"


def fetch(page):
    try:
        req = urllib.request.Request(SITE + page, headers=UA)
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.read().decode("utf-8", "replace"), "HTTP_%s" % r.status
    except urllib.error.HTTPError as e:
        return None, "HTTP_%s" % e.code
    except Exception as exc:
        return None, "FETCH_FAILED:%s" % type(exc).__name__


def required_tabs():
    p = os.path.join(ROOT, "ssot", "page_format_v1.json")
    with io.open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    return [(t.get("id"), str(t.get("panel_id_hint") or "").replace("pn-", ""))
            for t in d.get("required_tabs") or []]


def corrections():
    p = os.path.join(ROOT, "scripts", "baselines", "published_corrections.json")
    if not os.path.exists(p):
        return None
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh).get("pages", {})


def main():
    m = load_gate()
    req = required_tabs()
    corr = corrections()

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--topics" in sys.argv:
        i = sys.argv.index("--topics")
        with io.open(sys.argv[i + 1], encoding="utf-8") as fh:
            args = [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    pages = args or [p for p in m.pages() if m.store_for(p)]

    print("MOAT STANDARD, ON THE SERVED BYTES")
    print("  ref  origin/main = %s        MEASURED  (git ls-remote origin main)"
          % remote_ref())
    print("  gate %s" % gate_commit())
    print("           MEASURED  (git log -1 -- gates/gate16_reader_can_check.py)")
    print("  ruled tabs: %s" % ", ".join(t[0] for t in req))
    print("  corrections list: %s"
          % ("%d page(s)" % len(corr) if corr is not None else "ABSENT -- correction "
             "column is NOT_ASSESSABLE, not 'no correction'"))
    print("  pages to evaluate: %d" % len(pages))
    print("")
    if not plant_content_detector(print):
        print("REFUSED: the content detector does not behave as declared. No count "
              "is printed -- a detector that credits a declination measures nothing.")
        return 3
    print("")

    rows = []
    for n, page in enumerate(pages, 1):
        # POSITIVE FORM. Both this and the fetch check below already recorded a
        # NAMED state before continuing, so the semantics were right -- but the
        # syntactic shape `if X is None: continue` inside a corpus loop is the one
        # audit_exclusion_by_absence refuses, and it refuses it because the shape
        # is what gets copied. Stated positively there is nothing to copy wrong.
        sp = m.store_for(page)
        if sp is not None:
            pass
        else:
            rows.append((page, "NO_STORE", None, None, None))
            continue
        html, state = fetch(page)
        if html is not None:
            pass
        else:
            rows.append((page, state, None, None, None))
            print("  %3d/%d  %-46s %s" % (n, len(pages), page[:46], state))
            continue
        with io.open(sp, encoding="utf-8") as fh:
            canon = json.load(fh)
        if m.is_tombstone(html):
            rows.append((page, "TOMBSTONE", None, None, None))
            continue
        cl, ev = m.assess(page, html, canon)
        body = m._body(html)
        ids = dict(re.findall(r'<label for="rt-([a-z0-9_-]+)">([^<]+)</label>', body))
        tabs = sum(1 for _, hint in req if hint in ids)
        content = sum(1 for _, hint in req
                      if tab_has_content(body, "pn-" + hint)[1])
        c_state = "n/a"
        if corr is None:
            c_state = "NOT_ASSESSABLE"
        else:
            rec = corr.get(page)
            if rec and rec.get("class") == "PUBLISHED_CORRECTION":
                must = rec.get("must_render")
                if not must:
                    c_state = "UNPINNED"
                else:
                    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))
                    c_state = "PRESENT" if norm(must) in norm(body) else "*** DROPPED ***"
        rows.append((page, "OK", cl, (tabs, content), c_state))
        ap = [k for k, v in cl.items() if v is not None]
        got = sum(1 for k in ap if cl[k])
        print("  %3d/%d  %-44s %d/%d clauses  present %d/%d  CONTENT %d/%d  corr=%s"
              % (n, len(pages), page[:44], got, len(ap), tabs, len(req),
                 content, len(req), c_state))
        time.sleep(0.15)

    print("")
    print("SUMMARY -- all MEASURED on fetched bytes")
    named = {}
    full = 0
    for page, state, cl, tabs, c in rows:
        if state != "OK":
            named[state] = named.get(state, 0) + 1
            continue
        ap = [k for k, v in cl.items() if v is not None]
        # ⭐ CONTENT, NOT PRESENCE. tabs[0] is presence and is reported; tabs[1]
        # is what the standard requires.
        ok = (all(cl[k] for k in ap) and tabs[1] == len(req)
              and c in ("n/a", "PRESENT"))
        full += 1 if ok else 0
    print("  pages evaluated              : %d" % sum(1 for r in rows if r[1] == "OK"))
    print("  AT FULL MOAT STANDARD        : %d" % full)
    print("     (every applicable clause, all %d ruled tabs, correction intact)"
          % len(req))
    for k, v in sorted(named.items()):
        print("  %-28s : %d   <- a NAMED state, not an absence" % (k, v))
    print("")
    print("  NOT at full standard, individually:")
    for page, state, cl, tabs, c in rows:
        if state != "OK":
            continue
        ap = [k for k, v in cl.items() if v is not None]
        bad = [k for k in ap if not cl[k]]
        if bad or tabs[1] != len(req) or c not in ("n/a", "PRESENT"):
            print("     %-44s fails %-12s present %d/%d  CONTENT %d/%d  corr=%s"
                  % (page[:44], ",".join(bad) or "-", tabs[0], len(req),
                     tabs[1], len(req), c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
