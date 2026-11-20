'use strict';
// In R editors, Alt+- inserts <- and Ctrl+Shift+M inserts %>%.
module.exports = {
  name: 'rkeys',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.openFile('analysis.R');
    await page.waitForSelector('.jp-FileEditor .cm-content');
    await page.waitForTimeout(1200);
    await page.locator('.jp-FileEditor .cm-content').first().click();
    await page.keyboard.press('Control+End');
    await take.H.place(page, 1150 * take.k, 650 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const editor = page.locator('.jp-FileEditor .cm-content').first();
    const eb = await editor.boundingBox();
    await take.focus('editor', { x: eb.x - 40 * take.k, y: eb.y - 4, width: 640 * take.k, height: 150 * take.k }, { zoom: 2.0, pad: 6 });
    await H.pause(900);
    take.beat('type1');
    await H.type(page, 'weather ', { cps: 12 });
    await H.pause(250);
    take.beat('assign');
    await page.keyboard.press('Alt+-');
    await H.pause(700);
    await H.type(page, 'read.csv("data/measurements.csv", comment.char = "#")', { cps: 22 });
    await page.keyboard.press('Enter');
    await H.pause(400);
    await H.type(page, 'weather ', { cps: 12 });
    await H.pause(250);
    take.beat('pipe');
    await page.keyboard.press('Control+Shift+M');
    await H.pause(700);
    await H.type(page, 'count(station)', { cps: 14 });
    await H.pause(2200);
  }
};
