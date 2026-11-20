'use strict';
// Mermaid diagrams are drawn again when the theme changes.
const C = require('../common');

module.exports = {
  name: 'mermaid',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.openFile('pipeline.ipynb');
    const noKernel = page.locator('.jp-Dialog button').filter({ hasText: 'No Kernel' });
    await noKernel.first().waitFor({ timeout: 8000 }).catch(() => null);
    if (await noKernel.count()) await noKernel.first().click();
    await page.waitForSelector('.jp-NotebookPanel .jp-RenderedMermaid', { timeout: 30000 });
    await page.waitForTimeout(1500);
    const cells = await C.cells(page);
    const box0 = await cells.nth(0).boundingBox();
    await cells.nth(0).click({ position: { x: box0.width - 160, y: 40 } });
    await lab.exec('notebook:enter-command-mode');
    await C.park(take, 1150 * take.k, 560 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const cells = await C.cells(page);
    await take.focus('diagram', cells.nth(0), { zoom: 1.5, pad: 16 });
    await H.pause(1500);
    take.beat('menu');
    const bar = page.locator('.lm-MenuBar-item').filter({ hasText: /^Settings$/ }).first();
    await H.click(page, bar);
    await page.waitForTimeout(300);
    const bb = await bar.boundingBox();
    await H.moveTo(page, bb.x + bb.width / 2, bb.y + bb.height + 14, { arc: 0, ms: 220 });
    const themeItem = page.locator('.lm-Menu-content > .lm-Menu-item').filter({ hasText: /^Theme/ }).first();
    await H.moveToLocator(page, themeItem, { dx: -20, arc: 0 });
    await page.waitForTimeout(500);
    const dark = page.locator('.lm-Menu-item').filter({ hasText: /^JupyterLab Dark$/ }).first();
    await dark.waitFor();
    const tb = await themeItem.boundingBox();
    await H.moveTo(page, (await dark.boundingBox()).x + 30, tb.y + tb.height / 2, { ms: 300, arc: 0 });
    take.beat('pick');
    await H.click(page, dark, { dx: -10, arc: 0 });
    await page.waitForFunction(() => document.body.dataset.jpThemeLight === 'false', null, { timeout: 15000 });
    take.beat('dark');
    await page.waitForTimeout(1500);
    await take.focus('diagram-dark', cells.nth(0), { zoom: 1.5, pad: 16 });
    await H.moveTo(page, 1200 * take.k, 620 * take.k);
    await H.pause(2500);
  }
};
