# Notebook 7.7 and JupyterLite 0.9 for the 4.7 video

Checked on 2026-11-18 with `gh` and the PyPI JSON API, without installing or running anything. "From the code" marks claims read from plugin lists and diffs, and nobody checked those in a browser.

## 1. Jupyter Notebook 7.7

### Status

Notebook 7.7 pairs with JupyterLab 4.7. Each 7.7 pre-release on PyPI requires the matching JupyterLab pre-release, for example `jupyterlab>=4.7.0b1,<4.8` for 7.7.0b1. On `main`, `app/package.json` uses `@jupyterlab/*` `~4.7.0-beta.1`.

Notebook 7.7 is in beta. PyPI and GitHub give the same dates:

- 7.7.0a0: 2026-07-06, on JupyterLab 4.7.0a0
- 7.7.0a1: 2026-07-22, on 4.7.0a1
- 7.7.0a2: 2026-09-23, on 4.7.0a2
- 7.7.0b0: 2026-10-29, on 4.7.0b0
- 7.7.0b1: 2026-11-09, on 4.7.0b1

The latest stable release is 7.6.5 (2026-11-06). JupyterLab 4.7.0b2 came out on 2026-11-16, but Notebook has no release or open PR on it yet. Notebook 7.6.0 shipped on the same day as JupyterLab 4.6.0. Since 7.7.0b0, Notebook needs Python 3.11 or newer: https://github.com/jupyter/notebook/pull/8084.

The 7.7.0 milestone has 86 closed and 39 open items: https://github.com/jupyter/notebook/milestone/61. There is no "7.7 Release Plan" issue. The last one was for 7.6: https://github.com/jupyter/notebook/issues/7786.

### Notebook's own user-facing changes

There are 10: six enhancements and four fixes. None of them is in a 7.6.x release.

- Help from `object?` opens in a bottom panel by default, as in the classic notebook. The "Show Help in Bottom Panel" setting turns it off (7.7.0a1): https://github.com/jupyter/notebook/pull/7713, for https://github.com/jupyter/notebook/issues/6692.
- Open With in the file browser offers "Notebook (no kernel)", and the notebook URL accepts `?kernel=none` (7.7.0a2): https://github.com/jupyter/notebook/pull/8039, for https://github.com/jupyter/notebook/issues/3170.
- New > Terminal starts the terminal in the folder that the file browser shows (7.7.0a2): https://github.com/jupyter/notebook/pull/8041, for https://github.com/jupyter/notebook/issues/1898.
- Help > About Jupyter opens a dialog instead of the website (7.7.0a2): https://github.com/jupyter/notebook/pull/8020.
- The `/tree`, `/notebooks` and `/edit` URLs accept `?open-with=`, for example `?open-with=txt` (7.7.0b1): https://github.com/jupyter/notebook/pull/8122.
- Disabled prebuilt extensions are no longer loaded at startup (7.7.0a2): https://github.com/jupyter/notebook/pull/8056.
- The Editor Syntax Highlighting menu shows only in the file editor: https://github.com/jupyter/notebook/pull/8038.
- The Advanced Tools section of the property inspector expands in translated interfaces: https://github.com/jupyter/notebook/pull/8037.
- A folder named `notebooks`, `consoles` or `terminals` in a path no longer gives a "File Load Error": https://github.com/jupyter/notebook/pull/7903 and https://github.com/jupyter/notebook/pull/8091.
- The kernel status and more strings can be translated: https://github.com/jupyter/notebook/pull/8013 and https://github.com/jupyter/notebook/pull/8029.

### JupyterLab 4.7 features in Notebook 7.7.0b1

Notebook 7.7.0b1 bundles the JupyterLab 4.7.0b1 front-end packages, so features first released in 4.7.0b2 are missing until Notebook updates.

