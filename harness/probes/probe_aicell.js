'use strict';
// Jupyter AI Lite next to a notebook: drag a failing cell into the chat, ask, replace the cell with the answer, run it.
const fs = require('fs');
const { startTake, H } = require('../rv');
const { BASE } = require('../paths');
const QUESTION = process.argv[2] || 'The file starts with # comment lines. How do I fix this cell?';

const NOTEBOOK = {
  cells: [
    { cell_type: 'markdown', id: 'title', metadata: {}, source: '# Weather stations\n\nDaily measurements of five European stations in October 2026.' },
    { cell_type: 'code', id: 'load', metadata: {}, execution_count: null, outputs: [], source: 'import pandas as pd\n\nweather = pd.read_csv("data/measurements.csv")\nweather.head()' }
  ],
  metadata: { kernelspec: { display_name: 'Python 3 (ipykernel)', language: 'python', name: 'python3-data' }, language_info: { name: 'python' } },
  nbformat: 4,
  nbformat_minor: 5
};

(async () => {
  fs.rmSync(`${BASE}/settings/@jupyter-ai`, { recursive: true, force: true });
  fs.mkdirSync(`${BASE}/settings/@jupyter-ai/jupyternaut-lite`, { recursive: true });
  fs.writeFileSync(`${BASE}/settings/@jupyter-ai/jupyternaut-lite/settings-model.jupyterlab-settings`, JSON.stringify({
    defaultProvider: 'local',
    useSameProviderForChatAndCompleter: false,
    providers: [{ id: 'local', name: 'Local model', provider: 'generic', model: 'gemma-4-e4b', baseURL: 'http://localhost:8080/v1' }]
  }, null, 1));
  fs.rmSync(`${BASE}/root/untitled.chat`, { force: true });
  fs.writeFileSync(`${BASE}/root/weather.ipynb`, JSON.stringify(NOTEBOOK, null, 1));
  const take = await startTake({ name: 'probe-aicell', port: 8962, width: 1152, height: 648, dsf: 1 });
  const { page, lab } = take;
  const shot = async n => page.screenshot({ path: `${take.dir}/${n}.png` });
  try {
    page.setDefaultTimeout(30000);
    await lab.open();
    await lab.openFile('weather.ipynb');
    await page.waitForTimeout(1500);
    await page.evaluate(async () => {
      const nb = window.jupyterapp.shell.currentWidget;
      await nb.sessionContext.ready;
      await nb.sessionContext.session.kernel.requestExecute({ code: '%xmode Minimal', silent: true }).done;
      nb.content.activeCellIndex = 1;
      await window.jupyterapp.commands.execute('notebook:run-cell');
    });
    await page.locator('.jp-OutputArea-output[data-mime-type="application/vnd.jupyter.stderr"]').first().waitFor();
    await page.waitForTimeout(800);
    await shot('1-error');
    await page.locator('.jp-SideBar .lm-TabBar-tab[title="Jupyter Chat"]').click();
    await page.waitForTimeout(800);
    await page.getByRole('button', { name: /New chat/i }).first().click();
    const input = page.locator('#jp-left-stack textarea[placeholder^="Type a chat message"]').first();
    await input.waitFor();
    await page.waitForTimeout(800);
    console.log('left panel width:', await page.evaluate(() => document.querySelector('#jp-left-stack').getBoundingClientRect().width));
    await shot('2-chat');
    const prompt = page.locator('.jp-Notebook .jp-CodeCell .jp-InputPrompt').first();
    await H.drag(page, prompt, input, { hoverMs: 450, ms: 900 });
    await page.waitForTimeout(800);
    await shot('3-dragged');
    console.log('attachments:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('[class*=attachment]')).map(e => e.className + ': ' + e.textContent.trim().slice(0, 80)).slice(0, 8))));
    await input.click();
    await page.keyboard.type(QUESTION);
    await page.keyboard.press('Enter');
    const t0 = Date.now();
    const stop = page.getByRole('button', { name: /Stop generating/i });
    await page.waitForTimeout(3000);
    for (let i = 0; i < 1200; i++) {
      const busy = await stop.isEnabled().catch(() => false) && await stop.isVisible().catch(() => false);
      if (!busy) break;
      await page.waitForTimeout(500);
    }
    console.log('answered after', (Date.now() - t0) / 1000, 's');
    await page.waitForTimeout(1000);
    await shot('4-answer');
    const code = page.locator('.jp-chat-rendered-markdown pre, .jp-chat-messages pre').last();
    await code.hover();
    await page.waitForTimeout(600);
    await shot('5-hover');
    console.log('toolbar buttons:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('button')).map(b => b.getAttribute('title') || b.getAttribute('aria-label') || '').filter(t => /cell|selection|clipboard/i.test(t)))));
    console.log('code block style:', JSON.stringify(await code.evaluate(e => ({ ws: getComputedStyle(e).whiteSpace, ox: getComputedStyle(e).overflowX, w: e.getBoundingClientRect().width, sw: e.scrollWidth }))));
    const replace = page.locator('button[title^="Replace selection"], [aria-label^="Replace selection"]').last();
    await replace.click();
    await page.waitForTimeout(800);
    console.log('cell source after replace:', JSON.stringify(await page.evaluate(() => window.jupyterapp.shell.currentWidget.content.widgets[1].model.sharedModel.getSource())));
    await shot('6-replaced');
    await page.locator('.jp-NotebookPanel-toolbar [data-command="notebook:run-cell-and-select-next"], .jp-NotebookPanel-toolbar [data-command="notebook:run-cell"]').first().click();
    await page.waitForTimeout(3000);
    await shot('7-run');
    const reqs = fs.readdirSync(`${BASE}/llm-requests`).sort();
    const last = JSON.parse(fs.readFileSync(`${BASE}/llm-requests/${reqs[reqs.length - 1]}`));
    console.log('last request user message:', JSON.stringify(last.messages.filter(m => m.role === 'user').slice(-1)[0].content).slice(0, 1500));
  } finally {
    await take.browser.close();
  }
})();
