'use strict';
// Jupyter AI Lite next to a notebook, with a model on this machine: a local OpenAI-compatible server
// (scripts/local_llm_server.py, Gemma 4 E4B on http://localhost:8080/v1). A cell fails on a CSV file with comment
// lines; the cell goes into the chat, the answer replaces the cell, and the next cell shows the table.
const fs = require('fs');
const { BASE } = require('../../../harness/paths');
const QUESTION = 'How do I make pandas skip the # comment lines in this file?';

const NOTEBOOK = {
  cells: [
    { cell_type: 'markdown', id: 'title', metadata: {}, source: '# Weather stations\n\nDaily measurements of five European stations in October 2026.' },
    { cell_type: 'code', id: 'imports', metadata: {}, execution_count: null, outputs: [], source: 'import pandas as pd' },
    { cell_type: 'code', id: 'load', metadata: {}, execution_count: null, outputs: [], source: 'weather = pd.read_csv("weather.csv")' },
    { cell_type: 'code', id: 'show', metadata: {}, execution_count: null, outputs: [], source: 'weather.head()' },
    // Run and select next stops here instead of adding an empty cell.
    { cell_type: 'markdown', id: 'next', metadata: {}, source: '## Warmest days' }
  ],
  // This kernel has pandas; the kernel of the 4.7.0b2 environment does not.
  metadata: { kernelspec: { display_name: 'Python 3 (ipykernel)', language: 'python', name: 'python3-data' }, language_info: { name: 'python' } },
  nbformat: 4,
  nbformat_minor: 5
};

