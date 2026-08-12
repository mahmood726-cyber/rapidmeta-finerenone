"""Ingest today's recovered evidence into the repo, byte-for-byte.

Nothing is reformatted, merged, summarised or tidied. The struck-through
correction in the backward-citation pass and the unaltered screener decisions are
the evidence; a clean-up would destroy exactly what makes them auditable.

Every file is hashed AT SOURCE and again AT DESTINATION and the two must match,
so a silent truncation during copy is caught rather than assumed away.
"""
import io, os, sys, json, shutil, hashlib, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

B = (r"C:\Users\mahmo\AppData\Roaming\Claude\local-agent-mode-sessions"
     r"\bdc5772c-ca03-473f-9464-80d37a7559d2\44788c9b-d162-4f2e-b3c2-d89031e65ab6")
SCRATCH = os.path.dirname(os.path.abspath(__file__))
DEST = r"F:\rapidmeta-ssot-shell\evidence\2026-08-12"

LANES = {
    "chagas-recovery":   os.path.join(B, "local_551b531f-277a-4351-9685-c26bfa0a4642", "outputs"),
    "count-recovery":    os.path.join(B, "local_95f555f3-c719-446f-9f1a-d5253bed5c4e", "outputs"),
    "search-and-screening": os.path.join(B, "local_520f4862-edcf-4de9-8ff9-1455a7636be6", "outputs"),
}

# Named explicitly in the preservation order, so absence is reported rather than
# noticed later.
EXPECTED = {
    "chagas-recovery": ["chagas_arni_data_recovery_report.md", "chagas_arni_extraction.csv",
                        "li2019_determination_memo.md", "answer_hf_route_log.md",
                        "corpus_provenance_audit_running_report.md",
                        "corpus_provenance_audit_running_report_2.md",
                        "corpus_provenance_audit_running_report_3_access_ledger.md"],
    "count-recovery": ["ARNI_HFrEF_per_arm_event_counts_extraction.md",
                       "CARDIO_COUNT_RECOVERY_PROGRESS.md", "rapidmeta_count_harness.py",
                       "COUNT_RECOVERY_PROCEDURE.md", "build_cardio_extraction.py",
                       "cardio_acm_extraction.json", "cardio_acm_harness_report.md",
                       "cardio_acm_harness_findings.json"],
    "search-and-screening": ["01_SEARCH_CAPTURE.md", "02_CORPUS_AND_SCREENING.tsv",
                             "03_PRISMA_AND_SCREENING_NOTES.md", "04_DEPARTURES.md",
                             "05_ADJUDICATION_LOG.md", "05_ADJUDICATION_OVERLAY.tsv",
                             "06_BACKWARD_CITATION_PASS1.md",
                             "07_PROTOCOL_AMENDMENTS_PROPOSED.md",
                             "08_REEXAMINATION_AND_REVISED_PRISMA.md"],
}

# My own build artifacts. Scratchpad is session-scoped and is not durable either.
BUILD = ["ARNI_v6_mitral-base_2026-08-12.html", "ARNI_manuscript.docx",
         "ARNI_HF_REVIEW_FULL.html", "citations.json", "linkcheck.json",
         "panels_out.json", "panels2_out.json", "readiness.json", "classify.json",
         "panels.R", "panels2.R", "make_docx.py"]
DETECT = ["guard2.py", "prose_guard.py", "selfaudit.py", "tier_detector.py",
          "pertab.py", "degrade_test.py", "object_to_cells.py", "ingest_evidence.py",
          "rob2_packet.py", "classify_gained.py", "ab_all.py", "readiness_scan.py"]

SKIP_DIRS = {"__pycache__", ".claude"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
manifest, missing, mismatched = [], [], []


def take(src, relgroup, name=None):
    name = name or os.path.basename(src)
    outdir = os.path.join(DEST, relgroup)
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, name)
    s1 = sha(src)
    shutil.copy2(src, dst)                       # copy2 preserves mtime
    s2 = sha(dst)
    if s1 != s2:
        mismatched.append((src, s1, s2))
    manifest.append({
        "group": relgroup, "file": name,
        "bytes": os.path.getsize(dst), "sha256": s2,
        "sha256_at_source": s1, "sha256_match": s1 == s2,
        "source_path": src,
        "source_mtime_utc": datetime.datetime.fromtimestamp(
            os.path.getmtime(src), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ingested_utc": now})


for lane, d in LANES.items():
    if not os.path.isdir(d):
        missing.append((lane, d, "LANE DIRECTORY ABSENT"))
        continue
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in sorted(files):
            src = os.path.join(root, f)
            rel = os.path.relpath(root, d)
            grp = lane if rel == "." else os.path.join(lane, rel)
            take(src, grp)
    for want in EXPECTED.get(lane, []):
        if not os.path.exists(os.path.join(d, want)):
            missing.append((lane, want, "NAMED IN THE ORDER BUT NOT FOUND AT SOURCE"))

for f in BUILD:
    p = os.path.join(SCRATCH, f)
    if os.path.exists(p):
        take(p, "build-artifacts")
    else:
        missing.append(("build-artifacts", f, "not present in scratchpad"))
for f in DETECT:
    p = os.path.join(SCRATCH, f)
    if os.path.exists(p):
        take(p, "detector-library")
    else:
        missing.append(("detector-library", f, "not present in scratchpad"))

os.makedirs(DEST, exist_ok=True)
json.dump({"ingested_utc": now, "files": len(manifest),
           "total_bytes": sum(m["bytes"] for m in manifest),
           "hash_mismatches": mismatched, "missing": missing,
           "manifest": manifest},
          open(os.path.join(DEST, "MANIFEST.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

print("ingested %d files, %s bytes" % (len(manifest), f"{sum(m['bytes'] for m in manifest):,}"))
print("hash mismatches (source vs destination):", len(mismatched))
by = {}
for m in manifest:
    by.setdefault(m["group"], []).append(m)
for g in sorted(by):
    print("  %-34s %3d files  %10s bytes" % (g, len(by[g]), f"{sum(x['bytes'] for x in by[g]):,}"))
print("\nMISSING / NOT FOUND:", len(missing))
for x in missing:
    print("   ", x)