- View-only notebooks: yes, since 7.7.0b0. The update PR makes "Not Trusted" do nothing for them: https://github.com/jupyter/notebook/pull/8108.
- Lock icon on read-only cells: yes, since 7.7.0b0, because Notebook loads the whole cell toolbar extension (https://github.com/jupyterlab/jupyterlab/pull/19789).
- Help in a bottom panel: yes, and on by default.
- Recent commands in the palette: yes, but from the code the list is not saved, because Notebook does not load `palette-restorer` (https://github.com/jupyterlab/jupyterlab/pull/19175). Every notebook opens in a new page, so the list starts empty for each one.
- MathJax 4.1: no. It came in JupyterLab 4.7.0b2 (https://github.com/jupyterlab/jupyterlab/pull/19815), and the Notebook lockfile on `main` still has `mathjax-full` 3.2.2.
- Current search match marked in rendered Markdown: no release has it, because the JupyterLab PR is still open: https://github.com/jupyterlab/jupyterlab/pull/20432. Notebook loads the notebook search plugin, so it will get the change.
- Also in Notebook: the cell ID in the property inspector, the `input()` style, the CSV viewer and the Kernel Sources tree.
- Missing in Notebook, from the code: Copy Image and section reordering. The Copy Image command is in `@jupyterlab/application-extension:commands`, and Notebook loads that plugin only on the tree page. Notebook does not load `@jupyterlab/apputils-extension:move-sections` at all.

## 2. JupyterLite 0.9

### Status

JupyterLite 0.9 uses JupyterLab 4.7 and Notebook 7.7. On `main`, the apps use `@jupyterlab/*` `~4.7.0-beta.1` and `@jupyter-notebook/*` `~7.7.0-beta.1`, since https://github.com/jupyterlite/jupyterlite/pull/2108. No open PR updates JupyterLite to 4.7.0b2.

The `jupyterlite-core` dates on PyPI and GitHub agree:

- 0.9.0a0: 2026-07-10
- 0.9.0a1: 2026-08-03
- 0.9.0a2: 2026-09-24
- 0.9.0b0: 2026-10-29
- 0.9.0b1: 2026-11-09

The latest stable release is 0.8.7 (2026-10-30). JupyterLite 0.8.0 shipped five days after JupyterLab 4.6.0. The release plan has no timeline: https://github.com/jupyterlite/jupyterlite/issues/1991. `jupyterlite-core` 0.9 needs Python 3.11 or newer: https://github.com/jupyterlite/jupyterlite/pull/2082.

Kernels:

- `jupyterlite-pyodide-kernel` 0.9.0b0 (2026-11-10) requires `jupyterlite-core>=0.9.0b1`. It has no user-facing change over 0.8.7.
- `jupyterlite-xeus` 6.0.0 (2026-11-09) and its `main` require `jupyterlite-core<0.9.0`, and no PR is open to change the pin. So pip refuses xeus kernels next to 0.9. `jupyterlite-terminal` 1.7.1 has the same pin.

The public demo https://jupyterlite.github.io/demo runs 0.8.0. The docs demo https://jupyterlite.readthedocs.io/en/latest/_static/lab/index.html runs 0.9.0-beta.1, with 19 prebuilt extensions and a read-only notebook.

### JupyterLite's own user-facing changes since 0.8.7

There are 11: seven enhancements and four fixes. Fixes that 0.8.x also got are left out.

- The left sidebar has an Extension Manager that lists the extensions shipped with the site, with their versions: https://github.com/jupyterlite/jupyterlite/pull/2056.
- Users can disable and enable extensions there, and single plugins in the Advanced Plugin Manager. The browser keeps the choices, and they apply after a reload: https://github.com/jupyterlite/jupyterlite/pull/2059.
- `doc/` URLs open JupyterLab in the Simple Interface, for example `doc/index.html?path=intro.ipynb`: https://github.com/jupyterlite/jupyterlite/pull/2067, for https://github.com/jupyterlite/jupyterlite/issues/385.
- An opt-in, read-only "site drive" shows the configuration files of the site in the file browser: https://github.com/jupyterlite/jupyterlite/pull/2000.
- `notebooks/` without a file redirects to the tree, a file that cannot open shows "Cannot Open File", and `?path=` accepts folders: https://github.com/jupyterlite/jupyterlite/pull/2048.
- The `?open-with=` and `?kernel=none` URL parameters work as in JupyterLab and Notebook: https://github.com/jupyterlite/jupyterlite/pull/2108.
- Disabled prebuilt extensions are no longer loaded at startup: https://github.com/jupyterlite/jupyterlite/pull/2058.
- Opening a binary file as text shows an error: https://github.com/jupyterlite/jupyterlite/pull/2079.
- File names with `%` are decoded once: https://github.com/jupyterlite/jupyterlite/pull/2068.
- Recreating a folder from a kernel after deleting it in the file browser no longer raises `FileExistsError`: https://github.com/jupyterlite/jupyterlite/pull/2036.
- Five plugins of `@jupyterlite/apputils-extension` have new IDs, so `disabledExtensions` entries for them need updating: https://github.com/jupyterlite/jupyterlite/pull/2051.

### JupyterLab 4.7 features in JupyterLite

From the plugin lists, these work: view-only mode for files made read-only before the build (https://jupyterlite.readthedocs.io/en/latest/howto/content/readonly.html), the lock icon, the cell ID, Copy Image, section reordering, Markdown Preview search and the CSV viewer. Pyodide does not start for a view-only notebook. Recent commands survive a reload in the lab app, because it loads `palette-restorer`.

These do not work:

- Debugger features, such as the Kernel Sources tree, because no JupyterLite app includes `@jupyterlab/debugger-extension` (request: https://github.com/jupyterlite/jupyterlite/issues/1653).
- Terminal features, because `jupyterlite-terminal` is pinned below 0.9.
- Help in a bottom panel, from the code: the Pyodide kernel returns payloads, but it does not register the pager hook that ipykernel uses, so `object?` prints in the cell output.
- Server features: config file errors, authorizer checks, and the nbconvert and translation startup changes.
- JupyterLab 4.7.0b2 features, until JupyterLite updates: MathJax 4.1, Show Toolbar, paste into the selected folder, and the fix for files deleted when dropped on their folder's breadcrumb (https://github.com/jupyterlab/jupyterlab/pull/20424).

## 3. Best shots

### Notebook 7.7

Setup with Python 3.11 or newer: `pip install "notebook==7.7.0b1" "jupyterlab==4.7.0b2"`, then `jupyter notebook`. The same environment serves JupyterLab 4.7.0b2 at `/lab`.

1. Help opens in a bottom panel. The user runs `import statistics` and `statistics.median?` in a cell, and the docstring opens in a panel below the notebook. The user keeps editing cells with the help in view. Works today.
2. Terminals open in the current folder. The user opens the `data/` folder in the tree and clicks New > Terminal, and `pwd` prints a path that ends in `data`. Works today.
3. Notebooks open without a kernel. The user right-clicks a notebook and picks Open With > Notebook (no kernel). The new tab shows "No Kernel" in the toolbar. Works today.
4. Read-only notebooks open in view-only mode. Skip this shot if the JupyterLab part shows it. After `chmod a-w reference.ipynb`, the notebook opens with the read-only indicator and no run buttons. File > Save Notebook As makes an editable copy.

MathJax 4.1 needs a Notebook release on JupyterLab 4.7.0b2 or later. The rendered Markdown search also needs https://github.com/jupyterlab/jupyterlab/pull/20432 merged.

### JupyterLite 0.9

Setup with Python 3.11 or newer: `pip install "jupyterlite-core[all]==0.9.0b1" "jupyterlite-pyodide-kernel==0.9.0b0" "jupyterlab-night==0.5.2"`. Put the notebooks in `files/`, then run `jupyter lite build --contents files --output-dir _output` and `jupyter lite serve`. The kernel downloads Pyodide 314.0.6 from cdn.jsdelivr.net when it first starts, so start it once before recording. The docs demo needs no build, but it changes with `main`.

1. Users disable extensions in the Extension Manager. The sidebar lists the shipped extensions with versions. Disable on the `jupyterlab-night` entry opens a dialog with a Reload button, and after the reload Settings > Theme no longer lists "JupyterLab Night". Enable brings it back. The JupyterLite UI tests run this sequence.
2. Read-only reference notebooks open in view-only mode. Run `chmod a-w files/reference.ipynb` before the build, or open `read-only.ipynb` on the docs demo. The notebook opens without starting a kernel, and editing and running are disabled. Save As then creates an editable copy in the browser.
3. A `doc/` link opens the Simple Interface. `doc/index.html?path=intro.ipynb` opens JupyterLab in the Simple Interface with that notebook.
4. A URL opens a notebook without a kernel. `notebooks/index.html?path=intro.ipynb&kernel=none` opens the notebook without starting Pyodide.

Nothing blocks these four shots today.

## 4. Existing "What's new" text

- JupyterLab: the `## v4.7` section of CHANGELOG.md on `main` (https://jupyterlab.readthedocs.io/en/latest/getting_started/changelog.html#v4-7), and the Discourse post "JupyterLab 4.7 beta - call for testing!" of 2026-11-16: https://discourse.jupyter.org/t/jupyterlab-4-7-beta-call-for-testing/39135.
- Notebook: CHANGELOG.md on `main` has no `## v7.7` section yet, only the generated 7.7.0a0 to 7.7.0b1 entries. The 7.6 highlights came in https://github.com/jupyter/notebook/pull/7954, six days before 7.6.0.
- JupyterLite: docs/changelog.md has no `## v0.9` section, only the generated 0.9 entries. The migration guide has a "v0.8.0 to v0.9.0" section on the Extension Manager, the plugin IDs and Python 3.11: https://jupyterlite.readthedocs.io/en/latest/migration.html.
- The blog and Discourse have no post for Notebook 7.7 or JupyterLite 0.9. The last release posts can serve as templates: https://blog.jupyter.org/posts/2026/jupyterlab-4-6-and-notebook-7-6-are-out/ and https://blog.jupyter.org/posts/2026/jupyterlite-0-8-is-released/.
