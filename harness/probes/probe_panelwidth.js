'use strict';
// Does the left panel keep a dragged width after it is collapsed and opened from another sidebar tab?
const { startTake } = require('../rv');
(async () => {
  const take = await startTake({ name: 'probe-panelwidth', port: 8962, width: 1152, height: 648, dsf: 1 });
  const { page, lab } = take;
  try {
    await lab.open();
    await lab.openFile('weather.ipynb');
    await page.waitForTimeout(1000);
    const width = () => page.evaluate(() => document.querySelector('#jp-left-stack').getBoundingClientRect().width);
    console.log('start', await width());
    const handle = page.locator('#jp-main-split-panel > .lm-SplitPanel-handle').first();
    const box = await handle.boundingBox();
    console.log('handle', JSON.stringify(box));
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(33 + 440, box.y + box.height / 2, { steps: 8 });
    await page.mouse.up();
    await page.waitForTimeout(300);
    console.log('dragged', await width());
    await page.locator('.jp-SideBar .lm-TabBar-tab[title^="File Browser"]').click();
    await page.waitForTimeout(400);
    console.log('collapsed', await width(), await page.evaluate(() => document.querySelector('#jp-left-stack').classList.contains('lm-mod-hidden')));
    await page.locator('.jp-SideBar .lm-TabBar-tab[title="Jupyter Chat"]').click();
    await page.waitForTimeout(600);
    console.log('chat opened', await width());
    await page.screenshot({ path: `${take.dir}/chat.png` });
  } finally {
    await take.browser.close();
  }
})();
