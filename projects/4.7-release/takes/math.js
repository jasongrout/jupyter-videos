'use strict';
// MathJax 4.1: \\ breaks lines in display math, long inline formulas wrap.
const C = require('../../../harness/common');

module.exports = {
  name: 'math',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.openFile('pipeline.ipynb');
    const noKernel = page.locator('.jp-Dialog button').filter({ hasText: 'No Kernel' });
    await noKernel.first().waitFor({ timeout: 8000 }).catch(() => null);
    if (await noKernel.count()) await noKernel.first().click();
    await page.waitForSelector('.jp-NotebookPanel .jp-RenderedMarkdown mjx-container', { timeout: 20000 });
    await page.waitForTimeout(1500);
    const cells = await C.cells(page);
    // Show the source of the dew point cell, scrolled to the top of the notebook.
    await cells.nth(1).dblclick({ position: { x: 200, y: 20 } });
    await page.waitForTimeout(500);
    await lab.exec('notebook:enter-command-mode');
    await cells.nth(1).evaluate(el => el.scrollIntoView({ block: 'start' }));
    await page.waitForTimeout(500);
    await C.park(take, 1150 * take.k, 650 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const cells = await C.cells(page);
    await take.focus('source', cells.nth(1), { zoom: 1.55, pad: 18 });
    await H.pause(2200);
    take.beat('render');
    await page.keyboard.press('Shift+Enter');
    await page.waitForTimeout(700);
    take.beat('rendered');
    await take.focus('rendered', cells.nth(1), { zoom: 1.55, pad: 18 });
    await H.pause(3200);
  }
};
