'use strict';
// JupyterLite docs demo: toast buttons, extension list, and what Disable does.
const { startTake } = require('../rv');
const URL = 'https://jupyterlite.readthedocs.io/en/latest/_static/lab/index.html';
(async () => {
  const take = await startTake({ name: 'probe-lite', port: 0, width: 1152, height: 648, dsf: 1 });
  const { page } = take;
  try {
    page.setDefaultTimeout(60000);
    await page.goto(URL);
    await page.waitForFunction(() => window.jupyterapp && window.jupyterapp.restored, null, { timeout: 90000 });
    await page.evaluate(() => window.jupyterapp.restored);
    await page.waitForTimeout(3000);
    console.log('toasts:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.Toastify button')).map(b => b.className + ' | ' + b.textContent.trim()))));
    console.log('commands:', JSON.stringify(await page.evaluate(() => window.jupyterapp.commands.listCommands().filter(c => /notif|extensionmanager|plugin/i.test(c)))));
    const tab = page.locator('.jp-SideBar.jp-mod-left .lm-TabBar-tab[title*="Extension"]').first();
    await tab.click();
    await page.waitForTimeout(1500);
    console.log('entries:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.jp-extensionmanager-entry')).map(e => e.querySelector('.jp-extensionmanager-entry-name, a, .jp-extensionmanager-entry-title')?.textContent.trim() + ' :: ' + Array.from(e.querySelectorAll('button')).map(b => b.textContent.trim()).join('/')))));
    console.log('files:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.jp-DirListing-itemText')).map(e => e.textContent.trim()))));
    await page.screenshot({ path: `${take.dir}/list.png` });
    const theme = page.locator('.jp-extensionmanager-entry').filter({ hasText: /night|theme|geojson/i }).first();
    console.log('pick:', await theme.textContent().catch(() => 'none'));
    await theme.locator('button').filter({ hasText: /Disable/ }).first().click();
    await page.waitForTimeout(1500);
    console.log('dialog:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.jp-Dialog-header, .jp-Dialog-body, .jp-Dialog-footer button')).map(e => e.textContent.trim()))));
    await page.screenshot({ path: `${take.dir}/disable.png` });
  } finally {
    await take.browser.close();
  }
})();
