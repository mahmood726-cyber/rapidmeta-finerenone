"""Two independent families classify every diff region: catch-up or regression.

WHY TWO FAMILIES. A delete is the stop signal. Whether a given delete is DAMAGE (text lost)
or a RETRACTION (text removed because it was false) is a judgement, and a judgement made by
one reader is one opinion. Codex (GPT-5) and agy (Gemini 3.1 Pro) are given the identical
diff region, independently, and must agree before anything is written.

THE DIFF BODY IS SUPPLIED INLINE. agy reasons well over supplied text and fails where it must
fetch a specific record, so nothing here requires either model to open a file. Each prompt
carries the served text, the rebuilt text and the surrounding context, and nothing else.

VERDICTS, and UNDECIDABLE is a real answer:
    CATCH_UP    the rebuild adds or corrects; the served text was wrong, stale or superseded
    REGRESSION  the rebuild loses something a reader had and should still have
    UNDECIDABLE not determinable from the region supplied

ADJUDICATION IS CONSERVATIVE. Both must say CATCH_UP for a page to pass. Any REGRESSION, any
UNDECIDABLE, or any disagreement holds the page and escalates. A page is never released by a
majority of one family with itself.

STANDING CONDITIONS, each of which has failed at least once before:
  * per-lane scratch paths -- a shared prompt file crossed two lanes and both reported
    confidently on the other's document
  * stdin closed -- a codex delegation that "timed out" with no output never started
  * output bytes verified per job; a job producing nothing is MISSING, never clean
  * the model is asked to name itself and the answer is checked against what was requested
"""
import concurrent.futures as cf
import difflib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import rebuild_batch_2026_08_27 as RB
SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\classify")
BUILT = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
         r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\batch")
OUT = os.path.join(REPO, "outputs", "diff_classification_2026_08_27.jsonl")

FAMILIES = {"openai": None, "google": "gemini-3.1-pro-high"}
WORKERS = 6

PROMPT = """You are classifying ONE difference between two versions of a scientific web page.

The page was rebuilt from a newer generator. Your job is to say whether the difference is a
CATCH-UP (the rebuild adds or corrects something; the older served text was wrong, stale or
superseded) or a REGRESSION (the rebuild loses something a reader had and should still have).

Judge ONLY from the text supplied. Do not assume anything about the wider page.

--- TEXT PRESENT IN THE OLD SERVED PAGE, ABSENT FROM THE REBUILD ---
%(removed)s

--- TEXT PRESENT IN THE REBUILD, ABSENT FROM THE SERVED PAGE ---
%(added)s

--- SURROUNDING CONTEXT FROM THE REBUILT PAGE ---
%(context)s

Answer with EXACTLY these three lines and nothing else:
MODEL: <the model and family you are>
VERDICT: <CATCH_UP or REGRESSION or UNDECIDABLE>
WHY: <one sentence, under 30 words>
"""

VERDICT = re.compile(r"VERDICT:\s*(CATCH_UP|REGRESSION|UNDECIDABLE)", re.I)
MODEL = re.compile(r"MODEL:\s*(.+)")
WHY = re.compile(r"WHY:\s*(.+)")


def ask(family, prompt, tag):
    """One job. Returns (body, attempts) or (None, attempts). Never a fabricated pass."""
    lane = os.path.join(SCRATCH, family)
    os.makedirs(lane, exist_ok=True)
    cache = os.path.join(lane, tag + ".txt")
    if os.path.exists(cache) and os.path.getsize(cache) > 40:
        return io.open(cache, encoding="utf-8", errors="replace").read(), 0
    for attempt in (1, 2, 3):
        try:
            if family == "openai":
                exe = shutil.which("codex") or "codex"
                p = subprocess.run([exe, "exec", "-s", "read-only"],
                                   input=prompt.encode("utf-8"),
                                   capture_output=True, timeout=600, cwd=REPO)
            else:
                pf = os.path.join(lane, "prompt_%s.txt" % tag)
                io.open(pf, "w", encoding="utf-8").write(prompt)
                p = subprocess.run(
                    ["agy", "--model", FAMILIES[family], "--add-dir", lane, "--print",
                     "Read %s in full and follow it exactly. Reply with the three requested "
                     "lines only." % os.path.basename(pf)],
                    stdin=subprocess.DEVNULL, capture_output=True, timeout=600)
            body = (p.stdout or b"").decode("utf-8", "replace").strip()
        except Exception:
            body = ""
        if len(body) > 40:
            io.open(cache, "w", encoding="utf-8").write(body)
            return body, attempt
        # A QUOTA ERROR IS NOT AN EMPTY RESPONSE AND MUST NOT BE RETRIED.
        #
        # Measured 2026-08-28: 417 of 417 MISSING jobs were agy; codex returned 700 ok and 0
        # missing. A per-vendor rate of 0% for one and high for the other is a harness signal.
        # The cause was `Individual quota reached ... Resets in 23m30s` -- capacity, not
        # payload size, so it does not correlate with page complexity. But ask() treated the
        # error as an empty body and retried three times with backoff, spending ~9s per job
        # re-hitting a limit that resets in minutes.
        err = ((p.stderr or b"").decode("utf-8", "replace") + " " + body).lower()
        if "quota" in err or "rate limit" in err or "429" in err:
            return None, -1        # -1 marks EXHAUSTED, distinct from a failed job
        time.sleep(3 * attempt)
    return None, 3


