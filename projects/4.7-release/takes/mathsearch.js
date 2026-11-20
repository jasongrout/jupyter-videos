'use strict';
// Search finds text inside rendered formulas, in a Markdown Preview.
module.exports = {
  name: 'mathsearch',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.openFile('notes/small-angles.md', 'Markdown Preview');
    await page.waitForSelector('.jp-RenderedMarkdown mjx-container', { timeout: 20000 });
    await page.waitForTimeout(1500);
    await page.locator('.jp-MarkdownViewer').first().click({ position: { x: 600, y: 360 } });
    await take.H.place(page, 1150 * take.k, 650 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    const doc = page.locator('.jp-MarkdownViewer .jp-RenderedMarkdown').first();
    await take.focus('doc', doc, { zoom: 1.5, pad: 12 });
    await H.pause(1100);
    take.beat('find');
    await page.keyboard.press('Control+f');
    await page.locator('.jp-DocumentSearch-input').first().waitFor();
    await take.focus('search-open', ['.jp-DocumentSearch-overlay', doc], { zoom: 1.5, pad: 10 });
    await H.pause(400);
    await H.type(page, 'sin', { cps: 9 });
    await page.waitForTimeout(900);
    take.beat('typed');
    await take.focus('matches', ['.jp-DocumentSearch-overlay', doc], { zoom: 1.5, pad: 10 });
    await H.pause(1200);
    for (let i = 0; i < 2; i++) {
      take.beat('next' + i);
      await page.keyboard.press('Enter');
      await H.pause(1100);
    }
    await H.pause(1200);
  }
};
