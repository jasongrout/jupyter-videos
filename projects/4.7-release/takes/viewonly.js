'use strict';
// A notebook from a file that is not writable opens in view-only mode.
const C = require('../../../harness/common');

module.exports = {
  name: 'viewonly',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await page.evaluate(() => window.jupyterapp.serviceManager.contents.delete('report-copy.ipynb').catch(() => null));
    await lab.exec('filebrowser:activate');
    await page.waitForTimeout(500);
    await C.park(take, 700 * take.k, 520 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    await H.pause(700);
    const item = page.locator('.jp-DirListing-item').filter({ hasText: 'report.ipynb' }).first();
    take.beat('open');
    await H.dblclick(page, item);
    await page.waitForSelector('.jp-NotebookPanel:not(.lm-mod-hidden) .jp-Cell');
    await page.waitForTimeout(1200);
    take.beat('opened');
    const toolbar = await C.current(page, '.jp-NotebookPanel-toolbar');
    await take.focus('toolbar', toolbar, { zoom: 1.9, pad: 8 });
    await H.moveTo(page, 1100 * take.k, 330 * take.k);
    await H.pause(2300);
    take.beat('saveas');
    await take.unfocus();
    await C.menu(take, 'File', 'Save Notebook As…');
    await page.locator('.jp-Dialog').waitFor();
    await page.waitForTimeout(300);
    await take.focus('dialog', '.jp-Dialog-content', { zoom: 1.7, pad: 20 });
    await H.pause(900);
    // The dialog proposes the read-only file's own name with Save focused: rename first.
    await H.click(page, page.locator('.jp-Dialog input').first());
    await page.keyboard.press('Control+A');
    await H.type(page, 'report-copy.ipynb', { cps: 16 });
    await H.pause(500);
    take.beat('save');
    await H.click(page, page.locator('.jp-Dialog .jp-mod-accept'));
    await page.locator('.lm-TabBar-tab.lm-mod-current').filter({ hasText: 'report-copy.ipynb' }).first().waitFor({ timeout: 15000 });
    await page.waitForFunction(() => {
      const w = window.jupyterapp.shell.currentWidget;
      const k = w && w.sessionContext && w.sessionContext.session && w.sessionContext.session.kernel;
      return k && k.status === 'idle';
    }, null, { timeout: 30000 });
    await page.waitForTimeout(400);
    take.beat('copy');
    const toolbar2 = await C.current(page, '.jp-NotebookPanel-toolbar');
    await take.focus('copy', toolbar2, { zoom: 1.9, pad: 8 });
    await H.moveTo(page, 1100 * take.k, 420 * take.k);
    await H.pause(2000);
  }
};
