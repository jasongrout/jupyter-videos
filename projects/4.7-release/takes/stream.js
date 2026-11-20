'use strict';
// The streamed output race: 1,000 log lines with links (the case of #16957).
// Recorded once per server: RV_NAME=stream-46 on 4.6.6, RV_NAME=stream-47 on 4.7.
const C = require('../../../harness/common');
const N = 1000;
const LAST = `tmp/${String(N).padStart(4, '0')}.csv`;

async function startTimer(page) {
  await page.evaluate(
    ([last, n]) => {
      const cells = () => document.querySelectorAll('.jp-NotebookPanel:not(.lm-mod-hidden) .jp-Cell');
      const w = (window.__rv = { first: null, all: null, links: null, done: null, finished: undefined });
      const t0 = performance.now();
      w.t0 = t0;
      const tick = now => {
        const out1 = cells()[0]?.querySelector('.jp-OutputArea');
        const text = out1 ? out1.textContent : '';
        if (!w.armed) {
          const old = cells()[1]?.querySelector('.jp-OutputArea-output');
          if (text.includes(last) || (old && old.textContent.includes('All parts saved'))) {
            requestAnimationFrame(tick);
            return;
          }
          w.armed = now - t0;
        }
        if (w.first === null && text.length) w.first = now - t0;
        if (w.all === null && text.includes(last)) w.all = now - t0;
        if (w.links === null && out1 && out1.querySelectorAll('a[href^="http"]').length >= n) w.links = now - t0;
        const out2 = cells()[1]?.querySelector('.jp-OutputArea-output');
        if (w.done === null && out2 && out2.textContent.includes('All parts saved')) w.done = now - t0;
        if (w.all !== null && w.links !== null && w.done !== null) {
          w.finished = Math.max(w.all, w.links, w.done);
          return;
        }
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    },
    [LAST, N]
  );
}

module.exports = {
  name: process.env.RV_NAME || 'stream',
  // The 4.7 cut used takes at 960x540 and RV_DSF=1.5; later takes are meant for 800x500 at 1.8.
  width: Number(process.env.RV_WIDTH || 800),
  height: Number(process.env.RV_HEIGHT || 500),
  dsf: Number(process.env.RV_DSF || 1.8),
  async setup(take) {
    const { page, lab } = take;
    await lab.open();
    await lab.sidebars({ left: false });
    await lab.openFile('logs.ipynb');
    await C.waitIdle(page);
    const cells = await C.cells(page);
    await cells.nth(1).click();
    await lab.exec('notebook:enter-command-mode');
    // A warm-up run, so that the recorded run replaces an output, as in the release notes.
    await startTimer(page);
    await lab.exec('notebook:run-all-cells');
    await page.waitForFunction(() => window.__rv && window.__rv.finished !== undefined, null, { timeout: 120000, polling: 300 });
    await C.waitIdle(page);
    // Show the outputs, not the code, and start the recorded run from empty outputs.
    const b0 = await cells.nth(0).boundingBox();
    await cells.nth(0).click({ position: { x: b0.width - 80, y: 20 } });
    await lab.exec('notebook:enter-command-mode');
    await lab.exec('notebook:hide-cell-code');
    await lab.exec('notebook:clear-all-cell-outputs');
    await page.evaluate(() => document.querySelector('.jp-NotebookPanel:not(.lm-mod-hidden) .jp-WindowedPanel-outer').scrollTo(0, 0));
    await page.waitForTimeout(1500);
    await take.H.place(page, 900, 500);
  },
  async run(take) {
    const { page } = take;
    await page.waitForTimeout(1200);
    await startTimer(page);
    take.beat('run');
    await page.evaluate(() => window.jupyterapp.commands.execute('notebook:run-all-cells'));
    await page.waitForFunction(() => window.__rv.finished !== undefined, null, { timeout: 120000, polling: 50 });
    const times = await page.evaluate(() => window.__rv);
    take.mark('result', times);
    take.beat('done');
    console.log('times', JSON.stringify(times));
    await page.waitForTimeout(2500);
  }
};
