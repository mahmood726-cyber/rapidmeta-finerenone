"""Shared utilities for R-validation Python wrappers (P1-1, P1-2, P1-4, P1-5).

Single source of truth for:
  * RSCRIPT_EXE resolution (env → PATH → hardcoded fallback)
  * Path-traversal stem guard
  * Idempotency: SHA-256 sidecar (.input.sha256) — skip rerun when input
    + R-script mtime haven't changed
  * Concurrency: ProcessPoolExecutor (≤4 workers per lessons.md throttle rule)
  * stderr persistence: <REVIEW>.error.log on non-zero exit + always log
    non-empty stderr at WARN even on success
  * Schema validation: minimal contract check on _index.json and R-output JSON
"""
from __future__ import annotations
import concurrent.futures as _cf
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

# P1-3 fix: only wrap stdout once; idempotent against multiple imports.
if (sys.platform == "win32"
    and hasattr(sys.stdout, "buffer")
    and getattr(sys.stdout, "encoding", "").lower() != "utf-8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


RSCRIPT_EXE = (
    os.environ.get("RSCRIPT_EXE")
    or shutil.which("Rscript")
    or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
)

_STEM_OK = re.compile(r"^[A-Za-z0-9_.-]+$")


def stem_safe(s) -> bool:
    """P1-7: refuse path-traversal in review stems."""
    return isinstance(s, str) and bool(_STEM_OK.match(s)) and ".." not in s


def hash_input(payload: dict, r_script_path: Path) -> str:
    """SHA-256 of (canonicalised input JSON || R-script mtime)."""
    canon = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    mtime = str(int(r_script_path.stat().st_mtime)).encode("utf-8") if r_script_path.exists() else b"-"
    return hashlib.sha256(canon + b"|" + mtime).hexdigest()


def already_validated(out_json_path: Path, sha_sidecar: Path, expected_sha: str) -> bool:
    """P1-1 idempotency: skip rerun when output exists, parses, AND sidecar matches."""
    if not (out_json_path.exists() and sha_sidecar.exists()):
        return False
    try:
        if sha_sidecar.read_text().strip() != expected_sha:
            return False
        json.loads(out_json_path.read_text(encoding="utf-8"))
        return True
    except Exception:
        return False


def write_sidecar(sha_sidecar: Path, expected_sha: str) -> None:
    sha_sidecar.write_text(expected_sha, encoding="utf-8")


def run_rscript_one(args: tuple) -> dict:
    """Worker for the pool. args = (r_script, input_path, output_path,
    error_log_path)."""
    r_script, input_path, output_path, error_log_path = args
    try:
        result = subprocess.run(
            [RSCRIPT_EXE, str(r_script), str(input_path), str(output_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit": -1, "stderr": "timeout"}
    except FileNotFoundError:
        return {"ok": False, "exit": -2, "stderr": f"Rscript not found at {RSCRIPT_EXE}"}
    # P1-4: persist stderr on any non-empty content
    if result.stderr.strip():
        error_log_path.write_text(result.stderr, encoding="utf-8")
    return {"ok": result.returncode == 0 and output_path.exists(),
            "exit": result.returncode, "stderr": result.stderr[:500]}


def parallel_run(jobs: list, max_workers: int = 4, on_done: Callable | None = None) -> list:
    """Run R subprocesses in parallel. jobs = list of (r_script, in, out, err).
    P1-2: ProcessPoolExecutor with throttle ≤4 per lessons.md."""
    results = []
    workers = min(max_workers, max(1, (os.cpu_count() or 1) - 1), 4)
    with _cf.ProcessPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(run_rscript_one, jobs):
            results.append(r)
            if on_done: on_done(r)
    return results


def validate_index_entry(entry: dict) -> bool:
    """P1-5: minimal schema check on _index.json entries."""
    return (isinstance(entry, dict)
            and isinstance(entry.get("stem"), str)
            and isinstance(entry.get("has_realData"), bool)
            and stem_safe(entry["stem"]))


def validate_r_output(doc: dict) -> bool:
    """P1-5: minimal schema check on R wrapper output JSON."""
    if not isinstance(doc, dict):
        return False
    if "fit_ok" not in doc or not isinstance(doc["fit_ok"], bool):
        return False
    if "engine" not in doc or not isinstance(doc["engine"], str):
        return False
    return True
