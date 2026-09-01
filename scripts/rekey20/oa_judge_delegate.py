# -*- coding: utf-8 -*-
"""DELEGATED ADJUDICATION. A lane that did not write the matcher judges its output.

⛔⛔ WHY THIS EXISTS AND IT IS NOT ONLY THROUGHPUT. I built `axis_match.py` and I was the
sole labeller of its output -- recorded as a real weakness in `REPORT-OA-LANE.md` §5, and
this project's own standing lesson says the labeller should not be the classifier's author.
Codex is a different lab (GPT-5, liveness confirmed by a real exec that named its family),
so its verdicts are decorrelated from mine in a way a second pass by me can never be.

⭐ THE SCOPE IS CHOSEN SO IT CANNOT BE PADDING. The headline metric is TOPICS WITH >=1 JUDGED
COUNTERPART. Only topics currently at ZERO can change it, so only those are sent. Sending
more pairs from topics that already have a counterpart would raise the PAIR count and move
the headline not at all -- which is the shape of padding.

⛔ EVIDENCE INLINE, NO FILE TOOLS. The full title and abstract of every row travel in the
prompt. Codex's sandbox blocks sockets and a delegation that needs to fetch anything fails
for a reason that has nothing to do with the judgement.

⭐ KNOWN-ANSWER CONTROLS, EXPECTED PRINTED BESIDE OBSERVED. Two pairs I already judged and
whose answers are recorded in `oa_judgements.json` are injected into every slice:
  POSITIVE  PMC10328856 for etripamil-psvt          -> COUNTERPART
  NEGATIVE  PMC11424296 for riociguat-pah           -> NOT_COUNTERPART (a procedure, not a drug)
⚠️ Both sides are required. A judge that returns COUNTERPART for everything passes the
positive control alone, and over-calling is the failure mode that matters when the question
is "does this topic have one at all".

⛔ AND THE VERDICTS ARE GATED THE SAME WAY MINE WERE. Every returned label must quote a span
literally present in the row's own title+abstract -- `gate_label_vs_reason.check`, the same
gate my 33 judgements passed. A foreign lane's output is not trusted more than my own.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                              line_buffering=True)
from gate_label_vs_reason import check                                  # noqa: E402

PAGED = "../../evidence/2026-08-31-axis/oa_paged_twenty.json"
MINE = "../../evidence/2026-08-31-axis/oa_judgements.json"
OUT = "../../evidence/2026-08-31-axis/oa_judgements_delegated.json"
SCRATCH = "F:/claude-temp/claude/F--rapidmeta-ssot-shell/delegate"


def _resolve_codex():
    """The Windows-resolvable entry point, or None. NEVER a bare 'codex'."""
    import shutil
    for cand in ("codex.cmd", "codex.exe", "codex"):
        p = shutil.which(cand)
        if p and not p.endswith(("/codex", "\\codex")):
            return p
    return shutil.which("codex.cmd") or None


CODEX_EXE = _resolve_codex()

RUBRIC = """You are adjudicating whether a systematic review is a COUNTERPART to a topic.

THE RULE, applied exactly:
- COUNTERPART: the review's UNIT OF WORK is the topic's drug, or a coherent CLASS containing
  it, AND the review's POPULATION is the topic's condition.
- A NARROWER OUTCOME SET does not disqualify. A DIFFERENT CONSTRUCT does (a harm signal, a
  different disease, a dose-vs-dose comparison, a head-to-head against another active drug).
- A LANDSCAPE review ("eighteen targeted drugs", "all medications for X") is NOT a class
  review and is NOT a counterpart.
- UNDECIDABLE_BY_RULE only if the text genuinely does not say.

OUTPUT: a JSON array, one object per pair, nothing else. No prose before or after.
Each object:
{"pair_id": "<given>", "label": "COUNTERPART" | "NOT_COUNTERPART" | "UNDECIDABLE_BY_RULE",
 "reason": "<one sentence>",
 "quotes_intervention": ["<exact span copied from the record>"],
 "quotes_condition": ["<exact span copied from the record>"],
 "quotes_disqualifying": ["<exact span copied from the record>"]}

QUOTES MUST BE COPIED VERBATIM from the record's title or abstract. A quote that is not
literally present is rejected automatically.
- COUNTERPART requires quotes_intervention AND quotes_condition.
- NOT_COUNTERPART requires quotes_disqualifying, and the reason must state a ground of
  difference (use the word "not", "different", or "rather than").
