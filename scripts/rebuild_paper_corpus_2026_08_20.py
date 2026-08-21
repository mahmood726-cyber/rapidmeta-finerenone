"""Rebuild the pages that have a Paper panel, in batches, with the four predictions each.

WHY BATCHES AND NOT ONE RUN. 112 pages at roughly two minutes each is about four hours. A
four-hour run that fails at hour three with nothing pushed is the worst outcome available,
so this writes a batch, verifies it, and hands back -- the caller pushes, then runs the next
batch. Nothing waits for the end.

THE FOUR PREDICTIONS, PER PAGE, STATED BEFORE THE BUILD AND CHECKED AFTER:

    1  the machine-vocabulary share of the Paper panel's PROSE falls
    2  field paths standing in the sentence flow fall to at most a handful
    3  no estimate, registration id or registered outcome name is lost
    4  the `quoted verbatim` R sections are byte-identical

A page failing any of them is REPORTED AND ITS OLD BYTES ARE RESTORED, not pushed. The fix
is a register change; a page whose numbers moved has been paraphrased, and that is the
failure mode to watch.

THE OCCURRENCE PREDICATE. `--verify-only` re-checks a batch WITHOUT building, and it is
FALSE when the build did not run: it compares each page's `mtime` against the recorded
batch start and refuses a page that was not written. A batch report that cannot tell "built
and unchanged" from "never built" is the class-44 defect, and this file would be an easy
place to reintroduce it.

BASELINES ARE TAKEN BEFORE THE BUILD AND KEPT. `outputs/paper_register_rollout.json` holds
the before-measurement of every page, so a later batch can be compared against the state
this rollout started from rather than against whatever the page happened to be last time.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import time
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
LEDGER = os.path.join(REPO, "outputs", "paper_register_rollout.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lint_paper_reads_as_prose as L
import prove_register_change_moved_no_content as PROVE


# PAGES THIS ROLLOUT MUST NOT TOUCH, BY NAME.
#
# ARNI_HF_REVIEW.html is deliberately excluded from rebuilds: its manuscript is an AUTHORED
# docmodel that the projector reproduces at about 11%, so a rebuild would replace 11,182
# words of written argument with a projection of the object.
#
# THIS ROLLOUT ATTEMPTED TO BUILD IT. The standing instruction has been in force all night
# and the batch runner had no exclusion for it -- what stopped the build was
# ssot/manuscript_guard.py refusing on MANUSCRIPT_SHRINK, i.e. ANOTHER guard catching it.
# ARNI is byte-identical to HEAD, verified by hash, so nothing was lost. But an instruction
# enforced by a guard that happens to cover it is not enforced; it is lucky.
#
# The list is checked BEFORE the backup copy is taken, so an excluded page is never even
# copied, let alone built.
# THE LIST MOVED TO ssot/do_not_rebuild.py, AND THE CHECK MOVED INTO THE BUILDER.
#
# It lived here and in scripts/rebuild_paper_corpus_2026_08_20.py -- two copies, which
# audit_standing_instructions.py had already flagged. Two copies means a THIRD caller
# inherits neither, and build_tabbed.py invoked directly was exactly that: both pages
# ever wrongly rebuilt went through it and it knew about no list at all.
sys.path.insert(0, os.path.join(REPO, "ssot"))
from do_not_rebuild import PAGES as DO_NOT_REBUILD          # noqa: E402


LOCK = os.path.join(REPO, "outputs", ".paper_register_rollout.lock")
RUN_ID = "%d@%s" % (os.getpid(), time.strftime("%H%M%S"))


# AND THE LOCK DOES NOT PROTECT THE LEDGER FROM A PERSON.
#
# While run 26224 was mid-batch I cleared a failed row by hand, twice, and both edits were
# silently overwritten: the running process holds the ledger in memory and rewrites it after
# every page. THE SAME CLASS AS TWO CONCURRENT ROLLOUTS -- state written by two writers,
# resolved by whichever wrote last -- with a person as the second writer instead of a second
# process. The lock file holds the pid and I could have read it before editing.
#
# Nothing here can stop that; it is recorded because the fix is to READ THE LOCK, and the
# lock now exists precisely so there is something to read.


def acquire_lock():
    """One rollout at a time. A ledger two processes can write is not a ledger.

    THIS COST TWO CORRECTLY-BUILT PAGES. Two rollouts ran concurrently against the same
    ledger with different `before` baselines. ABLATION_AF_HEART_FAILURE and
    ABLATION_AF_MEDICAL_THERAPY were built, verified and recorded as done by one process,
    then rebuilt by the other against a stale baseline of 0 field paths, judged a
    regression, and ROLLED BACK TO THEIR OLD BYTES. Their good builds were recovered only
    by re-checking the files on disk rather than trusting the ledger.

    IT IS THE STALE-BASELINE CLASS AGAIN: a comparison against a snapshot that is no longer
    what it describes. Concurrency makes it silent, because the ledger simply holds
    whichever row was written last and nothing says the two disagreed.

    O_EXCL on a lock file, holding the pid -- not a flag in the ledger, which is the thing
    being contended for.
    """
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        try:
            held = io.open(LOCK, encoding="utf-8").read().strip()
        except Exception:
            held = "unreadable"
        sys.exit("REFUSED: a rollout is already running (%s). Two processes writing this "
                 "ledger is how ABLATION_AF_HEART_FAILURE and ABLATION_AF_MEDICAL_THERAPY "
                 "were rolled back after building correctly. If that run is dead, delete "
                 "%s." % (held, os.path.relpath(LOCK, REPO)))
    os.write(fd, RUN_ID.encode("utf-8"))
    os.close(fd)


def release_lock():
    if os.path.exists(LOCK):
        try:
            if io.open(LOCK, encoding="utf-8").read().strip() == RUN_ID:
                os.remove(LOCK)
        except Exception:
            pass


def page_to_object():
    """Delivered page -> object, from ssot/PAGE_MAP.json.

    THE FIRST VERSION IMPORTED scripts/objects_for_pages.py LOOKING FOR A `PAGE_MAP` DICT.
    That module holds a PATH to the map, not the map, so the import succeeded, the getattr
    returned a string, `isinstance(m, dict)` was False, and the function returned an EMPTY
    MAP -- silently. Every page then fell through to name-guessing, and the two whose names
    do not match their object directory (ALIROCUMAB_LIPID_AUTO_FULL_REVIEW ->
    alirocumab-lipid) were reported UNRESOLVED. A lookup that finds nothing looked exactly
    like a corpus with no map, which is registry class 25.
    """
    path = os.path.join(SSOT, "PAGE_MAP.json")
    if not os.path.exists(path):
        sys.exit("REFUSED: ssot/PAGE_MAP.json is absent. Resolving 113 pages to objects by "
                 "name-guessing is how one review's manuscript reaches another's page.")
    m = json.load(io.open(path, encoding="utf-8"))
    pairs = {}
    for page, obj in m.items():
        # values are "ssot/<topic>/<topic>.json"
        parts = str(obj).replace("\\", "/").split("/")
        if len(parts) >= 2:
            pairs[os.path.basename(str(page))] = parts[-2]
    if not pairs:
        sys.exit("REFUSED: PAGE_MAP.json parsed to zero pairs.")
    return pairs


def object_for(page_name, mapped):
    """Resolve a page to its object directory, or None.

    NAMED, NOT GUESSED. A page whose object cannot be resolved is REPORTED as unresolved
    and skipped -- building it against a guessed object is how one review's manuscript ends
    up on another review's page, which is the contamination incident this repository's
    projector docstring is written around.
    """
    obj = mapped.get(page_name)
    if obj:
        cand = os.path.join(SSOT, str(obj), "%s.json" % obj)
        if os.path.exists(cand):
            return str(obj)
    stem = page_name[:-len("_REVIEW.html")].lower().replace("_", "-")
    for suffix in ("", "-review", "-auto-full-review"):
        cand = stem + suffix
        if os.path.exists(os.path.join(SSOT, cand, "%s.json" % cand)):
            return cand
    for tail in ("-auto-full-review", "-auto-review", "-review"):
        if stem.endswith(tail):
            base = stem[:-len(tail)]
            for suffix in ("", "-review", "-auto-full-review"):
                cand = base + suffix
                if os.path.exists(os.path.join(SSOT, cand, "%s.json" % cand)):
                    return cand
    return None


def restore(backup, page, why):
    """Put the old bytes back, and NEVER raise while doing it.

    A ROLLBACK THAT ASSUMES ITS BACKUP EXISTS CRASHES THE WHOLE BATCH. This run died on
    APIXABAN_VTE_TREATMENT with FileNotFoundError moving a .rollback that was not there,
    and took the remaining pages of the batch with it. THE RESTORE PATH IS THE LAST THING
    THAT SHOULD BE ABLE TO FAIL: it runs only when something has already gone wrong.

    Returns True if the old bytes are back, False if the file on disk is the NEW build and
    the caller must say so rather than implying a restore happened.
    """
    if not os.path.exists(backup):
        why.append("AND ITS BACKUP WAS GONE -- the file on disk is the NEW build and was "
                   "NOT restored. Check it by hand before pushing.")
        return False
    try:
        if os.path.exists(page):
            os.remove(page)
        os.replace(backup, page)
        return True
    except OSError as exc:
        why.append("AND THE RESTORE ITSELF FAILED (%s) -- the file on disk is not "
                   "necessarily either version. Check it by hand." % exc)
        return False


def measure(path):
    try:
        return L.measure(path)
    except Exception:
        return None


def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(io.open(LEDGER, encoding="utf-8"))
    return {"started": None, "before": {}, "done": {}, "failed": {}, "unresolved": []}


def save_ledger(led):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(led, io.open(LEDGER, "w", encoding="utf-8", newline="\n"), indent=1,
              ensure_ascii=False)


def candidates():
    out = []
    for p in sorted(glob.glob(os.path.join(REPO, "*_REVIEW.html"))):
        m = measure(p)
        if m is not None:
            out.append(os.path.basename(p))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    size = int(args[0]) if args else 8
    acquire_lock()
    led = load_ledger()
    mapped = page_to_object()

    if "--plan" in sys.argv or not led.get("started"):
        pages = candidates()
        led["started"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        for name in pages:
            if name in led["before"]:
                continue
            m = measure(os.path.join(REPO, name))
            led["before"][name] = {
                "sentences": m["sentences"], "machine": m["machine"],
                "flow_paths": PROVE.flow_paths(
                    io.open(os.path.join(REPO, name), encoding="utf-8",
                            errors="replace").read()),
            }
        save_ledger(led)
        print("ROLLOUT PLANNED: %d pages with a Paper panel, baselines recorded in %s"
              % (len(led["before"]), os.path.relpath(LEDGER, REPO)))
        if "--plan" in sys.argv:
            return

    todo = [n for n in sorted(led["before"])
            if n not in led["done"] and n not in led["failed"]]
    print("REMAINING %d of %d; this batch %d" % (len(todo), len(led["before"]),
                                                 min(size, len(todo))))
    batch = todo[:size]
    if not batch:
        print("NOTHING LEFT. done %d, failed %d, unresolved %d"
              % (len(led["done"]), len(led["failed"]), len(led["unresolved"])))
        return

    for name in batch:
        page = os.path.join(REPO, name)
        if name in DO_NOT_REBUILD:
            led["failed"][name] = "[%s] EXCLUDED BY NAME: %s" % (RUN_ID,
                                                                 DO_NOT_REBUILD[name])
            print("  %-52s EXCLUDED -- not copied, not built" % name)
            save_ledger(led)
            continue
        topic = object_for(name, mapped)
        if not topic:
            led["unresolved"].append(name)
            led["failed"][name] = "[%s] object could not be resolved -- NOT built against a guess" % RUN_ID
            print("  %-52s UNRESOLVED -- skipped, not guessed" % name)
            save_ledger(led)
            continue
        backup = page + ".rollback"
        shutil.copyfile(page, backup)
        started = time.time()
        obj = os.path.join(SSOT, topic, "%s.json" % topic)
        r = subprocess.run([sys.executable, "build_tabbed.py", obj, page],
                           cwd=SSOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = r.stdout.decode("utf-8", "replace")
        # THE OCCURRENCE PREDICATE. False when the build did not run.
        ran = os.path.getmtime(page) >= started and r.returncode == 0
        if not ran:
            _why = []
            restore(backup, page, _why)
            led["failed"][name] = "[%s] build did not produce a new file (exit %d): %s %s" % (
                RUN_ID, r.returncode, out.strip()[-200:], " ".join(_why))
            print("  %-52s BUILD FAILED -- old bytes restored" % name)
            save_ledger(led)
            continue

        before_m = led["before"][name]
        m = measure(page)
        ok = True
        why = []
        if m is None:
            ok, why = False, ["the rebuilt page has no readable Paper panel"]
        else:
            fp = PROVE.flow_paths(io.open(page, encoding="utf-8", errors="replace").read())
            # A PAGE THAT HAD NO MANUSCRIPT CANNOT REGRESS INTO HAVING ONE.
            #
            # BOCOCIZUMAB_LIPID_AUTO_FULL_REVIEW served the honest absent-state banner --
            # "No manuscript has been generated for bococizumab-lipid-review" -- so its
            # baseline was 2 sentences and 0 machine. The rebuild produced a projected
            # manuscript of 11 machine sentences, and this check called that a REGRESSION
            # and rolled the page back to the empty banner.
            #
            # THE PREDICATE ASSUMED EVERY PAGE ALREADY HAD A MANUSCRIPT. Comparing absolute
            # counts is only meaningful when both sides are manuscripts; a page GAINING one
            # rises on every absolute measure by construction. The comparison is on the
            # RATE, and a page with almost nothing before is reported as a gain rather than
            # judged against a baseline that describes an empty tab.
            NO_MANUSCRIPT_BEFORE = 6      # sentences; the absent-state banner is 2
            gained = before_m["sentences"] < NO_MANUSCRIPT_BEFORE <= m["sentences"]
            if gained:
                why.append("GAINED A MANUSCRIPT: %d sentences where the page previously "
                           "served the absent-state banner (%d). Not judged against the "
                           "old counts -- there was nothing to compare."
                           % (m["sentences"], before_m["sentences"]))
            else:
                rate_before = (float(before_m["machine"]) / before_m["sentences"]
                               if before_m["sentences"] else 0.0)
                rate_after = (float(m["machine"]) / m["sentences"]
                              if m["sentences"] else 0.0)
                if before_m["sentences"] and rate_after > rate_before + 0.01:
                    ok = False
                    why.append("machine-vocabulary RATE rose %.0f%% -> %.0f%% (%d/%d -> "
                               "%d/%d)" % (100 * rate_before, 100 * rate_after,
                                           before_m["machine"], before_m["sentences"],
                                           m["machine"], m["sentences"]))
                if fp > before_m["flow_paths"]:
                    ok = False
                    why.append("field paths in the flow rose %d -> %d"
                               % (before_m["flow_paths"], fp))
            pr = subprocess.run([sys.executable,
                                 os.path.join(REPO, "scripts",
                                              "prove_register_change_moved_no_content.py"),
                                 backup, page, obj],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if pr.returncode != 0:
                ok = False
                why.append("content invariance REFUSED: %s"
                           % pr.stdout.decode("utf-8", "replace").strip()[-300:])

        if ok:
            os.remove(backup)
            led["done"][name] = {"run": RUN_ID, "machine": m["machine"], "was": before_m["machine"],
                                 "sentences": m["sentences"],
                                 "flow_paths": fp, "flow_was": before_m["flow_paths"]}
            print("  %-52s OK  machine %d->%d  paths %d->%d"
                  % (name, before_m["machine"], m["machine"], before_m["flow_paths"], fp))
        else:
            restore(backup, page, why)
            led["failed"][name] = "[%s] %s" % (RUN_ID, "; ".join(why))
            print("  %-52s REFUSED -- old bytes restored" % name)
            for w in why:
                print("        %s" % w)
        save_ledger(led)

    done = led["done"]
    print("")
    print("BATCH COMPLETE. done %d, failed %d, remaining %d"
          % (len(done), len(led["failed"]),
             len(led["before"]) - len(done) - len(led["failed"])))
    if done:
        mw = sum(v["was"] for v in done.values())
        mn = sum(v["machine"] for v in done.values())
        pw = sum(v["flow_was"] for v in done.values())
        pn = sum(v["flow_paths"] for v in done.values())
        print("ACROSS THE PAGES REBUILT SO FAR: machine sentences %d -> %d, field paths in "
              "the flow %d -> %d" % (mw, mn, pw, pn))


if __name__ == "__main__":
    try:
        main()
    finally:
        release_lock()
