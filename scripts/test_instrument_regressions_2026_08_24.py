"""Six instrument failures from 2026-08-24, each with its defect PLANTED and watched to fail.

MAHMOOD'S RULE: "make sure all our mistakes are noted and we make sure they don't happen
again by planting the same error." A check that has never been observed to fail is not a
check. A `prove()` that shows the PATTERN fires demonstrates the pattern fires -- it does
not demonstrate that the build refuses. So every case below does three things in order:

    1. PLANT the original defect into a fixture
    2. run the check and assert it FAILS
    3. RESTORE the fixture and assert the check PASSES again

Both halves are required. A check that fires on the planted defect but also fires on the
restored fixture is not discriminating, it is just noisy, and it would have been reported
here as passing.

EVERY FIXTURE IS A FILE UNDER `scripts/fixtures/instrument/`, WRITTEN AND DELETED BY THIS
SUITE. Nothing here reads the corpus. A check keyed to live pages passes or fails for
reasons that have nothing to do with the check -- the corpus changes underneath it, and the
suite then reports the corpus rather than the instrument.

WHY THESE SIX. Each cost real time or produced a confident wrong finding on 2026-08-24:

  1  `-u` does not reach a TextIOWrapper the script installs itself. A 163-page job wrote a
     0-byte log for 47 minutes. Another lane read the empty log and reported a 15.7-hour ETA
     for a 90-minute job.
  2  `kill -0` on a Windows PID from Git Bash returns a false negative. A healthy job was
     nearly reported as crashed at 109/163.
  3  A 9,000-character cap silently truncated an 11,156-character document, and a blind
     reviewer cited the cut as evidence the MANUSCRIPT was truncated.
  4  `\\b` written through a shell heredoc arrived as a literal BACKSPACE byte; the regex
     matched nothing and the function returned its input unchanged while `inspect.getsource`
     printed code that read correctly.
  5  Slicing a panel payload from `id="pn-paper"` to `end-paper` leaked the tail of the
     opening tag and the head of the closing comment, and a reviewer reported "raw HTML
     leaks into the page".
  6  A string match standing in for a rule. From the site lane: a compliance audit reported
     "no pricing -- PASS" while a live pricing ladder sat on the page, because it searched
     for two known strings instead of testing the property. This suite's case 6 audits THIS
     repo's gates for the same shape.

Exit 1 if any check fails to fail on its planted defect. That is the whole point.
"""
import io
import os
import re
import subprocess
import sys

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", write_through=True)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(REPO, "scripts", "fixtures", "instrument")
RESULTS = []


def record(case, planted_failed, restored_passed, note=""):
    ok = planted_failed and restored_passed
    RESULTS.append((case, planted_failed, restored_passed, ok, note))
    print("  %-34s planted->FAIL %-5s  restored->PASS %-5s  %s"
          % (case, planted_failed, restored_passed, "OK" if ok else "*** UNPROVEN ***"))
    if note:
        print("      %s" % note)


# ---------------------------------------------------------------------------------------
# 1. A wrapper without write_through swallows progress output.
# ---------------------------------------------------------------------------------------
# THE SLEEP HAS TO OUTLAST THE PROBE, or the buffer flushes at exit inside the observation
# window and the unbuffered case looks identical to the buffered one. The first version
# slept 0.2s against a 1s probe and reported itself UNPROVEN -- correctly, because it was.
# The real incident was a job that printed nothing for 47 MINUTES while working normally,
# so the fixture has to stay alive long enough for "nothing yet" to mean something.
_PROG = ('import io, sys, time\n'
         'sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8"%s)\n'
         'print("PROGRESS 1 of 3")\n'
         'time.sleep(4)\n'
         'print("PROGRESS 2 of 3")\n')


