"""Complete the trial-identity sweep over the pages the first pass excluded.

MAHMOOD: finish the sweep across all 149.

The first pass excluded 19 pages by a CLASS_TOPICS regex, on the reasoning that a
dapagliflozin trial correctly shares no name with "SGLT2" and would flood the result with
false candidates. That reasoning holds for genuine class topics. The regex did not.

  `statin` matched PITAVASTATIN and ROSUVASTATIN -- two SPECIFIC DRUGS, excluded from a
  defect sweep because their names end in the class they belong to.

So the exclusion regex, written to prevent over-flagging, produced under-checking instead.
Both directions of the same error, in the same week, from the same instinct: a pattern
applied without asking what it actually matches. The corrected list is explicit membership,
not substring matching.

TWO QUESTIONS, NOT ONE. For a single-drug page the question is "does this trial study THIS
drug". For a class page it is "does this trial study a MEMBER of this class, and is that
member in the experimental arm". The second is a real question with real failure modes --
ACS_ANTIPLATELET pooling a trial whose antiplatelet is the comparator has the same
direction-of-effect hazard as any other comparator mismatch -- so class pages get their own
prompt rather than being waved through.

ARNI, SGLT2_HF and ACS_ANTIPLATELET are all in this batch. They are among the most looked-at
pages in the corpus and none of them has ever had its trial identities checked.
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
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\trialidentity_cls")
LEDGER = os.path.join(REPO, "outputs", "trial_identity_sweep_2026_08_25.jsonl")
WORKERS = 4

sys.path.insert(0, os.path.join(REPO, "scripts"))
import sweep_trial_identity_2026_08_25 as S

# EXPLICIT membership. Not a substring test -- that is what excluded pitavastatin.
CLASS_PAGES = {
    "ABLATION_AF_HEART_FAILURE_REVIEW.html": "catheter ablation for atrial fibrillation",
    "ABLATION_AF_MEDICAL_THERAPY_REVIEW.html": "catheter ablation versus medical therapy for AF",
    "ABLATION_AF_REVIEW.html": "catheter ablation for atrial fibrillation",
    "ACS_ANTIPLATELET_REVIEW.html": "oral P2Y12 antiplatelet agents in acute coronary syndrome",
    "ARNI_HF_REVIEW.html": "angiotensin receptor-neprilysin inhibition (sacubitril/valsartan) "
                           "in heart failure with reduced ejection fraction",
    "COVID19_VACCINES_REVIEW.html": "COVID-19 vaccines",
    "DOAC_AF_NMA_REVIEW.html": "direct oral anticoagulants in atrial fibrillation",
    "DOAC_AF_REVIEW.html": "direct oral anticoagulants in atrial fibrillation",
    "DOAC_CANCER_VTE_REVIEW.html": "direct oral anticoagulants for cancer-associated venous "
                                   "thromboembolism",
    "EARLY_RHYTHM_CONTROL_AF_REVIEW.html": "early rhythm-control therapy in atrial fibrillation",
    "INCRETIN_HFpEF_REVIEW.html": "incretin-based therapy (GLP-1 receptor agonists) in HFpEF",
    "INTENSIVE_BP_REVIEW.html": "intensive versus standard blood-pressure lowering",
    "PCSK9_INHIBITORS_CV_REVIEW.html": "PCSK9 inhibitors for cardiovascular outcomes",
    "PCSK9_LIPID_NMA_REVIEW.html": "PCSK9 inhibitors for lipid lowering",
    "SGLT2_CKD_REVIEW.html": "SGLT2 inhibitors in chronic kidney disease",
    "SGLT2_HF_REVIEW.html": "SGLT2 inhibitors in heart failure",
    "SGLT2_MACE_CVOT_REVIEW.html": "SGLT2 inhibitors for major adverse cardiovascular events",
}
# These two were excluded by a SUBSTRING match on "statin" and are single drugs.
SINGLE_DRUG_RESCUED = {
    "PITAVASTATIN_AUTO_FULL_REVIEW.html": "pitavastatin",
    "ROSUVASTATIN_AUTO_FULL_REVIEW.html": "rosuvastatin",
}

CLASS_PROMPT = """You are checking one thing about one systematic-review page: does every
trial it includes actually study the class of treatment the page is about?

