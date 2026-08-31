# -*- coding: utf-8 -*-
"""FRAME CONTRACT PRECONDITION CHECKER.

REUSED, NOT REBUILT. The base-uniqueness precondition and the record_kind /
objectives_verbatim contract are the peer lane's, authored in
F:/claude-temp/pend/build_cardio_frame.py (the block printing
"PRECONDITION base-uniqueness ... HOLDS"). This module lifts that contract to
the consumer side, where it can refuse a frame it did not build, and adds the
one check the builder could not make about itself: that the frame is keyed by
CD BASE and not by TITLE.

WHY THE TITLE-KEY CHECK IS THE ONE THAT MATTERS HERE
  A title-keyed frame cannot be deduplicated (Cochrane retitles reviews across
  versions) and cannot be joined to any enumerable source. A consumer handed one
  will still produce counts. So the failure is silent, which is why it is
  REFUSED with its reason rather than warned about.

REFUSAL FORMAT -- the offending path and line FIRST, the rule second, the gate
third. Naming the accuser before the accused has cost this project a four-hour
standoff.
"""
import io, json, os, sys

# NO sys.stdout reassignment here. This is a library: a caller that has already
# wrapped stdout has its wrapper closed by the import. Documented trap, hit once
# while writing this file.

GATE = "rekey20/frame_contract.py"

REQUIRED = ("cd_base", "current_pubN", "title", "objectives_verbatim",
            "record_kind", "specialty", "provenance")


class FrameRefused(Exception):
    pass


def _refuse(path, lineno, rule):
    raise FrameRefused("%s:%s\n  rule: %s\n  found by: %s" % (path, lineno, rule, GATE))


def load_frame(path):
    """Return rows, or raise FrameRefused naming the offending path and line."""
    if not os.path.exists(path):
        _refuse(path, 0, "frame file does not exist")
    rows, seen = [], {}
    with io.open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError as e:
                _refuse(path, lineno, "row is not JSON (%s)" % e)

            # C1 -- every contract field present.
            for k in REQUIRED:
                if k not in r:
                    _refuse(path, lineno, "row is missing contract field %r; a frame "
                                          "missing %r is not this frame" % (k, k))

            # C2 -- THE KEY IS A CD BASE, NOT A TITLE.
            b = r["cd_base"]
            if not (isinstance(b, str) and len(b) == 8 and b[:2] == "CD" and b[2:].isdigit()):
                _refuse(path, lineno,
                        "cd_base %r is not a Cochrane base of the form CDdddddd. A frame keyed "
                        "by title cannot be deduplicated across versions and cannot be joined "
                        "to an enumerable source; it is REFUSED, not accepted with a warning"
                        % (b,))

            # C3 -- base-uniqueness (the peer lane's precondition, enforced at the consumer).
            if b in seen:
                _refuse(path, lineno,
                        "duplicate cd_base %s, first seen at line %d -- one row per base is the "
                        "frame contract" % (b, seen[b]))
            seen[b] = lineno

            # C4 -- null means UNOBTAINABLE and is never the empty string.
            o = r["objectives_verbatim"]
            if o is not None and not (isinstance(o, str) and o.strip()):
                _refuse(path, lineno,
                        "objectives_verbatim is %r -- null means UNOBTAINABLE from the source; "
                        "the empty string means the parser saw nothing and said so quietly. "
                        "They are different facts and only null is permitted" % (o,))

            # C5 -- record_kind is stated, because a protocol is a third kind of item.
            if r["record_kind"] not in ("review", "protocol", "unknown"):
                _refuse(path, lineno, "record_kind %r is not one of review/protocol/unknown"
                        % (r["record_kind"],))
            rows.append(r)
    if not rows:
        _refuse(path, 0, "frame holds no rows")
    return rows


def kinds(rows):
    from collections import Counter
    return Counter(r["record_kind"] for r in rows)