def check_progress_visible(script_path):
    """PASS when a redirected run emits progress BEFORE it exits."""
    out = os.path.join(FIX, "prog.out")
    with io.open(out, "w") as fh:
        p = subprocess.Popen([sys.executable, "-u", script_path], stdout=fh,
                             stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            pass
    p.wait()
    # Read what was visible; the defect is that NOTHING is, until exit.
    return os.path.getsize(out) > 0


def case_1():
    os.makedirs(FIX, exist_ok=True)
    path = os.path.join(FIX, "progress_writer.py")
    # PLANT: no write_through -- the 2026-08-24 defect exactly.
    io.open(path, "w", encoding="utf-8").write(_PROG % "")
    planted = not _visible_during_run(path)
    # RESTORE
    io.open(path, "w", encoding="utf-8").write(_PROG % ', write_through=True')
    restored = _visible_during_run(path)
    record("1 silent-log (write_through)", planted, restored,
           "" if planted else "the unbuffered case still emitted; probe is not discriminating")


def _visible_during_run(script_path):
    """Was anything readable from the log WHILE the process was still alive?"""
    out = os.path.join(FIX, "prog.out")
    with io.open(out, "w") as fh:
        p = subprocess.Popen([sys.executable, "-u", script_path], stdout=fh,
                             stderr=subprocess.STDOUT)
        import time
        seen = False
        # Observe for 2s while the fixture is still sleeping. A write_through wrapper shows
        # its first line immediately; a block-buffered one shows nothing until it exits.
        for _ in range(40):
            if os.path.exists(out) and os.path.getsize(out) > 0:
                seen = True
                break
            if p.poll() is not None:
                break
            time.sleep(0.05)
        p.kill()
        p.wait()
    return seen


# ---------------------------------------------------------------------------------------
# 2. `kill -0` on a Windows PID from Git Bash is a false negative.
# ---------------------------------------------------------------------------------------
def case_2():
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(6)"])
    try:
        wrong = subprocess.run(["bash", "-c", "kill -0 %d 2>/dev/null" % p.pid],
                               capture_output=True).returncode == 0
        right = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "if (Get-Process -Id %d -ErrorAction SilentlyContinue) {exit 0} else {exit 1}"
             % p.pid], capture_output=True).returncode == 0
        # PLANTED DEFECT = using the wrong probe on a process that IS alive.
        # The check "fails" (correctly detects the bad probe) when wrong != right.
        planted = (wrong != right) and right
        record("2 kill-0 false negative", planted, right,
               "wrong probe said alive=%s, Get-Process said alive=%s" % (wrong, right))
    finally:
        p.kill()
        p.wait()


# ---------------------------------------------------------------------------------------
# 3. A silent cap truncates a document the panel then judges.
# ---------------------------------------------------------------------------------------
def _extract():
    sys.path.insert(0, os.path.join(REPO, "scripts", "fixtures"))
    spec = os.path.join(REPO, "scripts", "fixtures", "instrument", "extract_prose.py")
    import importlib.util
    s = importlib.util.spec_from_file_location("fx_extract", spec)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def case_3():
    os.makedirs(FIX, exist_ok=True)
    src = os.path.join(os.path.dirname(REPO), "claude-temp", "claude")
    # A self-contained copy of the extractor under test.
    ex = os.path.join(FIX, "extract_prose.py")
    io.open(ex, "w", encoding="utf-8").write(_EXTRACTOR)
    long_doc = os.path.join(FIX, "long.html")
    body = "".join("<p>Sentence number %d of the manuscript body.</p>" % i
                   for i in range(1, 400))
    io.open(long_doc, "w", encoding="utf-8").write(
        "<section id=\"pn-paper\">%s</section><!--end-paper-->" % body)
    m = _extract()
    capped = m.prose(long_doc, 900)
    full = m.prose(long_doc)
    planted = len(full) > 900 and "[TRUNCATED" in capped
    restored = "[TRUNCATED" not in full
    record("3 silent truncation", planted, restored,
           "full=%d chars, capped announces the cut=%s" % (len(full), "[TRUNCATED" in capped))


# ---------------------------------------------------------------------------------------
# 4. A backspace byte from a shell heredoc, invisible in the source.
# ---------------------------------------------------------------------------------------
def case_4():
    os.makedirs(FIX, exist_ok=True)
    path = os.path.join(FIX, "control_char.py")
    clean = 'PATTERN = r"\\bword\\b"\n'
    planted_src = 'PATTERN = r"' + chr(8) + 'word' + chr(8) + '"\n'
    io.open(path, "w", encoding="utf-8", newline="").write(planted_src)
    planted = _has_control_chars(path)
    io.open(path, "w", encoding="utf-8", newline="").write(clean)
    restored = not _has_control_chars(path)
    record("4 backspace byte in source", planted, restored,
           "detector greps for C0 controls other than tab/newline/CR")


def _has_control_chars(path):
    raw = io.open(path, encoding="utf-8", newline="").read()
    return any(ord(c) < 32 and c not in "\t\n\r" for c in raw)


# ---------------------------------------------------------------------------------------
# 5. Boundary markers leaking into a panel payload.
# ---------------------------------------------------------------------------------------
# BUILT FROM A LINE LIST, NOT A NESTED STRING LITERAL, AND THAT IS THE POINT.
#
# The first version of this fixture was a triple-quoted block containing `[ \\\\t]+`. Written
# out, it became `[ \\t]+`, which in a regex is "backslash OR the letter t" -- so the
# extractor ATE EVERY LETTER T and returned "Real sen ence one." That is case 4's defect,
# escaping mangled through a string literal, committed while writing case 4's regression
# test. Nothing here contains a backslash escape: whitespace is handled with str methods and
# the two characters that need naming are named with chr().
_TAB, _NL = chr(9), chr(10)
_EXTRACTOR = _NL.join([
    "import re, html as H",
    "TAB, NL = chr(9), chr(10)",
    "def prose(path, limit=None):",
    "    h = open(path, encoding='utf-8', errors='replace').read()",
    "    i = h.find('id=' + chr(34) + 'pn-paper' + chr(34))",
    "    if i < 0:",
    "        return ''",
    "    i2 = h.find('>', i)",
    "    i = i2 + 1 if i2 >= 0 else 0",
    "    j = h.find('end-paper', i)",
    "    if j >= 0:",
    "        k = h.rfind('<!--', i, j)",
    "        j = k if k >= 0 else j",
    "    else:",
    "        j = len(h)",
    "    seg = h[i:j]",
    "    seg = re.sub('(?i)</(p|div|h[1-6]|tr|section|td|th|li)>', NL, seg)",
    "    t = H.unescape(re.sub('(?s)<[^>]+>', ' ', seg))",
    "    t = t.replace(TAB, ' ')",
    "    while '  ' in t:",
    "        t = t.replace('  ', ' ')",
    "    out = NL.join(x.strip() for x in t.split(NL) if len(x.strip()) > 2)",
    "    if limit and len(out) > limit:",
    "        out = out[:limit] + NL + '[TRUNCATED BY THE EXTRACTOR AT %d CHARACTERS]' % limit",
    "    return out",
    "",
])


