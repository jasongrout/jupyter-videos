'use strict';
// Sidebar sections can be reordered: Running panel, Terminals above Kernels.
const C = require('../../../harness/common');

module.exports = {
  name: 'reorder',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.openFile('stations.ipynb');
    await C.waitIdle(page);
    await lab.exec('terminal:create-new');
    await page.waitForSelector('.jp-Terminal .xterm');
    await page.waitForTimeout(800);
    await lab.openFile('stations.ipynb');
    await lab.exec('running:show-panel');
    await page.waitForTimeout(800);
    await C.collapseSections(page, 'jp-running-sessions', ['Language servers', 'Recently closed', 'Workspaces']);
    await C.widen(page, 'left', 120 * take.k);
    await C.park(take, 900 * take.k, 560 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const title = name => page.locator('#jp-running-sessions .lm-AccordionPanel-title').filter({ hasText: name }).first();
    await take.focus('panel', '#jp-running-sessions', { zoom: 1.7, pad: 8, maxHeight: 330 * take.k });
    await H.pause(900);
    take.beat('menu');
    await H.click(page, title('Kernels'), { button: 'right', dx: -30 });
    const item = page.locator('.lm-Menu-item').filter({ hasText: 'Enable Section Reordering' }).first();
    await item.waitFor();
    await H.pause(600);
    await H.click(page, item, { dx: -30 });
    await page.waitForTimeout(500);
    take.beat('enabled');
    await H.pause(500);
    const handle = title('Terminals').locator('.jp-AccordionPanel-dragHandle').first();
    await handle.waitFor();
    take.beat('drag');
    await H.drag(page, handle, title('Kernels'), { to: { dy: -6 }, hoverMs: 450, ms: 900 });
    await page.waitForTimeout(500);
    take.beat('dropped');
    await take.focus('after', '#jp-running-sessions', { zoom: 1.7, pad: 10 });
    await H.moveTo(page, 700 * take.k, 520 * take.k);
    await H.pause(2600);
  }
};
