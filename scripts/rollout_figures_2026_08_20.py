"""Deliver the manuscript figures to every page with a Paper panel, in batches.

FOUR PREDICTIONS PER PAGE, STATED FROM THE OBJECT BEFORE THE BUILD AND CHECKED ON THE
BUILT BYTES AFTER IT. A batch report that measures only what it finds afterwards cannot
distinguish "built correctly" from "built something else".

    1. FIGURE SLOTS   -- how many <figure> elements the paper panel will carry.
    2. FORESTS DRAWN  -- how many of them carry a drawn plot.
    3. DECLINED       -- how many refuse IN PLACE, each with a stated reason. A declined
                         figure that vanishes instead of refusing is a failure, not a
                         smaller success.
    4. SECTION DELTA  -- the manuscript gains EXACTLY ONE section (Figures) and loses
                         none; and a page whose object holds no pooled outcome gains ZERO
                         figures.

CLASS 70 IS BAKED IN RATHER THAN RECOVERED FROM. Every page is restored from the last
KNOWN-GOOD COMMITTED copy before it is measured and before it is built, and restored from
git if the build is refused. The class says a guard comparing against what is DELIVERED
goes blind once a first failure has lowered the baseline -- it was hit live, hours after
being written, when a bad build of SGLT2_HF became the baseline the manuscript guard then
defended. Reaching for `git checkout` when a guard refuses makes it a thing recovered from.
Doing it before every build makes it a thing that CANNOT OCCUR.

A PAGE CARRYING UNCOMMITTED CHANGES IS SKIPPED AND NAMED, NEVER CHECKED OUT. Restoring
from git is only safe on a page whose current bytes are already committed; on any other it
would destroy work this rollout did not make. The safe direction is to refuse.

THE OCCURRENCE PREDICATE IS FALSE WHEN THE BUILD DID NOT RUN -- mtime against the recorded
start plus the exit status. A report that cannot tell "built and unchanged" from "never
built" is the class-44 defect.
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSOT = os.path.join(REPO, "ssot")
LEDGER = os.path.join(REPO, "outputs", "paper_figures_rollout.json")
LOCK = os.path.join(REPO, "outputs", ".paper_figures_rollout.lock")
RUN_ID = "%d@%s" % (os.getpid(), time.strftime("%H%M%S"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SSOT)
import lint_paper_reads_as_prose as L                  # noqa: E402
import paper_projector as ppj                          # noqa: E402

# THE LIST MOVED TO ssot/do_not_rebuild.py, AND THE CHECK MOVED INTO THE BUILDER.
#
# It lived here and in scripts/rebuild_paper_corpus_2026_08_20.py -- two copies, which
# audit_standing_instructions.py had already flagged. Two copies means a THIRD caller
# inherits neither, and build_tabbed.py invoked directly was exactly that: both pages
# ever wrongly rebuilt went through it and it knew about no list at all.
sys.path.insert(0, os.path.join(REPO, "ssot"))
from do_not_rebuild import PAGES as DO_NOT_REBUILD          # noqa: E402

FIG_RE = re.compile(r"(?is)<figure>(.*?)</figure>")
FOREST_RE = re.compile(r'aria-label="Forest plot')


def sh(args):
    return subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)


def acquire_lock():
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError:
        held = ""
        try:
            held = io.open(LOCK, encoding="utf-8").read().strip()
        except Exception:
            pass
        sys.exit("REFUSED: a figure rollout is already running (%s). Two rollouts sharing "
                 "one ledger is how two correctly-built pages were rolled back earlier "
                 "tonight: each process holds the ledger in memory and rewrites it." % held)
    os.write(fd, RUN_ID.encode("utf-8"))
    os.close(fd)


def release_lock():
    if os.path.exists(LOCK):
        try:
            os.remove(LOCK)
        except OSError:
            pass


def load_ledger():
    if os.path.exists(LEDGER):
        return json.load(io.open(LEDGER, encoding="utf-8"))
    return {"started": None, "predicted": {}, "done": {}, "failed": {}, "skipped": {}}


def save_ledger(led):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    json.dump(led, io.open(LEDGER, "w", encoding="utf-8", newline="\n"), indent=1,
              ensure_ascii=False)


def is_clean(page):
    """Are this page's bytes on disk exactly what is committed?"""
    r = sh(["git", "status", "--porcelain", "--", page])
    return not r.stdout.decode("utf-8", "replace").strip()


