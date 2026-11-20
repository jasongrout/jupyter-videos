'use strict';
// The Chromium and the playwright-core that the harness drives: RV_CHROMIUM and PLAYWRIGHT_CORE when they are set,
// else the newest build in Playwright's browser cache and the playwright-core of this repository.
// A Playwright install anywhere on the machine can replace the cached build, so the newest one is looked up.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { PLAYWRIGHT_CORE } = require('../paths');

const CACHE = process.env.PLAYWRIGHT_BROWSERS_PATH || path.join(os.homedir(), '.cache', 'ms-playwright');

/** The executable of the newest build whose folder matches `prefix-<number>`. */
function newest(prefix, executable) {
  const builds = fs.existsSync(CACHE)
    ? fs.readdirSync(CACHE).filter(name => new RegExp(`^${prefix}-\\d+$`).test(name))
    : [];
  builds.sort((a, b) => Number(b.split('-').pop()) - Number(a.split('-').pop()));
  for (const build of builds) {
    const file = path.join(CACHE, build, executable);
    if (fs.existsSync(file)) return file;
  }
  return null;
}

const CHROMIUM =
  process.env.RV_CHROMIUM || newest('chromium_headless_shell', 'chrome-headless-shell-linux64/chrome-headless-shell');
const FULL_CHROMIUM = newest('chromium', 'chrome-linux64/chrome');

module.exports = { CHROMIUM, FULL_CHROMIUM, PLAYWRIGHT_CORE };
