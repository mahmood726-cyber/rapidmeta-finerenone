"""Sweep the trial-identity class by asking a model, because a token match provably cannot.

WHY THIS IS NOT A REGEX. A first version compared the page's drug tokens against each trial's
official title, arms and registered conditions. It FAILED ITS OWN POSITIVE CONTROL on the one
case we already know is real, and refused to print a count -- which is the control working.

The reason is worth keeping. CEFEPIME_TAZ is about cefepime-TAZOBACTAM. Its wrongly-matched
trial is titled "...Ceftazidime And Avibactam Compared With Cefepime...", so the token
"cefepime" IS present -- as the COMPARATOR. Deciding this case needs two judgements a token
match cannot make:

  * a COMBINATION drug is not its components. cefepime-tazobactam is not cefepime, and
    cefepime/VNRX-5133 (taniborbactam) is a different combination again.
  * an intervention in the EXPERIMENTAL arm is not the same as one in the CONTROL arm.

Both are ordinary clinical-pharmacology reasoning and neither is string matching, so the
sweep delegates per page and keeps the local detector only as the thing that proved a regex
could not do it.

THE CORRECT TRIAL FOR CEFEPIME_TAZ EXISTS: NCT03630081, WCK 4282 (FEP-TAZ), Wockhardt,
cefepime-tazobactam versus meropenem in complicated UTI, n=1004. So that page is a MATCHING
failure, not an absence of evidence. Each job is told to distinguish those two outcomes,
because they call for opposite fixes: re-match, or withdraw the claim that trials were found.

EVIDENCE INLINE. Each job carries the page's subject, every trial's official title, arms and
registered conditions. No file tools, so it runs under -s read-only.
"""
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
SESSION = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\trialidentity")
LEDGER = os.path.join(REPO, "outputs", "trial_identity_sweep_2026_08_25.jsonl")
WORKERS = 4

# Class/procedure topics: a dapagliflozin trial correctly shares no name with "SGLT2".
# Excluded because the question "does this trial study the subject" has a different and
# much looser answer for a class, and mixing the two would drown the real cases.
CLASS_TOPICS = re.compile(
    r"sglt2|doac|pcsk9|arni|nma|antiplatelet|anticoagul|ablation|statin|incretin|"
    r"dapt|rhythm|intensive_bp|umbrella|vaccines", re.I)

PROMPT = """You are checking one thing about one systematic-review page: does every trial it
includes actually study the drug the page is about?

THE PAGE IS ABOUT: %(subject)s

THE TRIALS IT INCLUDES:
%(trials)s

For EACH trial decide whether the page's subject drug is being STUDIED as an experimental
intervention in that trial.

Two distinctions decide almost every case:
- A COMBINATION is not its components. Cefepime-tazobactam is not cefepime; cefepime/VNRX-5133
  (taniborbactam) is a different combination again. A trial of one is not a trial of another.
- A drug in the CONTROL arm is not the subject of the trial. "X compared with Y" is a trial of
  X, not of Y.
- Code names count as the drug: WCK 4282 IS cefepime-tazobactam, AAI101 IS enmetazobactam.

Answer in EXACTLY this format and nothing else, one TRIAL block per trial:

TRIAL: <NCT id>
STUDIES_SUBJECT: <YES or NO or UNCLEAR>
ROLE: <EXPERIMENTAL or COMPARATOR or ABSENT or UNCLEAR>
WHY: <one sentence quoting the trial title>

Then one final block:

PAGE_VERDICT: <CLEAN if every trial studies the subject, MISMATCH if any does not>
IF_MISMATCH: <one of REMATCH if you believe correct trials for this subject plausibly exist,
or NO_ELIGIBLE_TRIAL if you believe no trial of this subject exists, or UNKNOWN>
"""


