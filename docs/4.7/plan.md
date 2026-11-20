# JupyterLab 4.7 release video

This page plans the release video for JupyterLab 4.7 and describes its rough cut. The rendered cuts are not in this repository. The rough cut shows only features that are merged on `main` (0d5e835301, 18 November 2026). Every shot is a script that plays a live JupyterLab, so all shots can be recorded again from the 4.7.0 release in about ten minutes.

## Rough cut

The video covers JupyterLab 4.7 with Notebook 7.7 and JupyterLite 0.9: the combined cut is 5:08 at 1920x1080 and 60 fps, with Matilda's voice, music and a title per shot. Notebook and JupyterLite do not have enough new features for videos of their own, so they get a chapter here, followed by an addendum on AI after the end card. The JupyterLab cut (3:52) is the same video without these two chapters, in case Notebook 7.7 is released later than JupyterLab 4.7. [script.md](script.md) has the narration of both, and the cut writes it as captions into an `.srt` file next to each video. The shots follow the order of the 4.7 release notes. Until the final releases, the voice says that the releases are available for testing, and the end card gives the commands that install the betas; `TESTING = False` in `edits/make_edit.py` switches both back to the release, and the voice clips for both are recorded.

| Start | Shot | What the viewer sees | PR |
| --- | --- | --- | --- |
| 0:00 | Faster output | An opening card with the title beside the 4.7 window; the window moves aside, 4.6 slides in, and a pointer in each window clicks Run. 4.7 finishes the 1,000 log lines in 1.15 s, 4.6 in 10.96 s | #17197 |
| 0:20 | Title card | The JupyterLab wordmark and 4.7 | |
| 0:23 | Read-only files open view-only | A read-only notebook opens in view-only mode; Save Notebook As makes a copy that can be edited and run | #19707 |
| 0:37 | Read-only cells show a lock | The lock of a read-only test cell offers to make it editable, and the author then adds a test | #19789 |
| 0:52 | Help opens in a panel below | `statistics.median?` opens its docstring under the notebook | #18179 |
| 1:02 | Undo brings back a running cell | A running cell is deleted and restored with Edit, Undo Cell Operation; a notification offers the outputs that arrived meanwhile | #18977 |
| 1:18 | Recent commands come first | The command palette lists the last three commands and runs one again | #19175 |
| 1:26 | Jump to a tab by position | Ctrl + Alt + 1, 3, 2 and 9 switch tabs | #18293 |
| 1:38 | Reorder sidebar sections | Terminals is dragged above Kernels in the Running panel | #18933 |
| 1:48 | Terminal titles in the Running panel | `train.py` sets "Training: epoch 5/10", and the Running panel shows it | #19138 |
| 2:02 | Search inside rendered math | Ctrl + F in a Markdown Preview finds `sin` inside formulas | #19815 |
| 2:12 | Long formulas wrap | A Markdown cell renders a two-line equation and an inline formula that wraps | #19815 |
| 2:26 | Mermaid diagrams follow the theme | Switching to JupyterLab Dark redraws the diagram | #20356 |
| 2:37 | CSV comment lines | "hash" picked from the Comment menu turns `#` lines into comments, and the search counts the matches | #18714, #20028 |
| 2:52 | Shortcuts for R operators | Alt + - inserts `<-`, Ctrl + Shift + M inserts `%>%` | #19220 |
| 3:03 | Kernel sources as a tree | The debugger lists modules by package | #18092 |
| 3:12 | Settings from the keyboard | Tab and the arrow keys reach the Settings Editor's plugin list, then every shortcut and button of the Keyboard Shortcuts editor | #19028, #19159 |
| 3:26 | Help opens below by default | Notebook 7.7 opens the docstring of `statistics.median?` below the notebook | [jupyter/notebook#7713](https://github.com/jupyter/notebook/pull/7713) |
| 3:35 | Turn extensions off | The JupyterLite Extension Manager turns off the tour extension, and after the reload its two notifications are gone | [jupyterlite/jupyterlite#2059](https://github.com/jupyterlite/jupyterlite/pull/2059) |
| 3:49 | And more | Six areas with three changes each, under JupyterLab's own icons; Notebook 7.7 and JupyterLite 0.9 with three changes each; the full changelog link | |
| 3:57 | Upgrade | `pip` and `conda` commands for the betas, ways to support Project Jupyter (the Jupyter Foundation, stars on GitHub, the community page); the thanks, the release managers, and the handles of 76 first-time contributors and of 34 returning contributors and maintainers. After a pause of 0.8 s, the voice asks "Noticed something is missing?" | |
| 4:11 | AI, when you want it | A title card; the voice answers that Jupyter does not force AI on anyone | |
| 4:18 | A local model next to your notebook | A cell fails on a CSV file with comment lines. Jupyter AI Lite gets a provider for a model on this machine, the cell is dragged into the chat, and Gemma 4 E4B answers with `comment='#'`. Replace selection puts the answer into the cell, and the next cell shows the table | |
| 4:57 | Get started with AI in Jupyter | Jupyter AI, Jupyter AI Lite and agents in a terminal, with install commands; links for local models and for getting started | |

The look is JupyterLab's own. The colours, fonts, the 2 px radius and the key caps come from the variables of the light theme and its `kbd` style, the background is `--jp-layout-color2`, and the title card uses the JupyterLab wordmark, with 4.7 as tall as its "l" and on its baseline. The opening card follows the title slide of the mini summit deck: an orange kicker in Source Code Pro, a large title in Source Sans 3, and the app window turned beside it. JupyterLab runs in a 1152x648 viewport at device scale factor 2.5, so the notebook, its toolbars and its notifications share one screen. The camera zooms at most 1.12 times, and up to 1.3 or 1.6 times only where the subject is small: the lock, the palette, the CSV menu and the R editor. A spotlight dims the rest of the window, with no outline, and the pointer is a plain black arrow with a white edge. A shot of an opt-in feature shows where to turn it on, in a label such as "Enable in Settings Editor → Notebook → Show Help in Bottom Panel". Key caps show above the bottom fifth of the frame, where players draw captions, and a lighter line under them gives the Mac keys.

The voice announces the race as an example of the performance improvements before the click. The pointers that click Run are drawn in the cut, because the takes started the cells from a script. The race needs a quiet machine. Three runs on a lightly loaded machine gave 10.78, 11.05 and 10.96 s for 4.6.6 and 1.15, 1.31 and 1.13 s for 4.7.0b2, and the cut uses the median of each. Runs at the smaller viewport later in the day gave 21 to 29 s against 2.7 to 3.3 s, because other jobs held a load average of 8 to 23 on 8 cores. So the cut still uses the earlier takes, at a 960x540 viewport, and the race should be recorded again with the 4.7.0 release on a quiet machine, with a real click on Run. The release notes give 0.6 s against 5.8 s on another machine: a ratio of 9.7, against 9.5 here.

## Voice and music

The voice is Matilda, an ElevenLabs voice on the `eleven-v4` model, through OpenRouter. The nine samples and the full script for both cuts cost $0.70 in all, by the usage of the OpenRouter key. Before it, the draft voice was Piper, a speech model that runs on this machine, with its `en_GB-alba-medium` voice. The 54 lines of the video (604 words) are in [`edit/make_edit.py`](../../edit/make_edit.py), each tied to a beat of its shot, and the cut lengthens a shot when its lines need more time. Each line gives the problem or the benefit first and then the change. The lines do not read setting names, text on screen or Mac shortcuts, and they do not say whether a view-only notebook starts a kernel, because that is still under discussion. An opt-in feature is said with "can", and its label gives the setting. A transcription of the voice back to text heard "JupyterLab" as "Jobpeter Lab", so the voice now reads it as "Jupiter Lab". Samples of the first 45 s with nine ElevenLabs voices on `eleven-v4` cost $0.31 through OpenRouter, and the full script costs about $0.35 per voice. `voice/voice.py` voices the lines with Piper and `voice/el_voice.py` with ElevenLabs through OpenRouter, into folders of the same format, so a cut changes its voice with one argument of `edit/make_edit.py`. A human narrator can read the same script, and the cut then follows the recorded line lengths.

The music is "Intergalactic Journey" by spinmeister: https://ccmixter.org/files/spinmeister/21067. It is CC0 ("The artist has waived all rights"), calm ambient electronic at 90 BPM, and 5:59 long, so it covers the cut without a loop. Its soft intro plays under the race, and the full sound starts at the title card. The music sits about 10 dB under the voice, and the cuts fall on its beat. Three other CC0 tracks were considered. FreePD has closed, Kevin MacLeod's music is now registered in Content ID, and the Free Music Archive needs an account to download.

## How the cut follows the research

The research is in [research/craft.md](research/craft.md), one source per claim. The research found no official JupyterLab release video under 3 minutes: the 3.0 and 4.0 blog posts used short clips, 4.1 to 4.6 used stills, and the videos were talks of 15 to 42 minutes. Highlight videos of developer tools run 2:12 to 2:51 with 6 or 7 features, such as the VS Code release highlights (2:51) and Warp 2.0 (2:27).

The cut follows these rules:

- A feature is on screen at 0:00, the title card lasts 3.3 s, and the strongest features play in the first 30 s, where YouTube measures its "Intro" retention.
- Every shot reads with the sound off: a headline of at most 6 words names it, and the action shows it. The captions come as an SRT file with cues of at most two lines of 42 characters, so YouTube can show and translate them.
- The camera never rotates or tilts, and nothing flashes; the theme switch is one change.
- The pointer hides when idle, a click ripple lasts 0.5 s, and key caps show shortcuts only, never typed text.
- The UI is recorded at device scale factor 2.5 and exported at 60 fps.

These rules are not followed yet:

- The research suggests 5 to 7 features at 15 to 25 s each. The cut has 16 shots of 9 to 16 s, and the narration carries them. A 7-feature cut of about 2:00 is an edit of the same takes (race, undo, view-only, palette, reorder, CSV, R).
- Each feature should also exist as a clip of 15 to 30 s, and feed cuts should be 4:5 or 1:1.
- The end card should give the number of contributors. The 4.7.0 changelog gives it at release time.

## Scenarios for the pull requests that are still open

Seven pull requests on the 4.7.0 milestone are open. Four of them would change the video.

| PR | Status on 18 November | If it merges | If it does not |
| --- | --- | --- | --- |
| #20432 Mark the current search match in rendered Markdown cells | Review required; the 4.7 notes already describe it | A 7 s shot after "Search inside rendered math": stepping through matches in a notebook keeps the Markdown cells rendered | The video does not change, but the bullet in the 4.7 notes has to go |
| #19142 Notebook kernel locking | Changes requested | An 8 s shot after "Read-only cells show a lock": the kernel dialog's new checkbox disables Switch Kernel. The two shots make a teaching pair | No change |
| #20033 xterm.js 6.1 beta | One approval | One line in "And more": Option and AltGr keys type characters in the terminal again | No change |
| #20511 Known extensions in the Extension Manager | Review required | One line in "And more", or a 5 s shot of Discover listing the extensions of the Jupyter organizations | No change |
| #20012 Save button of view-only notebooks | Draft | Record "Read-only files open view-only" again, since its toolbar may change | No change |
| #20484 Stale breakpoints | Review required | No change: a bug fix with nothing new to show | No change |
| #19033 Spelling script for the docs | Review required | No change | No change |

Three cuts follow from the table:

- With nothing more merged, the video is the rough cut: 5:08.
- With #20432 and #20033, the two closest to merging, it is about 5:18.
- With all four that change the video, it is about 5:32.

The cut without the Notebook, JupyterLite and AI chapters is 75 s shorter in each case.

Merged features can still change before 4.7.0, so the final shots are recorded from the 4.7.0 release and the lines are checked against the final notes. The cut makes no claim about tab switching apart from one line in "And more", so a change to the `contentVisibility` default (the Firefox blocker #19162) only touches that line.

## Notebook 7.7 and JupyterLite 0.9

The details are in [research/notebook-lite.md](research/notebook-lite.md), with a link for every pull request. Both are in beta and pair with JupyterLab 4.7:

- Notebook 7.7.0b1 (9 November) is on JupyterLab 4.7.0b1. It has 10 user-facing changes of its own, and it needs Python 3.11 or newer.
- JupyterLite 0.9.0b1 (9 November) is on JupyterLab 4.7.0b1 and Notebook 7.7.0b1. It has 11 user-facing changes of its own. `jupyterlite-xeus` and `jupyterlite-terminal` still require a JupyterLite below 0.9.

The "And more" card lists three changes of each. A chapter of 22 s before that card has two shots:

- Notebook 7.7 opens help from `object?` below the notebook by default ([jupyter/notebook#7713](https://github.com/jupyter/notebook/pull/7713)), recorded from Notebook `main` with [jupyter/notebook#8128](https://github.com/jupyter/notebook/pull/8128), which centers the icon of the Help tab, assumed merged.
- The JupyterLite Extension Manager turns off the tour extension, and after the reload its two notifications are gone ([jupyterlite/jupyterlite#2056](https://github.com/jupyterlite/jupyterlite/pull/2056), [jupyterlite/jupyterlite#2059](https://github.com/jupyterlite/jupyterlite/pull/2059)).

The JupyterLite shot was recorded on the docs demo, which runs 0.9.0b1. JupyterLite also opens read-only notebooks in view-only mode, but the JupyterLab shot already shows that. The narration calls JupyterLab 4.7 and Notebook 7.7 "the point 7 releases" where a change applies to both, starting with the opening line. New > Terminal in the current folder ([jupyter/notebook#8041](https://github.com/jupyter/notebook/pull/8041)) is not in the cut, because Notebook opens the terminal in a new browser tab.

Two features need a newer Notebook release: MathJax 4.1 came with JupyterLab 4.7.0b2, and the rendered Markdown search waits for #20432. In JupyterLite, the debugger and terminal features do not apply, and `object?` prints its help in the cell output.

## AI

The AI chapter makes a different bet from LibreOffice, which markets itself as free of AI. It comes after the end card, as an addendum. The end card stays on screen for 0.8 s after the thanks, and the voice then asks "Noticed something is missing?", so the question plays before the answer is on screen. The title card "AI, when you want it" follows, and the voice answers that Jupyter does not force AI on anyone, because these releases work without it. The video ends on the card with the AI packages and links, so the music fades out there. Its next lines say that Jupyter is ready for AI when the user wants it, also with a model on the user's own machine, that the answer about a failing cell goes straight back into the notebook, and that the question and the answer stay on that machine.

The shot runs Jupyter AI Lite 0.21 in JupyterLab 4.7.0b2. A notebook reads `weather.csv`, a copy of the measurements with two `#` comment lines at the top, and its cell fails with a `ParserError`. The shot adds a provider named "Local model" of the type Generic (OpenAI-compatible), with the model `gemma-4-e4b` and the base URL `http://localhost:8080/v1`. It then opens a chat in the side panel, drags the failing cell into the chat, and asks "How do I make pandas skip the # comment lines in this file?". Gemma 4 E4B answers on this machine with `weather = pd.read_csv("weather.csv", comment='#')`. Replace selection puts that line into the cell, and the run of the next cell shows the table. The kernel of this notebook runs in another environment (`setup/add_data_kernel.sh`), because the 4.7.0b2 environment has no pandas.

The recorder shares the 8 cores with the model, so the answer is slower while it records: 6.9 s until the first word and 13.7 s for the text, against 3.9 s and 5.9 s for the same request right after the take (the medians of three runs). The cut plays each part at the speed that matches the run without the recorder, with no badge. `ai/llm_marks.py` takes these times from the server and writes them to the take. Before the take and before each run, the server gets a different request, so that the model reads the whole question again, as for a first question. The setup, from the Settings menu to the drag of the cell, plays at 2× under a badge, and the question is typed in real time. While the answer plays faster, the caret of the chat input is hidden, because it would blink faster too. The load on this machine changes the speed of the model: a short question took 3.9 s at 13:25 and 7.2 s at 14:25. A take at a quiet moment therefore gives a faster answer. A smaller model does not answer sooner, because it writes a longer answer, and the models under 1.7B parameters answer wrongly.

The local API is `ai/local_llm_server.py`: llama-cpp-python behind an OpenAI-compatible endpoint, with a fixed seed, so every take gets the same answer. It cannot run tools, so for a request that offers tools it replaces Jupyternaut's system prompt (12,400 characters about tools) with a short one that asks for one or two sentences. With the full prompt, the model wrote its tool calls as text, and a CPU took minutes to read the prompt. Ollama was not used. The JupyterLite demo of Jupyter AI Lite was not used, because a page on `jupyterlab.github.io` would have to call a server on `localhost`.

The card after the shot gives the three packages and their install commands, from the Jupyter AI getting-started guide:

- `pip install jupyter-ai`: a chat panel in JupyterLab with agents such as Claude Code, Codex and OpenCode.
- `pip install jupyter-ai-lite`: Jupyternaut in the browser, in JupyterLab, Notebook and JupyterLite.
- `pip install jupyter-ai-core`: coding agents in a terminal work in JupyterLab through its MCP server.

It links https://jupyter-ai-lite.readthedocs.io/en/latest/ollama/ for local models and https://jupyter-ai.readthedocs.io/en/stable/getting-started.html.

## Credits

The end card has two columns: the install commands and the ways to support Project Jupyter on the left, and the thanks, the release managers and the contributors on the right. The release managers are Mike Krassowski for JupyterLab and Jeremy Tuloup for Notebook and JupyterLite. The contributors are the GitHub handles from the "Contributors to this release" lists of the changelogs, which count code, reviews and discussions: 100 for JupyterLab 4.7.0a0 to 4.7.0b2, and 110 with Notebook 7.7.0a0 to 7.7.0b1 and JupyterLite 0.9.0a0 to 0.9.0b1. The Copilot and claude bot accounts are left out. The card splits them into first-time contributors and returning contributors and maintainers, and gives each release manager a line of their own. A handle is first-time when it is in no such list up to JupyterLab 4.6.0, Notebook 7.6.0 and JupyterLite 0.8.0, which go back to JupyterLab 3.0. That gives 72 first-time and 28 returning contributors for JupyterLab, and 76 and 34 for the three projects. The lists are in `edit/contributors-split.json` (from `tools/split_contributors.py`), and they need the final releases added before publishing.

## Open decisions

- Should the end card ask for donations? The About page of jupyter.org has a Donate button (https://jupyter.org/about). A fourth line asks individuals for money next to the Foundation line, which asks organizations; without it, the card asks for no money from individuals.
- Should a person narrate instead of Matilda? A human narrator sounds most natural, and the cut follows the recorded line lengths, but it takes a recording session, and each later change to a line needs another one.
- Full cut or main cut? The 18-shot cut (4:02) shows the breadth of 4.7. A 7-feature cut (about 2:00) follows the exemplars, but it leaves nine features to the blog post.
- Which build for the final takes? The 4.7.0 wheel from PyPI is what users get. A `main` build could include changes made after 4.7.0.
- Where does it go? The Project Jupyter YouTube channel with the release post reaches the most viewers, and the channel's owners decide. Single shots can also go into the post as short clips, as KDE does for Plasma.

## Found while recording

- A notebook with no kernel shows "No Kernel | Initializing" in the status bar for as long as it is open, in 4.6.6 too. In 4.7 every view-only notebook shows it. No issue was found.
- The 4.7 notes do not mention #20498 (merged 14 November). The pull request adds commands that move sidebar sections up and down without dragging.
- The 4.7 notes describe #20432, but the pull request is still open.

## How it is made

Each shot is a Playwright script in `harness/takes/`. It opens JupyterLab on a demo project about weather stations: notebooks, a CSV file with comment lines, a Markdown file with formulas, an R script and a training script. The screen recorder (`harness/recorder/`) records the Chromium screencast at 2880x1620, one frame per 1/30 s of wall time. The page draws no pointer and no key labels. The script logs every mouse and key event with its time, and the cut draws the pointer, ripples and key caps at 60 fps. A magenta square flashed in the corner at the start of each take measures the delay between an event and the frame that shows it: 10 to 59 ms in these takes. The screencast does not capture the popup list of a `<select>`, so the CSV take draws the Comment menu in the page with `appearance: base-select`, sized like Chromium's own popup (`harness/picker-css.js`).

The script also marks the element that matters at each moment, by the box of its text and media rather than its full width. The cut frames the marks of each 2.5 s together, so the camera stays still while the action moves between nearby elements, and it follows them with a critically damped spring. Spans that only wait play faster under a labelled badge.

The commands that record the takes and render the cut are in the [README](../../README.md).