def restore_from_git(page):
    sh(["git", "checkout", "--", page])


def panel_of(html):
    i = html.find('id="pn-paper"')
    if i < 0:
        return ""
    j = html.find('<section class="panel"', i + 10)
    return html[i:j if j > 0 else len(html)]


def observe(path):
    """What the built page actually carries: slots, drawn, declined, sections."""
    html = io.open(path, encoding="utf-8", errors="replace").read()
    p = panel_of(html)
    blocks = FIG_RE.findall(p)
    drawn = len([b for b in blocks if FOREST_RE.search(b) or "<svg" in b])
    declined = [b for b in blocks if "<svg" not in b]
    reasoned = len([b for b in declined if "not drawn." in b])
    return {"slots": len(blocks), "drawn": drawn, "declined": len(declined),
            "declined_with_reason": reasoned,
            "sections": len(re.findall(r"(?i)<h3", p))}


def predict(topic):
    """From the OBJECT, before the build. Returns None if the object cannot be read."""
    path = os.path.join(SSOT, topic, "%s.json" % topic)
    try:
        obj = json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return None
    figs = []
    for s in ppj.project(obj):
        if getattr(s, "key", None) == "figures":
            figs = list(getattr(s, "figures", []))
    drawn = len([f for f in figs if f[2]])
    has_outcome = bool(((obj.get("results") or {}).get("by_outcome") or {}))
    return {"slots": len(figs), "drawn": drawn, "declined": len(figs) - drawn,
            "has_outcome": has_outcome}


def candidates():
    out = []
    for p in sorted(glob.glob(os.path.join(REPO, "*_REVIEW.html"))):
        try:
            readable = L.measure(p) is not None
        except Exception:
            readable = False
        if readable:
            out.append(os.path.basename(p))
    return out


