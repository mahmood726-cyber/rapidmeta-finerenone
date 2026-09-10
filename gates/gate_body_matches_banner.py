# -*- coding: utf-8 -*-
r"""GATE: a page's correction/supersession BANNER and its own reader-facing BODY must not
declare two different CURRENT pooled results.

THE DEFECT, NARROW AND EXACT. A page carries a correction banner that states the current pool
(k and/or effect), while the page's own summary/headline/result prose still presents a
DIFFERENT pooled value as current. Both numbers render; a reader takes whichever they read
first. This is not "a stale number exists somewhere" -- the withdrawn/superseded/benchmark
value is allowed to be shown when it is DISOWNED in words. It is the case where the old value
is still framed as the live pooled result while the banner says otherwise.

WHY IT NEEDS ITS OWN GATE. Every single-file consistency check here reads the object or one
surface. This defect lives in the RENDERED page, between two regions of the same file, and
each region is internally consistent. gate19 compares three SERVED surfaces to each other;
this compares the banner against the body WITHIN one served page.

THE CONTROLS ARE SYNTHETIC AND PERMANENT, ON PURPOSE. The obvious control -- "must flag
SGLT2_HF_REVIEW" -- retires itself the day that page is regenerated from the corrected object
(the next such commit in this project). A control anchored to a live defect fails after the
fix and reads as a regression, or passes for the wrong reason. So discrimination is proven by
two IN-MEMORY pages every run: one with a banner/body split that MUST fire, one with a banner
and a consistent body that MUST NOT. The gate is VACUOUS unless both are decided correctly and
BROKEN if the positive does not fire (the detector has gone inert).

WITHDRAWN NOTICES ARE EXEMPT, AND THE EXEMPTION IS ENCODED, NOT ASSUMED. A page that declares
`<meta name="rapidmeta:pooled-estimate" content="NONE">` publishes NO current pool; it is a
withdrawal notice whose whole purpose is to show the withdrawn value beside the statement that
it is withdrawn. Policing it for "two live pooled values" is a category error. Skipped by name,
counted in kinds, never folded into the clean population.

RATCHETED. Four pages split today (ALIROCUMAB_LIPID, ARNI_HF, INCLISIRAN_LIPID_KIDNEY,
SGLT2_HF); ALIROCUMAB belongs to another lane and is frozen by NAME, not touched. A PASS means
NO NEW split, never "clean". Frozen in gates/BODY_BANNER_SPLIT_BASELINE.json, printed every run;
retired entries are reported as the fix landing, never required to persist.

Exit codes are the harness's: 0 PASS, 1 FAIL, 2 VACUOUS, 3 BROKEN.
"""
from __future__ import annotations

import glob
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _harness as H                                                        # noqa: E402

FREEZE = "BODY_BANNER_SPLIT_BASELINE.json"
POOL_NONE_RE = re.compile(r'name="rapidmeta:pooled-estimate"\s+content="NONE"', re.I)

BANNER_RE = re.compile(
    r"(?is)<aside\b[^>]*\bdata-banner\s*=\s*['\"][^'\"]+['\"][^>]*>.*?</aside>")
DROP_BLOCK_RE = re.compile(r"(?is)<(script|style|svg|table|pre|code)\b[^>]*>.*?</\1>")
TAG_RE = re.compile(r"(?s)<[^>]+>")
ELEMENT_RE = re.compile(
    r"(?is)<(?P<tag>h1|h2|h3|p|li)\b(?P<attrs>[^>]*)>(?P<body>.*?)</(?P=tag)>")
K_RE = re.compile(r"\bk\s*=\s*(\d+)\b|\bacross\s+(\d+)\s+trials?\b", re.I)
TRIALS_RE = re.compile(r"\bfrom\s+the\s+(\w+)\s+trials?\b", re.I)
EFFECT_RE = re.compile(
    r"\b(?P<label>HR|RR|OR|MD|SMD|hazard ratio|risk ratio|rate ratio|odds ratio|"
    r"mean difference|risk difference)\b[^.;:<>{}]{0,80}?(?P<value>-?\d+(?:\.\d+)?)", re.I)
BARE_POOLED_RE = re.compile(
    r"\bpooled(?:\s+(?:estimate|result|effect|ratio|hazard ratio|risk ratio|"
    r"rate ratio|odds ratio|mean difference))?\s+(?:is|was)?\s*(?P<value>-?\d+(?:\.\d+)?)", re.I)
CURRENT_WORDS = re.compile(r"\b(current|corrected|now|moving|moves|making this)\b", re.I)
SUMMARY_WORDS = re.compile(
    r"\b(abstract|results?\.|headline|summary|take from this|clinician|programme|"
    r"pooled estimate|pooled hazard ratio|pooled result)\b", re.I)