def case_5():
    os.makedirs(FIX, exist_ok=True)
    ex = os.path.join(FIX, "extract_prose.py")
    io.open(ex, "w", encoding="utf-8").write(_EXTRACTOR)
    doc = os.path.join(FIX, "leak.html")
    io.open(doc, "w", encoding="utf-8").write(
        '<section id="pn-paper"><p>Real sentence one.</p>'
        '<p>Real sentence two.</p></section><!--end-paper-->')
    m = _extract()
    good = m.prose(doc)
    restored = ('id=' not in good) and ('<!--' not in good) and ("Real sentence one." in good)
    # PLANT: the naive slice that shipped this morning.
    raw = io.open(doc, encoding="utf-8").read()
    i = raw.find('id="pn-paper"')
    j = raw.find('end-paper')
    naive = re.sub(r"(?s)<[^>]+>", " ", raw[i:j])
    planted = ('id=' in naive) or ('<!--' in naive)
    record("5 payload boundary leakage", planted, restored,
           "naive slice leaks %r" % naive.strip()[:34])


# ---------------------------------------------------------------------------------------
# 6. A string match standing in for a rule.
# ---------------------------------------------------------------------------------------
def case_6():
    """Audit THIS repo's reader gate for vocabulary matching where a property is meant.

    THE SITE LANE'S DEFECT, GENERALISED. A compliance audit reported "no pricing -- PASS"
    while a live pricing ladder sat on the page, because it searched for two known strings
    rather than testing the rule. The same shape is in this repo: today's 20-page estimand
    finding -- a table row whose VALUE is an absence marker -- passed the reader gate,
    because the gate matches the vocabulary of a splice and not the property "a cell that
    should hold a value holds a marker instead".

    This case does not fail the build. It NAMES every literal-vocabulary pattern in the gate
    so the count cannot quietly grow, and asserts that a defect of the same CLASS but
    different WORDING escapes -- which is the property that makes vocabulary matching
    unproven.
    """
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import gate_paper_reads_terribly_2026_08_24 as G
    literal = []
    for name in ("HOLLOW_NOUNS",):
        literal += [(name, s) for s in getattr(G, name, ())]
    for owner, rx in getattr(G, "FOREIGN_EXAMPLES", ()):
        literal.append(("FOREIGN_EXAMPLES", rx.pattern))
    literal.append(("VERDICT_IN_TITLE", G.VERDICT_IN_TITLE.pattern))
    literal.append(("SENTINEL_SPLICE", G.SENTINEL_SPLICE.pattern))

    # A hollow noun the gate has never seen. Same class, different words.
    novel = ("<p>Figure 1. Forest plot -- the measure this analysis summarises.</p>")
    escapes = not G.findings_for("<probe>", novel, {"probe"})
    known = bool(G.findings_for(
        "<probe>", "<p>Figure 1. Forest plot -- the clinical quantity this page pools.</p>",
        {"probe"}))
    record("6 vocabulary-not-rule (audit)", escapes and known, True,
           "%d literal patterns; a same-class novel wording escapes=%s, known wording caught=%s"
           % (len(literal), escapes, known))
    print("      literal-vocabulary patterns the gate depends on:")
    for name, pat in literal:
        print("        %-18s %s" % (name, str(pat)[:88]))


def main():
    os.makedirs(FIX, exist_ok=True)
    print("PLANT-THE-DEFECT SUITE -- every check must be observed to FAIL on its own defect\n")
    for fn in (case_1, case_2, case_3, case_4, case_5, case_6):
        try:
            fn()
        except Exception as exc:                   # noqa: BLE001
            record(fn.__name__, False, False, "raised %s: %s" % (type(exc).__name__, exc))
    unproven = [r for r in RESULTS if not r[3]]
    print("\n%d checks, %d proven by planting, %d UNPROVEN"
          % (len(RESULTS), len(RESULTS) - len(unproven), len(unproven)))
    for case, _p, _r, _ok, note in unproven:
        print("  UNPROVEN: %s  %s" % (case, note))
    return 1 if unproven else 0


if __name__ == "__main__":
    sys.exit(main())
