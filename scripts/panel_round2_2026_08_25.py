"""Panel round 2: re-read the pages that changed, with BOTH families on every job.

THREE DAYS TO THE 28th. Round 1 read all 149 pages once, each job going to one family.
That leaves two questions it cannot answer, and this round is built to answer both.

  (1) DID TODAY'S FIXES MOVE A READER? Fifteen pages carried an agreement statistic in the
      abstract for a pool they did not present; the projector now suppresses it. Round 1 read
      those pages BEFORE the fix -- five of the twenty worst were flagged for exactly that
      sentence. If the verdicts do not move, the fix did not matter to a reader and we should
      know that rather than assume it.

  (2) IS THE PANEL A MONOCULTURE? Round 1 alternated families by index, so no page was read
      twice by different families on the same question. A verdict from one family is one
      opinion. This round sends EVERY (page, role) to Codex (GPT-5) AND to agy (Gemini 3.1
      Pro) and records both, so cross-family agreement is measured rather than assumed. Where
      the two families disagree, neither verdict is reported as the page's verdict.

THE PAGES: the union of the 37 both-personas-negative pages from round 1 and the 15 the i2
fix touched. Those are the pages where movement is possible; re-reading a page nothing
changed on would spend a job to confirm a number we already have.

EVERY STANDING CONDITION APPLIES, and at this volume each has already failed once:
  * output bytes verified per job; a job producing nothing is MISSING, never clean
  * per-lane scratch paths -- a shared /tmp/msg.txt crossed two lanes and corrupted both
  * payloads verified before any verdict is drawn
  * resumable: a completed (page, role, family) is never re-run
"""
# collinearity-checked: every (page, role) goes to BOTH families, so family is crossed
# with role rather than confounded with it. Role and family are separately identified.
# Contrast round 1, where family = (openai, google)[(idx + role_offset) % 2] made student
# and editor on the same page ALWAYS different families -- balanced in aggregate, and every
# page-level role comparison simultaneously a family comparison.

import concurrent.futures as cf
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
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad")
SESSION = os.path.join(SCRATCH, "panel_r2")
LEDGER = os.path.join(REPO, "outputs", "corpus_panel_round2_2026_08_25.jsonl")
R1 = os.path.join(REPO, "outputs", "corpus_panel_2026_08_25.jsonl")
ANCHOR = os.path.join(SCRATCH, "anchor_zelniker.txt")

WORKERS = 4

sys.path.insert(0, os.path.join(REPO, "scripts"))
import panel_the_corpus_2026_08_25 as R1MOD          # personas, extraction, payload checks


def i2_fixed_pages():
    """The pages the projector fix touched, read from the recorded measurement."""
    p = os.path.join(REPO, "outputs", "pooled_claim_without_pool_2026_08_25.json")
    # That file now records ZERO -- it is the post-fix state. The pre-fix population is in
    # the commit message and in CORPUS_PANEL. Re-derive it from git rather than trusting a
    # remembered list: the pages that carried the sentence at the pre-fix commit.
    import audit_pooled_claim_without_pool_2026_08_25 as A
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    out = []
    for page in sorted(pmap):
        r = subprocess.run(["git", "show", "%s:%s" % (A.PRE_FIX, page)],
                           capture_output=True, cwd=REPO)
        if r.returncode:
            continue
        if A.examine(r.stdout.decode("utf-8", "replace"))[0]:
            out.append(page)
    return out


