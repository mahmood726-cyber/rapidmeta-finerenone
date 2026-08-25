"""Screen the same records with THREE independent model families, blind, and measure agreement.

MAHMOOD: duplicate screening is 2 of 156 by Cochrane's definition, but two model families
plus a third adjudicating IS duplicate independent screening by a different route -- and that
is a substitution we can demonstrate rather than concede.

The demonstration needs data, and there is almost none: of 20 objects carrying a
`duplicate_screening` block, EIGHTEEN record `performed: false`. Only two were ever run. So
this generates the missing data rather than reporting the absence again.

THREE FAMILIES, NOT TWO, because the agy Claude and GPT-OSS pools had never been touched:

    anthropic     claude-opus-4-6-thinking
    open_weights  gpt-oss-120b-medium
    google        gemini-3.1-pro-high

Three is materially better than two for this purpose. With two seats a disagreement tells you
only THAT they differ; with three, a 2-1 split identifies which seat is the outlier, and a
3-way split says the QUESTION is unclear rather than the readers. The existing ABLATION_AF
record shows why that matters: adjudication there found the question itself defective for 20
of 25 hard contradictions, which two seats could never have distinguished from reader error.

BLIND, AND BLIND IN THE WAY THAT COUNTS. Each seat gets the same records and the same
criteria, is not told another seat exists, and never sees another seat's answers. Prompts are
written to per-family lane directories so no two lanes can read each other's file -- a shared
prompt path has crossed two lanes in this project before and both reported confidently on the
other's document.

WHAT IS REPORTED: per topic, records read by all three, three-way agreement, 2-1 splits, and
the pairwise rate for each family pair. Vocabulary is deliberately coarse -- INCLUDE / EXCLUDE
/ UNCLEAR -- because a finer vocabulary lowers the agreement rate by measuring its own
granularity rather than the readers', which is recorded as P34 on the existing objects.
"""
import concurrent.futures as cf
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\triscreen")
LEDGER = os.path.join(REPO, "outputs", "triplicate_screening_2026_08_25.jsonl")

FAMILIES = {"anthropic": "claude-opus-4-6-thinking",
            "open_weights": "gpt-oss-120b-medium",
            "google": "gemini-3.1-pro-high"}
WORKERS = 6
BATCH = 12               # records per job, so one bad response costs 12 rather than 72

PROMPT = """You are screening trial registrations for a systematic review. Decide, for each
record, whether it is eligible.

THE REVIEW'S QUESTION: %(question)s

ELIGIBILITY CRITERIA, as recorded by the review:
%(criteria)s

Answer with ONE LINE PER RECORD and nothing else, in this exact form:

<NCT id> | <INCLUDE or EXCLUDE or UNCLEAR> | <at most 12 words of reason>

Use UNCLEAR only when the record genuinely does not say enough to decide. It is a real answer,
not a way to avoid one.

RECORDS:
%(records)s
"""

_LINE = re.compile(r"(NCT\d{8})\s*\|\s*(INCLUDE|EXCLUDE|UNCLEAR)\s*\|\s*(.{0,120})", re.I)


def ask(family, prompt, tag):
    lane = os.path.join(SCRATCH, family)
    os.makedirs(lane, exist_ok=True)
    out = os.path.join(lane, "%s.txt" % tag)
    if os.path.exists(out) and os.path.getsize(out) > 60:
        return io.open(out, encoding="utf-8", errors="replace").read(), 0
    pf = os.path.join(lane, "prompt_%s.txt" % tag)
    io.open(pf, "w", encoding="utf-8").write(prompt)
    for attempt in (1, 2, 3):
        try:
            p = subprocess.run(
                ["agy", "--model", FAMILIES[family], "--add-dir", lane, "--print",
                 "Read %s in full and follow it exactly. Reply with the requested lines only."
                 % os.path.basename(pf)],
                stdin=subprocess.DEVNULL, capture_output=True, timeout=900)
            body = (p.stdout or b"").decode("utf-8", "replace").strip()
        except Exception:
            body = ""
        if len(body) > 60:
            io.open(out, "w", encoding="utf-8").write(body)
            return body, attempt
        time.sleep(3)
    return None, 3


def topics():
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    out = []
    for page, rel in sorted(pmap.items()):
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        o = json.load(io.open(path, encoding="utf-8"))
        sc = o.get("screening") or {}
        recs = sc.get("records")
        if not isinstance(recs, list) or len(recs) < 5:
            continue
        items = []
        for r in recs:
            if not isinstance(r, dict):
                continue
            nct = r.get("nct") or r.get("trial_id")
            if not nct:
                continue
            bits = [str(r.get(k)) for k in ("title", "label", "status", "primaryPurpose",
                                            "condition", "intervention") if r.get(k)]
            items.append((nct, " | ".join(bits)[:300] or "(registration fields not stored)"))
        if len(items) >= 5:
            out.append({"page": page,
                        "question": str(o.get("question") or o.get("title") or page)[:300],
                        "criteria": json.dumps(sc.get("eligibility"))[:900],
                        "records": items})
    return out


def one(args):
    page, question, criteria, chunk, family, idx = args
    body, attempts = ask(family, PROMPT % {
        "question": question, "criteria": criteria,
        "records": "\n".join("%s | %s" % (n, t) for n, t in chunk)}, "%s__%02d" % (page.replace(".html", ""), idx))
    rec = {"page": page, "family": family, "batch": idx, "attempts": attempts,
           "n_sent": len(chunk)}
    if body is None:
        rec["status"] = "no output"
        return rec
    got = {m.group(1).upper(): m.group(2).upper() for m in _LINE.finditer(body)}
    rec["status"] = "ok" if got else "unparsed"
    rec["verdicts"] = got
    rec["n_parsed"] = len(got)
    return rec


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    ts = topics()
    done = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("status") == "ok":
                    done.add((d["page"], d["family"], d["batch"]))
            except ValueError:
                pass
    jobs = []
    for t in ts:
        chunks = [t["records"][i:i + BATCH] for i in range(0, len(t["records"]), BATCH)]
        for i, c in enumerate(chunks):
            for f in FAMILIES:
                if (t["page"], f, i) not in done:
                    jobs.append((t["page"], t["question"], t["criteria"], c, f, i))

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("topics with a screenable record set: %d" % len(ts))
    log("records total: %d" % sum(len(t["records"]) for t in ts))
    log("jobs: %d across %d families  (%d already done)"
        % (len(jobs), len(FAMILIES), len(done)))
    n = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for fut in cf.as_completed(futs):
            n += 1
            rec = fut.result()
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("[%4d/%d] %-42s %-13s b%-2d %s %s/%s"
                % (n, len(jobs), rec["page"][:40], rec["family"], rec["batch"],
                   rec["status"], rec.get("n_parsed", 0), rec["n_sent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
