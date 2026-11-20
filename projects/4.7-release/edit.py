"""Write the edit file of the narrated cut.

Usage: python edit.py <out.json> [<race 4.6 take> <race 4.7 take>] [--nb-lite] [--voice <folder>]

--nb-lite adds the Notebook 7.7, JupyterLite 0.9 and AI chapters (the combined cut). --voice names the folder of
voice clips in $RV_WORK/voice (piper by default). TESTING below switches the outro between the betas and the release.

The narration ("say") is written for the screen: each line plays while its
shot shows what it describes, and "at" ties a line to a beat of the take.
Spoken text avoids symbols; the voice script's lexicon handles names.
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
# The takes, voice clips and music of this project.
WORK = Path(os.environ.get("RV_WORK", REPO / "work" / HERE.name))
sys.path.insert(0, str(REPO / "cut"))
from cards import addendum_card, also, area, areas_card, end_card, jupyter_area, opening_card  # noqa: E402

# Until the final releases, the voice says "available for testing" and the end card gives the pre-release commands.
TESTING = True
THANKS = "Thank you to the contributors, reviewers, and everyone who tested the betas and reported issues."


# First-time contributors appear in no "Contributors to this release" list up to JupyterLab 4.6.0, Notebook 7.6.0
# and JupyterLite 0.8.0 (tools/split_contributors.py).
CONTRIBUTORS = json.loads((HERE / "contributors-split.json").read_text())

if TESTING:
    # The betas are on these conda-forge labels (the beta-4.x and beta-7.x branches of the feedstocks).
    INSTALL_LAB = ["pip install --upgrade --pre jupyterlab", "conda install jupyterlab \\\n  -c conda-forge/label/jupyterlab_beta"]
    INSTALL_NB = ["pip install --upgrade --pre jupyterlab notebook",
                  "conda install jupyterlab notebook \\\n  -c conda-forge/label/jupyterlab_beta \\\n  -c conda-forge/label/notebook_beta"]
else:
    INSTALL_LAB = ["pip install --upgrade jupyterlab", "conda install -c conda-forge jupyterlab"]
    INSTALL_NB = ["pip install --upgrade jupyterlab notebook", "conda install -c conda-forge jupyterlab notebook"]
OUTRO = end_card("4.7", INSTALL_LAB, ["github.com/jupyterlab/jupyterlab"], ["Mike Krassowski (JupyterLab)"], CONTRIBUTORS["lab"], THANKS)
OUTRO_NB = end_card("4.7", INSTALL_NB, ["github.com/jupyterlab/jupyterlab", "github.com/jupyter/notebook", "github.com/jupyterlite/jupyterlite"],
                    ["Mike Krassowski (JupyterLab)", "Jeremy Tuloup (Notebook and JupyterLite)"], CONTRIBUTORS["all"], THANKS)
AVAILABLE = "available for testing" if TESTING else "available now"

INTRO = opening_card(["Introducing", "JupyterLab&nbsp;4.7"])

# The cut with Notebook 7.7 and JupyterLite 0.9: "the point 7 releases" names JupyterLab 4.7 and Notebook 7.7 together.
INTRO_NB = opening_card(["JupyterLab&nbsp;4.7", "Notebook&nbsp;7.7"], sub="and JupyterLite 0.9")

NB_LITE_CHAPTER = [
    {"take": "nb-help", "from": "beat:type-0.6", "to": "flash:end-0.15", "chapter": "Notebook and JupyterLite",
     "kicker": "Notebook 7.7", "title": "Help opens below by default",
     "say": [
         {"id": "nb_1", "text": "Notebook 7.7 shares most of these changes.", "at": "beat:type-0.6"},
         {"id": "nb_2", "text": "Help from a question mark opens below the notebook by default.", "at": "beat:shown-1.0"},
     ]},
    {"take": "lite-extensions", "from": "beat:open-1.2", "to": "beat:reloaded+2.6", "zoom_cap": 1.2,
     "kicker": "JupyterLite 0.9", "title": "Turn extensions off",
     "speed": [{"from": "beat:list+1.2", "to": "beat:disable-0.3", "x": 2}, {"from": "beat:reload+0.2", "to": "beat:reloaded-0.1", "x": 2}],
     "say": [
         {"id": "lite_1", "text": "JupyterLite 0.9 brings the point 7 releases to the browser, with no server.", "at": "beat:open-1.2"},
         {"id": "lite_2", "text": "Its new Extension Manager can turn off an extension, such as the tour that shows these notifications.", "at": "beat:list"},
     ]},
]

# The opening of that cut is longer, so the race starts later.
NB_LITE_INTRO = {"hold": 4.0, "point": 3.9}
NB_LITE_AT = {"race_s": "+4.6", "race_1": "+8.9"}

# AI after the JupyterLite part: Jupyter does not force AI, and is ready for it, also with local models.
# The setup, up to the drag of the cell, plays at 2x under a badge; the question is typed in real time. The recorder
# slows the model down, so each phase of the answer plays at the speed measured without the recorder right after the
# take (scripts/llm_marks.py), with no badge.
SPEED_FILE = WORK / "takes/ai-local/llm-speed.json"
LLM_SPEED = json.loads(SPEED_FILE.read_text())["x"] if SPEED_FILE.exists() else {"wait": 1.0, "stream": 1.0}
AI_LOCAL_SPEED = [{"from": "beat:settings+0.2", "to": "beat:drag-0.3", "x": 2},
                  {"from": "llm:received", "to": "llm:first", "x": LLM_SPEED["wait"], "badge": False},
                  {"from": "llm:first", "to": "llm:done", "x": LLM_SPEED["stream"], "badge": False}]

AI_CARD = areas_card("Get started with AI in Jupyter", [
    jupyter_area("Jupyter AI", [
        "Chat with agents such as Claude Code, Codex and OpenCode in JupyterLab",
        '<span class="mono">pip install jupyter-ai</span>',
    ]),
    jupyter_area("Jupyter AI Lite", [
        "Jupyternaut in the browser, in JupyterLab, Notebook and JupyterLite",
        '<span class="mono">pip install jupyter-ai-lite</span>',
        '<span class="url">Demo: jupyterlab.github.io/jupyter-ai-lite</span>',
    ]),
    area("statusbar/terminal.svg", "Your agent in a terminal", [
        "Coding agents work in JupyterLab through its MCP server",
        '<span class="mono">pip install jupyter-ai-core</span>',
    ]),
    also("Resources"),
    area("statusbar/kernel.svg", "Local models", [
        "Ollama, LiteLLM and other OpenAI-compatible servers on your machine",
        '<span class="url">jupyter-ai-lite.readthedocs.io/<br>en/latest/ollama/</span>',
    ]),
    area("toolbar/link.svg", "Get started", [
        '<span class="url">jupyter-ai.readthedocs.io/en/stable/<br>getting-started.html</span>',
    ]),
])

AI_TITLE = addendum_card("AI, when you want it")

# After the end card, as an addendum: the video first seems to skip AI.
AI_CHAPTER = [
    {"card": "html", "length": 3.0, "chapter": "AI, when you want it", "html": AI_TITLE, "tail": 0.4,
     "say": [
         {"id": "ai_1", "text": "Yes, Jupyter does not force AI on anyone: these releases work without it.", "at": "+0.3"},
     ]},
    {"take": "ai-local", "from": "beat:settings-0.6", "to": "beat:result+2.6",
     "kicker": "Jupyter AI Lite", "title": "A local model next to your notebook",
     "speed": AI_LOCAL_SPEED,
     "say": [
         {"id": "ai_2", "text": "When you want AI, extensions bring assistants and agents, with the model of your choice,", "at": "beat:add"},
         {"id": "ai_3", "text": "including one that runs on your own machine, through a local API.", "at": "beat:url"},
         {"id": "ai_6", "text": "A cell fails? Ask about it, and put the answer straight back into the notebook.", "at": "beat:drag"},
         {"id": "ai_5", "text": "The question and the answer stay on this machine.", "at": "llm:received"},
     ]},
    {"card": "html", "length": 8.5, "music_outro": True, "html": AI_CARD,
     "say": [
         {"id": "ai_4", "text": "Jupyter AI brings agents such as Claude Code and Codex into JupyterLab. Jupyter AI Lite runs an assistant in the browser.", "at": "+0.5"},
     ]},
]

# Lines that change in that cut, by id.
NB_LITE_LINES = {
    "race_0": {"id": "race_0p", "text": "Introducing the point 7 releases of JupyterLab and Notebook.", "at": "+0.4"},
    "view_2": {"id": "view_2p", "text": "In the point 7 releases, such notebooks open in view-only mode instead.", "at": "beat:opened"},
    "outro_1t" if TESTING else "outro_1": {"id": "outro_1pt" if TESTING else "outro_1p", "text": f"The point 7 releases are {AVAILABLE}.", "at": "+0.5"},
    "math_1": {"id": "math_1p", "text": "The point 7 releases update MathJax to version 4.1.", "at": "beat:render-0.8"},
}


def with_nb_lite(seq):
    out = []
    for item in seq:
        item = json.loads(json.dumps(item))
        item["say"] = [NB_LITE_LINES.get(l["id"], l) for l in item.get("say", []) if l["id"] != "more_3"]
        if "intro" in item:
            item["intro"]["html"] = INTRO_NB
            item["intro"].update(NB_LITE_INTRO)
            for l in item["say"]:
                l["at"] = NB_LITE_AT.get(l["id"], l.get("at"))
        if item.get("music_outro"):
            item["html"] = OUTRO_NB
            # The music goes on into the addendum, after a pause.
            del item["music_outro"]
            # The question comes on the end card, after a pause; the next card answers it.
            item["say"] = item["say"] + [{"id": "ai_0", "text": "Noticed something is missing?", "pause": 0.8}]
            item["tail"] = 0.5
            out.append(item)
            out += json.loads(json.dumps(AI_CHAPTER))
            continue
        if item.get("chapter") == "More":
            out += json.loads(json.dumps(NB_LITE_CHAPTER))
        out.append(item)
    return out

MORE = areas_card("And more in JupyterLab 4.7", [
    area("filetype/notebook.svg", "Notebooks", [
        "Right-click an image to copy it",
        "Copy the ID of a cell, or a link to it",
        "Selecting a collapsed heading selects its section",
    ]),
    area("filetype/folder.svg", "Files and editors", [
        "Paste into the selected folder",
        "Links to folders in Markdown open them",
        "Julia highlighting from Pluto.jl",
    ]),
    area("filetype/console.svg", "Console and debugger", [
        "Rename code consoles",
        "Faster completions in the Debug Console",
        "Debug Console completions for more languages",
    ]),
    area("filetype/settings.svg", "Settings", [
        'Find settings by tag, such as <span class="mono">tag:performance</span>',
        "Search finds editor options, such as rulers",
        "Hide the notebook toolbar from the View menu",
    ]),
    area("toolbar/fast-forward.svg", "Performance", [
        "Faster switching between tabs",
        "84 KB less JavaScript at startup",
        "Faster edits in large notebooks",
    ]),
    area("sidebar/running.svg", "Terminal, server and touch", [
        "Terminal links ask before they open",
        "Errors in configuration files stop the server",
        "Menus respond to taps on touch screens again",
    ]),
    also("Built on JupyterLab 4.7"),
    jupyter_area("Notebook 7.7", [
        "Help opens in a panel at the bottom",
        "Open a notebook without a kernel",
        "New terminals start in the current folder",
    ]),
    jupyter_area("JupyterLite 0.9", [
        "Disable extensions in the Extension Manager",
        "Links can open the Simple Interface",
        "An optional drive shows the site's configuration",
    ]),
    # The link sits in the last row, above the bottom of the frame where players draw captions.
    area("toolbar/link.svg", "Full changelog", [
        '<span class="url">jupyterlab.readthedocs.io/en/stable/<br>getting_started/changelog.html</span>',
    ]),
])

# Each line gives the problem or the benefit first, then the change. Lines do not read setting
# names or what the screen already shows: an opt-in feature starts with that, an opt-out one ends with it.
SEQUENCE = [
    {"left": {"take": "RACE46", "label": "JupyterLab 4.6"}, "right": {"take": "RACE47", "label": "JupyterLab 4.7"},
     "chapter": "Faster output", "kicker": "Performance", "title": "Faster output",
     "note": "The same notebook, machine and kernel: JupyterLab 4.6.6 and 4.7.0b2",
     "intro": {"html": INTRO, "hold": 2.8, "move": 1.0, "point": 3.9, "click": [200.7, 75.3], "pointer_from": [430, 330]},
     "post": 2.0, "speed": [{"from": 3.6, "to": "slowest", "x": 2}],
     "say": [
         {"id": "race_0", "text": "Introducing JupyterLab 4.7.", "at": "+0.4"},
         {"id": "race_s", "text": "Let's start with an example of the performance improvements.", "at": "+3.3"},
         {"id": "race_1", "text": "One thousand lines of logging output appear.", "at": "+7.7"},
         {"id": "race_2", "text": "JupyterLab 4.7 shows them in about a second. 4.6 took nine times longer."},
     ]},

    {"card": "title", "length": 3.0, "version": "4.7", "line": "What's new", "caption": "JupyterLab 4.7: highlights of the release", "music_hit": True},

    {"take": "viewonly", "from": "beat:open-0.2", "to": "beat:copy+2.0", "chapter": "Notebooks",
     "kicker": "Notebook", "title": "Read-only files open view-only",
     "speed": [{"from": "beat:saveas+0.4", "to": "beat:copy-0.2", "x": 1.5}],
     "hide_keys": ["Control+A"],
     "say": [
         {"id": "view_1", "text": "Ever edited a notebook, only to find that you cannot save it?", "at": "beat:open-0.2"},
         {"id": "view_2", "text": "In 4.7, such notebooks open in view-only mode instead.", "at": "beat:opened"},
         {"id": "view_3", "text": "To edit or run the code, save a copy.", "at": "beat:saveas"},
     ]},
    {"take": "lock", "zoom_cap": 1.3, "from": "beat:select-0.3", "to": "focus:typed+1.4",
     "kicker": "Notebook", "title": "Read-only cells show a lock",
     "hide_keys": ["Control+End", "Enter"],
     "labels": [{"text": "Enable in Settings Editor → Notebook → Show lock icon for read-only cells", "from": "beat:select-0.3", "to": "focus:typed+1.4"}],
     "say": [
         {"id": "lock_1", "text": "As an option useful for teaching, a lock icon marks the cells that students cannot edit.", "at": "beat:select"},
         {"id": "lock_2", "text": "Clicking it asks before the cell becomes editable,", "at": "beat:dialog"},
         {"id": "lock_3", "text": "so the author of an exercise can still add a test.", "at": "beat:type"},
     ]},
    {"take": "help", "from": "beat:type-0.4", "to": "beat:resized+2.6",
     "kicker": "Notebook", "title": "Help opens in a panel below",
     "labels": [{"text": "Enable in Settings Editor → Notebook → Show Help in Bottom Panel", "from": "beat:type-0.4", "to": "beat:resized+2.6"}],
     "say": [
         {"id": "help_1", "text": "Help from a question mark can open in a panel under the notebook, as in the classic notebook.", "at": "beat:type"},
         {"id": "help_2", "text": "This works in code consoles too.", "at": "beat:resized"},
     ]},
    {"take": "undo", "from": "beat:run-0.4", "to": "beat:shown+1.8",
     "kicker": "Notebook", "title": "Undo brings back a running cell",
     "say": [
         {"id": "undo_1", "text": "Deleted the wrong cell while it was still running?", "at": "beat:delete-0.2"},
         {"id": "undo_2", "text": "The Undo command brings it back as it was,", "at": "beat:undo"},
         {"id": "undo_3", "text": "and a notification offers the output that it printed in the meantime.", "at": "beat:restored"},
     ]},

    {"take": "palette", "zoom_cap": 1.3, "outline": False, "from": "beat:open-0.5", "to": "beat:run+1.6", "chapter": "Your workspace",
     "kicker": "Command palette", "title": "Recent commands come first",
     "say": [
         {"id": "palette_1", "text": "To run a command again, you no longer have to search for it.", "at": "beat:open-0.5"},
         {"id": "palette_2", "text": "The command palette lists your recent commands first."},
     ]},
    {"take": "tabs", "from": "beat:key1-0.7", "to": "beat:key9+1.3",
     "kicker": "Keyboard", "title": "Jump to a tab by position",
     "say": [
         {"id": "tabs_1", "text": "With many tabs open, Control, Alt and a number jump to the tab at that position.", "at": "beat:key1-0.5"},
         {"id": "tabs_2", "text": "Nine jumps to the last one, however many are open.", "at": "beat:key9"},
     ]},
    {"take": "reorder", "from": "beat:menu-0.5", "to": "beat:dropped+2.4",
     "kicker": "Sidebars", "title": "Reorder sidebar sections",
     "say": [
         {"id": "reorder_1", "text": "Once you turn on reordering, you can drag the sections of a sidebar into the order you like.", "at": "beat:menu-0.3"},
         {"id": "reorder_2", "text": "The order is saved with your workspace.", "at": "beat:dropped"},
     ]},
    {"take": "terminal", "from": "beat:type-0.4", "to": "beat:epoch5+0.6",
     "kicker": "Terminal", "title": "Terminal titles in the Running panel",
     "hide_keys": ["Enter"],
     "say": [
         {"id": "term_1", "text": "A program can set the title of its terminal.", "at": "beat:run"},
         {"id": "term_2", "text": "In 4.7 the Running panel shows these titles too, so you can follow a long job at a glance.", "at": "beat:title"},
     ]},

    {"take": "mathsearch", "zoom_cap": 1.25, "from": "beat:find-0.4", "to": "beat:next1+1.5", "chapter": "Markdown and math",
     "kicker": "Search", "title": "Search inside rendered math",
     "say": [
         {"id": "msearch_1", "text": "Markdown previews can be searched in 4.7, even inside rendered formulas.", "at": "beat:find-0.4"},
         {"id": "msearch_2", "text": "The same works for formulas in cell outputs."},
     ]},
    {"take": "math", "from": 0.3, "to": "beat:rendered+2.6",
     "kicker": "Math", "title": "Long formulas wrap",
     "say": [
         {"id": "math_1", "text": "JupyterLab 4.7 updates MathJax to version 4.1.", "at": "beat:render-0.8"},
         {"id": "math_2", "text": "Long formulas no longer run past the edge of the cell, and a double backslash starts a new line again.", "at": "beat:rendered"},
     ]},
    {"take": "mermaid", "from": "beat:menu-0.4", "to": "beat:dark+2.4",
     "kicker": "Diagrams", "title": "Mermaid diagrams follow the theme",
     "say": [
         {"id": "mermaid_1", "text": "Mermaid diagrams no longer keep the colors of the old theme: they are drawn again when you switch between light and dark.", "at": "beat:pick-0.8"},
     ]},

    {"take": "csv", "zoom_cap": 1.3, "from": 1.2, "to": "beat:found+2.4", "chapter": "Files and tools",
     "kicker": "CSV viewer", "title": "CSV comment lines",
     "hide_keys": ["Escape"],
     "say": [
         {"id": "csv_1", "text": "Comment lines at the top of a CSV file used to break its header."},
         {"id": "csv_2", "text": "Pick a comment character, and they are shown as comments.", "at": "beat:comment"},
         {"id": "csv_3", "text": "Search in CSV files was also improved: it shows the number of matches.", "at": "beat:find"},
     ]},
    {"take": "rkeys", "zoom_cap": 1.6, "from": "beat:type1-0.4", "to": "flash:end-0.15",
     "kicker": "R", "title": "Shortcuts for R operators",
     "hide_keys": ["Enter", "Control+End"],
     "say": [
         {"id": "r_1", "text": "R users get two familiar shortcuts:", "at": "beat:type1-0.4"},
         {"id": "r_2", "text": "Alt and minus for the assignment arrow,", "at": "beat:assign"},
         {"id": "r_3", "text": "and Control, Shift and M for the pipe.", "at": "beat:pipe"},
     ]},
    {"take": "sources", "from": "beat:enable-0.4", "to": "beat:expand+3.0",
     "kicker": "Debugger", "title": "Kernel sources as a tree",
     "speed": [{"from": "beat:enable+0.4", "to": "beat:panel-0.2", "x": 2}],
     "say": [
         {"id": "src_1", "text": "The kernel sources in the debugger used to be one long list.", "at": "beat:enable"},
         {"id": "src_2", "text": "This release groups them by package, in a tree.", "at": "beat:panel"},
     ]},

    {"take": "a11y", "from": "beat:type-0.4", "to": "beat:end+1.2", "chapter": "Accessibility",
     "kicker": "Accessibility", "title": "Settings from the keyboard", "keys_x": 0.15, "spot": False,
     "say": [
         {"id": "a11y_1", "text": "Parts of the Settings Editor used to need a mouse.", "at": "beat:type"},
         {"id": "a11y_2", "text": "Now the Tab key and the arrow keys reach the plugin list,", "at": "beat:tab"},
         {"id": "a11y_3", "text": "and every shortcut of the Keyboard Shortcuts editor, with the buttons next to it.", "at": "beat:shortcuts"},
     ]},

    {"card": "html", "length": 8.0, "chapter": "More", "html": MORE,
     "say": [
         {"id": "more_1", "text": "There is much more in this release.", "at": "+0.6"},
         {"id": "more_3", "text": "Notebook 7.7 and JupyterLite 0.9 build on JupyterLab 4.7, with changes of their own."},
         {"id": "more_2", "text": "The release notes list every change."},
     ]},

    {"card": "html", "length": 8.0, "music_outro": True, "html": OUTRO,
     "say": [
         {"id": "outro_1t" if TESTING else "outro_1", "text": f"JupyterLab 4.7 is {AVAILABLE}.", "at": "+0.5"},
         {"id": "outro_2", "text": "Thank you to the contributors, reviewers, and everyone who tested the betas and reported issues."},
     ]},
]


def main():
    voice = "piper"
    if "--voice" in sys.argv:
        voice = sys.argv[sys.argv.index("--voice") + 1]
    args = [a for i, a in enumerate(sys.argv[1:], 1) if a not in ("--nb-lite", "--voice") and sys.argv[i - 1] != "--voice"]
    out = Path(args[0])
    race46 = args[1] if len(args) > 1 else "stream-46f"
    race47 = args[2] if len(args) > 2 else "stream-47d"
    seq = json.loads(json.dumps(SEQUENCE).replace("RACE46", race46).replace("RACE47", race47))
    if "--nb-lite" in sys.argv:
        seq = with_nb_lite(seq)
    edit = {"work": str(WORK), "fps": 60, "preview_fps": 30, "bpm": 90, "clicks": True,
            # CC0: "Intergalactic Journey" by spinmeister, https://ccmixter.org/files/spinmeister/21067
            "music": str(WORK / "music/intergalactic-journey.wav"),
            "voice": str(WORK / "voice" / voice), "duck": 0.55, "music_gain": 0.32, "sequence": seq}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(edit, indent=1, ensure_ascii=False) + "\n")
    words = sum(len(l["text"].split()) for it in seq for l in it.get("say", []))
    print(out, len(seq), "parts,", words, "words of narration")


if __name__ == "__main__":
    main()
