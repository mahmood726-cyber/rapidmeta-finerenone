"""Panel all 149 Paper Studio pages, blind, against a published comparator.

DEADLINE THE 28th. 145 of 149 pages have never been read by anyone; that is now the largest
gap in the project, larger than any remaining defect class. Sampling four more pages will not
close it. This reads all of them.

WHAT IS BEING MEASURED, and it is a DISTRIBUTION, not a verdict per page:

    how many pages would MISLEAD a medical student who has to check and rewrite them
    how many pages would an EDITOR desk-reject, and for what
    does the 3-2 shape hold across the corpus, or is SGLT2_HF unusually good

Two personas per page, chosen because they answer those two questions and disagree with each
other by construction -- the student rewards disclosure and the editor punishes it. A page
both accept is genuinely clean; a page both reject is genuinely bad; the gap between them is
the finding this corpus keeps producing.

EVERY JOB CARRIES THE COMPARATOR. Each persona sees two documents, A and B, one of them
Zelniker (Lancet 2019), and is not told which is which. Order alternates by page index. A
verdict without a comparator is a mood; with one, a bad verdict on our page beside a good
verdict on a published paper is evidence, and a bad verdict on both indicts the instrument.

AT THIS VOLUME SILENT FAILURE IS CERTAIN UNLESS CHECKED. `codex exec` intermittently fails to
receive its prompt and exits 0 having produced nothing. Across ~300 jobs that will happen
repeatedly. Every job is verified for output bytes and retried; a job that never produces
output is recorded as MISSING, never as a verdict, and never as a clean page.

PAYLOADS ARE VERIFIED BEFORE ANY VERDICT IS DRAWN. Truncated text, leaked markup and flattened
disclosures have each produced confident findings about documents no reader sees.
"""
import concurrent.futures as cf
import html as H
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
           r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\corpuspanel")
LEDGER = os.path.join(REPO, "outputs", "corpus_panel_2026_08_25.jsonl")
ANCHOR = (r"F:\claude-temp\claude\F--rapidmeta-finerenone"
          r"\e2e2a1d5-c19e-44de-90ab-690dbc5235a1\scratchpad\anchor_zelniker.txt")

WORKERS = 4

PERSONAS = {
    "student": """You are a MEDICAL STUDENT, bright but unfamiliar with this clinical field
and new to evidence synthesis. You have been asked to check one of these documents and
rewrite it into a publishable review.

THE ONLY QUESTION: could you improve it WITHOUT BEING MISLED BY IT?

A confident sentence written over missing data is the worst thing you can find, because you
would not question it and it would survive your edit. Quote any you see.""",

    "editor": """You are the EDITOR of a clinical journal deciding what happens to a
submission today.

THE ONLY QUESTION: SEND FOR PEER REVIEW, or DESK-REJECT? Editors desk-reject for an unclear
question, an unsound method, no advance, or unreadability -- say which applies.""",
}

TAIL = """
You are shown TWO documents, A and B. One may be a published paper and one may not. You are
not told which and should not assume. Judge BOTH on the same terms.

Answer in EXACTLY this format and nothing else:

A_VERDICT: <one of: MISLEADING / SAFE>   (student)   or   <DESK-REJECT / REVIEW>   (editor)
A_WHY: <one sentence, quoting the document>
B_VERDICT: <same scale>
B_WHY: <one sentence, quoting the document>
BETTER: <A or B or NEITHER>
SEPARATOR: <one sentence on what separates them>

=== DOCUMENT A ===
%(a)s

=== DOCUMENT B ===
%(b)s
"""

_PAPER = re.compile(r'id="pn-paper"(.*?)(?:id="pn-[a-z]|<!--\s*end-paper)', re.S)


