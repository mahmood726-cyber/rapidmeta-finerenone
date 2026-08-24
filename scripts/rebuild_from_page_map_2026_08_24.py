"""Rebuild every page named in PAGE_MAP, sequentially, reporting per-page outcome.

THREE WORKERS, AND THE CAP IS THE POINT. Each build spawns a cold headless Chrome for every
uncached figure -- 21 seconds at best, a 90-second timeout at worst -- so a serial rebuild of
162 pages runs to roughly nine hours. A parallel run froze this machine earlier today, so the
worker count is held at three: enough to make the job tractable, few enough to bound the
number of browsers alive at once.

A BUILD THAT HAS TO BE WATCHED MUST PRINT AS IT GOES. A 0-byte log for forty-seven minutes
earlier today made a healthy job look dead and produced a 15.7-hour ETA for ninety minutes of
work. So: `write_through=True`, one line per page, flushed, and `as_completed` rather than
`map` -- `map` yields in SUBMISSION order, so a single slow page freezes the ledger while
dozens finish behind it, which is how that same job came to look stalled at 109 of 163.

Do not pipe this to `tail` or `head`: both buffer, and `head` closes the pipe early.
"""
import concurrent.futures as cf
import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RAW = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                        errors="replace", write_through=True)


class _Flushing(object):
    """write_through=True IS NOT ENOUGH, and this cost a second silent log today.

    `write_through` tells the TEXT layer not to buffer. The BufferedWriter underneath it
    still does, so a redirected run holds everything until the process exits -- which is
    how a rebuild that was healthily producing a page a minute showed a 0-byte log for
    twenty minutes, the same signature that made a 90-minute job look like 15.7 hours
    this morning. The wrapper has to flush the layer below it, explicitly, every line.
    """

    def write(self, s):
        _RAW.write(s)
        _RAW.flush()
        try:
            os.fsync(sys.stdout.fileno())
        except (OSError, ValueError):
            pass


OUT = _Flushing()


def build_one(args):
    i, total, page, src, dst = args
    if not os.path.exists(src):
        return page, None, "source object missing"
    try:
        # NO `text=True`. It decodes with the system codepage, which on this machine is
        # cp1252, and these builds print trial names and outcome text carrying characters
        # cp1252 cannot represent. A driver that dies decoding its child's output would
        # report a healthy build as a failure. Bytes out, explicit UTF-8 in, replace on the
        # way. `scripts/lint_subprocess_decode.py` refuses any new site that skips this.
        r = subprocess.run([sys.executable, os.path.join(REPO, "ssot", "build_tabbed.py"),
                            src, dst],
                           cwd=REPO, capture_output=True, timeout=900)
    except subprocess.TimeoutExpired:
        return page, None, "build exceeded 900s"
    if r.returncode == 0:
        return page, (os.path.getsize(dst) if os.path.exists(dst) else 0), None
    msg = (r.stderr or r.stdout or b"").decode("utf-8", "replace")
    return page, None, " ".join(msg.split())[-200:]


def main():
    pmap = json.load(io.open(os.path.join(REPO, "ssot", "PAGE_MAP.json"),
                             encoding="utf-8"))
    ok, failed = 0, []
    total = len(pmap)
    jobs = [(i, total, page,
             os.path.join(REPO, pmap[page].replace("/", os.sep)),
             os.path.join(REPO, page))
            for i, page in enumerate(sorted(pmap), 1)]

    # THREE WORKERS, NOT MORE. Each build spawns headless Chrome per uncached figure, and
    # a parallel run saturated this machine badly enough to freeze it earlier today. Three
    # keeps the browser count bounded while still turning a nine-hour serial rebuild into
    # about three. `as_completed`, not `map`: with `map` the ledger advances in SUBMISSION
    # order, so one slow page freezes the progress line while dozens finish behind it --
    # which is exactly how a healthy job looked dead earlier in this session.
    done = 0
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(build_one, j): j[2] for j in jobs}
        for fut in cf.as_completed(futs):
            done += 1
            page, size, err = fut.result()
            if err:
                failed.append((page, err))
                OUT.write("[%3d/%d] %-52s FAIL %s\n" % (done, total, page, err[:70]))
            else:
                ok += 1
                OUT.write("[%3d/%d] %-52s ok  %8d bytes\n" % (done, total, page, size))

    OUT.write("\nBUILT OK: %d of %d\n" % (ok, total))
    if failed:
        OUT.write("FAILED %d:\n" % len(failed))
        for page, why in failed:
            OUT.write("   %-52s %s\n" % (page, why[:150]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
