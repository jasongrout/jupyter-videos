#!/bin/bash
# Record takes in order: run_takes.sh <port> <name>...
# Each take writes to $RV_TAKES/<name>/ and its log to $RV_TAKES/log-<name>.txt.
cd "$(dirname "$0")"
TAKES="${RV_TAKES:-${RV_WORK:-$(cd .. && pwd)/work}/takes}"
mkdir -p "$TAKES"
PORT=$1; shift
for name in "$@"; do
  start=$(date +%s)
  if timeout 240 node run_take.js "takes/$name.js" "$PORT" > "$TAKES/log-$name.txt" 2>&1; then
    echo "OK $name $(( $(date +%s) - start ))s $(grep -m1 '^take ' "$TAKES/log-$name.txt")"
  else
    echo "FAIL $name $(( $(date +%s) - start ))s: $(grep -m1 -A2 'TAKE FAILED\|Error' "$TAKES/log-$name.txt" | head -3 | tr '\n' ' ' | cut -c1-300)"
  fi
done
