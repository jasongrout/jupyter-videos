'use strict';
// The CSV viewer recognizes comment lines and counts search matches.
module.exports = {
  name: 'csv',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.openFile('data/measurements.csv');
    await page.waitForSelector('.jp-CSVViewer');
    // The screencast does not capture the native popup of a <select>, so the menu is drawn in the page.
    await page.addStyleTag({ content: require('../../../harness/picker-css') });
    await page.waitForTimeout(1200);
    await take.H.place(page, 1150 * take.k, 650 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const viewer = page.locator('.jp-CSVViewer').first();
    const vb = await viewer.boundingBox();
    await take.focus('grid', { x: vb.x, y: vb.y - 34, width: 760 * take.k, height: 330 * take.k }, { zoom: 1.6, pad: 6 });
    await H.pause(1800);
    const select = page.locator('.jp-CSVComment select').first();
    const sb = await select.boundingBox();
    await take.focus('menu', { x: vb.x, y: sb.y - 6, width: 520 * take.k, height: 150 * take.k }, { zoom: 2.2, pad: 6 });
    await H.pause(700);
    take.beat('comment');
    await H.click(page, select);
    const option = page.locator('.jp-CSVComment select option[value="#"]');
    await page.waitForFunction(() => document.querySelector('.jp-CSVComment select').matches(':open'));
    await H.pause(500);
    await H.click(page, option);
    await page.waitForFunction(() => document.querySelector('.jp-CSVComment select').value === '#');
    await page.waitForTimeout(600);
    take.beat('comments');
    await take.focus('grid2', { x: vb.x, y: sb.y - 6, width: 760 * take.k, height: 300 * take.k }, { zoom: 1.8, pad: 6 });
    await H.pause(2200);
    take.beat('find');
    await H.click(page, viewer, { position: { x: 500, y: 300 } });
    await page.keyboard.press('Control+f');
    await page.locator('.jp-DocumentSearch-input').first().waitFor();
    await take.focus('search-open', ['.jp-DocumentSearch-overlay', { x: vb.x, y: vb.y, width: 760 * take.k, height: 300 * take.k }], { zoom: 1.5, pad: 6 });
    await H.pause(300);
    await H.type(page, 'Oslo', { cps: 9 });
    await page.waitForTimeout(1500);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(400);
    take.beat('found');
    await take.focus('search', ['.jp-DocumentSearch-overlay', { x: vb.x, y: vb.y, width: 760 * take.k, height: 300 * take.k }], { zoom: 1.5, pad: 6 });
    await H.pause(1000);
    await page.keyboard.press('Enter');
    await H.pause(2000);
  }
};
