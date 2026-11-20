'use strict';
// Helpers shared by the takes of the release video.

const PAL_INPUT = '.jp-ModalCommandPalette input.lm-CommandPalette-input';

async function openPalette(page) {
  const input = page.locator(PAL_INPUT);
  for (let i = 0; i < 5; i++) {
    await page.waitForTimeout(400);
    await page.keyboard.press('Control+Shift+C');
    await page.waitForTimeout(400);
    if (await input.isVisible()) return input;
  }
  throw new Error('palette did not open');
}

/** Run a command through the palette, during setup (fill, not typing). */
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

/** A locator inside the current main area widget. */
async function current(page, selector = '') {
  const id = await page.evaluate(() => window.jupyterapp.shell.currentWidget.id);
  return page.locator(`[id="${id}"] ${selector}`.trim());
}

async function cells(page) {
  return current(page, '.jp-Cell');
}

/** Collapse the named sections of an accordion side panel (by its id). */
async function collapseSections(page, panelId, names) {
  for (const name of names) {
    const t = page.locator(`#${panelId} .lm-AccordionPanel-title`).filter({ hasText: name }).first();
    if ((await t.count()) && (await t.getAttribute('aria-expanded')) === 'true') {
      await t.click({ position: { x: 40, y: 10 } });
      await page.waitForTimeout(250);
    }
  }
}

async function splitHandle(page, side) {
  const handles = page.locator('#jp-main-split-panel > .lm-SplitPanel-handle');
  const n = await handles.count();
  let best = null;
  for (let i = 0; i < n; i++) {
    const b = await handles.nth(i).boundingBox();
    if (b && b.width > 0 && (!best || (side === 'left' ? b.x < best.x : b.x > best.x))) best = b;
  }
  return best;
}

/** Drag the side panel's split handle by `by` px (positive widens it), during setup. */
async function widen(page, side, by) {
  const b = await splitHandle(page, side);
  if (!b) return;
  const x = b.x + b.width / 2;
  await page.mouse.move(x, b.y + 200);
  await page.mouse.down();
  await page.mouse.move(side === 'left' ? x + by : x - by, b.y + 200, { steps: 8 });
  await page.mouse.up();
  await page.waitForTimeout(400);
}

/** Click a menu bar entry and then an item of its menu (a label, or { command }), as a person does. */
async function menu(take, top, item) {
  const { page, H } = take;
  const bar = page.locator('.lm-MenuBar-item').filter({ hasText: new RegExp(`^${top}$`) }).first();
  await H.click(page, bar);
  await page.waitForTimeout(250);
  const entry =
    typeof item === 'string'
      ? page.locator('.lm-Menu-content > .lm-Menu-item').filter({ hasText: item }).first()
      : page.locator(`.lm-Menu-content > .lm-Menu-item[data-command="${item.command}"]`).first();
  // Straight down first: a pointer that crosses another menu bar title opens that menu.
  const b = await bar.boundingBox();
  await H.moveTo(page, b.x + b.width / 2, b.y + b.height + 14, { arc: 0, ms: 220 });
  await H.click(page, entry, { dx: -20, arc: 0 });
}

async function waitIdle(page, timeout = 60000) {
  await page.waitForFunction(
    () => {
      const w = window.jupyterapp.shell.currentWidget;
      const s = w && w.sessionContext;
      return s && s.session && s.session.kernel && s.session.kernel.status === 'idle';
    },
    null,
    { timeout }
  );
}

/** Put the pointer somewhere neutral before recording. */
async function park(take, x = 1180, y = 600) {
  await take.H.place(take.page, x, y);
  await take.page.waitForTimeout(200);
}

module.exports = { openPalette, paletteRun, current, cells, collapseSections, widen, menu, waitIdle, park, PAL_INPUT };
