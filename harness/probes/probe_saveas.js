'use strict';
// Where the focus is in the Save As dialog of a view-only notebook, and what Enter does.
const { startTake } = require('../rv');
const C = require('../common');
(async () => {
  const port = Number(process.argv[2]);
  const take = await startTake({ name: 'probe-saveas-' + port, port, width: 1200, height: 700, dsf: 1 });
  const { page, lab } = take;
  try {
    await lab.open();
    await page.evaluate(() => window.jupyterapp.serviceManager.contents.delete('report-copy.ipynb').catch(() => null));
    await lab.openFile('report.ipynb');
    await page.waitForSelector('.jp-NotebookPanel .jp-Cell');
    await page.waitForTimeout(1500);
    await lab.exec('docmanager:save-as');
    await page.locator('.jp-Dialog').waitFor();
    await page.waitForTimeout(500);
    const info = await page.evaluate(() => {
      const a = document.activeElement;
      const input = document.querySelector('.jp-Dialog input');
      return {
        active: a ? `${a.tagName}.${a.className}` : null,
        activeText: a ? (a.textContent || a.value || '').slice(0, 40) : null,
        inputValue: input && input.value,
        selection: input ? [input.selectionStart, input.selectionEnd] : null
      };
    });
    console.log(port, JSON.stringify(info));
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2000);
    const after = await page.evaluate(() => Array.from(document.querySelectorAll('.jp-Dialog .jp-Dialog-header, .jp-Dialog-body')).map(e => e.textContent.trim()).join(' | '));
    console.log(port, 'after Enter:', JSON.stringify(after), 'tab:', await page.evaluate(() => window.jupyterapp.shell.currentWidget.title.label));
    await page.screenshot({ path: `${take.dir}/after-enter.png` });
  } finally {
    await take.browser.close();
  }
})();
