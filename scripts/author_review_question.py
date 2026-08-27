"""Author a replacement review question with two families, cold, from the same material.

COLD MEANS THE DEFECTIVE QUESTION IS NOT SHOWN. Each author is given the topic's title
and its trials -- names, registry ids, arms, and registered primary outcome where the
object holds one -- and asked to write a PICO question. Showing them the existing
question would anchor both to the defect being repaired, and the two "independent"
answers would inherit the same flaw.

TWO FAMILIES AUTHOR, A THIRD ADJUDICATES.
    Codex   (openai family)  -- authors
    agy     (google family, PINNED gemini-3.1-pro-high) -- authors
    Claude  (anthropic)      -- adjudicates, and is not shown either draft until both
                                are in, so the adjudication is over two finished texts
                                rather than a first draft plus a reaction to it.

THE MODEL PIN IS VERIFIED FROM THE CLI, NOT FROM A SELF-CLAIM. agy's settings.json here
defaults to GPT-OSS 120B, which is openai-family -- an unpinned run would produce a
same-family second opinion wearing a cross-family label. A model's report about itself is
testimony whichever field you ask for, so the pin is passed on the command line and the
command line is recorded beside the answer.

THE OLD QUESTION IS SUPERSEDED, NEVER DELETED. Any claim about a store is a claim about a
VERSION. Both are kept, with dates, so a later reader can see what was asked before and
what is asked now -- the corpus's own prior reasoning has already proved to be the best
evidence available in one paper tonight.
"""
import datetime, hashlib, io, json, os, re, shutil, subprocess, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
S = r"F:\claude-temp\claude\C--Users-mahmo\f842b4e4-f3de-4ce2-83d8-0adf7aa7cfb1\scratchpad"
SSOT = os.path.join(S, "main-wt", "ssot")
NCT = re.compile(r"NCT\d{8}")

BRIEF = """You are writing the REVIEW QUESTION for a systematic review, from scratch.

A review question must state, in one sentence a clinician would recognise:
  POPULATION    who the patients are
  INTERVENTION  the thing being tested
  COMPARATOR    what it is tested against
  OUTCOME       ONE named quantity, specific enough that a trial either reports it or
                does not

HARD RULES, and each exists because a question in this corpus broke it:
  1. DO NOT name, count or refer to the trials. Not "the two trials", not "both phase 3
     trials", not "the trials on this page". A question that defines eligibility as
     membership in its own answer cannot be searched for -- the search would only
     rediscover what it already contains.
  2. DO NOT defer the outcome. "the outcome each trial registered as its primary" is not
     a quantity; a protocol whose estimand says that has registered nothing. Name ONE
     outcome, chosen by you from the material, and say why in one line.
  3. DO NOT write a statement, an observation, or a comment about the evidence. It must
     be a QUESTION, ending in a question mark.
  4. DO NOT invent a population, drug, comparator or outcome that the material does not
     support. If the material cannot support a single coherent question -- for example
     because the trials share no common comparator or no common outcome -- SAY SO and
     explain what is missing, rather than writing a question the evidence cannot answer.

  5. CHOOSING THE OUTCOME -- follow this rule and report which branch you took.
     (a) If every trial registers the SAME PRIMARY outcome, use it. Do not descend to a
         secondary when a shared primary exists.
     (b) If the registered primaries are NOT the same quantity -- different components,
         different arity, a hierarchical composite against a plain endpoint -- then no
         shared primary exists, and you may descend to a shared SECONDARY.
     (c) IF AND ONLY IF you descend to a secondary, you MUST first compare the two
         registered DEFINITIONS WORD BY WORD and quote them, because two outcomes with
         the same NAME are routinely not the same QUANTITY. A real case from this corpus:
         both trials register "all-cause mortality", but one of them registers
         "All-cause Mortality by Month 30, Including Death Due to Any Cause, Heart
         Transplant or Cardiac Mechanical Assist Device" -- deaths in one, deaths OR
         transplant OR device in the other. Nothing in the field name reveals that. If
         the definitions are not equivalent, say so and either choose another outcome or
         answer UNANSWERABLE.

Add these two lines to your answer, after OUTCOME:

OUTCOME RULE BRANCH: (a) shared primary / (b) no shared primary, used a secondary
DEFINITIONS COMPARED: <if branch (b), quote BOTH registered definitions verbatim and say
                       whether they are equivalent. If branch (a), write NOT APPLICABLE.>

Answer in EXACTLY this form and nothing else:

QUESTION: <one sentence, ending in a question mark, or the word UNANSWERABLE>
POPULATION: <...>
INTERVENTION: <...>
COMPARATOR: <...>
OUTCOME: <one named quantity>
WHY THIS OUTCOME: <one line>
CONCERNS: <anything the material does not settle, or NONE>
"""


