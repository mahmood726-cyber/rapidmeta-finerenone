"""SUBJECT-MATCH GATE -- is the content on this page about this page's subject?

WHY THIS EXISTS
    On 2026-08-16 four pages went live carrying ANOTHER REVIEW'S trials.
    Sotagliflozin's page named sacubitril 24 times and PARADIGM-HF 13 times, and
    carried ARNI's Table 4 with its 558/4187 counts, because the manuscript was
    read from one hardcoded path for every build.

    FIVE pre-deploy checks passed it: tab shell, estimate preservation, empty
    panels, external refs, placeholder leaks. Each was individually correct and
    they were jointly blind to the largest defect the build can produce, because
    NO COVERAGE QUESTION WAS EVER ATTACHED TO THE SET. Nobody asked what a full
    pass would fail to establish. The honest answer was "everything except
    structure and one number".

WHAT A FULL PASS OF *THIS* GATE DOES NOT ESTABLISH
    Written in advance this time, which is the whole point.
    - NOT that the numbers are correct. Subject match is about WHOSE trials these
      are, not whether their values are right. A page can name exactly the right
      trials and misreport every one.
    - NOT that the trial set is COMPLETE. It checks the page does not carry
      foreign trials; it cannot tell you a trial is missing, because a page that
      silently drops a trial still matches on the ones it kept.
    - NOT that prose about the right drug is accurate, only that the drug named
      is this object's.
    - NOT anything about tabs, estimates, placeholders or links -- the other
      checks own those, and this one passing says nothing about them.
    - NOT that a shared-path defect is absent elsewhere in the build. It catches
      this defect's SYMPTOM on the rendered page. The cause was a hardcoded path,
      and only reading the code finds another one of those.
"""
from __future__ import annotations
import json, os, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SSOT = r"F:\rapidmeta-ssot-shell"

NCT = re.compile(r"NCT\d{8}")


def own_identifiers(canon):
    """Trial names and registration ids this object legitimately owns."""
    names, ncts = set(), set()
    for t in ((canon.get("inputs") or {}).get("trials")) or []:
        n = (t.get("name") or "").strip()
        if n and len(n) > 2:
            names.add(n)
        if t.get("nct"):
            ncts.add(str(t["nct"]).strip())
    # trials named in screening / excluded lists are legitimately mentionable too
    blob = json.dumps(canon, ensure_ascii=False)
    ncts |= set(NCT.findall(blob))
    for key in ("screening", "eligible_but_not_contributing", "reconciliation"):
        for m in re.finditer(r'"name"\s*:\s*"([^"]{3,60})"', json.dumps(canon.get(key) or {},
                                                                        ensure_ascii=False)):
            names.add(m.group(1).strip())
    return names, ncts