def main():
    import rebuild_paper_corpus_2026_08_20 as R
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    size = int(args[0]) if args else 10
    acquire_lock()
    led = load_ledger()
    mapped = R.page_to_object()

    if not led.get("started"):
        led["started"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        for name in candidates():
            if name in DO_NOT_REBUILD:
                led["skipped"][name] = DO_NOT_REBUILD[name]
                continue
            topic = R.object_for(name, mapped)
            if not topic:
                led["skipped"][name] = ("object could not be resolved -- NOT built against "
                                        "a guess")
                continue
            pr = predict(topic)
            if pr is None:
                led["skipped"][name] = "object does not parse"
                continue
            pr["topic"] = topic
            led["predicted"][name] = pr
        save_ledger(led)
        print("ROLLOUT PLANNED: %d pages, %d skipped by name or resolution"
              % (len(led["predicted"]), len(led["skipped"])))
        tot_d = sum(v["drawn"] for v in led["predicted"].values())
        tot_s = sum(v["slots"] for v in led["predicted"].values())
        print("PREDICTED ACROSS THE ROLLOUT: %d figure slots, %d forests drawn, %d declined"
              % (tot_s, tot_d, tot_s - tot_d))
        if "--plan" in sys.argv:
            return 0

    todo = [n for n in sorted(led["predicted"])
            if n not in led["done"] and n not in led["failed"]]
    print("REMAINING %d of %d; this batch %d"
          % (len(todo), len(led["predicted"]), min(size, len(todo))))
    batch = todo[:size]
    if not batch:
        print("NOTHING LEFT. done %d, failed %d" % (len(led["done"]), len(led["failed"])))
        return 0

    for name in batch:
        page = os.path.join(REPO, name)
        pr = led["predicted"][name]
        topic = pr["topic"]

        # CLASS 70, BAKED IN. Build from the last KNOWN-GOOD COMMITTED copy, never from
        # whatever is on disk -- which may be an earlier bad build of this same rollout.
        if not is_clean(page):
            led["failed"][name] = ("[%s] the page carries UNCOMMITTED changes. Restoring it "
                                   "from git would destroy work this rollout did not make, "
                                   "so it is skipped and named." % RUN_ID)
            print("  %-52s SKIPPED -- uncommitted changes, not overwritten" % name)
            save_ledger(led)
            continue
        restore_from_git(page)                      # no-op when clean; the guarantee is
        before = observe(page)                      # that the baseline IS the committed copy

        # ALREADY DELIVERED. SGLT2_HF was built and pushed before this rollout existed, and
        # a re-run would fail PREDICTION 4 -- its section count cannot rise by one again
        # because the Figures section is already there. Recorded as delivered rather than
        # rebuilt, which also makes the rollout resumable without re-doing finished pages.
        # The test is exact equality with the prediction on a COMMITTED page, so a page that
        # merely happens to carry some figures cannot pass through here.
        if before["slots"] == pr["slots"] and before["slots"] > 0:
            led["done"][name] = {"run": RUN_ID, "topic": topic, "slots": before["slots"],
                                 "drawn": before["drawn"], "declined": before["declined"],
                                 "sections": "already delivered, not rebuilt"}
            print("  %-52s ALREADY DELIVERED  %d slots, %d drawn"
                  % (name, before["slots"], before["drawn"]))
            save_ledger(led)
            continue

        head_copy = os.path.join(REPO, "outputs", ".head_%s" % name)
        r0 = sh(["git", "show", "HEAD:%s" % name])
        io.open(head_copy, "wb").write(r0.stdout)

        started = time.time()
        obj = os.path.join(SSOT, topic, "%s.json" % topic)
        r = subprocess.run([sys.executable, "build_tabbed.py", obj, page], cwd=SSOT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = r.stdout.decode("utf-8", "replace")
        ran = os.path.exists(page) and os.path.getmtime(page) >= started and r.returncode == 0
        if not ran:
            restore_from_git(page)
            led["failed"][name] = ("[%s] build did not produce a new file (exit %d): %s"
                                   % (RUN_ID, r.returncode, out.strip()[-220:]))
            print("  %-52s BUILD FAILED -- restored from git" % name)
            save_ledger(led)
            continue

        after = observe(page)
        why = []
        if after["slots"] != pr["slots"]:
            why.append("PREDICTION 1 MISSED: %d figure slots predicted, %d present"
                       % (pr["slots"], after["slots"]))
        if after["drawn"] != pr["drawn"]:
            why.append("PREDICTION 2 MISSED: %d forests predicted drawn, %d drawn"
                       % (pr["drawn"], after["drawn"]))
        if after["declined"] != pr["declined"]:
            why.append("PREDICTION 3 MISSED: %d declined predicted, %d present"
                       % (pr["declined"], after["declined"]))
        if after["declined"] != after["declined_with_reason"]:
            why.append("A DECLINED FIGURE CARRIES NO REASON: %d declined, %d with a reason"
                       % (after["declined"], after["declined_with_reason"]))
        if after["sections"] != before["sections"] + 1:
            why.append("PREDICTION 4 MISSED: sections %d -> %d, expected exactly +1"
                       % (before["sections"], after["sections"]))
        if (after["slots"] == 0) != (not pr["has_outcome"]):
            why.append("THE DEGENERATE CASE: figures %d on a page whose object %s a pooled "
                       "outcome" % (after["slots"],
                                    "HAS" if pr["has_outcome"] else "has NO"))
        inv = subprocess.run(
            [sys.executable, os.path.join(REPO, "scripts",
                                          "prove_register_change_moved_no_content.py"),
             head_copy, page, obj, "--content-change"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if inv.returncode != 0:
            why.append("content invariance REFUSED: %s"
                       % inv.stdout.decode("utf-8", "replace").strip()[-260:])
        if os.path.exists(head_copy):
            os.remove(head_copy)

        if why:
            restore_from_git(page)
            led["failed"][name] = "[%s] %s" % (RUN_ID, "; ".join(why))
            print("  %-52s REFUSED -- restored from git" % name)
            for w in why:
                print("        %s" % w)
        else:
            led["done"][name] = {"run": RUN_ID, "topic": topic, "slots": after["slots"],
                                 "drawn": after["drawn"], "declined": after["declined"],
                                 "sections": "%d->%d" % (before["sections"],
                                                         after["sections"])}
            print("  %-52s OK  %d slots, %d drawn, %d declined, sections %d->%d"
                  % (name, after["slots"], after["drawn"], after["declined"],
                     before["sections"], after["sections"]))
        save_ledger(led)

    d = led["done"]
    print("")
    print("BATCH COMPLETE. done %d, failed %d, remaining %d"
          % (len(d), len(led["failed"]),
             len(led["predicted"]) - len(d) - len(led["failed"])))
    print("DELIVERED SO FAR: %d figure slots, %d forests drawn, %d declined in place"
          % (sum(v["slots"] for v in d.values()), sum(v["drawn"] for v in d.values()),
             sum(v["declined"] for v in d.values())))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        release_lock()
