# -*- coding: utf-8 -*-
"""Applied literally, the shared definition attributes 31 pages, not 141.

THE DEFINITION BOTH LANES ADOPTED: a page has a canonical object when it DECLARES that
object's identity in its served bytes. It is the right definition -- evidence a reader
receives, independent of either side's directory conventions. This measures how many pages
actually meet it.

  pages I classify HAS_STORE                144   == the denominator
  declare the store path ssot/<topic>/       25   17.4%
  contain the object's app_id string         31   21.5%
  either of those                            31   21.5%
  NEITHER -- no object identity in bytes    113   78.5%
  carry a build stamp                       138   95.8%

SO THE AGREED DEFINITION AND THE AGREED NUMBER ARE INCOMPATIBLE. 141 and 144 both rest on
inference -- a filename that resembles a directory, or a map that names a page. Only 31 pages
say what they are. That is not a residual disagreement to reconcile; it is the definition
being right and the corpus not meeting it.

AND THE PAGES ARE NOT SILENT, THEY ARE SILENT ABOUT THE WRONG THING. 138 of 144 carry a build
stamp naming the GENERATOR that must rebuild them. Almost none names the OBJECT they were
built from. The corpus records how a page was made and not what it is about, which is why
every attribution instrument on this project has had to guess, and why two lanes guessing
differently was the predictable outcome rather than an accident.

THE FIX IS ONE LINE IN THE GENERATOR, and it retires the whole class: emit the store path
beside the build stamp that is already there. Attribution then stops being inference for
every lane at once, no join is needed, and a page that cannot say what it is about becomes
visible as such instead of being silently assigned by whichever matcher ran.
"""
import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HERE)))


def declares(page, topic):
    """(path_declared, app_id_declared, stamped) for one page."""
    try:
        raw = open(page, "rb").read()
    except OSError:
        return (False, False, False)
    path_decl = ("ssot/%s/" % topic).encode() in raw
    app = None
    try:
        app = json.load(io.open("ssot/%s/%s.json" % (topic, topic),
                                encoding="utf-8")).get("app_id")
    except Exception:
        pass
    return (path_decl, bool(app) and str(app).encode() in raw, b"Generator build" in raw)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace",
                                  line_buffering=True)
    rows = json.load(io.open(r"F:\claude-temp\pend\has_store_144.json", encoding="utf-8"))
    c = collections.Counter()
    silent = []
    for r in rows:
        p, a, s = declares(r["page"], r["topic"])
        c["path"] += p
        c["app"] += a
        c["either"] += (p or a)
        c["stamp"] += s
        if not (p or a):
            silent.append(r["page"])
    n = len(rows)
    print("")
    print("WHAT THE ATTRIBUTED PAGES ACTUALLY DECLARE")
    print("")
    print("  pages                                    %4d  == the denominator" % n)
    print("  declare the store path ssot/<topic>/     %4d   %5.1f%%" % (c["path"], 100.0 * c["path"] / n))
    print("  contain the object's app_id              %4d   %5.1f%%" % (c["app"], 100.0 * c["app"] / n))
    print("  either                                   %4d   %5.1f%%" % (c["either"], 100.0 * c["either"] / n))
    print("  NEITHER: no object identity in bytes     %4d   %5.1f%%" % (n - c["either"], 100.0 * (n - c["either"]) / n))
    print("  carry a build stamp (the GENERATOR)      %4d   %5.1f%%" % (c["stamp"], 100.0 * c["stamp"] / n))
    print("")
    print("  A page that records how it was made and not what it is about forces every")
    print("  attribution instrument to guess. Two lanes guessing differently was the")
    print("  predictable outcome, not an accident.")
    print("")
    print("  silent about their object, first 10:")
    for s in silent[:10]:
        print("     %s" % os.path.basename(s))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
