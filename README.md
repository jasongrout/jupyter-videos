# Jupyter release video

The tools that made the release video of JupyterLab 4.7, Notebook 7.7 and JupyterLite 0.9. Every shot is a script that plays a live JupyterLab in Chromium while a recorder captures it. A narrator voice reads lines tied to moments of the takes, and a cut tool renders the video frame by frame: camera, pointer, key caps, titles, cards, captions, music. So a shot can be recorded again from a new build in a minute, and the whole video can be cut again after any change.

[docs/4.7/](docs/4.7/) is the record of the 4.7 video: its [plan](docs/4.7/plan.md), its [narration](docs/4.7/script.md), the research behind it, and the brief of its first critique.

## How a video is made

1. **Servers.** One JupyterLab server per version on its own port, with its own settings, all serving one folder of demo files about weather stations (`setup/`).
2. **Takes.** A take script (`harness/takes/`) prepares the page, then plays the shot like a person: eased pointer moves, clicks, typing. The recorder writes the screencast to `raw.mp4`, a timeline of marks (beats, focus boxes) and a log of every pointer and key event. The page draws no pointer: the cut draws it from the log.
3. **Edit.** `edit/make_edit.py` writes the edit file: the cards, the segments of takes between beats, the spans that play faster, the titles, and the narration lines, each tied to a beat.
4. **Voice.** `voice/el_voice.py` voices the lines with ElevenLabs through the audio API of OpenRouter: the 4.7 video used the voice Matilda on `elevenlabs/eleven-v4`, for $0.70 with nine voice samples. `voice/voice.py` voices drafts with Piper, a speech model that runs locally. `voice/stt.py` transcribes the clips back to text, to catch words that the voice reads wrongly.
5. **Cut.** `cut/cut.py` renders 1920x1080 at 60 fps. A spring camera follows the focus boxes, and the cut draws the pointer and key caps, renders the cards and titles from HTML with Chromium, ducks the music under the voice, normalizes the loudness to -14 LUFS, and writes captions (`.srt`) and chapters next to the video.

## Layout

| Folder | What is in it |
| --- | --- |
| `harness/` | `run_take.js` records one take, `run_takes.sh` several; `rv.js` holds the helpers of the takes, `common.js` the JupyterLab ones; `takes/` has one script per shot, `probes/` the scripts that checked the app before a take, `recorder/` the screen recorder and the pointer and keyboard driver |
| `cut/` | `cut.py` and the overlay renderer, the CSS of the cards, the fonts, the JupyterLab wordmark; `sheet.py`, `takesheet.py` and `sample.py` draw frames for checks; `music.py` writes a placeholder music bed |
| `edit/` | `make_edit.py`, with the narration, the cards and the order of the shots; the contributors of the end card |
| `voice/` | ElevenLabs through OpenRouter, Piper, and the transcription check |
| `setup/` | the server script and its config, a build of `main` without an install, the demo files, the settings of the takes, the kernel of the AI shot |
| `ai/` | the local model of the AI shot: an OpenAI-compatible server, the speed measure of its answer, a benchmark of models |
| `tools/` | the PRs of a milestone, the split of first-time and returning contributors, the narration script from a cut |
| `docs/` | the plan, the narration and the research of each video |
| `.agents/skills/` | `release-video` (the steps and the lessons) and `video-critic` (a critique of a cut by a background agent), for any coding agent; `AGENTS.md` lists them, and `.claude` and `CLAUDE.md` link to the same files for Claude Code |

Everything that the tools make goes to `work/` (or `$RV_WORK`): takes, voice clips, music, rendered overlays, edit files and videos. The servers' folders go to `work/runtime/` (or `$RV_BASE`). `env.example` lists every setting.

## Requirements

- Linux, with the Noto and DejaVu fonts (`fonts-noto-core`, `fonts-dejavu-core`), ffmpeg, Node.js 20 or newer, and Python 3.12 with `requirements.txt`.
- `npm install` for playwright-core 1.64.0, and `npm run browser` for its Chromium headless shell.
- A JupyterLab checkout with its `node_modules`, to build `main` and to read JupyterLab's icons for the cards (`JUPYTERLAB_SRC`).
- `gh`, authenticated, for the tools that read GitHub.
- For the AI shot: llama-cpp-python, huggingface_hub, and a GGUF model (Gemma 4 E4B for 4.7).
- For narration: an OpenRouter key in `OPENROUTER_API_KEY`, or Piper and a Piper voice.

## Making the 4.7 video

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

# Takes: on a quiet machine, one at a time, with no render running.
harness/run_takes.sh 8963 undo help lock viewonly mathsearch csv palette reorder terminal tabs a11y math rkeys sources mermaid
harness/run_takes.sh 0 lite-extensions   # the JupyterLite docs demo: retry when a chunk fails to load
RV_NAME=stream-46f RV_WIDTH=960 RV_HEIGHT=540 RV_DSF=1.5 node harness/run_take.js harness/takes/stream.js 8961
RV_NAME=stream-47d RV_WIDTH=960 RV_HEIGHT=540 RV_DSF=1.5 node harness/run_take.js harness/takes/stream.js 8962
node harness/run_take.js harness/takes/nb-help.js 8964

# The AI shot: a local model behind an OpenAI-compatible endpoint, then the speed of its answer without the recorder.
MODEL=$(python -c 'from huggingface_hub import hf_hub_download as d; print(d("ggml-org/gemma-4-E4B-it-GGUF", "gemma-4-E4B-it-Q4_0.gguf"))')
setsid python ai/local_llm_server.py "$MODEL" gemma-4-e4b 8080 > work/llm-server.log 2>&1 < /dev/null &
node harness/run_take.js harness/takes/ai-local.js 8962
python ai/llm_marks.py work/takes/ai-local

# Music: "Intergalactic Journey" by spinmeister (CC0), from https://ccmixter.org/files/spinmeister/21067
mkdir -p work/music && ffmpeg -i <downloaded file> work/music/intergalactic-journey.wav

# Edit, voice and cut.
python edit/make_edit.py work/edits/cut.json --nb-lite --voice el-v4-matilda
python voice/el_voice.py work/edits/cut.json work/voice/el-v4-matilda --voice matilda
python cut/cut.py work/edits/cut.json work/out/cut.mp4 --stills 1.0   # plans the cut and prints its length
python cut/cut.py work/edits/cut.json work/out/cut.mp4                # 60 fps; --preview renders at 30 fps
```

Without `--nb-lite`, `make_edit.py` writes the JupyterLab cut. Until the final releases, `TESTING = True` in `edit/make_edit.py` makes the voice say that the releases are available for testing, and the end card give the commands that install the betas.

## Third-party parts

- `cut/fonts/`: Source Sans 3 and Source Code Pro, under the SIL Open Font License (the licenses are next to the fonts).
- `cut/jupyterlab-wordmark.svg` is JupyterLab's wordmark, and the cards read JupyterLab's icons from a checkout; both are under JupyterLab's BSD 3-Clause license.
- `harness/recorder/` comes from the author's whybook project (see its README).
- The music is not in this repository: download it from the link above.
