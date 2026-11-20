'use strict';
// Computed styles of the CSV Comment select with and without appearance: base-select.
const { startTake } = require('../rv');
const PICKER_CSS = require('../picker-css');
(async () => {
  const port = Number(process.argv[2]);
  const take = await startTake({ name: 'probe-select2', port, width: 1152, height: 648, dsf: 1 });
  const { page, lab } = take;
  const props = ['width', 'height', 'padding', 'border', 'borderRadius', 'backgroundColor', 'color', 'fontSize', 'lineHeight', 'fieldSizing', 'boxShadow', 'outline', 'appearance', 'display', 'gap', 'alignItems', 'minWidth', 'boxSizing'];
  const read = () => page.evaluate(props => {
    const s = getComputedStyle(document.querySelector('.jp-CSVComment select'));
    const w = getComputedStyle(document.querySelector('.jp-CSVComment .jp-HTMLSelect') || document.querySelector('.jp-CSVComment select').parentElement);
    const r = document.querySelector('.jp-CSVComment select').getBoundingClientRect();
    return { select: Object.fromEntries(props.map(p => [p, s[p]])), wrapper: { border: w.border, boxShadow: w.boxShadow, cls: document.querySelector('.jp-CSVComment select').parentElement.className }, rect: [r.x, r.y, r.width, r.height] };
  }, props);
  try {
    await lab.open();
    await lab.openFile('data/measurements.csv');
    await page.waitForSelector('.jp-CSVViewer');
    await page.waitForTimeout(800);
    console.log('native', JSON.stringify(await read()));
    await page.addStyleTag({ content: PICKER_CSS });
    await page.waitForTimeout(300);
    console.log('base', JSON.stringify(await read()));
  } finally {
    await take.browser.close();
  }
})();
