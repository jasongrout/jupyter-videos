# Brief: critique the rough cut of the JupyterLab 4.7 release video

You are an experienced producer of software release videos (developer tools, data science), with a sharp eye for pacing, legibility and on-screen text. You review the first rough cut of the release video for JupyterLab 4.7, an open-source notebook IDE, from frames sampled out of its 1080p preview. You do not watch the video: you read frames.

## What the video is

- 2:34 long, 16:9, 1920x1080, music only (a placeholder track; ignore the music), no narration. Every feature is a shot of 5 to 15 seconds of a live JupyterLab, played by a script, with a title in the top left: a small orange kicker, a headline and sometimes a sub-line.
- The app window floats on a dark background at rest; a camera zooms into what changes, sometimes with a spotlight that dims the rest. A drawn pointer shows clicks as an orange ripple, and key presses show as key caps at the bottom centre.
- It opens on a race: JupyterLab 4.6 and 4.7 side by side run a notebook that logs 1,000 lines with links, with timers. Then a title card, then shots grouped in chapters (see chapters.txt), an "And more" card and an end card.
- Spans that only wait (a kernel restart, training epochs) play faster under a badge such as "2× speed". The race plays at 4× after 3.4 s, under a "4× speed" badge.
- The audience is international: data scientists, researchers, teachers and extension authors. Many will watch on a phone, many with the sound off.

## Materials (in the folder `frames/` next to this brief)

- `frames.md`: one row per sampled frame: the file, its time in the cut, the shot, and the title on screen.
- `f-*.jpg`: the frames, 1280 px wide, about every 3.5 seconds plus one 1.2 s into each shot.
- `chapters.txt`: the chapters.

Read `frames.md` first, then the frames in order. Do not draw other frames, do not open the video, do not download anything, and do not call any AI model.

## What to judge

1. The first 10 seconds: does a viewer have a reason to stay? Is the race readable at a glance?
2. Pacing: shots that drag or rush, frames that look frozen, badges that confuse.
3. Legibility at 1080p and on a phone: text too small at the moment it matters, a zoom that would help, a zoom that cuts off something the title talks about.
4. Each shot: does the frame show what its title claims, at the moment the viewer reads the title? Is the title right, short and plain? Would a viewer know how to get the feature (a setting to turn on, a shortcut)?
5. Structure: order of shots and chapters, the title card, "And more", the end card.
6. Honesty: anything a sceptical developer could read as staged or misleading.

## Report

Write `findings.json` in this folder (not in `frames/`): a JSON list, most important first, at most 15 items, each

    {"n": 1, "time": "0:12", "frame": "f-0011.60.jpg", "severity": "high|medium|low",
     "finding": "what a viewer experiences, in one or two plain sentences",
     "suggestion": "the concrete change: a different title, a cut, a zoom, a different order"}

Also write `verdict.txt` in this folder: three plain sentences on the whole. Use plain, short sentences; no em dashes or en dashes. Do not change any other file. Your final message: the three sentences of the verdict, then the five most important changes, one line each.
