'use strict';
// Notebook 7.7: help from object? opens in a panel below the notebook, by default.
const C = require('../common');

module.exports = {
  name: 'nb-help',
  port: 8964,
  async setup(take) {
    const { page } = take;
    await page.goto(`http://localhost:${take.port}/notebooks/help.ipynb`);
    await page.waitForFunction(() => window.jupyterapp && window.jupyterapp.shell && window.jupyterapp.shell.currentWidget);
    await page.addStyleTag({ content: '.jp-LabShell.jp-mod-devMode { border-top: 0 !important; }' });
    await page.waitForSelector('.jp-Notebook .jp-Cell');
    await C.waitIdle(page);
    // A fresh kernel, so the prompts count from 1.
    void page.evaluate(() => window.jupyterapp.commands.execute('notebook:restart-kernel'));
    await page.locator('.jp-Dialog .jp-mod-accept').click();
    await page.waitForTimeout(1500);
    await C.waitIdle(page);
    await page.waitForTimeout(800);
    const cells = page.locator('.jp-Notebook .jp-Cell');
    await cells.nth(0).click();
    await page.keyboard.press('Shift+Enter');
    await C.waitIdle(page);
    await page.keyboard.press('Escape');
    await C.park(take, 1000 * take.k, 500 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const cells = page.locator('.jp-Notebook .jp-Cell');
    await H.pause(600);
    await H.click(page, cells.nth(1).locator('.cm-content'));
    await take.focus('cell', cells.nth(1), { zoom: 1.12, pad: 30 });
    take.beat('type');
    await H.type(page, 'statistics.median?', { cps: 13 });
    await H.pause(400);
    take.beat('run');
    await page.keyboard.press('Shift+Enter');
    await page.locator('#jp-down-stack .lm-TabBar-tab, .jp-Inspector').first().waitFor({ timeout: 15000 }).catch(() => null);
    await page.waitForTimeout(500);
    take.beat('shown');
    await take.focus('panel', ['#jp-down-stack', cells.nth(1)], { zoom: 1.12, pad: 10 });
    await H.moveTo(page, 1100 * take.k, 300 * take.k);
    await H.pause(3200);
  }
};
