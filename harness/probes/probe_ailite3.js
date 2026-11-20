'use strict';
// Jupyter AI Lite demo: the Add Provider dialog and the Generic (OpenAI-compatible) provider.
const { startTake } = require('../rv');
const URL = 'https://jupyterlab.github.io/jupyter-ai-lite/lab/index.html';
(async () => {
  const take = await startTake({ name: 'probe-ailite3', port: 0, width: 1152, height: 648, dsf: 1 });
  const { page } = take;
  try {
    page.setDefaultTimeout(30000);
    await page.goto(URL);
    await page.waitForSelector('#jp-main-dock-panel', { timeout: 90000 });
    await page.waitForTimeout(5000);
    await page.locator('.lm-MenuBar-itemLabel', { hasText: 'Settings' }).click();
    await page.locator('.lm-Menu-itemLabel', { hasText: 'Jupyternaut Settings' }).click();
    await page.getByRole('button', { name: /Add Provider/i }).click();
    await page.waitForTimeout(1200);
    await page.screenshot({ path: `${take.dir}/add.png` });
    const texts = await page.evaluate(() => Array.from(document.querySelectorAll('[role=dialog] label, [role=dialog] [role=combobox], [role=dialog] input, [role=dialog] button')).map(e => (e.getAttribute('aria-label') || e.textContent || e.getAttribute('placeholder') || '').trim()).filter(Boolean));
    console.log('dialog:', JSON.stringify(texts));
    // Open the provider list.
    const combo = page.locator('[role=dialog] [role=combobox]').first();
    if (await combo.count()) {
      await combo.click();
      await page.waitForTimeout(800);
      console.log('options:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('[role=option]')).map(o => o.textContent.trim()))));
      await page.screenshot({ path: `${take.dir}/providers.png` });
      const generic = page.locator('[role=option]').filter({ hasText: /Generic|OpenAI-compatible/ }).first();
      if (await generic.count()) {
        await generic.click();
        await page.waitForTimeout(1000);
        await page.screenshot({ path: `${take.dir}/generic.png` });
        const url = page.locator('[role=dialog] input').filter({ has: page.locator('xpath=.') }).nth(0);
        const base = page.getByLabel('Base URL');
        await base.click();
        await page.waitForTimeout(800);
        console.log('suggestions:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('[role=option], [role=listbox] li')).map(o => o.textContent.trim()))));
        await page.screenshot({ path: `${take.dir}/baseurl.png` });
        const model = page.getByLabel('Model');
        await model.click();
        await page.waitForTimeout(800);
        console.log('models:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('[role=option], [role=listbox] li')).map(o => o.textContent.trim()).slice(0, 15))));
        console.log('after generic:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('[role=dialog] label, [role=dialog] input')).map(e => (e.textContent || e.getAttribute('placeholder') || e.value || '').trim()).filter(Boolean))));
      }
    }
  } finally {
    await take.browser.close();
  }
})();