def trials_block(trials):
    out = []
    for t in trials:
        if not isinstance(t, dict):
            continue
        nct = t.get("nct") or t.get("trial_id") or "?"
        title = str(t.get("label") or t.get("name") or "").strip()
        arms = t.get("arms")
        conds = t.get("registered_conditions")
        out.append("NCT: %s\n  official title: %s\n  arms: %s\n  registered conditions: %s"
                   % (nct, title[:400] or "(not recorded)",
                      str(arms)[:300] if arms else "(not recorded)",
                      str(conds)[:200] if conds else "(not recorded)"))
    return "\n\n".join(out)


def ask(prompt, tag):
    os.makedirs(SESSION, exist_ok=True)
    out = os.path.join(SESSION, "%s.txt" % tag)
    if os.path.exists(out) and os.path.getsize(out) > 80:
        return io.open(out, encoding="utf-8", errors="replace").read(), 0
    exe = shutil.which("codex") or "codex"
    for attempt in (1, 2, 3):
        try:
            p = subprocess.run([exe, "exec", "-s", "read-only"],
                               input=prompt.encode("utf-8"),
                               capture_output=True, timeout=900, cwd=REPO)
            body = (p.stdout or b"").decode("utf-8", "replace").strip()
        except Exception:
            body = ""
        if len(body) > 80:
            io.open(out, "w", encoding="utf-8").write(body)
            return body, attempt
        time.sleep(3)
    return None, 3


_PV = re.compile(r"PAGE_VERDICT:\s*([A-Z_]+)")
_IM = re.compile(r"IF_MISMATCH:\s*([A-Z_]+)")
_TR = re.compile(r"TRIAL:\s*(\S+)\s*STUDIES_SUBJECT:\s*([A-Z]+)\s*ROLE:\s*([A-Z]+)\s*"
                 r"WHY:\s*(.+?)(?=\nTRIAL:|\nPAGE_VERDICT:|$)", re.S)


def one(args):
    page, subject, trials = args
    prompt = PROMPT % {"subject": subject, "trials": trials_block(trials)}
    body, attempts = ask(prompt, page.replace(".html", ""))
    if body is None:
        return {"page": page, "status": "no output", "attempts": attempts}
    rec = {"page": page, "subject": subject, "attempts": attempts,
           "bytes": len(body), "status": "ok"}
    pv = _PV.search(body)
    rec["page_verdict"] = pv.group(1) if pv else None
    im = _IM.search(body)
    rec["if_mismatch"] = im.group(1) if im else None
    rec["trials"] = [{"nct": m.group(1), "studies_subject": m.group(2),
                      "role": m.group(3), "why": " ".join(m.group(4).split())[:220]}
                     for m in _TR.finditer(body)]
    if not rec["trials"] or rec["page_verdict"] is None:
        rec["status"] = "unparsed"
    return rec


def main():
    os.makedirs(SESSION, exist_ok=True)
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    jobs, skipped = [], 0
    for page in sorted(pmap):
        path = os.path.join(REPO, pmap[page])
        if not os.path.exists(path):
            continue
        if CLASS_TOPICS.search(page):
            skipped += 1
            continue
        try:
            o = json.load(io.open(path, encoding="utf-8"))
        except Exception:
            continue
        trials = [t for t in ((o.get("inputs") or {}).get("trials") or [])
                  if isinstance(t, dict) and (t.get("label") or t.get("name"))]
        if not trials:
            continue
        subject = str(o.get("title") or o.get("question") or page).strip()[:200]
        jobs.append((page, subject, trials))

    done = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("status") == "ok":
                    done.add(d["page"])
            except ValueError:
                pass
    jobs = [j for j in jobs if j[0] not in done]

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("pages with named trials to check: %d  (%d class/procedure topics skipped, "
        "%d already done)" % (len(jobs), skipped, len(done)))
    n = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for fut in cf.as_completed(futs):
            n += 1
            rec = fut.result()
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("[%3d/%d] %-44s %-9s %s"
                % (n, len(jobs), rec["page"][:42],
                   rec.get("page_verdict") or rec.get("status"),
                   rec.get("if_mismatch") or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
