'use strict';
// What the status bar says for a notebook with No Kernel, and for a view-only one.
const { startTake } = require('../rv');
(async () => {
  const port = Number(process.argv[2]);
  const take = await startTake({ name: 'probe-status-' + port, port, width: 1200, height: 700, dsf: 1 });
  const { page, lab } = take;
  try {
    await lab.open();
    for (const file of ['pipeline.ipynb', 'report.ipynb']) {
      await lab.openFile(file);
      const noKernel = page.locator('.jp-Dialog button').filter({ hasText: 'No Kernel' });
      await noKernel.first().waitFor({ timeout: 6000 }).catch(() => null);
      if (await noKernel.count()) await noKernel.first().click();
      await page.waitForTimeout(6000);
      const status = await page.locator('.jp-StatusBar-Widget').allTextContents();
      console.log(port, file, JSON.stringify(status.filter(t => /Kernel|Idle|Initializing|Unknown/.test(t))));
      await page.screenshot({ path: `${take.dir}/${file}.png` });
    }
  } finally {
    await take.browser.close();
  }
})();
