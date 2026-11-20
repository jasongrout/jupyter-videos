'use strict';
// object? opens its help in a panel below the notebook.
const C = require('../common');

module.exports = {
  name: 'help',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.setSetting('@jupyterlab/notebook-extension:tracker', 'helpInBottomPanel', true);
    await lab.openFile('help.ipynb');
    await C.waitIdle(page);
    const cells = await C.cells(page);
    await cells.nth(0).click();
    await lab.exec('notebook:run-cell-and-select-next');
    await C.waitIdle(page);
    await lab.exec('notebook:enter-command-mode');
    await C.park(take, 1000 * take.k, 500 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const cells = await C.cells(page);
    await H.pause(600);
    await H.click(page, cells.nth(1).locator('.cm-content'));
    await take.focus('cell', cells.nth(1), { zoom: 1.6, pad: 30 });
    await H.pause(300);
    take.beat('type');
    await H.type(page, 'statistics.median?', { cps: 13 });
    await H.pause(400);
    take.beat('run');
    await page.keyboard.press('Shift+Enter');
    await page.locator('#jp-down-stack .lm-TabBar-tab').filter({ hasText: 'Help' }).first().waitFor({ timeout: 15000 });
    await page.waitForTimeout(400);
    take.beat('shown');
    // Give the Help panel more room, as a reader would, by dragging the handle above it.
    const handle = page.locator('#jp-main-vsplit-panel > .lm-SplitPanel-handle').first();
    const hb = await handle.boundingBox();
    if (hb) {
      await H.moveTo(page, 700 * take.k, hb.y + hb.height / 2, { ms: 500 });
      await page.mouse.down();
      await H.moveTo(page, 700 * take.k, 330 * take.k, { ms: 600, arc: 0 });
      await page.mouse.up();
      await page.waitForTimeout(300);
    }
    take.beat('resized');
    await take.focus('panel', '#jp-down-stack', { zoom: 1.6, pad: 14 });
    await H.moveTo(page, 1250 * take.k, 260 * take.k);
    await H.pause(3000);
  }
};
