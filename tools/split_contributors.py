"""Split the contributors of a release cycle into first-time and returning, from the "Contributors to this release" lists.

Usage: python split_contributors.py <out.json> [--lab 4.7 4.6.0] [--notebook 7.7 7.6.0] [--lite 0.9 0.8.0]

Each option gives the minor version of the cycle and the last release before it: a contributor is first-time when
no list up to that release names them. The changelogs come from the main branch of the three repositories, through
`gh api`, into work/changelogs; delete them there to fetch them again. The 4.7 video used the files of
19 November 2026. The output has the contributors of JupyterLab ("lab") and of all three projects ("all").
"""
import argparse, base64, json, os, re, subprocess
from pathlib import Path
from packaging.version import Version
LOGS = Path(os.environ.get("RV_CHANGELOGS", Path(__file__).resolve().parents[1] / "work" / "changelogs"))
SOURCES = {"lab-changelog.md": ("jupyterlab/jupyterlab", "CHANGELOG.md"),
           "lab-changelog-v3.md": ("jupyterlab/jupyterlab", "docs/source/getting_started/changelog_v3.md"),
           "nb-changelog.md": ("jupyter/notebook", "CHANGELOG.md"),
           "lite-changelog.md": ("jupyterlite/jupyterlite", "CHANGELOG.md")}


def fetch():
    LOGS.mkdir(parents=True, exist_ok=True)
    for name, (repo, path) in SOURCES.items():
        if not (LOGS / name).exists():
            content = subprocess.run(["gh", "api", f"repos/{repo}/contents/{path}", "--jq", ".content"],
                                     check=True, capture_output=True, text=True).stdout
            (LOGS / name).write_bytes(base64.b64decode(content))


fetch()
# github-activity wrote "[@name](search link)" before 2026 and "@name ([activity](...))" since.
HANDLES = [re.compile(r"@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))\s\(\[activity\]"),
           re.compile(r"\[@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))\]\(https://github\.com/search")]
BOTS = re.compile(r"bot$|\[bot\]|^pre-commit-ci$|^dependabot$|^github-actions$|^Copilot$|^claude$", re.I)

def sections(*paths):
    for path in paths:
        for part in re.split(r"\n(?=## )", (LOGS / path).read_text()):
            m = re.match(r"## v?(\d+\.\d+\.\d+\S*)\s*$", part.split("\n", 1)[0])
            if not m:
                continue
            c = re.search(r"### Contributors to this release(.*)", part, re.S)
            users = {u for h in HANDLES for u in h.findall(c.group(1))} if c else set()
            yield Version(m.group(1)), {u for u in users if not BOTS.search(u)}

def split(paths, cycle, last_before):
    now, before, empty, count = set(), set(), [], 0
    for v, users in sections(*paths):
        count += 1
        if (v.major, v.minor) == cycle:
            now |= users
        elif v <= Version(last_before):
            before |= users
        if not users:
            empty.append(str(v))
    print(paths[0], count, "sections, without names:", empty)
    return now, before

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--lab", nargs=2, default=["4.7", "4.6.0"])
ap.add_argument("--notebook", nargs=2, default=["7.7", "7.6.0"])
ap.add_argument("--lite", nargs=2, default=["0.9", "0.8.0"])
args = ap.parse_args()


def cycle(minor):
    return tuple(int(x) for x in minor.split("."))


lab_now, lab_before = split(["lab-changelog.md", "lab-changelog-v3.md"], cycle(args.lab[0]), args.lab[1])
nb_now, nb_before = split(["nb-changelog.md"], cycle(args.notebook[0]), args.notebook[1])
lite_now, lite_before = split(["lite-changelog.md"], cycle(args.lite[0]), args.lite[1])
# The contributors of the release: everyone in the lists of its pre-releases and releases.
lab_list = lab_now
all_list = lab_now | nb_now | lite_now
key = str.lower
lab_first = sorted(lab_list - lab_before, key=key)
all_first = sorted(all_list - (lab_before | nb_before | lite_before), key=key)
print("lab first-time", len(lab_first), "returning", len(lab_list) - len(lab_first))
print("all first-time", len(all_first), "returning", len(all_list) - len(all_first))
print("lab first:", " ".join(lab_first))
print("all first, not in lab first:", sorted(set(all_first) - set(lab_first), key=key), "| lab first, returning elsewhere:", sorted(set(lab_first) - set(all_first), key=key))
json.dump({"lab": {"first": lab_first, "returning": sorted(lab_list - set(lab_first), key=key)},
           "all": {"first": all_first, "returning": sorted(all_list - set(all_first), key=key)}},
          open(args.out, "w"), indent=1)
