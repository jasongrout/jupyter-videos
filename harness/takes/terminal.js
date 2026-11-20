'use strict';
// The Running panel shows the title that a program sets for its terminal.
const C = require('../common');
const { BASE } = require('../paths');

module.exports = {
  name: 'terminal',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.exec('terminal:create-new');
    await page.waitForSelector('.jp-Terminal .xterm');
    await page.waitForTimeout(1500);
    await lab.exec('running:show-panel');
    await page.waitForTimeout(1000);
    await C.collapseSections(page, 'jp-running-sessions', ['Kernels', 'Language servers', 'Recently closed', 'Workspaces']);
    await C.widen(page, 'left', 60 * take.k);
    await page.locator('.jp-Terminal').first().click();
    await page.keyboard.type(`cd ${BASE}/root; clear`);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(900);
    await C.park(take, 900 * take.k, 560 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    await H.pause(600);
    await H.click(page, page.locator('.jp-Terminal').first(), { position: { x: 400, y: 120 } });
    take.beat('type');
    await H.type(page, 'python train.py', { cps: 12 });
    await H.pause(300);
    take.beat('run');
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.body.textContent.includes('Training: epoch 1/10'), null, { timeout: 15000 });
    await page.waitForTimeout(200);
    take.beat('title');
    await take.focus('running', ['#jp-running-sessions', '#jp-main-dock-panel .lm-DockPanel-tabBar'], { zoom: 1.6, pad: 8 });
    await H.moveTo(page, 600 * take.k, 600 * take.k);
    await page.waitForFunction(() => document.body.textContent.includes('Training: epoch 5/10'), null, { timeout: 20000 });
    take.beat('epoch5');
    await H.pause(1200);
  }
};
