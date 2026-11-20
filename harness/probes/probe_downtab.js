'use strict';
// The Help tab of the down panel in JupyterLab and in Notebook: computed styles and the CSS rules that match.
const { startTake } = require('../rv');
const C = require('../common');
(async () => {
  const [port, app] = [Number(process.argv[2]), process.argv[3]];
  const take = await startTake({ name: `probe-downtab-${process.argv[4] || app}`, port, width: 1152, height: 648, dsf: 2 });
  const { page, lab } = take;
  try {
    if (app === 'lab') {
      await lab.open();
      await lab.setSetting('@jupyterlab/notebook-extension:tracker', 'helpInBottomPanel', true);
      await lab.openFile('help.ipynb');
    } else {
      await page.goto(`http://localhost:${port}/notebooks/help.ipynb`);
      await page.waitForFunction(() => window.jupyterapp && window.jupyterapp.shell && window.jupyterapp.shell.currentWidget);
    }
    await page.waitForSelector('.jp-Notebook .jp-Cell');
    await C.waitIdle(page);
    const cells = page.locator('.jp-Notebook .jp-Cell');
    await cells.nth(0).click();
    await page.keyboard.press('Shift+Enter');
    await C.waitIdle(page);
    await cells.nth(1).locator('.cm-content').click();
    await page.keyboard.type('statistics.median?');
    await page.keyboard.press('Shift+Enter');
    await C.waitIdle(page);
    await page.locator('#jp-down-stack .lm-TabBar-tab').first().waitFor({ timeout: 15000 });
    await page.waitForTimeout(800);
    const info = await page.evaluate(() => {
      const tab = document.querySelector('#jp-down-stack .lm-TabBar-tab');
      const pick = (el, props) => { const s = getComputedStyle(el); return Object.fromEntries(props.map(p => [p, s[p]])); };
      const icon = tab.querySelector('.lm-TabBar-tabIcon');
      const label = tab.querySelector('.lm-TabBar-tabLabel');
      const svg = icon && icon.querySelector('svg');
      const r = el => { const b = el.getBoundingClientRect(); return [b.x, b.y, b.width, b.height].map(v => Math.round(v * 10) / 10); };
      return {
        tabClass: tab.className, barClass: tab.closest('.lm-TabBar').className,
        tab: { rect: r(tab), ...pick(tab, ['display', 'alignItems', 'padding', 'height', 'lineHeight', 'fontSize', 'flexDirection']) },
        icon: icon && { rect: r(icon), cls: icon.className, ...pick(icon, ['display', 'width', 'height', 'margin', 'padding', 'verticalAlign', 'alignSelf', 'lineHeight']) },
        svg: svg && { rect: r(svg), ...pick(svg, ['display', 'verticalAlign', 'height', 'width']) },
        label: label && { rect: r(label), ...pick(label, ['display', 'lineHeight', 'padding', 'height']) },
        sheets: Array.from(document.styleSheets).length,
      };
    });
    console.log(JSON.stringify(info, null, 1));
    // The rules that match the tab and its icon.
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
    const { root } = await cdp.send('DOM.getDocument', { depth: -1 });
    for (const sel of ['#jp-down-stack .lm-TabBar-tab', '#jp-down-stack .lm-TabBar-tabIcon', '#jp-down-stack .lm-TabBar-tabIcon svg']) {
      const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector: sel });
      if (!nodeId) { console.log(sel, 'no node'); continue; }
      const m = await cdp.send('CSS.getMatchedStylesForNode', { nodeId });
      console.log('RULES', sel);
      for (const r of m.matchedCSSRules || []) {
        if (r.rule.origin !== 'regular') continue;
        const props = r.rule.style.cssProperties.filter(p => p.text).map(p => p.text.trim()).join(' ');
        console.log('  ', r.rule.selectorList.text.slice(0, 160), '=>', props.slice(0, 200));
      }
    }
    await page.locator('#jp-down-stack').screenshot({ path: `${take.dir}/down.png` });
  } finally {
    await take.browser.close();
  }
})();
