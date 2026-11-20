"""Narration of the combined cut, then what the JupyterLab cut changes: python make_script.py <combined plan> <lab plan> <out.md>

The plans are the .plan.json files that cut.py writes next to each cut.
"""
import json
import sys
from pathlib import Path

nb_plan, lab_plan, out = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), Path(sys.argv[3])


def stamp(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def title(row, rows=None):
    if row.get("title"):
        return row["title"]
    if row["what"] == "card title":
        return "Title card"
    if row.get("chapter") and row.get("chapter") != "More":
        return row["chapter"]
    if rows is not None:
        whats = [r["what"] for r in rows]
        if "ai-local" in whats and rows.index(row) > whats.index("ai-local"):
            return "Get started with AI in Jupyter"
    return "And more" if row.get("chapter") == "More" else "Upgrade"


lines = ["# JupyterLab 4.7 release video: narration", "",
         "This is the voice-over of the combined cut, one section per shot, with the time each line starts. \"The point 7 releases\" names JupyterLab 4.7 and Notebook 7.7 together. The source is `edit/make_edit.py`.", ""]
for row in nb_plan:
    head = f"{row.get('kicker')}: {title(row, nb_plan)}" if row["what"] in ("nb-help", "lite-extensions", "ai-local") else title(row, nb_plan)
    lines += [f"## {int(row['start'] // 60)}:{int(row['start'] % 60):02d} {head}", ""]
    lines += [f"- {stamp(l['start'])} {l['text']}" for l in row["lines"]] or ["No narration."]
    lines.append("")
nb_text = {l["id"]: l["text"] for row in nb_plan for l in row["lines"]}
lab_ids = {l["id"] for row in lab_plan for l in row["lines"]}
lines += ["## JupyterLab cut", "",
          "The JupyterLab cut leaves out the Notebook 7.7 and JupyterLite 0.9 shots and changes these lines:", ""]
for row in lab_plan:
    for l in row["lines"]:
        if l["id"] + "p" in nb_text:
            lines.append(f"- {stamp(l['start'])} \"{l['text']}\" for \"{nb_text[l['id'] + 'p']}\"")
        elif l["id"] not in nb_text:
            lines.append(f"- {stamp(l['start'])} adds \"{l['text']}\"")
lines.append("")
out.write_text("\n".join(lines))
print(out)
