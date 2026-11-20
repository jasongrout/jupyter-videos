'use strict';
// Keyboard access: the Settings Editor's plugin list and the Keyboard Shortcuts editor.

/** Spotlight the element that has the keyboard focus. */
async function focusActive(take, name) {
  const box = await take.page.evaluate(() => {
    const r = document.activeElement && document.activeElement.getBoundingClientRect();
    return r && r.width ? { x: r.x, y: r.y, width: r.width, height: r.height } : null;
  });
  if (box) await take.focus(name, box, { zoom: 1.35, pad: 8, spot: true, content: false });
}

module.exports = {
  name: 'a11y',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.exec('settingeditor:open');
    await page.waitForSelector('.jp-PluginList');
    await page.waitForTimeout(1500);
    const search = page.locator('.jp-SettingsEditor input[type="text"], .jp-PluginList input').first();
    await search.click();
    await page.waitForTimeout(300);
    // Over the empty right sidebar: rows of the shortcuts table highlight under the pointer.
    await take.H.place(page, 1420 * take.k, 563 * take.k);
  },
  async run(take) {
    const { page, H } = take;
    await take.focus('editor', ['.jp-PluginList', '.jp-SettingsPanel'], { zoom: 1.15, pad: 0, content: false });
    await H.pause(800);
    take.beat('type');
    await H.type(page, 'keyboard', { cps: 11 });
    await page.waitForTimeout(600);
    take.beat('tab');
    await page.keyboard.press('Tab');
    await page.waitForTimeout(150);
    await focusActive(take, 'list');
    await H.pause(700);
    for (let i = 0; i < 3; i++) {
      const label = await page.evaluate(() => document.activeElement && document.activeElement.textContent.trim().slice(0, 40));
      if (/Keyboard Shortcuts/.test(label || '')) break;
      await page.keyboard.press('ArrowDown');
      await H.pause(550);
    }
    take.beat('open');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1200);
    take.beat('shortcuts');
    await take.focus('table', '.jp-SettingsPanel', { zoom: 1.2, pad: 0, content: false });
    // Tab through the first rows of the shortcuts table and the buttons in them.
    for (let i = 0; i < 9; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(120);
      await focusActive(take, 'tab' + i);
      await H.pause(i < 3 ? 650 : 520);
    }
    take.beat('end');
    await H.pause(1500);
    const where = await page.evaluate(() => {
      const a = document.activeElement;
      return a ? `${a.tagName}.${a.className} "${(a.getAttribute('aria-label') || a.textContent || '').trim().slice(0, 40)}"` : null;
    });
    console.log('focus at the end:', where);
  }
};
