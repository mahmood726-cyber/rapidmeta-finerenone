# Reading logged BEFORE the remaining four verdicts land — 2026-08-30

**Written with 2 of 6 in and 4 outstanding. Nothing below may be edited after the run;
corrections go underneath, dated.**

---

## ⛔ THE OPENAI PAIR IS A TIE, AND MUST BE REPORTED AS ONE

| judge | position | verdict |
|---|---|---|
| openai | ours first (A = ours) | **A better, MODERATELY** — ours |
| openai | theirs first (A = theirs) | **A better, MODERATELY** — theirs |

Same family, same prompt verbatim, same two documents, opposite order, opposite winner, and
**the same stated strength both times**.

⇒ ***THIS IS WHAT "TOO CLOSE TO CALL FOR THIS JUDGE" LOOKS LIKE.*** The openai family did not
choose our page and did not choose the comparator. It chose **A**.

### The rule, fixed now so it cannot be re-read once the score is known

* The openai pair counts as **ONE TIE**, not as one-for and one-against.
* It is **not averaged into a total** and neither half is quoted on its own.
* If the remaining four all choose ours, the honest result is **"4 of 6, with one family
  tied"** — never "5 of 6".
* A family that flips on position has told us its verdict is not about the documents. Reporting
  either half would be reporting the order they were pasted in.

### Why this is bad news and is being written down as such

**Round 2 had NO position effect on direction: 6 of 6 chose the hand-built page from both
positions.** A position flip is therefore a CHANGE, and it is a change in the direction of the
comparison being closer, not further apart. ⚠️ Whatever the remaining four do, this pair is
evidence that the regenerated page does not dominate the way the authored page did — which is
the prediction I logged, resolving against us.

### What openai said against us, both times, unprompted

* *"internally cluttered, contradictory in places, and repeatedly labels itself not ready"*
* *"much more informative but cluttered and internally repetitive"*
* *"hard for a normal clinical reader to use"*
* GRADE recorded as **"Pending"**; risk-of-bias adjudication unresolved

⇒ The LENGTH prediction and the CLINICAL-READING prediction are **both** firing, and they are
firing in the same rationale, which is why they were pre-registered as separate falsifiers: the
reading is 1,623 characters of an 87,437-character page and can hold perfectly while the page
around it loses an axis on reading burden.

---

## ⭐⭐⭐ THE FINDING THAT MATTERS MORE THAN THE SCORE: TWO OF THREE FAMILIES ALMOST COLLAPSED INTO ONE

`agy --print` takes its prompt as an ARGUMENT, and a 97 KB prompt cannot be passed that way.
**Bare `agy` does read stdin** — so the obvious repair works, produces a full-length, well-formed
verdict, and is wrong:

    $ echo "Reply with exactly: OK and name your model family" | agy
    OK GPT-OSS

It answers as **GPT-OSS**, the model persisted in `~/.gemini/antigravity-cli/settings.json`
(`"GPT-OSS 120B (Medium)"`), **not** Gemini. A verdict filed under `family: google` would have
been an OpenAI-family model.

### Why this would have been invisible

⛔ **Three independent families is the ENTIRE basis for calling the panel's agreement
meaningful.** Two of three collapsing into one inflates agreement — the openai family would
effectively have voted twice more — while **every label in the results table still reads
correctly**. Nothing downstream checks a family label against the model that produced it.

⇒ ***`--model` on the command line proves nothing. The proof is the model NAMING ITS OWN FAMILY
IN THE COMPLETION.*** With the flag supplied, the same probe returns `OK Gemini`. The flag is a
configuration; the echoed family is a measurement, and only one of them is evidence.

**Same distinction as proving a model from its CLI log rather than from its self-claim, and the
same distinction as asserting on served bytes rather than on a push's exit code.** This project
keeps rediscovering one rule: *a statement about what you asked for is not a statement about
what happened.*

---

## Failed runs, counted as failures and not as verdicts

| attempt | rc | what it was |
|---|---|---|
| openai / ours-first | **126** | `Argument list too long` — 97 KB prompt as argv. 104-byte artefact. |
| google / ours-first | **2** | `agy --print` printed its help; it needs an argument, not stdin. 2,710-byte artefact of usage text. |

⚠️ Both produced NON-EMPTY files that a looser harness would have parsed as short verdicts. The
size threshold and the rc check are what stopped them. **An empty or malformed artefact is a
FAILED RUN, never a tie** — a tie is a judgement, and neither of these contained one.
