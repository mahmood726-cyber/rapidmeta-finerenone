import io, sys, json, re, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ------------------------------------------------------------------ projector
P = r"F:\rapidmeta-ssot-shell\ssot\projectors2.py"
s = open(P, encoding="utf-8").read()

old = '''    boxes = [
        {"label": "Records identified by database searching", "n": None,
         "note": "Not recorded by the pipeline that built this corpus."},
        {"label": "Duplicates removed", "n": None,
         "note": "Not recorded; cannot be reconstructed without inventing it."},'''
new = '''    # THE IDENTIFICATION TIER WAS NOT UNRECOVERABLE. The object recorded it all
    # along, in search.databases: each database's hit count as the API returned
    # it and how many of those were retrieved. They sum to exactly the screened
    # corpus, and the corpus's own per-source tally agrees independently. The
    # "permanently unrecoverable" note was stale, and an empty identification
    # tier is a submission blocker -- so this is populated from stored evidence
    # rather than by re-running the search, which means no record enters or
    # leaves the pool and k cannot move.
    dbs = (canon.get("search") or {}).get("databases") or []
    ident, per_db = 0, []
    for db in dbs:
        m = re.search(r"(\\d+)", str(db.get("records_retrieved")
                                     or db.get("hit_count") or ""))
        if not m:
            per_db, ident = [], 0
            break
        ident += int(m.group(1))
        per_db.append("%s %s" % (str(db.get("database", "")).split(" (")[0],
                                 m.group(1)))
    by_src = collections.Counter(r.get("source") for r in corpus)
    boxes = [
        {"label": "Records identified from databases and registers",
         "n": ident or None,
         "note": ("; ".join(per_db)) if per_db else
                 "No per-database counts are recorded.",
         "side": "corpus tally: %s" % ", ".join(
             "%s %d" % (k, v) for k, v in sorted(by_src.items()) if k)},
        {"label": "Records removed before screening",
         "n": 0 if ident and ident == len(corpus) else None,
         "note": ("No de-duplication step is recorded. The two sources return "
                  "disjoint record types and their retrieved totals sum exactly "
                  "to the screened corpus, so none was removed."
                  if ident == len(corpus) else
                  "Not recorded; cannot be reconstructed without inventing it.")},'''
assert s.count(old) == 1
s = s.replace(old, new)

# arithmetic closure now spans the identification tier as well
old2 = '''    screened = len(corpus)
    tiab_removed = (ex_tiab or 0) + (und or 0)
    if screened - tiab_removed != full:'''
new2 = '''    screened = len(corpus)
    tiab_removed = (ex_tiab or 0) + (und or 0)
    _ident_ok = (not ident) or (ident == screened)
    if screened - tiab_removed != full or not _ident_ok:'''
assert s.count(old2) == 1
s = s.replace(old2, new2)
old3 = '''            "Refused: %d screened minus %d removed at title/abstract does not "
            "equal the %d assessed at full text."
            % (screened, tiab_removed, full)),'''
new3 = '''            "Refused: the flow does not reconcile. %d identified, %d screened, "
            "%d removed at title/abstract, %d assessed at full text."
            % (ident, screened, tiab_removed, full)),'''
assert s.count(old3) == 1
s = s.replace(old3, new3)
open(P, "w", encoding="utf-8").write(s)
print("projectors2: identification tier populated; closure spans it")

# ------------------------------------------------------------------- object
O = r"F:\rapidmeta-ssot-shell\ssot\arni-hfref\arni-hfref.json"
d = json.load(open(O, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
pi = d.get("prisma_items") or {}
if "_permanently_unrecoverable" in pi:
    old_claim = pi["_permanently_unrecoverable"]
    pi["_permanently_unrecoverable"] = collections.OrderedDict(
        items=[],
        why="NONE. This field previously claimed the identification counts -- "
            "duplicates removed, records sought against retrieved -- could not "
            "be reconstructed. That was wrong, and it was wrong about data the "
            "object already held: search.databases records each database's hit "
            "count as the API returned it and how many were retrieved (PubMed "
            "331 of 331, ClinicalTrials.gov 92 of 92). Those sum to 423, which "
            "is exactly the screened corpus, and the corpus's own per-source "
            "tally gives the same split independently. The PRISMA identification "
            "tier is populated from that evidence. No search was re-run, so no "
            "record entered or left the pool and k is unchanged at 4.",
        corrected_utc="2026-08-14T00:00:00Z",
        superseded_claim=old_claim)
    d["prisma_items"] = pi
d.setdefault("claims_corrected", []).append(collections.OrderedDict([
    ("claim", "that the PRISMA identification counts for this corpus were "
              "permanently unrecoverable and had to be shown as NOT RECORDED"),
    ("correction", "They were in search.databases the whole time. PubMed "
                   "returned 331 and all 331 were retrieved; ClinicalTrials.gov "
                   "returned 92 and all 92 were retrieved; 331 + 92 = 423 = the "
                   "screened corpus, and the corpus's per-source tally agrees. "
                   "An empty identification tier is a submission blocker and it "
                   "was empty because of a stale note, not because of missing "
                   "data. Populated WITHOUT re-running the search, so the pool "
                   "is untouched."),
    ("source_id", "search.databases; screening.corpus source tally"),
    ("corrected_utc", "2026-08-14T00:00:00Z")]))
json.dump(d, open(O, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("object: unrecoverable claim corrected and logged")
