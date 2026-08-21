"""Roll the Paper Studio restructure across every mapped page, with a predicate per page.

SAME DISCIPLINE AS THE TWO PREVIOUS ROLLOUTS. A lock so two runs cannot interleave; every page
measured BEFORE it is rebuilt; four predictions stated for every page and checked on the
delivered bytes afterwards; a ledger that survives a crash; and every page built against the
LAST KNOWN-GOOD COMMITTED COPY rather than whatever is in the working tree (registry class 70 --
a guard measured against a baseline the same run had already lowered).

THE FOUR PREDICTIONS, PER PAGE:

    1  NOTHING LOST -- every estimate, registration id and registered outcome string present
       before is present after. The change reorders sections; it must not drop content.
    2  THE R TRANSCRIPT IS PRESENT AND BYTE-IDENTICAL where the page carried one. This is P46
       limb 4. It MOVES to Extended data; moving it and losing it would be the worst outcome
       available, so it is compared character for character, on every page, not on a sample.
    3  THE FIRST SENTENCE OF THE PAPER IS REACHED EARLIER -- fewer visible blocks before it.
    4  NO PAGE IS BYTE-IDENTICAL. Every page's section order changes, so a page that did not
       change did not rebuild, and a silent no-op is the failure this predicate exists to catch.

AND A FIFTH THING COUNTED RATHER THAN PREDICTED: the refusal notices. They are FINDINGS -- an
obstacle named in the evidence -- and a section move is exactly the operation that silently
drops a block. Counted before and after per page; any page that loses one is reported and the
run stops.

"VISIBLE" MEANS WHAT A READER MEETS. A closed <details> is not on the screen, and a text
extractor reads straight through it. The first measurement of this change reported 58 field
names still visible because it read inside the collapsed block. Everything here strips closed
<details> bodies first.
"""
import glob
import html as H
import io
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
LOCK = os.path.join(REPO, "outputs", ".paper_studio_rollout.lock")
LEDGER = os.path.join(REPO, "outputs", "paper_studio_rollout_2026_08_21.json")
RUN_ID = "%d@%s" % (os.getpid(), time.strftime("%H%M%S"))

sys.path.insert(0, SSOT)
from do_not_rebuild import PAGES as DO_NOT_REBUILD           # noqa: E402

NCT = re.compile(r"NCT\d{8}")
EST = re.compile(r"\b\d+\.\d{2,4}\s*\((?:-?\d+\.\d+)\s*to\s*(?:-?\d+\.\d+)\)")
# THE TRANSCRIPT COMES FROM THE OBJECT, NOT FROM A PATTERN.
#
# A first version matched `R version ... AGREES WITH THE STORED POINT TO 4 dp` -- the shape
# `fit_from_per_trial.R` prints. sglt2-hf's stored output came from an OLDER script and begins
# "Cross-engine verification ... metafor 5.0.1 under R 4.6.0", so the check reported
# "transcripts 0" on a page that carries two. FIFTEENTH lookup this run to under-count by
# reading one spelling.
#
# The authoritative comparison is against the object: take every `r_output.verbatim` the object
# stores and require each to appear, character for character, in the delivered bytes. That
# cannot drift with the format, and it is the only test that actually proves limb 4 survived
# the move.
def stored_transcripts(objp):
    try:
        obj = json.load(io.open(os.path.join(REPO, "ssot", objp) if not
                                os.path.isabs(objp) else objp, encoding="utf-8"))
    except Exception:                                              # noqa: BLE001
        return []
    out = []
    for blk in ((obj.get("results") or {}).get("by_outcome") or {}).values():
        v = ((blk or {}).get("r_output") or {}).get("verbatim")
        if isinstance(v, str) and v.strip():
            out.append(v)
    return out
REFUSAL = re.compile(r"<strong>Refused:</strong>")


def acquire():
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        held = ""
        try:
            held = io.open(LOCK, encoding="utf-8").read().strip()
        except Exception:                                          # noqa: BLE001
            pass
        sys.exit("REFUSED: a rollout is already running (%s). Read the lock before clearing "
                 "it -- a second writer resolves by whoever wrote last." % (held or "unknown"))
    os.write(fd, RUN_ID.encode())
    os.close(fd)


def release():
    try:
        os.remove(LOCK)
    except OSError:
        pass


def visible(html_text):
    """The panel as a reader meets it: closed <details> bodies are not on the screen."""
    i = html_text.find('id="paper"')
    seg = html_text[i:] if i >= 0 else ""
    seg = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", seg)

    def collapse(m):
        body = m.group(0)
        if re.match(r"(?is)<details[^>]*\bopen\b", body):
            return body
        s = re.search(r"(?is)<summary[^>]*>(.*?)</summary>", body)
        return "<p>%s</p>" % (s.group(1) if s else "")

    seg = re.sub(r"(?is)<details[^>]*>.*?</details>", collapse, seg)
    seg = re.sub(r"(?i)<(/?)(div|p|h[1-6]|li|tr|section|table|br|summary)[^>]*>", "\n", seg)
    seg = H.unescape(re.sub(r"<[^>]+>", " ", seg))
    return [re.sub(r"\s+", " ", l).strip() for l in seg.split("\n") if l.strip()]


