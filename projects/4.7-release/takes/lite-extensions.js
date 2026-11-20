'use strict';
// JupyterLite 0.9: the Extension Manager lists the extensions that the site ships and turns one off.
// The tour extension shows two notifications at the start; after it is disabled and the page reloads, they are gone.
const L = require('./lite-common');

module.exports = {
  name: 'lite-extensions',
  port: 0,
  async setup(take) {
    await L.open(take.page);
    await take.H.place(take.page, 760 * take.k, 470 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    await take.focus('toasts', '.Toastify', { zoom: 1.12, pad: 20 });
    await H.pause(1400);
    take.beat('open');
    await H.click(page, page.locator('.jp-SideBar.jp-mod-left .lm-TabBar-tab[title*="Extension"]').first());
    await page.waitForTimeout(700);
    take.beat('list');
    await take.focus('panel', '.jp-SidePanel.jp-extensionmanager-view, #extensionmanager\\.main-view', { zoom: 1.12, pad: 8, content: false });
    await H.pause(900);
    const entry = page.locator('.jp-extensionmanager-entry').filter({ hasText: 'jupyterlab-tour' }).first();
    const list = await page.locator('.jp-extensionmanager-entry').first().boundingBox();
    await H.moveTo(page, list.x + list.width / 2, list.y + 160 * take.k);
    for (let i = 0; i < 8 && !(await entry.isVisible() && (await entry.boundingBox()).y + 60 < 600 * take.k); i++) {
      await H.wheel(page, 300, { ms: 500 });
    }
    await H.pause(500);
    take.beat('disable');
    await H.click(page, entry.locator('button').filter({ hasText: 'Disable' }).first());
    await page.locator('.jp-Dialog').waitFor();
    await page.waitForTimeout(250);
    take.beat('dialog');
    await take.focus('dialog', '.jp-Dialog-content', { zoom: 1.3, pad: 20 });
    await H.pause(1500);
    await H.click(page, page.locator('.jp-Dialog button').filter({ hasText: 'Reload' }).first());
    take.beat('reload');
    take.unfocus();
    await L.ready(page);
    take.beat('reloaded');
    await H.moveTo(page, 760 * take.k, 470 * take.k);
    await page.waitForTimeout(3500);
    const toasts = await page.locator('.Toastify__toast').count();
    console.log('toasts after reload:', toasts);
    take.beat('end');
  }
};
