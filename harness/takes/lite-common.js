'use strict';
// Shared setup of the JupyterLite takes: the docs demo, which runs JupyterLite 0.9.0b1 (no local build needed).
const URL = process.env.RV_LITE_URL || 'https://jupyterlite.readthedocs.io/en/latest/_static/lab/index.html';

async function ready(page) {
  await page.waitForFunction(() => window.jupyterapp && window.jupyterapp.restored, null, { timeout: 90000 });
  await page.evaluate(() => window.jupyterapp.restored);
  await page.waitForSelector('#jupyterlab-splash', { state: 'detached' }).catch(() => null);
}

async function open(page) {
  page.setDefaultTimeout(60000);
  // The Read the Docs banner of the docs site is not part of JupyterLite.
  await page.addInitScript(() => {
    document.addEventListener('DOMContentLoaded', () => {
      const style = document.createElement('style');
      style.textContent = 'readthedocs-notification, readthedocs-flyout, readthedocs-hotkeys { display: none !important; }';
      document.head.appendChild(style);
    });
  });
  await page.goto(URL);
  await ready(page);
  // The tour extension offers two tours a moment after the start.
  await page.locator('.Toastify__toast').first().waitFor({ timeout: 15000 }).catch(() => null);
  await page.waitForTimeout(800);
}

async function dismissToasts(page) {
  // "Don't show me again" keeps the tour offers away for the rest of the take.
  for (let i = 0; i < 4; i++) {
    const button = page.locator('.Toastify__toast button').filter({ hasText: "Don't show me again" }).first();
    if (!(await button.isVisible().catch(() => false))) break;
    await button.click().catch(() => null);
    await page.waitForTimeout(400);
  }
  await page.waitForTimeout(500);
}

module.exports = { URL, ready, open, dismissToasts };
