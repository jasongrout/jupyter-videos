# JupyterLab 4.7 release video

The release video of JupyterLab 4.7, Notebook 7.7 and JupyterLite 0.9. [plan.md](plan.md) describes the shots, the voice, the music and the open decisions, and [script.md](script.md) is the narration. [research/](research/) holds the research behind the plan, and [critique-brief.md](critique-brief.md) the brief of the first critique.

- `takes/` has one script per shot.
- `edit.py` writes the edit file: the order of the shots, the cards, the narration and the spans that play faster. `--nb-lite` adds the Notebook, JupyterLite and AI chapters; without it, the edit is the JupyterLab cut. `TESTING = True` makes the voice say that the releases are available for testing, and the end card give the commands that install the betas.
- `contributors-split.json` lists the first-time and returning contributors of the end card (`tools/split_contributors.py`).
- `make_script.py` writes `script.md` from the plans of the two cuts.

The takes, voice clips, music and renders go to `work/4.7-release/` (or `$RV_WORK`).

## Making it

Start the servers as the [README](../../README.md) describes, then:

```bash
# Takes: on a quiet machine, one at a time, with no render running.
harness/run_takes.sh 4.7-release 8963 undo help lock viewonly mathsearch csv palette reorder terminal tabs a11y math rkeys sources mermaid
harness/run_takes.sh 4.7-release 0 lite-extensions   # the JupyterLite docs demo: retry when a chunk fails to load
RV_NAME=stream-46f RV_WIDTH=960 RV_HEIGHT=540 RV_DSF=1.5 node harness/run_take.js projects/4.7-release/takes/stream.js 8961
RV_NAME=stream-47d RV_WIDTH=960 RV_HEIGHT=540 RV_DSF=1.5 node harness/run_take.js projects/4.7-release/takes/stream.js 8962
node harness/run_take.js projects/4.7-release/takes/nb-help.js 8964

# The AI shot: a local model behind an OpenAI-compatible endpoint, then the speed of its answer without the recorder.
MODEL=$(python -c 'from huggingface_hub import hf_hub_download as d; print(d("ggml-org/gemma-4-E4B-it-GGUF", "gemma-4-E4B-it-Q4_0.gguf"))')
setsid python ai/local_llm_server.py "$MODEL" gemma-4-e4b 8080 > work/llm-server.log 2>&1 < /dev/null &
node harness/run_take.js projects/4.7-release/takes/ai-local.js 8962
python ai/llm_marks.py work/4.7-release/takes/ai-local

# Music: "Intergalactic Journey" by spinmeister (CC0), from https://ccmixter.org/files/spinmeister/21067
mkdir -p work/4.7-release/music && ffmpeg -i <downloaded file> work/4.7-release/music/intergalactic-journey.wav

# Edit, voice and cut.
python projects/4.7-release/edit.py work/4.7-release/edits/cut.json --nb-lite --voice el-v4-matilda
python voice/el_voice.py work/4.7-release/edits/cut.json work/4.7-release/voice/el-v4-matilda --voice matilda
python cut/cut.py work/4.7-release/edits/cut.json work/4.7-release/out/cut.mp4 --stills 1.0   # plans the cut and prints its length
python cut/cut.py work/4.7-release/edits/cut.json work/4.7-release/out/cut.mp4                # 60 fps; --preview renders at 30 fps
```
