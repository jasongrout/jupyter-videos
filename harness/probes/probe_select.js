'use strict';
// Does the CSV Comment menu render inside the page with appearance: base-select, and how does it look?
const { startTake } = require('../rv');
const PICKER_CSS = require('../picker-css');
(async () => {
  const port = Number(process.argv[2]);
  const take = await startTake({ name: 'probe-select', port, width: 1152, height: 648, dsf: 1 });
  const { page, lab } = take;
  try {
    await lab.open();
    await lab.openFile('data/measurements.csv');
    await page.waitForSelector('.jp-CSVViewer');
    await page.addStyleTag({ content: PICKER_CSS });
    await page.waitForTimeout(800);
    const select = page.locator('.jp-CSVComment select').first();
    await page.screenshot({ path: `${take.dir}/closed.png`, clip: { x: 0, y: 60, width: 700, height: 200 } });
    await select.click();
    await page.waitForTimeout(500);
    console.log('open:', await page.evaluate(() => document.querySelector('.jp-CSVComment select').matches(':open')));
    const opt = page.locator('.jp-CSVComment select option[value="#"]');
    console.log('option box:', JSON.stringify(await opt.boundingBox()));
    await page.screenshot({ path: `${take.dir}/open.png`, clip: { x: 0, y: 60, width: 700, height: 200 } });
    await opt.click();
    await page.waitForTimeout(600);
    console.log('value:', await page.evaluate(() => document.querySelector('.jp-CSVComment select').value));
    await page.screenshot({ path: `${take.dir}/picked.png`, clip: { x: 0, y: 60, width: 700, height: 260 } });
  } finally {
    await take.browser.close();
  }
})();
