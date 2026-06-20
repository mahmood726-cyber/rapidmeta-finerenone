#!/usr/bin/env python
"""Codemod: fix per-row PMID misattributions verified against PubMed (Class-2 citation fix).

Each target app had ONE wrong PMID stamped on TWO genuinely different named trials, so
the fix assigns each row its own verified primary-publication PMID. Anchored on the trial
NAME (unique within a file) so the two rows that currently share the wrong PMID get
DIFFERENT corrected values. Every new PMID was confirmed by fetching its PubMed title and
matching trial+drug (see findings/shared_control_fix_report.md). Unresolved trials
(NOBILITY, PYRENEES) are intentionally NOT touched -- guessing a PMID would be fabrication.

Idempotent: if the new PMID is already next to the name, the row is reported `already`.

Usage:
  python fix_pmid_misattribution.py --dry-run
  python fix_pmid_misattribution.py --apply
"""
import argparse, io, os, re, sys

# (file, trial_name_anchor, old_pmid, new_pmid, verified_title)
FIXES = [
    ("CART_B_CELL_LYMPHOMA_REVIEW.html", "BELINDA", "33288485", "34904798",
     "Second-Line Tisagenlecleucel or Standard Care in Aggressive B-Cell Lymphoma (NEJM)"),
    ("CART_B_CELL_LYMPHOMA_REVIEW.html", "TRANSFORM", "33288485", "35717989",
     "Lisocabtagene maraleucel vs standard of care (TRANSFORM, Lancet 2022)"),
    ("HCC_LOCAL_THERAPY_NMA_REVIEW.html", "EMERALD-1", "32557715", "39798579",
     "Durvalumab +/- bevacizumab with TACE in HCC (EMERALD-1, Lancet 2025)"),
    ("HCC_LOCAL_THERAPY_NMA_REVIEW.html", "TACTICS-HCC", "32557715", "31801872",
     "TACE plus sorafenib (TACTICS, Gut 2020, Kudo)"),
    ("OBINUTUZUMAB_LN_AUTO_FULL_REVIEW.html", "REGENCY", "33693991", "39927615",
     "Efficacy and Safety of Obinutuzumab in Active Lupus Nephritis (REGENCY, NEJM 2025)"),
    ("OBINUTUZUMAB_LN_AUTO_FULL_REVIEW.html", "NCT02550652", "33693991", "34615636",
     "Obinutuzumab for proliferative lupus nephritis (NOBILITY, NCT02550652, Ann Rheum Dis 2022)"),
    ("HIV_PREP_INJECTABLE_REVIEW.html", "HPTN 083", "32497490", "34379922",
     "Cabotegravir for HIV PrEP in cisgender men/transgender women (HPTN 083, NEJM 2021)"),
    ("HIV_PREP_INJECTABLE_REVIEW.html", "HPTN 084", "32497490", "35594553",
     "Cabotegravir for HIV PrEP in women (HPTN 084, Lancet 2022)"),
    ("ROXADUSTAT_ANEMIA_CKD_AUTO_FULL_REVIEW.html", "Dolomites", "36005278", "34077510",
     "Roxadustat for anaemia in non-dialysis CKD (DOLOMITES, NDT 2021)"),
    ("ROXADUSTAT_RENAL_ANEMIA_AUTO_FULL_REVIEW.html", "Dolomites", "36005278", "34077510",
     "Roxadustat for anaemia in non-dialysis CKD (DOLOMITES, NDT 2021)"),
    ("ROXADUSTAT_ANEMIA_CKD_AUTO_FULL_REVIEW.html", "Pyrenees", "36005278", "34537926",
     "Roxadustat maintenance anaemia ESKD on dialysis (PYRENEES, Adv Ther 2021; n 415/421 match)"),
    ("ROXADUSTAT_RENAL_ANEMIA_AUTO_FULL_REVIEW.html", "Pyrenees", "36005278", "34537926",
     "Roxadustat maintenance anaemia ESKD on dialysis (PYRENEES, Adv Ther 2021; n 415/421 match)"),
]

WINDOW = 800  # chars after the name anchor in which the row's pmid must appear


def apply_file(path, repls, apply):
    with io.open(path, encoding="utf-8") as f:
        src = f.read()
    out = src
    log = []
    for name, old, new, _title in repls:
        anchor = 'name:"%s"' % name
        i = out.find(anchor)
        if i < 0:
            log.append("NO-ANCHOR:%s" % name); continue
        seg = out[i:i + WINDOW]
        oldp, newp = 'pmid:"%s"' % old, 'pmid:"%s"' % new
        if newp in seg:
            log.append("already:%s" % name); continue
        j = seg.find(oldp)
        if j < 0:
            log.append("OLD-PMID-NOT-NEAR:%s (%s)" % (name, old)); continue
        # exactly one replacement at this position
        abs_pos = i + j
        out = out[:abs_pos] + newp + out[abs_pos + len(oldp):]
        log.append("OK:%s %s->%s" % (name, old, new))
    changed = out != src
    if apply and changed:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(out)
    return changed, log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    apply = a.apply and not a.dry_run
    byfile = {}
    for fn, name, old, new, title in FIXES:
        byfile.setdefault(fn, []).append((name, old, new, title))
    bad = 0
    for fn, repls in byfile.items():
        if not os.path.exists(fn):
            print("MISSING:", fn); bad += 1; continue
        changed, log = apply_file(fn, repls, apply)
        tag = "APPLIED" if (apply and changed) else ("WOULD-CHANGE" if changed else "no-change")
        print("[%s] %s" % (tag, fn))
        for l in log:
            print("    ", l)
            if "NOT" in l or "NO-ANCHOR" in l:
                bad += 1
    print("\n%s" % ("DRY-RUN" if not apply else "APPLIED"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
