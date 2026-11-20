'use strict';
// The Jupyter AI Lite online demo: what the chat and its settings look like, without an API key.
const { startTake } = require('../rv');
const URL = 'https://jupyterlab.github.io/jupyter-ai-lite/lab/index.html';
(async () => {
  const take = await startTake({ name: 'probe-ailite', port: 0, width: 1152, height: 648, dsf: 1 });
  const { page } = take;
  try {
    page.setDefaultTimeout(60000);
    await page.goto(URL);
    await page.waitForSelector('#jp-main-dock-panel, .jp-LabShell', { timeout: 90000 });
    await page.waitForTimeout(6000);
    await page.screenshot({ path: `${take.dir}/start.png` });
    console.log('app exposed:', await page.evaluate(() => !!window.jupyterapp));
    console.log('left tabs:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.jp-SideBar .lm-TabBar-tab')).map(t => t.getAttribute('title') || t.textContent.trim()))));
    console.log('settings menu:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.lm-MenuBar-itemLabel')).map(e => e.textContent))));
  } finally {
    await take.browser.close();
  }
})();
