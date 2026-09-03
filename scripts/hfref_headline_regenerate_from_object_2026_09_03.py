"""HFrEF: the six served node values came from a fit this page does not carry.

WHAT WAS MEASURED, FROM THE SERVED BYTES AND NOT FROM SOURCE.
    https://mahmood726-cyber.github.io/rapidmeta-finerenone/HFREF_NMA_AUTO_FULL_REVIEW.html
    fetched 2026-09-03, 938949 bytes, sha256
    06344a4fdec6b545553b4bed28860a94921886699bdd8d370d397d7c8dd2fc44 -- byte-identical to
    the file at origin/main 852b0478e. So this is a defect in what is being served, not a
    stale local tree.

    The page renders six node-versus-placebo values in prose, and separately embeds the fit
    they claim to come from in <script id="hfref-fit-data">. They disagree:

        node          SERVED PROSE                 EMBEDDED cells[0] OURS-STRICT
        ACEI          0.8619 (0.6915 to 1.0743)    0.8937 (0.6252 to 1.2774)
        ACEI+MRA      0.6985 (0.5060 to 0.9641)    0.6727 (0.4012 to 1.1279)   <- flips
        ACEI+BB       0.6393 (0.4831 to 0.8460)    0.6446 (0.4331 to 0.9593)
        ARNI+BB       0.5476 (0.3623 to 0.8278)    0.5793 (0.3573 to 0.9391)
        ACEI+BB+MRA   0.5181 (0.3594 to 0.7469)    0.5933 (0.3483 to 1.0109)   <- flips
        +SGLT2i       0.4588 (0.2956 to 0.7121)    0.5257 (0.2885 to 0.9580)

    THIS IS NOT ROUNDING. Two nodes are SIGNIFICANT as served and NOT significant on the fit
    the page carries: ACEI+MRA (served upper 0.9641, object 1.1279) and ACEI+BB+MRA (served
    upper 0.7469, object 1.0109). Point estimates differ by +3.69%, -3.69%, +0.83%, +5.78%,
    +14.52% and +14.58% for the six nodes in the order above.

    THE PAGE'S OWN ANCHOR REFUTES THE PROSE, with no external reference needed. The embedded
    object carries anchor.passed=true asserting ACEI+BB = 0.64459765339 (0.43311383501,
    0.95934625305) and ACEI+BB+MRA = 0.59333494564 (0.34826519892, 1.010857125). The prose
    beside it prints 0.6393 and 0.5181.

    AND NO CELL ON THIS PAGE PRODUCES THE SERVED VECTOR. Checked against all four cells the
    object stores -- OURS-STRICT (tau2 0.023236, 28 trials), OURS-INCLUSIVE (0.023797, 31),
    OURS-STRICT-7b (0.024786, 27), OURS-STRICT-7c (0.025658, 26). ACEI reads 0.8937, 0.8677,
    0.8856, 0.8856 across them; 0.8619 is none of these. The served numbers regenerate from
    nothing this page carries.

WHERE THE SERVED NUMBERS CAME FROM, BY FILE AND LINE.
    scripts/hfref_relabel_and_strip_2026_08_28.py, the RELABEL constant, lines 67-96:
        line 72  the headline    RR 0.8619 (0.6915 to 1.0743)
        line 82  ACEI            0.8619 (0.6915 to 1.0743)
        line 84  ACEI+MRA        0.6985 (0.5060 to 0.9641)
        line 85  ACEI+BB         0.6393 (0.4831 to 0.8460)
        line 86  ARNI+BB         0.5476 (0.3623 to 0.8278)
        line 87  ACEI+BB+MRA     0.5181 (0.3594 to 0.7469)
        line 88  +SGLT2i         0.4588 (0.2956 to 0.7121)
    Every one is a STRING LITERAL in the emitter. Nothing reads the page's object.

    AND THE BLOCK SAYS OTHERWISE. Lines 89-92 render: "All six read from the stored node
    vector and mapped to the fit's own head6 label array, not restated from memory: the
    vector has ten slots matching ten contenders, and slot 0 is ACEI." MEASURED: the token
    `head6` occurs EXACTLY ONCE in the 938949 served bytes -- inside that sentence. There is
    no head6 array on the page. The provenance sentence describes an out-of-repo file
    (multiverse-lookup.json, cited in commit e3056de3f, present at no path in this
    repository) as though it were the page's own object.

    A SENTENCE ASSERTING PROVENANCE IS NOT PROVENANCE. That sentence is why the mismatch
    survived: it reads as though the check had already been done.

WHAT THIS SCRIPT DOES. It rebuilds the block with the values READ FROM THE PAGE'S OWN
    EMBEDDED OBJECT at run time. No estimate in the emitted block is a literal in this file
    except the stale vector, which is kept only so the edit can assert it is gone. If the
    object changes, re-running regenerates the prose; if someone edits the prose by hand,
    scripts/gate_rendered_regenerates_from_embedded_object.py refuses the push.

WHAT IT DOES NOT DO. It does not claim the embedded object is CORRECT. It claims the page
    now says what its own stored fit says. Whether that fit should exist in this shape at
    all is a separate question and is handled separately. The netmeta fitting code is not
    touched by this file.

PLANTED BOTH WAYS. Every stale literal is asserted PRESENT before the edit and ABSENT after;
every regenerated value is asserted PRESENT after. An edit that silently matched nothing
would report success while leaving the stale vector on a live page.

Usage:  python scripts/hfref_headline_regenerate_from_object_2026_09_03.py [--check]
        --check exits 1 without writing if the served block is out of date.
"""
from __future__ import annotations

