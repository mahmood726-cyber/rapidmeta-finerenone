# -*- coding: utf-8 -*-
"""Build a review's eligibility block FROM its authored JSON protocol, through the harness, and
diff it against the CURRENTLY SERVED page -- reporting what would change and what a full rebuild
would refuse or drop, and WRITING NOTHING. This is the "report before applying" step.

It does NOT overwrite the served page. It answers three questions per review:

  1. WHAT WOULD CHANGE. The protocol's P/I/C/D rows vs the served page's current PICO rows
     (data-pico cells if present, else the eligibility prose). A criterion the rebuild would add,
     remove, narrow or widen is shown, never silently applied.

  2. WHAT THE REBUILD WOULD DROP OR REFUSE. The real guards, evaluated against the REAL page
     name: do_not_rebuild (is the page protected?), the generator pin (is the working generator
     missing a served renderer fix?), and check_correction_survives (does the page carry a pinned
     published correction, and is it still present?). A rebuild that would drop a pinned
     correction is REFUSED by the builder; this reports that in advance.

  3. WHETHER THE REBUILD WOULD SILENTLY IMPROVE A NUMBER OR CRITERION. If the served page states
     a criterion the object has since retracted (the iv-iron 'route and outcome' case), a rebuild
     would correct it -- an improvement, which the owner's rule says is a FINDING, not a success,
     and must be surfaced here.
"""
from __future__ import annotations
import io, os, re, sys, json, glob
sys.path.insert(0, "ssot")
sys.path.insert(0, "scripts")
import protocol_schema as PS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rendered(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def load_protocol(stem):
    """Read + VALIDATE the authored JSON protocol for a review stem. Refuse an invalid one."""
    hits = sorted(glob.glob(os.path.join(ROOT, "protocols", "*_retrospective_v1.json")))
    for h in hits:
        p = json.load(io.open(h, encoding="utf-8"))
        if p.get("review_stem") == stem:
            ok, errs = PS.validate(p)
            if not ok:
                raise SystemExit("protocol %s is INVALID, refusing to diff:\n  - %s"
                                 % (os.path.basename(h), "\n  - ".join(errs)))
            p["_path"] = h
            return p
    return None


def protocol_rows(p):
    """The four eligibility rows the harness would render from the protocol, as rendered text."""
    el = p["eligibility"]
    return [("Population", el["population"]["criterion"], el["population"]["rule_id"]),
            ("Intervention", el["intervention"]["criterion"], el["intervention"]["rule_id"]),
            ("Comparator", el["comparator"]["criterion"], el["comparator"]["rule_id"]),
            ("Design", el["design"]["criterion"], el["design"]["rule_id"])]


def served_pico(html):
    """Current PICO rows on the served page: data-pico cells if inserted, else parsed from the
    eligibility prose. Returns {label: (value_or_None, source)} for P/I/C."""
    out = {}
    # data-pico cells ONLY -- the attribute must actually be present, or this is some other
    # table (a trial-characteristics row labelled 'Population' is NOT the eligibility PICO).
    for m in re.finditer(r"<t[dh][^>]*>\s*(Population|Intervention|Comparator)\s*</t[dh]>\s*"
                         r"<t[dh][^>]*\bdata-pico\b[^>]*>(.*?)</t[dh]>", html, re.S | re.I):
        label = m.group(1).title()
        attr_and_cell = m.group(0)
        is_null = "data-pico='null'" in attr_and_cell or 'data-pico="null"' in attr_and_cell
        out[label] = (None if is_null else _rendered(m.group(2))[:400], "data-pico row")
    if out:
        return out
    # fall back to eligibility prose: "The population is X. The intervention is Y. The comparator is Z."
    txt = _rendered(html)
    for label, pat in (("Population", r"The population is (.+?)\.\s+The intervention"),
                       ("Intervention", r"The intervention is (.+?)\.\s+The comparator"),
                       ("Comparator", r"The comparator is (.+?)(?:\s+--|\.\s+The outcome|\.\s+[A-Z])")):
        mm = re.search(pat, txt)
        out[label] = (mm.group(1).strip()[:400] if mm else None, "eligibility prose")
    return out


def guard_report(page, served_html):
    import do_not_rebuild as DNR
    rep = {}
    # do-not-rebuild
    rep["do_not_rebuild"] = ("PROTECTED -- rebuild refused" if page in DNR.PAGES else "not protected")
    # generator pin
    import subprocess
    miss = []
    for sha in DNR.REQUIRED_GENERATOR_COMMITS:
        r = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                           cwd=ROOT, capture_output=True)
        if r.returncode != 0:
            miss.append(sha[:9])
    rep["generator_pin"] = ("OK -- all %d renderer fixes are ancestors of HEAD"
                            % len(DNR.REQUIRED_GENERATOR_COMMITS)) if not miss \
        else ("STALE -- missing %s (a rebuild would revert a served fix)" % ", ".join(miss))
    # published correction
    try:
        rec = json.load(io.open(DNR.CORRECTIONS, encoding="utf-8")).get("pages", {}).get(page)
    except Exception:
        rec = None
        rep["published_correction"] = "corrections file unreadable -- builder would REFUSE"
    if rec and rec.get("class") == "PUBLISHED_CORRECTION":
        must = rec.get("must_render", "")
        present = DNR._rendered(must) in DNR._rendered(served_html) if must else False
        rep["published_correction"] = ("PINNED -- must survive any rebuild; currently %s on served"
                                       % ("PRESENT" if present else "ABSENT (!)"))
    elif "published_correction" not in rep:
        rep["published_correction"] = "none pinned for this page"
    return rep


