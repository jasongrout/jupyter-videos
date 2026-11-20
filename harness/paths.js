'use strict';
// Where the harness reads and writes. RV_WORK holds the takes and everything that the cut makes; RV_BASE holds
// the folders of the JupyterLab servers (root, settings, environments). Both default to folders in this repository.
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const WORK = process.env.RV_WORK || path.join(REPO, 'work');
const BASE = process.env.RV_BASE || path.join(WORK, 'runtime');
const TAKES = process.env.RV_TAKES || path.join(WORK, 'takes');

/** PLAYWRIGHT_CORE, or the playwright-core that `npm install` put in this repository. */
function playwrightCore() {
  if (process.env.PLAYWRIGHT_CORE) return process.env.PLAYWRIGHT_CORE;
  const local = path.join(REPO, 'node_modules', 'playwright-core');
  return fs.existsSync(path.join(local, 'package.json')) ? local : null;
}

module.exports = { REPO, WORK, BASE, TAKES, PLAYWRIGHT_CORE: playwrightCore() };