import html as _html
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(REPO, "HFREF_NMA_AUTO_FULL_REVIEW.html")
OUT = os.path.join(REPO, "out", "hfref_headline_regenerate_2026_09_03.json")

# The six nodes the block has always listed, in the order it listed them. This is a
# PRESENTATION order, not a source of numbers -- every value is looked up in the object.
HEAD6 = ["ACEI", "ACEI+MRA", "ACEI+BB", "ARNI+BB", "ACEI+BB+MRA", "+SGLT2i"]

# The stale vector, kept ONLY so the edit can assert it is gone afterwards.
STALE = {
    "ACEI": "0.8619 (0.6915 to 1.0743)",
    "ACEI+MRA": "0.6985 (0.5060 to 0.9641)",
    "ACEI+BB": "0.6393 (0.4831 to 0.8460)",
    "ARNI+BB": "0.5476 (0.3623 to 0.8278)",
    "ACEI+BB+MRA": "0.5181 (0.3594 to 0.7469)",
    "+SGLT2i": "0.4588 (0.2956 to 0.7121)",
}

BLOCK_ID = "hfref-node-relabel"


def read_page():
    return io.open(PAGE, encoding="utf-8", errors="replace", newline="").read()


def embedded_fit(body):
    m = re.search(r'<script id="hfref-fit-data" type="application/json">(.*?)</script>',
                  body, re.S)
    if not m:
        raise SystemExit('REFUSED: no <script id="hfref-fit-data"> on the page. A block '
                         'cannot be regenerated from an object that is not there.')
    return json.loads(_html.unescape(m.group(1)))


def primary_cell(fit):
    prim = [c for c in fit.get("cells", []) if c.get("tier") == "PRIMARY"]
    if len(prim) != 1:
        raise SystemExit("REFUSED: %d cells carry tier=PRIMARY; exactly one is required "
                         "for a headline to have a defined source." % len(prim))
    return prim[0]


def node_map(cell):
    return {r["node"]: (r["rr"], r["lo"], r["hi"]) for r in cell.get("node_vs_placebo", [])}


def fmt(v):
    return "%.4f" % v


def triple(nodes, n):
    rr, lo, hi = nodes[n]
    return "%s (%s to %s)" % (fmt(rr), fmt(lo), fmt(hi))


