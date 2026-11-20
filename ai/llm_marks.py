"""Put the model's answer into the AI take's timeline, and measure its speed without the recorder.

Usage: python llm_marks.py <take folder> [replays]

The take marks the wall-clock time when it sends the question ("wall"), and local_llm_server.py writes the wall-clock
times of each answer (received, first token, done). This script adds marks llm:received, llm:first and llm:done to
the take's timeline. It takes the replays of the same request sent after the take, or sends the request again until
there are `replays` of them (3 by default), with the prompt cache cleared before each. It writes the median length of
each phase to <take folder>/llm-speed.json, and the cut plays each phase of the recorded answer at the speed that
makes it as long as without the recorder.
"""

import json
import os
import statistics
import sys
import urllib.request
from pathlib import Path

LOG = Path(os.environ.get("LLM_REQUEST_LOG", Path(os.environ.get("RV_BASE", Path(__file__).resolve().parents[1] / "work/runtime")) / "llm-requests"))
URL = os.environ.get("LLM_URL", "http://localhost:8080/v1") + "/chat/completions"


def post(body):
    request = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=900) as response:
        return response.read()


def timings():
    return {f.name[:3]: json.loads(f.read_text()) for f in LOG.glob("*.timing.json")}


def main():
    take = Path(sys.argv[1])
    replays = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    timeline = take / "raw.mp4.timeline.jsonl"
    marks = [json.loads(line) for line in timeline.read_text().splitlines() if line.strip()]
    marks = [m for m in marks if m["kind"] != "llm"]
    wall = next(m for m in marks if m["kind"] == "wall")
    # The answer of the take is the first one that the server received after the question was sent.
    number, recorded = min(((n, t) for n, t in timings().items() if t["received"] >= wall["epoch"] - 0.5), key=lambda nt: nt[1]["received"])
    for name in ("received", "first", "done"):
        marks.append({"t": round(wall["t"] + recorded[name] - wall["epoch"], 3), "kind": "llm", "name": name})
    timeline.write_text("".join(json.dumps(m) + "\n" for m in marks))
    request = json.loads((LOG / f"{number}.json").read_text())
    # Replays sent right after the take, with the same request, count first.
    done = sorted(n for n in timings() if n > number and json.loads((LOG / f"{n}.json").read_text()) == request)[:replays]
    waits = [timings()[n]["first"] - timings()[n]["received"] for n in done]
    streams = [timings()[n]["done"] - timings()[n]["first"] for n in done]
    for _ in range(replays - len(done)):
        # A different prompt clears the prompt cache, as in the setup of the take.
        post({"messages": [{"role": "system", "content": "Say hi."}, {"role": "user", "content": "Hi"}], "max_tokens": 1})
        before = set(timings())
        post(request)
        replay = timings()[max(set(timings()) - before)]
        waits.append(replay["first"] - replay["received"])
        streams.append(replay["done"] - replay["first"])
    speed = {
        "request": number,
        "recorded": {"wait": round(recorded["first"] - recorded["received"], 3), "stream": round(recorded["done"] - recorded["first"], 3)},
        "replays": {"wait": [round(w, 3) for w in waits], "stream": [round(s, 3) for s in streams]},
        "without_recorder": {"wait": round(statistics.median(waits), 3), "stream": round(statistics.median(streams), 3)},
    }
    speed["x"] = {phase: round(speed["recorded"][phase] / speed["without_recorder"][phase], 3) for phase in ("wait", "stream")}
    (take / "llm-speed.json").write_text(json.dumps(speed, indent=1) + "\n")
    print(json.dumps(speed))


main()
