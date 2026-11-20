#!/bin/bash
# Add the kernel that the AI take's notebook asks for (python3-data) to the data folder of a server.
# Usage: add_data_kernel.sh <what> <python>
#   <what> is the server name of start_server.sh (4.7.0b2 for the AI take), and <python> an interpreter with
#   ipykernel and pandas: the environment of the server itself may have no pandas.
# The kernel shows as "Python 3 (ipykernel)", like the default one.
set -euo pipefail
WHAT="${1:?server name, such as 4.7.0b2}"
PY="${2:?a Python with ipykernel and pandas}"
BASE="${RV_BASE:-${RV_WORK:-$(cd "$(dirname "$0")/.." && pwd)/work}/runtime}"
K="$BASE/jupyter-data-$WHAT/kernels/python3-data"
mkdir -p "$K"
cat > "$K/kernel.json" <<EOF
{
 "argv": ["$PY", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
 "display_name": "Python 3 (ipykernel)",
 "language": "python",
 "metadata": {"debugger": true}
}
EOF
echo "wrote $K/kernel.json"