def run(stem, page):
    served_path = os.path.join(ROOT, page)
    served = io.open(served_path, encoding="utf-8").read()
    p = load_protocol(stem)
    print("=" * 78)
    print("REVIEW: %s   ->   %s" % (stem, page))
    print("=" * 78)
    if not p:
        print("  NO authored JSON protocol found for this stem.")
        return
    print("  protocol: %s" % os.path.basename(p["_path"]))
    print("  prospective: %s   authored: %s" % (p["prospective"], p["authored_utc"]))
    print("  provenance: %s" % _rendered(p["provenance"])[:200])
    print()
    prows = protocol_rows(p)
    served_rows = served_pico(served)
    print("  --- WHAT WOULD CHANGE (protocol P/I/C/D  vs  served) ---")
    for label, crit, rid in prows:
        sv = served_rows.get(label, ("(no such row served)", "-"))
        sval, ssrc = sv
        if sval is None:
            verdict = "ADD (served shows null/absent)"
        else:
            pa = set(re.findall(r"[a-z]{4,}", crit.lower()))
            sa = set(re.findall(r"[a-z]{4,}", (sval or "").lower()))
            j = len(pa & sa) / max(1, len(pa | sa))
            contained = sa and (len(sa & pa) / len(sa) >= 0.8)
            if contained and j < 0.5:
                verdict = "reproduces (served substance kept; protocol adds rationale)"
            elif j >= 0.5:
                verdict = "reproduces (overlap %.2f)" % j
            else:
                verdict = "CHANGES (overlap %.2f)" % j
        print("   [%s] %-12s %s" % (rid, label, verdict))
        print("        protocol: %s" % crit[:150])
        print("        served  : %s  [%s]" % ((sval or "(null/absent)")[:150], ssrc))
    # design has no served counterpart in the P/I/C model
    print()
    # retracted-criterion-served check
    print("  --- SILENT-IMPROVEMENT CHECK (served states a retracted criterion?) ---")
    cf = p.get("carries_forward")
    st = _rendered(served)
    if re.search(r"comparator,?\s+route\s+and\s+outcome|outcome criterion is", st, re.I):
        print("   FINDING: served eligibility still states OUTCOME as an eligibility axis")
        print("            ('route and outcome' / 'The outcome criterion is ...').")
        if cf:
            print("            protocol.carries_forward: %s" % _rendered(json.dumps(cf.get("what","")))[:180])
        print("            A rebuild from the current object would correct this. Per the rule,")
        print("            that is a FINDING to report, NOT a change to apply silently.")
    else:
        print("   served eligibility does not state a retracted outcome-eligibility criterion.")
    print()
    print("  --- WHAT A FULL REBUILD WOULD REFUSE / DROP (real guards, real page name) ---")
    for k, v in guard_report(page, served).items():
        print("   %-22s %s" % (k, v))
    print()
    print("  NOTHING WRITTEN. This is the pre-apply report.")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    TARGETS = [("azilsartan-chlorthalidone-vs-olmesartan-hctz", "AZILSARTAN_CLD_VS_OLM_HCTZ_REVIEW.html"),
               ("iv-iron-hf", "IV_IRON_HF_REVIEW.html")]
    if len(sys.argv) >= 3:
        TARGETS = [(sys.argv[1], sys.argv[2])]
    for stem, page in TARGETS:
        run(stem, page)
        print()
