---
name: release-video
description: Plan, record, voice and cut a release video of JupyterLab, Notebook or JupyterLite with this repository (scripted Playwright takes of live servers, narration by ElevenLabs through OpenRouter or by Piper for drafts, a 1080p cut at 60 fps). Use when asked for a new release video, a new or changed shot, a change of the narration, cards or music, or a fix to a cut.
---

# Release videos of Jupyter

The README describes each folder and the commands. This skill is the order of work and what the earlier videos taught. A video is a project in `projects/<name>/`: its takes, its `edit.py`, its plan and its notes. `projects/4.7-release/` is the first video.

## Steps

1. **Plan.** List what the release merged (`tools/fetch_milestone.py`) and read the release notes. Pick the changes that show well in a few seconds, and order them as the notes do. Make the project folder after the layout of `projects/4.7-release/`, and write its `plan.md`: a table of shots (start, shot, what the viewer sees, pull request), then the voice, the music and the open decisions.
2. **Servers.** Build `main` with `setup/build_main.sh`, make environments for released versions, write the demo files with `setup/make_demo.py`, and start one server per version with `setup/start_server.sh`. Copy `setup/settings-template/` into the settings folder of the takes.
3. **Probes.** Before a take relies on a selector, a click or a style, answer the question with a probe (`harness/probes/`), and look at its screenshots.
4. **Takes.** One script per shot in the project's `takes/`: `setup()` is not recorded, `run()` is. Mark beats (`take.beat`) where lines and cuts attach, and focus boxes (`take.focus`) for the camera. Record each take as a tracked background job, then draw a sheet of it (`cut/takesheet.py`) and look at every frame.
5. **Edit.** The project's `edit.py` writes the edit file: the cards (from `cut/cards.py`), the segments of takes between beats, speed pieces, titles and the narration lines, each tied to a beat.
6. **Voice.** `voice/el_voice.py` voices new lines with ElevenLabs through OpenRouter; it prints what the key has spent before and after, and the owner sets the budget. `voice/voice.py` voices drafts with Piper for free. Transcribe every new line with `voice/stt.py`, and reword a line whose words come back wrong.
7. **Cut.** Plan with `cut/cut.py <edit> <out> --stills <times>` first: it prints the length and draws the frames at the times given. Look at the stills of every changed shot. Then render at 60 fps as a tracked background job, and check the length, the loudness (-14 LUFS integrated, true peak under -1 dBTP), the chapters and the captions.
8. **Critique.** Before a final render, run the `video-critic` skill on the cut.

## Rules from the owner's reviews

- Every step that the viewer must follow is on screen. A popup that the screencast does not capture, such as the list of a `<select>`, is drawn in the page with `appearance: base-select` (`harness/picker-css.js`).
- No overlay highlight where the UI already shows the state, such as a focus ring after Tab. A spotlight dims the rest of the frame and draws no outline.
- Park the pointer on an empty area before keyboard steps and at the end of a shot, so that no element shows a hover state.
- A version number next to a wordmark has the height of its tallest lowercase letters and shares its baseline.
- The opening card follows the title slide of the mini summit deck: a kicker and a large title on the left, the app tilted beside them, which then moves into the first shot.
- The end card asks for support: organizations join the Jupyter Foundation, a star on GitHub (one line per repository), the community page. It names the release managers one per line, and lists first-time contributors apart from returning contributors and maintainers.
- A length that the owner gives as a guide is not a limit. Never shorten lines, pauses or holds, or add speed-ups, to get under a length; report the length instead.
- Typing in a question plays in real time. The setup of a shot may play at 2× under a badge.
- An answer of a model plays at the speed it has without the recorder, with no badge (see the lessons).

### Narration

- Open gently ("Introducing JupyterLab 4.7"), and announce the first demonstration before it starts.
- A line gives the problem or the benefit first, then the change, and marks the change as new ("no longer", "In 4.7"). "X now does Y" over a shot of X doing Y sounds like a description of the shot.
- Do not read setting names, text on screen or Mac shortcuts. An opt-in feature is said with "can", and a label on screen gives where to turn it on ("Enable in Settings Editor → Notebook → ..."). Say "option" only with who it helps ("an option useful for teaching").
- Do not state behaviour that is still under discussion, and do not say the same fact twice, also not in a later chapter.
- A measurement is a comparison that the viewer takes in at once ("4.6 took nine times longer"); the exact numbers stay on screen.
- A synthetic voice pauses at every comma, so a short opening phrase takes none ("In 4.7 the Running panel shows...").
- A problem line names the user's mistake concretely ("Deleted the wrong cell while it was still running?").
- Key caps and labels stay above the bottom fifth of the frame, where players draw captions; a lighter line under the key caps gives the Mac keys.
- "The point 7 releases" names JupyterLab 4.7 and Notebook 7.7 together where a change applies to both.

## Lessons

- **Load.** A render and a take compete for the CPU: never render while recording. The recorder itself slows a local model two to three times, and the load of the host can halve its speed within minutes.
- **Answer speed.** For the AI shot, the take marks the wall clock when it sends the question, and `ai/local_llm_server.py` writes the times of each answer. `ai/llm_marks.py` then replays the request three times without the recorder and writes the speeds that the cut uses. The server's prompt cache is cleared before the take and before each replay, so that the model reads the whole question, as it would for a first question.
- **Caret.** A text caret blinks faster in a span that plays faster: the AI take hides the caret of the chat input from sending until the answer is complete.
- **Jobs.** Run takes, renders and benchmarks as tracked background jobs. Stop a process by its PID, never with `pkill -f`, which matches the shell that runs it.
- **Blockers.** Report a blocker as soon as it shows, such as an expired API key or a server that does not start; do not work around it in silence.
- **One-line errors.** For a shot that shows a failing cell, run `%xmode Minimal` silently in the kernel during setup, so that the error is one line.
- **Packages.** The environment of a server may lack the packages of a shot: `setup/add_data_kernel.sh` adds a kernel from another environment that shows with the default name.
- **Side panels.** A side panel opens at the width it had before it was collapsed: drag the splitter in `setup()`, collapse the panel, and the shot opens it at that width.
- **Drags.** Lumino drags need a hover before the move: use `H.drag` with `hoverMs`, and probe the drop target first.
- **JupyterLite demo.** The docs demo fails to load a chunk now and then: retry the take. Hide the Read the Docs flyout and dismiss the notifications with "Don't show me again".
- **Install commands.** Beta builds are on conda-forge labels (`jupyterlab_beta`, `notebook_beta`, from the `beta-*` branches of the feedstocks). Until the release, `TESTING = True` in the project's `edit.py` makes the voice say "available for testing" and the end card give the pre-release commands.
- **Contributors.** `tools/split_contributors.py` splits first-time from returning contributors by the "Contributors to this release" lists of earlier releases. Run it again with the final releases.
- **Models.** For the AI shot, smaller local models did not answer sooner, because they wrote longer answers, and the ones under 1.7B parameters answered wrongly (`ai/bench_models.py`). The question has to name what the model cannot see: asked "Why does this cell fail?" without the file, it suggested `sep=';'`.
- **Warped windows.** A perspective warp samples black outside the image and leaves a dark line on the window's edge: `cut/cut.py` repeats the edge pixels before the warp and warps a rounded mask.
