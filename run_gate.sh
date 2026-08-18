set -o pipefail
cd /f/rapidmeta-ssot-shell
# RELAY, DO NOT MATCH. This harness truncated a gate's diagnostic TWICE -- once by a
# case-sensitive grep, once by a pattern that did not cover the message. A reporting
# layer that PARSES its source's output is a second route, and every multi-route value
# in this corpus has diverged. It now passes the gate's own words through whole.
p=0; w=0; f=0
: > .gate_failures.txt
while IFS=' ' read -r page obj kind; do
  page="${page%$'\r'}"; obj="${obj%$'\r'}"; kind="${kind%$'\r'}"
  [ -z "$page" ] && continue
  if [ "$kind" = "content" ]; then s=scripts/content_gate.py; else s=scripts/verdict_gate.py; fi
  if python "$s" "$page" "$obj" r4 > .g_one.txt 2>&1; then
    p=$((p+1))
  elif grep -q "STALE" .g_one.txt; then
    w=$((w+1)); echo "WAIT $page" | tee -a .gate_failures.txt
  else
    f=$((f+1))
    { echo "=== FAIL $page  [$kind]"; cat .g_one.txt; echo; } >> .gate_failures.txt
  fi
done < .gate_pairs.txt
echo "GATED PASS=$p WAIT=$w FAIL=$f"
echo "Every failure's message relayed WHOLE into .gate_failures.txt"
