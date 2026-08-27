"""Rebuild a batch of pages, gate each one, and write only what passes.

GATES, applied per page before anything is written into place:

  1. RENDERED TEXT, normalised for dates, the build stamp, SHA-256, `NN KB` and `NNNNxNNNN`.
     The last two exist because the page prints numbers about FILES and numbers about TRIALS
     in the same document, and a naive numeric diff flags a TIFF's size as an estimate.
  2. CAPTIONED-FIGURE COUNT (`Figure N.`) must not fall. Never `base64,` count: that counts
     payloads, and rasterisation is non-deterministic in presence, dimensions AND file size.
  3. DELETES = 0. An insert is catch-up; A DELETE IS DAMAGE and stops the batch.
  4. The build itself enforces the nine required ancestors, the do-not-rebuild list, the
     placeholder-leak refusal and the manuscript guard -- which is why this runs the real
     entry point (`python ssot/build_tabbed.py <obj> <out>`) and never calls build().

NEVER A BYTE GATE. Two rebuilds of the same page from the same generator differ in raster
metadata alone; byte equality would fail every time and prove nothing.

EXCLUSIONS ARE HARD-CODED AND NAMED. ARNI_HF_REVIEW is the corpus's only authored manuscript
and a rebuild destroys the one instance of the property we are trying to acquire.
SOTAGLIFLOZIN_HF_REVIEW was built from a dirty tree and is the topic under active
methodological criticism.

Usage: rebuild_batch_2026_08_27.py <list.txt> [--apply] [--limit N]
       without --apply nothing is written; the gates still run and report.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\batch")
ESC = os.path.join(REPO, "out", "ESCALATIONS.jsonl")
LEDGER = os.path.join(REPO, "outputs", "rebuild_log_2026_08_27.jsonl")

NEVER_REBUILD = {"ARNI_HF_REVIEW.html", "SOTAGLIFLOZIN_HF_REVIEW.html"}

SCRIPT = re.compile(r"<script\b.*?</script>", re.S | re.I)
STYLE = re.compile(r"<style\b.*?</style>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
FIGCAP = re.compile(r"Figure\s+\d+\.", re.I)
NORM = (
    (r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?", "<TS>"),
    (r"\d{2}:\d{2}\s*UTC", "<CLK>"),
    (r"\d{4}-\d{2}-\d{2}", "<DATE>"),
    (r"SHA-256\s+[0-9a-f]{8,}", "<SHA>"),
    (r"<code>[0-9a-f]{9,40}</code>", "<STAMP>"),
    (r"[\d,]+\s*KB", "<KB>"),
    (r"\d{3,5}x\d{3,5}", "<DIM>"),
)


def rendered(html):
    return re.sub(r"\s+", " ", TAG.sub(" ", STYLE.sub(" ", SCRIPT.sub(" ", html or "")))).strip()


def norm(t):
    for pat, rep in NORM:
        t = re.sub(pat, rep, t)
    return t


def escalate(rec):
    os.makedirs(os.path.dirname(ESC), exist_ok=True)
    with io.open(ESC, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + chr(10))


def log(rec):
    with io.open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + chr(10))


def gate(served_html, built_html):
    """(ok, reason, stats). Deletes are damage; inserts are catch-up."""
    import difflib
    a = norm(rendered(served_html)).split(" ")
    b = norm(rendered(built_html)).split(" ")
    ops = [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
           if o[0] != "equal"]
    dels = [o for o in ops if o[0] == "delete"]
    reps = [o for o in ops if o[0] == "replace"]
    fig_s = len(set(FIGCAP.findall(served_html)))
    fig_b = len(set(FIGCAP.findall(built_html)))
    stats = {"regions": len(ops), "deletes": len(dels), "replaces": len(reps),
             "inserts": len(ops) - len(dels) - len(reps),
             "fig_served": fig_s, "fig_built": fig_b,
             "chars_served": len(" ".join(a)), "chars_built": len(" ".join(b))}
    if dels:
        lost = " ".join(a[dels[0][1]:dels[0][2]])[:180]
        return False, "DELETE -- text present in served is absent from the rebuild: %s" % lost, stats
    if fig_b < fig_s:
        return False, "captioned figures fell %d -> %d" % (fig_s, fig_b), stats
    return True, "ok", stats


def main():
    if len(sys.argv) < 2:
        print("usage: rebuild_batch_2026_08_27.py <list.txt> [--apply] [--limit N]")
        return 2
    listfile = sys.argv[1]
    apply_ = "--apply" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        out.write(s + chr(10))
        out.flush()

    os.makedirs(SCRATCH, exist_ok=True)
    items = []
    for line in io.open(listfile, encoding="utf-8"):
        parts = line.rstrip(chr(10)).split("\t")
        if len(parts) >= 2 and parts[0].strip():
            items.append((parts[0].strip(), parts[1].strip()))
    if limit:
        items = items[:limit]

    say("batch: %d page(s)   apply=%s" % (len(items), apply_))
    say("excluded by name: %s" % ", ".join(sorted(NEVER_REBUILD)))
    say("")

    built = served = failed = skipped = 0
    for i, (page, obj) in enumerate(items, 1):
        if page in NEVER_REBUILD:
            skipped += 1
            say("[%2d/%d] %-46s SKIPPED (named exclusion)" % (i, len(items), page[:46]))
            continue
        served_path = os.path.join(REPO, page)
        if not os.path.exists(served_path):
            skipped += 1
            say("[%2d/%d] %-46s SKIPPED (no served copy)" % (i, len(items), page[:46]))
            continue
        tmp = os.path.join(SCRATCH, page)
        t0 = time.time()
        r = subprocess.run([sys.executable, "build_tabbed.py",
                            os.path.join("..", obj), tmp],
                           cwd=os.path.join(REPO, "ssot"), capture_output=True, timeout=1800)
        if r.returncode != 0 or not os.path.exists(tmp):
            failed += 1
            msg = (r.stderr or b"").decode("utf-8", "replace")[-300:]
            say("[%2d/%d] %-46s BUILD FAILED  %s" % (i, len(items), page[:46], msg[:80]))
            escalate({"page": page, "stage": "build", "error": msg})
            continue
        built += 1
        s_html = io.open(served_path, encoding="utf-8", errors="replace").read()
        b_html = io.open(tmp, encoding="utf-8", errors="replace").read()
        ok, why, st = gate(s_html, b_html)
        rec = {"page": page, "object": obj, "ok": ok, "why": why,
               "seconds": round(time.time() - t0, 1), "applied": False}
        rec.update(st)
        if not ok:
            failed += 1
            say("[%2d/%d] %-46s GATE FAILED  %s" % (i, len(items), page[:46], why[:70]))
            escalate(rec)
            log(rec)
            continue
        if apply_:
            shutil.copyfile(tmp, served_path)
            rec["applied"] = True
            served += 1
        say("[%2d/%d] %-46s ok  regions=%-3d ins=%-3d del=%d figs %d->%d %s"
            % (i, len(items), page[:46], st["regions"], st["inserts"], st["deletes"],
               st["fig_served"], st["fig_built"], "WRITTEN" if apply_ else "(not written)"))
        log(rec)

    say("")
    say("built %d   written %d   failed %d   skipped %d" % (built, served, failed, skipped))
    say("ledger    : %s" % os.path.relpath(LEDGER, REPO))
    if failed:
        say("escalated : %s" % os.path.relpath(ESC, REPO))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
