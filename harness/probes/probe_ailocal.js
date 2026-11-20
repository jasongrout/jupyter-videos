'use strict';
// Jupyter AI Lite in JupyterLab 4.7 with a local model: add the provider, open a chat, ask a question.
const { startTake } = require('../rv');
(async () => {
  const take = await startTake({ name: 'probe-ailocal', port: 8962, width: 1152, height: 648, dsf: 1 });
  const { page, lab } = take;
  const shot = async n => page.screenshot({ path: `${take.dir}/${n}.png` });
  try {
    page.setDefaultTimeout(20000);
    await lab.open();
    await lab.openFile('stations.ipynb');
    await page.waitForTimeout(1500);
    console.log('settings items:', JSON.stringify(await page.evaluate(() => window.jupyterapp.commands.listCommands().filter(c => /jupyternaut|chat|persona|ai/i.test(c)).slice(0, 40))));
    await page.locator('.lm-MenuBar-itemLabel', { hasText: 'Settings' }).click();
    await page.locator('.lm-Menu-itemLabel', { hasText: 'Jupyternaut Settings' }).click();
    await page.getByRole('button', { name: /Add Provider/i }).click();
    await page.locator('[role=dialog]').waitFor();
    await page.getByLabel('Provider Name').fill('Local model');
    await page.locator('[role=dialog] [role=combobox]').first().click();
    await page.locator('[role=option]').filter({ hasText: 'Generic (OpenAI-compatible)' }).first().click();
    await page.getByLabel('Model').fill('gemma-4-e4b');
    await page.getByLabel('Base URL').fill('http://localhost:8080/v1');
    await page.keyboard.press('Escape').catch(() => null);
    await shot('1-dialog');
    const add = page.locator('[role=dialog] button').filter({ hasText: /^Add Provider$/i }).first();
    console.log('add enabled:', await add.isEnabled());
    await add.click();
    await page.waitForTimeout(1200);
    await shot('2-added');
    await page.locator('.jp-SideBar .lm-TabBar-tab[title="Jupyter Chat"]').click();
    await page.waitForTimeout(800);
    await shot('3-chatpanel');
    const newChat = page.getByRole('button', { name: /New chat/i }).first();
    await newChat.click();
    await page.waitForTimeout(1500);
    await shot('4-newchat');
    console.log('dialog after new chat:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.jp-Dialog, [role=dialog]')).map(d => d.textContent.slice(0, 200)))));
    console.log('chat inputs:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('textarea, [contenteditable=true], button')).filter(e => e.closest('.jp-chat-input-container, .jp-chat-input, [class*=chat]')).map(e => e.tagName + ':' + (e.getAttribute('aria-label') || e.getAttribute('title') || e.textContent || e.getAttribute('placeholder') || '').trim().slice(0, 60)).slice(0, 30))));
  } finally {
    await take.browser.close();
  }
})();
