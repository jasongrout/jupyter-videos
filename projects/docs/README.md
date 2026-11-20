# Documentation clips

Short silent clips for the JupyterLab documentation, made from takes like the videos: the app fills the frame, with the drawn pointer, clicks and key caps, and no titles, badges or sound. A clip can be recorded again for each release, so that the animations of the docs show the current interface.

- `takes/` has the take scripts. A clip can reuse a take of a video: `reorder-sections.js` reuses the 4.7 shot under its own name.
- `edit.py` lists the clips: the take, the span between two of its marks, the crop, the width, the frame rate, the format, and the file of the JupyterLab repository that the clip replaces.

The takes and clips go to `work/docs/` (or `$RV_WORK`).

## Making a clip

Start the server of the version that the docs describe (see the [README](../../README.md)), then:

```bash
node harness/run_take.js projects/docs/takes/reorder-sections.js 8963
python projects/docs/edit.py 4.7-reorder-sections
python cut/cut.py work/docs/edits/4.7-reorder-sections.json work/docs/out/4.7-reorder-sections.gif --stills 1.0,5.0   # check frames first
python cut/cut.py work/docs/edits/4.7-reorder-sections.json work/docs/out/4.7-reorder-sections.gif
```

Then copy the GIF to the path in `edit.py` in a JupyterLab checkout. Any shot of a video can also become a clip: `python cut/cut.py <edit of the video> <out.gif> --clip --only <index of the shot>`.

## Animations to make again

These animations of the JupyterLab docs show an old interface:

- `docs/source/user/images/toc/toc.gif`, `runcell.gif`, `numberingH1.gif`, `syncCollapseState.gif` and `includeOutput.gif`, on the table of contents page (May 2022, 1280x716)
- `docs/source/user/images/debugger/step.gif`, on the debugger page (September 2020, 1200x800)
