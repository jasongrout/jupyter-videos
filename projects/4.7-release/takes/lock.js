'use strict';
// Read-only cells show a lock in the cell toolbar; a click offers to unlock.
const C = require('../../../harness/common');

module.exports = {
  name: 'lock',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.setSetting('@jupyterlab/notebook-extension:tracker', 'showLockForReadOnlyCells', true);
    await lab.openFile('exercise.ipynb');
    await C.waitIdle(page);
    const cells = await C.cells(page);
    await cells.nth(1).click();
    await lab.exec('notebook:enter-command-mode');
    await C.park(take, 1000 * take.k, 620 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const cells = await C.cells(page);
    await H.pause(700);
    take.beat('select');
    await H.click(page, cells.nth(2), { position: { x: 30, y: 12 } });
    await page.waitForTimeout(300);
    await take.focus('cells', [cells.nth(1), cells.nth(2)], { zoom: 1.6, pad: 20 });
    await H.pause(900);
    const lock = cells.nth(2).locator('.jp-cell-toolbar [data-command="notebook:make-cell-editable"]');
    await lock.waitFor();
    take.beat('lock');
    await take.focus('lock', lock, { zoom: 2.0, pad: 70, spot: true, content: false });
    await H.moveToLocator(page, lock);
    await H.pause(1500);
    await H.click(page, lock, { pauseBefore: 80 });
    await page.locator('.jp-Dialog').waitFor();
    await page.waitForTimeout(250);
    take.beat('dialog');
    await take.focus('dialog', '.jp-Dialog-content', { zoom: 1.7, pad: 20 });
    await H.pause(1700);
    await H.click(page, page.locator('.jp-Dialog .jp-mod-accept'));
    take.beat('unlocked');
    await page.waitForTimeout(300);
    await take.focus('after', [cells.nth(1), cells.nth(2)], { zoom: 1.7, pad: 20 });
    await H.pause(500);
    // The cell takes typing now: the author adds a test.
    await H.click(page, cells.nth(2).locator('.cm-content'), { position: { x: 300, y: 40 } });
    await page.waitForTimeout(200);
    await page.keyboard.press('Control+End');
    await H.pause(200);
    take.beat('type');
    await H.type(page, '\nassert mean([5]) == 5', { cps: 14 });
    await page.waitForTimeout(300);
    await take.focus('typed', [cells.nth(1), cells.nth(2)], { zoom: 1.7, pad: 20 });
    await H.moveTo(page, 1250 * take.k, 640 * take.k);
    await H.pause(1600);
  }
};