DISOWNED_WORDS = re.compile(
    r"\b(withdrawn|superseded|retired|dead-analysis|dead analysis|disregard|prior|"
    r"sensitivity|benchmark|prior synthesis|external benchmark|not shown beside it|"
    r"not support for a published pool|not as a robustness claim|defect was detected)\b", re.I)
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def _clean(fragment):
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", fragment))).strip()


def _measure(label):
    if not label:
        return None
    x = label.lower()
    return {"hr": "HR", "hazard ratio": "HR", "rr": "RR", "risk ratio": "RR",
            "rate ratio": "RR", "or": "OR", "odds ratio": "OR", "md": "MD",
            "mean difference": "MD", "risk difference": "MD", "smd": "SMD"}.get(x, label.upper())


def _banner_current(block):
    """(k, measure, effect) declared CURRENT in a correction/supersession banner, or None."""
    text = _clean(block)
    if not re.search(r"\b(correction|supersession|superseded)\b", text, re.I):
        return None
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if not CURRENT_WORDS.search(sent) or not re.search(r"\bpool(?:ed)?\b", sent, re.I):
            continue
        parse = sent
        mover = re.search(r"\b(?:moves?|moving)\b.+?\bfrom\b.+?\bto\b(?P<tail>.+)", sent, re.I)
        if mover:
            parse = mover.group("tail")
        k = None
        km = K_RE.search(parse if mover else sent)
        if km:
            k = int(km.group(1) or km.group(2))
        else:
            tm = TRIALS_RE.search(sent)
            if tm:
                k = NUMBER_WORDS.get(tm.group(1).lower())
        measure = effect = None
        em = list(EFFECT_RE.finditer(parse))
        if em:
            measure = _measure(em[-1].group("label"))
            effect = float(em[-1].group("value"))
        elif "pool" in sent.lower():
            bm = BARE_POOLED_RE.search(parse)
            if bm:
                effect = float(bm.group("value"))
        if k is not None or effect is not None:
            return (k, measure, effect)
    return None


def _declarations(src):
    out = []
    for m in BANNER_RE.finditer(src):
        d = _banner_current(m.group(0))
        if d:
            out.append(d)
    return out


def _effect_matches(a, b):
    if a is None or b is None:
        return True
    return abs(a - b) <= max(0.001, abs(a) * 0.0005)


def _body_statements(src):
    body = DROP_BLOCK_RE.sub(" ", BANNER_RE.sub(" ", src))
    out, heading, pending = [], "", ""
    for m in ELEMENT_RE.finditer(body):
        tag = m.group("tag").lower()
        attrs = m.group("attrs") or ""
        text = _clean(m.group("body"))
        if not text:
            continue
        if tag in {"h1", "h2", "h3"}:
            heading = text
            continue
        combined = ("%s. %s" % (heading, text)).strip(". ")
        if "class" in attrs.lower() and "num" in attrs.lower():
            pending = combined
            continue
        if pending:
            combined = "%s %s" % (pending, text)
            pending = ""
        if DISOWNED_WORDS.search(combined) or not SUMMARY_WORDS.search(combined):
            continue
        if not (EFFECT_RE.search(combined) or BARE_POOLED_RE.search(combined)):
            continue
        if not re.search(r"\b(pool|pooled|hazard ratio|risk ratio|rate ratio|odds ratio|"
                         r"mean difference|HR|RR|OR|MD|SMD|across\s+\d+\s+trials?)\b",
                         combined, re.I):
            continue
        out.append(combined)
    return out


def _stmt_values(text):
    k = None
    km = K_RE.search(text)
    if km:
        k = int(km.group(1) or km.group(2))
    vals = []
    for m in EFFECT_RE.finditer(text):
        vals.append((k, _measure(m.group("label")), float(m.group("value"))))
    for m in BARE_POOLED_RE.finditer(text):
        v = float(m.group("value"))
        if not any(abs(v - e[2]) < 1e-12 for e in vals):
            vals.append((k, None, v))
    return vals


def page_split(src):
    """Return a short reason string if banner and body declare different current pools, else ''."""
    decls = _declarations(src)
    if not decls:
        return ""
    for dk, dm, de in decls:
        for stmt in _body_statements(src):
            for bk, bm, be in _stmt_values(stmt):
                measure_ok = dm is None or bm is None or dm == bm
                k_diff = dk is not None and bk is not None and dk != bk
                eff_diff = measure_ok and de is not None and not _effect_matches(de, be)
                if k_diff or eff_diff:
                    parts = []
                    if k_diff:
                        parts.append("k %s != current k %s" % (bk, dk))
                    if eff_diff:
                        parts.append("effect %g != current %g" % (be, de))
                    return "; ".join(parts)
    return ""


