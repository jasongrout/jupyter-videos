# Probes

A probe answers one question about the app before a take relies on it: where an element is, what a click does, what a style computes to. It opens a page like a take, takes screenshots into `$RV_TAKES/<probe name>/`, and prints what it finds. Run one with `node harness/probes/<file> [args]` against the server that the take will use.

| Probe | Question |
| --- | --- |
| `probe_aicell.js` | Jupyter AI Lite next to a notebook: can a failing cell be dragged into the chat, and does Replace selection put the answer into the cell? |
| `probe_ailite.js` | What do the chat and its settings look like in the Jupyter AI Lite online demo, without an API key? |
| `probe_ailite2.js` | Where are the Jupyternaut settings in the Settings menu of the demo? |
| `probe_ailite3.js` | What does the Add Provider dialog ask for with the Generic (OpenAI-compatible) provider? |
| `probe_ailocal.js` | Does Jupyter AI Lite in JupyterLab 4.7 answer through a local model: add the provider, open a chat, ask? |
| `probe_downtab.js` | Why does the Help tab of the down panel look different in Notebook and JupyterLab: computed styles and matching CSS rules. |
| `probe_lite.js` | In the JupyterLite docs demo: the toast buttons, the extension list, and what Disable does. |
| `probe_logtab.js` | Is the icon of the Log Console tab in Notebook's down area centred on its label? |
| `probe_panelwidth.js` | Does the left panel keep a dragged width after it is collapsed and opened from another sidebar tab? |
| `probe_saveas.js` | Where is the focus in the Save As dialog of a view-only notebook, and what does Enter do? |
| `probe_select.js` | Does the CSV Comment menu render inside the page with `appearance: base-select`, so that the screencast captures it? |
| `probe_select2.js` | The computed styles of the CSV Comment select with and without `appearance: base-select`. |
| `probe_status.js` | What does the status bar say for a notebook with No Kernel, and for a view-only one? |
| `probe_stream.js` | How long does the race take without the recorder: `node probe_stream.js <port>` prints the times of one run. |
