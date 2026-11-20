#!/bin/bash
# Start a JupyterLab or Notebook server for the takes.
# Usage: start_server.sh <what> <port> [settings subfolder]
#   <what> is main (the build copy of setup/build_main.sh, served by the jupyter-lab of $JLAB_DEV_BIN),
#   a version with an environment in $RV_BASE/venv-<version> (4.6.6, 4.7.0b2),
#   or nb<name> for Jupyter Notebook from $RV_BASE/venv-nb<name> (nb77 for Notebook 7.7).
# Every server gets its own config, data, runtime and workspaces folders under $RV_BASE,
# and serves $RV_BASE/root (setup/make_demo.py writes it).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WHAT="$1"
PORT="$2"
BASE="${RV_BASE:-${RV_WORK:-$HERE/../work}/runtime}"
mkdir -p "$BASE"
BASE="$(cd "$BASE" && pwd)"
export RV_BASE="$BASE"
export RV_SETTINGS="${3:-settings}"
export RV_WORKSPACES="workspaces-$PORT"
export JUPYTER_CONFIG_DIR="$BASE/jupyter-config"
export JUPYTER_DATA_DIR="$BASE/jupyter-data-$WHAT"
export JUPYTER_RUNTIME_DIR="$BASE/jupyter-runtime-$PORT"
export IPYTHONDIR="$BASE/ipython"
export PS1='$ '
export MPLBACKEND=module://matplotlib_inline.backend_inline
mkdir -p "$JUPYTER_CONFIG_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_RUNTIME_DIR" "$IPYTHONDIR" "$BASE/$RV_SETTINGS" "$BASE/$RV_WORKSPACES"
cd "$BASE"
EXTRA=()
if [ "$WHAT" = main ]; then
  export PYTHONPATH="$BASE/main"
  BIN="${JLAB_DEV_BIN:-jupyter-lab}"
  EXTRA=(--dev-mode --LabApp.skip_dev_build=True)
elif [[ "$WHAT" == nb* ]]; then
  unset PYTHONPATH || true
  BIN="$BASE/venv-$WHAT/bin/jupyter-notebook"
else
  unset PYTHONPATH || true
  BIN="$BASE/venv-$WHAT/bin/jupyter-lab"
fi
LOG="$BASE/server-$PORT.log"
setsid "$BIN" "${EXTRA[@]}" --config="$HERE/jupyter_config.py" --port="$PORT" > "$LOG" 2>&1 < /dev/null &
echo "started pid $! log $LOG"