# -- synthetic, permanent discrimination controls (never the live page) --------------
_POS = (
    '<aside data-banner="__ctl_correction__" role="note">'
    '<strong>Correction — this page’s analysis is superseded</strong>'
    '<p>The analysis below is the prior <strong>k=3</strong> pool, <strong>HR 0.7636</strong>. '
    'The <strong>current object holds k=4</strong>: adding a trial gives a pooled '
    '<strong>HR 0.7738</strong>.</p></aside>'
    '<h2>Results.</h2><p>Pooled result. HR 0.7636 (0.71 to 0.83), random, estimator REML, k = 3.</p>')
_NEG = (
    '<aside data-banner="__ctl_correction__" role="note">'
    '<strong>Correction — this page’s analysis is superseded</strong>'
    '<p>The analysis below is the prior <strong>k=3</strong> pool. '
    'The <strong>current object holds k=4</strong>: adding a trial gives a pooled '
    '<strong>HR 0.7738</strong>.</p></aside>'
    '<h2>Results.</h2><p>Pooled result. HR 0.7738 (0.72 to 0.83), random, estimator REML, k = 4.</p>')
# EXEMPT: a withdrawal notice that carries a REAL banner/body split, protected ONLY by the
# pooled-estimate=NONE tag. Proves the exemption does the work -- not a coincidentally-clean
# page -- and cannot silently rot into a page the detector simply never flags.
_EXEMPT = '<meta name="rapidmeta:pooled-estimate" content="NONE">' + _POS


def main(argv):
    plant = "--plant" in argv
    gate = H.Gate("BODY MATCHES BANNER",
                  "a page's correction banner and its own body must not declare two "
                  "different current pooled results")
    named = gate.expect_case(
        "discriminates",
        "three SYNTHETIC pages -- one banner/body split (must fire), one consistent (must "
        "not), one withdrawal notice with a real split protected only by pooled-estimate=NONE "
        "(must be exempt) -- decided correctly, every run")
    gate.requires_control()

    pos_fires = bool(page_split(_POS))
    neg_clean = not page_split(_NEG)
    # the exempt probe MUST have a real split AND be tagged; the exemption, not luck, protects it
    exempt_would_flag = bool(page_split(_EXEMPT))
    exempt_is_tagged = bool(POOL_NONE_RE.search(_EXEMPT))
    exempt_ok = exempt_would_flag and exempt_is_tagged
    if pos_fires and neg_clean and exempt_ok:
        gate.saw(named)
    if not pos_fires:
        gate.broken("positive control did not fire -- the banner/body detector is inert")
    if not exempt_would_flag:
        gate.broken("exempt probe has no split -- it would pass for the wrong reason, not "
                    "because the exemption protected it")
    gate.control(1, 0 if neg_clean else 1,
                 [] if neg_clean else ["consistent synthetic page flagged"], accuses=True)

    repo = H.repo_root()
    pages = sorted(glob.glob(os.path.join(repo, "*_REVIEW.html")))
    flagged, with_banner, withdrawn = {}, 0, 0
    for p in pages:
        src = open(p, encoding="utf-8", errors="replace").read()
        if POOL_NONE_RE.search(src):
            withdrawn += 1
            continue
        if _declarations(src):
            with_banner += 1
        reason = page_split(src)
        if reason:
            flagged[os.path.basename(p)] = reason

    if plant:
        # verify_gates_can_fail: a NEW split not in the freeze must make the gate FAIL.
        flagged["__planted_split_page__.html"] = "PLANT: k 3 != current k 4"

    gate.kinds({
        "*_REVIEW.html pages scanned": len(pages),
        "  withdrawal notices (pooled-estimate=NONE) -- exempt, no current pool": withdrawn,
        "  carry a correction/supersession banner": with_banner,
        "  banner/body split -- the finding": len(flagged),
    })
    gate.coverage(len(pages) - withdrawn, len(pages),
                  "withdrawal notices publish NO current pool, so there are not two live "
                  "values for them to disagree on")

    new = H.ratchet(gate, FREEZE, sorted(flagged),
                    "rendered pages whose correction banner and body declare different "
                    "current pooled results",
                    escalated="out/ESCALATIONS.jsonl")
    for name in sorted(flagged):
        mark = "NEW " if name in new else "frozen "
        gate.note("%s%s -- %s" % (mark, name, flagged[name]))
    for name in new:
        gate.finding("body-banner-split", "%s: %s" % (name, flagged[name]),
                     numerator=1, denominator=len(pages) - withdrawn)

    return gate.report(denominator="%d pages (%d exempt withdrawals)" % (len(pages), withdrawn))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