def paper_text(path):
    h = io.open(path, encoding="utf-8", errors="replace").read()
    m = _PAPER.search(h)
    if not m:
        return None
    seg = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", m.group(1))
    # A DISCLOSURE REACHES THE REVIEWER AS A DISCLOSURE. Flattening one handed a persona a
    # document no reader sees, and it desk-rejected the page for content behind a click.
    seg = re.sub(
        r"(?is)<details[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>",
        lambda md: "\n[%s -- collapsed on the page, %d entries behind a disclosure]\n"
                   % (" ".join(re.sub(r"<[^>]+>", " ", md.group(1)).split()),
                      len(re.findall(r"<li\b", md.group(2)))), seg)
    seg = re.sub(r"(?i)<h([1-6])[^>]*>", "\n\n## ", seg)
    seg = re.sub(r"(?i)<(p|tr|li|div)\b[^>]*>", "\n", seg)
    txt = H.unescape(re.sub(r"<[^>]+>", " ", seg))
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", txt)).strip()


def payload_ok(txt):
    if not txt or len(txt.split()) < 120:
        return False, "too short"
    if re.search(r"<[a-z/][^>]*>", txt):
        return False, "markup survived"
    if 'id="' in txt or "pn-paper" in txt:
        return False, "element id leaked"
    if "&#x27;" in txt or "&quot;" in txt:
        return False, "entities not unescaped"
    return True, "ok"


def ask(family, prompt, tag):
    out = os.path.join(SESSION, "%s.txt" % tag)
    for attempt in (1, 2, 3):
        try:
            if family == "openai":
                exe = shutil.which("codex") or "codex"
                p = subprocess.run([exe, "exec", "-s", "read-only"],
                                   input=prompt.encode("utf-8"),
                                   capture_output=True, timeout=900, cwd=REPO)
            else:
                pf = os.path.join(SESSION, "prompt_%s.txt" % tag)
                io.open(pf, "w", encoding="utf-8").write(prompt)
                p = subprocess.run(
                    ["agy", "--add-dir", SESSION, "--print",
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
    idx, page, role, anchor = args
    txt = paper_text(os.path.join(REPO, page))
    ok, why = payload_ok(txt)
    if not ok:
        return {"page": page, "role": role, "status": "payload refused: " + why}
    ours_is_a = (idx % 2 == 0)
    a, b = (txt, anchor) if ours_is_a else (anchor, txt)
    family = ("openai", "google")[(idx + (0 if role == "student" else 1)) % 2]
    prompt = PERSONAS[role] + TAIL % {"a": a, "b": b}
    tag = "%s__%s" % (page.replace(".html", ""), role)
    body, attempts = ask(family, prompt, tag)
    if body is None:
        return {"page": page, "role": role, "family": family, "status": "no output",
                "attempts": attempts}
    m = _V.search(body)
    rec = {"page": page, "role": role, "family": family, "ours": "A" if ours_is_a else "B",
           "attempts": attempts, "bytes": len(body), "status": "ok"}
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
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"), encoding="utf-8"))
    pages = [p for p in sorted(pmap)
             if os.path.exists(os.path.join(REPO, p)) and paper_text(os.path.join(REPO, p))]
    done = set()
    if os.path.exists(LEDGER):
        for line in io.open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(line)
                if d.get("status") == "ok":
                    done.add((d["page"], d["role"]))
            except ValueError:
                pass

    jobs = [(i, p, r, anchor) for i, p in enumerate(pages)
            for r in ("student", "editor") if (p, r) not in done]
    raw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                           write_through=True)

    def log(s):
        raw.write(s + "\n")
        raw.flush()

    log("pages with a Paper tab: %d | jobs to run: %d (%d already done)"
        % (len(pages), len(jobs), len(done)))
    n = 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for fut in cf.as_completed(futs):
            n += 1
            rec = fut.result()
            with io.open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log("[%4d/%d] %-46s %-8s %s %s"
                % (n, len(jobs), rec["page"][:44], rec["role"], rec.get("status"),
                   rec.get("ours_verdict", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
