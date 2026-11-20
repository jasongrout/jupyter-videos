"""A contact sheet of a take: one frame after each beat and focus mark.

Usage: python takesheet.py <take folder or name> [<out.png>] [--after 0.4]
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
TAKES = Path(os.environ.get("RV_TAKES", Path(os.environ.get("RV_WORK", Path(__file__).resolve().parents[1] / "work")) / "takes"))
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"


def frame_at(take_dir, t, width=720):
    out = subprocess.run(
        [FFMPEG, "-v", "error", "-ss", f"{max(0, t):.3f}", "-i", str(take_dir / "raw.mp4"), "-frames:v", "1",
         "-vf", f"scale={width}:-1", "-f", "image2pipe", "-vcodec", "png", "-"],
        capture_output=True, check=True).stdout
    from io import BytesIO
    return Image.open(BytesIO(out)).convert("RGB")


def main():
    name = sys.argv[1]
    # A take by its folder, or by its name in $RV_TAKES.
    d = Path(name) if Path(name).is_dir() else TAKES / name
    out = Path(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else d / "sheet.png"
    after = float(sys.argv[sys.argv.index("--after") + 1]) if "--after" in sys.argv else 0.4
    marks = [json.loads(l) for l in (d / "raw.mp4.timeline.jsonl").read_text().splitlines() if l.strip()]
    picks = [m for m in marks if m["kind"] in ("beat", "focus")]
    stop = next(m for m in marks if m["kind"] == "stop")
    picks.append({"t": stop["t"] - 0.6, "kind": "end", "name": ""})
    ims = []
    font = ImageFont.truetype(FONT, 20)
    for m in picks:
        im = frame_at(d, m["t"] + after)
        dr = ImageDraw.Draw(im)
        label = f'{m["t"]:.1f}s {m["kind"]} {m.get("name") or ""}'
        dr.rectangle((0, 0, 12 + dr.textlength(label, font=font), 30), fill=(0, 0, 0))
        dr.text((6, 3), label, font=font, fill=(255, 200, 80))
        ims.append(im)
    cols = 3
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), "white")
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out)
    print(out, len(ims), "frames")


if __name__ == "__main__":
    main()
