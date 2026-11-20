'use strict';
// Ctrl+Alt+1..8 switch to the tab at that position, Ctrl+Alt+9 to the last.
const C = require('../../../harness/common');

module.exports = {
  name: 'tabs',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.openFile('stations.ipynb');
    await C.waitIdle(page);
    await lab.openFile('README.md', 'Markdown Preview');
    await lab.openFile('data/measurements.csv');
    await lab.openFile('train.py');
    await lab.openFile('notes/small-angles.md', 'Markdown Preview');
    await page.waitForTimeout(1500);
    await C.park(take, 1100 * take.k, 640 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const bar = page.locator('#jp-main-dock-panel .lm-DockPanel-tabBar').first();
    const box = await bar.boundingBox();
    await take.focus('tabs', { x: box.x, y: box.y, width: Math.min(box.width, 820 * take.k), height: 360 * take.k }, { zoom: 1.7, pad: 6 });
    await H.pause(1100);
    for (const k of ['1', '3', '2', '9']) {
      take.beat('key' + k);
      await page.keyboard.press(`Control+Alt+${k}`);
      await H.pause(1300);
    }
    await H.pause(600);
  }
};