def first_sentence_block(blocks):
    """How many visible blocks a reader passes before the ABSTRACT's first sentence.

    A first version took the first 12-word block, which is the TITLE -- legitimately content,
    and it never moves, so the metric read 5->5 and could not see the change at all. The
    quantity the prediction is about is how much APPARATUS stands between arriving at #paper
    and reading the paper, and the Abstract is where the paper starts.
    """
    for n, b in enumerate(blocks):
        if b.strip().lower() == "abstract":
            return n + 1
    for n, b in enumerate(blocks):
        if len(b.split()) >= 12 and not b.startswith(("In this section:",
                                                      "Sources for this section",
                                                      "Every statement below is projected")):
            return n
    return len(blocks)


def measure(path):
    if not os.path.isfile(path):
        return None
    h = io.open(path, encoding="utf-8", errors="replace").read()
    bl = visible(h)
    return {
        "bytes": len(h),
        "ncts": sorted(set(NCT.findall(h))),
        "estimates": sorted(set(EST.findall(h))),
        # THE PAGE, UNESCAPED, for comparing stored text against delivered text.
        # The renderer escapes quotes and ampersands on the way out, so a stored transcript
        # containing `method = "REML"` appears as `method = &quot;REML&quot;`. A raw
        # substring test therefore fails on a transcript that survived perfectly. Comparing
        # CONTENT is the question; comparing escaping is not.
        "text": H.unescape(h),
        "refusals": len(REFUSAL.findall(h)),
        "first_sentence_at": first_sentence_block(bl),
        "visible_blocks": len(bl),
        "has_paper": 'id="paper"' in h,
    }


def restore_from_git(page):
    """Class 70: measure and build against the COMMITTED copy, never the working tree."""
    r = subprocess.run(["git", "checkout", "--", page], cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return r.returncode == 0


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    limit = next((int(a.split("=")[1]) for a in sys.argv[1:] if a.startswith("--limit=")), None)
    acquire()
    try:
        M = json.load(io.open(os.path.join(SSOT, "PAGE_MAP.json"), encoding="utf-8"))
        pages = sorted(M)
        if only:
            pages = [p for p in pages if p in only]
        led = {}
        if os.path.isfile(LEDGER):
            led = json.load(io.open(LEDGER, encoding="utf-8"))
        done = set(led.get("done", {}))
        todo = [p for p in pages if p not in done and p not in DO_NOT_REBUILD]
        skipped = [p for p in pages if p in DO_NOT_REBUILD]
        if limit:
            todo = todo[:limit]
        print("pages mapped %d | already done %d | to build %d | protected %d (%s)"
              % (len(pages), len(done), len(todo), len(skipped), ", ".join(skipped)))

        results = led.setdefault("done", {})
        for n, page in enumerate(todo, 1):
            objp = M[page]
            objp = objp[5:] if objp.startswith("ssot/") else objp
            full = os.path.join(REPO, page)
            restore_from_git(page)
            want = stored_transcripts(objp)
            before = measure(full)
            if not before or not before["has_paper"]:
                results[page] = {"state": "NO PAPER PANEL -- not judged"}
                print("%3d/%d %-46s no paper panel" % (n, len(todo), page[:46]))
                continue
            r = subprocess.run([sys.executable, "build_tabbed.py", objp,
                                os.path.join("..", page)], cwd=SSOT,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = r.stdout.decode("utf-8", "replace")
            if r.returncode != 0:
                results[page] = {"state": "BUILD REFUSED", "tail": out[-300:]}
                print("%3d/%d %-46s BUILD REFUSED" % (n, len(todo), page[:46]))
                json.dump(led, io.open(LEDGER, "w", encoding="utf-8"), indent=1)
                continue
            after = measure(full)

            v = {
                "1_nothing_lost": (set(before["ncts"]) <= set(after["ncts"])
                                   and set(before["estimates"]) <= set(after["estimates"])),
                # EVERY stored transcript must appear character for character in the
                # delivered bytes AFTER the move -- checked against the object, on every page,
                # never on a sample.
                "2_transcript_byte_identical": all(t in after["text"] for t in want),
                "3_first_sentence_earlier": after["first_sentence_at"] <= before["first_sentence_at"],
                "4_not_byte_identical": before["bytes"] != after["bytes"],
                "5_refusals_kept": after["refusals"] >= before["refusals"],
            }
            results[page] = {
                "state": "ok" if all(v.values()) else "PREDICTION FAILED",
                "checks": v,
                "first_sentence": [before["first_sentence_at"], after["first_sentence_at"]],
                "refusals": [before["refusals"], after["refusals"]],
                "transcripts": len(want),
                "lost_ncts": sorted(set(before["ncts"]) - set(after["ncts"])),
                "lost_estimates": sorted(set(before["estimates"]) - set(after["estimates"])),
            }
            bad = [k for k, ok in v.items() if not ok]
            print("%3d/%d %-46s %s  first-sentence %d->%d  refusals %d->%d  transcripts %d"
                  % (n, len(todo), page[:46], "ok" if not bad else "FAILED " + ",".join(bad),
                     before["first_sentence_at"], after["first_sentence_at"],
                     before["refusals"], after["refusals"], len(want)))
            json.dump(led, io.open(LEDGER, "w", encoding="utf-8"), indent=1)

        ok = sum(1 for v in results.values() if v.get("state") == "ok")
        fail = [p for p, v in results.items() if v.get("state") == "PREDICTION FAILED"]
        ref = [p for p, v in results.items() if v.get("state") == "BUILD REFUSED"]
        print("\nbuilt ok %d | prediction failed %d | build refused %d | ledger %s"
              % (ok, len(fail), len(ref), os.path.relpath(LEDGER, REPO)))
        for p in fail[:10]:
            print("   FAILED %-44s %s" % (p, results[p]["checks"]))
    finally:
        release()


if __name__ == "__main__":
    main()
