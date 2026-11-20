'use strict';
// Undo the deletion of a running cell: it comes back as it was, and a
// notification offers the outputs that arrived since.
const C = require('../common');

async function outputLines(page) {
  return page.evaluate(() => {
    const id = window.jupyterapp.shell.currentWidget.id;
    const cell = document.querySelectorAll(`[id="${id}"] .jp-Cell`)[1];
    const out = cell && cell.querySelector('.jp-OutputArea');
    return out ? out.textContent.split('Downloaded').length - 1 : 0;
  });
}

module.exports = {
  name: 'undo',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.openFile('download.ipynb');
    await C.waitIdle(page);
    const cells = await C.cells(page);
    await cells.nth(1).click();
    await lab.exec('notebook:enter-command-mode');
    await C.park(take, 980 * take.k, 560 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const cells = await C.cells(page);
    await H.pause(700);
    take.beat('run');
    await page.keyboard.press('Control+Enter');
    await take.focus('cell', cells.nth(1), { zoom: 1.5, pad: 24 });
    await page.waitForFunction(() => document.querySelector('.jp-NotebookPanel:not(.lm-mod-hidden) .jp-OutputArea-output'));
    for (let i = 0; i < 40 && (await outputLines(page)) < 2; i++) await page.waitForTimeout(100);
    await H.pause(200);
    take.beat('delete');
    await H.click(page, cells.nth(1).locator('.jp-cell-toolbar [data-command="cell-toolbar:delete"]'));
    const accept = page.locator('.jp-Dialog .jp-mod-accept');
    await accept.waitFor({ timeout: 3000 }).catch(() => null);
    if (await accept.isVisible()) {
      await take.focus('dialog', '.jp-Dialog-content', { zoom: 1.5, pad: 20 });
      await H.pause(900);
      await H.click(page, accept);
    }
    take.beat('deleted');
    await take.focus('gone', '.jp-NotebookPanel:not(.lm-mod-hidden) .jp-Notebook', { zoom: 1.3, pad: 0 });
    await C.waitIdle(page);
    await H.pause(700);
    take.beat('undo');
    await C.menu(take, 'Edit', { command: 'notebook:undo-cell-action' });
    const btn = page.locator('.Toastify__toast button').filter({ hasText: 'Show new outputs' }).first();
    await btn.waitFor({ timeout: 10000 });
    await page.waitForTimeout(300);
    take.beat('restored');
    await take.focus('toast', '.Toastify__toast', { zoom: 1.6, pad: 18 });
    await H.pause(1700);
    await H.click(page, btn);
    take.beat('shown');
    await page.waitForTimeout(300);
    await take.focus('cell2', cells.nth(1), { zoom: 1.5, pad: 24 });
    await H.moveTo(page, 1250 * take.k, 620 * take.k);
    await H.pause(2400);
  }
};