"""

CONTROLS = [
    {"pair_id": "__control_pos", "expect": "COUNTERPART",
     "app_id": "etripamil-psvt", "oa_id": "PMC10328856"},
    {"pair_id": "__control_neg", "expect": "NOT_COUNTERPART",
     "app_id": "riociguat-pah", "oa_id": "PMC11424296"},
]


def build_pairs(paged, only_zero_topics):
    """Verified pairs for topics that could still change the headline."""
    pairs = []
    for t in paged["topics"]:
        if t["app_id"] not in only_zero_topics:
            continue
        for r in ((t.get("verified") or {}).get("rows") or []):
            pairs.append({"pair_id": "%s::%s" % (t["app_id"], r["oa_id"]),
                          "app_id": t["app_id"], "oa_id": r["oa_id"],
                          "topic_intervention": ", ".join(t["intervention_terms"][:6]),
                          "topic_condition": ", ".join(t["condition_terms"]),
                          "record_title": r["title"],
                          "record_abstract": (r["objectives_verbatim"] or "")[:1100]})
    return pairs


def slice_prompt(pairs, control_rows):
    body = {"pairs": control_rows + pairs}
    return RUBRIC + "\n\nPAIRS:\n" + json.dumps(body, ensure_ascii=False, indent=1)


def run_codex(prompt_path, timeout):
    # ⛔ stdin CLOSED. A codex delegation that inherits an open stdin hangs and is then
    # reported as a timeout with no output -- recorded, and it looks exactly like a dead
    # lane. ⛔ NOT text=True: the records carry non-ASCII and cp1252 would mangle or raise.
    # ⛔⛔ THE PROMPT GOES BY FILE REFERENCE, NEVER IN argv. `codex.cmd` is a BATCH FILE and
    # cmd.exe caps a command line at 8191 characters; a 15 KB prompt was SILENTLY TRUNCATED
    # to the rubric alone, so Codex received the instructions and ZERO pairs and replied
    # "Send me the topic and the systematic review details". The harness recorded that as
    # UNPARSEABLE on every slice -- 0 of 16 -- which reads exactly like "the model cannot
    # follow a JSON instruction".
    #
    # ⇒ SAME DEFECT CLASS AS THE 100-ROW CAP, NOW IN MY OWN DELEGATION: the evidence was a
    # WINDOW (here, an empty one) and the judge was asked about a population. It was caught
    # ONLY because the raw output was kept on failure -- a harness that stores just the
    # verdict cannot tell a model that refused from a prompt that never arrived.
    prompt = ("Read the file %s and follow the instructions in it exactly. "
              "Output ONLY the JSON array, no prose." % prompt_path.replace("\\", "/"))
    # ⛔ `codex` ON WINDOWS IS AN npm BASH SHIM, NOT AN EXECUTABLE. `command -v codex` finds
    # it and Python's CreateProcess does not: WinError 2, "cannot find the file specified".
    # Swallowing that exception would have produced "Codex returned nothing" -- a wrong
    # belief about a tool, which this project has already paid for twice. The resolver is
    # explicit and its result is asserted before any slice is sent.
    exe = CODEX_EXE
    p = subprocess.run([exe, "exec", "--skip-git-repo-check", prompt],
                       capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout)
    return p.stdout.decode("utf-8", "replace"), p.returncode


def main():
    import concurrent.futures as cf

    paged = json.load(io.open(PAGED, encoding="utf-8"))
    byid = {t["app_id"]: t for t in paged["topics"]}

    # ⭐ THE TEN TOPICS THAT CARRY NO COUNTERPART TODAY. Only these can move the headline.
    ZERO = ["apixaban-af-review", "apixaban-vte-prophylaxis", "dabigatran-af",
            "dabigatran-stroke", "evolocumab-ascvd-auto2",
            "evolocumab-dyslipidemia-review",
            "evolocumab-mixed-dyslipidemia-auto-full-review", "olmesartan-htn",
            "pitavastatin-auto-full-review", "warfarin-af"]
    CAP = 25          # pairs examined per topic, DECLARED BEFORE THE RUN
    CHUNK = 8         # pairs per codex call, so the prompt stays under the
                      # command-line limit

    os.makedirs(SCRATCH, exist_ok=True)
    ctrl_rows = []
    for c in CONTROLS:
        t = byid[c["app_id"]]
        row = next(r for r in (t["verified"] or {})["rows"] if r["oa_id"] == c["oa_id"])
        ctrl_rows.append({"pair_id": c["pair_id"], "app_id": c["app_id"],
                          "oa_id": c["oa_id"],
                          "topic_intervention": ", ".join(t["intervention_terms"][:6]),
                          "topic_condition": ", ".join(t["condition_terms"]),
                          "record_title": row["title"],
                          "record_abstract": (row["objectives_verbatim"] or "")[:1100]})

    # ⛔ THE RUNNER IS PROVEN BEFORE ANY SLICE IS SENT. A delegation whose executable does
    # not resolve returns nothing and reads as "the model produced nothing" -- a wrong
    # belief about a tool. This asserts the exe exists AND that a real exec comes back with
    # model tokens, which a version string or a login check cannot show.
    print("=== RUNNER LIVENESS, PROVEN BY A REAL EXEC ===")
    if not CODEX_EXE:
        print("   REFUSING: no Windows-resolvable codex entry point. NOTHING SENT.")
        sys.exit(1)
    print("   exe: %s" % CODEX_EXE)
    probe = subprocess.run([CODEX_EXE, "exec", "--skip-git-repo-check",
                            "Reply with exactly: ALIVE"],
                           capture_output=True, stdin=subprocess.DEVNULL, timeout=180)
    ptxt = probe.stdout.decode("utf-8", "replace")
    if "ALIVE" not in ptxt:
        print("   REFUSING: the probe did not come back. NOTHING SENT.")
        print(ptxt[-600:])
        sys.exit(1)
    print("   probe returned ALIVE  (rc=%d)" % probe.returncode)
    print("")

    print("=== SCOPE, DECLARED BEFORE THE RUN ===")
    print("   topics sent          : the %d with NO counterpart today" % len(ZERO))
    print("   pairs per topic      : first %d by oa_id sort -- an ARBITRARY declared order," % CAP)
    print("                          not relevance, so a slice cannot be cherry-picked")
    print("   ⛔ a topic with no counterpart in its slice is reported as a LOWER BOUND")
    print("")

    slices, skipped = [], []
    for app in ZERO:
        t = byid.get(app)
        rows = sorted(((t.get("verified") or {}).get("rows") or []),
                      key=lambda r: r["oa_id"]) if t else []
        if not rows:
            skipped.append((app, t["state"] if t else "MISSING"))
            continue
        pairs = build_pairs({"topics": [dict(t, verified={"rows": rows[:CAP]})]}, {app})
        # ⚠️ CHUNKED. A Windows command line caps near 32 KB; 25 records of abstract text
        # exceeds it, and a prompt truncated by the SHELL would be judged as if it were the
        # whole record -- a silent corruption of the evidence, not a visible failure.
        for ci, k in enumerate(range(0, len(pairs), CHUNK)):
            slices.append((app, len(rows), pairs[k:k + CHUNK], ci))

    print("   %-46s %8s %8s %7s" % ("app_id", "verified", "sent", "slices"))
    agg = {}
    for app, total, pairs, _ci in slices:
        agg.setdefault(app, [total, 0, 0])
        agg[app][1] += len(pairs)
        agg[app][2] += 1
    for app, (total, sent, ns) in sorted(agg.items()):
        print("   %-46s %8d %8d %7d%s" % (app, total, sent, ns,
                                          "   <- CAPPED, lower bound" if total > sent else ""))
    for app, st in skipped:
        print("   %-46s %8s %8s   (%s -- nothing to judge)" % (app, 0, 0, st))
    print("")

    def work(item):
        app, total, pairs, ci = item
        # ⛔ THE CHUNK INDEX IS IN THE FILENAME. Without it all four chunks of a topic wrote
        # to ONE path and ran concurrently, so each chunk judged whichever write landed last:
        # 129 judgements over only 89 DISTINCT pairs, 31 pairs judged repeatedly, and a
        # reported "25 examined" that was false. A race on a shared filename, and it looked
        # exactly like a completed run.
        pth = os.path.join(SCRATCH, "slice_%s_%d.txt" % (app.replace("/", "_"), ci))
        io.open(pth, "w", encoding="utf-8").write(slice_prompt(pairs, ctrl_rows))
        try:
            out, rc = run_codex(pth, timeout=900)
        except subprocess.TimeoutExpired:
            return app, total, None, "TIMEOUT"
        parsed = extract_json(out)
        # ⛔ RAW OUTPUT KEPT ON FAILURE. A harness that stores only the verdict cannot tell a
        # model that refused from a parser that could not read it, and that mistake produced
        # "codex 105 unparseable, 0 scoreable" once already.
        if parsed is None:
            io.open(pth + ".raw", "w", encoding="utf-8").write(out)
            return app, total, None, "UNPARSEABLE(rc=%s, raw kept)" % rc
        # ⭐ THE SLICE ONLY OWNS THE PAIRS IT WAS SENT. A judgement for a pair that was not
        # in this chunk is dropped -- it can only come from a stale file or a hallucinated id.
        mine = {x["pair_id"] for x in pairs}
        parsed = [j for j in parsed
                  if (j.get("pair_id") in mine or str(j.get("pair_id","")).startswith("__control"))]
        return app, total, parsed, "OK"

    results = []
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for r in ex.map(work, slices):
            results.append(r)
            print("   %-46s %s" % (r[0], r[3]))

    print("")
    print("=== CONTROLS -- expected beside observed, per slice ===")
    ctrl_ok = True
    for app, total, parsed, st in results:
        if parsed is None:
            continue
        got = {j.get("pair_id"): j.get("label") for j in parsed}
        line = []
        for c in CONTROLS:
            o = got.get(c["pair_id"])
            ok = (o == c["expect"])
            ctrl_ok = ctrl_ok and ok
            line.append("%s expected=%s observed=%s %s"
                        % (c["pair_id"], c["expect"], o, "OK" if ok else "MISMATCH"))
        print("   %-40s %s" % (app, " | ".join(line)))
    if not ctrl_ok:
        print("")
        print("   ⛔ A CONTROL FAILED. The delegated verdicts are NOT scored.")

    print("")
    print("=== GATE -- every delegated label must quote the record it judges ===")
    rowtext, judgements = {}, []
    for app, total, parsed, st in results:
        if parsed is None:
            continue
        t = byid[app]
        text = {r["oa_id"]: (r["title"] or "") + " " + (r["objectives_verbatim"] or "")
                for r in (t["verified"] or {})["rows"]}
        for j in parsed:
            pid = j.get("pair_id") or ""
            if pid.startswith("__control"):
                continue
            oid = pid.split("::")[-1]
            if oid not in text:
                continue
            rowtext[(app, oid)] = text[oid]
            judgements.append({"app_id": app, "cd_base": oid, "label": j.get("label"),
                               "reason": j.get("reason") or "",
                               "quotes_intervention": j.get("quotes_intervention") or [],
                               "quotes_condition": j.get("quotes_condition") or [],
                               "quotes_disqualifying": j.get("quotes_disqualifying") or []})
    ref = check(judgements, rowtext, path="oa_judgements_delegated.json")
    kept = [j for i, j in enumerate(judgements)
            if not any(("oa_judgements_delegated.json:%d " % (i + 1)) in r for r in ref)]
    print("   judgements returned : %d" % len(judgements))
    print("   REFUSED by the gate : %d   (quote not present, or label unsupported)"
          % (len(judgements) - len(kept)))
    print("   surviving           : %d" % len(kept))

    print("")
    print("=== RESULT -- topics that GAIN a counterpart ===")
    gained = sorted({j["app_id"] for j in kept if j["label"] == "COUNTERPART"})
    print("   %-46s %8s %8s %s" % ("app_id", "examined", "of", "gains?"))
    for app, total, parsed, st in results:
        n = sum(1 for j in kept if j["app_id"] == app)
        g = app in gained
        print("   %-46s %8d %8d %s" % (app, n, total,
                                       "YES" if g else
                                       ("no -- LOWER BOUND, %d of %d examined" % (n, total)
                                        if total > n else "no -- all examined")))
    print("")
    print("   topics gaining a counterpart : %d of %d topics sent"
          % (len(gained), len({a for a, _, _, _ in slices})))

    json.dump({"controls_ok": ctrl_ok, "scope": {"topics": ZERO, "cap": CAP},
               "judgements": kept, "gained": gained},
              io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("   written: %s" % OUT)


def extract_json(text):
    """Bare JSON or fenced -- both, because a parser that requires one shape reports the
    other vendor as 100% unparseable and that becomes a wrong belief about a tool."""
    for candidate in (text, text.replace("```json", "```")):
        depth, start = 0, None
        for i, ch in enumerate(candidate):
            if ch == "[":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        return json.loads(candidate[start:i + 1])
                    except ValueError:
                        start = None
    return None


if __name__ == "__main__":
    main()
