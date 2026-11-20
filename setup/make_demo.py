"""Write the demo project that the release video takes open.

Usage: python make_demo.py <root>

One theme runs through the files: a small study of weather stations. The
logs notebook is the case of issue #16957 that the 4.7 release notes measured
(1,000 log lines with links), kept as it was so that the numbers compare.
"""

import json
import os
import stat
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(sys.argv[1])
# The Python that runs the demo notebooks once, to store their outputs: it needs pandas and matplotlib.
PY = os.environ.get("DEMO_PYTHON", sys.executable)


def notebook(cells, kernel=True, hint="nb"):
    out = {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    if kernel:
        out["metadata"] = {
            "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        }
    for i, (kind, source, *extra) in enumerate(cells):
        meta = dict(extra[0]) if extra else {}
        cell = {
            "cell_type": kind,
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{hint}/{i}")),
            "metadata": meta,
            "source": source,
        }
        if kind == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        out["cells"].append(cell)
    return out


def write_nb(path, cells, execute=False, kernel=True):
    if path.exists():
        path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    path.write_text(json.dumps(notebook(cells, kernel, path.name), indent=1) + "\n")
    if execute:
        subprocess.run(
            [PY, "-m", "nbconvert", "--to", "notebook", "--execute", "--inplace", str(path)],
            check=True,
            cwd=str(path.parent),
            capture_output=True,
        )


ROOT.mkdir(parents=True, exist_ok=True)
for sub in ("data", "notes", "results"):
    (ROOT / sub).mkdir(exist_ok=True)

STATIONS = ["Lisbon", "Oslo", "Reykjavik", "Vienna", "Madrid"]

# Daily temperatures of five stations, a smooth seasonal curve plus a fixed wobble.
rows = []
import math

for day in range(1, 31):
    for k, station in enumerate(STATIONS):
        base = [19.5, 7.8, 5.1, 11.2, 17.4][k]
        temp = base + 2.4 * math.sin((day + 3 * k) / 4.0) - 0.06 * day
        rain = max(0.0, 4.0 * math.sin((day * (k + 2)) / 3.1) - 1.2)
        rows.append((f"2026-10-{day:02}", station, round(temp, 1), round(rain, 1)))

lines = [
    "# Weather station measurements, October 2026",
    "# temperature in degrees Celsius, rainfall in mm",
    "date,station,temperature,rainfall",
]
for i, (date, station, temp, rain) in enumerate(rows):
    if i == 17:
        lines.append("# Oslo sensor recalibrated on 2026-10-04")
    lines.append(f"{date},{station},{temp},{rain}")
(ROOT / "data" / "measurements.csv").write_text("\n".join(lines) + "\n")

load = (
    "import pandas as pd\n"
    "\n"
    'weather = pd.read_csv("data/measurements.csv", comment="#", parse_dates=["date"])\n'
    "weather.head()"
)
plot = (
    "import matplotlib.pyplot as plt\n"
    "\n"
    "fig, ax = plt.subplots(figsize=(7, 3.2))\n"
    'for station, group in weather.groupby("station"):\n'
    '    ax.plot(group["date"], group["temperature"], label=station, linewidth=2)\n'
    'ax.set_ylabel("Temperature (°C)")\n'
    'ax.legend(ncols=5, loc="upper center", bbox_to_anchor=(0.5, 1.18), frameon=False)\n'
    'ax.spines[["top", "right"]].set_visible(False)\n'
    "fig.autofmt_xdate()"
)
write_nb(
    ROOT / "stations.ipynb",
    [
        ("markdown", "# Weather stations\n\nDaily temperatures of five European stations in October 2026."),
        ("code", load),
        ("code", plot),
        ("markdown", "## Warmest days\n\nThe three warmest days of each station."),
        ("code", 'weather.sort_values("temperature", ascending=False).groupby("station").head(3)'),
    ],
    execute=True,
)

write_nb(
    ROOT / "report.ipynb",
    [
        ("markdown", "# October report\n\nThis notebook is shared read-only."),
        ("code", load),
        ("code", plot),
    ],
    execute=True,
)
(ROOT / "report.ipynb").chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

write_nb(
    ROOT / "exercise.ipynb",
    [
        (
            "markdown",
            "# Exercise 1\n\nWrite the body of `mean()`. The instructions and the tests are locked.",
            {"editable": False, "deletable": False},
        ),
        ("code", 'def mean(values):\n    """Return the arithmetic mean of values."""\n    ...'),
        (
            "code",
            "assert mean([2, 4]) == 3\nassert mean([1, 2, 3, 4]) == 2.5\nprint(\"All tests passed\")",
            {"editable": False, "deletable": False},
        ),
    ],
)

write_nb(
    ROOT / "help.ipynb",
    [
        ("code", "import statistics"),
        ("code", ""),
    ],
)

download = (
    "import time\n"
    "\n"
    f"stations = {STATIONS!r}\n"
    "for i, station in enumerate(stations, 1):\n"
    "    time.sleep(1.2)\n"
    '    print(f"Downloaded {station} ({i}/{len(stations)})")'
)
write_nb(
    ROOT / "download.ipynb",
    [
        ("markdown", "# Update the data"),
        ("code", download),
        ("code", 'print("Data ready")'),
    ],
)

write_nb(
    ROOT / "debugging.ipynb",
    [
        (
            "code",
            "import numpy as np\n"
            "import pandas as pd\n"
            "from dateutil import parser\n"
            "\n"
            "def warmest(values):\n"
            "    series = pd.Series(values)\n"
            "    return float(np.max(series))",
        ),
        ("code", "warmest([7.8, 5.1, 11.2, 17.4, 19.5])"),
    ],
)

write_nb(
    ROOT / "input.ipynb",
    [("code", 'station = input("Which station?")\nprint(f"Loading {station}")')],
)

mermaid = (
    "## How the data flows\n"
    "\n"
    "```mermaid\n"
    "flowchart LR\n"
    "    A[Stations] --> B[Measurements CSV]\n"
    "    B --> C[Notebook]\n"
    "    C --> D[Report]\n"
    "    C --> E[Plots]\n"
    "```"
)
math_md = (
    "## Dew point\n"
    "\n"
    "The Magnus formula gives the dew point $T_d$ from the temperature $T$ and the relative humidity $RH$:\n"
    "\n"
    "$$\n"
    "\\gamma = \\ln\\left(\\frac{RH}{100}\\right) + \\frac{b\\,T}{c + T} \\\\\n"
    "T_d = \\frac{c\\,\\gamma}{b - \\gamma}\n"
    "$$\n"
    "\n"
    "Over a day, the temperature follows a few harmonics of the daily cycle, "
    "$T(t) = T_0 + a_1 \\sin(\\omega t) + b_1 \\cos(\\omega t) + a_2 \\sin(2 \\omega t) + b_2 \\cos(2 \\omega t) "
    "+ a_3 \\sin(3 \\omega t) + b_3 \\cos(3 \\omega t) + a_4 \\sin(4 \\omega t) + b_4 \\cos(4 \\omega t) "
    "+ a_5 \\sin(5 \\omega t) + b_5 \\cos(5 \\omega t)$, with $\\omega = 2\\pi / 24\\,\\mathrm{h}$."
)
write_nb(
    ROOT / "pipeline.ipynb",
    [("markdown", mermaid), ("markdown", math_md)],
    kernel=False,
)

(ROOT / "notes" / "small-angles.md").write_text(
    "# Small-angle approximation\n"
    "\n"
    "For small angles in radians, $\\sin\\theta \\approx \\theta$ and\n"
    "$\\cos\\theta \\approx 1 - \\theta^2/2$. Dividing the two gives\n"
    "\n"
    "$$\n"
    "\\tan\\theta = \\frac{\\sin\\theta}{\\cos\\theta} \\approx \\theta\n"
    "$$\n"
    "\n"
    "The error of $\\sin\\theta \\approx \\theta$ stays below 1% for angles up to 0.24 rad.\n"
)

(ROOT / "README.md").write_text(
    "# Weather analysis\n"
    "\n"
    "Notebooks and data for the weather station study.\n"
    "\n"
    "The measurements are in [the data folder](data/), and the plots go to\n"
    "[the results folder](results/).\n"
)

(ROOT / "fibonacci.jl").write_text(
    '"""\n'
    "    fibonacci(n)\n"
    "\n"
    "Return the first `n` Fibonacci numbers.\n"
    '"""\n'
    "function fibonacci(n::Integer)\n"
    "    numbers = zeros(BigInt, n)\n"
    "    a, b = big(0), big(1)\n"
    "    for i in 1:n\n"
    "        numbers[i] = a\n"
    "        a, b = b, a + b\n"
    "    end\n"
    "    return numbers\n"
    "end\n"
)

(ROOT / "analysis.R").write_text(
    "library(dplyr)\n"
    "\n"
)

n_logs = 1000
logs_source = (
    "import logging\n"
    "from IPython.display import Pretty\n"
    "\n"
    "logging.basicConfig(level=logging.INFO, force=True)\n"
    f'progress = display(Pretty("Saved 0 of {n_logs} files"), display_id=True)\n'
    f"for i in range(1, {n_logs + 1}):\n"
    '    logging.info(f"Saved https://example.com/{i:04}.csv to /tmp/{i:04}.csv")\n'
    "    if i % 10 == 0:\n"
    f'        progress.update(Pretty(f"Saved {{i}} of {n_logs} files"))'
)
write_nb(
    ROOT / "logs.ipynb",
    [("code", logs_source, {"scrolled": True}), ("code", 'print("All parts saved")')],
)

(ROOT / "train.py").write_text(
    '"""Train the model and show the progress in the terminal title."""\n'
    "\n"
    "import sys\n"
    "import time\n"
    "\n"
    "EPOCHS = 10\n"
    "\n"
    "for epoch in range(1, EPOCHS + 1):\n"
    '    sys.stdout.write(f"\\033]0;Training: epoch {epoch}/{EPOCHS}\\007")\n'
    '    print(f"epoch {epoch}/{EPOCHS}: loss {0.9 / epoch:.2f}", flush=True)\n'
    "    time.sleep(1.5)\n"
)

print("demo files in", ROOT)
