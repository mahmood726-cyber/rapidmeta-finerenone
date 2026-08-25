"""ARNI against three published comparators, blind, both personas, both families.

MAHMOOD: "Run ARNI through the panel alongside the published comparators. If our own best
page scores like Zelniker, that's the achievable target for the manuscript layer and it
changes what we aim at."

That is the question. Round 1 put ARNI against one anchor once per persona and it beat it --
the editor sent ARNI to REVIEW and desk-rejected Zelniker. A single pairing against a single
anchor read by a single family is not a result you can aim a programme at. It is one draw.

SO: three published anchors, two personas, two families, both orderings. 24 jobs on one page.

  Zelniker, Lancet 2019   SGLT2i cardiovascular and renal outcomes in T2D
  Zannad,   Lancet 2020   SGLT2i in HFrEF -- EMPEROR-Reduced + DAPA-HF
  Tromp,    JACC HF 2021  network meta-analysis of HFrEF pharmacotherapy, includes ARNI

The last two are the harder test and were chosen for that: same disease as ARNI, same design
class, and Tromp is a network meta-analysis of 75 trials and 95,444 participants. If ARNI
holds up against those it is not holding up against a distant comparator.

BOTH ORDERINGS PER PAIRING, because position bias is real and round 1 alternated by page
index, which on a single page means ARNI always sat in the same slot for a given persona.
Here each pairing is run with ARNI as A and again as B, and a verdict that flips with
position is recorded as POSITION-DEPENDENT rather than counted for either side.
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
SESSION = os.path.join(SCRATCH, "arni_anchors")
LEDGER = os.path.join(REPO, "outputs", "arni_against_published_2026_08_25.jsonl")

ANCHORS = {
    "zelniker_lancet_2019": os.path.join(SCRATCH, "anchor_zelniker.txt"),
    "zannad_lancet_2020": os.path.join(SCRATCH, "anchor_zannad.txt"),
    "tromp_jaccHF_2021": os.path.join(SCRATCH, "anchor_tromp.txt"),
}

PAGE = "ARNI_HF_REVIEW.html"
WORKERS = 3

sys.path.insert(0, os.path.join(REPO, "scripts"))
import panel_the_corpus_2026_08_25 as P


def ask(family, prompt, tag):
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
    anchor_name, anchor_text, role, family, ours_is_a, ours = args
    a, b = (ours, anchor_text) if ours_is_a else (anchor_text, ours)
    prompt = P.PERSONAS[role] + P.TAIL % {"a": a, "b": b}
    tag = "%s__%s__%s__%s" % (anchor_name, role, family, "A" if ours_is_a else "B")
    body, attempts = ask(family, prompt, tag)
    rec = {"anchor": anchor_name, "role": role, "family": family,
           "ours_slot": "A" if ours_is_a else "B", "attempts": attempts}
    if body is None:
        rec["status"] = "no output"
        return rec
    m = _V.search(body)
    rec["bytes"] = len(body)
    if not m:
        rec["status"] = "unparsed"
        return rec
    av, bv, better = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    rec["status"] = "ok"
    rec["ours_verdict"] = av if ours_is_a else bv
    rec["anchor_verdict"] = bv if ours_is_a else av
    rec["better"] = ("ours" if better == ("A" if ours_is_a else "B")
                     else ("anchor" if better in ("A", "B") else "neither"))
    return rec


def main():
    os.makedirs(SESSION, exist_ok=True)
    ours = P.paper_text(os.path.join(REPO, PAGE))
    ok, why = P.payload_ok(ours)
    if not ok:
        print("REFUSED: the ARNI payload did not pass its checks (%s). No verdict is "
              "drawn on a document the reader would not have seen." % why)
        return 2
    print("ARNI paper panel: %d chars, %d words" % (len(ours), len(ours.split())))

    jobs = []
    for name, path in sorted(ANCHORS.items()):
        if not os.path.exists(path):
            print("REFUSED: anchor %s missing at %s" % (name, path))
            return 2
        text = io.open(path, encoding="utf-8").read().strip()
        for role in ("student", "editor"):
            for family in ("openai", "google"):
                for slot in (True, False):
                    jobs.append((name, text, role, family, slot, ours))

    done = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("status") == "ok":
                    done.add((d["anchor"], d["role"], d["family"], d["ours_slot"]))
            except ValueError:
                pass
    jobs = [j for j in jobs
            if (j[0], j[2], j[3], "A" if j[4] else "B") not in done]

    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("jobs: %d  (%d already done)" % (len(jobs), len(done)))
    n = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for fut in cf.as_completed(futs):
            n += 1
            rec = fut.result()
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("[%2d/%d] %-22s %-8s %-7s ours=%s  %s ours:%s anchor:%s"
                % (n, len(jobs), rec["anchor"][:20], rec["role"], rec["family"],
                   rec["ours_slot"], rec["status"],
                   rec.get("ours_verdict", "-"), rec.get("anchor_verdict", "-")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
