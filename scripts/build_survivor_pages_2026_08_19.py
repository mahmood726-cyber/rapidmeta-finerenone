#!/usr/bin/env python3
"""BUILD PAGES FOR THE THREE DEFERRED MERGE SURVIVORS, so their merges can execute.

THE DEPENDENCY, WHICH IS ALSO THE RULE. `execute_merges_2026_08_19.py` DEFERRED three clusters
because the survivor object -- the richer one, correctly chosen -- had never been built, while
the topic to be retired carried the live URL. Retiring a page-bearing topic in favour of an
object with no page would leave a tombstone pointing at a URL that does not exist.

    A POINTER IS ONLY SAFE ONCE ITS TARGET IS.

That generalises past tombstones to every redirect and cross-reference this corpus publishes,
and it is why these three pages come before the merges rather than after. Until they exist, each
deferred cluster is a KNOWN DUPLICATE STILL LIVE -- two pages answering one question.

THE THREE, AND WHY NONE OF THEM PUBLISHES A POOLED ESTIMATE:

  lenacapavir-prep            k=2, and the object publishes no pooled point. Both trials'
                              registered outcomes are read at every rank.
  mavacamten-ohcm-review      k=1. ONE TRIAL IS NOT A META-ANALYSIS, and the page says so as
                              its first statement rather than rendering an interval of one.
  pcsk9-inhibitors-cv-review  k=2 and its estimate was WITHDRAWN on 2026-08-19 -- FOURIER and
                              ODYSSEY OUTCOMES register composites differing on death, stroke
                              AND revascularisation. See withdraw_pcsk9_estimate_2026_08_19.py.

WHAT THE PAGES ARE CHECKED AGAINST. `regression_check.py` now holds a definition of correct for
a review that publishes nothing: it must DECLARE it publishes nothing, SAY so where a reader
sees it and not only in a meta tag, NAME at least one trial, and every link it offers must
resolve. These pages are built to satisfy that by construction, and the builder asserts it.

USAGE
    python scripts/build_survivor_pages_2026_08_19.py [--apply] [--selftest]
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retirement as R                                                  # noqa: E402

# ONLY THE SURVIVOR THAT GENUINELY HAS NO PAGE. The merge executor DEFERRED three clusters
# saying "THE SURVIVOR HAS NO PAGE", and for TWO OF THE THREE THAT WAS FALSE: the page existed
# on disk and PAGE_MAP simply had no entry for it. `page_for()` searches PAGE_MAP, so the
# executor was reporting the state of its own index as a fact about the world.
#
#   LENACAPAVIR_PREP_SSOT.html       21,276 bytes, titled exactly as `lenacapavir-prep`
#   PCSK9_INHIBITORS_CV_REVIEW.html 722,350 bytes, the survivor's real dashboard
#
# Those two needed a MAPPING, not a build. Acting on the deferral literally, this script wrote a
# 7.6 KB stub over the 722 KB dashboard and took the RETIREE's live URL for the survivor --
# destroying a real page and silently substituting content at a URL readers hold. Both reverted
# from HEAD before anything was committed.
#
#   AN ABSENCE REPORTED BY AN INDEX IS NOT AN ABSENCE IN THE WORLD. See the overwrite guard in
#   run(): this script now REFUSES to write any page that already exists on disk.
SURVIVORS = {
    "mavacamten-ohcm-review": {
        "page": "MAVACAMTEN_OHCM_REVIEW.html",
        "retires": "mavacamten-ohcm",
        "headline": "One trial -- not a meta-analysis",
        "why": ("This review holds ONE trial. A meta-analysis requires at least two studies "
                "with poolable data, so there is no pooled estimate here and no interval is "
                "rendered. What follows is a record of the single trial, which is what this "
                "topic honestly is."),
    },
}

# The two survivors whose page EXISTS and was merely unmapped. Listed so the correction is
# auditable rather than an unexplained PAGE_MAP edit.
MAP_ONLY = {
    "lenacapavir-prep": "LENACAPAVIR_PREP_SSOT.html",
    "pcsk9-inhibitors-cv-review": "PCSK9_INHIBITORS_CV_REVIEW.html",
}

CSS = """
 :root{color-scheme:light dark;--fg:#111;--bg:#fff;--mut:#555;--line:#d8d8d8;--warn:#8a4b00}
 @media (prefers-color-scheme:dark){:root{--fg:#eee;--bg:#111;--mut:#aaa;--line:#333;
   --warn:#e2a45c}}
 *{box-sizing:border-box}
 body{font:16px/1.62 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:56rem;
      margin:0 auto;padding:2.5rem 1.25rem 5rem;background:var(--bg);color:var(--fg)}
 h1{font-size:1.5rem;line-height:1.28;margin:.4rem 0 .2rem}
 h2{font-size:1.05rem;margin:2.4rem 0 .6rem;padding-bottom:.3rem;
    border-bottom:1px solid var(--line)}
 .tag{display:inline-block;font:600 .7rem/1 system-ui;letter-spacing:.09em;
      text-transform:uppercase;padding:.4rem .6rem;border:1px solid currentColor;
      border-radius:.25rem;opacity:.8;color:var(--warn)}
 .q{font-size:1.06rem;margin:1rem 0;padding:1rem 1.1rem;border-left:3px solid currentColor}
 .sub{color:var(--mut);font-size:.94rem}
 .wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:.8rem 0}
 table{border-collapse:collapse;width:100%;min-width:38rem;font-size:.9rem}
 th,td{text-align:left;padding:.5rem .6rem;border-bottom:1px solid var(--line);
       vertical-align:top}
 th{font-weight:600;white-space:nowrap}
 td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
 .why{margin:.9rem 0;padding:.85rem 1rem;border:1px solid var(--line);border-radius:.3rem}
 a.go{display:inline-block;margin:.4rem .6rem .4rem 0;padding:.6rem 1rem;
      border:1px solid currentColor;border-radius:.3rem;text-decoration:none;font-weight:600}
 footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);
        color:var(--mut);font-size:.86rem}
 code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em}
