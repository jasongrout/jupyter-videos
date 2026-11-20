"""Sample frames of a cut for a critic: python sample.py <cut.mp4> <out dir> [--every 3]

Takes a frame every --every seconds and one 1.2 s into each part, at 1280 px,
and writes frames.md: the time, the part and its on-screen title for each frame.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
cut, out = Path(sys.argv[1]), Path(sys.argv[2])
every = float(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else 3.0
plan = json.loads(Path(str(cut) + ".plan.json").read_text())
total = plan[-1]["start"] + plan[-1]["length"]
times = sorted({round(t * every, 2) for t in range(int(total / every) + 1)} | {round(p["start"] + min(1.2, p["length"] / 2), 2) for p in plan})
out.mkdir(parents=True, exist_ok=True)
rows = ["| frame | time | part | on screen |", "| --- | --- | --- | --- |"]
for t in times:
    if t >= total:
        continue
    part = next(p for p in plan if p["start"] <= t < p["start"] + p["length"])
    name = f"f-{t:07.2f}.jpg"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(cut), "-frames:v", "1", "-vf", "scale=1280:-2",
                    "-q:v", "3", str(out / name)], check=True)
    text = " / ".join(x for x in (part.get("kicker"), part.get("title"), part.get("sub")) if x)
    rows.append(f"| {name} | {int(t // 60)}:{t % 60:05.2f} | {part['what']} | {text} |")
(out / "frames.md").write_text("\n".join(rows) + "\n")
print(out / "frames.md", len(rows) - 2, "frames")
