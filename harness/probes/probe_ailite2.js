'use strict';
// Jupyter AI Lite demo: the Settings menu and the Jupyternaut settings.
const { startTake } = require('../rv');
const URL = 'https://jupyterlab.github.io/jupyter-ai-lite/lab/index.html';
(async () => {
  const take = await startTake({ name: 'probe-ailite2', port: 0, width: 1152, height: 648, dsf: 1 });
  const { page } = take;
  try {
    page.setDefaultTimeout(30000);
    await page.goto(URL);
    await page.waitForSelector('#jp-main-dock-panel', { timeout: 90000 });
    await page.waitForTimeout(5000);
    await page.locator('.lm-MenuBar-itemLabel', { hasText: 'Settings' }).click();
    await page.waitForTimeout(500);
    console.log('settings items:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.lm-Menu-itemLabel')).map(e => e.textContent))));
    const item = page.locator('.lm-Menu-itemLabel').filter({ hasText: /Jupyternaut|AI/ }).first();
    if (await item.count()) {
      await item.click();
      await page.waitForTimeout(2500);
      await page.screenshot({ path: `${take.dir}/settings.png` });
      console.log('buttons:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.jp-MainAreaWidget button, .jp-MainAreaWidget [role=button]')).map(b => b.textContent.trim()).filter(Boolean).slice(0, 30))));
    } else {
      await page.keyboard.press('Escape');
    }
    // The chat panel.
    await page.locator('.jp-SideBar .lm-TabBar-tab[title="Jupyter Chat"]').click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `${take.dir}/chat.png` });
  } finally {
    await take.browser.close();
  }
})();
