"""HFrEF NMA: relabel the estimate, strip the outputs built on top of it.

THE CENTRAL CHARGE WAS REFUTED AND THE REPAIR CHANGED SHAPE. The reviewer said the headline
number "averages fifteen structurally different comparisons". It does not. `0.8619` is the
ACEI-versus-Placebo node, established four independent ways -- slot position across 117
occurrences, the label array ordering the nodes, `reference.group = "Placebo"` in the fit
script, and a reconciliation file listing the same six node values in the same order three
days BEFORE the R fit it corroborates. I relayed the charge without checking it; that was
my error, and this file records it so the correction outlives the session.

  WHAT IS ACTUALLY WRONG: a SPECIFIC estimate presented as a POOLED one. The page frames a
  single node as an omnibus result and then derives an NNT, a ranking and a patient-facing
  sentence from that misreading. The repository contains no rationale for the omnibus
  framing and no derivation of the NNT.

  So the number STAYS and gets its true label. Everything built on the misreading goes.

WHY DISABLING IS NOT ENOUGH FOR THE PATIENT SENTENCE. A patient-facing "3 out of 100
benefit" derived from a MISLABELLED node is worse than one derived from a meaningless
average: it is confidently wrong about a specific drug. So these are removed from the served
BYTES, not hidden with a CSS class that a reader can defeat.

WHAT IS KEPT, DELIBERATELY. The arm-level ledger, the direct-versus-indirect tagging and the
page's own "VERDICT: UNCERTAIN -- NOT AN INTEGRITY PASS" banner all stay. They are the
transparent data, and they are the part that was honest all along.

EVERY REMOVAL IS PLANTED BOTH WAYS. Each target is asserted PRESENT before the edit and
ABSENT after, and the keeps are asserted present after. A removal that silently matched
nothing would report success while leaving a patient-facing claim on a live page, which is
the one failure mode that matters here.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(REPO, "HFREF_NMA_AUTO_FULL_REVIEW.html")
OUT = os.path.join(REPO, "outputs", "hfref_relabel_2026_08_28.json")

# Panels whose entire contents are generated outputs built on the omnibus misreading.
KILL_PANELS = {
    "tab-report": ("Scientific Output", "carries the integrity score, the NNT pictogram and "
                                        "the generated report built on the omnibus framing"),
    "tab-paper": ("Paper Studio", "generates a manuscript from the same misread estimate"),
}

NOTICE = (
    '<div class="glass p-8 rounded-[32px] border" '
    'style="border-color:#b45309;background:rgba(180,83,9,.08)">'
    '<h3 style="font-size:1.05rem;font-weight:800;margin:0 0 .6rem">'
    'This section has been withdrawn, %(date)s</h3>'
    '<p style="margin:0 0 .7rem;line-height:1.6"><strong>%(what)s</strong> generated results '
    'from the network\'s headline estimate read as an omnibus, pooled result. It is not one. '
    'The estimate is a single node &mdash; <strong>ACEI versus Placebo, all-cause '
    'mortality</strong> &mdash; and everything derived from the pooled reading (a '
    'number-needed-to-treat, a treatment ranking, an integrity score and a plain-language '
    'patient summary) has been removed rather than corrected, because nothing in this '
    'repository derives them.</p>'
    '<p style="margin:0;line-height:1.6">The underlying data stays on this page: the '
    'arm-level ledger, the direct-versus-indirect tagging, and the page\'s own verdict '
    'banner, which already reads <em>UNCERTAIN &mdash; not an integrity pass</em>.</p>'
    '</div>')

RELABEL = (
    '<div id="hfref-node-relabel" class="glass p-8 rounded-[32px] border" '
    'style="border-color:#1d4ed8;background:rgba(29,78,216,.08);margin:0 0 1.5rem">'
    '<h3 style="font-size:1.05rem;font-weight:800;margin:0 0 .6rem">'
    'What the headline number is</h3>'
    '<p style="margin:0 0 .7rem;line-height:1.6">The headline estimate is '
    '<strong>ACEI versus Placebo for all-cause mortality &mdash; RR 0.8619 '
    '(0.6915 to 1.0743)</strong>. It is <strong>one node in a network</strong>, not a '
    'pooled average across the network&rsquo;s comparisons, and its interval crosses 1: '
    'on this network ACEI versus placebo is <strong>null</strong>. This page previously '
    'presented the number as an omnibus result and derived a number-needed-to-treat, a '
    'treatment ranking, an integrity score and a plain-language patient summary from that '
    'reading. Those have been removed.</p>'
    '<p style="margin:0 0 .7rem;line-height:1.6">The six headline nodes, in the order the '
    'fit stores them, so a reader can see this is one of six:</p>'
    '<ul style="margin:0 0 .7rem 1.1rem;line-height:1.7">'
    '<li><strong>ACEI</strong> &mdash; 0.8619 (0.6915 to 1.0743) &nbsp;&larr; the headline '
    'number</li>'
    '<li><strong>ACEI+MRA</strong> &mdash; 0.6985 (0.5060 to 0.9641)</li>'
    '<li><strong>ACEI+BB</strong> &mdash; 0.6393 (0.4831 to 0.8460)</li>'
    '<li><strong>ARNI+BB</strong> &mdash; 0.5476 (0.3623 to 0.8278)</li>'
    '<li><strong>ACEI+BB+MRA</strong> &mdash; 0.5181 (0.3594 to 0.7469)</li>'
    '<li><strong>+SGLT2i</strong> &mdash; 0.4588 (0.2956 to 0.7121)</li>'
    '</ul>'
    '<p style="margin:0;line-height:1.6"><small>All six read from the stored node vector '
    'and mapped to the fit&rsquo;s own <code>head6</code> label array, not restated from '
    'memory: the vector has ten slots matching ten <code>contenders</code>, and slot 0 is '
    'ACEI. An independent refit '
    '(<code>HFREF-FULL-NETWORK-RECONCILIATION-2026-07-19</code>) reports different values '
    'under a different estimator &mdash; ACEI+BB 0.628 (0.468&ndash;0.843), ACEI+BB+MRA '
    '0.541 (0.378&ndash;0.777) &mdash; and records that <strong>ACEI versus placebo '
    'remains robustly null</strong>, agreeing with the node above. That reconciliation '
    'carries its own status: <em>analysis only, prototype, not for public deploy</em>.'
    '</small></p></div>')


def read_page():
    return io.open(PAGE, encoding="utf-8", errors="replace", newline="").read()


def element_span(body, pid):
    """(start, inner_start, inner_end, end) for the element carrying id=pid, by nesting.

    THE TAG IS READ FROM THE PAGE, NOT ASSUMED. The first version hard-coded <div> and these
    panels are <section>, so the nesting walk ran off the end of the file and refused. The
    refusal was correct; the assumption was not.
    """
    m = re.search(r'<(\w+)[^>]*\bid="' + re.escape(pid) + r'"[^>]*>', body)
    if not m:
        return None
    tag_name = m.group(1).lower()
    inner_start = m.end()
    depth, i = 1, inner_start
    tag = re.compile(r"</?" + tag_name + r"\b", re.I)
    while depth:
        n = tag.search(body, i)
        if not n:
            return None
        depth += 1 if not n.group(0).startswith("</") else -1
        i = n.end()
    close = body.rfind("</" + tag_name, 0, i + 1)
    return (m.start(), inner_start, close, i)


def main():
    apply_ = "--apply" in sys.argv
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        raw.write(s + chr(10))
        raw.flush()

    date = "2026-08-28"
    body = read_page()
    before_len = len(body)
    say("page bytes before : %d" % before_len)

    # ---- assert every target is PRESENT before touching anything -------------------
    targets = {
        "Scientific Output tab button": r'switchTab\(.report.\)',
        "Paper Studio tab button": r'switchTab\(.paper.\)',
        # THE CONTROL, NOT THE IDENTIFIER. `togglePatientMode` also names the minified method
        # definition, and "Clinical Utility (NNT Curve)" also appears twice in the Arabic
        # i18n table. Asserting on the bare identifier failed after a correct removal and
        # would have been "fixed" by loosening the check -- which is how a real miss gets
        # waved through. These target the button and the chart container instead.
        "Patient Mode toggle button": r'onclick="RapidMeta\.togglePatientMode\(\)"',
        "patient summary block": r'class="patient-summary',
        "NNT clinical-utility chart": r'id="plot-nnt"',
        "integrity score element": r'id="guardian-integrity-score"',
    }
    missing = [k for k, rx in targets.items() if not re.search(rx, body)]
    say("")
    say("PLANTED BOTH WAYS -- targets asserted PRESENT before the edit")
    for k, rx in targets.items():
        say("   %-32s %s" % (k, "present" if re.search(rx, body) else "ABSENT"))
    if missing:
        say("REFUSED: %d target(s) not found, so a removal would silently do nothing: %s"
            % (len(missing), ", ".join(missing)))
        return 2

    keeps = {
        "verdict banner (kept)": r'NOT AN INTEGRITY PASS',
        "arm-level ledger (kept)": r'nma_config',
    }
    for k, rx in keeps.items():
        if not re.search(rx, body):
            say("REFUSED: a KEEP target is already absent: %s" % k)
            return 2

    # ---- 1. replace the two generated-output panels ---------------------------------
    for pid, (what, why) in KILL_PANELS.items():
        span = element_span(body, pid)
        if not span:
            say("REFUSED: could not bound panel %s by div nesting" % pid)
            return 2
        s0, i0, i1, s1 = span
        removed = i1 - i0
        body = body[:i0] + (NOTICE % {"date": date, "what": what}) + body[i1:]
        say("   panel %-12s inner content replaced: %d bytes  (%s)" % (pid, removed, why))

    # ---- 2. remove the two tab buttons ----------------------------------------------
    for which in ("report", "paper"):
        body, n = re.subn(r'<button[^>]*switchTab\(.' + which + r'.\)[^>]*>.*?</button>',
                          "", body, flags=re.S | re.I)
        say("   tab button %-8s removed: %d" % (which, n))

    # ---- 3. Patient Mode: the toggle and the summary block --------------------------
    body, n = re.subn(r'<button[^>]*togglePatientMode\(\)[^>]*>.*?</button>', "", body,
                      flags=re.S | re.I)
    say("   patient-mode toggle removed: %d" % n)
    span = None
    m = re.search(r'<div class="patient-summary[^"]*"[^>]*>', body)
    if m:
        depth, i = 1, m.end()
        tag = re.compile(r"</?div\b", re.I)
        while depth:
            nn = tag.search(body, i)
            if not nn:
                break
            depth += 1 if nn.group(0).lower() == "<div" else -1
            i = nn.end()
        span = (m.start(), i)
    if not span:
        say("REFUSED: could not bound the patient-summary block")
        return 2
    body = body[:span[0]] + body[span[1]:]
    say("   patient-summary block removed: %d bytes" % (span[1] - span[0]))

    # ---- 4. the NNT clinical-utility chart CARD, whole ------------------------------
    # Renaming the heading would leave the plot container and its renderer in place. The
    # card is self-contained and anchored on plot-nnt, so it comes out entire.
    card = re.compile(r'<div class="col-span-1 md:col-span-2">'
                      r'(?:(?!</div>\s*<div class="col-span-1).)*?id="plot-nnt".*?'
                      r'<div id="desc-nnt"[^>]*></div></div>', re.S)
    body, n = card.subn(
        '<div class="col-span-1 md:col-span-2"><div class="chart-header mb-2 px-2">'
        '<h4 class="text-[10px] opacity-70 font-bold uppercase tracking-widest">'
        '8. Clinical utility &mdash; withdrawn ' + date + '</h4></div>'
        '<div class="chart-desc" style="padding:.6rem .8rem;line-height:1.55">'
        'A number-needed-to-treat curve was computed here from the headline estimate read '
        'as a pooled result. That estimate is a single node (ACEI versus Placebo), no '
        'derivation of the NNT exists in this repository, and the curve has been removed '
        'rather than relabelled.</div></div>', body)
    say("   NNT chart card removed whole: %d" % n)

    # ---- 5. the relabel, above the analysis panel -----------------------------------
    span = element_span(body, "tab-analysis")
    if not span:
        say("REFUSED: could not bound tab-analysis for the relabel")
        return 2
    body = body[:span[1]] + RELABEL + body[span[1]:]
    say("   relabel inserted at the top of the analysis panel")

    # ---- assert ABSENT after ---------------------------------------------------------
    say("")
    say("AFTER -- the same targets asserted ABSENT, and the keeps still present")
    still = {}
    for k, rx in targets.items():
        hit = bool(re.search(rx, body))
        still[k] = hit
        say("   %-32s %s" % (k, "STILL PRESENT" if hit else "gone"))
    kept_ok = {}
    for k, rx in keeps.items():
        hit = bool(re.search(rx, body))
        kept_ok[k] = hit
        say("   %-32s %s" % (k, "kept" if hit else "LOST"))

    bad = [k for k, v in still.items() if v] + [k for k, v in kept_ok.items() if not v]
    say("")
    if bad:
        say("REFUSED to write: %d assertion(s) failed: %s" % (len(bad), ", ".join(bad)))
        return 2

    ob = len(re.findall(r"<div\b", body))
    cb = len(re.findall(r"</div>", body))
    say("div balance: %d open, %d close, delta %d" % (ob, cb, ob - cb))
    say("bytes after : %d  (%+d)" % (len(body), len(body) - before_len))

    if not apply_:
        say("")
        say("(dry run -- nothing written; pass --apply)")
        return 0

    io.open(PAGE, "w", encoding="utf-8", newline="").write(body)
    json.dump({"page": os.path.basename(PAGE), "date": date,
               "bytes_before": before_len, "bytes_after": len(body),
               "removed": sorted(targets), "kept": sorted(keeps),
               "correction": "0.8619 is the ACEI-versus-Placebo node, NOT an omnibus "
                             "average. The reviewer's central charge was refuted; the "
                             "defect is a specific estimate presented as a pooled one.",
               "div_delta": ob - cb},
              io.open(OUT, "w", encoding="utf-8"), indent=1)
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
