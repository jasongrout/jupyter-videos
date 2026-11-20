---
name: video-critic
description: Critique a rendered cut of a release video before the final render: sample its frames, brief a background agent as a producer of release videos, check its findings, and give the owner the ones to decide. Use when asked to critique, review or check a cut.
---

# A critic of a cut

The critic reads frames, not the video. It works from a brief, as an experienced producer of developer-tool release videos, and writes its findings for the owner to decide. `projects/4.7-release/critique-brief.md` is the brief of the first rough cut of 4.7.

## Steps

1. Sample the frames: `python cut/sample.py <cut.mp4> <folder>/frames --every 3`. It takes a frame every 3 s and one 1.2 s into each shot, and writes `frames.md` with the time, the shot and its title for each frame. Copy the cut's `.chapters.txt` into the folder.
2. Write the brief in the folder. Say what the video is (length, voice, music, the parts of a shot, the speed badges), who watches it (international, on phones, often with the sound off), and what it may read. Ask it to judge:
   - the first 10 seconds: does a viewer have a reason to stay?
   - pacing: shots that drag or rush, frames that look frozen, badges that confuse;
   - legibility at 1080p and on a phone;
   - each shot: does the frame show what its title claims when the viewer reads the title, and would a viewer know how to get the feature?
   - structure: the order of the shots and chapters, the cards;
   - honesty: anything a sceptical developer could read as staged.
3. Launch the critic as a background agent with a short prompt that names the brief. It reads only the frames, downloads nothing, calls no AI model, and writes only `findings.json` (at most 15 items: n, time, frame, severity, finding, suggestion) and `verdict.txt` (three sentences) into the folder.
4. Check each high finding against its frame yourself, and drop what the frame does not show.
5. Give the owner the findings in plain words, with the change you propose for each. The owner decides; change nothing that they have not accepted.

## The voice-over

For the narration, take one frame at the start of each line from the cut's `.plan.json` (`lines` of each part, with their start times), and check each line against its frame: the line plays while the screen shows what it describes, it does not read what the viewer can read, and the voice says each word as written (`voice/stt.py`).
