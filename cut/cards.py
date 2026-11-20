"""The HTML of the cards that a project's edit can use. cut.py renders a card's HTML with style.css.

- opening_card: a kicker and a large title, for the "intro" of a race, which puts the app beside them.
- areas_card: a heading over areas, each with an icon, a title and short lines; also() starts a second group.
- end_card: install commands and the ways to support Project Jupyter on the left, the credits on the right.
- addendum_card: one large line, such as the title of a chapter after the end card.

WORDMARK in a card's HTML becomes the JupyterLab wordmark. icon() reads JupyterLab's own icons from a checkout
(JUPYTERLAB_SRC) or the build copy of setup/build_main.sh.
"""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ICONS = Path(os.environ.get("JUPYTERLAB_SRC", Path(os.environ.get("RV_BASE", REPO / "work/runtime")) / "main")) / "packages/ui-components/style/icons"

JUPYTER_LOGO = '<svg viewBox="0 0 152 165"><path fill="#F37726" d="M76.021 140.163c-32.64 0-61.145-11.927-75.942-29.58 5.51 15.84 15.781 29.567 29.39 39.278a80.17 80.17 0 0 0 46.57 14.929 80.17 80.17 0 0 0 46.57-14.929c13.61-9.711 23.88-23.437 29.391-39.278-14.833 17.653-43.338 29.58-75.979 29.58m-.005-114.832c32.64 0 61.146 11.927 75.943 29.58a80.9 80.9 0 0 0-29.391-39.278A80.16 80.16 0 0 0 75.998.705a80.16 80.16 0 0 0-46.57 14.928A80.9 80.9 0 0 0 .038 54.912c14.832-17.617 43.338-29.58 75.978-29.58"/></svg>'

# The GitHub mark (Octicons "mark-github"), for the links to the repositories.
GITHUB_MARK = '<svg viewBox="0 0 16 16"><path fill="#1f2328" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'


def icon(name):
    """A JupyterLab icon by its path under packages/ui-components/style/icons, such as "sidebar/users.svg"."""
    svg = (ICONS / name).read_text()
    return svg.replace("<svg ", '<svg width="34" height="34" ', 1) if "width=" not in svg.split(">")[0] else svg


def area(icon_file, title, items):
    rows = "".join(f"<div>{x}</div>" for x in items)
    return f'<div class="area"><h2>{icon(icon_file)}{title}</h2>{rows}</div>'


def jupyter_area(title, items):
    """An area under the Jupyter logo, for another Jupyter project."""
    rows = "".join(f"<div>{x}</div>" for x in items)
    return f'<div class="area"><h2>{JUPYTER_LOGO}{title}</h2>{rows}</div>'


def also(text):
    """The heading of a second group of areas on an areas card."""
    return f'<div class="also">{text}</div>'


def areas_card(heading, blocks):
    return f'<div class="areas"><h1>{heading}</h1>' + "".join(blocks) + "</div>"


def opening_card(title_lines, kicker="Release highlights", sub=None):
    html = '<div class="intro"><div class="intro-kicker">' + JUPYTER_LOGO + kicker + "</div>"
    html += '<div class="intro-title">' + "<br>".join(title_lines) + "</div>"
    if sub:
        html += f'<div class="intro-sub">{sub}</div>'
    return html + "</div>"


def addendum_card(text):
    return f'<div class="card"><div class="addendum">{text}</div></div>'


def end_card(version, install, repos, managers, contributors, thanks):
    """The end card. contributors is {"first": [...], "returning": [...]}, from tools/split_contributors.py."""
    if len(repos) == 1:
        stars = f'<div><b>Star on GitHub:</b> {repos[0]}</div>'
    else:
        stars = '<div><b>Star on GitHub:</b><div class="repos">' + "".join(f"<div>{r}</div>" for r in repos) + "</div></div>"
    left = (
        f'<div class="lockup">WORDMARK<div class="ver">{version}</div></div>'
        + "".join(f'<div><span class="cmd">{c}</span></div>' for c in install)
        + '<div class="support"><div class="support-head">Support Project Jupyter</div>'
        + '<div class="support-item">' + JUPYTER_LOGO + '<div><b>Join the Jupyter Foundation (for organizations):</b> jupyterfoundation.org/join</div></div>'
        + '<div class="support-item">' + GITHUB_MARK + stars + '</div>'
        + '<div class="support-item">' + icon("sidebar/users.svg") + '<div><b>Join the community and contribute:</b> jupyter.org/community</div></div>'
        + '</div>'
    )

    def names(users):
        return '<div class="names">' + " ".join(f"<span>@{u}</span>" for u in users) + "</div>"

    right = (
        f'<div class="thanks">{thanks}</div>'
        + ('<div class="managers"><b>Release managers:</b>' + "".join(f"<div>{m}</div>" for m in managers) + '</div>' if len(managers) > 1
           else f'<div class="managers"><b>Release manager:</b> {managers[0]}</div>')
        + '<div class="names-head">First-time contributors</div>' + names(contributors["first"])
        + '<div class="names-head">Returning contributors and maintainers</div>' + names(contributors["returning"])
    )
    return f'<div class="outro two"><div class="col">{left}</div><div class="col credits">{right}</div></div>'