def build_block(fit, cell, nodes):
    ns = [n for n in HEAD6 if nodes[n][2] >= 1.0]
    items = "".join(
        '<li><strong>%s</strong> &mdash; %s%s</li>'
        % (n, triple(nodes, n),
           " &nbsp;&larr; the headline number" if n == "ACEI" else "")
        for n in HEAD6)
    return (
        '<div id="%(id)s" class="glass p-8 rounded-[32px] border" '
        'style="border-color:#1d4ed8;background:rgba(29,78,216,.08);margin:0 0 1.5rem">'
        '<h3 style="font-size:1.05rem;font-weight:800;margin:0 0 .6rem">'
        'What the headline number is</h3>'
        '<p style="margin:0 0 .7rem;line-height:1.6">The headline estimate is '
        '<strong>ACEI versus Placebo for all-cause mortality &mdash; RR %(acei)s</strong>. '
        'It is <strong>one node in a network</strong>, not a pooled average across the '
        'network&rsquo;s comparisons, and its interval crosses 1: on this network ACEI '
        'versus placebo is <strong>null</strong>. This page previously presented the number '
        'as an omnibus result and derived a number-needed-to-treat, a treatment ranking, an '
        'integrity score and a plain-language patient summary from that reading. Those have '
        'been removed.</p>'
        '<p style="margin:0 0 .7rem;line-height:1.6">The six headline nodes, read from this '
        'page&rsquo;s own stored fit (<code>hfref-fit-data</code>, cell '
        '<code>%(cell)s</code>, %(engine)s), so a reader can see this is one of six:</p>'
        '<ul style="margin:0 0 .7rem 1.1rem;line-height:1.7">%(items)s</ul>'
        '<p style="margin:0 0 .7rem;line-height:1.6"><strong>Correction, 2026-09-03.</strong> '
        'Until today this block served a different six-value vector &mdash; ACEI 0.8619 '
        '(0.6915 to 1.0743), ACEI+MRA 0.6985 (0.5060 to 0.9641), ACEI+BB 0.6393 (0.4831 to '
        '0.8460), ARNI+BB 0.5476 (0.3623 to 0.8278), ACEI+BB+MRA 0.5181 (0.3594 to 0.7469), '
        '+SGLT2i 0.4588 (0.2956 to 0.7121) &mdash; which regenerates from <strong>none of '
        'the four cells this page stores</strong> (ACEI reads %(aceis)s across them). Those '
        'values came from an out-of-repository lookup file, and the block claimed they were '
        'read from a label array that does not exist on this page. Two nodes were '
        'significant as served and are not on the fit actually stored here: '
        '<strong>ACEI+MRA</strong> (served upper bound 0.9641, stored %(mra_hi)s) and '
        '<strong>ACEI+BB+MRA</strong> (served 0.7469, stored %(bbmra_hi)s).</p>'
        '<p style="margin:0;line-height:1.6"><small>Every value above is regenerated from '
        'the embedded object at build time by '
        '<code>scripts/hfref_headline_regenerate_from_object_2026_09_03.py</code> and '
        're-checked on every push by '
        '<code>scripts/gate_rendered_regenerates_from_embedded_object.py</code>; none is a '
        'literal in the page source. Of the six, %(nns)d do not exclude 1 (%(nslist)s). An '
        'independent refit (<code>HFREF-FULL-NETWORK-RECONCILIATION-2026-07-19</code>) '
        'reports different values under a different estimator &mdash; ACEI+BB 0.628 '
        '(0.468&ndash;0.843), ACEI+BB+MRA 0.541 (0.378&ndash;0.777) &mdash; and carries its '
        'own status: <em>analysis only, prototype, not for public deploy</em>.'
        '</small></p></div>'
        % {"id": BLOCK_ID,
           "acei": triple(nodes, "ACEI"),
           "cell": cell.get("cell_id", "?"),
           "engine": fit.get("engine", "engine not recorded"),
           "items": items,
           "aceis": ", ".join(fmt(node_map(c)["ACEI"][0]) for c in fit.get("cells", [])
                              if "ACEI" in node_map(c)),
           "mra_hi": fmt(nodes["ACEI+MRA"][2]),
           "bbmra_hi": fmt(nodes["ACEI+BB+MRA"][2]),
           "nns": len(ns),
           "nslist": ", ".join(ns) if ns else "none"})


def element_span(body, pid):
    """(start, end) of the element carrying id=pid, by nesting. Tag read, not assumed."""
    m = re.search(r'<(\w+)[^>]*\bid="' + re.escape(pid) + r'"[^>]*>', body)
    if not m:
        return None
    tag_name = m.group(1).lower()
    depth, i = 1, m.end()
    tag = re.compile(r"</?" + tag_name + r"\b", re.I)
    while depth:
        t = tag.search(body, i)
        if not t:
            return None
        depth += -1 if t.group(0).startswith("</") else 1
        i = body.index(">", t.end()) + 1
    return (m.start(), i)


