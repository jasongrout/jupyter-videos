# Recorder

These four modules come from the author's whybook project (its `video/harness`, commit 8fede19 of 9 October 2026). Only their machine-specific defaults changed: ffmpeg comes from the PATH, and the browser from `browser.js`, which finds the newest build in Playwright's cache.

- `recorder.js` launches Chromium at a real device scale factor and records its screencast to an H.264 file while the take runs, with a timeline of marks next to it (`raw.mp4.timeline.jsonl`).
- `human.js` moves the pointer, clicks, types and drags like a person: eased paths, a typing speed, pauses. It logs every event, so the cut draws the pointer, the click ripples and the key caps.
- `regions.js` measures boxes of elements, for the focus marks that the camera follows.
- `browser.js` names the Chromium and the playwright-core that the takes use.
