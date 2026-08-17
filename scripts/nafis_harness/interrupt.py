"""The one idea taken from LangGraph: `interrupt()`. Nothing else.

LangGraph's durable pause is genuinely useful -- a run stops at a point that
needs a named human adjudication, and resumes later without losing its place.
This project already has such moments on the record: N1 was "overturned by named
human adjudication (Mahmood, 2026-08-12T13:30:45Z)", and the TWILIGHT and CANVAS
defects each end in "Decision required (do not guess)".

What is NOT taken is LangGraph's resume mechanism. Its replay re-executes the
graph, model calls included. Against a written ledger that is a downgrade paid
for in tokens: the ledger already holds the answer, and re-deriving it can
disagree with it -- which is the correction-is-less-reliable-than-the-original
failure, mechanised.

So resumption here reads the ledger. Zero model calls, zero network, append-only
JSONL, and a pending interrupt is a hard stop: `blocking_interrupts()` is
non-empty and the caller may not report a result past it.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Interrupt:
    interrupt_id: str
    raised_at: str
    reason: str
    options: tuple[str, ...]
    context: Mapping[str, Any]
    resolved_at: str | None = None
    resolved_by: str | None = None
    decision: str | None = None
    rationale: str = ""

    @property
    def pending(self) -> bool:
        return self.decision is None


class Ledger:
    """Append-only JSONL. The record is the state; nothing is re-derived."""

    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)

    def _append(self, obj: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, sort_keys=True, default=str) + "\n")

    def _read(self) -> list[dict]:
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    # ---------- api ----------------------------------------------------------

    def raise_interrupt(self, interrupt_id: str, reason: str,
                        options: Iterable[str], **context) -> Interrupt:
        itr = Interrupt(interrupt_id=interrupt_id, raised_at=_now(), reason=reason,
                        options=tuple(options), context=dict(context))
        self._append({"event": "raise", **asdict(itr)})
        return itr

    def resolve(self, interrupt_id: str, decision: str, resolved_by: str,
                rationale: str = "") -> None:
        """A decision is recorded verbatim and never re-derived on resume."""
        self._append({"event": "resolve", "interrupt_id": interrupt_id,
                      "decision": decision, "resolved_by": resolved_by,
                      "rationale": rationale, "resolved_at": _now()})

    def state(self) -> dict[str, Interrupt]:
        out: dict[str, Interrupt] = {}
        for rec in self._read():
            if rec.get("event") == "raise":
                out[rec["interrupt_id"]] = Interrupt(
                    interrupt_id=rec["interrupt_id"], raised_at=rec["raised_at"],
                    reason=rec["reason"], options=tuple(rec.get("options", ())),
                    context=rec.get("context", {}))
            elif rec.get("event") == "resolve":
                prev = out.get(rec["interrupt_id"])
                if prev is not None:
                    out[rec["interrupt_id"]] = Interrupt(
                        interrupt_id=prev.interrupt_id, raised_at=prev.raised_at,
                        reason=prev.reason, options=prev.options,
                        context=prev.context, resolved_at=rec["resolved_at"],
                        resolved_by=rec["resolved_by"], decision=rec["decision"],
                        rationale=rec.get("rationale", ""))
        return out

    def blocking_interrupts(self) -> list[Interrupt]:
        return [i for i in self.state().values() if i.pending]

    def may_report(self) -> tuple[bool, list[str]]:
        pend = self.blocking_interrupts()
        return (not pend, [f"{i.interrupt_id}: {i.reason}" for i in pend])