# MATERIAL IS NOW SCHEMA-DERIVED. The hand-listed version of this function caused
# two of the two disagreements in this batch; see trial_material.py.
sys.path.insert(0, S)
from trial_material import material  # noqa: E402


# ONE STEP BELOW THE HIGHEST, PINNED EXPLICITLY, AND THE LADDER WAS MEASURED.
#
# Codex does not validate this key at parse time -- it echoes whatever it is given in
# its own banner, including nonsense. So the ladder was established by what the API
# does, not by what the banner says:
#     -c model_reasoning_effort=__invalid__  -> HTTP 400, no completion
#     -c model_reasoning_effort=max          -> HTTP 400, no completion  (NOT a level)
#     -c model_reasoning_effort=xhigh        -> completes
#     -c model_reasoning_effort=high         -> completes
# `max` is not a reasoning effort for gpt-5.5; the highest valid level is `xhigh`, so
# one step below it is `high`.
#
# THIS MATTERS BECAUSE THE DEFAULT IS THE TOP. ~/.codex/config.toml sets
# model_reasoning_effort = "xhigh", so ANY call that omits the flag runs at the highest
# setting. The first 44 authoring calls omitted it and therefore ran at xhigh. Their
# results are labelled with that level and must NOT be pooled with results from this
# one: a split direction and a caveats-per-answer rate are properties of the
# CONFIGURATION as much as of the model, exactly as a disagreement can be a property of
# the extractor.
CODEX_EFFORT = "high"


def ask_codex(topic, prompt):
    exe = shutil.which("codex")
    if not exe:
        return {"family": "openai", "ok": False, "outcome": "FAILED",
                "error": "codex not on PATH"}
    pf = os.path.join(S, "q_codex_" + topic + ".txt")
    open(pf, "w", encoding="utf-8").write(prompt)
    cmd = [exe, "exec", "--skip-git-repo-check",
           "-c", "model_reasoning_effort=" + CODEX_EFFORT, "-"]
    r = subprocess.run(cmd, stdin=open(pf, encoding="utf-8"), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=900)
    raw = (r.stdout or "") + (r.stderr or "")
    body = (r.stdout or "").strip()
    # VERIFIED FROM THE INVOCATION LOG, NOT FROM A SELF-REPORT. Codex prints the level
    # it actually started with in its own banner; a model asked what level it is running
    # at would be giving testimony, which is the mistake the agy pin already taught.
    m = re.search(r"reasoning effort:\s*(\S+)", raw)
    observed = m.group(1) if m else None
    return {"family": "openai", "model": "gpt-5.5",
            "effort_requested": CODEX_EFFORT,
            "effort_observed_in_banner": observed,
            "effort_confirmed": observed == CODEX_EFFORT,
            "command": " ".join(cmd),
            "ok": bool(body) and observed == CODEX_EFFORT,
            "outcome": "EXECUTED" if (body and observed == CODEX_EFFORT) else "FAILED",
            "failure": None if (body and observed == CODEX_EFFORT) else
                       ("empty reply" if not body else
                        "effort level not confirmed in banner: saw " + str(observed)),
            "stdout_bytes": len(r.stdout or ""), "exit": r.returncode, "reply": body}


