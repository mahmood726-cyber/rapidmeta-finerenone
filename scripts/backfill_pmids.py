"""Inject verified/mapped PMIDs into trial entries that have an empty pmid.

Sources (verified only): outputs/pmid_resolver/nct_to_pmid_recovered.json
(DataBankList-verified) + nct_to_pmid.json (AACT). Only fills EMPTY pmids;
never overwrites an existing one. jscheck-gated.
"""
from __future__ import annotations
import glob, io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_map():
    m = {}
    main = json.load(io.open(os.path.join(HERE, "outputs/pmid_resolver/nct_to_pmid.json"), encoding="utf-8"))
    for nct, v in main.items():
        if v.get("pmid"):
            m[nct] = v["pmid"]
    rec_path = os.path.join(HERE, "outputs/pmid_resolver/nct_to_pmid_recovered.json")
    if os.path.isfile(rec_path):
        for nct, v in json.load(io.open(rec_path, encoding="utf-8")).items():
            if v.get("pmid"):
                m[nct] = v["pmid"]
    return m


# NCT entry up to its (empty) pmid field. pmid is rendered right after name,
# before any nested braces, so [^{}]* is safe.
_PMID_RE = re.compile(r'((NCT\d{6,8}):\{[^{}]*?pmid:")(")')


def main():
    dry = "--dry-run" in sys.argv
    try:
        import jscheck
    except Exception:
        jscheck = None
    pmap = load_map()
    filled = files = reverted = 0
    for f in sorted(glob.glob(os.path.join(HERE, "*_AUTO*_FULL_REVIEW.html"))):
        html = io.open(f, encoding="utf-8", errors="replace").read()
        cnt = [0]

        def repl(m):
            pmid = pmap.get(m.group(2))
            if not pmid:
                return m.group(0)
            cnt[0] += 1
            return m.group(1) + pmid + m.group(3)

        new = _PMID_RE.sub(repl, html)
        if cnt[0] == 0 or new == html:
            continue
        files += 1
        filled += cnt[0]
        if dry:
            continue
        io.open(f, "w", encoding="utf-8", newline="").write(new)
        if jscheck is not None and jscheck.check(f):
            io.open(f, "w", encoding="utf-8", newline="").write(html)
            reverted += 1
            filled -= cnt[0]
            files -= 1

    print(f"{'DRY-RUN' if dry else 'APPLIED'}  pmids filled={filled} across {files} apps  reverted={reverted}")


if __name__ == "__main__":
    main()
