"""RENDERED-REGENERATES-FROM-OBJECT -- does the number a reader sees come from the object
the same page ships?

WHY THIS EXISTS, AND WHAT IT IS NOT.
    scripts/headline_reproducible_gate.py asks a HARDER question of a store object: does the
    pooled headline follow from the per-trial rows? It needs an estimator, a subset search
    and a tolerance, and its honest verdict is NOT_REPRODUCED -- a flag for a human.

    THIS GATE ASKS AN EASIER QUESTION AND GETS A HARDER ANSWER. When a page carries BOTH a
    rendered estimate AND an embedded object that stores that same estimate under the same
    label, the two are the same claim written twice. There is no estimator, no subset, no
    tolerance beyond the rendered precision, and no oracle. Either they agree or the page
    contradicts itself.

THE CASE THAT PRODUCED IT, MEASURED 2026-09-03 FROM THE SERVED BYTES.
    HFREF_NMA_AUTO_FULL_REVIEW.html served six node-versus-placebo values in prose while
    embedding <script id="hfref-fit-data"> whose PRIMARY cell stores six different ones:

        ACEI          prose 0.8619 (0.6915 to 1.0743)   object 0.8937 (0.6252 to 1.2774)
        ACEI+MRA      prose 0.6985 (0.5060 to 0.9641)   object 0.6727 (0.4012 to 1.1279)
        ACEI+BB       prose 0.6393 (0.4831 to 0.8460)   object 0.6446 (0.4331 to 0.9593)
        ARNI+BB       prose 0.5476 (0.3623 to 0.8278)   object 0.5793 (0.3573 to 0.9391)
        ACEI+BB+MRA   prose 0.5181 (0.3594 to 0.7469)   object 0.5933 (0.3483 to 1.0109)
        +SGLT2i       prose 0.4588 (0.2956 to 0.7121)   object 0.5257 (0.2885 to 0.9580)

    TWO OF THEM CHANGE THE VERDICT. ACEI+MRA and ACEI+BB+MRA read as significant in the
    prose and do not exclude 1 on the fit the page carries. The prose was bolted to an
    out-of-repository fit and nobody could tell, because the block asserted its own
    provenance in a sentence.

THE REFUSAL THAT WAS RECORDED AND NOT ACTED ON.
    scripts/check_cross_surface_consistency.py already compares a page's card against its
    store object, and it had already looked at this page. out/card_vs_object_2026_08_28.json
    records the result: n_pages 26, agree 24, and HFREF_NMA_AUTO_FULL_REVIEW.html in TWO
    refusal lists at once --

        "no_object":        {"page": "HFREF...", "reason": "absent_from_PAGE_MAP"}
        "unparseable_card": {"page": "HFREF...", "pub": "ACEI versus Placebo ... RR 0.8619
                             (0.6915 to 1.0743)", "reason": "pub_pattern_not_matched"}

    The existing check had the wrong number in its hand and could not compare it, because
    this page keeps its model object EMBEDDED rather than in ssot/PAGE_MAP.json. It said so
    honestly and nothing consumed the saying. THIS GATE IS THE CONSUMER: it reads the
    embedded object, which is the case the store-based check names as out of reach.

WHAT IT CHECKS, EXACTLY.
    1. Every <script type="application/json"> block on the page is parsed.
    2. The object is walked for LABELLED ESTIMATE TRIPLES: a dict carrying a label-ish
       string and a point/low/high numeric triple under a recognised key set.
    3. The page's STATIC rendered text is produced -- tags stripped, entities unescaped.
    4. For each label, the rendered text is searched for that label followed by its own
       triple. Where one is found, it must equal the stored triple ROUNDED TO THE PRECISION
       THE PAGE PRINTS. 0.8937 rendered as 0.89 is agreement; rendered as 0.8619 is not.

SIX STATES, BECAUSE FOUR OF THEM ARE NOT VERDICTS -- the run_hook_chain.py convention:
    ok              at least one label was compared and every comparison agreed
    FAILED          a rendered value disagrees with the object beside it  <- the finding
    NO_OBJECT       the page embeds no application/json block
    NO_LABELLED     it embeds one, but the object stores inputs only (per-arm counts,
                    per-trial rows) and no labelled estimate. There is nothing to
                    contradict. NOT a pass.
    NOT_RENDERED    the object stores labelled estimates and the page renders none of them
                    in a form this gate can find. NOT a pass -- it is this gate's reach
                    running out, and it is reported as such.
    UNPARSEABLE     a json block that does not parse

WHAT THIS DOES NOT ESTABLISH, WRITTEN IN ADVANCE.
    - NOT that an agreeing page is CORRECT. The object can store the wrong trials, the wrong
      arms or the wrong estimand and the prose will agree with it perfectly. This gate
      polices one failure mode: prose that has come loose from its own object.
    - NOT that a page with no embedded object is clean. It is UNCHECKED, and the denominator
      below says so by name rather than by omission.
    - NOTHING about values a client-side script computes at run time. This reads the static
      bytes a reader is served, which is the surface the defect lived on.

USAGE
    python scripts/gate_rendered_regenerates_from_embedded_object.py            # whole corpus
    python scripts/gate_rendered_regenerates_from_embedded_object.py PAGE.html [...]
    python scripts/gate_rendered_regenerates_from_embedded_object.py --selftest
    python scripts/gate_rendered_regenerates_from_embedded_object.py --json OUT
Exit 1 if any page FAILED.
"""
from __future__ import annotations

