'use strict';
// The debugger's Kernel Sources panel lists modules as a tree, by package.
const C = require('../common');

module.exports = {
  name: 'sources',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.setSetting('@jupyterlab/debugger-extension:main', 'hideNativeSources', true);
    await lab.openFile('debugging.ipynb');
    await C.waitIdle(page);
    const cells = await C.cells(page);
    await cells.nth(0).click();
    await lab.exec('notebook:run-all-cells');
    await C.waitIdle(page);
    await page.waitForTimeout(800);
    await lab.exec('notebook:enter-command-mode');
    await page.evaluate(() => window.jupyterapp.shell.activateById('jp-debugger-sidebar'));
    await page.waitForTimeout(800);
    await C.widen(page, 'right', 130 * take.k);
    await page.evaluate(() => window.jupyterapp.shell.collapseRight());
    await page.waitForTimeout(400);
    await C.park(take, 900 * take.k, 560 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    await H.pause(600);
    const bug = (await C.current(page, '.jp-NotebookPanel-toolbar .jp-DebuggerBugButton')).first();
    await take.focus('bug', bug, { zoom: 1.4, pad: 160 });
    take.beat('enable');
    await H.click(page, bug);
    await page.waitForTimeout(1200);
    await take.lab.exec('debugger:show-panel').catch(() => null);
    await page.evaluate(() => window.jupyterapp.shell.activateById('jp-debugger-sidebar'));
    await page.waitForTimeout(1200);
    await C.collapseSections(page, 'jp-debugger-sidebar', ['Variables', 'Callstack', 'Breakpoints']);
    await page.waitForTimeout(600);
    take.beat('panel');
    await take.focus('sources', '#jp-debugger-sidebar', { zoom: 1.7, pad: 6 });
    await H.pause(1200);
    const pandas = page.locator('.jp-DebuggerKernelSource-dir > .jp-DebuggerKernelSource-item').filter({ hasText: /^pandas$/ }).first();
    if (await pandas.count()) {
      take.beat('expand');
      await H.click(page, pandas);
      await page.waitForTimeout(400);
      await take.focus('tree', '#jp-debugger-sidebar', { zoom: 1.7, pad: 6, maxHeight: 430 * take.k });
    } else {
      console.log('no pandas entry');
    }
    await H.pause(3600);
  }
};
