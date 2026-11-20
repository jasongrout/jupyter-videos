#!/bin/bash
# Record takes of a project in order: run_takes.sh <project> <port> <name>...
# projects/<project>/takes/<name>.js records into $RV_TAKES/<name>/ (default: work/<project>/takes), with its log
# next to it in log-<name>.txt.
cd "$(dirname "$0")"
REPO="$(cd .. && pwd)"
PROJECT=$1; shift
PORT=$1; shift
TAKES="${RV_TAKES:-${RV_WORK:-$REPO/work/$PROJECT}/takes}"
mkdir -p "$TAKES"
for name in "$@"; do
  start=$(date +%s)
  if timeout 240 node run_take.js "$REPO/projects/$PROJECT/takes/$name.js" "$PORT" > "$TAKES/log-$name.txt" 2>&1; then
    echo "OK $name $(( $(date +%s) - start ))s $(grep -m1 '^take ' "$TAKES/log-$name.txt")"
  else
    echo "FAIL $name $(( $(date +%s) - start ))s: $(grep -m1 -A2 'TAKE FAILED\|Error' "$TAKES/log-$name.txt" | head -3 | tr '\n' ' ' | cut -c1-300)"
  fi
done