import glob
import html as _html
import io
import json
import os
import re
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JSON_BLOCK = re.compile(
    r'<script(?=[^>]*\btype="application/json")([^>]*)>(.*?)</script>', re.S | re.I)

# Key sets recognised as a point estimate and its interval. Extend deliberately: a key
# added here without a fixture below widens what the gate claims to police without
# widening what it has been shown to catch.
POINT_KEYS = ("rr", "or", "hr", "point", "estimate", "value", "smd", "md", "irr",
              "lsm_ratio", "sens", "spec", "sensitivity", "specificity")
LO_KEYS = ("lo", "low", "ci_low", "ci_lo", "lower", "ci95_lo", "ci90_lo", "l95", "lcl")
HI_KEYS = ("hi", "high", "ci_high", "ci_hi", "upper", "ci95_hi", "ci90_hi", "u95", "ucl")
LABEL_KEYS = ("node", "label", "name", "treatment", "comparison", "arm", "studlab",
              "trial", "id", "cohort", "test", "model")

NUM = r"[0-9]+(?:\.[0-9]+)?"
SEP = r"(?:to|–|—|-|,|\s+)"


def render_text(body: str) -> str:
    """Static rendered text: script/style removed, tags to space, entities resolved.

    TAGS BECOME A SPACE, NOT NOTHING. A sentence a reader sees as one string is often
    several strings in the file, split by an inline <strong>. Deleting the tag glues words
    together and the match fails; replacing it with a space keeps the reader's string.
    """
    b = re.sub(r"<script.*?</script>", " ", body, flags=re.S | re.I)
    b = re.sub(r"<style.*?</style>", " ", b, flags=re.S | re.I)
    b = re.sub(r"<[^>]+>", " ", b)
    b = _html.unescape(b)
    return re.sub(r"\s+", " ", b)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def collect_labelled(obj, out, path=""):
    """Walk any JSON and collect (label, point, lo, hi) wherever a dict carries all four."""
    if isinstance(obj, dict):
        lab = None
        for k in LABEL_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                lab = v.strip()
                break
        pt = lo = hi = None
        for k in POINT_KEYS:
            if _num(obj.get(k)):
                pt = float(obj[k])
                break
        for k in LO_KEYS:
            if _num(obj.get(k)):
                lo = float(obj[k])
                break
        for k in HI_KEYS:
            if _num(obj.get(k)):
                hi = float(obj[k])
                break
        if lab and pt is not None and lo is not None and hi is not None:
            out.append({"label": lab, "point": pt, "lo": lo, "hi": hi, "path": path})
        for k, v in obj.items():
            collect_labelled(v, out, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            collect_labelled(v, out, "%s[%d]" % (path, i))


def _decimals(s: str) -> int:
    return len(s.split(".")[1]) if "." in s else 0


def _agrees(rendered: str, stored: float) -> bool:
    """Agreement at the precision the page prints. Rounding is not a defect."""
    d = _decimals(rendered)
    return abs(float(rendered) - round(stored, d)) < 0.5 * 10 ** (-d) + 1e-12


def compare_page(body: str):
    blocks = JSON_BLOCK.findall(body)
    if not blocks:
        return "NO_OBJECT", [], {}
    labelled, bad = [], 0
    for _attrs, raw in blocks:
        try:
            obj = json.loads(_html.unescape(raw))
        except Exception:
            bad += 1
            continue
        collect_labelled(obj, labelled)
    if bad and not labelled:
        return "UNPARSEABLE", ["%d embedded json block(s) do not parse" % bad], {}
    if not labelled:
        return "NO_LABELLED", ["embedded object stores no labelled point+interval triple; "
                               "there is nothing on the page to contradict"], {}

    text = render_text(body)
    notes, compared, failed = [], 0, 0
    seen = set()
    for row in labelled:
        lab = row["label"]
        if lab in seen:
            continue
        seen.add(lab)
        # The label must not be a prefix of a longer label: ACEI must not match inside
        # ACEI+MRA. Anything that could continue the token disqualifies the match.
        rx = re.compile(
            r"(?<![A-Za-z0-9+])" + re.escape(lab) + r"(?![A-Za-z0-9+])"
            r"[^0-9\n]{0,40}?(" + NUM + r")\s*\(\s*(" + NUM + r")\s*" + SEP + r"\s*("
            + NUM + r")\s*\)")
        m = rx.search(text)
        if not m:
            continue
        compared += 1
        rp, rl, rh = m.group(1), m.group(2), m.group(3)
        ok = (_agrees(rp, row["point"]) and _agrees(rl, row["lo"])
              and _agrees(rh, row["hi"]))
        if not ok:
            failed += 1
            flip = ""
            try:
                if (float(rh) < 1.0) != (row["hi"] < 1.0):
                    flip = "  <- CHANGES THE VERDICT (one side excludes 1, the other does not)"
            except ValueError:
                pass
            notes.append("  %-16s rendered %s (%s to %s)   object %.4f (%.4f to %.4f)  "
                         "at %s%s"
                         % (lab[:16], rp, rl, rh, row["point"], row["lo"], row["hi"],
                            row["path"][:48], flip))
    stats = {"labelled_in_object": len(labelled), "distinct_labels": len(seen),
             "compared": compared, "disagreeing": failed}
    if compared == 0:
        return ("NOT_RENDERED",
                ["object stores %d labelled estimate(s) and the page renders none of them "
                 "in a form this gate can find; this is the gate's reach, not a pass"
                 % len(labelled)], stats)
    if failed:
        return "FAILED", notes, stats
    return "ok", ["  %d label(s) compared, all agree" % compared], stats


# ---------------------------------------------------------------------------- selftest

_OBJ = ('<script id="t" type="application/json">'
        '{"cells":[{"tier":"PRIMARY","node_vs_placebo":['
        '{"node":"ACEI","rr":0.89369,"lo":0.62520,"hi":1.27740},'
        '{"node":"ACEI+MRA","rr":0.67270,"lo":0.40120,"hi":1.12790},'
        '{"node":"ACEI+BB+MRA","rr":0.59333,"lo":0.34827,"hi":1.01086}]}]}'
        '</script>')


def _page(prose):
    return "<html><body>" + _OBJ + "<div>" + prose + "</div></body></html>"


def selftest() -> int:
    ok = True
    cases = [
        ("THE REAL DEFECT: the vector HFREF served on 2026-09-03 against its own object",
         _page("<li><strong>ACEI</strong> &mdash; 0.8619 (0.6915 to 1.0743)</li>"
               "<li><strong>ACEI+MRA</strong> &mdash; 0.6985 (0.5060 to 0.9641)</li>"
               "<li><strong>ACEI+BB+MRA</strong> &mdash; 0.5181 (0.3594 to 0.7469)</li>"),
         "FAILED"),
        ("THE FIX: the same page rendering its object's own values",
         _page("<li><strong>ACEI</strong> &mdash; 0.8937 (0.6252 to 1.2774)</li>"
               "<li><strong>ACEI+MRA</strong> &mdash; 0.6727 (0.4012 to 1.1279)</li>"
               "<li><strong>ACEI+BB+MRA</strong> &mdash; 0.5933 (0.3483 to 1.0109)</li>"),
         "ok"),
        ("ROUNDING IS NOT A DEFECT: two decimals of the same number",
         _page("<p>ACEI &mdash; 0.89 (0.63 to 1.28)</p>"), "ok"),
        ("A PREFIX LABEL MUST NOT MATCH A LONGER ONE: only ACEI+MRA is on the page, and "
         "it is correct; ACEI must not be scored against it",
         _page("<p>ACEI+MRA &mdash; 0.6727 (0.4012 to 1.1279)</p>"), "ok"),
        ("EN-DASH AND HYPHEN INTERVALS READ THE SAME AS 'to'",
         _page("<p>ACEI &mdash; 0.8937 (0.6252&ndash;1.2774)</p>"), "ok"),
        ("A PAGE WITH NO OBJECT IS UNCHECKED, NOT CLEAN",
         "<html><body><p>ACEI 0.8619 (0.6915 to 1.0743)</p></body></html>", "NO_OBJECT"),
        ("AN OBJECT OF INPUTS ONLY HAS NOTHING TO CONTRADICT",
         '<html><body><script type="application/json">'
         '[{"studlab":"X","arms":[{"dose":0,"events":5,"n":100}]}]</script>'
         "<p>0.50 (0.30 to 0.80)</p></body></html>", "NO_LABELLED"),
        ("AN OBJECT WHOSE ESTIMATES THE PAGE NEVER PRINTS IS OUT OF REACH, NOT PASSED",
         _page("<p>Nothing quantitative here.</p>"), "NOT_RENDERED"),
        ("A VALUE INSIDE A SCRIPT IS NOT RENDERED TEXT and must not be compared",
         _page("<p>See below.</p>")
         .replace("</body>", "<script>var x='ACEI 0.8619 (0.6915 to 1.0743)';</script>"
                             "</body>"), "NOT_RENDERED"),
    ]
    for label, page, want in cases:
        got, notes, _ = compare_page(page)
        good = got == want
        ok &= good
        print("  %-72s -> %-13s (want %-13s) %s"
              % (label[:72], got, want, "correct" if good else "WRONG"))
        if not good:
            for n in notes:
                print("        " + n.strip()[:150])
    print()
    print("  WHAT A FAILURE LOOKS LIKE: case 1 reporting ok. Those six values were served")
    print("  for six days beside an object that contradicted two of their verdicts.")
    print("  THE OPPOSITE FAILURE MATTERS AS MUCH: case 3 or 4 reporting FAILED would")
    print("  manufacture a finding out of rounding, or out of one label being another's")
    print("  prefix -- and a gate that cries wolf on rounding gets switched off.")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()
    out_json = None
    if "--json" in argv:
        i = argv.index("--json")
        out_json = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    paths = [a for a in argv if not a.startswith("--")]
    scoped = bool(paths)
    if not paths:
        paths = sorted(glob.glob(os.path.join(REPO, "*.html")))

    tally, rows = {}, []
    for p in paths:
        try:
            body = io.open(p, encoding="utf-8", errors="replace", newline="").read()
        except Exception as ex:
            tally["UNREADABLE"] = tally.get("UNREADABLE", 0) + 1
            rows.append({"page": os.path.basename(p), "state": "UNREADABLE",
                         "notes": [type(ex).__name__]})
            continue
        state, notes, stats = compare_page(body)
        tally[state] = tally.get(state, 0) + 1
        if state != "NO_OBJECT" or scoped:
            rows.append({"page": os.path.basename(p), "state": state, "notes": notes,
                         "stats": stats})

    print("RENDERED-REGENERATES-FROM-OBJECT")
    print("  pages read: %d (the denominator is every *.html at the repository root, "
          "named by glob, not a curated list)" % len(paths))
    for k in ("ok", "FAILED", "NOT_RENDERED", "NO_LABELLED", "UNPARSEABLE", "NO_OBJECT",
              "UNREADABLE"):
        if tally.get(k):
            print("    %-14s %d" % (k, tally[k]))
    print("  CHECKED means an object was present AND stored a labelled estimate AND the "
          "page printed it: %d of %d pages." % (tally.get("ok", 0) + tally.get("FAILED", 0),
                                                len(paths)))
    print("  NO_OBJECT, NO_LABELLED and NOT_RENDERED are NOT passes. They are this gate's")
    print("  reach running out, and they are counted so the reach cannot read as coverage.")

    for r in rows:
        if r["state"] in ("FAILED", "UNPARSEABLE"):
            print("\n  %s  %s" % (r["state"], r["page"]))
            for n in r["notes"]:
                print("  " + n)
    for r in rows:
        if r["state"] in ("ok", "NOT_RENDERED", "NO_LABELLED"):
            print("  %-13s %-52s %s"
                  % (r["state"], r["page"][:52],
                     (r["notes"][0].strip()[:70] if r["notes"] else "")))

    if out_json:
        io.open(out_json, "w", encoding="utf-8", newline="\n").write(json.dumps(
            {"pages_read": len(paths), "tally": tally, "rows": rows}, indent=1))
        print("\n  wrote %s" % out_json)
    return 1 if tally.get("FAILED") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