THE PAGE IS ABOUT: %(subject)s

THE TRIALS IT INCLUDES:
%(trials)s

For EACH trial decide whether a member of that class is being STUDIED as an experimental
intervention in that trial.

This is a CLASS question, so a trial of any member counts -- a dapagliflozin trial IS an
SGLT2-inhibitor trial. But two distinctions still decide most cases:
- A class member in the CONTROL arm is not the subject of the trial. "X compared with
  ticagrelor" is a trial of X, not of ticagrelor, even though ticagrelor is in the class.
- A trial of a DIFFERENT class is a mismatch even if the page's class appears as background
  therapy that all participants receive.

Answer in EXACTLY this format and nothing else, one TRIAL block per trial:

TRIAL: <NCT id>
STUDIES_SUBJECT: <YES or NO or UNCLEAR>
ROLE: <EXPERIMENTAL or COMPARATOR or BACKGROUND or ABSENT or UNCLEAR>
WHY: <one sentence quoting the trial title>

Then one final block:

PAGE_VERDICT: <CLEAN if every trial studies the class, MISMATCH if any does not>
IF_MISMATCH: <REMATCH if correct trials for this class plausibly exist, NO_ELIGIBLE_TRIAL if
you believe none exists, or UNKNOWN>
"""


def one(args):
    page, subject, trials, is_class = args
    tmpl = CLASS_PROMPT if is_class else S.PROMPT
    prompt = tmpl % {"subject": subject, "trials": S.trials_block(trials)}
    body, attempts = _ask(prompt, page.replace(".html", ""))
    if body is None:
        return {"page": page, "status": "no output", "attempts": attempts,
                "batch": "class" if is_class else "single"}
    rec = {"page": page, "subject": subject, "attempts": attempts, "bytes": len(body),
           "status": "ok", "batch": "class" if is_class else "single"}
    pv = S._PV.search(body)
    rec["page_verdict"] = pv.group(1) if pv else None
    im = S._IM.search(body)
    rec["if_mismatch"] = im.group(1) if im else None
    rec["trials"] = [{"nct": m.group(1), "studies_subject": m.group(2), "role": m.group(3),
                      "why": " ".join(m.group(4).split())[:220]}
                     for m in S._TR.finditer(body)]
    if not rec["trials"] or rec["page_verdict"] is None:
        rec["status"] = "unparsed"
    return rec


def _ask(prompt, tag):
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


def main():
    os.makedirs(SESSION, exist_ok=True)
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    done = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("status") == "ok":
                    done.add(d["page"])
            except ValueError:
                pass

    jobs = []
    for page, subject in sorted(CLASS_PAGES.items()) + sorted(SINGLE_DRUG_RESCUED.items()):
        if page in done or page not in pmap:
            continue
        path = os.path.join(REPO, pmap[page])
        if not os.path.exists(path):
            continue
        o = json.load(io.open(path, encoding="utf-8"))
        trials = [t for t in ((o.get("inputs") or {}).get("trials") or [])
                  if isinstance(t, dict) and (t.get("label") or t.get("name"))]
        if not trials:
            continue
        jobs.append((page, subject, trials, page in CLASS_PAGES))

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("completion batch: %d pages (%d class, %d single-drug rescued from a substring "
        "match on 'statin')"
        % (len(jobs), sum(1 for j in jobs if j[3]), sum(1 for j in jobs if not j[3])))
    n = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for fut in cf.as_completed(futs):
            n += 1
            rec = fut.result()
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("[%2d/%d] %-44s %-9s %s"
                % (n, len(jobs), rec["page"][:42],
                   rec.get("page_verdict") or rec.get("status"),
                   rec.get("if_mismatch") or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
