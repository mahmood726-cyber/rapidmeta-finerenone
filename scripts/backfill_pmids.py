"""Verified PMID backfill: fill EMPTY/null pmids on NCT-keyed trials from the
DataBankList-derived resolver (outputs/pmid_resolver/nct_to_pmid.json), spot-
verified correct against PubMed (each PMID's record names its NCT). NO guessing:
a trial whose NCT is absent from the resolver is left null. Never overwrites an
existing pmid. Scoped per-trial via brace-matched objects (robust to field order,
unlike a flat [^{}] regex which breaks when baseline:{} precedes pmid).

--dry-run : report counts, write nothing.
"""
import re, glob, io, sys, os, json, subprocess, importlib.util, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("dia", os.path.join(REPO, "scripts", "data_integrity_audit.py"))
dia = importlib.util.module_from_spec(spec); spec.loader.exec_module(dia)

_raw = json.load(open(os.path.join(REPO, "outputs", "pmid_resolver", "nct_to_pmid.json"), encoding="utf-8"))
RESOLVER = {}
for nct, v in _raw.items():
    pmid = v.get("pmid") if isinstance(v, dict) else v
    if pmid and re.fullmatch(r"\d{6,8}", str(pmid)):
        RESOLVER[nct] = str(pmid)

EMPTY_PMID = re.compile(r'(pmid\s*:\s*)(null|""|\'\')')


def jscheck(fn):
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "jscheck.py"), fn],
                       capture_output=True, text=True)
    return "[JS-OK]" in (r.stdout + r.stderr)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apps = trials = reverts = 0
    for fn in sorted(glob.glob(os.path.join(REPO, "*_REVIEW.html"))):
        html = open(fn, encoding="utf-8", errors="replace").read()
        repls = []  # (old_obj, new_obj)
        for key, obj in dia.find_trial_objects(html):
            if not re.fullmatch(r"NCT\d{8}", str(key)):
                continue
            pmid = RESOLVER.get(str(key))
            if not pmid:
                continue
            m = EMPTY_PMID.search(obj)
            if not m:
                continue  # already has a pmid, or no pmid field
            new_obj = obj[:m.start()] + f'pmid:"{pmid}"' + obj[m.end():]
            repls.append((obj, new_obj))
        if not repls:
            continue
        new = html
        n = 0
        for old, rep in repls:
            if new.count(old) == 1:        # unique -> safe splice
                new = new.replace(old, rep, 1); n += 1
        if n == 0 or new == html:
            continue
        if args.dry_run:
            apps += 1; trials += n; continue
        open(fn, "w", encoding="utf-8").write(new)
        if not jscheck(fn):
            open(fn, "w", encoding="utf-8").write(html); reverts += 1
            print(f"  REVERTED {os.path.basename(fn)}"); continue
        apps += 1; trials += n

    print(f"{'DRY-RUN ' if args.dry_run else ''}apps: {apps}, pmids filled: {trials}, reverts: {reverts}")


if __name__ == "__main__":
    main()
