'use strict';
// Command palette: recently used commands at the top.
const palInput = '.jp-ModalCommandPalette input.lm-CommandPalette-input';

async function openPalette(page) {
  const input = page.locator(palInput);
  for (let i = 0; i < 5; i++) {
    await page.waitForTimeout(500);
    await page.keyboard.press('Control+Shift+C');
    await page.waitForTimeout(400);
    if (await input.isVisible()) return input;
  }
  throw new Error('palette did not open');
}

async function paletteRun(page, query, label) {
  const input = await openPalette(page);
  await input.fill(query);
  await page.waitForTimeout(300);
  const want = label || query;
  for (let i = 0; i < 12; i++) {
    const active = await page.locator('.jp-ModalCommandPalette .lm-CommandPalette-item.lm-mod-active .lm-CommandPalette-itemLabel').textContent();
    if (active === want) break;
    await page.keyboard.press('ArrowDown');
  }
  await page.keyboard.press('Enter');
  await page.waitForTimeout(700);
}

module.exports = {
  name: 'palette',
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.openFile('stations.ipynb');
    await lab.waitKernelIdle();
    await lab.sidebars({ left: false });
    await page.locator('.jp-NotebookPanel .jp-Cell').nth(1).click();
    await paletteRun(page, 'Restart Kernel and Run All Cells', 'Restart Kernel and Run All Cells…');
    await page.locator('.jp-Dialog .jp-mod-accept').click();
    await lab.waitKernelIdle();
    await page.waitForTimeout(1500);
    await page.locator('.jp-NotebookPanel .jp-Cell').nth(1).click();
    await paletteRun(page, 'Run All Cells');
    await lab.waitKernelIdle();
    await page.waitForTimeout(800);
    await page.locator('.jp-NotebookPanel .jp-Cell').nth(1).click();
    await paletteRun(page, 'Clear Outputs of All Cells');
    await lab.exec('notebook:enter-command-mode');
    await page.locator('.jp-NotebookPanel .jp-Cell').first().click({ position: { x: 3, y: 3 } });
    await page.evaluate(() => document.querySelector('.jp-NotebookPanel .jp-WindowedPanel-outer').scrollTo(0, 0));
    await take.H.place(page, 1100 * take.k, 640 * take.k);
    await page.waitForTimeout(600);
  },
  async run(take) {
    const { page, H } = take;
    await H.pause(900);
    take.beat('open');
    const input = await openPalette(page);
    await page.waitForTimeout(250);
    // The palette's own box: the box of its text would leave its right edge in the shade.
    await take.focus('palette', '.jp-ModalCommandPalette .lm-CommandPalette', { zoom: 1.7, pad: 3, spot: true, content: false });
    await H.pause(1600);
    // Walk down to "Restart Kernel and Run All Cells…" in the recent list.
    for (let i = 0; i < 6; i++) {
      const active = await page.locator('.jp-ModalCommandPalette .lm-CommandPalette-item.lm-mod-active .lm-CommandPalette-itemLabel').textContent();
      if (active === 'Restart Kernel and Run All Cells…') break;
      await page.keyboard.press('ArrowDown');
      await H.pause(380);
    }
    await H.pause(500);
    take.beat('pick');
    await page.keyboard.press('Enter');
    await page.waitForSelector('.jp-Dialog');
    await take.focus('dialog', '.jp-Dialog-content', { zoom: 1.5, pad: 24 });
    await H.pause(700);
    await H.click(page, page.locator('.jp-Dialog .jp-mod-accept'));
    take.unfocus();
    take.beat('run');
    // The shot ends as the cells run again; the plot is below the fold at this size.
    await page.waitForSelector('.jp-NotebookPanel .jp-OutputArea-output', { timeout: 30000 });
    await page.waitForTimeout(400);
    take.beat('done');
    await H.moveTo(page, 900 * take.k, 600 * take.k);
    await H.pause(2600);
  }
};