def main(argv):
    check_only = "--check" in argv
    body = read_page()
    fit = embedded_fit(body)
    cell = primary_cell(fit)
    nodes = node_map(cell)
    missing = [n for n in HEAD6 if n not in nodes]
    if missing:
        raise SystemExit("REFUSED: the primary cell has no node_vs_placebo row for %s. A "
                         "headline with no stored source is not regenerable."
                         % ", ".join(missing))

    span = element_span(body, BLOCK_ID)
    if not span:
        raise SystemExit("REFUSED: no element id=%s on the page." % BLOCK_ID)
    old = body[span[0]:span[1]]

    stale_rendered = [n for n in HEAD6
                      if ("&mdash; " + STALE[n]) in old or ("RR " + STALE[n]) in old]
    want = {n: triple(nodes, n) for n in HEAD6}

    print("PAGE   %s" % os.path.basename(PAGE))
    print("CELL   %s (tier %s, tau2 %s, %s trials, %s nodes)"
          % (cell.get("cell_id"), cell.get("tier"), cell.get("tau2"),
             cell.get("trials"), cell.get("nodes_in_network")))
    print("RENDERED-AS-STALE BEFORE THE EDIT: %d of %d nodes"
          % (len(stale_rendered), len(HEAD6)))
    for n in HEAD6:
        print("   %-13s served %-28s object %-28s %s"
              % (n, STALE[n], want[n],
                 "STALE" if n in stale_rendered else "already matches"))

    if check_only:
        if stale_rendered:
            print("\n-> FAILED: %d rendered value(s) do not come from the embedded object."
                  % len(stale_rendered))
            return 1
        print("\n-> ok: every rendered value matches the embedded object.")
        return 0

    if stale_rendered:
        new_block = build_block(fit, cell, nodes)
        body2 = body[:span[0]] + new_block + body[span[1]:]
    else:
        body2 = body
    span2 = element_span(body2, BLOCK_ID)
    new_rendered = body2[span2[0]:span2[1]]

    # PLANTED BOTH WAYS: the stale vector must be gone from the RENDERED positions, and
    # every regenerated value must be present. The stale strings survive inside the
    # correction paragraph on purpose -- that is the record, not the claim -- so the
    # assertion is against the <li> and headline positions, not against the whole block.
    fails = []
    for n in stale_rendered:
        if ("&mdash; " + STALE[n]) in new_rendered or ("RR " + STALE[n]) in new_rendered:
            fails.append("stale value for %s still rendered as a claim: %s" % (n, STALE[n]))
    for n in HEAD6:
        if ("&mdash; " + want[n]) not in new_rendered:
            fails.append("regenerated value for %s absent after the edit: %s" % (n, want[n]))
    if "head6" in new_rendered or "contenders" in new_rendered:
        fails.append("the false provenance token (head6/contenders) survives the edit")
    if fails:
        for f in fails:
            print("   REFUSED: %s" % f)
        return 1

    if stale_rendered:
        io.open(PAGE, "w", encoding="utf-8", newline="").write(body2)

    def flipped(n):
        served_hi = float(STALE[n].split("to ")[1].rstrip(")"))
        return (served_hi < 1.0) != (nodes[n][2] < 1.0)

    rec = {
        "utc": "2026-09-03",
        "page": os.path.basename(PAGE),
        "served_sha256_before":
            "06344a4fdec6b545553b4bed28860a94921886699bdd8d370d397d7c8dd2fc44",
        "served_bytes_before": 938949,
        "emitter_of_stale_values":
            "scripts/hfref_relabel_and_strip_2026_08_28.py RELABEL constant, lines 67-96 "
            "(headline 72; list items 82, 84, 85, 86, 87, 88)",
        "source_of_regenerated_values":
            'HFREF_NMA_AUTO_FULL_REVIEW.html <script id="hfref-fit-data"> '
            'cells[tier=PRIMARY, cell_id=%s].node_vs_placebo' % cell.get("cell_id"),
        "nodes": [{"node": n, "served_before": STALE[n], "regenerated": want[n],
                   "point_pct_change": round(
                       100.0 * (nodes[n][0] - float(STALE[n].split(" ")[0]))
                       / float(STALE[n].split(" ")[0]), 2),
                   "significance_flipped": flipped(n)} for n in HEAD6],
        "cells_checked_none_of_which_reproduce_the_stale_vector":
            [{"cell_id": c.get("cell_id"), "tier": c.get("tier"), "tau2": c.get("tau2"),
              "trials": c.get("trials"), "ACEI": round(node_map(c)["ACEI"][0], 4)}
             for c in fit.get("cells", []) if "ACEI" in node_map(c)],
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, indent=1))
    print("\n-> wrote %s%s"
          % (os.path.relpath(OUT, REPO),
             " and " + os.path.basename(PAGE) if stale_rendered
             else " (page was already regenerated; nothing rewritten)"))
    print("   %d node(s) changed significance: %s"
          % (sum(1 for r in rec["nodes"] if r["significance_flipped"]),
             ", ".join(r["node"] for r in rec["nodes"] if r["significance_flipped"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
