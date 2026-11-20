'use strict';
// Render HTML overlays to PNGs with a transparent background.
// Usage: node render_overlays.js <spec.json>
// The spec is a list of { file, html, width, height } (output pixels); every
// item shares the CSS of style.css next to this script. An item whose file
// exists with the same HTML (kept in <file>.html) is skipped.
const fs = require('fs');
const path = require('path');

const { PLAYWRIGHT_CORE } = require('../harness/paths');
const { CHROMIUM } = require('../harness/recorder/browser');

(async () => {
  const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  // fonts.css holds the deck typefaces as data URLs: a page from setContent cannot load local files.
  const fontsFile = path.join(__dirname, 'fonts.css');
  const css = (fs.existsSync(fontsFile) ? fs.readFileSync(fontsFile, 'utf8') : '') + fs.readFileSync(path.join(__dirname, 'style.css'), 'utf8');
  // An overlay is drawn again when its HTML or the shared CSS changed.
  const stamp = item => item.html + '\n<!-- css ' + require('crypto').createHash('sha256').update(css).digest('hex') + ' -->';
  const todo = spec.filter(item => {
    const key = item.file + '.html';
    return !(fs.existsSync(item.file) && fs.existsSync(key) && fs.readFileSync(key, 'utf8') === stamp(item));
  });
  if (!todo.length) {
    console.log('overlays: all', spec.length, 'up to date');
    return;
  }
  const { chromium } = require(PLAYWRIGHT_CORE);
  const browser = await chromium.launch({ executablePath: CHROMIUM, headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  for (const item of todo) {
    await page.setViewportSize({ width: item.width, height: item.height });
    await page.setContent(
      `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head>` +
        `<body><div id="root" style="width:${item.width}px;height:${item.height}px">${item.html}</div></body></html>`
    );
    await page.evaluate(() => document.fonts.ready);
    fs.mkdirSync(path.dirname(item.file), { recursive: true });
    await page.locator('#root').screenshot({ path: item.file, omitBackground: true });
    fs.writeFileSync(item.file + '.html', stamp(item));
  }
  await browser.close();
  console.log('overlays: rendered', todo.length, 'of', spec.length);
})();
