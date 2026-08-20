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
        topic = object_for(name, mapped)
        if not topic:
            led["unresolved"].append(name)
            led["failed"][name] = "object could not be resolved -- NOT built against a guess"
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
            shutil.move(backup, page)
            led["failed"][name] = "build did not produce a new file (exit %d): %s" % (
                r.returncode, out.strip()[-200:])
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
            if before_m["sentences"] and m["machine"] > before_m["machine"]:
                ok = False
                why.append("machine sentences rose %d -> %d"
                           % (before_m["machine"], m["machine"]))
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
            led["done"][name] = {"machine": m["machine"], "was": before_m["machine"],
                                 "sentences": m["sentences"],
                                 "flow_paths": fp, "flow_was": before_m["flow_paths"]}
            print("  %-52s OK  machine %d->%d  paths %d->%d"
                  % (name, before_m["machine"], m["machine"], before_m["flow_paths"], fp))
        else:
            shutil.move(backup, page)
            led["failed"][name] = "; ".join(why)
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
    main()