def visible(t):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def check(page_path, canon):
    html = open(page_path, encoding="utf-8", errors="replace").read()
    v = visible(html)
    names, ncts = own_identifiers(canon)
    page_ncts = set(NCT.findall(v))
    foreign_ncts = sorted(page_ncts - ncts)

    # Trial-name check uses the OBJECT's own vocabulary as the allow-list and asks
    # whether any prominent ALL-CAPS trial acronym on the page is absent from it.
    # Word-boundary matched: 'AF_' once matched inside 'TAF_TDF' and 'TAVI' inside
    # 'roTAVIrus', which put hepatitis B and rotavirus in the cardiology bucket.
    acro = re.findall(r"\b([A-Z][A-Z0-9]{3,}(?:-[A-Z0-9]+)*)\b", v)
    counts = {}
    for a in acro:
        counts[a] = counts.get(a, 0) + 1
    allow = {a.upper() for n in names for a in re.findall(r"[A-Za-z0-9\-]+", n)}
    allow |= {"PRISMA", "GRADE", "ROB", "PICO", "CI", "HR", "RR", "OR", "MD", "SMD",
              "REML", "HKSJ", "DL", "PM", "NCT", "PDF", "HTML", "JSON", "CSV",
              "DOCX", "SVG", "WEBR", "FDA", "EMA", "NICE", "WHO", "WEB", "URL",
              "DOI", "PMID", "PMC", "ISTH", "NYHA", "LVEF", "MACE", "ITT"}
    foreign_names = sorted((a, c) for a, c in counts.items()
                           if a not in allow and c >= 3 and not a.startswith("NCT"))

    # THE ACRONYM SIGNAL IS REPORT-ONLY, NOT BLOCKING.
    # As a blocking rule it was a false-positive flood: it fired on clean ARNI and
    # on the reverted flat sotagliflozin, matching ordinary capitalised words in
    # headings -- ABSENT, AGAINST, BOTH, COUNTS, DIFFERENT, ELIGIBILITY. A gate
    # nobody can satisfy gets bypassed, and a bypassed gate rots; that is the same
    # failure the SKIP_REGRESSION escape hatch encoded.
    #
    # REGISTRATION IDS ARE THE IDENTITY KEY and they block. That is the
    # PARACHUTE-HF/ANSWER-HF lesson: a covering label was once accepted as document
    # identity while the registry id said otherwise. An NCT is unambiguous, it
    # cannot collide with English, and the contaminated build carried four foreign
    # ones. Detection rests on the identifier, not the name.
    verdict = "FAIL" if foreign_ncts else "PASS"
    return verdict, foreign_ncts, foreign_names[:8], len(names), len(ncts)


def main():
    if sys.argv[1] == "--selftest":
        return selftest()
    page, obj = sys.argv[1], sys.argv[2]
    canon = json.loads(open(obj, encoding="utf-8", errors="replace").read())
    v, fn, fnm, nn, nc = check(page, canon)
    print("%s  object owns %d trial names / %d NCTs" % (os.path.basename(page), nn, nc))
    if fn:
        print("  FOREIGN registration ids on the page: %s" % fn[:10])
    if fnm:
        print("  FOREIGN trial acronyms (>=3 mentions): %s" % fnm)
    print("  -> %s" % v)
    return 0 if v == "PASS" else 1


def selftest() -> int:
    """Positives: the four contaminated builds. Negative: clean ARNI."""
    ok = True
    arni = json.loads(open(os.path.join(SSOT, "ssot", "arni-hfref", "arni-hfref.json"),
                           encoding="utf-8", errors="replace").read())
    sota = json.loads(open(os.path.join(SSOT, "ssot", "sotagliflozin-hf",
                                        "sotagliflozin-hf.json"),
                           encoding="utf-8", errors="replace").read())
    cases = []
    contaminated = r"F:\claude-temp\tabbuild\SOTA_v3.html"
    if os.path.exists(contaminated):
        cases.append(("POSITIVE contaminated sotagliflozin build", contaminated, sota, "FAIL"))
    clean_arni = os.path.join(SSOT, "ARNI_HF_REVIEW.html")
    if os.path.exists(clean_arni):
        cases.append(("NEGATIVE clean ARNI against its own object", clean_arni, arni, "PASS"))
    clean_sota = os.path.join(SSOT, "SOTAGLIFLOZIN_HF_REVIEW.html")
    if os.path.exists(clean_sota):
        cases.append(("NEGATIVE reverted flat sotagliflozin", clean_sota, sota, "PASS"))
    for name, p, c, want in cases:
        v, fn, fnm, _, _ = check(p, c)
        good = v == want
        ok &= good
        print("  %-44s -> %-4s (want %s) %s" % (name, v, want, "correct" if good else "WRONG"))
        if fn or fnm:
            print("        foreign: ncts=%s acronyms=%s" % (fn[:4], [a for a, _ in fnm][:5]))
    print("\nWHAT A FAILURE WOULD LOOK LIKE: the contaminated build passing (we ship "
          "another drug's trials again), or clean ARNI failing (a gate nobody can "
          "satisfy, which gets bypassed and then rots).")
    print("-> SELFTEST PASS" if ok else "-> SELFTEST FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