def both_negative_pages():
    import collections
    pages = collections.defaultdict(dict)
    for line in io.open(R1, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("ours_verdict"):
            pages[d["page"]][d["role"]] = d["ours_verdict"]
    return [p for p, v in pages.items()
            if v.get("student") == "MISLEADING" and v.get("editor") == "DESK-REJECT"]


def ask(family, prompt, tag):
    """Run one job. Returns (body, attempts) or (None, attempts) -- never a fabricated pass."""
    lane = os.path.join(SESSION, family)
    os.makedirs(lane, exist_ok=True)
    out = os.path.join(lane, "%s.txt" % tag)
    if os.path.exists(out) and os.path.getsize(out) > 120:
        return io.open(out, encoding="utf-8", errors="replace").read(), 0
    for attempt in (1, 2, 3):
        try:
            if family == "openai":
                exe = shutil.which("codex") or "codex"
                p = subprocess.run([exe, "exec", "-s", "read-only"],
                                   input=prompt.encode("utf-8"),
                                   capture_output=True, timeout=900, cwd=REPO)
            else:
                # PER-LANE prompt file. A shared path let two lanes overwrite each other and
                # both reported confidently on the other's document.
                pf = os.path.join(lane, "prompt_%s.txt" % tag)
                io.open(pf, "w", encoding="utf-8").write(prompt)
                p = subprocess.run(
                    ["agy", "--add-dir", lane, "--print",
                     "Read %s in full and follow it exactly. Reply with the requested "
                     "fields only." % os.path.basename(pf)],
                    stdin=subprocess.DEVNULL, capture_output=True, timeout=900)
            body = (p.stdout or b"").decode("utf-8", "replace").strip()
        except Exception:
            body = ""
        if len(body) > 120:
            io.open(out, "w", encoding="utf-8").write(body)
            return body, attempt
        time.sleep(3)
    return None, 3


_V = re.compile(r"A_VERDICT:\s*([A-Z\- ]+).*?B_VERDICT:\s*([A-Z\- ]+).*?BETTER:\s*([AB]|NEITHER)",
                re.S)


def one(args):
    idx, page, role, family, anchor = args
    txt = R1MOD.paper_text(os.path.join(REPO, page))
    ok, why = R1MOD.payload_ok(txt)
    if not ok:
        return {"page": page, "role": role, "family": family,
                "status": "payload refused: " + why}
    ours_is_a = (idx % 2 == 0)
    a, b = (txt, anchor) if ours_is_a else (anchor, txt)
    prompt = R1MOD.PERSONAS[role] + R1MOD.TAIL % {"a": a, "b": b}
    tag = "%s__%s" % (page.replace(".html", ""), role)
    body, attempts = ask(family, prompt, tag)
    if body is None:
        return {"page": page, "role": role, "family": family, "status": "no output",
                "attempts": attempts}
    m = _V.search(body)
    rec = {"page": page, "role": role, "family": family,
           "ours": "A" if ours_is_a else "B", "attempts": attempts,
           "bytes": len(body), "status": "ok"}
    if m:
        av, bv, better = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        rec["ours_verdict"] = av if ours_is_a else bv
        rec["anchor_verdict"] = bv if ours_is_a else av
        rec["better"] = ("ours" if better == ("A" if ours_is_a else "B")
                         else ("anchor" if better in ("A", "B") else "neither"))
    else:
        rec["status"] = "unparsed"
    return rec


def main():
    os.makedirs(SESSION, exist_ok=True)
    anchor = io.open(ANCHOR, encoding="utf-8").read().strip()
    neg = both_negative_pages()
    fixed = i2_fixed_pages()
    pages = sorted(set(neg) | set(fixed))
    pages = [p for p in pages if os.path.exists(os.path.join(REPO, p))]

    done = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("status") == "ok":
                    done.add((d["page"], d["role"], d["family"]))
            except ValueError:
                pass

    jobs = [(i, p, r, f, anchor) for i, p in enumerate(pages)
            for r in ("student", "editor") for f in ("openai", "google")
            if (p, r, f) not in done]

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("pages: %d  (%d both-negative, %d i2-fixed, %d in both)"
        % (len(pages), len(neg), len(fixed), len(set(neg) & set(fixed))))
    log("jobs: %d  (%d already done)  workers=%d" % (len(jobs), len(done), WORKERS))
    n = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for fut in cf.as_completed(futs):
            n += 1
            rec = fut.result()
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("[%4d/%d] %-42s %-8s %-7s %s %s"
                % (n, len(jobs), rec["page"][:40], rec["role"], rec["family"],
                   rec.get("status"), rec.get("ours_verdict", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