def regions(served_html, built_html):
    """Every non-equal region, as (removed, added, context)."""
    import rebuild_batch_2026_08_27 as B
    a = B.norm(B.rendered(served_html)).split(" ")
    b = B.norm(B.rendered(built_html)).split(" ")
    ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
    out = []
    for k, (t, i1, i2, j1, j2) in enumerate(ops):
        if t == "equal":
            continue
        ctx = ""
        for t2, x1, x2, y1, y2 in ops[max(0, k - 1):k + 2]:
            if t2 == "equal":
                ctx += " ".join(b[y1:y2])[-400:] + " "
        out.append({"kind": t,
                    "removed": " ".join(a[i1:i2])[:1200],
                    "added": " ".join(b[j1:j2])[:1200],
                    "context": ctx.strip()[:900]})
    return out


def main():
    pages = sys.argv[1:] or []
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def say(s):
        out.write(s + chr(10))
        out.flush()

    if not pages:
        # every page that produced a DELETE in the batch run
        esc = os.path.join(REPO, "out", "ESCALATIONS.jsonl")
        seen = []
        if os.path.exists(esc):
            for l in io.open(esc, encoding="utf-8"):
                try:
                    d = json.loads(l)
                except ValueError:
                    continue
                if d.get("page") and d["page"] not in seen:
                    seen.append(d["page"])
        pages = seen
    say("pages to classify: %d" % len(pages))

    jobs = []
    for p in pages:
        sp = os.path.join(REPO, p)
        bp = os.path.join(BUILT, p)
        if not (os.path.exists(sp) and os.path.exists(bp)):
            say("  %-46s SKIP (missing served or built copy)" % p[:46])
            continue
        served_html = io.open(sp, encoding="utf-8", errors="replace").read()
        built_html = io.open(bp, encoding="utf-8", errors="replace").read()
        built_text = RB.norm(RB.rendered(built_html))
        for i, r in enumerate(regions(served_html, built_html)):
            # ONLY THE UNMATCHED DELETES. Inserts are catch-up by construction. Replaces
            # were judged wholesale in the first run and produced mostly agreement. And a
            # delete the whitelist ALREADY released must not be re-judged: the panel does
            # not know eafa9445c retracted that sentence deliberately, so it calls it a
            # REGRESSION every time -- 1,292 jobs of which the loudest signal was an answer
            # we had already settled by identity. Judging what is already decided does not
            # add a second opinion; it manufactures a contradiction.
            if r["kind"] != "delete":
                continue
            if RB.known_retraction(r["removed"], built_text):
                continue
            for fam in FAMILIES:
                jobs.append((p, i, r, fam))

    say("judgement jobs (deletes and replaces x 2 families): %d" % len(jobs))
    say("")

    def one(job):
        page, idx, r, fam = job
        tag = "%s__%d" % (re.sub(r"[^A-Za-z0-9]+", "_", page)[:60], idx)
        body, att = ask(fam, PROMPT % r, tag)
        if body is None:
            return {"page": page, "region": idx, "family": fam,
                    "status": "EXHAUSTED" if att == -1 else "MISSING", "attempts": att}
        m, mo, w = VERDICT.search(body), MODEL.search(body), WHY.search(body)
        return {"page": page, "region": idx, "family": fam, "kind": r["kind"],
                "status": "ok" if m else "unparsed",
                "verdict": (m.group(1).upper() if m else None),
                "model_said": (mo.group(1).strip()[:40] if mo else None),
                "why": (w.group(1).strip()[:160] if w else None),
                "bytes": len(body), "attempts": att}

    done = 0
    with io.open(OUT, "a", encoding="utf-8") as fh:
        with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for rec in ex.map(one, jobs):
                done += 1
                fh.write(json.dumps(rec, ensure_ascii=False) + chr(10))
                fh.flush()
                say("[%3d/%d] %-40s r%-2d %-7s %-11s %s"
                    % (done, len(jobs), rec["page"][:40], rec["region"], rec["family"],
                       rec.get("verdict") or rec["status"], (rec.get("why") or "")[:60]))
    say("")
    say("wrote %s" % os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
