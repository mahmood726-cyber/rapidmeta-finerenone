"""Four independent families on the same pages: does a panel verdict survive more readers?

THE QUESTION, and it is a question about every panel number this project has reported:

  We have been running two families and calling the monoculture a known weakness. If four
  families disagree MORE than two did, then our confidence in every panel result so far is
  overstated -- and it is better to know that than to keep quoting the numbers.

FOUR DISTINCT FAMILIES, each proved live by an exec that named itself:

  openai        codex exec            Codex GPT-5
  google        agy gemini-3.1-pro-high    Gemini 3.1 Pro
  anthropic     agy claude-opus-4-6-thinking   Claude Opus 4.6
  open-weights  agy gpt-oss-120b-medium    GPT-OSS 120B

The last two come from a pool that has never been used. Per-invocation `--model` selection
works -- verified, and contrary to a standing note that said it does not -- so all four run
concurrently from one machine without touching settings.json.

WHAT IS MEASURED, and it is agreement, not quality:

  * per (page, role), how many of the four agree on the verdict
  * unanimous / 3-1 / 2-2 splits
  * pairwise agreement for each family pair, so a single odd family is visible
  * whether the TWO-family agreement we reported (83%) holds up as four

A SAMPLE, NOT THE CORPUS. 25 pages, chosen as a stratified spread across page length so the
result is not dominated by short notes. Stated as a sample everywhere.

STANDING CONDITIONS, and they matter more at this volume: output bytes verified per job,
per-lane scratch paths so no two lanes share a prompt file, three attempts then MISSING, and
a job that produces nothing is never counted as a verdict.
"""
# collinearity-checked: all four families read every (page, role). No exclusion rule is
# applied, so role, family and page vary independently and each is identified. This is the
# only panel design in the repo that can separate role from family, and it satisfies that
# by accident rather than by choice -- see 'every rater sees every item' in the handover.

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
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\panel4")
LEDGER = os.path.join(REPO, "outputs", "panel_four_families_2026_08_25.jsonl")
ANCHOR = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
          r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\anchor_zelniker.txt")

WORKERS = 6
N_PAGES = 25

FAMILIES = {
    "openai": None,                                  # codex
    "google": "gemini-3.1-pro-high",
    "anthropic": "claude-opus-4-6-thinking",
    "open_weights": "gpt-oss-120b-medium",
}

sys.path.insert(0, os.path.join(REPO, "scripts"))
import panel_the_corpus_2026_08_25 as P

_V = re.compile(r"A_VERDICT:\s*([A-Z\- ]+).*?B_VERDICT:\s*([A-Z\- ]+).*?BETTER:\s*([AB]|NEITHER)",
                re.S)


def ask(family, prompt, tag):
    lane = os.path.join(SCRATCH, family)
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
                pf = os.path.join(lane, "prompt_%s.txt" % tag)
                io.open(pf, "w", encoding="utf-8").write(prompt)
                p = subprocess.run(
                    ["agy", "--model", FAMILIES[family], "--add-dir", lane, "--print",
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


def one(args):
    idx, page, role, family, anchor = args
    txt = P.paper_text(os.path.join(REPO, page))
    ok, why = P.payload_ok(txt)
    if not ok:
        return {"page": page, "role": role, "family": family,
                "status": "payload refused: " + why}
    ours_is_a = (idx % 2 == 0)
    a, b = (txt, anchor) if ours_is_a else (anchor, txt)
    prompt = P.PERSONAS[role] + P.TAIL % {"a": a, "b": b}
    tag = "%s__%s" % (page.replace(".html", ""), role)
    body, attempts = ask(family, prompt, tag)
    if body is None:
        return {"page": page, "role": role, "family": family, "status": "no output",
                "attempts": attempts}
    m = _V.search(body)
    rec = {"page": page, "role": role, "family": family, "attempts": attempts,
           "ours": "A" if ours_is_a else "B", "bytes": len(body), "status": "ok"}
    if m:
        av, bv = m.group(1).strip(), m.group(2).strip()
        rec["ours_verdict"] = av if ours_is_a else bv
        rec["anchor_verdict"] = bv if ours_is_a else av
    else:
        rec["status"] = "unparsed"
    return rec


def sample_pages():
    """25 pages spread across LENGTH, so short notes do not dominate."""
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    sized = []
    for page in sorted(pmap):
        p = os.path.join(REPO, page)
        if not os.path.exists(p):
            continue
        t = P.paper_text(p)
        if t:
            sized.append((len(t), page))
    sized.sort()
    if not sized:
        return []
    step = max(1, len(sized) // N_PAGES)
    return [pg for _n, pg in sized[::step]][:N_PAGES]


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    anchor = io.open(ANCHOR, encoding="utf-8").read().strip()
    pages = sample_pages()
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
            for r in ("student", "editor") for f in FAMILIES
            if (p, r, f) not in done]

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("pages sampled (length-stratified): %d" % len(pages))
    log("families: %s" % ", ".join(sorted(FAMILIES)))
    log("jobs: %d  (%d already done)  workers=%d" % (len(jobs), len(done), WORKERS))
    n = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for fut in cf.as_completed(futs):
            n += 1
            rec = fut.result()
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("[%4d/%d] %-40s %-8s %-13s %s %s"
                % (n, len(jobs), rec["page"][:38], rec["role"], rec["family"],
                   rec.get("status"), rec.get("ours_verdict", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