def ask_agy(topic, prompt):
    """Prompt via FILE, not argv, with a canary proving the file was actually read.

    WHY NOT --print=<prompt>. Windows caps a command line at 32,767 characters. The
    schema-derived material pushes these prompts past 20 KB and the cap was hit on the
    seventh topic, raising WinError 206 mid-batch. agy's --print takes an inline argument
    and does not read stdin in text mode, so the prompt goes to a file and agy is pointed
    at it; settings.json here already grants read_file(*).

    WHY A CANARY. A file read that silently fails leaves the model with no material and
    nothing stopping it answering anyway -- and an answer composed from its own knowledge
    is indistinguishable, in shape, from one grounded in the material. So the file carries
    a token the reply must echo. No echo means the read failed, and the answer is recorded
    as FAILED rather than believed. This is the same law as the search harness: an
    instrument that could not read must not report a reading.
    """
    exe = shutil.which("agy")
    if not exe:
        return {"family": "google", "ok": False, "outcome": "FAILED",
                "error": "agy not on PATH"}
    canary = "CANARY-" + hashlib.sha256(
        (topic + prompt[:200]).encode("utf-8")).hexdigest()[:12].upper()
    pf = os.path.join(S, "q_agy_" + topic + ".txt")
    open(pf, "w", encoding="utf-8").write(
        "VERIFICATION TOKEN: " + canary + "\n\n" + prompt)
    instruction = (
        "Read the file " + pf + " in full. It contains a VERIFICATION TOKEN and then your "
        "complete task. Carry out the task exactly as the file specifies. Begin your reply "
        "with a line reading 'TOKEN: <the verification token from the file>' and then give "
        "the answer in the form the file requires. If you cannot read the file, reply with "
        "exactly 'FILE UNREADABLE' and nothing else -- do not attempt the task from memory.")
    cmd = [exe, "--model", "gemini-3.1-pro-high", "--add-dir", S, "--print=" + instruction]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1200)
    except Exception as e:
        return {"family": "google", "ok": False, "outcome": "FAILED",
                "error": type(e).__name__ + ": " + str(e)[:200]}
    body = (r.stdout or "").strip()
    read_ok = canary in body
    return {"family": "google", "model_pinned_on_cli": "gemini-3.1-pro-high",
            "command": " ".join(cmd[:5]) + " --print=<pointer, %d chars>" % len(instruction),
            "prompt_file": pf, "prompt_bytes": len(prompt.encode("utf-8")),
            "canary": canary, "canary_echoed": read_ok,
            "outcome": "EXECUTED" if (body and read_ok) else "FAILED",
            "ok": bool(body) and read_ok,
            "failure": None if (body and read_ok) else
                       ("empty reply" if not body else
                        "CANARY NOT ECHOED -- the material was not read, so the answer is "
                        "not grounded in it and is discarded"),
            "stdout_bytes": len(r.stdout or ""), "exit": r.returncode, "reply": body}


def author(topic):
    text, completeness = material(topic)
    prompt = BRIEF + "\n" + text + "\n"
    print("--- " + topic + "  (prompt " + str(len(prompt.encode("utf-8"))) + " bytes, "
          + str(len(completeness["truncated"])) + " values truncated)")
    out = {"topic": topic, "completeness": completeness, "authored_utc": datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "drafts": {}}
    for name, fn in (("openai", ask_codex), ("google", ask_agy)):
        d = fn(topic, prompt)
        out["drafts"][name] = d
        q = ""
        for line in (d.get("reply") or "").splitlines():
            if line.strip().upper().startswith("QUESTION:"):
                q = line.split(":", 1)[1].strip()
                break
        print("    %-7s bytes=%-6s %s" % (name, d.get("stdout_bytes"),
                                          ("OK  " + q[:90]) if d.get("ok") else
                                          "*** NO OUTPUT: " + str(d.get("error"))))
    return out


if __name__ == "__main__":
    results = []
    for topic in sys.argv[1:]:
        results.append(author(topic))
    p = os.path.join(S, "authored_drafts.json")
    prev = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
    prev = [r for r in prev if r["topic"] not in {x["topic"] for x in results}]
    json.dump(prev + results, open(p, "w", encoding="utf-8"), indent=1)
    print("\nwrote " + p + "  (%d topics held)" % len(prev + results))
