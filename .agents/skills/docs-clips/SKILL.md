---
name: docs-clips
description: Make or remake short silent clips (GIF, WebM or MP4) for the documentation of JupyterLab, Notebook or JupyterLite with this repository: a take of a live server, cut without titles, badges or sound. Use when asked for a docs animation, to refresh outdated GIFs of the docs, or to turn a shot of a video into a clip.
---

# Documentation clips

`projects/docs/` holds the takes and the list of clips; its README has the commands. A clip shows what the page's text describes, in the same order, at a size that reads on the page.

## Steps

1. Read the page of the docs and look at the old animation: what it shows, its size, its length. Note the file that the clip replaces.
2. Start the server of the version that the page documents (`setup/start_server.sh`), and the demo files that the take needs.
3. Write the take in `projects/docs/takes/`, or reuse a take of a video under a new name. Probe the selectors first (`harness/probes/`). Mark beats where the clip starts and ends.
4. Record the take, then add the clip to `CLIPS` in `projects/docs/edit.py`: the span, a crop around the part of the interface that the text names, and the width of the old file.
5. Draw stills with `cut/cut.py <edit> <out> --stills ...` and look at the start, the middle and the end. Then render, and compare the new file with the old one: its size, its length and its weight.
6. Copy the clip into the JupyterLab checkout at the path in `edit.py`.

## Rules

- The clip shows the steps of the text, and nothing that the text does not mention.
- The camera stays still: the crop frames the subject. Set `"zoom": true` only when a small control must be read.
- Park the pointer on an empty area before keyboard steps, and at the end.
- Keep a GIF under about 1 MB: 10 frames per second, the width of the docs column, and a crop that leaves out the parts the text does not name.
- Use the light theme, unless the page is about themes.
- Name the take after the clip, so that the takes of different clips do not overwrite each other.
