#!/usr/bin/env bash
# Gemini (agy) liveness probe with HONEST exit status.
#
# THE DEFECT THIS FIXES. `agy --print` returns exit 0 even when the call failed:
#     $ agy --print "..."
#     Error: Individual quota reached. ... Resets in 1h19m35s.
#     $ echo $?
#     0
# Observed four times on 2026-08-12. A probe that reports success while the call
# failed is a guard that cannot fail -- the fourth such we found in a single day
# -- and it means a dead Gemini is indistinguishable from a passing one. Any
# cross-family certification resting on it would be worthless.
#
# The fix cannot rely on the exit code, so it inspects the PAYLOAD: the model must
# name its own family. A liveness check that can only report "alive" is not a
# check; this one can only report alive if the answer contains a model name.
#
# Exit codes:
#   0  live, and the reply names a Gemini/Google model
#   4  quota exhausted (reply says so)
#   5  auth / permission failure
#   6  reply arrived but names no model -- indeterminate, treat as NOT live
#   7  transport failure, empty reply, or timeout
set -uo pipefail

PROMPT="${1:-Reply with exactly: OK followed by your model name and family. Nothing else.}"
TIMEOUT="${AGY_TIMEOUT:-240}"

OUT="$(timeout "$TIMEOUT" agy --print "$PROMPT" 2>&1)"
RC=$?

if [ $RC -eq 124 ] || [ -z "${OUT// /}" ]; then
    echo "agy_probe: NOT LIVE (timeout or empty reply after ${TIMEOUT}s)" >&2
    printf '%s\n' "$OUT" >&2
    exit 7
fi

low="$(printf '%s' "$OUT" | tr '[:upper:]' '[:lower:]')"

case "$low" in
    *"quota reached"*|*"quota exceeded"*|*"upgrade your subscription"*|*"resets in"*)
        echo "agy_probe: NOT LIVE -- quota exhausted" >&2
        printf '%s\n' "$OUT" >&2
        exit 4 ;;
    *"unauthor"*|*"not authenticated"*|*"permission denied"*|*"login"*|*"api key"*)
        echo "agy_probe: NOT LIVE -- auth failure" >&2
        printf '%s\n' "$OUT" >&2
        exit 5 ;;
esac

# The payload must name a model. "OK" alone is not evidence a model answered.
case "$low" in
    *gemini*|*google*)
        printf '%s\n' "$OUT"
        echo "agy_probe: LIVE (reply names a Gemini/Google model)" >&2
        exit 0 ;;
esac

echo "agy_probe: INDETERMINATE -- reply names no model; treating as NOT live" >&2
printf '%s\n' "$OUT" >&2
exit 6