module.exports = {
  name: 'ai-local',
  port: 8962,
  async setup(take) {
    const { page, lab, H } = take;
    // Start from no provider and no chat. Completions stay off, so that no request competes with the chat.
    fs.rmSync(`${BASE}/settings/@jupyter-ai`, { recursive: true, force: true });
    fs.mkdirSync(`${BASE}/settings/@jupyter-ai/jupyternaut-lite`, { recursive: true });
    fs.writeFileSync(`${BASE}/settings/@jupyter-ai/jupyternaut-lite/settings-model.jupyterlab-settings`,
      JSON.stringify({ useSameProviderForChatAndCompleter: false }));
    fs.rmSync(`${BASE}/root/untitled.chat`, { force: true });
    fs.copyFileSync(`${BASE}/root/data/measurements.csv`, `${BASE}/root/weather.csv`);
    fs.writeFileSync(`${BASE}/root/weather.ipynb`, JSON.stringify(NOTEBOOK, null, 1));
    // A different prompt clears the server's prompt cache, so that the model reads the whole question, as a first question would.
    await fetch('http://localhost:8080/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: [{ role: 'system', content: 'Say hi.' }, { role: 'user', content: 'Hi' }], max_tokens: 1 })
    }).then(r => r.text());
    await lab.open();
    await lab.openFile('weather.ipynb');
    await page.waitForTimeout(1500);
    // The chat panel opens at this width later: wide enough for the code of the answer.
    const handle = await page.locator('#jp-main-split-panel > .lm-SplitPanel-handle').first().boundingBox();
    await page.mouse.move(handle.x + handle.width / 2, 300);
    await page.mouse.down();
    await page.mouse.move(33 + 485, 300, { steps: 8 });
    await page.mouse.up();
    await page.locator('.jp-SideBar .lm-TabBar-tab[title^="File Browser"]').click();
    await page.waitForTimeout(300);
    // One-line errors, and the failing cell run before the shot starts.
    await page.evaluate(async () => {
      const nb = window.jupyterapp.shell.currentWidget;
      await nb.sessionContext.ready;
      await nb.sessionContext.session.kernel.requestExecute({ code: '%xmode Minimal', silent: true }).done;
      nb.content.activeCellIndex = 1;
      await window.jupyterapp.commands.execute('notebook:run-cell-and-select-next');
      await window.jupyterapp.commands.execute('notebook:run-cell');
    });
    await page.locator('.jp-OutputArea-output[data-mime-type="application/vnd.jupyter.stderr"]').first().waitFor();
    await page.evaluate(() => { window.jupyterapp.shell.currentWidget.content.activeCellIndex = 2; });
    await page.waitForTimeout(1000);
    await H.place(page, 760 * take.k, 470 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    page.setDefaultTimeout(30000);
    await H.pause(700);
    take.beat('settings');
    await H.click(page, page.locator('.lm-MenuBar-itemLabel', { hasText: 'Settings' }));
    await page.waitForTimeout(300);
    await H.click(page, page.locator('.lm-Menu-itemLabel', { hasText: 'Jupyternaut Settings' }));
    const addButton = page.getByRole('button', { name: /Add Provider/i });
    await addButton.waitFor();
    await page.waitForTimeout(600);
    take.beat('add');
    await H.click(page, addButton);
    const dialog = page.locator('[role=dialog]');
    await dialog.waitFor();
    await page.waitForTimeout(400);
    await take.focus('dialog', '[role=dialog] .MuiDialog-paper, [role=dialog]', { zoom: 1.12, pad: 6, content: false });
    await H.click(page, page.getByLabel('Provider Name'));
    await H.type(page, 'Local model', { cps: 12 });
    take.beat('type');
    await H.click(page, dialog.locator('[role=combobox]').first());
    await page.locator('[role=option]').first().waitFor();
    await H.pause(400);
    await H.click(page, page.locator('[role=option]').filter({ hasText: 'Generic (OpenAI-compatible)' }).first());
    await page.waitForTimeout(500);
    take.beat('model');
    await H.click(page, page.getByLabel('Model'));
    await H.type(page, 'gemma-4-e4b', { cps: 12 });
    take.beat('url');
    await H.click(page, page.getByLabel('Base URL'));
    await H.pause(500);
    await H.type(page, 'http://localhost:8080/v1', { cps: 16 });
    await H.pause(400);
    // Close the suggestions with a click on the dialog title, not Escape, which would close the dialog.
    await H.click(page, dialog.locator('h2, .MuiDialogTitle-root').first());
    await H.pause(400);
    take.beat('added');
    await H.click(page, dialog.locator('button').filter({ hasText: /^Add Provider$/i }).first());
    await dialog.waitFor({ state: 'hidden' });
    take.unfocus();
    await H.pause(700);
    take.beat('notebook');
    const settingsTab = page.locator('#jp-main-dock-panel .lm-TabBar-tab').filter({ hasText: 'Jupyternaut Settings' }).first();
    await H.click(page, settingsTab.locator('.lm-TabBar-tabCloseIcon'));
    await settingsTab.waitFor({ state: 'detached' });
    await H.pause(700);
    take.beat('chat');
    await H.click(page, page.locator('.jp-SideBar .lm-TabBar-tab[title="Jupyter Chat"]'));
    await page.waitForTimeout(500);
    await H.click(page, page.getByRole('button', { name: /New chat/i }).first());
    const input = page.locator('#jp-left-stack textarea[placeholder^="Type a chat message"]').first();
    await input.waitFor();
    await page.waitForTimeout(600);
    take.beat('drag');
    const prompt = page.locator('.jp-Notebook .jp-CodeCell').nth(1).locator('.jp-InputPrompt');
    await H.drag(page, prompt, input, { hoverMs: 450, ms: 900 });
    await page.locator('#jp-left-stack .jp-chat-attachment').first().waitFor();
    take.beat('attached');
    await H.pause(500);
    take.beat('ask');
    await H.click(page, input);
    await H.type(page, QUESTION, { cps: 16 });
    await H.pause(300);
    // The cut maps the server's wall-clock times of the answer into the take with this mark.
    take.mark('wall', { epoch: Date.now() / 1000 });
    await page.keyboard.press('Enter');
    take.beat('sent');
    // The cut plays the answer faster, to take out the slowdown from the recorder, and the caret would blink faster too.
    const caret = await page.addStyleTag({ content: '#jp-left-stack textarea { caret-color: transparent !important; }' });
    // The answer streams in; the Stop button goes away when it is complete.
    const stop = page.getByRole('button', { name: /Stop generating/i });
    await page.locator('#jp-left-stack .jp-chat-code-toolbar').first().waitFor({ timeout: 600000 });
    for (let i = 0; i < 1200; i++) {
      const busy = await stop.isEnabled().catch(() => false) && await stop.isVisible().catch(() => false);
      if (!busy) break;
      await page.waitForTimeout(100);
    }
    take.beat('answered');
    await caret.evaluate(e => e.remove());
    await H.pause(1200);
    take.beat('replace');
    const replace = page.locator('#jp-left-stack .jp-chat-code-toolbar .jp-chat-code-toolbar-item').nth(2);
    await H.click(page, replace);
    await page.waitForFunction(() => window.jupyterapp.shell.currentWidget.content.widgets[2].model.sharedModel.getSource().includes('comment'));
    await H.pause(900);
    take.beat('run');
    const runButton = page.locator('.jp-NotebookPanel-toolbar [data-command="notebook:run-cell-and-select-next"]').first();
    await H.click(page, runButton);
    await H.pause(700);
    await H.click(page, runButton);
    await page.locator('.jp-Notebook .jp-CodeCell').nth(2).locator('.jp-OutputArea-output table').first().waitFor();
    take.beat('result');
    // An empty part of the notebook toolbar: no hover state while the table shows.
    const spacer = page.locator('.jp-NotebookPanel-toolbar .jp-Toolbar-spacer').first();
    const box = (await spacer.count()) ? await spacer.boundingBox() : null;
    console.log('pointer parked on', box ? 'the toolbar spacer' : 'the fallback point');
    await H.moveTo(page, box ? box.x + box.width / 2 : 1300 * take.k, box ? box.y + box.height / 2 : 700 * take.k);
    await H.pause(3200);
    console.log('answer:', JSON.stringify((await page.locator('#jp-left-stack').innerText()).slice(-700)));
    take.beat('end');
  }
};
