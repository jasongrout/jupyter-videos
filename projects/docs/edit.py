"""Write the edit files of the documentation clips: one silent clip per edit, for a page of the docs.

Usage: python edit.py [<clip>...]

It writes $RV_WORK/edits/<clip>.json (default work/docs/edits/) for each clip, or for every clip in CLIPS. Then
`python cut/cut.py <edit> <out.gif>` renders one: the app fills the frame, with the pointer, the clicks and the key
caps, and no titles, badges or sound.

A clip names a take of this project, the span between two marks of it, the spans that play faster, and how to
export it: "crop" ([x, y, width, height] in CSS px of the take), "width" (px), "fps", "format" (gif, webm or mp4),
and "zoom" (the camera follows the focus marks of the take; off by default). "page" says where the clip goes in the
JupyterLab repository, so that a new clip can replace the old file.
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("RV_WORK", HERE.parents[1] / "work" / HERE.name))

CLIPS = {
    "4.7-reorder-sections": {
        "page": "docs/source/getting_started/changelog_assets/4.7-reorder-sections.gif",
        "take": "reorder-sections", "from": "beat:menu-0.5", "to": "beat:dropped+2.4",
        "clip": {"crop": [0, 28, 480, 592], "width": 480, "format": "gif"},
    },
    "4.7-undo-deleted-running-cell": {
        "page": "docs/source/getting_started/changelog_assets/4.7-undo-deleted-running-cell.gif",
        "take": "undo-deleted-running-cell", "from": "beat:run-0.4", "to": "beat:shown+1.8",
        "clip": {"width": 960, "format": "gif"},
    },
}


def main():
    names = sys.argv[1:] or list(CLIPS)
    out = WORK / "edits"
    out.mkdir(parents=True, exist_ok=True)
    for name in names:
        spec = dict(CLIPS[name])
        clip = spec.pop("clip")
        spec.pop("page")
        edit = {"work": str(WORK), "clip": clip, "sequence": [spec]}
        path = out / f"{name}.json"
        path.write_text(json.dumps(edit, indent=1) + "\n")
        print(path)


if __name__ == "__main__":
    main()
