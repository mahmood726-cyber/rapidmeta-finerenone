#!/usr/bin/env bash
# check.sh -- the single entry point. Run this, not the modules individually.
#
# `set -euo pipefail` is load-bearing, not boilerplate:
#   -e            a failing stage stops the run
#   -o pipefail   a failing stage stops the run EVEN WHEN PIPED, which is the
#                 exact bug that let a dead guard ship today: the exit code was
#                 read after a pipe, so it was always the tee's status, never
#                 the checker's.
# Nothing below pipes a checker. If you ever add `| tee`, pipefail is what
# keeps the status honest.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! "$PYTHON_BIN" -c "import sys" >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

fail=0
run () {
  local label="$1"; shift
  echo
  echo "### $label"
  if "$@"; then
    echo "### $label: OK"
  else
    local rc=$?
    echo "### $label: FAILED (exit $rc)"
    fail=1
  fi
}

run "static dead-guard audit"   "$PYTHON_BIN" mg_audit.py
run "adversarial suite"         "$PYTHON_BIN" mg_test.py
run "mutation self-check"       "$PYTHON_BIN" mg_mutate.py

echo
if [ "$fail" -ne 0 ]; then
  echo "SUITE FAILED"
  exit 1
fi
echo "SUITE PASSED -- every detector fires on a known-bad input, is quiet on a"
echo "known-good input, and every one of those assertions has been shown"
echo "capable of failing."
exit 0
