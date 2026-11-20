# Jupyter videos

Tools to record, narrate and cut videos of Jupyter apps: release videos, and short clips for the documentation. Every shot is a script that plays a live JupyterLab in Chromium while a recorder captures it. A cut tool renders the video frame by frame: camera, pointer, key caps, titles, cards, captions and music, or a silent clip in which the app fills the frame. So a shot can be recorded again from a new build in a minute, and a video or a clip can be cut again after any change.

## Projects

A video, or a set of clips, is a project in `projects/<name>/`: its take scripts in `takes/`, an `edit.py` that writes its edit files, and its notes. What a project makes goes to `work/<name>/`.

| Project | What it makes |
| --- | --- |
| [`4.7-release`](projects/4.7-release/) | The release video of JupyterLab 4.7, Notebook 7.7 and JupyterLite 0.9, with its plan, narration, research and critique brief |
| [`docs`](projects/docs/) | Clips for the JupyterLab documentation, such as the animations of the 4.7 changelog |

## How a video is made

1. **Servers.** One JupyterLab server per version on its own port, with its own settings, all serving one folder of demo files about weather stations (`setup/`). The projects share the servers.
2. **Takes.** A take script prepares the page, then plays the shot like a person: eased pointer moves, clicks, typing. The recorder writes the screencast to `raw.mp4`, a timeline of marks (beats, focus boxes) and a log of every pointer and key event. The page draws no pointer: the cut draws it from the log.
3. **Edit.** The project's `edit.py` writes the edit file: the cards, the segments of takes between beats, the spans that play faster, the titles, and the narration lines, each tied to a beat. `cut/cards.py` builds the cards that any project can use: an opening card beside a tilted app, a card of areas, the end card with install commands, support and credits, and a one-line card.
4. **Voice.** `voice/el_voice.py` voices the lines with ElevenLabs through the audio API of OpenRouter: the 4.7 video used the voice Matilda on `elevenlabs/eleven-v4`, for $0.70 with nine voice samples. `voice/voice.py` voices drafts with Piper, a speech model that runs locally. `voice/stt.py` transcribes the clips back to text, to catch words that the voice reads wrongly.
5. **Cut.** `cut/cut.py` renders 1920x1080 at 60 fps. A spring camera follows the focus boxes, and the cut draws the pointer and key caps, renders the cards and titles from HTML with Chromium, ducks the music under the voice, normalizes the loudness to -14 LUFS, and writes captions (`.srt`) and chapters next to the video.

A **clip** for the documentation skips the voice and the music: `cut/cut.py` with `--clip`, or an edit file with `"clip"` settings, renders the take, or a crop of it, to fill the frame, with no cards, titles or badges, and writes a GIF, WebM or MP4 at the width of a docs page. Any shot of a video can become a clip with `--clip --only <index of the shot>`.

## Layout

| Folder | What is in it |
| --- | --- |
| `harness/` | `run_take.js` records one take, `run_takes.sh` several takes of a project; `rv.js` holds the helpers of the takes, `common.js` the JupyterLab ones; `probes/` the scripts that checked the app before a take; `recorder/` the screen recorder and the pointer and keyboard driver |
| `cut/` | `cut.py`, `cards.py` and the overlay renderer, the CSS of the cards, the fonts, the JupyterLab wordmark; `sheet.py`, `takesheet.py` and `sample.py` draw frames for checks; `music.py` writes a placeholder music bed |
| `voice/` | ElevenLabs through OpenRouter, Piper, and the transcription check |
| `setup/` | the server script and its config, a build of `main` without an install, the demo files, the settings of the takes, the kernel of the AI shot |
| `ai/` | the local model of the AI shot: an OpenAI-compatible server, the speed measure of its answer, a benchmark of models |
| `tools/` | the PRs of a milestone, and the split of first-time and returning contributors of a release |
| `projects/` | one folder per video or set of clips |
| `.agents/skills/` | `release-video`, `docs-clips` and `video-critic`; `AGENTS.md` lists them |

The servers' folders go to `work/runtime/` (or `$RV_BASE`), and each project's takes, voice clips, music, overlays, edit files and videos to `work/<project>/` (or `$RV_WORK`). `env.example` lists every setting.

## Requirements

- Linux, with the Noto and DejaVu fonts (`fonts-noto-core`, `fonts-dejavu-core`), ffmpeg, Node.js 20 or newer, and Python 3.12 with `requirements.txt`.
- `npm install` for playwright-core 1.64.0, and `npm run browser` for its Chromium headless shell.
- A JupyterLab checkout with its `node_modules`, to build `main` and to read JupyterLab's icons for the cards (`JUPYTERLAB_SRC`).
- `gh`, authenticated, for the tools that read GitHub.
- For the AI shot: llama-cpp-python, huggingface_hub, and a GGUF model (Gemma 4 E4B for 4.7).
- For narration: an OpenRouter key in `OPENROUTER_API_KEY`, or Piper and a Piper voice.

## Setting up

```bash
npm install && npm run browser
python -m pip install -r requirements.txt
python cut/make_fonts_css.py

# Servers: main from a checkout, released versions from PyPI.
JUPYTERLAB_SRC=/path/to/jupyterlab setup/build_main.sh main
for v in 4.6.6 4.7.0b2; do python -m venv work/runtime/venv-$v; work/runtime/venv-$v/bin/pip install jupyterlab==$v; done
work/runtime/venv-4.7.0b2/bin/pip install jupyter-ai-lite==0.21.0
python -m venv work/runtime/venv-nb77 && work/runtime/venv-nb77/bin/pip install notebook==7.7.0b1
DEMO_PYTHON=/path/to/python-with-pandas python setup/make_demo.py work/runtime/root
mkdir -p work/runtime/settings && cp -r setup/settings-template/. work/runtime/settings/
JLAB_DEV_BIN=/path/to/jupyter-lab setup/start_server.sh main 8963
setup/start_server.sh 4.6.6 8961
setup/start_server.sh 4.7.0b2 8962
setup/start_server.sh nb77 8964
setup/add_data_kernel.sh 4.7.0b2 /path/to/python-with-pandas
```

Then follow the README of the project: [4.7-release](projects/4.7-release/README.md) or [docs](projects/docs/README.md).

## Third-party parts

- `cut/fonts/`: Source Sans 3 and Source Code Pro, under the SIL Open Font License (the licenses are next to the fonts).
- `cut/jupyterlab-wordmark.svg` is JupyterLab's wordmark, and the cards read JupyterLab's icons from a checkout; both are under JupyterLab's BSD 3-Clause license.
- `harness/recorder/` comes from the author's whybook project (see its README).
- The music of the 4.7 video is not in this repository: its project README links it.