"""


def esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def load(topic):
    with io.open(os.path.join(REPO, "ssot", topic, topic + ".json"),
                 "r", encoding="utf-8") as fh:
        return json.load(fh)


def num(v):
    return "{:,}".format(v) if isinstance(v, int) else "&mdash;"


def primary_of(t):
    for k in ("outcome_definition", "registered_primary_title"):
        if t.get(k):
            return t[k]
    ps = t.get("registered_primaries") or []
    return ps[0] if ps else None


def trials_table(o):
    rows = []
    for t in (o.get("inputs") or {}).get("trials") or []:
        sec = t.get("registered_secondaries")
        rows.append(
            "<tr><td><code>%s</code></td><td>%s</td><td class='n'>%s</td><td>%s</td>"
            "<td class='n'>%s</td></tr>"
            % (esc(t.get("nct") or t.get("id")),
               esc(t.get("name") or ""),
               num((t.get("analysed") or {}).get("treatment")
                   if isinstance(t.get("analysed"), dict) else t.get("enrollment")),
               esc(primary_of(t) or "(not recorded on this object)"),
               len(sec) if isinstance(sec, list) else "&mdash;"))
    return "\n".join(rows)


def page(topic, spec, o):
    pr = ((o.get("results") or {}).get("by_outcome") or {}).get("primary") or {}
    pl = pr.get("pooled") or {}
    sup = pr.get("pooled_superseded")
    trials = (o.get("inputs") or {}).get("trials") or []

    withdrawn = ""
    if pl.get("withdrawn") and sup:
        withdrawn = (
            "<h2>The estimate that was withdrawn</h2>"
            "<div class='why'><p>This review served "
            "<code>%s %.4g (%.4g&ndash;%.4g)</code> at k=%s, computed with "
            "<code>%s</code>. It is <strong>withdrawn</strong> and kept on the object under "
            "<code>pooled_superseded</code> rather than deleted &mdash; what a reader saw is "
            "the evidence for the withdrawal, not something to tidy away.</p>"
            "<p class='sub'>%s</p></div>"
            % (esc(sup.get("measure") or "OR"), sup.get("point"), sup.get("ci_low"),
               sup.get("ci_high"), pr.get("k"), esc(pr.get("estimator") or "unrecorded"),
               esc(pr.get("pooled_superseded_because") or pl.get("withdrawn_reason") or "")))

    verbatim = ""
    cmp_ = pr.get("registered_primaries_compared_verbatim")
    if cmp_:
        items = "".join("<li><code>%s</code><br>%s</li>" % (esc(k), esc(v))
                        for k, v in cmp_.items() if k.startswith("NCT"))
        verbatim = ("<h2>The registered primaries, verbatim</h2>"
                    "<p>Read from ClinicalTrials.gov on %s, from "
                    "<code>%s</code>. Compared on their components, not on their names.</p>"
                    "<ul>%s</ul>" % (esc(cmp_.get("read_utc")), esc(cmp_.get("source")), items))

    notestab = pr.get("what_this_verdict_does_not_establish") or (
        "NOT that any trial here is poor, and NOT that no poolable question exists in this "
        "area. Only that this review does not publish a pooled estimate as it stands.")

    return """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="rapidmeta:page-state" content="LIVE">
