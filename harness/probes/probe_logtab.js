'use strict';
// The Log Console tab in the down area of Notebook: is its icon centred on the label?
const { startTake } = require('../rv');
(async () => {
  const [port, name] = [Number(process.argv[2]), process.argv[3]];
  const take = await startTake({ name: `probe-logtab-${name}`, port, width: 900, height: 500, dsf: 2 });
  const { page } = take;
  try {
    await page.goto(`http://localhost:${port}/notebooks/help.ipynb`);
    await page.waitForFunction(() => window.jupyterapp && window.jupyterapp.shell && window.jupyterapp.shell.currentWidget);
    await page.waitForSelector('.jp-Notebook .jp-Cell');
    await page.evaluate(() => window.jupyterapp.commands.execute('logconsole:open'));
    const tab = page.locator('#jp-down-stack .lm-TabBar-tab').first();
    await tab.waitFor({ timeout: 15000 });
    await page.waitForTimeout(600);
    const m = await page.evaluate(() => {
      const t = document.querySelector('#jp-down-stack .lm-TabBar-tab');
      const box = el => el.getBoundingClientRect();
      const svg = box(t.querySelector('.lm-TabBar-tabIcon svg'));
      const label = box(t.querySelector('.lm-TabBar-tabLabel'));
      const icon = box(t.querySelector('.lm-TabBar-tabIcon'));
      return { label: t.querySelector('.lm-TabBar-tabLabel').textContent, svgCenter: svg.y + svg.height / 2, labelCenter: label.y + label.height / 2, svgWidth: svg.width, iconWidth: icon.width };
    });
    console.log(name, JSON.stringify(m));
    const bar = await page.locator('#jp-down-stack > .lm-TabBar').boundingBox();
    await page.screenshot({ path: `${take.dir}/tab.png`, clip: { x: 0, y: bar.y - 6, width: 260, height: bar.height + 12 } });
  } finally {
    await take.browser.close();
  }
})();
