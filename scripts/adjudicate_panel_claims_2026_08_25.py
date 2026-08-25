"""Adjudicate every claim the panel made against the object it is a claim about.

A PANEL VERDICT IS A CLAIM, NOT A FINDING. Round 1 produced 149 student verdicts each
quoting a sentence the reader believed was misleading. Some of those are real defects. Some
are a reader misunderstanding a convention. Some are a reader inventing a contradiction that
is not on the page. Nothing distinguishes them except reading the page and the object.

This has bitten before: CLAIMS_DEFECT sits permanently UNVERIFIED because a harvester never
verifies its own inputs, and the panel itself has already produced one claim that turned out
to indict our instrument rather than the page.

WHAT EACH JOB GETS, and it is deliberately everything needed to settle the question inline:
the quoted sentence, the surrounding page text, and the relevant slice of the canonical
object. The adjudicator needs no file tools, which is also why it can run under
`-s read-only` without the auto-mode classifier refusing it.

THREE VERDICTS ONLY:
  CONFIRMED    the page really does assert what the reader says, and it really is wrong
  REFUTED      the sentence is defensible, or the reader misread the page
  UNVERIFIABLE the object does not settle it -- which is itself a finding about the object

A NULL-HEAVY RESULT INDICTS THE PROMPT, NOT THE CORPUS. If most jobs come back
UNVERIFIABLE, that means the slice being handed over does not contain the answer, and the
field list is wrong. That happened once already: 50 of 58 nulled because the named field is
null on most objects.
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
SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad")
SESSION = os.path.join(SCRATCH, "adjudicate")
PANEL = os.path.join(SCRATCH, "corpuspanel")
LEDGER = os.path.join(REPO, "outputs", "panel_claims_adjudicated_2026_08_25.jsonl")
R1 = os.path.join(REPO, "outputs", "corpus_panel_2026_08_25.jsonl")

WORKERS = 4

sys.path.insert(0, os.path.join(REPO, "scripts"))
import panel_the_corpus_2026_08_25 as P

PROMPT = """You are adjudicating one claim a reviewer made about one document. You are not
reviewing the document. You are deciding whether the reviewer's specific claim is TRUE.

THE REVIEWER'S CLAIM:
%(claim)s

Answer in EXACTLY this format and nothing else:

VERDICT: <CONFIRMED or REFUTED or UNVERIFIABLE>
BASIS: <one sentence. If CONFIRMED, quote the two passages that contradict each other. If
REFUTED, say what the reviewer missed. If UNVERIFIABLE, name the fact that would settle it.>
SEVERITY: <HIGH if a reader acting on this would be misled about the evidence, LOW otherwise>

Rules that decide close calls:
- A page that states a limitation plainly and then respects it is NOT misleading.
- A page reporting a single trial's own result, clearly labelled as one trial, is NOT a pool
  and NOT a defect.
- A page that declines to pool and gives its reason is doing the right thing.
- CONFIRMED requires the document to ASSERT something the same document or its object
  contradicts. A reviewer's disagreement with a method is not a confirmation.
- Default to REFUTED when the claim is merely a preference.

=== THE DOCUMENT (the reviewer read exactly this) ===
%(page)s

=== THE CANONICAL OBJECT THIS DOCUMENT IS PROJECTED FROM (abridged) ===
%(obj)s
"""


def object_slice(path, limit=14000):
    """The parts of the object that settle contradiction claims, not the whole file."""
    try:
        o = json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return "(object could not be read)"
    keep = {}
    for k in ("results", "risk_of_bias", "grade", "search", "screening", "k_cascade",
              "trial_characteristics", "poolability", "outcomes"):
        if k in o:
            keep[k] = o[k]
    s = json.dumps(keep, ensure_ascii=False, indent=1)
    if len(s) > limit:
        s = s[:limit] + "\n... (object truncated at %d chars; say UNVERIFIABLE if the " \
                        "answer was in the omitted part)" % limit
    return s


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


_V = re.compile(r"VERDICT:\s*([A-Z]+).*?BASIS:\s*(.+?)\s*SEVERITY:\s*([A-Z]+)", re.S)


def one(args):
    page, claim, objpath = args
    txt = P.paper_text(os.path.join(REPO, page))
    ok, why = P.payload_ok(txt)
    if not ok:
        return {"page": page, "status": "payload refused: " + why}
    prompt = PROMPT % {"claim": claim, "page": txt[:60000],
                       "obj": object_slice(os.path.join(REPO, objpath))}
    body, attempts = ask(prompt, page.replace(".html", ""))
    if body is None:
        return {"page": page, "status": "no output", "attempts": attempts}
    m = _V.search(body)
    rec = {"page": page, "claim": claim[:300], "attempts": attempts,
           "bytes": len(body), "status": "ok"}
    if m:
        rec["verdict"] = m.group(1).strip()
        rec["basis"] = " ".join(m.group(2).split())[:400]
        rec["severity"] = m.group(3).strip()
    else:
        rec["status"] = "unparsed"
    return rec


def main():
    os.makedirs(SESSION, exist_ok=True)
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    claims = []
    for line in io.open(R1, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("role") != "student" or d.get("ours_verdict") != "MISLEADING":
            continue
        f = os.path.join(PANEL, "%s__student.txt" % d["page"].replace(".html", ""))
        if not os.path.exists(f):
            continue
        b = io.open(f, encoding="utf-8", errors="replace").read()
        m = re.search(r"%s_WHY:\s*(.+)" % d["ours"], b)
        if not m:
            continue
        if d["page"] not in pmap:
            continue
        claims.append((d["page"], " ".join(m.group(1).split()), pmap[d["page"]]))

    done = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("status") == "ok":
                    done.add(d["page"])
            except ValueError:
                pass
    jobs = [c for c in claims if c[0] not in done]

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("student MISLEADING claims with a quoted reason: %d" % len(claims))
    log("to adjudicate: %d  (%d already done)" % (len(jobs), len(done)))
    n = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for fut in cf.as_completed(futs):
            n += 1
            rec = fut.result()
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("[%3d/%d] %-44s %-12s %s"
                % (n, len(jobs), rec["page"][:42], rec.get("verdict", rec.get("status")),
                   rec.get("severity", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