<meta name="rapidmeta:pooled-estimate" content="NONE">
<meta name="description" content="{desc}">
<style>{css}</style>
</head><body>
<span class="tag">No pooled estimate</span>
<h1>{title}</h1>
<p class="sub">{headline}</p>

<div class="q"><strong>Question.</strong> {question}</div>

<h2>Why this review publishes no pooled estimate</h2>
<div class="why">{why}</div>
{withdrawn}
{verbatim}

<h2>The {k} trial(s) in this review</h2>
<div class="wrap"><table>
<thead><tr><th>Registration</th><th>Trial</th><th>Analysed / enrolled</th>
<th>Registered primary</th><th>Secondaries recorded</th></tr></thead>
<tbody>
{rows}
</tbody></table></div>

<h2>What this review does not establish</h2>
<p>{notestab}</p>

<footer>
Built 2026-08-19 by <code>scripts/build_survivor_pages_2026_08_19.py</code> from
<code>ssot/{topic}/{topic}.json</code>. Every figure on this page is read from that object;
none is typed into the page. This review is the surviving topic of a merge with
<code>{retires}</code>, and this page exists so that the merge does not retire a page-bearing
topic in favour of one with no page.
</footer>
</body></html>
""".format(css=CSS, title=esc(o.get("title") or topic),
           desc=esc((o.get("question") or "")[:150]),
           headline=esc(re.sub("<[^>]+>", "", spec["headline"])),
           question=esc(o.get("question") or "(no question is recorded on this object)"),
           why=esc(spec["why"]), withdrawn=withdrawn, verbatim=verbatim,
           k=len(trials), rows=trials_table(o), notestab=esc(notestab),
           topic=esc(topic), retires=esc(spec["retires"]))


def run(apply_it):
    built = {}
    for topic, spec in sorted(SURVIVORS.items()):
        o = load(topic)
        if R.is_retired(o):
            print("REFUSED: %s is already RETIRED; it cannot be a survivor." % topic)
            return 1
        html = page(topic, spec, o)
        built[spec["page"]] = html
        k = len((o.get("inputs") or {}).get("trials") or [])
        print("  %-40s %6d bytes  k=%d  <- retires %s"
              % (spec["page"], len(html.encode("utf-8")), k, spec["retires"]))

    # THE DEFINITION regression_check.py HOLDS, asserted here rather than discovered at push.
    bad = []
    for pg, html in built.items():
        if "No pooled estimate" not in html:
            bad.append("%s: does not say so where a reader sees it" % pg)
        if not re.search(r"NCT\d{8}", html):
            bad.append("%s: names no trial" % pg)
        for href in re.findall(r'class="go" href="([^"]+)"', html):
            if not os.path.exists(os.path.join(REPO, href)):
                bad.append("%s: links to %s which does not exist" % (pg, href))
    if bad:
        print("\nREFUSED -- these would fail the regression check:")
        for b in bad:
            print("   %s" % b)
        return 1
    print("\n  all pages satisfy the no-pool review definition")

    # THE GUARD THAT WOULD HAVE PREVENTED A DESTRUCTIVE OVERWRITE. A page this builder is about
    # to write must NOT already exist. Acting on a deferral that said "THE SURVIVOR HAS NO
    # PAGE", this script wrote a 7.6 KB stub over a 722 KB live dashboard and took the RETIREE's
    # live URL for the survivor. Both were reverted from HEAD. No amount of care in the template
    # protects against writing to the wrong filename -- only refusing to overwrite does.
    clash = [pg for pg in built if os.path.exists(os.path.join(REPO, pg))]
    if clash:
        print("\nREFUSED -- these pages already exist and would be OVERWRITTEN:")
        for c in clash:
            print("   %-44s %d bytes" % (c, os.path.getsize(os.path.join(REPO, c))))
        print("   A builder must never write over a page it did not create. Choose a name that "
              "collides with nothing, or MAP the existing page instead of rebuilding it.")
        return 1

    if not apply_it:
        print("\nDRY RUN -- nothing written. Re-run with --apply.")
        return 0

    for pg, html in sorted(built.items()):
        with io.open(os.path.join(REPO, pg), "w", encoding="utf-8", newline="") as fh:
            fh.write(html)
    pmp = os.path.join(REPO, "ssot", "PAGE_MAP.json")
    with io.open(pmp, "r", encoding="utf-8") as fh:
        pmap = json.load(fh)
    for topic, spec in SURVIVORS.items():
        pmap[spec["page"]] = "ssot/%s/%s.json" % (topic, topic)
    # A CORRECTION, NOT A BUILD. Two survivors' pages existed on disk and were simply absent
    # from PAGE_MAP, which is why the executor reported them as having no page at all.
    for topic, pg in MAP_ONLY.items():
        if not os.path.exists(os.path.join(REPO, pg)):
            print("REFUSED: %s would be mapped to %s, which is not on disk." % (topic, pg))
            return 1
        pmap[pg] = "ssot/%s/%s.json" % (topic, topic)
        print("  mapped (EXISTING page, not rebuilt)  %-38s -> %s" % (pg, topic))
    with io.open(pmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(pmap, indent=1, ensure_ascii=False, sort_keys=True))
    print("\nwrote %d page(s); PAGE_MAP updated" % len(built))
    return 0


def selftest():
    fails = []

    def ck(n, got, want):
        ok = got == want
        print("  %-64s %s  %r" % (n, "ok" if ok else "FAIL", got))
        if not ok:
            fails.append(n)

    print("1. ESCAPING AND ABSENCE:")
    ck("markup cannot be injected from a registry string",
       esc("<b>x</b>"), "&lt;b&gt;x&lt;/b&gt;")
    ck("an absent count is a dash, not a zero", num(None), "&mdash;")

    print("\n2. THE k=1 PAGE SAYS SO, rather than rendering an interval of one:")
    o = load("mavacamten-ohcm-review")
    h = page("mavacamten-ohcm-review", SURVIVORS["mavacamten-ohcm-review"], o)
    ck("one trial", len((o.get("inputs") or {}).get("trials") or []), 1)
    ck("and the page states a meta-analysis needs two",
       "at least two studies" in h, True)
    ck("...and declares it publishes nothing", 'content="NONE"' in h, True)

    print("\n3. THE WITHDRAWN ESTIMATE IS SHOWN AS WITHDRAWN, not hidden:")
    o = load("pcsk9-inhibitors-cv-review")
    h = page("pcsk9-inhibitors-cv-review", SURVIVORS["pcsk9-inhibitors-cv-review"], o)
    ck("the old value appears on the page", "0.844" in h, True)
    ck("labelled withdrawn", "withdrawn</strong>" in h, True)
    ck("and both composites are quoted verbatim", "Revascularization" in h, True)
    ck("...with the trial that does NOT count it named",
       "NCT01663402" in h, True)

    print("\n4. EVERY PAGE MEETS THE NO-POOL REVIEW DEFINITION:")
    for t, s in sorted(SURVIVORS.items()):
        hh = page(t, s, load(t))
        ck("%s says it where a reader sees it" % t, "No pooled estimate" in hh, True)
        ck("%s names a trial" % t, bool(re.search(r"NCT\d{8}", hh)), True)

    print("\n%s" % ("SELFTEST FAILED: %s" % fails if fails else "SELFTEST PASSED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(run("--apply" in sys.argv))
